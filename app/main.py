from fastapi import FastAPI
from app.db.db import get_session
from app.db.models import User

app = FastAPI()

@app.get("/")
async def read_root():
    with get_session() as session:
        users = session.query(User).all()
        return {"users": users}
