#!/usr/bin/env python3
"""Complete saved-data B11 reader; zero native transitions or new fits."""
import argparse
import json
from pathlib import Path
import resource
import sys
import time
import traceback
ROOT=Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.audit import equal,require
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.assets import checked_path
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import load_raw
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.records import artifact
from experiments.candidates.uav_local_history.b01.study import file_identity,write_json
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.assets import load_assets
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.audit import audit_episode
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.contract import CONTRASTS, DETERMINISTIC,FROZEN,OBJECT,Protocol,source_identities
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.reading import comparisons,paired_behavior
from experiments.candidates.uav_fleet_adaptation.b11_silence_commitment.study import validate_counts


def _read_all(batch,out,parent,protocol,report,publish):
    out=Path(out)
    expected=[("evaluation",program,world,tape) for wi,world in enumerate(protocol.worlds)
              for program,tape in protocol.episode_order(wi)]
    require([tuple(row[key] for key in ("kind","program","world","tape")) for row in batch["rows"]]==expected,
            "complete frozen execution order")
    require(batch["protocol"]==protocol.to_dict() and batch["expected"]==protocol.expected(),"protocol and expected bill")
    counts=report["actual"]
    audits=[]
    layouts={}
    behavior={}
    world_raw={}
    active_world=None
    def finish_world(world):
        if world is None:
            return
        result={}
        for left,right in CONTRASTS:
            tapes=(None,) if right in DETERMINISTIC else (0,1)
            result[left+"-"+right]=[dict(right_tape=tape,**paired_behavior(world_raw[left,None],world_raw[right,tape])) for tape in tapes]
        behavior[str(world)]=result
    for row in batch["rows"]:
        report["progress"]={key:row[key] for key in ("id","program","world","tape")}
        require(row["id"]==f'evaluation_{row["program"]}_w{row["world"]}_t{row["tape"]}',"episode id")
        require(row["motion_root"]==(None if row["tape"] is None else protocol.evaluation_motion_roots[row["tape"]]),"private root")
        raw=load_raw(checked_path(out,row["raw"]["path"],row["raw"]))
        require(row["raw"]["path"]=="raw/"+row["id"]+".npz","raw episode path")
        require(row["raw_array_bytes"]==sum(value.nbytes for value in raw.values()),"raw byte roster")
        if active_world!=row["world"]:
            finish_world(active_world)
            world_raw.clear()
            active_world=row["world"]
        audits.append(audit_episode(raw,row,protocol,parent,counts=counts,inflight=report["inflight"]))
        # Keep only compared trajectories for this world's six cells, not a
        # duplicate serialized raw archive.
        world_raw[row["program"],row["tape"]]={key:raw[key] for key in ("commands","transmitter_mask","positions","action_index")}
        layout=raw["positions"][0].tobytes()+raw["initial_users"].tobytes()
        if row["world"] in layouts:
            require(layout==layouts[row["world"]],"paired world layout")
        else:
            require(layout not in layouts.values(),"distinct world layout")
            layouts[row["world"]]=layout
        report["policy_costs"]=sum_counts(audit["policy_counts"] for audit in audits)
        publish()
    finish_world(active_world)
    bill=protocol.expected()
    for key,reference in (("saved_episodes","complete_episodes"),("saved_native_ticks","native_steps"),
        ("scalar_states","reader_scalar_states"),("observation_rows","reader_local_rows"),
        ("policy_requests","motion_requests"),("gate_requests","gate_opportunities")):
        require(counts[key]==bill[reference],"full reader exposure "+key)
    counts.update(scalar_power_links=counts["scalar_states"]*270,distance_pairs=counts["scalar_states"]*260,
        dense_sinr_slots=counts["scalar_states"]*275,layout_verification_draws=bill["layout_verification_draws"],
        bootstrap_integers=bill["bootstrap_integers"])
    for key,reference in (("scalar_power_links","reader_scalar_power_links"),("distance_pairs","reader_distance_pairs"),
        ("dense_sinr_slots","reader_dense_sinr_slots")):
        require(counts[key]==bill[reference],"full physical bill "+key)
    require(report["policy_costs"]==batch["costs"]["all_policy"],"independent policy/cache work")
    validate_counts(batch["actual"],batch["costs"],protocol)
    require(state_digest(parent.state_dict())==batch["initial_parent_state"]==batch["final_parent_state"],"unchanged parent")
    result=comparisons(batch["rows"],protocol)
    require(result==batch["comparisons"],"all metrics/nine contrasts/shared bootstrap")
    report.update(episodes=audits,comparisons=result,per_world_behavior=behavior,
        max_abs_errors={key:max(audit["max_abs_errors"][key] for audit in audits) for key in audits[0]["max_abs_errors"]})
    return result


