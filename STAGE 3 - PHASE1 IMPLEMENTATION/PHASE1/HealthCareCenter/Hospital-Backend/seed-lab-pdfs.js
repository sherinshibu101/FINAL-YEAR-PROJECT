/**
 * Seed script to ensure lab_tests have result_pdf_key values
 * Run after database is created
 */
require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

async function seedLabTestPDFs() {
  const client = await pool.connect();
  try {
    console.log('📝 Updating lab_tests with PDF keys...\n');

    // Get all lab tests
    const res = await client.query('SELECT id, test_name, patient_id FROM lab_tests ORDER BY id LIMIT 10');
    const tests = res.rows;

    if (tests.length === 0) {
      console.log('ℹ️  No lab tests found in database');
      return;
    }

    console.log(`Found ${tests.length} lab tests\n`);

    // Map test IDs to PDF files
    const pdfMap = {
      1: { pdf: 'labs/cbc-alice-2024-11-25.pdf', status: 'completed' },
      2: { pdf: 'labs/blood-test-bob-2024-11-20.pdf', status: 'completed' },
      3: { pdf: 'labs/urinalysis-carol-2024-11-22.pdf', status: 'completed' }
    };

    // Update each test
    for (const test of tests) {
      const pdfInfo = pdfMap[test.id];
      if (pdfInfo) {
        await client.query(
          'UPDATE lab_tests SET result_pdf_key = $1, status = $2 WHERE id = $3',
          [pdfInfo.pdf, pdfInfo.status, test.id]
        );
        console.log(`✓ Updated test ${test.id}: ${test.test_name}`);
        console.log(`  PDF: ${pdfInfo.pdf}`);
        console.log(`  Status: ${pdfInfo.status}\n`);
      } else {
        console.log(`ℹ️  Skipped test ${test.id}: No PDF mapping`);
      }
    }

    console.log('✓ Lab tests updated successfully!');
  } catch (error) {
    console.error('✗ Error:', error.message);
  } finally {
    client.release();
    pool.end();
  }
}

seedLabTestPDFs();
