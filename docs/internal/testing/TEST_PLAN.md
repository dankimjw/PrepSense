# PrepSense Test Plan

## Comprehensive Testing Guide for v2.0 Features

This document outlines the testing procedures for all features in PrepSense v2.0.

## Pre-Testing Setup

### 1. Environment Setup
```bash
# Backend
cd /Users/danielkim/_Capstone/PrepSense
source venv/bin/activate
python run_app.py

# Frontend (new terminal)
cd ios-app
npx expo start --ios
```

### 2. Verify Services
- Backend API: http://localhost:8001/docs
- iOS App: Should launch in simulator
- Database: PostgreSQL should be running

---

## Feature Test Cases

### 1. OCR Receipt Scanner

#### Test Case 1.1: Camera Capture
**Steps**:
1. Open app → Tap "+" button
2. Select "Scan Receipt"
3. Tap "Take Photo"
4. Capture a receipt image
5. Wait for processing

**Expected Results**:
- ✅ Camera opens correctly
- ✅ Image captures and displays
- ✅ "Scanning receipt..." overlay appears
- ✅ Items are extracted and displayed

#### Test Case 1.2: Gallery Selection
**Steps**:
1. Open app → Tap "+" button
2. Select "Scan Receipt"
3. Tap "Choose from Gallery"
4. Select a receipt image
5. Review extracted items

**Expected Results**:
- ✅ Gallery opens
- ✅ Selected image displays
- ✅ Items extracted with name, quantity, unit
- ✅ Categories auto-assigned

#### Test Case 1.3: Edit Scanned Items
**Steps**:
1. After scanning, tap edit icon on any item
2. Change name to "Test Item"
3. Change quantity to 5
4. Change unit to "kg"
5. Tap "Save"

**Expected Results**:
- ✅ Edit modal opens
- ✅ Changes reflect in list
- ✅ Original items unchanged

#### Test Case 1.4: Add to Pantry
**Steps**:
1. Deselect one item
2. Tap "Add X Items"
3. Check pantry tab

**Expected Results**:
- ✅ Only selected items added
- ✅ Success message appears
- ✅ Items appear in pantry with correct details

---

### 2. Recipe Completion Modal

#### Test Case 2.1: Basic Completion
**Steps**:
1. Navigate to any recipe with available ingredients
2. Tap "Quick Complete"
3. Leave sliders at default (100%)
4. Tap "Complete Recipe"

**Expected Results**:
- ✅ Modal shows all available ingredients
- ✅ Quantities display correctly
- ✅ Pantry updates with reduced quantities
- ✅ Success message shows summary

#### Test Case 2.2: Partial Usage
**Steps**:
1. Open recipe → "Quick Complete"
2. Adjust first ingredient to 50%
3. Adjust second ingredient to 0%
4. Complete recipe

**Expected Results**:
- ✅ Only 50% deducted from first item
- ✅ Nothing deducted from second item
- ✅ Other items deducted 100%

#### Test Case 2.3: Insufficient Quantities
**Steps**:
1. Find recipe with limited ingredients
2. Quick Complete
3. Set usage > available amount
4. Complete

**Expected Results**:
- ✅ Warning shows for insufficient items
- ✅ Available amount used
- ✅ Item reaches 0 in pantry

---

### 3. Bookmark & Rating System

#### Test Case 3.1: Bookmark Recipe
**Steps**:
1. Open any recipe detail
2. Tap bookmark icon
3. Navigate away and return
4. Check bookmark state

**Expected Results**:
- ✅ Icon changes to filled bookmark
- ✅ State persists after navigation
- ✅ Recipe saved to user collection

#### Test Case 3.2: Rate Recipe
**Steps**:
1. Open recipe detail
2. Tap thumbs up
3. Tap thumbs up again (toggle off)
4. Tap thumbs down

**Expected Results**:
- ✅ Thumbs up highlights green
- ✅ Second tap returns to neutral
- ✅ Thumbs down highlights red
- ✅ Only one rating active at a time

#### Test Case 3.3: Rating Persistence
**Steps**:
1. Rate a recipe thumbs up
2. Close app completely
3. Reopen and find same recipe
4. Check rating state

**Expected Results**:
- ✅ Rating persists
- ✅ Correct icon highlighted

---

### 4. Enhanced Unit Validation

#### Test Case 4.1: Count Unit Validation
**Steps**:
1. Edit pantry item
2. Select "each" as unit
3. Try entering 1.5
4. Try entering 2

**Expected Results**:
- ✅ Error for decimal with "each"
- ✅ Whole number accepted
- ✅ Clear error message

#### Test Case 4.2: Unit Switching
**Steps**:
1. Edit item with 2.5 kg
2. Switch to "package"
3. Observe prompt

**Expected Results**:
- ✅ Alert about rounding
- ✅ Quantity rounds to 3
- ✅ Can proceed or cancel

#### Test Case 4.3: Range Validation
**Steps**:
1. Set unit to "ml"
2. Enter 15000
3. Observe warning

