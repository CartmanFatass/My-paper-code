"""The single complete B07 saved-evidence reconstruction and endpoint reading."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import time
import traceback

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b06_count_development.audit import check_episode, _equal, _require
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import FROZEN as OLD_PROTOCOL
from experiments.candidates.uav_fleet_adaptation.b06_count_development.controllers import FeatureMemo, MemoC
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import checked_path, verify_inputs, load_actors, load_dataset
from .audit import check_native, check_final_policy, forward_one, probability_reference, target_reference, replay_scope
from .contract import FITS, FROZEN, INPUT_ROOT, INPUT_MANIFEST_SHA256, OLD_REL, OBJECT, array_digest, source_identities
from .data import STAT_NAMES, statistics_summary, target_statistics
from .fit_reading import check_fits, endpoint_reading, equal_tree
from .reading import comparisons
from .study import costs, validate_counts


def _load_raw(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def check_archive(manifest, dataset, targets, parent, counts, progress, *, work=None, record=None, root=INPUT_ROOT):
    """All256 source files,81920 C/helper/parent/target rows; no old actor replay."""
    work = {} if work is None else work
    record = {} if record is None else record
    records = record.setdefault("records", [])
    offset = 0
    all_scores = np.empty((81920, 27), dtype=np.float64)
    max_score_error = max_target_error = 0.
    for row in manifest["rows"]:
        progress(dict(kind="archive", id=row["id"], completed_rows=offset))
        path = checked_path(root, OLD_REL / row["raw"]["path"], row["raw"])
        raw = _load_raw(path)
        algebra = check_episode(raw, row, OLD_PROTOCOL)
        teachers, helpers = [MemoC(5) for _ in range(5)], [FeatureMemo(5) for _ in range(5)]
        first = offset
        with replay_scope(work, row["id"], teachers, helpers):
            offset, score_error, target_error = _archive_episode(raw, dataset, targets, parent, counts,
                                                                 teachers, helpers, offset, all_scores)
            max_score_error = max(max_score_error, score_error)
            max_target_error = max(max_target_error, target_error)
            _require(sum_counts(p.counters for p in teachers) == row["expert_counts"], "archive C cache/work reconstruction")
        counts["saved_files"] += 1
        counts["saved_ticks"] += algebra["saved_native_steps"]
        counts["decision_rows"] += algebra["decision_rows"]
        counts["archive_target_rows"] += 2 * (offset - first)
        records.append(dict(id=row["id"], first=first, stop=offset, phase=row["phase"],
                            saved_ticks=algebra["saved_native_steps"], decision_rows=algebra["decision_rows"]))
        record.update(files=len(records), rows=offset, max_score_abs_error=max_score_error, max_target_abs_error=max_target_error)
    _require(offset == 81920, "complete archived row count")
    record.update(C_costs=work["C_costs"], helper_costs=work["helper_costs"],
                  scope="Every old saved native tick/assignment/observation and every C/feature/nav/target row; "
                        "phase1/2 saved acquisition actor logits receive original algebra/cache checks, not an unpriced actor replay")
    return all_scores, record


def _archive_episode(raw, dataset, targets, parent, counts, teachers, helpers, offset, all_scores):
    max_score_error = max_target_error = 0.
    for di, tick in enumerate(raw["decision_ticks"]):
        tick = int(tick)
        for agent in range(5):
            obs, nav = raw["observations"][tick, agent], int(raw["nav_pre"][di, agent])
            counts["C_requests"] += 1
            teacher = teachers[agent].query(obs.copy(), tick, nav)
            counts["helper_requests"] += 1
            helper = helpers[agent].query(obs.copy(), tick, nav)
            for key in ("features", "fallback", "next_nav", "n_current", "n_peers"):
                _equal(helper[key], teacher[key], "archive full helper/C " + key)
            for field, source in (("features", "features"), ("expert_fallback", "fallback"),
                                  ("expert_action_index", "action_index"), ("expert_nav_next", "next_nav"),
                                  ("expert_memo_hit", "memo_hit"), ("expert_scores", "scores"),
                                  ("expert_served", "served")):
                _equal(raw[field][di, agent], teacher[source], "archive full C " + field,
                       tolerance=1e-12 if field == "expert_scores" else None)
            max_score_error = max(max_score_error, float(np.max(np.abs(raw["expert_scores"][di, agent] - teacher["scores"]))))
            _equal(dataset[0][offset], helper["features"], "archive fixed dataset feature")
            _equal(dataset[1][offset], teacher["action_index"], "archive fixed dataset label")
            _require(dataset[2][offset] == 5, "archive fixed count")
            logits = forward_one(parent, helper["features"], counts)
            p = probability_reference(logits)
            # Targets are bound to the original saved FP64 scores, which were
            # independently reconstructed above within the declared tolerance.
            s = raw["expert_scores"][di, agent]
            t, h = target_reference(p, s, int(dataset[1][offset]))
            _equal(targets["parent_logits"][offset], logits, "archive frozen P0 logits")
            for key, expected in (("parent_probabilities", p), ("T", t), ("H", h)):
                _equal(targets[key][offset], expected, "archive target " + key, tolerance=5e-14)
                max_target_error = max(max_target_error, float(np.max(np.abs(targets[key][offset] - expected))))
            if np.all(s == s[0]):
                _require(targets["T"][offset].tobytes() == p.tobytes(), "archive flat exact P0 copy")
            _require(np.all(targets["T"][offset][p == 0] == 0), "archive T zero-support preservation")
            stats = target_statistics(p, t, h, s, int(dataset[1][offset]), bool(teacher["fallback"]))
            _equal(targets["statistics"][offset], stats, "archive complete target diagnostics", tolerance=1e-12)
            all_scores[offset] = s
            offset += 1
    return offset, max_score_error, max_target_error


def _reserve_reader(out):
    """The exclusive marker is acquired before failure-record ownership."""
    if (out / "reading.json").exists():
        raise FileExistsError("B07 reading already exists; preserve/reconcile rather than repeat it")
    with (out / "reading-progress.json").open("x", encoding="utf-8") as stream:
        json.dump(dict(object=OBJECT, status="INCOMPLETE", reservation="exclusive-reader",
                       pid=os.getpid(), start_utc=datetime.now(timezone.utc).isoformat()), stream)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_result(out, repo):
    wall, cpu = time.perf_counter(), time.process_time()
    out, repo = Path(out).resolve(), Path(repo).resolve()
    _reserve_reader(out)
    counts = dict(saved_files=0, saved_ticks=0, decision_rows=0, archive_target_rows=0,
                  C_requests=0, helper_requests=0, actor_forward_calls=0, actor_rows=0,
                  endpoint_rows=0, native_steps=0, optimizer_steps=0)
    work = dict(archive={}, final={})
    reading = dict(object=OBJECT, status="INCOMPLETE", reader_counts=counts, archive={}, final={}, fits=[], endpoints=[],
                   reconstruction_work=work,
                   start_utc=datetime.now(timezone.utc).isoformat(),
                   scope="One complete saved-data reader; no native transitions, optimizer replay, shadow C/P on learned "
                         "deployment histories, new uniform sample, calibration or counterfactual branches")

    def progress(value):
        reading["progress"] = value
        write_json(out / "reading-progress.json", dict(status=reading["status"], progress=value,
                   counts=counts, reconstruction_work=work,
                   wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu))

    try:
        progress(dict(kind="bindings"))
        batch = json.loads((out / "summary.json").read_text())
        reading["summary_identity"] = file_identity(out / "summary.json")
        reading["launch_sha"] = batch["launch_sha"]
        _require(batch["object"] == OBJECT and batch["state"] == "COMPLETE"
                 and batch["scientific_execution"] is True and batch["input_manifest_sha256"] == INPUT_MANIFEST_SHA256
                 and batch["input_root"] == str(INPUT_ROOT), "complete selected B07 worker")
        equal_tree(batch["protocol"], FROZEN.to_dict(), "frozen B07 protocol")
        equal_tree(batch["expected"], FROZEN.expected(), "frozen B07 expectations")
        equal_tree(batch["sources"], source_identities(repo), "published source identities")
        config = json.loads((out / "config.json").read_text())
        for key, value in config.items():
            equal_tree(batch[key], value, "config/summary " + key)
        manifest = verify_inputs()
        parent_state, parent, fixed = load_actors(repo, manifest=manifest)
        dataset = load_dataset(manifest)
        target_record = batch["targets"]
        target_path = checked_path(out, target_record["artifact"]["path"], target_record["artifact"])
        targets = _load_raw(target_path)
        required = {"parent_logits", "parent_probabilities", "T", "H", "statistics"}
        _require(set(targets) == required, "saved target schema")
        for key, values in targets.items():
            shape = (81920, len(STAT_NAMES) if key == "statistics" else 27)
            dtype = np.float32 if key == "parent_logits" else np.float64
            _require(values.shape == shape and values.dtype == dtype and np.isfinite(values).all(), "saved target " + key)
            _require(array_digest(values) == target_record["array_sha256"][key], "saved target array hash " + key)
            if key in ("parent_probabilities", "T", "H"):
                _require(np.all(values >= 0) and np.all(np.abs(values.sum(axis=1) - 1.) <= 5e-14), "saved target mass")
        _require(target_record["rows"] == 81920 and target_record["source_data_sha256"] == array_digest(*dataset),
                 "target-to-original-dataset binding")
        scores, _ = check_archive(manifest, dataset, targets, parent, counts, progress,
                                  work=work["archive"], record=reading["archive"])
        expected_mapping = [{k: r[k] for k in ("id", "first", "stop", "phase")} for r in reading["archive"]["records"]]
        equal_tree(target_record["mapping"], expected_mapping, "complete target row order")
        reading["target_statistics"] = statistics_summary(targets["statistics"])
        equal_tree(target_record["statistics"], reading["target_statistics"], "target activation summary")
        progress(dict(kind="training_records"))
        learned, reading["fits"] = check_fits(out, batch, manifest, parent_state, dataset, targets)
        actors = dict(P0=parent, Bstar0=parent, F0=fixed, T=learned["T"], H=learned["H"], Tdirect=parent, Hdirect=parent)
        identities = {arm: state_digest(actor.state_dict()) for arm, actor in actors.items()}
        _require(batch["initial_state_sha256"] == identities["P0"]
                 and batch["fixed_F0_state_sha256"] == identities["F0"], "fixed asset identities")
        expected_order = [(arm, world, tape) for wi, world in enumerate(FROZEN.worlds)
                          for arm, tape in FROZEN.episode_order(wi)]
        _require([(r["arm"], r["world"], r["tape"]) for r in batch["rows"]] == expected_order, "complete cyclic final order")
        final_rows, final_checks = [], []
        reading["final"].update(files=0, records=final_checks)
        layouts = {}
        for row in batch["rows"]:
            progress(dict(kind="final", id=row["id"], completed_files=counts["saved_files"]))
            _require(row["policy_sha256"] == identities.get(row["arm"]), "actual deployed tensor binding")
            path = checked_path(out, row["raw"]["path"], row["raw"])
            raw = _load_raw(path)
            native = check_native(raw, row, FROZEN)
            policy = check_final_policy(raw, row, actors.get(row["arm"]), counts, work["final"])
            pair = layouts.setdefault(row["world"], row["shared_layout_sha256"])
            _require(pair == row["shared_layout_sha256"], "paired layouts across all programs/tapes")
            counts["saved_files"] += 1
            counts["saved_ticks"] += native["saved_ticks"]
            counts["decision_rows"] += native["decision_rows"]
            final_rows.append({**row, **policy["metrics"]})
            final_checks.append(dict(id=row["id"], **native, max_score_abs_error=policy["max_score_abs_error"],
                                     max_logit_abs_error=policy["max_logit_abs_error"]))
            reading["final"]["files"] = len(final_rows)
        final_c, final_helper = work["final"]["C_costs"], work["final"]["helper_costs"]
        reading["final"].update(C_costs=final_c, helper_costs=final_helper)
        equal_tree(batch["costs"], costs(final_rows, batch["actual"]), "all worker cached costs")
        validate_counts(batch["actual"], batch["costs"])
        reading["comparisons"] = comparisons(final_rows, FROZEN)
        equal_tree(batch["comparisons"], reading["comparisons"], "all native paired-world reductions")
        for arm in FITS:
            progress(dict(kind="endpoint", arm=arm))
            reading["endpoints"].append(endpoint_reading(out, arm, learned[arm], dataset, targets, scores, counts))
        for arm, actor in actors.items():
            _require(state_digest(actor.state_dict()) == identities[arm], "reader frozen tensor preservation")
        expected = FROZEN.expected()
        for actual, key in (("saved_files", "reader_files"), ("saved_ticks", "reader_saved_ticks"),
                            ("C_requests", "reader_C_requests"), ("helper_requests", "reader_helper_requests"),
                            ("actor_rows", "reader_actor_rows"), ("endpoint_rows", "reader_endpoint_rows"),
                            ("archive_target_rows", "target_rows")):
            _require(counts[actual] == expected[key], "full reader exposure " + actual)
        _require(counts["decision_rows"] == 296960 and counts["actor_forward_calls"] == counts["actor_rows"]
                 and counts["native_steps"] == counts["optimizer_steps"] == 0, "reader complete non-native scope")
        c_total = sum_counts((reading["archive"]["C_costs"], final_c))
        h_total = sum_counts((reading["archive"]["helper_costs"], final_helper))
        reading["costs"] = dict(C=c_total, helper=h_total, neural_rows=counts["actor_rows"],
                                controller_power_links=sum(c_total.get(k, 0) + h_total.get(k, 0) for k in
                                    ("candidate_links", "setup_links", "helper_setup_links", "helper_extreme_links")),
                                native_steps=0, optimizer_steps=0,
                                scope="Every requested row checked; actual C/helper miss work retained; every paid actor row forwarded once")
        verify_inputs()
        reading.update(status="VERIFIED", finish_utc=datetime.now(timezone.utc).isoformat())
        progress(dict(kind="complete"))
    except BaseException:
        reading.update(status="FAILED", failure=traceback.format_exc(),
                       interrupted_call_work_may_be_unmeasured=True, finish_utc=datetime.now(timezone.utc).isoformat())
        raise
    finally:
        c = sum_counts(stage.get("C_costs", {}) for stage in work.values())
        helper = sum_counts(stage.get("helper_costs", {}) for stage in work.values())
        reading["actual_reconstruction_costs"] = dict(C=c, helper=helper, neural_rows=counts["actor_rows"],
            controller_power_links=sum(c.get(k, 0) + helper.get(k, 0) for k in
                ("candidate_links", "setup_links", "helper_setup_links", "helper_extreme_links")),
            scope="Completed work prefixes, including interrupted scopes, folded once by each replay finally block")
        reading.update(reader_wall_seconds=time.perf_counter() - wall, reader_cpu_seconds=time.process_time() - cpu,
                       reader_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                       reader_timing_scope="reader entry through full bindings/native/archive/laws/fits/endpoints; final write additional")
        write_json(out / "reading.json", reading)
    return reading
