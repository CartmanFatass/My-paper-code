"""Focused tests for the D7.S part B shard pooler.

The pooling contract: shards whose seeds tile one contiguous block are exactly
the episode set of one monolithic run, so the pooled JSON must equal what
`--episodes N` at `seed_0` would have written — same arithmetic, same bootstrap
functions, same `ci_seed = seed_0 + 7717`. Anything whose identity cannot be
proven is refused, not warned about: an unprovable shard is the topology
defect (4a) coming back through the side door.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, _ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


audit = _load("audit_d7_s_persistence_margin")
pooling = _load("pool_d7_s_persistence_shards")

ARMS = pooling.ARMS
SEED0 = 3229000


def _per_episode(rng, n, *, b_h_scale=10.0, stable_norm=-0.2, flex_norm=0.2):
    """Synthetic per-episode returns whose expected margins are known."""
    base = 100.0 + rng.normal(0.0, 1.0, size=n)
    return {
        "constructive": list(base),
        "null": list(base - b_h_scale + rng.normal(0.0, 0.5, size=n)),
        "keep_stable": list(base - 1.0 + rng.normal(0.0, 0.2, size=n)),
        "set_stable": list(base - 1.0 + stable_norm * b_h_scale
                           + rng.normal(0.0, 0.2, size=n)),
        "keep_flex": list(base - 2.0 + rng.normal(0.0, 0.2, size=n)),
        "set_flex": list(base - 2.0 + flex_norm * b_h_scale
                         + rng.normal(0.0, 0.2, size=n)),
    }


def _shard(per_ep, *, seed, episodes, **overrides):
    s = {
        "branch": "SOURCE_NECESSITY_UNRESOLVED",
        "reason": "shard-level branch is not read",
        "horizon": 1500,
        "energy_stage": "S3",
        "check_every": 10,
        "episodes": episodes,
        "seed": seed,
        "episode_seed_base": seed + 100000,
        "topology_seed": 20260725,
        "initial_energies": [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90],
        "n_relay": 2,
        "n_service": 6,
        "n_uavs": 8,
        "n_users": 40,
        "focal_stable_uav": 0,
        "focal_flex_uav": 2,
        "external_return": "unclipped mean rate / qos_target",
        "probe_qos_saturation_fraction": 0.8,
        "arms_all_equal": False,
        "driven_via": "env.step",
        "arm_means": {a: float(np.mean(per_ep[a])) for a in ARMS},
        "per_episode": {a: list(per_ep[a]) for a in ARMS},
        "thresholds": {"stable_ceiling": -0.10, "flex_floor": 0.10},
        "contract": "docs/research/designs/D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md",
    }
    s.update(overrides)
    return s


def _split(per_ep, sizes, seed0=SEED0):
    """Cut one monolithic per-episode set into seed-contiguous shards."""
    shards, at, seed = [], 0, seed0
    for n in sizes:
        cut = {a: per_ep[a][at:at + n] for a in ARMS}
        shards.append(_shard(cut, seed=seed, episodes=n))
        at += n
        seed += n
    return shards


def test_pooling_matches_the_monolithic_arithmetic_field_for_field():
    per_ep = _per_episode(np.random.default_rng(0), 4)
    out = pooling.pool(_split(per_ep, [2, 2]))

    arr = {a: np.asarray(per_ep[a], dtype=float) for a in ARMS}
    mean = {a: float(np.mean(v)) for a, v in arr.items()}
    b_h_ep = arr["constructive"] - arr["null"]
    b_h = mean["constructive"] - mean["null"]

    assert out["per_episode"] == {a: [float(x) for x in per_ep[a]] for a in ARMS}
    assert out["arm_means"] == mean
    assert out["b_h"] == pytest.approx(b_h)
    assert out["episodes"] == 4
    assert out["seed"] == SEED0

    # The interval a monolithic run at SEED0 would write: same function, same
    # ci_seed = seed + 7717.
    expect = audit.bootstrap_mean_ci(b_h_ep, seed=SEED0 + 7717)
    assert out["intervals"]["b_h"] == expect
    expect_ratio = audit.bootstrap_ratio_ci(
        arr["set_stable"] - arr["keep_stable"], b_h_ep, seed=SEED0 + 7717 + 3)
    assert out["intervals"]["normalized_stable"] == expect_ratio


def test_branch_fires_only_when_both_margins_clear():
    rng = np.random.default_rng(1)
    both = pooling.pool(_split(_per_episode(rng, 6), [3, 3]))
    assert both["branch"] == "PERSISTENCE_NECESSARY_SOURCE"

    rng = np.random.default_rng(2)
    stable_fails = _per_episode(rng, 6, stable_norm=0.2)   # wrong sign
    one = pooling.pool(_split(stable_fails, [3, 3]))
    assert one["branch"] == "SOURCE_NECESSITY_UNRESOLVED"


def test_shards_are_sorted_by_seed_before_pooling():
    per_ep = _per_episode(np.random.default_rng(3), 4)
    a = pooling.pool(_split(per_ep, [2, 2]))
    b = pooling.pool(list(reversed(_split(per_ep, [2, 2]))))
    assert a["per_episode"] == b["per_episode"]
    assert a["intervals"] == b["intervals"]


def test_identity_mismatch_is_refused():
    s1, s2 = _split(_per_episode(np.random.default_rng(4), 4), [2, 2])
    s2["horizon"] = 450
    with pytest.raises(SystemExit, match="horizon"):
        pooling.pool([s1, s2])


def test_topology_seed_mismatch_is_refused():
    s1, s2 = _split(_per_episode(np.random.default_rng(5), 4), [2, 2])
    s2["topology_seed"] = 20260726
    with pytest.raises(SystemExit, match="topology_seed"):
        pooling.pool([s1, s2])


def test_missing_provenance_is_refused():
    s1, s2 = _split(_per_episode(np.random.default_rng(6), 4), [2, 2])
    del s2["seed"]
    with pytest.raises(SystemExit, match="provenance"):
        pooling.pool([s1, s2])


def test_seed_gap_is_refused():
    s1, s2 = _split(_per_episode(np.random.default_rng(7), 4), [2, 2])
    s2["seed"] = SEED0 + 3          # gap: episode at SEED0+2 measured nowhere
    with pytest.raises(SystemExit, match="tiling"):
        pooling.pool([s1, s2])


def test_seed_overlap_is_refused():
    s1, s2 = _split(_per_episode(np.random.default_rng(8), 4), [2, 2])
    s2["seed"] = SEED0 + 1          # overlap: episode at SEED0+1 counted twice
    with pytest.raises(SystemExit, match="tiling"):
        pooling.pool([s1, s2])


def test_per_episode_length_mismatch_is_refused():
    s1, s2 = _split(_per_episode(np.random.default_rng(9), 4), [2, 2])
    s2["per_episode"]["null"] = s2["per_episode"]["null"][:1]
    with pytest.raises(SystemExit, match="per_episode"):
        pooling.pool([s1, s2])


def test_energy_diagnostics_recombine_weighted_by_episodes():
    s1, s2 = _split(_per_episode(np.random.default_rng(10), 4), [1, 3])
    s1["energy_diagnostics"] = {a: {"charge_steps": 100.0} for a in ARMS}
    s2["energy_diagnostics"] = {a: {"charge_steps": 500.0} for a in ARMS}
    out = pooling.pool([s1, s2])
    # (1*100 + 3*500) / 4 = 400 — episode-weighted, not shard-averaged.
    assert out["energy_diagnostics"]["null"]["charge_steps"] == pytest.approx(400.0)


def test_required_n_is_reported_for_a_noisy_b_h():
    out = pooling.pool(_split(_per_episode(np.random.default_rng(11), 8), [4, 4]))
    n = out["required_n_b_h_excludes_zero"]
    assert n is not None and n >= 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
