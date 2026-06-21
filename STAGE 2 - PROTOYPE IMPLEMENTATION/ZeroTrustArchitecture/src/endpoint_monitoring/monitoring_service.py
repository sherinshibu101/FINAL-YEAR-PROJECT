"""
Endpoint Monitoring Service for Zero Trust Architecture
Collects and processes telemetry from endpoint agents
"""

import json
import asyncio
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from loguru import logger

from ..models import Device, SecurityEvent, DevicePosture, ThreatLevel
from ..database import db_manager


class EndpointMonitoringService:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.device_cache = {}  # In-memory cache for device states
        self.telemetry_buffer = {}  # Buffer for batch processing
        
        # Configuration
        self.HEARTBEAT_TIMEOUT = 300  # 5 minutes
        self.TELEMETRY_BATCH_SIZE = 100
        self.COMPLIANCE_THRESHOLD = 0.8
        
        logger.info("Endpoint Monitoring Service initialized")
    
    def register_device(self, db: Session, device_data: Dict[str, Any]) -> bool:
        """Register a new device or update existing one"""
        try:
            device_id = device_data.get("device_id")
            if not device_id:
                logger.error("Device ID is required for registration")
                return False
            
            # Check if device exists
            device = db.query(Device).filter(Device.device_id == device_id).first()
            
            if not device:
                # Create new device
                device = Device(
                    device_id=device_id,
                    device_name=device_data.get("device_name", f"Device {device_id}"),
                    device_type=device_data.get("device_type", "unknown"),
                    mac_address=device_data.get("mac_address", ""),
                    ip_address=device_data.get("ip_address"),
                    os_version=device_data.get("os_version")
                )
                db.add(device)
                logger.info(f"Registered new device: {device_id}")
            else:
                # Update existing device
                device.device_name = device_data.get("device_name", device.device_name)
                device.ip_address = device_data.get("ip_address", device.ip_address)
                device.os_version = device_data.get("os_version", device.os_version)
                device.last_seen = datetime.utcnow()
                logger.info(f"Updated device: {device_id}")
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            db.rollback()
            return False
    
    def process_heartbeat(self, heartbeat_data: Dict[str, Any]) -> bool:
        """Process device heartbeat"""
        try:
            device_id = heartbeat_data.get("device_id")
            timestamp = heartbeat_data.get("timestamp")
            status = heartbeat_data.get("status", "unknown")
            
            if not device_id:
                return False
            
            # Store in Redis for quick access
            heartbeat_key = f"heartbeat:{device_id}"
            self.redis_client.setex(
                heartbeat_key,
                self.HEARTBEAT_TIMEOUT,
                json.dumps({
                    "timestamp": timestamp,
                    "status": status
                })
            )
            
            # Update device cache
            self.device_cache[device_id] = {
                "last_heartbeat": timestamp,
                "status": status,
                "online": True
            }
            
            logger.debug(f"Processed heartbeat from device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing heartbeat: {e}")
            return False
    
    def process_telemetry(self, db: Session, telemetry_data: Dict[str, Any]) -> bool:
        """Process device telemetry data"""
        try:
            device_id = telemetry_data.get("device_id")
            if not device_id:
                logger.error("Device ID is required for telemetry")
                return False
            
            # Find device
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                logger.warning(f"Unknown device sending telemetry: {device_id}")
                # Auto-register device if not found
                self.register_device(db, {
                    "device_id": device_id,
                    "device_name": f"Auto-registered {device_id}",
                    "device_type": "unknown"
                })
                device = db.query(Device).filter(Device.device_id == device_id).first()
            
            # Update device last seen
            device.last_seen = datetime.utcnow()
            
            # Process security events
            security_events = telemetry_data.get("security_events", [])
            for event_data in security_events:
                self._create_security_event(db, device, event_data)
            
            # Update device posture
            compliance_status = telemetry_data.get("compliance_status", {})
            self._update_device_posture(db, device, compliance_status)
            
            # Calculate trust score
            trust_score = self._calculate_trust_score(telemetry_data, compliance_status)
            device.trust_score = trust_score
            
            # Store detailed telemetry in Redis for analysis
            telemetry_key = f"telemetry:{device_id}:{datetime.utcnow().timestamp()}"
            self.redis_client.setex(
                telemetry_key,
                3600,  # 1 hour TTL
                json.dumps(telemetry_data)
            )
            
            # Update device compliance status
            compliance_score = sum(compliance_status.values()) / len(compliance_status) if compliance_status else 0
            device.is_compliant = compliance_score >= self.COMPLIANCE_THRESHOLD
            
            db.commit()
            logger.debug(f"Processed telemetry from device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing telemetry: {e}")
            db.rollback()
            return False
    
    def _create_security_event(self, db: Session, device: Device, event_data: Dict[str, Any]) -> None:
        """Create a security event"""
        try:
            event_id = f"evt_{device.device_id}_{datetime.utcnow().timestamp()}"
            
            # Map severity to threat level
            severity_mapping = {
                "low": ThreatLevel.LOW,
                "medium": ThreatLevel.MEDIUM,
                "high": ThreatLevel.HIGH,
                "critical": ThreatLevel.CRITICAL
            }
            
            threat_level = severity_mapping.get(
                event_data.get("severity", "medium"),
                ThreatLevel.MEDIUM
            )
            
            # Calculate confidence score based on event type
            confidence_scores = {
                "suspicious_process": 0.8,
                "suspicious_network": 0.7,
                "high_resource_usage": 0.6,
                "unusual_listening_port": 0.5
            }
            
            confidence_score = confidence_scores.get(
                event_data.get("type", "unknown"),
                0.5
            )
            
            security_event = SecurityEvent(
                event_id=event_id,
                event_type=event_data.get("type", "unknown"),
                device_id=device.id,
                threat_level=threat_level,
                confidence_score=confidence_score,
                description=event_data.get("description", ""),
                raw_data=event_data.get("details", {})
            )
            
            db.add(security_event)
            logger.info(f"Created security event {event_id} for device {device.device_id}")
            
        except Exception as e:
            logger.error(f"Error creating security event: {e}")
    
    def _update_device_posture(self, db: Session, device: Device, compliance_status: Dict[str, bool]) -> None:
        """Update device posture information"""
        try:
            # Find existing posture record or create new one
            posture = db.query(DevicePosture).filter(DevicePosture.device_id == device.id).first()
            
            if not posture:
                posture = DevicePosture(device_id=device.id)
                db.add(posture)
            
            # Update posture fields
            posture.antivirus_enabled = compliance_status.get("antivirus_running", False)
            posture.firewall_enabled = compliance_status.get("firewall_enabled", False)
            posture.os_updated = compliance_status.get("os_up_to_date", False)
            posture.encryption_enabled = compliance_status.get("encryption_enabled", False)
            
            # Calculate compliance score
            compliance_values = list(compliance_status.values())
            if compliance_values:
                posture.compliance_score = sum(compliance_values) / len(compliance_values)
            else:
                posture.compliance_score = 0.0
            
            posture.last_check = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error updating device posture: {e}")
    
    def _calculate_trust_score(self, telemetry_data: Dict[str, Any], compliance_status: Dict[str, bool]) -> float:
        """Calculate device trust score based on telemetry and compliance"""
        try:
            base_score = 0.5  # Start with neutral trust
            
            # Factor 1: Compliance score (40% weight)
            compliance_values = list(compliance_status.values()) if compliance_status else []
            if compliance_values:
                compliance_score = sum(compliance_values) / len(compliance_values)
                base_score += (compliance_score - 0.5) * 0.4
            
            # Factor 2: Security events (30% weight)
            security_events = telemetry_data.get("security_events", [])
            if security_events:
                high_severity_events = sum(1 for event in security_events if event.get("severity") in ["high", "critical"])
                event_penalty = min(high_severity_events * 0.1, 0.3)
                base_score -= event_penalty
            else:
                base_score += 0.1  # Bonus for no security events
            
            # Factor 3: Resource usage (20% weight)
            cpu_usage = telemetry_data.get("cpu_usage", 50)
            memory_usage = telemetry_data.get("memory_usage", 50)
            
            # Penalty for high resource usage
            if cpu_usage > 80 or memory_usage > 80:
                base_score -= 0.1
            elif cpu_usage < 50 and memory_usage < 50:
                base_score += 0.05
            
            # Factor 4: Network activity (10% weight)
            connections = telemetry_data.get("network_connections", [])
            unusual_connections = sum(1 for conn in connections if conn.get("remote_port", 0) in [4444, 31337, 12345])
            if unusual_connections > 0:
                base_score -= unusual_connections * 0.05
            
            # Ensure score is between 0 and 1
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error(f"Error calculating trust score: {e}")
            return 0.5  # Return neutral score on error
    
    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get current device status"""
        try:
            # Check heartbeat
            heartbeat_key = f"heartbeat:{device_id}"
            heartbeat_data = self.redis_client.get(heartbeat_key)
            
            online = False
            last_seen = None
            
            if heartbeat_data:
                heartbeat_info = json.loads(heartbeat_data)
                last_seen = heartbeat_info.get("timestamp")
                online = True
            
            # Get device info from cache or database
            with db_manager.get_session() as db:
                device = db.query(Device).filter(Device.device_id == device_id).first()
                if not device:
                    return {"error": "Device not found"}
                
                # Get latest posture
                posture = db.query(DevicePosture).filter(DevicePosture.device_id == device.id).first()
                
                return {
                    "device_id": device_id,
                    "device_name": device.device_name,
                    "device_type": device.device_type,
                    "online": online,
                    "last_seen": last_seen or (device.last_seen.isoformat() if device.last_seen else None),
                    "trust_score": device.trust_score,
                    "is_compliant": device.is_compliant,
                    "is_quarantined": device.is_quarantined,
                    "compliance_score": posture.compliance_score if posture else 0.0,
                    "ip_address": device.ip_address,
                    "mac_address": device.mac_address
                }
            
        except Exception as e:
            logger.error(f"Error getting device status: {e}")
            return {"error": str(e)}
    
    def get_offline_devices(self) -> List[str]:
        """Get list of offline devices"""
        try:
            offline_devices = []
            
            with db_manager.get_session() as db:
                # Get all devices
                devices = db.query(Device).all()
                
                for device in devices:
                    heartbeat_key = f"heartbeat:{device.device_id}"
                    if not self.redis_client.exists(heartbeat_key):
                        offline_devices.append(device.device_id)
            
            return offline_devices
            
        except Exception as e:
            logger.error(f"Error getting offline devices: {e}")
            return []
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary across all devices"""
        try:
            with db_manager.get_session() as db:
                # Count devices by status
                total_devices = db.query(Device).count()
                compliant_devices = db.query(Device).filter(Device.is_compliant == True).count()
                quarantined_devices = db.query(Device).filter(Device.is_quarantined == True).count()
                
                # Count recent security events
                recent_threshold = datetime.utcnow() - timedelta(hours=24)
                recent_events = db.query(SecurityEvent).filter(
                    SecurityEvent.created_at >= recent_threshold
                ).count()
                
                # Count critical events
                critical_events = db.query(SecurityEvent).filter(
                    SecurityEvent.threat_level == ThreatLevel.CRITICAL,
                    SecurityEvent.is_resolved == False
                ).count()
                
                # Average trust score
                devices_with_scores = db.query(Device).filter(Device.trust_score > 0).all()
                avg_trust_score = 0
                if devices_with_scores:
                    avg_trust_score = sum(d.trust_score for d in devices_with_scores) / len(devices_with_scores)
                
                # Get offline devices
                offline_count = len(self.get_offline_devices())
                
                return {
                    "total_devices": total_devices,
                    "online_devices": total_devices - offline_count,
                    "offline_devices": offline_count,
                    "compliant_devices": compliant_devices,
                    "non_compliant_devices": total_devices - compliant_devices,
                    "quarantined_devices": quarantined_devices,
                    "recent_security_events": recent_events,
                    "critical_events": critical_events,
                    "average_trust_score": round(avg_trust_score, 3),
                    "compliance_rate": round((compliant_devices / total_devices) * 100, 1) if total_devices > 0 else 0
                }
            
        except Exception as e:
            logger.error(f"Error getting security summary: {e}")
            return {}
    
    def quarantine_device(self, db: Session, device_id: str, reason: str) -> bool:
        """Quarantine a device"""
        try:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                logger.error(f"Device not found for quarantine: {device_id}")
                return False
            
            device.is_quarantined = True
            db.commit()
            
            # Store quarantine reason in Redis
            quarantine_key = f"quarantine:{device_id}"
            self.redis_client.setex(
                quarantine_key,
                86400,  # 24 hours
                json.dumps({
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            logger.info(f"Device {device_id} quarantined: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error quarantining device: {e}")
            db.rollback()
            return False
    
    def release_quarantine(self, db: Session, device_id: str) -> bool:
        """Release device from quarantine"""
        try:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                logger.error(f"Device not found for quarantine release: {device_id}")
                return False
            
            device.is_quarantined = False
            db.commit()
            
            # Remove quarantine record
            quarantine_key = f"quarantine:{device_id}"
            self.redis_client.delete(quarantine_key)
            
            logger.info(f"Device {device_id} released from quarantine")
            return True
            
        except Exception as e:
            logger.error(f"Error releasing device from quarantine: {e}")
            db.rollback()
            return False
    
    async def start_monitoring(self):
        """Start the monitoring service"""
        logger.info("Starting endpoint monitoring service...")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._cleanup_old_data()),
            asyncio.create_task(self._monitor_device_health()),
            asyncio.create_task(self._process_telemetry_buffer())
        ]
        
        await asyncio.gather(*tasks)
    
    async def _cleanup_old_data(self):
        """Clean up old telemetry and heartbeat data"""
        while True:
            try:
                # Clean up old Redis keys
                pattern = "telemetry:*"
                keys = self.redis_client.keys(pattern)
                
                current_time = datetime.utcnow().timestamp()
                for key in keys:
                    # Extract timestamp from key
                    try:
                        timestamp = float(key.split(":")[-1])
                        if current_time - timestamp > 86400:  # 24 hours
                            self.redis_client.delete(key)
                    except (ValueError, IndexError):
                        pass
                
                logger.debug(f"Cleaned up {len(keys)} old telemetry keys")
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _monitor_device_health(self):
        """Monitor device health and mark offline devices"""
        while True:
            try:
                offline_devices = self.get_offline_devices()
                if offline_devices:
                    logger.warning(f"Found {len(offline_devices)} offline devices: {offline_devices}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in device health monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _process_telemetry_buffer(self):
        """Process buffered telemetry data"""
        while True:
            try:
                if self.telemetry_buffer:
                    with db_manager.get_session() as db:
                        for device_id, telemetry_list in self.telemetry_buffer.items():
                            for telemetry in telemetry_list:
                                self.process_telemetry(db, telemetry)
                    
                    self.telemetry_buffer.clear()
                    logger.debug("Processed telemetry buffer")
                
                await asyncio.sleep(60)  # Process every minute
                
            except Exception as e:
                logger.error(f"Error processing telemetry buffer: {e}")
                await asyncio.sleep(30)