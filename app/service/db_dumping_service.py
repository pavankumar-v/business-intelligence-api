import datetime
from io import BytesIO
from loguru import logger
import pandas as pd
from pandas.io.parsers import TextFileReader
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.db.db import SessionLocal
import csv
from sqlalchemy import Table

from app.models.transaction import Transaction
from app.models.user import User

class DBDumpingService():
    TRANSACTION_CHUNK_SIZE = 1000
    USER_CHUNK_SIZE = 1000
    
    def __init__(self, db: Session, user_csv: BytesIO, transaction_csv: BytesIO) -> None:
        self.db = db
        self.user_csv = user_csv
        self.transaction_csv = transaction_csv

    def bulk_upsert(self, table: Table, rows: list[dict], conflict_cols: list[str], update_cols: list[str]):
        stmt = insert(table).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={col: getattr(stmt.excluded, col) for col in update_cols}
        )
        self.db.execute(stmt)

    def map_user_csv_rows(self, row) -> User.__dict__:
        """Map a pandas row/Series to a CSVUser schema instance."""
        return {
            "id": row["User_ID"],
            "username": row["User_Name"],
            "region": row["Region"],
            "is_active_sub": row["Is_Active_Sub"],
            "department": row["Department"],
            "company_name": row["Company_Name"],
            "signup_date": row["Signup_Date"]
        }
    
    def map_transaction_csv_rows(self, row) -> Transaction.__dict__:
        """Map a pandas row/Series to a CSVTransaction schema instance."""
        return {
            "id": row["RowId"],
            "user_id": row["User_ID"],
            "model_name": row["Model_Name"],
            "conversation_id": row["Conversation_ID"],
            "token_type": row["Token_Type"],
            "token_count": row["Token_Count"],
            "rate_per_1k": row["Rate_Per_1k"],
            "calculated_cost": row["Calculated_Cost"],
            "timestamp": row["Timestamp"],
            "date": datetime.datetime.strptime(row["Timestamp"], "%Y-%m-%dT%H:%M:%SZ").date()
        }

    def dump_users(self) -> None:
        """Bulk upsert users from a CSV file in chunks using ON CONFLICT.

        Key: username (unique).
        """
        user_chunks: TextFileReader = pd.read_csv(self.user_csv, chunksize=self.USER_CHUNK_SIZE)
        for chunk in user_chunks:
            records: list[dict] = []

            # Build one record dict per row in this chunk
            for _, row in chunk.iterrows():
                record = self.map_user_csv_rows(row)
                records.append(record)

            if not records:
                continue

            self.bulk_upsert(
                table=User,
                rows=records,
                conflict_cols=["username"],
                update_cols=[
                    "region",
                    "is_active_sub",
                    "department",
                    "company_name",
                    "signup_date",
                ],
            )
            self.db.commit()



    def dump_transactions_in_chunks(self) -> None:
        transaction_chunks: TextFileReader = pd.read_csv(self.transaction_csv, chunksize=self.TRANSACTION_CHUNK_SIZE)
        for chunk in transaction_chunks:
            records: list[dict] = []

            # Build one record dict per row in this chunk
            for _, row in chunk.iterrows():
                record = self.map_transaction_csv_rows(row)
                records.append(record)

            if not records:
                continue

            self.bulk_upsert(
                table=Transaction,
                rows=records,
                conflict_cols=["id"],
                update_cols=[
                    "user_id",
                    "model_name",
                    "conversation_id",
                    "token_type",
                    "token_count",
                    "rate_per_1k",
                    "calculated_cost",
                    "timestamp",
                ],
            )
            self.db.commit()