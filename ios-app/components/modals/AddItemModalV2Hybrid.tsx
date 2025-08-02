import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Portal, Dialog, Button, IconButton } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { savePantryItem } from '../../services/api';
import { formatQuantity } from '../../utils/numberFormatting';
import { FOOD_CATEGORIES, getIngredientIcon, capitalizeIngredientName } from '../../utils/ingredientIcons';
import { formatQuantityInput, validateQuantity, shouldAllowDecimals } from '../../constants/quantityRules';
import { validateUnit, getUnitSuggestions, shouldSuggestUnitChange } from '../../services/unitValidationService';
import { HybridTextInput } from '../hybrid/HybridTextInput';
import { SuccessAnimation, useLottieAnimation } from '../hybrid/HybridLottie';
import { debugLog, debugBorder } from '../debug/DebugPanel';

// Unit rules for each food category
const CATEGORY_UNIT_RULES = {
  produce: {
    allowedTypes: ['count', 'mass'],
    defaultType: 'count',
    units: {
      count: [
        { id: 'ea', label: 'each', isDefault: true },
        { id: 'bunch', label: 'bunch' },
        { id: 'head', label: 'head' },
        { id: 'dozen', label: 'dozen' },
      ],
      mass: [
        { id: 'g', label: 'grams', isDefault: true },
        { id: 'kg', label: 'kilograms' },
        { id: 'oz', label: 'ounces' },
        { id: 'lb', label: 'pounds' },
      ],
    },
  },
  dairy: {
    allowedTypes: ['volume', 'mass', 'count'],
    defaultType: 'volume',
    units: {
      volume: [
        { id: 'ml', label: 'millilitres', isDefault: true },
        { id: 'l', label: 'litres' },
        { id: 'cup', label: 'cups' },
        { id: 'floz', label: 'fluid ounces' },
      ],
      mass: [
        { id: 'g', label: 'grams', isDefault: true },
        { id: 'kg', label: 'kilograms' },
        { id: 'oz', label: 'ounces' },
        { id: 'lb', label: 'pounds' },
      ],
      count: [
        { id: 'ea', label: 'each', isDefault: true },
        { id: 'dozen', label: 'dozen' },
      ],
    },
  },
  meat: {
    allowedTypes: ['mass'],
    defaultType: 'mass',
    units: {
      mass: [
        { id: 'g', label: 'grams', isDefault: true },
        { id: 'kg', label: 'kilograms' },
        { id: 'oz', label: 'ounces' },
        { id: 'lb', label: 'pounds' },
      ],
    },
  },
  beverages: {
    allowedTypes: ['volume', 'count'],
    defaultType: 'volume',
    units: {
      volume: [
        { id: 'ml', label: 'millilitres', isDefault: true },
        { id: 'l', label: 'litres' },
        { id: 'cup', label: 'cups' },
        { id: 'floz', label: 'fluid ounces' },
        { id: 'gal', label: 'gallons' },
      ],
      count: [
        { id: 'bottle', label: 'bottles' },
        { id: 'can', label: 'cans' },
        { id: 'ea', label: 'each' },
      ],
    },
  },
  // Add more categories...
  other: {
    allowedTypes: ['count', 'mass', 'volume'],
    defaultType: 'count',
    units: {
      count: [{ id: 'ea', label: 'each', isDefault: true }],
      mass: [{ id: 'g', label: 'grams', isDefault: true }],
      volume: [{ id: 'ml', label: 'millilitres', isDefault: true }],
    },
  },
};

