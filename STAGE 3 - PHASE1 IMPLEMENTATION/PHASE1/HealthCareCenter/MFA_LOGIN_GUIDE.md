# MFA Login Guide ✅

## MFA is NOW ENABLED for 7 Roles

All roles except `patient` require MFA verification during login.

## Login Credentials with MFA Secrets

| Email | Password | Role | MFA Secret | MFA |
|-------|----------|------|-----------|-----|
| admin@hospital.com | Admin@123 | admin | JBSWY3DPEBLW64TMMQ====== | ✅ Yes |
| doctor@hospital.com | Doctor@123 | doctor | JBSWY3DPEBLW64TMMQ====== | ✅ Yes |
| nurse@hospital.com | Nurse@123 | nurse | MFXHS4DSNFXWG2LS | ✅ Yes |
| receptionist@hospital.com | Receptionist@123 | receptionist | ONSWG4TFOQ====== | ✅ Yes |
| labtech@hospital.com | LabTech@123 | lab_technician | PZXXK3DSMFZXI2LO | ✅ Yes |
| pharmacist@hospital.com | Pharmacist@123 | pharmacist | QZXXK3DSMFZWI2LP | ✅ Yes |
| accountant@hospital.com | Accountant@123 | accountant | RZXXK3DSNFZWG2LQ | ✅ Yes |
| patient@hospital.com | Patient@123 | patient | (none) | ❌ No |

## How to Get MFA Codes

### Option 1: Use Authenticator App (Recommended)
1. Install any TOTP authenticator app:
   - Google Authenticator
   - Microsoft Authenticator
   - Authy
   - FreeOTP
   - LastPass Authenticator

2. In the app, scan this QR code or enter the MFA Secret manually

3. The app will generate 6-digit codes that refresh every 30 seconds

### Option 2: Generate Code Programmatically

**Node.js Script:**
```javascript
const speakeasy = require('speakeasy');

const mfaSecret = 'JBSWY3DPEBLW64TMMQ======'; // Use the secret for your role

const code = speakeasy.totp({
  secret: mfaSecret,
  encoding: 'base32',
  window: 2
});

console.log('MFA Code:', code);
```

**Run:** `node -e "const s = require('speakeasy'); console.log(s.totp({secret: 'JBSWY3DPEBLW64TMMQ======', encoding: 'base32'}))"`

### Option 3: Use Online TOTP Generator
Go to: https://totp.danhersam.com/
1. Paste the MFA Secret
2. Click "Generate"
3. Use the 6-digit code shown

## Login Flow

### Step 1: Enter Credentials
- Email: `labtech@hospital.com`
- Password: `LabTech@123`
- Click "Login"

### Step 2: Frontend Shows MFA Screen
- You'll see "Enter MFA Code" input
- Message: "Check your authenticator app for a 6-digit code"

### Step 3: Get MFA Code
- Open your authenticator app
- Find the code for your account (it changes every 30 seconds)
- Example: `081507`

### Step 4: Enter Code & Verify
- Enter the 6-digit code: `081507`
- Click "Verify MFA"
- You're logged in! ✅

## Important Notes

⚠️ **MFA Code Validity:**
- Each code is valid for ~30 seconds
- If code expires, wait for a new one to appear in your app
- The system allows a 2-step window (±60 seconds) for clock drift

⚠️ **Code Re-use:**
- Each code can only be used ONCE
- You cannot use the same code twice
- Wait for the next code to generate

⚠️ **Timing Issues:**
- If MFA keeps failing, your device clock might be out of sync
- Sync your device time with NTP
- The backend checks within a 60-second window for flexibility

## Testing MFA

### Quick Test: Run MFA Test Script
```bash
cd Hospital-Backend
node test-mfa-complete.js
```

This will:
1. Test login with password for each user
2. Generate valid TOTP codes
3. Verify each code with the backend
4. Show success/failure for each role

Output:
```
✅ admin@hospital.com (admin) - MFA verified successfully!
✅ doctor@hospital.com (doctor) - MFA verified successfully!
✅ nurse@hospital.com (nurse) - MFA verified successfully!
... (7/8 total)
```

## Troubleshooting MFA Issues

### Issue: "Invalid MFA code" Error
**Solution:**
1. Check that code hasn't expired (should be recent)
2. Verify you're using the correct MFA Secret for that role
3. Sync your device clock to NTP
4. Wait 30 seconds for next code and try again

### Issue: "Invalid credentials" on Password Screen
**Solution:**
1. Check email is typed correctly (case-insensitive, ok)
2. Verify password: `Role@123` format (Role with capital first letter)
3. Example: `Doctor@123`, `LabTech@123`
4. Ensure no extra spaces

### Issue: MFA Screen Never Appears
**Solution:**
1. Check that `mfa_enabled: true` in database
2. Verify `mfa_secret` is set (not NULL)
3. Check backend logs for errors
4. Restart backend: `npm start`

### Issue: MFA Works in Test Script but Not in Frontend
**Solution:**
1. Frontend might not be passing code correctly
2. Check browser console for errors (F12)
3. Verify proxy is correctly routing to backend (port 3000)
4. Restart frontend: `npm run dev`

## Database Check

To verify MFA is enabled for a user:

```bash
node check-users-db.js
```

Look for:
- `mfa_enabled: true` ✅
- `mfa_secret: (not NULL)` ✅

## System Status

- ✅ MFA Backend Endpoint: `/api/mfa/verify`
- ✅ MFA Enabled: 7 roles (all except patient)
- ✅ TOTP Algorithm: 30-second window, ±2 steps allowed
- ✅ Secrets: Stored in database (not hashed - for TOTP verification)
- ✅ Test Script: `test-mfa-complete.js` (all 7 roles pass)

---

**Last Updated:** November 28, 2025
**Status:** ✅ MFA Fully Operational
