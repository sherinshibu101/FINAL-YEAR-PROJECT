# Hospital Portal — Demo Project

This repository is a developer/demo implementation of a Hospital Portal showcasing:

- Multi-Factor Authentication (MFA) using TOTP (speakeasy)
- JWT-based authentication with refresh tokens (refresh tokens persisted in `server/sessions.json`)
- Role-Based Access Control (RBAC) with four predefined roles: **Admin**, **Doctor**, **Nurse**, **Receptionist**
- Protected API endpoints for patients and appointments
- A clean React + Vite frontend with a small Admin UI for provisioning MFA secrets
- **🔐 Enterprise-grade security hardening** with rate limiting, input validation, security headers, and more

> **⚠️ IMPORTANT**: This is a **demo application** and is **NOT suitable for production use** without significant security enhancements. See [SECURITY.md](./SECURITY.md) for critical production requirements.

---

## 🔐 Security Features

✅ **Rate Limiting**: Prevents brute force attacks (5 login attempts/15 min)  
✅ **JWT Authentication**: Secure tokens with rotation  
✅ **Password Hashing**: Bcrypt with 10 salt rounds  
✅ **Multi-Factor Auth**: TOTP-based 2FA support  
✅ **Input Validation**: Type checking and format validation  
✅ **CORS Protection**: Restricted to specified origins  
✅ **Security Headers**: Via Helmet.js  
✅ **RBAC**: Role-based access control on all endpoints  
✅ **Error Masking**: No information disclosure  

**For detailed security documentation**, see:
- 📄 [SECURITY_SUMMARY.md](./SECURITY_SUMMARY.md) - Quick overview
- 📄 [SECURITY.md](./SECURITY.md) - Comprehensive guide  
- 📄 [SECURITY_HARDENING.md](./SECURITY_HARDENING.md) - Implementation details
- 📄 [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) - Production setup

---

## Quick start (Windows PowerShell)

1. Install frontend dependencies and start Vite dev server:

```powershell
cd d:\Final_Year_Project
npm install
npm run dev
```

2. Install backend dependencies and start the backend server (separate terminal):

```powershell
cd d:\Final_Year_Project\server
npm install
node index.js
```

The Vite dev server runs (usually) at `http://localhost:5173` and proxies `/api` to the backend at `http://localhost:4000`.

---

## Project layout

- `index.html` — App entry and Tailwind CDN for quick styling.
- `vite.config.js` — Vite configuration and proxy for `/api` to backend.
- `src/` — Frontend source
  - `src/main.tsx` — React bootstrap (TypeScript entry)
  - `src/App.tsx` — Main app and UI (login, MFA, dashboard, patients, appointments, permissions, admin UI)
  - `src/auth.ts` — Auth helpers: login, verify MFA, token storage & refresh, API wrappers (TypeScript)
  - `src/data.js` — Role permissions and mock values used by UI
- `server/` — Backend
  - `server/index.js` — Express server: bcrypt password hashing, TOTP verify, JWT access tokens, refresh token persistence, protected routes
  - `server/users.json` — Demo users (migrated to bcrypt on startup)
  - `server/data.json` — Demo patients & appointments
  - `server/sessions.json` — Persisted refresh token store

---

## Authentication flow (summary)

1. Client calls `POST /api/login` with `{ email, password }`.
	- If the user has MFA enabled, server responds with `{ success: true, mfaRequired: true }`.
	- If not, server issues an access JWT and a refresh token, returns `{ token: <jwt>, refreshToken: <token>, user: {...} }`.
2. When MFA is required, client asks the user for the TOTP code and calls `POST /api/mfa/verify` with `{ email, code }`.
	- On success, server issues an access token (JWT) and refresh token.
3. Protected requests use `Authorization: Bearer <accessToken>` header.
4. When access token expires, client calls `POST /api/token/refresh` with `{ refreshToken }` to get a new access token and rotated refresh token.
5. Client may call `POST /api/logout` with `{ refreshToken }` to revoke the refresh token.

