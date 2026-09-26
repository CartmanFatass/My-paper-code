"""Fixed B02 partner-conditioned native training and paired evaluation."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import resource
import time
from typing import Any

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.bounded_confirmation_b15 import runner as b15
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.local_ordinary_b16 import runner as b16
from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20 import runner as b20
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS, capture_parameters, digest_agent, finite, jsonable,
    model_modules, native_components, optimizer_counts, parameter_motion,
    preserve_rng, seed_rng, write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11
from experiments.candidates.controller_composition.b01 import runner as b01
from experiments.candidates.controller_composition.b01.bindings import SOURCE, SOURCE_COMMIT
from experiments.candidates.controller_composition.b02.bindings import (
    ARMS, ASSIGNMENT_SEED, BOOTSTRAP_DRAWS, BOOTSTRAP_SEED, EVAL_CELLS,
    EVAL_LANES, EVAL_WORLD_BASE, EPOCHS, HORIZON, OBJECT, ROLLOUTS,
    RUNTIME_SEED, SEED, TAG, TRAIN_LANES, TRAIN_WORLD_BASE,
)
from experiments.candidates.controller_composition.b02.reducer import reduce_panel
from experiments.candidates.controller_composition.b02.update_path import learner_buffer, store_learner_step, update_learner

N = 6
SPEC = replace(DEFAULT_SPEC, train_n=N, eval_lanes=EVAL_LANES, horizon=HORIZON,
               train_lanes=TRAIN_LANES, rollouts=ROLLOUTS, ppo_epochs=EPOCHS)


def _artifact(path: Path, out: Path) -> dict:
    return {"path": path.relative_to(out).as_posix(), "sha256": b01.sha256(path),
            "bytes": path.stat().st_size}


def _compact_update_audit(audit: dict, path: Path, out: Path) -> dict:
    """Keep exact sampler exposure in raw and bounded aggregates in compact records."""
    sizes = np.asarray(audit["batch_sizes"], dtype=np.int32)
    lengths = np.asarray(audit["chunk_lengths"], dtype=np.int32)
    if (sizes.shape != lengths.shape or sizes.ndim != 1 or
        sizes.size != audit["minibatches"] or not sizes.size or
        int(sizes.sum()) != audit["sampled_sequences"] or
        np.any(sizes <= 0) or np.any(lengths <= 0)):
        raise ValueError("B02 sampler audit is incomplete")
    np.savez_compressed(path, batch_sizes=sizes, chunk_lengths=lengths)
    def histogram(values: np.ndarray) -> dict[str, int]:
        unique, frequencies = np.unique(values, return_counts=True)
        return {str(int(value)): int(count) for value, count in zip(unique, frequencies)}
    return {key: value for key, value in audit.items() if key not in ("batch_sizes", "chunk_lengths")} | {
        "batch_size_min": int(sizes.min()), "batch_size_max": int(sizes.max()),
        "batch_size_histogram": histogram(sizes),
        "chunk_length_min": int(lengths.min()), "chunk_length_max": int(lengths.max()),
        "chunk_length_histogram": histogram(lengths),
        "raw_artifact": _artifact(path, out),
    }


def _save_snapshot(agent: Any, path: Path, arm: str, rollout: int, launch_sha: str, out: Path) -> dict:
    payload = {"schema": 1, "object": OBJECT, "arm": arm, "launch_sha": launch_sha,
               "rollout": rollout, "config": b16._config_record(agent.config),
               "modules": {name: module.state_dict() for name, module in model_modules(agent).items()},
               "normalizers": b11._normalizer_manifest(agent),
               "usage": "Strict read-only deterministic evaluation; no optimizer resume."}
    partial = path.with_suffix(path.suffix + ".partial")
    torch.save(payload, partial)
    partial.replace(path)
    return {**_artifact(path, out), "parameter_normalizer_digest": digest_agent(agent)}


def _make_config(envs: list[Any], seed: int, spec: Any = SPEC) -> Any:
    return b16.make_b16_config(b20.Arm("F", seed), envs, spec, expected_n=N)


def _source_runtime(source: int, envs: list[Any], payloads: dict, log: Path, spec: Any = SPEC) -> Any:
    cfg = _make_config(envs, SOURCE[source]["seed"], spec)
    if spec == SPEC:
        actual = b16._config_record(cfg)
        published = payloads[source]["published_config"]["config"]
        differing = {key for key in set(actual) | set(published)
                     if actual.get(key) != published.get(key)}
        permitted = {"num_envs", "batch_size", "discriminator_batch_size",
                     "high_level_batch_size", "high_level_buffer_size"}
        if differing - permitted:
            raise ValueError(f"source runtime config differs from published B20: {differing}")
    return b01.restore_runtime(cfg, payloads[source]["checkpoint"],
                               payloads[source]["expected_digest"], log)


def _assignments(arm: str, rng: np.random.Generator, lanes: int) -> np.ndarray:
    if arm == "F1":
        return np.ones(lanes, dtype=np.int8)
    if arm == "F2":
        return np.full(lanes, 2, dtype=np.int8)
    if arm != "M":
        raise ValueError("unknown B02 fit")
    if lanes % 2:
        raise ValueError("M requires an even lane count")
    return rng.permutation(np.array([1] * (lanes // 2) + [2] * (lanes // 2), dtype=np.int8))


def _train_rollout(agent: Any, buffer: Any, arm: str, rollout: int, payloads: dict,
                   assignment_rng: np.random.Generator, out: Path, spec: Any = SPEC,
                   world_base: int = TRAIN_WORLD_BASE) -> dict:
    base = world_base + 100 * rollout
    if buffer.num_steps != spec.horizon or buffer.num_envs != spec.train_lanes:
        raise ValueError("training buffer/spec mismatch")
    envs: list[Any] = []
    trace: dict[str, Any] = {}
    active_step = -1
    try:
        rng_before = b03._rng_digest()
        with preserve_rng():
            envs = make_envs(spec.train_lanes, base, N, spec.horizon)
            pairs = [env.reset(seed=base + lane) for lane, env in enumerate(envs)]
        if b03._rng_digest() != rng_before:
            raise ValueError("native construction/reset perturbed learner RNG")
        b11._assert_native_envs(envs, N)
        if any(list(env.env.agents) != list(env.env.env.possible_agents) or
               len(env.env.agents) != N for env in envs):
            raise ValueError("native training roster order differs")
        states = np.stack([info["state"] for _, info in pairs])
        observations = np.stack([obs for obs, _ in pairs])
        world = {"rollout": rollout, "lane_world_seeds": list(range(base, base + spec.train_lanes)),
                 "states": b01._identity(states), "observations": b01._identity(observations),
                 "uav_positions": b01._identity(np.stack([e.env.env.uav_positions for e in envs])),
                 "user_positions": b01._identity(np.stack([e.env.env.user_positions for e in envs])),
                 "reset_convention": "constructor then explicit reset(seed=base+lane)"}
        reset_path = out / "raw" / f"reset_{arm}_{rollout:02d}.npz"
        np.savez_compressed(reset_path, lane_world_seeds=np.arange(base, base + spec.train_lanes),
                            states=states, observations=observations,
                            uav_positions=np.stack([e.env.env.uav_positions for e in envs]),
                            user_positions=np.stack([e.env.env.user_positions for e in envs]))
        world["raw_artifact"] = _artifact(reset_path, out)
        assignment = _assignments(arm, assignment_rng, spec.train_lanes)
        if arm == "M" and (int((assignment == 1).sum()) != spec.train_lanes // 2 or
                            int((assignment == 2).sum()) != spec.train_lanes // 2):
            raise ValueError("M partition differs from 8/8")
        sources: dict[int, Any] = {}
        with preserve_rng():
            seed_rng(RUNTIME_SEED)
            for source in sorted(set(map(int, assignment))):
                sources[source] = _source_runtime(source, envs, payloads,
                                                  out / "raw" / "logs" / f"{arm}_{rollout}_source{source}", spec)
        if b03._rng_digest() != rng_before:
            raise ValueError("source runtime construction perturbed learner RNG")
        for lane in range(spec.train_lanes):
            agent.reset_env_state(lane)
            for source in sources.values():
                source.reset_env_state(lane)
        source_before = {str(k): digest_agent(v) for k, v in sources.items()}
        source_done = np.zeros(spec.train_lanes, dtype=bool)
        source_steps = np.zeros(spec.train_lanes, dtype=np.int64)
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        shape = (spec.horizon, spec.train_lanes)
        raw_learner = np.full((*shape, 3, 3), np.nan, dtype=np.float32)
        raw_partner = np.full_like(raw_learner, np.nan)
        executed = np.full((*shape, N, 3), np.nan, dtype=np.float32)
        logprobs = np.full((*shape, 3), np.nan, dtype=np.float32)
        streams = {name: np.full(shape, np.nan, dtype=np.float64)
                   for name in (*COMPONENTS, "scalar_reward", "E", "S", "U", "height")}
        env_attempted = np.zeros(shape, dtype=bool)
        env_returned = np.zeros(shape, dtype=bool)
        validated = np.zeros(shape, dtype=bool)
        learner_infer_attempted = np.zeros(spec.horizon, dtype=bool)
        learner_infer_returned = np.zeros(spec.horizon, dtype=bool)
        partner_infer_attempted = np.zeros((spec.horizon, len(sources)), dtype=bool)
        partner_infer_returned = np.zeros_like(partner_infer_attempted)
        trace = locals().copy()
        with torch.no_grad():
            for t in range(spec.horizon):
                active_step = t
                learner_infer_attempted[t] = True
                learner_raw, _, data = agent.step(states, observations, steps, dones,
                                                  deterministic=False, return_step_data=True,
                                                  build_infos=False)
                learner_infer_returned[t] = True
                finite((learner_raw, data), "B02 learner policy output")
                if learner_raw.shape != (spec.train_lanes, N, 3) or learner_raw.dtype != np.float32:
                    raise ValueError("learner physical action shape/dtype mismatch")
                source_raw = {}
                for index, (source, runtime) in enumerate(sources.items()):
                    partner_infer_attempted[t, index] = True
                    with preserve_rng():
                        action, _, _ = runtime.step(states, observations, source_steps, source_done,
                                                    deterministic=True, return_step_data=True,
                                                    build_infos=False)
                    partner_infer_returned[t, index] = True
                    finite(action, "B02 source policy output")
                    if action.shape != learner_raw.shape or action.dtype != np.float32:
                        raise ValueError("source physical action shape/dtype mismatch")
                    source_raw[source] = action
                selected = np.stack([source_raw[int(assignment[lane])][lane, 3:]
                                     for lane in range(spec.train_lanes)])
                joined = np.concatenate((learner_raw[:, :3], selected), axis=1)
                mapped = b03.map_training_actions(joined, "clip")
                if (mapped.shape != joined.shape or not np.isfinite(mapped).all() or
                    np.any(mapped < -1) or np.any(mapped > 1)):
                    raise ValueError("native action clipping invalid")
                raw_learner[t], raw_partner[t], executed[t] = learner_raw[:, :3], selected, mapped
                logprobs[t] = np.asarray(data["action_logprobs"])[:, :3]
                next_states, next_observations = [], []
                rewards = np.zeros(spec.train_lanes, dtype=np.float32)
                next_dones = np.zeros(spec.train_lanes, dtype=bool)
                for lane, env in enumerate(envs):
                    env_attempted[t, lane] = True
                    obs, reward, term, trunc, info = env.step(mapped[lane])
                    env_returned[t, lane] = True
                    streams["scalar_reward"][t, lane] = float(reward)
                    raw_parts = info.get("reward_components", {}).get("reward_info", {})
                    for name in COMPONENTS:
                        if name in raw_parts:
                            streams[name][t, lane] = float(raw_parts[name])
                    parts = native_components(info, reward, N)
                    e, s, u, height = b01._service(env, parts)
                    for name, value in (("E", e), ("S", s), ("U", u), ("height", height)):
                        streams[name][t, lane] = value
                    validated[t, lane] = True
                    next_states.append(info["next_state"])
                    next_observations.append(obs)
                    rewards[lane], next_dones[lane] = reward, bool(term or trunc)
                store_learner_step(buffer, agent, t=t, states=states, observations=observations,
                                   raw_actions=learner_raw, step_data=data,
                                   scalar_rewards=rewards, dones=next_dones)
                if next_dones.any() and (t != spec.horizon - 1 or not next_dones.all()):
                    raise ValueError("unexpected native training terminal")
                states, observations = np.stack(next_states), np.stack(next_observations)
                dones = source_done = next_dones
                steps += 1
                source_steps += 1
        if not dones.all() or not env_returned.all() or not validated.all():
            raise ValueError("incomplete B02 training rollout")
        source_after = {str(k): digest_agent(v) for k, v in sources.items()}
        if source_after != source_before:
            raise ValueError("frozen source drift during training")
        path = out / "raw" / f"train_{arm}_{rollout:02d}.npz"
        np.savez_compressed(path, learner_raw=raw_learner, partner_raw=raw_partner,
                            executed=executed, learner_old_logprobs=logprobs,
                            assignment=assignment, env_attempted=env_attempted,
                            env_returned=env_returned, components_validated=validated,
                            learner_infer_attempted=learner_infer_attempted,
                            learner_infer_returned=learner_infer_returned,
                            partner_infer_attempted=partner_infer_attempted,
                            partner_infer_returned=partner_infer_returned, **streams)
        return {"rollout": rollout, "status": "collected", "world": world,
                "assignment": assignment.tolist(), "source_digest_before": source_before,
                "source_digest_after": source_after,
                "per_lane_scalar_return": streams["scalar_reward"].sum(axis=0).tolist(),
                "per_lane_J": (N * streams["scalar_reward"].mean(axis=0)).tolist(),
                "per_lane_served_per_step": streams["S"].mean(axis=0).tolist(),
                "counts": {"team_steps": int(env_returned.sum()),
                           "environment_step_attempts": int(env_attempted.sum()),
                           "learner_inference_calls": int(learner_infer_returned.sum()),
                           "learner_inferred_rows": int(learner_infer_returned.sum()) * spec.train_lanes * N,
                           "partner_inference_calls": int(partner_infer_returned.sum()),
                           "partner_inferred_rows": int(partner_infer_returned.sum()) * spec.train_lanes * N,
                           "executed_learner_rows": int(env_returned.sum()) * 3,
                           "executed_partner_rows": int(env_returned.sum()) * 3},
                "raw_artifact": _artifact(path, out)}
    except Exception as exc:
        failure = {"rollout": rollout, "status": "failed", "active_step": active_step,
                   "failure": f"{type(exc).__name__}: {exc}"}
        if "world" in locals():
            failure["world"] = world
        if trace:
            attempted, returned = trace["env_attempted"], trace["env_returned"]
            failure["counts"] = {"environment_step_attempts": int(attempted.sum()),
                                 "environment_step_returns": int(returned.sum()),
                                 "environment_outcomes_unknown": int((attempted & ~returned).sum()),
                                 "components_validated": int(trace["validated"].sum()),
                                 "executed_action_rows_confirmed": int(returned.sum()) * N,
                                 "learner_inference_attempts": int(trace["learner_infer_attempted"].sum()),
                                 "learner_inference_returns": int(trace["learner_infer_returned"].sum()),
                                 "partner_inference_attempts": int(trace["partner_infer_attempted"].sum()),
                                 "partner_inference_returns": int(trace["partner_infer_returned"].sum())}
            path = out / "raw" / f"train_{arm}_{rollout:02d}_partial.npz"
            np.savez_compressed(path, learner_raw=trace["raw_learner"], partner_raw=trace["raw_partner"],
                                executed=trace["executed"], learner_old_logprobs=trace["logprobs"],
                                assignment=trace["assignment"], env_attempted=attempted,
                                env_returned=returned, components_validated=trace["validated"],
                                **trace["streams"])
            failure["raw_artifact"] = _artifact(path, out)
        write_json(out / f"train_{arm}_{rollout:02d}.json", failure)
        raise
    finally:
        for env in envs:
            env.close()


def _eval_cell(learner_name: str, partner: int, snapshots: dict[str, dict],
               payloads: dict, out: Path, spec: Any = SPEC,
               world_base: int = EVAL_WORLD_BASE) -> dict:
    """Build private full-roster runtimes and run one fixed native evaluation cell."""
    envs: list[Any] = []
    active_step = -1
    trace: dict[str, Any] = {}
    key = f"{learner_name}_p{partner}"
    try:
        with preserve_rng():
            seed_rng(RUNTIME_SEED)
            envs = make_envs(spec.eval_lanes, world_base, N, spec.horizon)
            b11._assert_native_envs(envs, N)
            if any(list(env.env.agents) != list(env.env.env.possible_agents) or
                   len(env.env.agents) != N for env in envs):
                raise ValueError("native evaluation roster order differs")
            if learner_name == "OLD3":
                first = _source_runtime(3, envs, payloads, out / "raw/logs" / key / "first", spec)
            else:
                snapshot = snapshots[learner_name]
                first = b01.restore_runtime(_make_config(envs, SEED, spec), snapshot["payload"],
                                            snapshot["digest"], out / "raw/logs" / key / "first")
            second = _source_runtime(partner, envs, payloads, out / "raw/logs" / key / "second", spec)
            if first is second:
                raise ValueError("evaluation runtimes are not independent")
            agents = (first, second)
            pairs = [env.reset() for env in envs]
            states = np.stack([info["state"] for _, info in pairs])
            observations = np.stack([obs for obs, _ in pairs])
            scenes = {"states": states, "observations": observations,
                      "uav_positions": np.stack([e.env.env.uav_positions for e in envs]),
                      "user_positions": np.stack([e.env.env.user_positions for e in envs])}
            identity = {name: b01._identity(value) for name, value in scenes.items()}
            per_world_identity = [{name: b01._identity(value[lane]) for name, value in scenes.items()}
                                  for lane in range(spec.eval_lanes)]
            steps = np.zeros(spec.eval_lanes, dtype=np.int64)
            dones = np.zeros(spec.eval_lanes, dtype=bool)
            shape = (spec.horizon, spec.eval_lanes)
            first_raw = np.full((*shape, N, 3), np.nan, dtype=np.float32)
            second_raw = np.full_like(first_raw, np.nan)
            executed = np.full_like(first_raw, np.nan)
            streams = {name: np.full(shape, np.nan, dtype=np.float64)
                       for name in (*COMPONENTS, "scalar_reward", "E", "S", "U", "height")}
            infer_attempted = np.zeros((spec.horizon, 2), dtype=bool)
            infer_returned = np.zeros_like(infer_attempted)
            env_attempted = np.zeros(shape, dtype=bool)
            env_returned = np.zeros_like(env_attempted)
            validated = np.zeros_like(env_attempted)
            terminated = np.zeros_like(env_attempted)
            truncated = np.zeros_like(env_attempted)
            before = [digest_agent(agent) for agent in agents]
            trace = locals().copy()
            with torch.no_grad():
                for t in range(spec.horizon):
                    active_step = t
                    actions = []
                    for side, agent in enumerate(agents):
                        infer_attempted[t, side] = True
                        raw, _, data = agent.step(states, observations, steps, dones,
                                                  deterministic=True, return_step_data=True,
                                                  build_infos=False)
                        infer_returned[t, side] = True
                        finite((raw, data), "B02 evaluation policy output")
                        if raw.shape != (spec.eval_lanes, N, 3) or raw.dtype != np.float32:
                            raise ValueError("evaluation full-roster output differs")
                        (first_raw if side == 0 else second_raw)[t] = raw
                        actions.append(raw)
                    joined = b01.route_actions(*actions)
                    mapped = b03.map_training_actions(joined, "clip")
                    if not np.isfinite(mapped).all() or np.any(mapped < -1) or np.any(mapped > 1):
                        raise ValueError("invalid evaluation clipping")
                    executed[t] = mapped
                    next_pairs = []
                    for lane, env in enumerate(envs):
                        env_attempted[t, lane] = True
                        obs, reward, term, trunc, info = env.step(mapped[lane])
                        env_returned[t, lane] = True
                        terminated[t, lane], truncated[t, lane] = bool(term), bool(trunc)
                        streams["scalar_reward"][t, lane] = float(reward)
                        raw_parts = info.get("reward_components", {}).get("reward_info", {})
                        for name in COMPONENTS:
                            if name in raw_parts:
                                streams[name][t, lane] = float(raw_parts[name])
                        parts = native_components(info, reward, N)
                        e, s, u, h = b01._service(env, parts)
                        for name, value in (("E", e), ("S", s), ("U", u), ("height", h)):
                            streams[name][t, lane] = value
                        validated[t, lane] = True
                        next_pairs.append((obs, info))
                        dones[lane] = bool(term or trunc)
                    states = np.stack([info["next_state"] for _, info in next_pairs])
                    observations = np.stack([obs for obs, _ in next_pairs])
                    steps += 1
                    if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                        raise ValueError("unexpected evaluation terminal")
            if (not dones.all() or not env_returned.all() or not validated.all() or
                [digest_agent(agent) for agent in agents] != before or
                any(np.any(agent.rollout_buffer.env_lengths) for agent in agents)):
                raise ValueError("incomplete panel or evaluation model/storage drift")
            means = {name: values.mean(axis=0) for name, values in streams.items()}
            jvalue = N * means["scalar_reward"]
            native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
            if (not np.allclose(jvalue, means["total_reward"], atol=1e-7, rtol=1e-6) or
                not np.allclose(jvalue, native_j, atol=1e-7, rtol=1e-6) or
                not np.allclose(means["S"], 50 * means["coverage_reward"], atol=1e-7, rtol=1e-6) or
                not np.allclose(means["U"], means["E"] - means["S"], atol=1e-7, rtol=1e-6)):
                raise ValueError("native evaluation aggregates differ")
            path = out / "raw" / f"eval_{key}.npz"
            np.savez_compressed(path, learner_raw=first_raw, partner_raw=second_raw,
                                executed=executed, inference_attempted=infer_attempted,
                                inference_returned=infer_returned, environment_attempted=env_attempted,
                                environment_returned=env_returned, components_validated=validated,
                                terminated=terminated, truncated=truncated, **streams)
            return {"cell": [learner_name, partner], "status": "complete",
                    "world_seeds": list(range(world_base, world_base + spec.eval_lanes)),
                    "reset_convention": "constructor then unseeded reset()",
                    "initial_world_identity": identity, "initial_world_identity_per_world": per_world_identity,
                    "per_world": {"J": jvalue.tolist(), "scalar_return": (means["scalar_reward"] * spec.horizon).tolist(),
                                  **{name: values.tolist() for name, values in means.items()}},
                    "counts": {"team_steps": int(env_returned.sum()),
                               "environment_step_attempts": int(env_attempted.sum()),
                               "executed_action_rows": int(env_returned.sum()) * N,
                               "policy_step_calls": int(infer_returned.sum()),
                               "inferred_action_rows": int(infer_returned.sum()) * spec.eval_lanes * N,
                               "optimizer_updates": 0, "storage_calls": 0},
                    "runtime_digest_before_after": before, "raw_artifact": _artifact(path, out)}
    except Exception as exc:
        failure = {"cell": [learner_name, partner], "status": "failed", "active_step": active_step,
                   "failure": f"{type(exc).__name__}: {exc}"}
        if trace:
            attempted, returned = trace["env_attempted"], trace["env_returned"]
            failure["counts"] = {"environment_step_attempts": int(attempted.sum()),
                                 "environment_step_returns": int(returned.sum()),
                                 "environment_outcomes_unknown": int((attempted & ~returned).sum()),
                                 "components_validated": int(trace["validated"].sum()),
                                 "executed_action_rows_confirmed": int(returned.sum()) * N,
                                 "policy_step_attempts": int(trace["infer_attempted"].sum()),
                                 "policy_step_returns": int(trace["infer_returned"].sum())}
            path = out / "raw" / f"eval_{key}_partial.npz"
            np.savez_compressed(path, learner_raw=trace["first_raw"], partner_raw=trace["second_raw"],
                                executed=trace["executed"], inference_attempted=trace["infer_attempted"],
                                inference_returned=trace["infer_returned"], environment_attempted=attempted,
                                environment_returned=returned, components_validated=trace["validated"],
                                terminated=trace["terminated"], truncated=trace["truncated"],
                                **trace["streams"])
            failure["raw_artifact"] = _artifact(path, out)
        write_json(out / f"eval_{key}.json", failure)
        raise
    finally:
        for env in envs:
            env.close()


def _fit(arm: str, payloads: dict, assignment_rng: np.random.Generator,
         out: Path, launch_sha: str, progress: dict, spec: Any = SPEC,
         world_base: int = TRAIN_WORLD_BASE) -> tuple[dict, dict]:
    fit_start = time.perf_counter()
    fit_cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    seed_rng(SEED)
    # First native reset also supplies the shape/config contract; it has no learner-RNG effect.
    with preserve_rng():
        probe_envs = make_envs(spec.train_lanes, world_base + 100, N, spec.horizon)
    try:
        config = _make_config(probe_envs, SEED, spec)
    finally:
        for env in probe_envs:
            env.close()
    agent = b16.build_local_agent(config, str(out / "raw/logs" / f"fit_{arm}"))
    agent.train(True)
    initial_digest = digest_agent(agent)
    initial_optimizers = b15._optimizer_state_digest(agent)
    initial_parameters = capture_parameters(agent)
    initial_normalizers = b11._normalizer_manifest(agent)
    initial_path = out / "raw" / f"init_{arm}.pt"
    initial_snapshot = _save_snapshot(agent, initial_path, arm, 0, launch_sha, out)
    buffer = learner_buffer(agent, horizon=spec.horizon, lanes=spec.train_lanes)
    counts, handles = optimizer_counts(agent)
    rows = []
    try:
        for rollout in range(1, spec.rollouts + 1):
            progress.update(active_fit=arm, active_rollout=rollout, phase="collecting")
            write_json(out / "progress.json", progress)
            row = _train_rollout(agent, buffer, arm, rollout, payloads, assignment_rng, out, spec,
                                 world_base)
            progress["phase"] = "updating"
            write_json(out / "progress.json", progress)
            before_counts = counts.copy()
            try:
                losses, audit = update_learner(agent, buffer, np.ones(spec.train_lanes, dtype=bool))
                finite(losses, "B02 learner update losses")
                compact_audit = _compact_update_audit(
                    audit, out / "raw" / f"sampler_{arm}_{rollout:02d}.npz", out)
                row["update_audit"] = compact_audit
                row["losses"] = jsonable(losses)
                expected_calls = ((spec.horizon // int(config.k) * spec.train_lanes * 3 +
                                   int(config.sequence_batch_size) - 1) // int(config.sequence_batch_size)) * int(config.ppo_epochs)
                if (counts["discoverer_actor"] - before_counts["discoverer_actor"] != expected_calls or
                    counts["discoverer_critic"] - before_counts["discoverer_critic"] != expected_calls or
                    any(counts[name] != before_counts[name] for name in counts if name not in
                        ("discoverer_actor", "discoverer_critic"))):
                    raise ValueError("B02 optimizer exposure differs from learner-only recipe")
                row.update(status="complete",
                           optimizer_calls={name: counts[name] - before_counts[name] for name in counts},
                           parameter_normalizer_digest_after=digest_agent(agent))
                write_json(out / f"train_{arm}_{rollout:02d}.json", row)
            except Exception as exc:
                try:
                    current_digest = digest_agent(agent)
                except Exception as digest_exc:
                    current_digest = f"unavailable: {type(digest_exc).__name__}: {digest_exc}"
                row.update(status="failed_during_update", failure=f"{type(exc).__name__}: {exc}",
                           optimizer_calls_after_failure=counts.copy(),
                           optimizer_calls_during_rollout={name: counts[name] - before_counts[name]
                                                           for name in counts},
                           parameter_normalizer_digest_after_failure=current_digest)
                write_json(out / f"train_{arm}_{rollout:02d}.json", row)
                raise
            rows.append(row)
            progress["completed_rollouts"].append([arm, rollout])
            write_json(out / "progress.json", progress)
            buffer.reset()  # Keeps its private sampler RNG advancing across rollouts.
        final_path = out / "raw" / f"final_{arm}.pt"
        final_snapshot = _save_snapshot(agent, final_path, arm, spec.rollouts, launch_sha, out)
        fit = {"arm": arm, "status": "complete", "config": b16._config_record(config),
               "initial_digest": initial_digest, "initial_optimizer_state_digest": initial_optimizers,
               "initial_normalizers": initial_normalizers, "initial_checkpoint": initial_snapshot,
               "final_checkpoint": final_snapshot, "final_digest": digest_agent(agent),
               "final_optimizer_state_digest": b15._optimizer_state_digest(agent),
               "parameter_motion": parameter_motion(agent, initial_parameters),
               "telemetry": {"wall_seconds": time.perf_counter() - fit_start,
                             "process_cpu_seconds": (resource.getrusage(resource.RUSAGE_SELF).ru_utime - fit_cpu_start.ru_utime) +
                                                    (resource.getrusage(resource.RUSAGE_SELF).ru_stime - fit_cpu_start.ru_stime)},
               "optimizer_calls": counts.copy(), "rollouts": rows,
               "counts": {"team_steps": sum(row["counts"]["team_steps"] for row in rows),
                          "episodes": sum(row["counts"]["team_steps"] for row in rows) // spec.horizon,
                          "executed_learner_rows": sum(row["counts"]["executed_learner_rows"] for row in rows),
                          "executed_partner_rows": sum(row["counts"]["executed_partner_rows"] for row in rows),
                          "learner_inferred_rows": sum(row["counts"]["learner_inferred_rows"] for row in rows),
                          "partner_inferred_rows": sum(row["counts"]["partner_inferred_rows"] for row in rows)}}
        write_json(out / f"fit_{arm}.json", fit)
        return fit, {"payload": torch.load(final_path, map_location="cpu", weights_only=True),
                     "digest": fit["final_digest"]}
    finally:
        for handle in handles:
            handle.remove()


def run_study(out: Path, launch_sha: str, admission: dict, checkpoint_paths: dict[int, Path],
              *, seed: int, command_start: float) -> dict:
    """Run the single admitted, fixed three-fit/thirteen-cell B02 batch."""
    if seed != SEED or launch_sha != admission["sha"]:
        raise ValueError("B02 seed/launch admission mismatch")
    out = Path(out).resolve()
    bound_output = admission.get("output_root")
    if bound_output is not None and out != Path(bound_output).resolve():
        raise ValueError("B02 output path disagrees with admission")
    if not out.is_dir():
        raise ValueError("B02 requires launcher-created output directory")
    scientific_prefixes = ("config.json", "progress.json", "summary.json", "fit_", "train_", "eval_", "raw")
    collisions = [entry.name for entry in out.iterdir() if entry.name.startswith(scientific_prefixes)]
    if collisions:
        raise ValueError(f"B02 scientific output already exists: {sorted(collisions)}")
    torch.set_num_threads(4)
    payloads, dependencies = b01.validate_sources(checkpoint_paths)
    (out / "raw").mkdir()
    config = {"object": OBJECT, "tag": TAG, "launch_sha": launch_sha,
              "admission": jsonable(admission), "seed": SEED,
              "assignment_seed": ASSIGNMENT_SEED, "runtime_seed": RUNTIME_SEED,
              "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_draws": BOOTSTRAP_DRAWS,
              "train_world_base": TRAIN_WORLD_BASE, "eval_world_base": EVAL_WORLD_BASE,
              "train_lanes": TRAIN_LANES, "eval_lanes": EVAL_LANES, "horizon": HORIZON,
              "rollouts": ROLLOUTS, "epochs": EPOCHS, "physical_n": N,
              "learner_roles": [0, 1, 2], "partner_roles": [3, 4, 5],
              "arms": ARMS, "eval_cells": EVAL_CELLS,
              "source_commit": SOURCE_COMMIT, "source_bindings": SOURCE,
              "checkpoints": {str(k): {"path": str(checkpoint_paths[k]),
                                       "sha256": SOURCE[k]["checkpoint_sha256"]} for k in SOURCE},
              "source_dependencies_sha256": dependencies,
              "torch_threads": 4, "device": "cpu", "dtype": "float32",
              "training_reset": "constructor then explicit reset(seed=base+lane)",
              "evaluation_reset": "constructor then unseeded reset()"}
    write_json(out / "config.json", config)
    progress = {"status": "running", "phase": "training", "active_fit": None,
                "active_rollout": None, "active_cell": None,
                "completed_rollouts": [], "completed_fits": [], "completed_cells": []}
    write_json(out / "progress.json", progress)
    fits: list[dict] = []
    cells: list[dict] = []
    try:
        assignment_rng = np.random.default_rng(ASSIGNMENT_SEED)
        snapshots: dict[str, dict] = {}
        common_initial = None
        common_optimizer = None
        common_normalizers = None
        for arm in ARMS:
            fit, snapshot = _fit(arm, payloads, assignment_rng, out, launch_sha, progress)
            if common_initial is None:
                common_initial = fit["initial_digest"]
                common_optimizer = fit["initial_optimizer_state_digest"]
                common_normalizers = fit["initial_normalizers"]
                init_path = out / fit["initial_checkpoint"]["path"]
                snapshots["I"] = {"payload": torch.load(init_path, map_location="cpu", weights_only=True),
                                  "digest": common_initial}
            elif (fit["initial_digest"] != common_initial or
                  fit["initial_optimizer_state_digest"] != common_optimizer or
                  fit["initial_normalizers"] != common_normalizers):
                raise ValueError("B02 fresh learner initial states differ")
            fits.append(fit)
            snapshots[arm] = snapshot
            progress["completed_fits"].append(arm)
            write_json(out / "progress.json", progress)
        if any(fit["optimizer_calls"].get(name, 0) != (50_625 if name in
               ("discoverer_actor", "discoverer_critic") else 0)
               for fit in fits for name in fit["optimizer_calls"]):
            raise ValueError("B02 fixed optimizer call count mismatch")
        if any(fit["counts"]["team_steps"] != 360_000 for fit in fits):
            raise ValueError("B02 physical training step count mismatch")
        progress.update(phase="evaluation", active_fit=None, active_rollout=None)
        write_json(out / "progress.json", progress)
        first_identity = None
        first_per_world = None
        for learner_name, partner in EVAL_CELLS:
            progress["active_cell"] = [learner_name, partner]
            write_json(out / "progress.json", progress)
            row = _eval_cell(learner_name, partner, snapshots, payloads, out)
            if first_identity is None:
                first_identity = row["initial_world_identity"]
                first_per_world = row["initial_world_identity_per_world"]
            elif (row["initial_world_identity"] != first_identity or
                  row["initial_world_identity_per_world"] != first_per_world):
                raise ValueError("B02 initial world bytes differ across cells")
            cells.append(row)
            write_json(out / f"eval_{learner_name}_p{partner}.json", row)
            progress["completed_cells"].append([learner_name, partner])
            write_json(out / "progress.json", progress)
        j = np.stack([row["per_world"]["J"] for row in cells], axis=1)
        s = np.stack([row["per_world"]["S"] for row in cells], axis=1)
        analysis = reduce_panel(j, s)
        ru = resource.getrusage(resource.RUSAGE_SELF)
        artifacts = [_artifact(path, out) for path in sorted((out / "raw").rglob("*")) if path.is_file()]
        counts = {"fits": 3, "training_team_steps": sum(fit["counts"]["team_steps"] for fit in fits),
                  "training_executed_learner_rows": sum(fit["counts"]["executed_learner_rows"] for fit in fits),
                  "training_executed_partner_rows": sum(fit["counts"]["executed_partner_rows"] for fit in fits),
                  "training_learner_inferred_rows": sum(fit["counts"]["learner_inferred_rows"] for fit in fits),
                  "training_partner_inferred_rows": sum(fit["counts"]["partner_inferred_rows"] for fit in fits),
                  "evaluation_team_steps": sum(row["counts"]["team_steps"] for row in cells),
                  "evaluation_executed_action_rows": sum(row["counts"]["executed_action_rows"] for row in cells),
                  "evaluation_inferred_action_rows": sum(row["counts"]["inferred_action_rows"] for row in cells),
                  "evaluation_episodes": EVAL_LANES * len(EVAL_CELLS),
                  "actor_optimizer_calls": sum(fit["optimizer_calls"]["discoverer_actor"] for fit in fits),
                  "critic_optimizer_calls": sum(fit["optimizer_calls"]["discoverer_critic"] for fit in fits)}
        if (counts["training_team_steps"] != 1_080_000 or
            counts["training_executed_learner_rows"] != 3_240_000 or
            counts["training_executed_partner_rows"] != 3_240_000 or
            counts["evaluation_team_steps"] != 208_000 or
            counts["evaluation_executed_action_rows"] != 1_248_000):
            raise ValueError("B02 fixed total exposure mismatch")
        summary = {"object": OBJECT, "status": "complete", "launch_sha": launch_sha,
                   "config_sha256": b01.sha256(out / "config.json"), "sources": config["checkpoints"],
                   "source_bindings": SOURCE, "source_dependencies_sha256": dependencies,
                   "fits": fits, "cells": cells, "analysis": analysis, "counts": counts,
                   "telemetry": {"wall_seconds": time.perf_counter() - command_start,
                                 "process_cpu_seconds": ru.ru_utime + ru.ru_stime,
                                 "peak_process_rss_kib": ru.ru_maxrss,
                                 "raw_bytes": sum(item["bytes"] for item in artifacts)},
                   "artifacts": artifacts,
                   "interpretation_limit": "One exploratory fit per arm; world intervals are conditional, not training-population inference."}
        write_json(out / "summary.json", summary)
        progress.update(status="complete", phase="complete", active_cell=None,
                        summary_sha256=b01.sha256(out / "summary.json"))
        write_json(out / "progress.json", progress)
        return summary
    except Exception as exc:
        progress.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        # Preserve the latest cell/rollout failure record and the completed-prefix identities.
        write_json(out / "progress.json", progress)
        raise
