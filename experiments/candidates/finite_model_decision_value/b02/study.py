"""B02 fixed five-arm planning-budget study over the frozen B01 NEAR evaluator.

The calibration exposure is fixed at four lawful moves; the intervention is
planner particle count.
Each arm has its own subsequent host and local filters. All contrasts use matched
new context IDs; root diagnostics reuse samples already written by B01.
"""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import platform
import resource
import time

import numpy as np

from experiments.candidates.finite_model_decision_value.b01.study import (
    Config as B01Config, THETAS, calibration_posterior, difference_reading,
    evaluate_batch, sha256, write_json,
)


@dataclass(frozen=True)
class ArmSpec:
    name: str
    mode: str | None
    calibration_k: int | None
    particles: int


@dataclass(frozen=True)
class Config:
    seed: int = 925831
    model_seed: int = 926073
    calibration_phase: int = 50
    evaluation_phase: int = 51
    model_phase: int = 52
    contexts: int = 256
    batch: int = 16
    horizon: int = 96
    particles_low: int = 32
    particles_high: int = 256
    calibration_steps: int = 4


SOURCE_B01 = "b40ea0965788f0d04b023870c34f47e86a00ceff"
METRICS = ("completed_jobs", "service", "conflicts", "wait_ticks", "packets")
RECORD_FIELDS = ("own", "last_sent", "last_sent_time", "peer_packet",
                 "peer_packet_time", "available", "root_joint_weights")
SAMPLE_FIELDS = ("sample_delta", "near_end", "opportunity_tick", "opportunity_kind")


def arm_specs(config):
    """The four named modes and one AF control are explicit, with no budget sweep."""
    arms = (
        ArmSpec(f"P_k4_M{config.particles_low}", "POSTERIOR_MEAN", 4, config.particles_low),
        ArmSpec(f"U_k4_M{config.particles_low}", "JOINT", 4, config.particles_low),
        ArmSpec(f"P_k4_M{config.particles_high}", "POSTERIOR_MEAN", 4, config.particles_high),
        ArmSpec(f"U_k4_M{config.particles_high}", "JOINT", 4, config.particles_high),
        ArmSpec("AF", None, None, 0),
    )
    for arm in arms[:-1]:
        if (arm.name.startswith("U") != (arm.mode == "JOINT") or
                arm.calibration_k != 4):
            raise AssertionError("B01 mode dispatch or calibration exposure changed")
    return arms


def _labels(config):
    return dict(p_low=f"P_k4_M{config.particles_low}",
                u_low=f"U_k4_M{config.particles_low}",
                p_high=f"P_k4_M{config.particles_high}",
                u_high=f"U_k4_M{config.particles_high}")


def _validate_config(config):
    if (config.contexts <= 0 or config.batch <= 0 or config.horizon <= 0 or
            config.horizon % 48 or config.calibration_steps != 4 or
            config.particles_low < 2 or config.particles_high <= config.particles_low):
        raise ValueError("invalid fixed four-move, two-budget study configuration")
    # SeedSequence takes nonnegative integer addresses.
    if any(int(value) != value or value < 0 for value in (
            config.seed, config.model_seed, config.calibration_phase,
            config.evaluation_phase, config.model_phase)):
        raise ValueError("RNG addresses must be nonnegative integers")


def collect_calibration(config, ids):
    """Draw a persistent context law; expose only four unsaturated positions to fit."""
    if config.calibration_steps != 4:
        raise ValueError("B02 uses exactly four controlled moves")
    theta, paths = [], []
    for context in ids:
        source = np.random.default_rng(np.random.SeedSequence(
            [config.seed, config.calibration_phase, int(context), 0]))
        actual = THETAS[int(source.integers(len(THETAS)))]
        movement = np.random.default_rng(np.random.SeedSequence(
            [config.seed, config.calibration_phase, int(context), 1]))
        distance = 33
        positions = [distance]
        for _ in range(4):
            distance -= int(movement.random() < actual)
            positions.append(distance)
        theta.append(actual)
        paths.append(positions)
    return np.asarray(theta, dtype=np.float64), np.asarray(paths, dtype=np.int16)


def _b01_config(config, particles):
    return B01Config(seed=config.seed, model_seed=config.model_seed,
        contexts=config.contexts, batch=config.batch, horizon=config.horizon,
        particles=particles, calibration_steps=4,
        calibration_phase=config.calibration_phase,
        evaluation_phase=config.evaluation_phase, model_phase=config.model_phase)


