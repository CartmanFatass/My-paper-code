"""Stage published FSD source only; invoke under an external complete-command cap."""
import time

STARTED = time.monotonic()

import argparse
import json
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path


REMOTE = r'''
import json, pathlib, shlex, subprocess, time
started = time.monotonic()
def run(argv):
    result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                            check=True)
    return result.stdout
try:
    repo = pathlib.Path(p["repo"])
    work = pathlib.Path(p["destination"])
    if work.parent.resolve() != pathlib.Path(p["worktree_root"]).resolve():
        raise ValueError("destination must be one named checkout under worktree_root")
    if work.exists():
        raise FileExistsError(str(work))
    print(json.dumps({"boundary": "payload_received", "destination": str(work)}), flush=True)
    fetch = shlex.join(["git", "-C", str(repo), "fetch", "origin", p["sha"]])
    run(shlex.split(p["network_shell"]) + [fetch])
    run(["git", "-C", str(repo), "worktree", "add", "--detach", "--no-checkout",
         str(work), p["sha"]])
    git = ["git", "-C", str(work), "-c", "core.autocrlf=false"]
    run(git + ["sparse-checkout", "set", "--cone", *p["sparse"]])
    run(git + ["checkout", "--detach", p["sha"]])
    head = run(git + ["rev-parse", "HEAD"]).decode().strip()
    if head != p["sha"]:
        raise ValueError("delivered commit differs from requested full SHA")
    for relative in p["readback"]:
        actual = (work / relative).read_bytes()
        expected = run(git + ["show", p["sha"] + ":" + relative])
        if actual != expected:
            raise ValueError("source readback differs: " + relative)
        if relative.endswith(".sh"):
            if b"\r" in actual:
                raise ValueError("CR byte in published shell source: " + relative)
            run(["/bin/bash", "-n", str(work / relative)])
    print(json.dumps({"status": "ready", "sha": head, "worktree": str(work),
                      "readback_paths": p["readback"], "scientific_submissions": 0,
                      "remote_wall_seconds": time.monotonic() - started}), flush=True)
except Exception as exc:
    failure = {"status": "failed", "error": str(exc),
               "remote_wall_seconds": time.monotonic() - started}
    if isinstance(exc, subprocess.CalledProcessError):
        failure.update(command=exc.cmd, returncode=exc.returncode,
                       stdout=exc.stdout.decode(errors="replace"),
                       stderr=exc.stderr.decode(errors="replace"))
    print(json.dumps(failure), flush=True)
    raise SystemExit(1)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--commands-dir", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=45)
    args = parser.parse_args()
    started = STARTED
    config = tomllib.loads((args.control_root / ".codex/hmasd-compute.toml").read_text())
    node = config["nodes"][config["default_result_node"]]
    readback = ["scripts/run_fsd_uav_renewal_batch_b02.py",
                "scripts/run_fsd_uav_individual_renewal_b01.py",
                "scripts/run_flexible_skill_duration_e0.py", "hmasd/agent.py",
                "hmasd/utils.py", "configs/config_1.py", "envs/pettingzoo/scenario1.py"]
    readback += [args.commands_dir + "/" + arm + ".sh" for arm in ("D0", "I")]
    payload = dict(repo=node["repo_root"], worktree_root=node["worktree_root"],
                   destination=args.destination, sha=args.sha,
                   network_shell=node["network_shell"],
                   sparse=node["sparse_checkout"] + ["configs", args.commands_dir],
                   readback=readback)
    code = ("p = " + repr(payload) + "\n" + REMOTE).replace("\r\n", "\n").encode("utf-8")
    remote = shlex.join(["/usr/bin/timeout", "--signal=KILL", str(args.seconds - 10) + "s",
                        node["python"], "-u", "-"])
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
               "-o", "ServerAliveInterval=3", "-o", "ServerAliveCountMax=1",
               node["ssh_target"], remote]
    receipt = dict(sha=args.sha, destination=args.destination, command=command,
                   payload_bytes=len(code), cr_bytes=code.count(b"\r"),
                   requested_outer_limit_seconds=args.seconds,
                   remote_limit_seconds=args.seconds - 10, scientific_submissions=0)
    try:
        remaining = args.seconds - 5 - (time.monotonic() - started)
        result = subprocess.run(command, input=code, capture_output=True, timeout=remaining)
        receipt.update(returncode=result.returncode,
                       stdout=result.stdout.decode("utf-8", errors="replace"),
                       stderr=result.stderr.decode("utf-8", errors="replace"))
    except subprocess.TimeoutExpired as exc:
        receipt.update(returncode=None, error="local SSH transport deadline",
                       stdout=(exc.stdout or b"").decode("utf-8", errors="replace"),
                       stderr=(exc.stderr or b"").decode("utf-8", errors="replace"))
    receipt["local_wall_before_receipt_seconds"] = time.monotonic() - started
    receipt["timing_limit"] = "External caller measures startup, receipt publication and exit."
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if receipt["returncode"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
