"""Admitted sequential B03 training replication and common native panel."""
from __future__ import annotations

from pathlib import Path
import resource
import time

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.runner import jsonable, write_json
from experiments.candidates.controller_composition.b01 import runner as b01
from experiments.candidates.controller_composition.b01.bindings import SOURCE, SOURCE_COMMIT
from experiments.candidates.controller_composition.b02 import runner as b02
from .bindings import (ARMS, BLOCKS, BOOTSTRAP_DRAWS, BOOTSTRAP_SEED, EVAL_CELLS,
                       EVAL_WORLD_BASE, OBJECT, TAG)
from .reducer import reduce_panel


def _prefix_identity(fit: dict) -> list[dict]:
    return [row["world"] for row in fit["rollouts"]]


def _whole_run_paths(value: object, block: str) -> object:
    """Translate B02's block-relative artifact locators for the outer summary."""
    if isinstance(value, list):
        return [_whole_run_paths(item, block) for item in value]
    if isinstance(value, dict):
        result = {key: _whole_run_paths(item, block) for key, item in value.items()}
        if {"path", "sha256", "bytes"} <= result.keys():
            result["path"] = f"{block}/{result['path']}"
        return result
    return value


def _complete_counts(fits: list[dict], cells: list[dict], spec: object) -> dict:
    count = {"fits": len(fits),
             "training_team_steps": sum(f["counts"]["team_steps"] for f in fits),
             "training_executed_learner_rows": sum(f["counts"]["executed_learner_rows"] for f in fits),
             "training_executed_partner_rows": sum(f["counts"]["executed_partner_rows"] for f in fits),
             "training_learner_inferred_rows": sum(f["counts"]["learner_inferred_rows"] for f in fits),
             "training_partner_inferred_rows": sum(f["counts"]["partner_inferred_rows"] for f in fits),
             "evaluation_team_steps": sum(c["counts"]["team_steps"] for c in cells),
             "evaluation_executed_action_rows": sum(c["counts"]["executed_action_rows"] for c in cells),
             "evaluation_inferred_action_rows": sum(c["counts"]["inferred_action_rows"] for c in cells),
             "evaluation_episodes": spec.eval_lanes * len(cells),
             "actor_optimizer_calls": sum(f["optimizer_calls"]["discoverer_actor"] for f in fits),
             "critic_optimizer_calls": sum(f["optimizer_calls"]["discoverer_critic"] for f in fits)}
    expected_train = len(BLOCKS) * len(ARMS) * spec.rollouts * spec.train_lanes * spec.horizon
    expected_eval = len(EVAL_CELLS) * spec.eval_lanes * spec.horizon
    if (count["training_team_steps"] != expected_train or
        count["training_executed_learner_rows"] != expected_train * 3 or
        count["training_executed_partner_rows"] != expected_train * 3 or
        count["evaluation_team_steps"] != expected_eval or
        count["evaluation_executed_action_rows"] != expected_eval * 6 or
        count["evaluation_inferred_action_rows"] != expected_eval * 12):
        raise ValueError("B03 fixed exposure/count mismatch")
    if spec == b02.SPEC and (expected_train != 1_440_000 or expected_eval != 304_000 or
                            count["actor_optimizer_calls"] != 202_500 or
                            count["critic_optimizer_calls"] != 202_500):
        raise ValueError("B03 full-spec optimizer/count mismatch")
    return count


