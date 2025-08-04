// app/(tabs)/_layout.tsx - Part of the PrepSense mobile app
import { Tabs } from 'expo-router';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { View, TouchableOpacity, StyleSheet, Text, Platform, Modal, Pressable } from 'react-native';
import React, { useState, useRef, useEffect } from 'react';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
} from 'react-native-reanimated';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { useFocusEffect } from '@react-navigation/native';
import { CustomHeader } from '../components/CustomHeader';
import AddButton from '../components/AddButton';
import * as Haptics from 'expo-haptics';

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

// Animated FAB component for the chat button
function AnimatedFAB({ onPress }: { onPress: () => void }) {
  const scale = useSharedValue(1);
  const rotation = useSharedValue(0);
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value },
      { rotate: `${rotation.value}deg` },
    ],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.9, {
      damping: 15,
      stiffness: 300,
    });
    rotation.value = withSpring(-10, {
      damping: 15,
      stiffness: 300,
    });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1, {
      damping: 15,
      stiffness: 300,
    });
    rotation.value = withSpring(0, {
      damping: 15,
      stiffness: 300,
    });
  };

  return (
    <View style={styles.fabContainer}>
      <AnimatedTouchable
        style={[styles.fab, animatedStyle]}
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        activeOpacity={1}
      >
        <MaterialCommunityIcons name="chef-hat" size={28} color="#fff" />
      </AnimatedTouchable>
    </View>
  );
}

// Tab item component with restored text labels
function TabItem({ route, iconName, isFocused, onPress, label }: {
  route: any;
  iconName: any;
  isFocused: boolean;
  onPress: () => void;
  label: string;
}) {
  const scale = useSharedValue(1);
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.9, {
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

  return (
    <AnimatedTouchable
      accessibilityRole="button"
      accessibilityState={isFocused ? { selected: true } : {}}
      style={[styles.tab, animatedStyle]}
      onPress={onPress}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      activeOpacity={1}
    >
      <Ionicons 
        name={iconName} 
        size={24} 
        color={isFocused ? '#297A56' : '#888'} 
      />
      <Text style={[
        styles.tabLabel,
        { color: isFocused ? '#297A56' : '#888' }
      ]}>
        {label}
      </Text>
    </AnimatedTouchable>
  );
}

function CustomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  // Track current tab index for animations
  const currentTabIndex = useSharedValue(0);
  const previousTabIndex = useRef(0);
  
  // Update animation when tab changes
  useEffect(() => {
    const currentIndex = state.routes.findIndex(r => r.name === state.routes[state.index].name);
    if (currentIndex !== previousTabIndex.current) {
      currentTabIndex.value = withSpring(currentIndex, {
        damping: 20,
        stiffness: 150,
      });
      previousTabIndex.current = currentIndex;
    }
  }, [state.index]);
  
  // Filter out the admin, profile, and add tabs from the routes
  const filteredRoutes = state.routes.filter(route => 
    route.name !== 'admin' && route.name !== 'profile' && route.name !== 'add'
  );
  console.log('Tab Routes:', filteredRoutes.map(r => r.name));
  console.log('Current route:', state.routes[state.index].name);

  // Tab labels mapping
  const getTabLabel = (routeName: string): string => {
    switch (routeName) {
      case 'index': return 'Home';
      case 'stats': return 'Stats';
      case 'recipes': return 'Recipes';
      case 'shopping-list': return 'Shopping List';
      case 'chat': return 'Chat';
      default: return routeName;
    }
  };

  return (
    <>
      <View style={styles.tabBar}>
        {filteredRoutes.map((route, index) => {
          // Skip rendering the admin tab
          if (route.name === 'admin') return null;
          if (route.name === 'chat') {
            return (
              <AnimatedFAB
                key={route.key}
                onPress={() => {
                  const router = require('expo-router').router;
                  router.push('/chat-modal');
                }}
              />
            );
          }
          const { options } = descriptors[route.key];
          // Fix the highlighting by checking if the current route matches this tab
          const isFocused = state.routes[state.index].name === route.name;
          let iconName: keyof typeof Ionicons.glyphMap = 'ellipse';
          if (route.name === 'index') iconName = isFocused ? 'home' : 'home-outline';
          if (route.name === 'stats') iconName = isFocused ? 'bar-chart' : 'bar-chart-outline';
          if (route.name === 'recipes') iconName = isFocused ? 'restaurant' : 'restaurant-outline';
          if (route.name === 'shopping-list') iconName = isFocused ? 'cart' : 'cart-outline';
          
          return (
            <TabItem
              key={route.key}
              route={route}
              iconName={iconName}
              isFocused={isFocused}
              label={getTabLabel(route.name)}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                navigation.navigate(route.name);
              }}
            />
          );
        })}
      </View>
    </>
  );
}

