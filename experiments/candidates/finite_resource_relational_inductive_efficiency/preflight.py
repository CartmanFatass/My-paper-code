"""Direct, prospective, value-blind FRRIE production preflight.

The preflight validates caller-provided canonical structures and current
create-only filesystem state.  It neither reads a prewritten receipt nor
starts RNG, environment, training, evaluation, or checkpoint activity.
"""

from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping

from .contracts import ccic_control, egrcr_control, vqfp_controls
from .contracts.core import (
    FRRIE_SEALED_SEED_PACKET_V2,
    IMPLEMENTATION_CONTRACT,
    NATIVE_ABI,
    NATIVE_BINDING_KIND,
    NATIVE_COMPONENT,
    ContractError,
    canonical_json_bytes,
    manifest_packet_contract,
    validate_manifest,
)
from .host import NativeBackendUnavailable
from .controls import raw_value
from .native_adapter import (
    REQUIRED_NATIVE_CAPABILITIES,
    REQUIRED_NATIVE_STEP_ABI,
    PackageNativeAdapter,
    admit_package_native_adapter,
    expected_native_contract,
    load_package_native_adapter,
    package_native_artifact_is_fresh_in_process,
    package_native_artifact_path,
)

PREFLIGHT_SCHEMA = "FRRIE_PROSPECTIVE_PREFLIGHT_V2"
SEED_PACKET_SCHEMA = FRRIE_SEALED_SEED_PACKET_V2
_ROOT_256_HEX = re.compile(r"[0-9a-f]{64}")
_PACKAGE_DIR = Path(__file__).resolve().parent
_FIXTURE_DIR = _PACKAGE_DIR / "fixtures"
_FIREWALL_PACKAGE_DIR = _PACKAGE_DIR
_REPO_ROOT = _PACKAGE_DIR.parents[2]
_FORBIDDEN_IMPORT_TOKENS = (
    "semantic_graphon_shared_policy", "sgsp", "vqfp_vnpa",
    "vqfp_frrie_action_codec", "envs.native", "action_codec",
)


def _literal_adam_keywords(training_source: str) -> dict[str, Any]:
    tree = ast.parse(training_source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "Adam"
        ):
            return {
                keyword.arg: ast.literal_eval(keyword.value)
                for keyword in node.keywords
                if keyword.arg is not None
            }
    raise ContractError("frozen Torch Adam construction is absent")


def _actual_package_source_inventory() -> list[str]:
    return sorted(
        path.relative_to(_PACKAGE_DIR).as_posix()
        for path in _PACKAGE_DIR.rglob("*")
        if path.is_file()
        and (
            path.suffix in {".py", ".cpp"}
            or (path.parent.name == "fixtures" and path.suffix == ".json")
        )
    )


