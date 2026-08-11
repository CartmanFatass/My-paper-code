"""Stage-1-safe wiring and dormant Stage-2 entry points for VSP06-B2R1."""
from __future__ import annotations
import argparse
import json
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
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def _load(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        value = json.load(stream)
    if not isinstance(value, Mapping):
        raise RunnerInvalid("JSON root is not an object")
    return value

def _authorization(path: Path) -> Mapping[str, Any]:
    path = selector.safe_existing_path(path)
    value = _load(path)
    selector.validate_stage2_authorization(value)
    selector.authorize_read_path(value, path)
    return value

def _authorized_load(authorization: Mapping[str, Any], path: Path) -> Mapping[str, Any]:
    return _load(selector.authorize_read_path(authorization, path))

def stage1_status() -> Mapping[str, Any]:
    return {
        "synthetic_only": True, "domain": SYNTHETIC_DOMAIN, "success_token": SYNTHETIC_SUCCESS,
        "canonical_authorized": False, "full_authorized": False,
        "reserved_paths_absent": all(not path.exists() for path in RESERVED_PATHS),
        "activity": dict(experiment.ACTIVITY_COUNTERS),
        "K_search": 0, "hypothetical_transitions": 0,
    }

def prepare_catalog(output: Path, universe_output: Path, authorization_path: Path) -> Mapping[str, Any]:
    authorization = _authorization(authorization_path)
    if output.exists() or universe_output.exists():
        raise RunnerInvalid("canonical catalog/universe destination already exists")
    rows = list(experiment.canonical_catalog_rows(authorization))
    catalog = {"catalog_id": selector.CATALOG_ID, "salt": selector.SALT, "rows": rows}
    selector.parse_catalog(catalog)
    selector.write_exclusive(output, _bytes(catalog) + b"\n")
    universe={"universe_id":"VSP06-B2R1-INDEPENDENT-CANONICAL-UNIVERSE-V1","salt":selector.SALT,"rows":rows}
    selector.write_exclusive(universe_output, _bytes(universe) + b"\n")
    return {"catalog_path": str(output), "catalog_sha256": selector.sha256_file(output), "universe_path":str(universe_output),"universe_sha256":selector.sha256_file(universe_output),"row_count": len(rows)}

def run_selector(args: argparse.Namespace) -> Mapping[str, Any]:
    authorization = _authorization(Path(args.stage2_authorization))
    counters = _authorized_load(authorization, Path(args.zero_counters))
    if counters != experiment.ACTIVITY_COUNTERS:
        raise RunnerInvalid("zero-start activity binding failed")
    return selector.run_two_replica_sequence(
        catalog_path=Path(args.catalog), ledger_path=Path(args.ledger),
        manifest_path=Path(args.manifest), verifier_path=Path(args.verifier),
        universe_path=Path(args.universe), work_root=Path(args.work_root),
        stage2_authorization_path=Path(args.stage2_authorization),
    )

def run_full(args: argparse.Namespace) -> Mapping[str, Any]:
    authorization = _authorization(Path(args.stage2_authorization))
    for locator in (args.manifest, args.selector_receipt, args.verifier_report):
        selector.authorize_read_path(authorization, Path(locator))
    receipt = _authorized_load(authorization, Path(args.selector_receipt))
    return experiment.run_registered_full(
        manifest_path=Path(args.manifest),
        manifest_content_digest=str(receipt["manifest_content_sha256"]),
        session_root=Path(args.session_root), selector_receipt_path=Path(args.selector_receipt),
        verifier_report_path=Path(args.verifier_report), run_root=Path(args.run_root), result_path=Path(args.result),
        stage2_authorization=authorization,
    )

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stage1-status")
    catalog = sub.add_parser("prepare-catalog")
    catalog.add_argument("--output", required=True); catalog.add_argument("--universe-output", required=True); catalog.add_argument("--stage2-authorization", required=True)
    select = sub.add_parser("select")
    for name in ("catalog", "universe", "ledger", "manifest", "verifier", "work-root", "zero-counters", "stage2-authorization"):
        select.add_argument("--" + name, required=True)
    full = sub.add_parser("run-full")
    for name in ("manifest", "session-root", "selector-receipt", "verifier-report", "run-root", "result", "stage2-authorization"):
        full.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    command = args.command or "stage1-status"
    if command == "stage1-status": result = stage1_status()
    elif command == "prepare-catalog": result = prepare_catalog(Path(args.output), Path(args.universe_output), Path(args.stage2_authorization))
    elif command == "select": result = run_selector(args)
    else: result = run_full(args)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"branch": selector.INVALID, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
