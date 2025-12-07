from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import UUID, Column, Integer, String, Float, Date # Added Date
import sqlalchemy as sa # Added sa import

class DailyCompanyMetric(Base):
    __tablename__ = "daily_company_metrics"

    # PK
    date = Column(Date, primary_key=True)
    region = Column(String, primary_key=True)
    company_name = Column(String, primary_key=True)

    highest_used_model = Column(String, nullable=False)
    least_used_model = Column(String, nullable=False)

    total_cost = Column(Float, nullable=False)
    conversation_count = Column(Integer, nullable=False)
