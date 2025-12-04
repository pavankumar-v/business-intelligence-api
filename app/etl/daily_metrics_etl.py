from datetime import date
from select import select
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
        affected_date_regions = db_dumping_service.dump_transactions_in_chunks()

        for idx, (date_val, region, total_rows) in enumerate(sorted(affected_date_regions), 1):
            logger.info("Processing {}/{}: Date: {} Region: {} Total Rows: {}", idx, len(affected_date_regions), date_val, region, total_rows)
            aggregate_daily_metrics_from_db(db, date_val, region)


def calculate_model_metrics_from_db(db: Session, target_date: date, target_region: str) -> dict:
    """
    Calculate model-specific metrics by querying database
    Gets ALL transactions for this date/region (not just current chunk)
    """
    
    model_query = (
        db.query(
            Transaction.model_name,
            func.count(Transaction.id).label('usage_count'),
            func.sum(Transaction.calculated_cost).label('total_cost'),
        )
        .join(User, Transaction.user_id == User.id)
        .filter(Transaction.date == target_date)
        .filter(User.region == target_region)
        .group_by(Transaction.model_name)
        .all()
    )
    
    if not model_query:
        return {
            'highest_model_used': 'N/A',
            'costliest_model': 'N/A',
            'least_used_model': 'N/A',
        }
    
    # per-model metrics
    model_data = []
    for model in model_query:
        avg_cost = model.total_cost / model.usage_count if model.usage_count > 0 else 0
        model_data.append({
            'name': model.model_name,
            'count': model.usage_count,
            'avg_cost': avg_cost,
            'total_cost': model.total_cost
        })
    
    highest_used = max(model_data, key=lambda x: x['count'])
    least_used = min(model_data, key=lambda x: x['count'])
    costliest = max(model_data, key=lambda x: x['avg_cost'])
    
    return {
        'highest_model_used': highest_used['name'],
        'costliest_model': costliest['name'],
        'least_used_model': least_used['name'],
    }


def aggregate_daily_metrics_from_db(db: Session, target_date: date, target_region: str):
    """
    Calculate metrics by querying ALL transactions from database for this date/region
    This ensures accuracy even if transactions were added across multiple CSV imports
    """
    
    # Query ALL transactions for this date/region from database
    base_stats = (
        db.query(
            func.sum(Transaction.calculated_cost).label('total_cost'),
            func.count(Transaction.id).label('total_transactions'),
            func.count(distinct(Transaction.conversation_id)).label('total_conversations'),
            func.count(distinct(Transaction.user_id)).label('unique_users'),
            func.sum(case(
                (Transaction.token_type == 'prompt', Transaction.token_count),
                else_=0
            )).label('total_prompt_tokens'),
            func.sum(case(
                (Transaction.token_type == 'completion', Transaction.token_count),
                else_=0
            )).label('total_completion_tokens'),
            func.sum(Transaction.token_count).label('total_tokens'),
        )
        .join(User, Transaction.user_id == User.id)
        .filter(Transaction.date == target_date)
        .filter(User.region == target_region)
    ).first()
    
    if not base_stats or base_stats.total_transactions == 0:
        print(f"No transactions found for {target_date}, {target_region}")
        return
    
    # model-specific metrics from database
    model_stats = calculate_model_metrics_from_db(db, target_date, target_region)
    
    # derived metrics
    avg_spending = (
        base_stats.total_cost / base_stats.total_transactions 
        if base_stats.total_transactions > 0 else 0
    )
    
    avg_token_consumption = (
        base_stats.total_tokens / base_stats.total_transactions 
        if base_stats.total_transactions > 0 else 0
    )
    
    model_efficiency_ratio = (
        base_stats.total_completion_tokens / base_stats.total_prompt_tokens 
        if base_stats.total_prompt_tokens > 0 else 0
    )
    
    # active subscriber utilization rate
    active_subscribers = get_active_subscribers_count(db, target_date, target_region)
    active_subscriber_utilization_rate = (
        (base_stats.unique_users / active_subscribers * 100) 
        if active_subscribers > 0 else 0
    )
    
    metric_data = {
        'highest_model_used': model_stats['highest_model_used'],
        'avg_spending': round(avg_spending, 4),
        'costliest_model': model_stats['costliest_model'],
        'least_used_model': model_stats['least_used_model'],
        'avg_token_consumption': round(avg_token_consumption, 2),
        'total_prompt_tokens': int(base_stats.total_prompt_tokens or 0),
        'total_completion_tokens': int(base_stats.total_completion_tokens or 0),
        'model_efficiency_ratio': round(model_efficiency_ratio, 4),
        'active_subscriber_utilization_rate': round(active_subscriber_utilization_rate, 2),
        'total_cost': round(float(base_stats.total_cost), 4),
        'total_conversations': int(base_stats.total_conversations),
    }
    
    # Upsert: Update if exists, insert if new
    existing = db.query(DailyMetric).filter(
        DailyMetric.date == target_date,
        DailyMetric.region == target_region
    ).first()
    
    if existing:
        for key, value in metric_data.items():
            setattr(existing, key, value)
        print(f"Updated existing metrics")
    else:
        metric = DailyMetric(
            date=target_date,
            region=target_region,
            **metric_data
        )
        db.add(metric)
        print(f"Created new metrics")
    
    db.commit()



def get_active_subscribers_count(db: Session, target_date: date, target_region: str) -> int:
    """
    Get count of active subscribers for a region on a specific date
    """
    count = db.query(func.count(User.id)).filter(
        User.region == target_region,
    ).scalar()
    
    return count or 1 