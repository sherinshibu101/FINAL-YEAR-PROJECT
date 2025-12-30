/**
 * Test MFA login with valid TOTP codes
 * Run with: node test-mfa-complete.js
 */

const speakeasy = require('speakeasy');

const users = [
  { email: 'admin@hospital.com', password: 'Admin@123', role: 'admin', mfaSecret: 'PVSU22Z3OBIWIZKXF52GWNDHLJJUMMSJKJJFI7L2IVAS44CJF42Q' },
  { email: 'doctor@hospital.com', password: 'Doctor@123', role: 'doctor', mfaSecret: 'MU7EI4S3KI2SQKDWMEYCS4KEKBXHUNBMNUUUY5KLIQ3FQTJQKZ4Q' },
  { email: 'nurse@hospital.com', password: 'Nurse@123', role: 'nurse', mfaSecret: 'IJ5HAYSCGB5S42CHGAXHS532MEZCY5L2OZESS4CRFRICGN2OHM4Q' },
  { email: 'receptionist@hospital.com', password: 'Receptionist@123', role: 'receptionist', mfaSecret: 'ENXE2JCKKZXHOMJRMV2EEOTHINCDIYLOPJ6SYRDDIJUFOYD5PMZA' },
  { email: 'labtech@hospital.com', password: 'LabTech@123', role: 'lab_technician', mfaSecret: 'MJSSSLCEHQ7XQ4JROY3TSJCUJJ5VCXKHNBWTCXS3MIUHAJZJZOQ' },
  { email: 'pharmacist@hospital.com', password: 'Pharmacist@123', role: 'pharmacist', mfaSecret: 'MJMHSWBDJ5JWG4JKOY7UQTTLJ5SCUZSIK4ZEWQLDG5AGEJCYI5SQ' },
  { email: 'accountant@hospital.com', password: 'Accountant@123', role: 'accountant', mfaSecret: 'IBSG27J4NN3HSZTQGY4SS2DMNRPEGJRZIJFW4423J5WDMUBFEVKA' }
];

async function testMfaLogin(email, password, role, mfaSecret) {
  try {
    console.log(`\n📧 ${email} (${role})`);
    
    // Step 1: Login with password
    console.log('  Step 1: Sending credentials...');
    let loginResponse;
    try {
      loginResponse = await fetch('http://localhost:3000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
    } catch (fetchErr) {
      console.log(`  ❌ Fetch error: ${fetchErr.message}`);
      console.log(`  ❌ Error code: ${fetchErr.code}`);
      return false;
    }

    const loginData = await loginResponse.json();

    if (!loginData.success) {
      console.log(`  ❌ Login failed: ${loginData.error}`);
      return false;
    }

    if (!loginData.mfaRequired) {
      console.log(`  ⚠️  MFA not required (mfa_enabled: false in DB)`);
      console.log(`  ✅ Direct login successful`);
      return true;
    }

    // Step 2: Generate TOTP code
    console.log('  Step 2: Generating TOTP code...');
    const mfaCode = speakeasy.totp({
      secret: mfaSecret,
      encoding: 'base32',
      window: 2
    });
    console.log(`     Generated code: ${mfaCode}`);

    // Step 3: Verify MFA
    console.log('  Step 3: Verifying MFA code...');
    const mfaResponse = await fetch('http://localhost:3000/api/mfa/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code: mfaCode })
    });

    const mfaData = await mfaResponse.json();

    if (mfaData.success) {
      console.log(`  ✅ MFA verified successfully!`);
      console.log(`     Token: ${mfaData.token ? mfaData.token.substring(0, 25) + '...' : 'N/A'}`);
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
  console.log('═══════════════════════════════════════════════════');
  console.log('Testing MFA Login Flow for All Roles');
  console.log('═══════════════════════════════════════════════════');

  let passed = 0;
  for (const user of users) {
    const success = await testMfaLogin(user.email, user.password, user.role, user.mfaSecret);
    if (success) passed++;
  }

  // Test patient (no MFA)
  console.log(`\n📧 patient@hospital.com (patient)`);
  try {
    const response = await fetch('http://localhost:3000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'patient@hospital.com', password: 'Patient@123' })
    });
    const data = await response.json();
    if (data.success && data.token) {
      console.log(`  ✅ Login successful (no MFA)`);
      passed++;
    }
  } catch (error) {
    console.log(`  ❌ Error: ${error.message}`);
  }

  console.log(`\n═══════════════════════════════════════════════════`);
  console.log(`✅ Successful: ${passed}/8 users\n`);
}

runTests();
