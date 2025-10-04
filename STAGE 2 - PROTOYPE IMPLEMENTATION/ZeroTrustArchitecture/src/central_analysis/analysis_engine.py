"""
Central Analysis Engine for Zero Trust Architecture
Handles event correlation, threat intelligence, and ML-based threat detection
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session
from loguru import logger
import joblib
import redis

from ..models import SecurityEvent, Device, ThreatIntelligence, ThreatLevel, ResponseAction
from ..database import db_manager


class EventCorrelationEngine:
    """Engine for correlating security events across devices and time"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.correlation_window = timedelta(minutes=30)
        self.correlation_threshold = 0.7
        
        # Event correlation rules
        self.correlation_rules = {
            "lateral_movement": {
                "events": ["suspicious_network", "suspicious_process"],
                "time_window": 600,  # 10 minutes
                "device_threshold": 2,
                "severity": "high"
            },
            "data_exfiltration": {
                "events": ["unusual_listening_port", "high_resource_usage"],
                "time_window": 900,  # 15 minutes
                "device_threshold": 1,
                "severity": "critical"
            },
            "malware_outbreak": {
                "events": ["suspicious_process", "high_resource_usage"],
                "time_window": 1800,  # 30 minutes
                "device_threshold": 3,
                "severity": "critical"
            },
            "reconnaissance": {
                "events": ["suspicious_network", "unusual_listening_port"],
                "time_window": 300,  # 5 minutes
                "device_threshold": 1,
                "severity": "medium"
            }
        }
        
        logger.info("Event Correlation Engine initialized")
    
    def correlate_events(self, db: Session) -> List[Dict[str, Any]]:
        """Correlate security events to identify attack patterns"""
        correlated_events = []
        
        try:
            # Get recent unresolved events
            recent_threshold = datetime.utcnow() - self.correlation_window
            events = db.query(SecurityEvent).filter(
                SecurityEvent.created_at >= recent_threshold,
                SecurityEvent.is_resolved == False
            ).all()
            
            if not events:
                return []
            
            # Group events by correlation rules
            for rule_name, rule_config in self.correlation_rules.items():
                pattern_events = self._find_pattern_events(events, rule_config)
                if pattern_events:
                    correlation = self._create_correlation(rule_name, rule_config, pattern_events)
                    correlated_events.append(correlation)
            
            logger.debug(f"Found {len(correlated_events)} correlated event patterns")
            return correlated_events
            
        except Exception as e:
            logger.error(f"Error correlating events: {e}")
            return []
    
    def _find_pattern_events(self, events: List[SecurityEvent], rule_config: Dict[str, Any]) -> List[SecurityEvent]:
        """Find events matching a correlation pattern"""
        matching_events = []
        target_event_types = rule_config["events"]
        time_window = timedelta(seconds=rule_config["time_window"])
        device_threshold = rule_config["device_threshold"]
        
        # Filter events by type
        relevant_events = [event for event in events if event.event_type in target_event_types]
        
        if not relevant_events:
            return []
        
        # Group by time windows
        for base_event in relevant_events:
            window_start = base_event.created_at
            window_end = window_start + time_window
            
            window_events = [
                event for event in relevant_events
                if window_start <= event.created_at <= window_end
            ]
            
            # Check if enough different devices are affected
            affected_devices = set(event.device_id for event in window_events if event.device_id)
            
            if len(affected_devices) >= device_threshold:
                # Check if all required event types are present
                present_types = set(event.event_type for event in window_events)
                required_types = set(target_event_types)
                
                if required_types.issubset(present_types):
                    matching_events.extend(window_events)
        
        return list(set(matching_events))  # Remove duplicates
    
    def _create_correlation(self, rule_name: str, rule_config: Dict[str, Any], 
                          events: List[SecurityEvent]) -> Dict[str, Any]:
        """Create a correlation object"""
        affected_devices = list(set(event.device_id for event in events if event.device_id))
        
        correlation = {
            "correlation_id": f"corr_{rule_name}_{datetime.utcnow().timestamp()}",
            "pattern_name": rule_name,
            "severity": rule_config["severity"],
            "confidence_score": self._calculate_correlation_confidence(events),
            "event_count": len(events),
            "affected_devices": affected_devices,
            "time_span": {
                "start": min(event.created_at for event in events).isoformat(),
                "end": max(event.created_at for event in events).isoformat()
            },
            "event_ids": [event.event_id for event in events],
            "description": self._generate_correlation_description(rule_name, events),
            "created_at": datetime.utcnow().isoformat()
        }
        
        return correlation
    
    def _calculate_correlation_confidence(self, events: List[SecurityEvent]) -> float:
        """Calculate confidence score for correlation"""
        if not events:
            return 0.0
        
        # Base confidence from individual event confidence scores
        avg_confidence = sum(event.confidence_score for event in events) / len(events)
        
        # Boost confidence based on number of events
        event_boost = min(len(events) * 0.1, 0.3)
        
        # Boost confidence based on time proximity
        if len(events) > 1:
            time_span = max(event.created_at for event in events) - min(event.created_at for event in events)
            time_penalty = min(time_span.total_seconds() / 3600, 0.2)  # Penalty for events spread over time
        else:
            time_penalty = 0
        
        final_confidence = min(avg_confidence + event_boost - time_penalty, 1.0)
        return max(final_confidence, 0.0)
    
    def _generate_correlation_description(self, rule_name: str, events: List[SecurityEvent]) -> str:
        """Generate human-readable description of correlation"""
        device_count = len(set(event.device_id for event in events if event.device_id))
        event_types = list(set(event.event_type for event in events))
        
        descriptions = {
            "lateral_movement": f"Potential lateral movement detected across {device_count} devices with {', '.join(event_types)} activities",
            "data_exfiltration": f"Possible data exfiltration attempt with {', '.join(event_types)} indicators",
            "malware_outbreak": f"Suspected malware outbreak affecting {device_count} devices",
            "reconnaissance": f"Network reconnaissance activity detected with {', '.join(event_types)}"
        }
        
        return descriptions.get(rule_name, f"Correlated security events: {', '.join(event_types)}")


