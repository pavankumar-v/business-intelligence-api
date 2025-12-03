from fastapi import FastAPI
from app.config.settings import settings
from app.db.db import SessionLocal, get_session
from app.db.models import User
import uuid
from app.rq.rq import queue
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from rq import Retry
from rq_dashboard_fast import RedisQueueDashboard
dashboard = RedisQueueDashboard(settings.redis_url, "/rq")

app = FastAPI(
    logger=logger
)

app.mount("/rq", dashboard)


def count_words_at_url(url):
    """Just an example function that's called async."""
    logger.info("Counting words at")
    engine = create_engine(
        settings.pg_url,
        pool_size=10,
        max_overflow=20,
        future=True,   # modern 2.0 style if using SQLAlchemy 1.4+
    )

    # session factory
    SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=False)
    session = SessionLocal()
    new_user = User(
        username=f"test{uuid.uuid4()}",
        region="test",
        is_active_sub=False,
    )
    session.add(new_user)
    session.commit()
    session.close()
    
    return len(url.split())

@app.get("/")
async def read_root():
    logger.info(f"request / endpoint!")
    job = queue.enqueue(count_words_at_url, 'https://stamps.id', retry=Retry(max=3, interval=[10, 30, 60]))
    # create_user()
    logger.info(f"Enqueued job: {job}")
    with get_session() as session:
        users = session.query(User).all()
        return {"users": users}
