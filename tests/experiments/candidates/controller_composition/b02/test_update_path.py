import copy
import json
import os
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.bounded_confirmation_b15 import runner as b15
from experiments.candidates.agent_count_generalization.configuration import FitSpec
from experiments.candidates.agent_count_generalization.local_ordinary_b16 import runner as b16
from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20.runner import Arm
from experiments.candidates.agent_count_generalization.runner import digest_agent, model_modules, seed_rng
from experiments.candidates.controller_composition.b01.bindings import CHECKPOINT_ROOT, SOURCE
from experiments.candidates.controller_composition.b01.runner import restore_runtime, validate_sources
from experiments.candidates.controller_composition.b02.update_path import learner_buffer, store_learner_step, update_learner


def _source_paths():
    override = os.environ.get("HMASD_CONTROLLER_COMPOSITION_CHECKPOINTS")
    if override:
        values = json.loads(override)
        if len(values) != 3:
            raise ValueError("three B01 checkpoint paths required")
        return dict(zip(SOURCE, map(Path, values)))
    return {i: Path(CHECKPOINT_ROOT) / row["tag"] / "F/raw/checkpoint_45.pt" for i, row in SOURCE.items()}


def _reference_returns(rewards, values, dones, gamma=.99, gae=.95):
    advantage = np.zeros_like(values)
    last = np.zeros_like(values[0])
    for t in reversed(range(len(values))):
        next_val = np.zeros_like(last) if t == len(values) - 1 else values[t + 1]
        nonterminal = 1.0 - dones[t]
        last = rewards[t] + gamma * next_val * nonterminal - values[t] + gamma * gae * nonterminal * last
        advantage[t] = last
    return advantage + values


