"""Real tiny-host executions of the commitment-visibility probe.

Two lanes, twenty-step episodes, the real Scenario 1 environment and the real D agent, through the
frozen runner's own learner construction, evaluator construction and evaluation panel; then B08's
real checkpoint, B08's real `load_model`, and B11's own collection of the frozen collector's
per-step calls on the real D2 route with this object's caps set on the learner instance. The tiny
fit and the tiny harness are B08's own test fixtures, loaded by path, because this object probes
B08's checkpoints and is read against B09's and B10's panels, and all of them must be checked
against one panel and not against copies of it. Technical checks, no result: nothing here asserts
the direction or the size of any measured quantity.
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

_SPEC = importlib.util.spec_from_file_location(
    "fsd_commitment_visibility_b08_tiny",
    Path(__file__).parents[1] / "label_content_b08/test_label_content_real_tiny.py")
b08tiny = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(b08tiny)

import run_fsd_commitment_visibility_b12 as b12  # noqa: E402
import run_fsd_coordinator_signal_b11 as b11  # noqa: E402
import run_fsd_label_content_b08 as b08  # noqa: E402

shrunken = b08tiny.shrunken
build_harness = b08tiny.build_harness
point_at_the_tiny_fit = b08tiny.point_at_the_tiny_fit
SEED, EVALUATION_SEED = b08tiny.SEED, b08tiny.EVALUATION_SEED
LANES, HORIZON = b08tiny.LANES, b08tiny.HORIZON
N_UAVS, N_z, SKILL_PERIOD = b08tiny.N_UAVS, b08tiny.N_z, b08tiny.SKILL_PERIOD
# The tiny host's own caps: the frozen ten-step cadence and one commitment for the whole episode,
# which is the cap the non-additivity block is defined on. The production caps are (10, 50, 100, 500).
CAPS = (SKILL_PERIOD, b12.NON_ADDITIVITY_CAP)
ROLLOUTS_PER_CAP = 4


@pytest.fixture
def tiny():
    with shrunken() as shared:
        yield shared


@pytest.fixture(scope="module")
def tiny_fit(tmp_path_factory):
    """B08's own tiny fit, run once: its summary, its output root and its checkpoint."""
    out = tmp_path_factory.mktemp("commitment_visibility_fit")
    with shrunken():
        assert b08.run_fit(b08.SAVE_ARM, SEED, out, admission=b08tiny.ADMISSION) == 0
    return json.loads((out / "summary.json").read_text()), out


@pytest.fixture
def harness(tmp_path, tiny, tiny_fit):
    """B08's probe harness: its learner with the checkpoint loaded, and its evaluator."""
    _fit_summary, fit_out = tiny_fit
    summary, learner, evaluator = build_harness(tmp_path / "harness",
                                                fit_out / b08.WEIGHTS_NAME)
    out = tmp_path / "harness"
    return summary, learner, evaluator, out


def collection_envs(seed=SEED):
    return b11.shared.e0._make_envs(LANES, b11.world_base_seed(seed), N_UAVS,
                                    b11.shared.N_USERS, HORIZON)


