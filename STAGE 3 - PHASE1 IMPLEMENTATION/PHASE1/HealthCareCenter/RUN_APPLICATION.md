╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║              🚀 HOW TO RUN THE COMPLETE APPLICATION               ║
║                                                                    ║
║                      Hospital Management System                   ║
║                    with File Encryption + IAM + MFA               ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════
PREREQUISITES - BEFORE YOU START
═══════════════════════════════════════════════════════════════════════

✅ Check you have:
   □ Node.js installed (v14+)
   □ Docker installed (for PostgreSQL database)
   □ Git (optional, but recommended)
   □ 5 terminal windows/tabs ready (or use VS Code)

✅ Check dependencies installed:
   cd Hospital-Backend && npm install
   cd Hospital-Frontend && npm install
   cd Hospital-Frontend/server && npm install
   cd Encryption && npm install

✅ Verify database is running:
   docker-compose up -d
   → PostgreSQL should be running on port 5432
   → Adminer should be accessible at http://localhost:8080

═══════════════════════════════════════════════════════════════════════
QUICK START - 3 EASY STEPS
═══════════════════════════════════════════════════════════════════════

If you're in a hurry, just do this:

STEP 1: Start PostgreSQL Database
─────────────────────────────────────────────────────────────────────

Open a terminal and run:

  cd HealthCareCenter
  docker-compose up -d

You should see:
  Creating postgresql_db ... done
  Creating adminer_ui ... done

✓ Database is now running!


STEP 2: Start All 3 Servers (Open 3 New Terminals)
─────────────────────────────────────────────────────────────────────

Terminal 1 - Backend API (port 3000):

  cd Hospital-Backend
  npm start

Expected output:
  ✓ Hospital Backend listening on http://localhost:3000
  ✓ Environment: development
  ✓ Database: connected
  ✓ Encryption service loaded


Terminal 2 - IAM Service (port 4000):

  cd Hospital-Frontend/server
  node index.js

Expected output:
  Backend listening on http://localhost:4000
  ✓ JWT verification ready
  ✓ Rate limiter initialized


Terminal 3 - Frontend/Portal (port 5173):

  cd Hospital-Frontend
  npm run dev

Expected output:
  VITE v5.4.21 ready in 450 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose


STEP 3: Open Browser & Login
─────────────────────────────────────────────────────────────────────

1. Open: http://localhost:5173

2. Login with:
   Email: admin@hospital.com
   Password: Admin@123
   MFA Code: (if enabled - use authenticator app with secret: JBSWY3DPEHPK3PXP)

3. Click around and test:
   ✓ Patient CRUD (add, view, edit, delete)
   ✓ Appointments (schedule, reschedule, cancel)
   ✓ File Encryption (decrypt files)
   ✓ User Settings

✓ You're done! Application is running!


═══════════════════════════════════════════════════════════════════════
DETAILED STEP-BY-STEP GUIDE
═══════════════════════════════════════════════════════════════════════

PART 1: PREPARE DATABASE
─────────────────────────────────────────────────────────────────────

Command:
  cd c:\Harini\S7\Final Year Project\HealthCareCenter
  docker-compose up -d

What happens:
  ✓ Pulls PostgreSQL 14 image (if not already downloaded)
  ✓ Starts PostgreSQL container on port 5432
  ✓ Starts Adminer UI on port 8080
  ✓ Creates hospital_db database
  ✓ Mounts data volume (persists between restarts)

How to verify:
  docker-compose ps
  
Expected:
  NAME                COMMAND                  SERVICE        STATUS
  postgresql_db       docker-entrypoint.s...   postgresql     Up 2 minutes
  adminer_ui          entrypoint.sh apache2    adminer        Up 2 minutes

Access database UI:
  Open: http://localhost:8080
  System: PostgreSQL
  Server: postgresql_db
  Username: hospital
  Password: F1UFDk8H36Ry2RITAvnErulW
  Database: hospital_db


PART 2: START BACKEND API SERVER
─────────────────────────────────────────────────────────────────────

Open Terminal 1:

Commands:
  cd c:\Harini\S7\Final Year Project\HealthCareCenter\Hospital-Backend
  npm start

