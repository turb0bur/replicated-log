import asyncio
import logging
import os
import uuid

import httpx
from fastapi import FastAPI, HTTPException, Body
from starlette.responses import JSONResponse

from common.log_entry import LogEntryCreate, LogEntry
from common.log_storage import LogStorage
from common.storage_strategy import MasterStorageStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("master")


async def run_replication_tasks(tasks, sequence_number):
    await asyncio.gather(*tasks)
    logger.info(f"Log #{sequence_number}. Successfully replicated to all secondary nodes.")


class MasterNode:
    def __init__(self):
        self.app = FastAPI(lifespan=self.lifespan)
        self.app.post("/logs")(self.append_log)
        self.app.get("/logs")(self.list_logs)

        self.SECONDARY_URLS = [
            f"{url.strip()}/replicate"
            for url in os.getenv("SECONDARY_URLS", "").split(",")
            if url.strip()
        ]
        self.RETRY_COUNT = int(os.getenv("RETRY_COUNT", 3))
        self.RETRY_DELAY = float(os.getenv("RETRY_DELAY", 2))
        self.REPLICATE_SECRET = os.getenv("REPLICATE_SECRET")

        logger.info(f"Loaded {len(self.SECONDARY_URLS)} secondary URLs.")
        logger.info(f"Retry Count set to: {self.RETRY_COUNT}")
        logger.info(f"Retry Delay set to: {self.RETRY_DELAY} seconds.")

        self.client = httpx.AsyncClient()
        self.lock = asyncio.Lock()
        self.log_storage = LogStorage(MasterStorageStrategy())

    async def lifespan(self, app: FastAPI):
        logger.debug("Starting up the Master application...")
        yield  # Application runs here
        logger.debug("Shutting down the Master application...")
        await self.shutdown()

    async def shutdown(self):
        await self.client.aclose()
        logger.info("HTTP client closed.")

    async def append_log(self, entry: LogEntryCreate = Body(...)) -> JSONResponse:
        async with self.lock:  # to ensure that only one coroutine can modify sequence_counter
            new_sequence_number = self.log_storage.count() + 1
            logger.info(f"Log #{new_sequence_number}. Received log entry request: {entry.message}")

            message_id = str(uuid.uuid4())
            write_concern = entry.write_concern
            logger.debug(f"Log #{new_sequence_number}. Generated message ID: {message_id}")

            log_entry = LogEntry(
                id=message_id,
                message=entry.message,
                write_concern=write_concern,
                sequence_number=new_sequence_number
            )

            self.log_storage.append(log_entry)
            logger.info(f"Log #{log_entry.sequence_number}. Appended log to the storage")

            logger.debug(f"Sequence counter incremented to: {self.log_storage.count()}")

            logger.info(f"Log #{log_entry.sequence_number}. Secondary URLs to replicate to: {self.SECONDARY_URLS}")

            ack_count = 1
            logger.info(f"Replication count for message #{log_entry.sequence_number} is {ack_count}/{write_concern}")

            replication_coroutines = [self.replicate_with_retries(url, log_entry) for url in self.SECONDARY_URLS]
            replication_tasks = [asyncio.create_task(coro) for coro in replication_coroutines]

            if write_concern == 1:
                logger.info(f"Write concern 1 met. Responding immediately.")
                return JSONResponse(content=log_entry.model_dump(), status_code=200)

            acks_needed = write_concern - ack_count
            acks_received = 0

            async def monitor_acks():
                nonlocal acks_received
                for task in asyncio.as_completed(replication_tasks):
                    try:
                        response = await task
                        if response.status_code == 200:
                            acks_received += 1
                            logger.info(
                                f"Replication count for message #{log_entry.sequence_number} is {acks_received + ack_count}/{write_concern}")
                            if acks_received >= acks_needed:
                                logger.debug(f"Write concern of {write_concern} met.")
                                return
                    except Exception as e:
                        logger.error(f"Error replicating to secondary: {e}")

            monitor_task = asyncio.create_task(monitor_acks())
            await monitor_task

            if acks_received + ack_count >= write_concern:
                logger.info(f"Write concern {write_concern} met. Responding to client.")
                return JSONResponse(content=log_entry.model_dump(), status_code=200)
            else:
                logger.error(
                    f"Failed to meet write concern: {write_concern}.\n"
                    f"Replication count for message #{log_entry.sequence_number} is {acks_received + ack_count}/{write_concern}"
                )
                raise HTTPException(status_code=500, detail=f"Failed to meet write concern: {write_concern}")

    async def replicate_with_retries(self, url: str, log_entry: LogEntry) -> httpx.Response:
        headers = {"X-API-Key": self.REPLICATE_SECRET}
        for attempt in range(1, self.RETRY_COUNT + 1):
            try:
                logger.info(
                    f"Log #{log_entry.sequence_number}. "
                    f"Attempting replication to {url}. Attempt {attempt}/{self.RETRY_COUNT}"
                )
                response = await self.client.post(
                    url,
                    json=log_entry.model_dump(),
                    headers=headers,
                    timeout=self.RETRY_DELAY
                )
                if response.status_code == 200:
                    logger.debug(f"Replication to {url} succeeded on attempt {attempt}")
                    return response
                else:
                    logger.warning(
                        f"Log #{log_entry.sequence_number}. "
                        f"Replication to {url} failed with status code {response.status_code} on attempt {attempt}"
                    )
            except Exception as e:
                logger.error(
                    f"Log #{log_entry.sequence_number}. "
                    f"Replication to {url} encountered an error on attempt {attempt}: {e}"
                )

            logger.info(
                f"Log #{log_entry.sequence_number}."
                f"Waiting for {self.RETRY_DELAY} seconds before next replication attempt to {url}"
            )
            await asyncio.sleep(self.RETRY_DELAY)

        logger.error(
            f"Log #{log_entry.sequence_number}. "
            f"Failed to replicate to {url} after {self.RETRY_COUNT} attempts."
        )
        raise HTTPException(status_code=500, detail=f"Failed to replicate to {url} after {self.RETRY_COUNT} attempts.")

    def list_logs(self) -> JSONResponse:
        logger.info("Received request to list all logs.")
        return JSONResponse(
            content=[log.model_dump() for log in self.log_storage.list()],
            status_code=200
        )


master_node = MasterNode()
app = master_node.app
