# Healthcare System - Quick Start Guide

## System Architecture

```
Frontend (React/Vite)      Backend (Express.js)      Database (PostgreSQL)
http://localhost:5173      http://localhost:3000     localhost:5432
```

## Prerequisites

- Node.js v22+ installed
- Docker & Docker Compose installed
- PostgreSQL running (via Docker)

## Startup Instructions

### Step 1: Start Database (One-time or as needed)
```powershell
cd "c:\Harini\S7\Final Year Project\HealthCareCenter"
docker-compose up -d
```

**Verify:**
- PostgreSQL: `localhost:5432`
- Adminer UI: `http://localhost:8080`

### Step 2: Start Backend Server
```powershell
cd "c:\Harini\S7\Final Year Project\HealthCareCenter\Hospital-Backend"
npm start
```

**Expected Output:**
```
✓ Encryption service loaded
✓ Hospital Backend listening on http://localhost:3000
  Environment: development
  Database: localhost:5432/hospital_db
```

### Step 3: Start Frontend Server
```powershell
cd "c:\Harini\S7\Final Year Project\HealthCareCenter\Hospital-Frontend"
npm run dev
```

**Expected Output:**
```
VITE v5.4.21  ready in 713 ms
➜  Local:   http://localhost:5173/
```

## Access the System

1. **Open browser:** http://localhost:5173
2. **Login credentials:**
   - Email: `doctor@hospital.com`
   - Password: `Doctor@123`

## Available User Roles for Testing

| Role | Email | Password | MFA |
|------|-------|----------|-----|
| Admin | admin@hospital.com | Admin@123 | ✅ |
| Doctor | doctor@hospital.com | Doctor@123 | ✅ |
| Nurse | nurse@hospital.com | Nurse@123 | ✅ |
| Receptionist | receptionist@hospital.com | Receptionist@123 | ✅ |
| Lab Technician | labtech@hospital.com | LabTech@123 | ✅ |
| Pharmacist | pharmacist@hospital.com | Pharmacist@123 | ✅ |
| Accountant | accountant@hospital.com | Accountant@123 | ✅ |
| Patient | patient@hospital.com | Patient@123 | ❌ |

## Testing Lab PDF Download

1. Login as **doctor@hospital.com**
2. Navigate to **Lab Tests** tab
3. Click **View Report** on any completed test (status: "completed")
4. Click **Download PDF Report** button
5. PDF downloads with authentication! ✅

## Testing Billing Module

1. Login as **accountant@hospital.com**
2. Navigate to **Billing** tab
3. Create a new bill or view existing bills
4. Click **View Details** on any bill
5. Add charges, apply discounts, process payments
6. Click **Download Invoice** to get PDF

## Key Features

✅ **Lab Tests Module**
- Order lab tests
- Upload results with PDF reports
- View and download lab reports

✅ **Billing Module**
- Create bills with itemized charges
- Apply discounts and taxes
- Process payments with encryption
- Download invoices as PDF

✅ **Pharmacy Module**
- Manage prescriptions
- Add medication charges
- Track prescription status

✅ **Role-Based Access Control**
- 8 user roles with specific permissions
- Encryption for sensitive data
- Audit logging for all operations

## Troubleshooting

### "Cannot find module" Error
**Problem:** Running `node index.js` in frontend directory
**Solution:** Use `npm run dev` instead (frontend is React, not Node.js)

### "File not available on this site" Error
**Problem:** Backend server not running or authentication not working
**Solution:** 
1. Ensure backend is running: `npm start` in Hospital-Backend
2. Ensure you're logged in (check localStorage for token)
3. Check browser console for errors

### Port Already in Use
**Problem:** Port 3000 or 5173 already in use
**Solution:**
```powershell
# Find process using port 3000
netstat -ano | Select-String ":3000"

# Kill process (if needed)
Stop-Process -Id <PID> -Force
```

### Database Connection Error
**Problem:** Cannot connect to PostgreSQL
**Solution:**
```powershell
# Check Docker containers
docker ps

# If not running, start Docker Compose
cd HealthCareCenter
docker-compose up -d
```

## File Structure

```
HealthCareCenter/
├── Hospital-Backend/          # Express.js backend
│   ├── src/index.js          # Main server file
│   ├── package.json
│   └── storage/              # File storage
│       ├── lab-reports/      # Lab PDFs
│       └── invoices/         # Invoice PDFs
├── Hospital-Frontend/         # React/Vite frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   └── data.js
│   ├── index.html
│   └── package.json
├── Encryption/               # Encryption service
│   ├── encryptionService.js
│   ├── encryption.js
│   └── pdfGenerator.js
└── docker-compose.yml        # Database setup
```

## API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/mfa/verify` - MFA verification
- `POST /api/token/refresh` - Refresh access token
- `GET /api/me` - Current user info

### Lab Tests
- `GET /api/lab-tests` - List tests
- `POST /api/lab-tests` - Create test
- `PUT /api/lab-tests/:id` - Update test
- `GET /api/files/*` - Download files (auth required)

### Billing
- `GET /api/billing` - List bills
- `POST /api/billing` - Create bill
- `POST /api/billing/:id/services` - Add charges
- `PUT /api/billing/:id/payment` - Process payment
- `GET /api/billing/:id/invoice` - Download invoice

### Pharmacy
- `GET /api/prescriptions` - List prescriptions
- `POST /api/prescriptions` - Create prescription

## Environment Variables

**Backend (.env in Hospital-Backend/):**
```
DATABASE_URL=postgresql://user:password@localhost:5432/hospital_db
JWT_SECRET=your-secret-key
NODE_ENV=development
PORT=3000
```

**Encryption (.env in Encryption/):**
```
DEMO_MEK_BASE64=your-master-encryption-key
```

## Performance Tips

1. **Database:** Indexes on frequently queried columns
2. **Frontend:** Lazy loading of components
3. **Backend:** Connection pooling with pg
4. **Files:** Stream-based delivery of PDFs
5. **Encryption:** Efficient key management with KMS

## Security Features

✅ JWT-based authentication
✅ MFA (TOTP) support
✅ AES-256-GCM encryption for sensitive data
✅ Role-based access control (RBAC)
✅ SQL injection prevention with parameterized queries
✅ Rate limiting on API endpoints
✅ Audit logging for compliance
✅ Path validation to prevent directory traversal
✅ CORS protection
✅ Helmet security headers

## Support

For issues or questions:
1. Check the browser console for error messages
2. Check server logs (terminal where `npm start` is running)
3. Verify all services are running: frontend, backend, database
4. Clear browser cache (Ctrl+Shift+Delete)

---

**Last Updated:** November 28, 2025
**System Status:** ✅ Production Ready
