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

      parsedIngredients.forEach(parsed => {
        if (!parsed.name) return;

        // Find matching pantry items
        const matchingItems = pantryItems.filter(item => 
          item.item_name.toLowerCase().includes(parsed.name.toLowerCase()) ||
          parsed.name.toLowerCase().includes(item.item_name.toLowerCase())
        );

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

        // Calculate total available and max usable
        let totalAvailable = 0;
        const pantryItemsData = matchingItems.map(item => {
          const available = item.quantity_amount || 0;
          totalAvailable += available;
          
          return {
            id: item.id,
            name: item.item_name,
            availableQuantity: available,
            unit: item.quantity_unit || 'unit',
            maxUsable: available // For now, assume 1:1 conversion
          };
        });

        const requestedAmount = parsed.quantity || 0;
        const maxPossible = Math.min(requestedAmount, totalAvailable);

        usages.push({
          ingredientName: parsed.name,
          requestedQuantity: requestedAmount,
          requestedUnit: parsed.unit || 'unit',
          pantryItems: pantryItemsData,
          selectedAmount: maxPossible,
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
              Needs: {usage.requestedQuantity} {usage.requestedUnit}
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
              {usage.pantryItems.map((item, itemIndex) => (
                <Text key={itemIndex} style={styles.pantryItemText}>
                  • {item.name}: {item.availableQuantity} {item.unit}
                </Text>
              ))}
            </View>

            <View style={styles.sliderContainer}>
              <Text style={styles.sliderLabel}>
                Use: {usage.selectedAmount.toFixed(1)} {usage.requestedUnit} 
                ({usagePercentage.toFixed(0)}% of recipe requirement)
              </Text>
              
              <Slider
                style={styles.slider}
                minimumValue={0}
                maximumValue={usage.maxPossible}
                value={usage.selectedAmount}
                onValueChange={(value) => updateIngredientAmount(index, value)}
                minimumTrackTintColor={isFullyUsed ? '#10B981' : '#F59E0B'}
                maximumTrackTintColor="#E5E7EB"
                thumbStyle={styles.sliderThumb}
                trackStyle={styles.sliderTrack}
                step={0.1}
              />
              
              <View style={styles.sliderLabels}>
                <Text style={styles.sliderLabelText}>0</Text>
                <Text style={styles.sliderLabelText}>
                  Max: {usage.maxPossible.toFixed(1)}
                </Text>
              </View>
            </View>

            {usage.selectedAmount < usage.requestedQuantity && (
              <View style={styles.shortfallWarning}>
                <Ionicons name="warning" size={16} color="#F59E0B" />
                <Text style={styles.shortfallText}>
                  Short by {(usage.requestedQuantity - usage.selectedAmount).toFixed(1)} {usage.requestedUnit}
                </Text>
              </View>
            )}
          </>
        ) : (
          <View style={styles.unavailableInfo}>
            <Text style={styles.unavailableText}>
              Not available in your pantry
            </Text>
            <TouchableOpacity style={styles.addToShoppingButton}>
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
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
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
  sliderContainer: {
    marginBottom: 12,
  },
  sliderLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderThumb: {
    backgroundColor: '#6366F1',
    width: 20,
    height: 20,
  },
  sliderTrack: {
    height: 4,
    borderRadius: 2,
  },
  sliderLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: -8,
  },
  sliderLabelText: {
    fontSize: 12,
    color: '#9CA3AF',
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