What happens:
  ✓ Starts Express.js server
  ✓ Loads environment variables from .env
  ✓ Connects to PostgreSQL database
  ✓ Initializes encryption service
  ✓ Sets up all API routes
  ✓ Listens on port 3000

Expected output:
  
  > hospital-backend@1.0.0 start
  > node src/index.js
  
  ✓ Hospital Backend listening on http://localhost:3000
    Environment: development
    Database: localhost:5432/hospital_db
    ✓ Encryption service loaded
  
  ✓ Ready to receive requests!

Keep this terminal OPEN - don't close it!


PART 3: START IAM SERVICE SERVER
─────────────────────────────────────────────────────────────────────

Open Terminal 2:

Commands:
  cd c:\Harini\S7\Final Year Project\HealthCareCenter\Hospital-Frontend\server
  node index.js

What happens:
  ✓ Starts Express.js server for IAM
  ✓ Loads user credentials from users.json
  ✓ Sets up JWT token generation
  ✓ Sets up MFA verification (TOTP)
  ✓ Listens on port 4000

Expected output:

  Backend listening on http://localhost:4000
  ✓ JWT verification ready
  ✓ Rate limiter initialized (5 attempts per 15 minutes)
  
  ✓ Ready to handle authentication!

Keep this terminal OPEN - don't close it!


PART 4: START FRONTEND DEVELOPMENT SERVER
─────────────────────────────────────────────────────────────────────

Open Terminal 3:

Commands:
  cd c:\Harini\S7\Final Year Project\HealthCareCenter\Hospital-Frontend
  npm run dev

What happens:
  ✓ Starts Vite dev server
  ✓ Sets up proxy to backend (port 3000)
  ✓ Enables hot module replacement (HMR)
  ✓ Listens on port 5173

Expected output:

  > hospital-portal-demo@1.0.0 dev
  > vite
  
  The CJS build of Vite's Node API is deprecated...
  
    VITE v5.4.21  ready in 450 ms
  
    ➜  Local:   http://localhost:5173/
    ➜  Network: use --host to expose
    ➜  press h + enter to show help

Keep this terminal OPEN - don't close it!


PART 5: LOGIN TO PORTAL
─────────────────────────────────────────────────────────────────────

Browser:

1. Open: http://localhost:5173

   You should see the login page

2. Enter credentials:

   Email: admin@hospital.com
   Password: Admin@123

3. Click Login

   What happens:
   ✓ Frontend sends POST /api/login to backend (port 3000)
   ✓ Backend validates password (bcrypt)
   ✓ Backend sends to IAM for token generation
   ✓ IAM generates JWT token
   ✓ Frontend stores token in localStorage
   ✓ You're logged in!

4. If MFA is enabled (it is by default):

   A modal appears asking for MFA code
   
   Open authenticator app and find:
   Account: Hospital Management System (admin)
   Secret: JBSWY3DPEHPK3PXP
   Current code: 123456 (changes every 30 seconds)
   
   Enter the 6-digit code
   Click Verify
   
   What happens:
   ✓ Frontend sends MFA code to IAM (port 4000)
   ✓ IAM verifies TOTP code
   ✓ IAM confirms authentication
   ✓ Portal fully loads

5. After login:

   You should see the dashboard with:
   ✓ Patient Management section
   ✓ Appointments section
   ✓ File Encryption section
   ✓ User Profile
   ✓ Settings

✓ You're now logged in and ready to use the system!


PART 6: TEST FEATURES
─────────────────────────────────────────────────────────────────────

In the portal, you can test:

A. Patient Management:
   - Click "Add Patient" button
   - Fill in form (name, DOB, contact, insurance)
   - Click "Create Patient"
   - See new patient in list
   - Click on patient to edit
   - Click delete to remove

B. Appointments:
   - Click "Appointments" section
   - Click "Schedule Appointment"
   - Select patient, doctor, date/time
   - Click "Schedule"
   - See appointment in list
   - Click "Reschedule" to change time
   - Click "Cancel" to delete

C. File Encryption:
   - Go to "File Encryption" section
   - See list of encrypted files
   - Click "Decrypt" on a file
   - If MFA enabled: enter MFA code
   - See decrypted content
   - Click Copy/Download/Close

