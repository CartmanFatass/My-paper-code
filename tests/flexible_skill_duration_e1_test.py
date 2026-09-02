"""Tests for the E1 age-input runner (`scripts/run_flexible_skill_duration_e1.py`).

Contract: `docs/Claude_docs/experiments/E1_AGE_INPUT_20260902.md`.

Three things are covered, in the order the executing instruction names them:

1. the frozen probe set's content-digest check (and that a wrong digest refuses the run);
2. the age-bucket split, the label-agreement arithmetic, the accuracy-by-bucket arithmetic
   and the age-weight-share arithmetic, each on a tiny synthetic array whose answer is
   written out by hand;
3. the rollout-1 comparison.  **No E0 `d0` run exists at 32 lanes** (E0 ran its arms at 16
   lanes; the only 32-lane E0 runs are two-rollout `off`-arm timing runs), so contract
   section 2's fallback is used and the two E1 arms' rollout 1 is compared to each other.
   What is compared, and what parity actually holds, is stated in the test docstrings.

Top-level tests use `*_test.py` (`.gitignore` ignores `test*.py`).  Run with an isolated
temp dir, e.g.

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
        --basetemp C:/Projects/HMASD/temp/pytest_e1_age_input \
        tests/flexible_skill_duration_e1_test.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_flexible_skill_duration_e1 as e1  # noqa: E402

E1_OUTPUT_ROOT = Path(os.environ.get(
    "E1_OUTPUT_ROOT",
    "C:/Projects/HMASD/temp/directions/flexible_skill_duration/exp/E1_20260902",
))
E0_OUTPUT_ROOT = Path(os.environ.get(
    "E0_OUTPUT_ROOT",
    "C:/Projects/HMASD/temp/directions/flexible_skill_duration/exp/E0_20260902",
))


# ---------------------------------------------------------------------------
# 1. probe-set digest
# ---------------------------------------------------------------------------


def test_frozen_probe_set_matches_the_contract_digest():
    """The contract's probe set loads and reproduces its recorded content digest."""
    path = Path(e1.DEFAULT_PROBE_SET)
    if not path.exists():
        pytest.skip(f"frozen probe set not present at {path}")
    arrays, digest = e1.load_probe_set(path)
    assert digest == e1.PROBE_SET_CONTENT_SHA256
    assert arrays["states"].shape == (1536, 119)
    assert arrays["states"].dtype == np.float64
    assert arrays["observations"].shape == (1536, 6, 104)
    assert arrays["observations"].dtype == np.float32
    assert arrays["team_skills"].shape == (1536,)
    assert arrays["agent_skills"].shape == (1536, 6)
    assert arrays["env_step"].shape == (1536,)


def test_probe_set_with_a_wrong_digest_is_refused(tmp_path):
    """A probe set whose content digest does not match refuses the run."""
    path = tmp_path / "probe_set.npz"
    np.savez(
        path,
        states=np.zeros((2, 3), dtype=np.float64),
        observations=np.zeros((2, 2, 4), dtype=np.float32),
        team_skills=np.zeros(2, dtype=np.int64),
        agent_skills=np.zeros((2, 2), dtype=np.int64),
        env_step=np.zeros(2, dtype=np.int64),
        rollout_index=np.zeros(2, dtype=np.int64),
        lane=np.zeros(2, dtype=np.int64),
    )
    with pytest.raises(RuntimeError, match="content digest mismatch"):
        e1.load_probe_set(path, e1.PROBE_SET_CONTENT_SHA256)

    # the same file passes once its own digest is the expected one
    import run_flexible_skill_duration_e0 as e0  # noqa: WPS433 - local, test-only
    with np.load(str(path)) as handle:
        own = e0._sha256_arrays({k: np.asarray(handle[k]) for k in handle.files})
    arrays, digest = e1.load_probe_set(path, own)
    assert digest == own
    assert set(arrays) >= set(e1.PROBE_ARRAY_KEYS)


def test_probe_set_missing_array_is_refused(tmp_path):
    path = tmp_path / "incomplete.npz"
    np.savez(path, states=np.zeros((2, 3)))
    with pytest.raises(RuntimeError, match="missing arrays"):
        e1.load_probe_set(path, "0" * 64)


# ---------------------------------------------------------------------------
# 2a. the age bucket split
# ---------------------------------------------------------------------------


def test_normalized_ages_are_env_step_mod_10_over_10():
    env_step = np.array([0, 1, 7, 9, 10, 13, 19, 500, 499], dtype=np.int64)
    raw, age = e1.normalized_ages(env_step)
    assert raw.tolist() == [0, 1, 7, 9, 0, 3, 9, 0, 9]
    np.testing.assert_allclose(
        age, np.array([0.0, 0.1, 0.7, 0.9, 0.0, 0.3, 0.9, 0.0, 0.9], dtype=np.float32),
        rtol=0, atol=1e-7)
    assert age.dtype == np.float32


