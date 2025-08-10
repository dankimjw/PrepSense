"""
Message Context Service
Extract rich context from user messages for better recipe matching
"""

import logging
import re
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class MessageContextService:
    """Extract rich context from user messages for better recipe matching"""

    def __init__(self):
        # Meal type patterns with variations
        self.meal_patterns = {
            "breakfast": [
                "breakfast",
                "morning",
                "brunch",
                "wake up",
                "start my day",
                "morning meal",
                "first meal",
                "break fast",
            ],
            "lunch": [
                "lunch",
                "midday",
                "noon",
                "work meal",
                "quick bite",
                "afternoon meal",
                "lunchtime",
                "mid-day",
            ],
            "dinner": [
                "dinner",
                "supper",
                "evening",
                "tonight",
                "family meal",
                "evening meal",
                "main meal",
                "night meal",
            ],
            "snack": [
                "snack",
                "appetizer",
                "munchies",
                "bite",
                "treat",
                "nibble",
                "finger food",
                "small bite",
                "between meals",
            ],
            "dessert": [
                "dessert",
                "sweet",
                "cake",
                "cookie",
                "after dinner",
                "sweet treat",
                "pudding",
                "ice cream",
                "pie",
            ],
        }

        # Time constraint patterns
        self.time_patterns = {
            "quick": [
                "quick",
                "fast",
                "hurry",
                "instant",
                "speedy",
                "rapid",
                "swift",
                "express",
                "asap",
                "short time",
                "in a rush",
                "pressed for time",
                "minimal time",
            ],
            "medium": [
                "normal",
                "regular",
                "standard",
                "typical",
                "usual",
                "moderate time",
                "reasonable time",
            ],
            "leisurely": [
                "slow",
                "weekend",
                "elaborate",
                "fancy",
                "special",
                "take my time",
                "no rush",
                "lazy",
                "relaxed",
                "sunday",
                "holiday",
                "celebration",
            ],
        }

        # Health and dietary focus patterns
        self.health_patterns = {
            "healthy": [
                "healthy",
                "nutritious",
                "light",
                "fresh",
                "clean",
                "wholesome",
                "balanced",
                "good for me",
                "diet friendly",
                "low fat",
                "low sodium",
                "heart healthy",
            ],
            "comfort": [
                "comfort",
                "hearty",
                "filling",
                "cozy",
                "satisfying",
                "soul food",
                "homestyle",
                "rich",
                "indulgent",
                "warming",
                "stick to your ribs",
            ],
            "diet": [
                "diet",
                "low calorie",
                "weight loss",
                "lean",
                "fit",
                "slim",
                "light",
                "calorie conscious",
                "portion control",
                "watching my weight",
                "cutting calories",
            ],
        }

        # Cuisine patterns
        self.cuisine_patterns = {
            "italian": ["italian", "pasta", "pizza", "risotto", "marinara"],
            "mexican": ["mexican", "taco", "burrito", "salsa", "quesadilla"],
            "chinese": ["chinese", "stir fry", "wok", "kung pao", "lo mein"],
            "japanese": ["japanese", "sushi", "ramen", "teriyaki", "tempura"],
            "indian": ["indian", "curry", "tikka", "masala", "tandoori"],
            "thai": ["thai", "pad thai", "green curry", "tom yum"],
            "mediterranean": ["mediterranean", "greek", "hummus", "falafel"],
            "american": ["american", "burger", "bbq", "sandwich", "classic"],
        }

        # Cooking method patterns
        self.cooking_methods = {
            "baked": ["bake", "baked", "oven", "roast", "roasted"],
            "grilled": ["grill", "grilled", "bbq", "barbecue", "char"],
            "fried": ["fry", "fried", "pan-fried", "deep-fried", "crispy"],
            "steamed": ["steam", "steamed", "healthy", "light cooking"],
            "slow_cooked": ["slow cook", "crock pot", "stew", "braised"],
            "raw": ["raw", "no cook", "fresh", "salad", "uncooked"],
        }

        # Special occasion patterns
        self.occasion_patterns = {
            "party": ["party", "guests", "entertaining", "gathering", "crowd"],
            "romantic": ["date", "romantic", "special someone", "two of us"],
            "family": ["family", "kids", "children", "family-friendly"],
            "meal_prep": ["meal prep", "batch", "week ahead", "prepare ahead"],
        }

    def extract_context(self, message: str, time_of_day: Optional[datetime] = None) -> dict:
        """
        Extract comprehensive context from user message

        Args:
            message: User's message
            time_of_day: Current time for context

        Returns:
            Dictionary with extracted context
        """
        message_lower = message.lower()

        # Remove extra whitespace and normalize
        message_lower = " ".join(message_lower.split())

        context = {
            "meal_type": self._detect_meal_type(message_lower, time_of_day),
            "time_constraint": self._extract_time_constraint(message_lower),
            "health_focus": self._detect_health_intent(message_lower),
            "cuisine_hints": self._extract_cuisine_hints(message_lower),
            "ingredient_focus": self._extract_ingredient_focus(message_lower),
            "serving_info": self._extract_serving_info(message_lower),
            "cooking_method": self._extract_cooking_method(message_lower),
            "occasion": self._detect_occasion(message_lower),
            "dietary_overrides": self._extract_dietary_overrides(message_lower),
            "special_requirements": self._extract_special_requirements(message_lower),
            "expiring_focus": self._detect_expiring_intent(message_lower),
            "user_mood": self._detect_user_mood(message_lower),
        }

        # Log extracted context for debugging
        logger.info(f"Extracted context from '{message[:50]}...': {context}")

        return context

    def _detect_meal_type(self, message: str, time_of_day: Optional[datetime]) -> str:
        """Detect meal type with time-based defaults"""
        # Check explicit mentions
        for meal_type, patterns in self.meal_patterns.items():
            if any(pattern in message for pattern in patterns):
                return meal_type

        # Use time of day as hint
        if time_of_day:
            hour = time_of_day.hour
            if 5 <= hour < 11:
                return "breakfast"
            elif 11 <= hour < 15:
                return "lunch"
            elif 15 <= hour < 17:
                return "snack"
            elif 17 <= hour < 21:
                return "dinner"
            else:
                return "snack"

        # Check for meal-specific ingredients as hints
        breakfast_ingredients = ["egg", "bacon", "cereal", "oatmeal", "pancake"]
        if any(ing in message for ing in breakfast_ingredients):
            return "breakfast"

        return "dinner"  # default

    def _extract_time_constraint(self, message: str) -> dict:
        """Extract cooking time preferences"""
        # Check for specific time mentions
        time_patterns = [
            (r"(\d+)\s*(?:min|minute)s?", "minutes"),
            (r"(\d+)\s*(?:hr|hour)s?", "hours"),
            (r"under\s*(\d+)\s*(?:min|minute)s?", "max_minutes"),
            (r"less\s*than\s*(\d+)\s*(?:min|minute)s?", "max_minutes"),
        ]

        for pattern, unit in time_patterns:
            match = re.search(pattern, message)
            if match:
                value = int(match.group(1))
                if unit == "hours":
                    value *= 60  # Convert to minutes

                # Determine preference based on time
                if value <= 20:
                    preference = "quick"
                elif value <= 45:
                    preference = "medium"
                else:
                    preference = "leisurely"

                return {"max_minutes": value, "preference": preference, "explicit_time": True}

        # Check for qualitative time
        for time_type, patterns in self.time_patterns.items():
            if any(pattern in message for pattern in patterns):
                max_times = {"quick": 20, "medium": 45, "leisurely": 120}
                return {
                    "max_minutes": max_times.get(time_type, 45),
                    "preference": time_type,
                    "explicit_time": False,
                }

        return {"max_minutes": 60, "preference": "medium", "explicit_time": False}

    def _detect_health_intent(self, message: str) -> Optional[str]:
        """Detect health-related intent in the message"""
        for health_type, patterns in self.health_patterns.items():
            if any(pattern in message for pattern in patterns):
                return health_type
        return None

    def _extract_cuisine_hints(self, message: str) -> list[str]:
        """Extract cuisine preferences from message"""
        cuisines = []
        for cuisine, patterns in self.cuisine_patterns.items():
            if any(pattern in message for pattern in patterns):
                cuisines.append(cuisine)
        return cuisines

    def _extract_ingredient_focus(self, message: str) -> list[str]:
        """Extract specific ingredients user wants to use"""
        ingredients = []

        # Patterns for ingredient extraction
        patterns = [
            r"using\s+(\w+(?:\s+\w+)?)",
            r"with\s+(\w+(?:\s+\w+)?)",
            r"make\s+(?:a\s+)?(?:recipe\s+)?with\s+(\w+(?:\s+\w+)?)",
            r"recipe\s+for\s+(\w+(?:\s+\w+)?)",
            r"cook\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
            r"use\s+(?:up\s+)?(?:the\s+)?(\w+(?:\s+\w+)?)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, message)
            ingredients.extend(matches)

        # Clean and deduplicate
        cleaned_ingredients = []
        seen = set()

        # Common words to exclude
        exclude_words = {
            "something",
            "anything",
            "recipe",
            "meal",
            "dish",
            "food",
            "breakfast",
            "lunch",
            "dinner",
            "snack",
            "quick",
            "easy",
            "healthy",
            "delicious",
            "tasty",
            "good",
            "nice",
            "great",
        }

        for ing in ingredients:
            ing_clean = ing.strip().lower()
            if ing_clean not in exclude_words and ing_clean not in seen:
                seen.add(ing_clean)
                cleaned_ingredients.append(ing_clean)

        return cleaned_ingredients

    def _extract_serving_info(self, message: str) -> dict:
        """Extract serving size information"""
        serving_info = {"servings": 4, "meal_prep": False, "leftovers_ok": True}  # default

        # Look for serving numbers
        serving_patterns = [
            (r"for\s+(\d+)\s*(?:people|persons?|servings?)?", "servings"),
            (r"serve(?:s)?\s+(\d+)", "servings"),
            (r"(\d+)\s*servings?", "servings"),
            (r"feed(?:s)?\s+(\d+)", "servings"),
        ]

        for pattern, _key in serving_patterns:
            match = re.search(pattern, message)
            if match:
                serving_info["servings"] = int(match.group(1))
                break

        # Check for meal prep intent
        if any(phrase in message for phrase in ["meal prep", "batch", "week ahead", "freeze"]):
            serving_info["meal_prep"] = True
            serving_info["servings"] = max(serving_info["servings"], 8)  # Increase for meal prep

        # Check for single serving
        if any(
            phrase in message
            for phrase in ["just for me", "single serving", "one person", "myself"]
        ):
            serving_info["servings"] = 1
            serving_info["leftovers_ok"] = False

        return serving_info

    def _extract_cooking_method(self, message: str) -> Optional[str]:
        """Extract preferred cooking method"""
        for method, patterns in self.cooking_methods.items():
            if any(pattern in message for pattern in patterns):
                return method
        return None

    def _detect_occasion(self, message: str) -> Optional[str]:
        """Detect special occasion context"""
        for occasion, patterns in self.occasion_patterns.items():
            if any(pattern in message for pattern in patterns):
                return occasion
        return None

    def _extract_dietary_overrides(self, message: str) -> list[str]:
        """Extract temporary dietary preferences from message"""
        dietary_overrides = []

        dietary_patterns = {
            "vegetarian": ["vegetarian", "veggie", "no meat", "meatless"],
            "vegan": ["vegan", "plant based", "no animal", "dairy free"],
            "gluten_free": ["gluten free", "no gluten", "celiac"],
            "low_carb": ["low carb", "keto", "no carbs", "carb free"],
            "paleo": ["paleo", "caveman", "primal"],
            "dairy_free": ["dairy free", "no dairy", "lactose free"],
        }

        for diet, patterns in dietary_patterns.items():
            if any(pattern in message for pattern in patterns):
                dietary_overrides.append(diet)

        return dietary_overrides

    def _extract_special_requirements(self, message: str) -> dict:
        """Extract any special requirements or constraints"""
        requirements = {
            "no_shopping": False,
            "use_leftovers": False,
            "one_pot": False,
            "no_cleanup": False,
            "kid_friendly": False,
            "budget_conscious": False,
        }

        # Check for no shopping requirement
        if any(
            phrase in message
            for phrase in [
                "no shopping",
                "dont buy",
                "don't buy",
                "only what i have",
                "without shopping",
                "no store",
                "already have",
            ]
        ):
            requirements["no_shopping"] = True

        # Check for leftover usage
        if any(phrase in message for phrase in ["leftover", "use up", "finish"]):
            requirements["use_leftovers"] = True

        # Check for one-pot meals
        if any(
            phrase in message for phrase in ["one pot", "one pan", "single pot", "easy cleanup"]
        ):
            requirements["one_pot"] = True
            requirements["no_cleanup"] = True

        # Check for kid-friendly
        if any(phrase in message for phrase in ["kids", "children", "family", "picky eater"]):
            requirements["kid_friendly"] = True

        # Check for budget
        if any(phrase in message for phrase in ["budget", "cheap", "affordable", "save money"]):
            requirements["budget_conscious"] = True

        return requirements

    def _detect_expiring_intent(self, message: str) -> bool:
        """Check if user wants to use expiring ingredients"""
        expiring_phrases = [
            "expiring",
            "expire",
            "going bad",
            "use soon",
            "about to expire",
            "spoil",
            "use up",
            "before it goes bad",
            "need to use",
        ]
        return any(phrase in message for phrase in expiring_phrases)

    def _detect_user_mood(self, message: str) -> Optional[str]:
        """Detect user's mood or emotional state"""
        mood_patterns = {
            "stressed": ["stressed", "exhausted", "tired", "long day", "rough day"],
            "celebratory": ["celebrate", "special", "birthday", "anniversary"],
            "adventurous": ["try something new", "experiment", "different", "unique"],
            "nostalgic": ["childhood", "comfort", "grandma", "traditional", "classic"],
            "lazy": ["lazy", "dont feel like", "don't want to cook", "minimal effort"],
        }

        for mood, patterns in mood_patterns.items():
            if any(pattern in message for pattern in patterns):
                return mood

        return None

    def get_response_tone(self, context: dict) -> str:
        """
        Determine appropriate response tone based on context

        Args:
            context: Extracted context dictionary

        Returns:
            Suggested tone for response
        """
        mood = context.get("user_mood")

        if mood == "stressed":
            return "supportive"
        elif mood == "celebratory":
            return "enthusiastic"
        elif mood == "adventurous":
            return "encouraging"
        elif mood == "lazy":
            return "understanding"

        # Default based on other factors
        if context.get("health_focus") == "diet":
            return "motivational"
        elif context.get("occasion") == "party":
            return "festive"
        elif context.get("time_constraint", {}).get("preference") == "quick":
            return "efficient"

        return "friendly"  # default
