"""Stage-1-safe wiring and dormant Stage-2 entry points for VSP06-B2R1."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from experiments.candidates.vsp_06_mssr import vsp06_b2r1_authenticated_partner_recall_credit_efficiency as experiment  # noqa: E402
from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector  # noqa: E402

SYNTHETIC_DOMAIN = "VSP06-B2R1-SYNTHETIC-NONCANONICAL-V1"
SYNTHETIC_SUCCESS = "SYNTHETIC_STRUCTURAL_VALID_ONLY"
RESERVED_PATHS = (
    ROOT / "docs/research/candidates/vsp_06_mssr/VSP06_B2R1_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_RESULT.json",
    ROOT / "temp/sessions/code_project_manager/vsp06_b2r1_source_bound_exact_feasibility_credit_efficiency",
    ROOT / "temp/sessions/code_project_manager/vsp06_b2r1_operator_receipt.json",
)

class RunnerInvalid(RuntimeError):
    pass

def _bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")

def _load(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise RunnerInvalid("JSON root is not an object")
    return value

def _authorization(path: Path) -> Mapping[str, Any]:
    path = selector.safe_existing_path(path)
    bootstrap = _load(path)
    selector.validate_stage2_authorization(bootstrap)
    selector.authorize_read_path(bootstrap, path)
    value = selector.authorized_json(bootstrap, path)
    selector.validate_stage2_authorization(value)
    if value != bootstrap:
        raise RunnerInvalid("Stage-2 authorization changed during secure load")
    return value

def _authorized_load(authorization: Mapping[str, Any], path: Path) -> Mapping[str, Any]:
    return selector.authorized_json(authorization, path)

def stage1_status() -> Mapping[str, Any]:
    return {
        "synthetic_only": True, "domain": SYNTHETIC_DOMAIN, "success_token": SYNTHETIC_SUCCESS,
        "canonical_authorized": False, "full_authorized": False,
        "reserved_paths_absent": all(not path.exists() for path in RESERVED_PATHS),
        "activity": dict(experiment.ACTIVITY_COUNTERS),
        "K_search": 0, "hypothetical_transitions": 0,
    }

def _preclaim_readiness(
    stage2_authorization_path: Path,
) -> tuple[Mapping[str, Any], Mapping[str, Any], object]:
    """Write-free exact readiness; no namespace creation or catalog observation."""

    authorization = _authorization(stage2_authorization_path)
    selector.verify_authorized_source_config(authorization)
    environment_path, environment = selector.load_full_environment_receipt(authorization)
    paths = selector.stage2_paths()
    selector._require_exhaustive_allowlist(
        authorization, stage2_authorization_path.resolve(), paths, environment
    )
    selector.validate_selector_environment_receipt(authorization, environment)
    experiment.bind_full_environment(authorization, environment)
    if authorization["zero_start_activity"] != experiment.ACTIVITY_COUNTERS:
        raise RunnerInvalid("zero-start activity binding failed")
    if any(authorization["zero_start_activity"].values()):
        raise RunnerInvalid("readiness requires all 18 activity counters zero")
    selector.output_paths_must_be_absent(paths)
    capability = selector._issue_stage2_readiness_capability(
        authorization, stage2_authorization_path.resolve()
    )
    return authorization, {
        "ready": True, "write_free": True,
        "full_environment_receipt_path": str(environment_path),
        "full_environment_receipt_sha256": authorization["full_environment_receipt_sha256"],
        "activity": dict(authorization["zero_start_activity"]),
    }, capability


def stage2_readiness(stage2_authorization_path: Path) -> Mapping[str, Any]:
    _authorization_value, result, capability = _preclaim_readiness(
        stage2_authorization_path
    )
    selector._discard_stage2_readiness_capability(capability)
    return result


def _claim_fixed_stage2_namespace(
    authorization: Mapping[str, Any], readiness_capability: object,
    on_claim_created: object,
) -> tuple[object, dict[str, int]]:
    paths = selector.stage2_paths()
    continuation = selector.claim_stage2_namespace(
        authorization, readiness_capability=readiness_capability,
        on_claim_created=on_claim_created,
    )
    activity = dict(authorization["zero_start_activity"])
    return continuation, activity


def _latest_stage2_activity(
    authorization: Mapping[str, Any],
) -> dict[str, int]:
    paths = selector.stage2_paths()
    activity = dict(authorization["zero_start_activity"])
    for phase in (
        "claim", "catalog", "replica_1", "replica_2", "witness", "verifier",
        "manifest",
    ):
        path = paths[f"activity_{phase}"]
        if not path.exists():
            break
        try:
            snapshot = selector.authorized_json(authorization, path)
            if set(snapshot) != {"phase", "activity_counts"} or snapshot["phase"] != phase:
                break
            activity = selector.validate_activity_counts(snapshot["activity_counts"])
        except Exception:
            break
    return activity


def _terminal_failure(
    authorization: Mapping[str, Any], exc: BaseException,
    activity: Mapping[str, Any], *, failure_path: Path,
) -> Mapping[str, Any]:
    failure = {
        "branch": "B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY",
        "error_type": type(exc).__name__, "error": str(exc),
        "activity_counts": selector.validate_activity_counts(activity),
        "retry_authorized": False, "rescue_authorized": False,
        "sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0,
    }
    try:
        if not failure_path.exists():
            selector.write_exclusive(failure_path, _bytes(failure) + b"\n")
        persisted = selector.authorized_json(authorization, failure_path)
        if persisted == failure:
            return persisted
    except Exception:
        pass
    return failure


def _existing_stage2_lifecycle(
    authorization: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    """Terminalize an earlier durable claim/activity; never resume or replay it."""

    paths = selector.stage2_paths()
    if not paths["session_root"].exists():
        return None
    activity = _latest_stage2_activity(authorization)
    exact_claim_exists = False
    if paths["claim"].is_file():
        try:
            claim = selector.authorized_json(authorization, paths["claim"])
            selector.validate_exact_claim(
                claim, authorization, phase="stage2_selector_continuation",
            )
            exact_claim_exists = True
        except Exception:
            exact_claim_exists = False
    if exact_claim_exists or any(activity.values()):
        return _terminal_failure(
            authorization,
            RunnerInvalid("existing Stage-2 claim/activity forbids retry or resume"),
            activity,
            failure_path=paths["stage2_failure"],
        )
    raise RunnerInvalid(
        "preconstructed Stage-2 root lacks an exact claim and durable activity; technical no-start"
    )


def simulate_fixed_root_claim(root: Path) -> Mapping[str, Any]:
    """Synthetic-only exact-once namespace proof for temporary test roots."""

    if root.resolve() == selector.STAGE2_SESSION_ROOT.resolve() or root.exists():
        raise RunnerInvalid("synthetic fixed-root simulation requires one absent temporary root")
    os.mkdir(root)
    marker = root / "synthetic_namespace_claim.json"
    selector.write_exclusive(marker, _bytes({
        "synthetic_only": True, "domain": SYNTHETIC_DOMAIN,
        "sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0,
    }) + b"\n")
    return {"root": str(root.resolve()), "marker": str(marker.resolve()), "synthetic_only": True}


def orchestrate_stage2(stage2_authorization_path: Path) -> Mapping[str, Any]:
    """The only canonical Stage-2 entry: fixed root, exact once, no alternatives."""

    paths = selector.stage2_paths()
    if paths["session_root"].exists():
        initial_authorization = _authorization(stage2_authorization_path)
        existing = _existing_stage2_lifecycle(initial_authorization)
        if existing is not None:
            return existing
    authorization, _readiness, readiness_capability = _preclaim_readiness(
        stage2_authorization_path
    )
    paths = selector.stage2_paths()
    activity = dict(authorization["zero_start_activity"])
    claim_created = False
    def mark_claim_created() -> None:
        nonlocal claim_created
        claim_created = True
    try:
        continuation, activity = _claim_fixed_stage2_namespace(
            authorization, readiness_capability, mark_claim_created
        )
        selector.persist_activity_snapshot(
            authorization, paths, "claim", activity
        )
        universe_spec = experiment.canonical_universe_spec(
            authorization, claim_continuation=continuation
        )
        selector.write_exclusive(paths["universe_spec"], _bytes(universe_spec) + b"\n")
        catalog_capability = selector.begin_catalog_generation(
            authorization, continuation
        )
        rows = []
        generator_counted = False
        for value in experiment.canonical_catalog_rows(
            authorization, catalog_capability=catalog_capability
        ):
            if not generator_counted:
                activity["canonical_generator_calls"] += 1
                generator_counted = True
            rows.append(value)
            activity["canonical_rows_observed"] += 1
        catalog = {"catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": rows}
        selector.parse_catalog(catalog)
        selector.write_exclusive(paths["catalog"], _bytes(catalog) + b"\n")
        selector.persist_activity_snapshot(
            authorization, paths, "catalog", activity
        )
        return selector.run_two_replica_sequence(
            stage2_authorization_path=stage2_authorization_path,
            claim_continuation=continuation, activity_counts=activity,
        )
    except Exception as exc:
        if not claim_created and not any(activity.values()):
            raise
        return _terminal_failure(
            authorization, exc, activity, failure_path=paths["stage2_failure"]
        )


def run_full(
    stage2_authorization_path: Path, selector_receipt_sha256: str,
) -> Mapping[str, Any]:
    paths = selector.stage2_paths()
    if not paths["claim"].is_file():
        raise RunnerInvalid("registered full has no Stage-2 claim; technical no-start")
    authorization = _authorization(stage2_authorization_path)
    try:
        selector.verify_authorized_source_config(authorization)
        _environment_path, environment = selector.load_full_environment_receipt(
            authorization
        )
        selector._require_exhaustive_allowlist(
            authorization, selector.safe_existing_path(stage2_authorization_path),
            paths, environment,
        )
        selector.validate_selector_environment_receipt(authorization, environment)
        experiment.bind_full_environment(authorization, environment)
        stage2_claim = selector.authorized_json(authorization, paths["claim"])
        selector.validate_exact_claim(
            stage2_claim, authorization, phase="stage2_selector_continuation"
        )
        if (
            not isinstance(selector_receipt_sha256, str)
            or len(selector_receipt_sha256) != 64
            or any(char not in "0123456789abcdef" for char in selector_receipt_sha256)
        ):
            raise RunnerInvalid("selector receipt digest anchor must be lowercase 64-hex")
        actual_receipt_sha256 = selector.sha256_authorized_file(
            authorization, paths["receipt"]
        )
        if actual_receipt_sha256 != selector_receipt_sha256:
            raise RunnerInvalid("selector receipt digest anchor mismatch")
        receipt = _authorized_load(authorization, paths["receipt"])
        return experiment.run_registered_full(
            manifest_path=paths["manifest"],
            manifest_content_digest=str(receipt["manifest_content_sha256"]),
            session_root=paths["session_root"], selector_receipt_path=paths["receipt"],
            verifier_report_path=paths["verifier_report"], run_root=paths["registered_full"],
            result_path=paths["result"],
            stage2_authorization=authorization,
            selector_receipt_sha256=selector_receipt_sha256,
            selector_activity_counts=receipt["activity_counts"],
        )
    except Exception as exc:
        return _terminal_failure(
            authorization, exc, _latest_stage2_activity(authorization),
            failure_path=paths["stage2_failure"],
        )

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stage1-status")
    ready = sub.add_parser("stage2-readiness")
    ready.add_argument("--stage2-authorization", required=True)
    select = sub.add_parser("stage2-seal")
    select.add_argument("--stage2-authorization", required=True)
    full = sub.add_parser("run-full")
    full.add_argument("--stage2-authorization", required=True)
    full.add_argument("--selector-receipt-sha256", required=True)
    args = parser.parse_args(argv)
    command = args.command or "stage1-status"
    if command == "stage1-status": result = stage1_status()
    elif command == "stage2-readiness": result = stage2_readiness(Path(args.stage2_authorization))
    elif command == "stage2-seal": result = orchestrate_stage2(Path(args.stage2_authorization))
    else: result = run_full(Path(args.stage2_authorization), args.selector_receipt_sha256)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"branch": selector.INVALID, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
