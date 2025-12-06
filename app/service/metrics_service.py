from app.db.db import get_session
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional
from app.models.daily_metric import DailyMetric

class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # Metrics to return
    # top_model_user 
    # highest_model_used
    # avg_spending_per_day
    # costliest_model
    # least_used_model
    # avg_token_consumption_per_day
    # model_efficiency
    # active_subscriber_utilization_rate
    def get_metrics(self, start_date: date, end_date: date, regions: Optional[list[str]] = None) -> dict:
        # Build base query with filters
        query = self.db.query(DailyMetric).filter(
            DailyMetric.date.between(start_date, end_date)
        )
        
        # Apply region filter if provided
        if regions:
            query = query.filter(DailyMetric.region.in_(regions))
        
        # Get all matching records
        daily_metrics = query.all()
        
        if not daily_metrics:
            return {
                "highest_model_used": None,
                "avg_spending_per_day": 0.0,
                "costliest_model": None,
                "least_used_model": None,
                "avg_token_consumption_per_day": 0.0,
                "model_efficiency": 0.0,
                "active_subscriber_utilization_rate": 0.0,
                "total_cost": 0.0,
                "spends_trend": [],
            }
        
        # Aggregate metrics
        total_spending = sum(metric.avg_spending for metric in daily_metrics)
        total_token_consumption = sum(metric.avg_token_consumption for metric in daily_metrics)
        num_days = len(set(metric.date for metric in daily_metrics))
        
        # Find highest model used (most frequent)
        model_usage = {}
        for metric in daily_metrics:
            model_usage[metric.highest_model_used] = model_usage.get(metric.highest_model_used, 0) + metric.total_conversations
        highest_model_used = max(model_usage, key=model_usage.get) if model_usage else None
        
        # Find costliest model
        model_costs = {}
        for metric in daily_metrics:
            model_costs[metric.costliest_model] = model_costs.get(metric.costliest_model, 0) + metric.total_cost
        costliest_model = max(model_costs, key=model_costs.get) if model_costs else None
        
        # Find least used model
        model_counts = {}
        for metric in daily_metrics:
            if metric.least_used_model:
                model_counts[metric.least_used_model] = model_counts.get(metric.least_used_model, 0) + 1
        least_used_model = min(model_counts, key=model_counts.get) if model_counts else None
        
        # Calculate averages
        avg_spending_per_day = total_spending / num_days if num_days > 0 else 0.0
        avg_token_consumption_per_day = total_token_consumption / num_days if num_days > 0 else 0.0
        
        # Calculate average model efficiency
        avg_model_efficiency = sum(metric.model_efficiency_ratio for metric in daily_metrics) / len(daily_metrics)
        
        # Calculate average active subscriber utilization rate
        avg_utilization_rate = sum(metric.active_subscriber_utilization_rate for metric in daily_metrics) / len(daily_metrics)
        
        # Calculate total cost across all metrics
        total_cost = sum(metric.total_cost for metric in daily_metrics)
        
        # Build spends_trend and token_consumption_trend
        # Group by date and sum costs/tokens across all regions
        date_aggregates = {}
        for metric in daily_metrics:
            date_key = metric.date
            if date_key not in date_aggregates:
                date_aggregates[date_key] = {
                    'cost': 0.0,
                    'token_consumption': 0
                }
            date_aggregates[date_key]['cost'] += metric.total_cost
            date_aggregates[date_key]['token_consumption'] += metric.avg_token_consumption
        
        # Convert to sorted list format
        spends_trend = [
            {
                'date': date_key.isoformat(),
                'cost': round(values['cost'], 2),
                'token_consumption': int(values['token_consumption'])
            }
            for date_key, values in sorted(date_aggregates.items())
        ]
        
        token_consumption_trend = [
            {
                'date': date_key.isoformat(),
                'cost': round(values['cost'], 2),
                'token_consumption': int(values['token_consumption'])
            }
            for date_key, values in sorted(date_aggregates.items())
        ]
        
        return {
            "highest_model_used": highest_model_used,
            "avg_spending_per_day": round(avg_spending_per_day, 2),
            "costliest_model": costliest_model,
            "least_used_model": least_used_model,
            "avg_token_consumption_per_day": round(avg_token_consumption_per_day, 2),
            "model_efficiency": round(avg_model_efficiency, 4),
            "active_subscriber_utilization_rate": round(avg_utilization_rate, 4),
            "total_cost": round(total_cost, 2),
            "spends_trend": spends_trend,
            # "token_consumption_trend": token_consumption_trend
        }


def get_metrics_service() -> MetricsService:
    with get_session() as db:
        return MetricsService(db)