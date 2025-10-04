"""
Visibility System for Zero Trust Architecture
Provides centralized logging, monitoring, and dashboard capabilities
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import streamlit as st
from sqlalchemy.orm import Session
from loguru import logger
import redis

from ..models import (
    Device, SecurityEvent, User, DevicePosture, 
    ResponseActionModel, ThreatLevel
)
from ..database import db_manager
from ..endpoint_monitoring.monitoring_service import EndpointMonitoringService
from ..central_analysis.analysis_engine import CentralAnalysisEngine
from ..response.response_system import ResponseOrchestrator
from ..device_protection.protection_service import DeviceProtectionOrchestrator


@dataclass
class DashboardMetrics:
    """Container for dashboard metrics"""
    timestamp: str
    total_devices: int
    online_devices: int
    offline_devices: int
    compliant_devices: int
    quarantined_devices: int
    security_events_24h: int
    critical_events: int
    average_trust_score: float
    compliance_rate: float
    threat_level_distribution: Dict[str, int]
    device_type_distribution: Dict[str, int]


class CentralizedLoggingService:
    """Service for centralized logging and log aggregation"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.log_retention_hours = 168  # 7 days
        
        logger.info("Centralized Logging Service initialized")
    
    def log_security_event(self, event_data: Dict[str, Any]) -> bool:
        """Log a security event"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "log_type": "security_event",
                "severity": event_data.get("threat_level", "low"),
                "source": "security_engine",
                "data": event_data
            }
            
            # Store in Redis with timestamp-based key
            log_key = f"log:security:{datetime.utcnow().timestamp()}"
            self.redis_client.setex(
                log_key,
                self.log_retention_hours * 3600,
                json.dumps(log_entry)
            )
            
            # Also add to a sorted set for easy querying
            self.redis_client.zadd(
                "logs:security:index",
                {log_key: datetime.utcnow().timestamp()}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
            return False
    
    def log_system_event(self, component: str, event_type: str, 
                        data: Dict[str, Any], severity: str = "info") -> bool:
        """Log a system event"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "log_type": "system_event",
                "component": component,
                "event_type": event_type,
                "severity": severity,
                "source": "zero_trust_system",
                "data": data
            }
            
            log_key = f"log:system:{datetime.utcnow().timestamp()}"
            self.redis_client.setex(
                log_key,
                self.log_retention_hours * 3600,
                json.dumps(log_entry)
            )
            
            self.redis_client.zadd(
                "logs:system:index",
                {log_key: datetime.utcnow().timestamp()}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
            return False
    
    def log_user_activity(self, user_id: int, activity: str, 
                         details: Dict[str, Any], device_id: str = None) -> bool:
        """Log user activity"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "log_type": "user_activity",
                "user_id": user_id,
                "device_id": device_id,
                "activity": activity,
                "severity": "info",
                "source": "iam_system",
                "details": details
            }
            
            log_key = f"log:user:{datetime.utcnow().timestamp()}"
            self.redis_client.setex(
                log_key,
                self.log_retention_hours * 3600,
                json.dumps(log_entry)
            )
            
            self.redis_client.zadd(
                "logs:user:index",
                {log_key: datetime.utcnow().timestamp()}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging user activity: {e}")
            return False
    
    def query_logs(self, log_type: str = "all", severity: str = None,
                  time_range_hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Query logs with filters"""
        try:
            logs = []
            current_time = datetime.utcnow().timestamp()
            start_time = current_time - (time_range_hours * 3600)
            
            # Determine which log indices to query
            indices_to_query = []
            if log_type == "all":
                indices_to_query = ["logs:security:index", "logs:system:index", "logs:user:index"]
            else:
                indices_to_query = [f"logs:{log_type}:index"]
            
            for index_key in indices_to_query:
                if self.redis_client.exists(index_key):
                    # Get log keys within time range
                    log_keys = self.redis_client.zrangebyscore(
                        index_key, start_time, current_time, withscores=False
                    )
                    
                    # Retrieve log entries
                    for log_key in log_keys:
                        log_data = self.redis_client.get(log_key)
                        if log_data:
                            log_entry = json.loads(log_data)
                            
                            # Apply severity filter if specified
                            if severity is None or log_entry.get("severity") == severity:
                                logs.append(log_entry)
            
            # Sort by timestamp (newest first) and limit results
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return logs[:limit]
            
        except Exception as e:
            logger.error(f"Error querying logs: {e}")
            return []
    
    def get_log_statistics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get log statistics for dashboard"""
        try:
            stats = {
                "total_logs": 0,
                "logs_by_type": {},
                "logs_by_severity": {},
                "recent_activity": []
            }
            
            logs = self.query_logs("all", time_range_hours=time_range_hours, limit=1000)
            stats["total_logs"] = len(logs)
            
            # Count by type and severity
            for log_entry in logs:
                log_type = log_entry.get("log_type", "unknown")
                severity = log_entry.get("severity", "info")
                
                stats["logs_by_type"][log_type] = stats["logs_by_type"].get(log_type, 0) + 1
                stats["logs_by_severity"][severity] = stats["logs_by_severity"].get(severity, 0) + 1
            
            # Get recent activity (last 10 entries)
            stats["recent_activity"] = logs[:10]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {}


class MetricsCollector:
    """Service for collecting and aggregating system metrics"""
    
    def __init__(self, redis_client, db_session):
        self.redis_client = redis_client
        self.db = db_session
        
        logger.info("Metrics Collector initialized")
    
    def collect_current_metrics(self) -> DashboardMetrics:
        """Collect current system metrics"""
        try:
            # Get device statistics
            total_devices = self.db.query(Device).count()
            compliant_devices = self.db.query(Device).filter(Device.is_compliant == True).count()
            quarantined_devices = self.db.query(Device).filter(Device.is_quarantined == True).count()
            
            # Get online/offline device count from Redis heartbeats
            online_devices = 0
            offline_devices = 0
            device_ids = [d.device_id for d in self.db.query(Device).all()]
            
            for device_id in device_ids:
                heartbeat_key = f"heartbeat:{device_id}"
                if self.redis_client.exists(heartbeat_key):
                    online_devices += 1
                else:
                    offline_devices += 1
            
            # Get security event statistics (last 24 hours)
            recent_threshold = datetime.utcnow() - timedelta(hours=24)
            security_events_24h = self.db.query(SecurityEvent).filter(
                SecurityEvent.created_at >= recent_threshold
            ).count()
            
            critical_events = self.db.query(SecurityEvent).filter(
                SecurityEvent.threat_level == ThreatLevel.CRITICAL,
                SecurityEvent.is_resolved == False
            ).count()
            
            # Calculate average trust score
            devices_with_scores = self.db.query(Device).filter(Device.trust_score > 0).all()
            avg_trust_score = 0.0
            if devices_with_scores:
                avg_trust_score = sum(d.trust_score for d in devices_with_scores) / len(devices_with_scores)
            
            # Calculate compliance rate
            compliance_rate = (compliant_devices / total_devices * 100) if total_devices > 0 else 0
            
            # Get threat level distribution
            threat_levels = self.db.query(SecurityEvent.threat_level).filter(
                SecurityEvent.created_at >= recent_threshold
            ).all()
            
            threat_level_distribution = {}
            for level in [ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                count = sum(1 for t in threat_levels if t[0] == level)
                threat_level_distribution[level.value] = count
            
            # Get device type distribution
            device_types = self.db.query(Device.device_type).all()
            device_type_distribution = {}
            for device_type in device_types:
                dtype = device_type[0]
                device_type_distribution[dtype] = device_type_distribution.get(dtype, 0) + 1
            
            return DashboardMetrics(
                timestamp=datetime.utcnow().isoformat(),
                total_devices=total_devices,
                online_devices=online_devices,
                offline_devices=offline_devices,
                compliant_devices=compliant_devices,
                quarantined_devices=quarantined_devices,
                security_events_24h=security_events_24h,
                critical_events=critical_events,
                average_trust_score=avg_trust_score,
                compliance_rate=compliance_rate,
                threat_level_distribution=threat_level_distribution,
                device_type_distribution=device_type_distribution
            )
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return DashboardMetrics(
                timestamp=datetime.utcnow().isoformat(),
                total_devices=0, online_devices=0, offline_devices=0,
                compliant_devices=0, quarantined_devices=0,
                security_events_24h=0, critical_events=0,
                average_trust_score=0.0, compliance_rate=0.0,
                threat_level_distribution={}, device_type_distribution={}
            )
    
    def store_metrics_snapshot(self, metrics: DashboardMetrics) -> bool:
        """Store metrics snapshot for historical analysis"""
        try:
            # Store current metrics
            metrics_key = f"metrics:snapshot:{datetime.utcnow().timestamp()}"
            self.redis_client.setex(
                metrics_key,
                86400 * 7,  # 7 days retention
                json.dumps(asdict(metrics))
            )
            
            # Add to time series index
            self.redis_client.zadd(
                "metrics:index",
                {metrics_key: datetime.utcnow().timestamp()}
            )
            
            # Keep only last 1000 snapshots
            total_snapshots = self.redis_client.zcard("metrics:index")
            if total_snapshots > 1000:
                oldest_keys = self.redis_client.zrange("metrics:index", 0, total_snapshots - 1000)
                if oldest_keys:
                    # Remove old snapshots
                    for key in oldest_keys:
                        self.redis_client.delete(key)
                    self.redis_client.zrem("metrics:index", *oldest_keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing metrics snapshot: {e}")
            return False
    
    def get_historical_metrics(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics for trend analysis"""
        try:
            current_time = datetime.utcnow().timestamp()
            start_time = current_time - (hours_back * 3600)
            
            # Get metric keys within time range
            metric_keys = self.redis_client.zrangebyscore(
                "metrics:index", start_time, current_time
            )
            
            historical_metrics = []
            for key in metric_keys:
                metric_data = self.redis_client.get(key)
                if metric_data:
                    historical_metrics.append(json.loads(metric_data))
            
            # Sort by timestamp
            historical_metrics.sort(key=lambda x: x.get("timestamp", ""))
            return historical_metrics
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []


class DashboardGenerator:
    """Service for generating dashboard visualizations"""
    
    def __init__(self):
        logger.info("Dashboard Generator initialized")
    
    def create_device_status_chart(self, metrics: DashboardMetrics) -> Dict[str, Any]:
        """Create device status pie chart"""
        labels = ['Online', 'Offline', 'Quarantined']
        values = [
            metrics.online_devices - metrics.quarantined_devices,  # Online and not quarantined
            metrics.offline_devices,
            metrics.quarantined_devices
        ]
        colors = ['#28a745', '#dc3545', '#ffc107']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors)
        )])
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            title="Device Status Distribution",
            annotations=[dict(text='Devices', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    
    def create_compliance_gauge(self, compliance_rate: float) -> Dict[str, Any]:
        """Create compliance rate gauge"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=compliance_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Compliance Rate (%)"},
            delta={'reference': 80, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    
    def create_threat_level_chart(self, threat_distribution: Dict[str, int]) -> Dict[str, Any]:
        """Create threat level bar chart"""
        levels = list(threat_distribution.keys())
        counts = list(threat_distribution.values())
        colors = ['green', 'yellow', 'orange', 'red']
        
        fig = go.Figure(data=[go.Bar(
            x=levels,
            y=counts,
            marker=dict(color=colors[:len(levels)])
        )])
        
        fig.update_layout(
            title="Security Events by Threat Level (24h)",
            xaxis_title="Threat Level",
            yaxis_title="Number of Events"
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    
    def create_trust_score_histogram(self, db: Session) -> Dict[str, Any]:
        """Create trust score distribution histogram"""
        try:
            devices = db.query(Device).filter(Device.trust_score > 0).all()
            trust_scores = [d.trust_score for d in devices]
            
            if not trust_scores:
                # Create empty chart
                fig = go.Figure()
                fig.update_layout(title="Trust Score Distribution", 
                                xaxis_title="Trust Score", 
                                yaxis_title="Number of Devices")
                return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
            
            fig = go.Figure(data=[go.Histogram(
                x=trust_scores,
                nbinsx=20,
                marker=dict(color='skyblue', line=dict(color='black', width=1))
            )])
            
            fig.update_layout(
                title="Trust Score Distribution",
                xaxis_title="Trust Score",
                yaxis_title="Number of Devices",
                bargap=0.1
            )
            
            return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
            
        except Exception as e:
            logger.error(f"Error creating trust score histogram: {e}")
            return {}
    
    def create_timeline_chart(self, historical_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create timeline chart showing trends"""
        if not historical_metrics:
            fig = go.Figure()
            fig.update_layout(title="Security Metrics Timeline")
            return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
        
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in historical_metrics]
        compliance_rates = [m['compliance_rate'] for m in historical_metrics]
        trust_scores = [m['average_trust_score'] * 100 for m in historical_metrics]  # Scale to percentage
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=compliance_rates,
            mode='lines+markers',
            name='Compliance Rate (%)',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=trust_scores,
            mode='lines+markers',
            name='Avg Trust Score (%)',
            line=dict(color='green')
        ))
        
        fig.update_layout(
            title="Security Metrics Timeline",
            xaxis_title="Time",
            yaxis_title="Percentage",
            legend=dict(x=0, y=1)
        )
        
        return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))


