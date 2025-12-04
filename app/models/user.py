import datetime as dt
import uuid
from sqlalchemy import UUID, Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    region = Column(String)
    is_active_sub = Column(Boolean, default=False)
    department = Column(String)
    company_name = Column(String)
    signup_date = Column(DateTime, default=dt.datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user")