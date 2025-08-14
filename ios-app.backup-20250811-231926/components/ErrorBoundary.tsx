/**
 * Enhanced Error Boundary Component with Sentry Integration
 * 
 * Provides user-friendly error states when API calls fail and
 * comprehensive error reporting to Sentry
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as Sentry from '@sentry/react-native';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  componentName?: string; // For better Sentry context
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  private resetTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Store errorInfo in state
    this.setState({ errorInfo });

    // Enhanced Sentry reporting
    Sentry.withScope((scope) => {
      // Add component context
      scope.setTag('errorBoundary', true);
      scope.setTag('component', this.props.componentName || 'unknown');
      scope.setLevel('fatal');
      
      // Add error boundary context
      scope.setContext('errorBoundary', {
        componentStack: errorInfo.componentStack,
        componentName: this.props.componentName,
      });

      // Add breadcrumb
      Sentry.addBreadcrumb({
        message: 'Error boundary triggered',
        level: 'error',
        data: {
          errorMessage: error.message,
          componentName: this.props.componentName,
        },
      });

      // Capture exception
      Sentry.captureException(error);
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      try {
        this.props.onError(error, errorInfo);
      } catch (handlerError) {
        console.error('Error in custom error handler:', handlerError);
        Sentry.captureException(handlerError);
      }
    }
  }

  handleRetry = () => {
    // Clear any existing timeout
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }

    // Add breadcrumb for retry attempt
    Sentry.addBreadcrumb({
      message: 'User triggered error boundary reset',
      level: 'info',
      data: {
        previousError: this.state.error?.message,
        componentName: this.props.componentName,
      },
    });

    this.setState({ hasError: false, error: undefined, errorInfo: undefined });

    // Set timeout to detect recurring errors
    this.resetTimeoutId = setTimeout(() => {
      if (this.state.hasError) {
        Sentry.captureMessage(
          'Error boundary error recurred after reset',
          'warning'
        );
      }
    }, 5000);
  };

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <View style={styles.container}>
          <MaterialCommunityIcons name="alert-circle" size={64} color="#f44336" />
          <Text style={styles.title}>Oops! Something went wrong</Text>
          <Text style={styles.message}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </Text>
          <Text style={styles.subtitle}>
            We've been notified and are working to fix this issue.
          </Text>
          
          {__DEV__ && this.state.errorInfo && (
            <View style={styles.debugContainer}>
              <Text style={styles.debugTitle}>Debug Info:</Text>
              <Text style={styles.debugText}>
                {this.state.errorInfo.componentStack?.slice(0, 300)}...
              </Text>
            </View>
          )}

          <TouchableOpacity style={styles.retryButton} onPress={this.handleRetry}>
            <Text style={styles.retryText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component for easier usage with automatic component naming
 */
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children' | 'componentName'>
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary 
      {...errorBoundaryProps}
      componentName={Component.displayName || Component.name}
    >
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

/**
 * Network Error Component with Sentry integration
 * Shows specific UI for network connectivity issues
 */
interface NetworkErrorProps {
  onRetry: () => void;
  message?: string;
  reportToSentry?: boolean;
}

export function NetworkError({ onRetry, message, reportToSentry = true }: NetworkErrorProps) {
  React.useEffect(() => {
    if (reportToSentry) {
      Sentry.addBreadcrumb({
        message: 'Network error displayed',
        level: 'warning',
        data: {
          errorMessage: message,
        },
      });

      Sentry.captureMessage(
        `Network connectivity issue: ${message || 'Unknown network error'}`,
        'warning'
      );
    }
  }, [message, reportToSentry]);

  const handleRetry = () => {
    Sentry.addBreadcrumb({
      message: 'User triggered network retry',
      level: 'info',
    });
    onRetry();
  };

  return (
    <View style={styles.container}>
      <MaterialCommunityIcons name="wifi-off" size={64} color="#ff9800" />
      <Text style={styles.title}>Connection Problem</Text>
      <Text style={styles.message}>
        {message || 'Unable to connect to PrepSense services. Please check your internet connection.'}
      </Text>
      <TouchableOpacity style={styles.retryButton} onPress={handleRetry}>
        <Text style={styles.retryText}>Retry Connection</Text>
      </TouchableOpacity>
    </View>
  );
}

/**
 * Loading Error Component with Sentry integration
 * Shows when data fails to load
 */
interface LoadingErrorProps {
  onRetry: () => void;
  title?: string;
  message?: string;
  reportToSentry?: boolean;
}

export function LoadingError({ onRetry, title, message, reportToSentry = true }: LoadingErrorProps) {
  React.useEffect(() => {
    if (reportToSentry) {
      Sentry.addBreadcrumb({
        message: 'Loading error displayed',
        level: 'warning',
        data: {
          title,
          errorMessage: message,
        },
      });

      Sentry.captureMessage(
        `Loading error: ${title || 'Data loading failed'} - ${message || 'Unknown error'}`,
        'warning'
      );
    }
  }, [title, message, reportToSentry]);

  const handleRetry = () => {
    Sentry.addBreadcrumb({
      message: 'User triggered loading retry',
      level: 'info',
    });
    onRetry();
  };

  return (
    <View style={styles.container}>
      <MaterialCommunityIcons name="reload" size={64} color="#2196f3" />
      <Text style={styles.title}>{title || 'Failed to Load'}</Text>
      <Text style={styles.message}>
        {message || 'Something went wrong while loading data.'}
      </Text>
      <TouchableOpacity style={styles.retryButton} onPress={handleRetry}>
        <Text style={styles.retryText}>Try Again</Text>
      </TouchableOpacity>
    </View>
  );
}

/**
 * Empty State Component
 * Shows when no data is available
 */
interface EmptyStateProps {
  icon?: string;
  title: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
}

export function EmptyState({ icon, title, message, actionText, onAction }: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <MaterialCommunityIcons 
        name={icon as any || "information-outline"} 
        size={64} 
        color="#9e9e9e" 
      />
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
      {onAction && actionText && (
        <TouchableOpacity style={styles.actionButton} onPress={onAction}>
          <Text style={styles.actionText}>{actionText}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    backgroundColor: '#f9fafb',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
    color: '#333',
  },
  message: {
    fontSize: 16,
    textAlign: 'center',
    color: '#666',
    marginBottom: 8,
    lineHeight: 24,
  },
  subtitle: {
    fontSize: 14,
    textAlign: 'center',
    color: '#888',
    marginBottom: 24,
    lineHeight: 20,
  },
  debugContainer: {
    backgroundColor: '#fff3cd',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    width: '100%',
  },
  debugTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#856404',
    marginBottom: 4,
  },
  debugText: {
    fontSize: 10,
    color: '#856404',
    fontFamily: 'monospace',
  },
  retryButton: {
    backgroundColor: '#297A56',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  retryText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  actionButton: {
    backgroundColor: '#2196f3',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  actionText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});