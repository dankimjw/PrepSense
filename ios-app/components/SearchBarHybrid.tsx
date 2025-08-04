// Hybrid SearchBar component using React Native Paper with NativeWind styling
import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { Searchbar, IconButton } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { HybridTextInput } from './hybrid/HybridTextInput';
import { LoadingAnimation } from './hybrid/HybridLottie';
import { debugLog } from './debug/DebugPanel';

interface SearchBarHybridProps {
  onSearch: (text: string) => void;
  onFilterPress: () => void;
  onSortPress: () => void;
  searchQuery: string;
  placeholder?: string;
  isLoading?: boolean;
  // Hybrid styling props
  containerClassName?: string;
  searchClassName?: string;
}

export const SearchBarHybrid: React.FC<SearchBarHybridProps> = ({
  onSearch,
  onFilterPress,
  onSortPress,
  searchQuery,
  placeholder = "Search items...",
  isLoading = false,
  containerClassName = "px-4 mb-4",
  searchClassName = "flex-1 mr-2",
}) => {
  
  // Debug logging
  React.useEffect(() => {
    debugLog('SearchBarHybrid', 'Search query changed', { searchQuery });
  }, [searchQuery]);

  return (
    <View className={`flex-row items-center ${containerClassName}`} style={styles.container}>
      {/* Use Paper's Searchbar component for better accessibility and theming */}
      <Searchbar
        placeholder={placeholder}
        onChangeText={onSearch}
        value={searchQuery}
        style={[styles.searchbar, { flex: 1, marginRight: 8 }]}
        inputStyle={styles.searchInput}
        iconColor="#6B7280"
        placeholderTextColor="#9CA3AF"
        className={searchClassName}
        // Show loading animation instead of search icon when loading
        icon={isLoading ? () => <LoadingAnimation size={24} /> : 'magnify'}
        // Enhanced accessibility
        accessible={true}
        accessibilityLabel="Search pantry items"
        accessibilityHint="Enter text to search your pantry items"
      />

      {/* Filter button with Paper IconButton for consistency */}
      <IconButton
        icon="filter"
        size={24}
        onPress={onFilterPress}
        style={styles.actionButton}
        iconColor="#4B5563"
        accessible={true}
        accessibilityLabel="Filter items"
        accessibilityHint="Open filter options"
      />

      {/* Sort button with Paper IconButton */}
      <IconButton
        icon="swap-vertical"
        size={24}
        onPress={onSortPress}
        style={styles.actionButton}
        iconColor="#4B5563"
        accessible={true}
        accessibilityLabel="Sort items"
        accessibilityHint="Change sorting order"
      />
    </View>
  );
};

// Alternative implementation using HybridTextInput for more customization
export const SearchBarHybridCustom: React.FC<SearchBarHybridProps> = ({
  onSearch,
  onFilterPress,
  onSortPress,
  searchQuery,
  placeholder = "Search items...",
  containerClassName = "px-4 mb-4",
  searchClassName = "flex-1 mr-2",
}) => {
  
  return (
    <View className={`flex-row items-center ${containerClassName}`} style={styles.container}>
      {/* Custom search input using HybridTextInput */}
      <View style={{ flex: 1, marginRight: 8 }}>
        <HybridTextInput
          value={searchQuery}
          onChangeText={onSearch}
          placeholder={placeholder}
          left={
            isLoading ? (
              <View style={styles.searchIconContainer}>
                <LoadingAnimation size={20} />
              </View>
            ) : (
              <View style={styles.searchIconContainer}>
                <Ionicons name="search" size={20} color="#6B7280" />
              </View>
            )
          }
          className={`${searchClassName} bg-gray-100 rounded-lg`}
          style={styles.customSearchInput}
          // No label for search input
          label=""
          // Enhanced accessibility
          accessible={true}
          accessibilityLabel="Search pantry items"
          accessibilityHint="Enter text to search your pantry items"
          debugName="SearchInput"
        />
      </View>

      {/* Action buttons using TouchableOpacity for custom styling */}
      <TouchableOpacity
        style={styles.customActionButton}
        onPress={onFilterPress}
        accessible={true}
        accessibilityLabel="Filter items"
        accessibilityHint="Open filter options"
      >
        <Ionicons name="filter" size={24} color="#4B5563" />
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.customActionButton}
        onPress={onSortPress}
        accessible={true}
        accessibilityLabel="Sort items"
        accessibilityHint="Change sorting order"
      >
        <Ionicons name="swap-vertical" size={24} color="#4B5563" />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  searchbar: {
    backgroundColor: '#F3F4F6',
    elevation: 0,
    shadowOpacity: 0,
  },
  searchInput: {
    fontSize: 16,
    color: '#111827',
  },
  actionButton: {
    backgroundColor: '#F3F4F6',
    margin: 0,
  },
  // Custom styles for alternative implementation
  customSearchInput: {
    backgroundColor: '#F3F4F6',
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 48,
  },
  searchIconContainer: {
    paddingLeft: 12,
    justifyContent: 'center',
  },
  customActionButton: {
    width: 48,
    height: 48,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
});