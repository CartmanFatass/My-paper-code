"""Lifecycle runner for the VSP06-B2 source/config candidate.

The default/readiness path is zero-activity.  Canonical catalog materialization
and the one two-replica selector invocation require explicit subcommands.  The
single registered-full subcommand executes only from an already fixed, verified
manifest and is never called by source/config readiness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.vsp_06_mssr import (  # noqa: E402
    vsp06_b2_authenticated_partner_recall_credit_efficiency as experiment,
)
from experiments.candidates.vsp_06_mssr import (  # noqa: E402
    vsp06_b2_source_bound_exact_feasibility as selector,
)


DEFAULT_LEDGER = ROOT / "docs/research/candidates/vsp_06_mssr/VSP06_B2_CONSTRAINT_TARGET_LEDGER_V1.json"
DEFAULT_VERIFIER = ROOT / "experiments/candidates/vsp_06_mssr/vsp06_b2_independent_exact_manifest_verifier.py"
RESULT_PATH = ROOT / "docs/research/candidates/vsp_06_mssr/VSP06_B2_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_RESULT.json"
SESSION_ROOT = ROOT / "temp/sessions/code_project_manager/vsp06_b2_source_bound_exact_feasibility_credit_efficiency"
CATALOG_PATH = SESSION_ROOT / "canonical_catalog.json"
MANIFEST_PATH = SESSION_ROOT / "frozen_manifest.json"
SELECTOR_ROOT = SESSION_ROOT / "selector"
SELECTOR_RECEIPT_PATH = SELECTOR_ROOT / "selector_success_receipt.json"
VERIFIER_REPORT_PATH = SELECTOR_ROOT / "independent_verifier_report.json"
RUN_ROOT = SESSION_ROOT / "registered_full"
FULL_NOT_STARTED = "B2_REGISTERED_FULL_NOT_STARTED"
FULL_TERMINAL = "B2_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
EXECUTION_DISPOSITION = "B2_SELECTOR_INVALID_NO_RUN_PENDING_EXPLORER_REBIND_DECISION"


class RunnerInvalid(RuntimeError):
    """Fail-closed runner lifecycle error."""


def _bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise RunnerInvalid(f"JSON root is not an object: {path}")
    return value


def _zero_activity(path: Path) -> None:
    counters = _load(path)
    required = {
        "environment_episodes", "environment_transitions", "production_policy_forwards",
        "learner_updates", "optimizer_steps", "evaluator_calls", "evaluation_episodes",
        "model_fits", "trainer_invocations", "environment_rng_draws", "action_rng_draws",
    }
    if set(counters) != required or any(isinstance(value, bool) or value != 0 for value in counters.values()):
        raise RunnerInvalid("preselector activity/RNG counters are not exactly zero")


def readiness() -> dict[str, Any]:
    result = experiment.readiness_contract()
    try:
        selector.selector_environment()
    except selector.SelectorInvalid as exc:
        result["selector_dependency_gate"] = {
            "ready": False,
            "branch": selector.INVALID,
            "reason": str(exc),
            "fallback_available": False,
        }
    else:
        result["selector_dependency_gate"] = {
            "ready": True,
            "branch": None,
            "reason": None,
            "fallback_available": False,
        }
    result["result_path_exists"] = RESULT_PATH.exists()
    result["execution_disposition"] = EXECUTION_DISPOSITION
    return result


def prepare_catalog(path: Path) -> dict[str, Any]:
    raise RunnerInvalid(EXECUTION_DISPOSITION)
    # Retained below as the frozen candidate pathway pending Explorer decision.
    if path.exists():
        raise RunnerInvalid("canonical catalog destination already exists")
    rows = list(experiment.canonical_catalog_rows())
    catalog = {"catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": rows}
    selector.parse_catalog(catalog)
    selector.write_exclusive(path, _bytes(catalog) + b"\n")
    return {"catalog_path": str(path), "catalog_sha256": selector.sha256_file(path), "row_count": len(rows)}


def run_selector(args: argparse.Namespace) -> dict[str, Any]:
    raise RunnerInvalid(EXECUTION_DISPOSITION)
    # Retained below as the frozen candidate pathway pending Explorer decision.
    if RESULT_PATH.exists():
        raise RunnerInvalid("result destination exists before selector admission")
    _zero_activity(Path(args.zero_counters).resolve())
    return selector.run_two_replica_sequence(
        catalog_path=Path(args.catalog).resolve(),
        ledger_path=Path(args.ledger).resolve(),
        manifest_path=Path(args.manifest).resolve(),
        verifier_path=Path(args.verifier).resolve(),
        work_root=Path(args.work_root).resolve(),
    )


def run_full() -> dict[str, Any]:
    """The unique executable registered-full path, gated by a fixed manifest."""

    raise RunnerInvalid(EXECUTION_DISPOSITION)
    # Retained below as the frozen candidate pathway pending Explorer decision.
    receipt = _load(SELECTOR_RECEIPT_PATH)
    return experiment.run_registered_full(
        manifest_path=MANIFEST_PATH,
        manifest_content_digest=str(receipt["manifest_content_sha256"]),
        session_root=SESSION_ROOT,
        selector_receipt_path=SELECTOR_RECEIPT_PATH,
        verifier_report_path=VERIFIER_REPORT_PATH,
        run_root=RUN_ROOT,
        result_path=RESULT_PATH,
    )


def _full_failure_payload(exc: Exception, run_root: Path = RUN_ROOT) -> dict[str, Any]:
    failure_path = run_root / "registered_full_failure.json"
    claim_path = run_root / "registered_full_claim.json"
    if claim_path.exists() or failure_path.exists():
        recorded = _load(failure_path) if failure_path.exists() else {}
        return {
            "branch": FULL_TERMINAL,
            "failure_path": str(failure_path) if failure_path.exists() else None,
            "activity_counts": recorded.get("activity_counts"),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "retry_authorized": False,
        }
    return {
        "branch": FULL_NOT_STARTED,
        "failure_path": None,
        "activity_counts": None,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "retry_authorized": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("readiness")
    catalog = sub.add_parser("prepare-catalog")
    catalog.add_argument("--output", required=True)
    select = sub.add_parser("select")
    select.add_argument("--catalog", required=True)
    select.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    select.add_argument("--manifest", required=True)
    select.add_argument("--verifier", default=str(DEFAULT_VERIFIER))
    select.add_argument("--work-root", required=True)
    select.add_argument("--zero-counters", required=True)
    sub.add_parser("run-full")
    args = parser.parse_args(argv)
    try:
        if args.command == "readiness":
            result = readiness()
        elif args.command == "prepare-catalog":
            result = prepare_catalog(Path(args.output).resolve())
        elif args.command == "select":
            result = run_selector(args)
        else:
            result = run_full()
        sys.stdout.buffer.write(_bytes(result) + b"\n")
        return 0
    except Exception as exc:
        if args.command == "run-full":
            sys.stderr.buffer.write(_bytes(_full_failure_payload(exc)) + b"\n")
        else:
            sys.stderr.write(f"{selector.INVALID}: {type(exc).__name__}: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
