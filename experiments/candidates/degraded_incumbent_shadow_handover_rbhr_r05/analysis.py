"""TEST-only Gate-B analyzer seams for the frozen r05 first-match law."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

import numpy as np

from .contracts import TEST_NAMESPACE


BRANCH_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "tests" / "fixtures" / "dish_rbhr_r05" / "TEST_SYNTHETIC_BRANCH_VECTORS_V1.json"
)


def classify_atomic(vector: Mapping[str, object]) -> tuple[int, str]:
    get = lambda name, default=False: bool(vector.get(name, default))
    if not get("protocol_ok"):
        return 1, "INVALID_PROTOCOL_OR_MEASUREMENT"
    if not get("comp"):
        return 2, "LEARNED_ARM_COMPETENCE_NOT_ESTABLISHED"
    if not get("witness"):
        return 3, "NO_REGISTERED_RECOVERY_WITNESS"
    if not get("headroom", True) or not get("precision", True):
        return 4, "NONANSWERABLE_OR_NO_HEADROOM"
    if not get("support"):
        if get("rule_fallback_i"):
            return 5, "SIMPLE_RULE_SUFFICIENT[IMMEDIATE]"
        if get("rule_fallback_h"):
            return 5, "SIMPLE_RULE_SUFFICIENT[HYSTERESIS]"
        return 5, "EFFECTIVE_HANDOVER_SUPPORT_NOT_ESTABLISHED"
    if get("harm"):
        return 6, "TARGET_SPECIFIC_HARM"
    if get("package_effect"):
        return 7, "NONACTUATION_PACKAGE_EFFECT"
    if get("fork_excluded") and not get("nm_all"):
        return 8, "SHADOW_ACTUATION_NONPASS"
    if get("rulequal_i"):
        return 9, "SIMPLE_RULE_SUFFICIENT[IMMEDIATE]"
    if get("rulequal_h"):
        return 10, "SIMPLE_RULE_SUFFICIENT[HYSTERESIS]"
    if get("flexqual"):
        return 11, "FLEXIBLE_CONTAINER_SUPERIOR"
    if get("flex_rel"):
        return 12, "FLEX_RELATIVE_NONRETENTION"
    if get("core") and not get("flex_rel"):
        return 13, "STRUCTURED_ATOMIC_VALUE"
    if get("nm_all"):
        return 14, "TARGET_SPECIFIC_NO_MATERIAL"
    return 15, "UNRESOLVED"


def load_and_validate_branch_fixture(path: Path = BRANCH_FIXTURE) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "DISH_RBHR_R05_TEST_SYNTHETIC_BRANCH_VECTORS_V1":
        raise ValueError("branch fixture schema mismatch")
    if payload.get("namespace") != TEST_NAMESPACE or payload.get("synthetic_only") is not True:
        raise ValueError("branch fixture is not in the exact TEST-only namespace")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) != 15:
        raise ValueError("branch fixture must contain exactly fifteen first-match cases")
    seen: set[int] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("branch fixture case is not an object")
        branch, label = classify_atomic(case)
        if branch != case.get("expected_branch") or label != case.get("expected_label"):
            raise ValueError(f"branch fixture mismatch for {case.get('id')}")
        seen.add(branch)
    if seen != set(range(1, 16)):
        raise ValueError("branch fixture does not cover all first-match branches")
    return payload


def _test_block_indices(key: bytes, start: int, count: int) -> np.ndarray:
    values = np.empty((count, 24), dtype=np.int16)
    for local in range(count):
        g = start + local + 1
        for q in range(24):
            address = f"TEST/DISH/RBHR/R05/INFERENCE/{g}/{q}".encode("ascii")
            word = int.from_bytes(hashlib.sha256(key + b"\x00" + address).digest()[:8], "big")
            values[local, q] = int(24 * (((word >> 11) + 0.5) / float(1 << 53)))
    return values


def joint_max_t(
    block_values: np.ndarray,
    *,
    resamples: int = 99_999,
    chunk_size: int = 512,
    test_key: bytes = b"DISH-RBHR-R05-GATE-B-TEST-INFERENCE-V1",
) -> dict[str, object]:
    values = np.asarray(block_values, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != 24 or values.shape[1] == 0:
        raise ValueError("block_values must have shape [24,H] with H>0")
    if not np.isfinite(values).all():
        raise ValueError("block_values contain a nonfinite value")
    if resamples <= 0 or chunk_size <= 0:
        raise ValueError("resamples and chunk_size must be positive")
    theta = values.mean(axis=0)
    se = values.std(axis=0, ddof=1) / np.sqrt(24.0)
    identical = np.all(values == values[:1, :], axis=0)
    if np.any((se == 0.0) & ~identical):
        raise ValueError("nonidentical estimand has zero observed standard error")
    maxima = np.empty(resamples, dtype=np.float64)
    cursor = 0
    while cursor < resamples:
        count = min(chunk_size, resamples - cursor)
        indices = _test_block_indices(test_key, cursor, count)
        sampled = values[indices]
        theta_star = sampled.mean(axis=1)
        se_star = sampled.std(axis=1, ddof=1) / np.sqrt(24.0)
        numerator = np.abs(theta_star - theta)
        statistic = np.zeros_like(numerator)
        active = ~identical
        finite = active & (se_star > 0.0)
        statistic[finite] = numerator[finite] / se_star[finite]
        zero_se = active & (se_star == 0.0)
        statistic[zero_se & (numerator > 0.0)] = np.inf
        maxima[cursor:cursor+count] = np.max(statistic, axis=1)
        cursor += count
    critical = float(np.partition(maxima, 94_999)[94_999]) if resamples >= 95_000 else float(np.max(maxima))
    lower = theta - critical * se
    upper = theta + critical * se
    lower[identical] = theta[identical]
    upper[identical] = theta[identical]
    return {
        "resamples": resamples,
        "critical": critical,
        "estimands": values.shape[1],
        "theta": theta.tolist(),
        "se": se.tolist(),
        "lower": lower.tolist(),
        "upper": upper.tolist(),
        "all_finite": bool(np.isfinite(lower).all() and np.isfinite(upper).all()),
        "test_only": True,
    }
