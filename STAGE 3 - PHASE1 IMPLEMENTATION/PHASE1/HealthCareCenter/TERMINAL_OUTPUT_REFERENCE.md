╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║         WHAT YOU'LL SEE - TERMINAL & BROWSER OUTPUT REFERENCE      ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════
BROWSER (http://localhost:5173)
═══════════════════════════════════════════════════════════════════════

INITIAL STATE - File Encryption Component
───────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────┐
│                   Hospital Management Portal                       │
│ ═════════════════════════════════════════════════════════════════  │
│                                                                    │
│  📁 File Encryption & Access Control                              │
│                                                                    │
│  Logged in as: Dr. Sarah Admin (admin@hospital.com)              │
│  Your Permissions: View ✓  Download ✓  Manage ✓                 │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Patient Files                            │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │                                                             │ │
│  │ File Name          Size      Status       Algorithm    Date │ │
│  │ ─────────────────────────────────────────────────────────  │ │
│  │                                                             │ │
│  │ 🔒 Patient1.txt    2.3 KB    Encrypted    AES-256-GCM 11-26 │ │
│  │    [Decrypt]  [Download]  [Delete]                         │ │
│  │                                                             │ │
│  │ 🔒 sample.txt      1.8 KB    Encrypted    AES-256-GCM 11-25 │ │
│  │    [Decrypt]  [Download]  [Delete]                         │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  [+ Upload New File]                                              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

Key things visible:
  ✓ File list with encryption status
  ✓ User permissions displayed
  ✓ Decrypt button available
  ✓ File sizes and upload dates


WHEN USER CLICKS [Decrypt]:
───────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────┐
│                    🔄 Decrypting File...                           │
│                                                                    │
│                    ┌──────────────────┐                           │
│                    │  ⠋ Loading...    │                           │
│                    │  Processing...   │                           │
│                    └──────────────────┘                           │
│                                                                    │
│                  Please wait... (~ 1 second)                      │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

What you see:
  ✓ Modal overlay
  ✓ Loading spinner
  ✓ "Processing..." message
  ✓ File table still visible in background (dimmed)


IF USER HAS MFA ENABLED - Next Step:
───────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────┐
│             🔐 MFA Verification Required                           │
│                                                                    │
│  Your account is protected with Two-Factor Authentication.       │
│                                                                    │
│  Enter the 6-digit code from your authenticator app:             │
│  • Google Authenticator                                          │
│  • Microsoft Authenticator                                       │
│  • Authy                                                         │
│  • Any TOTP-compatible app                                       │
│                                                                    │
│  MFA Code:                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ [______________________________________]               │   │
│  │ (6-digit code will appear here)                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  [Cancel]                                      [Verify Code]      │
│                                                                    │
│  ⏱️  Code expires in: 28 seconds                                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

What user does:
  1. Opens authenticator app
  2. Finds "Hospital Management System" entry
  3. Sees 6-digit code (changes every 30 seconds)
  4. Copies/enters the code
  5. Clicks [Verify Code]

Example codes:
  ✓ Current code: 123456
  ✓ Next code: 456789
  ✓ Each valid for ~30 seconds


AFTER MFA VERIFICATION - SUCCESS:
───────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────┐
│  ✅ File Decrypted Successfully                                    │
│ ═══════════════════════════════════════════════════════════════   │
│                                                                    │
│  📄 File: sample.txt                                              │
│  🔐 Encryption: AES-256-GCM                                       │
│  👤 Decrypted by: Dr. Sarah Admin (Admin)                         │
│  🕐 Decrypted at: 2025-11-28 10:30:00                            │
│  ⚠️  Auto-deletes in: 5 minutes                                   │
│                                                                    │
│  ─────────────────────────────────────────────────────────────    │
│  Content:                                                         │
│  ─────────────────────────────────────────────────────────────    │
│                                                                    │
│  Hello Harini! This is a full integration test.                  │
│                                                                    │
│  ─────────────────────────────────────────────────────────────    │
│                                                                    │
│  [Copy to Clipboard]  [Download as .txt]  [Close]               │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

What you see:
  ✓ Success message with checkmark
  ✓ File metadata (name, algorithm, decrypted by, timestamp)
  ✓ Auto-delete warning (5 minutes)
  ✓ Actual decrypted content
  ✓ Action buttons (Copy, Download, Close)


ERROR SCENARIOS - Wrong MFA Code:
───────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────┐
│  ❌ Decryption Failed                                              │
│                                                                    │
│  Error: Invalid MFA token - MFA verification failed              │
│                                                                    │
│  Please try again with the correct code.                          │
│                                                                    │
│  [Try Again]  [Cancel]                                           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘


ERROR - Permission Denied:
───────────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────────┐
│  ❌ Access Denied                                                  │
│                                                                    │
│  Error: User does not have permission to decrypt files            │
│                                                                    │
│  Your role (Receptionist) does not have the required              │
│  permissions to decrypt patient files.                            │
│                                                                    │
│  Contact your administrator for access.                           │
│                                                                    │
│  [Close]                                                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
BACKEND TERMINAL (port 3000) - npm start
═══════════════════════════════════════════════════════════════════════

NORMAL STARTUP:
───────────────────────────────────────────────────────────────────────

$ npm start

> hospital-backend@1.0.0 start
> node src/index.js

✓ Hospital Backend listening on http://localhost:3000
  Environment: development
  Database: localhost:5432/hospital_db
  ✓ Encryption service loaded


WHEN USER CLICKS DECRYPT:
───────────────────────────────────────────────────────────────────────

POST /api/files/decrypt - From: 127.0.0.1:54321
[JWT] Validating authorization header...
✓ JWT is valid
✓ User ID: 1
✓ Token expires in: 14m 32s
[Encryption Service] Calling decryptFileWithIAM()...
[IAM Integration] Verifying user access...
[IAM] Calling /api/me (port 4000)...
✓ User verified: Dr. Sarah Admin (admin)
✓ MFA Enabled: true
[IAM] User has MFA enabled - MFA token required
Response: 401 Unauthorized
{
  "success": false,
  "error": "MFA token required - user has MFA enabled"
}


WHEN USER SUBMITS MFA CODE:
───────────────────────────────────────────────────────────────────────

POST /api/files/decrypt (with MFA) - From: 127.0.0.1:54322
[JWT] Validating authorization header...
✓ JWT is valid
[Encryption Service] Calling decryptFileWithIAM()...
[IAM Integration] Verifying user access...
[IAM] Calling /api/me (port 4000)...
✓ User verified: Dr. Sarah Admin
✓ MFA Enabled: true
[MFA] Verifying MFA token: 123456
[IAM] Calling /api/mfa/verify (port 4000)...
✓ MFA verified successfully
✓ User authorized
[Permissions] Checking user permissions...
✓ User has 'canViewPatients' permission
[KMS] Getting DEK for file: sample.txt
✓ DEK found (32 bytes)
[Encryption] Decrypting file with AES-256-GCM...
  Input:  storage/encrypted/sample.txt.enc
  Output: storage/temp/sample.txt.temp
  IV: a7f3b9c2e1d4f6a8b5c2d9e1f6a3b8c5
  Tag verified: ✓ (authenticated encryption)
✓ Decryption successful (47 bytes)
[Storage] Temp file created: storage/temp/sample.txt.temp
[Cleanup] Auto-delete scheduled in 5 minutes
[AUDIT] DECRYPT_SUCCESS
  User: 1 (Dr. Sarah Admin)
  File: sample.txt
  Timestamp: 2025-11-28T10:30:00Z
  Size: 47 bytes
✓ Response sent: 200 OK


═══════════════════════════════════════════════════════════════════════
IAM SERVICE TERMINAL (port 4000) - node index.js
═══════════════════════════════════════════════════════════════════════

NORMAL STARTUP:
───────────────────────────────────────────────────────────────────────

$ node index.js

Backend listening on http://localhost:4000
✓ Rate limiter initialized (5 attempts per 15 minutes)
✓ JWT verification ready


WHEN BACKEND CALLS /api/me:
───────────────────────────────────────────────────────────────────────

GET /api/me - From: localhost:3000
Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
[JWT] Decoding JWT...
✓ JWT signature valid
✓ User ID: 1
✓ Token not expired (14m 32s remaining)
[User Lookup] Finding user with ID: 1
✓ User found in database
  Name: Dr. Sarah Admin
  Email: admin@hospital.com
  Role: admin
✓ Loaded user permissions:
  - canViewPatients
  - canEditPatients
  - canDeletePatients
  - canViewAppointments
  - canManageAppointments
  - canViewRecords
  - canEditRecords
  - canManageUsers
  - canViewReports
  - canAccessSettings
✓ MFA Status: enabled
✓ MFA Secret: JBSWY3DPEHPK3PXP
Response: 200 OK


WHEN BACKEND CALLS /api/mfa/verify:
───────────────────────────────────────────────────────────────────────

POST /api/mfa/verify - From: localhost:3000
Body: { "userId": "1", "mfaToken": "123456" }
[Rate Limit] Checking rate limiter for user 1
✓ User has 1 attempts (limit: 5 per 15 minutes)
[MFA] Looking up user: 1
✓ User found
✓ MFA enabled: true
[TOTP] Generating TOTP code...
  Secret: JBSWY3DPEHPK3PXP
  Algorithm: SHA1
  Digits: 6
  Time window: 30 seconds
  Current time: 2025-11-28T10:30:00Z
✓ Generated TOTP: 123456
[TOTP] Comparing codes...
  Expected: 123456
  Received: 123456
✓ MATCH! Code is valid ✓
✓ Time window verified
Response: 200 OK
{
  "success": true,
  "message": "MFA verified successfully",
  "verified": true
}


═══════════════════════════════════════════════════════════════════════
FRONTEND TERMINAL (port 5173) - npm run dev
═══════════════════════════════════════════════════════════════════════

STARTUP:
───────────────────────────────────────────────────────────────────────

$ npm run dev

> hospital-portal-demo@1.0.0 dev
> vite

  VITE v5.4.21  ready in 450 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help


WHEN COMPONENT MOUNTS:
───────────────────────────────────────────────────────────────────────

[HMR] connected
FileEncryption component mounted
✓ Files loaded from state (2 files)
✓ User permissions checked
✓ Access control initialized


WHEN USER CLICKS DECRYPT:
───────────────────────────────────────────────────────────────────────

[FileEncryption] Decrypt initiated for: sample.txt
✓ Permission check passed
✓ Modal opened
✓ Loading spinner shown
[API] JWT token found in localStorage
[API] Sending POST /api/files/decrypt
[API] Payload: { fileId: "sample.txt" }


IF MFA REQUIRED:
───────────────────────────────────────────────────────────────────────

[API] Response status: 401
[API] Error detected: "MFA token required - user has MFA enabled"
[UI] MFA prompt displayed
[UI] User input required


WHEN USER ENTERS MFA:
───────────────────────────────────────────────────────────────────────

[MFA] User entered code: 123456
[MFA] Retrying API call with MFA token
[API] Sending POST /api/files/decrypt (retry)
[API] Payload: { fileId: "sample.txt", mfaToken: "123456" }


ON SUCCESS:
───────────────────────────────────────────────────────────────────────

[API] Response status: 200
[API] Decryption successful!
✓ Content received (47 bytes)
[UI] Modal updated with content
✓ File metadata displayed
✓ Decrypted content rendered
[Timer] Auto-delete timer started (5 minutes)


═══════════════════════════════════════════════════════════════════════
BROWSER CONSOLE (Press F12 to Open)
═══════════════════════════════════════════════════════════════════════

Console output while decrypting:

FileEncryption.tsx:82 Decryption initiated
FileEncryption.tsx:85 JWT token found
FileEncryption.tsx:89 Sending API request...
POST /api/files/decrypt 401 (Unauthorized)
FileEncryption.tsx:95 Response status: 401
FileEncryption.tsx:98 MFA required - showing prompt
FileEncryption.tsx:112 User entered MFA: 123456
FileEncryption.tsx:115 Retrying with MFA token
POST /api/files/decrypt 200 (OK)
FileEncryption.tsx:122 Decryption successful!
FileEncryption.tsx:125 Content: "Hello Harini! This is a full integration test."
FileEncryption.tsx:128 Updating modal...


═══════════════════════════════════════════════════════════════════════
QUICK REFERENCE - What Output Appears Where
═══════════════════════════════════════════════════════════════════════

BROWSER (http://localhost:5173):
  ✓ Loading spinner during processing
  ✓ MFA prompt (if MFA enabled)
  ✓ Success modal with decrypted content
  ✓ Error messages
  ✓ File list with encryption status
  ✓ User permissions displayed

BACKEND TERMINAL (port 3000):
  ✓ JWT validation logs
  ✓ Encryption service logs
  ✓ KMS operations logs
  ✓ Decryption progress logs
  ✓ Audit logs
  ✓ HTTP response status
  ✓ Auto-delete scheduling
  ✓ Any errors/warnings

IAM TERMINAL (port 4000):
  ✓ JWT verification logs
  ✓ User lookup logs
  ✓ Permissions check logs
  ✓ MFA verification logs
  ✓ TOTP code generation/matching logs
  ✓ Rate limiting info
  ✓ HTTP response status
  ✓ Any errors/warnings

FRONTEND TERMINAL (port 5173):
  ✓ Component lifecycle logs
  ✓ API call logs
  ✓ State update logs
  ✓ Error logs
  ✓ Vite HMR logs
  ✓ Any React warnings

BROWSER CONSOLE (F12):
  ✓ All API requests/responses
  ✓ JavaScript errors
  ✓ Component logs
  ✓ Network timing
  ✓ Any console.log statements

═══════════════════════════════════════════════════════════════════════
TIMING - From Click to Display

T=0ms    ← User clicks [Decrypt]
T=100ms  ← Frontend sends API request
T=200ms  ← Backend receives request, validates JWT
T=250ms  ← IAM returns user info (MFA required)
T=300ms  ← Backend responds 401 (MFA needed)
T=350ms  ← Frontend shows MFA prompt
T=500ms  ← User enters code
T=550ms  ← Frontend retries with MFA
T=600ms  ← Backend receives MFA, calls IAM
T=650ms  ← IAM verifies TOTP, responds success
T=700ms  ← Backend decrypts file
T=900ms  ← Backend sends response
T=950ms  ← Frontend updates modal
T=1000ms ← User sees content!

Total time: ~1 second

═══════════════════════════════════════════════════════════════════════
