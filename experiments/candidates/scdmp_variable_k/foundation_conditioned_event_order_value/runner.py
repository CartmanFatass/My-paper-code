"""Result-blind FCEOV preflight CLI with no empirical phase command."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from .contracts import Manifest
from .foundation import validate_competence_rng_contract
from .host_bridge import headroom_conformance, verify_public_alias
from .panel import build_native_resets, build_panel_inventory, validate_tape_pairing
from .source_manifest import load_source_manifest
from .training import build_training_plan, summarize_resource_usage, validate_training_rng_contract


class PreflightError(RuntimeError):
    pass


def run_preflight(*, manifest: str | Path, result_root: str | Path) -> dict[str, object]:
    loaded = load_source_manifest(manifest)
    loaded.validate()
    root = Path(result_root)
    if root.exists():
        raise PreflightError("prospective result-root must not exist; it must be absent and fresh")
    parent = root.parent
    if not parent.exists() or not parent.is_dir():
        raise PreflightError("result-root parent does not exist")
    plan = build_training_plan()
    inventory = build_panel_inventory()
    validate_tape_pairing(inventory)
    resets = build_native_resets(inventory)
    training_rng = validate_training_rng_contract()
    competence_rng = validate_competence_rng_contract()
    alias = verify_public_alias()
    headroom = headroom_conformance()
    return {
        "manifest": loaded.to_dict(),
        "training_episodes": len(plan),
        "panel_width": len(inventory),
        "reset_width": len(resets),
        "public_alias": alias[0] == alias[1],
        "headroom": {
            "analytic_matched_load": headroom.analytic_witness.matched_load,
            "analytic_mismatched_load": headroom.analytic_witness.mismatched_load,
            "analytic_common_maximum_load": headroom.analytic_witness.common_maximum_load,
            "native_matched_exposure_zero": headroom.native_matched_exposure_zero,
            "native_mismatched_exposure": headroom.native_mismatched_exposure,
            "native_common_exposure_zero": headroom.native_common_exposure_zero,
        },
        "resources": summarize_resource_usage(),
        "training_rng_addresses": training_rng,
        "competence_rng_addresses": competence_rng,
        "result_root_absent": True,
        "production_result_path_implemented": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scdmp-fceov")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--result-root", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.preflight_only:
        parser.error("only --preflight-only is implemented; every result-bearing invocation is refused")
    try:
        run_preflight(manifest=args.manifest, result_root=args.result_root)
    except (ValueError, RuntimeError, OSError) as error:
        print(f"FCEOV preflight failed: {error}", file=sys.stderr)
        return 1
    print("FCEOV result-blind preflight passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["PreflightError", "main", "run_preflight"]
