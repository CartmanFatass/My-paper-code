"""Two fixed H6 warm-start fits followed by one common final evaluation panel."""
from __future__ import annotations

from dataclasses import asdict
import gc
import json
from pathlib import Path
import platform
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_transmission.study import (
    artifact, frozen, process_resources, sha256, write_json,
)
from .evaluation import ARMS, EvalSpec, evaluate_episode
from .host import EVAL_WORLD_IDS, TRAIN_WORLD_IDS
from .training import TrainSpec, build_warmstart, load_parent, train_arm

DIRECTION = "uav_fleet_adaptation"
OBJECT_ID = "fleet_adaptation_b01"
PARENT_SHA256 = "98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343"
EXPECTED_OPTIMIZERS = {"coordinator":480, "discoverer_actor":96000,
    "discoverer_critic":96000, "team_discriminator":480, "individual_discriminator":1920}


def validate_worker(summary: dict) -> None:
    acceptable = summary.get("status") in ("collected","complete") or (
        summary.get("status") == "failed" and summary.get("failure_stage") == "reader")
    if not acceptable or summary.get("worker_status") != "complete":
        raise ValueError("worker incomplete; a trajectory panel cannot override failed training/freeze checks")
    if (summary.get("schema"),summary.get("direction"),summary.get("object_id")) != (1,DIRECTION,OBJECT_ID):
        raise ValueError("worker result identity differs")
    config = summary["config"]
    expected = {"new_fits":2,"training_episodes":1024,"training_team_steps":512000,
                "outer_updates":64,"evaluation_episodes":128,"evaluation_team_steps":64000,
                "total_native_steps":576000,"mask_requests":8160000,"motion_requests":3456000}
    if config.get("expected") != expected or summary.get("counts") != expected:
        raise ValueError("worker exposure differs from fixed complete comparison")
    if (config.get("direction") != DIRECTION or config.get("object_id") != OBJECT_ID
            or config.get("launch_sha") != summary["launch_sha"]
            or tuple(config.get("arms",())) != ARMS
            or tuple(config.get("training_world_ids",())) != TRAIN_WORLD_IDS
            or tuple(config.get("evaluation_world_ids",())) != EVAL_WORLD_IDS
            or config.get("train_spec") != json.loads(json.dumps(asdict(TrainSpec())))
            or config.get("eval_spec") != json.loads(json.dumps(asdict(EvalSpec())))):
        raise ValueError("worker fixed design binding differs")
    parent = summary["parent"]
    if (parent.get("checkpoint_sha256_before") != PARENT_SHA256
            or parent.get("checkpoint_sha256_after") != PARENT_SHA256):
        raise ValueError("parent checkpoint identity differs")
    if set(summary["fits"]) != {"A","F"} or set(summary["frozen_checks"]) != {"I","A","F"}:
        raise ValueError("missing fit or neural endpoint")
    expected_digests = {"I":parent["final_parameter_normalizer_digest"]}
    for arm,fit in summary["fits"].items():
        if (fit["status"] != "complete" or fit["initial_digest"] != expected_digests["I"]
                or fit["optimizer_calls"] != EXPECTED_OPTIMIZERS or fit["outer_updates"] != 32
                or fit["training_team_steps"] != 256000 or fit["training_episodes"] != 512
                or fit["final_digest"] == fit["initial_digest"]):
            raise ValueError("fit identity, exposure or movement differs")
        expected_digests[arm] = fit["final_digest"]
    for arm,check in summary["frozen_checks"].items():
        if (check["initial_digest"] != expected_digests[arm]
                or check["final_digest"] != expected_digests[arm]
                or check["normalizers_unchanged"] is not True
                or set(check["optimizer_calls"]) != set(EXPECTED_OPTIMIZERS)
                or any(check["optimizer_calls"].values())):
            raise ValueError("evaluation changed weights, normalizers or optimizers")


def _close_agent(agent):
    if getattr(agent,"writer",None):
        agent.writer.close()


