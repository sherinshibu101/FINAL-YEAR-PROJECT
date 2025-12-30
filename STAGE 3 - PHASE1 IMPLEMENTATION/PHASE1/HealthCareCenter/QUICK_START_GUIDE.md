# Hospital Portal - Quick Start & Access Guide

## System Status Check

### Prerequisites
Ensure all services are running:

```powershell
# Check if processes are running
Get-Process node | Where-Object {$_.ProcessName -eq 'node'}

# Expected output: Should show 2 node processes (backend + frontend)
```

### Service URLs
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:3000
- **Database Admin:** http://localhost:8080 (Adminer)
- **IAM Server:** http://localhost:4000

---

## Quick Access - Test Credentials

### Step 1: Open Frontend
```
URL: http://localhost:5173
```

### Step 2: Login with These Credentials

**Admin (Full Access)**
```
Email:    admin@hospital.com
Password: Admin@123
MFA Code: 123456
```

**Doctor**
```
Email:    doctor@hospital.com
Password: Doctor@123
MFA Code: 123456
```

**Lab Technician**
```
Email:    labtech@hospital.com
Password: LabTech@123
MFA Code: 123456
```

**Accountant**
```
Email:    accountant@hospital.com
Password: Accountant@123
MFA Code: 123456
```

**Pharmacist**
```
Email:    pharmacist@hospital.com
Password: Pharmacist@123
MFA Code: 123456
```

**Patient**
```
Email:    patient@hospital.com
Password: Patient@123
MFA Code: 123456
```

---

## Feature Access by Role

### Admin → Can Access Everything
1. Navigate to **Dashboard** → See all statistics
2. Click **Admin Dashboard** → View audit logs and system stats
3. Click **Lab Tests** → Order tests
4. Click **Billing** → Create bills, manage payments
5. Click **Pharmacy** → Manage inventory
6. Click **Patients** → Manage patient records
7. Click **Appointments** → Manage scheduling

### Doctor → Can Order Lab Tests & View Patients
1. Click **Patients** → See patient list
2. Click **Lab Tests** → Order lab tests
3. Click **Files** → View encrypted patient files
4. Click **Appointments** → See scheduled appointments

### Lab Technician → Can Upload Lab Results
1. Click **Lab Tests** → See list of pending tests
2. Click **Upload** button → Upload test results (PDF or JSON)
3. Status changes to "completed"

### Accountant → Can Create & Manage Bills
1. Click **Billing** → View all bills
2. Click **Create Bill** button → Create new bill
3. Click **+** button on bill → Add itemized services
4. Click **Pay** button → Process payment

### Pharmacist → Can Manage Inventory & Fulfill Prescriptions
1. Click **Pharmacy** → Switch to **Inventory** tab
2. Click **Add Medication** → Add new drugs
3. Switch to **Prescriptions** tab
4. Click **Fill** button → Mark prescriptions as completed

### Patient → Can View Own Data
1. Click **Files** → See own uploaded documents
2. Click **Appointments** → See own appointments
3. Click **Lab Tests** → See own lab results
4. Click **Billing** → See own bills

---

## Database Access (Adminer)

### View Database Tables
```
URL: http://localhost:8080
Server: postgres
Username: postgres
Password: postgres
Database: hospital_db
```

### Tables Available
1. `users` - User accounts and roles
2. `patients` - Patient records
3. `appointments` - Scheduled appointments
4. `lab_tests` - Lab test requests and results
5. `prescriptions` - Medicine prescriptions
6. `vitals` - Vital signs data
7. `files` - Encrypted file metadata
8. `audit_logs` - Action logging
9. `billing` - Invoice records
10. `billing_services` - Itemized services
11. `pharmacy_inventory` - Medicine stock

---

## Test Workflows

### Workflow 1: Order and Upload Lab Test (5 minutes)

**Step 1: Login as Doctor**
- Email: doctor@hospital.com
- Password: Doctor@123
- MFA: 123456

**Step 2: Order Lab Test**
- Navigate to "Lab Tests"
- Click "Order Test"
- Enter Patient ID (see note below)
- Test Name: "Blood Test"
- Click "Order Test"
- ✅ Test appears as "pending"

