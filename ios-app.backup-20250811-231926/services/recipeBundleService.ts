// services/recipeBundleService.ts - Offline recipe bundle management with SQLite + FTS5
/**
 * Comprehensive offline recipe storage service using SQLite with FTS5 for full-text search.
 * Implements recipe bundle downloads, local storage, and vector-based similarity search.
 */

import * as SQLite from 'expo-sqlite';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Recipe } from './recipeService';
import { apiClient } from './apiClient';
import { vectorSearchEngine } from '../utils/vectorSearch';

export interface RecipeBundle {
  id: string;
  name: string;
  version: string;
  description: string;
  recipe_count: number;
  download_url: string;
  size_bytes: number;
  created_at: string;
  updated_at: string;
  tags: string[];
}

export interface OfflineRecipe extends Recipe {
  bundle_id: string;
  download_date: string;
  search_vector?: number[]; // For similarity search
  popularity_score?: number;
}

export interface SearchResult {
  recipe: OfflineRecipe;
  relevance_score: number;
  match_type: 'title' | 'ingredient' | 'instruction' | 'tag';
}

export interface BundleStats {
  total_bundles: number;
  total_recipes: number;
  total_size_mb: number;
  last_update: string;
  available_space_mb: number;
}

class RecipeBundleService {
  private db: SQLite.SQLiteDatabase | null = null;
  private readonly DB_NAME = 'recipe_bundles.db';
  private readonly BUNDLE_CACHE_KEY = 'recipe_bundles_cache';
  private readonly MAX_STORAGE_MB = 500; // 500MB limit for recipe storage

  /**
   * Initialize the SQLite database with FTS5 support
   */
  async initializeDatabase(): Promise<void> {
    try {
      this.db = await SQLite.openDatabaseAsync(this.DB_NAME);
      
      // Create main tables
      await this.db.execAsync(`
        PRAGMA journal_mode = WAL;
        PRAGMA foreign_keys = ON;
        
        -- Recipe bundles metadata table
        CREATE TABLE IF NOT EXISTS recipe_bundles (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          version TEXT NOT NULL,
          description TEXT,
          recipe_count INTEGER DEFAULT 0,
          download_url TEXT,
          size_bytes INTEGER DEFAULT 0,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          tags TEXT, -- JSON array of tags
          download_date TEXT,
          is_downloaded INTEGER DEFAULT 0
        );
        
        -- Offline recipes table
        CREATE TABLE IF NOT EXISTS offline_recipes (
          id INTEGER PRIMARY KEY,
          bundle_id TEXT NOT NULL,
          spoonacular_id INTEGER UNIQUE,
          title TEXT NOT NULL,
          image TEXT,
          ready_in_minutes INTEGER,
          servings INTEGER,
          recipe_data TEXT NOT NULL, -- JSON blob of full recipe data
          search_vector TEXT, -- JSON array for similarity search
          popularity_score REAL DEFAULT 0,
          download_date TEXT NOT NULL,
          FOREIGN KEY (bundle_id) REFERENCES recipe_bundles (id) ON DELETE CASCADE
        );
        
        -- Create FTS5 virtual table for full-text search
        CREATE VIRTUAL TABLE IF NOT EXISTS recipe_search USING fts5(
          recipe_id UNINDEXED,
          title,
          ingredients,
          instructions,
          tags,
          content='offline_recipes',
          content_rowid='id'
        );
        
        -- Triggers to keep FTS5 in sync
        CREATE TRIGGER IF NOT EXISTS recipe_search_insert AFTER INSERT ON offline_recipes BEGIN
          INSERT INTO recipe_search(recipe_id, title, ingredients, instructions, tags)
          SELECT 
            NEW.id,
            NEW.title,
            json_extract(NEW.recipe_data, '$.extendedIngredients') as ingredients,
            json_extract(NEW.recipe_data, '$.analyzedInstructions') as instructions,
            json_extract(NEW.recipe_data, '$.dishTypes') as tags;
        END;
        
        CREATE TRIGGER IF NOT EXISTS recipe_search_delete AFTER DELETE ON offline_recipes BEGIN
          DELETE FROM recipe_search WHERE recipe_id = OLD.id;
        END;
        
        CREATE TRIGGER IF NOT EXISTS recipe_search_update AFTER UPDATE ON offline_recipes BEGIN
          DELETE FROM recipe_search WHERE recipe_id = OLD.id;
          INSERT INTO recipe_search(recipe_id, title, ingredients, instructions, tags)
          SELECT 
            NEW.id,
            NEW.title,
            json_extract(NEW.recipe_data, '$.extendedIngredients') as ingredients,
            json_extract(NEW.recipe_data, '$.analyzedInstructions') as instructions,
            json_extract(NEW.recipe_data, '$.dishTypes') as tags;
        END;
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_offline_recipes_bundle ON offline_recipes(bundle_id);
        CREATE INDEX IF NOT EXISTS idx_offline_recipes_spoonacular ON offline_recipes(spoonacular_id);
        CREATE INDEX IF NOT EXISTS idx_offline_recipes_popularity ON offline_recipes(popularity_score DESC);
        CREATE INDEX IF NOT EXISTS idx_bundles_downloaded ON recipe_bundles(is_downloaded);
      `);
      
      console.log('Recipe bundle database initialized successfully');
      
      // Initialize vector search engine
      await vectorSearchEngine.initialize();
    } catch (error) {
      console.error('Failed to initialize recipe bundle database:', error);
      throw error;
    }
  }

