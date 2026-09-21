"""Real tiny-host executions of the label-bandit fit.

Six lanes, thirty-step episodes, two rollouts, the real Scenario 1 environment and the real D
agent, through the frozen runner's own learner construction, evaluator construction, collector
loop, update and evaluation panels, with this object's law on the learner's own skill assignment
and its estimator inside the learner's own `update`.  The tiny host keeps the frozen ten-step
cadence, so a rollout carries `lanes * 3` commitments against the regression's eight columns and
the estimator really runs; only the geometry is shrunken.

Technical checks, no result: nothing here asserts the direction or the size of any measured
quantity.  Kept apart from the synthetic tests in `test_label_bandit.py`.
"""
import hashlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_label_bandit_b13 as bandit  # noqa: E402
import run_fsd_label_map_b09 as b09  # noqa: E402

SEED = sorted(bandit.BLOCKS)[0]
EVALUATION_SEED = bandit.BLOCKS[SEED]
LANES, HORIZON, ROLLOUTS = 6, 30, 2
N_UAVS, N_LABELS, SKILL_PERIOD = 6, bandit.N_LABELS, bandit.SKILL_PERIOD
COMMITMENTS_PER_LANE = HORIZON // bandit.COMMITMENT_CAP  # 3, at the frozen ten-step cadence
PANELS = 2 * ROLLOUTS + N_LABELS  # two panels a boundary, and the six constants at the last
ADMISSION = {"sha": "tiny-technical-check", "command_sha256": "x"}


@contextmanager
def shrunken():
    """The tiny host, applied to the shared module and to this object's own rollout schedule."""
    shared = b01.shared
    saved = {"TRAIN_LANES": shared.TRAIN_LANES, "EVAL_LANES": shared.EVAL_LANES,
             "HORIZON": shared.HORIZON, "PROCESS_START": shared.PROCESS_START}
    mine = {"ROLLOUTS": bandit.ROLLOUTS, "PANEL_ROLLOUTS": bandit.PANEL_ROLLOUTS,
            "LATE_PANELS": bandit.LATE_PANELS}
    shared.TRAIN_LANES = shared.EVAL_LANES = LANES
    shared.HORIZON = HORIZON
    shared.PROCESS_START = shared.time.perf_counter()
    bandit.ROLLOUTS, bandit.PANEL_ROLLOUTS = ROLLOUTS, tuple(range(1, ROLLOUTS + 1))
    bandit.LATE_PANELS = bandit.PANEL_ROLLOUTS
    try:
        yield shared
    finally:
        for name, value in saved.items():
            setattr(shared, name, value)
        for name, value in mine.items():
            setattr(bandit, name, value)


def coordinator_digest(agent):
    """Every byte of the coordinator and of its ValueNorm: what its update would have moved."""
    digest = hashlib.sha256()
    for key, tensor in sorted(agent.skill_coordinator.state_dict().items()):
        digest.update(key.encode("utf-8"))
        digest.update(np.ascontiguousarray(tensor.detach().cpu().numpy()).tobytes())
    norm = getattr(agent, "value_norm_coordinator", None)
    if norm is not None:
        for name in ("mean", "var", "count"):
            value = getattr(norm, name, None)
            if value is not None:
                digest.update(np.ascontiguousarray(np.asarray(
                    value.detach().cpu().numpy() if hasattr(value, "detach") else value)).tobytes())
    return digest.hexdigest()


def run_tiny_fit(arm, out, monkeypatch=None):
    """One tiny fit, with a spy on the learner construction so the coordinator can be weighed."""
    captured = {}
    original = bandit.build_learner

    def spy(fit_arm, summary, fit_out, training_seed):
        envs, agent, theta0, counters = original(fit_arm, summary, fit_out, training_seed)
        captured.update(agent=agent, envs=envs, counters=counters,
                        coordinator_before=coordinator_digest(agent))
        return envs, agent, theta0, counters

    bandit.build_learner = spy
    try:
        status = bandit.run_fit(arm, SEED, out, admission=ADMISSION)
    finally:
        bandit.build_learner = original
    captured["status"] = status
    captured["coordinator_after"] = coordinator_digest(captured["agent"])
    captured["summary"] = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    return captured


