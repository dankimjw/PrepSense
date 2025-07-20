import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

export interface QuickAction {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  color: string;
  route?: string;
  onPress?: () => void;
}

interface QuickActionsProps {
  actions?: QuickAction[];
}

const defaultActions: QuickAction[] = [
  { 
    id: 'add', 
    icon: 'add-circle',
    title: 'Add Item',
    color: '#297A56',
    route: '/add-item'
  },
  { 
    id: 'scan', 
    icon: 'receipt',
    title: 'Scan Receipt',
    color: '#4F46E5',
    route: '/receipt-scanner'
  },
  { 
    id: 'recipe', 
    icon: 'restaurant',
    title: 'Recipes',
    color: '#DB2777',
    route: '/recipes'
  },
  { 
    id: 'shopping', 
    icon: 'cart',
    title: 'Shopping List',
    color: '#7C3AED',
    route: '/shopping-list'
  },
];

export const QuickActions: React.FC<QuickActionsProps> = ({ actions = defaultActions }) => {
  const router = useRouter();

  const handleActionPress = (action: QuickAction) => {
    if (action.onPress) {
      action.onPress();
    } else if (action.route) {
      router.push(action.route as any);
    }
  };

  return (
    <>
      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.quickActions}>
        {actions.map((action) => (
          <TouchableOpacity 
            key={action.id}
            style={[styles.actionCard, { backgroundColor: action.color + '15' }]}
            onPress={() => handleActionPress(action)}
          >
            <View style={[styles.actionIcon, { backgroundColor: action.color }]}>
              <Ionicons name={action.icon} size={24} color="white" />
            </View>
            <Text style={styles.actionText}>{action.title}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </>
  );
};

const styles = StyleSheet.create({
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  actionCard: {
    flex: 1,
    marginHorizontal: 4,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#111827',
    textAlign: 'center',
    lineHeight: 14,
  },
});