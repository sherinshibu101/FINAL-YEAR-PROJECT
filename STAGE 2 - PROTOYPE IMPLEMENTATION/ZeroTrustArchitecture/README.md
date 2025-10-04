# Zero Trust Architecture Simulation

A comprehensive Zero Trust security system simulation designed for healthcare environments, demonstrating the complete workflow from threat detection to automated response.

## 🏗️ Architecture Overview

This simulation implements a complete Zero Trust Architecture with the following components:

### Phase 1: Identity & Access Management
- **Multi-Factor Authentication (MFA)** with TOTP support
- **Role-Based Access Control (RBAC)** with healthcare-specific roles
- **Session Management** with device tracking
- **Microsegmentation** for network isolation
- **Secure Access Proxy** for controlled resource access

### Phase 2: Endpoint Monitoring
- **Device Registration** and health tracking
- **Real-time Telemetry Collection** from agents
- **Heartbeat Monitoring** for device status
- **IoT Device Support** with specialized monitoring

### Central Analysis Engine
- **Event Correlation** across devices and time
- **Threat Intelligence Feeds** integration
- **ML-based Anomaly Detection** using Isolation Forest
- **Risk Scoring** and assessment

### Response System
- **Automated Response Actions**: Device isolation, quarantine, access revocation
- **Incident Management** with escalation workflows
- **Multi-channel Notifications**: Email, Slack, SMS
- **Response Orchestration** with configurable policies

### Device & Data Protection
- **Device Posture Assessment** with compliance checking
- **Encryption Management** with key rotation
- **Data Loss Prevention** with sensitive data detection
- **Policy Enforcement** automation

### Centralized Visibility
- **Real-time Dashboard** with interactive charts
- **Centralized Logging** with search capabilities
- **Historical Metrics** and trend analysis
- **System Health Monitoring**

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Docker Desktop** (optional, for supporting services)
3. **Git** for cloning the repository

### Installation Steps

1. **Navigate to the project directory:**
   ```powershell
   cd C:\Users\VARUN DIPU SANKAR\ZeroTrustArchitecture
   ```

2. **Create a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Create necessary directories:**
   ```powershell
   New-Item -ItemType Directory -Force -Path logs, data
   ```

### Running with Docker (Recommended)

5. **Start supporting services:**
   ```powershell
   docker-compose up -d
   ```
   This starts Redis, Elasticsearch, Kibana, Prometheus, Grafana, and RabbitMQ.

### Running without Docker

5. **Install Redis locally** (or use Redis Cloud)
6. **Update config/config.yaml** with your Redis connection details

## 🎯 Running the Demonstration

### Step 1: Start the Zero Trust System

```powershell
python main.py
```

The system will start on `http://localhost:8000` and automatically:
- Initialize the database with sample data
- Start background monitoring tasks
- Expose REST API endpoints

### Step 2: Run the Interactive Demo

In a new terminal:

```powershell
python demo.py
```

This will run a comprehensive demonstration showcasing:

#### 🔧 Phase 0: System Health Check
- Verifies all services are running
- Checks database and Redis connectivity

#### 🔐 Phase 1: Identity & Access Management
- Demonstrates user authentication
- Shows JWT token generation
- Simulates user registration

#### 📊 Phase 2: Device Registration & Monitoring
- Registers hospital computers, laptops, and IoT devices
- Sends heartbeat signals
- Transmits realistic telemetry data

#### 🛡️ Phase 3: Security Event Processing
- Creates various types of security events
- Shows event classification and processing
- Demonstrates confidence scoring

#### 🎯 Phase 4: Threat Detection & Analysis
- Simulates coordinated attack scenarios
- Shows event correlation across devices
- Demonstrates threat intelligence matching

#### ⚡ Phase 5: Automated Response
- Triggers automated response actions
- Shows device quarantine and isolation
- Demonstrates incident creation

#### 🔒 Phase 6: Device Protection & Compliance
- Assesses device security posture
- Shows compliance checking
- Demonstrates policy enforcement

#### 📈 Phase 7: Dashboard & Visibility
- Displays real-time security metrics
- Shows device status and trust scores
- Demonstrates log search capabilities

## 🔍 Exploring the System

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Dashboard Access
The system provides REST endpoints for dashboard data at:
- `/api/dashboard` - Complete dashboard metrics
- `/api/devices` - Device listing and details
- `/api/events` - Security events
- `/api/logs` - Centralized logs

### Sample Credentials
The system comes with pre-configured users:

| Username | Password | Role | Department |
|----------|----------|------|------------|
| admin | admin123 | system_admin | IT |
| dr.smith | doctor123 | admin | clinical |
| nurse.jane | nurse123 | user | nursing |
| security.admin | security123 | security_admin | security |

## 🧪 Testing Scenarios

