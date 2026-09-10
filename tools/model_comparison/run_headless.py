"""Run one explicitly assigned CM comparison arm; never select tasks or retry them."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from datetime import datetime, timezone
from uuid import uuid4


MODELS = {
    "claude": ("claude", "opus", "high"),
    "grok": ("grok", "grok-4.6", "high"),
    "omp": ("omp", "google-antigravity/gemini-3.8-flash-high", "high"),
}


def command(arm: str, executable: str, cwd: Path, prompt: Path, output: Path,
            session_id: str, resume: bool = False, session_dir: Path | None = None) -> list[str]:
    session_flag = "--resume" if resume else "--session-id"
    if arm == "claude":
        return [executable, "--print", "--model", "opus", "--effort", "high",
                "--output-format", "stream-json", "--verbose", session_flag, session_id,
                "--safe-mode", "--tools", "Read,Write,Edit,Bash,Grep,Glob",
                "--permission-mode", "bypassPermissions"]
    if arm == "grok":
        return [executable, "--model", "grok-4.6", "--reasoning-effort", "high",
                "--cwd", str(cwd), "--prompt-file", str(prompt),
                session_flag, session_id, "--output-format", "streaming-json",
                "--no-plan", "--no-subagents", "--permission-mode", "bypassPermissions"]
    if arm == "omp":
        return [executable, "--print", "--model", MODELS[arm][1], "--thinking", "high",
                "--cwd", str(cwd), "--mode", "json", "--no-prewalk", "--no-title",
                "--no-extensions", "--no-skills", "--no-rules", "--no-lsp", "--no-pty",
                "--tools", "read,bash,edit,write,grep,glob", "--auto-approve",
                "--session-dir", str(session_dir or output / "sessions"),
                *(["--resume", session_id] if resume else []), "@" + str(prompt)]
    raise ValueError(f"Unknown comparison arm: {arm}")


def stop_process_tree(process: subprocess.Popen) -> None:
    # Only the process created by this invocation and its children are terminated.
    if os.name == "nt":
        result = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Termination unconfirmed for PID {process.pid}: taskkill exit {result.returncode}")
    else:
        import signal
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=10)


def run(arm: str, cwd: Path, prompt: Path, output: Path, source_sha: str,
        timeout_seconds: int, resume_from: Path | None = None) -> dict:
    cwd, prompt, output = cwd.resolve(), prompt.resolve(), output.resolve()
    payload = prompt.read_bytes()
    payload.decode("utf-8")
    if b"\r" in payload:
        raise ValueError("Comparison prompt must be UTF-8 LF, with no CR bytes")
    head = subprocess.check_output(["git", "-C", str(cwd), "rev-parse", "HEAD"],
                                   text=True).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(cwd), "status", "--porcelain=v1", "--untracked-files=all"],
        text=True)
    previous = json.loads(resume_from.read_text(encoding="utf-8")) if resume_from else None
    if resume_from is not None and not previous:
        raise ValueError("Missing session record; cannot resume as a new conversation")
    if previous:
        if (previous["arm"] != arm or Path(previous["cwd"]).resolve() != cwd
                or previous["source_sha"] != source_sha):
            raise ValueError("Resume must keep the original arm, worktree and source binding")
        if previous["status"] != "exited" or previous["exit_code"] is None:
            raise ValueError("Resolve prior process/session state before resuming")
        if not previous.get("resume_target"):
            raise ValueError("No exact saved session target; inspect original session evidence")
    if dirty and not previous:
        raise ValueError("Comparison worktree has starting modifications or untracked files")
    changed = "" if previous else subprocess.check_output(
        ["git", "-C", str(cwd), "diff", "--name-only", source_sha, "--"], text=True)
    if changed:
        raise ValueError(f"Wrong starting source content relative to {source_sha}")
    executable = shutil.which(MODELS[arm][0])
    if not executable:
        raise FileNotFoundError(f"CLI unavailable: {MODELS[arm][0]}")
    output.mkdir(parents=True, exist_ok=False)
    session_id = previous["resume_target"] if previous else str(uuid4())
    session_dir = Path(previous["session_dir"]) if previous else output / "sessions"
    argv = command(arm, executable, cwd, prompt, output, session_id,
                   resume=bool(previous), session_dir=session_dir)
    record = {
        "arm": arm, "requested_model": MODELS[arm][1], "requested_effort": "high",
        "session_id_argument": session_id if arm != "omp" else None,
        "resume_target": session_id if arm != "omp" or previous else None,
        "session_dir": str(session_dir), "session_mode": "resume" if previous else "new",
        "previous_receipt": str(resume_from.resolve()) if resume_from else None,
        "turn_number": previous.get("turn_number", 1) + 1 if previous else 1,
        "cwd": str(cwd), "source_sha": source_sha, "actual_head": head,
        "starting_worktree_clean": not bool(dirty),
        "starting_worktree_status": dirty, "source_content_matches": None if previous else True,
        "prompt_path": str(prompt), "argv": argv,
        "started_at": datetime.now(timezone.utc).isoformat(), "pid": None,
        "status": "starting", "timeout_seconds": timeout_seconds,
        "exit_code": None, "elapsed_seconds": None,
        "resolved_model": None, "model_verification": "read_raw_session_before_acceptance",
        "quality": "not_assessed", "tokens": "not_requested_for_this_provider",
    }
    receipt = output / "process.json"
    receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    started = time.monotonic()
    try:
        with (output / "stdout.jsonl").open("wb") as stdout, \
                (output / "stderr.log").open("wb") as stderr:
            kwargs = {"start_new_session": True} if os.name != "nt" else {
                "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            }
            process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE,
                                       stdout=stdout, stderr=stderr, **kwargs)
            record.update(pid=process.pid, status="running")
            receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            try:
                process.communicate(input=payload if arm == "claude" else b"",
                                    timeout=timeout_seconds)
                record["status"] = "exited"
            except subprocess.TimeoutExpired:
                record["status"] = "administrative_timeout"
                try:
                    stop_process_tree(process)
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                    record.update(status="termination_unconfirmed", error=str(error))
            record["exit_code"] = process.returncode
    except OSError as error:
        record.update(status="start_or_process_error", error=str(error))
    finally:
        record.update(ended_at=datetime.now(timezone.utc).isoformat(),
                      elapsed_seconds=time.monotonic() - started)
        if arm == "omp" and not previous:
            sessions = list(session_dir.rglob("*.jsonl"))
            if len(sessions) == 1:
                record["resume_target"] = str(sessions[0].resolve())
        record["cumulative_elapsed_seconds"] = record["elapsed_seconds"] + (
            previous.get("cumulative_elapsed_seconds", previous["elapsed_seconds"]) if previous else 0)
        receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=MODELS, required=True)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--timeout-seconds", type=int, required=True)
    parser.add_argument("--resume-from", type=Path, help="Previous turn process.json; reuse exact session and worktree")
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    result = run(args.arm, args.cwd, args.prompt, args.out, args.source_sha,
                 args.timeout_seconds, args.resume_from)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "exited" and result["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
