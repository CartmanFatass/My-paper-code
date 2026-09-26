"""Fixed two-block D/S/G successor to the frozen service-auxiliary experiment."""

from __future__ import annotations

import json
import resource
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from hmasd.agent import HMASDAgent
from ..b01.native import (
    NativeSpec, METRIC_FIELDS, _bootstrap_values, _json_default, _module_parameters,
    _write_progress, active_config, initialization_fingerprint, make_config, make_env,
    optimizer_steps, parameter_displacement, seed_everything, sha256_file,
)
from .auxiliary import B03AuxiliaryReplay
from .facts import array_digest, copy_initial_facts, evaluate, finish_initial_scores, replay_facts

OBJECT_ID = "UAV-SERVICE-AUXILIARY-B03"
TRAINING_SEEDS = (912211, 912347)


@dataclass(frozen=True)
class B03Spec(NativeSpec):
    seed: int = 912211
    fact_seeds: tuple[int, ...] = (932201, 932202)
    endpoint_fact_seeds: tuple[int, ...] = tuple(range(933201, 933205))
    final_seeds: tuple[int, ...] = tuple(range(936001, 936033))
    eval_rollouts: tuple[int, ...] = (0, 10, 20, 30)
    generic_head_seed_offset: int = 300000


def production_spec(seed: int) -> B03Spec:
    if seed not in TRAINING_SEEDS:
        raise ValueError("unplanned training seed")
    offset = 0 if seed == TRAINING_SEEDS[0] else 10
    return B03Spec(seed=seed, fact_seeds=(932201 + offset, 932202 + offset),
                   endpoint_fact_seeds=tuple(range(933201 + offset, 933205 + offset)))


def assert_finite(value: Any) -> None:
    if isinstance(value, dict):
        for child in value.values():
            assert_finite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_finite(child)
    elif isinstance(value, (float, np.floating)) and not np.isfinite(value):
        raise FloatingPointError("non-finite reported value")


def _load_reference(path: Path, digest: str) -> dict[str, Any]:
    if sha256_file(path) != digest:
        raise ValueError("calibration artifact digest mismatch")
    payload = json.loads(path.read_text())
    if payload.get("schema") != "uav_service_auxiliary_b03_calibration_v1":
        raise ValueError("calibration artifact schema mismatch")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, default=_json_default, allow_nan=False) + "\n")


