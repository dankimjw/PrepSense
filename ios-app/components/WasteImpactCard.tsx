import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface WasteImpactCardProps {
  expiringItems: Array<{
    name: string;
    daysLeft: number;
    quantity: number;
    unit: string;
  }>;
  onPress?: () => void;
}

const WasteImpactCard: React.FC<WasteImpactCardProps> = ({ expiringItems, onPress }) => {
  // Calculate total impact based on expiring items
  const calculateImpact = () => {
    let totalCO2 = 0;
    let totalValue = 0;
    let totalOriginalProduction = 0;

    // Sample calculations (would use actual API data)
    expiringItems.forEach(item => {
      const itemLower = item.name.toLowerCase();
      
      // Estimate multipliers based on food type
      let multiplier = 1.8;
      let co2PerKg = 2.0;
      let pricePerKg = 5.0;
      
      if (itemLower.includes('lettuce') || itemLower.includes('spinach')) {
        multiplier = 2.8;  // High supply chain loss
        co2PerKg = 1.5;
      } else if (itemLower.includes('tomato')) {
        multiplier = 2.52;
        co2PerKg = 2.09;
      } else if (itemLower.includes('banana')) {
        multiplier = 2.86;
        co2PerKg = 0.86;
      } else if (itemLower.includes('beef')) {
        multiplier = 1.8;
        co2PerKg = 99.48;
        pricePerKg = 15.0;
      }
      
      // Assume 0.5kg average per item if unit not specified
      const kgAmount = item.unit === 'kg' ? item.quantity : item.quantity * 0.5;
      
      totalCO2 += kgAmount * co2PerKg * multiplier;
      totalValue += kgAmount * pricePerKg;
      totalOriginalProduction += kgAmount * multiplier;
    });

    return {
      co2: totalCO2.toFixed(1),
      value: totalValue.toFixed(0),
      originalKg: totalOriginalProduction.toFixed(1),
      drivingMiles: (totalCO2 * 2.5).toFixed(0)
    };
  };

  const impact = calculateImpact();
  const hasHighRisk = expiringItems.some(item => item.daysLeft <= 2);

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.8}>
      <View style={[styles.card, hasHighRisk && styles.urgentCard]}>
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <MaterialCommunityIcons 
              name="earth" 
              size={24} 
              color={hasHighRisk ? '#dc2626' : '#f59e0b'} 
            />
            <Text style={styles.title}>Waste Impact Alert</Text>
          </View>
          {hasHighRisk && (
            <View style={styles.urgentBadge}>
              <Text style={styles.urgentText}>URGENT</Text>
            </View>
          )}
        </View>

        <View style={styles.impactGrid}>
          <View style={styles.impactItem}>
            <Text style={styles.impactValue}>{impact.co2}</Text>
            <Text style={styles.impactLabel}>kg CO₂e</Text>
            <Text style={styles.impactContext}>= {impact.drivingMiles} miles</Text>
          </View>
          
          <View style={styles.impactItem}>
            <Text style={styles.impactValue}>${impact.value}</Text>
            <Text style={styles.impactLabel}>at risk</Text>
            <Text style={styles.impactContext}>economic value</Text>
          </View>
          
          <View style={styles.impactItem}>
            <Text style={styles.impactValue}>{impact.originalKg}</Text>
            <Text style={styles.impactLabel}>kg produced</Text>
            <Text style={styles.impactContext}>supply chain</Text>
          </View>
        </View>

        <View style={styles.insightBox}>
          <MaterialCommunityIcons name="lightbulb-outline" size={16} color="#f59e0b" />
          <Text style={styles.insightText}>
            {expiringItems.length} items expiring soon. Preventing their waste saves the entire supply chain impact!
          </Text>
        </View>

        <View style={styles.actionRow}>
          <Text style={styles.actionText}>Tap to see waste-smart recipes →</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  urgentCard: {
    borderWidth: 2,
    borderColor: '#dc2626',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  urgentBadge: {
    backgroundColor: '#dc2626',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  urgentText: {
    color: 'white',
    fontSize: 11,
    fontWeight: '700',
  },
  impactGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  impactItem: {
    alignItems: 'center',
  },
  impactValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1f2937',
  },
  impactLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  impactContext: {
    fontSize: 11,
    color: '#9ca3af',
    marginTop: 2,
  },
  insightBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#fef3c7',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    gap: 8,
  },
  insightText: {
    flex: 1,
    fontSize: 13,
    color: '#92400e',
    lineHeight: 18,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  actionText: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: '500',
  },
});

export default WasteImpactCard;