def test_age_bucket_split_covers_0_to_9_exactly_once():
    raw = np.arange(10, dtype=np.int64)
    masks = e1.age_bucket_masks(raw)
    assert masks["0-2"].tolist() == [True] * 3 + [False] * 7
    assert masks["3-6"].tolist() == [False] * 3 + [True] * 4 + [False] * 3
    assert masks["7-9"].tolist() == [False] * 7 + [True] * 3
    # every age lands in exactly one bucket
    stacked = np.stack([masks[name] for name, _v in e1.AGE_BUCKETS])
    assert stacked.sum(axis=0).tolist() == [1] * 10
    assert e1.age_bucket_index(raw).tolist() == [0, 0, 0, 1, 1, 1, 1, 2, 2, 2]


# ---------------------------------------------------------------------------
# 2b. label agreement
# ---------------------------------------------------------------------------


def test_team_label_agreement_on_a_tiny_array():
    previous = np.array([0, 1, 2, 3, 4])
    current = np.array([0, 1, 5, 3, 5])
    # 3 of 5 probes keep their label
    assert e1.team_agreement(previous, current) == pytest.approx(0.6)
    assert e1.team_agreement(previous, previous) == 1.0
    assert e1.team_agreement(np.array([]), np.array([])) is None


def test_individual_label_agreement_is_per_agent_then_averaged():
    # 4 probes, 3 agents
    previous = np.array([[0, 0, 0],
                         [1, 1, 1],
                         [2, 2, 2],
                         [3, 3, 3]])
    current = np.array([[0, 0, 9],
                        [1, 9, 9],
                        [2, 2, 9],
                        [9, 3, 3]])
    per_agent, mean = e1.individual_agreement(previous, current)
    # agent 0: 3/4, agent 1: 3/4, agent 2: 1/4
    assert per_agent == pytest.approx([0.75, 0.75, 0.25])
    assert mean == pytest.approx((0.75 + 0.75 + 0.25) / 3)
    # the per-agent-then-average order matters only when agents differ; here every agent
    # has the same probe count, so the flat mean coincides
    assert mean == pytest.approx(float(np.mean(previous == current)))


def test_individual_label_agreement_rejects_a_wrong_rank():
    with pytest.raises(ValueError):
        e1.individual_agreement(np.zeros(4), np.zeros(4))
    with pytest.raises(ValueError):
        e1.individual_agreement(np.zeros((4, 3)), np.zeros((4, 2)))


# ---------------------------------------------------------------------------
# 2c. accuracy overall and by age bucket
# ---------------------------------------------------------------------------


def test_team_accuracy_by_age_bucket_on_a_tiny_array():
    #                ages: 0    1    4    7    9    3
    raw = np.array([0, 1, 4, 7, 9, 3], dtype=np.int64)
    truth = np.array([1, 1, 2, 2, 3, 3])
    labels = np.array([1, 0, 2, 2, 3, 0])
    out = e1.accuracy_overall_and_by_bucket(labels, truth, raw)
    # overall: 4 of 6 correct
    assert out["overall"] == pytest.approx(4 / 6)
    assert out["overall_n"] == 6
    # bucket 0-2: probes at ages 0 and 1 -> correct, wrong -> 1/2
    assert out["0-2"] == pytest.approx(0.5)
    assert out["0-2_n"] == 2
    # bucket 3-6: probes at ages 4 and 3 -> correct, wrong -> 1/2
    assert out["3-6"] == pytest.approx(0.5)
    assert out["3-6_n"] == 2
    # bucket 7-9: probes at ages 7 and 9 -> both correct
    assert out["7-9"] == pytest.approx(1.0)
    assert out["7-9_n"] == 2


def test_individual_accuracy_broadcasts_the_age_over_agents():
    raw = np.array([0, 8], dtype=np.int64)
    truth = np.array([[1, 1, 1], [2, 2, 2]])
    labels = np.array([[1, 1, 0], [2, 0, 0]])
    out = e1.accuracy_overall_and_by_bucket(labels, truth, raw)
    assert out["overall"] == pytest.approx(3 / 6)
    assert out["overall_n"] == 6
    assert out["0-2"] == pytest.approx(2 / 3)
    assert out["0-2_n"] == 3
    assert out["3-6"] is None
    assert out["3-6_n"] == 0
    assert out["7-9"] == pytest.approx(1 / 3)
    assert out["7-9_n"] == 3


