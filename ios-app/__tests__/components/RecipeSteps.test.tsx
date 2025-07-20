import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { View, Text, StyleSheet } from 'react-native';

// Simple RecipeSteps component for testing
const RecipeSteps = ({ steps, testID = 'recipe-steps' }) => {
  return (
    <View testID={testID}>
      {steps.map((step, index) => (
        <View key={index} style={styles.stepRow} testID={`step-${index}`}>
          <View style={styles.stepNumber}>
            <Text style={styles.stepNumberText}>{index + 1}</Text>
          </View>
          <Text style={styles.stepText} testID={`step-text-${index}`}>
            {step}
          </Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  stepRow: {
    flexDirection: 'row',
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  stepNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#E0E0E0',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
  },
  stepText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
});

describe('RecipeSteps', () => {
  describe('Rendering all steps', () => {
    it('should render all recipe steps', () => {
      const steps = ['Chop onions', 'Saute vegetables', 'Simmer sauce'];
      const { getAllByTestId, getByText } = render(
        <RecipeSteps steps={steps} />
      );

      // Verify the correct number of steps are rendered
      const stepElements = getAllByTestId(/^step-\d+$/);
      expect(stepElements).toHaveLength(steps.length);

      // Verify each step text is rendered
      steps.forEach(step => {
        expect(getByText(step)).toBeTruthy();
      });
    });

    it('should render empty list when no steps provided', () => {
      const { queryByTestId } = render(
        <RecipeSteps steps={[]} />
      );

      expect(queryByTestId('step-0')).toBeNull();
    });

    it('should render step numbers correctly', () => {
      const steps = ['Step one', 'Step two', 'Step three'];
      const { getByText } = render(
        <RecipeSteps steps={steps} />
      );

      // Check step numbers
      expect(getByText('1')).toBeTruthy();
      expect(getByText('2')).toBeTruthy();
      expect(getByText('3')).toBeTruthy();
    });

    it('should handle long recipe with many steps', () => {
      const longRecipeSteps = Array.from({ length: 20 }, (_, i) => `Step ${i + 1}: Do something`);
      const { getAllByTestId } = render(
        <RecipeSteps steps={longRecipeSteps} />
      );

      const stepElements = getAllByTestId(/^step-\d+$/);
      expect(stepElements).toHaveLength(20);
    });

    it('should preserve step order', () => {
      const steps = ['First step', 'Second step', 'Third step', 'Fourth step'];
      const { getAllByTestId } = render(
        <RecipeSteps steps={steps} />
      );

      const stepTexts = getAllByTestId(/^step-text-\d+$/);
      
      stepTexts.forEach((element, index) => {
        expect(element.children[0]).toBe(steps[index]);
      });
    });
  });

  describe('Edge cases', () => {
    it('should handle steps with special characters', () => {
      const steps = [
        'Heat oil to 350°F',
        'Add 1/2 cup of flour & mix',
        'Season with salt, pepper, and herbs'
      ];
      const { getByText } = render(
        <RecipeSteps steps={steps} />
      );

      steps.forEach(step => {
        expect(getByText(step)).toBeTruthy();
      });
    });

    it('should handle very long step descriptions', () => {
      const longStep = 'Take the chicken breast and carefully slice it horizontally to create a pocket. ' +
        'Be sure not to cut all the way through. Season the inside of the pocket with salt, pepper, and ' +
        'your favorite herbs. Stuff with cheese and spinach mixture, then secure with toothpicks.';
      
      const steps = ['Preheat oven', longStep, 'Bake for 25 minutes'];
      const { getByText } = render(
        <RecipeSteps steps={steps} />
      );

      expect(getByText(longStep)).toBeTruthy();
    });

    it('should handle steps with line breaks', () => {
      const steps = [
        'Step 1:\n- Chop vegetables\n- Prepare sauce',
        'Step 2:\nCombine all ingredients'
      ];
      const { getByText } = render(
        <RecipeSteps steps={steps} />
      );

      steps.forEach(step => {
        expect(getByText(step)).toBeTruthy();
      });
    });
  });
});

// Test for list components
describe('List Rendering', () => {
  const ListComponent = ({ items, testID = 'list' }) => (
    <View testID={testID}>
      {items.map((item, index) => (
        <Text key={index} testID={`item-${index}`}>
          {item}
        </Text>
      ))}
    </View>
  );

  it('should render all items in a list', () => {
    const items = ['Milk', 'Eggs', 'Flour', 'Sugar', 'Butter'];
    const { getAllByTestId, getByText } = render(
      <ListComponent items={items} />
    );

    const itemElements = getAllByTestId(/^item-\d+$/);
    expect(itemElements).toHaveLength(items.length);

    items.forEach(item => {
      expect(getByText(item)).toBeTruthy();
    });
  });

  it('should handle empty lists', () => {
    const { queryByTestId } = render(
      <ListComponent items={[]} />
    );

    expect(queryByTestId('item-0')).toBeNull();
  });

  it('should maintain item order', () => {
    const items = ['First', 'Second', 'Third'];
    const { getAllByTestId } = render(
      <ListComponent items={items} />
    );

    const itemElements = getAllByTestId(/^item-\d+$/);
    itemElements.forEach((element, index) => {
      expect(element.children[0]).toBe(items[index]);
    });
  });
});