### Scenario 1: Malware Detection
```powershell
# This creates a critical security event that triggers automated response
curl -X POST "http://localhost:8000/api/events" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "malware_detection",
    "device_id": 1,
    "threat_level": "critical", 
    "confidence_score": 0.95,
    "description": "Ransomware detected"
  }'
```

### Scenario 2: Device Compliance Check
```powershell
# Assess device security with compliance issues
curl -X POST "http://localhost:8000/api/devices/DEMO-PC-001/assess-security" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '@sample_telemetry.json'
```

### Scenario 3: Manual Response Actions
```powershell
# Quarantine a device
curl -X POST "http://localhost:8000/api/devices/DEMO-PC-001/quarantine?reason=Security%20incident"

# Release from quarantine  
curl -X POST "http://localhost:8000/api/devices/DEMO-PC-001/release-quarantine"
```

## 📊 Monitoring and Observability

### Real-time Metrics
- **Device Status**: Online/offline status with heartbeat monitoring
- **Trust Scores**: ML-based device trust assessment
- **Compliance Rates**: Percentage of compliant devices
- **Threat Levels**: Distribution of security events by severity

### Log Analysis
- **Centralized Logging**: All events stored in Redis with time-based indexing
- **Search Capabilities**: Full-text search across logs
- **Log Retention**: Configurable retention periods

### Dashboard Visualizations
- **Device Status Pie Chart**: Visual breakdown of device states
- **Compliance Gauge**: Real-time compliance percentage
- **Threat Timeline**: Security events over time
- **Trust Score Distribution**: Histogram of device trust scores

## 🛠️ Configuration

### Database Configuration
Edit `config/config.yaml` to configure database settings:

```yaml
database:
  url: "sqlite:///./data/zerotrust.db"
  echo: false
```

### Security Settings
```yaml
api:
  secret_key: "your-secret-key-change-in-production"
  access_token_expire_minutes: 30

identity:
  mfa_required: true
  session_timeout: 1800
  max_failed_attempts: 3
```

### Monitoring Configuration
```yaml
endpoint_monitoring:
  collection_interval: 60
  agent_heartbeat: 30
  
threat_detection:
  confidence_threshold: 0.7
  anomaly_threshold: 2.0
```

## 🔧 Extending the System

### Adding New Device Types
1. Update `DeviceType` enum in `src/models.py`
2. Add compliance requirements in `src/device_protection/protection_service.py`
3. Create specialized agent in `src/endpoint_monitoring/`

### Custom Threat Detection Rules
1. Add correlation rules in `src/central_analysis/analysis_engine.py`
2. Implement custom ML models for specific threats
3. Update threat intelligence feeds

### Response Actions
1. Define new response actions in `ResponseAction` enum
2. Implement action logic in `src/response/response_system.py`
3. Configure notification channels

## 📈 Performance Considerations

### Scalability
- **Redis Caching**: Reduces database load for frequent queries
- **Background Tasks**: Asynchronous processing of telemetry and events
- **Batch Processing**: Efficient handling of multiple device updates

### Security
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Pydantic models for request validation
- **Encryption**: AES-256-GCM for sensitive data protection

### Monitoring
- **Prometheus Metrics**: System performance monitoring
- **Health Checks**: Automatic service health monitoring
- **Log Rotation**: Prevents disk space issues

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```
   Error: Port 8000 is already in use
   ```
   Solution: Change port in `main.py` or kill the existing process

2. **Redis Connection Failed**
   ```
   Error: Redis connection failed
   ```
   Solution: Start Redis with `docker-compose up -d redis`

3. **Database Lock Error**
   ```
   Error: database is locked
   ```
   Solution: Ensure only one instance is running

### Debug Mode
Start the server in debug mode:
```powershell
python main.py --debug
```

### Log Files
Check log files in the `logs/` directory:
- `zerotrust.log` - Main application logs
- `demo.log` - Demonstration script logs

## 📚 API Reference

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout

### Device Management
- `GET /api/devices` - List all devices
- `POST /api/devices/register` - Register new device
- `GET /api/devices/{device_id}` - Get device details
- `POST /api/devices/{device_id}/quarantine` - Quarantine device
- `POST /api/devices/{device_id}/release-quarantine` - Release quarantine

### Security Events
- `GET /api/events` - List security events
- `POST /api/events` - Create security event

### Telemetry
- `POST /api/telemetry` - Submit device telemetry
- `POST /api/heartbeat` - Send device heartbeat

### Dashboard & Monitoring  
- `GET /api/dashboard` - Get dashboard data
- `GET /api/logs` - Search logs
- `GET /health` - System health check

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **SQLAlchemy** for database ORM
- **Plotly** for interactive visualizations
- **Scikit-learn** for machine learning capabilities
- **Redis** for high-performance caching
- **Docker** for containerization support

---

## 📞 Support

For questions, issues, or contributions, please create an issue in the repository or contact the development team.

**Zero Trust Architecture Simulation v1.0** - Comprehensive healthcare security demonstration system.