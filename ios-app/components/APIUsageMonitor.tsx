import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import apiRateLimiter from '../utils/apiRateLimiter';

interface UsageStats {
  requestsInLastMinute: number;
  requestsInLastHour: number;
  requestsInLastDay: number;
  dailyCost: number;
  isBlocked: boolean;
  limitsApproaching: boolean;
}

export const APIUsageMonitor: React.FC<{ compact?: boolean }> = ({ compact = false }) => {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [expanded, setExpanded] = useState(!compact);

  useEffect(() => {
    // Update stats every 5 seconds
    const updateStats = () => {
      const currentStats = apiRateLimiter.getUsageStats();
      setStats(currentStats);
    };

    updateStats();
    const interval = setInterval(updateStats, 5000);

    return () => clearInterval(interval);
  }, []);

  if (!stats) return null;

  const getUsageColor = (current: number, max: number) => {
    const percentage = (current / max) * 100;
    if (percentage >= 90) return '#DC2626'; // Red
    if (percentage >= 75) return '#F59E0B'; // Orange
    if (percentage >= 50) return '#10B981'; // Green
    return '#6B7280'; // Gray
  };

  if (compact && !expanded) {
    return (
      <TouchableOpacity style={styles.compactContainer} onPress={() => setExpanded(true)}>
        <Ionicons 
          name="analytics" 
          size={16} 
          color={stats.limitsApproaching ? '#F59E0B' : '#6B7280'} 
        />
        <Text style={[styles.compactText, stats.limitsApproaching && styles.warningText]}>
          {stats.requestsInLastDay}/500 daily
        </Text>
        {stats.limitsApproaching && (
          <Ionicons name="warning" size={14} color="#F59E0B" />
        )}
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.container}>
      {compact && (
        <TouchableOpacity style={styles.closeButton} onPress={() => setExpanded(false)}>
          <Ionicons name="close" size={18} color="#6B7280" />
        </TouchableOpacity>
      )}
      
      <Text style={styles.title}>API Usage Monitor</Text>
      
      {stats.isBlocked && (
        <View style={styles.blockedAlert}>
          <Ionicons name="alert-circle" size={20} color="#DC2626" />
          <Text style={styles.blockedText}>API Blocked - Limits Exceeded</Text>
        </View>
      )}

      <View style={styles.statRow}>
        <Text style={styles.label}>Last Minute:</Text>
        <View style={styles.progressContainer}>
          <View 
            style={[
              styles.progressBar, 
              { 
                width: `${Math.min((stats.requestsInLastMinute / 20) * 100, 100)}%`,
                backgroundColor: getUsageColor(stats.requestsInLastMinute, 20)
              }
            ]} 
          />
          <Text style={styles.statValue}>{stats.requestsInLastMinute}/20</Text>
        </View>
      </View>

      <View style={styles.statRow}>
        <Text style={styles.label}>Last Hour:</Text>
        <View style={styles.progressContainer}>
          <View 
            style={[
              styles.progressBar, 
              { 
                width: `${Math.min((stats.requestsInLastHour / 100) * 100, 100)}%`,
                backgroundColor: getUsageColor(stats.requestsInLastHour, 100)
              }
            ]} 
          />
          <Text style={styles.statValue}>{stats.requestsInLastHour}/100</Text>
        </View>
      </View>

      <View style={styles.statRow}>
        <Text style={styles.label}>Today:</Text>
        <View style={styles.progressContainer}>
          <View 
            style={[
              styles.progressBar, 
              { 
                width: `${Math.min((stats.requestsInLastDay / 500) * 100, 100)}%`,
                backgroundColor: getUsageColor(stats.requestsInLastDay, 500)
              }
            ]} 
          />
          <Text style={styles.statValue}>{stats.requestsInLastDay}/500</Text>
        </View>
      </View>

      {stats.dailyCost > 0 && (
        <View style={styles.costRow}>
          <Text style={styles.label}>Est. Cost Today:</Text>
          <Text style={[styles.costValue, stats.dailyCost > 1 && styles.warningText]}>
            ${stats.dailyCost.toFixed(3)}
          </Text>
        </View>
      )}

      {stats.limitsApproaching && (
        <View style={styles.warningRow}>
          <Ionicons name="warning" size={16} color="#F59E0B" />
          <Text style={styles.warningText}>Approaching API limits!</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  compactContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  compactText: {
    fontSize: 12,
    color: '#6B7280',
  },
  closeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    zIndex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  statRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  label: {
    fontSize: 12,
    color: '#6B7280',
    width: 70,
  },
  progressContainer: {
    flex: 1,
    height: 20,
    backgroundColor: '#E5E7EB',
    borderRadius: 10,
    overflow: 'hidden',
    position: 'relative',
  },
  progressBar: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    borderRadius: 10,
  },
  statValue: {
    position: 'absolute',
    right: 8,
    fontSize: 11,
    color: '#374151',
    fontWeight: '500',
  },
  costRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  costValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  warningRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 8,
  },
  warningText: {
    color: '#F59E0B',
    fontSize: 12,
    fontWeight: '500',
  },
  blockedAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FEE2E2',
    padding: 8,
    borderRadius: 6,
    marginBottom: 8,
  },
  blockedText: {
    color: '#DC2626',
    fontSize: 12,
    fontWeight: '600',
  },
});