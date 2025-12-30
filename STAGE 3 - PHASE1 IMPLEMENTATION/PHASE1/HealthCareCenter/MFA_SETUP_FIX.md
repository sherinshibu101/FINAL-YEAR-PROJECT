# MFA Setup Guide - Fix "Invalid MFA Code" Error

## Problem
You're getting "Invalid MFA code" error when trying to login even though you entered the correct code from your authenticator app.

## Root Cause
Your authenticator app has a **different secret** than what's stored in the system database. This happens when:
- The app was set up with the wrong QR code
- You manually typed the wrong secret
- The app was reconfigured

## Solution: Rescan the QR Code or Add the Correct Secret

### Step 1: Get Your MFA Secret
The correct MFA secret for each role is:

| Email | Secret |
|-------|--------|
| admin@hospital.com | `PVSU22Z3OBIWIZKXF52GWNDHLJJUMMSJKJJFI7L2IVAS44CJF42Q` |
| doctor@hospital.com | `MU7EI4S3KI2SQKDWMEYCS4KEKBXHUNBMNUUUY5KLIQ3FQTJQKZ4Q` |
| nurse@hospital.com | `IJ5HAYSCGB5S42CHGAXHS532MEZCY5L2OZESS4CRFRICGN2OHM4Q` |
| receptionist@hospital.com | `ENXE2JCKKZXHOMJRMV2EEOTHINCDIYLOPJ6SYRDDIJUFOJD5PMZA` |
| labtech@hospital.com | `MJSSSLCEHQ7XQ4JROY3TSJCUJJ5VCXKHNBWTCXS3MIUHA3JZJZOQ` |
| pharmacist@hospital.com | `MJMHSWBDJ5JWG4JKOY7UQTTLJ5SCUZSIK4ZEWQLDG5AGEJCYI5SQ` |
| accountant@hospital.com | `IBSG27J4NN3HSZTQGY4SS2DMNRPEGJRZIJFW4423J5WDMUBFEVKA` |

### Step 2: Add to Your Authenticator App

**Using Google Authenticator or Similar:**
1. Open your authenticator app
2. Tap the **+** button to add a new account
3. Select "Enter a setup key"
4. Enter:
   - **Account name**: Your email (e.g., `doctor@hospital.com`)
   - **Key**: Copy the secret from the table above
   - **Type**: TOTP (Time-based One-Time Password)
   - **Time step**: 30 seconds
5. Tap **Add**

**OR scan the QR code:**
1. Open your authenticator app
2. Tap the **+** button to scan QR code
3. Scan the QR code provided by the system

### Step 3: Verify the New Setup
1. Open your authenticator app
2. Find your account (e.g., `doctor@hospital.com`)
3. Note the 6-digit code displayed
4. Try logging in again with this NEW code

## If It Still Doesn't Work

### Check Your Device Time
TOTP codes are time-sensitive. If your device clock is more than 2 minutes off, codes won't validate.

**Fix:**
1. Go to Settings → Date & Time
2. Turn on "Automatic date & time"
3. Restart your device
4. Try again

### Check You're Using the Right Secret
Make sure you're using the secret for YOUR email address, not a different role.

### Contact Admin
If the above doesn't work, ask an admin to reset your MFA by:
- Deleting your account and re-creating it
- Or running the seed script: `npx knex seed:run`

---

**Note**: Each 6-digit code is valid for ~30 seconds, then a new one is generated. If a code expires before you submit it, just wait for the next one.
