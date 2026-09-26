"""Five independent paired B02 blocks; B01 policy and scientific steps are reused."""

from dataclasses import asdict, dataclass
from math import ceil, comb
from pathlib import Path
import json
import os
import platform
import resource
import time

import numpy as np
import torch

from experiments.candidates.finite_model_decision_value.b01.study import difference_reading, sha256, write_json
from experiments.candidates.planning_policy_compression.b01.model import Student
from experiments.candidates.planning_policy_compression.b01.study import (
    _artifacts, _state_hash, _sum_counts, calibration, endpoint_diagnostic,
    episode_batch, train_stage,
)

B01_SOURCE_SHA = "a576d6b6c830d712703ae069f91f74a57485e264"
ARMS = ("BC", "WBC", "P_k4_M32", "AF")
METRICS = ("completed_jobs", "service", "jobs_started", "conflicts", "wait_ticks",
           "packets", "forced_packets", "delivered", "gate_disagreement",
           "unknown_gate", "gate_opportunities")
PAIRS = (("WBC", "BC"), ("BC", "AF"), ("WBC", "AF"),
         ("BC", "P_k4_M32"), ("WBC", "P_k4_M32"), ("P_k4_M32", "AF"))


@dataclass(frozen=True)
class Config:
    block_seeds: tuple = (925951, 925952, 925953, 925954, 925955)
    block_model_seeds: tuple = (926151, 926152, 926153, 926154, 926155)
    evaluation_seeds: tuple = (925961, 925962, 925963, 925964, 925965)
    evaluation_model_seeds: tuple = (926161, 926162, 926163, 926164, 926165)
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
    if (any(len(getattr(config, name)) != 5 for name in (
            "block_seeds", "block_model_seeds", "evaluation_seeds", "evaluation_model_seeds")) or
            len(config.collect_phases) != 3 or len(config.evaluation_phases) != 3 or
            len(config.epochs) != 2 or min(config.initial_contexts, config.rollout_contexts,
            config.evaluation_contexts, config.horizon, config.batch,
            config.train_batch, *config.epochs) <= 0 or
            config.horizon % 48 or config.particles < 2 or
            config.train_batch > 2 * config.initial_contexts):
        raise ValueError("invalid five-block configuration")
    addresses = (*config.block_seeds, *config.block_model_seeds,
                 *config.evaluation_seeds, *config.evaluation_model_seeds,
                 *config.collect_phases, *config.evaluation_phases)
    if any(int(x) != x or x < 0 for x in addresses):
        raise ValueError("RNG addresses must be nonnegative integers")
    for name in ("block_seeds", "block_model_seeds", "evaluation_seeds", "evaluation_model_seeds"):
        if len(set(getattr(config, name))) != 5:
            raise ValueError(f"{name} must contain five distinct block addresses")


def exact_sign_decision(integer_total_differences):
    """Frozen n=5 upper-tail test and one-sided CP lower bound at alpha .05."""
    values = tuple(integer_total_differences)
    if len(values) != 5 or any(isinstance(x, bool) or not isinstance(x, (int, np.integer)) for x in values):
        raise ValueError("five complete integer completed-job total differences required")
    positive = sum(int(x > 0) for x in values)
    ties = sum(int(x == 0) for x in values)
    p = sum(comb(5, k) for k in range(positive, 6)) / 32
    if positive == 0:
        lower = 0.
    else:
        # P_(q=lower){Binomial(5,q) >= positive} = .05.
        left, right = 0., 1.
        for _ in range(80):
            middle = (left + right) / 2
            upper_tail = sum(comb(5, k) * middle ** k * (1-middle) ** (5-k)
                             for k in range(positive, 6))
            if upper_tail < .05:
                left = middle
            else:
                right = middle
        lower = (left + right) / 2
    return dict(unit="independent paired training and fresh 256-context evaluation block",
        estimand="q_256=Pr_(T,E){mean_256(C_WBC-C_BC)>0}",
        integer_total_differences=[int(x) for x in values],
        strictly_positive_blocks=positive, tied_blocks=ties,
        nonpositive_blocks=5-positive, exact_one_sided_p=p,
        one_sided_95_clopper_pearson_lower=lower,
        alpha=.05, confirmed=(positive == 5 and p <= .05),
        verdict="CONFIRMED_NARROW_SIGN_CLAIM" if positive == 5 and p <= .05 else "NOT_CONFIRMED",
        scope="sign recurrence only; no mean-benefit lower bound, equivalence or useful-deployment verdict")


