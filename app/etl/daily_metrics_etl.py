import uuid
from app.db.db import get_session
from app.service.db_dumping_service import DBDumpingService
from app.db.models.job import Job

async def aggregate_daily_metrics(job_id: uuid.UUID) -> None:
    """
    Start the aggregation process.
    """
    with get_session() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        users_csv_path = job.file_location + "/" + job.filename.split(",")[1]
        user_csv_file = open(users_csv_path, "rb")
        await DBDumpingService(db).dump_users(user_csv_file)

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