def _same_history_at_tick_zero(traces, labels):
    reference = traces[labels["p_low"]]
    for arm in (labels["u_low"], labels["p_high"], labels["u_high"]):
        for name in RECORD_FIELDS:
            if not np.array_equal(reference[name][:, 0], traces[arm][name][:, 0]):
                raise AssertionError(f"initial local history differs for {arm}: {name}")
        if not np.all(traces[arm]["evaluated"][:, 0]):
            raise AssertionError(f"initial optional roots missing for {arm}")
    if not np.all(reference["evaluated"][:, 0]):
        raise AssertionError("initial optional roots missing for low-budget plug-in arm")


def _nested_variance(samples, low):
    """Plug-in iid fixed-root Var(high-minus-prefix-low); diagnostic only."""
    samples = np.asarray(samples, dtype=np.float64)
    return float(samples.var(ddof=1) * (1 / low - 1 / len(samples)))


def initial_root_diagnostics(traces, ids, config):
    """Describe common tick-zero samples; construct no additional model rollouts."""
    labels = _labels(config)
    _same_history_at_tick_zero(traces, labels)
    low, high = config.particles_low, config.particles_high
    results = []
    for row, context in enumerate(ids):
        for short_name, long_name in ((labels["p_low"], labels["p_high"]),
                                      (labels["u_low"], labels["u_high"])):
            shorter = traces[short_name]
            longer = traces[long_name]
            for field in SAMPLE_FIELDS:
                if not np.array_equal(shorter[field][row, 0], longer[field][row, 0, :low]):
                    raise AssertionError(f"{short_name} nested {field} prefix differs for context {context}")
        paired = {}
        for label, count, p_name, u_name in (
                ("low", low, labels["p_low"], labels["u_low"]),
                ("high", high, labels["p_high"], labels["u_high"])):
            p = traces[p_name]["sample_delta"][row, 0]
            u = traces[u_name]["sample_delta"][row, 0]
            differences = u - p
            paired[label] = dict(
                p_delta=float(p.mean()), u_delta=float(u.mean()),
                paired_u_minus_p=float(differences.mean()),
                paired_u_minus_p_mc_se=float(differences.std(ddof=1) / np.sqrt(count)),
                p_mc_se=float(traces[p_name]["mc_se"][row, 0]),
                u_mc_se=float(traces[u_name]["mc_se"][row, 0]),
                p_exact_zero=bool(p.mean() == 0), u_exact_zero=bool(u.mean() == 0),
                p_all_samples_zero=bool(np.all(p == 0)),
                u_all_samples_zero=bool(np.all(u == 0)),
                p_send=bool(traces[p_name]["sent"][row, 0]),
                u_send=bool(traces[u_name]["sent"][row, 0]),
            )
        p_high = traces[labels["p_high"]]["sample_delta"][row, 0]
        u_high = traces[labels["u_high"]]["sample_delta"][row, 0]
        results.append(dict(context=int(context), tick=0, nested_prefix_verified=True,
            **{"posterior_mean_nested_variance_estimate": _nested_variance(p_high, low),
               "joint_nested_variance_estimate": _nested_variance(u_high, low),
               "paired_u_minus_p_nested_variance_estimate": _nested_variance(u_high-p_high, low)},
            estimate="sample variance over high-budget tick-zero paired particles times (1/Mlow-1/Mhigh); conditional iid plug-in only",
            low=paired["low"], high=paired["high"]))
    return results


def _paired_arrays(episodes, config):
    labels = _labels(config)
    names = (*labels.values(), "AF")
    if len(episodes) != 5 * config.contexts or {row["arm"] for row in episodes} != set(names):
        raise ValueError("exactly five complete matched context panels are required")
    by_arm = {arm: sorted((r for r in episodes if r["arm"] == arm),
                          key=lambda r: r["context"]) for arm in names}
    ids = [row["context"] for row in by_arm["AF"]]
    if (ids != list(range(config.contexts)) or
            any([row["context"] for row in by_arm[arm]] != ids for arm in names)):
        raise ValueError("all five complete matched context panels are required")
    arrays = {arm: {metric: np.asarray([row[metric] for row in rows], dtype=np.float64)
                    for metric in METRICS} for arm, rows in by_arm.items()}
    return ids, by_arm, arrays


