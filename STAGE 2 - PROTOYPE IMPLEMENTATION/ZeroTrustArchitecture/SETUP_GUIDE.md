# 🚀 **SecureHealthCare: Zero Trust Architecture - Complete Setup Guide**

## 🎯 **Project Overview**

This prototype demonstrates a complete Zero Trust Architecture specifically designed for healthcare systems. It implements the "never trust, always verify" principle to protect patient data and critical medical infrastructure.

---

## 📋 **Prerequisites**

- **Python 3.8+** (Download from [python.org](https://python.org))
- **Git** (optional, for cloning)
- **2GB RAM minimum, 4GB recommended**
- **500MB free storage space**

---

## ⚡ **Quick Setup (5 Minutes)**

### **Step 1: Download/Clone Project**
```bash
# Option A: Clone from repository
git clone <your-repo-url>
cd ZeroTrustArchitecture

# Option B: Extract from ZIP file
# Extract ZeroTrustArchitecture.zip to your desired location
# cd ZeroTrustArchitecture
```

### **Step 2: Create Virtual Environment (Recommended)**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux  
python3 -m venv venv
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Run the System**

**Terminal 1 - Start Server:**
```bash
python main.py
```
Wait for: `INFO: Uvicorn running on http://localhost:8004`

**Terminal 2 - Run Demo:**
```bash
python demo.py
```

### **Step 5: View Results**
- **Demo Output**: Watch the 7-phase Zero Trust demonstration in Terminal 2
- **API Documentation**: Open `http://localhost:8004/docs` in your browser
- **Health Check**: Visit `http://localhost:8004/health`

---

## 🏗️ **Essential Files Structure**

```
ZeroTrustArchitecture/
├── main.py              # 🖥️ Main FastAPI server
├── demo.py              # 🎬 Demo script (7 phases)
├── requirements.txt     # 📦 Dependencies
├── SETUP_GUIDE.md      # 📖 This setup guide
├── config/
│   └── config.yaml     # ⚙️ Configuration
├── data/               # 💾 Database (auto-created)
└── src/                # 🔧 Core modules
    ├── models.py       # Database models
    ├── database.py     # Database setup
    ├── identity/       # Authentication
    ├── device_protection/
    ├── endpoint_monitoring/
    ├── central_analysis/
    ├── response/
    └── visibility/
```

---

## 🎬 **The 7-Phase Demo Explanation**

### **Phase 1: Identity Verification** 🔐
- Admin login + Multi-factor authentication
- JWT token generation (30-minute sessions)

### **Phase 2: Network Access Control** 🌐
- Microsegmentation by user role
- Firewall rules (specific ports allowed/blocked)

### **Phase 3: Device & Data Protection** 🛡️
- Device security assessment
- HIPAA-compliant encryption verification

### **Phase 4: Visibility** 👁️
- Centralized logging setup
- SIEM integration simulation

### **Phase 5: Endpoint Monitoring** 📊
- Deploy agents on hospital devices
- Real-time heartbeat and telemetry

### **Phase 6: Central Analysis** 🎯
- Security event correlation
- Threat intelligence integration

### **Phase 7: Response System** ⚡
- Automated incident response
- Device quarantine and access revocation

---

## 🔧 **Troubleshooting**

### **Port Already in Use**
```bash
# Find process using port 8004
netstat -ano | findstr :8004
# Kill the process (replace PID)
taskkill /PID <process_id> /F
```

### **Module Not Found**
```bash
pip install -r requirements.txt
```

### **Database Issues**
```bash
# Delete database (will be recreated)
rm data/zerotrust.db     # Linux/Mac
del data\zerotrust.db    # Windows
```

---

## ✅ **Success Indicators**

✅ Server starts on port 8004  
✅ All 7 phases complete with green checkmarks  
✅ API documentation loads at `/docs`  
✅ No red error messages in terminal  

---

## 🏥 **Healthcare Features**

- **Hospital Computers**: Patient room workstations
- **Doctor Laptops**: Mobile clinical devices  
- **IoT Medical Devices**: Patient monitors, ventilators
- **HIPAA Compliance**: AES-256 encryption, audit trails
- **Threat Scenarios**: Ransomware, credential theft, network intrusions

---

## 🎓 **Academic Project Info**

**Project**: SecureHealthCare: Zero Trust Approach  
**Course**: 19CSE495 PROJECT PHASE-1  
**Institution**: Amrita School of Computing  
**Team**: D12 Group  

**🎉 This prototype demonstrates a complete, working Zero Trust Architecture for healthcare security!**
