# Climate & Water Risk Intelligence Platform

A production-ready platform that ingests environmental sensor data (rainfall, water level, temperature), calculates regional flood/drought risk, sends real-time alerts, and exposes a full React dashboard — designed for NGOs, churches, and local governments.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Local Development Setup](#local-development-setup)
   - [Backend](#backend-local)
   - [Frontend](#frontend-local)
5. [Production Deployment (Docker Compose)](#production-deployment)
6. [Environment Variables](#environment-variables)
7. [Database Migrations](#database-migrations)
8. [API Reference](#api-reference)
9. [WebSocket Protocol](#websocket-protocol)
10. [Running Tests](#running-tests)
11. [Production Hardening Checklist](#production-hardening-checklist)

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                       Browser / Client                     │
│           React 18 + Vite (port 3000 / 5173)              │
│   Dashboard · Regions · Alerts · Readings · Live Feed      │
└─────────────────────────┬──────────────────────────────────┘
                          │ HTTP  /api/v1/*
                          │ WS    /ws/{org_id}?token=…
┌─────────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend (port 8000)               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Auth /   │  │  Risk Engine │  │   Forecast Engine    │  │
│  │ JWT RBAC │  │  (scoring)   │  │ (linear regression)  │  │
│  └──────────┘  └──────┬───────┘  └──────────────────────┘  │
│  ┌──────────┐         │          ┌──────────────────────┐  │
│  │ Alert    │         │          │  WebSocket Manager   │  │
│  │ Engine   │         │          │  (per-org broadcast) │  │
│  └──────────┘         │          └──────────────────────┘  │
└──────────────┬─────────┴──────────────────────┬────────────┘
               │ SQLAlchemy async                │ redis.asyncio
┌──────────────▼──────────────┐  ┌──────────────▼─────────┐
│  MySQL 8  (port 3306)       │  │  Redis 7  (port 6379)  │
│  Organizations · Users      │  │  Risk cache · Throttle │
│  Regions · Readings         │  │  WS pub/sub            │
│  RiskAssessments · Alerts   │  └────────────────────────┘
└─────────────────────────────┘
```

Multi-tenant: every database query is scoped to `organization_id` extracted from the JWT. Users cannot access data outside their own organisation.

---

## Tech Stack

| Layer      | Technology                                          |
|------------|-----------------------------------------------------|
| Frontend   | React 18, TypeScript, Vite 5, Tailwind CSS v3      |
| Data / UI  | TanStack Query v5, Recharts, Lucide React, Axios   |
| Backend    | Python 3.11, FastAPI, SQLAlchemy 2.x (async)       |
| Database   | MySQL 8.0, Alembic migrations                      |
| Cache/RT   | Redis 7, WebSockets                                |
| Auth       | JWT (HS256), bcrypt, role-based access control     |
| Container  | Docker, Docker Compose                             |

---

## Prerequisites

**Local development:**

| Tool            | Minimum version |
|-----------------|-----------------|
| Python          | 3.11            |
| Node.js         | 20 LTS          |
| npm             | 10              |
| MySQL           | 8.0             |
| Redis           | 7               |

**Docker (production):**

| Tool            | Minimum version |
|-----------------|-----------------|
| Docker          | 24              |
| Docker Compose  | v2 (plugin)     |

---

## Local Development Setup

### Clone and configure

```bash
git clone https://github.com/IsaacJM03/Climate-Water-Risk-Intelligence-Platform.git
cd Climate-Water-Risk-Intelligence-Platform
cp .env.example .env          # edit values before use
cp frontend/.env.example frontend/.env
```

---

### Backend (local) <a name="backend-local"></a>

**1. Create and activate a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Start MySQL and Redis locally**

If you have Docker available, the quickest way:

```bash
docker run -d --name climate_mysql \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=climate_db \
  -e MYSQL_USER=climate_user \
  -e MYSQL_PASSWORD=climate_pass \
  -p 3306:3306 mysql:8.0

docker run -d --name climate_redis -p 6379:6379 redis:7-alpine
```

Or install and start them natively via your OS package manager.

**4. Set environment variables**

Edit `.env` (copy from `.env.example`) and set `DATABASE_URL` to point to your local MySQL:

```
DATABASE_URL=mysql+aiomysql://climate_user:climate_pass@localhost:3306/climate_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
APP_ENV=development
```

**5. Run database migrations**

```bash
alembic upgrade head
```

**6. Start the backend**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend is live at **http://localhost:8000**

- Interactive API docs: http://localhost:8000/api/docs
- Health check: http://localhost:8000/health

**Bootstrap your first organisation and user via Swagger:**

1. Open http://localhost:8000/api/docs
2. `POST /api/v1/auth/register` → create an organisation, note the returned `id`
3. You need an admin user. Since `/auth/register-user` requires a JWT, the bootstrap path is:
   - Temporarily call `POST /api/v1/auth/register-user` directly with a tool like cURL after creating a test token, **or**
   - Use the Alembic seed approach: insert a user row directly (hashed password via `passlib`).

Quick Python seed script:

```python
# seed.py  (run once, then delete)
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password

async def main():
    async with AsyncSessionLocal() as db:
        user = User(
            email="admin@example.com",
            hashed_password=hash_password("changeme"),
            role="admin",
            organization_id=1,   # ID returned from POST /auth/register
        )
        db.add(user)
        await db.commit()

asyncio.run(main())
```

```bash
python seed.py
```

---

### Frontend (local) <a name="frontend-local"></a>

**1. Install dependencies**

```bash
cd frontend
npm install
```

**2. Configure environment**

```bash
cp .env.example .env
```

`frontend/.env`:

```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

The Vite dev server proxies `/api` and `/ws` to `localhost:8000` automatically, so you can also leave `VITE_API_URL` unset and use relative paths.

**3. Start the dev server**

```bash
npm run dev
```

Frontend is live at **http://localhost:5173**

---

## Production Deployment

Everything is containerised. A single command builds and starts MySQL, Redis, the FastAPI backend, and the Nginx-served React frontend.

**1. Configure environment**

```bash
cp .env.example .env
```

Minimum required changes in `.env`:

```
DATABASE_URL=mysql+aiomysql://climate_user:climate_pass@db:3306/climate_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
APP_ENV=production
```

**2. Build and start all services**

```bash
docker compose up -d --build
```

| Service  | URL                      |
|----------|--------------------------|
| Frontend | http://localhost:3000    |
| Backend  | http://localhost:8000    |
| API Docs | http://localhost:8000/api/docs |

**3. Run database migrations inside the container**

```bash
docker compose exec backend alembic upgrade head
```

**4. Check health**

```bash
curl http://localhost:8000/health
# {"status":"ok","env":"production"}

docker compose ps            # all services should be "healthy" or "running"
docker compose logs backend  # tail backend logs
```

**5. Stop all services**

```bash
docker compose down          # keeps volumes (data preserved)
docker compose down -v       # also deletes MySQL + Redis volumes
```

---

## Environment Variables

| Variable                  | Default                               | Description                                          |
|---------------------------|---------------------------------------|------------------------------------------------------|
| `DATABASE_URL`            | `mysql+aiomysql://…@localhost/…`     | Async MySQL connection string                        |
| `REDIS_URL`               | `redis://localhost:6379/0`           | Redis connection URL                                 |
| `SECRET_KEY`              | *(must change)*                       | JWT signing secret — use `secrets.token_hex(32)`     |
| `ALGORITHM`               | `HS256`                              | JWT algorithm                                        |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                            | JWT lifetime in minutes                              |
| `FLOOD_RISK_THRESHOLD`    | `70.0`                               | Risk score above which flood alert is triggered      |
| `DROUGHT_RISK_THRESHOLD`  | `65.0`                               | Risk score above which drought alert is triggered    |
| `ALERT_THROTTLE_MINUTES`  | `30`                                 | Minimum gap between duplicate CRITICAL alerts        |
| `RISK_CACHE_TTL`          | `300`                                | Redis TTL (seconds) for cached risk assessments      |
| `APP_ENV`                 | `production`                         | `production` or `development`                        |

Frontend build-time variables (in `frontend/.env`):

| Variable       | Default                    | Description                    |
|----------------|----------------------------|--------------------------------|
| `VITE_API_URL` | `http://localhost:8000`    | Backend base URL               |
| `VITE_WS_URL`  | `ws://localhost:8000`      | WebSocket base URL             |

---

## Database Migrations

This project uses **Alembic** for schema management. Never apply manual SQL.

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back one revision
alembic downgrade -1

# Autogenerate a new migration after editing SQLAlchemy models
alembic revision --autogenerate -m "add column xyz"

# View migration history
alembic history --verbose

# Check current revision
alembic current
```

Migrations live in `migrations/versions/`. The initial migration (`001_initial_schema.py`) creates all six tables with indexes and foreign keys.

---

## API Reference

All endpoints are under `/api/v1`. Interactive docs at `/api/docs`.

### Authentication

| Method | Path                    | Auth     | Description                              |
|--------|-------------------------|----------|------------------------------------------|
| POST   | `/auth/register`        | None     | Create a new organisation                |
| POST   | `/auth/login`           | None     | Login; returns JWT access token          |
| POST   | `/auth/register-user`   | admin    | Create a user within the current org     |

### Regions

| Method | Path                       | Auth              | Description                          |
|--------|----------------------------|-------------------|--------------------------------------|
| GET    | `/regions`                 | Any               | List all regions for current org     |
| POST   | `/regions`                 | admin / analyst   | Create a region                      |
| GET    | `/regions/{id}`            | Any               | Get a region                         |
| GET    | `/regions/{id}/risk`       | Any               | Latest risk assessment (cached)      |
| GET    | `/regions/{id}/forecast`   | Any               | Flood/drought probability forecast   |
| DELETE | `/regions/{id}`            | admin             | Delete a region                      |

### Readings

| Method | Path        | Auth   | Description                               |
|--------|-------------|--------|-------------------------------------------|
| POST   | `/readings` | Any    | Ingest a sensor reading; triggers bg task |
| GET    | `/readings` | Any    | List readings (filterable by region_id)   |

### Alerts

| Method | Path                       | Auth   | Description                    |
|--------|----------------------------|--------|--------------------------------|
| GET    | `/alerts`                  | Any    | List alerts (filterable)       |
| GET    | `/alerts/{id}`             | Any    | Get a single alert             |
| POST   | `/alerts/{id}/acknowledge` | Any    | Mark an alert as acknowledged  |

### Example: ingest a reading

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@example.com&password=changeme" | jq -r .access_token)

# 2. Post a reading for region 1
curl -s -X POST "http://localhost:8000/api/v1/readings?region_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"latitude":1.28,"longitude":36.82,"rainfall":85.5,"temperature":31.0,"water_level":2.3}'
```

---

## WebSocket Protocol

Connect to `/ws/{org_id}?token=<JWT>`.  
The token must belong to the organisation matching `org_id`, otherwise the connection is closed with code 4003.

**Server → Client events:**

```json
{ "type": "risk_update", "region_id": 5, "calculated_risk": 78.4,
  "flood_probability": 0.62, "drought_probability": 0.12 }

{ "type": "alert", "level": "high", "region_id": 5,
  "message": "High flood risk detected (78.4/100)" }
```

**Client → Server:**

```
ping   →   pong
```

---

## Running Tests

```bash
# From repo root, with virtualenv activated
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database. No MySQL or Redis instance required.

---

## Production Hardening Checklist

- [ ] **Rotate `SECRET_KEY`** — generate with `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] **Use strong DB password** — replace `climate_pass` with a generated secret
- [ ] **TLS/HTTPS** — terminate SSL at a reverse proxy (Nginx, Caddy, or cloud LB) in front of the services
- [ ] **Restrict CORS** — update `_ALLOWED_ORIGINS` in `app/main.py` to your real domain only
- [ ] **Rate limiting** — add an Nginx or API gateway rate limit on `/api/v1/readings`
- [ ] **DB backups** — configure automated MySQL dumps or snapshot the Docker volume
- [ ] **Log aggregation** — forward container stdout to a log service (Loki, CloudWatch, Datadog)
- [ ] **Health monitoring** — hook `/health` into your uptime monitor
- [ ] **Secret management** — inject secrets via vault or cloud secret manager; never commit `.env`
- [ ] **Non-root container user** — add `USER nobody` to the backend Dockerfile for production images
- [ ] **Resource limits** — set `mem_limit` and `cpus` in `docker-compose.yml` for production
- [ ] **Alembic run at startup** — add `alembic upgrade head &&` before `uvicorn` in the CMD or entrypoint script
