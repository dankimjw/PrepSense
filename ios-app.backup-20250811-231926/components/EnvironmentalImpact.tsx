import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface EnvironmentalImpactProps {
  ghgPerKg?: number;
  landPerKg?: number;
  waterPerKg?: number;
  impactCategory?: string;
  visual?: string;
  compact?: boolean;
}

const EnvironmentalImpact: React.FC<EnvironmentalImpactProps> = ({
  ghgPerKg,
  landPerKg,
  waterPerKg,
  impactCategory,
  visual,
  compact = false
}) => {
  const getImpactColor = () => {
    switch (impactCategory) {
      case 'very_low':
        return '#047857';
      case 'low':
        return '#10b981';
      case 'medium':
        return '#f59e0b';
      case 'high':
        return '#f97316';
      case 'very_high':
        return '#dc2626';
      default:
        return '#6b7280';
    }
  };

  if (compact) {
    return (
      <View style={styles.compactContainer}>
        {ghgPerKg !== undefined && (
          <View style={styles.compactItem}>
            <MaterialCommunityIcons name="cloud-outline" size={16} color="#6b7280" />
            <Text style={styles.compactValue}>{ghgPerKg.toFixed(1)}</Text>
            <Text style={styles.compactUnit}>kg CO₂</Text>
          </View>
        )}
        {visual && (
          <Text style={styles.visual}>{visual}</Text>
        )}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Environmental Impact</Text>
        {visual && <Text style={styles.visualLarge}>{visual}</Text>}
      </View>
      
      {impactCategory && (
        <View style={[styles.categoryBadge, { backgroundColor: getImpactColor() }]}>
          <Text style={styles.categoryText}>
            {impactCategory.replace('_', ' ').toUpperCase()}
          </Text>
        </View>
      )}

      <View style={styles.metricsContainer}>
        {ghgPerKg !== undefined && (
          <View style={styles.metric}>
            <View style={styles.metricHeader}>
              <MaterialCommunityIcons name="cloud-outline" size={20} color="#6b7280" />
              <Text style={styles.metricLabel}>Carbon Footprint</Text>
            </View>
            <Text style={styles.metricValue}>{ghgPerKg.toFixed(1)}</Text>
            <Text style={styles.metricUnit}>kg CO₂e per kg</Text>
            {ghgPerKg > 10 && (
              <Text style={styles.comparison}>
                = driving {(ghgPerKg * 2.5).toFixed(0)} miles
              </Text>
            )}
          </View>
        )}

        {landPerKg !== undefined && (
          <View style={styles.metric}>
            <View style={styles.metricHeader}>
              <MaterialCommunityIcons name="terrain" size={20} color="#6b7280" />
              <Text style={styles.metricLabel}>Land Use</Text>
            </View>
            <Text style={styles.metricValue}>{landPerKg.toFixed(1)}</Text>
            <Text style={styles.metricUnit}>m² per kg</Text>
          </View>
        )}

        {waterPerKg !== undefined && (
          <View style={styles.metric}>
            <View style={styles.metricHeader}>
              <MaterialCommunityIcons name="water-outline" size={20} color="#6b7280" />
              <Text style={styles.metricLabel}>Water Use</Text>
            </View>
            <Text style={styles.metricValue}>{waterPerKg.toFixed(0)}</Text>
            <Text style={styles.metricUnit}>liters per kg</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  visualLarge: {
    fontSize: 24,
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
    marginBottom: 16,
  },
  categoryText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  metricsContainer: {
    gap: 16,
  },
  metric: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  metricHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  metricValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1f2937',
  },
  metricUnit: {
    fontSize: 14,
    color: '#6b7280',
  },
  comparison: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
  },
  compactContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  compactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  compactValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4b5563',
  },
  compactUnit: {
    fontSize: 12,
    color: '#6b7280',
  },
  visual: {
    fontSize: 16,
  },
});

export default EnvironmentalImpact;