def _read_block(rows, block, config):
    by_arm = {arm: sorted((row for row in rows if row["arm"] == arm and row["block"] == block),
                           key=lambda row: row["context"]) for arm in ARMS}
    ids = list(range(config.evaluation_contexts))
    if any([row["context"] for row in values] != ids for values in by_arm.values()):
        raise ValueError("incomplete within-block common evaluation panel")
    reference_theta = [row["theta"] for row in by_arm["AF"]]
    if any([row["theta"] for row in values] != reference_theta for values in by_arm.values()):
        raise ValueError("within-block calibration/world mismatch")
    arrays = {arm: {metric: np.asarray([row[metric] for row in values], dtype=float)
                    for metric in METRICS} for arm, values in by_arm.items()}
    contrasts = {a + "-" + b: {metric: difference_reading(arrays[a][metric] - arrays[b][metric])
                               for metric in METRICS} for a, b in PAIRS}
    integer_difference = sum(row["completed_jobs"] for row in by_arm["WBC"]) - sum(
        row["completed_jobs"] for row in by_arm["BC"])
    if not isinstance(integer_difference, int):
        raise AssertionError("completed-job sign must be based on integer totals")
    contexts = [dict(block=block, context=i, theta=float(reference_theta[i]),
                     arms={arm: {metric: float(arrays[arm][metric][i]) for metric in METRICS}
                           for arm in ARMS},
                     completed_job_differences={a+"-"+b: int(arrays[a]["completed_jobs"][i] -
                                                       arrays[b]["completed_jobs"][i]) for a, b in PAIRS})
                for i in ids]
    losses = {a+"-"+b: [dict(context=i, difference=int(arrays[a]["completed_jobs"][i]-
                                                    arrays[b]["completed_jobs"][i]))
                         for i in ids if arrays[a]["completed_jobs"][i] < arrays[b]["completed_jobs"][i]]
              for a, b in PAIRS}
    return dict(block=block, evaluation_contexts=len(ids),
        integer_wbc_minus_bc_total=integer_difference,
        signed_wbc_minus_bc_mean=integer_difference / len(ids),
        wbc_minus_bc_positive=integer_difference > 0,
        wbc_minus_bc_tie=integer_difference == 0,
        arms={arm: {metric: float(value.mean()) for metric, value in items.items()}
              for arm, items in arrays.items()},
        contrasts=contrasts, loss_worlds=losses, per_context=contexts)


