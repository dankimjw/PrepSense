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
// Slider removed - using quick amount buttons instead
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
}

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

  useEffect(() => {
    if (visible && recipe?.ingredients) {
      calculateIngredientUsages();
    }
  }, [visible, recipe, pantryItems]);

  const calculateIngredientUsages = () => {
    setIsCalculating(true);
    
    try {
      const parsedIngredients = parseIngredientsList(recipe.ingredients);
      const usages: IngredientUsage[] = [];

      recipe.ingredients.forEach((ingredient, idx) => {
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

  const updateIngredientAmount = (index: number, newAmount: number) => {
    setIngredientUsages(prev => 
      prev.map((usage, i) => 
        i === index ? { ...usage, selectedAmount: newAmount } : usage
      )
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

    onConfirm(ingredientUsages);
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
          <View style={styles.statusIndicator}>
            <Ionicons 
              name={isAvailable ? 'checkmark-circle' : 'close-circle'} 
              size={24} 
              color={isAvailable ? '#10B981' : '#EF4444'} 
            />
          </View>
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
              <Text style={styles.amountLabel}>
                Use: {formatQuantity(usage.selectedAmount)} {usage.requestedUnit} 
                ({Math.round(usagePercentage)}% of recipe requirement)
              </Text>
              
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
                  <Text style={[
                    styles.amountButtonSubtext,
                    usage.selectedAmount === 0 && styles.amountButtonTextSelected
                  ]}>0 {usage.requestedUnit}</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  testID={`use-half-${index}`}
                  onPress={() => updateIngredientAmount(index, Math.min(usage.requestedQuantity * 0.5, usage.maxPossible))}
                  style={[
                    styles.amountButton,
                    Math.abs(usage.selectedAmount - (usage.requestedQuantity * 0.5)) < 0.01 && styles.amountButtonSelected
                  ]}
                >
                  <Text style={[
                    styles.amountButtonText,
                    Math.abs(usage.selectedAmount - (usage.requestedQuantity * 0.5)) < 0.01 && styles.amountButtonTextSelected
                  ]}>Half</Text>
                  <Text style={[
                    styles.amountButtonSubtext,
                    Math.abs(usage.selectedAmount - (usage.requestedQuantity * 0.5)) < 0.01 && styles.amountButtonTextSelected
                  ]}>
                    {formatQuantity(Math.min(usage.requestedQuantity * 0.5, usage.maxPossible))} {usage.requestedUnit}
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  testID={`use-most-${index}`}
                  onPress={() => updateIngredientAmount(index, Math.min(usage.requestedQuantity * 0.75, usage.maxPossible))}
                  style={[
                    styles.amountButton,
                    Math.abs(usage.selectedAmount - (usage.requestedQuantity * 0.75)) < 0.01 && styles.amountButtonSelected
                  ]}
                >
                  <Text style={[
                    styles.amountButtonText,
                    Math.abs(usage.selectedAmount - (usage.requestedQuantity * 0.75)) < 0.01 && styles.amountButtonTextSelected
                  ]}>Most</Text>
                  <Text style={[
                    styles.amountButtonSubtext,
                    Math.abs(usage.selectedAmount - (usage.requestedQuantity * 0.75)) < 0.01 && styles.amountButtonTextSelected
                  ]}>
                    {formatQuantity(Math.min(usage.requestedQuantity * 0.75, usage.maxPossible))} {usage.requestedUnit}
                  </Text>
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
                  <Text style={[
                    styles.amountButtonSubtext,
                    usage.selectedAmount === usage.maxPossible && styles.amountButtonTextSelected
                  ]}>
                    {formatQuantity(usage.maxPossible)} {usage.requestedUnit}
                  </Text>
                </TouchableOpacity>
              </View>
              
              {/* Visual progress bar (non-interactive) */}
              <View style={styles.progressBar}>
                <View 
                  style={[
                    styles.progressFill, 
                    { 
                      width: `${usage.maxPossible > 0 ? (usage.selectedAmount / usage.maxPossible) * 100 : 0}%`,
                      backgroundColor: isFullyUsed ? '#10B981' : '#F59E0B'
                    }
                  ]}
                />
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
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  unavailableCard: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
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
    marginBottom: 12,
  },
  amountLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 12,
  },
  quickAmounts: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    gap: 8,
  },
  amountButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#F9FAFB',
    alignItems: 'center',
  },
  amountButtonSelected: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
  },
  amountButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 2,
  },
  amountButtonTextSelected: {
    color: '#fff',
  },
  amountButtonSubtext: {
    fontSize: 11,
    color: '#6B7280',
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
    paddingVertical: 16,
  },
  unavailableText: {
    fontSize: 14,
    color: '#DC2626',
    marginBottom: 12,
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
});