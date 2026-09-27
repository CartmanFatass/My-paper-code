"""B03 learner on B02's loop: decision cadence, replay identity, tiny fit, checkpoints, resume."""

from __future__ import annotations

import copy
import json
from collections import Counter

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b02 import training as tr2
from experiments.candidates.energy_relay_benchmark.b03 import agent as ag
from experiments.candidates.energy_relay_benchmark.b03 import training as tr3
from experiments.candidates.energy_relay_benchmark.b03.anchors import anchors_from_state
from experiments.candidates.energy_relay_benchmark.b03.configuration import (
    GAS_RECORD, PROGRAMME, config_dict, make_b03_config,
)
from experiments.candidates.uav_service_auxiliary.b01.native import (
    initialization_fingerprint, optimizer_steps,
)
from hmasd.agent import HMASDAgent

CPU = torch.device("cpu")


def _rows(pairs):
    """Multiset of (actor input row bytes, label) from [(inputs (..., 3605), labels (...))]."""
    counter = Counter()
    for inputs, labels in pairs:
        inputs = inputs.reshape(-1, inputs.shape[-1]).numpy()
        labels = labels.reshape(-1).numpy()
        counter.update((row.tobytes(), int(label)) for row, label in zip(inputs, labels))
    return counter


@pytest.fixture(scope="module")
def captured(tmp_path_factory, tiny_spec):
    """Two rollouts of 2 x 30 with episodes of 25 (a mid-rollout reset and a live boundary)."""
    torch.set_num_threads(1)
    spec = tiny_spec(rollouts=2, rollout_length=30, episode_length=25)
    config = make_b03_config(spec)
    agent, _ = tr2.new_agent(config, device=CPU, log_dir=tmp_path_factory.mktemp("cap") / "logs",
                             seed=spec.seed, construct=ag.build_agent)
    actor = agent.skill_discoverer.actor
    acting, replay, steps, data, marks = [], [], [], [], []
    original_forward, original_evaluate = actor.forward, actor.evaluate_actions
    original_step, original_update = agent.step, agent.update

    def forward(obs, rnn_states, masks, agent_skill, *args, **kwargs):
        acting.append((obs.detach().clone(), agent_skill.detach().clone()))
        return original_forward(obs, rnn_states, masks, agent_skill, *args, **kwargs)

    def evaluate_actions(obs, rnn_states, action, masks, agent_skill, *args, **kwargs):
        replay.append((obs.detach().clone(), agent_skill.detach().clone()))
        return original_evaluate(obs, rnn_states, action, masks, agent_skill, *args, **kwargs)

    def step(states, observations, env_steps, dones, *args, **kwargs):
        before = agent._central_snapshot_states[:spec.lanes].copy()
        result = original_step(states, observations, env_steps, dones, *args, **kwargs)
        steps.append({"states": np.asarray(states).copy(), "env_steps": np.asarray(env_steps).copy(),
                      "timers": [agent.env_timers[lane] for lane in range(spec.lanes)],
                      "skills": np.asarray(result[2]["agent_skills"]).copy(), "before": before,
                      "after": agent._central_snapshot_states[:spec.lanes].copy()})
        return result

    def update(*args, **kwargs):
        data.append(copy.deepcopy(agent.rollout_buffer._get_full_rollout_data()))
        return original_update(*args, **kwargs)

    actor.forward, actor.evaluate_actions = forward, evaluate_actions
    agent.step, agent.update = step, update
    result = tr2.collect_and_train(agent, config, spec, feedback=True,
                                   after_rollout=lambda r, rec: marks.append((len(acting),
                                                                              len(replay))))
    return dict(spec=spec, config=config, agent=agent, acting=acting, replay=replay, steps=steps,
                data=data, marks=marks, result=result)


def test_decision_cadence_labels_and_anchors_come_from_the_same_step(captured):
    spec, steps = captured["spec"], captured["steps"]
    assert len(steps) == spec.rollouts * spec.rollout_length
    for index, row in enumerate(steps):
        decided = np.asarray(row["timers"]) == 0
        # Decisions exactly at episode steps 0, 10, 20 (including after the mid-rollout reset
        # and across the live rollout boundary).
        np.testing.assert_array_equal(decided, row["env_steps"] % 10 == 0, err_msg=str(index))
        for lane in range(spec.lanes):
            held = row["after"][lane]
            np.testing.assert_array_equal(held[324:332], row["skills"][lane])
            if decided[lane]:
                np.testing.assert_array_equal(held[:306], row["states"][lane].astype(np.float64))
                np.testing.assert_array_equal(held[306:324],
                                              anchors_from_state(row["states"][lane]).reshape(-1))
            else:
                np.testing.assert_array_equal(held, row["before"][lane])
    assert [r["live_lanes_at_boundary"] for r in captured["result"]["rollouts"]] == [2, 2]
    assert captured["result"]["rollouts"][0]["live_lane_timers_reset_by_clear"] == 0


