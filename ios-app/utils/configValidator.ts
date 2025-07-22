/**
 * Configuration validator for PrepSense
 * Ensures backend connectivity and proper environment setup
 */

import { Config } from '../config';

export interface ConfigValidationResult {
  isValid: boolean;
  warnings: string[];
  errors: string[];
  apiUrl: string;
  detectedIP?: string;
}

/**
 * Validates the current configuration and network setup
 */
export async function validateConfiguration(): Promise<ConfigValidationResult> {
  const result: ConfigValidationResult = {
    isValid: true,
    warnings: [],
    errors: [],
    apiUrl: Config.API_BASE_URL,
  };

  // Check if we're using the fallback localhost URL
  if (Config.API_BASE_URL.includes('127.0.0.1') || Config.API_BASE_URL.includes('localhost')) {
    result.warnings.push(
      '⚠️ Using localhost URL. The app may not connect to the backend properly.\n' +
      'Make sure to run the app with: python run_app.py'
    );
  }

  // Check if EXPO_PUBLIC_API_BASE_URL was set
  if (!process.env.EXPO_PUBLIC_API_BASE_URL) {
    result.errors.push(
      '❌ EXPO_PUBLIC_API_BASE_URL environment variable not set.\n' +
      'The app cannot detect your backend server.\n' +
      'Please restart the app using: python run_app.py'
    );
    result.isValid = false;
  }

  // Try to detect if we're using an old/invalid IP
  const urlMatch = Config.API_BASE_URL.match(/(\d+\.\d+\.\d+\.\d+):(\d+)/);
  if (urlMatch) {
    const [_, ip, port] = urlMatch;
    result.detectedIP = ip;

    // Check if port is correct
    if (port !== '8001') {
      result.errors.push(
        `❌ Wrong backend port: ${port}. Expected: 8001`
      );
      result.isValid = false;
    }

    // Try to ping the backend
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const response = await fetch(`${Config.API_BASE_URL}/health`, {
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        result.warnings.push(
          `⚠️ Backend returned status ${response.status}. It may not be fully operational.`
        );
      }
    } catch (error) {
      result.errors.push(
        `❌ Cannot connect to backend at ${Config.API_BASE_URL}\n` +
        'Possible causes:\n' +
        '1. Backend is not running (run: python run_app.py)\n' +
        '2. Your IP address has changed (restart the app)\n' +
        '3. Firewall is blocking the connection'
      );
      result.isValid = false;
    }
  }

  return result;
}

/**
 * Get instructions for fixing configuration issues
 */
export function getConfigFixInstructions(): string[] {
  return [
    '🔧 To fix configuration issues:',
    '',
    '1. Stop the current app (Ctrl+C)',
    '2. Make sure you\'re in the project root directory',
    '3. Activate your virtual environment:',
    '   source venv/bin/activate',
    '4. Run the unified launcher:',
    '   python run_app.py',
    '',
    'This will automatically:',
    '- Detect your current IP address',
    '- Start the backend on port 8001',
    '- Configure the iOS app with the correct backend URL',
    '',
    'If you\'re on a team and sharing code:',
    '- Never commit hardcoded IP addresses',
    '- Always use run_app.py to start the app',
    '- Each team member\'s IP will be detected automatically',
  ];
}

/**
 * Format validation result for display
 */
export function formatValidationResult(result: ConfigValidationResult): string {
  const lines: string[] = [];

  lines.push(`API URL: ${result.apiUrl}`);
  
  if (result.detectedIP) {
    lines.push(`Detected IP: ${result.detectedIP}`);
  }

  if (result.errors.length > 0) {
    lines.push('\n❌ ERRORS:');
    result.errors.forEach(error => lines.push(error));
  }

  if (result.warnings.length > 0) {
    lines.push('\n⚠️  WARNINGS:');
    result.warnings.forEach(warning => lines.push(warning));
  }

  if (!result.isValid) {
    lines.push('\n' + getConfigFixInstructions().join('\n'));
  }

  return lines.join('\n');
}