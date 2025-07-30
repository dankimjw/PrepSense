// debugPreload.ts - Utility functions for debugging preload status
import AsyncStorage from '@react-native-async-storage/async-storage';

const PRELOAD_STATUS_KEY = 'prepsense_preload_status';
const PRELOAD_LOG_KEY = 'prepsense_preload_logs';

interface PreloadLogEntry {
  timestamp: string;
  type: 'start' | 'success' | 'error' | 'status';
  message: string;
  data?: any;
}

// Global function to check preload status from console
(global as any).checkPreload = async () => {
  try {
    const status = await AsyncStorage.getItem(PRELOAD_STATUS_KEY);
    const logs = await AsyncStorage.getItem(PRELOAD_LOG_KEY);
    
    console.log('\n=== PRELOAD STATUS ===');
    if (status) {
      const parsed = JSON.parse(status);
      console.log('Last Preload:', new Date(parsed.lastPreloadTime).toLocaleString());
      console.log('Load Duration:', `${parsed.loadDuration}ms`);
      console.log('Recipes Count:', parsed.recipesCount);
      console.log('Stats Loaded:', parsed.statsLoaded ? 'Yes' : 'No');
      console.log('Chat Questions:', parsed.chatQuestionsCount);
      if (parsed.errors?.length > 0) {
        console.log('Errors:', parsed.errors.join(', '));
      }
    } else {
      console.log('No preload status found');
    }
    
    if (logs) {
      const parsedLogs = JSON.parse(logs) as PreloadLogEntry[];
      console.log('\n=== RECENT LOGS ===');
      parsedLogs.slice(-10).forEach(log => {
        console.log(`[${new Date(log.timestamp).toLocaleTimeString()}] ${log.type.toUpperCase()}: ${log.message}`);
        if (log.data) {
          console.log('  Data:', log.data);
        }
      });
    }
    
    console.log('\nTo clear preload data, run: clearPreload()');
    console.log('To force reload, run: forcePreload()');
  } catch (error) {
    console.error('Failed to check preload status:', error);
  }
};

// Global function to clear preload data
(global as any).clearPreload = async () => {
  try {
    await AsyncStorage.multiRemove([PRELOAD_STATUS_KEY, PRELOAD_LOG_KEY]);
    console.log('Preload data cleared successfully');
  } catch (error) {
    console.error('Failed to clear preload data:', error);
  }
};

// Export logging functions for use in TabDataProvider
export const logPreloadEvent = async (type: PreloadLogEntry['type'], message: string, data?: any) => {
  try {
    const existingLogs = await AsyncStorage.getItem(PRELOAD_LOG_KEY);
    const logs: PreloadLogEntry[] = existingLogs ? JSON.parse(existingLogs) : [];
    
    logs.push({
      timestamp: new Date().toISOString(),
      type,
      message,
      data
    });
    
    // Keep only last 50 logs
    if (logs.length > 50) {
      logs.splice(0, logs.length - 50);
    }
    
    await AsyncStorage.setItem(PRELOAD_LOG_KEY, JSON.stringify(logs));
  } catch (error) {
    console.error('Failed to log preload event:', error);
  }
};

// Initialize debug commands
export const initPreloadDebug = () => {
  console.log('🛠️  Preload Debug Commands Available:');
  console.log('  - checkPreload() : Check current preload status');
  console.log('  - clearPreload() : Clear all preload data');
};