interface AddItemModalV2HybridProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddItemModalV2Hybrid: React.FC<AddItemModalV2HybridProps> = ({
  visible,
  onClose,
  onSuccess,
}) => {
  // Step tracking
  const [currentStep, setCurrentStep] = useState(1);
  
  // Form data
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [itemName, setItemName] = useState('');
  const [quantity, setQuantity] = useState('');
  const [selectedUnitType, setSelectedUnitType] = useState<string | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);
  const [expirationDate, setExpirationDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [notes, setNotes] = useState('');
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [unitPreview, setUnitPreview] = useState('');
  const [unitValidationResult, setUnitValidationResult] = useState<any>(null);
  const [isValidatingUnit, setIsValidatingUnit] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  
  // Lottie animation hook
  const successAnimation = useLottieAnimation(false);

  // Form validation state
  const [nameError, setNameError] = useState('');
  const [quantityError, setQuantityError] = useState('');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (!visible) {
      setCurrentStep(1);
      setSelectedCategory(null);
      setItemName('');
      setQuantity('');
      setSelectedUnitType(null);
      setSelectedUnit(null);
      setExpirationDate(new Date());
      setNotes('');
      setNameError('');
      setQuantityError('');
    }
  }, [visible]);

  // Debug logging
  useEffect(() => {
    debugLog('AddItemModalV2Hybrid', `Step ${currentStep}, Category: ${selectedCategory}`, {
      itemName,
      quantity,
      selectedUnit,
    });
  }, [currentStep, selectedCategory, itemName, quantity, selectedUnit]);

  // Update unit preview
  useEffect(() => {
    if (quantity && selectedUnit) {
      const unitLabel = getUnitLabel(selectedUnit);
      setUnitPreview(`${formatQuantity(quantity)} ${unitLabel}`);
    } else {
      setUnitPreview('');
    }
  }, [quantity, selectedUnit]);

  // Validate unit when item name or unit changes
  useEffect(() => {
    const validateCurrentUnit = async () => {
      if (itemName && selectedUnit) {
        setIsValidatingUnit(true);
        try {
          const validation = await validateUnit(itemName, selectedUnit, parseFloat(quantity) || undefined);
          setUnitValidationResult(validation);
          
          // Show warning if unit is not appropriate
          if (shouldSuggestUnitChange(validation)) {
            // Don't auto-change, just show the suggestion
            console.log(`Unit validation: ${validation.reason}`);
          }
        } catch (error) {
          console.error('Unit validation failed:', error);
          setUnitValidationResult(null);
        } finally {
          setIsValidatingUnit(false);
        }
      } else {
        setUnitValidationResult(null);
      }
    };

    const debounceTimer = setTimeout(validateCurrentUnit, 500);
    return () => clearTimeout(debounceTimer);
  }, [itemName, selectedUnit, quantity]);

  const getUnitLabel = (unitId: string) => {
    if (!selectedCategory || !selectedUnitType) return unitId;
    
    const rules = CATEGORY_UNIT_RULES[selectedCategory] || CATEGORY_UNIT_RULES.other;
    const units = rules.units[selectedUnitType] || [];
    const unit = units.find(u => u.id === unitId);
    return unit?.label || unitId;
  };

  const handleCategorySelect = (categoryId: string) => {
    setSelectedCategory(categoryId);
    
    // Auto-select default unit type for this category
    const rules = CATEGORY_UNIT_RULES[categoryId] || CATEGORY_UNIT_RULES.other;
    setSelectedUnitType(rules.defaultType);
    
    // Auto-select default unit
    const defaultUnits = rules.units[rules.defaultType] || [];
    const defaultUnit = defaultUnits.find(u => u.isDefault);
    if (defaultUnit) {
      setSelectedUnit(defaultUnit.id);
    }
    
    setCurrentStep(2);
  };

  const validateForm = () => {
    let isValid = true;
    
    // Validate item name
    if (!itemName.trim()) {
      setNameError('Item name is required');
      isValid = false;
    } else {
      setNameError('');
    }
    
    // Validate quantity
    if (!quantity.trim()) {
      setQuantityError('Quantity is required');
      isValid = false;
    } else {
      const quantityValue = parseFloat(quantity);
      const validation = validateQuantity(quantityValue, itemName, selectedUnit || '');
      
      if (!validation.isValid) {
        setQuantityError(validation.error || 'Please enter a valid quantity');
        isValid = false;
      } else {
        setQuantityError('');
      }
    }
    
    return isValid;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    if (!selectedUnit || !selectedCategory) {
      Alert.alert('Missing Information', 'Please fill in all required fields.');
      return;
    }

    // Check unit validation result
    if (unitValidationResult && unitValidationResult.severity === 'error') {
      Alert.alert(
        'Unit Warning',
        `${unitValidationResult.reason}\n\nWould you like to use "${unitValidationResult.suggested_unit}" instead?`,
        [
          {
            text: 'Keep Current',
            style: 'cancel',
          },
          {
            text: `Use ${unitValidationResult.suggested_unit}`,
            onPress: () => {
              setSelectedUnit(unitValidationResult.suggested_unit);
              // Don't submit yet, let user review the change
            },
          },
        ]
      );
      return;
    }

    setIsLoading(true);

    try {
      const categoryInfo = FOOD_CATEGORIES.find(c => c.id === selectedCategory);
      
      await savePantryItem(111, { // TODO: Get actual user ID
        item_name: itemName,
        quantity_amount: parseFloat(quantity),
        quantity_unit: selectedUnit,
        expected_expiration: expirationDate.toISOString(),
        category: categoryInfo?.label || 'Other',
      });

      // Show success animation
      setShowSuccess(true);
      successAnimation.play();
      
      // Wait for animation then close
      setTimeout(() => {
        onSuccess();
        onClose();
        setShowSuccess(false);
      }, 2000);
    } catch (error) {
      console.error('Error adding item:', error);
      Alert.alert('Error', 'Failed to add item. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStep1 = () => (
    <View style={[styles.stepContainer, debugBorder(true)]}>
      <Text style={styles.stepTitle}>Step 1: Choose Food Category</Text>
      <Text style={styles.stepSubtitle}>
        This helps us suggest the right units for your item
      </Text>
      
      <ScrollView style={styles.categoryGrid} showsVerticalScrollIndicator={false}>
        <View style={styles.categoryGridInner}>
          {FOOD_CATEGORIES.map(category => (
            <TouchableOpacity
              key={category.id}
              style={[
                styles.categoryCard,
                selectedCategory === category.id && styles.categoryCardSelected,
                { borderColor: category.color }
              ]}
              onPress={() => handleCategorySelect(category.id)}
            >
              <Text style={styles.categoryIcon}>{category.icon}</Text>
              <Text style={[
                styles.categoryLabel,
                selectedCategory === category.id && styles.categoryLabelSelected
              ]}>
                {category.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );

  const renderStep2 = () => {
    const rules = CATEGORY_UNIT_RULES[selectedCategory || 'other'] || CATEGORY_UNIT_RULES.other;
    const availableUnits = rules.units[selectedUnitType || rules.defaultType] || [];
    const categoryInfo = FOOD_CATEGORIES.find(c => c.id === selectedCategory);

    return (
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.stepContainer}
      >
        <View style={styles.stepHeader}>
          <IconButton
            icon="arrow-back"
            size={24}
            onPress={() => setCurrentStep(1)}
          />
          <Text style={styles.stepTitle}>Step 2: Item Details</Text>
        </View>

        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={[styles.selectedCategoryBadge, { backgroundColor: categoryInfo?.color + '20' }]}>
            <Text style={styles.categoryIcon}>{categoryInfo?.icon}</Text>
            <Text style={[styles.selectedCategoryText, { color: categoryInfo?.color }]}>
              {categoryInfo?.label}
            </Text>
          </View>

          <HybridTextInput
            label="Item Name *"
            value={itemName}
            onChangeText={(text) => {
              // Apply proper capitalization as user types
              const capitalized = capitalizeIngredientName(text);
              setItemName(capitalized);
              if (nameError) setNameError(''); // Clear error when user types
            }}
            placeholder="e.g., Whole Milk, Chicken Breast, Tomatoes"
            error={!!nameError}
            helperText={nameError}
            containerClassName="mb-4"
            debugName="ItemNameInput"
          />

          <View style={styles.formRow}>
            <HybridTextInput
              label="Quantity *"
              value={quantity}
              onChangeText={(text) => {
                if (itemName && selectedUnit) {
                  const formatted = formatQuantityInput(text, itemName, selectedUnit);
                  setQuantity(formatted);
                } else {
                  setQuantity(text);
                }
                if (quantityError) setQuantityError(''); // Clear error when user types
              }}
              placeholder="0"
              keyboardType="decimal-pad"
              error={!!quantityError}
              helperText={quantityError}
              containerClassName="flex-1 mr-2"
              debugName="QuantityInput"
            />

            <View style={[styles.formGroup, { flex: 1.5 }]}>
              <Text style={styles.label}>Unit *</Text>
              {rules.allowedTypes.length > 1 && (
                <View style={styles.unitTypeSelector}>
                  {rules.allowedTypes.map(type => (
                    <TouchableOpacity
                      key={type}
                      style={[
                        styles.unitTypeButton,
                        selectedUnitType === type && styles.unitTypeButtonSelected
                      ]}
                      onPress={() => {
                        setSelectedUnitType(type);
                        const units = rules.units[type] || [];
                        const defaultUnit = units.find(u => u.isDefault);
                        if (defaultUnit) {
                          setSelectedUnit(defaultUnit.id);
                        }
                      }}
                    >
                      <Text style={[
                        styles.unitTypeText,
                        selectedUnitType === type && styles.unitTypeTextSelected
                      ]}>
                        {type}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
              
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.unitSelector}>
                {availableUnits.map(unit => (
                  <TouchableOpacity
                    key={unit.id}
                    style={[
                      styles.unitButton,
                      selectedUnit === unit.id && styles.unitButtonSelected
                    ]}
                    onPress={() => setSelectedUnit(unit.id)}
                  >
                    <Text style={[
                      styles.unitButtonText,
                      selectedUnit === unit.id && styles.unitButtonTextSelected
                    ]}>
                      {unit.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          </View>

          {/* Unit validation feedback */}
          {unitValidationResult && unitValidationResult.severity !== 'info' && (
            <View style={[
              styles.validationContainer,
              unitValidationResult.severity === 'error' ? styles.validationError : styles.validationWarning
            ]}>
              <Ionicons 
                name={unitValidationResult.severity === 'error' ? 'alert-circle' : 'warning'} 
                size={16} 
                color={unitValidationResult.severity === 'error' ? '#EF4444' : '#F59E0B'} 
              />
              <Text style={[
                styles.validationText,
                unitValidationResult.severity === 'error' ? styles.validationTextError : styles.validationTextWarning
              ]}>
                {unitValidationResult.reason}
              </Text>
              {unitValidationResult.suggested_unit !== selectedUnit && (
                <TouchableOpacity
                  onPress={() => {
                    setSelectedUnit(unitValidationResult.suggested_unit);
                    // Find and set the appropriate unit type
                    const rules = CATEGORY_UNIT_RULES[selectedCategory || 'other'] || CATEGORY_UNIT_RULES.other;
                    for (const [type, units] of Object.entries(rules.units)) {
                      if (units.some((u: any) => u.id === unitValidationResult.suggested_unit)) {
                        setSelectedUnitType(type);
                        break;
                      }
                    }
                  }}
                  style={styles.suggestionButton}
                >
                  <Text style={styles.suggestionButtonText}>
                    Use {unitValidationResult.suggested_unit}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          )}

          {unitPreview ? (
            <View style={styles.previewContainer}>
              <Ionicons name="checkmark-circle" size={20} color="#10B981" />
              <Text style={styles.previewText}>Amount: {unitPreview}</Text>
            </View>
          ) : null}

          <View style={styles.formGroup}>
            <Text style={styles.label}>Expiration Date</Text>
            <TouchableOpacity
              style={styles.dateButton}
              onPress={() => setShowDatePicker(true)}
            >
              <Ionicons name="calendar-outline" size={20} color="#6B7280" />
              <Text style={styles.dateButtonText}>
                {expirationDate.toLocaleDateString()}
              </Text>
            </TouchableOpacity>
          </View>

          <HybridTextInput
            label="Notes (optional)"
            value={notes}
            onChangeText={setNotes}
            placeholder="e.g., Organic, Low-fat, Brand name"
            multiline
            containerClassName="mb-4"
            className="min-h-[80px]"
            debugName="NotesInput"
          />
        </ScrollView>

        {showDatePicker && (
          <DateTimePicker
            value={expirationDate}
            mode="date"
            display="default"
            onChange={(event, selectedDate) => {
              setShowDatePicker(false);
              if (selectedDate) {
                setExpirationDate(selectedDate);
              }
            }}
            minimumDate={new Date()}
          />
        )}
      </KeyboardAvoidingView>
    );
  };

  return (
    <Portal>
      <Dialog visible={visible} onDismiss={onClose} style={styles.dialog}>
        <Dialog.Title style={styles.dialogTitle}>
          Add to Pantry
        </Dialog.Title>
        
        <View style={styles.stepIndicator}>
          <View style={[styles.stepDot, currentStep >= 1 && styles.stepDotActive]} />
          <View style={[styles.stepLine, currentStep >= 2 && styles.stepLineActive]} />
          <View style={[styles.stepDot, currentStep >= 2 && styles.stepDotActive]} />
        </View>

        <Dialog.ScrollArea style={styles.scrollArea}>
          <ScrollView showsVerticalScrollIndicator={false}>
            {showSuccess ? (
              <View style={styles.successContainer}>
                <SuccessAnimation
                  ref={successAnimation.ref}
                  size={200}
                  onAnimationFinish={successAnimation.onAnimationFinish}
                />
                <Text style={styles.successText}>Item added to pantry!</Text>
              </View>
            ) : (
              <>
                {currentStep === 1 && renderStep1()}
                {currentStep === 2 && renderStep2()}
              </>
            )}
          </ScrollView>
        </Dialog.ScrollArea>

        <Dialog.Actions style={styles.dialogActions}>
          <Button onPress={onClose} textColor="#374151">
            Cancel
          </Button>
          
          <Button 
            mode="contained"
            onPress={handleSubmit}
            loading={isLoading}
            disabled={isLoading}
            buttonColor="#10B981"
            icon="plus-circle"
          >
            Add to Pantry
          </Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
};

const styles = StyleSheet.create({
  dialog: {
    maxHeight: '85%',
  },
  dialogTitle: {
    textAlign: 'center',
    fontSize: 20,
    fontWeight: '600',
  },
  stepIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  stepDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#D1D5DB',
  },
  stepDotActive: {
    backgroundColor: '#10B981',
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  stepLine: {
    width: 40,
    height: 2,
    backgroundColor: '#D1D5DB',
    marginHorizontal: 8,
  },
  stepLineActive: {
    backgroundColor: '#10B981',
  },
  scrollArea: {
    paddingHorizontal: 0,
    maxHeight: 500,
  },
  stepContainer: {
    paddingHorizontal: 20,
    paddingTop: 10,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  stepTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
    flex: 1,
  },
  stepSubtitle: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 8,
    marginBottom: 20,
  },
  categoryGrid: {
    flex: 1,
    maxHeight: 400,
  },
  categoryGridInner: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingBottom: 20,
  },
  categoryCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#E5E7EB',
  },
  categoryCardSelected: {
    borderWidth: 2,
  },
  categoryIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  categoryLabel: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
    textAlign: 'center',
  },
  categoryLabelSelected: {
    fontWeight: '600',
  },
  selectedCategoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginBottom: 20,
  },
  selectedCategoryText: {
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  formGroup: {
    marginBottom: 20,
  },
  formRow: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  unitTypeSelector: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  unitTypeButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
  },
  unitTypeButtonSelected: {
    backgroundColor: '#10B981',
  },
  unitTypeText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  unitTypeTextSelected: {
    color: '#fff',
  },
  unitSelector: {
    flexDirection: 'row',
    marginTop: 4,
  },
  unitButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    marginRight: 8,
  },
  unitButtonSelected: {
    backgroundColor: '#10B981',
    borderColor: '#10B981',
  },
  unitButtonText: {
    fontSize: 14,
    color: '#374151',
  },
  unitButtonTextSelected: {
    color: '#fff',
    fontWeight: '600',
  },
  previewContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginBottom: 20,
  },
  previewText: {
    fontSize: 14,
    color: '#065F46',
    fontWeight: '500',
    marginLeft: 8,
  },
  dateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  dateButtonText: {
    fontSize: 16,
    color: '#111827',
    marginLeft: 8,
  },
  dialogActions: {
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  validationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginBottom: 12,
    flexWrap: 'wrap',
  },
  validationError: {
    backgroundColor: '#FEE2E2',
  },
  validationWarning: {
    backgroundColor: '#FEF3C7',
  },
  validationText: {
    fontSize: 13,
    marginLeft: 6,
    flex: 1,
  },
  validationTextError: {
    color: '#991B1B',
  },
  validationTextWarning: {
    color: '#92400E',
  },
  suggestionButton: {
    marginLeft: 8,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: 'rgba(0,0,0,0.1)',
  },
  suggestionButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#374151',
  },
  successContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  successText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#10B981',
    marginTop: 20,
  },
});