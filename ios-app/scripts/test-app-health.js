#!/usr/bin/env node

/**
 * Comprehensive App Health Testing Script
 * 
 * This script runs a complete suite of tests to validate:
 * - Backend connectivity and health
 * - All critical API endpoints
 * - Data integrity and response validation
 * - Error handling scenarios
 * - Performance and timeout handling
 */

const fs = require('fs');
const path = require('path');

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8001/api/v1';

console.log('🏥 PrepSense App Health Check');
console.log('=============================');
console.log(`API Base URL: ${API_BASE_URL}`);
console.log(`Timestamp: ${new Date().toISOString()}`);
console.log('');

// Test configurations
const TESTS = [
  {
    category: 'Core Services',
    tests: [
      {
        name: 'Health Check',
        endpoint: '/health',
        method: 'GET',
        critical: true,
        validate: (data) => data.status === 'healthy',
        timeout: 5000,
      },
      {
        name: 'Database Connection',
        endpoint: '/health',
        method: 'GET',
        critical: true,
        validate: (data) => data.environment?.database_connected === true,
        timeout: 5000,
      }
    ]
  },
  {
    category: 'Pantry Operations',
    tests: [
      {
        name: 'Get Pantry Items',
        endpoint: '/pantry/user/111/items',
        method: 'GET',
        critical: true,
        validate: (data) => Array.isArray(data) && data.length > 0,
        timeout: 10000,
      },
      {
        name: 'Pantry Data Integrity',
        endpoint: '/pantry/user/111/items',
        method: 'GET',
        critical: true,
        validate: (data) => {
          if (!Array.isArray(data) || data.length === 0) return false;
          const item = data[0];
          return item.product_name && typeof item.quantity === 'number';
        },
        timeout: 10000,
      }
    ]
  },
  {
    category: 'Recipe Discovery',
    tests: [
      {
        name: 'Recipes from Pantry',
        endpoint: '/recipes/search/from-pantry',
        method: 'POST',
        body: {
          user_id: 111,
          max_missing_ingredients: 5,
          use_expiring_first: true
        },
        critical: true,
        validate: (data) => data.recipes && Array.isArray(data.recipes),
        timeout: 15000,
      },
      {
        name: 'Recipe Search Results',
        endpoint: '/recipes/search/from-pantry',
        method: 'POST',
        body: {
          user_id: 111,
          max_missing_ingredients: 5
        },
        critical: true,
        validate: (data) => {
          if (!data.recipes || !Array.isArray(data.recipes)) return false;
          if (data.recipes.length === 0) return false;
          const recipe = data.recipes[0];
          return recipe.id && recipe.title && typeof recipe.usedIngredientCount === 'number';
        },
        timeout: 15000,
      },
      {
        name: 'Random Recipes',
        endpoint: '/recipes/random?number=5',
        method: 'GET',
        critical: false,
        validate: (data) => data.recipes && Array.isArray(data.recipes) && data.recipes.length > 0,
        timeout: 10000,
      }
    ]
  },
  {
    category: 'Error Handling',
    tests: [
      {
        name: 'Invalid Endpoint',
        endpoint: '/nonexistent-endpoint',
        method: 'GET',
        critical: false,
        expectedStatus: 404,
        validate: () => true, // We expect this to fail
        timeout: 5000,
      },
      {
        name: 'Invalid User ID',
        endpoint: '/pantry/user/99999/items',
        method: 'GET',
        critical: false,
        validate: (data) => Array.isArray(data), // Should return empty array
        timeout: 5000,
      }
    ]
  },
  {
    category: 'Performance',
    tests: [
      {
        name: 'Fast Health Check',
        endpoint: '/health',
        method: 'GET',
        critical: false,
        validate: (data) => data.status === 'healthy',
        timeout: 2000, // Stricter timeout
        maxResponseTime: 1000,
      },
      {
        name: 'Large Pantry Query',
        endpoint: '/pantry/user/111/items',
        method: 'GET',
        critical: false,
        validate: (data) => Array.isArray(data),
        timeout: 8000,
        maxResponseTime: 5000,
      }
    ]
  }
];

async function runTest(test) {
  const startTime = Date.now();
  const { name, endpoint, method, body, expectedStatus = 200, validate, timeout = 10000, maxResponseTime } = test;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    clearTimeout(timeoutId);

    const responseTime = Date.now() - startTime;

    if (response.status !== expectedStatus) {
      return {
        success: false,
        error: `Expected status ${expectedStatus}, got ${response.status}`,
        responseTime,
      };
    }

    let data;
    try {
      data = await response.json();
    } catch (e) {
      data = null;
    }

    // Validate response time if specified
    if (maxResponseTime && responseTime > maxResponseTime) {
      return {
        success: false,
        error: `Response too slow: ${responseTime}ms (max: ${maxResponseTime}ms)`,
        responseTime,
        data,
      };
    }

    // Validate response data if validator provided
    if (validate && !validate(data)) {
      return {
        success: false,
        error: 'Response validation failed',
        responseTime,
        data,
      };
    }

    return {
      success: true,
      responseTime,
      data,
    };

  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      success: false,
      error: error.name === 'AbortError' ? 'Request timeout' : error.message,
      responseTime,
    };
  }
}

