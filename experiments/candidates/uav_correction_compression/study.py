"""Exactly seven private frozen programs on the bound new 32-world panel."""

import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import time

import torch

from experiments.candidates.uav_message_content.b06.collector import collect_episode
from experiments.candidates.uav_message_content.b06.study import new_counts, resources_since
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from .model import TimedActor, load_programs, state_hashes

ARMS = ("D19701", "C19701", "D19702", "C19702", "D19703", "C19703", "B40")
INPUTS_PATH = Path(__file__).with_name("b01_inputs.json")
INPUTS_SHA256 = "c2601ec8175faa9b0b3c26b90993583ee4cb919bb8746168ae2f0f7b843b42fa"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load_inputs():
    content = INPUTS_PATH.read_bytes()
    if hashlib.sha256(content).hexdigest() != INPUTS_SHA256:
        raise ValueError("fixed B01 inputs digest mismatch")
    inputs = json.loads(content)
    if (inputs["horizon"] != 256 or len(inputs["worlds"]) != 32
            or [a["master"] for a in inputs["assets"]] != [19701, 19702, 19703]):
        raise ValueError("fixed B01 panel mismatch")
    for world, row in enumerate(inputs["worlds"]):
        if row != dict(world=world, scene_seed=1980002000 + world,
                       channel_seed=1980007000 + world, motion_seed=1980003000 + world):
            raise ValueError("fixed B01 tuple mismatch")
    return inputs


def expected_counts(horizon=256, worlds=32):
    result = new_counts()
    steps = horizon * worlds
    result.update(constructors=1, explicit_resets=worlds, final_eval_episodes=worlds,
                  final_eval_team_steps=steps, team_steps=steps, native_step_calls=steps,
                  motion_samples=steps * 5, broadcasts=steps, attempts=steps,
                  behavior_actor_forward_calls=steps, behavior_actor_forward_rows=steps * 5)
    # Delivery/censor counts depend on actual channel tuples, not a nominal count.
    return {key: value for key, value in result.items()
            if key not in ("delivered_packets", "censored_packets")}


def rotating_order(world):
    offset = world % len(ARMS)
    return ARMS[offset:] + ARMS[:offset]


def measured(cost, method, *args):
    wall, cpu = time.perf_counter_ns(), time.process_time_ns()
    try:
        return method(*args)
    finally:
        cost["calls"] += 1
        cost["wall_ns"] += time.perf_counter_ns() - wall
        cost["process_cpu_ns"] += time.process_time_ns() - cpu


def new_cost():
    return dict(calls=0, wall_ns=0, process_cpu_ns=0)


