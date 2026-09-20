"""Paired ordinary-G learning with initial latent scales 1.0 and 0.5."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
import traceback

import numpy as np
import torch

from ..uav_motion_prefix_b01.environment import SyntheticAdapter, make_real
from ..uav_motion_prefix_b01.learner import collect_episode, optimizer_for, update
from ..uav_motion_prefix_b01.policy import arm_copy, exposure, generator, snapshot, templates
from ..uav_motion_prefix_b01.study import new_counts, write_summary


OBJECT = "UCOPE_GAUSSIAN_SCALE_INITIALIZATION_B06"
NOTEBOOK = "docs/research/candidates/ucope/NOTES.md"
NOTEBOOK_SECTION = "B06 prepared design: initial Gaussian scale and attained ordinary control"
EXECUTION_NODE = "local_linux"
ALLOWED_MASTERS = (8941, 8942, 8943)
ARMS = ("G1", "Ghalf")
MODES = ("G1_sampled", "Ghalf_sampled", "G1_mean", "Ghalf_mean")
CONTRASTS = (
    ("Ghalf_mean_minus_G1_mean", "Ghalf_mean", "G1_mean"),
    ("Ghalf_sampled_minus_G1_sampled", "Ghalf_sampled", "G1_sampled"),
    ("Ghalf_mean_minus_Ghalf_sampled", "Ghalf_mean", "Ghalf_sampled"),
    ("G1_mean_minus_G1_sampled", "G1_mean", "G1_sampled"),
)
REPO = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Config:
    master: int
    horizon: int = 256
    train_episodes: int = 2048
    eval_episodes: int = 64
    chunk: int = 32
    watchdog_seconds: float = 6000.0
    fixture: bool = False

    @classmethod
    def engineering(cls):
        return cls(
            master=9941,
            horizon=8,
            train_episodes=4,
            eval_episodes=3,
            chunk=4,
            watchdog_seconds=180.0,
            fixture=True,
        )


def require_config(config):
    if config.fixture:
        if config != Config.engineering():
            raise ValueError("only the fixed B06 engineering fixture is supported off path")
        return
    if config.master not in ALLOWED_MASTERS:
        raise ValueError("master must be one of the three prepared B06 pairs")
    if config != Config(master=config.master):
        raise ValueError("B06 training and evaluation exposure is fixed")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _file_identity(path):
    path = Path(path)
    if not path.is_file():
        return {"path": str(path), "present": False}
    data = path.read_bytes()
    return {
        "path": str(path),
        "present": True,
        "bytes": len(data),
        "sha256": _sha256(data),
    }


def _write_json(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def _tensor_digest(tensor):
    tensor = tensor.detach().cpu().contiguous()
    return _sha256(tensor.numpy().tobytes())


def _model_digest(actor, critic, exclude_log_std=False):
    digest = hashlib.sha256()
    items = [(f"actor.{name}", value) for name, value in actor.state_dict().items()]
    items += [(f"critic.{name}", value) for name, value in critic.state_dict().items()]
    for name, value in sorted(items):
        if exclude_log_std and name == "actor.log_std":
            continue
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(tensor.dtype).encode("ascii") + b"\0")
        digest.update(json.dumps(list(tensor.shape)).encode("ascii") + b"\0")
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _generator_digest(rng):
    return _tensor_digest(rng.get_state())


def build_fit_states(master):
    """Construct independent paired fits; only Ghalf's initial log_std differs."""
    common = templates(master)
    models = {
        arm: arm_copy(common, False)
        for arm in ARMS
    }
    with torch.no_grad():
        models["Ghalf"][0].log_std.fill_(math.log(0.5))
    common_digests = {
        arm: _model_digest(*models[arm], exclude_log_std=True)
        for arm in ARMS
    }
    if len(set(common_digests.values())) != 1:
        raise RuntimeError("paired B06 model bytes differ outside log_std")

    base = 100000 * master
    states = {}
    for arm in ARMS:
        actor, critic = models[arm]
        optimizer = optimizer_for(actor, critic)
        velocity_rng = generator(base + 21)
        duration_rng = generator(base + 22)
        optimizer_parameters = {
            id(parameter)
            for group in optimizer.param_groups
            for parameter in group["params"]
        }
        if not actor.log_std.requires_grad or id(actor.log_std) not in optimizer_parameters:
            raise RuntimeError(f"{arm} log_std is not trainable through its optimizer")
        states[arm] = {
            "actor": actor,
            "critic": critic,
            "optimizer": optimizer,
            "velocity_rng": velocity_rng,
            "duration_rng": duration_rng,
            "initial_snapshot": snapshot(actor, critic),
            "initial_model_sha256": _model_digest(actor, critic),
            "common_initial_sha256": common_digests[arm],
            "initial_log_std": actor.log_std.detach().tolist(),
            "initial_scale": actor.log_std.detach().clamp(-5, 2).exp().tolist(),
            "velocity_rng_initial_sha256": _generator_digest(velocity_rng),
            "duration_rng_initial_sha256": _generator_digest(duration_rng),
            "episode_start_scale_means": [],
        }
    if states["G1"]["actor"] is states["Ghalf"]["actor"]:
        raise RuntimeError("paired B06 actors share an instance")
    if states["G1"]["optimizer"] is states["Ghalf"]["optimizer"]:
        raise RuntimeError("paired B06 optimizers share an instance")
    if states["G1"]["velocity_rng"] is states["Ghalf"]["velocity_rng"]:
        raise RuntimeError("paired B06 generators share an instance")
    return states


