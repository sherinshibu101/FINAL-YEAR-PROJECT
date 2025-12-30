/**
 * Test speakeasy TOTP directly with database secrets
 */

const speakeasy = require('speakeasy');

const mfaSecrets = {
  'admin@hospital.com': 'PVSU22Z3OBIWIZKXF52GWNDHLJJUMMSJKJJFI7L2IVAS44CJF42Q',
  'doctor@hospital.com': 'MU7EI4S3KI2SQKDWMEYCS4KEKBXHUNBMNUUUY5KLIQ3FQTJQKZ4Q',
  'nurse@hospital.com': 'IJ5HAYSCGB5S42CHGAXHS532MEZCY5L2OZESS4CRFRICGN2OHM4Q',
  'receptionist@hospital.com': 'ENXE2JCKKZXHOMJRMV2EEOTHINCDIYLOPJ6SYRDDIJUFOYD5PMZA',
  'labtech@hospital.com': 'MJSSSLCEHQ7XQ4JROY3TSJCUJJ5VCXKHNBWTCXS3MIUHAJZJZOQ',
  'pharmacist@hospital.com': 'MJMHSWBDJ5JWG4JKOY7UQTTLJ5SCUZSIK4ZEWQLDG5AGEJCYI5SQ',
  'accountant@hospital.com': 'IBSG27J4NN3HSZTQGY4SS2DMNRPEGJRZIJFW4423J5WDMUBFEVKA'
};

console.log('🧪 Testing Speakeasy TOTP Verification\n');

Object.entries(mfaSecrets).forEach(([email, secret]) => {
  console.log(`\n📧 ${email}`);
  console.log(`   Secret: ${secret}`);
  console.log(`   Length: ${secret.length}`);
  
  // Generate code
  const code = speakeasy.totp({
    secret: secret,
    encoding: 'base32',
    window: 2
  });
  
  console.log(`   Generated Code: ${code}`);
  
  // Verify the code
  const verified = speakeasy.totp.verify({
    secret: secret,
    encoding: 'base32',
    token: code,
    window: 2
  });
  
  console.log(`   Verification Result: ${verified ? '✅ PASS' : '❌ FAIL'}`);
  
  // Also test with window 1 (more strict)
  const verifiedStrict = speakeasy.totp.verify({
    secret: secret,
    encoding: 'base32',
    token: code,
    window: 1
  });
  
  console.log(`   With window: 1 = ${verifiedStrict ? '✅ PASS' : '❌ FAIL'}`);
});

console.log('\n✅ If all tests show PASS, speakeasy is working correctly');
