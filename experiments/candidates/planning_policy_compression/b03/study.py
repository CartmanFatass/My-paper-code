"""B03 retraining on one fixed B02 archive; no collection or teacher calls."""

from dataclasses import asdict, dataclass
from io import BytesIO
from math import ceil
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

from experiments.candidates.finite_model_decision_value.b01.study import (
    difference_reading, sha256, write_json,
)
from experiments.candidates.planning_policy_compression.b01.model import Student
from experiments.candidates.planning_policy_compression.b01.study import (
    _artifacts, _state_hash, calibration, endpoint_diagnostic, episode_batch,
    stage_weights,
)

ARCHIVE_SHA256 = "eba65c4c17b49a18c6376628913feabac79dd38ba497e8003808d79ebadb55a4"
ARCHIVE_BYTES = 1_041_468
ARCHIVE_PRODUCER_SHA = "443d392ec47a3e53652114d28084d48ce1e5d9e2"
ARMS = ("O", "S", "BC")
PAIRS = (("O", "S"), ("O", "BC"), ("S", "BC"))
METRICS = ("completed_jobs", "service", "jobs_started", "conflicts", "wait_ticks",
           "packets", "forced_packets", "delivered", "gate_disagreement",
           "unknown_gate", "gate_opportunities")


@dataclass(frozen=True)
class Config:
    initial_seeds: tuple = (926001, 926002)
    order_seeds: tuple = (926101, 926102)
    weight_seeds: tuple = (926201, 926202)
    evaluation_seeds: tuple = (926301, 926302)
    evaluation_model_seeds: tuple = (926401, 926402)
    evaluation_phases: tuple = (80, 81, 82)
    initial_contexts: int = 256
    rollout_contexts: int = 128
    evaluation_contexts: int = 256
    horizon: int = 96
    batch: int = 16
    train_batch: int = 64
    epochs: tuple = (40, 40)
    particles: int = 32


def _validate(config):
    seed_fields = ("initial_seeds", "order_seeds", "weight_seeds",
                   "evaluation_seeds", "evaluation_model_seeds")
    if (any(len(getattr(config, name)) != 2 for name in seed_fields) or
            any(len(set(getattr(config, name))) != 2 for name in seed_fields) or
            len(config.evaluation_phases) != 3 or len(config.epochs) != 2 or
            min(config.initial_contexts, config.rollout_contexts, config.evaluation_contexts,
                config.horizon, config.batch, config.train_batch, *config.epochs) <= 0 or
            config.horizon % 48 or config.particles < 2 or
            config.train_batch > 2 * config.initial_contexts):
        raise ValueError("invalid two-pair archive study configuration")
    addresses = (*config.initial_seeds, *config.order_seeds, *config.weight_seeds,
                 *config.evaluation_seeds, *config.evaluation_model_seeds,
                 *config.evaluation_phases)
    if any(int(value) != value or value < 0 for value in addresses):
        raise ValueError("RNG addresses must be nonnegative integers")
    independent_seeds = tuple(value for name in seed_fields for value in getattr(config, name))
    if len(set(independent_seeds)) != len(independent_seeds):
        raise ValueError("training and evaluation seed roles must be distinct")


