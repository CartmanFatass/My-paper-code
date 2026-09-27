"""Direction-owned instrumentation around the published B02 collector contract."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.energy_relay_benchmark.b02 import training as b02_training
from experiments.candidates.uav_service_auxiliary.b01.native import optimizer_steps


def collect_with_policy_surrogate_mask(
    agent,
    config,
    spec,
    *,
    mask_direct_policy_surrogate: bool,
    after_rollout: Callable[[int, dict[str, Any]], None] | None = None,
    start_rollout: int,
    start_transitions: int,
    env_seed: int,
) -> dict[str, Any]:
    """Run the frozen B02 collector while recording each production shield-mode row.

    The collector's shield and storage calls are wrapped for the duration of this single-threaded
    call and restored in ``finally``.  The actual feedback function, submitted actions, stored
    proposal likelihood actions, reset sequence, RNG calls, bootstrap and optimizer update remain
    the B02 implementation.  The only new buffer value is a per-agent bool mask aligned to the
    same stored ``(time, environment, agent)`` row.
    """
    if int(config.num_envs) != int(spec.lanes):
        raise ValueError("mask recorder lane count differs from the B02 collector")
    if int(config.rollout_length) != int(spec.rollout_length):
        raise ValueError("mask recorder rollout length differs from the B02 collector")
    if not isinstance(mask_direct_policy_surrogate, (bool, np.bool_)):
        raise TypeError("mask_direct_policy_surrogate must be bool")

    agent._shield_surrogate_experiment = {
        "mask_direct_policy_surrogate": bool(mask_direct_policy_surrogate),
        "capture_gradient_probe": True,
    }
    agent._shield_surrogate_gradient_probe_done = False
    agent.shield_surrogate_gradient_probe = None
    agent.rollout_buffer.enable_policy_surrogate_mask()

    lanes, n_agents, rollout_length = int(spec.lanes), int(config.n_agents), int(spec.rollout_length)
    capture = {
        "pending": [],
        "feedback_calls": 0,
        "stored_steps": 0,
        "mode_rows": np.zeros((rollout_length, lanes, n_agents), dtype=np.bool_),
        "previous_optimizer_steps": optimizer_steps(agent),
    }
    source_apply_feedback = b02_training.apply_feedback
    source_store_transition_batch = agent.store_transition_batch
    had_instance_store = "store_transition_batch" in getattr(agent, "__dict__", {})
    instance_store_transition_batch = getattr(agent, "__dict__", {}).get("store_transition_batch")

    def record_feedback(*args, **kwargs):
        decision = source_apply_feedback(*args, **kwargs)
        index = capture["feedback_calls"]
        step, lane = divmod(index, lanes)
        if step >= rollout_length:
            raise RuntimeError("production shield produced more rows than the current rollout")
        modes = np.asarray(decision.modes)
        if modes.shape != (n_agents,) or modes.dtype != np.bool_:
            raise RuntimeError("production shield mode is not one bool per UAV")
        capture["mode_rows"][step, lane] = modes
        capture["feedback_calls"] += 1
        capture["pending"].append(decision)
        return decision

    def store_transition_batch(*args, **kwargs):
        step = kwargs.get("rollout_step_idx")
        if step is None or int(step) != capture["stored_steps"]:
            raise RuntimeError("collector transition index differs from captured shield row")
        result = source_store_transition_batch(*args, **kwargs)
        if len(capture["pending"]) != lanes:
            raise RuntimeError(
                f"expected {lanes} production shield decisions before storage, "
                f"got {len(capture['pending'])}"
            )
        modes = np.stack([np.asarray(row.modes, dtype=np.bool_) for row in capture["pending"]])
        # True means retain this agent's direct PPO policy-surrogate row.
        agent.rollout_buffer.set_policy_surrogate_mask(int(step), np.logical_not(modes))
        capture["pending"].clear()
        capture["stored_steps"] += 1
        return result

    def finish_rollout(rollout: int, record: dict[str, Any]) -> None:
        if capture["pending"]:
            raise RuntimeError("unpaired shield decisions remain at the PPO update boundary")
        if capture["feedback_calls"] != rollout_length * lanes:
            raise RuntimeError("captured shield decision count differs from rollout length")
        if capture["stored_steps"] != rollout_length:
            raise RuntimeError("stored shield mask count differs from rollout length")
        full_override_rows = int(capture["mode_rows"].sum())
        if full_override_rows != int(record["f_mode_uav_steps"]):
            raise RuntimeError("recorded full-override rows differ from the native B02 mode count")

        metrics = getattr(agent, "shield_surrogate_update_metrics", None)
        if not isinstance(metrics, dict):
            raise RuntimeError("learner did not return shield-surrogate update diagnostics")
        current_steps = optimizer_steps(agent)
        update_delta = {
            key: int(current_steps[key]) - int(capture["previous_optimizer_steps"][key])
            for key in current_steps
        }
        if update_delta["low_actor"] != int(metrics["optimizer_updates"]):
            raise RuntimeError("actor optimizer count differs from surrogate diagnostic updates")
        if update_delta["low_critic"] != int(metrics["optimizer_updates"]):
            raise RuntimeError("critic optimizer count differs from surrogate diagnostic updates")
        if any(update_delta[key] for key in ("high", "team_discriminator", "individual_discriminator")):
            raise RuntimeError("a non-SET learner unexpectedly updated")

        total_action_rows = int(record["submitted_commands"])
        ppo_epochs = int(getattr(config, "ppo_epochs", 15))
        expected_presentations = int(metrics["valid_action_sample_presentations"])
        expected_masked_presentations = int(metrics["shielded_action_sample_presentations"])
        if rollout_length % int(config.k) == 0:
            if expected_presentations != total_action_rows * ppo_epochs:
                raise RuntimeError("the recurrent sampler dropped valid production PPO rows")
            if expected_masked_presentations != full_override_rows * ppo_epochs:
                raise RuntimeError("shield mask exposure differs from sampler PPO presentations")

        record["full_override_action_rows"] = full_override_rows
        record["action_rows"] = total_action_rows
        record["full_override_action_share"] = (
            full_override_rows / total_action_rows if total_action_rows else 0.0
        )
        record["shield_surrogate"] = {
            **metrics,
            "full_override_action_rows": full_override_rows,
            "action_rows": total_action_rows,
            "ppo_presentations_expected_from_source_count": full_override_rows * ppo_epochs,
            "optimizer_step_delta": update_delta,
        }
        if agent.shield_surrogate_gradient_probe is not None:
            record["shield_surrogate_gradient_probe"] = dict(
                agent.shield_surrogate_gradient_probe
            )
        capture["previous_optimizer_steps"] = current_steps

        if after_rollout is not None:
            after_rollout(rollout, record)

        # The frozen B02 collector clears the buffer before this callback. Re-enable the optional
        # sidecar only for a subsequent rollout; reset discards it by default.
        if int(rollout) < int(spec.rollouts):
            agent.rollout_buffer.enable_policy_surrogate_mask()
        capture["pending"].clear()
        capture["feedback_calls"] = 0
        capture["stored_steps"] = 0
        capture["mode_rows"] = np.zeros((rollout_length, lanes, n_agents), dtype=np.bool_)

    b02_training.apply_feedback = record_feedback
    agent.store_transition_batch = store_transition_batch
    try:
        return b02_training.collect_and_train(
            agent,
            config,
            spec,
            feedback=True,
            after_rollout=finish_rollout,
            start_rollout=int(start_rollout),
            start_transitions=int(start_transitions),
            env_seed=int(env_seed),
        )
    finally:
        b02_training.apply_feedback = source_apply_feedback
        if had_instance_store:
            agent.store_transition_batch = instance_store_transition_batch
        else:
            delattr(agent, "store_transition_batch")


def _low_level_parameter_groups(agent):
    discoverer = agent.skill_discoverer
    groups = {
        "actor": [("actor", discoverer.actor)],
        "critic": [("critic", discoverer.critic)],
    }
    if discoverer.actor_context_adapter is not None:
        groups["actor"].append(("actor_context_adapter", discoverer.actor_context_adapter))
    if discoverer.critic_context_adapter is not None:
        groups["critic"].append(("critic_context_adapter", discoverer.critic_context_adapter))
    if agent.low_level_compact_extractor is not None:
        groups["shared_compact_extractor"] = [
            ("low_level_compact_extractor", agent.low_level_compact_extractor)
        ]
    return groups


def _named_parameters_for_group(modules):
    return {
        f"{prefix}.{name}": parameter
        for prefix, module in modules
        for name, parameter in module.named_parameters()
    }


def snapshot_low_level_parameters(agent) -> dict[str, dict[str, torch.Tensor]]:
    """Copy every updated low-level actor/critic parameter to a fixed c03 reference."""
    return {
        group: {
            name: parameter.detach().to(device="cpu", dtype=torch.float32).clone()
            for name, parameter in _named_parameters_for_group(modules).items()
        }
        for group, modules in _low_level_parameter_groups(agent).items()
    }


def parameter_displacement(agent, reference: dict[str, dict[str, torch.Tensor]]) -> dict[str, Any]:
    """Return actor/critic L2 and max-absolute parameter changes from c03."""
    output: dict[str, Any] = {}
    for group, modules in _low_level_parameter_groups(agent).items():
        saved = reference[group]
        current = _named_parameters_for_group(modules)
        if current.keys() != saved.keys():
            raise RuntimeError(f"{group} parameter names differ from c03 initialization")
        squared_delta = 0.0
        squared_reference = 0.0
        max_abs_delta = 0.0
        for name, parameter in current.items():
            initial = saved[name]
            value = parameter.detach().to(device="cpu", dtype=torch.float32)
            delta = value.to(torch.float64) - initial.to(torch.float64)
            squared_delta += float(delta.square().sum().item())
            squared_reference += float(initial.to(torch.float64).square().sum().item())
            max_abs_delta = max(max_abs_delta, float(delta.abs().max().item()))
        displacement = squared_delta ** 0.5
        reference_norm = squared_reference ** 0.5
        output[group] = {
            "parameter_count": sum(parameter.numel() for parameter in current.values()),
            "l2_from_c03": displacement,
            "relative_l2_from_c03": displacement / reference_norm if reference_norm else 0.0,
            "max_abs_from_c03": max_abs_delta,
        }
    return output
