// components/modals/RecipeCompletionModal.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';
import { RecipeIngredient, PantryItem } from '../../services/api';
import { parseIngredientsList } from '../../utils/ingredientParser';
import { formatQuantity } from '../../utils/numberFormatting';

interface IngredientUsage {
  ingredientName: string;
  requestedQuantity: number;
  requestedUnit: string;
  pantryItems: {
    id: string;
    name: string;
    availableQuantity: number;
    unit: string;
    maxUsable: number;
  }[];
  selectedAmount: number;
  maxPossible: number;
  conversionNote?: string;
  selectedUnit?: string; // Unit user selected for conversion
  convertedAmount?: number; // Amount after conversion
}

// Unit conversion utilities
const UNIT_CONVERSIONS: Record<string, Record<string, number>> = {
  // Volume conversions
  'tsp': { 'tbsp': 1/3, 'cup': 1/48, 'ml': 5, 'l': 0.005, 'oz': 0.167 },
  'tbsp': { 'tsp': 3, 'cup': 1/16, 'ml': 15, 'l': 0.015, 'oz': 0.5 },
  'cup': { 'tsp': 48, 'tbsp': 16, 'ml': 237, 'l': 0.237, 'oz': 8 },
  'ml': { 'tsp': 0.2, 'tbsp': 0.067, 'cup': 0.0042, 'l': 0.001, 'oz': 0.034 },
  'l': { 'tsp': 200, 'tbsp': 67, 'cup': 4.2, 'ml': 1000, 'oz': 34 },
  'oz': { 'tsp': 6, 'tbsp': 2, 'cup': 0.125, 'ml': 30, 'l': 0.03 },
  
  // Weight conversions
  'g': { 'kg': 0.001, 'oz': 0.035, 'lb': 0.0022 },
  'kg': { 'g': 1000, 'oz': 35.3, 'lb': 2.2 },
  'oz': { 'g': 28.35, 'kg': 0.028, 'lb': 0.0625 },
  'lb': { 'g': 454, 'kg': 0.454, 'oz': 16 },
};

const getCompatibleUnits = (unit: string): string[] => {
  const normalizedUnit = unit.toLowerCase();
  const allUnits = new Set<string>();
  
  // Add the original unit
  allUnits.add(normalizedUnit);
  
  // Find all units that can be converted to/from this unit
  Object.keys(UNIT_CONVERSIONS).forEach(fromUnit => {
    if (fromUnit === normalizedUnit || UNIT_CONVERSIONS[fromUnit][normalizedUnit]) {
      allUnits.add(fromUnit);
      Object.keys(UNIT_CONVERSIONS[fromUnit]).forEach(toUnit => {
        allUnits.add(toUnit);
      });
    }
  });
  
  return Array.from(allUnits);
};

const convertUnits = (amount: number, fromUnit: string, toUnit: string): number => {
  if (fromUnit === toUnit) return amount;
  
  const from = fromUnit.toLowerCase();
  const to = toUnit.toLowerCase();
  
  if (UNIT_CONVERSIONS[from]?.[to]) {
    return amount * UNIT_CONVERSIONS[from][to];
  }
  
  // Try reverse conversion
  if (UNIT_CONVERSIONS[to]?.[from]) {
    return amount / UNIT_CONVERSIONS[to][from];
  }
  
  // No conversion available
  return amount;
};

// Calculate appropriate step size for slider based on unit and max value
const calculateStepSize = (maxValue: number, unit: string): number => {
  const normalizedUnit = unit.toLowerCase();
  
  // Step sizes based on unit type and common cooking measurements
  const stepSizes: Record<string, number> = {
    // Small volume units - use small precise steps
    'tsp': 0.25,
    'tbsp': 0.25,
    
    // Medium volume units
    'cup': 0.125, // 1/8 cup increments
    'ml': maxValue <= 50 ? 5 : maxValue <= 250 ? 10 : 25,
    'l': 0.1,
    'oz': 0.25,
    
    // Weight units
    'g': maxValue <= 100 ? 5 : maxValue <= 500 ? 10 : 25,
    'kg': 0.1,
    'lb': 0.25,
    
    // Count-based units
    'unit': 1,
    'each': 1,
    'piece': 1,
    'cloves': 1,
    'dozen': 1,
    'bunch': 0.25,
    'bunches': 0.25,
  };
  
  const baseStep = stepSizes[normalizedUnit];
  if (baseStep) return baseStep;
  
  // Default step calculation for unknown units
  if (maxValue <= 1) return 0.1;
  if (maxValue <= 5) return 0.25;
  if (maxValue <= 20) return 0.5;
  if (maxValue <= 100) return 1;
  return Math.ceil(maxValue / 20); // About 20 steps
};

