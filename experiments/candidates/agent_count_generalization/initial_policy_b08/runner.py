"""Evaluate frozen H6/SET checkpoint-00 policies on the fixed stage-45 worlds."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback
from typing import Any, Callable, Mapping

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.action_law_b02.probe import (
    _normalizer_record,
    _rng_digest,
    restore_checkpoint,
)
from experiments.candidates.agent_count_generalization.action_law_b03.runner import (
    runtime_state_digest,
)
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC as TRAINING_SPEC,
    DIRECTION,
    FitSpec,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    NORMALIZERS,
    digest_agent,
    finite,
    jsonable,
    native_components,
    optimizer_counts,
    preserve_rng,
    reset_all,
    seed_rng,
    write_json,
)


OBJECT_ID = "s1_initial_policy_b08"
TAG = OBJECT_ID
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
POLICY_STAGE = 0
WORLD_PANEL_STAGE = 45
WORLD_SEED_BASE = 1_500_000 + 45_000


@dataclass(frozen=True)
class EvalSpec:
    test_ns: tuple[int, ...] = (4, 6, 8)
    horizon: int = 500
    eval_lanes: int = 16
    torch_threads: int = 4


DEFAULT_SPEC = EvalSpec()


@dataclass(frozen=True)
class AssetSpec:
    key: str
    arm: str
    seed: int
    tag: str
    source_sha: str
    object_id: str
    cell_key: str
    summary_sha256: str
    checkpoint00_sha256: str
    checkpoint00_bytes: int
    checkpoint45_sha256: str
    checkpoint45_bytes: int
    initial_digest: str
    final_panel_sha256: tuple[str, str, str]


ASSETS = (
    AssetSpec(
        "h6", "H6", 952201, "s1_bounded_package_b07_h6_l05_s952201",
        "0a9e3fde40659fdcc1d05922c9920c5c04b2ab23", "s1_bounded_package_b07",
        "h6_l05", "9d7f90523b74ea0fb4b9d7720086baefff13c22cdb41547c2b793764273b550a",
        "65cfcc9f6afc69bae78712a4dd15bc772e2d3b56c82797504e27555a814ef398",
        23_073_626, "6d71f3023e5593a801b4d618f7eece93df1a15575f8a71d769566190ba6498df",
        23_073_626, "1d55b8320256e589e6b88ae4b7873d97d54a536de85d6a33df46fa87a521c733",
        (
            "e5624c9faad75358d86ae7d664f4fabc51d506d397d03981f183915aeff607c7",
            "263b486c2cf433ebc791e21f09a4768e6031c4734710aadd12b54bf7a94f3a15",
            "15f578a91a99621668649f2d901441f60158092eba9d9b9d587b9987138e1d11",
        ),
    ),
    AssetSpec(
        "set", "SET", 953201, "s1_entropy_b05_set_l05_s953201",
        "e2ea736457e0992fb53cf21aa775fd15da3d8231", "s1_entropy_b05", "set_l05",
        "136d090b32a8c5fec1eefad5dbaaefa9155d44ce4335c7fb0f07585d36cff4c4",
        "37b34c34d6bc84bfe43d78e5283668f38db180a16bf99b22d9caf8eb608857ca",
        20_968_771, "98062b5b338b684219c43b5c9a3dc13bf176322a948c439294beee1d52ae477e",
        20_968_771, "b6d466c143157fdb052df6f16f27351516e1e6b8f6e77789b1fa75ecf5876854",
        (
            "92a1f956fbd99396cb3e9547f962e1c5b9c3a505937e230a07b127bc6bc1f9de",
            "f2c06e720cbd99a31d3d79d46e58a62218aa0174a485d5ac0f92203703903eea",
            "dab2278091e7de2406c76b5af1137bc0ebcc1f44479f24c4117c2b198da6e6e5",
        ),
    ),
)


@dataclass
class LoadedAsset:
    spec: AssetSpec
    checkpoint: Path
    summary: dict[str, Any]
    summary_identity: dict[str, Any]
    final_panels: dict[int, dict[str, Any]]
    final_panel_identities: dict[int, dict[str, Any]]
    payload: dict[str, Any]
    fit_spec: FitSpec


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _array_digest(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(repr(array.shape).encode("ascii"))
    digest.update(array.tobytes())
    return digest.hexdigest()


def _finite_tree(value: Any, label: str) -> None:
    if torch.is_tensor(value):
        if value.dtype.is_floating_point and not bool(torch.isfinite(value).all()):
            raise ValueError(f"nonfinite {label}")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _finite_tree(item, f"{label}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _finite_tree(item, f"{label}[{index}]")
    elif isinstance(value, (float, np.floating)) and not np.isfinite(value):
        raise ValueError(f"nonfinite {label}")


def _world_seed(n: int) -> int:
    return WORLD_SEED_BASE + 100 * n


def _config_record(config: Any) -> dict[str, Any]:
    return {
        **config_dict(config),
        "lambda_l_initial": float(config.lambda_l_initial),
        "lambda_l_final": float(config.lambda_l_final),
        "use_entropy_annealing": bool(config.use_entropy_annealing),
        "use_entropy_targets": bool(config.use_entropy_targets),
    }


def _read_bound_json(
    path: Path, expected_sha256: str, *, relative: Path, committed: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if committed:
        raw = subprocess.run(
            ["git", "-C", str(REPOSITORY_ROOT), "show", f"HEAD:{relative.as_posix()}"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        if path.read_bytes() != raw:
            raise ValueError(f"B08 committed/working bytes differ: {relative}")
        binding = "HEAD git blob plus identical working bytes"
    else:
        raw = path.read_bytes()
        binding = "pytest fixture bytes"
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"B08 source JSON SHA-256 mismatch: {relative}")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"B08 source JSON is not an object: {relative}")
    return value, {"path": str(path), "sha256": digest, "bytes": len(raw), "binding": binding}


def _fit_spec(summary: dict[str, Any]) -> FitSpec:
    recorded = summary.get("spec")
    if not isinstance(recorded, dict):
        raise ValueError("B08 source summary lacks training spec")
    fields = {}
    for key, default in vars(TRAINING_SPEC).items():
        if key not in recorded:
            raise ValueError(f"B08 source spec missing {key}")
        fields[key] = tuple(recorded[key]) if isinstance(default, tuple) else recorded[key]
    return FitSpec(**fields)


def _validate_output_panel(
    row: dict[str, Any], *, n: int, lanes: int, horizon: int,
    world_panel_stage: int,
) -> None:
    expected_worlds = list(range(_world_seed(n), _world_seed(n) + lanes))
    if row.get("status") != "complete" or row.get("test_n") != n:
        raise ValueError(f"B08 final panel identity invalid at N={n}")
    if row.get("after_rollout") != world_panel_stage or row.get("world_seeds") != expected_worlds:
        raise ValueError(f"B08 final panel stage/worlds invalid at N={n}")
    if row.get("steps") != lanes * horizon or row.get("episodes") != lanes:
        raise ValueError(f"B08 final panel exposure invalid at N={n}")
    if row.get("execution_law") != "clip" or row.get("frozen_weights_and_normalizers") is not True:
        raise ValueError(f"B08 final panel execution/freeze evidence invalid at N={n}")
    optimizer_calls = row.get("optimizer_calls")
    if not isinstance(optimizer_calls, dict) or any(optimizer_calls.values()):
        raise ValueError(f"B08 final panel optimizer evidence invalid at N={n}")
    if not isinstance(row.get("config"), dict):
        raise ValueError(f"B08 final panel config missing at N={n}")
    for field in ("J", "scalar_returns"):
        values = np.asarray(row.get(field), dtype=np.float64)
        if values.shape != (lanes,) or not np.isfinite(values).all():
            raise ValueError(f"B08 final panel {field} invalid at N={n}")
    components = row.get("component_means", {})
    if set(components) != set(COMPONENTS):
        raise ValueError(f"B08 final components invalid at N={n}")
    arrays = {name: np.asarray(components[name], dtype=np.float64) for name in COMPONENTS}
    if any(values.shape != (lanes,) or not np.isfinite(values).all() for values in arrays.values()):
        raise ValueError(f"B08 final component payload invalid at N={n}")
    j = np.asarray(row["J"], dtype=np.float64)
    returns = np.asarray(row["scalar_returns"], dtype=np.float64)
    native = .7 * arrays["coverage_reward"] + .3 * arrays["quality_reward"] - arrays["energy_penalty"]
    if not np.allclose(j, n * returns / horizon, atol=1e-7, rtol=1e-6):
        raise ValueError(f"B08 final scalar/J identity invalid at N={n}")
    if not np.allclose(j, arrays["total_reward"], atol=1e-7, rtol=1e-6) \
            or not np.allclose(j, native, atol=1e-7, rtol=1e-6):
        raise ValueError(f"B08 final native component identity invalid at N={n}")


def _validate_summary_and_final_panels(
    asset: AssetSpec, *, summary_root: Path, committed: bool, eval_spec: EvalSpec,
) -> tuple[dict[str, Any], dict[str, Any], dict[int, dict[str, Any]], dict[int, dict[str, Any]], FitSpec]:
    run_root = Path(summary_root) / asset.tag
    relative_root = Path("runs") / DIRECTION / asset.tag
    summary, summary_identity = _read_bound_json(
        run_root / "summary.json", asset.summary_sha256,
        relative=relative_root / "summary.json", committed=committed,
    )
    expected = {
        "direction": DIRECTION, "object_id": asset.object_id, "arm": asset.arm,
        "seed": asset.seed, "tag": asset.tag, "launch_sha": asset.source_sha,
        "status": "complete", "training_action_law": "clip",
    }
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError(f"B08 source summary identity mismatch for {asset.key}")
    if summary.get("fit_started") is not True:
        raise ValueError(f"B08 source fit incomplete for {asset.key}")
    cell = summary.get("cell", {})
    if cell.get("key") != asset.cell_key or cell.get("tag") != asset.tag \
            or cell.get("arm") != asset.arm or cell.get("law") != "clip" \
            or cell.get("seed") != asset.seed:
        raise ValueError(f"B08 source cell mismatch for {asset.key}")
    if cell.get("lambda_l", .05) != .05:
        raise ValueError(f"B08 source coefficient mismatch for {asset.key}")
    fit = _fit_spec(summary)
    if (fit.horizon, fit.eval_lanes, fit.torch_threads, fit.test_ns) != (
        eval_spec.horizon, eval_spec.eval_lanes, eval_spec.torch_threads, eval_spec.test_ns,
    ):
        raise ValueError(f"B08 runtime/spec mismatch for {asset.key}")
    config = summary.get("config", {})
    expected_config = {
        "count_arm": asset.arm, "seed": asset.seed, "n_agents": 6, "n_uavs": 6,
        "lambda_l": .05, "lambda_l_initial": .05, "lambda_l_final": .05,
        "use_entropy_annealing": False, "use_entropy_targets": False,
        "hidden_size": fit.hidden_size, "n_heads": fit.n_heads,
        "n_encoder_layers": fit.n_layers, "n_decoder_layers": fit.n_layers,
        "ppo_epochs": fit.ppo_epochs, "sequence_batch_size": fit.sequence_batch_size,
        "coordinator_batch_size": fit.coordinator_batch_size,
    }
    if any(config.get(key) != value for key, value in expected_config.items()):
        raise ValueError(f"B08 source config/architecture mismatch for {asset.key}")
    if summary.get("observed_initial_parameter_normalizer_digest") != asset.initial_digest:
        raise ValueError(f"B08 source initial digest mismatch for {asset.key}")
    records = {row.get("path"): row for row in summary.get("checkpoints", [])}
    expected_checkpoints = {
        "checkpoint_00.pt": (asset.checkpoint00_sha256, asset.checkpoint00_bytes),
        "checkpoint_45.pt": (asset.checkpoint45_sha256, asset.checkpoint45_bytes),
    }
    for name, (digest, size) in expected_checkpoints.items():
        row = records.get(name)
        if row is None or row.get("sha256") != digest or row.get("bytes") != size:
            raise ValueError(f"B08 source {name} identity mismatch for {asset.key}")
    final_panels, identities = {}, {}
    panel_hashes = dict(zip(eval_spec.test_ns, asset.final_panel_sha256))
    for n in eval_spec.test_ns:
        relative = relative_root / f"panel_45_n{n}.json"
        panel, identity = _read_bound_json(
            run_root / f"panel_45_n{n}.json", panel_hashes[n],
            relative=relative, committed=committed,
        )
        matches = [
            row for row in summary.get("panels", [])
            if row.get("after_rollout") == WORLD_PANEL_STAGE and row.get("test_n") == n
        ]
        if len(matches) != 1 or matches[0] != panel:
            raise ValueError(f"B08 summary/final panel bytes disagree for {asset.key} N={n}")
        _validate_output_panel(
            panel, n=n, lanes=eval_spec.eval_lanes, horizon=eval_spec.horizon,
            world_panel_stage=WORLD_PANEL_STAGE,
        )
        final_panels[n], identities[n] = panel, identity
    return summary, summary_identity, final_panels, identities, fit


def _validate_payload(asset: AssetSpec, payload: Any, fit: FitSpec) -> None:
    required = {"schema", "direction", "launch_sha", "rollout", "config", "modules", "normalizers", "usage"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError(f"B08 checkpoint payload keys mismatch for {asset.key}")
    for key, value in {"schema": 1, "direction": DIRECTION,
                       "launch_sha": asset.source_sha, "rollout": POLICY_STAGE}.items():
        if payload.get(key) != value:
            raise ValueError(f"B08 checkpoint {key} mismatch for {asset.key}")
    config = payload.get("config", {})
    expected = {
        "count_arm": asset.arm, "seed": asset.seed, "n_agents": 6, "n_uavs": 6,
        "lambda_l": .05, "hidden_size": fit.hidden_size, "n_heads": fit.n_heads,
        "n_encoder_layers": fit.n_layers, "n_decoder_layers": fit.n_layers,
        "ppo_epochs": fit.ppo_epochs, "sequence_batch_size": fit.sequence_batch_size,
        "coordinator_batch_size": fit.coordinator_batch_size,
    }
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError(f"B08 checkpoint config/architecture mismatch for {asset.key}")
    modules = payload.get("modules")
    if not isinstance(modules, dict) or not modules:
        raise ValueError(f"B08 checkpoint modules missing for {asset.key}")
    for module_name, state in modules.items():
        if not isinstance(state, dict) or not state:
            raise ValueError(f"B08 checkpoint module state invalid: {asset.key}.{module_name}")
        for tensor_name, tensor in state.items():
            if not torch.is_tensor(tensor) or tensor.numel() == 0:
                raise ValueError(f"B08 checkpoint tensor invalid: {asset.key}.{module_name}.{tensor_name}")
            if tensor.dtype.is_floating_point and not bool(torch.isfinite(tensor).all()):
                raise ValueError(f"B08 checkpoint tensor nonfinite: {asset.key}.{module_name}.{tensor_name}")
    normalizers = payload.get("normalizers")
    if not isinstance(normalizers, dict) or set(normalizers) != set(NORMALIZERS):
        raise ValueError(f"B08 checkpoint normalizers invalid for {asset.key}")
    _finite_tree(normalizers, f"{asset.key}.normalizers")


def _make_eval_config(record: LoadedAsset, envs: list[Any], n: int) -> Any:
    config = make_config(record.spec.arm, envs, record.spec.seed, record.fit_spec)
    config.lambda_l = config.lambda_l_initial = config.lambda_l_final = .05
    config.use_entropy_annealing = False
    config.use_entropy_targets = False
    config.validate_config()
    rebuilt = _config_record(config)
    saved = record.payload["config"]
    allowed = {"n_agents", "n_uavs", "batch_size", "discriminator_batch_size"}
    changed = {
        key: (saved.get(key), rebuilt.get(key))
        for key in saved if key not in allowed and saved.get(key) != rebuilt.get(key)
    }
    if changed:
        raise ValueError(f"B08 rebuilt config changed checkpoint policy fields: {changed}")
    if rebuilt["n_agents"] != n or rebuilt["n_uavs"] != n:
        raise ValueError("B08 rebuilt config has wrong N-specific roster")
    historical = record.final_panels[n]["config"]
    differences = {
        key: (historical.get(key), rebuilt.get(key))
        for key in set(historical) | set(rebuilt) if historical.get(key) != rebuilt.get(key)
    }
    if differences:
        raise ValueError(f"B08 rebuilt config differs from original final evaluator: {differences}")
    return config


def _strict_restore_all_ns(record: LoadedAsset, eval_spec: EvalSpec, log_root: Path) -> None:
    for n in eval_spec.test_ns:
        envs = make_envs(eval_spec.eval_lanes, _world_seed(n), n, eval_spec.horizon)
        target = None
        try:
            config = _make_eval_config(record, envs, n)
            target = build_agent(config, str(log_root / record.spec.key / f"n{n}"))
            restore_checkpoint(target, record.payload)
            observed = digest_agent(target)
            if observed != record.spec.initial_digest:
                raise ValueError(
                    f"B08 restored initial digest mismatch for {record.spec.key} N={n}"
                )
        finally:
            for env in envs:
                env.close()
            del target


def load_assets(
    checkpoint_paths: Mapping[str, Path], *, assets: tuple[AssetSpec, ...] = ASSETS,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_sources: bool = True, eval_spec: EvalSpec = DEFAULT_SPEC,
    restore_log_root: Path | None = None,
) -> list[LoadedAsset]:
    if set(checkpoint_paths) != {asset.key for asset in assets}:
        raise ValueError("B08 requires exactly the H6 and SET checkpoint-00 paths")
    loaded = []
    for asset in assets:
        summary, summary_identity, final_panels, panel_identities, fit = (
            _validate_summary_and_final_panels(
                asset, summary_root=summary_root, committed=committed_sources,
                eval_spec=eval_spec,
            )
        )
        checkpoint = Path(checkpoint_paths[asset.key])
        if not checkpoint.is_file() or checkpoint.stat().st_size != asset.checkpoint00_bytes:
            raise ValueError(f"B08 checkpoint-00 byte-size mismatch for {asset.key}")
        if file_sha256(checkpoint) != asset.checkpoint00_sha256:
            raise ValueError(f"B08 checkpoint-00 SHA-256 mismatch for {asset.key}")
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        _validate_payload(asset, payload, fit)
        record = LoadedAsset(
            asset, checkpoint, summary, summary_identity, final_panels,
            panel_identities, payload, fit,
        )
        log_root = (
            Path(restore_log_root) if restore_log_root is not None
            else checkpoint.parent / "b08_restore_validation_logs"
        )
        _strict_restore_all_ns(record, eval_spec, log_root)
        loaded.append(record)
    return loaded


def evaluate_policy(
    record: LoadedAsset, n: int, out: Path, eval_spec: EvalSpec,
    progress: Callable[[int, int, int, int, int], None] | None = None,
) -> dict[str, Any]:
    world_seed = _world_seed(n)
    rng_before = _rng_digest()
    row: dict[str, Any]
    with preserve_rng():
        seed_rng(world_seed + 51)
        envs = make_envs(eval_spec.eval_lanes, world_seed, n, eval_spec.horizon)
        target, hooks = None, []
        try:
            config = _make_eval_config(record, envs, n)
            target = build_agent(config, str(out / "evaluation_logs" / f"{record.spec.key}_n{n}"))
            restore_checkpoint(target, record.payload)
            for lane in range(eval_spec.eval_lanes):
                target.reset_env_state(lane)
            calls, hooks = optimizer_counts(target)
            model_before = digest_agent(target)
            if model_before != record.spec.initial_digest:
                raise ValueError("B08 loader/original initial digest mismatch")
            normalizers_before = _normalizer_record(target)
            runtime_before = runtime_state_digest(target)
            states, observations = reset_all(envs)
            if progress is not None:
                progress(0, 0, n, 0, eval_spec.eval_lanes)
            initial = [{
                "world_seed": world_seed + lane,
                "state_sha256": _array_digest(states[lane]),
                "observation_sha256": _array_digest(observations[lane]),
            } for lane in range(eval_spec.eval_lanes)]
            steps = np.zeros(eval_spec.eval_lanes, dtype=np.int64)
            dones = np.zeros(eval_spec.eval_lanes, dtype=bool)
            returns = np.zeros(eval_spec.eval_lanes, dtype=np.float64)
            components = {name: np.zeros(eval_spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
            action_min, action_max = float("inf"), float("-inf")
            mapping_unchanged = True
            diagnostics_rng_unchanged = True
            with torch.no_grad():
                for t in range(eval_spec.horizon):
                    actions, _, data = target.step(
                        states, observations, steps, dones, deterministic=True,
                        return_step_data=True, build_infos=False,
                    )
                    if progress is not None:
                        progress(0, 0, n, 1, 0)
                    finite((actions, data), "B08 deterministic policy output")
                    if actions.shape != (eval_spec.eval_lanes, n, 3) or actions.dtype != np.float32:
                        raise ValueError("B08 action shape/dtype mismatch")
                    diagnostic_rng = _rng_digest()
                    before = actions.copy()
                    executed = np.clip(actions, -1.0, 1.0)
                    mapping_unchanged &= np.array_equal(actions, before)
                    diagnostics_rng_unchanged &= _rng_digest() == diagnostic_rng
                    action_min = min(action_min, float(executed.min()))
                    action_max = max(action_max, float(executed.max()))
                    next_states, next_observations = [], []
                    for lane, env in enumerate(envs):
                        obs, reward, terminated, truncated, info = env.step(executed[lane])
                        done = bool(terminated or truncated)
                        if progress is not None:
                            progress(1, int(done), n, 0, 0)
                        parts = native_components(info, reward, n)
                        returns[lane] += reward
                        for name in COMPONENTS:
                            components[name][lane] += parts[name]
                        next_states.append(info["next_state"])
                        next_observations.append(obs)
                        dones[lane] = done
                    states, observations = np.stack(next_states), np.stack(next_observations)
                    steps += 1
                    if dones.any() and (t != eval_spec.horizon - 1 or not dones.all()):
                        raise ValueError("unexpected B08 terminal boundary")
            if not dones.all():
                raise ValueError("B08 evaluation missed fixed terminal boundary")
            means = {name: values / eval_spec.horizon for name, values in components.items()}
            j = n * returns / eval_spec.horizon
            native = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
            if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6) \
                    or not np.allclose(j, native, atol=1e-7, rtol=1e-6):
                raise ValueError("B08 native J/component identity failed")
            model_after = digest_agent(target)
            normalizers_after = _normalizer_record(target)
            runtime_after = runtime_state_digest(target)
            if any(calls.values()) or model_after != model_before or normalizers_after != normalizers_before:
                raise ValueError("B08 evaluation changed weights/normalizers or optimized")
            if not mapping_unchanged or not diagnostics_rng_unchanged \
                    or action_min < -1.0 or action_max > 1.0:
                raise ValueError("B08 deterministic clip/diagnostic contract failed")
            row = {
                "status": "complete", "asset_key": record.spec.key, "arm": record.spec.arm,
                "seed": record.spec.seed, "policy_stage": POLICY_STAGE,
                "prior_training_team_steps": 0, "world_panel_stage": WORLD_PANEL_STAGE,
                "test_n": n, "world_seeds": list(range(world_seed, world_seed + eval_spec.eval_lanes)),
                "runtime_seed": world_seed + 51,
                "steps": eval_spec.eval_lanes * eval_spec.horizon,
                "episodes": eval_spec.eval_lanes, "policy_step_calls": eval_spec.horizon,
                "J": j.tolist(), "scalar_returns": returns.tolist(),
                "component_means": jsonable(means), "initial_world_digests": initial,
                "optimizer_calls": calls.copy(), "frozen_weights_and_normalizers": True,
                "parameter_normalizer_digest_before": model_before,
                "parameter_normalizer_digest_after": model_after,
                "restored_digest_matches_original_initial": model_before == record.spec.initial_digest,
                "normalizers_before": normalizers_before, "normalizers_after": normalizers_after,
                "runtime_digest_before": runtime_before, "runtime_digest_after": runtime_after,
                "runtime_evolved": runtime_before != runtime_after,
                "executed_action_bounds": {"minimum": action_min, "maximum": action_max},
                "policy_outputs_unchanged_by_mapping": mapping_unchanged,
                "diagnostics_rng_unchanged": diagnostics_rng_unchanged,
                "config": _config_record(config),
            }
        finally:
            for hook in hooks:
                hook.remove()
            for env in envs:
                env.close()
            del target
    rng_after = _rng_digest()
    if rng_after != rng_before:
        raise ValueError("B08 evaluation changed global RNG state")
    row["global_rng_isolation"] = {
        "digest_before": rng_before, "digest_after": rng_after, "preserved": True,
    }
    return row


def _quantity_reading(
    h0: np.ndarray, h45: np.ndarray, s0: np.ndarray, s45: np.ndarray,
) -> dict[str, Any]:
    arrays = [np.asarray(value, dtype=np.float64) for value in (h0, h45, s0, s45)]
    if len({value.shape for value in arrays}) != 1 or not all(np.isfinite(value).all() for value in arrays):
        raise ValueError("B08 comparison quantity shape/nonfinite mismatch")
    h0, h45, s0, s45 = arrays
    i_h, i_s = h45 - h0, s45 - s0
    d0, d45 = h0 - s0, h45 - s45
    delta = i_h - i_s
    residual = delta - (d45 - d0)
    result = {
        "absolute": {
            "H0_per_world": h0.tolist(), "H0_mean": float(h0.mean()),
            "H45_per_world": h45.tolist(), "H45_mean": float(h45.mean()),
            "S0_per_world": s0.tolist(), "S0_mean": float(s0.mean()),
            "S45_per_world": s45.tolist(), "S45_mean": float(s45.mean()),
        },
        "self_gains": {
            "I_H_H45_minus_H0_per_world": i_h.tolist(), "I_H_mean": float(i_h.mean()),
            "I_S_S45_minus_S0_per_world": i_s.tolist(), "I_S_mean": float(i_s.mean()),
        },
        "package_gaps": {
            "D0_H0_minus_S0_per_world": d0.tolist(), "D0_mean": float(d0.mean()),
            "D45_H45_minus_S45_per_world": d45.tolist(), "D45_mean": float(d45.mean()),
        },
        "difference_of_self_gains": {
            "Delta_per_world": delta.tolist(), "Delta_mean": float(delta.mean()),
            "D45_minus_D0_per_world": (d45 - d0).tolist(),
            "identity_residual_per_world": residual.tolist(),
            "identity_max_abs_residual": float(np.abs(residual).max(initial=0.0)),
        },
    }
    return result


def compute_readings(
    current_panels: list[dict[str, Any]], records: list[LoadedAsset], test_ns: tuple[int, ...],
) -> dict[str, Any]:
    current = {(row["asset_key"], row["test_n"]): row for row in current_panels}
    sources = {record.spec.key: record for record in records}
    by_n = {}
    for n in test_ns:
        h0, s0 = current[("h6", n)], current[("set", n)]
        h45, s45 = sources["h6"].final_panels[n], sources["set"].final_panels[n]
        worlds = h0["world_seeds"]
        if any(row["world_seeds"] != worlds for row in (s0, h45, s45)):
            raise ValueError(f"B08 source join worlds differ at N={n}")
        quantities = {
            "J": _quantity_reading(h0["J"], h45["J"], s0["J"], s45["J"]),
        }
        for component in COMPONENTS:
            quantities[component] = _quantity_reading(
                h0["component_means"][component], h45["component_means"][component],
                s0["component_means"][component], s45["component_means"][component],
            )
        coverage = quantities["coverage_reward"]
        coverage["users_per_step"] = {
            "H0_mean": 50 * coverage["absolute"]["H0_mean"],
            "H45_mean": 50 * coverage["absolute"]["H45_mean"],
            "S0_mean": 50 * coverage["absolute"]["S0_mean"],
            "S45_mean": 50 * coverage["absolute"]["S45_mean"],
            "I_H_mean": 50 * coverage["self_gains"]["I_H_mean"],
            "I_S_mean": 50 * coverage["self_gains"]["I_S_mean"],
            "D0_mean": 50 * coverage["package_gaps"]["D0_mean"],
            "D45_mean": 50 * coverage["package_gaps"]["D45_mean"],
            "Delta_mean": 50 * coverage["difference_of_self_gains"]["Delta_mean"],
        }
        by_n[str(n)] = {"test_n": n, "world_seeds": worlds, "quantities": quantities}
    unseen = {}
    if 4 in test_ns and 8 in test_ns:
        for quantity in ("J", *COMPONENTS):
            unseen[quantity] = {}
            for field, path in {
                "H0_mean": ("absolute", "H0_mean"),
                "H45_mean": ("absolute", "H45_mean"),
                "S0_mean": ("absolute", "S0_mean"),
                "S45_mean": ("absolute", "S45_mean"),
                "I_H_mean": ("self_gains", "I_H_mean"),
                "I_S_mean": ("self_gains", "I_S_mean"),
                "D0_mean": ("package_gaps", "D0_mean"),
                "D45_mean": ("package_gaps", "D45_mean"),
                "Delta_mean": ("difference_of_self_gains", "Delta_mean"),
            }.items():
                unseen[quantity][field] = float(np.mean([
                    by_n[str(n)]["quantities"][quantity][path[0]][path[1]] for n in (4, 8)
                ]))
            if quantity == "coverage_reward":
                unseen[quantity]["users_per_step"] = {
                    field: 50 * value for field, value in unseen[quantity].items()
                    if field.endswith("_mean")
                }
    return {
        "reading_order": ["absolute", "self_gains", "package_gaps", "difference_of_self_gains"],
        "by_test_n": by_n, "U_equal_weight_N4_N8": unseen,
        "n6_kept_separate": by_n.get("6"),
        "scope": "two fixed trained-policy states; accounting identity, not causal decomposition",
    }


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "scripts" / "run_agent_count_initial_policy_b08.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b02/probe.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
    )


def _source_hashes() -> dict[str, str]:
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path) for path in _source_paths()}


def _input_identities(records: list[LoadedAsset]) -> dict[str, Any]:
    result = {}
    for record in records:
        panels = {}
        for n, identity in record.final_panel_identities.items():
            path = Path(identity["path"])
            panels[str(n)] = {"path": str(path), "exists": path.is_file(),
                              "bytes": path.stat().st_size if path.is_file() else None,
                              "sha256": file_sha256(path) if path.is_file() else None}
        summary_path = Path(record.summary_identity["path"])
        checkpoint = record.checkpoint
        result[record.spec.key] = {
            "summary": {"path": str(summary_path), "exists": summary_path.is_file(),
                        "bytes": summary_path.stat().st_size if summary_path.is_file() else None,
                        "sha256": file_sha256(summary_path) if summary_path.is_file() else None},
            "checkpoint00": {"path": str(checkpoint), "exists": checkpoint.is_file(),
                             "bytes": checkpoint.stat().st_size if checkpoint.is_file() else None,
                             "sha256": file_sha256(checkpoint) if checkpoint.is_file() else None},
            "final_panels": panels,
        }
    return result


def _expected_counts(eval_spec: EvalSpec, asset_count: int = len(ASSETS)) -> dict[str, int]:
    panels = asset_count * len(eval_spec.test_ns)
    team_steps = panels * eval_spec.eval_lanes * eval_spec.horizon
    return {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_calls": 0, "panels": panels,
        "evaluation_team_steps": team_steps,
        "evaluation_uav_steps": (
            asset_count * eval_spec.eval_lanes * eval_spec.horizon * sum(eval_spec.test_ns)
        ),
        "evaluation_episodes": panels * eval_spec.eval_lanes,
        "evaluation_resets": panels * eval_spec.eval_lanes,
        "batched_policy_step_calls": panels * eval_spec.horizon,
        "reused_final_evaluation_steps": 0,
    }


def run_study(
    out: Path, launch_sha: str, admission: dict[str, Any], checkpoint_paths: Mapping[str, Path],
    *, assets: tuple[AssetSpec, ...] = ASSETS, eval_spec: EvalSpec = DEFAULT_SPEC,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_sources: bool = True, command_start: float | None = None,
    evaluate_fn: Callable[..., dict[str, Any]] = evaluate_policy,
) -> int:
    out = Path(out)
    if out.name != TAG:
        raise ValueError(f"B08 output basename must be {TAG}")
    if (out / "summary.json").exists():
        raise ValueError("existing B08 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected_counts = _expected_counts(eval_spec, len(assets))
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": TAG, "direction": DIRECTION,
        "launch_sha": launch_sha, "admission": admission, "status": "validating_assets",
        "zero_fit": True, "failure": None, "spec": jsonable(vars(eval_spec)),
        "policy_stage": POLICY_STAGE, "world_panel_stage": WORLD_PANEL_STAGE,
        "prior_training_exposure": 0, "world_seed_base": WORLD_SEED_BASE,
        "assets": [], "panels": [], "readings": None,
        "counts": {key: 0 for key in expected_counts}, "expected_counts": expected_counts,
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
    active_row: dict[str, Any] | None = None
    active_filename: str | None = None
    publish("admitted")
    try:
        torch.set_num_threads(eval_spec.torch_threads)
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "object_id": OBJECT_ID, "tag": TAG,
            "spec": jsonable(vars(eval_spec)), "policy_stage": POLICY_STAGE,
            "world_panel_stage": WORLD_PANEL_STAGE, "prior_training_exposure": 0,
            "world_seed_base": WORLD_SEED_BASE, "assets": [jsonable(vars(a)) for a in assets],
        })
        records = load_assets(
            checkpoint_paths, assets=assets, summary_root=summary_root,
            committed_sources=committed_sources, eval_spec=eval_spec,
            restore_log_root=out / "restore_validation_logs",
        )
        summary["assets"] = [{
            "key": row.spec.key, "arm": row.spec.arm, "seed": row.spec.seed,
            "tag": row.spec.tag, "source_sha": row.spec.source_sha,
            "policy_stage": POLICY_STAGE, "initial_digest": row.spec.initial_digest,
            "summary": row.summary_identity,
            "checkpoint00": {"path": str(row.checkpoint),
                             "sha256": row.spec.checkpoint00_sha256,
                             "bytes": row.spec.checkpoint00_bytes},
            "checkpoint45_identity_only": {"sha256": row.spec.checkpoint45_sha256,
                                           "bytes": row.spec.checkpoint45_bytes,
                                           "loaded_or_evaluated": False},
            "final_panel_sources": row.final_panel_identities,
        } for row in records]
        summary["input_identities_before"] = _input_identities(records)
        publish("both checkpoint-00 assets and independent final arrays validated")

        def progress(
            steps: int, episodes: int, n: int, calls: int, resets: int,
        ) -> None:
            summary["counts"]["evaluation_team_steps"] += steps
            summary["counts"]["evaluation_uav_steps"] += steps * n
            summary["counts"]["evaluation_episodes"] += episodes
            summary["counts"]["evaluation_resets"] += resets
            summary["counts"]["batched_policy_step_calls"] += calls

        for record in records:
            for n in eval_spec.test_ns:
                active_filename = f"panel_{record.spec.key}_policy0_world45_n{n}.json"
                active_row = {
                    "status": "running", "asset_key": record.spec.key, "arm": record.spec.arm,
                    "seed": record.spec.seed, "policy_stage": POLICY_STAGE,
                    "prior_training_team_steps": 0, "world_panel_stage": WORLD_PANEL_STAGE,
                    "test_n": n,
                    "world_seeds": list(range(_world_seed(n), _world_seed(n) + eval_spec.eval_lanes)),
                }
                summary["panels"].append(active_row)
                write_json(out / active_filename, active_row)
                publish(f"{record.spec.key} checkpoint00 on world-panel45 N={n} starting")
                evaluated = evaluate_fn(record, n, out, eval_spec, progress)
                active_row.clear()
                active_row.update(evaluated)
                summary["counts"]["panels"] += 1
                write_json(out / active_filename, active_row)
                publish(f"{record.spec.key} checkpoint00 on world-panel45 N={n} complete")
                active_row = None
                active_filename = None
        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in summary["panels"]:
            grouped.setdefault(int(row["test_n"]), []).append(row)
        initial_matches = {}
        for n, rows in grouped.items():
            if len(rows) != 2:
                raise ValueError(f"B08 initial reset comparison lacks both policies at N={n}")
            matched = rows[0]["initial_world_digests"] == rows[1]["initial_world_digests"]
            initial_matches[str(n)] = {
                "both_policies_match": matched, "per_world": rows[0]["initial_world_digests"],
            }
            if not matched:
                raise ValueError(f"B08 environmental initial state/observation mismatch at N={n}")
        summary["initial_state_observation_matches"] = initial_matches
        summary["readings"] = compute_readings(summary["panels"], records, eval_spec.test_ns)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B08 source bytes changed during evaluation")
        summary["input_identities_after"] = _input_identities(records)
        summary["input_identities_unchanged"] = (
            summary["input_identities_before"] == summary["input_identities_after"]
        )
        if not summary["input_identities_unchanged"]:
            raise ValueError("B08 source/checkpoint inputs changed during evaluation")
        if summary["counts"] != expected_counts:
            raise ValueError(f"B08 exposure mismatch: {summary['counts']} != {expected_counts}")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        if active_row is not None and active_row.get("status") == "running":
            active_row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
            if active_filename is not None:
                write_json(out / active_filename, active_row)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if records:
            summary["input_identities_after"] = _input_identities(records)
            summary["input_identities_unchanged"] = (
                summary.get("input_identities_before") == summary["input_identities_after"]
            )
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
            "resources_unmeasured": ["peak_scratch_bytes"],
        }
        publish(summary["status"])
    return return_code
