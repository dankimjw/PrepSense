// app/(tabs)/_layout.tsx - Part of the PrepSense mobile app
import { Tabs } from 'expo-router';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { View, TouchableOpacity, StyleSheet, Text, Platform, Modal, Pressable } from 'react-native';
import React, { useState } from 'react';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { CustomHeader } from '../components/CustomHeader';
import AddButton from '../components/AddButton';

function CustomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  // Filter out the admin, profile, and add tabs from the routes
  const filteredRoutes = state.routes.filter(route => 
    route.name !== 'admin' && route.name !== 'profile' && route.name !== 'add'
  );
  console.log('Tab Routes:', filteredRoutes.map(r => r.name));
  console.log('Current route:', state.routes[state.index].name);

  return (
    <>
      <View style={styles.tabBar}>
        {filteredRoutes.map((route, index) => {
          // Skip rendering the admin tab
          if (route.name === 'admin') return null;
          if (route.name === 'chat') {
            return (
              <TouchableOpacity
                key={route.key}
                accessibilityRole="button"
                style={styles.fabContainer}
                onPress={() => {
                  const router = require('expo-router').router;
                  router.push('/chat-modal');
                }}
              >
                <View style={styles.fab}>
                  <MaterialCommunityIcons name="chef-hat" size={28} color="#fff" />
                </View>
              </TouchableOpacity>
            );
          }
          const { options } = descriptors[route.key];
          const label =
            options.tabBarLabel !== undefined
              ? options.tabBarLabel
              : options.title !== undefined
              ? options.title
              : route.name;
          // Fix the highlighting by checking if the current route matches this tab
          const isFocused = state.routes[state.index].name === route.name;
          let iconName: keyof typeof Ionicons.glyphMap = 'ellipse';
          if (route.name === 'index') iconName = isFocused ? 'home' : 'home-outline';
          if (route.name === 'stats') iconName = isFocused ? 'bar-chart' : 'bar-chart-outline';
          if (route.name === 'recipes') iconName = isFocused ? 'restaurant' : 'restaurant-outline';
          if (route.name === 'shopping-list') iconName = isFocused ? 'cart' : 'cart-outline';
          let labelText = '';
          if (typeof label === 'string') labelText = label;
          else if (typeof label === 'function') labelText = '';
          else labelText = String(label);
          return (
            <TouchableOpacity
              key={route.key}
              accessibilityRole="button"
              accessibilityState={isFocused ? { selected: true } : {}}
              style={styles.tab}
              onPress={() => navigation.navigate(route.name)}
            >
              <Ionicons 
                name={iconName} 
                size={24} 
                color={isFocused ? '#297A56' : '#888'} 
              />
              <Text style={[styles.label, isFocused && { color: '#297A56' }]}>{labelText}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </>
  );
}

// Define the tabs we want to show in the bottom tab bar
const mainTabs = ['index', 'stats', 'chat', 'recipes', 'shopping-list'];

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
                showAIBulkEditButton={true}
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
                showAIBulkEditButton={true}
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
                showAIBulkEditButton={true}
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
            tabBarLabel: '',
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
                showAIBulkEditButton={true}
                showAdminButton={true}
              />
            )
          }} 
        />
        <Tabs.Screen 
          name="shopping-list" 
          options={{ 
            tabBarLabel: 'List',
            header: () => (
              <CustomHeader 
                title="Shopping List"
                showBackButton={false}
                showAIBulkEditButton={true}
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
    height: 72,
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: -2 },
    elevation: 8,
    paddingVertical: 12,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    paddingBottom: 8,
    maxWidth: 80,
    overflow: 'hidden',
  },
  label: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
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