def test_accuracy_rejects_mismatched_shapes():
    with pytest.raises(ValueError):
        e1.accuracy_overall_and_by_bucket(np.zeros(3), np.zeros(4), np.zeros(3))


# ---------------------------------------------------------------------------
# 2d. the age-feature weight share
# ---------------------------------------------------------------------------


def test_age_weight_share_takes_the_last_column():
    weight = np.array([[3.0, 0.0, 4.0],
                       [0.0, 0.0, 0.0]])
    share = e1.age_weight_share(weight, age_columns=1)
    assert share["age_column_norm"] == pytest.approx(4.0)
    assert share["input_projection_norm"] == pytest.approx(5.0)
    assert share["age_share"] == pytest.approx(0.8)
    assert e1.age_weight_share(weight, age_columns=0) is None


# ---------------------------------------------------------------------------
# 2e. the r >= R/2 window
# ---------------------------------------------------------------------------


def _record(rollout, agreement, team_acc, drift):
    accuracy = {"overall": team_acc, "overall_n": 4,
                "0-2": team_acc, "0-2_n": 2, "3-6": team_acc, "3-6_n": 1,
                "7-9": team_acc, "7-9_n": 1}
    return {
        "rollout": rollout,
        "team_label_agreement": agreement,
        "individual_label_agreement": agreement,
        "team_value_mean_abs_change": drift,
        "agent_value_mean_abs_change": drift,
        "team_accuracy": accuracy,
        "individual_accuracy": accuracy,
        "age_weight_share": {"team": None, "individual": None},
    }


def test_window_starts_at_ceil_R_over_2():
    records = [_record(r, None if r == 1 else 0.5 + 0.1 * r, 0.1 * r, float(r))
               for r in range(1, 5)]
    out = e1.summarise_probe_records(records, rollouts=4)
    assert out["window_start_rollout"] == 2
    assert out["window_rollouts"] == [2, 3, 4]
    assert out["team_label_agreement_mean_window"] == pytest.approx(
        np.mean([0.7, 0.8, 0.9]))
    assert out["team_value_mean_abs_change_mean_window"] == pytest.approx(3.0)
    assert out["team_value_mean_abs_change_var_window"] == pytest.approx(
        float(np.var([2.0, 3.0, 4.0])))
    assert out["team_accuracy_overall_mean_window"] == pytest.approx(
        np.mean([0.2, 0.3, 0.4]))
    assert out["team_accuracy_final"]["overall"] == pytest.approx(0.4)


def test_window_of_20_rollouts_holds_ten_checkpoints():
    records = [_record(r, None if r == 1 else 1.0, 1.0, 1.0) for r in range(1, 21)]
    out = e1.summarise_probe_records(records, rollouts=20)
    assert out["window_start_rollout"] == 10
    assert len(out["window_rollouts"]) == 11  # rollouts 10..20 inclusive


# ---------------------------------------------------------------------------
# 3. rollout-1 comparison
# ---------------------------------------------------------------------------


