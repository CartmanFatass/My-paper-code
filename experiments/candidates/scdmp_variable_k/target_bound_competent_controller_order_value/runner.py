"""Foreground-only command line for the frozen TBCC r02 production object."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Sequence

from .lease import PHASE, PYTHON_EXECUTABLE, RUNNER_MODULE
from .native_backend import native_artifact_identity
from .production import (
    ProductionContractError,
    preflight_only,
    run_with_root_lease,
)


def _shared_guard(*args: object, **kwargs: object) -> object:
    from envs.native.production_backend import require_cpp_batched_production

    return require_cpp_batched_production(*args, **kwargs)


def _paths(result_root: Path) -> dict[str, str]:
    root = result_root.resolve()
    return {
        "result_root": str(root),
        "frontier_root": str(root / "frontiers"),
        "source_manifest_path": str(root / "empirical_source_manifest.json"),
        "preactivity_acceptance_path": str(root / "CM_PREACTIVITY_ACCEPTANCE.json"),
        "run_identity_path": str(root / "RUN_IDENTITY.json"),
        "completion_inventory_path": str(root / "COMPLETION_INVENTORY.json"),
        "final_result_path": str(root / "COMPLETE_ATOMIC_RESULT.json"),
        "cm_acceptance_path": str(root / "CM_TECHNICAL_ACCEPTANCE.json"),
    }


def _load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductionContractError(f"cannot load canonical object: {path}") from error
    if not isinstance(value, dict):
        raise ProductionContractError(f"JSON object is required: {path}")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=RUNNER_MODULE,
        description="SCDMP TBCC r02 foreground-only production runner",
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight-only", action="store_true")
    modes.add_argument("--phase", choices=(PHASE,))
    parser.add_argument("--lease", type=Path)
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--result-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(values)
    repository_root = (
        Path(args.repository_root).resolve()
        if args.repository_root is not None
        else Path(__file__).resolve().parents[4]
    )
    if args.preflight_only:
        if args.lease is not None or args.result_root is None:
            raise ProductionContractError(
                "--preflight-only requires --result-root and forbids --lease"
            )
        paths = _paths(args.result_root)
        state = preflight_only(
            repository_root=repository_root,
            source_manifest_path=Path(paths["source_manifest_path"]),
            preactivity_acceptance_path=Path(paths["preactivity_acceptance_path"]),
            output_paths=paths,
            native_identity_loader=native_artifact_identity,
            shared_guard=_shared_guard,
        )
        print(
            json.dumps(
                {
                    "schema": "SCDMP_TBCC_R02_IDENTITY_FREE_PREFLIGHT_CLI_V1",
                    "accepted": True,
                    "source_manifest_sha256": state.source_manifest_sha256,
                    "preactivity_acceptance_sha256": state.preactivity_acceptance_sha256,
                    "native_binding_sha256": state.native_binding_sha256,
                    "materialized": False,
                    "master_present": False,
                    "scientific_activity_started": False,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    if args.phase != PHASE or args.lease is None:
        raise ProductionContractError("production requires exact --phase and --lease")
    if args.result_root is not None or args.repository_root is not None:
        raise ProductionContractError("leased production argv cannot add path overrides")
    lease_path = args.lease.resolve()
    lease = _load_json(lease_path)
    lease_paths = lease.get("paths")
    if not isinstance(lease_paths, dict) or not isinstance(lease_paths.get("result_root"), str):
        raise ProductionContractError("Root lease result paths are absent")
    paths = _paths(Path(lease_paths["result_root"]))
    state = preflight_only(
        repository_root=repository_root,
        source_manifest_path=Path(paths["source_manifest_path"]),
        preactivity_acceptance_path=Path(paths["preactivity_acceptance_path"]),
        output_paths=paths,
        native_identity_loader=native_artifact_identity,
        shared_guard=_shared_guard,
    )
    result_sha = run_with_root_lease(
        lease=lease,
        lease_path=lease_path,
        actual_argv=[PYTHON_EXECUTABLE, "-m", RUNNER_MODULE, *values],
        now=datetime.now(timezone.utc),
        preactivity=state,
        shared_guard=_shared_guard,
        services=None,
    )
    print(
        json.dumps(
            {
                "schema": "SCDMP_TBCC_R02_FOREGROUND_RUN_TERMINAL_V1",
                "complete_result_sha256": result_sha,
                "complete": True,
                "partial_result": False,
                "interpretation_included": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
