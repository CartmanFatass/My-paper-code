"""Read-only, native S1/N6 controller-composition matrix."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import time
from types import MethodType
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
    COMPONENTS, NORMALIZERS, digest_agent, finite, jsonable, model_modules,
    native_components, preserve_rng, seed_rng, write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11
from experiments.candidates.controller_composition.b01.bindings import (
    ANALYSIS_SEED, BOOTSTRAP_DRAWS, CELL_ORDER, HORIZON, N, RUNTIME_SEED,
    SOURCE, SOURCE_COMMIT, SOURCE_DEPENDENCY_SHA256, WORLDS,
)
from experiments.candidates.controller_composition.b01.reducer import reduce_panel

ROOT = Path(__file__).resolve().parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identity(value: Any) -> dict:
    array = np.ascontiguousarray(value)
    return {"shape": list(array.shape), "dtype": str(array.dtype),
            "sha256": hashlib.sha256(array.tobytes()).hexdigest()}


def source_dependencies() -> dict[str, str]:
    """Assert exact B20 code and native dependencies, including shared unchanged bytes."""
    result = {}
    for relative, digest in SOURCE_DEPENDENCY_SHA256.items():
        actual = ROOT / relative
        if sha256(actual) != digest:
            raise ValueError(f"B20 source dependency differs: {relative}")
        result[relative] = digest
    return result


def validate_sources(paths: dict[int, Path]) -> tuple[dict[int, dict], dict[str, str]]:
    if set(paths) != set(SOURCE):
        raise ValueError("exactly the three frozen checkpoints are required")
    dependencies = source_dependencies()
    payloads = {}
    for number, binding in SOURCE.items():
        path = paths[number]
        if sha256(path) != binding["checkpoint_sha256"]:
            raise ValueError(f"source {number} checkpoint hash mismatch")
        published = ROOT / "runs/agent_count_generalization" / binding["tag"] / "F"
        config_path, summary_path = published / "config.json", published / "summary.json"
        if sha256(config_path) != binding["config_sha256"] or sha256(summary_path) != binding["summary_sha256"]:
            raise ValueError(f"source {number} published config/summary hash mismatch")
        config, summary = json.loads(config_path.read_text()), json.loads(summary_path.read_text())
        if (config["object_id"] != "s1_ordered_roster_confirmation_b20" or
            config["arm"] != "F" or config["block"] != number or
            config["seed"] != binding["seed"] or config["launch_sha"] != SOURCE_COMMIT or
            config["schedule"] != [6] * 45 or config["spec"]["horizon"] != HORIZON or
            config["spec"]["torch_threads"] != 4 or config["config"]["count_arm"] != "LOCAL1" or
            summary["launch_sha"] != SOURCE_COMMIT or summary["seed"] != binding["seed"] or
            summary["checkpoints"][-1]["sha256"] != binding["checkpoint_sha256"]):
            raise ValueError(f"source {number} published identity mismatch")
        payload = torch.load(path, map_location="cpu", weights_only=True)
        if (set(payload) != {"schema", "direction", "launch_sha", "rollout", "config", "modules", "normalizers", "usage"}
            or payload["schema"] != 1 or payload["direction"] != "agent_count_generalization"
            or payload["launch_sha"] != SOURCE_COMMIT or payload["rollout"] != 45
            or any(config["config"].get(k) != v for k, v in payload["config"].items())
            or set(payload["normalizers"]) != set(NORMALIZERS)):
            raise ValueError(f"source {number} checkpoint/config mismatch")
        if set(payload["modules"]) != {"skill_coordinator", "skill_discoverer"}:
            raise ValueError(f"source {number} module inventory mismatch")
        for module in payload["modules"].values():
            if any(not isinstance(value, torch.Tensor) or not bool(torch.isfinite(value).all())
                   for value in module.values()):
                raise ValueError(f"source {number} has invalid tensor")
        for norm in payload["normalizers"].values():
            if norm is not None and (set(norm) != {"mean", "var", "count"} or
                                     any(not np.isfinite(float(v)) for v in norm.values())):
                raise ValueError(f"source {number} has invalid normalizer")
        payloads[number] = {"checkpoint": payload, "published_config": config,
                            "expected_digest": summary["final_parameter_normalizer_digest"]}
    return payloads, dependencies


def _forbid_updates(agent: Any) -> None:
    def rejected(*_args: Any, **_kwargs: Any) -> None:
        raise ValueError("B01 attempted a forbidden update/storage operation")
    agent.store_transition_batch = MethodType(rejected, agent)
    for name in ("coordinator", "discoverer_actor", "discoverer_critic", "team_discriminator", "individual_discriminator"):
        optimizer = getattr(agent, name + "_optimizer", None)
        if optimizer is not None:
            optimizer.step = rejected


def restore_runtime(config: Any, payload: dict, expected_digest: str, log_dir: Path) -> Any:
    """Build a distinct full N6 runtime and restore every serialized state strictly."""
    agent = b16.build_local_agent(config, str(log_dir))
    expected_modules = model_modules(agent)
    if set(payload["modules"]) != set(expected_modules):
        raise ValueError("runtime/checkpoint module inventory differs")
    for name, module in expected_modules.items():
        module.load_state_dict(payload["modules"][name], strict=True)
    for name in NORMALIZERS:
        encoded, norm = payload["normalizers"][name], getattr(agent, name, None)
        if (encoded is None) != (norm is None):
            raise ValueError(f"normalizer presence differs: {name}")
        if norm is not None:
            if set(vars(norm)) != set(encoded):
                raise ValueError(f"normalizer fields differ: {name}")
            for field, value in encoded.items():
                setattr(norm, field, value)
    agent.train(False)
    for lane in range(config.num_envs):
        agent.reset_env_state(lane)
    if b11._normalizer_manifest(agent) != payload["normalizers"]:
        raise ValueError("normalizer restore mismatch")
    if digest_agent(agent) != expected_digest:
        raise ValueError("restored checkpoint digest differs from published source")
    _forbid_updates(agent)
    return agent


def _service(env: Any, parts: dict[str, float]) -> tuple[int, int, int, float]:
    """Actual post-transition native service and height, with B11 component checks."""
    native = env.env.env
    sinr, links = np.asarray(native.sinr_matrix), np.asarray(native.connections, dtype=bool)
    if sinr.shape != (N, 50) or links.shape != (N, 50):
        raise ValueError("native service roster mismatch")
    eligible = sinr >= float(native.min_sinr)
    if np.any(links & ~eligible) or np.any(links.sum(axis=0) > 1) or np.any(links.sum(axis=1) > 10):
        raise ValueError("native service/capacity invariant failed")
    e, s = int(eligible.any(axis=0).sum()), int(links.any(axis=0).sum())
    u = int((eligible.any(axis=0) & ~links.any(axis=0)).sum())
    quality = float(np.clip((sinr[links] - float(native.min_sinr)) / 30., 0., 1.).sum())
    height = float(np.asarray(native.uav_positions)[:, 2].mean())
    low, high = map(float, native.height_range)
    checks = {"coverage_reward": s / 50., "quality_reward": quality / max(s, 1),
              "energy_penalty": (height - low) / (high - low) * .1}
    if any(not np.isclose(parts[k], value, atol=1e-10, rtol=0) for k, value in checks.items()):
        raise ValueError("native service/quality/height components mismatch")
    return e, s, u, height



def route_actions(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    """Keep the adapter's native rows 0-2 and 3-5 in their original order."""
    a, b = np.asarray(first), np.asarray(second)
    if a.shape != b.shape or a.ndim != 3 or a.shape[1:] != (N, 3) or a.dtype != np.float32 or b.dtype != np.float32:
        raise ValueError("B01 full-roster action shape/dtype mismatch")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("B01 nonfinite source action")
    return np.concatenate((a[:, :3], b[:, 3:]), axis=1)

