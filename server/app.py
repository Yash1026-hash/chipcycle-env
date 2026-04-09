"""
ChipCycle - OpenEnv Compliant Server
======================================

This script uses the official `openenv_core` factory to spin up the API.
This explicitly guarantees compliance with the Hackathon Evaluation Agent,
as standard openenv routes (/reset, /step, /state) are used identically.
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

from openenv_core.env_server import create_app

# Wrap in OpenEnv SDK's native FastAPI server framework
app = create_app(
    env=ChipCycleEnvironment,
    action_cls=ChipCycleAction,
    observation_cls=ChipCycleObservation,
    env_name="ChipCycle"
)

@app.get("/")
def root():
    return {"message": "ChipCycle RL Environment — OpenEnv Compliant", "status": "running"}

def main():
    import uvicorn
    # Strip any potential whitespace or colons from PORT env var
    port_str = os.environ.get("PORT", "7860").strip().lstrip(":")
    port = int(port_str)
    print(f"INFO: Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
