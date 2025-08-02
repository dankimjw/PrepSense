// Debug panel for frontend development
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet, Platform } from 'react-native';
import { Portal, Dialog, Button, Divider, Switch, Badge } from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

interface DebugPanelProps {
  visible?: boolean;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({ visible: propVisible }) => {
  const [visible, setVisible] = useState(propVisible || false);
  const [debugOptions, setDebugOptions] = useState({
    showComponentBorders: false,
    logStateChanges: false,
    logApiCalls: false,
    showRenderCount: false,
    slowAnimations: false,
    mockData: false,
    // Hybrid-specific debug options
    showHybridDebug: false,
    logPaperTheme: false,
    showNativeWindClasses: false,
    measureRenderPerformance: false,
  });
  const [logs, setLogs] = useState<string[]>([]);
  const [hybridStats, setHybridStats] = useState({
    hybridComponentsCount: 0,
    paperComponentsCount: 0,
    nativeComponentsCount: 0,
    renderTimes: {} as Record<string, number[]>,
  });

  // Float button for easy access
  const FloatingDebugButton = () => (
    <TouchableOpacity
      style={styles.floatingButton}
      onPress={() => setVisible(true)}
    >
      <Ionicons name="bug" size={24} color="white" />
      {hybridStats.hybridComponentsCount > 0 && (
        <Badge size={18} style={styles.hybridBadge}>
          {hybridStats.hybridComponentsCount}
        </Badge>
      )}
    </TouchableOpacity>
  );

  // Apply debug options
  useEffect(() => {
    if (__DEV__) {
      global.__debugOptions = debugOptions;
      
      // Store preferences
      AsyncStorage.setItem('debugOptions', JSON.stringify(debugOptions));
      
      // Apply slow animations
      if (debugOptions.slowAnimations) {
        global.__slowAnimations = 0.1;
      } else {
        global.__slowAnimations = 1;
      }

      // Initialize hybrid debug tracking
      if (debugOptions.showHybridDebug) {
        global.__hybridDebug = {
          trackComponent: (name: string, type: 'hybrid' | 'paper' | 'native') => {
            setHybridStats(prev => ({
              ...prev,
              [`${type}ComponentsCount`]: prev[`${type}ComponentsCount`] + 1,
            }));
          },
          trackRenderTime: (componentName: string, renderTime: number) => {
            setHybridStats(prev => ({
              ...prev,
              renderTimes: {
                ...prev.renderTimes,
                [componentName]: [...(prev.renderTimes[componentName] || []), renderTime].slice(-10), // Keep last 10
              },
            }));
          },
        };
      }
    }
  }, [debugOptions]);

  // Enhanced log capture for hybrid components
  useEffect(() => {
    if (__DEV__ && (debugOptions.logStateChanges || debugOptions.showHybridDebug)) {
      const originalLog = console.log;
      console.log = (...args) => {
        originalLog(...args);
        const logMessage = args.join(' ');
        if (
          logMessage.includes('[Component]') || 
          logMessage.includes('[State]') ||
          logMessage.includes('🎨') || // StyleDebugger logs
          logMessage.includes('[Hybrid]')
        ) {
          setLogs(prev => [...prev.slice(-50), logMessage]);
        }
      };
      
      return () => {
        console.log = originalLog;
      };
    }
  }, [debugOptions.logStateChanges, debugOptions.showHybridDebug]);

  const toggleOption = (key: keyof typeof debugOptions) => {
    setDebugOptions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const clearLogs = () => setLogs([]);
  
  const exportLogs = async () => {
    const logData = logs.join('\n');
    const hybridStatsData = JSON.stringify(hybridStats, null, 2);
    const exportData = `Debug Logs:\n${logData}\n\nHybrid Stats:\n${hybridStatsData}`;
    console.log('Debug Export:', exportData);
    // Could implement sharing functionality here
  };

  const resetHybridStats = () => {
    setHybridStats({
      hybridComponentsCount: 0,
      paperComponentsCount: 0,
      nativeComponentsCount: 0,
      renderTimes: {},
    });
  };

  const getAverageRenderTime = (componentName: string) => {
    const times = hybridStats.renderTimes[componentName] || [];
    if (times.length === 0) return 0;
    return Math.round(times.reduce((sum, time) => sum + time, 0) / times.length);
  };

  if (!__DEV__) return null;

  return (
    <>
      {!visible && <FloatingDebugButton />}
      
      <Portal>
        <Dialog visible={visible} onDismiss={() => setVisible(false)} style={styles.dialog}>
          <Dialog.Title>🛠️ Hybrid Debug Panel</Dialog.Title>
          
          <Dialog.ScrollArea style={styles.scrollArea}>
            <ScrollView>
              {/* Hybrid Component Stats */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>📊 Hybrid Components</Text>
                
                <View style={styles.statsContainer}>
                  <View style={styles.statItem}>
                    <Text style={styles.statLabel}>Hybrid</Text>
                    <Badge size={24} style={[styles.statBadge, { backgroundColor: '#10B981' }]}>
                      {hybridStats.hybridComponentsCount}
                    </Badge>
                  </View>
                  
                  <View style={styles.statItem}>
                    <Text style={styles.statLabel}>Paper</Text>
                    <Badge size={24} style={[styles.statBadge, { backgroundColor: '#3B82F6' }]}>
                      {hybridStats.paperComponentsCount}
                    </Badge>
                  </View>
                  
                  <View style={styles.statItem}>
                    <Text style={styles.statLabel}>Native</Text>
                    <Badge size={24} style={[styles.statBadge, { backgroundColor: '#6B7280' }]}>
                      {hybridStats.nativeComponentsCount}
                    </Badge>
                  </View>
                </View>

                <Button mode="outlined" onPress={resetHybridStats} style={styles.actionButton}>
                  Reset Stats
                </Button>
              </View>

              <Divider />

              {/* Performance Tracking */}
              {Object.keys(hybridStats.renderTimes).length > 0 && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>⚡ Render Performance</Text>
                  
                  {Object.entries(hybridStats.renderTimes).map(([componentName, times]) => (
                    <View key={componentName} style={styles.performanceItem}>
                      <Text style={styles.componentName}>{componentName}</Text>
                      <Text style={styles.renderTime}>
                        {getAverageRenderTime(componentName)}ms avg
                      </Text>
                      <Text style={styles.renderCount}>
                        ({times.length} renders)
                      </Text>
                    </View>
                  ))}
                </View>
              )}

              <Divider />

              {/* Visual Debugging */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>👁️ Visual Debugging</Text>
                
                <View style={styles.option}>
                  <Text>Show Component Borders</Text>
                  <Switch
                    value={debugOptions.showComponentBorders}
                    onValueChange={() => toggleOption('showComponentBorders')}
                  />
                </View>
                
                <View style={styles.option}>
                  <Text>Show NativeWind Classes</Text>
                  <Switch
                    value={debugOptions.showNativeWindClasses}
                    onValueChange={() => toggleOption('showNativeWindClasses')}
                  />
                </View>
                
                <View style={styles.option}>
                  <Text>Show Render Count</Text>
                  <Switch
                    value={debugOptions.showRenderCount}
                    onValueChange={() => toggleOption('showRenderCount')}
                  />
                </View>
                
                <View style={styles.option}>
                  <Text>Slow Animations (0.1x)</Text>
                  <Switch
                    value={debugOptions.slowAnimations}
                    onValueChange={() => toggleOption('slowAnimations')}
                  />
                </View>
              </View>
              
              <Divider />
              
              {/* Hybrid-Specific Options */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>🔄 Hybrid Debug Options</Text>
                
                <View style={styles.option}>
                  <Text>Show Hybrid Debug Info</Text>
                  <Switch
                    value={debugOptions.showHybridDebug}
                    onValueChange={() => toggleOption('showHybridDebug')}
                  />
                </View>
                
                <View style={styles.option}>
                  <Text>Log Paper Theme Changes</Text>
                  <Switch
                    value={debugOptions.logPaperTheme}
                    onValueChange={() => toggleOption('logPaperTheme')}
                  />
                </View>
                
                <View style={styles.option}>
                  <Text>Measure Render Performance</Text>
                  <Switch
                    value={debugOptions.measureRenderPerformance}
                    onValueChange={() => toggleOption('measureRenderPerformance')}
                  />
                </View>
              </View>
              
              <Divider />
              
              {/* Logging Options */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>📝 Logging</Text>
                
                <View style={styles.option}>
                  <Text>Log State Changes</Text>
                  <Switch
                    value={debugOptions.logStateChanges}
                    onValueChange={() => toggleOption('logStateChanges')}
                  />
                </View>
                
                <View style={styles.option}>
                  <Text>Log API Calls</Text>
                  <Switch
                    value={debugOptions.logApiCalls}
                    onValueChange={() => toggleOption('logApiCalls')}
                  />
                </View>
                
                <View style={styles.option}>
                  <Text>Use Mock Data</Text>
                  <Switch
                    value={debugOptions.mockData}
                    onValueChange={() => toggleOption('mockData')}
                  />
                </View>
              </View>
              
              <Divider />
              
              {/* Quick Actions */}
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>🚀 Quick Actions</Text>
                
                <Button 
                  mode="outlined" 
                  onPress={() => {
                    console.log('🎬 Triggering intro animation...');
                    // @ts-ignore
                    global.showIntroAnimation?.();
                  }}
                  style={styles.actionButton}
                >
                  Show Intro Animation
                </Button>
                
                <Button 
                  mode="outlined" 
                  onPress={() => {
                    console.log('🎨 Testing hybrid components...');
                    // @ts-ignore
                    global.__hybridDebug?.trackComponent('TestComponent', 'hybrid');
                  }}
                  style={styles.actionButton}
                >
                  Test Hybrid Tracking
                </Button>
                
                <Button 
                  mode="outlined" 
                  onPress={() => AsyncStorage.clear()}
                  style={styles.actionButton}
                >
                  Clear AsyncStorage
                </Button>
                
                <Button 
                  mode="outlined" 
                  onPress={() => {
                    // @ts-ignore
                    global.__reloadApp?.();
                  }}
                  style={styles.actionButton}
                >
                  Reload App
                </Button>
              </View>
              
              <Divider />
              
              {/* Log Viewer */}
              {logs.length > 0 && (
                <View style={styles.section}>
                  <View style={styles.logHeader}>
                    <Text style={styles.sectionTitle}>📄 Recent Logs</Text>
                    <TouchableOpacity onPress={clearLogs}>
                      <Text style={styles.clearButton}>Clear</Text>
                    </TouchableOpacity>
                  </View>
                  
                  <View style={styles.logContainer}>
                    {logs.slice(-20).map((log, index) => (
                      <Text key={index} style={[
                        styles.logEntry,
                        log.includes('🎨') && styles.hybridLog,
                        log.includes('[Component]') && styles.componentLog,
                      ]}>
                        {log}
                      </Text>
                    ))}
                  </View>
                  
                  <Button mode="text" onPress={exportLogs}>
                    Export Logs & Stats
                  </Button>
                </View>
              )}
            </ScrollView>
          </Dialog.ScrollArea>
          
          <Dialog.Actions>
            <Button onPress={() => setVisible(false)}>Close</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </>
  );
};

const styles = StyleSheet.create({
  floatingButton: {
    position: 'absolute',
    bottom: 100,
    right: 20,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#ff6b6b',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  hybridBadge: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: '#10B981',
  },
  dialog: {
    maxHeight: '80%',
  },
  scrollArea: {
    paddingHorizontal: 0,
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  // Hybrid Stats Styles
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  statBadge: {
    backgroundColor: '#10B981',
  },
  // Performance Styles
  performanceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  componentName: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
  },
  renderTime: {
    fontSize: 12,
    color: '#10B981',
    fontWeight: '600',
  },
  renderCount: {
    fontSize: 10,
    color: '#6B7280',
    marginLeft: 8,
  },
  // Existing styles
  option: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  actionButton: {
    marginVertical: 4,
  },
  logHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  clearButton: {
    color: '#0a7ea4',
    fontSize: 14,
  },
  logContainer: {
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 8,
    maxHeight: 200,
  },
  logEntry: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 4,
  },
  hybridLog: {
    color: '#10B981',
    fontWeight: '500',
  },
  componentLog: {
    color: '#3B82F6',
  },
});

// Export debug helpers
export const debugBorder = (enabled: boolean) => 
  enabled && __DEV__ && global.__debugOptions?.showComponentBorders
    ? { borderWidth: 1, borderColor: 'red' }
    : {};

export const debugLog = (component: string, message: string, data?: any) => {
  if (__DEV__ && global.__debugOptions?.logStateChanges) {
    console.log(`[Component] ${component}: ${message}`, data || '');
  }
};

// Hybrid-specific debug helpers
export const debugHybrid = (componentName: string, type: 'hybrid' | 'paper' | 'native') => {
  if (__DEV__ && global.__hybridDebug) {
    global.__hybridDebug.trackComponent(componentName, type);
  }
};

export const debugRenderTime = (componentName: string, renderTime: number) => {
  if (__DEV__ && global.__hybridDebug) {
    global.__hybridDebug.trackRenderTime(componentName, renderTime);
  }
};