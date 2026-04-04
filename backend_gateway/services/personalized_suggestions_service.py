"""
Personalized Suggestions Service for generating user-specific chat suggestions
based on dietary preferences, allergens, and pantry contents.
"""

import json
import logging
import random
from datetime import datetime
from typing import Any

from sqlalchemy import text

from backend_gateway.services.postgres_service import PostgresService

logger = logging.getLogger(__name__)


class PersonalizedSuggestionsService:
    """Service for generating personalized chat suggestions based on user preferences and pantry"""

    def __init__(self):
        self.db_service = PostgresService()
        self.exploration_rate = 0.2
        self.exploration_min_candidates = 3
        self._outcome_actions = {"shown", "clicked", "saved", "cooked", "dismissed"}

        # Base suggestion templates categorized by type
        self.suggestion_templates = {
            "dietary_specific": {
                "vegetarian": [
                    "What vegetarian recipes can I make tonight?",
                    "Show me plant-based dinner ideas",
                    "What can I cook with my vegetables?",
                    "Vegetarian recipes with protein alternatives",
                ],
                "vegan": [
                    "What vegan meals can I prepare?",
                    "Show me dairy-free and egg-free recipes",
                    "Plant-based dinner options for tonight",
                    "Vegan recipes using my ingredients",
                ],
                "gluten-free": [
                    "What gluten-free recipes can I make?",
                    "Show me wheat-free dinner options",
                    "Gluten-free meals with my pantry items",
                    "Safe recipes without gluten",
                ],
                "keto": [
                    "What low-carb keto recipes can I make?",
                    "High-fat, low-carb dinner ideas",
                    "Keto-friendly meals tonight",
                    "Show me ketogenic recipes",
                ],
                "paleo": [
                    "What paleo-friendly recipes can I cook?",
                    "Show me grain-free dinner options",
                    "Paleo meals with my ingredients",
                    "Whole foods recipes for tonight",
                ],
            },
            "allergen_safe": {
                "nuts": [
                    "What nut-free recipes are safe for me?",
                    "Show me allergy-safe dinner options",
                    "Recipes without nuts or nut oils",
                ],
                "dairy": [
                    "What dairy-free recipes can I make?",
                    "Show me lactose-free dinner ideas",
                    "Recipes without milk, cheese, or butter",
                ],
                "shellfish": [
                    "What shellfish-free seafood recipes are safe?",
                    "Show me fish recipes without shellfish",
                    "Safe seafood options for my allergy",
                ],
                "eggs": [
                    "What egg-free recipes can I cook?",
                    "Show me dinner options without eggs",
                    "Recipes safe for egg allergy",
                ],
            },
            "cuisine_specific": {
                "italian": [
                    "What Italian dishes can I make tonight?",
                    "Show me pasta and Italian recipes",
                    "Mediterranean dinner ideas",
                ],
                "mexican": [
                    "What Mexican recipes can I prepare?",
                    "Show me Latin American dinner ideas",
                    "Spicy Mexican dishes for tonight",
                ],
                "asian": [
                    "What Asian recipes can I cook?",
                    "Show me stir-fry and Asian dinner ideas",
                    "Oriental cuisine with my ingredients",
                ],
                "indian": [
                    "What Indian curry recipes can I make?",
                    "Show me spiced Indian dinner options",
                    "Flavorful Indian dishes tonight",
                ],
            },
            "expiring_items": [
                "What can I make with expiring ingredients?",
                "Help me use items that expire soon",
                "Recipes to prevent food waste",
                "Use my expiring pantry items",
            ],
            "quick_meals": [
                "What can I make in 20 minutes?",
                "Quick and easy dinner ideas",
                "Fast recipes for busy nights",
                "Simple meals under 30 minutes",
            ],
            "pantry_based": [
                "What can I make with ingredients I have?",
                "Show me recipes using my pantry",
                "Dinner ideas without shopping",
                "Use only what I have available",
            ],
            "healthy": [
                "What healthy recipes can I make tonight?",
                "Show me nutritious dinner options",
                "Low-calorie meals with my ingredients",
                "Balanced and wholesome recipes",
            ],
        }

    async def get_personalized_suggestions(self, user_id: int, limit: int = 6) -> list[dict[str, Any]]:
        """
        Generate personalized chat suggestions based on user preferences and pantry

        Args:
            user_id: The user's ID
            limit: Maximum number of suggestions to return

        Returns:
            Ranked personalized suggestions with scoring metadata
        """
        try:
            await self._ensure_suggestion_outcomes_table()

            # Fetch user preferences
            user_preferences = await self._fetch_user_preferences(user_id)

            # Check for expiring items
            expiring_items = await self._check_expiring_items(user_id)
            interaction_signals = await self._fetch_interaction_signals(user_id)
            outcome_priors = await self._fetch_suggestion_outcome_priors(user_id)

            # Generate suggestion candidates (templates remain candidate source)
            candidates = self._build_template_candidates(
                user_preferences=user_preferences,
                expiring_items=expiring_items,
            )
            if not candidates:
                return self._get_fallback_suggestions(limit)

            ranked_candidates = self._rank_candidates(
                candidates=candidates,
                interaction_signals=interaction_signals,
                outcome_priors=outcome_priors,
                expiring_items=expiring_items,
            )
            selected_candidates = self._select_with_exploration(ranked_candidates, limit)
            await self._persist_served_suggestions(user_id, selected_candidates)

            suggestions = []
            for candidate in selected_candidates:
                expected_utility = max(min(candidate["score"], 1.0), 0.0)
                suggestions.append(
                    {
                        "suggestion": candidate["suggestion"],
                        "reason_code": candidate["reason_code"],
                        "confidence": round(expected_utility, 3),
                        "source_signal": candidate["source_signal"],
                        "expected_utility": round(expected_utility, 3),
                        "exploration_selected": candidate.get("exploration_selected", False),
                    }
                )

            logger.info(
                f"Generated {len(suggestions)} ranked personalized suggestions for user {user_id}"
            )
            return suggestions

        except Exception as e:
            logger.error(f"Error generating personalized suggestions for user {user_id}: {str(e)}")
            # Fallback to generic suggestions
            return self._get_fallback_suggestions(limit)

    async def track_suggestion_outcome(
        self,
        user_id: int,
        suggestion: str,
        action: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Persist suggestion outcome events for learning and offline evaluation."""
        normalized_action = action.lower()
        if normalized_action not in self._outcome_actions:
            logger.warning(
                f"Rejected unknown suggestion action '{action}' for user {user_id}, suggestion '{suggestion}'"
            )
            return False

        try:
            await self._ensure_suggestion_outcomes_table()
            query = text(
                """
                INSERT INTO personalized_suggestion_outcomes
                (user_id, suggestion, action, metadata, created_at)
                VALUES (:user_id, :suggestion, :action, CAST(:metadata AS JSONB), NOW())
                """
            )
            with self.db_service.get_session() as session:
                session.execute(
                    query,
                    {
                        "user_id": user_id,
                        "suggestion": suggestion,
                        "action": normalized_action,
                        "metadata": json.dumps(metadata or {}),
                    },
                )
                session.commit()
            return True
        except Exception as e:
            logger.error(f"Error persisting suggestion outcome: {str(e)}")
            return False

    async def _fetch_user_preferences(self, user_id: int) -> dict[str, Any]:
        """Fetch user dietary preferences and allergens"""
        try:
            query = text(
                """
                SELECT
                    dietary_preferences,
                    allergies,
                    cuisine_preferences,
                    household_size,
                    cooking_skill_level
                FROM user_preferences
                WHERE user_id = :user_id
            """
            )

            with self.db_service.get_session() as session:
                result = session.execute(query, {"user_id": user_id}).fetchone()

                if result:
                    return {
                        "dietary_preferences": result.dietary_preferences or [],
                        "allergens": result.allergies or [],
                        "cuisine_preferences": result.cuisine_preferences or [],
                        "household_size": result.household_size,
                        "cooking_skill_level": result.cooking_skill_level,
                    }
                else:
                    return {
                        "dietary_preferences": [],
                        "allergens": [],
                        "cuisine_preferences": [],
                        "household_size": None,
                        "cooking_skill_level": None,
                    }
        except Exception as e:
            logger.error(f"Error fetching user preferences: {str(e)}")
            return {"dietary_preferences": [], "allergens": [], "cuisine_preferences": []}

    async def _check_expiring_items(self, user_id: int) -> list[dict[str, Any]]:
        """Check for items expiring in the next 7 days"""
        try:
            query = text(
                """
                SELECT
                    pi.name as product_name,
                    pi.expiration_date,
                    pi.quantity,
                    pi.quantity_consumed
                FROM pantry_items pi
                WHERE pi.user_id = :user_id
                    AND pi.expiration_date IS NOT NULL
                    AND pi.expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                    AND pi.quantity > COALESCE(pi.quantity_consumed, 0)
                    AND pi.is_deleted = false
                ORDER BY pi.expiration_date ASC
            """
            )

            with self.db_service.get_session() as session:
                result = session.execute(query, {"user_id": user_id})
                expiring_items = []

                for row in result:
                    days_until_expiry = (row.expiration_date - datetime.now().date()).days
                    expiring_items.append(
                        {
                            "product_name": row.product_name,
                            "expiration_date": row.expiration_date,
                            "days_until_expiry": days_until_expiry,
                            "quantity": row.quantity,
                            "quantity_consumed": row.quantity_consumed or 0,
                        }
                    )

                return expiring_items[:5]  # Limit to 5 most urgent items

        except Exception as e:
            logger.error(f"Error checking expiring items: {str(e)}")
            return []

    def _get_allergen_safe_suggestions(self, user_preferences: dict[str, Any]) -> list[str]:
        """Generate allergen-safe suggestions based on user allergens"""
        allergens = user_preferences.get("allergens", [])
        if not allergens:
            return []

        suggestions = []
        for allergen in allergens[:2]:  # Limit to top 2 allergens to avoid overwhelming
            allergen_lower = allergen.lower()
            if allergen_lower in self.suggestion_templates["allergen_safe"]:
                suggestions.extend(self.suggestion_templates["allergen_safe"][allergen_lower][:1])
            else:
                # Generic allergen-safe suggestion
                suggestions.append(f"What {allergen}-free recipes are safe for me?")

        return suggestions

    def _get_dietary_suggestions(self, user_preferences: dict[str, Any]) -> list[str]:
        """Generate dietary preference-based suggestions"""
        dietary_prefs = user_preferences.get("dietary_preferences", [])
        if not dietary_prefs:
            return []

        suggestions = []
        for diet in dietary_prefs[:2]:  # Limit to top 2 dietary preferences
            diet_lower = diet.lower()
            if diet_lower in self.suggestion_templates["dietary_specific"]:
                suggestions.extend(self.suggestion_templates["dietary_specific"][diet_lower][:1])
            else:
                # Generic dietary suggestion
                suggestions.append(f"What {diet} recipes can I make tonight?")

        return suggestions

    def _get_cuisine_suggestions(self, user_preferences: dict[str, Any]) -> list[str]:
        """Generate cuisine preference-based suggestions"""
        cuisine_prefs = user_preferences.get("cuisine_preferences", [])
        if not cuisine_prefs:
            return []

        suggestions = []
        for cuisine in cuisine_prefs[:1]:  # Limit to 1 cuisine to keep suggestions diverse
            cuisine_lower = cuisine.lower()
            if cuisine_lower in self.suggestion_templates["cuisine_specific"]:
                suggestions.extend(self.suggestion_templates["cuisine_specific"][cuisine_lower][:1])
            else:
                # Generic cuisine suggestion
                suggestions.append(f"What {cuisine} recipes can I cook tonight?")

        return suggestions

    def _get_fallback_suggestions(self, limit: int) -> list[dict[str, Any]]:
        """Fallback suggestions when personalization fails"""
        fallback = [
            "What can I make for dinner?",
            "What can I make with ingredients I have?",
            "Show me healthy recipes",
            "Quick meals under 20 minutes",
            "What should I cook tonight?",
            "Help me use expiring ingredients",
        ]
        return [
            {
                "suggestion": suggestion,
                "reason_code": "generic_fallback",
                "confidence": 0.35,
                "source_signal": "fallback_template",
                "expected_utility": 0.35,
                "exploration_selected": False,
            }
            for suggestion in fallback[:limit]
        ]

    def _build_template_candidates(
        self,
        user_preferences: dict[str, Any],
        expiring_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build candidate suggestions from templates before ranking."""
        candidates: list[dict[str, Any]] = []

        if expiring_items:
            for suggestion in self.suggestion_templates["expiring_items"]:
                candidates.append(
                    {
                        "suggestion": suggestion,
                        "reason_code": "expiring_item_relevance",
                        "source_signal": "expiring_items",
                    }
                )

        for suggestion in self._get_allergen_safe_suggestions(user_preferences):
            candidates.append(
                {
                    "suggestion": suggestion,
                    "reason_code": "allergen_safety",
                    "source_signal": "allergen_preference",
                }
            )
        for suggestion in self._get_dietary_suggestions(user_preferences):
            candidates.append(
                {
                    "suggestion": suggestion,
                    "reason_code": "dietary_affinity",
                    "source_signal": "dietary_preference",
                }
            )
        for suggestion in self._get_cuisine_suggestions(user_preferences):
            candidates.append(
                {
                    "suggestion": suggestion,
                    "reason_code": "cuisine_affinity",
                    "source_signal": "cuisine_preference",
                }
            )

        for suggestion in (
            self.suggestion_templates["pantry_based"]
            + self.suggestion_templates["quick_meals"]
            + self.suggestion_templates["healthy"]
        ):
            candidates.append(
                {
                    "suggestion": suggestion,
                    "reason_code": "general_helpfulness",
                    "source_signal": "general_template",
                }
            )

        # De-duplicate while preserving first semantic reason/source assignment.
        deduped = []
        seen = set()
        for candidate in candidates:
            if candidate["suggestion"] in seen:
                continue
            deduped.append(candidate)
            seen.add(candidate["suggestion"])
        return deduped

    def _rank_candidates(
        self,
        candidates: list[dict[str, Any]],
        interaction_signals: dict[str, Any],
        outcome_priors: dict[str, Any],
        expiring_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Rank by expected utility from interaction and freshness signals."""
        cuisine_affinity = interaction_signals.get("cuisine_affinity", {})
        positive_rate = interaction_signals.get("positive_rate", 0.5)
        dismiss_rate = interaction_signals.get("dismiss_rate", 0.0)

        for candidate in candidates:
            text_value = candidate["suggestion"].lower()

            expiring_score = 0.0
            if expiring_items and any(
                keyword in text_value for keyword in ["expir", "waste", "pantry", "use"]
            ):
                expiring_score = 1.0

            cuisine_score = 0.0
            for cuisine, affinity in cuisine_affinity.items():
                if cuisine and cuisine.lower() in text_value:
                    cuisine_score = max(cuisine_score, affinity)

            outcome_stats = outcome_priors.get(candidate["suggestion"], {})
            historical_success = outcome_stats.get("success_rate", 0.5)
            historical_dismiss = outcome_stats.get("dismiss_rate", 0.0)

            expected_utility = (
                0.30 * expiring_score
                + 0.25 * cuisine_score
                + 0.20 * positive_rate
                + 0.20 * historical_success
                - 0.15 * dismiss_rate
                - 0.10 * historical_dismiss
            )
            candidate["score"] = expected_utility

        return sorted(candidates, key=lambda row: row["score"], reverse=True)

    def _select_with_exploration(
        self, ranked_candidates: list[dict[str, Any]], limit: int
    ) -> list[dict[str, Any]]:
        """Use epsilon-greedy exploration to avoid repeatedly serving same templates."""
        if not ranked_candidates:
            return []

        top_ranked = ranked_candidates[: max(limit, 1)]
        final_selection = list(top_ranked)

        should_explore = (
            len(ranked_candidates) >= self.exploration_min_candidates
            and random.random() < self.exploration_rate
        )
        if not should_explore or len(ranked_candidates) <= limit:
            return final_selection[:limit]

        exploration_pool = ranked_candidates[limit:]
        if not exploration_pool:
            return final_selection[:limit]

        replace_index = random.randrange(min(limit, len(final_selection)))
        exploration_candidate = random.choice(exploration_pool).copy()
        exploration_candidate["exploration_selected"] = True
        final_selection[replace_index] = exploration_candidate
        return final_selection[:limit]

    async def _fetch_interaction_signals(self, user_id: int) -> dict[str, Any]:
        """Aggregate interaction behavior from user_recipe_interactions."""
        try:
            query = text(
                """
                SELECT
                    COUNT(*) FILTER (WHERE action IN ('clicked', 'saved', 'cooked'))::float AS positive_events,
                    COUNT(*) FILTER (WHERE action = 'dismissed')::float AS dismiss_events,
                    COUNT(*)::float AS total_events
                FROM user_recipe_interactions
                WHERE user_id = :user_id
                    AND timestamp >= NOW() - INTERVAL '60 days'
                """
            )

            cuisine_query = text(
                """
                SELECT
                    LOWER(COALESCE(metadata->>'cuisine', context->>'cuisine')) AS cuisine,
                    AVG(
                        CASE
                            WHEN action IN ('clicked', 'saved', 'cooked') THEN 1.0
                            WHEN action = 'dismissed' THEN 0.0
                            ELSE 0.4
                        END
                    ) AS affinity
                FROM user_recipe_interactions
                WHERE user_id = :user_id
                    AND timestamp >= NOW() - INTERVAL '90 days'
                GROUP BY LOWER(COALESCE(metadata->>'cuisine', context->>'cuisine'))
                HAVING LOWER(COALESCE(metadata->>'cuisine', context->>'cuisine')) IS NOT NULL
                """
            )

            with self.db_service.get_session() as session:
                counts = session.execute(query, {"user_id": user_id}).fetchone()
                cuisine_rows = session.execute(cuisine_query, {"user_id": user_id}).fetchall()

            total_events = float(counts.total_events or 0.0) if counts else 0.0
            positive_rate = (
                float(counts.positive_events or 0.0) / total_events if total_events else 0.5
            )
            dismiss_rate = float(counts.dismiss_events or 0.0) / total_events if total_events else 0.0
            cuisine_affinity = {
                row.cuisine: max(min(float(row.affinity or 0.0), 1.0), 0.0) for row in cuisine_rows
            }
            return {
                "positive_rate": positive_rate,
                "dismiss_rate": dismiss_rate,
                "cuisine_affinity": cuisine_affinity,
            }
        except Exception as e:
            logger.warning(f"Failed to fetch interaction signals for user {user_id}: {str(e)}")
            return {"positive_rate": 0.5, "dismiss_rate": 0.0, "cuisine_affinity": {}}

    async def _fetch_suggestion_outcome_priors(self, user_id: int) -> dict[str, Any]:
        """Load prior suggestion-level outcomes for expected utility estimation."""
        try:
            query = text(
                """
                SELECT
                    suggestion,
                    COUNT(*) FILTER (WHERE action = 'shown')::float AS shown_count,
                    COUNT(*) FILTER (WHERE action IN ('clicked', 'saved', 'cooked'))::float AS success_count,
                    COUNT(*) FILTER (WHERE action = 'dismissed')::float AS dismiss_count
                FROM personalized_suggestion_outcomes
                WHERE user_id = :user_id
                    AND created_at >= NOW() - INTERVAL '120 days'
                GROUP BY suggestion
                """
            )
            with self.db_service.get_session() as session:
                rows = session.execute(query, {"user_id": user_id}).fetchall()

            priors: dict[str, Any] = {}
            for row in rows:
                shown_count = float(row.shown_count or 0.0)
                denominator = shown_count if shown_count > 0 else 1.0
                priors[row.suggestion] = {
                    "success_rate": float(row.success_count or 0.0) / denominator,
                    "dismiss_rate": float(row.dismiss_count or 0.0) / denominator,
                }
            return priors
        except Exception as e:
            logger.warning(f"Failed to fetch suggestion outcome priors for user {user_id}: {str(e)}")
            return {}

    async def _persist_served_suggestions(
        self, user_id: int, suggestions: list[dict[str, Any]]
    ) -> None:
        """Persist shown events per suggestion for future learning."""
        if not suggestions:
            return
        try:
            query = text(
                """
                INSERT INTO personalized_suggestion_outcomes
                (user_id, suggestion, action, metadata, created_at)
                VALUES (
                    :user_id,
                    :suggestion,
                    'shown',
                    CAST(:metadata AS JSONB),
                    NOW()
                )
                """
            )
            with self.db_service.get_session() as session:
                for candidate in suggestions:
                    metadata = {
                        "reason_code": candidate.get("reason_code"),
                        "source_signal": candidate.get("source_signal"),
                        "score": candidate.get("score"),
                        "exploration_selected": candidate.get("exploration_selected", False),
                    }
                    session.execute(
                        query,
                        {
                            "user_id": user_id,
                            "suggestion": candidate.get("suggestion"),
                            "metadata": json.dumps(metadata),
                        },
                    )
                session.commit()
        except Exception as e:
            logger.warning(f"Failed to persist shown suggestions for user {user_id}: {str(e)}")

    async def _ensure_suggestion_outcomes_table(self) -> None:
        """Ensure lightweight suggestion outcomes table exists."""
        try:
            ddl = text(
                """
                CREATE TABLE IF NOT EXISTS personalized_suggestion_outcomes (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    suggestion TEXT NOT NULL,
                    action VARCHAR(32) NOT NULL,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_pso_user_created
                    ON personalized_suggestion_outcomes(user_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_pso_user_suggestion
                    ON personalized_suggestion_outcomes(user_id, suggestion);
                """
            )
            with self.db_service.get_session() as session:
                session.execute(ddl)
                session.commit()
        except Exception as e:
            logger.warning(f"Unable to create suggestion outcomes table: {str(e)}")

    async def get_suggestion_context(self, user_id: int, suggestion: str) -> dict[str, Any]:
        """
        Get context about why a suggestion was made for the user

        Args:
            user_id: The user's ID
            suggestion: The suggestion text

        Returns:
            Dict with context about the suggestion
        """
        try:
            user_preferences = await self._fetch_user_preferences(user_id)
            expiring_items = await self._check_expiring_items(user_id)

            context = {
                "suggestion": suggestion,
                "user_id": user_id,
                "reasoning": [],
                "safety_considerations": [],
                "personalization_applied": True,
            }

            # Analyze why this suggestion was made
            suggestion_lower = suggestion.lower()

            if "expir" in suggestion_lower and expiring_items:
                context["reasoning"].append(f"You have {len(expiring_items)} items expiring soon")
                context["expiring_items"] = expiring_items
                context["safety_considerations"].append(
                    "Prioritizing expiring items to prevent waste"
                )

            if user_preferences.get("allergens"):
                for allergen in user_preferences["allergens"]:
                    if allergen.lower() in suggestion_lower:
                        context["reasoning"].append(f"Personalized for your {allergen} allergy")
                        context["safety_considerations"].append(
                            f"Will exclude {allergen} from all recommendations"
                        )

            if user_preferences.get("dietary_preferences"):
                for diet in user_preferences["dietary_preferences"]:
                    if diet.lower() in suggestion_lower:
                        context["reasoning"].append(f"Matched your {diet} dietary preference")

            if user_preferences.get("cuisine_preferences"):
                for cuisine in user_preferences["cuisine_preferences"]:
                    if cuisine.lower() in suggestion_lower:
                        context["reasoning"].append(f"Based on your love for {cuisine} cuisine")

            return context

        except Exception as e:
            logger.error(f"Error getting suggestion context: {str(e)}")
            return {
                "suggestion": suggestion,
                "user_id": user_id,
                "reasoning": ["Generic suggestion"],
                "safety_considerations": [],
                "personalization_applied": False,
            }
