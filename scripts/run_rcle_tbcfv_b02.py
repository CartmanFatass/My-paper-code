"""RCLE-TBCFV-B02 0.02-norm persist-vs-flex entry. Thread env is set before torch is imported."""

from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse
import json
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RCLE-TBCFV-B02 0.02-norm persist-vs-flex")
    sub = parser.add_subparsers(dest="mode", required=True)

    build = sub.add_parser("build")
    build.add_argument("--build-root", type=Path, required=True)

    arm = sub.add_parser("arm")
    arm.add_argument("--arm", required=True, choices=("C1P1", "FLEX"))
    arm.add_argument("--out", type=Path, required=True)
    arm.add_argument("--wall-cap", type=float, default=580.0)
    arm.add_argument("--admission-receipt", type=Path, default=None)
    arm.add_argument("--control-summary", type=Path, default=None)
    arm.add_argument("--updates", type=int, default=200)
    arm.add_argument("--eval-episodes", type=int, default=256)
    arm.add_argument("--launch-sha", default="")

    reference = sub.add_parser("reference")
    reference.add_argument("--out", type=Path, required=True)
    reference.add_argument("--eval-episodes", type=int, default=256)
    reference.add_argument("--admission-receipt", type=Path, default=None)
    reference.add_argument("--launch-sha", default="")
    return parser


def _arm_identity(payload: dict[str, object]) -> dict[str, object]:
    default_root = payload.get("default_root")
    body: dict[str, object] = {
        "source_sha256": payload["source_sha256"],
        "build_key": payload["build_key"],
        "artifact_sha256": payload["artifact_sha256"],
        "path": payload["path"],
    }
    if isinstance(default_root, dict):
        body["default_root"] = {
            "source_sha256": default_root["source_sha256"],
            "build_key": default_root["build_key"],
            "artifact_sha256": default_root["artifact_sha256"],
            "path": default_root["path"],
        }
    return body


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode == "build":
        from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b02.study import (
            build_native,
        )

        payload = build_native(args.build_root)
        sys.stdout.write(
            json.dumps(_arm_identity(payload), indent=2, sort_keys=True) + "\n"
        )
        return 0
    if args.mode == "arm":
        import torch

        torch.set_num_threads(1)
        from experiments.candidates.roster_consistent_latent_exploration_tbcfv.config import (
            C1P1,
            FLEX,
        )
        from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b02.study import (
            ArmWallExpired,
            run_arm,
        )

        previous = None
        timer_armed = False
        if hasattr(signal, "SIGALRM") and hasattr(signal, "setitimer"):
            def timeout(signum, frame):
                raise ArmWallExpired("SIGALRM")

            previous = signal.signal(signal.SIGALRM, timeout)
            signal.setitimer(signal.ITIMER_REAL, max(0.001, float(args.wall_cap)))
            timer_armed = True
        arm_name = C1P1 if args.arm == "C1P1" else FLEX
        try:
            summary = run_arm(
                arm=arm_name,
                out=args.out,
                updates=args.updates,
                eval_episodes=args.eval_episodes,
                wall_cap=args.wall_cap,
                admission_receipt=args.admission_receipt,
                launch_sha=args.launch_sha,
                control_summary=args.control_summary,
            )
        finally:
            if timer_armed:
                signal.setitimer(signal.ITIMER_REAL, 0.0)
                if previous is not None:
                    signal.signal(signal.SIGALRM, previous)
        sys.stdout.write(json.dumps({"status": summary["status"], "arm": arm_name}) + "\n")
        return 0 if summary["status"] == "COMPLETE" else 2
    if args.mode == "reference":
        from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b02.study import (
            run_reference,
        )

        summary = run_reference(
            out=args.out,
            eval_episodes=args.eval_episodes,
            admission_receipt=args.admission_receipt,
            launch_sha=args.launch_sha,
        )
        sys.stdout.write(json.dumps({"status": summary["status"]}) + "\n")
        return 0 if summary["status"] == "COMPLETE" else 2
    raise ValueError(f"unknown mode {args.mode!r}")


if __name__ == "__main__":
    raise SystemExit(main())
