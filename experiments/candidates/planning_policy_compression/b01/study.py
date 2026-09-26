"""Fixed two-block BC/WBC study with a callable small correctness fixture."""

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import json
import os
import platform
import resource
import time

import numpy as np
import torch
from torch.nn import functional as F

from experiments.candidates.finite_model_decision_value.b01.belief import JointPhysicalBelief, take_local
from experiments.candidates.finite_model_decision_value.b01.host import CrossingHost, Worlds, FRAME
from experiments.candidates.finite_model_decision_value.b01.planning import paired_values, select_record
from experiments.candidates.finite_model_decision_value.b01.study import (
    THETAS, difference_reading, threshold_requests, write_json, sha256,
)
from experiments.candidates.finite_model_decision_value.b02.study import collect_calibration
from experiments.candidates.finite_model_decision_value.b01.study import calibration_posterior
from .model import Student, features

SOURCE_B01 = "experiments/candidates/finite_model_decision_value/b01"
ARMS = ("BC0", "WBC0", "BC1", "WBC1", "P_k4_M32", "AF")
METRICS = ("completed_jobs", "service", "conflicts", "wait_ticks", "packets", "forced_packets")


@dataclass(frozen=True)
class Config:
    block_seeds: tuple = (925941, 925942)
    block_model_seeds: tuple = (926141, 926142)
    evaluation_seed: int = 925943
    evaluation_model_seed: int = 926143
    collect_phases: tuple = (70, 71, 72)
    evaluation_phases: tuple = (80, 81, 82)
    initial_contexts: int = 256
    rollout_contexts: int = 128
    evaluation_contexts: int = 256
    horizon: int = 96
    batch: int = 16
    epochs: tuple = (40, 40)
    train_batch: int = 64
    particles: int = 32


def _validate(config):
    if (len(config.block_seeds) != 2 or len(config.block_model_seeds) != 2 or
            len(config.collect_phases) != 3 or len(config.evaluation_phases) != 3 or
            min(config.initial_contexts, config.rollout_contexts,
                config.evaluation_contexts, config.batch, config.train_batch,
                *config.epochs) <= 0 or config.horizon % 48 or config.particles < 2 or
            config.train_batch > config.initial_contexts * 2):
        raise ValueError("invalid fixed-shaped study/fixture configuration")
    if any(int(x) != x or x < 0 for x in (
            *config.block_seeds, *config.block_model_seeds,
            config.evaluation_seed, config.evaluation_model_seed,
            *config.collect_phases, *config.evaluation_phases)):
        raise ValueError("RNG addresses must be nonnegative integers")


def _artifact(path, out):
    return dict(path=str(path.relative_to(out)), bytes=path.stat().st_size, sha256=sha256(path))


def _artifacts(out):
    named = [out / name for name in ("config.json", "status.json", "episodes.json",
                                     "curves.json", "per_context.json")]
    raw = out / "raw"
    owned = [path for path in named if path.is_file()]
    if raw.is_dir():
        owned.extend(path for path in sorted(raw.rglob("*")) if path.is_file())
    return [_artifact(path, out) for path in owned]


