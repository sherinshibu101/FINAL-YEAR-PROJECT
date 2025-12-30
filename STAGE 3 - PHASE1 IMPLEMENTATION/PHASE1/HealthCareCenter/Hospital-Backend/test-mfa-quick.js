/**
 * Quick MFA test with actual backend
 */

const speakeasy = require('speakeasy');

const testUser = {
  email: 'admin@hospital.com',
  password: 'Admin@123',
  mfaSecret: 'PVSU22Z3OBIWIZKXF52GWNDHLJJUMMSJKJJFI7L2IVAS44CJF42Q'
};

async function test() {
  try {
    console.log('🧪 Testing MFA Flow\n');
    
    // Step 1: Login
    console.log('Step 1: Logging in...');
    const loginRes = await fetch('http://localhost:3000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        email: testUser.email, 
        password: testUser.password 
      })
    });
    
    const loginData = await loginRes.json();
    console.log('Login response:', JSON.stringify(loginData, null, 2));
    
    if (!loginData.success) {
      console.log('❌ Login failed');
      return;
    }
    
    if (!loginData.mfaRequired) {
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
    const mfaRes = await fetch('http://localhost:3000/api/mfa/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: testUser.email,
        code: mfaCode
      })
    });
    
    const mfaData = await mfaRes.json();
    console.log('MFA verify response:', JSON.stringify(mfaData, null, 2));
    
    if (mfaData.success) {
      console.log('\n✅ MFA VERIFICATION SUCCESSFUL!');
      console.log(`Token: ${mfaData.token ? mfaData.token.substring(0, 50) + '...' : 'N/A'}`);
    } else {
      console.log('\n❌ MFA verification failed:', mfaData.error);
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

test();
