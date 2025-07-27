# RecipeDetailCardV3 Design Style & Language Notes

## Design Philosophy

### Visual Hierarchy
- **Fixed Hero Section**: 25% of screen height creates immediate visual impact without overwhelming
- **Overlaid Controls**: Floating navigation maintains accessibility while preserving image real estate
- **Scrollable Content**: Independent scrolling allows extensive recipe information without cluttering

### Layout Proportions
```
┌─────────────────────────────┐
│     Hero Image (25%)        │ ← Fixed, always visible
│  [X]              [💾][👍]  │ ← Overlaid controls
├─────────────────────────────┤
│                             │
│    Scrollable Content       │ ← Independent scroll area
│    - Recipe Info Card       │
│    - Ingredients            │
│    - Instructions           │ ← Can be very long
│                             │
└─────────────────────────────┘
```

## Visual Language

### Color Palette
- **Primary Red**: `#FF6B6B` - Primary actions (Cook Now button)
- **Primary Purple**: `#6366F1` - Secondary actions (Quick Complete)
- **Success Green**: `#4CAF50` - Available ingredients, positive feedback
- **Warning Orange**: `#FF9800` - Missing ingredients
- **Error Red**: `#F44336` - Negative feedback
- **Neutral Grays**: `#F8F9FA`, `#E0E0E0`, `#666` - Backgrounds, borders, text

### Typography Scale
- **Hero Title**: 22px, Bold - Main recipe title
- **Section Headers**: 18px, Semibold - Ingredients, Instructions
- **Body Text**: 15px, Regular - Instructions, ingredient lists
- **Metadata**: 14px, Medium - Stats, time, calories
- **Small Labels**: 12px, Medium - Step numbers, legends

### Spacing System
- **Card Padding**: 20px - Main content areas
- **Section Margins**: 20px - Between major sections
- **Item Spacing**: 12px - Between related elements
- **Micro Spacing**: 6-8px - Icon gaps, small elements

## Component Architecture

### Layout Strategy
```typescript
<View style={styles.container}>
  {/* Fixed Hero Section */}
  <View style={styles.fixedHeroSection}>
    <Image style={styles.heroImage} />
    <SafeAreaView style={styles.overlayButtons}>
      {/* Navigation controls */}
    </SafeAreaView>
  </View>
  
  {/* Scrollable Content */}
  <ScrollView style={styles.scrollableContent}>
    <View style={styles.infoCard}>
      {/* Recipe details */}
    </View>
    {/* Additional sections */}
  </ScrollView>
</View>
```

### Button Design Language

#### Primary Actions
- **Cook Now**: Full-width, bold red (`#FF6B6B`), high visual weight
- **Quick Complete**: Compact, secondary purple (`#6366F1`), with flash icon

#### Overlay Controls
- **Circular buttons**: 40px diameter, white background with transparency
- **Shadow elevation**: Subtle depth for floating effect
- **Icon-only**: Clean, minimal visual noise

### Interactive States
- **Active States**: Scale animation (1.0 → 1.3 → 1.0) for bookmark
- **Disabled States**: Reduced opacity, no interactions
- **Loading States**: Spinner with branded colors

## Content Strategy

### Information Architecture
1. **Immediate Context**: Hero image + overlaid controls
2. **Essential Info**: Title, time, calories, match percentage
3. **Action Layer**: Primary cooking actions
4. **Detailed Content**: Ingredients with availability status
5. **Instructional**: Step-by-step cooking directions

### Progressive Disclosure
- **Ingredients**: Show first 5, expand on demand
- **Instructions**: Always show all steps (cooking is linear)
- **Nutrition**: Modal overlay for detailed breakdown

### Accessibility Language
- **Semantic Labels**: Clear, descriptive accessibility labels
- **Status Communication**: Available vs missing ingredients clearly marked
- **Action Feedback**: Immediate visual feedback for all interactions

## Animation & Transitions

### Micro-Interactions
- **Bookmark**: Scale bounce animation for tactile feedback
- **Modal Transitions**: Fade in/out for overlays
- **Scroll Behavior**: Smooth, native iOS momentum

### Visual Feedback
- **Success States**: Green checkmarks for available ingredients
- **Warning States**: Orange plus icons for missing items
- **Rating Feedback**: Immediate icon change with color transition

## Responsive Considerations

### Screen Adaptation
- **Hero Height**: 25% maintains proportion across device sizes
- **Safe Areas**: Proper handling of notches and home indicators
- **Text Scaling**: Supports iOS Dynamic Type preferences

### Content Overflow
- **Long Titles**: Ellipsis truncation with full text on multiple lines
- **Ingredient Lists**: Vertical scrolling within fixed containers
- **Instructions**: Natural text wrapping with generous line height

## Technical Implementation Notes

### Performance Optimizations
- **Image Loading**: Progressive loading with placeholder states
- **List Rendering**: Efficient mapping for ingredients/steps
- **Modal Management**: Proper cleanup and state management

### Platform Consistency
- **iOS Guidelines**: Follows Human Interface Guidelines
- **React Native**: Uses platform-appropriate components
- **Expo Integration**: Compatible with Expo development workflow

## Future Enhancement Opportunities

### Potential Improvements
- **Gesture Navigation**: Swipe gestures for quick actions
- **Dynamic Sizing**: Adaptive hero image based on content
- **Rich Media**: Video instructions integration
- **Personalization**: User-customizable layout preferences

### Accessibility Enhancements
- **Voice Control**: Enhanced voice navigation support
- **High Contrast**: Improved contrast ratios for accessibility
- **Screen Reader**: Optimized screen reader experience

---

**Last Updated**: 2025-01-27  
**Component**: RecipeDetailCardV3.tsx  
**Design System**: PrepSense v3.0