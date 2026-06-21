/**
 * MFA Code Generator Utility
 * This file can be used to generate TOTP codes for testing
 * Usage: node mfa-code-generator.js <secret>
 * Example: node mfa-code-generator.js JBSWY3DPEBLW64TMMQ======
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

function generateMfaCode(secret) {
  return speakeasy.totp({
    secret: secret,
    encoding: 'base32',
    window: 2
  });
}

function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('MFA Code Generator\n');
    console.log('Usage: node mfa-code-generator.js <email-or-secret>\n');
    console.log('Predefined Users:');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    Object.entries(mfaSecrets).forEach(([email, secret]) => {
      const code = generateMfaCode(secret);
      console.log(`${email.padEnd(30)} | Code: ${code}`);
    });
    
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('\nOr generate code for custom secret:');
    console.log('  node mfa-code-generator.js JBSWY3DPEBLW64TMMQ======\n');
    return;
  }

  const input = args[0];

  // Check if input is an email
  if (mfaSecrets[input]) {
    const code = generateMfaCode(mfaSecrets[input]);
    console.log(`\n${input}`);
    console.log(`Secret: ${mfaSecrets[input]}`);
    console.log(`Current MFA Code: ${code}`);
    console.log(`Valid for: ~30 seconds\n`);
    return;
  }

  // Otherwise treat as secret
  try {
    const code = generateMfaCode(input);
    console.log(`\nSecret: ${input}`);
    console.log(`Current MFA Code: ${code}`);
    console.log(`Valid for: ~30 seconds\n`);
  } catch (error) {
    console.error('Error:', error.message);
    console.log('\nPlease provide a valid base32-encoded secret\n');
  }
}

main();
