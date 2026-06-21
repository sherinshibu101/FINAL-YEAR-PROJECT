/**
 * Generate unique MFA secrets for all users
 */

const speakeasy = require('speakeasy');

const users = [
  'admin@hospital.com',
  'doctor@hospital.com',
  'nurse@hospital.com',
  'receptionist@hospital.com',
  'labtech@hospital.com',
  'pharmacist@hospital.com',
  'accountant@hospital.com'
];

console.log('Generating unique MFA secrets for each user...\n');

const secrets = {};

users.forEach(email => {
  const secret = speakeasy.generateSecret({
    name: email,
    issuer: 'Hospital Management System'
  });
  secrets[email] = secret.base32;
  console.log(`'${email}': '${secret.base32}',`);
});

console.log('\n\nCopy the above for use in seed file and mfa-code-generator.js');
