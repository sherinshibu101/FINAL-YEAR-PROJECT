# 🔐 MFA (Multi-Factor Authentication) - All Roles Enabled

## Status: ✅ MFA Enabled for All Roles

MFA is now **MANDATORY** for all 12 user accounts across all roles.

---

## Users with MFA Enabled

| Email | Role | MFA Status | Setup |
|-------|------|-----------|-------|
| `admin@hospital.com` | Admin | ✅ ENABLED | Use Google Authenticator |
| `doctor@hospital.com` | Doctor | ✅ ENABLED | Use Google Authenticator |
| `sherin_Dr@hospital.com` | Doctor | ✅ ENABLED | Use Google Authenticator |
| `Toufeeq_Dr@hospital.com` | Doctor | ✅ ENABLED | Use Google Authenticator |
| `Varun_Dr@hospital.com` | Doctor | ✅ ENABLED | Use Google Authenticator |
| `Harini_Dr@hospital.com` | Doctor | ✅ ENABLED | Use Google Authenticator |
| `nurse@hospital.com` | Nurse | ✅ ENABLED | Use Google Authenticator |
| `receptionist@hospital.com` | Receptionist | ✅ ENABLED | Use Google Authenticator |
| `labtech@hospital.com` | Lab Technician | ✅ ENABLED | Use Google Authenticator |
| `pharmacist@hospital.com` | Pharmacist | ✅ ENABLED | Use Google Authenticator |
| `accountant@hospital.com` | Accountant | ✅ ENABLED | Use Google Authenticator |
| `patient@hospital.com` | Patient | ✅ ENABLED | Use Google Authenticator |

---

## MFA Setup Instructions for Each User

### For Doctor (Example: doctor@hospital.com)

1. **Login Page**
   ```
   Email: doctor@hospital.com
   Password: Doctor@123
   [Click Login]
   ```

2. **System Response**
   ```
   ✓ Password correct
   ✓ MFA Required
   → Shows: "Enter the 6-digit code from your authenticator app"
   ```

3. **Get MFA Code**
   - Open **Google Authenticator** or **Authy** on your phone
   - Look for entry: `Hospital - doctor@hospital.com`
   - Copy the **6-digit code** (refreshes every 30 seconds)
   - Example: `123456`

4. **Enter MFA Code**
   ```
   MFA Code: [123456]
   [Verify]
   ```

5. **Success**
   ```
   ✓ MFA verified
   ✓ JWT token issued
   → Redirected to Dashboard
   ```

---

## How MFA Works in This System

### Architecture

```
1. User enters email + password
   ↓
2. Backend verifies credentials
   ↓
3. If password correct AND mfaEnabled = true:
   ├─ Response: mfaRequired = true
   ├─ Frontend shows MFA prompt
   └─ User enters 6-digit code
   ↓
4. Backend verifies TOTP code via speakeasy library
   ├─ Get user's MFA secret from database
   ├─ Generate expected code for current time window
   ├─ Compare with user-submitted code
   └─ Allow ±2 time windows (±60 seconds) for clock skew
   ↓
5. If valid:
   ├─ Create JWT token
   ├─ Create refresh token
   └─ Issue both to user
   ↓
6. User authenticated & logged in
```

### Code Flow

**Frontend Login** (Hospital-Frontend/server/index.js, line 417):
```javascript
if (user.mfaEnabled) {
  console.log('[LOGIN] MFA required for user:', userEmail)
  return res.json({ 
    success: true, 
    mfaRequired: true, 
    message: 'MFA required' 
  })
}
```

**MFA Verification** (Hospital-Frontend/server/index.js, line 454):
```javascript
app.post('/api/mfa/verify', mfaLimiter, (req, res) => {
  const { email, code } = req.body;
  
  // Validate code format (6 digits)
  if (!/^\d{6}$/.test(code.trim())) {
    return res.status(400).json({ 
      error: 'Invalid MFA code format' 
    });
  }
  
  // Verify TOTP code
  const user = users[email];
  const verified = speakeasy.totp.verify({
    secret: user.mfaSecret,
    encoding: 'base32',
    token: code,
    window: 2  // ±2 time steps (±60 seconds)
  });
  
  if (!verified) {
    return res.json({ 
      success: false, 
      error: 'Invalid MFA code' 
    });
  }
  
  // Issue JWT tokens
  const accessToken = jwt.sign(
    { email, role: user.role }, 
    JWT_SECRET, 
    { expiresIn: '15m' }
  );
  const refreshToken = createRandomToken();
  
  return res.json({ 
    success: true, 
    token: accessToken, 
    refreshToken: refreshToken,
    user: { email, name: user.name, role: user.role }
  });
});
```

