"""One fixed 12-fit program with all unscreened roots and final I/P/K/D panels."""

from collections import defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from .collection import collect_parent, collect_composed
from .model import (build_c, build_b, build_adaptation, load_evaluation,
                    save_checkpoint, snapshot, exposure)
from .protocol import (HORIZON, TRAIN, EVAL, LINEAGES, STAGES, PROGRAMS, FIRST_MASTER,
                       masters, addresses, rng_table, expected_training_counts,
                       expected_evaluation_counts)
from .update import parent_optimizer, optimizers_for, update_parent, update_adaptation


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tensor_hashes(actor, critic):
    return {key: hashlib.sha256(value.numpy().tobytes()).hexdigest()
            for key, value in snapshot(actor, critic).items()}


def record_exposure(summary, initial, actor, critic):
    """Keep failed-fit accounting writable even when its learner tensors are damaged."""
    try:
        value = exposure(initial, actor, critic)
        missing = []
        for group, fields in value.items():
            for name, measurement in fields.items():
                if isinstance(measurement, float) and not math.isfinite(measurement):
                    fields[name] = None
                    missing.append(f"{group}.{name}")
        summary["exposure"] = value
        if missing:
            summary["exposure_unavailable"] = dict(
                reason="nonfinite parameter-derived diagnostics after learner failure", fields=missing)
    except Exception as diagnostic_error:
        summary["exposure"] = None
        summary["exposure_unavailable"] = dict(
            reason=f"diagnostic failed: {type(diagnostic_error).__name__}: {diagnostic_error}")


def new_counts():
    counts = defaultdict(int, expected_evaluation_counts())
    for key in counts:
        counts[key] = 0
    counts.update(delivered_packets=0, censored_packets=0)
    return counts


def resources_since(start, wall):
    end = resource.getrusage(resource.RUSAGE_SELF)
    return dict(wall_seconds=time.monotonic() - wall,
                process_user_seconds=end.ru_utime - start.ru_utime,
                process_system_seconds=end.ru_stime - start.ru_stime,
                process_cpu_seconds=end.ru_utime + end.ru_stime - start.ru_utime - start.ru_stime,
                process_lifetime_peak_rss_kib_linux=end.ru_maxrss,
                cpu_scope="RUSAGE_SELF delta; one worker; nested cells are not added to batch",
                rss_scope="worker lifetime high-water Linux KiB, not incremental cell peak",
                torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads())


def check_counts(counts, expected):
    for key, value in expected.items():
        if counts[key] != value:
            raise RuntimeError(f"count mismatch {key}: {counts[key]} != {value}")
    if counts["delivered_packets"] + counts["censored_packets"] != counts["team_steps"]:
        raise RuntimeError("delivered/censored packet closure")


