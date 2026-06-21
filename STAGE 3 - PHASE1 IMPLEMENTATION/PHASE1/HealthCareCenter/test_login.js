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
    // Try port 4000 first, then 4001
    let res = await makeRequest('localhost', 4000, 'POST', '/api/login', {
      email: 'admin@hospital.com',
      password: 'Admin@123'
    });
    
    if (res.status === 404 || res.status === 500) {
      console.log('Port 4000 failed, trying 4001...');
      res = await makeRequest('localhost', 4001, 'POST', '/api/login', {
        email: 'admin@hospital.com',
        password: 'Admin@123'
      });
    }

    console.log('Login Response Status:', res.status);
    console.log('Login Response:', JSON.stringify(res.body, null, 2));

    if (res.body?.success && res.body?.token) {
      console.log('\n✓ Login successful!');
      console.log('Token:', res.body.token);
      console.log('Refresh Token:', res.body.refreshToken);
    }

  } catch (err) {
    console.error('Error:', err.message);
  }
}

test();
