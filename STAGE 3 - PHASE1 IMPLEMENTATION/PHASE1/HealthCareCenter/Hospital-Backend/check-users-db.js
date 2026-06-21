/**
 * Check what users are in the database
 * Run with: node check-users-db.js
 */

require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

async function checkUsers() {
  try {
    console.log('Connecting to database...');
    const client = await pool.connect();
    
    console.log('\nFetching users from database:\n');
    const result = await client.query(
      'SELECT id, email, role, password_hash, mfa_enabled FROM users ORDER BY email'
    );
    
    console.log(`Found ${result.rows.length} users:\n`);
    result.rows.forEach(user => {
      const hashPreview = user.password_hash ? user.password_hash.substring(0, 30) + '...' : 'NULL';
      console.log(`Email: ${user.email}`);
      console.log(`  Role: ${user.role}`);
      console.log(`  Hash: ${hashPreview}`);
      console.log(`  MFA: ${user.mfa_enabled}`);
      console.log('');
    });
    
    client.release();
    pool.end();
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

checkUsers();