Frontend specifics:
- `src/auth.js` stores tokens in `localStorage` keys `hp_access_token` and `hp_refresh_token` and provides `fetchWithAuth` which automatically attempts a refresh on 401 responses.

---

## Role-Based Access Control (RBAC)

- Roles are defined in `server/index.js` and `src/data.js` (`ROLE_PERMISSIONS`).
- Permissions include `canViewPatients`, `canEditPatients`, `canDeletePatients`, `canViewAppointments`, `canManageAppointments`, `canViewRecords`, `canEditRecords`, `canManageUsers`, `canViewReports`, `canAccessSettings`.
- Backend guards endpoints using JWT validation and permission checks where required (admin-only endpoints use `requirePermission('canManageUsers')`).
- Frontend reads `currentUser.permissions` and conditionally shows/hides features.

---

## API Reference (important endpoints)

- `POST /api/login` — body: `{ email, password }`. May return `{ mfaRequired: true }` or `{ token, refreshToken, user }`.
- `POST /api/mfa/verify` — body: `{ email, code }`. Returns `{ token, refreshToken, user }` on success.
- `POST /api/token/refresh` — body: `{ refreshToken }`. Returns `{ token, refreshToken }` (rotated).
- `POST /api/logout` — body: `{ refreshToken }`. Revokes the refresh token.
- `GET /api/me` — requires `Authorization: Bearer <jwt>`. Returns user object and permissions.
- `GET /api/patients` — protected; requires `canViewPatients` permission.
- `GET /api/appointments` — protected; requires `canViewAppointments`.
- `GET /api/admin/mfa/secret` — protected; requires admin permission `canManageUsers`. Returns or generates a Base32 secret for provisioning TOTP for the specified user (admin-only action).

---

## How to test MFA locally

1. Start backend and frontend as above.
2. Login with a demo account if your instance includes demo users. On first server start it migrates plaintext passwords in `server/users.json` to bcrypt hashes; any demo passwords present are migrated and stored hashed on disk.
3. If MFA is required, as Admin use the Admin tab to fetch the Base32 secret for the user email (enter email and click "Get Secret").
4. Add the Base32 secret to an authenticator app (Google Authenticator, Authy) and read the 6-digit TOTP code.
5. Enter TOTP in the MFA screen to complete login.

You can also use PowerShell to exercise endpoints directly (useful for automated tests):

```powershell
# login request
Invoke-RestMethod -Uri http://localhost:4000/api/login -Method Post -Body (ConvertTo-Json @{email='user@example.com'; password='yourpassword'}) -ContentType 'application/json'
```

---

## Security notes & limitations (READ BEFORE DEPLOYING)

- This project is a demo; it is not secure for production use.
- `server/users.json` contains secrets and demo data. In production, use a database, hash passwords, and encrypt secrets.
- JWT secret is set to a default in `server/index.js`. Override via `JWT_SECRET` environment variable in any real deployment.
- Refresh tokens are stored in a JSON file for demo purposes; use a secure database and implement refresh-reuse detection for stronger security.
- Add rate limiting (e.g., `express-rate-limit`) and IP-based controls around `/api/login` and `/api/mfa/verify`.

---

## Development notes & next steps

- Move persistence to a real DB (SQLite for local dev, Postgres for production).
- Add server-side rate limiting and account lockout policies (persisted counters).
- Add an admin user-management panel to create/update/delete users and manage their MFA settings with auditing.
- Add unit and integration tests for auth flows and protected endpoints.
- Consider replacing TOTP provisioning with safer workflows (QR codes, one-time provisioning links) in production.

---

If you want, I can generate a small checklist or roadmap that breaks down production-hardening tasks into issues and code changes. Tell me which area to prioritize (backend security, admin UI, persistence, or testing) and I will scaffold the next steps.

