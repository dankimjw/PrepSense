import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  FadeInDown,
  Layout,
  SlideOutLeft,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { Item } from '../../types';

interface AnimatedPantryItemProps {
  item: Item;
  index: number;
  onPress: () => void;
  onDelete: () => void;
}

const AnimatedPantryItem: React.FC<AnimatedPantryItemProps> = ({
  item,
  index,
  onPress,
  onDelete,
}) => {
  const scale = useSharedValue(1);
  const translateX = useSharedValue(0);

  const getDaysUntilExpiry = (expiryDate: string) => {
    const today = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getExpiryColor = (days: number) => {
    if (days <= 0) return '#FF4444';
    if (days <= 3) return '#FF8C00';
    if (days <= 7) return '#FFA500';
    return '#4CAF50';
  };

  const daysUntilExpiry = getDaysUntilExpiry(item.expiry_date);
  const expiryColor = getExpiryColor(daysUntilExpiry);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value },
      { translateX: translateX.value },
    ],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.98, {
      damping: 15,
      stiffness: 300,
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 15,
      stiffness: 300,
    });
  };

  const handleSwipeLeft = () => {
    translateX.value = withTiming(-100, { duration: 200 });
  };

  const handleSwipeRight = () => {
    translateX.value = withTiming(0, { duration: 200 });
  };

  return (
    <Animated.View
      entering={FadeInDown.delay(index * 50).springify()}
      exiting={SlideOutLeft}
      layout={Layout.springify()}
      style={[animatedStyle]}
    >
      <TouchableOpacity
        style={styles.container}
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        activeOpacity={1}
      >
        <View style={styles.content}>
          <View style={styles.leftContent}>
            <Text style={styles.name}>{item.name}</Text>
            <Text style={styles.quantity}>
              {item.quantity} {item.unit}
            </Text>
          </View>
          <View style={styles.rightContent}>
            <View style={[styles.expiryBadge, { backgroundColor: expiryColor }]}>
              <Text style={styles.expiryText}>
                {daysUntilExpiry <= 0 
                  ? 'Expired' 
                  : `${daysUntilExpiry}d`}
              </Text>
            </View>
            <TouchableOpacity onPress={onDelete} style={styles.deleteButton}>
              <Ionicons name="trash-outline" size={20} color="#FF4444" />
            </TouchableOpacity>
          </View>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginVertical: 4,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  content: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  leftContent: {
    flex: 1,
  },
  rightContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  quantity: {
    fontSize: 14,
    color: '#666',
  },
  expiryBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginRight: 8,
  },
  expiryText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  deleteButton: {
    padding: 8,
  },
});

export default AnimatedPantryItem;