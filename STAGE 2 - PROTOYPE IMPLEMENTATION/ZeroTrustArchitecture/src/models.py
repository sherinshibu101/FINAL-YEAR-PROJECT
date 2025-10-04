"""
Database models for Zero Trust Architecture
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from pydantic import BaseModel

Base = declarative_base()


class DeviceType(str, Enum):
    HOSPITAL_COMPUTER = "hospital_computer"
    HOSPITAL_LAPTOP = "hospital_laptop"
    IOT_DEVICE = "iot_device"


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseAction(str, Enum):
    ISOLATE_DEVICE = "isolate_device"
    REVOKE_ACCESS = "revoke_access"
    QUARANTINE = "quarantine"
    ALERT_ADMIN = "alert_admin"


# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    devices = relationship("Device", back_populates="owner")
    sessions = relationship("UserSession", back_populates="user")


class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    device_name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)  # DeviceType enum
    mac_address = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    is_compliant = Column(Boolean, default=False)
    is_quarantined = Column(Boolean, default=False)
    trust_score = Column(Float, default=0.0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="devices")
    events = relationship("SecurityEvent", back_populates="device")
    posture_checks = relationship("DevicePosture", back_populates="device")


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class SecurityEvent(Base):
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    threat_level = Column(String, nullable=False)  # ThreatLevel enum
    confidence_score = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="events")
    responses = relationship("ResponseActionModel", back_populates="event")


class ResponseActionModel(Base):
    __tablename__ = "response_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(String, unique=True, index=True, nullable=False)
    event_id = Column(Integer, ForeignKey("security_events.id"), nullable=False)
    action_type = Column(String, nullable=False)  # ResponseAction enum
    description = Column(Text, nullable=False)
    is_automated = Column(Boolean, default=True)
    status = Column(String, default="pending")  # pending, executed, failed
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("SecurityEvent", back_populates="responses")


class DevicePosture(Base):
    __tablename__ = "device_posture"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    antivirus_enabled = Column(Boolean, default=False)
    firewall_enabled = Column(Boolean, default=False)
    os_updated = Column(Boolean, default=False)
    encryption_enabled = Column(Boolean, default=False)
    compliance_score = Column(Float, default=0.0)
    last_check = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship("Device", back_populates="posture_checks")


class ThreatIntelligence(Base):
    __tablename__ = "threat_intelligence"
    
    id = Column(Integer, primary_key=True, index=True)
    ioc_type = Column(String, nullable=False)  # ip, domain, hash, etc.
    ioc_value = Column(String, nullable=False, index=True)
    threat_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


# Pydantic Models for API
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    department: str
    role: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    department: str
    role: str
    is_active: bool
    is_mfa_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    device_id: str
    device_name: str
    device_type: DeviceType
    mac_address: str
    ip_address: Optional[str] = None
    os_version: Optional[str] = None


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: str
    device_type: str
    mac_address: str
    ip_address: Optional[str]
    is_compliant: bool
    is_quarantined: bool
    trust_score: float
    last_seen: Optional[datetime]

    class Config:
        from_attributes = True


class SecurityEventCreate(BaseModel):
    event_type: str
    device_id: Optional[int] = None
    user_id: Optional[int] = None
    threat_level: ThreatLevel
    confidence_score: float
    description: str
    raw_data: Optional[dict] = None


class SecurityEventResponse(BaseModel):
    id: int
    event_id: str
    event_type: str
    threat_level: str
    confidence_score: float
    description: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str
    device_id: Optional[str] = None


class MFAVerifyRequest(BaseModel):
    username: str
    mfa_code: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class DevicePostureUpdate(BaseModel):
    device_id: int
    antivirus_enabled: bool
    firewall_enabled: bool
    os_updated: bool
    encryption_enabled: bool