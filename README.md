# ☁️ Toomer Cloud — Distributed Microservices Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Docker Support](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Architecture](https://img.shields.io/badge/Architecture-Cloud--Native-success)](#system-architecture)

> High-throughput, distributed cloud microservices engine engineered for resilient task processing, asynchronous event streams, and enterprise workflow automation.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    Client["Client / Webhook Trigger"] --> API["FastAPI Gateway"]
    API --> Auth["Token & Auth Verifier"]
    Auth --> Queue["Asynchronous Task Broker"]
    Queue --> Worker1["Worker Node 01 (ETL / Compute)"]
    Queue --> Worker2["Worker Node 02 (Media / Automation)"]
    Worker1 --> Telemetry["DuckDB / State Store"]
    Worker2 --> Telemetry
    Telemetry --> Output["Consolidated Webhook Response"]
```

---

## ⚡ Core Capabilities

- **Distributed Task Scheduling**: Asynchronous background job distribution with zero unhandled event loss.
- **Resilient Microservices**: Fault-tolerant service discovery, circuit-breaker retry logic, and exponential backoff.
- **Enterprise Security**: Strict environment isolation, rate-limiting, and header-based credential verification.
- **Production Telemetry**: Real-time logging, health check probes (`/healthz`), and system metrics.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- Docker & Docker Compose (Optional for containerization)

### Installation
```bash
# Clone the repository
git clone https://github.com/kushaggarwal2007-byte/toomer-cloud.git
cd toomer-cloud

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Create a `.env` file in the project root:
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### Running Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🛡️ License & Author

Developed & maintained by **Kush Aggarwal** ([@kushaggarwal2007-byte](https://github.com/kushaggarwal2007-byte)).  
Released under the [MIT License](LICENSE).