def capped_collection(learner, summary, out, cap, *, rollouts=1, seed=SEED, tape=None):
    """One cap's collection on a built harness: B11's loop, this object's caps and seeds."""
    frames, commitments = [], []

    def measure(rollout, states, observations):
        frame = b11.rollout_frame(learner, HORIZON, states.copy(), observations.copy(),
                                  rollout, LANES)
        if tape is not None:
            commitments.append(b12.commitment_frame(
                frame, tape.rollout(rollout, HORIZON), cap=cap,
                gamma=float(learner.config.gamma), horizon=HORIZON))
        return frame, {"commitment_cap": int(cap), "rows_M": frame["rows_M"]}

    envs = collection_envs(seed)
    with b11.shared.e0._preserve_rng():
        managers = [b12.commitment_cap(learner, cap), b12.b11_collection_seed_bound(cap)]
        if tape is not None:
            tape.envs = list(envs)
            tape.rewards = [[] for _ in envs]
            managers.append(tape.attached())
        entered = []
        try:
            for manager in managers:
                manager.__enter__()
                entered.append(manager)
            frames.extend(b11.collect_training_law(
                envs, learner, summary, out, rollouts=rollouts, training_seed=seed,
                measure=measure))
        finally:
            for manager in reversed(entered):
                manager.__exit__(None, None, None)
    return frames, commitments


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def test_the_probe_runs_one_capped_collection_per_cap_and_takes_no_step(
        tmp_path, tiny, tiny_fit, monkeypatch):
    fit_summary, fit_out = tiny_fit
    point_at_the_tiny_fit(monkeypatch, fit_out / "summary.json")
    out = tmp_path / "probe"
    head = b11.shared.e0._git("rev-parse", "HEAD")
    assert b12.main(["probe", "--seed", str(SEED), "--weights",
                     str(fit_out / b08.WEIGHTS_NAME), "--launch-sha", head,
                     "--output-root", str(out), "--caps", *[str(cap) for cap in CAPS],
                     "--rollouts-per-cap", str(ROLLOUTS_PER_CAP)]) == 0
    summary = json.loads((out / "summary.json").read_text())

    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == b12.OBJECT_ID and summary["command"] == "probe"
    assert summary["card"] == b12.CARD and "B12" in summary["card"]
    assert summary["block_seed"] == SEED and summary["evaluation_seed"] == EVALUATION_SEED
    assert summary["launch_sha"] == head == summary["requested_launch_sha"]
    assert summary["caps"] == list(CAPS) and summary["rollouts_per_cap"] == ROLLOUTS_PER_CAP
    assert summary["frozen_cap"] == SKILL_PERIOD

    # the probe takes no optimizer step and moves no parameter or running statistic
    assert summary["optimizer_steps"] == 0 and not any(summary["optimizer_calls"].values())
    state = summary["learner_state"]
    assert state["unchanged"] is True
    assert state["before"]["parameter_digest"] == state["after"]["parameter_digest"]
    assert state["before"]["value_norm_coordinator"] == state["after"]["value_norm_coordinator"]
    assert state["before"]["value_norm_discoverer"] == state["after"]["value_norm_discoverer"]
    assert summary["collection_rng"]["restored"] is True

    # the construction is the frozen caps-10 one, and the probe records what it moved
    caps = summary["construction_caps"]
    assert (caps["d2_k_max"], caps["d2_k_Z"]) == b08.ARM_CAPS
    assert (caps["skill_cap_k_max"], caps["team_cap_k_Z"]) == b08.ARM_CAPS
    assert caps["interruption_cost_c"] == caps["interruption_cost_c_Z"] == "inf"
    assert caps["age_feature"] == "off"
    assert "hmasd/agent.py:2596" in caps["definition"]

    # the frozen panel and the faithful-load check B09 does not relax
    faithful = summary["faithful_load"]
    assert faithful["faithful_load"] is True and faithful["first_differing_world"] is None
    final_panel = [p for p in fit_summary["panels"]
                   if p["panel_rollouts"] == b08tiny.ROLLOUTS][0]
    assert summary["as_trained_world_scores"] == final_panel["native_scores_J"]
    assert summary["weights_record"]["sha256"] == fit_summary["final_weights"]["sha256"]
    assert summary["evaluation_panels"] == 1

    # one collection per cap, at the cadence the cap implies
    assert summary["collection_transitions"] == LANES * HORIZON * ROLLOUTS_PER_CAP * len(CAPS)
    assert summary["collection_episodes"] == LANES * ROLLOUTS_PER_CAP * len(CAPS)
    assert summary["rollouts_collected"] == {str(cap): ROLLOUTS_PER_CAP for cap in CAPS}
    assert len(summary["collection_geometry"]) == len(CAPS) * ROLLOUTS_PER_CAP
    lines = (out / "construction" / "collection.jsonl").read_text().strip().splitlines()
    assert len(lines) == len(CAPS) * ROLLOUTS_PER_CAP
    assert [json.loads(line)["commitment_cap"] for line in lines] == (
        [CAPS[0]] * ROLLOUTS_PER_CAP + [CAPS[1]] * ROLLOUTS_PER_CAP)

    for record in summary["collection_geometry"]:
        cap = record["cap"]
        commitments = math.ceil(HORIZON / cap)
        assert record["rows_M_team"] == record["rows_M"] == LANES * commitments
        assert record["rows_M_agent"] == LANES * commitments * N_UAVS
        assert record["expected_rows_M_team"] == LANES * commitments
        assert record["commitments_per_lane_episode"] == commitments
        assert record["flushed_open_segments"] == 0  # every lane ends terminal
        assert record["cause_counts"]["reset"] == LANES
        assert record["cause_counts"]["team_cap"] == LANES * (commitments - 1)
        assert not any(record["cause_counts"][name] for name in ("team_gap", "gap", "cap"))
        assert record["segment_length_team_mean"] == pytest.approx(HORIZON / commitments)
        assert record["mean_commitment_elapsed"] == pytest.approx(HORIZON / commitments)

    for row in summary["collection_rows"]:
        cap = row["commitment_cap"]
        assert row["collection_seed"] == b12.collection_seed(SEED, cap, row["rollout_index"])
        assert row["completed_episodes"] == LANES
        assert row["discounted_reward_agreement"] < b12.DISCOUNTED_AGREEMENT_TOLERANCE
        assert not any(row["optimizer_calls_total"].values())

    # the measures: one block per cap, both responses, the placebo, and the cap-500 extras
    assert sorted(summary["measures"]) == sorted(str(cap) for cap in CAPS)
    for cap in CAPS:
        block = summary["measures"][str(cap)]
        commitments = math.ceil(HORIZON / cap)
        assert block["cap"] == cap and block["rollouts"] == ROLLOUTS_PER_CAP
        assert block["lane_episodes"] == LANES * ROLLOUTS_PER_CAP
        assert block["commitments"] == LANES * ROLLOUTS_PER_CAP * commitments
        assert block["commitments_per_lane_episode"] == commitments
        assert block["clusters"] == LANES * ROLLOUTS_PER_CAP
        assert block["team_rows"] == block["commitments"]
        assert block["agent_rows"] == block["commitments"] * N_UAVS
        assert block["discounted_reward_agreement"]["max_absolute_difference"] < 1e-5
        assert block["behaviour"]["lane_episodes"] == LANES * ROLLOUTS_PER_CAP
        assert block["behaviour"]["mean_episode_J"] == pytest.approx(
            block["behaviour"]["mean_episode_return_U"] * N_UAVS / HORIZON)
        assert block["label_law"]["uniform_entropy"] == pytest.approx(float(np.log(N_z)))
        assert sorted(block["secondary_agent_advantage"]["agent_label_table"]) == [
            str(label) for label in range(N_z)]
        assert "arithmetic" in block["secondary_agent_advantage"]["reading_note"]
        assert block["wall_seconds"] > 0.
        for response in b12.RESPONSES:
            entry = block["responses"][response]
            regression = entry["agent_label_regression"]
            assert regression["segments"] == block["commitments"]
            assert regression["positions"] == commitments
            assert regression["clusters"] == block["clusters"]
            assert sorted(regression["centred_coefficients"]) == [
                str(label) for label in range(N_z)]
            assert sum(regression["centred_coefficients"].values()) == pytest.approx(0., abs=1e-9)
            assert entry["agent_label_permutation"]["permutations"] == b12.PERMUTATIONS
            assert entry["agent_label_permutation"]["identity_check"] == pytest.approx(
                regression["max_minus_min"], abs=1e-12)
            assert entry["placebo_regression"]["segments"] == block["commitments"]
            assert entry["placebo_permutation"]["permutations"] == b12.PERMUTATIONS
            assert entry["centred_coefficient_drop_invariance"][
                "max_absolute_difference"] < 1e-6
            assert ("non_additivity" in entry) == (cap == b12.NON_ADDITIVITY_CAP)
            if cap == b12.NON_ADDITIVITY_CAP:
                assert entry["non_additivity"]["model"]["extra"]["name"].startswith("sum_c n_c^2")
                assert (entry["all_equal_prediction"]["episode_J_by_label"] is not None) == (
                    response == b12.UNDISCOUNTED)

    assert summary["reporting_factor"] == pytest.approx(N_UAVS / HORIZON)
    assert "run_fsd_baseline_interruption_b01.py:254" in summary["reporting_factor_note"]
    assert summary["coordinator_training_mode"] is False  # put back after the collection
    assert (out / "construction" / "summary.json").exists()
    assert "wsl_4070" in summary["interpretation_limit"]
    assert summary["wall_seconds"] > 0.


