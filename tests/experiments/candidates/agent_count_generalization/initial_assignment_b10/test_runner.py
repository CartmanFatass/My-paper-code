"""Focused native and synthetic checks for the fixed B10 evaluator."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import MethodType, SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.action_law_b02.probe import restore_checkpoint
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC, make_config
from experiments.candidates.agent_count_generalization.initial_assignment_b10 import runner
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS, digest_agent, native_components, optimizer_counts, reset_all,
    save_checkpoint, seed_rng,
)
from scripts import run_agent_count_initial_assignment_b10 as entry


TECH_FIT = replace(
    DEFAULT_SPEC, horizon=12, train_lanes=2, eval_lanes=2, rollouts=1,
    panels=(0, 1), hidden_size=16, n_heads=2, n_layers=1, ppo_epochs=1,
    sequence_batch_size=4, coordinator_batch_size=2, torch_threads=1,
)
TECH_EVAL = runner.EvalSpec(horizon=12, eval_lanes=2, torch_threads=1)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config(arm: str, seed: int, n: int):
    envs = make_envs(TECH_EVAL.eval_lanes, runner._world_seed(n), n, TECH_EVAL.horizon)
    try:
        config = make_config(arm, envs, seed, TECH_FIT)
        config.lambda_l = config.lambda_l_initial = config.lambda_l_final = .05
        config.use_entropy_annealing = False
        config.use_entropy_targets = False
        config.validate_config()
        return config
    finally:
        for env in envs:
            env.close()


def _baseline_panel(payload: dict, seed: int, n: int, root: Path) -> dict:
    world_seed = runner._world_seed(n)
    seed_rng(world_seed + 51)
    envs = make_envs(TECH_EVAL.eval_lanes, world_seed, n, TECH_EVAL.horizon)
    target, hooks = None, []
    try:
        config = _config("H6", seed, n)
        target = build_agent(config, str(root / "baseline_logs" / str(n)))
        restore_checkpoint(target, payload)
        for lane in range(TECH_EVAL.eval_lanes):
            target.reset_env_state(lane)
        calls, hooks = optimizer_counts(target)
        states, observations = reset_all(envs)
        steps = np.zeros(TECH_EVAL.eval_lanes, dtype=np.int64)
        dones = np.zeros(TECH_EVAL.eval_lanes, dtype=bool)
        returns = np.zeros(TECH_EVAL.eval_lanes, dtype=np.float64)
        parts = {name: np.zeros(TECH_EVAL.eval_lanes) for name in COMPONENTS}
        with torch.no_grad():
            for _ in range(TECH_EVAL.horizon):
                actions, _, _ = target.step(
                    states, observations, steps, dones, deterministic=True,
                    return_step_data=True, build_infos=False,
                )
                next_states, next_observations = [], []
                for lane, env in enumerate(envs):
                    observation, reward, terminated, truncated, info = env.step(
                        np.clip(actions[lane], -1.0, 1.0)
                    )
                    dones[lane] = bool(terminated or truncated)
                    returns[lane] += reward
                    values = native_components(info, reward, n)
                    for name in COMPONENTS:
                        parts[name][lane] += values[name]
                    next_states.append(info["next_state"])
                    next_observations.append(observation)
                states, observations = np.stack(next_states), np.stack(next_observations)
                steps += 1
        means = {name: (value / TECH_EVAL.horizon).tolist() for name, value in parts.items()}
        return {
            "after_rollout": 45, "training_team_steps": 360_000, "test_n": n,
            "world_seeds": list(range(world_seed, world_seed + TECH_EVAL.eval_lanes)),
            "execution_law": "clip", "status": "complete",
            "steps": TECH_EVAL.eval_lanes * TECH_EVAL.horizon,
            "episodes": TECH_EVAL.eval_lanes,
            "J": (n * returns / TECH_EVAL.horizon).tolist(),
            "scalar_returns": returns.tolist(), "component_means": means,
            "optimizer_calls": calls.copy(), "frozen_weights_and_normalizers": True,
            "config": runner.b08._config_record(config),
        }
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        del target


def _set_panel(n: int) -> dict:
    coverage = np.asarray([.4, .5], dtype=np.float64)
    quality = np.asarray([.2, .3], dtype=np.float64)
    penalty = np.asarray([.05, .07], dtype=np.float64)
    total = .7 * coverage + .3 * quality - penalty
    returns = total * TECH_EVAL.horizon / n
    return {
        "after_rollout": 45, "test_n": n,
        "world_seeds": list(range(runner._world_seed(n), runner._world_seed(n) + 2)),
        "execution_law": "clip", "status": "complete", "steps": 24, "episodes": 2,
        "J": total.tolist(), "scalar_returns": returns.tolist(),
        "component_means": {
            "coverage_reward": coverage.tolist(), "quality_reward": quality.tolist(),
            "energy_penalty": penalty.tolist(), "total_reward": total.tolist(),
        },
        "optimizer_calls": {"coordinator": 0},
        "frozen_weights_and_normalizers": True,
        "config": runner.b08._config_record(_config("SET", 953201, n)),
    }


def _make_assets(root: Path):
    seed, tag, source = 952201, "technical_b10_h6", "technical-b10-h6-source"
    config = _config("H6", seed, 6)
    seed_rng(seed)
    agent = build_agent(config, str(root / "agent_logs"))
    try:
        agent.value_norm_discoverer.mean = np.asarray(2.25)
        agent.value_norm_discoverer.var = np.asarray(3.5)
        agent.value_norm_discoverer.count = 13.0
        with torch.no_grad():
            next(agent.skill_discoverer.actor.parameters()).add_(.004)
        final_digest = digest_agent(agent)
        checkpoint_root = root / "checkpoints" / tag
        checkpoint_root.mkdir(parents=True)
        checkpoint_record = save_checkpoint(agent, checkpoint_root, 45, config, source)
    finally:
        del agent
    checkpoint = checkpoint_root / checkpoint_record["path"]
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    run_root = root / "summaries" / tag
    panels, hashes = [], []
    for n in TECH_EVAL.test_ns:
        panel = _baseline_panel(payload, seed, n, root)
        path = run_root / f"panel_45_n{n}.json"
        _write(path, panel)
        panels.append(panel)
        hashes.append(_sha(path))
    initial_digest = "1" * 64
    summary = {
        "schema": 1, "object_id": "technical-b10-h6-object",
        "direction": "agent_count_generalization",
        "cell": {"key": "h6_l05", "tag": tag, "arm": "H6", "law": "clip",
                 "seed": seed, "lambda_l": .05},
        "arm": "H6", "training_action_law": "clip", "seed": seed, "tag": tag,
        "launch_sha": source, "status": "complete", "fit_started": True,
        "spec": runner.jsonable(vars(TECH_FIT)), "config": runner.b08._config_record(config),
        "observed_initial_parameter_normalizer_digest": initial_digest,
        "checkpoints": [
            {"path": "checkpoint_00.pt", "sha256": "2" * 64, "bytes": 123},
            checkpoint_record,
        ],
        "panels": panels,
    }
    summary_path = run_root / "summary.json"
    _write(summary_path, summary)
    h6 = runner.b09.AssetSpec(
        "h6", "H6", seed, tag, source, summary["object_id"], "h6_l05",
        _sha(summary_path), "2" * 64, 123,
        checkpoint_record["sha256"], checkpoint_record["bytes"],
        initial_digest, final_digest, tuple(hashes),
    )

    set_tag = "technical_b10_set_reference"
    set_root = root / "summaries" / set_tag
    set_panels, set_hashes = [], []
    set_config = _config("SET", 953201, 6)
    for n in TECH_EVAL.test_ns:
        panel = _set_panel(n)
        path = set_root / f"panel_45_n{n}.json"
        _write(path, panel)
        set_panels.append(panel)
        set_hashes.append(_sha(path))
    set_summary = {
        "schema": 1, "object_id": "technical-b10-set-object",
        "direction": "agent_count_generalization",
        "cell": {"key": "set_l05", "tag": set_tag, "arm": "SET", "law": "clip",
                 "seed": 953201, "lambda_l": .05},
        "arm": "SET", "training_action_law": "clip", "seed": 953201,
        "tag": set_tag, "launch_sha": "technical-b10-set-source", "status": "complete",
        "fit_started": True, "spec": runner.jsonable(vars(TECH_FIT)),
        "config": runner.b08._config_record(set_config),
        "observed_initial_parameter_normalizer_digest": "3" * 64,
        "checkpoints": [
            {"path": "checkpoint_00.pt", "sha256": "4" * 64, "bytes": 456},
            {"path": "checkpoint_45.pt", "sha256": "5" * 64, "bytes": 789},
        ], "panels": set_panels,
    }
    set_summary_path = set_root / "summary.json"
    _write(set_summary_path, set_summary)
    set_reference = runner.b08.AssetSpec(
        "set", "SET", 953201, set_tag, set_summary["launch_sha"],
        set_summary["object_id"], "set_l05", _sha(set_summary_path),
        "4" * 64, 456, "5" * 64, 789, "3" * 64, tuple(set_hashes),
    )
    return h6, set_reference, checkpoint


@pytest.fixture(scope="module")
def technical_assets(tmp_path_factory):
    root = tmp_path_factory.mktemp("initial-assignment-b10-assets")
    h6, set_reference, checkpoint = _make_assets(root)
    return root, h6, set_reference, checkpoint


@pytest.fixture(scope="module")
def completed_study(tmp_path_factory, technical_assets):
    root, h6, set_reference, checkpoint = technical_assets
    out = tmp_path_factory.mktemp("initial-assignment-b10-study") / runner.TAG
    assert runner.run_study(
        out, "technical-b10", {"sha": "technical-b10"}, checkpoint,
        h6_asset=h6, set_reference=set_reference, eval_spec=TECH_EVAL,
        summary_root=root / "summaries", committed_sources=False,
    ) == 0, (out / "summary.json").read_text(encoding="utf-8")
    return out, _read(out / "summary.json")


class _FakeCoordinator:
    def assign_and_value_batch(self, states, observations, deterministic=False):
        count = states.shape[0]
        offset = states[:, 0].to(dtype=torch.long)
        return {
            "team_skills": offset % 4,
            "agent_skills": torch.stack([(offset + i) % 5 for i in range(4)], dim=1),
            "team_log_probs": torch.zeros(count), "agent_log_probs": torch.zeros(count, 4),
            "state_values": torch.zeros(count, 1), "agent_values": torch.zeros(count, 4),
        }


class _FakeAgent:
    def __init__(self, fail_after_forward=False):
        self.config = SimpleNamespace(k=10, n_agents=4)
        self.skill_coordinator = _FakeCoordinator()
        self.env_team_skills = {0: -1, 1: -1}
        self.env_agent_skills = {0: np.full(4, -1), 1: np.full(4, -1)}
        self.env_log_probs = {0: {}, 1: {}}
        self.fail_after_forward = fail_after_forward

    def _batched_assign_skills(self, states, observations, steps, dones, deterministic=False):
        needed = (steps % 10 == 0) | dones | np.asarray([
            self.env_team_skills[i] == -1 or np.any(self.env_agent_skills[i] == -1)
            for i in range(len(steps))
        ])
        lanes = np.where(needed)[0]
        if not len(lanes):
            return (
                np.asarray([self.env_team_skills[i] for i in range(len(steps))]),
                np.asarray([self.env_agent_skills[i] for i in range(len(steps))]),
                [self.env_log_probs[i] for i in range(len(steps))],
            )
        values = self.skill_coordinator.assign_and_value_batch(
            torch.as_tensor(states[lanes], dtype=torch.float32),
            torch.as_tensor(observations[lanes], dtype=torch.float32), deterministic=deterministic,
        )
        if self.fail_after_forward:
            raise RuntimeError("native postprocessing failure")
        teams = np.asarray([self.env_team_skills[i] for i in range(len(steps))])
        agents = np.asarray([self.env_agent_skills[i] for i in range(len(steps))])
        logs = [self.env_log_probs[i] for i in range(len(steps))]
        for j, lane in enumerate(lanes):
            teams[lane] = int(values["team_skills"][j])
            agents[lane] = values["agent_skills"][j].numpy()
            logs[lane] = {"team_log_prob": 0., "agent_log_probs": [0.] * 4,
                          "state_value": 0., "agent_values": [0.] * 4}
            self.env_team_skills[lane] = int(teams[lane])
            self.env_agent_skills[lane] = agents[lane].copy()
            self.env_log_probs[lane] = logs[lane].copy()
        return teams, agents, logs


def test_fixed_contract_and_production_counts():
    assert runner.MODES == ("ordinary", "initial_replay")
    assert runner.H6_ASSET.checkpoint_sha256 == (
        "6d71f3023e5593a801b4d618f7eece93df1a15575f8a71d769566190ba6498df"
    )
    assert runner.SET_REFERENCE.summary_sha256.startswith("136d090b")
    assert runner._expected_counts(runner.DEFAULT_SPEC) == {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_calls": 0, "panels": 6, "evaluation_team_steps": 48000,
        "evaluation_uav_steps": 288000, "evaluation_episodes": 96,
        "evaluation_resets": 96, "actual_batched_policy_step_calls": 3000,
        "coordinator_selection_forwards": 300,
        "per_lane_coordinator_selections": 4800, "opening_lane_selections": 96,
        "later_lane_selections": 4704, "trace_files": 6, "shadow_forwards": 0,
        "set_model_loads": 0, "training_storage_calls": 0,
    }


def test_adapter_caches_real_opening_copies_and_replays_before_action():
    agent = _FakeAgent()
    observed = []
    adapter = runner.AssignmentAdapter(agent, "initial_replay", lambda *row: observed.append(row))
    try:
        adapter.mark_reset(0)
        adapter.mark_reset(1)
        states = np.asarray([[1.], [2.]], dtype=np.float32)
        observations = states.copy()
        team0, individual0, logs0 = agent._batched_assign_skills(
            states, observations, np.asarray([0, 0]), np.asarray([False, False]), True
        )
        opening = individual0.copy()
        individual0[0, 0] = 99
        assert adapter.opening_individual[0][0] != 99
        team1, individual1, _ = agent._batched_assign_skills(
            states, observations, np.asarray([1, 1]), np.asarray([False, False]), True
        )
        assert np.array_equal(individual1, opening)
        states10 = np.asarray([[3.], [4.]], dtype=np.float32)
        team10, individual10, logs10 = agent._batched_assign_skills(
            states10, states10, np.asarray([10, 10]), np.asarray([False, False]), True
        )
        assert np.array_equal(individual10, opening)
        assert np.array_equal(agent.env_agent_skills[0], opening[0])
        assert logs10[0]["semantics"] == "native coordinator proposal only"
        assert logs10[0]["eligible_for_training_storage"] is False
        adapter.mark_reset(1)
        mixed = np.asarray([[5.], [8.]], dtype=np.float32)
        _, reset_labels, _ = agent._batched_assign_skills(
            mixed, mixed, np.asarray([11, 0]), np.asarray([False, False]), True
        )
        assert np.array_equal(reset_labels[0], opening[0])
        assert not np.array_equal(reset_labels[1], opening[1])
        assert observed == [
            (1, 2, 0, 0), (0, 0, 2, 0),
            (1, 2, 0, 0), (0, 0, 0, 2),
            (1, 1, 0, 0), (0, 0, 1, 0),
        ]
    finally:
        adapter.close()
    assert agent._batched_assign_skills.__func__ is _FakeAgent._batched_assign_skills


def test_successful_coordinator_forward_count_survives_native_postprocessing_failure():
    agent = _FakeAgent(fail_after_forward=True)
    observed = []
    adapter = runner.AssignmentAdapter(agent, "ordinary", lambda *row: observed.append(row))
    adapter.mark_reset(0)
    adapter.mark_reset(1)
    values = np.zeros((2, 1), dtype=np.float32)
    with pytest.raises(RuntimeError, match="postprocessing"):
        agent._batched_assign_skills(values, values, np.zeros(2, dtype=int), np.zeros(2, dtype=bool))
    assert observed == [(1, 2, 0, 0), (0, 0, 2, 0)]
    assert adapter.selection_forwards == 1 and adapter.per_lane_selections == 2
    adapter.close()


def test_actual_forward_and_lane_count_precede_opportunity_diagnostic():
    class Mismatched(_FakeAgent):
        def _batched_assign_skills(self, states, observations, steps, dones, deterministic=False):
            self.skill_coordinator.assign_and_value_batch(
                torch.as_tensor(states[:1]), torch.as_tensor(observations[:1]),
                deterministic=deterministic,
            )
            raise AssertionError("unreachable")

    agent = Mismatched()
    observed = []
    adapter = runner.AssignmentAdapter(agent, "ordinary", lambda *row: observed.append(row))
    adapter.mark_reset(0)
    adapter.mark_reset(1)
    values = np.zeros((2, 1), dtype=np.float32)
    with pytest.raises(ValueError, match="input count"):
        agent._batched_assign_skills(values, values, np.zeros(2, dtype=int), np.zeros(2, dtype=bool))
    assert observed == [(1, 1, 0, 0)]
    assert adapter.selection_forwards == 1 and adapter.per_lane_selections == 1
    assert adapter.opening_lane_selections == 0
    adapter.close()


def _run_real_native_routing(root: Path, checkpoint: Path, mode: str) -> dict:
    n, world_seed = 4, runner._world_seed(4)
    seed_rng(world_seed + 51)
    envs = make_envs(TECH_EVAL.eval_lanes, world_seed, n, TECH_EVAL.horizon)
    target = build_agent(_config("H6", 952201, n), str(root / f"native_{mode}"))
    restore_checkpoint(target, torch.load(checkpoint, map_location="cpu", weights_only=True))
    native_coordinator = target.skill_coordinator.assign_and_value_batch
    native_select = target._batched_select_action
    coordinator_calls = 0
    opening_native = None
    routed = []

    def forced(_coordinator, states, observations, deterministic=False):
        nonlocal coordinator_calls, opening_native
        result = native_coordinator(states, observations, deterministic=deterministic)
        result = {key: value.clone() if torch.is_tensor(value) else value for key, value in result.items()}
        coordinator_calls += 1
        if coordinator_calls == 1:
            opening_native = (
                result["team_skills"].clone(), result["agent_skills"].clone(),
            )
        else:
            source = opening_native[1] if result["agent_skills"].shape[0] == 2 else opening_native[1][1:2]
            source_team = opening_native[0] if result["team_skills"].shape[0] == 2 else opening_native[0][1:2]
            result["team_skills"] = (source_team + 1) % target.config.n_Z
            result["agent_skills"] = (source + 1) % target.config.n_z
        return result

    def select_spy(
        _agent, states, observations, agent_skills, team_skills, dones, deterministic=False,
    ):
        routed.append((np.asarray(team_skills).copy(), np.asarray(agent_skills).copy()))
        return native_select(
            states, observations, agent_skills, team_skills, dones, deterministic,
        )

    target.skill_coordinator.assign_and_value_batch = MethodType(forced, target.skill_coordinator)
    target._batched_select_action = MethodType(select_spy, target)
    adapter = runner.AssignmentAdapter(target, mode)
    try:
        states, observations = runner._reset_lanes_counted(envs, target, adapter, n, None)
        steps = np.zeros(2, dtype=np.int64)
        dones = np.zeros(2, dtype=bool)
        timers, hidden = [], []
        with torch.no_grad():
            for _ in range(12):
                actions, _, data = target.step(
                    states, observations, steps, dones, deterministic=True,
                    return_step_data=True, build_infos=False,
                )
                timers.append(np.asarray(data["skill_timer"]).copy())
                hidden.append(runner._actor_lane_digests(target.actor_hidden_np, 2))
                next_states, next_observations = [], []
                for lane, env in enumerate(envs):
                    observation, _reward, terminated, truncated, info = env.step(
                        np.clip(actions[lane], -1., 1.)
                    )
                    dones[lane] = bool(terminated or truncated)
                    next_states.append(info["next_state"])
                    next_observations.append(observation)
                states, observations = np.stack(next_states), np.stack(next_observations)
                steps += 1
        opening_cache = {lane: value.copy() for lane, value in adapter.opening_individual.items()}
        target.reset_env_state(1)
        observation, info = envs[1].reset()
        adapter.mark_reset(1)
        states[1], observations[1], steps[1], dones[1] = info["state"], observation, 0, False
        target.step(
            states, observations, steps, dones, deterministic=True,
            return_step_data=True, build_infos=False,
        )
        assert np.array_equal(adapter.opening_individual[0], opening_cache[0])
        assert not np.array_equal(adapter.opening_individual[1], opening_cache[1])
        return {
            "routed": routed, "timers": timers, "hidden": hidden,
            "opening": opening_cache, "selection_forwards": adapter.selection_forwards,
        }
    finally:
        adapter.close()
        target.skill_coordinator.assign_and_value_batch = native_coordinator
        target._batched_select_action = native_select
        for env in envs:
            env.close()
        del target


def test_real_step_routes_replayed_labels_before_actor_and_preserves_native_clock(
    tmp_path, technical_assets,
):
    _asset_root, _h6, _set_reference, checkpoint = technical_assets
    ordinary = _run_real_native_routing(tmp_path, checkpoint, "ordinary")
    replay = _run_real_native_routing(tmp_path, checkpoint, "initial_replay")
    assert np.array_equal(ordinary["routed"][0][1], replay["routed"][0][1])
    assert not np.array_equal(ordinary["routed"][10][1], ordinary["routed"][0][1])
    assert np.array_equal(replay["routed"][10][1], replay["routed"][0][1])
    assert ordinary["selection_forwards"] == replay["selection_forwards"] == 3
    assert all(np.array_equal(a, b) for a, b in zip(ordinary["timers"], replay["timers"]))
    expected_timer = np.asarray([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1])
    assert np.array_equal(np.stack(replay["timers"]), np.repeat(expected_timer[:, None], 2, axis=1))
    assert not np.array_equal(replay["hidden"][0], replay["hidden"][-1])


def test_native_restore_replay_cadence_traces_and_isolation(completed_study):
    out, result = completed_study
    assert result["status"] == "complete"
    assert result["counts"] == runner._expected_counts(TECH_EVAL)
    assert [(row["mode"], row["test_n"]) for row in result["panels"]] == [
        (mode, n) for mode in runner.MODES for n in TECH_EVAL.test_ns
    ]
    for row in result["panels"]:
        assert row["assignment"]["selection_forwards"] == 2
        assert row["assignment"]["opening_lane_selections"] == 2
        assert row["assignment"]["later_lane_selections"] == 2
        assert row["shadow_forwards"] == row["training_storage_calls"] == 0
        assert row["parameter_normalizer_digest_before"] == row["parameter_normalizer_digest_after"]
        assert row["normalizers_before"] == row["normalizers_after"]
        assert row["global_rng_isolation"]["preserved"] and not any(row["optimizer_calls"].values())
        identity = row["trace"]
        assert Path(identity["path"]).is_file() and _sha(Path(identity["path"])) == identity["sha256"]
        if row["mode"] == "ordinary":
            assert row["historical_ordinary_identity"]["all_exact"]
    for comparison in result["mode_comparisons"].values():
        assert all(comparison["first_ten_common_prefix"].values())
        assert all(comparison["selection_cadence"].values())
    assert result["construction_counts"] == {
        "input_validation_attempts": 2, "input_validation_completions": 2,
        "checkpoint_deserialization_attempts": 1, "checkpoint_deserialization_completions": 1,
        "validation_environment_batch_construction_attempts": 3,
        "validation_environment_batch_construction_completions": 3,
        "validation_environment_instances_constructed": 6,
        "validation_agent_construction_attempts": 3,
        "validation_agent_construction_completions": 3,
        "panel_environment_batch_construction_attempts": 6,
        "panel_environment_batch_construction_completions": 6,
        "panel_environment_instances_constructed": 12,
        "panel_agent_construction_attempts": 6, "panel_agent_construction_completions": 6,
    }
    assert result["assets"]["set_reference"]["model_loaded_or_executed"] is False
    assert result["readings"]["positive_energy_penalty_change_is_adverse"]


def _synthetic_trace(root: Path, name: str, changed: bool) -> dict:
    spec, n = TECH_EVAL, 4
    arrays = runner._new_trace_arrays(spec, n)
    arrays["opportunity"][0] = True
    arrays["opportunity"][10] = True
    if changed:
        arrays["execution_individual"][10:, :, 0] = 1
        arrays["raw_actions"][10:, :, 0, 0] = 2.0
        arrays["actor_state_after_sha256"][10:, :, 0] = 1
        arrays["actor_state_before_sha256"][11:, :, 0] = 1
        arrays["clipped_actions"][10:, :, 0, 0] = 1.0
        arrays["state_sha256"][11:, :, 0] = 1
        arrays["observation_sha256"][11:, :, 0] = 1
    return runner._write_trace(root / f"{name}.npz", arrays)


def test_first_prefix_and_divergence_arithmetic_is_from_binary_trace(tmp_path):
    ordinary = _synthetic_trace(tmp_path, "ordinary", False)
    replay = _synthetic_trace(tmp_path, "replay", True)
    result = runner.compare_mode_traces(ordinary, replay, 4)
    assert all(result["first_ten_common_prefix"].values())
    for world in result["worlds"]:
        assert world["first_execution_individual_label_difference"] == 10
        assert world["first_raw_action_difference"] == 10
        assert world["first_clipped_action_difference"] == 10
        assert world["first_actor_state_after_difference"] == 10
        assert world["first_actor_state_before_difference"] == 11
        assert world["first_state_history_difference"] == 11
        assert world["first_observation_history_difference"] == 11


def test_reset_counter_is_at_actual_lane_boundary():
    class Env:
        def __init__(self, fail=False): self.fail = fail
        def reset(self):
            if self.fail: raise RuntimeError("later reset")
            return np.zeros(1), {"state": np.zeros(1)}
    class Agent:
        def reset_env_state(self, lane): pass
    class Adapter:
        def mark_reset(self, lane): pass
    counts = []
    progress = lambda *row: counts.append(row)
    with pytest.raises(RuntimeError, match="later reset"):
        runner._reset_lanes_counted([Env(), Env(True)], Agent(), Adapter(), 4, progress)
    assert counts == [(0, 0, 4, 0, 1, 0, 0, 0, 0, 0)]


def test_ordinary_mismatch_retains_measured_payload(tmp_path, technical_assets):
    root, h6, set_reference, checkpoint = technical_assets
    out = tmp_path / runner.TAG

    def failing(record, mode, n, target, spec, progress, construction):
        progress(1, 0, n, 1, 0, 1, 2, 2, 0, 0)
        row = {
            "status": "failed", "mode": mode, "test_n": n,
            "J": [1., 2.], "scalar_returns": [3., 4.],
            "component_means": {name: [5., 6.] for name in COMPONENTS},
            "historical_ordinary_identity": {"all_exact": False, "J": {"exact": False}},
        }
        runner.write_json(target / f"panel_{mode}_policy45_world45_n{n}.json", row)
        raise ValueError("ordinary arrays differ")

    assert runner.run_study(
        out, "failure", {"sha": "failure"}, checkpoint, h6_asset=h6,
        set_reference=set_reference, eval_spec=TECH_EVAL,
        summary_root=root / "summaries", committed_sources=False, evaluate_fn=failing,
    ) == 1
    result = _read(out / "summary.json")
    panel = result["panels"][0]
    assert panel["J"] == [1., 2.] and panel["historical_ordinary_identity"]["all_exact"] is False
    assert panel["status"] == result["status"] == "failed"
    assert result["counts"]["evaluation_team_steps"] == 1
    assert result["counts"]["evaluation_uav_steps"] == 4
    assert result["counts"]["actual_batched_policy_step_calls"] == 1
    assert result["counts"]["coordinator_selection_forwards"] == 1
    assert result["counts"]["per_lane_coordinator_selections"] == 2


def test_loader_rejects_changed_bound_h6_panel(tmp_path, technical_assets):
    root, h6, set_reference, checkpoint = technical_assets
    source_root = root / "summaries" / h6.tag
    copied = tmp_path / "summaries" / h6.tag
    copied.mkdir(parents=True)
    for path in source_root.iterdir():
        (copied / path.name).write_bytes(path.read_bytes())
    panel = _read(copied / "panel_45_n4.json")
    panel["J"][0] += 1
    _write(copied / "panel_45_n4.json", panel)
    with pytest.raises(ValueError, match="SHA-256"):
        runner.load_inputs(
            checkpoint, h6_asset=h6, set_reference=set_reference,
            summary_root=tmp_path / "summaries", committed_sources=False,
            eval_spec=TECH_EVAL,
        )


def test_cli_admission_precedes_scientific_import_and_preserves_fixed_surface(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(entry, "require_admission", lambda *_args, **_kwargs: calls.append("admit") or {"sha": "x"})
    out = tmp_path / entry.TAG
    checkpoint = tmp_path / "h6.pt"
    result = entry.main(
        ["--launch-sha", "x", "--out", str(out), "--h6-checkpoint", str(checkpoint)],
        run_fn=lambda *args, **kwargs: calls.append((args, kwargs)) or 7,
    )
    assert result == 7 and calls[0] == "admit" and not out.exists()
    with pytest.raises(SystemExit):
        entry.main(["--launch-sha", "x", "--out", str(out), "--h6-checkpoint", str(checkpoint), "--seed", "1"])
