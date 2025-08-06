"""Nutrient Auditor Agent for analyzing dietary gaps and deficiencies."""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from crewai import Agent, Task
from pydantic import BaseModel, Field

from ..config.nutrient_config import ESSENTIAL_NUTRIENTS, UPPER_LIMIT_NUTRIENTS
from ..models.nutrition import DailyIntakeLog, NutrientGapAnalysis, NutrientProfile
from ..services.nutrient_auditor_service import NutrientAuditorService

# from crewai.flow import Flow, listen, start # Commented out - not available in crewai 0.1.32
from .mock_flow import Flow, listen, start  # Using mocks for compatibility

logger = logging.getLogger(__name__)


class NutrientAuditorState(BaseModel):
    """State for the Nutrient Auditor Flow."""

    user_id: str
    analysis_date: date
    daily_logs: List[DailyIntakeLog] = Field(default_factory=list)
    gap_analysis: Optional[NutrientGapAnalysis] = None
    recommendations: List[str] = Field(default_factory=list)
    priority_message: Optional[str] = None
    error_message: Optional[str] = None


class NutrientAuditorAgent:
    """Agent responsible for analyzing nutrient gaps and dietary deficiencies."""

    def __init__(self):
        """Initialize the Nutrient Auditor Agent."""
        self.service = NutrientAuditorService()
        self.agent = Agent(
            role="Nutrient Auditor",
            goal="Analyze user dietary intake to identify nutrient gaps, deficiencies, and excesses",
            backstory=(
                "You are a skilled nutritional analyst who carefully examines daily food intake "
                "to identify nutritional gaps. You compare actual consumption against recommended "
                "daily allowances (RDA) and flag concerning deficiencies or excesses. Your analysis "
                "helps users understand their nutritional status and guides recipe recommendations."
            ),
            verbose=True,
            allow_delegation=False,
        )

    def create_analysis_task(self, user_id: str, daily_logs: List[DailyIntakeLog]) -> Task:
        """Create a task for analyzing nutrient gaps."""
        return Task(
            description=(
                f"Analyze the dietary intake for user {user_id} and identify nutrient gaps.\n"
                f"Review {len(daily_logs)} days of meal logs and:\n"
                "1. Calculate total nutrients consumed per day\n"
                "2. Compare against RDA values for each nutrient\n"
                "3. Identify significant deficiencies (< 70% RDA)\n"
                "4. Identify concerning excesses (> 120% RDA for limited nutrients)\n"
                "5. Prioritize gaps based on health importance\n"
                "6. Generate actionable recommendations\n"
                "\nFocus on essential nutrients: protein, fiber, vitamins C/D, calcium, iron, potassium.\n"
                "Flag excess sodium, saturated fat, and sugar."
            ),
            expected_output=(
                "A comprehensive nutrient gap analysis including:\n"
                "- List of significant nutrient deficiencies with amounts needed\n"
                "- List of concerning nutrient excesses with amounts to reduce\n"
                "- Priority ranking of nutritional issues\n"
                "- Overall nutritional completeness score\n"
                "- Specific recommendations for improvement"
            ),
            agent=self.agent,
        )

    def analyze_gaps(self, user_id: str, daily_logs: List[DailyIntakeLog]) -> NutrientGapAnalysis:
        """Analyze nutrient gaps for given daily logs."""
        logger.info(f"Analyzing nutrient gaps for user {user_id}")

        try:
            if len(daily_logs) == 1:
                # Single day analysis
                analysis = self.service.analyze_daily_gaps(user_id, daily_logs[0])
            else:
                # Multi-day analysis
                analysis = self.service.analyze_weekly_gaps(user_id, daily_logs)

            logger.info(f"Analysis complete. Overall score: {analysis.overall_score:.1f}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing nutrient gaps: {e}")
            # Return empty analysis on error
            return self.service._get_empty_analysis(user_id)

    def generate_priority_message(self, analysis: NutrientGapAnalysis) -> str:
        """Generate a priority message summarizing the most important nutrient gaps."""
        if not analysis.gaps:
            return "No nutritional data available for analysis."

        # Get significant deficiencies
        significant_deficiencies = analysis.get_significant_deficiencies(threshold=0.7)
        significant_excesses = analysis.get_significant_excesses()

        if not significant_deficiencies and not significant_excesses:
            return f"Good nutritional balance! Overall score: {analysis.overall_score:.0f}%"

        message_parts = []

        # Address top deficiencies
        if significant_deficiencies:
            top_deficiencies = significant_deficiencies[:2]  # Top 2
            deficiency_names = []
            amounts = []

            for gap in top_deficiencies:
                nutrient_name = gap.nutrient.replace("_", " ").title()
                deficiency_names.append(nutrient_name)

                # Calculate amount needed
                amount_needed = abs(gap.gap)
                if amount_needed > 1:
                    amounts.append(f"{amount_needed:.0f}g")
                else:
                    amounts.append(f"{amount_needed:.1f}g")

            if len(deficiency_names) == 1:
                message_parts.append(f"You need {amounts[0]} more {deficiency_names[0]}")
            else:
                message_parts.append(
                    f"You need {amounts[0]} more {deficiency_names[0]} and {amounts[1]} more {deficiency_names[1]}"
                )

        # Address top excesses
        if significant_excesses:
            top_excesses = significant_excesses[:1]  # Top 1
            for gap in top_excesses:
                nutrient_name = gap.nutrient.replace("_", " ").title()
                message_parts.append(f"reduce {nutrient_name}")

        if message_parts:
            return " and ".join(message_parts) + " today."

        return "Focus on balanced nutrition today."


