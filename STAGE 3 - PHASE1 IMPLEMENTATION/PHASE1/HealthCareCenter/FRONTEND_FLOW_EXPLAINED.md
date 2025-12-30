╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║    HOW FILE ENCRYPTION WORKS IN THE FRONTEND & WHAT YOU'LL SEE     ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════
FRONTEND FLOW (What You'll See in Browser)
═══════════════════════════════════════════════════════════════════════

USER INTERFACE:
┌─────────────────────────────────────────────────────────────────────┐
│                      File Encryption Dashboard                      │
│                                                                     │
│  Logged in as: admin@hospital.com (Admin)                          │
│                                                                     │
│  ┌─ Uploaded Files ──────────────────────────────────────────────┐ │
│  │                                                               │ │
│  │  File Name          Size    Status      Algorithm    Date    │ │
│  │  ─────────────────────────────────────────────────────────   │ │
│  │  Patient1.txt       2.3 KB  🔒 Encrypted AES-256-GCM 11-26  │ │
│  │                            [Decrypt] [Download] [Delete]    │ │
│  │                                                               │ │
│  │  sample.txt         1.8 KB  🔒 Encrypted AES-256-GCM 11-25  │ │
│  │                            [Decrypt] [Download] [Delete]    │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  [+ Upload New File]                                               │
└─────────────────────────────────────────────────────────────────────┘


STEP-BY-STEP: USER CLICKS "DECRYPT" BUTTON
─────────────────────────────────────────────────────────────────────

STEP 1: Frontend UI Changes
  
  User clicks: [Decrypt] button on "sample.txt"
  
  What happens immediately:
  ✓ Modal opens with loading spinner
  ✓ Shows: "Decrypting... Please wait"
  ✓ Button becomes disabled

STEP 2: Frontend Gets JWT Token

  JavaScript code:
  ```javascript
  const token = localStorage.getItem('authToken')
  ```
  
  What this means:
  ✓ Frontend retrieves the JWT token saved during login
  ✓ Token looks like: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

STEP 3: Frontend Sends Request to Backend

  JavaScript code:
  ```javascript
  const response = await fetch('/api/files/decrypt', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      fileId: 'sample.txt'
    })
  })
  ```

  What gets sent:
  POST /api/files/decrypt
  Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
  Body: { "fileId": "sample.txt" }

STEP 4: Backend Processes Request

  Backend receives request:
  ✓ Validates JWT (checks if token is valid)
  ✓ Calls encryption service with user info
  ✓ Encryption service verifies with IAM (port 4000)

STEP 5: IAM Service Verifies User

  IAM service (port 4000):
  ✓ Calls /api/me with JWT
  ✓ Returns: { "id": "1", "name": "Dr. Sarah", "role": "admin", "mfaEnabled": true }
  ✓ Checks if MFA enabled → YES
  ✓ Returns: "MFA token required"

STEP 6: Frontend Detects MFA Needed

  Backend responds with 401:
  {
    "success": false,
    "error": "MFA token required - user has MFA enabled"
  }
  
  Frontend code:
  ```javascript
  if (data.error.includes('MFA')) {
    const mfaToken = prompt('Enter your MFA code:')
    // ... retry with MFA token
  }
  ```
  
  What user sees:
  ┌─────────────────────────────────────┐
  │  Enter your MFA code:               │
  │  ┌─────────────────────────────┐   │
  │  │ [XXXXXX________________]    │   │
  │  └─────────────────────────────┘   │
  │  [Cancel]  [OK]                     │
  └─────────────────────────────────────┘

STEP 7: User Enters MFA Code

  User gets OTP from authenticator app:
  ✓ Opens Google Authenticator/Authy
  ✓ Finds "Hospital Management System"
  ✓ Sees 6-digit code: 123456
  ✓ Enters in modal

STEP 8: Frontend Retries with MFA Token

  JavaScript retries:
  ```javascript
  const retryResponse = await fetch('/api/files/decrypt', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      fileId: 'sample.txt',
      mfaToken: '123456'
    })
  })
  ```

STEP 9: Backend + Encryption Service

  Backend receives MFA token:
  ✓ Calls encryption service
  ✓ Calls IAM: verify MFA with token
  ✓ IAM checks TOTP: Valid! ✓
  ✓ Gets user permissions
  ✓ Calls KMS to get DEK (Data Encryption Key)
  ✓ Decrypts file using AES-256-GCM
  ✓ Creates temp file
  ✓ Schedules auto-delete (5 min)

STEP 10: Backend Returns Decrypted Content

  Response from backend:
  {
    "success": true,
    "fileId": "sample.txt",
    "content": "Hello Harini! This is a full integration test.",
    "user": {
      "id": "1",
      "name": "Dr. Sarah Admin",
      "role": "admin"
    },
    "decryptedAt": "2025-11-28T10:30:00Z",
    "autoDeleteIn": "5 minutes"
  }

STEP 11: Frontend Displays Content

  Modal updates:
  ┌─────────────────────────────────────────────────────┐
  │  Decrypted File: sample.txt                         │
  │  ─────────────────────────────────────────────────  │
  │                                                     │
  │  File: sample.txt                                   │
  │  Encryption: AES-256-GCM                            │
  │  Decrypted by: Dr. Sarah Admin                      │
  │  Decrypted at: 2025-11-28 10:30:00                 │
  │                                                     │
  │  ────────────────────────────────────────────────  │
  │  Content:                                           │
  │  ────────────────────────────────────────────────  │
  │                                                     │
  │  Hello Harini! This is a full integration test.    │
  │                                                     │
  │  ────────────────────────────────────────────────  │
  │  Auto-deletes in: 5 minutes                        │
  │                                                     │
  │  [Copy] [Download] [Close]                         │
  └─────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
TERMINAL OUTPUT (What You'll See in Console)
═══════════════════════════════════════════════════════════════════════

BACKEND TERMINAL (port 3000):
─────────────────────────────────────────────────────────────────────

$ npm start

> hospital-backend@1.0.0 start
> node src/index.js

✓ Hospital Backend listening on http://localhost:3000
  Environment: development
  Database: localhost:5432/hospital_db

[Request arrives]
POST /api/files/decrypt - From: 127.0.0.1

[JWT validated]
✓ JWT authenticated

[Calls encryption service]
Calling encryptionService.decryptFileWithIAM()

[Encryption service logs]
[DECRYPT] Decrypting file for authorized user: 1 (Dr. Sarah Admin)
[Storage] File paths:
  Encrypted: storage/encrypted/sample.txt.enc
  Metadata: storage/metadata/sample.txt.meta.json
  Temp: storage/temp/sample.txt.temp

[KMS logs]
KMS: Getting DEK for file: sample.txt
KMS: Found DEK (32 bytes)

[Encryption logs]
[AES-256-GCM] Decrypting...
[AES-256-GCM] IV: a7f3b9c2e1d4f6a8...
[AES-256-GCM] Decryption successful
[AES-256-GCM] Plaintext size: 47 bytes

[Temp file created]
✓ Temporary file created: storage/temp/sample.txt.temp

[Cleanup scheduled]
⏰ Auto-delete scheduled in 5 minutes

[Audit log]
[AUDIT] DECRYPT_SUCCESS user=1 file=sample.txt timestamp=2025-11-28T10:30:00Z

[Response sent]
✓ Response: 200 OK
Response body: {
  "success": true,
  "fileId": "sample.txt",
  "content": "Hello Harini! This is a full integration test.",
  "user": { "id": "1", "name": "Dr. Sarah Admin", "role": "admin" },
  "decryptedAt": "2025-11-28T10:30:00Z",
  "autoDeleteIn": "5 minutes"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


IAM SERVICE TERMINAL (port 4000):
─────────────────────────────────────────────────────────────────────

$ node index.js

Backend listening on http://localhost:4000

[IAM request received]
GET /api/me
Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

[JWT verification]
✓ JWT is valid
✓ User ID: 1
✓ Token expires in: 14m 32s

[User lookup]
User found: Dr. Sarah Admin
Role: admin
MFA Enabled: true
Permissions: canViewPatients, canEditPatients, canDeletePatients, ...

[MFA check]
⚠ MFA is enabled for this user
✓ Returning: mfaEnabled: true

Response: 200 OK
{
  "id": "1",
  "name": "Dr. Sarah Admin",
  "email": "admin@hospital.com",
  "role": "admin",
  "mfaEnabled": true,
  "permissions": ["canViewPatients", "canEditPatients", ...]
}

────────────────────────────────────────────────────────────────────

[MFA verification request]
POST /api/mfa/verify
Body: { "userId": "1", "mfaToken": "123456" }

[TOTP verification]
✓ User secret found: JBSWY3DPEHPK3PXP
✓ Generating TOTP code for current time window
✓ Generated code: 123456
✓ User provided: 123456
✓ MATCH! ✓

[Rate limiting check]
✓ User has not exceeded MFA attempts

Response: 200 OK
{
  "success": true,
  "message": "MFA verified successfully",
  "verified": true
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


FRONTEND TERMINAL (port 5173):
─────────────────────────────────────────────────────────────────────

$ npm run dev

> hospital-portal-demo@1.0.0 dev
> vite

  VITE v5.4.21  ready in 450 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose

[User navigates to File Encryption]
✓ Component mounted
✓ Files loaded from state
✓ User permissions checked: canDownloadFiles = true

[User clicks Decrypt]
[Console] Decryption initiated for: sample.txt
[Console] JWT token found: eyJhbGciOiJIUzI1NiIs...

[First API call]
[Console] Sending request to /api/files/decrypt
[Console] Request body: { fileId: 'sample.txt' }

[Response received - MFA required]
[Console] Response status: 401
[Console] Error: "MFA token required - user has MFA enabled"

[MFA prompt shown]
[Console] MFA prompt displayed to user

[User enters MFA]
[Console] User entered MFA code: 123456

[Second API call - with MFA]
[Console] Retrying with MFA token: 123456

[Success response]
[Console] Decryption successful!
[Console] Content received: "Hello Harini! This is a full integration test."
[Console] Updating modal with decrypted content

[Modal displayed]
[Console] Modal state updated
[Console] Content rendered
[Console] Auto-delete timer set to 5 minutes


═══════════════════════════════════════════════════════════════════════
ERROR SCENARIOS - What You'll See
═══════════════════════════════════════════════════════════════════════

SCENARIO 1: Wrong MFA Code
─────────────────────────────────────────────────────────────────────

User enters: 000000 (wrong code)

IAM Terminal:
  [TOTP verification]
  ✓ User secret found: JBSWY3DPEHPK3PXP
  ✓ Expected code: 123456
  ✓ User provided: 000000
  ✗ NO MATCH! 

  Response: 401
  {
    "success": false,
    "error": "Invalid MFA code"
  }

Frontend Modal:
  ┌─────────────────────────────────┐
  │ ❌ Decryption Failed             │
  │                                 │
  │ Error: Invalid MFA code          │
  │                                 │
  │ [Try Again] [Close]             │
  └─────────────────────────────────┘

Browser Console:
  ❌ Error: Invalid MFA token - MFA verification failed


SCENARIO 2: User Without Permission
─────────────────────────────────────────────────────────────────────

User: receptionist@hospital.com (no canViewPatients permission)

Backend Terminal:
  [User permission check]
  ✗ User lacks required permissions
  ✗ Required: canViewPatients, canViewRecords, or canManageUsers
  ✗ User has: canManageAppointments only

  Response: 403 Forbidden
  {
    "success": false,
    "error": "User does not have permission to decrypt files"
  }

Frontend Modal:
  ┌─────────────────────────────────┐
  │ ❌ Access Denied                 │
  │                                 │
  │ You do not have permission to    │
  │ decrypt files. Contact admin.    │
  │                                 │
  │ [Close]                         │
  └─────────────────────────────────┘


SCENARIO 3: Invalid JWT Token
─────────────────────────────────────────────────────────────────────

Token expired or tampered

Backend Terminal:
  POST /api/files/decrypt
  
  [JWT validation]
  ✗ JWT validation failed
  ✗ Token expired
  
  authenticate middleware:
  ✗ Missing or invalid authorization header
  ✗ Rejecting request
  
  Response: 401 Unauthorized
  {
    "success": false,
    "error": "Invalid JWT token - IAM verification failed"
  }

Frontend:
  [Console] Not authenticated - please log in
  Modal shows: "Authentication failed. Please login again."

User sees prompt to re-login


SCENARIO 4: File Not Found
─────────────────────────────────────────────────────────────────────

Encrypted file missing from storage

Backend Terminal:
  [DECRYPT] File paths:
    Encrypted: storage/encrypted/missing.txt.enc
    Metadata: storage/metadata/missing.txt.meta.json
  
  ✗ File access check
  ✗ File not found: storage/encrypted/missing.txt.enc
  
  Response: 500 Internal Server Error
  {
    "success": false,
    "error": "File not found: missing.txt"
  }

Frontend Modal:
  ┌─────────────────────────────────┐
  │ ❌ Decryption Failed             │
  │                                 │
  │ Error: File not found            │
  │                                 │
  │ [Close]                         │
  └─────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════
COMPLETE TIMING EXAMPLE
═══════════════════════════════════════════════════════════════════════

Timeline:

T=0ms      → User clicks [Decrypt] button
            Frontend: Shows loading spinner in modal

T=50ms     → Frontend sends request to Backend
            Frontend: "Connecting to API..."

T=100ms    → Backend receives request at /api/files/decrypt
            Backend Terminal:
            POST /api/files/decrypt - From: 127.0.0.1
            ✓ JWT authenticated
            Calling encryptionService.decryptFileWithIAM()

T=150ms    → Encryption service calls IAM
            Backend Terminal:
            [Calling IAM service at localhost:4000]

T=200ms    → IAM verifies JWT
            IAM Terminal:
            GET /api/me
            ✓ User verified: Dr. Sarah Admin
            ✓ MFA Enabled: true
            Response: mfaEnabled: true

T=250ms    → Backend gets MFA requirement
            Backend Terminal:
            ✓ User has MFA enabled
            Requesting MFA token from client

T=300ms    → Backend responds to Frontend
            Response: 401, "MFA token required"

T=350ms    → Frontend shows MFA prompt
            Frontend: Modal shows input field
            Browser: Prompt appears

T=500ms    → User enters MFA code: 123456
            User types code and clicks OK

T=550ms    → Frontend retries with MFA token
            Frontend sends: { fileId: "sample.txt", mfaToken: "123456" }

T=600ms    → Backend receives MFA token
            Backend Terminal:
            Retrying with MFA verification

T=650ms    → Backend calls IAM to verify MFA
            IAM Terminal:
            POST /api/mfa/verify
            Body: { userId: "1", mfaToken: "123456" }
            ✓ TOTP verification successful

T=700ms    → IAM responds MFA verified
            IAM Terminal:
            Response: { success: true, verified: true }

T=750ms    → Backend gets DEK from KMS
            Backend Terminal:
            KMS: Getting DEK for file: sample.txt
            ✓ Found DEK (32 bytes)

T=800ms    → Backend decrypts file
            Backend Terminal:
            [AES-256-GCM] Decrypting...
            ✓ Decryption successful (47 bytes)

T=850ms    → Backend creates temp file
            Backend Terminal:
            ✓ Temporary file created
            ⏰ Auto-delete scheduled in 5 minutes

T=900ms    → Backend sends response to Frontend
            Response: 200 OK with decrypted content

T=950ms    → Frontend receives content
            Frontend: Modal displays decrypted text
            Frontend Terminal:
            [Console] Decryption successful!
            [Console] Content: "Hello Harini!..."

T=1000ms   → User sees decrypted content
            Browser: Modal shows full content with [Copy], [Download], [Close]


═══════════════════════════════════════════════════════════════════════
SUMMARY: What Gets Output Where
═══════════════════════════════════════════════════════════════════════

BROWSER (Frontend):
  ✓ Modal with loading spinner
  ✓ MFA prompt (if MFA enabled)
  ✓ Decrypted content displayed
  ✓ Error messages if anything fails
  ✓ Browser console logs (press F12)

BACKEND TERMINAL:
  ✓ Request received logs
  ✓ JWT validation logs
  ✓ Encryption service logs
  ✓ KMS logs
  ✓ Audit logs
  ✓ Response status
  ✓ Any errors

IAM SERVICE TERMINAL:
  ✓ User verification logs
  ✓ JWT validation logs
  ✓ MFA verification logs
  ✓ TOTP code matching logs
  ✓ Permissions check logs
  ✓ Response status
  ✓ Any errors

FRONTEND TERMINAL:
  ✓ Vite dev server logs
  ✓ API request logs
  ✓ Component lifecycle logs
  ✓ Any React errors
  ✓ Browser console output

═══════════════════════════════════════════════════════════════════════
