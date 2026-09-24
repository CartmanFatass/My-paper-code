"""Fixed B07 E/M/U entropy intervention with frozen multi-stream readings."""
from __future__ import annotations

import contextlib
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import resource
import sys
import time
import traceback
from typing import Any, Iterator, Mapping

import numpy as np
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b04 import runner as b04
from experiments.candidates.complementary_skill_learning.b04.learning import (
    TrainingLawAgent,
    _capture_process_rng_state,
    _restore_process_rng_state,
)
from experiments.candidates.complementary_skill_learning.b05 import runner as b05
from scripts import run_fsd_uav_individual_renewal_b01 as support

DIRECTION = "complementary_skill_learning"
OBJECT = "complementary_skill_b07"
ARMS = ("M", "E", "U")
FIXED_SEED = 260924001
S_SEEDS = {f"S{i}": 260924101 + i for i in range(4)}
R_SEEDS = {f"R{i}": 262625201 + i for i in range(4)}
NON_LABEL_SEED = 260924105
UNIFORM_LOG_FACTOR = -math.log(6.0)
REFERENCE_SCHEMA = "complementary_skill_b07_m_final_s_reference_v1"
EXPECTED_NATIVE_OPTIMIZER_CALLS = {
    "E": {
        "coordinator": 675,
        "discoverer_actor": 101250,
        "discoverer_critic": 101250,
        "team_discriminator": 675,
        "individual_discriminator": 2700,
    },
    "M": {
        "coordinator": 675,
        "discoverer_actor": 101250,
        "discoverer_critic": 101250,
        "team_discriminator": 675,
        "individual_discriminator": 2700,
    },
    "U": {
        "coordinator": 0,
        "discoverer_actor": 101250,
        "discoverer_critic": 101250,
        "team_discriminator": 675,
        "individual_discriminator": 2700,
    },
}


@dataclass(frozen=True)
class Spec:
    n_agents: int = 6
    n_users: int = 50
    k: int = 10
    horizon: int = 500
    lanes: int = 16
    rollouts: int = 45
    eval_lanes: int = 32
    init_seed: int = 260924001
    head_seed: int = 260924002
    train_rng_seed: int = 260924003
    aux_seed: int = 260924004
    low_action_seed: int = 260924005
    high_collection_seed: int = 260924006
    high_update_seed: int = 260924007
    train_world_base: int = 2300000
    eval_world_base: int = 1700200
    threads: int = 4
    small_model: bool = False  # technical checks only; the CLI cannot enable it

    @property
    def world_base(self) -> int:
        """B05 trajectory helper compatibility; B07 keeps the explicit name."""

        return self.eval_world_base


