import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  interpolate,
} from 'react-native-reanimated';

interface SkeletonLoaderProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: ViewStyle;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  width = '100%',
  height = 20,
  borderRadius = 4,
  style,
}) => {
  const opacity = useSharedValue(0.3);

  React.useEffect(() => {
    opacity.value = withRepeat(
      withTiming(1, { duration: 1000 }),
      -1,
      true
    );
  }, [opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <Animated.View
      style={[
        styles.skeleton,
        {
          width,
          height,
          borderRadius,
        },
        animatedStyle,
        style,
      ]}
    />
  );
};

interface RecipeCardSkeletonProps {
  count?: number;
}

export const RecipeCardSkeleton: React.FC<RecipeCardSkeletonProps> = ({ count = 6 }) => {
  return (
    <View style={styles.recipesGrid}>
      {Array.from({ length: count }).map((_, index) => (
        <View key={index} style={styles.recipeCardWrapper}>
          <View style={styles.recipeCardSkeleton}>
            <SkeletonLoader 
              width="100%" 
              height={140}
              borderRadius={12}
              style={styles.imageSkeleton}
            />
            <View style={styles.cardContent}>
              <SkeletonLoader width="90%" height={16} style={{ marginBottom: 8 }} />
              <SkeletonLoader width="60%" height={14} />
            </View>
          </View>
        </View>
      ))}
    </View>
  );
};

interface StatCardSkeletonProps {
  count?: number;
}

export const StatCardSkeleton: React.FC<StatCardSkeletonProps> = ({ count = 4 }) => {
  return (
    <View style={styles.statsGrid}>
      {Array.from({ length: count }).map((_, index) => (
        <View key={index} style={styles.statCardWrapper}>
          <View style={styles.statCardSkeleton}>
            <View style={styles.statCardHeader}>
              <SkeletonLoader width={40} height={40} borderRadius={20} />
              <View style={styles.statCardTitleContainer}>
                <SkeletonLoader width="80%" height={14} style={{ marginBottom: 4 }} />
                <SkeletonLoader width="60%" height={12} />
              </View>
            </View>
            <SkeletonLoader width="50%" height={24} style={{ marginTop: 8 }} />
          </View>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: '#E1E5E9',
  },
  recipesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  recipeCardWrapper: {
    width: '50%',
    paddingHorizontal: 8,
    marginBottom: 16,
  },
  recipeCardSkeleton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  imageSkeleton: {
    marginBottom: 12,
  },
  cardContent: {
    padding: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
  },
  statCardWrapper: {
    width: '48%',
    marginBottom: 16,
  },
  statCardSkeleton: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statCardTitleContainer: {
    flex: 1,
    marginLeft: 12,
  },
});