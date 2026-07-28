"""Focused tests for the D7.S normalizer autopsy
(`scripts/d7s_normalizer_autopsy.py`).

These are calibration of an instrument, not a specification of behavior:
each expected value here is a frozen literal from the task brief (itself
independently reconstructed from the recorded artifact, never re-derived the
way the production code computes it) or a deliberately-constructed fixture
whose "wrong answer" is known by hand-worked construction.

Cost note: two tests below run the REAL registered bootstrap
(`audit.BOOTSTRAP_ITERS=10000`) against the real artifact
(`test_b_stable_interval_lower_edge_matches_recorded_lcb`, ~20-30s) or the
real end-to-end `--quick` path against the real artifact
(`test_quick_refuses_to_emit_evidence_matrix`, well under that). Every other
test uses small synthetic fixtures and stays fast, including the sentinel's
six independently-driven condition tests, which use a SMALL synthetic
8-topology fixture (still 8 topologies, since conditions 3/5 check that
length -- see `_tiny_valid_result`) rather than the real ~630KB artifact.
"""

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]

_AUDIT_SPEC = importlib.util.spec_from_file_location(
    "audit_d7_s_event_aligned", _ROOT / "scripts" / "audit_d7_s_event_aligned.py")
audit = importlib.util.module_from_spec(_AUDIT_SPEC)
sys.modules[_AUDIT_SPEC.name] = audit
_AUDIT_SPEC.loader.exec_module(audit)

_AUTOPSY_SPEC = importlib.util.spec_from_file_location(
    "d7s_normalizer_autopsy", _ROOT / "scripts" / "d7s_normalizer_autopsy.py")
autopsy = importlib.util.module_from_spec(_AUTOPSY_SPEC)
sys.modules[_AUTOPSY_SPEC.name] = autopsy
_AUTOPSY_SPEC.loader.exec_module(autopsy)

REAL_ARTIFACT_PATH = _ROOT / autopsy.ARTIFACT_RELATIVE_PATH

# Frozen reference values from the task brief's own manual reconstruction
# against the recorded artifact -- an independent source of truth, never
# recomputed the way `standalone_distribution`/`hierarchical_bootstrap_*`
# compute them.
FROZEN_T_M_BOUNDS = {
    "b_stable_lcb": -0.077366986884,
    "b_flex_lcb": -8.648833349327,
    "t_stable_ucb": 7.206992755590,
    "t_stable_lcb": -2.189142979011,
    "t_flex_lcb": -14.293053950075,
    "t_flex_ucb": 3.115870660595,
}
FROZEN_POINTS = {
    "b_stable": 0.180139,
    "b_flex": 4.288854,
    "u_star_stable": 1.254074,
    "u_star_flex": -4.122402,
}


# =============================================================================
# Small synthetic fixture for the sentinel's six independently-driven
# conditions. Real 8-seed topology list (conditions 3/5 check that exact
# list/length), tiny 1-event-per-quantity topologies (keeps condition 6's
# real `compute_t_m_bootstrap` call fast at a small `iters`).
# =============================================================================

def _tiny_event(select_val: float, eval_set_val: float, eval_keep_val: float) -> dict:
    return {"candidates": {"z0": {"select": [select_val], "eval_set": [eval_set_val]}},
            "eval_keep": [eval_keep_val]}


def _tiny_topology_unit(seed: int, offset: float) -> dict:
    # `offset` varies the point value per topology so the eight topologies
    # are not all numerically identical (irrelevant to the sentinel itself,
    # but keeps the fixture from being a degenerate all-equal case).
    return {
        "topology_seed": seed,
        "calibration_units_stable": [_tiny_event(0.0, 1.0 + offset, 0.0)],
        "calibration_units_flex": [_tiny_event(0.0, -1.0 + offset, 0.0)],
        "audit_units_stable": [_tiny_event(0.0, 2.0 + offset, 0.0)],
        "audit_units_flex": [_tiny_event(0.0, -2.0 + offset, 0.0)],
    }


