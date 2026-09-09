"""Engineering-only B01 fixture runner and prospective native command binding."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import (
    collect_episode,
    optimizer_for,
    update,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import (
    generator,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.study import (
    Deadline, clean_json, new_counts, write_summary,
)

from .geometry import (DENSE, REL, build_pair, parameter_summary,
                       geometry_snapshot as snapshot, geometry_exposure as exposure)


CARD = "docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_SCIENCE_CARD_20260908.md"
SOURCE_SHA = "d726acf63f8db47bd2e93e43cac8bbd27529d8ad"
MASTERS = (8201, 8202)
RECONCILED_MAIN_SHA = "6485fe0080abafe7521ed89f3425516407303d78"


def _fixture_check():
    """The tiny fixture relies on its caller's timeout; learner checks numerics."""
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
                 "episode": episode_index}, _fixture_check, counts,
                emit_episode, emit_diagnostic, limits, real=False,
                diagnostics=False, ratio_grouping="agent_compound"))
        records = update(actor, critic, optimizer, episodes, min(4, horizon),
                         _fixture_check, counts, ratio_grouping="agent_compound",
                         entropy_coef=0.01)
        eval_start = len(rows)
        for episode_index in range(eval_episodes):
            collect_episode(
                env, actor, critic, horizon, seed + 3000 + episode_index,
                generator(seed + 4000 + episode_index), generator(seed + 5000 + episode_index),
                {"pair_master": seed, "arm": kind, "phase": "eval",
                 "episode": episode_index}, _fixture_check, counts,
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


def _primary(rows, expected, mei=0.01, steps=None):
    values = {arm: {} for arm in (REL, DENSE, "H")}
    errors = {arm: [] for arm in values}
    for row in rows:
        if row.get("phase") != "eval":
            continue
        arm, episode, value = row.get("arm"), row.get("episode"), row.get("J")
        if arm not in values:
            for messages in errors.values():
                messages.append("unknown evaluation arm")
            continue
        if (type(episode) is not int or episode not in range(expected)
                or episode in values[arm]):
            errors[arm].append("duplicate or invalid episode index")
            continue
        if (type(value) not in (int, float) or not math.isfinite(value)
                or (steps is not None and row.get("steps") != steps)):
            errors[arm].append("missing, nonfinite or incomplete J")
            values[arm][episode] = None
        else:
            values[arm][episode] = value
    complete = {arm: set(values[arm]) == set(range(expected)) and not errors[arm]
                for arm in values}
    ids = sorted(e for e in set(values[REL]) & set(values[DENSE])
                 if values[REL][e] is not None and values[DENSE][e] is not None)
    differences = [values[REL][episode] - values[DENSE][episode] for episode in ids]
    result = {
        "complete": complete[REL] and complete[DENSE],
        "hover_complete": complete["H"],
        "errors": errors,
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
             eval_episodes=32, factory=None, start=None, clock=time.monotonic,
             arm_cap=1800.0, pair_cap=3600.0, publish=write_summary):
    """Run one declared B01 master, with native execution opt-in only.

    The fixture path is used by engineering checks. The native path is the
    prospective result-bearing entry point and is never called by this task.
    """
    start = clock() if start is None else start
    deadline = Deadline(start, arm_cap, pair_cap, clock)
    deadline.arm = REL
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
    pair = None
    rows = []
    limits = []
    arms = {}
    arm_info = None
    output_files = {name: (output / f"{name}.jsonl").open("w", encoding="utf-8")
                    for name in ("episodes", "rollouts")}

    def emit_episode(row):
        rows.append(row)
        output_files["episodes"].write(json.dumps(clean_json(row, limits), allow_nan=False) + "\n")
        output_files["episodes"].flush()

    def emit_diagnostic(_row):
        return None

    try:
        deadline.check()
        pair = build_pair(seed)
        deadline.check()
        base = 100000 * seed
        for kind in (REL, DENSE):
            if kind == DENSE:
                deadline.arm_start = deadline.check()
                deadline.arm = DENSE
            counts = new_counts(False)
            arm_info = {"fit_complete": False, "complete": False, "counts": counts}
            arms[kind] = arm_info
            deadline.check()
            actor, critic = pair[kind]
            env = factory(base + 1000)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1
            deadline.check()
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
                         "episode": episode_index}, deadline.check, counts,
                        emit_episode, emit_diagnostic, limits, real=not fixture,
                        diagnostics=False, ratio_grouping="agent_compound"))
                records = update(actor, critic, optimizer, episodes, min(32, horizon),
                                 deadline.check, counts,
                                 ratio_grouping="agent_compound", entropy_coef=0.01)
                output_files["rollouts"].write(json.dumps({
                    "pair_master": seed, "arm": kind, "rollout": rollout_index,
                    "episodes": 2, "steps": 2 * horizon, "epochs": records,
                    "optimizer_steps": counts["optimizer_steps"] - before["optimizer_steps"],
                }, allow_nan=False) + "\n")
                counts["rollouts"] += 1
                deadline.check()
            arm_info.update(fit_complete=True, training_counts=counts.copy(),
                            exposure=exposure(initial, actor, critic))
            torch.save({"actor": actor.state_dict(), "critic": critic.state_dict(),
                        "arm": kind, "seed": seed}, output / f"final_{kind}.pt")
            before_eval = len(rows)
            for episode_index in range(eval_episodes):
                collect_episode(
                    env, actor, critic, horizon, base + 2000 + episode_index,
                    generator(base + 3000 + episode_index), generator(base + 5000 + episode_index),
                    {"pair_master": seed, "arm": kind, "phase": "eval",
                     "episode": episode_index}, deadline.check, counts,
                    emit_episode, emit_diagnostic, limits, real=not fixture,
                    diagnostics=False, ratio_grouping="agent_compound")
            arm_info.update(complete=(len(rows) - before_eval == eval_episodes),
                            evaluation_episodes=len(rows) - before_eval,
                            counts=counts)
            arm_info["elapsed_wall"] = deadline.check() - deadline.arm_start
        # Fixed-zero-velocity reference on the DENSE environment's reset seeds.
        deadline.check()
        counts = new_counts(False)
        arms["H"] = {"complete": False, "counts": counts}
        env = factory(100000 * seed + 1000)
        counts["constructors"] += 1
        counts["constructor_resets"] += 1
        deadline.check()
        for episode_index in range(eval_episodes):
            collect_episode(
                env, None, None, horizon, 100000 * seed + 2000 + episode_index,
                None, None, {"pair_master": seed, "arm": "H", "phase": "eval",
                              "episode": episode_index}, deadline.check, counts,
                emit_episode, emit_diagnostic, limits, real=not fixture,
                diagnostics=False, ratio_grouping="agent_compound")
        arms["H"] = {"complete": counts["eval_episodes"] == eval_episodes,
                     "counts": counts}
    except Exception as error:
        limits.append(f"execution: {type(error).__name__}: {error}")
    finally:
        for stream in output_files.values():
            stream.close()
    summary = {
        "mode": "ENGINEERING_FIXTURE" if fixture else "UAV_B_EXPLORE",
        "object": "MGTAP-NATIVE-GROUND-GEOMETRY-B01",
        "card": CARD,
        "source_sha": SOURCE_SHA,
        "reconciled_main_sha": RECONCILED_MAIN_SHA,
        "launch_sha": launch_sha,
        "seed": seed,
        "declared_masters": list(MASTERS),
        "configuration": {"horizon": horizon, "train_episodes": train_episodes,
                          "eval_episodes": eval_episodes, "chunk": 32,
                          "ratio_grouping": "agent_compound", "entropy_coef": 0.01,
                          "primitive_g": True, "fixture": fixture,
                          "dtype": "float32", "device": "cpu", "threads": 1,
                          "arm_cap": arm_cap, "pair_cap": pair_cap},
        "arms": arms,
        "rows": rows,
        "primary": _primary(rows, eval_episodes, steps=horizon),
        "parameter_summary": parameter_summary(pair) if pair is not None else None,
        "cost_law": "C_a=C_init+131072*c_env+actor+1024*c_update+8192*c_eval+C_publication",
        "cost_unknowns": ["c_env+actor", "c_update", "c_eval", "C_init", "C_publication",
                          "incremental elapsed time", "activation memory", "RSS"],
        "limits": limits,
        "scientific_invocation": not fixture,
        "status": "COMPLETE" if not limits and len(arms) == 3 else "INCOMPLETE",
    }
    summary["counts"] = {key: sum(a["counts"][key] for a in arms.values())
                         for key in new_counts(False)}
    summary["counts"]["partial_episode_steps"] = (summary["counts"]["team_steps"]
                                                   - summary["counts"]["completed_episode_steps"])
    if not summary["primary"]["complete"] or not all(a["complete"] for a in arms.values()):
        summary["status"] = "INCOMPLETE"

    def observe_time():
        now = clock()
        summary["pair_elapsed_wall"] = now - start
        if deadline.arm in arms:
            arms[deadline.arm]["elapsed_wall"] = now - deadline.arm_start
        try:
            deadline.check()
        except TimeoutError as error:
            if str(error) not in limits:
                limits.append(str(error))
            summary["status"] = "CAP_BREACH"
        summary["cap_breach"] = deadline.breach is not None

    observe_time()
    try:
        publish(output / "summary.json", summary)
    except Exception as error:
        limits.append(f"publication: {type(error).__name__}: {error}")
        summary["status"] = "PUBLICATION_FAILED"
    observe_time()
    write_summary(output / "summary.json", summary)
    previous_breach = summary["cap_breach"]
    observe_time()
    if summary["cap_breach"] and not previous_breach:
        write_summary(output / "summary.json", summary)
    return clean_json(summary, limits)


