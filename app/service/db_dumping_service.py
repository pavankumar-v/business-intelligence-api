from io import BytesIO
from loguru import logger
import pandas as pd
from pandas.io.parsers import TextFileReader
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.db.db import SessionLocal
import csv
from sqlalchemy import Table

from app.db.models.user import User

class DBDumpingService():
    TRANSACTION_CHUNK_SIZE = 1000
    USER_CHUNK_SIZE = 1000
    
    def __init__(self, db: Session) -> None:
        self.db = db

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

    async def dump_users(self, user_csv: BytesIO) -> None:
        """Bulk upsert users from a CSV file in chunks using ON CONFLICT.

        Key: username (unique).
        """
        user_chunks: TextFileReader = pd.read_csv(user_csv, chunksize=self.USER_CHUNK_SIZE)
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

    def dump_transactions_in_chunks(self, transaction_csv: BytesIO) -> None:
        # TODO: Implement this
        pass