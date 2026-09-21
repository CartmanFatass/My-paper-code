"""Read the three completed B10 records. No model, environment or forward call."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import statistics

import numpy as np

from .storage import inspect_pair


MASTERS = (8971, 8972, 8973)
ARMS = ("R_CF", "R_FULL", "S_FULL", "G")
SOURCE = "07605eecde6bba632b86ac2e92862057ea6d9fe2"
OBJECT = "UCOPE_PAIRED_BRANCH_CREDIT_B10"
COMPARISONS = (("R_CF", "R_FULL"), ("R_CF", "G"), ("R_CF", "S_FULL"),
               ("S_FULL", "G"), ("R_FULL", "G"))


def _json(path):
    return json.loads(Path(path).read_text())


def _rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_file(path, identity):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    _require(path.stat().st_size == identity["bytes"] and digest.hexdigest() == identity["sha256"],
             f"artifact identity mismatch: {path}")


def panel_reading(path, *, horizon, worlds, ordinary):
    """Independent NumPy reward reduction and exact recorded-action-law checks."""
    with np.load(path, allow_pickle=False) as arrays:
        reward = arrays["reward"]
        eligible, keep = arrays["eligible"], arrays["keep"]
        commands, previous = arrays["commands"], arrays["previous"]
        context, probability = arrays["context"], arrays["keep_probability"]
        coins = arrays["gate_uniforms"].copy()
        _require(reward.shape == (worlds, horizon) and reward.dtype == np.float64,
                 "final reward panel shape/dtype mismatch")
        _require(eligible.shape == (worlds, horizon, 5) and eligible.dtype == bool
                 and keep.shape == eligible.shape and keep.dtype == bool, "final mask shape/dtype mismatch")
        _require(context.shape == (worlds, horizon, 5, 175), "final legal-context shape mismatch")
        _require(commands.shape == previous.shape == (worlds, horizon, 5, 3), "final command shape mismatch")
        _require(probability.shape == coins.shape == eligible.shape, "final probability/coin shape mismatch")
        _require(all(np.isfinite(value).all() for value in
                     (reward, commands, previous, context, probability, coins)), "nonfinite evaluation data")
        _require(not eligible[:, 0].any() and not previous[:, 0].any() and not (keep & ~eligible).any(),
                 "reset or eligibility law changed")
        _require(np.array_equal(previous[:, 1:], commands[:, :-1]), "previous command lost its actual history")
        _require(np.array_equal(context[..., 104:107], previous), "gate context uses a different prior command")
        _require(np.array_equal(commands, np.where(keep[..., None], previous, context[..., 107:110])),
                 "final commands do not implement recorded KEEP/END")
        _require(((probability >= 0) & (probability <= 1)).all(), "invalid gate probability")
        if ordinary:
            _require(not keep.any() and not eligible.any() and not coins.any(), "G acquired a gate intervention")
        else:
            _require(np.array_equal(eligible[:, 1:], ~keep[:, :-1]), "KEEP lost its forced-fresh successor")
            _require(np.array_equal(keep, eligible & (coins < probability)), "evaluation gate coins were not applied")
        values = probability[eligible].astype(np.float64)
        reading = {"J": (reward.sum(axis=1, dtype=np.float64) / horizon).tolist(),
            "eligible": int(eligible.sum()), "kept": int(keep.sum()),
            "copied_fraction_all_agent_ticks": float(keep.mean()),
            "keep_probability_mean": float(values.mean()) if values.size else None,
            "keep_probability_sd": float(values.std()) if values.size else None,
            "keep_probability_range": [float(values.min()), float(values.max())] if values.size else None}
    return reading, coins


def compare(left, right):
    _require(len(left) == len(right) and len(left) > 1, "paired world panels differ")
    values = [a - b for a, b in zip(left, right)]
    return {"mean": statistics.mean(values), "differences": values,
            "positive_worlds": sum(value > 0 for value in values),
            "negative_worlds": sum(value < 0 for value in values),
            "conditional_world_se": statistics.stdev(values) / len(values) ** .5}


def investment_reading(blocks):
    _require(len(blocks) == 3 and sorted(block["master"] for block in blocks) == list(MASTERS),
             "investment rule requires exactly the three declared blocks")
    readings = {}
    for left, right in COMPARISONS:
        name = left + "_minus_" + right
        values = [block["comparisons"][name]["mean"] for block in blocks]
        _require(all(np.isfinite(values)), "nonfinite block contrast")
        readings[name] = {"block_means": values, "three_block_mean": statistics.mean(values),
                          "passes_investment_rule": all(value > 0 for value in values)
                          and statistics.mean(values) >= .01}
    readings["retain_paired_over_rich_and_G"] = all(readings[name]["passes_investment_rule"] for name in
                                                  ("R_CF_minus_R_FULL", "R_CF_minus_G"))
    readings["prefer_paired_over_simple"] = readings["retain_paired_over_rich_and_G"] and readings[
        "R_CF_minus_S_FULL"]["passes_investment_rule"]
    readings["interpretation"] = "Investment criteria on selected foundations; worlds are nested, not independent fits."
    return readings


def read_block(root, master):
    root = Path(root).resolve()
    summary = _json(root / "summary.json")
    manifest, terminal = _json(root / "launch-manifest.json"), _json(root / "process-exit.json")
    _require(summary["status"] == "COMPLETE" and terminal["status"] == "exited" and terminal["exit_code"] == 0,
             "native result lacks a complete summary and successful terminal witness")
    _require(summary["object"] == OBJECT and summary["master"] == master and summary["launch_sha"] == SOURCE
             and manifest["sha"] == SOURCE, "producing object/master/source mismatch")
    _require(terminal["process_identity"] == manifest["runner_process"]["identity"], "terminal process identity mismatch")
    config = summary["configuration"]
    _require(config == {"master": master, "horizon": 256, "train_episodes": 2048,
                        "eval_episodes": 64, "pairs_per_round": 16, "fixture": False}, "declared exposure changed")
    _require(summary["foundation_unchanged"] and summary["foundation_optimizer_steps"] == 0
             and summary["foundation"]["foundation_master"] == master - 30
             and summary["foundation_final_digest"] == summary["foundation"]["actor_parameter_digest"],
             "foundation identity/immutability mismatch")
    expected_artifacts = {"source.json", "config.json", "admission.json", "episodes.jsonl", "pairs.jsonl",
        "updates.jsonl", "inherited_checkpoint.pt", "inherited_summary.json", "inherited_source.json"}
    expected_artifacts.update(arm + "_final.pt" for arm in ARMS[:-1])
    expected_artifacts.update(arm + "_evaluation.npz" for arm in ARMS)
    expected_artifacts.update(f"pairs/R_CF/{index:04d}.npz" for index in range(1024))
    _require(set(summary["artifacts"]) == expected_artifacts, "promised scientific artifacts are incomplete")
    _require(summary["fit_accounting"] == {"planned_new_gate_fits": 3, "planned_batch_fits": 9,
        "started_new_gate_fits": 3, "completed_new_gate_fits": 3, "new_foundation_fits": 0}, "fit accounting changed")
    _require(all(summary["arms"][arm]["train_complete"] for arm in ARMS[:-1]), "a fitted arm is incomplete")
    _require(summary["arms"]["R_CF"]["initial_gate_digest"] == summary["arms"]["R_FULL"]["initial_gate_digest"],
             "the rich gates did not share their declared initialization")
    for name, identity in summary["artifacts"].items():
        path = (root / name).resolve()
        _require(path.is_relative_to(root), "artifact escaped its run root")
        verify_file(path, identity)
    base = 100000 * master
    episodes = _rows(root / "episodes.jsonl")
    _require(len(episodes) == 6400, "missing or duplicated episode records")
    _require(all(row["phase"] == "train" for row in episodes[:6144])
             and all(row["phase"] == "eval" for row in episodes[6144:]), "evaluation occurred before all fits finished")
    for arm in ARMS:
        for phase in ("train", "eval"):
            rows = [row for row in episodes if row["arm"] == arm and row["phase"] == phase]
            expected = 64 if phase == "eval" else (0 if arm == "G" else 2048)
            _require(len(rows) == expected and [row["episode"] for row in rows] == list(range(expected)),
                     f"episode exposure/order mismatch: {arm}/{phase}")
            for index, row in enumerate(rows):
                offset = 30000 + index if phase == "eval" else 10000 + (index // 2 if arm == "R_CF" else index)
                _require(row["world_seed"] == base + offset and row["steps"] == 256 and row["master"] == master,
                         "episode world or horizon changed")
    pairs = _rows(root / "pairs.jsonl")
    _require(len(pairs) == 1024 and [row["pair"] for row in pairs] == list(range(1024)), "pair schedule incomplete")
    rng = np.random.default_rng(base + 81)
    ticks, agents = rng.integers(1, 256, size=1024), rng.integers(0, 5, size=1024)
    for index, row in enumerate(pairs):
        _require(row["arm"] == "R_CF" and row["tick"] == int(ticks[index]) and row["agent"] == int(agents[index])
                 and row["world_seed"] == base + 10000 + index and row["common_seed"] == base + 50000 + index
                 and row["focal_seed"] == base + 60000 + index, "pair address changed or resampled")
        _require(row["raw_path"] == f"pairs/R_CF/{index:04d}.npz"
                 and row["raw"] == summary["artifacts"][row["raw_path"]], "paired archive identity changed")
        _require(row["behavior_digest"] == pairs[16 * (index // 16)]["behavior_digest"], "policy changed within a pair round")
        raw = inspect_pair(root / row["raw_path"])
        _require(raw["eligible"] == row["eligible"] and raw["tick"] == row["tick"] and raw["agent"] == row["agent"],
                 "raw and indexed pair disagree")
        _require(np.allclose(raw["suffix_returns"], row["suffix_returns"], rtol=0, atol=1e-13), "raw credit reconstruction failed")
        _require(row["delta"] == row["suffix_returns"][0] - row["suffix_returns"][1], "recorded learning delta changed")
    updates = _rows(root / "updates.jsonl")
    _require(len(updates) == 2112, "missing or extra optimizer-round records")
    gate_calls = critic_calls = 0
    for arm in ARMS[:-1]:
        rows = [row for row in updates if row["arm"] == arm]
        expected_indices = list(range(16, 1025, 16)) if arm == "R_CF" else list(range(2, 2049, 2))
        key = "pairs_seen" if arm == "R_CF" else "episodes_seen"
        _require([row[key] for row in rows] == expected_indices, "optimizer round cadence changed")
        for row in rows:
            stats = row["statistics"]
            _require(len(stats) == (4 if arm == "R_CF" else 8), "optimizer epoch/minibatch exposure changed")
            gate_calls += len(stats) if arm == "R_CF" else sum(bool(item["gate_step"]) for item in stats)
            critic_calls += 0 if arm == "R_CF" else len(stats)
    counts = summary["counts"]
    _require(counts["train_team_steps"] == 1572864 and counts["eval_team_steps"] == 65536
             and counts["team_steps"] == counts["foundation_forward_calls"] == 1638400
             and counts["recurrent_agent_observations"] == 8192000, "native transition/forward exposure changed")
    _require(counts["gate_optimizer_steps"] == gate_calls and counts["critic_optimizer_steps"] == critic_calls
             and counts["optimizer_steps"] == gate_calls + critic_calls, "actual optimizer call counts disagree")
    _require(counts["completed_pairs"] == 1024 and counts["eligible_pairs"] == sum(row["eligible"] for row in pairs),
             "pair eligibility denominator changed")
    panels, shared_coins = {}, None
    for arm in ARMS:
        record = summary["arms"][arm]
        _require(record["eval_complete"] and all(record["evaluation_immutability"].values()), "evaluation mutated training")
        reading, coins = panel_reading(root / (arm + "_evaluation.npz"), horizon=256, worlds=64, ordinary=arm == "G")
        _require(np.allclose(reading["J"], summary["final_panel"]["world_scores"][arm], rtol=0, atol=1e-13),
                 "raw final rewards disagree with reported J")
        if arm != "G":
            _require(shared_coins is None or np.array_equal(coins, shared_coins), "final arms used different coin slots")
            shared_coins = coins
        panels[arm] = reading
    contrasts = {left + "_minus_" + right: compare(panels[left]["J"], panels[right]["J"]) for left, right in COMPARISONS}
    deltas = np.asarray([row["delta"] for row in pairs if row["eligible"]], dtype=np.float64)
    return {"master": master, "source": SOURCE, "root": str(root), "panels": panels,
        "comparisons": contrasts, "counts": counts, "fits": summary["fit_accounting"],
        "movement": {arm: summary["arms"][arm]["movement"] for arm in ARMS[:-1]},
        "pair_targets": {"scheduled": 1024, "eligible": int(deltas.size),
            "positive": int((deltas > 0).sum()), "negative": int((deltas < 0).sum()),
            "zero": int((deltas == 0).sum()), "mean": float(deltas.mean()), "sd": float(deltas.std()),
            "range": [float(deltas.min()), float(deltas.max())],
            "meaning": "Actual training targets under old behavior; not an oracle bound or deployment score."},
        "wall_seconds": summary["wall_seconds"], "cpu_seconds": summary["process_cpu_seconds"],
        "process_peak_rss_kib": summary["process_peak_rss_kib"],
        "accepted_epoch": datetime.fromisoformat(manifest["accepted_at"].replace("Z", "+00:00")).timestamp(),
        "finished_epoch": terminal["finished_at_epoch"],
        "artifact_bytes": sum(identity["bytes"] for identity in summary["artifacts"].values()),
        "verified_artifacts": len(summary["artifacts"])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    _require(not args.out.exists(), "readback output already exists")
    blocks = [read_block(args.runs / f"paired_branch_credit_b10_{master}", master) for master in MASTERS]
    result = {"object": OBJECT, "producing_source": SOURCE, "blocks": blocks,
              "investment": investment_reading(blocks), "new_fits": 0, "new_native_ticks": 0,
              "new_optimizer_steps": 0, "checkpoint_forward_calls": 0,
              "batch_elapsed_seconds": max(block["finished_epoch"] for block in blocks)
              - min(block["accepted_epoch"] for block in blocks)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"investment": result["investment"], "new_native_ticks": 0}, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