DEFAULT_SPEC = Spec()
jsonable = b01.jsonable
write_json = b01.write_json
seed_rng = b01.seed_rng
update_digest = b01.update_digest
native_digest = b01.native_digest
frozen_digest = b01.frozen_digest
make_envs = b01.make_envs
physical_step = b01.physical_step
rng_state_digest = b04.rng_state_digest
store_verified_batch = b04.store_verified_batch


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_identity(path: Path) -> dict[str, Any]:
    return {"file": path.name, "bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def _fixed_addresses(spec: Spec) -> dict[str, int]:
    names = (
        "init_seed", "head_seed", "train_rng_seed", "aux_seed",
        "low_action_seed", "high_collection_seed", "high_update_seed",
        "train_world_base", "eval_world_base",
    )
    return {name: int(getattr(spec, name)) for name in names}


def _validate_protocol(spec: Spec) -> None:
    if _fixed_addresses(spec) != _fixed_addresses(DEFAULT_SPEC):
        raise ValueError("B07 fixed RNG/world addresses differ")
    if not spec.small_model and spec != DEFAULT_SPEC:
        raise ValueError("B07 production Spec differs from the fixed protocol")
    if spec.n_agents != 6 or spec.k != 10 or spec.horizon % spec.k:
        raise ValueError("B07 requires six agents and complete k10 renewals")


def make_config(spec: Spec, envs: list[Any], arm: str):
    arm = str(arm).upper()
    if arm not in ARMS:
        raise ValueError(arm)
    config = b04.make_config(spec, envs, "U" if arm == "U" else "M")
    if float(config.lambda_h) != 0.07 or float(config.lambda_l) != 0.05:
        raise ValueError("B07 inherited entropy coefficients differ from the protocol")
    config.lambda_h = 0.0 if arm == "E" else 0.07
    return config


def _build_agent(spec: Spec, config: Any, arm: str, out: Path, device: torch.device):
    agent = TrainingLawAgent(
        config=config,
        arm="U" if arm == "U" else "M",
        head_seed=spec.head_seed,
        aux_seed=spec.aux_seed,
        low_action_seed=spec.low_action_seed,
        high_collection_seed=spec.high_collection_seed,
        high_update_seed=spec.high_update_seed,
        log_dir=str(out / "learner_logs"),
        device=device,
    )
    agent.arm = arm
    return agent


def _prepare_output_root(out: Path | str, admission: Mapping[str, Any] | None) -> Path:
    try:
        return b05.prepare_output_root(out, admission)
    except FileExistsError as exc:
        raise FileExistsError(str(exc).replace("B05", "B07")) from exc


def _evaluation_state(agent: TrainingLawAgent) -> dict[str, Any]:
    return {
        "frozen_digest": frozen_digest(agent),
        "private_rng": agent.rng_stream_telemetry(),
        "sampler_rng": agent.sampler_rng_telemetry(),
        "process_rng": b05._process_telemetry(),
        "training": bool(agent.training),
        "module_modes": {
            name: bool(getattr(agent, name).training)
            for name in (*b01.MODULES, "g_head", "p_head")
            if getattr(agent, name, None) is not None
        },
    }


@contextlib.contextmanager
def _frozen_evaluation(agent: TrainingLawAgent) -> Iterator[dict[str, Any]]:
    process = _capture_process_rng_state()
    before = _evaluation_state(agent)
    optimizers = b05._optimizer_states(agent)
    modes = [
        (getattr(agent, name), getattr(agent, name).training)
        for name in (*b01.MODULES, "g_head", "p_head")
        if getattr(agent, name, None) is not None
    ]
    try:
        for module, _ in modes:
            module.eval()
        with torch.no_grad():
            yield before
    finally:
        for module, mode in modes:
            module.train(mode)
        _restore_process_rng_state(process)
    if _evaluation_state(agent) != before:
        raise RuntimeError("B07 evaluation changed weights, state, RNG, sampler, or modes")
    if not b05._nested_equal(b05._optimizer_states(agent), optimizers):
        raise RuntimeError("B07 evaluation changed optimizer state")


def _full_probabilities(
    agent: TrainingLawAgent,
    states: np.ndarray,
    observations: np.ndarray,
    team: np.ndarray,
    individual: np.ndarray,
    team_log_probs: np.ndarray | None = None,
    individual_log_probs: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Score canonical held prefixes; decoder individual logits are already mu."""

    result = agent.skill_coordinator.evaluate_held_batch(
        torch.as_tensor(states, dtype=torch.float32, device=agent.device),
        torch.as_tensor(observations, dtype=torch.float32, device=agent.device),
        torch.as_tensor(team, dtype=torch.long, device=agent.device),
        torch.as_tensor(individual, dtype=torch.long, device=agent.device),
    )
    team_distribution = torch.distributions.Categorical(logits=result["Z_logits"])
    individual_distribution = torch.distributions.Categorical(logits=result["z_logits"])
    team_probabilities = team_distribution.probs.cpu().numpy()
    individual_probabilities = individual_distribution.probs.cpu().numpy()
    team_entropy = team_distribution.entropy().cpu().numpy()
    individual_entropy = individual_distribution.entropy().cpu().numpy()
    if team_log_probs is not None and individual_log_probs is not None:
        selected_team = np.take_along_axis(
            team_probabilities, np.asarray(team)[:, None], axis=-1
        ).squeeze(-1)
        selected_individual = np.take_along_axis(
            individual_probabilities,
            np.asarray(individual)[..., None],
            axis=-1,
        ).squeeze(-1)
        if not np.allclose(np.log(selected_team), team_log_probs, rtol=0.0, atol=2e-6):
            raise RuntimeError("B07 S team probabilities differ from sampled log-probs")
        if not np.allclose(
            np.log(selected_individual), individual_log_probs, rtol=0.0, atol=2e-6
        ):
            raise RuntimeError("B07 S individual probabilities differ from sampled log-probs")
    return (
        team_probabilities.astype(np.float32),
        individual_probabilities.astype(np.float32),
        team_entropy.astype(np.float32),
        individual_entropy.astype(np.float32),
    )


def _entropy_from_probabilities(probabilities: np.ndarray) -> np.ndarray:
    """Categorical entropy with the mathematical convention 0*log(0)=0."""

    probabilities = np.asarray(probabilities)
    logs = np.zeros_like(probabilities)
    np.log(probabilities, out=logs, where=probabilities > 0)
    return -(probabilities * logs).sum(axis=-1)


def _panel_arrays(spec: Spec, agent: TrainingLawAgent, learned: bool) -> dict[str, np.ndarray]:
    arrays = b05._allocate_trajectory(
        spec, agent.config.state_dim, agent.config.obs_dim, agent.config.action_dim
    )
    if learned:
        arrays.update(
            team_factor_probabilities=np.full(
                (spec.horizon, spec.eval_lanes, 6), np.nan, np.float32
            ),
            individual_factor_probabilities=np.full(
                (spec.horizon, spec.eval_lanes, spec.n_agents, 6),
                np.nan,
                np.float32,
            ),
            team_factor_entropy=np.full(
                (spec.horizon, spec.eval_lanes), np.nan, np.float32
            ),
            individual_factor_entropy=np.full(
                (spec.horizon, spec.eval_lanes, spec.n_agents),
                np.nan,
                np.float32,
            ),
        )
    return arrays


def evaluate_panel(
    agent: TrainingLawAgent,
    spec: Spec,
    stage: str,
    panel: str,
    out: Path,
    *,
    counter: dict[str, int],
    call_audit: b05.EvaluationCallAudit,
    capture_reference: bool = False,
) -> tuple[dict[str, Any], dict[str, np.ndarray] | None]:
    if stage not in {"initial", "final"} or panel not in {*S_SEEDS, *R_SEEDS}:
        raise ValueError(f"invalid B07 panel {stage}_{panel}")
    learned = panel.startswith("S")
    arrays = _panel_arrays(spec, agent, learned)
    label_digest, initial_digest = hashlib.sha256(), hashlib.sha256()
    r_rng = np.random.Generator(np.random.PCG64(R_SEEDS[panel])) if not learned else None
    s_stream = b05.PersistentTorchRNG(S_SEEDS[panel]) if learned else None
    reference: dict[str, list[np.ndarray]] | None = (
        {name: [] for name in (
            "states", "observations", "team_labels", "individual_labels",
            "team_probabilities", "individual_probabilities",
        )}
        if capture_reference
        else None
    )
    raw = out / "raw"
    trajectory_path = raw / f"{stage}_{panel}_trajectory.npz"
    panel_path = raw / f"{stage}_{panel}.json"
    envs: list[Any] = []
    completed_steps = saturation = action_coordinates = 0
    audit_before = call_audit.snapshot()
    try:
        with _frozen_evaluation(agent) as frozen_before:
            seed_rng(NON_LABEL_SEED)
            envs = make_envs(spec, spec.eval_lanes, spec.eval_world_base)
            states, observations = b01.native._reset_all(envs)
            update_digest(initial_digest, states, observations)
            hidden = np.zeros(
                (spec.eval_lanes, spec.n_agents, agent.config.gru_hidden_size),
                np.float32,
            )
            arrays["states"][0] = states
            arrays["observations"][0] = observations
            team = individual = None
            for t in range(spec.horizon):
                if t % spec.k == 0:
                    if learned:
                        assert s_stream is not None
                        with s_stream.use():
                            team, individual, team_lp, individual_lp, order = b05._select_learned(
                                agent, states, observations, deterministic=False
                            )
                        team_probs, individual_probs, team_h, individual_h = _full_probabilities(
                            agent,
                            states,
                            observations,
                            team,
                            individual,
                            team_lp,
                            individual_lp,
                        )
                        arrays["team_factor_probabilities"][t] = team_probs
                        arrays["individual_factor_probabilities"][t] = individual_probs
                        arrays["team_factor_entropy"][t] = team_h
                        arrays["individual_factor_entropy"][t] = individual_h
                        counter["S_probability_forward_batches"] += 1
                        counter["S_probability_context_rows"] += spec.eval_lanes
                        counter["S_probability_factor_distributions"] += (
                            spec.eval_lanes * (spec.n_agents + 1)
                        )
                        if reference is not None:
                            for name, value in (
                                ("states", states),
                                ("observations", observations),
                                ("team_labels", team),
                                ("individual_labels", individual),
                                ("team_probabilities", team_probs),
                                ("individual_probabilities", individual_probs),
                            ):
                                reference[name].append(np.asarray(value).copy())
                    else:
                        assert r_rng is not None
                        team = r_rng.integers(0, 6, size=spec.eval_lanes, dtype=np.int64)
                        individual = r_rng.integers(
                            0, 6, size=(spec.eval_lanes, spec.n_agents), dtype=np.int64
                        )
                        team_lp = np.full(spec.eval_lanes, UNIFORM_LOG_FACTOR, np.float32)
                        individual_lp = np.full(
                            (spec.eval_lanes, spec.n_agents), UNIFORM_LOG_FACTOR, np.float32
                        )
                        order = np.broadcast_to(
                            np.arange(spec.n_agents, dtype=np.int64),
                            (spec.eval_lanes, spec.n_agents),
                        ).copy()
                    update_digest(
                        label_digest, np.asarray([t], np.int64), team, individual
                    )
                    arrays["renewal"][t] = True
                    arrays["team_factor_log_probs"][t] = team_lp
                    arrays["individual_factor_log_probs"][t] = individual_lp
                    arrays["renewal_order"][t] = order
                if team is None or individual is None:
                    raise RuntimeError("B07 labels were not assigned before low control")
                arrays["team_labels"][t] = team
                arrays["individual_labels"][t] = individual
                raw_actions, hidden = b01.low_actions(
                    agent, observations, individual, hidden, deterministic=True
                )
                clipped = np.clip(raw_actions, -1.0, 1.0)
                arrays["raw_mean_actions"][t] = raw_actions
                arrays["clipped_actions"][t] = clipped
                saturation += int((np.abs(raw_actions) > 1).sum())
                action_coordinates += raw_actions.size
                next_states, next_observations = [], []
                for lane, env in enumerate(envs):
                    state, obs, reward, done, parts, executed = physical_step(
                        env, raw_actions[lane]
                    )
                    if not np.array_equal(executed, clipped[lane]):
                        raise RuntimeError("B07 recorded clip differs from physical action")
                    if done != (t == spec.horizon - 1):
                        raise ValueError("unexpected B07 evaluation episode boundary")
                    next_states.append(state)
                    next_observations.append(obs)
                    arrays["rewards"][t, lane] = reward
                    arrays["episode_ends"][t, lane] = done
                    for name in b01.COMPONENTS:
                        arrays[name][t, lane] = parts[name]
                    counter["evaluation_transitions"] += 1
                    counter["evaluation_episodes"] += int(done)
                    counter[f"{panel[0]}_transitions"] += 1
                states, observations = np.stack(next_states), np.stack(next_observations)
                arrays["states"][t + 1] = states
                arrays["observations"][t + 1] = observations
                completed_steps = t + 1
            panel_summary = b05._panel_summary_from_trajectory(
                panel,
                spec,
                arrays,
                label_digest,
                initial_digest,
                saturation,
                action_coordinates,
            )
            panel_summary.update(stage=stage, panel_key=f"{stage}_{panel}")
            panel_summary["frozen_state_before"] = frozen_before
    except Exception as exc:
        partial = {
            "status": "failed",
            "stage": stage,
            "panel": panel,
            "completed_steps": completed_steps,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
        if completed_steps:
            partial["trajectory"] = b05._save_npz(
                trajectory_path, arrays, completed_steps
            )
        write_json(panel_path, partial)
        raise
    finally:
        for env in envs:
            env.close()

    mutation_delta = b05._counter_delta(call_audit.snapshot(), audit_before)
    if any(mutation_delta.values()):
        raise RuntimeError("B07 evaluation reached a prohibited mutation path")
    panel_summary["observed_mutation_calls"] = mutation_delta
    panel_summary["non_label_rng_seed"] = NON_LABEL_SEED
    if learned:
        assert s_stream is not None
        renewals = arrays["renewal"]
        panel_summary["label_rng"] = {
            "kind": "persistent_private_torch_cpu_and_active_cuda",
            "seed": S_SEEDS[panel],
            "uses": s_stream.uses,
            "state": s_stream.telemetry(),
        }
        panel_summary["factor_law"] = {
            "team": "unchanged_native_team_logits_no_uniform_floor",
            "individual": "native_MixtureSkillDecoder_mu=.9*pi+.1/6_once",
        }
        panel_summary["entropy"] = {
            "context_distribution": f"B07 {stage} {panel} own evolving states/prefixes",
            "team_mean": float(arrays["team_factor_entropy"][renewals].mean()),
            "individual_mean": float(
                arrays["individual_factor_entropy"][renewals].mean()
            ),
            "team_factor_count": int(renewals.sum() * spec.eval_lanes),
            "individual_factor_count": int(
                renewals.sum() * spec.eval_lanes * spec.n_agents
            ),
        }
    else:
        panel_summary["label_rng"] = {
            "kind": "PCG64",
            "seed": R_SEEDS[panel],
            "draw_order": "team[lanes] then individual[lanes,n_agents] at each renewal",
        }
        panel_summary["entropy"] = {
            "context_distribution": "independent uniform factors",
            "team_mean": math.log(6.0),
            "individual_mean": math.log(6.0),
            "team_factor_count": spec.horizon // spec.k * spec.eval_lanes,
            "individual_factor_count": (
                spec.horizon // spec.k * spec.eval_lanes * spec.n_agents
            ),
        }
    panel_summary["trajectory"] = b05._save_npz(
        trajectory_path, arrays, completed_steps
    )
    write_json(panel_path, panel_summary)
    packed_reference = (
        {name: np.stack(values) for name, values in reference.items()}
        if reference is not None
        else None
    )
    return panel_summary, packed_reference


def _module_snapshot(module: torch.nn.Module) -> list[torch.Tensor]:
    return [parameter.detach().double().clone() for parameter in module.parameters()]


def _module_relative_movement(
    module: torch.nn.Module, initial: list[torch.Tensor]
) -> float:
    parameters = list(module.parameters())
    with torch.no_grad():
        numerator = torch.sqrt(
            sum(
                ((parameter.detach().double() - reference) ** 2).sum()
                for parameter, reference in zip(parameters, initial)
            )
        ).item()
        denominator = torch.sqrt(sum(reference.square().sum() for reference in initial)).item()
    return float(numerator / max(denominator, 1e-12))


def save_checkpoint(
    agent: TrainingLawAgent, path: Path, config: dict[str, Any], stage: int
) -> dict[str, Any]:
    body = {
        "object_id": OBJECT,
        "arm": agent.arm,
        "stage": stage,
        "config": config,
        "native": {
            name: getattr(agent, name).state_dict()
            for name in b01.MODULES
            if getattr(agent, name) is not None
        },
        "normalizers": {
            name: copy.deepcopy(getattr(agent, name)) for name in b01.NORMALIZERS
        },
        "auxiliary": agent.auxiliary_state_dict(),
        "rng": {
            "schema": "complementary_skill_b04_rng_v1",
            "default_process": copy.deepcopy(_capture_process_rng_state()),
            "private_streams": agent.rng_stream_state_dict(),
            "rollout_samplers": agent.sampler_rng_state_dict(),
        },
    }
    torch.save(body, path)
    return {
        "file": path.name,
        "sha256": b01.native._sha256_file(path),
        "bytes": path.stat().st_size,
        "native_digest": native_digest(agent),
        "frozen_digest": frozen_digest(agent),
        "rng_streams": agent.rng_stream_telemetry(),
        "sampler_rng_streams": agent.sampler_rng_telemetry(),
    }


def _storage_telemetry() -> dict[str, Any]:
    return {
        "batch_calls": 0,
        "expected_rows": 0,
        "verified_rows": 0,
        "failures": 0,
        "last_failure": None,
    }


def _write_training_occupancy(
    out: Path,
    rollout: int,
    team: np.ndarray,
    individual: np.ndarray,
    joint: Mapping[str, int],
) -> dict[str, Any]:
    path = out / "raw" / "training_occupancy.json"
    write_json(
        path,
        {
            "rollout": rollout,
            "actual_team_label_occupancy": team,
            "actual_individual_label_occupancy": individual,
            "actual_joint_occupancy": joint,
        },
    )
    return {**_file_identity(path), "path": "raw/training_occupancy.json"}


def _compact_training_row(row: Mapping[str, Any]) -> dict[str, Any]:
    losses = row["native_losses"]
    auxiliary = row["auxiliary"]
    return {
        "rollout": row["rollout"],
        "training_transitions": row["training_transitions"],
        "training_J": row["training_J"],
        "native_losses": {
            name: losses[name]
            for name in (
                "coordinator_loss", "coordinator_policy_loss", "coordinator_value_loss",
                "discoverer_loss", "discoverer_policy_loss", "discoverer_value_loss",
                "discriminator_loss", "discriminator_team_loss",
                "discriminator_individual_loss", "team_skill_entropy",
                "agent_skill_entropy", "action_entropy",
            )
        },
        "coordinator_update_reading": row["coordinator_update_reading"],
        "optimizer_delta": row["optimizer_delta"],
        "relative_initialization_displacement": row[
            "relative_initialization_displacement"
        ],
        "auxiliary_head_relative_movement": row[
            "auxiliary_head_relative_movement"
        ],
        "auxiliary": {
            name: auxiliary[name]
            for name in (
                "samples", "head_optimizer_steps", "trunk_optimizer_steps",
                "loss_normalized", "loss_raw", "gradient_norm_mean",
                "trunk_relative_movement", "raw_predictions",
            )
        },
        "raw_saturation_fraction": row["raw_saturation_fraction"],
        "wall_seconds": row["wall_seconds"],
    }


def _compact_summary(summary: Mapping[str, Any], out: Path) -> dict[str, Any]:
    compact = copy.deepcopy(dict(summary))
    full_rows = compact.pop("training_rows", [])
    compact["training_rows"] = [_compact_training_row(row) for row in full_rows]
    compact.pop("actual_team_label_occupancy", None)
    compact.pop("actual_individual_label_occupancy", None)
    compact.pop("actual_joint_occupancy", None)
    compact.pop("d2_retained_work", None)
    compact.pop("auxiliary_history", None)
    locators = dict(compact.get("bulk_locators", {}))
    for name, relative in (
        ("training_rows", "training.jsonl"),
        ("auxiliary_predictions", "auxiliary_predictions.jsonl"),
        ("training_occupancy", "raw/training_occupancy.json"),
    ):
        path = out / relative
        if path.is_file():
            locators[name] = {**_file_identity(path), "path": relative}
    compact["bulk_locators"] = locators
    compact["summary_storage"] = {
        "kind": "compact_versionable_view",
        "full_training_rows": "training.jsonl",
        "full_occupancy": "raw/training_occupancy.json",
        "raw_panels": "raw/*_trajectory.npz",
    }
    return compact


def _reference_metadata(
    summary: Mapping[str, Any], spec: Spec, state_dim: int, obs_dim: int
) -> dict[str, Any]:
    return {
        "schema": REFERENCE_SCHEMA,
        "object_id": OBJECT,
        "arm": "M",
        "stage": "final",
        "spec": asdict(spec),
        "stream_order": [f"S{i}" for i in range(4)],
        "stream_seeds": S_SEEDS,
        "worlds": list(range(spec.eval_world_base, spec.eval_world_base + spec.eval_lanes)),
        "row_order": "stream,renewal,world; individual prefixes are canonical agent order",
        "state_dim": int(state_dim),
        "obs_dim": int(obs_dim),
        "source_launch_sha": summary["launch_sha"],
        "source_final_native_digest": summary["final_native_digest"],
        "source_final_frozen_digest": summary["final_frozen_digest"],
        "source_final_checkpoint_sha256": summary["checkpoints"]["final"]["sha256"],
        "individual_probability_law": "MixtureSkillDecoder output mu=.9*pi+.1/6 exactly once",
        "team_probability_law": "unchanged native team logits with no mixture floor",
    }


def save_reference(
    out: Path,
    captures: Mapping[str, Mapping[str, np.ndarray]],
    summary: Mapping[str, Any],
    spec: Spec,
) -> dict[str, Any]:
    expected_streams = [f"S{i}" for i in range(4)]
    if list(captures) != expected_streams:
        raise ValueError("B07 M reference stream order differs")
    arrays = {
        name: np.stack([captures[stream][name] for stream in expected_streams])
        for name in next(iter(captures.values()))
    }
    metadata = _reference_metadata(
        summary, spec, arrays["states"].shape[-1], arrays["observations"].shape[-1]
    )
    arrays["metadata_json"] = np.asarray(
        json.dumps(metadata, sort_keys=True, allow_nan=False)
    )
    path = out / "raw" / "final_S_reference.npz"
    np.savez_compressed(path, **arrays)
    identity = _file_identity(path)
    return {
        **identity,
        "path": str(path.resolve()),
        "context_rows": 4 * (spec.horizon // spec.k) * spec.eval_lanes,
        "factor_distributions": (
            4 * (spec.horizon // spec.k) * spec.eval_lanes * (spec.n_agents + 1)
        ),
        "arrays": b05._trajectory_manifest(arrays),
        "metadata": metadata,
    }


def validate_reference(
    path: Path | str,
    expected_sha256: str,
    spec: Spec,
    *,
    expected_source_launch_sha: str,
) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise ValueError("B07 E reference file is absent")
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise ValueError("B07 E reference SHA256 differs")
    try:
        with np.load(path, allow_pickle=False) as loaded:
            names = set(loaded.files)
            required = {
                "states", "observations", "team_labels", "individual_labels",
                "team_probabilities", "individual_probabilities", "metadata_json",
            }
            if names != required:
                raise ValueError("B07 E reference arrays differ")
            metadata = json.loads(str(loaded["metadata_json"].item()))
            arrays = {name: loaded[name].copy() for name in required - {"metadata_json"}}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith("B07"):
            raise
        raise ValueError("B07 E reference NPZ is invalid") from exc
    if metadata.get("source_launch_sha") != expected_source_launch_sha:
        raise ValueError("B07 E reference source_launch_sha differs")
    for name in (
        "source_final_native_digest",
        "source_final_frozen_digest",
        "source_final_checkpoint_sha256",
    ):
        value = metadata.get(name)
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError(f"B07 E reference has malformed {name}")
    schema_envs = make_envs(spec, 1, spec.eval_world_base)
    try:
        expected_state_dim = int(schema_envs[0].state_dim)
        expected_obs_dim = int(schema_envs[0].obs_dim)
    finally:
        for env in schema_envs:
            env.close()
    expected_metadata = {
        "schema": REFERENCE_SCHEMA,
        "object_id": OBJECT,
        "arm": "M",
        "stage": "final",
        "spec": asdict(spec),
        "stream_order": [f"S{i}" for i in range(4)],
        "stream_seeds": S_SEEDS,
        "worlds": list(range(spec.eval_world_base, spec.eval_world_base + spec.eval_lanes)),
        "row_order": "stream,renewal,world; individual prefixes are canonical agent order",
        "state_dim": expected_state_dim,
        "obs_dim": expected_obs_dim,
        "individual_probability_law": "MixtureSkillDecoder output mu=.9*pi+.1/6 exactly once",
        "team_probability_law": "unchanged native team logits with no mixture floor",
    }
    for name, value in expected_metadata.items():
        if metadata.get(name) != value:
            raise ValueError(f"B07 E reference metadata differs: {name}")
    r, b, n = spec.horizon // spec.k, spec.eval_lanes, spec.n_agents
    expected_shapes = {
        "states": (4, r, b, expected_state_dim),
        "observations": (4, r, b, n, expected_obs_dim),
        "team_labels": (4, r, b),
        "individual_labels": (4, r, b, n),
        "team_probabilities": (4, r, b, 6),
        "individual_probabilities": (4, r, b, n, 6),
    }
    if any(arrays[name].shape != shape for name, shape in expected_shapes.items()):
        raise ValueError("B07 E reference array shape differs")
    if not np.isfinite(arrays["states"]).all() or not np.isfinite(
        arrays["observations"]
    ).all():
        raise ValueError("B07 E reference contexts are nonfinite")
    for name in ("team_labels", "individual_labels"):
        labels = arrays[name]
        if not np.issubdtype(labels.dtype, np.integer) or np.any(labels < 0) or np.any(
            labels >= 6
        ):
            raise ValueError("B07 E reference labels are outside integer support 0..5")
    team_probabilities = arrays["team_probabilities"]
    individual_probabilities = arrays["individual_probabilities"]
    if not np.isfinite(team_probabilities).all() or np.any(team_probabilities < 0):
        raise ValueError("B07 E reference team probabilities are invalid")
    if not np.isfinite(individual_probabilities).all() or np.any(
        individual_probabilities <= 0
    ):
        raise ValueError("B07 E reference individual probabilities are invalid")
    for probabilities in (team_probabilities, individual_probabilities):
        if not np.allclose(
            probabilities.sum(axis=-1), 1.0, rtol=1e-6, atol=1e-6
        ):
            raise ValueError("B07 E reference probabilities are not normalized")
    return {
        "path": str(path.resolve()),
        "sha256": actual_sha256,
        "bytes": path.stat().st_size,
        "metadata": metadata,
        "arrays": arrays,
    }


def score_reference(
    agent: TrainingLawAgent,
    reference: Mapping[str, Any],
    out: Path,
    counts: dict[str, int],
) -> dict[str, Any]:
    arrays = reference["arrays"]
    shape = arrays["team_probabilities"].shape
    e_team = np.empty(shape, np.float32)
    e_individual = np.empty(arrays["individual_probabilities"].shape, np.float32)
    started = time.perf_counter()
    before = _evaluation_state(agent)
    optimizers = b05._optimizer_states(agent)
    with _frozen_evaluation(agent):
        for stream in range(shape[0]):
            for renewal in range(shape[1]):
                team_probs, individual_probs, _, _ = _full_probabilities(
                    agent,
                    arrays["states"][stream, renewal],
                    arrays["observations"][stream, renewal],
                    arrays["team_labels"][stream, renewal],
                    arrays["individual_labels"][stream, renewal],
                )
                e_team[stream, renewal] = team_probs
                e_individual[stream, renewal] = individual_probs
                counts["reference_scoring_batches"] += 1
                counts["reference_scoring_context_rows"] += shape[2]
                counts["reference_scoring_factor_distributions"] += shape[2] * 7
    if _evaluation_state(agent) != before or not b05._nested_equal(
        b05._optimizer_states(agent), optimizers
    ):
        raise RuntimeError("B07 E common-context scoring changed frozen state")
    m_team = arrays["team_probabilities"]
    m_individual = arrays["individual_probabilities"]
    e_team_h = _entropy_from_probabilities(e_team)
    m_team_h = _entropy_from_probabilities(m_team)
    e_individual_h = _entropy_from_probabilities(e_individual)
    m_individual_h = _entropy_from_probabilities(m_individual)
    path = out / "raw" / "E_on_M_final_S_reference.npz"
    np.savez_compressed(
        path,
        E_team_probabilities=e_team,
        E_individual_probabilities=e_individual,
        M_team_probabilities=m_team,
        M_individual_probabilities=m_individual,
        E_team_entropy=e_team_h,
        M_team_entropy=m_team_h,
        E_individual_entropy=e_individual_h,
        M_individual_entropy=m_individual_h,
        team_entropy_difference=e_team_h - m_team_h,
        individual_entropy_difference=e_individual_h - m_individual_h,
    )
    return {
        "input": {
            "path": reference["path"],
            "sha256": reference["sha256"],
            "bytes": reference["bytes"],
            "source": reference["metadata"],
        },
        "output": {**_file_identity(path), "path": str(path.resolve())},
        "batches": counts["reference_scoring_batches"],
        "context_rows": counts["reference_scoring_context_rows"],
        "factor_distributions": counts["reference_scoring_factor_distributions"],
        "environment_transitions": 0,
        "rng_draws": 0,
        "wall_seconds": time.perf_counter() - started,
        "entropy": {
            "E_team_mean": float(e_team_h.mean()),
            "M_team_mean": float(m_team_h.mean()),
            "E_minus_M_team_mean": float((e_team_h - m_team_h).mean()),
            "E_individual_mean": float(e_individual_h.mean()),
            "M_individual_mean": float(m_individual_h.mean()),
            "E_minus_M_individual_mean": float(
                (e_individual_h - m_individual_h).mean()
            ),
        },
    }


def _metric_arrays(panel: Mapping[str, Any]) -> dict[str, np.ndarray]:
    return b05._metric_arrays(panel)


def aggregate_arm(
    panels: Mapping[str, Mapping[str, Any]], arm: str, spec: Spec
) -> dict[str, Any]:
    result: dict[str, Any] = {"worlds": np.arange(
        spec.eval_world_base, spec.eval_world_base + spec.eval_lanes
    )}
    for metric in ("J", "users", "coverage", "quality", "height"):
        if arm in {"E", "M"}:
            s = np.stack([_metric_arrays(panels[f"final_S{i}"])[metric] for i in range(4)])
            r = np.stack([_metric_arrays(panels[f"final_R{i}"])[metric] for i in range(4)])
            mean_s, mean_r = s.mean(axis=0), r.mean(axis=0)
            row = {
                "world_mean_S4": mean_s,
                "world_mean_R4": mean_r,
                "G_S_minus_R_world": mean_s - mean_r,
                "mean_S4": float(mean_s.mean()),
                "mean_R4": float(mean_r.mean()),
                "G_S_minus_R": float((mean_s - mean_r).mean()),
                "S_stream_world_means": {
                    f"S{i}": _metric_arrays(panels[f"final_S{i}"])[metric]
                    for i in range(4)
                },
                "R_stream_world_means": {
                    f"R{i}": _metric_arrays(panels[f"final_R{i}"])[metric]
                    for i in range(4)
                },
                "learning_final_S0_minus_initial_S0_world": (
                    _metric_arrays(panels["final_S0"])[metric]
                    - _metric_arrays(panels["initial_S0"])[metric]
                ),
            }
        else:
            r = np.stack([_metric_arrays(panels[f"final_R{i}"])[metric] for i in range(4)])
            mean_r = r.mean(axis=0)
            row = {
                "world_mean_R4": mean_r,
                "mean_R4": float(mean_r.mean()),
                "R_stream_world_means": {
                    f"R{i}": _metric_arrays(panels[f"final_R{i}"])[metric]
                    for i in range(4)
                },
            }
        row["learning_final_R0_minus_initial_R0_world"] = (
            _metric_arrays(panels["final_R0"])[metric]
            - _metric_arrays(panels["initial_R0"])[metric]
        )
        result[metric] = row
    return result


def aggregate_batch(
    m: Mapping[str, Any], e: Mapping[str, Any], u: Mapping[str, Any]
) -> dict[str, Any]:
    summaries = {"M": m, "E": e, "U": u}
    if any(summaries[arm].get("arm") != arm for arm in summaries):
        raise ValueError("B07 batch summaries have the wrong arms")
    if len({json.dumps(summary["spec"], sort_keys=True) for summary in summaries.values()}) != 1:
        raise ValueError("B07 batch summaries do not share one Spec")
    result: dict[str, Any] = {}
    for metric in ("J", "users", "coverage", "quality", "height"):
        es = np.asarray(e["aggregates"][metric]["world_mean_S4"])
        er = np.asarray(e["aggregates"][metric]["world_mean_R4"])
        ms = np.asarray(m["aggregates"][metric]["world_mean_S4"])
        mr = np.asarray(m["aggregates"][metric]["world_mean_R4"])
        ur = np.asarray(u["aggregates"][metric]["world_mean_R4"])
        p, d, ge, gm, bank = es - ur, es - ms, es - er, ms - mr, er - mr
        interaction = ge - gm
        identity = d - bank
        if not np.allclose(interaction, identity, rtol=0.0, atol=1e-12):
            raise ValueError(f"B07 interaction identity failed for {metric}")
        result[metric] = {
            "P_E_S_minus_U_R_world": p,
            "D_E_S_minus_M_S_world": d,
            "G_E_world": ge,
            "G_M_world": gm,
            "I_world": interaction,
            "bank_E_R_minus_M_R_world": bank,
            "means": {
                "P": float(p.mean()), "D": float(d.mean()),
                "G_E": float(ge.mean()), "G_M": float(gm.mean()),
                "I": float(interaction.mean()), "bank": float(bank.mean()),
            },
            "identity_residual": float(np.max(np.abs(interaction - identity))),
        }
    return result


def _evaluate_schedule(
    agent: TrainingLawAgent,
    spec: Spec,
    arm: str,
    stage: str,
    panels: list[str],
    out: Path,
    summary: dict[str, Any],
    counts: dict[str, int],
) -> dict[str, dict[str, np.ndarray]]:
    before = _evaluation_state(agent)
    optimizers = b05._optimizer_states(agent)
    captures: dict[str, dict[str, np.ndarray]] = {}
    with b05.EvaluationCallAudit(agent) as audit:
        for panel in panels:
            result, capture = evaluate_panel(
                agent,
                spec,
                stage,
                panel,
                out,
                counter=counts,
                call_audit=audit,
                capture_reference=(arm == "M" and stage == "final" and panel.startswith("S")),
            )
            summary["panels"][f"{stage}_{panel}"] = result
            if capture is not None:
                captures[panel] = capture
            write_json(out / "summary.json", _compact_summary(summary, out))
        observed = audit.snapshot()
    if any(observed.values()):
        raise RuntimeError("B07 evaluation schedule reached a prohibited mutation path")
    if _evaluation_state(agent) != before or not b05._nested_equal(
        b05._optimizer_states(agent), optimizers
    ):
        raise RuntimeError("B07 evaluation schedule changed frozen state")
    summary.setdefault("evaluation_audits", {})[stage] = observed
    return captures


def _validate_completed_contract(summary: dict[str, Any], spec: Spec) -> None:
    arm = summary["arm"]
    panel_count = 10 if arm in {"E", "M"} else 5
    s_panel_count = 5 if arm in {"E", "M"} else 0
    expected_counts = {
        "started_fits": 1,
        "model_constructions": 1,
        "training_transitions": spec.lanes * spec.horizon * spec.rollouts,
        "stored_transitions": spec.lanes * spec.horizon * spec.rollouts,
        "training_episodes": spec.lanes * spec.rollouts,
        "native_updates": spec.rollouts,
        "evaluation_transitions": panel_count * spec.eval_lanes * spec.horizon,
        "evaluation_episodes": panel_count * spec.eval_lanes,
        "S_transitions": s_panel_count * spec.eval_lanes * spec.horizon,
        "R_transitions": (panel_count - s_panel_count) * spec.eval_lanes * spec.horizon,
        "S_probability_forward_batches": s_panel_count * spec.horizon // spec.k,
        "S_probability_context_rows": (
            s_panel_count * spec.horizon // spec.k * spec.eval_lanes
        ),
        "S_probability_factor_distributions": (
            s_panel_count * spec.horizon // spec.k * spec.eval_lanes * 7
        ),
        "reference_scoring_batches": (
            4 * spec.horizon // spec.k if arm == "E" else 0
        ),
        "reference_scoring_context_rows": (
            4 * spec.horizon // spec.k * spec.eval_lanes if arm == "E" else 0
        ),
        "reference_scoring_factor_distributions": (
            4 * spec.horizon // spec.k * spec.eval_lanes * 7 if arm == "E" else 0
        ),
    }
    if summary["counts"] != expected_counts:
        raise ValueError(f"B07 transition/update/read counts differ: {summary['counts']}")
    initial = ["initial_S0", "initial_R0"] if arm in {"E", "M"} else ["initial_R0"]
    final = (
        [item for i in range(4) for item in (f"final_S{i}", f"final_R{i}")]
        if arm in {"E", "M"}
        else [f"final_R{i}" for i in range(4)]
    )
    expected_panels = initial + final
    if list(summary["panels"]) != expected_panels:
        raise ValueError("B07 arm has the wrong evaluation panel order")
    panels = summary["panels"]
    if len({panel["physical_initial_state_sha256"] for panel in panels.values()}) != 1:
        raise ValueError("B07 panels did not repeat one physical initial state")
    if (
        panels["initial_R0"]["selected_label_stream_sha256"]
        != panels["final_R0"]["selected_label_stream_sha256"]
    ):
        raise ValueError("B07 R0 did not repeat one label stream")
    if any(
        panel["optimizer_calls"]
        or panel["normalizer_updates"]
        or any(panel["observed_mutation_calls"].values())
        for panel in panels.values()
    ):
        raise ValueError("B07 evaluation changed training state")
    storage = summary["storage_verification"]
    if storage != {
        "batch_calls": spec.horizon * spec.rollouts,
        "expected_rows": expected_counts["stored_transitions"],
        "verified_rows": expected_counts["stored_transitions"],
        "failures": 0,
        "last_failure": None,
    }:
        raise ValueError("B07 did not verify every native storage row")
    expected_label_batches = spec.horizon * spec.rollouts
    if summary["label_flow_checks"] != {
        "action_batches": expected_label_batches,
        "reward_batches": expected_label_batches,
        "factual_batches": expected_label_batches,
        "storage_batches": expected_label_batches,
        "failures": 0,
    }:
        raise ValueError("B07 did not verify each low/reward/factual/storage label path")

    if not spec.small_model:
        if summary["native_optimizer_calls"] != EXPECTED_NATIVE_OPTIMIZER_CALLS[arm]:
            raise ValueError("B07 production native optimizer counts differ")
        auxiliary = {
            "head_G": sum(
                row["auxiliary"]["head_optimizer_steps"]["G"]
                for row in summary["training_rows"]
            ),
            "head_P": sum(
                row["auxiliary"]["head_optimizer_steps"]["P"]
                for row in summary["training_rows"]
            ),
            "trunk": sum(
                row["auxiliary"]["trunk_optimizer_steps"]
                for row in summary["training_rows"]
            ),
        }
        if auxiliary != {"head_G": 315, "head_P": 315, "trunk": 0}:
            raise ValueError("B07 auxiliary optimizer counts differ")
        summary["auxiliary_optimizer_calls"] = auxiliary

    final_movement = summary["training_rows"][-1]["relative_initialization_displacement"]
    trained = (
        "discoverer_actor",
        "discoverer_critic",
        "team_discriminator",
        "individual_discriminator",
    )
    if any(not (final_movement[name] > 0.0) for name in trained):
        raise ValueError("a required B07 native component did not move")
    if arm == "U" and final_movement["coordinator"] != 0.0:
        raise ValueError("U coordinator parameters changed")
    if arm in {"E", "M"} and not (final_movement["coordinator"] > 0.0):
        raise ValueError(f"{arm} coordinator parameters did not move")
    if any(
        not (summary["training_rows"][-1]["auxiliary_head_relative_movement"][name] > 0.0)
        for name in ("G", "P")
    ):
        raise ValueError("a required B07 factual head did not move")
    if arm == "M" and summary.get("M_final_S_reference", {}).get(
        "factor_distributions"
    ) != 4 * spec.horizon // spec.k * spec.eval_lanes * 7:
        raise ValueError("B07 M reference pool count differs")
    if arm == "E" and summary.get("common_context_scoring", {}).get(
        "factor_distributions"
    ) != 4 * spec.horizon // spec.k * spec.eval_lanes * 7:
        raise ValueError("B07 E common-context score count differs")


def run_fit(
    arm: str,
    out: Path | str,
    launch_sha: str,
    *,
    spec: Spec = DEFAULT_SPEC,
    device: str | torch.device = "cuda",
    admission: dict[str, Any] | None = None,
    reference_path: Path | str | None = None,
    reference_sha256: str | None = None,
):
    arm = str(arm).upper()
    if arm not in ARMS:
        raise ValueError(arm)
    _validate_protocol(spec)
    reference = None
    if arm == "E":
        if reference_path is None or reference_sha256 is None:
            raise ValueError("B07 E requires the pinned M final-S reference path and SHA256")
        reference = validate_reference(
            reference_path,
            reference_sha256,
            spec,
            expected_source_launch_sha=launch_sha,
        )
    elif reference_path is not None or reference_sha256 is not None:
        raise ValueError("B07 M/U do not accept an external reference")

    out = _prepare_output_root(out, admission)
    (out / "raw").mkdir()
    torch.set_num_threads(spec.threads)
    logging.getLogger().setLevel(logging.WARNING)
    started = time.perf_counter()
    cpu_started = resource.getrusage(resource.RUSAGE_SELF)
    count_names = (
        "started_fits", "model_constructions", "training_transitions",
        "stored_transitions", "training_episodes", "native_updates",
        "evaluation_transitions", "evaluation_episodes", "S_transitions",
        "R_transitions", "S_probability_forward_batches",
        "S_probability_context_rows", "S_probability_factor_distributions",
        "reference_scoring_batches", "reference_scoring_context_rows",
        "reference_scoring_factor_distributions",
    )
    counts = {name: 0 for name in count_names}
    training_law = (
        "learned_team_and_mu=.9*pi+.1/6_individual_lambda_h=0"
        if arm == "E"
        else (
            "learned_team_and_mu=.9*pi+.1/6_individual_lambda_h=.07"
            if arm == "M"
            else "independent_uniform_team_and_individual_lambda_h=.07_no_high_update"
        )
    )
    summary: dict[str, Any] = {
        "object_id": OBJECT,
        "direction": DIRECTION,
        "arm": arm,
        "training_law": training_law,
        "launch_sha": launch_sha,
        "status": "incomplete",
        "spec": asdict(spec),
        "device": str(device),
        "admission": admission,
        "counts": counts,
        "training_rows": [],
        "panels": {},
        "checkpoints": {},
        "storage_verification": _storage_telemetry(),
        "d2_retained_work": [],
        "reference_binding": (
            None
            if reference is None
            else {
                "path": reference["path"],
                "sha256": reference["sha256"],
                "bytes": reference["bytes"],
                "source": reference["metadata"],
            }
        ),
    }
    summary["runtime"] = {
        "python": sys.version,
        "numpy": np.__version__,
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "torch_threads": torch.get_num_threads(),
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
        },
        "learner_dtype": "float32",
        "reward_return_dtype": "float64",
        "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
    }
    write_json(
        out / "config.json",
        {
            "object_id": OBJECT,
            "arm": arm,
            "spec": asdict(spec),
            "launch_sha": launch_sha,
            "device": str(device),
            "training_law": training_law,
            "reference_binding": summary["reference_binding"],
        },
    )

    envs: list[Any] = []
    agent = counters = None
    try:
        device = torch.device(device)
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
            summary["runtime"]["cuda_device"] = torch.cuda.get_device_name(device)
        envs = make_envs(spec, spec.lanes, spec.train_world_base)
        config = make_config(spec, envs, arm)
        summary["learner_config"] = effective_config(config)
        summary["intervention"] = {
            "public_arm": arm,
            "lambda_h": float(config.lambda_h),
            "lambda_l": float(config.lambda_l),
            "disable_high_level_training": bool(config.disable_high_level_training),
            "only_declared_E_change": "lambda_h=.07_to_0" if arm == "E" else None,
        }
        seed_rng(spec.init_seed)
        agent = _build_agent(spec, config, arm, out, device)
        counts["model_constructions"] += 1
        theta0 = b01.native._capture_theta0(agent)
        head0 = {
            "G": _module_snapshot(agent.g_head),
            "P": _module_snapshot(agent.p_head),
        }
        counters = support.optimizer_counters(agent)
        summary["initial_native_digest"] = native_digest(agent)
        summary["initial_frozen_digest"] = frozen_digest(agent)
        summary["auxiliary_parameter_counts"] = jsonable(agent.parameter_counts)
        summary["auxiliary_architecture"] = jsonable(agent.auxiliary_architecture)
        seed_rng(spec.train_rng_seed)
        summary["initial_default_rng_state_sha256"] = rng_state_digest()
        summary["initial_private_rng_streams"] = agent.rng_stream_telemetry()
        summary["initial_sampler_rng_streams"] = agent.sampler_rng_telemetry()
        summary["checkpoints"]["initial"] = save_checkpoint(
            agent, out / "initial.pt", summary["learner_config"], 0
        )
        initial_panels = ["S0", "R0"] if arm in {"E", "M"} else ["R0"]
        _evaluate_schedule(
            agent, spec, arm, "initial", initial_panels, out, summary, counts
        )
        states, observations = b01.native._reset_all(envs)
        env_steps = np.zeros(spec.lanes, np.int64)
        dones = np.zeros(spec.lanes, bool)
        agent.train(True)
        counts["started_fits"] += 1
        first_digest = hashlib.sha256()
        label_hist = np.zeros((spec.n_agents, 6), np.int64)
        team_hist = np.zeros(6, np.int64)
        joint_hist: dict[str, int] = {}
        for rollout in range(spec.rollouts):
            began = time.perf_counter()
            returns = np.zeros(spec.lanes, np.float64)
            saturation = action_coordinates = 0
            before = support.optimizer_counts(counters)
            rng_before = agent.rng_stream_telemetry()
            sampler_rng_before = agent.sampler_rng_telemetry()
            for t in range(spec.horizon):
                actions, _, data = agent.step(
                    states,
                    observations,
                    env_steps,
                    dones,
                    deterministic=False,
                    return_step_data=True,
                    build_infos=False,
                )
                next_states, next_obs = [], []
                rewards = np.zeros(spec.lanes, np.float64)
                next_dones = np.zeros(spec.lanes, bool)
                for lane, env in enumerate(envs):
                    ns, no, reward, done, _, _ = physical_step(env, actions[lane])
                    counts["training_transitions"] += 1
                    counts["training_episodes"] += int(done)
                    next_states.append(ns)
                    next_obs.append(no)
                    rewards[lane], next_dones[lane] = reward, done
                if not np.all(next_dones == (t == spec.horizon - 1)):
                    raise ValueError("unexpected B07 training episode boundary")
                next_states, next_obs = np.stack(next_states), np.stack(next_obs)
                if rollout == 0:
                    update_digest(
                        first_digest,
                        states,
                        observations,
                        actions,
                        rewards,
                        data["team_skills"],
                        data["agent_skills"],
                        data["action_logprobs"],
                    )
                if t % spec.k == 0:
                    if not np.asarray(data["d2_team_decision"]).all():
                        raise ValueError("fixed k10 boundary was not a full native team decision")
                    team_hist += np.bincount(
                        np.asarray(data["team_skills"], dtype=np.int64), minlength=6
                    )
                    for lane, skill in enumerate(data["agent_skills"]):
                        label_hist[np.arange(spec.n_agents), skill] += 1
                        key = ",".join(
                            map(str, [int(data["team_skills"][lane]), *map(int, skill)])
                        )
                        joint_hist[key] = joint_hist.get(key, 0) + 1
                saturation += int((np.abs(actions) > 1).sum())
                action_coordinates += actions.size
                verified = store_verified_batch(
                    agent,
                    summary["storage_verification"],
                    states=states,
                    next_states=next_states.copy(),
                    observations=observations,
                    next_observations=next_obs.copy(),
                    actions=actions,
                    rewards=rewards,
                    dones=next_dones,
                    infos_batch=None,
                    rollout_step_idx=t,
                    step_data=data,
                )
                counts["stored_transitions"] += verified
                returns += rewards
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        no, info = env.reset()
                        next_obs[lane] = np.asarray(no, np.float32)
                        next_states[lane] = np.asarray(info["state"], np.float64)
                        agent.reset_env_state(lane)
                        env_steps[lane] = 0
                    else:
                        env_steps[lane] += 1
                states, observations, dones = next_states, next_obs, next_dones

            losses = agent.update(
                last_values=np.zeros((spec.lanes, spec.n_agents), np.float32),
                dones=dones.copy(),
                steps_in_buffer=spec.horizon,
                last_state=states.copy(),
                last_observations=observations.copy(),
            )
            counts["native_updates"] += 1
            coordinator_gradient_norm = math.sqrt(
                sum(
                    float(parameter.grad.detach().double().square().sum().item())
                    for parameter in agent.skill_coordinator.parameters()
                    if parameter.grad is not None
                )
            )
            entropy_objective = float(
                losses["coordinator_loss"]
                - losses["coordinator_policy_loss"]
                - config.value_loss_coef * losses["coordinator_value_loss"]
            )
            after = support.optimizer_counts(counters)
            optimizer_delta = {key: after[key] - before[key] for key in after}
            expected_delta = {
                "coordinator": 15 if arm in {"E", "M"} else 0,
                "discoverer_actor": 2250,
                "discoverer_critic": 2250,
                "team_discriminator": 15,
                "individual_discriminator": 60,
            }
            if not spec.small_model and optimizer_delta != expected_delta:
                raise ValueError(f"B07 per-rollout optimizer counts differ: {optimizer_delta}")

            # Terminal storage closes this fixed-horizon rollout's last D2
            # segments.  Read the authoritative canonical tables before
            # clear_buffers resets them.  In U, inherited rows_M*/optimizer
            # metrics remain zero because the coordinator update is skipped;
            # they do not mean collection or table storage was skipped.
            d2_tables = agent.rollout_buffer.get_d2_tables(spec.horizon)
            if d2_tables is None:
                raise RuntimeError("B07 native D2 tables were not retained")
            retained = {
                "rollout": rollout + 1,
                "canonical_count_source": "rollout_buffer.get_d2_tables",
                "decision_rows": int(np.asarray(d2_tables["decision"]).sum()),
                "team_valid_rows": int(np.asarray(d2_tables["team_valid"]).sum()),
                "agent_valid_rows": int(np.asarray(d2_tables["agent_valid"]).sum()),
                "metrics": jsonable(agent.get_d2_metrics()),
                "inherited_update_metric_scope": (
                    "rows_M and optimizer_steps describe coordinator update work; "
                    "canonical table counts above describe retained collection/storage"
                ),
            }
            if arm == "U":
                retained["uniform_factor_audit_after_update"] = agent.audit_uniform_d2_storage(
                    spec.horizon
                )
            summary["d2_retained_work"].append(retained)

            aux = agent.auxiliary_history[-1]
            expected_windows = spec.lanes * spec.horizon // spec.k
            expected_aux_steps = (expected_windows + 127) // 128
            if (
                aux["samples"] != expected_windows
                or aux["discarded_terminal_windows"] != 0
                or aux["head_optimizer_steps"]
                != {"G": expected_aux_steps, "P": expected_aux_steps}
                or aux["trunk_optimizer_steps"] != 0
            ):
                raise ValueError("B07 factual-head exposure differs from protocol")
            predictions = {
                "rollout": rollout + 1,
                **jsonable(aux.pop("raw_prediction_rows")),
            }
            prediction_bytes = (json.dumps(predictions, allow_nan=False) + "\n").encode()
            with (out / "auxiliary_predictions.jsonl").open("ab") as stream:
                stream.write(prediction_bytes)
            aux["raw_predictions"] = {
                "file": "auxiliary_predictions.jsonl",
                "line": rollout + 1,
                "sha256": hashlib.sha256(prediction_bytes).hexdigest(),
                "rows": aux["samples"],
                "timing": "after this rollout's auxiliary update",
            }
            if rollout == 0:
                summary["first_rollout_facts_sha256"] = first_digest.hexdigest()
            movement = b01.native._exposure_line(agent, theta0)
            row = {
                "rollout": rollout + 1,
                "training_transitions": counts["training_transitions"],
                "returns_U": returns,
                "training_J": spec.n_agents * returns / spec.horizon,
                "native_losses": losses,
                "coordinator_update_reading": {
                    "lambda_h": float(config.lambda_h),
                    "total_loss": float(losses["coordinator_loss"]),
                    "policy_loss": float(losses["coordinator_policy_loss"]),
                    "value_loss": float(losses["coordinator_value_loss"]),
                    "entropy_objective_reconstructed": entropy_objective,
                    "post_update_gradient_norm": coordinator_gradient_norm,
                    "reported_team_entropy": float(losses["team_skill_entropy"]),
                    "reported_individual_entropy": float(losses["agent_skill_entropy"]),
                    "context_distribution": "native D2 training-update minibatches",
                },
                "native_optimizer_calls": after,
                "optimizer_delta": optimizer_delta,
                "auxiliary": aux,
                "relative_initialization_displacement": movement,
                "auxiliary_head_relative_movement": {
                    "G": _module_relative_movement(agent.g_head, head0["G"]),
                    "P": _module_relative_movement(agent.p_head, head0["P"]),
                },
                "rng_streams_before": rng_before,
                "rng_streams_after": agent.rng_stream_telemetry(),
                "sampler_rng_streams_before": sampler_rng_before,
                "sampler_rng_streams_after": agent.sampler_rng_telemetry(),
                "default_rng_state_sha256_after": rng_state_digest(),
                "raw_saturation_fraction": saturation / action_coordinates,
                "wall_seconds": time.perf_counter() - began,
                "d2_retained_work": retained,
            }
            summary["training_rows"].append(jsonable(row))
            summary["native_optimizer_calls"] = after
            summary["actual_team_label_occupancy"] = team_hist
            summary["actual_individual_label_occupancy"] = label_hist
            summary["actual_joint_occupancy"] = joint_hist
            summary["training_occupancy"] = _write_training_occupancy(
                out, rollout + 1, team_hist, label_hist, joint_hist
            )
            with (out / "training.jsonl").open("a") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            agent.clear_buffers()
            write_json(out / "summary.json", _compact_summary(summary, out))


        summary["checkpoints"]["final"] = save_checkpoint(
            agent, out / "final.pt", summary["learner_config"], spec.rollouts
        )
        summary["final_native_digest"] = native_digest(agent)
        summary["final_frozen_digest"] = frozen_digest(agent)
        final_panels = (
            [item for i in range(4) for item in (f"S{i}", f"R{i}")]
            if arm in {"E", "M"}
            else [f"R{i}" for i in range(4)]
        )
        captures = _evaluate_schedule(
            agent, spec, arm, "final", final_panels, out, summary, counts
        )
        if arm == "M":
            summary["M_final_S_reference"] = save_reference(
                out, captures, summary, spec
            )
        if arm == "E":
            assert reference is not None
            summary["common_context_scoring"] = score_reference(
                agent, reference, out, counts
            )
        summary["aggregates"] = aggregate_arm(summary["panels"], arm, spec)
        summary["auxiliary_predictions"] = {
            "file": "auxiliary_predictions.jsonl",
            "sha256": _sha256_file(out / "auxiliary_predictions.jsonl"),
            "batches": spec.rollouts,
        }
        summary["training_log"] = {
            "file": "training.jsonl",
            "sha256": _sha256_file(out / "training.jsonl"),
            "rows": spec.rollouts,
        }
        summary["final_private_rng_streams"] = agent.rng_stream_telemetry()
        summary["final_sampler_rng_streams"] = agent.sampler_rng_telemetry()
        summary["label_flow_checks"] = copy.deepcopy(agent.label_flow_checks)
        if arm == "U":
            summary["uniform_factor_audits"] = copy.deepcopy(agent.uniform_factor_audits)
        _validate_completed_contract(summary, spec)
        summary["status"] = "complete"
    except BaseException as exc:
        summary["status"] = "failed"
        summary["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "process_wall_seconds": time.perf_counter() - started,
            "user_cpu_seconds": usage.ru_utime - cpu_started.ru_utime,
            "system_cpu_seconds": usage.ru_stime - cpu_started.ru_stime,
            "peak_process_rss_kib": usage.ru_maxrss,
            "scope": "runner body; process RSS lifetime peak; shared-node occupancy unmeasured",
            "resources_unmeasured": ["peak_scratch_bytes"],
        }
        if torch.device(device).type == "cuda" and torch.cuda.is_initialized():
            summary["resources"]["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated(
                torch.device(device)
            )
            summary["resources"]["peak_cuda_reserved_bytes"] = torch.cuda.max_memory_reserved(
                torch.device(device)
            )
        if agent is not None:
            summary["auxiliary_history"] = jsonable(agent.auxiliary_history)
            summary["label_flow_checks"] = copy.deepcopy(agent.label_flow_checks)
            summary["final_private_rng_streams"] = agent.rng_stream_telemetry()
            summary["final_sampler_rng_streams"] = agent.sampler_rng_telemetry()
        counts["stored_transitions"] = int(summary["storage_verification"]["verified_rows"])
        if counters is not None:
            summary["native_optimizer_calls"] = support.optimizer_counts(counters)
        summary["resources"]["durable_output_bytes_excluding_summary"] = sum(
            path.stat().st_size
            for path in out.rglob("*")
            if path.is_file() and path != out / "summary.json"
        )
        summary["resources"]["scratch_telemetry_scope"] = (
            "final candidate output files excluding summary.json; peak scratch usage unmeasured"
        )
        write_json(out / "summary.json", _compact_summary(summary, out))
        for env in envs:
            env.close()
    return summary


__all__ = [
    "ARMS",
    "DEFAULT_SPEC",
    "EXPECTED_NATIVE_OPTIMIZER_CALLS",
    "FIXED_SEED",
    "NON_LABEL_SEED",
    "R_SEEDS",
    "REFERENCE_SCHEMA",
    "S_SEEDS",
    "Spec",
    "TrainingLawAgent",
    "aggregate_arm",
    "aggregate_batch",
    "evaluate_panel",
    "make_config",
    "run_fit",
    "save_checkpoint",
    "score_reference",
    "validate_reference",
]