def test_no_e0_d0_run_exists_at_32_lanes():
    """States the premise of the fallback in `test_e1_arms_rollout1_parity`.

    The executing instruction asks for a bit-identity check of the E1 `d0` arm's first
    rollout against an E0 `d0` run at the same seed and lanes.  E0 ran its arms at 16 lanes
    (E0 result document deviation D1); the only 32-lane E0 runs are two-rollout `off`-arm
    timing runs.  This test records that absence rather than assuming it.
    """
    if not E0_OUTPUT_ROOT.exists():
        pytest.skip(f"E0 output root not present at {E0_OUTPUT_ROOT}")
    at_32 = []
    for manifest_path in sorted(E0_OUTPUT_ROOT.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("arm") == "d0" and int(manifest["config"]["num_envs"]) == 32:
            at_32.append(manifest_path.parent.name)
    assert at_32 == [], (
        "an E0 d0 run at 32 lanes now exists; the E1 rollout-1 check should compare "
        f"against it instead of against the other E1 arm: {at_32}"
    )


def _e1_rollout1(run_name):
    run_dir = E1_OUTPUT_ROOT / run_name
    if not (run_dir / "rollout1_summary.json").exists():
        pytest.skip(f"E1 run artifacts not present at {run_dir}")
    return {
        "dir": run_dir,
        "summary": json.loads((run_dir / "rollout1_summary.json").read_text(encoding="utf-8")),
        "boundaries": np.load(run_dir / "rollout1_boundaries.npy"),
        "team_skills": np.load(run_dir / "rollout1_team_skills.npy"),
        "agent_skills": np.load(run_dir / "rollout1_agent_skills.npy"),
        "metrics": [json.loads(line) for line in
                    (run_dir / "metrics.jsonl").read_text(encoding="utf-8").splitlines()
                    if line.strip()],
    }


def test_e1_arms_rollout1_parity():
    """Contract section 2's fallback comparison, stated precisely.

    Compared: the D0 and D1 arms of seed 1, rollout 1, at the same lanes and the same
    learner seed.

    **Identical (asserted):** the skill-boundary mask `[T, E]` and its sha256; the
    high-level row count `M`; the transition and episode counts.

    **Not identical (asserted, and recorded as deviation):** the sampled team and agent
    skills, hence the trajectory and the returns.  Contract section 2 expects rollout 1 to
    be "identical up to the first discriminator update"; it is not, and
    `test_d0_d1_construction_parity_and_rng_divergence` shows why - the D1 discriminators
    take one extra input column, so their initialisation consumes a different number of
    draws from the global torch RNG and every later sample diverges.  The coordinator and
    the discoverer, which are constructed *before* the discriminators, are bit-identical.
    """
    d0 = _e1_rollout1("d0_seed1")
    d1 = _e1_rollout1("d1_seed1")

    assert np.array_equal(d0["boundaries"], d1["boundaries"])
    assert d0["summary"]["boundaries_sha256"] == d1["summary"]["boundaries_sha256"]
    assert d0["summary"]["boundary_count"] == d1["summary"]["boundary_count"]
    assert d0["summary"]["rows_M"] == d1["summary"]["rows_M"]

    m0, m1 = d0["metrics"][0], d1["metrics"][0]
    assert m0["rows_M"] == m1["rows_M"]
    assert m0["transitions_this_rollout"] == m1["transitions_this_rollout"]
    assert m0["episodes_this_rollout"] == m1["episodes_this_rollout"]
    assert m0["optimizer_steps_this_rollout"] == m1["optimizer_steps_this_rollout"]

    # the recorded non-parity, asserted so a future change of it is caught
    assert not np.array_equal(d0["team_skills"], d1["team_skills"])
    assert not np.array_equal(d0["agent_skills"], d1["agent_skills"])


def test_d0_d1_construction_parity_and_rng_divergence():
    """Why rollout 1 is not bit-identical between the arms.

    With the same `torch.manual_seed(seed)`, the coordinator and the discoverer - both
    constructed before the discriminators - come out bit-identical in the two arms.  The
    D1 discriminators carry one extra input column (`state_dim + 1`, `obs_dim + 1`), so
    their initialisation draws a different number of values and the global torch RNG state
    after construction differs.  Everything sampled afterwards therefore differs.
    """
    import random

    import torch

    import run_flexible_skill_duration_e0 as e0
    from hmasd.agent import HMASDAgent

    scratch = REPO_ROOT / "temp" / "directions" / "flexible_skill_duration" / "test"
    scratch.mkdir(parents=True, exist_ok=True)

    def build(arm):
        random.seed(1)
        np.random.seed(1)
        torch.manual_seed(1)
        config = e0._make_config("d0", 1, 4, 100, 100, 6, 50, 2, 119, 104)
        if arm == "d1":
            config.age_feature = "normalized"
            config._validate_policy_interruption()
        agent = HMASDAgent(config,
                           log_dir=str(scratch / f"e1_rng_parity_{arm}"),
                           device=torch.device("cpu"))
        return agent, torch.get_rng_state().clone()

    agent_d0, state_d0 = build("d0")
    agent_d1, state_d1 = build("d1")

    def parameters_equal(left, right):
        left_params = dict(left.named_parameters())
        right_params = dict(right.named_parameters())
        assert set(left_params) == set(right_params)
        return all(torch.equal(left_params[k], right_params[k]) for k in left_params)

    assert parameters_equal(agent_d0.skill_coordinator, agent_d1.skill_coordinator)
    assert parameters_equal(agent_d0.skill_discoverer, agent_d1.skill_discoverer)

    assert agent_d0.team_discriminator.age_input_dim == 0
    assert agent_d1.team_discriminator.age_input_dim == 1
    assert agent_d0.individual_discriminator.age_input_dim == 0
    assert agent_d1.individual_discriminator.age_input_dim == 1
    assert (agent_d1.team_discriminator.input_projection.weight.shape[1]
            == agent_d0.team_discriminator.input_projection.weight.shape[1] + 1)
    assert (agent_d1.individual_discriminator.obs_input_projection.weight.shape[1]
            == agent_d0.individual_discriminator.obs_input_projection.weight.shape[1] + 1)

    assert not torch.equal(state_d0, state_d1)
