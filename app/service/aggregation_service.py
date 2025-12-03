from io import BytesIO
from typing import Iterable

from sqlalchemy.orm import Session
from app.db.models.job import Job
from app.service.db_dumping_service import DBDumpingService
from app.db.models.transaction import Transaction

class AggregationService():
    def __init__(
                self, 
                db: Session,
                job: Job,
                db_dumping_service: DBDumpingService,
                user_csv_io: BytesIO, 
                transaction_csv_io: BytesIO
        ) -> None:
        """
        Initialize the AggregationService with the provided dependencies.
        """
        self.db = db
        self.db_dumping_service = db_dumping_service
        self.user_csv_io = user_csv_io
        self.transaction_csv_io = transaction_csv_io
    
    def aggregate_daily_metrics(self, transactions: Iterable[Transaction]):
        pass

    def aggregate_daily_model_metrics(self, transactions: Iterable[Transaction]):
        pass

    def aggregate_daily_company_metrics(self, transactions: Iterable[Transaction]):
        pass
    
    async def start(self) -> None:
        """
        Start the aggregation process.
        """
        await self.db_dumping_service.dump_users(self.user_csv_io)

        # with await self.db_dumping_service.dump_transactions_in_chunks(self.transaction_csv_io) as transactions:
        #     self.aggregate_daily_metrics(transactions)
        #     self.aggregate_daily_model_metrics(transactions)
        #     self.aggregate_daily_company_metrics(transactions)

        #     self.job.rows_processed += len(transactions)
        #     self.db.add(self.job)
        #     self.db.commit()
        
        # self.job.processed_at = datetime.now()
        # self.db.add(self.job)
        # self.db.commit()


