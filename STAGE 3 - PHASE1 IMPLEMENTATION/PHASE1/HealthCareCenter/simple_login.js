#!/usr/bin/env node

const http = require('http');

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
    // Login
    console.log('Logging in...');
    let res = await makeRequest('localhost', 4000, 'POST', '/api/login', {
      email: 'admin@hospital.com',
      password: 'Admin@123'
    });

    console.log('Status:', res.status);
    console.log('Response:', JSON.stringify(res.body, null, 2));

    if (res.body?.token) {
      console.log('\n✓ Got token:', res.body.token);
    } else if (res.body?.mfaRequired) {
      console.log('\n⚠ MFA Required - token:', res.body.token || 'none');
    }

  } catch (err) {
    console.error('Error:', err);
  }
}

test();
