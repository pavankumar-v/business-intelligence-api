from sqlalchemy import UUID, Column, String, Date
from app.db.base import Base

class DailyActiveUser(Base):
    """
    Helper table to track unique active users per (date, region).
    Used to accurately calculate Active Subscriber Utilization Rate across chunks.
    """
    __tablename__ = "daily_active_users"
    
    date = Column(Date, primary_key=True, index=True)
    region = Column(String, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