// Define the tabs we want to show in the bottom tab bar
const mainTabs = ['index', 'stats', 'chat', 'recipes', 'shopping-list'];

// Screen wrapper with fade animation
function AnimatedScreen({ children, routeName }: { children: React.ReactNode; routeName: string }) {
  const opacity = useSharedValue(0);
  const translateY = useSharedValue(20);
  
  useFocusEffect(
    React.useCallback(() => {
      // Animate in
      opacity.value = withTiming(1, { duration: 300 });
      translateY.value = withSpring(0, {
        damping: 20,
        stiffness: 150,
      });
      
      return () => {
        // Reset for next time
        opacity.value = 0;
        translateY.value = 20;
      };
    }, [])
  );
  
  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: translateY.value }],
  }));
  
  return (
    <Animated.View style={[{ flex: 1 }, animatedStyle]}>
      {children}
    </Animated.View>
  );
}

export default function TabsLayout() {
  return (
    <>
      <Tabs
        tabBar={props => <CustomTabBar {...props} />}
        screenOptions={{
          header: ({ navigation, route, options }) => {
            // Don't show header for the chat screen as it has its own
            if (route.name === 'chat') return null;
            
            return (
              <CustomHeader 
                title="PrepSense"
                showBackButton={false}
                showAdminButton={true}
              />
            );
          },
          headerShown: true,
          tabBarStyle: { display: 'none' },
        }}
      >
        <Tabs.Screen 
          name="index" 
          options={{ 
            tabBarLabel: 'Home',
            title: 'PrepSense',
            header: () => (
              <CustomHeader 
                title="PrepSense"
                showBackButton={false}
                showAdminButton={true}
              />
            )
          }} 
        />
        <Tabs.Screen 
          name="stats" 
          options={{ 
            tabBarLabel: 'Stats',
            header: () => (
              <CustomHeader 
                title="Statistics"
                showBackButton={false}
                showAdminButton={true}
              />
            )
          }} 
        />
        <Tabs.Screen 
          name="add" 
          options={{ 
            tabBarButton: () => null, // Hide from tab bar
            headerShown: false
          }} 
        />
        <Tabs.Screen 
          name="chat" 
          options={{ 
            tabBarLabel: 'Chat',
            tabBarButton: () => null, // This ensures the tab button is handled by CustomTabBar
            header: () => (
              <CustomHeader 
                title="Chat with Chef"
                showBackButton={true}
                showChatButton={false}
                showAdminButton={false}
              />
            )
          }} 
        />
        <Tabs.Screen 
          name="recipes" 
          options={{ 
            tabBarLabel: 'Recipes',
            header: () => (
              <CustomHeader 
                title="Recipes"
                showBackButton={false}
                showAdminButton={true}
              />
            )
          }} 
        />
        <Tabs.Screen 
          name="shopping-list" 
          options={{ 
            tabBarLabel: 'Shopping List',
            header: () => (
              <CustomHeader 
                title="Shopping List"
                showBackButton={false}
                showAdminButton={true}
              />
            )
          }} 
        />
        <Tabs.Screen 
          name="profile" 
          options={{ 
            tabBarButton: () => null, // This hides the tab from the bottom bar
            header: () => (
              <CustomHeader 
                title="My Profile"
                showBackButton={true}
                showChatButton={false}
                showAdminButton={false}
              />
            )
          }} 
        />
        {/* Admin screen is not included in the tab bar */}
        <Tabs.Screen 
          name="admin" 
          options={{
            tabBarButton: () => null, // This hides the tab bar button
            header: () => (
              <CustomHeader 
                title="Admin Dashboard"
                showBackButton={true}
                showChatButton={false}
                showAdminButton={false}
              />
            )
          }}
        />
      </Tabs>
      <AddButton />
    </>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#eee',
    height: 90, // Increased height to accommodate labels
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: -2 },
    elevation: 8,
    paddingVertical: 8, // Reduced padding since we need space for labels
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    maxWidth: 80,
    overflow: 'hidden',
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '500',
    marginTop: 4,
    textAlign: 'center',
  },
  fabContainer: {
    position: 'relative',
    top: -24,
    zIndex: 10,
    alignItems: 'center',
    justifyContent: 'center',
    width: 64,
    paddingHorizontal: 0,
  },
  fab: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#297A56',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#297A56',
    shadowOpacity: 0.2,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    marginBottom: 90,
    width: 260,
    alignItems: 'stretch',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 12,
  },
  modalBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 10,
    borderRadius: 8,
    marginBottom: 8,
  },
  modalBtnText: {
    fontSize: 16,
    color: '#297A56',
    marginLeft: 12,
    fontWeight: '600',
  },
});