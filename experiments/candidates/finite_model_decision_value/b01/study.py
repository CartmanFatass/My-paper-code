"""B01 complete finite-knowledge comparison; prospective contract is in NOTES.md.

The callable loop also supports small, separate correctness fixtures. The production
entry fixes the declared configuration and requires native launch admission.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import time

import numpy as np

from .belief import JointPhysicalBelief, take_local
from .host import DONE, PACKET_BYTES, Worlds, CrossingHost
from .planning import paired_values, select_record


THETAS = np.array([.35, .55, .75, .95], dtype=np.float64)
THETAS.setflags(write=False)
ARMS = ("P4", "U4", "P32", "U32", "AF", "KNOW_P_NEAR")
SOURCE_PARENT = "3ca4cb1f83ea869e1efca852a099db31c52b0e2c"


@dataclass(frozen=True)
class Config:
    seed: int = 925731
    model_seed: int = 925973
    contexts: int = 256
    batch: int = 16
    horizon: int = 96
    particles: int = 32
    calibration_steps: int = 32
    calibration_phase: int = 40
    evaluation_phase: int = 41
    model_phase: int = 42


def write_json(path, value):
    path = Path(path)
    pending = path.with_suffix(path.suffix + ".pending")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(pending, path)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def calibration_posterior(positions, trials):
    """Consume only the supplied lawful prefix, not simulator success flags."""
    positions = np.asarray(positions)
    if positions.ndim != 2 or positions.shape[1] != trials + 1:
        raise ValueError("give only the requested own-position prefix")
    movement = positions[:, :-1] - positions[:, 1:]
    if np.any((movement != 0) & (movement != 1)) or np.any(positions <= 0):
        raise ValueError("calibration must contain unsaturated zero/one advances")
    successes = movement.sum(axis=1)
    likelihood = THETAS[None, :] ** successes[:, None] * (
        1 - THETAS[None, :]) ** (trials - successes[:, None])
    return likelihood / likelihood.sum(axis=1, keepdims=True), successes


def collect_calibration(config, ids):
    """Environment-side controlled corridor; only positions go to estimation."""
    if config.calibration_steps != 32:
        raise ValueError("the declared corridor contains exactly32 attempted advances")
    theta, observed = [], []
    for context in ids:
        parameter_rng = np.random.default_rng(np.random.SeedSequence(
            [config.seed, config.calibration_phase, int(context), 0]))
        actual_theta = THETAS[int(parameter_rng.integers(len(THETAS)))]
        motion_rng = np.random.default_rng(np.random.SeedSequence(
            [config.seed, config.calibration_phase, int(context), 1]))
        position = 33
        path = [position]
        for _ in range(config.calibration_steps):
            # The estimator receives path, never this event or parameter.
            position -= int(motion_rng.random() < actual_theta)
            path.append(position)
        theta.append(actual_theta)
        observed.append(path)
    return np.asarray(theta), np.asarray(observed, dtype=np.int16)


def threshold_requests(delta, active):
    delta = np.asarray(delta, dtype=np.float64)
    active = np.asarray(active, dtype=bool)
    if delta.shape != active.shape or not np.isfinite(delta).all():
        raise ValueError("finite estimates and matching AF fallback required")
    return np.where(delta > 0, True, np.where(delta < 0, False, active))


def _trace(batch, horizon, particles, components, states):
    trace = {
        name: np.zeros((batch, horizon, 2, 5), dtype=np.int16)
        for name in ("own", "last_sent", "peer_packet")
    }
    trace.update({name: np.zeros((batch, horizon, 2), dtype=np.int64)
                  for name in ("last_sent_time", "peer_packet_time")})
    trace["available"] = np.zeros((batch, horizon, 2), dtype=bool)
    for name in ("requested", "sent", "eligible", "evaluated"):
        trace[name] = np.zeros((batch, horizon), dtype=bool)
    for name in ("delta", "mc_se"):
        trace[name] = np.full((batch, horizon), np.nan)
    for name in ("theta_mean", "theta_variance"):
        trace[name] = np.full((batch, horizon, 2), np.nan)
    trace["root_joint_weights"] = np.full((batch, horizon, components, states), np.nan)
    trace["sample_delta"] = np.full((batch, horizon, particles), np.nan)
    for name in ("near_end", "opportunity_tick", "opportunity_kind"):
        trace[name] = np.full((batch, horizon, particles), -1, dtype=np.int16)
    for name in ("reward", "completed_jobs", "conflicts", "wait_ticks", "packets"):
        trace[name] = np.zeros((batch, horizon), dtype=np.float64)
    return trace


def evaluate_batch(config, ids, actual_theta, q, arm, raw_path):
    start, cpu_start = time.perf_counter(), time.process_time()
    components = 0 if arm == "AF" else 1 if arm == "KNOW_P_NEAR" else len(THETAS)
    counters = {}
    timing = dict(filter_seconds=0., planning_seconds=0., environment_seconds=0., save_seconds=0.)
    host = CrossingHost(Worlds.make(config.seed, config.evaluation_phase, ids,
                                   horizon=config.horizon, probabilities=actual_theta))
    beliefs = []
    if components:
        parameters = (actual_theta[:, None] if components == 1 else
                      np.broadcast_to(THETAS, (len(ids), len(THETAS))).copy())
        initial = np.ones((len(ids), 1)) if components == 1 else q
        mark = time.perf_counter()
        beliefs = [JointPhysicalBelief(take_local(host, agent), parameters, initial)
                   for agent in range(2)]
        timing["filter_seconds"] += time.perf_counter() - mark
    states = len(beliefs[0].states) if beliefs else 22
    trace = _trace(len(ids), config.horizon, config.particles, components, states)
    steps = 0
    observed_ticks = 0
    rows = []
    failure = None
    try:
        for tick in range(config.horizon):
            records = [take_local(host, agent) for agent in range(2)]
            for agent, record in enumerate(records):
                if beliefs and tick:
                    mark = time.perf_counter()
                    try:
                        beliefs[agent].update(record)
                    finally:
                        timing["filter_seconds"] += time.perf_counter() - mark
                for name in ("own", "last_sent", "last_sent_time", "peer_packet",
                             "peer_packet_time", "available"):
                    trace[name][:, tick, agent] = getattr(record, name)
                if beliefs:
                    trace["theta_mean"][:, tick, agent] = beliefs[agent].parameter_mean
                    trace["theta_variance"][:, tick, agent] = beliefs[agent].parameter_variance
            observed_ticks = tick + 1
            sender = tick % 2
            record = records[sender]
            active = record.own[:, 0] != DONE
            eligible = record.available & (tick % 8 < 6)
            trace["eligible"][:, tick] = eligible
            requested = active.copy()
            if beliefs and eligible.any():
                selected = np.flatnonzero(eligible)
                belief = beliefs[sender]
                trace["root_joint_weights"][selected, tick] = belief.weights[selected]
                mark = time.perf_counter()
                try:
                    result = paired_values(
                        select_record(record, selected), belief.weights[selected],
                        belief.theta_values[selected], belief.states,
                        tuple(ids[index] for index in selected), seed=config.model_seed,
                        phase=config.model_phase, particles=config.particles,
                        mode="JOINT" if arm.startswith("U") else "POSTERIOR_MEAN",
                        counters=counters)
                finally:
                    timing["planning_seconds"] += time.perf_counter() - mark
                requested[selected] = threshold_requests(result["delta"], active[selected])
                trace["evaluated"][selected, tick] = True
                for name in ("delta", "mc_se", "sample_delta", "near_end",
                             "opportunity_tick", "opportunity_kind"):
                    trace[name][selected, tick] = result[name]
            trace["requested"][:, tick] = requested
            trace["sent"][:, tick] = record.available & (requested | (tick % 8 >= 6))
            mark = time.perf_counter()
            try:
                trace["reward"][:, tick] = host.step(requested)
            finally:
                timing["environment_seconds"] += time.perf_counter() - mark
            steps = tick + 1
            for name in ("completed_jobs", "conflicts", "wait_ticks", "packets"):
                trace[name][:, tick] = host.metrics[name]
        for index, context in enumerate(ids):
            row = dict(context=int(context), arm=arm, theta=float(actual_theta[index]))
            row.update({name: int(host.metrics[name][index]) for name in host.metrics})
            row["bytes"] = row["packets"] * PACKET_BYTES
            row["service"] = row["completed_jobs"] / row["jobs_started"]
            if row["packets"] != config.horizon // 8 * 2:
                raise AssertionError("frozen per-frame packet quota not exhausted")
            rows.append(row)
    except Exception as error:
        failure = dict(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        mark = time.perf_counter()
        try:
            np.savez_compressed(raw_path, ids=np.asarray(ids), completed_steps=np.asarray(steps),
                                observed_ticks=np.asarray(observed_ticks),
                                **{name: values[:, :observed_ticks] for name, values in trace.items()})
        except Exception as error:
            failure = dict(error_type=type(error).__name__, error=str(error), prior_failure=failure)
            raise
        finally:
            timing["save_seconds"] += time.perf_counter() - mark
            filter_counters = {}
            for belief in beliefs:
                for name, value in belief.stats.items():
                    filter_counters[name] = filter_counters.get(name, 0) + int(value)
            cost = dict(
                state="COMPLETE" if failure is None else "FAILED", failure=failure,
                arm=arm, contexts=list(ids), steps=steps * len(ids), observed_ticks=observed_ticks,
                model=counters, filtering=filter_counters, **timing,
                wall_seconds=time.perf_counter() - start, cpu_seconds=time.process_time() - cpu_start)
            write_json(Path(raw_path).with_suffix(".cost.json"), cost)
    return rows, trace, cost


def common_prefix(left, right, ids, dose):
    """Only the never-diverged actual histories count, even if later states meet."""
    rows = []
    record_names = ("own", "last_sent", "last_sent_time", "peer_packet", "peer_packet_time", "available")
    for row, context in enumerate(ids):
        roots, value_differences, first = 0, 0, None
        variances, first_root, first_value = [], None, None
        for tick in range(left["sent"].shape[1]):
            for name in record_names:
                if not np.array_equal(left[name][row, tick], right[name][row, tick]):
                    raise AssertionError("actual records diverged before the first different send")
            if left["evaluated"][row, tick] != right["evaluated"][row, tick]:
                raise AssertionError("same lawful prefix has different root eligibility")
            if left["evaluated"][row, tick]:
                if not np.array_equal(left["root_joint_weights"][row, tick],
                                      right["root_joint_weights"][row, tick]):
                    raise AssertionError("shared filter differs on identical lawful history")
                roots += 1
                sender = tick % 2
                variance = float(left["theta_variance"][row, tick, sender])
                variances.append(variance)
                detail = dict(tick=tick, sender=sender, theta_variance=variance,
                              theta_mean=float(left["theta_mean"][row, tick, sender]),
                              p_delta=float(left["delta"][row, tick]),
                              u_delta=float(right["delta"][row, tick]),
                              p_mc_se=float(left["mc_se"][row, tick]),
                              u_mc_se=float(right["mc_se"][row, tick]),
                              p_requested=bool(left["requested"][row, tick]),
                              u_requested=bool(right["requested"][row, tick]))
                if first_root is None:
                    first_root = detail.copy()
                if detail["p_delta"] != detail["u_delta"]:
                    value_differences += 1
                    if first_value is None:
                        first_value = detail.copy()
            if left["sent"][row, tick] != right["sent"][row, tick]:
                if not left["evaluated"][row, tick]:
                    raise AssertionError("different send outside an evaluated optional root")
                first = detail.copy()
                break
        rows.append(dict(context=int(context), dose=dose, common_prefix_roots=roots,
                         roots_with_different_values=value_differences,
                         mean_prefix_theta_variance=float(np.mean(variances)) if variances else None,
                         first_root=first_root, first_value_difference=first_value,
                         first_action_difference=first))
    return rows


def difference_reading(values):
    values = np.asarray(values, dtype=np.float64)
    se = float(values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else None
    mean = float(values.mean())
    return dict(n=len(values), mean=mean, se=se,
                approximate_normal_95=[mean - 1.96 * se, mean + 1.96 * se] if se is not None else None,
                positive=int((values > 0).sum()), negative=int((values < 0).sum()),
                tied=int((values == 0).sum()), minimum=float(values.min()), maximum=float(values.max()))


def summarize(episodes, prefix):
    by_arm = {arm: sorted((r for r in episodes if r["arm"] == arm), key=lambda r: r["context"])
              for arm in ARMS}
    reference_ids = [r["context"] for r in by_arm["AF"]]
    if not reference_ids or any([r["context"] for r in rows] != reference_ids for rows in by_arm.values()):
        raise ValueError("all six complete paired panels are required")
    metrics = ("completed_jobs", "service", "conflicts", "wait_ticks", "packets")
    arrays = {arm: {metric: np.array([r[metric] for r in rows]) for metric in metrics}
              for arm, rows in by_arm.items()}
    pairs = [("U4", "P4"), ("U32", "P32")]
    pairs += [(arm, reference) for arm in ("P4", "U4", "P32", "U32")
              for reference in ("AF", "KNOW_P_NEAR")]
    pairs += [("KNOW_P_NEAR", "AF"), ("P32", "P4"), ("U32", "U4")]
    contrasts = {left + "-" + right: {
        metric: difference_reading(arrays[left][metric] - arrays[right][metric]) for metric in metrics}
        for left, right in pairs}
    dose = (arrays["U32"]["completed_jobs"] - arrays["P32"]["completed_jobs"] -
            arrays["U4"]["completed_jobs"] + arrays["P4"]["completed_jobs"])
    per_parameter = {}
    for theta in THETAS:
        mask = np.array([r["theta"] == theta for r in by_arm["AF"]])
        if mask.any():
            per_parameter[str(float(theta))] = {
                left + "-" + right: difference_reading(
                    (arrays[left]["completed_jobs"] - arrays[right]["completed_jobs"])[mask])
                for left, right in (("U4", "P4"), ("U32", "P32"))}
    return dict(
        estimand="Exploratory finite-program context mean; no confirmation/equivalence claim",
        arms={arm: {metric: float(value.mean()) for metric, value in items.items()}
              for arm, items in arrays.items()}, contrasts=contrasts,
        dose_contrast=difference_reading(dose), parameter_strata=per_parameter,
        common_prefix={str(dose): dict(
            contexts=sum(r["dose"] == dose for r in prefix),
            contexts_with_action_difference=sum(r["dose"] == dose and r["first_action_difference"] is not None
                                                for r in prefix),
            roots=sum(r["common_prefix_roots"] for r in prefix if r["dose"] == dose),
            roots_with_different_values=sum(r["roots_with_different_values"] for r in prefix if r["dose"] == dose))
            for dose in (4, 32)})


def run_study(out, launch_sha, config=Config()):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "config.json").exists() or (out / "summary.json").exists():
        raise FileExistsError("scientific output already exists; no automatic repeat")
    raw = out / "raw"
    raw.mkdir(exist_ok=False)
    start, cpu_start = time.perf_counter(), time.process_time()
    config_value = dict(**asdict(config), arms=list(ARMS), parameter_support=THETAS.tolist(),
                        launch_sha=launch_sha, retained_source=SOURCE_PARENT,
                        nominal_receiver_probability=.75, state_count=22,
                        threads={key: os.environ.get(key) for key in (
                            "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
    write_json(out / "config.json", config_value)
    episodes, prefixes, batch_costs = [], [], []
    status = dict(state="RUNNING", completed_arm_contexts=0, planned_arm_contexts=6 * config.contexts,
                  calibration_fits_started=0, calibration_fits_completed=0)
    write_json(out / "status.json", status)
    artifact_paths = [out / "config.json"]
    try:
        ids = tuple(range(config.contexts))
        mark = time.perf_counter()
        actual_theta, positions = collect_calibration(config, ids)
        collection_seconds = time.perf_counter() - mark
        posteriors, successes = {}, {}
        mark = time.perf_counter()
        for dose in (4, 32):
            status["calibration_fits_started"] += len(ids)
            posteriors[dose], successes[dose] = calibration_posterior(positions[:, :dose + 1].copy(), dose)
            status["calibration_fits_completed"] += len(ids)
        fitting_seconds = time.perf_counter() - mark
        calibration_file = raw / "calibration.npz"
        np.savez_compressed(calibration_file, ids=np.asarray(ids), positions=positions,
                            actual_theta=actual_theta, q4=posteriors[4], q32=posteriors[32],
                            successes4=successes[4], successes32=successes[32])
        artifact_paths.append(calibration_file)
        write_json(out / "status.json", status)
        for begin in range(0, len(ids), config.batch):
            end = min(begin + config.batch, len(ids))
            traces = {}
            for arm in ARMS:
                dose = 32 if arm.endswith("32") else 4
                trace_file = raw / f"{arm}_{begin:04d}_{end:04d}.npz"
                rows, traces[arm], cost = evaluate_batch(
                    config, ids[begin:end], actual_theta[begin:end],
                    posteriors[dose][begin:end], arm, trace_file)
                episodes.extend(rows)
                batch_costs.append(cost)
                artifact_paths.extend((trace_file, trace_file.with_suffix(".cost.json")))
                status["completed_arm_contexts"] += len(rows)
                status["last_arm"] = arm
                status["last_context_exclusive"] = end
                write_json(out / "episodes.json", episodes)
                write_json(out / "status.json", status)
            for dose in (4, 32):
                prefixes.extend(common_prefix(traces[f"P{dose}"], traces[f"U{dose}"], ids[begin:end], dose))
            write_json(out / "common_prefix.json", prefixes)
        reading = summarize(episodes, prefixes)
        branches = sum(cost["model"].get("model_branch_transitions", 0) for cost in batch_costs)
        upper = 5 * config.contexts * (config.horizon * 3 // 4) * config.particles * 2 * 32
        if branches > upper:
            raise AssertionError("model branch count exceeds declared bound")
        status["state"] = "COMPLETE"
        write_json(out / "status.json", status)
        artifact_paths.extend(out / name for name in ("episodes.json", "common_prefix.json", "status.json"))
        artifacts = [dict(path=str(path.relative_to(out)), bytes=path.stat().st_size, sha256=sha256(path))
                     for path in artifact_paths]
        summary = dict(
            state="COMPLETE", launch_sha=launch_sha, config=config_value, **reading,
            counts=dict(calibration_fits_started=status["calibration_fits_started"],
                        calibration_fits_completed=status["calibration_fits_completed"],
                        policy_fits_started=0, optimizer_updates=0, policy_parameter_updates=0,
                        calibration_steps=32 * config.contexts,
                        evaluation_episodes=len(episodes), evaluation_team_ticks=sum(c["steps"] for c in batch_costs),
                        model_branch_transitions=branches, model_branch_transition_upper=upper),
            calibration=dict(collection_seconds=collection_seconds, fitting_seconds=fitting_seconds,
                             mean_variance={str(k): float(np.mean((posteriors[k] * THETAS**2).sum(axis=1) -
                                 (posteriors[k] * THETAS).sum(axis=1)**2)) for k in (4, 32)}),
            batch_costs=batch_costs, artifacts=artifacts,
            resources=dict(wall_seconds_through_artifact_hashing=time.perf_counter() - start,
                           cpu_seconds=time.process_time() - cpu_start,
                           peak_single_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                           python=platform.python_version(), numpy=np.__version__, node=platform.node(),
                           measurement_scope="scientific process through hashing; excludes final summary write and supervisor",
                           raw_artifact_bytes=sum(a["bytes"] for a in artifacts if a["path"].startswith("raw/"))),
            inference_scope="Approximate joint physical filtering omits peer-send/silence likelihood; fixed nominal receiver",
            failure_policy="No replacement contexts, zero filling, automatic retry or post-score extension")
        write_json(out / "summary.json", summary)
        return summary
    except Exception as error:
        status.update(state="FAILED", error_type=type(error).__name__, error=str(error))
        write_json(out / "status.json", status)
        retained_costs = [json.loads(path.read_text()) for path in sorted(raw.glob("*.cost.json"))]
        failure_artifacts = [dict(path=str(path.relative_to(out)), bytes=path.stat().st_size, sha256=sha256(path))
                             for path in sorted(raw.iterdir()) if path.is_file()]
        write_json(out / "summary.json", dict(
            state="FAILED", launch_sha=launch_sha, status=status, batch_costs=retained_costs,
            artifacts=failure_artifacts,
            wall_seconds=time.perf_counter() - start,
            scope="incomplete technical attempt; no complete primary paired reading"))
        raise
