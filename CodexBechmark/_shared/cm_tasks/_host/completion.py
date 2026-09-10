"""One-shot completion for an already-open CM session; no second CM or scheduler."""
import argparse
from contextlib import closing
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

from . import runtime


def detach(directory, state):
    if state.get("finalizer"):
        return
    command = [sys.executable, "-B", str(Path(state["runtime_dir"]) / "runner.py"),
               "finalize", "--run", str(directory)]
    options = {"start_new_session": True} if os.name != "nt" else {
        "creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}
    with (directory / "finalizer.log").open("a", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   cwd=directory, **options)
    state["finalizer"] = {"pid": process.pid, "started": runtime.now(), "status": "waiting_for_cm_turn"}
    runtime.save(directory / "state.json", state)


def closed_turn(state):
    """Read actual terminal events; never infer completion from a candidate assertion."""
    home = Path(state["launch"]["codex_home"])
    db = home / "state_5.sqlite"
    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        row = connection.execute("SELECT rollout_path,source FROM threads WHERE id=?",
                                 (state["launch"]["session_id"],)).fetchone()
    if not row:
        return "waiting"
    try:
        source = json.loads(row[1])
    except (TypeError, ValueError):
        source = {}
    if isinstance(source, dict) and source.get("subagent"):
        raise ValueError("CM must be the existing top-level session, not a subagent")
    terminal = "waiting"
    cutoff = datetime.fromisoformat(state["finished"])
    with Path(row[0]).open(encoding="utf-8") as lines:
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = event.get("payload", {})
            if event.get("type") != "event_msg" or payload.get("type") not in ("task_complete", "turn_aborted"):
                continue
            stamp = event.get("timestamp")
            if stamp and datetime.fromisoformat(stamp.replace("Z", "+00:00")) >= cutoff:
                terminal = "complete" if payload["type"] == "task_complete" else "aborted"
                break
    return terminal


def report(directory, state, status):
    judgement_file = directory / "judgement.json"
    judgement = json.loads(judgement_file.read_text(encoding="utf-8")) if judgement_file.is_file() else {}
    label = lambda value: "通过" if value is True else "未通过" if value is False else "未完成/无法确认"
    rows = "\n".join(f"- `{task}`：{state['task_metadata'][task]['difficulty']}（预估）" for task in state["tasks"])
    content = (f"# CM benchmark {state['id']}\n\n自动收尾状态：{status}\n\n抽题 seed：`{state['seed']}`。本轮两题：\n\n{rows}\n\n"
        f"行为检查：{label(judgement.get('behavior_passed'))}；流程产物：{label(judgement.get('protocol_artifacts_passed'))}；"
        f"完整判定：{label(judgement.get('full_run_passed'))}。\n\n"
        "- [逐题与流程评分](judgement.json)\n- [实际会话与配置](export.json)\n"
        "- [独立裁判](assessment/report.json)\n- [CM 团队成本原始报告](cost/team.md)\n"
        "- [独立裁判成本原始报告](cost/evaluator.md)\n- [成本提取状态](cost/status.json)\n\n"
        "费用是冻结 API Standard 费率的参考值，不是订阅额度或实际账单；未处理单请求超长/tier 倍率。"
        "未完成、缺失或 UNPRICED 的项目不能按零费用或通过处理。一次流程不能得出最佳策略。\n")
    (directory / "REPORT.md").write_text(content, encoding="utf-8")


def finalize(directory, state, base):
    status = "waiting_for_cm_turn"
    runtime.save(directory / "finalization.json", {"started": runtime.now(), "status": status})
    try:
        # One bounded helper for this run. It exits; there is no recurring task/service.
        deadline = time.monotonic() + 3600
        while time.monotonic() < deadline:
            try:
                status = closed_turn(state)
            except (sqlite3.Error, OSError):
                status = "waiting"
            if status != "waiting":
                break
            time.sleep(2)
        if status == "waiting":
            raise TimeoutError("CM completion was not observable within one hour; no grader was launched")
        export_args = argparse.Namespace(session=state["launch"]["session_id"], codex_home=state["launch"]["codex_home"])
        runtime.export(export_args, directory, state, base)
        runtime.save(directory / "judgement.json", runtime.judge(directory, state, base))
        if status == "complete":
            runtime.assess(argparse.Namespace(codex=None), directory, state, base)
        cost_args = argparse.Namespace(pricing_json=Path(state["runtime_dir"]) / "_host/pricing.json", script=Path.home() / ".agents/skills/codex-task-cost-analysis/scripts/codex_task_cost_analysis.py")
        runtime.cost(cost_args, directory, state, base)
        status = "finished" if status == "complete" else "cm_aborted_no_model_grader"
        runtime.save(directory / "finalization.json", {"ended": runtime.now(), "status": status})
    except Exception as exc:
        status = "error"
        runtime.save(directory / "finalization.json", {"ended": runtime.now(), "status": status, "error": str(exc)})
    finally:
        current = json.loads((directory / "state.json").read_text(encoding="utf-8"))
        current.setdefault("finalizer", {}).update(status=status, ended=runtime.now())
        runtime.save(directory / "state.json", current)
        report(directory, state, status)
