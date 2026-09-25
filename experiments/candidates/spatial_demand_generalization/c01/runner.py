"""Isolated A2 block execution and offline C01 five-block reading."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import sys
from typing import Any, Mapping, Sequence
from uuid import uuid4

import numpy as np
import torch

from experiments.candidates.spatial_demand_generalization.a2 import runner as a2_reference


ROOT = Path(__file__).resolve().parents[4]
DIRECTION = "spatial_demand_generalization"
OBJECT_ID = "s1_spatial_coverage_c01"
BLOCKS = tuple(range(5))
FAMILIES = ("uniform", "cluster", "hotspot")
MODEL_SEED_BASE = 263000101
TRAINING_BASE = 264000000
CONSTRUCTOR_BASE = 269900000
EVALUATION_BASES = {"uniform": 265000000, "cluster": 265010000, "hotspot": 265020000}
T975_DF4 = 2.7764451051977987


def model_seed(block: int) -> int:
    if block not in BLOCKS:
        raise ValueError(f"C01 block must be one of {BLOCKS}")
    return MODEL_SEED_BASE + block


def tag_for(block: int) -> str:
    return f"s1_spatial_coverage_c01_b{block}_s{model_seed(block)}"


def load_block_runner(block: int, *, technical_constructor_base: int | None = None):
    """Load one private A2 function namespace; never alter the published A2 module."""
    seed = model_seed(block)
    name = f"_hmasd_c01_a2_{block}_{uuid4().hex}"
    path = Path(a2_reference.__file__).resolve()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the published A2 runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)

    module.OBJECT_ID = OBJECT_ID
    module.TAG = tag_for(block)
    module.SEED = seed
    module.CONFIG_SEED = (
        CONSTRUCTOR_BASE + 1000 * block if technical_constructor_base is None
        else int(technical_constructor_base)
    )
    module.TRAINING_WORLD_BASE = TRAINING_BASE + 100000 * block
    module.WORLD_SEED_BASES = dict(EVALUATION_BASES)
    module.ARMS = {arm: module.Arm(arm, seed=seed) for arm in ("U", "M")}

    inherited_paths = tuple(path for path in module._source_paths()
                            if path.name != "run_spatial_demand_generalization_a2.py")
    c01_paths = (
        Path(__file__).resolve(), Path(__file__).resolve().with_name("__init__.py"),
        ROOT / "scripts/run_spatial_demand_generalization_c01.py",
    )
    module._source_paths = lambda: inherited_paths + c01_paths

    original_write_json = module.write_json

    def write_c01_json(path: Path, value: Any) -> None:
        if path.name in ("summary.json", "config.json") and isinstance(value, dict):
            value.update(
                direction=DIRECTION, object_id=OBJECT_ID, tag=module.TAG,
                block=block, model_seed=int(value.get("seed", seed)),
                planned_model_seed=seed,
            )
        original_write_json(path, value)

    module.write_json = write_c01_json

    def save_c01_checkpoint(agent: Any, out: Path, rollout: int, config: Any,
                            launch_sha: str, arm: Any) -> dict[str, Any]:
        path = out / f"checkpoint_{rollout:02d}.pt"
        payload = {
            "schema": 1, "direction": DIRECTION, "object_id": OBJECT_ID,
            "tag": module.TAG, "block": block, "model_seed": int(config.seed),
            "planned_model_seed": seed, "arm": arm.key,
            "launch_sha": launch_sha, "rollout": rollout,
            "config": module.config_dict(config),
            "modules": {name: item.state_dict() for name, item in module.model_modules(agent).items()},
            "normalizers": {
                name: module.jsonable(vars(norm)) if (norm := getattr(agent, name, None)) is not None
                else None for name in module.NORMALIZERS
            },
            "usage": "Evaluation weights; no training resume contract or optimizer restoration.",
        }
        partial = path.with_suffix(".pt.partial")
        with partial.open("wb") as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        partial.replace(path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return {
            "path": path.name, "sha256": module.b15.file_sha256(path),
            "bytes": path.stat().st_size, "direction": DIRECTION,
            "object_id": OBJECT_ID, "tag": module.TAG, "block": block,
            "model_seed": int(config.seed), "arm": arm.key, "rollout": rollout,
        }

    module.save_a2_checkpoint = save_c01_checkpoint
    return module


def run_block(out: Path, launch_sha: str, admission: Mapping[str, Any], block: int,
              *, spec: Any = None, technical_seed: int | None = None,
              technical_constructor_base: int | None = None,
              schedules: Mapping[str, tuple[int, ...]] | None = None,
              command_start: float | None = None) -> int:
    """Run exactly one fixed pair; reduced technical specs are callable only in Python."""
    seed = model_seed(block)
    out = Path(out)
    if out.name != tag_for(block):
        raise ValueError("C01 output basename disagrees with its block")
    if launch_sha != admission.get("sha"):
        raise ValueError("C01 launch SHA disagrees with admission")
    if spec is None and (technical_seed is not None or technical_constructor_base is not None or
                         schedules is not None):
        raise ValueError("C01 production protocol does not accept technical overrides")
    if spec is not None and (technical_seed is None or technical_constructor_base is None or
                             schedules is None):
        raise ValueError("C01 technical run needs complete separate seed and schedule bindings")
    if technical_seed == seed:
        raise ValueError("C01 technical model seed equals its fixed production seed")
    module = load_block_runner(block, technical_constructor_base=technical_constructor_base)
    selected_spec = module.PRODUCTION_SPEC if spec is None else spec
    selected_schedule = module.SCHEDULES if schedules is None else schedules
    if spec is not None and selected_spec == module.PRODUCTION_SPEC:
        raise ValueError("C01 technical spec must differ from production")
    return module.run_batch(
        out, launch_sha, admission, selected_spec,
        command_start=command_start, schedules=selected_schedule,
        technical_seed=technical_seed,
    )


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"C01 expected JSON object: {path}")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _quantities(row: Mapping[str, Any]) -> dict[str, np.ndarray]:
    return {
        "J": np.asarray(row["J"], dtype=np.float64),
        "C": np.asarray(row["component_means"]["coverage_reward"], dtype=np.float64),
        "Q": np.asarray(row["component_means"]["quality_reward"], dtype=np.float64),
        "P": np.asarray(row["component_means"]["energy_penalty"], dtype=np.float64),
        "E": np.asarray(row["service_arrays"]["E_eligible_users_per_step"], dtype=np.float64),
        "S": np.asarray(row["service_arrays"]["S_served_users_per_step"], dtype=np.float64),
        "U": np.asarray(row["service_arrays"]["U_eligible_unserved_users_per_step"], dtype=np.float64),
        "height": np.asarray(row["uav_height_means_per_world"], dtype=np.float64),
    }


def _interval(values: Sequence[float]) -> dict[str, Any]:
    _require(len(values) == 5 and all(math.isfinite(value) for value in values),
             "C01 interval requires five finite block means")
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    half = T975_DF4 * sd / math.sqrt(5)
    return {
        "block_values": list(values), "mean": mean, "sample_sd": sd,
        "minimum": min(values), "maximum": max(values),
        "signs": {"positive": sum(value > 0 for value in values),
                  "zero": sum(value == 0 for value in values),
                  "negative": sum(value < 0 for value in values)},
        "t_critical_975_df4": T975_DF4, "df": 4, "half_width": half,
        "lower_95": mean - half, "upper_95": mean + half,
    }


def aggregate_five_blocks(summary_paths: Sequence[Path]) -> dict[str, Any]:
    """Read exactly five complete fixed blocks, using paired block means as the units."""
    _require(len(summary_paths) == 5, "C01 requires exactly five block summaries")
    blocks: dict[int, dict[str, Any]] = {}
    reference_sources = reference_sha = reference_protocol = reference_physical = None
    for input_path in summary_paths:
        path = Path(input_path)
        root = path.parent
        batch = _load_json(path)
        block = batch.get("block")
        _require(type(block) is int and block in BLOCKS and block not in blocks,
                 "C01 missing, duplicate or invalid block identity")
        seed, tag = model_seed(block), tag_for(block)
        _require(path.name == "summary.json" and root.name == tag,
                 "C01 summary path/tag mismatch")
        _require(batch.get("status") == "complete" and batch.get("direction") == DIRECTION and
                 batch.get("object_id") == OBJECT_ID and batch.get("tag") == tag and
                 batch.get("seed") == seed and batch.get("model_seed") == seed and
                 batch.get("planned_model_seed") == seed and batch.get("arm_order") == ["U", "M"],
                 "C01 incomplete or mismatched batch identity")
        expected_arm_counts = {
            arm: a2_reference._expected_arm_counts(a2_reference.SCHEDULES[arm],
                                                    a2_reference.PRODUCTION_SPEC,
                                                    common_stage0=(arm == "M"))
            for arm in ("U", "M")
        }
        expected_batch_counts = {
            key: sum(expected_arm_counts[arm][key] for arm in ("U", "M"))
            for key in expected_arm_counts["U"]
        }
        _require(batch.get("counts") == expected_batch_counts, "C01 batch exposure mismatch")
        _require(batch.get("source_hashes_unchanged") is True and
                 batch.get("source_hashes_before") == batch.get("source_hashes_after"),
                 "C01 source changed within block")
        sources = batch["source_hashes_before"]
        _require(isinstance(sources, dict) and
                 all(name in sources for name in (
                     "experiments/candidates/spatial_demand_generalization/a2/runner.py",
                     "experiments/candidates/spatial_demand_generalization/a2/adapter.py",
                     "experiments/candidates/spatial_demand_generalization/c01/runner.py",
                     "scripts/run_spatial_demand_generalization_c01.py")),
                 "C01 source manifest is incomplete")
        sha = batch.get("launch_sha")
        _require(isinstance(sha, str) and len(sha) > 0, "C01 launch SHA missing")
        if reference_sources is None:
            reference_sources, reference_sha = sources, sha
        _require(sources == reference_sources and sha == reference_sha,
                 "C01 blocks have different source or launch SHA")

        arms = {}
        configs = {}
        for arm in ("U", "M"):
            arm_ref = batch.get("arms", {}).get(arm, {})
            _require(arm_ref.get("status") == "complete" and arm_ref.get("fit_started") is True and
                     arm_ref.get("summary") == f"{arm}/summary.json", "C01 arm is incomplete")
            row = _load_json(root / arm / "summary.json")
            config = _load_json(root / arm / "config.json")
            _require(all(row.get(key) == expected and config.get(key) == expected for key, expected in
                         {"direction": DIRECTION, "object_id": OBJECT_ID, "tag": tag,
                          "block": block, "seed": seed, "model_seed": seed,
                          "planned_model_seed": seed, "arm": arm}.items()),
                     "C01 arm/config identity mismatch")
            _require(row.get("status") == "complete" and row.get("fit_started") is True and
                     row.get("launch_sha") == sha and config.get("launch_sha") == sha and
                     row.get("source_hashes_unchanged") is True and
                     row.get("source_hashes_before") == sources and
                     row.get("source_hashes_after") == sources,
                     "C01 arm source or completion mismatch")
            expected_spec = a2_reference.jsonable(vars(a2_reference.PRODUCTION_SPEC))
            _require(row.get("spec") == expected_spec and
                     row.get("schedule") == [6] * 45 and config.get("spec") == expected_spec and
                     config.get("schedule") == [6] * 45 and
                     config.get("evaluation_order") == list(FAMILIES) and
                     config.get("world_seed_bases") == EVALUATION_BASES and
                     config.get("config_constructor_seed") == CONSTRUCTOR_BASE + 1000 * block and
                     config.get("training_world_seed_formula") ==
                     f"{TRAINING_BASE + 100000 * block} + 1000 * (rollout - 1) + lane",
                     "C01 production protocol differs")
            arm_counts = row.get("counts", {})
            _require(arm_counts == expected_arm_counts[arm] and
                     arm_ref.get("counts") == arm_counts and
                     row.get("optimizer_calls", {}).get("discoverer_actor") == 101250 and
                     row.get("optimizer_calls", {}).get("discoverer_critic") == 101250,
                     "C01 arm exposure/optimizer mismatch")
            _require(len(row.get("checkpoints", [])) == 2 and
                     [item.get("rollout") for item in row["checkpoints"]] == [0, 45] and
                     all(item.get("direction") == DIRECTION and item.get("object_id") == OBJECT_ID and
                         item.get("tag") == tag and item.get("block") == block and
                         item.get("model_seed") == seed and item.get("arm") == arm
                         for item in row["checkpoints"]), "C01 checkpoint identity mismatch")
            arms[arm], configs[arm] = row, config
        required_initial = (
            "parameter_normalizer_digest_equal", "tensor_manifest_equal", "normalizers_equal",
            "optimizer_ownership_equal", "optimizer_state_digest_equal",
            "post_initialization_rng_digest_equal", "initial_buffer_equal",
            "runtime_digest_equal", "actual_config_equal",
        )
        _require(all(batch.get("initial_identity", {}).get(key) is True for key in required_initial) and
                 batch.get("initial_identity", {}).get(
                         "common_stage0_reused_without_new_steps") is True and
                 batch.get("common_training_world_identity", {}).get("all_equal") is True,
                 "C01 within-block initialization/training-world identity failed")
        config_u = dict(configs["U"]["config"])
        config_m = dict(configs["M"]["config"])
        _require(config_u == config_m and config_u.get("seed") == seed,
                 "C01 U/M learner configs differ")
        normalized = dict(config_u)
        normalized.pop("seed", None)
        if reference_protocol is None:
            reference_protocol = normalized
        _require(normalized == reference_protocol, "C01 learner protocol differs across blocks")

        panels = {}
        for arm, stages in (("U", (0, 45)), ("M", (45,))):
            expected_keys = {(stage, family) for stage in stages for family in FAMILIES}
            rows = arms[arm].get("panels", [])
            _require(len(rows) == len(expected_keys) and
                     {(row.get("policy_stage"), row.get("family")) for row in rows} == expected_keys,
                     "C01 panels are missing or duplicated")
            for row in rows:
                family = row["family"]
                worlds = list(range(EVALUATION_BASES[family], EVALUATION_BASES[family] + 32))
                _require(row.get("status") == "complete" and row.get("world_seeds") == worlds and
                         row.get("test_n") == 6 and row.get("steps") == 16000 and
                         row.get("episodes") == 32 and row.get("trace", {}).get("sha256") and
                         row.get("initial_world_identity"), "C01 panel is incomplete or changed")
                quantities = _quantities(row)
                _require(all(value.shape == (32,) and np.isfinite(value).all()
                             for value in quantities.values()), "C01 nonfinite/incomplete panel quantities")
                panels[(arm, row["policy_stage"], family)] = row
        physical = {}
        for family in FAMILIES:
            identities = [panels[key]["initial_world_identity"] for key in
                          (("U", 0, family), ("U", 45, family), ("M", 45, family))]
            _require(identities[0] == identities[1] == identities[2],
                     "C01 within-block physical evaluation mismatch")
            physical[family] = identities[0]
        if reference_physical is None:
            reference_physical = physical
        _require(physical == reference_physical, "C01 cross-block physical evaluation mismatch")
        blocks[block] = {"path": path, "batch": batch, "arms": arms, "panels": panels}

    _require(set(blocks) == set(BLOCKS), "C01 requires blocks zero through four")
    by_family: dict[str, Any] = {}
    for family in FAMILIES:
        readings = []
        for block in BLOCKS:
            item = blocks[block]
            rows = [item["panels"][key] for key in
                    (("U", 0, family), ("U", 45, family), ("M", 45, family))]
            q0, qu, qm = (_quantities(row) for row in rows)
            delta = {name: qm[name] - qu[name] for name in q0}
            readings.append({
                "block": block, "summary": str(item["path"]),
                "arm_summaries": {arm: str(item["path"].parent / arm / "summary.json")
                                  for arm in ("U", "M")},
                "world_seeds": rows[0]["world_seeds"],
                "mean_M_minus_U": {name: float(value.mean()) for name, value in delta.items()},
                "mean_U_minus_initial": {name: float((qu[name] - q0[name]).mean()) for name in q0},
                "mean_M_minus_initial": {name: float((qm[name] - q0[name]).mean()) for name in q0},
                "adverse_J_or_S_worlds": [
                    {"world_seed": rows[0]["world_seeds"][index],
                     "delta_J": float(delta["J"][index]), "delta_S": float(delta["S"][index])}
                    for index in range(32) if delta["J"][index] <= 0 or delta["S"][index] <= 0
                ],
                "per_world_M_minus_U": {name: value.tolist() for name, value in delta.items()},
            })
        by_family[family] = {
            "blocks": readings,
            "between_block_M_minus_U": {
                name: _interval([row["mean_M_minus_U"][name] for row in readings])
                for name in ("J", "S", "C", "Q", "P", "E", "U", "height")
            },
        }
    primary = {name: by_family["hotspot"]["between_block_M_minus_U"][name]
               for name in ("J", "S")}
    return {
        "schema": 1, "direction": DIRECTION, "object_id": OBJECT_ID,
        "status": "complete_five_block_conditional_reading",
        "source_hashes": reference_sources, "launch_sha": reference_sha,
        "units": "five paired training blocks; world panel fixed and conditional",
        "interval": "two marginal two-sided t95 intervals, df=4; intersection rule",
        "by_family": by_family, "primary_hotspot": primary,
        "primary_joint_lower_bounds_positive": all(row["lower_95"] > 0 for row in primary.values()),
        "decision_limit": "conditional program mean on the fixed hotspot panel; no mechanism, next-fit or adoption claim",
    }
