// PreloadDebugOverlay.tsx - Shows preloading status in development
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTabData } from '../context/TabDataProvider';

export const PreloadDebugOverlay = () => {
  const { 
    recipesData, 
    statsData, 
    chatData, 
    isPreloadComplete,
    isLoadingRecipes,
    isLoadingStats,
    isLoadingChat,
    recipesError,
    statsError,
    chatError
  } = useTabData();
  
  // Only show in development
  if (__DEV__ === false) return null;
  
  // Hide after preload is complete and no errors
  if (isPreloadComplete && !recipesError && !statsError && !chatError) {
    return null;
  }
  
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Preload Status</Text>
      
      <View style={styles.statusRow}>
        <Text style={styles.label}>Overall:</Text>
        <Text style={[styles.status, isPreloadComplete ? styles.success : styles.loading]}>
          {isPreloadComplete ? '✅ Complete' : '⏳ Loading...'}
        </Text>
      </View>
      
      <View style={styles.statusRow}>
        <Text style={styles.label}>Recipes:</Text>
        <Text style={[styles.status, 
          recipesError ? styles.error : 
          isLoadingRecipes ? styles.loading : 
          recipesData ? styles.success : styles.pending
        ]}>
          {recipesError ? '❌ Error' :
           isLoadingRecipes ? '⏳ Loading...' :
           recipesData ? `✅ ${recipesData.pantryRecipes.length} recipes` : 
           '⏸️ Pending'}
        </Text>
      </View>
      
      <View style={styles.statusRow}>
        <Text style={styles.label}>Stats:</Text>
        <Text style={[styles.status, 
          statsError ? styles.error : 
          isLoadingStats ? styles.loading : 
          statsData ? styles.success : styles.pending
        ]}>
          {statsError ? '❌ Error' :
           isLoadingStats ? '⏳ Loading...' :
           statsData ? '✅ Loaded' : 
           '⏸️ Pending'}
        </Text>
      </View>
      
      <View style={styles.statusRow}>
        <Text style={styles.label}>Chat:</Text>
        <Text style={[styles.status, 
          chatError ? styles.error : 
          isLoadingChat ? styles.loading : 
          chatData ? styles.success : styles.pending
        ]}>
          {chatError ? '❌ Error' :
           isLoadingChat ? '⏳ Loading...' :
           chatData ? `✅ ${chatData.suggestedQuestions.length} questions` : 
           '⏸️ Pending'}
        </Text>
      </View>
      
      {(recipesError || statsError || chatError) && (
        <View style={styles.errorSection}>
          <Text style={styles.errorTitle}>Errors:</Text>
          {recipesError && <Text style={styles.errorText}>Recipes: {recipesError}</Text>}
          {statsError && <Text style={styles.errorText}>Stats: {statsError}</Text>}
          {chatError && <Text style={styles.errorText}>Chat: {chatError}</Text>}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 100,
    right: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    padding: 15,
    borderRadius: 10,
    minWidth: 200,
    zIndex: 1000,
  },
  title: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 5,
  },
  label: {
    color: '#fff',
    fontSize: 14,
  },
  status: {
    fontSize: 14,
    fontWeight: '500',
  },
  success: {
    color: '#4CAF50',
  },
  loading: {
    color: '#FFC107',
  },
  error: {
    color: '#F44336',
  },
  pending: {
    color: '#9E9E9E',
  },
  errorSection: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#666',
  },
  errorTitle: {
    color: '#F44336',
    fontWeight: 'bold',
    marginBottom: 5,
  },
  errorText: {
    color: '#F44336',
    fontSize: 12,
    marginBottom: 2,
  },
});