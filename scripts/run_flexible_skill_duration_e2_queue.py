"""E2 launch queue - the contract's ordered 18 runs, two detached processes at a time.

Launch contract: `docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_20260903.md`
section 2 (order) and section 4 (budget, stop rule).

The queue is `(arm, seed)` in contract order: the central pair `d0_k40` and `d2_c1p0`
first (seed 1 then seed 2), then the remaining `k` arms, then the remaining `c` arms, so
that a stop after any pair leaves the central comparison matched.  Two runs execute
concurrently; each is a separate `python scripts/run_flexible_skill_duration_e2.py`
process with its stdout and stderr redirected into its run directory.

This script is itself launched detached, so the queue survives the loss of the session
that started it.  It writes `queue_state.json` at the study root after every state
change; poll that file (and the per-run directories) rather than blocking on a shell.

Usage:

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe \
        scripts/run_flexible_skill_duration_e2_queue.py \
        --output-root <study root> --launch-commit <sha> [--drop-outer-seed2]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_flexible_skill_duration_e2 import ARM_ORDER, OUTER_ARMS  # noqa: E402

RUNNER = REPO_ROOT / "scripts" / "run_flexible_skill_duration_e2.py"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_queue(seeds=(1, 2), drop_outer_seed2: bool = False):
    """Contract section 2 order; section 4.4 drop rule when asked for."""
    queue = []
    for arm in ARM_ORDER:
        for seed in seeds:
            if drop_outer_seed2 and seed == 2 and arm in OUTER_ARMS:
                continue
            queue.append((arm, int(seed)))
    return queue


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="E2 ordered launch queue")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--launch-commit", required=True)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--rollouts", type=int, default=20)
    parser.add_argument("--num-envs", type=int, default=16)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--eval-interval", type=int, default=5)
    parser.add_argument("--eval-tape-set", type=int, default=4096)
    parser.add_argument("--eval-episodes", type=int, default=4096)
    parser.add_argument("--eval-intermediate-episodes", type=int, default=4096)
    parser.add_argument("--eval-chunk", type=int, default=512)
    parser.add_argument("--eval-master-seed", type=int, default=770001)
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    parser.add_argument("--drop-outer-seed2", action="store_true",
                        help="contract section 4.4 drop rule")
    parser.add_argument("--poll-seconds", type=float, default=20.0)
    args = parser.parse_args(argv)

    root = Path(args.output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "queue_state.json"

    queue = build_queue(tuple(args.seeds), args.drop_outer_seed2)
    state = {
        "started_at": _utc_now(),
        "study_root": str(root),
        "launch_commit": args.launch_commit,
        "concurrency": int(args.concurrency),
        "queue": [{"arm": arm, "seed": seed, "status": "pending",
                   "started_at": None, "ended_at": None, "returncode": None}
                  for arm, seed in queue],
        "finished_at": None,
    }

    def write_state():
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    write_state()

    running = []  # (index, Popen, stdout handle, stderr handle)
    next_index = 0
    while next_index < len(queue) or running:
        while len(running) < int(args.concurrency) and next_index < len(queue):
            arm, seed = queue[next_index]
            run_dir = root / f"{arm}_seed{seed}"
            run_dir.mkdir(parents=True, exist_ok=True)
            command = [
                sys.executable, str(RUNNER),
                "--arm", arm,
                "--seed", str(seed),
                "--rollouts", str(args.rollouts),
                "--num-envs", str(args.num_envs),
                "--threads", str(args.threads),
                "--output-root", str(root),
                "--launch-commit", str(args.launch_commit),
                "--eval-interval", str(args.eval_interval),
                "--eval-tape-set", str(args.eval_tape_set),
                "--eval-episodes", str(args.eval_episodes),
                "--eval-intermediate-episodes", str(args.eval_intermediate_episodes),
                "--eval-chunk", str(args.eval_chunk),
                "--eval-master-seed", str(args.eval_master_seed),
            ]
            out = open(run_dir / "stdout.txt", "w", encoding="utf-8")
            err = open(run_dir / "stderr.txt", "w", encoding="utf-8")
            process = subprocess.Popen(command, cwd=str(REPO_ROOT), stdout=out,
                                       stderr=err, stdin=subprocess.DEVNULL)
            (run_dir / "command.txt").write_text(" ".join(command) + "\n",
                                                 encoding="utf-8")
            state["queue"][next_index]["status"] = "running"
            state["queue"][next_index]["started_at"] = _utc_now()
            state["queue"][next_index]["pid"] = int(process.pid)
            write_state()
            running.append((next_index, process, out, err))
            next_index += 1

        time.sleep(float(args.poll_seconds))

        still = []
        for index, process, out, err in running:
            code = process.poll()
            if code is None:
                still.append((index, process, out, err))
                continue
            out.close()
            err.close()
            state["queue"][index]["status"] = "done" if code == 0 else "failed"
            state["queue"][index]["ended_at"] = _utc_now()
            state["queue"][index]["returncode"] = int(code)
            write_state()
        running = still

    state["finished_at"] = _utc_now()
    write_state()
    print(json.dumps({"study_root": str(root),
                      "runs": len(queue),
                      "state": str(state_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
