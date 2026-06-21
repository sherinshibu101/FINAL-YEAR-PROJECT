#!/usr/bin/env node

/**
 * Integration Test: File Encryption with IAM + MFA
 * 
 * Tests the complete flow:
 * Frontend (React) -> Backend API (3000) -> IAM Service (4000) -> Encryption Module
 * 
 * Prerequisites:
 * 1. Backend API running on port 3000
 * 2. IAM Service running on port 4000
 * 3. Encryption module initialized
 * 4. PostgreSQL database running
 */

const http = require('http');
const fs = require('fs').promises;
const path = require('path');

const API_HOST = 'localhost';
const API_PORT = 3000;
const IAM_PORT = 4000;

let jwtToken = null;
let userId = null;

// ===== UTILITIES =====

async function makeRequest(method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: API_HOST,
      port: API_PORT,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      },
      timeout: 10000
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            body: data ? JSON.parse(data) : null,
            headers: res.headers
          });
        } catch (err) {
          resolve({
            status: res.statusCode,
            body: data,
            headers: res.headers
          });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

// ===== TEST SCENARIOS =====

async function test1_Login() {
  console.log('\n📝 TEST 1: User Login');
  console.log('─'.repeat(60));

  const response = await makeRequest('POST', '/api/login', {
    email: 'admin@hospital.com',
    password: 'Admin@123'
  });

  if (response.status !== 200) {
    throw new Error(`Login failed: ${response.status} - ${JSON.stringify(response.body)}`);
  }

  jwtToken = response.body.token;
  userId = response.body.userId;

  console.log(`✓ Login successful`);
  console.log(`  User ID: ${userId}`);
  console.log(`  Token: ${jwtToken.slice(0, 20)}...`);

  return true;
}

async function test2_CheckEncryptionServiceAvailable() {
  console.log('\n📝 TEST 2: Check Encryption Service Available');
  console.log('─'.repeat(60));

  const response = await makeRequest('GET', '/api/files/status/sample.txt', null, {
    'Authorization': `Bearer ${jwtToken}`
  });

  if (response.status === 503) {
    console.warn('⚠ Encryption service not available - this is normal if Encryption module not initialized');
    console.warn('  To enable, ensure /Encryption folder is set up and storageManager is initialized');
    return false;
  }

  if (response.status !== 200) {
    throw new Error(`Status check failed: ${response.status}`);
  }

  console.log(`✓ Encryption service is available`);
  console.log(`  Response:`, response.body);

  return true;
}

async function test3_CheckIAMIntegration() {
  console.log('\n📝 TEST 3: Verify IAM Integration');
  console.log('─'.repeat(60));

  // Call IAM service directly to verify it's working
  const iamTest = await new Promise((resolve, reject) => {
    const options = {
      hostname: API_HOST,
      port: IAM_PORT,
      path: '/api/me',
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${jwtToken}`,
        'Content-Type': 'application/json'
      },
      timeout: 5000
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            body: JSON.parse(data)
          });
        } catch (err) {
          resolve({
            status: res.statusCode,
            body: data
          });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('IAM timeout'));
    });

    req.end();
  });

  if (iamTest.status !== 200) {
    throw new Error(`IAM check failed: ${iamTest.status}`);
  }

  console.log(`✓ IAM Service Integration working`);
  console.log(`  User: ${iamTest.body.name} (${iamTest.body.role})`);
  console.log(`  MFA Enabled: ${iamTest.body.mfaEnabled}`);
  console.log(`  Permissions: ${iamTest.body.permissions?.join(', ')}`);

  return true;
}

async function test4_DecryptWithIAM() {
  console.log('\n📝 TEST 4: Decrypt File with IAM Verification');
  console.log('─'.repeat(60));

  const response = await makeRequest('POST', '/api/files/decrypt', {
    fileId: 'sample.txt',
    mfaToken: null
  }, {
    'Authorization': `Bearer ${jwtToken}`
  });

  if (response.status === 503) {
    console.warn('⚠ Encryption service not initialized - skipping test');
    return false;
  }

  if (response.status === 404 || (response.body && response.body.error && response.body.error.includes('not found'))) {
    console.warn('⚠ Sample file not found in encryption storage');
    console.log('  To test decryption, first upload and encrypt a file');
    return false;
  }

  if (response.status !== 200) {
    console.error(`✗ Decryption failed: ${response.status}`);
    console.error(`  Error: ${response.body?.error}`);
    return false;
  }

  console.log(`✓ File decrypted successfully with IAM verification`);
  console.log(`  File ID: ${response.body.fileId}`);
  console.log(`  User: ${response.body.user.name} (${response.body.user.role})`);
  console.log(`  Decrypted at: ${response.body.decryptedAt}`);
  console.log(`  Auto-delete in: ${response.body.autoDeleteIn}`);

  return true;
}

async function test5_DecryptWithoutAuth() {
  console.log('\n📝 TEST 5: Verify Authentication Required');
  console.log('─'.repeat(60));

  const response = await makeRequest('POST', '/api/files/decrypt', {
    fileId: 'sample.txt'
  });

  if (response.status === 401 || response.status === 403) {
    console.log(`✓ Authentication properly enforced`);
    console.log(`  Status: ${response.status}`);
    console.log(`  Error: ${response.body?.error}`);
    return true;
  }

  throw new Error(`Expected 401/403 but got ${response.status}`);
}

// ===== MAIN TEST SUITE =====

async function runAllTests() {
  console.log('\n');
  console.log('╔' + '═'.repeat(58) + '╗');
  console.log('║' + ' '.repeat(10) + 'ENCRYPTION INTEGRATION TEST SUITE' + ' '.repeat(15) + '║');
  console.log('║' + ' '.repeat(15) + 'IAM + MFA + File Encryption' + ' '.repeat(17) + '║');
  console.log('╚' + '═'.repeat(58) + '╝');

  const results = [];

  try {
    // Test 1: Login
    try {
      await test1_Login();
      results.push({ name: 'Login', status: '✓ PASS' });
    } catch (err) {
      results.push({ name: 'Login', status: `✗ FAIL: ${err.message}` });
      throw err;
    }

    // Test 2: Check encryption service
    try {
      const available = await test2_CheckEncryptionServiceAvailable();
      results.push({ 
        name: 'Encryption Service Available', 
        status: available ? '✓ PASS' : '⚠ SKIP (Not initialized)' 
      });
    } catch (err) {
      results.push({ name: 'Encryption Service Available', status: `✗ FAIL: ${err.message}` });
    }

    // Test 3: IAM Integration
    try {
      await test3_CheckIAMIntegration();
      results.push({ name: 'IAM Integration', status: '✓ PASS' });
    } catch (err) {
      results.push({ name: 'IAM Integration', status: `✗ FAIL: ${err.message}` });
      throw err;
    }

    // Test 4: Decrypt with IAM
    try {
      const decrypted = await test4_DecryptWithIAM();
      results.push({ 
        name: 'Decrypt with IAM', 
        status: decrypted ? '✓ PASS' : '⚠ SKIP (No files)' 
      });
    } catch (err) {
      results.push({ name: 'Decrypt with IAM', status: `✗ FAIL: ${err.message}` });
    }

    // Test 5: Auth required
    try {
      await test5_DecryptWithoutAuth();
      results.push({ name: 'Authentication Required', status: '✓ PASS' });
    } catch (err) {
      results.push({ name: 'Authentication Required', status: `✗ FAIL: ${err.message}` });
    }

  } catch (err) {
    console.error('\n❌ Test suite failed:', err.message);
  }

  // Print summary
  console.log('\n');
  console.log('╔' + '═'.repeat(58) + '╗');
  console.log('║' + ' '.repeat(25) + 'TEST SUMMARY' + ' '.repeat(21) + '║');
  console.log('╠' + '═'.repeat(58) + '╣');

  for (const result of results) {
    const status = result.status;
    const padding = ' '.repeat(50 - result.name.length - status.length);
    console.log(`║ ${result.name}${padding}${status} ║`);
  }

  const passCount = results.filter(r => r.status.includes('PASS')).length;
  const totalCount = results.length;

  console.log('╠' + '═'.repeat(58) + '╣');
  console.log(`║ TOTAL: ${passCount}/${totalCount} tests passed` + ' '.repeat(50 - `TOTAL: ${passCount}/${totalCount} tests passed`.length) + '║');
  console.log('╚' + '═'.repeat(58) + '╝\n');

  return passCount === totalCount;
}

// Run tests
runAllTests().then(success => {
  process.exit(success ? 0 : 1);
}).catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
