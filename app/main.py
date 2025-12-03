from fastapi import FastAPI, UploadFile, File
from app.config.settings import settings
from app.db.models import User
import uuid
from app.rq.rq import queue
from loguru import logger
from rq import Retry
from rq_dashboard_fast import RedisQueueDashboard
from app.service.csv_service import dump_csv
dashboard = RedisQueueDashboard(settings.redis_url, "/rq")

app = FastAPI(
    logger=logger
)

app.mount("/rq", dashboard)

@app.post("/upload-csv")
async def uploadcsv(
    transactions: UploadFile = File(...),
    users: UploadFile = File(...),
):
    # Dump both files to disk in a single call
    queue.enqueue(dump_csv, transactions, users, retry=Retry(max=3, interval=[10, 30, 60]))

    return {
        "message": "Files received and dumped to disk",
        "transactions_name": transactions.filename,
        "users_name": users.filename,
    }
