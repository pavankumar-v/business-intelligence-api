from app.service.aggregation_service import AggregationService
from datetime import date
from select import select
from time import sleep
import uuid
from typing import Set, Tuple
from loguru import logger
import pandas as pd
from sqlalchemy import func, case, distinct, insert
from sqlalchemy.orm import Session
from app.db.db import get_session
from app.models.daily_metric import DailyMetric
from app.service import db_dumping_service
from app.service.db_dumping_service import DBDumpingService
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.user import User

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
        db_dumping_service.dump_transactions_in_chunks()

        aggregation_service = AggregationService(db=db, job_id=job_id)
        aggregation_service.aggregate_daily_metrics()
