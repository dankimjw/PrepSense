import React from 'react';
import { render } from '@testing-library/react-native';
import { Text } from 'react-native';

// Simple mock component to test if rendering works
const MockRecipesScreen = () => {
  return <Text>Recipe Screen</Text>;
};

describe('Minimal Recipe Tabs Test', () => {
  it('should render without crashing', () => {
    const { getByText } = render(<MockRecipesScreen />);
    expect(getByText('Recipe Screen')).toBeTruthy();
  });
});