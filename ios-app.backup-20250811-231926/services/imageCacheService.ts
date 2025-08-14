// services/imageCacheService.ts - Advanced image caching with WebP conversion and optimization
/**
 * High-performance image caching service with WebP conversion, progressive loading,
 * and intelligent cache management for recipe images.
 */

import * as FileSystem from 'expo-file-system';
import * as ImageManipulator from 'expo-image-manipulator';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Image } from 'react-native';
import { isValidImageUrl, normalizeImageUrl } from '../utils/imageUtils';

export interface CachedImageInfo {
  url: string;
  localPath: string;
  webpPath?: string;
  size: number;
  width: number;
  height: number;
  format: 'jpeg' | 'png' | 'webp';
  cachedAt: number;
  lastAccessed: number;
  accessCount: number;
}

export interface ImageCacheStats {
  totalImages: number;
  totalSizeMB: number;
  availableSpaceMB: number;
  hitRate: number;
  averageLoadTime: number;
}

export interface ImageLoadOptions {
  width?: number;
  height?: number;
  quality?: number;
  progressive?: boolean;
  preferWebP?: boolean;
  placeholder?: string;
}

class ImageCacheService {
  private readonly CACHE_DIR = `${FileSystem.cacheDirectory}recipe_images/`;
  private readonly WEBP_DIR = `${FileSystem.cacheDirectory}recipe_images_webp/`;
  private readonly MAX_CACHE_SIZE_MB = 100; // 100MB cache limit
  private readonly METADATA_KEY = 'image_cache_metadata';
  private readonly STATS_KEY = 'image_cache_stats';
  
  private cacheMetadata: Map<string, CachedImageInfo> = new Map();
  private loadingPromises: Map<string, Promise<string>> = new Map();
  private stats = {
    hits: 0,
    misses: 0,
    totalLoadTime: 0,
    loadCount: 0
  };

  /**
   * Initialize the image cache service
   */
  async initialize(): Promise<void> {
    try {
      console.log('ImageCacheService: Initializing...');
      
      // Ensure cache directories exist
      await this.ensureDirectoriesExist();
      
      // Load metadata from storage
      await this.loadMetadata();
      
      // Clean up expired cache entries
      await this.cleanupExpiredEntries();
      
      console.log('ImageCacheService: Initialized successfully');
    } catch (error) {
      console.error('ImageCacheService: Failed to initialize:', error);
      throw error;
    }
  }

  /**
   * Ensure all required cache directories exist
   */
  private async ensureDirectoriesExist(): Promise<void> {
    try {
      // Create main cache directory
      await FileSystem.makeDirectoryAsync(this.CACHE_DIR, { intermediates: true });
      console.log('ImageCacheService: Created/verified cache directory:', this.CACHE_DIR);
      
      // Create WebP cache directory
      await FileSystem.makeDirectoryAsync(this.WEBP_DIR, { intermediates: true });
      console.log('ImageCacheService: Created/verified WebP directory:', this.WEBP_DIR);
      
      // Verify directories exist
      const cacheInfo = await FileSystem.getInfoAsync(this.CACHE_DIR);
      const webpInfo = await FileSystem.getInfoAsync(this.WEBP_DIR);
      
      if (!cacheInfo.exists) {
        throw new Error(`Failed to create cache directory: ${this.CACHE_DIR}`);
      }
      
      if (!webpInfo.exists) {
        throw new Error(`Failed to create WebP directory: ${this.WEBP_DIR}`);
      }
      
      console.log('ImageCacheService: Directory verification successful');
    } catch (error) {
      console.error('ImageCacheService: Failed to create directories:', error);
      throw new Error(`Directory creation failed: ${error.message}`);
    }
  }

  /**
   * Ensure a specific directory exists with detailed error handling
   */
  private async ensureDirectoryExists(dirPath: string, context: string = 'cache operation'): Promise<void> {
    try {
      const dirInfo = await FileSystem.getInfoAsync(dirPath);
      
      if (!dirInfo.exists) {
        console.log(`ImageCacheService: Creating missing directory for ${context}:`, dirPath);
        await FileSystem.makeDirectoryAsync(dirPath, { intermediates: true });
        
        // Verify creation was successful
        const verifyInfo = await FileSystem.getInfoAsync(dirPath);
        if (!verifyInfo.exists) {
          throw new Error(`Directory creation failed - path does not exist after creation: ${dirPath}`);
        }
        
        console.log(`ImageCacheService: Successfully created directory for ${context}:`, dirPath);
      }
    } catch (error) {
      console.error(`ImageCacheService: Failed to ensure directory exists for ${context}:`, error);
      throw new Error(`Directory validation failed for ${context}: ${error.message}`);
    }
  }

