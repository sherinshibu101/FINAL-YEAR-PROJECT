#!/usr/bin/env node

const http = require('http');

let JWT_TOKEN = null;

function makeRequest(hostname, port, method, path, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: hostname === '127.0.0.1' ? 'localhost' : hostname,
      port,
      path,
      method,
      headers: { 'Content-Type': 'application/json' }
    };
    
    if (JWT_TOKEN && path !== '/api/login') {
      options.headers['Authorization'] = `Bearer ${JWT_TOKEN}`;
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: data ? JSON.parse(data) : null
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
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

async function debug() {
  // Login
  let res = await makeRequest('127.0.0.1', 4000, 'POST', '/api/login', {
    email: 'admin@hospital.com',
    password: 'Admin@123'
  });
  JWT_TOKEN = res.body.token;
  console.log('Logged in');

  // Create patient
  const newPatient = {
    first_name: 'DebugTest',
    last_name: 'Patient',
    dob: '1990-05-15',
    gender: 'Male',
    contact: '555-1234',
    insurance: 'INS123'
  };
  res = await makeRequest('127.0.0.1', 3000, 'POST', '/api/patients', newPatient);
  const patientId = res.body.data?.id;
  console.log('Created patient:', patientId);

  // Try to update
  console.log('\nUpdating patient...');
  res = await makeRequest('127.0.0.1', 3000, 'PUT', `/api/patients/${patientId}`, {
    first_name: 'Updated',
    last_name: 'Patient'
  });
  console.log('Status:', res.status);
  console.log('Response:', JSON.stringify(res.body, null, 2));
}

setTimeout(debug, 2000);
