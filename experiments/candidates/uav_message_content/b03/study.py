"""One fixed panel for four already-trained content assets."""

import json
import os
from pathlib import Path
import resource
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from .evaluate import collect_episode
from .model import ASSETS, actor_state_sha256, load_asset

SEED, HORIZON, EPISODES = 19461, 256, 32
ARMS = ("C", "B", "O", "L")
BASE = 100000 * SEED


def write_json(path, value):
    target = Path(path)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def counts_template():
    return dict(constructors=0, explicit_resets=0, eval_episodes=0,
                team_steps=0, native_step_calls=0, motion_samples=0,
                content_samples=0, broadcasts=0, attempts=0,
                delivered_packets=0, censored_packets=0,
                actor_forward_calls=0, critic_forward_calls=0,
                diagnostic_forward_calls=0,
                fits=0, optimizer_steps=0, evaluation_optimizer_steps=0)


def usage_delta(start, end):
    return dict(process_cpu_seconds=(end.ru_utime + end.ru_stime -
                                     start.ru_utime - start.ru_stime),
                process_lifetime_peak_rss_kib_linux=end.ru_maxrss,
                cpu_scope="RUSAGE_SELF user+system time delta",
                rss_scope="RUSAGE_SELF process-lifetime high-water mark; Linux ru_maxrss is KiB")


def run_asset(cell, assets_root, *, factory=make_real, horizon=HORIZON,
              episodes=EPISODES, check=lambda: None, publish=lambda: None,
              specification=ASSETS):
    out = Path(cell["directory"])
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    start_usage = resource.getrusage(resource.RUSAGE_SELF)
    cell["started_wall"] = time.time()
    actor = None
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episode_file:
        def emit(row):
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()
            cell["rows"].append(row)
            publish()

        try:
            check()
            actor, source = load_asset(cell["label"], assets_root,
                                       specification=specification)
            cell["source"] = source
            cell["initial_actor_sha256"] = actor_state_sha256(actor)
            if actor.training or any(p.requires_grad for p in actor.parameters()):
                raise RuntimeError("frozen actor contract failed")
            publish()
            env = factory(BASE + 2000)
            cell["counts"]["constructors"] += 1
            for e in range(episodes):
                metadata = dict(arm=cell["label"], asset=cell["label"],
                                master=source["master"], study_seed=SEED,
                                phase="eval", episode=e,
                                motion_seed=BASE + 3000 + e,
                                content_seed=BASE + 4000 + e,
                                checkpoint_sha256=source["sha256"])
                collect_episode(env, actor, cell["label"], horizon,
                                BASE + 2000 + e, BASE + 7000 + e,
                                generator(BASE + 3000 + e),
                                generator(BASE + 4000 + e),
                                metadata, cell["counts"], emit, check,
                                out / "raw" / f"eval_{e:02d}.npz",
                                require_quality=factory is make_real)
            cell["status"] = "COMPLETE"
        except Exception as error:
            cell["limits"].append(f"{type(error).__name__}: {error}")
        finally:
            if actor is not None:
                cell["final_actor_sha256"] = actor_state_sha256(actor)
            cell["finished_wall"] = time.time()
            cell["resources"] = usage_delta(
                start_usage, resource.getrusage(resource.RUSAGE_SELF))
            cell["resources"]["wall_seconds"] = cell["finished_wall"] - cell["started_wall"]
            publish()
    return cell


