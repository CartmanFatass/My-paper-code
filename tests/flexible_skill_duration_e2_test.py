"""Tests-as-specs for the E2 runner and aggregator.

Contract: `docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_20260903.md`.

Covered, in the order the executing instruction names them:

1. the arm table - nine arms, D0 `c = inf` with `k_max = k_Z = k`, D2 `c` with cap 40;
2. the references being computed and recorded in the manifest;
3. the event-alignment definition - within one step after the agent's region flag flipped;
4. the segment-length and gap-decile accounting;
5. the matching property of contract section 2 - D0 `k = 40` and D2 `c = 2.0` share a
   first rollout until the first interruption - at a miniature size;
6. contract section 5's reading rule on synthetic summaries, for each of its branches.

Plus one end-to-end miniature run that exercises the manifest, the matched evaluation
tapes, `eval.jsonl` / `interruptions.jsonl` / `gaps.jsonl` / `summary.json` and the final
checkpoint.

Run (root `CLAUDE.md` sections Environment and Commands/Tests)::

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q \
        tests/flexible_skill_duration_e2_test.py \
        --basetemp C:/Projects/HMASD/temp/pytest_fsd_e2 -p no:cacheprovider

The memory preflight (`scripts/hmasd_resource_preflight.py admit-memory`) must pass
immediately before the run: the miniature runs here build models.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_flexible_skill_duration_e2 as e2  # noqa: E402
import run_flexible_skill_duration_e2_aggregate as agg  # noqa: E402
from envs.relay_corridor.config import RelayCorridorConfig, validate_horizon  # noqa: E402
from envs.relay_corridor.hmasd_driver import RelayCorridorHMASDDriver  # noqa: E402
from envs.relay_corridor.references import enumerate_references  # noqa: E402

INF = float("inf")

#: A miniature corridor: the same shape as the E2 point, small enough to run in a test.
MINI_HOST = dict(
    n_agents=3,
    n_roles=2,
    n_zones=4,
    n_regions=2,
    horizon=40,
    delta=0.4,
    event_process="bernoulli",
    lambda_regions=(0.02, 0.02),
    d0_k_set=(1, 2, 4),
    rho=0.0,
    c_probe=0.0,
    role_decode="argmax",
)


# ---------------------------------------------------------------------------
# 1. the arm table
# ---------------------------------------------------------------------------


def test_arm_table_has_nine_arms_with_the_contract_grid() -> None:
    assert len(e2.ARMS) == 9
    assert set(e2.ARM_ORDER) == set(e2.ARMS)
    assert len(e2.ARM_ORDER) == 9
    # contract section 2 order: the central pair first, seed order handled by the queue
    assert e2.ARM_ORDER[:2] == ("d0_k40", "d2_c1p0")
    assert e2.D0_K_SET == (1, 2, 5, 20, 40)
    assert e2.D2_C_SET == (0.25, 0.5, 1.0, 2.0)
    assert e2.D2_K_CAP == 40
    d0 = sorted(row["k"] for row in e2.ARMS.values() if row["family"] == "d0")
    d2 = sorted(row["c"] for row in e2.ARMS.values() if row["family"] == "d2")
    assert d0 == [1, 2, 5, 20, 40]
    assert d2 == [0.25, 0.5, 1.0, 2.0]


@pytest.mark.parametrize("k", [1, 2, 5, 20, 40])
def test_d0_arms_are_infinite_cost_with_both_caps_tied_to_k(k: int) -> None:
    """The fair D0 of ADR 01: `c = c_Z = inf`, `k_max = k_Z = k`."""
    params = e2.arm_parameters(f"d0_k{k}")
    assert params["policy_interruption_mode"] == "d2"
    assert params["interruption_delta"] == 1
    assert params["interruption_cost_c"] == INF
    assert params["interruption_cost_c_Z"] == INF
    assert params["skill_cap_k_max"] == k
    assert params["team_cap_k_Z"] == k
    assert params["age_feature"] == "off"


@pytest.mark.parametrize("c,slug", [(0.25, "0p25"), (0.5, "0p5"),
                                    (1.0, "1p0"), (2.0, "2p0")])
def test_d2_arms_carry_the_cost_on_both_levels_with_cap_40(c: float, slug: str) -> None:
    params = e2.arm_parameters(f"d2_c{slug}")
    assert params["policy_interruption_mode"] == "d2"
    assert params["interruption_cost_c"] == pytest.approx(c)
    assert params["interruption_cost_c_Z"] == pytest.approx(c)
    assert params["skill_cap_k_max"] == 40
    assert params["team_cap_k_Z"] == 40
    assert params["age_feature"] == "off"


def test_unknown_arm_is_refused() -> None:
    with pytest.raises(KeyError):
        e2.arm_parameters("d2_c3p0")


def test_outer_arms_are_the_contract_4_4_drop_list() -> None:
    assert set(e2.OUTER_ARMS) == {"d0_k1", "d0_k2", "d2_c0p25", "d2_c2p0"}


# ---------------------------------------------------------------------------
# 2. the host point and the references
# ---------------------------------------------------------------------------


def test_host_point_is_the_contract_section_2_point() -> None:
    corridor = e2.corridor_config()
    record = corridor.parameter_record()
    assert record["N"] == 6
    assert record["K"] == 2
    assert record["Z"] == 4
    assert record["H"] == 400
    assert record["Delta"] == pytest.approx(0.4)
    assert record["event_process"] == "bernoulli"
    # homogeneous: the small row's *second* region rate for both regions
    assert record["lambda_regions"] == (0.02, 0.02)
    assert record["rho"] == 0.0
    assert record["c_probe"] == 0.0
    assert record["role_decode"] == "argmax"
    assert record["D0_k_set"] == (1, 2, 5, 20, 40)
    assert record["e5_coupling_enabled"] is False
    # ADR 02 invariant 6: H >= 10 * max(D0_k_set)
    assert validate_horizon(corridor, mode="d0_fixed_k")["accepted"] is True


def test_references_are_computed_for_the_e2_point() -> None:
    """`enumerate_references` on this point; the numbers are pinned as a regression."""
    report = enumerate_references(e2.corridor_config())
    record = report.as_dict()
    assert record["J_switch"] == pytest.approx(0.39202, abs=1e-9)
    # K = 2: greedy equals the switching oracle exactly (ADR 02 invariant 8)
    assert record["J_switch"] == pytest.approx(report.j_greedy, abs=0.0)
    expected = {1: 0.001, 2: 0.197, 5: 0.3053168128,
                20: 0.3133920282449043, 40: 0.2681497980245237}
    assert set(record["J_fixed_k"]) == set(expected)
    for k, value in expected.items():
        assert record["J_fixed_k"][k] == pytest.approx(value, abs=1e-9)
    assert record["best_fixed_k"] == 20
    assert record["J_best_fixed_k"] == pytest.approx(expected[20], abs=1e-9)
    assert record["m"] == pytest.approx(record["J_switch"] - record["J_open_best"],
                                        abs=1e-12)
    assert record["m_dur"] == pytest.approx(record["J_switch"] - expected[20], abs=1e-12)
    # the acceptance-scale margin is positive and resolvable at the contract's tapes
    assert record["m_dur"] > 0.0
    assert report.resolution_ok(sigma_delta=0.4, episodes=4096)


# ---------------------------------------------------------------------------
# 3. the event-alignment definition
# ---------------------------------------------------------------------------


def test_event_alignment_counts_the_flip_step_and_the_step_after() -> None:
    """`within one step after the flag flipped` = the window {t_flip, t_flip + 1}."""
    steps, lanes, agents, regions = 6, 1, 2, 2
    region_of_agent = np.array([0, 1], dtype=np.int64)
    change_flag = np.zeros((steps, lanes, regions), dtype=np.int64)
    change_flag[2, 0, 0] = 1          # region 0 flips at step 2
    sampled = np.zeros((steps, lanes, agents), dtype=bool)
    sampled[2, 0, 0] = True           # on the flip step        -> aligned (both readings)
    sampled[3, 0, 0] = True           # one step after          -> aligned (window only)
    sampled[4, 0, 0] = True           # two steps after         -> not aligned
    sampled[2, 0, 1] = True           # other region, same step -> not aligned

    out = e2.event_alignment(sampled, change_flag, region_of_agent)
    assert out["interruptions"] == 4
    assert out["aligned_count"] == 2
    assert out["aligned_fraction"] == pytest.approx(0.5)
    assert out["aligned_count_strict"] == 1
    assert out["aligned_fraction_strict"] == pytest.approx(0.25)
    assert out["aligned_window"] == "{t_flip, t_flip + 1}"


def test_event_alignment_never_reaches_back_before_the_flip() -> None:
    steps, lanes, agents, regions = 4, 1, 1, 1
    change_flag = np.zeros((steps, lanes, regions), dtype=np.int64)
    change_flag[2, 0, 0] = 1
    sampled = np.zeros((steps, lanes, agents), dtype=bool)
    sampled[1, 0, 0] = True           # the step *before* the flip is not aligned
    out = e2.event_alignment(sampled, change_flag, np.array([0]))
    assert out["aligned_count"] == 0
    assert out["aligned_fraction"] == pytest.approx(0.0)


def test_event_alignment_of_an_empty_interruption_set_is_none() -> None:
    out = e2.event_alignment(np.zeros((3, 1, 1), dtype=bool),
                             np.zeros((3, 1, 1), dtype=np.int64), np.array([0]))
    assert out["interruptions"] == 0
    assert out["aligned_fraction"] is None


# ---------------------------------------------------------------------------
# 4. segment-length and gap-decile accounting
# ---------------------------------------------------------------------------


def test_decile_summary_reports_nine_deciles_and_drops_non_finite() -> None:
    values = list(range(1, 11)) + [float("nan"), float("inf")]
    out = e2.decile_summary(values)
    assert out["count"] == 10
    assert out["min"] == 1.0 and out["max"] == 10.0
    assert out["mean"] == pytest.approx(5.5)
    assert len(out["deciles"]) == 9
    assert out["quantiles"] == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    assert out["deciles"] == pytest.approx(
        [float(q) for q in np.quantile(np.arange(1.0, 11.0), e2.DECILE_QUANTILES)])
    empty = e2.decile_summary([])
    assert empty["count"] == 0 and empty["deciles"] is None


def test_interruption_record_accounts_causes_segments_and_alignment() -> None:
    steps, lanes, agents, regions = 5, 1, 2, 2
    region_of_agent = np.array([0, 1], dtype=np.int64)
    sampled = np.zeros((steps, lanes, agents), dtype=bool)
    agent_cause = np.full((steps, lanes, agents), e2.CAUSE_NONE, dtype=np.int64)
    team_cause = np.full((steps, lanes), e2.CAUSE_NONE, dtype=np.int64)
    change_flag = np.zeros((steps, lanes, regions), dtype=np.int64)

    # t = 0: reset, both agents sampled, team decision
    sampled[0, 0, :] = True
    agent_cause[0, 0, :] = e2.CAUSE_RESET
    team_cause[0, 0] = e2.CAUSE_RESET
    # t = 2: region 0 flips; agent 0 fires on the gap
    change_flag[2, 0, 0] = 1
    sampled[2, 0, 0] = True
    agent_cause[2, 0, 0] = e2.CAUSE_GAP
    # t = 4: agent 1 fires on the cap
    sampled[4, 0, 1] = True
    agent_cause[4, 0, 1] = e2.CAUSE_CAP

    record = e2.interruption_record(
        3, "d2_c1p0", 1, sampled, agent_cause, team_cause, change_flag,
        region_of_agent, [4, 4, 2], [4, 6], k_max=40)

    assert record["rollout"] == 3 and record["arm"] == "d2_c1p0" and record["seed"] == 1
    assert record["agent_steps"] == steps * lanes * agents == 10
    assert record["interruptions"] == 4
    assert record["interruption_rate_per_agent_step"] == pytest.approx(0.4)
    assert record["cause_counts_sampled_positions"]["reset"] == 2
    assert record["cause_counts_sampled_positions"]["gap"] == 1
    assert record["cause_counts_sampled_positions"]["cap"] == 1
    assert record["fraction_closed_by_cap"] == pytest.approx(0.25)
    assert record["fraction_closed_by_gap"] == pytest.approx(0.25)
    assert record["team_reset_count"] == 1
    assert record["team_switch_count_gap"] == 0
    # alignment over all interruptions: only the t = 2 firing sits in the window
    assert record["event_alignment"]["aligned_count"] == 1
    assert record["event_alignment"]["aligned_fraction"] == pytest.approx(0.25)
    # alignment restricted to gap-caused interruptions: 1 of 1
    assert record["event_alignment_gap_caused_only"]["interruptions"] == 1
    assert record["event_alignment_gap_caused_only"]["aligned_fraction"] == pytest.approx(1.0)
    # segment lengths flow through untouched
    assert record["segment_length_agent"]["count"] == 3
    assert record["segment_length_agent"]["mean"] == pytest.approx(10.0 / 3.0)
    assert record["segment_length_team"]["count"] == 2
    assert record["k_max"] == 40


def test_gap_record_reports_deciles_of_both_levels_and_drops_reset_steps() -> None:
    gap_agent = np.array([[[0.1, 0.2]], [[np.nan, np.nan]], [[0.3, 0.4]]])
    gap_team = np.array([[0.5], [np.nan], [0.7]])
    record = e2.gap_record(2, "d0_k40", 1, gap_agent, gap_team)
    assert record["rollout"] == 2
    assert record["gap_agent"]["count"] == 4          # the NaN reset step is excluded
    assert record["gap_agent"]["min"] == pytest.approx(0.1)
    assert record["gap_agent"]["max"] == pytest.approx(0.4)
    assert len(record["gap_agent"]["deciles"]) == 9
    assert record["gap_team"]["count"] == 2


# ---------------------------------------------------------------------------
# 5. the matching property of contract section 2, at a miniature size
# ---------------------------------------------------------------------------


def _mini_driver(tmp_path: Path, tag: str, overrides: dict,
                 seed: int = 1) -> RelayCorridorHMASDDriver:
    corridor = RelayCorridorConfig(**MINI_HOST)
    driver = RelayCorridorHMASDDriver(
        corridor,
        mode="d2",
        num_envs=2,
        rollout_length=corridor.horizon,
        k=int(overrides["skill_cap_k_max"]),
        master_seed=seed,
        seed=seed,
        log_dir=str(tmp_path / f"logs_{tag}"),
        config_overrides=dict(overrides),
    )
    driver.config.__class__ = e2.E2CorridorConfig
    return driver


def _mini_rollout1(tmp_path: Path, run_dir: Path, overrides: dict, tag: str,
                   seed: int = 1) -> None:
    driver = _mini_driver(tmp_path, tag, overrides, seed=seed)
    recorder = e2.DriverRecorder(driver)
    summary = driver.run_rollout(update=False)
    captured = recorder.stacked()
    run_dir.mkdir(parents=True, exist_ok=True)
    np.savez(
        run_dir / "rollout1_match.npz",
        sampled=captured["sampled"],
        roles=np.asarray(summary["roles"], dtype=np.int64),
        rewards=np.asarray(summary["rewards"], dtype=np.float64),
        service=np.asarray(summary["service_indicators"], dtype=bool),
        gap_agent=captured["gap_agent"],
        gap_team=captured["gap_team"],
        agent_cause=captured["agent_cause"],
        change_flag=captured["change_flag"],
    )


def test_d0_and_d2_share_the_first_rollout_until_the_first_interruption(
        tmp_path: Path) -> None:
    """Contract section 2's matched pair, at miniature size.

    Both arms carry `k_max = k_Z = 40` and the same host master seed and learner
    seed, so the two runs can only part at the first step whose D2 sampled masks
    differ - the first interruption the finite `c` produces that infinite `c` does
    not.  Everything strictly before that step must be identical.
    """
    root = tmp_path / "study"
    d0 = dict(e2.arm_parameters("d0_k40"))
    d2 = dict(e2.arm_parameters("d2_c2p0"))
    assert d0["skill_cap_k_max"] == d2["skill_cap_k_max"] == 40
    assert d0["interruption_cost_c"] == INF and d2["interruption_cost_c"] == 2.0

    _mini_rollout1(tmp_path, root / "d0_k40_seed1", d0, "d0")
    _mini_rollout1(tmp_path, root / "d2_c2p0_seed1", d2, "d2")

    check = agg.matched_pair_check(root, 1)
    assert check["available"] is True
    assert check["pair"] == ["d0_k40", "d2_c2p0"]
    assert check["all_identical_before_first_interruption"] is True
    assert all(check["identical_before_first_interruption"].values())


def test_a_small_cost_does_diverge_and_the_prefix_is_still_identical(
        tmp_path: Path) -> None:
    """The same property with a cost small enough that a divergence certainly exists."""
    root = tmp_path / "study_small_c"
    d0 = dict(e2.arm_parameters("d0_k40"))
    small = dict(d0)
    small["interruption_cost_c"] = 1e-6
    small["interruption_cost_c_Z"] = INF

    _mini_rollout1(tmp_path, root / "d0_k40_seed1", d0, "d0s")
    _mini_rollout1(tmp_path, root / "d2_c2p0_seed1", small, "d2s")

    check = agg.matched_pair_check(root, 1)
    assert check["available"] is True
    assert check["first_divergent_step"] is not None
    assert check["first_divergent_step"] >= 1  # step 0 is the forced reset in both arms
    assert check["all_identical_before_first_interruption"] is True


def test_d0_never_produces_a_gap_boundary_cause(tmp_path: Path) -> None:
    """`c = inf` permits no policy switch before the cap (ADR 01 invariant 3)."""
    driver = _mini_driver(tmp_path, "d0inv", dict(e2.arm_parameters("d0_k40")))
    recorder = e2.DriverRecorder(driver)
    driver.run_rollout(update=False)
    causes = recorder.stacked()["agent_cause"]
    assert not np.any(causes == e2.CAUSE_GAP)
    assert not np.any(recorder.stacked()["team_cause"] == e2.CAUSE_TEAM_GAP)


# ---------------------------------------------------------------------------
# the miniature end-to-end run
# ---------------------------------------------------------------------------


def test_runner_end_to_end_writes_every_contract_artifact(tmp_path: Path,
                                                          monkeypatch) -> None:
    monkeypatch.setattr(e2, "HOST_POINT", dict(MINI_HOST))
    root = tmp_path / "E2_mini"
    code = e2.main([
        "--arm", "d0_k20", "--seed", "1", "--rollouts", "1",
        "--num-envs", "2", "--threads", "1",
        "--output-root", str(root), "--launch-commit", "deadbeef",
        "--eval-interval", "1", "--eval-tape-set", "8", "--eval-episodes", "8",
        "--eval-intermediate-episodes", "8", "--eval-chunk", "4",
        "--eval-master-seed", "770001",
    ])
    assert code == 0
    run_dir = root / "d0_k20_seed1"
    assert not (run_dir / "QUARANTINED").exists()
    for name in ("manifest.json", "preflight.json", "metrics.jsonl", "eval.jsonl",
                 "interruptions.jsonl", "gaps.jsonl", "summary.json",
                 "checkpoint_final.pt", "rollout1_match.npz"):
        assert (run_dir / name).exists(), name

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["launch_commit"] == "deadbeef"
    assert manifest["arm"] == "d0_k20"
    assert manifest["arm_parameters"]["interruption_cost_c"] == "Infinity"
    assert manifest["arm_parameters"]["skill_cap_k_max"] == 20
    # the host point is recorded
    assert manifest["host_point"]["H"] == MINI_HOST["horizon"]
    assert manifest["host_point"]["lambda_regions"] == [0.02, 0.02]
    # the exact references are recorded, from `enumerate_references`
    references = manifest["references"]
    for key in ("J_switch", "J_fixed_k", "best_fixed_k", "J_best_fixed_k", "m", "m_dur"):
        assert key in references
    expected = enumerate_references(RelayCorridorConfig(**MINI_HOST)).as_dict()
    assert references["J_switch"] == pytest.approx(expected["J_switch"])
    assert sorted(int(k) for k in references["J_fixed_k"]) == sorted(MINI_HOST["d0_k_set"])
    # the matched evaluation tapes are recorded with a digest
    tapes = manifest["evaluation"]["tapes"]
    assert tapes["episodes"] == 8
    assert len(tapes["content_sha256"]) == 64
    assert manifest["evaluation"]["master_seed"] == 770001

    evaluations = [json.loads(line) for line in
                   (run_dir / "eval.jsonl").read_text(encoding="utf-8").splitlines()
                   if line.strip()]
    assert len(evaluations) == 1
    evaluation = evaluations[0]
    assert evaluation["episodes"] == 8
    assert evaluation["final_checkpoint"] is True
    assert 0.0 <= evaluation["return_mean"] <= MINI_HOST["delta"]
    assert evaluation["gap_to_J_switch"] == pytest.approx(
        evaluation["J_switch"] - evaluation["return_mean"])
    assert (evaluation["regime_low_events"]["episodes"]
            + evaluation["regime_high_events"]["episodes"]) == 8

    interruptions = [json.loads(line) for line in
                     (run_dir / "interruptions.jsonl").read_text(
                         encoding="utf-8").splitlines() if line.strip()]
    assert len(interruptions) == 1
    assert interruptions[0]["event_alignment"]["interruptions"] > 0
    gaps = [json.loads(line) for line in
            (run_dir / "gaps.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    assert len(gaps) == 1
    assert gaps[0]["gap_agent"]["count"] > 0

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["completed"] is True
    assert summary["rollouts_completed"] == 1
    assert summary["final_evaluation_return_mean"] is not None
    assert summary["references"]["best_fixed_k"] in MINI_HOST["d0_k_set"]


def test_tape_set_is_matched_across_arms_and_the_digest_is_stable() -> None:
    corridor = RelayCorridorConfig(**MINI_HOST)
    a = e2.tape_digest_and_events(corridor, 770001, 8, 4)
    b = e2.tape_digest_and_events(corridor, 770001, 8, 4)
    c = e2.tape_digest_and_events(corridor, 770002, 8, 4)
    assert a["content_sha256"] == b["content_sha256"]
    assert a["content_sha256"] != c["content_sha256"]
    assert np.array_equal(a["event_counts"], b["event_counts"])
    assert a["event_counts"].shape == (8,)
    assert a["event_counts"].min() >= 0


# ---------------------------------------------------------------------------
# 6. contract section 5's reading rule, on synthetic summaries
# ---------------------------------------------------------------------------


REFERENCES = {
    "J_switch": 0.39202,
    "J_fixed_k": {1: 0.001, 2: 0.197, 5: 0.3053168128,
                  20: 0.3133920282449043, 40: 0.2681497980245237},
    "best_fixed_k": 20,
    "J_best_fixed_k": 0.3133920282449043,
}


def _synthetic(d0_by_seed, d2_by_seed, alignment_by_seed, segment_by_seed) -> dict:
    return {
        seed: {
            "d0": d0_by_seed[seed],
            "d2": d2_by_seed[seed],
            "alignment": alignment_by_seed[seed],
            "segment_mean": segment_by_seed[seed],
        } for seed in d0_by_seed
    }


def test_reading_rule_mechanism_a_branch() -> None:
    """Some `c` reaches `R_best0 - s` in both seeds, aligned, segments rise with `c`."""
    d0 = {1: {1: 0.10, 2: 0.12, 5: 0.20, 20: 0.24, 40: 0.21},
          2: {1: 0.10, 2: 0.12, 5: 0.20, 20: 0.25, 40: 0.21}}
    d2 = {1: {0.25: 0.10, 0.5: 0.20, 1.0: 0.26, 2.0: 0.22},
          2: {0.25: 0.11, 0.5: 0.21, 1.0: 0.27, 2.0: 0.23}}
    alignment = {1: {0.25: 0.30, 0.5: 0.55, 1.0: 0.80, 2.0: 0.90},
                 2: {0.25: 0.31, 0.5: 0.56, 1.0: 0.82, 2.0: 0.91}}
    segments = {1: {0.25: 2.0, 0.5: 5.0, 1.0: 12.0, 2.0: 25.0},
                2: {0.25: 2.1, 0.5: 5.2, 1.0: 12.5, 2.0: 26.0}}
    out = agg.apply_reading_rule(
        _synthetic(d0, d2, alignment, segments), REFERENCES)
    assert out["verdict"] == "mechanism_A_supported"
    assert out["mechanism_A_supported"] is True
    assert out["mechanism_B_supported"] is False
    assert 1.0 in out["c_satisfying_return_and_alignment"]
    assert out["segment_mean_monotone_in_c_both_seeds"] is True
    assert out["d2_pays_for_a_reason_other_than_event_alignment"] is False
    assert out["d0_sanity_disagrees_at_the_top"] is False
    # the reviewer's clauses are scored separately and both hold here
    reviewer = out["reviewer_numerical_prediction"]
    assert reviewer["best_c_by_seed_mean"] == 1.0
    assert reviewer["clause_1_best_c_in_0p5_to_1p0"] is True
    assert reviewer["clause_2_alignment_above_half_at_best_c"] is True


def test_reading_rule_mechanism_b_branch() -> None:
    """No `c` reaches `R_best0 - s` in either seed and nothing is aligned."""
    d0 = {1: {1: 0.10, 2: 0.12, 5: 0.20, 20: 0.30, 40: 0.21},
          2: {1: 0.10, 2: 0.12, 5: 0.20, 20: 0.301, 40: 0.21}}
    d2 = {1: {0.25: 0.05, 0.5: 0.06, 1.0: 0.07, 2.0: 0.08},
          2: {0.25: 0.05, 0.5: 0.06, 1.0: 0.07, 2.0: 0.081}}
    alignment = {1: {0.25: 0.10, 0.5: 0.12, 1.0: 0.14, 2.0: 0.16},
                 2: {0.25: 0.11, 0.5: 0.13, 1.0: 0.15, 2.0: 0.17}}
    segments = {1: {0.25: 2.0, 0.5: 5.0, 1.0: 12.0, 2.0: 25.0},
                2: {0.25: 2.1, 0.5: 5.2, 1.0: 12.5, 2.0: 26.0}}
    out = agg.apply_reading_rule(
        _synthetic(d0, d2, alignment, segments), REFERENCES)
    assert out["verdict"] == "mechanism_B_supported"
    assert out["mechanism_B_supported"] is True
    assert out["mechanism_A_supported"] is False
    assert out["c_satisfying_return_condition_both_seeds"] == []
    reviewer = out["reviewer_numerical_prediction"]
    assert reviewer["best_c_by_seed_mean"] == 2.0
    assert reviewer["clause_1_best_c_in_0p5_to_1p0"] is False
    assert reviewer["clause_2_alignment_above_half_at_best_c"] is False


def test_reading_rule_neither_branch_when_return_holds_but_alignment_does_not() -> None:
    """The named `neither` sub-case: "D2 pays for a reason other than event alignment"."""
    d0 = {1: {1: 0.10, 2: 0.12, 5: 0.20, 20: 0.24, 40: 0.21},
          2: {1: 0.10, 2: 0.12, 5: 0.20, 20: 0.25, 40: 0.21}}
    d2 = {1: {0.25: 0.10, 0.5: 0.20, 1.0: 0.26, 2.0: 0.22},
          2: {0.25: 0.11, 0.5: 0.21, 1.0: 0.27, 2.0: 0.23}}
    alignment = {1: {0.25: 0.10, 0.5: 0.12, 1.0: 0.20, 2.0: 0.30},
                 2: {0.25: 0.11, 0.5: 0.13, 1.0: 0.21, 2.0: 0.31}}
    segments = {1: {0.25: 2.0, 0.5: 5.0, 1.0: 12.0, 2.0: 25.0},
                2: {0.25: 2.1, 0.5: 5.2, 1.0: 12.5, 2.0: 26.0}}
    out = agg.apply_reading_rule(
        _synthetic(d0, d2, alignment, segments), REFERENCES)
    assert out["verdict"] == "neither"
    assert out["mechanism_A_supported"] is False
    assert out["mechanism_B_supported"] is False
    assert out["c_satisfying_return_condition_both_seeds"] != []
    assert out["c_satisfying_return_and_alignment"] == []
    assert out["d2_pays_for_a_reason_other_than_event_alignment"] is True


def test_reading_rule_neither_branch_when_segments_do_not_rise_with_c() -> None:
    """Returns and alignment both hold, but the monotonicity clause fails."""
    d0 = {1: {20: 0.24}, 2: {20: 0.25}}
    d2 = {1: {0.25: 0.10, 0.5: 0.20, 1.0: 0.26, 2.0: 0.22},
          2: {0.25: 0.11, 0.5: 0.21, 1.0: 0.27, 2.0: 0.23}}
    alignment = {1: {0.25: 0.60, 0.5: 0.70, 1.0: 0.80, 2.0: 0.90},
                 2: {0.25: 0.61, 0.5: 0.71, 1.0: 0.82, 2.0: 0.91}}
    segments = {1: {0.25: 20.0, 0.5: 5.0, 1.0: 12.0, 2.0: 25.0},   # not monotone
                2: {0.25: 2.1, 0.5: 5.2, 1.0: 12.5, 2.0: 26.0}}
    out = agg.apply_reading_rule(
        _synthetic(d0, d2, alignment, segments), REFERENCES)
    assert out["segment_mean_monotone_in_c_per_seed"]["1"] is False
    assert out["segment_mean_monotone_in_c_both_seeds"] is False
    assert out["mechanism_A_supported"] is False
    assert out["verdict"] == "neither"


def test_reading_rule_neither_branch_when_one_seed_only() -> None:
    """`in both seeds` is literal: one seed satisfying the return condition is not enough."""
    # `s` comes from the D0 across-seed range (0.30), which is wide enough for seed 2
    # (whose own `R_best0` is low) and not for seed 1.
    d0 = {1: {20: 0.50}, 2: {20: 0.20}}
    d2 = {1: {c: 0.10 for c in e2.D2_C_SET}, 2: {c: 0.10 for c in e2.D2_C_SET}}
    alignment = {1: {c: 0.9 for c in e2.D2_C_SET}, 2: {c: 0.9 for c in e2.D2_C_SET}}
    segments = {1: {0.25: 1.0, 0.5: 2.0, 1.0: 3.0, 2.0: 4.0},
                2: {0.25: 1.0, 0.5: 2.0, 1.0: 3.0, 2.0: 4.0}}
    out = agg.apply_reading_rule(
        _synthetic(d0, d2, alignment, segments), REFERENCES)
    row = out["per_c"]["1.0"]
    assert row["return_condition_per_seed"]["2"] is True
    assert row["return_condition_per_seed"]["1"] is False
    assert row["return_condition_both_seeds"] is False
    assert row["return_condition_any_seed"] is True
    # mechanism B also fails: some `c` reached the bar in *some* seed
    assert out["c_satisfying_return_condition_both_seeds"] == []
    assert out["mechanism_A_supported"] is False
    assert out["mechanism_B_supported"] is False
    assert out["verdict"] == "neither"
    assert out["d2_pays_for_a_reason_other_than_event_alignment"] is False


def test_reading_rule_d0_sanity_check_flags_a_disagreement_at_the_top() -> None:
    """The learner's best `k` is neither `k*` nor a reference-adjacent neighbour."""
    d0 = {1: {1: 0.40, 2: 0.12, 5: 0.20, 20: 0.24, 40: 0.21},
          2: {1: 0.41, 2: 0.12, 5: 0.20, 20: 0.25, 40: 0.21}}
    d2 = {1: {c: 0.01 for c in e2.D2_C_SET}, 2: {c: 0.01 for c in e2.D2_C_SET}}
    alignment = {1: {c: 0.1 for c in e2.D2_C_SET}, 2: {c: 0.1 for c in e2.D2_C_SET}}
    segments = {1: {c: 1.0 for c in e2.D2_C_SET}, 2: {c: 1.0 for c in e2.D2_C_SET}}
    out = agg.apply_reading_rule(
        _synthetic(d0, d2, alignment, segments), REFERENCES)
    sanity = out["d0_sanity_check"]["1"]
    assert sanity["learner_best_k"] == 1
    assert sanity["reference_best_k"] == 20
    assert sanity["agrees_reference_ordering"] is False
    assert sanity["agrees_grid_adjacency"] is False
    assert out["d0_sanity_disagrees_at_the_top"] is True
    # and the reference ordering itself is the J ordering, best first
    assert sanity["reference_ordering"] == [20, 5, 40, 2, 1]


