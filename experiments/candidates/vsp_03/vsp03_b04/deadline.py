"""B04 terminal publication inside deadline.sh containment; no supervisor edits."""
import os
import time
import argparse
import ctypes
import json
import signal
import subprocess
from pathlib import Path


def direct_children():
    return [int(pid) for pid in Path(
        f"/proc/{os.getpid()}/task/{os.getpid()}/children").read_text().split()]


def clean_children(until):
    killed, reaped = [], []
    while time.perf_counter() < until:
        children = direct_children()
        if not children:
            return killed, reaped, []
        for pid in children:
            try:
                os.kill(pid, signal.SIGKILL)
                killed.append(pid)
            except ProcessLookupError:
                pass
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if pid == 0:
                break
            reaped.append({"pid": pid, "wait_status": status})
        time.sleep(0.005)
    return killed, reaped, direct_children()


def run(args):
    # Map the supervisor's single pre-start wall timestamp once to this monotonic
    # clock. Sampling wall after monotonic makes the conversion conservative.
    observed_monotonic = time.perf_counter()
    observed_unix = time.time()
    started = observed_monotonic - (observed_unix - args.start_wall)
    deadline = started + args.cap
    work_until = deadline - args.reserve
    cleanup_until = deadline - 2.0
    child = None
    timed_out = False
    error = None
    root_returncode = None
    try:
        # Adopt orphaned descendants so a normal nonzero root exit cannot hide them.
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
            raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER")
        os.environ["VSP03_B04_STARTED"] = str(started)
        if time.perf_counter() >= work_until:
            timed_out = True
        else:
            # Keep the inherited timeout process group: no setsid/new session.
            child = subprocess.Popen(args.command)
            try:
                root_returncode = child.wait(timeout=max(0, work_until - time.perf_counter()))
            except subprocess.TimeoutExpired:
                timed_out = True
    except Exception as exc:
        error = repr(exc)
    finally:
        if child is not None and child.returncode is None:
            child.kill()
            try:
                child.wait(timeout=max(0, cleanup_until - time.perf_counter()))
            except subprocess.TimeoutExpired:
                error = "root did not terminate within shutdown reserve"
        if child is not None:
            root_returncode = child.returncode
        killed, reaped, remaining = clean_children(cleanup_until)

    code = 124 if timed_out else (125 if error else root_returncode)
    if remaining or code is None:
        code = 125
    if code < 0:
        code = 128 - code
    record = {"object": "VSP03_B04", "command": args.command, "cwd": os.getcwd(),
        "started_unix_s": args.start_wall, "started_monotonic": started,
        "observed_unix_s": observed_unix, "observed_monotonic": observed_monotonic, "deadline_monotonic": deadline,
        "cap_s": args.cap, "shutdown_publication_reserve_s": args.reserve,
        "root_returncode": root_returncode, "task_exit_code": code,
        "timed_out": timed_out, "error": error,
        "descendants_killed": killed, "descendants_reaped": reaped,
        "descendants_remaining": remaining, "all_descendants_terminated": not remaining,
        "elapsed_before_terminal_publication_s": time.perf_counter() - started}
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    assert json.loads(args.record.read_text(encoding="utf-8")) == record
    print(json.dumps({"terminal_published": str(args.record), "task_exit_code": code,
        "all_descendants_terminated": not remaining,
        "elapsed_through_terminal_readback_s": time.perf_counter() - started}), flush=True)
    if remaining:
        # Do not release the outer containment while any descendant survives.
        time.sleep(max(0, deadline - time.perf_counter()) + 1)
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-wall", type=int, required=True)
    parser.add_argument("--cap", type=float, required=True)
    parser.add_argument("--reserve", type=float, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    if not 2 < args.reserve < args.cap <= 120:
        parser.error("reserve must exceed2s and stay inside the complete cap<=120s")
    raise SystemExit(run(args))