def _scale_record(state, arm, rollout, when):
    log_std = state["actor"].log_std.detach()
    scale = log_std.clamp(-5, 2).exp()
    return {
        "arm": arm,
        "rollout": rollout,
        "when": when,
        "training_episodes_seen": 2 * rollout + (2 if when == "after_update" else 0),
        "log_std": log_std.tolist(),
        "latent_scale": scale.tolist(),
        "arithmetic_mean_latent_scale": float(scale.mean()),
    }


def _early_scale_summary(values):
    selected = list(values[:256])
    return {
        "definition": (
            "arithmetic mean of the three latent Gaussian scales at each episode start, "
            "averaged over the first 256 training episodes"
        ),
        "target_episode_starts": 256,
        "observed_episode_starts": len(selected),
        "complete": len(selected) == 256,
        "mean": statistics.mean(selected) if selected else None,
        "values": selected,
    }


def _empty_eval_arrays(config):
    e, m, h, n, d = config.eval_episodes, len(MODES), config.horizon, 5, 3
    return {
        "mode_names": np.asarray(MODES, dtype="U16"),
        "completed": np.zeros((e, m), dtype=bool),
        "rewards": np.full((e, m, h), np.nan, dtype=np.float32),
        "latent_u": np.full((e, m, h, n, d), np.nan, dtype=np.float32),
        "actions": np.full((e, m, h, n, d), np.nan, dtype=np.float32),
        "velocity_mask": np.zeros((e, m, h, n), dtype=bool),
        "duration_mask": np.zeros((e, m, h, n), dtype=bool),
        "phase": np.full((e, m, h, n), np.nan, dtype=np.float32),
    }


def final_panel(rows, expected, invocation_complete):
    values = {
        mode: {
            row["episode"]: row["J"]
            for row in rows
            if row["mode"] == mode and row["phase"] == "eval"
        }
        for mode in MODES
    }
    full = {
        mode: sorted(items) == list(range(expected))
        and all(math.isfinite(value) for value in items.values())
        for mode, items in values.items()
    }
    panel = {
        "selected_contrast": "Ghalf_mean_minus_G1_mean",
        "returns": {
            mode: [items[index] for index in sorted(items)]
            for mode, items in values.items()
        },
        "episode_ids": {mode: sorted(items) for mode, items in values.items()},
        "arm_means": {
            mode: statistics.mean(items.values()) if items else None
            for mode, items in values.items()
        },
        "all_panels_complete": all(full.values()),
    }
    for name, first, second in CONTRASTS:
        ids = sorted(values[first].keys() & values[second].keys())
        differences = [values[first][index] - values[second][index] for index in ids]
        panel[name] = {
            "episode_ids": ids,
            "differences": differences,
            "mean": statistics.mean(differences) if differences else None,
            "conditional_se": (
                statistics.stdev(differences) / math.sqrt(len(differences))
                if len(differences) > 1 else None
            ),
            "signs": [1 if value > 0 else -1 if value < 0 else 0 for value in differences],
            "favorable": sum(value > 0 for value in differences),
            "adverse": sum(value < 0 for value in differences),
            "tied": sum(value == 0 for value in differences),
            "panel_complete": full[first] and full[second],
            "complete": bool(invocation_complete and full[first] and full[second]),
        }
    panel["primary"] = panel["Ghalf_mean_minus_G1_mean"]
    panel["complete"] = bool(invocation_complete and panel["all_panels_complete"])
    panel["reading_scope"] = (
        "Paired worlds from one trained pair; conditional world-panel SEs are not "
        "training-population precision, equivalence, or a historical pooled estimate."
    )
    return panel


