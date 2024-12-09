import asyncio
import os
from datetime import datetime
from enum import Enum
from typing import Dict
import httpx
import logging


class NodeStatus(Enum):
    HEALTHY = "healthy"
    SUSPECTED = "suspected"
    UNHEALTHY = "unhealthy"


logger = logging.getLogger("node-status-manager")


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class NodeStatusManager(metaclass=SingletonMeta):
    def __init__(self):
        self.HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", 10))
        self.HEALTH_CHECK_TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", 10))
        self.HEALTHY_THRESHOLD = int(os.getenv("HEALTHY_THRESHOLD", 2))
        self.UNHEALTHY_THRESHOLD = int(os.getenv("UNHEALTHY_THRESHOLD", 2))
        self.SECONDARY_AUTH_SECRET = os.getenv("SECONDARY_AUTH_SECRET")
        self.node_status: Dict[str, Dict] = {}

    async def ping_node(self, node_url: str) -> bool:
        """Pings the secondary node to check its health."""
        try:
            logger.debug(f"Pinging node {node_url} with timeout {self.HEALTH_CHECK_TIMEOUT} seconds.")
            async with httpx.AsyncClient(timeout=self.HEALTH_CHECK_TIMEOUT) as client:
                response = await client.get(f"{node_url}/ping", headers={"X-API-Key": self.SECONDARY_AUTH_SECRET})
                return response.status_code == 200
        except httpx.RequestError as e:
            logger.debug(f"Request error while pinging node {node_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while pinging node {node_url}: {e}")
        return False

    async def monitor_health(self, nodes: list):
        """Monitors the health of the secondary nodes."""
        try:
            while True:
                tasks = [self.check_node_status(node) for node in nodes]
                await asyncio.gather(*tasks)
                for node, status in self.node_status.items():
                    logger.info(f"Node {node} is {status['status']}")
                await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Health check monitor encountered an error: {e}")

    async def check_node_status(self, node_url: str):
        """Check and update the status of the node."""
        if node_url not in self.node_status:
            self.initialize_node_status(node_url)

        is_healthy = await self.ping_node(node_url)

        if is_healthy:
            self.handle_healthy_node(node_url)
        else:
            self.handle_unhealthy_node(node_url)

    def initialize_node_status(self, node_url: str):
        """Initialize the status for a new node."""
        self.node_status[node_url] = {
            "healthy_count": 0,
            "unhealthy_count": 0,
            "status": NodeStatus.HEALTHY.value,
            "last_updated": datetime.now().isoformat(),
        }

    def handle_healthy_node(self, node_url: str):
        """Update the status when a node is healthy."""
        self.node_status[node_url]["healthy_count"] += 1
        self.node_status[node_url]["unhealthy_count"] = 0

        if self.node_status[node_url]["status"] != NodeStatus.HEALTHY.value:
            self.mark_as_healthy(node_url)

    def handle_unhealthy_node(self, node_url: str):
        """Update the status when a node is unhealthy."""
        self.node_status[node_url]["unhealthy_count"] += 1
        self.node_status[node_url]["healthy_count"] = 0

        if self.node_status[node_url]["unhealthy_count"] >= self.UNHEALTHY_THRESHOLD:
            self.mark_as_unhealthy(node_url)
        else:
            self.mark_as_suspected(node_url)

    def mark_as_healthy(self, node_url: str):
        """Mark the node as healthy."""
        self.update_node_status(node_url, NodeStatus.HEALTHY)
        logger.info(f"Node {node_url} is marked as Healthy.")

    def mark_as_suspected(self, node_url: str):
        """Mark the node as suspected."""
        self.update_node_status(node_url, NodeStatus.SUSPECTED)
        logger.info(f"Node {node_url} is marked as Suspected.")

    def mark_as_unhealthy(self, node_url: str):
        """Mark the node as unhealthy."""
        self.update_node_status(node_url, NodeStatus.UNHEALTHY)
        logger.info(f"Node {node_url} is marked as Unhealthy.")

    def update_node_status(self, node_url: str, status: NodeStatus):
        """Update the status and last_updated field for a node."""
        self.node_status[node_url]["status"] = status.value
        self.node_status[node_url]["last_updated"] = datetime.now().isoformat()

    def is_node_healthy(self, node_url: str) -> bool:
        """Checks if a node is healthy based on its status. Returns True if healthy, False otherwise."""
        node_status = self.node_status.get(node_url)
        if node_status is None:
            logger.warning(f"Node status for {node_url} not found.")
            return False

        if node_status["status"] == NodeStatus.HEALTHY.value:
            return True
        else:
            logger.info(f"Node {node_url} is {node_status['status']}. Skipping replication.")
            return False