class ThreatIntelligenceService:
    """Service for managing and querying threat intelligence data"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.ioc_cache_ttl = 3600  # 1 hour
        
        # Sample threat intelligence feeds
        self.threat_feeds = [
            {
                "name": "malware_domains",
                "url": "https://api.threatintel.example.com/domains",
                "type": "domain",
                "update_interval": 3600
            },
            {
                "name": "malicious_ips",
                "url": "https://api.threatintel.example.com/ips",
                "type": "ip",
                "update_interval": 1800
            }
        ]
        
        logger.info("Threat Intelligence Service initialized")
    
    def update_threat_intelligence(self, db: Session) -> bool:
        """Update threat intelligence from feeds"""
        try:
            # Sample threat intelligence data (in production, this would fetch from real feeds)
            sample_iocs = [
                {
                    "ioc_type": "ip",
                    "ioc_value": "192.168.100.1",
                    "threat_type": "malware_c2",
                    "confidence": 0.9,
                    "source": "internal_honeypot",
                    "description": "Known malware command and control server"
                },
                {
                    "ioc_type": "domain",
                    "ioc_value": "malicious.example.com",
                    "threat_type": "phishing",
                    "confidence": 0.85,
                    "source": "threat_feed_alpha",
                    "description": "Phishing domain targeting healthcare organizations"
                },
                {
                    "ioc_type": "hash",
                    "ioc_value": "d41d8cd98f00b204e9800998ecf8427e",
                    "threat_type": "ransomware",
                    "confidence": 0.95,
                    "source": "virus_total",
                    "description": "Known ransomware file hash"
                },
                {
                    "ioc_type": "ip",
                    "ioc_value": "10.0.0.100",
                    "threat_type": "lateral_movement",
                    "confidence": 0.7,
                    "source": "ml_detection",
                    "description": "IP showing signs of lateral movement activity"
                }
            ]
            
            for ioc_data in sample_iocs:
                # Check if IOC already exists
                existing_ioc = db.query(ThreatIntelligence).filter(
                    ThreatIntelligence.ioc_value == ioc_data["ioc_value"]
                ).first()
                
                if existing_ioc:
                    # Update existing IOC
                    existing_ioc.confidence = ioc_data["confidence"]
                    existing_ioc.last_seen = datetime.utcnow()
                else:
                    # Create new IOC
                    new_ioc = ThreatIntelligence(**ioc_data)
                    db.add(new_ioc)
                
                # Cache in Redis for quick lookup
                cache_key = f"ioc:{ioc_data['ioc_type']}:{ioc_data['ioc_value']}"
                self.redis_client.setex(
                    cache_key,
                    self.ioc_cache_ttl,
                    json.dumps(ioc_data)
                )
            
            db.commit()
            logger.info(f"Updated {len(sample_iocs)} threat intelligence indicators")
            return True
            
        except Exception as e:
            logger.error(f"Error updating threat intelligence: {e}")
            db.rollback()
            return False
    
    def check_ioc(self, ioc_type: str, ioc_value: str) -> Optional[Dict[str, Any]]:
        """Check if an indicator is known threat"""
        try:
            # First check Redis cache
            cache_key = f"ioc:{ioc_type}:{ioc_value}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            
            # Check database
            with db_manager.get_session() as db:
                ioc = db.query(ThreatIntelligence).filter(
                    ThreatIntelligence.ioc_type == ioc_type,
                    ThreatIntelligence.ioc_value == ioc_value,
                    ThreatIntelligence.is_active == True
                ).first()
                
                if ioc:
                    ioc_data = {
                        "ioc_type": ioc.ioc_type,
                        "ioc_value": ioc.ioc_value,
                        "threat_type": ioc.threat_type,
                        "confidence": ioc.confidence,
                        "source": ioc.source,
                        "description": ioc.description,
                        "first_seen": ioc.first_seen.isoformat(),
                        "last_seen": ioc.last_seen.isoformat()
                    }
                    
                    # Cache the result
                    self.redis_client.setex(cache_key, self.ioc_cache_ttl, json.dumps(ioc_data))
                    return ioc_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking IOC: {e}")
            return None
    
    def enrich_security_event(self, db: Session, event: SecurityEvent) -> bool:
        """Enrich security event with threat intelligence"""
        try:
            if not event.raw_data:
                return False
            
            enrichment_data = {"threat_intel": []}
            
            # Extract IOCs from event data
            raw_data = event.raw_data
            
            # Check IP addresses
            if "remote_address" in raw_data:
                ip = raw_data["remote_address"]
                if ip and ip != "":
                    ioc_data = self.check_ioc("ip", ip)
                    if ioc_data:
                        enrichment_data["threat_intel"].append({
                            "type": "ip_reputation",
                            "value": ip,
                            "threat_data": ioc_data
                        })
            
            # Check processes/files (simplified - would need hash calculation)
            if "name" in raw_data:
                process_name = raw_data["name"]
                # In a real implementation, we'd calculate file hashes
                # For now, simulate checking known bad process names
                known_bad_processes = ["mimikatz", "psexec", "nc.exe"]
                if any(bad in process_name.lower() for bad in known_bad_processes):
                    enrichment_data["threat_intel"].append({
                        "type": "malicious_process",
                        "value": process_name,
                        "threat_data": {
                            "threat_type": "malware_tool",
                            "confidence": 0.8,
                            "description": f"Known malicious process: {process_name}"
                        }
                    })
            
            # Update event with enrichment data if found
            if enrichment_data["threat_intel"]:
                if isinstance(event.raw_data, dict):
                    event.raw_data.update(enrichment_data)
                else:
                    event.raw_data = enrichment_data
                
                # Increase confidence if threat intel match found
                event.confidence_score = min(event.confidence_score + 0.2, 1.0)
                db.commit()
                
                logger.debug(f"Enriched event {event.event_id} with threat intelligence")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enriching security event: {e}")
            return False


class MLThreatDetector:
    """Machine Learning based threat detector using anomaly detection"""
    
    def __init__(self, model_path: str = "./data/threat_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_columns = [
            'cpu_usage', 'memory_usage', 'disk_usage', 'network_connection_count',
            'process_count', 'suspicious_process_count', 'unusual_port_count'
        ]
        
        # Load existing model or create new one
        self._load_or_create_model()
        logger.info("ML Threat Detector initialized")
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        try:
            # Try to load existing model
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.model_path.replace('.pkl', '_scaler.pkl'))
            logger.info("Loaded existing ML model")
        except FileNotFoundError:
            # Create new model
            self.model = IsolationForest(
                contamination=0.1,  # Expect 10% of data to be anomalous
                random_state=42,
                n_estimators=100
            )
            self.scaler = StandardScaler()
            logger.info("Created new ML model")
    
    def extract_features(self, telemetry_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from telemetry data"""
        try:
            features = {}
            
            # Basic system metrics
            features['cpu_usage'] = telemetry_data.get('cpu_usage', 0)
            features['memory_usage'] = telemetry_data.get('memory_usage', 0)
            features['disk_usage'] = telemetry_data.get('disk_usage', 0)
            
            # Network metrics
            connections = telemetry_data.get('network_connections', [])
            features['network_connection_count'] = len(connections)
            
            # Process metrics
            processes = telemetry_data.get('running_processes', [])
            features['process_count'] = len(processes)
            
            # Security metrics
            security_events = telemetry_data.get('security_events', [])
            features['suspicious_process_count'] = sum(
                1 for event in security_events if event.get('type') == 'suspicious_process'
            )
            features['unusual_port_count'] = sum(
                1 for event in security_events if event.get('type') == 'unusual_listening_port'
            )
            
            # Convert to numpy array
            feature_vector = np.array([features[col] for col in self.feature_columns]).reshape(1, -1)
            return feature_vector
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.zeros((1, len(self.feature_columns)))
    
    def detect_anomaly(self, telemetry_data: Dict[str, Any]) -> Tuple[bool, float]:
        """Detect if telemetry data represents an anomaly"""
        try:
            if self.model is None:
                logger.warning("ML model not initialized")
                return False, 0.0
            
            # Extract features
            features = self.extract_features(telemetry_data)
            
            # Scale features if scaler is trained
            if hasattr(self.scaler, 'mean_'):
                features = self.scaler.transform(features)
            
            # Predict anomaly
            prediction = self.model.predict(features)[0]
            anomaly_score = self.model.decision_function(features)[0]
            
            # Convert to probability (higher score = more normal)
            confidence = min(max((anomaly_score + 0.5) / 1.0, 0.0), 1.0)
            is_anomaly = prediction == -1
            
            return is_anomaly, confidence
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return False, 0.0
    
    def train_model(self, training_data: List[Dict[str, Any]]):
        """Train the ML model with new data"""
        try:
            if not training_data:
                logger.warning("No training data provided")
                return
            
            # Extract features from training data
            features_list = []
            for data in training_data:
                features = self.extract_features(data)
                features_list.append(features.flatten())
            
            X = np.array(features_list)
            
            # Fit scaler and transform data
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled)
            
            # Save model
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.model_path.replace('.pkl', '_scaler.pkl'))
            
            logger.info(f"Trained ML model with {len(training_data)} samples")
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")


