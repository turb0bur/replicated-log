from fastapi import FastAPI
from pydantic import BaseModel
import logging
import os
import asyncio
from typing import List

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secondary")

logs: List[dict] = []

REPLICATION_DELAY = float(os.getenv("REPLICATION_DELAY", "2"))

class LogEntry(BaseModel):
    id: int
    message: str

@app.post("/replicate")
async def replicate_log(entry: LogEntry):
    logger.info(f"Received replication request: {entry}")

    logger.info(f"Simulating delay of {REPLICATION_DELAY} seconds.")
    await asyncio.sleep(REPLICATION_DELAY)

    if any(log['id'] == entry.id for log in logs):
        logger.warning(f"Duplicate log entry received: {entry.id}")
        return {"status": "duplicate"}

    logs.append(entry.dict())
    logger.info(f"Log entry replicated: {entry}")
    return {"status": "ack"}

@app.get("/logs")
async def get_logs():
    logger.info("Retrieving all replicated log entries.")
    return logs
