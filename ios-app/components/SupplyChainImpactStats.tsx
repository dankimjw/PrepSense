import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSupplyChainImpact } from '../hooks/useSupplyChainImpact';

interface SupplyChainStatsProps {
  userId: string;
}

const SupplyChainImpactStats: React.FC<SupplyChainStatsProps> = ({ userId }) => {
  const { todayImpact, supplyChainGuide, weeklyTrends, loading } = useSupplyChainImpact(userId);
  const [selectedTab, setSelectedTab] = useState<'today' | 'trends' | 'impact'>('today');

  if (loading || !todayImpact) {
    return (
      <View style={styles.loading}>
        <Text>Loading impact data...</Text>
      </View>
    );
  }

  const renderTodayTab = () => (
    <View style={styles.tabContent}>
      <View style={styles.heroCard}>
        <View style={styles.heroHeader}>
          <MaterialCommunityIcons name="earth" size={32} color="#dc2626" />
          <Text style={styles.heroTitle}>Today's Impact</Text>
        </View>
        
        <View style={styles.heroMetrics}>
          <View style={styles.heroMetric}>
            <Text style={styles.heroValue}>{todayImpact.total_co2e}</Text>
            <Text style={styles.heroLabel}>kg CO₂e at risk</Text>
          </View>
          <View style={styles.heroMetric}>
            <Text style={styles.heroValue}>{todayImpact.supply_chain_multiplier}x</Text>
            <Text style={styles.heroLabel}>supply chain impact</Text>
          </View>
        </View>

        <View style={styles.insightBox}>
          <MaterialCommunityIcons name="information" size={20} color="#3b82f6" />
          <Text style={styles.insightText}>
            For every 1kg you waste, {todayImpact.supply_chain_multiplier}kg was originally produced across the supply chain
          </Text>
        </View>
      </View>

      <View style={styles.breakdownCard}>
        <Text style={styles.cardTitle}>Supply Chain Breakdown</Text>
        <View style={styles.breakdownItem}>
          <Text style={styles.breakdownLabel}>Food reaching your kitchen:</Text>
          <Text style={styles.breakdownValue}>45%</Text>
        </View>
        <View style={styles.breakdownItem}>
          <Text style={styles.breakdownLabel}>Lost at farm & harvest:</Text>
          <Text style={styles.breakdownValue}>25%</Text>
        </View>
        <View style={styles.breakdownItem}>
          <Text style={styles.breakdownLabel}>Lost in transport & storage:</Text>
          <Text style={styles.breakdownValue}>20%</Text>
        </View>
        <View style={styles.breakdownItem}>
          <Text style={styles.breakdownLabel}>Lost at retail:</Text>
          <Text style={styles.breakdownValue}>10%</Text>
        </View>
      </View>
    </View>
  );

  const renderTrendsTab = () => (
    <View style={styles.tabContent}>
      <View style={styles.trendCard}>
        <Text style={styles.cardTitle}>This Week's Impact</Text>
        
        <View style={styles.trendMetrics}>
          <View style={styles.trendMetric}>
            <MaterialCommunityIcons name="check-circle" size={24} color="#10b981" />
            <Text style={styles.trendValue}>{weeklyTrends.reduce((sum, week) => sum + week.items_prevented, 0)}</Text>
            <Text style={styles.trendLabel}>items saved</Text>
          </View>
          
          <View style={styles.trendMetric}>
            <MaterialCommunityIcons name="close-circle" size={24} color="#ef4444" />
            <Text style={styles.trendValue}>{weeklyTrends.reduce((sum, week) => sum + week.items_wasted, 0)}</Text>
            <Text style={styles.trendLabel}>items wasted</Text>
          </View>
          
          <View style={styles.trendMetric}>
            <MaterialCommunityIcons name="leaf" size={24} color="#22c55e" />
            <Text style={styles.trendValue}>{weeklyTrends.reduce((sum, week) => sum + week.prevented_co2e, 0).toFixed(1)}</Text>
            <Text style={styles.trendLabel}>kg CO₂e saved</Text>
          </View>
        </View>

        <View style={styles.achievementBox}>
          <Text style={styles.achievementText}>🌟 Great job! You saved the equivalent of:</Text>
          <Text style={styles.achievementDetail}>
            • {(weeklyTrends.reduce((sum, week) => sum + week.prevented_co2e, 0) * 2.5).toFixed(0)} miles of driving
          </Text>
          <Text style={styles.achievementDetail}>
            • Prevented {(weeklyTrends.reduce((sum, week) => sum + week.items_prevented, 0) * 2.2).toFixed(1)}kg of upstream production waste
          </Text>
        </View>
      </View>
    </View>
  );

  const renderImpactTab = () => (
    <View style={styles.tabContent}>
      <Text style={styles.sectionTitle}>Supply Chain Multipliers</Text>
      <Text style={styles.sectionSubtitle}>
        How much was originally produced for each food type
      </Text>
      
      {supplyChainGuide.map((item, index) => (
        <View key={index} style={styles.impactItemCard}>
          <View style={styles.impactItemHeader}>
            <Text style={styles.impactItemName}>{item.food}</Text>
            <View style={styles.multiplierBadge}>
              <Text style={styles.multiplierText}>{item.multiplier}x</Text>
            </View>
          </View>
          
          <Text style={styles.impactItemDescription}>{item.description}</Text>
          
          <View style={styles.impactItemStats}>
            <Text style={styles.impactStat}>
              CO₂: {item.co2e_per_kg} kg/kg → {item.amplified_co2e.toFixed(1)} kg/kg wasted
            </Text>
          </View>
        </View>
      ))}
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Supply Chain Impact</Text>
        <Text style={styles.headerSubtitle}>See the full journey of your food</Text>
      </View>

      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, selectedTab === 'today' && styles.activeTab]}
          onPress={() => setSelectedTab('today')}
        >
          <Text style={[styles.tabText, selectedTab === 'today' && styles.activeTabText]}>
            Today
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, selectedTab === 'trends' && styles.activeTab]}
          onPress={() => setSelectedTab('trends')}
        >
          <Text style={[styles.tabText, selectedTab === 'trends' && styles.activeTabText]}>
            Trends
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, selectedTab === 'impact' && styles.activeTab]}
          onPress={() => setSelectedTab('impact')}
        >
          <Text style={[styles.tabText, selectedTab === 'impact' && styles.activeTabText]}>
            Impact Guide
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView}>
        {selectedTab === 'today' && renderTodayTab()}
        {selectedTab === 'trends' && renderTrendsTab()}
        {selectedTab === 'impact' && renderImpactTab()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    padding: 20,
    backgroundColor: 'white',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1f2937',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 4,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  tab: {
    flex: 1,
    paddingVertical: 16,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#3b82f6',
  },
  tabText: {
    fontSize: 16,
    color: '#6b7280',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#3b82f6',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  tabContent: {
    padding: 16,
  },
  heroCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  heroHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
  },
  heroMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  heroMetric: {
    alignItems: 'center',
  },
  heroValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#dc2626',
  },
  heroLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  insightBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#dbeafe',
    borderRadius: 12,
    padding: 12,
    gap: 8,
  },
  insightText: {
    flex: 1,
    fontSize: 14,
    color: '#1e40af',
    lineHeight: 20,
  },
  breakdownCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 16,
  },
  breakdownItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  breakdownLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  breakdownValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  trendCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
  },
  trendMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  trendMetric: {
    alignItems: 'center',
  },
  trendValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1f2937',
    marginTop: 4,
  },
  trendLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  achievementBox: {
    backgroundColor: '#f0fdf4',
    borderRadius: 12,
    padding: 16,
  },
  achievementText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#166534',
    marginBottom: 8,
  },
  achievementDetail: {
    fontSize: 14,
    color: '#166534',
    marginBottom: 4,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 20,
  },
  impactItemCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  impactItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  impactItemName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  multiplierBadge: {
    backgroundColor: '#fef3c7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  multiplierText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#92400e',
  },
  impactItemDescription: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
  },
  impactItemStats: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 8,
  },
  impactStat: {
    fontSize: 12,
    color: '#374151',
  },
});

export default SupplyChainImpactStats;