# Hospital Management System - Local Development Setup

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Docker Desktop running
- Node.js 18+
- PowerShell 5.1 or higher

### Step 1: Start the Database
```powershell
cd Hospital-Backend
docker-compose up -d
```

You should see:
```
✔ Network hospital-backend_default      Created
✔ Volume hospital-backend_db-data       Created
✔ Container hospital-backend-db-1       Started
✔ Container hospital-backend-adminer-1  Started
```

### Step 2: Run Migrations & Seeds (First time only)
```powershell
cd Hospital-Backend
npx knex migrate:latest --env development
npx knex seed:run --env development
```

You should see:
```
Using environment: development
Batch 1 run: 1 migrations
✓ Database seeded successfully
```

### Step 3: Start Backend Server
```powershell
cd Hospital-Backend
npm run dev
```

or

```powershell
node src/index.js
```

You should see:
```
✓ Hospital Backend listening on http://localhost:3000
  Environment: development
  Database: localhost:5432/hospital_db
```

### Step 4: Start Frontend Server
In a new terminal:
```powershell
cd Hospital-Frontend
npm run dev
```

You should see:
```
  Port: 5174
```

### Step 5: Access the Applications

| Application | URL | Purpose |
|---|---|---|
| Frontend | http://localhost:5174 | React UI |
| Backend API | http://localhost:3000 | REST API |
| Database UI | http://localhost:8080 | Adminer (DB Browser) |

---

## 📝 Environment Files

### Backend (`.env`)
Located: `Hospital-Backend/.env`

Key variables:
- `PORT=3000` - Backend server port
- `NODE_ENV=development` - Environment mode
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET` - Shared with frontend for token verification

### Frontend (`.env`)
Located: `Hospital-Frontend/server/.env`

Key variables:
- `PORT=4000` - Frontend server port
- `NODE_ENV=development` - Environment mode
- `JWT_SECRET` - Matches backend JWT_SECRET
- `CORS_ORIGIN=http://localhost:5174` - Frontend URL

⚠️ **Important**: Both servers use the **same JWT_SECRET** for token verification.

---

## 🗄️ Database Access

### Option 1: Adminer Web UI (Recommended for beginners)
- **URL**: http://localhost:8080
- **Server**: `db`
- **Username**: `hospital`
- **Password**: `F1UFDk8H36Ry2RITAvnErulW`
- **Database**: `hospital_db`

### Option 2: psql Command Line
```bash
# Install PostgreSQL client if not present
# Then connect to:
psql -h localhost -U hospital -d hospital_db
# Password: F1UFDk8H36Ry2RITAvnErulW
```

---

## 📚 API Endpoints

### Patients
```bash
# List all patients
GET /api/patients

# Get single patient
GET /api/patients/:id

# Create new patient
POST /api/patients
# Body: { first_name, last_name, dob, gender, contact, insurance }
```

### Appointments
```bash
# List all appointments
GET /api/appointments

# Create appointment
POST /api/appointments
# Body: { patient_id, doctor_id, scheduled_at, appointment_type, notes }
```

### Lab Tests
```bash
# List lab tests
GET /api/lab-tests

# Create lab test
POST /api/lab-tests
# Body: { patient_id, requested_by, test_name, result_data }
```

### Vitals
```bash
# Get patient vitals
GET /api/vitals/:patient_id

# Record vitals
POST /api/vitals
# Body: { patient_id, recorded_by, metrics: { bp_systolic, bp_diastolic, heart_rate, ... } }
```

### Health
```bash
# Backend health check
GET /health
GET /
```

---

## 🔄 Development Workflow

### Local Development Loop
```powershell
# Terminal 1: Database
cd Hospital-Backend
docker-compose up -d

# Terminal 2: Backend
cd Hospital-Backend
npm run dev

# Terminal 3: Frontend
cd Hospital-Frontend
npm run dev

# Open browser to http://localhost:5174
```

### Making Database Changes
```powershell
# Create a new migration
cd Hospital-Backend
npx knex migrate:make add_new_table

# Edit the migration file in src/migrations/

# Run the migration
npx knex migrate:latest --env development
```

### Resetting the Database
```powershell
# Stop and remove containers + volumes
cd Hospital-Backend
docker-compose down -v

# Start fresh
docker-compose up -d

# Re-run migrations and seeds
npx knex migrate:latest --env development
npx knex seed:run --env development
```

---

## 🐛 Troubleshooting

### "Address already in use" error
```powershell
# Kill Node processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill Docker containers
docker-compose down
docker-compose up -d
```

### Database connection fails
```bash
# Check Docker status
docker ps

# View logs
docker-compose logs db

# Verify password matches in .env and docker-compose.yml
```

### Knex command not found
```bash
# Use npx instead
npx knex migrate:latest --env development
npx knex seed:run --env development
```

### Port 5174 already in use (Frontend)
```bash
# Change port in Hospital-Frontend/vite.config.js
# or kill existing process
Get-Process node | Stop-Process -Force
```

---

## 📊 Database Schema

### Tables
- `users` - User accounts with roles and MFA
- `patients` - Patient demographic and medical info
- `appointments` - Appointment scheduling
- `lab_tests` - Lab test orders and results
- `prescriptions` - Medication prescriptions
- `vitals` - Blood pressure, heart rate, temperature, etc.
- `files` - Document storage and tracking
- `audit_logs` - Compliance logging for HIPAA

See `SETUP_COMPLETE.md` for detailed schema documentation.

---

## 🔐 Security Notes

### For Local Development
✅ Allowed: Plain HTTP, demo JWT secrets, file-based storage
✅ Allowed: No HTTPS, simple passwords
✅ Allowed: Accessing database directly via Adminer

### For Production
❌ Never: Use these demo configurations
❌ Never: Commit `.env` files to Git
❌ Never: Expose database to internet
❌ Never: Use default secrets

Production checklist:
- [ ] Enable HTTPS/TLS
- [ ] Use strong, unique JWT secrets
- [ ] Migrate to production database (RDS, managed PostgreSQL)
- [ ] Set up encryption at rest
- [ ] Enable database backups
- [ ] Configure centralized logging
- [ ] Set up monitoring and alerting
- [ ] Implement secrets management (AWS Secrets Manager, HashiCorp Vault)

---

## 📞 Support & Documentation

- **Full Setup Guide**: See `SETUP_COMPLETE.md`
- **Security Details**: See `Hospital-Frontend/SECURITY.md`
- **Production Deployment**: See `Hospital-Frontend/PRODUCTION_DEPLOYMENT.md`
- **API Reference**: See inline comments in `Hospital-Backend/src/index.js`

---

## ✅ Verification Checklist

After starting the system, verify:

- [ ] Backend running on http://localhost:3000
- [ ] Frontend running on http://localhost:5174
- [ ] Database accessible via http://localhost:8080
- [ ] Can list patients: `curl http://localhost:3000/api/patients`
- [ ] Can view frontend UI
- [ ] No errors in console

---

**Last Updated**: 2025-11-27
**Status**: ✅ Complete and Ready for Development