def run_batch(out, launch_sha, parent_checkpoint, endpoint_dir, *, seed=19801,
              factory=make_real, check=lambda: None, worker_start=None):
    """No retry/resume. The admitted CLI alone enables native scientific effects."""
    if seed != 19801:
        raise ValueError("fixed B01 seed")
    out, parent_checkpoint, endpoint_dir = map(Path, (out, parent_checkpoint, endpoint_dir))
    if not parent_checkpoint.is_absolute() or not endpoint_dir.is_absolute():
        raise ValueError("checkpoint inputs must be absolute")
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json",
               "stdout.log", "stderr.log"}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError("B01 refuses previous/unknown output; no automatic retry")
    usage = resource.getrusage(resource.RUSAGE_SELF)
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    json_cost = new_cost()
    batch = dict(object="UAV-CORRECTION-COMPRESSION-B01", status="INCOMPLETE",
                 launch_sha=launch_sha, seed=seed, inputs_sha256=INPUTS_SHA256,
                 cells=[], actual=new_counts(), limits=[], arm_order=[],
                 checkpoint_bindings={}, timing=dict(json_output=json_cost),
                 timing_scope=dict(actor_forward="actual full base+GRU+composition call; two clock reads per boundary",
                     episode_loop="collector reset/host/channel/sampler/trace/compressed NPZ+raw hash; excludes JSON writes",
                     json_output="cumulative completed JSON/config/stream writes; final self-report write excluded"))
    programs, envs = {}, {}
    cells = {}
    try:
        check()
        inputs = load_inputs()
        horizon, worlds = inputs["horizon"], len(inputs["worlds"])
        batch["configuration"] = dict(horizon=horizon, final_eval=worlds, arms=list(ARMS),
            fits=0, optimizer_updates=0, device="cpu", dtype="float32", inputs_sha256=INPUTS_SHA256,
            torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
            blas_threads={key: os.environ.get(key) for key in
                         ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
        batch["expected"] = {key: 7 * value for key, value in expected_counts(horizon, worlds).items()}
        measured(json_cost, write_json, out / "inputs.json", inputs)
        measured(json_cost, write_json, out / "config.json", dict(batch["configuration"],
                  launch_sha=launch_sha, seed=seed, inputs=inputs))
        parent_content = parent_checkpoint.read_bytes()
        if len(parent_content) != inputs["parent"]["bytes"]:
            raise ValueError("parent checkpoint byte count mismatch")
        batch["checkpoint_bindings"]["parent"] = dict(inputs["parent"], actual_path=str(parent_checkpoint))
        endpoint_contents = {}
        for asset in inputs["assets"]:
            path = endpoint_dir / asset["checkpoint"]["staged_name"]
            endpoint_contents[asset["endpoint"]] = path.read_bytes()
            if len(endpoint_contents[asset["endpoint"]]) != asset["checkpoint"]["bytes"]:
                raise ValueError("endpoint checkpoint byte count mismatch")
            batch["checkpoint_bindings"][asset["endpoint"]] = dict(asset["checkpoint"],
                actual_path=str(path), source_sha=asset["source_sha"], master=asset["master"])
        programs = load_programs(parent_content, inputs, endpoint_contents)
        del parent_content, endpoint_contents
        for arm in ARMS:
            actor = programs[arm]
            directory = out / arm
            directory.mkdir()
            (directory / "raw").mkdir()
            (directory / "episodes.jsonl").touch(exist_ok=False)
            cell = dict(arm=arm, master=19451 if arm == "B40" else int(arm[1:]),
                directory=arm, launch_sha=launch_sha, status="INCOMPLETE", rows=[], counts=new_counts(),
                initial_tensor_sha256=state_hashes(actor), log_std=actor.log_std.detach().tolist(),
                actor_trainable_parameters=sum(p.numel() for p in actor.parameters() if p.requires_grad),
                actor_parameters=sum(p.numel() for p in actor.parameters()),
                timing=dict(actor_forward=new_cost(), episode_loop=new_cost(), json_output=new_cost()))
            if arm.startswith("C"):
                cell["constant_float32"] = actor.constant.tolist()
            cells[arm] = cell
            batch["cells"].append(cell)
            check()
            envs[arm] = factory(inputs["worlds"][0]["scene_seed"])
            cell["counts"]["constructors"] += 1
            programs[arm] = TimedActor(actor)
        batch["timing"]["input_and_construction"] = dict(wall_ns=time.perf_counter_ns() - start_wall,
                                                         process_cpu_ns=time.process_time_ns() - start_cpu)
        for world in inputs["worlds"]:
            order = rotating_order(world["world"])
            actual_order = dict(world=world["world"], arms=[])
            batch["arm_order"].append(actual_order)
            for arm in order:
                actual_order["arms"].append(arm)
                batch["active_cell"] = dict(arm=arm, world=world["world"])
                actor, cell = programs[arm], cells[arm]
                before = actor.timing.copy()
                pending = []
                raw_relative = f"{arm}/raw/final_{world['world']:02d}.npz"
                wall, cpu = time.perf_counter_ns(), time.process_time_ns()
                try:
                    collect_episode(envs[arm], actor, None, "B40" if arm == "B40" else "D",
                        horizon, world["scene_seed"], world["channel_seed"], generator(world["motion_seed"]),
                        dict(phase="final_eval", arm=arm, master=cell["master"], episode=world["world"],
                             world=world["world"], motion_seed=world["motion_seed"]),
                        cell["counts"], pending.append, check, raw_path=out / raw_relative)
                finally:
                    loop = dict(wall_ns=time.perf_counter_ns() - wall,
                                process_cpu_ns=time.process_time_ns() - cpu)
                    forward = {key: actor.timing[key] - before[key] for key in before}
                    for key in loop:
                        cell["timing"]["episode_loop"][key] += loop[key]
                    cell["timing"]["episode_loop"]["calls"] += 1
                    for key in forward:
                        cell["timing"]["actor_forward"][key] += forward[key]
                    for row in pending:
                        row["raw"] = raw_relative
                        row["raw_bytes"] = (out / raw_relative).stat().st_size
                        row["timing"] = dict(actor_forward=forward, episode_loop=loop)
                        cell["rows"].append(row)
                        def append_row():
                            with (out / arm / "episodes.jsonl").open("a", encoding="utf-8") as stream:
                                stream.write(json.dumps(row, allow_nan=False) + "\n")
                                stream.flush()
                        measured(cell["timing"]["json_output"], append_row)
                measured(cell["timing"]["json_output"], write_json, out / arm / "summary.json", cell)
                batch["actual"] = {key: sum(c["counts"][key] for c in batch["cells"]) for key in new_counts()}
                measured(json_cost, write_json, out / "summary.json", batch)
        for cell in batch["cells"]:
            expected = expected_counts(horizon, worlds)
            if any(cell["counts"][key] != value for key, value in expected.items()):
                raise RuntimeError(f"fixed evaluation counts differ: {cell['arm']}")
            if cell["timing"]["actor_forward"]["calls"] != horizon * worlds:
                raise RuntimeError("actual actor timing call count differs")
            cell["status"] = "COMPLETE"
        batch["status"] = "COMPLETE"
    except Exception as error:
        batch["limits"].append(f"{type(error).__name__}: {error}")
        batch["failed_cell"] = batch.get("active_cell")
    finally:
        for cell in batch["cells"]:
            actor = programs.get(cell["arm"])
            if isinstance(actor, TimedActor):
                actor = actor.actor
            if actor is not None:
                cell["final_tensor_sha256"] = state_hashes(actor)
                cell["frozen_equal"] = cell["initial_tensor_sha256"] == cell["final_tensor_sha256"]
                cell["parameter_displacement"] = 0.0 if cell["frozen_equal"] else None
                if not cell["frozen_equal"]:
                    cell["status"] = batch["status"] = "INCOMPLETE"
                    batch["limits"].append(f"frozen state changed: {cell['arm']}")
            cell["episode_stream_sha256"] = sha256(out / cell["directory"] / "episodes.jsonl")
            cell["raw_bytes"] = sum(path.stat().st_size for path in (out / cell["directory"] / "raw").iterdir())
            # Final self-report writes cannot include their own completed duration.
            write_json(out / cell["directory"] / "summary.json", cell)
        for env in envs.values():
            close = getattr(env, "close", None)
            if close is not None:
                try:
                    close()
                except Exception as error:
                    batch["limits"].append(f"environment close: {type(error).__name__}: {error}")
                    batch["status"] = "INCOMPLETE"
        batch["actual"] = {key: sum(c["counts"][key] for c in batch["cells"]) for key in new_counts()}
        batch["frozen_equal"] = bool(batch["cells"]) and all(c.get("frozen_equal", False) for c in batch["cells"])
        batch["active_cell"] = None
        batch["resources"] = dict(resources_since(usage), host=platform.node(), platform=platform.platform(),
                                   torch_version=torch.__version__, wall_seconds=(time.perf_counter_ns() - start_wall) / 1e9)
        if worker_start is not None:
            batch["worker_resources"] = dict(resources_since(worker_start[0]),
                wall_seconds=(time.perf_counter_ns() - worker_start[1]) / 1e9,
                scope="admitted worker before torch import through final evidence preparation; final summary write excluded")
        batch["timing"]["batch"] = dict(wall_ns=time.perf_counter_ns() - start_wall,
                                         process_cpu_ns=time.process_time_ns() - start_cpu)
        batch["output_bytes_before_final_summary"] = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
        write_json(out / "summary.json", batch)
    return batch
