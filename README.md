# ChipCycle 🔄

**AI Chip Design Sign-off Review Environment**

An OpenEnv-compliant reinforcement learning environment where AI agents learn to review ASIC chip design reports — from synthesis QoR analysis through static timing analysis to multi-corner multi-mode sign-off triage.

> **Why this matters:** A single chip respin costs $5M–$50M. Design review is done manually by engineers reading thousands of lines of reports. ChipCycle trains AI agents to catch what humans miss.

---

## 🎯 Overview

ChipCycle simulates the chip design review process across three stages of the VLSI back-end flow:

| Task | Stage | Difficulty | Issues | Description |
|------|-------|-----------|--------|-------------|
| `synthesis_review` | Post-Synthesis | 🟢 Easy | 4 | Review synthesis QoR report: timing violations, unmapped cells, DRV |
| `sta_debug` | Static Timing Analysis | 🟡 Medium | 5 | Debug STA paths: real vs false violations, hold issues, at-risk paths |
| `signoff_triage` | Multi-Corner Sign-off | 🔴 Hard | 7 + red herrings | Full MCMM triage: setup/hold across PVT corners, CTS, DRC, power |

The agent interacts through a structured action space:
- **Investigate:** `analyze_section`, `check_constraint`, `compare_corners`
- **Diagnose:** `submit_finding` with severity and root cause
- **Fix:** `propose_eco` (cell upsize, buffer insert, constraint update, etc.)
- **Decide:** `submit_review` with tapeout go/no-go recommendation

---

## 📊 Reward Function

| Action | Reward |
|--------|--------|
| Correctly identify a real issue | +0.15 |
| Correct severity rating | +0.05 |
| Actionable fix recommendation | +0.05 to +0.10 |
| Specific ECO proposal | +0.05 bonus |
| False positive (flag valid design) | -0.10 |
| Duplicate finding | -0.05 |
| Each investigation step | -0.02 (time pressure) |

The false-positive penalty is a key design choice: it models the real-world cost of unnecessary ECO iterations, where a wrong flag can cost days of engineering effort.

---

## 🚀 Quick Start

### Local Setup

```bash
# Install dependencies
pip install fastapi uvicorn pydantic httpx openai

# Start the server
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860

# In another terminal, run inference
export OPENAI_API_KEY="your-key"
export MODEL_NAME="gpt-4"
python inference.py
```

### Docker

```bash
docker build -t chipcycle .
docker run -p 7860:7860 chipcycle
```

### HuggingFace Spaces

Deploy as a Docker Space on HuggingFace with the included Dockerfile.

---

## 🔌 API Reference

### `POST /reset`
Start a new episode.
```json
{"task_id": "synthesis_review"}
```

### `POST /step`
Take an action.
```json
{
  "action": {
    "action_type": "analyze_section",
    "section_name": "timing_summary"
  }
}
```

### `GET /state`
Get current episode state (score, issues found, etc.).

### `GET /health`
Health check.

### `GET /tasks`
List available tasks with metadata.

---

## 🏗️ Action Space

```
action_type: str
  ├── "analyze_section"    → section_name: str
  ├── "check_constraint"   → path_id: str
  ├── "compare_corners"    → param, corner_a, corner_b: str
  ├── "propose_eco"        → finding: {issue_type, location, severity, root_cause, recommended_fix}
  │                          ECO types: cell_upsize, buffer_insert, constraint_update,
  │                                     cell_swap_vt, pipeline_insert, clock_tree_rebalance,
  │                                     add_delay_cell
  ├── "submit_finding"     → finding: {issue_type, location, severity, root_cause, recommended_fix}
  └── "submit_review"      → review: {decision: "go"|"no-go", blocking_issues: [...], summary: "..."}
```

## 👁️ Observation Space

```
task_id: str              — Current task identifier
task_description: str     — Human-readable objective
difficulty: str           — easy | medium | hard
report_overview: str      — Full design report overview (on reset)
section_content: str      — Detailed section content (on analyze)
available_sections: [str] — Sections available for analysis
findings_submitted: [{}]  — Agent's findings so far
feedback: str             — Feedback on last action
reward: float             — Reward from last action
done: bool                — Episode finished
step_number: int          — Current step
max_steps: int            — Maximum steps for this task
```

---

## 📁 Project Structure

