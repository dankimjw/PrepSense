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
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { apiClient } from '../../services/apiClient';
import { formatQuantity } from '../../utils/numberFormatting';
import { PantryItemSelectionModal } from './PantryItemSelectionModal';

interface QuickCompleteModalProps {
  visible: boolean;
  onClose: () => void;
  onConfirm: () => void;
  recipeId: number;
  recipeName: string;
  userId: number;
  servings?: number;
}

interface PantryItem {
  pantryItemId: number;
  pantryItemName: string;
  quantityAvailable: number;
  unit: string;
  expirationDate?: string;
  addedDate?: string;
  daysUntilExpiry?: number;
}

interface IngredientSelection {
  ingredientName: string;
  requiredQuantity: number;
  requiredUnit: string;
  selectedItem?: PantryItem;
  availableItems: PantryItem[];
  status: 'available' | 'partial' | 'missing';
}

interface IngredientCheck {
  ingredients: Array<{
    ingredient_name: string;
    required_quantity: number;
    required_unit: string;
    pantry_matches: Array<{
      pantry_item_id: number;
      pantry_item_name: string;
      quantity_available: number;
      unit: string;
      expiration_date?: string;
      created_at?: string;
      days_until_expiry?: number;
    }>;
    status: 'available' | 'partial' | 'missing';
  }>;
}

