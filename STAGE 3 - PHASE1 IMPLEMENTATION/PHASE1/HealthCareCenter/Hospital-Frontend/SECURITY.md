# Security Documentation - Hospital Management Portal

## ⚠️ IMPORTANT: Demo Application Warning

**This project is a demo/proof-of-concept and is NOT suitable for production use without significant security enhancements.**

---

## Security Features Implemented

### 1. **Rate Limiting (Express Rate Limit)**
✅ **Implemented:** `server/index.js` uses `express-rate-limit`

- **Login Endpoint** (`/api/login`): **5 attempts per 15 minutes per IP**
  - Prevents brute force password attacks
  - Returns 429 status with rate limit headers
  
- **MFA Verification** (`/api/mfa/verify`): **10 attempts per 15 minutes per IP**
  - Protects against MFA code guessing attacks
  - Validates code format (must be 6 digits)
  
- **General API Rate Limit**: **100 requests per 15 minutes per IP**
  - Protects authenticated endpoints
  - Prevents DoS attacks

### 2. **HTTPS Security Headers (Helmet.js)**
✅ **Implemented:** `helmet()` middleware applied

- Content Security Policy (CSP)
- X-Frame-Options (clickjacking protection)
- X-Content-Type-Options (MIME sniffing prevention)
- Strict-Transport-Security (HSTS - when HTTPS enabled)
- X-XSS-Protection

### 3. **Authentication & Authorization**

#### JWT Implementation ✅
- **Access Tokens**: 15-minute expiry (short-lived)
- **Refresh Tokens**: 7-day expiry, rotated on each refresh
- **Environment Variable Required in Production**:
  ```bash
  export JWT_SECRET="your-strong-secret-key-here"
  ```
  - If not set in production mode, server exits with error
  - Default demo key clearly marked as insecure

#### Role-Based Access Control (RBAC) ✅
- 5 roles implemented: Admin, Doctor, Nurse, Receptionist, Patient
- Permission-based endpoint access
- Field-level authorization for sensitive operations

#### Password Security ✅
- **Bcrypt Hashing**: All passwords hashed with bcrypt (salt rounds: 10)
- **On-Startup Migration**: Plaintext passwords auto-migrated to hashed format
- **Password Comparison**: Secure timing-resistant comparison via bcryptjs

### 4. **Multi-Factor Authentication (TOTP)**
✅ **Implemented:** Time-based One-Time Password via Speakeasy

- 20-character secrets, Base32 encoded
- 6-digit time-window verification with ±1 window
- Admin provisioning endpoint with permission checks
- MFA flag properly enforced at login

### 5. **Input Validation & Sanitization**
✅ **Implemented:**

- **Type Validation**: Email and password must be strings
- **Length Limits**: Email and password max 255 characters
- **Format Validation**: MFA code must match `/^\d{6}$/` regex
- **Payload Size Limit**: 1MB max for JSON bodies
- **No SQL Injection**: Using JSON file storage (not applicable)

### 6. **CORS Configuration**
✅ **Restricted CORS**:
```javascript
origin: process.env.CORS_ORIGIN || 'http://localhost:5174'
credentials: true
methods: ['GET', 'POST', 'PUT', 'DELETE']
allowedHeaders: ['Content-Type', 'Authorization']
```
- Only specified origin can access API
- Credentials allowed for session management
- Methods explicitly whitelisted

### 7. **Error Handling & Information Disclosure**
✅ **Implemented:**

- Generic error messages for failed logins (no user enumeration)
- Server errors logged but not exposed to client
- Rate limit messages informative but not exploitable
- Try-catch blocks around critical operations

---

## Known Security Issues & Production Recommendations

### 🔴 **CRITICAL - NOT FOR PRODUCTION:**

#### 1. **User Data Storage**
**Current:** `server/users.json` (file-based)
**Production Recommendation:**
- Use PostgreSQL, MongoDB, or similar DBMS
- Encrypt sensitive data at rest
- Implement access controls at database level
- Use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)

#### 2. **Refresh Token Storage**
**Current:** `server/sessions.json` (file-based, persisted in plain JSON)
**Production Recommendation:**
- Store in Redis with automatic TTL expiration
- Implement refresh token rotation with reuse detection
- Track token families to detect compromised tokens
- Revoke entire token chain if reuse detected

#### 3. **JWT Secret Management**
**Current:** Defaults to `'demo_key_only_change_in_production'`
**Production Requirement:**
```bash
# Must set environment variable before startup
export JWT_SECRET="<generate-strong-random-key>"
# or use secrets manager
```
**Recommendation:**
- Generate strong 256-bit random key
- Rotate keys regularly
- Use different keys for different environments
- Never commit secrets to version control

#### 4. **HTTPS/TLS**
**Current:** No HTTPS enforcement (localhost only)
**Production Requirement:**
- All traffic must be HTTPS
- Valid SSL/TLS certificate
- HSTS header enforced
- HTTP → HTTPS redirect

#### 5. **Database Encryption**
**Not Implemented:**
- Enable encryption-at-rest for database
- Use encryption-in-transit (TLS 1.2+)
- Encrypt PII fields (SSN, medical records, etc.)

