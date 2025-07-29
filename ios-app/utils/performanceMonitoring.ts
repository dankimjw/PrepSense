import { useEffect } from 'react';

export class NavigationPerformanceMonitor {
  private static instance: NavigationPerformanceMonitor;
  private metrics: Map<string, number> = new Map();
  private navigationHistory: Array<{
    from: string;
    to: string;
    duration: number;
    timestamp: number;
  }> = [];

  private constructor() {}

  static getInstance(): NavigationPerformanceMonitor {
    if (!NavigationPerformanceMonitor.instance) {
      NavigationPerformanceMonitor.instance = new NavigationPerformanceMonitor();
    }
    return NavigationPerformanceMonitor.instance;
  }

  startMeasure(label: string): void {
    this.metrics.set(label, performance.now());
  }

  endMeasure(label: string): number {
    const start = this.metrics.get(label);
    if (!start) {
      console.warn(`[Performance] No start time found for label: ${label}`);
      return 0;
    }

    const duration = performance.now() - start;
    this.metrics.delete(label);
    
    if (__DEV__) {
      const durationColor = duration < 200 ? '\x1b[32m' : duration < 500 ? '\x1b[33m' : '\x1b[31m';
      console.log(`[Performance] ${label}: ${durationColor}${duration.toFixed(2)}ms\x1b[0m`);
    }
    
    return duration;
  }

  recordNavigation(from: string, to: string, duration: number): void {
    this.navigationHistory.push({
      from,
      to,
      duration,
      timestamp: Date.now(),
    });

    // Keep only last 50 navigations
    if (this.navigationHistory.length > 50) {
      this.navigationHistory.shift();
    }

    // Warn if navigation takes too long
    if (duration > 500) {
      console.warn(`[Performance] Slow navigation detected: ${from} → ${to} took ${duration.toFixed(2)}ms`);
    }
  }

  getAverageNavigationTime(): number {
    if (this.navigationHistory.length === 0) return 0;
    const total = this.navigationHistory.reduce((sum, nav) => sum + nav.duration, 0);
    return total / this.navigationHistory.length;
  }

  getSlowNavigations(threshold = 500): Array<{ from: string; to: string; duration: number }> {
    return this.navigationHistory
      .filter(nav => nav.duration > threshold)
      .map(({ from, to, duration }) => ({ from, to, duration }));
  }

  clearHistory(): void {
    this.navigationHistory = [];
  }

  getReport(): string {
    const avgTime = this.getAverageNavigationTime();
    const slowNavs = this.getSlowNavigations();
    
    return `
Navigation Performance Report:
- Total navigations: ${this.navigationHistory.length}
- Average navigation time: ${avgTime.toFixed(2)}ms
- Slow navigations (>500ms): ${slowNavs.length}
${slowNavs.map(nav => `  - ${nav.from} → ${nav.to}: ${nav.duration.toFixed(2)}ms`).join('\n')}
    `.trim();
  }
}

// Helper hook for component performance monitoring
export const useComponentPerformance = (componentName: string) => {
  const monitor = NavigationPerformanceMonitor.getInstance();
  
  useEffect(() => {
    monitor.startMeasure(`${componentName}-mount`);
    
    return () => {
      const mountTime = monitor.endMeasure(`${componentName}-mount`);
      if (mountTime > 100) {
        console.warn(`[Performance] ${componentName} took ${mountTime.toFixed(2)}ms to mount`);
      }
    };
  }, [componentName]);
};

// Measure async operations
export const measureAsync = async <T>(
  label: string,
  operation: () => Promise<T>
): Promise<T> => {
  const monitor = NavigationPerformanceMonitor.getInstance();
  monitor.startMeasure(label);
  
  try {
    const result = await operation();
    const duration = monitor.endMeasure(label);
    
    if (duration > 1000) {
      console.warn(`[Performance] Async operation "${label}" took ${duration.toFixed(2)}ms`);
    }
    
    return result;
  } catch (error) {
    monitor.endMeasure(label);
    throw error;
  }
};

// Export singleton instance
export const performanceMonitor = NavigationPerformanceMonitor.getInstance();