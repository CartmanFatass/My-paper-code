#!/usr/bin/env python3
"""CPU reproduction harness for the energy-relay ``listobject.c:2529`` fault (diagnostic only).

Resumes the learner from a local training checkpoint (default: B02 Stage 1 ``c03``, rollout 100)
on the CPU and runs the real training loop -- B05's ``collect_and_train_canonical`` (SW frame) or
B02's ``collect_and_train`` -- i.e. agent.step, shield, env.step (native geometry backend),
store_transition_batch, the rollout checks, agent.update and clear_buffers, until ``--steps``
collector steps (each = one env step per lane) or ``--max-seconds`` are reached.  Nothing is
checkpointed and no result-bearing record is written; ``summary.json`` under ``--out`` records
what ran: steps, env steps, wall, the ending (steps reached / time / exception with traceback),
RSS / pymalloc block / gc samples, interpreter and allocator settings.

Allocator/debug modes (``--malloc``): the process re-executes itself once with
``PYTHONMALLOC=<mode>`` and ``-X dev -X faulthandler`` when the mode is not ``inherit`` (both
must be set before the interpreter starts).  ``debug`` = pymalloc with CPython's debug hooks
(a double free or a write past a block is fatal at the faulty call with a traceback; freed
memory is filled with 0xDD); ``malloc_debug`` = the same hooks over the C allocator; ``malloc``
= glibc malloc without hooks.  Debug hooks change the heap layout, so a negative result means
"no detectable Python-heap API misuse in N steps", not "the site is clean".

The seed is the resume contract's (``spec.seed + checkpoint rollout`` = 925131 for c03);
``--seed`` exists to record it and may be changed only for a diagnostic, never for a result.
Core dumps are disabled in the process by default (``prctl(PR_SET_DUMPABLE, 0)``): on WSL the
kernel pipes them to ``wsl-capture-crash`` (~150 MB each, written to the Windows temp folder).

Example (from the checkout root, venv ``bin`` first on PATH)::

    timeout 3000 python -m experiments.candidates.energy_relay_benchmark.diagnostics.crash_harness \
        --out temp/directions/energy_relay_benchmark/scratch/<tag>/run --steps 40000 \
        --max-seconds 2700 --malloc debug --audit
"""

from __future__ import annotations

import argparse
import ctypes
import gc
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_CHECKPOINT = ROOT / "runs/energy_relay_benchmark/b02_s1_set_a01/checkpoints/c03"
MALLOC_MODES = ("inherit", "debug", "malloc_debug", "malloc", "pymalloc", "pymalloc_debug")
REEXEC_MARK = "HMASD_CRASH_HARNESS_REEXEC"


class _Stop(Exception):
    """Raised from ``observe_step`` to end the loop (exits through the collector's ``finally``)."""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="new directory for summary.json")
    parser.add_argument("--steps", type=int, required=True,
                        help="collector steps to run (each = one env step in each of 2 lanes)")
    parser.add_argument("--max-seconds", type=float, default=None,
                        help="stop cleanly at the first step after this wall (before `timeout`)")
    parser.add_argument("--collector", choices=("b05", "b02"), default="b05")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT,
                        help="B02 checkpoints/cNN directory (record.json + agent.pt)")
    parser.add_argument("--seed", type=int, default=None,
                        help="resume seed (default: the resume contract, spec seed + rollout)")
    parser.add_argument("--launch-sha", default=None, help="recorded; default git HEAD")
    parser.add_argument("--threads", type=int, default=4, help="torch threads (node: 4)")
    parser.add_argument("--malloc", choices=MALLOC_MODES, default="inherit")
    parser.add_argument("--audit", action="store_true",
                        help="install diagnostics.crash_audit into --out (HMASD_CRASH_AUDIT=1)")
    parser.add_argument("--sample-every", type=int, default=500,
                        help="collector steps between RSS/gc samples in summary.json")
    parser.add_argument("--build-root", type=Path, default=None,
                        help="native build root (default: $HMASD_UAV_CPP_BUILD_ROOT, else "
                             "<out>/../cpp-build)")
    parser.add_argument("--allow-core", action="store_true",
                        help="leave the process dumpable (WSL copies cores to Windows temp)")
    args = parser.parse_args(argv)
    if args.steps <= 0:
        parser.error("--steps must be positive")
    return args


def _reexec_if_needed(args, argv) -> None:
    """Restart once under the requested allocator with ``-X dev -X faulthandler``."""
    if args.malloc == "inherit" or os.environ.get(REEXEC_MARK) == "1":
        return
    environment = dict(os.environ, PYTHONMALLOC=args.malloc, **{REEXEC_MARK: "1"})
    command = [sys.executable, "-X", "dev", "-X", "faulthandler", str(Path(__file__).resolve()),
               *(sys.argv[1:] if argv is None else argv)]
    os.execve(sys.executable, command, environment)


def _git_head() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return None


