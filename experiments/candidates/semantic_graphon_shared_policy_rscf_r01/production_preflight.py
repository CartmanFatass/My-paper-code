"""Extended TEST-only measurement for the SGSP production service graph."""

from __future__ import annotations

from dataclasses import asdict
import math
from pathlib import Path
import time
from types import SimpleNamespace

import torch

from .contracts import TestIdentity
from .policy import (
    ACTOR_PARAMETER_SHAPES,
    CRITIC_PARAMETER_SHAPES,
    RSCFActor,
    TerminalCritic,
)
from .production_boundary import (
    LEASE_FINALIZATION_MARGIN_SECONDS,
    PREFLIGHT_ARTIFACT_SCHEMA,
    PROJECTED_PANEL_WALL_SECONDS,
    EmpiricalCoordinateAdapter,
    _atomic_write_once,
    canonical_json_bytes,
    canonical_sha256,
    exact_future_launch_contract,
    run_sealed_test_preflight,
)
from .production_runner import ProductionSeedEngine, _ArmState
from .runner import RSCFGateBRunner
from .training import make_projected_adam


EXTENDED_PREFLIGHT_SCHEMA = "SGSP_RSCF_R01_EXTENDED_TEST_ONLY_PRODUCTION_PREFLIGHT_V1"


def _literal_parameters(shapes, phase: int):
    result = {}
    cursor = phase * 101
    for name, shape in shapes.items():
        count = math.prod(shape)
        values = torch.arange(cursor, cursor + count, dtype=torch.float32)
        result[name] = (0.015 * torch.sin(values * 0.017 + phase)).reshape(shape).contiguous()
        cursor += count
    return result


def _test_engine(helper: RSCFGateBRunner, actor_parameters, critic_parameters, coordinates):
    engine = ProductionSeedEngine.__new__(ProductionSeedEngine)
    engine.coordinates = coordinates
    engine.seed_block_index = 0
    engine.identity = SimpleNamespace(namespace="TEST_ONLY|SGSP-RSCF-EXTENDED-PREFLIGHT")
    engine._helper = helper
    engine.native_identity = helper.native_identity
    engine._arms = {}
    for arm in ("PHY-TRUST", "EDGE-FLEX"):
        actor = RSCFActor(actor_parameters)
        critic = TerminalCritic(critic_parameters)
        engine._arms[arm] = _ArmState(actor, critic, make_projected_adam(actor, critic))
    engine.completed_updates = 0
    engine._rolling_origin_digest = "0" * 64
    engine._update_receipts = []
    return engine