async function runAllTests() {
  const results = {
    timestamp: new Date().toISOString(),
    apiBaseUrl: API_BASE_URL,
    categories: [],
    summary: {
      totalTests: 0,
      passed: 0,
      failed: 0,
      criticalFailures: 0,
      averageResponseTime: 0,
    }
  };

  let totalResponseTime = 0;
  let responseTimeCount = 0;

  for (const category of TESTS) {
    console.log(`\n📂 ${category.category}`);
    console.log('─'.repeat(category.category.length + 3));

    const categoryResult = {
      name: category.category,
      tests: [],
      passed: 0,
      failed: 0,
    };

    for (const test of category.tests) {
      const result = await runTest(test);
      results.summary.totalTests++;

      if (result.success) {
        console.log(`✅ ${test.name}: PASS (${result.responseTime}ms)`);
        results.summary.passed++;
        categoryResult.passed++;
      } else {
        const emoji = test.critical ? '❌' : '⚠️';
        console.log(`${emoji} ${test.name}: FAIL - ${result.error} (${result.responseTime}ms)`);
        results.summary.failed++;
        categoryResult.failed++;
        
        if (test.critical) {
          results.summary.criticalFailures++;
        }
      }

      totalResponseTime += result.responseTime;
      responseTimeCount++;

      categoryResult.tests.push({
        name: test.name,
        success: result.success,
        error: result.error,
        responseTime: result.responseTime,
        critical: test.critical,
      });
    }

    results.categories.push(categoryResult);
  }

  results.summary.averageResponseTime = Math.round(totalResponseTime / responseTimeCount);

  // Print summary
  console.log('\n📊 Final Summary');
  console.log('================');
  console.log(`Tests: ${results.summary.passed}/${results.summary.totalTests} passed`);
  console.log(`Critical failures: ${results.summary.criticalFailures}`);
  console.log(`Average response time: ${results.summary.averageResponseTime}ms`);

  // Health assessment
  if (results.summary.criticalFailures === 0) {
    console.log('🎉 App is healthy and ready for use!');
  } else {
    console.log('🚨 Critical issues detected - app may not function properly');
    
    console.log('\n🔧 Recommended Actions:');
    console.log('1. Check backend server status');
    console.log('2. Verify API configuration');
    console.log('3. Test network connectivity');
    console.log('4. Review server logs for errors');
  }

  // Save detailed results
  const resultsPath = path.join(__dirname, '../test-results.json');
  fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
  console.log(`\n📄 Detailed results saved to: ${resultsPath}`);

  return results.summary.criticalFailures === 0;
}

// Environment validation
function validateEnvironment() {
  console.log('🔍 Environment Check');
  console.log('====================');

  const checks = [
    {
      name: 'API URL Configuration',
      check: () => API_BASE_URL && API_BASE_URL !== 'undefined',
      fix: 'Set EXPO_PUBLIC_API_BASE_URL environment variable'
    },
    {
      name: 'Network Reachability',
      check: async () => {
        try {
          const response = await fetch(API_BASE_URL.replace('/api/v1', ''), { method: 'HEAD' });
          return response.status < 500;
        } catch {
          return false;
        }
      },
      fix: 'Check if backend server is running and accessible'
    }
  ];

  return Promise.all(checks.map(async check => {
    const result = await Promise.resolve(check.check());
    console.log(`${result ? '✅' : '❌'} ${check.name}: ${result ? 'OK' : 'FAILED'}`);
    if (!result) {
      console.log(`   Fix: ${check.fix}`);
    }
    return result;
  }));
}

// Main execution
async function main() {
  try {
    // Validate environment first
    const envChecks = await validateEnvironment();
    const envHealthy = envChecks.every(Boolean);

    if (!envHealthy) {
      console.log('\n❌ Environment validation failed. Please fix issues above before running tests.');
      process.exit(1);
    }

    // Run comprehensive tests
    console.log('\n🧪 Running Comprehensive Tests...');
    const success = await runAllTests();

    process.exit(success ? 0 : 1);

  } catch (error) {
    console.error('\n💥 Test runner crashed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { runAllTests, runTest };