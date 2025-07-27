# iOS Simulator Warning Suppression

## Overview
Implemented a system to suppress warnings and errors in the iOS simulator UI while keeping them visible in the terminal console.

## Implementation Details

### 1. LogBox Configuration (ios-app/app/_layout.tsx)
- Added React Native's LogBox import and configuration
- Two modes controlled by environment variable:
  - **Full suppression**: `LogBox.ignoreAllLogs(true)` when `EXPO_PUBLIC_SUPPRESS_WARNINGS=true`
  - **Selective suppression**: Ignores specific common warnings when `false`

### 2. Environment Variable (.env)
- Added `EXPO_PUBLIC_SUPPRESS_WARNINGS=false` 
- Controls whether warnings appear in the iOS simulator
- Terminal warnings are NOT affected

### 3. Toggle Script (toggle_warnings.sh)
```bash
./toggle_warnings.sh off  # Hide warnings in simulator
./toggle_warnings.sh on   # Show warnings in simulator  
./toggle_warnings.sh      # Check current status
```

## Common Warnings Ignored by Default
- React lifecycle warnings (componentWillReceiveProps, componentWillMount)
- Non-serializable values in state/navigation
- VirtualizedLists nesting warnings
- Expo Constants warnings
- AsyncStorage extraction warnings

## Usage
1. To hide all warnings in simulator: `./toggle_warnings.sh off`
2. Restart app: `python run_app.py`
3. To re-enable warnings: `./toggle_warnings.sh on`

## Notes
- Warnings still appear in terminal for debugging
- Only affects the yellow/red warning boxes in the simulator
- Can add more specific warnings to ignore list in _layout.tsx
- Requires app restart after toggling

## Files Modified
- `/ios-app/app/_layout.tsx` - Added LogBox configuration
- `/.env` - Added EXPO_PUBLIC_SUPPRESS_WARNINGS variable
- `/toggle_warnings.sh` - Created toggle script (chmod +x)