D. User Profile:
   - Click profile icon (top right)
   - View your user info
   - See your role and permissions


═══════════════════════════════════════════════════════════════════════
WHAT YOU'LL SEE IN EACH TERMINAL
═══════════════════════════════════════════════════════════════════════

BACKEND TERMINAL (port 3000) - When user logs in:

POST /api/login - From: 127.0.0.1:xxxxx
[JWT] Generating token for user: 1
✓ Token generated (expires in 15 minutes)
Response: 200 OK

POST /api/patients - From: 127.0.0.1:xxxxx
[JWT] Validating token...
✓ Token is valid
[Database] Inserting new patient...
✓ Patient created (ID: 5)
Response: 201 Created

GET /api/appointments
[JWT] Validating token...
✓ Token is valid
[Database] Fetching appointments...
✓ Found 4 appointments
Response: 200 OK


IAM TERMINAL (port 4000) - When user logs in:

GET /api/me
Header: Authorization: Bearer eyJhbGci...
[JWT] Verifying token...
✓ Token is valid
✓ User: Dr. Sarah Admin
Response: 200 OK

POST /api/mfa/verify
Body: { "userId": "1", "mfaToken": "123456" }
[TOTP] Generating code...
✓ Expected: 123456
✓ Received: 123456
✓ MATCH! ✓
Response: 200 OK


FRONTEND TERMINAL (port 5173) - When you navigate:

✓ http://localhost:5173/ resolved to 127.0.0.1 via Vite
FileEncryption component mounted
✓ Files loaded from state
[HMR] connected
POST /api/login (HTTP/1.1 200)
GET /api/patients (HTTP/1.1 200)
✓ Component updated with data


═══════════════════════════════════════════════════════════════════════
TROUBLESHOOTING - COMMON ISSUES
═══════════════════════════════════════════════════════════════════════

ISSUE 1: Port Already in Use
─────────────────────────────────────────────────────────────────────

Error: listen EADDRINUSE: address already in use :::3000

Solution:
  1. Kill existing Node processes:
     Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
  
  2. Wait 5 seconds
  
  3. Start server again:
     npm start

Or check what's using the port:
  Get-NetTCPConnection -State Listen | Where-Object {$_.LocalPort -eq 3000}


ISSUE 2: Database Connection Failed
─────────────────────────────────────────────────────────────────────

Error: Error: connect ECONNREFUSED 127.0.0.1:5432

Solution:
  1. Check PostgreSQL is running:
     docker-compose ps
  
  2. If not running, start it:
     docker-compose up -d
  
  3. Wait 10 seconds for PostgreSQL to start
  
  4. Retry backend server


ISSUE 3: npm Packages Not Installed
─────────────────────────────────────────────────────────────────────

Error: Cannot find module 'express'

Solution:
  1. Run npm install in each directory:
     
     cd Hospital-Backend && npm install
     cd Hospital-Frontend && npm install
     cd Hospital-Frontend/server && npm install
  
  2. If still failing:
     npm cache clean --force
     rm -r node_modules package-lock.json
     npm install


ISSUE 4: MFA Code Not Working
─────────────────────────────────────────────────────────────────────

Error: Invalid MFA token

Solution:
  1. Make sure your authenticator app is synchronized
  
  2. Try entering the next code (they change every 30 seconds)
  
  3. Check the secret is correct: JBSWY3DPEHPK3PXP
  
  4. To disable MFA temporarily:
     Edit Hospital-Frontend/server/users.json
     Change "mfaEnabled": true to "mfaEnabled": false


ISSUE 5: Frontend Can't Connect to Backend
─────────────────────────────────────────────────────────────────────

Error: Failed to fetch from /api/patients

Solution:
  1. Check backend is running:
     Terminal 1 should show: ✓ Hospital Backend listening on http://localhost:3000
  
  2. Check port 3000 is not blocked by firewall
  
  3. Restart frontend server:
     Ctrl+C in Terminal 3
     npm run dev


ISSUE 6: CORS Error
─────────────────────────────────────────────────────────────────────

Error: Access to XMLHttpRequest has been blocked by CORS policy

