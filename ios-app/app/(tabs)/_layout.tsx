import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, TouchableOpacity, StyleSheet, Text, Platform, Modal, Pressable, Alert } from 'react-native';
import React, { useState } from 'react';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';

function CustomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const [modalVisible, setModalVisible] = useState(false);

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
        {state.routes.map((route, index) => {
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
          if (route.name === 'index') iconName = 'home';
          if (route.name === 'stats') iconName = 'bar-chart';
          if (route.name === 'recipes') iconName = 'restaurant';
          if (route.name === 'profile') iconName = 'person';
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
              <Ionicons name={iconName} size={24} color={isFocused ? '#297A56' : '#888'} />
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

export default function TabsLayout() {
  return (
    <Tabs
      tabBar={props => <CustomTabBar {...props} />}
      screenOptions={{
        headerShown: false,
      }}
    >
      <Tabs.Screen name="index" options={{ tabBarLabel: 'Dashboard' }} />
      <Tabs.Screen name="stats" options={{ tabBarLabel: 'Stats' }} />
      <Tabs.Screen name="add" options={{ tabBarLabel: '' }} />
      <Tabs.Screen name="recipes" options={{ tabBarLabel: 'Recipes' }} />
      <Tabs.Screen name="profile" options={{ tabBarLabel: 'Profile' }} />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#eee',
    height: 64,
    alignItems: 'center',
    justifyContent: 'space-around',
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: -2 },
    elevation: 8,
    paddingBottom: Platform.OS === 'ios' ? 24 : 8,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
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