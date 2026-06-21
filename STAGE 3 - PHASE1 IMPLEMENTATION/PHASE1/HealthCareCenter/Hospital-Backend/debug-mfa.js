/**
 * Debug MFA verification
 */

const speakeasy = require('speakeasy');

const mfaSecrets = {
  'admin@hospital.com': 'PVSU22Z3OBIWIZKXF52GWNDHLJJUMMSJKJJFI7L2IVAS44CJF42Q',
  'doctor@hospital.com': 'MU7EI4S3KI2SQKDWMEYCS4KEKBXHUNBMNUUUY5KLIQ3FQTJQKZ4Q',
  'nurse@hospital.com': 'IJ5HAYSCGB5S42CHGAXHS532MEZCY5L2OZESS4CRFRICGN2OHM4Q',
  'receptionist@hospital.com': 'ENXE2JCKKZXHOMJRMV2EEOTHINCDIYLOPJ6SYRDDIJUFOJD5PMZA',
  'labtech@hospital.com': 'MJSSSLCEHQ7XQ4JROY3TSJCUJJ5VCXKHNBWTCXS3MIUHA3JZJZOQ',
  'pharmacist@hospital.com': 'MJMHSWBDJ5JWG4JKOY7UQTTLJ5SCUZSIK4ZEWQLDG5AGEJCYI5SQ',
  'accountant@hospital.com': 'IBSG27J4NN3HSZTQGY4SS2DMNRPEGJRZIJFW4423J5WDMUBFEVKA'
};

// Test generating code using stored secret
const email = 'admin@hospital.com';
const secret = mfaSecrets[email];

console.log(`\nTesting MFA Code Generation for: ${email}`);
console.log(`Secret: ${secret}`);
console.log(`Secret length: ${secret.length}`);

const code = speakeasy.totp({
  secret: secret,
  encoding: 'base32'
});

console.log(`Generated Code: ${code}`);

// Test verifying this code immediately
const verified = speakeasy.totp.verify({
  secret: secret,
  encoding: 'base32',
  token: code,
  window: 2
});

console.log(`Code verification (window 2): ${verified ? 'SUCCESS' : 'FAILED'}`);

// Show what the backend should be doing
console.log(`\nBackend should verify like this:`);
console.log(`speakeasy.totp.verify({
  secret: '${secret}',
  encoding: 'base32',
  token: '${code}',
  window: 2
});`);
