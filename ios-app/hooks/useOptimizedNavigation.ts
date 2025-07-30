import { useCallback, useRef, useEffect } from 'react';
import { InteractionManager } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useRouter } from 'expo-router';
import { performanceMonitor } from '../utils/performanceMonitoring';
import Animated, { cancelAnimation } from 'react-native-reanimated';

interface NavigationOptions {
  skipAnimation?: boolean;
  preload?: boolean;
  priority?: 'high' | 'normal' | 'low';
}

export const useOptimizedNavigation = () => {
  const navigation = useNavigation();
  const router = useRouter();
  const route = useRoute();
  const pendingNavigationRef = useRef<any>(null);
  const activeAnimationsRef = useRef<any[]>([]);

  // Cancel all active animations
  const cancelActiveAnimations = useCallback(() => {
    activeAnimationsRef.current.forEach(animation => {
      try {
        cancelAnimation(animation);
      } catch (error) {
        // Animation might already be cancelled
      }
    });
    activeAnimationsRef.current = [];
  }, []);

  // Register an animation to be cancelled on navigation
  const registerAnimation = useCallback((animation: any) => {
    activeAnimationsRef.current.push(animation);
    return () => {
      const index = activeAnimationsRef.current.indexOf(animation);
      if (index > -1) {
        activeAnimationsRef.current.splice(index, 1);
      }
    };
  }, []);

  // Optimized navigation function
  const navigateWithOptimization = useCallback(
    (screenName: string, params?: any, options: NavigationOptions = {}) => {
      const { skipAnimation = false, priority = 'normal' } = options;
      
      // Start performance measurement
      const perfLabel = `navigation-${route.name}-to-${screenName}`;
      performanceMonitor.startMeasure(perfLabel);

      // Cancel any pending navigation
      if (pendingNavigationRef.current) {
        cancelIdleCallback(pendingNavigationRef.current);
      }

      // Cancel active animations
      cancelActiveAnimations();

      const performNavigation = () => {
        try {
          // Use router.push for Expo Router navigation
          router.push({
            pathname: screenName as any,
            params,
          });

          // End performance measurement
          const duration = performanceMonitor.endMeasure(perfLabel);
          performanceMonitor.recordNavigation(route.name, screenName, duration);
        } catch (error) {
          console.error('[Navigation] Error during navigation:', error);
          performanceMonitor.endMeasure(perfLabel);
        }
      };

      if (skipAnimation || priority === 'high') {
        // Navigate immediately for high priority
        performNavigation();
      } else {
        // Defer navigation until interactions complete
        InteractionManager.runAfterInteractions(() => {
          // Use requestIdleCallback for low priority navigation
          if (priority === 'low' && 'requestIdleCallback' in window) {
            pendingNavigationRef.current = requestIdleCallback(performNavigation, {
              timeout: 500, // Fallback after 500ms
            });
          } else {
            performNavigation();
          }
        });
      }
    },
    [route.name, router, cancelActiveAnimations]
  );

  // Navigate back with optimization
  const goBackWithOptimization = useCallback(
    (options: NavigationOptions = {}) => {
      const perfLabel = `navigation-back-from-${route.name}`;
      performanceMonitor.startMeasure(perfLabel);

      cancelActiveAnimations();

      const performGoBack = () => {
        if (navigation.canGoBack()) {
          navigation.goBack();
        } else {
          router.back();
        }
        
        const duration = performanceMonitor.endMeasure(perfLabel);
        performanceMonitor.recordNavigation(route.name, 'back', duration);
      };

      if (options.skipAnimation) {
        performGoBack();
      } else {
        InteractionManager.runAfterInteractions(performGoBack);
      }
    },
    [navigation, router, route.name, cancelActiveAnimations]
  );

  // Preload a screen's data
  const preloadScreen = useCallback(
    async (screenName: string, dataLoader?: () => Promise<any>) => {
      if (!dataLoader) return;

      const perfLabel = `preload-${screenName}`;
      performanceMonitor.startMeasure(perfLabel);

      try {
        await dataLoader();
        performanceMonitor.endMeasure(perfLabel);
      } catch (error) {
        console.error(`[Navigation] Failed to preload ${screenName}:`, error);
        performanceMonitor.endMeasure(perfLabel);
      }
    },
    []
  );

  // Replace current screen (no back navigation)
  const replaceWithOptimization = useCallback(
    (screenName: string, params?: any, options: NavigationOptions = {}) => {
      const perfLabel = `navigation-replace-${route.name}-to-${screenName}`;
      performanceMonitor.startMeasure(perfLabel);

      cancelActiveAnimations();

      const performReplace = () => {
        router.replace({
          pathname: screenName as any,
          params,
        });
        
        const duration = performanceMonitor.endMeasure(perfLabel);
        performanceMonitor.recordNavigation(route.name, screenName, duration);
      };

      if (options.skipAnimation) {
        performReplace();
      } else {
        InteractionManager.runAfterInteractions(performReplace);
      }
    },
    [router, route.name, cancelActiveAnimations]
  );

  return {
    navigate: navigateWithOptimization,
    goBack: goBackWithOptimization,
    replace: replaceWithOptimization,
    preloadScreen,
    registerAnimation,
    cancelActiveAnimations,
    navigationPerformance: {
      getReport: () => performanceMonitor.getReport(),
      getAverageTime: () => performanceMonitor.getAverageNavigationTime(),
      clearHistory: () => performanceMonitor.clearHistory(),
    },
  };
};

// Hook to preload screens based on user behavior
export const useNavigationPreloader = (predictions: Array<{ screen: string; probability: number; loader?: () => Promise<any> }>) => {
  const { preloadScreen } = useOptimizedNavigation();

  useEffect(() => {
    // Sort by probability and preload top candidates
    const sortedPredictions = [...predictions].sort((a, b) => b.probability - a.probability);
    
    // Preload screens with >50% probability
    sortedPredictions
      .filter(p => p.probability > 0.5 && p.loader)
      .forEach(p => {
        // Delay preloading to avoid blocking initial render
        setTimeout(() => {
          preloadScreen(p.screen, p.loader);
        }, 1000);
      });
  }, [predictions, preloadScreen]);
};