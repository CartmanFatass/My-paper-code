"""Fixed B/G/H study using the inherited reactive and ordinary learners."""

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import statistics
import time
import traceback

import torch

from ..reactive_renewal_b01 import reactive
from ..uav_motion_prefix_b01.study import difference_stats, new_counts, write_summary
from ..reactive_rate_b03.scalar import ScalarGate, scalar_actor


OBJECT = "UCOPE_SCALAR_FEEDBACK_B04"
NOTEBOOK = "docs/research/candidates/ucope/NOTES.md"
NOTEBOOK_SECTION = "2026-09-19 — owner continuation and selected B04: scalar renewal versus ordinary feedback"
EXECUTION_NODE = "local_linux"
ALLOWED_MASTERS = (8931, 8932, 8933)
LEARNED_ARMS = ("B", "G")
LABELS = ("B", "G", "H")


@dataclass
class Config:
    seed: int
    horizon: int = 256
    train_episodes: int = 2048
    eval_episodes: int = 64
    chunk: int = 32
    watchdog_seconds: float = 6000
    fixture: bool = False

    @classmethod
    def engineering(cls):
        return cls(
            seed=9931,
            horizon=8,
            train_episodes=4,
            eval_episodes=3,
            chunk=8,
            watchdog_seconds=180,
            fixture=True,
        )


def require_config(config):
    if config.fixture:
        if config != Config.engineering():
            raise ValueError("only the fixed engineering fixture is supported off path")
        return
    if config.seed not in ALLOWED_MASTERS:
        raise ValueError("master must be one of the three prospectively selected B04 blocks")
    expected = Config(seed=config.seed)
    if config != expected:
        raise ValueError("B04 scientific exposure is fixed")


def make_arm(common, arm, base):
    from ..uav_motion_prefix_b01.policy import arm_copy

    if arm == "B":
        return scalar_actor(common)
    if arm == "G":
        return arm_copy(common, False)
    raise ValueError(arm)


def _parameter_groups(actor, critic):
    common = [
        parameter
        for name, parameter in actor.named_parameters()
        if not name.startswith("duration.")
    ]
    groups = {
        "common_actor": common,
        "critic": list(critic.parameters()),
    }
    if actor.duration is not None:
        groups["duration"] = list(actor.duration.parameters())
        if isinstance(actor.duration, ScalarGate):
            groups["duration_scalar"] = list(actor.duration.parameters())
    groups["total"] = list(actor.parameters()) + list(critic.parameters())
    return groups


def snapshot(actor, critic):
    return {
        name: torch.cat([parameter.detach().flatten() for parameter in group]).clone()
        for name, group in _parameter_groups(actor, critic).items()
    }


def exposure(initial, actor, critic):
    final = snapshot(actor, critic)
    result = {}
    for name, start in initial.items():
        end = final[name]
        initial_norm = float(start.norm())
        displacement = float((end - start).norm())
        result[name] = {
            "parameters": start.numel(),
            "initial_norm": initial_norm,
            "final_norm": float(end.norm()),
            "displacement": displacement,
            "relative_displacement": (
                None if initial_norm == 0 else displacement / initial_norm
            ),
        }
    return result


def final_panel(rows, expected, invocation_complete):
    values = {
        arm: {
            row["episode"]: row["J"]
            for row in rows
            if row["arm"] == arm and row["phase"] == "eval"
        }
        for arm in LABELS
    }
    full = {
        arm: sorted(episodes) == list(range(expected))
        for arm, episodes in values.items()
    }
    result = {
        "arm_means": {
            arm: statistics.mean(episodes.values()) if episodes else None
            for arm, episodes in values.items()
        },
        "returns": {
            arm: [episodes[index] for index in sorted(episodes)]
            for arm, episodes in values.items()
        },
        "all_panels_complete": all(full.values()),
        "selected_contrast": "B_minus_G",
    }
    for first, second in (("B", "G"), ("B", "H"), ("G", "H")):
        ids = sorted(values[first].keys() & values[second].keys())
        differences = [values[first][index] - values[second][index] for index in ids]
        item = difference_stats(differences)
        item.update(
            episode_ids=ids,
            panel_complete=full[first] and full[second],
            complete=bool(invocation_complete and full[first] and full[second]),
            favorable=sum(value > 0 for value in differences),
            adverse=sum(value < 0 for value in differences),
            tied=sum(value == 0 for value in differences),
        )
        result[f"{first}_minus_{second}"] = item
    result["complete"] = bool(invocation_complete and result["all_panels_complete"])
    result["primary"] = result["B_minus_G"]
    result["interpretation"] = (
        "Exploratory whole-package contrasts only. G draws fresh innovations each tick, "
        "while its recurrent action means still depend on current observations and history; "
        "the panel does not identify a renewal mechanism and carries no significance, "
        "equivalence or categorical practical-importance label."
    )
    return result


