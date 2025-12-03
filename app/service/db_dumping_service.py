from io import BytesIO
from loguru import logger
import pandas as pd
from pandas.io.parsers import TextFileReader
from sqlalchemy.orm import Session
from app.db.db import SessionLocal
import csv

from app.db.models.user import User
from schema.schema import CSVUser

class DBDumpingService():
    TRANSACTION_CHUNK_SIZE = 1000
    USER_CHUNK_SIZE = 1000
    
    def __init__(self, db: Session) -> None:
        self.db = db

    def map_user_csv_rows(self,user: CSVUser) -> User:
        return User(
            id=user["User_ID"],
            username=user["User_Name"],
            region=user["Region"],
            is_active_sub=user["Is_Active_Sub"],
            department=user["Department"],
            company_name=user["Company_Name"],
            signup_date=user["Signup_Date"],
        )

    async def dump_users(self, user_csv: BytesIO) -> None:
        user_chunks: TextFileReader = pd.read_csv(user_csv, chunksize=self.USER_CHUNK_SIZE)
        for chunk in user_chunks:
            users = chunk.apply(self.map_user_csv_rows, axis=1)
            self.db.add_all(users)
            self.db.commit()

    def dump_transactions_in_chunks(self, transaction_csv: BytesIO) -> None:
        # TODO: Implement this
        pass