def run_fit(lineage, stage, out, launch_sha, parent=None, *, factory=make_real,
            horizon=HORIZON, train=TRAIN, check=lambda: None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    started_usage, started_clock = resource.getrusage(resource.RUSAGE_SELF), time.monotonic()
    master = masters(lineage)[stage]
    addr = addresses(lineage, stage, train=train)
    counts = new_counts()
    summary = dict(object="UAV-PARENT-ADAPTATION-B01-FIT", lineage=lineage, stage=stage,
                   master=master, directory=str(out), launch_sha=launch_sha,
                   status="INCOMPLETE", limits=[], counts=counts, parent=parent,
                   addresses=addr, started_wall=time.time(),
                   scientific_invocation=factory is make_real,
                   configuration=dict(train=train, horizon=horizon, epochs=4, chunk=32,
                                      episodes_per_rollout=2, packet_bytes=28 if stage in ("C", "B") else 40))
    actor = critic = initial = None
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episode_file, \
         (out / "updates.jsonl").open("x", encoding="utf-8") as update_file:
        def emit(row):
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()
            summary["last_completed_episode"] = row["episode"]

        def emit_update(row):
            update_file.write(json.dumps(row, allow_nan=False) + "\n")
            update_file.flush()

        try:
            check()
            if stage == "C":
                if parent is not None:
                    raise ValueError("C begins independently, with no checkpoint parent")
                actor, critic = build_c(master)
            elif stage == "B":
                actor, critic = build_b(master, Path(parent["path"]).read_bytes(), parent,
                                        lineage=lineage, launch_sha=launch_sha)
            else:
                actor, critic = build_adaptation(master, stage, Path(parent["path"]).read_bytes(), parent,
                                                 lineage=lineage, launch_sha=launch_sha)
            initial = snapshot(actor, critic)
            summary["initial_tensor_sha256"] = tensor_hashes(actor, critic)
            summary["initial_checkpoint"] = save_checkpoint(
                out / "initial.pt", actor, critic, lineage=lineage, stage=stage,
                endpoint="initial", master=master, launch_sha=launch_sha, parent=parent)
            summary["initial_sigma"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
            summary["actor_trainable_parameters"] = sum(p.numel() for p in actor.parameters() if p.requires_grad)
            summary["critic_trainable_parameters"] = sum(p.numel() for p in critic.parameters() if p.requires_grad)
            if stage in ("C", "B"):
                opt = parent_optimizer(actor, critic)
                summary["initial_optimizer_state_entries"] = [len(opt.state)]
                summary["actual_optimizer_lrs"] = [opt.param_groups[0]["lr"]]
                summary["optimizer_law"] = "joint_actor_critic_global_clip"
            else:
                actor_opt, critic_opt = optimizers_for(actor, critic)
                summary["initial_optimizer_state_entries"] = [len(actor_opt.state), len(critic_opt.state)]
                summary["actual_optimizer_lrs"] = [actor_opt.param_groups[0]["lr"], critic_opt.param_groups[0]["lr"]]
                summary["optimizer_law"] = "separate_actor_critic_separate_clips"
            env = factory(addr["scene_start"])
            counts["constructors"] += 1
            motion_rng = generator(addr["motion"])
            counts["fit_started"] = 1
            write_json(out / "summary.json", summary)
            collect = collect_parent if stage in ("C", "B") else collect_composed
            for rollout in range(train // 2):
                episodes = []
                for e in (2 * rollout, 2 * rollout + 1):
                    episodes.append(collect(
                        env, actor, critic, stage, horizon,
                        addr["scene_start"] + e, addr["channel_start"] + e, motion_rng,
                        dict(lineage=lineage, arm=stage, master=master, phase="train", episode=e,
                             motion_seed=addr["motion"]), counts, emit, check))
                record = lambda row: emit_update(dict(rollout=rollout, **row))
                if stage in ("C", "B"):
                    update_parent(actor, critic, opt, episodes, counts, check, record)
                else:
                    update_adaptation(actor, critic, actor_opt, critic_opt, episodes, counts, check, record)
                counts["rollouts"] += 1
                write_json(out / "summary.json", summary)
            record_exposure(summary, initial, actor, critic)
            summary["final_tensor_sha256"] = tensor_hashes(actor, critic)
            summary["final_sigma"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
            if stage in ("K", "D"):
                if summary["initial_tensor_sha256"]["base_actor"] != summary["final_tensor_sha256"]["base_actor"]:
                    raise RuntimeError("frozen parent actor changed")
                if summary["initial_sigma"] != summary["final_sigma"]:
                    raise RuntimeError("frozen parent variance changed")
            summary["final_checkpoint"] = save_checkpoint(
                out / "final.pt", actor, critic, lineage=lineage, stage=stage,
                endpoint="final", master=master, launch_sha=launch_sha, parent=parent)
            check_counts(counts, expected_training_counts(stage, horizon, train))
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
            if initial is not None:
                record_exposure(summary, initial, actor, critic)
        finally:
            summary["finished_wall"] = time.time()
            summary["resources"] = resources_since(started_usage, started_clock)
            summary["episode_stream_sha256"] = digest(out / "episodes.jsonl")
            summary["update_stream_sha256"] = digest(out / "updates.jsonl")
            write_json(out / "summary.json", summary)
    return summary


def run_evaluation(lineage, program, checkpoint, out, launch_sha, *, factory=make_real,
                   horizon=HORIZON, evaluation=EVAL, check=lambda: None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    started_usage, started_clock = resource.getrusage(resource.RUSAGE_SELF), time.monotonic()
    stage, endpoint = (("C", "initial") if program == "I" else
                       ("B", "final") if program == "P" else (program, "final"))
    addr = addresses(lineage, "evaluation", evaluation=evaluation)
    counts, rows = new_counts(), []
    summary = dict(object="UAV-PARENT-ADAPTATION-B01-EVALUATION", lineage=lineage,
                   program=program, directory=str(out), launch_sha=launch_sha,
                   checkpoint=checkpoint, status="INCOMPLETE", limits=[], counts=counts, rows=rows,
                   addresses=addr, started_wall=time.time(), scientific_invocation=factory is make_real,
                   configuration=dict(horizon=horizon, evaluation=evaluation, packet_bytes=40,
                                      action_mode="sampled", training=0))
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as stream:
        def emit(row):
            if "raw" in row:
                row["raw_bytes"] = Path(row["raw"]).stat().st_size
            rows.append(row)
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            write_json(out / "summary.json", summary)

        try:
            check()
            actor, critic = load_evaluation(Path(checkpoint["path"]).read_bytes(), checkpoint,
                                            lineage=lineage, stage=stage, endpoint=endpoint,
                                            launch_sha=launch_sha)
            summary["initial_tensor_sha256"] = tensor_hashes(actor, critic)
            summary["inherited_sigma"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
            env = factory(addr["scene_start"])
            counts["constructors"] += 1
            for e in range(evaluation):
                collect_composed(
                    env, actor, critic, program, horizon, addr["scene_start"] + e,
                    addr["channel_start"] + e, generator(addr["motion_start"] + e),
                    dict(lineage=lineage, arm=program, master=masters(lineage)[stage],
                         phase="final_eval", episode=e, motion_seed=addr["motion_start"] + e),
                    counts, emit, check, raw_path=out / "raw" / f"final_{e:02d}.npz")
            summary["after_eval_tensor_sha256"] = tensor_hashes(actor, critic)
            if summary["initial_tensor_sha256"] != summary["after_eval_tensor_sha256"]:
                raise RuntimeError("evaluation changed frozen tensors")
            check_counts(counts, expected_evaluation_counts(horizon, evaluation))
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
        finally:
            summary["finished_wall"] = time.time()
            summary["resources"] = resources_since(started_usage, started_clock)
            summary["episode_stream_sha256"] = digest(out / "episodes.jsonl")
            write_json(out / "summary.json", summary)
    return summary


def validate_batch(summary, *, horizon=HORIZON, train=TRAIN, evaluation=EVAL):
    fits, evaluations = summary["fits"], summary["evaluations"]
    if [(x["lineage"], x["stage"]) for x in fits] != [(l, s) for l in LINEAGES for s in STAGES]:
        raise RuntimeError("missing or reordered fixed fits")
    if [(x["lineage"], x["program"]) for x in evaluations] != [(l, p) for l in LINEAGES for p in PROGRAMS]:
        raise RuntimeError("missing or reordered evaluation programs")
    for cell in fits + evaluations:
        if cell["status"] != "COMPLETE" or cell["limits"]:
            raise RuntimeError("incomplete scientific cell")
        expected = (expected_training_counts(cell["stage"], horizon, train) if "stage" in cell else
                    expected_evaluation_counts(horizon, evaluation))
        check_counts(cell["counts"], expected)
    for lineage in LINEAGES:
        paired = [cell for cell in fits if cell["lineage"] == lineage and cell["stage"] in ("K", "D")]
        for group in ("base_actor", "critic_old", "critic_forecast"):
            if paired[0]["initial_tensor_sha256"][group] != paired[1]["initial_tensor_sha256"][group]:
                raise RuntimeError("adapter initial common tensors differ")
    return True


def run_batch(out, launch_sha, *, seed=FIRST_MASTER, factory=make_real,
              horizon=HORIZON, train=TRAIN, evaluation=EVAL, check=lambda: None, start_usage=None):
    if seed != FIRST_MASTER or train % 2 or horizon % 32:
        raise ValueError("fixed lineage seed and rollout/chunk laws")
    if factory is make_real and (horizon, train, evaluation) != (HORIZON, TRAIN, EVAL):
        raise ValueError("native scientific exposure is fixed")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists() or (out / "config.json").exists():
        raise FileExistsError("existing scientific output is never restarted")
    start_usage = start_usage or resource.getrusage(resource.RUSAGE_SELF)
    start_clock = time.monotonic()
    summary = dict(object="UAV-PARENT-ADAPTATION-B01", source_sha=launch_sha, seed=seed,
                   status="INCOMPLETE", limits=[], fits=[], evaluations=[], actual={},
                   started_wall=time.time(), scientific_invocation=factory is make_real)
    config = dict(direction="uav_parent_adaptation", source_sha=launch_sha,
                  lineages=list(LINEAGES), stages=list(STAGES), programs=list(PROGRAMS),
                  horizon=horizon, train=train, evaluation=evaluation, rng=rng_table(),
                  device="cpu", dtype="float32", torch_threads=1, parent_packet_bytes=28,
                  evaluation_and_adaptation_packet_bytes=40, correction_bound=.10,
                  episode_endpoint="fixed_final", action_mode="sampled",
                  checkpoint_selection=False, parent_quality_selection=False,
                  parent_generation_fits=6, adaptation_fits=6,
                  expected_team_steps=3 * (4 * train + 4 * evaluation) * horizon,
                  expected_adam_calls=3 * (2 + 4) * (train // 2 * 4),
                  expected_actor_replay_rows=12 * (train // 2 * 4) * 2 * horizon * 5)
    write_json(out / "config.json", config)

    def persist():
        cells = summary["fits"] + summary["evaluations"]
        keys = set(new_counts()).union(*(cell["counts"] for cell in cells))
        summary["actual"] = {key: sum(c["counts"].get(key, 0) for c in cells) for key in sorted(keys)}
        write_json(out / "summary.json", summary)

    try:
        for lineage in LINEAGES:
            completed = {}
            for stage in STAGES:
                summary["active_cell"] = f"{lineage}/{stage}"
                persist()
                parent = None if stage == "C" else completed["C" if stage == "B" else "B"]["final_checkpoint"]
                cell = run_fit(lineage, stage, out / str(lineage) / stage, launch_sha, parent,
                               factory=factory, horizon=horizon, train=train, check=check)
                summary["fits"].append(cell)
                completed[stage] = cell
                persist()
                if cell["status"] != "COMPLETE":
                    raise RuntimeError(f"incomplete fit {lineage}/{stage}: {cell['limits']}")
            checkpoints = {"I": completed["C"]["initial_checkpoint"],
                           "P": completed["B"]["final_checkpoint"],
                           "K": completed["K"]["final_checkpoint"],
                           "D": completed["D"]["final_checkpoint"]}
            for program in PROGRAMS:
                summary["active_cell"] = f"{lineage}/eval/{program}"
                persist()
                cell = run_evaluation(lineage, program, checkpoints[program],
                                      out / str(lineage) / "evaluation" / program, launch_sha,
                                      factory=factory, horizon=horizon, evaluation=evaluation, check=check)
                summary["evaluations"].append(cell)
                persist()
                if cell["status"] != "COMPLETE":
                    raise RuntimeError(f"incomplete evaluation {lineage}/{program}: {cell['limits']}")
        validate_batch(summary, horizon=horizon, train=train, evaluation=evaluation)
        summary["status"] = "COMPLETE"
        summary["active_cell"] = None
    except Exception as error:
        summary["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        summary["finished_wall"] = time.time()
        summary["resources"] = resources_since(start_usage, start_clock)
        summary["config_sha256"] = digest(out / "config.json")
        persist()
    return summary
