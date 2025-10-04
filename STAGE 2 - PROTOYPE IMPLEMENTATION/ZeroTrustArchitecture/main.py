"""
Zero Trust Architecture FastAPI Application
Fully integrates IAMService, MFA, Microsegmentation, and Secure Proxy
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from loguru import logger

from src.database import get_db, init_database
from src.models import (
    UserCreate, UserResponse, LoginRequest, Token, DeviceCreate, DeviceResponse, User, Device,
    SecurityEventCreate, SecurityEventResponse
)
from src.identity.iam_service import IAMService, MicrosegmentationService, SecureAccessProxyService

# ----------------------
# Global Service Instances
# ----------------------
iam_service: IAMService = None
microsegmentation_service: MicrosegmentationService = None
proxy_service: SecureAccessProxyService = None

security = HTTPBearer()

# ----------------------
# Background Monitoring Task
# ----------------------
async def background_monitoring_task():
    while True:
        try:
            logger.debug("Background monitoring running...")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Background monitoring error: {e}")
            await asyncio.sleep(10)

# ----------------------
# Lifespan (startup/shutdown)
# ----------------------
async def lifespan(app: FastAPI):
    logger.info("Starting Zero Trust Architecture app...")
    init_database()

    global iam_service, microsegmentation_service, proxy_service
    iam_service = IAMService(secret_key="zero-trust-secret-key")
    microsegmentation_service = MicrosegmentationService()
    proxy_service = SecureAccessProxyService()

    asyncio.create_task(background_monitoring_task())
    yield
    logger.info("Shutting down Zero Trust Architecture app")

# ----------------------
# FastAPI App
# ----------------------
app = FastAPI(
    title="Zero Trust Architecture",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# Auth Helpers
# ----------------------
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security),
                 db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = iam_service.verify_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = iam_service.get_user_by_session(db, payload.get("session_id", ""))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ----------------------
# Health Check
# ----------------------
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "monitoring": "healthy"
        }
    }

# ----------------------
# User Registration & Login
# ----------------------
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return iam_service.create_user(
        db, user_data.username, user_data.email, user_data.password,
        user_data.full_name, user_data.department, user_data.role
    )

@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = iam_service.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Handle MFA requirement
    if user.is_mfa_enabled and not login_data.mfa_token:
        return {"mfa_required": True}

    if user.is_mfa_enabled:
        if not iam_service.verify_mfa_token(user.mfa_secret, login_data.mfa_token):
            raise HTTPException(status_code=401, detail="Invalid MFA token")

    session = iam_service.create_user_session(
        db, user, login_data.device_id, "127.0.0.1", "ZeroTrust-Client"
    )
    token_data = {"sub": user.username, "session_id": session.session_id}
    access_token = iam_service.create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": iam_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/api/auth/logout")
async def logout(current_user=Depends(verify_token), db: Session = Depends(get_db)):
    sessions = db.query(User).filter(User.id == current_user.id).all()
    for s in sessions:
        iam_service.invalidate_session(db, s.session_id)
    return {"message": "Logged out successfully"}

# ----------------------
# MFA Endpoints
# ----------------------
@app.post("/api/auth/mfa/enable")
async def enable_mfa(current_user=Depends(verify_token), db: Session = Depends(get_db)):
    secret = iam_service.enable_mfa(db, current_user.id)
    qr_url = iam_service.get_mfa_qr_code_url(current_user.email, secret)
    return {"mfa_secret": secret, "qr_url": qr_url}

@app.post("/api/auth/mfa/disable")
async def disable_mfa(current_user=Depends(verify_token), db: Session = Depends(get_db)):
    iam_service.disable_mfa(db, current_user.id)
    return {"message": "MFA disabled successfully"}

# ----------------------
# Device Management
# ----------------------
@app.post("/api/devices/register", response_model=DeviceResponse)
async def register_device(device_data: DeviceCreate, db: Session = Depends(get_db),
                          current_user=Depends(verify_token)):
    # Check if device already exists
    existing_device = db.query(Device).filter(Device.device_id == device_data.device_id).first()
    if existing_device:
        # Update existing device with new information
        existing_device.device_name = device_data.device_name
        existing_device.device_type = device_data.device_type
        existing_device.mac_address = device_data.mac_address
        existing_device.ip_address = device_data.ip_address
        existing_device.os_version = device_data.os_version
        existing_device.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_device)
        return existing_device
    
    # Create new device
    device = Device(
        device_id=device_data.device_id,
        device_name=device_data.device_name,
        device_type=device_data.device_type,
        mac_address=device_data.mac_address,
        ip_address=device_data.ip_address,
        os_version=device_data.os_version,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

@app.get("/api/devices")
async def list_devices(db: Session = Depends(get_db), current_user=Depends(verify_token)):
    devices = db.query(Device).all()
    return [dict(
        device_id=d.device_id,
        device_name=d.device_name,
        device_type=d.device_type,
        ip_address=d.ip_address,
        os_version=d.os_version,
        trust_score=d.trust_score,
        is_compliant=d.is_compliant,
        is_quarantined=d.is_quarantined,
        last_seen=d.last_seen.isoformat() if d.last_seen else None
    ) for d in devices]

# ----------------------
# Microsegmentation Firewall
# ----------------------
@app.post("/api/devices/{device_id}/firewall")
async def generate_firewall_rules(device_id: str, db: Session = Depends(get_db),
                                  current_user=Depends(verify_token)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    rules = microsegmentation_service.generate_firewall_rules(device, current_user)
    return rules

# ----------------------
# Secure Access Proxy
# ----------------------
@app.post("/api/proxy/session")
async def create_proxy_session(device_id: str, target_resource: str,
                               db: Session = Depends(get_db),
                               current_user=Depends(verify_token)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    session = proxy_service.create_proxy_session(current_user, device, target_resource)
    return session

# ----------------------
# Telemetry Endpoints
# ----------------------
@app.post("/api/telemetry")
async def receive_telemetry(telemetry_data: Dict[str, Any]):
    """Receive telemetry data from devices"""
    logger.debug(f"Received telemetry from device: {telemetry_data.get('device_id')}")
    # In a real implementation, this would store telemetry data
    # For simulation purposes, we just acknowledge receipt
    return {"status": "received", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/heartbeat")
async def receive_heartbeat(heartbeat_data: Dict[str, Any]):
    """Receive heartbeat from devices"""
    logger.debug(f"Heartbeat from device: {heartbeat_data.get('device_id')}")
    return {"status": "acknowledged", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/devices/{device_id}/telemetry")
async def get_device_telemetry(device_id: str, db: Session = Depends(get_db),
                               current_user=Depends(verify_token)):
    """Get telemetry data for a specific device"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Return mock telemetry data for simulation
    return {
        "device_id": device_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "online",
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 34.1
    }

