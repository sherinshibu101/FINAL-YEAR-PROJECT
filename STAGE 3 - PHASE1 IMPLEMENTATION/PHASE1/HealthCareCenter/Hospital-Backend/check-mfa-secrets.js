const pg = require('pg');

const client = new pg.Client({
  user: 'hospital',
  password: 'F1UFDk8H36Ry2RITAvnErulW',
  host: 'localhost',
  port: 5432,
  database: 'hospital_db'
});

client.connect();

client.query('SELECT email, mfa_enabled, mfa_secret FROM users ORDER BY email', (err, result) => {
  if (err) {
    console.error('Database error:', err);
  } else {
    console.log('\nAll MFA Secrets in Database:\n');
    result.rows.forEach(row => {
      const status = row.mfa_enabled ? 'Enabled' : 'Disabled';
      console.log(`${row.email.padEnd(30)} | ${status.padEnd(10)} | ${row.mfa_secret || '(none)'}`);
    });
  }
  client.end();
});
