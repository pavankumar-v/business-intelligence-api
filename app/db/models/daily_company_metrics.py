from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import UUID, Column, Integer, String, Float, Date # Added Date
import sqlalchemy as sa # Added sa import

class DailyCompanyMetric(Base):
    __tablename__ = "daily_company_metrics"

    date = Column(Date, primary_key=True)
    company_name = Column(String, primary_key=True)
    total_cost = Column(Float, nullable=False)
    conversation_count = Column(Integer, nullable=False)
