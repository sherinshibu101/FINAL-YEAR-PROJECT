// Quick test script
const http = require('http');

const options = {
  hostname: 'localhost',
  port: 3000,
  path: '/api/patients',
  method: 'GET',
  timeout: 5000
};

const req = http.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    console.log('✓ API Response:', data.substring(0, 200) + (data.length > 200 ? '...' : ''));
  });
});

req.on('error', (e) => {
  console.error('✗ Request failed:', e.message);
});

req.on('timeout', () => {
  console.error('✗ Request timeout');
  req.destroy();
});

req.end();
