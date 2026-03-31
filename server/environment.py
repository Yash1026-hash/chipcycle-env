"""
ChipCycle — Core Environment
=============================

This is the BRAIN of ChipCycle. It manages the entire interaction loop:

    Agent calls reset()  →  Gets a fresh design report to review
    Agent calls step()   →  Takes an action, gets feedback + reward
    Agent calls state()  →  Checks the scoreboard

The environment simulates what a real chip design sign-off engineer does:
  1. Read design reports (synthesis, timing, sign-off)
  2. Investigate specific sections for issues
  3. Submit findings with severity and root cause
  4. Propose ECO fixes (engineering change orders)
  5. Make a final tapeout go/no-go decision

SCORING:
  +0.15  → Correctly found a real design issue
  +0.05  → Got the severity right (critical/major/minor/info)
  +0.10  → Suggested a good fix
  +0.05  → ECO proposal with specific fix technique
  -0.10  → FALSE POSITIVE (flagged something that's actually fine)
  -0.05  → Duplicate finding (already reported this)
  -0.02  → Each investigation step (time = money in chip design)
"""

import random
import uuid
from typing import Any, Dict, List, Optional

from models import ChipCycleAction, ChipCycleObservation, ChipCycleState
from server.graders import compute_episode_score, grade_finding, grade_review
from server.tasks import TASKS
from openenv_core.env_server.interfaces import Environment

