import os
from pathlib import Path
from fastapi import UploadFile

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"

# Ensure uploads directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def dump_csv(
    transactions: UploadFile,
    users: UploadFile,
):
    """Dump two uploaded CSV files to local disk and return their saved paths."""

    if not transactions.filename:
        raise ValueError("Transactions filename is required to dump CSV")
    if not users.filename:
        raise ValueError("Users filename is required to dump CSV")

    transactions_path = UPLOAD_DIR / transactions.filename
    users_path = UPLOAD_DIR / users.filename

    # Ensure we read from the start
    await transactions.seek(0)
    await users.seek(0)

    transactions_content = await transactions.read()
    users_content = await users.read()

    with open(transactions_path, "wb") as f:
        f.write(transactions_content)

    with open(users_path, "wb") as f:
        f.write(users_content)

    return str(transactions_path), str(users_path)