  /**
   * Get cached image path with progressive loading and WebP optimization
   */
  async getCachedImage(
    url: string, 
    options: ImageLoadOptions = {}
  ): Promise<string> {
    // Validate and normalize URL
    const normalizedUrl = normalizeImageUrl(url);
    if (!normalizedUrl || !isValidImageUrl(normalizedUrl)) {
      console.warn('ImageCacheService: Invalid URL provided:', url);
      return '';
    }

    const startTime = Date.now();
    const cacheKey = this.generateCacheKey(normalizedUrl, options);
    
    try {
      // Check if already loading
      if (this.loadingPromises.has(cacheKey)) {
        return await this.loadingPromises.get(cacheKey)!;
      }

      // Check cache first
      const cachedInfo = this.cacheMetadata.get(cacheKey);
      if (cachedInfo && await this.isCacheEntryValid(cachedInfo)) {
        // Update access statistics
        cachedInfo.lastAccessed = Date.now();
        cachedInfo.accessCount++;
        this.stats.hits++;
        
        // Return WebP version if available and preferred
        if (options.preferWebP && cachedInfo.webpPath && 
            await this.fileExists(cachedInfo.webpPath)) {
          return cachedInfo.webpPath;
        }
        
        return cachedInfo.localPath;
      }

      // Create loading promise
      const loadingPromise = this.downloadAndCacheImage(normalizedUrl, options, cacheKey);
      this.loadingPromises.set(cacheKey, loadingPromise);

      try {
        const result = await loadingPromise;
        this.stats.misses++;
        this.stats.totalLoadTime += Date.now() - startTime;
        this.stats.loadCount++;
        return result;
      } finally {
        this.loadingPromises.delete(cacheKey);
      }

    } catch (error) {
      console.error(`ImageCacheService: Failed to get cached image for ${normalizedUrl}:`, error);
      this.stats.misses++;
      
      // Return empty string instead of original URL to prevent render errors
      return '';
    }
  }

  /**
   * Preload multiple images for better user experience
   */
  async preloadImages(
    urls: string[], 
    options: ImageLoadOptions = {},
    onProgress?: (loaded: number, total: number) => void
  ): Promise<void> {
    // Filter and validate URLs
    const validUrls = urls
      .map(url => normalizeImageUrl(url))
      .filter(url => url && isValidImageUrl(url));

    if (validUrls.length === 0) {
      console.warn('ImageCacheService: No valid URLs provided for preloading');
      return;
    }

    const loadPromises = validUrls.map(async (url, index) => {
      try {
        await this.getCachedImage(url, options);
        onProgress?.(index + 1, validUrls.length);
      } catch (error) {
        console.error(`ImageCacheService: Failed to preload image ${url}:`, error);
      }
    });

    await Promise.allSettled(loadPromises);
  }

  /**
   * Check if file exists with error handling
   */
  private async fileExists(path: string): Promise<boolean> {
    try {
      const fileInfo = await FileSystem.getInfoAsync(path);
      return fileInfo.exists === true;
    } catch (error) {
      console.warn('ImageCacheService: Error checking file existence:', path, error);
      return false;
    }
  }

