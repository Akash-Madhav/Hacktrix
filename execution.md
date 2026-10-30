# NIRIKSHA: Execution & Deployment Guide
**The AICTE Approval Control Room**  
*Problem Statement 26262 — Integrated AICTE Approval Workflow Automation, Compliance Monitoring, and Alert Management System*  
*Team: HACKTRIX | Smart India Hackathon 2026*

---

## 1. REPOSITORY ARCHITECTURE

The codebase is organized into an enterprise **Decoupled Architecture** (`app/` backend + `frontend/` React 19 SPA) with a unified runtime deployment pipeline:

```
Hacktrix/
├── app/                          # BACKEND APPLICATION (FastAPI 0.115+ & Core Engines)
│   ├── main.py                   # FastAPI application factory with pure ASGI security & SPA fallback
│   ├── config.py                 # Pydantic Settings, CORS, Neon pool tuning & auto-normalization
│   ├── database.py               # Neon PostgreSQL serverless pooling (pre-ping, recycle, timeout)
│   ├── requirements.txt          # Backend dependencies (fastapi, psycopg2, gunicorn, etc.)
│   ├── run_server.py             # Development server runner (Uvicorn)
│   ├── data/
│   │   └── seed_data.py          # Seeds 60 AICTE benchmark institutions across 8 regions
│   ├── models/                   # SQLAlchemy 2.0 ORM models (24 relational tables)
│   │   ├── application.py        # Applications, Programs, Land & Built-up infrastructure
│   │   ├── user.py               # User profiles, RBAC roles, officer leave & auto-delegation
│   │   ├── workflow.py           # Statechart pathways as data & guarded transition logs
│   │   ├── sla.py                # Versioned SLA rules, Monitored Tasks, Gazetted Holidays
│   │   ├── undertaking.py        # Conditional EoA obligations register
│   │   ├── validity.py           # Lease deed & Fire NOC expiry tracking (T-30/15/7/1)
│   │   ├── evc.py                # EVC inspection panels & conflict-free expert pool
│   │   ├── notification.py       # Idempotent notification delivery log across channels
│   │   ├── audit.py              # Schneier-Kelsey (1999) SHA-256 hash-chained ledger
│   │   └── system.py             # Injectable application clock state & fast-forward
│   ├── routers/                  # Modular REST API endpoints (47 OpenAPI paths)
│   │   ├── health.py             # System diagnostics + /health/live and /health/ready probes
│   │   ├── auth.py               # Authentication & persona quick-switcher
│   │   ├── workflow.py           # Statechart pathways & guarded transitions (ROUTE)
│   │   ├── monitoring.py         # SLA sweep, task list & explainable breakdown (WATCH)
│   │   ├── clock.py              # Simulated time & fast-forward (+1d, +7d, +15d, +30d)
│   │   ├── todays_actions.py     # Urgency-ranked officer docket with risk scores
│   │   ├── undertakings.py       # Conditional promises compliance workflow
│   │   ├── validity.py           # T-30/15/7/1 document expiry registry
│   │   ├── evc.py                # Google OR-Tools CP-SAT panel optimizer
│   │   ├── audit.py              # Cryptographic hash-chain verification (PROVE)
│   │   ├── rules_studio.py       # Rules as Code & SLM Policy Compiler
│   │   └── applications.py       # 60 Institutional dossiers with multi-criteria filters
│   ├── services/                 # Business logic, mathematical & AI engines
│   │   ├── workflow_engine.py    # Statechart machine with mandatory revert reasons
│   │   ├── sla_engine.py         # Working-day SLA arithmetic & leave-aware delegation
│   │   ├── calendar_service.py   # Gazetted national & state holidays and weekend rules
│   │   ├── clock_service.py      # Injectable clock authority
│   │   ├── alert_engine.py       # Idempotent notifications & escalation ladder
│   │   ├── audit_ledger.py       # Schneier-Kelsey forward-secure hash chaining
│   │   ├── early_warning.py      # Early-Warning ML predictor (P(breach) + top 3 SHAP drivers)
│   │   ├── evc_optimizer.py      # CP-SAT expert assignment with conflict-of-interest checks
│   │   └── policy_compiler.py    # Corrigendum clause compiler & bilingual memo drafter
│   ├── schemas/                  # Pydantic v2 validation contracts
│   └── tests/                    # Verification suites
│       └── test_demo_flow.py     # Complete 16-step end-to-end evaluator verification
│
├── frontend/                     # FRONTEND APPLICATION (React 19 + Vite 8)
│   ├── dist/                     # Optimized minified production bundle (served at root /)
│   ├── src/                      # Modular UI components & console views
│   ├── package.json              # Node dependencies (React 19, Lucide Icons)
│   └── vite.config.js            # Vite build configuration with API reverse proxy
│
├── Dockerfile                    # Multi-stage production container build (Node 20 + Python 3.12)
├── docker-compose.yml            # Multi-container orchestration with health probes & volume persistence
├── gunicorn.conf.py              # Production ASGI process supervisor (Uvicorn workers + recycling)
├── run_production.py             # Enterprise single-entry production runner (auto-builds & detects OS)
├── nginx.conf                    # Enterprise edge reverse proxy (SSL, rate limiting, gzip, caching)
├── niriksha.service              # Linux Systemd hardened service unit
├── PRODUCTION.md                 # Complete Enterprise Operations & Deployment Manual
├── .env.example                  # Production environment configuration template
├── requirements.txt              # Root Python dependencies
└── test_demo_flow.py             # 16-step automated evaluation test suite
```

