"""Three fixed U fits and fresh, interleaved P/U/K/D deployment panels."""

import json
import math
from pathlib import Path
import platform
import resource
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.uav_correction_compression.model import TimedActor
from experiments.candidates.uav_correction_compression.study import measured, new_cost
from experiments.candidates.uav_parent_adaptation.b01 import model as old_model
from experiments.candidates.uav_parent_adaptation.b01.study import (
    write_json, digest, new_counts, resources_since, check_counts,
    tensor_hashes as old_tensor_hashes,
)
from experiments.candidates.uav_parent_adaptation.b01.update import parent_optimizer, update_parent
from .assets import load_assets
from .collection import collect_training, collect_evaluation
from . import model
from .protocol import (HORIZON, TRAIN, EVAL, LINEAGES, PROGRAMS, FIRST_MASTER,
                       PARENT_SOURCE, PARENT_SUMMARY_SHA256, PARENT_ROOT, WITNESS_FIELDS,
                       masters, addresses, rng_table, rotating_order,
                       expected_training_counts, expected_evaluation_counts)


def tensor_hashes(actor, critic):
    import hashlib
    return {key: hashlib.sha256(value.numpy().tobytes()).hexdigest()
            for key, value in model.snapshot(actor, critic).items()}


def record_exposure(summary, initial, actor, critic):
    try:
        value = model.exposure(initial, actor, critic)
        missing = []
        for group, fields in value.items():
            for name, measurement in fields.items():
                if isinstance(measurement, float) and not math.isfinite(measurement):
                    fields[name] = None
                    missing.append(f"{group}.{name}")
        summary["exposure"] = value
        if missing:
            summary["exposure_unavailable"] = dict(reason="nonfinite parameter diagnostics", fields=missing)
    except Exception as error:
        summary["exposure"] = None
        summary["exposure_unavailable"] = dict(reason=f"{type(error).__name__}: {error}")


