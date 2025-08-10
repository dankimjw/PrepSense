"""Service for nutrient gap analysis and auditing."""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from backend_gateway.config.nutrient_config import (
    ESSENTIAL_NUTRIENTS,
    RDA_VALUES,
    UPPER_LIMIT_NUTRIENTS,
    format_nutrient_value,
    get_nutrient_gap,
    is_nutrient_deficient,
    is_nutrient_excessive,
)
from backend_gateway.models.nutrition import (
    DailyIntakeLog,
    NutrientGap,
    NutrientGapAnalysis,
    NutrientProfile,
    RecipeNutrientScore,
)

logger = logging.getLogger(__name__)


class NutrientAuditorService:
    """Service for analyzing nutrient gaps and scoring recipes."""

    def __init__(self, storage_path: str = "/tmp/nutrient_gaps"):
        """Initialize the nutrient auditor service."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def analyze_daily_gaps(self, user_id: str, daily_log: DailyIntakeLog) -> NutrientGapAnalysis:
        """Analyze nutrient gaps for a single day."""
        logger.info(f"Analyzing daily nutrient gaps for user {user_id}")

        # Get total nutrients consumed
        total_nutrients = daily_log.get_total_nutrients()

        # Calculate gaps for each nutrient
        gaps = []
        priority_deficiencies = []
        priority_excesses = []

        for nutrient, rda_value in RDA_VALUES.items():
            consumed = getattr(total_nutrients, nutrient, 0.0)
            gap = get_nutrient_gap(consumed, nutrient)

            # Calculate percentage met
            percentage_met = (consumed / rda_value * 100) if rda_value > 0 else 0

            # Check if deficient or excessive
            is_deficient = is_nutrient_deficient(consumed, nutrient)
            is_excessive = is_nutrient_excessive(consumed, nutrient)

            # Determine priority
            priority = self._get_nutrient_priority(nutrient, consumed, rda_value)

            nutrient_gap = NutrientGap(
                nutrient=nutrient,
                consumed=consumed,
                recommended=rda_value,
                gap=gap,
                percentage_met=percentage_met,
                is_deficient=is_deficient,
                is_excessive=is_excessive,
                priority=priority,
            )
            gaps.append(nutrient_gap)

            # Track priority issues
            if is_deficient and nutrient in ESSENTIAL_NUTRIENTS:
                priority_deficiencies.append(nutrient)
            elif is_excessive and nutrient in UPPER_LIMIT_NUTRIENTS:
                priority_excesses.append(nutrient)

        # Calculate overall nutritional completeness score
        overall_score = self._calculate_overall_score(gaps)

        analysis = NutrientGapAnalysis(
            user_id=user_id,
            analysis_date=daily_log.date,
            gaps=gaps,
            priority_deficiencies=priority_deficiencies,
            priority_excesses=priority_excesses,
            overall_score=overall_score,
        )

        # Save analysis to storage
        self._save_analysis(analysis)

        return analysis

    def analyze_weekly_gaps(
        self, user_id: str, daily_logs: list[DailyIntakeLog]
    ) -> NutrientGapAnalysis:
        """Analyze nutrient gaps over a week period."""
        logger.info(f"Analyzing weekly nutrient gaps for user {user_id}")

        if not daily_logs:
            return self._get_empty_analysis(user_id)

        # Calculate average daily nutrients
        total_nutrients = NutrientProfile()
        for log in daily_logs:
            total_nutrients = total_nutrients + log.get_total_nutrients()

        # Average over the number of days
        avg_nutrients = total_nutrients * (1.0 / len(daily_logs))

        # Create a synthetic daily log for analysis
        synthetic_log = DailyIntakeLog(user_id=user_id, date=daily_logs[-1].date, meals=[])

        # Override total nutrients method to return our average
        synthetic_log.get_total_nutrients = lambda: avg_nutrients

        # Analyze as a single day but mark as weekly
        analysis = self.analyze_daily_gaps(user_id, synthetic_log)
        analysis.period_days = len(daily_logs)

        return analysis

    def score_recipe_for_gaps(
        self, recipe_nutrients: NutrientProfile, gap_analysis: NutrientGapAnalysis, recipe_id: str
    ) -> RecipeNutrientScore:
        """Score a recipe based on how well it addresses nutrient gaps."""
        logger.debug(f"Scoring recipe {recipe_id} for nutrient gaps")

        addressed_deficiencies = []
        created_excesses = []
        gap_closure_score = 0.0
        balance_score = 0.0
        health_score = 0.0

        # Analyze each nutrient
        for gap in gap_analysis.gaps:
            nutrient = gap.nutrient
            recipe_amount = getattr(recipe_nutrients, nutrient, 0.0)

            if recipe_amount <= 0:
                continue

            # Check if recipe addresses a deficiency
            if gap.is_deficient and recipe_amount > 0:
                # Calculate how much of the gap this recipe fills
                gap_fill_percentage = min(recipe_amount / abs(gap.gap), 1.0)

                # Weight by nutrient priority
                priority_weight = self._get_priority_weight(gap.priority)
                gap_closure_score += gap_fill_percentage * priority_weight
                addressed_deficiencies.append(nutrient)

            # Check if recipe creates an excess
            elif not gap.is_deficient and nutrient in UPPER_LIMIT_NUTRIENTS:
                # For upper limit nutrients, any addition when already adequate is negative
                if gap.gap >= 0:  # Already at or over limit
                    excess_penalty = min(recipe_amount / gap.recommended, 1.0)
                    gap_closure_score -= excess_penalty * 0.5
                    created_excesses.append(nutrient)

        # Calculate balance score (how well-rounded the recipe is)
        balance_score = self._calculate_balance_score(recipe_nutrients)

        # Calculate health score (overall healthiness)
        health_score = self._calculate_health_score(recipe_nutrients)

        # Create and return the score
        recipe_score = RecipeNutrientScore(
            recipe_id=recipe_id,
            gap_closure_score=max(0.0, gap_closure_score),
            balance_score=balance_score,
            health_score=health_score,
            addressed_deficiencies=addressed_deficiencies,
            created_excesses=created_excesses,
        )

        recipe_score.calculate_total_score()
        return recipe_score

    def get_gap_analysis(
        self, user_id: str, analysis_date: Optional[date] = None
    ) -> Optional[NutrientGapAnalysis]:
        """Retrieve stored gap analysis for a user."""
        if analysis_date is None:
            analysis_date = date.today()

        file_path = self.storage_path / f"{user_id}_gaps_{analysis_date.isoformat()}.json"

        try:
            if file_path.exists():
                with open(file_path) as f:
                    data = json.load(f)
                    return NutrientGapAnalysis.parse_obj(data)
        except Exception as e:
            logger.error(f"Error loading gap analysis: {e}")

        return None

    def get_nutrient_recommendations(self, gap_analysis: NutrientGapAnalysis) -> list[str]:
        """Generate nutrient recommendations based on gap analysis."""
        recommendations = []

        # Focus on priority deficiencies
        significant_deficiencies = gap_analysis.get_significant_deficiencies(threshold=0.7)

        if significant_deficiencies:
            for gap in significant_deficiencies[:3]:  # Top 3 deficiencies
                nutrient = gap.nutrient
                amount_needed = abs(gap.gap)
                formatted_amount = format_nutrient_value(amount_needed, nutrient)

                rec = f"Add {formatted_amount} more {nutrient.replace('_', ' ').title()}"
                recommendations.append(rec)

        # Address significant excesses
        significant_excesses = gap_analysis.get_significant_excesses()
        if significant_excesses:
            for gap in significant_excesses[:2]:  # Top 2 excesses
                nutrient = gap.nutrient
                excess_amount = gap.gap
                formatted_amount = format_nutrient_value(excess_amount, nutrient)

                rec = f"Reduce {nutrient.replace('_', ' ').title()} by {formatted_amount}"
                recommendations.append(rec)

        return recommendations

    def _get_nutrient_priority(self, nutrient: str, consumed: float, rda: float) -> str:
        """Determine priority level for a nutrient."""
        if nutrient in ESSENTIAL_NUTRIENTS:
            if consumed < rda * 0.5:
                return "high"
            elif consumed < rda * 0.8:
                return "medium"
        elif nutrient in UPPER_LIMIT_NUTRIENTS:
            if consumed > rda * 1.5:
                return "high"
            elif consumed > rda * 1.2:
                return "medium"

        return "low"

    def _get_priority_weight(self, priority: str) -> float:
        """Get weight for priority level."""
        weights = {"high": 3.0, "medium": 2.0, "low": 1.0}
        return weights.get(priority, 1.0)

    def _calculate_overall_score(self, gaps: list[NutrientGap]) -> float:
        """Calculate overall nutritional completeness score (0-100)."""
        if not gaps:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for gap in gaps:
            # Score based on how well RDA is met
            if gap.nutrient in UPPER_LIMIT_NUTRIENTS:
                # For upper limit nutrients, score decreases if exceeded
                if gap.consumed <= gap.recommended:
                    score = 100.0
                else:
                    score = max(0.0, 100.0 - (gap.consumed / gap.recommended - 1.0) * 100)
            else:
                # For essential nutrients, score based on percentage met
                score = min(100.0, gap.percentage_met)

            weight = self._get_priority_weight(gap.priority)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _calculate_balance_score(self, nutrients: NutrientProfile) -> float:
        """Calculate how balanced a recipe is nutritionally."""
        # Simple balance score based on presence of multiple nutrient types
        score = 0.0

        # Check macronutrient balance
        if nutrients.protein > 0:
            score += 25.0
        if nutrients.carbohydrates > 0:
            score += 20.0
        if nutrients.fiber > 0:
            score += 15.0
        if nutrients.total_fat > 0:
            score += 10.0

        # Check vitamin presence
        vitamins = [nutrients.vitamin_c, nutrients.vitamin_a, nutrients.vitamin_d]
        vitamin_score = sum(1 for v in vitamins if v > 0) * 5.0
        score += vitamin_score

        # Check mineral presence
        minerals = [nutrients.calcium, nutrients.iron, nutrients.potassium]
        mineral_score = sum(1 for m in minerals if m > 0) * 5.0
        score += mineral_score

        return min(100.0, score)

    def _calculate_health_score(self, nutrients: NutrientProfile) -> float:
        """Calculate overall health score for a recipe."""
        score = 100.0

        # Penalize high sodium
        if nutrients.sodium > 600:  # mg per serving
            score -= min(30.0, (nutrients.sodium - 600) / 20)

        # Penalize high saturated fat
        if nutrients.saturated_fat > 5:  # g per serving
            score -= min(20.0, (nutrients.saturated_fat - 5) * 2)

        # Penalize high sugar
        if nutrients.sugar > 15:  # g per serving
            score -= min(25.0, (nutrients.sugar - 15) * 1.5)

        # Reward high fiber
        if nutrients.fiber > 5:  # g per serving
            score += min(20.0, (nutrients.fiber - 5) * 2)

        # Reward good protein
        if nutrients.protein > 10:  # g per serving
            score += min(15.0, (nutrients.protein - 10) * 1)

        return max(0.0, score)

    def _save_analysis(self, analysis: NutrientGapAnalysis):
        """Save gap analysis to storage."""
        file_path = (
            self.storage_path / f"{analysis.user_id}_gaps_{analysis.analysis_date.isoformat()}.json"
        )

        try:
            with open(file_path, "w") as f:
                json.dump(analysis.dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving gap analysis: {e}")

    def _get_empty_analysis(self, user_id: str) -> NutrientGapAnalysis:
        """Get empty analysis for when no data is available."""
        return NutrientGapAnalysis(
            user_id=user_id,
            analysis_date=date.today(),
            gaps=[],
            priority_deficiencies=[],
            priority_excesses=[],
            overall_score=0.0,
        )
