import { useEffect, useRef, useCallback, useState } from 'react';
import { InteractionManager } from 'react-native';

interface DeferredOperationOptions {
  priority?: 'high' | 'normal' | 'low';
  timeout?: number;
  condition?: boolean;
}

/**
 * Hook to defer expensive operations until after interactions complete
 * Helps prevent janky animations during navigation
 */
export const useDeferredOperation = () => {
  const interactionHandles = useRef<any[]>([]);
  const timeoutHandles = useRef<NodeJS.Timeout[]>([]);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      interactionHandles.current.forEach(handle => handle.cancel());
      timeoutHandles.current.forEach(handle => clearTimeout(handle));
    };
  }, []);

  const runDeferred = useCallback(
    (operation: () => void | Promise<void>, options: DeferredOperationOptions = {}) => {
      const { priority = 'normal', timeout = 2000, condition = true } = options;

      if (!condition) return;

      if (priority === 'high') {
        // Run immediately for high priority
        operation();
        return;
      }

      // Defer operation
      const handle = InteractionManager.runAfterInteractions(() => {
        if (priority === 'low') {
          // Further defer low priority operations
          const timeoutHandle = setTimeout(operation, 100);
          timeoutHandles.current.push(timeoutHandle);
        } else {
          operation();
        }
      });

      interactionHandles.current.push(handle);

      // Fallback timeout to ensure operation runs
      const timeoutHandle = setTimeout(() => {
        handle.cancel();
        operation();
      }, timeout);
      
      timeoutHandles.current.push(timeoutHandle);
    },
    []
  );

  return { runDeferred };
};

/**
 * Hook to defer state updates until after interactions
 */
export const useDeferredState = <T>(initialValue: T, options?: DeferredOperationOptions) => {
  const [value, setValue] = useState(initialValue);
  const [pendingValue, setPendingValue] = useState<T | undefined>(undefined);
  const { runDeferred } = useDeferredOperation();

  useEffect(() => {
    if (pendingValue !== undefined) {
      runDeferred(() => {
        setValue(pendingValue);
        setPendingValue(undefined);
      }, options);
    }
  }, [pendingValue, runDeferred, options]);

  const setDeferredValue = useCallback((newValue: T) => {
    setPendingValue(newValue);
  }, []);

  return [value, setDeferredValue] as const;
};

/**
 * Hook to batch multiple operations and run them deferred
 */
export const useBatchedDeferredOperations = () => {
  const operations = useRef<Array<() => void | Promise<void>>>([]);
  const { runDeferred } = useDeferredOperation();
  const isProcessing = useRef(false);

  const addOperation = useCallback((operation: () => void | Promise<void>) => {
    operations.current.push(operation);
  }, []);

  const processBatch = useCallback((options?: DeferredOperationOptions) => {
    if (isProcessing.current || operations.current.length === 0) return;

    isProcessing.current = true;
    const batch = [...operations.current];
    operations.current = [];

    runDeferred(async () => {
      for (const operation of batch) {
        try {
          await operation();
        } catch (error) {
          console.error('[BatchedOperations] Operation failed:', error);
        }
      }
      isProcessing.current = false;
    }, options);
  }, [runDeferred]);

  return { addOperation, processBatch };
};

/**
 * Component wrapper that defers children rendering
 */
interface DeferredRenderProps {
  children: React.ReactNode;
  placeholder?: React.ReactNode;
  priority?: DeferredOperationOptions['priority'];
}

export const DeferredRender: React.FC<DeferredRenderProps> = ({ 
  children, 
  placeholder = null,
  priority = 'normal' 
}) => {
  const [shouldRender, setShouldRender] = useState(priority === 'high');
  const { runDeferred } = useDeferredOperation();

  useEffect(() => {
    if (!shouldRender) {
      runDeferred(() => setShouldRender(true), { priority });
    }
  }, [shouldRender, runDeferred, priority]);

  return <>{shouldRender ? children : placeholder}</>;
};