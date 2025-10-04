"""
Response System for Zero Trust Architecture
Handles incident response and automated response actions
"""

import json
import asyncio
import smtplib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from loguru import logger
import redis

from ..models import (
    SecurityEvent, Device, ResponseActionModel, User, UserSession,
    ThreatLevel, ResponseAction
)
from ..database import db_manager


class ResponseStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ResponseActionConfig:
    """Configuration for response actions"""
    action_type: ResponseAction
    severity_threshold: str
    auto_execute: bool
    confirmation_required: bool
    timeout_seconds: int
    escalation_delay_minutes: int
    description: str


class IncidentResponseService:
    """Service for managing security incidents and their response"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.incidents = {}  # In-memory incident store
        self.escalation_rules = {
            ThreatLevel.LOW: {"timeout": 3600, "escalate_to": "security_team"},
            ThreatLevel.MEDIUM: {"timeout": 1800, "escalate_to": "security_admin"},
            ThreatLevel.HIGH: {"timeout": 900, "escalate_to": "ciso"},
            ThreatLevel.CRITICAL: {"timeout": 300, "escalate_to": "emergency_team"}
        }
        
        logger.info("Incident Response Service initialized")
    
    def create_incident(self, db: Session, event: SecurityEvent, 
                       correlations: List[Dict] = None) -> Dict[str, Any]:
        """Create a new security incident"""
        try:
            incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
            
            # Determine incident severity based on event and correlations
            incident_severity = self._determine_incident_severity(event, correlations)
            
            incident = {
                "incident_id": incident_id,
                "title": f"{event.event_type.replace('_', ' ').title()} - {event.description[:50]}...",
                "description": event.description,
                "severity": incident_severity,
                "status": "open",
                "priority": self._calculate_priority(incident_severity, event),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "assigned_to": self._auto_assign_incident(incident_severity),
                "device_id": event.device_id,
                "user_id": event.user_id,
                "source_events": [event.event_id],
                "correlations": [c.get("correlation_id") for c in (correlations or [])],
                "timeline": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "incident_created",
                        "description": f"Incident created from event {event.event_id}",
                        "user": "system"
                    }
                ],
                "response_actions": [],
                "escalation_level": 0
            }
            
            # Store incident
            self.incidents[incident_id] = incident
            
            # Store in Redis for persistence
            self.redis_client.setex(
                f"incident:{incident_id}",
                86400,  # 24 hours
                json.dumps(incident)
            )
            
            logger.info(f"Created incident {incident_id} for event {event.event_id}")
            return incident
            
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            raise
    
    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing incident"""
        try:
            incident = self.get_incident(incident_id)
            if not incident:
                logger.error(f"Incident not found: {incident_id}")
                return False
            
            # Update fields
            incident.update(updates)
            incident["updated_at"] = datetime.utcnow().isoformat()
            
            # Add to timeline
            if "timeline_entry" in updates:
                incident["timeline"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": updates.get("action", "update"),
                    "description": updates["timeline_entry"],
                    "user": updates.get("user", "system")
                })
            
            # Update storage
            self.incidents[incident_id] = incident
            self.redis_client.setex(
                f"incident:{incident_id}",
                86400,
                json.dumps(incident)
            )
            
            logger.debug(f"Updated incident {incident_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating incident: {e}")
            return False
    
    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get incident by ID"""
        try:
            # Check memory first
            if incident_id in self.incidents:
                return self.incidents[incident_id]
            
            # Check Redis
            incident_data = self.redis_client.get(f"incident:{incident_id}")
            if incident_data:
                incident = json.loads(incident_data)
                self.incidents[incident_id] = incident
                return incident
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting incident: {e}")
            return None
    
    def list_open_incidents(self) -> List[Dict[str, Any]]:
        """List all open incidents"""
        try:
            open_incidents = []
            
            # Get incident keys from Redis
            incident_keys = self.redis_client.keys("incident:*")
            
            for key in incident_keys:
                incident_data = self.redis_client.get(key)
                if incident_data:
                    incident = json.loads(incident_data)
                    if incident.get("status") == "open":
                        open_incidents.append(incident)
            
            # Sort by priority and creation time
            open_incidents.sort(key=lambda x: (x.get("priority", 0), x.get("created_at")), reverse=True)
            return open_incidents
            
        except Exception as e:
            logger.error(f"Error listing open incidents: {e}")
            return []
    
    def escalate_incident(self, incident_id: str, reason: str) -> bool:
        """Escalate an incident to the next level"""
        try:
            incident = self.get_incident(incident_id)
            if not incident:
                return False
            
            current_level = incident.get("escalation_level", 0)
            new_level = current_level + 1
            
            # Determine new assignee based on escalation level
            escalation_assignments = {
                1: "security_admin",
                2: "ciso",
                3: "emergency_team"
            }
            
            new_assignee = escalation_assignments.get(new_level, "emergency_team")
            
            updates = {
                "escalation_level": new_level,
                "assigned_to": new_assignee,
                "priority": min(incident.get("priority", 1) + 1, 5),  # Increase priority
                "timeline_entry": f"Incident escalated to level {new_level}: {reason}",
                "action": "escalated"
            }
            
            return self.update_incident(incident_id, updates)
            
        except Exception as e:
            logger.error(f"Error escalating incident: {e}")
            return False
    
    def close_incident(self, incident_id: str, resolution: str, user: str = "system") -> bool:
        """Close an incident"""
        try:
            updates = {
                "status": "closed",
                "resolution": resolution,
                "closed_at": datetime.utcnow().isoformat(),
                "timeline_entry": f"Incident closed: {resolution}",
                "action": "closed",
                "user": user
            }
            
            return self.update_incident(incident_id, updates)
            
        except Exception as e:
            logger.error(f"Error closing incident: {e}")
            return False
    
    def _determine_incident_severity(self, event: SecurityEvent, 
                                   correlations: List[Dict] = None) -> str:
        """Determine incident severity based on event and correlations"""
        base_severity = event.threat_level
        
        # Escalate severity if there are correlations
        if correlations:
            correlation_severities = [c.get("severity", "low") for c in correlations]
            if "critical" in correlation_severities:
                return "critical"
            elif "high" in correlation_severities:
                return "high"
        
        return base_severity
    
    def _calculate_priority(self, severity: str, event: SecurityEvent) -> int:
        """Calculate incident priority (1-5, 5 being highest)"""
        severity_priority = {
            "low": 1,
            "medium": 2,
            "high": 4,
            "critical": 5
        }
        
        base_priority = severity_priority.get(severity, 1)
        
        # Adjust priority based on confidence score
        if event.confidence_score > 0.8:
            base_priority = min(base_priority + 1, 5)
        
        return base_priority
    
    def _auto_assign_incident(self, severity: str) -> str:
        """Auto-assign incident based on severity"""
        assignments = {
            "low": "security_team",
            "medium": "security_team",
            "high": "security_admin",
            "critical": "ciso"
        }
        
        return assignments.get(severity, "security_team")


class AutomatedResponseService:
    """Service for automated response actions"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.response_configs = self._initialize_response_configs()
        self.notification_service = NotificationService()
        
        logger.info("Automated Response Service initialized")
    
    def _initialize_response_configs(self) -> Dict[ResponseAction, ResponseActionConfig]:
        """Initialize response action configurations"""
        return {
            ResponseAction.ISOLATE_DEVICE: ResponseActionConfig(
                action_type=ResponseAction.ISOLATE_DEVICE,
                severity_threshold="high",
                auto_execute=True,
                confirmation_required=False,
                timeout_seconds=300,
                escalation_delay_minutes=15,
                description="Isolate device from network"
            ),
            ResponseAction.QUARANTINE: ResponseActionConfig(
                action_type=ResponseAction.QUARANTINE,
                severity_threshold="medium",
                auto_execute=True,
                confirmation_required=False,
                timeout_seconds=600,
                escalation_delay_minutes=30,
                description="Quarantine device with limited network access"
            ),
            ResponseAction.REVOKE_ACCESS: ResponseActionConfig(
                action_type=ResponseAction.REVOKE_ACCESS,
                severity_threshold="high",
                auto_execute=True,
                confirmation_required=True,
                timeout_seconds=120,
                escalation_delay_minutes=10,
                description="Revoke user access and terminate sessions"
            ),
            ResponseAction.ALERT_ADMIN: ResponseActionConfig(
                action_type=ResponseAction.ALERT_ADMIN,
                severity_threshold="low",
                auto_execute=True,
                confirmation_required=False,
                timeout_seconds=60,
                escalation_delay_minutes=5,
                description="Send alert to administrators"
            )
        }
    
    def evaluate_response_actions(self, db: Session, event: SecurityEvent, 
                                analysis_results: Dict[str, Any]) -> List[ResponseAction]:
        """Evaluate which response actions should be taken"""
        recommended_actions = []
        
        try:
            risk_score = analysis_results.get("risk_score", 0)
            threat_intel_matches = analysis_results.get("threat_intel_matches", [])
            ml_anomaly = analysis_results.get("ml_anomaly", False)
            
            # Critical risk score - isolate device
            if risk_score > 0.9:
                recommended_actions.append(ResponseAction.ISOLATE_DEVICE)
                recommended_actions.append(ResponseAction.ALERT_ADMIN)
            
            # High risk score - quarantine
            elif risk_score > 0.7:
                recommended_actions.append(ResponseAction.QUARANTINE)
                recommended_actions.append(ResponseAction.ALERT_ADMIN)
            
            # Threat intelligence matches - quarantine and revoke access
            if threat_intel_matches:
                if not ResponseAction.QUARANTINE in recommended_actions:
                    recommended_actions.append(ResponseAction.QUARANTINE)
                if event.user_id:  # Only revoke if there's a user associated
                    recommended_actions.append(ResponseAction.REVOKE_ACCESS)
            
            # ML anomaly detected
            if ml_anomaly:
                recommended_actions.append(ResponseAction.ALERT_ADMIN)
            
            # Always alert on high/critical events
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                if ResponseAction.ALERT_ADMIN not in recommended_actions:
                    recommended_actions.append(ResponseAction.ALERT_ADMIN)
            
            return recommended_actions
            
        except Exception as e:
            logger.error(f"Error evaluating response actions: {e}")
            return [ResponseAction.ALERT_ADMIN]  # Fallback to alert
    
    async def execute_response_action(self, db: Session, action_type: ResponseAction,
                                    event: SecurityEvent, context: Dict[str, Any]) -> bool:
        """Execute a specific response action"""
        try:
            action_id = f"action_{action_type}_{datetime.utcnow().timestamp()}"
            
            # Create response action record
            response_action = ResponseActionModel(
                action_id=action_id,
                event_id=event.id,
                action_type=action_type,
                description=self.response_configs[action_type].description,
                is_automated=True,
                status=ResponseStatus.EXECUTING
            )
            
            db.add(response_action)
            db.commit()
            
            # Execute the specific action
            success = False
            if action_type == ResponseAction.ISOLATE_DEVICE:
                success = await self._isolate_device(db, event, context)
            elif action_type == ResponseAction.QUARANTINE:
                success = await self._quarantine_device(db, event, context)
            elif action_type == ResponseAction.REVOKE_ACCESS:
                success = await self._revoke_user_access(db, event, context)
            elif action_type == ResponseAction.ALERT_ADMIN:
                success = await self._alert_administrators(db, event, context)
            
            # Update action status
            response_action.status = ResponseStatus.COMPLETED if success else ResponseStatus.FAILED
            response_action.executed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Executed response action {action_type} with result: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Error executing response action {action_type}: {e}")
            # Update status to failed
            if 'response_action' in locals():
                response_action.status = ResponseStatus.FAILED
                db.commit()
            return False
    
    async def _isolate_device(self, db: Session, event: SecurityEvent, 
                            context: Dict[str, Any]) -> bool:
        """Isolate device from network"""
        try:
            device = db.query(Device).filter(Device.id == event.device_id).first()
            if not device:
                logger.error("Device not found for isolation")
                return False
            
            # Mark device as quarantined (complete isolation)
            device.is_quarantined = True
            device.trust_score = 0.0  # Zero trust score for isolated devices
            
            # Store isolation reason in Redis
            isolation_key = f"isolation:{device.device_id}"
            self.redis_client.setex(
                isolation_key,
                86400 * 7,  # 7 days
                json.dumps({
                    "reason": f"Automated isolation due to {event.event_type}",
                    "event_id": event.event_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "risk_score": context.get("risk_score", 0)
                })
            )
            
            # Generate firewall rules to block all traffic
            firewall_rules = {
                "device_id": device.device_id,
                "action": "block_all",
                "rules": [
                    {"direction": "inbound", "action": "deny", "ports": "all"},
                    {"direction": "outbound", "action": "deny", "ports": "all"}
                ],
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store firewall rules
            self.redis_client.setex(
                f"firewall:{device.device_id}",
                86400 * 7,
                json.dumps(firewall_rules)
            )
            
            db.commit()
            
            # Send notification
            await self.notification_service.send_notification({
                "type": "device_isolated",
                "device_id": device.device_id,
                "device_name": device.device_name,
                "reason": event.description,
                "severity": "critical"
            })
            
            logger.info(f"Successfully isolated device {device.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error isolating device: {e}")
            return False
    
    async def _quarantine_device(self, db: Session, event: SecurityEvent, 
                               context: Dict[str, Any]) -> bool:
        """Quarantine device with limited network access"""
        try:
            device = db.query(Device).filter(Device.id == event.device_id).first()
            if not device:
                logger.error("Device not found for quarantine")
                return False
            
            # Mark device as quarantined
            device.is_quarantined = True
            device.trust_score = max(device.trust_score - 0.3, 0.1)  # Reduce trust score
            
            # Store quarantine reason
            quarantine_key = f"quarantine:{device.device_id}"
            self.redis_client.setex(
                quarantine_key,
                86400,  # 24 hours
                json.dumps({
                    "reason": f"Automated quarantine due to {event.event_type}",
                    "event_id": event.event_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "risk_score": context.get("risk_score", 0)
                })
            )
            
            # Generate limited firewall rules (allow only essential services)
            firewall_rules = {
                "device_id": device.device_id,
                "action": "quarantine",
                "rules": [
                    {"direction": "outbound", "action": "allow", "ports": [53, 80, 443]},  # DNS, HTTP, HTTPS
                    {"direction": "outbound", "action": "deny", "ports": "others"},
                    {"direction": "inbound", "action": "deny", "ports": "all"}
                ],
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store firewall rules
            self.redis_client.setex(
                f"firewall:{device.device_id}",
                86400,
                json.dumps(firewall_rules)
            )
            
            db.commit()
            
            # Send notification
            await self.notification_service.send_notification({
                "type": "device_quarantined",
                "device_id": device.device_id,
                "device_name": device.device_name,
                "reason": event.description,
                "severity": "high"
            })
            
            logger.info(f"Successfully quarantined device {device.device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error quarantining device: {e}")
            return False
    
    async def _revoke_user_access(self, db: Session, event: SecurityEvent, 
                                context: Dict[str, Any]) -> bool:
        """Revoke user access and terminate sessions"""
        try:
            if not event.user_id:
                logger.warning("No user associated with event for access revocation")
                return False
            
            user = db.query(User).filter(User.id == event.user_id).first()
            if not user:
                logger.error("User not found for access revocation")
                return False
            
            # Disable user account temporarily
            user.is_active = False
            
            # Terminate all active sessions
            active_sessions = db.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).all()
            
            for session in active_sessions:
                session.is_active = False
            
            # Store revocation reason
            revocation_key = f"access_revoked:{user.id}"
            self.redis_client.setex(
                revocation_key,
                86400,  # 24 hours
                json.dumps({
                    "reason": f"Automated access revocation due to {event.event_type}",
                    "event_id": event.event_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "risk_score": context.get("risk_score", 0)
                })
            )
            
            db.commit()
            
            # Send notification
            await self.notification_service.send_notification({
                "type": "user_access_revoked",
                "user_id": user.id,
                "username": user.username,
                "reason": event.description,
                "severity": "high"
            })
            
            logger.info(f"Successfully revoked access for user {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking user access: {e}")
            return False
    
    async def _alert_administrators(self, db: Session, event: SecurityEvent, 
                                  context: Dict[str, Any]) -> bool:
        """Send alert to administrators"""
        try:
            # Get device info for context
            device_info = "Unknown device"
            if event.device_id:
                device = db.query(Device).filter(Device.id == event.device_id).first()
                if device:
                    device_info = f"{device.device_name} ({device.device_id})"
            
            # Get user info for context
            user_info = "No user associated"
            if event.user_id:
                user = db.query(User).filter(User.id == event.user_id).first()
                if user:
                    user_info = f"{user.full_name} ({user.username})"
            
            alert_data = {
                "type": "security_alert",
                "event_type": event.event_type,
                "threat_level": event.threat_level,
                "confidence_score": event.confidence_score,
                "description": event.description,
                "device": device_info,
                "user": user_info,
                "timestamp": event.created_at.isoformat(),
                "risk_score": context.get("risk_score", 0),
                "ml_anomaly": context.get("ml_anomaly", False),
                "threat_intel_matches": len(context.get("threat_intel_matches", [])),
                "severity": event.threat_level
            }
            
            # Send notification
            success = await self.notification_service.send_notification(alert_data)
            
            if success:
                logger.info(f"Successfully sent alert for event {event.event_id}")
            else:
                logger.error(f"Failed to send alert for event {event.event_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending administrator alert: {e}")
            return False


class NotificationService:
    """Service for sending notifications via various channels"""
    
    def __init__(self):
        self.channels = ["email", "slack", "sms"]  # Available notification channels
        self.admin_contacts = {
            "email": ["security@hospital.com", "admin@hospital.com"],
            "slack": ["#security-alerts", "#it-alerts"],
            "sms": ["+1234567890", "+0987654321"]
        }
        
        logger.info("Notification Service initialized")
    
    async def send_notification(self, alert_data: Dict[str, Any]) -> bool:
        """Send notification through configured channels"""
        try:
            success_count = 0
            total_channels = len(self.channels)
            
            # Send email notification
            if "email" in self.channels:
                email_success = await self._send_email_notification(alert_data)
                if email_success:
                    success_count += 1
            
            # Send Slack notification (simulated)
            if "slack" in self.channels:
                slack_success = await self._send_slack_notification(alert_data)
                if slack_success:
                    success_count += 1
            
            # Send SMS notification (simulated)
            if "sms" in self.channels:
                sms_success = await self._send_sms_notification(alert_data)
                if sms_success:
                    success_count += 1
            
            # Consider success if at least one channel worked
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            return False
    
    async def _send_email_notification(self, alert_data: Dict[str, Any]) -> bool:
        """Send email notification (simulated)"""
        try:
            # In a real implementation, this would use SMTP to send emails
            logger.info(f"EMAIL NOTIFICATION: {alert_data['type']} - {alert_data.get('description', 'Security Alert')}")
            logger.info(f"Recipients: {self.admin_contacts['email']}")
            
            # Simulate email sending delay
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    async def _send_slack_notification(self, alert_data: Dict[str, Any]) -> bool:
        """Send Slack notification (simulated)"""
        try:
            # In a real implementation, this would use Slack API
            logger.info(f"SLACK NOTIFICATION: {alert_data['type']} - {alert_data.get('description', 'Security Alert')}")
            logger.info(f"Channels: {self.admin_contacts['slack']}")
            
            # Simulate Slack API delay
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    async def _send_sms_notification(self, alert_data: Dict[str, Any]) -> bool:
        """Send SMS notification (simulated)"""
        try:
            # In a real implementation, this would use SMS service like Twilio
            severity = alert_data.get('severity', 'medium')
            
            # Only send SMS for high/critical alerts to avoid spam
            if severity in ['high', 'critical']:
                logger.info(f"SMS NOTIFICATION: {alert_data['type']} - {alert_data.get('description', 'Security Alert')}")
                logger.info(f"Recipients: {self.admin_contacts['sms']}")
            
            # Simulate SMS service delay
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False


class ResponseOrchestrator:
    """Main orchestrator for coordinating incident response and automated actions"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Initialize services
        self.incident_service = IncidentResponseService(self.redis_client)
        self.automated_response = AutomatedResponseService(self.redis_client)
        
        logger.info("Response Orchestrator initialized")
    
    async def process_security_event(self, db: Session, event: SecurityEvent,
                                   analysis_results: Dict[str, Any],
                                   correlations: List[Dict] = None) -> Dict[str, Any]:
        """Process a security event and coordinate response"""
        try:
            response_summary = {
                "event_id": event.event_id,
                "incident_created": False,
                "incident_id": None,
                "actions_executed": [],
                "actions_failed": [],
                "notifications_sent": False
            }
            
            # Create incident for high severity events or those with correlations
            should_create_incident = (
                event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL] or
                analysis_results.get("risk_score", 0) > 0.6 or
                correlations
            )
            
            if should_create_incident:
                incident = self.incident_service.create_incident(db, event, correlations)
                response_summary["incident_created"] = True
                response_summary["incident_id"] = incident["incident_id"]
            
            # Evaluate and execute automated response actions
            recommended_actions = self.automated_response.evaluate_response_actions(
                db, event, analysis_results
            )
            
            for action in recommended_actions:
                try:
                    success = await self.automated_response.execute_response_action(
                        db, action, event, analysis_results
                    )
                    
                    if success:
                        response_summary["actions_executed"].append(action.value)
                    else:
                        response_summary["actions_failed"].append(action.value)
                        
                except Exception as e:
                    logger.error(f"Error executing action {action}: {e}")
                    response_summary["actions_failed"].append(action.value)
            
            # Update incident with response actions if created
            if response_summary["incident_created"]:
                action_summary = f"Executed actions: {response_summary['actions_executed']}"
                if response_summary["actions_failed"]:
                    action_summary += f", Failed actions: {response_summary['actions_failed']}"
                
                self.incident_service.update_incident(
                    response_summary["incident_id"],
                    {
                        "response_actions": response_summary["actions_executed"],
                        "timeline_entry": action_summary,
                        "action": "automated_response"
                    }
                )
            
            response_summary["notifications_sent"] = ResponseAction.ALERT_ADMIN.value in response_summary["actions_executed"]
            
            logger.info(f"Processed security event {event.event_id} with {len(response_summary['actions_executed'])} successful actions")
            return response_summary
            
        except Exception as e:
            logger.error(f"Error processing security event: {e}")
            return response_summary
    
    def get_response_status(self, event_id: str) -> Dict[str, Any]:
        """Get response status for a specific event"""
        try:
            # This could be enhanced to track response status in Redis
            status_key = f"response_status:{event_id}"
            status_data = self.redis_client.get(status_key)
            
            if status_data:
                return json.loads(status_data)
            
            return {"error": "Response status not found"}
            
        except Exception as e:
            logger.error(f"Error getting response status: {e}")
            return {"error": str(e)}