def _eval_cell(i: int, j: int, payloads: dict[int, dict], out: Path) -> dict:
    with preserve_rng():
        seed_rng(RUNTIME_SEED)
        envs = make_envs(len(WORLDS), WORLDS[0], N, HORIZON)
        agents = []
        guarded_normalizer_classes = {}
        active_t = -1
        try:
            b11._assert_native_envs(envs, N)
            rows = [list(env.env.agents) for env in envs]
            if any(row != list(env.env.env.possible_agents) or len(row) != N for row, env in zip(rows, envs)):
                raise ValueError("native ordered-agent roster mismatch")
            for side, source in (("first", i), ("second", j)):
                config = b16.make_b16_config(b20.Arm("F", SOURCE[source]["seed"]), envs,
                                             DEFAULT_SPEC.__class__(**{**vars(DEFAULT_SPEC), "eval_lanes": len(WORLDS)}), expected_n=N)
                actual_config = b16._config_record(config)
                source_config = payloads[source]["published_config"]["config"]
                differing = {k for k in set(actual_config) | set(source_config)
                             if actual_config.get(k) != source_config.get(k)}
                if differing - {"num_envs", "batch_size", "discriminator_batch_size", "high_level_batch_size", "high_level_buffer_size"}:
                    raise ValueError(f"evaluation runtime config differs from source: {differing}")
                agents.append(restore_runtime(config, payloads[source]["checkpoint"],
                                              payloads[source]["expected_digest"],
                                              out / "raw" / "logs" / f"cell_{i}{j}_{side}"))
            if agents[0] is agents[1]:
                raise ValueError("B01 requires independent policy runtimes")
            def reject_normalizer_update(*_args: Any, **_kwargs: Any) -> None:
                raise ValueError("B01 attempted a forbidden normalizer update")
            for agent in agents:
                for name in NORMALIZERS:
                    norm = getattr(agent, name, None)
                    if norm is not None:
                        cls = type(norm)
                        if cls not in guarded_normalizer_classes:
                            guarded_normalizer_classes[cls] = cls.update
                            cls.update = reject_normalizer_update
            pairs = [env.reset() for env in envs]
            states = np.stack([info["state"] for _, info in pairs])
            observations = np.stack([obs for obs, _ in pairs])
            initial_arrays = {"states": states, "observations": observations,
                              "uav_positions": np.stack([env.env.env.uav_positions for env in envs]),
                              "user_positions": np.stack([env.env.env.user_positions for env in envs])}
            initial = {name: _identity(value) for name, value in initial_arrays.items()}
            initial_per_world = [{name: _identity(value[lane]) for name, value in initial_arrays.items()}
                                 for lane in range(len(WORLDS))]
            steps, dones = np.zeros(len(WORLDS), dtype=np.int64), np.zeros(len(WORLDS), dtype=bool)
            raw_first = np.full((HORIZON, len(WORLDS), N, 3), np.nan, dtype=np.float32)
            raw_second = np.full_like(raw_first, np.nan)
            executed = np.full_like(raw_first, np.nan)
            stream = {name: np.full((HORIZON, len(WORLDS)), np.nan, dtype=np.float64)
                      for name in (*COMPONENTS, "scalar_reward", "E", "S", "U", "height")}
            inference_attempted = np.zeros((HORIZON, 2), dtype=bool)
            inference_returned = np.zeros_like(inference_attempted)
            environment_attempted = np.zeros((HORIZON, len(WORLDS)), dtype=bool)
            environment_returned = np.zeros_like(environment_attempted)
            components_validated = np.zeros_like(environment_attempted)
            terminated = np.zeros_like(environment_attempted)
            truncated = np.zeros_like(environment_attempted)
            before = [digest_agent(agent) for agent in agents]
            with torch.no_grad():
                for t in range(HORIZON):
                    active_t = t
                    actions = []
                    for side, agent in enumerate(agents):
                        inference_attempted[t, side] = True
                        raw, _, data = agent.step(states, observations, steps, dones,
                                                  deterministic=True, return_step_data=True, build_infos=False)
                        inference_returned[t, side] = True
                        (raw_first if side == 0 else raw_second)[t] = raw
                        finite((raw, data), "B01 deterministic policy output")
                        if raw.shape != (len(WORLDS), N, 3) or raw.dtype != np.float32:
                            raise ValueError("B01 policy output roster/dtype mismatch")
                        actions.append(raw)
                    joined = route_actions(*actions)
                    mapped = b03.map_training_actions(joined, "clip")
                    if mapped.shape != joined.shape or not np.array_equal(joined, route_actions(*actions)):
                        raise ValueError("action mapping changed raw route")
                    if not np.isfinite(mapped).all() or np.any(mapped < -1) or np.any(mapped > 1):
                        raise ValueError("invalid executed native actions")
                    executed[t] = mapped
                    next_pairs = []
                    for lane, env in enumerate(envs):
                        environment_attempted[t, lane] = True
                        obs, reward, term, trunc, info = env.step(mapped[lane])
                        environment_returned[t, lane] = True
                        terminated[t, lane], truncated[t, lane] = bool(term), bool(trunc)
                        stream["scalar_reward"][t, lane] = float(reward)
                        # Preserve the returned reward data before native identity checks.
                        raw_parts = info.get("reward_components", {}).get("reward_info", {})
                        for name in COMPONENTS:
                            if name in raw_parts:
                                stream[name][t, lane] = float(raw_parts[name])
                        parts = native_components(info, reward, N)
                        e, s, u, h = _service(env, parts)
                        for name, value in (("E", e), ("S", s), ("U", u), ("height", h)):
                            stream[name][t, lane] = value
                        components_validated[t, lane] = True
                        next_pairs.append((obs, info))
                        dones[lane] = bool(term or trunc)
                    states = np.stack([info["next_state"] for _, info in next_pairs])
                    observations = np.stack([obs for obs, _ in next_pairs])
                    steps += 1
                    if dones.any() and (t != HORIZON - 1 or not dones.all()):
                        raise ValueError("unexpected native terminal boundary")
            if not dones.all() or not np.all(steps == HORIZON):
                raise ValueError("incomplete native world panel")
            if (not inference_attempted.all() or not inference_returned.all() or
                not environment_attempted.all() or not environment_returned.all() or
                not components_validated.all()):
                raise ValueError("B01 complete panel has missing returned policy/environment work")
            if [digest_agent(agent) for agent in agents] != before:
                raise ValueError("runtime model/normalizer drift")
            if any(np.any(agent.rollout_buffer.env_lengths) for agent in agents):
                raise ValueError("training storage changed")
            means = {name: values.mean(axis=0) for name, values in stream.items()}
            jvalue = N * means["scalar_reward"]
            native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
            if (not np.allclose(jvalue, means["total_reward"], atol=1e-7, rtol=1e-6) or
                not np.allclose(jvalue, native_j, atol=1e-7, rtol=1e-6) or
                not np.allclose(means["S"], 50 * means["coverage_reward"], atol=1e-7, rtol=1e-6) or
                not np.allclose(means["U"], means["E"] - means["S"], atol=1e-7, rtol=1e-6)):
                raise ValueError("native aggregate identity failed")
            raw_path = out / "raw" / f"cell_{i}{j}.npz"
            np.savez_compressed(raw_path, source_i_raw_actions=raw_first, source_j_raw_actions=raw_second,
                                executed_actions=executed, inference_attempted=inference_attempted,
                                inference_returned=inference_returned,
                                environment_attempted=environment_attempted,
                                environment_returned=environment_returned,
                                components_validated=components_validated,
                                terminated=terminated, truncated=truncated, **stream)
            return {"cell": [i, j], "status": "complete", "world_seeds": WORLDS,
                    "native_agent_rows": rows, "initial_world_identity": initial,
                    "initial_world_identity_per_world": initial_per_world,
                    "per_world": {"J": jvalue.tolist(), "scalar_return": (means["scalar_reward"] * HORIZON).tolist(),
                                  **{name: value.tolist() for name, value in means.items()}},
                    "counts": {"team_steps": int(environment_returned.sum()),
                               "environment_step_attempts": int(environment_attempted.sum()),
                               "executed_uav_action_rows": int(environment_returned.sum()) * N,
                               "inference_step_attempts": int(inference_attempted.sum()),
                               "inferred_policy_action_rows": int(inference_returned.sum()) * len(WORLDS) * N,
                               "policy_step_calls": int(inference_returned.sum()),
                               "optimizer_updates": 0, "storage_calls": 0},
                    "runtime_digest_before": before, "runtime_digest_after": [digest_agent(agent) for agent in agents],
                    "raw_artifact": {"path": raw_path.relative_to(out).as_posix(), "sha256": sha256(raw_path),
                                     "bytes": raw_path.stat().st_size}}
        except Exception as exc:
            failure_counts = {"inference_step_attempts": 0, "inference_step_returns": 0,
                              "inference_action_rows_requested": 0, "inferred_policy_action_rows_returned": 0,
                              "environment_step_attempts": 0, "environment_step_returns": 0,
                              "environment_outcomes_unknown": 0, "components_validated": 0,
                              "executed_uav_action_rows_confirmed": 0}
            failure = {"cell": [i, j], "status": "failed", "failure": f"{type(exc).__name__}: {exc}",
                       "active_step": active_t if active_t >= 0 else None, "counts": failure_counts}
            if "stream" in locals():
                failure_counts.update(
                    inference_step_attempts=int(inference_attempted.sum()),
                    inference_step_returns=int(inference_returned.sum()),
                    inference_action_rows_requested=int(inference_attempted.sum()) * len(WORLDS) * N,
                    inferred_policy_action_rows_returned=int(inference_returned.sum()) * len(WORLDS) * N,
                    environment_step_attempts=int(environment_attempted.sum()),
                    environment_step_returns=int(environment_returned.sum()),
                    environment_outcomes_unknown=int((environment_attempted & ~environment_returned).sum()),
                    components_validated=int(components_validated.sum()),
                    executed_uav_action_rows_confirmed=int(environment_returned.sum()) * N,
                )
            if active_t >= 0 and "stream" in locals():
                length = active_t + 1
                partial = out / "raw" / f"cell_{i}{j}_partial.npz"
                np.savez_compressed(partial, source_i_raw_actions=raw_first[:length],
                                    source_j_raw_actions=raw_second[:length],
                                    executed_actions=executed[:length],
                                    inference_attempted=inference_attempted[:length],
                                    inference_returned=inference_returned[:length],
                                    environment_attempted=environment_attempted[:length],
                                    environment_returned=environment_returned[:length],
                                    components_validated=components_validated[:length],
                                    terminated=terminated[:length], truncated=truncated[:length],
                                    **{key: value[:length] for key, value in stream.items()})
                failure["raw_artifact"] = {"path": partial.relative_to(out).as_posix(),
                                           "sha256": sha256(partial), "bytes": partial.stat().st_size}
            write_json(out / f"cell_{i}{j}.json", failure)
            raise
        finally:
            for cls, original in guarded_normalizer_classes.items():
                cls.update = original
            for env in envs:
                env.close()


