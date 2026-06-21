/**
 * Test MFA flow to get tokens for all users
 * Run with: node test-mfa-login.js
 */

const speakeasy = require('speakeasy');

const users = [
  { email: 'admin@hospital.com', password: 'Admin@123', mfaSecret: 'JBSWY3DPEBLW64TMMQ======' },
  { email: 'doctor@hospital.com', password: 'Doctor@123', mfaSecret: 'JBSWY3DPEBLW64TMMQ======' },
  { email: 'nurse@hospital.com', password: 'Nurse@123', mfaSecret: 'MFXHS4DSNFXWG2LS' },
  { email: 'receptionist@hospital.com', password: 'Receptionist@123', mfaSecret: 'ONSWG4TFOQ======' },
  { email: 'labtech@hospital.com', password: 'LabTech@123', mfaSecret: 'PZXXK3DSMFZXI2LO' },
  { email: 'pharmacist@hospital.com', password: 'Pharmacist@123', mfaSecret: 'QZXXK3DSMFZWI2LP' },
  { email: 'accountant@hospital.com', password: 'Accountant@123', mfaSecret: 'RZXXK3DSNFZWG2LQ' }
];

async function testMfaLogin(email, password, mfaSecret) {
  try {
    // Step 1: Login with email/password
    console.log(`\n📧 ${email}:`);
    const loginResponse = await fetch('http://localhost:3000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const loginData = await loginResponse.json();

    if (!loginData.success) {
      console.log(`  ❌ Login failed: ${loginData.error}`);
      return false;
    }

    if (!loginData.mfaRequired) {
      console.log(`  ✅ Login successful (no MFA needed) - Token received`);
      return true;
    }

    // Step 2: Generate MFA code from secret
    const mfaCode = speakeasy.totp({
      secret: mfaSecret,
      encoding: 'base32'
    });

    console.log(`  🔐 MFA required, generating code...`);

    // Step 3: Verify MFA
    const mfaResponse = await fetch('http://localhost:3000/api/mfa/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, mfaCode })
    });

    const mfaData = await mfaResponse.json();

    if (mfaData.success) {
      console.log(`  ✅ MFA verified - Token received`);
      console.log(`     Role: ${mfaData.user.role}`);
      if (mfaData.token) console.log(`     Token: ${mfaData.token.substring(0, 25)}...`);
      return true;
    } else {
      console.log(`  ❌ MFA verification failed: ${mfaData.error}`);
      return false;
    }
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('Testing MFA login flow for all users...\n');
  console.log('=' .repeat(50));

  let passed = 0;
  for (const user of users) {
    const success = await testMfaLogin(user.email, user.password, user.mfaSecret);
    if (success) passed++;
  }

  // Test patient (no MFA)
  console.log(`\n📧 patient@hospital.com:`);
  const patientResponse = await fetch('http://localhost:3000/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'patient@hospital.com', password: 'Patient@123' })
  });
  const patientData = await patientResponse.json();
  if (patientData.success && patientData.token) {
    console.log(`  ✅ Login successful (no MFA) - Token received`);
    passed++;
  }

  console.log(`\n${'='.repeat(50)}`);
  console.log(`\n✅ Successfully logged in: ${passed}/8 users`);
}

runTests();
