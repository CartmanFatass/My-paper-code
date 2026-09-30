#!/usr/bin/env python3
"""Complete saved-data reading with bounded extra model work and no native steps."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.read import identity
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.read import equal, regenerate_bundle, require
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.study import load_asset
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.contract import (
    ASSET, ASSET_PATH, FROZEN, OBJECT, PINS, READER_CPU_SECONDS, CpuBudget, Protocol,
    arm_parts, source_identities, validate_counts,
)
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.reading import (
    cost_totals, episode_metrics, read_comparisons,
)
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.verify_coordinator import (
    coordinator_counts, verify_coordinator,
)
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.verify_local import local_counts, verify_local


def error_summary(values):
    result = {}
    for offset, entries in values.items():
        result[offset] = {key: dict(count=len(entries), mean=float(np.mean([e[key] for e in entries])),
                                   mean_absolute=float(np.mean([abs(e[key]) for e in entries])),
                                   rms=float(np.sqrt(np.mean([e[key] ** 2 for e in entries]))),
                                   minimum=float(min(e[key] for e in entries)),
                                   maximum=float(max(e[key] for e in entries)))
                          for key in entries[0]}
    return result


def read_batch(out, *, permit_fixture=False):
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    budget = CpuBudget(READER_CPU_SECONDS, started=start_cpu)
    out = Path(out).resolve()
    progress_path = out / "reader-progress.json"
    if progress_path.exists() or (out / "reading.json").exists():
        raise FileExistsError("reader already attempted; reconcile paid reading rather than repeat")
    calls = dict(environment_steps=0, full_C_ranking_queries=0, optimizer_steps=0,
                 regenerated_tape_integers=0, episode_metric_reconstructions=0,
                 metric_one_step_clip_agent_ops=0, **local_counts(), **coordinator_counts())
    progress = dict(object=OBJECT, status="READING", completed_rows=0, current_row=None,
                    reader_calls=calls, reader_cpu_envelope_seconds=READER_CPU_SECONDS)

    def publish():
        progress.update(reader_wall_seconds=time.perf_counter() - start_wall,
                        reader_cpu_seconds=time.process_time() - start_cpu,
                        process_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        write_json(progress_path, progress)

    publish()
    try:
        budget.check()
        summary_path, config_path = out / "summary.json", out / "config.json"
        summary = json.loads(summary_path.read_text())
        config = json.loads(config_path.read_text())
        progress["inputs"] = {"summary": file_identity(summary_path), "config": file_identity(config_path)}
        require(summary["object"] == OBJECT and summary["status"] == "COMPLETE", "incomplete/wrong collection")
        protocol = Protocol.from_dict(summary["protocol"])
        production = summary["scientific_invocation"]
        require(production or permit_fixture, "fixture reading requires explicit permission")
        require(not production or protocol == FROZEN, "production panel differs from selection")
        for key in config:
            require(summary[key] == config[key], "config/summary binding " + key)
        require(summary["expected"] == protocol.expected(), "expected cost contract")
        require(summary["source_sha256"] == source_identities(ROOT), "reader code/dependency identity")
        if production:
            require(all(summary["asset"][key] == value for key, value in ASSET.items()), "original S binding")
            require(Path(summary["asset"]["path"]) == ASSET_PATH, "original S file path")
            require(torch.get_num_threads() == torch.get_num_interop_threads() == 1, "reader CPU thread contract")
        else:
            require(Path(summary["asset"]["path"]).resolve() != ASSET_PATH.resolve()
                    and summary["asset"]["sha256"] != ASSET["sha256"]
                    and summary["asset"]["state_sha256"] != ASSET["state_sha256"],
                    "synthetic reading must not load the production asset or its tensors")
        actor, actor_identity = load_asset(summary["asset"]["path"], ASSET if production else summary["asset"])
        require(actor_identity["state_sha256"] == summary["asset_after_state_sha256"], "unchanged worker asset")
        validate_counts(summary)
        require(cost_totals(summary["rows"]) == summary["costs"], "worker cost aggregation")
        require([(r["arm"], r["world"], r["tape"]) for r in summary["rows"]] == list(protocol.schedule()),
                "complete ordered schedule")
        bundles = {}
        for world in protocol.worlds:
            for tape in protocol.tapes:
                budget.check()
                calls["regenerated_tape_integers"] += (protocol.horizon // 4) * 11
                bundles[world, tape] = regenerate_bundle(protocol, world, tape)
        require(summary["tape_provision"]["unique_integers"] == calls["regenerated_tape_integers"]
                == summary["expected"]["unique_tape_integers"], "once-per-bundle generation")
        require(summary["tape_provision"]["unique_bytes"] == calls["regenerated_tape_integers"] * 8
                and summary["tape_provision"]["unique_bundles"] == len(bundles), "tape storage exposure")
        audits, initials = [], {}
        for index, row in enumerate(summary["rows"]):
            budget.check()
            progress["current_row"] = {k: row[k] for k in ("arm", "world", "tape")}
            publish()
            family, coordinator = arm_parts(row["arm"])
            require(row["policy_sha256"] == (summary["asset"]["state_sha256"] if family == "S_I"
                    else PINS["experiments/candidates/uav_local_history/b01/controller.py"]), "row policy identity")
            raw_path = identity(out, row["raw"])
            with np.load(raw_path, allow_pickle=False) as archive:
                raw = {key: archive[key] for key in archive.files}
            local = verify_local(raw, row, protocol, actor, bundles.get((row["world"], row["tape"])), calls, budget.check)
            radio = verify_coordinator(raw, row, protocol, calls, budget.check)
            budget.check()
            calls["episode_metric_reconstructions"] += 1
            calls["metric_one_step_clip_agent_ops"] += protocol.horizon * 5 + protocol.horizon // 4 * 10
            if coordinator in ("S2", "T2"):
                calls["metric_one_step_clip_agent_ops"] += protocol.horizon // 4 * 10
            for key, value in episode_metrics(raw, row["arm"]).items():
                equal(row[key], value, "native/exposure metric " + key, 1e-12)
            digest = array_digest(raw["positions"][0], raw["initial_users"], raw["observations"][0])
            require(initials.setdefault(row["world"], digest) == digest, "paired initial geometry/observation")
            audits.append(dict(**progress["current_row"], local=local,
                               independently_checked_candidate_pairs=sum(len(r["independently_checked_pairs"]) for r in radio["rounds"]),
                               forecast_error_summary=error_summary(radio["forecast_errors_by_offset"])))
            progress["completed_rows"] = index + 1
            publish()
            if (index + 1) % 16 == 0:
                print("B05_READER", index + 1, "of", len(summary["rows"]), flush=True)
        e = summary["expected"]
        require(calls["S_forward_attempts"] == calls["S_forward_completed"] == e["reader_s_forward_rows"], "complete S forward reading")
        require(calls["S_helper_attempts"] == calls["S_helper_completed"] == e["reader_s_helper_calls"], "complete S helper reading")
        require(calls["native_formula_attempts"] == calls["native_formula_completed"]
                == e["reader_native_observation_formula_checks"], "complete endpoint/report/terminal formula reading")
        require(calls["candidate_reduction_attempts"] == calls["candidate_reduction_completed"]
                <= e["reader_candidate_state_reductions_ceiling"], "bounded coordinator radio reading")
        require(calls["full_C_ranking_queries"] == calls["environment_steps"] == calls["optimizer_steps"] == 0,
                "undeclared reader work")
        require(state_digest(actor.state_dict()) == summary["asset"]["state_sha256"], "reader mutated actor")
        require(source_identities(ROOT) == summary["source_sha256"], "reader source drift")
        comparisons = read_comparisons(summary["rows"], protocol)
        require(comparisons == summary["comparisons"], "fixed paired-world arithmetic")
        for key, path in (("summary", summary_path), ("config", config_path)):
            require(file_identity(path) == progress["inputs"][key], "reader input changed during verification")
        budget.check()
        result = dict(object=OBJECT, status="VERIFIED", launch_sha=summary["launch_sha"],
                      inputs=progress["inputs"], source_sha256=summary["source_sha256"], asset=summary["asset"],
                      actual=summary["actual"], worker_costs=summary["costs"], reader_calls=calls,
                      audits=audits, comparisons=comparisons, reader_cpu_envelope_seconds=READER_CPU_SECONDS,
                      reader_wall_seconds=time.perf_counter() - start_wall,
                      reader_cpu_seconds=time.process_time() - start_cpu,
                      process_peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                      scope="All saved native endpoints and every report/terminal masked observation reconstructed; "
                      "every S helper/one-row forward and I draw verified; C/Q use paid source-bound rankings with "
                      "no new full C query. All completed E scores and at most five actually scored joint pairs per "
                      "round recomputed. All saved search/arrival decisions checked. Radio kernels shared with the "
                      "native source; observation assembly/search/forecast arithmetic separately reconstructed. "
                      "No native suffix counterfactual, new fit or safety/energy equivalence. Timings include input "
                      "loads/checks, arithmetic/model work and prior writes; final self-writes excluded.")
        write_json(out / "reading.json", result)
        progress.update(status="VERIFIED", current_row=None)
        publish()
        return result
    except Exception:
        progress.update(status="INCOMPLETE", error=traceback.format_exc())
        publish()
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    result = read_batch(args.out)
    print(result["status"], flush=True)


if __name__ == "__main__":
    main()
