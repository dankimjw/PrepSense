# PrepSense Logo Setup Guide

## Step-by-Step Instructions

### Step 1: Prepare Your Logo Files

You need to save the PrepSense logo in these sizes:

1. **prepsense-logo.png** (For in-app display)
   - Size: 512x512px or larger
   - Background: Transparent or white
   - Save to: `/ios-app/assets/images/prepsense-logo.png`

2. **icon.png** (App icon - REPLACE existing file)
   - Size: 1024x1024px
   - Background: Solid color (no transparency for app stores)
   - Save to: `/ios-app/assets/images/icon.png`

3. **splash-icon.png** (Splash screen - REPLACE existing file)
   - Size: 1024x1024px
   - Background: White or transparent
   - Save to: `/ios-app/assets/images/splash-icon.png`

4. **adaptive-icon.png** (Android - REPLACE existing file)
   - Size: 1024x1024px
   - Background: Transparent with padding
   - Save to: `/ios-app/assets/images/adaptive-icon.png`

5. **favicon.png** (Web - REPLACE existing file)
   - Size: 48x48px
   - Save to: `/ios-app/assets/images/favicon.png`

### Step 2: Enable Logo in App Screens

Once you've added `prepsense-logo.png`, uncomment the Image components:

#### Sign-in Screen
1. Open `/ios-app/app/(auth)/sign-in.tsx`
2. Find lines 50-54 (the commented Image component)
3. Remove the `{/* */}` comment markers
4. Delete or comment out the Ionicons leaf icon on line 55

#### Navigation Header
1. Open `/ios-app/app/components/CustomHeader.tsx`
2. Find lines 87-91 (the commented Image component)
3. Remove the `{/* */}` comment markers
4. Delete or comment out the Ionicons leaf icon on line 92

#### Profile Screen
1. Open `/ios-app/app/(tabs)/profile.tsx`
2. Find lines 121-125 (the commented Image component)
3. Remove the `{/* */}` comment markers
4. Delete or comment out the logoContainer div (lines 127-130)

### Step 3: Restart Your App

```bash
# Stop the current server (Ctrl+C)
# Clear cache and restart
npx expo start -c
```

### Step 4: Test Different Platforms

- **iOS Simulator**: Press `i`
- **Android**: Press `a`
- **Physical device**: Scan QR code with Expo Go

## Logo Design Tips

For the best results:
- Use a square logo for app icons
- Include padding (10-15%) around the logo for icons
- Use high contrast for small sizes (favicon)
- Test on both light and dark backgrounds

## Brand Colors

- Primary Green: `#297A56`
- Gradient Start: `#4ECDC4` (Turquoise)
- Gradient End: `#A8E6CF` (Light Green)
- Background: `#FFFFFF` (White)

## Troubleshooting

If you see "Unable to resolve module" error:
1. Make sure the file exists in the correct location
2. File names are case-sensitive
3. Restart Metro bundler with cache clear: `npx expo start -c`

## Current Status

- ✅ Code prepared for logo integration
- ✅ Fallback to leaf icon if logo missing
- ✅ Navigation header prepared for logo (small, 28x28)
- ✅ Sign-in screen prepared for logo (large, 120x120)
- ✅ Profile screen prepared for logo (medium, 80x80)
- ⏳ Waiting for logo image files to be added