def _recompute_implementation_contract() -> dict[str, Any]:
    # Imports are local so an absent production dependency becomes a direct
    # fail-closed implementation blocker rather than an import-time fallback.
    from . import arms, policy, rng, state_codec, tapes, training, work
    from .host import PUBLIC_ROLES, native_endpoint
    from .native import native_abi

    shapes = dict(arms.LAYER_SHAPES)
    training_source = (_PACKAGE_DIR / "training.py").read_text(encoding="utf-8")
    orchestration_source = (_PACKAGE_DIR / "orchestration.py").read_text(encoding="utf-8")
    optimizer = _literal_adam_keywords(training_source)
    adam_step = training_source.index("self.optimizer.step()")
    beta_projection = training_source.index("self.model.project_beta()")
    required_rscf_markers = (
        "alternative_suffixes_executed != 7",
        "factual_suffixes_audited != 3",
        "factual audit terminal primitives or FP32 J differ",
        "q_targets = torch.full((3, 6)",
    )
    if not all(marker in orchestration_source for marker in required_rscf_markers):
        raise ContractError("RSCF cached-factual/suffix implementation markers drifted")
    if not (
        native_endpoint(3, 3, 0.0) == 1.0
        and native_endpoint(0, 0, 1.0) == 0.0
        and native_endpoint(3, 0, 0.0) == 0.42500000000000004
    ):
        raise ContractError("endpoint implementation probes drifted")
    actual_sources = _actual_package_source_inventory()
    recomputed = deepcopy(IMPLEMENTATION_CONTRACT)
    recomputed["dgp_native"].update({
        "component": NATIVE_COMPONENT,
        "abi": native_abi.NATIVE_STEP_ABI,
        "binding_kind": NATIVE_BINDING_KIND,
        "horizon": native_abi.HORIZON,
        "basins": native_abi.BASINS,
    })
    recomputed["observation_and_rosters"].update({
        "observation_width": native_abi.OBSERVATION_DIM,
        "rosters": list(native_abi.REGISTERED_ROSTERS),
        "roles": list(PUBLIC_ROLES),
        "roster_churn": False,
    })
    recomputed["actor"].update({
        "message_encoder": [
            [shapes["message_encoder.weight_ih"][1], shapes["message_encoder.weight_ih"][0]],
            [shapes["message_encoder.weight_ho"][1], shapes["message_encoder.weight_ho"][0]],
        ],
        "gru_input_width": shapes["gru.weight_input_zrn"][1],
        "gru_hidden_width": shapes["gru.weight_hidden_zrn"][1],
        "action_head": [shapes["action_head.weight"][1], shapes["action_head.weight"][0]],
        "layer_shapes_in_order": [[name, list(shape)] for name, shape in arms.LAYER_SHAPES],
        "parameter_count": arms.architecture_parameter_count(),
        "fp32_probability_tolerance": training.FP32_PROBABILITY_TOLERANCE,
        "rotation": (
            "SENDER_COLUMNS_ONLY_ONE_GRU_STEP_NO_PROPAGATION"
            if policy.SEMANTIC_COLUMN_ROTATION == (2, 0, 1) else "INVALID"
        ),
        "semantic_column_rotation": list(policy.SEMANTIC_COLUMN_ROTATION),
        "projection_boxes": {
            name: list(bounds) for name, bounds in arms.PROJECTION_BOXES.items()
        },
    })
    recomputed["optimizer"].update({
        "kind": (
            "TORCH_ADAM_PROJECT_AFTER_STEP_MOMENTS_UNTOUCHED"
            if adam_step < beta_projection else "INVALID"
        ),
        "lr": optimizer["lr"], "betas": list(optimizer["betas"]),
        "eps": optimizer["eps"], "weight_decay": optimizer["weight_decay"],
        "amsgrad": optimizer["amsgrad"], "maximize": optimizer["maximize"],
        "foreach": optimizer["foreach"], "capturable": optimizer["capturable"],
        "differentiable": optimizer["differentiable"], "fused": optimizer["fused"],
        "gradient_clip_l2": training.GRADIENT_CLIP_NORM,
    })
    recomputed["state_codec"].update({
        "optimizer_magic_ascii": state_codec.OPTIMIZER_STATE_MAGIC.decode("ascii"),
        "optimizer_state_version": state_codec.OPTIMIZER_STATE_VERSION,
    })
    recomputed["rng"].update({
        "addressing": (
            "SEMANTIC_ARM_CUT_BRANCH_INDEPENDENT"
            if {"arm", "cut", "branch"}.issubset(rng.FORBIDDEN_ADDRESS_LABELS)
            else "INVALID"
        ),
        "fp32_uniform_mapping": rng.float32_uniform_mapping_contract(),
    })
    recomputed["rscf"]["origin_schedule"] = tapes.origin_schedule_contract()
    recomputed["work_estimator"].update({
        "version": work.FLOP_ESTIMATOR_VERSION,
        "formula": work.FLOP_ESTIMATOR_FORMULA,
    })
    recomputed["package_relative_sources"] = actual_sources
    return recomputed