def load_archive(path, config, expected_sha=ARCHIVE_SHA256, expected_bytes=ARCHIVE_BYTES):
    """Hash exactly the byte buffer parsed by NumPy, then freeze all saved arrays."""
    mark = time.perf_counter()
    blob = Path(path).read_bytes()
    read_seconds = time.perf_counter() - mark
    mark = time.perf_counter()
    digest = hashlib.sha256(blob).hexdigest()
    hash_seconds = time.perf_counter() - mark
    if digest != expected_sha or len(blob) != expected_bytes:
        raise ValueError("archived training bytes disagree with fixed digest/size")
    mark = time.perf_counter()
    with np.load(BytesIO(blob), allow_pickle=False) as archive:
        required = {"x", "y", "mask", "delta", "mc_se", "context", "agent"}
        if set(archive.files) != required:
            raise ValueError("archived training keys differ from fixed schema")
        data = {name: np.array(archive[name], copy=True) for name in required}
    n_context = config.initial_contexts + 2 * config.rollout_contexts
    n = n_context * 2
    h = config.horizon
    shapes = dict(x=(n, h, 35), y=(n, h), mask=(n, h), delta=(n, h),
                  mc_se=(n, h), context=(n,), agent=(n,))
    dtypes = dict(x=np.float32, y=np.float32, mask=np.bool_, delta=np.float64,
                  mc_se=np.float64, context=np.int64, agent=np.int64)
    for name in required:
        if data[name].shape != shapes[name] or data[name].dtype != dtypes[name]:
            raise ValueError(f"archive {name} shape/dtype differs from fixed schema")
    if (not np.array_equal(data["context"], np.repeat(np.arange(n_context), 2)) or
            not np.array_equal(data["agent"], np.tile(np.arange(2), n_context))):
        raise ValueError("archive context/agent order differs from fixed paired sequences")
    if any(not np.isfinite(data[name]).all() for name in ("x", "y", "delta", "mc_se")):
        raise ValueError("archive contains nonfinite numeric values")
    if not np.isin(data["y"][data["mask"]], (0., 1.)).all():
        raise ValueError("eligible teacher actions must be binary")
    ticks = np.arange(h)[None, :]
    invalid_optional = (ticks % 2 != data["agent"][:, None]) | (ticks % 8 >= 6)
    if np.any(data["mask"] & invalid_optional):
        raise ValueError("eligible mask includes a nonsender or forced tick")
    stage1 = data["context"] < config.initial_contexts
    if (int(stage1.sum()) != 2 * config.initial_contexts or
            not stage1[:2*config.initial_contexts].all() or
            stage1[2*config.initial_contexts:].any() or
            not data["mask"][stage1].any() or not data["mask"].any()):
        raise ValueError("archive stage assignment/eligibility differs from fixed contract")
    for value in data.values():
        value.setflags(write=False)
    return data, stage1, dict(sha256=digest, bytes=len(blob), read_seconds=read_seconds,
                               hash_seconds=hash_seconds,
                               parse_validate_seconds=time.perf_counter()-mark,
                               stage1_sequences=int(stage1.sum()), stage2_sequences=n,
                               stage1_eligible=int(data["mask"][stage1].sum()),
                               stage2_eligible=int(data["mask"].sum()))


def stage_data(data, stage1=None):
    if stage1 is None:
        return data
    return {name: value[stage1] for name, value in data.items()}


def weight_maps(data, pair, stage, weight_seed):
    """One fixed C-order shuffle for each saved teacher-action label."""
    original, info = stage_weights(data)
    shuffled = np.zeros_like(original)
    flat_mask = data["mask"].reshape(-1)
    flat_y = data["y"].reshape(-1)
    source_original = original.reshape(-1)
    maps = {}
    for label in (0, 1):
        destination = np.flatnonzero(flat_mask & (flat_y == label)).astype(np.int64)
        generator = np.random.default_rng(np.random.SeedSequence(
            [weight_seed, 91, stage, label]))
        source = destination[generator.permutation(len(destination))]
        shuffled.reshape(-1)[destination] = source_original[source]
        if not np.array_equal(np.sort(shuffled.reshape(-1)[destination]),
                              np.sort(source_original[destination])):
            raise AssertionError("stage/label weight multiset changed")
        maps[f"label{label}_destination"] = destination
        maps[f"label{label}_source"] = source
    if not np.array_equal(original[~data["mask"]], shuffled[~data["mask"]]):
        raise AssertionError("ineligible weights changed")
    if not np.isclose(float(shuffled[data["mask"]].sum(dtype=np.float64)),
                      float(original[data["mask"]].sum(dtype=np.float64)),
                      rtol=2e-7, atol=2e-4):
        raise AssertionError("weight sum changed outside float32 roundoff")
    unit = data["mask"].astype(np.float32)
    identity = dict(pair=pair, stage=stage, weight_seed=weight_seed,
        eligible=info["eligible"], original_weight_mean=info["weight_mean"],
        shuffled_weight_mean=float(shuffled[data["mask"]].mean(dtype=np.float64)),
        label_counts={str(label):len(maps[f"label{label}_destination"]) for label in (0, 1)},
        changed_assignments=int(np.count_nonzero(shuffled != original)))
    arrays = dict(original=original, shuffled=shuffled, unit=unit, **maps)
    identity["array_sha256"] = {name:hashlib.sha256(value.tobytes()).hexdigest()
                                 for name,value in arrays.items()}
    return arrays, identity