def run_study(out, launch_sha, config=Config(), entry_started=None):
    """Run all five blocks to the fixed endpoint, retaining completed and partial work."""
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
    parameter_count = sum(p.numel() for p in Student().parameters())
    if parameter_count != 27329:
        raise AssertionError("frozen student parameter count changed")
    cfg = dict(**asdict(config), launch_sha=launch_sha, source_asset="planning_policy_compression/b01",
               frozen_b01_source_sha=B01_SOURCE_SHA, device="cpu", dtype="float32",
               parameter_count=parameter_count, torch=torch.__version__, numpy=np.__version__,
               host=platform.node(), nominal_receiver_probability=.75,
               threads={name: os.environ.get(name) for name in (
                   "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
    write_json(out / "config.json", cfg)
    status = dict(state="RUNNING", current_block=None, blocks_completed=0,
        policy_fits_started=0, policy_fits_completed=0, optimizer_updates=0,
        processed_agent_time_rows=0, collection_team_ticks=0, evaluation_team_ticks=0,
        executed_collection_team_ticks=0, executed_evaluation_team_ticks=0,
        calibration_contexts=0, calibration_moves=0, calibration_fits=0,
        completed_batches=0)
    write_json(out / "status.json", status)
    episodes, costs, fits, curves, diagnostics, block_results = [], [], [], [], [], []
    per_context = []
    fit_timing, block_timing, model_counts = {}, {}, {}
    timing = dict(calibration_generation_seconds=0., calibration_posterior_seconds=0.,
        optimization_seconds=0., checkpoint_io_seconds=0., checkpoint_io_cpu_seconds=0.,
        output_write_seconds=0., artifact_hash_seconds=0.,
        entry_import_and_startup_seconds=(time.perf_counter()-entry_started)
        if entry_started is not None else None)

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

    def collect(block, ids, theta, posterior, moves, seed, phase, model_seed,
                model_phase, arm, group, model=None, labels=False):
        parts = []
        for begin in range(0, len(ids), config.batch):
            batch_ids = ids[begin:begin+config.batch]
            sl = slice(begin, begin+len(batch_ids))
            stem = f"block{block}_{group}_{arm}_{begin:04d}"
            trace_path = raw / f"{stem}.npz"
            try:
                rows, data, cost = episode_batch(batch_ids, theta[sl], posterior[sl], moves[sl],
                    seed=seed, phase=phase, model_seed=model_seed, model_phase=model_phase,
                    config=config, arm=arm, model=model, labels=labels, trace_path=trace_path)
            except Exception:
                cost_path = trace_path.with_suffix(".cost.json")
                if cost_path.is_file():
                    cost = json.loads(cost_path.read_text())
                    cost["block"] = block
                    costs.append(cost)
                    _sum_counts(model_counts, cost["model"])
                    key = "executed_collection_team_ticks" if labels else "executed_evaluation_team_ticks"
                    status[key] += cost["executed_team_ticks"]
                    save_status()
                raise
            cost["block"] = block
            costs.append(cost)
            _sum_counts(model_counts, cost["model"])
            key = "executed_collection_team_ticks" if labels else "executed_evaluation_team_ticks"
            status[key] += cost["executed_team_ticks"]
            if labels:
                parts.append(data)
                status["collection_team_ticks"] += cost["team_ticks"]
            else:
                for row in rows:
                    row["block"] = block
                save_json(raw / f"{stem}.episodes.json", rows)
                episodes.extend(rows)
                status["evaluation_team_ticks"] += cost["team_ticks"]
            status["completed_batches"] += 1
            save_status()
        return {key: np.concatenate([part[key] for part in parts]) for key in parts[0]} if labels else None

    try:
        for block in range(5):
            status["current_block"] = block
            block_started, block_cpu = time.perf_counter(), time.process_time()
            block_timing[block] = dict(state="RUNNING", deployment_costs={},
                calibration_generation_seconds=0., calibration_posterior_seconds=0.)
            save_status()
            seed = config.block_seeds[block]
            model_seed = config.block_model_seeds[block]
            eval_seed = config.evaluation_seeds[block]
            eval_model_seed = config.evaluation_model_seeds[block]
            ids = tuple(range(config.initial_contexts + 2 * config.rollout_contexts))
            theta, positions, posterior, successes, moves, generation, posterior_cost = calibration(
                seed, config.collect_phases[0], ids)
            timing["calibration_generation_seconds"] += generation
            timing["calibration_posterior_seconds"] += posterior_cost
            block_timing[block]["calibration_generation_seconds"] += generation
            block_timing[block]["calibration_posterior_seconds"] += posterior_cost
            status["calibration_contexts"] += len(ids)
            status["calibration_moves"] += 4 * len(ids)
            status["calibration_fits"] += len(ids)
            save_npz(raw / f"block{block}_calibration_train.npz", ids=ids, theta=theta,
                     positions=positions, posterior=posterior, successes=successes)
            save_status()
            first_ids = ids[:config.initial_contexts]
            first = collect(block, first_ids, theta[:len(first_ids)], posterior[:len(first_ids)],
                moves[:len(first_ids)], seed, config.collect_phases[1], model_seed,
                config.collect_phases[2], "TEACHER", "initial", labels=True)
            torch.manual_seed(seed)
            initial_model = Student()
            initial = {key: value.detach().clone() for key, value in initial_model.state_dict().items()}
            initial_hash = _state_hash(initial)
            models = {}
            for arm in ("BC", "WBC"):
                key = f"block{block}_{arm}"
                status["policy_fits_started"] += 1
                save_status()
                mark, cpu_mark = time.perf_counter(), time.process_time()
                model = Student()
                model.load_state_dict(initial)
                if _state_hash(model.state_dict()) != initial_hash:
                    raise AssertionError("paired initial state differs")
                optimizer = torch.optim.Adam(model.parameters(), lr=.001)
                fit_timing[key] = dict(initialization_wall_seconds=time.perf_counter()-mark,
                    initialization_cpu_seconds=time.process_time()-cpu_mark)
                wall, cpu = save_checkpoint(raw / f"{key}_initial.pt", model, optimizer)
                fit_timing[key].update(checkpoint_io_seconds=wall, checkpoint_io_cpu_seconds=cpu)
                save_status()
                mark, cpu_mark = time.perf_counter(), time.process_time()
                try:
                    c1, u1, r1, w1 = train_stage(model, optimizer, first,
                        weighted=arm == "WBC", model_seed=model_seed, block=block,
                        stage=1, epochs=config.epochs[0], batch=config.train_batch,
                        initial=initial, status_callback=lambda n: status.update(
                            optimizer_updates=status["optimizer_updates"]+1,
                            processed_agent_time_rows=status["processed_agent_time_rows"]+n))
                finally:
                    elapsed = time.perf_counter()-mark
                    timing["optimization_seconds"] += elapsed
                    fit_timing[key]["stage1_optimization_wall_seconds"] = elapsed
                    fit_timing[key]["stage1_optimization_cpu_seconds"] = time.process_time()-cpu_mark
                curves.extend(dict(block=block, arm=arm, **row) for row in c1)
                wall, cpu = save_checkpoint(raw / f"{key}_stage1.pt", model, optimizer)
                fit_timing[key]["checkpoint_io_seconds"] += wall
                fit_timing[key]["checkpoint_io_cpu_seconds"] += cpu
                models[arm] = (model, optimizer, c1, u1, r1, w1)
                save_status()
            for arm in ("BC", "WBC"):
                diagnostics.append(dict(block=block, arm=arm, stage=1,
                    **endpoint_diagnostic(models[arm][0], first, config.train_batch)))
            parts = [first]
            for arm, offset in (("BC", config.initial_contexts),
                                ("WBC", config.initial_contexts+config.rollout_contexts)):
                selected = ids[offset:offset+config.rollout_contexts]
                parts.append(collect(block, selected, theta[offset:offset+len(selected)],
                    posterior[offset:offset+len(selected)], moves[offset:offset+len(selected)],
                    seed, config.collect_phases[1], model_seed, config.collect_phases[2],
                    f"{arm}_ROLLIN", "rollin", model=models[arm][0], labels=True))
            merged = {name: np.concatenate([part[name] for part in parts]) for name in first}
            save_npz(raw / f"block{block}_training.npz", **merged)
            for arm in ("BC", "WBC"):
                key = f"block{block}_{arm}"
                model, optimizer, c1, u1, r1, w1 = models[arm]
                mark, cpu_mark = time.perf_counter(), time.process_time()
                try:
                    c2, u2, r2, w2 = train_stage(model, optimizer, merged,
                        weighted=arm == "WBC", model_seed=model_seed, block=block,
                        stage=2, epochs=config.epochs[1], batch=config.train_batch,
                        initial=initial, status_callback=lambda n: status.update(
                            optimizer_updates=status["optimizer_updates"]+1,
                            processed_agent_time_rows=status["processed_agent_time_rows"]+n))
                finally:
                    elapsed = time.perf_counter()-mark
                    timing["optimization_seconds"] += elapsed
                    fit_timing[key]["stage2_optimization_wall_seconds"] = elapsed
                    fit_timing[key]["stage2_optimization_cpu_seconds"] = time.process_time()-cpu_mark
                curves.extend(dict(block=block, arm=arm, **row) for row in c2)
                wall, cpu = save_checkpoint(raw / f"{key}_final.pt", model, optimizer)
                fit_timing[key]["checkpoint_io_seconds"] += wall
                fit_timing[key]["checkpoint_io_cpu_seconds"] += cpu
                fit_timing[key]["fit_wall_seconds"] = sum(fit_timing[key][part] for part in (
                    "initialization_wall_seconds", "stage1_optimization_wall_seconds",
                    "stage2_optimization_wall_seconds", "checkpoint_io_seconds"))
                fit_timing[key]["fit_cpu_seconds"] = sum(fit_timing[key][part] for part in (
                    "initialization_cpu_seconds", "stage1_optimization_cpu_seconds",
                    "stage2_optimization_cpu_seconds", "checkpoint_io_cpu_seconds"))
                fit_timing[key]["fit_scope"] = "initialization, optimizer stages, checkpoints; shared collection excluded"
                fits.append(dict(block=block, arm=arm, updates=u1+u2,
                    processed_agent_time_rows=r1+r2, parameter_movement_l2=float(np.sqrt(sum(
                        torch.sum((value.detach()-initial[name])**2).item()
                        for name, value in model.state_dict().items()))),
                    initial_state_sha256=initial_hash,
                    initial_checkpoint_sha256=sha256(raw / f"{key}_initial.pt"),
                    stage1_checkpoint_sha256=sha256(raw / f"{key}_stage1.pt"),
                    final_checkpoint_sha256=sha256(raw / f"{key}_final.pt"),
                    stage1_weights=w1, stage2_weights=w2,
                    stage1_final=c1[-1], stage2_final=c2[-1], timing=fit_timing[key]))
                status["policy_fits_completed"] += 1
                save_status()
            for arm in ("BC", "WBC"):
                diagnostics.append(dict(block=block, arm=arm, stage=2,
                    **endpoint_diagnostic(models[arm][0], merged, config.train_batch)))
            save_json(out / "curves.json", curves)
            eval_ids = tuple(range(config.evaluation_contexts))
            ev_theta, ev_positions, ev_q, ev_successes, ev_moves, ev_generation, ev_posterior = calibration(
                eval_seed, config.evaluation_phases[0], eval_ids)
            timing["calibration_generation_seconds"] += ev_generation
            timing["calibration_posterior_seconds"] += ev_posterior
            block_timing[block]["calibration_generation_seconds"] += ev_generation
            block_timing[block]["calibration_posterior_seconds"] += ev_posterior
            status["calibration_contexts"] += len(eval_ids)
            status["calibration_moves"] += 4 * len(eval_ids)
            status["calibration_fits"] += len(eval_ids)
            save_npz(raw / f"block{block}_calibration_eval.npz", ids=eval_ids, theta=ev_theta,
                     positions=ev_positions, posterior=ev_q, successes=ev_successes)
            save_status()
            deployment = block_timing[block]["deployment_costs"]
            for arm in ARMS:
                setup_mark = time.perf_counter()
                student = None
                try:
                    if arm in models:
                        student = Student()
                        checkpoint = torch.load(raw / f"block{block}_{arm}_final.pt",
                                                map_location="cpu", weights_only=False)
                        student.load_state_dict(checkpoint["model"])
                        del checkpoint
                except Exception:
                    deployment[arm] = dict(state="FAILED_SETUP",
                        attempted_setup_seconds=time.perf_counter()-setup_mark)
                    raise
                setup = time.perf_counter()-setup_mark
                required_calibration = 0. if arm == "AF" else ev_generation
                if arm == "P_k4_M32":
                    required_calibration += ev_posterior
                mark = time.perf_counter()
                try:
                    collect(block, eval_ids, ev_theta, ev_q, ev_moves, eval_seed,
                        config.evaluation_phases[1], eval_model_seed,
                        config.evaluation_phases[2], arm, "evaluation", model=student)
                except Exception:
                    attempted = time.perf_counter()-mark
                    deployment[arm] = dict(state="FAILED_DEPLOYMENT", setup_seconds=setup,
                        attempted_batched_deployment_seconds=attempted,
                        attached_shared_calibration_seconds=required_calibration,
                        attempted_conditional_total_seconds=setup+attempted+required_calibration)
                    raise
                deployed = time.perf_counter()-mark
                deployment[arm] = dict(state="COMPLETE", setup_seconds=setup,
                    batched_deployment_seconds=deployed,
                    attached_shared_calibration_seconds=required_calibration,
                    conditional_total_seconds=setup+deployed+required_calibration)
                save_json(out / "episodes.json", episodes)
            reading = _read_block(episodes, block, config)
            per_context.extend(reading.pop("per_context"))
            block_timing[block].update(state="COMPLETE",
                wall_seconds=time.perf_counter()-block_started,
                cpu_seconds=time.process_time()-block_cpu)
            reading["timing"] = block_timing[block]
            block_results.append(reading)
            save_json(raw / f"block{block}_result.json", reading)
            save_json(out / "per_context.json", per_context)
            status["blocks_completed"] += 1
            save_status()
        expected_collection = 5 * (config.initial_contexts+2*config.rollout_contexts) * config.horizon
        expected_evaluation = 5 * len(ARMS) * config.evaluation_contexts * config.horizon
        expected_updates = 10 * (config.epochs[0] * ceil(2*config.initial_contexts/config.train_batch) +
                                 config.epochs[1] * ceil(2*(config.initial_contexts+2*config.rollout_contexts)/config.train_batch))
        expected_rows = 10 * 2 * config.horizon * (config.epochs[0]*config.initial_contexts +
                                                   config.epochs[1]*(config.initial_contexts+2*config.rollout_contexts))
        branch_upper = (expected_collection+5*config.evaluation_contexts*config.horizon) * config.particles * 2 * 32
        if (status["policy_fits_started"] != 10 or status["policy_fits_completed"] != 10 or
            status["blocks_completed"] != 5 or status["collection_team_ticks"] != expected_collection or
            status["evaluation_team_ticks"] != expected_evaluation or
            status["optimizer_updates"] != expected_updates or
            status["processed_agent_time_rows"] != expected_rows or
            status["calibration_fits"] != 5*(config.initial_contexts+2*config.rollout_contexts+
                                              config.evaluation_contexts) or
            status["calibration_moves"] != 4*status["calibration_fits"]):
            raise AssertionError("fixed five-block work accounting mismatch")
        if model_counts.get("model_branch_transitions", 0) > branch_upper:
            raise AssertionError("model branches exceed conservative fixed bound")
        if len(diagnostics) != 20:
            raise AssertionError("two endpoints per fit required")
        formal = exact_sign_decision([row["integer_wbc_minus_bc_total"] for row in block_results])
        status["state"] = "COMPLETE"
        status["current_block"] = None
        save_status()
        mark = time.perf_counter()
        artifacts = _artifacts(out)
        timing["artifact_hash_seconds"] += time.perf_counter()-mark
        model_counts["model_root_particles"] = model_counts.get("model_initialization_worlds", 0)//2
        root_counts = {name: sum(cost.get(name, 0) for cost in costs) for name in (
            "optional_roots", "exact_zero_roots", "zero_af_send_fallbacks", "nonzero_roots")}
        descriptive = dict(blocks=block_results,
            signed_mean_of_five_block_job_totals=float(np.mean(formal["integer_total_differences"])),
            range_of_five_block_job_totals=[min(formal["integer_total_differences"]),
                                            max(formal["integer_total_differences"])],
            signed_mean_of_five_block_context_means=float(np.mean(
                [row["signed_wbc_minus_bc_mean"] for row in block_results])),
            scope="descriptive complete native utility and costs; no second formal claim or automatic deployment decision")
        summary = dict(state="COMPLETE", launch_sha=launch_sha, config=cfg,
            formal_confirmation=formal, descriptive_full_utility=descriptive,
            counts={**status, **model_counts, **root_counts,
                "evaluation_optimizer_updates":0,
                "model_branch_transition_upper":branch_upper,
                "endpoint_diagnostic_agent_time_rows":sum(
                    item["processed_agent_time_rows"] for item in diagnostics),
                "expected_collection_team_ticks":expected_collection,
                "expected_evaluation_team_ticks":expected_evaluation,
                "expected_optimizer_updates":expected_updates,
                "expected_processed_agent_time_rows":expected_rows},
            fits=fits, endpoint_diagnostics=diagnostics, batch_costs=costs,
            timing=timing, block_timing=block_timing,
            resources=dict(wall_seconds=time.perf_counter()-started,
                cpu_seconds=time.process_time()-cpu_started,
                peak_single_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                scope="single scientific process through hashing; excludes final summary write"),
            artifacts=artifacts,
            inference_scope="five independent complete paired blocks; formal sign verdict separate from descriptive utility")
        write_json(out / "summary.json", summary)
        return summary
    except Exception as error:
        status.update(state="FAILED", error_type=type(error).__name__, error=str(error))
        current = status.get("current_block")
        if current in block_timing:
            block_timing[current].update(state="FAILED_PARTIAL",
                attempted_wall_seconds=time.perf_counter()-block_started,
                attempted_cpu_seconds=time.process_time()-block_cpu)
        save_status()
        save_json(out / "curves.json", curves)
        save_json(out / "episodes.json", episodes)
        save_json(out / "per_context.json", per_context)
        write_json(out / "summary.json", dict(state="FAILED", launch_sha=launch_sha,
            status=status, fits=fits, fit_timing=fit_timing,
            endpoint_diagnostics=diagnostics, completed_block_results=block_results,
            batch_costs=costs, timing=timing, block_timing=block_timing,
            artifacts=_artifacts(out),
            wall_seconds=time.perf_counter()-started,
            scope="incomplete technical attempt; no formal confirmation decision"))
        raise
