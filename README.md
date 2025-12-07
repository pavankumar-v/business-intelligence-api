# Business Intelligence Backend

FastAPI-based backend for processing and analyzing business intelligence data from CSV uploads.

## Tech Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Database
- **Redis** - Cache & job queue
- **RQ** - Background task processing
- **Alembic** - Database migrations

## Quick Start with Docker

### 1. Start services

```bash
docker compose up --build
```

Visit to verify it's running
http://localhost:8000/docs

### 2. Run migrations

```bash
docker compose exec app alembic upgrade head
```

### 3. Access the API

- API Docs: http://localhost:8000/docs
- RQ Dashboard: http://localhost:8000/rq

## Architecture

<img width="1222" height="632" alt="Screenshot 2025-12-02 at 10 40 38 PM" src="https://github.com/user-attachments/assets/81f74c65-2bd1-4005-a575-2ba76488b0bc" />

```
┌─────────────┐
│   FRONTEND  │
│             │
│  [Upload]   │
│  [Progress] │───WebSocket───┐
│  [Dashboard]│               │
└──────┬──────┘               │
       │                      │
       │ POST /upload         │
       │ GET /dashboard       │
       ▼                      ▼
┌─────────────────────────────────┐
│      FASTAPI BACKEND            │
│                                 │
│  • Creates Job Record           │
│  • Saves CSV to disk            │
│  • Enqueues tasks               │
│  • Serves Dashboard API         │
└────┬────────────────────┬──────┘
     │                    │
     │ Enqueue            │ Read
     ▼                    ▼
┌─────────────┐    ┌──────────────┐
│ REDIS/RQ    │    │  POSTGRESQL  │
│             │    │              │
│ Job Queue   │    │ • jobs       │
└──────┬──────┘    │ • users      │
       │           │ • transactions│
       │           │ • daily_metrics│
       ▼           └───▲──────────┘
┌─────────────┐       │
│  RQ WORKER  │       │
│             │       │
│ 1. Dump     │───────┤ Write
│    Users    │       │
│ 2. Process  │───────┤ Write + Update
│    Chunks   │       │ (500 rows)
│ 3. Aggregate│───────┘ Upsert
│    Metrics  │
└─────────────┘
```

**Flow:**
Upload → Job Created → Queue Tasks → Worker Processes → DB Updated → WebSocket Notifies → Dashboard Refreshes

## Database Design

The database is implemented in PostgreSQL using SQLAlchemy models in `app/models`.

```
             ┌───────────────┐            1        *
             │    users      │────────────┬────────────┐
             │   (User)      │            │            │
             ├───────────────┤            │            │
             │ id (PK, UUID) │            │            │
             │ username      │            │            │
             │ region        │            │            │
             │ ...           │            │            │
             └───────────────┘            │            │
                                          │            │
                                          ▼            │
                                   ┌───────────────┐   │
                                   │ transactions  │   │
                                   │ (Transaction) │   │
                                   ├───────────────┤   │
                                   │ id (PK)       │   │
                                   │ user_id (FK)  │◀──┘
                                   │ model_name    │
                                   │ token_count   │
                                   │ cost fields   │
                                   │ timestamp     │
                                   └───────────────┘


    ┌───────────────┐          Aggregates from `transactions` (per job run)
    │     jobs      │
    │    (Job)      │
    ├───────────────┤
    │ id (PK)       │
    │ filename      │
    │ total_rows    │
    │ processed_*   │
    │ job_metadata  │
    └───────────────┘


   Per-day aggregates (dashboard KPIs)

   ┌───────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
   │   daily_metrics       │   │   daily_company_metrics   │   │   daily_model_metrics     │
   │    (DailyMetric)      │   │ (DailyCompanyMetric)      │   │  (DailyModelMetric)       │
   ├───────────────────────┤   ├───────────────────────────┤   ├───────────────────────────┤
   │ date, region (PK)     │   │ date, company_name (PK)   │   │ date, region, model (PK)  │
   │ KPIs (avg_spend, ...) │   │ total_cost, conv_count    │   │ total_cost, conv_count    │
   └───────────────────────┘   └───────────────────────────┘   └───────────────────────────┘

```

**High level:**

- **users** and **transactions** capture raw usage
- **jobs** represent CSV ingestion/processing runs
- Daily aggregate tables power the dashboard KPIs

## Local Development Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run migrations

```bash
alembic upgrade head
```

### 3. Start the server

```bash
uvicorn app.main:app --reload
```

## Common Docker Commands

```bash
# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Reset database (removes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec app alembic upgrade head

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d business_intelligence

# Access Redis CLI
docker-compose exec redis redis-cli
```

## Project Structure

```
app/
├── models/          # SQLAlchemy models
├── service/         # Business logic
├── etl/            # Data processing pipelines
├── db/             # Database configuration
├── rq/             # Job queue setup
└── main.py         # FastAPI application

alembic/            # Database migrations
```

## API Endpoints

- `POST /upload-csv` - Upload CSV files for processing
- `GET /metrics/kpis` - Get dashboard metrics
- `WS /jobs/{job_id}` - WebSocket for job progress
- `GET /rq` - RQ Dashboard

## Environment Variables

### `.env.local` (Local Development)

```env
PG_HOST=localhost
PG_USER=postgres
PG_PASSWORD=root
PG_DB=business_intelligence
PG_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
```

### `.env.docker` (Docker Containers)

```env
PG_HOST=postgres
PG_USER=postgres
PG_PASSWORD=root
PG_DB=business_intelligence

REDIS_HOST=redis
REDIS_PORT=6379
```
