"""Read the three fixed B20 pair artifacts without constructing a learner or environment."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
from typing import Any, Mapping

import numpy as np

if __package__:
    from .bindings import (
        BLOCKS, EVALUATION_ORDER, OBJECT_ID, PRODUCTION_SPEC_VALUES,
        SCHEDULES, SOURCE_RELATIVE_PATHS, WORLD_SEED_BASES,
    )
else:
    # Direct-file CLI avoids the parent candidate package's scientific imports.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from bindings import (
        BLOCKS, EVALUATION_ORDER, OBJECT_ID, PRODUCTION_SPEC_VALUES,
        SCHEDULES, SOURCE_RELATIVE_PATHS, WORLD_SEED_BASES,
    )


T975_DF2 = 4.302652729696142
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
QUANTITIES = ("J", "C", "Q", "P", "E", "S", "U", "height")
INITIAL_EQUAL_FIELDS = (
    "parameter_normalizer_digest", "tensor_manifest", "normalizers",
    "optimizer_ownership", "optimizer_state_digest", "post_initialization_rng_digest",
    "initial_buffer", "runtime_digest", "actual_config",
)
REQUIRED_INITIAL_CONFIG = {
    "count_arm": "LOCAL1", "algorithm": "mappo", "n_agents": 6, "n_uavs": 6,
    "n_users": 50, "num_envs": 16, "rollout_length": 500, "episode_length": 500,
    "k": 10, "state_dim": 133, "obs_dim": 104, "use_valuenorm": True,
    "use_obsnorm": False, "use_statenorm": False,
    "lambda_l": .05, "lambda_l_initial": .05, "lambda_l_final": .05,
    "disable_high_level_training": True, "disable_discriminator_training": True,
    "ppo_epochs": 15, "sequence_batch_size": 32, "coordinator_batch_size": 1280,
    "hidden_size": 256, "n_heads": 8, "n_encoder_layers": 2, "n_decoder_layers": 2,
    "action_space_type": "continuous", "policy_interruption_mode": "off",
    "use_central_snapshot_in_flat_actor": False,
}


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(f"B20 reducer: {detail}")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"expected JSON object at {path}")
    return value


def _sha256(path: Path, limit: int | None = None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        remaining = limit
        while remaining is None or remaining > 0:
            block = stream.read(1024 * 1024 if remaining is None else min(1024 * 1024, remaining))
            if not block:
                break
            digest.update(block)
            if remaining is not None:
                remaining -= len(block)
        _require(remaining is None or remaining == 0, f"short artifact: {path}")
    return digest.hexdigest()


def _artifact(path: Path, identity: Mapping[str, Any], *, prefix: bool = False) -> None:
    size = identity.get("bytes")
    _require(type(size) is int and size >= 0, f"invalid byte count: {path}")
    actual_size = path.stat().st_size
    _require(actual_size >= size if prefix else actual_size == size, f"byte count mismatch: {path}")
    _require(_sha256(path, size if prefix else None) == identity.get("sha256"),
             f"SHA256 mismatch: {path}")


def _source_hashes() -> dict[str, str]:
    return {relative: _sha256(REPOSITORY_ROOT / relative) for relative in SOURCE_RELATIVE_PATHS}


def _finite_numbers(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _finite_numbers(item, f"{label}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _finite_numbers(item, f"{label}[{index}]")
    elif isinstance(value, float):
        _require(math.isfinite(value), f"nonfinite value at {label}")


def _numbers(values: Any, label: str) -> np.ndarray:
    _require(isinstance(values, list) and len(values) == 32, f"wrong 32-world array: {label}")
    _require(all(type(value) in (int, float) for value in values), f"nonnumeric array: {label}")
    result = np.asarray(values, dtype=np.float64)
    _require(bool(np.isfinite(result).all()), f"nonfinite array: {label}")
    return result


def _quantities(panel: Mapping[str, Any], label: str, n: int) -> dict[str, np.ndarray]:
    components = panel["component_means"]
    service = panel["service_arrays"]
    values = {
        "J": panel["J"], "C": components["coverage_reward"],
        "Q": components["quality_reward"], "P": components["energy_penalty"],
        "E": service["E_eligible_users_per_step"],
        "S": service["S_served_users_per_step"],
        "U": service["U_eligible_unserved_users_per_step"],
        "height": panel["uav_height_means_per_world"],
    }
    result = {key: _numbers(value, f"{label}.{key}") for key, value in values.items()}
    total = _numbers(components["total_reward"], f"{label}.total_reward")
    returns = _numbers(panel["scalar_returns"], f"{label}.scalar_returns")
    _require(bool(np.allclose(result["J"], total, rtol=1e-6, atol=1e-7)),
             f"native total identity mismatch: {label}")
    _require(bool(np.allclose(result["J"], .7 * result["C"] + .3 * result["Q"] - result["P"],
                              rtol=1e-6, atol=1e-7)), f"native components mismatch: {label}")
    _require(bool(np.allclose(result["J"], n * returns / 500, rtol=1e-6, atol=1e-7)),
             f"scalar J/N mismatch: {label}")
    _require(bool(np.allclose(result["S"], 50 * result["C"], rtol=1e-6, atol=1e-7)),
             f"served-user identity mismatch: {label}")
    _require(bool(np.allclose(result["U"], result["E"] - result["S"], rtol=1e-6, atol=1e-7)),
             f"unserved-user identity mismatch: {label}")
    return result


def _stats(values: np.ndarray, worlds: list[int]) -> dict[str, Any]:
    minimum, maximum = int(np.argmin(values)), int(np.argmax(values))
    return {
        "per_world": values.tolist(), "mean": float(values.mean()),
        "median": float(np.median(values)),
        "minimum": {"value": float(values[minimum]), "world_seed": worlds[minimum]},
        "maximum": {"value": float(values[maximum]), "world_seed": worlds[maximum]},
        "signs": {"positive": int((values > 0).sum()), "zero": int((values == 0).sum()),
                  "negative": int((values < 0).sum())},
    }


def _check_panel(arm_dir: Path, row: dict[str, Any], arm: str, stage: int,
                 n: int) -> dict[str, np.ndarray]:
    label = f"{arm} stage{stage} N{n}"
    _require(row.get("status") == "complete" and row.get("arm") == arm, f"incomplete {label}")
    _require(row.get("policy_stage") == stage and row.get("after_rollout") == stage and
             row.get("test_n") == n, f"wrong endpoint: {label}")
    worlds = list(range(WORLD_SEED_BASES[n], WORLD_SEED_BASES[n] + 32))
    _require(row.get("world_seeds") == worlds and row.get("runtime_seed") == WORLD_SEED_BASES[n] + 51,
             f"wrong fixed panel: {label}")
    _require(row.get("steps") == 16_000 and row.get("episodes") == 32 and
             row.get("resets") == 32 and row.get("policy_step_calls") == 500,
             f"wrong native evaluation counts: {label}")
    _require(row.get("training_storage_calls") == 0 and
             not any(row.get("optimizer_calls", {}).values()) and
             row.get("frozen_weights_and_normalizers") is True,
             f"evaluation changed training state: {label}")
    _require(row.get("parameter_normalizer_digest_before") ==
             row.get("parameter_normalizer_digest_after") and
             row.get("normalizers_before") == row.get("normalizers_after") and
             row.get("post_transition_semantics") is True,
             f"evaluation isolation/native semantics missing: {label}")
    panel_path = arm_dir / f"panel_stage{stage:02d}_n{n}.json"
    _require(_read(panel_path) == row, f"panel JSON differs from arm summary: {label}")
    trace = row["trace"]
    expected_trace = f"raw/trace_stage{stage:02d}_n{n}.npz"
    _require(trace.get("relative_to_arm") == expected_trace, f"wrong raw trace locator: {label}")
    _artifact(arm_dir / expected_trace, trace)
    physical = row["initial_world_identity"]
    _require(set(physical) == {"states", "observations", "uav_positions", "user_positions"},
             f"missing physical reset identities: {label}")
    _finite_numbers(row, label)
    return _quantities(row, label, n)


def _expected_counts(arm: str) -> dict[str, int]:
    stages = 2 if arm == "F" else 1
    schedule = SCHEDULES[arm]
    return {
        "fits": 1, "training_team_steps": 360_000, "stored_team_steps": 360_000,
        "training_uav_steps": 16 * 500 * sum(schedule), "training_episodes": 720,
        "updates": 45, "training_policy_step_calls": 22_500,
        "panels": stages * 3, "evaluation_team_steps": stages * 48_000,
        "evaluation_uav_steps": stages * 16_000 * sum(EVALUATION_ORDER),
        "evaluation_episodes": stages * 96, "evaluation_resets": stages * 96,
        "evaluation_policy_step_calls": stages * 1_500,
        "evaluation_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }


def _check_arm(arm_dir: Path, block: int, arm: str,
               sources: Mapping[str, str]) -> tuple[dict[str, Any], dict[str, Any],
                                                       dict[tuple[int, int], dict[str, np.ndarray]],
                                                       dict[int, dict[str, np.ndarray]]]:
    summary = _read(arm_dir / "summary.json")
    binding = BLOCKS[block]
    _require(summary.get("status") == "complete" and summary.get("block") == block and
             summary.get("arm") == arm and summary.get("tag") == binding.tag and
             summary.get("seed") == binding.seed, f"wrong or incomplete {arm} in block {block}")
    _require(summary.get("spec") == PRODUCTION_SPEC_VALUES and
             summary.get("schedule") == list(SCHEDULES[arm]), f"technical/substituted {arm} fit")
    expected = _expected_counts(arm)
    _require(summary.get("counts") == expected and summary.get("expected_counts") == expected,
             f"wrong measured counts for {arm} block {block}")
    _require(summary.get("source_hashes_before") == sources and
             summary.get("source_hashes_after") == sources and
             summary.get("source_hashes_unchanged") is True,
             f"source mismatch in {arm} block {block}")
    configuration = _read(arm_dir / "config.json")
    _require(configuration.get("object_id") == OBJECT_ID and
             configuration.get("tag") == binding.tag and
             configuration.get("block") == block and
             configuration.get("arm") == arm and
             configuration.get("seed") == binding.seed and
             configuration.get("spec") == PRODUCTION_SPEC_VALUES and
             configuration.get("schedule") == list(SCHEDULES[arm]) and
             configuration.get("world_seed_bases") ==
             {str(n): base for n, base in WORLD_SEED_BASES.items()} and
             configuration.get("training_world_seed_formula") ==
             f"{binding.training_world_base} + 100 * rollout + lane",
             f"wrong config binding: {arm} block {block}")
    config = configuration["config"]
    _require(summary.get("initial_config") == config and config.get("seed") == binding.seed and
             all(config.get(key) == value for key, value in REQUIRED_INITIAL_CONFIG.items()),
             f"wrong learner/input contract: {arm} block {block}")
    _require(summary.get("final_config", {}).get("n_agents") == SCHEDULES[arm][-1],
             f"wrong final roster: {arm} block {block}")
    raw_init = summary["initialization"]["raw"]
    _require(raw_init.get("path") == "raw/initialization.json", f"wrong initialization locator: {arm}")
    _artifact(arm_dir / raw_init["path"], raw_init)
    initialization = _read(arm_dir / raw_init["path"])
    _finite_numbers(initialization, f"{arm} block {block} initialization")
    _require(summary["initialization"]["parameter_normalizer_digest"] ==
             initialization["parameter_normalizer_digest"], f"initial digest mismatch: {arm}")
    _require(initialization.get("actual_config") == config,
             f"initial manifest/config mismatch: {arm} block {block}")
    stream = summary["training_stream"]
    _require(stream.get("path") == "raw/training.jsonl" and stream.get("completed_rows") == 45,
             f"incomplete training stream: {arm}")
    training_path = arm_dir / stream["path"]
    _artifact(training_path, stream)
    lines = training_path.read_text(encoding="utf-8").splitlines()
    _require(len(lines) == 45 and len(summary.get("rollouts", [])) == 45,
             f"wrong completed row count: {arm}")
    actor_calls = critic_calls = 0
    for index, (line, compact, n) in enumerate(zip(lines, summary["rollouts"], SCHEDULES[arm]), start=1):
        row = json.loads(line)
        _require(row.get("rollout") == compact.get("rollout") == index and
                 row.get("n") == compact.get("n") == n, f"wrong training row {arm} r{index}")
        expected_calls = {4: 1_500, 6: 2_250, 8: 3_000}[n]
        delta = row["optimizer_delta"]
        _require(delta.get("discoverer_actor") == expected_calls and
                 delta.get("discoverer_critic") == expected_calls and
                 row["sampler"]["recurrent_minibatches"] == expected_calls,
                 f"PPO optimizer/sampler mismatch {arm} r{index}")
        actor_calls += delta["discoverer_actor"]
        critic_calls += delta["discoverer_critic"]
    _require(actor_calls == critic_calls == 101_250, f"wrong optimizer totals: {arm}")
    optimizers = summary.get("optimizer_calls", {})
    _require(set(optimizers) == {"coordinator", "discoverer_actor", "discoverer_critic",
                                "team_discriminator", "individual_discriminator"} and
             optimizers["discoverer_actor"] == 101_250 and
             optimizers["discoverer_critic"] == 101_250 and
             all(optimizers[name] == 0 for name in
                 ("coordinator", "team_discriminator", "individual_discriminator")),
             f"arm optimizer counts disagree: {arm}")
    resets = summary.get("training_reset_scenes")
    _require(isinstance(resets, list) and len(resets) == 45, f"missing reset scenes: {arm}")
    n6_resets = {}
    for index, (identity, n) in enumerate(zip(resets, SCHEDULES[arm]), start=1):
        relative = f"raw/training_reset_r{index:02d}_n{n}.npz"
        _require(identity.get("path") == relative and identity.get("rollout") == index and
                 identity.get("n") == n, f"wrong reset locator {arm} r{index}")
        path = arm_dir / relative
        _artifact(path, identity)
        with np.load(path, allow_pickle=False) as scene:
            _require(int(scene["rollout"]) == index and int(scene["n"]) == n and
                     scene["lane_world_seeds"].tolist() == [
                         binding.training_world_base + 100 * index + lane for lane in range(16)
                     ], f"wrong reset seed/content {arm} r{index}")
            _require(scene["states"].shape[0] == 16 and
                     scene["observations"].shape[:2] == (16, n) and
                     scene["uav_positions"].shape[:2] == (16, n) and
                     scene["user_positions"].shape[:2] == (16, 50) and
                     all(not np.issubdtype(scene[key].dtype, np.floating) or
                         bool(np.isfinite(scene[key]).all()) for key in scene.files),
                     f"invalid reset arrays {arm} r{index}")
            if n == 6:
                n6_resets[index] = {key: scene[key].copy() for key in
                                    ("states", "observations", "uav_positions", "user_positions")}
    expected_panels = [(stage, n) for stage in ((0, 45) if arm == "F" else (45,))
                       for n in EVALUATION_ORDER]
    panels = summary.get("panels")
    _require(isinstance(panels, list) and
             [(row.get("policy_stage"), row.get("test_n")) for row in panels] == expected_panels,
             f"wrong actual panel set: {arm}")
    quantities = {(stage, n): _check_panel(arm_dir, row, arm, stage, n)
                  for row, (stage, n) in zip(panels, expected_panels)}
    _require(summary.get("stage_isolation", {}).keys() ==
             {str(stage) for stage in ((0, 45) if arm == "F" else (45,))},
             f"missing isolation record: {arm}")
    _require(all(value for stage in summary["stage_isolation"].values()
                 for key, value in stage.items() if key.endswith("_preserved")),
             f"evaluation isolation failed: {arm}")
    _require(summary.get("checkpoints") and
             {row.get("relative_to_arm") for row in summary["checkpoints"]} ==
             {"raw/checkpoint_00.pt", "raw/checkpoint_45.pt"},
             f"wrong initial/final checkpoints: {arm}")
    for identity in summary["checkpoints"]:
        _artifact(arm_dir / identity["relative_to_arm"], identity)
    return summary, initialization, quantities, n6_resets


def _block_reading(block: int, out: Path, sources: Mapping[str, str]) -> dict[str, Any]:
    binding = BLOCKS[block]
    _require(out.name == binding.tag, f"wrong block {block} output tag")
    batch = _read(out / "summary.json")
    _require(batch.get("status") == "complete" and batch.get("production_contract") is True and
             batch.get("object_id") == OBJECT_ID and batch.get("block") == block and
             batch.get("tag") == binding.tag and batch.get("seed") == binding.seed and
             batch.get("training_world_base") == binding.training_world_base and
             batch.get("evaluation_world_bases") == {str(n): seed for n, seed in WORLD_SEED_BASES.items()},
             f"wrong/technical/incomplete block {block}")
    _require(batch.get("arm_order") == ["F", "M"] and set(batch.get("arms", {})) == {"F", "M"},
             f"wrong arm set in block {block}")
    _require(batch.get("source_hashes_before") == sources and
             batch.get("source_hashes_after") == sources and
             batch.get("source_hashes_unchanged") is True,
             f"source mismatch in block {block}")
    _require(isinstance(batch.get("launch_sha"), str) and
             re.fullmatch(r"[0-9a-f]{40}", batch["launch_sha"]) is not None,
             f"missing or invalid full launch SHA in block {block}")
    _require(batch.get("admission", {}).get("sha") == batch.get("launch_sha"),
             f"launch admission identity mismatch in block {block}")
    arms = {name: _check_arm(out / name, block, name, sources) for name in ("F", "M")}
    f_summary, f_init, f_q, f_n6 = arms["F"]
    m_summary, m_init, m_q, m_n6 = arms["M"]
    for name, (summary, _, _, _) in arms.items():
        _require(batch["arms"][name]["status"] == "complete" and
                 batch["arms"][name]["counts"] == summary["counts"] and
                 batch["arms"][name]["summary"] == f"{name}/summary.json" and
                 summary.get("launch_sha") == batch["launch_sha"] and
                 summary.get("admission") == batch["admission"],
                 f"arm/batch mismatch block {block} {name}")
    counts = {key: f_summary["counts"][key] + m_summary["counts"][key]
              for key in f_summary["counts"]}
    _require(batch.get("counts") == counts, f"batch counts mismatch block {block}")
    _require(all(f_init[key] == m_init[key] for key in INITIAL_EQUAL_FIELDS) and
             all(batch.get("initial_identity", {}).get(key + "_equal") is True
                 for key in INITIAL_EQUAL_FIELDS), f"F/M initial model/runtime/RNG mismatch block {block}")
    _require(f_summary["initial_config"] == m_summary["initial_config"],
             f"F/M learner config mismatch block {block}")
    _require(m_summary.get("common_stage0", {}).get("new_environment_steps") == 0 and
             m_summary["common_stage0"].get("reused_after_full_initial_identity") is True and
             m_summary["common_stage0"].get("trace_sha256") ==
             f_summary.get("initial_evaluation_trace_sha256") and
             batch["initial_identity"].get("common_stage0_reused_without_new_steps") is True,
             f"initial stage was rerun or unproven in block {block}")
    _require(batch.get("common_n6_training_world_identity", {}).get("all_equal") is True,
             f"N6 reset identity absent block {block}")
    for index in set(f_n6) & set(m_n6):
        _require(all(np.array_equal(f_n6[index][key], m_n6[index][key])
                     for key in f_n6[index]), f"N6 reset mismatch block {block} r{index}")
    _require(len(set(f_n6) & set(m_n6)) == 15, f"missing matched N6 resets block {block}")
    by_n = {}
    for n in EVALUATION_ORDER:
        f_initial_row = f_summary["panels"][EVALUATION_ORDER.index(n)]
        f_final_row = f_summary["panels"][len(EVALUATION_ORDER) + EVALUATION_ORDER.index(n)]
        m_final_row = m_summary["panels"][EVALUATION_ORDER.index(n)]
        _require(f_initial_row["initial_world_identity"] == f_final_row["initial_world_identity"] ==
                 m_final_row["initial_world_identity"], f"physical pairing mismatch block {block} N{n}")
        _require(m_summary["common_stage0"]["panel_paths"][EVALUATION_ORDER.index(n)] ==
                 f"../F/panel_stage00_n{n}.json", f"wrong shared stage0 reference block {block} N{n}")
        worlds = list(range(WORLD_SEED_BASES[n], WORLD_SEED_BASES[n] + 32))
        initial, final_f, final_m = f_q[(0, n)], f_q[(45, n)], m_q[(45, n)]
        by_n[str(n)] = {
            "world_seeds": worlds,
            "initial": {key: _stats(initial[key], worlds) for key in QUANTITIES},
            "final_F": {key: _stats(final_f[key], worlds) for key in QUANTITIES},
            "final_M": {key: _stats(final_m[key], worlds) for key in QUANTITIES},
            "F_own_learning": {key: _stats(final_f[key] - initial[key], worlds) for key in QUANTITIES},
            "M_own_learning": {key: _stats(final_m[key] - initial[key], worlds) for key in QUANTITIES},
            "M_minus_F": {key: _stats(final_m[key] - final_f[key], worlds) for key in QUANTITIES},
            "adverse_J_or_S_worlds": [
                {"world_seed": worlds[i], "delta_J": float(final_m["J"][i] - final_f["J"][i]),
                 "delta_S": float(final_m["S"][i] - final_f["S"][i])}
                for i in range(32) if final_m["J"][i] <= final_f["J"][i]
                or final_m["S"][i] <= final_f["S"][i]
            ],
            "quality_height_tradeoff_worlds": [
                {"world_seed": worlds[i], "delta_Q": float(final_m["Q"][i] - final_f["Q"][i]),
                 "delta_height": float(final_m["height"][i] - final_f["height"][i])}
                for i in range(32) if (final_m["Q"][i] - final_f["Q"][i]) *
                (final_m["height"][i] - final_f["height"][i]) > 0
            ],
        }
        recorded = batch.get("readings", {}).get("by_test_n", {}).get(str(n), {})
        for quantity in ("J", "S"):
            _require(recorded.get("final_M_minus_F", {}).get(quantity, {}).get("per_world") ==
                     by_n[str(n)]["M_minus_F"][quantity]["per_world"],
                     f"batch paired reading mismatch block {block} N{n} {quantity}")
    _finite_numbers(batch, f"block {block} batch")
    return {
        "block": block, "tag": binding.tag, "launch_sha": batch["launch_sha"],
        "source_hashes": dict(sources), "counts": counts,
        "learner_contract": {key: value for key, value in f_summary["initial_config"].items()
                             if key != "seed"},
        "arm_optimizer_calls": {name: arms[name][0]["optimizer_calls"] for name in ("F", "M")},
        "by_n": by_n, "inputs": {"summary": str(out / "summary.json"),
                              "F": str(out / "F/summary.json"), "M": str(out / "M/summary.json")},
    }


def reduce_blocks(block_outputs: Mapping[int, Path], out: Path) -> dict[str, Any]:
    """Validate exactly the fixed three production blocks, then write one result."""
    _require(set(block_outputs) == {1, 2, 3} and all(type(key) is int for key in block_outputs),
             "requires exactly blocks 1, 2, and 3")
    paths = {block: Path(block_outputs[block]).resolve() for block in BLOCKS}
    _require(len(set(paths.values())) == 3, "duplicate block output directory")
    out = Path(out)
    _require(not out.exists(), "reducer output already exists")
    sources = _source_hashes()
    blocks = {block: _block_reading(block, paths[block], sources) for block in BLOCKS}
    _require(len({blocks[block]["launch_sha"] for block in BLOCKS}) == 1,
             "fixed three-block batch has mixed launch SHA values")
    _require(all(blocks[block]["learner_contract"] == blocks[1]["learner_contract"]
                 for block in BLOCKS), "learner/input contract differs across blocks")
    primary = {}
    for n in (5, 7):
        for quantity in ("J", "S"):
            values = [blocks[block]["by_n"][str(n)]["M_minus_F"][quantity]["mean"]
                      for block in BLOCKS]
            mean = statistics.mean(values)
            sd = statistics.stdev(values)  # sample SD, ddof=1
            half_width = T975_DF2 * sd / math.sqrt(3)
            lower, upper = mean - half_width, mean + half_width
            primary[f"N{n}_{quantity}"] = {
                "block_effects": values, "mean": mean, "sd_ddof1": sd,
                "t975_df2": T975_DF2, "half_width": half_width,
                "lower": lower, "upper": upper,
                "interval": "two-sided 95% Student t, df=2, conditional fixed worlds",
                "reading": "supported" if lower > 0 else "adverse" if upper < 0 else "unresolved",
            }
    joint = all(row["lower"] > 0 for row in primary.values())
    totals = {key: sum(blocks[block]["counts"][key] for block in BLOCKS)
              for key in blocks[1]["counts"]}
    optimizer_names = ("coordinator", "discoverer_actor", "discoverer_critic",
                       "team_discriminator", "individual_discriminator")
    optimizer_totals = {
        name: sum(blocks[block]["arm_optimizer_calls"][arm].get(name, 0)
                  for block in BLOCKS for arm in ("F", "M"))
        for name in optimizer_names
    }
    _require(optimizer_totals["discoverer_actor"] == 607_500 and
             optimizer_totals["discoverer_critic"] == 607_500 and
             all(optimizer_totals[name] == 0 for name in optimizer_names
                 if name not in ("discoverer_actor", "discoverer_critic")),
             "aggregate optimizer exposure differs from fixed six-fit contract")
    result = {
        "schema": 1, "object_id": OBJECT_ID, "status": "complete",
        "block_order": [1, 2, 3], "launch_sha": blocks[1]["launch_sha"],
        "fixed_world_bases": {str(n): base for n, base in WORLD_SEED_BASES.items()},
        "source_hashes": sources, "training_block_unit_n": 3,
        "estimand": "mean paired M45-F45 over fresh training blocks, conditional on fixed evaluation worlds",
        "primary": primary, "joint_supported": joint,
        "joint_verdict": "supported" if joint else "claim_not_established",
        "model_limit": "nominal t intervals assume approximately iid normal block effects; n=3 cannot check this",
        "counts": totals, "optimizer_calls_total": optimizer_totals,
        "blocks": [blocks[block] for block in BLOCKS],
    }
    _finite_numbers(result, "reducer result")
    out.mkdir(parents=True, exist_ok=False)
    target = out / "summary.json"
    temporary = out / "summary.json.partial"
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(target)
    directory_fd = os.open(out, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for block in BLOCKS:
        parser.add_argument(f"--block{block}", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    reduce_blocks({block: getattr(args, f"block{block}") for block in BLOCKS}, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
