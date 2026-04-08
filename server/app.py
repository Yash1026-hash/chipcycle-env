"""
ChipCycle - OpenEnv Compliant Server
======================================

This script uses the official `openenv_core` factory to spin up the API.
This explicitly guarantees compliance with the Hackathon Evaluation Agent,
as standard openenv routes (/reset, /step, /state) are used identically.
"""

import os
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv_core.env_server import create_app
from server.environment import ChipCycleEnvironment
from models import ChipCycleAction, ChipCycleObservation

# Initialize core environment logic
env = ChipCycleEnvironment()

# Wrap in OpenEnv SDK's native FastAPI server framework
app = create_app(
    env=ChipCycleEnvironment,
    action_cls=ChipCycleAction,
    observation_cls=ChipCycleObservation,
    env_name="ChipCycle"
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