```
chipcycle/
├── models.py              # Pydantic models: Action, Observation, State
├── client.py              # HTTP client with typed interface
├── inference.py           # Baseline LLM agent (OpenAI API)
├── openenv.yaml           # OpenEnv manifest
├── pyproject.toml         # Python project config
├── Dockerfile             # Container for HF Spaces
├── README.md              # This file
├── __init__.py            # Package exports
└── server/
    ├── __init__.py
    ├── app.py             # FastAPI server (/reset, /step, /state)
    ├── environment.py     # Core environment logic
    ├── tasks.py           # Task definitions + synthetic EDA data
    └── graders.py         # Deterministic grading engine
```

---

## 🌡️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API key for LLM inference | Required for inference |
| `API_BASE_URL` | OpenAI-compatible API endpoint | `https://api.openai.com/v1` |
| `MODEL_NAME` | LLM model name | `gpt-4` |
| `HF_TOKEN` | HuggingFace token | Optional |
| `ENV_URL` | ChipCycle server URL | `http://localhost:7860` |
| `PORT` | Server port | `7860` |

---

## 🧪 Grading Details

### Task 1 — Synthesis QoR Review (Easy)
**Score = 0.80 × detection_rate + 0.20 × precision**

4 issues: timing violation (WNS -0.82ns), unmapped cells (behavioral mux + inferred latch), fanout violations (rst_n_sync overloaded), transition violations (7 nets).

### Task 2 — STA Timing Debug (Medium)
**Score = 0.50 × detection + 0.25 × precision + 0.25 × analysis_quality**

5 issues: ALU setup violation, async FIFO false path (must NOT flag as real), hold violation on synchronizer, at-risk path (20ps slack), multiplier CPA bottleneck.

### Task 3 — MCMM Sign-off Triage (Hard)
**Score = 0.35 × detection + 0.25 × precision + 0.25 × analysis + 0.15 × triage_quality**

7 issues + 2 red herrings: setup violations at SS corners, hold violation at FF corner, clock skew exceeding target, real DRC violations (5), power budget exceeded (14%), OCV-sensitive path. Red herrings: 142 antenna DRCs (waivable), high clk_test insertion delay (expected for scan mode).

---

## 🔬 Research Roadmap

ChipCycle v1.0 uses synthetic reports for reproducibility. The roadmap for research-grade extensions:

### Near-term
1. **Real EDA flow data** — Generate reports using Yosys → OpenROAD → OpenSTA on open PDKs (SKY130, GF180MCU)
2. **Design scenario generator** — Parameterized RTL generator varying clock domains, pipeline depth, PVT corners, and fanout for thousands of training cases
3. **Benchmark dataset** — Release design reports + ground truth violations + expected fixes as a standardized benchmark

### Medium-term
4. **Timing graph representation** — Model designs as directed graphs (cells = nodes, nets = edges) for learning delay propagation and critical path analysis
5. **Multi-agent sign-off** — Separate agents for timing, physical verification, and power analysis coordinated by a sign-off decision agent
6. **Advanced constraint debugging** — Tasks focused on SDC debugging: missing constraints, incorrect multi-cycle paths, complex clock relationships

### Long-term
7. **Visualization tools** — Timing path graphs, clock tree visualizations, congestion heatmaps
8. **GNN baselines** — Compare RL agent with graph neural network approaches for timing prediction
9. **Transfer learning** — Pre-train on synthetic reports, fine-tune on proprietary EDA outputs
10. **Curriculum learning** — Progressive difficulty from single-clock designs to complex SoC hierarchies with multiple power domains

---

## 🏭 Industry Context

- **Market:** The EDA tools market is $15B+ annually (Synopsys $60B, Cadence $80B market cap)
- **Cost of bugs:** A single chip respin costs $5M–$50M depending on node
- **Talent gap:** 200,000+ chip designers worldwide, with chronic shortage of sign-off engineers
- **India Semiconductor Mission:** $10B government investment driving massive hiring in chip design
- **AI in EDA:** Google AlphaChip (floorplanning), Synopsys DSO.ai (design optimization), NVIDIA cuLitho (lithography) — sign-off review is the next frontier

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

Built for the Meta PyTorch OpenEnv Hackathon × Scaler School of Technology (2026).
Synthetic design data modeled after PrimeTime, Design Compiler, and ICC2 report formats.
