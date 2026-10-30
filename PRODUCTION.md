# NIRIKSHA: The AICTE Approval Control Room
## Enterprise Production Deployment & Operations Manual
**Problem Statement 26262** — *Integrated AICTE Approval Workflow Automation, Compliance Monitoring, and Alert Management System*

---

## 1. Architectural Topology

NIRIKSHA is architected as an **Enterprise Decoupled System** packaged for **Zero-Friction Unified Deployment**:

```
                       [ Incoming Traffic (HTTPS 443 / HTTP 80) ]
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │   Nginx Reverse Proxy & Edge Gateway   │
                      │   - SSL Termination & Modern Ciphers   │
                      │   - Rate Limiting (30 req/s, burst 50) │
                      │   - Asset Cache (Cache-Control 1 year) │
                      │   - Correlation ID Injection           │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │   Gunicorn Master ASGI Process (x4)    │
                      │   Supervising Uvicorn Worker Pools     │
                      └───────────────────┬────────────────────┘
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 │                                                 │
                 ▼                                                 ▼
┌─────────────────────────────────┐               ┌─────────────────────────────────┐
│     FastAPI Core Services       │               │      React 19 Control Room      │
│  - Statechart Workflow Engine   │               │  - Responsive Officer Console   │
│  - Working-Day SLA Calculator   │               │  - Live Timeline & Gantt View   │
│  - ML Early-Warning Predictor   │               │  - Audit Ledger Live Verifier   │
│  - CP-SAT EVC Committee Solver  │               │  - Rules Studio (APH-as-Code)   │
│  - Schneier-Kelsey Hash Ledger  │               │  - Static assets at /assets     │
└────────────────┬────────────────┘               └─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│             Neon Serverless PostgreSQL DB Cluster                │
│             - Pooled Connection Endpoint (Port 5432/6543)        │
│             - Auto-Suspend Resilient (pool_pre_ping=True)        │
│             - Stale Socket Prevention (pool_recycle=300s)        │
│             - 24 Enterprise Relational Tables                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Production Deployment Options

### Option A: Containerized Deployment via Docker (Recommended)

NIRIKSHA includes a hardened, multi-stage `Dockerfile` and `docker-compose.yml`:
- **Stage 1 (Frontend Builder)**: Node.js 20 Alpine compiles the React 19 SPA into optimized, minified chunks.
- **Stage 2 (Runtime)**: Minimalist Python 3.12-slim runs as an unprivileged user (`niriksha:1001`) with built-in health probes.

#### 1. Setup Environment
```bash
cp .env.example .env
# Edit .env to supply your Neon PostgreSQL connection string and secret key
nano .env
```

#### 2. Launch with Docker Compose
```bash
docker compose up -d --build
```

#### 3. Verify Container Status & Health
```bash
docker compose ps
docker compose logs -f niriksha
curl -f http://localhost:8000/health/ready
```

---

### Option B: Bare-Metal / Linux VM Enterprise Deployment (Ubuntu / Debian)

For production deployment on dedicated AWS EC2, GCP Compute Engine, or National Informatics Centre (NIC) bare-metal servers:

#### 1. Prerequisites & User Creation
```bash
sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv libpq-dev curl nginx
sudo useradd -m -s /bin/bash -u 1001 niriksha
sudo mkdir -p /opt/niriksha && sudo chown niriksha:niriksha /opt/niriksha
```

#### 2. Deploy Code & Setup Virtualenv
```bash
cd /opt/niriksha
# Clone or copy application repository
python3.12 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

#### 3. Build Production Frontend
```bash
cd /opt/niriksha/frontend
npm ci
npm run build
cd /opt/niriksha
```

#### 4. Configure Systemd Service
```bash
sudo cp niriksha.service /etc/systemd/system/niriksha.service
sudo systemctl daemon-reload
sudo systemctl enable niriksha
sudo systemctl start niriksha
sudo systemctl status niriksha
```

