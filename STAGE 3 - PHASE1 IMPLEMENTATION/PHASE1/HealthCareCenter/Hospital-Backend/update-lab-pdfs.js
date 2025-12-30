/**
 * Update lab tests with result_pdf_key values
 * This script updates the lab_tests table to include PDF file references
 */

const db = require('./src/db');

async function updateLabTestsPDFKeys() {
  try {
    console.log('Updating lab_tests with PDF keys...');

    // Update lab tests with result_pdf_key
    const updates = [
      {
        id: 1,
        result_pdf_key: 'labs/cbc-alice-2024-11-25.pdf'
      },
      {
        id: 2,
        result_pdf_key: 'labs/blood-test-bob-2024-11-20.pdf'
      },
      {
        id: 3,
        result_pdf_key: 'labs/urinalysis-carol-2024-11-22.pdf'
      }
    ];

    for (const update of updates) {
      await db.query(
        'UPDATE lab_tests SET result_pdf_key = $1, status = $2 WHERE id = $3',
        [update.result_pdf_key, 'completed', update.id]
      );
      console.log(`✓ Updated lab_tests id=${update.id} with PDF key`);
    }

    console.log('✓ All lab tests updated with PDF keys!');
    process.exit(0);
  } catch (error) {
    console.error('✗ Error:', error.message);
    process.exit(1);
  }
}

updateLabTestsPDFKeys();
