"""Reduce original B01 bytes only; no target imports or new numerical invocation."""
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parent
PREFIX = "cbsc-public-stream-b01-20260912/"
SOURCE = "2717796fb4f38cdb7059cd9d17e1dfb2f19abd47"
OBJECT = "CBSC-OPPORTUNITY-CREDIT-PUBLIC-STREAM-B01"
SEED = 2026091231

def frac(record):
    value = Fraction(record["numerator"], record["denominator"])
    assert float(value) == record["float"]
    return value

def episode(row):
    assert len(row["contributions"]) == len(row["actions"]) == 24
    assert [r["opportunity_index"] for r in row["contributions"]] == list(range(24))
    assert [r["action"] for r in row["contributions"]] == row["actions"]
    assert sum(row["action_counts"].values()) == 24
    decision = sum((frac(r["decision_reward"]) for r in row["contributions"]), Fraction())
    settlement = sum((frac(r["settlement_reward"]) for r in row["contributions"]), Fraction())
    assert decision == frac(row["decision_sum"])
    assert settlement == frac(row["settlement_sum"])
    assert decision + settlement == frac(row["native_return"])
    return decision + settlement

archive = ROOT / "original-results.tar.gz"
assert hashlib.sha256(archive.read_bytes()).hexdigest() == "b56e5d6fe6453478ade30c03625be39ae0b0341dc765e95afdbf64fe45adad70"
with tarfile.open(archive) as tar:
    blobs = {m.name[len(PREFIX):]: tar.extractfile(m).read()
             for m in tar.getmembers() if m.isfile() and m.name.startswith(PREFIX)}
    manifest = {name: {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
                for name, value in blobs.items()}
    results = {arm: json.loads(blobs[arm + "/summary.json"]) for arm in ("raw", "struct")}
    pair = json.loads(blobs["struct/paired_summary.json"])
    out = {"object": OBJECT, "source": SOURCE, "seed": SEED, "independent_training_pairs": 1,
           "arms": {}, "context": {}, "all32": pair["differences"],
           "artifact_manifest": manifest}
    for arm, r in results.items():
        assert (r["object"], r["seed"], r["launch_sha"]) == (OBJECT, SEED, SOURCE)
        expected = {"rollout_updates": 48, "adam_steps": 768, "train_episodes": 384,
                    "train_transitions": 58368, "train_decisions": 9216}
        assert r["counters"] == expected
        assert r["parameter_count"] == 121349 and r["parameter_movement_l2"] > 0 and r["changed_parameters"] > 0
        assert r["execution"]["torch_threads"] == 1 and r["execution"]["dtype"] == "torch.float32"
        assert r["execution"]["device"] == "cpu"
        assert r["execution"]["python_version"].startswith("3.10.21")
        assert r["execution"]["torch_version"] == "2.7.0+cu118"
        updates = [json.loads(line) for line in blobs[arm + "/updates.jsonl"].splitlines()]
        assert [u["update"] for u in updates] == list(range(48))
        assert [e for u in updates for e in u["episode_ids"]] == list(range(384))
        for u in updates:
            assert len(u["losses"]) == 16
            assert u["counters"]["adam_steps"] == 16 * (u["update"] + 1)
            assert u["observation_shape"] == [8, 152, 168] and u["observation_dtype"] == "torch.float32"
        assert [e["update"] for e in r["evaluations"]] == [0, 48]
        for evaluation, curve in zip(r["evaluations"], r["curve"], strict=True):
            rows = evaluation["episodes"]
            assert len(rows) == 32
            assert [x["identity"]["episode_id"] for x in rows] == list(range(32))
            assert all(x["identity"]["split"] == "EVAL_STOCHASTIC" and x["identity"]["seed"] == SEED for x in rows)
            assert sum((episode(row) for row in rows), Fraction()) / 32 == frac(curve["mean_native_return"])
            assert evaluation["optimizer_before"] == evaluation["optimizer_after"]
        assert r["evaluation_executions"] == 64 and r["evaluation_transitions"] == 9728
        assert [c["update"] for c in r["checkpoints"]] == [0, 48]
        assert all(arm + "/" + c["path"] in blobs for c in r["checkpoints"])
        admission = json.loads(blobs[arm + "-admission.json"])
        assert admission["passed"] and admission["available_physical_bytes"] >= 4294967296
        assert admission["effective_available_bytes"] >= 4294967296
        timing = {k: float(v) for k, v in re.findall(r"([A-Z_]+)=([0-9.]+)", blobs[arm + ".time"].decode())}
        assert timing["EXIT"] == 0 and timing["ELAPSED_SECONDS"] <= 600
        out["arms"][arm] = {k: r[k] for k in ("arm", "configuration", "counters", "execution",
                            "parameter_count", "parameter_movement_l2", "relative_parameter_movement",
                            "changed_parameters", "training_action_counts", "context_means")}
        out["arms"][arm].update(initial=frac(r["curve"][0]["mean_native_return"]).__float__(),
            final=frac(r["curve"][-1]["mean_native_return"]).__float__(),
            final_actions=r["evaluations"][-1]["action_counts"],
            rule_gap=frac(r["request_only_comparison"]["mean_difference"]).__float__(),
            timing=timing, admission=admission,
            internal_readback_seconds=r["cost"]["wall_seconds_through_primary_readback"])
    raw, struct = results["raw"], results["struct"]
    for key in ("object", "seed", "rng_namespace", "profile", "configuration", "initialization_digest",
                "training_tape_digest", "evaluation_tape_digest", "updates", "eval_episodes", "counters",
                "minibatch_order_digest", "action_uniform_digest", "context"):
        assert raw[key] == struct[key], key
    assert pair["launch_shas"] == [SOURCE, SOURCE] and pair["independent_training_seeds"] == 1
    assert pair["endpoint_update"] == 48 and len(pair["differences"]) == 32
    differences = []
    for i, row in enumerate(pair["differences"]):
        left, right = raw["evaluations"][-1]["episodes"][i], struct["evaluations"][-1]["episodes"][i]
        assert row["identity"] == left["identity"] == right["identity"]
        assert frac(row["raw_return"]) == episode(left) and frac(row["struct_return"]) == episode(right)
        d = frac(row["struct_return"]) - frac(row["raw_return"])
        assert d == frac(row["difference"])
        differences.append(d)
    mean = sum(differences, Fraction()) / 32
    assert mean == frac(pair["mean_difference"])
    out["mean_difference"] = pair["mean_difference"]
    out["signs"] = {"positive": sum(d > 0 for d in differences),
                    "zero": sum(d == 0 for d in differences), "negative": sum(d < 0 for d in differences)}
    for label, rows in raw["context"].items():
        assert len(rows) == 32
        mean_rule = sum((episode(row) for row in rows), Fraction()) / 32
        assert mean_rule == frac(raw["context_means"][label])
        out["context"][label] = float(mean_rule)
    out["native_wall_sum_seconds"] = sum(a["timing"]["ELAPSED_SECONDS"] for a in out["arms"].values())
    out["native_aggregate_cpu_seconds"] = sum(a["timing"]["USER_SECONDS"] + a["timing"]["SYSTEM_SECONDS"] for a in out["arms"].values())
    assert out["native_wall_sum_seconds"] <= 1200
    out["checked"] = "source/identity/configuration/counters/48 records/768 losses per arm/full episode coverage/4 snapshots/2x32 evaluations/native ledger contributions/all32 paired differences/context/admission/inclusive time"
    (ROOT / "intake-summary.json").write_text(json.dumps(out, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (ROOT / "run-scores.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("task", "seed", "arm", "score"))
        for r in results.values():
            writer.writerow((OBJECT, SEED, r["arm"], r["curve"][-1]["mean_native_return"]["float"]))
    print(json.dumps({k:v for k,v in out.items() if k not in ("all32", "artifact_manifest")}, indent=2))