def summarize(episodes, root_diagnostics, config):
    ids, by_arm, arrays = _paired_arrays(episodes, config)
    if [item["context"] for item in sorted(root_diagnostics, key=lambda x: x["context"])] != ids:
        raise ValueError("one verified initial root per matched context is required")
    labels = _labels(config)
    p_low, u_low, p_high, u_high = (labels[key] for key in
                                     ("p_low", "u_low", "p_high", "u_high"))
    pairs = ((u_low, p_low), (u_high, p_high), (u_high, u_low), (p_high, p_low),
             (p_low, "AF"), (u_low, "AF"), (p_high, "AF"), (u_high, "AF"))
    contrast_arrays = {
        f"{left}-{right}": {metric: arrays[left][metric] - arrays[right][metric]
                            for metric in METRICS} for left, right in pairs}
    interaction = (arrays[u_high]["completed_jobs"] - arrays[p_high]["completed_jobs"] -
                   arrays[u_low]["completed_jobs"] + arrays[p_low]["completed_jobs"])
    contrast_arrays["I"] = {metric: (arrays[u_high][metric] - arrays[p_high][metric] -
                                      arrays[u_low][metric] + arrays[p_low][metric])
                             for metric in METRICS}
    per_context = []
    for row, context in enumerate(ids):
        per_context.append(dict(context=int(context), theta=float(by_arm["AF"][row]["theta"]),
            arms={arm: {metric: float(arrays[arm][metric][row]) for metric in METRICS}
                  for arm in arrays},
            contrasts={name: {metric: float(values[metric][row]) for metric in METRICS}
                       for name, values in contrast_arrays.items()}))
    strata = {}
    for theta in THETAS:
        mask = np.asarray([entry["theta"] == float(theta) for entry in per_context])
        if mask.any():
            strata[str(float(theta))] = difference_reading(interaction[mask])
    return dict(
        estimand="Exploratory paired context mean of finite-program budget interaction",
        arms={arm: {metric: float(values.mean()) for metric, values in metrics.items()}
              for arm, metrics in arrays.items()},
        contrasts={name: {metric: difference_reading(values)
                          for metric, values in metrics.items()}
                   for name, metrics in contrast_arrays.items()},
        primary_interaction=f"I=({u_high}-{p_high})-({u_low}-{p_low})",
        parameter_strata_primary=strata,
        initial_root=dict(contexts=len(root_diagnostics),
            p_action_changes=sum(item["low"]["p_send"] != item["high"]["p_send"]
                                 for item in root_diagnostics),
            u_action_changes=sum(item["low"]["u_send"] != item["high"]["u_send"]
                                 for item in root_diagnostics),
            low_u_p_action_differences=sum(item["low"]["u_send"] != item["low"]["p_send"]
                                       for item in root_diagnostics),
            high_u_p_action_differences=sum(item["high"]["u_send"] != item["high"]["p_send"]
                                        for item in root_diagnostics),
            nested_prefix_verified=all(item["nested_prefix_verified"] for item in root_diagnostics)),
        per_context=per_context)


def _artifact(path, out):
    return dict(path=str(path.relative_to(out)), bytes=path.stat().st_size, sha256=sha256(path))


def _existing_artifacts(out):
    named = [out / name for name in (
        "config.json", "status.json", "episodes.json", "per_context.json", "initial_roots.json")]
    raw = out / "raw"
    owned = [path for path in named if path.is_file()]
    if raw.is_dir():
        owned.extend(path for path in sorted(raw.rglob("*")) if path.is_file())
    return [_artifact(path, out) for path in owned]


