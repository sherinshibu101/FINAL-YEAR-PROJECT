# 🚀 LAB TECHNICIAN PORTAL - SETUP & DEPLOYMENT GUIDE

## 📋 Table of Contents
1. Prerequisites
2. Database Setup
3. Backend Integration
4. Frontend Integration
5. Testing the System
6. Troubleshooting

---

## 1️⃣ PREREQUISITES

### Backend Requirements
- Node.js 16+ with npm
- PostgreSQL 12+ with uuid-ossp extension
- `.env` file with:
  ```
  DB_HOST=localhost
  DB_PORT=5432
  DB_NAME=healthcare_center
  DB_USER=postgres
  DB_PASSWORD=your_password
  
  JWT_SECRET=your_jwt_secret
  JWT_REFRESH_SECRET=your_refresh_secret
  
  ENCRYPTION_KEK=your_256_bit_key_in_base64
  ```

### Frontend Requirements
- Node.js 16+ with npm
- React 18+
- TypeScript 4.9+

---

## 2️⃣ DATABASE SETUP

### Step 1: Verify PostgreSQL is Running

```powershell
# Windows - Check if PostgreSQL service is running
Get-Service postgresql-x64-* | Select Status

# If not running, start it:
Start-Service postgresql-x64-15
```

### Step 2: Create Database (if not exists)

```powershell
# Connect to PostgreSQL
psql -U postgres

# In PostgreSQL:
CREATE DATABASE healthcare_center;
\c healthcare_center
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

### Step 3: Run Migrations

```powershell
# In Hospital-Backend folder:
cd Hospital-Backend

# Install dependencies
npm install

# Run all migrations including lab_tests
npx knex migrate:latest

# Output should show:
# Batch 1 run: x migrations
# ✓ 01_create_base_tables.js
# ✓ 02_create_auth_tables.js
# ✓ 03_seed_initial_users.js
# ✓ 20251129_lab_tests.js
```

### Step 4: Verify Tables Created

```powershell
# Connect to database
psql -U postgres -d healthcare_center

# Verify tables exist:
\dt

# Should show:
# lab_tests
# lab_samples
# lab_results
# lab_audit_logs
# (plus existing users, patients, etc.)

# Check lab_tests structure:
\d lab_tests

# Exit
\q
```

---

## 3️⃣ BACKEND INTEGRATION

### Step 1: Update Main Server File

**File:** `Hospital-Backend/src/index.js`

Find line ~1800 where routes are registered, and add:

```javascript
// Import lab routes
const labRoutes = require('./routes/lab');

// Register lab routes (add with other route registrations)
app.use('/api/lab', labRoutes);
```

**Location:** Should be near other `app.use()` statements like:
```javascript
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
// ... add lab routes here:
const labRoutes = require('./routes/lab');

app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/lab', labRoutes);  // <-- ADD THIS
```

### Step 2: Verify .env Has KEK

Update `Hospital-Backend/.env`:

```env
# Encryption Key Encryption Key (256-bit)
# This key encrypts the DEK (Data Encryption Keys)
ENCRYPTION_KEK=abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz==
```

### Step 3: Verify File Upload Directory

The migration creates an upload directory. Check it exists:

```powershell
# In Hospital-Backend folder:
New-Item -ItemType Directory -Force -Path "storage/lab_results"

# Permissions (Windows):
# Right-click storage folder → Properties → Security → Edit → Give Full Control to your user
```

### Step 4: Test Backend API

```powershell
# In Hospital-Backend:
npm start

# Terminal output should show:
# ✓ Server running on http://0.0.0.0:3000
# ✓ Database connected
```

Test the dashboard endpoint:
```powershell
# Open new terminal
curl -X GET http://localhost:3000/api/lab/dashboard `
  -H "Authorization: Bearer <TOKEN>"
```

Expected response:
```json
{
  "success": true,
  "dashboard": {
    "pending": 0,
    "collected": 0,
    "completed": 0,
    "total": 0
  }
}
```

---

## 4️⃣ FRONTEND INTEGRATION

### Step 1: Update App.tsx

**File:** `Hospital-Frontend/src/App.tsx`

Import the component:
```typescript
import LabTechnician from './components/LabTechnician';
```

Add to your tab switcher (find where you have `LabTests`, `Pharmacy`, etc.):

```typescript
{role === 'lab_technician' && (
  <button 
    onClick={() => setActiveTab('lab')}
    className={`px-4 py-2 rounded ${
      activeTab === 'lab' ? 'bg-blue-600 text-white' : 'bg-gray-200'
    }`}
  >
    Lab Portal
  </button>
)}

{/* In your render section: */}
{activeTab === 'lab' && <LabTechnician />}
```

### Step 2: Copy Component File

```powershell
# Copy LabTechnician.tsx to Hospital-Frontend/src/components/
Copy-Item -Path "Hospital-Frontend\src\components\LabTechnician.tsx" `
  -Destination "Hospital-Frontend\src\components\LabTechnician.tsx"
```

### Step 3: Install Dependencies (if needed)

```powershell
cd Hospital-Frontend

# These should already be installed:
npm install react react-dom
npm install axios
npm install lucide-react  # for icons

npm start
```

### Step 4: Test Frontend

```
1. Open browser: http://localhost:3000
2. Login as: labtech@hospital.com
3. Password: LabTech@123
4. Enter MFA code from authenticator
5. Click "Lab Portal" tab
6. Should see:
   - Dashboard with 4 stat cards
   - Tests tab
   - Upload tab
   - Audit tab
```

