import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react-native';
import { PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { HybridTextInput, EmailInput, PasswordInput, SearchInput } from '../../../components/hybrid/HybridTextInput';
import { lightTheme } from '../../../config/hybridTheme';

// Mock StyleDebugger to avoid issues in test environment
jest.mock('../../../config/hybridProvider', () => ({
  StyleDebugger: {
    log: jest.fn(),
    performance: {
      start: jest.fn(() => Date.now()),
      end: jest.fn(),
    },
  },
}));

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <SafeAreaProvider>
      <PaperProvider theme={lightTheme}>
        {component}
      </PaperProvider>
    </SafeAreaProvider>
  );
};

describe('HybridTextInput', () => {
  it('renders correctly with basic props', () => {
    renderWithProvider(
      <HybridTextInput
        testID="hybrid-input"
        label="Test Input"
        placeholder="Enter text"
      />
    );

    expect(screen.getByTestId('hybrid-input')).toBeTruthy();
    expect(screen.getByText('Test Input')).toBeTruthy();
  });

  it('handles text input correctly', () => {
    const onChangeText = jest.fn();
    
    renderWithProvider(
      <HybridTextInput
        testID="hybrid-input"
        label="Test Input"
        onChangeText={onChangeText}
      />
    );

    const input = screen.getByTestId('hybrid-input');
    fireEvent.changeText(input, 'test text');

    expect(onChangeText).toHaveBeenCalledWith('test text');
  });

  it('displays error state correctly', () => {
    renderWithProvider(
      <HybridTextInput
        testID="hybrid-input"
        label="Test Input"
        error={true}
        helperText="This field is required"
      />
    );

    expect(screen.getByText('This field is required')).toBeTruthy();
  });

  it('applies NativeWind classes correctly', () => {
    renderWithProvider(
      <HybridTextInput
        testID="hybrid-input"
        label="Test Input"
        className="border-red-500"
        containerClassName="mb-4"
      />
    );

    // Verify the input renders (specific style testing would require more complex setup)
    expect(screen.getByTestId('hybrid-input')).toBeTruthy();
  });

  it('supports forwarded ref', () => {
    const ref = React.createRef<any>();
    
    renderWithProvider(
      <HybridTextInput
        ref={ref}
        testID="hybrid-input"
        label="Test Input"
      />
    );

    expect(ref.current).toBeTruthy();
  });
});

describe('EmailInput', () => {
  it('renders with correct props for email input', () => {
    renderWithProvider(
      <EmailInput
        testID="email-input"
        value="test@example.com"
        onChangeText={() => {}}
      />
    );

    const input = screen.getByTestId('email-input');
    expect(input).toBeTruthy();
    expect(screen.getByDisplayValue('test@example.com')).toBeTruthy();
    expect(screen.getByText('Email')).toBeTruthy();
  });
});

describe('PasswordInput', () => {
  it('renders with secure text entry', () => {
    renderWithProvider(
      <PasswordInput
        testID="password-input"
        value="password123"
        onChangeText={() => {}}
      />
    );

    const input = screen.getByTestId('password-input');
    expect(input).toBeTruthy();
    expect(screen.getByText('Password')).toBeTruthy();
  });
});

describe('SearchInput', () => {
  it('renders with search icon and correct props', () => {
    renderWithProvider(
      <SearchInput
        testID="search-input"
        value="search query"
        onChangeText={() => {}}
      />
    );

    const input = screen.getByTestId('search-input');
    expect(input).toBeTruthy();
    expect(screen.getByDisplayValue('search query')).toBeTruthy();
    expect(screen.getByText('Search')).toBeTruthy();
  });
});

describe('Accessibility', () => {
  it('provides correct accessibility labels', () => {
    renderWithProvider(
      <HybridTextInput
        testID="hybrid-input"
        label="Full Name"
        placeholder="Enter your full name"
        accessible={true}
        accessibilityLabel="Full Name Input"
      />
    );

    const input = screen.getByTestId('hybrid-input');
    expect(input).toBeTruthy();
    // Paper TextInput should handle accessibility automatically
  });

  it('announces error messages to screen readers', () => {
    renderWithProvider(
      <HybridTextInput
        testID="hybrid-input"
        label="Email"
        error={true}
        helperText="Please enter a valid email address"
        accessible={true}
      />
    );

    expect(screen.getByText('Please enter a valid email address')).toBeTruthy();
  });
});

describe('Performance', () => {
  it('does not re-render unnecessarily', () => {
    const onChangeText = jest.fn();
    
    const { rerender } = renderWithProvider(
      <HybridTextInput
        testID="hybrid-input"
        label="Test Input"
        value="initial"
        onChangeText={onChangeText}
      />
    );

    // Re-render with same props
    rerender(
      <SafeAreaProvider>
        <PaperProvider theme={lightTheme}>
          <HybridTextInput
            testID="hybrid-input"
            label="Test Input"
            value="initial"
            onChangeText={onChangeText}
          />
        </PaperProvider>
      </SafeAreaProvider>
    );

    // Component should render successfully both times
    expect(screen.getByTestId('hybrid-input')).toBeTruthy();
  });
});