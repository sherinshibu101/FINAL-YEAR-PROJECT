#!/usr/bin/env node

/**
 * QUICK START - FILE ENCRYPTION INTEGRATION
 * 
 * Run this to verify integration is working
 */

const http = require('http');

async function makeRequest(method, path, body, port = 3000) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port,
      path,
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 5000
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            body: JSON.parse(data)
          });
        } catch {
          resolve({
            status: res.statusCode,
            body: data
          });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Timeout'));
    });

    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function verify() {
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║          ENCRYPTION INTEGRATION VERIFICATION                   ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  // Check services running
  console.log('🔍 Checking services...\n');

  const checks = [
    {
      name: 'Backend API (port 3000)',
      test: async () => {
        const res = await makeRequest('GET', '/health', null, 3000);
        return res.status < 400;
      }
    },
    {
      name: 'IAM Service (port 4000)',
      test: async () => {
        const res = await makeRequest('GET', '/', null, 4000);
        return res.status < 500;
      }
    },
    {
      name: 'Frontend (port 5173)',
      test: async () => {
        const res = await makeRequest('GET', '/', null, 5173);
        return res.status < 500;
      }
    }
  ];

  let allRunning = true;
  for (const check of checks) {
    try {
      const passed = await check.test();
      console.log(`${passed ? '✓' : '✗'} ${check.name}`);
      if (!passed) allRunning = false;
    } catch (err) {
      console.log(`✗ ${check.name} - Not running`);
      allRunning = false;
    }
  }

  console.log('\n' + '─'.repeat(64) + '\n');

  if (!allRunning) {
    console.log('❌ Some services are not running!\n');
    console.log('Start services with:');
    console.log('  Terminal 1: cd Hospital-Backend && npm start');
    console.log('  Terminal 2: cd Hospital-Frontend/server && node index.js');
    console.log('  Terminal 3: cd Hospital-Frontend && npm run dev\n');
    return;
  }

  // Test login
  console.log('🔐 Testing authentication...\n');

  try {
    const loginRes = await makeRequest('POST', '/api/login', {
      email: 'admin@hospital.com',
      password: 'Admin@123'
    }, 3000);

    if (loginRes.status !== 200) {
      console.log(`✗ Login failed: ${loginRes.status}`);
      console.log(JSON.stringify(loginRes.body, null, 2));
      return;
    }

    const token = loginRes.body.token;
    console.log(`✓ Login successful - token obtained\n`);

    // Test encryption endpoints
    console.log('🔐 Checking encryption endpoints...\n');

    const options = {
      hostname: 'localhost',
      port: 3000,
      path: '/api/files/status/sample.txt',
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      timeout: 5000
    };

    const statusRes = await new Promise((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', chunk => { data += chunk; });
        res.on('end', () => {
          try {
            resolve({
              status: res.statusCode,
              body: JSON.parse(data)
            });
          } catch {
            resolve({
              status: res.statusCode,
              body: data
            });
          }
        });
      });
      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Timeout'));
      });
      req.end();
    });

    if (statusRes.status === 503) {
      console.log('⚠ Encryption service not initialized');
      console.log('  → To enable: Set up /Encryption folder and initialize storage\n');
    } else if (statusRes.status === 200) {
      console.log('✓ Encryption endpoints available');
      console.log(`  → Endpoints: /api/files/decrypt, /api/files/encrypt, /api/files/status/:fileId\n`);
    }

  } catch (err) {
    console.log(`✗ Test failed: ${err.message}\n`);
    return;
  }

  console.log('─'.repeat(64) + '\n');
  console.log('✅ Integration verification complete!\n');
  console.log('🚀 Next steps:');
  console.log('   1. Go to http://localhost:5173');
  console.log('   2. Login with: admin@hospital.com / Admin@123');
  console.log('   3. Navigate to File Encryption section');
  console.log('   4. Click "Decrypt" on a file\n');
  console.log('📚 For detailed info: Read ENCRYPTION_INTEGRATION_GUIDE.md\n');
}

verify().catch(console.error);
