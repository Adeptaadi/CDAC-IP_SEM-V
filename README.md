# Project Sentinel — Autonomous Cyber Threat Hunting Platform

An Agentic AI-powered Security Operations Center (SOC) platform that continuously investigates security telemetry, correlates events, and generates explainable reports with human-in-the-loop validation.

---

## 🏗️ Quick Start with Docker

### Prerequisites
* Docker & Docker Compose installed.
* (Optional) Local [Ollama](https://ollama.com) running on the host machine (`ollama run qwen2.5:latest`) if using local LLM inference.

### 1. Initialize Environment
Copy the sample environment file:
```bash
cp .env.example .env
```

### 2. Build & Launch Containers
```bash
docker compose up --build -d
```

### 3. Verify Services
* **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
* **Backend API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **PostgreSQL Database:** `localhost:5432` (`sentinel_dev` / `sentinel_secure_pass`)
* **Redis Cache / Queue:** `localhost:6379`

---

## 📁 Repository Structure

```
├── .env.example             # Base environment configuration
├── docker-compose.yml       # Multi-container orchestration (DB, Cache, Backend, Frontend)
├── backend/                 # Python 3.12 FastAPI backend & Agent Runtime
│   ├── Dockerfile           # Backend container definition with live-reload
│   ├── requirements.txt     # Python dependencies (FastAPI, SQLAlchemy, LangGraph, etc.)
│   └── app/
│       ├── main.py          # FastAPI application entrypoint
│       ├── config.py        # Typed settings & confidence weights
│       ├── database.py      # SQLAlchemy session manager
│       ├── models/          # Relational ORM models (PostgreSQL DDL matching IS §2)
│       ├── schemas/         # Pydantic schemas (WorkerTask, WorkerResult, Finding)
│       ├── planner/         # Orchestrator (Log-odds ConfidenceEngine, Worker Selection)
│       ├── workers/         # Specialized Worker implementations
│       └── api/             # REST & WebSocket API routers
├── frontend/                # React 18 + Vite + TailwindCSS dashboard
│   ├── Dockerfile           # Frontend container definition
│   ├── package.json         # Node dependencies
│   └── src/
│       ├── App.tsx          # SOC Dashboard UI & Planner tester
│       └── main.tsx         # React entrypoint
├── datasets/                # Sample telemetry event streams (Sysmon, Windows Event Logs)
└── docs/                    # Architectural Specifications (PRD, SDD, AAD, AIDD, TDD, IS)
```

---

## 🧠 Core Architecture Highlights

1. **Logit-Space Confidence Engine (`backend/app/planner/confidence.py`):** Bounded update mechanism applying deltas in log-odds space using 6 weighted factors (Detection, Evidence, Correlation, Knowledge, Agreement, Historical).
2. **Dynamic Worker Selection (`backend/app/planner/selection.py`):** Scores worker candidates dynamically based on the current state gap (triaging untriaged events, graph sparseness, hypothesis strength).
3. **Pydantic Contracts (`backend/app/schemas/contracts.py`):** Type-safe contracts for all Worker inputs and outputs (`WorkerTask`, `Finding`, `WorkerResult`).

---

## 🛠️ Development Guidelines
* **Code Style:** PEP8 for Python, ESLint/Prettier for TypeScript.
* **Database Migrations:** Use Alembic when modifying models in `backend/app/models/`.
* **State Immutability:** Workers return `WorkerResult` deltas; only the central Planner mutates the investigation state.
