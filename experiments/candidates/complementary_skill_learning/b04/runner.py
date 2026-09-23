"""Fixed B04 M/U training-law comparison using the audited B03 loop."""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import resource
import sys
import time
import traceback
from typing import Any

import numpy as np
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b03 import runner as b03
from scripts import run_fsd_uav_individual_renewal_b01 as support

from .learning import TrainingLawAgent, _capture_process_rng_state


DIRECTION = "complementary_skill_learning"
OBJECT = "complementary_skill_b04"
EXPECTED_UNIFORM_LABEL_STREAM_SHA256 = b03.EXPECTED_UNIFORM_LABEL_STREAM_SHA256
EXPECTED_NATIVE_OPTIMIZER_CALLS = {
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
    init_seed: int = 260923931
    head_seed: int = 260923932
    train_rng_seed: int = 260923933
    aux_seed: int = 260923934
    low_action_seed: int = 260923935
    high_collection_seed: int = 260923936
    high_update_seed: int = 260923937
    eval_rng_seed: int = 260923905
    train_world_base: int = 2100000
    eval_world_base: int = 1700200
    threads: int = 4
    small_model: bool = False  # technical checks only; the CLI cannot enable it


DEFAULT_SPEC = Spec()
jsonable = b01.jsonable
write_json = b01.write_json
seed_rng = b01.seed_rng
update_digest = b01.update_digest
native_digest = b01.native_digest
frozen_digest = b01.frozen_digest
make_envs = b01.make_envs
physical_step = b01.physical_step
rng_state_digest = b03.rng_state_digest
store_verified_batch = b03.store_verified_batch


def make_config(spec: Spec, envs: list[Any], arm: str):
    if arm not in {"M", "U"}:
        raise ValueError(arm)
    config = b01.make_config(spec, envs)
    config.disable_high_level_training = arm == "U"
    return config


def _uniform_stream_digest(spec: Spec) -> str:
    rng = np.random.Generator(np.random.PCG64(spec.eval_rng_seed + spec.eval_world_base))
    digest = hashlib.sha256()
    for t in range(0, spec.horizon, spec.k):
        team = rng.integers(0, 6, size=spec.eval_lanes)
        individual = rng.integers(0, 6, size=(spec.eval_lanes, spec.n_agents))
        update_digest(digest, np.asarray([t], np.int64), team, individual)
    return digest.hexdigest()


def evaluate_panel(agent: TrainingLawAgent, spec: Spec, rule: str, *, counter=None):
    panel = b03.evaluate_panel(agent, spec, rule, counter=counter)
    if rule == "uniform":
        panel["frozen_b01_uniform_stream_sha256"] = EXPECTED_UNIFORM_LABEL_STREAM_SHA256
        panel["frozen_b01_uniform_stream_match"] = (
            panel["selected_label_stream_sha256"]
            == EXPECTED_UNIFORM_LABEL_STREAM_SHA256
        )
        if spec == DEFAULT_SPEC and not panel["frozen_b01_uniform_stream_match"]:
            raise ValueError("B04 uniform evaluation stream differs from frozen B01")
    return panel


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


def _validate_completed_contract(summary: dict[str, Any], spec: Spec) -> None:
    arm = summary["arm"]
    panel_multiplier = 4 if arm == "M" else 2
    expected_counts = {
        "started_fits": 1,
        "model_constructions": 1,
        "training_transitions": spec.lanes * spec.horizon * spec.rollouts,
        "stored_transitions": spec.lanes * spec.horizon * spec.rollouts,
        "training_episodes": spec.lanes * spec.rollouts,
        "native_updates": spec.rollouts,
        "evaluation_transitions": panel_multiplier * spec.eval_lanes * spec.horizon,
        "evaluation_episodes": panel_multiplier * spec.eval_lanes,
    }
    if summary["counts"] != expected_counts:
        raise ValueError(f"B04 transition/update counts differ: {summary['counts']}")
    expected_panels = (
        {"initial_own", "initial_uniform", "final_own", "final_uniform"}
        if arm == "M"
        else {"initial_uniform", "final_uniform"}
    )
    if set(summary["panels"]) != expected_panels:
        raise ValueError("B04 arm has the wrong evaluation panel set")
    panels = summary["panels"]
    if len({panel["physical_initial_state_sha256"] for panel in panels.values()}) != 1:
        raise ValueError("B04 evaluation panels did not repeat one physical initial state")
    if (
        panels["initial_uniform"]["selected_label_stream_sha256"]
        != panels["final_uniform"]["selected_label_stream_sha256"]
    ):
        raise ValueError("B04 uniform panels did not repeat one label stream")
    if any(panel["optimizer_calls"] or panel["normalizer_updates"] for panel in panels.values()):
        raise ValueError("B04 evaluation changed optimizer or normalizer state")
    storage = summary["storage_verification"]
    if storage != {
        "batch_calls": spec.horizon * spec.rollouts,
        "expected_rows": expected_counts["stored_transitions"],
        "verified_rows": expected_counts["stored_transitions"],
        "failures": 0,
        "last_failure": None,
    }:
        raise ValueError("B04 did not verify every native storage row")
    expected_label_batches = spec.horizon * spec.rollouts
    if summary["label_flow_checks"] != {
        "action_batches": expected_label_batches,
        "reward_batches": expected_label_batches,
        "factual_batches": expected_label_batches,
        "storage_batches": expected_label_batches,
        "failures": 0,
    }:
        raise ValueError("B04 did not verify each low/reward/factual/storage label path")

    if not spec.small_model:
        if summary["native_optimizer_calls"] != EXPECTED_NATIVE_OPTIMIZER_CALLS[arm]:
            raise ValueError("B04 production native optimizer counts differ")
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
            raise ValueError("B04 auxiliary optimizer counts differ")
        summary["auxiliary_optimizer_calls"] = auxiliary

    final_movement = summary["training_rows"][-1]["relative_initialization_displacement"]
    trained = (
        "discoverer_actor",
        "discoverer_critic",
        "team_discriminator",
        "individual_discriminator",
    )
    if any(not (final_movement[name] > 0.0) for name in trained):
        raise ValueError("a required B04 native component did not move")
    if arm == "U" and final_movement["coordinator"] != 0.0:
        raise ValueError("U coordinator parameters changed")
    if arm == "M" and not (final_movement["coordinator"] > 0.0):
        raise ValueError("M coordinator parameters did not move")
    if any(
        not (summary["training_rows"][-1]["auxiliary_head_relative_movement"][name] > 0.0)
        for name in ("G", "P")
    ):
        raise ValueError("a required B04 factual head did not move")


def run_fit(
    arm: str,
    out: Path | str,
    launch_sha: str,
    *,
    spec: Spec = DEFAULT_SPEC,
    device: str | torch.device = "cuda",
    admission: dict[str, Any] | None = None,
):
    arm = str(arm).upper()
    if arm not in {"M", "U"}:
        raise ValueError(arm)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists():
        raise ValueError("a fit never overwrites an existing summary")
    torch.set_num_threads(spec.threads)
    logging.getLogger().setLevel(logging.WARNING)
    started = time.perf_counter()
    cpu_started = resource.getrusage(resource.RUSAGE_SELF)
    counts = dict.fromkeys(
        (
            "started_fits",
            "model_constructions",
            "training_transitions",
            "stored_transitions",
            "training_episodes",
            "native_updates",
            "evaluation_transitions",
            "evaluation_episodes",
        ),
        0,
    )
    summary: dict[str, Any] = {
        "object_id": OBJECT,
        "direction": DIRECTION,
        "arm": arm,
        "training_law": (
            "learned_team_and_mu=.9*pi+.1/6_individual" if arm == "M"
            else "independent_uniform_team_and_individual_1_over_6"
        ),
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
        },
    )

    envs: list[Any] = []
    agent = counters = None
    try:
        if torch.device(device).type == "cuda":
            torch.cuda.reset_peak_memory_stats(torch.device(device))
            summary["runtime"]["cuda_device"] = torch.cuda.get_device_name(torch.device(device))
        envs = make_envs(spec, spec.lanes, spec.train_world_base)
        config = make_config(spec, envs, arm)
        summary["learner_config"] = effective_config(config)
        seed_rng(spec.init_seed)
        agent = TrainingLawAgent(
            config=config,
            arm=arm,
            head_seed=spec.head_seed,
            aux_seed=spec.aux_seed,
            low_action_seed=spec.low_action_seed,
            high_collection_seed=spec.high_collection_seed,
            high_update_seed=spec.high_update_seed,
            log_dir=str(out / "learner_logs"),
            device=torch.device(device),
        )
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

        if arm == "M":
            summary["panels"]["initial_own"] = evaluate_panel(
                agent, spec, "own", counter=counts
            )
        summary["panels"]["initial_uniform"] = evaluate_panel(
            agent, spec, "uniform", counter=counts
        )
        write_json(out / "summary.json", summary)

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
                    raise ValueError("unexpected B04 training episode boundary")
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
            after = support.optimizer_counts(counters)
            optimizer_delta = {key: after[key] - before[key] for key in after}
            expected_delta = {
                "coordinator": 15 if arm == "M" else 0,
                "discoverer_actor": 2250,
                "discoverer_critic": 2250,
                "team_discriminator": 15,
                "individual_discriminator": 60,
            }
            if not spec.small_model and optimizer_delta != expected_delta:
                raise ValueError(f"B04 per-rollout optimizer counts differ: {optimizer_delta}")

            # Terminal storage closes this fixed-horizon rollout's last D2
            # segments.  Read the authoritative canonical tables before
            # clear_buffers resets them.  In U, inherited rows_M*/optimizer
            # metrics remain zero because the coordinator update is skipped;
            # they do not mean collection or table storage was skipped.
            d2_tables = agent.rollout_buffer.get_d2_tables(spec.horizon)
            if d2_tables is None:
                raise RuntimeError("B04 native D2 tables were not retained")
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
                raise ValueError("B04 factual-head exposure differs from protocol")
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
            with (out / "training.jsonl").open("a") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            agent.clear_buffers()
            write_json(out / "summary.json", summary)

        summary["checkpoints"]["final"] = save_checkpoint(
            agent, out / "final.pt", summary["learner_config"], spec.rollouts
        )
        if arm == "M":
            summary["panels"]["final_own"] = evaluate_panel(
                agent, spec, "own", counter=counts
            )
            write_json(out / "summary.json", summary)
        summary["panels"]["final_uniform"] = evaluate_panel(
            agent, spec, "uniform", counter=counts
        )
        summary["auxiliary_predictions"] = {
            "file": "auxiliary_predictions.jsonl",
            "sha256": b01.native._sha256_file(out / "auxiliary_predictions.jsonl"),
            "batches": spec.rollouts,
        }
        summary["training_log"] = {
            "file": "training.jsonl",
            "sha256": b01.native._sha256_file(out / "training.jsonl"),
            "rows": spec.rollouts,
        }
        summary["final_native_digest"] = native_digest(agent)
        summary["final_frozen_digest"] = frozen_digest(agent)
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
        write_json(out / "summary.json", summary)
        for env in envs:
            env.close()
    return summary


__all__ = [
    "DEFAULT_SPEC",
    "EXPECTED_NATIVE_OPTIMIZER_CALLS",
    "EXPECTED_UNIFORM_LABEL_STREAM_SHA256",
    "Spec",
    "TrainingLawAgent",
    "evaluate_panel",
    "make_config",
    "run_fit",
    "save_checkpoint",
]
