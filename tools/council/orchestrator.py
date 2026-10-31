"""
ChatDev-Style Council Orchestrator for Rogue2D
Coordinates autonomous cyclical development across specialized roles:
Designer -> Engineer -> Validator (Zero-Token QA) -> Harsh Critic -> Checkpoint

Usage:
  python tools/council/orchestrator.py status
  python tools/council/orchestrator.py active-task
  python tools/council/orchestrator.py diff
  python tools/council/orchestrator.py verify
  python tools/council/orchestrator.py advance
  python tools/council/orchestrator.py checkpoint
  python tools/council/orchestrator.py next
"""

import os
import sys
import json
import subprocess

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

COUNCIL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(COUNCIL_DIR))
BACKLOG_PATH = os.path.join(COUNCIL_DIR, "backlog.json")

def load_backlog():
    if not os.path.exists(BACKLOG_PATH):
        return {"current_task_id": None, "tasks": []}
    with open(BACKLOG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_backlog(data):
    with open(BACKLOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_current_task(backlog):
    tid = backlog.get("current_task_id")
    for t in backlog.get("tasks", []):
        if t["id"] == tid:
            return t
    return None

def get_git_diff():
    res = subprocess.run(["git", "diff", "--stat"], cwd=PROJECT_ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    stat_summary = res.stdout.strip()
    res_diff = subprocess.run(["git", "diff"], cwd=PROJECT_ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    full_diff = res_diff.stdout.strip()
    return stat_summary, full_diff

def run_local_validation():
    val_script = os.path.join(COUNCIL_DIR, "validator.py")
    venv_candidates = [
        os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe"),
    ]
    py_exec = next((candidate for candidate in venv_candidates if os.path.exists(candidate)), sys.executable)
    res = subprocess.run([py_exec, val_script], cwd=PROJECT_ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    try:
        return json.loads(res.stdout)
    except Exception:
        return {"overall_status": "FAIL", "details": res.stderr or res.stdout}

def cmd_status():
    backlog = load_backlog()
    current = get_current_task(backlog)
    print("=" * 60)
    print("  ROGUE 2D: COUNCIL ORCHESTRATOR STATUS")
    print("=" * 60)
    if current:
        print(f"Active Task: [{current['id']}] {current['title']}")
        print(f"Status:      {current['status']}")
        print(f"Assigned To: {current.get('assigned_to', 'engineer').upper()}")
        print(f"Priority:    {current.get('priority', 'MEDIUM')}")
        print(f"AC Items:    {len(current.get('acceptance_criteria', []))} criteria")
    else:
        print("No active task. All tasks completed or unassigned.")

    print("\nBacklog Overview:")
    for t in backlog.get("tasks", []):
        marker = "->" if current and t["id"] == current["id"] else "  "
        print(f"{marker} [{t['status']:<11}] {t['id']}: {t['title']}")
    print("=" * 60)

def cmd_diff():
    stat, full = get_git_diff()
    print("=" * 60)
    print("  CURRENT TASK GIT DIFF (TOKEN-EFFICIENT VIEW)")
    print("=" * 60)
    if not stat:
        print("No uncommitted changes.")
    else:
        print(stat)
        print("-" * 60)
        # Limit diff output to prevent token bloating
        lines = full.splitlines()
        if len(lines) > 200:
            print("\n".join(lines[:200]))
            print(f"\n... [Truncated: {len(lines) - 200} lines omitted for token economy] ...")
        else:
            print(full)
    print("=" * 60)

def cmd_verify():
    print("[Council QA] Running zero-token local verification...")
    result = run_local_validation()
    status = result.get("overall_status", "FAIL")
    print(f"Result: [{status}]")
    print(f"Details: {result.get('details', '')}")
    return 0 if status == "PASS" else 1

def cmd_advance():
    backlog = load_backlog()
    current = get_current_task(backlog)
    if not current:
        print("No active task to advance.")
        return 1

    status_transitions = {
        "TODO": "IN_PROGRESS",
        "IN_PROGRESS": "TESTING",
        "TESTING": "REVIEW",
        "REVIEW": "DONE"
    }
    old_status = current.get("status", "TODO")
    new_status = status_transitions.get(old_status)
    if not new_status:
        print(f"Task is already {old_status}.")
        return 0

    if new_status in ["REVIEW", "DONE"]:
        val = run_local_validation()
        if val.get("overall_status") != "PASS":
            print(f"[REJECTED] Cannot advance to {new_status}: Local validation failed!")
            print(val.get("details"))
            return 1

    current["status"] = new_status
    save_backlog(backlog)
    print(f"[Council SOP] Task [{current['id']}] advanced: {old_status} -> {new_status}")
    return 0

def cmd_checkpoint():
    backlog = load_backlog()
    current = get_current_task(backlog)
    if not current:
        print("No active task to checkpoint.")
        return 1

    val = run_local_validation()
    if val.get("overall_status") != "PASS":
        print("[REJECTED] Cannot checkpoint: Tests are failing!")
        return 1

    msg = f"[Council: {current['id']}] {current['title']}"
    subprocess.run(["git", "add", "."], cwd=PROJECT_ROOT)
    res = subprocess.run(["git", "commit", "-m", msg], cwd=PROJECT_ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(f"[Git Checkpoint] Created commit: {msg}")
    print(res.stdout.strip())
    current["status"] = "DONE"
    save_backlog(backlog)
    return 0

def cmd_next():
    backlog = load_backlog()
    for t in backlog.get("tasks", []):
        if t["status"] in ["TODO", "IN_PROGRESS"]:
            backlog["current_task_id"] = t["id"]
            save_backlog(backlog)
            print(f"[Council SOP] Switched to task: [{t['id']}] {t['title']}")
            return 0
    print("All tasks in backlog are DONE!")
    return 0

def main():
    if len(sys.argv) < 2:
        cmd_status()
        return

    action = sys.argv[1].lower()
    if action == "status":
        cmd_status()
    elif action == "diff":
        cmd_diff()
    elif action == "verify":
        sys.exit(cmd_verify())
    elif action == "advance":
        sys.exit(cmd_advance())
    elif action == "checkpoint":
        sys.exit(cmd_checkpoint())
    elif action == "next":
        sys.exit(cmd_next())
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
