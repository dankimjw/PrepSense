// components/modals/PantryConsumptionSuccessModal.tsx
import React from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { formatQuantity } from '../../utils/numberFormatting';

const { width } = Dimensions.get('window');

interface ConsumptionItem {
  ingredientName: string;
  pantryItemName: string;
  beforeQuantity: number;
  afterQuantity: number;
  consumedQuantity: number;
  unit: string;
  status: 'consumed' | 'partial' | 'depleted' | 'insufficient';
}

interface ConsumptionSummary {
  recipeName: string;
  servingsCooked: number;
  consumedItems: ConsumptionItem[];
  warnings: string[];
  errors: string[];
  totalIngredients: number;
  successfullyConsumed: number;
  partiallyConsumed: number;
  insufficientItems: number;
}

interface PantryConsumptionSuccessModalProps {
  visible: boolean;
  onClose: () => void;
  summary: ConsumptionSummary | null;
}

export const PantryConsumptionSuccessModal: React.FC<PantryConsumptionSuccessModalProps> = ({
  visible,
  onClose,
  summary,
}) => {
  if (!summary) return null;

  // Always show success
  const overallStatus = { icon: 'checkmark-circle', color: '#10B981', text: 'SUCCESS' };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <SafeAreaView style={styles.container}>
          <View style={styles.modal}>
            {/* Header */}
            <View style={styles.header}>
              <View style={styles.headerContent}>
                <Ionicons 
                  name={overallStatus.icon as any} 
                  size={32} 
                  color={overallStatus.color} 
                />
                <View style={styles.headerText}>
                  <Text style={styles.title}>SUCCESS</Text>
                  <Text style={styles.subtitle}>Recipe Completed!</Text>
                </View>
              </View>
              <TouchableOpacity onPress={onClose} style={styles.closeButton}>
                <Ionicons name="close" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>

            {/* Recipe Info */}
            <View style={styles.recipeInfo}>
              <Text style={styles.recipeName}>{summary.recipeName}</Text>
              <Text style={styles.servingsText}>
                {summary.servingsCooked} {summary.servingsCooked === 1 ? 'serving' : 'servings'} cooked
              </Text>
            </View>

            {/* Removed Summary Stats - just show success */}

            {/* Consumption Details */}
            <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
              <Text style={styles.sectionTitle}>Ingredients Updated</Text>
              
              {summary.consumedItems.map((item, index) => (
                <View key={index} style={styles.consumptionItem}>
                  <View style={styles.itemHeader}>
                    <View style={styles.itemHeaderLeft}>
                      <Ionicons 
                        name="checkmark-circle" 
                        size={20} 
                        color="#10B981" 
                      />
                      <Text style={styles.ingredientName}>{item.ingredientName}</Text>
                    </View>
                  </View>
                  
                  <View style={styles.itemDetails}>
                    <Text style={styles.pantryItemName}>{item.pantryItemName}</Text>
                    <View style={styles.quantityChange}>
                      <View style={styles.quantityBox}>
                        <Text style={styles.quantityLabel}>Before</Text>
                        <Text style={styles.quantityValue}>
                          {formatQuantity(item.beforeQuantity)} {item.unit}
                        </Text>
                      </View>
                      
                      <View style={styles.arrow}>
                        <Ionicons name="arrow-forward" size={16} color="#9CA3AF" />
                      </View>
                      
                      <View style={styles.quantityBox}>
                        <Text style={styles.quantityLabel}>After</Text>
                        <Text style={[
                          styles.quantityValue,
                          item.afterQuantity === 0 && styles.depletedText
                        ]}>
                          {item.afterQuantity === 0 ? 'Empty' : `${formatQuantity(item.afterQuantity)} ${item.unit}`}
                        </Text>
                      </View>

                    </View>
                  </View>
                </View>
              ))}

              {/* Removed warnings, errors and tips sections for cleaner UI */}
            </ScrollView>

            {/* Footer */}
            <View style={styles.footer}>
              <TouchableOpacity 
                style={styles.doneButton}
                onPress={onClose}
              >
                <Text style={styles.doneButtonText}>Done</Text>
              </TouchableOpacity>
            </View>
          </View>
        </SafeAreaView>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  modal: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: -2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
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
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  headerText: {
    marginLeft: 12,
    flex: 1,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  closeButton: {
    padding: 4,
  },
  recipeInfo: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#F9FAFB',
  },
  recipeName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  servingsText: {
    fontSize: 14,
    color: '#6B7280',
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 8,
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginTop: 20,
    marginBottom: 12,
  },
  consumptionItem: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  itemHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  ingredientName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
  },
  itemDetails: {
    marginLeft: 28,
  },
  pantryItemName: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  quantityChange: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  quantityBox: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 8,
    minWidth: 70,
    alignItems: 'center',
  },
  consumedBox: {
    backgroundColor: '#FEF3C7',
    marginLeft: 8,
  },
  quantityLabel: {
    fontSize: 10,
    color: '#6B7280',
    marginBottom: 2,
  },
  quantityValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  consumedValue: {
    color: '#92400E',
  },
  depletedText: {
    color: '#EF4444',
  },
  arrow: {
    paddingHorizontal: 4,
  },
  alertSection: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    marginBottom: 12,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  alertTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#92400E',
    marginLeft: 8,
  },
  warningText: {
    fontSize: 13,
    color: '#92400E',
    marginLeft: 28,
    marginBottom: 4,
  },
  errorText: {
    fontSize: 13,
    color: '#991B1B',
    marginLeft: 28,
    marginBottom: 4,
  },
  tipsSection: {
    backgroundColor: '#EEF2FF',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    marginBottom: 20,
  },
  tipsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  tipsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4338CA',
    marginLeft: 8,
  },
  tipText: {
    fontSize: 13,
    color: '#4338CA',
    marginLeft: 28,
    marginBottom: 4,
  },
  footer: {
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  doneButton: {
    backgroundColor: '#297A56',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  doneButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
