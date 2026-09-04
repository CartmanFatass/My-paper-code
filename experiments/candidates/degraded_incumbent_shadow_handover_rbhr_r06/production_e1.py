"""Stage-E1 flow-local result-blind self-audits for DISH RBHR r06."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping

from .production_contract import SCIENCE_REVISION, complete_inventory
from .production_backend import flow_local_native_abi_self_audit
from .production_evaluator import flow_local_evaluator_self_audit
from .production_real_sham import flow_local_real_sham_self_audit
from .production_recurrent_trainer import flow_local_trainer_self_audit
from .production_reducer import flow_local_reducer_self_audit
from .production_train_reset import flow_local_reset_fixture_manifest


E1_SOURCE_FILES = (
    "production_train_reset.py",
    "production_recurrent_trainer.py",
    "production_training_engine.py",
    "production_evaluator.py",
    "production_real_sham.py",
    "production_reducer.py",
    "production_inference.py",
    "production_preactivity.py",
    "production_backend.py",
    "native/rbhr_r06_production_backend.cpp",
)


class E1AuditError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_e1_flow_local_self_audits() -> dict[str, object]:
    package = Path(__file__).resolve().parent
    flows: Mapping[str, Mapping[str, object]] = {
        "TRAIN_RESET_32_LANES": flow_local_reset_fixture_manifest(),
        "NATIVE_RECURRENT_PERSISTENT_TRAINER": flow_local_trainer_self_audit(),
        "FIVE_ARM_MASK_ON_OFF_EVALUATOR": flow_local_evaluator_self_audit(),
        "FIRST_VALID_REAL_SHAM_RUNNER": flow_local_real_sham_self_audit(),
        "COMPLETE_24x6990_REDUCER_INFERENCE": flow_local_reducer_self_audit(),
    }
    native_abi = flow_local_native_abi_self_audit()
    inventory = complete_inventory()
    exact = {
        "TRAIN_RESET_32_LANES": (
            flows["TRAIN_RESET_32_LANES"]["lanes"] == 32
            and flows["TRAIN_RESET_32_LANES"]["lane_ids_exact"]
            and flows["TRAIN_RESET_32_LANES"]["four_lanes_per_cell"]
        ),
        "NATIVE_RECURRENT_PERSISTENT_TRAINER": (
            flows["NATIVE_RECURRENT_PERSISTENT_TRAINER"]["transitions_per_update"] == 4_096
            and flows["NATIVE_RECURRENT_PERSISTENT_TRAINER"]["updates_per_job"] == 1_024
            and flows["NATIVE_RECURRENT_PERSISTENT_TRAINER"]["required_tokens_present"]
        ),
        "FIVE_ARM_MASK_ON_OFF_EVALUATOR": (
            flows["FIVE_ARM_MASK_ON_OFF_EVALUATOR"]["evaluation_items"] == 115_200
            and flows["FIVE_ARM_MASK_ON_OFF_EVALUATOR"]["plan_unique"]
            and flows["FIVE_ARM_MASK_ON_OFF_EVALUATOR"]["checkpoint_loaded"]
        ),
        "FIRST_VALID_REAL_SHAM_RUNNER": (
            flows["FIRST_VALID_REAL_SHAM_RUNNER"]["paired_window_ticks"] == 100
            and flows["FIRST_VALID_REAL_SHAM_RUNNER"]["first_valid_only_fixture"]
            and flows["FIRST_VALID_REAL_SHAM_RUNNER"]["native_predicate_before_clone"]
        ),
        "COMPLETE_24x6990_REDUCER_INFERENCE": (
            flows["COMPLETE_24x6990_REDUCER_INFERENCE"]["matrix_shape"] == [24, 6_990]
            and flows["COMPLETE_24x6990_REDUCER_INFERENCE"]["all_estimands_source_bound"]
            and flows["COMPLETE_24x6990_REDUCER_INFERENCE"]["duplicates_fail_closed"]
            and flows["COMPLETE_24x6990_REDUCER_INFERENCE"]["incomplete_fail_closed"]
        ),
    }
    if not (
        native_abi["passive_label_shapes_exact"]
        and native_abi["mask_on_off_pair_shared_randomness"]
        and native_abi["first_application_predicate_callable"]
    ):
        raise E1AuditError("r06 native flow-local ABI audit differs")
    if not all(exact.values()):
        raise E1AuditError("one or more E1 flow-local inventories differ")
    return {
        "schema": "DISH_RBHR_R06_E1_FIVE_FLOW_LOCAL_SELF_AUDITS_V1",
        "science_revision": SCIENCE_REVISION,
        "stage": "E1_SOURCE_AND_FLOW_LOCAL_SELF_AUDIT_ONLY",
        "flow_families": dict(flows), "family_acceptance": exact,
        "native_abi_flow_local_self_audit": native_abi,
        "all_five_families_flow_local_accepted": True,
        "inventory": inventory,
        "source_sha256": {relative: _sha256(package / relative) for relative in E1_SOURCE_FILES},
        "frozen_invariants": {
            "panel_tapes": inventory["evaluation_tapes"],
            "training_jobs": inventory["training_jobs"],
            "updates_per_job": inventory["updates_per_job"],
            "training_transitions": inventory["training_transitions"],
            "evaluation_episodes": inventory["evaluation_episodes"],
            "estimands": 6_990, "bootstrap_resamples": inventory["bootstrap_resamples"],
            "single_fresh_nonreplaceable_identity": True,
            "native_recurrence": True, "persistent_training": True,
            "first_valid_real_sham": True, "result_blind_atomicity": True,
        },
        "e2_cross_flow_integration": False, "independent_test_acceptance": False,
        "lease_request": False, "lease": False, "master": False, "identity": False,
        "coordinate": False, "tape": False, "model": False, "checkpoint": False,
        "training": False, "evaluation": False, "inference": False,
        "partial_value": False, "question_relevant_output": False,
    }


__all__ = ["E1AuditError", "run_e1_flow_local_self_audits"]
