import React, { useEffect } from 'react';
import { TouchableOpacity, TextInput, View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  interpolate,
  runOnJS,
} from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface AnimatedSearchBarProps {
  value: string;
  onChangeText: (text: string) => void;
  onSubmitEditing?: () => void;
  onFocus?: () => void;
  onBlur?: () => void;
  placeholder?: string;
  showSearchButton?: boolean;
  onSearchPress?: () => void;
  onSortPress?: () => void;
  testID?: string;
}

const AnimatedSearchBar: React.FC<AnimatedSearchBarProps> = ({
  value,
  onChangeText,
  onSubmitEditing,
  onFocus,
  onBlur,
  placeholder = "Search recipes...",
  showSearchButton = false,
  onSearchPress,
  onSortPress,
  testID,
}) => {
  const focusProgress = useSharedValue(0);
  const clearButtonScale = useSharedValue(0);
  const searchButtonScale = useSharedValue(showSearchButton ? 1 : 0);

  useEffect(() => {
    clearButtonScale.value = withSpring(value.length > 0 ? 1 : 0, {
      damping: 15,
      stiffness: 300,
    });
  }, [value]);

  useEffect(() => {
    searchButtonScale.value = withSpring(showSearchButton ? 1 : 0, {
      damping: 15,
      stiffness: 300,
    });
  }, [showSearchButton]);

  const animatedContainerStyle = useAnimatedStyle(() => ({
    borderColor: interpolate(
      focusProgress.value,
      [0, 1],
      [0, 1]
    ) === 1 ? '#297A56' : 'transparent',
    backgroundColor: interpolate(
      focusProgress.value,
      [0, 1],
      [0, 1]
    ) === 1 ? '#fff' : '#F3F4F6',
    shadowOpacity: interpolate(focusProgress.value, [0, 1], [0, 0.1]),
    shadowRadius: interpolate(focusProgress.value, [0, 1], [0, 4]),
    elevation: interpolate(focusProgress.value, [0, 1], [0, 2]),
  }));

  const animatedClearStyle = useAnimatedStyle(() => ({
    transform: [{ scale: clearButtonScale.value }],
    opacity: clearButtonScale.value,
  }));

  const animatedSearchButtonStyle = useAnimatedStyle(() => ({
    transform: [{ scale: searchButtonScale.value }],
    opacity: searchButtonScale.value,
  }));

  const handleFocus = () => {
    focusProgress.value = withTiming(1, { duration: 200 });
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
    onFocus?.();
  };

  const handleBlur = () => {
    focusProgress.value = withTiming(0, { duration: 200 });
    onBlur?.();
  };

  const handleClearPress = () => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Light);
    onChangeText('');
  };

  const handleSearchPress = () => {
    runOnJS(Haptics.impactAsync)(Haptics.ImpactFeedbackStyle.Medium);
    onSearchPress?.();
  };

  return (
    <View style={styles.searchContainer} testID={testID}>
      {/* Sort Button */}
      {onSortPress && (
        <TouchableOpacity
          style={styles.sortButton}
          onPress={onSortPress}
          activeOpacity={0.8}
        >
          <Ionicons name="options-outline" size={20} color="#297A56" />
        </TouchableOpacity>
      )}

      <Animated.View style={[styles.searchBar, animatedContainerStyle]}>
        <Ionicons name="search" size={20} color="#666" />
        <TextInput
          style={styles.searchInput}
          placeholder={placeholder}
          placeholderTextColor="#999"
          value={value}
          onChangeText={onChangeText}
          onSubmitEditing={onSubmitEditing}
          onFocus={handleFocus}
          onBlur={handleBlur}
          returnKeyType="search"
        />
        
        {/* Clear Button */}
        <Animated.View style={animatedClearStyle}>
          <TouchableOpacity
            onPress={handleClearPress}
            style={styles.clearButton}
            activeOpacity={0.7}
          >
            <Ionicons name="close-circle" size={20} color="#666" />
          </TouchableOpacity>
        </Animated.View>
      </Animated.View>

      {/* Search Button */}
      <Animated.View style={animatedSearchButtonStyle}>
        <TouchableOpacity
          style={styles.searchButton}
          onPress={handleSearchPress}
          activeOpacity={0.8}
        >
          <Ionicons name="search" size={18} color="#fff" />
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    alignItems: 'center',
    gap: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  sortButton: {
    backgroundColor: '#F3F4F6',
    padding: 10,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 40,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    paddingHorizontal: 16,
    height: 44,
    borderWidth: 1.5,
    borderColor: 'transparent',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0,
    shadowRadius: 4,
  },
  searchInput: {
    flex: 1,
    marginLeft: 12,
    fontSize: 16,
    color: '#333',
  },
  clearButton: {
    padding: 4,
  },
  searchButton: {
    backgroundColor: '#297A56',
    paddingHorizontal: 16,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#297A56',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
});

export default AnimatedSearchBar;