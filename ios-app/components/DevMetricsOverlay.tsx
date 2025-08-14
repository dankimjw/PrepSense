import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { apiMetrics } from '../utils/apiMetrics';

/**
 * Development Metrics Overlay
 * Shows API metrics in a small floating widget during development
 */
export const DevMetricsOverlay: React.FC = () => {
  const [stats, setStats] = useState(apiMetrics.getQuickStats());
  const [minimized, setMinimized] = useState(true);

  useEffect(() => {
    // Update stats every 5 seconds
    const interval = setInterval(() => {
      setStats(apiMetrics.getQuickStats());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Only show in development
  if (!__DEV__) return null;

  if (minimized) {
    return (
      <TouchableOpacity
        style={styles.minimizedContainer}
        onPress={() => setMinimized(false)}
        activeOpacity={0.8}
      >
        <Text style={styles.minimizedText}>📊 {stats.total}</Text>
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.header}
        onPress={() => setMinimized(true)}
        activeOpacity={0.8}
      >
        <Text style={styles.title}>API Metrics</Text>
        <Text style={styles.closeButton}>−</Text>
      </TouchableOpacity>
      
      <View style={styles.statsGrid}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats.total}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
        
        <View style={styles.statItem}>
          <Text style={[styles.statValue, styles.successText]}>{stats.success}</Text>
          <Text style={styles.statLabel}>Success</Text>
        </View>
        
        <View style={styles.statItem}>
          <Text style={[styles.statValue, stats.failed > 0 && styles.errorText]}>{stats.failed}</Text>
          <Text style={styles.statLabel}>Failed</Text>
        </View>
        
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats.avgTime}</Text>
          <Text style={styles.statLabel}>Avg Time</Text>
        </View>
      </View>
      
      <TouchableOpacity
        style={styles.consoleButton}
        onPress={() => {
          apiMetrics.displayMetrics();
          console.log('📊 Check console for detailed metrics');
        }}
      >
        <Text style={styles.consoleButtonText}>Log Details to Console</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  minimizedContainer: {
    position: 'absolute',
    bottom: 100,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    zIndex: 9999,
  },
  minimizedText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  container: {
    position: 'absolute',
    bottom: 100,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    borderRadius: 12,
    padding: 12,
    width: 200,
    zIndex: 9999,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  closeButton: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '300',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  statItem: {
    width: '48%',
    alignItems: 'center',
    marginBottom: 12,
  },
  statValue: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  statLabel: {
    color: '#999',
    fontSize: 10,
    marginTop: 2,
  },
  successText: {
    color: '#4CAF50',
  },
  errorText: {
    color: '#F44336',
  },
  consoleButton: {
    backgroundColor: 'rgba(33, 150, 243, 0.2)',
    paddingVertical: 6,
    borderRadius: 6,
    alignItems: 'center',
  },
  consoleButtonText: {
    color: '#2196F3',
    fontSize: 11,
    fontWeight: '500',
  },
});