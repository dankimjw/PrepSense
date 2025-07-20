// utils/environmentValidator.ts - Environment configuration validator for PrepSense

import { Platform } from 'react-native';

interface ValidationResult {
  isValid: boolean;
  message: string;
  status: 'OK' | 'ERROR' | 'WARNING';
}

interface EnvironmentStatus {
  allValid: boolean;
  checks: {
    apiUrl: ValidationResult;
    googleCredentials: ValidationResult;
    openAIKey: ValidationResult;
    environment: ValidationResult;
  };
}

// Color codes for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

class EnvironmentValidator {
  private static instance: EnvironmentValidator;
  
  private constructor() {}
  
  static getInstance(): EnvironmentValidator {
    if (!EnvironmentValidator.instance) {
      EnvironmentValidator.instance = new EnvironmentValidator();
    }
    return EnvironmentValidator.instance;
  }

  // Main validation function
  async validateEnvironment(): Promise<EnvironmentStatus> {
    console.log(`\n${colors.cyan}${colors.bright}========================================${colors.reset}`);
    console.log(`${colors.cyan}${colors.bright}🔍 PrepSense Environment Validation${colors.reset}`);
    console.log(`${colors.cyan}${colors.bright}========================================${colors.reset}\n`);

    const checks = {
      environment: this.checkEnvironment(),
      apiUrl: await this.checkAPIUrl(),
      googleCredentials: await this.checkGoogleCredentials(),
      openAIKey: await this.checkOpenAIKey(),
    };

    const allValid = Object.values(checks).every(check => check.status !== 'ERROR');

    // Display results
    this.displayResults(checks);

    console.log(`\n${colors.cyan}${colors.bright}========================================${colors.reset}\n`);

    return {
      allValid,
      checks,
    };
  }

  private checkEnvironment(): ValidationResult {
    const isDev = __DEV__;
    const platform = Platform.OS;
    const nodeEnv = process.env.NODE_ENV;

    return {
      isValid: true,
      message: `${isDev ? 'Development' : 'Production'} mode on ${platform} (NODE_ENV: ${nodeEnv || 'not set'})`,
      status: 'OK',
    };
  }