def run_study(out: Path, launch_sha: str, admission: dict, checkpoint_paths: dict[int, Path],
              *, seed: int, command_start: float) -> dict:
    if seed != WORLDS[0] or launch_sha != admission["sha"]:
        raise ValueError("B01 seed/launch admission mismatch")
    out = Path(out).resolve()
    bound_output = admission.get("output_root")
    if bound_output is not None and out != Path(bound_output).resolve():
        raise ValueError("B01 output path disagrees with admission")
    if not out.is_dir():
        raise ValueError("B01 requires the launcher-created output directory")
    scientific_prefixes = ("config.json", "progress.json", "summary.json", "cell_")
    collisions = [entry.name for entry in out.iterdir()
                  if entry.name == "raw" or entry.name.startswith(scientific_prefixes)]
    if collisions:
        raise ValueError(f"B01 scientific output already exists: {sorted(collisions)}")
    torch.set_num_threads(4)
    payloads, dependencies = validate_sources(checkpoint_paths)
    (out / "raw").mkdir()
    config = {"object": "controller_composition_b01", "launch_sha": launch_sha,
              "admission": jsonable(admission), "world_seeds": WORLDS, "horizon": HORIZON,
              "roster": N, "source_roles": {"first": [0, 1, 2], "second": [3, 4, 5]},
              "cell_order": CELL_ORDER, "runtime_seed": RUNTIME_SEED, "analysis_seed": ANALYSIS_SEED,
              "bootstrap_draws": BOOTSTRAP_DRAWS, "torch_threads": 4, "device": "cpu", "dtype": "float32",
              "source_commit": SOURCE_COMMIT, "source_bindings": SOURCE,
              "checkpoints": {str(k): {"path": str(checkpoint_paths[k]), "sha256": SOURCE[k]["checkpoint_sha256"]}
                              for k in SOURCE}, "source_dependencies_sha256": dependencies}
    write_json(out / "config.json", config)
    cells = []
    progress = {"status": "running", "completed_cells": [], "active_cell": None}
    write_json(out / "progress.json", progress)
    try:
        first_initial = None
        first_initial_per_world = None
        for i, j in CELL_ORDER:
            progress["active_cell"] = [i, j]
            write_json(out / "progress.json", progress)
            row = _eval_cell(i, j, payloads, out)
            if first_initial is None:
                first_initial = row["initial_world_identity"]
                first_initial_per_world = row["initial_world_identity_per_world"]
            elif (row["initial_world_identity"] != first_initial or
                  row["initial_world_identity_per_world"] != first_initial_per_world):
                raise ValueError("initial world bytes differ across cells")
            cells.append(row)
            write_json(out / f"cell_{i}{j}.json", row)
            progress["completed_cells"].append([i, j])
            write_json(out / "progress.json", progress)
        progress["active_cell"] = None
        write_json(out / "progress.json", progress)
        def panel(name: str) -> np.ndarray:
            return np.stack([np.array([[cells[3 * i + j]["per_world"][name][world]
                                        for j in range(3)] for i in range(3)])
                             for world in range(len(WORLDS))])
        analysis = reduce_panel(panel("J"), panel("S"), draws=BOOTSTRAP_DRAWS, seed=ANALYSIS_SEED)
        ru = resource.getrusage(resource.RUSAGE_SELF)
        raw_artifacts = [{"path": path.relative_to(out).as_posix(), "sha256": sha256(path),
                          "bytes": path.stat().st_size}
                         for path in sorted((out / "raw").rglob("*")) if path.is_file()]
        telemetry = {"wall_seconds": time.perf_counter() - command_start,
                     "process_cpu_seconds": ru.ru_utime + ru.ru_stime,
                     "peak_process_rss_kib": ru.ru_maxrss,
                     "scratch_raw_bytes": sum(item["bytes"] for item in raw_artifacts)}
        summary = {"object": config["object"], "status": "complete", "launch_sha": launch_sha,
                   "world_seeds": WORLDS, "source_commit": SOURCE_COMMIT,
                   "sources": config["checkpoints"], "source_bindings": SOURCE,
                   "source_dependencies_sha256": dependencies, "config_sha256": sha256(out / "config.json"),
                   "cells": cells, "analysis": analysis,
                   "counts": {"fits": 0, "optimizer_updates": 0, "storage_calls": 0,
                              "team_steps": sum(row["counts"]["team_steps"] for row in cells),
                              "executed_uav_action_rows": sum(row["counts"]["executed_uav_action_rows"] for row in cells),
                              "inferred_policy_action_rows": sum(row["counts"]["inferred_policy_action_rows"] for row in cells),
                              "world_episodes": len(WORLDS) * len(CELL_ORDER)},
                   "telemetry": telemetry,
                   "artifacts": raw_artifacts}
        write_json(out / "summary.json", summary)
        progress.update(status="complete", active_cell=None, summary_sha256=sha256(out / "summary.json"))
        write_json(out / "progress.json", progress)
        return summary
    except Exception as exc:
        progress.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        active = progress.get("active_cell")
        if active is not None:
            cell_record = out / f"cell_{active[0]}{active[1]}.json"
            if cell_record.exists():
                recorded = json.loads(cell_record.read_text())
                if recorded.get("status") == "failed":
                    progress["failed_cell"] = recorded
        write_json(out / "progress.json", progress)
        raise
