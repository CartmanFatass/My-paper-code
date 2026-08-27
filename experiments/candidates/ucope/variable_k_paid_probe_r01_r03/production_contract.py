"""Immutable R03 empirical-transaction contract; no activity is performed here."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping

from .contract import (
    COUNTER_LAYOUT_ID,
    EPISODES_PER_BATCH,
    FINAL_CHECKPOINT_SLOT_COUNT,
    K_TEST,
    K_TRAIN,
    OBJECT_REVISION,
    REGISTERED_MASTER_SEEDS,
    TRAINING_BATCHES,
    CounterNamespace,
    LearnedArm,
    NonlearnedArm,
    Panel,
)
from .s2_construction import OBJECT_DIGEST, REQUIRED_TOP_LEVEL_FIELDS


S3_SCOPE: Final[str] = "UCOPE-R03-S3-EMPIRICAL-PRELAUNCH-V2"
PAYLOAD_MODULE: Final[str] = (
    "experiments.candidates.ucope.variable_k_paid_probe_r01_r03.empirical_transaction"
)
PYTHON_EXECUTABLE: Final[str] = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"


@dataclass(frozen=True)
class RunBinding:
    """One complete immutable run identity, including its purchasing authority."""

    run_id: str
    output_root: str
    effect_kind: str
    effect_operation: str
    effect_resource_id: str
    emit_reference_metadata: bool
    authority_refs: tuple[tuple[str, str], ...] = ()
    authority_commit: str | None = None

    @property
    def parameters_path(self) -> str:
        return f"{self.output_root}/parameters.json"

    @property
    def estimate_path(self) -> str:
        return f"{self.output_root}/estimate.json"

    @property
    def source_manifest_path(self) -> str:
        return f"{self.output_root}/source-manifest.json"

    @property
    def checkpoint_manifest_path(self) -> str:
        return f"{self.output_root}/checkpoint-manifest.json"

    @property
    def hmasd_manifest_path(self) -> str:
        return f"{self.output_root}/manifest.json"

    @property
    def prelaunch_manifest_path(self) -> str:
        return f"{self.output_root}/prelaunch-manifest.json"

    def authority_document(self) -> list[dict[str, str]]:
        return [
            {
                "path": path,
                "sha256": sha256,
                **(
                    {"git_commit": self.authority_commit}
                    if self.authority_commit is not None
                    else {}
                ),
            }
            for path, sha256 in self.authority_refs
        ]

    def reference_document(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "output_root": self.output_root,
            "authority_refs": self.authority_document(),
        }

    def optional_reference_document(self) -> dict[str, object] | None:
        return self.reference_document() if self.emit_reference_metadata else None

    def optional_authority_document(self) -> list[dict[str, str]] | None:
        return self.authority_document() if self.emit_reference_metadata else None

    def output_effect(self) -> dict[str, str]:
        return {
            "kind": self.effect_kind,
            "resource_id": self.effect_resource_id,
            "operation": self.effect_operation,
        }


DEFAULT_RUN_BINDING: Final[RunBinding] = RunBinding(
    run_id="ucope-r03-complete-20260827-01",
    output_root="temp/directions/ucope/exp/ucope-r03-complete-20260827-01",
    effect_kind="DIRECTORY_CREATE_ONLY",
    effect_operation="create_and_populate_once",
    effect_resource_id="temp/directions/ucope/exp/ucope-r03-complete-20260827-01",
    emit_reference_metadata=False,
)
REPLACEMENT_RUN_BINDING: Final[RunBinding] = RunBinding(
    run_id="ucope-r03-complete-20260827-02",
    output_root="temp/directions/ucope/exp/ucope-r03-complete-20260827-02",
    effect_kind="LOCAL_RESULT_ROOT",
    effect_operation="CREATE_ONLY",
    effect_resource_id="temp/directions/ucope/exp/ucope-r03-complete-20260827-02/",
    emit_reference_metadata=True,
    authority_refs=(
        (
            "docs/research/portfolio/PORTFOLIO.md",
            "b0011cbf74f0226d0963960ac4721b5d38376c3d7f05b704028c43ac21cd06a5",
        ),
        (
            "docs/research/portfolio/workflow/registry.json",
            "b663741df8367cf16c96629f91541d1e69983edab6b13fb7abdf2a5c4afad8c8",
        ),
    ),
    authority_commit="3ace7bbe67ac6ded4c8b6bf37e3e60b3de50ce23",
)
CANONICAL_RUN_BINDINGS: Final[tuple[RunBinding, ...]] = (
    DEFAULT_RUN_BINDING,
    REPLACEMENT_RUN_BINDING,
)


def require_canonical_run_binding(binding: RunBinding) -> RunBinding:
    if not isinstance(binding, RunBinding):
        raise ValueError("run binding is absent or malformed")
    for canonical in CANONICAL_RUN_BINDINGS:
        if binding == canonical:
            return canonical
    raise ValueError("run binding is not a canonical purchased identity")


def canonical_run_binding(run_id: str, output_root: str) -> RunBinding:
    for binding in CANONICAL_RUN_BINDINGS:
        if binding.run_id == run_id and binding.output_root == output_root:
            return binding
    raise ValueError("run/output pair is not a canonical purchased identity")


# Public compatibility aliases remain the exact failed -01 transaction identity.
RUN_ID: Final[str] = DEFAULT_RUN_BINDING.run_id
OUTPUT_ROOT: Final[str] = DEFAULT_RUN_BINDING.output_root
PARAMETERS_PATH: Final[str] = DEFAULT_RUN_BINDING.parameters_path
ESTIMATE_PATH: Final[str] = DEFAULT_RUN_BINDING.estimate_path
SOURCE_MANIFEST_PATH: Final[str] = DEFAULT_RUN_BINDING.source_manifest_path
CHECKPOINT_MANIFEST_PATH: Final[str] = DEFAULT_RUN_BINDING.checkpoint_manifest_path
HMASD_MANIFEST_PATH: Final[str] = DEFAULT_RUN_BINDING.hmasd_manifest_path
PRELAUNCH_MANIFEST_PATH: Final[str] = DEFAULT_RUN_BINDING.prelaunch_manifest_path

REGISTERED_SEEDS: Final[tuple[int, ...]] = tuple(sorted(REGISTERED_MASTER_SEEDS))
PANELS: Final[tuple[str, ...]] = tuple(panel.name for panel in Panel)
LEARNED_ARMS: Final[tuple[str, ...]] = tuple(arm.name for arm in LearnedArm)
NONLEARNED_CONTROLS: Final[tuple[str, ...]] = (
    *(arm.name for arm in NonlearnedArm),
    "RAW_PERMAVG",
)
RNG_NAMESPACES: Final[tuple[str, ...]] = tuple(item.name for item in CounterNamespace)
REQUIRED_DIAGNOSTICS: Final[tuple[str, ...]] = tuple(sorted(REQUIRED_TOP_LEVEL_FIELDS))
TERMINAL_RESULT_MAP: Final[tuple[str, ...]] = (
    "PREACTIVITY_INCOMPLETE_OUTPUT",
    "PREACTIVITY_INVARIANT_FAILURE",
    "TERMINAL_SUPPORT_FAILURE",
    "TERMINAL_COMPETENCE_FAILURE",
    "TERMINAL_ACQUISITION_OR_SPECIFICITY_FAILURE",
    "TERMINAL_SEVEN_BRANCH_ATTRIBUTION",
)

DIRECTION_GIT_PATHS: Final[tuple[str, ...]] = (
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/__init__.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/checkpoint.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/contract.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/empirical_transaction.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/model.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/native/ucope_r01_r03_backend.cpp",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/native_backend.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/production_contract.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/production_checkpoint.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/production_engine.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/production_learner.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/production_manifest.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/production_result.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/production_validation.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/reference_oracle.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/s2_construction.py",
    "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/training.py",
    "tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py",
    "tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py",
    "tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s2.py",
    "tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_production.py",
    "tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_executor.py",
)


def canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def document_sha256(value: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def checkpoint_slots() -> tuple[dict[str, object], ...]:
    rows = tuple(
        {
            "arm": arm,
            "panel": panel,
            "master_seed": seed,
            "batch": TRAINING_BATCHES,
            "path": f"checkpoints/{arm.lower()}-{panel.lower()}-{seed}.json",
        }
        for arm in LEARNED_ARMS
        for panel in PANELS
        for seed in REGISTERED_SEEDS
    )
    if len(rows) != FINAL_CHECKPOINT_SLOT_COUNT:
        raise RuntimeError("final checkpoint inventory drift")
    return rows


def parameters_document(binding: RunBinding = DEFAULT_RUN_BINDING) -> dict[str, object]:
    """Return the one canonical, result-independent registered parameter object."""

    binding = require_canonical_run_binding(binding)
    return {
        "schema": "UCOPE_R01_R03_EMPIRICAL_PARAMETERS_V1",
        "scope": S3_SCOPE,
        "run_id": binding.run_id,
        "object_revision": OBJECT_REVISION,
        "object_digest": OBJECT_DIGEST,
        "registered_master_seeds": list(REGISTERED_SEEDS),
        "panels": list(PANELS),
        "learned_arms": list(LEARNED_ARMS),
        "nonlearned_controls": list(NONLEARNED_CONTROLS),
        "training": {
            "batches": TRAINING_BATCHES,
            "episodes_per_arm_batch": EPISODES_PER_BATCH,
            "joint_adamw_steps_per_batch": 1,
            "final_checkpoint_batch_only": TRAINING_BATCHES,
            "worker_count": 1,
            "dtype": "FP32",
        },
        "evaluation": {
            "k_train": list(K_TRAIN),
            "k_test": list(K_TEST),
            "required_diagnostics": list(REQUIRED_DIAGNOSTICS),
            "terminal_result_map": list(TERMINAL_RESULT_MAP),
            "complete_only": True,
        },
        "rng": {
            "counter_layout_id": COUNTER_LAYOUT_ID,
            "namespaces": list(RNG_NAMESPACES),
            "shared_regime_probe_tail_within_seed_panel_across_arms": True,
            "independent_action_and_initialization_across_arm_addresses": True,
        },
        "checkpoint_inventory": list(checkpoint_slots()),
        "checkpoint_slot_count": FINAL_CHECKPOINT_SLOT_COUNT,
        "rerun_permitted": False,
        "result_responsive_options": [],
        "result_firewall": "ATOMIC_COMPLETE_ONLY",
    }


def conservative_estimate_document(
    binding: RunBinding = DEFAULT_RUN_BINDING,
) -> dict[str, object]:
    """Freeze the accepted no-unmeasured-speedup S2 projection."""

    binding = require_canonical_run_binding(binding)
    return {
        "schema": "HMASD_RESOURCE_ESTIMATE_V1",
        "direction_id": "ucope",
        "run_id": binding.run_id,
        "cpu_cores": 1,
        "cpu_hours": 0.10810758191836511,
        "wall_seconds": 388.0782459051625,
        "peak_memory_gib": 0.479766845703125,
        "basis": "accepted S2 no-unmeasured-speedup complete-object projection",
        "workers": 1,
        "threads_per_worker": 1,
        "peak_memory_bytes": 515145728,
        "io_bytes": 2312507074,
        "gpu_count": 0,
        "no_unmeasured_speedup": True,
        "source": "UCOPE S2 accepted complete-object projection",
    }


def payload_argv(binding: RunBinding = DEFAULT_RUN_BINDING) -> tuple[str, ...]:
    """Exact future child argv; it contains no responsive/partial selector."""

    binding = require_canonical_run_binding(binding)
    return (
        PYTHON_EXECUTABLE,
        "-m",
        PAYLOAD_MODULE,
        "--run-id",
        binding.run_id,
        "--output-root",
        binding.output_root,
        "--hmasd-manifest",
        binding.hmasd_manifest_path,
    )


def repo_path(root: Path, relative: str) -> Path:
    return Path(root).resolve() / Path(*relative.split("/"))