def train_explicit(model, optimizer, data, weights, *, order_seed, pair, stage,
                   epochs, batch, initial, status_callback=None):
    """B01 full-sequence Adam path with caller-supplied eligible weights."""
    if (weights.shape != data["mask"].shape or weights.dtype != np.float32 or
            np.any(weights[~data["mask"]] != 0) or
            not np.isfinite(weights).all() or np.any(weights[data["mask"]] <= 0)):
        raise ValueError("explicit weights must be positive exactly at eligible roots")
    model.train()
    # The archive stays read-only; PyTorch receives private writable storage.
    x = torch.tensor(data["x"])
    y = torch.tensor(data["y"])
    mask = torch.tensor(data["mask"])
    w = torch.from_numpy(weights)
    curves = []
    updates = rows = 0
    for epoch in range(epochs):
        rng = np.random.default_rng(np.random.SeedSequence([order_seed, 90, pair, stage, epoch]))
        order = rng.permutation(len(x))
        loss_sum = correct = eligible = 0.
        for selected in (order[i:i + batch] for i in range(0, len(order), batch)):
            logits, _ = model(x[selected])
            valid = mask[selected]
            n = int(valid.sum())
            if n == 0:
                raise AssertionError("training batch has no optional roots")
            bce = F.binary_cross_entropy_with_logits(logits[valid], y[selected][valid], reduction="none")
            loss = (bce * w[selected][valid]).sum() / n
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            optimizer.step()
            loss_sum += float((bce.detach() * w[selected][valid]).sum())
            correct += int(((logits.detach()[valid] >= 0) == (y[selected][valid] >= .5)).sum())
            eligible += n
            updates += 1
            rows += len(selected) * x.shape[1]
            if status_callback is not None:
                status_callback(len(selected) * x.shape[1])
        movement = float(np.sqrt(sum(torch.sum((value.detach()-initial[name])**2).item()
                                     for name, value in model.state_dict().items())))
        curves.append(dict(stage=stage, epoch=epoch, loss=loss_sum/eligible,
            eligible_accuracy=correct/eligible, eligible=int(eligible), updates=updates,
            processed_agent_time_rows=rows, parameter_movement_l2=movement))
    return curves, updates, rows


def _read_pair(episodes, pair, config):
    by_arm = {arm: sorted((row for row in episodes if row["pair"] == pair and row["arm"] == arm),
                           key=lambda row: row["context"]) for arm in ARMS}
    ids = list(range(config.evaluation_contexts))
    if any([row["context"] for row in rows] != ids for rows in by_arm.values()):
        raise ValueError("incomplete matched pair evaluation panel")
    theta = [row["theta"] for row in by_arm["BC"]]
    if any([row["theta"] for row in rows] != theta for rows in by_arm.values()):
        raise ValueError("paired evaluation calibrations differ")
    arrays = {arm: {metric: np.asarray([row[metric] for row in rows], dtype=float)
                    for metric in METRICS} for arm, rows in by_arm.items()}
    totals = {a+"-"+b: int(sum(row["completed_jobs"] for row in by_arm[a]) -
                            sum(row["completed_jobs"] for row in by_arm[b])) for a,b in PAIRS}
    if totals["O-BC"] != totals["O-S"] + totals["S-BC"]:
        raise AssertionError("three contrast totals violate arithmetic identity")
    contrast = {a+"-"+b: {metric: difference_reading(arrays[a][metric]-arrays[b][metric])
                           for metric in METRICS} for a,b in PAIRS}
    contexts = [dict(pair=pair, context=i, theta=float(theta[i]),
        arms={arm: {metric: float(arrays[arm][metric][i]) for metric in METRICS} for arm in ARMS},
        completed_job_differences={a+"-"+b: int(arrays[a]["completed_jobs"][i]-
                                             arrays[b]["completed_jobs"][i]) for a,b in PAIRS})
        for i in ids]
    losses = {a+"-"+b: [dict(context=i, difference=int(arrays[a]["completed_jobs"][i]-
                                                    arrays[b]["completed_jobs"][i]))
                         for i in ids if arrays[a]["completed_jobs"][i] < arrays[b]["completed_jobs"][i]]
              for a,b in PAIRS}
    return dict(pair=pair, integer_completed_job_total_differences=totals,
        signed_completed_job_mean_differences={key:value/len(ids) for key,value in totals.items()},
        arms={arm: {metric: float(values.mean()) for metric,values in metrics.items()}
              for arm,metrics in arrays.items()}, contrasts=contrast,
        loss_worlds=losses, per_context=contexts)