  /**
   * Download and cache image with optimization and defensive directory creation
   */
  private async downloadAndCacheImage(
    url: string,
    options: ImageLoadOptions,
    cacheKey: string
  ): Promise<string> {
    const { width, height, quality = 0.8, preferWebP = true } = options;
    
    try {
      // Ensure cache directories exist before any file operations
      await this.ensureDirectoryExists(this.CACHE_DIR, 'image download');
      if (preferWebP) {
        await this.ensureDirectoryExists(this.WEBP_DIR, 'WebP conversion');
      }

      // Download image
      const fileName = `${cacheKey}.jpg`;
      const localPath = `${this.CACHE_DIR}${fileName}`;
      
      console.log(`ImageCacheService: Downloading image from ${url} to ${localPath}`);
      
      const downloadResult = await FileSystem.downloadAsync(url, localPath);
      
      if (downloadResult.status !== 200) {
        throw new Error(`Download failed with status ${downloadResult.status}. Headers: ${JSON.stringify(downloadResult.headers)}`);
      }

      // Verify download
      if (!await this.fileExists(localPath)) {
        throw new Error(`Downloaded file does not exist at path: ${localPath}`);
      }

      // Get file info
      const fileInfo = await FileSystem.getInfoAsync(localPath);
      if (!fileInfo.exists || !fileInfo.size || fileInfo.size === 0) {
        throw new Error(`Downloaded file is empty or invalid. Size: ${fileInfo.size}, Exists: ${fileInfo.exists}`);
      }

      console.log(`ImageCacheService: Successfully downloaded image (${fileInfo.size} bytes)`);

      // Get image dimensions with error handling
      const imageDimensions = await this.getImageDimensions(localPath);
      
      let finalPath = localPath;
      let format: 'jpeg' | 'png' | 'webp' = 'jpeg';
      let webpPath: string | undefined;

      // Optimize image if dimensions are specified
      if (width || height) {
        try {
          const optimizedResult = await ImageManipulator.manipulateAsync(
            localPath,
            [
              {
                resize: {
                  width: width || imageDimensions.width,
                  height: height || imageDimensions.height
                }
              }
            ],
            {
              compress: quality,
              format: ImageManipulator.SaveFormat.JPEG
            }
          );
          
          // Replace original with optimized version
          await FileSystem.moveAsync({
            from: optimizedResult.uri,
            to: localPath
          });
          
          console.log('ImageCacheService: Image optimization completed');
        } catch (error) {
          console.warn('ImageCacheService: Image optimization failed:', error);
          // Continue with original image
        }
      }

      // Convert to WebP if supported and preferred
      if (preferWebP) {
        try {
          // Ensure WebP directory exists before conversion
          await this.ensureDirectoryExists(this.WEBP_DIR, 'WebP conversion');
          
          webpPath = `${this.WEBP_DIR}${cacheKey}.webp`;
          const webpResult = await ImageManipulator.manipulateAsync(
            localPath,
            [],
            {
              compress: quality,
              format: ImageManipulator.SaveFormat.WEBP
            }
          );
          
          await FileSystem.moveAsync({
            from: webpResult.uri,
            to: webpPath
          });
          
          format = 'webp';
          finalPath = webpPath;
          console.log('ImageCacheService: WebP conversion completed');
        } catch (error) {
          console.warn('ImageCacheService: WebP conversion failed, using JPEG:', error);
          webpPath = undefined;
          finalPath = localPath;
        }
      }

      // Update cache metadata
      const finalFileInfo = await FileSystem.getInfoAsync(finalPath);
      const cacheInfo: CachedImageInfo = {
        url,
        localPath,
        webpPath,
        size: finalFileInfo.size || 0,
        width: width || imageDimensions.width,
        height: height || imageDimensions.height,
        format,
        cachedAt: Date.now(),
        lastAccessed: Date.now(),
        accessCount: 1
      };

      this.cacheMetadata.set(cacheKey, cacheInfo);
      await this.persistMetadata();

      // Clean up cache if needed
      await this.enforceStorageLimit();

      console.log(`ImageCacheService: Successfully cached image with key: ${cacheKey}`);
      return finalPath;
    } catch (error) {
      console.error('ImageCacheService: Failed to download and cache image:', error);
      
      // Clean up any partial files
      try {
        await FileSystem.deleteAsync(`${this.CACHE_DIR}${cacheKey}.jpg`, { idempotent: true });
        await FileSystem.deleteAsync(`${this.WEBP_DIR}${cacheKey}.webp`, { idempotent: true });
      } catch (cleanupError) {
        console.warn('ImageCacheService: Failed to clean up partial files:', cleanupError);
      }
      
      throw error;
    }
  }

