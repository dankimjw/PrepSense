#!/usr/bin/env node

/**
 * Connectivity Test Script for PrepSense App
 * 
 * This script tests all critical API endpoints to ensure they're reachable
 * and functioning correctly. Run this before launching the app to verify
 * backend connectivity.
 */

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8001/api/v1';

console.log('🔍 PrepSense Connectivity Test');
console.log('================================');
console.log(`Testing API: ${API_BASE_URL}`);
console.log('');

const testEndpoints = [
  {
    name: 'Health Check',
    endpoint: '/health',
    method: 'GET',
    expectedStatus: 200,
    critical: true
  },
  {
    name: 'Pantry Items',
    endpoint: '/pantry/user/111/items',
    method: 'GET',
    expectedStatus: 200,
    critical: true,
    validateResponse: (data) => Array.isArray(data) && data.length > 0
  },
  {
    name: 'Recipes from Pantry',
    endpoint: '/recipes/search/from-pantry',
    method: 'POST',
    body: {
      user_id: 111,
      max_missing_ingredients: 5,
      use_expiring_first: true
    },
    expectedStatus: 200,
    critical: true,
    validateResponse: (data) => data.recipes && Array.isArray(data.recipes)
  },
  {
    name: 'Random Recipes',
    endpoint: '/recipes/random?number=5',
    method: 'GET',
    expectedStatus: 200,
    critical: false
  }
];

async function testEndpoint(test) {
  try {
    const options = {
      method: test.method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (test.body) {
      options.body = JSON.stringify(test.body);
    }

    const response = await fetch(`${API_BASE_URL}${test.endpoint}`, options);
    
    if (response.status !== test.expectedStatus) {
      throw new Error(`Expected status ${test.expectedStatus}, got ${response.status}`);
    }

    const data = await response.json();
    
    if (test.validateResponse && !test.validateResponse(data)) {
      throw new Error('Response validation failed');
    }

    console.log(`✅ ${test.name}: PASS`);
    if (test.name === 'Pantry Items' && Array.isArray(data)) {
      console.log(`   Found ${data.length} pantry items`);
    }
    if (test.name === 'Recipes from Pantry' && data.recipes) {
      console.log(`   Found ${data.recipes.length} recipes`);
    }
    
    return { success: true, data };
  } catch (error) {
    const emoji = test.critical ? '❌' : '⚠️';
    console.log(`${emoji} ${test.name}: FAIL - ${error.message}`);
    return { success: false, error: error.message, critical: test.critical };
  }
}

async function runAllTests() {
  console.log('Running connectivity tests...\n');
  
  const results = [];
  let criticalFailures = 0;

  for (const test of testEndpoints) {
    const result = await testEndpoint(test);
    results.push({ ...test, ...result });
    
    if (!result.success && test.critical) {
      criticalFailures++;
    }
  }

  console.log('\n📊 Test Summary');
  console.log('================');
  
  const passed = results.filter(r => r.success).length;
  const total = results.length;
  
  console.log(`Tests passed: ${passed}/${total}`);
  
  if (criticalFailures > 0) {
    console.log(`❌ ${criticalFailures} critical test(s) failed!`);
    console.log('🚨 App may not function correctly');
    
    console.log('\n🔧 Troubleshooting:');
    console.log('1. Check if backend is running: curl http://localhost:8001/api/v1/health');
    console.log('2. Verify EXPO_PUBLIC_API_BASE_URL environment variable');
    console.log('3. Check network connectivity to the API server');
    console.log('4. Make sure all required services are healthy');
    
    process.exit(1);
  } else {
    console.log('🎉 All critical tests passed! App should work correctly.');
    
    const warnings = results.filter(r => !r.success && !r.critical);
    if (warnings.length > 0) {
      console.log(`⚠️  ${warnings.length} non-critical test(s) failed - some features may not work`);
    }
  }
}

// Run tests if called directly
if (require.main === module) {
  runAllTests().catch(error => {
    console.error('❌ Test runner failed:', error);
    process.exit(1);
  });
}

module.exports = { runAllTests, testEndpoint };