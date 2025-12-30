# 🧪 LAB TECHNICIAN PORTAL - DEVELOPER QUICK REFERENCE

## 📁 File Structure

```
Hospital-Backend/
  src/
    index.js                    ← Add lab routes here
    routes/
      lab.js                    ← 6 endpoints + encryption logic
    migrations/
      20251129_lab_tests.js     ← Database schema

Hospital-Frontend/
  src/
    components/
      LabTechnician.tsx         ← React UI component
    App.tsx                     ← Add tab here

Encryption/
  encryptionService.js          ← Already exists, we import it
  kms.js                        ← Already exists, we use for KEK
```

---

## 🔌 QUICK SETUP (5 MINUTES)

### 1. Backend Integration (2 min)

**File:** `Hospital-Backend/src/index.js`

Add at top with other requires:
```javascript
const labRoutes = require('./routes/lab');
```

Add in route registration section:
```javascript
app.use('/api/lab', labRoutes);
```

### 2. Database Migrations (2 min)

```powershell
cd Hospital-Backend
npx knex migrate:latest
```

### 3. Frontend Integration (1 min)

**File:** `Hospital-Frontend/src/App.tsx`

```typescript
import LabTechnician from './components/LabTechnician';

// In render:
{role === 'lab_technician' && <LabTechnician />}
```

---

## 📊 ENDPOINT QUICK REFERENCE

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/lab/dashboard` | Get stat counts | lab_tech |
| GET | `/api/lab/tests?status=X` | List tests | lab_tech |
| POST | `/api/lab/samples` | Collect sample | lab_tech |
| POST | `/api/lab/results` | Upload results | lab_tech |
| GET | `/api/lab/results/:testId` | View result | doctor/admin |
| GET | `/api/lab/audit-logs` | View audit trail | lab_tech/admin |

---

## 🔐 ENCRYPTION QUICK REFERENCE

### How Results Are Stored

```javascript
// When uploaded:
POST /api/lab/results {
  testId: "uuid",
  resultValues: { hemoglobin: 13.5 },  // These get encrypted
  reportFile: <PDF>,                    // This gets encrypted
  techniciannotes: "Normal"              // This gets encrypted
}

// In database:
{
  result_values_encrypted: "a1b2c3d4...",  // AES-256-GCM
  result_values_iv: "12345678...",        // 128-bit IV
  result_values_tag: "abcdef...",         // Auth tag
  report_file_hash: "sha256hash...",      // SHA-256 for integrity
  dek_encrypted_with_kek: "wrapped..."    // KEK wrapping
}
```

### How Results Are Retrieved

```javascript
// When doctor views:
GET /api/lab/results/testId {
  1. Check IAM (is doctor or admin?)
  2. Decrypt using IV, tag, DEK
  3. Verify file hash (tamper check)
  4. Return plaintext
  5. Log access in audit_logs
}
```

---

## 🧪 TEST DATA SETUP

### Create Test Patient & Doctor Order

```javascript
// Via Doctor UI or API:
POST /api/patients {
  name: "John Doe",
  email: "john@example.com",
  ...
}

// Doctor orders test:
POST /api/lab/tests {
  patientId: "uuid",
  doctorId: "uuid", 
  testType: "CBC",
  status: "pending"
}
```

### Create Lab Technician

**Already exists:**
- Email: `labtech@hospital.com`
- Password: `LabTech@123`
- MFA Secret: `MJSSSLCEHQ7XQ4JROY3TSJCUJJ5VCXKHNBWTCXS3MIUHA3JZJZOQ`
- Role: `lab_technician`

---

## 🚨 COMMON ISSUES

### "Encryption failed: KEK not found"
```
Solution: Add ENCRYPTION_KEK to .env
ENCRYPTION_KEK=abcd1234efgh5678...
```

### "Cannot find module './routes/lab'"
```
Solution: Check Hospital-Backend/src/routes/lab.js exists
Verify import: const labRoutes = require('./routes/lab');
```

### "Unauthorized: User is not lab_technician"
```
Solution: Verify JWT token contains role: "lab_technician"
Use curl with proper Authorization header:
curl -H "Authorization: Bearer <token>" http://localhost:3000/api/lab/dashboard
```

### "File size exceeds 10MB"
```
Solution: Upload smaller file (max 10MB)
Or increase limit in lab.js multer config:
storage: multer.memoryStorage(),
limits: { fileSize: 50 * 1024 * 1024 } // 50MB
```

---

## 🔍 DEBUGGING TIPS

### Check If Database Tables Exist

```powershell
psql -U postgres -d healthcare_center
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public';
\q
```

### View Encrypted Data in Database

```powershell
psql -U postgres -d healthcare_center
SELECT 
  id,
  result_values_encrypted,
  result_values_hash,
  created_at
