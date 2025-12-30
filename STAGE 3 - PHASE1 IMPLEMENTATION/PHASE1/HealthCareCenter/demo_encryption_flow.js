#!/usr/bin/env node

/**
 * INTERACTIVE DEMO - File Encryption Flow
 * 
 * Shows exactly what happens when user clicks "Decrypt" in frontend
 */

const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function log(color, text) {
  const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    dim: '\x1b[2m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
    white: '\x1b[37m'
  };
  console.log(colors[color] + text + colors.reset);
}

function divider(title) {
  console.log('\n' + '═'.repeat(70));
  if (title) log('cyan', `  ${title}`);
  console.log('═'.repeat(70) + '\n');
}

async function showBrowserUI() {
  divider('BROWSER - File Encryption Component');
  
  log('white', `
  ┌────────────────────────────────────────────────────────────┐
  │               File Encryption Dashboard                    │
  │                                                            │
  │  Logged in as: admin@hospital.com (Admin)                 │
  │                                                            │
  │  ┌─ Uploaded Files ────────────────────────────────────┐ │
  │  │                                                    │ │
  │  │  File Name       Size    Status      Algorithm    │ │
  │  │  ────────────────────────────────────────────────   │
  │  │  Patient1.txt    2.3 KB  🔒 Encrypted AES-256-GCM │ │
  │  │  sample.txt      1.8 KB  🔒 Encrypted AES-256-GCM │ │
  │  │                         [Decrypt] [Download]     │ │
  │  └────────────────────────────────────────────────────┘ │
  └────────────────────────────────────────────────────────────┘
  `);
}

async function userClicksDecrypt() {
  divider('STEP 1: User Clicks Decrypt Button');
  
  log('yellow', '  User clicks [Decrypt] on sample.txt\n');
  
  await sleep(500);
  
  log('white', `
  ┌────────────────────────────────────────────────────────────┐
  │              ⏳ Decrypting File...                          │
  │                                                            │
  │              ┌──────────────────┐                         │
  │              │   ⠋ Loading...   │                         │
  │              └──────────────────┘                         │
  │                                                            │
  │              Please wait...                               │
  └────────────────────────────────────────────────────────────┘
  `);
  
  log('cyan', '  ✓ Modal opened');
  log('cyan', '  ✓ Loading spinner shown\n');
}

async function frontendGetsToken() {
  divider('STEP 2: Frontend Gets JWT Token');
  
  log('blue', '  Frontend Code:');
  log('white', `    const token = localStorage.getItem('authToken')`);
  
  await sleep(1000);
  
  log('green', '\n  ✓ Token retrieved');
  log('green', '  ✓ Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\n');
}

async function frontendSendsRequest() {
  divider('STEP 3: Frontend Sends Request to Backend');
  
  log('blue', '  Frontend Code:');
  log('white', `
    await fetch('/api/files/decrypt', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer eyJhbGci...',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fileId: 'sample.txt'
      })
    })`);
  
  await sleep(1500);
  
  log('green', '\n  ✓ POST /api/files/decrypt sent');
  log('green', '  ✓ JWT token included');
  log('green', '  ✓ File ID: sample.txt\n');
}

async function backendProcessing() {
  divider('STEP 4: Backend Processing (port 3000)');
  
  log('yellow', '  ▶ Backend received request\n');
  
  await sleep(500);
  log('cyan', '  📝 Backend Terminal Output:');
  log('white', `
    POST /api/files/decrypt - From: 127.0.0.1
    [JWT] Validating token...
    ✓ JWT is valid
    ✓ User ID: 1 (Dr. Sarah Admin)
    [Encryption Service] Calling decryptFileWithIAM()...
  `);
  
  await sleep(1000);
}