**Expected Results**:
- ✅ Suggestion to use liters
- ✅ Can still save if desired

---

### 5. AI Meal Type Detection

#### Test Case 5.1: Breakfast Query
**Steps**:
1. Open chat
2. Type "What can I make for breakfast?"
3. Review suggestions

**Expected Results**:
- ✅ Breakfast recipes returned
- ✅ No dinner/dessert recipes

#### Test Case 5.2: Dinner Query
**Steps**:
1. Chat: "Quick dinner ideas"
2. Review results

**Expected Results**:
- ✅ Dinner-appropriate recipes
- ✅ 20-30 minute cook times

---

### 6. Stats Dashboard

#### Test Case 6.1: Time Period Switching
**Steps**:
1. Navigate to Stats tab
2. Select "Week"
3. Select "Month"
4. Select "Year"

**Expected Results**:
- ✅ Data updates for each period
- ✅ Charts redraw
- ✅ Counts change appropriately

#### Test Case 6.2: Pantry Analytics
**Steps**:
1. Stats tab
2. Check pantry section
3. Tap "Total Items"

**Expected Results**:
- ✅ Correct item count
- ✅ Modal shows all items
- ✅ Expired items highlighted

#### Test Case 6.3: Environmental Impact
**Steps**:
1. Check sustainability section
2. Toggle metric/imperial
3. Verify calculations

**Expected Results**:
- ✅ Food saved in kg/lbs
- ✅ CO2 calculations update
- ✅ Units convert correctly

---

### 7. User Preferences

#### Test Case 7.1: Set Preferences
**Steps**:
1. Tap user icon in header
2. Select "Vegetarian"
3. Add "Nuts" allergy
4. Select "Italian" cuisine
5. Close modal

**Expected Results**:
- ✅ Selections save
- ✅ Pills show correctly
- ✅ Persists on reopen

#### Test Case 7.2: Preference Impact
**Steps**:
1. Set vegetarian preference
2. Open chat
3. Ask for recipe suggestions

**Expected Results**:
- ✅ Only vegetarian recipes
- ✅ No meat ingredients
- ✅ Preferences mentioned in response

---

### 8. Shopping List Integration

#### Test Case 8.1: Missing Ingredients Flow
**Steps**:
1. Open recipe with missing items
2. Start cooking
3. Select "Add to Shopping List"
4. Select specific items
5. Add to list

**Expected Results**:
- ✅ Routes to selection screen
- ✅ Can toggle items
- ✅ Only selected items added

---

## Performance Tests

### Test P1: Receipt Scan Speed
**Metric**: Time from image capture to results
**Target**: < 5 seconds
**Test**: Scan 5 different receipts, average time

### Test P2: Stats Load Time
**Metric**: Time to load comprehensive stats
**Target**: < 2 seconds
**Test**: Fresh load of stats page

### Test P3: Recipe Search
**Metric**: Chat response time
**Target**: < 3 seconds
**Test**: Submit 5 different queries

---

## Edge Cases

### Edge Case 1: No Internet
1. Disable WiFi
2. Try OCR scan
3. Try rating recipe

**Expected**: Graceful error messages

### Edge Case 2: Blurry Receipt
1. Scan very blurry receipt
2. Check extraction

**Expected**: Error with retry option

### Edge Case 3: Empty Pantry
1. Clear all pantry items
2. Check stats page
3. Ask for recipes

**Expected**: Appropriate empty states

---

## Regression Tests

### Core Functionality
- [ ] Add manual pantry item
- [ ] Upload image for recognition
- [ ] Basic recipe search
- [ ] Shopping list add/remove
- [ ] Recipe cooking mode
- [ ] Pantry item editing
- [ ] User authentication

---

## Bug Report Template

```markdown
### Bug Description
[Clear description of the issue]

### Steps to Reproduce
1. 
2. 
3. 

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Environment
- iOS Version: 
- Device/Simulator: 
- Backend Running: Yes/No

### Screenshots
[If applicable]

### Additional Context
[Any other relevant information]
```

---

## Test Execution Checklist

### Pre-Release Testing
- [ ] All feature test cases pass
- [ ] Performance metrics met
- [ ] Edge cases handled gracefully
- [ ] No regression in core features
- [ ] Documentation updated
- [ ] CHANGELOG updated

### Sign-off Criteria
- Zero critical bugs
- All high-priority features working
- Performance within targets
- User flows smooth
- Error handling appropriate

---

## Known Issues

1. **OCR Accuracy**: Depends on receipt quality
   - Mitigation: Allow manual editing

2. **Stats Calculation**: May be slow with large datasets
   - Mitigation: Caching implemented

3. **Image Loading**: Network dependent
   - Mitigation: Placeholder images

---

## Test Environment Details

- **Backend**: FastAPI on port 8001
- **Database**: PostgreSQL (local)
- **iOS**: Expo Go / Simulator
- **Test User**: ID 111 (demo user)

---

Last Updated: January 2025
Version: 2.0.0