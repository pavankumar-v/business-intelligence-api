from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from contextlib import contextmanager

# engine — one per process
engine = create_engine(
    settings.pg_url,
    pool_size=10,
    max_overflow=20,
    future=True,   # modern 2.0 style if using SQLAlchemy 1.4+
)

# session factory
SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=False)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()