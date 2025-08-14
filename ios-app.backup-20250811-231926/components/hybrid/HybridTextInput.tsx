// Hybrid TextInput component combining React Native Paper with NativeWind styling
import React, { forwardRef } from 'react';
import { TextInput as PaperTextInput, HelperText } from 'react-native-paper';
import { View } from 'react-native';
import { StyleDebugger } from '../../config/hybridProvider';
import { twMerge } from 'tailwind-merge';

interface HybridTextInputProps extends React.ComponentProps<typeof PaperTextInput> {
  // NativeWind className support
  className?: string;
  containerClassName?: string;
  helperClassName?: string;
  
  // Enhanced props
  error?: boolean;
  helperText?: string;
  
  // Debug props
  debugName?: string;
}

export const HybridTextInput = forwardRef<any, HybridTextInputProps>(({
  className,
  containerClassName,
  helperClassName,
  error,
  helperText,
  debugName = 'HybridTextInput',
  style,
  ...props
}, ref) => {
  // Debug styling in development
  if (__DEV__ && (className || containerClassName)) {
    StyleDebugger.log(debugName, `container: ${containerClassName}, input: ${className}`, style);
  }

  // Performance tracking for complex inputs
  const renderStart = __DEV__ ? StyleDebugger.performance.start(`${debugName}-render`) : 0;

  const renderContent = () => (
    <View className={twMerge('w-full', containerClassName)}>
      <PaperTextInput
        ref={ref}
        mode="outlined"
        error={error}
        className={className}
        style={[
          {
            backgroundColor: 'transparent',
          },
          style,
        ]}
        {...props}
      />
      {helperText && (
        <HelperText 
          type={error ? 'error' : 'info'} 
          visible={!!helperText}
          className={helperClassName}
        >
          {helperText}
        </HelperText>
      )}
    </View>
  );

  const content = renderContent();
  
  if (__DEV__) {
    StyleDebugger.performance.end(`${debugName}-render`, renderStart);
  }

  return content;
});

HybridTextInput.displayName = 'HybridTextInput';

// Export convenience components for common use cases
export const EmailInput = forwardRef<any, HybridTextInputProps>((props, ref) => (
  <HybridTextInput
    ref={ref}
    label="Email"
    keyboardType="email-address"
    autoCapitalize="none"
    autoComplete="email"
    textContentType="emailAddress"
    debugName="EmailInput"
    {...props}
  />
));

export const PasswordInput = forwardRef<any, HybridTextInputProps>((props, ref) => (
  <HybridTextInput
    ref={ref}
    label="Password"
    secureTextEntry
    autoComplete="password"
    textContentType="password"
    debugName="PasswordInput"
    {...props}
  />
));

export const SearchInput = forwardRef<any, HybridTextInputProps>((props, ref) => (
  <HybridTextInput
    ref={ref}
    label="Search"
    left={<PaperTextInput.Icon icon="magnify" />}
    autoCapitalize="none"
    returnKeyType="search"
    debugName="SearchInput"
    {...props}
  />
));

// Debug helper for form validation
export const useInputDebug = (inputName: string) => {
  return {
    onFocus: () => __DEV__ && console.log(`[Input] ${inputName} focused`),
    onBlur: () => __DEV__ && console.log(`[Input] ${inputName} blurred`),
    onChangeText: (text: string) => __DEV__ && console.log(`[Input] ${inputName} changed:`, text.length, 'chars'),
    onSubmitEditing: () => __DEV__ && console.log(`[Input] ${inputName} submitted`),
  };
};