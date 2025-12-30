/**
 * Test if the database secret is valid base32
 */

const speakeasy = require('speakeasy');

// This is the exact secret for doctor from DB
const doctorSecret = 'MU7EI4S3KI2SQKDWMEYCS4KEKBXHUNBMNUUUY5KLIQ3FQTJQKZ4Q';

console.log('Testing doctor secret:', doctorSecret);
console.log('Length:', doctorSecret.length);

try {
  // Try to generate a code from this secret
  const code = speakeasy.totp({
    secret: doctorSecret,
    encoding: 'base32'
  });
  
  console.log('Generated code:', code);
  
  // Try to verify it
  const verified = speakeasy.totp.verify({
    secret: doctorSecret,
    encoding: 'base32',
    token: code,
    window: 2
  });
  
  console.log('Verified:', verified);
  
  if (verified) {
    console.log('✅ Secret is valid!');
  } else {
    console.log('❌ Verification failed even with generated code');
  }
} catch (error) {
  console.error('❌ Error:', error.message);
}
