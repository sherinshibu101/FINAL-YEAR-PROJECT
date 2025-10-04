# 🚀 Quick Start Guide - Zero Trust Architecture

## ⚠️ Fixing the Cryptography Installation Error

If you encountered the cryptography version error, here are **3 easy solutions**:

### Solution 1: Use the Minimal Requirements (Recommended)
```powershell
pip install -r requirements-minimal.txt
```

### Solution 2: Use the PowerShell Setup Script  
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

### Solution 3: Install Core Packages Manually
```powershell
# Install core packages one by one
pip install fastapi uvicorn pydantic sqlalchemy
pip install python-jose[cryptography] passlib[bcrypt] 
pip install requests pandas numpy scikit-learn plotly
pip install redis python-dotenv pyyaml loguru joblib psutil pyotp
```

---

## 🎯 Running the Demo (After Installing Dependencies)

### Step 1: Start the Zero Trust System
```powershell
python main.py
```

### Step 2: Run the Demo (New Terminal)
```powershell
python demo.py
```

---

## 🔧 Alternative: One-Command Setup

If you're having package conflicts, try this approach:

```powershell
# Create a fresh virtual environment
python -m venv fresh_env
fresh_env\Scripts\Activate.ps1

# Install only essential packages
pip install fastapi uvicorn sqlalchemy pydantic requests loguru

# Try running with minimal functionality
python main.py
```

---

## 📊 What the Demo Shows

The demo will demonstrate:

1. **🔐 Authentication System** - Login with admin/admin123
2. **📱 Device Registration** - Hospital computers, laptops, IoT devices  
3. **🛡️ Threat Detection** - ML-based security analysis
4. **⚡ Automated Response** - Device quarantine and isolation
5. **📈 Dashboard Metrics** - Real-time security visualization

---

## 🆘 Still Having Issues?

### Check Python Version
```powershell
python --version
# Should be 3.8 or higher
```

### Upgrade Pip
```powershell
python -m pip install --upgrade pip
```

### Install from Source (Last Resort)
```powershell
git clone https://github.com/pyca/cryptography.git
cd cryptography
pip install -e .
```

---

## 🎪 Demo Output Preview

When the demo runs successfully, you'll see:

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    ZERO TRUST ARCHITECTURE DEMONSTRATION              ║
║                      Healthcare Security Simulation                   ║
╠═══════════════════════════════════════════════════════════════════════╣
║  This demo showcases a complete Zero Trust security system with:      ║
║  • Identity & Access Management                                       ║
║  • Endpoint Monitoring & Agent Telemetry                             ║
║  • Central Analysis & Threat Intelligence                             ║
║  • Automated Response & Incident Management                           ║
║  • Device & Data Protection                                           ║
║  • Centralized Visibility & Monitoring                               ║
╚═══════════════════════════════════════════════════════════════════════╝

🔧 PHASE 0: System Health Check
✅ System Status: healthy
   Database: connected
   Redis: connected
   Monitoring: active

🔐 PHASE 1: Identity & Access Management Demo
✅ Admin login successful
   Token expires in: 1800 seconds
✅ New user registered successfully

📊 PHASE 2: Device Registration & Monitoring Demo
✅ Device registered: Demo Hospital Computer 1
✅ Device registered: Demo Doctor Laptop 1  
✅ Device registered: Demo Patient Monitor 1
```

And much more! The demo takes about 2-3 minutes to complete and shows the entire zero trust workflow.

---

## 🌐 Access Points After Demo

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health  
- **Dashboard Data**: http://localhost:8000/api/dashboard

Happy hacking! 🎉