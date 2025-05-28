// app/(tabs)/admin.tsx - Part of the PrepSense mobile app
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, TouchableOpacity, Switch, Alert, ActivityIndicatorBase } from 'react-native';
import { MaterialCommunityIcons, Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../context/AuthContext';
import { router } from 'expo-router';
import { Config } from '../../config';

interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

// Mock data for prototype - TODO: Replace with real API calls when backend is ready
const MOCK_USERS: UserProfile[] = [
  {
    id: 'samantha-smith-001',
    email: 'samantha.smith@prepsense.com',
    first_name: 'Samantha',
    last_name: 'Smith',
    is_admin: true,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'john-doe-002',
    email: 'john.doe@prepsense.com',
    first_name: 'John',
    last_name: 'Doe',
    is_admin: false,
    created_at: '2024-01-20T14:30:00Z',
    updated_at: '2024-01-20T14:30:00Z',
  },
  {
    id: 'jane-admin-003',
    email: 'jane.admin@prepsense.com',
    first_name: 'Jane',
    last_name: 'Admin',
    is_admin: true,
    created_at: '2024-02-01T09:15:00Z',
    updated_at: '2024-02-01T09:15:00Z',
  },
];

export default function AdminScreen() {
  const { user: currentUser } = useAuth(); // Removed token and signOut for prototype
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'cleanup' | 'users' | 'bigquery'>('cleanup');
  const [isMockMode, setIsMockMode] = useState(false);
  const [isCleaningUp, setIsCleaningUp] = useState(false);

  // Load mock users for prototype - TODO: Replace with real API when backend is ready
  useEffect(() => {
    const loadMockUsers = async () => {
      try {
        setIsLoading(true);
        
        // Simulate API delay for realistic feel
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Use mock data for prototype
        setUsers(MOCK_USERS);
        setError(null);
        
        // TODO: Replace with real API call when backend is ready
        // const response = await fetch(`${Config.API_BASE_URL}/users/`, {
        //   headers: {
        //     'Authorization': `Bearer ${token}`,
        //     'Content-Type': 'application/json',
        //   },
        // });

        // if (!response.ok) {
        //   if (response.status === 403) {
        //     throw new Error('Admin access required');
        //   }
        //   throw new Error(`Failed to fetch users: ${response.status}`);
        // }

        // const userData = await response.json();
        // setUsers(userData);
        
      } catch (err) {
        console.error('Error loading users:', err);
        setError(err instanceof Error ? err.message : 'Failed to load users');
        
        // For prototype: still show mock data even if there's an "error"
        setUsers(MOCK_USERS);
      } finally {
        setIsLoading(false);
      }
    };

    loadMockUsers();
  }, []); // Removed token dependency for prototype

  // Mock toggle user admin status - TODO: Implement real API when backend is ready
  const toggleUserAdmin = async (userId: string) => {
    try {
      // For prototype: just update local state
      setUsers(prevUsers =>
        prevUsers.map(user =>
          user.id === userId
            ? { ...user, is_admin: !user.is_admin, updated_at: new Date().toISOString() }
            : user
        )
      );

      // TODO: Implement real API call when backend is ready
      // const response = await fetch(`${Config.API_BASE_URL}/users/${userId}/toggle-admin`, {
      //   method: 'PATCH',
      //   headers: {
      //     'Authorization': `Bearer ${token}`,
      //     'Content-Type': 'application/json',
      //   },
      // });

      // if (!response.ok) {
      //   throw new Error('Failed to update user');
      // }

      // const updatedUser = await response.json();
      // setUsers(prevUsers =>
      //   prevUsers.map(user => user.id === userId ? updatedUser : user)
      // );
    } catch (err) {
      console.error('Error updating user:', err);
      setError(err instanceof Error ? err.message : 'Failed to update user');
    }
  };

  const renderUsersTab = () => (
    <>
      <Text style={styles.header}>User Management</Text>

      {users.length === 0 ? (
        <Text>No users found</Text>
      ) : (
        <View style={styles.usersContainer}>
          {users.map((user) => (
            <View key={user.id} style={styles.userCard}>
              <Text style={styles.userName}>
                {user.first_name} {user.last_name}
                {user.is_admin && ' (Admin)'}
              </Text>
              <Text style={styles.userEmail}>{user.email}</Text>
              <Text style={styles.userId}>ID: {user.id}</Text>
              <Text style={styles.userDate}>
                Created: {new Date(user.created_at).toLocaleDateString()}
              </Text>
              
              {/* User Actions */}
              <View style={styles.userActions}>
                <TouchableOpacity
                  style={[styles.actionButton, user.is_admin ? styles.removeAdminButton : styles.makeAdminButton]}
                  onPress={() => toggleUserAdmin(user.id)}
                >
                  <Text style={styles.actionButtonText}>
                    {user.is_admin ? '⬇️ Remove Admin' : '⬆️ Make Admin'}
                  </Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[styles.actionButton, styles.viewUserButton]}
                  onPress={() => {
                    Alert.alert(
                      'User Details',
                      `Name: ${user.first_name} ${user.last_name}\nEmail: ${user.email}\nAdmin: ${user.is_admin ? 'Yes' : 'No'}\nCreated: ${new Date(user.created_at).toLocaleDateString()}\nLast Updated: ${new Date(user.updated_at).toLocaleDateString()}`,
                      [{ text: 'OK' }]
                    );
                  }}
                >
                  <Text style={styles.actionButtonText}>👁️ View Details</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      )}
    </>
  );

  // Function to cleanup recently added items from BigQuery
  const cleanupRecentItems = async () => {
    if (isCleaningUp) return;
    
    Alert.alert(
      'Clean up recent items?',
      'This will delete items added via vision detection in the last 24 hours. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Clean Up', 
          style: 'destructive',
          onPress: async () => {
            try {
              setIsCleaningUp(true);
              
              const response = await fetch(`${Config.API_BASE_URL}/images/cleanup-detected-items`, {
                method: 'DELETE',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  user_id: 111, // Default demo user ID
                  hours_ago: 24  // Delete items from the last 24 hours
                }),
              });
              
              if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to clean up items');
              }
              
              const result = await response.json();
              console.log('Items cleaned up:', result);
              Alert.alert('Success', 'Vision-detected items have been cleaned up from the database');
              
            } catch (error: any) {
              console.error('Error cleaning up items:', error);
              Alert.alert('Error', `Failed to clean up items: ${error.message}`);
            } finally {
              setIsCleaningUp(false);
            }
          } 
        },
      ]
    );
  };

  const renderBigQueryTab = () => (
    <View style={styles.bigQueryContainer}>
      <Text style={styles.header}>BigQuery Testing</Text>

      <View style={styles.settingRow}>
        <Text style={styles.settingLabel}>Mock Mode</Text>
        <Switch
          value={isMockMode}
          onValueChange={setIsMockMode}
          trackColor={{ false: '#767577', true: '#81b0ff' }}
          thumbColor={isMockMode ? '#f5dd4b' : '#f4f3f4'}
        />
        <Text style={[styles.settingValue, !isMockMode && styles.activeMode]}>
          {isMockMode ? 'Using Mock Data' : 'Live Mode'}
        </Text>

        {/* Cleanup Button */}
        <View style={styles.cleanupContainer}>
          <TouchableOpacity
            style={[styles.cleanupButton, isCleaningUp && styles.cleanupButtonDisabled]}
            onPress={cleanupRecentItems}
            disabled={isCleaningUp}
          >
            {isCleaningUp ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <>
                <MaterialCommunityIcons name="trash-can-outline" size={20} color="#FFFFFF" style={styles.cleanupIcon} />
                <Text style={styles.cleanupButtonText}>Cleanup Vision Items</Text>
              </>
            )}
          </TouchableOpacity>
          <Text style={styles.cleanupDescription}>
            Remove items added via vision detection in the last 24 hours
          </Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Available Tables</Text>
      <View style={styles.tablesContainer}>
        {[
          { id: 'users', name: 'Users', description: 'User accounts and profiles' },
          { id: 'inventory', name: 'Inventory', description: 'Inventory items' },
          { id: 'transactions', name: 'Transactions', description: 'Transaction history' },
          { id: 'food_items', name: 'Food Items', description: 'Food items in inventory' },
          { id: 'expenses', name: 'Expenses', description: 'Expense tracking' },
        ].map((table) => (
          <TouchableOpacity
            key={table.id}
            style={styles.tableCard}
            onPress={() => router.push('/bigquery-tester')}
          >
            <Text style={styles.tableName}>{table.name}</Text>
            <Text style={styles.tableDescription}>{table.description}</Text>
            <View style={styles.tableFooter}>
              <Text style={styles.tableId}>{table.id}</Text>
              <Text style={styles.tableLink}>Open in Query Tester →</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.quickQueries}>
        <Text style={styles.sectionTitle}>Quick Access</Text>

        <TouchableOpacity
          style={styles.queryButton}
          onPress={() => router.push('/bigquery-tester')}
        >
          <Text style={styles.queryButtonText}>🔍 Open BigQuery Tester</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.queryButton}
          onPress={() => router.push('/bigquery-tester')}
        >
          <Text style={styles.queryButtonText}>📊 Test Database Queries</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text>Loading users...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity
          style={[styles.button, { marginTop: 20 }]}
          onPress={() => router.back()}
        >
          <Text style={styles.buttonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'cleanup' && styles.activeTab]}
          onPress={() => setActiveTab('cleanup')}
        >
          <Text style={[styles.tabText, activeTab === 'cleanup' && styles.activeTabText]}>
            <MaterialCommunityIcons name="broom" size={16} style={styles.tabIcon} /> Cleanup
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'users' && styles.activeTab]}
          onPress={() => setActiveTab('users')}
        >
          <Text style={[styles.tabText, activeTab === 'users' && styles.activeTabText]}>
            <Ionicons name="people-outline" size={16} style={styles.tabIcon} /> Users
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'bigquery' && styles.activeTab]}
          onPress={() => setActiveTab('bigquery')}
        >
          <Text style={[styles.tabText, activeTab === 'bigquery' && styles.activeTabText]}>
            <Ionicons name="analytics-outline" size={16} style={styles.tabIcon} /> BigQuery
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView}>
        {activeTab === 'cleanup' ? (
          <View style={styles.cleanupTabContainer}>
            <Text style={styles.header}>Cleanup Vision Items</Text>
            <View style={styles.cleanupContainer}>
              <Text style={styles.cleanupDescription}>
                This will remove all items that were added via vision detection in the last 24 hours.
                This action cannot be undone.
              </Text>
              <TouchableOpacity
                style={[styles.cleanupButton, isCleaningUp && styles.cleanupButtonDisabled]}
                onPress={cleanupRecentItems}
                disabled={isCleaningUp}
              >
                {isCleaningUp ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <>
                    <MaterialCommunityIcons name="broom" size={20} color="#FFFFFF" style={styles.cleanupIcon} />
                    <Text style={styles.cleanupButtonText}>Cleanup Vision Items</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </View>
        ) : activeTab === 'users' ? (
          renderUsersTab()
        ) : (
          renderBigQueryTab()
        )}
      </ScrollView>

      {activeTab === 'users' && (
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            {users.length} user{users.length !== 1 ? 's' : ''} total
          </Text>
        </View>
      )}
    </View>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9f9f9',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5e5',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
    flexDirection: 'row',
    alignItems: 'center',
  },
  tabIcon: {
    marginRight: 4,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#297A56',
  },
  activeTabText: {
    color: '#297A56',
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#333',
  },
  usersContainer: {
    marginBottom: 20,
  },
  userCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  userName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
    color: '#297A56',
  },
  userEmail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  userId: {
    fontSize: 12,
    color: '#999',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  userDate: {
    fontSize: 12,
    color: '#999',
    fontStyle: 'italic',
  },
  userActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
  },
  actionButton: {
    padding: 8,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 80,
  },
  makeAdminButton: {
    backgroundColor: '#297A56',
  },
  removeAdminButton: {
    backgroundColor: '#d32f2f',
  },
  viewUserButton: {
    backgroundColor: '#4CAF50',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  bigQueryContainer: {
    flex: 1,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  settingLabel: {
    fontSize: 16,
    marginRight: 12,
    flex: 1,
  },
  settingValue: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
  },
  activeMode: {
    color: '#297A56',
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  tablesContainer: {
    marginBottom: 24,
  },
  tableCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  tableName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#297A56',
    marginBottom: 4,
  },
  tableDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  tableFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tableId: {
    fontSize: 12,
    color: '#999',
    fontFamily: 'monospace',
  },
  tableLink: {
    fontSize: 12,
    color: '#297A56',
    fontWeight: '500',
  },
  quickQueries: {
    marginTop: 8,
  },
  queryButton: {
    backgroundColor: '#297A56',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    alignItems: 'center',
  },
  queryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  errorText: {
    color: '#d32f2f',
    textAlign: 'center',
    marginBottom: 16,
    fontSize: 16,
  },
  button: {
    backgroundColor: '#297A56',
    padding: 10,
    borderRadius: 6,
    alignItems: 'center',
    minWidth: 120,
    alignSelf: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 0.5,
    borderTopColor: '#e5e5e5',
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#666',
  },
  // Cleanup Tab Styles
  cleanupTabContainer: {
    padding: 20,
  },
  cleanupContainer: {
    marginTop: 20,
    marginBottom: 20,
    padding: 24,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  cleanupButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#dc3545',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 8,
    elevation: 2,
    marginTop: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cleanupButtonDisabled: {
    opacity: 0.7,
    backgroundColor: '#f87171',
  },
  cleanupIcon: {
    marginRight: 10,
  },
  cleanupButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  cleanupDescription: {
    fontSize: 15,
    color: '#4b5563',
    lineHeight: 24,
    marginBottom: 8,
  },
});
