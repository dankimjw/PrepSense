import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import SupplyChainImpactStats from '@/components/SupplyChainImpactStats';
import { useSupplyChainImpact } from '@/hooks/useSupplyChainImpact';
import { mockSupplyChainData, loadingState, errorState } from '../helpers/supplyChainMocks';

// Mock the hook
jest.mock('@/hooks/useSupplyChainImpact');
const mockUseSupplyChainImpact = useSupplyChainImpact as jest.MockedFunction<typeof useSupplyChainImpact>;

describe('SupplyChainImpactStats', () => {
  const defaultUserId = 'test-user-123';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('displays loading indicator', () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...loadingState,
        refreshData: jest.fn()
      });

      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      expect(getByText('Loading impact data...')).toBeTruthy();
    });
  });

  describe('Success State', () => {
    beforeEach(() => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...mockSupplyChainData,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });
    });

    it('renders header and navigation tabs', () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      expect(getByText('Supply Chain Impact')).toBeTruthy();
      expect(getByText('See the full journey of your food')).toBeTruthy();
      expect(getByText('Today')).toBeTruthy();
      expect(getByText('Trends')).toBeTruthy();
      expect(getByText('Impact Guide')).toBeTruthy();
    });

    it('displays today tab by default', () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      expect(getByText("Today's Impact")).toBeTruthy();
      expect(getByText(/kg CO₂e at risk/)).toBeTruthy();
      expect(getByText(/supply chain impact/)).toBeTruthy();
    });

    it('shows today impact metrics', () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      expect(getByText('23.4')).toBeTruthy(); // total_co2e
      expect(getByText('2.2x')).toBeTruthy(); // supply_chain_multiplier
    });

    it('displays supply chain breakdown', () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      expect(getByText('Supply Chain Breakdown')).toBeTruthy();
      expect(getByText('Food reaching your kitchen:')).toBeTruthy();
      expect(getByText('45%')).toBeTruthy();
      expect(getByText('Lost at farm & harvest:')).toBeTruthy();
      expect(getByText('25%')).toBeTruthy();
    });

    it('switches to trends tab when tapped', async () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      fireEvent.press(getByText('Trends'));
      
      await waitFor(() => {
        expect(getByText("This Week's Impact")).toBeTruthy();
      });
    });

    it('displays weekly trends data', async () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      fireEvent.press(getByText('Trends'));
      
      await waitFor(() => {
        expect(getByText('25')).toBeTruthy(); // items saved (12+13)
        expect(getByText('8')).toBeTruthy(); // items wasted (3+5)
        expect(getByText('87.5')).toBeTruthy(); // CO2e saved (42.0+45.5)
      });
    });

    it('shows achievement messages in trends', async () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      fireEvent.press(getByText('Trends'));
      
      await waitFor(() => {
        expect(getByText(/Great job! You saved the equivalent of:/)).toBeTruthy();
        expect(getByText(/miles of driving/)).toBeTruthy();
        expect(getByText(/upstream production waste/)).toBeTruthy();
      });
    });

    it('switches to impact guide tab', async () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      fireEvent.press(getByText('Impact Guide'));
      
      await waitFor(() => {
        expect(getByText('Supply Chain Multipliers')).toBeTruthy();
        expect(getByText('How much was originally produced for each food type')).toBeTruthy();
      });
    });

    it('displays supply chain guide items', async () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      fireEvent.press(getByText('Impact Guide'));
      
      await waitFor(() => {
        expect(getByText('Lettuce')).toBeTruthy();
        expect(getByText('5.7x')).toBeTruthy();
        expect(getByText('82.5% lost in supply chain')).toBeTruthy();
        expect(getByText('Tomatoes')).toBeTruthy();
        expect(getByText('2.52x')).toBeTruthy();
      });
    });

    it('shows CO2 calculations in impact guide', async () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      fireEvent.press(getByText('Impact Guide'));
      
      await waitFor(() => {
        expect(getByText(/CO₂: 1.5 kg\/kg → 8.6 kg\/kg wasted/)).toBeTruthy();
        expect(getByText(/CO₂: 2.09 kg\/kg → 5.3 kg\/kg wasted/)).toBeTruthy();
      });
    });

    it('highlights active tab', async () => {
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      // Today tab should be active by default
      const todayTab = getByText('Today');
      expect(todayTab.props.style).toMatchObject(
        expect.objectContaining({ color: '#3b82f6' })
      );
      
      // Switch to trends tab
      fireEvent.press(getByText('Trends'));
      
      await waitFor(() => {
        const trendsTab = getByText('Trends');
        expect(trendsTab.props.style).toMatchObject(
          expect.objectContaining({ color: '#3b82f6' })
        );
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles null today impact data', () => {
      mockUseSupplyChainImpact.mockReturnValue({
        todayImpact: null,
        supplyChainGuide: [],
        weeklyTrends: [],
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      expect(getByText('Loading impact data...')).toBeTruthy();
    });

    it('handles empty supply chain guide', async () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...mockSupplyChainData,
        supplyChainGuide: [],
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText, queryByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      fireEvent.press(getByText('Impact Guide'));
      
      await waitFor(() => {
        expect(getByText('Supply Chain Multipliers')).toBeTruthy();
        expect(queryByText('Lettuce')).toBeNull();
        expect(queryByText('Tomatoes')).toBeNull();
      });
    });

    it('handles empty weekly trends', async () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...mockSupplyChainData,
        weeklyTrends: [],
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      fireEvent.press(getByText('Trends'));
      
      await waitFor(() => {
        expect(getByText("This Week's Impact")).toBeTruthy();
        expect(getByText('0')).toBeTruthy(); // Should show 0 for all metrics
      });
    });

    it('handles zero impact values', () => {
      const zeroImpactData = {
        ...mockSupplyChainData,
        todayImpact: {
          ...mockSupplyChainData.todayImpact,
          items_at_risk: 0,
          total_co2e: 0,
          supply_chain_multiplier: 0,
          economic_value: 0,
          driving_equivalent_miles: 0,
          items: []
        },
        loading: false,
        error: null,
        refreshData: jest.fn()
      };

      mockUseSupplyChainImpact.mockReturnValue(zeroImpactData);

      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      
      expect(getByText('0')).toBeTruthy(); // total_co2e
      expect(getByText('0x')).toBeTruthy(); // supply_chain_multiplier
    });
  });

  describe('Error State', () => {
    it('still renders with error but no crash', () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...errorState,
        refreshData: jest.fn()
      });

      // Component should handle error gracefully and show loading state
      const { getByText } = render(<SupplyChainImpactStats userId={defaultUserId} />);
      expect(getByText('Loading impact data...')).toBeTruthy();
    });
  });

  describe('User ID Prop', () => {
    it('passes correct user ID to hook', () => {
      const testUserId = 'custom-user-456';
      mockUseSupplyChainImpact.mockReturnValue({
        ...mockSupplyChainData,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      render(<SupplyChainImpactStats userId={testUserId} />);
      
      expect(mockUseSupplyChainImpact).toHaveBeenCalledWith(testUserId);
    });
  });
});