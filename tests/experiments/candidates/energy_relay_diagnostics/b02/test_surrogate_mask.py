"""Focused transport, loss, admission and endpoint-contract checks for B02."""

from __future__ import annotations

import copy
import json
import random
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from configs.config_1 import Config
from experiments.candidates.energy_relay_benchmark.b02 import checkpoint_eval
from experiments.candidates.energy_relay_benchmark.b02 import configuration as b02_cfg
from experiments.candidates.energy_relay_benchmark.b02 import training as b02_training
from experiments.candidates.energy_relay_diagnostics.b02 import runner
from experiments.candidates.energy_relay_diagnostics.b02 import training as mask_training
from experiments.candidates.uav_service_auxiliary.b01.native import seed_everything
from hmasd.agent import HMASDAgent, _masked_policy_surrogate_loss
from hmasd.utils import RolloutBuffer


def _filled_buffer(*, sampler_seed=73, with_mask):
    buffer = RolloutBuffer(
        num_steps=4,
        num_envs=2,
        n_agents=2,
        obs_dim=3,
        action_dim=1,
        gru_hidden_size=2,
        n_Z=1,
        n_z=1,
        state_dim=3,
        sampler_seed=sampler_seed,
    )
    if with_mask:
        buffer.enable_policy_surrogate_mask()
    expected = np.zeros((4, 2, 2), dtype=np.bool_)
    for step in range(4):
        for env in range(2):
            codes = np.asarray([100 * step + 10 * env + agent + 1 for agent in range(2)])
            assert buffer.add(
                t=step,
                env_idx=env,
                state=np.asarray([env, step, 0.25], dtype=np.float32),
                obs=np.full((2, 3), step + env, dtype=np.float32),
                action=codes[:, None].astype(np.float32),
                reward=np.zeros(2, dtype=np.float32),
                done=np.zeros(2, dtype=np.bool_),
                value=np.zeros(2, dtype=np.float32),
                log_prob=np.zeros(2, dtype=np.float32),
                gru_hidden_state=np.zeros((2, 2), dtype=np.float32),
                critic_gru_hidden_state=np.zeros((2, 2), dtype=np.float32),
                team_skill=0,
                agent_skills=np.zeros(2, dtype=np.int64),
            )
            expected[step, env] = (step + env + np.arange(2)) % 2 == 0
    if with_mask:
        for step in range(4):
            buffer.set_policy_surrogate_mask(step, expected[step])
    return buffer, expected


