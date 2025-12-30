/**
 * Check what MFA secrets are actually in the database
 */

const pg = require('pg');

const client = new pg.Client({
  user: 'hospital',
  password: 'F1UFDk8H36Ry2RITAvnErulW',
  host: 'localhost',
  port: 5432,
  database: 'hospital_db'
});

client.connect(async (err) => {
  if (err) {
    console.error('Connection error:', err);
    process.exit(1);
  }
  
  try {
    const result = await client.query(`
      SELECT email, mfa_secret, length(mfa_secret) as secret_length 
      FROM users 
      WHERE mfa_enabled = 'true'
      ORDER BY email
    `);
    
    console.log('MFA Secrets from Database:\n');
    result.rows.forEach(row => {
      console.log(`Email: ${row.email}`);
      console.log(`Secret: ${row.mfa_secret}`);
      console.log(`Length: ${row.secret_length}`);
      console.log('---');
    });
    
    client.end();
  } catch (error) {
    console.error('Query error:', error);
    client.end();
  }
});
