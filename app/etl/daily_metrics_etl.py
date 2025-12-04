import uuid
from app.db.db import get_session
from app.service import db_dumping_service
from app.service.db_dumping_service import DBDumpingService
from app.models.job import Job

async def aggregate_daily_metrics(job_id: uuid.UUID) -> None:
    """
    Start the aggregation process.
    """
    with get_session() as db:
        job = db.query(Job).filter(Job.id == job_id).first()

        users_csv_path = job.file_location + "/" + job.filename.split(",")[1]
        transactions_csv_path = job.file_location + "/" + job.filename.split(",")[0]

        user_csv_file = open(users_csv_path, "rb")
        transaction_csv_file = open(transactions_csv_path, "rb")

        db_dumping_service = DBDumpingService(
            db=db,
            user_csv=user_csv_file,
            transaction_csv=transaction_csv_file
        )
        
        db_dumping_service.dump_users()
        affected_date_regions = db_dumping_service.dump_transactions_in_chunks()

        for idx, (date_val, region) in enumerate(sorted(affected_date_regions), 1):
            logger.info("Processing {}/{}: Date: {} Region: {}", idx, len(affected_date_regions), date_val, region)

    
    # self.job.processed_at = datetime.now()
    # self.db.add(self.job)
    # self.db.commit()
