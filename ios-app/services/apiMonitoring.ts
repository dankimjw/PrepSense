/**
 * API Monitoring Service for PrepSense React Native App
 * 
 * Features:
 * - Performance monitoring for all API calls
 * - Error tracking and classification
 * - Response time SLA monitoring  
 * - Network connectivity status
 * - Retry logic with exponential backoff
 * - Offline queue management
 */

import { trackAPIPerformance, trackNetworkError, sentryLogger } from '../config/sentryConfig';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

// Types
interface APIMonitoringConfig {
  baseURL: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  maxRetryDelay: number;
  slaThresholdMs: number;
  enableOfflineQueue: boolean;
}

interface APICallMetrics {
  endpoint: string;
  method: string;
  startTime: number;
  endTime?: number;
  status?: number;
  responseTime?: number;
  error?: Error;
  retryAttempt: number;
  networkType?: string;
  isOnline: boolean;
}

interface QueuedRequest {
  id: string;
  endpoint: string;
  method: string;
  body?: any;
  headers?: Record<string, string>;
  timestamp: number;
  attempts: number;
}

class APIMonitoringService {
  private config: APIMonitoringConfig;
  private requestQueue: QueuedRequest[] = [];
  private isOnline: boolean = true;
  private networkType: string = 'unknown';
  private pendingRequests: Map<string, APICallMetrics> = new Map();

  constructor(config: Partial<APIMonitoringConfig> = {}) {
    this.config = {
      baseURL: process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8001',
      timeout: 30000, // 30 seconds
      retryAttempts: 3,
      retryDelay: 1000, // 1 second
      maxRetryDelay: 10000, // 10 seconds  
      slaThresholdMs: 5000, // 5 seconds
      enableOfflineQueue: true,
      ...config,
    };

    this.initializeNetworkMonitoring();
    this.loadOfflineQueue();
  }

  /**
   * Initialize network connectivity monitoring
   */
  private async initializeNetworkMonitoring() {
    try {
      // Initial network state
      const netInfo = await NetInfo.fetch();
      this.isOnline = !!netInfo.isConnected;
      this.networkType = netInfo.type || 'unknown';

      // Subscribe to network changes
      NetInfo.addEventListener(state => {
        const wasOnline = this.isOnline;
        this.isOnline = !!state.isConnected;
        this.networkType = state.type || 'unknown';

        sentryLogger.info('Network state changed', {
          isOnline: this.isOnline,
          networkType: this.networkType,
          wasOnline,
        });

        // Process offline queue when coming back online
        if (!wasOnline && this.isOnline) {
          this.processOfflineQueue();
        }
      });
    } catch (error) {
      sentryLogger.error('Failed to initialize network monitoring', error as Error);
    }
  }

  /**
   * Enhanced fetch with monitoring, retries, and error handling
   */
  public async monitoredFetch(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const requestId = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const method = options.method || 'GET';
    const fullUrl = endpoint.startsWith('http') ? endpoint : `${this.config.baseURL}${endpoint}`;

    // Start performance tracking
    const transaction = trackAPIPerformance(endpoint, method);
    
    const metrics: APICallMetrics = {
      endpoint,
      method,
      startTime: Date.now(),
      retryAttempt: 0,
      networkType: this.networkType,
      isOnline: this.isOnline,
    };

    this.pendingRequests.set(requestId, metrics);

    try {
      // Check if offline and should queue
      if (!this.isOnline && this.config.enableOfflineQueue && method !== 'GET') {
        await this.queueRequest(endpoint, method, options.body, options.headers as Record<string, string>);
        throw new Error('Device is offline - request queued for later');
      }

      // Execute request with retries
      const response = await this.executeWithRetries(fullUrl, options, metrics);
      
      // Record successful metrics
      metrics.endTime = Date.now();
      metrics.responseTime = metrics.endTime - metrics.startTime;
      metrics.status = response.status;

      // Check SLA compliance
      if (metrics.responseTime > this.config.slaThresholdMs) {
        sentryLogger.warning('API response time SLA violation', {
          endpoint,
          responseTime: metrics.responseTime,
          slaThreshold: this.config.slaThresholdMs,
        });
      }

      // Log successful request
      sentryLogger.info('API request completed', {
        endpoint,
        method,
        status: response.status,
        responseTime: metrics.responseTime,
        retryAttempt: metrics.retryAttempt,
      });

      transaction.setStatus('ok');
      transaction.setTag('status_code', response.status.toString());
      transaction.setData('response_time', metrics.responseTime);

      return response;

    } catch (error) {
      const err = error as Error;
      metrics.error = err;
      metrics.endTime = Date.now();
      metrics.responseTime = metrics.endTime - metrics.startTime;

      // Track error
      this.handleAPIError(endpoint, method, err, metrics);
      
      transaction.setStatus('internal_error');
      transaction.setTag('error', err.message);

      throw err;

    } finally {
      this.pendingRequests.delete(requestId);
      transaction.finish();
    }
  }

