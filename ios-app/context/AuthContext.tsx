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

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  });

  // Load token and user from secure storage on initial load
  useEffect(() => {
    const loadAuthData = async () => {
      try {
        const [token, userData] = await Promise.all([
          SecureStore.getItemAsync(TOKEN_KEY),
          SecureStore.getItemAsync(USER_KEY),
        ]);

        if (token && userData) {
          setAuthState({
            user: JSON.parse(userData),
            token,
            isLoading: false,
            isAuthenticated: true,
          });
        } else {
          setAuthState(prev => ({ ...prev, isLoading: false }));
        }
      } catch (error) {
        console.error('Failed to load auth data', error);
        setAuthState(prev => ({ ...prev, isLoading: false }));
      }
    };

    loadAuthData();
  }, []);

  const signIn = async (email: string, password: string) => {
    try {
      const response = await fetch(`${Config.API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sign in');
      }

      const { access_token, user } = await response.json();
      
      // Store the token and user data
      await Promise.all([
        SecureStore.setItemAsync(TOKEN_KEY, access_token),
        SecureStore.setItemAsync(USER_KEY, JSON.stringify(user)),
      ]);
      
      setAuthState({
        user,
        token: access_token,
        isLoading: false,
        isAuthenticated: true,
      });
    } catch (error) {
      console.error('Sign in error:', error);
      // Fallback to mock data if API is not available
      if (__DEV__) {
        console.log('Falling back to mock user data');
        const mockUser = {
          id: '1',
          email: 'samantha.smith@example.com',
          first_name: 'Samantha',
          last_name: 'Smith',
          is_admin: true,
        };
        
        const mockToken = 'mock-jwt-token';
        
        await Promise.all([
          SecureStore.setItemAsync(TOKEN_KEY, mockToken),
          SecureStore.setItemAsync(USER_KEY, JSON.stringify(mockUser)),
        ]);
        
        setAuthState({
          user: mockUser,
          token: mockToken,
          isLoading: false,
          isAuthenticated: true,
        });
        return;
      }
      throw error;
    }
  };

  const signOut = async () => {
    try {
      await Promise.all([
        SecureStore.deleteItemAsync(TOKEN_KEY),
        SecureStore.deleteItemAsync(USER_KEY),
      ]);
      
      setAuthState({
        user: null,
        token: null,
        isLoading: false,
        isAuthenticated: false,
      });
    } catch (error) {
      console.error('Sign out error:', error);
      throw new Error('Failed to sign out');
    }
  };

  const getAuthHeader = async () => {
    // First try to use the in-memory token if available
    if (authState.token) {
      return { Authorization: `Bearer ${authState.token}` };
    }
    
    // Fall back to secure storage if needed
    const token = await SecureStore.getItemAsync(TOKEN_KEY);
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
    return undefined;
  };

  return (
    <AuthContext.Provider
      value={{
        ...authState,
        signIn,
        signOut,
        getAuthHeader,
      }}
    >
      {!authState.isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
