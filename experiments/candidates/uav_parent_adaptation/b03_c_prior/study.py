"""One complete, bounded B03 study. No continuation or partial-fit retry mode."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import platform
import resource
import sys
import time
import traceback

import numpy as np
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from .collection import collect_episode
from .policy import templates, optimizers
from .protocol import (ARMS, EVAL_WORLDS, HORIZON, MASTERS, OBJECT, TRAIN_EPISODES,
                       clock, elapsed, eval_world, expected_counts, identity,
                       train_world, write_json)
from .update import update

ROOT = Path(__file__).resolve().parents[4]


def tensors(actor, critic):
    return {prefix + key: value.detach().cpu().clone()
            for prefix, model in (("actor.", actor), ("critic.", critic))
            for key, value in model.state_dict().items()}


def tensor_identities(actor, critic):
    return {key: hashlib.sha256(value.numpy().tobytes()).hexdigest()
            for key, value in tensors(actor, critic).items()}


def movement(initial, actor, critic):
    final = tensors(actor, critic)
    groups = dict(table=["actor.table"],
                  hidden=[key for key in final if key.startswith(("actor.mlp.0.", "actor.mlp.2."))],
                  head=[key for key in final if key.startswith("actor.mlp.4.")],
                  critic=[key for key in final if key.startswith("critic.")])
    return {name: dict(l2=float(torch.linalg.vector_norm(torch.cat([
                (final[key] - initial[key]).flatten() for key in keys]))),
                changed_entries=sum(int(torch.count_nonzero(final[key] != initial[key])) for key in keys))
            for name, keys in groups.items()}


def save_checkpoint(path, actor, critic, aopt, copt, *, endpoint, master, launch_sha):
    torch.save(dict(object=OBJECT, endpoint=endpoint, master=master, launch_sha=launch_sha,
                    actor=actor.state_dict(), critic=critic.state_dict(),
                    actor_optimizer=aopt.state_dict(), critic_optimizer=copt.state_dict()), path)
    return identity(path, Path(path).parent.parent)


def source_manifest():
    names = {Path(module.__file__).resolve() for module in list(sys.modules.values())
             if getattr(module, "__file__", None) and str(module.__file__).endswith(".py")
             and Path(module.__file__).is_absolute()
             and Path(module.__file__).resolve().is_relative_to(ROOT)
             and Path(module.__file__).is_file()}
    names.update(Path(__file__).parent.glob("*.py"))
    # Pure-reader dependencies are not necessarily imported by the worker.
    names.add(ROOT / "experiments/candidates/uav_local_history/b01/read_b01.py")
    return [identity(path, ROOT) for path in sorted(names)]


def run_batch(out, launch_sha, *, start_usage=None, factory=make_real):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    forbidden = ("summary.json", "training.jsonl", "evaluation.jsonl", "updates.jsonl", "raw", "checkpoints")
    if any((out / name).exists() for name in forbidden):
        raise FileExistsError("B03 never overwrites accepted or uncertain output")
    started = clock()
    counts = defaultdict(int)
    rows, fits = [], []
    summary = dict(object=OBJECT, status="INCOMPLETE", launch_sha=launch_sha, limits=[],
                   counts=counts, expected_counts=expected_counts(), rows=rows, fits=fits)
    config = dict(object=OBJECT, launch_sha=launch_sha, masters=MASTERS, horizon=HORIZON,
                  train_episodes_per_fit=TRAIN_EPISODES, evaluation_worlds_per_block=EVAL_WORLDS,
                  arms=ARMS, prior_c_probability=.9, kappa=float(np.log(234.0)),
                  selection_sha="c5ff2774ec4423dfb8629abf49a71cc4bd4772cd",
                  design_sha="e1a1171a0cb21c463dcb058dc3d71e946dc75c88",
                  train_worlds=[[train_world(b, e) for e in range(TRAIN_EPISODES)] for b in range(3)],
                  eval_worlds=[[eval_world(b, j) for j in range(EVAL_WORLDS)] for b in range(3)],
                  runtime=dict(python=sys.version, executable=sys.executable,
                               platform=platform.platform(), numpy=np.__version__, torch=str(torch.__version__),
                               torch_threads=torch.get_num_threads(),
                               torch_interop_threads=torch.get_num_interop_threads()),
                  source_identities=source_manifest(), expected_counts=expected_counts())
    (out / "checkpoints").mkdir()
    write_json(out / "config.json", config)
    endpoints = []
    def persist():
        summary["resources"] = elapsed(started)
        if start_usage is not None:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            summary["resources"]["process_cpu_since_admission_seconds"] = (
                usage.ru_utime + usage.ru_stime - start_usage.ru_utime - start_usage.ru_stime)
        write_json(out / "summary.json", summary)
    persist()
    with (out / "training.jsonl").open("x") as training_log, (out / "updates.jsonl").open("x") as update_log, (out / "evaluation.jsonl").open("x") as eval_log:
        def emit(stream, record):
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
        try:
            env = factory(train_world(0, 0))
            counts["environment_constructions"] += 1
            config["source_identities"] = source_manifest()
            write_json(out / "config.json", config)
            for block, master in enumerate(MASTERS):
                fit_started = clock()
                actor, critic = templates(master)
                aopt, copt = optimizers(actor, critic)
                initial = tensors(actor, critic)
                fit = dict(block=block, master=master, status="INCOMPLETE",
                           initial_tensor_sha256=tensor_identities(actor, critic),
                           actor_parameters=sum(p.numel() for p in actor.parameters()),
                           critic_parameters=sum(p.numel() for p in critic.parameters()),
                           initial_optimizer_entries=[len(aopt.state), len(copt.state)],
                           initial_checkpoint=save_checkpoint(out / "checkpoints" / f"{master}_initial.pt",
                               actor, critic, aopt, copt, endpoint="initial", master=master, launch_sha=launch_sha))
                fits.append(fit)
                counts["fits"] += 1
                for first in range(0, TRAIN_EPISODES, 2):
                    episodes = []
                    for episode_index in (first, first + 1):
                        episode, row = collect_episode(env, actor, critic, arm="train", master=master,
                            world_seed=train_world(block, episode_index), training=True,
                            out=out / "raw" / "train" / f"{master}_{episode_index:03d}.npz", counts=counts)
                        row.update(block=block, episode=episode_index)
                        row["raw"]["path"] = str(Path(row["raw"]["path"]).relative_to(out))
                        emit(training_log, row)
                        episodes.append(episode)
                    update_started = clock()
                    def emit_update(record):
                        emit(update_log, dict(record, block=block, master=master, rollout=first // 2,
                                              movement_from_fit_start=movement(initial, actor, critic)))
                    update(actor, critic, aopt, copt, episodes, counts, emit=emit_update)
                    cost = elapsed(update_started)
                    fit["update_wall_seconds"] = fit.get("update_wall_seconds", 0.0) + cost["wall_seconds"]
                    fit["update_cpu_seconds"] = fit.get("update_cpu_seconds", 0.0) + cost["cpu_seconds"]
                    fit["trained_episodes"] = first + 2
                    if (first + 2) % 32 == 0:
                        persist()
                        print(json.dumps(dict(event="train_checkpoint", master=master,
                                              episodes=first + 2, team_steps=counts["team_steps"])), flush=True)
                fit.update(status="COMPLETE", resources=elapsed(fit_started),
                           final_tensor_sha256=tensor_identities(actor, critic),
                           movement_from_fit_start=movement(initial, actor, critic),
                           final_checkpoint=save_checkpoint(out / "checkpoints" / f"{master}_final.pt",
                               actor, critic, aopt, copt, endpoint="final", master=master, launch_sha=launch_sha))
                initial_actor, _ = templates(master)
                endpoints.append((initial_actor.eval(), actor.eval()))
                persist()
            # No evaluation is exposed until all three final checkpoints are fixed.
            summary["evaluation_started_after_all_fits_complete"] = True
            for block, master in enumerate(MASTERS):
                initial_actor, final_actor = endpoints[block]
                for world in range(EVAL_WORLDS):
                    offset = (block + world) % len(ARMS)
                    for arm in ARMS[offset:] + ARMS[:offset]:
                        actor = initial_actor if arm in ("C", "I") else final_actor
                        _, row = collect_episode(env, actor, None, arm=arm, master=master,
                            world_seed=eval_world(block, world), training=False,
                            out=out / "raw" / "eval" / f"{master}_{arm}_{world:02d}.npz", counts=counts)
                        row.update(block=block, world=world)
                        row["raw"]["path"] = str(Path(row["raw"]["path"]).relative_to(out))
                        rows.append(row)
                        emit(eval_log, row)
                    persist()
            for key, expected in expected_counts().items():
                if counts[key] != expected:
                    raise RuntimeError(f"cost count mismatch {key}: {counts[key]} != {expected}")
            for name in ("training.jsonl", "updates.jsonl", "evaluation.jsonl", "config.json"):
                summary.setdefault("artifacts", {})[name] = identity(out / name, out)
            summary["status"] = "COMPLETE"
        except BaseException as exc:
            summary["limits"].append(f"{type(exc).__name__}: {exc}")
            (out / "traceback.txt").write_text(traceback.format_exc())
        finally:
            persist()
    return summary
