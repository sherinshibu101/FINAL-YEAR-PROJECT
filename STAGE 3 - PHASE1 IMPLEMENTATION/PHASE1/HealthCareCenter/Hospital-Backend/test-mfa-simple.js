/**
 * Simple MFA test using http module
 */

const http = require('http');
const speakeasy = require('speakeasy');

function makeRequest(path, data) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          resolve({ error: 'Invalid JSON response', body });
        }
      });
    });

    req.on('error', (e) => reject(e));
    req.write(data);
    req.end();
  });
}

async function testMfa() {
  console.log('Testing MFA Login Flow\n');

  const testUser = {
    email: 'admin@hospital.com',
    password: 'Admin@123',
    mfaSecret: 'PVSU22Z3OBIWIZKXF52GWNDHLJJUMMSJKJJFI7L2IVAS44CJF42Q'
  };

  try {
    // Step 1: Login
    console.log('📧 Step 1: Logging in with credentials...');
    const loginData = JSON.stringify({
      email: testUser.email,
      password: testUser.password
    });

    const loginRes = await makeRequest('/api/login', loginData);
    console.log('Response:', loginRes);

    if (!loginRes.success) {
      console.log('❌ Login failed:', loginRes.error);
      return;
    }

    if (!loginRes.mfaRequired) {
      console.log('⚠️  MFA not required');
      return;
    }

    console.log('✅ Login successful, MFA required\n');

    // Step 2: Generate TOTP
    console.log('🔐 Step 2: Generating TOTP code...');
    const mfaCode = speakeasy.totp({
      secret: testUser.mfaSecret,
      encoding: 'base32',
      window: 2
    });
    console.log('Generated code:', mfaCode + '\n');

    // Step 3: Verify MFA
    console.log('✔️  Step 3: Verifying MFA code...');
    const mfaData = JSON.stringify({
      email: testUser.email,
      code: mfaCode
    });

    const mfaRes = await makeRequest('/api/mfa/verify', mfaData);
    console.log('Response:', mfaRes);

    if (mfaRes.success) {
      console.log('\n✅ MFA verification successful!');
      console.log('User:', mfaRes.user.email, '-', mfaRes.user.role);
    } else {
      console.log('\n❌ MFA verification failed:', mfaRes.error);
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testMfa();