def _fit_binding(arm: str, fit: dict, base: Path) -> dict:
    """Keep one complete fit record; outer summary carries its checked compact binding."""
    # Collector schema is normalized here; it remains visible in the direction-owned source.
    return {"status":fit["status"], "summary":artifact(base / arm / "summary.json",base),
            "initial_digest":fit["initialization"]["parameter_normalizer_digest"],
            "final_digest":fit["final_parameter_normalizer_digest"],
            "optimizer_calls":fit["optimizer_calls"], "outer_updates":fit["counts"]["updates"],
            "training_team_steps":fit["counts"]["training_team_steps"],
            "training_episodes":fit["counts"]["training_episodes"],
            "checkpoint":fit["checkpoint"], "parameter_motion":fit["parameter_motion"],
            "mask_requests":sum(d["counts"]["requested_candidates"] for row in fit["rollouts"]
                                for d in row["mask_decisions"]),
            "timing":{key:fit[key] for key in ("wall_seconds","cpu_seconds","peak_rss_kib_process","rss_scope")}}


def run_study(out: Path, checkpoint_root: Path, launch_sha: str, admission: dict) -> dict:
    wall, cpu = time.perf_counter(),time.process_time()
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    out.mkdir(parents=True,exist_ok=True)
    if (out / "summary.json").exists():
        raise FileExistsError("scientific summary exists; this study has no automatic retry or resume")
    expected = {"new_fits":2,"training_episodes":1024,"training_team_steps":512000,
                "outer_updates":64,"evaluation_episodes":128,"evaluation_team_steps":64000,
                "total_native_steps":576000,"mask_requests":8160000,"motion_requests":3456000}
    config = {"direction":DIRECTION,"object_id":OBJECT_ID,"launch_sha":launch_sha,
        "admission_operation":admission.get("operation_id"), "checkpoint_root":str(checkpoint_root),
        "source_training_sha":frozen.PRODUCER_SHA,"train_spec":asdict(TrainSpec()),
        "eval_spec":asdict(EvalSpec()),"arms":ARMS,"training_world_ids":TRAIN_WORLD_IDS,
        "evaluation_world_ids":EVAL_WORLD_IDS,"world_address":[260930,17],
        "training_order":["A","F"],"evaluation_order":"world increasing; cyclic four-arm order",
        "expected":expected,"expected_optimizer_calls_per_fit":EXPECTED_OPTIMIZERS,
        "runtime":{"python":platform.python_version(),"numpy":np.__version__,"torch":torch.__version__,
                   "device":"cpu","torch_threads":torch.get_num_threads(),
                   "torch_interop_threads":torch.get_num_interop_threads()},
        "checkpoint_semantics":"weights and retained normalizers; fresh Adam, buffers, recurrent/skill state, environments and RNG; no exact resume"}
    config = json.loads(json.dumps(config))
    write_json(out / "config.json",config)
    summary = {"schema":1,"direction":DIRECTION,"object_id":OBJECT_ID,"launch_sha":launch_sha,
               "status":"loading","config":config,"fits":{},"episodes":[],"frozen_checks":{}}
    write_json(out / "summary.json",summary)
    stage = "parent_loading"
    agents,hooks = {},[]
    try:
        record = load_parent(checkpoint_root)
        summary["parent"] = {"source":asdict(record["source"]),
            "source_training_sha":frozen.PRODUCER_SHA,"summary_identity":record["summary_identity"],
            "checkpoint":str(record["checkpoint"]),"checkpoint_record":record["checkpoint_record"],
            "checkpoint_sha256_before":record["checkpoint_sha256_before"],
            "final_parameter_normalizer_digest":record["summary"]["final_parameter_normalizer_digest"],
            "lineage_counts":record["summary"]["counts"]}
        for arm in ("A","F"):
            stage = f"training_{arm}"
            summary["status"] = stage
            write_json(out / "summary.json",summary)
            agent,fit = train_arm(arm,record,out / arm,launch_sha)
            _close_agent(agent)
            del agent
            gc.collect()
            summary["fits"][arm] = _fit_binding(arm,fit,out)
            write_json(out / "summary.json",summary)
        stage = "evaluation_loading"
        bindings = {}
        for arm in ("I","A","F"):
            payload = None
            expected_digest = record["summary"]["final_parameter_normalizer_digest"]
            if arm != "I":
                binding = summary["fits"][arm]["checkpoint"]
                checkpoint = out / arm / binding["path"]
                if checkpoint.stat().st_size != binding["bytes"] or sha256(checkpoint) != binding["sha256"]:
                    raise ValueError("endpoint checkpoint identity changed before evaluation")
                payload = torch.load(checkpoint,map_location="cpu",weights_only=True)
                expected_digest = summary["fits"][arm]["final_digest"]
            agent,_,initialization = build_warmstart(record,out / "runtime_logs" / f"eval_{arm}",payload=payload)
            agent.train(False)
            digest = frozen.digest_agent(agent)
            if digest != expected_digest:
                raise ValueError("evaluation restore identity differs")
            counts,handles = frozen.optimizer_counts(agent)
            hooks.extend(handles)
            agents[arm] = agent
            bindings[arm] = {"initial_digest":digest,"normalizers":frozen._normalizer_record(agent),"calls":counts}
        stage = "evaluation"
        summary["status"] = "evaluating"
        write_json(out / "summary.json",summary)
        for i,world_id in enumerate(EVAL_WORLD_IDS):
            ordered = ARMS[i % len(ARMS):] + ARMS[:i % len(ARMS)]
            for arm in ordered:
                row = evaluate_episode(arm,world_id,agents.get(arm.split("_")[0]),out)
                summary["episodes"].append(row)
                write_json(out / "summary.json",summary)
                print(json.dumps({"evaluation_episodes":len(summary["episodes"]),"arm":arm,"world":world_id}),flush=True)
        stage = "final_worker_checks"
        for arm,agent in agents.items():
            before = bindings[arm]
            summary["frozen_checks"][arm] = {"initial_digest":before["initial_digest"],
                "final_digest":frozen.digest_agent(agent),
                "normalizers_unchanged":before["normalizers"] == frozen._normalizer_record(agent),
                "optimizer_calls":dict(before["calls"])}
        for arm,fit in summary["fits"].items():
            checkpoint = out / arm / fit["checkpoint"]["path"]
            if (checkpoint.stat().st_size != fit["checkpoint"]["bytes"]
                    or sha256(checkpoint) != fit["checkpoint"]["sha256"]):
                raise ValueError("endpoint checkpoint changed during evaluation")
        summary["parent"]["checkpoint_sha256_after"] = sha256(record["checkpoint"])
        fit_values = summary["fits"].values()
        evaluation_steps = sum(row["steps"] for row in summary["episodes"])
        training_steps = sum(fit["training_team_steps"] for fit in fit_values)
        summary["counts"] = {
            "new_fits":len(summary["fits"]),
            "training_episodes":sum(fit["training_episodes"] for fit in fit_values),
            "training_team_steps":training_steps,
            "outer_updates":sum(fit["outer_updates"] for fit in fit_values),
            "evaluation_episodes":len(summary["episodes"]),"evaluation_team_steps":evaluation_steps,
            "total_native_steps":training_steps+evaluation_steps,
            "mask_requests":sum(fit["mask_requests"] for fit in fit_values)+sum(
                row["candidate_counts"]["mask"]["requested_candidates"] for row in summary["episodes"]),
            "motion_requests":sum(row["candidate_counts"]["motion"]["requested_candidates"] for row in summary["episodes"])}
        summary["worker_status"] = "complete"
        summary["status"] = "collected"
        validate_worker(summary)
        summary["worker_timing"] = {"wall_seconds":time.perf_counter()-wall,"cpu_seconds":time.process_time()-cpu}
        summary["process_resources_before_reader"] = process_resources()
        write_json(out / "summary.json",summary)
        stage = "reader"
        from .reader import read_run
        reading = read_run(out)
        summary["reading"] = artifact(out / "reading.json",out)
        summary["status"] = "complete"
        summary["timing"] = {"wall_seconds":time.perf_counter()-wall,"cpu_seconds":time.process_time()-cpu,
                             "scope":"run_study including training, evaluation, evidence and reader; imports/admission excluded"}
        summary["process_resources"] = process_resources()
        write_json(out / "summary.json",summary)
        return summary
    except BaseException as error:
        summary["status"],summary["failure_stage"] = "failed",stage
        summary["failure"] = {"type":type(error).__name__,"message":str(error),"traceback":traceback.format_exc()}
        summary["process_resources"] = process_resources()
        write_json(out / "summary.json",summary)
        raise
    finally:
        for handle in hooks:
            handle.remove()
        for agent in agents.values():
            _close_agent(agent)
