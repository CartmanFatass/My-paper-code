"""Run one fixed B16 fresh LOCAL1 ordinary-MAPPO fit."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import resource
import sys
import time
import traceback
from types import MethodType
from typing import Any, Callable

import numpy as np
import torch
from torch.optim import Adam

from configs.config_1 import Config
from hmasd.agent import HMASDAgent
from hmasd.baselines import apply_algorithm_config
from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.bounded_confirmation_b15 import runner as b15
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC, DIRECTION, FitSpec, config_dict,
)
from experiments.candidates.agent_count_generalization.models import (
    SharedValueHeads, StateSetEncoder, strict_sync,
)
from experiments.candidates.agent_count_generalization.ordinary_control_b13 import runner as b13
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS, capture_parameters, digest_agent, finite, jsonable, model_modules,
    native_components, optimizer_counts, parameter_motion, preserve_rng,
    save_checkpoint, seed_rng, write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11


OBJECT_ID = "s1_local_ordinary_b16"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
EVALUATION_ORDER = (8, 6)
WORLD_SEED_BASES = {8: 1_945_800, 6: 1_945_600}
FINAL_ROLLOUT = 45
ATOL = 1e-7
RTOL = 1e-6


@dataclass(frozen=True)
class TrainingCell:
    key: str
    arm: str
    tag: str
    seed: int
    block: int
    training_env_seed_base: int
    train_n: int = 6
    law: str = "clip"
    lambda_l: float = .05


CELLS = (
    TrainingCell("b1_local1", "LOCAL1", "s1_local_ordinary_b16_b1_local1_s994101", 994101, 1, 2_994_100),
    TrainingCell("b2_local1", "LOCAL1", "s1_local_ordinary_b16_b2_local1_s994102", 994102, 2, 2_994_200),
    TrainingCell("b3_local1", "LOCAL1", "s1_local_ordinary_b16_b3_local1_s994103", 994103, 3, 2_994_300),
)
CELL_BY_KEY = {cell.key: cell for cell in CELLS}
B16_BASE_SPEC = replace(
    DEFAULT_SPEC, train_n=6, test_ns=EVALUATION_ORDER, eval_lanes=32,
    panels=(0, FINAL_ROLLOUT),
)


def spec_for(cell: TrainingCell, base: FitSpec = B16_BASE_SPEC) -> FitSpec:
    if cell not in CELLS:
        raise ValueError("B16 accepts only its three fixed LOCAL1 cells")
    return replace(base, train_n=6, test_ns=EVALUATION_ORDER, panels=(0, base.rollouts))


def _config_record(config: Any) -> dict[str, Any]:
    return {
        **config_dict(config),
        "num_team_codes": int(config.num_team_codes),
        "lambda_l_initial": float(config.lambda_l_initial),
        "lambda_l_final": float(config.lambda_l_final),
        "use_entropy_annealing": bool(config.use_entropy_annealing),
        "use_entropy_targets": bool(config.use_entropy_targets),
    }


def _assert_config(config: Any, cell: TrainingCell, expected_n: int) -> None:
    if cell.arm != "LOCAL1" or str(config.count_arm) != "LOCAL1":
        raise ValueError("B16 requires honest LOCAL1 cell/config identity")
    if str(config.algorithm) != "mappo" or int(config.n_z) != 1 or int(config.n_Z) != 1 \
            or int(config.num_team_codes) != 1:
        raise ValueError("B16 requires task-only MAPPO with n_z=n_Z=1")
    if int(config.n_agents) != expected_n or int(config.n_uavs) != expected_n:
        raise ValueError(f"B16 config has wrong physical roster for N={expected_n}")
    if int(config.k) != 10 or bool(config.use_central_snapshot_in_flat_actor):
        raise ValueError("B16 requires k10 and the 104-wide local actor route")
    if int(config.obs_dim) != 104 or int(config.state_dim) != 133:
        raise ValueError("B16 native S1 observation/state contract changed")
    if str(getattr(config, "continuous_action_distribution", "gaussian")) != "gaussian":
        raise ValueError("B16 requires the native Gaussian action distribution")
    if any(float(value) != .05 for value in (
        config.lambda_l, config.lambda_l_initial, config.lambda_l_final,
    )) or bool(config.use_entropy_annealing) or bool(config.use_entropy_targets):
        raise ValueError("B16 fixed .05 raw-Gaussian entropy treatment changed")
    if not bool(config.disable_high_level_training) \
            or not bool(config.disable_discriminator_training) \
            or not bool(config.disable_discriminator_rewards) \
            or bool(config.collects_high_level_samples):
        raise ValueError("B16 task-only disabled-update contract changed")
    if any(float(getattr(config, name)) != 0.0 for name in (
        "lambda_D", "lambda_d", "lambda_h", "lambda_cd", "lambda_mi",
    )) or bool(config.use_process_exploration) \
            or bool(config.use_process_reward_for_discoverer):
        raise ValueError("B16 task-only reward contract changed")


def make_b16_config(
    cell: TrainingCell, envs: list[Any], spec: FitSpec, *, expected_n: int | None = None,
) -> Any:
    """Freeze a genuine LOCAL1 config before constructing any network."""
    if cell.arm != "LOCAL1":
        raise ValueError("B16 config construction accepts LOCAL1 only")
    config = Config()
    config.n_uavs = envs[0].n_uavs
    config.n_users = 50
    config.num_envs = len(envs)
    config.rollout_length = config.episode_length = spec.horizon
    config.k = 10
    config.seed = int(cell.seed)
    config.hidden_size = config.embedding_dim = config.gru_hidden_size = spec.hidden_size
    config.n_heads = spec.n_heads
    config.n_encoder_layers = config.n_decoder_layers = spec.n_layers
    config.policy_interruption_mode = "off"
    config.use_obsnorm = config.use_statenorm = False
    config.use_lr_decay = False
    config.n_Z = config.n_z = 1
    config.ppo_epochs = spec.ppo_epochs
    config.sequence_batch_size = spec.sequence_batch_size
    config.coordinator_batch_size = spec.coordinator_batch_size
    config.total_timesteps = spec.train_lanes * spec.horizon * spec.rollouts
    config.update_env_dims(
        state_dim=envs[0].state_dim, obs_dim=envs[0].obs_dim,
        n_agents=envs[0].n_uavs,
    )
    config = apply_algorithm_config(config, "mappo")
    # MAPPO deliberately changes k and its buffer allocation. B16 restores the
    # prospectively fixed recurrent chunk/decision clock before construction.
    config.k = 10
    config.num_team_codes = 1
    config.use_central_snapshot_in_flat_actor = False
    config.count_arm = "LOCAL1"
    config.lambda_l = config.lambda_l_initial = config.lambda_l_final = cell.lambda_l
    config.use_entropy_annealing = False
    config.use_entropy_targets = False
    config.calculate_and_set_buffer_sizes()
    config.discriminator_batch_size = config.batch_size
    config.validate_config()
    _assert_config(config, cell, spec.train_n if expected_n is None else expected_n)
    return config


def _adam(parameters: Any, *, lr: float, weight_decay: float) -> Adam:
    params = list(parameters)
    if len({id(parameter) for parameter in params}) != len(params):
        raise AssertionError("B16 optimizer parameter inventory contains duplicates")
    return Adam(params, lr=float(lr), weight_decay=float(weight_decay))


def _assert_optimizer_exactly_once(optimizer: Any, parameters: Any, name: str) -> None:
    expected = [id(parameter) for parameter in parameters if parameter.requires_grad]
    actual = [
        id(parameter) for group in optimizer.param_groups for parameter in group["params"]
        if parameter.requires_grad
    ]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise AssertionError(f"B16 {name} optimizer ownership is not exact")


def build_local_agent(config: Any, log_dir: str) -> HMASDAgent:
    """Construct LOCAL1 directly, without entering or weakening the H6/SET builder."""
    if str(getattr(config, "count_arm", "")) != "LOCAL1":
        raise ValueError("B16 constructor requires count_arm=LOCAL1")
    if bool(getattr(config, "use_central_snapshot_in_flat_actor", False)):
        raise ValueError("B16 constructor refuses a central actor snapshot")
    if int(config.n_z) != 1 or int(config.n_Z) != 1:
        raise ValueError("B16 constructor requires one constant category")
    agent = HMASDAgent(config, log_dir=log_dir, device=torch.device("cpu"))
    device = agent.device

    # The coordinator remains inference-only but its state route must still
    # transfer strictly across N. The learned critic is likewise count stable.
    agent.skill_coordinator.state_embedding = StateSetEncoder(
        int(config.embedding_dim), hidden_dim=min(256, int(config.hidden_size)),
        uav_hidden_dim=min(64, int(config.hidden_size)),
    ).to(device)
    agent.skill_coordinator.value_heads_obs = SharedValueHeads(
        int(config.embedding_dim), int(config.n_agents),
    ).to(device)
    agent.skill_discoverer.critic.base = StateSetEncoder(
        int(config.hidden_size), hidden_dim=min(256, int(config.hidden_size)),
        uav_hidden_dim=min(64, int(config.hidden_size)),
    ).to(device)
    agent.coordinator_optimizer = _adam(
        agent.skill_coordinator.parameters(), lr=config.lr_coordinator,
        weight_decay=config.weight_decay,
    )
    agent.discoverer_critic_optimizer = _adam(
        agent.skill_discoverer.critic_update_parameters(),
        lr=config.lr_discoverer_critic, weight_decay=config.weight_decay,
    )

    _assert_optimizer_exactly_once(
        agent.coordinator_optimizer, agent.skill_coordinator.parameters(), "coordinator",
    )
    _assert_optimizer_exactly_once(
        agent.discoverer_actor_optimizer,
        agent.skill_discoverer.actor_update_parameters(), "discoverer actor",
    )
    _assert_optimizer_exactly_once(
        agent.discoverer_critic_optimizer,
        agent.skill_discoverer.critic_update_parameters(), "discoverer critic",
    )
    if agent.team_discriminator is not None or agent.individual_discriminator is not None:
        raise AssertionError("B16 task-only construction unexpectedly created discriminators")
    actor_input_width = int(agent.skill_discoverer.actor.base.mlp[0].in_features)
    if actor_input_width != 104:
        raise AssertionError("B16 actor base is not the native 104-wide local path")
    return agent


def _world_seed(n: int) -> int:
    try:
        return WORLD_SEED_BASES[int(n)]
    except KeyError as exc:
        raise ValueError(f"B16 has no evaluation panel at N={n}") from exc


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        Path(__file__).resolve().with_name("__init__.py"),
        REPOSITORY_ROOT / "scripts/run_agent_count_local_ordinary_b16.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/bounded_confirmation_b15/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/training_condition_b11/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/ordinary_control_b13/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
        REPOSITORY_ROOT / "configs/config_1.py",
        REPOSITORY_ROOT / "hmasd/agent.py",
        REPOSITORY_ROOT / "hmasd/networks.py",
        REPOSITORY_ROOT / "hmasd/r_mappo_utils.py",
        REPOSITORY_ROOT / "hmasd/baselines.py",
    )


def _source_hashes() -> dict[str, str]:
    return {
        path.relative_to(REPOSITORY_ROOT).as_posix(): b15.file_sha256(path)
        for path in _source_paths()
    }


def _initialization(cell: TrainingCell, config: Any, out: Path) -> tuple[Any, dict[str, Any]]:
    agent = build_local_agent(config, str(out / "initialization_logs" / "fresh_local1"))
    parameter_ids: set[int] = set()
    ownership = b11._optimizer_ownership(agent, parameter_ids)
    evidence = {
        "method": "fresh_true_n_local1_construction_no_cross_architecture_copy",
        "canonical_n": None, "target_n": int(config.n_agents),
        "post_initialization_rng_digest": b03._rng_digest(),
        "parameter_normalizer_digest": digest_agent(agent),
        "tensor_manifest": b11._tensor_manifest(agent),
        "normalizers": b11._normalizer_manifest(agent),
        "target_optimizer_ownership": ownership,
        "target_initial_buffer": b11._buffer_initial_record(agent),
        "target_fresh_runtime_digest": b03.runtime_state_digest(agent),
        "actual_config": _config_record(config),
        "actor_input_width": int(agent.skill_discoverer.actor.base.mlp[0].in_features),
        "actor_base_type": type(agent.skill_discoverer.actor.base).__name__,
        "critic_base_type": type(agent.skill_discoverer.critic.base).__name__,
        "actor_has_trainable_film": any(
            parameter.requires_grad
            for parameter in agent.skill_discoverer.actor.film_generator.parameters()
        ),
        "actor_has_gru": hasattr(agent.skill_discoverer.actor, "rnn"),
        "central_snapshot_enabled": bool(agent.use_central_snapshot),
    }
    return agent, evidence


class _InferenceCounter:
    """Count native inference plus actual central-snapshot refresh calls."""

    def __init__(self, agent: Any, n: int):
        self._agent = agent
        self._closed = False
        self._inner = b13._InferenceCounter(agent, "LOCAL1", n)
        self.data = self._inner.data
        self._original_refresh = agent._refresh_central_snapshots

        def counted_refresh(
            _agent: Any, states: Any, observations: Any, refresh_mask: Any,
        ) -> Any:
            mask = np.asarray(refresh_mask, dtype=bool)
            self.data["set_snapshot_refresh_steps"] += int(mask.any())
            self.data["set_snapshot_lane_refreshes"] += int(mask.sum())
            return self._original_refresh(states, observations, refresh_mask)

        agent._refresh_central_snapshots = MethodType(counted_refresh, agent)

    def observe_choices(self, data: dict[str, Any]) -> None:
        self._inner.observe_choices(data)

    def finish(self, spec: FitSpec) -> dict[str, Any]:
        result = self._inner.finish(spec)
        result["set_snapshot_refresh_steps"] = int(self.data["set_snapshot_refresh_steps"])
        result["set_snapshot_lane_refreshes"] = int(
            self.data["set_snapshot_lane_refreshes"]
        )
        return result

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._agent._refresh_central_snapshots = self._original_refresh
        self._inner.close()


def _evaluate_stage(
    learner: Any, training_envs: list[Any], cell: TrainingCell, stage: int,
    out: Path, summary: dict[str, Any], spec: FitSpec, publish: Callable[[str], None],
) -> None:
    isolation_before = b15._isolation_snapshot(learner, training_envs)
    with preserve_rng():
        for n in EVALUATION_ORDER:
            world_seed = _world_seed(n)
            seed_rng(world_seed + 51)
            envs = make_envs(spec.eval_lanes, world_seed, n, spec.horizon)
            target, inference, hooks = None, None, []
            storage_calls = 0
            original_store = None
            row = {
                "status": "running", "arm": cell.arm, "cell_key": cell.key,
                "policy_stage": stage, "after_rollout": stage,
                "prior_training_team_steps": stage * spec.train_lanes * spec.horizon,
                "test_n": n,
                "world_seeds": list(range(world_seed, world_seed + spec.eval_lanes)),
                "runtime_seed": world_seed + 51, "execution_law": "clip",
                "steps": 0, "episodes": 0, "resets": 0, "policy_step_calls": 0,
            }
            summary["panels"].append(row)
            publish(f"stage {stage} evaluation N={n} starting")
            try:
                b11._assert_native_envs(envs, n)
                config = make_b16_config(cell, envs, replace(spec, train_n=n), expected_n=n)
                target = build_local_agent(
                    config, str(out / "evaluation_logs" / f"stage{stage:02d}_n{n}"),
                )
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                before = digest_agent(target)
                if before != digest_agent(learner):
                    raise ValueError("B16 evaluation target did not strictly load learner")
                normals_before = b11._normalizer_manifest(target)
                runtime_before = b03.runtime_state_digest(target)
                original_store = target.store_transition_batch

                def reject_store(_target: Any, *args: Any, **kwargs: Any) -> None:
                    nonlocal storage_calls
                    storage_calls += 1
                    summary["counts"]["evaluation_storage_calls"] += 1
                    raise ValueError("B16 evaluation attempted training storage")

                target.store_transition_batch = MethodType(reject_store, target)
                inference = _InferenceCounter(target, n)
                pairs = [env.reset() for env in envs]
                row["resets"] = len(pairs)
                summary["counts"]["evaluation_resets"] += len(pairs)
                states = np.stack([info["state"] for observation, info in pairs])
                observations = np.stack([observation for observation, info in pairs])
                steps = np.zeros(spec.eval_lanes, dtype=np.int64)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                sums = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
                trace = b15._new_panel_trace(spec, n)
                trace["initial_states"] = states.copy()
                trace["initial_observations"] = observations.copy()
                action_min, action_max = float("inf"), float("-inf")
                with torch.no_grad():
                    for t in range(spec.horizon):
                        trace["states"][t] = states
                        trace["observations"][t] = observations
                        raw_actions, _, data = target.step(
                            states, observations, steps, dones, deterministic=True,
                            return_step_data=True, build_infos=False,
                        )
                        row["policy_step_calls"] += 1
                        summary["counts"]["evaluation_policy_step_calls"] += 1
                        finite((raw_actions, data), "B16 deterministic evaluation output")
                        inference.observe_choices(data)
                        raw_before = raw_actions.copy()
                        executed = b03.map_training_actions(raw_actions, "clip")
                        if not np.array_equal(raw_actions, raw_before):
                            raise ValueError("B16 evaluation clip changed raw policy output")
                        trace["raw_actions"][t] = raw_actions
                        trace["executed_actions"][t] = executed
                        action_min = min(action_min, float(executed.min()))
                        action_max = max(action_max, float(executed.max()))
                        next_states, next_observations = [], []
                        for lane, env in enumerate(envs):
                            observation, reward, terminated, truncated, info = env.step(executed[lane])
                            done = bool(terminated or truncated)
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_uav_steps"] += n
                            summary["counts"]["evaluation_episodes"] += int(done)
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                sums[name][lane] += parts[name]
                            b11._observe_post_transition(trace, t, lane, env, reward, parts, n)
                            next_states.append(info["next_state"])
                            next_observations.append(observation)
                            dones[lane] = done
                        states = np.stack(next_states)
                        observations = np.stack(next_observations)
                        trace["next_states"][t] = states
                        trace["next_observations"][t] = observations
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected B16 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B16 evaluation missed fixed terminal boundary")
                means = {name: value / spec.horizon for name, value in sums.items()}
                j = n * returns / spec.horizon
                native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means[
                    "energy_penalty"
                ]
                if not np.allclose(j, means["total_reward"], atol=ATOL, rtol=RTOL) \
                        or not np.allclose(j, native_j, atol=ATOL, rtol=RTOL):
                    raise ValueError("B16 native J/component identity failed")
                service = trace["served_user_counts"].mean(axis=0)
                eligibility = trace["eligible_user_counts"].mean(axis=0)
                unserved = trace["eligible_unserved_user_counts"].mean(axis=0)
                if not np.allclose(service, 50 * means["coverage_reward"], atol=ATOL, rtol=RTOL) \
                        or not np.allclose(unserved, eligibility - service, atol=ATOL, rtol=RTOL):
                    raise ValueError("B16 native C/S or E/S/U identity failed")
                inference_counts = inference.finish(spec)
                if inference.data["set_snapshot_refresh_steps"] != 0 \
                        or inference.data["set_snapshot_lane_refreshes"] != 0:
                    raise ValueError("B16 LOCAL1 unexpectedly refreshed a central actor snapshot")
                inference_counts["set_snapshot_refresh_steps"] = 0
                inference_counts["set_snapshot_lane_refreshes"] = 0
                model_after = digest_agent(target)
                if any(calls.values()) or storage_calls or model_after != before:
                    raise ValueError("B16 evaluation optimized, stored, or changed target parameters")
                if b11._normalizer_manifest(target) != normals_before:
                    raise ValueError("B16 evaluation changed target normalizers")
                if np.any(target.rollout_buffer.env_lengths):
                    raise ValueError("B16 evaluation populated training storage")
                trace_identity = b11._write_trace(out / f"trace_stage{stage:02d}_n{n}.npz", trace)
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                    component_means=jsonable(means),
                    service_arrays={
                        "E_eligible_users_per_step": eligibility.tolist(),
                        "S_served_users_per_step": service.tolist(),
                        "U_eligible_unserved_users_per_step": unserved.tolist(),
                    },
                    optimizer_calls=calls.copy(), training_storage_calls=storage_calls,
                    rollout_storage_env_lengths=target.rollout_buffer.env_lengths.tolist(),
                    frozen_weights_and_normalizers=True,
                    parameter_normalizer_digest_before=before,
                    parameter_normalizer_digest_after=model_after,
                    normalizers_before=normals_before,
                    normalizers_after=b11._normalizer_manifest(target),
                    runtime_digest_before=runtime_before,
                    runtime_digest_after=b03.runtime_state_digest(target),
                    runtime_evolved=runtime_before != b03.runtime_state_digest(target),
                    executed_action_bounds={"minimum": action_min, "maximum": action_max},
                    inference_counts=inference_counts, trace=trace_identity,
                    config=_config_record(config), post_transition_semantics=True,
                    actual_sinr_threshold=float(envs[0].env.env.min_sinr),
                    max_connections_per_uav=int(envs[0].env.env.max_connections),
                    height_range=[float(value) for value in envs[0].env.env.height_range],
                    n_users=int(envs[0].env.env.n_users),
                )
                summary["counts"]["panels"] += 1
                summary["counts"]["evaluation_optimizer_calls"] += sum(calls.values())
                write_json(out / f"panel_stage{stage:02d}_n{n}.json", row)
                publish(f"stage {stage} evaluation N={n} complete")
            except Exception as exc:
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                write_json(out / f"panel_stage{stage:02d}_n{n}.json", row)
                raise
            finally:
                if inference is not None:
                    inference.close()
                if target is not None and original_store is not None:
                    target.store_transition_batch = original_store
                for hook in hooks:
                    hook.remove()
                for env in envs:
                    env.close()
                del target
    isolation_after = b15._isolation_snapshot(learner, training_envs)
    preservation = {
        "before": isolation_before, "after": isolation_after,
        **{name + "_preserved": isolation_before[name] == isolation_after[name]
           for name in isolation_before},
    }
    summary["stage_isolation"][str(stage)] = preservation
    if not all(value for key, value in preservation.items() if key.endswith("_preserved")):
        raise ValueError("B16 evaluation changed learner, optimizer, sampler, RNG, or training environments")


def _finish_training_inference(
    observed: dict[str, Any], cell: TrainingCell, spec: FitSpec,
) -> dict[str, Any]:
    decisions = spec.rollouts * (spec.horizon // 10)
    rows = decisions * spec.train_lanes
    expected = {
        "coordinator_batched_calls": decisions, "coordinator_rows": rows,
        "decoder_team_calls": decisions, "decoder_team_rows": rows,
        "decoder_individual_calls": decisions * spec.train_n,
        "decoder_individual_rows": rows * spec.train_n,
        "team_selections": rows, "individual_selections": rows * spec.train_n,
    }
    if cell.arm != "LOCAL1" or any(observed[key] != value for key, value in expected.items()) \
            or observed["coordinator_batch_sizes"] != [spec.train_lanes] * decisions:
        raise ValueError(f"B16 training inference exposure changed: {observed} != {expected}")
    if sum(observed["team_choice_counts"]) != rows \
            or sum(observed["individual_choice_counts"]) != rows * spec.train_n:
        raise ValueError("B16 training inference choice counts are incomplete")
    if observed["team_choice_counts"] != [rows] \
            or observed["individual_choice_counts"] != [rows * spec.train_n]:
        raise ValueError("B16 constant LOCAL1 labels are invalid")
    if observed["set_snapshot_refresh_steps"] != 0 \
            or observed["set_snapshot_lane_refreshes"] != 0:
        raise ValueError("B16 LOCAL1 unexpectedly refreshed a central actor snapshot")
    return dict(observed)


def _aggregate_evaluation_inference(panels: list[dict[str, Any]]) -> dict[str, Any]:
    keys = (
        "coordinator_batched_calls", "coordinator_rows", "decoder_team_calls",
        "decoder_team_rows", "decoder_individual_calls", "decoder_individual_rows",
        "team_selections", "individual_selections", "set_snapshot_refresh_steps",
        "set_snapshot_lane_refreshes",
    )
    result = {key: sum(int(row["inference_counts"][key]) for row in panels) for key in keys}
    if result["set_snapshot_refresh_steps"] != 0 \
            or result["set_snapshot_lane_refreshes"] != 0:
        raise ValueError("B16 aggregate LOCAL1 snapshot refresh count is nonzero")
    return result


def _expected_optimizer_calls(_cell: TrainingCell) -> dict[str, int]:
    return {
        "coordinator": 0, "discoverer_actor": 101_250,
        "discoverer_critic": 101_250, "team_discriminator": 0,
        "individual_discriminator": 0,
    }


def run_fit(
    out: Path, cell: TrainingCell, launch_sha: str, admission: dict[str, Any],
    spec: FitSpec, *, command_start: float | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
    evaluate_initial: bool = True,
) -> int:
    out = Path(out)
    if cell not in CELLS or out.name != cell.tag:
        raise ValueError("B16 accepts only its three fixed cells and matching output tags")
    if spec.train_n != 6 or tuple(spec.test_ns) != EVALUATION_ORDER \
            or tuple(spec.panels) != (0, spec.rollouts):
        raise ValueError("B16 spec must bind N6 training and stage0/final N8 then N6 evaluation")
    if spec == spec_for(cell) and not evaluate_initial:
        raise ValueError("B16 production execution cannot omit initial evaluation")
    if (out / "summary.json").exists():
        raise ValueError("existing B16 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected = b15._expected_counts(spec, initial_evaluation=evaluate_initial)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
        "cell": jsonable(vars(cell)), "arm": cell.arm, "tag": cell.tag,
        "seed": cell.seed, "block": cell.block,
        "training_env_seed_base": cell.training_env_seed_base,
        "launch_sha": launch_sha, "admission": admission,
        "training_action_law": "clip", "status": "initializing", "fit_started": False,
        "failure": None, "spec": jsonable(vars(spec)), "panels": [], "checkpoints": [],
        "rollouts": [], "stage_isolation": {}, "stage_readings": None,
        "initial_evaluation_enabled": bool(evaluate_initial),
        "counts": {key: 0 for key in expected}, "expected_counts": expected,
        "training_world_seeds": list(range(
            cell.training_env_seed_base,
            cell.training_env_seed_base + spec.train_lanes,
        )),
        "evaluation_order": [
            {"stage": stage, "test_n": n}
            for stage in ((0, spec.rollouts) if evaluate_initial else (spec.rollouts,))
            for n in EVALUATION_ORDER
        ],
        "world_seed_bases": WORLD_SEED_BASES, "source_hashes_before": _source_hashes(),
        "reward_units": {
            "training": "native R / train_N=6", "J": "test_N * scalar_return / horizon",
            "C": "coverage fraction", "S": "served users per step = 50*C",
            "U": "eligible unserved users per step = E-S",
        },
        "runtime": {
            "python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
            "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
        },
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_fit_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    envs: list[Any] = []
    agent, hooks, optimizer_call_counts = None, [], {}
    active_training_counter = None
    reset_identity_written = False
    publish("admitted")
    try:
        torch.set_num_threads(spec.torch_threads)
        # External scenes are materialized before the learning RNG is seeded.
        envs = [
            b15._ResetSceneRecorder(env, lane)
            for lane, env in enumerate(make_envs(
                spec.train_lanes, cell.training_env_seed_base, 6, spec.horizon,
            ))
        ]
        b11._assert_native_envs(envs, 6)
        seed_rng(cell.seed)
        config = make_b16_config(cell, envs, spec)
        summary["config"] = _config_record(config)
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "cell": vars(cell), "spec": vars(spec),
            "config": summary["config"], "evaluation_order": summary["evaluation_order"],
            "world_seed_bases": WORLD_SEED_BASES,
        })
        agent, initialization = _initialization(cell, config, out)
        agent.train(True)
        summary["initialization"] = initialization
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        optimizer_call_counts, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = optimizer_call_counts
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        initial_parameters = capture_parameters(agent)
        summary["observed_initial_parameter_normalizer_digest"] = digest_agent(agent)
        summary["initial_raw_sigma"] = b03.raw_sigma(agent)
        summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
        if evaluate_initial:
            _evaluate_stage(agent, envs, cell, 0, out, summary, spec, publish)
        pairs = [env.reset() for env in envs]
        states = np.stack([info["state"] for observation, info in pairs])
        observations = np.stack([observation for observation, info in pairs])
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"] = "training"
        publish("training starts")
        training_inference_totals = b15._new_inference_totals(agent)
        b03_cell = b03.TrainingCell(1, cell.key, cell.arm, "clip", cell.seed, cell.tag)

        def count_training_start(event: dict[str, Any]) -> None:
            if not summary["fit_started"]:
                if summary["counts"]["training_team_steps"] <= 0:
                    raise ValueError("B16 fit start requires a counted training transition")
                summary["fit_started"] = True
                summary["counts"]["fits"] = 1
            if training_step_hook is not None:
                training_step_hook(event)

        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            optimizer_before = optimizer_call_counts.copy()
            active_training_counter = _InferenceCounter(agent, 6)
            counted_agent = b15._CountingAgent(
                agent, summary["counts"], summary, active_training_counter,
            )
            counted_agent.optimizer_before = optimizer_before
            sigma_before = b03.raw_sigma(agent)
            try:
                states, observations, steps, dones, motion, returns = b03.collect_rollout(
                    counted_agent, envs, states, observations, steps, dones, b03_cell, rollout,
                    summary, spec, training_step_hook=count_training_start,
                )
            finally:
                active_training_counter.close()
            b15._add_inference_counts(training_inference_totals, active_training_counter.data)
            active_training_counter = None
            summary["counts"]["training_uav_steps"] = (
                summary["counts"]["training_team_steps"] * 6
            )
            publish(f"rollout {rollout} collected")
            summary["_active_training_rollout"].update(
                phase="updating", raw_sigma_before_update=sigma_before,
                optimizer_calls_before_update=optimizer_before,
            )
            losses = agent.update(
                last_values=np.zeros((spec.train_lanes, 6), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon,
                last_state=states.copy(), last_observations=observations.copy(),
            )
            summary["counts"]["updates"] += 1
            finite(losses, "B16 training losses")
            _assert_config(agent.config, cell, 6)
            motion_parameters = parameter_motion(agent, initial_parameters)
            row = {
                "rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": {
                    name: optimizer_call_counts[name] - optimizer_before[name]
                    for name in optimizer_call_counts
                },
                "optimizer_total": optimizer_call_counts.copy(),
                "parameter_motion": motion_parameters,
                "raw_sigma_before_update": sigma_before,
                "raw_sigma_after_update": b03.raw_sigma(agent),
                "action_motion_telemetry": motion,
                "rollout_wall_seconds": time.perf_counter() - rollout_start,
            }
            with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            summary["rollouts"].append(row)
            summary["parameter_motion"] = motion_parameters
            agent.clear_buffers()
            summary.pop("_active_training_rollout", None)
            publish(f"rollout {rollout} updated")
        summary["training_inference_counts"] = _finish_training_inference(
            training_inference_totals, cell, spec,
        )
        summary["training_reset_trace"] = b15._write_training_resets(
            out / "training_reset_scenes.npz", envs, cell.training_env_seed_base,
        )
        reset_identity_written = True
        summary["checkpoints"].append(save_checkpoint(
            agent, out, spec.rollouts, config, launch_sha,
        ))
        _evaluate_stage(agent, envs, cell, spec.rollouts, out, summary, spec, publish)
        if summary["counts"] != expected:
            raise ValueError(f"B16 exposure mismatch: {summary['counts']} != {expected}")
        if spec == spec_for(cell) and optimizer_call_counts != _expected_optimizer_calls(cell):
            raise ValueError("B16 production optimizer exposure differs from fixed contract")
        for name in ("discoverer_actor", "discoverer_critic"):
            if optimizer_call_counts[name] <= 0 \
                    or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"B16 required learner module did not update: {name}")
        if any(optimizer_call_counts[name] for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        )):
            raise ValueError("B16 unexpectedly optimized disabled modules")
        if [row["path"] for row in summary["checkpoints"]] != [
            "checkpoint_00.pt", f"checkpoint_{spec.rollouts:02d}.pt",
        ]:
            raise ValueError("B16 requires actual checkpoint00 and final checkpoint only")
        final_panels = [row for row in summary["panels"] if row["status"] == "complete"]
        summary["evaluation_inference_counts"] = _aggregate_evaluation_inference(final_panels)
        if evaluate_initial:
            summary["stage_readings"] = b15._stage_readings(final_panels, spec.rollouts)
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_raw_sigma"] = b03.raw_sigma(agent)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B16 source bytes changed during fit")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        summary["counts"]["training_uav_steps"] = summary["counts"]["training_team_steps"] * 6
        summary["fit_started"] = summary["counts"]["training_team_steps"] > 0
        summary["counts"]["fits"] = int(summary["fit_started"])
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                telemetry = active.pop("_telemetry")
                component_sums = active.pop("component_sums")
                active["action_motion_telemetry_partial"] = b03._finish_motion(telemetry, 6)
                active["native_component_sums_partial"] = jsonable(component_sums)
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = optimizer_call_counts.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: count - int(before.get(name, 0))
                for name, count in optimizer_call_counts.items()
            }
            summary["incomplete_rollout"] = jsonable(active)
        if envs and any(env.records for env in envs) and not reset_identity_written:
            try:
                summary["training_reset_trace"] = b15._write_training_resets(
                    out / "training_reset_scenes.npz", envs, cell.training_env_seed_base,
                )
            except Exception as trace_exc:
                summary["training_reset_trace_failure"] = f"{type(trace_exc).__name__}: {trace_exc}"
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        if active_training_counter is not None:
            active_training_counter.close()
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        artifact_files = [
            path for path in out.rglob("*")
            if path.is_file() and path.name not in {"summary.json", "summary.json.partial"}
        ]
        summary["resources"] = {
            "command_wall_seconds": time.perf_counter() - command_start,
            "run_fit_wall_seconds": time.perf_counter() - started,
            "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss,
            "rss_scope": "scientific process Linux RUSAGE_SELF",
            "artifact_bytes_excluding_summary": sum(path.stat().st_size for path in artifact_files),
            "artifact_files_excluding_summary": len(artifact_files),
            "resources_unmeasured": ["peak_scratch_bytes", "other_processes"],
        }
        publish(summary["status"])
    return return_code
