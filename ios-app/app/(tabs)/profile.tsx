// app/(tabs)/profile.tsx - Part of the PrepSense mobile app
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { router } from 'expo-router';
import { Config } from '../../config';

interface UserProfilePreference {
  household_size?: number | null;
  dietary_preference?: string | null;
  allergens?: string[] | null;
  cuisine_preference?: string | null;
  preference_created_at?: string | null; 
}

interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_admin: boolean;
  user_created_at: string;
  user_updated_at: string;
  password_hash: string;
  role: string;
  api_key_enc: string;
  preferences?: UserProfilePreference | null;
}

export default function ProfileScreen() {
  const { user: authUser, isLoading: isAuthLoading, signOut, token } = useAuth();
  const [userProfileData, setUserProfileData] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch the latest user data when the component mounts
  useEffect(() => {
    const fetchUserData = async () => {
      if (!authUser?.id || !token) {
        setIsLoading(false);
        return;
      }
      
      try {
        setIsLoading(true);
        const response = await fetch(`${Config.API_BASE_URL}/users/${authUser.id}/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }
        
        const userData = await response.json();
        setUserProfileData(userData);
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to load user data. Using cached data.');
        // Fall back to the user data from auth context if available (basic info only)
        if (authUser) {
          setUserProfileData({
            ...authUser,
            user_created_at: '', // These fields won't be in authUser
            user_updated_at: '', // These fields won't be in authUser
            preferences: null,
            password_hash: '', // Add missing required fields
            role: authUser.is_admin ? 'admin' : 'user',
            api_key_enc: ''
          });
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchUserData();
  }, [authUser?.id, token]);
  
  const handleSignOut = async () => {
    try {
      await signOut();
      router.replace('/(auth)/sign-in');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  if (isLoading || isAuthLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text>Loading user data...</Text>
      </View>
    );
  }

  if (!userProfileData) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Text style={styles.errorText}>
          {error || 'No user data available. Please sign in.'}
        </Text>
        <TouchableOpacity 
          style={[styles.button, { marginTop: 20 }]} 
          onPress={() => router.replace('/(auth)/sign-in')}
        >
          <Text style={styles.buttonText}>Go to Sign In</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.profileHeader}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {userProfileData.first_name ? userProfileData.first_name[0] : ''}{userProfileData.last_name ? userProfileData.last_name[0] : ''}
          </Text>
        </View>
        <Text style={styles.name}>
          {userProfileData.first_name} {userProfileData.last_name}
        </Text>
        <Text style={styles.email}>{userProfileData.email}</Text>
        {userProfileData.is_admin && (
          <View style={styles.adminBadge}>
            <Text style={styles.adminText}>Administrator</Text>
          </View>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account Information</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>User ID</Text>
          <Text style={styles.infoValue} numberOfLines={1} ellipsizeMode="tail">
            {userProfileData.id}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Username</Text>
          <Text style={styles.infoValue}>
            {userProfileData.first_name.toLowerCase()}_{userProfileData.last_name.toLowerCase()}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Email</Text>
          <Text style={styles.infoValue}>{userProfileData.email}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Role</Text>
          <Text style={styles.infoValue}>
            {userProfileData.is_admin ? 'Administrator' : 'Standard User'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>API Key</Text>
          <Text style={styles.infoValue} numberOfLines={1} ellipsizeMode="tail">
            {userProfileData.api_key_enc}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Created At</Text>
          <Text style={styles.infoValue}>
            {new Date(userProfileData.user_created_at).toLocaleString()}
          </Text>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Preferences</Text>
        <View>
          {userProfileData.preferences ? (
            <>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Household Size</Text>
                <Text style={styles.infoValue}>{userProfileData.preferences?.household_size || 'N/A'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Dietary Preference</Text>
                <Text style={styles.infoValue}>{userProfileData.preferences?.dietary_preference || 'N/A'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Allergens</Text>
                <Text style={styles.infoValue}>{userProfileData.preferences?.allergens?.join(', ') || 'N/A'}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Cuisine Preference</Text>
                <Text style={styles.infoValue}>{userProfileData.preferences?.cuisine_preference || 'N/A'}</Text>
              </View>
            </>
          ) : (
            <Text style={styles.preferencesText}>
              No preferences set.
            </Text>
          )}
        </View>
      </View>

      <View style={styles.buttonContainer}>
        <TouchableOpacity 
          style={[styles.button, styles.dangerButton]} 
          onPress={handleSignOut}
        >
          <Text style={styles.buttonText}>Sign Out</Text>
        </TouchableOpacity>
      </View>

      {userProfileData.is_admin && (
        <View style={[styles.section, styles.adminSection]}> 
          <Text style={styles.sectionTitle}>Admin</Text>
          <TouchableOpacity 
            style={[styles.button, { backgroundColor: '#4a6da7' }]} 
            onPress={() => router.push('/(tabs)/admin')}
          >
            <Text style={styles.buttonText}>Manage Users</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9f9f9',
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  contentContainer: {
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  errorText: {
    color: 'red',
    textAlign: 'center',
    marginTop: 20,
  },
  profileHeader: {
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
    borderRadius: 10,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  avatar: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#297A56',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  avatarText: {
    color: '#fff',
    fontSize: 48,
    fontWeight: 'bold',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
    color: '#333',
  },
  email: {
    fontSize: 16,
    color: '#666',
    marginBottom: 15,
  },
  adminBadge: {
    backgroundColor: '#ffeb3b',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 15,
  },
  adminText: {
    color: '#333',
    fontWeight: '600',
    fontSize: 14,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#297A56',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    paddingBottom: 10,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  infoLabel: {
    fontSize: 16,
    color: '#666',
  },
  buttonContainer: {
    marginTop: 10,
    marginBottom: 30,
  },
  button: {
    backgroundColor: '#297A56',
    padding: 10,
    borderRadius: 6,
    alignItems: 'center',
    marginBottom: 10,
    minWidth: 120,
    alignSelf: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  dangerButton: {
    backgroundColor: '#dc3545',
  },
  infoValue: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  preferencesText: {
    color: '#666',
    fontStyle: 'italic',
  },
  adminSection: {
    marginTop: 20,
  },
});