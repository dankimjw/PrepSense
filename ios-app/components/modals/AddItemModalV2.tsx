import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { addPantryItem } from '../../services/api';
import { formatQuantity } from '../../utils/numberFormatting';

// Food categories with their allowed unit types
const FOOD_CATEGORIES = [
  { id: 'produce', label: 'Produce', icon: '🥬', color: '#4ADE80' },
  { id: 'dairy', label: 'Dairy', icon: '🥛', color: '#60A5FA' },
  { id: 'meat', label: 'Meat', icon: '🥩', color: '#F87171' },
  { id: 'seafood', label: 'Seafood', icon: '🐟', color: '#93C5FD' },
  { id: 'grains', label: 'Grains', icon: '🌾', color: '#FBBF24' },
  { id: 'bakery', label: 'Bakery', icon: '🍞', color: '#D97706' },
  { id: 'beverages', label: 'Beverages', icon: '🥤', color: '#06B6D4' },
  { id: 'condiments', label: 'Condiments', icon: '🍯', color: '#F59E0B' },
  { id: 'oils', label: 'Oils & Vinegars', icon: '🫒', color: '#84CC16' },
  { id: 'baking', label: 'Baking', icon: '🧁', color: '#F472B6' },
  { id: 'spices', label: 'Spices', icon: '🌶️', color: '#EF4444' },
  { id: 'pasta', label: 'Pasta & Rice', icon: '🍝', color: '#A78BFA' },
  { id: 'canned', label: 'Canned Goods', icon: '🥫', color: '#FB923C' },
  { id: 'frozen', label: 'Frozen', icon: '🧊', color: '#67E8F9' },
  { id: 'snacks', label: 'Snacks', icon: '🍿', color: '#FACC15' },
  { id: 'other', label: 'Other', icon: '📦', color: '#9CA3AF' },
];

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

interface AddItemModalV2Props {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const AddItemModalV2: React.FC<AddItemModalV2Props> = ({
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
    }
  }, [visible]);

  // Update unit preview
  useEffect(() => {
    if (quantity && selectedUnit) {
      const unitLabel = getUnitLabel(selectedUnit);
      setUnitPreview(`${formatQuantity(quantity)} ${unitLabel}`);
    } else {
      setUnitPreview('');
    }
  }, [quantity, selectedUnit]);

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

  const handleSubmit = async () => {
    if (!itemName || !quantity || !selectedUnit || !selectedCategory) {
      Alert.alert('Missing Information', 'Please fill in all required fields.');
      return;
    }

    setIsLoading(true);

    try {
      const categoryInfo = FOOD_CATEGORIES.find(c => c.id === selectedCategory);
      
      await addPantryItem({
        user_id: 111, // TODO: Get actual user ID
        product_name: itemName,
        quantity: parseFloat(quantity),
        unit_of_measurement: selectedUnit,
        expiration_date: expirationDate.toISOString().split('T')[0],
        food_category: categoryInfo?.label || 'Other',
        notes: notes || undefined,
      });

      Alert.alert('Success', 'Item added to pantry!', [
        { text: 'OK', onPress: () => {
          onSuccess();
          onClose();
        }}
      ]);
    } catch (error) {
      console.error('Error adding item:', error);
      Alert.alert('Error', 'Failed to add item. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStep1 = () => (
    <View style={styles.stepContainer}>
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
          <TouchableOpacity onPress={() => setCurrentStep(1)} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color="#374151" />
          </TouchableOpacity>
          <Text style={styles.stepTitle}>Step 2: Item Details</Text>
        </View>

        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={[styles.selectedCategoryBadge, { backgroundColor: categoryInfo?.color + '20' }]}>
            <Text style={styles.categoryIcon}>{categoryInfo?.icon}</Text>
            <Text style={[styles.selectedCategoryText, { color: categoryInfo?.color }]}>
              {categoryInfo?.label}
            </Text>
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Item Name *</Text>
            <TextInput
              style={styles.input}
              value={itemName}
              onChangeText={setItemName}
              placeholder="e.g., Whole Milk, Chicken Breast, Tomatoes"
              placeholderTextColor="#9CA3AF"
            />
          </View>

          <View style={styles.formRow}>
            <View style={[styles.formGroup, { flex: 1, marginRight: 8 }]}>
              <Text style={styles.label}>Quantity *</Text>
              <TextInput
                style={styles.input}
                value={quantity}
                onChangeText={setQuantity}
                placeholder="0"
                keyboardType="numeric"
                placeholderTextColor="#9CA3AF"
              />
            </View>

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

          <View style={styles.formGroup}>
            <Text style={styles.label}>Notes (optional)</Text>
            <TextInput
              style={[styles.input, styles.notesInput]}
              value={notes}
              onChangeText={setNotes}
              placeholder="e.g., Organic, Low-fat, Brand name"
              placeholderTextColor="#9CA3AF"
              multiline
            />
          </View>
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity 
            style={styles.cancelButton} 
            onPress={onClose}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.submitButton, isLoading && styles.submitButtonDisabled]} 
            onPress={handleSubmit}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <>
                <Ionicons name="add-circle" size={20} color="#fff" />
                <Text style={styles.submitButtonText}>Add to Pantry</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

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
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Text style={styles.title}>Add to Pantry</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color="#374151" />
            </TouchableOpacity>
          </View>
          
          <View style={styles.stepIndicator}>
            <View style={[styles.stepDot, currentStep >= 1 && styles.stepDotActive]} />
            <View style={[styles.stepLine, currentStep >= 2 && styles.stepLineActive]} />
            <View style={[styles.stepDot, currentStep >= 2 && styles.stepDotActive]} />
          </View>
        </View>

        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
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
    backgroundColor: '#fff',
    paddingTop: 60,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
  },
  closeButton: {
    position: 'absolute',
    right: 20,
    padding: 4,
  },
  stepIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
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
  stepContainer: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  backButton: {
    marginRight: 12,
    padding: 4,
  },
  stepTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  stepSubtitle: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 8,
    marginBottom: 20,
  },
  categoryGrid: {
    flex: 1,
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
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#111827',
  },
  notesInput: {
    minHeight: 80,
    textAlignVertical: 'top',
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
  footer: {
    flexDirection: 'row',
    paddingTop: 20,
    paddingBottom: 40,
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
  submitButton: {
    flex: 2,
    flexDirection: 'row',
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#10B981',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});