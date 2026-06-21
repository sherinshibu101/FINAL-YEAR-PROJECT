/**
 * Test script to verify all 8 users can login
 * Run with: node test-all-logins.js
 */

const credentials = [
  { email: 'admin@hospital.com', password: 'Admin@123', role: 'admin' },
  { email: 'doctor@hospital.com', password: 'Doctor@123', role: 'doctor' },
  { email: 'nurse@hospital.com', password: 'Nurse@123', role: 'nurse' },
  { email: 'receptionist@hospital.com', password: 'Receptionist@123', role: 'receptionist' },
  { email: 'labtech@hospital.com', password: 'LabTech@123', role: 'lab_technician' },
  { email: 'pharmacist@hospital.com', password: 'Pharmacist@123', role: 'pharmacist' },
  { email: 'accountant@hospital.com', password: 'Accountant@123', role: 'accountant' },
  { email: 'patient@hospital.com', password: 'Patient@123', role: 'patient' }
];

async function testLogin(email, password, expectedRole) {
  try {
    const response = await fetch('http://localhost:3000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (response.ok && data.success) {
      console.log(`✅ ${email} (${expectedRole}) - Login successful`);
      if (data.token) {
        console.log(`   Token: ${data.token.substring(0, 30)}...`);
      }
      return true;
    } else {
      console.log(`❌ ${email} (${expectedRole}) - ${data.error || 'Unknown error'}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ ${email} (${expectedRole}) - ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('Testing all 8 user roles...\n');
  
  let passed = 0;
  for (const cred of credentials) {
    const success = await testLogin(cred.email, cred.password, cred.role);
    if (success) passed++;
  }

  console.log(`\n${passed}/${credentials.length} logins successful`);
}

runTests();