**Step 3: Switch to Lab Technician**
- Logout (top right)
- Login as labtech@hospital.com
- Password: LabTech@123
- MFA: 123456

**Step 4: Upload Results**
- Navigate to "Lab Tests"
- Click "Upload" on the pending test
- Enter result data: `{"hemoglobin": 13.5, "blood_type": "O+"}`
- Click "Upload Results"
- ✅ Status changes to "completed"

### Workflow 2: Create Bill and Process Payment (5 minutes)

**Step 1: Login as Accountant**
- Email: accountant@hospital.com
- Password: Accountant@123
- MFA: 123456

**Step 2: Create Bill**
- Navigate to "Billing"
- Click "Create Bill"
- Patient ID: (see note below)
- Total Amount: 500
- Discount: 50
- Click "Create Bill"
- ✅ Bill created with final amount $450

**Step 3: Add Services**
- Click "+" button on the bill
- Service: "Consultation"
- Quantity: 1
- Unit Price: 100
- Click "Add Service"
- ✅ Service added

**Step 4: Process Payment**
- Click "Pay" button
- Amount: 450
- Click "Process Payment"
- ✅ Bill status changes to "paid"

### Workflow 3: Manage Pharmacy Inventory (5 minutes)

**Step 1: Login as Pharmacist**
- Email: pharmacist@hospital.com
- Password: Pharmacist@123
- MFA: 123456

**Step 2: Add Medication**
- Navigate to "Pharmacy"
- Make sure "Inventory" tab is selected
- Click "Add Medication"
- Medicine Name: "Aspirin"
- Generic Name: "Acetylsalicylic Acid"
- Manufacturer: "Bayer"
- Stock: 500
- Reorder Level: 50
- Price: 2.50
- Click "Add Medication"
- ✅ Medication appears in table

**Step 3: Edit Stock**
- Click "Edit" on the medication
- Stock: 480 (simulate sales)
- Click "Update"
- ✅ Stock updated

### Workflow 4: View Admin Dashboard (5 minutes)

**Step 1: Login as Admin**
- Email: admin@hospital.com
- Password: Admin@123
- MFA: 123456

**Step 2: Check Statistics**
- Navigate to "Admin Dashboard"
- See 6 stat cards:
  - Total Patients
  - Total Appointments
  - Today's Appointments
  - Total Revenue
  - Pending Bills
  - Active Staff

**Step 3: View Audit Logs**
- Click "Audit Logs" tab
- See all system actions
- Columns: Actor, Role, Action, Entity, Timestamp
- ✅ All previous actions logged

---

## Important Notes

### Getting Patient ID
To order tests or create bills, you need a patient UUID. Here's how:

**Option 1: Create New Patient**
1. Login as admin/doctor
2. Click "Patients"
3. Click "Add Patient"
4. Fill form with patient details
5. Copy the ID that appears

**Option 2: View Existing Patient**
1. Click "Patients"
2. Right-click on a patient in the table
3. Copy the UUID from the database

**Option 3: Check Database Directly**
1. Go to Adminer: http://localhost:8080
2. Select `patients` table
3. Copy any `id` value

### MFA Code
- All test users have MFA code: **123456**
- Same code works for all test accounts
- In real deployment, codes would be unique per user

### File Upload
- Patient Files accepts: PDF, images, documents
- Files are automatically encrypted with AES-256
- Only authorized users can decrypt

### Low Stock Alert
In Pharmacy module, if medication stock ≤ reorder level:
- Red alert box appears automatically
- Lists medicines needing reorder
- Reorder level is customizable

---

## Common Tasks

### Create a Test Patient
1. Login as admin
2. Click "Patients"
3. Click "Add Patient"
4. Fill all fields (name, age, condition, etc.)
5. Click "Save"
6. Use the returned ID for tests/bills

### Upload Encrypted File
1. Click "Patient Files"
2. Select a file from your computer
3. Choose encryption method
4. Click "Upload"
5. File is encrypted and stored in database

