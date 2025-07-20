/**
 * useApiCall Hook
 * 
 * Provides standardized API call handling with loading states,
 * error handling, retry logic, and offline support.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { testEndpoint } from '../utils/connectivityValidator';

export interface ApiCallState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  retryCount: number;
}

export interface ApiCallOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: any;
  headers?: Record<string, string>;
  maxRetries?: number;
  retryDelay?: number;
  timeout?: number;
  skipRetryOn?: number[]; // HTTP status codes to not retry
}

export function useApiCall<T = any>(endpoint: string, options: ApiCallOptions = {}) {
  const [state, setState] = useState<ApiCallState<T>>({
    data: null,
    loading: false,
    error: null,
    retryCount: 0,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  const execute = useCallback(async (overrideOptions: Partial<ApiCallOptions> = {}) => {
    // Abort previous request if still running
    abortControllerRef.current?.abort();
    
    const mergedOptions = { ...options, ...overrideOptions };
    const {
      method = 'GET',
      body,
      headers = {},
      maxRetries = 3,
      skipRetryOn = [400, 401, 403, 404, 422],
    } = mergedOptions;

    if (!isMountedRef.current) return;

    setState(prev => ({
      ...prev,
      loading: true,
      error: null,
    }));

    try {
      const requestOptions: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
      };

      if (body && method !== 'GET') {
        requestOptions.body = JSON.stringify(body);
      }

      const result = await testEndpoint(endpoint, requestOptions, {
        maxRetries,
        baseDelay: mergedOptions.retryDelay || 1000,
      });

      if (!isMountedRef.current) return;

      if (result.success) {
        setState(prev => ({
          ...prev,
          data: result.data,
          loading: false,
          error: null,
        }));
      } else {
        setState(prev => ({
          ...prev,
          data: null,
          loading: false,
          error: result.error || 'Unknown error occurred',
          retryCount: prev.retryCount + 1,
        }));
      }
    } catch (error) {
      if (!isMountedRef.current) return;

      setState(prev => ({
        ...prev,
        data: null,
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        retryCount: prev.retryCount + 1,
      }));
    }
  }, [endpoint, options]);

  const retry = useCallback(() => {
    execute();
  }, [execute]);

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    setState({
      data: null,
      loading: false,
      error: null,
      retryCount: 0,
    });
  }, []);

  return {
    ...state,
    execute,
    retry,
    reset,
  };
}

/**
 * Hook specifically for pantry data with caching
 */
export function usePantryData(userId: number = 111) {
  const [cachedData, setCachedData] = useState<any[] | null>(null);
  const [cacheTimestamp, setCacheTimestamp] = useState<number | null>(null);
  
  const apiCall = useApiCall<any[]>(`/pantry/user/${userId}/items`);

  const fetchPantryData = useCallback(async (forceRefresh = false) => {
    const now = Date.now();
    const cacheAge = cacheTimestamp ? now - cacheTimestamp : Infinity;
    const cacheExpired = cacheAge > 5 * 60 * 1000; // 5 minutes

    // Use cached data if available and not expired
    if (!forceRefresh && cachedData && !cacheExpired) {
      return cachedData;
    }

    await apiCall.execute();
    
    if (apiCall.data) {
      setCachedData(apiCall.data);
      setCacheTimestamp(now);
    }

    return apiCall.data;
  }, [apiCall, cachedData, cacheTimestamp]);

  const clearCache = useCallback(() => {
    setCachedData(null);
    setCacheTimestamp(null);
  }, []);

  return {
    data: apiCall.data || cachedData,
    loading: apiCall.loading,
    error: apiCall.error,
    retryCount: apiCall.retryCount,
    fetchPantryData,
    retry: apiCall.retry,
    reset: apiCall.reset,
    clearCache,
    isCached: Boolean(cachedData && !apiCall.data),
    cacheAge: cacheTimestamp ? Date.now() - cacheTimestamp : null,
  };
}

/**
 * Hook for recipe search with intelligent retries
 */
export function useRecipeSearch() {
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  
  const pantrySearch = useApiCall('/recipes/search/from-pantry', {
    method: 'POST',
    maxRetries: 2,
  });

  const complexSearch = useApiCall('/recipes/search/complex', {
    method: 'POST',
    maxRetries: 2,
  });

  const randomRecipes = useApiCall('/recipes/random', {
    method: 'GET',
    maxRetries: 1,
  });

  const searchFromPantry = useCallback(async (params: {
    user_id: number;
    max_missing_ingredients?: number;
    use_expiring_first?: boolean;
  }) => {
    await pantrySearch.execute({ body: params });
    return pantrySearch.data;
  }, [pantrySearch]);

  const searchComplex = useCallback(async (query: string, filters: any = {}) => {
    const searchParams = { query, ...filters };
    await complexSearch.execute({ body: searchParams });
    
    // Add to search history
    if (query && !searchHistory.includes(query)) {
      setSearchHistory(prev => [query, ...prev.slice(0, 9)]); // Keep last 10 searches
    }
    
    return complexSearch.data;
  }, [complexSearch, searchHistory]);

  const getRandomRecipes = useCallback(async (count: number = 20) => {
    await randomRecipes.execute({ 
      method: 'GET',
      // Override endpoint with query parameter
    });
    return randomRecipes.data;
  }, [randomRecipes]);

  const clearSearchHistory = useCallback(() => {
    setSearchHistory([]);
  }, []);

  return {
    pantrySearch: {
      data: pantrySearch.data,
      loading: pantrySearch.loading,
      error: pantrySearch.error,
      execute: searchFromPantry,
      retry: pantrySearch.retry,
    },
    complexSearch: {
      data: complexSearch.data,
      loading: complexSearch.loading,
      error: complexSearch.error,
      execute: searchComplex,
      retry: complexSearch.retry,
    },
    randomRecipes: {
      data: randomRecipes.data,
      loading: randomRecipes.loading,
      error: randomRecipes.error,
      execute: getRandomRecipes,
      retry: randomRecipes.retry,
    },
    searchHistory,
    clearSearchHistory,
  };
}