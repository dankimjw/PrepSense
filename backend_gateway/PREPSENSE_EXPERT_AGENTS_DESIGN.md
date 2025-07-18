# PrepSense Multi-Expert Agent System Design

## Core Principle: "Consulting a Team of Experts"

Instead of technical agents (Pantry Scanner, Filter, etc.), we design agents that represent actual human experts you'd consult for comprehensive meal planning.

## Expert Agent Team

### 1. 👨‍⚕️ **Clinical Nutritionist Agent**
**Human Equivalent**: Licensed nutritionist who reviews medical history
```python
Role: "Medical Nutrition Therapist"
Expertise:
- Manages dietary requirements for health conditions
- Reviews medications for food interactions
- Monitors nutritional deficiencies
- Creates therapeutic meal plans

Input: {
    "user_health_profile": {
        "conditions": ["diabetes", "hypertension"],
        "medications": ["metformin", "lisinopril"],
        "lab_results": {"A1C": 7.2, "cholesterol": 220}
    },
    "family_members": [...]
}

Output: {
    "dietary_requirements": {
        "must_limit": ["sodium < 2300mg", "added_sugars < 25g"],
        "must_include": ["fiber > 30g", "potassium-rich foods"],
        "meal_timing": "3 meals + 2 snacks for blood sugar"
    },
    "red_flags": ["Avoid grapefruit with medications"],
    "monitoring_plan": "Check blood sugar before/after new recipes"
}
```

### 2. 👩‍🍳 **Executive Chef Agent**
**Human Equivalent**: Professional chef who adapts recipes for families
```python
Role: "Family Meal Planning Chef"
Expertise:
- Modifies recipes for different dietary needs
- Suggests cooking techniques for health
- Plans efficient meal prep
- Creates kid-friendly versions

Input: {
    "dietary_requirements": {...},  # From Nutritionist
    "family_preferences": {
        "mom": ["spicy food", "asian cuisine"],
        "dad": ["no mushrooms", "likes grilled"],
        "teen": ["vegetarian", "loves pasta"],
        "toddler": ["finger foods", "mild flavors"]
    },
    "available_ingredients": [...],
    "time_constraints": "30 min weekdays, 1hr weekends"
}

Output: {
    "weekly_meal_plan": {
        "monday": {
            "dinner": "Deconstructed Taco Bar",
            "why": "Everyone can customize; toddler gets mild version",
            "variations": {
                "dad": "Low-carb lettuce wraps",
                "teen": "Black bean version",
                "toddler": "Cheese quesadilla with hidden veggies"
            }
        }
    },
    "prep_schedule": "Sunday: prep proteins, cut veggies",
    "cooking_techniques": ["Grill proteins for dad", "Steam for toddler"]
}
```

### 3. 🏃‍♀️ **Sports Nutritionist Agent**
**Human Equivalent**: Expert in performance nutrition
```python
Role: "Performance Nutrition Specialist"
Expertise:
- Times nutrition with training schedules
- Optimizes recovery meals
- Manages competition day nutrition
- Balances family meals with athlete needs

Input: {
    "athlete_profile": {
        "sport": "marathon",
        "training_phase": "peak week",
        "schedule": "6am runs, 20 miles Saturday"
    }
}

Output: {
    "performance_modifications": {
        "pre_run": "Banana + toast 30min before",
        "post_run": "Chocolate milk within 30min",
        "dinner_adjustments": "+50% carbs on long run days",
        "family_integration": "Make pasta, add extra portion for athlete"
    }
}
```

### 4. 👶 **Pediatric Nutrition Agent**
**Human Equivalent**: Child nutrition specialist
```python
Role: "Pediatric Dietitian"
Expertise:
- Age-appropriate portions and nutrients
- Picky eater strategies
- Hidden vegetable techniques
- Development-supporting foods

Input: {
    "children": [
        {"age": 3, "issues": ["picky", "low iron"], "growth_percentile": 45},
        {"age": 15, "issues": ["acne", "vegetarian"], "activity": "high"}
    ]
}

Output: {
    "child_strategies": {
        "toddler": {
            "iron_sources": ["Meatballs with hidden liver", "Fortified cereal"],
            "presentation": "Fun shapes, dipping sauces",
            "portion_sizes": "1 tbsp per year of age"
        },
        "teen": {
            "skin_health": "Limit dairy, increase omega-3s",
            "protein_needs": "65g/day from plants",
            "independence": "Teach meal prep for after-school"
        }
    }
}
```

### 5. 🧠 **Behavioral Nutrition Agent**
**Human Equivalent**: Eating psychology expert
```python
Role: "Nutrition Psychologist"
Expertise:
- Family mealtime dynamics
- Emotional eating patterns
- Habit formation
- Sustainable change strategies

Input: {
    "family_challenges": [
        "Dad stress-eats at night",
        "Teen skips breakfast",
        "Toddler tantrums at dinner",
        "Different schedules"
    ],
    "goals": ["Family dinners 4x/week", "Reduce food waste"]
}

Output: {
    "behavioral_strategies": {
        "family_meals": "Start with 2 dinners, build up",
        "dad_evening": "Prep portioned snacks, herbal tea ritual",
        "teen_breakfast": "Grab-and-go stations",
        "toddler_tips": "Involve in cooking, choice of 2 vegetables",
        "implementation": "Weekly family meal planning meeting"
    }
}
```

