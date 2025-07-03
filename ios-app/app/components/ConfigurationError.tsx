// app/components/ConfigurationError.tsx - Configuration error screen for PrepSense

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Linking,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { EnvironmentStatus } from '../../utils/environmentValidator';

interface ConfigurationErrorProps {
  status: EnvironmentStatus;
  onRetry?: () => void;
}

export function ConfigurationError({ status, onRetry }: ConfigurationErrorProps) {
  const openDocs = () => {
    Linking.openURL('https://github.com/YOUR_REPO/PrepSense/blob/main/README.md');
  };

  const getIconForStatus = (status: 'OK' | 'ERROR' | 'WARNING') => {
    switch (status) {
      case 'OK':
        return <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />;
      case 'WARNING':
        return <Ionicons name="warning" size={24} color="#FF9800" />;
      case 'ERROR':
        return <Ionicons name="close-circle" size={24} color="#F44336" />;
    }
  };

  const hasErrors = Object.values(status.checks).some(check => check.status === 'ERROR');

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Ionicons name="settings-outline" size={64} color="#666" />
          <Text style={styles.title}>Configuration Issues Detected</Text>
          <Text style={styles.subtitle}>
            {hasErrors 
              ? 'Some required configurations are missing or invalid.'
              : 'Some configurations need attention.'}
          </Text>
        </View>

        <View style={styles.checksContainer}>
          <Text style={styles.sectionTitle}>Configuration Status</Text>
          
          {/* Environment Check */}
          <View style={styles.checkItem}>
            <View style={styles.checkHeader}>
              {getIconForStatus(status.checks.environment.status)}
              <Text style={styles.checkTitle}>Environment</Text>
            </View>
            <Text style={styles.checkMessage}>{status.checks.environment.message}</Text>
          </View>

          {/* API URL Check */}
          <View style={styles.checkItem}>
            <View style={styles.checkHeader}>
              {getIconForStatus(status.checks.apiUrl.status)}
              <Text style={styles.checkTitle}>API URL</Text>
            </View>
            <Text style={styles.checkMessage}>{status.checks.apiUrl.message}</Text>
            {status.checks.apiUrl.status !== 'OK' && (
              <Text style={styles.helpText}>
                Make sure the backend is running and EXPO_PUBLIC_API_BASE_URL is set correctly.
              </Text>
            )}
          </View>

          {/* Google Cloud Check */}
          <View style={styles.checkItem}>
            <View style={styles.checkHeader}>
              {getIconForStatus(status.checks.googleCredentials.status)}
              <Text style={styles.checkTitle}>Google Cloud Credentials</Text>
            </View>
            <Text style={styles.checkMessage}>{status.checks.googleCredentials.message}</Text>
            {status.checks.googleCredentials.status === 'ERROR' && (
              <Text style={styles.helpText}>
                Ensure GOOGLE_APPLICATION_CREDENTIALS is set in the backend environment.
              </Text>
            )}
          </View>

          {/* OpenAI Check */}
          <View style={styles.checkItem}>
            <View style={styles.checkHeader}>
              {getIconForStatus(status.checks.openAIKey.status)}
              <Text style={styles.checkTitle}>OpenAI API Key</Text>
            </View>
            <Text style={styles.checkMessage}>{status.checks.openAIKey.message}</Text>
            {status.checks.openAIKey.status === 'ERROR' && (
              <Text style={styles.helpText}>
                Set OPENAI_API_KEY in the backend environment or create config/openai_key.txt.
              </Text>
            )}
          </View>
        </View>

        <View style={styles.instructionsContainer}>
          <Text style={styles.instructionsTitle}>Setup Instructions:</Text>
          <Text style={styles.instruction}>1. Start the backend server: cd backend_gateway && python app.py</Text>
          <Text style={styles.instruction}>2. Set environment variables in backend_gateway/.env:</Text>
          <Text style={styles.codeBlock}>
            GOOGLE_APPLICATION_CREDENTIALS=path/to/gcp-key.json{'\n'}
            OPENAI_API_KEY=your-openai-api-key
          </Text>
          <Text style={styles.instruction}>3. For the iOS app, set in your terminal:</Text>
          <Text style={styles.codeBlock}>
            export EXPO_PUBLIC_API_BASE_URL=http://YOUR_IP:8001/api/v1
          </Text>
        </View>

        <View style={styles.actions}>
          {onRetry && (
            <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
              <Ionicons name="refresh" size={20} color="#fff" />
              <Text style={styles.retryButtonText}>Retry Validation</Text>
            </TouchableOpacity>
          )}
          
          <TouchableOpacity style={styles.docsButton} onPress={openDocs}>
            <Ionicons name="document-text-outline" size={20} color="#297A56" />
            <Text style={styles.docsButtonText}>View Documentation</Text>
          </TouchableOpacity>

          {!hasErrors && (
            <TouchableOpacity style={styles.continueButton} onPress={() => {}}>
              <Text style={styles.continueButtonText}>Continue Anyway</Text>
            </TouchableOpacity>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
    paddingTop: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  checksContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
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
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  checkItem: {
    marginBottom: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  checkHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  checkTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginLeft: 8,
  },
  checkMessage: {
    fontSize: 14,
    color: '#666',
    marginLeft: 32,
  },
  helpText: {
    fontSize: 12,
    color: '#999',
    marginLeft: 32,
    marginTop: 4,
    fontStyle: 'italic',
  },
  instructionsContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  instructionsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  instruction: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    lineHeight: 20,
  },
  codeBlock: {
    backgroundColor: '#f5f5f5',
    padding: 12,
    borderRadius: 8,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 12,
    marginVertical: 8,
    marginLeft: 16,
  },
  actions: {
    gap: 12,
  },
  retryButton: {
    flexDirection: 'row',
    backgroundColor: '#297A56',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  docsButton: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#297A56',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  docsButtonText: {
    color: '#297A56',
    fontSize: 16,
    fontWeight: '600',
  },
  continueButton: {
    backgroundColor: '#f0f0f0',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  continueButtonText: {
    color: '#666',
    fontSize: 16,
  },
});