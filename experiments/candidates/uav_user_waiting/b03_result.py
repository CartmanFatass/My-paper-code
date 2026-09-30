"""Extract compact B03 evidence from the two complete, pinned saved records.

No native steps, physical/actor/value queries, or optimization. Full records stay
at their original canonical node paths; the extractor never copies raw data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time


SOURCE = "a045bc9b4e3ba9ef211474293c4bc43ad8b16b08"
SUMMARY_SHA = "f7b8a56a94c6c07a97071527ae43df6b0c1324f93e90c02815eb9a0ea100b525"
READING_SHA = "448ecaf87e604642c19cdcbe70dc989757f5e74eedf65abc1d73c26bb2281722"
ROOT = "/home/wu/projects/HMASD/runs/uav_user_waiting"


def load_pinned(path, digest):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("changed complete B03 input")
    return json.loads(data), len(data)


def terminal(path, source):
    value = json.loads(Path(path).read_text())
    assert value["record_consistency"]["state"] == "consistent"
    assert value["sha"] == source
    assert value["execution"]["state"] == "exited"
    assert value["execution"]["exit_code"] == 0
    assert value["execution"]["exit_witness"]["state"] == "valid"
    return value


def extract(summary_path, reading_path, worker_status, reader_status):
    wall, cpu = time.perf_counter(), time.process_time()
    s, summary_bytes = load_pinned(summary_path, SUMMARY_SHA)
    r, reading_bytes = load_pinned(reading_path, READING_SHA)
    assert s["status"] == "COMPLETE" and r["status"] == "VERIFIED_COMPLETE"
    assert s["launch_sha"] == r["launch_sha"] == SOURCE
    assert r["summary"]["sha256"] == SUMMARY_SHA
    assert r["paired"] == s["paired"]
    assert r["verified_artifacts"] == s["artifacts"]
    assert len(r["rows"]) == 512
    assert sum(x["verified_steps"] for x in r["rows"]) == 131072
    expected = {(a, seed) for a in ("M", "S", "G0", "LR", "LN")
                for seed in range(29424000, 29424064)}
    assert {(x["arm"], x["seed"]) for x in s["evaluation_rows"]} == expected
    assert len(s["evaluation_rows"]) == 320
    assert all(x["status"] == "BITWISE_REPLAYED" for x in r["fits"].values())
    verification_rows = []
    for row in r["rows"]:
        compact = {k: v for k, v in row.items()
                   if k not in ("settled_burden_errors", "continuation_slots")}
        anchors = row["settled_burden_errors"]
        compact["settled_burden_anchors"] = len(anchors)
        compact["anchors_with_any_burden_difference"] = sum(
            x["differing_users"] > 0 for x in anchors)
        compact["max_anchor_burden_abs_error"] = max(
            (x["max_absolute_error"] for x in anchors), default=0)
        verification_rows.append(compact)
    calibration = {arm: {k: v for k, v in row.items() if not isinstance(v, list)}
                   | {"queries": len(row["target"]),
                      "target_mean": sum(row["target"]) / len(row["target"])}
                   for arm, row in r["fresh_m_calibration"].items()}
    all_rows = s["acquisition_rows"] + s["evaluation_rows"]
    # Retain each scientific endpoint and diagnostic scalar; interval lists are
    # recoverable in the bound full summary and canonical native arrays.
    compact_rows = [{k: v for k, v in row.items()
                     if not isinstance(v, (list, dict)) or k in
                     ("raw", "value_range", "controller_counts", "decision_counts")}
                    for row in all_rows]
    per_user_keys = ("arm", "seed", "per_user_mean_age", "worst_users",
                     "per_user_gaps", "per_window_coverage")
    per_user = [{k: row[k] for k in per_user_keys} for row in s["evaluation_rows"]]
    worker_cpu = s["resources"]["process_user_seconds"] + s["resources"]["process_system_seconds"]
    reader_cpu = r["resources"]["process_user_seconds"] + r["resources"]["process_system_seconds"]
    result = dict(
        object=s["object"], status=r["status"], launch_sha=SOURCE,
        summary=dict(node="wsl_4070", path=f"{ROOT}/b03_value_a01/summary.json",
                     bytes=summary_bytes, sha256=SUMMARY_SHA),
        full_reading=dict(node="wsl_4070", path=f"{ROOT}/b03_value_read_a01/reading.json",
                          bytes=reading_bytes, sha256=READING_SHA),
        retention="One canonical node copy of full records, native raw, training data, models and fit traces; old M remains by canonical reference.",
        counts=s["counts"], fixed_policy_evaluation_counts=s["fixed_policy_evaluation_counts"],
        exposure=dict(new_episodes=512, new_native_steps=131072, acquisition_episodes=192,
                      evaluation_episodes=320, scientific_fits=2, optimizer_updates=4096,
                      reused_episodes=64, reused_previously_paid_steps=16384,
                      correctness_native_steps=40, correctness_scientific_fits=0),
        training=s["training"], fits=s["fits"], evaluation_parameter_sha256=s["evaluation_parameter_sha256"],
        verification=dict(status=r["status"], counts=r["counts"], training=r["training"],
                          fits=r["fits"], reader_c_calls=r["reader_c_calls"],
                          physics_scope=r["physics_scope"], raw_files=len(r["verified_artifacts"]),
                          raw_bytes=sum(x["bytes"] for x in r["verified_artifacts"])),
        verification_rows=verification_rows, fresh_m_calibration=calibration,
        calibration_scope=r["calibration_scope"], worker_resources=s["resources"],
        reader_resources=r["resources"],
        measured_cost=dict(worker_lifetime_cpu_seconds=worker_cpu,
                           reader_lifetime_cpu_seconds=reader_cpu,
                           worker_plus_reader_cpu_seconds=worker_cpu + reader_cpu,
                           worker_plus_reader_cpu_hours=(worker_cpu + reader_cpu) / 3600,
                           scope="Excludes separately recorded fixture, scientific/engineering review and unmetered support. Reader numerical replay is verification, not independent scientific fits."),
        native_worker_terminal=terminal(worker_status, SOURCE),
        native_reader_terminal=terminal(reader_status, r["admission"]["sha"]),
        paired=s["paired"], episode_rows=compact_rows, per_user=per_user,
        artifacts=s["artifacts"],
        analysis_scope="Complete fixed panel conditional on one shared acquisition/initialization realization; every world vector and adverse endpoint retained. Calibration is actual held-out M suffixes only.",
        extraction_resources=dict(wall_seconds=time.perf_counter() - wall,
                                  cpu_seconds=time.process_time() - cpu,
                                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                  native_steps=0, model_queries=0, optimizer_updates=0),
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("summary", "reading", "worker-status", "reader-status", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    value = extract(args.summary, args.reading, args.worker_status, args.reader_status)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, separators=(",", ":"), allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
