import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { Config } from '../config';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_admin: boolean;
}

interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  getAuthHeader: () => Promise<{ Authorization: string } | undefined>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'user_data';

// Default user for prototype - Samantha Smith (admin user)
// TODO: Remove this when implementing real authentication
const DEFAULT_USER: User = {
  id: 'samantha-smith-001',
  email: 'samantha.smith@prepsense.com',
  first_name: 'Samantha',
  last_name: 'Smith',
  is_admin: true,
};

// Mock token for prototype
// TODO: Remove this when implementing real authentication
const MOCK_TOKEN = 'mock-admin-token-for-prototype';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  });

  // Load default user for prototype (no real authentication)
  // TODO: Replace with real authentication when backend is ready
  useEffect(() => {
    const loadDefaultUser = async () => {
      try {
        // For prototype: automatically set Samantha Smith as authenticated user
        setAuthState({
          user: DEFAULT_USER,
          token: MOCK_TOKEN,
          isLoading: false,
          isAuthenticated: true,
        });
      } catch (error) {
        console.error('Error loading default user:', error);
        setAuthState({
          user: null,
          token: null,
          isLoading: false,
          isAuthenticated: false,
        });
      }
    };

    loadDefaultUser();
  }, []);

  // Mock sign in function for prototype
  // TODO: Implement real authentication when backend is ready
  const signIn = async (email: string, password: string): Promise<void> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));

      // For prototype: always succeed with Samantha Smith
      setAuthState({
        user: DEFAULT_USER,
        token: MOCK_TOKEN,
        isLoading: false,
        isAuthenticated: true,
      });

      // TODO: Replace with real API call when backend is ready
      // const response = await fetch(`${Config.API_BASE_URL}/auth/login`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ email, password }),
      // });
      
      // if (!response.ok) {
      //   throw new Error('Login failed');
      // }
      
      // const data = await response.json();
      // await Promise.all([
      //   SecureStore.setItemAsync(TOKEN_KEY, data.token),
      //   SecureStore.setItemAsync(USER_KEY, JSON.stringify(data.user)),
      // ]);
      
      // setAuthState({
      //   user: data.user,
      //   token: data.token,
      //   isLoading: false,
      //   isAuthenticated: true,
      // });
    } catch (error) {
      console.error('Sign in error:', error);
      setAuthState({
        user: null,
        token: null,
        isLoading: false,
        isAuthenticated: false,
      });
      throw error;
    }
  };

  // Mock sign out function for prototype
  // TODO: Implement real sign out when authentication is added
  const signOut = async (): Promise<void> => {
    try {
      // For prototype: just reset to default user
      await Promise.all([
        SecureStore.deleteItemAsync(TOKEN_KEY).catch(() => {}),
        SecureStore.deleteItemAsync(USER_KEY).catch(() => {}),
      ]);

      // Reset to default user for prototype
      setAuthState({
        user: DEFAULT_USER,
        token: MOCK_TOKEN,
        isLoading: false,
        isAuthenticated: true,
      });

      // TODO: When real auth is implemented, call logout API and set to unauthenticated state
      // setAuthState({
      //   user: null,
      //   token: null,
      //   isLoading: false,
      //   isAuthenticated: false,
      // });
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  // Get authentication header for API calls
  // TODO: Update when implementing real authentication
  const getAuthHeader = async (): Promise<{ Authorization: string } | undefined> => {
    const { token } = authState;
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
    return undefined;
  };

  const contextValue: AuthContextType = {
    ...authState,
    signIn,
    signOut,
    getAuthHeader,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