async function iamVerification() {
  divider('STEP 5: IAM Service Verification (port 4000)');
  
  log('yellow', '  ▶ Backend calls IAM to verify user\n');
  
  await sleep(500);
  log('cyan', '  📝 IAM Terminal Output:');
  log('white', `
    GET /api/me
    Header: Authorization: Bearer eyJhbGci...
    [JWT] Verifying token...
    ✓ Token is valid
    [User Lookup] Finding user...
    ✓ User found: Dr. Sarah Admin
    ✓ Role: admin
    ✓ MFA Enabled: true
    ✓ Permissions: canViewPatients, canEditPatients, ...
  `);
  
  await sleep(1000);
  
  log('yellow', '\n  ▶ IAM detects MFA is enabled\n');
  
  await sleep(500);
  log('cyan', '  📝 IAM Response:');
  log('white', `
    {
      "id": "1",
      "name": "Dr. Sarah Admin",
      "role": "admin",
      "mfaEnabled": true,
      "permissions": [...]
    }
  `);
  
  await sleep(1000);
}

async function backendRequestsMFA() {
  divider('STEP 6: Backend Detects MFA Required');
  
  log('cyan', '  📝 Backend Terminal:');
  log('white', `
    [IAM Response] MFA is enabled
    ✗ MFA token not provided
    ⚠ Requesting MFA verification from client
    Response: 401 Unauthorized
    {
      "success": false,
      "error": "MFA token required - user has MFA enabled"
    }
  `);
  
  await sleep(1000);
}

async function frontendShowsMFAPrompt() {
  divider('STEP 7: Frontend Shows MFA Prompt');
  
  log('yellow', '  ▶ Frontend received 401 with MFA error\n');
  
  await sleep(500);
  
  log('white', `
  ┌──────────────────────────────────────────────────────────┐
  │             MFA Verification Required                    │
  │                                                          │
  │  Your account has Two-Factor Authentication enabled.    │
  │  Please enter the 6-digit code from your authenticator  │
  │  app (Google Authenticator, Authy, etc.)               │
  │                                                          │
  │  Enter MFA Code:                                        │
  │  ┌────────────────────────────────────────────────────┐ │
  │  │ [______________________________________]          │ │
  │  └────────────────────────────────────────────────────┘ │
  │                                                          │
  │  [Cancel]                              [Verify]        │
  └──────────────────────────────────────────────────────────┘
  `);
  
  log('cyan', '\n  ✓ MFA prompt displayed to user\n');
}

async function userEntersMFA() {
  divider('STEP 8: User Enters MFA Code');
  
  log('yellow', '  ▶ User opens authenticator app\n');
  
  await sleep(1000);
  
  log('white', `
  Authenticator App Screen:
  ┌─────────────────────────────┐
  │  Hospital Management System │
  │                             │
  │  Your MFA Code:             │
  │                             │
  │      123456                 │
  │                             │
  │  Expires in: 28 seconds     │
  └─────────────────────────────┘
  `);
  
  await sleep(1500);
  
  log('cyan', '  ✓ User sees code: 123456');
  log('cyan', '  ✓ User enters code\n');
}

async function frontendRetriesWithMFA() {
  divider('STEP 9: Frontend Retries With MFA Token');
  
  log('blue', '  Frontend Code:');
  log('white', `
    await fetch('/api/files/decrypt', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer eyJhbGci...',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        fileId: 'sample.txt',
        mfaToken: '123456'
      })
    })`);
  
  await sleep(1500);
  
  log('green', '\n  ✓ Retrying with MFA token');
  log('green', '  ✓ MFA Code: 123456\n');
}

async function backendVerifiesMFA() {
  divider('STEP 10: Backend Calls IAM to Verify MFA');
  
  log('cyan', '  📝 Backend Terminal:');
  log('white', `
    [MFA Verification] Calling IAM...
  `);
  
  await sleep(800);
  
  log('cyan', '  📝 IAM Terminal:');
  log('white', `
    POST /api/mfa/verify
    Body: { "userId": "1", "mfaToken": "123456" }
    [TOTP] Generating code for current time...
    ✓ Expected code: 123456
    ✓ User provided: 123456
    ✓ MATCH! ✓
    Response: { "success": true, "verified": true }
  `);
  
  await sleep(1000);
}

