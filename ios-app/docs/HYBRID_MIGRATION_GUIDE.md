# Hybrid React Native Paper + NativeWind Migration Guide

## Overview
This guide shows how to migrate existing forms to use React Native Paper components while keeping NativeWind styling and preserving all animations.

## ✅ What's Preserved
- **All intro animations** - EnhancedAnimatedIntroScreenV2 remains untouched
- **Custom navigation animations** - Tab bar and screen transitions unchanged
- **Gradient overlays** - Recipe cards keep their visual style
- **Performance optimizations** - List rendering and image caching intact

## 🔄 Migration Examples

### Before: Plain React Native TextInput
```tsx
// Old approach
<View style={styles.inputContainer}>
  <Text style={styles.label}>Item Name</Text>
  <TextInput
    style={styles.input}
    value={itemName}
    onChangeText={setItemName}
    placeholder="Enter item name"
  />
  {error && <Text style={styles.error}>{error}</Text>}
</View>
```

### After: Hybrid Approach
```tsx
// New approach with Paper + NativeWind
import { HybridTextInput } from '@/components/hybrid/HybridTextInput';

<HybridTextInput
  label="Item Name"
  value={itemName}
  onChangeText={setItemName}
  placeholder="Enter item name"
  error={!!error}
  helperText={error}
  containerClassName="mb-4"
  className="bg-white"
  debugName="ItemNameInput"
/>
```

## 📋 Form Migration Checklist

### 1. AddItemModalV2.tsx Migration
```tsx
// Import hybrid components
import { HybridTextInput } from '@/components/hybrid/HybridTextInput';
import { Button, Dialog, Portal } from 'react-native-paper';

// Replace TextInput with HybridTextInput
<HybridTextInput
  label="Item Name"
  value={itemName}
  onChangeText={setItemName}
  error={!!nameError}
  helperText={nameError}
  containerClassName="mb-4"
  left={<TextInput.Icon icon={() => getIngredientIcon(selectedCategory)} />}
/>

// Replace custom quantity input
<HybridTextInput
  label="Quantity"
  value={quantity}
  onChangeText={(text) => {
    const formatted = formatQuantityInput(text, selectedUnit);
    setQuantity(formatted);
  }}
  keyboardType="decimal-pad"
  error={!validateQuantity(quantity, selectedUnit)}
  helperText={!validateQuantity(quantity, selectedUnit) ? "Invalid quantity" : undefined}
  containerClassName="flex-1 mr-2"
/>

// Use Paper Button for actions
<Button 
  mode="contained"
  onPress={handleSave}
  loading={isLoading}
  disabled={!canSave}
  className="mt-4"
>
  Add to Pantry
</Button>
```

### 2. SearchBar.tsx Migration
```tsx
import { SearchInput } from '@/components/hybrid/HybridTextInput';

<SearchInput
  value={searchQuery}
  onChangeText={setSearchQuery}
  onSubmitEditing={handleSearch}
  containerClassName="mx-4 my-2"
  className="bg-surface-variant"
/>
```

### 3. Modal Migration
```tsx
// Replace Modal with Paper Dialog
import { Dialog, Portal, Button } from 'react-native-paper';

<Portal>
  <Dialog visible={visible} onDismiss={onClose}>
    <Dialog.Title>Add Item</Dialog.Title>
    <Dialog.Content>
      {/* Form content */}
    </Dialog.Content>
    <Dialog.Actions>
      <Button onPress={onClose}>Cancel</Button>
      <Button onPress={handleSave}>Save</Button>
    </Dialog.Actions>
  </Dialog>
</Portal>
```

## 🎨 Styling Strategy

### Combining Paper Theme with NativeWind
```tsx
// Use Paper's theme colors
<HybridTextInput
  style={{ 
    backgroundColor: theme.colors.surface 
  }}
  className="rounded-lg" // NativeWind for utilities
/>

// Or use CSS variables
<View className="bg-[var(--color-surface)]">
  <HybridTextInput className="text-[var(--color-text)]" />
</View>
```

### Debugging Styles
```tsx
// Enable style debugging
<HybridTextInput
  debugName="MyInput"
  className="border-2 border-primary"
  onFocus={() => StyleDebugger.log('MyInput', 'focused')}
/>
```

## 🐛 Debug Features

### 1. Debug Panel
- Access via floating bug button (bottom right)
- Toggle component borders
- View render counts
- Slow down animations
- Export logs

### 2. Component Debugging
```tsx
import { debugBorder, debugLog } from '@/components/debug/DebugPanel';

<View style={debugBorder(true)}>
  <HybridTextInput
    onChangeText={(text) => {
      debugLog('AddItem', 'Name changed', text);
      setItemName(text);
    }}
  />
</View>
```

### 3. Performance Monitoring
```tsx
const renderStart = StyleDebugger.performance.start('AddItemModal');

// ... component logic ...

useEffect(() => {
  StyleDebugger.performance.end('AddItemModal', renderStart);
}, []);
```

## 📱 Testing Accessibility

### Built-in Paper Accessibility
- TextInput: Automatic label announcements
- Button: Proper role and state
- Dialog: Focus trapping and escape handling

### Testing
```bash
# Run with screen reader
npx react-native run-ios --simulator="iPhone 15"
# Enable: Settings > Accessibility > VoiceOver

# Android
npx react-native run-android
# Enable: Settings > Accessibility > TalkBack
```

## ⚡ Performance Tips

1. **Lazy load Paper components**
   ```tsx
   const Dialog = React.lazy(() => 
     import('react-native-paper').then(m => ({ default: m.Dialog }))
   );
   ```

2. **Use Paper's animation config**
   ```tsx
   <PaperProvider theme={{ animation: { scale: 1.0 } }}>
   ```

3. **Memoize hybrid components**
   ```tsx
   const MemoizedInput = React.memo(HybridTextInput);
   ```

## 🚀 Next Steps

1. Start with high-value forms (login, add item, search)
2. Test with VoiceOver/TalkBack
3. Measure bundle size impact
4. Document any custom Paper components created

## 📊 Metrics to Track

- Bundle size before/after
- Render time for forms
- Accessibility score
- Lines of code reduced
- Test coverage improvement