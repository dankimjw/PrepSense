import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
  Alert,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';
import { useItems } from '../../context/ItemsContext';
import { Config } from '../../config';
import Svg, { Circle, G } from 'react-native-svg';

const { width } = Dimensions.get('window');

interface ConsumptionModalProps {
  visible: boolean;
  item: any;
  onClose: () => void;
  onExpirationPress?: () => void;
}

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

export default function ConsumptionModal({ visible, item, onClose, onExpirationPress }: ConsumptionModalProps) {
  const [percentage, setPercentage] = useState(50);
  const [loading, setLoading] = useState(false);
  const { updateItem } = useItems();
  const animatedValue = React.useRef(new Animated.Value(50)).current;

  // For single unit items (quantity = 1), we still allow partial consumption
  const isSingleUnit = item?.quantity_amount === 1;
  const quickPercentages = [25, 50, 75, 100];

  React.useEffect(() => {
    // Reset to default percentage when item changes
    setPercentage(50);
  }, [item]);

  React.useEffect(() => {
    Animated.timing(animatedValue, {
      toValue: percentage,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [percentage]);

  const calculateConsumedAmount = () => {
    if (!item) return 0;
    return (item.quantity_amount * percentage) / 100;
  };

  const calculateRemainingAmount = () => {
    if (!item) return 0;
    return item.quantity_amount - calculateConsumedAmount();
  };

  const handleConfirm = async () => {
    try {
      setLoading(true);
      
      const consumedAmount = calculateConsumedAmount();
      const remainingAmount = calculateRemainingAmount();

      // Update the item in the database using the new consumption endpoint
      const response = await fetch(`${Config.API_BASE_URL}/pantry/items/${item.id}/consume`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quantity_amount: remainingAmount,
          used_quantity: (item.used_quantity || 0) + consumedAmount,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update item');
      }

      // Update local state
      updateItem(item.id, {
        ...item,
        quantity_amount: remainingAmount,
        used_quantity: (item.used_quantity || 0) + consumedAmount,
      });

      Alert.alert(
        'Success',
        `Consumed ${consumedAmount.toFixed(1)} ${item.quantity_unit} of ${item.name}`,
        [{ text: 'OK', onPress: onClose }]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to update item consumption');
      console.error('Consumption error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!item) return null;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <MaterialCommunityIcons name="close" size={24} color="#666" />
          </TouchableOpacity>

          <Text style={styles.title}>Consume Item</Text>
          <Text style={styles.itemName}>{item.name}</Text>
          
          <View style={styles.currentQuantity}>
            <Text style={styles.quantityLabel}>Current Quantity:</Text>
            <Text style={styles.quantityValue}>
              {item.quantity_amount} {item.quantity_unit}
            </Text>
          </View>

          {/* Expiration Date Section */}
          <TouchableOpacity 
            style={styles.expirationSection} 
            onPress={onExpirationPress}
            activeOpacity={0.7}
          >
            <View style={styles.expirationLeft}>
              <Text style={styles.expirationLabel}>Expires:</Text>
              <Text style={[
                styles.expirationValue,
                item.daysUntilExpiry <= 0 && styles.expiredText,
                item.daysUntilExpiry > 0 && item.daysUntilExpiry <= 3 && styles.expiringSoonText
              ]}>
                {item.expiry || 'No expiration date'}
              </Text>
            </View>
            <View style={styles.expirationRight}>
              <MaterialCommunityIcons 
                name="calendar-edit" 
                size={20} 
                color="#297A56" 
              />
              <Text style={styles.updateText}>Update</Text>
            </View>
          </TouchableOpacity>

          {isSingleUnit && (
            <Text style={styles.singleUnitNote}>
              This is a single unit item. Consuming will reduce the count.
            </Text>
          )}

          <View style={styles.gaugeContainer}>
            <View style={styles.gaugeWrapper}>
              <Svg width={200} height={200} viewBox="0 0 200 200">
                <G rotation={-90} origin="100, 100">
                  {/* Background circle */}
                  <Circle
                    cx="100"
                    cy="100"
                    r="80"
                    stroke="#E0E0E0"
                    strokeWidth="20"
                    fill="none"
                  />
                  {/* Progress circle */}
                  <Circle
                    cx="100"
                    cy="100"
                    r="80"
                    stroke={percentage > 75 ? "#E74C3C" : percentage > 50 ? "#F39C12" : "#297A56"}
                    strokeWidth="20"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 80}`}
                    strokeDashoffset={`${2 * Math.PI * 80 * (1 - percentage / 100)}`}
                    strokeLinecap="round"
                  />
                </G>
              </Svg>
              <View style={styles.gaugeCenter}>
                <Text style={styles.percentageText}>{percentage}%</Text>
                <Text style={styles.consumingText}>Consuming</Text>
              </View>
            </View>
            
            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={100}
              value={percentage}
              onValueChange={setPercentage}
              step={5}
              minimumTrackTintColor="transparent"
              maximumTrackTintColor="transparent"
              thumbTintColor="#297A56"
            />
          </View>

          <View style={styles.quickButtons}>
            {quickPercentages.map((percent) => (
              <TouchableOpacity
                key={percent}
                style={[
                  styles.quickButton,
                  percentage === percent && styles.quickButtonActive,
                ]}
                onPress={() => setPercentage(percent)}
              >
                <Text
                  style={[
                    styles.quickButtonText,
                    percentage === percent && styles.quickButtonTextActive,
                  ]}
                >
                  {percent}%
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.consumptionInfo}>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Consuming:</Text>
              <Text style={styles.infoValueConsuming}>
                {isSingleUnit 
                  ? `${percentage}% of item`
                  : `${calculateConsumedAmount().toFixed(1)} ${item.quantity_unit}`
                }
              </Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Remaining:</Text>
              <Text style={styles.infoValueRemaining}>
                {isSingleUnit
                  ? `${calculateRemainingAmount() > 0 ? 'Partial item' : 'None'}`
                  : `${calculateRemainingAmount().toFixed(1)} ${item.quantity_unit}`
                }
              </Text>
            </View>
          </View>

          <TouchableOpacity
            style={styles.confirmButton}
            onPress={handleConfirm}
            disabled={loading || percentage === 0}
          >
            <LinearGradient
              colors={['#297A56', '#1E5A40']}
              style={styles.gradientButton}
            >
              {loading ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text style={styles.confirmButtonText}>Confirm Consumption</Text>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 20,
    width: width * 0.9,
    maxWidth: 400,
    alignItems: 'center',
  },
  closeButton: {
    position: 'absolute',
    top: 15,
    right: 15,
    zIndex: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#297A56',
    marginBottom: 10,
  },
  itemName: {
    fontSize: 18,
    color: '#333',
    marginBottom: 20,
  },
  currentQuantity: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  quantityLabel: {
    fontSize: 16,
    color: '#666',
    marginRight: 10,
  },
  quantityValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  expirationSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E9ECEF',
  },
  expirationLeft: {
    flex: 1,
  },
  expirationLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  expirationValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  expiredText: {
    color: '#DC2626',
  },
  expiringSoonText: {
    color: '#D97706',
  },
  expirationRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  updateText: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '500',
  },
  singleUnitNote: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
    marginBottom: -10,
    fontStyle: 'italic',
  },
  gaugeContainer: {
    width: '100%',
    alignItems: 'center',
    marginBottom: 20,
  },
  gaugeWrapper: {
    width: 200,
    height: 200,
    position: 'relative',
    marginBottom: 20,
  },
  gaugeCenter: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  percentageText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#297A56',
  },
  consumingText: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  quickButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 30,
  },
  quickButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: '#297A56',
    backgroundColor: 'white',
  },
  quickButtonActive: {
    backgroundColor: '#297A56',
  },
  quickButtonText: {
    color: '#297A56',
    fontWeight: '600',
  },
  quickButtonTextActive: {
    color: 'white',
  },
  consumptionInfo: {
    width: '100%',
    backgroundColor: '#F5F5F5',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  infoLabel: {
    fontSize: 16,
    color: '#666',
  },
  infoValueConsuming: {
    fontSize: 16,
    fontWeight: '600',
    color: '#E74C3C',
  },
  infoValueRemaining: {
    fontSize: 16,
    fontWeight: '600',
    color: '#297A56',
  },
  confirmButton: {
    width: '100%',
    marginTop: 10,
  },
  gradientButton: {
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  confirmButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
});