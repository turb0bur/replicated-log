from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import os
import httpx
import asyncio
from typing import List

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("master")

logs: List[dict] = []

SECONDARY_URLS = os.getenv("SECONDARY_URLS", "").split(",")

class LogEntry(BaseModel):
    message: str

async def replicate_to_secondary(log_entry: dict, url: str, client: httpx.AsyncClient):
    """
    Asynchronously replicate a single log entry to a secondary node.
    """
    try:
        logger.info(f"Replicating to Secondary at {url}")
        response = await client.post(f"{url}/replicate", json=log_entry, timeout=10.0)
        if response.status_code == 200:
            logger.info(f"Replication to {url} acknowledged.")
        else:
            logger.error(f"Replication to {url} failed with status code {response.status_code}.")
            raise HTTPException(status_code=500, detail=f"Replication to {url} failed.")
    except httpx.RequestError as e:
        logger.error(f"Error replicating to {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error replicating to {url}: {e}")

@app.post("/logs")
async def add_log(entry: LogEntry):
    log_id = len(logs) + 1
    log_entry = {"id": log_id, "message": entry.message}
    logs.append(log_entry)
    logger.info(f"Received log entry: {log_entry}")

    async with httpx.AsyncClient() as client:
        tasks = [
            replicate_to_secondary(log_entry, url.strip(), client)
            for url in SECONDARY_URLS if url.strip()
        ]

        try:
            await asyncio.gather(*tasks)
        except HTTPException as e:

            logs.pop()
            logger.error(f"Replication failed: {e.detail}")
            raise HTTPException(status_code=500, detail="Failed to replicate to all secondaries.")

    return {"status": "success", "log": log_entry}

@app.get("/logs")
async def get_logs():
    logger.info("Retrieving all log entries.")
    return logs
