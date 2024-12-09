import asyncio
import logging
import os
import random
import time
import uuid

import httpx
from fastapi import FastAPI, HTTPException, Body, Depends
from starlette.responses import JSONResponse

from common.log_entry import LogEntryCreate, LogEntry
from common.log_storage import LogStorage
from common.storage_strategy import MasterStorageStrategy
from common.node_status_manager import NodeStatusManager, NodeStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("master")


async def exponential_backoff_with_jitter(delay: float, max_delay: float) -> None:
    """
    Handles exponential backoff with jitter. This method will pause for the calculated backoff time.

    Parameters:
        delay: The current retry delay.
        max_delay: The maximum retry delay.
    """
    jitter = random.uniform(0, delay)
    backoff_delay = min(delay + jitter, max_delay)

    start_time = time.time()  # Record the time before sleeping
    logger.info(f"Waiting for {backoff_delay:.2f} seconds before retrying...")
    await asyncio.sleep(backoff_delay)

    end_time = time.time()
    actual_delay = end_time - start_time
    logger.debug(f"Sleep finished after {actual_delay:.2f} seconds (intended delay was {backoff_delay:.2f} seconds).")


class MasterNode:
    health_check_task = None

    def __init__(self,
                 log_storage: LogStorage = Depends(LogStorage),
                 status_manager: NodeStatusManager = Depends(NodeStatusManager)):
        self.app = FastAPI(lifespan=self.lifespan)
        self.app.post("/logs")(self.append_log)
        self.app.get("/logs")(self.list_logs)
        self.app.get("/health")(self.get_health_status)

        self.read_only = False
        self.secondary_urls = [url for url in os.getenv("SECONDARY_URLS", "").split(",") if url.strip()]
        self.INITIAL_RETRY_DELAY = int(os.getenv("INITIAL_RETRY_DELAY", 2))
        self.MAX_RETRY_DELAY = int(os.getenv("MAX_RETRY_DELAY", 30))
        self.SECONDARY_AUTH_SECRET = os.getenv("SECONDARY_AUTH_SECRET")

        logger.info(f"Loaded {len(self.secondary_urls)} secondary URLs.")
        logger.info(f"Initial Retry Delay set to: {self.INITIAL_RETRY_DELAY} seconds.")
        logger.info(f"Max Retry Delay set to: {self.MAX_RETRY_DELAY} seconds.")

        self.client = httpx.AsyncClient()
        self.lock = asyncio.Lock()
        self.log_storage = storage
        self.status_manager = status_manager

    async def lifespan(self, app: FastAPI):
        logger.debug("Starting up the Master application...")
        self.health_check_task = asyncio.create_task(self.status_manager.monitor_health(self.secondary_urls))
        yield
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                logger.info("Health check task successfully cancelled.")
        logger.debug("Shutting down the Master application...")
        await self.shutdown()

    async def shutdown(self):
        await self.client.aclose()
        logger.info("HTTP client closed.")

    def validate_write_concern(self, message_write_concern: int):
        """Ensure the write concern does not exceed the available secondary nodes."""
        if message_write_concern > (len(self.secondary_urls) + 1):
            raise ValueError(
                f"Write concern ({message_write_concern}) exceeds the number of secondary nodes available "
                f"({len(self.secondary_urls)}). Adjust the write concern or add more secondary nodes."
            )

    def has_quorum(self) -> bool:
        """Check if the majority of the nodes are healthy."""
        total_nodes = len(self.secondary_urls) + 1
        healthy_nodes = self.status_manager.get_healthy_nodes_count()
        required_quorum = (total_nodes // 2) + 1
        return healthy_nodes + 1 >= required_quorum

    def is_read_only(self) -> bool:
        """Returns True if the node should be in read-only mode due to quorum failure."""
        return not self.has_quorum()

    def update_read_only_status(self):
        """Update the read-only status based on the quorum."""
        if self.is_read_only():
            self.set_read_only_mode()
        else:
            self.unset_read_only_mode()

    def set_read_only_mode(self):
        """Switch the master node into read-only mode."""
        self.read_only = True
        logger.warning("Master node switched to read-only mode due to insufficient quorum.")

    def unset_read_only_mode(self):
        """Switch the master node back to writable mode."""
        self.read_only = False
        logger.info("Master node switched to writable mode.")

    async def append_log(self, entry: LogEntryCreate = Body(...)) -> JSONResponse:
        self.update_read_only_status()
        if self.read_only:
            logger.info("Master node is in read-only mode, rejecting log append request.")
            return JSONResponse(
                content={"detail": "Read-only mode due to insufficient nodes quorum."},
                status_code=503
            )

        async with self.lock:  # to ensure that only one coroutine can modify sequence_counter
            new_sequence_number = self.log_storage.count() + 1
            logger.info(f"Log #{new_sequence_number}. Received log entry request: {entry.message}")

            message_id = str(uuid.uuid4())
            write_concern = entry.write_concern
            try:
                self.validate_write_concern(write_concern)
            except ValueError as e:
                logger.error(f"Invalid write concern: {e}")
                return JSONResponse(
                    content={"detail": str(e)},
                    status_code=400
                )

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

            logger.info(
                f"Log #{log_entry.sequence_number}. Secondary URLs to replicate to: {self.secondary_urls}")

            ack_count = 1
            logger.info(f"Replication count for message #{log_entry.sequence_number} is {ack_count}/{write_concern}")

            replication_coroutines = [self.replicate_with_retries(url, log_entry) for url in self.secondary_urls]
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
        headers = {"X-API-Key": self.SECONDARY_AUTH_SECRET}
        max_delay = self.MAX_RETRY_DELAY
        delay = self.INITIAL_RETRY_DELAY

        attempt = 0
        while True:
            attempt += 1
            if not self.status_manager.is_node_healthy(url):
                await exponential_backoff_with_jitter(delay, max_delay)
                delay = min(delay * 2, max_delay)
                continue

            try:
                logger.info(
                    f"Log #{log_entry.sequence_number}. "
                    f"Attempting replication to {url}. Attempt {attempt}"
                )
                response = await self.client.post(
                    f"{url}/replicate",
                    json=log_entry.model_dump(),
                    headers=headers,
                    timeout=delay
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

            await exponential_backoff_with_jitter(delay, max_delay)
            delay = min(delay * 2, max_delay)

    def list_logs(self) -> JSONResponse:
        logger.info("Received request to list all logs.")
        return JSONResponse(
            content=[log.model_dump() for log in self.log_storage.list()],
            status_code=200
        )

    def get_health_status(self) -> JSONResponse:
        logger.info("Received request to get health status of secondary nodes.")
        logger.info(self.status_manager.node_status.items())
        health_status = [
            {
                "node_url": node_url,
                **status_data,
            }
            for node_url, status_data in self.status_manager.node_status.items()
        ]
        return JSONResponse(
            content={"nodes": health_status},
            status_code=200
        )


storage = LogStorage(MasterStorageStrategy('./storage.log'))
status_manager = NodeStatusManager()
master_node = MasterNode(log_storage=storage, status_manager=status_manager)
app = master_node.app