def _tiny_valid_result(*, iters: int, seed: int) -> tuple[dict, bytes]:
    """A small, otherwise-valid `result` dict: real 8-seed topology list,
    structurally complete topology_units, and a `t_m_bootstrap` block made
    SELF-CONSISTENT by actually running the real, reused
    `compute_t_m_bootstrap` once over this fixture's own tiny data at the
    given (iters, seed) -- this is establishing a controlled MECHANISM
    fixture (does the sentinel correctly detect a later corruption?), not a
    claim about any registered scientific bound; the scientific claim is
    covered separately by the frozen-literal tests below, which run
    against the real artifact at the real registered BOOTSTRAP_ITERS."""
    topology_seeds = list(audit.TOPOLOGY_SEEDS_INITIAL)
    topology_units = [_tiny_topology_unit(s, float(i)) for i, s in enumerate(topology_seeds)]
    recomputed = audit.compute_t_m_bootstrap(
        b_stable_topology_units=[u["calibration_units_stable"] for u in topology_units],
        b_flex_topology_units=[u["calibration_units_flex"] for u in topology_units],
        u_star_stable_topology_units=[u["audit_units_stable"] for u in topology_units],
        u_star_flex_topology_units=[u["audit_units_flex"] for u in topology_units],
        n_topo=len(topology_units), iters=iters, seed=seed)
    result = {
        "contract_id": audit.CONTRACT_ID,
        "procedure_version": audit.TOPOLOGY_PROCEDURE_VERSION,
        "topology_seeds": topology_seeds,
        "smoke": False,
        "topology_units": topology_units,
        "t_m_bootstrap": {k: recomputed[k] for k in (
            "b_stable_lcb", "b_flex_lcb", "t_stable_ucb", "t_stable_lcb",
            "t_flex_lcb", "t_flex_ucb")},
    }
    raw_bytes = json.dumps(result, default=audit._json_default).encode("utf-8")
    # Round-trip through JSON so `raw_bytes`'s hash is the hash of exactly
    # what a real `result` load would see (matching how `run_autopsy` reads
    # `raw_bytes` and `json.loads`s it separately).
    result = json.loads(raw_bytes)
    return result, raw_bytes


_TINY_ITERS = 300
_TINY_SEED = 1234567


@pytest.fixture(scope="module")
def tiny_fixture():
    return _tiny_valid_result(iters=_TINY_ITERS, seed=_TINY_SEED)


def _tiny_hash(raw_bytes: bytes) -> str:
    import hashlib
    return hashlib.sha256(raw_bytes).hexdigest()


def test_tiny_fixture_passes_sentinel_when_uncorrupted(tiny_fixture):
    """Control case: proves the fixture itself is a legitimate "everything
    passes" baseline before any single-condition test corrupts exactly one
    field."""
    result, raw_bytes = tiny_fixture
    out = autopsy.run_sentinel(
        result, raw_bytes, iters=_TINY_ITERS, seed=_TINY_SEED,
        expected_hash=_tiny_hash(raw_bytes))
    assert all(c["ok"] is not False for c in out["checks"].values())


# =============================================================================
# Required test 1: the sentinel fails closed on EACH of its six conditions,
# driven separately -- one corruption per test, control passes on the rest.
# =============================================================================

def test_sentinel_condition_1_artifact_hash(tiny_fixture):
    result, raw_bytes = tiny_fixture
    with pytest.raises(autopsy.SentinelFailure) as exc_info:
        autopsy.run_sentinel(
            result, raw_bytes, iters=_TINY_ITERS, seed=_TINY_SEED,
            expected_hash="0" * 64)  # deliberately wrong reference hash
    assert exc_info.value.failed == ["artifact_hash"]


def test_sentinel_condition_2_contract_and_procedure(tiny_fixture):
    result, raw_bytes = tiny_fixture
    corrupted = dict(result)
    corrupted["contract_id"] = "SOME_OTHER_CONTRACT"
    raw2 = json.dumps(corrupted, default=audit._json_default).encode("utf-8")
    corrupted = json.loads(raw2)
    with pytest.raises(autopsy.SentinelFailure) as exc_info:
        autopsy.run_sentinel(
            corrupted, raw2, iters=_TINY_ITERS, seed=_TINY_SEED,
            expected_hash=_tiny_hash(raw2))
    assert exc_info.value.failed == ["contract_and_procedure"]


def test_sentinel_condition_3_topology_seeds(tiny_fixture):
    result, _raw = tiny_fixture
    corrupted = dict(result)
    corrupted["topology_seeds"] = list(audit.TOPOLOGY_SEEDS_INITIAL[:-1])  # drop one
    raw2 = json.dumps(corrupted, default=audit._json_default).encode("utf-8")
    corrupted = json.loads(raw2)
    with pytest.raises(autopsy.SentinelFailure) as exc_info:
        autopsy.run_sentinel(
            corrupted, raw2, iters=_TINY_ITERS, seed=_TINY_SEED,
            expected_hash=_tiny_hash(raw2))
    assert exc_info.value.failed == ["topology_seeds"]


def test_sentinel_condition_4_smoke_false(tiny_fixture):
    result, _raw = tiny_fixture
    corrupted = dict(result)
    corrupted["smoke"] = True
    raw2 = json.dumps(corrupted, default=audit._json_default).encode("utf-8")
    corrupted = json.loads(raw2)
    with pytest.raises(autopsy.SentinelFailure) as exc_info:
        autopsy.run_sentinel(
            corrupted, raw2, iters=_TINY_ITERS, seed=_TINY_SEED,
            expected_hash=_tiny_hash(raw2))
    assert exc_info.value.failed == ["smoke_false"]