class NutrientAuditorFlow(Flow):
    """Background flow for nutrient gap analysis."""

    def __init__(self):
        """Initialize the flow."""
        super().__init__()
        self.auditor = NutrientAuditorAgent()

    # @start()  # Commented out - not available
    def load_dietary_data(self) -> str:
        """Load dietary data for analysis."""
        logger.info(f"Loading dietary data for user {self.state.user_id}")

        try:
            # In a real implementation, this would load from database
            # For now, we'll use the provided daily_logs

            if not self.state.daily_logs:
                self.state.error_message = "No dietary data available for analysis"
                return "error"

            logger.info(f"Loaded {len(self.state.daily_logs)} days of dietary data")
            return "data_loaded"

        except Exception as e:
            logger.error(f"Error loading dietary data: {e}")
            self.state.error_message = str(e)
            return "error"

    # @listen(load_dietary_data)  # Commented out - not available
    def analyze_nutrient_gaps(self, _) -> str:
        """Analyze nutrient gaps using the auditor agent."""
        logger.info("Starting nutrient gap analysis")

        try:
            # Perform the analysis
            analysis = self.auditor.analyze_gaps(self.state.user_id, self.state.daily_logs)
            self.state.gap_analysis = analysis

            # Generate recommendations
            recommendations = self.auditor.service.get_nutrient_recommendations(analysis)
            self.state.recommendations = recommendations

            # Generate priority message
            priority_message = self.auditor.generate_priority_message(analysis)
            self.state.priority_message = priority_message

            logger.info(
                f"Analysis complete. Found {len(analysis.priority_deficiencies)} deficiencies, {len(analysis.priority_excesses)} excesses"
            )
            return "analysis_complete"

        except Exception as e:
            logger.error(f"Error during nutrient gap analysis: {e}")
            self.state.error_message = str(e)
            return "error"

    # @listen(analyze_nutrient_gaps)  # Commented out - not available
    def save_analysis_results(self, _) -> str:
        """Save analysis results for later use."""
        logger.info("Saving nutrient gap analysis results")

        try:
            # The analysis is already saved by the service
            # This step could trigger notifications or other actions

            if self.state.gap_analysis:
                logger.info(
                    f"Analysis saved for user {self.state.user_id} on {self.state.analysis_date}"
                )
                return "saved"
            else:
                return "error"

        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            self.state.error_message = str(e)
            return "error"


def create_nutrient_auditor_flow(
    user_id: str, daily_logs: List[DailyIntakeLog], analysis_date: Optional[date] = None
) -> NutrientAuditorFlow:
    """Create and configure a nutrient auditor flow."""
    flow = NutrientAuditorFlow()  # Create the flow instance

    if analysis_date is None:
        analysis_date = date.today()

    # Set initial state
    flow.state = NutrientAuditorState(
        user_id=user_id, analysis_date=analysis_date, daily_logs=daily_logs
    )

    return flow