async function backendDecryptsFile() {
  divider('STEP 11: Backend Decrypts File');
  
  log('cyan', '  📝 Backend Terminal:');
  log('white', `
    [MFA] ✓ Verified successfully
    [Permissions] Checking user permissions...
    ✓ User has 'canViewPatients' permission
    [KMS] Getting Data Encryption Key...
    ✓ DEK found (32 bytes)
    [AES-256-GCM] Decrypting file...
      Input: storage/encrypted/sample.txt.enc
      Output: storage/temp/sample.txt.temp
    ✓ Decryption successful
    ✓ Plaintext size: 47 bytes
    ✓ Temp file created
    ⏰ Auto-delete scheduled: 5 minutes
    [AUDIT] DECRYPT_SUCCESS user=1 file=sample.txt
  `);
  
  await sleep(1500);
}

async function backendRespondsWithContent() {
  divider('STEP 12: Backend Returns Decrypted Content');
  
  log('cyan', '  📝 Backend Response (200 OK):');
  log('white', `
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
  `);
  
  await sleep(1500);
}

async function frontendDisplaysContent() {
  divider('STEP 13: Frontend Displays Content');
  
  log('yellow', '  ▶ Frontend received decrypted content\n');
  
  await sleep(500);
  
  log('white', `
  ┌──────────────────────────────────────────────────────────┐
  │  ✓ Decrypted: sample.txt                                 │
  │  ──────────────────────────────────────────────────────  │
  │                                                          │
  │  File: sample.txt                                        │
  │  Encryption: AES-256-GCM                                 │
  │  Decrypted by: Dr. Sarah Admin (Admin)                  │
  │  Decrypted at: 2025-11-28 10:30:00                      │
  │  Auto-deletes in: 5 minutes                             │
  │                                                          │
  │  ──────────────────────────────────────────────────────  │
  │  Content:                                                │
  │  ──────────────────────────────────────────────────────  │
  │                                                          │
  │  Hello Harini! This is a full integration test.         │
  │                                                          │
  │  ──────────────────────────────────────────────────────  │
  │                                                          │
  │  [Copy to Clipboard]  [Download]  [Close]              │
  │                                                          │
  └──────────────────────────────────────────────────────────┘
  `);
  
  log('cyan', '\n  ✓ Modal updated with content');
  log('cyan', '  ✓ User can see decrypted file');
  log('cyan', '  ✓ Auto-delete timer started\n');
}

async function summary() {
  divider('COMPLETE FLOW SUMMARY');
  
  log('white', `
  What Happened:
  
  1. ✓ User clicked [Decrypt] in browser
  2. ✓ Frontend got JWT token from storage
  3. ✓ Frontend sent POST to /api/files/decrypt
  4. ✓ Backend validated JWT
  5. ✓ Backend called IAM service (/api/me)
  6. ✓ IAM verified user and detected MFA enabled
  7. ✓ Backend responded: MFA required (401)
  8. ✓ Frontend showed MFA prompt to user
  9. ✓ User entered 6-digit code from authenticator app
  10. ✓ Frontend retried with MFA token
  11. ✓ Backend called IAM to verify MFA code
  12. ✓ IAM verified TOTP code
  13. ✓ Backend got DEK from KMS
  14. ✓ Backend decrypted file using AES-256-GCM
  15. ✓ Backend created temp file (auto-deletes in 5 min)
  16. ✓ Backend returned decrypted content
  17. ✓ Frontend displayed content in modal
  18. ✓ User can view/copy/download content
  
  Time taken: ~1 second (from click to display)
  
  Terminal Output Visible:
  - Backend (port 3000): ✓ All operations logged
  - IAM (port 4000): ✓ JWT and MFA verification logged
  - Frontend (port 5173): ✓ Component updates logged
  - Browser Console (F12): ✓ Request/response logged
  `);
  
  await sleep(1000);
}

