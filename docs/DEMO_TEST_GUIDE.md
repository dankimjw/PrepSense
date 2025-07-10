# Recipe Completion Demo Test Guide

## 🚀 Quick Start

1. **Setup Demo Data**:
   ```bash
   cd backend_gateway/scripts
   python setup_demo_data.py --reset
   ```

2. **Start Backend**:
   ```bash
   python start_backend.py
   ```

3. **Check Current Quantities**:
   ```bash
   cd backend_gateway/scripts
   python setup_demo_data.py --show
   ```

## 📱 Demo Recipes in App

### Recipe 1: Classic Spaghetti Carbonara
**Tests**: Weight conversions (g to lb), count items
- **Pasta**: 400g (pantry has 1 lb = 453g) ✅
- **Eggs**: 4 each (pantry has 12) ✅
- **Olive Oil**: 2 tbsp (pantry has 750ml) ✅
- **Salt**: 1 tsp (pantry has 500g) ✅
- **Black Pepper**: 0.5 tsp (pantry has 100g) ✅

**Expected Results**:
- Pasta: Converts 400g from 1lb (453g), leaves 53g
- Eggs: Subtracts 4, leaves 8
- Olive Oil: Converts 2 tbsp to ~30ml, leaves 720ml
- Shows conversion details in response

### Recipe 2: Chocolate Chip Cookies
**Tests**: Volume conversions (cups to ml/g), baking measurements
- **Flour**: 2.25 cups (pantry has 2.5kg) ✅
- **Butter**: 1 cup (pantry has 1 lb) ✅
- **Sugar**: 0.75 cup (pantry has 1000g) ✅
- **Eggs**: 2 each (pantry has 12) ✅
- **Vanilla**: 1 tsp (pantry has 4 fl oz) ✅

**Expected Results**:
- Flour: Converts 2.25 cups to ~530ml/265g from 2.5kg
- Butter: Converts 1 cup to ~227g from 1lb (453g)
- Sugar: Converts 0.75 cup to ~150g from 1000g
- Vanilla: Converts 1 tsp to ~5ml from 4 fl oz (118ml)

### Recipe 3: Lemon Herb Roasted Chicken
**Tests**: Direct pound matching, mixed units
- **Chicken**: 1.5 lb (pantry has 2 lb) ✅
- **Olive Oil**: 0.25 cup (pantry has 750ml) ✅
- **Salt**: 2 tsp (pantry has 500g) ✅
- **Black Pepper**: 1 tsp (pantry has 100g) ✅

**Expected Results**:
- Chicken: Direct subtraction 1.5 from 2 lb, leaves 0.5 lb
- Olive Oil: Converts 0.25 cup to ~59ml, leaves 691ml

## 🧪 Testing Steps

1. **Navigate to Recipes Tab** → **My Recipes**
2. **Select a demo recipe** (they're marked as favorites ⭐)
3. **Tap "Quick Complete"** button
4. **Confirm** when prompted about subtracting ingredients
5. **Check the response** for:
   - ✅ Updated items with quantities
   - 📐 Conversion details (e.g., "2 cups = 473.18 ml")
   - ⚠️ Any warnings about unit mismatches

## 📊 Verify Results

After completing a recipe, run:
```bash
python setup_demo_data.py --show
```

You should see reduced quantities for used ingredients.

## 🔄 Reset for Another Demo

```bash
python setup_demo_data.py --reset
```

This restores all original quantities.

## 🎯 Key Features to Highlight

1. **Smart Unit Conversion**: 
   - Recipe needs cups, pantry has ml → Automatic conversion
   - Recipe needs grams, pantry has pounds → Automatic conversion

2. **Intelligent Matching**:
   - "pasta" matches "Pasta (Spaghetti)"
   - "flour" matches "All-Purpose Flour"
   - "olive oil" matches "Olive Oil"

3. **Clear Feedback**:
   - Shows exactly what was subtracted
   - Displays conversion calculations
   - Warns about any issues

4. **Multiple Item Support**:
   - If one item isn't enough, uses multiple
   - FIFO approach (uses items with less quantity first)

## 🐛 Troubleshooting

- **"Network request failed"**: Backend not running → Run `python start_backend.py`
- **"No pantry items"**: Run setup script → `python setup_demo_data.py --reset`
- **Quantities not changing**: Check backend logs for errors