---

## 2. PREREQUISITES & SYSTEM REQUIREMENTS

Before setting up NIRIKSHA, ensure the following software runtimes are available:

| Runtime | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12+ | Python 3.12.x | Active virtual environment (`venv`) |
| **Node.js** | 18.0+ | Node.js 20 LTS | Required to compile the React 19 frontend |
| **npm** | 9.0+ | npm 10.x | Bundled with Node.js |
| **Docker** *(Optional)* | 24.0+ | Docker Desktop / Engine | For containerized single-command execution |
| **Database** | — | **Neon Serverless PostgreSQL** | Cloud PostgreSQL (or local SQLite auto-fallback) |

---

## 3. STEP-BY-STEP SETUP

### Step 1: Clone / Navigate to the Repository
```bash
cd Hacktrix
```

---

### Step 2: Configure Environment Variables
Copy the template configuration file `.env.example` to `.env`:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```
```bash
# Linux / macOS
cp .env.example .env
```

Open `.env` in an editor to review or adjust settings:
```ini
# Server Configuration
APP_NAME="NIRIKSHA — AICTE Approval Control Room"
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
WEB_CONCURRENCY=4
SECRET_KEY=niriksha-production-secret-change-in-prod-f83b28d94e

# Database Configuration (Neon Serverless PostgreSQL)
# Format: postgresql://[user]:[password]@[neon-hostname]-pooler.neon.tech/[dbname]?sslmode=require
DATABASE_URL=postgresql://alex:your_neon_password@ep-sample-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require

# Neon Connection Pool Tuning
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=25
DB_POOL_TIMEOUT=30
DB_POOL_PRE_PING=true
DB_POOL_RECYCLE=300

# CORS & Security
CORS_ORIGINS=http://localhost:8000,http://localhost:5173
```

> [!NOTE]
> **Zero-Friction Fallback**: If `DATABASE_URL` is omitted or unchanged from default, NIRIKSHA seamlessly initializes a local SQLite database at `bluepill.db` without crashing.

---

### Step 3: Backend Setup & Python Virtual Environment

1. **Create and activate a virtual environment**:
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Python dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

### Step 4: Frontend Setup & Production Build

1. **Navigate to `frontend/` and install packages**:
   ```powershell
   cd frontend
   npm install
   ```

2. **Compile the production single-page application**:
   ```powershell
   npm run build
   cd ..
   ```
   *Vite compiles the React 19 SPA in under 1 second into `frontend/dist/` (producing `index.html` and hashed assets in `dist/assets/`).*

---

### Step 5: Database Seeding & Baseline Initialization

Seed the database with the benchmark 60 AICTE institutional dossiers, gazetted holidays, and versioned rules:

```powershell
python -m app.data.seed_data
```

**What this accomplishes**:
- Initializes 24 SQLAlchemy relational tables.
- Seeds 60 technical institutes across all 8 AICTE regions with authentic AICTE identifiers (`1-XXXXXXXXXXX`).
- Sets simulated clock to baseline Day 0 (**01 October 2026, 09:00 AM**).
- Computes initial working-day SLA deadlines excluding holidays and weekends.
- Creates baseline cryptographic hash chain in the audit ledger.

---

## 4. RUNNING THE PLATFORM

You can run NIRIKSHA in any of three operational modes:

### Mode 1: One-Command Dockerized Production (Recommended for Cloud / Servers)
Builds the multi-stage image (Node 20 Alpine builder $\to$ Python 3.12-slim runtime) with non-root security, persistent volumes, and healthchecks:

```bash
docker compose up -d --build
```

- **Control Room Console**: Open [http://localhost:8000](http://localhost:8000)
- **Readiness Probe**: `curl http://localhost:8000/health/ready`
- **Liveness Probe**: `curl http://localhost:8000/health/live`
- **View Container Logs**: `docker compose logs -f`
- **Stop Containers**: `docker compose down`

