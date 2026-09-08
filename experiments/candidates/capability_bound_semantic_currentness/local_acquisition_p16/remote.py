"""P16 remote command, transfer receiver and pinned offline setup (never on import)."""

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from inputs import BODIES, CONTAINERS, PINS
from processes import LinuxLimit, boottime, remaining

HERE = Path(__file__).resolve().parent
PREFLIGHT_SHA = "ec8866b3968fcb1566976ce405d7c552d4d9a5de"


def clock_sample():
    return {"seconds": boottime(),
            "boot": Path("/proc/sys/kernel/random/boot_id").read_text().strip()}


def remote_remaining(deadline, boot, sample=None):
    now = clock_sample() if sample is None else sample
    if now["boot"] != boot:
        raise RuntimeError("Remote clock domain changed; no next phase")
    return remaining(deadline, lambda: now["seconds"])


def receive(out, stream, bodies=BODIES):
    wheels = out / "wheels"
    wheels.mkdir(parents=True)
    for name, _, size in bodies:
        left = size
        with (wheels / name).open("xb") as target:
            while left:
                chunk = stream.read(min(left, 1024 * 1024))
                if not chunk:
                    raise RuntimeError(f"Incomplete transfer: {name}, {left} bytes absent")
                target.write(chunk)
                left -= len(chunk)
    if stream.read(1):
        raise RuntimeError("Unexpected trailing transfer bytes")


def setup(args):
    os.chdir(args.repo)
    out, candidate = Path(args.out), Path(args.candidate)
    env = os.environ.copy()
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[name] = "1"
    env.update(UV_CACHE_DIR=str(out / "uv-cache"), TMPDIR=str(out / "tmp"))
    # Adjacent admission and setup form one sequential, fail-fast process chain.
    remote_remaining(args.deadline, args.boot)
    subprocess.run([args.python, str(Path(args.repo) / "scripts/hmasd_resource_preflight.py"),
                    "admit-memory", "--out", str(out / "admission.json")], check=True, env=env)
    remote_remaining(args.deadline, args.boot)
    (out / "tmp").mkdir()
    subprocess.run([args.uv, "--no-config", "venv", "--python", args.python,
                    "--no-python-downloads", str(candidate)], check=True, env=env)
    for name in CONTAINERS:
        (out / "wheels" / name).symlink_to(Path(args.retained) / name)
    remote_remaining(args.deadline, args.boot)
    with (out / "install.log").open("wb") as log:
        subprocess.run([args.uv, "--no-config", "pip", "install", "--python",
                        str(candidate / "bin/python"), "--no-index", "--find-links",
                        str(out / "wheels"), "--only-binary", ":all:", *PINS],
                       check=True, env=env, stdout=log, stderr=subprocess.STDOUT)
    remote_remaining(args.deadline, args.boot)
    subprocess.run([str(candidate / "bin/python"), str(HERE / "metadata.py"), str(out),
                    PREFLIGHT_SHA, str(candidate / "bin/python"), args.source, str(args.seed)],
                   check=True, env=env)


def common(args):
    return ["--python", args.python, "--repo", args.repo, "--out", args.out,
            "--deadline", str(args.deadline), "--boot", args.boot, "--handle", args.handle,
            "--candidate", args.candidate, "--retained", args.retained, "--uv", args.uv,
            "--source", args.source, "--seed", str(args.seed), "--supervisor", args.supervisor,
            "--tmux", args.tmux]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("anchor", "receive", "launch",
                                         "controller", "setup", "collect"))
    for flag in ("python", "repo", "out", "boot", "handle", "candidate", "retained",
                 "uv", "source", "supervisor", "tmux"):
        parser.add_argument("--" + flag)
    parser.add_argument("--deadline", type=float)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    if args.mode == "anchor":
        print(json.dumps(clock_sample()), flush=True)
        return 0
    # The same node-domain absolute deadline is kept through dispatch and setup.
    remote_remaining(args.deadline, args.boot)
    if args.mode == "setup":
        setup(args)
        return 0
    complete_deadline = args.deadline + 59  # Within the original 60 s publication margin.
    limit = LinuxLimit(complete_deadline if args.mode in ("controller", "collect") else args.deadline)
    try:
        if args.mode == "receive":
            receive(Path(args.out), sys.stdin.buffer)
            return 0
        if args.mode == "launch":
            command = shlex.join(["/usr/bin/env", "-u", "BASH_ENV", "-u", "ENV",
                                  args.python, str(HERE / "remote.py"), "controller", *common(args)])
            return limit.run([args.supervisor, "run", args.handle, command], args.deadline)
        if args.mode == "controller":
            code, error = 1, None
            try:
                # The sole task process group on the remote node.
                code = limit.run([args.python, str(HERE / "remote.py"), "setup", *common(args)],
                                 args.deadline, group=True)
            except Exception as exc:
                error = str(exc)
            finally:
                terminal = {"exit_code": code, "error": error, "handle": args.handle,
                            "remote_deadline_boottime_seconds": args.deadline}
                (Path(args.out) / "terminal.json").write_text(json.dumps(terminal), encoding="utf-8")
                limit.run([args.tmux, "wait-for", "-S", args.handle], min(complete_deadline, boottime() + 1))
            return code
        if args.mode == "collect":
            terminal_path = Path(args.out) / "terminal.json"
            if not terminal_path.exists():
                code = limit.run([args.tmux, "wait-for", args.handle], args.deadline)
                if code:
                    return code
            remote_remaining(args.deadline, args.boot)
            terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
            summary_path = Path(args.out) / "summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
            remote_remaining(args.deadline, args.boot)
            print(json.dumps({"terminal": terminal, "summary": summary}), flush=True)
            return 0
        raise AssertionError(args.mode)
    finally:
        limit.close()


if __name__ == "__main__":
    raise SystemExit(main())
