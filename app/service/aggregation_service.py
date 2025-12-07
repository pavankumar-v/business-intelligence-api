from app.models.daily_model_metrics import DailyModelMetric
import uuid

from sqlalchemy import null, func, and_, case
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.daily_metric import DailyMetric

from sqlalchemy import select, func, case, Float
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.daily_metric import DailyMetric
from app.models.user import User  # adjust import path

class AggregationService():
    def __init__(self, db: Session, job_id: uuid.UUID) -> None:
        self.db = db
        self.job_id = job_id
    
    def aggregate_daily_metrics(self):
        # 1) Base CTE: use transactions as the core fact table
        base = (
            select(
                Transaction.date.label("usage_date"),
                Transaction.region.label("region"),
                Transaction.model_name.label("model_name"),
                Transaction.calculated_cost.label("calculated_cost"),
                Transaction.token_type.label("token_type"),
                Transaction.token_count.label("token_count"),
                Transaction.conversation_id.label("conversation_id"),
                Transaction.user_id.label("user_id"),
            )
            .cte("base")
        )

        # 2) Aggregate per (date, region)
        agg = (
            select(
                base.c.usage_date,
                base.c.region,
                func.sum(base.c.calculated_cost).label("total_cost"),
                func.count(func.distinct(base.c.conversation_id)).label(
                    "total_conversations"
                ),
                func.avg(base.c.calculated_cost).label("avg_spending"),
                # total prompt tokens
                func.sum(
                    case(
                        (base.c.token_type == "prompt", base.c.token_count),
                        else_=0,
                    )
                ).label("total_prompt_tokens"),
                # total completion tokens
                func.sum(
                    case(
                        (base.c.token_type == "completion", base.c.token_count),
                        else_=0,
                    )
                ).label("total_completion_tokens"),
            )
            .group_by(base.c.usage_date, base.c.region)
            .cte("agg")
        )

        # 3) Model-wise stats per (date, region, model_name)
        model_counts_base = (
            select(
                base.c.usage_date,
                base.c.region,
                base.c.model_name,
                func.count(func.distinct(base.c.conversation_id)).label(
                    "model_conversations"
                ),
                func.sum(base.c.calculated_cost).label("model_cost"),
            )
            .group_by(base.c.usage_date, base.c.region, base.c.model_name)
            .cte("model_counts_base")
        )

        # 4) Row-number windows to pick:
        #    - highest_model_used   (by model_conversations DESC)
        #    - least_used_model     (by model_conversations ASC)
        #    - costliest_model      (by model_cost DESC)
        model_counts = (
            select(
                model_counts_base.c.usage_date,
                model_counts_base.c.region,
                model_counts_base.c.model_name,
                model_counts_base.c.model_conversations,
                model_counts_base.c.model_cost,
                func.row_number()
                .over(
                    partition_by=(
                        model_counts_base.c.usage_date,
                        model_counts_base.c.region,
                    ),
                    order_by=model_counts_base.c.model_conversations.desc(),
                )
                .label("rn_highest"),
                func.row_number()
                .over(
                    partition_by=(
                        model_counts_base.c.usage_date,
                        model_counts_base.c.region,
                    ),
                    order_by=model_counts_base.c.model_conversations.asc(),
                )
                .label("rn_least"),
                func.row_number()
                .over(
                    partition_by=(
                        model_counts_base.c.usage_date,
                        model_counts_base.c.region,
                    ),
                    order_by=model_counts_base.c.model_cost.desc(),
                )
                .label("rn_costliest"),
            )
            .cte("model_counts")
        )

        mc_highest = model_counts.alias("mc_highest")
        mc_least = model_counts.alias("mc_least")
        mc_costliest = model_counts.alias("mc_costliest")

        # 5) Active subscribers per region (denominator)
        users_active = (
            select(
                User.region.label("region"),
                func.count(User.id).label("active_subscribers"),
            )
            .where(User.is_active_sub.is_(True))
            .group_by(User.region)
            .cte("users_active")
        )

        # 6) Active subscribers who used the product that day (numerator)
        used_active = (
            select(
                Transaction.date.label("usage_date"),
                Transaction.region.label("region"),
                func.count(func.distinct(Transaction.user_id)).label(
                    "used_active_subscribers"
                ),
            )
            .join(User, User.id == Transaction.user_id)
            .where(User.is_active_sub.is_(True))
            .group_by(Transaction.date, Transaction.region)
            .cte("used_active")
        )

        # total tokens for avg_token_consumption
        total_tokens = agg.c.total_prompt_tokens + agg.c.total_completion_tokens

        # 7) Final statement shaped like DailyMetric
        # active_subscriber_utilization_rate =
        #   used_active_subscribers / active_subscribers (per region)
        utilization_expr = func.coalesce(
            (
                func.coalesce(used_active.c.used_active_subscribers, 0)
                / func.nullif(users_active.c.active_subscribers, 0)
            ),
            0.0,
        )

        stmt = (
            select(
                # PK
                agg.c.usage_date.label("date"),
                agg.c.region.label("region"),

                # KPIs
                mc_highest.c.model_name.label("highest_model_used"),
                agg.c.avg_spending.label("avg_spending"),
                mc_costliest.c.model_name.label("costliest_model"),
                mc_least.c.model_name.label("least_used_model"),

                # avg_token_consumption = total tokens / total_conversations
                (
                    total_tokens
                    / func.nullif(agg.c.total_conversations, 0)
                ).label("avg_token_consumption"),

                agg.c.total_prompt_tokens.label("total_prompt_tokens"),
                agg.c.total_completion_tokens.label("total_completion_tokens"),

                utilization_expr.label("active_subscriber_utilization_rate"),

                # Supporting data
                agg.c.total_cost.label("total_cost"),
                agg.c.total_conversations.label("total_conversations"),
            )
            .join(
                mc_highest,
                (mc_highest.c.usage_date == agg.c.usage_date)
                & (mc_highest.c.region == agg.c.region)
                & (mc_highest.c.rn_highest == 1),
            )
            .join(
                mc_least,
                (mc_least.c.usage_date == agg.c.usage_date)
                & (mc_least.c.region == agg.c.region)
                & (mc_least.c.rn_least == 1),
            )
            .join(
                mc_costliest,
                (mc_costliest.c.usage_date == agg.c.usage_date)
                & (mc_costliest.c.region == agg.c.region)
                & (mc_costliest.c.rn_costliest == 1),
            )
            .outerjoin(
                used_active,
                (used_active.c.usage_date == agg.c.usage_date)
                & (used_active.c.region == agg.c.region),
            )
            .outerjoin(
                users_active,
                users_active.c.region == agg.c.region,
            )
            .order_by(agg.c.usage_date, agg.c.region)
        )

        rows = self.db.execute(stmt).all()

        for row in rows:
            dm = DailyMetric(
                date=row.date,
                region=row.region,
                highest_model_used=row.highest_model_used,
                avg_spending=row.avg_spending,
                costliest_model=row.costliest_model,
                least_used_model=row.least_used_model,
                avg_token_consumption=row.avg_token_consumption,
                total_prompt_tokens=row.total_prompt_tokens,
                total_completion_tokens=row.total_completion_tokens,
                active_subscriber_utilization_rate=row.active_subscriber_utilization_rate,
                total_cost=row.total_cost,
                total_conversations=row.total_conversations,
            )

            # (date, region) is the PK, so merge works as an "upsert"
            self.db.merge(dm)

        self.db.commit()

    def aggregate_daily_model_metrics(self):
        stmt = (
            select(
                Transaction.date.label("date"),
                Transaction.region.label("region"),
                Transaction.model_name.label("model_name"),
                func.sum(Transaction.calculated_cost).label("total_cost"),
                func.count(func.distinct(Transaction.conversation_id)).label(
                    "conversation_count"
                ),
                func.sum(Transaction.token_count).label("token_consumption"),
            )
            .group_by(
                Transaction.date,
                Transaction.region,
                Transaction.model_name,
            )
            .order_by(
                Transaction.date,
                Transaction.region,
                Transaction.model_name,
            )
        )

        rows = self.db.execute(stmt).all()

        for row in rows:
            dmm = DailyModelMetric(
                date=row.date,
                region=row.region,
                model_name=row.model_name,
                total_cost=row.total_cost,
                conversation_count=row.conversation_count,
                token_consumption=row.token_consumption,
            )

            # Composite PK (date, region, model_name) ensures merge works as upsert
            self.db.merge(dmm)

        self.db.commit()

    def aggregate_daily_company_metrics(self):
        pass
