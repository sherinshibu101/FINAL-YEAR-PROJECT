#!/usr/bin/env node

/**
 * Test Patient CRUD Operations
 * Tests: Create, Read, Update, Delete
 */

const http = require('http');
const assert = require('assert');

let JWT_TOKEN = null;

function makeRequest(hostname, port, method, path, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: hostname,
      port: port,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    // Add authorization header if we have a token (except for login)
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

async function runTests() {
  console.log('=== Patient CRUD Test Suite ===\n');
  
  try {
    // First, get a fresh JWT token
    console.log('Authenticating...');
    let res = await makeRequest('127.0.0.1', 4000, 'POST', '/api/login', {
      email: 'admin@hospital.com',
      password: 'Admin@123'
    });
    
    if (!res.body?.token) {
      throw new Error('Failed to get authentication token: ' + JSON.stringify(res.body));
    }
    
    JWT_TOKEN = res.body.token;
    console.log('✓ Got authentication token\n');
    
    let patientId = null;
    
    // Test 1: GET existing patients
    console.log('Test 1: GET /api/patients');
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    console.log(`Status: ${res.status}`);
    console.log(`Response:`, res.body);
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.body.success === true, 'Expected success: true');
    assert(Array.isArray(res.body.patients), 'Expected patients array');
    console.log(`✓ Found ${res.body.patients.length} existing patients\n`);

    // Test 2: POST create new patient
    console.log('Test 2: POST /api/patients (Create)');
    const newPatient = {
      first_name: 'Test',
      last_name: 'Patient',
      dob: '1990-01-15',
      gender: 'Male',
      contact: '555-0123',
      insurance: 'HEALTH123'
    };
    res = await makeRequest('127.0.0.1', 3000, 'POST', '/api/patients', newPatient);
    console.log(`Status: ${res.status}`);
    console.log(`Response:`, res.body);
    assert(res.status === 201, `Expected 201, got ${res.status}`);
    assert(res.body.success === true, 'Expected success: true');
    assert(res.body.data?.id, 'Expected patient ID in response');
    patientId = res.body.data.id;
    console.log(`✓ Created patient with ID: ${patientId}\n`);

    // Test 3: GET to verify creation
    console.log('Test 3: GET /api/patients (Verify creation)');
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    console.log(`Status: ${res.status}`);
    const createdPatient = res.body.patients.find(p => p.id === patientId);
    assert(createdPatient, 'Patient not found after creation');
    console.log(`✓ Patient found in list:`, createdPatient);
    console.log(`✓ Patient details: Name=${createdPatient.name}, Age=${createdPatient.age}\n`);

    // Test 4: PUT update patient
    console.log('Test 4: PUT /api/patients/:id (Update)');
    const updatedData = {
      first_name: 'Updated',
      last_name: 'Patient',
      contact: '555-9999',
      insurance: 'HEALTH456'
    };
    res = await makeRequest('127.0.0.1', 3000, 'PUT', `/api/patients/${patientId}`, updatedData);
    console.log(`Status: ${res.status}`);
    console.log(`Response:`, res.body);
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.body.success === true, 'Expected success: true');
    console.log(`✓ Patient updated successfully\n`);

    // Test 5: GET to verify update
    console.log('Test 5: GET /api/patients (Verify update)');
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    const updatedPatient = res.body.patients.find(p => p.id === patientId);
    console.log(`✓ Updated patient:`, updatedPatient);
    assert(updatedPatient.first_name === 'Updated', 'First name not updated');
    console.log(`✓ Verified update: Name is now ${updatedPatient.first_name}\n`);

    // Test 6: DELETE patient
    console.log('Test 6: DELETE /api/patients/:id (Delete)');
    res = await makeRequest('127.0.0.1', 3000, 'DELETE', `/api/patients/${patientId}`);
    console.log(`Status: ${res.status}`);
    console.log(`Response:`, res.body);
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.body.success === true, 'Expected success: true');
    console.log(`✓ Patient deleted successfully\n`);

    // Test 7: GET to verify deletion
    console.log('Test 7: GET /api/patients (Verify deletion)');
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    const deletedPatient = res.body.patients.find(p => p.id === patientId);
    assert(!deletedPatient, 'Patient still exists after deletion');
    console.log(`✓ Patient no longer in list (deletion verified)\n`);

    console.log('=== ✓ ALL TESTS PASSED ===');
    process.exit(0);

  } catch (err) {
    console.error('\n✗ TEST FAILED:', err.message);
    console.error('Full error:', err);
    process.exit(1);
  }
}

runTests();
