import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, TouchableOpacity, StyleSheet, Text, Platform, Modal, Pressable, Alert } from 'react-native';
import React, { useState } from 'react';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { CustomHeader } from '../components/CustomHeader';

function CustomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const [modalVisible, setModalVisible] = useState(false);
  
  // Filter out the admin tab from the routes
  const filteredRoutes = state.routes.filter(route => route.name !== 'admin');
  console.log('Tab Routes:', filteredRoutes.map(r => r.name));

  const handleAddImage = () => {
    setModalVisible(false);
    navigation.navigate('upload-photo');
  };
  const handleAddFoodItem = () => {
    setModalVisible(false);
    Alert.alert('Coming Soon', 'Add Food Item feature is a placeholder.');
  };

  return (
    <>
      <View style={styles.tabBar}>
        {filteredRoutes.map((route, index) => {
          // Skip rendering the admin tab
          if (route.name === 'admin') return null;
          if (route.name === 'add') {
            return (
              <TouchableOpacity
                key={route.key}
                accessibilityRole="button"
                style={styles.fabContainer}
                onPress={() => setModalVisible(true)}
              >
                <View style={styles.fab}>
                  <Ionicons name="add" size={32} color="#fff" />
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
          const isFocused = state.index === index;
          let iconName: keyof typeof Ionicons.glyphMap = 'ellipse';
          if (route.name === 'index') iconName = isFocused ? 'home' : 'home-outline';
          if (route.name === 'stats') iconName = isFocused ? 'bar-chart' : 'bar-chart-outline';
          if (route.name === 'recipes') iconName = isFocused ? 'restaurant' : 'restaurant-outline';
          if (route.name === 'profile') iconName = isFocused ? 'person' : 'person-outline';
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
      <Modal
        visible={modalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setModalVisible(false)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setModalVisible(false)}>
          <View style={styles.modalContent}>
            <TouchableOpacity style={styles.modalBtn} onPress={handleAddImage}>
              <Ionicons name="image" size={22} color="#297A56" />
              <Text style={styles.modalBtnText}>Add Image</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.modalBtn} onPress={handleAddFoodItem}>
              <Ionicons name="fast-food" size={22} color="#297A56" />
              <Text style={styles.modalBtnText}>Add Food Item</Text>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>
    </>
  );
}

// Define the tabs we want to show in the bottom tab bar
const mainTabs = ['index', 'stats', 'add', 'recipes', 'profile'];

export default function TabsLayout() {
  return (
    <Tabs
      tabBar={props => <CustomTabBar {...props} />}
      screenOptions={{
        header: ({ navigation, route, options }) => {
          // Don't show header for the add screen
          if (route.name === 'add') return null;
          
          return (
            <CustomHeader 
              title="PrepSense"
              showBackButton={false}
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
          title: 'Home',
          header: () => (
            <CustomHeader 
              title="Home"
              showBackButton={false}
              showChatButton={true}
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
              showChatButton={true}
              showAdminButton={true}
            />
          )
        }} 
      />
      <Tabs.Screen 
        name="add" 
        options={{ 
          tabBarLabel: '',
          headerShown: false
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
              showChatButton={true}
              showAdminButton={true}
            />
          )
        }} 
      />
      <Tabs.Screen 
        name="profile" 
        options={{ 
          tabBarLabel: 'Profile',
          header: () => (
            <CustomHeader 
              title="My Profile"
              showBackButton={false}
              showChatButton={true}
              showAdminButton={true}
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