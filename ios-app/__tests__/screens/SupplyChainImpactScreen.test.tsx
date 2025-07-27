import React from 'react';
import { render } from '@testing-library/react-native';
import SupplyChainImpactScreen from '@/app/supply-chain-impact';
import { useRouter } from 'expo-router';
import { useSupplyChainImpact } from '@/hooks/useSupplyChainImpact';
import { mockSupplyChainData } from '../helpers/supplyChainMocks';

// Mock expo-router
jest.mock('expo-router', () => ({
  Stack: {
    Screen: ({ options }: any) => {
      // Render the header component if provided
      if (options?.header) {
        return options.header();
      }
      return null;
    }
  },
  useRouter: jest.fn()
}));

// Mock the hook
jest.mock('@/hooks/useSupplyChainImpact');
const mockUseSupplyChainImpact = useSupplyChainImpact as jest.MockedFunction<typeof useSupplyChainImpact>;

// Mock the SupplyChainImpactStats component
jest.mock('@/components/SupplyChainImpactStats', () => ({
  SupplyChainImpactStats: ({ userId }: { userId: string }) => {
    const MockedComponent = require('react-native').Text;
    return <MockedComponent testID="supply-chain-impact-stats">Supply Chain Stats for {userId}</MockedComponent>;
  }
}));

// Mock CustomHeader
jest.mock('@/app/components/CustomHeader', () => ({
  CustomHeader: ({ title, showBackButton, onBackPress }: any) => {
    const MockedComponent = require('react-native').View;
    const MockedText = require('react-native').Text;
    const MockedTouchable = require('react-native').TouchableOpacity;
    return (
      <MockedComponent testID="custom-header">
        <MockedText testID="header-title">{title}</MockedText>
        {showBackButton && (
          <MockedTouchable testID="back-button" onPress={onBackPress}>
            <MockedText>Back</MockedText>
          </MockedTouchable>
        )}
      </MockedComponent>
    );
  }
}));

describe('SupplyChainImpactScreen', () => {
  const mockRouter = {
    back: jest.fn(),
    push: jest.fn(),
    replace: jest.fn(),
    canGoBack: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    
    mockUseSupplyChainImpact.mockReturnValue({
      ...mockSupplyChainData,
      loading: false,
      error: null,
      refreshData: jest.fn()
    });
  });

  it('renders the screen with correct structure', () => {
    const { getByTestId } = render(<SupplyChainImpactScreen />);
    
    // Check that the main container exists
    expect(getByTestId('supply-chain-impact-stats')).toBeTruthy();
  });

  it('passes correct userId to SupplyChainImpactStats', () => {
    const { getByText } = render(<SupplyChainImpactScreen />);
    
    expect(getByText('Supply Chain Stats for demo_user')).toBeTruthy();
  });

  it('renders custom header with correct props', () => {
    const { getByTestId, getByText } = render(<SupplyChainImpactScreen />);
    
    expect(getByTestId('custom-header')).toBeTruthy();
    expect(getByText('Supply Chain Impact')).toBeTruthy();
    expect(getByTestId('back-button')).toBeTruthy();
  });

  it('calls router.back when back button is pressed', () => {
    const { getByTestId } = render(<SupplyChainImpactScreen />);
    
    const backButton = getByTestId('back-button');
    backButton.props.onPress();
    
    expect(mockRouter.back).toHaveBeenCalledTimes(1);
  });

  it('applies correct styles to container', () => {
    const { getByTestId } = render(<SupplyChainImpactScreen />);
    
    const container = getByTestId('supply-chain-impact-stats').parent;
    expect(container.props.style).toMatchObject({
      flex: 1,
      backgroundColor: '#f9fafb'
    });
  });

  it('renders with accessibility support', () => {
    const { getByTestId } = render(<SupplyChainImpactScreen />);
    
    // Check that components have test IDs for accessibility
    expect(getByTestId('supply-chain-impact-stats')).toBeTruthy();
    expect(getByTestId('custom-header')).toBeTruthy();
  });

  describe('Navigation Integration', () => {
    it('uses expo-router navigation', () => {
      render(<SupplyChainImpactScreen />);
      
      expect(useRouter).toHaveBeenCalled();
    });

    it('configures Stack.Screen correctly', () => {
      // This test ensures the Stack.Screen is properly configured
      // The actual configuration is tested through the header rendering
      const { getByTestId } = render(<SupplyChainImpactScreen />);
      
      expect(getByTestId('custom-header')).toBeTruthy();
    });
  });

  describe('Component Integration', () => {
    it('integrates with SupplyChainImpactStats component', () => {
      const { getByTestId } = render(<SupplyChainImpactScreen />);
      
      const statsComponent = getByTestId('supply-chain-impact-stats');
      expect(statsComponent).toBeTruthy();
      expect(statsComponent.props.children).toContain('demo_user');
    });

    it('maintains consistent styling with app theme', () => {
      const { getByTestId } = render(<SupplyChainImpactScreen />);
      
      const container = getByTestId('supply-chain-impact-stats').parent;
      expect(container.props.style.backgroundColor).toBe('#f9fafb');
    });
  });

  describe('Error Handling', () => {
    it('renders without crashing when router is undefined', () => {
      (useRouter as jest.Mock).mockReturnValue(undefined);
      
      // Should not crash even with undefined router
      expect(() => render(<SupplyChainImpactScreen />)).not.toThrow();
    });

    it('handles missing router methods gracefully', () => {
      (useRouter as jest.Mock).mockReturnValue({});
      
      const { getByTestId } = render(<SupplyChainImpactScreen />);
      
      // Should render without error
      expect(getByTestId('supply-chain-impact-stats')).toBeTruthy();
    });
  });

  describe('Screen Lifecycle', () => {
    it('renders immediately without loading state', () => {
      const { getByTestId } = render(<SupplyChainImpactScreen />);
      
      // Should render stats component immediately
      expect(getByTestId('supply-chain-impact-stats')).toBeTruthy();
    });

    it('persists across re-renders', () => {
      const { getByTestId, rerender } = render(<SupplyChainImpactScreen />);
      
      expect(getByTestId('supply-chain-impact-stats')).toBeTruthy();
      
      rerender(<SupplyChainImpactScreen />);
      
      expect(getByTestId('supply-chain-impact-stats')).toBeTruthy();
    });
  });
});