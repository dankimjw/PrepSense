import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TouchableWithoutFeedback,
  Platform,
  Alert,
  Animated,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Ionicons } from '@expo/vector-icons';
import { updatePantryItem } from '../../services/api';
import { useToast } from '../../hooks/useToast';

interface ExpirationDateModalProps {
  visible: boolean;
  item: any;
  onClose: () => void;
  onUpdate: (newDate: Date) => void;
}

export const ExpirationDateModal: React.FC<ExpirationDateModalProps> = ({
  visible,
  item,
  onClose,
  onUpdate,
}) => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(Platform.OS === 'ios');
  const [isUpdating, setIsUpdating] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    if (item?.expirationDate) {
      setSelectedDate(new Date(item.expirationDate));
    }
  }, [item]);

  const handleDateChange = (event: any, date?: Date) => {
    if (Platform.OS === 'android') {
      setShowDatePicker(false);
    }
    if (date) {
      setSelectedDate(date);
    }
  };

  const handleUpdate = async () => {
    if (!item) return;

    // Store original date for rollback
    const originalDate = item.expirationDate;
    
    // Optimistically update UI and close modal
    if (onUpdate) {
      onUpdate(selectedDate);
    }
    onClose();

    // Show sync indicator in console
    console.log('🔄 Updating expiration date for:', item.id, item.name);

    // Perform backend update asynchronously
    try {
      await updatePantryItem(item.id, {
        product_name: item.name,
        quantity: item.quantity_amount,
        unit_of_measurement: item.quantity_unit,
        expiration_date: selectedDate.toISOString().split('T')[0],
        category: item.category,
      });

      console.log('✅ Expiration date updated successfully:', item.id);
      showToast('Expiration date updated', 'success');
    } catch (error: any) {
      console.error('❌ Error updating expiration date:', error);
      
      // Rollback the optimistic update
      if (onUpdate && originalDate) {
        onUpdate(new Date(originalDate));
      }
      
      if (error.message?.includes('timeout')) {
        console.error('⏱️ Update timed out');
        showToast('Update timed out. Please try again.', 'error');
      } else {
        showToast('Failed to update expiration date', 'error');
      }
    }
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const calculateDaysUntilExpiry = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const expiry = new Date(date);
    expiry.setHours(0, 0, 0, 0);
    const days = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return days;
  };

  const daysUntilExpiry = calculateDaysUntilExpiry(selectedDate);
  const getExpiryStatus = () => {
    if (daysUntilExpiry < 0) return { text: 'Expired', color: '#DC2626' };
    if (daysUntilExpiry === 0) return { text: 'Expires today', color: '#DC2626' };
    if (daysUntilExpiry === 1) return { text: 'Expires tomorrow', color: '#D97706' };
    if (daysUntilExpiry <= 3) return { text: `Expires in ${daysUntilExpiry} days`, color: '#D97706' };
    if (daysUntilExpiry <= 7) return { text: `Expires in ${daysUntilExpiry} days`, color: '#059669' };
    return { text: `Expires in ${daysUntilExpiry} days`, color: '#297A56' };
  };

  const expiryStatus = getExpiryStatus();

  if (!item) return null;

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
            <View style={styles.modalContainer}>
              <View style={styles.handle} />
              
              <View style={styles.header}>
                <Text style={styles.title}>Update Expiration Date</Text>
                <TouchableOpacity onPress={onClose} style={styles.closeButton}>
                  <Ionicons name="close" size={24} color="#6B7280" />
                </TouchableOpacity>
              </View>

              <View style={styles.itemInfo}>
                <View style={[styles.itemIcon, { backgroundColor: item.color + '20' }]}>
                  <Ionicons name="cube-outline" size={24} color={item.color} />
                </View>
                <View style={styles.itemDetails}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemQuantity}>
                    {item.quantity_amount} {item.quantity_unit}
                  </Text>
                </View>
              </View>

              <View style={styles.dateSection}>
                <Text style={styles.sectionTitle}>Select New Date</Text>
                
                <TouchableOpacity 
                  style={styles.dateDisplay}
                  onPress={() => Platform.OS === 'android' && setShowDatePicker(true)}
                >
                  <Ionicons name="calendar-outline" size={20} color="#297A56" />
                  <Text style={styles.dateText}>{formatDate(selectedDate)}</Text>
                </TouchableOpacity>

                <View style={[styles.statusBadge, { backgroundColor: expiryStatus.color + '20' }]}>
                  <Text style={[styles.statusText, { color: expiryStatus.color }]}>
                    {expiryStatus.text}
                  </Text>
                </View>

                {(Platform.OS === 'ios' || showDatePicker) && (
                  <DateTimePicker
                    value={selectedDate}
                    mode="date"
                    display={Platform.OS === 'ios' ? 'spinner' : 'default'}
                    onChange={handleDateChange}
                    minimumDate={new Date()}
                    style={styles.datePicker}
                  />
                )}
              </View>

              <View style={styles.quickSelectSection}>
                <Text style={styles.sectionTitle}>Quick Select</Text>
                <View style={styles.quickSelectButtons}>
                  <TouchableOpacity
                    style={styles.quickSelectButton}
                    onPress={() => {
                      const date = new Date();
                      date.setDate(date.getDate() + 3);
                      setSelectedDate(date);
                    }}
                  >
                    <Text style={styles.quickSelectText}>+3 days</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.quickSelectButton}
                    onPress={() => {
                      const date = new Date();
                      date.setDate(date.getDate() + 7);
                      setSelectedDate(date);
                    }}
                  >
                    <Text style={styles.quickSelectText}>+1 week</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.quickSelectButton}
                    onPress={() => {
                      const date = new Date();
                      date.setDate(date.getDate() + 14);
                      setSelectedDate(date);
                    }}
                  >
                    <Text style={styles.quickSelectText}>+2 weeks</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.quickSelectButton}
                    onPress={() => {
                      const date = new Date();
                      date.setMonth(date.getMonth() + 1);
                      setSelectedDate(date);
                    }}
                  >
                    <Text style={styles.quickSelectText}>+1 month</Text>
                  </TouchableOpacity>
                </View>
              </View>

              <TouchableOpacity
                style={[styles.updateButton, isUpdating && styles.updateButtonDisabled]}
                onPress={handleUpdate}
                disabled={isUpdating}
              >
                <Text style={styles.updateButtonText}>
                  {isUpdating ? 'Updating...' : 'Update Expiration Date'}
                </Text>
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
  modalContainer: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 40,
    width: '100%',
    maxHeight: '90%',
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
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
  },
  closeButton: {
    padding: 8,
  },
  itemInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 24,
    paddingVertical: 12,
    backgroundColor: '#F9FAFB',
    marginHorizontal: 20,
    borderRadius: 12,
  },
  itemIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  itemDetails: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 2,
  },
  itemQuantity: {
    fontSize: 14,
    color: '#6B7280',
  },
  dateSection: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  dateDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  dateText: {
    fontSize: 16,
    color: '#111827',
    marginLeft: 12,
    fontWeight: '500',
  },
  statusBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginBottom: 16,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '600',
  },
  datePicker: {
    height: 180,
    marginTop: -10,
  },
  quickSelectSection: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  quickSelectButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  quickSelectButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  quickSelectText: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '500',
  },
  updateButton: {
    backgroundColor: '#297A56',
    marginHorizontal: 20,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  updateButtonDisabled: {
    opacity: 0.6,
  },
  updateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});