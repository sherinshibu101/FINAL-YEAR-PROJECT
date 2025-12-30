/**
 * MFA Test using http module (no fetch)
 */

const http = require('http');
const speakeasy = require('speakeasy');

const testUser = {
  email: 'admin@hospital.com',
  password: 'Admin@123',
  mfaSecret: 'PVSU22Z3OBIWIZKXF52GWNDHLJJUMMSJKJJFI7L2IVAS44CJF42Q'
};

function makeRequest(method, path, data) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 3000,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(body) });
        } catch (e) {
          resolve({ status: res.statusCode, body });
        }
      });
    });

    req.on('error', (err) => {
      console.error('Request error:', err.message, err.code);
      reject(err);
    });
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

async function test() {
  try {
    console.log('🧪 Testing MFA Flow\n');
    
    // Step 1: Login
    console.log('Step 1: Logging in...');
    const loginRes = await makeRequest('POST', '/api/login', { 
      email: testUser.email, 
      password: testUser.password 
    });
    
    console.log('Status:', loginRes.status);
    console.log('Response:', JSON.stringify(loginRes.body, null, 2));
    
    if (!loginRes.body.success) {
      console.log('❌ Login failed');
      return;
    }
    
    if (!loginRes.body.mfaRequired) {
      console.log('⚠️  MFA not required');
      return;
    }
    
    console.log('\n✅ MFA required - proceeding to verify\n');
    
    // Step 2: Generate MFA code
    console.log('Step 2: Generating MFA code...');
    const mfaCode = speakeasy.totp({
      secret: testUser.mfaSecret,
      encoding: 'base32',
      window: 2
    });
    
    console.log(`Generated code: ${mfaCode}\n`);
    
    // Step 3: Verify MFA
    console.log('Step 3: Verifying MFA code...');
    const mfaRes = await makeRequest('POST', '/api/mfa/verify', {
      email: testUser.email,
      code: mfaCode
    });
    
    console.log('Status:', mfaRes.status);
    console.log('Response:', JSON.stringify(mfaRes.body, null, 2));
    
    if (mfaRes.body.success) {
      console.log('\n✅ MFA VERIFICATION SUCCESSFUL!');
      console.log(`Token: ${mfaRes.body.token ? mfaRes.body.token.substring(0, 50) + '...' : 'N/A'}`);
    } else {
      console.log('\n❌ MFA verification failed:', mfaRes.body.error);
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

test();