def _state_hash(state):
    digest = hashlib.sha256()
    for name, value in sorted(state.items()):
        array = value.detach().cpu().contiguous().numpy()
        digest.update(name.encode())
        digest.update(str(array.shape).encode())
        digest.update(str(array.dtype).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def _sum_counts(target, source):
    for name, value in source.items():
        target[name] = target.get(name, 0) + int(value)


def calibration(seed, phase, ids):
    """Four addressed moves; identical to the old corridor's four-move prefix."""
    proxy = type("CalibrationConfig", (), dict(seed=seed, calibration_phase=phase, calibration_steps=4))()
    mark = time.perf_counter()
    theta, positions = collect_calibration(proxy, ids)
    generation_seconds = time.perf_counter() - mark
    mark = time.perf_counter()
    posterior, successes = calibration_posterior(positions, 4)
    posterior_seconds = time.perf_counter() - mark
    moves = positions[:, :-1] - positions[:, 1:]
    return (theta, positions, posterior, successes, moves.astype(np.float32),
            generation_seconds, posterior_seconds)


def _policy_step(model, vector, memory):
    with torch.no_grad():
        logits, memory = model(torch.from_numpy(vector[:, None, :]), memory)
    return logits[:, 0].numpy() >= 0, memory


def episode_batch(ids, theta, posterior, moves, *, seed, phase, model_seed,
                  model_phase, config, arm, model=None, labels=False, trace_path=None):
    """Execute complete matched worlds; label actual histories at optional roots."""
    started, cpu_started = time.perf_counter(), time.process_time()
    timing = dict(feature_seconds=0., filter_seconds=0., query_seconds=0.,
                  network_seconds=0., environment_seconds=0., trace_save_seconds=0.)
    counters, filter_counts = {}, {}
    host = CrossingHost(Worlds.make(seed, phase, ids, config.horizon, theta))
    belief = None
    if labels or arm == "P_k4_M32":
        mark = time.perf_counter()
        belief = [JointPhysicalBelief(take_local(host, a), THETAS, posterior) for a in range(2)]
        timing["filter_seconds"] += time.perf_counter() - mark
    memories = [None, None]
    if model is not None:
        model.eval()
    sequence = np.zeros((len(ids), 2, config.horizon, 35), np.float32) if labels else None
    target = np.zeros((len(ids), 2, config.horizon), np.float32) if labels else None
    eligible_trace = np.zeros((len(ids), 2, config.horizon), bool) if labels else None
    delta_trace = np.zeros((len(ids), 2, config.horizon), np.float64) if labels else None
    mc_se_trace = np.zeros((len(ids), 2, config.horizon), np.float64) if labels else None
    trace = {name: np.zeros((len(ids), config.horizon), dtype=dtype) for name, dtype in (
        ("requested", bool), ("sent", bool), ("eligible", bool), ("reward", np.float32),
        ("completed_jobs", np.int64), ("conflicts", np.int64),
        ("wait_ticks", np.int64), ("packets", np.int64), ("forced_packets", np.int64))}
    zero_roots = tie_roots = nonzero_roots = optional_roots = 0
    executed_ticks = observed_ticks = feature_ticks = 0
    failure = None
    try:
        for tick in range(config.horizon):
            records = [take_local(host, a) for a in range(2)]
            if belief is not None and tick:
                mark = time.perf_counter()
                for a in range(2):
                    belief[a].update(records[a])
                timing["filter_seconds"] += time.perf_counter() - mark
            observed_ticks = tick + 1
            vectors = None
            if labels or model is not None:
                mark = time.perf_counter()
                vectors = [features(record, moves) for record in records]
                timing["feature_seconds"] += time.perf_counter() - mark
                feature_ticks = tick + 1
            if labels:
                for a in range(2):
                    sequence[:, a, tick] = vectors[a]
            sender = tick % 2
            active = records[sender].own[:, 0] != 2
            eligible = records[sender].available & (tick % FRAME < FRAME - 2)
            requested = active.copy()  # unchanged AF request, including forced ticks
            trace["eligible"][:, tick] = eligible
            if model is not None:
                mark = time.perf_counter()
                actions = []
                for a in range(2):
                    action, memories[a] = _policy_step(model, vectors[a], memories[a])
                    actions.append(action)
                requested[eligible] = actions[sender][eligible]
                timing["network_seconds"] += time.perf_counter() - mark
            if belief is not None and eligible.any():
                selected = np.flatnonzero(eligible)
                mark = time.perf_counter()
                b = belief[sender]
                result = paired_values(select_record(records[sender], selected),
                    b.weights[selected], b.theta_values[selected], b.states,
                    tuple(ids[i] for i in selected), seed=model_seed,
                    phase=model_phase, particles=config.particles,
                    mode="POSTERIOR_MEAN", counters=counters)
                timing["query_seconds"] += time.perf_counter() - mark
                teacher = threshold_requests(result["delta"], active[selected])
                if arm == "P_k4_M32" or arm == "TEACHER":
                    requested[selected] = teacher
                if labels:
                    eligible_trace[selected, sender, tick] = True
                    target[selected, sender, tick] = teacher.astype(np.float32)
                    delta_trace[selected, sender, tick] = result["delta"]
                    mc_se_trace[selected, sender, tick] = result["mc_se"]
                optional_roots += len(selected)
                zero = result["delta"] == 0
                zero_roots += int(zero.sum())
                tie_roots += int(np.count_nonzero(zero & teacher))
                nonzero_roots += int((~zero).sum())
            mark = time.perf_counter()
            trace["requested"][:, tick] = requested
            trace["sent"][:, tick] = records[sender].available & (requested | (tick % FRAME >= FRAME - 2))
            trace["reward"][:, tick] = host.step(requested)
            for name in ("completed_jobs", "conflicts", "wait_ticks", "packets", "forced_packets"):
                trace[name][:, tick] = host.metrics[name]
            executed_ticks = tick + 1
            timing["environment_seconds"] += time.perf_counter() - mark
        if belief is not None:
            for b in belief:
                _sum_counts(filter_counts, b.stats)
        rows = []
        for i, row in enumerate(host.rows()):
            row.update(context=int(ids[i]), theta=float(theta[i]), arm=arm)
            if row["packets"] != config.horizon // 8 * 2:
                raise AssertionError("frozen packet quota not exhausted")
            rows.append(row)
        data = None
        if labels:
            data = dict(x=sequence.reshape(len(ids) * 2, config.horizon, 35),
                        y=target.reshape(len(ids) * 2, config.horizon),
                        mask=eligible_trace.reshape(len(ids) * 2, config.horizon),
                        delta=delta_trace.reshape(len(ids) * 2, config.horizon),
                        mc_se=mc_se_trace.reshape(len(ids) * 2, config.horizon),
                        context=np.repeat(np.asarray(ids), 2),
                        agent=np.tile(np.arange(2), len(ids)))
    except Exception as error:
        failure = dict(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        if belief is not None:
            filter_counts = {}
            for b in belief:
                _sum_counts(filter_counts, b.stats)
        if trace_path is not None:
            mark = time.perf_counter()
            stored = {key: value[:, :executed_ticks] for key, value in trace.items()}
            if labels:
                stored.update(x=sequence[:, :, :feature_ticks].reshape(len(ids) * 2, feature_ticks, 35),
                    y=target[:, :, :feature_ticks].reshape(len(ids) * 2, feature_ticks),
                    mask=eligible_trace[:, :, :feature_ticks].reshape(len(ids) * 2, feature_ticks),
                    delta=delta_trace[:, :, :feature_ticks].reshape(len(ids) * 2, feature_ticks),
                    mc_se=mc_se_trace[:, :, :feature_ticks].reshape(len(ids) * 2, feature_ticks),
                    context=np.repeat(np.asarray(ids), 2), agent=np.tile(np.arange(2), len(ids)))
            np.savez_compressed(trace_path, ids=np.asarray(ids),
                observed_ticks=np.asarray(observed_ticks), feature_ticks=np.asarray(feature_ticks),
                executed_ticks=np.asarray(executed_ticks), **stored)
            timing["trace_save_seconds"] += time.perf_counter()-mark
        cost = dict(state="FAILED" if failure else "COMPLETE", failure=failure, arm=arm,
            contexts=list(map(int, ids)), observed_ticks=observed_ticks,
            feature_ticks=feature_ticks, executed_ticks=executed_ticks,
            executed_team_ticks=executed_ticks * len(ids),
            completed_team_ticks=(config.horizon * len(ids)) if not failure else 0,
            team_ticks=(config.horizon * len(ids)) if not failure else 0,
            optional_roots=optional_roots, exact_zero_roots=zero_roots,
            zero_af_send_fallbacks=tie_roots, nonzero_roots=nonzero_roots,
            model=counters, filter=filter_counts, timing=timing,
            wall_seconds=time.perf_counter() - started,
            cpu_seconds=time.process_time() - cpu_started)
        if trace_path is not None:
            write_json(Path(trace_path).with_suffix(".cost.json"), dict(
                **cost, measurement_boundary="through trace write; excludes cost metadata write"))
    return rows, data, cost


def _merge(parts):
    return {key: np.concatenate([part[key] for part in parts]) for key in parts[0]}


def stage_weights(data):
    g = np.minimum(np.abs(data["delta"][data["mask"]]) / .25, 4.)
    if not len(g):
        raise ValueError("training stage has no optional roots")
    mean = float(g.mean())
    w = .5 + .5 * (.1 + g) / (.1 + mean)
    weights = np.zeros_like(data["delta"], dtype=np.float32)
    weights[data["mask"]] = w
    return weights, dict(eligible=int(len(g)), g_mean=mean,
                         weight_min=float(w.min()), weight_mean=float(w.mean()),
                         weight_max=float(w.max()), zero_delta=int((g == 0).sum()))


def _movement(model, initial):
    return float(np.sqrt(sum(torch.sum((value.detach() - initial[key]) ** 2).item()
                             for key, value in model.state_dict().items())))


def train_stage(model, optimizer, data, *, weighted, model_seed, block, stage,
                epochs, batch, initial, status_callback=None):
    model.train()
    weights, weight_info = stage_weights(data)
    x = torch.from_numpy(data["x"])
    y = torch.from_numpy(data["y"])
    mask = torch.from_numpy(data["mask"])
    w = torch.from_numpy(weights)
    curves = []
    updates = rows = 0
    for epoch in range(epochs):
        rng = np.random.default_rng(np.random.SeedSequence([model_seed, 90, block, stage, epoch]))
        order = rng.permutation(len(x))
        loss_sum = correct = eligible = 0.
        for selected in (order[i:i + batch] for i in range(0, len(order), batch)):
            # Full H96 unroll: memory is reset once per independent agent sequence.
            prediction, _ = model(x[selected])
            valid = mask[selected]
            n = int(valid.sum())
            if n == 0:
                raise AssertionError("batch has no optional roots")
            bce = F.binary_cross_entropy_with_logits(prediction[valid], y[selected][valid], reduction="none")
            local_w = w[selected][valid] if weighted else torch.ones_like(bce)
            loss = (bce * local_w).sum() / n
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            optimizer.step()
            loss_sum += float((bce.detach() * local_w).sum())
            correct += int(((prediction.detach()[valid] >= 0) == (y[selected][valid] >= .5)).sum())
            eligible += n
            updates += 1
            rows += len(selected) * x.shape[1]
            if status_callback is not None:
                status_callback(len(selected) * x.shape[1])
        curves.append(dict(stage=stage, epoch=epoch, loss=loss_sum / eligible,
                           eligible_accuracy=correct / eligible, eligible=int(eligible),
                           updates=updates, processed_agent_time_rows=rows,
                           parameter_movement_l2=_movement(model, initial)))
    return curves, updates, rows, weight_info


def endpoint_diagnostic(model, data, batch=64):
    """Read-only common-data endpoint disagreements after the stage finishes."""
    mark, cpu_mark = time.perf_counter(), time.process_time()
    model.eval()
    weights, info = stage_weights(data)
    ordinary = weighted = absolute_delta_wrong = n = 0.
    zero_n = zero_wrong = zero_af_n = zero_af_wrong = nonzero_n = nonzero_wrong = 0
    with torch.no_grad():
        for begin in range(0, len(data["x"]), batch):
            end = begin + batch
            predicted, _ = model(torch.from_numpy(data["x"][begin:end]))
            valid = data["mask"][begin:end]
            wrong = (predicted.numpy()[valid] >= 0) != (data["y"][begin:end][valid] >= .5)
            deltas = data["delta"][begin:end][valid]
            zero = deltas == 0
            zero_af = zero & (data["y"][begin:end][valid] >= .5)
            ordinary += int(wrong.sum())
            weighted += float((wrong * weights[begin:end][valid]).sum())
            absolute_delta_wrong += float((wrong * np.abs(deltas)).sum())
            n += int(valid.sum())
            zero_n += int(zero.sum())
            zero_wrong += int(wrong[zero].sum())
            zero_af_n += int(zero_af.sum())
            zero_af_wrong += int(wrong[zero_af].sum())
            nonzero_n += int((~zero).sum())
            nonzero_wrong += int(wrong[~zero].sum())
    return dict(eligible=int(n), ordinary_disagreement=ordinary / n,
                weighted_disagreement=weighted / n,
                zero_delta_roots=zero_n,
                zero_delta_disagreement=(zero_wrong / zero_n) if zero_n else None,
                zero_af_fallback_roots=zero_af_n,
                zero_af_fallback_disagreement=(zero_af_wrong / zero_af_n) if zero_af_n else None,
                nonzero_roots=nonzero_n,
                nonzero_disagreement=(nonzero_wrong / nonzero_n) if nonzero_n else None,
                mean_absolute_delta_times_disagreement=absolute_delta_wrong / n,
                processed_agent_time_rows=int(data["x"].shape[0] * data["x"].shape[1]),
                weight_mean=info["weight_mean"],
                wall_seconds=time.perf_counter()-mark,
                cpu_seconds=time.process_time()-cpu_mark)


def _readings(episodes, config):
    by_arm = {arm: sorted((r for r in episodes if r["arm"] == arm), key=lambda r: r["context"])
              for arm in ARMS}
    ids = list(range(config.evaluation_contexts))
    if any([row["context"] for row in rows] != ids for rows in by_arm.values()):
        raise ValueError("incomplete common evaluation panel")
    arrays = {arm: {metric: np.asarray([row[metric] for row in rows], dtype=float)
                    for metric in METRICS} for arm, rows in by_arm.items()}
    pairs = [(arm, ref) for arm in ARMS[:4] for ref in ("AF", "P_k4_M32")]
    pairs.extend((("WBC0", "BC0"), ("WBC1", "BC1"), ("P_k4_M32", "AF")))
    return dict(arms={arm: {metric: float(v.mean()) for metric, v in values.items()}
                       for arm, values in arrays.items()},
                contrasts={a + "-" + b: {metric: difference_reading(arrays[a][metric] - arrays[b][metric])
                                       for metric in METRICS} for a, b in pairs},
                per_context=[dict(context=i, theta=float(by_arm["AF"][i]["theta"]),
                                  arms={arm: {metric: float(values[metric][i]) for metric in METRICS}
                                        for arm, values in arrays.items()}) for i in ids])


def run_study(out, launch_sha, config=Config(), entry_started=None):
    """Four complete fits, one predetermined roll-in, one common matched panel."""
    _validate(config)
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in (
            "config.json", "status.json", "summary.json", "episodes.json",
            "curves.json", "per_context.json", "raw")):
        raise FileExistsError("scientific output already exists; no automatic retry")
    raw = out / "raw"
    raw.mkdir()
    started, cpu_started = time.perf_counter(), time.process_time()
    cfg = dict(**asdict(config), launch_sha=launch_sha, source_asset=SOURCE_B01,
               source_base="d5261580dcf6d7a23da9473a4ad4f175c312e6db",
               nominal_receiver_probability=.75, device="cpu", dtype="float32",
               parameter_count=sum(p.numel() for p in Student().parameters()),
               torch=torch.__version__, numpy=np.__version__, host=platform.node(),
               threads={name: os.environ.get(name) for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
    if cfg["parameter_count"] != 27329:
        raise AssertionError("student parameter count changed")
    write_json(out / "config.json", cfg)
    status = dict(state="RUNNING", policy_fits_started=0, policy_fits_completed=0,
                  optimizer_updates=0, processed_agent_time_rows=0,
                  collection_team_ticks=0, evaluation_team_ticks=0,
                  executed_collection_team_ticks=0, executed_evaluation_team_ticks=0,
                  calibration_contexts=0, calibration_moves=0,
                  calibration_fits=0, completed_batches=0)
    write_json(out / "status.json", status)
    episodes, costs, fits, curves, diagnostics = [], [], [], [], []
    fit_timing = {}
    timings = dict(calibration_generation_seconds=0., calibration_posterior_seconds=0.,
                   optimization_seconds=0., checkpoint_io_seconds=0., checkpoint_io_cpu_seconds=0.,
                   output_write_seconds=0., artifact_hash_seconds=0.,
                   deployment_setup_seconds={}, deployment_seconds={},
                   entry_import_and_startup_seconds=(time.perf_counter()-entry_started)
                   if entry_started is not None else None)
    model_counts = {}

    def save_json(path, value):
        mark = time.perf_counter()
        write_json(path, value)
        timings["output_write_seconds"] += time.perf_counter()-mark

    def save_npz(path, **values):
        mark = time.perf_counter()
        np.savez_compressed(path, **values)
        timings["output_write_seconds"] += time.perf_counter()-mark

    def save_status():
        save_json(out / "status.json", status)

    def save_checkpoint(name, model, optimizer=None):
        mark, cpu_mark = time.perf_counter(), time.process_time()
        torch.save(dict(model=model.state_dict(), optimizer=optimizer.state_dict() if optimizer else None),
                   raw / name)
        elapsed = time.perf_counter() - mark
        cpu_elapsed = time.process_time() - cpu_mark
        timings["checkpoint_io_seconds"] += elapsed
        timings["checkpoint_io_cpu_seconds"] += cpu_elapsed
        return elapsed, cpu_elapsed

    def collect(ids, theta, posterior, moves, seed, phase, model_seed, model_phase,
                arm, group, model=None, labels=False):
        parts = []
        for begin in range(0, len(ids), config.batch):
            batch_ids = ids[begin:begin + config.batch]
            sl = slice(begin, begin + len(batch_ids))
            trace_path = raw / f"{group}_{arm}_{begin:04d}.npz"
            try:
                rows, data, cost = episode_batch(batch_ids, theta[sl], posterior[sl], moves[sl],
                    seed=seed, phase=phase, model_seed=model_seed, model_phase=model_phase,
                    config=config, arm=arm, model=model, labels=labels, trace_path=trace_path)
            except Exception:
                partial = trace_path.with_suffix(".cost.json")
                if partial.is_file():
                    cost = json.loads(partial.read_text())
                    costs.append(cost)
                    _sum_counts(model_counts, cost["model"])
                    key = "executed_collection_team_ticks" if labels else "executed_evaluation_team_ticks"
                    status[key] += cost["executed_team_ticks"]
                    save_status()
                raise
            costs.append(cost)
            _sum_counts(model_counts, cost["model"])
            key = "executed_collection_team_ticks" if labels else "executed_evaluation_team_ticks"
            status[key] += cost["team_ticks"]
            if labels:
                parts.append(data)
                status["collection_team_ticks"] += cost["team_ticks"]
            else:
                # One compact batch write per method; the cumulative index is
                # written after its deployment timer, so later arms do not pay
                # for serializing earlier arms' rows.
                save_json(raw / f"{group}_{arm}_{begin:04d}.episodes.json", rows)
                episodes.extend(rows)
                status["evaluation_team_ticks"] += cost["team_ticks"]
            status["completed_batches"] += 1
            save_status()
        return _merge(parts) if labels else None

    try:
        models = {}
        for block, (seed, model_seed) in enumerate(zip(config.block_seeds, config.block_model_seeds)):
            ids = tuple(range(config.initial_contexts + 2 * config.rollout_contexts))
            theta, positions, posterior, successes, moves, generation, posterior_cost = calibration(
                seed, config.collect_phases[0], ids)
            timings["calibration_generation_seconds"] += generation
            timings["calibration_posterior_seconds"] += posterior_cost
            status["calibration_contexts"] += len(ids)
            status["calibration_moves"] += 4 * len(ids)
            status["calibration_fits"] += len(ids)
            save_npz(raw / f"calibration_block{block}.npz", ids=ids, theta=theta,
                     positions=positions, posterior=posterior, successes=successes)
            save_status()
            initial_ids = ids[:config.initial_contexts]
            first = collect(initial_ids, theta[:len(initial_ids)], posterior[:len(initial_ids)],
                moves[:len(initial_ids)], seed, config.collect_phases[1], model_seed,
                config.collect_phases[2], "TEACHER", f"block{block}_initial", labels=True)
            torch.manual_seed(seed)
            initial_model = Student()
            initial = {key: value.detach().clone() for key, value in initial_model.state_dict().items()}
            initial_digest = _state_hash(initial)
            for name in ("BC", "WBC"):
                arm = f"{name}{block}"
                status["policy_fits_started"] += 1
                save_status()
                init_mark, init_cpu = time.perf_counter(), time.process_time()
                model = Student()
                model.load_state_dict(initial)
                if _state_hash(model.state_dict()) != initial_digest:
                    raise AssertionError("paired initial parameter states differ")
                optimizer = torch.optim.Adam(model.parameters(), lr=.001)
                fit_timing[arm] = dict(initialization_wall_seconds=time.perf_counter()-init_mark,
                                       initialization_cpu_seconds=time.process_time()-init_cpu)
                checkpoint_wall, checkpoint_cpu = save_checkpoint(f"{arm}_initial.pt", model, optimizer)
                fit_timing[arm]["checkpoint_io_seconds"] = checkpoint_wall
                fit_timing[arm]["checkpoint_io_cpu_seconds"] = checkpoint_cpu
                save_status()
                mark, cpu_mark = time.perf_counter(), time.process_time()
                try:
                    c1, u1, r1, info1 = train_stage(model, optimizer, first, weighted=name == "WBC",
                        model_seed=model_seed, block=block, stage=1, epochs=config.epochs[0],
                        batch=config.train_batch, initial=initial,
                        status_callback=lambda n: status.update(optimizer_updates=status["optimizer_updates"] + 1,
                                                                 processed_agent_time_rows=status["processed_agent_time_rows"] + n))
                finally:
                    elapsed = time.perf_counter()-mark
                    timings["optimization_seconds"] += elapsed
                    fit_timing[arm]["stage1_optimization_wall_seconds"] = elapsed
                    fit_timing[arm]["stage1_optimization_cpu_seconds"] = time.process_time()-cpu_mark
                curves.extend([dict(arm=f"{name}{block}", **row) for row in c1])
                checkpoint_wall, checkpoint_cpu = save_checkpoint(f"{arm}_stage1.pt", model, optimizer)
                fit_timing[arm]["checkpoint_io_seconds"] += checkpoint_wall
                fit_timing[arm]["checkpoint_io_cpu_seconds"] += checkpoint_cpu
                models[f"{name}{block}"] = (model, optimizer, c1, u1, r1, info1)
                save_status()
            for name in ("BC", "WBC"):
                arm = f"{name}{block}"
                diagnostics.append(dict(arm=arm, stage=1,
                    **endpoint_diagnostic(models[arm][0], first, config.train_batch)))
            # A single predetermined augmentation: each stage1 policy visits its own worlds.
            parts = [first]
            for name, offset in (("BC", config.initial_contexts),
                                 ("WBC", config.initial_contexts + config.rollout_contexts)):
                indices = ids[offset:offset + config.rollout_contexts]
                model = models[f"{name}{block}"][0]
                parts.append(collect(indices, theta[offset:offset + len(indices)],
                    posterior[offset:offset + len(indices)], moves[offset:offset + len(indices)],
                    seed, config.collect_phases[1], model_seed, config.collect_phases[2],
                    f"{name}_ROLLIN", f"block{block}_rollin", model=model, labels=True))
            merged = _merge(parts)
            save_npz(raw / f"training_block{block}.npz", **merged)
            for name in ("BC", "WBC"):
                arm = f"{name}{block}"
                model, optimizer, c1, u1, r1, info1 = models[arm]
                mark, cpu_mark = time.perf_counter(), time.process_time()
                try:
                    c2, u2, r2, info2 = train_stage(model, optimizer, merged,
                        weighted=name == "WBC", model_seed=model_seed, block=block, stage=2,
                        epochs=config.epochs[1], batch=config.train_batch, initial=initial,
                        status_callback=lambda n: status.update(optimizer_updates=status["optimizer_updates"] + 1,
                                                                 processed_agent_time_rows=status["processed_agent_time_rows"] + n))
                finally:
                    elapsed = time.perf_counter()-mark
                    timings["optimization_seconds"] += elapsed
                    fit_timing[arm]["stage2_optimization_wall_seconds"] = elapsed
                    fit_timing[arm]["stage2_optimization_cpu_seconds"] = time.process_time()-cpu_mark
                curves.extend([dict(arm=arm, **row) for row in c2])
                checkpoint_wall, checkpoint_cpu = save_checkpoint(f"{arm}_final.pt", model, optimizer)
                fit_timing[arm]["checkpoint_io_seconds"] += checkpoint_wall
                fit_timing[arm]["checkpoint_io_cpu_seconds"] += checkpoint_cpu
                fit_timing[arm]["fit_wall_seconds"] = sum(fit_timing[arm][key] for key in (
                    "initialization_wall_seconds", "stage1_optimization_wall_seconds",
                    "stage2_optimization_wall_seconds", "checkpoint_io_seconds"))
                fit_timing[arm]["fit_cpu_seconds"] = sum(
                    fit_timing[arm][key] for key in ("initialization_cpu_seconds",
                    "stage1_optimization_cpu_seconds", "stage2_optimization_cpu_seconds",
                    "checkpoint_io_cpu_seconds"))
                fit_timing[arm]["fit_scope"] = "initialization, optimizer stages, checkpoints; shared collection excluded"
                fits.append(dict(arm=arm, block=block, updates=u1 + u2,
                    processed_agent_time_rows=r1 + r2, parameter_movement_l2=_movement(model, initial),
                    stage1_weights=info1, stage2_weights=info2, timing=fit_timing[arm],
                    stage1_final=c1[-1], stage2_final=c2[-1],
                    initial_state_sha256=initial_digest,
                    initial_checkpoint_sha256=sha256(raw / f"{arm}_initial.pt"),
                    stage1_checkpoint_sha256=sha256(raw / f"{arm}_stage1.pt"),
                    final_checkpoint_sha256=sha256(raw / f"{arm}_final.pt")))
                status["policy_fits_completed"] += 1
                save_status()
            for name in ("BC", "WBC"):
                arm = f"{name}{block}"
                diagnostics.append(dict(arm=arm, stage=2,
                    **endpoint_diagnostic(models[arm][0], merged, config.train_batch)))
            save_json(out / "curves.json", curves)
        eval_ids = tuple(range(config.evaluation_contexts))
        eval_theta, eval_positions, eval_q, eval_successes, eval_moves, generation, posterior_cost = calibration(
            config.evaluation_seed, config.evaluation_phases[0], eval_ids)
        eval_generation, eval_posterior_cost = generation, posterior_cost
        timings["calibration_generation_seconds"] += generation
        timings["calibration_posterior_seconds"] += posterior_cost
        status["calibration_contexts"] += len(eval_ids)
        status["calibration_moves"] += 4 * len(eval_ids)
        status["calibration_fits"] += len(eval_ids)
        save_npz(raw / "calibration_eval.npz", ids=eval_ids, theta=eval_theta,
                 positions=eval_positions, posterior=eval_q, successes=eval_successes)
        save_status()
        for arm in ARMS:
            mark = time.perf_counter()
            model = None
            if arm in models:
                model = Student()
                checkpoint = torch.load(raw / f"{arm}_final.pt", map_location="cpu", weights_only=False)
                model.load_state_dict(checkpoint["model"])
                del checkpoint
            timings["deployment_setup_seconds"][arm] = time.perf_counter() - mark
            mark = time.perf_counter()
            collect(eval_ids, eval_theta, eval_q, eval_moves, config.evaluation_seed,
                    config.evaluation_phases[1], config.evaluation_model_seed,
                    config.evaluation_phases[2], arm, "evaluation", model=model)
            timings["deployment_seconds"][arm] = time.perf_counter() - mark
            save_json(out / "episodes.json", episodes)
        reading = _readings(episodes, config)
        per_context = reading.pop("per_context")
        save_json(out / "per_context.json", per_context)
        save_json(out / "curves.json", curves)
        expected_collection = 2 * (config.initial_contexts + 2 * config.rollout_contexts) * config.horizon
        expected_eval = len(ARMS) * config.evaluation_contexts * config.horizon
        expected_updates = 4 * (config.epochs[0] * int(np.ceil(2 * config.initial_contexts / config.train_batch)) +
                                config.epochs[1] * int(np.ceil(2 * (config.initial_contexts + 2 * config.rollout_contexts) / config.train_batch)))
        expected_rows = 4 * 2 * config.horizon * (config.epochs[0] * config.initial_contexts +
                                                  config.epochs[1] * (config.initial_contexts + 2 * config.rollout_contexts))
        model_branch_transition_upper = (expected_collection +
            config.evaluation_contexts * config.horizon) * config.particles * 2 * 32
        if (status["collection_team_ticks"] != expected_collection or
            status["evaluation_team_ticks"] != expected_eval or
            status["optimizer_updates"] != expected_updates or
            status["processed_agent_time_rows"] != expected_rows or
            status["policy_fits_completed"] != 4):
            raise AssertionError("fixed work accounting mismatch")
        if model_counts.get("model_branch_transitions", 0) > model_branch_transition_upper:
            raise AssertionError("model branch transitions exceed conservative fixed bound")
        status["state"] = "COMPLETE"
        save_status()
        mark = time.perf_counter()
        artifacts = _artifacts(out)
        timings["artifact_hash_seconds"] += time.perf_counter()-mark
        eval_calibration = eval_generation
        # Conditional method totals attach the whole required shared calibration
        # exposure. They are not a split/allocation of a jointly acquired cost.
        deployment_costs = {}
        for arm in ARMS:
            setup = timings["deployment_setup_seconds"][arm]
            deployed = timings["deployment_seconds"][arm]
            required_calibration = 0. if arm == "AF" else eval_calibration
            if arm == "P_k4_M32":
                required_calibration += eval_posterior_cost
            deployment_costs[arm] = dict(setup_seconds=setup,
                batched_deployment_seconds=deployed,
                attached_shared_calibration_seconds=required_calibration,
                conditional_total_seconds=setup+deployed+required_calibration)
        model_counts["model_root_particles"] = model_counts.get("model_initialization_worlds", 0) // 2
        root_counts = {name: sum(cost.get(name, 0) for cost in costs) for name in (
            "optional_roots", "exact_zero_roots", "zero_af_send_fallbacks", "nonzero_roots")}
        summary = dict(state="COMPLETE", launch_sha=launch_sha, config=cfg, **reading,
            counts={**status, **model_counts, **root_counts,
                    "evaluation_optimizer_updates":0,
                    "model_branch_transition_upper":model_branch_transition_upper,
                    "endpoint_diagnostic_agent_time_rows":sum(
                        item["processed_agent_time_rows"] for item in diagnostics),
                    "expected_collection_team_ticks":expected_collection,
                    "expected_evaluation_team_ticks":expected_eval,
                    "expected_optimizer_updates":expected_updates,
                    "expected_processed_agent_time_rows":expected_rows},
            model_branch_transition_upper=model_branch_transition_upper,
            fits=fits, endpoint_diagnostics=diagnostics, batch_costs=costs,
            timing=timings, deployment_costs=deployment_costs,
            resources=dict(wall_seconds=time.perf_counter()-started,
                cpu_seconds=time.process_time()-cpu_started,
                peak_single_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                scope="single scientific process through artifact hashing, excluding final summary write"),
            artifacts=artifacts,
            inference_scope="exploratory two-block paired contexts; no confirmation or equivalence claim")
        write_json(out / "summary.json", summary)
        return summary
    except Exception as error:
        status.update(state="FAILED", error_type=type(error).__name__, error=str(error))
        save_status()
        save_json(out / "curves.json", curves)
        save_json(out / "episodes.json", episodes)
        write_json(out / "summary.json", dict(state="FAILED", launch_sha=launch_sha,
            status=status, fits=fits, fit_timing=fit_timing,
            endpoint_diagnostics=diagnostics,
            batch_costs=costs, timing=timings,
            artifacts=_artifacts(out), wall_seconds=time.perf_counter()-started,
            scope="incomplete technical attempt; completed counts only"))
        raise
