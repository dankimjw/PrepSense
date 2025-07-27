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
import { MaterialCommunityIcons, Feather } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';
import { useItems } from '../../context/ItemsContext';
import { Config } from '../../config';
import { apiClient, ApiError } from '../../services/apiClient';
import Svg, { Circle, G, Defs, LinearGradient as SvgLinearGradient, Stop } from 'react-native-svg';
import { shouldAllowDecimals, getQuantityRules } from '../../constants/quantityRules';

const { width } = Dimensions.get('window');

interface ConsumptionModalProps {
  visible: boolean;
  item: any;
  onClose: () => void;
  onExpirationPress?: () => void;
  onEditPress?: () => void;
}

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

export default function ConsumptionModal({ visible, item, onClose, onExpirationPress, onEditPress }: ConsumptionModalProps) {
  const [percentage, setPercentage] = useState(50);
  const [loading, setLoading] = useState(false);
  const { updateItem } = useItems();
  const animatedValue = React.useRef(new Animated.Value(50)).current;

  // Check if unit requires whole numbers only
  const allowDecimals = item ? shouldAllowDecimals(item.name || '', item.quantity_unit || '') : true;
  const quantityRules = item ? getQuantityRules(item.name || '', item.quantity_unit || '') : { allowDecimals: true, step: 1 };
  
  // Debug logging to help identify issues
  if (item && __DEV__) {
    console.log(`ConsumptionModal Debug - Item: "${item.name}", Unit: "${item.quantity_unit}", AllowDecimals: ${allowDecimals}`);
  }
  
  // Helper function to detect liquid items with wrong database units
  const isLiquidWithWrongUnit = (itemName: string) => {
    const lowerName = itemName.toLowerCase();
    return lowerName.includes('oil') || 
           lowerName.includes('sauce') ||
           lowerName.includes('vinegar') ||
           lowerName.includes('milk') ||
           lowerName.includes('juice') ||
           lowerName.includes('honey') ||
           lowerName.includes('syrup') ||
           lowerName.includes('broth') ||
           lowerName.includes('stock') ||
           lowerName.includes('extract') ||
           lowerName.includes('wine') ||
           lowerName.includes('beer');
  };

  // For discrete units (like "bunches", "each"), we need different percentage options
  const isSingleUnit = item?.quantity_amount === 1;
  const isDiscreteUnit = !allowDecimals;
  
  // Create consistent quick percentages for all items
  const quickPercentages = (() => {
    // Always show standard percentages for continuous items (liquids, powders, etc.)
    if (!isDiscreteUnit) {
      return [25, 50, 75, 100];
    }
    
    // For discrete units, create smart percentages based on quantity
    const totalQty = item?.quantity_amount || 1;
    
    // Special case: if quantity is 1 but it's likely a liquid in wrong unit (like olive oil "ea")
    // Force standard percentages to avoid bare modal
    if (totalQty === 1 && item?.item_name && isLiquidWithWrongUnit(item.item_name)) {
      return [25, 50, 75, 100]; // Force standard percentages for likely liquids
    }
    
    if (totalQty <= 4) {
      // For small discrete quantities, show percentages for each whole unit
      const percentages = [];
      for (let i = 1; i <= totalQty; i++) {
        percentages.push(Math.round((i / totalQty) * 100));
      }
      return percentages;
    } else {
      // For larger discrete quantities, use standard fractions
      return [25, 50, 75, 100];
    }
  })();

  React.useEffect(() => {
    // Reset to default percentage when item changes or modal opens
    if (visible && item) {
      setPercentage(50);
    }
  }, [item, visible]);

  React.useEffect(() => {
    Animated.timing(animatedValue, {
      toValue: percentage,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [percentage]);

  const calculateConsumedAmount = () => {
    if (!item) return 0;
    
    const rawAmount = (item.quantity_amount * percentage) / 100;
    
    // For discrete units, ensure consumed amount is a whole number
    if (isDiscreteUnit) {
      // Use smooth rounding with buffer zones for better UX
      const rounded = Math.round(rawAmount);
      return Math.max(1, Math.min(item.quantity_amount, rounded));
    }
    
    return rawAmount;
  };

  const calculateRemainingAmount = () => {
    if (!item) return 0;
    
    const consumedAmount = calculateConsumedAmount();
    const remaining = item.quantity_amount - consumedAmount;
    
    // For discrete units, ensure remaining is a whole number (or 0)
    if (isDiscreteUnit) {
      return Math.max(0, Math.floor(remaining));
    }
    
    return Math.max(0, remaining);
  };

  const handleConfirm = async () => {
    try {
      setLoading(true);
      
      const consumedAmount = calculateConsumedAmount();
      const remainingAmount = calculateRemainingAmount();

      // Update the item in the database using the new consumption endpoint
      await apiClient.patch(`/pantry/items/${item.id}/consume`, {
        quantity_amount: remainingAmount,
        used_quantity: (item.used_quantity || 0) + consumedAmount,
      }, 5000); // 5 second timeout

      // Update local state
      updateItem(item.id, {
        ...item,
        quantity_amount: remainingAmount,
        used_quantity: (item.used_quantity || 0) + consumedAmount,
      });

      Alert.alert(
        'Success',
        `Consumed ${consumedAmount.toFixed(1)} ${item.quantity_unit} of ${item.name}`,
        [{ text: 'OK', onPress: () => {
          setPercentage(50); // Reset to default
          onClose();
        }}]
      );
    } catch (error: any) {
      console.error('Consumption error:', error);
      if (error instanceof ApiError && error.isTimeout) {
        Alert.alert('Timeout', 'Consumption update is taking too long. Please check your connection and try again.');
      } else {
        Alert.alert('Error', 'Failed to update item consumption');
      }
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
          <View style={styles.headerButtons}>
            {onEditPress && (
              <TouchableOpacity style={styles.editButton} onPress={onEditPress}>
                <Feather name="edit-2" size={20} color="#297A56" />
              </TouchableOpacity>
            )}
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <MaterialCommunityIcons name="close" size={24} color="#666" />
            </TouchableOpacity>
          </View>

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
            onPress={() => {
              if (onExpirationPress) {
                onExpirationPress();
              }
            }}
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
              <Svg width={220} height={220} viewBox="0 0 220 220">
                <Defs>
                  {/* Modern gradient definitions */}
                  <SvgLinearGradient id="lowGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <Stop offset="0%" stopColor="#10B981" stopOpacity="1" />
                    <Stop offset="100%" stopColor="#059669" stopOpacity="1" />
                  </SvgLinearGradient>
                  <SvgLinearGradient id="mediumGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <Stop offset="0%" stopColor="#F59E0B" stopOpacity="1" />
                    <Stop offset="100%" stopColor="#D97706" stopOpacity="1" />
                  </SvgLinearGradient>
                  <SvgLinearGradient id="highGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <Stop offset="0%" stopColor="#EF4444" stopOpacity="1" />
                    <Stop offset="100%" stopColor="#DC2626" stopOpacity="1" />
                  </SvgLinearGradient>
                  <SvgLinearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <Stop offset="0%" stopColor="#F1F5F9" stopOpacity="1" />
                    <Stop offset="100%" stopColor="#E2E8F0" stopOpacity="1" />
                  </SvgLinearGradient>
                </Defs>
                <G rotation={-90} origin="110, 110">
                  {/* Background circle with gradient */}
                  <Circle
                    cx="110"
                    cy="110"
                    r="85"
                    stroke="url(#backgroundGradient)"
                    strokeWidth="16"
                    fill="none"
                  />
                  {/* Progress circle with dynamic gradient */}
                  <Circle
                    cx="110"
                    cy="110"
                    r="85"
                    stroke={
                      percentage > 75 
                        ? "url(#highGradient)" 
                        : percentage > 50 
                        ? "url(#mediumGradient)" 
                        : "url(#lowGradient)"
                    }
                    strokeWidth="16"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 85}`}
                    strokeDashoffset={`${2 * Math.PI * 85 * (1 - percentage / 100)}`}
                    strokeLinecap="round"
                    opacity="0.9"
                  />
                </G>
              </Svg>
              <View style={styles.gaugeCenter}>
                <Text style={[
                  styles.percentageText,
                  percentage > 75 ? styles.highPercentage : 
                  percentage > 50 ? styles.mediumPercentage : 
                  styles.lowPercentage
                ]}>{percentage}%</Text>
                <Text style={styles.consumingText}>Consuming</Text>
              </View>
            </View>
            
            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={100}
              value={percentage}
              onValueChange={(value) => {
                if (isDiscreteUnit) {
                  // Check if this is a liquid item with wrong database unit
                  const isLiquidItemWithWrongUnit = item?.name && isLiquidWithWrongUnit(item.name);
                  
                  if (isLiquidItemWithWrongUnit) {
                    // Treat as continuous liquid for smooth slider experience
                    setPercentage(value);
                  } else {
                    // Create smooth buffer zones around discrete values
                    const discreteValues = [];
                    for (let i = 1; i <= item.quantity_amount; i++) {
                      discreteValues.push((i / item.quantity_amount) * 100);
                    }
                    
                    // Find closest discrete value with tolerance buffer
                    let closestValue = value;
                    let minDistance = Infinity;
                    
                    for (const discreteValue of discreteValues) {
                      const distance = Math.abs(value - discreteValue);
                      // Use a tolerance buffer of ±5% for smoother feeling
                      if (distance < minDistance && distance <= 5) {
                        minDistance = distance;
                        closestValue = discreteValue;
                      }
                    }
                    
                    // If we're not close to any discrete value, allow free movement
                    // but still constrain to valid range
                    if (minDistance > 5) {
                      closestValue = value;
                    }
                    
                    setPercentage(Math.min(100, Math.max(0, closestValue)));
                  }
                } else {
                  setPercentage(value);
                }
              }}
              step={isDiscreteUnit ? 1 : 5}
              minimumTrackTintColor={
                percentage > 75 ? "#EF4444" : 
                percentage > 50 ? "#F59E0B" : 
                "#10B981"
              }
              maximumTrackTintColor="#E2E8F0"
              thumbTintColor={
                percentage > 75 ? "#DC2626" : 
                percentage > 50 ? "#D97706" : 
                "#059669"
              }
            />
          </View>

          <View style={styles.quickButtons}>
            {quickPercentages.map((percent) => {
              // For discrete units with small quantities, show the actual unit count
              const showUnitCount = isDiscreteUnit && item && item.quantity_amount <= 4;
              const unitCount = showUnitCount ? Math.round((percent / 100) * item.quantity_amount) : null;
              
              return (
                <TouchableOpacity
                  key={percent}
                  style={[
                    styles.quickButton,
                    percentage === percent && styles.quickButtonActive,
                    showUnitCount && styles.quickButtonWithUnit,
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
                  {showUnitCount && (
                    <Text
                      style={[
                        styles.quickButtonUnit,
                        percentage === percent && styles.quickButtonUnitActive,
                      ]}
                    >
                      ({unitCount} {item.quantity_unit})
                    </Text>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>

          <View style={styles.consumptionInfo}>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Consuming:</Text>
              <Text style={styles.infoValueConsuming}>
                {isDiscreteUnit 
                  ? `${calculateConsumedAmount()} ${item.quantity_unit}`
                  : `${calculateConsumedAmount().toFixed(1)} ${item.quantity_unit}`
                }
              </Text>
            </View>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Remaining:</Text>
              <Text style={styles.infoValueRemaining}>
                {isDiscreteUnit
                  ? `${calculateRemainingAmount()} ${item.quantity_unit}`
                  : `${calculateRemainingAmount().toFixed(1)} ${item.quantity_unit}`
                }
              </Text>
            </View>
            {isDiscreteUnit && (
              <Text style={styles.discreteUnitNote}>
                {item?.name && isLiquidWithWrongUnit(item.name)
                  ? '🧪 Liquid mode: Continuous consumption (database unit will be updated)'
                  : `📏 Smart mode: Slider snaps to whole ${item.quantity_unit} with smooth buffer zones`
                }
              </Text>
            )}
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
  headerButtons: {
    position: 'absolute',
    top: 15,
    right: 15,
    flexDirection: 'row',
    gap: 12,
    zIndex: 1,
  },
  editButton: {
    padding: 4,
  },
  closeButton: {
    padding: 4,
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
    width: 220,
    height: 220,
    position: 'relative',
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
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
    color: '#1F2937',
  },
  lowPercentage: {
    color: '#059669',
  },
  mediumPercentage: {
    color: '#D97706',
  },
  highPercentage: {
    color: '#DC2626',
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
    borderColor: '#E2E8F0',
    backgroundColor: '#F8FAFC',
  },
  quickButtonActive: {
    backgroundColor: '#10B981',
    borderColor: '#059669',
  },
  quickButtonText: {
    color: '#64748B',
    fontWeight: '600',
  },
  quickButtonTextActive: {
    color: 'white',
  },
  quickButtonWithUnit: {
    paddingVertical: 8,
    minHeight: 50,
  },
  quickButtonUnit: {
    fontSize: 10,
    color: '#94A3B8',
    marginTop: 2,
  },
  quickButtonUnitActive: {
    color: 'rgba(255, 255, 255, 0.8)',
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
    color: '#DC2626',
  },
  infoValueRemaining: {
    fontSize: 16,
    fontWeight: '600',
    color: '#059669',
  },
  discreteUnitNote: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 8,
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