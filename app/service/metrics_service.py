from app.db.db import get_session
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional
from app.models.daily_metric import DailyMetric
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.daily_metric import DailyMetric  # adjust import

class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_daily_metrics_summary(self,regions: list[str] | None, start_date, end_date):
        # 1) Build common filter conditions
        conditions = []
        if regions:
            conditions.append(DailyMetric.region.in_(regions))
        if start_date:
            conditions.append(DailyMetric.date >= start_date)
        if end_date:
            conditions.append(DailyMetric.date <= end_date)

        # 2) Aggregate query for summary metrics
        agg_stmt = (
            select(
                func.coalesce(func.sum(DailyMetric.total_cost), 0).label("total_spendings"),
                func.coalesce(
                    func.sum(
                        DailyMetric.total_prompt_tokens
                        + DailyMetric.total_completion_tokens
                    ),
                    0,
                ).label("total_tokens"),
                func.coalesce(func.sum(DailyMetric.total_conversations), 0).label(
                    "total_conversations"
                ),
                func.coalesce(
                    func.avg(DailyMetric.active_subscriber_utilization_rate), 0
                ).label("active_sub_utilization"),
                func.count(func.distinct(DailyMetric.date)).label("num_days"),
            )
            .where(*conditions)
        )

        agg_row = self.db.execute(agg_stmt).one()

        total_spendings = float(agg_row.total_spendings or 0)
        total_tokens = int(agg_row.total_tokens or 0)
        total_conversations = int(agg_row.total_conversations or 0)
        num_days = int(agg_row.num_days or 0)

        # average token consumption per conversation (overall)
        if total_conversations > 0:
            average_token_consumption = total_tokens / total_conversations
        else:
            average_token_consumption = 0.0

        # average per-day spending (over days that had data)
        if num_days > 0:
            average_per_day_spending = total_spendings / num_days
        else:
            average_per_day_spending = 0.0

        active_sub_utilization = float(agg_row.active_sub_utilization or 0.0)

        # 3) "heighest_model_user" = model that most often appears as highest_model_used
        top_model_stmt = (
            select(
                DailyMetric.highest_model_used,
                func.count().label("cnt"),
            )
            .where(*conditions)
            .group_by(DailyMetric.highest_model_used)
            .order_by(func.count().desc())
            .limit(1)
        )

        top_model_row = self.db.execute(top_model_stmt).first()
        heighest_model_user = (
            top_model_row.highest_model_used if top_model_row is not None else None
        )

        # 4) spends_trend = [{ date, cost }]
        trend_stmt = (
            select(
                DailyMetric.date.label("date"),
                func.sum(DailyMetric.total_cost).label("cost"),
            )
            .where(*conditions)
            .group_by(DailyMetric.date)
            .order_by(DailyMetric.date)
        )

        trend_rows = self.db.execute(trend_stmt).all()
        spends_trend = [
            {"date": row.date, "cost": float(row.cost)} for row in trend_rows
        ]

        # 5) Final payload
        return {
            "total_spendings": total_spendings,
            "heighest_model_user": heighest_model_user,
            "average_token_consumption": average_token_consumption,
            "average_per_day_spending": average_per_day_spending,
            "active_sub_utilization": active_sub_utilization,
            "spends_trend": spends_trend,
        }



def get_metrics_service() -> MetricsService:
    with get_session() as db:
        return MetricsService(db)