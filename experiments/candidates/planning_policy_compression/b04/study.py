"""B04: two standalone O/BC acquisitions with a shared teacher prefix."""

from dataclasses import asdict, dataclass
from math import ceil
from pathlib import Path
import json
import os
import platform
import resource
import time

import numpy as np
import torch

from experiments.candidates.finite_model_decision_value.b01.study import (
    difference_reading, sha256, write_json,
)
from experiments.candidates.planning_policy_compression.b01.model import Student
from experiments.candidates.planning_policy_compression.b01.study import (
    _artifacts, _merge, _movement, _state_hash, _sum_counts, calibration,
    endpoint_diagnostic, episode_batch, train_stage,
)

ARMS = ("O", "BC", "P_k4_M32", "AF")
PAIRS = (("O", "BC"), ("O", "AF"), ("BC", "AF"), ("O", "P_k4_M32"),
         ("BC", "P_k4_M32"), ("P_k4_M32", "AF"))
METRICS = ("completed_jobs", "service", "jobs_started", "conflicts", "wait_ticks",
           "packets", "forced_packets", "delivered", "gate_disagreement",
           "unknown_gate", "gate_opportunities")


@dataclass(frozen=True)
class Config:
    initial_seeds: tuple = (926501, 926502)
    order_seeds: tuple = (926601, 926602)
    collection_seeds: tuple = (926701, 926702)
    collection_model_seeds: tuple = (926801, 926802)
    evaluation_seeds: tuple = (926901, 926902)
    evaluation_model_seeds: tuple = (927001, 927002)
    prefix_phases: tuple = (100, 101, 102)
    rollin_phases: tuple = (110, 111, 112)
    evaluation_phases: tuple = (120, 121, 122)
    prefix_contexts: int = 256
    rollin_contexts: int = 256
    evaluation_contexts: int = 256
    horizon: int = 96
    batch: int = 16
    train_batch: int = 64
    epochs: tuple = (40, 40)
    particles: int = 32


def _validate(config):
    seed_names = ("initial_seeds", "order_seeds", "collection_seeds",
                  "collection_model_seeds", "evaluation_seeds", "evaluation_model_seeds")
    if (any(len(getattr(config, name)) != 2 for name in seed_names) or
            any(len(getattr(config, name)) != 3 for name in
                ("prefix_phases", "rollin_phases", "evaluation_phases")) or
            len(config.epochs) != 2 or
            min(config.prefix_contexts, config.rollin_contexts, config.evaluation_contexts,
                config.horizon, config.batch, config.train_batch, *config.epochs) <= 0 or
            config.horizon % 48 or config.particles < 2 or
            config.train_batch > 2 * config.prefix_contexts):
        raise ValueError("invalid B04 two-block configuration")
    addresses = [v for name in seed_names for v in getattr(config, name)]
    addresses += [v for name in ("prefix_phases", "rollin_phases", "evaluation_phases")
                  for v in getattr(config, name)]
    if any(int(v) != v or v < 0 for v in addresses) or len(set(addresses[:12])) != 12:
        raise ValueError("invalid or reused B04 RNG addresses")


