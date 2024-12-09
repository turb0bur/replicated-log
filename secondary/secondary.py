import asyncio
import logging
import os
import random

from fastapi import FastAPI, HTTPException, Depends, Header
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
    def __init__(self, log_storage: LogStorage):
        self.app = FastAPI(lifespan=self.lifespan)
        self.app.post("/replicate")(self.replicate)
        self.app.get("/logs")(self.list_logs)
        self.app.get("/ping")(self.ping)

        self.MAX_REPLICATION_DELAY = int(os.getenv("MAX_REPLICATION_DELAY", 5))
        self.SECONDARY_AUTH_SECRET = os.getenv("SECONDARY_AUTH_SECRET")
        self.SECONDARY_ERROR_PROBABILITY = float(os.getenv("SECONDARY_ERROR_PROBABILITY", 0.1))

        logger.info(f"Max Replication Delay set to: {self.MAX_REPLICATION_DELAY} seconds.")

        self.log_storage = log_storage

    async def lifespan(self, app: FastAPI):
        logger.debug("Starting up the Secondary application...")
        yield
        logger.debug("Shutting down the Secondary application...")

    def authorize_request(self, x_api_key: str = Header(None)):
        """Authorization dependency to validate the X-API-Key header."""
        logger.debug(f"Authorizing request with key: {x_api_key}")
        if x_api_key != self.SECONDARY_AUTH_SECRET:
            raise HTTPException(status_code=403, detail="Unauthorized")

    async def simulate_delay(self, sequence_number: int):
        """Simulates a random delay in replication."""
        delay = random.randint(1, self.MAX_REPLICATION_DELAY)
        logger.info(
            f"Log #{sequence_number}. "
            f"Simulating replication delay of {delay} seconds"
        )
        await asyncio.sleep(delay)

    def simulate_error(self, sequence_number: int):
        """Simulates a random internal server error based on probability."""
        if random.random() < self.SECONDARY_ERROR_PROBABILITY:
            logger.error(f"Log #{sequence_number}. "
                         f"Simulated error for log replication with {self.SECONDARY_ERROR_PROBABILITY * 100}% chance")
            raise HTTPException(status_code=500, detail="Simulated internal server error")

    async def replicate(self, log_entry: LogEntry, x_api_key: str = Header(None)) -> JSONResponse:
        """Replicates the log entry to the secondary node with authorization."""
        self.authorize_request(x_api_key)
        try:
            self.simulate_error(log_entry.sequence_number)
            await self.simulate_delay(log_entry.sequence_number)

            self.log_storage.append(log_entry)
            logger.info(f"Log #{log_entry.sequence_number}. Replicated to secondary node")

            return JSONResponse(content={
                "message": "Replication successful",
                "sequence_number": log_entry.sequence_number,
            }, status_code=200)
        except Exception as e:
            logger.error(f"Log #{log_entry.sequence_number}. Unexpected error in replication: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def list_logs(self) -> JSONResponse:
        """List all the logs stored in the secondary node, ensuring total order and completeness."""
        logger.info("Received request to list all replicated logs.")

        logs = self.log_storage.list()

        if not logs:
            return JSONResponse(content=[], status_code=200)

        max_sequence_number = max(log.sequence_number for log in logs)

        if len(logs) != max_sequence_number:
            logger.warning("Log sequence is incomplete. Missing sequence numbers.")
            raise HTTPException(status_code=500, detail="Log sequence is incomplete.")

        sorted_logs = sorted(logs, key=lambda log: log.sequence_number)
        return JSONResponse(
            content=[log.model_dump() for log in sorted_logs],
            status_code=200
        )

    async def ping(self, x_api_key: str = Header(None)) -> JSONResponse:
        """Ping endpoint to check secondary node health with authorization."""
        self.authorize_request(x_api_key)
        logger.debug("Ping request received.")
        return JSONResponse(
            content={"message": "Secondary node is healthy."},
            status_code=200
        )


storage = LogStorage(SecondaryStorageStrategy('./storage.log'))
secondary_node = SecondaryNode(log_storage=storage)
app = secondary_node.app
