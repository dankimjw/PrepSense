import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { PantryItem, PantryItemData } from './PantryItem';

interface PantryItemsListProps {
  items: PantryItemData[];
  title?: string;
  showSeeAll?: boolean;
  onItemPress: (item: PantryItemData) => void;
  onSeeAllPress?: () => void;
}

export const PantryItemsList: React.FC<PantryItemsListProps> = ({
  items,
  title = 'Expiring Soon',
  showSeeAll = true,
  onItemPress,
  onSeeAllPress,
}) => {
  return (
    <>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {showSeeAll && (
          <TouchableOpacity onPress={onSeeAllPress}>
            <Text style={styles.seeAll}>See All</Text>
          </TouchableOpacity>
        )}
      </View>
      
      <View style={styles.recentItems}>
        {items.map((item, index) => (
          <PantryItem
            key={`item-${item.id}-${index}`}
            item={item}
            onPress={onItemPress}
          />
        ))}
      </View>
    </>
  );
};

const styles = StyleSheet.create({
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  seeAll: {
    color: '#297A56',
    fontWeight: '500',
  },
  recentItems: {
    marginBottom: 24,
  },
});