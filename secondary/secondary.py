import asyncio
import logging
import os
import random

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from common.log_entry import LogEntry
from common.log_storage import LogStorage
from common.storage_strategy import SecondaryStorageStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("secondary")


class SecondaryNode:
    def __init__(self):
        self.app = FastAPI(lifespan=self.lifespan)
        self.app.post("/replicate")(self.replicate)
        self.app.get("/logs")(self.list_logs)

        self.MAX_REPLICATION_DELAY = int(os.getenv("MAX_REPLICATION_DELAY", 5))
        self.REPLICATE_SECRET = os.getenv("REPLICATE_SECRET", )

        logger.info(f"Max Replication Delay set to: {self.MAX_REPLICATION_DELAY} seconds.")

        self.log_storage = LogStorage(SecondaryStorageStrategy())

    async def lifespan(self, app: FastAPI):
        logger.debug("Starting up the Secondary application...")
        yield  # Application runs here
        logger.debug("Shutting down the Secondary application...")

    async def replicate(self, log_entry: LogEntry) -> JSONResponse:
        delay = random.randint(1, self.MAX_REPLICATION_DELAY)
        logger.info(
            f"Log #{log_entry.sequence_number}. "
            f"Simulating replication delay of {delay} seconds"
        )
        await asyncio.sleep(delay)

        try:
            self.log_storage.append(log_entry)
            logger.info(f"Log #{log_entry.sequence_number}. Replicated to secondary node")

            return JSONResponse(content={
                "message": "Replication successful",
                "sequence_number": log_entry.sequence_number,
            }, status_code=200)
        except Exception as e:
            logger.error(f"Error in replication: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def list_logs(self) -> JSONResponse:
        logger.info("Received request to list all replicated logs.")
        return JSONResponse(
            content=[log.model_dump() for log in self.log_storage.list()],
            status_code=200
        )


secondary_node = SecondaryNode()
app = secondary_node.app
