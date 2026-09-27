"""Direction-owned instrumentation around the published B02 collector contract."""

from __future__ import annotations

import json
import sys
from collections import deque
from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.energy_relay_benchmark.b02 import training as b02_training
from experiments.candidates.uav_service_auxiliary.b01.native import optimizer_steps


class StepCommunicationCacheInvariantError(RuntimeError):
    """A B02 training environment exposed a cache value outside its recorded invariant."""

    def __init__(self, details: dict[str, Any]):
        self.details = details
        super().__init__(
            "B02 step communication cache invariant violated: "
            + json.dumps(details, sort_keys=True, separators=(",", ":"))
        )


def install_step_communication_cache_diagnostic(env, *, lane: int, seed: int):
    """Guard one training environment's getter without changing valid cache behavior."""
    core_env = getattr(env, "env", env)
    getter_name = "_current_step_communication_cache"
    original_getter = getattr(core_env, getter_name, None)
    if not callable(original_getter):
        raise TypeError(
            f"lane {lane} environment lacks callable {getter_name}: {type(core_env).__name__}"
        )

    instance_dict = getattr(core_env, "__dict__", {})
    had_instance_getter = getter_name in instance_dict
    previous_instance_getter = instance_dict.get(getter_name)
    getter_function = getattr(original_getter, "__func__", original_getter)
    getter_module_name = getattr(getter_function, "__module__", None)
    getter_module = sys.modules.get(getter_module_name)
    getter_module_file = getattr(getter_module, "__file__", None)
    environment_class = f"{type(core_env).__module__}.{type(core_env).__qualname__}"
    recent_reads: deque[dict[str, Any]] = deque(maxlen=8)
    getter_ordinal = 0

    def type_name(value) -> str:
        return f"{type(value).__module__}.{type(value).__qualname__}"

    def record_read(cache, ordinal: int) -> dict[str, Any]:
        environment_step = getattr(core_env, "current_step", None)
        if isinstance(environment_step, (int, np.integer)):
            environment_step = int(environment_step)
        elif environment_step is not None:
            environment_step = repr(environment_step)
        active = getattr(core_env, "_channel_update_cache_active", False)
        record = {
            "getter_ordinal": int(ordinal),
            "environment_step": environment_step,
            "cache_type": None if cache is None else type_name(cache),
            "cache_identity": None if cache is None else int(id(cache)),
            "channel_update_cache_active": repr(active),
        }
        if cache is not None and not isinstance(cache, dict):
            try:
                rendered = repr(cache)
            except Exception as exc:  # diagnostic must survive a hostile repr implementation
                rendered = f"<repr raised {type(exc).__name__}: {exc}>"
            record["cache_value"] = rendered[:160]
        recent_reads.append(record)
        return record

    def make_error(record: dict[str, Any], *, stage: str, cause=None):
        details: dict[str, Any] = {
            "stage": stage,
            "lane": int(lane),
            "lane_seed": int(seed),
            "environment_step": record["environment_step"],
            "getter_ordinal": record["getter_ordinal"],
            "cache_type": record["cache_type"],
            "cache_value": record.get("cache_value"),
            "cache_identity": record["cache_identity"],
            "channel_update_cache_active": record["channel_update_cache_active"],
            "environment_class": environment_class,
            "getter_module": getter_module_name,
            "getter_module_file": getter_module_file,
            "recent_getter_reads": list(recent_reads),
        }
        if cause is not None:
            details["original_exception"] = f"{type(cause).__name__}: {cause}"
        return StepCommunicationCacheInvariantError(details)

    def diagnostic_getter():
        nonlocal getter_ordinal
        getter_ordinal += 1
        cache = getattr(core_env, "_step_communication_cache", None)
        record = record_read(cache, getter_ordinal)
        if cache is not None and not isinstance(cache, dict):
            raise make_error(record, stage="before_original_getter")
        try:
            result = original_getter()
        except Exception as exc:
            current_cache = getattr(core_env, "_step_communication_cache", None)
            if current_cache is not None and not isinstance(current_cache, dict):
                current_record = record_read(current_cache, getter_ordinal)
                raise make_error(
                    current_record,
                    stage="after_original_getter_exception",
                    cause=exc,
                ) from exc
            raise
        if result is not None and not isinstance(result, dict):
            result_record = record_read(result, getter_ordinal)
            raise make_error(
                result_record,
                stage="original_getter_result",
            )
        return result

    setattr(core_env, getter_name, diagnostic_getter)

    def restore():
        if had_instance_getter:
            setattr(core_env, getter_name, previous_instance_getter)
        else:
            delattr(core_env, getter_name)

    return restore


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
    source_make_env = b02_training.make_env
    source_apply_feedback = b02_training.apply_feedback
    source_store_transition_batch = agent.store_transition_batch
    cache_probe_restores = []
    had_instance_store = "store_transition_batch" in getattr(agent, "__dict__", {})
    instance_store_transition_batch = getattr(agent, "__dict__", {}).get("store_transition_batch")

    def make_diagnostic_env(env_config, seed):
        lane = len(cache_probe_restores)
        env = source_make_env(env_config, seed)
        try:
            restore = install_step_communication_cache_diagnostic(
                env, lane=lane, seed=int(seed)
            )
        except Exception:
            env.close()
            raise
        cache_probe_restores.append(restore)
        return env

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

    b02_training.make_env = make_diagnostic_env
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
        b02_training.make_env = source_make_env
        b02_training.apply_feedback = source_apply_feedback
        for restore in reversed(cache_probe_restores):
            restore()
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
