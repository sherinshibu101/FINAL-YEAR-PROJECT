/**
 * Test: Lab Report Encryption & Temp File Cleanup
 * Tests:
 * 1. Lab report encryption (POST /api/lab/results/:testId/encrypt) - should now work!
 * 2. Temp file creation on decryption
 * 3. Temp file cleanup on logout
 */

const http = require('http');
const fs = require('fs');

const BASE_URL = 'http://localhost:3000';
const TEST_USER = {
  email: 'labtech@hospital.com',
  password: 'SecurePass123!'
};

let authToken = null;
let sessionId = null;

// Helper to make HTTP requests
function makeRequest(method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      method,
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = data ? JSON.parse(data) : {};
          resolve({ status: res.statusCode, data: parsed, headers: res.headers });
        } catch {
          resolve({ status: res.statusCode, data: data, headers: res.headers });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function runTests() {
  try {
    console.log('\n╔════════════════════════════════════════════════════════════╗');
    console.log('║  Lab Report Encryption & Temp File Cleanup Test Suite     ║');
    console.log('╚════════════════════════════════════════════════════════════╝\n');

    // Step 1: Login
    console.log('📝 [TEST 1] Login as Lab Technician');
    console.log('   Endpoint: POST /api/auth/login');
    
    const loginRes = await makeRequest('POST', '/api/auth/login', {
      email: TEST_USER.email,
      password: TEST_USER.password,
      mfaCode: '000000'
    });

    if (loginRes.status !== 200) {
      console.log(`❌ Login failed: ${loginRes.status}`);
      console.log(JSON.stringify(loginRes.data, null, 2));
      process.exit(1);
    }

    authToken = loginRes.data.token;
    sessionId = loginRes.data.sessionId || 'session-' + Date.now();
    console.log(`✅ Login successful\n   Token: ${authToken.substring(0, 20)}...`);
    console.log(`   Session ID: ${sessionId}\n`);

    // Step 2: Get lab test ID
    console.log('🔍 [TEST 2] Fetch Lab Tests');
    console.log('   Endpoint: GET /api/lab-tests');

    const labTestsRes = await makeRequest('GET', '/api/lab-tests', null, {
      'Authorization': `Bearer ${authToken}`
    });

    if (labTestsRes.status !== 200 && labTestsRes.status !== 304) {
      console.log(`❌ Failed to get lab tests: ${labTestsRes.status}`);
      process.exit(1);
    }

    let testId = null;
    if (Array.isArray(labTestsRes.data)) {
      testId = labTestsRes.data[0]?.id;
    } else if (labTestsRes.data?.tests && Array.isArray(labTestsRes.data.tests)) {
      testId = labTestsRes.data.tests[0]?.id;
    }

    if (!testId) {
      console.log('❌ No lab tests found');
      process.exit(1);
    }

    console.log(`✅ Found lab test: ${testId}\n`);

    // Step 3: Encrypt lab report
    console.log('🔐 [TEST 3] Encrypt Lab Report');
    console.log(`   Endpoint: POST /api/lab/results/${testId}/encrypt`);

    // Create a simple test PDF content
    const testPdfContent = Buffer.from('PDF test content for encryption');

    const encryptRes = await makeRequest('POST', `/api/lab/results/${testId}/encrypt`, {
      filename: 'test-lab-report.pdf',
      fileContent: testPdfContent.toString('base64')
    }, {
      'Authorization': `Bearer ${authToken}`
    });

    console.log(`   Status: ${encryptRes.status}`);
    
    if (encryptRes.status === 500) {
      console.log(`❌ Encryption failed (500 error)`);
      console.log(`   Response: ${JSON.stringify(encryptRes.data, null, 2)}`);
      console.log('\n   This indicates the database columns are still missing or there\'s a schema issue.');
      process.exit(1);
    } else if (encryptRes.status === 200) {
      console.log(`✅ Encryption successful`);
      console.log(`   Response: ${JSON.stringify(encryptRes.data, null, 2)}\n`);
    } else {
      console.log(`⚠️  Unexpected status: ${encryptRes.status}`);
      console.log(`   Response: ${JSON.stringify(encryptRes.data, null, 2)}`);
    }

    // Step 4: Decrypt report (creates temp files)
    console.log('📂 [TEST 4] Decrypt Lab Report (creates temp files)');
    console.log(`   Endpoint: GET /api/lab/results/${testId}/download`);

    const decryptRes = await makeRequest('GET', `/api/lab/results/${testId}/download`, null, {
      'Authorization': `Bearer ${authToken}`
    });

    if (decryptRes.status === 200) {
      console.log(`✅ Decryption successful`);
      console.log(`   Content received: ${decryptRes.data.length || 0} bytes\n`);
      
      // Check if temp folder exists
      const tempDir = '.temp-decrypted';
      if (fs.existsSync(tempDir)) {
        const files = fs.readdirSync(tempDir);
        console.log(`📁 Temp folder contents: ${files.length} session folder(s)`);
        files.forEach(f => {
          const fullPath = `${tempDir}/${f}`;
          if (fs.statSync(fullPath).isDirectory()) {
            const sessionFiles = fs.readdirSync(fullPath);
            console.log(`   📂 ${f}/`);
            console.log(`      └─ ${sessionFiles.length} file(s): ${sessionFiles.join(', ')}`);
          }
        });
      } else {
        console.log('   ⚠️  Temp folder not created yet\n');
      }
    } else {
      console.log(`⚠️  Decryption status: ${decryptRes.status}`);
      if (decryptRes.status === 403) {
        console.log('   Permission denied - doctor access may be needed instead\n');
      }
    }

    // Step 5: Logout (should clean up temp files)
    console.log('🚪 [TEST 5] Logout (should trigger temp file cleanup)');
    console.log('   Endpoint: POST /api/logout');

    const logoutRes = await makeRequest('POST', '/api/logout', 
      { sessionId },
      { 'Authorization': `Bearer ${authToken}` }
    );

    if (logoutRes.status === 200) {
      console.log(`✅ Logout successful\n`);
      console.log(`   Temp files removed: ${logoutRes.data.tempFilesRemoved || false}`);
    } else {
      console.log(`⚠️  Logout status: ${logoutRes.status}`);
    }

    // Check temp folder again
    console.log('\n📁 [TEST 6] Verify Temp File Cleanup');
    const tempDir = '.temp-decrypted';
    if (fs.existsSync(tempDir)) {
      const files = fs.readdirSync(tempDir);
      if (files.length === 0) {
        console.log('✅ Temp folder is empty (cleanup successful)');
      } else {
        console.log(`⚠️  Temp files still exist: ${files.length} session(s)`);
        files.forEach(f => {
          const fullPath = `${tempDir}/${f}`;
          if (fs.statSync(fullPath).isDirectory()) {
            const sessionFiles = fs.readdirSync(fullPath);
            console.log(`   ⚠️  ${f}: ${sessionFiles.length} file(s) not deleted`);
          }
        });
      }
    } else {
      console.log('✅ Temp folder removed completely');
    }

    console.log('\n╔════════════════════════════════════════════════════════════╗');
    console.log('║                   Test Suite Complete                     ║');
    console.log('╚════════════════════════════════════════════════════════════╝\n');

    process.exit(0);

  } catch (err) {
    console.error('❌ Test failed with error:', err.message);
    process.exit(1);
  }
}

runTests();