@pytest.fixture(scope="module")
def tiny_fits(tmp_path_factory):
    """One tiny fit per arm, run once."""
    results = {}
    for arm in bandit.ARMS:
        out = tmp_path_factory.mktemp(f"label_bandit_{arm.lower()}")
        with shrunken():
            results[arm] = run_tiny_fit(arm, out)
            results[arm]["out"] = out
    return results


@pytest.fixture
def tiny():
    with shrunken() as shared:
        yield shared


# ---------------------------------------------------------------------------
# the fit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("arm", sorted(bandit.ARMS))
def test_a_tiny_fit_completes_on_the_declared_construction_with_the_coordinator_held_still(
        tiny, tiny_fits, arm):
    fit = tiny_fits[arm]
    summary = fit["summary"]
    assert fit["status"] == 0
    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == bandit.OBJECT_ID and summary["card"] == bandit.CARD
    assert summary["label_bandit_object"] == bandit.OBJECT_ID
    assert summary["label_bandit_arm"] == summary["factorial_arm"] == arm
    assert summary["arm"] == "D0" and summary["coordinator_batch_size"] == 1280
    assert summary["block_seed"] == SEED and summary["evaluation_seed"] == EVALUATION_SEED

    # the one declared configuration difference, and nothing else
    declared = summary["declared_config_difference"]
    assert declared["field"] == bandit.DECLARED_FIELD
    assert declared["baseline"] is False and declared["fit"] is True
    assert declared["in_config_snapshot"] is False
    assert declared["recorded_snapshot_differences_from_the_d1280_construction"] == {}
    assert summary["arm_overrides"] == {bandit.DECLARED_FIELD: True}
    for phase in ("learner_config", "evaluation_config"):
        config = summary[phase]
        assert config["policy_interruption_mode"] == "d2"
        assert config["interruption_cost_c"] == config["interruption_cost_c_Z"] == "Infinity"
        assert config["age_feature"] == "off"
        assert (config["skill_cap_k_max"], config["team_cap_k_Z"]) == bandit.ARM_CAPS
        assert config["k"] == SKILL_PERIOD and config["n_z"] == config["n_Z"] == N_LABELS
        recorded = summary[f"{phase}_differences_from_recorded_d1280"]
        assert recorded["available"] is True and recorded["reason"] is None
        # the only differences from the published D1280 fit are the shrunken host's geometry
        assert set(recorded["differences"]) == set(bandit.GEOMETRY_FIELDS)

    # the coordinator took no step and did not move a byte; everything else trained
    calls = summary["optimizer_calls"]
    assert calls["coordinator"] == 0
    assert calls["discoverer_actor"] > 0 and calls["discoverer_critic"] > 0
    assert calls["team_discriminator"] > 0 and calls["individual_discriminator"] > 0
    assert fit["coordinator_after"] == fit["coordinator_before"]
    for row in summary["training_rows"]:
        assert row["optimizer_calls_delta"]["coordinator"] == 0
        assert row["optimizer_calls_delta"]["discoverer_actor"] > 0
        assert row["relative_initialization_displacement"]["coordinator"] == 0.
        assert row["relative_initialization_displacement"]["discoverer_actor"] > 0.
        assert row["relative_initialization_displacement"]["discoverer_critic"] > 0.

    # every wrapper this object attached is off again
    agent = fit["agent"]
    assert "_batched_assign_skills" not in agent.__dict__
    assert "update" not in agent.__dict__
    assert not any("step" in env.__dict__ for env in fit["envs"])
    assert b01.build_learner is bandit._orig_build_learner
    assert b01.evaluate_panel is bandit._orig_evaluate_panel
    assert bandit.shared.base_summary is bandit._orig_base_summary
    assert bandit.CURRENT["arm"] is None and bandit.CURRENT["agent"] is None
    # the coordinator optimizer's own frozen counter is back in place
    assert agent.coordinator_optimizer.step is fit["counters"]["coordinator"]


