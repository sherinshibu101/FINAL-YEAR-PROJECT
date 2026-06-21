"""
Endpoint Agent for Zero Trust Architecture
Collects device telemetry and security information
"""

import os
import sys
import json
import time
import psutil
import socket
import hashlib
import platform
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class DeviceTelemetry:
    """Device telemetry data structure"""
    device_id: str
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_connections: List[Dict]
    running_processes: List[Dict]
    system_info: Dict[str, str]
    security_events: List[Dict]
    compliance_status: Dict[str, bool]


@dataclass
class NetworkConnection:
    """Network connection information"""
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    status: str
    pid: int
    process_name: str


@dataclass
class Process:
    """Process information"""
    pid: int
    name: str
    username: str
    cpu_percent: float
    memory_percent: float
    cmdline: List[str]
    create_time: float


class EndpointAgent:
    def __init__(self, device_id: str, server_url: str = "http://localhost:8000"):
        self.device_id = device_id
        self.server_url = server_url
        self.running = False
        self.collection_interval = 60  # seconds
        self.heartbeat_interval = 30  # seconds
        
        # Threat detection patterns
        self.suspicious_processes = [
            "nc.exe", "netcat", "ncat", "socat",
            "powershell.exe", "cmd.exe", "wmic.exe",
            "mimikatz", "psexec", "schtasks.exe"
        ]
        
        self.suspicious_network_patterns = [
            "0.0.0.0",  # Suspicious listening
            "127.0.0.1:4444",  # Common backdoor port
            ":22",  # SSH connections (uncommon in hospital environments)
            ":23",  # Telnet
            ":135", ":445"  # SMB ports
        ]
        
        # Compliance checks
        self.required_processes = {
            "windows": ["winlogon.exe", "explorer.exe", "svchost.exe"],
            "linux": ["systemd", "init", "kthreadd"],
            "darwin": ["kernel_task", "launchd"]
        }
        
        logger.info(f"Endpoint agent initialized for device {device_id}")
    
    def get_system_info(self) -> Dict[str, str]:
        """Collect system information"""
        return {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            "uptime": str(datetime.now() - datetime.fromtimestamp(psutil.boot_time()))
        }
    
    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        return psutil.cpu_percent(interval=1)
    
    def get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        memory = psutil.virtual_memory()
        return memory.percent
    
    def get_disk_usage(self) -> float:
        """Get disk usage percentage for primary drive"""
        try:
            if platform.system() == "Windows":
                disk = psutil.disk_usage('C:')
            else:
                disk = psutil.disk_usage('/')
            return disk.percent
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return 0.0
    
    def get_network_connections(self) -> List[Dict]:
        """Get network connections"""
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN' or conn.raddr:
                    process_name = "unknown"
                    try:
                        if conn.pid:
                            process = psutil.Process(conn.pid)
                            process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    
                    conn_dict = {
                        "local_address": conn.laddr.ip if conn.laddr else "",
                        "local_port": conn.laddr.port if conn.laddr else 0,
                        "remote_address": conn.raddr.ip if conn.raddr else "",
                        "remote_port": conn.raddr.port if conn.raddr else 0,
                        "status": conn.status,
                        "pid": conn.pid or 0,
                        "process_name": process_name
                    }
                    connections.append(conn_dict)
        except Exception as e:
            logger.error(f"Error getting network connections: {e}")
        
        return connections
    
    def get_running_processes(self) -> List[Dict]:
        """Get running processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'cmdline', 'create_time']):
                try:
                    proc_dict = {
                        "pid": proc.info['pid'],
                        "name": proc.info['name'] or "unknown",
                        "username": proc.info['username'] or "unknown",
                        "cpu_percent": proc.info['cpu_percent'] or 0.0,
                        "memory_percent": proc.info['memory_percent'] or 0.0,
                        "cmdline": " ".join(proc.info['cmdline']) if proc.info['cmdline'] else "",
                        "create_time": proc.info['create_time'] or 0
                    }
                    processes.append(proc_dict)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
        
        return processes
    
    def detect_security_events(self, processes: List[Dict], connections: List[Dict]) -> List[Dict]:
        """Detect security events from telemetry data"""
        events = []
        
        # Check for suspicious processes
        for proc in processes:
            proc_name = proc['name'].lower()
            if any(suspicious in proc_name for suspicious in self.suspicious_processes):
                events.append({
                    "type": "suspicious_process",
                    "severity": "high",
                    "description": f"Suspicious process detected: {proc['name']}",
                    "details": proc,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check for suspicious network connections
        for conn in connections:
            conn_str = f"{conn['remote_address']}:{conn['remote_port']}"
            if any(pattern in conn_str for pattern in self.suspicious_network_patterns):
                events.append({
                    "type": "suspicious_network",
                    "severity": "medium",
                    "description": f"Suspicious network connection: {conn_str}",
                    "details": conn,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check for high resource usage (potential DoS or crypto mining)
        for proc in processes:
            if proc['cpu_percent'] > 80 and proc['memory_percent'] > 50:
                events.append({
                    "type": "high_resource_usage",
                    "severity": "medium",
                    "description": f"High resource usage by process: {proc['name']}",
                    "details": proc,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check for unusual network listening ports
        listening_ports = [conn['local_port'] for conn in connections if conn['status'] == 'LISTEN']
        unusual_ports = [port for port in listening_ports if port > 10000 or port in [4444, 31337, 12345]]
        
        for port in unusual_ports:
            events.append({
                "type": "unusual_listening_port",
                "severity": "medium",
                "description": f"Unusual listening port detected: {port}",
                "details": {"port": port},
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return events
    
    def check_compliance(self, processes: List[Dict]) -> Dict[str, bool]:
        """Check device compliance"""
        compliance = {
            "antivirus_running": False,
            "firewall_enabled": False,
            "os_up_to_date": False,
            "required_processes_running": False,
            "no_unauthorized_software": True
        }
        
        process_names = [proc['name'].lower() for proc in processes]
        
        # Check for antivirus processes
        antivirus_processes = ['windefend', 'avp.exe', 'avgui.exe', 'avguard.exe', 'mcshield.exe']
        compliance["antivirus_running"] = any(av in process_names for av in antivirus_processes)
        
        # Check firewall (simplified - would need OS-specific checks)
        firewall_processes = ['mpssvc', 'bfe', 'iptables', 'firewalld']
        compliance["firewall_enabled"] = any(fw in process_names for fw in firewall_processes)
        
        # Check required processes
        os_name = platform.system().lower()
        if os_name in self.required_processes:
            required = self.required_processes[os_name]
            compliance["required_processes_running"] = all(
                any(req in proc_name for proc_name in process_names) for req in required
            )
        
        # Check for unauthorized software (simplified)
        unauthorized_software = ['teamviewer', 'anydesk', 'vnc', 'remote']
        compliance["no_unauthorized_software"] = not any(
            unauth in proc_name for proc_name in process_names for unauth in unauthorized_software
        )
        
        return compliance
    
    def collect_telemetry(self) -> DeviceTelemetry:
        """Collect all telemetry data"""
        try:
            system_info = self.get_system_info()
            cpu_usage = self.get_cpu_usage()
            memory_usage = self.get_memory_usage()
            disk_usage = self.get_disk_usage()
            connections = self.get_network_connections()
            processes = self.get_running_processes()
            
            security_events = self.detect_security_events(processes, connections)
            compliance = self.check_compliance(processes)
            
            telemetry = DeviceTelemetry(
                device_id=self.device_id,
                timestamp=datetime.utcnow().isoformat(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_connections=connections,
                running_processes=processes,
                system_info=system_info,
                security_events=security_events,
                compliance_status=compliance
            )
            
            logger.debug(f"Collected telemetry for device {self.device_id}")
            return telemetry
            
        except Exception as e:
            logger.error(f"Error collecting telemetry: {e}")
            raise
    
    def send_telemetry(self, telemetry: DeviceTelemetry) -> bool:
        """Send telemetry to the central server"""
        try:
            url = f"{self.server_url}/api/telemetry"
            headers = {"Content-Type": "application/json"}
            data = asdict(telemetry)
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.debug(f"Telemetry sent successfully for device {self.device_id}")
                return True
            else:
                logger.error(f"Failed to send telemetry: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending telemetry: {e}")
            return False
    
    def send_heartbeat(self) -> bool:
        """Send heartbeat to server"""
        try:
            url = f"{self.server_url}/api/heartbeat"
            data = {
                "device_id": self.device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "online"
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False
    
    def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        logger.info(f"Starting endpoint monitoring for device {self.device_id}")
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        # Main monitoring loop
        while self.running:
            try:
                telemetry = self.collect_telemetry()
                self.send_telemetry(telemetry)
                
                time.sleep(self.collection_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping endpoint monitoring...")
                self.stop_monitoring()
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _heartbeat_loop(self):
        """Heartbeat loop running in separate thread"""
        while self.running:
            try:
                self.send_heartbeat()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                time.sleep(5)
    
    def stop_monitoring(self):
        """Stop the monitoring"""
        self.running = False
        logger.info(f"Stopped endpoint monitoring for device {self.device_id}")


class IoTDeviceAgent(EndpointAgent):
    """Specialized agent for IoT devices with limited capabilities"""
    
    def __init__(self, device_id: str, device_type: str, server_url: str = "http://localhost:8000"):
        super().__init__(device_id, server_url)
        self.device_type = device_type
        self.collection_interval = 120  # Longer interval for IoT devices
        
    def get_iot_specific_metrics(self) -> Dict[str, Any]:
        """Get IoT device specific metrics"""
        metrics = {
            "device_type": self.device_type,
            "sensor_data": {},
            "connectivity_status": "connected",
            "battery_level": 100,  # Simulated
            "firmware_version": "1.0.0",
            "last_update": datetime.utcnow().isoformat()
        }
        
        # Simulate sensor data based on device type
        if "monitor" in self.device_type.lower():
            metrics["sensor_data"] = {
                "heart_rate": 72,
                "blood_pressure": "120/80",
                "temperature": 98.6
            }
        elif "pump" in self.device_type.lower():
            metrics["sensor_data"] = {
                "flow_rate": 50.0,
                "pressure": 15.0,
                "volume_remaining": 250.0
            }
        
        return metrics
    
    def collect_telemetry(self) -> DeviceTelemetry:
        """Collect IoT-specific telemetry"""
        # Get basic telemetry
        telemetry = super().collect_telemetry()
        
        # Add IoT-specific data
        iot_metrics = self.get_iot_specific_metrics()
        telemetry.system_info.update(iot_metrics)
        
        return telemetry


def main():
    """Main function for running the endpoint agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Zero Trust Endpoint Agent")
    parser.add_argument("--device-id", required=True, help="Device ID")
    parser.add_argument("--server-url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--device-type", default="computer", help="Device type")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger.remove()
    logger.add(sys.stdout, level=log_level, format="{time} | {level} | {message}")
    logger.add(f"logs/agent_{args.device_id}.log", level=log_level, rotation="10 MB")
    
    # Create appropriate agent type
    if args.device_type in ["iot_device", "monitor", "pump"]:
        agent = IoTDeviceAgent(args.device_id, args.device_type, args.server_url)
    else:
        agent = EndpointAgent(args.device_id, args.server_url)
    
    try:
        agent.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()