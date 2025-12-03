from time import sleep
from fastapi import FastAPI
from app.config.settings import settings
from app.db.db import get_session
from app.db.models import User
from app.rq.rq import queue
from loguru import logger

from rq_dashboard_fast import RedisQueueDashboard
dashboard = RedisQueueDashboard(settings.redis_url, "/rq")

app = FastAPI(
    logger=logger
)

app.mount("/rq", dashboard)

def count_words_at_url(url):
    """Just an example function that's called async."""
    logger.info("Counting words at")
    sleep(4)
    return len(url.split())

@app.get("/")
async def read_root():
    logger.info(f"request / endpoint!")
    job = queue.enqueue(count_words_at_url, 'https://stamps.id')
    logger.info(f"Enqueued job: {job}")
    with get_session() as session:
        users = session.query(User).all()
        return {"users": users}