@pytest.mark.parametrize("arm", sorted(bandit.ARMS))
def test_a_tiny_fit_runs_every_declared_panel_and_keeps_the_frozen_schedule(tiny, tiny_fits, arm):
    summary = tiny_fits[arm]["summary"]
    assert bandit.expected_panels() == PANELS
    assert [p["panel_rollouts"] for p in summary["panels"]] == list(bandit.PANEL_ROLLOUTS)
    assert len(summary["extra_panels"]) == PANELS - len(bandit.PANEL_ROLLOUTS)
    assert len(summary["panel_runs"]) == PANELS
    counts = summary["counts"]
    assert counts["evaluation_episodes"] == LANES * PANELS
    assert counts["evaluation_steps"] == LANES * HORIZON * PANELS
    assert counts["training_transitions"] == LANES * HORIZON * ROLLOUTS

    by_boundary = {}
    for entry in summary["panel_runs"]:
        by_boundary.setdefault(entry["panel_rollouts"], []).append(entry)
    for boundary, entries in by_boundary.items():
        names = [entry["rule"] for entry in entries]
        expected = [name for name, _executed in bandit.panel_names(
            boundary, entries[0]["estimate"]["argmax_beta_hat"])]
        assert names == expected
        assert [entry["schedule_slot"] for entry in entries] == [True] + [False] * (len(names) - 1)
        assert entries[0]["rule"] == bandit.SCHEDULE_RULE
        # the schedule slot is the panel the frozen reader sees at that boundary
        panel = [p for p in summary["panels"] if p["panel_rollouts"] == boundary][0]
        assert entries[0]["J_world_scores"] == panel["native_scores_J"]
    assert sorted(by_boundary) == list(bandit.PANEL_ROLLOUTS)
    assert len(by_boundary[ROLLOUTS]) == 2 + N_LABELS

    # `best_estimate` executes argmax beta_hat and nothing else
    for entry in summary["panel_runs"]:
        if entry["rule"] != bandit.SCHEDULE_RULE:
            continue
        label = int(entry["estimate"]["argmax_beta_hat"])
        assert entry["executed_rule"] == b09.constant_rule(label)
        assert entry["constant_label"] == label
        histogram = [int(value) for value in entry["agent_label_histogram"]]
        assert histogram[label] == LANES * HORIZON * N_UAVS
        assert sum(histogram) == histogram[label]
    # the six constant panels at the last boundary are the map, one panel per label
    final_map = {entry["constant_label"] for entry in by_boundary[ROLLOUTS]
                 if entry["rule"] in bandit.FINAL_MAP_RULES}
    assert final_map == set(range(N_LABELS))
    assert summary["evaluation"]["native_scores_J"] == by_boundary[ROLLOUTS][0]["J_world_scores"]