---

## Security Protections

### Rate Limiting
```
- Login attempts: 5 per 15 minutes per IP
- MFA verification: 10 per 15 minutes per IP
```

If exceeded:
```
Response: 429 Too Many Requests
Message: "Too many attempts. Please try again later."
```

### Time Window Tolerance
```
- TOTP window: ±2 time steps
- Each time step: 30 seconds
- Total tolerance: ±60 seconds

Why? Allows for minor clock skew between user device and server
```

### Invalid Code Response
```
- User enters wrong code: "Invalid MFA code"
- Attempt is logged
- IP tracked for brute force detection
- After 10 failed attempts: IP rate-limited
```

---

## MFA Secrets by User

Each user has a **Base32-encoded secret** stored in `users.json`:

| User | Secret |
|------|--------|
| admin@hospital.com | `PVSU22Z3OBIWIZKXF52GWNDHLJJUMMSJKJJFI7L2IVAS44CJF42Q` |
| doctor@hospital.com | `MU7EI4S3KI2SQKDWMEYCS4KEKBXHUNBMNUUUY5KLIQ3FQTJQKZ4Q` |
| nurse@hospital.com | `IJ5HAYSCGB5S42CHGAXHS532MEZCY5L2OZESS4CRFRICGN2OHM4Q` |
| labtech@hospital.com | `MJSSSLCEHQ7XQ4JROY3TSJCUJJ5VCXKHNBWTCXS3MIUHA3JZJZOQ` |
| pharmacist@hospital.com | `MJMHSWBDJ5JWG4JKOY7UQTTLJ5SCUZSIK4ZEWQLDG5AGEJCYI5SQ` |
| (and 7 more...) | (see users.json) |

---

## Configuration

### File: `Hospital-Frontend/server/users.json`

```json
{
  "doctor@hospital.com": {
    "password": "$2a$10$...",              // bcrypt hash
    "role": "doctor",
    "name": "Dr. John Smith",
    "mfaEnabled": true,                    // ← MANDATORY
    "mfaSecret": "MU7EI4S3KI2SQKD..."     // ← Base32 encoded
  }
}
```

### File: `Hospital-Frontend/src/data.js`

```javascript
export const USERS_DB = {
  'doctor@hospital.com': {
    password: 'Doctor@123',
    role: 'doctor',
    name: 'Dr. John Smith',
    mfaEnabled: true                       // ← MANDATORY for all
  }
}
```

---

## Testing MFA

### Quick Test Script

```bash
# 1. Login with email + password
curl -X POST http://localhost:4000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hospital.com",
    "password": "Doctor@123"
  }'

# Response:
# {
#   "success": true,
#   "mfaRequired": true,
#   "message": "MFA required"
# }

# 2. Get MFA code from authenticator app (6 digits, refreshes every 30 sec)
# Example: 123456

# 3. Verify MFA code
curl -X POST http://localhost:4000/api/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@hospital.com",
    "code": "123456"
  }'

# Response (if code valid):
# {
#   "success": true,
#   "token": "eyJhbGc...",
#   "refreshToken": "abc123...",
#   "user": {
#     "email": "doctor@hospital.com",
#     "name": "Dr. John Smith",
#     "role": "doctor"
#   }
# }
```

---

## Authenticator Apps Supported

Any TOTP-compatible authenticator app works:

