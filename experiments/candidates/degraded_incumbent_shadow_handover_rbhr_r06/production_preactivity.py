"""Current-byte TEST-only conformance and cost measurement for DISH r06."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Iterable

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.production_preactivity import (
    process_io_bytes,
    process_memory_bytes,
)
from .production_backend import (
    TestNativeBatch, TestProtocolNativeBatch, artifact_identity, empty_step_rows,
    native_natural_protocol_trace, native_protocol_audit,
    native_protocol_transition_probe, recovery_witness_test_rows, rng_words_test_native,
)
from .production_contract import (
    ARMS, BLOCKS, SCIENCE_FILES, TEST_NAMESPACE, TestAuthority,
    complete_inventory, science_root,
)
from .production_inference import (
    aggregate_schedule_regime_intersections, common_anchor_classify,
    inference_manifest, joint_max_t, reduce_speed_cell,
)
from .production_lifecycle import (
    BINDING_COMPONENTS, lifecycle_binding_manifest, run_r06_real_byte_lifecycle_seam,
)
from .production_population import (
    address, complete_evaluation_coordinates, population_manifest,
)
from .production_training import retained_training_binding, run_full_4096_test_update


HIGH_GATES = {
    "cpu_core_hours": 560.0, "wall_hours": 110.0,
    "aggregate_rss_gib": 40.0, "scratch_gib": 120.0,
    "durable_gib": 16.0, "total_io_gib": 400.0,
}
ORDINARY_GATES = {"cpu_core_hours": 320.0, "wall_hours": 65.0}


class R06AcceptanceError(RuntimeError):
    pass


def verify_science_composite(repository_root: Path) -> dict[str, str]:
    root = science_root(repository_root)
    observed: dict[str, str] = {}
    for name, expected in SCIENCE_FILES:
        path = root / name
        if not path.is_file():
            raise R06AcceptanceError(f"science member absent: {name}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise R06AcceptanceError(f"science member changed: {name}")
        observed[name] = digest
    return observed


def _rollout_rows(width: int, steps: int) -> np.ndarray:
    rows = np.repeat(empty_step_rows(width)[None, :], steps, axis=0)
    tick = np.arange(steps, dtype=np.float64)[:, None]
    lane = np.arange(width, dtype=np.float64)[None, :]
    rows["raw_action"][:, :, 0] = 0.7 * np.sin(tick * 0.03 + lane * 0.01)
    rows["raw_action"][:, :, 1] = 0.7 * np.cos(tick * 0.02 + lane * 0.01)
    rows["raw_action"][:, :, 2] = -rows["raw_action"][:, :, 0]
    rows["raw_action"][:, :, 3] = -rows["raw_action"][:, :, 1]
    rows["prediction_mean"][:, :, 0] = tick * 0.4
    rows["prediction_mean"][:, :, 1] = -120.0
    rows["prediction_mean"][:, :, 4] = tick * 0.4
    rows["prediction_mean"][:, :, 5] = -120.0
    rows["prepare"] = 1; rows["commit"] = 1; rows["promotion_alpha"] = 1.0
    return rows


def benchmark_native_rollout(width: int, *, steps: int = 1_200) -> dict[str, object]:
    batch = TestNativeBatch(width, TestAuthority()); rows = _rollout_rows(width, steps)
    started = time.perf_counter(); output = batch.rollout(rows); elapsed = time.perf_counter() - started
    digest = hashlib.sha256()
    for key in ("service", "terminal", "tick", "protocol_bytes", "total_energy"):
        digest.update(np.ascontiguousarray(output[key]).tobytes())
    return {
        "width": width, "steps": steps, "lane_ticks": width * steps,
        "wall_seconds": elapsed, "lane_ticks_per_second": width * steps / elapsed,
        "output_sha256": digest.hexdigest(),
        "all_finite": bool(np.isfinite(output["actor"]).all() and np.isfinite(output["critic"]).all()),
        "test_only": True,
    }


def _native_training_fragments() -> tuple[dict[str, torch.Tensor], dict[str, object]]:
    width, steps = 32, 128
    rows = _rollout_rows(width, steps)
    batch = TestProtocolNativeBatch(width, TestAuthority())
    output = batch.rollout(rows)
    def fragment(value: np.ndarray) -> np.ndarray:
        return np.ascontiguousarray(value.transpose(1, 0, *range(2, value.ndim)).reshape(64, 64, *value.shape[2:]))
    observation = fragment(output["actor"])
    critic = np.ascontiguousarray(output["critic"].transpose(1, 0, 2).reshape(4_096, 58))
    renew = fragment(output["renew"]).astype(bool)
    terminal_lane_tick = np.ascontiguousarray(output["terminal"].T)
    action = fragment(rows["raw_action"])
    prepare = fragment(rows["prepare"][:, :, 0]).astype(np.float32)
    commit = fragment(rows["commit"][:, :, 0]).astype(np.float32)
    service = np.ascontiguousarray(output["service"].T).astype(np.float32)
    actor_flat = observation.reshape(4_096, 4, 54)
    snapshot = fragment(output["snapshot_payload"])
    snapshot_mask = fragment(output["snapshot_delivery_mask"]).astype(bool)
    promotion = fragment(output["cas_applied"]).astype(bool)
    reset = np.ones((64, 64), dtype=np.float32)
    reset[terminal_lane_tick.reshape(64, 64).astype(bool)] = 0.0
    target = critic[:, :4].copy()
    links = fragment(output["readiness_candidate"]).reshape(4_096, 2)
    missing = actor_flat[:, 0, 14].copy()
    q_labels = np.repeat((service.T.reshape(4_096, 1) > 0).astype(np.float32), 20, axis=1)
    fragments = {
        "observation": torch.from_numpy(observation).float(),
        "critic": torch.from_numpy(critic).float(),
        "snapshot": torch.from_numpy(snapshot).float(),
        "snapshot_mask": torch.from_numpy(snapshot_mask),
        "promotion_mask": torch.from_numpy(promotion),
        "promotion_alpha": torch.ones((64, 64), dtype=torch.float32),
        "reset_mask": torch.from_numpy(reset),
        "renew": torch.from_numpy(renew),
        "prepare_mask": torch.from_numpy(renew),
        "commit_mask": torch.from_numpy(renew),
        "action": torch.from_numpy(action).float(),
        "prepare_outcome": torch.from_numpy(prepare).float(),
        "commit_outcome": torch.from_numpy(commit).float(),
        "reward": torch.from_numpy(service).float(),
        "done": torch.from_numpy(terminal_lane_tick),
        "target": torch.from_numpy(target).float(),
        "links": torch.from_numpy(np.repeat(links[:, None, :], 4, axis=1)).float(),
        "missing": torch.from_numpy(np.repeat(missing[:, None], 4, axis=1)).float(),
        "q_labels": torch.from_numpy(q_labels).float(),
        "q_mask": torch.ones(4_096, dtype=torch.bool),
        "next_mask": torch.ones(4_096, dtype=torch.bool),
        "q_copy_index": torch.ones(4_096, dtype=torch.long),
    }
    digest = hashlib.sha256()
    for name in sorted(fragments):
        digest.update(name.encode("ascii") + b"\0")
        digest.update(fragments[name].numpy().tobytes())
    return fragments, {
        "schema": "DISH_RBHR_R06_NATIVE_FRAGMENT_BINDING_V1",
        "transitions": 4_096, "native_rows": True,
        "sha256": digest.hexdigest(), "test_only": True,
    }


def run_native_connected_training_seam() -> dict[str, object]:
    fragments, binding = _native_training_fragments()
    value = run_full_4096_test_update(
        TestAuthority(), fragments=fragments, source_label="R06_NATIVE_TEST_HOST_ROWS",
    )
    return {**value, "native_fragment_binding": binding}


def run_analyzer_seam() -> dict[str, object]:
    started = time.perf_counter()
    block = np.arange(24, dtype=np.float64)[:, None]
    estimand = np.arange(32, dtype=np.float64)[None, :]
    values = 0.04 * np.sin((block + 1) * (estimand + 1) * 0.017) + 0.001 * estimand
    values[:, 0] = 0.0
    intervals = joint_max_t(values)
    common = {"protocol_ok": True, "comp": True, "witness": True, "headroom": True, "precision": True, "support": True}
    atomic = {}
    for regime in ("TARGET_VISUAL_MASK", "TERRAIN_RELAY_MASK"):
        for schedule in ("K8", "K4_TO_K12", "K12_TO_K4"):
            anchors = {speed: {"core": speed in ("SPEED_4", "SPEED_8")} for speed in ("SPEED_4", "SPEED_6", "SPEED_8")}
            atomic[(regime, schedule)] = common_anchor_classify(common, anchors)
    aggregate = aggregate_schedule_regime_intersections(atomic)
    return {
        "schema": "DISH_RBHR_R06_RESULT_BLIND_ANALYZER_SEAM_V1",
        "resamples": intervals["resamples"], "estimands": intervals["estimands"],
        "all_intervals_finite": intervals["all_finite"],
        "common_anchor_intersection": aggregate["cross_regime"]["common_anchor_speeds"],
        "first_match_branch_count": len(BRANCHES := tuple(range(15))),
        "wall_seconds": time.perf_counter() - started,
        "test_only": True, "question_relevant_output": False,
    }


def _component_payloads(repository_root: Path, native: dict[str, object], training: dict[str, object], analyzer: dict[str, object]) -> dict[str, bytes]:
    encoded = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    native_bytes = Path(str(native["artifact"])).read_bytes()
    population = population_manifest(); inference = inference_manifest()
    payloads = {
        "science_composite": (science_root(repository_root) / "DISH_RBHR_R06_SCIENCE_COMPOSITE_20260822.md").read_bytes(),
        "production_source": Path(__file__).read_bytes(),
        "native_artifact": native_bytes,
        "model": encoded({"state_sha256": training["model_state_sha256"], "test_only": True}),
        "optimizer": encoded({"state_sha256": training["optimizer_state_sha256"], "test_only": True}),
        "actor_welford": encoded({"count": training["welford_counts"]["actor"]}),
        "snapshot_welford": encoded({"count": training["welford_counts"]["snapshot"]}),
        "critic_welford": encoded({"count": training["welford_counts"]["critic"]}),
        "rng_frontier": encoded({"prefix": "DISH/RBHR/R06", "test_only": True}),
        "evaluation_population_frontier": encoded(population),
        "fork_frontier": encoded(native_protocol_transition_probe()),
        "reducer_frontier": encoded(inference),
        "analyzer_frontier": encoded(analyzer),
    }
    if tuple(sorted(payloads)) != tuple(sorted(BINDING_COMPONENTS)):
        raise R06AcceptanceError("r06 lifecycle payload inventory differs")
    return payloads


def storage_projection(checkpoint_bytes: int) -> dict[str, float]:
    jobs = BLOCKS * len(ARMS); generations = 64
    checkpoint_writes = checkpoint_bytes * jobs * generations
    final_checkpoint = checkpoint_bytes * jobs
    inventory = complete_inventory()
    frontier = 768 * jobs * generations
    tape_audit = int(inventory["evaluation_tapes"]) * 160
    evaluation = int(inventory["evaluation_episodes"]) * 512
    fork = int(inventory["claim_tapes"]) * 2 * 384
    analyzer = 512 * 24 * 256 * 8 + 99_999 * 8 + 24 * 6_990 * 8
    total_io = 2 * checkpoint_writes + final_checkpoint + frontier + tape_audit + evaluation + fork + analyzer
    durable = final_checkpoint + frontier + tape_audit + evaluation + fork
    scratch = max(8 * checkpoint_bytes * 2, analyzer, 240 * 1_200 * (2_280 + 192))
    return {
        "measured_formula_total_io_gib": total_io / 1024**3,
        "measured_formula_durable_gib": durable / 1024**3,
        "measured_formula_scratch_gib": scratch / 1024**3,
    }


def component_projection(rollout: dict[str, object], training: dict[str, object], analyzer: dict[str, object]) -> dict[str, object]:
    known_native_ticks = 676_116_480
    native_cpu = known_native_ticks / float(rollout["lane_ticks_per_second"]) / 3600.0
    full_updates = 120 * 1_024
    replay_cpu = float(training["wall_seconds"]) * full_updates / 3600.0
    analyzer_cpu = float(analyzer["wall_seconds"]) * 6_990 / int(analyzer["estimands"]) / 3600.0
    total = native_cpu + replay_cpu + analyzer_cpu
    return {
        "formula": "676116480/current_native_lane_ticks_per_second + 122880*current_native_connected_4096_update_seconds + current_analyzer_seconds_per_estimand*6990",
        "known_native_ticks": known_native_ticks,
        "native_lane_ticks_per_second": rollout["lane_ticks_per_second"],
        "native_cpu_core_hours": native_cpu,
        "full_updates": full_updates,
        "full_4096_update_seconds": training["wall_seconds"],
        "training_cpu_core_hours": replay_cpu,
        "analyzer_cpu_core_hours": analyzer_cpu,
        "cpu_core_hours": total,
        "candidate_scanner_or_admission_assay": False,
    }


def run_preactivity_acceptance(repository_root: Path, *, widths: Iterable[int] = (32, 48, 240)) -> dict[str, object]:
    started = time.perf_counter(); io_before = process_io_bytes(os.getpid()); rss_before = process_memory_bytes(os.getpid())
    science = verify_science_composite(repository_root)
    population = population_manifest(); inference = inference_manifest(); inventory = complete_inventory()
    native = artifact_identity(); rollouts = [benchmark_native_rollout(width) for width in widths]
    training = run_native_connected_training_seam(); analyzer = run_analyzer_seam()
    rng_address = address(
        purpose="INFERENCE", block=None, split="BOOTSTRAP", regime="NONE", schedule="NONE",
        evaluation_slot=None, inference_resample=1, field="BOOTSTRAP_BLOCK", draw_index=0,
    )
    rng_words = rng_words_test_native((rng_address,), TestAuthority())
    wire = native_protocol_audit(); transition = native_protocol_transition_probe(); natural = native_natural_protocol_trace()
    witness_rows = recovery_witness_test_rows(16, TestAuthority())
    witness_digest = hashlib.sha256(witness_rows.tobytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="dish-rbhr-r06-preactivity-") as temporary:
        lifecycle = run_r06_real_byte_lifecycle_seam(
            Path(temporary), _component_payloads(repository_root, native, training, analyzer), TestAuthority(),
        )
        lifecycle_bytes = sum(path.stat().st_size for path in Path(temporary).rglob("*") if path.is_file())
    storage = storage_projection(int(training["checkpoint_resume_bytes"]))
    projection = component_projection(rollouts[0], training, analyzer)
    io_after = process_io_bytes(os.getpid()); rss_after = process_memory_bytes(os.getpid())
    if not all((population["geometry_factorial_complete"], population["identity_combinations_twice_per_speed_cell"], population["clock_support_nonempty_per_speed_cell"], population["turn_magnitude_exact_across_blocks"])):
        raise R06AcceptanceError("deterministic population conformance failed")
    return {
        "schema": "DISH_RBHR_R06_ENGINEERING_CONFORMANCE_ACCEPTANCE_V1",
        "namespace": TEST_NAMESPACE, "test_only": True,
        "scientific_master": False, "identity": False, "coordinate": False,
        "evaluation_tape": False, "scientific_model_or_checkpoint": False,
        "training_or_evaluation_activity": False, "inference_result": False,
        "question_relevant_output": False,
        "science_composite": science, "inventory": inventory,
        "population_manifest": population, "inference_manifest": inference,
        "native": native, "rollout_measurements": rollouts,
        "training_measurement": training, "training_binding": retained_training_binding(),
        "analyzer_measurement": analyzer,
        "native_rng_measurement": {"request_count": 1, "sha256": hashlib.sha256(np.asarray(rng_words, dtype=">u8").tobytes()).hexdigest(), "test_only": True},
        "native_wire_protocol": wire, "native_transition": transition,
        "native_natural_protocol": natural,
        "native_recovery_witness_seam": {
            "rows": int(witness_rows.size), "sha256": witness_digest,
            "population_selector": False, "test_only": True,
            "question_relevant_output": False,
        },
        "lifecycle_binding": lifecycle_binding_manifest(), "lifecycle_measurement": lifecycle,
        "lifecycle_disk_bytes": lifecycle_bytes,
        "storage_measurement": storage, "component_projection": projection,
        "process_io_delta": {name: io_after[name] - io_before[name] for name in io_before},
        "process_rss_before_bytes": rss_before["current"],
        "process_rss_after_bytes": rss_after["current"],
        "high_gates": HIGH_GATES, "ordinary_gates": ORDINARY_GATES,
        "native_first": True, "python_environment_or_rollout_fallback": False,
        "wall_seconds": time.perf_counter() - started,
    }


__all__ = [
    "HIGH_GATES", "ORDINARY_GATES", "R06AcceptanceError", "benchmark_native_rollout",
    "process_io_bytes", "process_memory_bytes", "run_native_connected_training_seam",
    "run_preactivity_acceptance", "verify_science_composite",
]