def test_replayed_actor_input_equals_acting_input(captured):
    """float32-exact multiset equality per rollout: one PPO epoch replays every row once."""
    acting, replay, marks = captured["acting"], captured["replay"], captured["marks"]
    assert len(marks) == 2
    start_a = start_r = 0
    for end_a, end_r in marks:
        acted = _rows(acting[start_a:end_a])
        replayed = _rows(replay[start_r:end_r])
        assert sum(acted.values()) == 30 * 2 * 8 and acted == replayed
        assert all(inputs.shape[-1] == 3605 for inputs, _ in acting[start_a:end_a])
        start_a, start_r = end_a, end_r


def test_evaluate_sequence_rebuilds_the_acting_input(captured):
    agent, data = captured["agent"], captured["data"][1]
    acting = captured["acting"][30:60]
    disc = agent.skill_discoverer
    for env in range(2):
        states = torch.as_tensor(data["central_snapshot_states"][:, [env] * 8])
        observations = torch.as_tensor(data["central_snapshot_obs"][:, [env] * 8])
        central = agent._central_actor_input_from_replay(states, observations, torch.arange(8))
        obs_seq = torch.as_tensor(data["obs"][:, env])
        labels = torch.as_tensor(data["agent_skills"][:, env]).long()
        rebuilt = disc._apply_central_input(obs_seq, central, labels)
        expected = torch.stack([inputs[env * 8:(env + 1) * 8] for inputs, _ in acting])
        assert torch.equal(rebuilt, expected)
        log_probs, values, entropy = disc.evaluate_sequence(
            obs_seq, labels, torch.as_tensor(data["actions"][:, env]),
            torch.as_tensor(data["states"][:, [env] * 8]),
            torch.as_tensor(data["team_skills"][:, [env] * 8]).long(),
            initial_hxs=torch.zeros(8, agent.config.gru_hidden_size),
            initial_critic_hxs=torch.zeros(8, agent.config.gru_hidden_size),
            central_input_seq=central)
        assert log_probs.shape[:2] == (30, 8) and torch.isfinite(log_probs).all()
        with pytest.raises(RuntimeError, match="differs"):
            disc.evaluate_sequence(obs_seq, (labels + 1) % 9,
                                   torch.as_tensor(data["actions"][:, env]),
                                   torch.as_tensor(data["states"][:, [env] * 8]),
                                   torch.as_tensor(data["team_skills"][:, [env] * 8]).long(),
                                   central_input_seq=central)


@pytest.fixture(scope="module")
def fits(tmp_path_factory, tiny_spec):
    """run_a: full tiny GAS fit (3 rollouts, a checkpoint each).  run_b: resumed from c01."""
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp("b03_fit")
    spec = tiny_spec(rollouts=3)
    a = tr3.run_training(out=root / "run_a", launch_sha="sha-a", spec=spec, device_name="cpu",
                         threads=1, argv=["test"])
    b = tr3.run_training(out=root / "run_b", launch_sha="sha-b", spec=spec, device_name="cpu",
                         threads=1, argv=["test"],
                         resume_from=root / "run_a" / "checkpoints" / "c01",
                         resume_source_sha="sha-a")
    return dict(root=root, spec=spec, a=a, b=b)