  /**
   * Get available recipe bundles from the backend
   */
  async getAvailableBundles(): Promise<RecipeBundle[]> {
    try {
      // Try cache first
      const cached = await AsyncStorage.getItem(this.BUNDLE_CACHE_KEY);
      if (cached) {
        const { bundles, timestamp } = JSON.parse(cached);
        const isExpired = Date.now() - timestamp > 30 * 60 * 1000; // 30 minutes
        if (!isExpired) {
          return bundles;
        }
      }
      
      // Fetch from backend
      const response = await apiClient.get('/recipe-bundles/available');
      const bundles: RecipeBundle[] = response.data;
      
      // Cache the results
      await AsyncStorage.setItem(this.BUNDLE_CACHE_KEY, JSON.stringify({
        bundles,
        timestamp: Date.now()
      }));
      
      return bundles;
    } catch (error) {
      console.error('Failed to fetch available bundles:', error);
      // Return cached data if available, even if expired
      const cached = await AsyncStorage.getItem(this.BUNDLE_CACHE_KEY);
      if (cached) {
        const { bundles } = JSON.parse(cached);
        return bundles;
      }
      return [];
    }
  }

  /**
   * Download and install a recipe bundle
   */
  async downloadBundle(bundleId: string, onProgress?: (progress: number) => void): Promise<void> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      // Check storage space
      const stats = await this.getStorageStats();
      const bundle = await this.getBundleInfo(bundleId);
      
      if (!bundle) {
        throw new Error(`Bundle ${bundleId} not found`);
      }
      
      const bundleSizeMB = bundle.size_bytes / (1024 * 1024);
      if (stats.total_size_mb + bundleSizeMB > this.MAX_STORAGE_MB) {
        throw new Error(`Insufficient storage space. Need ${bundleSizeMB.toFixed(1)}MB, have ${(this.MAX_STORAGE_MB - stats.total_size_mb).toFixed(1)}MB available`);
      }
      
      // Download bundle data
      onProgress?.(0);
      const response = await apiClient.get(`/recipe-bundles/${bundleId}/download`);
      onProgress?.(50);
      
      const { recipes }: { recipes: Recipe[] } = response.data;
      