def test_sentinel_condition_5_topology_units_shape(tiny_fixture):
    """Unlike conditions 1-4 (hash/contract/procedure/seeds/smoke, each
    orthogonal to topology_units content), a missing required collection
    necessarily ALSO breaks condition 6 -- bound reproduction cannot
    succeed over data that condition 5 itself finds malformed, so that
    coupling is real, not a test artifact. What this isolates: (a) the
    `check_topology_units_shape` function itself, called directly, detects
    exactly this corruption and nothing else; (b) through the full
    `run_sentinel` path, the four conditions that do NOT depend on
    topology_units content stay independently true."""
    result, raw_bytes = tiny_fixture
    ok5, _detail5 = autopsy.check_topology_units_shape(result)
    assert ok5 is True  # control: uncorrupted fixture passes this check alone

    corrupted = dict(result)
    broken_units = [dict(u) for u in corrupted["topology_units"]]
    del broken_units[3]["audit_units_flex"]  # drop one of the four required collections
    corrupted["topology_units"] = broken_units
    raw2 = json.dumps(corrupted, default=audit._json_default).encode("utf-8")
    corrupted = json.loads(raw2)

    ok5c, detail5c = autopsy.check_topology_units_shape(corrupted)
    assert ok5c is False
    assert "topology_units[3].audit_units_flex" in detail5c

    with pytest.raises(autopsy.SentinelFailure) as exc_info:
        autopsy.run_sentinel(
            corrupted, raw2, iters=_TINY_ITERS, seed=_TINY_SEED,
            expected_hash=_tiny_hash(raw2))
    assert "topology_units_shape" in exc_info.value.failed
    for name in ("artifact_hash", "contract_and_procedure", "topology_seeds", "smoke_false"):
        assert exc_info.value.checks[name]["ok"] is True


def test_sentinel_condition_6_bounds_reproduction(tiny_fixture):
    result, _raw = tiny_fixture
    corrupted = dict(result)
    corrupted["t_m_bootstrap"] = dict(corrupted["t_m_bootstrap"])
    corrupted["t_m_bootstrap"]["b_stable_lcb"] += 5.0  # far outside BOUND_TOLERANCE
    raw2 = json.dumps(corrupted, default=audit._json_default).encode("utf-8")
    corrupted = json.loads(raw2)
    with pytest.raises(autopsy.SentinelFailure) as exc_info:
        autopsy.run_sentinel(
            corrupted, raw2, iters=_TINY_ITERS, seed=_TINY_SEED,
            expected_hash=_tiny_hash(raw2))
    assert exc_info.value.failed == ["bounds_reproduction"]


def test_sentinel_quick_mode_skips_bounds_check_without_failing(tiny_fixture):
    """`enforce_bounds=False` (--quick's effect) must not silently mark
    condition 6 as passing -- it is reported as skipped, and the OTHER five
    conditions still gate normally."""
    result, raw_bytes = tiny_fixture
    out = autopsy.run_sentinel(
        result, raw_bytes, iters=10, seed=_TINY_SEED,
        expected_hash=_tiny_hash(raw_bytes), enforce_bounds=False)
    assert out["checks"]["bounds_reproduction"]["ok"] is None
    assert "SKIPPED_QUICK_MODE" in out["checks"]["bounds_reproduction"]["detail"]


# =============================================================================
# Required test 2: the four artifact-derived points match the frozen
# literals (RNG-free true-argmax path -- fast even against the real artifact).
# =============================================================================

def _load_real_result() -> dict:
    return json.loads(REAL_ARTIFACT_PATH.read_bytes())


def test_four_artifact_derived_points_match_frozen_literals():
    result = _load_real_result()
    for quantity, expected in FROZEN_POINTS.items():
        units = autopsy.extract_quantity_units(result, quantity)
        points = autopsy.per_topology_points(units)
        finite = [p for p in points if p is not None]
        point = float(np.mean(finite))
        assert point == pytest.approx(expected, abs=1e-6), quantity


# =============================================================================
# Required test 3: the two-sided interval is the 5th-95th percentile of the
# SAME bootstrap distribution R3 took its one-sided 95% bound from -- assert
# the lower edge against both the frozen literal and the artifact's own
# recorded b_stable_lcb. Runs the REAL registered bootstrap (~20-30s).
# =============================================================================

def test_b_stable_interval_lower_edge_matches_recorded_lcb():
    result = _load_real_result()
    units = autopsy.extract_quantity_units(result, "b_stable")
    shared = audit.draw_shared_topology_indices(
        n_topo=len(units), iters=audit.BOOTSTRAP_ITERS, seed=audit.BOOTSTRAP_SEED)
    dist = autopsy.standalone_distribution(
        units, shared_topology_indices=shared, seed=audit.BOOTSTRAP_SEED)
    lower_edge = dist["interval_5_95"][0]
    assert lower_edge == pytest.approx(FROZEN_T_M_BOUNDS["b_stable_lcb"], abs=1e-9)
    assert lower_edge == pytest.approx(result["t_m_bootstrap"]["b_stable_lcb"], abs=1e-9)