#### 6. **Audit Logging**
**Current:** Basic console.error() logging
**Production Recommendation:**
- Centralized audit logs (ELK Stack, Datadog, Splunk)
- Log all authentication attempts (success and failure)
- Track API access and modifications
- Maintain immutable audit trail

#### 7. **API Key Management**
**Not Implemented:**
- Consider API keys for service-to-service communication
- Rotate keys regularly
- Associate keys with specific permissions

#### 8. **Content Security Policy (CSP)**
**Partially Implemented:** Via Helmet
**Production Enhancement:**
- Customize CSP for your domain
- Prevent inline scripts
- Whitelist specific script/style sources only

---

## Environment Variables Reference

### Required for Production:
```bash
NODE_ENV=production
JWT_SECRET=<strong-random-key>
CORS_ORIGIN=https://yourdomain.com
PORT=4000
```

### Optional:
```bash
LOG_LEVEL=info
DB_URL=postgresql://...  # when migrating from JSON
REDIS_URL=redis://...     # for session storage
```

---

## Security Checklist for Production Deployment

- [ ] **Secrets**: All secrets externalized to environment variables
- [ ] **Database**: Migrated from JSON files to encrypted database
- [ ] **Refresh Tokens**: Moved from JSON to Redis with TTL
- [ ] **HTTPS**: All endpoints over TLS 1.2+
- [ ] **Rate Limiting**: Tested and configured per endpoint
- [ ] **Logging**: Centralized audit logging implemented
- [ ] **Monitoring**: Security monitoring and alerts configured
- [ ] **Backup/Recovery**: Automated backups and disaster recovery tested
- [ ] **Penetration Testing**: Third-party security audit completed
- [ ] **Compliance**: Verified HIPAA compliance (for healthcare)
- [ ] **Authentication**: MFA required for all users
- [ ] **Authorization**: RBAC properly enforced on all endpoints
- [ ] **Dependencies**: All npm packages up-to-date and scanned for vulnerabilities
- [ ] **CORS**: Restricted to specific origin only
- [ ] **CSP**: Customized for production domain

---

## Running Securely

### Development:
```bash
npm run dev
# Backend: http://localhost:4000
# Frontend: http://localhost:5174
```

### Production:
```bash
# Set environment variables
export JWT_SECRET="<your-secret>"
export NODE_ENV="production"
export CORS_ORIGIN="https://yourdomain.com"

# Run backend
npm start
```

---

## Common Attack Vectors & Mitigations

| Attack | Current Status | Mitigation |
|--------|----------------|-----------|
| Brute Force Login | ✅ Mitigated | Rate limiting: 5 attempts/15 min |
| MFA Code Guessing | ✅ Mitigated | Rate limiting: 10 attempts/15 min |
| Session Hijacking | ⚠️ Partial | Use HTTPS + secure cookies in prod |
| CSRF | ✅ Mitigated | SameSite cookies (via Helmet) |
| XSS | ✅ Partially | CSP via Helmet, sanitization needed |
| SQL Injection | ✅ N/A | JSON storage, no SQL queries |
| Password Cracking | ✅ Mitigated | Bcrypt hashing, 10 rounds |
| Token Leakage | ⚠️ Partial | Use HTTPS + secure storage |
| Privilege Escalation | ✅ Mitigated | RBAC on all endpoints |
| Information Disclosure | ✅ Mitigated | Generic error messages |

---

## Testing Security

### Manual Testing:
```bash
# Test rate limiting on login
for i in {1..6}; do
  curl -X POST http://localhost:4000/api/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@hospital.com","password":"wrong"}'
  echo "Request $i"
done
# Should see 429 Too Many Requests on 6th attempt

# Test MFA validation
curl -X POST http://localhost:4000/api/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hospital.com","code":"000000"}'
# Should reject non-6-digit codes

# Test JWT expiration
curl -X GET http://localhost:4000/api/me \
  -H "Authorization: Bearer invalid_token"
# Should return 401 Unauthorized
```

### Automated Testing:
```bash
npm install --save-dev jest supertest
# Add security test suite
```

---

## Compliance Notes

For **HIPAA** (US healthcare) compliance, additional requirements:
- [ ] Encryption of PHI (Protected Health Information)
- [ ] Access audit logs
- [ ] Business Associate Agreements (BAA)
- [ ] Data retention policies
- [ ] Breach notification procedures
- [ ] Workforce access management

For **GDPR** (EU/Global) compliance:
- [ ] Data privacy by design
- [ ] User consent management
- [ ] Right to be forgotten implementation
- [ ] Data export functionality
- [ ] Privacy impact assessments

---

## Support & Incident Response

**Security Issues:** Report privately to the development team.

**Incident Response Plan:**
1. Detect anomaly via monitoring
2. Isolate affected system
3. Preserve logs and evidence
4. Notify stakeholders
5. Remediate vulnerability
6. Post-incident review

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Express Security Best Practices](https://expressjs.com/en/advanced/best-practice-security.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

---

**Last Updated:** November 25, 2025
**Status:** Demo Application - Not For Production Use
