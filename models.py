"""
ChipCycle — OpenEnv Native Models
===================================

Strictly compliant Action, Observation, and State Pydantic classes
inheriting from openenv.core.env_server.types.
"""

from typing import Any, Dict, List, Optional
from pydantic import Field
from openenv.core.env_server.types import Action, Observation, State

# ─── ACTION ───────────────────────────────────────────────────────────────

class ChipCycleAction(Action):
    """
    An action the agent takes in the chip design review environment.
    """
    action_type: str = Field(description="Type of action to execute")
    section_name: Optional[str] = Field(default="", description="Section to analyze")
    path_id: Optional[str] = Field(default="", description="Timing path ID to investigate")
    corner_a: Optional[str] = Field(default="", description="PVT Corner A")
    corner_b: Optional[str] = Field(default="", description="PVT Corner B")
    param: Optional[str] = Field(default="", description="Parameter to compare")
    
    finding: Optional[Dict[str, Any]] = Field(default=None, description="Reported finding data")
    review: Optional[Dict[str, Any]] = Field(default=None, description="Final review data")

# ─── OBSERVATION ──────────────────────────────────────────────────────────

class ChipCycleObservation(Observation):
    """
    What the environment returns after each agent action.
    Inherits `done` and `reward` and `metadata` from openenv Observation.
    """
    task_id: str = Field(default="", description="Current task ID")
    task_description: str = Field(default="", description="Description of the goal")
    difficulty: str = Field(default="", description="Task difficulty")
    
    report_overview: str = Field(default="", description="Overview of reports")
    section_content: str = Field(default="", description="Data from analyzed section")
    available_sections: List[str] = Field(default_factory=list, description="Sections available")
    
    findings_submitted: List[Dict[str, Any]] = Field(default_factory=list, description="Findings so far")
    feedback: str = Field(default="", description="Environment feedback on last action")
    step_number: int = Field(default=0, description="Steps elapsed")
    max_steps: int = Field(default=0, description="Max allowed steps")

# ─── STATE ────────────────────────────────────────────────────────────────

class ChipCycleState(State):
    """
    Internal state / scoreboard for the running episode.
    Inherits `episode_id` and `step_count` from openenv State.
    """
    task_id: str = Field(default="", description="Current task ID")
    difficulty: str = Field(default="", description="Task difficulty")
    issues_found: int = Field(default=0, description="Number of real issues matched")
    false_positives: int = Field(default=0, description="Red herrings flagged")
    total_issues: int = Field(default=0, description="Total issues in design")
    current_score: float = Field(default=0.0, description="Internal score")
    is_done: bool = Field(default=False, description="Is episode terminated")
