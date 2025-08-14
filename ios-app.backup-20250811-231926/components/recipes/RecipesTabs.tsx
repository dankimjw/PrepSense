import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Modal,
  Pressable,
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Router } from 'expo-router';

type ActiveTab = 'pantry' | 'discover' | 'my-recipes';
type SortOption = 'name' | 'date' | 'rating' | 'missing';

interface RecipesTabsProps {
  activeTab: ActiveTab;
  searchQuery: string;
  searchFocused: boolean;
  showSortModal: boolean;
  sortBy: SortOption;
  onTabChange: (tab: ActiveTab) => void;
  onSearchQueryChange: (query: string) => void;
  onSearchFocusChange: (focused: boolean) => void;
  onSortModalToggle: (show: boolean) => void;
  onSortChange: (sort: SortOption) => void;
  onSearchSubmit: () => void;
  router: Router;
}

const sortOptions = [
  { value: 'name', label: 'Name (A-Z)', icon: 'alphabetical' },
  { value: 'date', label: 'Recently Added', icon: 'clock-outline' },
  { value: 'rating', label: 'Highest Rated', icon: 'star' },
  { value: 'missing', label: 'Fewest Missing', icon: 'checkbox-marked-circle' },
];

export default function RecipesTabs({
  activeTab,
  searchQuery,
  searchFocused,
  showSortModal,
  sortBy,
  onTabChange,
  onSearchQueryChange,
  onSearchFocusChange,
  onSortModalToggle,
  onSortChange,
  onSearchSubmit,
  router,
}: RecipesTabsProps) {
  return (
    <>
      {/* Subheader for recipes screen */}
      <View style={styles.subHeader}>
        <Text testID="header-title" style={styles.headerTitle}>Recipes</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity testID="sort-button" onPress={() => onSortModalToggle(true)} style={styles.headerButton}>
            <MaterialCommunityIcons name="sort" size={24} color="#297A56" accessibilityLabel="Sort recipes" />
          </TouchableOpacity>
          <TouchableOpacity testID="chat-button" onPress={() => router.push('/chat')} style={styles.headerButton}>
            <MaterialCommunityIcons name="chef-hat" size={24} color="#297A56" accessibilityLabel="Open recipe chat" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Bar */}
      <View testID="search-container" style={styles.searchContainer}>
        <View style={[styles.searchBar, searchFocused && styles.searchBarFocused]}>
          <Ionicons name="search" size={20} color="#666" accessibilityLabel="Search icon" />
          <TextInput
            testID="search-input"
            style={styles.searchInput}
            placeholder={`Search ${activeTab === 'pantry' ? 'pantry recipes' : activeTab === 'discover' ? 'all recipes' : 'your recipes'}...`}
            value={searchQuery}
            onChangeText={onSearchQueryChange}
            onSubmitEditing={onSearchSubmit}
            returnKeyType="search"
            onFocus={() => onSearchFocusChange(true)}
            onBlur={() => onSearchFocusChange(false)}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity testID="clear-search-button" onPress={() => onSearchQueryChange('')}>
              <Ionicons name="close-circle" size={20} color="#666" accessibilityLabel="Clear search" />
            </TouchableOpacity>
          )}
        </View>
        {activeTab === 'discover' && searchQuery.length > 0 && (
          <TouchableOpacity testID="search-submit-button" style={styles.searchButton} onPress={onSearchSubmit}>
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Tab Navigation */}
      <View testID="tab-container" style={styles.tabContainer}>
        <TouchableOpacity
          testID="pantry-tab"
          style={[styles.tab, activeTab === 'pantry' && styles.activeTab]}
          onPress={() => onTabChange('pantry')}
        >
          <Text style={[styles.tabText, activeTab === 'pantry' && styles.activeTabText]}>
            From Pantry
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="discover-tab"
          style={[styles.tab, activeTab === 'discover' && styles.activeTab]}
          onPress={() => onTabChange('discover')}
        >
          <Text style={[styles.tabText, activeTab === 'discover' && styles.activeTabText]}>
            Discover
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="my-recipes-tab"
          style={[styles.tab, activeTab === 'my-recipes' && styles.activeTab]}
          onPress={() => onTabChange('my-recipes')}
        >
          <Text style={[styles.tabText, activeTab === 'my-recipes' && styles.activeTabText]}>
            My Recipes
          </Text>
        </TouchableOpacity>
      </View>

      {/* Sort Modal */}
      <Modal
        testID="sort-modal"
        visible={showSortModal}
        transparent
        animationType="slide"
        onRequestClose={() => onSortModalToggle(false)}
      >
        <Pressable testID="sort-modal-overlay" style={styles.modalOverlay} onPress={() => onSortModalToggle(false)}>
          <View testID="sort-modal-content" style={styles.modalContent}>
            <Text testID="sort-modal-title" style={styles.modalTitle}>Sort By</Text>
            {sortOptions.map(option => (
              <TouchableOpacity
                key={option.value}
                testID={`sort-option-${option.value}`}
                style={[styles.sortOption, sortBy === option.value && styles.sortOptionActive]}
                onPress={() => {
                  onSortChange(option.value as SortOption);
                  onSortModalToggle(false);
                }}
              >
                <MaterialCommunityIcons 
                  name={option.icon as any} 
                  size={24} 
                  color={sortBy === option.value ? '#297A56' : '#666'} 
                  accessibilityLabel={`Sort by ${option.label}`}
                />
                <Text style={[
                  styles.sortOptionText,
                  sortBy === option.value && styles.sortOptionTextActive
                ]}>
                  {option.label}
                </Text>
                {sortBy === option.value && (
                  <Ionicons name="checkmark" size={24} color="#297A56" accessibilityLabel="Selected" />
                )}
              </TouchableOpacity>
            ))}
          </View>
        </Pressable>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  subHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#297A56',
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  headerButton: {
    padding: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    alignItems: 'center',
    gap: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 40,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  searchBarFocused: {
    borderColor: '#297A56',
    backgroundColor: '#fff',
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#333',
  },
  searchButton: {
    backgroundColor: '#297A56',
    paddingHorizontal: 20,
    height: 40,
    borderRadius: 10,
    justifyContent: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#297A56',
  },
  tabText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#297A56',
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 40,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  sortOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 10,
    marginBottom: 8,
  },
  sortOptionActive: {
    backgroundColor: '#E6F7F0',
  },
  sortOptionText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    marginLeft: 16,
  },
  sortOptionTextActive: {
    color: '#297A56',
    fontWeight: '600',
  },
});