def test_reading_rule_d0_sanity_accepts_the_reference_adjacent_neighbour() -> None:
    d0 = {1: {1: 0.10, 2: 0.12, 5: 0.30, 20: 0.24, 40: 0.21},
          2: {1: 0.10, 2: 0.12, 5: 0.31, 20: 0.25, 40: 0.21}}
    d2 = {1: {c: 0.01 for c in e2.D2_C_SET}, 2: {c: 0.01 for c in e2.D2_C_SET}}
    alignment = {1: {c: 0.1 for c in e2.D2_C_SET}, 2: {c: 0.1 for c in e2.D2_C_SET}}
    segments = {1: {c: 1.0 for c in e2.D2_C_SET}, 2: {c: 1.0 for c in e2.D2_C_SET}}
    out = agg.apply_reading_rule(
        _synthetic(d0, d2, alignment, segments), REFERENCES)
    sanity = out["d0_sanity_check"]["1"]
    assert sanity["learner_best_k"] == 5
    assert sanity["agrees_reference_ordering"] is True
    assert sanity["agrees_grid_adjacency"] is True
    assert out["d0_sanity_disagrees_at_the_top"] is False


def test_reading_rule_s_is_the_larger_of_the_two_across_seed_ranges() -> None:
    d0 = {1: {20: 0.20}, 2: {20: 0.40}}          # across-seed range 0.20
    d2 = {1: {c: 0.10 for c in e2.D2_C_SET},     # across-seed range 0.00
          2: {c: 0.10 for c in e2.D2_C_SET}}
    alignment = {1: {c: 0.9 for c in e2.D2_C_SET}, 2: {c: 0.9 for c in e2.D2_C_SET}}
    segments = {1: {0.25: 1.0, 0.5: 2.0, 1.0: 3.0, 2.0: 4.0},
                2: {0.25: 1.0, 0.5: 2.0, 1.0: 3.0, 2.0: 4.0}}
    out = agg.apply_reading_rule(
        _synthetic(d0, d2, alignment, segments), REFERENCES)
    row = out["per_c"]["1.0"]
    assert row["across_seed_range_R_best0"] == pytest.approx(0.20)
    assert row["across_seed_range_R_c"] == pytest.approx(0.0)
    assert row["s"] == pytest.approx(0.20)
    # seed 1: 0.10 >= 0.20 - 0.20 = 0.00 True; seed 2: 0.10 >= 0.40 - 0.20 = 0.20 False
    assert row["return_condition_per_seed"]["1"] is True
    assert row["return_condition_per_seed"]["2"] is False