def test_native_partner_collector_compact_gae_sampler_and_real_optimizer(tmp_path, current_main_source_validation):
    with current_main_source_validation():
        sources, _ = validate_sources(_source_paths())
    torch.set_num_threads(4)
    seed_rng(92_526_001)
    envs = make_envs(2, 81, 6, 20)
    try:
        spec = FitSpec(horizon=20, train_lanes=2, eval_lanes=2, rollouts=1)
        config = b16.make_b16_config(Arm("F", 92_526_001), envs, spec, expected_n=6)
        learner = b16.build_local_agent(config, str(tmp_path / "learner"))
        learner.train(True)
        partner_config = b16.make_b16_config(Arm("F", SOURCE[1]["seed"]), envs, spec, expected_n=6)
        partner = restore_runtime(partner_config, sources[1]["checkpoint"],
                                  sources[1]["expected_digest"], tmp_path / "partner")
        partner_before = digest_agent(partner)
        compact = learner_buffer(learner, horizon=20, lanes=2)
        perturbed = learner_buffer(learner, horizon=20, lanes=2)
        pairs = [env.reset(seed=81 + lane) for lane, env in enumerate(envs)]
        states = np.stack([info["state"] for _, info in pairs])
        observations = np.stack([obs for obs, _ in pairs])
        steps, dones = np.zeros(2, dtype=np.int64), np.zeros(2, dtype=bool)
        first_raw, first_logprob = None, None
        with torch.no_grad():
            for t in range(20):
                raw, _, data = learner.step(states, observations, steps, dones,
                                            deterministic=False, return_step_data=True, build_infos=False)
                actor_pre = [learner.get_prev_actor_hidden_np(lane, n_agents=6)[:3].copy() for lane in range(2)]
                critic_pre = [learner.get_prev_critic_hidden_np(lane, n_agents=6)[:3].copy() for lane in range(2)]
                if t == 0:
                    first_raw, first_logprob = raw[:, :3].copy(), np.asarray(data["action_logprobs"])[:, :3].copy()
                with b03.preserve_rng():
                    frozen, _, _ = partner.step(states, observations, steps, dones,
                                                deterministic=True, return_step_data=True, build_infos=False)
                executed = b03.map_training_actions(np.concatenate((raw[:, :3], frozen[:, 3:]), axis=1), "clip")
                next_pairs = [env.step(executed[lane]) for lane, env in enumerate(envs)]
                rewards = np.asarray([row[1] for row in next_pairs], dtype=np.float32)
                next_dones = np.asarray([row[2] or row[3] for row in next_pairs], dtype=bool)
                store_learner_step(compact, learner, t=t, states=states,
                                   observations=observations, raw_actions=raw,
                                   step_data=data, scalar_rewards=rewards, dones=next_dones)
                changed_obs, changed_raw = observations.copy(), raw.copy()
                changed_data = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in data.items()}
                changed_obs[:, 3:] += 100
                changed_raw[:, 3:] += 100
                changed_data["action_logprobs"][:, 3:] += 100
                changed_data["values"][:, 3:] += 100
                changed_data["agent_skills"][:, 3:] = 0
                store_learner_step(perturbed, learner, t=t, states=states,
                                   observations=changed_obs, raw_actions=changed_raw,
                                   step_data=changed_data, scalar_rewards=rewards, dones=next_dones)
                assert np.array_equal(compact.gru_hidden_states[t], np.stack(actor_pre))
                assert np.array_equal(compact.critic_gru_hidden_states[t], np.stack(critic_pre))
                states = np.stack([row[4]["next_state"] for row in next_pairs])
                observations = np.stack([row[0] for row in next_pairs])
                dones, steps = next_dones, steps + 1
        assert dones.all() and compact.n_agents == 3 and compact.state_dim == 133
        assert compact.masks.all() and compact.actions.shape == (20, 2, 3, 3)
        assert np.array_equal(compact.actions[0], first_raw)
        assert np.array_equal(compact.log_probs[0], first_logprob)
        assert np.count_nonzero(compact.gru_hidden_states[10]) > 0
        assert np.count_nonzero(compact.critic_gru_hidden_states[10]) > 0
        for key in ("states", "obs", "actions", "rewards", "dones", "values", "log_probs",
                    "gru_hidden_states", "critic_gru_hidden_states", "agent_skills"):
            assert np.array_equal(getattr(compact, key), getattr(perturbed, key)), key
        expected_returns = _reference_returns(compact.rewards.copy(), compact.values.copy(), compact.dones.copy())
        compact.compute_advantages(np.zeros((2, 3), dtype=np.float32), dones, gamma=.99, gae_lambda=.95)
        assert compact.returns == pytest.approx(expected_returns, abs=1e-6)
        sampler_before = copy.deepcopy(compact._sampler_rng.bit_generator.state)
        batches = list(compact.get_discoverer_sampler(1, 32, chunk_length=10, device="cpu"))
        assert len(batches) == 1
        batch = batches[0]
        assert batch["actions"].shape == (10, 12, 3)
        assert batch["masks"].all()
        expected_entries = []
        for chunk in (0, 1):
            for lane in range(2):
                for role in range(3):
                    expected_entries.append((compact.actions[10 * chunk, lane, role],
                                             compact.gru_hidden_states[10 * chunk, lane, role],
                                             compact.critic_gru_hidden_states[10 * chunk, lane, role],
                                             compact.states[10 * chunk, lane]))
        unmatched = list(range(12))
        for j in range(12):
            action = batch["actions"][0, j].numpy()
            candidates = [idx for idx in unmatched if np.array_equal(action, expected_entries[idx][0])]
            assert len(candidates) == 1
            idx = candidates[0]
            unmatched.remove(idx)
            assert np.array_equal(batch["initial_hxs"][j].numpy(), expected_entries[idx][1])
            assert np.array_equal(batch["initial_critic_hxs"][j].numpy(), expected_entries[idx][2])
            assert np.array_equal(batch["global_states"][0, j].numpy(), expected_entries[idx][3])
        assert not unmatched
        compact._sampler_rng.bit_generator.state = copy.deepcopy(sampler_before)
        twin = b16.build_local_agent(config, str(tmp_path / "twin"))
        twin.train(True)
        for name, module in model_modules(twin).items():
            module.load_state_dict(model_modules(learner)[name].state_dict(), strict=True)
        # Nontrivial normalized baseline is identical in both agents; only valid learner returns may update it.
        for model in (learner, twin):
            model.value_norm_discoverer.mean = 1.25
            model.value_norm_discoverer.var = 2.5
            model.value_norm_discoverer.count = 7.0
        assert digest_agent(twin) == digest_agent(learner)
        assert learner.value_norm_discoverer.mean == 1.25
        before = digest_agent(learner)
        captured = []
        original_update = learner.value_norm_discoverer.update
        def record_update(values):
            captured.append(np.asarray(values).copy())
            return original_update(values)
        learner.value_norm_discoverer.update = record_update
        with pytest.raises(ValueError, match="terminal"):
            update_learner(learner, compact, np.array([True, False]))
        assert not captured
        missing = compact.masks[10, 1]
        compact.masks[10, 1] = False
        with pytest.raises(ValueError, match="missing rows"):
            update_learner(learner, compact, dones)
        assert not captured
        compact.masks[10, 1] = missing
        perturbed._sampler_rng.bit_generator.state = copy.deepcopy(sampler_before)
        seed_rng(33)
        losses, audit = update_learner(learner, compact, dones)
        del learner.value_norm_discoverer.update
        seed_rng(33)
        twin_losses, twin_audit = update_learner(twin, perturbed, dones)
        assert len(captured) == 1
        assert captured[0] == pytest.approx(expected_returns.reshape(-1), abs=1e-6)
        assert digest_agent(learner) != before
        assert digest_agent(twin) == digest_agent(learner)
        assert b15._optimizer_state_digest(twin) == b15._optimizer_state_digest(learner)
        assert twin_losses == pytest.approx(losses)
        assert twin_audit == audit
        assert digest_agent(partner) == partner_before
        assert audit["expected_sequences_per_epoch"] == 12
        assert audit["minibatches"] == 15 and audit["sampled_sequences"] == 180
        assert len(losses) >= 4
        sampler_after = copy.deepcopy(compact._sampler_rng.bit_generator.state)
        assert sampler_after != sampler_before
        compact.reset()
        assert compact._sampler_rng.bit_generator.state == sampler_after
    finally:
        for env in envs:
            env.close()
