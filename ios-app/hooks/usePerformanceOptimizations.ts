import { useMemo, useCallback, useRef, useEffect, memo, useState } from 'react';
import { debounce, throttle } from 'lodash';

/**
 * Custom hook for memoizing expensive list transformations
 * with built-in performance tracking
 */
export const useMemoizedList = <T, R>(
  list: T[],
  transformer: (items: T[]) => R,
  deps: any[] = []
) => {
  const startTime = useRef(0);
  
  const memoizedResult = useMemo(() => {
    if (__DEV__) {
      startTime.current = performance.now();
    }
    
    const result = transformer(list);
    
    if (__DEV__) {
      const duration = performance.now() - startTime.current;
      if (duration > 16) { // More than one frame
        console.warn(`[Performance] List transformation took ${duration.toFixed(2)}ms`);
      }
    }
    
    return result;
  }, [list, ...deps]);

  return memoizedResult;
};

/**
 * Hook for creating optimized event handlers with debouncing/throttling
 */
export const useOptimizedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  deps: any[],
  options: {
    debounce?: number;
    throttle?: number;
    leading?: boolean;
    trailing?: boolean;
  } = {}
) => {
  const callbackRef = useRef(callback);
  
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const optimizedCallback = useMemo(() => {
    const fn = (...args: Parameters<T>) => callbackRef.current(...args);

    if (options.debounce) {
      return debounce(fn, options.debounce, {
        leading: options.leading ?? false,
        trailing: options.trailing ?? true,
      });
    }

    if (options.throttle) {
      return throttle(fn, options.throttle, {
        leading: options.leading ?? true,
        trailing: options.trailing ?? true,
      });
    }

    return fn;
  }, [options.debounce, options.throttle, options.leading, options.trailing]);

  return optimizedCallback as T;
};

/**
 * Hook for preventing unnecessary re-renders with deep comparison
 */
export const useDeepMemo = <T>(factory: () => T, deps: any[]): T => {
  const ref = useRef<{ deps: any[]; value: T }>();

  if (!ref.current || !deepEqual(deps, ref.current.deps)) {
    ref.current = { deps, value: factory() };
  }

  return ref.current.value;
};

/**
 * Component wrapper for memoization with custom comparison
 */
export const MemoizedComponent = memo(
  ({ component: Component, props, compareProps }: {
    component: React.ComponentType<any>;
    props: any;
    compareProps?: (prevProps: any, nextProps: any) => boolean;
  }) => <Component {...props} />,
  (prevProps, nextProps) => {
    if (prevProps.compareProps) {
      return prevProps.compareProps(prevProps.props, nextProps.props);
    }
    return shallowEqual(prevProps.props, nextProps.props);
  }
);

/**
 * Hook for batching multiple state updates
 */
export const useBatchedUpdates = () => {
  const pendingUpdates = useRef<Array<() => void>>([]);
  const rafId = useRef<number>();

  const batchUpdate = useCallback((update: () => void) => {
    pendingUpdates.current.push(update);

    if (rafId.current) {
      cancelAnimationFrame(rafId.current);
    }

    rafId.current = requestAnimationFrame(() => {
      const updates = [...pendingUpdates.current];
      pendingUpdates.current = [];
      
      updates.forEach(fn => fn());
    });
  }, []);

  useEffect(() => {
    return () => {
      if (rafId.current) {
        cancelAnimationFrame(rafId.current);
      }
    };
  }, []);

  return { batchUpdate };
};

/**
 * Hook for lazy loading components
 */
export const useLazyComponent = <T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: {
    preload?: boolean;
    placeholder?: React.ReactNode;
  } = {}
) => {
  const [Component, setComponent] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (options.preload) {
      setIsLoading(true);
      importFn()
        .then(module => {
          setComponent(() => module.default);
          setIsLoading(false);
        })
        .catch(err => {
          setError(err);
          setIsLoading(false);
        });
    }
  }, [options.preload]);

  const load = useCallback(async () => {
    if (Component) return Component;

    setIsLoading(true);
    try {
      const module = await importFn();
      const LoadedComponent = module.default;
      setComponent(() => LoadedComponent);
      return LoadedComponent;
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [Component]);

  return {
    Component,
    isLoading,
    error,
    load,
  };
};

// Helper functions
function shallowEqual(obj1: any, obj2: any): boolean {
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) {
    return false;
  }

  for (const key of keys1) {
    if (obj1[key] !== obj2[key]) {
      return false;
    }
  }

  return true;
}

function deepEqual(a: any, b: any): boolean {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (a.constructor !== b.constructor) return false;

  if (Array.isArray(a)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!deepEqual(a[i], b[i])) return false;
    }
    return true;
  }

  if (typeof a === 'object') {
    const keys = Object.keys(a);
    if (keys.length !== Object.keys(b).length) return false;
    for (const key of keys) {
      if (!deepEqual(a[key], b[key])) return false;
    }
    return true;
  }

  return false;
}