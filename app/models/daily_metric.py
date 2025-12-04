from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import UUID, Column, String, Float, DateTime, Integer, Date # Added Date
import sqlalchemy as sa # Added sa import
import uuid

class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    date = Column(Date, primary_key=True, index=True)
    region = Column(String, primary_key=True, index=True)

    # KPIs
    highest_model_used = Column(String, nullable=False)
    avg_spending = Column(Float, nullable=False)
    costliest_model = Column(String, nullable=False)
    least_used_model = Column(String, nullable=False)
    avg_token_consumption = Column(Float, nullable=False)
    total_prompt_tokens = Column(Integer, nullable=False, default=0)
    total_completion_tokens = Column(Integer, nullable=False, default=0)
    model_efficiency_ratio = Column(Float, nullable=False)
    active_subscriber_utilization_rate = Column(Float, nullable=False)
    
    # Supporting data (for validation)
    total_cost = Column(Float, nullable=False)
    total_conversations = Column(Integer, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=sa.func.now())
    updated_at = Column(DateTime, default=sa.func.now(), onupdate=sa.func.now())