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

const ALLERGENS = [
  'Dairy', 'Nuts', 'Peanuts', 'Eggs', 'Soy', 'Gluten', 
  'Shellfish', 'Fish', 'Sesame', 'Sulfites'
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

interface UserPreferences {
  allergens: string[];
  dietary_restrictions: string[];
  cuisine_preferences: string[];
}

interface UserPreferencesModalProps {
  visible: boolean;
  onClose: () => void;
}

const UserPreferencesModal: React.FC<UserPreferencesModalProps> = ({
  visible,
  onClose,
}) => {
  const { token: authToken } = useAuth();
  const [preferences, setPreferences] = useState<UserPreferences>({
    allergens: [],
    dietary_restrictions: [],
    cuisine_preferences: [],
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (visible) {
      loadPreferences();
    }
  }, [visible]);

  const loadPreferences = async () => {
    setLoading(true);
    try {
      // First try to load from backend
      if (authToken) {
        console.log('Loading preferences from backend with token:', authToken);
        const response = await fetch(`${Config.API_BASE_URL}/preferences/`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          setPreferences(data.preferences);
          // Also save to AsyncStorage as backup
          await AsyncStorage.setItem('prepsense_user_preferences', JSON.stringify(data.preferences));
          setLoading(false);
          return;
        }
      }
      
      // Fallback to AsyncStorage if backend fails or no auth
      const saved = await AsyncStorage.getItem('prepsense_user_preferences');
      if (saved) {
        const parsed = JSON.parse(saved);
        setPreferences(parsed);
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
      // Try AsyncStorage as fallback
      try {
        const saved = await AsyncStorage.getItem('prepsense_user_preferences');
        if (saved) {
          const parsed = JSON.parse(saved);
          setPreferences(parsed);
        }
      } catch (storageError) {
        console.error('Error loading from AsyncStorage:', storageError);
      }
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    setLoading(true);
    try {
      console.log('Saving preferences, authToken exists:', !!authToken);
      // First try to save to backend
      if (authToken) {
        const response = await fetch(`${Config.API_BASE_URL}/preferences/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(preferences),
        });
        
        if (response.ok) {
          // Also save to AsyncStorage as backup
          await AsyncStorage.setItem('prepsense_user_preferences', JSON.stringify(preferences));
          Alert.alert('Success', 'Your preferences have been saved!');
          onClose();
          setLoading(false);
          return;
        } else {
          const errorText = await response.text();
          console.error('Failed to save preferences to backend:', response.status, errorText);
          console.warn('Failed to save to backend, falling back to AsyncStorage');
        }
      }
      
      // Fallback to AsyncStorage only
      await AsyncStorage.setItem('prepsense_user_preferences', JSON.stringify(preferences));
      Alert.alert('Success', 'Your preferences have been saved locally!');
      onClose();
    } catch (error) {
      console.error('Error saving preferences:', error);
      Alert.alert('Error', 'Failed to save preferences. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSelection = (
    category: keyof UserPreferences,
    item: string
  ) => {
    setPreferences(prev => ({
      ...prev,
      [category]: prev[category].includes(item)
        ? prev[category].filter(i => i !== item)
        : [...prev[category], item]
    }));
  };

  const renderMultiSelect = (
    title: string,
    items: string[],
    category: keyof UserPreferences,
    icon: string
  ) => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Ionicons name={icon as any} size={20} color="#1b6b45" />
        <Text style={styles.sectionTitle}>{title}</Text>
      </View>
      <View style={styles.optionsGrid}>
        {items.map((item) => {
          const isSelected = preferences[category].includes(item);
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

        {loading ? (
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
              'dietary_restrictions',
              'nutrition-outline'
            )}

            {renderMultiSelect(
              'Favorite Cuisines',
              CUISINES,
              'cuisine_preferences',
              'restaurant-outline'
            )}

          <View style={styles.summary}>
            <Text style={styles.summaryTitle}>Summary</Text>
            <Text style={styles.summaryText}>
              Allergens: {preferences.allergens.length > 0 ? preferences.allergens.join(', ') : 'None'}
            </Text>
            <Text style={styles.summaryText}>
              Dietary: {preferences.dietary_restrictions.length > 0 ? preferences.dietary_restrictions.join(', ') : 'None'}
            </Text>
            <Text style={styles.summaryText}>
              Cuisines: {preferences.cuisine_preferences.length > 0 ? preferences.cuisine_preferences.join(', ') : 'Any'}
            </Text>
          </View>
        </ScrollView>
        )}

        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.saveButton, loading && styles.saveButtonDisabled]}
            onPress={savePreferences}
            disabled={loading}
          >
            {loading ? (
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