@pytest.mark.parametrize("arm", sorted(bandit.ARMS))
def test_the_executed_labels_are_the_labels_the_buffer_stored_and_the_record_carries_them(
        tiny, tiny_fits, arm):
    """The rewrite reached the storage path: the fit itself refuses otherwise, and the two
    independent tallies of the executed labels agree."""
    fit = tiny_fits[arm]
    summary = fit["summary"]
    records = bandit.bandit_rows(summary)
    assert [record["rollout"] for record in records] == [1, 2]
    stored = np.zeros(N_LABELS, dtype=np.int64)
    for record in records:
        counts = np.asarray(record["commitment_label_counts"], dtype=np.int64)
        assert record["commitments"] == LANES * COMMITMENTS_PER_LANE
        assert int(counts.sum()) == record["commitments"] * N_UAVS
        assert record["discounted_agreement_max_abs"] < bandit.DISCOUNTED_AGREEMENT_TOLERANCE
        assert record["arm"] == arm
        # `draws` and `replaced_positions` are the rule's running totals over the fit so far
        assert record["draws"] == LANES * N_UAVS * HORIZON * record["rollout"]
        assert record["replaced_positions"] == (
            record["commitments"] * N_UAVS * record["rollout"])
        assert record["mean_reward_per_step"] is not None
        assert record["action_standard_deviation_mean"] > 0.
        assert record["optimizer_calls"]["coordinator"] == 0
        # the frozen update's own two discriminator accuracies, copied into the record
        row = summary["training_rows"][record["rollout"] - 1]
        for name in ("discriminator_team_accuracy", "discriminator_individual_accuracy"):
            assert record[name] == pytest.approx(row["losses"][name])
            assert 0. <= record[name] <= 1.
        stored += counts
    # the rule's own tally of the labels it executed at decisions, and the buffer's, agree
    final = summary["label_bandit_final"]
    assert final["decision_label_counts"] == stored.tolist()
    assert sum(final["executed_label_counts"]) == LANES * HORIZON * N_UAVS * ROLLOUTS
    assert final["draws"] == LANES * N_UAVS * HORIZON * ROLLOUTS

    lines = [json.loads(line) for line in
             (fit["out"] / "bandit.jsonl").read_text(encoding="utf-8").strip().splitlines()]
    assert [line["rollout"] for line in lines] == [1, 2]
    assert lines == records  # the sidecar stream and the training rows are the same records
    training = [json.loads(line) for line in
                (fit["out"] / "training.jsonl").read_text(encoding="utf-8").strip().splitlines()]
    assert [row["label_bandit"] for row in training] == records


def test_the_uniform_arms_law_never_leaves_uniform_while_its_estimator_updates(tiny, tiny_fits):
    records = bandit.bandit_rows(tiny_fits[bandit.UNIFORM_ARM]["summary"])
    uniform = [1. / N_LABELS] * N_LABELS
    for record in records:
        assert record["q_used_source"] == record["q_next_source"] == "uniform"
        assert record["q_used"] == pytest.approx(uniform)
        assert record["q_next"] == pytest.approx(uniform)
    # and the estimator ran anyway: it is passive in this arm, not switched off
    assert [record["estimate"]["rollouts_seen"] for record in records] == [1, 2]
    assert [record["estimate"]["rollouts_used"] for record in records] == [1, 2]
    assert all(record["estimate"]["estimate_available"] for record in records)
    assert any(value != 0. for value in records[-1]["estimate"]["beta_hat"])


def test_the_bandit_arms_law_is_the_declared_combination_once_an_estimate_exists(tiny, tiny_fits):
    records = bandit.bandit_rows(tiny_fits[bandit.BANDIT_ARM]["summary"])
    assert records[0]["q_used_source"] == "uniform_no_estimate"
    assert records[0]["q_used"] == pytest.approx([1. / N_LABELS] * N_LABELS)
    for record in records:
        if not record["estimate"]["estimate_available"]:
            continue
        assert record["q_next_source"] == "softmax_z"
        law = np.asarray(record["q_next"], dtype=np.float64)
        assert law.sum() == pytest.approx(1.)
        assert law.min() >= bandit.LABEL_FLOOR - 1e-12
        # the law is exactly `.7 softmax(z) + .3 uniform` of the estimate recorded beside it
        z = np.asarray(record["estimate"]["z"], dtype=np.float64)
        soft = np.exp(z - z.max())
        soft = soft / soft.sum()
        expected = bandit.EXPLOIT_WEIGHT * soft + bandit.FLOOR_WEIGHT / N_LABELS
        np.testing.assert_allclose(law, expected, rtol=0, atol=1e-15)
        assert record["argmax_q_next"] == int(np.argmax(law))
    # the two arms are the same construction and the same block, so only the law differs
    uniform = tiny_fits[bandit.UNIFORM_ARM]["summary"]
    bandit_fit = tiny_fits[bandit.BANDIT_ARM]["summary"]
    assert bandit_fit["learner_config"] == uniform["learner_config"]
    assert bandit_fit["evaluation_config"] == uniform["evaluation_config"]
    assert bandit_fit["training_lane_seeds"] == uniform["training_lane_seeds"]
    assert bandit_fit["evaluation_lane_seeds"] == uniform["evaluation_lane_seeds"]
    assert bandit_fit["initial_parameter_norms"] == uniform["initial_parameter_norms"]
    assert bandit_fit["counts"] == uniform["counts"]


