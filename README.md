## Business Intelligence Backend

This is the backend for the business intelligence application.

## TechStack

- FastAPI (ASGI server)
- PostgreSQL (Database)
- Redis (Cache)
- RQ (Task Queue)
- RQ Monitor (Task Queue Monitor)

## Architecture

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
