"""Pydantic models for nutrition and dietary intake tracking."""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Union
from datetime import datetime, date
from enum import Enum

class MealType(str, Enum):
    """Types of meals for dietary logging."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    BEVERAGE = "beverage"

class NutrientProfile(BaseModel):
    """Comprehensive nutrient profile for foods/recipes."""
    # Macronutrients (grams)
    protein: float = 0.0
    carbohydrates: float = 0.0
    fiber: float = 0.0
    total_fat: float = 0.0
    saturated_fat: float = 0.0
    trans_fat: float = 0.0
    sugar: float = 0.0
    
    # Vitamins (mg unless noted)
    vitamin_c: float = 0.0
    vitamin_a: float = 0.0
    vitamin_d: float = 0.0
    vitamin_e: float = 0.0
    vitamin_k: float = 0.0
    thiamin: float = 0.0
    riboflavin: float = 0.0
    niacin: float = 0.0
    vitamin_b6: float = 0.0
    folate: float = 0.0
    vitamin_b12: float = 0.0
    
    # Minerals (mg unless noted)
    calcium: float = 0.0
    iron: float = 0.0
    magnesium: float = 0.0
    phosphorus: float = 0.0
    potassium: float = 0.0
    sodium: float = 0.0
    zinc: float = 0.0
    copper: float = 0.0
    selenium: float = 0.0
    
    # Special nutrients
    cholesterol: float = 0.0
    omega_3: float = 0.0
    omega_6: float = 0.0
    
    # Energy
    calories: float = 0.0
    
    def __add__(self, other: 'NutrientProfile') -> 'NutrientProfile':
        """Add two nutrient profiles together."""
        result = NutrientProfile()
        for field in self.__fields__:
            setattr(result, field, getattr(self, field) + getattr(other, field))
        return result
    
    def __mul__(self, factor: float) -> 'NutrientProfile':
        """Multiply nutrient profile by a factor (for serving size adjustments)."""
        result = NutrientProfile()
        for field in self.__fields__:
            setattr(result, field, getattr(self, field) * factor)
        return result
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON storage."""
        return {field: getattr(self, field) for field in self.__fields__}

class FoodItem(BaseModel):
    """Individual food item with nutritional information."""
    name: str
    usda_id: Optional[str] = None
    brand: Optional[str] = None
    serving_size: float = 1.0
    serving_unit: str = "serving"
    nutrients: NutrientProfile = Field(default_factory=NutrientProfile)
    
    def get_nutrients_per_serving(self, serving_amount: float = 1.0) -> NutrientProfile:
        """Get nutrients adjusted for serving amount."""
        return self.nutrients * (serving_amount / self.serving_size)

class MealEntry(BaseModel):
    """Individual meal entry in dietary log."""
    id: Optional[str] = None
    meal_type: MealType
    food_item: FoodItem
    quantity: float = 1.0
    logged_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
    
    def get_total_nutrients(self) -> NutrientProfile:
        """Get total nutrients for this meal entry."""
        return self.food_item.get_nutrients_per_serving(self.quantity)

class DailyIntakeLog(BaseModel):
    """Daily dietary intake log for a user."""
    user_id: str
    date: date
    meals: List[MealEntry] = Field(default_factory=list)
    total_water: float = 0.0  # liters
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_total_nutrients(self) -> NutrientProfile:
        """Calculate total nutrients for the day."""
        total = NutrientProfile()
        for meal in self.meals:
            total = total + meal.get_total_nutrients()
        return total
    
    def get_nutrients_by_meal_type(self, meal_type: MealType) -> NutrientProfile:
        """Get nutrients for a specific meal type."""
        total = NutrientProfile()
        for meal in self.meals:
            if meal.meal_type == meal_type:
                total = total + meal.get_total_nutrients()
        return total

class NutrientGap(BaseModel):
    """Nutrient gap analysis for a user."""
    nutrient: str
    consumed: float
    recommended: float
    gap: float  # negative = deficit, positive = excess
    percentage_met: float
    is_deficient: bool
    is_excessive: bool
    priority: str = "medium"  # low, medium, high
    
    @field_validator('percentage_met')
    @classmethod
    def calculate_percentage(cls, v, values):
        if 'consumed' in values and 'recommended' in values:
            recommended = values['recommended']
            if recommended > 0:
                return (values['consumed'] / recommended) * 100
        return 0.0

class NutrientGapAnalysis(BaseModel):
    """Complete nutrient gap analysis for a user."""
    user_id: str
    analysis_date: date
    period_days: int = 1  # Analysis period (1 = single day, 7 = weekly average)
    gaps: List[NutrientGap] = Field(default_factory=list)
    priority_deficiencies: List[str] = Field(default_factory=list)
    priority_excesses: List[str] = Field(default_factory=list)
    overall_score: float = 0.0  # 0-100 nutritional completeness score
    created_at: datetime = Field(default_factory=datetime.now)
    
    def get_gap_by_nutrient(self, nutrient: str) -> Optional[NutrientGap]:
        """Get gap for a specific nutrient."""
        for gap in self.gaps:
            if gap.nutrient == nutrient:
                return gap
        return None
    
    def get_significant_deficiencies(self, threshold: float = 0.7) -> List[NutrientGap]:
        """Get nutrients with significant deficiencies."""
        return [gap for gap in self.gaps 
                if gap.is_deficient and gap.percentage_met < (threshold * 100)]
    
    def get_significant_excesses(self) -> List[NutrientGap]:
        """Get nutrients with significant excesses."""
        return [gap for gap in self.gaps if gap.is_excessive]

class RecipeNutrientScore(BaseModel):
    """Nutrient-based scoring for a recipe."""
    recipe_id: str
    gap_closure_score: float = 0.0  # How well recipe addresses nutrient gaps
    balance_score: float = 0.0  # How balanced the recipe is nutritionally
    health_score: float = 0.0  # Overall health score
    addressed_deficiencies: List[str] = Field(default_factory=list)
    created_excesses: List[str] = Field(default_factory=list)
    total_score: float = 0.0
    
    def calculate_total_score(self) -> float:
        """Calculate total nutrient score."""
        # Weighted combination of scores
        self.total_score = (
            self.gap_closure_score * 0.5 +
            self.balance_score * 0.3 +
            self.health_score * 0.2
        )
        return self.total_score

# Request/Response models for API

class LogMealRequest(BaseModel):
    """Request to log a meal."""
    meal_type: MealType
    food_name: str
    quantity: float = 1.0
    serving_unit: str = "serving"
    brand: Optional[str] = None
    notes: Optional[str] = None

class LogMealResponse(BaseModel):
    """Response after logging a meal."""
    meal_id: str
    nutrients_added: NutrientProfile
    daily_total: NutrientProfile
    message: str

class GetNutrientGapsRequest(BaseModel):
    """Request to get nutrient gaps."""
    user_id: str
    analysis_date: Optional[date] = None
    period_days: int = 1

class GetNutrientGapsResponse(BaseModel):
    """Response with nutrient gap analysis."""
    analysis: NutrientGapAnalysis
    recommendations: List[str] = Field(default_factory=list)
    priority_message: Optional[str] = None

class NutrientAwareRecipeRequest(BaseModel):
    """Request for nutrient-aware recipe recommendations."""
    user_id: str
    include_nutrient_gaps: bool = True
    focus_nutrients: Optional[List[str]] = None
    meal_type: Optional[MealType] = None
    max_recipes: int = 5