def publish_fixture(path, summary):
    """Publish one explicit fixture JSON file for the toy acceptance check."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    return destination


def aggregate(summaries, expected=32):
    """Apply the fixed two-master rule; never average the available subset."""
    pairs, errors = {}, []
    for summary in summaries:
        seed = summary.get("seed")
        if seed not in MASTERS or seed in pairs:
            errors.append("unexpected or duplicate master")
            continue
        rows = summary.get("rows", [])
        try:
            primary = _primary(rows, expected, steps=256)
        except (TypeError, KeyError, AttributeError, ValueError) as error:
            errors.append(f"{seed}: corrupt rows: {error}")
            primary = _primary([], expected)
            rows = []
        if any(row.get("pair_master") != seed for row in rows):
            errors.append(f"{seed}: row master mismatch")
        config = summary.get("configuration", {})
        if (summary.get("mode") != "UAV_B_EXPLORE"
                or config.get("eval_episodes") != expected
                or config.get("horizon") != 256 or config.get("train_episodes") != 512):
            errors.append(f"{seed}: native endpoint binding mismatch")
        if not all(summary.get("arms", {}).get(arm, {}).get("fit_complete") for arm in (REL, DENSE)):
            errors.append(f"{seed}: incomplete training fit")
        pairs[seed] = {"seed": seed, "primary": primary,
                       "status": summary.get("status"), "limits": summary.get("limits", [])}
    missing = sorted(set(MASTERS) - pairs.keys())
    if missing:
        errors.append(f"missing masters: {missing}")
    complete = not errors and all(p["primary"]["complete"] for p in pairs.values())
    means = {str(seed): pairs[seed]["primary"]["REL_minus_DENSE"]["mean"]
             if seed in pairs else None for seed in MASTERS}
    delta = statistics.mean(means.values()) if complete else None
    ses = [pairs[seed]["primary"]["REL_minus_DENSE"]["conditional_se"]
           for seed in MASTERS] if complete else []
    return {"mode": "AGGREGATE", "declared_masters": list(MASTERS), "card": CARD,
            "pairs": [pairs[seed] for seed in MASTERS if seed in pairs], "errors": errors,
            "primary": {"complete": complete, "pair_means": means, "mean": delta,
                        "training_endpoint_sample_sd": statistics.stdev(means.values()) if complete else None,
                        "conditional_se": math.hypot(*ses) / 2 if complete and all(s is not None for s in ses) else None,
                        "reading": ("INCOMPLETE" if not complete else
                                    "REL_ABOVE_MEI" if delta > .01 else
                                    "REL_ADVERSE" if delta < -.01 else "INSIDE_MEI")}}


def aggregate_files(paths):
    summaries, errors = [], []
    for path in paths:
        try:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("summary must be an object")
            summaries.append(value)
        except (OSError, ValueError) as error:
            errors.append(f"{path}: {type(error).__name__}: {error}")
    try:
        result = aggregate(summaries)
    except (TypeError, KeyError, AttributeError, ValueError) as error:
        result = aggregate([])
        errors.append(f"corrupt summary: {error}")
    if errors:
        result["errors"].extend(errors)
        result["primary"].update(complete=False, mean=None, reading="INCOMPLETE",
                                 training_endpoint_sample_sd=None, conditional_se=None)
    return result


def prospective_native_binding(master, sha):
    """Literal LF wrapper and command, generated after the source commit.

    This only describes a later invocation; it neither stages nor launches it.
    A wrapper avoids agent-task's argument flattening of nested bash -lc.
    """
    cwd = f"/home/wu/hmasd-worktrees/mgtap_b01_{sha}"
    out = f"{cwd}/temp/directions/metric_ground_transport_allocation/exp/b01_{master}"
    python = "/home/wu/.venvs/hmasd/bin/python"
    wrapper = f"/home/wu/hmasd-inputs/mgtap-b01-{sha}/run_{master}.sh"
    handle = f"mgtap-b01-{master}-{sha}"
    payload = (f"#!/usr/bin/env bash\nset -euo pipefail\ncd {cwd}\n"
               f"{python} scripts/hmasd_resource_preflight.py admit-memory --out {out}/admission.json && "
               f"/usr/bin/time -q -f '%e' -o {out}/process_wall_seconds.txt "
               f"{python} scripts/run_mgtap_native_ground_geometry_b01.py "
               f"--native --master {master} --output {out} --arm-cap 1800 --pair-cap 3600\n")
    return {"cwd": cwd, "output": out, "wrapper_path": wrapper, "wrapper": payload,
            "handle": handle, "command": f"ssh hmasd-wsl-node '/usr/local/bin/agent-task run {handle} bash {wrapper}'"}


def main(argv=None, process_start=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--aggregate", nargs=2, type=Path)
    mode.add_argument("--fixture", action="store_true",
                        help="run only the bounded engineering fixture")
    mode.add_argument("--native", action="store_true",
                        help="run the prospective native pair after external admission")
    parser.add_argument("--master", type=int, default=8201, choices=MASTERS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--arm-cap", type=float, default=1800.0, choices=[1800.0])
    parser.add_argument("--pair-cap", type=float, default=3600.0, choices=[3600.0])
    args = parser.parse_args(argv)
    if args.aggregate:
        if args.output is None:
            parser.error("--aggregate requires --output summary.json")
        result = aggregate_files(args.aggregate)
        publish_fixture(args.output, result)
        return 0 if result["primary"]["complete"] else 1
    if args.native:
        if args.output is None:
            parser.error("--native requires --output")
        summary = run_pair(args.master, args.output, fixture=False, start=process_start,
                           arm_cap=args.arm_cap, pair_cap=args.pair_cap)
        print(json.dumps({"status": summary["status"],
                          "scientific_invocation": summary["scientific_invocation"],
                          "primary": summary["primary"]}, sort_keys=True))
        return 0 if summary["status"] == "COMPLETE" else 1
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
