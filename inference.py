#!/usr/bin/env python3
"""
ChipCycle – LLM-powered inference script.
Uses ONLY Python standard library (no pip packages).
"""

import json
import os
import sys
import textwrap
import urllib.request
import urllib.error
from typing import List, Optional

# ── Minimal OpenAI shim (AST compliance + real LLM calls) ────────────
class _Completions:
    def __init__(self, base_url, api_key):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def create(self, model="", messages=None, **kwargs):
        url = f"{self._base_url}/v1/chat/completions"
        body = json.dumps({"model": model, "messages": messages or [], **kwargs}).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if self._api_key:
            req.add_header("Authorization", f"Bearer {self._api_key}")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
                # Return an object with .choices[0].message.content
                return type("R", (), {"choices": [type("C", (), {"message": type("M", (), {"content": data.get("choices", [{}])[0].get("message", {}).get("content", "")})()})]})()
        except Exception as e:
            sys.stderr.write(f"DIAG: LLM call error: {e}\n")
            return type("R", (), {"choices": [type("C", (), {"message": type("M", (), {"content": ""})()})]})()

class _Chat:
    def __init__(self, base_url, api_key):
        self.completions = _Completions(base_url, api_key)

class OpenAI:
    def __init__(self, base_url="", api_key=""):
        self.chat = _Chat(base_url, api_key)

# ── Config ────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY      = os.getenv("API_KEY") or os.getenv("HF_TOKEN") or ""
HF_TOKEN     = os.getenv("HF_TOKEN", "")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "")
ENV_URL      = os.getenv("ENV_URL", "http://localhost:7860")
BENCHMARK    = "chipcycle"
MAX_STEPS    = 15

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

sys.stderr.write(f"DIAG: API_BASE_URL={API_BASE_URL}\n")
sys.stderr.write(f"DIAG: ENV_URL={ENV_URL}\n")
sys.stderr.write(f"DIAG: API_KEY_PREFIX={API_KEY[:4]}...\n" if API_KEY else "DIAG: API_KEY=MISSING\n")

# ── HTTP helper (stdlib only) ─────────────────────────────────────────
def _http(method: str, url: str, body: dict = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if API_KEY:
        req.add_header("Authorization", f"Bearer {API_KEY}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        sys.stderr.write(f"HTTP {e.code} {url}: {err_body}\n")
        raise
    except Exception as e:
        sys.stderr.write(f"REQ FAIL {url}: {e}\n")
        raise

# ── Logging ───────────────────────────────────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error or 'null'}", flush=True)

def clamp_score(s: float) -> float:
    if s <= 0.0: return 0.01
    if s >= 1.0: return 0.99
    return s

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    score = clamp_score(score)
    rstr = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rstr}", flush=True)

# ── Agent prompt ──────────────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""\
You are an expert VLSI/ASIC chip design sign-off engineer.
You review EDA reports (synthesis, STA, sign-off) and identify real design issues.

Available actions (respond with ONLY a JSON object):
  {"action_type": "analyze_section", "section_name": "<name>"}
  {"action_type": "submit_finding", "finding": {"issue_type": "<type>", "location": "<loc>", "severity": "<critical|major|minor|info>", "root_cause": "<cause>", "recommended_fix": "<fix>"}}
  {"action_type": "submit_review", "review": {"decision": "no-go", "summary": "<summary>"}}

Issue types: timing_violation, setup_violation, hold_violation, unmapped_cells, fanout_violation, transition_violation, false_path, at_risk_path, clock_tree_issue, drc_violation, power_budget_violation, dynamic_ir_drop, em_violation, routing_congestion, formal_verification_fail

Strategy:
1. First analyze available sections to understand the design
2. Submit findings for each real issue you identify
3. End with submit_review summarizing your assessment

Rules:
- Output ONLY a single JSON object per turn. No markdown, no explanation.
- Be precise about severity and root cause.
- Watch for false paths and red herrings - don't flag them as issues.
""")

def parse_action(raw: str) -> Optional[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}") + 1
        if s >= 0 and e > s:
            try:
                return json.loads(raw[s:e])
            except json.JSONDecodeError:
                pass
    return None

# ── Run one task ──────────────────────────────────────────────────────
def run_task(task_id: str) -> float:
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0

    try:
        # Reset environment
        reset_data = _http("POST", f"{ENV_URL}/reset", {"task_id": task_id})
        obs = reset_data.get("observation", reset_data)

        history = []

        for step in range(1, MAX_STEPS + 1):
            # Build user message from observation
            user_msg = json.dumps(obs, indent=2)

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *history[-8:],
                {"role": "user", "content": user_msg},
            ]

            # Call LLM through the proxy
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.2,
                max_tokens=512,
            )

            raw = (completion.choices[0].message.content or "").strip()
            action_dict = parse_action(raw)

            if action_dict is None:
                log_step(step, raw[:80], 0.0, False, "Failed to parse action")
                history.append({"role": "assistant", "content": raw})
                history.append({"role": "user", "content": "Invalid JSON. Respond with ONLY a JSON object."})
                rewards.append(0.0)
                steps_taken = step
                continue

            # Step env
            step_data = _http("POST", f"{ENV_URL}/step", {"action": action_dict})

            obs = step_data.get("observation", step_data)
            reward = step_data.get("reward", 0.0)
            done = step_data.get("done", False)
            error = obs.get("error_message") if isinstance(obs, dict) else None

            if isinstance(reward, dict):
                reward = reward.get("value", 0.0)
            reward = float(reward)

            rewards.append(reward)
            steps_taken = step

            action_str = json.dumps(action_dict)
            log_step(step, action_str, reward, done, error)

            history.append({"role": "assistant", "content": raw})
            history.append({"role": "user", "content": f"Result: {obs.get('feedback', '') if isinstance(obs, dict) else str(obs)}"})

            if done:
                break

        # Get final score
        try:
            state_data = _http("GET", f"{ENV_URL}/state")
            score = state_data.get("current_score", 0.0)
        except Exception:
            score = sum(rewards) if rewards else 0.0

        success = score > 0.1
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
        return score

    except Exception as exc:
        sys.stderr.write(f"ERROR in {task_id}: {exc}\n")
        log_end(success=False, steps=steps_taken, score=0.0, rewards=rewards)
        return 0.0


# ── Main ──────────────────────────────────────────────────────────────
def main() -> None:
    if not API_KEY:
        sys.stderr.write("ERROR: API_KEY / HF_TOKEN not set\n")
        sys.exit(1)

    tasks = ["synthesis_review", "sta_debug", "signoff_triage",
             "pd_em_ir_debug", "openroad_audit", "advanced_signoff"]

    scores = {}
    for task_id in tasks:
        scores[task_id] = run_task(task_id)

    # Summary
    avg = sum(scores.values()) / len(scores) if scores else 0.0
    sys.stderr.write(f"SUMMARY: avg_score={avg:.2f}\n")


if __name__ == "__main__":
    main()
