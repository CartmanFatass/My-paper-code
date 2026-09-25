"""Evaluate six frozen B15/B16 policies on fixed old and fresh native panels."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import io
import json
from pathlib import Path
import resource
import sys
import time
import traceback
from types import MethodType
from typing import Any, Callable, Mapping

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.action_law_b02.probe import (
    _normalizer_record,
    _rng_digest,
    restore_checkpoint,
)
from experiments.candidates.agent_count_generalization.action_law_b03.runner import (
    map_training_actions,
    runtime_state_digest,
)
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.bounded_confirmation_b15 import runner as b15
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC as TRAINING_SPEC,
    DIRECTION,
    FitSpec,
    config_dict,
)
from experiments.candidates.agent_count_generalization.initial_policy_b08.runner import _finite_tree
from experiments.candidates.agent_count_generalization.local_ordinary_b16 import runner as b16
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.ordinary_control_b13 import runner as b13
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    NORMALIZERS,
    digest_agent,
    finite,
    jsonable,
    native_components,
    optimizer_counts,
    preserve_rng,
    seed_rng,
    write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11


OBJECT_ID = "s1_fresh_world_deployment_b17"
TAG = "s1_fresh_world_deployment_b17_final45"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
POLICY_STAGE = 45
PRIOR_TRAINING_TEAM_STEPS = 360_000
POLICY_ORDER = (
    "b1_local1", "b1_h6", "b2_local1", "b2_h6", "b3_local1", "b3_h6",
)
EVALUATION_ORDER = (8, 6, 4)
OLD_WORLD_SEED = 1_945_800
OLD_RUNTIME_SEED = 1_945_851
FRESH_WORLD_SEEDS = {8: 2_145_800, 6: 2_145_600, 4: 2_145_400}
FRESH_RUNTIME_SEEDS = {8: 2_145_851, 6: 2_145_651, 4: 2_145_451}
PROTOCOL_SEED = FRESH_RUNTIME_SEEDS[8]
ATOL = 1e-7
RTOL = 1e-6


@dataclass(frozen=True)
class EvalSpec:
    test_ns: tuple[int, ...] = EVALUATION_ORDER
    horizon: int = 500
    eval_lanes: int = 32
    torch_threads: int = 4


DEFAULT_SPEC = EvalSpec()


@dataclass(frozen=True)
class AssetSpec:
    key: str
    arm: str
    block: int
    seed: int
    tag: str
    source_sha: str
    object_id: str
    cell_key: str
    final_digest: str
    checkpoint_bytes: int
    hashes: tuple[tuple[str, str], ...]

    def hash_for(self, name: str) -> str:
        values = dict(self.hashes)
        if name not in values:
            raise ValueError(f"B17 has no binding for {self.key}:{name}")
        return values[name]


def _hashes(**values: str) -> tuple[tuple[str, str], ...]:
    return tuple(values.items())


ASSETS = (
    AssetSpec(
        "b1_local1", "LOCAL1", 1, 994101, "s1_local_ordinary_b16_b1_local1_s994101",
        "c95e57201dd7177fc8158b22a3379b56a5be8800", "s1_local_ordinary_b16", "b1_local1",
        "ce4f19c762e74fc1237a490c57275e58e79a62f77907e069f8d971baa2dec774", 19_694_959,
        _hashes(config="504f857cf7a99ea8adf71aacd7d8cef11975fcf013b4d59f5dc09267b0472a7e",
                summary="2aef84f2e8e26ca83ad526042d7350b8f103225c0ff171cfdf00eb0a9f6be720",
                checkpoint="98d42d3a1a537b6fc829d603c2dad429b3dcae2920c4e2731e6e0c956589c2cd",
                panel_n8="1fdb2d9d41a2c964c6dccc38463afcb9564b457ea0a3a82b4c576a5df554e43e",
                panel_n6="869ef23f67978ca14eec928b378c0fcc9980db2763e873e503ef7350f0bebfed",
                trace_n8="1625b8d838919096ca669349d59cfa043d47207ee28433778eb04d41fbc41954",
                manifest="55abd3ecd7539e9c1ae4bf1c26a2df966a35380ac9bb1b63724f1b1815f581f4"),
    ),
    AssetSpec(
        "b1_h6", "H6", 1, 994101, "s1_bounded_confirmation_b15_b1_h6_s994101",
        "e0a20add999ded53943f99df15f596822e6c13dc", "s1_bounded_confirmation_b15", "b1_h6",
        "47db194502608eede457a99129f056d5a11a39b6da20e33d242098f42ac57547", 23_073_626,
        _hashes(config="d73344704caa115e6aa1f63fd56b4e47949ab00df7b42dc95d8a117351913819",
                summary="40d61682b00daa60899dcc5242393f955122d9ee03075c59d12bc172e507633f",
                checkpoint="9d4e34c649e70056adf77c6cc8790e3034fe8c418d138a5a63bdbeedc24c179b",
                panel_n8="ee42dfdfd7ce71037f1d8d4783afe2dbd223bdcf3cddb015b756bb5d4fc748e1",
                panel_n6="ef750b892eed3d94302fde27353344194302f8609a6394da7dafca5e38e32b9c",
                trace_n8="c9fc3ce8257759e808ca4b776638e6867ac2989d5bf60fad0f3bc6cbefc44aa0",
                manifest="cb38f1092eeee420f7a4145a58834db72a8b7e316412ea2b4dc0dd56a364c358"),
    ),
    AssetSpec(
        "b2_local1", "LOCAL1", 2, 994102, "s1_local_ordinary_b16_b2_local1_s994102",
        "c95e57201dd7177fc8158b22a3379b56a5be8800", "s1_local_ordinary_b16", "b2_local1",
        "5ed8e41c1b4837ae547f19b279c002623f4460c5a9cdbe2f370f38d479744a1e", 19_694_959,
        _hashes(config="e9bef338ea9c0f0abc8a44f594fd91866503f1a3afa8239121021fb562d2e2d3",
                summary="f2a92baa064cb68eb6cd18394e797f2cec95dbfb7bdc1b13a425dbee78229a1d",
                checkpoint="b8540d79614673e5044b42c477b95c70d0adbf5fd7261e72e6f8f09728c6ab86",
                panel_n8="d42415734ec4566bfeae04714197d908bbd9c8322ef93cf5f005cbbee502ebe3",
                panel_n6="267bb24716f67820591e26b32acbc68513990eac8314f2c871d789d2606f0de1",
                trace_n8="122a25ee639e011f96880539ab23e8f88b9f2a9a8d407e126ff152fc756fcf37",
                manifest="daef14d073dbe09a886eb70ba2cf4ceb440eb690eaee164a12276f9a92a47ebf"),
    ),
    AssetSpec(
        "b2_h6", "H6", 2, 994102, "s1_bounded_confirmation_b15_b2_h6_s994102",
        "e0a20add999ded53943f99df15f596822e6c13dc", "s1_bounded_confirmation_b15", "b2_h6",
        "582ddc35ea934398788a79c8552bf07bdb269c67ebb30e3e2b25bf8331e04ed9", 23_073_626,
        _hashes(config="a0ec2e1fc0379a39612d38dc42263d9fbc6997e52f06308bc13a974dd30cc60b",
                summary="5925bc427d84fd666105b1f106e51f64f71fea71d1f608331a65b60229e03f73",
                checkpoint="32db623c26da4de55248c78dce099e73a25f5f7e89b4da765ea000bd3d54e804",
                panel_n8="009447ba5ba83ef6e7674322dd0b37a08fa55b7c49c071e2b7377f5a14a54fe3",
                panel_n6="7bcf00c2d0af3500561a5fabebd30c506876d23f90627da59672c74c38b056af",
                trace_n8="ea8a26a82ca6061a5a0aff063d9adda654d232cf3f8311d883ecfffd9423ee0f",
                manifest="3519a2a8d8b61869270cc66e25dba3499046e42923579591f860b39580b5d68a"),
    ),
    AssetSpec(
        "b3_local1", "LOCAL1", 3, 994103, "s1_local_ordinary_b16_b3_local1_s994103",
        "c95e57201dd7177fc8158b22a3379b56a5be8800", "s1_local_ordinary_b16", "b3_local1",
        "6ddd771b210750d7788bdb86d34ecc7c47062e7df8b8e9c8f7a980040d015d5e", 19_694_959,
        _hashes(config="9002a566176adcc5aabc5a2792bc80ef679a9b29af8163d25a5d94ff65b93433",
                summary="0f4d16fdd1e99fd6d84610ba98372e3a2d768035c002efd5bc2c3168fae229db",
                checkpoint="27d97c7e5eacb960cb317d2d8479a59e94641202a960c3add411ea16d09e3f60",
                panel_n8="a8698da57ad72b8a17dc07e69291b7f0f8a157e7de461b41299517ca042c164f",
                panel_n6="0758949daaa5b12004c5df32d53dce9f2c1131b7861617e703fc30883edd1c07",
                trace_n8="2c9f4f88dcf4acf31b078cc582c098b2966f764d9312a5178fbd31d6f1159ac9",
                manifest="ed5bf1eddb4ff36fa830460ec3e6e0ba88086234820cdb32aad8e2f078aa8d2e"),
    ),
    AssetSpec(
        "b3_h6", "H6", 3, 994103, "s1_bounded_confirmation_b15_b3_h6_s994103",
        "e0a20add999ded53943f99df15f596822e6c13dc", "s1_bounded_confirmation_b15", "b3_h6",
        "cc33620256f5420fabddb2f72983194883e4ad03e6cb2732883a66f6831df09a", 23_073_626,
        _hashes(config="4270b75dce40f1ad00e3969e9c13a2b680cbe74becd4b9ad5e7e8eea4e22a628",
                summary="0d0f3a50b025b342e3d741df84af44424b9a3a9f5778b2ef3f821e7f4e76bc8f",
                checkpoint="edbda8d16847f5ac1379315f8c7ddcdd18b00f7453ca6761f62e047fb98ca1a3",
                panel_n8="0032b78bd1700d96adbcb516fde62d46a3fd2f1855f0f58b614f8959711ad645",
                panel_n6="da2b702d1320477b39c3e057039737560218ab2f668d0d735b8f26fab57bda1a",
                trace_n8="28a6e2f21c1da8613038da4fedac9b0e78fc51bb54d93d6b91b2bc5d4c839dd1",
                manifest="021983b924bd8db11f70044f4041601355718d01c3dcecbd16b8274b23a1c993"),
    ),
)


@dataclass
class LoadedAsset:
    spec: AssetSpec
    root: Path
    config: dict[str, Any]
    summary: dict[str, Any]
    payload: dict[str, Any]
    old_panels: dict[int, dict[str, Any]]
    identities: dict[str, dict[str, Any]]
    fit_spec: FitSpec
    restore_validation: dict[int, dict[str, Any]]


class PanelFailure(RuntimeError):
    def __init__(self, message: str, row: dict[str, Any]):
        super().__init__(message)
        self.row = row


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_bound(path: Path, expected: str) -> tuple[bytes, dict[str, Any]]:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"B17 required input is missing: {path}")
    raw = path.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != expected:
        raise ValueError(f"B17 input SHA-256 mismatch: {path}")
    return raw, {"path": str(path), "sha256": observed, "bytes": len(raw)}


def _read_json(path: Path, expected: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw, identity = _read_bound(path, expected)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"B17 input JSON is not an object: {path}")
    return value, identity


def _fit_spec(summary: Mapping[str, Any]) -> FitSpec:
    source = summary.get("spec")
    if not isinstance(source, dict):
        raise ValueError("B17 source summary lacks training spec")
    values = {}
    for key, default in vars(TRAINING_SPEC).items():
        if key not in source:
            raise ValueError(f"B17 source training spec lacks {key}")
        values[key] = tuple(source[key]) if isinstance(default, tuple) else source[key]
    return FitSpec(**values)


def _validate_source(spec: AssetSpec, config: dict[str, Any], summary: dict[str, Any],
                     panels: dict[int, dict[str, Any]], manifest: dict[str, Any],
                     fit: FitSpec) -> None:
    expected = {"schema": 1, "direction": DIRECTION, "object_id": spec.object_id,
                "tag": spec.tag, "arm": spec.arm, "seed": spec.seed,
                "launch_sha": spec.source_sha, "status": "complete", "fit_started": True}
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError(f"B17 source summary identity mismatch for {spec.key}")
    cell = summary.get("cell", {})
    if cell.get("key") != spec.cell_key or cell.get("arm") != spec.arm \
            or cell.get("seed") != spec.seed or cell.get("law") != "clip":
        raise ValueError(f"B17 source cell identity mismatch for {spec.key}")
    if summary.get("final_parameter_normalizer_digest") != spec.final_digest:
        raise ValueError(f"B17 source final digest mismatch for {spec.key}")
    counts = summary.get("counts", {})
    if counts.get("training_team_steps") != PRIOR_TRAINING_TEAM_STEPS \
            or counts.get("stored_team_steps") != PRIOR_TRAINING_TEAM_STEPS \
            or counts.get("updates") != POLICY_STAGE:
        raise ValueError(f"B17 source exposure mismatch for {spec.key}")
    if (fit.train_n, fit.horizon, fit.rollouts, fit.train_lanes, fit.eval_lanes,
            fit.hidden_size, fit.n_heads, fit.n_layers) != (6, 500, 45, 16, 32, 256, 8, 2):
        raise ValueError(f"B17 source fit construction mismatch for {spec.key}")
    if config.get("launch_sha") != spec.source_sha or config.get("cell") != cell \
            or config.get("config") != summary.get("config") or config.get("spec") != summary.get("spec"):
        raise ValueError(f"B17 config/summary binding mismatch for {spec.key}")
    saved_config = summary.get("config", {})
    required_config = {
        "count_arm": spec.arm, "seed": spec.seed, "n_agents": 6, "n_uavs": 6,
        "n_users": 50, "num_envs": 16, "rollout_length": 500, "episode_length": 500,
        "k": 10, "state_dim": 133, "obs_dim": 104, "action_dim": 3,
        "hidden_size": 256, "n_heads": 8, "n_encoder_layers": 2,
        "n_decoder_layers": 2, "policy_interruption_mode": "off",
        "use_central_snapshot_in_flat_actor": False, "lambda_l": .05,
        "total_timesteps": PRIOR_TRAINING_TEAM_STEPS,
    }
    if any(saved_config.get(key) != value for key, value in required_config.items()):
        raise ValueError(f"B17 source policy config mismatch for {spec.key}")
    if spec.arm == "LOCAL1" and (saved_config.get("algorithm"), saved_config.get("n_Z"),
                                  saved_config.get("n_z"), saved_config.get("num_team_codes")) \
            != ("mappo", 1, 1, 1):
        raise ValueError(f"B17 LOCAL1 program identity mismatch for {spec.key}")
    if spec.arm == "H6" and (saved_config.get("algorithm"), saved_config.get("n_Z"),
                              saved_config.get("n_z")) != ("hmasd", 6, 6):
        raise ValueError(f"B17 H6 program identity mismatch for {spec.key}")
    checkpoint = {row.get("path"): row for row in summary.get("checkpoints", [])}.get(
        "checkpoint_45.pt"
    )
    if checkpoint != {"path": "checkpoint_45.pt", "sha256": spec.hash_for("checkpoint"),
                       "bytes": spec.checkpoint_bytes}:
        raise ValueError(f"B17 source checkpoint record mismatch for {spec.key}")
    source_panels = {(row.get("policy_stage"), row.get("test_n")): row
                     for row in summary.get("panels", [])}
    for n, panel in panels.items():
        if source_panels.get((POLICY_STAGE, n)) != panel:
            raise ValueError(f"B17 source panel/summary mismatch for {spec.key} N={n}")
        worlds = list(range(b15.WORLD_SEED_BASES[n], b15.WORLD_SEED_BASES[n] + 32))
        if panel.get("status") != "complete" or panel.get("world_seeds") != worlds \
                or panel.get("steps") != 16_000 or panel.get("episodes") != 32 \
                or panel.get("resets") != 32 or panel.get("policy_stage") != POLICY_STAGE \
                or panel.get("training_storage_calls") != 0 \
                or any(panel.get("optimizer_calls", {}).values()) \
                or panel.get("frozen_weights_and_normalizers") is not True:
            raise ValueError(f"B17 old panel contract mismatch for {spec.key} N={n}")
    if panels[8].get("trace", {}).get("sha256") != spec.hash_for("trace_n8"):
        raise ValueError(f"B17 old N8 panel trace binding mismatch for {spec.key}")
    if manifest.get("sha") != spec.source_sha or manifest.get("direction") != DIRECTION:
        raise ValueError(f"B17 source manifest identity mismatch for {spec.key}")


def _validate_payload(spec: AssetSpec, payload: Any, summary: Mapping[str, Any]) -> None:
    required = {"schema", "direction", "launch_sha", "rollout", "config", "modules",
                "normalizers", "usage"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError(f"B17 checkpoint payload keys mismatch for {spec.key}")
    if (payload.get("schema"), payload.get("direction"), payload.get("launch_sha"),
            payload.get("rollout")) != (1, DIRECTION, spec.source_sha, POLICY_STAGE):
        raise ValueError(f"B17 checkpoint stage/source mismatch for {spec.key}")
    source_config = summary["config"]
    expected_keys = set(config_dict(type("C", (), source_config)()))
    saved_config = payload.get("config")
    if not isinstance(saved_config, dict) or set(saved_config) != expected_keys \
            or any(saved_config[key] != source_config.get(key) for key in saved_config):
        raise ValueError(f"B17 checkpoint config mismatch for {spec.key}")
    expected_modules = ({"skill_coordinator", "skill_discoverer"}
                        if spec.arm == "LOCAL1" else
                        {"skill_coordinator", "skill_discoverer", "team_discriminator",
                         "individual_discriminator"})
    modules = payload.get("modules")
    if not isinstance(modules, dict) or set(modules) != expected_modules:
        raise ValueError(f"B17 checkpoint module set mismatch for {spec.key}")
    for module_name, state in modules.items():
        if not isinstance(state, dict) or not state:
            raise ValueError(f"B17 checkpoint module state missing: {spec.key}.{module_name}")
        for tensor_name, tensor in state.items():
            if not torch.is_tensor(tensor) or tensor.numel() == 0 \
                    or (tensor.dtype.is_floating_point and not bool(torch.isfinite(tensor).all())):
                raise ValueError(f"B17 checkpoint tensor invalid: {module_name}.{tensor_name}")
    normalizers = payload.get("normalizers")
    if not isinstance(normalizers, dict) or set(normalizers) != set(NORMALIZERS):
        raise ValueError(f"B17 checkpoint normalizer set mismatch for {spec.key}")
    _finite_tree(normalizers, f"{spec.key}.normalizers")
    if payload.get("usage") != "Evaluation weights; no training resume contract or optimizer restoration.":
        raise ValueError(f"B17 checkpoint usage mismatch for {spec.key}")


def _make_eval_config(record: LoadedAsset, envs: list[Any], n: int,
                      eval_spec: EvalSpec, *, strict_contract: bool = True) -> Any:
    fit = replace(record.fit_spec, train_n=n, test_ns=eval_spec.test_ns,
                  eval_lanes=eval_spec.eval_lanes, horizon=eval_spec.horizon)
    if record.spec.arm == "LOCAL1":
        cell = b16.CELL_BY_KEY[record.spec.cell_key]
        config = b16.make_b16_config(cell, envs, fit, expected_n=n)
        rebuilt = b16._config_record(config)
    else:
        cell = b15.CELL_BY_KEY[record.spec.cell_key]
        config = b15.make_b15_config(cell, envs, fit, expected_n=n)
        rebuilt = b15._config_record(config)
    source = record.summary["config"]
    allowed = {"n_agents", "n_uavs", "num_envs", "batch_size", "discriminator_batch_size",
               "high_level_buffer_size"}
    if not strict_contract:
        allowed.update({"rollout_length", "episode_length", "high_level_batch_size",
                        "total_timesteps"})
    changed = {key: (source.get(key), rebuilt.get(key)) for key in source
               if key not in allowed and source.get(key) != rebuilt.get(key)}
    if changed:
        raise ValueError(f"B17 rebuilt policy config changed for {record.spec.key}: {changed}")
    if (rebuilt["n_agents"], rebuilt["n_uavs"], rebuilt["num_envs"]) != (n, n, len(envs)):
        raise ValueError(f"B17 rebuilt roster/lanes mismatch for {record.spec.key} N={n}")
    if strict_contract and n in (8, 6) and rebuilt != record.old_panels[n]["config"]:
        raise ValueError(f"B17 rebuilt config differs from original evaluator for {record.spec.key} N={n}")
    return config


def _build_agent(record: LoadedAsset, config: Any, log_dir: Path) -> Any:
    if record.spec.arm == "LOCAL1":
        return b16.build_local_agent(config, str(log_dir))
    return build_agent(config, str(log_dir))


def _strict_restore(record: LoadedAsset, eval_spec: EvalSpec, log_root: Path,
                    *, strict_contract: bool = True) -> dict[int, dict[str, Any]]:
    evidence = {}
    for n in eval_spec.test_ns:
        runtime_seed = FRESH_RUNTIME_SEEDS[n]
        outer_before = _rng_digest()
        with preserve_rng():
            seed_rng(runtime_seed)
            rng_seeded = _rng_digest()
            envs = make_envs(eval_spec.eval_lanes, FRESH_WORLD_SEEDS[n], n, eval_spec.horizon)
            rng_after_env = _rng_digest()
            target = None
            try:
                b11._assert_native_envs(envs, n)
                config = _make_eval_config(record, envs, n, eval_spec,
                                           strict_contract=strict_contract)
                rng_after_config = _rng_digest()
                target = _build_agent(record, config, log_root / record.spec.key / f"n{n}")
                rng_after_builder = _rng_digest()
                restore_checkpoint(target, record.payload)
                observed = digest_agent(target)
                if observed != record.spec.final_digest:
                    raise ValueError(f"B17 strict restored digest mismatch for {record.spec.key} N={n}")
                buffer = b11._buffer_initial_record(target)
                evidence[n] = {
                    "test_n": n, "runtime_seed": runtime_seed,
                    "rng_seeded": rng_seeded, "rng_after_environment_construction": rng_after_env,
                    "rng_after_config_construction": rng_after_config,
                    "rng_after_agent_construction": rng_after_builder,
                    "rng_after_restore": _rng_digest(), "restored_digest": observed,
                    "module_names": sorted(record.payload["modules"]),
                    "normalizer_names": sorted(record.payload["normalizers"]),
                    "buffer_initial": buffer, "config": (
                        b16._config_record(config) if record.spec.arm == "LOCAL1"
                        else b15._config_record(config)
                    ),
                }
            finally:
                for env in envs:
                    env.close()
                del target
        outer_after = _rng_digest()
        evidence[n]["outer_rng_isolation"] = {
            "before": outer_before, "after": outer_after, "preserved": outer_before == outer_after,
        }
        if outer_before != outer_after:
            raise ValueError(f"B17 strict restore changed outer RNG for {record.spec.key} N={n}")
    digests = {row["restored_digest"] for row in evidence.values()}
    if digests != {record.spec.final_digest}:
        raise ValueError(f"B17 cross-N restore digest mismatch for {record.spec.key}")
    return evidence


def load_assets(input_root: Path, *, assets: tuple[AssetSpec, ...] = ASSETS,
                eval_spec: EvalSpec = DEFAULT_SPEC, restore_log_root: Path | None = None,
                strict_contract: bool = True) -> list[LoadedAsset]:
    input_root = Path(input_root)
    if tuple(asset.key for asset in assets) != POLICY_ORDER:
        raise ValueError("B17 policy order changed")
    if strict_contract and (input_root.name != DIRECTION or eval_spec != DEFAULT_SPEC):
        raise ValueError("B17 production input root/spec binding changed")
    loaded = []
    for spec in assets:
        root = input_root / spec.tag
        names = {
            "config": "config.json", "summary": "summary.json", "checkpoint": "checkpoint_45.pt",
            "panel_n8": "panel_stage45_n8.json", "panel_n6": "panel_stage45_n6.json",
            "trace_n8": "trace_stage45_n8.npz", "manifest": "launch-manifest.json",
        }
        identities, values = {}, {}
        for key, filename in names.items():
            if key in {"config", "summary", "panel_n8", "panel_n6", "manifest"}:
                values[key], identities[key] = _read_json(root / filename, spec.hash_for(key))
            else:
                _, identities[key] = _read_bound(root / filename, spec.hash_for(key))
        if identities["checkpoint"]["bytes"] != spec.checkpoint_bytes:
            raise ValueError(f"B17 checkpoint byte size mismatch for {spec.key}")
        fit = _fit_spec(values["summary"])
        panels = {8: values["panel_n8"], 6: values["panel_n6"]}
        _validate_source(spec, values["config"], values["summary"], panels,
                         values["manifest"], fit)
        payload = torch.load(root / "checkpoint_45.pt", map_location="cpu", weights_only=True)
        _validate_payload(spec, payload, values["summary"])
        record = LoadedAsset(spec, root, values["config"], values["summary"], payload,
                             panels, identities, fit, {})
        if restore_log_root is not None:
            record.restore_validation = _strict_restore(
                record, eval_spec, Path(restore_log_root), strict_contract=strict_contract,
            )
        loaded.append(record)
    return loaded


class _InferenceCounter:
    """Count actual actor, critic, coordinator, decoder and snapshot work."""
    def __init__(self, agent: Any, arm: str, n: int):
        self._agent = agent
        self._inner = b13._InferenceCounter(agent, arm, n)
        self._original_refresh = agent._refresh_central_snapshots
        self.data = {"actor_calls": 0, "actor_rows": 0, "critic_calls": 0,
                     "critic_rows": 0, "snapshot_refresh_calls": 0,
                     "snapshot_refresh_lane_rows": 0}
        self._handles = [
            agent.skill_discoverer.actor.register_forward_hook(self._actor),
            agent.skill_discoverer.critic.register_forward_hook(self._critic),
        ]

        def counted_refresh(_agent: Any, states: Any, observations: Any,
                            refresh_mask: Any) -> Any:
            mask = np.asarray(refresh_mask, dtype=bool)
            self.data["snapshot_refresh_calls"] += int(mask.any())
            self.data["snapshot_refresh_lane_rows"] += int(mask.sum())
            return self._original_refresh(states, observations, refresh_mask)

        agent._refresh_central_snapshots = MethodType(counted_refresh, agent)

    def _actor(self, _module: Any, args: tuple[Any, ...], _output: Any) -> None:
        self.data["actor_calls"] += 1
        self.data["actor_rows"] += int(args[0].shape[0])

    def _critic(self, _module: Any, args: tuple[Any, ...], _output: Any) -> None:
        self.data["critic_calls"] += 1
        self.data["critic_rows"] += int(args[0].shape[0])

    def observe_choices(self, data: dict[str, Any]) -> None:
        self._inner.observe_choices(data)

    def finish(self, eval_spec: EvalSpec) -> dict[str, Any]:
        result = self._inner.finish(eval_spec)
        expected_calls = eval_spec.horizon
        expected_rows = eval_spec.horizon * eval_spec.eval_lanes * self._inner.n
        if self.data["actor_calls"] != expected_calls or self.data["actor_rows"] != expected_rows \
                or self.data["critic_calls"] != expected_calls \
                or self.data["critic_rows"] != expected_rows:
            raise ValueError(f"B17 actor/critic inference counts changed: {self.data}")
        if self.data["snapshot_refresh_calls"] or self.data["snapshot_refresh_lane_rows"]:
            raise ValueError("B17 LOCAL1/H6 unexpectedly used central actor snapshots")
        return {**result, **self.data}

    def close(self) -> None:
        self._agent._refresh_central_snapshots = self._original_refresh
        for handle in self._handles:
            handle.remove()
        self._inner.close()


def _new_trace(eval_spec: EvalSpec, n: int) -> dict[str, np.ndarray]:
    trace = b15._new_panel_trace(eval_spec, n)
    base = (eval_spec.horizon, eval_spec.eval_lanes)
    trace.update({
        "terminated": np.zeros(base, dtype=bool),
        "truncated": np.zeros(base, dtype=bool),
        "team_skills": np.zeros(base, dtype=np.int64),
        "agent_skills": np.zeros((*base, n), dtype=np.int64),
        "skill_changed": np.zeros(base, dtype=bool),
        "skill_timer": np.zeros(base, dtype=np.int64),
        "uav_positions": np.zeros((*base, n, 3), dtype=np.float64),
        "user_positions": np.zeros((*base, 50, 2), dtype=np.float64),
    })
    return trace


def _phase_seed(phase: str, n: int) -> tuple[int, int]:
    if phase == "replay":
        if n != 8:
            raise ValueError("B17 old replay is N8 only")
        return OLD_WORLD_SEED, OLD_RUNTIME_SEED
    if phase != "fresh" or n not in FRESH_WORLD_SEEDS:
        raise ValueError(f"B17 invalid panel phase/N: {phase}/{n}")
    return FRESH_WORLD_SEEDS[n], FRESH_RUNTIME_SEEDS[n]


def _trace_path(out: Path, phase: str, key: str, n: int) -> Path:
    return out / f"trace_{phase}_{key}_n{n}.npz"


def evaluate_panel(record: LoadedAsset, n: int, phase: str, out: Path, eval_spec: EvalSpec,
                   progress: Callable[[int, int, int, int, int], None] | None = None,
                   *, strict_contract: bool = True) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    world_seed, runtime_seed = _phase_seed(phase, n)
    outer_before = _rng_digest()
    row: dict[str, Any] = {
        "status": "running", "phase": phase, "asset_key": record.spec.key,
        "arm": record.spec.arm, "block": record.spec.block, "seed": record.spec.seed,
        "policy_stage": POLICY_STAGE, "test_n": n,
        "world_seeds": list(range(world_seed, world_seed + eval_spec.eval_lanes)),
        "runtime_seed": runtime_seed, "steps": 0, "episodes": 0, "resets": 0,
        "policy_step_calls": 0, "training_storage_calls": 0,
    }
    trace: dict[str, np.ndarray] | None = None
    completed_full_timesteps = 0
    with preserve_rng():
        seed_rng(runtime_seed)
        rng = {"after_fixed_seed_before_construction": _rng_digest()}
        envs = make_envs(eval_spec.eval_lanes, world_seed, n, eval_spec.horizon)
        rng["after_environment_construction"] = _rng_digest()
        target, counter, hooks, calls = None, None, [], {}
        original_store = None
        storage_calls = 0
        try:
            b11._assert_native_envs(envs, n)
            config = _make_eval_config(record, envs, n, eval_spec,
                                       strict_contract=strict_contract)
            rng["after_config_construction"] = _rng_digest()
            target = _build_agent(record, config,
                                  out / "evaluation_logs" / phase / record.spec.key / f"n{n}")
            rng["after_agent_construction"] = _rng_digest()
            restore_checkpoint(target, record.payload)
            rng["after_checkpoint_restore"] = _rng_digest()
            target.train(False)
            for lane in range(eval_spec.eval_lanes):
                target.reset_env_state(lane)
            buffer_before = b11._buffer_initial_record(target)
            calls, hooks = optimizer_counts(target)
            before = digest_agent(target)
            if before != record.spec.final_digest:
                raise ValueError(f"B17 restored final digest mismatch for {record.spec.key} N={n}")
            normalizers_before = _normalizer_record(target)
            runtime_before = runtime_state_digest(target)
            original_store = target.store_transition_batch

            def reject_store(_target: Any, *args: Any, **kwargs: Any) -> None:
                nonlocal storage_calls
                storage_calls += 1
                raise ValueError("B17 fixed-policy evaluation attempted training storage")

            target.store_transition_batch = MethodType(reject_store, target)
            counter = _InferenceCounter(target, record.spec.arm, n)
            rng["before_reset_no_reseed"] = _rng_digest()
            pairs = []
            for env in envs:
                pairs.append(env.reset())
                row["resets"] += 1
                if progress is not None:
                    progress(0, 0, n, 0, 1)
            rng["after_reset"] = _rng_digest()
            states = np.stack([info["state"] for observation, info in pairs])
            observations = np.stack([observation for observation, info in pairs])
            steps = np.zeros(eval_spec.eval_lanes, dtype=np.int64)
            dones = np.zeros(eval_spec.eval_lanes, dtype=bool)
            returns = np.zeros(eval_spec.eval_lanes, dtype=np.float64)
            sums = {name: np.zeros(eval_spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
            trace = _new_trace(eval_spec, n)
            trace["initial_states"] = states.copy()
            trace["initial_observations"] = observations.copy()
            action_min, action_max = float("inf"), float("-inf")
            raw_executed_differ = False
            with torch.no_grad():
                for t in range(eval_spec.horizon):
                    trace["states"][t] = states
                    trace["observations"][t] = observations
                    raw_actions, _, data = target.step(
                        states, observations, steps, dones, deterministic=True,
                        return_step_data=True, build_infos=False,
                    )
                    row["policy_step_calls"] += 1
                    if progress is not None:
                        progress(0, 0, n, 1, 0)
                    finite((raw_actions, data), "B17 deterministic policy output")
                    if raw_actions.shape != (eval_spec.eval_lanes, n, 3) \
                            or raw_actions.dtype != np.float32:
                        raise ValueError("B17 action shape/dtype mismatch")
                    counter.observe_choices(data)
                    trace["team_skills"][t] = np.asarray(data["team_skills"], dtype=np.int64)
                    trace["agent_skills"][t] = np.asarray(data["agent_skills"], dtype=np.int64)
                    trace["skill_changed"][t] = np.asarray(data["skill_changed"], dtype=bool)
                    trace["skill_timer"][t] = np.asarray(data["skill_timer"], dtype=np.int64)
                    raw_before = raw_actions.copy()
                    executed = map_training_actions(raw_actions, "clip")
                    if not np.array_equal(raw_actions, raw_before):
                        raise ValueError("B17 clip mapping mutated raw policy output")
                    raw_executed_differ |= not np.array_equal(raw_actions, executed)
                    trace["raw_actions"][t] = raw_actions
                    trace["executed_actions"][t] = executed
                    action_min = min(action_min, float(executed.min()))
                    action_max = max(action_max, float(executed.max()))
                    next_states, next_observations = [], []
                    for lane, env in enumerate(envs):
                        observation, reward, terminated, truncated, info = env.step(executed[lane])
                        done = bool(terminated or truncated)
                        row["steps"] += 1
                        row["episodes"] += int(done)
                        trace["terminated"][t, lane] = bool(terminated)
                        trace["truncated"][t, lane] = bool(truncated)
                        if progress is not None:
                            progress(1, int(done), n, 0, 0)
                        parts = native_components(info, reward, n)
                        returns[lane] += reward
                        for name in COMPONENTS:
                            sums[name][lane] += parts[name]
                        b11._observe_post_transition(trace, t, lane, env, reward, parts, n)
                        native = env.env.env
                        trace["uav_positions"][t, lane] = np.asarray(
                            native.uav_positions, dtype=np.float64,
                        )
                        trace["user_positions"][t, lane] = np.asarray(
                            native.user_positions, dtype=np.float64,
                        )
                        next_states.append(info["next_state"])
                        next_observations.append(observation)
                        dones[lane] = done
                    states, observations = np.stack(next_states), np.stack(next_observations)
                    trace["next_states"][t] = states
                    trace["next_observations"][t] = observations
                    steps += 1
                    completed_full_timesteps = t + 1
                    if dones.any() and (t != eval_spec.horizon - 1 or not dones.all()):
                        raise ValueError("unexpected B17 terminal boundary")
            if not dones.all():
                raise ValueError("B17 evaluation missed fixed terminal boundary")
            expected_boundaries = np.broadcast_to(
                np.arange(eval_spec.horizon)[:, None] % 10 == 0,
                (eval_spec.horizon, eval_spec.eval_lanes),
            )
            if not np.array_equal(trace["skill_changed"], expected_boundaries):
                raise ValueError("B17 k10 temporal decision boundaries changed")
            means = {name: value / eval_spec.horizon for name, value in sums.items()}
            j = n * returns / eval_spec.horizon
            native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means[
                "energy_penalty"
            ]
            if not np.allclose(j, means["total_reward"], atol=ATOL, rtol=RTOL) \
                    or not np.allclose(j, native_j, atol=ATOL, rtol=RTOL):
                raise ValueError("B17 native J/component identity failed")
            service = trace["served_user_counts"].mean(axis=0)
            eligibility = trace["eligible_user_counts"].mean(axis=0)
            unserved = trace["eligible_unserved_user_counts"].mean(axis=0)
            if not np.allclose(service, 50.0 * means["coverage_reward"], atol=ATOL, rtol=RTOL) \
                    or not np.allclose(unserved, eligibility - service, atol=ATOL, rtol=RTOL):
                raise ValueError("B17 native C/S or E/S/U identity failed")
            if n == 4 and np.any(trace["served_user_counts"] > 40):
                raise ValueError("B17 N4 service exceeded physical c10 capacity")
            inference = counter.finish(eval_spec)
            model_after = digest_agent(target)
            normalizers_after = _normalizer_record(target)
            runtime_after = runtime_state_digest(target)
            if any(calls.values()) or storage_calls or model_after != before \
                    or normalizers_after != normalizers_before:
                raise ValueError("B17 evaluation optimized, stored, or changed weights/normalizers")
            if np.any(target.rollout_buffer.env_lengths):
                raise ValueError("B17 evaluation populated training rollout storage")
            trace_identity = b11._write_trace(_trace_path(out, phase, record.spec.key, n), trace)
            rng["after_rollout"] = _rng_digest()
            row = {
                "status": "complete", "phase": phase, "asset_key": record.spec.key,
                "arm": record.spec.arm, "block": record.spec.block, "seed": record.spec.seed,
                "policy_stage": POLICY_STAGE, "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS,
                "test_n": n, "world_seeds": list(range(world_seed, world_seed + eval_spec.eval_lanes)),
                "runtime_seed": runtime_seed, "rng_order": rng,
                "steps": row["steps"], "episodes": row["episodes"], "resets": row["resets"],
                "policy_step_calls": row["policy_step_calls"], "J": j.tolist(),
                "scalar_returns": returns.tolist(), "component_means": jsonable(means),
                "service_arrays": {
                    "E_eligible_users_per_step": eligibility.tolist(),
                    "S_served_users_per_step": service.tolist(),
                    "U_eligible_unserved_users_per_step": unserved.tolist(),
                },
                "optimizer_calls": calls.copy(), "training_storage_calls": storage_calls,
                "rollout_storage_before": buffer_before,
                "rollout_storage_env_lengths": target.rollout_buffer.env_lengths.tolist(),
                "frozen_weights_and_normalizers": True,
                "parameter_normalizer_digest_before": before,
                "parameter_normalizer_digest_after": model_after,
                "restored_digest_matches_original_final": before == record.spec.final_digest,
                "normalizers_before": normalizers_before, "normalizers_after": normalizers_after,
                "runtime_digest_before": runtime_before, "runtime_digest_after": runtime_after,
                "runtime_evolved": runtime_before != runtime_after,
                "execution_law": "raw low-level mean then clip to [-1,1]",
                "raw_executed_actions_differ": raw_executed_differ,
                "executed_action_bounds": {"minimum": action_min, "maximum": action_max},
                "inference_counts": inference, "trace": trace_identity,
                "config": (b16._config_record(config) if record.spec.arm == "LOCAL1"
                           else b15._config_record(config)),
                "post_transition_semantics": True,
                "terminal_successor_recorded": True,
                "actual_sinr_threshold": float(envs[0].env.env.min_sinr),
                "max_connections_per_uav": int(envs[0].env.env.max_connections),
                "height_range": [float(value) for value in envs[0].env.env.height_range],
                "n_users": int(envs[0].env.env.n_users),
            }
        except Exception as exc:
            row.update(
                status="failed", failure=f"{type(exc).__name__}: {exc}",
                completed_full_timesteps=completed_full_timesteps,
                partial_trace_validity={
                    "completed_full_timesteps": completed_full_timesteps,
                    "completed_transition_rows": row["steps"],
                    "allocated_timesteps": eval_spec.horizon,
                    "note": "rows before completed_full_timesteps are complete; later preallocated rows may be partial or zero",
                },
                training_storage_calls=storage_calls,
                optimizer_calls=calls.copy() if hooks else {},
                inference_counts_partial=(
                    {**counter._inner.data, **counter.data} if counter is not None else None
                ),
                rng_order=rng,
            )
            if trace is not None:
                partial_path = out / f"trace_{phase}_{record.spec.key}_n{n}_partial.npz"
                row["partial_trace"] = b11._write_trace(partial_path, trace)
            raise PanelFailure(row["failure"], row) from exc
        finally:
            if counter is not None:
                counter.close()
            if target is not None and original_store is not None:
                target.store_transition_batch = original_store
            for hook in hooks:
                hook.remove()
            for env in envs:
                env.close()
            del target
    outer_after = _rng_digest()
    row["global_rng_isolation"] = {
        "digest_before": outer_before, "digest_after": outer_after,
        "preserved": outer_before == outer_after,
    }
    if outer_before != outer_after:
        raise ValueError(f"B17 panel changed outer RNG for {record.spec.key} N={n}")
    assert trace is not None
    return row, trace


EXACT_REPLAY_ARRAYS = {
    "eligible_links", "connections", "per_uav_eligible_counts",
    "per_uav_connection_counts", "eligible_user_counts", "served_user_counts",
    "eligible_unserved_user_counts", "initial_states", "initial_observations",
}


def compare_array(actual: Any, expected: Any, *, exact: bool) -> dict[str, Any]:
    left, right = np.asarray(actual), np.asarray(expected)
    result: dict[str, Any] = {
        "actual_shape": list(left.shape), "expected_shape": list(right.shape),
        "actual_dtype": str(left.dtype), "expected_dtype": str(right.dtype),
        "rule": "exact" if exact else f"allclose atol={ATOL} rtol={RTOL}",
    }
    if left.shape != right.shape or left.dtype != right.dtype:
        return {**result, "match": False, "exact_equal": False,
                "max_abs_difference": None, "first_out_of_tolerance": None}
    exact_equal = bool(np.array_equal(left, right))
    if exact:
        mismatch = left != right
        match = exact_equal
    else:
        if not (np.isfinite(left).all() and np.isfinite(right).all()):
            return {**result, "match": False, "exact_equal": exact_equal,
                    "max_abs_difference": None, "first_out_of_tolerance": "nonfinite"}
        mismatch = ~np.isclose(left, right, atol=ATOL, rtol=RTOL)
        match = not bool(mismatch.any())
    if np.issubdtype(left.dtype, np.number):
        maximum = float(np.abs(left.astype(np.float64) - right.astype(np.float64)).max(initial=0.0))
    else:
        maximum = 0.0 if exact_equal else 1.0
    first = None if match else list(np.argwhere(mismatch)[0])
    return {**result, "match": match, "exact_equal": exact_equal,
            "max_abs_difference": maximum, "first_out_of_tolerance": first}


def compare_replay(row: Mapping[str, Any], trace: Mapping[str, np.ndarray],
                   record: LoadedAsset) -> dict[str, Any]:
    reference_panel = record.old_panels[8]
    if row["world_seeds"] != reference_panel.get("world_seeds"):
        raise ValueError(f"B17 old replay worlds differ for {record.spec.key}")
    panel_arrays = {
        "J": compare_array(row["J"], reference_panel["J"], exact=False),
        "scalar_returns": compare_array(row["scalar_returns"],
                                         reference_panel["scalar_returns"], exact=False),
    }
    for name in COMPONENTS:
        panel_arrays[f"component_means.{name}"] = compare_array(
            row["component_means"][name], reference_panel["component_means"][name], exact=False,
        )
    for name in ("E_eligible_users_per_step", "S_served_users_per_step",
                 "U_eligible_unserved_users_per_step"):
        panel_arrays[f"service_arrays.{name}"] = compare_array(
            row["service_arrays"][name], reference_panel["service_arrays"][name], exact=False,
        )
    reference_path = record.root / "trace_stage45_n8.npz"
    trace_arrays: dict[str, Any] = {}
    with np.load(reference_path, allow_pickle=False) as reference:
        required = set(reference.files)
        if not required.issubset(trace):
            raise ValueError(f"B17 replay omitted reference arrays for {record.spec.key}")
        for name in reference.files:
            trace_arrays[name] = compare_array(
                trace[name], reference[name], exact=name in EXACT_REPLAY_ARRAYS,
            )
    all_match = all(value["match"] for value in (*panel_arrays.values(), *trace_arrays.values()))
    return {
        "reference": record.identities["trace_n8"], "panel_arrays": panel_arrays,
        "trace_arrays": trace_arrays, "all_match": all_match,
        "continuous_contract": {"atol": ATOL, "rtol": RTOL},
    }


def _quantity_arrays(row: Mapping[str, Any]) -> dict[str, np.ndarray]:
    return {
        "J": np.asarray(row["J"], dtype=np.float64),
        "C": np.asarray(row["component_means"]["coverage_reward"], dtype=np.float64),
        "Q": np.asarray(row["component_means"]["quality_reward"], dtype=np.float64),
        "P": np.asarray(row["component_means"]["energy_penalty"], dtype=np.float64),
        "E": np.asarray(row["service_arrays"]["E_eligible_users_per_step"], dtype=np.float64),
        "S": np.asarray(row["service_arrays"]["S_served_users_per_step"], dtype=np.float64),
        "U": np.asarray(row["service_arrays"]["U_eligible_unserved_users_per_step"], dtype=np.float64),
    }


def _stats(values: Any, worlds: list[int]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (len(worlds),) or not np.isfinite(array).all():
        raise ValueError("B17 reducer received invalid world array")
    return {
        "mean": float(array.mean()), "median": float(np.median(array)),
        "minimum": float(array.min()), "maximum": float(array.max()),
        "minimum_world": worlds[int(array.argmin())],
        "maximum_world": worlds[int(array.argmax())], "values": array.tolist(),
    }


def compute_readings(fresh_panels: list[Mapping[str, Any]],
                     records: list[LoadedAsset], test_ns: tuple[int, ...]) -> dict[str, Any]:
    by_key_n = {(row["asset_key"], row["test_n"]): row for row in fresh_panels}
    if set(by_key_n) != {(key, n) for key in POLICY_ORDER for n in test_ns}:
        raise ValueError("B17 fresh reducer panel inventory mismatch")
    record_by_key = {record.spec.key: record for record in records}
    blocks, n_block_means = {}, {str(n): {name: [] for name in "JCQPESU"} for n in test_ns}
    all_n8_signs = True
    all_n_signs = True
    for block in (1, 2, 3):
        local_key, h6_key = f"b{block}_local1", f"b{block}_h6"
        block_row: dict[str, Any] = {}
        for n in test_ns:
            local, h6 = by_key_n[(local_key, n)], by_key_n[(h6_key, n)]
            worlds = local["world_seeds"]
            if h6["world_seeds"] != worlds:
                raise ValueError(f"B17 pair worlds differ in block {block} N={n}")
            lq, hq = _quantity_arrays(local), _quantity_arrays(h6)
            delta = {name: lq[name] - hq[name] for name in lq}
            adverse = [{"world": worlds[i], "delta_J": float(delta["J"][i]),
                        "delta_S": float(delta["S"][i])}
                       for i in range(len(worlds))
                       if delta["J"][i] <= 0.0 or delta["S"][i] <= 0.0]
            quantities = {name: {"LOCAL1": _stats(lq[name], worlds),
                                 "H6": _stats(hq[name], worlds),
                                 "LOCAL1_minus_H6": _stats(delta[name], worlds)}
                          for name in lq}
            for name in lq:
                n_block_means[str(n)][name].append(float(delta[name].mean()))
            signs = {name: float(delta[name].mean()) > 0.0 for name in ("J", "S")}
            all_n_signs &= all(signs.values())
            if n == 8:
                all_n8_signs &= all(signs.values())
            block_row[str(n)] = {
                "worlds_shared_within_n": worlds, "quantities": quantities,
                "adverse_J_or_S_worlds": adverse, "mean_signs": signs,
                "minimum_absolute_service": {
                    "LOCAL1": quantities["S"]["LOCAL1"], "H6": quantities["S"]["H6"],
                },
            }
        gaps = {}
        for n in (8, 6):
            old_l = _quantity_arrays(record_by_key[local_key].old_panels[n])
            old_h = _quantity_arrays(record_by_key[h6_key].old_panels[n])
            new = block_row[str(n)]["quantities"]
            gaps[str(n)] = {
                name: float(new[name]["LOCAL1_minus_H6"]["mean"]
                            - (old_l[name] - old_h[name]).mean())
                for name in old_l
            }
        block_row["new_minus_old_LOCAL1_minus_H6_gap"] = gaps
        blocks[str(block)] = block_row
    by_n = {}
    for n in test_ns:
        by_n[str(n)] = {
            name: {"block_means": values, "mean": float(np.mean(values)),
                   "median": float(np.median(values)), "minimum": float(np.min(values)),
                   "maximum": float(np.max(values))}
            for name, values in n_block_means[str(n)].items()
        }
    return {
        "blocks": blocks, "by_n_descriptive_block_mean_dispersion": by_n,
        "n8_prediction_all_three_blocks_J_and_S_positive": all_n8_signs,
        "all_nine_block_by_n_J_and_S_means_positive": all_n_signs,
        "scope": "descriptive fixed finite panels; no pooled-N winner, p-value, or equivalence claim",
    }


def _expected_counts(eval_spec: EvalSpec) -> dict[str, int]:
    replay_panels = len(ASSETS)
    fresh_panels = len(ASSETS) * len(eval_spec.test_ns)
    replay_steps = replay_panels * eval_spec.eval_lanes * eval_spec.horizon
    fresh_steps = fresh_panels * eval_spec.eval_lanes * eval_spec.horizon
    replay_uav = replay_steps * 8
    fresh_uav = len(ASSETS) * eval_spec.eval_lanes * eval_spec.horizon * sum(eval_spec.test_ns)
    return {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_updates": 0, "replay_panels": replay_panels, "fresh_panels": fresh_panels,
        "panels": replay_panels + fresh_panels, "replay_team_steps": replay_steps,
        "fresh_team_steps": fresh_steps, "evaluation_team_steps": replay_steps + fresh_steps,
        "replay_uav_steps": replay_uav, "fresh_uav_steps": fresh_uav,
        "evaluation_uav_steps": replay_uav + fresh_uav,
        "evaluation_episodes": (replay_panels + fresh_panels) * eval_spec.eval_lanes,
        "evaluation_resets": (replay_panels + fresh_panels) * eval_spec.eval_lanes,
        "batched_policy_step_calls": (replay_panels + fresh_panels) * eval_spec.horizon,
        "training_storage_calls": 0, "evaluation_optimizer_calls": 0,
    }


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(), Path(__file__).resolve().with_name("__init__.py"),
        REPOSITORY_ROOT / "scripts/run_agent_count_fresh_world_deployment_b17.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/bounded_confirmation_b15/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/local_ordinary_b16/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
    )


def _source_hashes() -> dict[str, str]:
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path) for path in _source_paths()}


def _input_identities(records: list[LoadedAsset]) -> dict[str, dict[str, Any]]:
    result = {}
    for record in records:
        for name, identity in record.identities.items():
            path = Path(identity["path"])
            result[f"{record.spec.key}:{name}"] = {
                "path": str(path), "bytes": path.stat().st_size, "sha256": file_sha256(path),
            }
    return result


def _output_inventory(out: Path) -> dict[str, Any]:
    files = [path for path in out.rglob("*") if path.is_file()]
    rows = {path.relative_to(out).as_posix(): path.stat().st_size for path in files}
    return {"scope": "all current files including summary.json", "files": rows,
            "bytes": int(sum(rows.values())), "file_count": len(rows)}


def run_study(out: Path, launch_sha: str, admission: dict[str, Any], input_root: Path,
              protocol_seed: int, *, assets: tuple[AssetSpec, ...] = ASSETS,
              eval_spec: EvalSpec = DEFAULT_SPEC, strict_contract: bool = True,
              command_start: float | None = None,
              evaluate_fn: Callable[..., tuple[dict[str, Any], dict[str, np.ndarray]]] = evaluate_panel) -> int:
    out, input_root = Path(out), Path(input_root)
    if out.name != TAG or protocol_seed != PROTOCOL_SEED:
        raise ValueError("B17 output tag or fixed protocol seed changed")
    if strict_contract and eval_spec != DEFAULT_SPEC:
        raise ValueError("B17 production evaluation dimensions changed")
    if (out / "summary.json").exists():
        raise ValueError("existing B17 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected = _expected_counts(eval_spec)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": TAG, "direction": DIRECTION,
        "launch_sha": launch_sha, "admission": admission, "status": "validating_assets",
        "zero_fit": True, "failure": None, "protocol_seed": protocol_seed,
        "spec": jsonable(vars(eval_spec)), "policy_stage": POLICY_STAGE,
        "prior_training_team_steps_per_asset": PRIOR_TRAINING_TEAM_STEPS,
        "policy_order": list(POLICY_ORDER), "fresh_n_order_per_policy": list(EVALUATION_ORDER),
        "old_world_seed": OLD_WORLD_SEED, "old_runtime_seed": OLD_RUNTIME_SEED,
        "fresh_world_seed_bases": FRESH_WORLD_SEEDS,
        "fresh_runtime_seeds": FRESH_RUNTIME_SEEDS, "input_root": str(input_root),
        "assets": [], "replay_panels": [], "fresh_panels": [], "readings": None,
        "counts": {key: 0 for key in expected}, "expected_counts": expected,
        "source_hashes_before": _source_hashes(),
        "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                    "device": "cpu", "dtype": "float32", "torch_threads": eval_spec.torch_threads},
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_study_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    records: list[LoadedAsset] = []
    active: dict[str, Any] | None = None
    active_path: Path | None = None
    active_phase: str | None = None
    publish("admitted before model construction or interaction")
    try:
        torch.set_num_threads(eval_spec.torch_threads)
        records = load_assets(input_root, assets=assets, eval_spec=eval_spec,
                              restore_log_root=out / "restore_validation_logs",
                              strict_contract=strict_contract)
        summary["assets"] = [{
            "key": record.spec.key, "arm": record.spec.arm, "block": record.spec.block,
            "seed": record.spec.seed, "tag": record.spec.tag,
            "source_sha": record.spec.source_sha, "final_digest": record.spec.final_digest,
            "identities": record.identities,
            "strict_restore_validation": record.restore_validation,
        } for record in records]
        summary["input_identities_before"] = _input_identities(records)
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "object_id": OBJECT_ID, "tag": TAG,
            "protocol_seed": protocol_seed, "spec": jsonable(vars(eval_spec)),
            "policy_order": list(POLICY_ORDER), "fresh_n_order_per_policy": list(EVALUATION_ORDER),
            "old_world_seed": OLD_WORLD_SEED, "old_runtime_seed": OLD_RUNTIME_SEED,
            "fresh_world_seed_bases": FRESH_WORLD_SEEDS,
            "fresh_runtime_seeds": FRESH_RUNTIME_SEEDS, "input_root": str(input_root),
            "assets": [jsonable(vars(asset)) for asset in assets],
        })
        publish("six final45 assets strictly restored across N4/N6/N8")

        def progress(steps: int, episodes: int, n: int, calls: int, resets: int) -> None:
            if active_phase not in {"replay", "fresh"}:
                raise ValueError("B17 progress arrived outside an active panel phase")
            summary["counts"]["evaluation_team_steps"] += steps
            summary["counts"]["evaluation_uav_steps"] += steps * n
            summary["counts"][f"{active_phase}_team_steps"] += steps
            summary["counts"][f"{active_phase}_uav_steps"] += steps * n
            summary["counts"]["evaluation_episodes"] += episodes
            summary["counts"]["evaluation_resets"] += resets
            summary["counts"]["batched_policy_step_calls"] += calls

        def account_panel_effects(row: Mapping[str, Any]) -> None:
            summary["counts"]["training_storage_calls"] += int(
                row.get("training_storage_calls", 0)
            )
            optimizer_calls = row.get("optimizer_calls", {})
            summary["counts"]["evaluation_optimizer_calls"] += sum(
                int(value) for value in optimizer_calls.values()
            )

        for record in records:
            active_path = out / f"panel_replay_{record.spec.key}_n8.json"
            active = {"status": "running", "phase": "replay", "asset_key": record.spec.key,
                      "arm": record.spec.arm, "block": record.spec.block, "test_n": 8}
            summary["replay_panels"].append(active)
            write_json(active_path, active)
            publish(f"old N8 replay {record.spec.key} starting")
            active_phase = "replay"
            panel_effects_accounted = False
            try:
                evaluated, trace = evaluate_fn(record, 8, "replay", out, eval_spec, progress,
                                               strict_contract=strict_contract)
                account_panel_effects(evaluated)
                panel_effects_accounted = True
                evaluated["replay_comparison"] = compare_replay(evaluated, trace, record)
                if not evaluated["replay_comparison"]["all_match"]:
                    evaluated.update(status="failed",
                                     failure="B17 old replay arrays failed fixed comparison contract")
                    raise PanelFailure(evaluated["failure"], evaluated)
            except PanelFailure as exc:
                if not panel_effects_accounted:
                    account_panel_effects(exc.row)
                active.clear()
                active.update(exc.row)
                write_json(active_path, active)
                raise
            active.clear()
            active.update(evaluated)
            summary["counts"]["replay_panels"] += 1
            summary["counts"]["panels"] += 1
            write_json(active_path, active)
            publish(f"old N8 replay {record.spec.key} matched")
            active = active_path = None
            active_phase = None

        if len(summary["replay_panels"]) != len(records) \
                or not all(row.get("replay_comparison", {}).get("all_match")
                           for row in summary["replay_panels"]):
            raise ValueError("B17 replay gate incomplete; fresh panels forbidden")
        summary["replay_gate_passed_before_fresh"] = True
        publish("all six old N8 replay gates passed before fresh interaction")

        fresh_initial_references: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        for record in records:
            for n in eval_spec.test_ns:
                active_path = out / f"panel_fresh_{record.spec.key}_n{n}.json"
                active = {"status": "running", "phase": "fresh", "asset_key": record.spec.key,
                          "arm": record.spec.arm, "block": record.spec.block, "test_n": n}
                summary["fresh_panels"].append(active)
                write_json(active_path, active)
                publish(f"fresh {record.spec.key} N={n} starting")
                active_phase = "fresh"
                panel_effects_accounted = False
                try:
                    evaluated, trace = evaluate_fn(record, n, "fresh", out, eval_spec, progress,
                                                   strict_contract=strict_contract)
                    account_panel_effects(evaluated)
                    panel_effects_accounted = True
                except PanelFailure as exc:
                    if not panel_effects_accounted:
                        account_panel_effects(exc.row)
                    active.clear()
                    active.update(exc.row)
                    write_json(active_path, active)
                    raise
                initial = (trace["initial_states"], trace["initial_observations"])
                if n not in fresh_initial_references:
                    fresh_initial_references[n] = (initial[0].copy(), initial[1].copy())
                elif not (np.array_equal(initial[0], fresh_initial_references[n][0])
                          and np.array_equal(initial[1], fresh_initial_references[n][1])):
                    evaluated.update(
                        status="failed",
                        failure=f"B17 common fresh initial scenarios differ at N={n}",
                    )
                    active.clear()
                    active.update(evaluated)
                    write_json(active_path, active)
                    raise PanelFailure(evaluated["failure"], evaluated)
                active.clear()
                active.update(evaluated)
                summary["counts"]["fresh_panels"] += 1
                summary["counts"]["panels"] += 1
                write_json(active_path, active)
                publish(f"fresh {record.spec.key} N={n} complete")
                active = active_path = None
                active_phase = None

        initial_matches: dict[str, Any] = {}
        all_panels = summary["replay_panels"] + summary["fresh_panels"]
        for phase, ns in (("replay", (8,)), ("fresh", eval_spec.test_ns)):
            for n in ns:
                rows = [row for row in all_panels if row["phase"] == phase and row["test_n"] == n]
                arrays = []
                for row in rows:
                    with np.load(row["trace"]["path"], allow_pickle=False) as source:
                        arrays.append((row["asset_key"], source["initial_states"].copy(),
                                       source["initial_observations"].copy()))
                reference = arrays[0]
                matches = {key: bool(np.array_equal(states, reference[1])
                                     and np.array_equal(observations, reference[2]))
                           for key, states, observations in arrays}
                if not all(matches.values()):
                    raise ValueError(f"B17 common initial scenarios differ for {phase} N={n}")
                initial_matches[f"{phase}_n{n}"] = matches
        summary["common_initial_scenario_matches"] = initial_matches
        summary["readings"] = compute_readings(summary["fresh_panels"], records,
                                               eval_spec.test_ns)
        summary["counts"]["fits"] = 0
        summary["counts"]["training_team_steps"] = 0
        summary["counts"]["stored_training_steps"] = 0
        summary["counts"]["optimizer_updates"] = 0
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        summary["input_identities_after"] = _input_identities(records)
        summary["input_identities_unchanged"] = (
            summary["input_identities_before"] == summary["input_identities_after"]
        )
        if not summary["source_hashes_unchanged"] or not summary["input_identities_unchanged"]:
            raise ValueError("B17 source or bound inputs changed during evaluation")
        if summary["counts"] != expected:
            raise ValueError(f"B17 cost totals mismatch: {summary['counts']} != {expected}")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        if active is not None and active.get("status") == "running":
            active.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
            if active_path is not None:
                write_json(active_path, active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["fresh_interaction_started"] = bool(summary["fresh_panels"])
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if records:
            try:
                summary["input_identities_after"] = _input_identities(records)
                summary["input_identities_unchanged"] = (
                    summary.get("input_identities_before") == summary["input_identities_after"]
                )
            except Exception as identity_exc:
                summary["input_identity_recheck_failure"] = f"{type(identity_exc).__name__}: {identity_exc}"
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "command_wall_seconds": time.perf_counter() - command_start,
            "run_study_wall_seconds": time.perf_counter() - started,
            "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss,
            "rss_scope": "scientific process Linux RUSAGE_SELF",
            "resources_unmeasured": [],
        }
        publish(summary["status"])
        for _ in range(3):
            summary["output_inventory"] = _output_inventory(out)
            publish(summary["status"])
    return return_code