### 6. 💰 **Budget Dietitian Agent**
**Human Equivalent**: Expert in economical healthy eating
```python
Role: "Budget Nutrition Specialist"
Expertise:
- Cost-effective healthy meals
- Bulk buying strategies
- Seasonal menu planning
- Minimizing food waste

Input: {
    "budget": "$200/week for 4",
    "dietary_needs": {...},
    "local_prices": {...},
    "storage_space": "standard + chest freezer"
}

Output: {
    "budget_strategy": {
        "bulk_buys": ["Brown rice", "Frozen vegetables", "Whole chickens"],
        "weekly_shopping": {
            "proteins": "$60 - rotate sales",
            "produce": "$50 - seasonal focus",
            "staples": "$40 - bulk monthly",
            "extras": "$50 - dairy, eggs, bread"
        },
        "cost_saving_swaps": {
            "Pine nuts → Sunflower seeds",
            "Fresh berries → Frozen in smoothies"
        },
        "batch_cooking": "Sunday: 3 proteins, 2 grains, prep veggies"
    }
}
```

### 7. 🌍 **Cultural Food Agent**
**Human Equivalent**: Cultural cuisine expert
```python
Role: "Cultural Cuisine Specialist"
Expertise:
- Authentic cultural recipes
- Dietary adaptation of traditional foods
- Fusion cuisine for mixed families
- Teaching food heritage

Input: {
    "cultural_backgrounds": ["Korean", "Italian"],
    "traditions": ["Sunday pasta", "Kimchi making"],
    "dietary_conflicts": ["Grandma's recipes all have gluten"]
}

Output: {
    "cultural_adaptations": {
        "preserved_traditions": {
            "sunday_pasta": "Gluten-free version that Nonna approves",
            "kimchi": "Low-sodium version for dad"
        },
        "fusion_ideas": "Korean-Italian fusion: Gochujang marinara",
        "teaching_moments": "Monthly cultural cooking with kids"
    }
}
```

### 8. 🚨 **Food Safety Agent**
**Human Equivalent**: Food safety inspector
```python
Role: "Food Safety Expert"
Expertise:
- Expiration management
- Safe food handling
- Allergen cross-contamination
- Storage optimization

Input: {
    "pantry_items": [...],
    "allergies": ["severe nut allergy"],
    "storage_conditions": "Hot climate, power outages common"
}

Output: {
    "safety_protocols": {
        "expiration_alerts": {
            "urgent": ["Chicken - use today", "Milk - 2 days"],
            "planning": ["Yogurt - use in smoothies this week"]
        },
        "allergy_safety": {
            "separate_cutting_boards": true,
            "storage": "Nuts in sealed container, top shelf",
            "emergency_plan": "EpiPen locations, hospital route"
        },
        "power_outage_plan": "Cooler ready, ice packs frozen"
    }
}
```

## How These Agents Collaborate

### Example: "Plan our meals for next week"

```python
1. Clinical Nutritionist → Reviews health needs
   "Dad needs low sodium, Mom needs high protein..."

2. Pediatric Nutrition → Adds child requirements
   "Toddler needs iron, teen needs calcium alternatives..."

3. Sports Nutritionist → Overlays training needs
   "Mom has long run Saturday, carb-load Friday..."

4. Budget Dietitian → Checks financial constraints
   "Here's how to meet all needs within $200..."

5. Executive Chef → Creates meal plan
   "Deconstructed meals for customization..."

6. Cultural Food Agent → Incorporates traditions
   "Sunday pasta with gluten-free option..."

7. Behavioral Nutrition → Adds implementation strategy
   "Prep Sunday, teen helps Wednesday..."

8. Food Safety Agent → Final safety check
   "Use chicken Monday, freeze portion for Thursday..."

Result: Comprehensive weekly plan addressing ALL family needs
```

## When This Multi-Agent System Makes Sense

### ✅ **Complex Family Scenarios**
- Multiple health conditions
- Different life stages
- Cultural considerations
- Budget constraints
- Time limitations

### ✅ **Health Journey Support**
- New diagnosis requiring diet change
- Weight loss for whole family
- Athletic performance + family meals
- Managing multiple allergies

### ✅ **Life Transitions**
- New baby (feeding family + infant)
- Teen athlete + aging parents
- Moving to new country (finding ingredients)
- Divorce (cooking for one → family)

## Implementation Benefits

1. **Each agent is truly specialized** (not just doing DB queries)
2. **Agents debate and negotiate** (Chef vs Nutritionist vs Budget)
3. **Holistic solutions** (not just "here's recipes")
4. **Personalized strategies** (behavioral change, not just meal lists)
5. **Educational value** (learn from expert reasoning)

## The Key Difference

**Old Design**: Technical agents doing simple tasks
```
Pantry Scanner → "Here's what's in your pantry"
Filter → "Here's what's not expired"
Recipe Finder → "Here's matching recipes"
```

**New Design**: Expert agents providing consultation
```
Clinical Nutritionist → "Given your diabetes, prioritize these foods..."
Executive Chef → "Here's how to make one meal work for everyone..."
Behavioral Expert → "Here's why your teen skips breakfast and how to fix it..."
```

This is when CrewAI shines - when you're truly orchestrating multiple experts who need to collaborate, negotiate, and build on each other's expertise to solve complex, multifaceted problems.