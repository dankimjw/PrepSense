// components/bundles/RecipeBundleManager.tsx - UI for managing offline recipe bundles
/**
 * Comprehensive UI for downloading, managing, and browsing offline recipe bundles.
 * Provides bundle management, storage stats, and offline search capabilities.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Modal,
  SafeAreaView,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { recipeBundleService, RecipeBundle, BundleStats } from '../../services/recipeBundleService';
import { Theme } from '../../constants/Theme';

interface RecipeBundleManagerProps {
  visible: boolean;
  onClose: () => void;
}

export const RecipeBundleManager: React.FC<RecipeBundleManagerProps> = ({ visible, onClose }) => {
  const [availableBundles, setAvailableBundles] = useState<RecipeBundle[]>([]);
  const [downloadedBundles, setDownloadedBundles] = useState<RecipeBundle[]>([]);
  const [storageStats, setStorageStats] = useState<BundleStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [downloadingBundles, setDownloadingBundles] = useState<Set<string>>(new Set());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, number>>(new Map());
  const [selectedTab, setSelectedTab] = useState<'available' | 'downloaded' | 'settings'>('available');

  useEffect(() => {
    if (visible) {
      loadData();
    }
  }, [visible]);

  const loadData = async () => {
    try {
      setLoading(true);
      await recipeBundleService.initializeDatabase();
      
      const [available, downloaded, stats] = await Promise.all([
        recipeBundleService.getAvailableBundles(),
        recipeBundleService.getDownloadedBundles(),
        recipeBundleService.getStorageStats()
      ]);
      
      setAvailableBundles(available);
      setDownloadedBundles(downloaded);
      setStorageStats(stats);
    } catch (error) {
      console.error('Failed to load bundle data:', error);
      Alert.alert('Error', 'Failed to load bundle information');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleDownloadBundle = async (bundle: RecipeBundle) => {
    if (downloadingBundles.has(bundle.id)) return;
    
    Alert.alert(
      'Download Bundle',
      `Download "${bundle.name}" with ${bundle.recipe_count} recipes (${(bundle.size_bytes / (1024 * 1024)).toFixed(1)}MB)?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Download',
          onPress: async () => {
            try {
              setDownloadingBundles(prev => new Set([...prev, bundle.id]));
              setDownloadProgress(prev => new Map([...prev, [bundle.id, 0]]));
              
              await recipeBundleService.downloadBundle(
                bundle.id,
                (progress) => {
                  setDownloadProgress(prev => new Map([...prev, [bundle.id, progress]]));
                }
              );
              
              // Refresh data after successful download
              await loadData();
              
              Alert.alert(
                'Download Complete',
                `"${bundle.name}" has been downloaded successfully!`
              );
            } catch (error) {
              console.error('Download failed:', error);
              Alert.alert(
                'Download Failed',
                error instanceof Error ? error.message : 'Unknown error occurred'
              );
            } finally {
              setDownloadingBundles(prev => {
                const newSet = new Set(prev);
                newSet.delete(bundle.id);
                return newSet;
              });
              setDownloadProgress(prev => {
                const newMap = new Map(prev);
                newMap.delete(bundle.id);
                return newMap;
              });
            }
          }
        }
      ]
    );
  };

  const handleRemoveBundle = (bundle: RecipeBundle) => {
    Alert.alert(
      'Remove Bundle',
      `Remove "${bundle.name}" and all its recipes from your device?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              await recipeBundleService.removeBundle(bundle.id);
              await loadData();
              Alert.alert('Success', 'Bundle removed successfully');
            } catch (error) {
              console.error('Remove failed:', error);
              Alert.alert('Error', 'Failed to remove bundle');
            }
          }
        }
      ]
    );
  };

  const handleCleanupStorage = () => {
    Alert.alert(
      'Cleanup Storage',
      'Remove bundles older than 30 days?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Cleanup',
          onPress: async () => {
            try {
              await recipeBundleService.cleanupStorage(30);
              await loadData();
              Alert.alert('Success', 'Storage cleanup completed');
            } catch (error) {
              console.error('Cleanup failed:', error);
              Alert.alert('Error', 'Failed to cleanup storage');
            }
          }
        }
      ]
    );
  };

  const formatSize = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)}MB`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  const renderBundleCard = (bundle: RecipeBundle, isDownloaded: boolean) => {
    const isDownloading = downloadingBundles.has(bundle.id);
    const progress = downloadProgress.get(bundle.id) || 0;

    return (
      <View key={bundle.id} style={styles.bundleCard}>
        <View style={styles.bundleHeader}>
          <View style={styles.bundleInfo}>
            <Text style={styles.bundleName}>{bundle.name}</Text>
            <Text style={styles.bundleDescription}>{bundle.description}</Text>
            <View style={styles.bundleMetrics}>
              <View style={styles.metric}>
                <Ionicons name="restaurant" size={16} color={Theme.colors.textSecondary} />
                <Text style={styles.metricText}>{bundle.recipe_count} recipes</Text>
              </View>
              <View style={styles.metric}>
                <Ionicons name="archive" size={16} color={Theme.colors.textSecondary} />
                <Text style={styles.metricText}>{formatSize(bundle.size_bytes)}</Text>
              </View>
              <View style={styles.metric}>
                <Ionicons name="time" size={16} color={Theme.colors.textSecondary} />
                <Text style={styles.metricText}>v{bundle.version}</Text>
              </View>
            </View>
          </View>
          
          <View style={styles.bundleActions}>
            {isDownloaded ? (
              <TouchableOpacity
                style={[styles.actionButton, styles.removeButton]}
                onPress={() => handleRemoveBundle(bundle)}
              >
                <Ionicons name="trash" size={20} color={Theme.colors.error} />
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={[styles.actionButton, styles.downloadButton, isDownloading && styles.downloadingButton]}
                onPress={() => handleDownloadBundle(bundle)}
                disabled={isDownloading}
              >
                {isDownloading ? (
                  <ActivityIndicator size="small" color={Theme.colors.surface} />
                ) : (
                  <Ionicons name="download" size={20} color={Theme.colors.surface} />
                )}
              </TouchableOpacity>
            )}
          </View>
        </View>
        
        {bundle.tags && bundle.tags.length > 0 && (
          <View style={styles.tagsContainer}>
            {bundle.tags.slice(0, 3).map((tag) => (
              <View key={tag} style={styles.tag}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
            {bundle.tags.length > 3 && (
              <Text style={styles.moreTagsText}>+{bundle.tags.length - 3} more</Text>
            )}
          </View>
        )}
        
        {isDownloading && (
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: `${progress}%` }]} />
            </View>
            <Text style={styles.progressText}>{Math.round(progress)}%</Text>
          </View>
        )}
        
        {isDownloaded && bundle.download_date && (
          <Text style={styles.downloadDate}>
            Downloaded: {formatDate(bundle.download_date)}
          </Text>
        )}
      </View>
    );
  };

  const renderStorageStats = () => {
    if (!storageStats) return null;

    const usagePercentage = (storageStats.total_size_mb / 500) * 100;

    return (
      <View style={styles.statsContainer}>
        <Text style={styles.statsTitle}>Storage Usage</Text>
        
        <View style={styles.storageBar}>
          <View style={[styles.storageBarFill, { width: `${Math.min(usagePercentage, 100)}%` }]} />
        </View>
        
        <View style={styles.statsGrid}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{storageStats.total_bundles}</Text>
            <Text style={styles.statLabel}>Bundles</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{storageStats.total_recipes}</Text>
            <Text style={styles.statLabel}>Recipes</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{storageStats.total_size_mb.toFixed(1)}MB</Text>
            <Text style={styles.statLabel}>Used</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{storageStats.available_space_mb.toFixed(1)}MB</Text>
            <Text style={styles.statLabel}>Available</Text>
          </View>
        </View>
        
        <TouchableOpacity style={styles.cleanupButton} onPress={handleCleanupStorage}>
          <Ionicons name="trash" size={16} color={Theme.colors.warning} />
          <Text style={styles.cleanupButtonText}>Cleanup Old Bundles</Text>
        </TouchableOpacity>
      </View>
    );
  };

  if (!visible) return null;

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet">
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={Theme.colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>Recipe Bundles</Text>
          <TouchableOpacity onPress={handleRefresh} style={styles.refreshButton}>
            <Ionicons name="refresh" size={24} color={Theme.colors.info} />
          </TouchableOpacity>
        </View>

        {/* Tab Bar */}
        <View style={styles.tabBar}>
          {[
            { id: 'available', label: 'Available', icon: 'cloud' },
            { id: 'downloaded', label: 'Downloaded', icon: 'archive' },
            { id: 'settings', label: 'Settings', icon: 'settings' }
          ].map((tab) => (
            <TouchableOpacity
              key={tab.id}
              style={[styles.tab, selectedTab === tab.id && styles.activeTab]}
              onPress={() => setSelectedTab(tab.id as any)}
            >
              <Ionicons 
                name={tab.icon as any} 
                size={20} 
                color={selectedTab === tab.id ? Theme.colors.primary : Theme.colors.textSecondary} 
              />
              <Text style={[
                styles.tabLabel,
                selectedTab === tab.id && styles.activeTabLabel
              ]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Content */}
        <ScrollView 
          style={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
        >
          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={Theme.colors.primary} />
              <Text style={styles.loadingText}>Loading bundles...</Text>
            </View>
          ) : (
            <>
              {selectedTab === 'available' && (
                <View>
                  <Text style={styles.sectionTitle}>Available for Download</Text>
                  {availableBundles.length === 0 ? (
                    <Text style={styles.emptyText}>No bundles available</Text>
                  ) : (
                    availableBundles.map(bundle => renderBundleCard(bundle, false))
                  )}
                </View>
              )}

              {selectedTab === 'downloaded' && (
                <View>
                  <Text style={styles.sectionTitle}>Downloaded Bundles</Text>
                  {downloadedBundles.length === 0 ? (
                    <Text style={styles.emptyText}>No bundles downloaded yet</Text>
                  ) : (
                    downloadedBundles.map(bundle => renderBundleCard(bundle, true))
                  )}
                </View>
              )}

              {selectedTab === 'settings' && renderStorageStats()}
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.colors.background,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Theme.spacing.lg,
    paddingVertical: Theme.spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: Theme.colors.border,
  },
  closeButton: {
    padding: Theme.spacing.xs,
  },
  title: {
    fontSize: Theme.typography.sizes.lg,
    fontWeight: Theme.typography.weights.semiBold,
    color: Theme.colors.text,
  },
  refreshButton: {
    padding: Theme.spacing.xs,
  },
  
  // Tab Bar
  tabBar: {
    flexDirection: 'row',
    backgroundColor: Theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Theme.colors.border,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Theme.spacing.md,
    gap: Theme.spacing.xs,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: Theme.colors.primary,
  },
  tabLabel: {
    fontSize: Theme.typography.sizes.sm,
    color: Theme.colors.textSecondary,
    fontWeight: Theme.typography.weights.medium,
  },
  activeTabLabel: {
    color: Theme.colors.primary,
  },
  
  // Content
  content: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: Theme.typography.sizes.lg,
    fontWeight: Theme.typography.weights.semiBold,
    color: Theme.colors.text,
    margin: Theme.spacing.lg,
    marginBottom: Theme.spacing.md,
  },
  
  // Bundle Cards
  bundleCard: {
    backgroundColor: Theme.colors.surface,
    marginHorizontal: Theme.spacing.lg,
    marginBottom: Theme.spacing.md,
    borderRadius: Theme.borderRadius.lg,
    padding: Theme.spacing.lg,
    ...Theme.shadows.sm,
  },
  bundleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  bundleInfo: {
    flex: 1,
  },
  bundleName: {
    fontSize: Theme.typography.sizes.md,
    fontWeight: Theme.typography.weights.semiBold,
    color: Theme.colors.text,
    marginBottom: Theme.spacing.xs,
  },
  bundleDescription: {
    fontSize: Theme.typography.sizes.sm,
    color: Theme.colors.textSecondary,
    marginBottom: Theme.spacing.sm,
    lineHeight: 20,
  },
  bundleMetrics: {
    flexDirection: 'row',
    gap: Theme.spacing.lg,
  },
  metric: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Theme.spacing.xs,
  },
  metricText: {
    fontSize: Theme.typography.sizes.xs,
    color: Theme.colors.textSecondary,
  },
  bundleActions: {
    marginLeft: Theme.spacing.md,
  },
  actionButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  downloadButton: {
    backgroundColor: Theme.colors.primary,
  },
  downloadingButton: {
    opacity: 0.7,
  },
  removeButton: {
    backgroundColor: Theme.colors.errorLight,
  },
  
  // Tags
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: Theme.spacing.md,
    gap: Theme.spacing.xs,
  },
  tag: {
    backgroundColor: Theme.colors.primaryLight,
    paddingHorizontal: Theme.spacing.sm,
    paddingVertical: Theme.spacing.xs,
    borderRadius: Theme.borderRadius.sm,
  },
  tagText: {
    fontSize: Theme.typography.sizes.xs,
    color: Theme.colors.primary,
    fontWeight: Theme.typography.weights.medium,
  },
  moreTagsText: {
    fontSize: Theme.typography.sizes.xs,
    color: Theme.colors.textSecondary,
    alignSelf: 'center',
  },
  
  // Progress
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: Theme.spacing.md,
    gap: Theme.spacing.sm,
  },
  progressBar: {
    flex: 1,
    height: 6,
    backgroundColor: Theme.colors.borderLight,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: Theme.colors.primary,
  },
  progressText: {
    fontSize: Theme.typography.sizes.xs,
    color: Theme.colors.textSecondary,
    fontWeight: Theme.typography.weights.medium,
    minWidth: 35,
    textAlign: 'right',
  },
  
  downloadDate: {
    fontSize: Theme.typography.sizes.xs,
    color: Theme.colors.textSecondary,
    marginTop: Theme.spacing.sm,
  },
  
  // Storage Stats
  statsContainer: {
    margin: Theme.spacing.lg,
    backgroundColor: Theme.colors.surface,
    borderRadius: Theme.borderRadius.lg,
    padding: Theme.spacing.lg,
    ...Theme.shadows.sm,
  },
  statsTitle: {
    fontSize: Theme.typography.sizes.md,
    fontWeight: Theme.typography.weights.semiBold,
    color: Theme.colors.text,
    marginBottom: Theme.spacing.md,
  },
  storageBar: {
    height: 8,
    backgroundColor: Theme.colors.borderLight,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: Theme.spacing.lg,
  },
  storageBarFill: {
    height: '100%',
    backgroundColor: Theme.colors.primary,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Theme.spacing.lg,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: Theme.typography.sizes.md,
    fontWeight: Theme.typography.weights.semiBold,
    color: Theme.colors.text,
  },
  statLabel: {
    fontSize: Theme.typography.sizes.xs,
    color: Theme.colors.textSecondary,
    marginTop: Theme.spacing.xs,
  },
  cleanupButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Theme.spacing.md,
    backgroundColor: Theme.colors.warningLight,
    borderRadius: Theme.borderRadius.md,
    gap: Theme.spacing.sm,
  },
  cleanupButtonText: {
    fontSize: Theme.typography.sizes.sm,
    fontWeight: Theme.typography.weights.medium,
    color: Theme.colors.warning,
  },
  
  // States
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Theme.spacing.xxxl,
  },
  loadingText: {
    fontSize: Theme.typography.sizes.md,
    color: Theme.colors.textSecondary,
    marginTop: Theme.spacing.md,
  },
  emptyText: {
    fontSize: Theme.typography.sizes.md,
    color: Theme.colors.textSecondary,
    textAlign: 'center',
    paddingVertical: Theme.spacing.xxxl,
  },
});