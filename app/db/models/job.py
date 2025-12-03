from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import UUID, Column, String, Float, DateTime, Integer, ForeignKey, Text
import uuid

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    file_location = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    total_rows = Column(Integer, nullable=False)
    processed_rows = Column(Integer, nullable=False)
    error = Column(Text)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    