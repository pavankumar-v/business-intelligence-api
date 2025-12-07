from app.models.daily_company_metrics import DailyCompanyMetric
from app.models.daily_model_metrics import DailyModelMetric
from app.db.db import get_session
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.daily_metric import DailyMetric
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from loguru import logger
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

        # 3) "heighest_model_used" = model that most often appears as highest_model_used
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
        heighest_model_used = (
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

        logger.info(f"{trend_stmt}")

        trend_rows = self.db.execute(trend_stmt).all()
        spends_trend = [
            {"date": row.date, "cost": round(row.cost, 2)} for row in trend_rows
        ]

        # 5) Final payload
        return {
            "total_spendings": round(total_spendings, 2),
            "heighest_model_used": heighest_model_used,
            "average_token_consumption": round(average_token_consumption),
            "average_per_day_spending": round(average_per_day_spending, 2),
            "active_sub_utilization": round(active_sub_utilization, 2),
            "spends_trend": spends_trend,
        }

    def get_model_cost_summary(self, regions: list[str] | None = None, start_date=None, end_date=None):
        conditions = []

        if regions:
            conditions.append(DailyModelMetric.region.in_(regions))

        if start_date:
            conditions.append(DailyModelMetric.date >= start_date)

        if end_date:
            conditions.append(DailyModelMetric.date <= end_date)

        stmt = (
            select(
                DailyModelMetric.model_name.label("model"),
                func.sum(DailyModelMetric.total_cost).label("total_cost"),
            )
            .where(*conditions)
            .group_by(DailyModelMetric.model_name)
            .order_by(func.sum(DailyModelMetric.total_cost).desc())
        )

        rows = self.db.execute(stmt).all()

        return [
            {
                "model": row.model,
                "total_cost": float(row.total_cost),
            }
            for row in rows
        ]

    def get_region_wise_metrics(self, regions: list[str] | None = None, start_date=None, end_date=None):
        conditions = []

        if regions:
            conditions.append(DailyMetric.region.in_(regions))

        if start_date:
            conditions.append(DailyMetric.date >= start_date)

        if end_date:
            conditions.append(DailyMetric.date <= end_date)

        stmt = (
            select(
                DailyMetric.region.label("region"),
                func.sum(DailyMetric.total_cost).label("total_spends"),
            )
            .where(*conditions)
            .group_by(DailyMetric.region)
            .order_by(func.sum(DailyMetric.total_cost).desc())
        )

        rows = self.db.execute(stmt).all()

        return [
            {
                "region": row.region,
                "total_spends": round(row.total_spends, 2),
            }
            for row in rows
        ]
    
    def get_company_wise_spends(self, regions: list[str] | None = None, start_date=None, end_date=None):
        conditions = []

        if regions:
            conditions.append(DailyCompanyMetric.region.in_(regions))

        if start_date:
            conditions.append(DailyCompanyMetric.date >= start_date)

        if end_date:
            conditions.append(DailyCompanyMetric.date <= end_date)

        stmt = (
            select(
                DailyCompanyMetric.company_name.label("company"),
                func.sum(DailyCompanyMetric.total_cost).label("total_spends"),
            )
            .where(*conditions)
            .group_by(DailyCompanyMetric.company_name)
            .order_by(func.sum(DailyCompanyMetric.total_cost).desc())
        )

        rows = self.db.execute(stmt).all()

        return [
            {
                "company": row.company,
                "total_spends": round(row.total_spends, 2),
            }
            for row in rows
        ]

    def max_date_range(self):
        # min_date, max_date
        stmt = (
            select(
                func.min(DailyMetric.date).label("min_date"),
                func.max(DailyMetric.date).label("max_date"),
            )
        )

        rows = self.db.execute(stmt).all()

        return rows[0].min_date, rows[0].max_date



        
def get_metrics_service() -> MetricsService:
    with get_session() as db:
        return MetricsService(db)