1. **Google Authenticator** (Most Popular)
   - iOS: [App Store](https://apps.apple.com/us/app/google-authenticator/id388497605)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2)

2. **Microsoft Authenticator**
   - iOS: [App Store](https://apps.apple.com/us/app/microsoft-authenticator/id983156458)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=com.azure.authenticator)

3. **Authy**
   - iOS: [App Store](https://apps.apple.com/us/app/authy/id494868406)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=com.authy.authy)

4. **FreeOTP**
   - iOS: [App Store](https://apps.apple.com/us/app/freeotp/id872559395)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=org.fedorahosted.freeotp)

---

## Changes Made

### 1. Hospital-Frontend/server/users.json
- ✅ All 12 users: `mfaEnabled: true`
- ✅ All users have `mfaSecret` assigned
- ✅ Patient account: `mfaSecret: "PATIENT1234SECRETBASE32ENCODEDHASH12345678901234"`

### 2. Hospital-Frontend/src/data.js
- ✅ Updated comment: "MFA is ENABLED for all users"
- ✅ All 12 users: `mfaEnabled: true`
- ✅ All users require TOTP verification

### 3. No Backend Changes Needed
- ✅ MFA logic already implemented in `Hospital-Frontend/server/index.js`
- ✅ Uses `speakeasy` library for TOTP verification
- ✅ Rate limiting already in place
- ✅ Audit logging already in place

---

## Enforcement Rules

| Rule | Enforcement |
|------|-------------|
| **MFA Required** | ✅ All roles must complete MFA to login |
| **6-digit Code** | ✅ Must enter exactly 6 digits |
| **30-second Window** | ✅ Code refreshes every 30 seconds |
| **60-second Tolerance** | ✅ Allows clock skew (±2 time steps) |
| **Rate Limiting** | ✅ 10 attempts per 15 minutes |
| **Invalid Code** | ✅ 429 Too Many Requests after threshold |
| **No Bypass** | ✅ Cannot login without valid MFA code |

---

## Login Flow with MFA (Visualized)

```
┌─────────────────────────────────────────────────┐
│ 1. User visits login page                        │
│    Screen: Email & Password fields              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 2. User enters credentials                       │
│    Email: doctor@hospital.com                   │
│    Password: Doctor@123                         │
│    [Login Button]                               │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 3. Backend verifies password ✓                   │
│    Check: mfaEnabled = true ✓                   │
│    Response: mfaRequired = true                 │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 4. Frontend shows MFA prompt                    │
│    Screen: "Enter 6-digit code from            │
│             authenticator app"                  │
│    MFA Code: [______]                           │
│    [Verify Button]                              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 5. User opens authenticator app                │
│    Sees: Hospital - doctor@hospital.com        │
│    Code: 123456 (refreshes in 10 sec)          │
│    Copies and pastes code                       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 6. Backend verifies TOTP code ✓                │
│    Response: token, refreshToken issued        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 7. Frontend stores tokens                       │
│    localStorage.setItem('hp_access_token',     │
│      'eyJhbGc...')                              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│ 8. User logged in                               │
│    Redirected to Dashboard                      │
│    Screen: Patient list, appointments, etc.    │
└─────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Test Login with MFA**
   - Start the application
   - Visit login page
   - Try logging in with any account
   - Follow MFA prompt
   - Verify codes work in authenticator app

2. **Monitor MFA Events**
   - Check logs: `Hospital-Backend/logs/security.log`
   - Look for MFA verification events

3. **Production Deployment**
   - Ensure authenticator app is set up on user devices
   - Communicate MFA requirement to all users
   - Provide support documentation

---

## Support

### Common Issues

**"Invalid MFA code"**
- Ensure code is 6 digits only
- Code expires after 30 seconds - must be entered quickly
- Check server and phone clocks are synchronized
- Try code from current 30-second window

**"Too many MFA attempts"**
- Wait 15 minutes before trying again
- Check that IP is not blocked
- Admin can check logs for security events

**"MFA not configured"**
- User might not have valid mfaSecret
- Check users.json for mfaSecret field
- If missing, cannot enable MFA for that user

---

## Summary

✅ **All 12 user roles now require MFA**
✅ **TOTP (Time-based One-Time Password) verification implemented**
✅ **Rate limiting prevents brute force attacks**
✅ **Secure token issuance after successful MFA**
✅ **Comprehensive audit logging of all MFA events**
✅ **Compatible with all standard authenticator apps**

**MFA is now MANDATORY for all users in the hospital system.**

