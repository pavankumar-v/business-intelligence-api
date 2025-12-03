from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    User_ID: int
    User_Name: str
    Region: str
    Is_Active_Sub: bool
    Department: Optional[str] = None
    Company_Name: Optional[str] = None
    Signup_Date: datetime


class Transaction(BaseModel):
    RowId: int
    User_ID: int
    Model_Name: str
    Conversation_ID: str
    Token_Type: str
    Token_Count: int
    Rate_Per_1k: float
    Calculated_Cost: float
    Timestamp: datetime
