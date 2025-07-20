/**
 * Comprehensive Connectivity Validator for PrepSense App
 * 
 * This module provides runtime connectivity validation, error handling,
 * and user-friendly error states for network issues.
 */

import { Alert } from 'react-native';
import { Config } from '../config';

export interface ConnectivityResult {
  isHealthy: boolean;
  services: {
    api: boolean;
    database: boolean;
    openai: boolean;
    spoonacular: boolean;
  };
  errors: string[];
  warnings: string[];
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 8000,
  backoffMultiplier: 2
};

/**
 * Performs a comprehensive health check of all app services
 */
export async function performHealthCheck(): Promise<ConnectivityResult> {
  const result: ConnectivityResult = {
    isHealthy: false,
    services: {
      api: false,
      database: false,
      openai: false,
      spoonacular: false
    },
    errors: [],
    warnings: []
  };

  try {
    const healthResponse = await fetchWithTimeout(`${Config.API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    }, 5000);

    if (!healthResponse.ok) {
      result.errors.push(`API unhealthy: ${healthResponse.status}`);
      return result;
    }

    const healthData = await healthResponse.json();
    
    // Check API connectivity
    result.services.api = healthData.status === 'healthy';
    
    // Check individual services
    if (healthData.environment) {
      result.services.database = healthData.environment.database_connected;
      result.services.openai = healthData.environment.openai_valid;
      result.services.spoonacular = healthData.environment.spoonacular_configured;
    }

    // Collect errors
    if (healthData.errors && healthData.errors.length > 0) {
      result.errors.push(...healthData.errors);
    }

    // Add warnings for unhealthy services
    if (!result.services.database) {
      result.warnings.push('Database connection issues detected');
    }
    if (!result.services.openai) {
      result.warnings.push('OpenAI API configuration issues');
    }
    if (!result.services.spoonacular) {
      result.warnings.push('Spoonacular API configuration issues');
    }

    result.isHealthy = result.services.api && result.services.database;

  } catch (error) {
    result.errors.push(`Failed to connect to API: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  return result;
}

/**
 * Tests a specific API endpoint with retry logic
 */
export async function testEndpoint(
  endpoint: string, 
  options: RequestInit = {}, 
  retryConfig: Partial<RetryConfig> = {}
): Promise<{ success: boolean; data?: any; error?: string }> {
  const config = { ...DEFAULT_RETRY_CONFIG, ...retryConfig };
  
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const response = await fetchWithTimeout(
        `${Config.API_BASE_URL}${endpoint}`,
        options,
        10000
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, data };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      if (attempt === config.maxRetries) {
        return { success: false, error: errorMessage };
      }

      // Wait before retry with exponential backoff
      const delay = Math.min(
        config.baseDelay * Math.pow(config.backoffMultiplier, attempt),
        config.maxDelay
      );
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  return { success: false, error: 'Max retries exceeded' };
}

/**
 * Fetch with timeout support
 */
async function fetchWithTimeout(url: string, options: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeout);
    return response;
  } catch (error) {
    clearTimeout(timeout);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeoutMs}ms`);
    }
    throw error;
  }
}

/**
 * Shows user-friendly error messages for connectivity issues
 */
export function showConnectivityError(result: ConnectivityResult) {
  if (result.isHealthy) return;

  const title = 'Connection Issue';
  let message = 'Unable to connect to PrepSense services.\n\n';

  if (result.errors.length > 0) {
    message += 'Issues found:\n';
    result.errors.forEach(error => {
      message += `• ${error}\n`;
    });
  }

  message += '\nPlease check your internet connection and try again.';

  Alert.alert(title, message, [
    { text: 'Retry', onPress: () => performHealthCheck() },
    { text: 'Continue Offline', style: 'cancel' }
  ]);
}

/**
 * Validates critical app functionality on startup
 */
export async function validateAppStartup(): Promise<boolean> {
  console.log('🔍 Validating app connectivity...');
  
  const healthCheck = await performHealthCheck();
  
  if (!healthCheck.isHealthy) {
    console.error('❌ App startup validation failed:', healthCheck.errors);
    
    if (Config.IS_DEVELOPMENT) {
      // In development, show detailed error information
      console.log('🔧 Development Debug Info:');
      console.log('API URL:', Config.API_BASE_URL);
      console.log('Environment variable:', process.env.EXPO_PUBLIC_API_BASE_URL);
      console.log('Services status:', healthCheck.services);
    }
    
    showConnectivityError(healthCheck);
    return false;
  }

  console.log('✅ App connectivity validated successfully');
  
  if (healthCheck.warnings.length > 0) {
    console.warn('⚠️ Some services have warnings:', healthCheck.warnings);
  }

  return true;
}

/**
 * Monitors connectivity during app usage
 */
export class ConnectivityMonitor {
  private isMonitoring = false;
  private monitorInterval?: NodeJS.Timeout;
  private listeners: ((result: ConnectivityResult) => void)[] = [];

  start(intervalMs: number = 30000) {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.monitorInterval = setInterval(async () => {
      const result = await performHealthCheck();
      this.notifyListeners(result);
    }, intervalMs);
  }

  stop() {
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = undefined;
    }
    this.isMonitoring = false;
  }

  addListener(callback: (result: ConnectivityResult) => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  private notifyListeners(result: ConnectivityResult) {
    this.listeners.forEach(listener => {
      try {
        listener(result);
      } catch (error) {
        console.error('Error in connectivity listener:', error);
      }
    });
  }
}

// Global connectivity monitor instance
export const connectivityMonitor = new ConnectivityMonitor();