import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { WasteImpactCard } from '@/components/WasteImpactCard';
import { createMockExpiringItem } from '../helpers/supplyChainMocks';

describe('WasteImpactCard', () => {
  const mockOnPress = jest.fn();
  
  const defaultProps = {
    expiringItems: [
      createMockExpiringItem({ name: 'Lettuce', daysLeft: 1, quantity: 1, unit: 'head' }),
      createMockExpiringItem({ name: 'Tomatoes', daysLeft: 2, quantity: 500, unit: 'g' }),
      createMockExpiringItem({ name: 'Bananas', daysLeft: 1, quantity: 3, unit: 'pieces' })
    ],
    onPress: mockOnPress
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders waste impact alert with correct data', () => {
    const { getByText } = render(<WasteImpactCard {...defaultProps} />);
    
    expect(getByText('🌍 Waste Impact Alert')).toBeTruthy();
    expect(getByText(/3 items expiring soon/)).toBeTruthy();
  });

  it('displays CO2 impact and driving equivalent', () => {
    const { getByText } = render(<WasteImpactCard {...defaultProps} />);
    
    // Should show CO2 impact
    expect(getByText(/kg CO₂e/)).toBeTruthy();
    // Should show driving equivalent  
    expect(getByText(/= \d+ miles/)).toBeTruthy();
  });

  it('displays economic value at risk', () => {
    const { getByText } = render(<WasteImpactCard {...defaultProps} />);
    
    expect(getByText(/\$[\d.]+/)).toBeTruthy();
    expect(getByText('economic value')).toBeTruthy();
  });

  it('shows supply chain multiplier effect', () => {
    const { getByText } = render(<WasteImpactCard {...defaultProps} />);
    
    expect(getByText(/[\d.]+kg produced/)).toBeTruthy();
    expect(getByText('supply chain')).toBeTruthy();
  });

  it('displays urgent badge for high-risk items', () => {
    const urgentItems = [
      createMockExpiringItem({ name: 'Lettuce', daysLeft: 0, multiplier: 5.7 }),
      createMockExpiringItem({ name: 'Berries', daysLeft: 0, multiplier: 4.1 })
    ];
    
    const { getByText } = render(
      <WasteImpactCard {...defaultProps} expiringItems={urgentItems} />
    );
    
    expect(getByText('URGENT')).toBeTruthy();
  });

  it('shows motivational message', () => {
    const { getByText } = render(<WasteImpactCard {...defaultProps} />);
    
    expect(getByText(/Preventing their waste saves the entire supply chain impact!/)).toBeTruthy();
  });

  it('displays call-to-action', () => {
    const { getByText } = render(<WasteImpactCard {...defaultProps} />);
    
    expect(getByText('Tap to see waste-smart recipes →')).toBeTruthy();
  });

  it('calls onPress when tapped', () => {
    const { getByTestId } = render(<WasteImpactCard {...defaultProps} />);
    
    fireEvent.press(getByTestId('waste-impact-card'));
    expect(mockOnPress).toHaveBeenCalledTimes(1);
  });

  it('handles empty expiring items', () => {
    const { queryByText } = render(
      <WasteImpactCard {...defaultProps} expiringItems={[]} />
    );
    
    // Should not render anything for empty items
    expect(queryByText('🌍 Waste Impact Alert')).toBeNull();
  });

  it('handles single expiring item', () => {
    const singleItem = [
      createMockExpiringItem({ name: 'Lettuce', daysLeft: 1, quantity: 1, unit: 'head' })
    ];
    
    const { getByText } = render(
      <WasteImpactCard {...defaultProps} expiringItems={singleItem} />
    );
    
    expect(getByText(/1 item expiring soon/)).toBeTruthy();
  });

  it('formats quantities correctly', () => {
    const items = [
      createMockExpiringItem({ name: 'Lettuce', quantity: 2, unit: 'heads' }),
      createMockExpiringItem({ name: 'Milk', quantity: 1.5, unit: 'L' })
    ];
    
    const { getByText } = render(
      <WasteImpactCard {...defaultProps} expiringItems={items} />
    );
    
    expect(getByText(/2 items expiring soon/)).toBeTruthy();
  });

  it('calculates correct total impact', () => {
    const highImpactItems = [
      createMockExpiringItem({ 
        name: 'Lettuce', 
        daysLeft: 0, 
        quantity: 2, 
        unit: 'heads',
        multiplier: 5.7 
      }),
      createMockExpiringItem({ 
        name: 'Avocados', 
        daysLeft: 1, 
        quantity: 4, 
        unit: 'pieces',
        multiplier: 3.8 
      })
    ];
    
    const { getByText } = render(
      <WasteImpactCard {...defaultProps} expiringItems={highImpactItems} />
    );
    
    // Should show higher CO2 and economic values due to multipliers
    expect(getByText(/kg CO₂e/)).toBeTruthy();
    expect(getByText(/\$[\d.]+/)).toBeTruthy();
  });
});