@pytest.mark.parametrize("arm", sorted(bandit.ARMS))
def test_the_final_weights_are_written_after_the_fit_with_this_objects_sidecar(
        tiny, tiny_fits, arm):
    fit = tiny_fits[arm]
    summary, out = fit["summary"], fit["out"]
    weights = summary["final_weights"]
    path = out / bandit.WEIGHTS_NAME
    assert path.exists() and weights["file"] == bandit.WEIGHTS_NAME
    assert weights["object_id"] == bandit.OBJECT_ID
    assert weights["sha256"] == bandit.b08.file_sha256(path)
    assert weights["bytes"] == path.stat().st_size > 0
    assert weights["arm"] == arm and weights["block_seed"] == SEED
    assert weights["training_seed"] == SEED and weights["evaluation_seed"] == EVALUATION_SEED
    assert weights["rollouts"] == ROLLOUTS
    assert weights["argmax_beta_hat"] == summary["label_bandit_final"]["argmax_beta_hat"]
    assert weights["inventory"]
    sidecar = json.loads((out / bandit.SIDECAR_NAME).read_text(encoding="utf-8"))
    assert sidecar == weights


@pytest.mark.parametrize("arm", sorted(bandit.ARMS))
def test_this_objects_own_reader_reads_its_own_tiny_fit(tiny, tiny_fits, arm):
    summary = tiny_fits[arm]["summary"]
    assert bandit.check_fit_refusals(summary) is True
    scores = bandit.fit_endpoint(summary)
    assert sorted(scores) == list(bandit.PANEL_ROLLOUTS)
    means, worlds = bandit.panel_scores(summary)
    assert sorted(means) == sorted(
        {bandit.SCHEDULE_RULE, bandit.REFERENCE_RULE} | set(bandit.FINAL_MAP_RULES))
    row = bandit.fit_row(summary, scores)
    assert row["arm"] == arm and row["block_seed"] == SEED
    assert sorted(row["label_map_J"]) == [str(label) for label in range(N_LABELS)]
    assert sorted(row["label_map_ranking"]) == list(range(N_LABELS))
    assert 1 <= row["rank_of_argmax_beta_hat_in_the_map"] <= N_LABELS
    assert row["schedule_slot_matches_its_constant_panel"] is True
    assert len(row["law"]["argmax_beta_hat_by_rollout"]) == ROLLOUTS
    assert row["law"]["rank_deficient_rollouts"] == []
    assert all(value is not None
               for value in row["law"]["discriminator_team_accuracy_by_rollout"])


def test_the_coordinator_optimizer_cannot_take_a_step_while_a_fit_runs(tiny, tiny_fits):
    """The run-time guard on the real optimizer, and the frozen counter it hands back."""
    fit = tiny_fits[bandit.BANDIT_ARM]
    agent, counters = fit["agent"], fit["counters"]
    frozen = agent.coordinator_optimizer.step
    assert frozen is counters["coordinator"]
    with bandit.forbid_coordinator_steps(agent) as original:
        assert original is frozen
        with pytest.raises(RuntimeError, match="coordinator optimizer took a step"):
            agent.coordinator_optimizer.step()
        # the other optimizers are untouched and still step normally
        assert agent.discoverer_actor_optimizer.step is counters["discoverer_actor"]
    assert agent.coordinator_optimizer.step is frozen
    assert counters["coordinator"].count == 0


