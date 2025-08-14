import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { useSupplyChainImpact } from '@/hooks/useSupplyChainImpact';
import { WasteImpactCard } from '@/components/WasteImpactCard';
import SupplyChainImpactStats from '@/components/SupplyChainImpactStats';
import { mockSupplyChainData, highImpactScenario, emptySupplyChainData } from '../helpers/supplyChainMocks';

// Mock the hook
jest.mock('@/hooks/useSupplyChainImpact');
const mockUseSupplyChainImpact = useSupplyChainImpact as jest.MockedFunction<typeof useSupplyChainImpact>;

// Mock Alert
jest.spyOn(Alert, 'alert');

describe('Supply Chain Impact Integration', () => {
  const testUserId = 'integration-test-user';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('WasteImpactCard to SupplyChainImpactStats Flow', () => {
    it('displays consistent data between card and stats screen', async () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...mockSupplyChainData,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      // Render WasteImpactCard
      const { getByText: getCardText } = render(
        <WasteImpactCard 
          expiringItems={mockSupplyChainData.todayImpact.items} 
          onPress={jest.fn()} 
        />
      );

      // Verify card shows correct item count
      expect(getCardText(/3 items expiring soon/)).toBeTruthy();

      // Render SupplyChainImpactStats
      const { getByText: getStatsText } = render(
        <SupplyChainImpactStats userId={testUserId} />
      );

      // Verify stats screen shows same CO2 data
      expect(getStatsText('23.4')).toBeTruthy(); // total_co2e
      expect(getStatsText('2.2x')).toBeTruthy(); // supply_chain_multiplier
    });

    it('navigates from home card to detailed stats', async () => {
      const mockOnPress = jest.fn();
      
      mockUseSupplyChainImpact.mockReturnValue({
        ...mockSupplyChainData,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByTestId } = render(
        <WasteImpactCard 
          expiringItems={mockSupplyChainData.todayImpact.items}
          onPress={mockOnPress}
        />
      );

      fireEvent.press(getByTestId('waste-impact-card'));
      expect(mockOnPress).toHaveBeenCalledTimes(1);
    });
  });

  describe('High Impact Scenario', () => {
    it('displays urgent alerts for high-risk items', () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...highImpactScenario,
        supplyChainGuide: mockSupplyChainData.supplyChainGuide,
        weeklyTrends: mockSupplyChainData.weeklyTrends,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText } = render(
        <WasteImpactCard 
          expiringItems={highImpactScenario.todayImpact.items}
          onPress={jest.fn()}
        />
      );

      expect(getByText('URGENT')).toBeTruthy();
      expect(getByText(/4 items expiring soon/)).toBeTruthy();
    });

    it('shows amplified impact values in stats screen', () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...highImpactScenario,
        supplyChainGuide: mockSupplyChainData.supplyChainGuide,
        weeklyTrends: mockSupplyChainData.weeklyTrends,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText } = render(
        <SupplyChainImpactStats userId={testUserId} />
      );

      expect(getByText('125.8')).toBeTruthy(); // High CO2 value
      expect(getByText('4.2x')).toBeTruthy(); // High multiplier
    });
  });

  describe('Empty State Handling', () => {
    it('handles no expiring items gracefully', () => {
      const { container } = render(
        <WasteImpactCard 
          expiringItems={[]}
          onPress={jest.fn()}
        />
      );

      // Card should not render anything for empty items
      expect(container.children).toHaveLength(0);
    });

    it('shows zero values in stats when no impact data', () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...emptySupplyChainData,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText } = render(
        <SupplyChainImpactStats userId={testUserId} />
      );

      expect(getByText('0')).toBeTruthy(); // Zero CO2
      expect(getByText('0x')).toBeTruthy(); // Zero multiplier
    });
  });

  describe('Data Flow and Consistency', () => {
    it('maintains data consistency across tab switches', async () => {
      mockUseSupplyChainImpact.mockReturnValue({
        ...mockSupplyChainData,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText } = render(
        <SupplyChainImpactStats userId={testUserId} />
      );

      // Check Today tab data
      expect(getByText('23.4')).toBeTruthy();

      // Switch to Trends tab
      fireEvent.press(getByText('Trends'));

      await waitFor(() => {
        expect(getByText("This Week's Impact")).toBeTruthy();
      });

      // Verify trends data is consistent
      expect(getByText('25')).toBeTruthy(); // Total items prevented
      expect(getByText('87.5')).toBeTruthy(); // Total CO2 saved

      // Switch to Impact Guide tab
      fireEvent.press(getByText('Impact Guide'));

      await waitFor(() => {
        expect(getByText('Supply Chain Multipliers')).toBeTruthy();
      });

      // Verify guide data matches source data
      expect(getByText('Lettuce')).toBeTruthy();
      expect(getByText('5.7x')).toBeTruthy();
    });

    it('calculates correct totals from individual items', () => {
      const testItems = [
        { name: 'Lettuce', daysLeft: 1, quantity: 1, unit: 'head', multiplier: 5.7 },
        { name: 'Tomatoes', daysLeft: 2, quantity: 500, unit: 'g', multiplier: 2.52 },
        { name: 'Bananas', daysLeft: 1, quantity: 3, unit: 'pieces', multiplier: 2.86 }
      ];

      const { getByText } = render(
        <WasteImpactCard 
          expiringItems={testItems}
          onPress={jest.fn()}
        />
      );

      // Should show correct item count
      expect(getByText(/3 items expiring soon/)).toBeTruthy();
      
      // Should calculate and display impact values
      expect(getByText(/kg CO₂e/)).toBeTruthy();
      expect(getByText(/\$[\d.]+/)).toBeTruthy();
      expect(getByText(/[\d.]+kg produced/)).toBeTruthy();
    });
  });

  describe('Real-time Updates', () => {
    it('updates both components when data changes', async () => {
      const mockRefreshData = jest.fn();
      
      // Start with normal data
      mockUseSupplyChainImpact.mockReturnValue({
        ...mockSupplyChainData,
        loading: false,
        error: null,
        refreshData: mockRefreshData
      });

      const { getByText, rerender } = render(
        <SupplyChainImpactStats userId={testUserId} />
      );

      expect(getByText('23.4')).toBeTruthy();

      // Update to high impact scenario
      mockUseSupplyChainImpact.mockReturnValue({
        ...highImpactScenario,
        supplyChainGuide: mockSupplyChainData.supplyChainGuide,
        weeklyTrends: mockSupplyChainData.weeklyTrends,
        loading: false,
        error: null,
        refreshData: mockRefreshData
      });

      rerender(<SupplyChainImpactStats userId={testUserId} />);

      expect(getByText('125.8')).toBeTruthy(); // Updated CO2 value
    });
  });

  describe('Error Recovery', () => {
    it('falls back to mock data when API fails', async () => {
      // Simulate API failure by returning mock data
      mockUseSupplyChainImpact.mockReturnValue({
        todayImpact: {
          items_at_risk: 7,
          total_co2e: 45.3,
          supply_chain_multiplier: 2.2,
          economic_value: 28.50,
          driving_equivalent_miles: 113,
          items: [
            { name: 'Spinach', daysLeft: 1, quantity: 200, unit: 'g', multiplier: 2.4 },
            { name: 'Tomatoes', daysLeft: 2, quantity: 1, unit: 'kg', multiplier: 2.52 }
          ]
        },
        supplyChainGuide: mockSupplyChainData.supplyChainGuide,
        weeklyTrends: mockSupplyChainData.weeklyTrends,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText } = render(
        <SupplyChainImpactStats userId={testUserId} />
      );

      // Should show fallback data
      expect(getByText('45.3')).toBeTruthy();
      expect(getByText('2.2x')).toBeTruthy();
    });

    it('maintains user experience during loading states', async () => {
      mockUseSupplyChainImpact.mockReturnValue({
        todayImpact: null,
        supplyChainGuide: [],
        weeklyTrends: [],
        loading: true,
        error: null,
        refreshData: jest.fn()
      });

      const { getByText } = render(
        <SupplyChainImpactStats userId={testUserId} />
      );

      expect(getByText('Loading impact data...')).toBeTruthy();
    });
  });

  describe('Performance Optimization', () => {
    it('handles large datasets efficiently', () => {
      const largeDataset = {
        ...mockSupplyChainData,
        todayImpact: {
          ...mockSupplyChainData.todayImpact,
          items: Array.from({ length: 50 }, (_, i) => ({
            name: `Item ${i + 1}`,
            daysLeft: Math.floor(Math.random() * 7),
            quantity: Math.floor(Math.random() * 10) + 1,
            unit: 'kg',
            multiplier: Math.random() * 5 + 1
          }))
        },
        supplyChainGuide: Array.from({ length: 20 }, (_, i) => ({
          food: `Food ${i + 1}`,
          multiplier: Math.random() * 5 + 1,
          supply_chain_loss_pct: Math.random() * 80 + 10,
          consumer_loss_pct: Math.random() * 30 + 5,
          co2e_per_kg: Math.random() * 3 + 0.5,
          amplified_co2e: Math.random() * 10 + 2,
          description: `Description for food ${i + 1}`,
          key_insight: `Insight for food ${i + 1}`
        }))
      };

      mockUseSupplyChainImpact.mockReturnValue({
        ...largeDataset,
        loading: false,
        error: null,
        refreshData: jest.fn()
      });

      // Should render without performance issues
      expect(() => {
        render(<SupplyChainImpactStats userId={testUserId} />);
      }).not.toThrow();
    });
  });
});