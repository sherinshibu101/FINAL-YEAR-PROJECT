# Lab Report Encryption Fix - Database Schema

## Problem Identified
The backend was throwing this error when trying to encrypt lab reports:
```
Encryption error: error: column "encryption_status" of relation "lab_results" does not exist
```

**Root Cause:** The code in `Hospital-Backend/src/index.js` (line 3299) was trying to UPDATE/INSERT the `encryption_status` column in the `lab_results` table, but the database migration that created the table didn't include this column.

## Solution Applied

### 1. Created New Migration
**File:** `Hospital-Backend/src/migrations/20251201_add_encryption_status.js`

Added the following columns to the `lab_results` table:
- `encryption_status` (text, default 'none') - Tracks: 'none', 'encrypted', 'decrypted'
- `encrypted_at` (timestamp) - When encryption was performed
- `encrypted_by` (uuid) - Which user encrypted the report
- `decrypted_at` (timestamp) - When decryption was performed
- `decrypted_by` (uuid) - Which user decrypted the report

### 2. Fixed Existing Migrations
**File:** `Hospital-Backend/src/migrations/20251130_comprehensive_update.js`

Fixed migration script to check if columns already exist before attempting to add them, preventing "column already exists" errors on subsequent runs.

### 3. Executed Migrations
```bash
npx knex migrate:latest
```

**Result:** ✅ All migrations succeeded
```
✓ Migration 20251130_comprehensive_update completed
Batch 2 run: 2 migrations
```

## Code Files Affected

### 1. `Hospital-Backend/src/index.js`
**Lines:** 3280-3320 (POST /api/lab/results/:testId/encrypt)
- Now can successfully INSERT lab results with `encryption_status = 'encrypted'`
- Records `encrypted_at` timestamp
- Tracks which user performed the encryption (`encrypted_by`)

**Lines:** 3370-3385 (POST /api/lab/results/:testId/decrypt)
- Now can successfully UPDATE lab results with `encryption_status = 'decrypted'`
- Records `decrypted_at` timestamp
- Tracks which user performed the decryption (`decrypted_by`)

### 2. `Hospital-Backend/src/routes/lab.js`
**Lines:** 360-400 (GET /api/lab/results/:testId/download)
- Already uses encryption status from database via `results.encryption_status`
- Download endpoint now properly reads encryption metadata

## Database Schema

Updated `lab_results` table now includes:
```
 id                              | uuid | Primary Key
 test_id                         | uuid | FK → lab_tests
 sample_id                       | uuid | FK → lab_samples
 technician_id                   | uuid | FK → users
 result_values_encrypted         | text | Encrypted result values
 result_values_iv                | text | IV for encryption
 result_values_tag               | text | Auth tag for encryption
 report_file_encrypted           | text | Encrypted PDF file
 report_file_iv                  | text | IV for encryption
 report_file_tag                 | text | Auth tag for encryption
 report_file_hash                | text | SHA-256 integrity check
 report_file_mime_type           | text | MIME type (e.g., application/pdf)
 technician_notes_encrypted      | text | Encrypted notes
 technician_notes_iv             | text | IV for encryption
 technician_notes_tag            | text | Auth tag for encryption
 dek_encrypted_with_kek          | text | Wrapped Data Encryption Key
 kek_version                     | text | KMS version (e.g., 'v1')
 result_category                 | text | Normal, Abnormal, Critical
 reference_ranges                | text | JSON reference ranges
 completed_at                    | timestamp | When result was completed
 status                          | text | draft, completed, reviewed, reported
 ** encryption_status **         | text | none, encrypted, decrypted    [NEW]
 ** encrypted_at **              | timestamp | Encryption timestamp       [NEW]
 ** encrypted_by **              | uuid | User who encrypted            [NEW]
 ** decrypted_at **              | timestamp | Decryption timestamp       [NEW]
 ** decrypted_by **              | uuid | User who decrypted            [NEW]
 created_at                      | timestamp | Record created
 updated_at                      | timestamp | Record updated
```

## Testing the Fix

### Option 1: Test via API
Once the backend is running (port 3000), perform these steps:

1. **Login as Lab Technician:**
   ```bash
   POST /api/auth/login
   {
     "email": "labtech@hospital.com",
     "password": "SecurePass123!",
     "mfaCode": "000000"
   }
   ```

2. **Encrypt a Lab Report:**
   ```bash
   POST /api/lab/results/[test-id]/encrypt
   Content-Type: application/json
   Authorization: Bearer [jwt-token]
   
   {
     "filename": "lab-report.pdf",
     "fileContent": "[base64-encoded-pdf]"
   }
   ```
   
   **Expected Response:** ✅ 200 OK
   ```json
   {
     "success": true,
     "message": "Report encrypted and saved",
     "testId": "e8b79a4f-b3db-48ed-8149-ed13027a3bff",
     "encryptionStatus": "encrypted",
     "encryptedAt": "2025-12-01T09:00:00Z"
   }
   ```

3. **Decrypt Lab Report (Doctor):**
   ```bash
   GET /api/lab/results/[test-id]/download
   Authorization: Bearer [doctor-jwt-token]
   ```
   
   **Expected Response:** ✅ 200 OK with decrypted PDF

### Option 2: Direct Database Query
```sql
SELECT 
  id, 
  test_id, 
  encryption_status, 
  encrypted_at, 
  encrypted_by, 
  decrypted_at, 
  decrypted_by
FROM lab_results
WHERE encryption_status IS NOT NULL
ORDER BY encrypted_at DESC
LIMIT 5;
```

## Verification Checklist

- [x] Migration file created: `20251201_add_encryption_status.js`
- [x] Previous migration fixed: `20251130_comprehensive_update.js`
- [x] All migrations executed successfully
- [x] Backend server restarted with new schema
- [x] No "column does not exist" errors expected
- [x] Encryption/decryption endpoints have required database columns
- [x] Audit trail supports encryption metadata

## Known Issues Resolved

| Error | Status | Solution |
|-------|--------|----------|
| "column 'encryption_status' of relation 'lab_results' does not exist" | ✅ FIXED | Added column via migration 20251201_add_encryption_status.js |
| Migration failure: "column 'doctor_fees' already exists" | ✅ FIXED | Updated 20251130 to check for existing columns |
| Missing encryption tracking columns | ✅ FIXED | Added encrypted_at, encrypted_by, decrypted_at, decrypted_by |

## Next Steps

1. **Run full test suite** to verify encryption/decryption flows
2. **Monitor logs** for any remaining schema-related errors
3. **Verify audit trail** shows encryption metadata
4. **Test temp file cleanup** still works with new columns
5. **Load test** the encrypt/decrypt endpoints

## Files Modified

```
Hospital-Backend/
├── src/
│   └── migrations/
│       ├── 20251130_comprehensive_update.js [UPDATED - Fixed column existence checks]
│       └── 20251201_add_encryption_status.js [NEW - Added encryption tracking columns]
├── src/index.js [NO CHANGES NEEDED - Code already references new columns]
└── src/routes/lab.js [NO CHANGES NEEDED - Code already references encryption_status]
```

## Related Documentation

- `LAB_DECRYPTION_FIXES.md` - Detailed implementation guide
- `LAB_DECRYPTION_IMPLEMENTATION_CHECKLIST.md` - Testing procedures
- `LAB_REPORT_COMPLETE_SOLUTION.md` - Complete solution overview
- `LAB_SOLUTION_SUMMARY.md` - Visual summary with diagrams
