"""Reduce already-collected B04 bytes; no host, model, or new evaluation call."""
import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re


def frac(row):
    return Fraction(row["numerator"], row["denominator"])


def number(value):
    return {"numerator": value.numerator, "denominator": value.denominator,
            "float": float(value)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collected-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    exp = args.collected_root / "exp/opportunity_credit_b04_20260906"
    timing = args.collected_root / "test/opportunity_credit_b04_20260906"
    control = args.collected_root / "test/opportunity_credit_b04_control_20260906"
    raw = json.loads((exp / "raw/summary.json").read_text(encoding="utf-8"))
    engineering = json.loads((exp / "engineering/summary.json").read_text(encoding="utf-8"))
    updates = [json.loads(line) for line in (exp / "raw/updates.jsonl").read_text(encoding="utf-8").splitlines()]
    ids = [e for row in updates for e in row["episode_ids"]]
    assert ids == list(range(384)) and len(updates) == 48
    assert sum(len(row["losses"]) for row in updates) == 768
    assert updates[-1]["counters"] == raw["counters"]
    train_actions = Counter(action for row in updates for episode in row["actions"]
                            for action in episode["decision_actions"])
    assert dict(train_actions) == raw["training_action_counts"]
    assert [row["update"] for row in raw["evaluations"]] == [0, 48]
    assert [len(row["episodes"]) for row in raw["evaluations"]] == [32, 32]
    endpoint = raw["evaluations"][-1]["episodes"]
    rule = raw["context"]["REQUEST_ONLY"]
    rows, conditional = [], Counter()
    conditional_reward, conditional_rule_reward = Counter(), Counter()
    for e, (actual, reference) in enumerate(zip(endpoint, rule, strict=True)):
        assert actual["identity"] == reference["identity"]
        for episode in (actual, reference):
            assert len(episode["actions"]) == len(episode["contributions"]) == 24
            ledger = sum((frac(c["decision_reward"]) + frac(c["settlement_reward"])
                          for c in episode["contributions"]), Fraction())
            assert ledger == frac(episode["native_return"])
        for q, (chosen, public_rule) in enumerate(zip(actual["actions"], reference["actions"], strict=True)):
            key = ("request_active" if public_rule == "REFRESH" else "request_inactive", chosen)
            conditional[key] += 1
            a, b = actual["contributions"][q], reference["contributions"][q]
            conditional_reward[key] += frac(a["decision_reward"]) + frac(a["settlement_reward"])
            conditional_rule_reward[key] += frac(b["decision_reward"]) + frac(b["settlement_reward"])
        difference = frac(actual["native_return"]) - frac(reference["native_return"])
        rows.append({"episode_index": e, "identity": actual["identity"],
                     "raw_return": actual["native_return"],
                     "request_only_return": reference["native_return"],
                     "raw_minus_request_only": number(difference)})
    mean = sum((frac(row["raw_return"]) for row in rows), Fraction()) / len(rows)
    gap = sum((frac(row["raw_minus_request_only"]) for row in rows), Fraction()) / len(rows)
    assert mean == frac(raw["curve"][-1]["mean_native_return"])
    assert gap == frac(raw["request_only_comparison"]["mean_difference"])
    calls, files = [], []
    for name in ("engineering", "raw", "struct"):
        handle = f"cbsc-b04-{name}-20260906"
        admission_path = timing / f"{handle}-admission.json"
        time_path = timing / f"{handle}-time.txt"
        status_path = control / f"{handle}-status.txt"
        log_path = control / f"{handle}-logs.txt"
        command_path = control / f"{handle}-command.json"
        time_text = time_path.read_text(encoding="utf-8")
        calls.append({"handle": handle,
                      "wall_seconds": float(re.search(r"process_wall_seconds=([0-9.]+)", time_text)[1]),
                      "peak_rss_kib": int(re.search(r"peak_rss_kib=([0-9]+)", time_text)[1]),
                      "admission": json.loads(admission_path.read_text(encoding="utf-8")),
                      "terminal_status": json.loads(status_path.read_text(encoding="utf-8"))})
        files.extend((admission_path, time_path, status_path, log_path, command_path))
    files.extend(exp / name for name in (
        "engineering/summary.json", "engineering/struct/paired_summary.json",
        "raw/summary.json", "raw/updates.jsonl", "raw/update-0.pt", "raw/update-48.pt"))
    evidence = [{"path": str(path), "bytes": path.stat().st_size,
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in files]
    signs = Counter("positive" if frac(row["raw_minus_request_only"]) > 0 else
                    "negative" if frac(row["raw_minus_request_only"]) < 0 else "zero" for row in rows)
    result = {"object": raw["object"], "launch_sha": raw["launch_sha"],
              "analysis_exposure": "zero new host/model/evaluation calls; recorded-byte reduction only",
              "completed_formal_training_instances": 1, "completed_formal_pairs": 0,
              "seed": raw["seed"], "structured_minus_raw": None,
              "raw_initial_return": raw["curve"][0]["mean_native_return"],
              "raw_endpoint_return": number(mean), "raw_minus_request_only": number(gap),
              "raw_minus_initial": number(mean - frac(raw["curve"][0]["mean_native_return"])),
              "raw_minus_always_refresh": number(mean - frac(raw["context_means"]["ALWAYS_REFRESH"])),
              "context_means": raw["context_means"], "raw_rule_gap_sign_counts": dict(signs),
              "observed_public_request_by_action": [
                  {"public_condition": key[0], "raw_action": key[1], "count": count,
                   "raw_mean_native_contribution": number(conditional_reward[key] / count),
                   "rule_mean_native_contribution": number(conditional_rule_reward[key] / count)}
                  for key, count in sorted(conditional.items())],
              "raw_counters": raw["counters"], "raw_training_action_counts": dict(train_actions),
              "raw_endpoint_action_counts": raw["evaluations"][-1]["action_counts"],
              "evaluation_executions": raw["evaluation_executions"],
              "evaluation_transitions": raw["evaluation_transitions"],
              "raw_context_ledger_passes": sum(len(panel) for panel in raw["context"].values()),
              "raw_context_action_scores": sum(len(row["actions"]) for panel in raw["context"].values() for row in panel),
              "completed_logged_adam_steps_including_engineering": raw["counters"]["adam_steps"] + engineering["adam_steps"],
              "completed_logged_train_eval_transitions_including_engineering": raw["counters"]["train_transitions"] + raw["evaluation_transitions"] + engineering["transitions"],
              "raw_parameter_measurements": {key: raw[key] for key in (
                  "parameter_count", "initial_parameter_l2", "final_parameter_l2",
                  "parameter_movement_l2", "relative_parameter_movement", "changed_parameters")},
              "execution": raw["execution"], "engineering": engineering,
              "calls": calls, "formal_sum_wall_seconds": round(sum(row["wall_seconds"] for row in calls[1:]), 2),
              "all_sum_wall_seconds": round(sum(row["wall_seconds"] for row in calls), 2),
              "struct_collected_files": sorted(str(path.relative_to(exp / "struct"))
                                               for path in (exp / "struct").rglob("*") if path.is_file()),
              "per_episode_rule_comparison": rows, "source_artifacts": evidence}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "RECORDED_ANALYSIS.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (args.out / "ENDPOINT_RUNS.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("task", "seed", "arm", "score"))
        writer.writerow((raw["object"], raw["seed"], raw["arm"], float(mean)))
    print(json.dumps({key: result[key] for key in (
        "raw_initial_return", "raw_endpoint_return", "raw_minus_request_only",
        "raw_minus_always_refresh", "raw_rule_gap_sign_counts",
        "observed_public_request_by_action", "raw_counters", "struct_collected_files")}, indent=2))


if __name__ == "__main__":
    main()
