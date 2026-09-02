"""The HMASD stack running on the relay corridor host (review §VII.4 integration).

Specification: `docs/Claude_docs/plans/ADR_02_RELAY_CORRIDOR_HOST.md` "Decision"
and "Parameters" (`n_z = K`, continuous `K`-vector low-level action, host argmax
= role, `RENEW` exactly for `i in S_t`, shared mean reward to the learner,
per-agent indicators logged), and
`docs/Claude_docs/reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` §VI.2 F4 /
§VII.4, which hand this seam to one integration commit.

Three smoke runs, no learning claim and no training beyond one rollout each:

  1  `off`: shapes, `RENEW` exactly at the `off` boundaries, the learner's stored
     reward equals the adapter's shared reward, one `agent.update` completes
  2  `d2` at D0 (`c = c_Z = inf`, `k_max = k_Z = k`): the renew masks equal the
     `off` boundaries
  3  `d2` at a finite `c` (`c = 0`): the renew mask handed to the host equals the
     agent's sampled mask at every step

Run (root `CLAUDE.md` sections Environment and Commands/Tests)::

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
        tests/relay_corridor_hmasd_test.py \
        --basetemp C:/Projects/HMASD/temp/relay_corridor_hmasd/pytest \
        -p no:cacheprovider

The memory preflight (`scripts/hmasd_resource_preflight.py admit-memory`) must
pass immediately before the run: every test here builds models.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from envs.relay_corridor.config import RelayCorridorConfig  # noqa: E402
from envs.relay_corridor.hmasd_driver import (  # noqa: E402
    RelayCorridorHMASDDriver,
    build_corridor_learner_config,
)

#: The small smoke object: K = 2, N = 3, Z = 4, H = 40, two lanes, k = 10.
N_AGENTS = 3
N_ROLES = 2
N_ZONES = 4
HORIZON = 40
K_FIXED = 10
NUM_ENVS = 2
MASTER_SEED = 20260902


def _corridor() -> RelayCorridorConfig:
    return RelayCorridorConfig(
        n_agents=N_AGENTS,
        n_roles=N_ROLES,
        n_zones=N_ZONES,
        n_regions=2,
        horizon=HORIZON,
        delta=0.4,
        event_process="bernoulli",
        lambda_regions=(0.005, 0.02),
        d0_k_set=(1, 2, 5, 10, 20),
    )


def _driver(tmp_path: Path, mode: str, **overrides) -> RelayCorridorHMASDDriver:
    return RelayCorridorHMASDDriver(
        _corridor(),
        mode=mode,
        num_envs=NUM_ENVS,
        rollout_length=HORIZON,
        k=K_FIXED,
        master_seed=MASTER_SEED,
        seed=MASTER_SEED,
        log_dir=str(tmp_path / f"logs_{mode}"),
        config_overrides=overrides or None,
    )


def test_1_off_smoke_run_on_the_corridor(tmp_path: Path) -> None:
    """`off`: dimensions from the host, RENEW at the `off` boundaries, one update."""

    corridor = _corridor()
    driver = _driver(tmp_path, "off")
    config = driver.config

    # ADR 02 "Parameters": n_z = K, low-level action dim = K, N and H from the host.
    assert config.n_z == corridor.n_roles == N_ROLES
    assert config.action_dim == corridor.low_level_action_dim == N_ROLES
    assert config.action_space_type == "continuous"
    assert config.n_agents == N_AGENTS
    assert config.episode_length == HORIZON
    assert config.obs_dim == driver.adapter.obs_dim
    assert config.state_dim == driver.adapter.state_dim
    # The team code stays present and inert: n_Z is not taken from the host.
    assert config.n_Z == 6

    summary = driver.run_rollout(update=True)

    assert summary["updated"] is True
    assert summary["steps"] == HORIZON
    assert summary["renew_masks"].shape == (HORIZON, NUM_ENVS, N_AGENTS)
    assert summary["service_indicators"].shape == (HORIZON, NUM_ENVS, N_AGENTS)
    assert summary["rewards"].shape == (HORIZON, NUM_ENVS)
    assert summary["roles"].shape == (HORIZON, NUM_ENVS, N_AGENTS)
    assert np.all(summary["roles"] >= 0) and np.all(summary["roles"] < N_ROLES)

    # RENEW is emitted exactly at the `off` boundaries: env_steps % k == 0.
    expected = np.zeros((HORIZON, NUM_ENVS, N_AGENTS), dtype=bool)
    expected[np.arange(0, HORIZON, K_FIXED), :, :] = True
    np.testing.assert_array_equal(summary["renew_masks"], expected)
    np.testing.assert_array_equal(summary["renew_masks"], summary["off_boundary_masks"])

    # The shared mean reward is what the learner stored: r_t = Delta/N * sum_i serve_i,
    # broadcast unchanged over the agents in the buffer's env-reward component.
    shared = (corridor.delta / N_AGENTS) * summary["service_indicators"].sum(axis=2)
    np.testing.assert_allclose(summary["rewards"], shared, rtol=0, atol=1e-12)
    stored = summary["stored_reward_env"]
    assert stored.shape == (HORIZON, NUM_ENVS, N_AGENTS)
    np.testing.assert_allclose(
        stored, np.repeat(summary["rewards"][:, :, None], N_AGENTS, axis=2),
        rtol=0, atol=1e-6,
    )

    # A RENEW step scores exactly zero service (host step order, part 1).
    assert not summary["service_indicators"][summary["renew_masks"]].any()

    # Per-agent service indicators reach the summary (ADR 02 "Metrics to log").
    assert summary["service_rate_per_agent"].shape == (N_AGENTS,)
    assert float(summary["renew_fraction"]) == pytest.approx(
        len(range(0, HORIZON, K_FIXED)) / HORIZON
    )


def test_2_d2_at_d0_reproduces_the_off_boundaries(tmp_path: Path) -> None:
    """D0 (`c = c_Z = inf`, `k_max = k_Z = k`) renews exactly at the `off` boundaries."""

    off_summary = _driver(tmp_path, "off").run_rollout(update=False)
    driver = _driver(
        tmp_path,
        "d2",
        interruption_cost_c=float("inf"),
        interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=K_FIXED,
        team_cap_k_Z=K_FIXED,
    )
    summary = driver.run_rollout(update=True)

    expected = np.zeros((HORIZON, NUM_ENVS, N_AGENTS), dtype=bool)
    expected[np.arange(0, HORIZON, K_FIXED), :, :] = True
    np.testing.assert_array_equal(summary["off_boundary_masks"], expected)
    np.testing.assert_array_equal(summary["renew_masks"], expected)
    np.testing.assert_array_equal(summary["renew_masks"], off_summary["renew_masks"])
    # The mask handed to the host is the agent's sampled mask, and at D0 that is
    # the `off` boundary mask.
    np.testing.assert_array_equal(summary["sampled_masks"], summary["renew_masks"])

    # Stronger than the ADR requires, and recorded as an observation: at D0 the
    # skills are bit-equal to `off` on the same seed, so the low-level actions,
    # the decoded roles and the corridor trajectory are identical too.  Only the
    # boundary equality above is a claim of ADR 01 invariant 2; this comparison
    # is on the first rollout, before either run has updated anything.
    np.testing.assert_array_equal(summary["roles"], off_summary["roles"])
    np.testing.assert_array_equal(
        summary["service_indicators"], off_summary["service_indicators"]
    )
    np.testing.assert_allclose(
        summary["rewards"], off_summary["rewards"], rtol=0, atol=1e-12
    )

    metrics = summary["d2_metrics"]
    assert metrics["cause_counts"]["gap"] == 0
    assert metrics["cause_counts"]["team_gap"] == 0
    # Two lanes x four segments of length k: the D0 row count of one rollout.
    assert metrics["rows_M"] == NUM_ENVS * (HORIZON // K_FIXED)
    assert metrics["rows_M_agent"] == NUM_ENVS * N_AGENTS * (HORIZON // K_FIXED)
    assert metrics["cause_counts"]["reset"] == NUM_ENVS
    assert metrics["cause_counts"]["team_cap"] == NUM_ENVS * (HORIZON // K_FIXED - 1)
    assert summary["updated"] is True


def test_3_d2_at_finite_cost_passes_the_sampled_mask_to_the_host(tmp_path: Path) -> None:
    """A finite `c` renews exactly for `i in S_t`, step by step."""

    driver = _driver(
        tmp_path,
        "d2",
        interruption_cost_c=0.0,
        interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=K_FIXED,
        team_cap_k_Z=HORIZON,
    )
    summary = driver.run_rollout(update=False)

    sampled = summary["sampled_masks"]
    np.testing.assert_array_equal(summary["renew_masks"], sampled)
    # `c = 0` samples every live agent every step (ADR 01 invariant 4), so the
    # renew mask is all-True and is *not* the `off` boundary mask.
    assert sampled.all()
    metrics = summary["d2_metrics"]
    assert metrics["cause_counts"]["gap"] > 0
    assert metrics["rows_M"] == NUM_ENVS * HORIZON
    assert not np.array_equal(sampled, summary["off_boundary_masks"])
    # Every step is a RENEW step, so the corridor serves nobody: the shared
    # reward is identically zero.
    assert not summary["service_indicators"].any()
    np.testing.assert_array_equal(summary["rewards"], np.zeros((HORIZON, NUM_ENVS)))


def test_4_d2_config_takes_its_dimensions_from_the_host(tmp_path: Path) -> None:
    """`build_corridor_learner_config` reads the adapter, and the D2 guards apply."""

    driver = _driver(
        tmp_path,
        "d2",
        interruption_cost_c=float("inf"),
        interruption_cost_c_Z=float("inf"),
        skill_cap_k_max=K_FIXED,
        team_cap_k_Z=K_FIXED,
    )
    corridor = _corridor()
    config = build_corridor_learner_config(
        corridor,
        driver.adapter,
        mode="d2",
        num_envs=NUM_ENVS,
        rollout_length=2 * HORIZON,
        k=K_FIXED,
        overrides={
            "interruption_cost_c": float("inf"),
            "interruption_cost_c_Z": float("inf"),
            "skill_cap_k_max": K_FIXED,
            "team_cap_k_Z": K_FIXED,
        },
    )
    assert config.rollout_length == 2 * HORIZON
    assert config.n_z == corridor.n_roles

    # The rollout-boundary guard (review VII F1) applies on this route too.
    with pytest.raises(ValueError):
        build_corridor_learner_config(
            corridor,
            driver.adapter,
            mode="d2",
            num_envs=NUM_ENVS,
            rollout_length=HORIZON + 5,
            k=K_FIXED,
            overrides={
                "interruption_cost_c": float("inf"),
                "interruption_cost_c_Z": float("inf"),
                "skill_cap_k_max": K_FIXED,
                "team_cap_k_Z": K_FIXED,
            },
        )
