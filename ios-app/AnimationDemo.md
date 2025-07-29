# PrepSense Intro Animation Demo

## Animation Sequence

The new intro screen features an engaging animation sequence:

### 1. Character Jump Animation (0-1.5s)
- Each letter of "PrepSense" jumps in from the bottom of the screen
- Letters appear with a staggered delay (100ms between each)
- Each character:
  - Starts off-screen at the bottom
  - Springs up with a bounce effect
  - Rotates 360° while jumping
  - Scales from 0.5x to 1.2x then settles at 1x
  - Fades in from 0 to 100% opacity
  - Small bounce after landing

### 2. Vegetable Icons Animation (1.8-2.2s)
- 🥕 Carrot, 🥦 Broccoli, and 🍅 Tomato emojis fall from top
- Each vegetable:
  - Starts at random X positions
  - Falls with spring physics
  - Bounces when hitting their final position
  - Spins 720° while falling
  - Gently sways left and right after landing

### 3. Tagline Animation (1.5s+)
- "Smart Pantry, Zero Waste" fades in
- "Let's make every ingredient count" appears below
- Both scale from 0.8x to 1x with spring effect

### 4. Call-to-Action Button (2.5s+)
- "Get Started" button fades in
- Pulses continuously (scale 0.95x to 1.05x)
- Invites user interaction

## Visual Style
- Dark gradient background (#0a0a0a to #1a1a1a)
- Brand green (#5BA041) for logo text
- Text shadow with avocado green (#7FB96E)
- White text for taglines
- Smooth spring animations throughout

## How to Test

1. The animation will play automatically when:
   - First time launching the app
   - In development mode (for testing)

2. To force show the intro again:
   - Clear AsyncStorage
   - Or restart the app in dev mode

3. The animation is optimized for performance using:
   - React Native Reanimated 3
   - Hardware-accelerated animations
   - Efficient spring physics

## Implementation Details

The animation uses:
- `withSpring()` for bouncy, natural movements
- `withDelay()` for sequencing
- `withSequence()` for multi-step animations
- `useSharedValue()` for performance
- `useAnimatedStyle()` for smooth transforms

The entire sequence completes in about 3 seconds, creating an engaging and memorable first impression for users.