#!/usr/bin/env node

/**
 * Comprehensive System Test
 * Tests: Patient CRUD, Appointment CRUD, Authentication
 */

const http = require('http');
const assert = require('assert');

let JWT_TOKEN = null;
const results = {
  passed: 0,
  failed: 0,
  tests: []
};

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

function logTest(name, passed, error = null) {
  if (passed) {
    results.passed++;
    console.log(`✓ ${name}`);
  } else {
    results.failed++;
    console.log(`✗ ${name}`);
    if (error) console.log(`  Error: ${error}`);
  }
  results.tests.push({ name, passed, error });
}

async function runTests() {
  console.log('╔════════════════════════════════════════╗');
  console.log('║  Hospital Portal - Comprehensive Test  ║');
  console.log('╚════════════════════════════════════════╝\n');
  
  try {
    // ===== AUTHENTICATION TESTS =====
    console.log('📋 Authentication Tests\n');
    
    // Test 1: Login
    let res = await makeRequest('127.0.0.1', 4000, 'POST', '/api/login', {
      email: 'admin@hospital.com',
      password: 'Admin@123'
    });
    
    if (res.body?.token) {
      JWT_TOKEN = res.body.token;
      logTest('Login with valid credentials', true);
    } else {
      logTest('Login with valid credentials', false, JSON.stringify(res.body));
      throw new Error('Authentication failed');
    }

    // ===== PATIENT CRUD TESTS =====
    console.log('\n👥 Patient CRUD Tests\n');
    
    let patientId = null;
    
    // Test 2: GET patients
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    logTest('GET /api/patients', res.status === 200 && res.body.success);
    const initialPatientCount = res.body.patients?.length || 0;
    
    // Test 3: POST create patient
    const newPatient = {
      first_name: 'Test',
      last_name: 'Patient',
      dob: '1990-05-15',
      gender: 'Male',
      contact: '555-1234',
      insurance: 'INS123'
    };
    res = await makeRequest('127.0.0.1', 3000, 'POST', '/api/patients', newPatient);
    logTest('POST /api/patients (create)', res.status === 201 && res.body.success);
    patientId = res.body.data?.id;
    
    // Test 4: Verify patient created
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    const createdPatient = res.body.patients?.find(p => p.id === patientId);
    logTest('Patient appears in list after creation', !!createdPatient);
    
    // Test 5: PUT update patient
    res = await makeRequest('127.0.0.1', 3000, 'PUT', `/api/patients/${patientId}`, {
      first_name: 'Updated',
      last_name: 'Patient',
      contact: '555-9999'
    });
    const putSuccess = res.status === 200 && res.body.success;
    logTest('PUT /api/patients/:id (update)', putSuccess, !putSuccess ? `Status: ${res.status}, Body: ${JSON.stringify(res.body)}` : null);
    
    // Test 6: Verify patient updated
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    const updatedPatient = res.body.patients?.find(p => p.id === patientId);
    const isUpdated = updatedPatient?.first_name === 'Updated' || updatedPatient?.name?.includes('Updated');
    logTest('Patient updated correctly', isUpdated);

    // ===== APPOINTMENT CRUD TESTS =====
    console.log('\n📅 Appointment CRUD Tests\n');
    
    let appointmentId = null;
    
    // Test 7: GET appointments
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/appointments');
    logTest('GET /api/appointments', res.status === 200 && res.body.success);
    const initialAppointmentCount = res.body.appointments?.length || 0;
    
    // Test 8: POST create appointment
    const now = new Date();
    const futureDate = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000); // 7 days from now
    const newAppointment = {
      patient_id: patientId,
      doctor_id: null,
      scheduled_at: futureDate.toISOString(),
      appointment_type: 'consultation',
      notes: 'Test appointment'
    };
    res = await makeRequest('127.0.0.1', 3000, 'POST', '/api/appointments', newAppointment);
    logTest('POST /api/appointments (create)', res.status === 201 && res.body.success);
    appointmentId = res.body.data?.id;
    
    // Test 9: Verify appointment created
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/appointments');
    const createdAppointment = res.body.appointments?.find(a => a.id === appointmentId);
    logTest('Appointment appears in list after creation', !!createdAppointment);
    
    // Test 10: PUT update appointment
    const newFutureDate = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000); // 14 days from now
    res = await makeRequest('127.0.0.1', 3000, 'PUT', `/api/appointments/${appointmentId}`, {
      scheduled_at: newFutureDate.toISOString(),
      notes: 'Updated appointment'
    });
    logTest('PUT /api/appointments/:id (update)', res.status === 200 && res.body.success);
    
    // Test 11: DELETE appointment
    res = await makeRequest('127.0.0.1', 3000, 'DELETE', `/api/appointments/${appointmentId}`);
    logTest('DELETE /api/appointments/:id', res.status === 200 && res.body.success);
    
    // Test 12: Verify appointment deleted
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/appointments');
    const deletedAppointment = res.body.appointments?.find(a => a.id === appointmentId);
    logTest('Appointment removed after deletion', !deletedAppointment);

    // ===== AUTHENTICATION TESTS =====
    console.log('\n🔐 Authorization Tests\n');
    
    // Test 13: DELETE patient
    res = await makeRequest('127.0.0.1', 3000, 'DELETE', `/api/patients/${patientId}`);
    logTest('DELETE /api/patients/:id', res.status === 200 && res.body.success);
    
    // Test 14: Verify patient deleted
    res = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    const deletedPatient = res.body.patients?.find(p => p.id === patientId);
    logTest('Patient removed after deletion', !deletedPatient);

    // ===== ERROR HANDLING TESTS =====
    console.log('\n⚠️ Error Handling Tests\n');
    
    // Test 15: Invalid token
    const invalidRes = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    // First clear the token temporarily
    const savedToken = JWT_TOKEN;
    JWT_TOKEN = 'invalid_token_12345';
    const invalidAuthRes = await makeRequest('127.0.0.1', 3000, 'GET', '/api/patients');
    JWT_TOKEN = savedToken;
    logTest('Invalid token rejected', invalidAuthRes.status === 401);
    
    // Test 16: Missing required fields
    res = await makeRequest('127.0.0.1', 3000, 'POST', '/api/patients', {
      first_name: 'Test'
      // Missing last_name
    });
    logTest('POST /api/patients with missing fields', res.status === 400);

    // ===== SUMMARY =====
    console.log('\n╔════════════════════════════════════════╗');
    console.log(`║  Results: ${results.passed} passed, ${results.failed} failed      ║`);
    console.log('╚════════════════════════════════════════╝\n');
    
    if (results.failed === 0) {
      console.log('🎉 All tests passed!');
      process.exit(0);
    } else {
      console.log('❌ Some tests failed');
      process.exit(1);
    }

  } catch (err) {
    console.error('\n✗ CRITICAL TEST ERROR:', err.message);
    console.error('Full error:', err);
    process.exit(1);
  }
}

// Run with a delay to allow servers to stabilize
setTimeout(runTests, 2000);
