/**
 * Test MFA with actual database secrets
 */

const pg = require('pg');
const speakeasy = require('speakeasy');

const client = new pg.Client({
  user: 'hospital',
  password: 'F1UFDk8H36Ry2RITAvnErulW',
  host: 'localhost',
  port: 5432,
  database: 'hospital_db'
});

client.connect();

async function testMFAWithDatabaseSecrets() {
  try {
    const { rows: users } = await client.query('SELECT email, mfa_secret FROM users WHERE email = ANY($1)', 
      [['admin@hospital.com', 'doctor@hospital.com', 'labtech@hospital.com']]);
    
    console.log('\n═══════════════════════════════════════════════════');
    console.log('Testing MFA with Database Secrets');
    console.log('═══════════════════════════════════════════════════\n');

    for (const user of users) {
      const { email, mfa_secret } = user;
      
      if (!mfa_secret) {
        console.log(`❌ ${email}: No MFA secret in database`);
        continue;
      }

      console.log(`📧 ${email}`);
      console.log(`   Secret from DB: ${mfa_secret} (length: ${mfa_secret.length})`);
      
      // Generate code
      const code = speakeasy.totp({
        secret: mfa_secret,
        encoding: 'base32'
      });
      console.log(`   Generated Code: ${code}`);
      
      // Verify code
      const verified = speakeasy.totp.verify({
        secret: mfa_secret,
        encoding: 'base32',
        token: code,
        window: 2
      });
      
      console.log(`   Verification: ${verified ? '✅ SUCCESS' : '❌ FAILED'}`);
      console.log();
    }
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    client.end();
  }
}

testMFAWithDatabaseSecrets();
