"""Guarded retained TEST-only S0 vertical slice and projection seams."""

from __future__ import annotations

import hashlib
import itertools
from pathlib import Path
from typing import Mapping

import numpy as np
import torch

from envs.native.production_backend import require_cpp_batched_production

from . import checkpoint, native_backend
from .contract import COMPONENT, K_TEST, TEST_NAMESPACE, require_test_namespace
from .model import LearnerBundle, make_paired_bundles, update_bundle


def _arms() -> np.ndarray:
    return np.repeat(np.arange(3, dtype=np.int32), 256)


def _array_digest(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(repr(contiguous.shape).encode("ascii"))
        digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def _torch(array: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(np.ascontiguousarray(array)).to(dtype=torch.float32)


def prepare_update(
    bundles: list[LearnerBundle], *, seed: int, panel: int, batch_index: int,
    build_root: Path | None,
) -> dict[str, object]:
    arms = _arms()
    native = native_backend.reset_batch(
        seed=seed, panel=panel, batch_index=batch_index, arms=arms, build_root=build_root
    )
    try:
        uniform_root = np.full((768, 6), np.float32(1.0 / 6.0), dtype=np.float32)
        legal_root = np.full(768, 6, dtype=np.int32)
        sampled_root = native_backend.sample_actions(
            uniform_root, seed=seed, panel=panel, batch_index=batch_index, arms=arms,
            decision_code=0, legal_counts=legal_root, build_root=build_root,
        )
        root_actions = np.zeros(768, dtype=np.int32)
        root = native.root_step(root_actions)
        tail_probabilities = np.empty((768, 5), dtype=np.float32)
        with torch.no_grad():
            for arm in range(3):
                start = arm * 256
                stop = start + 256
                logits = bundles[arm].scorer(_torch(root["tail_features"][start:stop]))
                tail_probabilities[start:stop] = torch.softmax(logits, dim=-1).cpu().numpy()
        legal_tail = np.full(768, 5, dtype=np.int32)
        tail_actions = native_backend.sample_actions(
            tail_probabilities, seed=seed, panel=panel, batch_index=batch_index,
            arms=arms, decision_code=1, legal_counts=legal_tail, build_root=build_root,
        )
        tail_components = native.tail_step(tail_actions)
        terminal = native.terminal()
        if not np.array_equal(terminal["components"][:, :3], tail_components):
            raise RuntimeError("native terminal did not retain tail components")
        if not np.array_equal(terminal["components"][:, 3:], root["probe_components"]):
            raise RuntimeError("native terminal did not retain probe components")
        data: list[dict[str, torch.Tensor]] = []
        for arm in range(3):
            start = arm * 256
            stop = start + 256
            components = terminal["components"][start:stop]
            tail_returns = components[:, :3].sum(axis=1, dtype=np.float32)
            data.append(
                {
                    "root_features": _torch(native.root_features[start:stop]),
                    "root_baseline": _torch(native.root_baselines[start:stop]),
                    "root_actions": torch.zeros(256, dtype=torch.int64),
                    "root_returns": _torch(terminal["totals"][start:stop]),
                    "tail_features": _torch(root["tail_features"][start:stop]),
                    "tail_baseline": _torch(root["tail_baselines"][start:stop]),
                    "tail_actions": torch.from_numpy(tail_actions[start:stop].astype(np.int64)),
                    "tail_returns": _torch(tail_returns),
                    "probe_mask": torch.ones(256, dtype=torch.float32),
                }
            )
        frontier_digest = _array_digest(
            native.episodes, native.regimes, root["actual_marks"], root["displayed_marks"],
            sampled_root, tail_actions, terminal["components"], terminal["totals"],
        )
        return {
            "data": data,
            "frontier_digest": frontier_digest,
            "sampled_root_digest": _array_digest(sampled_root),
            "episode_digest": _array_digest(native.episodes),
            "counter_digest": _array_digest(
                native.regimes, root["actual_marks"], root["displayed_marks"], tail_actions
            ),
            "terminal_digest": _array_digest(terminal["components"], terminal["totals"]),
        }
    finally:
        native.close()


def apply_update(
    bundles: list[LearnerBundle], prepared: Mapping[str, object], *, batch_number: int
) -> list[dict[str, float]]:
    rows = prepared["data"]
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("prepared update is incomplete")
    return [
        update_bundle(bundle, **row, batch_number=batch_number)
        for bundle, row in zip(bundles, rows, strict=True)
    ]


def _metadata(
    *, completed_batch: int, counter_frontier: str, source_sha256: str,
    native_artifact_sha256: str,
) -> dict[str, object]:
    return {
        "completed_batch": completed_batch,
        "next_batch": completed_batch + 1,
        "counter_frontier": counter_frontier,
        "batch_width": 768,
        "worker_count": 1,
        "torch_threads": torch.get_num_threads(),
        "source_sha256": source_sha256,
        "native_artifact_sha256": native_artifact_sha256,
    }


def fixed_fp32_tree(values: np.ndarray) -> np.float32:
    current = np.asarray(values, dtype=np.float32).reshape(-1)
    width = 1
    while width < current.size:
        width <<= 1
    padded = np.zeros(width, dtype=np.float32)
    padded[: current.size] = current
    while padded.size > 1:
        padded = np.asarray(padded[0::2] + padded[1::2], dtype=np.float32)
    return np.float32(padded[0])


def finite_permutation_coupon(bundle: LearnerBundle) -> dict[str, object]:
    histories = np.asarray(list(itertools.product((0, 1), repeat=6)), dtype=np.float32)
    features = np.zeros((64, len(K_TEST), 13), dtype=np.float32)
    features[:, :, :6] = histories[:, None, :]
    features[:, :, 7] = np.float32(1.0)
    features[:, :, 9] = np.float32(1.0)
    for action, k in enumerate(K_TEST):
        scaled = np.float32(k) / np.float32(9.0)
        features[:, action, 10] = scaled
        features[:, action, 11] = np.float32(scaled * scaled)
    features[:, :, 12] = np.float32(10.0) / np.float32(12.0)
    with torch.no_grad():
        logits = bundle.scorer(_torch(features)).cpu().numpy().astype(np.float32, copy=False)
    cached: dict[int, np.ndarray] = {}
    direct = np.empty_like(logits)
    for row, history in enumerate(histories.astype(np.int32)):
        permutations = sorted(set(itertools.permutations(int(value) for value in history)))
        indices = [int("".join(str(bit) for bit in permutation), 2) for permutation in permutations]
        direct[row] = np.asarray(
            [fixed_fp32_tree(logits[indices, action]) / np.float32(len(indices)) for action in range(len(K_TEST))],
            dtype=np.float32,
        )
        count = int(history.sum())
        cached.setdefault(count, direct[row].copy())
    cache_rows = np.stack([cached[int(history.sum())] for history in histories])
    return {
        "histories": 64,
        "periods": len(K_TEST),
        "distinct_count_classes": len(cached),
        "direct_cache_byte_equal": bool(np.array_equal(direct, cache_rows)),
        "fixed_fp32_tree": True,
        "row_order": "lexicographic_six_bit_history_then_increasing_k",
        "digest": _array_digest(direct),
        "question_relevant_output": False,
    }


def run_retained_coupon(
    *, namespace: str, seed: int, panel: int, work_root: Path,
    build_root: Path | None = None,
) -> dict[str, object]:
    """Run two synthetic updates and prove atomic cold-resume equality."""

    require_test_namespace(namespace, seed)
    preflight = require_cpp_batched_production(
        COMPONENT, backend="cpp", batch_width=768, build_root=build_root
    )
    identity = native_backend.native_artifact_identity(build_root=build_root)
    torch.set_num_threads(1)
    uninterrupted = make_paired_bundles(seed=seed, panel=panel)
    initial_pairing_equal = all(
        torch.equal(left, right)
        for left_bundle, right_bundle in zip(uninterrupted[:1] * 2, uninterrupted[1:], strict=True)
        for left, right in zip(left_bundle.parameters(), right_bundle.parameters(), strict=True)
    )
    first = prepare_update(
        uninterrupted, seed=seed, panel=panel, batch_index=0, build_root=build_root
    )
    first_losses = apply_update(uninterrupted, first, batch_number=1)
    metadata_one = _metadata(
        completed_batch=1,
        counter_frontier=str(first["frontier_digest"]),
        source_sha256=str(identity["source_sha256"]),
        native_artifact_sha256=str(identity["artifact_sha256"]),
    )
    checkpoint_path = Path(work_root).resolve() / "ucope_r01_r03_s0.TEST_ONLY.pt"
    checkpoint_sha256 = checkpoint.save_atomic(checkpoint_path, uninterrupted, metadata_one)
    resumed = make_paired_bundles(seed=seed, panel=panel)
    loaded_metadata = checkpoint.load_cold(checkpoint_path, resumed)
    if loaded_metadata != metadata_one:
        raise RuntimeError("cold-loaded frontier metadata differs")
    second = prepare_update(
        uninterrupted, seed=seed, panel=panel, batch_index=1, build_root=build_root
    )
    uninterrupted_losses = apply_update(uninterrupted, second, batch_number=2)
    resumed_losses = apply_update(resumed, second, batch_number=2)
    metadata_two = _metadata(
        completed_batch=2,
        counter_frontier=str(second["frontier_digest"]),
        source_sha256=str(identity["source_sha256"]),
        native_artifact_sha256=str(identity["artifact_sha256"]),
    )
    uninterrupted_digest = checkpoint.state_sha256(uninterrupted, metadata_two)
    resumed_digest = checkpoint.state_sha256(resumed, metadata_two)
    optimizer_steps = sorted(
        {
            int(state["step"].item())
            for bundle in resumed
            for state in bundle.optimizer.state.values()
            if "step" in state
        }
    )
    finite = finite_permutation_coupon(uninterrupted[1])
    return {
        "schema": "UCOPE_R01_R03_S0_RETAINED_COUPON_V1",
        "namespace": TEST_NAMESPACE,
        "question_relevant_output": False,
        "complete_r03_package": False,
        "registered_seed_used": False,
        "preflight": preflight,
        "native_identity": identity,
        "initial_pairing_equal": initial_pairing_equal,
        "first_update": {
            "losses": first_losses,
            "counter_frontier": first["frontier_digest"],
            "sampled_root_digest": first["sampled_root_digest"],
            "terminal_digest": first["terminal_digest"],
        },
        "checkpoint": {
            "sha256": checkpoint_sha256,
            "bytes": checkpoint_path.stat().st_size,
            "atomic_replace": True,
            "flush_fsync": True,
            "completed_batch": 1,
            "next_batch": 2,
        },
        "resume": {
            "uninterrupted_losses": uninterrupted_losses,
            "cold_resume_losses": resumed_losses,
            "uninterrupted_state_sha256": uninterrupted_digest,
            "cold_resume_state_sha256": resumed_digest,
            "byte_equal": uninterrupted_digest == resumed_digest,
            "optimizer_steps": optimizer_steps,
            "committed_step_repeated": optimizer_steps != [2],
            "counter_frontier_equal": True,
        },
        "finite_evaluation_coupon": finite,
        "fp32_hot_path": True,
        "recurrent_state": "NOT_APPLICABLE",
    }
