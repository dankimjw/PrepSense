import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

interface SortFilterBarProps {
  sortBy: 'name' | 'expiry' | 'category' | 'dateAdded';
  sortOrder: 'asc' | 'desc';
  onSortChange: (sortBy: 'name' | 'expiry' | 'category' | 'dateAdded') => void;
  onSortOrderToggle: () => void;
}

export function SortFilterBar({ sortBy, sortOrder, onSortChange, onSortOrderToggle }: SortFilterBarProps) {
  const sortOptions = [
    { id: 'name', label: 'Name', icon: 'text' },
    { id: 'expiry', label: 'Expiry', icon: 'calendar-outline' },
    { id: 'category', label: 'Category', icon: 'pricetag-outline' },
    { id: 'dateAdded', label: 'Added', icon: 'time-outline' },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Sort by:</Text>
      <View style={styles.buttonsContainer}>
        {sortOptions.map((option) => {
          const isActive = sortBy === option.id;
          
          return (
            <TouchableOpacity
              key={option.id}
              onPress={() => onSortChange(option.id as any)}
              activeOpacity={0.7}
              style={styles.touchableButton}
            >
              {isActive ? (
                <LinearGradient
                  colors={['#348F68', '#297A56']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.gradientButton}
                >
                  <Ionicons 
                    name={option.icon as any} 
                    size={16} 
                    color="#fff" 
                  />
                  <Text style={styles.sortButtonTextActive}>
                    {option.label}
                  </Text>
                </LinearGradient>
              ) : (
                <View style={styles.sortButton}>
                  <Ionicons 
                    name={option.icon as any} 
                    size={16} 
                    color="#6B7280" 
                  />
                  <Text style={styles.sortButtonText}>
                    {option.label}
                  </Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
        
        <TouchableOpacity
          style={styles.orderButton}
          onPress={onSortOrderToggle}
          activeOpacity={0.7}
        >
          <MaterialCommunityIcons 
            name={sortOrder === 'asc' ? 'sort-ascending' : 'sort-descending'} 
            size={20} 
            color="#297A56" 
          />
          <Text style={styles.orderButtonText}>
            {sortBy === 'expiry' 
              ? 'Closest' 
              : sortOrder === 'asc' ? 'A-Z' : 'Z-A'
            }
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  label: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
    fontWeight: '600',
  },
  buttonsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    alignItems: 'center',
  },
  touchableButton: {
    // No styling needed, just a container
  },
  sortButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    gap: 4,
    justifyContent: 'center',
    opacity: 0.8,
  },
  gradientButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 4,
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  sortButtonText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  sortButtonTextActive: {
    color: '#fff',
    fontWeight: '700',
  },
  orderButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    gap: 4,
  },
  orderButtonText: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '500',
  },
});