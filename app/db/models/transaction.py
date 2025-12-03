from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import UUID, Column, String, Float, DateTime, Integer, ForeignKey
import uuid

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String, index=True)
    conversation_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    token_type = Column(String, nullable=False)
    token_count = Column(Integer, nullable=False)
    rate_per_1k = Column(Float, nullable=False)
    calculated_cost = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="transactions")