def _gate_activity(counts):
    return {
        key: int(counts.get(key, 0))
        for key in (
            "train_gate_decisions",
            "train_keep_decisions",
            "train_end_decisions",
            "train_final_gate_credit_decisions",
            "eval_gate_decisions",
            "eval_keep_decisions",
            "eval_end_decisions",
            "eval_final_gate_credit_decisions",
        )
    }


def _endpoint_gate(arm, actor):
    if arm == "B":
        return {
            "raw_logits": actor.duration.logits.detach().tolist(),
            "probabilities": actor.duration.logits.detach().softmax(-1).tolist(),
            "input_independent": True,
        }
    if arm == "G" and actor.duration is None:
        return {
            "present": False,
            "parameters": 0,
            "raw_logits": None,
            "probabilities": None,
            "qualification": "Ordinary G has no duration head or gate probabilities.",
        }
    raise ValueError(f"unexpected gate state for arm {arm}")


def _fit_accounting(summary):
    per_arm = {}
    for arm in LEARNED_ARMS:
        record = summary["arms"].get(arm)
        counts = record.get("counts", {}) if isinstance(record, dict) else {}
        activity = {
            key: int(counts.get(key, 0))
            for key in (
                "constructors",
                "train_episodes",
                "train_team_steps",
                "optimizer_steps",
                "eval_episodes",
                "eval_team_steps",
            )
        }
        per_arm[arm] = {
            "record_present": isinstance(record, dict),
            "scientific_constructor_observed": activity["constructors"] > 0,
            "training_activity_observed": any(
                activity[key] > 0
                for key in ("train_episodes", "train_team_steps", "optimizer_steps")
            ),
            "train_complete": bool(record.get("train_complete", False))
            if isinstance(record, dict)
            else False,
            "eval_complete": bool(record.get("eval_complete", False))
            if isinstance(record, dict)
            else False,
            "activity": activity,
        }
    activity_arms = [
        arm for arm, record in per_arm.items() if record["training_activity_observed"]
    ]
    complete_arms = [arm for arm, record in per_arm.items() if record["train_complete"]]
    constructor_arms = [
        arm for arm, record in per_arm.items() if record["scientific_constructor_observed"]
    ]
    return {
        "allocated_fit_arms": list(LEARNED_ARMS),
        "allocated_fits_this_invocation": 2,
        "allocated_fits_complete_batch": 6,
        "observed_training_activity_arms": activity_arms,
        "observed_training_activity_fit_lower_bound": len(activity_arms),
        "scientific_constructor_arms": constructor_arms,
        "completed_training_arms": complete_arms,
        "completed_training_fits": len(complete_arms),
        "exact_started_fits": 2 if summary["status"] == "COMPLETE" else None,
        "per_arm": per_arm,
        "qualification": (
            "Incomplete inherited counters provide only observed activity and constructor "
            "bounds; no unused or failed arm authorizes a replacement fit."
        ),
    }


