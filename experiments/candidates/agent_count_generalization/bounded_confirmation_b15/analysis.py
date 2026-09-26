"""Prewritten B15 saved-output analysis; never constructs a policy or environment.

This reducer checks saved identities and arithmetic. Scientific acceptance also
requires the DM's independent native trace/checkpoint and process-exit reading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


OBJECT_ID = "s1_bounded_confirmation_b15"
T975_DF2 = 4.302652729749464
WORLD_BASES = {8: 1_945_800, 6: 1_945_600}
BLOCKS = ((1, 994101, 2994100), (2, 994102, 2994200), (3, 994103, 2994300))
SPEC = {
    "train_n": 6, "test_ns": [8, 6], "horizon": 500, "train_lanes": 16,
    "eval_lanes": 32, "rollouts": 45, "panels": [0, 45], "hidden_size": 256,
    "n_heads": 8, "n_layers": 2, "ppo_epochs": 15, "sequence_batch_size": 32,
    "coordinator_batch_size": 1280, "torch_threads": 4,
}
COUNTS = {
    "fits": 1, "training_team_steps": 360000, "stored_team_steps": 360000,
    "training_uav_steps": 2160000, "training_episodes": 720, "terminal_resets": 720,
    "updates": 45, "training_policy_step_calls": 22500, "panels": 4,
    "evaluation_team_steps": 64000, "evaluation_uav_steps": 448000,
    "evaluation_episodes": 128, "evaluation_resets": 128,
    "evaluation_policy_step_calls": 2000, "evaluation_storage_calls": 0,
    "evaluation_optimizer_calls": 0,
}
ISOLATION = (
    "parameter_normalizer_digest", "runtime_digest", "global_rng_digest",
    "sampler_rng_digest", "optimizer_state_digest", "training_mode",
    "buffer_content_digest", "buffer_env_lengths", "buffer_last_t_per_env",
    "training_environment_digest",
)


class InvalidBatch(ValueError):
    """An incomplete or mismatched batch cannot establish the fixed claim."""


def require(condition, message):
    if not condition:
        raise InvalidBatch(message)


def finite_vector(values, size, name):
    require(isinstance(values, list) and len(values) == size, f"{name}: wrong length")
    require(all(isinstance(v, (int, float)) and not isinstance(v, bool)
                and math.isfinite(v) for v in values), f"{name}: nonfinite/nonnumeric")
    return [float(v) for v in values]


def close_vectors(a, b, name):
    require(all(math.isclose(x, y, rel_tol=1e-6, abs_tol=1e-7)
                for x, y in zip(a, b)), f"{name}: native arithmetic mismatch")


def interval(values, threshold):
    """Three training-block means, ddof=1; no world-based uncertainty."""
    values = finite_vector(values, 3, "training block differences")
    mean, sd = statistics.fmean(values), statistics.stdev(values)
    half_width = T975_DF2 * sd / math.sqrt(3)
    lower, upper = mean - half_width, mean + half_width
    return {
        "block_differences": values, "n_training_blocks": 3, "df": 2,
        "mean": mean, "sample_sd": sd, "lower": lower, "upper": upper,
        "confidence": .95, "threshold": threshold,
        "strict_lower_exceeds_threshold": lower > threshold,
        "reading": ("supported_component" if lower > threshold else
                    "against_component" if upper < threshold else "inconclusive"),
    }


def describe(values, worlds):
    lo, hi = min(range(len(values)), key=values.__getitem__), max(
        range(len(values)), key=values.__getitem__)
    return {
        "mean": statistics.fmean(values), "median": statistics.median(values),
        "positive": sum(v > 0 for v in values), "negative": sum(v < 0 for v in values),
        "zero": sum(v == 0 for v in values),
        "minimum": {"world_seed": worlds[lo], "value": values[lo]},
        "maximum": {"world_seed": worlds[hi], "value": values[hi]},
    }


def quantities(panel):
    components, service = panel["component_means"], panel["service_arrays"]
    values = {"J": panel["J"], "C": components["coverage_reward"],
              "Q": components["quality_reward"], "P": components["energy_penalty"],
              "E": service["E_eligible_users_per_step"],
              "S": service["S_served_users_per_step"],
              "U": service["U_eligible_unserved_users_per_step"]}
    values = {k: finite_vector(v, 32, k) for k, v in values.items()}
    close_vectors(values["J"], [.7*c + .3*q - p for c, q, p in
                  zip(values["C"], values["Q"], values["P"])], "J components")
    close_vectors(values["J"], finite_vector(components["total_reward"], 32, "total_reward"),
                  "native total")
    returns = finite_vector(panel["scalar_returns"], 32, "scalar_returns")
    close_vectors(values["J"], [panel["test_n"]*r/500 for r in returns], "native units")
    close_vectors(values["S"], [50*c for c in values["C"]], "S=50C")
    close_vectors(values["U"], [e-s for e, s in zip(values["E"], values["S"])], "U=E-S")
    require(all(0 <= s <= e <= 50 for s, e in zip(values["S"], values["E"])),
            "service population range")
    return values


def validate_run(run, block, seed, train_base, arm, source_sha):
    key = f"b{block}_{arm.lower()}"
    tag = f"{OBJECT_ID}_{key}_s{seed}"
    require(run["object_id"] == OBJECT_ID and run["direction"] == "agent_count_generalization",
            f"{key}: wrong scientific object")
    require(run["cell"]["key"] == key and run["arm"] == arm and run["tag"] == tag
            and run["seed"] == seed, f"{key}: wrong cell identity")
    for name, value in {"arm": arm, "seed": seed, "tag": tag, "train_n": 6,
                        "law": "clip", "lambda_l": .05}.items():
        require(run["cell"][name] == value, f"{key}: wrong cell {name}")
    require(run["launch_sha"] == source_sha, f"{key}: source mismatch")
    require(run["status"] == "complete" and run["fit_started"] is True
            and run["failure"] is None, f"{key}: incomplete or failed fit")
    require(run["spec"] == SPEC, f"{key}: changed exposure/spec")
    for name, value in {"seed": seed, "count_arm": arm, "n_agents": 6, "n_uavs": 6,
                        "k": 10, "lambda_l": .05, "lambda_l_initial": .05,
                        "lambda_l_final": .05, "use_entropy_annealing": False,
                        "use_entropy_targets": False,
                        "use_central_snapshot_in_flat_actor": arm == "SET"}.items():
        require(run["config"][name] == value, f"{key}: actual config mismatch {name}")
    require(run["counts"] == COUNTS and run["expected_counts"] == COUNTS,
            f"{key}: incomplete work")
    require(run["training_world_seeds"] == list(range(train_base, train_base+16)),
            f"{key}: training world binding")
    require(run["initial_evaluation_enabled"] is True and run["evaluation_order"]
            == [{"stage": stage, "test_n": n} for stage in (0, 45) for n in (8, 6)],
            f"{key}: missing/reordered endpoints")
    require(run["source_hashes_unchanged"] is True and bool(run["source_hashes_before"])
            and run["source_hashes_before"] == run["source_hashes_after"], f"{key}: changed source")
    require([(x["rollout"], x["team_steps"]) for x in run["rollouts"]]
            == [(i, i*8000) for i in range(1, 46)], f"{key}: missing rollout")
    expected_optimizers = {"discoverer_actor": 101250, "discoverer_critic": 101250,
                          "coordinator": 675 if arm == "H6" else 0,
                          "team_discriminator": 675 if arm == "H6" else 0,
                          "individual_discriminator": 2700 if arm == "H6" else 0}
    require(run["optimizer_calls"] == expected_optimizers, f"{key}: optimizer exposure")
    for name, value in {"device": "cpu", "dtype": "float32", "torch_threads": 4}.items():
        require(run["runtime"][name] == value, f"{key}: runtime mismatch")
    require([p["path"] for p in run["checkpoints"]] == ["checkpoint_00.pt", "checkpoint_45.pt"],
            f"{key}: checkpoint identity")
    require(run["training_reset_trace"]["reset_calls_per_lane"] == 46,
            f"{key}: reset record incomplete")
    require(set(run["stage_isolation"]) == {"0", "45"}, f"{key}: isolation stages")
    for stage in ("0", "45"):
        iso = run["stage_isolation"][stage]
        require(iso["before"] == iso["after"]
                and all(iso[name+"_preserved"] is True for name in ISOLATION),
                f"{key}: evaluation affected training state")
    panels = run["panels"]
    require([(p["policy_stage"], p["test_n"]) for p in panels]
            == [(0, 8), (0, 6), (45, 8), (45, 6)], f"{key}: wrong/missing panels")
    for panel in panels:
        n, stage = panel["test_n"], panel["policy_stage"]
        require(panel["arm"] == arm and panel["cell_key"] == key
                and panel["after_rollout"] == stage
                and panel["prior_training_team_steps"] == stage*8000, f"{key}: panel identity")
        require(panel["world_seeds"] == list(range(WORLD_BASES[n], WORLD_BASES[n]+32))
                and panel["runtime_seed"] == WORLD_BASES[n]+51, f"{key}: panel worlds/RNG")
        require(panel["status"] == "complete" and panel["steps"] == 16000
                and panel["episodes"] == 32 and panel["resets"] == 32
                and panel["policy_step_calls"] == 500, f"{key}: panel incomplete")
        require(panel["training_storage_calls"] == 0 and not any(panel["optimizer_calls"].values())
                and panel["frozen_weights_and_normalizers"] is True
                and panel["runtime_evolved"] is True and panel["post_transition_semantics"] is True,
                f"{key}: panel policy/storage semantics")
        require(panel["parameter_normalizer_digest_before"] == panel["parameter_normalizer_digest_after"],
                f"{key}: panel changed learner")
        expected_digest = run["observed_initial_parameter_normalizer_digest"] if stage == 0 else run["final_parameter_normalizer_digest"]
        require(panel["parameter_normalizer_digest_before"] == expected_digest,
                f"{key}: evaluation used wrong checkpoint")
        require(panel["execution_law"] == "clip" and panel["n_users"] == 50
                and panel["max_connections_per_uav"] == 10, f"{key}: native task identity")
        quantities(panel)


def analyze_batch(runs, source_sha):
    """Return the fixed analysis or fail explicitly; never impute an incomplete cell."""
    try:
        require(len(runs) == 6, "exactly six completed fits are required")
        keyed = {run["cell"]["key"]: run for run in runs}
        expected_keys = {f"b{b}_{a}" for b, _, _ in BLOCKS for a in ("h6", "set")}
        require(set(keyed) == expected_keys and len(keyed) == len(runs), "missing/duplicate/wrong cell")
        common_source = runs[0]["source_hashes_before"]
        for block, seed, base in BLOCKS:
            for arm in ("H6", "SET"):
                run = keyed[f"b{block}_{arm.lower()}"]
                validate_run(run, block, seed, base, arm, source_sha)
                require(run["source_hashes_before"] == common_source, "cross-fit source differences")
            require(keyed[f"b{block}_h6"]["training_reset_trace"]["sha256"]
                    == keyed[f"b{block}_set"]["training_reset_trace"]["sha256"],
                    f"block {block}: exogenous training scenes differ")
        for arm in ("h6", "set"):
            require(len({keyed[f"b{b}_{arm}"]["observed_initial_parameter_normalizer_digest"]
                         for b, _, _ in BLOCKS}) == 3, f"{arm}: duplicated initial policy")
            require(len({keyed[f"b{b}_{arm}"]["training_reset_trace"]["sha256"]
                         for b, _, _ in BLOCKS}) == 3, f"{arm}: duplicated exogenous block")
        blocks = []
        for block, seed, _base in BLOCKS:
            by_n = {}
            for n in (8, 6):
                worlds = list(range(WORLD_BASES[n], WORLD_BASES[n]+32))
                values = {}
                for arm in ("h6", "set"):
                    values[arm] = {p["policy_stage"]: quantities(p)
                                   for p in keyed[f"b{block}_{arm}"]["panels"] if p["test_n"] == n}
                contrasts, absolutes = {}, {}
                for name in values["h6"][0]:
                    h0, h45 = values["h6"][0][name], values["h6"][45][name]
                    s0, s45 = values["set"][0][name], values["set"][45][name]
                    subtract = lambda a, b: [x-y for x, y in zip(a, b)]
                    d0, d45 = subtract(h0, s0), subtract(h45, s45)
                    ih, iset = subtract(h45, h0), subtract(s45, s0)
                    contrasts[name] = {label: {"values": vector, **describe(vector, worlds)}
                                       for label, vector in {"D0": d0, "D45": d45, "I_H": ih,
                                                             "I_SET": iset, "Delta": subtract(ih, iset)}.items()}
                    absolutes[name] = {label: {"values": vector, **describe(vector, worlds)}
                                       for label, vector in {"H0": h0, "H45": h45, "SET0": s0, "SET45": s45}.items()}
                adverse = [{"world_seed": world,
                            "final_differences": {name: contrasts[name]["D45"]["values"][i]
                                                  for name in contrasts}}
                           for i, world in enumerate(worlds)
                           if contrasts["J"]["D45"]["values"][i] < 0 or contrasts["S"]["D45"]["values"][i] < 0]
                by_n[str(n)] = {"world_seeds": worlds, "contrasts": contrasts,
                                 "absolute": absolutes, "all_final_J_or_service_loss_worlds": adverse}
            blocks.append({"block": block, "learning_seed": seed, "by_test_n": by_n})
        primary = {name: interval([b["by_test_n"]["8"]["contrasts"][name]["D45"]["mean"]
                                   for b in blocks], threshold) for name, threshold in (("J", 0), ("S", 1))}
        supported = all(v["strict_lower_exceeds_threshold"] for v in primary.values())
        return {"object_id": OBJECT_ID, "launch_sha": source_sha, "primary": primary,
                "joint_claim_supported_under_stated_model": supported,
                "reading": "supported_conditional_mean_claim" if supported else "joint_claim_not_established",
                "scope": "fixed W8 panel; independent approximately normal training-block differences; n=3",
                "limits": "not next-training win probability, world-population inference, skill causality or an adoption verdict",
                "blocks": blocks, "counts": {name: sum(r["counts"][name] for r in runs) for name in COUNTS},
                "resources": [{"cell": r["cell"]["key"], "command_wall_seconds": r.get("command_wall_seconds"),
                               "resources": r.get("resources", "resources_unmeasured")} for r in runs]}
    except (KeyError, TypeError, IndexError) as exc:
        raise InvalidBatch(f"missing or malformed required result field: {exc}") from exc


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_batch(root, source_sha):
    runs = []
    for block, seed, _base in BLOCKS:
        for arm in ("h6", "set"):
            directory = root / f"{OBJECT_ID}_b{block}_{arm}_s{seed}"
            run = json.loads((directory / "summary.json").read_text())
            records = [*run["checkpoints"], run["training_reset_trace"],
                       *(p["trace"] for p in run["panels"])]
            for record in records:
                relative = Path(record.get("native_relative_path", record["path"]))
                require(not relative.is_absolute() and len(relative.parts) == 1,
                        "artifact must be a run-local basename")
                path = directory / relative
                require(path.is_file() and path.stat().st_size == record["bytes"]
                        and file_digest(path) == record["sha256"], f"artifact integrity: {path}")
            for panel in run["panels"]:
                path = directory / f"panel_stage{panel['policy_stage']:02d}_n{panel['test_n']}.json"
                require(json.loads(path.read_text()) == panel, f"panel/summary mismatch: {path}")
            runs.append(run)
    return analyze_batch(runs, source_sha)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--out", type=Path, required=True, help="private analysis scratch, not a replacement runner output")
    args = parser.parse_args(argv)
    result = read_batch(args.runs_root, args.source_sha)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False)+"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
