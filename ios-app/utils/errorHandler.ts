// utils/errorHandler.ts - Centralized error handling for PrepSense

/**
 * Silent error handler that suppresses console errors in production
 * while maintaining error tracking capabilities
 */
class ErrorHandler {
  private isDev: boolean;
  private suppressedErrors: Set<string>;

  constructor() {
    this.isDev = __DEV__;
    this.suppressedErrors = new Set();
  }

  /**
   * Log an error (only in development)
   */
  logError(context: string, error: any, details?: any) {
    if (this.isDev) {
      console.error(`[${context}]`, error, details);
    }
    // In production, errors are silently tracked but not displayed
    this.trackError(context, error, details);
  }

  /**
   * Log a warning (only in development)
   */
  logWarning(context: string, message: string, details?: any) {
    if (this.isDev) {
      console.warn(`[${context}]`, message, details);
    }
  }

  /**
   * Log info (only in development)
   */
  logInfo(context: string, message: string, details?: any) {
    if (this.isDev) {
      console.info(`[${context}]`, message, details);
    }
  }

  /**
   * Track errors for analytics (without displaying them)
   */
  private trackError(context: string, error: any, details?: any) {
    const errorKey = `${context}:${error?.message || error}`;
    
    // Avoid tracking the same error multiple times
    if (this.suppressedErrors.has(errorKey)) {
      return;
    }
    
    this.suppressedErrors.add(errorKey);
    
    // Here you could send errors to an analytics service
    // For now, we just silently track them
  }

  /**
   * Wrap an async function to handle errors gracefully
   */
  wrapAsync<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    context: string,
    fallbackValue?: any
  ): T {
    return (async (...args: Parameters<T>) => {
      try {
        return await fn(...args);
      } catch (error) {
        this.logError(context, error);
        return fallbackValue;
      }
    }) as T;
  }

  /**
   * Wrap a sync function to handle errors gracefully
   */
  wrapSync<T extends (...args: any[]) => any>(
    fn: T,
    context: string,
    fallbackValue?: any
  ): T {
    return ((...args: Parameters<T>) => {
      try {
        return fn(...args);
      } catch (error) {
        this.logError(context, error);
        return fallbackValue;
      }
    }) as T;
  }
}

// Export singleton instance
export const errorHandler = new ErrorHandler();

// Convenience exports
export const logError = errorHandler.logError.bind(errorHandler);
export const logWarning = errorHandler.logWarning.bind(errorHandler);
export const logInfo = errorHandler.logInfo.bind(errorHandler);
export const wrapAsync = errorHandler.wrapAsync.bind(errorHandler);
export const wrapSync = errorHandler.wrapSync.bind(errorHandler);