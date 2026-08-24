# LedgerPilot

> AI-powered payment reconciliation and financial operations controller.

## Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Frontend  | React 18 + TypeScript + Tailwind 3  |
| Backend   | Python 3.12 + FastAPI               |
| Database  | PostgreSQL 16                       |
| Charts    | Recharts                            |
| Container | Docker + Docker Compose             |

---

## Quick Start (Local Development)

### Prerequisites
- Node.js 20+
- Python 3.12+
- PostgreSQL 16 running locally (or use Docker)

### 1. Database
```bash
# Using Docker (recommended)
docker run -d \
  --name ledgerpilot_postgres \
  -e POSTGRES_USER=ledger \
  -e POSTGRES_PASSWORD=ledger \
  -e POSTGRES_DB=ledgerpilot \
  -p 5432:5432 \
  postgres:16-alpine
```

### 2. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
API docs available at: http://localhost:8000/api/docs  
Health check: http://localhost:8000/api/health

### 3. Frontend
```bash
cd frontend
npm install      # already done if you followed setup
npm run dev
```
App available at: http://localhost:5173

---

## Project Structure

```
RazorPay Project/
├── frontend/                    # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── api/client.ts        # Axios instance
│   │   ├── components/layout/   # Sidebar, Topbar, MainLayout
│   │   ├── hooks/useTheme.ts    # Dark/light mode hook
│   │   ├── pages/               # 7 route pages
│   │   ├── types/index.ts       # Shared TypeScript types
│   │   └── lib/utils.ts         # Utility helpers
│   ├── tailwind.config.ts       # Custom navy/charcoal palette
│   └── vite.config.ts           # Vite + proxy config
│
├── backend/                     # Python FastAPI
│   ├── main.py                  # App entry point
│   ├── app/
│   │   ├── api/health.py        # GET /api/health
│   │   ├── core/config.py       # Pydantic Settings
│   │   ├── db/database.py       # SQLAlchemy async engine
│   │   └── models/              # ORM models (Phase 2)
│   └── requirements.txt
│
├── docker-compose.yml           # Full stack orchestration
├── .env.example                 # Environment template
└── README.md
```

---

## API Endpoints (Phase 1)

| Method | Path          | Description            |
|--------|---------------|------------------------|
| GET    | /             | API welcome + links    |
| GET    | /api/health   | Health + DB status     |
| GET    | /api/docs     | Swagger UI             |
| GET    | /api/redoc    | ReDoc documentation    |

---

## Running with Docker (future)

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend:  http://localhost:8000
- Database: localhost:5432
