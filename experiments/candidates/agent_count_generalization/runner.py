"""One admitted native S1 fit and its fixed N=4/6/8 evaluation panels."""
from __future__ import annotations

import time
PROCESS_START = time.perf_counter()

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import sys
import traceback

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC, DIRECTION, SEEDS, config_dict, make_config,
)
from scripts.hmasd_admission import require_admission

COMPONENTS = ("coverage_reward", "quality_reward", "energy_penalty", "total_reward")
OPTIMIZERS = ("coordinator", "discoverer_actor", "discoverer_critic",
              "team_discriminator", "individual_discriminator")
NORMALIZERS = ("obs_norm", "state_norm", "value_norm_coordinator", "value_norm_discoverer")


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if torch.is_tensor(value):
        return jsonable(value.detach().cpu().numpy())
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path, value):
    encoded = json.dumps(jsonable(value), indent=2, allow_nan=False) + "\n"
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(encoded, encoding="utf-8")
    partial.replace(path)


def finite(value, label):
    if isinstance(value, dict):
        for k, v in value.items():
            finite(v, f"{label}.{k}")
    elif isinstance(value, (tuple, list)):
        for v in value:
            finite(v, label)
    elif torch.is_tensor(value):
        if not bool(torch.isfinite(value).all()):
            raise ValueError(f"nonfinite {label}")
    elif isinstance(value, (np.ndarray, float, np.number)) and not np.isfinite(value).all():
        raise ValueError(f"nonfinite {label}")


