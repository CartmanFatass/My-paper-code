"""Fail-closed source audit and atomic runner boundary for the fresh object."""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Mapping, Sequence

from .config import (
    BATCH_SIZE, BUDGETS, DELTA, FROZEN_POLICIES, NUMERIC_TOLERANCE, OBJECT_ID,
    PEAK_RSS_BYTES, PRODUCTION_CONFIG, RAW_LONG_MAX_MEAN_REGRET, RNG_NAMESPACE,
    PILOT_OBJECT_ID, SCHEMA_VERSION, SUPPORT_CENSUS_OBJECT_ID, WALL_SECONDS,
    refuse_consumed_support_census,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_ROOT / "result.schema.json"
LEGACY_HOST_MODULE = "experiments.candidates.commitment_residual_triggered_options.host"
ALLOWED_LEGACY_HOST_NAMES = frozenset({
    "DecisionKind", "DecisionRecord", "EventClass", "FIXED_ONSETS", "HORIZON", "Option",
    "Regime", "ScenarioSpec", "ScenarioTape", "ServiceRelayHost", "balanced_scenario_specs",
    "build_scenario_tape",
    "common_future_audit_rollout",
})
FORBIDDEN_LEGACY_MODULE_SUFFIXES = frozenset({
    "run", "execution", "training", "evaluation_bridge", "models", "data_bridge",
    "analysis", "controls", "rng", "config", "predictor",
})
FORBIDDEN_CLI_OPTIONS = frozenset({
    "--checkpoint", "--resume", "--legacy-result", "--update-1000",
})
PRE_ADMISSION_TORCH_DEPENDENCY_SUFFIXES = frozenset({
    "torch", "analysis", "calibration", "derangement", "evaluation", "models",
    "packets", "pilot", "production", "training",
})
IMPORT_SAFE_TRANSACTION_MODULES = frozenset({
    "pilot.py", "production.py", "support_census.py", "support_census_worker.py",
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
        if path.name in IMPORT_SAFE_TRANSACTION_MODULES:
            for node in tree.body:
                imported: tuple[str, ...] = ()
                if isinstance(node, ast.Import):
                    imported = tuple(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imported = (
                        (node.module,)
                        if node.module
                        else tuple(alias.name for alias in node.names)
                    )
                if any(
                    name.split(".")[-1] in PRE_ADMISSION_TORCH_DEPENDENCY_SUFFIXES
                    for name in imported
                ):
                    errors.append(
                        f"{path.name}: top-level Torch-dependent import violates "
                        "pre-admission capability"
                    )
        lowered = source.lower()
        historical_markers = (
            "crto_b1_" + "result.json",
            "crto-b1-" + "probe-v4",
            "update-1,000 " + "continuation",
        )
        for marker in historical_markers:
            if marker in lowered:
                errors.append(f"{path.name}: forbidden historical-state marker {marker!r}")
    try:
        from .preflight import validate_production_capability
        errors.extend(validate_production_capability())
    except Exception as error:
        errors.append(f"production capability check failed: {type(error).__name__}: {error}")
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
    replicates = result["replicates"]
    if not isinstance(replicates, Sequence) or [row.get("replicate") for row in replicates] != list(range(8)):  # type: ignore[union-attr]
        raise ValueError("result outer replicate ids must be exactly ordered 0..7")
    analysis = result["analysis"]
    assert isinstance(analysis, Mapping)
    provenance = result["provenance"]
    assert isinstance(provenance, Mapping)
    from .preflight import EXPECTED_PRODUCTION_CAPABILITY
    if provenance.get("production_capability") != dict(EXPECTED_PRODUCTION_CAPABILITY):
        raise ValueError("result provenance lacks the exact frozen production capability")
    hulls = [*analysis.get("effect_hulls", []), *analysis.get("trajectory_hulls", [])]  # type: ignore[misc]
    by_key: dict[tuple[str, str], tuple[float, ...]] = {}
    serialized_keys: list[tuple[str, str]] = []
    for hull in hulls:
        if not isinstance(hull, Mapping):
            raise ValueError("effect hull must be an object")
        effects = tuple(float(value) for value in hull["slot_effects"])  # type: ignore[index]
        lower, upper = min(effects), max(effects)
        mean = sum(effects) / 8.0
        if (
            len(effects) != 8
            or not math.isclose(float(hull["lower"]), lower, rel_tol=0.0, abs_tol=1e-12)
            or not math.isclose(float(hull["upper"]), upper, rel_tol=0.0, abs_tol=1e-12)
            or not math.isclose(float(hull["width"]), upper - lower, rel_tol=0.0, abs_tol=1e-12)
            or not math.isclose(float(hull["descriptive_mean"]), mean, rel_tol=0.0, abs_tol=1e-12)
        ):
            raise ValueError("effect hull extrema, width, or descriptive mean was not recomputed")
        key = (str(hull["contrast"]), str(hull["budget"]))
        serialized_keys.append(key)
        by_key[key] = effects
    if len(serialized_keys) != len(set(serialized_keys)):
        raise ValueError("serialized effect hull keys must be unique")
    for budget in ("SHORT", "LONG"):
        rt = by_key.get(("RAW_MINUS_TRUE", budget))
        rd = by_key.get(("RAW_MINUS_DERANGED", budget))
        dt = by_key.get(("DERANGED_MINUS_TRUE", budget))
        if any(value is not None for value in (rt, rd, dt)):
            if rt is None or rd is None or dt is None or any(
                not math.isclose(left, middle + right, rel_tol=0.0, abs_tol=1e-12)
                for left, middle, right in zip(rt, rd, dt)
            ):
                raise ValueError("serialized contrast identity x_RT=x_RD+x_DT failed")
    competence = analysis.get("raw_long_competence")
    if competence is not None:
        if not isinstance(competence, Mapping):
            raise ValueError("RAW-LONG competence report must be an object")
        cells = competence.get("cells")
        if not isinstance(cells, Sequence):
            raise ValueError("RAW-LONG competence cells are missing")
        identities = [(cell["slot"], cell["stratum"]) for cell in cells]  # type: ignore[index]
        expected = [(slot, stratum) for slot in range(8) for stratum in (
            "KEEP_MATERIAL", "REPLAN_MATERIAL",
        )]
        if identities != expected:
            raise ValueError("RAW-LONG competence cells must be slot-major exact 0..7")
        raw_means = [float(cell["raw_mean_regret"]) for cell in cells]  # type: ignore[index]
        raw_minus_script = [
            float(cell["raw_mean_regret"]) - float(cell["script_mean_regret"])
            for cell in cells  # type: ignore[index]
        ]
        if not math.isclose(float(competence["c_raw"]), max(raw_means), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("RAW-LONG c_raw does not equal the 16-cell maximum")
        if not math.isclose(
            float(competence["max_raw_minus_script"]), max(raw_minus_script),
            rel_tol=0.0, abs_tol=1e-12,
        ):
            raise ValueError("RAW-LONG script comparison maximum was not recomputed")
        if any(
            not math.isclose(float(cell["raw_minus_script"]), difference, rel_tol=0.0, abs_tol=1e-12)
            for cell, difference in zip(cells, raw_minus_script)  # type: ignore[arg-type]
        ):
            raise ValueError("RAW-LONG per-cell raw-minus-script identity failed")
    admission = result["admission"]
    resource = result["resource"]
    ledger = result["ledger"]
    runtime = result["runtime"]
    assert isinstance(admission, Mapping) and isinstance(resource, Mapping)
    assert isinstance(ledger, Mapping) and isinstance(runtime, Mapping)
    if admission.get("resource_valid") is True and not (
        resource.get("memory_floor_pass") is True
        and int(resource.get("available_physical_bytes", 0)) >= 4 * 1024**3
        and int(resource.get("effective_available_bytes", 0)) >= 4 * 1024**3
    ):
        raise ValueError("resource_valid is inconsistent with the retained 4-GiB receipt")
    if admission.get("ledger_valid") is True and not (
        ledger.get("pre_result_exact") is True
        and ledger.get("within_ceiling") is True
        and ledger.get("formula") == "8*1088*256 + 16*actual_common_future_branch_count"
        and int(ledger.get("charged_full_tape_primitive_team_steps", -1)) == 2_228_224
        and int(ledger.get("common_future_steps_per_actual_branch", -1)) == 16
        and int(ledger.get("expected_common_future_branch_count", -1))
        == int(ledger.get("actual_common_future_branch_count", -2))
        and int(ledger.get("actual_common_future_steps", -1))
        == 16 * int(ledger.get("actual_common_future_branch_count", -2))
        and int(ledger.get("actual_total_steps", -1))
        == 2_228_224 + int(ledger.get("actual_common_future_steps", -2))
        and int(ledger.get("actual_total_steps", -1)) <= int(ledger.get("ceiling", -2))
    ):
        raise ValueError("ledger_valid is inconsistent with the retained exact ledger")
    if admission.get("runtime_valid") is True and not (
        runtime.get("workers") == 1 and runtime.get("threads_per_worker") == 1
        and int(runtime.get("peak_rss_bytes", PEAK_RSS_BYTES + 1)) <= PEAK_RSS_BYTES
        and float(runtime.get("wall_seconds", WALL_SECONDS + 1)) <= WALL_SECONDS
    ):
        raise ValueError("runtime_valid is inconsistent with the retained runtime receipt")

    status = str(result["status"])
    interpretation = str(analysis["interpretation"])
    effect_keys = {
        (contrast, budget)
        for contrast in ("RAW_MINUS_TRUE", "DERANGED_MINUS_TRUE", "RAW_MINUS_DERANGED")
        for budget in ("SHORT", "LONG")
    }
    trajectory_keys = {("RAW_GAIN", "LONG"), ("TRUE_DEGRADE", "LONG")}
    if status == "IDENTIFYING":
        base_regrets: list[dict[tuple[str, str], float]] = []
        required_cells = {
            (representation, budget)
            for representation in ("RAW", "TRUE_RESIDUAL", "CALIBRATED_DERANGEMENT")
            for budget in ("SHORT", "LONG")
        }
        for slot, replicate in enumerate(replicates):
            if not isinstance(replicate, Mapping):
                raise ValueError("replicate result must be an object")
            evaluations = replicate.get("evaluations")
            if not isinstance(evaluations, Sequence) or len(evaluations) != 6:
                raise ValueError("IDENTIFYING result requires exact six evaluation cells per slot")
            values: dict[tuple[str, str], float] = {}
            for summary in evaluations:
                if not isinstance(summary, Mapping) or summary.get("replicate") != slot:
                    raise ValueError("evaluation cell is not bound to its outer replicate slot")
                key = (str(summary.get("representation")), str(summary.get("budget")))
                if key in values or key not in required_cells:
                    raise ValueError("evaluation cells are duplicated or outside the frozen six")
                regimes = summary.get("regime_mean_regret")
                if not isinstance(regimes, Mapping) or set(regimes) != {
                    "K8", "K16", "K4_TO_16", "K16_TO_4",
                }:
                    raise ValueError("complete evaluation cell requires exactly four regime means")
                target = sum(float(regimes[name]) for name in (
                    "K16", "K4_TO_16", "K16_TO_4",
                )) / 3.0
                if not math.isfinite(target) or target < 0.0 or any(
                    not math.isfinite(float(value)) or float(value) < 0.0
                    for value in regimes.values()
                ):
                    raise ValueError("evaluation base regrets must be finite and nonnegative")
                if not math.isclose(
                    float(summary.get("target_equal_weight_regret", float("nan"))),
                    target,
                    rel_tol=0.0,
                    abs_tol=NUMERIC_TOLERANCE,
                ):
                    raise ValueError("target equal-weight regret was not recomputed from regimes")
                values[key] = target
            if set(values) != required_cells:
                raise ValueError("IDENTIFYING result lacks the exact six evaluation cells")
            if (
                not isinstance(replicate.get("derangements"), Mapping)
                or set(replicate["derangements"]) != {"TRAIN", "EVALUATION"}
            ):
                raise ValueError("IDENTIFYING result requires persisted derangement plans")
            base_regrets.append(values)

        expected_slot_effects = {
            ("RAW_MINUS_TRUE", budget): tuple(
                slot[("RAW", budget)] - slot[("TRUE_RESIDUAL", budget)]
                for slot in base_regrets
            )
            for budget in ("SHORT", "LONG")
        }
        expected_slot_effects.update({
            ("DERANGED_MINUS_TRUE", budget): tuple(
                slot[("CALIBRATED_DERANGEMENT", budget)]
                - slot[("TRUE_RESIDUAL", budget)]
                for slot in base_regrets
            )
            for budget in ("SHORT", "LONG")
        })
        expected_slot_effects.update({
            ("RAW_MINUS_DERANGED", budget): tuple(
                slot[("RAW", budget)]
                - slot[("CALIBRATED_DERANGEMENT", budget)]
                for slot in base_regrets
            )
            for budget in ("SHORT", "LONG")
        })
        expected_slot_effects[("RAW_GAIN", "LONG")] = tuple(
            slot[("RAW", "SHORT")] - slot[("RAW", "LONG")]
            for slot in base_regrets
        )
        expected_slot_effects[("TRUE_DEGRADE", "LONG")] = tuple(
            slot[("TRUE_RESIDUAL", "LONG")] - slot[("TRUE_RESIDUAL", "SHORT")]
            for slot in base_regrets
        )
        if set(by_key) != set(expected_slot_effects) or any(
            any(
                not math.isclose(left, right, rel_tol=0.0, abs_tol=NUMERIC_TOLERANCE)
                for left, right in zip(by_key[key], expected)
            )
            for key, expected in expected_slot_effects.items()
        ):
            raise ValueError("analysis hull slot effects disagree with replicate base regrets")
        if set(serialized_keys[:len(analysis.get("effect_hulls", []))]) != effect_keys:
            raise ValueError("IDENTIFYING result requires the exact six contrast hulls")
        if set(serialized_keys[len(analysis.get("effect_hulls", [])):]) != trajectory_keys:
            raise ValueError("IDENTIFYING result requires the exact two trajectory hulls")
        if len(analysis.get("effect_hulls", [])) != 6 or len(analysis.get("trajectory_hulls", [])) != 2:
            raise ValueError("IDENTIFYING result requires six effect and two trajectory hulls")
        if competence is None or float(competence["c_raw"]) > (
            RAW_LONG_MAX_MEAN_REGRET + NUMERIC_TOLERANCE
        ):
            raise ValueError("IDENTIFYING result requires competent RAW-LONG in all sixteen cells")
        if analysis.get("failures") != []:
            raise ValueError("IDENTIFYING result cannot retain admission failures")
        required_admission = {
            "disjoint_panels", "matched_inputs", "derangement_valid", "common_future_valid",
            "raw_long_competent", "resource_valid", "ledger_valid", "runtime_valid",
            "calibration_valid", "k8_competence_support_valid",
        }
        if set(admission) != required_admission or any(
            admission[name] is not True for name in required_admission
        ):
            raise ValueError("IDENTIFYING result requires every frozen admission predicate")

        rt_short = by_key[("RAW_MINUS_TRUE", "SHORT")]
        rt_long = by_key[("RAW_MINUS_TRUE", "LONG")]
        raw_gain = by_key[("RAW_GAIN", "LONG")]
        true_degrade = by_key[("TRUE_DEGRADE", "LONG")]
        if any(
            not math.isclose(
                rt_short[index] - rt_long[index],
                raw_gain[index] + true_degrade[index],
                rel_tol=0.0,
                abs_tol=NUMERIC_TOLERANCE,
            )
            for index in range(8)
        ):
            raise ValueError(
                "serialized trajectory identity RT_SHORT-RT_LONG=RAW_GAIN+TRUE_DEGRADE failed"
            )

        def _lower(contrast: str, budget: str) -> float:
            return min(by_key[(contrast, budget)])

        def _upper(contrast: str, budget: str) -> float:
            return max(by_key[(contrast, budget)])

        def _sup(contrast: str, budget: str) -> bool:
            return _lower(contrast, budget) > DELTA

        def _eq(contrast: str, budget: str) -> bool:
            return _lower(contrast, budget) >= -DELTA and _upper(contrast, budget) <= DELTA

        if (
            _sup("RAW_MINUS_TRUE", "SHORT")
            and _sup("RAW_MINUS_TRUE", "LONG")
            and _sup("DERANGED_MINUS_TRUE", "SHORT")
            and _sup("DERANGED_MINUS_TRUE", "LONG")
        ):
            recomputed = "PERSISTENT_ALIGNED_BIAS"
        elif (
            _sup("RAW_MINUS_TRUE", "SHORT")
            and _sup("RAW_MINUS_TRUE", "LONG")
            and _sup("RAW_MINUS_DERANGED", "SHORT")
            and _sup("RAW_MINUS_DERANGED", "LONG")
            and _eq("DERANGED_MINUS_TRUE", "SHORT")
            and _eq("DERANGED_MINUS_TRUE", "LONG")
        ):
            recomputed = "GENERIC_PREPROCESSING"
        elif (
            _sup("RAW_MINUS_TRUE", "SHORT")
            and _sup("DERANGED_MINUS_TRUE", "SHORT")
            and _eq("RAW_MINUS_TRUE", "LONG")
            and _eq("DERANGED_MINUS_TRUE", "LONG")
            and _eq("RAW_MINUS_DERANGED", "LONG")
            and min(raw_gain) > DELTA
            and max(true_degrade) <= DELTA
        ):
            recomputed = "OPTIMIZATION_EXPOSURE_ONLY"
        elif (
            _upper("RAW_MINUS_TRUE", "SHORT") <= DELTA
            and _upper("RAW_MINUS_TRUE", "LONG") <= DELTA
        ):
            recomputed = "CLOSE_TESTED_MECHANISM"
        else:
            recomputed = "UNRESOLVED"
        if interpretation != recomputed:
            raise ValueError("serialized interpretation disagrees with the exact first-match law")

        close_descriptions = analysis.get("close_budget_descriptions")
        if recomputed == "CLOSE_TESTED_MECHANISM":
            expected_close: dict[str, str] = {}
            for budget in ("SHORT", "LONG"):
                if _upper("RAW_MINUS_TRUE", budget) < -DELTA:
                    expected_close[budget] = "RAW_SUPERIOR"
                elif _eq("RAW_MINUS_TRUE", budget):
                    expected_close[budget] = "PRACTICAL_EQUIVALENCE"
                else:
                    expected_close[budget] = "MIXED_OR_SMALL_TRUE_EFFECT"
            if close_descriptions != expected_close:
                raise ValueError("serialized CLOSE budget descriptions disagree with the hulls")
        elif close_descriptions is not None:
            raise ValueError("non-CLOSE result cannot retain CLOSE budget descriptions")
    else:
        if interpretation not in {
            "UNRESOLVED", "NONIDENTIFYING_K8_COMPETENCE_SUPPORT",
            "STOP_RAW_LONG_INCOMPETENT",
        }:
            raise ValueError("NONIDENTIFYING result cannot serialize a polarity branch")
        if analysis.get("failures") in (None, []):
            raise ValueError("NONIDENTIFYING result requires explicit failures")
        if analysis.get("effect_hulls") != [] or analysis.get("trajectory_hulls") != []:
            raise ValueError("NONIDENTIFYING result cannot retain decision-bearing hulls")
        if analysis.get("close_budget_descriptions") is not None:
            raise ValueError("NONIDENTIFYING result cannot retain CLOSE descriptions")
        if interpretation == "NONIDENTIFYING_K8_COMPETENCE_SUPPORT" and competence is not None:
            raise ValueError("K8 support failure cannot claim a complete competence report")
        if interpretation == "STOP_RAW_LONG_INCOMPETENT" and (
            competence is None
            or float(competence["c_raw"]) <= RAW_LONG_MAX_MEAN_REGRET + NUMERIC_TOLERANCE
        ):
            raise ValueError("RAW-LONG STOP requires a complete failing competence report")
        for slot, replicate in enumerate(replicates):
            if not isinstance(replicate, Mapping):
                raise ValueError("replicate result must be an object")
            if "derangements" in replicate:
                raise ValueError("NONIDENTIFYING result cannot serialize derangement plans")
            evaluations = replicate.get("evaluations")
            if interpretation == "UNRESOLVED":
                if evaluations is not None:
                    raise ValueError(
                        "structural/calibration NONIDENTIFYING result cannot serialize evaluations"
                    )
                continue
            if not isinstance(evaluations, Sequence) or len(evaluations) != 1:
                raise ValueError(
                    "competence NONIDENTIFYING result requires exact one RAW-LONG K8 evaluation"
                )
            summary = evaluations[0]
            if (
                not isinstance(summary, Mapping)
                or summary.get("replicate") != slot
                or summary.get("representation") != "RAW"
                or summary.get("budget") != "LONG"
                or not isinstance(summary.get("regime_mean_regret"), Mapping)
                or set(summary["regime_mean_regret"]) != {"K8"}
                or not isinstance(summary.get("row_count_by_regime"), Mapping)
                or set(summary["row_count_by_regime"]) != {"K8"}
            ):
                raise ValueError(
                    "competence NONIDENTIFYING result permits only exact RAW-LONG K8 evaluations"
                )


def result_skeleton(
    *,
    analysis: Mapping[str, object],
    replicates: Sequence[Mapping[str, object]],
    resource: Mapping[str, object],
    ledger: Mapping[str, object],
    runtime: Mapping[str, object],
    admission: Mapping[str, object],
) -> dict[str, object]:
    """Assemble only caller-supplied evidence; never synthesize production receipts."""

    from .preflight import EXPECTED_PRODUCTION_CAPABILITY
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
            "frozen_policies": dict(FROZEN_POLICIES),
            "production_capability": dict(EXPECTED_PRODUCTION_CAPABILITY),
        },
        "replicates": list(replicates),
        "analysis": dict(analysis),
        "resource": dict(resource),
        "ledger": dict(ledger),
        "runtime": dict(runtime),
        "admission": dict(admission),
    }


Executor = Callable[[Path], Mapping[str, object]]


def _launch_production_worker(
    *,
    output_root: Path,
    result_path: Path,
    preflight_receipt_path: Path,
    launch_resource_receipt_path: Path,
    launch_run_resource_receipt_path: Path,
) -> dict[str, object]:
    """Run the sole scientific worker with native thread limits set before import."""

    command = [
        sys.executable,
        "-m",
        (
            "experiments.candidates."
            "commitment_residual_triggered_options_common_history_gate_r01.production_worker"
        ),
        "--output-root", str(Path(output_root).resolve()),
        "--result", str(Path(result_path).resolve()),
        "--preflight-receipt", str(Path(preflight_receipt_path).resolve()),
        "--launch-resource-receipt", str(Path(launch_resource_receipt_path).resolve()),
        "--launch-run-resource-receipt", str(Path(launch_run_resource_receipt_path).resolve()),
    ]
    environment = os.environ.copy()
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        environment[name] = "1"
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["HMASD_CRTO_PRODUCTION_WORKER"] = OBJECT_ID
    completed = subprocess.run(
        command,
        cwd=PACKAGE_ROOT.parents[2],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or (
            f"exit {completed.returncode}"
        )
        raise RuntimeError(f"CRTO isolated production worker failed: {detail}")
    try:
        acknowledgement = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "CRTO isolated production worker returned invalid acknowledgement"
        ) from error
    if acknowledgement != {"status": "PUBLISHED", "object_id": OBJECT_ID}:
        raise RuntimeError("CRTO isolated production worker acknowledgement drifted")
    try:
        payload = json.loads(Path(result_path).resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("CRTO isolated production result is unreadable") from error
    if not isinstance(payload, Mapping):
        raise RuntimeError("CRTO isolated production result must be a JSON object")
    validate_result(payload)
    return dict(payload)


def _launch_raw_pilot_worker(
    *,
    output_root: Path,
    result_path: Path,
    resource_receipt_path: Path,
    launch_resource_receipt_path: Path,
    launch_run_resource_receipt_path: Path,
) -> dict[str, object]:
    """Launch the fixed pilot without importing Torch into the parent process."""

    output, result, memory, launch_memory, launch_assessment = tuple(
        Path(path).resolve() for path in (
            output_root, result_path, resource_receipt_path,
            launch_resource_receipt_path, launch_run_resource_receipt_path,
        )
    )
    if len({output, result, memory, launch_memory, launch_assessment}) != 5:
        raise ValueError("pilot root, result, and resource receipts must be distinct")
    if any(path.exists() for path in (
        output, result, memory, launch_memory, launch_assessment,
    )):
        raise FileExistsError("pilot requires fresh create-only targets and receipts")
    if any(output == path or output in path.parents for path in (
        result, memory, launch_memory, launch_assessment,
    )):
        raise ValueError("pilot result and resource receipts must be outside the output root")
    environment = os.environ.copy()
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        environment[name] = "1"
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["HMASD_CRTO_PILOT_WORKER"] = PILOT_OBJECT_ID
    completed = subprocess.run(
        [
            sys.executable, "-m",
            (
                "experiments.candidates."
                "commitment_residual_triggered_options_common_history_gate_r01.pilot"
            ),
            "--worker",
            "--output-root", str(output),
            "--result", str(result),
            "--resource-receipt", str(memory),
            "--launch-resource-receipt", str(launch_memory),
            "--launch-run-resource-receipt", str(launch_assessment),
        ],
        cwd=PACKAGE_ROOT.parents[2],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or (
            f"exit {completed.returncode}"
        )
        raise RuntimeError(f"isolated CRTO pilot worker failed: {detail}")
    try:
        payload = json.loads(result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("CRTO pilot worker did not publish a readable result") from error
    if not isinstance(payload, Mapping):
        raise RuntimeError("CRTO pilot worker result must be a JSON object")
    from .pilot import validate_pilot_result
    validate_pilot_result(payload)
    return dict(payload)


def _launch_support_census_worker(
    *,
    output_root: Path,
    result_path: Path,
    resource_receipt_path: Path,
    run_resource_receipt_path: Path,
) -> dict[str, object]:
    """Launch the frozen support-only census in one import-safe isolated worker."""

    refuse_consumed_support_census()
    source_check()
    output, result, memory, assessment = tuple(
        Path(path).resolve() for path in (
            output_root, result_path, resource_receipt_path, run_resource_receipt_path,
        )
    )
    if len({output, result, memory, assessment}) != 4:
        raise ValueError("support census root, result, and resource receipts must be distinct")
    if any(path.exists() for path in (output, result, memory, assessment)):
        raise FileExistsError("support census requires fresh create-only targets and receipts")
    if any(output == path or output in path.parents for path in (result, memory, assessment)):
        raise ValueError("support census result and resource receipts must be outside output root")
    environment = os.environ.copy()
    for name in (
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
    ):
        environment[name] = "1"
    environment["CUDA_VISIBLE_DEVICES"] = ""
    environment["HMASD_CRTO_SUPPORT_CENSUS_WORKER"] = SUPPORT_CENSUS_OBJECT_ID
    completed = subprocess.run(
        [
            sys.executable, "-m",
            (
                "experiments.candidates."
                "commitment_residual_triggered_options_common_history_gate_r01."
                "support_census_worker"
            ),
            "--output-root", str(output),
            "--result", str(result),
            "--resource-receipt", str(memory),
            "--run-resource-receipt", str(assessment),
        ],
        cwd=PACKAGE_ROOT.parents[2],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or (
            f"exit {completed.returncode}"
        )
        raise RuntimeError(f"isolated CRTO support census worker failed: {detail}")
    receipt = output / "support_census_receipt.json"
    marker_path = output / "PUBLICATION_COMPLETE.json"
    try:
        result_bytes = result.read_bytes()
        if receipt.read_bytes() != result_bytes:
            raise RuntimeError("support census dual-target publication is not byte-identical")
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if marker != {
            "format": "CRTO_SUPPORT_CENSUS_DUAL_PUBLICATION_V1",
            "object_id": SUPPORT_CENSUS_OBJECT_ID,
            "complete": True,
            "commit_law": "EXTERNAL_RESULT_FIRST_DIRECTION_ROOT_SECOND",
            "receipt": "support_census_receipt.json",
        }:
            raise RuntimeError("support census direction commit marker is malformed")
        if {path.name for path in output.iterdir()} != {
            "support_census_receipt.json", "PUBLICATION_COMPLETE.json",
        }:
            raise RuntimeError("support census direction root contains unexpected files")
        payload = json.loads(result_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("CRTO support census worker did not publish a readable result") from error
    if not isinstance(payload, Mapping):
        raise RuntimeError("CRTO support census worker result must be a JSON object")
    from .support_census import validate_support_census
    # The isolated worker already completed the independent full G16 replay.  The
    # parent validator is pure receipt arithmetic and structure only.
    validate_support_census(payload)
    return dict(payload)


def _missing_scientific_policy_executor(_stage_root: Path) -> Mapping[str, object]:
    """The threshold intentionally left result-sensitive numeric policy unfrozen."""

    analysis = {
        "status": "NONIDENTIFYING", "interpretation": "UNRESOLVED", "intervals": [],
        "failures": [
            "NONIDENTIFYING_ENGINEERING_PREFLIGHT: registered execution stopped before any "
            "optimizer update because the single-pass calibration/support/ledger production "
            "pipeline is incomplete"
        ],
    }
    # This private executor is reachable only from non-result publication tests.
    # Every value is an explicit TEST_ONLY_NONRESULT_FIXTURE, never a production
    # resource or scientific admission witness.
    return result_skeleton(
        analysis=analysis,
        replicates=({"replicate": index} for index in range(8)),
        resource={
            "memory_floor_pass": True,
            "available_physical_bytes": 4 * 1024**3,
            "effective_available_bytes": 4 * 1024**3,
        },
        ledger={
            "formula": "8*1088*256 + 16*actual_common_future_branch_count",
            "charged_full_tape_primitive_team_steps": 2_228_224,
            "common_future_steps_per_actual_branch": 16,
            "expected_common_future_branch_count": 0,
            "actual_common_future_branch_count": 0,
            "actual_common_future_steps": 0,
            "pre_result_exact": True, "within_ceiling": True,
            "actual_total_steps": 2_228_224, "ceiling": 2_596_864,
        },
        runtime={
            "workers": 1, "threads_per_worker": 1,
            "peak_rss_bytes": 0, "wall_seconds": 0,
        },
        admission={name: False for name in (
            "disjoint_panels", "matched_inputs", "derangement_valid", "common_future_valid",
            "raw_long_competent", "resource_valid", "ledger_valid", "runtime_valid",
            "calibration_valid", "k8_competence_support_valid",
        )},
    )


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
            "common_future_valid", "raw_long_competent", "resource_valid", "ledger_valid",
            "runtime_valid", "calibration_valid", "k8_competence_support_valid",
        }
        if (
            payload.get("status") != "NONIDENTIFYING"
            or not isinstance(provenance, Mapping)
            or provenance.get("frozen_policies") != dict(FROZEN_POLICIES)
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
            "under the exact frozen-policy receipt"
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


def _run_official_preflight(
    *,
    output_root: Path,
    result_path: Path,
    resource_receipt_path: Path,
    run_resource_receipt_path: Path,
    preflight_receipt_path: Path,
) -> dict[str, object]:
    """Create fresh resource receipts, dry-scan final manifests, and publish one receipt."""

    from .preflight import (
        atomic_create_json, create_shared_resource_receipt, create_shared_run_assessment,
        prospective_preflight,
    )

    paths = tuple(Path(path).resolve() for path in (
        output_root, result_path, resource_receipt_path, run_resource_receipt_path,
        preflight_receipt_path,
    ))
    if len(set(paths)) != len(paths):
        raise ValueError("scientific targets and preflight receipts must be distinct paths")
    if any(paths[0] in receipt.parents for receipt in paths[2:]):
        raise ValueError("preflight receipts must remain outside the scientific output root")
    if Path(output_root).resolve().exists() or Path(result_path).resolve().exists():
        raise FileExistsError("scientific output root and result path must both be fresh")
    if any(path.exists() for path in paths[2:]):
        raise FileExistsError("every official preflight receipt must be fresh")
    source_check()
    memory = create_shared_resource_receipt(paths[2])
    run_resource = create_shared_run_assessment(
        paths[3], run_id="crto_common_history_gate_r01",
    )
    report = prospective_preflight(
        resource_receipt=memory,
        run_resource_receipt=run_resource,
        output_root=paths[0],
        result_path=paths[1],
        scan_final_namespace=True,
    )
    atomic_create_json(paths[4], report)
    return report


def run_registered(
    output_root: Path,
    result_path: Path,
    *,
    resource_receipt_path: Path | None = None,
    run_resource_receipt_path: Path | None = None,
    preflight_receipt_path: Path | None = None,
    launch_resource_receipt_path: Path | None = None,
    launch_run_resource_receipt_path: Path | None = None,
) -> dict[str, object]:
    """Enforce current admission before work, optimizer updates, or publication."""

    source_check()
    if any(path is None for path in (
        resource_receipt_path, run_resource_receipt_path, preflight_receipt_path,
        launch_resource_receipt_path, launch_run_resource_receipt_path,
    )):
        raise PermissionError(
            "NONIDENTIFYING_MISSING_PREFLIGHT: official run requires "
            "first preflight plus second fresh launch 4-GiB/assess-run receipt paths "
            "before any output"
        )
    assert resource_receipt_path is not None
    assert run_resource_receipt_path is not None
    assert preflight_receipt_path is not None
    assert launch_resource_receipt_path is not None
    assert launch_run_resource_receipt_path is not None
    all_paths = tuple(Path(path).resolve() for path in (
        output_root, result_path, resource_receipt_path, run_resource_receipt_path,
        preflight_receipt_path, launch_resource_receipt_path,
        launch_run_resource_receipt_path,
    ))
    if len(set(all_paths)) != len(all_paths):
        raise ValueError("scientific targets and every preflight/launch receipt must be distinct")
    if any(all_paths[0] in receipt.parents for receipt in all_paths[2:]):
        raise ValueError("preflight and launch receipts must remain outside the scientific output root")
    report = _run_official_preflight(
        output_root=output_root,
        result_path=result_path,
        resource_receipt_path=resource_receipt_path,
        run_resource_receipt_path=run_resource_receipt_path,
        preflight_receipt_path=preflight_receipt_path,
    )
    if report.get("ready_for_optimizer") is not True:
        blockers = [
            issue
            for gate in report.get("gates", {}).values()  # type: ignore[union-attr]
            for issue in gate.get("issues", [])  # type: ignore[union-attr]
            if issue
        ]
        raise PermissionError(
            "CRTO prospective preflight refused before model/optimizer/result root: "
            + "; ".join(map(str, blockers))
        )
    payload = _launch_production_worker(
        output_root=Path(output_root), result_path=Path(result_path),
        preflight_receipt_path=Path(preflight_receipt_path),
        launch_resource_receipt_path=Path(launch_resource_receipt_path),
        launch_run_resource_receipt_path=Path(launch_run_resource_receipt_path),
    )
    validate_result(payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=OBJECT_ID)
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("source-check")
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--output-root", type=Path, required=True)
    preflight_parser.add_argument("--result", type=Path, required=True)
    preflight_parser.add_argument("--resource-receipt", type=Path, required=True)
    preflight_parser.add_argument("--run-resource-receipt", type=Path, required=True)
    preflight_parser.add_argument("--receipt", type=Path, required=True)
    pilot_parser = subparsers.add_parser("pilot")
    pilot_parser.add_argument("--output-root", type=Path, required=True)
    pilot_parser.add_argument("--result", type=Path, required=True)
    pilot_parser.add_argument("--resource-receipt", type=Path, required=True)
    pilot_parser.add_argument("--launch-resource-receipt", type=Path, required=True)
    pilot_parser.add_argument("--launch-run-resource-receipt", type=Path, required=True)
    subparsers.add_parser(
        "support-census", help="terminal consumed object; fresh execution is disabled",
    )
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--output-root", type=Path, required=True)
    run_parser.add_argument("--result", type=Path, required=True)
    run_parser.add_argument("--resource-receipt", type=Path)
    run_parser.add_argument("--run-resource-receipt", type=Path)
    run_parser.add_argument("--preflight-receipt", type=Path)
    run_parser.add_argument("--launch-resource-receipt", type=Path)
    run_parser.add_argument("--launch-run-resource-receipt", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else argv
    if len(raw_argv) > 0 and raw_argv[0] == "support-census":
        refuse_consumed_support_census()
    arguments = build_parser().parse_args(raw_argv)
    if arguments.action == "source-check":
        print(json.dumps(source_check(), indent=2, sort_keys=True))
        return 0
    if arguments.action == "preflight":
        report = _run_official_preflight(
            output_root=arguments.output_root,
            result_path=arguments.result,
            resource_receipt_path=arguments.resource_receipt,
            run_resource_receipt_path=arguments.run_resource_receipt,
            preflight_receipt_path=arguments.receipt,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["ready_for_optimizer"] else 6
    if arguments.action == "pilot":
        _launch_raw_pilot_worker(
            output_root=arguments.output_root,
            result_path=arguments.result,
            resource_receipt_path=arguments.resource_receipt,
            launch_resource_receipt_path=arguments.launch_resource_receipt,
            launch_run_resource_receipt_path=arguments.launch_run_resource_receipt,
        )
        return 0
    run_registered(
        arguments.output_root,
        arguments.result,
        resource_receipt_path=arguments.resource_receipt,
        run_resource_receipt_path=arguments.run_resource_receipt,
        preflight_receipt_path=arguments.preflight_receipt,
        launch_resource_receipt_path=arguments.launch_resource_receipt,
        launch_run_resource_receipt_path=arguments.launch_run_resource_receipt,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