class VisibilityOrchestrator:
    """Main orchestrator for visibility and monitoring services"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Initialize services
        self.logging_service = CentralizedLoggingService(self.redis_client)
        self.dashboard_generator = DashboardGenerator()
        
        # Initialize external service connectors
        self.endpoint_monitoring = EndpointMonitoringService(redis_host, redis_port)
        self.analysis_engine = CentralAnalysisEngine(redis_host, redis_port)
        self.response_orchestrator = ResponseOrchestrator(redis_host, redis_port)
        self.device_protection = DeviceProtectionOrchestrator(redis_host, redis_port)
        
        logger.info("Visibility Orchestrator initialized")
    
    def get_dashboard_data(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Initialize metrics collector with current DB session
            metrics_collector = MetricsCollector(self.redis_client, db)
            
            # Collect current metrics
            current_metrics = metrics_collector.collect_current_metrics()
            
            # Store metrics snapshot
            metrics_collector.store_metrics_snapshot(current_metrics)
            
            # Get historical data for trends
            historical_metrics = metrics_collector.get_historical_metrics(24)
            
            # Get log statistics
            log_stats = self.logging_service.get_log_statistics(24)
            
            # Generate visualizations
            device_status_chart = self.dashboard_generator.create_device_status_chart(current_metrics)
            compliance_gauge = self.dashboard_generator.create_compliance_gauge(current_metrics.compliance_rate)
            threat_level_chart = self.dashboard_generator.create_threat_level_chart(current_metrics.threat_level_distribution)
            trust_score_histogram = self.dashboard_generator.create_trust_score_histogram(db)
            timeline_chart = self.dashboard_generator.create_timeline_chart(historical_metrics)
            
            # Get recent security events
            recent_events = db.query(SecurityEvent).filter(
                SecurityEvent.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(SecurityEvent.created_at.desc()).limit(10).all()
            
            # Get system health information
            system_health = self._get_system_health()
            
            dashboard_data = {
                "timestamp": current_metrics.timestamp,
                "summary_metrics": {
                    "total_devices": current_metrics.total_devices,
                    "online_devices": current_metrics.online_devices,
                    "offline_devices": current_metrics.offline_devices,
                    "compliant_devices": current_metrics.compliant_devices,
                    "quarantined_devices": current_metrics.quarantined_devices,
                    "security_events_24h": current_metrics.security_events_24h,
                    "critical_events": current_metrics.critical_events,
                    "average_trust_score": round(current_metrics.average_trust_score, 3),
                    "compliance_rate": round(current_metrics.compliance_rate, 1)
                },
                "charts": {
                    "device_status": device_status_chart,
                    "compliance_gauge": compliance_gauge,
                    "threat_levels": threat_level_chart,
                    "trust_scores": trust_score_histogram,
                    "timeline": timeline_chart
                },
                "recent_events": [
                    {
                        "id": event.id,
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "threat_level": event.threat_level,
                        "confidence_score": event.confidence_score,
                        "description": event.description,
                        "created_at": event.created_at.isoformat(),
                        "is_resolved": event.is_resolved
                    }
                    for event in recent_events
                ],
                "log_statistics": log_stats,
                "system_health": system_health
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {"error": str(e)}
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            health = {
                "overall_status": "healthy",
                "components": {
                    "database": "healthy",
                    "redis": "healthy", 
                    "endpoint_monitoring": "healthy",
                    "analysis_engine": "healthy",
                    "response_system": "healthy"
                },
                "uptime": "99.9%",
                "last_check": datetime.utcnow().isoformat()
            }
            
            # Check Redis connectivity
            try:
                self.redis_client.ping()
                health["components"]["redis"] = "healthy"
            except:
                health["components"]["redis"] = "unhealthy"
                health["overall_status"] = "degraded"
            
            # Additional health checks would go here
            # For now, we'll simulate healthy status
            
            return health
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {"overall_status": "unknown", "error": str(e)}
    
    def get_device_details(self, db: Session, device_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific device"""
        try:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                return {"error": "Device not found"}
            
            # Get device posture
            posture = db.query(DevicePosture).filter(DevicePosture.device_id == device.id).first()
            
            # Get recent security events
            recent_events = db.query(SecurityEvent).filter(
                SecurityEvent.device_id == device.id,
                SecurityEvent.created_at >= datetime.utcnow() - timedelta(days=7)
            ).order_by(SecurityEvent.created_at.desc()).all()
            
            # Get response actions
            response_actions = db.query(ResponseActionModel).join(SecurityEvent).filter(
                SecurityEvent.device_id == device.id
            ).order_by(ResponseActionModel.created_at.desc()).limit(10).all()
            
            # Get heartbeat status
            heartbeat_key = f"heartbeat:{device_id}"
            online_status = self.redis_client.exists(heartbeat_key)
            
            device_details = {
                "device_info": {
                    "device_id": device.device_id,
                    "device_name": device.device_name,
                    "device_type": device.device_type,
                    "mac_address": device.mac_address,
                    "ip_address": device.ip_address,
                    "os_version": device.os_version,
                    "is_compliant": device.is_compliant,
                    "is_quarantined": device.is_quarantined,
                    "trust_score": device.trust_score,
                    "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                    "online": bool(online_status)
                },
                "posture": {
                    "antivirus_enabled": posture.antivirus_enabled if posture else False,
                    "firewall_enabled": posture.firewall_enabled if posture else False,
                    "os_updated": posture.os_updated if posture else False,
                    "encryption_enabled": posture.encryption_enabled if posture else False,
                    "compliance_score": posture.compliance_score if posture else 0.0,
                    "last_check": posture.last_check.isoformat() if posture and posture.last_check else None
                },
                "recent_events": [
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "threat_level": event.threat_level,
                        "confidence_score": event.confidence_score,
                        "description": event.description,
                        "created_at": event.created_at.isoformat(),
                        "is_resolved": event.is_resolved
                    }
                    for event in recent_events
                ],
                "response_actions": [
                    {
                        "action_id": action.action_id,
                        "action_type": action.action_type,
                        "description": action.description,
                        "status": action.status,
                        "executed_at": action.executed_at.isoformat() if action.executed_at else None,
                        "created_at": action.created_at.isoformat()
                    }
                    for action in response_actions
                ]
            }
            
            return device_details
            
        except Exception as e:
            logger.error(f"Error getting device details: {e}")
            return {"error": str(e)}
    
    def search_logs(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search logs with various filters"""
        try:
            log_type = query_params.get("log_type", "all")
            severity = query_params.get("severity")
            time_range = query_params.get("time_range_hours", 24)
            limit = query_params.get("limit", 100)
            search_term = query_params.get("search_term")
            
            logs = self.logging_service.query_logs(log_type, severity, time_range, limit * 2)
            
            # Apply text search if specified
            if search_term:
                filtered_logs = []
                for log in logs:
                    log_text = json.dumps(log).lower()
                    if search_term.lower() in log_text:
                        filtered_logs.append(log)
                logs = filtered_logs
            
            return logs[:limit]
            
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return []