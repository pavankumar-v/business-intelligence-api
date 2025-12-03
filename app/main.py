from time import sleep
from typing import Dict, List
from fastapi import FastAPI, UploadFile, File, WebSocket
from app.config.settings import settings
from app.db.models import User
from app.db.models.job import Job
from app.db.db import get_session
import uuid
from datetime import datetime
from app.etl.daily_metrics_etl import aggregate_daily_metrics
from app.rq.rq import queue
from loguru import logger
from rq import Retry
from rq_dashboard_fast import RedisQueueDashboard
from app.service.aggregation_service import AggregationService
from app.service.csv_service import dump_csv, FILE_UPLOAD_DIR
from app.service.db_dumping_service import DBDumpingService
dashboard = RedisQueueDashboard(settings.redis_url, "/rq")

app = FastAPI(
    logger=logger
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
            total_rows=0,
            processed_rows=0,
            error=None,
            processed_at=None,
            job_metadata={"rq_job_id": rq_job.id},
        )
        session.add(job)
        session.commit()

        queue.enqueue(aggregate_daily_metrics, job.id, retry=Retry(max=3, interval=[10, 30, 60]))
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

