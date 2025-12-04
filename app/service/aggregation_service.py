from io import BytesIO
from typing import Iterable
import uuid

from sqlalchemy import null
from sqlalchemy.orm import Session
from app.models.job import Job
from app.service.db_dumping_service import DBDumpingService
from app.models.transaction import Transaction

class AggregationService():
    def __init__(
                self, 
                db: Session,
                job_id: uuid.UUID,
                db_dumping_service: DBDumpingService,
                user_csv_io: BytesIO, 
                transaction_csv_io: BytesIO
        ) -> None:
        """
        Initialize the AggregationService with the provided dependencies.
        """
        self.db = db
        self.db_dumping_service = db_dumping_service
        self.job_id = job_id
        self.job = None
        self.user_csv_io = user_csv_io
        self.transaction_csv_io = transaction_csv_io
    
    def aggregate_daily_metrics(self, transactions: Iterable[Transaction]):
        pass

    def aggregate_daily_model_metrics(self, transactions: Iterable[Transaction]):
        pass

    def aggregate_daily_company_metrics(self, transactions: Iterable[Transaction]):
        pass