def _decisions(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_tiny_fit_trains_both_levels_and_records_the_arm(fits):
    a, root = fits["a"], fits["root"] / "run_a"
    assert a["status"] == "COMPLETE" and a["arm"] == "gas" and a["programme"] == PROGRAMME
    steps = a["optimizer_steps"]
    assert steps["high"] > 0 and steps["low_actor"] > 0 and steps["low_critic"] > 0
    assert steps["team_discriminator"] == steps["individual_discriminator"] == 0
    assert a["actor_input_width"] == 3605 and a["checkpoint_rollouts"] == [1, 2, 3]
    assert sorted(p.name for p in (root / "checkpoints").iterdir()) == ["c00", "c01", "c02", "c03"]
    config = json.loads((root / "config.json").read_text())
    assert config["arm"] == "gas" and config["config"]["gas"] == GAS_RECORD
    assert config["recipe_notes"]["decision_summary"] == tr3.SUMMARY_DEFINITIONS
    for name in ("c00", "c03"):
        record = json.loads((root / "checkpoints" / name / "record.json").read_text())
        assert record["arm"] == "gas" and record["programme"] == PROGRAMME
        assert record["config"] == config_dict(make_b03_config(fits["spec"]))


def test_decision_log_and_summary(fits):
    a, root = fits["a"], fits["root"] / "run_a"
    rows = _decisions(root / tr3.DECISIONS_FILE)
    # 3 rollouts x 2 lanes x one episode of 20 steps x decisions at steps 0 and 10.
    assert len(rows) == 12 == sum(r["gas_decisions"]["decisions"] for r in a["rollouts"])
    assert [row["rollout"] for row in rows] == [1] * 4 + [2] * 4 + [3] * 4
    for row in rows:
        assert set(row) == {"rollout", "env", "step", "labels", "anchors", "own_xy"}
        assert row["step"] % 10 == 0 and len(row["labels"]) == 8
        assert np.asarray(row["anchors"]).shape == (9, 2) and row["anchors"][8] == [0.0, 0.0]
        assert np.asarray(row["own_xy"]).shape == (8, 2)
    progress = [json.loads(line) for line in (root / "progress.jsonl").read_text().splitlines()]
    events = [row["event"] for row in progress if row["event"]["event"] == "rollout"]
    assert [event["gas_decisions"] for event in events] == \
        [r["gas_decisions"] for r in a["rollouts"]]
    for record in a["rollouts"]:
        summary = record["gas_decisions"]
        assert summary["agent_decisions"] == 8 * summary["decisions"] == sum(summary["label_counts"])
        assert abs(sum(summary["label_share"].values()) - 1.0) < 1e-12
        assert 0.0 <= summary["duplicate_rate"] <= 1.0
        # Only the step-10 decision of each lane has a previous decision in the same episode.
        assert summary["stability"]["compared_agent_decisions"] == 2 * 8
        assert summary["previous_anchor_distance_m"]["count"] <= 16
    # Recompute one rollout's summary from the raw rows.
    recomputed, _ = tr3.decision_summary([{k: v for k, v in row.items() if k != "rollout"}
                                          for row in rows if row["rollout"] == 2])
    assert recomputed == a["rollouts"][1]["gas_decisions"]


def test_checkpoint_round_trip_and_compatibility(fits, tmp_path):
    root = fits["root"] / "run_a" / "checkpoints" / "c03"
    record = json.loads((root / "record.json").read_text())
    config = make_b03_config(fits["spec"])
    agent, _ = tr2.new_agent(config, device=CPU, log_dir=tmp_path / "load", seed=1,
                             construct=ag.build_agent)
    assert initialization_fingerprint(agent) != record["policy_fingerprint"]
    agent.load_model(str(root / "agent.pt"))
    assert initialization_fingerprint(agent) == record["policy_fingerprint"]
    assert optimizer_steps(agent) == record["optimizer_steps"]
    # A GAS agent.pt does not load into a plain HMASDAgent (actor input 3605 vs 3599).
    plain = HMASDAgent(copy.deepcopy(config), log_dir=str(tmp_path / "plain"), device=CPU)
    with pytest.raises(RuntimeError, match="size mismatch"):
        plain.load_model(str(root / "agent.pt"))


def test_resume_continues_the_fit(fits):
    a, b, root = fits["a"], fits["b"], fits["root"]
    assert b["status"] == "COMPLETE" and b["arm"] == "gas"
    assert [r["rollout"] for r in b["rollouts"]] == [2, 3]
    assert b["optimizer_steps"] == a["optimizer_steps"]
    assert sorted(b["checkpoints"]) == ["c02", "c03"]
    assert b["resume"]["re_seeded"] == list(tr3.RESUME_RE_SEEDED)
    rows = _decisions(root / "run_b" / tr3.DECISIONS_FILE)
    assert [row["rollout"] for row in rows] == [2] * 4 + [3] * 4
    record = json.loads((root / "run_a" / "checkpoints" / "c01" / "record.json").read_text())
    for name in ("c02", "c03"):
        written = json.loads((root / "run_b" / "checkpoints" / name / "record.json").read_text())
        assert written["config"] == record["config"] and written["arm"] == "gas"
    # A GAS checkpoint is refused as a B02 (SET) resume source.
    with pytest.raises(ValueError, match="is not"):
        tr2.read_resume_checkpoint(root / "run_a" / "checkpoints" / "c01", fits["spec"],
                                   tr2.make_b02_config(fits["spec"]))


def test_b02_default_recipe_writes_no_gas_fields(tmp_path, tiny_spec):
    torch.set_num_threads(1)
    spec = tiny_spec(rollouts=1, checkpoint_every_transitions=40)
    summary = tr2.run_training(out=tmp_path / "set", launch_sha="sha", spec=spec,
                               device_name="cpu", threads=1, argv=["test"])
    assert summary["status"] == "COMPLETE" and "arm" not in summary
    assert all("gas_decisions" not in record for record in summary["rollouts"])
    config = json.loads((tmp_path / "set" / "config.json").read_text())
    record = json.loads((tmp_path / "set" / "checkpoints" / "c01" / "record.json").read_text())
    assert "arm" not in config and "arm" not in record and "gas" not in record["config"]
    assert record["object_id"] == "ENERGY-RELAY-BENCHMARK-B02"
    assert not (tmp_path / "set" / tr3.DECISIONS_FILE).exists()
