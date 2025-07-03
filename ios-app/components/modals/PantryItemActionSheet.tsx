import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TouchableWithoutFeedback,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { PantryItemData } from '../home/PantryItem';

interface PantryItemActionSheetProps {
  visible: boolean;
  item: PantryItemData | null;
  onClose: () => void;
  onUpdateExpiration: () => void;
  onEditItem: () => void;
  onConsumeItem: () => void;
  onDeleteItem: () => void;
}

export const PantryItemActionSheet: React.FC<PantryItemActionSheetProps> = ({
  visible,
  item,
  onClose,
  onUpdateExpiration,
  onEditItem,
  onConsumeItem,
  onDeleteItem,
}) => {
  if (!item) return null;

  const actions = [
    {
      icon: 'calendar-outline',
      label: 'Update Expiration Date',
      onPress: onUpdateExpiration,
      color: '#297A56',
    },
    {
      icon: 'create-outline',
      label: 'Edit Item Details',
      onPress: onEditItem,
      color: '#3B82F6',
    },
    {
      icon: 'restaurant-outline',
      label: 'Mark as Consumed',
      onPress: onConsumeItem,
      color: '#F59E0B',
    },
    {
      icon: 'trash-outline',
      label: 'Delete Item',
      onPress: onDeleteItem,
      color: '#DC2626',
    },
  ];

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.overlay}>
          <TouchableWithoutFeedback>
            <View style={styles.container}>
              <View style={styles.handle} />
              
              <View style={styles.header}>
                <View style={[styles.itemIcon, { backgroundColor: item.color + '20' }]}>
                  <Ionicons name="cube-outline" size={24} color={item.color} />
                </View>
                <View style={styles.itemInfo}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemQuantity}>
                    {item.quantity_amount} {item.quantity_unit}
                  </Text>
                </View>
              </View>

              <View style={styles.actions}>
                {actions.map((action, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.actionButton}
                    onPress={() => {
                      action.onPress();
                      onClose();
                    }}
                  >
                    <View style={[styles.actionIcon, { backgroundColor: action.color + '15' }]}>
                      <Ionicons name={action.icon as any} size={20} color={action.color} />
                    </View>
                    <Text style={[styles.actionLabel, { color: '#111827' }]}>
                      {action.label}
                    </Text>
                    <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity style={styles.cancelButton} onPress={onClose}>
                <Text style={styles.cancelText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
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
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 40,
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  itemIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 2,
  },
  itemQuantity: {
    fontSize: 14,
    color: '#6B7280',
  },
  actions: {
    paddingTop: 8,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 20,
  },
  actionIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  actionLabel: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
  },
  cancelButton: {
    marginTop: 8,
    marginHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    alignItems: 'center',
  },
  cancelText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
});