from fastapi import FastAPI, UploadFile, File
from app.config.settings import settings
from app.db.models import User
import uuid
from app.rq.rq import queue
from loguru import logger
from rq import Retry
from rq_dashboard_fast import RedisQueueDashboard
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
    content1 = (await transactions.read()).decode("utf-8")
    content2 = (await users.read()).decode("utf-8")

    print("=== FILE 1 CONTENT ===")
    print(content1)
    print("=== FILE 2 CONTENT ===")
    print(content2)

    return {
        "message": "Files received and printed",
        "transactions_name": transactions.filename,
        "users_name": users.filename,
    }
