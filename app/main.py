from anyio._core._eventloop import sleep
from starlette.middleware.cors import CORSMiddleware
from app.service.metrics_service import get_metrics_service
from typing import Dict, List, Optional
from fastapi import FastAPI, Query, UploadFile, File, WebSocket
from app.config.settings import settings
from app.models.job import Job
from app.db.db import get_session
import uuid
from datetime import date
import pandas as pd
from app.etl.daily_metrics_etl import aggregate_daily_metrics
from app.rq.rq import queue
from loguru import logger
from rq import Retry
from rq_dashboard_fast import RedisQueueDashboard
from app.service.csv_service import dump_csv, FILE_UPLOAD_DIR
from app.models.daily_metric import DailyMetric
dashboard = RedisQueueDashboard(settings.redis_url, "/rq")

app = FastAPI(
    logger=logger
)

allowed_origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/rq", dashboard)

active_connections: Dict[str, List[WebSocket]] = {}

@app.post("/upload-csv")
async def uploadcsv(
    transactions: UploadFile = File(...),
    users: UploadFile = File(...),
):
    # Dump both files to disk in a single call
    rq_job = queue.enqueue(dump_csv, transactions, users, retry=Retry(max=3, interval=[10, 30, 60]))

    # Create a corresponding DB Job record
    with get_session() as session:
        job = Job(
            id=uuid.uuid4(),
            file_location=str(FILE_UPLOAD_DIR),
            filename=f"{transactions.filename},{users.filename}",
            total_rows=pd.read_csv(transactions.file).shape[0],
            processed_rows=0,
            error=None,
            processed_at=None,
            job_metadata={"rq_job_id": rq_job.id},
        )
        session.add(job)
        session.commit()

        queue.enqueue(aggregate_daily_metrics, job.id, retry=Retry(max=3, interval=[10, 30, 60]), depends_on=rq_job)
    return {
        "message": "success",
        "data": {
            "job_id": str(job.id),
        },
    }

@app.websocket("/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()

        await websocket.send_text(f"Message text was: {data}")

@app.get("/metrics/kpis")
async def get_metrics(regions: Optional[List[str]] = Query(None), start_date: date = Query(...), end_date: date = Query(...)):
    logger.info("Received metrics request")
    logger.info(f"Regions: {regions}, Start: {start_date}, End: {end_date}")
    try:
        metrics_service = get_metrics_service()
        metrics = metrics_service.get_daily_metrics_summary(regions, start_date, end_date)
        return {
            "message": "success",
            "data": {
                "kpis": metrics,
                "models_metrics": metrics_service.get_model_cost_summary(regions, start_date, end_date),
                "region_wise_spends": metrics_service.get_region_wise_metrics(regions, start_date, end_date),
                "company_wise_spends": metrics_service.get_company_wise_spends(regions, start_date, end_date),
                "max_date_range": metrics_service.max_date_range(),
            },
        }
    except Exception as e:
        logger.error(e)
        return {
            "message": "error",
            "data": str(e),
        }