def _file_identity(path):
    path = Path(path)
    if not path.is_file():
        return {"path": str(path), "present": False}
    return {
        "path": str(path),
        "present": True,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _telemetry(summary):
    peak_rss_kib = None
    unmeasured = []
    try:
        import resource

        peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except ImportError:
        unmeasured.append("single-process peak RSS")
    return {
        "wall_seconds": summary.get("elapsed_wall_seconds"),
        "wall_scope": (
            "runner main entry through the scientific loop and prepublication accounting; "
            "excludes final summary write, print and process exit"
        ),
        "process_cpu_seconds": summary.get("aggregate_process_cpu_seconds"),
        "process_cpu_scope": (
            "single process from study entry through scientific loop and accounting; "
            "excludes parser, admission and Torch import startup"
        ),
        "peak_rss_kib": peak_rss_kib,
        "peak_rss_scope": (
            "single process ru_maxrss through publication accounting"
            if peak_rss_kib is not None
            else "unavailable in the runner"
        ),
        "complete_process_exit_wall": None,
        "external_scope": (
            "the native launch manifest is authoritative for actual node and complete "
            "process wall/resource telemetry"
        ),
        "resources_unmeasured": unmeasured,
    }


def run(config, out, admission, start=None, factory=None):
    """Run one sequential B/G block; tests may supply only the fixed fixture factory."""
    from ..uav_motion_prefix_b01.environment import SyntheticAdapter, make_real
    from ..uav_motion_prefix_b01.learner import (
        collect_episode as collect_hover_episode,
        optimizer_for,
        update as ordinary_update,
    )
    from ..uav_motion_prefix_b01.policy import generator, templates

    require_config(config)
    admitted_sha = admission.get("sha")
    if not isinstance(admitted_sha, str) or not admitted_sha:
        raise ValueError("B04 requires an admitted source SHA")
    start = time.monotonic() if start is None else start
    cpu_start = time.process_time()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    factory = factory or (
        (lambda seed: SyntheticAdapter(seed, config.horizon))
        if config.fixture
        else make_real
    )
    rows, limits, arms = [], [], {}
    summary = {
        "object": OBJECT,
        "notebook": NOTEBOOK,
        "notebook_section": NOTEBOOK_SECTION,
        "configuration": asdict(config),
        "seed": config.seed,
        "selected_masters": list(ALLOWED_MASTERS),
        "launch_sha": admitted_sha,
        "admission": dict(admission),
        "declared_execution_node": EXECUTION_NODE,
        "node_evidence_scope": (
            "local_linux is the prospective object binding; the native launch manifest "
            "is authoritative for the actual execution node"
        ),
        "mode": "ENGINEERING_FIXTURE" if config.fixture else "UAV_B_G_EXPLORE",
        "status": "INCOMPLETE",
        "arms": arms,
        "limits": limits,
        "independent_training_instances": 1,
        "ratio_grouping": "agent_compound",
        "entropy_coef": 0.0,
        "value_moments": None,
        "device": "cpu",
        "dtype": "float32",
        "torch_threads": [torch.get_num_threads(), torch.get_num_interop_threads()],
        "evaluation_optimizer_steps": 0,
    }
    base = config.seed * 100000
    streams = {
        "B": (51, 52, 90000, 95000),
        "G": (21, 22, 50000, 60000),
    }
    summary["seeds"] = {
        "base": base,
        "initialization": base + 11,
        "B_gate_initialization": "deterministic zero logits",
        "train_world_start": base + 10000,
        "eval_world_start": base + 20000,
        "stream_offsets": streams,
    }

    def check():
        if time.monotonic() - start > config.watchdog_seconds:
            raise TimeoutError(
                "ordinary invocation watchdog expired; preserve incomplete work"
            )

    episodes_path = out / "episodes.jsonl"
    updates_path = out / "updates.jsonl"
    with episodes_path.open("w", encoding="utf-8") as episodes_file, updates_path.open(
        "w", encoding="utf-8"
    ) as updates_file:

        def emit(row):
            rows.append(row)
            episodes_file.write(json.dumps(row, allow_nan=False) + "\n")
            episodes_file.flush()

        try:
            check()
            common = templates(config.seed)
            for arm in LEARNED_ARMS:
                arm_start = time.monotonic()
                counts = new_counts(renewal=True, short=True)
                record = {
                    "counts": counts,
                    "train_complete": False,
                    "eval_complete": False,
                }
                arms[arm] = record
                actor, critic = make_arm(common, arm, base)
                initial = snapshot(actor, critic)
                record["exposure"] = exposure(initial, actor, critic)
                record["endpoint_gate"] = _endpoint_gate(arm, actor)
                record["trainable_parameters"] = sum(
                    parameter.numel()
                    for model in (actor, critic)
                    for parameter in model.parameters()
                    if parameter.requires_grad
                )
                optimizer = optimizer_for(actor, critic)
                velocity_rng, gate_rng = (
                    generator(base + offset) for offset in streams[arm][:2]
                )
                check()
                env = factory(base + 10000)
                counts["constructors"] += 1
                counts["constructor_resets"] += 1

                def episode(
                    phase,
                    episode_index,
                    label,
                    model,
                    value_model,
                    velocity,
                    gate,
                    active_counts,
                ):
                    reset = base + (
                        10000 if phase == "train" else 20000
                    ) + episode_index
                    metadata = {
                        "pair_master": config.seed,
                        "arm": label,
                        "phase": phase,
                        "episode": episode_index,
                    }
                    if label == "B":
                        return reactive.collect_episode(
                            env,
                            model,
                            value_model,
                            config.horizon,
                            reset,
                            velocity,
                            gate,
                            metadata,
                            check,
                            active_counts,
                            emit,
                            real=not config.fixture,
                        )
                    return collect_hover_episode(
                        env,
                        model,
                        value_model,
                        config.horizon,
                        reset,
                        velocity,
                        gate,
                        metadata,
                        check,
                        active_counts,
                        emit,
                        lambda row: None,
                        limits,
                        real=not config.fixture,
                        ratio_grouping="agent_compound",
                        value_moments=None,
                        renewal=True,
                        duration_support=(1, 2),
                    )

                try:
                    for rollout in range(config.train_episodes // 2):
                        data = [
                            episode(
                                "train",
                                2 * rollout + index,
                                arm,
                                actor,
                                critic,
                                velocity_rng,
                                gate_rng,
                                counts,
                            )
                            for index in range(2)
                        ]
                        if arm == "B":
                            losses = reactive.update(
                                actor,
                                critic,
                                optimizer,
                                data,
                                config.chunk,
                                check,
                                counts,
                            )
                        else:
                            losses = ordinary_update(
                                actor,
                                critic,
                                optimizer,
                                data,
                                config.chunk,
                                check,
                                counts,
                                ratio_grouping="agent_compound",
                                entropy_coef=0.0,
                                value_moments=None,
                            )
                        counts["rollouts"] += 1
                        updates_file.write(
                            json.dumps(
                                {"arm": arm, "rollout": rollout, "epochs": losses},
                                allow_nan=False,
                            )
                            + "\n"
                        )
                        updates_file.flush()
                        if (rollout + 1) % 128 == 0:
                            print(
                                f"{arm} episodes={2 * (rollout + 1)} "
                                f"elapsed={time.monotonic() - start:.2f}s",
                                flush=True,
                            )
                    record["train_complete"] = True
                    record["exposure"] = exposure(initial, actor, critic)
                    before_eval = snapshot(actor, critic)
                    updates_before_eval = counts["optimizer_steps"]
                    before_velocity = velocity_rng.get_state().clone()
                    before_gate = gate_rng.get_state().clone()
                    for episode_index in range(config.eval_episodes):
                        episode(
                            "eval",
                            episode_index,
                            arm,
                            actor,
                            critic,
                            generator(base + streams[arm][2] + episode_index),
                            generator(base + streams[arm][3] + episode_index),
                            counts,
                        )
                    record["eval_complete"] = True
                    record["evaluation_optimizer_steps"] = (
                        counts["optimizer_steps"] - updates_before_eval
                    )
                    if record["evaluation_optimizer_steps"] != 0:
                        raise RuntimeError("evaluation changed optimizer count")
                    record["evaluation_parameter_exposure"] = exposure(
                        before_eval, actor, critic
                    )
                    record["training_generators_unchanged_by_evaluation"] = bool(
                        torch.equal(before_velocity, velocity_rng.get_state())
                        and torch.equal(before_gate, gate_rng.get_state())
                    )
                    checkpoint = out / f"{arm}_final.pt"
                    torch.save(
                        {
                            "object": OBJECT,
                            "actor": actor.state_dict(),
                            "critic": critic.state_dict(),
                            "arm": arm,
                            "seed": config.seed,
                            "train_episodes": config.train_episodes,
                            "optimizer_steps": counts["optimizer_steps"],
                        },
                        checkpoint,
                    )
                    record["checkpoint"] = _file_identity(checkpoint)
                    if arm == "G":
                        hover_counts = new_counts(renewal=True, short=True)
                        arms["H"] = {
                            "counts": hover_counts,
                            "trained": False,
                            "eval_complete": False,
                            "evaluation_optimizer_steps": 0,
                        }
                        for episode_index in range(config.eval_episodes):
                            episode(
                                "eval",
                                episode_index,
                                "H",
                                None,
                                None,
                                None,
                                None,
                                hover_counts,
                            )
                        arms["H"]["eval_complete"] = True
                finally:
                    record["exposure"] = exposure(initial, actor, critic)
                    record["endpoint_gate"] = _endpoint_gate(arm, actor)
                    record["gate_activity"] = (
                        _gate_activity(counts) if arm == "B" else None
                    )
                    if arm == "G":
                        record["ordinary_activity"] = {
                            key: int(counts.get(key, 0))
                            for key in (
                                "train_velocity_decisions",
                                "eval_velocity_decisions",
                                "train_duration_decisions",
                                "eval_duration_decisions",
                            )
                        }
                    record["elapsed_wall_seconds"] = time.monotonic() - arm_start
                    if hasattr(env, "close"):
                        env.close()
            summary["status"] = "COMPLETE"
        except Exception as error:
            traceback.print_exc()
            summary["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }

    summary["panel"] = final_panel(
        rows, config.eval_episodes, summary["status"] == "COMPLETE"
    )
    keys = {
        key
        for record in arms.values()
        for key in record.get("counts", {})
    }
    summary["counts"] = {
        key: sum(record.get("counts", {}).get(key, 0) for record in arms.values())
        for key in sorted(keys)
    }
    summary["fit_accounting"] = _fit_accounting(summary)
    summary["elapsed_wall_seconds"] = time.monotonic() - start
    summary["aggregate_process_cpu_seconds"] = time.process_time() - cpu_start
    summary["telemetry"] = _telemetry(summary)
    summary["resource_note"] = (
        "Runner telemetry has the explicit scopes in telemetry; missing complete-process "
        "telemetry limits only resource claims and does not invalidate the scientific result."
    )
    summary["artifacts"] = {
        "episodes": _file_identity(episodes_path),
        "updates": _file_identity(updates_path),
        "checkpoints": {
            arm: _file_identity(out / f"{arm}_final.pt") for arm in LEARNED_ARMS
        },
    }
    write_summary(out / "summary.json", summary)
    return summary