@pytest.mark.parametrize("cache_tensors", [False, True])
def test_sampler_mask_preserves_agent_sequence_order_and_default_rng(cache_tensors):
    ordinary, _ = _filled_buffer(with_mask=False)
    masked, expected = _filled_buffer(with_mask=True)
    ordinary_rng = copy.deepcopy(ordinary._sampler_rng.bit_generator.state)
    masked_rng = copy.deepcopy(masked._sampler_rng.bit_generator.state)
    ordinary_batches = list(ordinary.get_discoverer_sampler(
        ppo_epochs=2,
        num_sequences_per_batch=4,
        chunk_length=2,
        device="cpu" if cache_tensors else None,
        cache_tensors=cache_tensors,
    ))
    masked_batches = list(masked.get_discoverer_sampler(
        ppo_epochs=2,
        num_sequences_per_batch=4,
        chunk_length=2,
        device="cpu" if cache_tensors else None,
        cache_tensors=cache_tensors,
    ))
    assert len(ordinary_batches) == len(masked_batches) == 4
    assert all("policy_surrogate_include_mask" not in batch for batch in ordinary_batches)
    for ordinary_batch, masked_batch in zip(ordinary_batches, masked_batches):
        assert torch.equal(ordinary_batch["actions"], masked_batch["actions"])
        assert masked_batch["policy_surrogate_include_mask"].shape == masked_batch["masks"].shape
        actions = masked_batch["actions"][..., 0].cpu().numpy().astype(np.int64)
        include = masked_batch["policy_surrogate_include_mask"].cpu().numpy()
        for sequence in range(actions.shape[1]):
            encoded = int(actions[0, sequence])
            chunk_start = encoded // 100
            lane_agent = encoded - (encoded // 100) * 100 - 1
            env, agent = divmod(lane_agent, 10)
            for offset in range(2):
                step = chunk_start + offset
                next_code = int(actions[offset, sequence])
                assert next_code // 100 == step
                assert include[offset, sequence] == expected[step, env, agent]
    assert ordinary._sampler_rng.bit_generator.state == masked._sampler_rng.bit_generator.state
    assert ordinary._sampler_rng.bit_generator.state != ordinary_rng
    assert masked._sampler_rng.bit_generator.state != masked_rng


def test_masked_surrogate_keeps_all_valid_rows_in_loss_and_gradient_denominator():
    terms = torch.tensor([2.0, -1.0, 3.0, 4.0], requires_grad=True)
    include = torch.tensor([True, False, True, False])
    loss = _masked_policy_surrogate_loss(terms, include, valid_count=4)
    assert loss.item() == pytest.approx(-1.25)
    gradient, = torch.autograd.grad(loss, terms)
    torch.testing.assert_close(gradient, torch.tensor([-0.25, 0.0, -0.25, 0.0]))

    ordinary_loss = -terms.detach().mean()
    assert ordinary_loss.item() == pytest.approx(-2.0)
    all_masked = _masked_policy_surrogate_loss(
        terms, torch.zeros(4, dtype=torch.bool), valid_count=4
    )
    assert all_masked.item() == 0.0
    with pytest.raises(ValueError, match="denominator"):
        _masked_policy_surrogate_loss(terms, include, valid_count=2)
    with pytest.raises(ValueError, match="bool vector"):
        _masked_policy_surrogate_loss(terms, include.float(), valid_count=4)


def _tiny_learner(tmp_path, *, with_mask, mask_direct=None, shielded_rows=()):
    config = Config()
    config.seed = 20260927
    config.num_envs = 2
    config.rollout_length = 4
    config.episode_length = 4
    config.max_steps = 4
    config.k = 2
    config.n_Z = 2
    config.n_z = 2
    config.action_dim = 1
    config.hidden_size = 16
    config.embedding_dim = 16
    config.n_heads = 4
    config.n_encoder_layers = 1
    config.n_decoder_layers = 1
    config.gru_hidden_size = 16
    config.ppo_epochs = 1
    config.sequence_batch_size = 8
    config.use_obsnorm = False
    config.use_statenorm = False
    config.use_valuenorm = True
    config.ordinary_completed_segments = False
    config.update_env_dims(state_dim=5, obs_dim=3, n_agents=2)
    device = torch.device("cpu")
    seed_everything(config.seed, device)
    agent = HMASDAgent(config, log_dir=str(tmp_path / "logs"), device=device)
    buffer = agent.rollout_buffer
    if with_mask:
        buffer.enable_policy_surrogate_mask()
    include = np.ones((4, 2, 2), dtype=np.bool_)
    for step in range(4):
        for lane in range(2):
            obs = np.asarray([
                [step * 0.1 + lane, role * 0.2, 1.0]
                for role in range(2)
            ], dtype=np.float32)
            assert buffer.add(
                t=step,
                env_idx=lane,
                state=np.asarray([step * 0.1, lane, 0.5, -0.25, 1.0], dtype=np.float32),
                obs=obs,
                action=np.asarray([[0.1 + role * 0.05] for role in range(2)], dtype=np.float32),
                reward=np.asarray([step + lane + role * 0.5 for role in range(2)], dtype=np.float32),
                done=np.full(2, step == 3, dtype=np.bool_),
                value=np.asarray([lane * 0.1, step * 0.1], dtype=np.float32),
                log_prob=np.zeros(2, dtype=np.float32),
                gru_hidden_state=np.zeros((2, config.gru_hidden_size), dtype=np.float32),
                critic_gru_hidden_state=np.zeros((2, config.gru_hidden_size), dtype=np.float32),
                team_skill=0,
                agent_skills=np.zeros(2, dtype=np.int64),
            )
    for row in shielded_rows:
        step, lane, role = row
        include[step, lane, role] = False
    if with_mask:
        for step in range(4):
            buffer.set_policy_surrogate_mask(step, include[step])
    if mask_direct is not None:
        agent._shield_surrogate_experiment = {
            "mask_direct_policy_surrogate": bool(mask_direct),
            "capture_gradient_probe": True,
        }
        agent._shield_surrogate_gradient_probe_done = False
    return agent


def _run_tiny_update(agent):
    return agent.update_discoverer_from_rollout(
        last_values=np.zeros((2, 2), dtype=np.float32),
        dones=np.ones(2, dtype=np.bool_),
    )


def _assert_module_state_equal(left, right):
    left_state, right_state = left.state_dict(), right.state_dict()
    assert left_state.keys() == right_state.keys()
    for key in left_state:
        torch.testing.assert_close(left_state[key], right_state[key], rtol=0.0, atol=0.0)


def test_real_update_default_matches_unmasked_instrumentation_and_mask_changes_only_actor(
    tmp_path
):
    torch.set_num_threads(1)
    ordinary = _tiny_learner(tmp_path / "ordinary", with_mask=False, mask_direct=None)
    ordinary_result = _run_tiny_update(ordinary)
    torch_state_after_ordinary = torch.random.get_rng_state().clone()
    numpy_state_after_ordinary = copy.deepcopy(np.random.get_state())
    python_state_after_ordinary = random.getstate()
    ordinary_sampler_after = ordinary.rollout_buffer.get_sampler_rng_state()

    instrumented = _tiny_learner(
        tmp_path / "instrumented", with_mask=True, mask_direct=False
    )
    instrumented_result = _run_tiny_update(instrumented)
    assert instrumented.shield_surrogate_update_metrics["valid_action_sample_presentations"] == 16
    assert instrumented.shield_surrogate_update_metrics["shielded_action_sample_presentations"] == 0
    assert instrumented.shield_surrogate_gradient_probe["valid_rows_and_denominator"] == 16
    assert instrumented.shield_surrogate_gradient_probe["shielded_rows"] == 0
    for left, right in zip(ordinary_result, instrumented_result):
        assert left == pytest.approx(right, rel=0.0, abs=0.0)
    _assert_module_state_equal(ordinary.skill_discoverer.actor, instrumented.skill_discoverer.actor)
    _assert_module_state_equal(ordinary.skill_discoverer.critic, instrumented.skill_discoverer.critic)
    assert ordinary.rollout_buffer.get_sampler_rng_state() == instrumented.rollout_buffer.get_sampler_rng_state()
    assert torch.equal(torch_state_after_ordinary, torch.random.get_rng_state())
    numpy_state_after_instrumented = np.random.get_state()
    assert numpy_state_after_ordinary[0] == numpy_state_after_instrumented[0]
    assert np.array_equal(numpy_state_after_ordinary[1], numpy_state_after_instrumented[1])
    assert numpy_state_after_ordinary[2:] == numpy_state_after_instrumented[2:]
    assert python_state_after_ordinary == random.getstate()
    assert ordinary_sampler_after == instrumented.rollout_buffer.get_sampler_rng_state()

    masked = _tiny_learner(
        tmp_path / "masked",
        with_mask=True,
        mask_direct=True,
        shielded_rows=((0, 0, 0), (2, 1, 1)),
    )
    masked_result = _run_tiny_update(masked)
    metrics = masked.shield_surrogate_update_metrics
    assert metrics["valid_action_sample_presentations"] == 16
    assert metrics["shielded_action_sample_presentations"] == 2
    assert metrics["optimizer_updates"] == 1
    assert masked.shield_surrogate_gradient_probe["valid_rows_and_denominator"] == 16
    assert masked.shield_surrogate_gradient_probe["shielded_rows"] == 2
    assert np.isfinite(masked.shield_surrogate_gradient_probe[
        "masked_direct_policy_gradient_l2_preclip"
    ])
    assert metrics["combined_actor_gradient_l2_max_preclip"] >= 0.0
    assert masked_result[2] == pytest.approx(ordinary_result[2], rel=0.0, abs=0.0)
    assert masked_result[1] != pytest.approx(ordinary_result[1], rel=0.0, abs=1e-12)
    assert any(
        not torch.equal(left, right)
        for left, right in zip(
            ordinary.skill_discoverer.actor.parameters(), masked.skill_discoverer.actor.parameters()
        )
    )
    _assert_module_state_equal(ordinary.skill_discoverer.critic, masked.skill_discoverer.critic)
    assert ordinary.value_norm_discoverer.mean == masked.value_norm_discoverer.mean
    assert ordinary.value_norm_discoverer.var == masked.value_norm_discoverer.var
    assert ordinary.value_norm_discoverer.count == masked.value_norm_discoverer.count


@pytest.mark.parametrize("mask_direct", [False, True])
def test_collector_adapter_uses_returned_shield_mode_even_when_action_is_equal(
    monkeypatch, mask_direct
):
    modes_by_step = (
        np.asarray([True, False], dtype=np.bool_),
        np.asarray([False, True], dtype=np.bool_),
    )
    captured_masks = []
    step_counts = {"updates": 0}

    class Agent:
        def __init__(self):
            self.rollout_buffer = RolloutBuffer(
                2, 1, 2, 3, 1, 2, 1, 1, 3, sampler_seed=9
            )

        def store_transition_batch(self, *, rollout_step_idx):
            self.rollout_buffer.masks[int(rollout_step_idx), 0] = True

    agent = Agent()
    config = SimpleNamespace(num_envs=1, rollout_length=2, n_agents=2, k=1, ppo_epochs=1)
    spec = SimpleNamespace(lanes=1, rollout_length=2, rollouts=1, transitions=2)
    submitted = np.zeros((2, 1), dtype=np.float32)

    def fake_feedback(_obs, actions, _previous_modes):
        index = len(captured_masks)
        modes = modes_by_step[index]
        # Equal submitted/proposal values demonstrate why inequality is not the mask source.
        return SimpleNamespace(modes=modes.copy(), submitted_actions=actions.copy())

    def fake_collect(_agent, _config, _spec, *, after_rollout, **kwargs):
        record = {"f_mode_uav_steps": 2, "submitted_commands": 4}
        for step in range(2):
            decision = b02_training.apply_feedback(None, submitted.copy(), np.zeros(2, dtype=bool))
            agent.store_transition_batch(rollout_step_idx=step)
            captured_masks.append(
                agent.rollout_buffer.policy_surrogate_include_mask[step, 0].copy()
            )
            assert np.array_equal(decision.submitted_actions, submitted)
        agent.shield_surrogate_update_metrics = {
            "valid_action_sample_presentations": 4,
            "shielded_action_sample_presentations": 2,
            "unshielded_action_sample_presentations": 2,
            "shielded_action_sample_fraction": 0.5,
            "direct_surrogate_mask_enabled": bool(mask_direct),
            "policy_loss_denominator": "all valid PPO action rows before shield mask",
            "optimizer_updates": 1,
            "combined_actor_gradient_l2_rms_preclip": 1.0,
            "combined_actor_gradient_l2_max_preclip": 1.0,
            "actor_gradient_clip_fraction": 0.0,
        }
        step_counts["updates"] = 1
        agent.rollout_buffer.reset()
        after_rollout(1, record)
        return {"counts": {"transitions": 2, "rollouts": 1}, "rollouts": [record]}

    monkeypatch.setattr(b02_training, "apply_feedback", fake_feedback)
    monkeypatch.setattr(b02_training, "collect_and_train", fake_collect)
    monkeypatch.setattr(mask_training, "optimizer_steps", lambda _agent: {
        "low_actor": step_counts["updates"], "low_critic": step_counts["updates"],
        "high": 0, "team_discriminator": 0, "individual_discriminator": 0,
    })

    result = mask_training.collect_with_policy_surrogate_mask(
        agent,
        config,
        spec,
        mask_direct_policy_surrogate=mask_direct,
        start_rollout=0,
        start_transitions=0,
        env_seed=77,
    )
    assert [row.tolist() for row in captured_masks] == [[False, True], [True, False]]
    rollout = result["rollouts"][0]
    assert rollout["full_override_action_rows"] == 2
    assert rollout["shield_surrogate"]["shielded_action_sample_presentations"] == 2
    assert rollout["shield_surrogate"]["direct_surrogate_mask_enabled"] is mask_direct
    assert getattr(agent, "_shield_surrogate_experiment")["mask_direct_policy_surrogate"] is mask_direct


def test_runner_admission_precedes_thread_changes_and_training(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    out = tmp_path / "not-created"
    monkeypatch.setenv("OMP_NUM_THREADS", "before")
    monkeypatch.setattr(
        hmasd_admission,
        "require_admission",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("admission refused")),
    )
    with pytest.raises(RuntimeError, match="admission refused"):
        runner.main([
            "train", "--arm", "ordinary", "--seed", str(runner.SEED),
            "--launch-sha", "sha", "--out", str(out), "--device", "cpu",
        ])
    assert not out.exists()
    assert __import__("os").environ["OMP_NUM_THREADS"] == "before"


def test_runner_dispatches_only_after_matching_admission(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    calls = []
    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *_a, **_k: {"sha": "ok"})
    monkeypatch.setattr(runner, "train_continuation", lambda **kwargs: calls.append(kwargs) or "done")
    result = runner.main([
        "train", "--arm", "masked", "--seed", str(runner.SEED),
        "--launch-sha", "ok", "--out", str(tmp_path / "run"), "--device", "cpu",
    ])
    assert result == "done"
    assert calls == [{
        "arm": "masked", "seed": runner.SEED, "launch_sha": "ok",
        "out": Path(tmp_path / "run"), "device_name": "cpu", "threads": 4,
    }]


def test_value_norm_increment_preserves_checkpoint_pseudocount():
    start_count = 4_800_000.0001
    end_count = 7_200_000.0001
    assert runner._validate_value_norm_increment(
        start_count, end_count, expected_increment=2_400_000
    ) == pytest.approx(2_400_000, abs=1e-6)
    with pytest.raises(RuntimeError, match="expected 2400000 new action rows"):
        runner._validate_value_norm_increment(
            start_count, 7_199_999.0001, expected_increment=2_400_000
        )


def test_endpoint_pair_binds_the_fixed_development_panel_and_records_identity(
    tmp_path, monkeypatch
):
    calls = []
    checkpoints = {}
    for arm in ("ordinary", "masked"):
        checkpoint = tmp_path / arm / "endpoint"
        checkpoint.mkdir(parents=True)
        (checkpoint / "agent.pt").write_bytes((arm + " learner").encode())
        record = {
            "object_id": b02_cfg.OBJECT_ID,
            "programme": b02_cfg.PROGRAMME,
            "checkpoint": "endpoint",
            "rollout": runner.END_ROLLOUT,
            "transitions": runner.END_TRANSITIONS,
            "training_seed": runner.SEED,
            "agent_pt": "agent.pt",
            "agent_pt_sha256": checkpoint_eval.sha256_file(checkpoint / "agent.pt"),
            "policy_fingerprint": arm + "-fingerprint",
            "arm": arm,
            "source_agent_pt_sha256": runner.SOURCE_AGENT_SHA256,
        }
        (checkpoint / "record.json").write_text(json.dumps(record))
        checkpoints[arm] = checkpoint

    def fake_evaluate_checkpoint(**kwargs):
        calls.append(kwargs)
        summary_root = Path(kwargs["out"]) / "checkpoint-eval" / "endpoint_deterministic-stochastic"
        summary_root.mkdir(parents=True)
        (summary_root / "summary.json").write_text("{}")
        return {
            "status": "COMPLETE",
            "counts": {"episodes_completed": 64, "steps": 192000,
                       "panels_completed": 2, "failed_worlds": 0},
            "panels": {"deterministic": {"aggregate": {"mean_J": 1.0}},
                       "stochastic": {"aggregate": {"mean_J": 0.9}}},
        }

    monkeypatch.setattr(checkpoint_eval, "evaluate_checkpoint", fake_evaluate_checkpoint)
    out = tmp_path / "paired"
    summary = runner.evaluate_pair(
        ordinary_checkpoint=checkpoints["ordinary"],
        masked_checkpoint=checkpoints["masked"],
        launch_sha="eval-sha",
        out=out,
        workers=8,
        threads=2,
        device_name="cpu",
    )
    assert summary["status"] == "COMPLETE"
    assert summary["counts"] == {"episodes_completed": 128, "steps": 384000,
                                 "panels_completed": 4}
    assert len(calls) == 2
    for call in calls:
        assert call["worlds"] == checkpoint_eval.DEVELOPMENT_WORLDS
        assert call["modes"] == ("deterministic", "stochastic")
        assert call["final"] is False and call["horizon"] == 3000
        assert call["workers"] == 8 and call["threads"] == 2 and call["device_name"] == "cpu"
    assert (out / "paired_evaluation.json").is_file()
    paired = json.loads((out / "summary.json").read_text())
    assert paired["status"] == "COMPLETE"
    for arm in ("ordinary", "masked"):
        assert Path(paired["cells"][arm]["summary"]).is_file()