def seed_rng(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


@contextlib.contextmanager
def preserve_rng():
    py, np_state, torch_state = random.getstate(), np.random.get_state(), torch.get_rng_state()
    try:
        yield
    finally:
        random.setstate(py)
        np.random.set_state(np_state)
        torch.set_rng_state(torch_state)


def model_modules(agent):
    return {name: module for name in ("skill_coordinator", "skill_discoverer",
                                      "team_discriminator", "individual_discriminator")
            if (module := getattr(agent, name, None)) is not None}


def motion_modules(agent):
    result = {"coordinator": agent.skill_coordinator,
              "discoverer_actor": agent.skill_discoverer.actor,
              "discoverer_critic": agent.skill_discoverer.critic}
    for name in ("team_discriminator", "individual_discriminator"):
        module = getattr(agent, name, None)
        if module is not None:
            result[name] = module
    for root_name, module in list(result.items()):
        for name, child in module.named_modules():
            if name and type(child).__name__ in {"StateSetEncoder", "SetActorBase"}:
                result[f"{root_name}.{name}"] = child
    return result


def capture_parameters(agent):
    return {name: {k: p.detach().cpu().clone() for k, p in module.named_parameters()}
            for name, module in motion_modules(agent).items()}


def parameter_motion(agent, initial):
    result = {}
    for name, module in motion_modules(agent).items():
        numerator, denominator = 0.0, 0.0
        for key, p in module.named_parameters():
            p0 = initial[name][key].double()
            delta = p.detach().cpu().double() - p0
            numerator += float(delta.square().sum())
            denominator += float(p0.square().sum())
        result[name] = {"delta_l2": numerator ** .5,
                        "relative_l2": (numerator / denominator) ** .5 if denominator else None}
    return result


def digest_agent(agent):
    digest = hashlib.sha256()
    for module_name, module in model_modules(agent).items():
        for key, value in module.state_dict().items():
            array = value.detach().cpu().contiguous().numpy()
            digest.update(f"{module_name}.{key}|{array.dtype}|{array.shape}".encode())
            digest.update(array.tobytes())
    for name in NORMALIZERS:
        norm = getattr(agent, name, None)
        if norm is not None:
            digest.update(json.dumps(jsonable(vars(norm)), sort_keys=True, allow_nan=False).encode())
    return digest.hexdigest()


def optimizer_counts(agent):
    counts = {name: 0 for name in OPTIMIZERS}
    handles = []
    for name in OPTIMIZERS:
        optimizer = getattr(agent, name + "_optimizer", None)
        if optimizer is not None:
            def count_step(_optimizer, _args, _kwargs, key=name):
                counts[key] += 1
            handles.append(optimizer.register_step_post_hook(count_step))
    return counts, handles


def reset_all(envs):
    pairs = [env.reset() for env in envs]
    return (np.stack([info["state"] for obs, info in pairs]),
            np.stack([obs for obs, info in pairs]))


def native_components(info, scalar, n):
    parts = {name: float(info["reward_components"]["reward_info"][name]) for name in COMPONENTS}
    finite(parts, "native components")
    expected = .7 * parts["coverage_reward"] + .3 * parts["quality_reward"] - parts["energy_penalty"]
    if not np.isclose(n * scalar, expected, atol=1e-7, rtol=1e-6):
        raise ValueError(f"adapter scalar/native reward mismatch at N={n}: {n * scalar} vs {expected}")
    if not np.isclose(parts["total_reward"], expected, atol=1e-7, rtol=1e-6):
        raise ValueError("native reward component identity failed")
    return parts


def save_checkpoint(agent, out, rollout, config, sha):
    path = out / f"checkpoint_{rollout:02d}.pt"
    payload = {
        "schema": 1, "direction": DIRECTION, "launch_sha": sha, "rollout": rollout,
        "config": config_dict(config),
        "modules": {name: module.state_dict() for name, module in model_modules(agent).items()},
        "normalizers": {name: jsonable(vars(norm)) if (norm := getattr(agent, name, None)) is not None
                        else None for name in NORMALIZERS},
        "usage": "Evaluation weights; no training resume contract or optimizer restoration.",
    }
    partial = path.with_suffix(".pt.partial")
    torch.save(payload, partial)
    partial.replace(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": path.name, "sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def evaluate_panel(learner, arm, seed, rollout, out, summary, spec, publish):
    from experiments.candidates.agent_count_generalization.adapter import make_envs
    from experiments.candidates.agent_count_generalization.models import build_agent, strict_sync

    learner_before = digest_agent(learner)
    with preserve_rng():
        for n in spec.test_ns:
            # Fresh world addresses for each checkpoint; within one N/panel all
            # arms and all independent fits evaluate on the same world panel.
            world_seed = 930000 + rollout * 1000 + n * 100
            seed_rng(world_seed + 51)
            envs = make_envs(spec.eval_lanes, world_seed, n, spec.horizon)
            target = None
            row = {"after_rollout": rollout, "training_team_steps": rollout * spec.train_lanes * spec.horizon,
                   "test_n": n, "world_seeds": list(range(world_seed, world_seed + spec.eval_lanes)),
                   "status": "running", "steps": 0, "episodes": 0}
            summary["panels"].append(row)
            publish(f"evaluation {rollout} N={n} starting")
            try:
                config = make_config(arm, envs, seed, spec)
                target = build_agent(config, str(out / "evaluation_logs" / f"r{rollout}_n{n}"))
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                before = digest_agent(target)
                states, observations = reset_all(envs)
                steps = np.zeros(spec.eval_lanes, dtype=int)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                components = {key: np.zeros(spec.eval_lanes) for key in COMPONENTS}
                with torch.no_grad():
                    for t in range(spec.horizon):
                        actions, _, data = target.step(states, observations, steps, dones,
                            deterministic=True, return_step_data=True, build_infos=False)
                        finite(actions, "evaluation actions")
                        if actions.shape != (spec.eval_lanes, n, 3):
                            raise ValueError("evaluation action roster mismatch")
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(actions[lane])
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for key in COMPONENTS:
                                components[key][lane] += parts[key]
                            states[lane] = info["next_state"]
                            observations[lane] = obs
                            dones[lane] = bool(term or trunc)
                            row["steps"] += 1
                            summary["counts"]["evaluation_team_steps"] += 1
                            row["episodes"] += int(dones[lane])
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected S1 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("evaluation missing terminal boundary")
                j = n * returns / spec.horizon
                means = {key: value / spec.horizon for key, value in components.items()}
                if any(calls.values()) or digest_agent(target) != before:
                    raise ValueError("evaluation modified parameters or normalizers")
                row.update(status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                           component_means=jsonable(means), optimizer_calls=calls.copy(),
                           frozen_weights_and_normalizers=True, config=config_dict(config))
                for hook in hooks:
                    hook.remove()
                summary["counts"]["evaluation_episodes"] += row["episodes"]
                write_json(out / f"panel_{rollout:02d}_n{n}.json", row)
                publish(f"evaluation {rollout} N={n} complete")
            except Exception as exc:
                row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
                write_json(out / f"panel_{rollout:02d}_n{n}.json", row)
                raise
            finally:
                for env in envs:
                    env.close()
                del target
    if digest_agent(learner) != learner_before:
        raise ValueError("evaluator modified learner weights or normalizers")


def run_fit(out, arm, seed, launch_sha, admission, spec=DEFAULT_SPEC):
    from experiments.candidates.agent_count_generalization.adapter import make_envs
    from experiments.candidates.agent_count_generalization.models import build_agent

    out = Path(out)
    if (out / "summary.json").exists():
        raise ValueError("existing scientific summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    summary = {"schema": 1, "direction": DIRECTION, "arm": arm, "seed": seed,
               "launch_sha": launch_sha, "admission": admission,
               "status": "initializing", "fit_started": False, "failure": None,
               "spec": vars(spec), "panels": [], "checkpoints": [],
               "counts": {"training_team_steps": 0, "stored_team_steps": 0,
                          "training_episodes": 0, "updates": 0,
                          "evaluation_team_steps": 0, "evaluation_episodes": 0},
               "reward_units": {"training": "native R / train_N=6", "J": "test_N * scalar_return / horizon"},
               "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                           "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
                           "thread_environment": {name: os.environ[name] for name in
                              ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")}}}
    def publish(boundary):
        summary["last_boundary"] = boundary
        summary["wall_seconds"] = time.perf_counter() - PROCESS_START
        write_json(out / "summary.json", summary)
        print(json.dumps({"boundary": boundary, "wall_seconds": round(summary["wall_seconds"], 2)}), flush=True)
    publish("admitted")
    envs, agent, hooks = [], None, []
    try:
        torch.set_num_threads(spec.torch_threads)
        seed_rng(seed)
        envs = make_envs(spec.train_lanes, seed, spec.train_n, spec.horizon)
        config = make_config(arm, envs, seed, spec)
        summary["config"] = config_dict(config)
        write_json(out / "config.json", {"launch_sha": launch_sha, "spec": vars(spec), "config": summary["config"]})
        agent = build_agent(config, str(out / "learner_logs"))
        calls, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = calls
        summary["parameter_counts"] = {name: sum(p.numel() for p in module.parameters())
                                       for name, module in model_modules(agent).items()}
        initial = capture_parameters(agent)
        summary["initial_parameter_digest"] = digest_agent(agent)
        agent.train(True)
        if 0 in spec.panels:
            summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
            evaluate_panel(agent, arm, seed, 0, out, summary, spec, publish)
        states, observations = reset_all(envs)
        steps = np.zeros(spec.train_lanes, dtype=int)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"] = "training"
        summary["fit_started"] = True
        summary["training_started_wall"] = time.perf_counter() - PROCESS_START
        publish("training starts")
        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            before = calls.copy()
            returns = np.zeros(spec.train_lanes)
            for t in range(spec.horizon):
                actions, _, data = agent.step(states, observations, steps, dones,
                    deterministic=False, return_step_data=True, build_infos=False)
                finite(actions, "training actions")
                finite(data, "training step data")
                if actions.shape != (spec.train_lanes, spec.train_n, 3):
                    raise ValueError("training action roster mismatch")
                next_states, next_observations = [], []
                rewards = np.zeros(spec.train_lanes)
                next_dones = np.zeros(spec.train_lanes, dtype=bool)
                for lane, env in enumerate(envs):
                    obs, reward, term, trunc, info = env.step(actions[lane])
                    native_components(info, reward, spec.train_n)
                    next_states.append(info["next_state"])
                    next_observations.append(obs)
                    rewards[lane] = reward
                    next_dones[lane] = bool(term or trunc)
                    returns[lane] += reward
                    summary["counts"]["training_team_steps"] += 1
                    summary["counts"]["training_episodes"] += int(next_dones[lane])
                next_states, next_observations = np.stack(next_states), np.stack(next_observations)
                finite((next_states, next_observations, rewards), "training transition")
                agent.store_transition_batch(states=states, next_states=next_states.copy(),
                    observations=observations, next_observations=next_observations.copy(),
                    actions=actions, rewards=rewards, dones=next_dones, infos_batch=None,
                    rollout_step_idx=t, step_data=data)
                summary["counts"]["stored_team_steps"] += spec.train_lanes
                # Store the real terminal successor before constructing reset inputs.
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        obs, info = env.reset()
                        next_states[lane], next_observations[lane] = info["state"], obs
                        agent.reset_env_state(lane)
                        steps[lane] = 0
                    else:
                        steps[lane] += 1
                states, observations, dones = next_states, next_observations, next_dones
                if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                    raise ValueError("unexpected S1 training terminal boundary")
            if not dones.all():
                raise ValueError("training rollout missing full episodes")
            publish(f"rollout {rollout} collected")
            losses = agent.update(last_values=np.zeros((spec.train_lanes, spec.train_n), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon, last_state=states.copy(),
                last_observations=observations.copy())
            finite(losses, "training losses")
            summary["counts"]["updates"] += 1
            motion = parameter_motion(agent, initial)
            row = {"rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                   "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                   "optimizer_delta": {name: calls[name] - before[name] for name in calls},
                   "optimizer_total": calls.copy(), "parameter_motion": motion,
                   "rollout_wall_seconds": time.perf_counter() - rollout_start}
            with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            summary["parameter_motion"] = motion
            summary["last_training_row"] = row
            agent.clear_buffers()
            publish(f"rollout {rollout} updated")
            if rollout in spec.panels:
                summary["checkpoints"].append(save_checkpoint(agent, out, rollout, config, launch_sha))
                evaluate_panel(agent, arm, seed, rollout, out, summary, spec, publish)
        expected = spec.rollouts * spec.train_lanes * spec.horizon
        if summary["counts"]["training_team_steps"] != expected or summary["counts"]["stored_team_steps"] != expected:
            raise ValueError("training exposure incomplete")
        required = ("discoverer_actor", "discoverer_critic") + (
            ("coordinator", "team_discriminator", "individual_discriminator") if arm == "H6" else ())
        for name in required:
            if calls[name] <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"required learner module did not update: {name}")
        for name, motion in summary["parameter_motion"].items():
            if "." in name and not (arm == "SET" and name.startswith("coordinator.")) and motion["delta_l2"] <= 0:
                raise ValueError(f"new encoder did not update: {name}")
        if arm == "SET" and any(calls[name] for name in ("coordinator", "team_discriminator", "individual_discriminator")):
            raise ValueError("SET unexpectedly updated skill modules")
        summary["status"] = "complete"
        summary["final_parameter_digest"] = digest_agent(agent)
        return_code = 0
    except Exception as exc:
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {"wall_seconds_in_run_fit": time.perf_counter() - started,
                                "command_wall_seconds": time.perf_counter() - PROCESS_START,
                                "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
                                "peak_rss_kib": usage.ru_maxrss, "rss_scope": "scientific process Linux RUSAGE_SELF",
                                "resources_unmeasured": ["peak_scratch_bytes"]}
        publish(summary["status"])
    return return_code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=tuple(SEEDS), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seed not in SEEDS[args.arm]:
        parser.error("arm/seed is outside the prospective six-fit batch")
    admission = require_admission(__file__, direction="agent_count_generalization")
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA disagrees with admission")
    return run_fit(args.out, args.arm, args.seed, args.launch_sha, admission)


if __name__ == "__main__":
    raise SystemExit(main())
