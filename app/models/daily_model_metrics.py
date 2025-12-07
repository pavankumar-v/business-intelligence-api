from app.db.base import Base
from sqlalchemy import Column, String, Float, Date, Integer

class DailyModelMetric(Base):
    __tablename__ = "daily_model_metrics"

    # Primary Key (Composite)
    date = Column(Date, primary_key=True)
    region = Column(String, primary_key=True)
    model_name = Column(String, primary_key=True)
    total_cost = Column(Float, nullable=False)
    conversation_count = Column(Integer, nullable=False)
    token_consumption = Column(Integer, nullable=False)
