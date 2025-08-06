# Animation Documentation

This folder contains all documentation related to animations in the PrepSense iOS app.

## Documentation Index

### Core Animation Implementation
- [`ANIMATION_IMPLEMENTATION_NOTES.md`](./ANIMATION_IMPLEMENTATION_NOTES.md) - Comprehensive notes on all animation implementations
- [`ANIMATION_SESSION_SUMMARY_2025-01-29.md`](./ANIMATION_SESSION_SUMMARY_2025-01-29.md) - Latest session summary with merge conflict resolution

### Navigation & Performance
- [`../NAVIGATION_PERFORMANCE_OPTIMIZATION.md`](../NAVIGATION_PERFORMANCE_OPTIMIZATION.md) - Performance optimizations for navigation animations
- [`../NAVIGATION_PERFORMANCE_MIGRATION_EXAMPLES.md`](../NAVIGATION_PERFORMANCE_MIGRATION_EXAMPLES.md) - Migration examples for optimized navigation

### Related Documentation
- [`../Performance_Optimization_Session_Notes.md`](../Performance_Optimization_Session_Notes.md) - Performance optimization session notes
- [`../RecipeDetailCardV3_Design_Notes.md`](../RecipeDetailCardV3_Design_Notes.md) - Recipe card animation design notes

## Quick Reference

### Key Animation Components

1. **Intro Screen Animation** (`EnhancedAnimatedIntroScreenV2.tsx`)
   - Character-by-character jumping animation for "PrepSense" logo
   - Fruit/vegetable falling animations with botanical accuracy
   - Magical tunnel transition with circular gradients
   - Idle animations with random intervals

2. **Header Animation** (`CustomHeader.tsx`)
   - Text shadow effects
   - Subtle breathing animation
   - Long-press trigger for demo

3. **Quick Actions Animation** (`QuickActions.tsx`)
   - Staggered bounce-in animations
   - Spring physics for natural feel

### Technology Stack
- **React Native Reanimated 3** - Core animation library
- **react-native-svg** - SVG support for custom vegetable icons
- **Spring Physics** - Natural animation curves

### Performance Considerations
- Use `worklet` functions for animations
- Implement proper cleanup for intervals/timeouts
- Defer heavy operations with `InteractionManager`
- Use `React.memo` for animation-heavy components

### Animation Patterns

#### Staggered Animations
```typescript
characters.forEach((char, index) => {
  characterTransforms[index].value = withDelay(
    index * 150,
    withSequence(
      withSpring(-20, physics),
      withSpring(0, physics)
    )
  );
});
```

#### Breathing Animations
```typescript
const breathingAnimation = () => {
  scale.value = withSequence(
    withSpring(1.02, { damping: 12, stiffness: 80 }),
    withSpring(0.99, { damping: 12, stiffness: 80 }),
    withSpring(1.0, { damping: 12, stiffness: 80 })
  );
};
```

## Todo: Remaining Animation Tasks

1. 🔄 Create staggered pantry items list animations
2. 🔄 Enhance search bar focus/expand animations
3. 🔄 Add custom vegetable-themed pull-to-refresh
4. 🔄 Implement filter chips slide animations
5. 🔄 Create page load sequence orchestration

## Contributing

When adding new animations:
1. Follow existing patterns for consistency
2. Prioritize performance over complexity
3. Test on actual devices, not just simulator
4. Document in appropriate file in this folder
5. Update this README with new components

---
*Last updated: January 29, 2025*