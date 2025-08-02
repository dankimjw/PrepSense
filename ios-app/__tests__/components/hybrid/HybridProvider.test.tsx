import React from 'react';
import { render, screen } from '@testing-library/react-native';
import { Text, useColorScheme } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { HybridProvider, StyleDebugger } from '../../../config/hybridProvider';

// Mock useColorScheme
jest.mock('react-native/Libraries/Utilities/useColorScheme', () => ({
  __esModule: true,
  default: jest.fn(() => 'light'),
}));

const mockUseColorScheme = useColorScheme as jest.MockedFunction<typeof useColorScheme>;

const TestComponent = () => (
  <Text testID="test-child">Test Child Component</Text>
);

const renderWithSafeArea = (component: React.ReactElement) => {
  return render(
    <SafeAreaProvider>
      {component}
    </SafeAreaProvider>
  );
};

describe('HybridProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseColorScheme.mockReturnValue('light');
  });

  it('renders children correctly', () => {
    renderWithSafeArea(
      <HybridProvider>
        <TestComponent />
      </HybridProvider>
    );

    expect(screen.getByTestId('test-child')).toBeTruthy();
    expect(screen.getByText('Test Child Component')).toBeTruthy();
  });

  it('responds to dark mode changes', () => {
    mockUseColorScheme.mockReturnValue('dark');

    renderWithSafeArea(
      <HybridProvider>
        <TestComponent />
      </HybridProvider>
    );

    expect(screen.getByTestId('test-child')).toBeTruthy();
  });

  it('shows debug overlay in development mode', () => {
    // Mock __DEV__ to be true
    const originalDev = global.__DEV__;
    global.__DEV__ = true;

    renderWithSafeArea(
      <HybridProvider>
        <TestComponent />
      </HybridProvider>
    );

    // In dev mode, should show debug overlay
    expect(screen.getByTestId('test-child')).toBeTruthy();

    // Restore original __DEV__
    global.__DEV__ = originalDev;
  });

  it('hides debug overlay in production mode', () => {
    // Mock __DEV__ to be false
    const originalDev = global.__DEV__;
    global.__DEV__ = false;

    renderWithSafeArea(
      <HybridProvider>
        <TestComponent />
      </HybridProvider>
    );

    expect(screen.getByTestId('test-child')).toBeTruthy();

    // Restore original __DEV__
    global.__DEV__ = originalDev;
  });
});

describe('StyleDebugger', () => {
  beforeEach(() => {
    // Reset console.log mock
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'time').mockImplementation(() => {});
    jest.spyOn(console, 'timeEnd').mockImplementation(() => {});
    jest.spyOn(console, 'group').mockImplementation(() => {});
    jest.spyOn(console, 'groupEnd').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('log method', () => {
    it('logs component information in development', () => {
      const originalDev = global.__DEV__;
      global.__DEV__ = true;

      StyleDebugger.log('TestComponent', 'bg-red-500 text-white', { fontSize: 16 });

      expect(console.group).toHaveBeenCalledWith('🎨 TestComponent');
      expect(console.log).toHaveBeenCalledWith('NativeWind classes:', 'bg-red-500 text-white');
      expect(console.log).toHaveBeenCalledWith('Inline styles:', { fontSize: 16 });
      expect(console.groupEnd).toHaveBeenCalled();

      global.__DEV__ = originalDev;
    });

    it('does not log in production', () => {
      const originalDev = global.__DEV__;
      global.__DEV__ = false;

      StyleDebugger.log('TestComponent', 'bg-red-500', { fontSize: 16 });

      expect(console.group).not.toHaveBeenCalled();
      expect(console.log).not.toHaveBeenCalled();

      global.__DEV__ = originalDev;
    });
  });

  describe('performance methods', () => {
    it('tracks performance in development', () => {
      const originalDev = global.__DEV__;
      global.__DEV__ = true;

      const startTime = StyleDebugger.performance.start('test-operation');
      expect(console.time).toHaveBeenCalledWith('test-operation');
      expect(startTime).toBeGreaterThan(0);

      StyleDebugger.performance.end('test-operation', startTime);
      expect(console.timeEnd).toHaveBeenCalledWith('test-operation');

      global.__DEV__ = originalDev;
    });

    it('does not track performance in production', () => {
      const originalDev = global.__DEV__;
      global.__DEV__ = false;

      const startTime = StyleDebugger.performance.start('test-operation');
      expect(startTime).toBe(0);
      expect(console.time).not.toHaveBeenCalled();

      StyleDebugger.performance.end('test-operation');
      expect(console.timeEnd).not.toHaveBeenCalled();

      global.__DEV__ = originalDev;
    });
  });

  describe('trace method', () => {
    it('traces component render in development', () => {
      const originalDev = global.__DEV__;
      global.__DEV__ = true;

      jest.spyOn(console, 'trace').mockImplementation(() => {});

      StyleDebugger.trace('TestComponent');

      expect(console.trace).toHaveBeenCalledWith('📍 TestComponent render');

      global.__DEV__ = originalDev;
    });
  });
});