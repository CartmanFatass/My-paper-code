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

def _claim_fixed_stage2_namespace(authorization: Mapping[str, Any]) -> None:
    paths = selector.stage2_paths()
    root = paths["session_root"]
    if root.exists():
        raise RunnerInvalid("fixed Stage-2 namespace already exists; retry/overwrite is forbidden")
    try:
        os.mkdir(root)
    except FileExistsError as exc:
        raise RunnerInvalid("fixed Stage-2 namespace claim was not exclusive") from exc
    claim = {
        "treatment": selector.TREATMENT_ID,
        "final_commit": authorization["final_commit"],
        "stage2_authorization_sha256": selector.sha256_bytes(_bytes(authorization)),
        "ordinal": 1,
        "activity_accounting": {"sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0},
    }
    selector.write_exclusive(paths["claim"], _bytes(claim) + b"\n")


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

    authorization = _authorization(stage2_authorization_path)
    selector.verify_authorized_source_config(authorization)
    if authorization["zero_start_activity"] != experiment.ACTIVITY_COUNTERS:
        raise RunnerInvalid("zero-start activity binding failed")
    _claim_fixed_stage2_namespace(authorization)
    paths = selector.stage2_paths()
    universe_spec = experiment.canonical_universe_spec(authorization)
    selector.write_exclusive(paths["universe_spec"], _bytes(universe_spec) + b"\n")
    rows = list(experiment.canonical_catalog_rows(authorization))
    catalog = {"catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": rows}
    selector.parse_catalog(catalog)
    selector.write_exclusive(paths["catalog"], _bytes(catalog) + b"\n")
    return selector.run_two_replica_sequence(
        stage2_authorization_path=stage2_authorization_path
    )


def run_full(
    stage2_authorization_path: Path, selector_receipt_sha256: str,
) -> Mapping[str, Any]:
    authorization = _authorization(stage2_authorization_path)
    paths = selector.stage2_paths()
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
    run_root = paths["session_root"] / "registered_full"
    result_path = RESERVED_PATHS[0]
    return experiment.run_registered_full(
        manifest_path=paths["manifest"],
        manifest_content_digest=str(receipt["manifest_content_sha256"]),
        session_root=paths["session_root"], selector_receipt_path=paths["receipt"],
        verifier_report_path=paths["verifier_report"], run_root=run_root,
        result_path=result_path,
        stage2_authorization=authorization,
        selector_receipt_sha256=selector_receipt_sha256,
    )

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stage1-status")
    select = sub.add_parser("stage2-seal")
    select.add_argument("--stage2-authorization", required=True)
    full = sub.add_parser("run-full")
    full.add_argument("--stage2-authorization", required=True)
    full.add_argument("--selector-receipt-sha256", required=True)
    args = parser.parse_args(argv)
    command = args.command or "stage1-status"
    if command == "stage1-status": result = stage1_status()
    elif command == "stage2-seal": result = orchestrate_stage2(Path(args.stage2_authorization))
    else: result = run_full(Path(args.stage2_authorization), args.selector_receipt_sha256)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"branch": selector.INVALID, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
