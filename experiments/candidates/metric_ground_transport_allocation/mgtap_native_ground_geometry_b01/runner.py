"""Engineering-only B01 fixture runner and prospective native command binding."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    collect_episode,
    optimizer_for,
    update,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import (
    exposure,
    generator,
    snapshot,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.study import new_counts

from .geometry import DENSE, REL, build_pair, parameter_summary


CARD = "docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_SCIENCE_CARD_20260908.md"
SOURCE_SHA = "d726acf63f8db47bd2e93e43cac8bbd27529d8ad"
MASTERS = (8201, 8202)


def _check_finite():
    return None


def run_fixture_pair(seed=8201, horizon=8, train_episodes=2, eval_episodes=2):
    """Run a tiny non-scientific fixture through the source learner APIs.

    This helper is intentionally not a native study command. It exists only
    to prove the adapter's forward/backward, source credit and publication
    plumbing without creating a scientific result root or consuming B01
    exposure.
    """
    if horizon <= 0 or train_episodes <= 0 or eval_episodes <= 0:
        raise ValueError("fixture dimensions must be positive")
    pair = build_pair(seed)
    rows = []
    limits = []
    arms = {}
    for kind in (REL, DENSE):
        actor, critic = pair[kind]
        env = SyntheticAdapter(seed + 1, horizon=horizon)
        counts = new_counts(False)
        initial = snapshot(actor, critic)
        optimizer = optimizer_for(actor, critic)
        streams = {"train": generator(100000 * seed + 21),
                   "eval": generator(100000 * seed + 3000)}

        def emit_episode(row):
            rows.append(row)

        def emit_diagnostic(_row):
            return None

        episodes = []
        for episode_index in range(train_episodes):
            episodes.append(collect_episode(
                env, actor, critic, horizon, seed + 1000 + episode_index,
                streams["train"], generator(seed + 2000 + episode_index),
                {"pair_master": seed, "arm": kind, "phase": "train",
                 "episode": episode_index}, _check_finite, counts,
                emit_episode, emit_diagnostic, limits, real=False,
                diagnostics=False, ratio_grouping="agent_compound"))
        records = update(actor, critic, optimizer, episodes, min(4, horizon),
                         _check_finite, counts, ratio_grouping="agent_compound",
                         entropy_coef=0.01)
        eval_start = len(rows)
        for episode_index in range(eval_episodes):
            collect_episode(
                env, actor, critic, horizon, seed + 3000 + episode_index,
                generator(seed + 4000 + episode_index), generator(seed + 5000 + episode_index),
                {"pair_master": seed, "arm": kind, "phase": "eval",
                 "episode": episode_index}, _check_finite, counts,
                emit_episode, emit_diagnostic, limits, real=False,
                diagnostics=False, ratio_grouping="agent_compound")
        arms[kind] = {
            "training_episodes": train_episodes,
            "evaluation_episodes": len(rows) - eval_start,
            "optimizer_steps": counts["optimizer_steps"],
            "exposure": exposure(initial, actor, critic),
            "epochs": records,
        }
    return {
        "mode": "ENGINEERING_FIXTURE",
        "card": CARD,
        "source_sha": SOURCE_SHA,
        "seed": seed,
        "arms": arms,
        "rows": rows,
        "parameter_summary": parameter_summary(pair),
        "limits": limits,
        "status": "COMPLETE" if not limits else "COMPLETE_WITH_LIMITS",
        "scientific_invocation": False,
    }


def _primary(rows, expected, mei=0.01):
    values = {arm: {row["episode"]: row["J"] for row in rows
                    if row["arm"] == arm and row["phase"] == "eval"}
              for arm in (REL, DENSE, "H")}
    complete = {arm: set(values[arm]) == set(range(expected))
                and all(math.isfinite(value) for value in values[arm].values())
                for arm in values}
    ids = sorted(set(values[REL]) & set(values[DENSE]))
    differences = [values[REL][episode] - values[DENSE][episode] for episode in ids]
    result = {
        "complete": complete[REL] and complete[DENSE],
        "hover_complete": complete["H"],
        "J": {arm: [values[arm][episode] for episode in sorted(values[arm])]
              for arm in values},
        "episode_ids": {arm: sorted(values[arm]) for arm in values},
        "REL_minus_DENSE": {
            "differences": differences,
            "episode_ids": ids,
            "complete": complete[REL] and complete[DENSE],
            "mean": statistics.mean(differences) if differences else None,
            "conditional_se": (statistics.stdev(differences) / math.sqrt(len(differences))
                                if len(differences) > 1 else None),
        },
    }
    delta = result["REL_minus_DENSE"]["mean"]
    if result["complete"] and delta is not None:
        result["reading"] = ("REL_ABOVE_MEI" if delta > mei else
                              "REL_ADVERSE" if delta < -mei else "INSIDE_MEI")
    else:
        result["reading"] = "INCOMPLETE"
    return result


def run_pair(seed, output, *, fixture=False, horizon=256, train_episodes=512,
             eval_episodes=32, factory=None):
    """Run one declared B01 master, with native execution opt-in only.

    The fixture path is used by engineering checks. The native path is the
    prospective result-bearing entry point and is never called by this task.
    """
    if seed not in MASTERS:
        raise ValueError(f"B01 master must be one of {MASTERS}")
    if any(value <= 0 for value in (horizon, train_episodes, eval_episodes)):
        raise ValueError("run dimensions must be positive")
    if train_episodes % 2:
        raise ValueError("training episodes must form complete two-episode rollouts")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if factory is None:
        if fixture:
            factory = lambda constructor_seed: SyntheticAdapter(constructor_seed, horizon=horizon)
        else:
            from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
            factory = make_real
    try:
        launch_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[4], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        launch_sha = None
    pair = build_pair(seed)
    rows = []
    limits = []
    arms = {}
    output_files = {name: (output / f"{name}.jsonl").open("w", encoding="utf-8")
                    for name in ("episodes", "rollouts")}

    def emit_episode(row):
        rows.append(row)
        output_files["episodes"].write(json.dumps(row, allow_nan=False) + "\n")
        output_files["episodes"].flush()

    def emit_diagnostic(_row):
        return None

    try:
        base = 100000 * seed
        for kind in (REL, DENSE):
            actor, critic = pair[kind]
            env = factory(base + 1000)
            counts = new_counts(False)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1
            initial = snapshot(actor, critic)
            optimizer = optimizer_for(actor, critic)
            train_velocity = generator(base + 21)
            for rollout_index in range(train_episodes // 2):
                before = counts.copy()
                episodes = []
                for offset in (0, 1):
                    episode_index = 2 * rollout_index + offset
                    episodes.append(collect_episode(
                        env, actor, critic, horizon, base + 1000 + episode_index,
                        train_velocity, generator(base + 4000 + episode_index),
                        {"pair_master": seed, "arm": kind, "phase": "train",
                         "episode": episode_index}, _check_finite, counts,
                        emit_episode, emit_diagnostic, limits, real=not fixture,
                        diagnostics=False, ratio_grouping="agent_compound"))
                records = update(actor, critic, optimizer, episodes, min(32, horizon),
                                 _check_finite, counts,
                                 ratio_grouping="agent_compound", entropy_coef=0.01)
                output_files["rollouts"].write(json.dumps({
                    "pair_master": seed, "arm": kind, "rollout": rollout_index,
                    "episodes": 2, "steps": 2 * horizon, "epochs": records,
                    "optimizer_steps": counts["optimizer_steps"] - before["optimizer_steps"],
                }, allow_nan=False) + "\n")
            arm_info = {
                "fit_complete": True,
                "training_counts": counts.copy(),
                "exposure": exposure(initial, actor, critic),
            }
            torch.save({"actor": actor.state_dict(), "critic": critic.state_dict(),
                        "arm": kind, "seed": seed}, output / f"final_{kind}.pt")
            before_eval = len(rows)
            for episode_index in range(eval_episodes):
                collect_episode(
                    env, actor, critic, horizon, base + 2000 + episode_index,
                    generator(base + 3000 + episode_index), generator(base + 5000 + episode_index),
                    {"pair_master": seed, "arm": kind, "phase": "eval",
                     "episode": episode_index}, _check_finite, counts,
                    emit_episode, emit_diagnostic, limits, real=not fixture,
                    diagnostics=False, ratio_grouping="agent_compound")
            arm_info.update(complete=(len(rows) - before_eval == eval_episodes),
                            evaluation_episodes=len(rows) - before_eval,
                            counts=counts)
            arms[kind] = arm_info
        # Fixed-zero-velocity reference on the DENSE environment's reset seeds.
        env = factory(100000 * seed + 1000)
        counts = new_counts(False)
        counts["constructors"] += 1
        counts["constructor_resets"] += 1
        for episode_index in range(eval_episodes):
            collect_episode(
                env, None, None, horizon, 100000 * seed + 2000 + episode_index,
                None, None, {"pair_master": seed, "arm": "H", "phase": "eval",
                              "episode": episode_index}, _check_finite, counts,
                emit_episode, emit_diagnostic, limits, real=not fixture,
                diagnostics=False, ratio_grouping="agent_compound")
        arms["H"] = {"complete": counts["eval_episodes"] == eval_episodes,
                     "counts": counts}
    finally:
        for stream in output_files.values():
            stream.close()
    summary = {
        "mode": "ENGINEERING_FIXTURE" if fixture else "UAV_B_EXPLORE",
        "object": "MGTAP-NATIVE-GROUND-GEOMETRY-B01",
        "card": CARD,
        "source_sha": SOURCE_SHA,
        "launch_sha": launch_sha,
        "seed": seed,
        "declared_masters": list(MASTERS),
        "configuration": {"horizon": horizon, "train_episodes": train_episodes,
                          "eval_episodes": eval_episodes, "chunk": 32,
                          "ratio_grouping": "agent_compound", "entropy_coef": 0.01,
                          "primitive_g": True, "fixture": fixture},
        "arms": arms,
        "rows": rows,
        "primary": _primary(rows, eval_episodes),
        "parameter_summary": parameter_summary(pair),
        "cost_law": "C_a=C_init+131072*c_env+actor+1024*c_update+8192*c_eval+C_publication",
        "cost_unknowns": ["c_env+actor", "c_update", "c_eval", "C_init", "C_publication",
                          "incremental elapsed time", "activation memory", "RSS"],
        "limits": limits,
        "scientific_invocation": not fixture,
        "status": "COMPLETE" if not limits else "COMPLETE_WITH_LIMITS",
    }
    publish_fixture(output / "summary.json", summary)
    return summary


def publish_fixture(path, summary):
    """Publish one explicit fixture JSON file for the toy acceptance check."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    return destination