def _implementation_contract_report(manifest: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    origin_schedule_derived_from_runtime = False
    try:
        recomputed = _recompute_implementation_contract()
        from .tapes import origin_schedule_contract
        runtime_origin_schedule = origin_schedule_contract()
        origin_schedule_derived_from_runtime = _direct_equal(
            recomputed["rscf"]["origin_schedule"], runtime_origin_schedule
        ) and _direct_equal(
            runtime_origin_schedule, IMPLEMENTATION_CONTRACT["rscf"]["origin_schedule"]
        )
        direct_equal = (
            _direct_equal(recomputed, IMPLEMENTATION_CONTRACT)
            and _direct_equal(manifest["implementation_contract"], recomputed)
            and origin_schedule_derived_from_runtime
            and recomputed["package_relative_sources"]
            == sorted(recomputed["package_relative_sources"])
            and all((_PACKAGE_DIR / path).is_file() for path in recomputed["package_relative_sources"])
            and recomputed["dgp_native"]["abi"] == NATIVE_ABI
        )
    except Exception:
        direct_equal = False
    return {
        "passed": direct_equal,
        "direct_equal_to_manifest_and_runtime": direct_equal,
        "source_inventory_sorted": direct_equal,
        "all_declared_sources_present": direct_equal,
        "origin_schedule_derived_from_runtime": origin_schedule_derived_from_runtime,
        "scientific_result_values_read": False,
    }, ([] if direct_equal else ["IMPLEMENTATION_CONTRACT_FAILED"])


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _expected_ccic_fixture() -> dict[str, Any]:
    computed = ccic_control.canonical_ccic_fixture()
    return {
        "schema": "FRRIE_CCIC_CONTROL_V1",
        "complete": True,
        "source": "FRRIE_OWNED_PUBLIC_GRAPH",
        "edges": computed["edges"],
        "signs": {"A": computed["A"]["signs"], "B": computed["B"]["signs"]},
        "expected": {
            "A": {"wedge": computed["A"]["wedge"], "m3": computed["A"]["m3"]},
            "B": {"wedge": computed["B"]["wedge"], "m3": computed["B"]["m3"]},
        },
    }


def _expected_egrcr_fixture() -> dict[str, Any]:
    rows = egrcr_control.exact_fixture_rows()
    return {
        "schema": "FRRIE_EGRCR_CONTROL_V1",
        "complete": True,
        "arithmetic": "fractions.Fraction",
        "expected_update": ["0", "1/6"],
        "rows": [
            {
                "content": row.content, "mode": row.mode, "action": row.action,
                "p": _fraction_text(row.probability), "u": _fraction_text(row.utility),
            }
            for row in rows
        ],
    }


def _expected_raw_value_fixture() -> dict[str, Any]:
    return {
        "schema": "FRRIE_RAW_VALUE_CONTROL_V1",
        "complete": True,
        "balanced_accuracy": "1/2",
        "rows": [
            {
                "id": row.pair_id,
                "raw": [_fraction_text(value) for value in row.raw_values],
                "label": row.label,
                "association": row.association,
            }
            for row in raw_value.RAW_VALUE_ROWS
        ],
    }


def _vqfp_recomputation() -> tuple[dict[str, Any], dict[str, bool]]:
    measures = tuple(Fraction(value, 8) for value in (1, 2, 3, 2))
    densities = tuple(Fraction(value) for value in (1, 2, 3, 4))
    coordinates = tuple(Fraction(value, 8) for value in (1, 3, 5, 7))
    masses = vqfp_controls.mass_weights(measures, densities)
    masses_p = vqfp_controls.mass_weights(measures, densities, reassociated=True)
    mass_command = vqfp_controls.largest_remainder(masses, coordinates)
    mass_p_command = vqfp_controls.largest_remainder(masses_p, coordinates)
    marg0 = vqfp_controls.marg0_weights(masses, measures)
    marginal_command = vqfp_controls.marginal_heap(masses, measures, coordinates)
    vqfp_controls.assert_half_cycle_laws(measures)
    uniform_absorption = vqfp_controls.uniform_absorption_witness(
        (Fraction(1, 4),) * 4, Fraction(2),
    )
    try:
        vqfp_controls.require_action_seam()
    except vqfp_controls.ActionSeamAbsent as exc:
        action_seam_absent = str(exc) == vqfp_controls.FRRIE_ACTION_SEAM_ABSENT
    else:
        action_seam_absent = False
    laws = {
        "largest_remainder": mass_command == (5, 22, 49, 44) and sum(mass_command) == 120,
        "marg0": marg0 == tuple(
            mass / (600 * measure + 1) for mass, measure in zip(masses, measures)
        ),
        "marginal_heap": marginal_command == (0, 2, 54, 64) and sum(marginal_command) == 120,
        "utility": vqfp_controls.utility(marginal_command, masses, measures)
        <= vqfp_controls.utility(mass_command, masses, measures),
        "mass": masses == tuple(measure * density for measure, density in zip(measures, densities)),
        "mass_p": masses_p == tuple(
            measure * density
            for measure, density in zip(vqfp_controls.half_cycle(measures), densities)
        ) and mass_p_command == (20, 27, 20, 53),
        "half_cycle": vqfp_controls.half_cycle(vqfp_controls.half_cycle(measures)) == measures,
        "uniform_absorption": uniform_absorption is True,
        "action_seam_absent": action_seam_absent,
        "output_disconnected": vqfp_controls.OUTPUT_DISCONNECTED is True,
    }
    fixture = {
        "schema": "FRRIE_VQFP_CONTROLS_V1", "complete": True, "Q": 120,
        "coordinates": [_fraction_text(value) for value in coordinates],
        "measures": ["1/8", "2/8", "3/8", "2/8"],
        "densities": [_fraction_text(value) for value in densities],
        "half_cycle_indices": list(vqfp_controls.half_cycle_indices(4)),
        "tie_key": "PHYSICAL_COORDINATE_ASCENDING",
        "commands": {
            "MARGINAL_HEAP": list(marginal_command),
            "MASS": list(mass_command), "MASS-P": list(mass_p_command),
        },
        "mass_p": "lambda_i*d_i",
        "uniform_absorption": {
            "density": "2", "measures": ["1/4"] * 4, "passed": uniform_absorption,
        },
        "action_seam": vqfp_controls.FRRIE_ACTION_SEAM_ABSENT,
        "output_disconnected": vqfp_controls.OUTPUT_DISCONNECTED,
    }
    return fixture, laws


def _read_fixture(name: str) -> Any:
    path = _FIXTURE_DIR / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"package control fixture {name} is absent or invalid") from exc


