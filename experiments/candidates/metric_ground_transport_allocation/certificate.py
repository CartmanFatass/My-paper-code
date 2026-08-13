"""Deterministic preactivity answerability and implementation certificate."""

from __future__ import annotations

import numpy as np
import torch

from .actor import HADAMARD, Actor, metric_map
from .config import (
    BINDINGS, EVAL_SIZES, HEADROOM_MARGIN, LOADS, ORDERED_PAIRS, TRAIN_SIZES,
    demand, workload_counts, EXPECTED_COUNTS,
)
from .decoder import decode
from .environment import canonical_roles, coupling_from_actions, feasibility_residuals
from .oracle import canonical_oracle, load_diagnostic_expectation


def panel_tables() -> tuple[dict[str, np.ndarray], dict[tuple[int, int, int, int], int]]:
    rows = []
    oracle_tasks = []
    oracle_idle = []
    oracle_unmet = []
    oracle_reward = []
    load_reward = []
    headroom = []
    lookup: dict[tuple[int, int, int, int], int] = {}
    for n in EVAL_SIZES:
        for pair_index, pair in enumerate(ORDERED_PAIRS):
            for load_index, load in enumerate(LOADS):
                for epoch in (1, 2):
                    d = demand(n, pair, load, epoch)
                    oracle = canonical_oracle(n, d)
                    load_value = load_diagnostic_expectation(n, d)
                    h = (float(oracle["reward"]) - load_value) / n
                    key = len(rows)
                    lookup[(n, pair_index, load_index, epoch)] = key
                    rows.append((n, pair_index, load_index, epoch, *d))
                    oracle_tasks.append(oracle["role_task_counts"])
                    oracle_idle.append(oracle["role_idle_counts"])
                    oracle_unmet.append(oracle["unmet_counts"])
                    oracle_reward.append(oracle["reward"])
                    load_reward.append(load_value)
                    headroom.append(h)
    return {
        "oracle_panel_rows": np.asarray(rows, dtype=np.int16),
        "oracle_role_task_counts": np.asarray(oracle_tasks, dtype=np.int16),
        "oracle_role_idle_counts": np.asarray(oracle_idle, dtype=np.int16),
        "oracle_unmet_counts": np.asarray(oracle_unmet, dtype=np.int16),
        "oracle_reward": np.asarray(oracle_reward, dtype=np.float64),
        "load_diagnostic_expectation": np.asarray(load_reward, dtype=np.float64),
        "headroom": np.asarray(headroom, dtype=np.float64),
    }, lookup


def deterministic_certificate() -> tuple[dict[str, object], dict[str, np.ndarray], dict[tuple[int, int, int, int], int]]:
    tables, lookup = panel_tables()
    maps = [metric_map("INTACT"), metric_map("CUT"), HADAMARD]
    eig_min = [float(np.linalg.eigvalsh(item).min()) for item in maps[:2]]
    orthogonal_error = float(np.max(np.abs(HADAMARD.T @ HADAMARD - np.eye(8))))
    transform_errors = []
    fixture_w = np.arange(48, dtype=np.float64).reshape(8, 6) / 47.0
    features = []
    for n in TRAIN_SIZES:
        for pair in ORDERED_PAIRS:
            for load in LOADS:
                for epoch in (1, 2):
                    d = np.asarray(demand(n, pair, load, epoch), dtype=np.float64)
                    features.append((1.0, *(d / n), epoch - 1.0))
    feature_rank = int(np.linalg.matrix_rank(np.asarray(features)))
    for binding in BINDINGS:
        metric = metric_map(binding)
        free_w = HADAMARD.T @ metric @ fixture_w
        metric_w = np.linalg.solve(metric, HADAMARD @ free_w)
        transform_errors.append(float(np.max(np.abs(metric @ fixture_w - HADAMARD @ free_w))))
        transform_errors.append(float(np.max(np.abs(metric_w - fixture_w))))

    # Hand-written, nonregistered tape: no production seed/address is touched.
    actor = Actor("METRIC", "INTACT")
    with torch.no_grad():
        actor.W.copy_(torch.as_tensor(fixture_w, dtype=torch.float64))
    n = 4
    d = np.asarray([[2, 0, 0, 2]], dtype=np.int64)
    feature = torch.as_tensor([[1.0, 0.5, 0.0, 0.0, 0.5, 0.0]], dtype=torch.float64)
    roles = np.asarray([canonical_roles(n)])
    ranks = np.asarray([[2, 0, 3, 1]], dtype=np.int64)
    uniforms = np.asarray([[0.11, 0.37, 0.71, 0.93]], dtype=np.float64)
    raw, mapped, idle = actor.scores(feature)
    decoded = decode(mapped, idle, torch.as_tensor(roles), torch.as_tensor(d), torch.as_tensor(ranks), torch.as_tensor(uniforms))
    actions = decoded.actions.detach().numpy()
    x, iota, unmet = coupling_from_actions(actions, d)
    residuals = feasibility_residuals(x, iota, unmet, d)
    counts = workload_counts()
    certificate = {
        "revision": "MGTAP-B1-SCIENCE-20260813-04",
        "feature_rank": feature_rank,
        "metric_min_eigenvalues": eig_min,
        "free_orthogonal_error": orthogonal_error,
        "max_transform_error": max(transform_errors),
        "minimum_headroom": float(tables["headroom"].min()),
        "headroom_margin": HEADROOM_MARGIN,
        "fixture_feasible": bool(not np.any(residuals)),
        "fixture_action": actions[0].tolist(),
        "fixture_log_probability_finite": bool(torch.isfinite(decoded.log_probability).all()),
        "fixture_entropy_finite": bool(torch.isfinite(decoded.mean_entropy).all()),
        "workload_counts": counts,
        "workload_counts_exact": counts == EXPECTED_COUNTS,
        "projected_uncompressed_seed_packet_bytes": 110_000_000,
        "projected_all_seed_packets_uncompressed_bytes": 1_760_000_000,
    }
    certificate["passed"] = bool(
        feature_rank == 6 and min(eig_min) >= 0.5 - 1e-12
        and orthogonal_error < 1e-12 and max(transform_errors) < 1e-12
        and certificate["minimum_headroom"] >= HEADROOM_MARGIN - 1e-12
        and certificate["fixture_feasible"] and certificate["fixture_log_probability_finite"]
        and certificate["fixture_entropy_finite"] and certificate["workload_counts_exact"]
    )
    return certificate, tables, lookup