def test_a_refusal_after_a_complete_fit_is_reported_and_writes_no_weights(tmp_path, tiny,
                                                                         monkeypatch):
    """A fit that runs to the end but fails a declared refusal is an incomplete, reported fit."""
    monkeypatch.setattr(bandit, "panel_names",
                        lambda rollouts_completed, label: [
                            (bandit.SCHEDULE_RULE, b09.constant_rule(int(label)))])
    # `expected_panels` is left at the declared schedule, so the thin fan-out is refused
    out = tmp_path / "refused"
    result = run_tiny_fit(bandit.BANDIT_ARM, out)
    assert result["status"] == 1
    summary = result["summary"]
    assert summary["status"] == "incomplete"
    assert "panels, not the declared" in summary["failure"]
    assert summary["final_weights"] is None
    assert not (out / bandit.WEIGHTS_NAME).exists()
    assert not (out / bandit.SIDECAR_NAME).exists()
    # the collection itself did run, and its records are kept for the report
    assert len(summary["training_rows"]) == ROLLOUTS
    assert all(row.get("label_bandit") for row in summary["training_rows"])
    assert (out / "bandit.jsonl").exists()
    # and every wrapper still came off
    assert "_batched_assign_skills" not in result["agent"].__dict__
    assert "update" not in result["agent"].__dict__
    assert b01.evaluate_panel is bandit._orig_evaluate_panel


# ---------------------------------------------------------------------------
# the panels leave the training stream alone
# ---------------------------------------------------------------------------


def test_the_extra_panels_do_not_move_the_training_stream(tmp_path, tiny, tiny_fits, monkeypatch):
    """The same fit with the fan-out reduced to the schedule slot: identical training rows.

    Every panel runs inside the frozen `_preserve_rng`, so a boundary that runs ten panels must
    leave the Python, NumPy and torch streams exactly where a boundary that runs one leaves them.
    """
    monkeypatch.setattr(bandit, "panel_names",
                        lambda rollouts_completed, label: [
                            (bandit.SCHEDULE_RULE, b09.constant_rule(int(label)))])
    monkeypatch.setattr(bandit, "expected_panels", lambda: len(bandit.PANEL_ROLLOUTS))
    out = tmp_path / "no_fan_out"
    reduced = run_tiny_fit(bandit.BANDIT_ARM, out)
    assert reduced["status"] == 0
    thin = reduced["summary"]
    full = tiny_fits[bandit.BANDIT_ARM]["summary"]

    assert len(thin["panel_runs"]) == len(bandit.PANEL_ROLLOUTS) < len(full["panel_runs"])
    assert thin["extra_panels"] == []
    assert thin["counts"]["evaluation_episodes"] < full["counts"]["evaluation_episodes"]
    for mine, theirs in zip(thin["training_rows"], full["training_rows"]):
        assert mine["episode_returns_U"] == theirs["episode_returns_U"]
        assert mine["return_sums"] == theirs["return_sums"]
        assert mine["losses"] == theirs["losses"]
        assert mine["relative_initialization_displacement"] == theirs[
            "relative_initialization_displacement"]
        assert mine["segments"] == theirs["segments"]
        assert mine["label_bandit"] == theirs["label_bandit"]
    assert thin["learner_config"] == full["learner_config"]
    assert thin["initial_parameter_norms"] == full["initial_parameter_norms"]
    assert thin["optimizer_calls"] == full["optimizer_calls"]
    assert thin["label_bandit_final"] == full["label_bandit_final"]
    assert thin["final_weights"]["sha256"] == full["final_weights"]["sha256"]
    # and the schedule slot itself is the same panel at every boundary
    for mine, theirs in zip(thin["panels"], full["panels"]):
        assert mine["native_scores_J"] == theirs["native_scores_J"]
