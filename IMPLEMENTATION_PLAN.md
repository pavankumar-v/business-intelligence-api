# Implementation Plan

## APIs

### Upload

```bash
POST /upload
```

Response 200
```
{
    "data": {
        "job_id": "ej3423-f342-f342f-2234",
        "status": "pending",
        "total_rows": 2000,
        "progress": 0
    }
}
```

### websocket

```bash
ws://localhost:8000/ws
```

Events
```bash
{
    "data": {
        "job_id": "ej3423-f342-f342f-2234",
        "status": "pending",
        "rows_processed": 500
    }
}
```

### Dashboard

```bash
GET /kpis
```

Response 200
```
{
    "data": {
        "highest_model_user": 'claude-3.5-sonnet',
        "avg_spending_per_day": 200,
        "total_daily_metrics": 300,
        "avg_token_consumption": 200,
        "total_conversations": 200,
        "total_users": 200,
        "costliest_model": 'claude-3.5-sonnet',
        "total_cost": 200,
        "model_efficiency": 200,
        "total_users": 200,
        "active_user_comsumption_rate": "71",
        "regions": ['EU', 'US'],
        "region_wise_consumptions": [
            {
                "region": "EU",
                "consumption": 200
            },
            {
                "region": "US",
                "consumption": 200
            }
        ]
    }
}
```