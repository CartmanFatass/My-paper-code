"""Fail-closed source audit and atomic runner boundary for the fresh object."""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable, Mapping, Sequence

from .config import (
    BATCH_SIZE, BUDGETS, INHERITED_ASSUMPTIONS, OBJECT_ID, PRODUCTION_CONFIG,
    RNG_NAMESPACE, SCHEMA_VERSION,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_ROOT / "result.schema.json"
LEGACY_HOST_MODULE = "experiments.candidates.commitment_residual_triggered_options.host"
ALLOWED_LEGACY_HOST_NAMES = frozenset({
    "DecisionKind", "DecisionRecord", "HORIZON", "Option", "Regime", "ScenarioTape",
    "ServiceRelayHost", "balanced_scenario_specs", "build_scenario_tape",
    "common_future_audit_rollout",
})
FORBIDDEN_LEGACY_MODULE_SUFFIXES = frozenset({
    "run", "execution", "training", "evaluation_bridge", "models", "data_bridge",
    "analysis", "controls", "rng", "config", "predictor",
})
FORBIDDEN_CLI_OPTIONS = frozenset({
    "--checkpoint", "--resume", "--legacy-result", "--update-1000",
})


def source_check(package_root: Path = PACKAGE_ROOT) -> dict[str, object]:
    """AST-enforce the isolated legacy allowlist and forbidden route surface."""

    errors: list[str] = []
    checked: list[str] = []
    for path in sorted(Path(package_root).glob("*.py")):
        checked.append(path.name)
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            errors.append(f"{path.name}: syntax error: {error}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                normalized_name = node.name.lower().replace("-", "_")
                if normalized_name in {"resume", "load_checkpoint", "save_checkpoint", "load_legacy_result"}:
                    errors.append(f"{path.name}:{node.lineno}: forbidden external-state function surface")
                argument_names = {
                    argument.arg.lower() for argument in (
                        *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
                    )
                }
                if argument_names.intersection({"resume", "checkpoint_path", "legacy_result", "update_1000"}):
                    errors.append(f"{path.name}:{node.lineno}: forbidden external-state argument surface")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("experiments.candidates.commitment_residual_triggered_options"):
                        errors.append(f"{path.name}:{node.lineno}: direct legacy module import is forbidden")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module == LEGACY_HOST_MODULE:
                    names = {alias.name for alias in node.names}
                    extra = names - ALLOWED_LEGACY_HOST_NAMES
                    if extra:
                        errors.append(f"{path.name}:{node.lineno}: forbidden legacy host names {sorted(extra)}")
                elif node.module.startswith("experiments.candidates.commitment_residual_triggered_options."):
                    suffix = node.module.rsplit(".", 1)[-1]
                    if suffix in FORBIDDEN_LEGACY_MODULE_SUFFIXES or node.module != LEGACY_HOST_MODULE:
                        errors.append(f"{path.name}:{node.lineno}: forbidden legacy module {node.module}")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in {"load", "loads"}:
                    owner = node.func.value
                    if isinstance(owner, ast.Name) and owner.id in {
                        "torch", "np", "numpy", "pickle", "joblib",
                    }:
                        errors.append(f"{path.name}:{node.lineno}: generic persisted-state load is forbidden")
                for argument in (*node.args, *(keyword.value for keyword in node.keywords)):
                    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                        if argument.value in FORBIDDEN_CLI_OPTIONS:
                            errors.append(f"{path.name}:{node.lineno}: forbidden CLI option {argument.value}")
        lowered = source.lower()
        historical_markers = (
            "crto_b1_" + "result.json",
            "crto-b1-" + "probe-v4",
            "update-1,000 " + "continuation",
        )
        for marker in historical_markers:
            if marker in lowered:
                errors.append(f"{path.name}: forbidden historical-state marker {marker!r}")
    if errors:
        raise RuntimeError("source isolation check failed:\n" + "\n".join(errors))
    return {
        "status": "PASS", "object_id": OBJECT_ID, "checked_files": checked,
        "legacy_host_allowlist": sorted(ALLOWED_LEGACY_HOST_NAMES),
    }


def validate_result(result: Mapping[str, object]) -> None:
    try:
        import jsonschema
    except ImportError as error:  # pragma: no cover
        raise RuntimeError("result validation requires jsonschema") from error
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(dict(result))
    if result["status"] != result["analysis"]["status"]:  # type: ignore[index]
        raise ValueError("top-level and analysis status disagree")


def result_skeleton(*, analysis: Mapping[str, object], replicates: Sequence[Mapping[str, object]]) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "object_id": OBJECT_ID,
        "status": analysis["status"],
        "config": {
            "rng_namespace": RNG_NAMESPACE, "replicate_count": 8,
            "short_updates": BUDGETS["SHORT"], "long_updates": BUDGETS["LONG"],
            "batch_size": BATCH_SIZE, "run_config": asdict(PRODUCTION_CONFIG),
        },
        "provenance": {
            "fresh_genesis": True, "legacy_state_reads": False, "legacy_schema": False,
            "inherited_assumptions": dict(INHERITED_ASSUMPTIONS),
        },
        "replicates": list(replicates),
        "analysis": dict(analysis),
        "admission": {
            "disjoint_panels": False, "matched_inputs": False,
            "derangement_valid": False, "common_future_valid": False,
            "raw_long_competent": False,
        },
    }


Executor = Callable[[Path], Mapping[str, object]]


def _missing_scientific_policy_executor(_stage_root: Path) -> Mapping[str, object]:
    """The threshold intentionally left result-sensitive numeric policy unfrozen."""

    analysis = {
        "status": "NONIDENTIFYING", "interpretation": "UNRESOLVED", "intervals": [],
        "failures": [
            "NONIDENTIFYING_INHERITED_ASSUMPTIONS: registered execution stopped before any "
            "optimizer update because predictor, behavior continuation, calibration, gate "
            "initialization, evaluation population, and audit-boundary policies are not "
            "scientifically frozen",
            "NONIDENTIFYING_MISSING_INTERVAL_POLICY: retained-support, RAW-LONG competence, "
            "family alpha, and simultaneous-interval construction are not scientifically frozen"
        ],
    }
    return result_skeleton(analysis=analysis, replicates=({"replicate": index} for index in range(8)))


def _atomic_publish_with_executor(
    output_root: Path,
    result_path: Path,
    *,
    executor: Executor,
    before_publish: Callable[[], None] | None = None,
) -> dict[str, object]:
    """Private Windows no-clobber seam for non-result publication tests."""

    source_check()
    if os.name != "nt":
        raise RuntimeError("registered no-clobber publication is Windows-only")
    output_root = Path(output_root).resolve()
    result_path = Path(result_path).resolve()
    if output_root.exists() or result_path.exists():
        raise FileExistsError("output root and result path must both be fresh")
    if output_root == result_path or output_root in result_path.parents:
        raise ValueError("result path must be outside the atomic output root")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=output_root.name + ".stage.", dir=output_root.parent))
    result_descriptor, result_temporary_name = tempfile.mkstemp(
        prefix=result_path.name + ".", suffix=".tmp", dir=result_path.parent,
    )
    os.close(result_descriptor)
    result_temporary = Path(result_temporary_name)
    try:
        payload = dict(executor(stage))
        validate_result(payload)
        provenance = payload.get("provenance")
        analysis = payload.get("analysis")
        admission = payload.get("admission")
        expected_admission = {
            "disjoint_panels", "matched_inputs", "derangement_valid",
            "common_future_valid", "raw_long_competent",
        }
        if (
            payload.get("status") != "NONIDENTIFYING"
            or not isinstance(provenance, Mapping)
            or provenance.get("inherited_assumptions") != dict(INHERITED_ASSUMPTIONS)
            or not isinstance(analysis, Mapping)
            or analysis.get("status") != "NONIDENTIFYING"
            or analysis.get("interpretation") != "UNRESOLVED"
            or analysis.get("intervals") != []
            or not isinstance(admission, Mapping)
            or set(admission) != expected_admission
            or any(value is not False for value in admission.values())
        ):
            raise PermissionError(
                "private publication seam accepts only structural NONIDENTIFYING fixtures "
                "under the exact inherited-assumption receipt"
            )
        result_temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        # Recheck freshness immediately before either atomic publication.
        if output_root.exists() or result_path.exists():
            raise FileExistsError("fresh publication target appeared during execution")
        if before_publish is not None:
            before_publish()
        # On Windows os.rename is atomic and fails if the destination exists;
        # unlike os.replace it cannot clobber a concurrent creator.
        os.rename(stage, output_root)
        try:
            os.rename(result_temporary, result_path)
        except BaseException:
            # Publication is recoverable without deleting user data: move our
            # newly published root back to its unique staging name.
            os.rename(output_root, stage)
            raise
        return payload
    finally:
        if stage.exists():
            if stage.resolve().parent != output_root.parent.resolve() or not stage.name.startswith(
                output_root.name + ".stage."
            ):
                raise RuntimeError("refusing to clean an unexpected staging path")
            shutil.rmtree(stage)
        if result_temporary.exists():
            result_temporary.unlink()


def run_registered(output_root: Path, result_path: Path) -> dict[str, object]:
    """Enforce current admission before work, optimizer updates, or publication."""

    source_check()
    _ = (Path(output_root), Path(result_path))
    raise PermissionError(
        "NONIDENTIFYING_INHERITED_ASSUMPTIONS: run admission is blocked before any optimizer "
        "update or output until predictor, behavior continuation, calibration population, "
        "gate initialization, evaluation population, audit boundary, retained support, "
        "RAW-LONG competence, and interval policies are scientifically frozen"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=OBJECT_ID)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("source-check")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--output-root", type=Path, required=True)
    run_parser.add_argument("--result", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.action == "source-check":
        print(json.dumps(source_check(), indent=2, sort_keys=True))
        return 0
    run_registered(arguments.output_root, arguments.result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