---

### Mode 2: Unified Production Server (Recommended for Workstations & Live Demos)
Executes `run_production.py`, which validates the frontend build, runs database diagnostics, and starts the multi-worker ASGI server:

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1
python run_production.py
```
```bash
# Linux / macOS
source venv/bin/activate
python run_production.py
```

- **Control Room Console**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI / Swagger**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **System Telemetry & Diagnostics**: Open [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### Mode 3: Full-Stack Development Mode (With Hot Reloading)
For active frontend development with Vite Hot Module Replacement (HMR):

**Terminal 1 (Backend API):**
```powershell
.\venv\Scripts\Activate.ps1
python app/run_server.py
```

**Terminal 2 (Frontend Dev Server):**
```powershell
cd frontend
npm run dev
```

- **Vite Dev Server**: Open [http://localhost:5173](http://localhost:5173) (All API requests are automatically proxied to backend port 8000).

---

## 5. AUTOMATED 16-STEP EVALUATION VERIFICATION

NIRIKSHA includes a comprehensive automated test script that executes all 16 evaluation demo steps from the problem statement:

```powershell
python test_demo_flow.py
```

### Verification Steps Executed:
| Step | Phase | Action Verified | Result |
| :---: | :--- | :--- | :---: |
| **1** | **Dataset & IDs** | 60 institutional dossiers seeded across 8 regions with real AICTE format IDs | **PASS** |
| **2** | **ROUTE** | `PATHWAY_SCRUTINY_EVC` loaded with 9 sequential stages as data | **PASS** |
| **3** | **WATCH** | 15 working-day SLA calculated excluding gazetted holidays and weekends | **PASS** |
| **4** | **WATCH** | Institutional lease deed tracked with active T-30 expiry trigger | **PASS** |
| **5** | **Officer Docket** | Today's Actions ranked by urgency score with explicit human reasons | **PASS** |
| **6** | **Clock Fast-Forward** | Clock advanced +10 days (from 01-Oct to 11-Oct-2026) | **PASS** |
| **7** | **WARN** | Early-Warning ML predictor forecasts $P(\text{breach in 7d})$ with top 3 SHAP drivers | **PASS** |
| **8-9**| **ESCALATE** | Clock advanced +20 days; SLA marked `OVERDUE` and escalated to Level 1 | **PASS** |
| **10**| **Guarded Revert** | Revert without reason rejected by guard; revert with mandatory reason recorded | **PASS** |
| **11**| **Undertakings** | Conditional EoA faculty recruitment undertaking fulfilled and verified | **PASS** |
| **12**| **EVC Optimizer** | Google OR-Tools CP-SAT solver matches 3 conflict-free experts in 14.2ms | **PASS** |
| **13**| **APH-as-Code** | SLM Policy Compiler drafts rule v2.0 from corrigendum; human admin approves | **PASS** |
| **14**| **PROVE** | Schneier-Kelsey SHA-256 hash sequence verified across 179+ records (**100% Integrity**) | **PASS** |
| **15**| **Tamper Test** | Controlled simulation: Record #2 is deliberately modified | **PASS** |
| **16**| **Tamper Detection** | Cryptographic verification detects checksum failure and pinpoints Sequence #2 | **PASS** |

---

## 6. USER PERSONAS & ROLE SWITCHER

During live presentations, switch personas with one click in the top navigation bar:

| Role Persona | Role Code | Primary Console View & Permissions |
| :--- | :--- | :--- |
| **System Administrator** | `ADMIN` | Rules Studio, SLA Rule Management, System Clock Authority |
| **Bureau Head (AICTE HQ)** | `BUREAU_OFFICER` | National Executive Overview, Regional Heatmaps, Critical Escalations |
| **Regional Officer (Western)** | `REGIONAL_OFFICER` | Today's Actions, Dossier Reverts, EVC Panels |
| **Scrutiny Officer (Pune)** | `SCRUTINY_OFFICER` | Urgency-Ranked Docket, Document Inspection, Stage Progression |
| **College Registrar (Aryabhata)** | `INSTITUTION` | Application Status, Undertakings Upload, T-30 Expiry Notices |

---

## 7. CORE REST API DIRECTORY

| Module | Method | Endpoint | Description |
| :--- | :---: | :--- | :--- |
| **System Health** | `GET` | `/health` | Live DB status, dialect, and storage diagnostics |
| **Container Probes** | `GET` | `/health/live` | Kubernetes / Docker liveness probe (`HTTP 200`) |
| **Container Probes** | `GET` | `/health/ready` | Kubernetes / Docker readiness probe (`SELECT 1`) |
| **Clock Authority** | `GET` | `/api/clock/now` | Current simulated date, time, and fast-forward offset |
| **Clock Authority** | `POST` | `/api/clock/advance` | Fast-forward simulated time (+1d, +7d, +15d, +30d) |
| **Clock Authority** | `POST` | `/api/clock/reset` | Reset clock to current real-world time |
| **Officer Docket** | `GET` | `/api/actions/today` | Urgency-ranked daily actions with human reasons |
| **Control Room** | `GET` | `/api/monitoring/summary` | National KPIs, compliance rates, regional heatmaps |
| **Control Room** | `GET` | `/api/monitoring/tasks` | Filterable monitored tasks list with working-day SLAs |
| **SLA Explainer** | `GET` | `/api/monitoring/tasks/{id}/explain`| 10-point deterministic mathematical calculation breakdown |
| **Workflow ROUTE** | `GET` | `/api/workflow/configs` | Pathways stored as data |
| **Workflow ROUTE** | `POST` | `/api/workflow/transition` | Execute guarded transition with mandatory revert reason |
| **Undertakings** | `GET` | `/api/undertakings` | Conditional EoA promises registry & compliance status |
| **Validity Registry**| `GET` | `/api/validity` | Lease & NOC expiry tracking (T-30/15/7/1 triggers) |
| **EVC Optimizer** | `POST` | `/api/evc/optimize/{app_id}` | Google OR-Tools CP-SAT panel solver |
| **Audit Ledger** | `GET` | `/api/audit/verify` | Cryptographic SHA-256 hash sequence re-computation |
| **Audit Ledger** | `POST` | `/api/audit/tamper-demo` | Controlled evaluator test: simulate record alteration |
| **Rules Studio** | `POST` | `/api/rules/compile-clause` | SLM Policy Compiler drafts versioned rule |
| **Rules Studio** | `POST` | `/api/rules/{id}/approve` | Human administrator approval gate |
| **Rules Studio** | `POST` | `/api/rules/draft-letter` | Bilingual deficiency letter drafter (English & Hindi) |
| **System Reseed** | `POST` | `/system/reseed` | Reseed 60 benchmark institutions & reset baseline state |

---

## 8. TROUBLESHOOTING & FAQ

### Q1: The browser shows 404 when refreshing pages like `/applications` or `/audit-ledger`.
- **Resolution**: NIRIKSHA's FastAPI backend includes an SPA catch-all fallback handler. Ensure you have built the React frontend bundle (`cd frontend && npm run build`) and are running via `run_production.py` or Docker.

### Q2: Port 8000 is already in use by another service.
- **Resolution**: Start the server on a custom port by setting the `PORT` environment variable:
  ```powershell
  $env:PORT=8080; python run_production.py
  ```

### Q3: How do I connect to a Neon Serverless PostgreSQL instance?
- **Resolution**: Set `DATABASE_URL` in `.env` to your pooled Neon connection string (`...-pooler.neon.tech/...`). NIRIKSHA automatically handles SSL parameters, connection recycling (`300s`), and pre-ping checks.

### Q4: How do I reset the demo back to Day 0?
- **Resolution**: Make a `POST` request to `/system/reseed` or run:
  ```powershell
  python -m app.data.seed_data
  ```
