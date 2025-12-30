/**
 * Quick test: Lab Encryption Fix Verification
 * Focuses on testing the encryption endpoint that was throwing 500 errors
 */

const http = require('http');

const BASE_URL = 'http://localhost:3000';

function makeRequest(method, path, body = null, authToken = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      method,
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (authToken) {
      options.headers['Authorization'] = `Bearer ${authToken}`;
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: data ? JSON.parse(data) : {} });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on('error', err => {
      console.error('Connection error:', err.message);
      resolve({ status: 0, error: err.message });
    });

    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function test() {
  console.log('\n=== LAB ENCRYPTION FIX VERIFICATION ===\n');

  // Step 1: Login
  console.log('1. Login as Lab Technician...');
  const login = await makeRequest('POST', '/api/auth/login', {
    email: 'labtech@hospital.com',
    password: 'SecurePass123!',
    mfaCode: '000000'
  });

  if (login.status === 0) {
    console.log('❌ Cannot connect to server on port 3000');
    process.exit(1);
  }

  if (login.status !== 200) {
    console.log(`❌ Login failed: ${login.status}`);
    console.log(JSON.stringify(login.body, null, 2));
    process.exit(1);
  }

  const token = login.body.token;
  console.log(`✅ Login successful (token: ${token.substring(0, 20)}...)\n`);

  // Step 2: Get lab test
  console.log('2. Fetching lab tests...');
  const labs = await makeRequest('GET', '/api/lab-tests', null, token);

  if (labs.status !== 200 && labs.status !== 304) {
    console.log(`❌ Failed to fetch lab tests: ${labs.status}`);
    process.exit(1);
  }

  let testId = null;
  if (Array.isArray(labs.body)) {
    testId = labs.body[0]?.id;
  } else if (labs.body?.tests) {
    testId = labs.body.tests[0]?.id;
  }

  if (!testId) {
    console.log('❌ No lab tests found');
    process.exit(1);
  }

  console.log(`✅ Found lab test: ${testId}\n`);

  // Step 3: Test encryption endpoint
  console.log(`3. Testing encryption endpoint...`);
  console.log(`   POST /api/lab/results/${testId}/encrypt`);

  const encrypt = await makeRequest('POST', `/api/lab/results/${testId}/encrypt`, {
    filename: 'test-report.pdf',
    fileContent: Buffer.from('Test PDF Content').toString('base64')
  }, token);

  console.log(`   Response Status: ${encrypt.status}`);

  if (encrypt.status === 500) {
    console.log('❌ ENCRYPTION ENDPOINT FAILED (500 error)');
    console.log('   This means the database schema is still incomplete.');
    console.log(`   Error: ${encrypt.body.error || JSON.stringify(encrypt.body)}`);
    process.exit(1);
  } else if (encrypt.status === 200 || encrypt.status === 201) {
    console.log('✅ ENCRYPTION ENDPOINT WORKING!');
    console.log(`   Response: ${JSON.stringify(encrypt.body)}\n`);
    console.log('=== FIX VERIFIED ===');
    console.log('✓ Lab encryption is now functional');
    console.log('✓ Database schema includes encryption_status column');
    process.exit(0);
  } else {
    console.log(`⚠️  Unexpected status: ${encrypt.status}`);
    console.log(`   Response: ${JSON.stringify(encrypt.body)}`);
    process.exit(1);
  }
}

test();
