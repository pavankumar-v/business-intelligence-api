## Business Intelligence Backend

This is the backend for the business intelligence application.

## TechStack

- FastAPI (ASGI server)
- PostgreSQL (Database)
- Redis (Cache)
- RQ (Task Queue)
- RQ Monitor (Task Queue Monitor)

## Architecture
Tool: excalidraw
<img width="1222" height="632" alt="Screenshot 2025-12-02 at 10 40 38 PM" src="https://github.com/user-attachments/assets/81f74c65-2bd1-4005-a575-2ba76488b0bc" />

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

Flow:
Upload → Job Created → Queue Tasks → Worker Processes → DB Updated → WebSocket Notifies → Dashboard Refreshes

## Database Design

The database is implemented in PostgreSQL using SQLAlchemy models in `app/db/models`.

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
   │    (DailyMetric)     │   │ (DailyCompanyMetric)      │   │  (DailyModelMetric)       │
   ├───────────────────────┤   ├───────────────────────────┤   ├───────────────────────────┤
   │ date, region (PK)     │   │ date, company_name (PK)   │   │ date, region, model (PK)  │
   │ KPIs (avg_spend, ...)│   │ total_cost, conv_count    │   │ total_cost, conv_count    │
   └───────────────────────┘   └───────────────────────────┘   └───────────────────────────┘

```

High level:
- **users** and **transactions** capture raw usage.
- **jobs** represent CSV ingestion/processing runs.
- Daily aggregate tables power the dashboard KPIs.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app/main.py
```

## API

```bash
http://localhost:8000/docs
```
