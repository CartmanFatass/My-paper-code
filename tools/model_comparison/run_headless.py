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
            session_id: str) -> list[str]:
    if arm == "claude":
        return [executable, "--print", "--model", "opus", "--effort", "high",
                "--output-format", "stream-json", "--verbose", "--session-id", session_id,
                "--safe-mode", "--tools", "Read,Write,Edit,Bash,Grep,Glob",
                "--permission-mode", "bypassPermissions"]
    if arm == "grok":
        return [executable, "--model", "grok-4.6", "--reasoning-effort", "high",
                "--cwd", str(cwd), "--prompt-file", str(prompt),
                "--session-id", session_id, "--output-format", "streaming-json",
                "--no-plan", "--no-subagents", "--permission-mode", "bypassPermissions"]
    if arm == "omp":
        return [executable, "--print", "--model", MODELS[arm][1], "--thinking", "high",
                "--cwd", str(cwd), "--mode", "json", "--no-prewalk", "--no-title",
                "--no-extensions", "--no-skills", "--no-rules", "--no-lsp", "--no-pty",
                "--tools", "read,bash,edit,write,grep,glob", "--auto-approve",
                "--session-dir", str(output / "sessions"), "@" + str(prompt)]
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
        timeout_seconds: int) -> dict:
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
    if dirty:
        raise ValueError("Comparison worktree has starting modifications or untracked files")
    changed = subprocess.check_output(
        ["git", "-C", str(cwd), "diff", "--name-only", source_sha, "--"], text=True)
    if changed:
        raise ValueError(f"Wrong starting source content relative to {source_sha}")
    executable = shutil.which(MODELS[arm][0])
    if not executable:
        raise FileNotFoundError(f"CLI unavailable: {MODELS[arm][0]}")
    output.mkdir(parents=True, exist_ok=False)
    session_id = str(uuid4())
    argv = command(arm, executable, cwd, prompt, output, session_id)
    record = {
        "arm": arm, "requested_model": MODELS[arm][1], "requested_effort": "high",
        "session_id_argument": session_id if arm != "omp" else None,
        "cwd": str(cwd), "source_sha": source_sha, "actual_head": head,
        "starting_worktree_clean": True, "source_content_matches": True,
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
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    result = run(args.arm, args.cwd, args.prompt, args.out, args.source_sha, args.timeout_seconds)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "exited" and result["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
