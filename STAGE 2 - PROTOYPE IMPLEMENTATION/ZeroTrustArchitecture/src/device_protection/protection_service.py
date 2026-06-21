"""
Device and Data Protection Service for Zero Trust Architecture
Handles device posture assessment and encryption management
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from sqlalchemy.orm import Session
from loguru import logger
import redis

from ..models import Device, DevicePosture, User
from ..database import db_manager


class DevicePostureService:
    """Service for assessing and managing device security posture"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        
        # Define compliance requirements
        self.compliance_requirements = {
            "hospital_computer": {
                "antivirus_required": True,
                "firewall_required": True,
                "encryption_required": True,
                "os_updates_required": True,
                "min_os_version": {
                    "Windows": "10.0.19041",  # Windows 10 20H1
                    "Linux": "5.4",
                    "macOS": "10.15"
                },
                "required_software": ["endpoint_agent", "backup_client"],
                "prohibited_software": ["teamviewer", "anydesk", "vnc"],
                "network_requirements": {
                    "vpn_required": False,
                    "allowed_ports": [80, 443, 22, 3389, 5985, 5986],
                    "blocked_protocols": ["p2p", "torrent"]
                }
            },
            "hospital_laptop": {
                "antivirus_required": True,
                "firewall_required": True,
                "encryption_required": True,
                "os_updates_required": True,
                "min_os_version": {
                    "Windows": "10.0.19041",
                    "Linux": "5.4",
                    "macOS": "10.15"
                },
                "required_software": ["endpoint_agent", "vpn_client"],
                "prohibited_software": ["teamviewer", "anydesk", "vnc", "bittorrent"],
                "network_requirements": {
                    "vpn_required": True,
                    "allowed_ports": [80, 443, 993, 587],
                    "blocked_protocols": ["p2p", "torrent"]
                }
            },
            "iot_device": {
                "antivirus_required": False,  # Many IoT devices don't support AV
                "firewall_required": True,
                "encryption_required": True,
                "os_updates_required": True,
                "min_firmware_version": "1.0.0",
                "required_certificates": ["device_cert", "ca_cert"],
                "network_requirements": {
                    "vpn_required": False,
                    "allowed_ports": [443, 8883, 1883],  # HTTPS, MQTT over SSL, MQTT
                    "blocked_protocols": ["ssh", "telnet", "ftp"]
                }
            }
        }
        
        logger.info("Device Posture Service initialized")
    
    def assess_device_posture(self, db: Session, device_id: str, 
                            telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess device security posture based on telemetry"""
        try:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                logger.error(f"Device not found: {device_id}")
                return {}
            
            device_type = device.device_type
            requirements = self.compliance_requirements.get(device_type, {})
            
            assessment_results = {
                "device_id": device_id,
                "device_type": device_type,
                "assessment_time": datetime.utcnow().isoformat(),
                "compliance_checks": {},
                "overall_score": 0.0,
                "compliance_status": "unknown",
                "recommendations": [],
                "risk_factors": []
            }
            
            # Perform compliance checks
            compliance_checks = self._perform_compliance_checks(
                requirements, telemetry_data, device
            )
            assessment_results["compliance_checks"] = compliance_checks
            
            # Calculate overall compliance score
            overall_score = self._calculate_compliance_score(compliance_checks)
            assessment_results["overall_score"] = overall_score
            
            # Determine compliance status
            if overall_score >= 0.9:
                assessment_results["compliance_status"] = "fully_compliant"
            elif overall_score >= 0.7:
                assessment_results["compliance_status"] = "mostly_compliant"
            elif overall_score >= 0.5:
                assessment_results["compliance_status"] = "partially_compliant"
            else:
                assessment_results["compliance_status"] = "non_compliant"
            
            # Generate recommendations
            assessment_results["recommendations"] = self._generate_recommendations(
                compliance_checks, requirements
            )
            
            # Identify risk factors
            assessment_results["risk_factors"] = self._identify_risk_factors(
                compliance_checks, telemetry_data
            )
            
            # Update device posture in database
            self._update_device_posture_record(db, device, assessment_results)
            
            # Cache assessment results
            self.redis_client.setex(
                f"posture_assessment:{device_id}",
                3600,  # 1 hour cache
                json.dumps(assessment_results)
            )
            
            logger.debug(f"Assessed posture for device {device_id}: {assessment_results['compliance_status']}")
            return assessment_results
            
        except Exception as e:
            logger.error(f"Error assessing device posture: {e}")
            return {}
    
    def _perform_compliance_checks(self, requirements: Dict[str, Any], 
                                 telemetry_data: Dict[str, Any],
                                 device: Device) -> Dict[str, Any]:
        """Perform individual compliance checks"""
        checks = {}
        
        # Check antivirus status
        if requirements.get("antivirus_required", False):
            compliance_status = telemetry_data.get("compliance_status", {})
            checks["antivirus"] = {
                "required": True,
                "compliant": compliance_status.get("antivirus_running", False),
                "details": "Antivirus software must be running and up-to-date"
            }
        
        # Check firewall status
        if requirements.get("firewall_required", False):
            compliance_status = telemetry_data.get("compliance_status", {})
            checks["firewall"] = {
                "required": True,
                "compliant": compliance_status.get("firewall_enabled", False),
                "details": "Host firewall must be enabled"
            }
        
        # Check encryption
        if requirements.get("encryption_required", False):
            compliance_status = telemetry_data.get("compliance_status", {})
            checks["encryption"] = {
                "required": True,
                "compliant": compliance_status.get("encryption_enabled", False),
                "details": "Full disk encryption must be enabled"
            }
        
        # Check OS updates
        if requirements.get("os_updates_required", False):
            compliance_status = telemetry_data.get("compliance_status", {})
            checks["os_updates"] = {
                "required": True,
                "compliant": compliance_status.get("os_up_to_date", False),
                "details": "Operating system must be up-to-date"
            }
        
        # Check minimum OS version
        min_versions = requirements.get("min_os_version", {})
        if min_versions:
            system_info = telemetry_data.get("system_info", {})
            os_name = system_info.get("os", "Unknown")
            current_version = system_info.get("os_version", "0.0.0")
            required_version = min_versions.get(os_name)
            
            if required_version:
                version_compliant = self._compare_versions(current_version, required_version) >= 0
                checks["os_version"] = {
                    "required": True,
                    "compliant": version_compliant,
                    "details": f"OS version must be {required_version} or newer (current: {current_version})",
                    "current_version": current_version,
                    "required_version": required_version
                }
        
        # Check required software
        required_software = requirements.get("required_software", [])
        if required_software:
            processes = telemetry_data.get("running_processes", [])
            process_names = [p.get("name", "").lower() for p in processes]
            
            for software in required_software:
                software_running = any(software.lower() in name for name in process_names)
                checks[f"software_{software}"] = {
                    "required": True,
                    "compliant": software_running,
                    "details": f"Required software '{software}' must be running"
                }
        
        # Check prohibited software
        prohibited_software = requirements.get("prohibited_software", [])
        if prohibited_software:
            processes = telemetry_data.get("running_processes", [])
            process_names = [p.get("name", "").lower() for p in processes]
            
            for software in prohibited_software:
                software_found = any(software.lower() in name for name in process_names)
                checks[f"prohibited_{software}"] = {
                    "required": True,
                    "compliant": not software_found,
                    "details": f"Prohibited software '{software}' must not be running"
                }
        
        # Check network requirements
        network_reqs = requirements.get("network_requirements", {})
        if network_reqs:
            connections = telemetry_data.get("network_connections", [])
            
            # Check for prohibited ports
            allowed_ports = network_reqs.get("allowed_ports", [])
            if allowed_ports:
                listening_ports = [
                    conn.get("local_port") for conn in connections 
                    if conn.get("status") == "LISTEN"
                ]
                unauthorized_ports = [
                    port for port in listening_ports 
                    if port not in allowed_ports and port > 1024
                ]
                
                checks["network_ports"] = {
                    "required": True,
                    "compliant": len(unauthorized_ports) == 0,
                    "details": f"Only allowed ports should be listening. Unauthorized: {unauthorized_ports}",
                    "unauthorized_ports": unauthorized_ports
                }
        
        return checks
    
    def _calculate_compliance_score(self, compliance_checks: Dict[str, Any]) -> float:
        """Calculate overall compliance score"""
        if not compliance_checks:
            return 0.0
        
        total_checks = len(compliance_checks)
        passed_checks = sum(1 for check in compliance_checks.values() if check.get("compliant", False))
        
        return passed_checks / total_checks if total_checks > 0 else 0.0
    
    def _generate_recommendations(self, compliance_checks: Dict[str, Any],
                                requirements: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on compliance check results"""
        recommendations = []
        
        for check_name, check_result in compliance_checks.items():
            if not check_result.get("compliant", True):
                if check_name == "antivirus":
                    recommendations.append("Install and enable antivirus software")
                elif check_name == "firewall":
                    recommendations.append("Enable host-based firewall")
                elif check_name == "encryption":
                    recommendations.append("Enable full disk encryption (BitLocker/FileVault/LUKS)")
                elif check_name == "os_updates":
                    recommendations.append("Install latest operating system updates")
                elif check_name == "os_version":
                    required_version = check_result.get("required_version", "latest")
                    recommendations.append(f"Upgrade operating system to version {required_version} or newer")
                elif check_name.startswith("software_"):
                    software_name = check_name.replace("software_", "")
                    recommendations.append(f"Install required software: {software_name}")
                elif check_name.startswith("prohibited_"):
                    software_name = check_name.replace("prohibited_", "")
                    recommendations.append(f"Remove prohibited software: {software_name}")
                elif check_name == "network_ports":
                    unauthorized_ports = check_result.get("unauthorized_ports", [])
                    if unauthorized_ports:
                        recommendations.append(f"Close unauthorized listening ports: {unauthorized_ports}")
        
        return recommendations
    
    def _identify_risk_factors(self, compliance_checks: Dict[str, Any],
                             telemetry_data: Dict[str, Any]) -> List[str]:
        """Identify security risk factors"""
        risk_factors = []
        
        # High CPU/Memory usage could indicate malware
        cpu_usage = telemetry_data.get("cpu_usage", 0)
        memory_usage = telemetry_data.get("memory_usage", 0)
        
        if cpu_usage > 90:
            risk_factors.append("Abnormally high CPU usage detected")
        if memory_usage > 90:
            risk_factors.append("Abnormally high memory usage detected")
        
        # Check for security events
        security_events = telemetry_data.get("security_events", [])
        if security_events:
            high_severity_events = [e for e in security_events if e.get("severity") in ["high", "critical"]]
            if high_severity_events:
                risk_factors.append(f"High severity security events detected: {len(high_severity_events)}")
        
        # Check for non-compliance
        non_compliant_checks = [
            name for name, result in compliance_checks.items()
            if not result.get("compliant", True)
        ]
        
        if len(non_compliant_checks) > 3:
            risk_factors.append("Multiple compliance violations detected")
        
        # Check for unusual network activity
        connections = telemetry_data.get("network_connections", [])
        external_connections = [
            conn for conn in connections
            if conn.get("remote_address") and not conn.get("remote_address").startswith("10.")
            and not conn.get("remote_address").startswith("192.168.")
            and not conn.get("remote_address").startswith("172.")
            and conn.get("remote_address") != "127.0.0.1"
        ]
        
        if len(external_connections) > 10:
            risk_factors.append("High number of external network connections")
        
        return risk_factors
    
    def _update_device_posture_record(self, db: Session, device: Device,
                                    assessment_results: Dict[str, Any]):
        """Update device posture record in database"""
        try:
            posture = db.query(DevicePosture).filter(DevicePosture.device_id == device.id).first()
            
            if not posture:
                posture = DevicePosture(device_id=device.id)
                db.add(posture)
            
            # Update posture fields from compliance checks
            compliance_checks = assessment_results.get("compliance_checks", {})
            
            posture.antivirus_enabled = compliance_checks.get("antivirus", {}).get("compliant", False)
            posture.firewall_enabled = compliance_checks.get("firewall", {}).get("compliant", False)
            posture.os_updated = compliance_checks.get("os_updates", {}).get("compliant", False)
            posture.encryption_enabled = compliance_checks.get("encryption", {}).get("compliant", False)
            posture.compliance_score = assessment_results.get("overall_score", 0.0)
            posture.last_check = datetime.utcnow()
            
            # Update device compliance status
            device.is_compliant = assessment_results.get("compliance_status") in ["fully_compliant", "mostly_compliant"]
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating device posture record: {e}")
            db.rollback()
    
    def _compare_versions(self, current: str, required: str) -> int:
        """Compare version strings (returns -1, 0, or 1)"""
        try:
            def version_tuple(v):
                return tuple(map(int, (v.split("."))))
            
            current_tuple = version_tuple(current)
            required_tuple = version_tuple(required)
            
            if current_tuple < required_tuple:
                return -1
            elif current_tuple > required_tuple:
                return 1
            else:
                return 0
        except:
            return 0  # Assume equal if parsing fails
    
    def get_device_posture_summary(self, db: Session) -> Dict[str, Any]:
        """Get summary of device posture across all devices"""
        try:
            summary = {
                "total_devices": 0,
                "compliant_devices": 0,
                "non_compliant_devices": 0,
                "compliance_rate": 0.0,
                "posture_breakdown": {
                    "fully_compliant": 0,
                    "mostly_compliant": 0,
                    "partially_compliant": 0,
                    "non_compliant": 0
                },
                "common_issues": {}
            }
            
            devices = db.query(Device).all()
            summary["total_devices"] = len(devices)
            
            for device in devices:
                # Get cached assessment if available
                assessment_key = f"posture_assessment:{device.device_id}"
                assessment_data = self.redis_client.get(assessment_key)
                
                if assessment_data:
                    assessment = json.loads(assessment_data)
                    status = assessment.get("compliance_status", "unknown")
                    
                    if status in summary["posture_breakdown"]:
                        summary["posture_breakdown"][status] += 1
                    
                    if status in ["fully_compliant", "mostly_compliant"]:
                        summary["compliant_devices"] += 1
                    else:
                        summary["non_compliant_devices"] += 1
                    
                    # Track common issues
                    compliance_checks = assessment.get("compliance_checks", {})
                    for check_name, check_result in compliance_checks.items():
                        if not check_result.get("compliant", True):
                            if check_name not in summary["common_issues"]:
                                summary["common_issues"][check_name] = 0
                            summary["common_issues"][check_name] += 1
            
            # Calculate compliance rate
            if summary["total_devices"] > 0:
                summary["compliance_rate"] = (summary["compliant_devices"] / summary["total_devices"]) * 100
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting device posture summary: {e}")
            return {}


class EncryptionService:
    """Service for managing encryption keys and data protection"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.master_key = self._load_or_generate_master_key()
        self.device_keys = {}  # Cache for device encryption keys
        
        logger.info("Encryption Service initialized")
    
    def _load_or_generate_master_key(self) -> bytes:
        """Load existing master key or generate new one"""
        try:
            # In production, this would be stored in a secure key management system
            key_file = "data/master_key.key"
            
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    return f.read()
            else:
                # Generate new master key
                key = Fernet.generate_key()
                os.makedirs("data", exist_ok=True)
                with open(key_file, "wb") as f:
                    f.write(key)
                logger.info("Generated new master key")
                return key
                
        except Exception as e:
            logger.error(f"Error loading/generating master key: {e}")
            # Fallback to a fixed key (NOT for production!)
            return base64.urlsafe_b64encode(b"zero_trust_demo_key_32_bytes!")
    
    def generate_device_key(self, device_id: str) -> str:
        """Generate encryption key for a specific device"""
        try:
            # Generate device-specific key
            device_key = Fernet.generate_key()
            
            # Encrypt the device key with master key
            master_fernet = Fernet(self.master_key)
            encrypted_device_key = master_fernet.encrypt(device_key)
            
            # Store encrypted key in Redis
            self.redis_client.setex(
                f"device_key:{device_id}",
                86400 * 30,  # 30 days
                base64.b64encode(encrypted_device_key).decode()
            )
            
            # Cache decrypted key temporarily
            self.device_keys[device_id] = device_key
            
            logger.info(f"Generated encryption key for device {device_id}")
            return base64.b64encode(device_key).decode()
            
        except Exception as e:
            logger.error(f"Error generating device key: {e}")
            return ""
    
    def get_device_key(self, device_id: str) -> Optional[bytes]:
        """Get encryption key for a specific device"""
        try:
            # Check cache first
            if device_id in self.device_keys:
                return self.device_keys[device_id]
            
            # Get encrypted key from Redis
            encrypted_key_b64 = self.redis_client.get(f"device_key:{device_id}")
            if not encrypted_key_b64:
                return None
            
            encrypted_key = base64.b64decode(encrypted_key_b64)
            
            # Decrypt with master key
            master_fernet = Fernet(self.master_key)
            device_key = master_fernet.decrypt(encrypted_key)
            
            # Cache for future use
            self.device_keys[device_id] = device_key
            
            return device_key
            
        except Exception as e:
            logger.error(f"Error getting device key: {e}")
            return None
    
    def encrypt_data(self, data: str, device_id: str) -> Optional[str]:
        """Encrypt data using device-specific key"""
        try:
            device_key = self.get_device_key(device_id)
            if not device_key:
                device_key = self.generate_device_key(device_id)
                if not device_key:
                    return None
                device_key = base64.b64decode(device_key)
            
            fernet = Fernet(device_key)
            encrypted_data = fernet.encrypt(data.encode())
            
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str, device_id: str) -> Optional[str]:
        """Decrypt data using device-specific key"""
        try:
            device_key = self.get_device_key(device_id)
            if not device_key:
                logger.error(f"No encryption key found for device {device_id}")
                return None
            
            fernet = Fernet(device_key)
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return None
    
    def rotate_device_key(self, device_id: str) -> bool:
        """Rotate encryption key for a specific device"""
        try:
            # Generate new key
            new_key = self.generate_device_key(device_id)
            if not new_key:
                return False
            
            # Remove old key from cache
            if device_id in self.device_keys:
                del self.device_keys[device_id]
            
            # Store rotation timestamp
            self.redis_client.setex(
                f"key_rotation:{device_id}",
                86400 * 7,  # 7 days
                json.dumps({
                    "rotated_at": datetime.utcnow().isoformat(),
                    "reason": "scheduled_rotation"
                })
            )
            
            logger.info(f"Rotated encryption key for device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating device key: {e}")
            return False
    
    def get_encryption_status(self, device_id: str) -> Dict[str, Any]:
        """Get encryption status for a device"""
        try:
            status = {
                "device_id": device_id,
                "key_exists": False,
                "key_age_days": 0,
                "last_rotation": None,
                "encryption_enabled": False
            }
            
            # Check if key exists
            key_exists = self.redis_client.exists(f"device_key:{device_id}")
            status["key_exists"] = bool(key_exists)
            
            if key_exists:
                status["encryption_enabled"] = True
                
                # Check key age (simplified - would need to track creation time)
                # For now, assume keys need rotation every 90 days
                rotation_data = self.redis_client.get(f"key_rotation:{device_id}")
                if rotation_data:
                    rotation_info = json.loads(rotation_data)
                    last_rotation = datetime.fromisoformat(rotation_info["rotated_at"])
                    status["last_rotation"] = last_rotation.isoformat()
                    status["key_age_days"] = (datetime.utcnow() - last_rotation).days
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting encryption status: {e}")
            return {}


class DataProtectionService:
    """Service for data loss prevention and protection"""
    
    def __init__(self, redis_client, encryption_service: EncryptionService):
        self.redis_client = redis_client
        self.encryption_service = encryption_service
        
        # Define sensitive data patterns
        self.sensitive_patterns = {
            "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "phone": r"\b\d{3}[- ]?\d{3}[- ]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "medical_record": r"\bMRN[:\s]*\d{6,10}\b",
            "patient_id": r"\bPID[:\s]*\d{6,10}\b"
        }
        
        logger.info("Data Protection Service initialized")
    
    def scan_for_sensitive_data(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Scan content for sensitive data patterns"""
        try:
            findings = {
                "scan_time": datetime.utcnow().isoformat(),
                "content_length": len(content),
                "sensitive_data_found": False,
                "findings": [],
                "risk_level": "low",
                "context": context or {}
            }
            
            import re
            
            for pattern_name, pattern in self.sensitive_patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    finding = {
                        "type": pattern_name,
                        "pattern": pattern,
                        "match": "***REDACTED***",  # Don't store actual sensitive data
                        "position": match.start(),
                        "length": len(match.group())
                    }
                    findings["findings"].append(finding)
            
            # Determine risk level
            if findings["findings"]:
                findings["sensitive_data_found"] = True
                
                # Categorize findings by severity
                high_risk_types = ["ssn", "credit_card", "medical_record"]
                medium_risk_types = ["phone", "patient_id"]
                
                high_risk_findings = [f for f in findings["findings"] if f["type"] in high_risk_types]
                medium_risk_findings = [f for f in findings["findings"] if f["type"] in medium_risk_types]
                
                if high_risk_findings:
                    findings["risk_level"] = "high"
                elif medium_risk_findings:
                    findings["risk_level"] = "medium"
                else:
                    findings["risk_level"] = "low"
            
            return findings
            
        except Exception as e:
            logger.error(f"Error scanning for sensitive data: {e}")
            return {"error": str(e)}
    
    def protect_sensitive_data(self, content: str, device_id: str,
                             protection_method: str = "encrypt") -> Dict[str, Any]:
        """Protect sensitive data using specified method"""
        try:
            result = {
                "original_length": len(content),
                "protected_content": content,
                "protection_method": protection_method,
                "protection_applied": False,
                "metadata": {}
            }
            
            # First scan for sensitive data
            scan_results = self.scan_for_sensitive_data(content)
            
            if not scan_results.get("sensitive_data_found", False):
                result["protection_applied"] = False
                result["reason"] = "No sensitive data found"
                return result
            
            if protection_method == "encrypt":
                # Encrypt the entire content if it contains sensitive data
                encrypted_content = self.encryption_service.encrypt_data(content, device_id)
                if encrypted_content:
                    result["protected_content"] = encrypted_content
                    result["protection_applied"] = True
                    result["metadata"]["encryption_key_id"] = device_id
            
            elif protection_method == "redact":
                # Redact sensitive patterns
                import re
                protected_content = content
                
                for pattern_name, pattern in self.sensitive_patterns.items():
                    protected_content = re.sub(
                        pattern,
                        "***REDACTED***",
                        protected_content,
                        flags=re.IGNORECASE
                    )
                
                result["protected_content"] = protected_content
                result["protection_applied"] = True
            
            elif protection_method == "mask":
                # Mask sensitive data (show only partial information)
                import re
                protected_content = content
                
                # Mask SSN: XXX-XX-1234
                protected_content = re.sub(
                    r"\b(\d{3})-?(\d{2})-?(\d{4})\b",
                    r"XXX-XX-\3",
                    protected_content
                )
                
                # Mask credit card: XXXX-XXXX-XXXX-1234
                protected_content = re.sub(
                    r"\b(\d{4})[- ]?(\d{4})[- ]?(\d{4})[- ]?(\d{4})\b",
                    r"XXXX-XXXX-XXXX-\4",
                    protected_content
                )
                
                result["protected_content"] = protected_content
                result["protection_applied"] = True
            
            result["scan_results"] = scan_results
            return result
            
        except Exception as e:
            logger.error(f"Error protecting sensitive data: {e}")
            return {"error": str(e)}
    
    def create_data_protection_policy(self, device_type: str) -> Dict[str, Any]:
        """Create data protection policy for device type"""
        policies = {
            "hospital_computer": {
                "encryption_required": True,
                "data_loss_prevention": True,
                "allowed_data_types": ["medical_records", "patient_data", "administrative"],
                "prohibited_data_types": ["personal_files", "entertainment"],
                "backup_required": True,
                "retention_days": 2555,  # 7 years for medical data
                "access_controls": {
                    "require_authentication": True,
                    "allow_usb": False,
                    "allow_cloud_sync": False
                }
            },
            "hospital_laptop": {
                "encryption_required": True,
                "data_loss_prevention": True,
                "allowed_data_types": ["medical_records", "patient_data", "administrative"],
                "prohibited_data_types": ["personal_files", "entertainment"],
                "backup_required": True,
                "retention_days": 2555,
                "access_controls": {
                    "require_authentication": True,
                    "allow_usb": False,
                    "allow_cloud_sync": True,  # For mobile workers
                    "vpn_required": True
                }
            },
            "iot_device": {
                "encryption_required": True,
                "data_loss_prevention": True,
                "allowed_data_types": ["sensor_data", "device_logs"],
                "prohibited_data_types": ["patient_data", "personal_data"],
                "backup_required": False,
                "retention_days": 90,  # Shorter retention for sensor data
                "access_controls": {
                    "require_authentication": True,
                    "allow_usb": False,
                    "allow_cloud_sync": False
                }
            }
        }
        
        return policies.get(device_type, policies["hospital_computer"])


class DeviceProtectionOrchestrator:
    """Main orchestrator for device and data protection services"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Initialize services
        self.posture_service = DevicePostureService(self.redis_client)
        self.encryption_service = EncryptionService(self.redis_client)
        self.data_protection_service = DataProtectionService(self.redis_client, self.encryption_service)
        
        logger.info("Device Protection Orchestrator initialized")
    
    def assess_device_security(self, db: Session, device_id: str,
                             telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive device security assessment"""
        try:
            assessment = {
                "device_id": device_id,
                "assessment_time": datetime.utcnow().isoformat(),
                "posture_assessment": {},
                "encryption_status": {},
                "data_protection_policy": {},
                "overall_security_score": 0.0,
                "recommendations": []
            }
            
            # Get device info
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                assessment["error"] = "Device not found"
                return assessment
            
            # Assess device posture
            posture_assessment = self.posture_service.assess_device_posture(
                db, device_id, telemetry_data
            )
            assessment["posture_assessment"] = posture_assessment
            
            # Check encryption status
            encryption_status = self.encryption_service.get_encryption_status(device_id)
            assessment["encryption_status"] = encryption_status
            
            # Get data protection policy
            data_protection_policy = self.data_protection_service.create_data_protection_policy(
                device.device_type
            )
            assessment["data_protection_policy"] = data_protection_policy
            
            # Calculate overall security score
            posture_score = posture_assessment.get("overall_score", 0.0)
            encryption_score = 1.0 if encryption_status.get("encryption_enabled", False) else 0.0
            
            # Weighted average: 70% posture, 30% encryption
            assessment["overall_security_score"] = (posture_score * 0.7) + (encryption_score * 0.3)
            
            # Combine recommendations
            recommendations = posture_assessment.get("recommendations", [])
            if not encryption_status.get("encryption_enabled", False):
                recommendations.append("Enable device encryption")
            
            assessment["recommendations"] = recommendations
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in device security assessment: {e}")
            return {"error": str(e)}
    
    def enforce_security_policies(self, db: Session, device_id: str) -> Dict[str, Any]:
        """Enforce security policies on a device"""
        try:
            enforcement_results = {
                "device_id": device_id,
                "enforcement_time": datetime.utcnow().isoformat(),
                "actions_taken": [],
                "success": True,
                "errors": []
            }
            
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                enforcement_results["success"] = False
                enforcement_results["errors"].append("Device not found")
                return enforcement_results
            
            # Get data protection policy
            policy = self.data_protection_service.create_data_protection_policy(device.device_type)
            
            # Enforce encryption requirement
            if policy.get("encryption_required", False):
                encryption_status = self.encryption_service.get_encryption_status(device_id)
                
                if not encryption_status.get("key_exists", False):
                    # Generate encryption key
                    key_generated = self.encryption_service.generate_device_key(device_id)
                    if key_generated:
                        enforcement_results["actions_taken"].append("Generated encryption key")
                    else:
                        enforcement_results["errors"].append("Failed to generate encryption key")
                        enforcement_results["success"] = False
                
                # Check if key rotation is needed
                elif encryption_status.get("key_age_days", 0) > 90:
                    key_rotated = self.encryption_service.rotate_device_key(device_id)
                    if key_rotated:
                        enforcement_results["actions_taken"].append("Rotated encryption key")
                    else:
                        enforcement_results["errors"].append("Failed to rotate encryption key")
            
            # Enforce access controls
            access_controls = policy.get("access_controls", {})
            
            if not access_controls.get("allow_usb", True):
                # In a real implementation, this would disable USB ports
                enforcement_results["actions_taken"].append("Disabled USB ports (simulated)")
            
            if access_controls.get("vpn_required", False) and device.device_type == "hospital_laptop":
                # Check if VPN is connected (would need VPN status from telemetry)
                enforcement_results["actions_taken"].append("VPN requirement enforced (simulated)")
            
            return enforcement_results
            
        except Exception as e:
            logger.error(f"Error enforcing security policies: {e}")
            return {"error": str(e)}
    
    def get_protection_dashboard(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive protection dashboard"""
        try:
            dashboard = {
                "generated_at": datetime.utcnow().isoformat(),
                "device_posture_summary": {},
                "encryption_summary": {},
                "policy_compliance": {},
                "security_metrics": {}
            }
            
            # Get device posture summary
            dashboard["device_posture_summary"] = self.posture_service.get_device_posture_summary(db)
            
            # Get encryption summary
            devices = db.query(Device).all()
            encryption_summary = {
                "total_devices": len(devices),
                "encrypted_devices": 0,
                "keys_need_rotation": 0,
                "encryption_rate": 0.0
            }
            
            for device in devices:
                encryption_status = self.encryption_service.get_encryption_status(device.device_id)
                if encryption_status.get("encryption_enabled", False):
                    encryption_summary["encrypted_devices"] += 1
                
                if encryption_status.get("key_age_days", 0) > 90:
                    encryption_summary["keys_need_rotation"] += 1
            
            if encryption_summary["total_devices"] > 0:
                encryption_summary["encryption_rate"] = (
                    encryption_summary["encrypted_devices"] / encryption_summary["total_devices"]
                ) * 100
            
            dashboard["encryption_summary"] = encryption_summary
            
            # Calculate overall security metrics
            posture_compliance = dashboard["device_posture_summary"].get("compliance_rate", 0)
            encryption_rate = encryption_summary.get("encryption_rate", 0)
            
            dashboard["security_metrics"] = {
                "overall_security_score": (posture_compliance + encryption_rate) / 2,
                "devices_at_risk": (
                    dashboard["device_posture_summary"].get("non_compliant_devices", 0) +
                    (encryption_summary["total_devices"] - encryption_summary["encrypted_devices"])
                ),
                "critical_issues": encryption_summary["keys_need_rotation"]
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Error generating protection dashboard: {e}")
            return {"error": str(e)}