      // Start transaction
      await this.db!.withTransactionAsync(async () => {
        // Insert bundle metadata
        await this.db!.runAsync(`
          INSERT OR REPLACE INTO recipe_bundles (
            id, name, version, description, recipe_count, download_url,
            size_bytes, created_at, updated_at, tags, download_date, is_downloaded
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [
          bundle.id,
          bundle.name,
          bundle.version,
          bundle.description,
          recipes.length,
          bundle.download_url,
          bundle.size_bytes,
          bundle.created_at,
          bundle.updated_at,
          JSON.stringify(bundle.tags),
          new Date().toISOString(),
          1
        ]);
        
        // Insert recipes
        let processed = 0;
        for (const recipe of recipes) {
          await this.db!.runAsync(`
            INSERT OR REPLACE INTO offline_recipes (
              bundle_id, spoonacular_id, title, image, ready_in_minutes,
              servings, recipe_data, popularity_score, download_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
          `, [
            bundleId,
            recipe.id,
            recipe.title,
            recipe.image || '',
            recipe.readyInMinutes || 0,
            recipe.servings || 1,
            JSON.stringify(recipe),
            recipe.spoonacularScore || 0,
            new Date().toISOString()
          ]);
          
          // Index recipe for vector search
          vectorSearchEngine.indexRecipe(recipe);
          
          processed++;
          onProgress?.(50 + (processed / recipes.length) * 50);
        }
      });
      
      console.log(`Bundle ${bundleId} downloaded successfully with ${recipes.length} recipes`);
    } catch (error) {
      console.error(`Failed to download bundle ${bundleId}:`, error);
      throw error;
    }
  }

  /**
   * Remove a downloaded bundle
   */
  async removeBundle(bundleId: string): Promise<void> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      await this.db!.withTransactionAsync(async () => {
        // Delete recipes (cascade will handle FTS)
        await this.db!.runAsync('DELETE FROM offline_recipes WHERE bundle_id = ?', [bundleId]);
        
        // Delete bundle
        await this.db!.runAsync('DELETE FROM recipe_bundles WHERE id = ?', [bundleId]);
      });
      
      console.log(`Bundle ${bundleId} removed successfully`);
    } catch (error) {
      console.error(`Failed to remove bundle ${bundleId}:`, error);
      throw error;
    }
  }

  /**
   * Search recipes using FTS5 full-text search
   */
  async searchRecipes(query: string, limit: number = 20): Promise<SearchResult[]> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      const searchQuery = query.trim().replace(/[^a-zA-Z0-9\s]/g, '').split(' ').join(' OR ');
      
      const results = await this.db!.getAllAsync(`
        SELECT 
          r.id,
          r.recipe_data,
          r.bundle_id,
          r.download_date,
          r.popularity_score,
          s.bm25(recipe_search) as relevance_score
        FROM recipe_search s
        JOIN offline_recipes r ON r.id = s.recipe_id
        WHERE recipe_search MATCH ?
        ORDER BY relevance_score DESC, r.popularity_score DESC
        LIMIT ?
      `, [searchQuery, limit]);
      
      return results.map((row: any) => {
        const recipe: OfflineRecipe = {
          ...JSON.parse(row.recipe_data),
          bundle_id: row.bundle_id,
          download_date: row.download_date,
          popularity_score: row.popularity_score
        };
        
        return {
          recipe,
          relevance_score: -row.relevance_score, // BM25 returns negative scores
          match_type: 'title' as const // TODO: Determine actual match type
        };
      });
    } catch (error) {
      console.error('Failed to search recipes:', error);
      return [];
    }
  }

  /**
   * Get recipes by similarity using vector search
   */
  async getSimilarRecipes(recipeId: number, limit: number = 10): Promise<OfflineRecipe[]> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      // Use vector search engine for similarity
      const similarityResults = vectorSearchEngine.findSimilarRecipes(recipeId, limit);
      
      if (similarityResults.length === 0) {
        // Fallback to bundle-based similarity
        const results = await this.db!.getAllAsync(`
          SELECT recipe_data, bundle_id, download_date, popularity_score
          FROM offline_recipes 
          WHERE bundle_id = (
            SELECT bundle_id FROM offline_recipes WHERE spoonacular_id = ?
          ) AND spoonacular_id != ?
          ORDER BY popularity_score DESC
          LIMIT ?
        `, [recipeId, recipeId, limit]);
        
        return results.map((row: any) => ({
          ...JSON.parse(row.recipe_data),
          bundle_id: row.bundle_id,
          download_date: row.download_date,
          popularity_score: row.popularity_score
        }));
      }
      
      // Get recipe data for similar recipes
      const similarRecipes: OfflineRecipe[] = [];
      
      for (const result of similarityResults) {
        const recipeData = await this.db!.getFirstAsync(`
          SELECT recipe_data, bundle_id, download_date, popularity_score
          FROM offline_recipes 
          WHERE spoonacular_id = ?
        `, [result.recipe_id]);
        
        if (recipeData) {
          const recipe: OfflineRecipe = {
            ...JSON.parse(recipeData.recipe_data),
            bundle_id: recipeData.bundle_id,
            download_date: recipeData.download_date,
            popularity_score: recipeData.popularity_score
          };
          
          similarRecipes.push(recipe);
        }
      }
      
      return similarRecipes;
    } catch (error) {
      console.error('Failed to get similar recipes:', error);
      return [];
    }
  }

  /**
   * Search recipes by available pantry ingredients using vector similarity
   */
  async searchByPantryIngredients(
    availableIngredients: string[],
    limit: number = 20
  ): Promise<SearchResult[]> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      // Use vector search for ingredient-based similarity
      const similarityResults = vectorSearchEngine.searchByIngredients(
        availableIngredients,
        limit,
        true // Weight available ingredients higher
      );
      
      const searchResults: SearchResult[] = [];
      
      for (const result of similarityResults) {
        const recipeData = await this.db!.getFirstAsync(`
          SELECT recipe_data, bundle_id, download_date, popularity_score
          FROM offline_recipes 
          WHERE spoonacular_id = ?
        `, [result.recipe_id]);
        
        if (recipeData) {
          const recipe: OfflineRecipe = {
            ...JSON.parse(recipeData.recipe_data),
            bundle_id: recipeData.bundle_id,
            download_date: recipeData.download_date,
            popularity_score: recipeData.popularity_score
          };
          
          searchResults.push({
            recipe,
            relevance_score: result.similarity_score,
            match_type: 'ingredient'
          });
        }
      }
      
      return searchResults;
    } catch (error) {
      console.error('Failed to search by pantry ingredients:', error);
      return [];
    }
  }

  /**
   * Get all downloaded bundles
   */
  async getDownloadedBundles(): Promise<RecipeBundle[]> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      const results = await this.db!.getAllAsync(`
        SELECT * FROM recipe_bundles WHERE is_downloaded = 1
        ORDER BY download_date DESC
      `);
      
      return results.map((row: any) => ({
        ...row,
        tags: JSON.parse(row.tags || '[]')
      }));
    } catch (error) {
      console.error('Failed to get downloaded bundles:', error);
      return [];
    }
  }

  /**
   * Get storage statistics
   */
  async getStorageStats(): Promise<BundleStats> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      const stats = await this.db!.getFirstAsync(`
        SELECT 
          COUNT(*) as total_bundles,
          SUM(recipe_count) as total_recipes,
          SUM(size_bytes) as total_bytes,
          MAX(download_date) as last_update
        FROM recipe_bundles 
        WHERE is_downloaded = 1
      `);
      
      return {
        total_bundles: stats?.total_bundles || 0,
        total_recipes: stats?.total_recipes || 0,
        total_size_mb: (stats?.total_bytes || 0) / (1024 * 1024),
        last_update: stats?.last_update || '',
        available_space_mb: this.MAX_STORAGE_MB - ((stats?.total_bytes || 0) / (1024 * 1024))
      };
    } catch (error) {
      console.error('Failed to get storage stats:', error);
      return {
        total_bundles: 0,
        total_recipes: 0,
        total_size_mb: 0,
        last_update: '',
        available_space_mb: this.MAX_STORAGE_MB
      };
    }
  }

  /**
   * Get bundle information
   */
  private async getBundleInfo(bundleId: string): Promise<RecipeBundle | null> {
    const bundles = await this.getAvailableBundles();
    return bundles.find(b => b.id === bundleId) || null;
  }

  /**
   * Clean up old or unused bundles
   */
  async cleanupStorage(keepRecentDays: number = 30): Promise<void> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - keepRecentDays);
      
      const oldBundles = await this.db!.getAllAsync(`
        SELECT id FROM recipe_bundles 
        WHERE is_downloaded = 1 AND download_date < ?
        ORDER BY download_date ASC
      `, [cutoffDate.toISOString()]);
      
      for (const bundle of oldBundles) {
        await this.removeBundle(bundle.id);
      }
      
      console.log(`Cleaned up ${oldBundles.length} old bundles`);
    } catch (error) {
      console.error('Failed to cleanup storage:', error);
    }
  }

  /**
   * Check if a recipe is available offline
   */
  async isRecipeAvailableOffline(spoonacularId: number): Promise<boolean> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      const result = await this.db!.getFirstAsync(`
        SELECT 1 FROM offline_recipes WHERE spoonacular_id = ?
      `, [spoonacularId]);
      
      return !!result;
    } catch (error) {
      console.error('Failed to check recipe availability:', error);
      return false;
    }
  }

  /**
   * Get offline recipe by ID
   */
  async getOfflineRecipe(spoonacularId: number): Promise<OfflineRecipe | null> {
    if (!this.db) {
      await this.initializeDatabase();
    }

    try {
      const result = await this.db!.getFirstAsync(`
        SELECT recipe_data, bundle_id, download_date, popularity_score
        FROM offline_recipes 
        WHERE spoonacular_id = ?
      `, [spoonacularId]);
      
      if (!result) {
        return null;
      }
      
      return {
        ...JSON.parse(result.recipe_data),
        bundle_id: result.bundle_id,
        download_date: result.download_date,
        popularity_score: result.popularity_score
      };
    } catch (error) {
      console.error('Failed to get offline recipe:', error);
      return null;
    }
  }
}

// Export singleton instance
export const recipeBundleService = new RecipeBundleService();