import datetime as dt
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    region = Column(String)
    is_active_sub = Column(Boolean, default=False)
    department = Column(String)
    company_name = Column(String)
    signup_date = Column(DateTime, default=dt.datetime.utcnow)