class ChipCycleEnvironment(Environment):
    """
    The main RL environment for chip design review.

    Usage:
        env = ChipCycleEnvironment()
        obs = env.reset("synthesis_review")  # Start reviewing a synthesis report
        obs = env.step(action)                # Take investigation/submission action
        state = env.state()                   # Check current score
    """

    def __init__(self) -> None:
        """Initialize with empty state. Must call reset() before step()."""
        super().__init__()
        self._state: Optional[ChipCycleState] = None  # Scoreboard
        self._task: Optional[Dict[str, Any]] = None    # Current task data
        self._found_issue_ids: list = []                # IDs of correctly found issues
        self._false_positives: int = 0                  # Count of wrong flags
        self._accumulated_reward: float = 0.0           # Total reward this episode
        self._findings: list = []                       # All submitted findings

    # ══════════════════════════════════════════════════════════════════════
    #  PUBLIC API — These are the 3 functions required by OpenEnv spec
    # ══════════════════════════════════════════════════════════════════════

    def reset(self, task_id: str = "synthesis_review") -> ChipCycleObservation:
        """
        Start a fresh episode with a new design review task.

        Args:
            task_id: Which task to load. Options:
                - "synthesis_review"  (easy)  — Find bugs in a synthesis report
                - "sta_debug"         (medium) — Debug timing analysis paths
                - "signoff_triage"    (hard)   — Triage full multi-corner sign-off

        Returns:
            First observation with the report overview and available sections.
        """
        # Validate task_id, default to easy if invalid
        if task_id not in TASKS:
            task_id = "synthesis_review"

        task_data = TASKS[task_id]
        
        # If the task definition is a list of cases, pick one at random
        if isinstance(task_data, list):
            task = random.choice(task_data)
        else:
            task = task_data

        # Reset all internal state
        self._task = task
        self._found_issue_ids = []
        self._false_positives = 0
        self._accumulated_reward = 0.0
        self._findings = []

        self._state = ChipCycleState(
            task_id=task_id,
            difficulty=task["difficulty"],
            issues_found=0,
            false_positives=0,
            total_issues=len(task["issues"]),
            current_score=0.0,
            is_done=False,
        )
        self._state.episode_id = str(uuid.uuid4())
        self._state.step_count = 0

        # Return the initial observation: report overview + available sections
        return ChipCycleObservation(
            done=False,
            reward=0.0,
            task_id=task_id,
            task_description=task["description"],
            difficulty=task["difficulty"],
            report_overview=task["overview"],
            section_content="",
            available_sections=list(task["sections"].keys()),
            findings_submitted=[],
            feedback="Episode started. Review the report overview, then analyze sections to find issues.",
            step_number=0,
            max_steps=task["max_steps"],
        )

    def step(self, action: ChipCycleAction) -> ChipCycleObservation:
        """
        Process one agent action and return the result.

        The agent can:
          - analyze_section  → Read a detailed section of the report
          - check_constraint → Check if a timing path has SDC exceptions
          - compare_corners  → Compare a parameter across PVT corners
          - propose_eco      → Suggest a specific engineering fix
          - submit_finding   → Report a found design issue
          - submit_review    → Submit final review (ends episode)

        Returns:
            Observation with updated content, reward, and feedback.
        """
        # Safety checks
        if self._state is None or self._task is None:
            return self._error_obs("Environment not initialized. Call reset() first.")
        if self._state.is_done:
            return self._done_obs("Episode already finished.")

        # Count this step
        self._state.step_count += 1
        step_cost = -0.02  # Every investigation step costs "time"

        # Route to the correct handler based on action type
        action_type = action.action_type.lower().strip()
        handlers = {
            "analyze_section":  lambda: self._handle_analyze(action, step_cost),
            "check_constraint": lambda: self._handle_check_constraint(action, step_cost),
            "compare_corners":  lambda: self._handle_compare_corners(action, step_cost),
            "propose_eco":      lambda: self._handle_propose_eco(action),
            "submit_finding":   lambda: self._handle_submit_finding(action),
            "submit_review":    lambda: self._handle_submit_review(action),
        }

        handler = handlers.get(action_type)
        if handler:
            return handler()
        else:
            valid = list(handlers.keys())
            return self._make_obs(
                reward=step_cost,
                feedback=f"Unknown action: '{action_type}'. Valid actions: {valid}",
                section_content="",
            )

    @property
    def state(self) -> ChipCycleState:
        """Return the current scoreboard (state). Can be called anytime."""
        if self._state is None:
            return ChipCycleState()
        # Create a new instance copying the values
        return self._state.model_copy()

    # ══════════════════════════════════════════════════════════════════════
    #  ACTION HANDLERS — One function per action type
    # ══════════════════════════════════════════════════════════════════════

    def _handle_analyze(self, action: ChipCycleAction, step_cost: float) -> ChipCycleObservation:
        """
        ANALYZE_SECTION: Show detailed content of a report section.

        Like an engineer clicking on "Timing Summary" or "DRC Report"
        in their EDA tool to see the full details.
        """
        section = action.section_name.lower().strip()
        sections = self._task["sections"]

        if not section:
            return self._make_obs(
                reward=step_cost,
                feedback=f"Specify section_name. Available: {list(sections.keys())}",
                section_content="",
            )

        # Fuzzy match: "timing" matches "timing_summary"
        matched_section = None
        for key in sections:
            if section in key or key in section:
                matched_section = key
                break

        if matched_section is None:
            return self._make_obs(
                reward=step_cost,
                feedback=f"Section '{section}' not found. Available: {list(sections.keys())}",
                section_content="",
            )

        self._accumulated_reward += step_cost
        return self._make_obs(
            reward=step_cost,
            feedback=f"Showing section: {matched_section}",
            section_content=sections[matched_section],
        )

    def _handle_check_constraint(self, action: ChipCycleAction, step_cost: float) -> ChipCycleObservation:
        """
        CHECK_CONSTRAINT: Check if a timing path has SDC exceptions.

        In real chip design, not every "violation" is real. Some paths are
        intentionally excluded from timing (false paths, multicycle paths).
        This action lets the agent check if a path has such exceptions.
        """
        path_id = action.path_id.lower().strip()
        self._accumulated_reward += step_cost

        # In Task 2, path 2 is through an async FIFO — it's a false path
        if self._task["id"] == "sta_debug" and ("2" in path_id or "cross" in path_id or "async" in path_id):
            return self._make_obs(
                reward=step_cost,
                feedback=(
                    "SDC constraint check:\n"
                    "  Found: set_false_path -from [get_clocks clk_core] -to [get_clocks clk_spi]\n"
                    "  BUT: This doesn't cover paths through async_fifo/mem*.\n"
                    "  The async FIFO uses gray-code synchronization — this path is\n"
                    "  functionally safe but the SDC constraint is incomplete.\n"
                    "  Consider: Is this a real violation or a constraint issue?"
                ),
                section_content="",
            )

        return self._make_obs(
            reward=step_cost,
            feedback=f"No SDC exceptions found for path '{path_id}'. Path is timed normally.",
            section_content="",
        )

    def _handle_compare_corners(self, action: ChipCycleAction, step_cost: float) -> ChipCycleObservation:
        """
        COMPARE_CORNERS: Compare parameters across PVT corners.

        PVT = Process, Voltage, Temperature. Real chips must work across:
          - SS (slow-slow): worst for setup timing
          - FF (fast-fast): worst for hold timing
          - TT (typical): nominal conditions
        """
        self._accumulated_reward += step_cost

        if self._task["id"] != "signoff_triage":
            return self._make_obs(
                reward=step_cost,
                feedback="Corner comparison only available for sign-off triage task (Task 3).",
                section_content="",
            )

        section = self._task["sections"].get("corner_comparison", "")
        return self._make_obs(
            reward=step_cost,
            feedback="Cross-corner comparison table:",
            section_content=section,
        )

    def _handle_propose_eco(self, action: ChipCycleAction) -> ChipCycleObservation:
        """
        PROPOSE_ECO: Suggest a specific engineering change order.

        ECO = the actual fix that gets applied to the design before tapeout.
        This action tests if the agent can not only FIND issues but also FIX them.

        Valid ECO types:
          - cell_upsize:          Make a slow cell bigger/faster
          - buffer_insert:        Add buffers to fix fanout/transition
          - constraint_update:    Fix SDC constraints (false paths, etc.)
          - cell_swap_vt:         Swap to different threshold voltage cell
          - pipeline_insert:      Add a pipeline stage to break long paths
          - clock_tree_rebalance: Fix clock skew by rebalancing CTS
          - add_delay_cell:       Insert delay for hold fix
        """
        finding = action.finding
        if not finding:
            return self._make_obs(
                reward=0.0,
                feedback=(
                    "Empty ECO proposal. Use finding dict with: "
                    "issue_type (eco_type), location, severity, root_cause, recommended_fix"
                ),
                section_content="",
            )

        eco_type = finding.get("issue_type", "").lower()
        valid_ecos = [
            "cell_upsize", "buffer_insert", "constraint_update", "cell_swap_vt",
            "pipeline_insert", "clock_tree_rebalance", "add_delay_cell",
        ]

        if eco_type not in valid_ecos:
            return self._make_obs(
                reward=-0.02,
                feedback=f"Unknown ECO type: '{eco_type}'. Valid: {valid_ecos}",
                section_content="",
            )

        # Grade the ECO against known issues
        reward, matched_id, feedback = grade_finding(
            finding=finding,
            real_issues=self._task["issues"],
            red_herrings=self._task.get("red_herrings", []),
            already_found=self._found_issue_ids,
        )

        # Bonus for specific, actionable fix descriptions
        fix_text = finding.get("recommended_fix", "").lower()
        specific_keywords = [
            "upsize", "buffer", "pipeline", "cla", "kogge", "delay cell",
            "rebalance", "constraint", "false_path", "set_false",
        ]
        if any(kw in fix_text for kw in specific_keywords):
            reward += 0.05
            feedback += " | ECO specificity bonus: +0.05"

        # Update tracking
        if matched_id:
            self._found_issue_ids.append(matched_id)
            self._state.issues_found = len(self._found_issue_ids)
        if reward < 0 and not matched_id:
            self._false_positives += 1
            self._state.false_positives = self._false_positives

        self._accumulated_reward += reward
        self._findings.append({**finding, "_eco": True})
        self._state.current_score = compute_episode_score(
            self._found_issue_ids, self._false_positives,
            self._state.total_issues, self._accumulated_reward, self._state.difficulty,
        )

        return self._make_obs(reward=reward, feedback=f"ECO: {feedback}", section_content="")

    def _handle_submit_finding(self, action: ChipCycleAction) -> ChipCycleObservation:
        """
        SUBMIT_FINDING: Report a discovered design issue.

        The agent says: "I found a bug. Here's what it is, where it is,
        how severe it is, why it happened, and how to fix it."

        Grading:
          +0.15  → Correctly matched a real planted issue
          +0.05  → Severity rating matches expected
          +0.10  → Fix recommendation is relevant
          -0.10  → FALSE POSITIVE (flagged a red herring or non-issue)
          -0.05  → Duplicate (already reported this)
        """
        finding = action.finding
        if not finding:
            return self._make_obs(
                reward=0.0,
                feedback=(
                    "Empty finding. Provide dict with: "
                    "issue_type, location, severity, root_cause, recommended_fix"
                ),
                section_content="",
            )

        # Grade this finding against the real planted issues
        reward, matched_id, feedback = grade_finding(
            finding=finding,
            real_issues=self._task["issues"],
            red_herrings=self._task.get("red_herrings", []),
            already_found=self._found_issue_ids,
        )

        # Update tracking
        if matched_id:
            self._found_issue_ids.append(matched_id)
            self._state.issues_found = len(self._found_issue_ids)
        if reward < 0 and not matched_id:
            self._false_positives += 1
            self._state.false_positives = self._false_positives

        self._accumulated_reward += reward
        self._findings.append(finding)
        self._state.current_score = compute_episode_score(
            self._found_issue_ids, self._false_positives,
            self._state.total_issues, self._accumulated_reward, self._state.difficulty,
        )

        return self._make_obs(reward=reward, feedback=feedback, section_content="")

    def _handle_submit_review(self, action: ChipCycleAction) -> ChipCycleObservation:
        """
        SUBMIT_REVIEW: Final tapeout recommendation.

        This ENDS the episode. The agent says:
          "Based on my review, this design is GO / NO-GO for tapeout.
           Here are the blocking issues: [...]"

        For the hard task, the correct answer is NO-GO (there are
        blocking issues: setup violations + power budget exceeded).
        """
        review = action.review or {}

        # Grade the review
        review_reward, review_feedback = grade_review(
            review=review,
            real_issues=self._task["issues"],
            found_issue_ids=self._found_issue_ids,
            task_difficulty=self._state.difficulty,
        )
        self._accumulated_reward += review_reward

        # Compute final score
        final_score = compute_episode_score(
            self._found_issue_ids, self._false_positives,
            self._state.total_issues, self._accumulated_reward, self._state.difficulty,
        )

        self._state.current_score = final_score
        self._state.is_done = True

        return ChipCycleObservation(
            done=True,
            reward=review_reward,
            task_id=self._state.task_id,
            task_description=self._task["description"],
            difficulty=self._state.difficulty,
            report_overview="",
            section_content="",
            available_sections=[],
            findings_submitted=self._findings,
            feedback=(
                f"EPISODE COMPLETE | {review_feedback} | "
                f"Final Score: {final_score:.4f} | "
                f"Issues: {len(self._found_issue_ids)}/{self._state.total_issues} | "
                f"False Positives: {self._false_positives}"
            ),
            step_number=self._state.step_count,
            max_steps=self._task["max_steps"],
        )

    # ══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _make_obs(self, reward: float, feedback: str, section_content: str) -> ChipCycleObservation:
        """Build a standard observation. Handles max-step termination."""
        if self._state.step_count >= self._task["max_steps"]:
            self._state.is_done = True
            self._state.current_score = compute_episode_score(
                self._found_issue_ids, self._false_positives,
                self._state.total_issues, self._accumulated_reward, self._state.difficulty,
            )
            feedback += f" | MAX STEPS REACHED. Final score: {self._state.current_score:.4f}"

        return ChipCycleObservation(
            done=self._state.is_done,
            reward=reward,
            task_id=self._state.task_id,
            task_description=self._task["description"],
            difficulty=self._state.difficulty,
            report_overview=self._task["overview"] if self._state.step_count <= 1 else "",
            section_content=section_content,
            available_sections=list(self._task["sections"].keys()),
            findings_submitted=self._findings,
            feedback=feedback,
            step_number=self._state.step_count,
            max_steps=self._task["max_steps"],
        )

    def _error_obs(self, msg: str) -> ChipCycleObservation:
        """Return an error observation (environment not ready)."""
        return ChipCycleObservation(done=False, reward=0.0, feedback=msg)

    def _done_obs(self, msg: str) -> ChipCycleObservation:
        """Return a done observation (episode already finished)."""
        score = self._state.current_score if self._state else 0.0
        return ChipCycleObservation(done=True, reward=0.0, feedback=f"{msg} Final score: {score:.4f}")
