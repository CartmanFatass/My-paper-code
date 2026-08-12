"""CLI wiring for the isolated EOCIV-B9 receiver-addressed candidate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.eociv_lite.receiver_addressed_credit_edge import (
    READINESS_PHASES,
    readiness,
    registered_configuration,
    run_readiness_phase,
    run_registered_lifecycle,
)


def _print(value: object) -> None:
    print(json.dumps(value, sort_keys=True))


def _checkout_identity() -> tuple[str, bool]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return revision, not bool(status.strip())


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "EOCIV-B9 receiver-addressed credit edge. Configuration and readiness are "
            "zero-compute; run-registered is the explicit 312-episode scientific full."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("configuration", help="print the frozen candidate without episodes or updates")
    ready = commands.add_parser("readiness", help="candidate-bound zero-compute preflight")
    ready.add_argument("--candidate-revision", required=True)
    for phase_name in READINESS_PHASES:
        phase = commands.add_parser(
            phase_name,
            help=f"ordered temporary zero-science readiness phase: {phase_name}",
        )
        phase.add_argument("--candidate-revision", required=True)
        phase.add_argument("--exercise-root", type=Path, required=True)
    run = commands.add_parser(
        "run-registered",
        help="claim the reserved result exclusively, then run the registered 312-episode full",
    )
    run.add_argument("--candidate-revision", required=True)
    run.add_argument("--run-id", required=True)
    arguments = parser.parse_args()
    torch.set_num_threads(1)
    checkout_revision, checkout_clean = _checkout_identity()
    if arguments.command == "configuration":
        value = registered_configuration()
    elif arguments.command == "readiness":
        value = readiness(
            candidate_revision=arguments.candidate_revision,
            checkout_revision=checkout_revision,
            checkout_clean=checkout_clean,
        )
    elif arguments.command in READINESS_PHASES:
        value = run_readiness_phase(
            arguments.command,
            exercise_root=arguments.exercise_root,
            repository_root=ROOT,
            candidate_revision=arguments.candidate_revision,
            checkout_revision=checkout_revision,
            checkout_clean=checkout_clean,
        )
    else:
        value = run_registered_lifecycle(
            repository_root=ROOT,
            candidate_revision=arguments.candidate_revision,
            checkout_revision=checkout_revision,
            checkout_clean=checkout_clean,
            run_id=arguments.run_id,
        )
    _print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