FROM lab_results;
\q
```

### Check Backend Logs

```powershell
# Backend terminal should show:
[LAB] POST /api/lab/results - Tech: Rachel Wilson
[LAB] Encrypting result data...
[LAB] Generating file hash: a1b2c3...
[LAB] Saving to database...
[LAB] Result ID: uuid - SUCCESS
```

### Verify Frontend API Calls

In Browser DevTools:
```
1. Open Network tab
2. Perform action (upload result)
3. Should see:
   POST /api/lab/results - 200 OK
   Response: { success: true, resultId: "uuid" }
```

---

## 📈 PERFORMANCE CONSIDERATIONS

### Database Indexes (Already Created)

- `lab_tests` on `status`, `patient_id`, `doctor_id`
- `lab_samples` on `test_id`, `collected_at`
- `lab_results` on `test_id`, `technician_id`
- `lab_audit_logs` on `user_id`, `created_at`

These make queries fast even with thousands of records.

### File Upload Best Practices

```javascript
// Limit file size to prevent memory issues
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 } // 10MB max
});

// For very large files, use disk storage:
const storage = multer.diskStorage({
  destination: 'storage/lab_results/',
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}-${file.originalname}`);
  }
});
```

---

## 🛡️ SECURITY CHECKLIST

- [ ] ENCRYPTION_KEK is set in .env
- [ ] KEK is 256-bit (43 chars in base64)
- [ ] All endpoints check user role
- [ ] All actions are logged to audit_logs
- [ ] MFA is enforced before lab tech login
- [ ] Patient names are masked in lists
- [ ] File hashes are stored and verified
- [ ] Auth tags prevent tampering

---

## 📝 CODE EXAMPLES

### Using Lab API from Frontend

```typescript
import axios from 'axios';

const token = localStorage.getItem('token');
const headers = { Authorization: `Bearer ${token}` };

// Get dashboard stats
const dashboard = await axios.get('/api/lab/dashboard', { headers });

// Collect sample
const sample = await axios.post('/api/lab/samples', {
  testId: 'test-uuid',
  sampleType: 'Blood',
  barcode: 'SAMPLE-001'
}, { headers });

// Upload results with file
const formData = new FormData();
formData.append('testId', 'test-uuid');
formData.append('reportFile', file);
formData.append('resultValues', JSON.stringify({ hemoglobin: 13.5 }));

const result = await axios.post('/api/lab/results', formData, { headers });
```

### Verifying Encryption Works

```javascript
// In backend test file:
const crypto = require('crypto');
const kek = Buffer.from(process.env.ENCRYPTION_KEK, 'base64');

function testEncryption() {
  const plaintext = JSON.stringify({ hemoglobin: 13.5 });
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-gcm', kek, iv);
  
  let encrypted = cipher.update(plaintext, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const tag = cipher.getAuthTag();
  
  // Verify decryption
  const decipher = crypto.createDecipheriv('aes-256-gcm', kek, iv);
  decipher.setAuthTag(tag);
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  console.log('Plaintext:', plaintext);
  console.log('Decrypted:', decrypted);
  console.log('Match:', plaintext === decrypted); // Should be true
}
```

---

## 🆘 SUPPORT COMMANDS

```powershell
# Start backend
cd Hospital-Backend
npm start

# Start frontend
cd Hospital-Frontend
npm start

# Run migrations
cd Hospital-Backend
npx knex migrate:latest

# Rollback migrations
cd Hospital-Backend
npx knex migrate:rollback --all

# Check database
psql -U postgres -d healthcare_center

# Clear lab data (reset for testing)
DELETE FROM lab_audit_logs;
DELETE FROM lab_results;
DELETE FROM lab_samples;
DELETE FROM lab_tests;
```

---

## 📚 Documentation Links

- Complete Guide: `LAB_TECHNICIAN_COMPLETE.md`
- Setup Guide: `LAB_TECHNICIAN_SETUP.md`
- Design Document: User's original design (this implementation)

---

**Last Updated:** November 29, 2025
**Quick Reference Version:** 1.0