def validate_assets(assets, *, horizon=HORIZON, episodes=EPISODES):
    if [cell["label"] for cell in assets] != list(ARMS):
        return dict(complete=False, reading="INCOMPLETE")
    reference = assets[0]["rows"]
    for cell in assets:
        counts = cell["counts"]
        expected = dict(constructors=1, explicit_resets=episodes,
                        eval_episodes=episodes, team_steps=episodes * horizon,
                        native_step_calls=episodes * horizon,
                        motion_samples=5 * episodes * horizon,
                        content_samples=episodes * horizon if cell["label"] == "L" else 0,
                        broadcasts=episodes * horizon, attempts=episodes * horizon,
                        actor_forward_calls=episodes * horizon,
                        critic_forward_calls=0, diagnostic_forward_calls=0,
                        fits=0, optimizer_steps=0, evaluation_optimizer_steps=0)
        if cell["status"] != "COMPLETE" or any(
                counts.get(key) != value for key, value in expected.items()):
            return dict(complete=False, reading="INCOMPLETE")
        if cell.get("initial_actor_sha256") != cell.get("final_actor_sha256"):
            return dict(complete=False, reading="INCOMPLETE")
        if len(cell["rows"]) != episodes or [
                row["episode"] for row in cell["rows"]] != list(range(episodes)):
            return dict(complete=False, reading="INCOMPLETE")
        if any(row["steps"] != horizon or row["attempts"] != horizon or
               row["accepted_packets"] != horizon or row["collided_attempts"] != 0 or
               abs(row["charge_per_tick"] - .001) > 1e-10 or
               (cell["scientific_invocation"] and row["Q"] is None)
               for row in cell["rows"]):
            return dict(complete=False, reading="INCOMPLETE")
        if any((a["reset_seed"], a["channel_seed"], a["initial_scene_sha256"],
                a["channel_sequence_sha256"]) !=
               (b["reset_seed"], b["channel_seed"], b["initial_scene_sha256"],
                b["channel_sequence_sha256"]) for a, b in zip(reference, cell["rows"])):
            return dict(complete=False, reading="INCOMPLETE")
    return dict(complete=True, reading="COMPLETE_READY_FOR_SEPARATE_READER")


def run_batch(out, launch_sha, assets_root, seed=SEED, *,
              factory=make_real, horizon=HORIZON, episodes=EPISODES,
              check=lambda: None, specification=ASSETS):
    if seed != SEED or (factory is make_real and
                        (horizon, episodes) != (HORIZON, EPISODES)):
        raise ValueError("invalid fixed B03 contract")
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "summary.json").exists() or any(
            (output / arm).exists() for arm in ARMS):
        raise FileExistsError("scientific output already exists")
    torch.set_num_threads(1)
    start_usage = resource.getrusage(resource.RUSAGE_SELF)
    assets = []
    batch = dict(object="UAV-MESSAGE-CONTENT-B03", source_sha=launch_sha,
                 launch_sha=launch_sha, seed=seed, assets_root=str(assets_root),
                 status="INCOMPLETE", assets=assets, limits=[],
                 started_wall=time.time(),
                 expected=dict(arms=list(ARMS), episodes=128, team_steps=32768,
                               motion_samples=163840, content_samples=8192,
                               broadcasts=32768, actor_forward_calls=32768,
                               critic_forward_calls=0, diagnostic_forward_calls=0,
                               fits=0, optimizer_steps=0))

    def publish():
        batch["actual"] = {
            key: sum(cell["counts"][key] for cell in assets)
            for key in counts_template()}
        write_json(output / "summary.json", batch)

    publish()
    try:
        for arm in ARMS:
            declared = specification[arm]
            cell = dict(label=arm, arm=arm, master=declared["master"],
                        directory=str(output / arm), status="INCOMPLETE", limits=[],
                        rows=[], counts=counts_template(),
                        source=dict(path=str(Path(assets_root) / f"{arm}.pt"),
                                    sha256=declared["sha256"], bytes=declared["bytes"]),
                        scientific_invocation=factory is make_real)
            assets.append(cell)
            publish()
            run_asset(cell, assets_root, factory=factory, horizon=horizon,
                      episodes=episodes, check=check, publish=publish,
                      specification=specification)
            if cell["status"] != "COMPLETE":
                batch["limits"].append(f"{arm} incomplete")
                break
        batch["reduction"] = validate_assets(
            assets, horizon=horizon, episodes=episodes)
        batch["status"] = "COMPLETE" if batch["reduction"]["complete"] else "INCOMPLETE"
    except Exception as error:
        batch["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        batch["finished_wall"] = time.time()
        batch["resources"] = usage_delta(
            start_usage, resource.getrusage(resource.RUSAGE_SELF))
        batch["resources"].update(
            wall_seconds=batch["finished_wall"] - batch["started_wall"],
            torch_threads=torch.get_num_threads(),
            torch_interop_threads=torch.get_num_interop_threads())
        publish()
    return batch