  /**
   * Get image dimensions without loading the full image
   */
  private async getImageDimensions(localPath: string): Promise<{ width: number; height: number }> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Image dimension timeout'));
      }, 5000); // 5 second timeout

      Image.getSize(
        localPath,
        (width, height) => {
          clearTimeout(timeout);
          resolve({ width, height });
        },
        (error) => {
          clearTimeout(timeout);
          console.warn('ImageCacheService: Failed to get image dimensions:', error);
          resolve({ width: 300, height: 200 }); // Default dimensions
        }
      );
    });
  }

  /**
   * Generate cache key from URL and options
   */
  private generateCacheKey(url: string, options: ImageLoadOptions): string {
    const optionsString = JSON.stringify({
      width: options.width,
      height: options.height,
      quality: options.quality,
      preferWebP: options.preferWebP
    });
    
    const combined = `${url}_${optionsString}`;
    
    // Simple hash function for cache key
    let hash = 0;
    for (let i = 0; i < combined.length; i++) {
      const char = combined.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(36);
  }

  /**
   * Check if cache entry is still valid
   */
  private async isCacheEntryValid(cacheInfo: CachedImageInfo): Promise<boolean> {
    try {
      // Check if file exists
      if (!await this.fileExists(cacheInfo.localPath)) {
        return false;
      }

      // Check WebP file if it should exist
      if (cacheInfo.webpPath && !await this.fileExists(cacheInfo.webpPath)) {
        cacheInfo.webpPath = undefined; // Remove invalid WebP reference
      }

      // Cache entries are valid for 7 days
      const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds
      return (Date.now() - cacheInfo.cachedAt) < maxAge;
    } catch (error) {
      console.warn('ImageCacheService: Error validating cache entry:', error);
      return false;
    }
  }

  /**
   * Clean up expired cache entries
   */
  private async cleanupExpiredEntries(): Promise<void> {
    const expiredKeys: string[] = [];
    
    for (const [key, cacheInfo] of this.cacheMetadata) {
      if (!await this.isCacheEntryValid(cacheInfo)) {
        expiredKeys.push(key);
        
        // Delete files
        try {
          await FileSystem.deleteAsync(cacheInfo.localPath, { idempotent: true });
          if (cacheInfo.webpPath) {
            await FileSystem.deleteAsync(cacheInfo.webpPath, { idempotent: true });
          }
        } catch (error) {
          console.warn('ImageCacheService: Failed to delete expired cache file:', error);
        }
      }
    }

    // Remove from metadata
    expiredKeys.forEach(key => this.cacheMetadata.delete(key));
    
    if (expiredKeys.length > 0) {
      await this.persistMetadata();
      console.log(`ImageCacheService: Cleaned up ${expiredKeys.length} expired cache entries`);
    }
  }

  /**
   * Enforce storage limit by removing least recently used entries
   */
  private async enforceStorageLimit(): Promise<void> {
    const totalSize = Array.from(this.cacheMetadata.values())
      .reduce((sum, info) => sum + info.size, 0);
    
    const totalSizeMB = totalSize / (1024 * 1024);
    
    if (totalSizeMB <= this.MAX_CACHE_SIZE_MB) {
      return;
    }

    // Sort by last accessed time (LRU)
    const sortedEntries = Array.from(this.cacheMetadata.entries())
      .sort(([, a], [, b]) => a.lastAccessed - b.lastAccessed);

    let currentSize = totalSize;
    const targetSize = this.MAX_CACHE_SIZE_MB * 0.8 * 1024 * 1024; // Target 80% of limit

    for (const [key, cacheInfo] of sortedEntries) {
      if (currentSize <= targetSize) break;

      // Delete files
      try {
        await FileSystem.deleteAsync(cacheInfo.localPath, { idempotent: true });
        if (cacheInfo.webpPath) {
          await FileSystem.deleteAsync(cacheInfo.webpPath, { idempotent: true });
        }
        
        currentSize -= cacheInfo.size;
        this.cacheMetadata.delete(key);
      } catch (error) {
        console.warn('ImageCacheService: Failed to delete cache file during cleanup:', error);
      }
    }

    await this.persistMetadata();
    console.log(`ImageCacheService: Cache cleanup completed. Freed ${((totalSize - currentSize) / (1024 * 1024)).toFixed(2)}MB`);
  }

  /**
   * Load cache metadata from persistent storage
   */
  private async loadMetadata(): Promise<void> {
    try {
      const metadataJson = await AsyncStorage.getItem(this.METADATA_KEY);
      if (metadataJson) {
        const metadata = JSON.parse(metadataJson);
        this.cacheMetadata = new Map(Object.entries(metadata));
      }

      const statsJson = await AsyncStorage.getItem(this.STATS_KEY);
      if (statsJson) {
        this.stats = { ...this.stats, ...JSON.parse(statsJson) };
      }
    } catch (error) {
      console.error('ImageCacheService: Failed to load cache metadata:', error);
    }
  }

  /**
   * Persist cache metadata to storage
   */
  private async persistMetadata(): Promise<void> {
    try {
      const metadata = Object.fromEntries(this.cacheMetadata);
      await AsyncStorage.setItem(this.METADATA_KEY, JSON.stringify(metadata));
      await AsyncStorage.setItem(this.STATS_KEY, JSON.stringify(this.stats));
    } catch (error) {
      console.error('ImageCacheService: Failed to persist cache metadata:', error);
    }
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<ImageCacheStats> {
    const totalImages = this.cacheMetadata.size;
    const totalSize = Array.from(this.cacheMetadata.values())
      .reduce((sum, info) => sum + info.size, 0);
    const totalSizeMB = totalSize / (1024 * 1024);
    
    const hitRate = this.stats.hits + this.stats.misses > 0 
      ? this.stats.hits / (this.stats.hits + this.stats.misses) 
      : 0;
    
    const averageLoadTime = this.stats.loadCount > 0 
      ? this.stats.totalLoadTime / this.stats.loadCount 
      : 0;

    return {
      totalImages,
      totalSizeMB,
      availableSpaceMB: this.MAX_CACHE_SIZE_MB - totalSizeMB,
      hitRate,
      averageLoadTime
    };
  }

  /**
   * Clear entire cache
   */
  async clearCache(): Promise<void> {
    try {
      // Delete all cache files
      await FileSystem.deleteAsync(this.CACHE_DIR, { idempotent: true });
      await FileSystem.deleteAsync(this.WEBP_DIR, { idempotent: true });
      
      // Recreate directories
      await this.ensureDirectoriesExist();
      
      // Clear metadata
      this.cacheMetadata.clear();
      this.stats = { hits: 0, misses: 0, totalLoadTime: 0, loadCount: 0 };
      
      await this.persistMetadata();
      
      console.log('ImageCacheService: Cache cleared successfully');
    } catch (error) {
      console.error('ImageCacheService: Failed to clear image cache:', error);
      throw error;
    }
  }

  /**
   * Remove specific image from cache
   */
  async removeImage(url: string, options: ImageLoadOptions = {}): Promise<void> {
    const normalizedUrl = normalizeImageUrl(url);
    if (!normalizedUrl) return;

    const cacheKey = this.generateCacheKey(normalizedUrl, options);
    const cacheInfo = this.cacheMetadata.get(cacheKey);
    
    if (cacheInfo) {
      try {
        await FileSystem.deleteAsync(cacheInfo.localPath, { idempotent: true });
        if (cacheInfo.webpPath) {
          await FileSystem.deleteAsync(cacheInfo.webpPath, { idempotent: true });
        }
        
        this.cacheMetadata.delete(cacheKey);
        await this.persistMetadata();
      } catch (error) {
        console.error('ImageCacheService: Failed to remove cached image:', error);
      }
    }
  }

  /**
   * Check if image is cached
   */
  async isImageCached(url: string, options: ImageLoadOptions = {}): Promise<boolean> {
    const normalizedUrl = normalizeImageUrl(url);
    if (!normalizedUrl || !isValidImageUrl(normalizedUrl)) return false;

    const cacheKey = this.generateCacheKey(normalizedUrl, options);
    const cacheInfo = this.cacheMetadata.get(cacheKey);
    
    if (!cacheInfo) return false;
    
    return await this.isCacheEntryValid(cacheInfo);
  }

  /**
   * Get cached image info without loading
   */
  getCachedImageInfo(url: string, options: ImageLoadOptions = {}): CachedImageInfo | null {
    const normalizedUrl = normalizeImageUrl(url);
    if (!normalizedUrl) return null;

    const cacheKey = this.generateCacheKey(normalizedUrl, options);
    return this.cacheMetadata.get(cacheKey) || null;
  }
}

// Export singleton instance
export const imageCacheService = new ImageCacheService();