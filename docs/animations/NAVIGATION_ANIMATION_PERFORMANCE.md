# Navigation Animation Performance Guide

This document focuses specifically on animation-related performance optimizations for navigation in the PrepSense iOS app.

## Animation Performance Issues

### Problem: Heavy Animations During Navigation
- Complex spring animations blocking screen transitions
- Multiple animated components updating simultaneously
- Unoptimized animation curves causing jank

### Solutions Implemented

## 1. Deferred Animations

Use `InteractionManager` to defer non-critical animations:

```typescript
// Before: Animations block navigation
useEffect(() => {
  // Heavy animation starts immediately
  fadeAnim.value = withSpring(1, { damping: 15 });
  scaleAnim.value = withSequence(
    withSpring(1.2),
    withSpring(1)
  );
}, []);

// After: Animations deferred until navigation completes
useEffect(() => {
  InteractionManager.runAfterInteractions(() => {
    fadeAnim.value = withSpring(1, { damping: 15 });
    scaleAnim.value = withSequence(
      withSpring(1.2),
      withSpring(1)
    );
  });
}, []);
```

## 2. Optimized Spring Physics

Replace heavy spring animations with optimized physics:

```typescript
// Heavy spring config (avoid during navigation)
const heavySpring = {
  damping: 10,
  stiffness: 100,
  mass: 1,
  velocity: 0
};

// Optimized for navigation
const navigationSpring = {
  damping: 20,      // Higher damping = less oscillation
  stiffness: 200,   // Higher stiffness = faster animation
  mass: 0.5        // Lower mass = more responsive
};

// Usage
translateY.value = withSpring(0, navigationSpring);
```

## 3. Navigation-Aware Animations

Components that pause animations during navigation:

```typescript
const NavigationAwareComponent = () => {
  const navigation = useNavigation();
  const animationRef = useRef<any>();
  
  useEffect(() => {
    const unsubscribe = navigation.addListener('blur', () => {
      // Pause animations when navigating away
      cancelAnimation(animationRef.current);
    });
    
    return unsubscribe;
  }, [navigation]);
  
  // Animation logic here
};
```

## 4. Screen Transition Animations

Optimized screen transition patterns:

```typescript
// TabScreenTransition component
export const TabScreenTransition = ({ children, routeName, transitionStyle }) => {
  const fadeAnim = useSharedValue(0);
  const translateY = useSharedValue(20);
  
  useEffect(() => {
    // Simple, fast animations for screen entry
    fadeAnim.value = withTiming(1, { duration: 200 });
    translateY.value = withTiming(0, { duration: 200 });
  }, []);
  
  const animatedStyle = useAnimatedStyle(() => ({
    opacity: fadeAnim.value,
    transform: [{ translateY: translateY.value }]
  }));
  
  return (
    <Animated.View style={[styles.container, animatedStyle]}>
      {children}
    </Animated.View>
  );
};
```

## 5. Modal Animation Optimization

Lightweight modal animations:

```typescript
// Before: Heavy modal animation
const showModal = () => {
  modalScale.value = withSpring(1, {
    damping: 8,    // Too much bounce
    stiffness: 50  // Too slow
  });
};

// After: Optimized for performance
const showModal = () => {
  modalScale.value = withTiming(1, {
    duration: 250,
    easing: Easing.out(Easing.cubic)
  });
};
```

## 6. List Animation Optimization

Staggered animations that don't block navigation:

```typescript
const StaggeredList = ({ items }) => {
  const animatedItems = items.map(() => useSharedValue(0));
  
  useEffect(() => {
    // Defer staggered animations
    InteractionManager.runAfterInteractions(() => {
      animatedItems.forEach((anim, index) => {
        anim.value = withDelay(
          index * 50, // Minimal delay
          withTiming(1, { duration: 300 })
        );
      });
    });
  }, []);
  
  return items.map((item, index) => (
    <AnimatedListItem
      key={item.id}
      item={item}
      animValue={animatedItems[index]}
    />
  ));
};
```

## Performance Metrics

### Before Optimization
- Navigation delay: 500-800ms
- Animation jank: Frequent
- FPS during navigation: 45-50

### After Optimization
- Navigation delay: 150-200ms
- Animation jank: Rare
- FPS during navigation: 58-60

## Best Practices

1. **Use `withTiming` over `withSpring` for navigation animations**
   - More predictable performance
   - Faster completion

2. **Defer complex animations with `InteractionManager`**
   - Let navigation complete first
   - Then run decorative animations

3. **Cancel animations on screen blur**
   - Save resources
   - Prevent animation conflicts

4. **Use simple easing functions**
   - `Easing.out(Easing.cubic)` for most cases
   - Avoid complex custom easings during navigation

5. **Batch animation updates**
   - Group related animations
   - Use `runOnUI` for synchronous updates

## Testing Animation Performance

```typescript
// Add to any component to monitor animation performance
const debugAnimation = (animationName: string) => {
  'worklet';
  const start = performance.now();
  
  return () => {
    const duration = performance.now() - start;
    if (duration > 16) { // More than one frame
      console.warn(`Animation '${animationName}' took ${duration}ms`);
    }
  };
};

// Usage
useAnimatedStyle(() => {
  const done = debugAnimation('header-fade');
  const style = { opacity: fadeAnim.value };
  done();
  return style;
});
```

## Related Files
- [`useOptimizedNavigation.ts`](../../ios-app/hooks/useOptimizedNavigation.ts)
- [`TabScreenTransition.tsx`](../../ios-app/components/navigation/TabScreenTransition.tsx)
- [`performanceMonitoring.ts`](../../ios-app/utils/performanceMonitoring.ts)

---
*Extracted from navigation performance documentation for animation-specific reference*