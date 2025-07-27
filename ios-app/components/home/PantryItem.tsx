import React, { useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Animated, Pressable } from 'react-native';
import { Ionicons, MaterialIcons, MaterialCommunityIcons } from '@expo/vector-icons';
import Swipeable from 'react-native-gesture-handler/Swipeable';
import { RectButton } from 'react-native-gesture-handler';
import { getCategoryBgColor } from '../../utils/itemHelpers';
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
  onSwipeEdit?: (item: PantryItemData) => void;
  onDelete?: (item: PantryItemData) => void;
}

export const PantryItem: React.FC<PantryItemProps> = ({ item, onPress, onEditPress, onSwipeEdit, onDelete }) => {
  const swipeableRef = useRef<Swipeable>(null);

  const renderLeftActions = (
    progress: Animated.AnimatedValue,
    dragX: Animated.AnimatedValue
  ) => {
    const trans = dragX.interpolate({
      inputRange: [0, 100],
      outputRange: [-100, 0],
      extrapolate: 'clamp',
    });

    return (
      <RectButton
        style={styles.editAction}
        onPress={() => {
          swipeableRef.current?.close();
          if (onSwipeEdit) {
            onSwipeEdit(item);
          }
        }}
      >
        <Animated.View
          style={[
            styles.editActionContent,
            {
              transform: [{ translateX: trans }],
            },
          ]}
        >
          <Ionicons name="create-outline" size={24} color="#FFFFFF" />
          <Animated.Text style={styles.editActionText}>Edit</Animated.Text>
        </Animated.View>
      </RectButton>
    );
  };

  const renderRightActions = (
    progress: Animated.AnimatedValue,
    dragX: Animated.AnimatedValue
  ) => {
    const trans = dragX.interpolate({
      inputRange: [-100, 0],
      outputRange: [0, 100],
      extrapolate: 'clamp',
    });

    return (
      <RectButton
        style={styles.deleteAction}
        onPress={() => {
          swipeableRef.current?.close();
          if (onDelete) {
            onDelete(item);
          }
        }}
      >
        <Animated.View
          style={[
            styles.deleteActionContent,
            {
              transform: [{ translateX: trans }],
            },
          ]}
        >
          <Ionicons name="trash-outline" size={24} color="#FFFFFF" />
          <Animated.Text style={styles.deleteActionText}>Delete</Animated.Text>
        </Animated.View>
      </RectButton>
    );
  };

  return (
    <Swipeable
      ref={swipeableRef}
      renderLeftActions={renderLeftActions}
      renderRightActions={renderRightActions}
      leftThreshold={40}
      rightThreshold={40}
      friction={1.5}
      overshootLeft={false}
      overshootRight={false}
      onSwipeableWillOpen={(direction) => {
        console.log('Swipeable will open:', direction);
        if (direction === 'left' && onSwipeEdit) {
          // Automatically trigger edit when swiped right (which opens left actions)
          setTimeout(() => {
            swipeableRef.current?.close();
            onSwipeEdit(item);
          }, 100);
        }
      }}
      onSwipeableOpen={(direction) => console.log('Swiped open:', direction)}
      onSwipeableClose={(direction) => console.log('Swiped close:', direction)}
    >
      <Pressable 
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
            backgroundColor: getCategoryBgColor(item.category),
            opacity: item.daysUntilExpiry <= 3 ? 0.9 : 0.7
          }]}>
            <Text style={styles.categoryText}>{item.category}</Text>
          </View>
          <View style={[
            styles.expiryContainer,
            item.daysUntilExpiry <= 0 ? styles.expiredContainer : null,
            item.daysUntilExpiry <= 3 && item.daysUntilExpiry > 0 ? styles.expiringSoonContainer : null
          ]}>
            <Ionicons 
              name="time-outline" 
              size={16} 
              color={
                item.daysUntilExpiry <= 0 ? '#DC2626' :
                item.daysUntilExpiry <= 3 ? '#D97706' : '#6B7280'
              } 
            />
            <Text style={[
              styles.itemExpiry,
              item.daysUntilExpiry <= 0 ? styles.expired : null,
              item.daysUntilExpiry <= 3 ? styles.expiringSoon : null
            ]}>
              {item.expiry}
            </Text>
          </View>
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
      </Pressable>
    </Swipeable>
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
    fontSize: 15,
    color: '#6B7280',
    marginLeft: 4,
    fontWeight: '500',
  },
  expiringSoon: {
    color: '#D97706',
    fontWeight: '600',
  },
  expired: {
    color: '#DC2626',
    fontWeight: '700',
  },
  expiryContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 8,
    backgroundColor: 'rgba(107, 114, 128, 0.08)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  expiringSoonContainer: {
    backgroundColor: 'rgba(217, 119, 6, 0.12)',
  },
  expiredContainer: {
    backgroundColor: 'rgba(220, 38, 38, 0.12)',
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
  deleteAction: {
    backgroundColor: '#DC2626',
    justifyContent: 'center',
    alignItems: 'flex-end',
    marginBottom: 12,
    borderRadius: 12,
    width: 100,
  },
  deleteActionContent: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    flex: 1,
  },
  deleteActionText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
  },
  editAction: {
    backgroundColor: '#297A56',
    justifyContent: 'center',
    alignItems: 'flex-start',
    marginBottom: 12,
    borderRadius: 12,
    width: 100,
  },
  editActionContent: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
    flex: 1,
  },
  editActionText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
  },
});