"""Zero-training C06 comparison of short and long finite send-value rules."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import resource
import time

import numpy as np

from ..c01.host import DONE, FRAME, PACKET_BYTES, CrossingHost, Worlds
from .belief import PhysicalBelief, take_local
from .planning import paired_values, select_record


MODEL_COUNT_KEYS = (
    "model_root_decisions",
    "model_branch_transitions",
    "model_initialization_worlds",
    "synthetic_advance_draws",
    "synthetic_job_draws",
)


@dataclass(frozen=True)
class Config:
    seed: int = 73170
    model_seed: int = 973170
    horizon: int = 96
    batch: int = 16
    particles: int = 32
    selection_episodes: int = 64
    eval_episodes: int = 256
    thresholds: tuple[float, ...] = (-.05, 0., .05, .10)

    def __post_init__(self):
        thresholds = tuple(float(value) for value in self.thresholds)
        object.__setattr__(self, "thresholds", thresholds)
        if int(self.seed) < 0 or int(self.model_seed) < 0:
            raise ValueError("true-world and model seeds must be nonnegative")
        if self.horizon <= 0 or self.horizon % 48:
            raise ValueError("horizon must be a positive multiple of 48")
        if min(self.batch, self.selection_episodes, self.eval_episodes) < 1:
            raise ValueError("batch and episode counts must be positive")
        if self.particles < 2:
            raise ValueError("at least two particles are required for a finite SE")
        if not thresholds or not np.isfinite(thresholds).all():
            raise ValueError("thresholds must be a nonempty finite tuple")
        if len(set(thresholds)) != len(thresholds):
            raise ValueError("thresholds must be unique")


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _threshold_requests(delta, threshold, active):
    """Use ACTIVE_FIRST only for exact Monte Carlo ties."""
    delta = np.asarray(delta, dtype=np.float64)
    active = np.asarray(active, dtype=bool)
    if delta.shape != active.shape:
        raise ValueError("delta and ACTIVE_FIRST fallback must have the same shape")
    return np.where(delta > threshold, True,
        np.where(delta < threshold, False, active)).astype(bool)


def _reading(rows):
    return dict(
        worlds=len(rows),
        mean_completed_jobs=float(np.mean([row["completed_jobs"] for row in rows])),
        mean_service=float(np.mean([row["service"] for row in rows])),
        mean_conflicts=float(np.mean([row["conflicts"] for row in rows])),
        mean_wait_ticks=float(np.mean([row["wait_ticks"] for row in rows])),
        mean_packets=float(np.mean([row["packets"] for row in rows])),
        mean_bytes=float(np.mean([row["bytes"] for row in rows])),
    )


def _select_threshold(candidates):
    if not candidates:
        raise ValueError("at least one threshold candidate is required")
    return sorted(candidates, key=lambda item: (
        -item["reading"]["mean_completed_jobs"],
        abs(item["threshold"]),
        item["threshold"],
    ))[0]


def _paired_metric(left, right, key):
    left_values = np.asarray([row[key] for row in left], dtype=np.float64)
    right_values = np.asarray([row[key] for row in right], dtype=np.float64)
    if left_values.shape != right_values.shape or left_values.size == 0:
        raise ValueError("paired final panels must be nonempty and aligned")
    difference = left_values - right_values
    return dict(
        per_world_difference=difference.tolist(),
        positive=int(np.count_nonzero(difference > 0)),
        negative=int(np.count_nonzero(difference < 0)),
        tied=int(np.count_nonzero(difference == 0)),
        mean=float(difference.mean()),
        conditional_world_se=(float(difference.std(ddof=1) / np.sqrt(len(difference)))
            if len(difference) > 1 else None),
    )


def _contrast(left, right):
    left_ids = [row["world_id"] for row in left]
    right_ids = [row["world_id"] for row in right]
    if left_ids != right_ids:
        raise ValueError("paired final panels must have the same ordered world IDs")
    return {
        "completed_jobs": _paired_metric(left, right, "completed_jobs"),
        "service": _paired_metric(left, right, "service"),
    }


def _trace_arrays(batch, horizon, support):
    return dict(
        own=np.zeros((batch, horizon, 2, 5), dtype=np.int16),
        last_sent=np.zeros((batch, horizon, 2, 5), dtype=np.int16),
        last_sent_time=np.zeros((batch, horizon, 2), dtype=np.int64),
        peer_packet=np.zeros((batch, horizon, 2, 5), dtype=np.int16),
        peer_packet_time=np.zeros((batch, horizon, 2), dtype=np.int64),
        available=np.zeros((batch, horizon, 2), dtype=bool),
        forced=np.zeros((batch, horizon), dtype=bool),
        requests=np.zeros((batch, horizon), dtype=bool),
        sent=np.zeros((batch, horizon), dtype=bool),
        evaluated=np.zeros((batch, horizon), dtype=bool),
        predicted_delta=np.zeros((batch, horizon), dtype=np.float64),
        predicted_se=np.zeros((batch, horizon), dtype=np.float64),
        predicted_hold=np.zeros((batch, horizon), dtype=np.float64),
        predicted_send=np.zeros((batch, horizon), dtype=np.float64),
        belief_weights=np.zeros((batch, horizon, support), dtype=np.float64),
        reward=np.zeros((batch, horizon), dtype=np.float32),
        completed_jobs=np.zeros((batch, horizon), dtype=np.int16),
        conflicts=np.zeros((batch, horizon), dtype=np.int16),
        wait_ticks=np.zeros((batch, horizon), dtype=np.int16),
        gate_opportunities=np.zeros((batch, horizon), dtype=np.int16),
        bypass_jobs=np.zeros((batch, horizon), dtype=np.int16),
        jobs_started=np.zeros((batch, horizon), dtype=np.int16),
        packets=np.zeros((batch, horizon), dtype=np.int16),
        # These privileged arrays are populated only after the request is fixed.
        diagnostic_physical_payloads=np.zeros((batch, horizon, 2, 5), dtype=np.int16),
        diagnostic_delivered_cache=np.zeros((batch, horizon, 2, 5), dtype=np.int16),
        diagnostic_delivered_cache_time=np.zeros((batch, horizon, 2), dtype=np.int16),
    )


def _save_trace(out, phase, arm, start, stop, world_ids, trace, steps):
    suffix = "" if steps == trace["requests"].shape[1] else f"_partial{steps}"
    path = out / f"{phase}_trace_{arm}_worlds{start}-{stop}{suffix}.npz"
    np.savez_compressed(path, world_ids=np.asarray(world_ids, dtype=np.int64),
        **{name: values[:, :steps] for name, values in trace.items()})
    return path.name


def _run_batch(host, arm, threshold, world_ids, model_seed, phase, particles, counts,
               stage, retain_trace, out, start, trace_records):
    modeled = arm in ("SHORT", "LONG")
    initial = [take_local(host, agent) for agent in (0, 1)]
    beliefs = [PhysicalBelief(item) for item in initial] if modeled else None
    if modeled:
        counts["belief_observation_record_calls"] += 2
        counts["belief_observation_rows"] += 2 * host.batch
        counts[f"{stage}_belief_observation_record_calls"] += 2
        counts[f"{stage}_belief_observation_rows"] += 2 * host.batch
    support = len(PhysicalBelief.states)
    trace = _trace_arrays(host.batch, host.horizon, support)
    completed_steps = 0
    trace_name = None
    tracked_metrics = (
        "completed_jobs", "conflicts", "wait_ticks", "gate_opportunities",
        "bypass_jobs", "jobs_started", "packets",
    )
    previous_metrics = {name: np.zeros(host.batch, dtype=np.int64) for name in tracked_metrics}

    try:
        for tick in range(host.horizon):
            records = [take_local(host, agent) for agent in (0, 1)]
            if modeled and tick:
                for agent in (0, 1):
                    before_stats = beliefs[agent].stats
                    try:
                        beliefs[agent].update(records[agent])
                    finally:
                        after_stats = beliefs[agent].stats
                        observation_calls = after_stats["observations"] - before_stats["observations"]
                        packet_rows = after_stats["packet_updates"] - before_stats["packet_updates"]
                        contradiction_rows = after_stats["contradictions"] - before_stats["contradictions"]
                        counts["belief_observation_record_calls"] += observation_calls
                        counts["belief_observation_rows"] += observation_calls * host.batch
                        counts["belief_packet_update_rows"] += packet_rows
                        counts["belief_contradiction_rows"] += contradiction_rows
                        counts[f"{stage}_belief_observation_record_calls"] += observation_calls
                        counts[f"{stage}_belief_observation_rows"] += observation_calls * host.batch
                        counts[f"{stage}_belief_packet_update_rows"] += packet_rows
                        counts[f"{stage}_belief_contradiction_rows"] += contradiction_rows
            for agent, item in enumerate(records):
                trace["own"][:, tick, agent] = item.own
                trace["last_sent"][:, tick, agent] = item.last_sent
                trace["last_sent_time"][:, tick, agent] = item.last_sent_time
                trace["peer_packet"][:, tick, agent] = item.peer_packet
                trace["peer_packet_time"][:, tick, agent] = item.peer_packet_time
                trace["available"][:, tick, agent] = item.available

            sender = tick % 2
            current = records[sender]
            active = current.own[:, 0] != DONE
            forced = tick % FRAME >= FRAME - 2
            evaluated = current.available & (not forced)
            requested = active.copy() if arm == "ACTIVE_FIRST" else np.zeros(host.batch, dtype=bool)
            trace["forced"][:, tick] = forced
            trace["evaluated"][:, tick] = evaluated if modeled else False

            if modeled:
                trace["belief_weights"][:, tick] = beliefs[sender].weights
                indices = np.flatnonzero(evaluated)
                if len(indices):
                    selected_record = select_record(current, indices)
                    before = {key: counts[key] for key in MODEL_COUNT_KEYS}
                    try:
                        values = paired_values(
                            selected_record,
                            beliefs[sender].weights[indices].copy(),
                            beliefs[sender].states,
                            np.asarray(world_ids, dtype=np.int64)[indices],
                            seed=model_seed,
                            phase=phase,
                            particles=particles,
                            mode=arm,
                            counters=counts,
                        )
                    finally:
                        for key in MODEL_COUNT_KEYS:
                            counts[f"{stage}_{key}"] += counts[key] - before[key]
                    trace["predicted_delta"][indices, tick] = values["delta"]
                    trace["predicted_se"][indices, tick] = values["se"]
                    trace["predicted_hold"][indices, tick] = values["hold"]
                    trace["predicted_send"][indices, tick] = values["send"]
                    requested[indices] = _threshold_requests(
                        values["delta"], threshold, active[indices])

            sent = current.available & (requested | forced)
            trace["requests"][:, tick] = requested
            trace["sent"][:, tick] = sent
            # Policy computation is complete. Privileged host state below is diagnostic only.
            trace["diagnostic_physical_payloads"][:, tick] = host.payloads().copy()
            trace["diagnostic_delivered_cache"][:, tick] = host.cache.copy()
            trace["diagnostic_delivered_cache_time"][:, tick] = host.cache_time.copy()
            reward = host.step(requested)
            trace["reward"][:, tick] = reward
            for name in tracked_metrics:
                trace[name][:, tick] = host.metrics[name] - previous_metrics[name]
                previous_metrics[name] = host.metrics[name].copy()
            completed_steps += 1
            counts[f"{stage}_transitions"] += host.batch
            counts["actual_transitions"] += host.batch
    except Exception:
        if retain_trace and completed_steps:
            trace_name = _save_trace(out, stage, arm, start, start + host.batch,
                world_ids, trace, completed_steps)
            trace_records.append(dict(file=trace_name, phase=stage, arm=arm,
                threshold=threshold, world_start=start, world_stop=start + host.batch,
                completed_steps=completed_steps, complete=False))
        raise

    if retain_trace:
        trace_name = _save_trace(out, stage, arm, start, start + host.batch,
            world_ids, trace, completed_steps)
        trace_records.append(dict(file=trace_name, phase=stage, arm=arm,
            threshold=threshold, world_start=start, world_stop=start + host.batch,
            completed_steps=completed_steps, complete=True))
    return host.rows(), trace_name


def run_study(out, launch_sha, config=Config()):
    out = Path(out)
    native_control_files = {
        "launch-manifest.json",
        "admission-preflight.json",
        "launch-status.json",
        "stdout.log",
        "stderr.log",
    }
    if out.exists():
        if not out.is_dir():
            raise FileExistsError("C06 output path already exists and is not a directory")
        unexpected = [path.name for path in out.iterdir()
            if path.name not in native_control_files]
        if unexpected:
            raise FileExistsError(
                "C06 never overwrites or resumes scientific output: " + ", ".join(sorted(unexpected)))
    out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    counts = dict(
        started_fits=0,
        train_episodes=0,
        train_transitions=0,
        optimizer_steps=0,
        evaluation_optimizer_steps=0,
        selection_episodes=0,
        selection_native_episodes=0,
        selection_transitions=0,
        eval_episodes=0,
        eval_native_episodes=0,
        eval_transitions=0,
        actual_transitions=0,
        rule_search_arms=2 * len(config.thresholds),
        rule_search_exposure_episodes=0,
        belief_observation_record_calls=0,
        belief_observation_rows=0,
        belief_packet_update_rows=0,
        belief_contradiction_rows=0,
    )
    for key in MODEL_COUNT_KEYS:
        counts[key] = 0
        counts[f"selection_{key}"] = 0
        counts[f"eval_{key}"] = 0
    for stage in ("selection", "eval"):
        counts[f"{stage}_belief_observation_record_calls"] = 0
        counts[f"{stage}_belief_observation_rows"] = 0
        counts[f"{stage}_belief_packet_update_rows"] = 0
        counts[f"{stage}_belief_contradiction_rows"] = 0
    expected = dict(
        jobs_per_world=config.horizon // 12 + config.horizon // 16,
        packets_per_world=2 * config.horizon // FRAME,
        bytes_per_world=2 * config.horizon // FRAME * PACKET_BYTES,
    )
    summary = dict(
        object="SIR-C06",
        direction="skill_information_refresh",
        status="RUNNING",
        launch_sha=launch_sha,
        source_sha=launch_sha,
        config=asdict(config),
        counts=counts,
        phases_seconds={},
        resources_unmeasured=False,
        selection=[],
        selected={},
        final={},
        contrasts={},
        trace_files=[],
        final_selection="none",
        expected_accounting=expected,
        model="known finite physical law shared by SHORT and LONG",
        belief="approximate physical belief; peer silence likelihood intentionally ignored",
        belief_stats_semantics=("observations count batched LocalRecord calls; observation_rows "
            "multiply each successful call by its batch size; packet updates and contradictions count rows"),
        continuation="ACTIVE_FIRST after the paired root intervention",
        limits=[],
    )

    def refresh_runtime():
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["wall_seconds"] = time.monotonic() - started
        summary["resources"] = dict(
            ru_maxrss_child_kib=int(usage.ru_maxrss),
            rss_scope="single scientific process (launcher child in production), Linux ru_maxrss KiB",
            user_cpu_child_seconds=float(usage.ru_utime),
            system_cpu_child_seconds=float(usage.ru_stime),
            cpu_scope="single scientific process cumulative child user and system CPU",
        )

    def flush_summary():
        refresh_runtime()
        _write_json(out / "summary.json", summary)

    _write_json(out / "config.json", dict(source_sha=launch_sha, **asdict(config)))
    (out / "updates.jsonl").open("x", encoding="utf-8").close()
    summary["phases_seconds"]["setup"] = time.monotonic() - started
    flush_summary()
    final_rows = {}

    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episodes:
        def evaluate(stage, phase, arm, threshold, episodes_count, retain_trace=False):
            rows, traces = [], []
            for start in range(0, episodes_count, config.batch):
                stop = min(start + config.batch, episodes_count)
                ids = tuple(range(start, stop))
                host = CrossingHost(Worlds.make(config.seed, phase, ids, config.horizon))
                batch_rows, trace_name = _run_batch(
                    host, arm, threshold, ids, config.model_seed, phase, config.particles,
                    counts, stage, retain_trace, out, start, summary["trace_files"])
                if not all(row["jobs_started"] == expected["jobs_per_world"]
                        and row["packets"] == expected["packets_per_world"]
                        and row["bytes"] == expected["bytes_per_world"] for row in batch_rows):
                    raise RuntimeError("fixed host job or communication accounting changed")
                for row in batch_rows:
                    episodes.write(json.dumps(dict(
                        phase=stage,
                        arm=arm,
                        threshold=threshold,
                        **row,
                    ), allow_nan=False) + "\n")
                episodes.flush()
                rows.extend(batch_rows)
                traces.extend([trace_name] if trace_name is not None else [])
                counts[f"{stage}_episodes"] += len(batch_rows)
                counts[f"{stage}_native_episodes"] += len(batch_rows)
                if stage == "selection":
                    counts["rule_search_exposure_episodes"] += len(batch_rows)
                flush_summary()
                print(json.dumps(dict(status="PROGRESS", phase=stage, arm=arm,
                    threshold=threshold, completed_native_episodes=counts[f"{stage}_native_episodes"])),
                    flush=True)
            return rows, traces

        active_phase = "selection"
        phase_started = time.monotonic()
        try:
            grouped = {mode: [] for mode in ("SHORT", "LONG")}
            for mode in ("SHORT", "LONG"):
                for threshold in config.thresholds:
                    rows, _ = evaluate("selection", 20, mode, threshold,
                        config.selection_episodes)
                    candidate = dict(
                        arm=mode,
                        threshold=threshold,
                        reading=_reading(rows),
                    )
                    grouped[mode].append(candidate)
                    summary["selection"].append(candidate)
                    flush_summary()
            selected_records = {mode: _select_threshold(grouped[mode])
                for mode in ("SHORT", "LONG")}
            summary["selected"] = {mode: record["threshold"]
                for mode, record in selected_records.items()}
            _write_json(out / "selection.json", dict(
                candidates=summary["selection"],
                selected=summary["selected"],
                rule="largest mean completed_jobs; ties smallest abs(threshold), then numeric threshold",
                final_selection="none",
            ))
            summary["phases_seconds"]["selection"] = time.monotonic() - phase_started
            flush_summary()

            active_phase = "eval"
            phase_started = time.monotonic()
            final_traces = {}
            for arm in ("SHORT", "LONG", "ACTIVE_FIRST"):
                threshold = summary["selected"].get(arm)
                rows, traces = evaluate("eval", 21, arm, threshold,
                    config.eval_episodes, retain_trace=True)
                final_rows[arm] = rows
                final_traces[arm] = traces
                summary["final"][arm] = dict(
                    threshold=threshold,
                    reading=_reading(rows),
                    traces=traces,
                )
                flush_summary()
            summary["contrasts"] = {
                "LONG-SHORT": _contrast(final_rows["LONG"], final_rows["SHORT"]),
                "LONG-ACTIVE_FIRST": _contrast(final_rows["LONG"], final_rows["ACTIVE_FIRST"]),
                "SHORT-ACTIVE_FIRST": _contrast(final_rows["SHORT"], final_rows["ACTIVE_FIRST"]),
            }
            summary["phases_seconds"]["eval"] = time.monotonic() - phase_started

            all_rows = [row for rows in final_rows.values() for row in rows]
            if not all(row["jobs_started"] == expected["jobs_per_world"]
                    and row["packets"] == expected["packets_per_world"]
                    and row["bytes"] == expected["bytes_per_world"] for row in all_rows):
                raise RuntimeError("fixed host job or communication accounting changed")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["status"] = "TECHNICAL_FAILURE"
            summary["error"] = {"type": type(error).__name__, "message": str(error)}
            summary["limits"].append(f"{type(error).__name__}: {error}")
            summary["phases_seconds"][active_phase] = time.monotonic() - phase_started
            raise
        finally:
            summary["phases_seconds"]["total"] = time.monotonic() - started
            flush_summary()

    published = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    if published["status"] != "COMPLETE" or published["counts"] != counts:
        raise RuntimeError("C06 summary readback failed")
    return summary
