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
import { apiClient } from '../../services/apiClient';
import { formatQuantity } from '../../utils/numberFormatting';

interface QuickCompleteModalProps {
  visible: boolean;
  onClose: () => void;
  onConfirm: () => void;
  recipeId: number;
  recipeName: string;
  userId: number;
  servings?: number;
}

interface IngredientSummary {
  recipe_id: number;
  available_ingredients: string[];
  partial_ingredients: string[];
  missing_ingredients: string[];
  total_ingredients: number;
  available_count: number;
  partial_count: number;
  missing_count: number;
  availability_percentage: number;
}

interface QuickCompleteResponse {
  success: boolean;
  message: string;
  summary: {
    fully_consumed: Array<{
      ingredient: string;
      consumed_from: Array<{
        pantry_item_name: string;
        quantity_consumed: number;
        unit: string;
      }>;
    }>;
    partially_consumed: Array<{
      ingredient: string;
      consumed_from: Array<{
        pantry_item_name: string;
        quantity_consumed: number;
        unit: string;
      }>;
    }>;
    missing_ingredients: string[];
  };
}

interface ConsumptionSummary {
  success: boolean;
  recipe_title: string;
  summary: {
    total_ingredients: number;
    fully_consumed: number;
    partially_consumed: number;
    missing: number;
    pantry_items_updated: number;
  };
  consumed_ingredients: Array<{
    name: string;
    required: number;
    consumed: number;
    unit: string;
    items_used: Array<{
      name: string;
      consumed: number;
      unit: string;
      remaining: number;
    }>;
  }>;
  partial_ingredients: Array<{
    name: string;
    required: number;
    consumed: number;
    unit: string;
    shortfall: number;
  }>;
  missing_ingredients: Array<{
    name: string;
    required: number;
    unit: string;
  }>;
  message: string;
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
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<ConsumptionSummary | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (visible && !summary) {
      fetchQuickCompleteSummary();
    }
  }, [visible]);

  const fetchQuickCompleteSummary = async () => {
    setLoading(true);
    try {
      const response = await apiClient.post<IngredientSummary>('/recipe-consumption/check-ingredients', {
        recipe_id: recipeId,
        user_id: userId,
        servings,
      });
      
      if (response.data) {
        const data = response.data as IngredientSummary;
        setSummary({
          success: true,
          recipe_title: recipeName,
          summary: {
            total_ingredients: data.total_ingredients,
            fully_consumed: data.available_count,
            partially_consumed: data.partial_count,
            missing: data.missing_count,
            pantry_items_updated: 0,
          },
          consumed_ingredients: [],
          partial_ingredients: [],
          missing_ingredients: [],
          message: `Ready to quick complete ${recipeName}`,
        });
      }
    } catch (error) {
      console.error('Error fetching quick complete summary:', error);
      Alert.alert('Error', 'Failed to check ingredients availability');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleQuickComplete = async () => {
    setConfirming(true);
    try {
      const response = await apiClient.post<QuickCompleteResponse>('/recipe-consumption/quick-complete', {
        recipe_id: recipeId,
        user_id: userId,
        servings,
      });

      const data = response.data as QuickCompleteResponse;
      if (data?.success) {
        Alert.alert(
          'Recipe Completed!',
          data.message,
          [
            {
              text: 'OK',
              onPress: () => {
                onConfirm();
                onClose();
              },
            },
          ]
        );
      }
    } catch (error) {
      console.error('Error completing recipe:', error);
      Alert.alert('Error', 'Failed to complete recipe. Please try again.');
    } finally {
      setConfirming(false);
    }
  };

  const renderIngredientStatus = () => {
    if (!summary) return null;

    return (
      <View style={styles.summaryContainer}>
        <View style={styles.summaryHeader}>
          <Text style={styles.summaryTitle}>Ingredient Summary</Text>
          <Text style={styles.summarySubtitle}>
            {summary.summary.pantry_items_updated} pantry items will be updated
          </Text>
        </View>

        {/* Available Ingredients */}
        {summary.consumed_ingredients.length > 0 && (
          <View style={styles.ingredientSection}>
            <View style={styles.sectionHeader}>
              <Ionicons name="checkmark-circle" size={20} color="#10B981" />
              <Text style={styles.sectionTitle}>
                Available ({summary.consumed_ingredients.length})
              </Text>
            </View>
            {summary.consumed_ingredients.map((ing, index) => (
              <View key={index} style={styles.ingredientItem}>
                <Text style={styles.ingredientName}>{ing.name}</Text>
                <Text style={styles.ingredientQuantity}>
                  {formatQuantity(ing.consumed)} {ing.unit}
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Partial Ingredients */}
        {summary.partial_ingredients.length > 0 && (
          <View style={styles.ingredientSection}>
            <View style={styles.sectionHeader}>
              <Ionicons name="warning" size={20} color="#F59E0B" />
              <Text style={[styles.sectionTitle, styles.warningText]}>
                Partial ({summary.partial_ingredients.length})
              </Text>
            </View>
            {summary.partial_ingredients.map((ing, index) => (
              <View key={index} style={styles.ingredientItem}>
                <Text style={styles.ingredientName}>{ing.name}</Text>
                <Text style={[styles.ingredientQuantity, styles.warningText]}>
                  Have {formatQuantity(ing.consumed)} of {formatQuantity(ing.required)} {ing.unit}
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Missing Ingredients */}
        {summary.missing_ingredients.length > 0 && (
          <View style={styles.ingredientSection}>
            <View style={styles.sectionHeader}>
              <Ionicons name="close-circle" size={20} color="#EF4444" />
              <Text style={[styles.sectionTitle, styles.errorText]}>
                Missing ({summary.missing_ingredients.length})
              </Text>
            </View>
            {summary.missing_ingredients.map((ing, index) => (
              <View key={index} style={styles.ingredientItem}>
                <Text style={styles.ingredientName}>{ing.name}</Text>
                <Text style={[styles.ingredientQuantity, styles.errorText]}>
                  Need {formatQuantity(ing.required)} {ing.unit}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.header}>
            <View>
              <Text style={styles.title}>Quick Complete Recipe</Text>
              <Text style={styles.recipeName}>{recipeName}</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color="#6B7280" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {loading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#6366F1" />
                <Text style={styles.loadingText}>Checking ingredients...</Text>
              </View>
            ) : (
              <>
                <View style={styles.infoBox}>
                  <Ionicons name="information-circle" size={20} color="#6366F1" />
                  <Text style={styles.infoText}>
                    Quick Complete will automatically consume available ingredients from your pantry
                    and exit the recipe immediately.
                  </Text>
                </View>

                {renderIngredientStatus()}
              </>
            )}
          </ScrollView>

          <View style={styles.footer}>
            <TouchableOpacity
              style={styles.cancelButton}
              onPress={onClose}
              disabled={confirming}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.confirmButton,
                (loading || confirming) && styles.confirmButtonDisabled,
              ]}
              onPress={handleQuickComplete}
              disabled={loading || confirming}
            >
              {confirming ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Ionicons name="flash" size={20} color="#fff" />
                  <Text style={styles.confirmButtonText}>Quick Complete</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '85%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  recipeName: {
    fontSize: 16,
    color: '#6B7280',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 16,
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#EEF2FF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#4C1D95',
    lineHeight: 20,
  },
  summaryContainer: {
    marginBottom: 20,
  },
  summaryHeader: {
    marginBottom: 16,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  summarySubtitle: {
    fontSize: 14,
    color: '#6B7280',
  },
  ingredientSection: {
    marginBottom: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  ingredientItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    marginBottom: 6,
  },
  ingredientName: {
    fontSize: 14,
    color: '#374151',
    flex: 1,
  },
  ingredientQuantity: {
    fontSize: 14,
    color: '#6B7280',
  },
  warningText: {
    color: '#F59E0B',
  },
  errorText: {
    color: '#EF4444',
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
