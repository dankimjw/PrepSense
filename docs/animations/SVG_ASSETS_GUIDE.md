# SVG Assets Guide for Animations

This document describes the custom SVG assets created for the PrepSense animations.

## SVG Asset Location
- Original SVGs: `/Users/danielkim/_Capstone/PrepSense/notebooks/my_notes/SVGs`
- Implemented in: `EnhancedAnimatedIntroScreenV2.tsx`

## Custom Vegetable SVGs

### 1. Tomato Icon
```typescript
const TomatoIcon = ({ size = 80, style = {} }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Circle cx="50" cy="55" r="35" fill="#ff6b6b" />
      <Path d="M 50 20 L 45 30 L 40 25 L 50 35 L 60 25 L 55 30 Z" fill="#4CAF50" />
    </Svg>
  </Animated.View>
);
```
- **Color**: Red (#ff6b6b) with green stem
- **Shape**: Perfect circle with leafy top

### 2. Carrot Icon
```typescript
const CarrotIcon = ({ size = 85, style = {} }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path d="M 50 20 L 40 80 L 50 85 L 60 80 Z" fill="#ff8c42" />
      <Path d="M 45 20 L 50 15 L 55 20" fill="#4CAF50" stroke="#4CAF50" strokeWidth="3" />
    </Svg>
  </Animated.View>
);
```
- **Color**: Orange (#ff8c42) with green top
- **Shape**: Tapered triangle

### 3. Broccoli Icon (Botanically Accurate)
```typescript
const BroccoliIcon = ({ size = 85, style = {} }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      {/* Green stem - rectangular and thick */}
      <Rect x="45" y="50" width="10" height="30" fill="#228B22" />
      
      {/* Puffy head with multiple circles for texture */}
      <Circle cx="50" cy="40" r="20" fill="#228B22" />
      <Circle cx="40" cy="35" r="12" fill="#2F8B2F" />
      <Circle cx="60" cy="35" r="12" fill="#2F8B2F" />
      <Circle cx="35" cy="45" r="10" fill="#2F8B2F" />
      <Circle cx="65" cy="45" r="10" fill="#2F8B2F" />
      <Circle cx="45" cy="30" r="8" fill="#32CD32" />
      <Circle cx="55" cy="30" r="8" fill="#32CD32" />
      <Circle cx="50" cy="45" r="8" fill="#32CD32" />
    </Svg>
  </Animated.View>
);
```
- **Stem**: Green (#228B22), rectangular, uniform thickness
- **Head**: Multiple overlapping circles for "afro" texture
- **Shading**: Three shades of green for depth

### 4. Banana Icon (With Aging Details)
```typescript
const BananaIcon = ({ size = 95, style = {} }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      {/* Main banana body - C-shaped crescent curve */}
      <Path 
        d="M 35 15 C 25 15 12 25 12 35 C 12 45 18 55 23 65 C 28 75 33 85 43 90 C 50 93 58 91 58 85 C 58 79 52 74 47 69 C 42 64 37 54 32 44 C 27 34 27 24 35 15 Z" 
        fill="#fdd835" 
      />
      
      {/* Rectangular brown tip at the stem end */}
      <Path 
        d="M 33 13 L 37 13 L 37 17 L 33 17 Z" 
        fill="#8b4513" 
      />
      
      {/* Brown spots - overripe but still edible */}
      <Path d="M 28 28 C 27 27 26 28 27 29 C 28 30 29 29 28 28 Z" fill="#d2691e" opacity="0.4"/>
      <Path d="M 35 38 C 34 37 33 38 34 39 C 35 40 36 39 35 38 Z" fill="#d2691e" opacity="0.4"/>
      <Path d="M 42 48 C 41 47 40 48 41 49 C 42 50 43 49 42 48 Z" fill="#d2691e" opacity="0.5"/>
      <Path d="M 30 52 C 29 51 28 52 29 53 C 30 54 31 53 30 52 Z" fill="#d2691e" opacity="0.4"/>
      <Path d="M 38 62 C 37 61 36 62 37 63 C 38 64 39 63 38 62 Z" fill="#d2691e" opacity="0.5"/>
      <Path d="M 25 42 C 24 41 23 42 24 43 C 25 44 26 43 25 42 Z" fill="#d2691e" opacity="0.3"/>
    </Svg>
  </Animated.View>
);
```
- **Shape**: C-shaped crescent curve
- **Color**: Yellow (#fdd835) with brown aging spots
- **Details**: Rectangular brown tip, gradual brown spots with varying opacity
- **Size**: Larger than other vegetables (95px)

### 5. Lettuce Icon
```typescript
const LettuceIcon = ({ size = 80, style = {} }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Circle cx="50" cy="50" r="35" fill="#90EE90" />
      <Circle cx="50" cy="50" r="25" fill="#7FDD7F" />
      <Circle cx="50" cy="50" r="15" fill="#6FCF6F" />
    </Svg>
  </Animated.View>
);
```
- **Design**: Layered circles for leaf effect
- **Colors**: Three shades of green

### 6. Pepper Icon
```typescript
const PepperIcon = ({ size = 85, style = {} }) => (
  <Animated.View style={[{ width: size, height: size }, style]}>
    <Svg width={size} height={size} viewBox="0 0 100 100">
      <Path d="M 50 25 C 35 25 25 40 25 55 C 25 70 35 85 50 85 C 65 85 75 70 75 55 C 75 40 65 25 50 25 Z" fill="#FFC107" />
      <Path d="M 50 25 L 45 20 L 50 15 L 55 20 Z" fill="#4CAF50" />
    </Svg>
  </Animated.View>
);
```
- **Color**: Yellow bell pepper (#FFC107)
- **Shape**: Rounded rectangle with stem

## Animation Usage

### Falling Animation Pattern
```typescript
vegetables.forEach((veg, index) => {
  const translateY = useSharedValue(-150 - Math.random() * 100);
  const translateX = useSharedValue((index * 60) + 20);
  
  useEffect(() => {
    translateY.value = withDelay(
      index * 200,
      withSpring(FINAL_Y_POSITION, {
        damping: 8,
        stiffness: 40,
        mass: 1 + Math.random() * 0.5,
      })
    );
  }, []);
});
```

### Idle Bounce Animation
```typescript
const bounceAnimation = () => {
  'worklet';
  translateY.value = withSequence(
    withSpring(FINAL_Y_POSITION - 10, { damping: 15, stiffness: 200 }),
    withSpring(FINAL_Y_POSITION, { damping: 15, stiffness: 200 })
  );
};
```

## Design Principles

1. **Botanical Accuracy**
   - Green stems for broccoli (not brown)
   - Proper vegetable proportions
   - Realistic colors

2. **Visual Consistency**
   - All vegetables use similar viewBox (100x100)
   - Consistent stroke widths
   - Harmonious color palette

3. **Animation-Friendly**
   - Simple paths for performance
   - Centered in viewBox for rotation
   - Appropriate sizes for mobile screens

## Color Palette
- **Reds**: #ff6b6b (tomato)
- **Oranges**: #ff8c42 (carrot), #FFC107 (pepper)
- **Yellows**: #fdd835 (banana)
- **Greens**: #4CAF50 (stems), #228B22 (broccoli), #90EE90 (lettuce)
- **Browns**: #8b4513 (banana tip), #d2691e (aging spots)

## Performance Notes
- SVGs are wrapped in `Animated.View` for transform animations
- Simple paths used to minimize rendering overhead
- Consistent sizing prevents layout recalculations

---
*For implementation details, see `EnhancedAnimatedIntroScreenV2.tsx`*