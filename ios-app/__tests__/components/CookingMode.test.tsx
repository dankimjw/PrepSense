import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react-native';
import { useLocalSearchParams } from 'expo-router';
import CookingModeScreen from '../../app/cooking-mode';

// Mock expo-router
jest.mock('expo-router', () => ({
  useLocalSearchParams: jest.fn(),
  useRouter: () => ({
    back: jest.fn(),
  }),
}));

// Mock the API functions
jest.mock('../../services/api', () => ({
  completeRecipe: jest.fn(),
  fetchPantryItems: jest.fn().mockResolvedValue([]),
}));

const mockRecipe = {
  id: 1,
  name: 'Test Recipe',
  instructions: [
    'Heat oil in a large pan over medium heat for 5 minutes',
    'Add onions and cook until translucent',
    'Season with salt and pepper',
  ],
  ingredients: [
    { ingredient_name: 'Oil', quantity: 2, unit: 'tbsp' },
    { ingredient_name: 'Onions', quantity: 1, unit: 'medium' },
  ],
};

describe('CookingModeScreen Navigation Arrows', () => {
  beforeEach(() => {
    (useLocalSearchParams as jest.Mock).mockReturnValue({
      recipe: JSON.stringify(mockRecipe),
    });
  });

  it('should show right arrow on first step and hide left arrow', () => {
    render(<CookingModeScreen />);
    
    // Should show right arrow since we're not on the last step
    expect(screen.getByTestId('right-arrow')).toBeTruthy();
    
    // Should not show left arrow since we're on the first step
    expect(screen.queryByTestId('left-arrow')).toBeNull();
  });

  it('should show both arrows on middle steps', async () => {
    render(<CookingModeScreen />);
    
    // Navigate to second step
    const nextButton = screen.getByText('Next');
    fireEvent.press(nextButton);
    
    // Should show both arrows on middle step
    expect(screen.getByTestId('left-arrow')).toBeTruthy();
    expect(screen.getByTestId('right-arrow')).toBeTruthy();
  });

  it('should hide right arrow on last step and show left arrow', async () => {
    render(<CookingModeScreen />);
    
    // Navigate to last step
    const nextButton = screen.getByText('Next');
    fireEvent.press(nextButton); // Go to step 2
    fireEvent.press(nextButton); // Go to step 3 (last)
    
    // Should show left arrow but not right arrow on last step
    expect(screen.getByTestId('left-arrow')).toBeTruthy();
    expect(screen.queryByTestId('right-arrow')).toBeNull();
  });

  it('should navigate to previous step when left arrow is pressed', async () => {
    render(<CookingModeScreen />);
    
    // Navigate to second step first
    const nextButton = screen.getByText('Next');
    fireEvent.press(nextButton);
    
    // Verify we're on step 2
    expect(screen.getByText('Step 2 of 3')).toBeTruthy();
    
    // Press left arrow to go back
    const leftArrow = screen.getByTestId('left-arrow');
    fireEvent.press(leftArrow);
    
    // Should be back to step 1
    expect(screen.getByText('Step 1 of 3')).toBeTruthy();
    expect(screen.getByText(mockRecipe.instructions[0])).toBeTruthy();
  });

  it('should navigate to next step when right arrow is pressed', () => {
    render(<CookingModeScreen />);
    
    // Verify we're on step 1
    expect(screen.getByText('Step 1 of 3')).toBeTruthy();
    
    // Press right arrow to go forward
    const rightArrow = screen.getByTestId('right-arrow');
    fireEvent.press(rightArrow);
    
    // Should be on step 2
    expect(screen.getByText('Step 2 of 3')).toBeTruthy();
    expect(screen.getByText(mockRecipe.instructions[1])).toBeTruthy();
  });

  it('should display correct instruction text for each step', () => {
    render(<CookingModeScreen />);
    
    // Check first step
    expect(screen.getByText(mockRecipe.instructions[0])).toBeTruthy();
    
    // Navigate to second step
    const rightArrow = screen.getByTestId('right-arrow');
    fireEvent.press(rightArrow);
    
    // Check second step instruction
    expect(screen.getByText(mockRecipe.instructions[1])).toBeTruthy();
  });
});