Solution:
  1. This shouldn't happen with Vite proxy setup
  
  2. Check Hospital-Frontend/vite.config.js has proxy configured
  
  3. Restart frontend:
     Ctrl+C
     npm run dev


═══════════════════════════════════════════════════════════════════════
TESTING CHECKLIST
═══════════════════════════════════════════════════════════════════════

After everything is running, verify each feature:

☐ Login
  - Go to http://localhost:5173
  - Enter: admin@hospital.com / Admin@123
  - Enter MFA code
  - You're logged in ✓

☐ Patient CRUD
  - Click "Add Patient"
  - Fill form and submit
  - See patient in list ✓
  - Click patient to edit
  - Click delete ✓

☐ Appointments
  - See appointment list ✓
  - Click "Schedule" to add ✓
  - Click "Reschedule" to edit ✓
  - Click "Cancel" to delete ✓

☐ File Encryption
  - Click "File Encryption" ✓
  - Click "Decrypt" on a file ✓
  - Enter MFA code if needed ✓
  - See decrypted content ✓

☐ User Profile
  - Click profile icon ✓
  - See user info ✓

☐ Terminals Show Logs
  - Backend (3000): Shows API requests ✓
  - IAM (4000): Shows auth requests ✓
  - Frontend (5173): Shows component logs ✓


═══════════════════════════════════════════════════════════════════════
OTHER USER ACCOUNTS TO TEST
═══════════════════════════════════════════════════════════════════════

Doctor Account:
  Email: doctor@hospital.com
  Password: Doctor@123
  MFA Secret: KRSXG5DSMFZXI2LK
  Permissions: View patients, manage appointments

Nurse Account:
  Email: nurse@hospital.com
  Password: Nurse@123
  MFA Secret: MFXHS4DSNFXWG2LS
  Permissions: View patients, limited appointments

Receptionist Account:
  Email: receptionist@hospital.com
  Password: Reception@123
  MFA Secret: ONSWG4TFOQ======
  Permissions: Manage appointments only


═══════════════════════════════════════════════════════════════════════
USEFUL COMMANDS
═══════════════════════════════════════════════════════════════════════

View Database (Adminer):
  http://localhost:8080
  System: PostgreSQL
  Username: hospital
  Password: F1UFDk8H36Ry2RITAvnErulW

Check Database Status:
  docker-compose ps

View Database Logs:
  docker-compose logs postgresql_db

Stop All Services:
  docker-compose down

Restart Database:
  docker-compose restart

Kill Node Processes:
  Get-Process node | Stop-Process -Force

View Backend Logs:
  Terminal 1 (Backend tab)

View IAM Logs:
  Terminal 2 (IAM tab)

View Frontend Logs:
  Terminal 3 (Frontend tab)

View Browser Console Logs:
  Press F12 in browser, go to Console tab


═══════════════════════════════════════════════════════════════════════
NEXT STEPS AFTER RUNNING
═══════════════════════════════════════════════════════════════════════

1. Run Integration Tests:
   node test_encryption_integration.js

2. View Detailed Documentation:
   - ENCRYPTION_INTEGRATION_GUIDE.md
   - FRONTEND_FLOW_EXPLAINED.md
   - TERMINAL_OUTPUT_REFERENCE.md

3. Test Different User Roles:
   - Login as doctor@hospital.com
   - Login as nurse@hospital.com
   - See different permissions

4. Test Error Scenarios:
   - Enter wrong MFA code
   - Try to access file without permission
   - Edit patient record

5. Monitor Terminals:
   - Watch backend logs
   - Watch IAM logs
   - Watch frontend logs
   - See how everything works together


═══════════════════════════════════════════════════════════════════════
YOU'RE READY TO GO! 🚀
═══════════════════════════════════════════════════════════════════════

Follow these steps in order:

1. ✓ Start Docker: docker-compose up -d
2. ✓ Start Backend (Terminal 1): npm start
3. ✓ Start IAM (Terminal 2): node index.js
4. ✓ Start Frontend (Terminal 3): npm run dev
5. ✓ Open Browser: http://localhost:5173
6. ✓ Login & Enjoy!

All 3 servers will show logs of what they're doing.
The complete Hospital Management System is running!

═══════════════════════════════════════════════════════════════════════
