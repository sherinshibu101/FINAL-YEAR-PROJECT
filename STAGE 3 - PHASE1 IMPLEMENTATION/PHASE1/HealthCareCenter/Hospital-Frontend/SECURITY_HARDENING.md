# Hospital Management Portal - Security Hardening Summary

## 🔐 Security Enhancements Implemented

This document summarizes all security improvements made to the Hospital Management Portal to address common web application vulnerabilities.

---

## 1. **Rate Limiting** ✅

### Implementation
- **Package**: `express-rate-limit`
- **Location**: `server/index.js`

### Configuration

#### Login Endpoint
```
Path: POST /api/login
Limit: 5 attempts per 15 minutes per IP
Response: 429 Too Many Requests
```

#### MFA Verification Endpoint  
```
Path: POST /api/mfa/verify
Limit: 10 attempts per 15 minutes per IP
Response: 429 Too Many Requests
```

#### General API Rate Limit
```
Limit: 100 requests per 15 minutes per IP
Applied: All API endpoints
```

### Benefits
- Prevents brute force password attacks
- Protects MFA systems from code guessing
- Defends against Denial of Service (DoS)
- IP-based tracking included

### Testing
```bash
# Test login rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:4000/api/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@hospital.com","password":"wrong"}'
done
# Should get 429 on the 6th request
```

---

## 2. **Security Headers (Helmet.js)** ✅

### Implementation
- **Package**: `helmet`
- **Applied**: Global middleware

### Headers Added
```
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000 (when HTTPS enabled)
X-XSS-Protection: 1; mode=block
```

### Benefits
- Prevents clickjacking attacks
- Blocks MIME type sniffing
- Enables Content Security Policy
- Protects against XSS attacks

---

## 3. **Authentication & JWT Security** ✅

### JWT Configuration
```javascript
// Access Token: 15-minute expiry (short-lived)
const ACCESS_TOKEN_TTL = '15m'

// Refresh Token: 7-day expiry (long-term)
const REFRESH_TTL_MS = 7 * 24 * 60 * 60 * 1000

// Secret must be set in production
const JWT_SECRET = process.env.JWT_SECRET || 'demo_key_only_change_in_production'
```

### Secret Management
- **Default**: Clearly marked as insecure demo key
- **Production**: **MUST** use environment variable
- **Enforcement**: Exits with error if JWT_SECRET not set in production

### Token Rotation
- Refresh tokens rotated on each use
- Old token invalidated immediately
- New token family issued for next refresh

### Authorization
```javascript
// All protected routes verify JWT
app.get('/api/protected', authMiddleware, (req, res) => {
  // Validated user info in req.userEmail and req.userRole
})
```

---

## 4. **Password Security (Bcrypt)** ✅

### Implementation
- **Hash Function**: bcryptjs
- **Salt Rounds**: 10 (balanced security/performance)
- **Comparison**: Timing-resistant via bcryptjs

### Password Migration
- On startup: Auto-migrates plaintext passwords to bcrypt
- No downtime required
- One-time operation per user

### Code
```javascript
const hash = bcrypt.hashSync(password, 10)
const matches = bcrypt.compareSync(password, hash)
```

---

## 5. **Multi-Factor Authentication (TOTP)** ✅

### Implementation
- **Library**: Speakeasy
- **Algorithm**: Time-based One-Time Password (RFC 6238)
- **Code Length**: 6 digits
- **Time Window**: ±1 intervals (30-second window)

### Verification
```javascript
const verified = speakeasy.totp.verify({
  secret: userSecret,
  encoding: 'base32',
  token: userCode,
  window: 1
})
```

### Admin Provisioning
- Endpoint: `GET /api/admin/mfa/secret?email=user@hospital.com`
- Permission: Requires `canManageUsers` role
- Generates 20-character Base32 secret

---

## 6. **Input Validation** ✅

### Implemented Validation

#### Login Endpoint
```javascript
if (!email || !password) 
  return 400 // Missing credentials

if (typeof email !== 'string' || typeof password !== 'string')
  return 400 // Wrong type

if (email.length > 255 || password.length > 255)
  return 400 // Too long
```

#### MFA Verification
```javascript
if (!/^\d{6}$/.test(code.trim()))
  return 400 // Must be exactly 6 digits
```

#### Payload Size Limit
```javascript
app.use(bodyParser.json({ limit: '1mb' }))
```

### Benefits
- Prevents injection attacks
- Blocks oversized payloads
- Validates data types
- Enforces format requirements

---

## 7. **CORS Configuration** ✅

### Implementation
```javascript
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:5174',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))
```

### Security Features
- **Restricted Origin**: Only specified domain
- **Credentials**: Support for cookies/auth
- **Methods Whitelisting**: Only needed verbs
- **Headers Whitelisting**: Only needed headers

---

## 8. **Error Handling** ✅

### Generic Error Messages
```javascript
// Don't reveal user existence
if (!user) 
  return { success: false, error: 'Invalid email or password' }
// Could be wrong email OR wrong password, attacker doesn't know which
```

### Server Error Masking
```javascript
catch (err) {
  console.error('Login error:', err)  // Logged internally
  return res.status(500).json({ success: false, error: 'Server error' })
  // Generic message to client
}
```