def _rss_kib() -> int | None:
    try:
        with open("/proc/self/statm", "rb") as handle:
            return int(handle.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") // 1024
    except (OSError, ValueError, IndexError):
        return None


def _sample(step: int, started: float) -> dict:
    return {"step": step, "wall_s": time.monotonic() - started, "rss_kib": _rss_kib(),
            "allocated_blocks": sys.getallocatedblocks(), "gc_count": list(gc.get_count()),
            "gc_collections": [row["collections"] for row in gc.get_stats()]}


def _write(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=repr) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def run(args) -> dict:
    out = args.out.resolve()
    if (out / "summary.json").exists():
        raise FileExistsError(f"harness output already exists: {out}")
    out.mkdir(parents=True, exist_ok=True)
    if not args.allow_core and sys.platform.startswith("linux"):
        ctypes.CDLL(None).prctl(4, 0, 0, 0, 0)   # PR_SET_DUMPABLE = 0
    build_root = args.build_root or (Path(os.environ["HMASD_UAV_CPP_BUILD_ROOT"])
                                     if os.environ.get("HMASD_UAV_CPP_BUILD_ROOT")
                                     else out.parent / "cpp-build")
    os.environ["HMASD_UAV_CPP_BUILD_ROOT"] = str(Path(build_root).resolve())

    audit = None
    if args.audit:
        from experiments.candidates.energy_relay_benchmark.diagnostics import crash_audit
        audit = crash_audit.install(out)

    import numpy as np
    import torch

    from experiments.candidates.energy_relay_benchmark.b02 import training as b02_training
    from experiments.candidates.energy_relay_benchmark.b02.configuration import make_b02_config
    from experiments.candidates.energy_relay_benchmark.b05 import training as b05_training

    spec = b05_training.production_spec(925031)
    if args.collector == "b02":
        from experiments.candidates.energy_relay_benchmark.b02.configuration import production_spec
        spec = production_spec(925031)
    config = make_b02_config(spec)
    record = b02_training.read_resume_checkpoint(args.checkpoint, spec, config)
    seed = int(spec.seed) + int(record["rollout"]) if args.seed is None else int(args.seed)
    torch.set_num_threads(int(args.threads))
    started = time.monotonic()
    summary = {
        "object": "energy_relay_benchmark crash-debug CPU harness (diagnostic, not a result)",
        "launch_sha": args.launch_sha or _git_head(), "argv": sys.argv, "seed": seed,
        "collector": args.collector, "checkpoint": str(args.checkpoint),
        "checkpoint_rollout": record["rollout"], "steps_requested": args.steps,
        "max_seconds": args.max_seconds, "torch_threads": torch.get_num_threads(),
        "python": sys.version, "numpy": np.__version__, "torch": torch.__version__,
        "platform": platform.platform(), "pythonmalloc": os.environ.get("PYTHONMALLOC"),
        "dev_mode": bool(sys.flags.dev_mode), "faulthandler": __import__("faulthandler").is_enabled(),
        "build_root": os.environ["HMASD_UAV_CPP_BUILD_ROOT"], "audit": audit,
        "dumpable": bool(args.allow_core) or not sys.platform.startswith("linux"),
        "status": "RUNNING", "steps_completed": 0, "env_steps": 0, "rollouts_completed": 0,
        "samples": [], "rollouts": [], "ending": None,
    }
    _write(out / "summary.json", summary)
    counter = {"steps": 0}

    def observe_step(agent, step_data, step):
        counter["steps"] += 1
        done = counter["steps"]
        if done % max(1, int(args.sample_every)) == 0:
            summary["samples"].append(_sample(done, started))
            summary.update(steps_completed=done, env_steps=(done - 1) * spec.lanes)
            _write(out / "summary.json", summary)
        if done >= args.steps:
            raise _Stop("steps")
        if args.max_seconds is not None and time.monotonic() - started >= args.max_seconds:
            raise _Stop("max_seconds")

    def after_rollout(rollout, rollout_record):
        summary["rollouts_completed"] += 1
        summary["rollouts"].append({
            "rollout": rollout, "collection_seconds": rollout_record["collection_seconds"],
            "update_seconds": rollout_record["update_seconds"],
            **_sample(counter["steps"], started)})
        _write(out / "summary.json", summary)

    agent = None
    try:
        agent, _ = b02_training.resumed_agent(config, record, Path(args.checkpoint) / "agent.pt",
                                              device=torch.device("cpu"), log_dir=out / "logs",
                                              seed=seed)
        summary["agent_loaded_s"] = time.monotonic() - started
        collect = (b05_training.collect_and_train_canonical if args.collector == "b05"
                   else b02_training.collect_and_train)
        collect(agent, config, spec, feedback=True, observe_step=observe_step,
                after_rollout=after_rollout, start_rollout=int(record["rollout"]),
                start_transitions=int(record["transitions"]), env_seed=seed)
        summary.update(status="LOOP_ENDED", ending={"kind": "loop_returned"})
    except _Stop as stop:
        summary.update(status="STOPPED", ending={"kind": str(stop)})
    except BaseException as exc:
        summary.update(status="EXCEPTION", ending={
            "kind": "exception", "type": type(exc).__name__, "message": str(exc),
            "traceback": traceback.format_exc()})
        raise
    finally:
        # ``steps_completed`` counts agent.step calls.  A _Stop is raised before that step's
        # env.step calls, so it did not step the envs; an exception inside the loop leaves the
        # last step's env count unknown (the figure is then an upper bound).
        done = counter["steps"]
        env_steps = (done - 1 if summary["status"] == "STOPPED" else done) * spec.lanes
        summary.update(steps_completed=done, env_steps=max(env_steps, 0),
                       env_steps_exact=summary["status"] != "EXCEPTION",
                       wall_s=time.monotonic() - started)
        summary["samples"].append(_sample(counter["steps"], started))
        _write(out / "summary.json", summary)
    return summary


def main(argv=None):
    args = parse_args(argv)
    _reexec_if_needed(args, argv)
    summary = run(args)
    print(f"crash harness: {summary['status']} steps={summary['steps_completed']} "
          f"env_steps={summary['env_steps']} wall={summary['wall_s']:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