def run_study(out, data_path, launch_sha, config=Config(), *,
              expected_sha=ARCHIVE_SHA256, expected_bytes=ARCHIVE_BYTES,
              entry_started=None):
    """One fresh six-fit conditional study; fixtures pass tiny data and config."""
    _validate(config)
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in (
            "config.json", "status.json", "summary.json", "episodes.json", "curves.json",
            "per_context.json", "raw")):
        raise FileExistsError("scientific output already exists; no automatic retry")
    raw = out / "raw"
    raw.mkdir()
    started, cpu_started = time.perf_counter(), time.process_time()
    status = dict(state="RUNNING", current_pair=None, pairs_completed=0,
        policy_fits_started=0, policy_fits_completed=0,
        optimizer_updates=0, processed_agent_time_rows=0,
        evaluation_team_ticks=0, executed_evaluation_team_ticks=0,
        calibration_contexts=0, calibration_moves=0, calibration_fits=0,
        completed_batches=0, training_collection_team_ticks=0,
        teacher_queries=0, model_branch_transitions=0)
    write_json(out / "status.json", status)
    timing = dict(input_read_seconds=0., input_hash_seconds=0., input_parse_validate_seconds=0.,
        weight_mapping_seconds=0., optimization_seconds=0., diagnostic_seconds=0.,
        calibration_generation_seconds=0., calibration_posterior_seconds=0.,
        checkpoint_io_seconds=0., checkpoint_io_cpu_seconds=0.,
        output_write_seconds=0., artifact_hash_seconds=0.,
        entry_import_and_startup_seconds=(time.perf_counter()-entry_started)
        if entry_started is not None else None)
    fits, curves, diagnostics, episodes, costs, pair_results, mappings = [], [], [], [], [], [], []
    per_context = []
    fit_timing, pair_timing = {}, {}
    active_model = active_optimizer = active_key = None
    input_info = None

    def save_json(path, value):
        mark = time.perf_counter()
        write_json(path, value)
        timing["output_write_seconds"] += time.perf_counter()-mark

    def save_npz(path, **values):
        mark = time.perf_counter()
        np.savez_compressed(path, **values)
        timing["output_write_seconds"] += time.perf_counter()-mark

    def save_status():
        save_json(out / "status.json", status)

    def save_checkpoint(path, model, optimizer):
        mark, cpu_mark = time.perf_counter(), time.process_time()
        torch.save(dict(model=model.state_dict(), optimizer=optimizer.state_dict()), path)
        wall, cpu = time.perf_counter()-mark, time.process_time()-cpu_mark
        timing["checkpoint_io_seconds"] += wall
        timing["checkpoint_io_cpu_seconds"] += cpu
        return wall, cpu

    def evaluate(pair, arm, model, theta, posterior, moves):
        seed = config.evaluation_seeds[pair]
        model_seed = config.evaluation_model_seeds[pair]
        ids = tuple(range(config.evaluation_contexts))
        for begin in range(0, len(ids), config.batch):
            batch_ids = ids[begin:begin+config.batch]
            sl = slice(begin, begin+len(batch_ids))
            stem = f"pair{pair}_evaluation_{arm}_{begin:04d}"
            trace_path = raw / f"{stem}.npz"
            try:
                rows, _, cost = episode_batch(batch_ids, theta[sl], posterior[sl], moves[sl],
                    seed=seed, phase=config.evaluation_phases[1], model_seed=model_seed,
                    model_phase=config.evaluation_phases[2], config=config, arm=arm,
                    model=model, labels=False, trace_path=trace_path)
            except Exception:
                cost_path = trace_path.with_suffix(".cost.json")
                if cost_path.is_file():
                    cost = json.loads(cost_path.read_text())
                    cost["pair"] = pair
                    costs.append(cost)
                    status["executed_evaluation_team_ticks"] += cost["executed_team_ticks"]
                    save_status()
                raise
            cost["pair"] = pair
            costs.append(cost)
            status["executed_evaluation_team_ticks"] += cost["executed_team_ticks"]
            if cost["model"] or cost["filter"] or cost["optional_roots"]:
                save_status()
                raise AssertionError("student deployment performed teacher/filter work")
            status["evaluation_team_ticks"] += cost["team_ticks"]
            for row in rows:
                row["pair"] = pair
            save_json(raw / f"{stem}.episodes.json", rows)
            episodes.extend(rows)
            status["completed_batches"] += 1
            save_status()

    try:
        data, stage1_mask, input_info = load_archive(data_path, config, expected_sha, expected_bytes)
        timing["input_read_seconds"] = input_info["read_seconds"]
        timing["input_hash_seconds"] = input_info["hash_seconds"]
        timing["input_parse_validate_seconds"] = input_info["parse_validate_seconds"]
        first = stage_data(data, stage1_mask)
        stages = {1:first, 2:data}
        diagnostic_merged = dict(data, x=np.array(data["x"], copy=True))
        parameter_count = sum(p.numel() for p in Student().parameters())
        if parameter_count != 27329:
            raise AssertionError("frozen Student parameter count changed")
        cfg = dict(**asdict(config), launch_sha=launch_sha,
            archived_input=dict(path=str(Path(data_path).resolve()), **input_info),
            archive_producer_sha=ARCHIVE_PRODUCER_SHA, parameter_count=parameter_count,
            device="cpu", dtype="float32", torch=torch.__version__, numpy=np.__version__,
            host=platform.node(), threads={name:os.environ.get(name) for name in (
                "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
        save_json(out / "config.json", cfg)
        for pair in range(2):
            status["current_pair"] = pair
            pair_started, pair_cpu = time.perf_counter(), time.process_time()
            pair_timing[pair] = dict(state="RUNNING", deployment_costs={},
                calibration_generation_seconds=0., calibration_posterior_seconds=0.)
            save_status()
            maps = {}
            for stage in (1,2):
                mark = time.perf_counter()
                weights, identity = weight_maps(stages[stage], pair, stage,
                                                 config.weight_seeds[pair])
                timing["weight_mapping_seconds"] += time.perf_counter()-mark
                path = raw / f"pair{pair}_stage{stage}_weights.npz"
                save_npz(path, **weights)
                identity.update(path=str(path.relative_to(out)), sha256=sha256(path))
                mappings.append(identity)
                maps[stage] = weights
            torch.manual_seed(config.initial_seeds[pair])
            initial_model = Student()
            initial = {name: value.detach().clone() for name,value in initial_model.state_dict().items()}
            initial_hash = _state_hash(initial)
            models = {}
            for arm in ARMS:
                key = f"pair{pair}_{arm}"
                status["policy_fits_started"] += 1
                save_status()
                mark, cpu_mark = time.perf_counter(), time.process_time()
                model = Student()
                model.load_state_dict(initial)
                if _state_hash(model.state_dict()) != initial_hash:
                    raise AssertionError("paired initial tensors differ")
                optimizer = torch.optim.Adam(model.parameters(), lr=.001)
                fit_timing[key] = dict(initialization_wall_seconds=time.perf_counter()-mark,
                    initialization_cpu_seconds=time.process_time()-cpu_mark)
                wall,cpu = save_checkpoint(raw / f"{key}_initial.pt", model, optimizer)
                fit_timing[key].update(checkpoint_io_seconds=wall, checkpoint_io_cpu_seconds=cpu)
                models[arm] = (model, optimizer)
                active_model,active_optimizer,active_key = model,optimizer,key
                weight_name = {"O":"original", "S":"shuffled", "BC":"unit"}[arm]
                mark,cpu_mark = time.perf_counter(),time.process_time()
                try:
                    c1,u1,r1 = train_explicit(model,optimizer,first,maps[1][weight_name],
                        order_seed=config.order_seeds[pair], pair=pair, stage=1,
                        epochs=config.epochs[0], batch=config.train_batch, initial=initial,
                        status_callback=lambda n: status.update(
                            optimizer_updates=status["optimizer_updates"]+1,
                            processed_agent_time_rows=status["processed_agent_time_rows"]+n))
                finally:
                    elapsed = time.perf_counter()-mark
                    timing["optimization_seconds"] += elapsed
                    fit_timing[key]["stage1_optimization_wall_seconds"] = elapsed
                    fit_timing[key]["stage1_optimization_cpu_seconds"] = time.process_time()-cpu_mark
                curves.extend(dict(pair=pair,arm=arm,**row) for row in c1)
                wall,cpu = save_checkpoint(raw / f"{key}_stage1.pt", model, optimizer)
                fit_timing[key]["checkpoint_io_seconds"] += wall
                fit_timing[key]["checkpoint_io_cpu_seconds"] += cpu
                models[arm] = (model,optimizer,c1,u1,r1)
                active_model = active_optimizer = active_key = None
                save_status()
            for arm in ARMS:
                mark = time.perf_counter()
                diagnostics.append(dict(pair=pair,arm=arm,stage=1,
                    **endpoint_diagnostic(models[arm][0],first,config.train_batch)))
                timing["diagnostic_seconds"] += time.perf_counter()-mark
            for arm in ARMS:
                key = f"pair{pair}_{arm}"
                model,optimizer,c1,u1,r1 = models[arm]
                active_model,active_optimizer,active_key = model,optimizer,key
                weight_name = {"O":"original", "S":"shuffled", "BC":"unit"}[arm]
                mark,cpu_mark = time.perf_counter(),time.process_time()
                try:
                    c2,u2,r2 = train_explicit(model,optimizer,data,maps[2][weight_name],
                        order_seed=config.order_seeds[pair], pair=pair, stage=2,
                        epochs=config.epochs[1], batch=config.train_batch, initial=initial,
                        status_callback=lambda n: status.update(
                            optimizer_updates=status["optimizer_updates"]+1,
                            processed_agent_time_rows=status["processed_agent_time_rows"]+n))
                finally:
                    elapsed = time.perf_counter()-mark
                    timing["optimization_seconds"] += elapsed
                    fit_timing[key]["stage2_optimization_wall_seconds"] = elapsed
                    fit_timing[key]["stage2_optimization_cpu_seconds"] = time.process_time()-cpu_mark
                curves.extend(dict(pair=pair,arm=arm,**row) for row in c2)
                wall,cpu = save_checkpoint(raw / f"{key}_final.pt", model, optimizer)
                fit_timing[key]["checkpoint_io_seconds"] += wall
                fit_timing[key]["checkpoint_io_cpu_seconds"] += cpu
                fit_timing[key]["fit_wall_seconds"] = sum(fit_timing[key][part] for part in (
                    "initialization_wall_seconds","stage1_optimization_wall_seconds",
                    "stage2_optimization_wall_seconds","checkpoint_io_seconds"))
                fit_timing[key]["fit_cpu_seconds"] = sum(fit_timing[key][part] for part in (
                    "initialization_cpu_seconds","stage1_optimization_cpu_seconds",
                    "stage2_optimization_cpu_seconds","checkpoint_io_cpu_seconds"))
                fit_timing[key]["fit_scope"] = "initialization, both optimizer stages, checkpoints; shared archive excluded"
                movement = float(np.sqrt(sum(torch.sum((value.detach()-initial[name])**2).item()
                                             for name,value in model.state_dict().items())))
                fits.append(dict(pair=pair,arm=arm,updates=u1+u2,
                    processed_agent_time_rows=r1+r2,parameter_movement_l2=movement,
                    initial_state_sha256=initial_hash,
                    initial_checkpoint_sha256=sha256(raw / f"{key}_initial.pt"),
                    stage1_checkpoint_sha256=sha256(raw / f"{key}_stage1.pt"),
                    final_checkpoint_sha256=sha256(raw / f"{key}_final.pt"),
                    stage1_final=c1[-1],stage2_final=c2[-1],timing=fit_timing[key]))
                status["policy_fits_completed"] += 1
                active_model = active_optimizer = active_key = None
                save_status()
            for arm in ARMS:
                mark = time.perf_counter()
                diagnostics.append(dict(pair=pair,arm=arm,stage=2,
                    **endpoint_diagnostic(models[arm][0],diagnostic_merged,config.train_batch)))
                timing["diagnostic_seconds"] += time.perf_counter()-mark
            save_json(out / "curves.json", curves)
            ids = tuple(range(config.evaluation_contexts))
            theta,positions,posterior,successes,moves,generation,posterior_cost = calibration(
                config.evaluation_seeds[pair],config.evaluation_phases[0],ids)
            timing["calibration_generation_seconds"] += generation
            timing["calibration_posterior_seconds"] += posterior_cost
            pair_timing[pair]["calibration_generation_seconds"] += generation
            pair_timing[pair]["calibration_posterior_seconds"] += posterior_cost
            status["calibration_contexts"] += len(ids)
            status["calibration_moves"] += 4*len(ids)
            status["calibration_fits"] += len(ids)
            save_npz(raw / f"pair{pair}_calibration_eval.npz",ids=ids,theta=theta,
                positions=positions,posterior=posterior,successes=successes)
            save_status()
            deployment = pair_timing[pair]["deployment_costs"]
            for arm in ARMS:
                setup_mark = time.perf_counter()
                try:
                    model = Student()
                    checkpoint = torch.load(raw / f"pair{pair}_{arm}_final.pt",
                                            map_location="cpu",weights_only=False)
                    model.load_state_dict(checkpoint["model"])
                    del checkpoint
                except Exception:
                    deployment[arm] = dict(state="FAILED_SETUP",
                        attempted_setup_seconds=time.perf_counter()-setup_mark)
                    raise
                setup = time.perf_counter()-setup_mark
                mark = time.perf_counter()
                try:
                    evaluate(pair,arm,model,theta,posterior,moves)
                except Exception:
                    attempted = time.perf_counter()-mark
                    deployment[arm] = dict(state="FAILED_DEPLOYMENT",setup_seconds=setup,
                        attempted_batched_deployment_seconds=attempted,
                        attached_shared_calibration_seconds=generation,
                        attempted_conditional_total_seconds=setup+attempted+generation)
                    raise
                deployed = time.perf_counter()-mark
                deployment[arm] = dict(state="COMPLETE",setup_seconds=setup,
                    batched_deployment_seconds=deployed,
                    attached_shared_calibration_seconds=generation,
                    conditional_total_seconds=setup+deployed+generation)
                save_json(out / "episodes.json",episodes)
            reading = _read_pair(episodes,pair,config)
            per_context.extend(reading.pop("per_context"))
            pair_timing[pair].update(state="COMPLETE",wall_seconds=time.perf_counter()-pair_started,
                                     cpu_seconds=time.process_time()-pair_cpu)
            reading["timing"] = pair_timing[pair]
            pair_results.append(reading)
            save_json(raw / f"pair{pair}_result.json",reading)
            save_json(out / "per_context.json",per_context)
            status["pairs_completed"] += 1
            save_status()
        expected_updates = 6*(config.epochs[0]*ceil(2*config.initial_contexts/config.train_batch)+
                              config.epochs[1]*ceil(2*(config.initial_contexts+2*config.rollout_contexts)/config.train_batch))
        expected_rows = 6*2*config.horizon*(config.epochs[0]*config.initial_contexts+
                            config.epochs[1]*(config.initial_contexts+2*config.rollout_contexts))
        expected_eval = 2*len(ARMS)*config.evaluation_contexts*config.horizon
        expected_diagnostic = 2*len(ARMS)*2*config.horizon*(config.initial_contexts+
                                                        config.initial_contexts+2*config.rollout_contexts)
        if (status["policy_fits_started"] != 6 or status["policy_fits_completed"] != 6 or
            status["pairs_completed"] != 2 or status["optimizer_updates"] != expected_updates or
            status["processed_agent_time_rows"] != expected_rows or
            status["evaluation_team_ticks"] != expected_eval or
            status["calibration_fits"] != 2*config.evaluation_contexts or
            status["calibration_moves"] != 4*status["calibration_fits"] or
            sum(item["processed_agent_time_rows"] for item in diagnostics) != expected_diagnostic or
            status["training_collection_team_ticks"] or status["teacher_queries"] or
            status["model_branch_transitions"]):
            raise AssertionError("fixed archived-data work accounting mismatch")
        status.update(state="COMPLETE",current_pair=None)
        save_status()
        mark = time.perf_counter()
        artifacts = _artifacts(out)
        timing["artifact_hash_seconds"] += time.perf_counter()-mark
        totals = {key:[row["integer_completed_job_total_differences"][key] for row in pair_results]
                  for key in ("O-S","O-BC","S-BC")}
        reading = dict(pairs=pair_results,
            descriptive_integer_totals=totals,
            descriptive_signed_mean_totals={key:float(np.mean(value)) for key,value in totals.items()},
            descriptive_total_ranges={key:[min(value),max(value)] for key,value in totals.items()},
            scope="two exploratory starts share one exposed archive; no confirmation, equivalence or independent context replicates")
        summary = dict(state="COMPLETE",launch_sha=launch_sha,config=cfg,
            descriptive_native_reading=reading,
            counts={**status,"evaluation_optimizer_updates":0,
                "endpoint_diagnostic_agent_time_rows":expected_diagnostic,
                "expected_optimizer_updates":expected_updates,
                "expected_processed_agent_time_rows":expected_rows,
                "expected_evaluation_team_ticks":expected_eval},
            fits=fits,endpoint_diagnostics=diagnostics,weight_mappings=mappings,
            batch_costs=costs,pair_timing=pair_timing,timing=timing,
            resources=dict(wall_seconds=time.perf_counter()-started,
                cpu_seconds=time.process_time()-cpu_started,
                peak_single_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                scope="single scientific process through artifact hashing; excludes final summary write"),
            artifacts=artifacts)
        write_json(out / "summary.json",summary)
        return summary
    except Exception as error:
        status.update(state="FAILED",error_type=type(error).__name__,error=str(error))
        current = status.get("current_pair")
        if current in pair_timing:
            pair_timing[current].update(state="FAILED_PARTIAL",
                attempted_wall_seconds=time.perf_counter()-pair_started,
                attempted_cpu_seconds=time.process_time()-pair_cpu)
        partial_error = None
        if active_model is not None:
            try:
                save_checkpoint(raw / f"{active_key}_partial.pt",active_model,active_optimizer)
            except Exception as checkpoint_error:
                partial_error = f"{type(checkpoint_error).__name__}: {checkpoint_error}"
        save_status()
        save_json(out / "curves.json",curves)
        save_json(out / "episodes.json",episodes)
        save_json(out / "per_context.json",per_context)
        write_json(out / "summary.json",dict(state="FAILED",launch_sha=launch_sha,
            status=status,archived_input=input_info,expected_archive_sha256=expected_sha,
            fit_timing=fit_timing,fits=fits,
            endpoint_diagnostics=diagnostics,weight_mappings=mappings,
            completed_pair_results=pair_results,batch_costs=costs,pair_timing=pair_timing,
            timing=timing,partial_checkpoint_error=partial_error,artifacts=_artifacts(out),
            wall_seconds=time.perf_counter()-started,
            scope="incomplete technical attempt; no completed two-pair comparison"))
        raise