### View Patient Records
1. Click "Patients"
2. Search or scroll to find patient
3. Click patient row
4. See all associated data:
   - Appointments
   - Lab tests
   - Vital signs
   - Files

### Schedule Appointment
1. Click "Appointments"
2. Click "Schedule Appointment"
3. Select patient, date, time
4. Add notes
5. Click "Schedule"

---

## Troubleshooting

### "Cannot connect to server"
**Solution:** Ensure backend is running
```powershell
cd Hospital-Backend
npm start
```

### "Page not loading"
**Solution:** Ensure frontend is running
```powershell
cd Hospital-Frontend
npm run dev
```

### "401 Unauthorized"
**Solution:** Token expired or missing
- Logout and login again
- Token auto-refreshes on valid login

### "Database connection error"
**Solution:** Ensure PostgreSQL is running
```powershell
docker ps  # Should show postgres container
```

### "Patient ID not found"
**Solution:** Use valid UUID from patients table
1. Go to Adminer
2. Select patients table
3. Copy valid UUID

---

## API Testing with cURL

### Test Lab Tests Endpoint
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/api/lab-tests
```

### Test Billing Endpoint
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/api/billing
```

### Test Dashboard Endpoint
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3000/api/dashboard/stats
```

**Note:** Replace `YOUR_TOKEN` with actual JWT token from localStorage after login.

---

## System Architecture Overview

```
User Browser
    ↓
Frontend (React + TypeScript)
http://localhost:5173
    ↓
HTTP/REST API Calls
    ↓
Backend Express Server
http://localhost:3000 (30+ endpoints)
    ↓
    ├─→ PostgreSQL Database (Port 5432)
    │   └─→ 11 tables with patient data
    │
    ├─→ Encryption Service
    │   └─→ AES-256-GCM for file encryption
    │
    └─→ IAM Server (Port 4000)
        └─→ JWT + TOTP authentication
```

---

## Next Steps

### To Extend the System
1. **Add Notifications** - Email/SMS alerts
2. **Add Charts** - Revenue trends, appointment graphs
3. **Add Export** - PDF/Excel report generation
4. **Add Real-time** - WebSocket for live updates
5. **Add Mobile** - React Native app

### To Deploy to Production
1. Set up cloud database (AWS RDS, Azure DB)
2. Deploy backend to cloud server (AWS EC2, Heroku)
3. Deploy frontend to CDN (Netlify, Vercel)
4. Configure SSL/TLS certificates
5. Set up monitoring and logging

### To Add Users
1. Login as admin
2. Go to Admin > Provision MFA Secret
3. Enter new user email
4. Get TOTP secret and share securely
5. New user can login with password + MFA code

---

## Support Resources

- **Documentation:** See `.md` files in project root
- **Code Comments:** Inline comments in all components
- **Error Messages:** Check browser console (F12) for detailed errors
- **Logs:** Check terminal output for backend errors
- **Database:** Use Adminer to inspect data

---

## Quick Reference

| Task | Location | Time |
|------|----------|------|
| Order Lab Test | Lab Tests → Order Test | 2 min |
| Upload Results | Lab Tests → Upload | 2 min |
| Create Bill | Billing → Create Bill | 2 min |
| Add Service | Billing → + button | 1 min |
| Process Payment | Billing → Pay button | 1 min |
| Add Medication | Pharmacy → Add Medication | 2 min |
| Fill Prescription | Pharmacy → Prescriptions → Fill | 1 min |
| View Dashboard | Admin Dashboard → Overview | 1 min |
| Check Audit Logs | Admin Dashboard → Audit Logs | 1 min |
| Create Patient | Patients → Add Patient | 3 min |

---

## Success Indicators

✅ Frontend loads at http://localhost:5173
✅ Can login with provided credentials
✅ Navigation menu shows appropriate tabs
✅ Lab Tests tab visible and functional
✅ Billing tab visible and functional
✅ Pharmacy tab visible and functional
✅ Admin Dashboard visible (admin only)
✅ Forms submit and data persists
✅ API calls include authentication
✅ All modals work correctly

---

**System is ready for immediate use!** 🎉

For any issues, refer to the comprehensive testing guide or check backend logs.