def test_an_unfaithful_load_stops_the_probe_before_any_collection(tmp_path, tiny, tiny_fit,
                                                                  monkeypatch):
    """The reference is a panel this checkpoint cannot reproduce, so nothing is ever collected."""
    _fit_summary, fit_out = tiny_fit
    reference = tmp_path / "reference_summary.json"
    damaged = json.loads((fit_out / "summary.json").read_text())
    for panel in damaged["panels"]:
        panel["native_scores_J"] = [value + 1. for value in panel["native_scores_J"]]
    reference.write_text(json.dumps(damaged), encoding="utf-8")
    point_at_the_tiny_fit(monkeypatch, reference)
    out = tmp_path / "probe"
    assert b12.run_probe(SEED, fit_out / b08.WEIGHTS_NAME, out, caps=CAPS,
                         rollouts_per_cap=1) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["faithful_load"]["faithful_load"] is False
    assert "first differing world index 0" in summary["failure"]
    assert "measures" not in summary and "collection_rows" not in summary


# ---------------------------------------------------------------------------
# the caps on the real D2 route
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cap", [5, SKILL_PERIOD, HORIZON, 500])
def test_the_cap_reaches_the_learners_own_decision_cadence_and_comes_off_again(harness, cap):
    summary, learner, _evaluator, out = harness
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        frames, _commitments = capped_collection(learner, summary, out, cap)
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    frame = frames[0]
    commitments = math.ceil(HORIZON / cap)
    assert frame["rows_M"] == frame["rows_M_team"] == b12.expected_team_rows(LANES, HORIZON, cap)
    assert frame["rows_M"] == LANES * commitments
    assert frame["rows_M_agent"] == frame["rows_M_team"] * N_UAVS
    # every commitment runs for the cap, or to the end of the episode
    starts = np.asarray(frame["team"]["step"])
    assert np.array_equal(np.asarray(frame["team"]["elapsed"]),
                          np.minimum(cap, HORIZON - starts))
    assert sorted(set(starts.tolist())) == list(range(0, HORIZON, cap))
    # the six agent segments renew with the team commitment, at the same start and elapsed
    assert np.array_equal(np.asarray(frame["agent"]["elapsed"]).reshape(-1, N_UAVS),
                          np.repeat(np.asarray(frame["team"]["elapsed"])[:, None], N_UAVS, axis=1))
    assert np.array_equal(np.asarray(frame["agent"]["step"]).reshape(-1, N_UAVS),
                          np.repeat(starts[:, None], N_UAVS, axis=1))
    assert frame["team"]["counts"].sum(axis=1).tolist() == [float(N_UAVS)] * frame["rows_M"]
    assert frame["team"]["terminal"].sum() == LANES  # one terminal commitment per lane-episode
    # and the caps are the frozen fit's again
    assert (learner.d2_k_max, learner.d2_k_Z) == b08.ARM_CAPS
    assert "_batched_assign_skills" not in learner.__dict__  # this object wraps no agent callable