def test_queue_order_and_drop_rule() -> None:
    import run_flexible_skill_duration_e2_queue as queue

    full = queue.build_queue((1, 2), drop_outer_seed2=False)
    assert len(full) == 18
    assert full[:4] == [("d0_k40", 1), ("d0_k40", 2), ("d2_c1p0", 1), ("d2_c1p0", 2)]
    assert full[0][0] == "d0_k40" and full[2][0] == "d2_c1p0"
    dropped = queue.build_queue((1, 2), drop_outer_seed2=True)
    assert len(dropped) == 14
    assert all(not (arm in e2.OUTER_ARMS and seed == 2) for arm, seed in dropped)
    # the central pair survives the drop rule in both seeds
    for arm in e2.MATCHED_PAIR:
        assert (arm, 1) in dropped and (arm, 2) in dropped


def test_aggregate_end_to_end_on_synthetic_run_directories(tmp_path: Path) -> None:
    """`build_summary` reads run directories and skips quarantined ones."""
    root = tmp_path / "study"
    root.mkdir()
    for arm in ("d0_k20", "d2_c1p0"):
        for seed in (1, 2):
            run_dir = root / f"{arm}_seed{seed}"
            run_dir.mkdir()
            (run_dir / "summary.json").write_text(json.dumps({
                "arm": arm, "seed": seed, "completed": True, "timing_only": False,
                "references": REFERENCES,
                "rollouts_completed": 20,
                "final_evaluation_return_mean": 0.2 + 0.01 * seed,
                "final_evaluation_return_stderr": 0.001,
                "final_interruption_record": {
                    "interruption_rate_per_agent_step": 0.05,
                    "event_alignment": {"aligned_fraction": 0.7,
                                        "aligned_fraction_strict": 0.4},
                    "event_alignment_gap_caused_only": {"aligned_fraction": 0.9},
                    "segment_length_agent": {"mean": 12.0},
                    "segment_length_team": {"mean": 15.0},
                    "fraction_closed_by_cap": 0.2,
                    "fraction_closed_by_gap": 0.7,
                    "team_switch_rate_gap_per_env_step": 0.03,
                },
            }), encoding="utf-8")
    quarantined = root / "d0_k1_seed1"
    quarantined.mkdir()
    (quarantined / "summary.json").write_text(json.dumps(
        {"arm": "d0_k1", "seed": 1, "completed": False, "timing_only": False,
         "references": REFERENCES}), encoding="utf-8")
    (quarantined / "QUARANTINED").write_text("incomplete", encoding="utf-8")

    summary = agg.build_summary(root)
    assert summary["runs_loaded"] == 4
    assert any(row["reason"] == "QUARANTINED" for row in summary["runs_skipped"])
    assert summary["seeds"] == [1, 2]
    assert summary["reading_rule"] is not None
    present = {(row["arm"], row["seed"]) for row in summary["per_run"] if row["present"]}
    assert ("d0_k20", 1) in present and ("d2_c1p0", 2) in present
    # every arm of the contract table appears in the per-run table, present or not
    assert len(summary["per_run"]) == 9 * 2


def test_jsonable_round_trips_the_infinite_cost() -> None:
    """`c = inf` must survive the manifest as a readable value, not a crash."""
    payload = e2._jsonable(e2.arm_parameters("d0_k40"))
    assert payload["interruption_cost_c"] == "Infinity"
    assert json.loads(json.dumps(payload))["interruption_cost_c_Z"] == "Infinity"
    assert math.isinf(e2.ARMS["d0_k40"]["c"])