---

## 5️⃣ TESTING THE SYSTEM

### Test 1: Dashboard Loading

```
1. Login as lab technician
2. Go to Lab Portal tab
3. Verify 4 stat cards appear:
   - Pending
   - Collected
   - Completed
   - Total
4. All should show 0 (no data yet)
```

### Test 2: View Tests

```
1. In Lab Portal, click "Tests" tab
2. Click "Pending" filter
3. Should show: "No tests found" (add test data first via doctor UI)
4. Try other filters (Collected, Completed)
```

### Test 3: Sample Collection Workflow

**Setup:** First add test data via Doctor portal:
```
1. Login as doctor@hospital.com
2. Order a lab test for a patient (CBC, ECG, etc.)
3. Log out
```

**Test:**
```
1. Login as lab technician
2. Go to Tests tab, filter by Pending
3. Click "Collect" button on test
4. Fill form:
   - Sample Type: Blood
   - Barcode: SAMPLE-001
   - Notes: "Collected from left arm"
5. Click Submit
6. Verify: Test status changes to "Collected" ✓
```

### Test 4: Result Upload & Encryption

```
1. After sample collected, filter Tests to "Collected"
2. Click "Upload" button
3. Fill form:
   - Result Category: Normal
   - Select a PDF file from your computer
   - Notes: "All normal findings"
4. Click Submit
5. Watch network tab in DevTools:
   - POST /api/lab/results
   - Should show 200 OK
6. Verify: Test status changes to "Completed" ✓
```

### Test 5: Verify Encryption in Database

```powershell
# Connect to database
psql -U postgres -d healthcare_center

# Query encrypted data:
SELECT id, result_values_encrypted, result_values_iv, result_values_tag 
FROM lab_results 
LIMIT 1;

# Should show:
# - Ciphertext (looks like random hex)
# - IV (32 hex chars)
# - Tag (32 hex chars)
# Not readable plaintext ✓
```

### Test 6: Verify Audit Logging

```
1. In Lab Portal, go to "Audit" tab
2. Should see logs like:
   - "Rachel Wilson" "collected_sample" "success"
   - "Rachel Wilson" "uploaded_result" "success"
3. Timestamps should be current
4. Status should be "success"
```

### Test 7: File Hash Verification

```powershell
# Query audit logs:
SELECT id, action, log_hash FROM lab_audit_logs LIMIT 1;

# Hashes should be SHA-256 (64 hex chars)
# Example: "a1b2c3d4e5f6..."
```

---

## 6️⃣ TROUBLESHOOTING

### Issue: "Database connection refused"

**Solution:**
```powershell
# Check PostgreSQL is running:
Get-Service postgresql-x64-* | Select Status

# If not running:
Start-Service postgresql-x64-15

# Check connection:
psql -U postgres
\q
```

### Issue: "Migration failed: table already exists"

**Solution:**
```powershell
# If running migrations a second time:
npx knex migrate:rollback --all
npx knex migrate:latest
```

### Issue: "Cannot find module 'routes/lab'"

**Solution:**
1. Verify file exists: `Hospital-Backend/src/routes/lab.js`
2. Check import path in index.js:
   ```javascript
   const labRoutes = require('./routes/lab');  // Correct
   // NOT: require('./lab.js') or require('/routes/lab')
   ```

### Issue: "CORS error when calling API from frontend"

**Solution:**
Verify backend has CORS enabled in index.js:
```javascript
const cors = require('cors');
app.use(cors());  // Should be near top of file
```

### Issue: "File upload fails - 413 Payload Too Large"

**Solution:**
In `Hospital-Backend/src/index.js`, increase limit:
```javascript
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));
```

### Issue: "Cannot read property 'role' of undefined" in component

**Solution:**
In LabTechnician.tsx, verify you're reading role from auth context:
```typescript
const { user } = useAuth();  // Your auth hook
const role = user?.role || 'lab_technician';
```

### Issue: "Audit logs not showing"

**Solution:**
1. Check lab_audit_logs table has data:
   ```powershell
   psql -U postgres -d healthcare_center
   SELECT COUNT(*) FROM lab_audit_logs;
   ```
2. If 0 rows, try uploading a result again (should create log entry)
3. Verify API endpoint `/api/lab/audit-logs` works:
   ```powershell
   curl http://localhost:3000/api/lab/audit-logs
   ```

---

## ✅ FINAL CHECKLIST

- [ ] PostgreSQL database created and uuid-ossp extension added
- [ ] All migrations run successfully (`npx knex migrate:latest`)
- [ ] Backend .env has ENCRYPTION_KEK configured
- [ ] Lab routes imported in `Hospital-Backend/src/index.js`
- [ ] Frontend component LabTechnician.tsx exists in components folder
- [ ] LabTechnician component imported and added to App.tsx
- [ ] Backend starts with `npm start` on port 3000
- [ ] Frontend starts with `npm start` on port 3000 (or configured port)
- [ ] Can login as lab_technician
- [ ] Dashboard loads with stat cards
- [ ] Can view tests
- [ ] Can collect sample
- [ ] Can upload result
- [ ] Result data is encrypted in database
- [ ] Audit logs are recorded
- [ ] MFA verification works

---

## 🎉 SUCCESS!

Once all items are checked, the Lab Technician Portal is:
✅ Deployed
✅ Encrypted
✅ Auditable
✅ Production-Ready

---

**Last Updated:** November 29, 2025
**Status:** Ready for Deployment