def test_a_failure_inside_a_capped_collection_leaves_the_frozen_caps_behind(harness):
    summary, learner, _evaluator, out = harness

    def explode(*_args, **_kwargs):
        raise RuntimeError("the measure failed")

    envs = collection_envs()
    tape = b12.RewardTape(envs)
    with pytest.raises(RuntimeError, match="the measure failed"):
        with b11.shared.e0._preserve_rng():
            with b12.commitment_cap(learner, 500), b12.b11_collection_seed_bound(500), \
                    tape.attached():
                assert (learner.d2_k_max, learner.d2_k_Z) == (500, 500)
                b11.collect_training_law(envs, learner, summary, out, rollouts=1,
                                         training_seed=SEED, measure=explode)
    assert (learner.d2_k_max, learner.d2_k_Z) == b08.ARM_CAPS
    assert b11.collection_seed(SEED, 0) != b12.collection_seed(SEED, 500, 0)
    assert not any("step" in env.__dict__ for env in envs)  # the tape came off too
    assert tape.calls > 0  # and it really was recording when the failure happened


def test_a_cap_changes_the_collection_the_frozen_cadence_would_have_taken(harness):
    """The two caps are different collections of the same weights, not a relabelling of one."""
    summary, learner, _evaluator, out = harness
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        short, _c = capped_collection(learner, summary, out, SKILL_PERIOD)
        long, _c = capped_collection(learner, summary, out, HORIZON)
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    assert short[0]["rows_M"] == LANES * 2 and long[0]["rows_M"] == LANES
    assert short[0]["team"]["elapsed"].tolist() == [SKILL_PERIOD] * (LANES * 2)
    assert long[0]["team"]["elapsed"].tolist() == [HORIZON] * LANES


