// app/components/UserPreferencesModal.tsx - Part of the PrepSense mobile app
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  Pressable,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Config } from '../../config';
import { useAuth } from '../../context/AuthContext';
import { useUserPreferences } from '../../context/UserPreferencesContext';

const ALLERGENS = [
  'Dairy', 'Nuts', 'Peanuts', 'Eggs', 'Soy', 'Gluten', 
  'Shellfish', 'Fish'
];

const DIETARY_PREFERENCES = [
  'Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 
  'Low-Carb', 'Keto', 'Paleo', 'Mediterranean', 
  'Low-Sodium', 'High-Protein'
];

const CUISINES = [
  'Italian', 'Mexican', 'Asian', 'Indian', 'Mediterranean', 
  'American', 'French', 'Thai', 'Japanese', 'Chinese',
  'Korean', 'Greek', 'Spanish', 'Middle Eastern', 'Brazilian'
];

// Remove local interface - use the one from UserPreferencesContext

interface UserPreferencesModalProps {
  visible: boolean;
  onClose: () => void;
}

const UserPreferencesModal: React.FC<UserPreferencesModalProps> = ({
  visible,
  onClose,
}) => {
  const { token: authToken } = useAuth();
  const { 
    preferences, 
    updatePreferences, 
    addAllergen, 
    removeAllergen,
    addDietaryPreference,
    removeDietaryPreference,
    addCuisine,
    removeCuisine,
    isLoading 
  } = useUserPreferences();

  // No need for custom loading - context handles it

  const savePreferences = async () => {
    try {
      // Context already handles saving to AsyncStorage automatically
      Alert.alert('Success', 'Your preferences have been saved!');
      onClose();
    } catch (error) {
      console.error('Error saving preferences:', error);
      Alert.alert('Error', 'Failed to save preferences. Please try again.');
    }
  };

  const toggleSelection = async (
    category: 'allergens' | 'dietaryPreferences' | 'cuisines',
    item: string
  ) => {
    try {
      const isSelected = preferences[category]?.includes(item) || false;
      
      if (category === 'allergens') {
        if (isSelected) {
          await removeAllergen(item);
        } else {
          await addAllergen(item);
        }
      } else if (category === 'dietaryPreferences') {
        if (isSelected) {
          await removeDietaryPreference(item);
        } else {
          await addDietaryPreference(item);
        }
      } else if (category === 'cuisines') {
        if (isSelected) {
          await removeCuisine(item);
        } else {
          await addCuisine(item);
        }
      }
    } catch (error) {
      console.error('Error toggling preference:', error);
    }
  };

  const renderMultiSelect = (
    title: string,
    items: string[],
    category: 'allergens' | 'dietaryPreferences' | 'cuisines',
    icon: string
  ) => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Ionicons name={icon as any} size={20} color="#1b6b45" />
        <Text style={styles.sectionTitle}>{title}</Text>
      </View>
      <View style={styles.optionsGrid}>
        {items.map((item) => {
          const isSelected = preferences[category]?.includes(item) || false;
          return (
            <TouchableOpacity
              key={item}
              style={[
                styles.optionButton,
                isSelected && styles.optionButtonSelected,
              ]}
              onPress={() => toggleSelection(category, item)}
            >
              <Text
                style={[
                  styles.optionText,
                  isSelected && styles.optionTextSelected,
                ]}
              >
                {item}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>User Preferences</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color="#666" />
          </TouchableOpacity>
        </View>

        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#1b6b45" />
            <Text style={styles.loadingText}>Loading preferences...</Text>
          </View>
        ) : (
          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {renderMultiSelect(
              'Allergens',
              ALLERGENS,
              'allergens',
              'warning-outline'
            )}

            {renderMultiSelect(
              'Dietary Restrictions',
              DIETARY_PREFERENCES,
              'dietaryPreferences',
              'nutrition-outline'
            )}

            {renderMultiSelect(
              'Favorite Cuisines',
              CUISINES,
              'cuisines',
              'restaurant-outline'
            )}

          <View style={styles.summary}>
            <Text style={styles.summaryTitle}>Summary</Text>
            <Text style={styles.summaryText}>
              Allergens: {preferences.allergens?.length > 0 ? preferences.allergens.join(', ') : 'None'}
            </Text>
            <Text style={styles.summaryText}>
              Dietary: {preferences.dietaryPreferences?.length > 0 ? preferences.dietaryPreferences.join(', ') : 'None'}
            </Text>
            <Text style={styles.summaryText}>
              Cuisines: {preferences.cuisines?.length > 0 ? preferences.cuisines.join(', ') : 'Any'}
            </Text>
          </View>
        </ScrollView>
        )}

        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.saveButton, isLoading && styles.saveButtonDisabled]}
            onPress={savePreferences}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.saveButtonText}>Save Preferences</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5e5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1b6b45',
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  section: {
    marginVertical: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginLeft: 8,
  },
  optionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  optionButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#ddd',
    backgroundColor: '#f9f9f9',
    marginBottom: 8,
  },
  optionButtonSelected: {
    backgroundColor: '#1b6b45',
    borderColor: '#1b6b45',
  },
  optionText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  optionTextSelected: {
    color: '#fff',
  },
  summary: {
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 8,
    marginVertical: 20,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  summaryText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  footer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#e5e5e5',
  },
  saveButton: {
    backgroundColor: '#1b6b45',
    borderRadius: 8,
    paddingVertical: 16,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  saveButtonDisabled: {
    backgroundColor: '#ccc',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 50,
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
    fontSize: 16,
  },
});

export default UserPreferencesModal;