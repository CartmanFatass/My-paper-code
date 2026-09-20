"""C01 exposure is fixed before scores; each output retains every selected arm."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import resource
import time

import numpy as np
import torch

from .host import CrossingHost, Worlds
from .learner import build_scheduler, collect, flat_parameters, update


@dataclass(frozen=True)
class Config:
    seed: int = 73141
    horizon: int = 96
    train_episodes: int = 4096
    initial_episodes: int = 64
    selection_episodes: int = 256
    final_episodes: int = 256
    batch: int = 32
    epochs: int = 4

    def __post_init__(self):
        if self.seed < 0 or self.horizon <= 0 or self.horizon % 48:
            raise ValueError("invalid seed or nonterminal horizon")
        if min(self.train_episodes, self.initial_episodes, self.selection_episodes,
               self.final_episodes, self.batch, self.epochs) <= 0:
            raise ValueError("exposure counts must be positive")
        if self.train_episodes % self.batch:
            raise ValueError("training episodes must fill each declared rollout")


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def mean_reading(rows):
    if not rows:
        return None
    scalars = ("service", "completed_jobs", "conflicts", "wait_ticks", "gate_opportunities",
        "gate_disagreement", "unknown_gate", "packets", "bytes", "timing_slot_bits",
        "send_peer_near_crossing", "send_peer_shared_near_gate", "send_before_peer_decision", "send_changed", "shared_jobs",
        "bypass_jobs", "route_choices_with_valid_peer")
    result = {key: float(np.mean([r[key] for r in rows])) for key in scalars}
    for numerator, denominator, name in (
        ("gate_disagreement", "gate_opportunities", "gate_disagreement_rate"),
        ("message_age_sum", "message_age_count", "mean_valid_message_age"),
    ):
        count = sum(r[denominator] for r in rows)
        result[name] = sum(r[numerator] for r in rows) / count if count else None
    for name in ("send_phase", "send_peer_remaining", "send_clock_phase"):
        result[name] = np.sum([r[name] for r in rows], axis=0).tolist()
    return result


def run_study(out, launch_sha, config=Config()):
    out = Path(out)
    if (out / "summary.json").exists():
        raise FileExistsError("C01 never overwrites or resumes an existing scientific output")
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    torch.set_num_threads(1)
    counts = {f"{phase}_{quantity}": 0 for phase in ("train", "initial", "selection", "eval")
              for quantity in ("episodes", "transitions", "choice_opportunities")}
    counts.update(optimizer_steps=0, evaluation_optimizer_steps=0, started_fits=0)
    summary = dict(object="SIR-C01", direction="skill_information_refresh", status="RUNNING",
        launch_sha=launch_sha, config=asdict(config), counts=counts, limits=[],
        planned_independent_training_runs=1, claim_scope="exploratory single trained policy on a fixed-skill small host",
        dtype="float32", device="cpu", native_threads=1, phases_seconds={},
        selection=[], final={}, resources_unmeasured=False)
    write_json(out / "config.json", asdict(config))
    write_json(out / "summary.json", summary)
    model = initial_actor = initial_critic = None
    final_rows = {}
    with (out / "episodes.jsonl").open("x") as episodes_file, (out / "updates.jsonl").open("x") as updates_file:
        def emit(rows, phase, arm, **extra):
            for row in rows:
                episodes_file.write(json.dumps(dict(phase=phase, arm=arm, **extra, **row), allow_nan=False) + "\n")
            episodes_file.flush()

        def evaluate(arm, phase, phase_id, episodes, *, distance_delta=2, age_limit=None,
                     variant=None, trace=False):
            rows, traces = [], []
            for start in range(0, episodes, config.batch):
                ids = range(start, min(start + config.batch, episodes))
                host = CrossingHost(Worlds.make(config.seed, phase_id, ids, config.horizon))
                batch_rows, _, batch_trace = collect(host, model=model, arm=arm,
                    distance_delta=distance_delta, age_limit=age_limit, counts=counts,
                    phase=phase, retain_trace=trace)
                emit(batch_rows, phase, arm, variant=variant)
                rows.extend(batch_rows)
                if batch_trace is not None:
                    traces.append(batch_trace)
            if trace:
                merged = {key: np.concatenate([tr[key] for tr in traces]) for key in traces[0]}
                np.savez_compressed(out / f"final_trace_{arm}.npz", **merged)
            return rows

        try:
            model = build_scheduler(config.seed)
            initial_actor = flat_parameters(model.actor)
            initial_critic = flat_parameters(model.critic)
            torch.save(dict(model=model.state_dict(), launch_sha=launch_sha, config=asdict(config)), out / "initial.pt")
            rng = torch.Generator().manual_seed(config.seed + 41)
            optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
            phase_start = time.monotonic()
            initial_rows = evaluate("LEARNED", "initial", 3, config.initial_episodes)
            summary["initial"] = mean_reading(initial_rows)
            summary["phases_seconds"]["initial"] = time.monotonic() - phase_start
            phase_start = time.monotonic()
            counts["started_fits"] += 1
            for start in range(0, config.train_episodes, config.batch):
                host = CrossingHost(Worlds.make(config.seed, 0, range(start, start + config.batch), config.horizon))
                rows, rollout, _ = collect(host, model=model, rng=rng, stochastic=True,
                    counts=counts, phase="train")
                emit(rows, "train", "LEARNED")
                def record_update(record):
                    counts["optimizer_steps"] += 1
                    updates_file.write(json.dumps(dict(rollout=start // config.batch, **record), allow_nan=False) + "\n")
                    updates_file.flush()
                update(model, optimizer, rollout, config.epochs, record_update=record_update)
            summary["phases_seconds"]["train"] = time.monotonic() - phase_start
            summary["learner"] = dict(actor_displacement=float((flat_parameters(model.actor) - initial_actor).norm()),
                critic_displacement=float((flat_parameters(model.critic) - initial_critic).norm()),
                parameters=sum(p.numel() for p in model.parameters()))
            torch.save(dict(model=model.state_dict(), launch_sha=launch_sha, config=asdict(config)), out / "final.pt")
            phase_start = time.monotonic()
            for delta in (1, 2, 4):
                for age in (8, 12, None):
                    name = f"delta{delta}_age{age if age is not None else 'off'}"
                    rows = evaluate("AGE_CHANGE", "selection", 1, config.selection_episodes,
                        distance_delta=delta, age_limit=age, variant=name)
                    summary["selection"].append(dict(variant=name, distance_delta=delta, age_limit=age,
                        reading=mean_reading(rows)))
            # Lexical tie break is predeclared and independent of final-world scores.
            best = sorted(summary["selection"], key=lambda r: (-r["reading"]["service"], r["variant"]))[0]
            summary["selected_baseline"] = {key: best[key] for key in ("variant", "distance_delta", "age_limit")}
            summary["phases_seconds"]["selection"] = time.monotonic() - phase_start
            write_json(out / "selection.json", dict(variants=summary["selection"], selected=summary["selected_baseline"]))
            phase_start = time.monotonic()
            for arm in ("LEARNED", "AGE_CHANGE", "PRE_DECISION", "POLL"):
                rows = evaluate(arm, "eval", 2, config.final_episodes, trace=True,
                    distance_delta=best["distance_delta"], age_limit=best["age_limit"],
                    variant=best["variant"] if arm == "AGE_CHANGE" else None)
                final_rows[arm] = rows
                summary["final"][arm] = mean_reading(rows)
            summary["phases_seconds"]["eval"] = time.monotonic() - phase_start
            primary = np.asarray([l["service"] - r["service"] for l, r in
                zip(final_rows["LEARNED"], final_rows["AGE_CHANGE"])])
            summary["primary"] = dict(comparison="LEARNED minus development-selected AGE_CHANGE",
                world_ids=list(range(config.final_episodes)), per_world_difference=primary.tolist(),
                mean=float(primary.mean()), positive=int((primary > 0).sum()),
                negative=int((primary < 0).sum()), conditional_on="one trained policy; not independent training replicates")
            expected_packets = 2 * config.horizon // 8
            if not all(row["packets"] == expected_packets for rows in final_rows.values() for row in rows):
                raise RuntimeError("fixed communication count violated")
            if not all(torch.isfinite(p).all() for p in model.parameters()):
                raise FloatingPointError("non-finite final model")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["status"] = "TECHNICAL_FAILURE"
            summary["limits"].append(f"{type(error).__name__}: {error}")
            raise
        finally:
            if initial_actor is not None:
                actor_move = (flat_parameters(model.actor) - initial_actor).norm()
                critic_move = (flat_parameters(model.critic) - initial_critic).norm()
                summary["learner"] = dict(
                    actor_displacement=float(actor_move) if torch.isfinite(actor_move) else None,
                    critic_displacement=float(critic_move) if torch.isfinite(critic_move) else None,
                    parameters=sum(p.numel() for p in model.parameters()),
                    parameters_finite=bool(all(torch.isfinite(p).all() for p in model.parameters())))
            summary["wall_seconds"] = time.monotonic() - started
            usage = resource.getrusage(resource.RUSAGE_SELF)
            summary["resources"] = dict(peak_rss_kib=usage.ru_maxrss,
                rss_scope="one Linux scientific child, not aggregate node occupancy",
                user_cpu_seconds=usage.ru_utime, system_cpu_seconds=usage.ru_stime)
            write_json(out / "summary.json", summary)
    published = json.loads((out / "summary.json").read_text())
    if published["counts"] != counts or published["status"] != "COMPLETE":
        raise RuntimeError("summary readback failed")
    return summary