# ---------------------------------------------------------------------------
# the responses against an independent recomputation
# ---------------------------------------------------------------------------


def test_the_two_responses_are_the_taped_rewards_own_sums(harness):
    summary, learner, _evaluator, out = harness
    gamma = float(learner.config.gamma)
    tape = b12.RewardTape([])
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        frames, commitments = capped_collection(learner, summary, out, SKILL_PERIOD,
                                                rollouts=2, tape=tape)
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    assert tape.require_shape(2, HORIZON) == 2 * HORIZON
    assert len(commitments) == 2
    for index, (frame, commitment) in enumerate(zip(frames, commitments)):
        rewards = tape.rollout(index, HORIZON)
        # an independent recomputation, straight from the taped per-step rewards
        undiscounted, discounted = [], []
        for row in range(frame["rows_M"]):
            lane = int(frame["team"]["lane"][row])
            start = int(frame["team"]["step"][row])
            length = int(frame["team"]["elapsed"][row])
            window = [float(rewards[start + step, lane]) for step in range(length)]
            undiscounted.append(sum(window) / length)
            discounted.append(sum(gamma ** step * value for step, value in enumerate(window)))
        assert commitment[b12.UNDISCOUNTED].tolist() == pytest.approx(undiscounted)
        assert commitment["discounted_from_tape"].tolist() == pytest.approx(discounted)
        # and the frozen buffer's own discounted segment reward is that same sum, in float32
        assert commitment[b12.DISCOUNTED].tolist() == pytest.approx(discounted, abs=1e-5)
        assert np.array_equal(commitment[b12.DISCOUNTED],
                              np.asarray(frame["team"]["reward"], dtype=np.float64))
        # the undiscounted mean is not the discounted sum: the two responses are different numbers
        assert not np.allclose(commitment[b12.UNDISCOUNTED], commitment[b12.DISCOUNTED])
    # the whole episode's taped reward is the lane's own return
    rewards = tape.rollout(0, HORIZON)
    assert rewards.sum(axis=0).tolist() == pytest.approx(
        summary["training_rows"][0]["episode_returns_U"])


def test_the_collection_moves_no_parameter_and_gives_the_random_streams_back(harness):
    summary, learner, _evaluator, out = harness
    before = b11.learner_state_record(learner)
    rng_before = b11.rng_digest()
    counters = b11.shared.optimizer_counters(learner)
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        for cap in CAPS:
            capped_collection(learner, summary, out, cap)
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    after = b11.learner_state_record(learner)
    assert after["parameter_digest"] == before["parameter_digest"]
    assert after["value_norm_coordinator"] == before["value_norm_coordinator"]
    assert after["value_norm_discoverer"] == before["value_norm_discoverer"]
    assert b11.rng_digest() == rng_before
    assert not any(b11.shared.optimizer_counts(counters).values())
    assert learner.d2_metrics["optimizer_steps"] == 0
    # the buffer is left cleared, exactly as the fit's own loop leaves it
    assert not learner.rollout_buffer.d2_team_valid.any()
    assert not learner.rollout_buffer.d2_agent_valid.any()
