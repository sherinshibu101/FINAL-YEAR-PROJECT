/**
 * Test script to verify file serving endpoint
 */
const http = require('http');
const path = require('path');
const fs = require('fs');

// Check if files exist first
const labReportsDir = path.join(__dirname, 'storage/lab-reports');
console.log('\n📁 Checking lab report directory...');
console.log(`Directory: ${labReportsDir}`);

if (fs.existsSync(labReportsDir)) {
  const files = fs.readdirSync(labReportsDir);
  console.log(`✓ Directory exists with ${files.length} files:`);
  files.forEach(f => {
    const filepath = path.join(labReportsDir, f);
    const stats = fs.statSync(filepath);
    console.log(`  - ${f} (${stats.size} bytes)`);
  });
} else {
  console.log('✗ Lab reports directory does not exist');
}

// Test the path construction logic
console.log('\n🔍 Testing path construction logic...');

const testPaths = [
  'labs/cbc-alice-2024-11-25.pdf',
  'labs/blood-test-bob-2024-11-20.pdf',
  'invoices/invoice_1.pdf'
];

testPaths.forEach(filepath => {
  let fullPath;
  
  if (filepath.startsWith('labs/')) {
    const filename = filepath.substring(5);
    fullPath = path.join(__dirname, 'storage/lab-reports', filename);
  } else if (filepath.startsWith('invoices/')) {
    const filename = filepath.substring(9);
    fullPath = path.join(__dirname, 'storage/invoices', filename);
  } else {
    fullPath = path.join(__dirname, 'storage', filepath);
  }

  const exists = fs.existsSync(fullPath);
  console.log(`\n  ${filepath}`);
  console.log(`  → ${fullPath}`);
  console.log(`  → ${exists ? '✓ EXISTS' : '✗ NOT FOUND'}`);
});

console.log('\n✓ Path construction test completed');
