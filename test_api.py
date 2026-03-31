import subprocess
import time
import httpx
import sys

def test_api():
    print("Starting server process...")
    proc = subprocess.Popen(
        ["/Users/yash/SCALER/venv/bin/python3", "-m", "uvicorn", "server.app:app", "--host", "127.0.0.1", "--port", "7860"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give it a few seconds to start
    time.sleep(4)
    
    # Check if process is still running
    if proc.poll() is not None:
        out, err = proc.communicate()
        print("Server failed to start!")
        print("STDOUT:", out.decode())
        print("STDERR:", err.decode())
        sys.exit(1)
        
    try:
        B = "http://127.0.0.1:7860"
        
        # 1) Health
        health_resp = httpx.get(f"{B}/health", timeout=5).json()
        print(f"1. Health: {health_resp['status']}")
        
        # 2) Tasks
        tasks_resp = httpx.get(f"{B}/tasks", timeout=5).json()["tasks"]
        print(f"2. Tasks: {len(tasks_resp)} available")
        
        # 3) Reset (Easy task)
        reset_resp = httpx.post(f"{B}/reset", json={"task_id": "synthesis_review"}, timeout=5).json()["observation"]
        print(f"3. Reset: {reset_resp['task_id']}, sections: {reset_resp['available_sections']}")
        
        # 4) Step - Analyze section
        step_analyze = httpx.post(f"{B}/step", json={
            "action": {"action_type": "analyze_section", "section_name": "timing_summary"}
        }, timeout=5).json()["observation"]
        print(f"4. Analyze: reward={step_analyze['reward']:.3f}")
        
        # 5) Step - Submit valid ECO
        step_eco = httpx.post(f"{B}/step", json={
            "action": {
                "action_type": "propose_eco",
                "finding": {
                    "issue_type": "cell_upsize",
                    "location": "WNS -0.82ns critical path",
                    "severity": "critical",
                    "root_cause": "18 levels of logic",
                    "recommended_fix": "Pipeline insertion"
                }
            }
        }, timeout=5).json()["observation"]
        print(f"5. Propose ECO: reward={step_eco['reward']:.3f}, feedback={step_eco['feedback'][:70]}...")
        
        # 6) Step - Submit review
        step_review = httpx.post(f"{B}/step", json={
            "action": {
                "action_type": "submit_review",
                "review": {
                    "decision": "no-go",
                    "blocking_issues": ["timing"],
                    "summary": "Fix timing first"
                }
            }
        }, timeout=5).json()["observation"]
        print(f"6. Submit Review: done={step_review['done']}")
        
        # 7) State
        state = httpx.get(f"{B}/state", timeout=5).json()["state"]
        print(f"7. Final State: score={state['current_score']:.4f}, issues={state['issues_found']}/{state['total_issues']}")
        
        print("\n✅ FULL API TEST PASSED")
        
    except Exception as e:
        print(f"\n❌ API Test Failed: {e}")
        sys.exit(1)
    finally:
        print("Shutting down server...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_api()