def run_study(out, launch_sha, config=Config()):
    """Run exactly one fresh five-arm panel; preserve actual partial work on failure."""
    _validate_config(config)
    arms = arm_specs(config)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    scientific = ("config.json", "status.json", "summary.json", "episodes.json",
                  "per_context.json", "initial_roots.json", "raw")
    if any((out / name).exists() for name in scientific):
        raise FileExistsError("scientific output already exists; no automatic repeat")
    raw = out / "raw"
    raw.mkdir()
    start, cpu_start = time.perf_counter(), time.process_time()
    config_value = dict(**asdict(config), arms=[asdict(arm) for arm in arms],
        parameter_support=THETAS.tolist(), launch_sha=launch_sha,
        retained_b01_source=SOURCE_B01, nominal_receiver_probability=.75,
        threads={name: os.environ.get(name) for name in (
            "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
    write_json(out / "config.json", config_value)
    status = dict(state="RUNNING", completed_arm_contexts=0,
        planned_arm_contexts=5 * config.contexts, calibration_fits_started=0,
        calibration_fits_completed=0, completed_batches=0)
    write_json(out / "status.json", status)
    episodes, roots, batch_costs = [], [], []
    try:
        ids = tuple(range(config.contexts))
        mark = time.perf_counter()
        actual_theta, positions = collect_calibration(config, ids)
        collection_seconds = time.perf_counter() - mark
        status["calibration_fits_started"] = len(ids)
        mark = time.perf_counter()
        posterior, successes = calibration_posterior(positions.copy(), 4)
        fitting_seconds = time.perf_counter() - mark
        status["calibration_fits_completed"] = len(ids)
        np.savez_compressed(raw / "calibration.npz", ids=np.asarray(ids),
            positions=positions, actual_theta=actual_theta, q4=posterior, successes4=successes)
        write_json(out / "status.json", status)
        for begin in range(0, len(ids), config.batch):
            end = min(begin + config.batch, len(ids))
            traces = {}
            for arm in arms:
                if arm.name != "AF" and (arm.name.startswith("U") != (arm.mode == "JOINT") or
                                          arm.calibration_k != 4):
                    raise AssertionError("B01 evaluator mode dispatch differs from arm record")
                trace_file = raw / f"{arm.name}_{begin:04d}_{end:04d}.npz"
                arm_config = _b01_config(config, arm.particles if arm.particles else config.particles_low)
                rows, traces[arm.name], cost = evaluate_batch(
                    arm_config, ids[begin:end], actual_theta[begin:end],
                    posterior[begin:end], arm.name, trace_file)
                episodes.extend(rows)
                batch_costs.append(cost)
                status.update(completed_arm_contexts=status["completed_arm_contexts"]+len(rows),
                    last_arm=arm.name, last_context_exclusive=end)
                write_json(out / "episodes.json", episodes)
                write_json(out / "status.json", status)
            roots.extend(initial_root_diagnostics(traces, ids[begin:end], config))
            write_json(out / "initial_roots.json", roots)
            status["completed_batches"] += 1
            write_json(out / "status.json", status)
        reading = summarize(episodes, roots, config)
        write_json(out / "per_context.json", reading.pop("per_context"))
        model = {key: sum(cost["model"].get(key, 0) for cost in batch_costs)
                 for key in ("model_root_decisions", "model_branch_transitions",
                             "model_initialization_worlds", "synthetic_advance_draws",
                             "synthetic_job_draws")}
        model["model_root_particles"] = model["model_initialization_worlds"] // 2
        upper = config.contexts * 2 * (config.horizon * 3 // 4) * (
            config.particles_low + config.particles_high) * 2 * 32
        if model["model_branch_transitions"] > upper:
            raise AssertionError("model branch count exceeds declared conservative bound")
        status["state"] = "COMPLETE"
        write_json(out / "status.json", status)
        artifacts = _existing_artifacts(out)
        resources = dict(wall_seconds_through_artifact_hashing=time.perf_counter()-start,
            cpu_seconds=time.process_time()-cpu_start,
            peak_single_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            measurement_scope="scientific process through hashing; excludes final summary write and supervisor",
            python=platform.python_version(), numpy=np.__version__, node=platform.node(),
            raw_artifact_bytes=sum(item["bytes"] for item in artifacts
                                   if item["path"].startswith("raw/")))
        summary = dict(state="COMPLETE", launch_sha=launch_sha, config=config_value, **reading,
            counts=dict(calibration_fits_started=status["calibration_fits_started"],
                calibration_fits_completed=status["calibration_fits_completed"],
                calibration_steps=4*config.contexts, policy_fits_started=0,
                optimizer_updates=0, policy_parameter_updates=0,
                evaluation_episodes=len(episodes),
                evaluation_team_ticks=sum(cost["steps"] for cost in batch_costs),
                **model, model_branch_transition_upper=upper,
                model_root_particles_upper=config.contexts*2*(config.horizon*3//4)*(
                    config.particles_low+config.particles_high),
                model_initialization_worlds_upper=config.contexts*2*(config.horizon*3//4)*(
                    config.particles_low+config.particles_high)*2,
                synthetic_draws_each_upper=config.contexts*2*(config.horizon*3//4)*(
                    config.particles_low+config.particles_high)*config.horizon*2),
            calibration=dict(collection_seconds=collection_seconds,
                fitting_seconds=fitting_seconds,
                mean_parameter_variance=float(np.mean((posterior*THETAS**2).sum(axis=1)-
                    (posterior*THETAS).sum(axis=1)**2))),
            batch_costs=batch_costs, artifacts=artifacts, resources=resources,
            inference_scope="B01 approximate joint filter, fixed nominal receiver and NEAR/AF",
            failure_policy="No replacement contexts, zero filling, automatic retry or post-score extension")
        write_json(out / "summary.json", summary)
        return summary
    except Exception as error:
        status.update(state="FAILED", error_type=type(error).__name__, error=str(error))
        write_json(out / "status.json", status)
        retained_costs = [json.loads(path.read_text()) for path in sorted(raw.glob("*.cost.json"))]
        write_json(out / "summary.json", dict(
            state="FAILED", launch_sha=launch_sha, status=status,
            batch_costs=retained_costs, artifacts=_existing_artifacts(out),
            wall_seconds=time.perf_counter()-start,
            scope="incomplete technical attempt; no complete primary paired reading"))
        raise
