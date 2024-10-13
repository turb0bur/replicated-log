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

        self.SECONDARY_URLS = [f"{url.strip()}/replicate" for url in os.getenv("SECONDARY_URLS", "").split(",") if
                               url.strip()]
        self.RETRY_COUNT = int(os.getenv("RETRY_COUNT", 3))
        self.RETRY_DELAY = float(os.getenv("RETRY_DELAY", 2))
        self.REPLICATE_SECRET = os.getenv("REPLICATE_SECRET")

        logger.info(f"Loaded {len(self.SECONDARY_URLS)} secondary URLs.")
        logger.info(f"Retry Count set to: {self.RETRY_COUNT}")
        logger.info(f"Retry Delay set to: {self.RETRY_DELAY} seconds.")

        self.client = httpx.AsyncClient()
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
        async with asyncio.Lock():  # to ensure that only one coroutine can modify sequence_counter
            new_sequence_number = self.log_storage.count() + 1
            logger.info(f"Log #{new_sequence_number}. Received log entry request: {entry.message}")

            message_id = str(uuid.uuid4())
            logger.debug(f"Log #{new_sequence_number}. Generated message ID: {message_id}")

            log_entry = LogEntry(
                id=message_id,
                message=entry.message,
                write_concern=entry.write_concern,
                sequence_number=new_sequence_number
            )

            self.log_storage.append(log_entry)
            logger.info(f"Log #{log_entry.sequence_number}. Appended log to the storage")

            logger.debug(f"Sequence counter incremented to: {self.log_storage.count()}")

            secondary_urls = self.SECONDARY_URLS
            logger.info(f"Log #{log_entry.sequence_number}. Secondary URLs to replicate to: {secondary_urls}")

            ack_count = 1
            logger.info(
                f"Log #{log_entry.sequence_number}."
                f"Replication count for message #{self.log_storage.count()} is {ack_count}/{log_entry.write_concern}"
            )

            replication_tasks = [self.replicate_with_retries(url, log_entry) for url in self.SECONDARY_URLS]

            if log_entry.write_concern == 1:
                logger.info(
                    f"Log #{log_entry.sequence_number}."
                    f"Write concern of {log_entry.write_concern} is met. Returning response immediately."
                )
                asyncio.create_task(run_replication_tasks(replication_tasks, log_entry.sequence_number))
                return JSONResponse(
                    content=log_entry.model_dump(),
                    status_code=200
                )

            if replication_tasks:
                for task in asyncio.as_completed(replication_tasks):
                    try:
                        response = await task
                        if response.status_code == 200:
                            ack_count += 1
                            logger.info(
                                f"Log #{log_entry.sequence_number}."
                                f"Replication count for message #{self.log_storage.count()} is {ack_count}/{log_entry.write_concern}"
                            )
                    except Exception as e:
                        logger.error(f"Error replicating to secondary: {e}")
                        continue

                    if ack_count >= log_entry.write_concern:
                        logger.debug(
                            f"Log #{log_entry.sequence_number}."
                            f"Write concern of {log_entry.write_concern} met. Stopping further replication attempts."
                        )
                        asyncio.create_task(run_replication_tasks(replication_tasks, log_entry.sequence_number))
                        return JSONResponse(
                            content=log_entry.model_dump(),
                            status_code=200
                        )

            if ack_count < log_entry.write_concern:
                logger.error(
                    f"Failed to meet write concern: {log_entry.write_concern}.\n"
                    f"Replication count for message #{self.log_storage.count()} is {ack_count}/{log_entry.write_concern}"
                )
                raise HTTPException(status_code=500, detail=f"Failed to meet write concern: {log_entry.write_concern}")

            logger.info(f"Log #{log_entry.sequence_number}. Successfully replicated to all secondary nodes.")

            return JSONResponse(
                content=log_entry.model_dump(),
                status_code=200
            )

    async def replicate_with_retries(self, url: str, log_entry: LogEntry) -> httpx.Response:
        headers = {"X-API-Key": self.REPLICATE_SECRET}
        for attempt in range(1, self.RETRY_COUNT + 1):
            try:
                logger.info(
                    f"Log #{log_entry.sequence_number}."
                    f"Attempting replication to {url}. Attempt {attempt}/{self.RETRY_COUNT}"
                )
                response = await self.client.post(url, json=log_entry.model_dump(), headers=headers,
                                                  timeout=self.RETRY_DELAY)
                if response.status_code == 200:
                    logger.debug(f"Replication to {url} succeeded on attempt {attempt}")
                    return response
                else:
                    logger.warning(
                        f"Log #{log_entry.sequence_number}."
                        f"Replication to {url} failed with status code {response.status_code} on attempt {attempt}"
                    )
            except Exception as e:
                logger.error(
                    f"Log #{log_entry.sequence_number}."
                    f"Replication to {url} encountered an error on attempt {attempt}: {e}"
                )

            logger.info(
                f"Log #{log_entry.sequence_number}."
                f"Waiting for {self.RETRY_DELAY} seconds before next replication attempt to {url}"
            )
            await asyncio.sleep(self.RETRY_DELAY)

        logger.error(
            f"Log #{log_entry.sequence_number}."
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
