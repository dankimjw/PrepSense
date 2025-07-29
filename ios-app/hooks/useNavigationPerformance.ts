import { useEffect, useRef } from 'react';
import { usePathname, useSegments } from 'expo-router';
import { useNavigationState } from '@react-navigation/native';
import { performanceMonitor } from '../utils/performanceMonitoring';

interface NavigationMetrics {
  screenName: string;
  renderTime: number;
  transitionTime: number;
  totalTime: number;
  timestamp: number;
}

export const useNavigationPerformance = (screenName?: string) => {
  const pathname = usePathname();
  const segments = useSegments();
  const navigationState = useNavigationState(state => state);
  
  const mountTime = useRef(performance.now());
  const transitionStartTime = useRef(0);
  const lastPathname = useRef(pathname);
  const metricsHistory = useRef<NavigationMetrics[]>([]);

  // Detect navigation start
  useEffect(() => {
    if (pathname !== lastPathname.current) {
      transitionStartTime.current = performance.now();
      const fromScreen = lastPathname.current || 'unknown';
      const toScreen = pathname;
      
      performanceMonitor.startMeasure(`nav-transition-${fromScreen}-to-${toScreen}`);
      
      if (__DEV__) {
        console.log(`[Navigation] Starting transition: ${fromScreen} → ${toScreen}`);
      }
    }
  }, [pathname]);

  // Track screen render completion
  useEffect(() => {
    const renderEndTime = performance.now();
    const renderDuration = renderEndTime - mountTime.current;
    
    const currentScreen = screenName || pathname || segments.join('/');
    performanceMonitor.endMeasure(`screen-render-${currentScreen}`);
    
    if (transitionStartTime.current > 0) {
      const transitionDuration = renderEndTime - transitionStartTime.current;
      const fromScreen = lastPathname.current || 'unknown';
      const toScreen = pathname;
      
      performanceMonitor.endMeasure(`nav-transition-${fromScreen}-to-${toScreen}`);
      performanceMonitor.recordNavigation(fromScreen, toScreen, transitionDuration);
      
      // Record metrics
      const metrics: NavigationMetrics = {
        screenName: currentScreen,
        renderTime: renderDuration,
        transitionTime: transitionDuration,
        totalTime: transitionDuration + renderDuration,
        timestamp: Date.now(),
      };
      
      metricsHistory.current.push(metrics);
      
      // Keep only last 20 metrics
      if (metricsHistory.current.length > 20) {
        metricsHistory.current.shift();
      }
      
      // Log slow transitions
      if (transitionDuration > 500) {
        console.warn(
          `[Performance] Slow navigation detected:\n` +
          `  Route: ${fromScreen} → ${toScreen}\n` +
          `  Transition: ${transitionDuration.toFixed(0)}ms\n` +
          `  Render: ${renderDuration.toFixed(0)}ms\n` +
          `  Total: ${(transitionDuration + renderDuration).toFixed(0)}ms`
        );
      }
      
      transitionStartTime.current = 0;
    }
    
    lastPathname.current = pathname;
  }, [pathname, screenName, segments]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      const currentScreen = screenName || pathname || segments.join('/');
      performanceMonitor.endMeasure(`screen-render-${currentScreen}`);
    };
  }, []);

  return {
    getMetrics: () => metricsHistory.current,
    getAverageTransitionTime: () => {
      if (metricsHistory.current.length === 0) return 0;
      const sum = metricsHistory.current.reduce((acc, m) => acc + m.transitionTime, 0);
      return sum / metricsHistory.current.length;
    },
    getAverageRenderTime: () => {
      if (metricsHistory.current.length === 0) return 0;
      const sum = metricsHistory.current.reduce((acc, m) => acc + m.renderTime, 0);
      return sum / metricsHistory.current.length;
    },
    reportPerformance: () => {
      const avgTransition = metricsHistory.current.reduce((acc, m) => acc + m.transitionTime, 0) / metricsHistory.current.length;
      const avgRender = metricsHistory.current.reduce((acc, m) => acc + m.renderTime, 0) / metricsHistory.current.length;
      
      console.log(
        `\n📊 Navigation Performance Report:\n` +
        `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
        `Total navigations: ${metricsHistory.current.length}\n` +
        `Average transition time: ${avgTransition.toFixed(0)}ms\n` +
        `Average render time: ${avgRender.toFixed(0)}ms\n` +
        `Average total time: ${(avgTransition + avgRender).toFixed(0)}ms\n` +
        `\nRecent navigations:\n` +
        metricsHistory.current.slice(-5).map(m => 
          `  • ${m.screenName}: ${m.totalTime.toFixed(0)}ms (transition: ${m.transitionTime.toFixed(0)}ms, render: ${m.renderTime.toFixed(0)}ms)`
        ).join('\n') +
        `\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`
      );
    },
  };
};

// Global hook to track app-wide navigation performance
let globalPerformanceTracker: ReturnType<typeof useNavigationPerformance> | null = null;

export const useGlobalNavigationPerformance = () => {
  const tracker = useNavigationPerformance('global');
  
  useEffect(() => {
    globalPerformanceTracker = tracker;
  }, [tracker]);
  
  return tracker;
};

// Export function to get performance report
export const getNavigationPerformanceReport = () => {
  if (globalPerformanceTracker) {
    return globalPerformanceTracker.reportPerformance();
  }
  return performanceMonitor.getReport();
};