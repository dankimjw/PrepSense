// app/(tabs)/stats.tsx - Part of the PrepSense mobile app
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, RefreshControl, Dimensions, TouchableOpacity, Modal, FlatList, Pressable } from 'react-native';
import { MaterialCommunityIcons, Ionicons, FontAwesome5 } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { fetchPantryItems } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from '../../context/AuthContext';
import { LineChart, BarChart } from 'react-native-chart-kit';
import { Config } from '../../config';

const { width: screenWidth } = Dimensions.get('window');

interface StatsData {
  pantry: {
    totalItems: number;
    expiredItems: number;
    expiringItems: number;
    recentlyAdded: number;
    topProducts: { name: string; count: number }[];
    foodSavedKg: number;
    co2SavedKg: number;
  };
  recipes: {
    cookedThisWeek: number;
    cookedThisMonth: number;
    totalCooked: number;
    favoriteRecipes: { name: string; count: number }[];
    cookingStreak: number;
  };
}

interface PantryItem {
  pantry_item_id: string;
  product_name: string;
  quantity: number;
  unit_of_measurement: string;
  expiration_date: string | null;
  created_at: string;
  updated_at: string;
  category: string;
}

export default function StatsScreen() {
  const { token, isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('week');
  const [recipes, setRecipes] = useState<any[]>([]);
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalTitle, setModalTitle] = useState('');
  const [modalItems, setModalItems] = useState<PantryItem[]>([]);

  useEffect(() => {
    loadStats();
  }, [timeRange]); // Reload stats when time range changes

  const loadStats = async () => {
    try {
      setIsLoading(true);
      
      // Fetch pantry items
      const fetchedPantryItems = await fetchPantryItems(111); // Demo user ID
      setPantryItems(fetchedPantryItems); // Store for modal use
      
      // Fetch user recipes
      let fetchedRecipes = [];
      try {
        if (token && isAuthenticated) {
          const response = await fetch(`${Config.API_BASE_URL}/user-recipes`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (response.ok) {
            const data = await response.json();
            fetchedRecipes = data.recipes || [];
          }
        }
      } catch (error) {
        console.error('Error fetching user recipes:', error);
        // Continue with empty recipes array
      }
      
      setRecipes(fetchedRecipes); // Store recipes in state for chart generation
      
      // Get shopping list data from AsyncStorage
      const shoppingListData = await AsyncStorage.getItem('@PrepSense_ShoppingList');
      const shoppingList = shoppingListData ? JSON.parse(shoppingListData) : [];
      
      // Calculate stats based on selected time range
      const now = new Date();
      const oneWeekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      
      // Adjust time ago based on selected period
      let timeAgo;
      let daysAgo;
      if (timeRange === 'week') {
        timeAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        daysAgo = 7;
      } else if (timeRange === 'month') {
        timeAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        daysAgo = 30;
      } else { // year
        timeAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        daysAgo = 365;
      }
      
      // Pantry stats
      const expiredItems = fetchedPantryItems.filter(item => {
        if (!item.expiration_date) return false;
        const expDate = new Date(item.expiration_date);
        return expDate < now;
      }).length;
      
      const expiringItems = fetchedPantryItems.filter(item => {
        if (!item.expiration_date) return false;
        const expDate = new Date(item.expiration_date);
        return expDate <= oneWeekFromNow && expDate >= now;
      }).length;
      
      const recentlyAdded = fetchedPantryItems.filter(item => {
        const addedDate = new Date(item.created_at || item.updated_at);
        return addedDate >= timeAgo;
      }).length;
      
      // Calculate top products by frequency
      const productCounts: { [key: string]: number } = {};
      const recentItems = fetchedPantryItems.filter(item => {
        const addedDate = new Date(item.created_at || item.updated_at);
        return addedDate >= timeAgo;
      });
      
      recentItems.forEach(item => {
        const name = item.product_name || 'Unknown';
        productCounts[name] = (productCounts[name] || 0) + 1;
      });
      
      const topProducts = Object.entries(productCounts)
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 5);
      
      // Calculate environmental impact
      const unexpiredItems = fetchedPantryItems.filter(item => {
        if (!item.expiration_date) return true;
        const expDate = new Date(item.expiration_date);
        return expDate >= now;
      }).length;
      
      const foodSavedKg = Math.round(unexpiredItems * 0.3 * 10) / 10; // 0.3kg average per item
      const co2SavedKg = Math.round(foodSavedKg * 2.5 * 10) / 10; // 2.5kg CO2 per kg food
      
      // Recipe stats
      const cookedThisWeek = fetchedRecipes.filter(recipe => {
        const cookedDate = new Date(recipe.created_at);
        return cookedDate >= new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      }).length;
      
      const cookedThisMonth = fetchedRecipes.filter(recipe => {
        const cookedDate = new Date(recipe.created_at);
        return cookedDate >= new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      }).length;
      
      // Calculate favorite recipes
      const recipeCounts: { [key: string]: number } = {};
      fetchedRecipes.forEach(recipe => {
        const title = recipe.recipe_title || 'Unknown Recipe';
        recipeCounts[title] = (recipeCounts[title] || 0) + 1;
      });
      
      const favoriteRecipes = Object.entries(recipeCounts)
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 5);
      
      // Prepare stats data with real values
      const statsData: StatsData = {
        pantry: {
          totalItems: fetchedPantryItems.length,
          expiredItems,
          expiringItems,
          recentlyAdded,
          topProducts,
          foodSavedKg,
          co2SavedKg,
        },
        recipes: {
          cookedThisWeek,
          cookedThisMonth,
          totalCooked: fetchedRecipes.length,
          favoriteRecipes,
          cookingStreak: calculateCookingStreak(fetchedRecipes),
        },
      };
      
      setStats(statsData);
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  const calculateCookingStreak = (recipes: any[]): number => {
    if (recipes.length === 0) return 0;
    
    const sortedRecipes = [...recipes].sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
    
    let streak = 0;
    let currentDate = new Date();
    currentDate.setHours(0, 0, 0, 0);
    
    for (const recipe of sortedRecipes) {
      const recipeDate = new Date(recipe.created_at);
      recipeDate.setHours(0, 0, 0, 0);
      
      const dayDiff = Math.floor((currentDate.getTime() - recipeDate.getTime()) / (1000 * 60 * 60 * 24));
      
      if (dayDiff === streak) {
        streak++;
      } else if (dayDiff > streak) {
        break;
      }
    }
    
    return streak;
  };

  const calculateMilestones = (recipeCount: number, pantryCount: number): string[] => {
    const milestones = [];
    
    if (recipeCount >= 1) milestones.push('First Recipe! 🎉');
    if (recipeCount >= 10) milestones.push('10 Recipes Cooked 🍳');
    if (recipeCount >= 50) milestones.push('Master Chef 👨‍🍳');
    if (pantryCount >= 20) milestones.push('Well-Stocked Pantry 🏪');
    if (pantryCount >= 50) milestones.push('Pantry Pro 📦');
    
    return milestones;
  };

  const showItemsModal = (title: string, filterType: 'expired' | 'expiring' | 'recent' | 'all') => {
    setModalTitle(title);
    
    const now = new Date();
    const oneWeekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    let timeAgo;
    
    if (timeRange === 'week') {
      timeAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    } else if (timeRange === 'month') {
      timeAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    } else {
      timeAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
    }
    
    let filteredItems: PantryItem[] = [];
    
    switch (filterType) {
      case 'all':
        // Sort all items by expiration date (expired first, then expiring soon, then others)
        filteredItems = [...pantryItems].sort((a, b) => {
          if (!a.expiration_date && !b.expiration_date) return 0;
          if (!a.expiration_date) return 1;
          if (!b.expiration_date) return -1;
          
          const dateA = new Date(a.expiration_date).getTime();
          const dateB = new Date(b.expiration_date).getTime();
          const nowTime = now.getTime();
          
          // If both expired, show most recently expired first
          if (dateA < nowTime && dateB < nowTime) {
            return dateB - dateA;
          }
          // If one is expired, show it first
          if (dateA < nowTime) return -1;
          if (dateB < nowTime) return 1;
          // Otherwise sort by expiration date (soonest first)
          return dateA - dateB;
        });
        break;
      case 'expired':
        filteredItems = pantryItems.filter(item => {
          if (!item.expiration_date) return false;
          const expDate = new Date(item.expiration_date);
          return expDate < now;
        });
        break;
      case 'expiring':
        filteredItems = pantryItems.filter(item => {
          if (!item.expiration_date) return false;
          const expDate = new Date(item.expiration_date);
          return expDate <= oneWeekFromNow && expDate >= now;
        });
        break;
      case 'recent':
        filteredItems = pantryItems.filter(item => {
          const addedDate = new Date(item.created_at || item.updated_at);
          return addedDate >= timeAgo;
        });
        break;
    }
    
    setModalItems(filteredItems);
    setModalVisible(true);
  };

  const getDaysUntilExpiration = (expirationDate: string | null) => {
    if (!expirationDate) return null;
    const now = new Date();
    const expDate = new Date(expirationDate);
    const diffTime = expDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const renderStatCard = (
    title: string, 
    value: string | number, 
    icon: any, 
    color: string, 
    subtitle?: string, 
    trend?: { value: number; isPositive: boolean },
    onPress?: () => void
  ) => {
    const CardContent = (
      <>
        <View style={styles.statCardHeader}>
          <View style={[styles.iconContainer, { backgroundColor: color + '20' }]}>
            {icon}
          </View>
          <View style={styles.statCardTitleContainer}>
            <Text style={styles.statCardTitle}>{title}</Text>
            {trend && (
              <View style={styles.trendContainer}>
                <Ionicons 
                  name={trend.isPositive ? "trending-up" : "trending-down"} 
                  size={16} 
                  color={trend.isPositive ? "#10B981" : "#EF4444"} 
                />
                <Text style={[styles.trendText, { color: trend.isPositive ? "#10B981" : "#EF4444" }]}>
                  {trend.value}%
                </Text>
              </View>
            )}
          </View>
        </View>
        <Text style={[styles.statCardValue, { color }]}>{value}</Text>
        {subtitle && <Text style={styles.statCardSubtitle}>{subtitle}</Text>}
        {onPress && (
          <View style={styles.tapIndicator}>
            <Text style={styles.tapText}>Tap to see items</Text>
          </View>
        )}
      </>
    );

    if (onPress) {
      return (
        <TouchableOpacity 
          style={[styles.statCard, { borderLeftColor: color }]}
          onPress={onPress}
          activeOpacity={0.7}
        >
          {CardContent}
        </TouchableOpacity>
      );
    }

    return (
      <View style={[styles.statCard, { borderLeftColor: color }]}>
        {CardContent}
      </View>
    );
  };

  const renderMiniStat = (label: string, value: string | number, color: string) => (
    <View style={styles.miniStat}>
      <Text style={styles.miniStatLabel}>{label}</Text>
      <Text style={[styles.miniStatValue, { color }]}>{value}</Text>
    </View>
  );

  const renderAchievement = (achievement: string, index: number) => (
    <View key={index} style={styles.achievementBadge}>
      <Text style={styles.achievementText}>{achievement}</Text>
    </View>
  );

  const onRefresh = () => {
    setRefreshing(true);
    loadStats();
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#297A56" />
        <Text style={styles.loadingText}>Loading your stats...</Text>
      </View>
    );
  }

  if (!stats) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle" size={64} color="#DC2626" />
        <Text style={styles.errorText}>Failed to load stats</Text>
      </View>
    );
  }

  // Generate cooking frequency data based on time range
  const generateCookingFrequencyData = () => {
    const now = new Date();
    const labels: string[] = [];
    const data: number[] = [];
    
    if (timeRange === 'week') {
      // Last 7 days
      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      for (let i = 6; i >= 0; i--) {
        const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
        labels.push(dayNames[date.getDay()]);
        
        // Count recipes cooked on this day
        const dayStart = new Date(date);
        dayStart.setHours(0, 0, 0, 0);
        const dayEnd = new Date(date);
        dayEnd.setHours(23, 59, 59, 999);
        
        const count = stats?.recipes.totalCooked ? 
          recipes.filter(recipe => {
            const cookedDate = new Date(recipe.created_at);
            return cookedDate >= dayStart && cookedDate <= dayEnd;
          }).length : 0;
        
        data.push(count);
      }
    } else if (timeRange === 'month') {
      // Last 4 weeks
      for (let i = 3; i >= 0; i--) {
        const weekStart = new Date(now.getTime() - (i * 7 + 6) * 24 * 60 * 60 * 1000);
        const weekEnd = new Date(now.getTime() - i * 7 * 24 * 60 * 60 * 1000);
        labels.push(`Week ${4-i}`);
        
        const count = stats?.recipes.totalCooked ? 
          recipes.filter(recipe => {
            const cookedDate = new Date(recipe.created_at);
            return cookedDate >= weekStart && cookedDate <= weekEnd;
          }).length : 0;
        
        data.push(count);
      }
    } else { // year
      // Last 12 months
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      for (let i = 11; i >= 0; i--) {
        const monthDate = new Date(now.getFullYear(), now.getMonth() - i, 1);
        labels.push(monthNames[monthDate.getMonth()]);
        
        const monthStart = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
        const monthEnd = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
        
        const count = stats?.recipes.totalCooked ? 
          recipes.filter(recipe => {
            const cookedDate = new Date(recipe.created_at);
            return cookedDate >= monthStart && cookedDate <= monthEnd;
          }).length : 0;
        
        data.push(count);
      }
    }
    
    return {
      labels,
      datasets: [{
        data: data.length > 0 ? data : [0, 0, 0, 0, 0, 0, 0],
      }],
    };
  };

  const cookingFrequencyData = generateCookingFrequencyData();

  return (
    <ScrollView 
      style={styles.container}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor="#297A56"
        />
      }
    >
      {/* Header with gradient */}
      <LinearGradient
        colors={['#297A56', '#1F5A40']}
        style={styles.headerGradient}
      >
        <Text style={styles.headerTitle}>Your PrepSense Stats</Text>
        <Text style={styles.headerSubtitle}>Track your meal prep journey</Text>
        
        {/* Time Period Tabs */}
        <View style={styles.periodTabs}>
          <TouchableOpacity 
            style={[styles.periodTab, timeRange === 'week' && styles.periodTabActive]}
            onPress={() => setTimeRange('week')}
          >
            <Text style={[styles.periodTabText, timeRange === 'week' && styles.periodTabTextActive]}>
              Week
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.periodTab, timeRange === 'month' && styles.periodTabActive]}
            onPress={() => setTimeRange('month')}
          >
            <Text style={[styles.periodTabText, timeRange === 'month' && styles.periodTabTextActive]}>
              Month
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.periodTab, timeRange === 'year' && styles.periodTabActive]}
            onPress={() => setTimeRange('year')}
          >
            <Text style={[styles.periodTabText, timeRange === 'year' && styles.periodTabTextActive]}>
              Year
            </Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      {/* Quick Stats Overview */}
      <View style={styles.quickStatsContainer}>
        {renderMiniStat('Total Items', stats.pantry.totalItems, '#297A56')}
        {renderMiniStat('Recipes Made', stats.recipes.totalCooked, '#3B82F6')}
        {renderMiniStat('Streak', `${stats.recipes.cookingStreak}d`, '#F59E0B')}
        {renderMiniStat('CO₂ Saved', `${stats.pantry.co2SavedKg}kg`, '#10B981')}
      </View>

      {/* Hot This Week Section */}
      <View style={styles.hotThisWeekContainer}>
        <LinearGradient
          colors={['#F59E0B', '#EF4444']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.hotThisWeekGradient}
        >
          <View style={styles.hotThisWeekContent}>
            <View>
              <Text style={styles.hotThisWeekTitle}>🔥 Hot This Week!</Text>
              <Text style={styles.hotThisWeekSubtitle}>You've cooked {stats.recipes.cookedThisWeek} recipes</Text>
            </View>
            <View style={styles.hotThisWeekBadge}>
              <Text style={styles.hotThisWeekBadgeText}>{stats.pantry.foodSavedKg}kg saved</Text>
            </View>
          </View>
        </LinearGradient>
      </View>

      {/* Pantry Analytics Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🏪 Pantry Analytics</Text>
        <View style={styles.statsGrid}>
          {renderStatCard(
            'Total Items',
            stats.pantry.totalItems,
            <MaterialCommunityIcons name="package-variant" size={24} color="#297A56" />,
            '#297A56',
            undefined,
            undefined,
            () => showItemsModal('All Pantry Items', 'all')
          )}
          {renderStatCard(
            'Expired Items',
            stats.pantry.expiredItems,
            <Ionicons name="alert-circle" size={24} color="#DC2626" />,
            '#DC2626',
            stats.pantry.expiredItems === 0 ? '🥳 Great job!' : 'Need attention',
            undefined,
            stats.pantry.expiredItems > 0 ? () => showItemsModal('Expired Items', 'expired') : undefined
          )}
          {renderStatCard(
            'Expiring Soon',
            stats.pantry.expiringItems,
            <Ionicons name="warning" size={24} color="#F59E0B" />,
            '#F59E0B',
            'Next 7 days',
            undefined,
            stats.pantry.expiringItems > 0 ? () => showItemsModal('Expiring Soon', 'expiring') : undefined
          )}
          {renderStatCard(
            'Recently Added',
            stats.pantry.recentlyAdded,
            <Ionicons name="add-circle" size={24} color="#3B82F6" />,
            '#3B82F6',
            timeRange === 'week' ? 'Last 7 days' : timeRange === 'month' ? 'Last 30 days' : 'Last year',
            undefined,
            stats.pantry.recentlyAdded > 0 ? () => showItemsModal('Recently Added', 'recent') : undefined
          )}
        </View>

        {/* Environmental Impact */}
        <View style={styles.impactSection}>
          <Text style={styles.subSectionTitle}>♻️ Environmental Impact</Text>
          <View style={styles.impactGrid}>
            <View style={styles.impactCard}>
              <MaterialCommunityIcons name="food-apple" size={32} color="#10B981" />
              <Text style={styles.impactValue}>{stats.pantry.foodSavedKg} kg</Text>
              <Text style={styles.impactLabel}>Food Saved</Text>
            </View>
            <View style={styles.impactCard}>
              <MaterialCommunityIcons name="leaf" size={32} color="#10B981" />
              <Text style={styles.impactValue}>{stats.pantry.co2SavedKg} kg</Text>
              <Text style={styles.impactLabel}>CO₂ Saved</Text>
            </View>
          </View>
        </View>

        {/* Top Products */}
        {stats.pantry.topProducts.length > 0 && (
          <View style={styles.subSection}>
            <Text style={styles.subSectionTitle}>🎵 Pantry Top Hits {timeRange === 'week' ? 'This Week' : timeRange === 'month' ? 'This Month' : 'This Year'}</Text>
            {stats.pantry.topProducts.map((item, index) => {
              const emojis = ['🥇', '🥈', '🥉', '🔥', '💥'];
              return (
                <View key={index} style={styles.listItem}>
                  <Text style={styles.listItemName}>
                    {emojis[index] || `#${index + 1}`} {item.name}
                  </Text>
                  <View style={styles.listItemRight}>
                    <Text style={styles.listItemCount}>{item.count} times</Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </View>

      {/* Recipe & Cooking Stats Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>👨‍🍳 Recipe & Cooking Stats</Text>
        <View style={styles.statsGrid}>
          {renderStatCard(
            'This Week',
            stats.recipes.cookedThisWeek,
            <Ionicons name="calendar" size={24} color="#3B82F6" />,
            '#3B82F6',
            'Recipes cooked'
          )}
          {renderStatCard(
            'This Month',
            stats.recipes.cookedThisMonth,
            <Ionicons name="calendar-outline" size={24} color="#8B5CF6" />,
            '#8B5CF6',
            'Recipes cooked'
          )}
          {renderStatCard(
            'Total Recipes',
            stats.recipes.totalCooked,
            <MaterialCommunityIcons name="chef-hat" size={24} color="#10B981" />,
            '#10B981',
            'All time'
          )}
          {renderStatCard(
            'Cooking Streak',
            `${stats.recipes.cookingStreak} days`,
            <Ionicons name="flame" size={24} color="#F59E0B" />,
            '#F59E0B'
          )}
        </View>

        {/* Favorite Recipes */}
        {stats.recipes.favoriteRecipes.length > 0 && (
          <View style={styles.subSection}>
            <View style={styles.subSectionHeader}>
              <Text style={styles.subSectionTitle}>Top Recipes</Text>
              <TouchableOpacity>
                <Text style={styles.seeMoreText}>See More ›</Text>
              </TouchableOpacity>
            </View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.recipeCardsScroll}>
              {stats.recipes.favoriteRecipes.map((recipe, index) => (
                <TouchableOpacity key={index} style={styles.recipeCard}>
                  <View style={styles.recipeImageContainer}>
                    <LinearGradient
                      colors={['#297A56', '#1F5A40']}
                      style={styles.recipeImagePlaceholder}
                    >
                      <Ionicons name="restaurant" size={40} color="#fff" />
                    </LinearGradient>
                    <TouchableOpacity style={styles.bookmarkButton}>
                      <Ionicons name="bookmark" size={20} color="#F59E0B" />
                    </TouchableOpacity>
                  </View>
                  <View style={styles.recipeCardContent}>
                    <Text style={styles.recipeCardTitle} numberOfLines={2}>{recipe.name}</Text>
                    <View style={styles.recipeCardStats}>
                      <View style={styles.recipeCardStat}>
                        <Ionicons name="time-outline" size={14} color="#666" />
                        <Text style={styles.recipeCardStatText}>35 min</Text>
                      </View>
                      <View style={styles.recipeCardStat}>
                        <Ionicons name="flame-outline" size={14} color="#666" />
                        <Text style={styles.recipeCardStatText}>{recipe.count}x</Text>
                      </View>
                    </View>
                  </View>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

      </View>

      {/* Time-based Trends */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📊 Cooking Trends</Text>
        <Text style={styles.chartTitle}>
          {timeRange === 'week' ? 'Daily' : timeRange === 'month' ? 'Weekly' : 'Monthly'} Cooking Frequency
        </Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <LineChart
            data={cookingFrequencyData}
            width={screenWidth - 40}
            height={200}
            yAxisSuffix={timeRange === 'week' ? '' : ''}
            chartConfig={{
              backgroundColor: '#ffffff',
              backgroundGradientFrom: '#ffffff',
              backgroundGradientTo: '#ffffff',
              decimalPlaces: 0,
              color: (opacity = 1) => `rgba(41, 122, 86, ${opacity})`,
              labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              style: {
                borderRadius: 16,
              },
              propsForDots: {
                r: '6',
                strokeWidth: '2',
                stroke: '#297A56',
              },
            }}
            bezier
            style={styles.chart}
          />
        </ScrollView>
      </View>

      {/* Modal for showing item details */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{modalTitle}</Text>
              <TouchableOpacity
                onPress={() => setModalVisible(false)}
                style={styles.modalCloseButton}
              >
                <Ionicons name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>
            
            {modalItems.length === 0 ? (
              <View style={styles.emptyModalContent}>
                <Text style={styles.emptyModalText}>No items to display</Text>
              </View>
            ) : (
              <>
                {modalTitle === 'All Pantry Items' && (
                  <View style={styles.modalSummary}>
                    <View style={styles.modalSummaryRow}>
                      <View style={styles.modalSummaryItem}>
                        <Text style={styles.modalSummaryValue}>{stats?.pantry.totalItems || 0}</Text>
                        <Text style={styles.modalSummaryLabel}>Total Items</Text>
                      </View>
                      <View style={styles.modalSummaryItem}>
                        <Text style={[styles.modalSummaryValue, { color: '#DC2626' }]}>{stats?.pantry.expiredItems || 0}</Text>
                        <Text style={styles.modalSummaryLabel}>Expired</Text>
                      </View>
                      <View style={styles.modalSummaryItem}>
                        <Text style={[styles.modalSummaryValue, { color: '#F59E0B' }]}>{stats?.pantry.expiringItems || 0}</Text>
                        <Text style={styles.modalSummaryLabel}>Expiring Soon</Text>
                      </View>
                    </View>
                  </View>
                )}
                
                <FlatList
                  data={modalItems}
                  keyExtractor={(item) => item.pantry_item_id}
                  renderItem={({ item }) => {
                  const daysUntilExp = getDaysUntilExpiration(item.expiration_date);
                  const isExpired = daysUntilExp !== null && daysUntilExp < 0;
                  const isExpiringSoon = daysUntilExp !== null && daysUntilExp <= 7 && daysUntilExp >= 0;
                  
                  return (
                    <View style={styles.modalItem}>
                      <View style={styles.modalItemHeader}>
                        <Text style={styles.modalItemName}>{item.product_name}</Text>
                        <Text style={styles.modalItemQuantity}>
                          {item.quantity} {item.unit_of_measurement}
                        </Text>
                      </View>
                      
                      <View style={styles.modalItemDetails}>
                        {item.category && (
                          <Text style={styles.modalItemCategory}>{item.category}</Text>
                        )}
                        
                        {item.expiration_date && (
                          <View style={styles.modalItemExpiration}>
                            <Text style={[
                              styles.modalItemExpirationText,
                              isExpired && styles.modalItemExpired,
                              isExpiringSoon && styles.modalItemExpiringSoon
                            ]}>
                              {isExpired 
                                ? `Expired ${Math.abs(daysUntilExp)} days ago`
                                : isExpiringSoon
                                ? `Expires in ${daysUntilExp} day${daysUntilExp !== 1 ? 's' : ''}`
                                : `Expires: ${formatDate(item.expiration_date)}`
                              }
                            </Text>
                          </View>
                        )}
                        
                        {(modalTitle === 'Recently Added' || modalTitle === 'All Pantry Items') && (
                          <Text style={styles.modalItemAdded}>
                            Added: {formatDate(item.created_at || item.updated_at)}
                          </Text>
                        )}
                      </View>
                    </View>
                  );
                  }}
                  style={styles.modalList}
                  showsVerticalScrollIndicator={false}
                />
              </>
            )}
          </View>
        </View>
      </Modal>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  errorText: {
    marginTop: 16,
    fontSize: 18,
    color: '#DC2626',
    fontWeight: '600',
  },
  headerGradient: {
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: 20,
    marginBottom: -20,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#E6F4EA',
    opacity: 0.9,
  },
  quickStatsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 20,
    paddingVertical: 20,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  miniStat: {
    alignItems: 'center',
  },
  miniStatLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  miniStatValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  section: {
    marginHorizontal: 20,
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  statCardTitle: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  statCardTitleContainer: {
    flex: 1,
    marginRight: 8,
  },
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  trendText: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  statCardValue: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statCardSubtitle: {
    fontSize: 12,
    color: '#999',
  },
  subSection: {
    marginTop: 20,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  subSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 12,
  },
  listItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  listItemName: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  listItemRight: {
    alignItems: 'flex-end',
  },
  listItemCount: {
    fontSize: 14,
    color: '#666',
    fontWeight: '600',
    marginBottom: 4,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#297A56',
    borderRadius: 2,
    minWidth: 50,
  },
  nutritionGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 8,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
    marginLeft: 4,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  scoresContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  scoreCard: {
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  scoreLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
    fontWeight: '500',
  },
  scoreCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#E6F4EA',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#297A56',
    flexDirection: 'row',
  },
  scoreValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#297A56',
  },
  scorePercent: {
    fontSize: 16,
    color: '#297A56',
    fontWeight: '600',
  },
  achievementsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  achievementBadge: {
    backgroundColor: '#F59E0B',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    marginBottom: 8,
  },
  achievementText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  periodTabs: {
    flexDirection: 'row',
    marginTop: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 25,
    padding: 4,
    alignSelf: 'center',
  },
  periodTab: {
    paddingHorizontal: 24,
    paddingVertical: 8,
    borderRadius: 20,
    marginHorizontal: 4,
  },
  periodTabActive: {
    backgroundColor: '#fff',
  },
  periodTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.7)',
  },
  periodTabTextActive: {
    color: '#297A56',
  },
  subSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  seeMoreText: {
    fontSize: 14,
    color: '#297A56',
    fontWeight: '600',
  },
  recipeCardsScroll: {
    marginHorizontal: -16,
    paddingHorizontal: 16,
  },
  recipeCard: {
    width: 160,
    marginRight: 12,
    backgroundColor: '#fff',
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  recipeImageContainer: {
    position: 'relative',
    height: 120,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    overflow: 'hidden',
  },
  recipeImagePlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  bookmarkButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recipeCardContent: {
    padding: 12,
  },
  recipeCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  recipeCardStats: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  recipeCardStat: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  recipeCardStatText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  hotThisWeekContainer: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
  hotThisWeekGradient: {
    borderRadius: 16,
    padding: 20,
  },
  hotThisWeekContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  hotThisWeekTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  hotThisWeekSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  hotThisWeekBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  hotThisWeekBadgeText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  impactSection: {
    marginTop: 20,
    padding: 16,
    backgroundColor: '#E6F4EA',
    borderRadius: 12,
  },
  impactGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 12,
  },
  impactCard: {
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    flex: 0.45,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  impactValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#10B981',
    marginVertical: 8,
  },
  impactLabel: {
    fontSize: 14,
    color: '#666',
  },
  tapIndicator: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  tapText: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
    paddingBottom: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  modalCloseButton: {
    padding: 4,
  },
  modalList: {
    paddingHorizontal: 20,
    paddingTop: 10,
  },
  modalItem: {
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e5e5e5',
  },
  modalItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  modalItemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    flex: 1,
  },
  modalItemQuantity: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  modalItemDetails: {
    gap: 4,
  },
  modalItemCategory: {
    fontSize: 12,
    color: '#666',
    backgroundColor: '#e5e5e5',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  modalItemExpiration: {
    marginTop: 4,
  },
  modalItemExpirationText: {
    fontSize: 13,
    color: '#666',
  },
  modalItemExpired: {
    color: '#DC2626',
    fontWeight: '600',
  },
  modalItemExpiringSoon: {
    color: '#F59E0B',
    fontWeight: '600',
  },
  modalItemAdded: {
    fontSize: 13,
    color: '#666',
    marginTop: 4,
  },
  emptyModalContent: {
    padding: 40,
    alignItems: 'center',
  },
  emptyModalText: {
    fontSize: 16,
    color: '#999',
  },
  modalSummary: {
    padding: 20,
    backgroundColor: '#f5f5f5',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5e5',
  },
  modalSummaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  modalSummaryItem: {
    alignItems: 'center',
  },
  modalSummaryValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  modalSummaryLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
});