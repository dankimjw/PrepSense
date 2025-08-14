import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity } from 'react-native';

type RecipeBasic = {
  id: number;
  title: string;
  image?: string;
  readyInMinutes?: number;
  servings?: number;
  usedIngredientCount?: number;
  missedIngredientCount?: number;
  matchPercentage?: number;
};

interface RecipeCardProps {
  recipe: RecipeBasic;
  onPress: (recipe: RecipeBasic) => void;
}

const FALLBACK_IMAGE = 'https://img.spoonacular.com/recipes/default-312x231.jpg';

export default function RecipeCard({ recipe, onPress }: RecipeCardProps) {
  const imageUrl = recipe.image && recipe.image.startsWith('http') ? recipe.image : FALLBACK_IMAGE;

  const showCounts =
    typeof recipe.usedIngredientCount === 'number' &&
    typeof recipe.missedIngredientCount === 'number';

  const showMeta = typeof recipe.readyInMinutes === 'number' || typeof recipe.servings === 'number';

  const matchBadgeColor = (() => {
    const p = recipe.matchPercentage ?? -1;
    if (p >= 80) return '#4CAF50'; // green
    if (p >= 30) return '#FF9800'; // orange
    if (p >= 0) return '#9E9E9E'; // grey
    return 'transparent';
  })();

  return (
    <TouchableOpacity
      testID={`recipe-card-${recipe.id}`}
      style={styles.card}
      activeOpacity={0.85}
      onPress={() => onPress(recipe)}
    >
      <Image source={{ uri: imageUrl }} style={styles.image} resizeMode="cover" />
      <View style={styles.content}>
        <Text numberOfLines={2} style={styles.title}>
          {recipe.title}
        </Text>

        {showCounts && (
          <Text testID="ingredient-counts" style={styles.counts}>
            {`✓ ${recipe.usedIngredientCount} | ✗ ${recipe.missedIngredientCount}`}
          </Text>
        )}

        {showMeta && (
          <View style={styles.metaRow}>
            {typeof recipe.readyInMinutes === 'number' && (
              <Text style={styles.metaText}>{`${recipe.readyInMinutes} min`}</Text>
            )}
            {typeof recipe.servings === 'number' && (
              <Text style={styles.metaText}>{`${recipe.servings} servings`}</Text>
            )}
          </View>
        )}

        {typeof recipe.matchPercentage === 'number' && (
          <View testID="match-percentage-badge" style={[styles.badge, { backgroundColor: matchBadgeColor }]}>
            <Text style={styles.badgeText}>{`${recipe.matchPercentage}%`}</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  image: {
    width: '100%',
    height: 180,
    backgroundColor: '#EEE',
  },
  content: {
    padding: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#222',
    marginBottom: 6,
  },
  counts: {
    fontSize: 13,
    color: '#444',
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 6,
  },
  metaText: {
    fontSize: 12,
    color: '#666',
  },
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginTop: 4,
  },
  badgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
});



