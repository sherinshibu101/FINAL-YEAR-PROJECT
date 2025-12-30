/**
 * Generate bcrypt hashes for all user passwords
 * Run with: node generate-password-hashes.js
 */

const bcrypt = require('bcryptjs');

const users = [
  { email: 'admin@hospital.com', password: 'Admin@123' },
  { email: 'doctor@hospital.com', password: 'Doctor@123' },
  { email: 'nurse@hospital.com', password: 'Nurse@123' },
  { email: 'receptionist@hospital.com', password: 'Receptionist@123' },
  { email: 'labtech@hospital.com', password: 'LabTech@123' },
  { email: 'pharmacist@hospital.com', password: 'Pharmacist@123' },
  { email: 'accountant@hospital.com', password: 'Accountant@123' },
  { email: 'patient@hospital.com', password: 'Patient@123' }
];

async function generateHashes() {
  console.log('Generating bcrypt hashes for all passwords:\n');
  
  const hashes = {};
  for (const user of users) {
    const hash = await bcrypt.hash(user.password, 10);
    hashes[user.email] = hash;
    console.log(`'${user.email}': '${hash}', // ${user.password}`);
  }

  console.log('\n\nUpdate the seed file 03_users_with_passwords.js with these hashes.');
}

generateHashes();
