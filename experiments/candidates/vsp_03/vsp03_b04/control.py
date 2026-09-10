"""B04 one-shot controller, executed inside an already timed systemd unit."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from deadline import clean_children


def run(args):
    # The manager armed TimeoutStartSec before ExecStart, including this lookup.
    properties = subprocess.check_output([
        "systemctl", "--user", "show", args.unit,
        "-p", "InactiveExitTimestampMonotonic", "-p", "TimeoutStartUSec",
        "-p", "Type", "-p", "KillMode", "-p", "TimeoutStartFailureMode",
    ], text=True)
    values = dict(line.split("=", 1) for line in properties.splitlines())
    started = int(values["InactiveExitTimestampMonotonic"]) / 1e6
    deadline = started + args.cap
    cleanup_until = deadline - 2
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER")
    args.record.parent.mkdir(parents=True, exist_ok=True)
    socket_root = args.record.with_suffix(".tmux")
    socket_root.mkdir(mode=0o700)
    os.environ.pop("TMUX", None)
    os.environ["TMUX_TMPDIR"] = str(socket_root)
    os.environ["VSP03_B04_COMMAND"] = shlex.join(args.command)
    payload_record = args.record.with_suffix(".payload.json")
    command = shlex.join([
        args.python, str(Path(__file__).with_name("deadline.py")),
        "--start-monotonic", str(started), "--cap", str(args.cap),
        "--reserve", str(args.reserve), "--record", str(payload_record),
        "--", *args.command,
    ])
    receipt = args.task_dir / args.name / "exit_code"
    error, supervisor_code = None, None
    try:
        launch = subprocess.run([args.supervisor, "run", args.name, command],
                                timeout=max(.001, cleanup_until - time.monotonic()))
        if launch.returncode:
            error = f"agent-task launch exit {launch.returncode}"
        else:
            while time.monotonic() < cleanup_until:
                if receipt.exists():
                    supervisor_code = int(receipt.read_text().strip())
                    break
                time.sleep(.01)
            if supervisor_code is None:
                error = "supervisor receipt absent before cleanup cutoff"
    except Exception as exc:
        error = repr(exc)
    # Private tmux server, pane and any surviving descendants are all children
    # of this subreaper and also remain in the manager's task-only cgroup.
    killed, reaped, remaining = clean_children(cleanup_until)
    payload = json.loads(payload_record.read_text()) if payload_record.exists() else None
    code = payload["task_exit_code"] if payload else 125
    if supervisor_code is not None and supervisor_code != code:
        # Publication precedes process exit: the actual later nonzero exit wins.
        code = supervisor_code if supervisor_code != 0 else 125
    if error or remaining:
        code = 125
    record = {"object": "VSP03_B04", "unit": args.unit,
              "manager_properties": values, "started_monotonic": started,
              "cap_s": args.cap, "shutdown_publication_reserve_s": args.reserve,
              "task_exit_code": code, "supervisor_exit_code": supervisor_code,
              "payload": payload, "error": error,
              "descendants_killed": killed, "descendants_reaped": reaped,
              "descendants_remaining": remaining,
              "all_descendants_terminated": not remaining,
              "elapsed_before_terminal_publication_s": time.monotonic() - started}
    args.record.write_text(json.dumps(record, indent=2) + "\n")
    assert json.loads(args.record.read_text()) == record
    print(json.dumps({"terminal_published": str(args.record), "task_exit_code": code,
                      "elapsed_through_terminal_readback_s": time.monotonic() - started}),
          flush=True)
    if remaining:
        time.sleep(max(0, deadline - time.monotonic()) + 1)
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--cap", type=float, default=120)
    parser.add_argument("--reserve", type=float, default=10)
    parser.add_argument("--python", default="/home/wu/.venvs/hmasd/bin/python")
    parser.add_argument("--supervisor", default="/usr/local/bin/agent-task")
    parser.add_argument("--task-dir", type=Path, default=Path.home() / ".agent-tasks")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ["--"]:
        args.command = args.command[1:]
    raise SystemExit(run(args))