def _dependency_output_firewall() -> dict[str, Any]:
    violations: list[str] = []
    paths = sorted(_FIREWALL_PACKAGE_DIR.rglob("*.py"))
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as exc:
            raise ContractError(f"dependency firewall cannot inspect {path.name}") from exc
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or "", *(alias.name for alias in node.names)]
            for name in imported:
                lowered = name.casefold()
                if any(token in lowered for token in _FORBIDDEN_IMPORT_TOKENS):
                    violations.append(f"{path.name}:forbidden-import")
            if isinstance(node, ast.Name) and node.id.casefold() == "actioncodec":
                violations.append(f"{path.name}:ActionCodec")
            if isinstance(node, ast.Attribute) and node.attr.casefold() == "actioncodec":
                violations.append(f"{path.name}:ActionCodec")
    if violations:
        raise ContractError(f"dependency/output firewall violations: {sorted(set(violations))}")
    return {
        "passed": True,
        "python_files_scanned": len(paths),
        "historical_imports_absent": True,
        "action_codec_absent": True,
        "output_connection_absent": True,
    }


def _value_blind_controls() -> tuple[dict[str, Any], list[str]]:
    report: dict[str, Any] = {}
    blockers: list[str] = []
    expected_fixtures: dict[str, dict[str, Any]] = {}

    try:
        ccic = ccic_control.canonical_ccic_fixture()
        passed = (
            ccic["A"]["wedge"], ccic["B"]["wedge"],
            ccic["A"]["m3"], ccic["B"]["m3"],
        ) == (1, 0, 12, -12)
        if not passed:
            raise ContractError("CCIC typed-wedge/m3 equality failed")
        expected_fixtures["ccic"] = _expected_ccic_fixture()
        report["ccic"] = {"passed": True, "canonical_typed_wedge_m3_equal": True}
    except Exception:
        blockers.append("CCIC_CONTROL_FAILED")
        report["ccic"] = {"passed": False, "canonical_typed_wedge_m3_equal": False}

    try:
        equality = egrcr_control.assert_rao_blackwell_equality()
        if equality != (Fraction(0), Fraction(1, 6)):
            raise ContractError("EGRCR equality drift")
        expected_fixtures["egrcr"] = _expected_egrcr_fixture()
        report["egrcr"] = {"passed": True, "exact_fraction_rao_blackwell_equal": True}
    except Exception:
        blockers.append("EGRCR_CONTROL_FAILED")
        report["egrcr"] = {"passed": False, "exact_fraction_rao_blackwell_equal": False}

    try:
        raw_value.validate_opposite_label_pairs()
        half = raw_value.balanced_accuracy(lambda values: int(values[0] > 0))
        constant_half = raw_value.balanced_accuracy(lambda values: 0)
        calls: dict[tuple[Fraction, ...], int] = {}

        def stateful(values: tuple[Fraction, ...]) -> int:
            calls[values] = calls.get(values, 0) + 1
            return calls[values] % 2

        try:
            raw_value.balanced_accuracy(stateful)
        except ContractError as exc:
            nondeterminism_rejected = "not deterministic" in str(exc)
        else:
            nondeterminism_rejected = False
        if (
            half != Fraction(1, 2)
            or constant_half != Fraction(1, 2)
            or not nondeterminism_rejected
        ):
            raise ContractError("raw-value balanced-accuracy ceiling drift")
        expected_fixtures["raw_value"] = _expected_raw_value_fixture()
        report["raw_value"] = {
            "passed": True, "opposite_label_pairs": True,
            "balanced_accuracy_half": True, "deterministic": True,
        }
    except Exception:
        blockers.append("RAW_VALUE_CONTROL_FAILED")
        report["raw_value"] = {
            "passed": False, "opposite_label_pairs": False,
            "balanced_accuracy_half": False, "deterministic": False,
        }

    try:
        fixture, laws = _vqfp_recomputation()
        if not all(laws.values()):
            raise ContractError("VQFP control law failed")
        expected_fixtures["vqfp"] = fixture
        report["vqfp"] = {"passed": True, **laws}
    except Exception:
        blockers.append("VQFP_CONTROL_FAILED")
        report["vqfp"] = {"passed": False}

    fixture_names = {
        "ccic": "ccic_control_v1.json", "egrcr": "egrcr_control_v1.json",
        "raw_value": "raw_value_v1.json", "vqfp": "vqfp_controls_v1.json",
    }
    fixture_equal: dict[str, bool] = {}
    for name, filename in fixture_names.items():
        try:
            fixture_equal[name] = name in expected_fixtures and _direct_equal(
                _read_fixture(filename), expected_fixtures[name],
            )
        except Exception:
            fixture_equal[name] = False
    if not all(fixture_equal.values()):
        blockers.append("FIXTURE_CONTRACT_FAILED")
    report["fixture_contracts"] = {
        "passed": all(fixture_equal.values()), "direct_equal": fixture_equal,
    }

    try:
        report["dependency_output_firewall"] = _dependency_output_firewall()
    except Exception:
        blockers.append("DEPENDENCY_OUTPUT_FIREWALL_FAILED")
        report["dependency_output_firewall"] = {
            "passed": False, "historical_imports_absent": False,
            "action_codec_absent": False, "output_connection_absent": False,
        }
    report["value_blind"] = True
    report["scientific_result_values_read"] = False
    report["passed"] = not blockers
    return report, blockers


