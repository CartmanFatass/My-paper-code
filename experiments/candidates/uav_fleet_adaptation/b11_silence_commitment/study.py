"""One fixed sequential complete purchase, no optimizer or training endpoint."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import resource
import time
import traceback
import torch
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.records import add, artifact
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_assets
from .collect import collect_episode
from .contract import FROZEN, OBJECT, source_identities
from .reading import comparisons

ROOT=Path(__file__).resolve().parents[4]


def costs(rows, counts, inflight=None):
    ledgers=[row["policy_counts"] for row in rows]
    if inflight and inflight.get("policy_agents"):
        ledgers.append(sum_counts(inflight["policy_agents"]))
    policy=sum_counts(ledgers)
    return dict(all_policy=policy, frozen_forward_rows=policy.get("neural_rows",0),
        controller_power_links=sum(policy.get(key,0) for key in ("candidate_links","setup_links","off_setup_links")),
        native_dense_power_slots=counts.get("native_dense_power_slots",0),
        native_unique_distance_pairs=counts.get("native_unique_distance_pairs",0),
        raw_uncompressed_array_bytes=sum(row["raw_array_bytes"] for row in rows),
        raw_compressed_file_bytes=sum(row["raw"]["bytes"] for row in rows),
        scope="Actual per-agent episode C/P0 caches, CJ OFF work, bypasses; native constructor included. No shadow C at bypass.")


def validate_counts(actual, cost, protocol):
    expected=protocol.expected()
    for key in ("fits","optimizer_steps","new_acquisition_targets","complete_episodes","evaluation_episodes",
        "explicit_resets","constructor_resets","native_steps","native_uav_ticks","mask_installs","motion_requests",
        "motion_draws","gate_opportunities","gate_draws","native_dense_power_slots","native_unique_distance_pairs",
        "mask_refresh_dense_sinr_slots","layout_verification_draws","bootstrap_integers","worker_layout_draws"):
        if type(actual.get(key)) is not int or actual[key]!=expected[key]:
            raise AssertionError("complete B11 exposure differs: "+key)
    if actual["evaluation_native_steps"]!=expected["native_steps"]:
        raise AssertionError("evaluation step count")
    for first,second in (("explicit_reset_calls","explicit_resets"),("native_step_calls","native_steps"),
        ("motion_request_calls","motion_requests"),("constructor_calls","constructor_resets"),
        ("gate_opportunity_calls","gate_opportunities"),("mask_install_calls","mask_installs")):
        if actual.get(first,0)!=actual[second]:
            raise AssertionError("incomplete call: "+first)
    c=cost["all_policy"]
    bypass=c["memory_consumed"]
    exact=dict(policy_requests=expected["motion_requests"], sampled_draws=expected["motion_draws"],
        target_vectors=expected["Hdirect_target_vectors"],off_score_evaluations=expected["CJ_off_scores"],
        off_logical_ticks=expected["CJ_off_scores"]*4,requests=expected["motion_requests"]-bypass,
        law_evaluations=expected["motion_requests"]-bypass,bypass_requests=bypass)
    for key,value in exact.items():
        if c[key]!=value:
            raise AssertionError("B11 policy count: "+key)
    for key,limit in (("trajectories","C_path_ceiling"),("model_ticks","C_model_tick_ceiling"),
        ("off_setup_links","off_link_ceiling"),("neural_rows","frozen_forward_ceiling")):
        if not 0<=c[key]<=expected[limit]:
            raise AssertionError("B11 cache/branch ceiling: "+key)
    if c["hits"]+c["misses"]!=c["requests"] or c["trajectories"]!=27*c["misses"] or c["model_ticks"]!=108*c["misses"]:
        raise AssertionError("exact private C work")
    if cost["controller_power_links"]>expected["controller_link_ceiling"] or c["candidate_links"]+c["setup_links"]>expected["C_link_ceiling"] or c["off_sinr_slots"]!=c["off_setup_links"]:
        raise AssertionError("actual link accounting")
    if any(c[key]!=0 for key in ("helper_calls","helper_setup_links","helper_extreme_links","score_tail_evaluations")):
        raise AssertionError("unpurchased helper work")


def _execute(out, parent, env, protocol, batch, publish):
    protocol.validate()
    out=Path(out)
    counts,inflight=batch["actual"],batch["inflight"]
    batch["initial_parent_state"]=state_digest(parent.state_dict())
    with (out/"episodes.jsonl").open("x",encoding="utf-8") as stream:
        for wi,world in enumerate(protocol.worlds):
            for program,tape in protocol.episode_order(wi):
                row=collect_episode(env,program=program,world=world,tape=tape,parent=parent,out=out,
                    protocol=protocol,counts=counts,inflight=inflight)
                batch["rows"].append(row)
                stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+"\n")
                stream.flush()
                batch["progress"]={key:row[key] for key in ("program","world","tape")}
                publish()
    counts["worker_layout_draws"]=(counts["explicit_resets"]+counts["constructor_resets"])*115
    counts["bootstrap_integers"]=protocol.bootstrap_resamples*len(protocol.worlds)
    batch["episode_log"]=artifact(out/"episodes.jsonl",out)
    batch["final_parent_state"]=state_digest(parent.state_dict())
    if batch["final_parent_state"]!=batch["initial_parent_state"] or any(p.grad is not None or p.requires_grad for p in parent.parameters()):
        raise AssertionError("frozen parent changed")
    for program in ("CJ_KEEP","CJ_RETURN"):
        rows=[row for row in batch["rows"] if row["program"]==program]
        created=sum(row["memory_created"] for row in rows)
        consumed=sum(row["memory_consumed"] for row in rows)
        terminal=sum(row["terminal_pending"] for row in rows)
        if created-consumed!=terminal or created>protocol.expected()["memory_creation_per_arm_ceiling"] or consumed>protocol.expected()["memory_consumption_per_arm_ceiling"]:
            raise AssertionError("memory conservation/ceilings")
    batch["costs"]=costs(batch["rows"],counts)
    validate_counts(counts,batch["costs"],protocol)
    batch["comparisons"]=comparisons(batch["rows"],protocol)


def run_batch(out, launch_sha, *, admission, asset_paths, entry_start=None, entry_cpu=None):
    # Entrypoint obtains this token through the live admission kernel before
    # importing torch/worker or changing runtime state. This guard also protects
    # accidental direct API use from creating output or loading assets.
    if not admission or admission.get("sha")!=launch_sha:
        raise ValueError("production requires accepted exact-source admission")
    protocol=FROZEN
    out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    allowed={"launch-status.json","launch-manifest.json","admission-preflight.json","stdout.log","stderr.log"}
    if any(path.name not in allowed or not path.is_file() or path.is_symlink() for path in out.iterdir()):
        raise FileExistsError("scientific output exists; reconcile accepted operation")
    (out/"raw").mkdir()
    wall=time.perf_counter() if entry_start is None else entry_start
    cpu=time.process_time() if entry_cpu is None else entry_cpu
    counts=dict(fits=0,optimizer_steps=0,new_acquisition_targets=0,gate_draws=0)
    batch=dict(object=OBJECT,state="RUNNING",scientific_execution=True,launch_sha=launch_sha,
        protocol=protocol.to_dict(),expected=protocol.expected(),actual=counts,rows=[],inflight={},
        admission=admission,start_utc=datetime.now(timezone.utc).isoformat(),runtime=dict(python=platform.python_version(),
        torch=torch.__version__,threads=torch.get_num_threads(),thread_environment={key:os.environ.get(key) for key in
        ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")}),
        timing_scope="Runner entry through worker; full saved-data reader follows; admission/staging/support separate.")
    env=None
    def publish(full=False):
        batch.update(worker_wall_seconds=time.perf_counter()-wall,worker_cpu_seconds=time.process_time()-cpu,
            worker_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out/"summary.json",batch)
        write_json(out/"progress.json",{key:batch.get(key) for key in
            ("state","actual","progress","worker_wall_seconds","worker_cpu_seconds")})
    try:
        batch["sources"]=source_identities(ROOT)
        parent,batch["inputs"]=load_assets(asset_paths)
        write_json(out/"config.json",{key:batch[key] for key in
            ("object","scientific_execution","launch_sha","protocol","expected","sources","runtime","inputs")})
        publish(full=True)
        from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import make_real,check_host
        add(counts,"constructor_calls")
        env=make_real(protocol.constructor_seed)
        add(counts,"constructor_resets")
        add(counts,"native_dense_power_slots",275)
        add(counts,"native_unique_distance_pairs",int(env.env._path_loss_cache_misses))
        batch["host"]=check_host(env)
        _execute(out,parent,env,protocol,batch,publish)
        if source_identities(ROOT)!=batch["sources"]:
            raise AssertionError("accepted source changed")
        for name,path in asset_paths.items():
            identity=file_identity(path)
            if any(identity[key]!=batch["inputs"][name][key] for key in ("bytes","sha256")):
                raise AssertionError("consumed original asset changed")
        batch.update(state="COMPLETE",finish_utc=datetime.now(timezone.utc).isoformat())
    except BaseException:
        batch.update(state="FAILED",failure=traceback.format_exc(),interrupted_call_work_may_be_unmeasured=True)
        batch["costs"]=costs(batch["rows"],counts,batch["inflight"])
        raise
    finally:
        if env is not None:
            env.close()
        publish(full=True)
    return batch
