"""One declared A01 training attempt and its recoverable scientific outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import resource
import time
from typing import Mapping

import numpy as np

from .host import (OPTION_COUNT, STATE_COUNT, addressed_randomness,
                   behavior_episode, step)
from .learning import ARMS, greedy_probabilities, update_chunk


OBJECT = "termination_reuse_off_termination_a01"
SEEDS = (91021, 91022, 91023)
LIMITS = (
    "exploratory independent host; no UAV or novelty claim",
    "fixed teammate and focal termination law; no termination learning",
    "same data/update rows, different target-construction arithmetic",
    "constant step size and finite exposure; no convergence claim",
)


@dataclass(frozen=True)
class Config:
    arm: str
    seed: int
    train_episodes: int = 512
    horizon: int = 96
    eval_episodes: int = 64
    checkpoints: tuple = (0, 32, 128, 512)
    chunk: int = 8
    gamma: float = .95
    alpha: float = 1.
    beta: float = .5
    zeta: float = .125

    def validate(self):
        if self.arm not in ARMS or self.seed < 0:
            raise ValueError("invalid arm/seed")
        if min(self.train_episodes, self.horizon, self.eval_episodes, self.chunk) < 1:
            raise ValueError("all exposure dimensions must be positive")
        if self.horizon % self.chunk:
            raise ValueError("chunk must divide the declared horizon")
        if (tuple(sorted(set(self.checkpoints))) != self.checkpoints
                or self.checkpoints[0] != 0 or self.checkpoints[-1] != self.train_episodes):
            raise ValueError("checkpoints must run from zero to the final episode")
        if not (0 <= self.gamma < 1 and 0 < self.alpha <= 1
                and 0 <= self.beta <= 1 and 0 < self.zeta <= 1):
            raise ValueError("invalid learning or hazard parameter")


def evaluate(q: np.ndarray, config: Config, checkpoint: int):
    """Fixed target beta, greedy choices with uniform ties; never update Q."""
    rows = []
    for episode in range(config.eval_episodes):
        state, option_u, draws = addressed_randomness(
            config.seed, 1, episode, config.horizon
        )
        option = int(option_u >= greedy_probabilities(q[state.encode()])[0])
        reward_sum, renewals, changes = 0., 0, 0
        for demand_u, teammate_u, renewal_u, selection_u in draws:
            state, reward, _ = step(state, option, demand_u, teammate_u)
            reward_sum += reward
            if renewal_u < config.beta:
                renewals += 1
                next_option = int(selection_u >= greedy_probabilities(q[state.encode()])[0])
                changes += int(next_option != option)
                option = next_option
        rows.append({
            "checkpoint": checkpoint, "episode": episode,
            "J": reward_sum / config.horizon, "reward_sum": reward_sum,
            "team_steps": config.horizon, "termination_events": renewals,
            "changed_labels": changes, "new_updates": 0,
        })
    return rows


def write_json(path: Path, value):
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _identity(path: Path):
    return {"path": path.name, "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def run_study(config: Config, out: Path, admission: Mapping, start: float | None = None,
              *, object_id: str = OBJECT, run_label: str | None = None,
              limits: tuple[str, ...] = LIMITS):
    """The guarded script is the production entry. Tests may use small fixtures."""
    config.validate()
    run_label = config.arm if run_label is None else run_label
    if not isinstance(object_id, str) or not object_id:
        raise ValueError("object identifier must be nonempty")
    if not isinstance(run_label, str) or not run_label:
        raise ValueError("run label must be nonempty")
    if not isinstance(limits, tuple) or not limits or not all(
            isinstance(limit, str) and limit for limit in limits):
        raise ValueError("limits must be a nonempty tuple of strings")
    identity = {"object": object_id, "arm": run_label,
                "learner": config.arm, "seed": config.seed}
    start = time.monotonic() if start is None else start
    if (admission.get("direction") != "termination_rule_experience_reuse"
            or len(admission.get("sha", "")) != 40):
        raise ValueError("study requires the validated entry's admission identity")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    scientific_files = ("config.json", "status.json", "summary.json", "behavior.npz",
                        "final.npz", "updates.jsonl", "evaluation.jsonl", "curve.json")
    if any((out / name).exists() for name in scientific_files):
        raise FileExistsError("scientific output already exists; no overwrite or resume")
    with (out / "config.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({**identity, "config": asdict(config),
                   "launch_sha": admission["sha"], "admission": dict(admission),
                   "host": "independent_two_agent_service_line",
                   "dtype": "float64", "numpy_version": np.__version__,
                   "evaluation_new_updates": 0}, stream, indent=2, allow_nan=False)
        stream.write("\n")

    q = np.zeros((STATE_COUNT, OPTION_COUNT), dtype=np.float64)
    visits = np.zeros_like(q, dtype=np.int64)
    counts = {"started_fits": 0, "train_episodes": 0, "train_team_steps": 0,
              "evaluation_episodes": 0, "evaluation_team_steps": 0,
              "tabular_update_calls": 0, "target_rows": 0,
              "table_entries_written": 0, "evaluation_new_updates": 0,
              "gradient_optimizer_steps": 0}
    diagnostics = {}
    curve, episodes, checkpoint_tables = [], [], []
    status = "RUNNING"
    error = None
    write_json(out / "status.json", {**identity, "status": status, "counts": counts})

    def publish_panel(checkpoint, evaluation_stream):
        before = q.copy()
        rows = evaluate(q, config, checkpoint)
        if not np.array_equal(q, before):
            raise RuntimeError("evaluation mutated Q")
        for row in rows:
            evaluation_stream.write(json.dumps(row, allow_nan=False) + "\n")
        evaluation_stream.flush()
        counts["evaluation_episodes"] += len(rows)
        counts["evaluation_team_steps"] += sum(row["team_steps"] for row in rows)
        curve.append({"train_episodes": checkpoint,
                      "train_team_steps": checkpoint * config.horizon,
                      "mean_J": float(np.mean([row["J"] for row in rows])),
                      "q_l2_from_initial": float(np.linalg.norm(q)),
                      "nonzero_q_entries": int(np.count_nonzero(q))})
        checkpoint_tables.append(q.copy())
        write_json(out / "curve.json", curve)

    try:
        with (out / "updates.jsonl").open("x", encoding="utf-8") as updates, \
                (out / "evaluation.jsonl").open("x", encoding="utf-8") as evaluations:
            publish_panel(0, evaluations)
            counts["started_fits"] = 1
            for episode_index in range(config.train_episodes):
                data = behavior_episode(config.seed, episode_index, config.horizon, config.zeta)
                episodes.append(data)
                counts["train_team_steps"] += config.horizon
                for offset in range(0, config.horizon, config.chunk):
                    stats = update_chunk(q, visits, data, offset, offset + config.chunk,
                                         config.arm, config.gamma, config.beta, config.alpha)
                    counts["tabular_update_calls"] += 1
                    for key in ("target_rows", "table_entries_written"):
                        counts[key] += stats[key]
                    for key, value in stats.items():
                        if key == "raw_ratio_max":
                            diagnostics[key] = max(diagnostics.get(key, 0), value)
                        else:
                            diagnostics[key] = diagnostics.get(key, 0) + value
                    updates.write(json.dumps({"episode": episode_index, "start": offset,
                                              **stats}, allow_nan=False) + "\n")
                counts["train_episodes"] += 1
                if counts["train_episodes"] in config.checkpoints:
                    updates.flush()
                    publish_panel(counts["train_episodes"], evaluations)
                    write_json(out / "status.json",
                               {**identity, "status": status, "counts": counts})
                    print(f"{run_label} seed={config.seed} episodes={counts['train_episodes']}",
                          flush=True)
            status = "COMPLETE"
    except Exception as exc:
        status, error = "FAILED", f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if episodes:
            np.savez_compressed(out / "behavior.npz", **{
                name: np.stack([getattr(ep, name) for ep in episodes])
                for name in ("states", "options", "rewards", "renewed",
                             "teammate_renewed", "next_option_probability")
            })
        np.savez_compressed(out / "final.npz", q=q, visits=visits,
                            checkpoint_q=np.asarray(checkpoint_tables),
                            checkpoint_episodes=np.asarray([r["train_episodes"] for r in curve]))
        if counts["target_rows"]:
            diagnostics["mean_discounted_trace_mass"] = (
                diagnostics["discounted_trace_mass_sum"] / counts["target_rows"])
            diagnostics["mean_squared_return_increment"] = (
                diagnostics["return_increment_square_sum"] / counts["target_rows"])
        usage = resource.getrusage(resource.RUSAGE_SELF)
        artifacts = [_identity(out / name) for name in scientific_files
                     if name not in ("status.json", "summary.json") and (out / name).exists()]
        summary = {
            **identity, "status": status, "error": error,
            "launch_sha": admission["sha"],
            "counts": counts, "diagnostics": diagnostics, "curve": curve,
            "primary_mean_J": float(np.mean([row["mean_J"] for row in curve[1:]]))
                if status == "COMPLETE" else None,
            "final_mean_J": curve[-1]["mean_J"] if status == "COMPLETE" else None,
            "learner_movement": {"initial_l2": 0., "final_l2": float(np.linalg.norm(q)),
                                 "absolute_l2": float(np.linalg.norm(q)),
                                 "relative_l2": None,
                                 "nonzero_entries": int(np.count_nonzero(q))},
            "resources": {"wall_seconds_from_entry": time.monotonic() - start,
                          "user_cpu_seconds_process": usage.ru_utime,
                          "system_cpu_seconds_process": usage.ru_stime,
                          "peak_rss_kib_linux_process": usage.ru_maxrss,
                          "scratch_bytes_at_summary": sum(a["bytes"] for a in artifacts),
                          "scope": "one Linux scientific process, no children",
                          "resources_unmeasured": False},
            "artifacts": artifacts,
            "limits": list(limits),
        }
        write_json(out / "summary.json", summary)
        write_json(out / "status.json",
                   {**identity, "status": status, "error": error, "counts": counts})
    return summary
