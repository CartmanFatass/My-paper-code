"""Complete-only S4 validation and technical acceptance construction."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from typing import Final, Mapping

from .barriers import StageBarrier
from .foundation_activity_resource_estimate import (
    ESTIMATE_PATH,
    REPAIR_ESTIMATE_PATH,
    SOURCE_PATHS,
    S4_OUTPUT_ROOT,
    WORKLOAD,
)
from .foundation_activity_production import production_entrypoint_contract
from .foundation_run_manifest import (
    PROSPECTIVE_OUTPUT_ROOT,
    S4_RUN_MANIFEST_PATH,
    build_production_argv,
    canonical_json_bytes,
)


EXACT_TEST_COMMAND: Final[str] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest "
    "tests/experiments/candidates/scdmp_variable_k/"
    "test_native_fusion_r01_foundation_activity_prelaunch.py -q"
)
ESTIMATOR_MODULE: Final[str] = (
    "experiments.candidates.scdmp_variable_k.native_fusion_r01."
    "foundation_activity_resource_estimate"
)
ESTIMATOR_HELP_COMMAND: Final[str] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m "
    f"{ESTIMATOR_MODULE} --help"
)
ESTIMATOR_OUTPUT_COMMAND: Final[str] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m "
    f"{ESTIMATOR_MODULE} --output {ESTIMATE_PATH}"
)
S4_REPAIR_OUTPUT_ROOT: Final[str] = f"{S4_OUTPUT_ROOT}/executor-repair"
REPAIR_ESTIMATOR_OUTPUT_COMMAND: Final[str] = (
    "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m "
    f"{ESTIMATOR_MODULE} --output {REPAIR_ESTIMATE_PATH}"
)
ACCEPTED_CHAIN_REFS: Final[tuple[dict[str, str], ...]] = (
    {
        "path": (
            "docs/research/candidates/semigroup_consistent_duration_model_policy/"
            "SCDMP_NATIVE_FUSION_SCIENCE_AUTHORITY_R01_20260827.md"
        ),
        "sha256": "c8091b15293f2cdeae4fc00a42bdfc1a0ae165d930fc152bca86610979e0c47c",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s0/g1/S0_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "52bd81aed310a81791c441dd9253d1704f3e28efa295fe42a635d78776645cce",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s1/g1/S1_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "8dfcb06ca4b37d297a624323ef7f178009f1a84724f7797d6de7268a00dc3195",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s2/g1/S2_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "bacfbfe0da703b1bef4bb93a93fff92c4f5ce0c39c6f800617d255a6e7fdb825",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s3/g1/S3_SOURCE_MANIFEST.json"
        ),
        "sha256": "fad2a2bb80f2550be49573acccc30446fa3575750706f18f3a2f9d9ba885f457",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s3/g1/"
            "S3_PROSPECTIVE_FOUNDATION_ACTIVITY_MANIFEST.json"
        ),
        "sha256": "789e57de8051de5327791c56c0493925147a076da9cf423bedd41ac1860e1a12",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s3/g1/S3_COMPLETE_ACTIVITY_EVIDENCE.json"
        ),
        "sha256": "9b4c5ae28c9fe5041185c261fd1d050a5bbe8678dd94a3c342ef56ebf00fc3b7",
    },
    {
        "path": (
            "temp/directions/semigroup_consistent_duration_model_policy/test/"
            "native_fusion_r01/s3/g1/S3_TECHNICAL_ACCEPTANCE.json"
        ),
        "sha256": "1217e4f3474e1f1e0472581d32fc21ba7d0f434a3f19d74e705bfecf29791d10",
    },
)


class ActivityValidationError(ValueError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_sha(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True


def manifest_digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_source_manifest(repository_root: Path) -> dict[str, object]:
    root = Path(repository_root).resolve()
    files = []
    for relative in SOURCE_PATHS:
        target = root / relative
        if not target.is_file():
            raise ActivityValidationError(f"S4 source is absent: {relative}")
        files.append({"path": relative, "sha256": _sha(target)})
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S4_SOURCE_MANIFEST_V1",
        "complete": True,
        "files": files,
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }


def _require_chain_fresh(root: Path) -> None:
    for ref in ACCEPTED_CHAIN_REFS:
        target = root / ref["path"]
        if not target.is_file() or _sha(target) != ref["sha256"]:
            raise ActivityValidationError(f"accepted chain bytes changed: {ref['path']}")


def _validate_estimate(
    estimate: Mapping[str, object], source_manifest: Mapping[str, object]
) -> str:
    if estimate.get("schema") != (
        "SCDMP_NATIVE_FUSION_R01_S4_ACTIVITY_RESOURCE_ESTIMATE_V1"
    ):
        raise ActivityValidationError("activity estimate schema differs")
    if estimate.get("implementation_refs") != source_manifest.get("files"):
        raise ActivityValidationError("activity estimate source refs differ")
    if estimate.get("workload") != WORKLOAD:
        raise ActivityValidationError("activity estimate workload differs")
    measured = estimate.get("measured_primitives")
    if (
        not isinstance(measured, Mapping)
        or measured.get("registered") is not False
        or measured.get("reward_evaluated") is not False
        or measured.get("question_relevant_value_evaluated") is not False
    ):
        raise ActivityValidationError("measured primitive firewall differs")
    if estimate.get("unmeasured_primitives") != []:
        raise ActivityValidationError("activity estimate has unmeasured primitives")
    if estimate.get("device_limits") != {
        "workers": 1,
        "cpu_threads": 1,
        "accelerators": 0,
        "foundations_concurrent": 1,
    }:
        raise ActivityValidationError("one-worker device limits differ")
    estimates = estimate.get("estimates")
    if not isinstance(estimates, Mapping) or set(estimates) != {"low", "central", "high"}:
        raise ActivityValidationError("low/central/high estimates are incomplete")
    fields = {
        "wall_seconds",
        "cpu_core_seconds",
        "cpu_core_hours",
        "peak_memory_bytes",
        "scratch_bytes",
        "retained_storage_bytes",
        "io_bytes",
    }
    for row in estimates.values():
        if (
            not isinstance(row, Mapping)
            or set(row) != fields
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
                for value in row.values()
            )
        ):
            raise ActivityValidationError("activity estimate resource row differs")
    classification = estimate.get("runtime_classification")
    if classification not in {"<=7200", ">7200", "STILL_UNGROUNDED"}:
        raise ActivityValidationError("runtime classification is not literal")
    high_wall = float(estimates["high"]["wall_seconds"])
    expected = "<=7200" if high_wall <= 7_200 else ">7200"
    if classification != expected:
        raise ActivityValidationError("runtime classification disagrees with high wall")
    required = classification == ">7200"
    if (
        estimate.get("performance_reasonableness_review_required") is not required
        or estimate.get("explicit_user_approval_required_before_activity") is not required
        or estimate.get("unsafe_memory_plan") is not False
    ):
        raise ActivityValidationError("scheduling or memory boundary differs")
    return classification


def build_complete_prelaunch_evidence(
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    estimate: Mapping[str, object],
    prelaunch_manifest: Mapping[str, object],
    observed_activity_paths: tuple[str, ...],
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    if source_manifest != build_source_manifest(root):
        raise ActivityValidationError("S4 source manifest does not bind current bytes")
    _require_chain_fresh(root)
    if observed_activity_paths:
        raise ActivityValidationError("activity path is forbidden in S4")
    if (root / PROSPECTIVE_OUTPUT_ROOT).exists() or (root / S4_RUN_MANIFEST_PATH).exists():
        raise ActivityValidationError("run manifest or activity output already exists")
    classification = _validate_estimate(estimate, source_manifest)
    if (
        prelaunch_manifest.get("code_sha256") != manifest_digest(source_manifest)
        or prelaunch_manifest.get("activity_estimate_sha256")
        != manifest_digest(estimate)
        or prelaunch_manifest.get("payload_argv")
        != list(build_production_argv(code_sha256=manifest_digest(source_manifest)))
        or prelaunch_manifest.get("activity_authorized") is not False
        or prelaunch_manifest.get("operator_now") is not False
        or prelaunch_manifest.get("effect_refs") != []
    ):
        raise ActivityValidationError("prelaunch cross-reference or firewall differs")
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S4_COMPLETE_PRELAUNCH_EVIDENCE_V1",
        "complete": True,
        "accepted_chain_refs": [dict(ref) for ref in ACCEPTED_CHAIN_REFS],
        "source_manifest_sha256": manifest_digest(source_manifest),
        "activity_estimate_sha256": manifest_digest(estimate),
        "prelaunch_manifest_sha256": manifest_digest(prelaunch_manifest),
        "runtime_classification": classification,
        "prospective_payload_argv": prelaunch_manifest["payload_argv"],
        "output_effect_template": prelaunch_manifest["output_effect_template"],
        "observed_activity_paths": [],
        "run_manifest_present": False,
        "output_root_present": False,
        "hard_downstream_absence": True,
        "ordered_stage_barriers": ["I_native", "C_native", "O_native"],
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }


def _validate_command_measurements(value: Mapping[str, object]) -> None:
    if set(value) != {
        "focused_pytest",
        "estimator_help",
        "estimator_output",
        "storage_bytes",
    }:
        raise ActivityValidationError("technical command measurements are incomplete")
    storage = value["storage_bytes"]
    if isinstance(storage, bool) or not isinstance(storage, int) or storage < 0:
        raise ActivityValidationError("technical storage measurement is invalid")
    fields = {
        "cpu_seconds",
        "wall_seconds",
        "peak_working_set_bytes",
        "read_bytes",
        "write_bytes",
    }
    for label in ("focused_pytest", "estimator_help", "estimator_output"):
        row = value[label]
        if (
            not isinstance(row, Mapping)
            or set(row) != fields
            or any(
                isinstance(item, bool)
                or not isinstance(item, (int, float))
                or item < 0
                for item in row.values()
            )
        ):
            raise ActivityValidationError(f"technical command measurement differs: {label}")


def build_s4_acceptance(
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    estimate: Mapping[str, object],
    prelaunch_manifest: Mapping[str, object],
    evidence: Mapping[str, object],
    command_measurements: Mapping[str, object],
    command_ref_sha256: Mapping[str, str],
) -> dict[str, object]:
    root = Path(repository_root).resolve()
    expected_evidence = build_complete_prelaunch_evidence(
        repository_root=root,
        source_manifest=source_manifest,
        estimate=estimate,
        prelaunch_manifest=prelaunch_manifest,
        observed_activity_paths=(),
    )
    if evidence != expected_evidence:
        raise ActivityValidationError("complete S4 evidence differs")
    _validate_command_measurements(command_measurements)
    if set(command_ref_sha256) != {
        "focused_pytest",
        "estimator_help",
        "estimator_output",
    } or any(not _valid_sha(value) for value in command_ref_sha256.values()):
        raise ActivityValidationError("technical command refs are incomplete")
    classification = str(estimate["runtime_classification"])
    review_required = classification == ">7200"
    acceptance: dict[str, object] = {
        "schema": "SCDMP_NATIVE_FUSION_R01_S4_TECHNICAL_ACCEPTANCE_V1",
        "accepted": True,
        "stage": "S4_FOUNDATION_ACTIVITY_PRELAUNCH",
        "accepted_chain_refs": [dict(ref) for ref in ACCEPTED_CHAIN_REFS],
        "source_refs": [dict(ref) for ref in source_manifest["files"]],
        "artifact_refs": [
            {
                "path": f"{S4_OUTPUT_ROOT}/S4_SOURCE_MANIFEST.json",
                "sha256": manifest_digest(source_manifest),
            },
            {
                "path": ESTIMATE_PATH,
                "sha256": manifest_digest(estimate),
            },
            {
                "path": f"{S4_OUTPUT_ROOT}/S4_PRELAUNCH_MANIFEST.json",
                "sha256": manifest_digest(prelaunch_manifest),
            },
            {
                "path": f"{S4_OUTPUT_ROOT}/S4_COMPLETE_PRELAUNCH_EVIDENCE.json",
                "sha256": manifest_digest(evidence),
            },
        ],
        "technical_commands": {
            "focused_pytest": EXACT_TEST_COMMAND,
            "estimator_help": ESTIMATOR_HELP_COMMAND,
            "estimator_output": ESTIMATOR_OUTPUT_COMMAND,
        },
        "technical_command_refs": {
            "focused_pytest": {
                "path": f"{S4_OUTPUT_ROOT}/pytest-verification.json",
                "sha256": command_ref_sha256["focused_pytest"],
            },
            "estimator_help": {
                "path": f"{S4_OUTPUT_ROOT}/estimator-help-verification.json",
                "sha256": command_ref_sha256["estimator_help"],
            },
            "estimator_output": {
                "path": f"{S4_OUTPUT_ROOT}/estimator-output-verification.json",
                "sha256": command_ref_sha256["estimator_output"],
            },
        },
        "actual_technical_measurements": dict(command_measurements),
        "activity_estimates": estimate["estimates"],
        "runtime_classification": classification,
        "prospective_payload_argv": prelaunch_manifest["payload_argv"],
        "output_effect_template": prelaunch_manifest["output_effect_template"],
        "next_portfolio_boundary": {
            "kind": "PORTFOLIO_RECONCILE_FOUNDATION_ACTIVITY_PRELAUNCH",
            "runtime_classification": classification,
            "performance_reasonableness_review_required": review_required,
            "explicit_user_approval_required_before_activity": review_required,
            "separate_activity_authority_required": True,
            "immutable_run_manifest_required": True,
            "exact_code_sha_required": True,
            "create_only_output_root_required": True,
            "one_operator_required": True,
            "activity_authorized": False,
            "operator_now": False,
            "effect_refs": [],
        },
        "firewall": {
            "registered_identity_present": False,
            "eligible_artifact_present": False,
            "question_relevant_value_visible": False,
            "activity_authorized": False,
            "operator_now": False,
            "effect_refs": [],
        },
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }
    StageBarrier.s0().validate_payload(acceptance)
    return acceptance


def build_executor_repair_acceptance(
    *,
    repository_root: Path,
    source_manifest: Mapping[str, object],
    estimate: Mapping[str, object],
    prelaunch_manifest: Mapping[str, object],
    evidence: Mapping[str, object],
    command_measurements: Mapping[str, object],
    command_ref_sha256: Mapping[str, str],
) -> dict[str, object]:
    """Bind the fresh executor repair without authorizing the later activity."""

    acceptance = build_s4_acceptance(
        repository_root=repository_root,
        source_manifest=source_manifest,
        estimate=estimate,
        prelaunch_manifest=prelaunch_manifest,
        evidence=evidence,
        command_measurements=command_measurements,
        command_ref_sha256=command_ref_sha256,
    )
    acceptance["schema"] = (
        "SCDMP_NATIVE_FUSION_R01_S4_EXECUTOR_REPAIR_TECHNICAL_ACCEPTANCE_V1"
    )
    acceptance["stage"] = "S4_FOUNDATION_ACTIVITY_EXECUTOR_REPAIR"
    acceptance["artifact_refs"] = [
        {
            "path": f"{S4_REPAIR_OUTPUT_ROOT}/S4_EXECUTOR_REPAIR_SOURCE_MANIFEST.json",
            "sha256": manifest_digest(source_manifest),
        },
        {
            "path": REPAIR_ESTIMATE_PATH,
            "sha256": manifest_digest(estimate),
        },
        {
            "path": f"{S4_REPAIR_OUTPUT_ROOT}/S4_EXECUTOR_REPAIR_PRELAUNCH_MANIFEST.json",
            "sha256": manifest_digest(prelaunch_manifest),
        },
        {
            "path": f"{S4_REPAIR_OUTPUT_ROOT}/S4_EXECUTOR_REPAIR_COMPLETE_EVIDENCE.json",
            "sha256": manifest_digest(evidence),
        },
    ]
    acceptance["technical_commands"]["estimator_output"] = (
        REPAIR_ESTIMATOR_OUTPUT_COMMAND
    )
    for label in ("focused_pytest", "estimator_help", "estimator_output"):
        acceptance["technical_command_refs"][label]["path"] = (
            f"{S4_REPAIR_OUTPUT_ROOT}/{label.replace('_', '-')}-verification.json"
        )
    acceptance["production_entrypoint"] = production_entrypoint_contract()
    acceptance["later_activity_boundary"] = acceptance.pop("next_portfolio_boundary")
    acceptance["later_activity_boundary"]["kind"] = (
        "PORTFOLIO_RECONCILE_REPAIRED_FOUNDATION_ACTIVITY"
    )
    StageBarrier.s0().validate_payload(acceptance)
    return acceptance


def emit_create_only(path: Path, value: Mapping[str, object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", delete=False
        ) as temporary:
            temporary.write(canonical_json_bytes(value))
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.link(temporary_name, target)
    except FileExistsError as exc:
        raise ActivityValidationError(f"create-only artifact exists: {target}") from exc
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