def run_native(*, arm: str, out: Path, launch_sha: str, device_name: str = "cuda",
               threads: int = 4, facts: Path | None = None, facts_sha256: str | None = None,
               calibration: Path | None = None, calibration_sha256: str | None = None,
               spec: B03Spec | None = None) -> dict[str, Any]:
    spec = spec or B03Spec(threads=threads)
    if arm not in {"D", "S", "G"}:
        raise ValueError("arm must be D, S or G")
    if spec.window < 2:
        raise ValueError("B03 requires W>=2 so its W-valid rows have a next observation")
    supplied = (facts, facts_sha256, calibration, calibration_sha256)
    if arm == "D" and any(value is not None for value in supplied):
        raise ValueError("D creates initial facts and calibration")
    if arm != "D" and any(value is None for value in supplied):
        raise ValueError("S/G require exact D facts and calibration artifacts")
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    torch.set_num_threads(int(threads))
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json", "progress.jsonl")):
        raise FileExistsError(f"output already contains scientific records: {out}")
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    cpu_started = resource.getrusage(resource.RUSAGE_SELF)
    timings = {name: 0.0 for name in ("preparation", "collection", "native_update", "auxiliary",
                                     "evaluation", "facts", "replay", "checkpoint")}
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "status": "INCOMPLETE", "failure": None,
        "arm": arm, "seed": spec.seed, "launch_sha": launch_sha,
        "device": str(device), "torch_threads": torch.get_num_threads(),
        "counts": {name: 0 for name in ("transitions", "rollouts", "episodes", "evaluations",
                                      "evaluation_transitions", "fact_episodes", "fact_transitions",
                                      "reused_fact_episodes", "reused_fact_transitions", "replay_agent_rows")},
        "stage_wall_seconds": timings, "evaluations": {}, "updates": [],
        "training_rollouts": [], "rss_curve": [],
    }
    envs = []
    _write_json(out / "summary.json", summary)
    try:
        stage_start = time.perf_counter()
        seed_everything(spec.seed, device)
        config = make_config(spec)
        _write_json(out / "config.json", {
            "spec": asdict(spec),
            # Some inactive native thresholds use infinity as an unbounded sentinel.
            "active": json.loads(json.dumps(active_config(config)), parse_constant=str), "arm": arm,
            "references": {"facts_sha256": facts_sha256, "calibration_sha256": calibration_sha256},
            "generic_target": "next legal actor observation, fixed first-rollout centered RMS coordinates",
            "generic_loss": "mean squared error over W-valid agent rows and all coordinates; coefficient 1",
        })
        summary["config_sha256"] = sha256_file(out / "config.json")
        agent = HMASDAgent(config, log_dir=str(out / "logs"), device=device)
        initial = _module_parameters(agent)
        initial_sha256 = initialization_fingerprint(agent)
        auxiliary = B03AuxiliaryReplay(
            agent.skill_discoverer.actor, arm,
            initialization_seed=spec.seed + spec.head_seed_offset,
            generic_initialization_seed=spec.seed + spec.generic_head_seed_offset,
            observation_dim=config.obs_dim, action_dim=config.action_dim, window=spec.window,
        )
        reference = None
        if arm != "D":
            reference = _load_reference(Path(calibration), str(calibration_sha256))
            if reference["block_seed"] != spec.seed or reference["initialization_sha256"] != initial_sha256:
                raise ValueError("calibration belongs to a different block/initialization")
            auxiliary.load_calibration(reference["calibration"])
        summary["initialization_sha256"] = initial_sha256
        timings["preparation"] += time.perf_counter() - stage_start
        facts_local = out / "facts.npz"
        stage_start = time.perf_counter()
        if arm == "D":
            panel = evaluate(
                agent, config, spec.fact_seeds, device, policy_seed=spec.seed,
                log_dir=out / "initial_fact_evaluator", fact_path=facts_local,
                fact_metadata={"kind": "initial", "block_seed": spec.seed, "source_arm": arm},
            )
            digest = panel["facts_sha256"]
            summary["initial_fact_panel"] = panel
            summary["counts"]["fact_episodes"] += len(panel["worlds"])
            summary["counts"]["fact_transitions"] += panel["actual_transitions"]
        else:
            digest = copy_initial_facts(Path(facts), str(facts_sha256), facts_local,
                                        seeds=spec.fact_seeds, policy_sha256=initial_sha256, block_seed=spec.seed)
            with np.load(facts_local, allow_pickle=False) as saved:
                keys = [key for key in saved.files if key.endswith("_observations")]
                summary["counts"]["reused_fact_episodes"] = len(keys)
                summary["counts"]["reused_fact_transitions"] = sum(len(saved[key]) for key in keys)
        timings["facts"] += time.perf_counter() - stage_start
        summary["facts_sha256"] = digest
        _write_progress(out, summary, {"event": "facts_ready", "facts_sha256": digest})

        def measure_panel(rollout: int):
            stage_start = time.perf_counter()
            panel = evaluate(agent, config, spec.eval_seeds, device, policy_seed=spec.seed,
                             log_dir=out / "native_evaluator")
            timings["evaluation"] += time.perf_counter() - stage_start
            summary["counts"]["evaluations"] += len(panel["worlds"])
            summary["counts"]["evaluation_transitions"] += panel["actual_transitions"]
            stage_start = time.perf_counter()
            diagnostic = replay_facts(auxiliary, agent, facts_local,
                                      save_arrays=out / f"initial_fact_replay_{rollout}.npz")
            timings["replay"] += time.perf_counter() - stage_start
            summary["counts"]["replay_agent_rows"] += diagnostic["valid_agent_rows"]
            summary["evaluations"][str(rollout)] = {"native": panel, "initial_common_fact": diagnostic}
            _write_progress(out, summary, {"event": "development_evaluation", "rollout": rollout})

        measure_panel(0)
        envs = [make_env(config, spec.seed + lane) for lane in range(spec.lanes)]
        observations = []
        states = []
        for lane, env in enumerate(envs):
            obs, info = env.reset(seed=spec.seed + lane)
            observations.append(obs)
            states.append(info["state"])
        observations_arr = np.asarray(observations, dtype=np.float32)
        states_arr = np.asarray(states, dtype=np.float32)
        dones = np.ones(spec.lanes, dtype=bool)
        env_steps = np.zeros(spec.lanes, dtype=np.int64)
        straddling_boundaries = 0
        update_rows = summary["updates"]
        training_rollouts = summary["training_rollouts"]
        rss_curve = summary["rss_curve"]
        for rollout in range(1, spec.rollouts + 1):
            collection_started = time.perf_counter()
            qos = np.empty((spec.rollout_length, spec.lanes), dtype=np.float32)
            rollout_reward_sum = np.zeros(spec.lanes, dtype=np.float64)
            rollout_metric_sums = {
                field: np.zeros(spec.lanes, dtype=np.float64) for field in METRIC_FIELDS
            }
            rollout_terminal_types = {"terminated": 0, "truncated": 0}
            for step in range(spec.rollout_length):
                current_obs = observations_arr.copy()
                current_states = states_arr.copy()
                actions, _, step_data = agent.step(
                    current_states, current_obs, env_steps, dones, deterministic=False,
                    return_step_data=True, build_infos=False,
                )
                next_obs_rows = []
                next_state_rows = []
                rewards = np.empty(spec.lanes, dtype=np.float32)
                next_dones = np.empty(spec.lanes, dtype=bool)
                infos = []
                terminal_observations = []
                terminal_states = []
                for lane, env in enumerate(envs):
                    next_obs, reward, terminated, truncated, info = env.step(actions[lane])
                    terminal_obs = np.asarray(next_obs, dtype=np.float32)
                    terminal_state = np.asarray(info["next_state"], dtype=np.float32)
                    done = bool(terminated or truncated)
                    rewards[lane] = float(reward)
                    if not np.isfinite(rewards[lane]):
                        raise FloatingPointError("non-finite native training reward")
                    next_dones[lane] = done
                    reward_info = info.get("reward_info", {})
                    missing = [field for field in METRIC_FIELDS if field not in reward_info]
                    if missing:
                        raise KeyError(f"Scenario 7 reward_info is missing required metrics: {missing}")
                    qos[step, lane] = float(reward_info["qos_satisfaction_ratio"])
                    rollout_reward_sum[lane] += rewards[lane]
                    for field in METRIC_FIELDS:
                        value = float(reward_info[field])
                        if not np.isfinite(value):
                            raise FloatingPointError(f"non-finite Scenario 7 metric {field}")
                        rollout_metric_sums[field][lane] += value
                    if terminated:
                        rollout_terminal_types["terminated"] += 1
                    if truncated:
                        rollout_terminal_types["truncated"] += 1
                    infos.append(info)
                    terminal_observations.append(terminal_obs)
                    terminal_states.append(terminal_state)
                terminal_observations_arr = np.asarray(terminal_observations, dtype=np.float32)
                terminal_states_arr = np.asarray(terminal_states, dtype=np.float32)
                agent.store_transition_batch(
                    current_states, terminal_states_arr, current_obs,
                    terminal_observations_arr, actions, rewards, next_dones,
                    infos_batch=infos, rollout_step_idx=step, step_data=step_data,
                )
                # Reset only after the terminal transition and its terminal next input are stored.
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        summary["counts"]["episodes"] += 1
                        agent.reset_env_state(lane)
                        next_obs, reset_info = env.reset(seed=None)
                        next_obs_rows.append(np.asarray(next_obs, dtype=np.float32))
                        next_state_rows.append(np.asarray(reset_info["state"], dtype=np.float32))
                        env_steps[lane] = 0
                    else:
                        next_obs_rows.append(terminal_observations_arr[lane])
                        next_state_rows.append(terminal_states_arr[lane])
                        env_steps[lane] += 1
                observations_arr = np.asarray(next_obs_rows, dtype=np.float32)
                states_arr = np.asarray(next_state_rows, dtype=np.float32)
                dones = next_dones
                summary["counts"]["transitions"] += spec.lanes
                if (step + 1) % 100 == 0 or step + 1 == spec.rollout_length:
                    _write_progress(out, summary, {
                        "event": "collection", "rollout": rollout, "step": step + 1,
                        "transitions": summary["counts"]["transitions"],
                        "wall_seconds": time.time() - started,
                    })
            timings["collection"] += time.perf_counter() - collection_started
            auxiliary_started = time.perf_counter()
            rollout_data = agent.rollout_buffer._get_full_rollout_data()
            if rollout_data is None:
                raise RuntimeError("native rollout buffer is empty")
            aux_obs = np.asarray(rollout_data["obs"], dtype=np.float32).copy()
            aux_skills = np.asarray(rollout_data["agent_skills"], dtype=np.int64).copy()
            aux_actions = np.asarray(rollout_data["actions"], dtype=np.float32).copy()
            aux_dones = np.asarray(rollout_data["dones"], dtype=bool).any(axis=-1)
            aux_hidden = np.asarray(rollout_data["gru_hidden_states"][0], dtype=np.float32).copy()
            normalized = np.asarray(agent._normalize_observations(aux_obs, update=False), dtype=np.float32)
            if rollout == 1:
                scale = auxiliary.calibrate(aux_obs, aux_dones, qos, normalized_observations=normalized)
                collection_sha = array_digest(observations=aux_obs, normalized=normalized,
                                              skills=aux_skills, dones=aux_dones, hidden=aux_hidden,
                                              actions=aux_actions, qos=qos)
                if reference is not None and collection_sha != reference["collection_sha256"]:
                    raise RuntimeError("first rollout differs from D before any auxiliary update")
                if reference is not None and scale != reference["calibration"]:
                    raise RuntimeError("first rollout coordinate transform differs from D")
            timings["auxiliary"] += time.perf_counter() - auxiliary_started
            native_started = time.perf_counter()
            before_native = _module_parameters(agent)
            last_values = _bootstrap_values(agent, states_arr, dones)
            native_update = agent.update(
                last_values=last_values, dones=dones, steps_in_buffer=spec.rollout_length,
                last_state=states_arr, last_observations=observations_arr,
            )
            assert_finite(native_update)
            native_movement = parameter_displacement(before_native, agent)
            timings["native_update"] += time.perf_counter() - native_started
            auxiliary_started = time.perf_counter()
            if rollout == 1:
                first_native_sha = initialization_fingerprint(agent)
                if reference is not None and first_native_sha != reference["first_native_update_sha256"]:
                    raise RuntimeError("first native update differs from D before auxiliary update")
                payload = {
                    "schema": "uav_service_auxiliary_b03_calibration_v1", "block_seed": spec.seed,
                    "initialization_sha256": initial_sha256, "collection_sha256": collection_sha,
                    "first_native_update_sha256": first_native_sha,
                    "first_native_optimizer_steps": optimizer_steps(agent), "calibration": scale,
                }
                if reference is not None and payload != reference:
                    raise RuntimeError("first update/calibration provenance differs from D")
                _write_json(out / "calibration.json", payload)
                summary["calibration_sha256"] = sha256_file(out / "calibration.json")
                summary["first_rollout_checks"] = {key: value for key, value in payload.items() if key != "calibration"}
                finish_initial_scores(summary["evaluations"]["0"]["initial_common_fact"],
                                      out / "initial_fact_replay_0.npz", scale, spec.window)
            auxiliary_update = auxiliary.update(
                agent.skill_discoverer.actor, aux_obs, aux_skills, aux_dones, qos,
                actions=aux_actions, initial_hidden=aux_hidden, normalized_observations=normalized,
            )
            aux_row = dict(auxiliary_update)
            assert_finite(aux_row)
            timings["auxiliary"] += time.perf_counter() - auxiliary_started
            update_rows.append({"rollout": rollout, "native": native_update,
                                "native_parameter_displacement_l2": native_movement, "auxiliary": aux_row})
            agent.clear_buffers()
            if rollout < spec.rollouts:
                straddling_boundaries += int(np.count_nonzero(~dones))
            summary["counts"]["rollouts"] = rollout
            training_rollouts.append({
                "rollout": rollout,
                "raw_native_J_by_lane": rollout_reward_sum.tolist(),
                "metric_sums_by_lane": {
                    field: values.tolist() for field, values in rollout_metric_sums.items()
                },
                "terminal_types": rollout_terminal_types,
            })
            rss_curve.append({"rollout": rollout, "rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss), "wall_seconds": time.time() - started})
            if rollout in spec.eval_rollouts or rollout == spec.rollouts:
                measure_panel(rollout)
            _write_progress(out, summary, {
                "event": "rollout_complete", "rollout": rollout,
                "transitions": summary["counts"]["transitions"],
                "wall_seconds": time.time() - started,
            })
            print(f"rollout={rollout}/{spec.rollouts} transitions={summary['counts']['transitions']}", flush=True)
        if summary["counts"]["transitions"] != spec.transitions:
            raise RuntimeError("native transition count mismatch")
        steps = optimizer_steps(agent)
        displacement = parameter_displacement(initial, agent)
        if any(value <= 0 for value in steps.values()) or any(value <= 0 for value in displacement.values()):
            raise RuntimeError("one or more native learners did not update/move")
        stage_start = time.perf_counter()
        final_panel = evaluate(agent, config, spec.final_seeds, device, policy_seed=spec.seed,
                               log_dir=out / "final_evaluator")
        summary["final_evaluation"] = final_panel
        summary["counts"]["evaluations"] += len(final_panel["worlds"])
        summary["counts"]["evaluation_transitions"] += final_panel["actual_transitions"]
        timings["evaluation"] += time.perf_counter() - stage_start
        stage_start = time.perf_counter()
        endpoint_panel = evaluate(
            agent, config, spec.endpoint_fact_seeds, device, policy_seed=spec.seed,
            log_dir=out / "endpoint_fact_evaluator", fact_path=out / "endpoint_facts.npz",
            fact_metadata={"kind": "endpoint", "block_seed": spec.seed, "source_arm": arm,
                           "rollout": spec.rollouts, "launch_sha": launch_sha},
        )
        summary["endpoint_fact_panel"] = endpoint_panel
        summary["endpoint_facts_sha256"] = endpoint_panel["facts_sha256"]
        summary["counts"]["fact_episodes"] += len(endpoint_panel["worlds"])
        summary["counts"]["fact_transitions"] += endpoint_panel["actual_transitions"]
        timings["facts"] += time.perf_counter() - stage_start
        stage_start = time.perf_counter()
        checkpoint_dir = out / "checkpoint_final"
        checkpoint_dir.mkdir()
        agent.save_model(checkpoint_dir / "agent.pt")
        torch.save(auxiliary.checkpoint_state(), checkpoint_dir / "auxiliary.pt")
        timings["checkpoint"] += time.perf_counter() - stage_start
        summary.update({
            "status": "COMPLETE", "optimizer_steps": steps,
            "initialization_displacement_l2": displacement,
            "straddling_rollout_boundaries": straddling_boundaries,
            "checkpoint_sha256": {name: sha256_file(checkpoint_dir / name) for name in ("agent.pt", "auxiliary.pt")},
            "final_policy_sha256": initialization_fingerprint(agent),
        })
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        for env in envs:
            try:
                env.close()
            except Exception:
                pass
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary.update({"wall_seconds": time.time() - started,
                        "cpu_user_seconds": usage.ru_utime - cpu_started.ru_utime,
                        "cpu_system_seconds": usage.ru_stime - cpu_started.ru_stime,
                        "peak_rss_kib": int(usage.ru_maxrss), "rss_scope": "runner process high-water mark"})
        _write_json(out / "summary.json", summary)
