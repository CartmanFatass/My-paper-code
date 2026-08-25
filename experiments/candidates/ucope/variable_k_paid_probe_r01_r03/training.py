"""Result-blind S1 training, support, and deterministic-reduction surface."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import torch

from envs.native.production_backend import require_cpp_batched_production

from . import native_backend
from .contract import (
    COMPONENT,
    K_TRAIN,
    S1_TEST_NAMESPACE,
    S1_TEST_REQUEST,
    require_s1_test_request,
)
from .model import LearnerBundle, make_paired_bundles


def _array_digest(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(repr(value.shape).encode("ascii"))
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def fixed_fp32_tree(values: np.ndarray) -> np.float32:
    current = np.asarray(values, dtype=np.float32).reshape(-1)
    if current.size == 0:
        raise ValueError("fixed FP32 reduction requires at least one value")
    width = 1
    while width < current.size:
        width <<= 1
    padded = np.zeros(width, dtype=np.float32)
    padded[: current.size] = current
    while padded.size > 1:
        padded = np.asarray(padded[0::2] + padded[1::2], dtype=np.float32)
    return np.float32(padded[0])


@dataclass(frozen=True)
class ReductionFrontier:
    count: int
    ordered_values_sha256: str
    total_fp32_bits: int

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": "UCOPE_R01_R03_S1_REDUCTION_FRONTIER_V1",
            "count": self.count,
            "ordered_values_sha256": self.ordered_values_sha256,
            "total_fp32_bits": self.total_fp32_bits,
        }


def reduction_frontier(parts: Sequence[tuple[int, np.ndarray]]) -> ReductionFrontier:
    """Reassemble global row order before one partition-independent FP32 tree."""

    ordered = sorted(parts, key=lambda item: item[0])
    expected = 0
    values: list[np.ndarray] = []
    for start, part in ordered:
        array = np.asarray(part, dtype=np.float32).reshape(-1)
        if start != expected or array.size == 0:
            raise ValueError("reduction parts must form one nonempty gap-free global order")
        values.append(array)
        expected += array.size
    if not values:
        raise ValueError("reduction frontier requires at least one part")
    combined = np.concatenate(values).astype(np.float32, copy=False)
    total = fixed_fp32_tree(combined)
    return ReductionFrontier(
        count=int(combined.size),
        ordered_values_sha256=_array_digest(combined),
        total_fp32_bits=int(total.view(np.uint32)),
    )


@dataclass
class SupportCounters:
    root_actions: np.ndarray
    tail_actions: np.ndarray
    panel_roster_cells: np.ndarray
    displayed_counts: np.ndarray

    @classmethod
    def empty(cls) -> "SupportCounters":
        return cls(
            root_actions=np.zeros((3, 6), dtype=np.int64),
            tail_actions=np.zeros((3, 5), dtype=np.int64),
            panel_roster_cells=np.zeros((3, 4), dtype=np.int64),
            displayed_counts=np.zeros((3, 7), dtype=np.int64),
        )

    def validate(self) -> None:
        expected = {
            "root_actions": ((3, 6), self.root_actions),
            "tail_actions": ((3, 5), self.tail_actions),
            "panel_roster_cells": ((3, 4), self.panel_roster_cells),
            "displayed_counts": ((3, 7), self.displayed_counts),
        }
        for name, (shape, value) in expected.items():
            if not isinstance(value, np.ndarray) or value.dtype != np.int64 or value.shape != shape or not value.flags.c_contiguous:
                raise TypeError(f"{name} must be a C-contiguous int64 array with shape {shape}")
            if np.any(value < 0):
                raise ValueError(f"{name} must be monotone nonnegative state")

    def add_(self, delta: "SupportCounters") -> None:
        self.validate()
        delta.validate()
        for name in ("root_actions", "tail_actions", "panel_roster_cells", "displayed_counts"):
            target = getattr(self, name)
            addition = getattr(delta, name)
            updated = target + addition
            if np.any(updated < target):
                raise OverflowError("support counter overflow")
            target[:] = updated

    def as_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "schema": "UCOPE_R01_R03_S1_SUPPORT_COUNTERS_V1",
            "root_actions": self.root_actions.tolist(),
            "tail_actions": self.tail_actions.tolist(),
            "panel_roster_cells": self.panel_roster_cells.tolist(),
            "displayed_counts": self.displayed_counts.tolist(),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "SupportCounters":
        if value.get("schema") != "UCOPE_R01_R03_S1_SUPPORT_COUNTERS_V1":
            raise ValueError("support-counter schema mismatch")
        counters = cls(
            root_actions=np.ascontiguousarray(value["root_actions"], dtype=np.int64),
            tail_actions=np.ascontiguousarray(value["tail_actions"], dtype=np.int64),
            panel_roster_cells=np.ascontiguousarray(value["panel_roster_cells"], dtype=np.int64),
            displayed_counts=np.ascontiguousarray(value["displayed_counts"], dtype=np.int64),
        )
        counters.validate()
        return counters

    def sha256(self) -> str:
        self.validate()
        return _array_digest(
            self.root_actions, self.tail_actions, self.panel_roster_cells,
            self.displayed_counts,
        )


def support_delta(
    *, panel: int, root_actions: np.ndarray, tail_actions: np.ndarray,
    regimes: np.ndarray, displayed_marks: np.ndarray,
) -> SupportCounters:
    if root_actions.shape != (768,) or root_actions.dtype != np.int32:
        raise TypeError("root actions must be one int32 768-lane vector")
    if tail_actions.shape != (768,) or tail_actions.dtype != np.int32:
        raise TypeError("tail actions must be one int32 768-lane vector")
    if regimes.shape != (768, 3) or regimes.dtype != np.int32:
        raise TypeError("regimes must be one int32 [768,3] array")
    if displayed_marks.shape != (768, 6) or displayed_marks.dtype != np.int32:
        raise TypeError("displayed marks must be one int32 [768,6] array")
    delta = SupportCounters.empty()
    for arm in range(3):
        start, stop = arm * 256, (arm + 1) * 256
        root = root_actions[start:stop]
        tail = tail_actions[start:stop]
        delta.root_actions[arm] = np.bincount(root, minlength=6).astype(np.int64)
        probed_tail = tail[tail >= 0]
        if probed_tail.size:
            delta.tail_actions[arm] = np.bincount(probed_tail, minlength=5).astype(np.int64)
        panel_rows = regimes[start:stop]
        if panel == 0:
            cell = panel_rows[:, 0]
        elif panel == 1:
            cell = panel_rows[:, 0] * 2 + panel_rows[:, 1]
        elif panel == 2:
            cell = panel_rows[:, 0] * 2 + panel_rows[:, 2]
        else:
            raise ValueError("panel must be 0..2")
        delta.panel_roster_cells[arm] = np.bincount(cell, minlength=4).astype(np.int64)
        probe_mask = root == 0
        counts = displayed_marks[start:stop][probe_mask].sum(axis=1, dtype=np.int32)
        if counts.size:
            delta.displayed_counts[arm] = np.bincount(counts, minlength=7).astype(np.int64)
    delta.validate()
    return delta


def _torch(array: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(np.ascontiguousarray(array)).to(dtype=torch.float32)


def _optimizer_steps(bundle: LearnerBundle) -> set[int]:
    return {
        int(state["step"].item())
        for state in bundle.optimizer.state.values()
        if "step" in state
    }


def frozen_update(
    bundle: LearnerBundle, *, root_features: torch.Tensor, root_baseline: torch.Tensor,
    root_actions: torch.Tensor, root_returns: torch.Tensor,
    tail_features: torch.Tensor, tail_baseline: torch.Tensor,
    tail_actions: torch.Tensor, tail_returns: torch.Tensor,
    probe_mask: torch.Tensor, batch_number: int,
) -> dict[str, float]:
    """Apply exactly one frozen joint scorer/baseline AdamW step."""

    tensors = (
        root_features, root_baseline, root_returns, tail_features, tail_baseline,
        tail_returns, probe_mask,
    )
    if any(value.dtype != torch.float32 for value in tensors):
        raise TypeError("the S1 learner hot path is FP32 only")
    if root_actions.dtype != torch.int64 or tail_actions.dtype != torch.int64:
        raise TypeError("actions must use fixed-width integer tensors")
    if not 1 <= batch_number <= 320:
        raise ValueError("batch_number must be in 1..320")
    if root_features.shape != (256, 6, 13) or tail_features.shape != (256, 5, 13):
        raise ValueError("training must retain the exact 256-episode candidate shapes")
    root_logits = bundle.scorer(root_features)
    tail_logits = bundle.scorer(tail_features)
    root_log_probabilities = torch.log_softmax(root_logits, dim=-1)
    tail_log_probabilities = torch.log_softmax(tail_logits, dim=-1)
    root_probabilities = torch.softmax(root_logits, dim=-1)
    tail_probabilities = torch.softmax(tail_logits, dim=-1)
    root_values = bundle.baseline(root_baseline)
    tail_values = bundle.baseline(tail_baseline)
    root_selected = root_log_probabilities.gather(1, root_actions[:, None]).squeeze(1)
    tail_selected = tail_log_probabilities.gather(1, tail_actions[:, None]).squeeze(1)
    root_advantage = (root_returns - root_values).detach()
    tail_advantage = (tail_returns - tail_values).detach()
    root_entropy = -(root_probabilities * root_log_probabilities).sum(dim=-1)
    tail_entropy = -(tail_probabilities * tail_log_probabilities).sum(dim=-1)
    beta = torch.tensor(0.01 * (320 - batch_number) / 319, dtype=torch.float32)
    batch_size = np.float32(256.0)
    policy_loss = -(
        root_selected * root_advantage + probe_mask * tail_selected * tail_advantage
    ).sum() / batch_size
    policy_loss = policy_loss - beta * (
        root_entropy + probe_mask * tail_entropy
    ).sum() / batch_size
    baseline_loss = (
        (root_values - root_returns).square()
        + probe_mask * (tail_values - tail_returns).square()
    ).sum() / batch_size
    total_loss = policy_loss + torch.tensor(0.5, dtype=torch.float32) * baseline_loss
    before_steps = _optimizer_steps(bundle)
    bundle.optimizer.zero_grad(set_to_none=True)
    total_loss.backward()
    gradient_norm = torch.nn.utils.clip_grad_norm_(tuple(bundle.parameters()), max_norm=1.0)
    bundle.optimizer.step()
    after_steps = _optimizer_steps(bundle)
    if before_steps and after_steps != {next(iter(before_steps)) + 1}:
        raise RuntimeError("joint AdamW did not advance exactly once")
    if not before_steps and after_steps != {1}:
        raise RuntimeError("first joint AdamW step is not exactly one")
    if any(parameter.dtype != torch.float32 for parameter in bundle.parameters()):
        raise RuntimeError("learner parameter dtype widened")
    for state in bundle.optimizer.state.values():
        if any(torch.is_tensor(value) and value.dtype != torch.float32 for value in state.values()):
            raise RuntimeError("optimizer state dtype widened")
    return {
        "policy_loss": float(policy_loss.detach()),
        "baseline_loss": float(baseline_loss.detach()),
        "total_loss": float(total_loss.detach()),
        "gradient_norm": float(gradient_norm.detach()),
        "entropy_beta": float(beta),
    }


def prepare_training_batch(
    bundles: Sequence[LearnerBundle], *, namespace: str, test_seed: int,
    panel: int, batch_index: int, build_root: Path | None = None,
) -> dict[str, object]:
    require_s1_test_request(namespace, test_seed, S1_TEST_REQUEST)
    if len(bundles) != 3 or panel not in (0, 1, 2) or not 0 <= batch_index < 320:
        raise ValueError("S1 work unit requires three arms, panel 0..2 and batch 0..319")
    require_cpp_batched_production(
        COMPONENT, backend="cpp", batch_width=768, build_root=build_root
    )
    arms = np.repeat(np.arange(3, dtype=np.int32), 256)
    population = native_backend.counter_population(
        seed=test_seed, panel=panel, batch_index=batch_index, width=768,
        build_root=build_root,
    )
    native = native_backend.reset_batch(
        seed=test_seed, panel=panel, batch_index=batch_index, arms=arms,
        build_root=build_root,
    )
    try:
        root_probabilities = np.empty((768, 6), dtype=np.float32)
        with torch.no_grad():
            for arm in range(3):
                start, stop = arm * 256, (arm + 1) * 256
                logits = bundles[arm].scorer(_torch(native.root_features[start:stop]))
                root_probabilities[start:stop] = torch.softmax(logits, dim=-1).cpu().numpy()
        root_actions = native_backend.sample_actions(
            root_probabilities, seed=test_seed, panel=panel, batch_index=batch_index,
            arms=arms, decision_code=0, legal_counts=np.full(768, 6, dtype=np.int32),
            build_root=build_root,
        )
        root = native.root_step(root_actions)
        tail_probabilities = np.empty((768, 5), dtype=np.float32)
        with torch.no_grad():
            for arm in range(3):
                start, stop = arm * 256, (arm + 1) * 256
                logits = bundles[arm].scorer(_torch(root["tail_features"][start:stop]))
                tail_probabilities[start:stop] = torch.softmax(logits, dim=-1).cpu().numpy()
        probe_mask_np = root_actions == 0
        legal_tail = np.where(probe_mask_np, 5, 0).astype(np.int32)
        tail_actions = native_backend.sample_actions(
            tail_probabilities, seed=test_seed, panel=panel, batch_index=batch_index,
            arms=arms, decision_code=1, legal_counts=legal_tail,
            build_root=build_root,
        )
        tail_components = native.tail_step(tail_actions)
        terminal = native.terminal()
        if not np.array_equal(population["regimes"], native.regimes):
            raise RuntimeError("complete counter population roster differs from reset")
        if not np.array_equal(population["actual_marks"][probe_mask_np], root["actual_marks"][probe_mask_np]):
            raise RuntimeError("actual probe population differs from selected lifecycle marks")
        if not np.array_equal(population["displayed_marks"][probe_mask_np], root["displayed_marks"][probe_mask_np]):
            raise RuntimeError("displayed probe population differs from selected lifecycle marks")
        rows: list[dict[str, torch.Tensor]] = []
        for arm in range(3):
            start, stop = arm * 256, (arm + 1) * 256
            components = terminal["components"][start:stop]
            tail_returns = components[:, :3].sum(axis=1, dtype=np.float32)
            rows.append(
                {
                    "root_features": _torch(native.root_features[start:stop]),
                    "root_baseline": _torch(native.root_baselines[start:stop]),
                    "root_actions": torch.from_numpy(root_actions[start:stop].astype(np.int64)),
                    "root_returns": _torch(terminal["totals"][start:stop]),
                    "tail_features": _torch(root["tail_features"][start:stop]),
                    "tail_baseline": _torch(root["tail_baselines"][start:stop]),
                    "tail_actions": torch.from_numpy(np.maximum(tail_actions[start:stop], 0).astype(np.int64)),
                    "tail_returns": _torch(tail_returns),
                    "probe_mask": _torch(probe_mask_np[start:stop].astype(np.float32)),
                }
            )
        support = support_delta(
            panel=panel, root_actions=root_actions, tail_actions=tail_actions,
            regimes=native.regimes, displayed_marks=root["displayed_marks"],
        )
        reduction = reduction_frontier(((0, terminal["totals"]),))
        frontier_digest = _array_digest(
            population["regimes"], population["actual_marks"],
            population["displayed_marks"], population["potential_tail"],
            root_actions, tail_actions,
        )
        return {
            "data": rows,
            "support_delta": support,
            "reduction_frontier": reduction,
            "counter_frontier": frontier_digest,
            "population_digest": _array_digest(
                population["regimes"], population["actual_marks"],
                population["displayed_marks"], population["potential_tail"],
            ),
            "action_digest": _array_digest(root_actions, tail_actions),
            "terminal_digest": _array_digest(terminal["components"], terminal["totals"]),
            "question_relevant_output": False,
        }
    finally:
        native.close()


def apply_training_batch(
    bundles: Sequence[LearnerBundle], support: SupportCounters,
    prepared: Mapping[str, object], *, batch_number: int,
) -> list[dict[str, float]]:
    rows = prepared.get("data")
    delta = prepared.get("support_delta")
    if not isinstance(rows, list) or len(rows) != 3 or not isinstance(delta, SupportCounters):
        raise ValueError("prepared S1 training batch is incomplete")
    losses = [
        frozen_update(bundle, **row, batch_number=batch_number)
        for bundle, row in zip(bundles, rows, strict=True)
    ]
    support.add_(delta)
    return losses


def all_six_arm_semantic_digest(*, build_root: Path | None = None) -> dict[str, object]:
    """Exercise learned feature shapes and all three nonlearned action primitives."""

    periods = np.asarray(K_TRAIN, dtype=np.int32)
    digest = hashlib.sha256()
    calls = 0
    for panel in range(3):
        for count in range(7):
            actions = native_backend.nonlearned_actions(
                panel=panel, displayed_count=count, periods=periods,
                build_root=build_root,
            )
            digest.update(json_bytes(actions))
            calls += 1
    return {
        "learned_arms": ("COUNT_FP32", "RAW_FP32", "BELIEF_FEATURE_FP32"),
        "nonlearned_arms": ("BELIEF_DP", "IMMEDIATE_DP", "FORCED_PROBE_BLIND_DP"),
        "nonlearned_calls": calls,
        "action_only_sha256": digest.hexdigest(),
        "numeric_values_exposed": False,
        "question_relevant_output": False,
    }


def json_bytes(value: Mapping[str, object]) -> bytes:
    return repr(tuple(sorted(value.items()))).encode("ascii")


def _frontier_metadata(
    *, test_seed: int, test_seed_slot: int, panel: int, completed_batch: int,
    counter_frontier: str, reduction: ReductionFrontier,
    source_sha256: str, native_artifact_sha256: str,
) -> dict[str, object]:
    from .contract import COUNTER_LAYOUT_ID

    return {
        "test_seed": test_seed,
        "test_seed_slot": test_seed_slot,
        "panel": panel,
        "completed_batch": completed_batch,
        "next_batch": completed_batch + 1,
        "counter_frontier": counter_frontier,
        "reduction_frontier": reduction.as_dict(),
        "batch_width": 768,
        "worker_count": 1,
        "torch_threads": torch.get_num_threads(),
        "source_sha256": source_sha256,
        "native_artifact_sha256": native_artifact_sha256,
        "counter_layout_id": COUNTER_LAYOUT_ID,
    }


def run_s1_semantic_core_coupon(
    *, namespace: str, test_seed: int, test_seed_slot: int, panel: int,
    work_root: Path, build_root: Path | None = None,
) -> dict[str, object]:
    """Prove the S1 work-unit frontier and next-batch resume on TEST state."""

    from . import checkpoint

    require_s1_test_request(namespace, test_seed, S1_TEST_REQUEST)
    if test_seed_slot not in range(10):
        raise ValueError("test_seed_slot must be in 0..9")
    torch.set_num_threads(1)
    identity = native_backend.native_artifact_identity(build_root=build_root)
    uninterrupted = make_paired_bundles(seed=test_seed, panel=panel)
    support = SupportCounters.empty()
    first = prepare_training_batch(
        uninterrupted, namespace=namespace, test_seed=test_seed, panel=panel,
        batch_index=0, build_root=build_root,
    )
    first_losses = apply_training_batch(
        uninterrupted, support, first, batch_number=1
    )
    first_reduction = first["reduction_frontier"]
    if not isinstance(first_reduction, ReductionFrontier):
        raise RuntimeError("first reduction frontier is malformed")
    metadata_one = _frontier_metadata(
        test_seed=test_seed,
        test_seed_slot=test_seed_slot,
        panel=panel,
        completed_batch=1,
        counter_frontier=str(first["counter_frontier"]),
        reduction=first_reduction,
        source_sha256=str(identity["source_sha256"]),
        native_artifact_sha256=str(identity["artifact_sha256"]),
    )
    frontier_path = Path(work_root).resolve() / "ucope_r01_r03_s1_frontier.TEST_ONLY.pt"
    frontier_sha256 = checkpoint.save_s1_frontier_atomic(
        frontier_path, uninterrupted, support, first_reduction, metadata_one
    )
    resumed = make_paired_bundles(seed=test_seed, panel=panel)
    loaded_metadata, resumed_support, loaded_reduction = checkpoint.load_s1_frontier_cold(
        frontier_path, resumed
    )
    if loaded_metadata != metadata_one or loaded_reduction != first_reduction:
        raise RuntimeError("cold-loaded S1 metadata/reduction differs")
    if resumed_support.sha256() != support.sha256():
        raise RuntimeError("cold-loaded S1 support counters differ")
    second = prepare_training_batch(
        uninterrupted, namespace=namespace, test_seed=test_seed, panel=panel,
        batch_index=1, build_root=build_root,
    )
    uninterrupted_losses = apply_training_batch(
        uninterrupted, support, second, batch_number=2
    )
    resumed_losses = apply_training_batch(
        resumed, resumed_support, second, batch_number=2
    )
    second_reduction = second["reduction_frontier"]
    if not isinstance(second_reduction, ReductionFrontier):
        raise RuntimeError("second reduction frontier is malformed")
    metadata_two = _frontier_metadata(
        test_seed=test_seed,
        test_seed_slot=test_seed_slot,
        panel=panel,
        completed_batch=2,
        counter_frontier=str(second["counter_frontier"]),
        reduction=second_reduction,
        source_sha256=str(identity["source_sha256"]),
        native_artifact_sha256=str(identity["artifact_sha256"]),
    )
    uninterrupted_state = checkpoint.s1_state_sha256(
        uninterrupted, support, second_reduction, metadata_two
    )
    resumed_state = checkpoint.s1_state_sha256(
        resumed, resumed_support, second_reduction, metadata_two
    )
    slot_digests = {
        slot: hashlib.sha256(f"{uninterrupted_state}:{slot}".encode("ascii")).hexdigest()
        for slot in checkpoint.expected_s1_manifest_slots()
    }
    manifest = checkpoint.build_s1_structural_manifest(
        slot_digests, namespace=namespace, request=S1_TEST_REQUEST
    )
    all_six = all_six_arm_semantic_digest(build_root=build_root)
    optimizer_steps = sorted(
        {
            int(state["step"].item())
            for bundle in resumed
            for state in bundle.optimizer.state.values()
            if "step" in state
        }
    )
    return {
        "schema": "UCOPE_R01_R03_S1_SEMANTIC_CORE_COUPON_V1",
        "namespace": S1_TEST_NAMESPACE,
        "request": S1_TEST_REQUEST,
        "question_relevant_output": False,
        "partial_result": False,
        "complete_r03_package": False,
        "registered_seed_used": False,
        "native_identity": identity,
        "first_update_loss_digest": hashlib.sha256(repr(first_losses).encode("ascii")).hexdigest(),
        "next_update_loss_digests_equal": hashlib.sha256(repr(uninterrupted_losses).encode("ascii")).hexdigest()
        == hashlib.sha256(repr(resumed_losses).encode("ascii")).hexdigest(),
        "frontier": {
            "sha256": frontier_sha256,
            "bytes": frontier_path.stat().st_size,
            "atomic_replace": True,
            "flush_fsync": True,
            "completed_batch": 1,
            "next_batch": 2,
        },
        "resume": {
            "uninterrupted_state_sha256": uninterrupted_state,
            "cold_resume_state_sha256": resumed_state,
            "byte_equal": uninterrupted_state == resumed_state,
            "support_sha256_equal": support.sha256() == resumed_support.sha256(),
            "counter_frontier_equal": True,
            "reduction_frontier_equal": True,
            "optimizer_steps": optimizer_steps,
            "committed_step_repeated": optimizer_steps != [2],
        },
        "support": {
            "schema_valid": True,
            "monotone": True,
            "root_total": int(support.root_actions.sum()),
            "tail_total": int(support.tail_actions.sum()),
            "roster_total": int(support.panel_roster_cells.sum()),
            "displayed_count_total": int(support.displayed_counts.sum()),
            "synthetic_gate_conclusion": False,
            "sha256": support.sha256(),
        },
        "reduction": {
            "fixed_fp32_tree": True,
            "frontier_sha256": second_reduction.ordered_values_sha256,
            "numeric_total_exposed": False,
        },
        "manifest": {
            "schema": manifest["schema"],
            "slot_count": manifest["slot_count"],
            "structural_slots_complete": manifest["structural_slots_complete"],
            "complete_r03_package": manifest["complete_r03_package"],
            "sha256": hashlib.sha256(repr(manifest).encode("utf-8")).hexdigest(),
        },
        "all_six_arms": all_six,
        "fp32_hot_path": True,
        "recurrent_state": "NOT_APPLICABLE",
    }