def prospective_native_command():
    """Return the literal future binding without executing it."""
    return ("ssh hmasd-wsl-node "
            "'/usr/local/bin/agent-task mgtap-native-ground-geometry-b01-8201 "
            "-- bash -lc \"cd /home/wu/hmasd-worktrees/<EXACT_SHA> && "
            "/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py "
            "admit-memory --out <REMOTE_RUN_ROOT>/admission.json && "
            "/home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_native_ground_geometry_b01.py "
            "--native --master 8201 --output <REMOTE_RUN_ROOT>\"'")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true",
                        help="run only the bounded engineering fixture")
    parser.add_argument("--native", action="store_true",
                        help="run the prospective native pair after external admission")
    parser.add_argument("--master", type=int, default=8201, choices=MASTERS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.native:
        if args.output is None:
            parser.error("--native requires --output")
        summary = run_pair(args.master, args.output, fixture=False)
        print(json.dumps({"status": summary["status"],
                          "scientific_invocation": summary["scientific_invocation"],
                          "primary": summary["primary"]}, sort_keys=True))
        return 0
    if not args.fixture:
        parser.error("B01 source engineering exposes only --fixture or --native")
    summary = run_fixture_pair(seed=args.master)
    if args.output:
        publish_fixture(args.output, summary)
    print(json.dumps({"status": summary["status"],
                      "scientific_invocation": summary["scientific_invocation"],
                      "parameter_summary": summary["parameter_summary"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