def _direct_equal(left: Any, right: Any) -> bool:
    """Compare canonical JSON structures without Python bool/int coercion."""
    try:
        return canonical_json_bytes(left) == canonical_json_bytes(right)
    except ContractError:
        return False


def _validate_seed_packet(
    packet0: Mapping[str, Any], manifest: Mapping[str, Any],
) -> dict[str, Any]:
    required = {
        "schema", "version", "manifest_contract", "blocks",
        "addressed_rng_roots", "generation_provenance", "no_prior_use",
        "sealed", "complete",
    }
    if not isinstance(packet0, Mapping) or set(packet0) != required:
        raise ContractError("sealed seed packet fields must be exact")
    packet = dict(packet0)
    if packet["schema"] != SEED_PACKET_SCHEMA or type(packet["version"]) is not int or packet["version"] != 2:
        raise ContractError("sealed seed packet schema/version mismatch")
    if packet["sealed"] is not True or packet["complete"] is not True or packet["no_prior_use"] is not True:
        raise ContractError("seed packet must be sealed, complete, and declared unused")
    provenance = packet["generation_provenance"]
    if not isinstance(provenance, str) or not provenance:
        raise ContractError("seed packet generation provenance must be a nonempty direct string")
    blocks = packet["blocks"]
    if (
        not isinstance(blocks, list)
        or len(blocks) != 24
        or not _direct_equal(blocks, manifest["seed_blocks"])
    ):
        raise ContractError("seed packet blocks must equal the 24 manifest blocks in order")
    if not _direct_equal(packet["manifest_contract"], manifest_packet_contract(manifest)):
        raise ContractError("seed packet manifest contract mismatch")
    roots = packet["addressed_rng_roots"]
    if (
        not isinstance(roots, list)
        or len(roots) != 24
        or len(set(roots)) != 24
        or any(not isinstance(root, str) or _ROOT_256_HEX.fullmatch(root) is None for root in roots)
    ):
        raise ContractError(
            "seed packet must contain 24 unique ordered lowercase-hex 256-bit addressed-RNG roots"
        )
    # Shape inspection ends here.  Roots are never passed to AddressedRNG or
    # any other consumer during prospective preflight.
    return packet


