import React from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { formatAddedDate } from '../../utils/itemHelpers';

interface PantryItem {
  pantryItemId: number;
  pantryItemName: string;
  quantityAvailable: number;
  unit: string;
  expirationDate?: string;
  addedDate?: string;
  daysUntilExpiry?: number;
}

interface PantryItemSelectionModalProps {
  visible: boolean;
  ingredientName: string;
  requiredQuantity: number;
  requiredUnit: string;
  availableItems: PantryItem[];
  currentSelection?: PantryItem;
  onSelect: (item: PantryItem) => void;
  onClose: () => void;
}

export const PantryItemSelectionModal: React.FC<PantryItemSelectionModalProps> = ({
  visible,
  ingredientName,
  requiredQuantity,
  requiredUnit,
  availableItems,
  currentSelection,
  onSelect,
  onClose,
}) => {
  // Sort items by expiration date (closest first), then by timestamp (newest first)
  const sortedItems = [...availableItems].sort((a, b) => {
    const daysA = a.daysUntilExpiry ?? 999;
    const daysB = b.daysUntilExpiry ?? 999;
    
    if (daysA !== daysB) {
      return daysA - daysB;
    }
    
    // Secondary sort by added date (newest first)
    if (a.addedDate && b.addedDate) {
      return new Date(b.addedDate).getTime() - new Date(a.addedDate).getTime();
    }
    
    return 0;
  });

  const formatExpirationDate = (expirationDate?: string, daysUntilExpiry?: number) => {
    if (!expirationDate) return 'No expiry date';
    
    if (daysUntilExpiry !== undefined) {
      if (daysUntilExpiry < 0) return 'Expired';
      if (daysUntilExpiry === 0) return 'Expires today';
      if (daysUntilExpiry === 1) return 'Expires tomorrow';
      return `Expires in ${daysUntilExpiry} days`;
    }
    
    return `Expires ${new Date(expirationDate).toLocaleDateString()}`;
  };

  const getExpirationColor = (daysUntilExpiry?: number) => {
    if (daysUntilExpiry === undefined) return '#666';
    if (daysUntilExpiry < 0) return '#DC2626';
    if (daysUntilExpiry <= 3) return '#F59E0B';
    return '#059669';
  };

  const handleSelect = (item: PantryItem) => {
    onSelect(item);
    onClose();
  };

  return (
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
          <Text style={styles.title}>Select {ingredientName}</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Requirement Info */}
        <View style={styles.requirementInfo}>
          <Text style={styles.requirementText}>
            Recipe needs: {requiredQuantity} {requiredUnit}
          </Text>
        </View>

        {/* Items List */}
        <ScrollView style={styles.itemsList} showsVerticalScrollIndicator={false}>
          {sortedItems.map((item) => {
            const isSelected = currentSelection?.pantryItemId === item.pantryItemId;
            const expirationColor = getExpirationColor(item.daysUntilExpiry);
            
            return (
              <TouchableOpacity
                key={item.pantryItemId}
                style={[
                  styles.itemCard,
                  isSelected && styles.itemCardSelected,
                ]}
                onPress={() => handleSelect(item)}
                activeOpacity={0.7}
              >
                {/* Selection Indicator */}
                <View style={styles.itemContent}>
                  <View style={styles.selectionIndicator}>
                    <View style={[
                      styles.radioButton,
                      isSelected && styles.radioButtonSelected,
                    ]}>
                      {isSelected && (
                        <View style={styles.radioButtonInner} />
                      )}
                    </View>
                  </View>

                  {/* Item Info */}
                  <View style={styles.itemInfo}>
                    <Text style={styles.itemName}>{item.pantryItemName}</Text>
                    
                    <View style={styles.itemDetails}>
                      <Text style={styles.quantityText}>
                        {item.quantityAvailable} {item.unit} available
                      </Text>
                      
                      <Text style={[styles.expirationText, { color: expirationColor }]}>
                        {formatExpirationDate(item.expirationDate, item.daysUntilExpiry)}
                      </Text>
                      
                      {item.addedDate && (
                        <Text style={styles.addedText}>
                          Added: {formatAddedDate(item.addedDate)}
                        </Text>
                      )}
                    </View>
                  </View>

                  {/* Priority Badge */}
                  {item.daysUntilExpiry !== undefined && item.daysUntilExpiry <= 3 && (
                    <View style={styles.priorityBadge}>
                      <Ionicons name="warning" size={16} color="#F59E0B" />
                      <Text style={styles.priorityText}>Use soon</Text>
                    </View>
                  )}
                </View>
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
              styles.selectButton,
              !currentSelection && styles.selectButtonDisabled,
            ]}
            onPress={() => currentSelection && handleSelect(currentSelection)}
            activeOpacity={0.7}
            disabled={!currentSelection}
          >
            <Text style={[
              styles.selectButtonText,
              !currentSelection && styles.selectButtonTextDisabled,
            ]}>
              Use Selected
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </Modal>
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
  
  // Requirement Info
  requirementInfo: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#f8f9fa',
  },
  requirementText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  
  // Items List
  itemsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  itemCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginVertical: 6,
    borderWidth: 2,
    borderColor: '#f0f0f0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  itemCardSelected: {
    borderColor: '#6366F1',
    backgroundColor: '#f8f9ff',
  },
  itemContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  
  // Selection Indicator
  selectionIndicator: {
    marginRight: 12,
  },
  radioButton: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#ddd',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioButtonSelected: {
    borderColor: '#6366F1',
  },
  radioButtonInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#6366F1',
  },
  
  // Item Info
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  itemDetails: {
    gap: 2,
  },
  quantityText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  expirationText: {
    fontSize: 13,
    fontWeight: '500',
  },
  addedText: {
    fontSize: 12,
    color: '#999',
  },
  
  // Priority Badge
  priorityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    gap: 4,
  },
  priorityText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#F59E0B',
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
  selectButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#6366F1',
    alignItems: 'center',
  },
  selectButtonDisabled: {
    backgroundColor: '#ddd',
  },
  selectButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  selectButtonTextDisabled: {
    color: '#999',
  },
});