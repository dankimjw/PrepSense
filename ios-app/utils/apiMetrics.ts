/**
 * API Metrics Tracker for Development
 * Tracks and displays API usage statistics
 */

interface APICall {
  endpoint: string;
  timestamp: Date;
  duration?: number;
  status?: 'success' | 'error';
  errorMessage?: string;
  responseSize?: number;
}

interface MetricsSummary {
  totalCalls: number;
  successfulCalls: number;
  failedCalls: number;
  averageResponseTime: number;
  endpointBreakdown: Record<string, number>;
  lastHourCalls: number;
  sessionStartTime: Date;
  sessionDuration: string;
}

class APIMetrics {
  private calls: APICall[] = [];
  private sessionStart: Date = new Date();
  private displayInterval: NodeJS.Timeout | null = null;

  constructor() {
    // Display metrics every 30 seconds in development
    if (__DEV__) {
      this.startPeriodicDisplay();
    }
  }

  /**
   * Track an API call
   */
  trackCall(endpoint: string): { endTimer: (status: 'success' | 'error', error?: string) => void } {
    const startTime = Date.now();
    const call: APICall = {
      endpoint,
      timestamp: new Date(),
    };

    return {
      endTimer: (status: 'success' | 'error', error?: string) => {
        call.duration = Date.now() - startTime;
        call.status = status;
        if (error) call.errorMessage = error;
        
        this.calls.push(call);
        
        // Log immediately in dev mode
        if (__DEV__) {
          this.logCall(call);
        }
      }
    };
  }

  /**
   * Log a single call with color coding
   */
  private logCall(call: APICall): void {
    const statusEmoji = call.status === 'success' ? '✅' : '❌';
    const duration = call.duration ? `${call.duration}ms` : 'N/A';
    
    console.log(
      `${statusEmoji} API Call: ${call.endpoint} | ${duration} | ${call.timestamp.toLocaleTimeString()}`
    );
    
    if (call.errorMessage) {
      console.error(`   └─ Error: ${call.errorMessage}`);
    }
  }

  /**
   * Get current metrics summary
   */
  getSummary(): MetricsSummary {
    const now = Date.now();
    const oneHourAgo = now - 3600000;
    
    const successfulCalls = this.calls.filter(c => c.status === 'success').length;
    const failedCalls = this.calls.filter(c => c.status === 'error').length;
    
    const durations = this.calls.filter(c => c.duration).map(c => c.duration!);
    const averageResponseTime = durations.length > 0
      ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length)
      : 0;
    
    const endpointBreakdown: Record<string, number> = {};
    this.calls.forEach(call => {
      endpointBreakdown[call.endpoint] = (endpointBreakdown[call.endpoint] || 0) + 1;
    });
    
    const lastHourCalls = this.calls.filter(
      c => c.timestamp.getTime() > oneHourAgo
    ).length;
    
    const sessionDuration = this.formatDuration(now - this.sessionStart.getTime());
    
    return {
      totalCalls: this.calls.length,
      successfulCalls,
      failedCalls,
      averageResponseTime,
      endpointBreakdown,
      lastHourCalls,
      sessionStartTime: this.sessionStart,
      sessionDuration,
    };
  }

  /**
   * Display formatted metrics in console
   */
  displayMetrics(): void {
    const summary = this.getSummary();
    
    console.log('\n' + '='.repeat(60));
    console.log('📊 API METRICS DASHBOARD');
    console.log('='.repeat(60));
    console.log(`📅 Session: ${summary.sessionDuration} (started ${summary.sessionStartTime.toLocaleTimeString()})`);
    console.log(`📈 Total API Calls: ${summary.totalCalls}`);
    console.log(`   ├─ ✅ Successful: ${summary.successfulCalls}`);
    console.log(`   └─ ❌ Failed: ${summary.failedCalls}`);
    console.log(`⏱️  Avg Response Time: ${summary.averageResponseTime}ms`);
    console.log(`🕐 Last Hour: ${summary.lastHourCalls} calls`);
    
    if (Object.keys(summary.endpointBreakdown).length > 0) {
      console.log('\n📍 Endpoint Breakdown:');
      Object.entries(summary.endpointBreakdown)
        .sort((a, b) => b[1] - a[1])
        .forEach(([endpoint, count]) => {
          const percentage = ((count / summary.totalCalls) * 100).toFixed(1);
          console.log(`   • ${endpoint}: ${count} calls (${percentage}%)`);
        });
    }
    
    // Performance warnings
    if (summary.averageResponseTime > 3000) {
      console.warn('⚠️  Warning: High average response time detected!');
    }
    if (summary.failedCalls > summary.successfulCalls * 0.1) {
      console.warn('⚠️  Warning: High error rate detected (>10%)!');
    }
    
    console.log('='.repeat(60) + '\n');
  }

  /**
   * Start periodic display of metrics
   */
  private startPeriodicDisplay(): void {
    // Display every 30 seconds
    this.displayInterval = setInterval(() => {
      if (this.calls.length > 0) {
        this.displayMetrics();
      }
    }, 30000);
    
    // Also display on app startup
    setTimeout(() => {
      console.log('🚀 API Metrics tracking started. Metrics will display every 30 seconds.');
    }, 1000);
  }

  /**
   * Format duration in human-readable format
   */
  private formatDuration(ms: number): string {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  /**
   * Clear all metrics
   */
  reset(): void {
    this.calls = [];
    this.sessionStart = new Date();
    console.log('🔄 API Metrics reset');
  }

  /**
   * Get metrics for display in UI (optional)
   */
  getQuickStats(): { total: number; success: number; failed: number; avgTime: string } {
    const summary = this.getSummary();
    return {
      total: summary.totalCalls,
      success: summary.successfulCalls,
      failed: summary.failedCalls,
      avgTime: `${summary.averageResponseTime}ms`,
    };
  }

  /**
   * Export metrics to JSON (for debugging)
   */
  exportMetrics(): string {
    return JSON.stringify({
      summary: this.getSummary(),
      calls: this.calls,
    }, null, 2);
  }
}

// Singleton instance
export const apiMetrics = new APIMetrics();

// Make it available globally in dev mode
if (__DEV__) {
  (global as any).apiMetrics = apiMetrics;
  console.log('💡 Tip: Access API metrics anytime with: apiMetrics.displayMetrics()');
}