/**
 * Direct backend integration test - generate code and verify immediately
 */

const speakeasy = require('speakeasy');
const pg = require('pg');

const client = new pg.Client({
  user: 'hospital',
  password: 'F1UFDk8H36Ry2RITAvnErulW',
  host: 'localhost',
  port: 5432,
  database: 'hospital_db'
});

async function test() {
  try {
    await client.connect();
    
    console.log('🧪 Testing MFA Backend Logic Directly\n');
    
    // Get user from DB
    const email = 'doctor@hospital.com';
    const result = await client.query('SELECT * FROM users WHERE email = $1', [email]);
    const user = result.rows[0];
    
    if (!user) {
      console.log('❌ User not found');
      return;
    }
    
    console.log(`📧 ${email}`);
    console.log(`   Secret from DB: ${user.mfa_secret}`);
    console.log(`   Secret length: ${user.mfa_secret.length}`);
    
    // Generate fresh code
    const code = speakeasy.totp({
      secret: user.mfa_secret,
      encoding: 'base32',
      window: 2
    });
    
    console.log(`\n   Generated code: ${code}`);
    
    // Now simulate backend verification (exactly as the code does)
    const tokenStr = String(code).trim();
    const secretStr = String(user.mfa_secret).trim();
    
    console.log(`\n   Token (trimmed): "${tokenStr}"`);
    console.log(`   Secret (trimmed): "${secretStr}"`);
    
    const verified2 = speakeasy.totp.verify({
      secret: secretStr,
      encoding: 'base32',
      token: tokenStr,
      window: 2
    });
    
    const verified1 = speakeasy.totp.verify({
      secret: secretStr,
      encoding: 'base32',
      token: tokenStr,
      window: 1
    });
    
    console.log(`\n   Verified (window: 2): ${verified2}`);
    console.log(`   Verified (window: 1): ${verified1}`);
    
    if (verified2 || verified1) {
      console.log('\n✅ MFA VERIFICATION SUCCESS');
    } else {
      console.log('\n❌ MFA verification failed');
      
      // Try with the raw secret (no trim)
      const verifiedRaw = speakeasy.totp.verify({
        secret: user.mfa_secret,
        encoding: 'base32',
        token: code,
        window: 2
      });
      
      console.log(`   With raw secret and code: ${verifiedRaw}`);
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await client.end();
  }
}

test();
