#!/usr/bin/env node

const http = require('http');
const speakeasy = require('speakeasy');

function makeRequest(hostname, port, method, path, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname,
      port,
      path,
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            body: data ? JSON.parse(data) : null
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            body: data
          });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function test() {
  try {
    // Get MFA secret
    console.log('Getting MFA secret...');
    let res = await makeRequest('localhost', 4001, 'GET', '/api/admin/mfa/secret?email=admin@hospital.com');
    console.log('MFA Secret Response:', JSON.stringify(res.body, null, 2));

    if (res.body?.secret) {
      const secret = res.body.secret;
      console.log('\nUsing secret:', secret);
      
      // Generate TOTP code
      const token = speakeasy.totp({
        secret: secret,
        encoding: 'base32'
      });
      console.log('Generated TOTP Token:', token);

      // Now login with email and password
      console.log('\nLogging in...');
      res = await makeRequest('localhost', 4001, 'POST', '/api/login', {
        email: 'admin@hospital.com',
        password: 'Admin@123'
      });
      console.log('Login response:', JSON.stringify(res.body, null, 2));

      if (res.body?.mfaRequired) {
        console.log('\nVerifying MFA...');
        res = await makeRequest('localhost', 4001, 'POST', '/api/mfa/verify', {
          email: 'admin@hospital.com',
          code: token
        });
        console.log('MFA verify response:', JSON.stringify(res.body, null, 2));

        if (res.body?.success && res.body?.token) {
          console.log('\n✓ Login successful!');
          console.log('JWT Token:', res.body.token);
          process.stdout.write(res.body.token);
        }
      }
    }

  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
}

test();