def _read_block(episodes, block, config):
    by_arm = {arm: sorted((row for row in episodes if row["block"] == block and
                            row["arm"] == arm), key=lambda row: row["context"])
              for arm in ARMS}
    ids = list(range(config.evaluation_contexts))
    if any([row["context"] for row in rows] != ids for rows in by_arm.values()):
        raise ValueError("incomplete common B04 evaluation panel")
    theta = [row["theta"] for row in by_arm["AF"]]
    if any([row["theta"] for row in rows] != theta for rows in by_arm.values()):
        raise ValueError("B04 evaluation calibrations differ")
    arrays = {arm: {metric: np.asarray([row[metric] for row in rows], dtype=float)
                    for metric in METRICS} for arm, rows in by_arm.items()}
    contrasts = {a+"-"+b: {metric: difference_reading(arrays[a][metric]-arrays[b][metric])
                           for metric in METRICS} for a, b in PAIRS}
    totals = {a+"-"+b: int(sum(row["completed_jobs"] for row in by_arm[a]) -
                             sum(row["completed_jobs"] for row in by_arm[b])) for a,b in PAIRS}
    if totals["O-AF"] != totals["O-BC"] + totals["BC-AF"]:
        raise AssertionError("completed-job contrast identity failed")
    contexts = [dict(block=block, context=i, theta=float(theta[i]),
        arms={arm:{metric:float(arrays[arm][metric][i]) for metric in METRICS}
              for arm in ARMS},
        completed_job_differences={a+"-"+b:int(arrays[a]["completed_jobs"][i]-
                                          arrays[b]["completed_jobs"][i]) for a,b in PAIRS})
        for i in ids]
    losses = {a+"-"+b:[dict(context=i, difference=row["completed_job_differences"][a+"-"+b])
                      for i,row in enumerate(contexts)
                      if row["completed_job_differences"][a+"-"+b] < 0] for a,b in PAIRS}
    return dict(block=block, evaluation_contexts=len(ids),
        integer_completed_job_total_differences=totals,
        signed_completed_job_mean_differences={key:value/len(ids) for key,value in totals.items()},
        arms={arm:{metric:float(value.mean()) for metric,value in metrics.items()}
              for arm,metrics in arrays.items()},
        contrasts=contrasts, loss_worlds=losses, per_context=contexts)


def _sum_batch_costs(costs):
    model, filtr = {}, {}
    for cost in costs:
        _sum_counts(model,cost["model"])
        _sum_counts(filtr,cost["filter"])
    return dict(wall_seconds=sum(c["wall_seconds"] for c in costs),
        cpu_seconds=sum(c["cpu_seconds"] for c in costs),
        team_ticks=sum(c["team_ticks"] for c in costs),
        executed_team_ticks=sum(c["executed_team_ticks"] for c in costs),
        optional_roots=sum(c["optional_roots"] for c in costs),
        exact_zero_roots=sum(c["exact_zero_roots"] for c in costs),
        zero_af_send_fallbacks=sum(c["zero_af_send_fallbacks"] for c in costs),
        model=model,filter=filtr,
        model_branch_transitions=model.get("model_branch_transitions",0))


