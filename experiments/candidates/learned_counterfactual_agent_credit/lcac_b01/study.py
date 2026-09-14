"""One fixed two-arm comparison, direct output publication and panel arithmetic."""
import json
import math
from pathlib import Path
import statistics
import subprocess
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from .learner import collect_episode, new_counts, optimizer_for, update
from .policy import build_pair, movement, snapshot


CARD = "docs/research/candidates/learned_counterfactual_agent_credit/LCAC_B01_SCIENCE_CARD_20260914.md"


def primary(rows, expected=32, horizon=256):
    panels = {arm: [r for r in rows if r["arm"] == arm and r["phase"] == "eval"]
              for arm in ("V", "Q")}
    for arm, panel in panels.items():
        if len(panel) != expected or sorted(r["episode"] for r in panel) != list(range(expected)):
            raise ValueError(f"incomplete or duplicate final panel for {arm}")
        panel.sort(key=lambda r: r["episode"])
        if any(r["steps"] != horizon or not math.isfinite(r["J"]) or not math.isfinite(r["reward_sum"])
               or abs(r["J"] - r["reward_sum"] / horizon) > 1e-7 for r in panel):
            raise ValueError(f"invalid native primary units for {arm}")
    for v, q in zip(panels["V"], panels["Q"]):
        if (v["reset_seed"], v["action_seed"]) != (q["reset_seed"], q["action_seed"]):
            raise ValueError("final worlds/action streams are not paired")
    differences = [q["J"] - v["J"] for v, q in zip(panels["V"], panels["Q"])]
    delta = statistics.mean(differences)
    return dict(delta=delta, differences=differences, paired_worlds=expected,
                absolute_means={a: statistics.mean(r["J"] for r in p) for a, p in panels.items()},
                descriptive_sd=statistics.stdev(differences) if expected > 1 else None,
                minimum=min(differences), maximum=max(differences),
                adverse_worlds=sum(d < 0 for d in differences), mei=.01,
                reading="ABOVE_MEI" if delta > .01 else "ADVERSE" if delta < -.01 else "WITHIN_MEI",
                uncertainty="one trained pair; descriptive fixed panel; no training-population interval")


def resources():
    try:
        import resource
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        return {"peak_rss_bytes": own.ru_maxrss * 1024,
                "aggregate_cpu_seconds": own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime}
    except (ImportError, OSError):
        # Optional telemetry never suppresses the scientifically valid primary.
        return {"peak_rss_bytes": None, "aggregate_cpu_seconds": None,
                "self_cpu_seconds": time.process_time(), "resources_unmeasured": True}


def run_pair(output, seed=9411, *, start=None, env_factory=make_real, horizon=256,
             train_episodes=256, eval_episodes=32, chunk=32, native=True):
    start = time.monotonic() if start is None else start
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    summary = dict(object="LCAC_B01_256", card=CARD, launch_sha=sha, seed=seed,
                   mode="NATIVE_B_EXPLORE" if native else "ENGINEERING_CHECK",
                   config=dict(horizon=horizon, train_episodes=train_episodes,
                               eval_episodes=eval_episodes, chunk=chunk, epochs=4,
                               dtype="float32", device="cpu", threads=1),
                   arms={}, primary=None, complete=False)
    rows = []
    base = 100000 * seed
    try:
        # Each arm gets an independent environment, parameters, optimizer and trajectory.
        pair = build_pair(seed)
        with (output / "episodes.jsonl").open("w", encoding="utf-8") as episode_file, \
                (output / "rollouts.jsonl").open("w", encoding="utf-8") as rollout_file:
            def emit(row):
                episode_file.write(json.dumps(row, allow_nan=False) + "\n")
                episode_file.flush()
                if row["phase"] == "eval":
                    rows.append(row)
            for arm in ("V", "Q"):
                arm_start = time.monotonic()
                counts = new_counts()
                result = dict(counts=counts, complete=False)
                summary["arms"][arm] = result
                actor, critic = pair[arm]
                initial = snapshot(actor, critic)
                optimizer = optimizer_for(actor, critic)
                env = env_factory(base + 1000)
                counts["constructors"] += 1
                counts["constructor_resets"] += 1
                try:
                    for rollout in range(train_episodes // 2):
                        episodes = []
                        for offset in range(2):
                            episode = 2 * rollout + offset
                            episodes.append(collect_episode(
                                env, actor, horizon, base + 1000 + episode, base + 10000 + episode,
                                dict(arm=arm, phase="train", episode=episode, master=seed),
                                counts, emit, native=native))
                        record = update(actor, critic, optimizer, episodes, arm, counts, chunk)
                        record.update(arm=arm, rollout=rollout)
                        rollout_file.write(json.dumps(record, allow_nan=False) + "\n")
                        rollout_file.flush()
                    result["training_exposure"] = movement(initial, actor, critic)
                    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(),
                                    arm=arm, seed=seed, launch_sha=sha, config=summary["config"]),
                               output / f"final_{arm}.pt")
                    for episode in range(eval_episodes):
                        collect_episode(env, actor, horizon, base + 2000 + episode,
                                        base + 20000 + episode,
                                        dict(arm=arm, phase="eval", episode=episode, master=seed),
                                        counts, emit, native=native)
                    result["complete"] = True
                finally:
                    env.close()
                    result["elapsed_wall_seconds"] = time.monotonic() - arm_start
        summary["primary"] = primary(rows, eval_episodes, horizon)
        summary["complete"] = True
    except Exception as error:
        summary["error"] = f"{type(error).__name__}: {error}"
    finally:
        summary["elapsed_wall_seconds"] = time.monotonic() - start
        summary.update(resources())
        (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return summary
