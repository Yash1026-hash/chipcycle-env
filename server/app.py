"""
ChipCycle - OpenEnv Compliant Server (Singleton Pattern)
=========================================================

The OpenEnv SDK's create_app creates a new env per HTTP request,
which breaks stateful RL loops. This server uses a GLOBAL singleton
environment so /reset → /step → /state all share the same instance.
"""

import os
import sys
from pathlib import Path

# Ensure the project root is on the path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Startup Diagnostics
try:
    from server.environment import ChipCycleEnvironment
    from models import ChipCycleAction, ChipCycleObservation
    print(f"INFO: Application root is {root_dir}")
    print("INFO: ChipCycle models and environment imported successfully.")
except ImportError as e:
    print(f"CRITICAL: Failed to import internal modules: {e}")
    sys.exit(1)

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, Optional

app = FastAPI(title="ChipCycle OpenEnv Server", version="1.0.0")

# ── Global singleton environment ──────────────────────────────────────
_env = ChipCycleEnvironment()

# ── Request/Response models ───────────────────────────────────────────
class ResetRequest(BaseModel):
    task_id: str = "synthesis_review"

class ActionRequest(BaseModel):
    action: Dict[str, Any]

# ── Routes ────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "ChipCycle RL Environment — OpenEnv Compliant", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/reset")
def reset(req: ResetRequest):
    obs = _env.reset(task_id=req.task_id)
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward,
        "done": obs.done,
    }

@app.post("/step")
def step(req: ActionRequest):
    action_data = req.action
    action = ChipCycleAction(**action_data)
    obs = _env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": obs.reward,
        "done": obs.done,
    }

@app.get("/state")
def state():
    s = _env.state
    return s.model_dump()

@app.get("/tasks")
def tasks():
    from server.tasks import TASKS
    return {
        tid: {"description": t["description"], "difficulty": t["difficulty"]}
        for tid, t in TASKS.items()
    }

@app.get("/schema/action")
def action_schema():
    return ChipCycleAction.model_json_schema()

@app.get("/schema/observation")
def observation_schema():
    return ChipCycleObservation.model_json_schema()


def main():
    import uvicorn
    port_str = os.environ.get("PORT", "7860").strip().lstrip(":")
    port = int(port_str)
    print(f"INFO: Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
