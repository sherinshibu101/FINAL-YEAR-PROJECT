# SecureHealthCare

A production oriented hospital management platform with a backend, frontend, API gateway,
internal services, monitoring, and ML components.

## Features

### Core Platform
- Hospital backend service
- Frontend application
- API gateway and internal gateway
- Shared modules for common logic

### Supporting Services
- Monitoring stack
- Response handling components
- SDP controller and spa controller services
- ML engine for model-related workflows

### Security and Reliability
- Separate service boundaries
- Local development friendly structure
- Supports keeping secrets and certificates outside Git

## Quick Start

### Prerequisites
- Node.js and npm for JavaScript services
- Python for ML components
- Any required database or service dependencies for your environment

### Install

```powershell
cd Hospital-Backend
npm install

cd ..\Hospital-Frontend
npm install
```

### Run

Use the service-specific start commands defined in each folder.

## Project Structure

```text
Hospital-Backend/            Backend service
Hospital-Frontend/           Frontend application
api-gateway/                 Public API gateway
backend-internal-gateway/    Internal service gateway
ml-engine/                   Machine learning engine
monitoring/                  Observability and dashboard config
response/                    Response-related modules
sdp-controller/              Controller service
shared/                      Shared utilities and code
spa-controller/              SPA controller service
```


