"""Technical B03 action-boundary checks; these are not scientific fits."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import types

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC,
    make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.action_law_b03 import runner
from scripts import run_agent_count_action_law_training_b03 as entry


TECH_SPEC = replace(
    DEFAULT_SPEC,
    horizon=12,
    train_lanes=2,
    eval_lanes=2,
    rollouts=1,
    panels=(0, 1),
    hidden_size=16,
    n_heads=2,
    n_layers=1,
    ppo_epochs=1,
    sequence_batch_size=16,
    coordinator_batch_size=2,
    torch_threads=1,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def completed_cells(tmp_path_factory):
    root = tmp_path_factory.mktemp("action-law-b03-complete")
    results = {}
    initial_by_tag = {}
    replay_actions = {}

    for cell in runner.CELLS:
        expected = (
            initial_by_tag[cell.initial_digest_source]
            if cell.initial_digest_source is not None else None
        )
        captured = []

        def capture_replay(agent, *, sink=captured):
            original = agent.skill_discoverer.actor.evaluate_actions

            def wrapped(_actor, observations, initial_hxs, actions, masks, skills):
                sink.append(actions.detach().cpu().numpy().copy())
                return original(observations, initial_hxs, actions, masks, skills)

            agent.skill_discoverer.actor.evaluate_actions = types.MethodType(
                wrapped, agent.skill_discoverer.actor
            )

        out = root / cell.tag
        assert runner.run_fit(
            out,
            cell,
            "technical-fixture",
            {"sha": "technical-fixture"},
            expected,
            TECH_SPEC,
            agent_setup_hook=capture_replay,
        ) == 0, (out / "summary.json").read_text(encoding="utf-8")
        result = _read(out / "summary.json")
        results[cell.key] = result
        replay_actions[cell.key] = captured
        initial_by_tag[cell.tag] = result["observed_initial_parameter_normalizer_digest"]
    return results, replay_actions


def test_fixed_cells_and_production_defaults_are_exact():
    assert [
        (cell.index, cell.key, cell.arm, cell.law, cell.seed, cell.tag,
         cell.initial_digest_source)
        for cell in runner.CELLS
    ] == [
        (1, "h6_raw", "H6", "raw", 942201,
         "s1_action_law_b03_h6_raw_s942201", None),
        (2, "set_clip", "SET", "clip", 943201,
         "s1_action_law_b03_set_clip_s943201", None),
        (3, "h6_clip", "H6", "clip", 942201,
         "s1_action_law_b03_h6_clip_s942201",
         "s1_action_law_b03_h6_raw_s942201"),
        (4, "set_raw", "SET", "raw", 943201,
         "s1_action_law_b03_set_raw_s943201",
         "s1_action_law_b03_set_clip_s943201"),
    ]
    assert DEFAULT_SPEC == replace(
        DEFAULT_SPEC,
        train_n=6,
        test_ns=(4, 6, 8),
        horizon=500,
        train_lanes=16,
        eval_lanes=16,
        rollouts=45,
        panels=(0, 15, 30, 45),
        torch_threads=4,
    )


def test_real_tiny_four_cells_pair_initialization_update_and_evaluate(completed_cells):
    results, replay_actions = completed_cells
    for key, result in results.items():
        assert result["status"] == "complete" and result["fit_started"]
        assert result["counts"] == {
            "training_team_steps": 24,
            "stored_team_steps": 24,
            "training_episodes": 2,
            "terminal_resets": 2,
            "updates": 1,
            "evaluation_team_steps": 144,
            "evaluation_episodes": 12,
        }
        assert result["config"]["k"] == 10
        assert result["config"]["lambda_l"] == .05
        assert result["action_distribution"] == {
            "kind": "gaussian", "lambda_l": .05,
            "mapping_is_environment_only": True,
        }
        assert result["initial_raw_sigma"] == [1.0, 1.0, 1.0]
        assert result["rollouts"][0]["action_motion_telemetry"][
            "decision_step_indices_zero_based"
        ] == [0, 10]
        motion = result["rollouts"][0]["action_motion_telemetry"]
        assert motion["position_storage_dtypes"] == ["float64"]
        component_means = motion["native_component_means_per_world"]
        np.testing.assert_allclose(
            np.asarray(component_means["total_reward"]),
            6 * np.asarray(result["rollouts"][0]["training_scalar_returns"]) / 12,
            rtol=1e-6, atol=1e-7,
        )
        assert replay_actions[key]
        assert any(np.abs(actions).max() > 1.0 for actions in replay_actions[key])
        for name in ("discoverer_actor", "discoverer_critic"):
            assert result["optimizer_calls"][name] > 0
            assert result["parameter_motion"][name]["delta_l2"] > 0
        assert len(result["panels"]) == 6
        for panel in result["panels"]:
            assert panel["status"] == "complete"
            assert panel["config"]["n_agents"] == panel["test_n"]
            assert panel["executed_action_bounds"]["minimum"] >= -1.0
            assert panel["executed_action_bounds"]["maximum"] <= 1.0
            assert not any(panel["optimizer_calls"].values())

    for first, second in (("h6_raw", "h6_clip"), ("set_clip", "set_raw")):
        left, right = results[first], results[second]
        assert (
            left["observed_initial_parameter_normalizer_digest"]
            == right["observed_initial_parameter_normalizer_digest"]
            == right["expected_initial_parameter_normalizer_digest"]
        )
        assert left["config"] == right["config"]


@pytest.mark.parametrize("cell_key", ["h6_clip", "set_clip"])
def test_intentional_overrange_sample_stays_raw_in_storage_and_replay(tmp_path, cell_key):
    cell = runner.CELL_BY_KEY[cell_key]
    spec = replace(TECH_SPEC, panels=())
    runner.seed_rng(cell.seed)
    envs = make_envs(spec.train_lanes, cell.seed, spec.train_n, spec.horizon)
    try:
        config = make_config(cell.arm, envs, cell.seed, spec)
        agent = build_agent(config, str(tmp_path / f"logs-{cell_key}"))
        output = agent.skill_discoverer.actor.act.action_out
        with torch.no_grad():
            output.fc_mean.weight.zero_()
            output.fc_mean.bias.fill_(1.5)
            output.logstd._bias.fill_(-10.0)

        replayed = []
        original = agent.skill_discoverer.actor.evaluate_actions

        def wrapped(_actor, observations, initial_hxs, actions, masks, skills):
            replayed.append(actions.detach().cpu().numpy().copy())
            return original(observations, initial_hxs, actions, masks, skills)

        agent.skill_discoverer.actor.evaluate_actions = types.MethodType(
            wrapped, agent.skill_discoverer.actor
        )
        terminal_successors = []
        for lane, env in enumerate(envs):
            original_step = env.step

            def capture_terminal(action, *, step=original_step, lane_index=lane):
                observation, reward, term, trunc, info = step(action)
                if term or trunc:
                    terminal_successors.append({
                        "lane": lane_index,
                        "state": np.asarray(info["next_state"]).copy(),
                        "observation": np.asarray(observation).copy(),
                    })
                return observation, reward, term, trunc, info

            env.step = capture_terminal
        stored_terminal_successors = []
        original_store = agent.store_transition_batch

        def capture_store(*args, **kwargs):
            result = original_store(*args, **kwargs)
            for lane in np.flatnonzero(np.asarray(kwargs["dones"])):
                stored_terminal_successors.append({
                    "lane": int(lane),
                    "state": np.asarray(kwargs["next_states"])[lane].copy(),
                    "observation": np.asarray(kwargs["next_observations"])[lane].copy(),
                })
            return result

        agent.store_transition_batch = capture_store
        states, observations = runner.reset_all(envs)
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary = {"counts": {
            "training_team_steps": 0, "training_episodes": 0,
            "terminal_resets": 0, "stored_team_steps": 0,
        }}
        states, observations, _steps, dones, telemetry, _returns = runner.collect_rollout(
            agent, envs, states, observations, steps, dones, cell, 1, summary, spec
        )
        witness = telemetry["first_overrange_witness"]
        assert witness["stored_action_exact"] and witness["stored_old_logprob_exact"]
        assert np.max(np.abs(witness["raw_action"])) > 1.0
        assert np.max(np.abs(witness["executed_action"])) <= 1.0
        np.testing.assert_allclose(
            witness["position_after"], witness["predicted_position_after"], rtol=0, atol=0
        )
        assert np.isclose(
            spec.train_n * witness["reward"], witness["native_components"]["total_reward"],
            rtol=1e-6, atol=1e-7,
        )
        assert witness["transition_indexing"].endswith("indices are zero-based")
        assert len(terminal_successors) == len(stored_terminal_successors) == spec.train_lanes
        for physical, stored in zip(
            sorted(terminal_successors, key=lambda row: row["lane"]),
            sorted(stored_terminal_successors, key=lambda row: row["lane"]),
        ):
            assert physical["lane"] == stored["lane"]
            np.testing.assert_array_equal(physical["state"], stored["state"])
            np.testing.assert_array_equal(physical["observation"], stored["observation"])

        sampler_state = agent.rollout_buffer.get_sampler_rng_state()
        batch = next(agent.rollout_buffer.get_discoverer_sampler(
            1, spec.sequence_batch_size, chunk_length=config.k,
            device=agent.device, cache_tensors=False,
        ))
        agent.rollout_buffer.set_sampler_rng_state(sampler_state)
        observations_seq = batch["observations"].to(agent.device)
        central_input = None
        if agent.use_central_snapshot:
            central_input = agent._central_actor_input_from_replay(
                batch["central_snapshot_states"].to(agent.device),
                batch["central_snapshot_obs"].to(agent.device),
                batch["central_ego_indices"].to(agent.device),
            )
        actor_observations = agent.skill_discoverer._apply_central_input(
            agent.skill_discoverer._apply_compact_context(
                observations_seq, None, agent.skill_discoverer.actor_context_adapter,
            ),
            central_input,
        )
        dones_seq = batch["dones"].to(agent.device)
        masks = torch.ones_like(dones_seq, dtype=torch.float32)
        masks[1:] = 1.0 - dones_seq[:-1].float()
        with torch.no_grad():
            replay_logp, _entropy = original(
                actor_observations,
                batch["initial_hxs"].to(agent.device),
                batch["actions"].to(agent.device),
                masks,
                batch["agent_skills"].to(agent.device),
            )
        np.testing.assert_allclose(
            replay_logp.detach().cpu().numpy().squeeze(-1), batch["log_probs"].numpy(),
            rtol=2e-5, atol=2e-5,
        )
        agent.update(
            last_values=np.zeros((spec.train_lanes, spec.train_n), dtype=np.float32),
            dones=dones.copy(), steps_in_buffer=spec.horizon,
            last_state=states.copy(), last_observations=observations.copy(),
        )
        assert replayed and all(np.max(actions) > 1.0 for actions in replayed)
    finally:
        for env in envs:
            env.close()


def test_expected_initial_digest_mismatch_fails_before_eval_or_training(tmp_path):
    cell = runner.CELL_BY_KEY["h6_clip"]
    out = tmp_path / cell.tag
    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, "0" * 64,
        replace(TECH_SPEC, panels=()),
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed" and not result["fit_started"]
    assert "digest mismatch" in result["failure"]
    assert result["panels"] == []
    assert not any(result["counts"].values())


def test_partial_mid_rollout_failure_preserves_exact_progress(tmp_path):
    cell = runner.CELL_BY_KEY["h6_raw"]
    out = tmp_path / cell.tag

    def fail_at_three(event):
        if event["summary"]["counts"]["training_team_steps"] == 3:
            raise RuntimeError("injected step-three failure")

    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, None,
        replace(TECH_SPEC, panels=()), training_step_hook=fail_at_three,
    ) == 1
    result = _read(out / "summary.json")
    assert result["status"] == "failed"
    assert result["counts"]["training_team_steps"] == 3
    assert result["counts"]["stored_team_steps"] == 2
    assert result["counts"]["updates"] == 0
    assert result["incomplete_rollout"]["rollout"] == 1
    partial = result["incomplete_rollout"]["action_motion_telemetry_partial"]
    assert partial["team_steps"] == 3
    assert partial["raw_coordinate_violations"]["denominator"] == 54
    assert "step-three" in result["failure"]


def test_post_step_diagnostic_failure_retains_execution_but_not_diagnostic_count(
    tmp_path, monkeypatch,
):
    cell = runner.CELL_BY_KEY["h6_raw"]
    out = tmp_path / cell.tag

    def reject_components(*_args, **_kwargs):
        raise RuntimeError("injected component validation failure")

    monkeypatch.setattr(runner, "native_components", reject_components)
    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, None,
        replace(TECH_SPEC, panels=()),
    ) == 1
    result = _read(out / "summary.json")
    assert result["counts"]["training_team_steps"] == 1
    assert result["counts"]["stored_team_steps"] == 0
    partial = result["incomplete_rollout"]["action_motion_telemetry_partial"]
    assert partial["team_steps"] == 0
    assert partial["raw_coordinate_violations"]["denominator"] == 0


def test_evaluation_post_step_failure_retains_execution_count(tmp_path, monkeypatch):
    cell = runner.CELL_BY_KEY["h6_raw"]
    out = tmp_path / cell.tag

    def reject_components(*_args, **_kwargs):
        raise RuntimeError("injected evaluation component failure")

    monkeypatch.setattr(runner, "native_components", reject_components)
    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, None,
        replace(TECH_SPEC, panels=(0,)),
    ) == 1
    result = _read(out / "summary.json")
    assert not result["fit_started"]
    assert result["counts"]["evaluation_team_steps"] == 1
    assert result["panels"][0]["steps"] == 1


def test_update_failure_preserves_complete_collected_rollout(tmp_path):
    cell = runner.CELL_BY_KEY["set_clip"]
    out = tmp_path / cell.tag

    def break_update(agent):
        def fail_update(*_args, **_kwargs):
            raise RuntimeError("injected update failure")
        agent.update = fail_update

    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, None,
        replace(TECH_SPEC, panels=()), agent_setup_hook=break_update,
    ) == 1
    result = _read(out / "summary.json")
    assert result["counts"]["training_team_steps"] == 24
    assert result["counts"]["stored_team_steps"] == 24
    assert result["counts"]["updates"] == 0
    evidence = result["incomplete_rollout"]
    assert evidence["phase"] == "updating_failed"
    assert evidence["action_motion_telemetry"]["team_steps"] == 24
    assert evidence["raw_sigma_before_update"] == [1.0, 1.0, 1.0]
    assert not any(evidence["optimizer_calls_observed"].values())
    assert "update failure" in result["failure"]


def test_post_store_integrity_failure_retains_successful_store_count(tmp_path):
    cell = runner.CELL_BY_KEY["h6_raw"]
    out = tmp_path / cell.tag

    def corrupt_after_store(agent):
        original_store = agent.store_transition_batch

        def corrupt(*args, **kwargs):
            result = original_store(*args, **kwargs)
            t = int(kwargs["rollout_step_idx"])
            agent.rollout_buffer.actions[t, 0, 0, 0] += 1.0
            return result

        agent.store_transition_batch = corrupt

    assert runner.run_fit(
        out, cell, "technical", {"sha": "technical"}, None,
        replace(TECH_SPEC, panels=()), agent_setup_hook=corrupt_after_store,
    ) == 1
    result = _read(out / "summary.json")
    assert result["counts"]["training_team_steps"] == 2
    assert result["counts"]["stored_team_steps"] == 2
    assert result["counts"]["updates"] == 0
    assert "buffer did not retain raw" in result["failure"]


def test_cli_admission_precedes_candidate_import_and_any_output(tmp_path, monkeypatch):
    calls = []

    def refuse(*_args, **_kwargs):
        calls.append("admission")
        raise RuntimeError("not admitted")

    monkeypatch.setattr(entry, "require_admission", refuse)
    cell = runner.CELL_BY_KEY["h6_raw"]
    out = tmp_path / cell.tag
    with pytest.raises(RuntimeError, match="not admitted"):
        entry.main([
            "--cell", cell.key,
            "--launch-sha", "technical",
            "--out", str(out),
        ], run_fn=lambda *_args, **_kwargs: calls.append("run"))
    assert calls == ["admission"]
    assert not out.exists()


def test_cli_rejects_unbound_tag_and_missing_pair_digest(tmp_path):
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", "h6_raw", "--launch-sha", "x",
            "--out", str(tmp_path / "wrong"),
        ])
    cell = runner.CELL_BY_KEY["set_raw"]
    with pytest.raises(SystemExit):
        entry.main([
            "--cell", cell.key, "--launch-sha", "x",
            "--out", str(tmp_path / cell.tag),
        ])