async function showTerminalExample() {
  divider('EXAMPLE: What You See in Terminals During Decryption');
  
  log('cyan', '╔════════════════════════════════════════════════════════════╗');
  log('cyan', '║         BACKEND TERMINAL (port 3000) - npm start           ║');
  log('cyan', '╚════════════════════════════════════════════════════════════╝\n');
  
  log('white', `$ npm start

> hospital-backend@1.0.0 start
> node src/index.js

✓ Hospital Backend listening on http://localhost:3000

[USER CLICKS DECRYPT]

POST /api/files/decrypt - From: 127.0.0.1:54321
[JWT] Validating token...
✓ JWT is valid
✓ User ID: 1 (Dr. Sarah Admin)
[Encryption Service] Calling decryptFileWithIAM()
[DECRYPT] Decrypting file for authorized user: 1 (Dr. Sarah Admin)
  Encrypted file: storage/encrypted/sample.txt.enc
  Metadata file: storage/metadata/sample.txt.meta.json
  Temp file: storage/temp/sample.txt.temp
[KMS] Getting DEK for file: sample.txt
✓ DEK found (32 bytes)
[AES-256-GCM] Decrypting file...
  IV: a7f3b9c2e1d4f6a8b5c2d9e1f6a3b8c5
✓ Decryption successful (47 bytes)
✓ Temporary file created
⏰ Auto-delete scheduled in 5 minutes
[AUDIT] DECRYPT_SUCCESS user=1 file=sample.txt timestamp=2025-11-28T10:30:00Z
✓ Response: 200 OK - Content sent to frontend
`);
  
  await sleep(2000);
  
  log('cyan', '\n╔════════════════════════════════════════════════════════════╗');
  log('cyan', '║         IAM TERMINAL (port 4000) - node index.js           ║');
  log('cyan', '╚════════════════════════════════════════════════════════════╝\n');
  
  log('white', `$ node index.js

Backend listening on http://localhost:4000

[USER ENTERS MFA STEP]

GET /api/me
Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
[JWT] Verifying token...
✓ JWT is valid (expires in 14m 32s)
[User] Looking up user...
✓ User found: Dr. Sarah Admin
✓ Role: admin
✓ MFA Enabled: true
✓ Permissions: canViewPatients, canEditPatients, canDeletePatients, ...
Response: 200 OK

POST /api/mfa/verify
Body: { userId: "1", mfaToken: "123456" }
[TOTP] Generating code for current time window...
✓ Generated: 123456
✓ User provided: 123456
✓ MATCH! ✓
[Rate Limit] User has 1 attempt (limit: 5 per 15 min)
Response: 200 OK { success: true, verified: true }
`);
  
  await sleep(2000);
}

async function run() {
  console.clear();
  
  log('bright', '\n╔════════════════════════════════════════════════════════════════════╗');
  log('bright', '║                                                                    ║');
  log('bright', '║       FILE ENCRYPTION INTEGRATION - INTERACTIVE DEMO               ║');
  log('bright', '║                                                                    ║');
  log('bright', '║           Shows exactly what happens when user decrypts a file     ║');
  log('bright', '║                                                                    ║');
  log('bright', '╚════════════════════════════════════════════════════════════════════╝\n');
  
  await sleep(1000);
  
  await showBrowserUI();
  
  rl.question('Press ENTER to start the demo...', async (answer) => {
    await userClicksDecrypt();
    await sleep(1500);
    
    await frontendGetsToken();
    await sleep(1500);
    
    await frontendSendsRequest();
    await sleep(1500);
    
    await backendProcessing();
    await sleep(1500);
    
    await iamVerification();
    await sleep(1500);
    
    await backendRequestsMFA();
    await sleep(1500);
    
    await frontendShowsMFAPrompt();
    await sleep(1500);
    
    await userEntersMFA();
    await sleep(1500);
    
    await frontendRetriesWithMFA();
    await sleep(1500);
    
    await backendVerifiesMFA();
    await sleep(1500);
    
    await backendDecryptsFile();
    await sleep(1500);
    
    await backendRespondsWithContent();
    await sleep(1500);
    
    await frontendDisplaysContent();
    await sleep(1500);
    
    await summary();
    await sleep(1500);
    
    await showTerminalExample();
    
    divider('DEMO COMPLETE');
    
    log('green', '  ✓ You now understand the complete flow!');
    log('green', '  ✓ All 3 terminals output logs you can see\n');
    
    rl.close();
  });
}

run();