def run_study(out, launch_sha, config=Config(), entry_started=None):
    """Run a fixed complete study or retain every observed partial batch and fit."""
    _validate(config)
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if any((out/name).exists() for name in
           ("config.json","status.json","summary.json","episodes.json","curves.json",
            "per_context.json","raw")):
        raise FileExistsError("B04 scientific output already exists; no retry")
    raw = out/"raw"
    raw.mkdir()
    started, cpu_started = time.perf_counter(), time.process_time()
    parameter_count = sum(p.numel() for p in Student().parameters())
    if parameter_count != 27329:
        raise AssertionError("frozen Student parameter count changed")
    cfg = dict(**asdict(config), launch_sha=launch_sha, parameter_count=parameter_count,
        device="cpu", dtype="float32", torch=torch.__version__, numpy=np.__version__,
        host=platform.node(), threads={name:os.environ.get(name) for name in
              ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")})
    write_json(out/"config.json",cfg)
    status = dict(state="RUNNING",current_block=None,blocks_completed=0,
        policy_fits_started=0,policy_fits_completed=0,optimizer_updates=0,
        processed_agent_time_rows=0,collection_team_ticks=0,evaluation_team_ticks=0,
        executed_collection_team_ticks=0,executed_evaluation_team_ticks=0,
        calibration_contexts=0,calibration_moves=0,calibration_fits=0,completed_batches=0)
    write_json(out/"status.json",status)
    timing = dict(calibration_generation_seconds=0.,calibration_posterior_seconds=0.,
        optimization_seconds=0.,diagnostic_seconds=0.,checkpoint_io_seconds=0.,
        checkpoint_io_cpu_seconds=0.,output_write_seconds=0.,artifact_hash_seconds=0.,
        entry_import_and_startup_seconds=(time.perf_counter()-entry_started)
            if entry_started is not None else None)
    costs, episodes, curves, fits, diagnostics, block_results, provenance = [],[],[],[],[],[],[]
    per_context = []
    fit_timing, block_timing, model_counts, method_costs = {},{},{},{}
    active_model=active_optimizer=active_key=None

    def save_json(path,value):
        mark=time.perf_counter()
        write_json(path,value)
        timing["output_write_seconds"]+=time.perf_counter()-mark

    def save_npz(path,**data):
        mark=time.perf_counter()
        np.savez_compressed(path,**data)
        timing["output_write_seconds"]+=time.perf_counter()-mark
        return dict(path=str(path.relative_to(out)),sha256=sha256(path),
                    bytes=path.stat().st_size)

    def save_status():
        save_json(out/"status.json",status)

    def save_checkpoint(path,model,optimizer):
        mark,cpu_mark=time.perf_counter(),time.process_time()
        torch.save(dict(model=model.state_dict(),optimizer=optimizer.state_dict()),path)
        wall,cpu=time.perf_counter()-mark,time.process_time()-cpu_mark
        timing["checkpoint_io_seconds"]+=wall
        timing["checkpoint_io_cpu_seconds"]+=cpu
        return wall,cpu

    def collect(block,group,arm,ids,theta,posterior,moves,world_seed,phases,
                model=None,labels=False):
        parts=[]
        for begin in range(0,len(ids),config.batch):
            batch_ids=ids[begin:begin+config.batch]
            sl=slice(begin,begin+len(batch_ids))
            stem=f"block{block}_{group}_{arm}_{begin:04d}"
            trace_path=raw/f"{stem}.npz"
            try:
                rows,data,cost=episode_batch(batch_ids,theta[sl],posterior[sl],moves[sl],
                    seed=world_seed,phase=phases[1],
                    model_seed=(config.collection_model_seeds[block] if labels
                                else config.evaluation_model_seeds[block]),
                    model_phase=phases[2],config=config,arm=arm,model=model,
                    labels=labels,trace_path=trace_path)
            except Exception:
                cost_path=trace_path.with_suffix(".cost.json")
                if cost_path.is_file():
                    cost=json.loads(cost_path.read_text())
                    cost.update(block=block,group=group)
                    costs.append(cost)
                    _sum_counts(model_counts,cost["model"])
                    status["executed_collection_team_ticks" if labels else
                           "executed_evaluation_team_ticks"]+=cost["executed_team_ticks"]
                    save_status()
                raise
            cost.update(block=block,group=group)
            costs.append(cost)
            _sum_counts(model_counts,cost["model"])
            status["executed_collection_team_ticks" if labels else
                   "executed_evaluation_team_ticks"]+=cost["executed_team_ticks"]
            if labels:
                parts.append(data)
                status["collection_team_ticks"]+=cost["team_ticks"]
            else:
                if arm in ("O","BC") and (cost["model"] or cost["filter"] or
                                          cost["optional_roots"]):
                    raise AssertionError("student deployment performed teacher/filter work")
                for row in rows:
                    row["block"]=block
                save_json(raw/f"{stem}.episodes.json",rows)
                episodes.extend(rows)
                status["evaluation_team_ticks"]+=cost["team_ticks"]
            status["completed_batches"]+=1
            save_status()
        return _merge(parts) if labels else None

    def calibrated(block,group,seed,phases,ids):
        theta,positions,posterior,successes,moves,generation,posterior_cost=calibration(
            seed,phases[0],ids)
        timing["calibration_generation_seconds"]+=generation
        timing["calibration_posterior_seconds"]+=posterior_cost
        block_timing[block]["calibration_generation_seconds"]+=generation
        block_timing[block]["calibration_posterior_seconds"]+=posterior_cost
        status["calibration_contexts"]+=len(ids)
        status["calibration_moves"]+=4*len(ids)
        status["calibration_fits"]+=len(ids)
        identity=save_npz(raw/f"block{block}_calibration_{group}.npz",
            ids=ids,theta=theta,positions=positions,posterior=posterior,successes=successes)
        save_status()
        return theta,posterior,moves,dict(**identity,seed=seed,phase=phases[0],
            contexts=list(ids),moves=4*len(ids),posterior_fits=len(ids),
            generation_seconds=generation,posterior_seconds=posterior_cost)

    try:
        for block in range(2):
            status["current_block"]=block
            block_started,block_cpu=time.perf_counter(),time.process_time()
            block_timing[block]=dict(state="RUNNING",deployment_costs={},
                calibration_generation_seconds=0.,calibration_posterior_seconds=0.)
            save_status()
            world_seed=config.collection_seeds[block]
            prefix_ids=tuple(range(config.prefix_contexts))
            roll_ids=tuple(range(config.prefix_contexts,
                                 config.prefix_contexts+config.rollin_contexts))
            theta,q,moves,prefix_cal=calibrated(block,"prefix",world_seed,
                                                 config.prefix_phases,prefix_ids)
            cost_start=len(costs)
            prefix=collect(block,"prefix","TEACHER",prefix_ids,theta,q,moves,
                           world_seed,config.prefix_phases,labels=True)
            prefix_costs=costs[cost_start:]
            prefix_file=save_npz(raw/f"block{block}_prefix.npz",**prefix)
            provenance.append(dict(block=block,group="shared_teacher_prefix",owner="both",
                contexts=list(prefix_ids),world_seed=world_seed,
                world_phase=config.prefix_phases[1],model_seed=config.collection_model_seeds[block],
                model_phase=config.prefix_phases[2],calibration=prefix_cal,
                dataset=prefix_file,acquisition=_sum_batch_costs(prefix_costs)))
            torch.manual_seed(config.initial_seeds[block])
            initial_model=Student()
            initial={name:value.detach().clone() for name,value in initial_model.state_dict().items()}
            initial_hash=_state_hash(initial)
            models={}
            for arm in ("O","BC"):
                key=f"block{block}_{arm}"
                status["policy_fits_started"]+=1
                save_status()
                mark,cpu_mark=time.perf_counter(),time.process_time()
                model=Student()
                model.load_state_dict(initial)
                if _state_hash(model.state_dict())!=initial_hash:
                    raise AssertionError("paired initial tensors differ")
                optimizer=torch.optim.Adam(model.parameters(),lr=.001)
                fit_timing[key]=dict(initialization_wall_seconds=time.perf_counter()-mark,
                    initialization_cpu_seconds=time.process_time()-cpu_mark,
                    checkpoint_io_seconds=0.,checkpoint_io_cpu_seconds=0.)
                wall,cpu=save_checkpoint(raw/f"{key}_initial.pt",model,optimizer)
                fit_timing[key]["checkpoint_io_seconds"]+=wall
                fit_timing[key]["checkpoint_io_cpu_seconds"]+=cpu
                models[arm]=(model,optimizer)
                active_model,active_optimizer,active_key=model,optimizer,key
                mark,cpu_mark=time.perf_counter(),time.process_time()
                try:
                    c1,u1,r1,w1=train_stage(model,optimizer,prefix,weighted=arm=="O",
                        model_seed=config.order_seeds[block],block=block,stage=1,
                        epochs=config.epochs[0],batch=config.train_batch,initial=initial,
                        status_callback=lambda n:status.update(
                            optimizer_updates=status["optimizer_updates"]+1,
                            processed_agent_time_rows=status["processed_agent_time_rows"]+n))
                finally:
                    elapsed=time.perf_counter()-mark
                    timing["optimization_seconds"]+=elapsed
                    fit_timing[key]["stage1_optimization_wall_seconds"]=elapsed
                    fit_timing[key]["stage1_optimization_cpu_seconds"]=time.process_time()-cpu_mark
                curves.extend(dict(block=block,arm=arm,**row) for row in c1)
                wall,cpu=save_checkpoint(raw/f"{key}_stage1.pt",model,optimizer)
                fit_timing[key]["checkpoint_io_seconds"]+=wall
                fit_timing[key]["checkpoint_io_cpu_seconds"]+=cpu
                models[arm]=(model,optimizer,c1,u1,r1,w1)
                active_model=active_optimizer=active_key=None
                save_status()
            for arm in ("O","BC"):
                mark=time.perf_counter()
                diagnostics.append(dict(block=block,arm=arm,stage=1,
                    data_scope="common_teacher_prefix",
                    **endpoint_diagnostic(models[arm][0],prefix,config.train_batch)))
                timing["diagnostic_seconds"]+=time.perf_counter()-mark
            roll_theta,roll_q,roll_moves,roll_cal=calibrated(block,"shared_rollin",
                world_seed,config.rollin_phases,roll_ids)
            merged={}
            roll_costs={}
            for arm in ("O","BC"):
                cost_start=len(costs)
                roll=collect(block,"rollin",f"{arm}_ROLLIN",roll_ids,
                    roll_theta,roll_q,roll_moves,world_seed,config.rollin_phases,
                    model=models[arm][0],labels=True)
                roll_costs[arm]=costs[cost_start:]
                roll_file=save_npz(raw/f"block{block}_{arm}_rollin.npz",**roll)
                merged[arm]=_merge([prefix,roll])
                merged_file=save_npz(raw/f"block{block}_{arm}_training.npz",**merged[arm])
                if (not np.array_equal(merged[arm]["context"],
                    np.repeat(np.asarray((*prefix_ids,*roll_ids)),2)) or
                    not np.array_equal(merged[arm]["x"][:len(prefix["x"])],prefix["x"])):
                    raise AssertionError("own training data provenance invalid")
                provenance.append(dict(block=block,group=f"{arm}_own_rollin",owner=arm,
                    contexts=list(roll_ids),world_seed=world_seed,
                    world_phase=config.rollin_phases[1],model_seed=config.collection_model_seeds[block],
                    model_phase=config.rollin_phases[2],calibration=roll_cal,
                    dataset=roll_file,merged_dataset=merged_file,
                    merged_components=[prefix_file["sha256"],roll_file["sha256"]],
                    acquisition=_sum_batch_costs(roll_costs[arm])))
                required_batches=(prefix_costs,roll_costs[arm])
                required_calibration=(prefix_cal,roll_cal)
                method_costs[(block,arm)]=dict(block=block,arm=arm,
                    state="ACQUIRED",prefix_charged_in_full=True,
                    acquisition_measurement_scope=(
                        "Full required prefix and own-roll-in batch wall through trace writes, "
                        "plus both calibrations; excludes dataset merge/NPZ/hash, status/cost "
                        "metadata writes and other orchestration. Physical run wall includes overhead."),
                    required_acquisition_team_ticks=sum(
                        c["team_ticks"] for group in required_batches for c in group),
                    required_acquisition_optional_roots=sum(
                        c["optional_roots"] for group in required_batches for c in group),
                    required_acquisition_model_branch_transitions=sum(
                        c["model"].get("model_branch_transitions",0)
                        for group in required_batches for c in group),
                    required_acquisition_wall_seconds=sum(
                        c["wall_seconds"] for group in required_batches for c in group)+
                        sum(c["generation_seconds"]+c["posterior_seconds"]
                            for c in required_calibration),
                    batched_acquisition_cpu_seconds=sum(
                        c["cpu_seconds"] for group in required_batches for c in group),
                    required_calibration_contexts=sum(len(c["contexts"])
                                                      for c in required_calibration),
                    prefix_batch_costs=_sum_batch_costs(prefix_costs),
                    own_rollin_batch_costs=_sum_batch_costs(roll_costs[arm]),
                    prefix_calibration=prefix_cal,own_rollin_calibration=roll_cal)
            for arm in ("O","BC"):
                key=f"block{block}_{arm}"
                model,optimizer,c1,u1,r1,w1=models[arm]
                active_model,active_optimizer,active_key=model,optimizer,key
                mark,cpu_mark=time.perf_counter(),time.process_time()
                try:
                    c2,u2,r2,w2=train_stage(model,optimizer,merged[arm],weighted=arm=="O",
                        model_seed=config.order_seeds[block],block=block,stage=2,
                        epochs=config.epochs[1],batch=config.train_batch,initial=initial,
                        status_callback=lambda n:status.update(
                            optimizer_updates=status["optimizer_updates"]+1,
                            processed_agent_time_rows=status["processed_agent_time_rows"]+n))
                finally:
                    elapsed=time.perf_counter()-mark
                    timing["optimization_seconds"]+=elapsed
                    fit_timing[key]["stage2_optimization_wall_seconds"]=elapsed
                    fit_timing[key]["stage2_optimization_cpu_seconds"]=time.process_time()-cpu_mark
                curves.extend(dict(block=block,arm=arm,**row) for row in c2)
                wall,cpu=save_checkpoint(raw/f"{key}_final.pt",model,optimizer)
                fit_timing[key]["checkpoint_io_seconds"]+=wall
                fit_timing[key]["checkpoint_io_cpu_seconds"]+=cpu
                fit_timing[key]["fit_wall_seconds"]=sum(fit_timing[key][part] for part in
                    ("initialization_wall_seconds","stage1_optimization_wall_seconds",
                     "stage2_optimization_wall_seconds","checkpoint_io_seconds"))
                fit_timing[key]["fit_cpu_seconds"]=sum(fit_timing[key][part] for part in
                    ("initialization_cpu_seconds","stage1_optimization_cpu_seconds",
                     "stage2_optimization_cpu_seconds","checkpoint_io_cpu_seconds"))
                fits.append(dict(block=block,arm=arm,updates=u1+u2,
                    processed_agent_time_rows=r1+r2,parameter_movement_l2=_movement(model,initial),
                    initial_state_sha256=initial_hash,
                    initial_checkpoint_sha256=sha256(raw/f"{key}_initial.pt"),
                    stage1_checkpoint_sha256=sha256(raw/f"{key}_stage1.pt"),
                    final_checkpoint_sha256=sha256(raw/f"{key}_final.pt"),
                    stage1_weights=w1,stage2_weights=w2,stage1_final=c1[-1],
                    stage2_final=c2[-1],timing=fit_timing[key]))
                method_costs[(block,arm)].update(state="FITTED",fit=fit_timing[key])
                status["policy_fits_completed"]+=1
                active_model=active_optimizer=active_key=None
                save_status()
            for arm in ("O","BC"):
                mark=time.perf_counter()
                diagnostics.append(dict(block=block,arm=arm,stage=2,
                    data_scope=f"{arm}_own_prefix_plus_rollin_descriptive",
                    **endpoint_diagnostic(models[arm][0],merged[arm],config.train_batch)))
                timing["diagnostic_seconds"]+=time.perf_counter()-mark
            save_json(out/"curves.json",curves)
            eval_ids=tuple(range(config.evaluation_contexts))
            ev_theta,ev_q,ev_moves,ev_cal=calibrated(block,"evaluation",
                config.evaluation_seeds[block],config.evaluation_phases,eval_ids)
            deployment=block_timing[block]["deployment_costs"]
            for arm in ARMS:
                setup_mark=time.perf_counter()
                student=None
                try:
                    if arm in ("O","BC"):
                        student=Student()
                        checkpoint=torch.load(raw/f"block{block}_{arm}_final.pt",
                                              map_location="cpu",weights_only=False)
                        student.load_state_dict(checkpoint["model"])
                except Exception:
                    deployment[arm]=dict(state="FAILED_SETUP",
                        attempted_setup_seconds=time.perf_counter()-setup_mark)
                    if arm in ("O","BC"):
                        method_costs[(block,arm)].update(state="FAILED_DEPLOYMENT",
                            deployment=deployment[arm])
                    raise
                setup=time.perf_counter()-setup_mark
                required_calibration=0. if arm=="AF" else ev_cal["generation_seconds"]
                if arm=="P_k4_M32":
                    required_calibration+=ev_cal["posterior_seconds"]
                mark=time.perf_counter()
                try:
                    collect(block,"evaluation",arm,eval_ids,ev_theta,ev_q,ev_moves,
                            config.evaluation_seeds[block],config.evaluation_phases,model=student)
                except Exception:
                    attempted=time.perf_counter()-mark
                    deployment[arm]=dict(state="FAILED_DEPLOYMENT",setup_seconds=setup,
                        attempted_batched_deployment_seconds=attempted,
                        attached_shared_calibration_seconds=required_calibration,
                        attempted_conditional_total_seconds=setup+attempted+required_calibration)
                    if arm in ("O","BC"):
                        method_costs[(block,arm)].update(state="FAILED_DEPLOYMENT",
                            deployment=deployment[arm])
                    raise
                deployed=time.perf_counter()-mark
                deployment[arm]=dict(state="COMPLETE",setup_seconds=setup,
                    batched_deployment_seconds=deployed,
                    attached_shared_calibration_seconds=required_calibration,
                    conditional_total_seconds=setup+deployed+required_calibration)
                if arm in ("O","BC"):
                    method=method_costs[(block,arm)]
                    method.update(state="COMPLETE",deployment=deployment[arm],
                        component_wall_seconds=(method["required_acquisition_wall_seconds"]+
                            method["fit"]["fit_wall_seconds"]+
                            deployment[arm]["conditional_total_seconds"]),
                        component_measurement_scope=(
                            "Full required prefix plus own acquisition/calibrations, fit "
                            "initialization/optimization/checkpoints, evaluation calibration "
                            "and reload/batched deployment; excludes dataset and orchestration "
                            "I/O, hashing and support work. Not end-to-end standalone wall."))
                save_json(out/"episodes.json",episodes)
            reading=_read_block(episodes,block,config)
            per_context.extend(reading.pop("per_context"))
            block_timing[block].update(state="COMPLETE",wall_seconds=time.perf_counter()-block_started,
                                       cpu_seconds=time.process_time()-block_cpu)
            reading["timing"]=block_timing[block]
            block_results.append(reading)
            save_json(raw/f"block{block}_result.json",reading)
            save_json(out/"per_context.json",per_context)
            status["blocks_completed"]+=1
            save_status()

        expected_collection=2*(config.prefix_contexts+2*config.rollin_contexts)*config.horizon
        expected_evaluation=2*len(ARMS)*config.evaluation_contexts*config.horizon
        expected_updates=4*(config.epochs[0]*ceil(2*config.prefix_contexts/config.train_batch)+
            config.epochs[1]*ceil(2*(config.prefix_contexts+config.rollin_contexts)/config.train_batch))
        expected_rows=4*2*config.horizon*(config.epochs[0]*config.prefix_contexts+
            config.epochs[1]*(config.prefix_contexts+config.rollin_contexts))
        expected_diag=8*config.horizon*(2*config.prefix_contexts+config.rollin_contexts)
        branch_upper=(expected_collection+2*config.evaluation_contexts*config.horizon)*config.particles*2*32
        if (status["policy_fits_started"]!=4 or status["policy_fits_completed"]!=4 or
            status["blocks_completed"]!=2 or status["collection_team_ticks"]!=expected_collection or
            status["evaluation_team_ticks"]!=expected_evaluation or
            status["optimizer_updates"]!=expected_updates or
            status["processed_agent_time_rows"]!=expected_rows or
            status["calibration_fits"]!=2*(config.prefix_contexts+config.rollin_contexts+
                                             config.evaluation_contexts) or
            status["calibration_moves"]!=4*status["calibration_fits"] or
            sum(d["processed_agent_time_rows"] for d in diagnostics)!=expected_diag or
            len(diagnostics)!=8):
            raise AssertionError("fixed B04 work accounting mismatch")
        if model_counts.get("model_branch_transitions",0)>branch_upper:
            raise AssertionError("model branches exceed conservative bound")
        model_counts["model_root_particles"]=model_counts.get("model_initialization_worlds",0)//2
        root_counts={name:sum(cost.get(name,0) for cost in costs) for name in
            ("optional_roots","exact_zero_roots","zero_af_send_fallbacks","nonzero_roots")}
        status.update(state="COMPLETE",current_block=None)
        save_status()
        mark=time.perf_counter()
        artifacts=_artifacts(out)
        timing["artifact_hash_seconds"]+=time.perf_counter()-mark
        reading=dict(blocks=block_results,
            descriptive_integer_totals={a+"-"+b:[row["integer_completed_job_total_differences"][a+"-"+b]
                                     for row in block_results] for a,b in PAIRS},
            scope="two exploratory fresh paired blocks; no formal claim or pooling with B02/B03")
        summary=dict(state="COMPLETE",launch_sha=launch_sha,config=cfg,
            descriptive_native_reading=reading,counts={**status,**model_counts,**root_counts,
                "evaluation_optimizer_updates":0,"model_branch_transition_upper":branch_upper,
                "endpoint_diagnostic_agent_time_rows":expected_diag,
                "expected_collection_team_ticks":expected_collection,
                "expected_evaluation_team_ticks":expected_evaluation,
                "expected_optimizer_updates":expected_updates,
                "expected_processed_agent_time_rows":expected_rows},
            fits=fits,endpoint_diagnostics=diagnostics,data_provenance=provenance,
            standalone_method_costs=list(method_costs.values()),batch_costs=costs,
            physical_batch_costs=_sum_batch_costs(costs),block_timing=block_timing,
            timing=timing,resources=dict(wall_seconds=time.perf_counter()-started,
                cpu_seconds=time.process_time()-cpu_started,
                peak_single_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                scope="single scientific process through artifact hashing; excludes summary write"),
            artifacts=artifacts)
        write_json(out/"summary.json",summary)
        return summary
    except Exception as error:
        status.update(state="FAILED",error_type=type(error).__name__,error=str(error))
        current=status.get("current_block")
        if current in block_timing:
            block_timing[current].update(state="FAILED_PARTIAL",
                attempted_wall_seconds=time.perf_counter()-block_started,
                attempted_cpu_seconds=time.process_time()-block_cpu)
        if active_key is not None and current is not None:
            active_arm=active_key.rsplit("_",1)[-1]
            if (current,active_arm) in method_costs:
                method_costs[(current,active_arm)].update(state="FAILED_FIT",
                    attempted_fit_timing=fit_timing.get(active_key))
        partial_checkpoint_error=None
        if active_model is not None:
            try:
                save_checkpoint(raw/f"{active_key}_partial.pt",active_model,active_optimizer)
            except Exception as checkpoint_error:
                partial_checkpoint_error=f"{type(checkpoint_error).__name__}: {checkpoint_error}"
        save_status()
        save_json(out/"curves.json",curves)
        save_json(out/"episodes.json",episodes)
        save_json(out/"per_context.json",per_context)
        write_json(out/"summary.json",dict(state="FAILED",launch_sha=launch_sha,
            status=status,fit_timing=fit_timing,fits=fits,endpoint_diagnostics=diagnostics,
            data_provenance=provenance,completed_block_results=block_results,batch_costs=costs,
            block_timing=block_timing,timing=timing,partial_checkpoint_error=partial_checkpoint_error,
            standalone_method_costs=list(method_costs.values()),
            physical_batch_costs=_sum_batch_costs(costs),
            artifacts=_artifacts(out),resources=dict(
                wall_seconds=time.perf_counter()-started,
                cpu_seconds=time.process_time()-cpu_started,
                peak_single_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                scope="single scientific process through failed-summary preparation"),
            scope="incomplete technical attempt; no two-block B04 reading"))
        raise