# =============================================================================
# Required test 4: the inner calibration/audit blocks really are resampled
# independently (Modification 3). Fixture: several IDENTICAL topologies,
# each with a 1-value calibration event per index k with value k, and a
# 1-value audit event per index k with value (3-k) -- an exact affine
# relationship KEYED BY INDEX, replicated across topology slots so a single
# bootstrap iteration has multiple (B, U) pairs to correlate (correlation
# over a single pair is degenerate). Forcing the SAME within-topology draw
# for both blocks makes calibration+audit sum to exactly 3 on every
# resampled slot (r == -1.0 exactly across slots, since there is no other
# source of variance in this fixture). Independent resampling decouples the
# two draws per slot, so the true association is not -1.
# =============================================================================

def _forced_shared_association(b_units, u_units, *, shared_topology_indices, seed):
    """Deliberately WRONG variant (test-only): reuses the SAME within-
    topology event-index draw AND the same inner replicate seed for both
    the calibration and audit blocks -- exactly the Modification-3 defect
    the production `bootstrap_association` must NOT exhibit."""
    iters, n_topo = shared_topology_indices.shape
    pearsons = []
    for i in range(iters):
        topo_idx = shared_topology_indices[i]
        b_vals, u_vals = [], []
        for slot, ti in enumerate(topo_idx):
            ti = int(ti)
            events_b, events_u = b_units[ti], u_units[ti]
            ev_rng = np.random.default_rng((int(seed), int(i), int(slot)))
            idx = ev_rng.integers(0, len(events_b), size=len(events_b))
            resampled_b = [events_b[j] for j in idx]
            resampled_u = [events_u[j] for j in idx]  # BUG: reuses the SAME idx
            inner_seed = int(ev_rng.integers(0, 2 ** 63 - 1))
            bm = audit.hierarchical_bootstrap_events(
                resampled_b, iters=1, seed=inner_seed, compute_point=False)["u_star_iters"][0]
            um = audit.hierarchical_bootstrap_events(
                resampled_u, iters=1, seed=inner_seed, compute_point=False)["u_star_iters"][0]
            b_vals.append(bm)
            u_vals.append(um)
        if np.std(b_vals) > 0:
            pearsons.append(autopsy.pearson_r(b_vals, u_vals))
    finite = [p for p in pearsons if np.isfinite(p)]
    return float(np.mean(finite))


def test_independent_resampling_diverges_from_forced_shared_resampling():
    n_topo = 4
    single_b = [_tiny_event(0.0, float(k), 0.0) for k in range(4)]       # values 0,1,2,3
    single_u = [_tiny_event(0.0, float(3 - k), 0.0) for k in range(4)]   # values 3,2,1,0
    b_units = [single_b for _ in range(n_topo)]  # identical content in every topology slot
    u_units = [single_u for _ in range(n_topo)]

    iters = 800
    seed = 999
    # Every iteration visits all n_topo slots once each -- `slot` (not the
    # topology index, which is identical content everywhere here) is what
    # drives each slot's independent draw via `(seed, i, slot, tag)`.
    shared = np.tile(np.arange(n_topo), (iters, 1))

    forced_r = _forced_shared_association(
        b_units, u_units, shared_topology_indices=shared, seed=seed)
    assert forced_r == pytest.approx(-1.0, abs=1e-9), (
        "control: forced-shared resampling on this affine fixture must give r == -1.0 exactly")

    real = autopsy.bootstrap_association(
        b_units, u_units, shared_topology_indices=shared, seed=seed)
    real_lo, real_hi = real["pearson_interval_5_95"]
    assert real_lo is not None and real_hi is not None
    # Independent resampling must clearly diverge from the forced-shared
    # answer -- the interval must not even contain -1 to a nontrivial margin.
    assert real_lo > -0.9, (
        f"independent-resampling interval [{real_lo}, {real_hi}] is indistinguishable from "
        f"the forced-shared answer (r=-1.0); calibration/audit blocks may be sharing draws")


# =============================================================================
# Required test 5: --quick refuses to emit the evidence matrix.
# =============================================================================

def test_quick_refuses_to_emit_evidence_matrix():
    out = autopsy.run_autopsy(
        artifact_path=REAL_ARTIFACT_PATH, iters=autopsy.QUICK_ITERS,
        seed=audit.BOOTSTRAP_SEED, quick=True)
    assert out["quick_dev_run"] is True
    assert "evidence_matrix" not in out
    assert "r4_recommendations_non_binding" not in out