# ----------------------
# Security Events
# ----------------------
@app.post("/api/events")
async def create_security_event(event_data: SecurityEventCreate, db: Session = Depends(get_db)):
    """Create a new security event"""
    import uuid
    from src.models import SecurityEvent
    
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_data.event_type,
        device_id=event_data.device_id,
        user_id=event_data.user_id,
        threat_level=event_data.threat_level,
        confidence_score=event_data.confidence_score,
        description=event_data.description,
        raw_data=event_data.raw_data
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    logger.info(f"Security event created: {event.event_type} (ID: {event.event_id})")
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "threat_level": event.threat_level,
        "status": "created",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/events")
async def list_security_events(db: Session = Depends(get_db), current_user=Depends(verify_token)):
    """List all security events"""
    from src.models import SecurityEvent
    events = db.query(SecurityEvent).order_by(SecurityEvent.created_at.desc()).limit(100).all()
    return [{
        "event_id": event.event_id,
        "event_type": event.event_type,
        "threat_level": event.threat_level,
        "confidence_score": event.confidence_score,
        "description": event.description,
        "is_resolved": event.is_resolved,
        "created_at": event.created_at.isoformat()
    } for event in events]

# ----------------------
# Dashboard Endpoint
# ----------------------
@app.get("/api/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """Get dashboard metrics and data"""
    from src.models import SecurityEvent
    from datetime import timedelta

    # Get device statistics
    total_devices = db.query(Device).count()
    compliant_devices = db.query(Device).filter(Device.is_compliant == True).count()
    quarantined_devices = db.query(Device).filter(Device.is_quarantined == True).count()
    online_devices = total_devices - quarantined_devices  # Simplified for demo

    # Get security events from last 24 hours
    yesterday = datetime.utcnow() - timedelta(hours=24)
    security_events_24h = db.query(SecurityEvent).filter(SecurityEvent.created_at >= yesterday).count()
    critical_events = db.query(SecurityEvent).filter(
        SecurityEvent.threat_level == "critical",
        SecurityEvent.created_at >= yesterday
    ).count()

    # Calculate metrics
    compliance_rate = (compliant_devices / total_devices * 100) if total_devices > 0 else 0
    average_trust_score = 85.5  # Mock value for demo

    return {
        "summary_metrics": {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": total_devices - online_devices,
            "compliant_devices": compliant_devices,
            "quarantined_devices": quarantined_devices,
            "security_events_24h": security_events_24h,
            "critical_events": critical_events,
            "average_trust_score": average_trust_score,
            "compliance_rate": compliance_rate
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# ----------------------
# Run Server
# ----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8004, log_level="info")
