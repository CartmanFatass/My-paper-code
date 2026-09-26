"""B04 changes only source context pairing, preserving both marginal sets."""

from dataclasses import replace

import numpy as np
import pytest

from experiments.candidates.skill_teammate_drift_learning.joint_response_b03 import study


def test_permutation_preserves_marginals_but_removes_product_constraint():
    product = study.Config()
    permuted = replace(product, source_schedule="permuted")
    a, b = study.context_schedule(product), study.context_schedule(permuted)
    n = product.source_macros
    expected = np.arange(n) * 37 % n
    np.testing.assert_array_equal(b["u"], a["u"])
    np.testing.assert_array_equal(b["v"][:n], a["v"][expected])
    np.testing.assert_array_equal(np.sort(b["v"][:n]), np.sort(a["v"][:n]))
    np.testing.assert_array_equal(np.sort(b["q"][:n]), np.sort(a["q"][:n]))
    for key in a:
        np.testing.assert_array_equal(b[key][n:], a[key][n:])
    assert np.all(np.diff(b["p"]) != 0)
    assert np.all(np.diff(b["q"]) != 0)
    assert np.ptp(b["u"][:n] * b["v"][:n]) > .1
    for schedule, rank in ((a, 3), (b, 4)):
        u, v = schedule["u"][:n], schedule["v"][:n]
        phi = np.column_stack(((1-u)*(1-v), (1-u)*v, u*(1-v), u*v))
        assert np.linalg.matrix_rank(phi) == rank


def test_default_product_schedule_is_exact_original_formula():
    cfg = study.Config()
    schedule = study.context_schedule(cfg)
    source_u = .25 + .55 * (np.arange(2048, dtype=float) + .5) / 2048
    target_u = .82 + .10 * (np.arange(256, dtype=float) + .5) / 256
    target_v = .84 + .10 * (np.arange(256, dtype=float) + .5) / 256
    np.testing.assert_array_equal(schedule["u"], np.concatenate((source_u, target_u)))
    np.testing.assert_array_equal(schedule["v"], np.concatenate((.16/source_u, target_v)))
    np.testing.assert_array_equal(schedule["p"], 1-np.power(1-schedule["u"], 1/3))
    np.testing.assert_array_equal(schedule["q"], 1-np.power(1-schedule["v"], 1/3))


def test_same_slots_across_conditions_and_identical_target_data():
    cfg = study.Config(source_macros=32, target_macros=8)
    results = {}
    for schedule in ("product", "permuted"):
        for arm in ("joint_response", "fingerprint_full"):
            result = study.run_fit(replace(cfg, source_schedule=schedule), arm=arm, seed=14)
            results[(schedule, arm)] = result["transitions"]
        a = results[(schedule,"joint_response")]
        b = results[(schedule,"fingerprint_full")]
        for key in a:
            np.testing.assert_array_equal(a[key], b[key])
    a = results[("product","joint_response")]
    b = results[("permuted","joint_response")]
    for key in ("skill_uniform","primitive_uniform","reward_uniform_slots","collection_skill"):
        np.testing.assert_array_equal(a[key], b[key])
    for key in a:
        np.testing.assert_array_equal(a[key][32:], b[key][32:])
    assert not np.array_equal(a["q"][:32], b["q"][:32])


def test_unknown_or_nonpermuting_schedule_refuses():
    with pytest.raises(ValueError, match="source_schedule"):
        study.context_schedule(study.Config(source_schedule="other"))
    with pytest.raises(ValueError, match="coprime"):
        study.context_schedule(study.Config(source_macros=37, source_schedule="permuted"))
