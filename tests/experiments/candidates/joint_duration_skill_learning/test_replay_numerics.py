"""Frozen native-scale replay checks; no optimizer or physical transition."""
from copy import deepcopy
import json

import numpy as np
import pytest
import torch

from experiments.candidates.joint_duration_skill_learning import runner


def _intermediates(agent, events, *, double=False):
    coordinator = deepcopy(agent.skill_coordinator).double() if double else agent.skill_coordinator
    dtype = torch.float64 if double else torch.float32
    states = torch.as_tensor(np.stack([e.state for e in events]), device=agent.device, dtype=dtype)
    observations = torch.as_tensor(np.stack([e.observations for e in events]), device=agent.device, dtype=dtype)
    contexts = torch.as_tensor(np.stack([e.context for e in events]), device=agent.device, dtype=dtype)
    entities = coordinator._build_entity_sequence(states, observations)
    entities = entities.clone()
    entities[:, 0, :] += torch.tanh(coordinator.duration_context_projection(contexts))
    encoded = coordinator.encoder(entities)
    logits = coordinator.skill_decoder(encoded[:, :1], encoded[:, 1:])
    return entities.detach().cpu(), encoded.detach().cpu(), logits.detach().cpu()


@pytest.mark.parametrize("arm,asynchronous", [
    ("fixed", False), ("factored", False), ("ar", False),
    ("factored", True), ("ar", True),
])
def test_frozen_native_replay_grouping(arm, asynchronous, tmp_path):
    if not torch.cuda.is_available():
        pytest.skip("native CUDA grouping check")
    torch.set_num_threads(4)
    runner.seed_rng(2026092201)
    spec = runner.StudySpec(arm, 2026092201)
    envs = runner.native._make_envs(16, 850000, 6, 50, 500)
    try:
        agent = runner.DurationAgent(runner.make_config(spec, envs),
                                     log_dir=str(tmp_path / arm), device=torch.device("cuda"))
        agent.train(True)
        parameters = {k: v.detach().clone() for k, v in agent.skill_coordinator.state_dict().items()}
        counters = runner.count_optimizers(agent)
        groups = []
        for time_step in range(50):
            states, observations = runner.native._reset_all(envs)
            steps = np.full(16, time_step if asynchronous else 0, dtype=int)
            agent._batched_assign_skills_d2(states, observations, steps,
                                           np.zeros(16, dtype=bool), deterministic=False)
            active = np.flatnonzero(agent._d2_last_step["decision"])
            if len(active):
                groups.append([agent._new_event_record(i, time_step, agent.env_d2_last_decision[i])
                               for i in active])
        events = [event for group in groups for event in group]
        old, mask = agent._factor_tensors(events, agent.device)
        with torch.no_grad():
            grouped = torch.cat([agent._flatten_new_factors(agent._evaluate_events(g)) for g in groups])
            merged = agent._flatten_new_factors(agent._evaluate_events(events))
            small_intermediates = [_intermediates(agent, g) for g in groups]
            large_intermediates = _intermediates(agent, events)
        with torch.enable_grad():
            grad_merged = agent._flatten_new_factors(agent._evaluate_events(events)).detach()
        # An independent float64 encoder/decoder traversal locates rounding, without
        # changing the candidate policy or pretending this recreates the failed weights.
        with torch.no_grad():
            double_small = [_intermediates(agent, groups[i], double=True) for i in range(2)]
            double_merged = _intermediates(agent, groups[0] + groups[1], double=True)
        cpu_rng = torch.get_rng_state().clone()
        cuda_rng = [state.clone() for state in torch.cuda.get_rng_state_all()]
        # Closure-time order can differ from collection order. The production
        # auditor must reconstruct original groups, not treat adjacent rows as one.
        audit = agent.audit_event_replay(list(reversed(events)))
        assert audit["status"] == "passed"
        assert audit["grouped_max_abs_logprob_error"] <= 2e-5
        assert audit["merged_max_relative_probability_drift"] <= .001
        assert torch.equal(cpu_rng, torch.get_rng_state())
        assert all(torch.equal(a, b) for a, b in zip(cuda_rng, torch.cuda.get_rng_state_all()))
        details = {
            "arm": arm, "device": str(agent.device), "torch": torch.__version__,
            "production_audit": audit,
            "asynchronous": asynchronous, "events": len(events),
            "group_sizes": sorted(set(len(group) for group in groups)),
            "partial_eligibility_events": sum(not event.sampled_mask.all() for event in events),
            "matmul_precision": torch.get_float32_matmul_precision(),
            "tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
            "tf32_cudnn": torch.backends.cudnn.allow_tf32,
            "flash_sdp": torch.backends.cuda.flash_sdp_enabled(),
            "mem_efficient_sdp": torch.backends.cuda.mem_efficient_sdp_enabled(),
            "math_sdp": torch.backends.cuda.math_sdp_enabled(),
            "original_group_max_abs_logprob_error": float((grouped - old).abs()[mask].max()),
            "merged_max_abs_logprob_error": float((merged - old).abs()[mask].max()),
            "merged_max_relative_probability_error": float(torch.expm1(merged - old).abs()[mask].max()),
            "grad_merged_max_abs_logprob_error": float((grad_merged - old).abs()[mask].max()),
            "merged_grad_vs_no_grad": float((grad_merged - merged).abs()[mask].max()),
            "intermediate_max_abs_changes": {
                name: float((torch.cat([g[index] for g in small_intermediates]) - large_intermediates[index]).abs().max())
                for index, name in enumerate(("entities", "encoder", "team_logits"))
            },
            "float64_16_vs_32_intermediate_max_changes": {
                name: float((torch.cat([g[index] for g in double_small]) - double_merged[index]).abs().max())
                for index, name in enumerate(("entities", "encoder", "team_logits"))
            },
        }
        print("REPLAY_NUMERICS " + json.dumps(details, sort_keys=True), flush=True)
        assert details["original_group_max_abs_logprob_error"] <= 2e-5
        assert torch.isfinite(merged[mask]).all() and torch.isfinite(grad_merged[mask]).all()
        assert all(torch.equal(parameters[k], v) for k, v in agent.skill_coordinator.state_dict().items())
        assert all(value == 0 for value in runner.optimizer_counts(counters).values())
        assert agent.skill_coordinator.training
        if asynchronous:
            assert len(details["group_sizes"]) > 1
            assert details["partial_eligibility_events"] > 0
    finally:
        runner.close_envs(envs)
