"""
ChipCycle - HTTP Client for interacting with the environment server.
"""

import httpx
from typing import Any, Dict, Optional

from models import ChipCycleAction, ChipCycleObservation, ChipCycleState


class ChipCycleClient:
    """Client for the ChipCycle environment HTTP server."""

    def __init__(self, base_url: str = "http://localhost:7860", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout)

    def health(self) -> Dict[str, Any]:
        """Check server health."""
        resp = self.client.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()

    def list_tasks(self) -> Dict[str, Any]:
        """List available tasks."""
        resp = self.client.get(f"{self.base_url}/tasks")
        resp.raise_for_status()
        return resp.json()["tasks"]

    def reset(self, task_id: str = "synthesis_review") -> ChipCycleObservation:
        """Reset environment with a specific task."""
        resp = self.client.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id},
        )
        resp.raise_for_status()
        return ChipCycleObservation(**resp.json()["observation"])

    def step(self, action: ChipCycleAction) -> ChipCycleObservation:
        """Take an action in the environment."""
        resp = self.client.post(
            f"{self.base_url}/step",
            json={"action": action.model_dump()},
        )
        resp.raise_for_status()
        return ChipCycleObservation(**resp.json()["observation"])

    def state(self) -> ChipCycleState:
        """Get current environment state."""
        resp = self.client.get(f"{self.base_url}/state")
        resp.raise_for_status()
        return ChipCycleState(**resp.json()["state"])

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
