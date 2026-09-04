"""Explicit CLI for SCDMP B01 preflight, A-R2, or the confirmed replacement run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.runner import (
    RUN_CONFIRMATION,
    performance_assessment_record,
    preflight_only,
    run_assess,
    run_result,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.assessment import (
    ASSESS_ID,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.contracts import (
    ATTEMPT_ID, NAMED_RUN_ID, STUDY_ID,
)


def main(argv: list[str] | None = None) -> int:
    exact_argv = tuple(sys.argv if argv is None else (str(Path(__file__).resolve()), *argv))
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--assess-run", choices=("A/RECON",))
    mode.add_argument("--run-01", action="store_true")
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--assess-root", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stop-after-frontier")
    parser.add_argument("--confirm-run-id")
    # Section 11 recast, 2026-09-02: both are recorded evidence, not launch
    # conditions.  See docs/research/candidates/
    # semigroup_consistent_duration_model_policy/
    # SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md.
    parser.add_argument("--performance-readiness", type=Path)
    parser.add_argument("--performance-assessment", type=Path)
    args = parser.parse_args(argv)
    cwd = Path.cwd().resolve()

    if args.preflight_only:
        if (args.result_root is None or args.assess_root is not None or args.resume
                or args.stop_after_frontier or args.performance_readiness is not None
                or args.performance_assessment is not None):
            parser.error("--preflight-only requires only --result-root and --receipt")
        observed = preflight_only(
            receipt=args.receipt, result_root=args.result_root, command_runner=subprocess.run,
        )
        print(json.dumps({"mode": "PREFLIGHT_ONLY", "passed": observed.passed,
                          "receipt": str(observed.path.resolve()),
                          "prospective_result_root": str(args.result_root.resolve()),
                          "cwd": str(cwd), "argv": list(exact_argv)}, sort_keys=True))
        return 0

    if args.assess_run:
        if (args.assess_root is None or args.result_root is not None or args.resume
                or args.confirm_run_id or args.stop_after_frontier
                or args.performance_readiness is not None
                or args.performance_assessment is not None):
            parser.error("A/RECON requires --assess-root and forbids result/resume/confirmation options")
        print(json.dumps({"mode": "A/RECON", "assessment_id": ASSESS_ID,
                          "assess_root": str(args.assess_root.resolve()),
                          "receipt": str(args.receipt.resolve()), "cwd": str(cwd),
                          "argv": list(exact_argv)}, sort_keys=True), flush=True)
        result = run_assess(
            assess_root=args.assess_root, admission_receipt=args.receipt,
            command_runner=subprocess.run, argv=exact_argv, cwd=cwd,
        )
        print(json.dumps({"assessment": str(result.resolve()), "assessment_id": ASSESS_ID,
                         "source_identity": str((args.assess_root / "source-identity.json").resolve()),
                         "disposition": "REVIEW_REQUIRED"},
                         sort_keys=True))
        return 0

    if args.result_root is None or args.assess_root is not None:
        parser.error("--run-01 requires --result-root and forbids --assess-root")
    if args.result_root.name != ATTEMPT_ID:
        parser.error(f"--result-root name must be {ATTEMPT_ID}")
    if args.confirm_run_id != RUN_CONFIRMATION:
        parser.error(f"--run-01 requires --confirm-run-id {RUN_CONFIRMATION}")
    recorded_assessment = performance_assessment_record(
        performance_readiness=args.performance_readiness,
        performance_assessment=args.performance_assessment,
    )
    print(json.dumps({"mode": NAMED_RUN_ID, "study_id": STUDY_ID,
                      "attempt_id": ATTEMPT_ID,
                      "result_root": str(args.result_root.resolve()),
                      "receipt": str(args.receipt.resolve()), "resume": args.resume,
                      "recorded_performance_assessment": recorded_assessment,
                      "cwd": str(cwd), "argv": list(exact_argv)}, sort_keys=True), flush=True)
    result = run_result(
        result_root=args.result_root, admission_receipt=args.receipt,
        confirmation=args.confirm_run_id, resume=args.resume, argv=exact_argv, cwd=cwd,
        command_runner=subprocess.run, stop_after_frontier=args.stop_after_frontier,
        performance_readiness=args.performance_readiness,
        performance_assessment=args.performance_assessment,
    )
    key = "technical_frontier" if result.name == "technical-frontier.json" else "published_result"
    print(json.dumps({key: str(result.resolve()),
                      "source_identity": str((args.result_root / "source-identity.json").resolve())},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