### Benefits
- No user enumeration
- Prevents information disclosure
- Logging preserved for debugging

---

## 9. **HTTPS/TLS Recommendations** ⚠️

### Current Status
- Demo application running on localhost (HTTP only)
- Rate limiting and CORS don't require HTTPS to function

### Production Requirements
- **MANDATORY**: All traffic over TLS 1.2 or 1.3
- **Certificates**: Use Let's Encrypt or commercial CA
- **HSTS**: Set `Strict-Transport-Security` header
- **Redirect**: HTTP → HTTPS redirect
- **Cipher Suites**: Use strong ciphers only

---

## 10. **Environment Configuration** ✅

### New Files
- `.env.example`: Template for environment variables
- `SECURITY.md`: Detailed security documentation
- `PRODUCTION_DEPLOYMENT.md`: Step-by-step deployment guide

### Required Variables (Production)
```bash
export NODE_ENV=production
export JWT_SECRET="<generated-strong-key>"
export CORS_ORIGIN="https://yourdomain.com"
```

### Never Commit to Git
- `.env` (actual secrets file)
- Private keys
- Database passwords

---

## Installation & Setup

### Install Security Packages
```bash
cd server
npm install express-rate-limit helmet
```

### Verify Installation
```bash
npm list express-rate-limit helmet
npm audit  # Check for vulnerabilities
```

### Run Backend
```bash
cd server
node index.js
# Should see: Backend listening on http://localhost:4000
```

---

## Testing Security Features

### Rate Limiting Test
```bash
# Test login rate limiting
bash scripts/test-rate-limit.sh

# Manual test: 6 rapid requests should trigger 429
for i in {1..6}; do
  curl -X POST http://localhost:4000/api/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@hospital.com","password":"wrong"}' \
    -w "\nStatus: %{http_code}\n"
done
```

### JWT Expiration Test
```bash
# Generate expired token and test
curl -X GET http://localhost:4000/api/me \
  -H "Authorization: Bearer expired.jwt.token"
# Should return 401 Unauthorized
```

### CORS Test
```bash
# From different origin
curl -X GET http://localhost:4000/api/patients \
  -H "Origin: http://attacker.com" \
  -v
# Should fail CORS check
```

### MFA Code Validation
```bash
# Invalid code format
curl -X POST http://localhost:4000/api/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hospital.com","code":"abc123"}'
# Should return 400 Invalid MFA code format

# Too short
curl -X POST http://localhost:4000/api/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hospital.com","code":"12345"}'
# Should return 400
```

---

## Deployment Checklist

Before deploying to production:

- [ ] **Secrets**: All secrets in environment variables
- [ ] **Database**: Migrated from JSON to encrypted database
- [ ] **HTTPS**: All endpoints over TLS 1.2+
- [ ] **Rate Limiting**: Tested and working
- [ ] **Logging**: Centralized audit logging
- [ ] **Monitoring**: Alerts configured
- [ ] **Backups**: Automated backups enabled
- [ ] **Security Audit**: Third-party review completed
- [ ] **Compliance**: HIPAA/GDPR verified (if applicable)
- [ ] **Dependencies**: All npm packages up-to-date
- [ ] **Documentation**: SECURITY.md and PRODUCTION_DEPLOYMENT.md reviewed

---

## Known Limitations (Demo Only)

⚠️ **This application is a demo and NOT suitable for production without these changes:**

1. **User Storage**: JSON files → Must use encrypted database
2. **Session Storage**: JSON files → Must use Redis/database
3. **Logging**: Console only → Must use centralized logging
4. **Encryption**: At-rest encryption not implemented
5. **Audit Trail**: Minimal logging → Must implement comprehensive audit
6. **Backup/Recovery**: Not implemented
7. **Disaster Recovery**: Not implemented
8. **Monitoring**: Manual monitoring required
9. **Secrets Rotation**: Not automated

---

## Next Steps for Production

1. **Follow PRODUCTION_DEPLOYMENT.md** for deployment steps
2. **Read SECURITY.md** for comprehensive security overview
3. **Implement database migration** from JSON to PostgreSQL
4. **Set up Redis** for session/token storage
5. **Configure HTTPS** with Let's Encrypt
6. **Deploy monitoring** (Datadog, New Relic, Sentry, etc.)
7. **Schedule security audit** with external firm
8. **Implement HIPAA compliance** if required
9. **Set up incident response** procedures
10. **Create security runbooks** for operations team

---

## Security Contacts

- **Report Security Issues**: [Create private security advisory]
- **Support**: admin@yourdomain.com
- **Incident Response**: security@yourdomain.com

---

## References

- [OWASP Top 10 Web Application Security Risks](https://owasp.org/www-project-top-ten/)
- [Express.js Security Best Practices](https://expressjs.com/en/advanced/best-practice-security.html)
- [JWT Security Best Practices](https://tools.ietf.org/html/rfc8725)
- [Helmet.js Documentation](https://helmetjs.github.io/)
- [Rate Limiting Guide](https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html)

---

**Last Updated**: November 25, 2025  
**Application Status**: Demo / Proof of Concept  
**Production Ready**: ❌ Not Yet (Follow PRODUCTION_DEPLOYMENT.md)