def run_extended_test_preflight(root: Path | str, service_graph) -> dict[str, object]:
    base = asdict(run_sealed_test_preflight(root))
    actor_parameters = _literal_parameters(ACTOR_PARAMETER_SHAPES, 1)
    critic_parameters = _literal_parameters(CRITIC_PARAMETER_SHAPES, 2)
    helper = RSCFGateBRunner(
        TestIdentity("CASE_PREFLIGHT"),
        actor_parameters=actor_parameters,
        critic_parameters=critic_parameters,
        width=32,
    )
    coordinates = EmpiricalCoordinateAdapter.for_sealed_test_preflight(
        namespace="TEST_ONLY|SGSP-RSCF-EXTENDED-PREFLIGHT",
        secret=b"TEST_ONLY|RSCF_COORDINATE_KEY_00",
    )
    if type(coordinates) is not EmpiricalCoordinateAdapter or coordinates._test_only is not True:
        raise RuntimeError("extended preflight did not receive the exact TEST-only production adapter")

    baseline_wall_started = time.perf_counter()
    helper.run_test_update(fixture_update_index=0, verify_reverse_order=False)
    baseline_update_wall = time.perf_counter() - baseline_wall_started

    tape_engine = _test_engine(helper, actor_parameters, critic_parameters, coordinates)
    coordinate_tape_started = time.perf_counter()
    tape_schedules = tape_engine.selector_schedules(0)
    tape_batches = tuple(
        tape_engine._episode_batch(
            roster=schedule.roster_size,
            update=0,
            episode_offset=0,
            phase="TRAINING",
            schedule=schedule,
        )
        for schedule in tape_schedules
    )
    coordinate_tape_wall = time.perf_counter() - coordinate_tape_started
    if tuple(batch.n_agents.shape for batch in tape_batches) != ((32,), (32,)):
        raise RuntimeError("extended preflight coordinate-tape shape changed")

    engine = _test_engine(helper, actor_parameters, critic_parameters, coordinates)
    production_wall_started = time.perf_counter()
    receipt = engine.run_update(0)
    production_update_wall = time.perf_counter() - production_wall_started
    if not receipt.structural_valid or receipt.batch_roster_order != (9, 15) * 32:
        raise RuntimeError("extended preflight production update failed structure or alternating order")

    baseline_eval_started = time.perf_counter()
    helper._evaluation_trace_bundle(arm_name="PHY-TRUST", roster_size=6)
    baseline_eval_wall = time.perf_counter() - baseline_eval_started
    production_eval_started = time.perf_counter()
    engine._evaluation_accumulators(6, "PHY-TRUST")
    production_eval_wall = time.perf_counter() - production_eval_started

    service_started = time.perf_counter()
    observed_service_graph = service_graph()
    service_wall = time.perf_counter() - service_started
    measured_update_overhead = max(0.0, production_update_wall - baseline_update_wall)
    update_overhead = max(measured_update_overhead, coordinate_tape_wall)
    evaluation_delta = max(0.0, production_eval_wall - baseline_eval_wall)
    evaluation_overhead = production_eval_wall
    scaled_overhead = (
        update_overhead * (24 * 512)
        + evaluation_overhead * (24 * 8)
        + float(base["lifecycle_io_wall_seconds"]) * (24 * 512)
        + service_wall
    )
    projected = PROJECTED_PANEL_WALL_SECONDS + scaled_overhead
    required_lease = math.ceil(projected + LEASE_FINALIZATION_MARGIN_SECONDS)
    report: dict[str, object] = {
        **base,
        "schema": EXTENDED_PREFLIGHT_SCHEMA,
        "service_graph": observed_service_graph,
        "test_only_baseline_update_wall_seconds": baseline_update_wall,
        "test_only_exact_coordinate_tape_wall_seconds": coordinate_tape_wall,
        "test_only_production_update_wall_seconds": production_update_wall,
        "test_only_measured_update_orchestration_delta_seconds": measured_update_overhead,
        "test_only_update_orchestration_overhead_seconds": update_overhead,
        "test_only_baseline_evaluation_cell_wall_seconds": baseline_eval_wall,
        "test_only_production_evaluation_cell_wall_seconds": production_eval_wall,
        "test_only_evaluation_orchestration_delta_seconds": evaluation_delta,
        "test_only_evaluation_orchestration_overhead_seconds": evaluation_overhead,
        "test_only_launcher_service_wall_seconds": service_wall,
        "scaled_production_overhead_seconds": scaled_overhead,
        "accepted_base_projected_wall_seconds": PROJECTED_PANEL_WALL_SECONDS,
        "production_projected_wall_seconds": projected,
        "required_lease_remaining_seconds": required_lease,
        "exact_coordinate_adapter_class": (
            "experiments.candidates.semantic_graphon_shared_policy_rscf_r01."
            "production_boundary.EmpiricalCoordinateAdapter"
        ),
        "exact_coordinate_adapter_test_only": True,
        "production_launch_contract": exact_future_launch_contract(),
        "formal_activity": False,
        "empirical_objects_created": 0,
    }
    report["production_preflight_sha256"] = canonical_sha256(report)
    return report


def install_extended_preflight_artifact(
    report: dict[str, object], path: Path | str
) -> tuple[Path, str]:
    """Install the exact TEST-only report as a durable create-only artifact."""

    report_core = dict(report)
    report_sha = report_core.pop("production_preflight_sha256", None)
    if not isinstance(report_sha, str) or canonical_sha256(report_core) != report_sha:
        raise RuntimeError("extended preflight report digest changed before installation")
    envelope = {
        "schema": PREFLIGHT_ARTIFACT_SCHEMA,
        "report_sha256": report_sha,
        "report": report,
    }
    data = canonical_json_bytes(envelope)
    artifact_path = Path(path).resolve(strict=False)
    return artifact_path, _atomic_write_once(artifact_path, data)