class CentralAnalysisEngine:
    """Main central analysis engine coordinating all analysis components"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Initialize sub-components
        self.event_correlator = EventCorrelationEngine(self.redis_client)
        self.threat_intel = ThreatIntelligenceService(self.redis_client)
        self.ml_detector = MLThreatDetector()
        
        logger.info("Central Analysis Engine initialized")
    
    def analyze_telemetry(self, db: Session, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze telemetry data using all analysis components"""
        analysis_results = {
            "device_id": telemetry_data.get("device_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "ml_anomaly": False,
            "ml_confidence": 0.0,
            "threat_intel_matches": [],
            "risk_score": 0.0,
            "recommendations": []
        }
        
        try:
            # ML-based anomaly detection
            is_anomaly, confidence = self.ml_detector.detect_anomaly(telemetry_data)
            analysis_results["ml_anomaly"] = is_anomaly
            analysis_results["ml_confidence"] = confidence
            
            # Threat intelligence enrichment
            security_events = telemetry_data.get("security_events", [])
            for event_data in security_events:
                # Check for threat intelligence matches
                if "details" in event_data:
                    details = event_data["details"]
                    if "remote_address" in details:
                        ioc_match = self.threat_intel.check_ioc("ip", details["remote_address"])
                        if ioc_match:
                            analysis_results["threat_intel_matches"].append(ioc_match)
            
            # Calculate overall risk score
            analysis_results["risk_score"] = self._calculate_risk_score(
                telemetry_data, is_anomaly, confidence, analysis_results["threat_intel_matches"]
            )
            
            # Generate recommendations
            analysis_results["recommendations"] = self._generate_recommendations(
                telemetry_data, analysis_results
            )
            
            logger.debug(f"Analyzed telemetry for device {telemetry_data.get('device_id')}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing telemetry: {e}")
            return analysis_results
    
    def run_correlation_analysis(self, db: Session) -> List[Dict[str, Any]]:
        """Run event correlation analysis"""
        try:
            correlations = self.event_correlator.correlate_events(db)
            
            # Store correlations in Redis for quick access
            for correlation in correlations:
                correlation_key = f"correlation:{correlation['correlation_id']}"
                self.redis_client.setex(
                    correlation_key,
                    3600,  # 1 hour TTL
                    json.dumps(correlation)
                )
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            return []
    
    def update_threat_intelligence(self, db: Session) -> bool:
        """Update threat intelligence data"""
        return self.threat_intel.update_threat_intelligence(db)
    
    def _calculate_risk_score(self, telemetry_data: Dict[str, Any], is_anomaly: bool, 
                            ml_confidence: float, threat_matches: List[Dict]) -> float:
        """Calculate overall risk score for the device"""
        risk_score = 0.0
        
        # ML anomaly contribution (30%)
        if is_anomaly:
            risk_score += 0.3 * (1 - ml_confidence)
        
        # Security events contribution (40%)
        security_events = telemetry_data.get("security_events", [])
        if security_events:
            severity_weights = {"low": 0.1, "medium": 0.3, "high": 0.6, "critical": 1.0}
            event_risk = sum(
                severity_weights.get(event.get("severity", "low"), 0.1)
                for event in security_events
            ) / len(security_events)
            risk_score += 0.4 * min(event_risk, 1.0)
        
        # Threat intelligence matches contribution (20%)
        if threat_matches:
            threat_risk = sum(match.get("confidence", 0) for match in threat_matches) / len(threat_matches)
            risk_score += 0.2 * threat_risk
        
        # Compliance status contribution (10%)
        compliance_status = telemetry_data.get("compliance_status", {})
        if compliance_status:
            compliance_score = sum(compliance_status.values()) / len(compliance_status)
            risk_score += 0.1 * (1 - compliance_score)
        
        return min(risk_score, 1.0)
    
    def _generate_recommendations(self, telemetry_data: Dict[str, Any], 
                                analysis_results: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on analysis"""
        recommendations = []
        
        # ML anomaly recommendations
        if analysis_results["ml_anomaly"]:
            recommendations.append("Investigate unusual system behavior detected by ML analysis")
        
        # Security event recommendations
        security_events = telemetry_data.get("security_events", [])
        event_types = set(event.get("type") for event in security_events)
        
        if "suspicious_process" in event_types:
            recommendations.append("Review and terminate suspicious processes")
        
        if "suspicious_network" in event_types:
            recommendations.append("Investigate unusual network connections")
        
        if "high_resource_usage" in event_types:
            recommendations.append("Monitor system performance and check for resource abuse")
        
        # Threat intelligence recommendations
        if analysis_results["threat_intel_matches"]:
            recommendations.append("Block communication with known malicious indicators")
            recommendations.append("Consider quarantining device due to threat intelligence matches")
        
        # Compliance recommendations
        compliance_status = telemetry_data.get("compliance_status", {})
        if not compliance_status.get("antivirus_running", True):
            recommendations.append("Enable and update antivirus software")
        
        if not compliance_status.get("firewall_enabled", True):
            recommendations.append("Enable host-based firewall")
        
        if not compliance_status.get("os_up_to_date", True):
            recommendations.append("Install operating system updates")
        
        # Risk-based recommendations
        risk_score = analysis_results["risk_score"]
        if risk_score > 0.8:
            recommendations.append("Consider immediate quarantine due to high risk score")
        elif risk_score > 0.6:
            recommendations.append("Increase monitoring frequency for this device")
        
        return recommendations[:5]  # Limit to top 5 recommendations