def _telemetry(start, cpu_start):
    peak_rss_kib = None
    unmeasured = ["complete process exit wall"]
    try:
        import resource
        peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except ImportError:
        unmeasured.append("single-process peak RSS")
    return {
        "wall_seconds": time.monotonic() - start,
        "wall_scope": "runner main entry through B06 publication accounting",
        "process_cpu_seconds": time.process_time() - cpu_start,
        "process_cpu_scope": "study entry through B06 publication accounting",
        "peak_rss_kib": peak_rss_kib,
        "peak_rss_scope": "single process ru_maxrss" if peak_rss_kib is not None else "unavailable",
        "complete_process_exit_wall": None,
        "external_scope": "the native launch manifest is authoritative for actual-node and complete-process telemetry",
        "resources_unmeasured": unmeasured,
    }


def run(config, out, admission, start=None, factory=None):
    """Run one paired learning study; the factory override is fixture-only."""
    require_config(config)
    if not config.fixture and factory is not None:
        raise ValueError("production B06 environment cannot be overridden")
    admitted_sha = admission.get("sha")
    if not isinstance(admitted_sha, str) or not admitted_sha:
        raise ValueError("B06 requires an admitted source SHA")
    start = time.monotonic() if start is None else start
    cpu_start = time.process_time()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "config.json", asdict(config))
    _write_json(out / "admission.json", dict(admission))
    source = {
        "object": OBJECT,
        "launch_sha": admitted_sha,
        "runner": _file_identity(REPO / "scripts/run_ucope_gaussian_scale_initialization_b06.py"),
        "study": _file_identity(Path(__file__)),
        "shared_collector": _file_identity(REPO / "experiments/candidates/ucope/uav_motion_prefix_b01/learner.py"),
        "shared_policy": _file_identity(REPO / "experiments/candidates/ucope/uav_motion_prefix_b01/policy.py"),
    }
    _write_json(out / "source.json", source)

    arrays = _empty_eval_arrays(config)
    train_rows, eval_rows, update_rows, scale_rows = [], [], [], []
    states = {}
    arm_records = {}
    limits = []
    summary = {
        "object": OBJECT,
        "notebook": NOTEBOOK,
        "notebook_section": NOTEBOOK_SECTION,
        "configuration": asdict(config),
        "master": config.master,
        "selected_masters": list(ALLOWED_MASTERS),
        "launch_sha": admitted_sha,
        "admission": dict(admission),
        "declared_execution_node": EXECUTION_NODE,
        "device": "cpu",
        "dtype": "float32",
        "torch_threads": [torch.get_num_threads(), torch.get_num_interop_threads()],
        "mode": "ENGINEERING_FIXTURE" if config.fixture else "PAIRED_ORDINARY_G_LEARNING",
        "status": "INCOMPLETE",
        "arms": arm_records,
        "limits": limits,
        "policy_definition": {
            "G1": "ordinary G with trainable log_std initialized to log(1.0)",
            "Ghalf": "ordinary G with trainable log_std initialized to log(0.5)",
            "shared": (
                "fresh command each tick, phase zero, no duration head, agent-compound PPO, "
                "entropy coefficient zero, raw gamma-one returns, no value normalization"
            ),
            "primary": "Ghalf_mean minus G1_mean on paired final worlds",
        },
        "prepared_execution_exposure": {
            "fits_if_authorized": 6,
            "train_episodes": 12288,
            "train_team_steps": 3145728,
            "optimizer_calls": 24576,
            "eval_episodes": 768,
            "eval_team_steps": 196608,
            "total_team_steps": 3342336,
            "preparation_boundary": (
                "This implementation does not grant execution; any launch requires a "
                "separate owner amendment and admission."
            ),
        },
    }
    base = 100000 * config.master
    summary["rng"] = {
        "base": base,
        "common_initialization": base + 11,
        "train_world_start": base + 10000,
        "training_velocity_generator": base + 21,
        "training_unused_duration_generator": base + 22,
        "eval_world_start": base + 30000,
        "eval_sampled_velocity_per_episode": "base+80000+episode",
        "eval_unused_duration_per_episode": "base+85000+episode",
    }
    global_rng_before = torch.random.get_rng_state().clone()

    def check():
        if time.monotonic() - start > config.watchdog_seconds:
            raise TimeoutError(
                f"B06 {config.watchdog_seconds:g}-second watchdog expired; preserve partial work"
            )

    factory = factory or (
        (lambda seed: SyntheticAdapter(seed, config.horizon))
        if config.fixture else make_real
    )
    train_path = out / "train_episodes.jsonl"
    eval_path = out / "eval_episodes.jsonl"
    updates_path = out / "updates.jsonl"
    scales_path = out / "scales.jsonl"
    with (
        train_path.open("w", encoding="utf-8") as train_file,
        eval_path.open("w", encoding="utf-8") as eval_file,
        updates_path.open("w", encoding="utf-8") as updates_file,
        scales_path.open("w", encoding="utf-8") as scales_file,
    ):
        def emit_train(row):
            train_rows.append(row)
            train_file.write(json.dumps(row, allow_nan=False) + "\n")
            train_file.flush()

        def emit_eval(row):
            eval_rows.append(row)
            eval_file.write(json.dumps(row, allow_nan=False) + "\n")
            eval_file.flush()

        try:
            check()
            states = build_fit_states(config.master)
            summary["paired_common_initial_sha256"] = states["G1"]["common_initial_sha256"]
            summary["paired_initial_rng"] = {
                "velocity_equal": (
                    states["G1"]["velocity_rng_initial_sha256"]
                    == states["Ghalf"]["velocity_rng_initial_sha256"]
                ),
                "duration_equal": (
                    states["G1"]["duration_rng_initial_sha256"]
                    == states["Ghalf"]["duration_rng_initial_sha256"]
                ),
                "objects_independent": True,
            }
            for arm in ARMS:
                state = states[arm]
                actor, critic = state["actor"], state["critic"]
                counts = new_counts(renewal=True, short=True)
                record = {
                    "fit_started": True,
                    "train_complete": False,
                    "initial_model_sha256": state["initial_model_sha256"],
                    "common_initial_sha256": state["common_initial_sha256"],
                    "initial_log_std": state["initial_log_std"],
                    "initial_scale": state["initial_scale"],
                    "counts": counts,
                }
                arm_records[arm] = record
                env = None
                try:
                    check()
                    env = factory(base + 10000)
                    counts["constructors"] += 1
                    counts["constructor_resets"] += 1
                    for rollout in range(config.train_episodes // 2):
                        before = _scale_record(state, arm, rollout, "before_collection")
                        scale_rows.append(before)
                        scales_file.write(json.dumps(before, allow_nan=False) + "\n")
                        scales_file.flush()
                        episodes = []
                        for offset in range(2):
                            episode = 2 * rollout + offset
                            resets_before = counts["explicit_resets"]
                            try:
                                collected = collect_episode(
                                    env, actor, critic, config.horizon,
                                    base + 10000 + episode,
                                    state["velocity_rng"], state["duration_rng"],
                                    {"master": config.master, "arm": arm,
                                     "phase": "train", "episode": episode},
                                    check, counts, emit_train, lambda _row: None, limits,
                                    real=not config.fixture,
                                    ratio_grouping="agent_compound",
                                    value_moments=None,
                                    renewal=True,
                                    duration_support=(1, 2),
                                )
                            finally:
                                if counts["explicit_resets"] > resets_before:
                                    state["episode_start_scale_means"].append(
                                        before["arithmetic_mean_latent_scale"]
                                    )
                            episodes.append(collected)
                        losses = update(
                            actor, critic, state["optimizer"], episodes, config.chunk,
                            check, counts, ratio_grouping="agent_compound",
                            entropy_coef=0.0, value_moments=None,
                        )
                        counts["rollouts"] += 1
                        update_row = {"arm": arm, "rollout": rollout, "epochs": losses}
                        update_rows.append(update_row)
                        updates_file.write(json.dumps(update_row, allow_nan=False) + "\n")
                        updates_file.flush()
                        after = _scale_record(state, arm, rollout, "after_update")
                        scale_rows.append(after)
                        scales_file.write(json.dumps(after, allow_nan=False) + "\n")
                        scales_file.flush()
                    record["train_complete"] = True
                    checkpoint = out / f"{arm}_final.pt"
                    torch.save(
                        {
                            "object": OBJECT,
                            "actor": actor.state_dict(),
                            "critic": critic.state_dict(),
                            "arm": arm,
                            "seed": config.master,
                            "train_episodes": config.train_episodes,
                            "optimizer_steps": counts["optimizer_steps"],
                            "initial_log_std": state["initial_log_std"],
                        },
                        checkpoint,
                    )
                    record["checkpoint"] = _file_identity(checkpoint)
                finally:
                    record["movement"] = exposure(state["initial_snapshot"], actor, critic)
                    record["final_log_std"] = actor.log_std.detach().tolist()
                    record["final_scale"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
                    record["first_256_episode_start_scale"] = _early_scale_summary(
                        state["episode_start_scale_means"]
                    )
                    record["velocity_rng_final_sha256"] = _generator_digest(state["velocity_rng"])
                    record["duration_rng_final_sha256"] = _generator_digest(state["duration_rng"])
                    record["duration_rng_unchanged"] = (
                        record["duration_rng_final_sha256"]
                        == state["duration_rng_initial_sha256"]
                    )
                    if env is not None and hasattr(env, "close"):
                        env.close()

            before_evaluation = {
                arm: snapshot(states[arm]["actor"], states[arm]["critic"])
                for arm in ARMS
            }
            training_rng_before_evaluation = {
                arm: (
                    _generator_digest(states[arm]["velocity_rng"]),
                    _generator_digest(states[arm]["duration_rng"]),
                )
                for arm in ARMS
            }
            eval_counts = {mode: new_counts(renewal=True, short=True) for mode in MODES}
            # Counts mutate inside collection and must remain published if construction,
            # collection, or environment closure fails after native effects begin.
            summary["evaluation_counts"] = eval_counts
            eval_environments = {}
            try:
                for mode in MODES:
                    eval_environments[mode] = factory(base + 30000)
                    eval_counts[mode]["constructors"] += 1
                    eval_counts[mode]["constructor_resets"] += 1
                for episode in range(config.eval_episodes):
                    for mode_index, mode in enumerate(MODES):
                        arm = "Ghalf" if mode.startswith("Ghalf") else "G1"
                        velocity_mode = "mean" if mode.endswith("mean") else "sampled"
                        velocity_rng = generator(base + 80000 + episode)
                        duration_rng = generator(base + 85000 + episode)
                        velocity_before = _generator_digest(velocity_rng)
                        duration_before = _generator_digest(duration_rng)
                        emitted = []
                        rollout = collect_episode(
                            eval_environments[mode], states[arm]["actor"], states[arm]["critic"],
                            config.horizon, base + 30000 + episode,
                            velocity_rng, duration_rng,
                            {"master": config.master, "arm": arm, "mode": mode,
                             "phase": "eval", "episode": episode},
                            check, eval_counts[mode], emitted.append, lambda _row: None, limits,
                            real=not config.fixture,
                            ratio_grouping="agent_compound",
                            value_moments=None,
                            renewal=True,
                            duration_support=(1, 2),
                            velocity_mode=velocity_mode,
                        )
                        if len(emitted) != 1:
                            raise RuntimeError("ordinary evaluator emitted an unexpected row count")
                        row = emitted[0]
                        row["velocity_rng_changed"] = (
                            _generator_digest(velocity_rng) != velocity_before
                        )
                        row["duration_rng_changed"] = (
                            _generator_digest(duration_rng) != duration_before
                        )
                        if velocity_mode == "mean" and row["velocity_rng_changed"]:
                            raise RuntimeError("mean deployment consumed Gaussian innovations")
                        if row["duration_rng_changed"]:
                            raise RuntimeError("ordinary G consumed the unused duration stream")
                        emit_eval(row)
                        arrays["rewards"][episode, mode_index] = rollout["reward"].numpy()
                        arrays["latent_u"][episode, mode_index] = rollout["u"].numpy()
                        arrays["actions"][episode, mode_index] = rollout["u"].tanh().numpy()
                        arrays["velocity_mask"][episode, mode_index] = rollout["velocity_mask"].numpy()
                        arrays["duration_mask"][episode, mode_index] = rollout["duration_mask"].numpy()
                        arrays["phase"][episode, mode_index] = rollout["obs"][..., -1].numpy()
                        arrays["completed"][episode, mode_index] = True
            finally:
                for env in eval_environments.values():
                    if hasattr(env, "close"):
                        env.close()
            for arm in ARMS:
                movement = exposure(
                    before_evaluation[arm], states[arm]["actor"], states[arm]["critic"]
                )
                after_rng = (
                    _generator_digest(states[arm]["velocity_rng"]),
                    _generator_digest(states[arm]["duration_rng"]),
                )
                arm_records[arm]["evaluation_immutability"] = {
                    "parameter_exposure": movement,
                    "optimizer_steps": 0,
                    "training_generators_unchanged": after_rng == training_rng_before_evaluation[arm],
                }
                if movement["total"]["displacement"] != 0:
                    raise RuntimeError("evaluation changed trained parameters")
            summary["status"] = "COMPLETE"
        except Exception as error:
            traceback.print_exc()
            summary["error"] = {"type": type(error).__name__, "message": str(error)}

    invocation_complete = summary["status"] == "COMPLETE"
    summary["panel"] = final_panel(eval_rows, config.eval_episodes, invocation_complete)
    summary["fit_accounting"] = {
        "allocated_fit_arms": list(ARMS),
        "allocated_fits_this_invocation": 2,
        "allocated_fits_complete_batch": 6,
        "started_fits": sum(record.get("fit_started", False) for record in arm_records.values()),
        "completed_fits": sum(record.get("train_complete", False) for record in arm_records.values()),
        "qualification": (
            "This implementation was prepared without execution authority. If a later owner "
            "amendment and admission authorize launch, every started arm counts even after failure."
        ),
    }
    train_keys = {
        key for record in arm_records.values() for key in record.get("counts", {})
    }
    train_counts = {
        key: sum(record.get("counts", {}).get(key, 0) for record in arm_records.values())
        for key in sorted(train_keys)
    }
    evaluation_counts = summary.get("evaluation_counts", {})
    eval_steps = sum(item.get("eval_team_steps", 0) for item in evaluation_counts.values())
    eval_episodes = sum(item.get("eval_episodes", 0) for item in evaluation_counts.values())
    summary["counts"] = {
        **train_counts,
        "evaluation_optimizer_steps": sum(
            item.get("optimizer_steps", 0) for item in evaluation_counts.values()
        ),
        "final_deployment_eval_episodes": eval_episodes,
        "final_deployment_eval_team_steps": eval_steps,
        "all_team_steps": train_counts.get("train_team_steps", 0) + eval_steps,
    }
    summary["rng_isolation"] = {
        "global_torch_rng_unchanged": bool(
            torch.equal(global_rng_before, torch.random.get_rng_state())
        ),
        "training_velocity_final_states_equal": bool(
            states
            and _generator_digest(states["G1"]["velocity_rng"])
            == _generator_digest(states["Ghalf"]["velocity_rng"])
        ),
        "training_duration_final_states_equal": bool(
            states
            and _generator_digest(states["G1"]["duration_rng"])
            == _generator_digest(states["Ghalf"]["duration_rng"])
        ),
    }
    summary["telemetry"] = _telemetry(start, cpu_start)
    summary["resource_note"] = (
        "Telemetry scopes are explicit; unavailable complete-process telemetry limits only resource claims."
    )
    np.savez_compressed(out / "evaluation_primitives.npz", **arrays)
    summary["artifacts"] = {
        name: _file_identity(out / name)
        for name in (
            "config.json", "source.json", "admission.json", "train_episodes.jsonl",
            "eval_episodes.jsonl", "updates.jsonl", "scales.jsonl",
            "evaluation_primitives.npz", "G1_final.pt", "Ghalf_final.pt",
        )
    }
    write_summary(out / "summary.json", summary)
    return summary