def run_fit(lineage, out, launch_sha, parent, expected_witnesses, *, factory=make_real,
            horizon=HORIZON, train=TRAIN, check=lambda: None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    usage, clock = resource.getrusage(resource.RUSAGE_SELF), time.monotonic()
    master = masters(lineage)["U"]
    addr = addresses(lineage, "U", train=train)
    counts = new_counts()
    summary = dict(object="UAV-PARENT-ADAPTATION-B02-FIT", lineage=lineage, stage="U",
                   master=master, directory=str(out), launch_sha=launch_sha,
                   parent_source=PARENT_SOURCE, parent=parent, status="INCOMPLETE",
                   limits=[], counts=counts, addresses=addr, started_wall=time.time(),
                   scientific_invocation=factory is make_real, matched_training_episodes=0,
                   configuration=dict(train=train, horizon=horizon, epochs=4, chunk=32,
                                      episodes_per_rollout=2, packet_bytes=40))
    actor = critic = initial = None
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episode_file, \
         (out / "updates.jsonl").open("x", encoding="utf-8") as update_file:
        def emit(row):
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()
            summary["last_completed_episode"] = row["episode"]
            if tuple(row[k] for k in WITNESS_FIELDS) != expected_witnesses[row["episode"]]:
                raise RuntimeError("U actual exogenous stream differs from retained K/D")
            summary["matched_training_episodes"] += 1

        def emit_update(row):
            update_file.write(json.dumps(row, allow_nan=False) + "\n")
            update_file.flush()

        try:
            check()
            actor, critic = model.build_u(master, Path(parent["path"]).read_bytes(), parent,
                                          lineage=lineage, launch_sha=launch_sha)
            initial = model.snapshot(actor, critic)
            summary["initial_tensor_sha256"] = tensor_hashes(actor, critic)
            summary["initial_checkpoint"] = model.save_checkpoint(
                out / "initial.pt", actor, critic, lineage=lineage, endpoint="initial",
                master=master, launch_sha=launch_sha, parent=parent)
            summary["initial_log_std"] = actor.log_std.detach().tolist()
            summary["initial_sigma"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
            summary["actor_trainable_parameters"] = sum(p.numel() for p in actor.parameters() if p.requires_grad)
            summary["critic_trainable_parameters"] = sum(p.numel() for p in critic.parameters() if p.requires_grad)
            opt = parent_optimizer(actor, critic)
            summary["initial_optimizer_state_entries"] = [len(opt.state)]
            summary["actual_optimizer_lrs"] = [opt.param_groups[0]["lr"]]
            summary["optimizer_law"] = "joint_actor_critic_global_clip"
            env = factory(addr["scene_start"])
            counts["constructors"] += 1
            motion_rng = generator(addr["motion"])
            counts["fit_started"] = 1
            write_json(out / "summary.json", summary)
            for rollout in range(train // 2):
                episodes = []
                for e in (2 * rollout, 2 * rollout + 1):
                    episodes.append(collect_training(
                        env, actor, critic, horizon, addr["scene_start"] + e,
                        addr["channel_start"] + e, motion_rng,
                        dict(lineage=lineage, arm="U", master=master, phase="train", episode=e,
                             motion_seed=addr["motion"]), counts, emit, check))
                update_parent(actor, critic, opt, episodes, counts, check,
                              lambda row: emit_update(dict(rollout=rollout, **row)))
                counts["rollouts"] += 1
                write_json(out / "summary.json", summary)
            record_exposure(summary, initial, actor, critic)
            summary["final_tensor_sha256"] = tensor_hashes(actor, critic)
            summary["final_log_std"] = actor.log_std.detach().tolist()
            summary["final_sigma"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
            summary["final_checkpoint"] = model.save_checkpoint(
                out / "final.pt", actor, critic, lineage=lineage, endpoint="final",
                master=master, launch_sha=launch_sha, parent=parent)
            check_counts(counts, expected_training_counts(horizon, train))
            if summary["matched_training_episodes"] != train:
                raise RuntimeError("missing matched U training witnesses")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
            if initial is not None:
                record_exposure(summary, initial, actor, critic)
        finally:
            summary["finished_wall"] = time.time()
            summary["resources"] = resources_since(usage, clock)
            summary["episode_stream_sha256"] = digest(out / "episodes.jsonl")
            summary["update_stream_sha256"] = digest(out / "updates.jsonl")
            write_json(out / "summary.json", summary)
    return summary


def run_evaluation_panel(lineage, checkpoints, out, launch_sha, *, factory=make_real,
                         horizon=HORIZON, evaluation=EVAL, check=lambda: None, record_order=lambda row: None):
    out = Path(out)
    addr = addresses(lineage, "evaluation", evaluation=evaluation)
    cells, actors, critics, envs, streams = {}, {}, {}, {}, {}
    # All cells exist in the returned accounting even if one loader or episode fails.
    for program in PROGRAMS:
        directory = out / program
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "raw").mkdir()
        cells[program] = dict(object="UAV-PARENT-ADAPTATION-B02-EVALUATION",
            lineage=lineage, program=program, directory=str(directory), launch_sha=launch_sha,
            checkpoint=checkpoints[program], status="INCOMPLETE", limits=[], counts=new_counts(), rows=[],
            addresses=addr, scientific_invocation=factory is make_real,
            timing=dict(setup=new_cost(), episode_loop=new_cost()),
            configuration=dict(horizon=horizon, evaluation=evaluation, packet_bytes=40,
                               action_mode="sampled", training=0))
    active = None
    try:
        for program in PROGRAMS:
            active, cell = program, cells[program]
            check()
            checkpoint = checkpoints[program]
            content = Path(checkpoint["path"]).read_bytes()
            def setup():
                if program == "U":
                    actor, critic = model.load_evaluation(content, checkpoint, lineage=lineage,
                                                         endpoint="final", launch_sha=launch_sha)
                else:
                    actor, critic = old_model.load_evaluation(content, checkpoint, lineage=lineage,
                        stage="B" if program == "P" else program, endpoint="final", launch_sha=PARENT_SOURCE)
                return actor, critic, factory(addr["scene_start"])
            actor, critic, env = measured(cell["timing"]["setup"], setup)
            cell["counts"]["constructors"] += 1
            cell["initial_tensor_sha256"] = old_tensor_hashes(actor, critic)
            cell["actual_log_std"] = actor.log_std.detach().tolist()
            cell["actual_sigma"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
            actors[program], critics[program], envs[program] = TimedActor(actor), critic, env
            cell["timing"]["actor_forward"] = actors[program].timing
            streams[program] = (Path(cell["directory"]) / "episodes.jsonl").open("x", encoding="utf-8")
            write_json(Path(cell["directory"]) / "summary.json", cell)
        for e in range(evaluation):
            for rank, program in enumerate(rotating_order(e)):
                active, cell = program, cells[program]
                record_order(dict(lineage=lineage, world=e, rank=rank, program=program))
                def emit(row):
                    row["raw_bytes"] = Path(row["raw"]).stat().st_size
                    cell["rows"].append(row)
                    streams[program].write(json.dumps(row, allow_nan=False) + "\n")
                    streams[program].flush()
                measured(cell["timing"]["episode_loop"], collect_evaluation,
                    envs[program], actors[program], critics[program], program, horizon,
                    addr["scene_start"] + e, addr["channel_start"] + e, generator(addr["motion_start"] + e),
                    dict(lineage=lineage, arm=program, master=checkpoints[program]["master"],
                         phase="final_eval", episode=e, motion_seed=addr["motion_start"] + e),
                    cell["counts"], emit, check, Path(cell["directory"]) / "raw" / f"final_{e:02d}.npz")
                write_json(Path(cell["directory"]) / "summary.json", cell)
        for program, cell in cells.items():
            active = program
            cell["after_eval_tensor_sha256"] = old_tensor_hashes(actors[program].actor, critics[program])
            if cell["initial_tensor_sha256"] != cell["after_eval_tensor_sha256"]:
                raise RuntimeError("evaluation changed frozen tensors")
            check_counts(cell["counts"], expected_evaluation_counts(horizon, evaluation))
            if cell["timing"]["actor_forward"]["calls"] != horizon * evaluation:
                raise RuntimeError("actual actor timing call count mismatch")
            cell["status"] = "COMPLETE"
    except Exception as error:
        if active is not None:
            cells[active]["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        for stream in streams.values():
            stream.close()
        for cell in cells.values():
            path = Path(cell["directory"]) / "episodes.jsonl"
            cell["episode_stream_sha256"] = digest(path) if path.exists() else None
            write_json(Path(cell["directory"]) / "summary.json", cell)
    return list(cells.values())


def validate_batch(summary, *, horizon=HORIZON, train=TRAIN, evaluation=EVAL):
    fits, evaluations = summary["fits"], summary["evaluations"]
    if [(c["lineage"], c["stage"]) for c in fits] != [(l, "U") for l in LINEAGES]:
        raise RuntimeError("fixed U fits missing or reordered")
    if [(c["lineage"], c["program"]) for c in evaluations] != [(l, p) for l in LINEAGES for p in PROGRAMS]:
        raise RuntimeError("fixed evaluation programs missing or reordered")
    for cell in fits + evaluations:
        if cell["status"] != "COMPLETE" or cell["limits"]:
            raise RuntimeError("incomplete scientific cell")
        check_counts(cell["counts"], expected_training_counts(horizon, train) if "stage" in cell else
                     expected_evaluation_counts(horizon, evaluation))
    expected_order = [dict(lineage=l, world=e, rank=r, program=p)
                      for l in LINEAGES for e in range(evaluation) for r, p in enumerate(rotating_order(e))]
    if summary["evaluation_order"] != expected_order:
        raise RuntimeError("evaluation interleaving changed")


def run_batch(out, launch_sha, *, parent_root=PARENT_ROOT, seed=FIRST_MASTER, factory=make_real,
              horizon=HORIZON, train=TRAIN, evaluation=EVAL, parent_summary_sha256=PARENT_SUMMARY_SHA256,
              check=lambda: None, start_usage=None):
    if seed != FIRST_MASTER or train % 2 or horizon % 32:
        raise ValueError("fixed first master, full rollouts and chunk32")
    if factory is make_real and ((horizon, train, evaluation) != (HORIZON, TRAIN, EVAL)
                                or parent_summary_sha256 != PARENT_SUMMARY_SHA256
                                or str(Path(parent_root).resolve()) != PARENT_ROOT):
        raise ValueError("native scientific exposure and inputs are fixed")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError("scientific output is never restarted or overwritten")
    usage, clock = start_usage or resource.getrusage(resource.RUSAGE_SELF), time.monotonic()
    summary = dict(object="UAV-PARENT-ADAPTATION-B02", source_sha=launch_sha, seed=seed,
                   status="INCOMPLETE", limits=[], fits=[], evaluations=[], actual={},
                   evaluation_order=[], started_wall=time.time(), scientific_invocation=factory is make_real)
    config = dict(direction="uav_parent_adaptation", source_sha=launch_sha, lineages=list(LINEAGES),
                  train_program="U", programs=list(PROGRAMS), horizon=horizon, train=train,
                  evaluation=evaluation, rng=rng_table(), device="cpu", dtype="float32", torch_threads=1,
                  packet_bytes=40, actor_input_size=171, critic_input_size=451, episode_endpoint="fixed_final",
                  action_mode="sampled", checkpoint_selection=False, parent_quality_selection=False,
                  evaluation_order="world-major; rotate P,U,K,D left by world mod4; lineage1,2,3",
                  parent_source=PARENT_SOURCE, parent_root=str(Path(parent_root).resolve()),
                  parent_summary_sha256=parent_summary_sha256,
                  new_fits=3, parent_generation_fits=0, retained_adaptation_refits=0,
                  expected_team_steps=3 * (train + 4 * evaluation) * horizon,
                  expected_adam_calls=3 * (train // 2 * 4),
                  expected_actor_replay_rows=3 * (train // 2 * 4) * 2 * horizon * 5,
                  runtime=dict(python=platform.python_version(), torch=torch.__version__,
                               platform=platform.platform(), torch_threads=torch.get_num_threads()),
                  timing_scope=dict(actor_forward="actual full actor calls, including GRU/composition",
                      episode_loop="collector reset/host/channel/sampler/trace/NPZ/hash/stream write; excludes cell JSON",
                      setup="checkpoint load, isolated actor/critic construction and native env constructor",
                      worker="RUSAGE_SELF; includes all support and nested costs, do not add them again"))
    write_json(out / "config.json", config)
    def persist():
        cells = summary["fits"] + summary["evaluations"]
        keys = set(new_counts()).union(*(cell["counts"] for cell in cells))
        summary["actual"] = {key: sum(c["counts"].get(key, 0) for c in cells) for key in sorted(keys)}
        write_json(out / "summary.json", summary)
    try:
        assets = load_assets(parent_root, summary_sha256=parent_summary_sha256, train=train, horizon=horizon)
        summary["retained_inputs"] = assets["identity"]
        for lineage in LINEAGES:
            summary["active_cell"] = f"{lineage}/U"
            persist()
            checkpoints = dict(assets["checkpoints"][lineage])
            cell = run_fit(lineage, out / str(lineage) / "U", launch_sha, checkpoints["P"],
                           assets["witnesses"][lineage], factory=factory, horizon=horizon, train=train, check=check)
            summary["fits"].append(cell)
            persist()
            if cell["status"] != "COMPLETE":
                raise RuntimeError(f"incomplete U fit {lineage}: {cell['limits']}")
            checkpoints["U"] = cell["final_checkpoint"]
            summary["active_cell"] = f"{lineage}/evaluation"
            persist()
            cells = run_evaluation_panel(lineage, checkpoints, out / str(lineage) / "evaluation", launch_sha,
                factory=factory, horizon=horizon, evaluation=evaluation, check=check,
                record_order=summary["evaluation_order"].append)
            summary["evaluations"].extend(cells)
            persist()
            if any(c["status"] != "COMPLETE" for c in cells):
                raise RuntimeError(f"incomplete evaluation lineage {lineage}")
        validate_batch(summary, horizon=horizon, train=train, evaluation=evaluation)
        summary["status"], summary["active_cell"] = "COMPLETE", None
    except Exception as error:
        summary["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        summary["finished_wall"] = time.time()
        summary["resources"] = resources_since(usage, clock)
        summary["config_sha256"] = digest(out / "config.json")
        persist()
    return summary
