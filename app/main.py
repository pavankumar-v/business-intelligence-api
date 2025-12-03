from fastapi import FastAPI
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



@app.get("/")
async def read_root():
    logger.info(f"request / endpoint!")
    job = queue.enqueue(count_words_at_url, 'https://stamps.id', retry=Retry(max=3, interval=[10, 30, 60]))
    # create_user()
    logger.info(f"Enqueued job: {job}")
    with get_session() as session:
        users = session.query(User).all()
        return {"users": users}