def _validate_resource_ceiling(
    resource_ceiling0: Mapping[str, Any], manifest: Mapping[str, Any],
) -> dict[str, int]:
    if not isinstance(resource_ceiling0, Mapping):
        raise ContractError("prospective resource ceiling must be a direct mapping")
    expected = manifest["resource_ceiling"]
    resource_ceiling = dict(resource_ceiling0)
    if not _direct_equal(resource_ceiling, expected):
        raise ContractError("prospective resource ceiling must directly equal the manifest ceiling")
    return resource_ceiling


def _canonical_fresh_roots(
    manifest: Mapping[str, Any],
) -> tuple[Path, Path, Path, Path]:
    output = Path(manifest["roots"]["output"])
    checkpoint = Path(manifest["roots"]["checkpoint"])
    if not output.is_absolute() or not checkpoint.is_absolute():
        raise ContractError("fresh output and checkpoint roots must be absolute")
    output = output.resolve(strict=False)
    checkpoint = checkpoint.resolve(strict=False)
    if output == checkpoint:
        raise ContractError("fresh output and checkpoint roots must be distinct")
    if checkpoint.is_relative_to(output) or output.is_relative_to(checkpoint):
        raise ContractError("fresh output and checkpoint roots must not be nested")
    if output.parent != checkpoint.parent:
        raise ContractError(
            "fresh output and checkpoint roots must be sibling children of one common run parent"
        )
    common_run_parent = output.parent
    staging_parent = common_run_parent.with_name(
        common_run_parent.name + ".FRRIE_CLAIM_V2.tmp"
    )
    if common_run_parent.exists():
        raise ContractError("fresh common run parent must not already exist")
    if staging_parent.exists():
        raise ContractError("stale V2 common-run staging parent already exists")
    if output.exists() or checkpoint.exists():
        raise ContractError("fresh output and checkpoint roots must not already exist")
    input_paths = {
        "sealed_seed_packet": Path(manifest["sealed_seed_packet"]["path"]).resolve(strict=False),
        "preflight_receipt": Path(manifest["preflight_receipt"]["path"]).resolve(strict=False),
    }
    historical_candidates = _REPO_ROOT / "experiments" / "candidates"
    protected_areas = {
        "package_source_tree": _PACKAGE_DIR,
        "docs": _REPO_ROOT / "docs",
        "runtime": _REPO_ROOT / "runtime",
        "envs": _REPO_ROOT / "envs",
        "historical_sgsp": historical_candidates / "semantic_graphon_shared_policy_rscf_r01",
        "historical_vqfp": historical_candidates / "vqfp_vnpa_r03",
    }
    claim_paths = {
        "output": output, "checkpoint": checkpoint,
        "common_run_parent": common_run_parent, "claim_staging_parent": staging_parent,
    }
    for claim_name, claim_path in claim_paths.items():
        for protected_name, protected_path in {**input_paths, **protected_areas}.items():
            protected = protected_path.resolve(strict=False)
            if (
                claim_path == protected
                or claim_path.is_relative_to(protected)
                or protected.is_relative_to(claim_path)
            ):
                raise ContractError(
                    f"fresh {claim_name} overlaps protected {protected_name} path"
                )
    return output, checkpoint, common_run_parent, staging_parent


