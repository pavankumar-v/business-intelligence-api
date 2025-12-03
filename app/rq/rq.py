from redis import Redis
from rq import Queue
from app.config.settings import settings

queue = Queue(connection=Redis(
    host=settings.redis_host,
    port=settings.redis_port,
))