  /**
   * Execute request with retry logic
   */
  private async executeWithRetries(
    url: string,
    options: RequestInit,
    metrics: APICallMetrics
  ): Promise<Response> {
    let lastError: Error;

    for (let attempt = 0; attempt <= this.config.retryAttempts; attempt++) {
      metrics.retryAttempt = attempt;

      try {
        // Add timeout to request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

        const requestOptions: RequestInit = {
          ...options,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        };

        const response = await fetch(url, requestOptions);
        clearTimeout(timeoutId);

        // Check if response indicates a retryable error
        if (response.status >= 500 || response.status === 429) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response;

      } catch (error) {
        const err = error as Error;
        lastError = err;
        clearTimeout(timeoutId);

        // Don't retry on client errors (4xx) except 429 (rate limit)
        if (err.message.includes('HTTP 4') && !err.message.includes('HTTP 429')) {
          throw err;
        }

        // Don't retry if it's the last attempt
        if (attempt === this.config.retryAttempts) {
          throw err;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
          this.config.retryDelay * Math.pow(2, attempt),
          this.config.maxRetryDelay
        );

        sentryLogger.info('Retrying API request', {
          endpoint: metrics.endpoint,
          attempt: attempt + 1,
          delay,
          error: err.message,
        });

        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError!;
  }

  /**
   * Handle API errors with proper categorization
   */
  private handleAPIError(
    endpoint: string,
    method: string,
    error: Error,
    metrics: APICallMetrics
  ) {
    let errorCategory = 'unknown';
    let severity: 'warning' | 'error' = 'error';

    // Categorize errors
    if (error.message.includes('abort')) {
      errorCategory = 'timeout';
      severity = 'warning';
    } else if (error.message.includes('Network')) {
      errorCategory = 'network';
      severity = 'warning';
    } else if (error.message.includes('HTTP 4')) {
      errorCategory = 'client_error';
      severity = 'warning';
    } else if (error.message.includes('HTTP 5')) {
      errorCategory = 'server_error';
      severity = 'error';
    } else if (error.message.includes('offline')) {
      errorCategory = 'offline';
      severity = 'warning';
    }

    // Extract status code
    const statusMatch = error.message.match(/HTTP (\d+)/);
    const status = statusMatch ? parseInt(statusMatch[1]) : undefined;

    // Track network error
    trackNetworkError(endpoint, status, error.message);

    // Log error with context
    sentryLogger.error('API request failed', error, {
      endpoint,
      method,
      errorCategory,
      status,
      responseTime: metrics.responseTime,
      retryAttempt: metrics.retryAttempt,
      networkType: metrics.networkType,
      isOnline: metrics.isOnline,
    });
  }

  /**
   * Queue request for offline processing
   */
  private async queueRequest(
    endpoint: string,
    method: string,
    body?: any,
    headers?: Record<string, string>
  ) {
    const queuedRequest: QueuedRequest = {
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      endpoint,
      method,
      body,
      headers,
      timestamp: Date.now(),
      attempts: 0,
    };

    this.requestQueue.push(queuedRequest);
    await this.saveOfflineQueue();

    sentryLogger.info('Request queued for offline processing', {
      endpoint,
      method,
      queueSize: this.requestQueue.length,
    });
  }

  /**
   * Process offline queue when back online
   */
  private async processOfflineQueue() {
    if (!this.isOnline || this.requestQueue.length === 0) {
      return;
    }

    sentryLogger.info('Processing offline queue', {
      queueSize: this.requestQueue.length,
    });

    const queue = [...this.requestQueue];
    this.requestQueue = [];

    for (const request of queue) {
      try {
        await this.monitoredFetch(request.endpoint, {
          method: request.method,
          body: request.body ? JSON.stringify(request.body) : undefined,
          headers: request.headers,
        });

        sentryLogger.info('Offline request processed successfully', {
          endpoint: request.endpoint,
          method: request.method,
        });

      } catch (error) {
        request.attempts++;
        
        // Retry failed requests up to 3 times
        if (request.attempts < 3) {
          this.requestQueue.push(request);
        } else {
          sentryLogger.error('Offline request failed permanently', error as Error, {
            endpoint: request.endpoint,
            method: request.method,
            attempts: request.attempts,
          });
        }
      }
    }

    await this.saveOfflineQueue();
  }

  /**
   * Save offline queue to storage
   */
  private async saveOfflineQueue() {
    try {
      await AsyncStorage.setItem('api_offline_queue', JSON.stringify(this.requestQueue));
    } catch (error) {
      sentryLogger.error('Failed to save offline queue', error as Error);
    }
  }

  /**
   * Load offline queue from storage
   */
  private async loadOfflineQueue() {
    try {
      const saved = await AsyncStorage.getItem('api_offline_queue');
      if (saved) {
        this.requestQueue = JSON.parse(saved);
        sentryLogger.info('Loaded offline queue', {
          queueSize: this.requestQueue.length,
        });
      }
    } catch (error) {
      sentryLogger.error('Failed to load offline queue', error as Error);
    }
  }

  /**
   * Get current API health metrics
   */
  public getHealthMetrics() {
    return {
      isOnline: this.isOnline,
      networkType: this.networkType,
      queueSize: this.requestQueue.length,
      pendingRequests: this.pendingRequests.size,
      config: this.config,
    };
  }

  /**
   * Clear offline queue (for testing or reset)
   */
  public async clearOfflineQueue() {
    this.requestQueue = [];
    await AsyncStorage.removeItem('api_offline_queue');
    sentryLogger.info('Offline queue cleared');
  }

  /**
   * Update configuration
   */
  public updateConfig(newConfig: Partial<APIMonitoringConfig>) {
    this.config = { ...this.config, ...newConfig };
    sentryLogger.info('API monitoring configuration updated', newConfig);
  }
}

// Create singleton instance
export const apiMonitoring = new APIMonitoringService();

// Convenience wrapper for common HTTP methods
export const monitoredAPI = {
  get: (endpoint: string, headers?: Record<string, string>) =>
    apiMonitoring.monitoredFetch(endpoint, { method: 'GET', headers }),

  post: (endpoint: string, data?: any, headers?: Record<string, string>) =>
    apiMonitoring.monitoredFetch(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      headers,
    }),

  put: (endpoint: string, data?: any, headers?: Record<string, string>) =>
    apiMonitoring.monitoredFetch(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      headers,
    }),

  delete: (endpoint: string, headers?: Record<string, string>) =>
    apiMonitoring.monitoredFetch(endpoint, { method: 'DELETE', headers }),

  patch: (endpoint: string, data?: any, headers?: Record<string, string>) =>
    apiMonitoring.monitoredFetch(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
      headers,
    }),
};

export default apiMonitoring;