#### 5. Configure Nginx Reverse Proxy
```bash
sudo cp nginx.conf /etc/nginx/sites-available/niriksha.conf
sudo ln -s /etc/nginx/sites-available/niriksha.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

### Option C: Enterprise Evaluation / Demo Mode (Windows / macOS / Linux)

To run the unified production server directly on any workstation:

```bash
# 1. Activate Python virtual environment
source venv/bin/activate       # On Linux / macOS
.\venv\Scripts\Activate.ps1    # On Windows PowerShell

# 2. Build the production React bundle (if not already compiled)
cd frontend
npm run build
cd ..

# 3. Launch the unified enterprise server
python run_production.py
```
Open **`http://localhost:8000`** in your browser.

---

## 3. Database Resilience & Neon PostgreSQL Tuning

NIRIKSHA is configured out of the box for **Neon Serverless PostgreSQL** with resilience against scale-to-zero / connection drops:

| Parameter | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://...-pooler.neon.tech/...` | Utilizes Neon's built-in PgBouncer pooler for massive concurrency. |
| `DB_POOL_PRE_PING` | `True` | Emits a lightweight `SELECT 1` heartbeat prior to connection checkout to prevent stale socket errors during auto-resume. |
| `DB_POOL_RECYCLE` | `300` (5 minutes) | Periodically recycles connections to prevent firewall / NAT idle connection drops. |
| `DB_POOL_SIZE` | `15` | Baseline persistent connection pool. |
| `DB_MAX_OVERFLOW` | `25` | Temporary burst headroom for concurrent statutory batch sweeps. |
| `DB_POOL_TIMEOUT` | `30` | Seconds to block before returning connection timeout error. |

### Database Seeding & Reseeding
To reseed the database with the benchmark 60 AICTE institutional dossiers and 180+ cryptographic audit events:
```bash
# Via API Endpoint (curl)
curl -X POST http://localhost:8000/system/reseed

# Or via Python CLI
python -c "from app.data.seed_data import seed_database; seed_database()"
```

---

## 4. Security & Cryptographic Audit Verification

### Schneier-Kelsey (1999) Hash-Chained Audit Ledger
Every state change, document upload, scrutiny finding, and escalation is cryptographically sealed in an append-only ledger using forward-secure hashing:
$$h_i = \text{SHA-256}(h_{i-1} \parallel \text{event}_i)$$

To run a live cryptographic integrity audit:
```bash
curl -X GET http://localhost:8000/audit/verify
```
**Expected Response**:
```json
{
  "total_records_checked": 179,
  "tamper_detected": false,
  "head_digest": "8d9ce709b7115068de766e8f87878de9357de861616d204d3a359f71c8eb0a5f",
  "audit_status": "INTEGRITY_VERIFIED"
}
```

---

## 5. Kubernetes & Container Health Probes

NIRIKSHA exposes industry-standard health probes compliant with Kubernetes and AWS ECS specifications:

| Endpoint | HTTP Method | Probe Type | Description |
| :--- | :--- | :--- | :--- |
| `/health/live` | `GET` | **Liveness Probe** | Returns HTTP 200 `{ "status": "ALIVE" }` as long as the ASGI event loop is active. |
| `/health/ready` | `GET` | **Readiness Probe** | Executes active `SELECT 1` on PostgreSQL. Returns HTTP 200 if connected; returns HTTP 503 if database is unreachable. |
| `/health` | `GET` | **Diagnostic Probe** | Returns comprehensive system status including DB dialect, Neon resilience parameters, and file storage status. |

---

## 6. End-to-End Evaluation Verification

To execute the automated 16-step statutory evaluation scenario (proving statecharts, ML risk scoring, fast-forward clock, EVC CP-SAT solver, corrigendum compiler, and tamper detection):

```bash
python test_demo_flow.py
```
**Result**: 16/16 steps pass with 100% success.
