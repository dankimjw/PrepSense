import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons, MaterialIcons, MaterialCommunityIcons } from '@expo/vector-icons';
import { getCategoryColor } from '../../utils/itemHelpers';
import { formatQuantity } from '../../utils/numberFormatting';

export interface PantryItemData {
  id: string;
  name: string;
  quantity_amount: number;
  quantity_unit: string;
  category: string;
  expiry: string;
  daysUntilExpiry: number;
  expirationDate: Date;
  count?: number;
  icon: string;
  color?: string;
  iconColor?: string;
  bgColor?: string;
  isCommunity?: boolean;
  isBox?: boolean;
  isProduce?: boolean;
  isCan?: boolean;
}

interface PantryItemProps {
  item: PantryItemData;
  onPress: (item: PantryItemData) => void;
  onEditPress?: (item: PantryItemData) => void;
}

export const PantryItem: React.FC<PantryItemProps> = ({ item, onPress, onEditPress }) => {
  return (
    <TouchableOpacity 
      style={styles.itemCard}
      onPress={() => onPress(item)}
    >
      <View style={[
        styles.itemIcon,
        { 
          backgroundColor: item.color + '20', // Add transparency to the color
          borderRadius: item.isBox ? 6 : 20,
        },
        item.isProduce && styles.produceIcon,
        item.isBox && styles.boxIcon,
        item.isCan && styles.canIcon
      ]}>
        {item.isCommunity ? (
          <MaterialCommunityIcons 
            name={item.icon as any} 
            size={24} 
            color={item.color}
          />
        ) : (
          <MaterialIcons 
            name={item.icon as any} 
            size={24} 
            color={item.color}
          />
        )}
      </View>
      <View style={styles.itemInfo}>
        <View style={styles.itemNameRow}>
          <View style={styles.itemNameContainer}>
            <Text 
              style={styles.itemName} 
              numberOfLines={1} 
              ellipsizeMode="tail"
            >
              {item.name}
            </Text>
          </View>
          <View style={styles.itemAmountContainer}>
            <Text 
              style={styles.itemAmount}
              numberOfLines={1}
            >
              {formatQuantity(item.quantity_amount)} {item.quantity_unit}
            </Text>
          </View>
        </View>
        <View style={styles.itemDetails}>
          <View style={[styles.categoryTag, { 
            backgroundColor: getCategoryColor(item.category),
            opacity: item.daysUntilExpiry <= 3 ? 0.9 : 0.7
          }]}>
            <Text style={styles.categoryText}>{item.category}</Text>
          </View>
          <Text style={[
            styles.itemExpiry,
            item.daysUntilExpiry <= 0 ? styles.expired : null,
            item.daysUntilExpiry <= 3 ? styles.expiringSoon : null
          ]}>
            {item.expiry}
          </Text>
        </View>
      </View>
      <TouchableOpacity 
        style={styles.moreButton}
        onPress={(e) => {
          e.stopPropagation();
          if (onEditPress) {
            onEditPress(item);
          }
        }}
      >
        <Ionicons name="ellipsis-vertical" size={20} color="#6B7280" />
      </TouchableOpacity>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  itemCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  itemIcon: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  boxIcon: {},
  canIcon: {},
  produceIcon: {},
  itemInfo: {
    flex: 1,
    flexDirection: 'column',
  },
  itemNameRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
    flex: 1,
  },
  itemDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    flexShrink: 1,
    flexWrap: 'wrap',
  },
  itemNameContainer: {
    flex: 1,
    marginRight: 8,
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  itemAmountContainer: {
    flexShrink: 0,
  },
  itemAmount: {
    fontSize: 14,
    color: '#1F2937',
    fontWeight: '500',
  },
  itemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 4,
  },
  itemExpiry: {
    fontSize: 14,
    color: '#6B7280',
    marginLeft: 8,
  },
  expiringSoon: {
    color: '#D97706',
  },
  expired: {
    color: '#DC2626',
    fontWeight: '600',
  },
  categoryTag: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  categoryText: {
    fontSize: 12,
    color: '#4B5563',
    fontWeight: '500',
  },
  moreButton: {
    padding: 8,
  },
});