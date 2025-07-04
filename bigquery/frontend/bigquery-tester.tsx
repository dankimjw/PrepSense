import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  Switch
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
// TODO: Remove when implementing real authentication
// import { useAuth } from '../context/AuthContext';
import { CustomHeader } from './components/CustomHeader';
// TODO: Remove when implementing real backend API
// import { Config } from '../config';

type QueryType = 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' | 'CUSTOM';

interface TableInfo {
  tableId: string;
  description: string;
}

const MOCK_TABLES: TableInfo[] = [
  { tableId: 'users', description: 'User accounts and profiles' },
  { tableId: 'inventory', description: 'Inventory items' },
  { tableId: 'transactions', description: 'Transaction history' },
  { tableId: 'food_items', description: 'Food items in inventory' },
  { tableId: 'expenses', description: 'Expense tracking' },
];

// Get API base URL from environment or default
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8001/api/v1';

export default function BigQueryTester() {
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [queryType, setQueryType] = useState<QueryType>('SELECT');
  const [query, setQuery] = useState<string>('');
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [isMockMode, setIsMockMode] = useState<boolean>(false); // Changed to false for live mode default
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [queryResult, setQueryResult] = useState<any>(null);
  const [showResults, setShowResults] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize component
  useEffect(() => {
    loadTables();
  }, []);

  // Load available tables on component mount
  const loadTables = async () => {
    try {
      setIsLoading(true);
      
      if (isMockMode) {
        // Use mock data
        setTables(MOCK_TABLES);
        if (MOCK_TABLES.length > 0) {
          setSelectedTable(MOCK_TABLES[0].tableId);
          // Generate initial query
          setTimeout(() => {
            updateQuery();
          }, 100);
        }
      } else {
        // Real API call to get tables
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout for table loading
        
        try {
          const response = await fetch(`${API_BASE_URL}/bigquery/tables`, {
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
          
          if (response.ok) {
            const data = await response.json();
            setTables(data);
            if (data.length > 0) {
              setSelectedTable(data[0].tableId);
              // Generate initial query
              setTimeout(() => {
                updateQuery();
              }, 100);
            }
          } else {
            throw new Error('Failed to load tables from API');
          }
        } catch (apiError: unknown) {
          clearTimeout(timeoutId);
          console.warn('API call failed, falling back to mock data:', apiError);
          setTables(MOCK_TABLES);
          if (MOCK_TABLES.length > 0) {
            setSelectedTable(MOCK_TABLES[0].tableId);
            setTimeout(() => {
              updateQuery();
            }, 100);
          }
        }
      }
    } catch (err) {
      console.error('Error loading tables:', err);
      setError('Failed to load tables');
      // Fallback to mock data
      setTables(MOCK_TABLES);
      if (MOCK_TABLES.length > 0) {
        setSelectedTable(MOCK_TABLES[0].tableId);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Update tables when mock mode changes
  useEffect(() => {
    loadTables();
  }, [isMockMode]);

  // Generate a sample query based on selected table and query type
  const generateSampleQuery = (): string => {
    if (!selectedTable) return '';
    
    const fullTableName = `\`adsp-34002-on02-prep-sense\`.\`Inventory\`.\`${selectedTable}\``;
    
    switch (queryType) {
      case 'SELECT':
        // Generate specific queries based on table
        switch (selectedTable) {
          case 'user':
            return `-- Get all users
SELECT
  *
FROM
  ${fullTableName} AS user;`;
          case 'user_preference':
            return `-- Get all user preferences
SELECT
  *
FROM
  ${fullTableName} AS pref;`;
          case 'pantry':
            return `-- Get all pantry records
SELECT
  *
FROM
  ${fullTableName} AS pantry;`;
          case 'pantry_items':
            return `-- Get all pantry items
SELECT
  *
FROM
  ${fullTableName} AS items;`;
          case 'products':
            return `-- Get all products
SELECT
  *
FROM
  ${fullTableName} AS products;`;
          case 'recipies':
            return `-- Get all recipes
SELECT
  *
FROM
  ${fullTableName} AS recipes;`;
          default:
            return `-- Get all records from ${selectedTable}
SELECT
  *
FROM
  ${fullTableName}
LIMIT 10;`;
        }
      case 'INSERT':
        return `-- Insert example for ${selectedTable}
INSERT INTO ${fullTableName} 
  (column1, column2) 
VALUES 
  ('value1', 'value2');`;
      case 'UPDATE':
        return `-- Update example for ${selectedTable}
UPDATE ${fullTableName} 
SET 
  column1 = 'new_value' 
WHERE 
  id = 1;`;
      case 'DELETE':
        return `-- Delete example for ${selectedTable}
DELETE FROM ${fullTableName} 
WHERE 
  id = 1;`;
      case 'CUSTOM':
        return `-- Write your custom SQL query here
SELECT 
  *
FROM
  ${fullTableName}
LIMIT 10;`;
      default:
        return `-- Get all records from ${selectedTable}
SELECT
  *
FROM
  ${fullTableName}
LIMIT 10;`;
    }
  };
  
  // Update query when table or query type changes
  const updateQuery = () => {
    if (queryType !== 'CUSTOM') {
      setQuery(generateSampleQuery());
    }
  };

  // Format query results for display
  const formatResult = (result: any): string => {
    if (!result) return 'No results';
    
    try {
      if (typeof result === 'string') {
        return result;
      }
      
      if (Array.isArray(result)) {
        if (result.length === 0) {
          return 'Query executed successfully. No rows returned.';
        }
        
        // Format as table-like display
        const formatted = result.map((row, index) => {
          const rowStr = JSON.stringify(row, null, 2);
          return `Row ${index + 1}:\n${rowStr}`;
        }).join('\n\n');
        
        return `Results (${result.length} rows):\n\n${formatted}`;
      }
      
      // Handle other object types
      return JSON.stringify(result, null, 2);
    } catch (error) {
      return `Error formatting results: ${error}`;
    }
  };

  // Execute the query
  const executeQuery = async () => {
    if (!query.trim()) {
      Alert.alert('Error', 'Please enter a query');
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      if (isMockMode) {
        // Mock response
        await new Promise(resolve => setTimeout(resolve, 1000));
        setQueryResult({
          success: true,
          query: query,
          result: [
            { id: 1, name: 'Example Result', value: 'Test Data' },
            { id: 2, name: 'Another Row', value: 'More Data' }
          ],
          execution_time: '1.23s',
          rows_affected: queryType !== 'SELECT' ? 1 : undefined
        });
      } else {
        // Real API call to backend
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        try {
          const response = await fetch(`${API_BASE_URL}/bigquery/execute`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              query,
              queryType,
              table: selectedTable
            }),
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const data = await response.json();
          
          if (!data.success && data.error) {
            throw new Error(data.error);
          }
          
          setQueryResult(data);
        } catch (error: unknown) {
          if (error instanceof Error && error.name === 'AbortError') {
            setError('Query timed out');
          } else {
            console.error('Query execution error:', error);
            setError(`Failed to execute query: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
        }
      }
      
      setShowResults(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <CustomHeader 
        title="BigQuery Tester" 
        showBackButton={true}
        showDbButton={false}
      />
      <KeyboardAvoidingView 
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
        >
          {/* Mode Toggle */}
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
          </View>

          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Table Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Table</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={selectedTable}
                onValueChange={(itemValue: string) => {
                  setSelectedTable(itemValue);
                  setQueryType('SELECT');
                  updateQuery();
                }}
                style={styles.picker}
                dropdownIconColor="#333"
              >
                {tables.map((table) => (
                  <Picker.Item 
                    key={table.tableId} 
                    label={`${table.tableId} - ${table.description}`} 
                    value={table.tableId} 
                  />
                ))}
              </Picker>
            </View>
          </View>

          {/* Query Type */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Query Type</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={queryType}
                onValueChange={(itemValue: QueryType) => {
                  setQueryType(itemValue);
                  updateQuery();
                }}
                style={styles.picker}
                dropdownIconColor="#333"
              >
                <Picker.Item label="SELECT - Read data" value="SELECT" />
                <Picker.Item label="INSERT - Add new records" value="INSERT" />
                <Picker.Item label="UPDATE - Modify records" value="UPDATE" />
                <Picker.Item label="DELETE - Remove records" value="DELETE" />
                <Picker.Item label="CUSTOM - Write your own query" value="CUSTOM" />
              </Picker>
            </View>
          </View>

          {/* Query Input */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              {queryType === 'CUSTOM' ? 'Your SQL Query' : 'Generated Query'}
            </Text>
            <TextInput
              style={[styles.input, styles.queryInput]}
              multiline
              value={query}
              onChangeText={setQuery}
              placeholder="Enter your SQL query here..."
              placeholderTextColor="#999"
              editable={queryType === 'CUSTOM'}
            />
            {queryType !== 'CUSTOM' && (
              <Text style={styles.helperText}>
                This query is automatically generated. Switch to CUSTOM to edit.
              </Text>
            )}
          </View>

          {/* Quick Actions */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Quick Actions</Text>
            <View style={styles.quickActionsRow}>
              <TouchableOpacity
                style={[styles.quickActionButton, styles.clearButton]}
                onPress={() => {
                  setQuery('');
                  setQueryResult(null);
                  setShowResults(false);
                  setError(null);
                }}
              >
                <Text style={styles.quickActionText}>🗑️ Clear</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.quickActionButton, styles.refreshButton]}
                onPress={() => {
                  updateQuery();
                  setQueryResult(null);
                  setShowResults(false);
                  setError(null);
                }}
              >
                <Text style={styles.quickActionText}>🔄 Regenerate</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.quickActionButton, styles.copyButton]}
                onPress={() => {
                  Alert.alert(
                    'Query Copied',
                    'Query has been copied to clipboard (simulated for prototype)',
                    [{ text: 'OK' }]
                  );
                }}
              >
                <Text style={styles.quickActionText}>📋 Copy</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Execute Button */}
          <TouchableOpacity 
            style={[styles.button, isLoading && styles.buttonDisabled]}
            onPress={executeQuery}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>
                {isMockMode ? '🔄 Test Query (Mock Mode)' : '🚀 Execute Query (Live)'}
              </Text>
            )}
          </TouchableOpacity>

          {/* Results Section */}
          {queryResult && showResults && (
            <View style={styles.section}>
              <View style={styles.resultsHeader}>
                <Text style={styles.sectionTitle}>Results</Text>
                <TouchableOpacity onPress={() => setShowResults(false)}>
                  <Text style={styles.hideButton}>Hide</Text>
                </TouchableOpacity>
              </View>
              <View style={styles.resultsContainer}>
                <Text style={styles.resultText}>
                  {formatResult(queryResult)}
                </Text>
              </View>
            </View>
          )}

          {/* Help Section */}
          <View style={styles.helpSection}>
            <Text style={styles.helpTitle}>Need Help?</Text>
            <Text style={styles.helpText}>
              • Use the dropdowns to generate sample queries
            </Text>
            <Text style={styles.helpText}>
              • Switch to CUSTOM mode to write your own SQL
            </Text>
            <Text style={styles.helpText}>
              • Mock mode lets you test without affecting real data
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  keyboardView: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  section: {
    marginBottom: 20,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    padding: 12,
    backgroundColor: '#fff',
    borderRadius: 8,
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
    color: '#1b6b45',
    fontWeight: '600',
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#c62828',
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 8,
  },
  picker: {
    width: '100%',
    backgroundColor: '#fff',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#333',
    backgroundColor: '#fff',
  },
  queryInput: {
    minHeight: 100,
    textAlignVertical: 'top',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 13,
  },
  helperText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontStyle: 'italic',
  },
  button: {
    backgroundColor: '#1b6b45',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 24,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  hideButton: {
    color: '#1b6b45',
    fontWeight: '600',
  },
  resultsContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 12,
  },
  resultText: {
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 12,
    color: '#333',
  },
  helpSection: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#e8f5e9',
    borderRadius: 8,
  },
  helpTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#1b6b45',
  },
  helpText: {
    fontSize: 14,
    color: '#2e7d32',
    marginBottom: 4,
  },
  quickActionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 8,
  },
  quickActionButton: {
    padding: 8,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    width: 80,
  },
  clearButton: {
    backgroundColor: '#ff9800',
  },
  refreshButton: {
    backgroundColor: '#4caf50',
  },
  copyButton: {
    backgroundColor: '#2196f3',
  },
  quickActionText: {
    fontSize: 14,
    color: '#fff',
  },
});
