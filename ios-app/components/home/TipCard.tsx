import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface TipCardProps {
  title?: string;
  text: string;
  iconName?: keyof typeof Ionicons.glyphMap;
  iconColor?: string;
}

export const TipCard: React.FC<TipCardProps> = ({
  title = 'Storage Tip',
  text,
  iconName = 'bulb',
  iconColor = '#F59E0B',
}) => {
  return (
    <View style={styles.tipCard}>
      <Ionicons name={iconName} size={24} color={iconColor} />
      <View style={styles.tipContent}>
        <Text style={styles.tipTitle}>{title}</Text>
        <Text style={styles.tipText}>{text}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  tipCard: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  tipContent: {
    flex: 1,
    marginLeft: 12,
  },
  tipTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  tipText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
});