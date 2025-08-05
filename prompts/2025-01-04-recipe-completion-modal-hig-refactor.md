### Goal
Refactor the RecipeCompletionModal component to align with Apple Human Interface Guidelines, improving information architecture, visual hierarchy, controls & micro-interactions, actionability, and accessibility while maintaining all existing functionality.

### Background
- Project: PrepSense - pantry management application
- Relevant files / symbols:
  - `/Users/danielkim/_Capstone/PrepSense/ios-app/components/modals/RecipeCompletionModal.tsx` – main component to refactor
  - `/Users/danielkim/_Capstone/PrepSense/ios-app/__tests__/components/RecipeCompletionModal.test.tsx` – existing tests to preserve
  - `/Users/danielkim/_Capstone/PrepSense/docs/Doc_FrontEnd_iOS.md` – current implementation documentation
  - `/Users/danielkim/_Capstone/PrepSense/docs/QUICK_COMPLETE_REDESIGN_PLAN.md` – architectural guidance

### Requested Work

#### Phase 1: Information Architecture & Flow (Priority: High)
1. **Segmented Ingredients Display**
   - Group ingredients by availability status (Available/Partial/Missing)
   - Implement collapsible sections with clear visual indicators
   - Add overall progress indicator showing completion percentage

2. **Enhanced Progress Visualization**
   - Replace individual sliders with native iOS-style progress bars
   - Add summary progress bar at top showing overall recipe completion
   - Implement step-by-step visual flow indicators

#### Phase 2: Controls & Micro-interactions (Priority: High)
3. **Bottom Sheet Implementation**
   - Convert modal from full-screen to native bottom sheet presentation
   - Implement drag-to-dismiss gesture
   - Add proper safe area handling for different device sizes

4. **Native Stepper Controls**
   - Replace sliders with iOS-style steppers for precise quantity control
   - Implement cooking-friendly increment values (1/4, 1/2, 1 cup, etc.)

#### Phase 3: Visual Hierarchy & Aesthetics (Priority: Medium)
6. **Native InsetGrouped Style**
   - Convert ingredient cards to iOS InsetGrouped table view style
   - Implement proper section headers and footers
   - Use native iOS corner radius and shadow specifications

7. **Color Coding System**
   - Available ingredients: System green indicators
   - Partial ingredients: System orange warnings
   - Missing ingredients: System red alerts
   - Use SF Symbols for consistent iconography

#### Phase 4: Actionability (Priority: Medium)
8. **Bulk Shopping List Integration**
   - Add "Add Missing to Shopping List" bulk action
   - Implement swipe actions for individual ingredients
   - Add contextual menus for ingredient-specific actions

9. **Serving Size Scaler**
   - Add native iOS picker for serving size adjustment
   - Automatically recalculate all ingredient quantities
   - Show visual indicators for scaling changes

10. **Enhanced Cooking CTA**
    - Replace generic "Complete Recipe" with contextual actions
    - Add "Start Cooking" mode that guides through steps
    - Implement timer integration for cooking phases


### Acceptance Criteria
- Modal presents as native iOS bottom sheet with drag-to-dismiss
- All ingredients grouped by availability status with clear visual hierarchy
- Stepper controls replace sliders with cooking-friendly increments
- InsetGrouped table style implemented with proper section management
- Color coding follows iOS system colors
- Bulk actions available for shopping list integration
- Serving size scaler recalculates quantities automatically
- Existing API contract and test coverage preserved
- Performance maintains 60fps during all interactions

### Constraints
- Must maintain all existing props and callback interfaces
- Cannot break existing test suite without updating tests appropriately
- Must support iOS 14+ with proper fallbacks for older versions
- Performance must not degrade on older devices (iPhone 8+)
- Implementation must use React Native core components where possible
- No new dependencies without explicit approval
- Must maintain current error handling and loading state patterns

### Deliverable Format
Return orchestrator JSON under `## Final Result`.