def read_result(out,repo,*,asset_paths=None):
    out,repo=Path(out).resolve(),Path(repo).resolve()
    if (out/"reading.json").exists():
        raise FileExistsError("reader evidence exists; preserve and reconcile")
    wall,cpu=time.perf_counter(),time.process_time()
    report=dict(status="INCOMPLETE",actual=dict(native_steps=0,optimizer_steps=0,refits=0),inflight={},policy_costs={})
    def publish(full=False):
        report.update(reader_wall_seconds=time.perf_counter()-wall,reader_cpu_seconds=time.process_time()-cpu,
            process_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out/"reading.json",report)
        write_json(out/"reading-progress.json",{key:report.get(key) for key in
            ("status","actual","progress","reader_wall_seconds","reader_cpu_seconds")})
    try:
        batch=json.loads((out/"summary.json").read_text())
        require(batch["object"]==OBJECT and batch["state"]=="COMPLETE" and batch["scientific_execution"] is True
            and Protocol.from_dict(batch["protocol"])==FROZEN,"fixed complete production result")
        require(batch["admission"]["sha"]==batch["launch_sha"],"admitted source identity")
        report["worker_summary"]=artifact(out/"summary.json",out)
        require(source_identities(repo)==batch["sources"],"full consumed source identity")
        if asset_paths is None:
            asset_paths={name:value["path"] for name,value in batch["inputs"].items()}
        parent,identities=load_assets(asset_paths)
        require(set(batch["inputs"])=={"P0"},"P0-only inputs")
        for key in ("bytes","sha256","canonical_path","canonical_node","source_launch_sha","state_sha256"):
            require(identities["P0"][key]==batch["inputs"]["P0"][key],"original consumed P0 "+key)
        log=checked_path(out,batch["episode_log"]["path"],batch["episode_log"])
        require(batch["episode_log"]["path"]=="episodes.jsonl" and [json.loads(line) for line in log.read_text().splitlines()]==batch["rows"],"complete episode ledger")
        _read_all(batch,out,parent,FROZEN,report,publish)
        require(source_identities(repo)==batch["sources"],"reader source unchanged")
        identity=file_identity(asset_paths["P0"])
        require(all(identity[key]==identities["P0"][key] for key in ("bytes","sha256")),"reader asset unchanged")
        require(state_digest(parent.state_dict())==identities["P0"]["state_sha256"],"reader frozen P0 unchanged")
        report.update(status="VERIFIED",sources=batch["sources"],launch_sha=batch["launch_sha"],
            timing_scope="Full scalar radio/movement/row, source C, independent OFF/Hdirect and own-memory recursion; metrics and paired bootstrap. Zero native steps/fits.")
    except BaseException:
        report.update(status="FAILED",failure=traceback.format_exc(),interrupted_call_work_may_be_unmeasured=True)
        if report["inflight"].get("policy_agents"):
            report["incurred_policy_costs"]=sum_counts((report["policy_costs"],sum_counts(report["inflight"]["policy_agents"])))
        raise
    finally:
        publish(full=True)
    return report


def publication(batch,reading,out):
    out=Path(out)
    paths=[path for path in out.rglob("*") if path.is_file()]
    return dict(object=OBJECT,launch_sha=batch["launch_sha"],worker_state=batch["state"],reader_status=reading["status"],
        actual=batch["actual"],worker_costs=batch["costs"],reader_actual=reading["actual"],
        worker_wall_seconds=batch["worker_wall_seconds"],worker_cpu_seconds=batch["worker_cpu_seconds"],
        reader_wall_seconds=reading["reader_wall_seconds"],reader_cpu_seconds=reading["reader_cpu_seconds"],
        chain_wall_seconds=reading.get("chain_wall_seconds"),chain_cpu_seconds=reading.get("chain_cpu_seconds"),
        worker_max_rss_kib=batch["worker_max_rss_kib"],process_max_rss_kib=reading["process_max_rss_kib"],
        max_abs_errors=reading["max_abs_errors"],levels=reading["comparisons"]["levels"],
        contrasts=reading["comparisons"]["contrasts"],adverses=reading["comparisons"]["adverses"],
        memory_events=[event for episode in reading["episodes"] for event in episode["memory_events"]],
        uncertainty=reading["comparisons"]["uncertainty"],per_world_behavior=reading["per_world_behavior"],
        summary=artifact(out/"summary.json",out),reading=artifact(out/"reading.json",out),
        episode_log=batch["episode_log"],raw_files=[row["raw"] for row in batch["rows"]],
        canonical_output=str(out.resolve()),storage_before_publication=dict(files=len(paths),
            logical_bytes=sum(path.stat().st_size for path in paths),allocated_bytes=sum(path.stat().st_blocks*512 for path in paths)),
        evidence_scope="One canonical raw episode copy; compact all-world levels/effects, adverse worlds, identities and complete reader preserved.")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--p0",type=Path,required=True)
    parser.add_argument("--launch-sha",required=True)
    parser.add_argument("--seed",type=int,required=True)
    args=parser.parse_args(argv)
    if args.seed!=30022000:
        parser.error("fixed B11 seed required")
    batch=json.loads((args.out/"summary.json").read_text())
    require(batch["launch_sha"]==args.launch_sha,"reader requested launch sha")
    return read_result(args.out,ROOT,asset_paths={"P0":args.p0})

if __name__=="__main__":
    main()
