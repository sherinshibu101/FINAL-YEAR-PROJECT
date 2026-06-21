"""
Identity and Access Management Service for Zero Trust Architecture
"""

import secrets
import pyotp
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from loguru import logger

from ..models import User, UserSession, Device
from ..database import get_db


class IAMService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password using PBKDF2"""
        # Generate a random salt
        salt = os.urandom(32)
        # Hash the password with PBKDF2
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        # Combine salt and hash, encode as hex
        return salt.hex() + pwdhash.hex()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            # Extract salt (first 64 hex chars = 32 bytes) and hash (rest)
            salt = bytes.fromhex(hashed_password[:64])
            stored_hash = bytes.fromhex(hashed_password[64:])
            
            # Hash the provided password with the extracted salt
            pwdhash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
            
            # Compare the hashes
            return pwdhash == stored_hash
        except (ValueError, IndexError):
            return False
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"Login attempt with invalid username: {username}")
            return None
        
        # Check if user is locked due to failed attempts
        if user.locked_until and user.locked_until > datetime.utcnow():
            logger.warning(f"Login attempt for locked user: {username}")
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.locked_until}"
            )
        
        if not self.verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 3:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                logger.warning(f"Account locked due to failed attempts: {username}")
            db.commit()
            return None
        
        # Reset failed attempts on successful login
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()
        
        return user
    
    def generate_mfa_secret(self) -> str:
        """Generate a new MFA secret for TOTP"""
        return pyotp.random_base32()
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """Verify a MFA TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def get_mfa_qr_code_url(self, user_email: str, secret: str) -> str:
        """Generate QR code URL for MFA setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name="ZeroTrust Healthcare"
        )
    
    def create_user_session(self, db: Session, user: User, device_id: Optional[str] = None, 
                           ip_address: str = "unknown", user_agent: str = "unknown") -> UserSession:
        """Create a new user session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Get device if provided
        device = None
        if device_id:
            device = db.query(Device).filter(Device.device_id == device_id).first()
        
        session = UserSession(
            session_id=session_id,
            user_id=user.id,
            device_id=device.id if device else None,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(session)
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created session for user {user.username} from {ip_address}")
        return session
    
    def invalidate_session(self, db: Session, session_id: str) -> bool:
        """Invalidate a user session"""
        session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
        if session:
            session.is_active = False
            db.commit()
            logger.info(f"Invalidated session {session_id}")
            return True
        return False
    
    def get_active_session(self, db: Session, session_id: str) -> Optional[UserSession]:
        """Get an active session"""
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if session:
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.commit()
        
        return session
    
    def create_user(self, db: Session, username: str, email: str, password: str, 
                   full_name: str, department: str, role: str) -> User:
        """Create a new user"""
        # Check if user already exists
        if db.query(User).filter(User.username == username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            department=department,
            role=role
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created new user: {username}")
        return user
    
    def enable_mfa(self, db: Session, user_id: int) -> str:
        """Enable MFA for a user and return the secret"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA already enabled"
            )
        
        secret = self.generate_mfa_secret()
        user.mfa_secret = secret
        user.is_mfa_enabled = True
        db.commit()
        
        logger.info(f"Enabled MFA for user {user.username}")
        return secret
    
    def disable_mfa(self, db: Session, user_id: int) -> bool:
        """Disable MFA for a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_mfa_enabled = False
        user.mfa_secret = None
        db.commit()
        
        logger.info(f"Disabled MFA for user {user.username}")
        return True
    
    def check_user_permissions(self, user: User, required_role: str) -> bool:
        """Check if user has required permissions"""
        role_hierarchy = {
            "user": 1,
            "admin": 2,
            "security_admin": 3,
            "system_admin": 4
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def get_user_by_session(self, db: Session, session_id: str) -> Optional[User]:
        """Get user by session ID"""
        session = self.get_active_session(db, session_id)
        if session:
            return db.query(User).filter(User.id == session.user_id).first()
        return None


# Microsegmentation Service
class MicrosegmentationService:
    def __init__(self):
        self.network_segments = {
            "admin": {"subnets": ["10.0.1.0/24"], "ports": [22, 443, 3389]},
            "clinical": {"subnets": ["10.0.2.0/24"], "ports": [80, 443, 8080]},
            "iot": {"subnets": ["10.0.3.0/24"], "ports": [443, 8883, 1883]},
            "guest": {"subnets": ["10.0.4.0/24"], "ports": [80, 443]}
        }
    
    def get_segment_for_device(self, device: Device, user: User) -> str:
        """Determine appropriate network segment for device/user combination"""
        if user.role in ["system_admin", "security_admin"]:
            return "admin"
        elif device.device_type == "iot_device":
            return "iot"
        elif user.department in ["clinical", "nursing", "pharmacy"]:
            return "clinical"
        else:
            return "guest"
    
    def validate_network_access(self, source_segment: str, dest_segment: str, port: int) -> bool:
        """Validate if network access is allowed between segments"""
        # Define allowed inter-segment communication
        allowed_flows = {
            "admin": ["admin", "clinical", "iot", "guest"],
            "clinical": ["clinical", "iot"],
            "iot": ["iot"],
            "guest": ["guest"]
        }
        
        if dest_segment not in allowed_flows.get(source_segment, []):
            return False
        
        # Check if port is allowed for destination segment
        allowed_ports = self.network_segments.get(dest_segment, {}).get("ports", [])
        return port in allowed_ports
    
    def generate_firewall_rules(self, device: Device, user: User) -> Dict[str, Any]:
        """Generate firewall rules for a device"""
        segment = self.get_segment_for_device(device, user)
        segment_config = self.network_segments.get(segment, {})
        
        allowed_ports = segment_config.get("ports", [])
        total_blocked = 65535 - len(allowed_ports)

        rules = {
            "device_id": device.device_id,
            "segment": segment,
            "allowed_subnets": segment_config.get("subnets", []),
            "allowed_ports": allowed_ports,
            "blocked_ports_count": total_blocked,
            "blocked_ports_summary": f"All ports except {allowed_ports} ({total_blocked} ports blocked)",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return rules


# Secure Access Proxy Service
class SecureAccessProxyService:
    def __init__(self):
        self.proxy_rules = {}
    
    def create_proxy_session(self, user: User, device: Device, target_resource: str) -> Dict[str, Any]:
        """Create a secure proxy session"""
        session_id = secrets.token_urlsafe(16)
        
        proxy_session = {
            "session_id": session_id,
            "user_id": user.id,
            "device_id": device.id,
            "target_resource": target_resource,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=2),
            "is_active": True
        }
        
        self.proxy_rules[session_id] = proxy_session
        logger.info(f"Created proxy session {session_id} for user {user.username}")
        
        return proxy_session
    
    def validate_proxy_access(self, session_id: str, request_path: str) -> bool:
        """Validate if proxy access is allowed"""
        session = self.proxy_rules.get(session_id)
        if not session or not session["is_active"]:
            return False
        
        if session["expires_at"] < datetime.utcnow():
            session["is_active"] = False
            return False
        
        # Validate if the request path matches allowed resource
        return request_path.startswith(session["target_resource"])
    
    def terminate_proxy_session(self, session_id: str) -> bool:
        """Terminate a proxy session"""
        if session_id in self.proxy_rules:
            self.proxy_rules[session_id]["is_active"] = False
            logger.info(f"Terminated proxy session {session_id}")
            return True
        return False