def _resource_monitor_contract(ceiling: Mapping[str, int]) -> dict[str, Any]:
    return {
        "schema": "FRRIE_FUTURE_RESULT_RESOURCE_MONITOR_V2",
        "scope": "FUTURE_RESULT_PROCESS_ONLY",
        "ceilings": dict(ceiling),
        "measurements": {
            "wall_seconds": "MONOTONIC_ELAPSED_TIME",
            "cpu_core_hours": "RESULT_PROCESS_AND_CHILD_PROCESS_CPU_TIME_DIV_3600",
            "rss_bytes": "PEAK_RESULT_PROCESS_TREE_RESIDENT_SET_BYTES",
            "scratch_bytes": "DIRECT_RECURSIVE_BYTE_CENSUS_OF_RESULT_SCRATCH",
            "durable_bytes": "DIRECT_RECURSIVE_BYTE_CENSUS_OF_DURABLE_OUTPUT_AND_CHECKPOINTS",
        },
        "sampling": "FROM_PROCESS_START_THROUGH_ATOMIC_TERMINAL_PUBLICATION",
        "ceiling_rule": "ABORT_ON_FIRST_DIRECT_GT_CEILING",
        "abort_contract": "TECHNICAL_FAILURE_NO_SCIENTIFIC_VALUES",
        "observed_by_preflight": False,
        "host_availability_snapshot": None,
        "host_snapshot_is_conformance_evidence": False,
    }