  private async checkAPIUrl(): Promise<ValidationResult> {
    const apiUrl = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8001/api/v1';
    
    if (!process.env.EXPO_PUBLIC_API_BASE_URL) {
      console.warn('⚠️  EXPO_PUBLIC_API_BASE_URL not set!');
      console.warn('Using fallback URL:', apiUrl);
      console.warn('To fix: Stop the app and run: python run_app.py');
      
      return {
        isValid: false,
        message: 'EXPO_PUBLIC_API_BASE_URL not set. App may not connect properly!',
        status: 'ERROR',
      };
    }

    // Detect hardcoded or outdated IPs
    const ipMatch = apiUrl.match(/(\d+\.\d+\.\d+\.\d+)/);
    if (ipMatch && ipMatch[1] !== '127.0.0.1') {
      console.warn(`⚠️  Detected IP address: ${ipMatch[1]}`);
      console.warn('This IP may be outdated if your network has changed.');
    }

    // Try to validate the URL format
    try {
      const url = new URL(apiUrl);
      
      // In development, check if the backend is reachable
      if (__DEV__) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 5000);
          
          const response = await fetch(`${apiUrl}/health`, {
            signal: controller.signal,
          });
          
          clearTimeout(timeoutId);
          
          if (response.ok) {
            return {
              isValid: true,
              message: `${apiUrl} - Backend is reachable`,
              status: 'OK',
            };
          } else {
            return {
              isValid: false,
              message: `${apiUrl} - Backend returned ${response.status}`,
              status: 'WARNING',
            };
          }
        } catch (error) {
          return {
            isValid: false,
            message: `${apiUrl} - Backend not reachable. Is it running?`,
            status: 'WARNING',
          };
        }
      }
      
      return {
        isValid: true,
        message: apiUrl,
        status: 'OK',
      };
    } catch (error) {
      return {
        isValid: false,
        message: `Invalid URL format: ${apiUrl}`,
        status: 'ERROR',
      };
    }
  }

  private async checkGoogleCredentials(): Promise<ValidationResult> {
    // Check if we can reach the backend's health endpoint
    const apiUrl = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8001/api/v1';
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`${apiUrl}/health`, {
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        const googleConfigured = data.environment?.google_cloud_configured;
        
        if (googleConfigured) {
          return {
            isValid: true,
            message: 'Backend has valid Google Cloud credentials',
            status: 'OK',
          };
        } else {
          return {
            isValid: false,
            message: 'Backend Google Cloud credentials not configured',
            status: 'WARNING',
          };
        }
      } else {
        return {
          isValid: false,
          message: 'Unable to verify Google Cloud credentials',
          status: 'WARNING',
        };
      }
    } catch (error) {
      return {
        isValid: false,
        message: 'Cannot verify - Backend not reachable',
        status: 'WARNING',
      };
    }
  }

  private async checkOpenAIKey(): Promise<ValidationResult> {
    // Check if the backend has OpenAI configured
    const apiUrl = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8001/api/v1';
    
    try {
      // We'll check this by attempting a simple chat message
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`${apiUrl}/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'test',
          user_id: 111,
          use_preferences: false,
        }),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        return {
          isValid: true,
          message: 'Backend has valid OpenAI API key',
          status: 'OK',
        };
      } else if (response.status === 500) {
        const data = await response.json();
        if (data.detail?.includes('OpenAI') || data.detail?.includes('API key')) {
          return {
            isValid: false,
            message: 'Backend OpenAI API key issue',
            status: 'ERROR',
          };
        }
      }
      
      return {
        isValid: false,
        message: 'Unable to verify OpenAI API key',
        status: 'WARNING',
      };
    } catch (error) {
      return {
        isValid: false,
        message: 'Cannot verify - Backend not reachable',
        status: 'WARNING',
      };
    }
  }

  private displayResults(checks: EnvironmentStatus['checks']): void {
    const formatStatus = (result: ValidationResult): string => {
      const icon = result.status === 'OK' ? '✅' : result.status === 'WARNING' ? '⚠️ ' : '❌';
      const color = result.status === 'OK' ? colors.green : result.status === 'WARNING' ? colors.yellow : colors.red;
      return `${icon} ${color}${result.status}${colors.reset}`;
    };

    console.log(`${colors.blue}Environment:${colors.reset} ${formatStatus(checks.environment)} - ${checks.environment.message}`);
    console.log(`${colors.blue}API URL:${colors.reset} ${formatStatus(checks.apiUrl)} - ${checks.apiUrl.message}`);
    console.log(`${colors.blue}GCP JSON File:${colors.reset} ${formatStatus(checks.googleCredentials)} - ${checks.googleCredentials.message}`);
    console.log(`${colors.blue}OpenAI API Key:${colors.reset} ${formatStatus(checks.openAIKey)} - ${checks.openAIKey.message}`);

    // Show summary
    const errorCount = Object.values(checks).filter(c => c.status === 'ERROR').length;
    const warningCount = Object.values(checks).filter(c => c.status === 'WARNING').length;
    
    console.log(`\n${colors.bright}Summary:${colors.reset}`);
    if (errorCount > 0) {
      console.log(`${colors.red}❌ ${errorCount} error(s) found${colors.reset}`);
    }
    if (warningCount > 0) {
      console.log(`${colors.yellow}⚠️  ${warningCount} warning(s) found${colors.reset}`);
    }
    if (errorCount === 0 && warningCount === 0) {
      console.log(`${colors.green}✅ All checks passed!${colors.reset}`);
    }
  }

  // Helper to display on each screen load
  displayScreenLoad(screenName: string): void {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`\n${colors.blue}[${timestamp}] Loading screen: ${colors.bright}${screenName}${colors.reset}`);
  }
}

export const envValidator = EnvironmentValidator.getInstance();
export type { EnvironmentStatus, ValidationResult };