def run_study(out: Path, launch_sha: str, admission: dict, checkpoint_paths: dict[int, Path],
              *, seed: int, command_start: float, spec: object = b02.SPEC) -> dict:
    if seed != BLOCKS["B1"]["learner_seed"] or launch_sha != admission["sha"]:
        raise ValueError("B03 seed/launch admission mismatch")
    out = Path(out).resolve()
    bound = admission.get("output_root")
    if bound is not None and out != Path(bound).resolve():
        raise ValueError("B03 output path disagrees with admission")
    if not out.is_dir():
        raise ValueError("B03 requires launcher-created output directory")
    occupied = [p.name for p in out.iterdir() if p.name.startswith(
        ("config.json", "progress.json", "summary.json", "B1", "B2", "shared", "raw"))]
    if occupied:
        raise ValueError(f"B03 scientific output already exists: {sorted(occupied)}")
    torch.set_num_threads(4)
    payloads, dependencies = b01.validate_sources(checkpoint_paths)
    config = {"object": OBJECT, "tag": TAG, "launch_sha": launch_sha,
              "admission": jsonable(admission), "seed": seed, "blocks": BLOCKS,
              "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_draws": BOOTSTRAP_DRAWS,
              "runtime_seed": b02.RUNTIME_SEED,
              "eval_world_base": EVAL_WORLD_BASE, "eval_cells": EVAL_CELLS,
              "arms": ARMS, "train_lanes": spec.train_lanes, "eval_lanes": spec.eval_lanes,
              "horizon": spec.horizon, "rollouts": spec.rollouts, "epochs": spec.ppo_epochs,
              "physical_n": 6, "learner_roles": [0, 1, 2], "partner_roles": [3, 4, 5],
              "source_commit": SOURCE_COMMIT, "source_bindings": SOURCE,
              "checkpoints": {str(k): {"path": str(checkpoint_paths[k]),
                                       "sha256": SOURCE[k]["checkpoint_sha256"]} for k in SOURCE},
              "source_dependencies_sha256": dependencies,
              "torch_threads": 4, "device": "cpu", "dtype": "float32",
              "training_reset": "constructor then explicit reset(seed=base+lane)",
              "evaluation_reset": "constructor then unseeded reset()"}
    write_json(out / "config.json", config)
    progress = {"status": "running", "phase": "training", "active_block": None,
                "active_fit": None, "active_rollout": None, "active_cell": None,
                "completed_fits": [], "completed_cells": [], "completed_rollouts": []}
    write_json(out / "progress.json", progress)
    fits: list[dict] = []
    cells: list[dict] = []
    snapshots: dict[str, dict[str, dict]] = {}
    previous_initial = None
    try:
        for block, identity in BLOCKS.items():
            block_out = out / block
            (block_out / "raw").mkdir(parents=True)
            snapshots[block] = {}
            assignment_rng = np.random.default_rng(identity["assignment_seed"])
            common_initial = None
            for arm in ARMS:
                progress.update(active_block=block, active_fit=arm, active_rollout=None)
                write_json(out / "progress.json", progress)
                # The B02 fit writes its own progress in the block namespace.
                block_progress = {"block": block, "completed_rollouts": [], "active_fit": arm}
                fit, snapshot = b02._fit(
                    arm, payloads, assignment_rng, block_out, launch_sha, block_progress, spec,
                    world_base=identity["train_world_base"],
                    learner_seed=identity["learner_seed"], object_name=OBJECT)
                if fit["config"]["seed"] != identity["learner_seed"]:
                    raise ValueError("B03 learner seed did not reach config")
                if fit["learner_seed"] != identity["learner_seed"]:
                    raise ValueError("B03 learner seed did not reach fit")
                expected_sampler = int(np.random.SeedSequence(
                    [identity["learner_seed"], 0x484D4153, 0]
                ).generate_state(1, dtype=np.uint64)[0])
                if fit["rollout_sampler_seed"] != expected_sampler:
                    raise ValueError("B03 learner seed did not reach sampler")
                expected_worlds = [list(range(identity["train_world_base"] + 100 * r,
                                               identity["train_world_base"] + 100 * r + spec.train_lanes))
                                   for r in range(1, spec.rollouts + 1)]
                if [row["world"]["lane_world_seeds"] for row in fit["rollouts"]] != expected_worlds:
                    raise ValueError("B03 training world addresses differ")
                if arm == "M" and any(sorted(row["assignment"]) !=
                                      [1] * (spec.train_lanes // 2) + [2] * (spec.train_lanes // 2)
                                      for row in fit["rollouts"]):
                    raise ValueError("B03 M assignment differs from half/half")
                if common_initial is None:
                    common_initial = fit
                    initial_path = block_out / fit["initial_checkpoint"]["path"]
                    snapshots[block]["I"] = {
                        "payload": torch.load(initial_path, map_location="cpu", weights_only=True),
                        "digest": fit["initial_digest"]}
                else:
                    for key in ("initial_digest", "initial_optimizer_state_digest",
                                "initial_normalizers", "rollout_sampler_seed",
                                "initial_sampler_rng_sha256"):
                        if fit[key] != common_initial[key]:
                            raise ValueError(f"B03 within-block {key} mismatch")
                    for a, b in zip(_prefix_identity(common_initial), _prefix_identity(fit)):
                        for key in ("lane_world_seeds", "states", "observations",
                                    "uav_positions", "user_positions"):
                            if a[key] != b[key]:
                                raise ValueError(f"B03 within-block physical reset {key} mismatch")
                fits.append({"block": block, **_whole_run_paths(fit, block)})
                snapshots[block][arm] = snapshot
                progress["completed_rollouts"].extend(
                    [block, arm, rollout] for rollout in range(1, spec.rollouts + 1))
                progress["completed_fits"].append([block, arm])
                write_json(out / "progress.json", progress)
            if previous_initial is not None:
                if (common_initial["initial_digest"] == previous_initial["initial_digest"] or
                    common_initial["initial_sampler_rng_sha256"] == previous_initial["initial_sampler_rng_sha256"] or
                    common_initial["rollout_sampler_seed"] == previous_initial["rollout_sampler_seed"] or
                    _prefix_identity(common_initial)[0]["lane_world_seeds"] ==
                    _prefix_identity(previous_initial)[0]["lane_world_seeds"]):
                    raise ValueError("B03 independent blocks share initialization or worlds")
            previous_initial = common_initial
        progress.update(phase="evaluation", active_fit=None, active_rollout=None)
        write_json(out / "progress.json", progress)
        first_identity = None
        first_per_world = None
        for block, learner, partner in EVAL_CELLS:
            cell_out = out / block
            (cell_out / "raw").mkdir(parents=True, exist_ok=True)
            progress.update(active_block=block, active_cell=[block, learner, partner])
            write_json(out / "progress.json", progress)
            row = b02._eval_cell(learner, partner, snapshots.get(block, {}), payloads,
                                 cell_out, spec, world_base=EVAL_WORLD_BASE,
                                 learner_seed=BLOCKS[block]["learner_seed"] if block in BLOCKS else seed)
            if row["cell"] != [learner, partner] or row["world_seeds"] != list(range(
                    EVAL_WORLD_BASE, EVAL_WORLD_BASE + spec.eval_lanes)):
                raise ValueError("B03 evaluation cell/world identity mismatch")
            if first_identity is None:
                first_identity, first_per_world = (row["initial_world_identity"],
                                                   row["initial_world_identity_per_world"])
            elif (row["initial_world_identity"] != first_identity or
                  row["initial_world_identity_per_world"] != first_per_world):
                raise ValueError("B03 evaluation worlds differ across cells")
            cells.append({"block": block, **_whole_run_paths(row, block)})
            write_json(cell_out / f"eval_{learner}_p{partner}.json", row)
            progress["completed_cells"].append([block, learner, partner])
            write_json(out / "progress.json", progress)
        j = np.stack([row["per_world"]["J"] for row in cells], axis=1)
        s = np.stack([row["per_world"]["S"] for row in cells], axis=1)
        analysis = reduce_panel(j, s)
        counts = _complete_counts(fits, cells, spec)
        artifacts = [b02._artifact(path, out)
                     for block in (*BLOCKS, "shared")
                     for path in sorted((out / block / "raw").rglob("*")) if path.is_file()]
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary = {"object": OBJECT, "status": "complete", "launch_sha": launch_sha,
                   "config_sha256": b01.sha256(out / "config.json"),
                   "source_bindings": SOURCE, "source_dependencies_sha256": dependencies,
                   "fits": fits, "cells": cells, "analysis": analysis, "counts": counts,
                   "telemetry": {"wall_seconds": time.perf_counter() - command_start,
                                 "process_cpu_seconds": usage.ru_utime + usage.ru_stime,
                                 "peak_process_rss_kib": usage.ru_maxrss,
                                 "raw_bytes": sum(item["bytes"] for item in artifacts)},
                   "artifacts": artifacts,
                   "interpretation_limit": "Two exploratory training pairs; world intervals exclude training uncertainty."}
        write_json(out / "summary.json", summary)
        progress.update(status="complete", phase="complete", active_cell=None,
                        summary_sha256=b01.sha256(out / "summary.json"))
        write_json(out / "progress.json", progress)
        return summary
    except Exception as exc:
        progress.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        write_json(out / "progress.json", progress)
        raise