interface RecipeCompletionModalProps {
  visible: boolean;
  onClose: () => void;
  onConfirm: (ingredientUsages: IngredientUsage[]) => void;
  recipe: {
    name: string;
    ingredients: string[];
    pantry_item_matches?: Record<string, Array<{
      pantry_item_id: number;
      product_name: string;
      quantity: number;
      unit: string;
    }>>;
  };
  pantryItems: PantryItem[];
  loading?: boolean;
}

export const RecipeCompletionModal: React.FC<RecipeCompletionModalProps> = ({
  visible,
  onClose,
  onConfirm,
  recipe,
  pantryItems,
  loading = false,
}) => {
  const [ingredientUsages, setIngredientUsages] = useState<IngredientUsage[]>([]);
  const [isCalculating, setIsCalculating] = useState(false);
  const [activeUnitPicker, setActiveUnitPicker] = useState<{ index: number; units: string[] } | null>(null);

  useEffect(() => {
    if (visible && recipe?.ingredients) {
      calculateIngredientUsages();
    }
  }, [visible, recipe, pantryItems]);

  const calculateIngredientUsages = () => {
    setIsCalculating(true);
    
    try {
      // Validate ingredients array exists and is not undefined
      if (!recipe.ingredients || !Array.isArray(recipe.ingredients)) {
        console.error('Recipe ingredients are undefined or not an array:', recipe);
        setIngredientUsages([]);
        setIsCalculating(false);
        return;
      }

      // Filter out any undefined/null ingredients and ingredients with empty names
      const validIngredients = recipe.ingredients.filter(ing => {
        if (!ing || ing === undefined || ing === null) {
          console.warn('Filtering out undefined/null ingredient:', ing);
          return false;
        }
        
        // Check if ingredient has a valid name (for string ingredients)
        if (typeof ing === 'string') {
          if (!ing.trim()) {
            console.warn('Filtering out empty string ingredient:', ing);
            return false;
          }
          return true;
        }
        
        // Check if ingredient object has a valid name property
        if (typeof ing === 'object') {
          const name = ing.name || ing.ingredient_name || ing.original || '';
          if (!name || !name.trim()) {
            console.warn('Filtering out ingredient with empty name:', ing);
            return false;
          }
          return true;
        }
        
        console.warn('Filtering out ingredient with unknown type:', typeof ing, ing);
        return false;
      });
      
      if (validIngredients.length === 0) {
        console.error('No valid ingredients found in recipe');
        setIngredientUsages([]);
        setIsCalculating(false);
        return;
      }

      const parsedIngredients = parseIngredientsList(validIngredients);
      const usages: IngredientUsage[] = [];

      validIngredients.forEach((ingredient, idx) => {
        const parsed = parsedIngredients[idx];
        if (!parsed || !parsed.name) return;

        // First check if we have pantry_item_matches from the backend
        let matchingItems = [];
        
        if (recipe.pantry_item_matches && recipe.pantry_item_matches[ingredient]) {
          // Use the pre-calculated matches from backend
          const backendMatches = recipe.pantry_item_matches[ingredient];
          matchingItems = pantryItems.filter(item => {
            // Handle both id formats (pantry_item_id from backend, id from transformed)
            const itemId = item.id || item.pantry_item_id;
            // Convert both to strings for comparison to handle type mismatches
            return backendMatches.some(match => 
              String(match.pantry_item_id) === String(itemId) ||
              Number(match.pantry_item_id) === Number(itemId)
            );
          });
          
          // Debug logging removed for cleaner test output
        } else {
          // Fallback to local matching
          matchingItems = pantryItems.filter(item => {
            // Use item_name (transformed) or product_name (original)
            const itemName = (item.item_name || item.product_name || '').toLowerCase();
            const parsedName = parsed.name.toLowerCase();
            
            // More flexible matching
            return itemName.includes(parsedName) || 
                   parsedName.includes(itemName) ||
                   // Also check for partial matches (e.g., "milk" matches "whole milk")
                   itemName.split(' ').some(word => parsedName.includes(word)) ||
                   parsedName.split(' ').some(word => itemName.includes(word));
          });
        }

        if (matchingItems.length === 0) {
          // No matching items found
          usages.push({
            ingredientName: parsed.name,
            requestedQuantity: parsed.quantity || 0,
            requestedUnit: parsed.unit || 'unit',
            pantryItems: [],
            selectedAmount: 0,
            maxPossible: 0
          });
          return;
        }

        // Group matching items by expiration date to handle legitimate duplicates
        const itemGroups = matchingItems.reduce((groups, item) => {
          const expDate = item.expiration_date || 'no-expiration';
          const key = `${expDate}`;
          
          if (!groups[key]) {
            groups[key] = {
              items: [],
              totalQuantity: 0,
              expirationDate: item.expiration_date,
              unit: item.quantity_unit || item.unit_of_measurement || 'unit'
            };
          }
          
          groups[key].items.push(item);
          groups[key].totalQuantity += parseFloat(item.quantity_amount || item.quantity || 0);
          
          return groups;
        }, {});
        
        // Convert groups to pantry items data, sorted by expiration
        let totalAvailable = 0;
        const pantryItemsData = Object.entries(itemGroups)
          .sort(([a], [b]) => {
            // Sort by expiration date, earliest first
            if (a === 'no-expiration') return 1;
            if (b === 'no-expiration') return -1;
            return new Date(a) - new Date(b);
          })
          .map(([expDate, group]) => {
            totalAvailable += group.totalQuantity;
            
            // Create a display name that includes count if multiple items
            const baseName = group.items[0].item_name || group.items[0].product_name || 'Unknown Item';
            const displayName = group.items.length > 1 
              ? `${baseName} (${group.items.length} items)`
              : baseName;
            
            return {
              id: group.items[0].id || group.items[0].pantry_item_id,
              name: displayName,
              availableQuantity: group.totalQuantity,
              unit: group.unit,
              maxUsable: group.totalQuantity,
              expirationDate: group.expirationDate,
              itemCount: group.items.length,
              items: group.items // Keep reference to all items in this group
            };
          });

        const requestedAmount = parsed.quantity || 0;
        const maxPossible = Math.min(requestedAmount, totalAvailable);

        usages.push({
          ingredientName: parsed.name,
          requestedQuantity: requestedAmount,
          requestedUnit: parsed.unit || 'unit',
          pantryItems: pantryItemsData,
          selectedAmount: maxPossible > 0 ? maxPossible : 0, // Default to max if available
          maxPossible: maxPossible,
          selectedUnit: parsed.unit || 'unit', // Default to requested unit
          convertedAmount: maxPossible > 0 ? maxPossible : 0,
          conversionNote: pantryItemsData.length > 0 && 
            pantryItemsData[0].unit !== parsed.unit ? 
            `Converting from ${pantryItemsData[0].unit} to ${parsed.unit}` : 
            undefined
        });
      });

      setIngredientUsages(usages);
    } catch (error) {
      console.error('Error calculating ingredient usages:', error);
      Alert.alert('Error', 'Failed to calculate ingredient usage. Please try again.');
    } finally {
      setIsCalculating(false);
    }
  };

  const snapToStep = (value: number, stepSize: number, maxValue: number): number => {
    // Round to nearest step
    const snapped = Math.round(value / stepSize) * stepSize;
    // Ensure within bounds
    return Math.max(0, Math.min(snapped, maxValue));
  };

  const updateIngredientAmount = (index: number, newAmount: number) => {
    setIngredientUsages(prev => 
      prev.map((usage, i) => {
        if (i !== index) return usage;
        
        // Calculate step size for current unit
        const currentUnit = usage.selectedUnit || usage.requestedUnit;
        const stepSize = calculateStepSize(usage.maxPossible, currentUnit);
        
        // Snap to appropriate step
        const snappedAmount = snapToStep(newAmount, stepSize, usage.maxPossible);
        
        return { 
          ...usage, 
          selectedAmount: snappedAmount, 
          convertedAmount: snappedAmount 
        };
      })
    );
  };

  const updateIngredientUnit = (index: number, newUnit: string) => {
    setIngredientUsages(prev => 
      prev.map((usage, i) => {
        if (i !== index) return usage;
        
        // Convert the amount to the new unit
        const convertedAmount = convertUnits(
          usage.selectedAmount, 
          usage.selectedUnit || usage.requestedUnit, 
          newUnit
        );
        
        return { 
          ...usage, 
          selectedUnit: newUnit,
          convertedAmount: convertedAmount
        };
      })
    );
  };

  const handleConfirm = () => {
    // Check if any ingredients are available at all
    const hasAvailableIngredients = ingredientUsages.some(usage => usage.maxPossible > 0);
    
    if (!hasAvailableIngredients) {
      Alert.alert(
        'No Ingredients Available',
        'None of the recipe ingredients are available in your pantry. Would you like to add them to your shopping list?',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Add to Shopping List', 
            onPress: () => {
              // Close modal and navigate to shopping list
              onClose();
              // You can add navigation to shopping list here
            }
          }
        ]
      );
      return;
    }
    
    // Validate that we have some ingredients selected
    const hasSelectedIngredients = ingredientUsages.some(usage => usage.selectedAmount > 0);
    
    if (!hasSelectedIngredients) {
      Alert.alert(
        'No Ingredients Selected',
        'Please select at least some ingredients to use for this recipe.',
        [{ text: 'OK' }]
      );
      return;
    }

    // Additional validation to ensure no undefined ingredients are passed
    const validUsages = ingredientUsages.filter(usage => {
      if (!usage || !usage.ingredientName || !usage.ingredientName.trim()) {
        console.warn('Filtering out invalid ingredient usage:', usage);
        return false;
      }
      return usage.selectedAmount > 0;
    });

    if (validUsages.length === 0) {
      console.error('No valid ingredient usages after filtering');
      Alert.alert(
        'Error',
        'Unable to process ingredients. Please try again.',
        [{ text: 'OK' }]
      );
      return;
    }

    console.log('Sending valid ingredient usages:', validUsages.length, 'out of', ingredientUsages.length);
    onConfirm(validUsages);
  };

  const getTotalIngredients = () => ingredientUsages.length;
  const getAvailableIngredients = () => ingredientUsages.filter(usage => usage.maxPossible > 0).length;
  const getMissingIngredients = () => ingredientUsages.filter(usage => usage.maxPossible === 0).length;

  const renderIngredientUsage = (usage: IngredientUsage, index: number) => {
    const isAvailable = usage.maxPossible > 0;
    const isFullyUsed = usage.selectedAmount === usage.requestedQuantity;
    const usagePercentage = usage.requestedQuantity > 0 ? 
      (usage.selectedAmount / usage.requestedQuantity) * 100 : 0;

    return (
      <View key={index} style={[
        styles.ingredientCard,
        !isAvailable && styles.unavailableCard
      ]}>
        <View style={styles.ingredientHeader}>
          <View style={styles.ingredientInfo}>
            <Text style={styles.ingredientName}>{usage.ingredientName}</Text>
            <Text style={styles.requestedAmount}>
              Needs: {formatQuantity(usage.requestedQuantity)} {usage.requestedUnit}
            </Text>
            {usage.conversionNote && (
              <Text style={styles.conversionNote}>{usage.conversionNote}</Text>
            )}
          </View>
          {isAvailable && (
            <View style={styles.statusIndicator}>
              <Ionicons 
                name="checkmark-circle" 
                size={24} 
                color="#10B981" 
              />
            </View>
          )}
        </View>

        {isAvailable ? (
          <>
            <View style={styles.availabilityInfo}>
              <Text style={styles.availabilityText}>
                Available from {usage.pantryItems.length} item{usage.pantryItems.length > 1 ? 's' : ''}:
              </Text>
              {usage.pantryItems.map((item, itemIndex) => {
                const expirationInfo = item.expirationDate 
                  ? ` (exp: ${new Date(item.expirationDate).toLocaleDateString()})` 
                  : '';
                return (
                  <Text key={itemIndex} style={styles.pantryItemText}>
                    • {item.name}: {formatQuantity(item.availableQuantity)} {item.unit}{expirationInfo}
                  </Text>
                );
              })}
            </View>

            <View style={styles.amountSelector}>
              <View style={styles.amountHeader}>
                <Text style={styles.amountLabel}>
                  Use: {formatQuantity(usage.convertedAmount || usage.selectedAmount)} {usage.selectedUnit || usage.requestedUnit}
                </Text>
                
                {/* Unit selector dropdown */}
                <TouchableOpacity 
                  style={styles.unitDropdown}
                  onPress={() => {
                    // Show unit picker modal
                    setActiveUnitPicker({ index, units: getCompatibleUnits(usage.requestedUnit) });
                  }}
                >
                  <Text style={styles.unitDropdownText}>
                    {usage.selectedUnit || usage.requestedUnit}
                  </Text>
                  <Ionicons name="chevron-down" size={16} color="#6B7280" />
                </TouchableOpacity>
              </View>

              {/* Enhanced discrete slider */}
              <View style={styles.sliderContainer}>
                <Slider
                  style={styles.slider}
                  value={usage.selectedAmount}
                  minimumValue={0}
                  maximumValue={usage.maxPossible}
                  step={calculateStepSize(usage.maxPossible, usage.selectedUnit || usage.requestedUnit)}
                  onValueChange={(value) => updateIngredientAmount(index, value)}
                  minimumTrackTintColor={isFullyUsed ? '#10B981' : '#6366F1'}
                  maximumTrackTintColor="#E5E7EB"
                  thumbTintColor={isFullyUsed ? '#10B981' : '#6366F1'}
                  testID={`ingredient-slider-${index}`}
                />
                <View style={styles.sliderLabels}>
                  <Text style={styles.sliderLabelText}>0</Text>
                  <Text style={styles.sliderPercentage}>
                    {Math.round(usagePercentage)}%
                  </Text>
                  <Text style={styles.sliderLabelText}>{formatQuantity(usage.maxPossible)}</Text>
                </View>
                <Text style={styles.stepInfo}>
                  Step: {calculateStepSize(usage.maxPossible, usage.selectedUnit || usage.requestedUnit)} {usage.selectedUnit || usage.requestedUnit}
                </Text>
              </View>
              
              {/* Quick amount buttons */}
              <View style={styles.quickAmounts}>
                <TouchableOpacity 
                  testID={`use-none-${index}`}
                  onPress={() => updateIngredientAmount(index, 0)}
                  style={[
                    styles.amountButton, 
                    usage.selectedAmount === 0 && styles.amountButtonSelected
                  ]}
                >
                  <Text style={[
                    styles.amountButtonText,
                    usage.selectedAmount === 0 && styles.amountButtonTextSelected
                  ]}>None</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  testID={`use-quarter-${index}`}
                  onPress={() => {
                    const currentUnit = usage.selectedUnit || usage.requestedUnit;
                    const stepSize = calculateStepSize(usage.maxPossible, currentUnit);
                    const quarterAmount = snapToStep(usage.maxPossible * 0.25, stepSize, usage.maxPossible);
                    updateIngredientAmount(index, quarterAmount);
                  }}
                  style={[
                    styles.amountButton,
                    Math.abs(usage.selectedAmount - (usage.maxPossible * 0.25)) < 0.01 && styles.amountButtonSelected
                  ]}
                >
                  <Text style={[
                    styles.amountButtonText,
                    Math.abs(usage.selectedAmount - (usage.maxPossible * 0.25)) < 0.01 && styles.amountButtonTextSelected
                  ]}>1/4</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  testID={`use-half-${index}`}
                  onPress={() => {
                    const currentUnit = usage.selectedUnit || usage.requestedUnit;
                    const stepSize = calculateStepSize(usage.maxPossible, currentUnit);
                    const halfAmount = snapToStep(usage.maxPossible * 0.5, stepSize, usage.maxPossible);
                    updateIngredientAmount(index, halfAmount);
                  }}
                  style={[
                    styles.amountButton,
                    Math.abs(usage.selectedAmount - (usage.maxPossible * 0.5)) < 0.01 && styles.amountButtonSelected
                  ]}
                >
                  <Text style={[
                    styles.amountButtonText,
                    Math.abs(usage.selectedAmount - (usage.maxPossible * 0.5)) < 0.01 && styles.amountButtonTextSelected
                  ]}>Half</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  testID={`use-most-${index}`}
                  onPress={() => {
                    const currentUnit = usage.selectedUnit || usage.requestedUnit;
                    const stepSize = calculateStepSize(usage.maxPossible, currentUnit);
                    const mostAmount = snapToStep(usage.maxPossible * 0.75, stepSize, usage.maxPossible);
                    updateIngredientAmount(index, mostAmount);
                  }}
                  style={[
                    styles.amountButton,
                    Math.abs(usage.selectedAmount - (usage.maxPossible * 0.75)) < 0.01 && styles.amountButtonSelected
                  ]}
                >
                  <Text style={[
                    styles.amountButtonText,
                    Math.abs(usage.selectedAmount - (usage.maxPossible * 0.75)) < 0.01 && styles.amountButtonTextSelected
                  ]}>3/4</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  testID={`use-all-${index}`}
                  onPress={() => updateIngredientAmount(index, usage.maxPossible)}
                  style={[
                    styles.amountButton,
                    usage.selectedAmount === usage.maxPossible && styles.amountButtonSelected
                  ]}
                >
                  <Text style={[
                    styles.amountButtonText,
                    usage.selectedAmount === usage.maxPossible && styles.amountButtonTextSelected
                  ]}>All</Text>
                </TouchableOpacity>
              </View>
            </View>

            {usage.selectedAmount < usage.requestedQuantity && (
              <View style={styles.shortfallWarning}>
                <Ionicons name="warning" size={16} color="#F59E0B" />
                <Text style={styles.shortfallText}>
                  Short by {formatQuantity(usage.requestedQuantity - usage.selectedAmount)} {usage.requestedUnit}
                </Text>
              </View>
            )}
          </>
        ) : (
          <View style={styles.unavailableInfo}>
            <Text style={styles.unavailableText}>
              Not available in your pantry
            </Text>
            <TouchableOpacity 
              style={styles.addToShoppingButton}
              onPress={() => {
                // TODO: Implement actual shopping list integration
                Alert.alert(
                  'Add to Shopping List',
                  `Would add ${usage.requestedQuantity} ${usage.requestedUnit} of ${usage.ingredientName} to shopping list`,
                  [{ text: 'OK' }]
                );
              }}
            >
              <Ionicons name="add-circle-outline" size={16} color="#6B7280" />
              <Text style={styles.addToShoppingText}>Add to shopping list</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
      testID="recipe-completion-modal"
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton} testID="close-button">
            <Ionicons name="close" size={24} color="#374151" />
          </TouchableOpacity>
          <Text style={styles.title}>Complete Recipe</Text>
          <View style={styles.placeholder} />
        </View>

        <View style={styles.recipeInfo}>
          <Text style={styles.recipeName}>{recipe.name}</Text>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>{getTotalIngredients()}</Text>
              <Text style={styles.statLabel}>Total</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={[styles.statNumber, { color: '#10B981' }]}>
                {getAvailableIngredients()}
              </Text>
              <Text style={styles.statLabel}>Available</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={[styles.statNumber, { color: '#EF4444' }]}>
                {getMissingIngredients()}
              </Text>
              <Text style={styles.statLabel}>Missing</Text>
            </View>
          </View>
        </View>

        {/* Content */}
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {isCalculating ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#6366F1" />
              <Text style={styles.loadingText}>Calculating ingredient usage...</Text>
            </View>
          ) : (
            <View style={styles.ingredientsList}>
              {ingredientUsages.map(renderIngredientUsage)}
            </View>
          )}
        </ScrollView>

        {/* Footer */}
        <View style={styles.footer}>
          <TouchableOpacity 
            style={styles.cancelButton} 
            onPress={onClose}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.confirmButton, loading && styles.confirmButtonDisabled]} 
            onPress={handleConfirm}
            disabled={loading || isCalculating}
            testID="completion-confirm-button"
          >
            {loading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={20} color="#fff" />
                <Text style={styles.confirmButtonText}>Complete Recipe</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Unit Picker Modal */}
        {activeUnitPicker && (
          <Modal
            visible={true}
            transparent
            animationType="fade"
            onRequestClose={() => setActiveUnitPicker(null)}
          >
            <View style={styles.unitPickerOverlay}>
              <View style={styles.unitPickerModal}>
                <View style={styles.unitPickerHeader}>
                  <Text style={styles.unitPickerTitle}>Select Unit</Text>
                  <TouchableOpacity onPress={() => setActiveUnitPicker(null)}>
                    <Ionicons name="close" size={24} color="#374151" />
                  </TouchableOpacity>
                </View>
                
                <ScrollView style={styles.unitPickerList}>
                  {activeUnitPicker.units.map(unit => (
                    <TouchableOpacity
                      key={unit}
                      style={[
                        styles.unitPickerItem,
                        (ingredientUsages[activeUnitPicker.index]?.selectedUnit || 
                         ingredientUsages[activeUnitPicker.index]?.requestedUnit) === unit && 
                        styles.unitPickerItemSelected
                      ]}
                      onPress={() => {
                        updateIngredientUnit(activeUnitPicker.index, unit);
                        setActiveUnitPicker(null);
                      }}
                    >
                      <Text style={[
                        styles.unitPickerItemText,
                        (ingredientUsages[activeUnitPicker.index]?.selectedUnit || 
                         ingredientUsages[activeUnitPicker.index]?.requestedUnit) === unit && 
                        styles.unitPickerItemTextSelected
                      ]}>
                        {unit}
                      </Text>
                      {(ingredientUsages[activeUnitPicker.index]?.selectedUnit || 
                        ingredientUsages[activeUnitPicker.index]?.requestedUnit) === unit && (
                        <Ionicons name="checkmark" size={20} color="#6366F1" />
                      )}
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              </View>
            </View>
          </Modal>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  placeholder: {
    width: 40,
  },
  recipeInfo: {
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  recipeName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
    textAlign: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    paddingVertical: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#374151',
  },
  statLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 16,
  },
  ingredientsList: {
    paddingVertical: 16,
  },
  ingredientCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  unavailableCard: {
    backgroundColor: '#fff',
    opacity: 0.7,
  },
  ingredientHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  ingredientInfo: {
    flex: 1,
  },
  ingredientName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  requestedAmount: {
    fontSize: 14,
    color: '#6B7280',
  },
  conversionNote: {
    fontSize: 12,
    color: '#F59E0B',
    fontStyle: 'italic',
    marginTop: 2,
  },
  statusIndicator: {
    marginLeft: 12,
  },
  availabilityInfo: {
    marginBottom: 16,
  },
  availabilityText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  pantryItemText: {
    fontSize: 13,
    color: '#6B7280',
    marginLeft: 8,
    marginBottom: 2,
  },
  amountSelector: {
    marginBottom: 16,
  },
  amountHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  amountLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  unitDropdown: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FAFAFA',
    minWidth: 80,
    justifyContent: 'space-between',
  },
  unitDropdownText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginRight: 4,
  },
  sliderContainer: {
    marginBottom: 20,
    paddingVertical: 10,
  },
  slider: {
    width: '100%',
    height: 50,
  },
  sliderLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  sliderLabelText: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  sliderPercentage: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6366F1',
  },
  stepInfo: {
    fontSize: 12,
    color: '#9CA3AF',
    textAlign: 'center',
    marginTop: 4,
    fontStyle: 'italic',
  },
  quickAmounts: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    gap: 8,
  },
  amountButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#FAFAFA',
    alignItems: 'center',
  },
  amountButtonSelected: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  amountButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#374151',
  },
  amountButtonTextSelected: {
    color: '#fff',
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  shortfallWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  shortfallText: {
    fontSize: 13,
    color: '#92400E',
    marginLeft: 6,
  },
  unavailableInfo: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  unavailableText: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  addToShoppingButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  addToShoppingText: {
    fontSize: 13,
    color: '#6B7280',
    marginLeft: 6,
  },
  footer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  confirmButton: {
    flex: 2,
    flexDirection: 'row',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#6366F1',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  confirmButtonDisabled: {
    opacity: 0.6,
  },
  confirmButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  // Unit Picker Modal Styles
  unitPickerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  unitPickerModal: {
    backgroundColor: '#fff',
    borderRadius: 16,
    width: '80%',
    maxWidth: 300,
    maxHeight: '60%',
  },
  unitPickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  unitPickerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  unitPickerList: {
    maxHeight: 300,
  },
  unitPickerItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  unitPickerItemSelected: {
    backgroundColor: '#F0F4FF',
  },
  unitPickerItemText: {
    fontSize: 16,
    color: '#374151',
  },
  unitPickerItemTextSelected: {
    fontWeight: '600',
    color: '#6366F1',
  },
});