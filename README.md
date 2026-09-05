# RevTrace — AI Revenue Recovery Engine

> **Detect. Diagnose. Recover.**
>
> RevTrace is a fintech operations platform that detects revenue leakage from failed payment events, scores recovery opportunities, and orchestrates controlled recovery workflows with full audit trails.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + TypeScript + Tailwind CSS + Recharts |
| Backend | Python 3.11+ + FastAPI + Pydantic v2 |
| Database | PostgreSQL 16 (Docker) / SQLite (local dev fallback) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Infrastructure | Docker + Docker Compose |

---

## Quick Start

### Option A — Docker (Recommended)

Requires Docker Desktop.

```bash
# 1. Clone the repo
git clone <repo-url>
cd revtrace

# 2. Copy environment template
cp .env.example backend/.env
# Edit backend/.env if needed (defaults work for Docker)

# 3. Start all services
docker compose up --build

# 4. Open the app
# Frontend:  http://localhost:5173
# API docs:  http://localhost:8000/api/docs
# Health:    http://localhost:8000/api/health
```

### Option B — Local Development (SQLite fallback)

```bash
# ── Backend ──────────────────────────────────────────────────────────────────
cd backend

# Create virtualenv
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start API (SQLite auto-created as revtrace.db)
uvicorn main:app --reload --port 8000

# ── Frontend (new terminal) ───────────────────────────────────────────────────
cd frontend
npm install
npm run dev
```

---

## Environment Variables

Copy `.env.example` to `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `RevTrace` | Application display name |
| `VERSION` | `1.0.0` | API version |
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `DEBUG` | `true` | SQLAlchemy echo mode |
| `SECRET_KEY` | *(set this)* | JWT / session signing key |
| `DATABASE_URL` | SQLite fallback | PostgreSQL asyncpg or SQLite aiosqlite URL |
| `ALLOWED_ORIGINS_STR` | `localhost:5173,3000` | CORS allowed origins (comma-separated) |

---

## API Endpoints (Phase 1)

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Welcome message + links |
| `GET` | `/api/health` | System health (API + DB status) |
| `GET` | `/api/docs` | Swagger UI |
| `GET` | `/api/redoc` | ReDoc |

---

## Frontend Routes (Phase 1)

| Route | Page | Status |
|---|---|---|
| `/overview` | System Overview | ✅ Phase 1 |
| `/recovery` | Recovery Workflow | 🔜 Phase 5 |
| `/opportunities` | Recovery Opportunities | 🔜 Phase 4 |
| `/transactions` | Transaction Log | 🔜 Phase 2 |
| `/analytics` | Analytics Dashboard | 🔜 Phase 6 |
| `/assistant` | AI Assistant | 🔜 Phase 4 |
| `/simulator` | Recovery Simulator | 🔜 Phase 5 |
| `/audit` | Audit Log | 🔜 Phase 5 |
| `/evaluation` | Model Evaluation | 🔜 Phase 6 |

---

## Build Roadmap

| Phase | Description |
|---|---|
| **Phase 1** ✅ | Foundation + Fintech UI |
| **Phase 2** | Financial Event Ingestion + PostgreSQL Schema |
| **Phase 3** | Revenue Leakage Detection Engine |
| **Phase 4** | Recovery Scoring + AI Investigation |
| **Phase 5** | Recovery Workflow + Audit + Outcome Tracking |
| **Phase 6** | Analytics Dashboard + Model Evaluation |

---

## Financial Safety Principles

- Source transaction records are **immutable** after ingestion
- AI cannot directly modify financial records or balances
- Sensitive recovery actions require **explicit human approval**
- Every state-changing action is **audited**
- All UI values clearly distinguish: **Actual** | **Expected** | **Forecast** | **Simulated**
- No fabricated financial metrics are displayed in any phase