export const QuickCompleteModal: React.FC<QuickCompleteModalProps> = ({
  visible,
  onClose,
  onConfirm,
  recipeId,
  recipeName,
  userId,
  servings = 1,
}) => {
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [ingredientSelections, setIngredientSelections] = useState<IngredientSelection[]>([]);
  const [selectedIngredient, setSelectedIngredient] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch ingredient availability when modal opens
  useEffect(() => {
    if (visible) {
      fetchIngredientAvailability();
    }
  }, [visible, recipeId, userId, servings]);

  const fetchIngredientAvailability = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.post('/recipe-consumption/check-ingredients', {
        user_id: userId,
        recipe_id: recipeId,
        servings: servings,
      });

      if (response.data && response.data.ingredients) {
        const selections = response.data.ingredients.map((ing: any) => ({
          ingredientName: ing.ingredient_name,
          requiredQuantity: ing.required_quantity,
          requiredUnit: ing.required_unit,
          status: ing.status,
          availableItems: ing.pantry_matches.map((match: any) => ({
            pantryItemId: match.pantry_item_id,
            pantryItemName: match.pantry_item_name,
            quantityAvailable: match.quantity_available,
            unit: match.unit,
            expirationDate: match.expiration_date,
            addedDate: match.created_at,
            daysUntilExpiry: match.days_until_expiry,
          })),
          // Auto-select closest expiration item
          selectedItem: ing.pantry_matches.length > 0 ? {
            pantryItemId: ing.pantry_matches[0].pantry_item_id,
            pantryItemName: ing.pantry_matches[0].pantry_item_name,
            quantityAvailable: ing.pantry_matches[0].quantity_available,
            unit: ing.pantry_matches[0].unit,
            expirationDate: ing.pantry_matches[0].expiration_date,
            addedDate: ing.pantry_matches[0].created_at,
            daysUntilExpiry: ing.pantry_matches[0].days_until_expiry,
          } : undefined,
        }));

        setIngredientSelections(selections);
      }
    } catch (error) {
      console.error('Error fetching ingredient availability:', error);
      setError('Failed to load ingredient information');
    } finally {
      setLoading(false);
    }
  };

  const handleIngredientClick = (ingredientName: string) => {
    const ingredient = ingredientSelections.find(ing => ing.ingredientName === ingredientName);
    if (ingredient && ingredient.availableItems.length > 1) {
      setSelectedIngredient(ingredientName);
    }
  };

  const handleItemSelected = (item: PantryItem) => {
    setIngredientSelections(prev =>
      prev.map(ing =>
        ing.ingredientName === selectedIngredient
          ? { ...ing, selectedItem: item }
          : ing
      )
    );
    setSelectedIngredient(null);
  };

  const handleQuickComplete = async () => {
    try {
      setCompleting(true);
      
      // Build ingredient selections for API
      const ingredientSelectionPayload = ingredientSelections
        .filter(ing => ing.selectedItem)
        .map(ing => ({
          ingredient_name: ing.ingredientName,
          pantry_item_id: ing.selectedItem!.pantryItemId,
          quantity_to_use: Math.min(ing.requiredQuantity, ing.selectedItem!.quantityAvailable),
          unit: ing.requiredUnit,
        }));

      const response = await apiClient.post('/recipe-consumption/quick-complete', {
        user_id: userId,
        recipe_id: recipeId,
        servings: servings,
        ingredient_selections: ingredientSelectionPayload,
      });

      if (response.data?.success) {
        Alert.alert(
          'Recipe Completed!',
          response.data.message || 'Your recipe has been completed successfully!',
          [
            {
              text: 'OK',
              onPress: () => {
                onConfirm();
              },
            },
          ]
        );
      } else {
        throw new Error(response.data?.message || 'Failed to complete recipe');
      }
    } catch (error) {
      console.error('Error completing recipe:', error);
      Alert.alert(
        'Error',
        'Failed to complete recipe. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setCompleting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'available':
        return { name: 'checkmark-circle', color: '#059669' };
      case 'partial':
        return { name: 'warning', color: '#F59E0B' };
      case 'missing':
        return { name: 'close-circle', color: '#DC2626' };
      default:
        return { name: 'help-circle', color: '#6B7280' };
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'available':
        return 'Available';
      case 'partial':
        return 'Partially available';
      case 'missing':
        return 'Missing';
      default:
        return 'Unknown';
    }
  };

  const canComplete = ingredientSelections.some(ing => ing.status === 'available' || ing.status === 'partial');

  if (!visible) return null;

  return (
    <>
      <Modal
        visible={visible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={onClose}
      >
        <SafeAreaView style={styles.container}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color="#333" />
            </TouchableOpacity>
            <Text style={styles.title}>Quick Complete Recipe</Text>
            <View style={styles.placeholder} />
          </View>

          {/* Recipe Info */}
          <View style={styles.recipeInfo}>
            <Text style={styles.recipeName}>{recipeName}</Text>
            <Text style={styles.servingsText}>Servings: {servings}</Text>
          </View>

          {/* Content */}
          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#6366F1" />
              <Text style={styles.loadingText}>Checking ingredient availability...</Text>
            </View>
          ) : error ? (
            <View style={styles.errorContainer}>
              <Ionicons name="alert-circle" size={48} color="#DC2626" />
              <Text style={styles.errorText}>{error}</Text>
              <TouchableOpacity
                style={styles.retryButton}
                onPress={fetchIngredientAvailability}
              >
                <Text style={styles.retryButtonText}>Try Again</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              {/* Ingredients List */}
              <ScrollView style={styles.ingredientsList} showsVerticalScrollIndicator={false}>
                {ingredientSelections.map((ingredient, index) => {
                  const statusIcon = getStatusIcon(ingredient.status);
                  const hasMultipleOptions = ingredient.availableItems.length > 1;
                  
                  return (
                    <TouchableOpacity
                      key={index}
                      style={[
                        styles.ingredientCard,
                        ingredient.status === 'missing' && styles.ingredientCardMissing,
                      ]}
                      onPress={() => hasMultipleOptions && handleIngredientClick(ingredient.ingredientName)}
                      activeOpacity={hasMultipleOptions ? 0.7 : 1}
                      disabled={!hasMultipleOptions}
                    >
                      <View style={styles.ingredientHeader}>
                        <View style={styles.ingredientInfo}>
                          <Text style={styles.ingredientName}>
                            {ingredient.ingredientName}
                          </Text>
                          <Text style={styles.requiredQuantity}>
                            {formatQuantity(ingredient.requiredQuantity)} {ingredient.requiredUnit} needed
                          </Text>
                        </View>
                        
                        <View style={styles.statusContainer}>
                          <Ionicons
                            name={statusIcon.name as any}
                            size={20}
                            color={statusIcon.color}
                          />
                          <Text style={[styles.statusText, { color: statusIcon.color }]}>
                            {getStatusText(ingredient.status)}
                          </Text>
                        </View>
                      </View>

                      {/* Selected Item Display */}
                      {ingredient.selectedItem && (
                        <View style={styles.selectedItemContainer}>
                          <Text style={styles.usingLabel}>Using:</Text>
                          <Text style={styles.selectedItemName}>
                            {ingredient.selectedItem.pantryItemName}
                          </Text>
                          {ingredient.selectedItem.daysUntilExpiry !== undefined && (
                            <Text style={[
                              styles.expirationInfo,
                              { color: ingredient.selectedItem.daysUntilExpiry <= 3 ? '#F59E0B' : '#059669' }
                            ]}>
                              {ingredient.selectedItem.daysUntilExpiry === 0
                                ? 'Expires today'
                                : ingredient.selectedItem.daysUntilExpiry === 1
                                ? 'Expires tomorrow'
                                : `Expires in ${ingredient.selectedItem.daysUntilExpiry} days`
                              }
                            </Text>
                          )}
                        </View>
                      )}

                      {/* Multiple Options Indicator */}
                      {hasMultipleOptions && (
                        <View style={styles.multipleOptionsIndicator}>
                          <Text style={styles.multipleOptionsText}>
                            {ingredient.availableItems.length} options available
                          </Text>
                          <Ionicons name="chevron-forward" size={16} color="#6366F1" />
                        </View>
                      )}
                    </TouchableOpacity>
                  );
                })}
              </ScrollView>

              {/* Action Buttons */}
              <View style={styles.actions}>
                <TouchableOpacity
                  style={styles.cancelButton}
                  onPress={onClose}
                  activeOpacity={0.7}
                >
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[
                    styles.completeButton,
                    (!canComplete || completing) && styles.completeButtonDisabled,
                  ]}
                  onPress={handleQuickComplete}
                  activeOpacity={0.7}
                  disabled={!canComplete || completing}
                >
                  {completing ? (
                    <ActivityIndicator size="small" color="#fff" />
                  ) : (
                    <>
                      <Ionicons name="flash" size={20} color="#fff" />
                      <Text style={styles.completeButtonText}>Complete Recipe</Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>
            </>
          )}
        </SafeAreaView>
      </Modal>

      {/* Item Selection Modal */}
      {selectedIngredient && (
        <PantryItemSelectionModal
          visible={!!selectedIngredient}
          ingredientName={selectedIngredient}
          requiredQuantity={
            ingredientSelections.find(ing => ing.ingredientName === selectedIngredient)?.requiredQuantity || 0
          }
          requiredUnit={
            ingredientSelections.find(ing => ing.ingredientName === selectedIngredient)?.requiredUnit || ''
          }
          availableItems={
            ingredientSelections.find(ing => ing.ingredientName === selectedIngredient)?.availableItems || []
          }
          currentSelection={
            ingredientSelections.find(ing => ing.ingredientName === selectedIngredient)?.selectedItem
          }
          onSelect={handleItemSelected}
          onClose={() => setSelectedIngredient(null)}
        />
      )}
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  closeButton: {
    padding: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  placeholder: {
    width: 32,
  },
  
  // Recipe Info
  recipeInfo: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#f8f9fa',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  recipeName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  servingsText: {
    fontSize: 14,
    color: '#666',
  },
  
  // Loading/Error States
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  errorText: {
    fontSize: 16,
    color: '#DC2626',
    textAlign: 'center',
    marginVertical: 16,
  },
  retryButton: {
    backgroundColor: '#6366F1',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  
  // Ingredients List
  ingredientsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  ingredientCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginVertical: 6,
    padding: 16,
    borderWidth: 1,
    borderColor: '#f0f0f0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  ingredientCardMissing: {
    backgroundColor: '#fef2f2',
    borderColor: '#fecaca',
  },
  ingredientHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  ingredientInfo: {
    flex: 1,
  },
  ingredientName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  requiredQuantity: {
    fontSize: 14,
    color: '#666',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  
  // Selected Item
  selectedItemContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  usingLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  selectedItemName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  expirationInfo: {
    fontSize: 12,
    fontWeight: '500',
  },
  
  // Multiple Options
  multipleOptionsIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  multipleOptionsText: {
    fontSize: 12,
    color: '#6366F1',
    fontWeight: '600',
  },
  
  // Actions
  actions: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#f8f9fa',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  completeButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#6366F1',
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  completeButtonDisabled: {
    backgroundColor: '#ddd',
  },
  completeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});