def prospective_preflight(
    manifest0: Mapping[str, Any],
    seed_packet0: Mapping[str, Any],
    *,
    resource_ceiling: Mapping[str, Any],
    native_adapter: object | None = None,
) -> dict[str, Any]:
    """Return a deterministic admission report without scientific activity.

    A missing package artifact is an expected fail-closed condition represented
    by a normal ``ready=False`` report.  A supplied fake/callback is a contract
    violation and is rejected rather than converted into a blocker.
    """
    manifest = validate_manifest(manifest0)
    packet = _validate_seed_packet(seed_packet0, manifest)
    ceiling = _validate_resource_ceiling(resource_ceiling, manifest)
    output_root, checkpoint_root, common_run_parent, staging_parent = (
        _canonical_fresh_roots(manifest)
    )
    artifact = package_native_artifact_path()
    blockers: list[str] = ["SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS"]
    controls, control_blockers = _value_blind_controls()
    blockers.extend(control_blockers)
    implementation, implementation_blockers = _implementation_contract_report(manifest)
    blockers.extend(implementation_blockers)
    blockers.append("RESOURCE_RUNTIME_CONFORMANCE_UNOBSERVED")
    adapter: PackageNativeAdapter | None = None
    if native_adapter is None:
        if not artifact.exists():
            blockers.append("PACKAGE_NATIVE_ARTIFACT_ABSENT")
        elif not package_native_artifact_is_fresh_in_process():
            blockers.append("PACKAGE_NATIVE_FRESH_BUILD_REQUIRED")
        else:
            try:
                adapter = load_package_native_adapter(manifest["compute"])
            except NativeBackendUnavailable:
                blockers.append("PACKAGE_NATIVE_ABI_UNAVAILABLE")
    else:
        # Exact-type/package-local admission rejects Python fakes, ctypes
        # callbacks, subclasses, and TEST_ONLY backends.
        adapter = admit_package_native_adapter(native_adapter)

    contract_equal = False
    if adapter is not None:
        adapter = admit_package_native_adapter(adapter)
        expected_contract = expected_native_contract(manifest["compute"])
        contract_equal = adapter.contract == expected_contract
        if not contract_equal:
            blockers.append("PACKAGE_NATIVE_CONTRACT_MISMATCH")

    # Even a structurally valid artifact cannot close the unresolved
    # simultaneous inference law.  Result activity remains blocked until that
    # prospective analysis contract is frozen outside this implementation.
    ready = False
    return {
        "schema": PREFLIGHT_SCHEMA,
        "status": "READY" if ready else "BLOCKED",
        "ready": ready,
        "ready_for_result_activity": False,
        "blockers": blockers,
        "manifest": {
            "validated": True,
            "schema": manifest["schema"],
            "direction_id": manifest["direction_id"],
            "experiment_id": manifest["experiment_id"],
        },
        "input": {
            "seed_packet_directly_bound": True,
            "schema": packet["schema"],
            "version": packet["version"],
            "block_count": len(packet["blocks"]),
            "addressed_rng_roots": "24_UNIQUE_ORDERED_LOWERCASE_HEX_256_BIT",
            "generation_provenance_present": True,
            "no_prior_use": True,
        },
        "native": {
            "package_artifact_path": str(artifact),
            "artifact_present": artifact.exists(),
            "adapter_loaded": adapter is not None,
            "package_owned": adapter is not None,
            "required_abi": REQUIRED_NATIVE_STEP_ABI,
            "required_capabilities": list(REQUIRED_NATIVE_CAPABILITIES),
            "contract": asdict(adapter.contract) if adapter is not None else None,
            "contract_equal": contract_equal,
        },
        "resource": {
            "ceiling": ceiling,
            "direct_equal_to_manifest": True,
            "observed_conformance_claimed": False,
            "runtime_conformance_observed": False,
            "monitor_contract": _resource_monitor_contract(ceiling),
        },
        "controls": controls,
        "implementation_contract": implementation,
        "fresh_roots": {
            "output": str(output_root),
            "checkpoint": str(checkpoint_root),
            "common_run_parent": str(common_run_parent),
            "claim_staging_parent": str(staging_parent),
            "absolute": True,
            "distinct": True,
            "not_nested": True,
            "sibling_children": True,
            "absent": True,
            "common_run_parent_absent": True,
            "claim_staging_parent_absent": True,
            "protected_inputs_and_source_areas_disjoint": True,
            "atomic_claim": "ONE_COMMON_PARENT_RENAME",
            "created": False,
        },
        "scientific_values_read": False,
        "scientific_activity_started": False,
    }


__all__ = ["PREFLIGHT_SCHEMA", "SEED_PACKET_SCHEMA", "prospective_preflight"]
