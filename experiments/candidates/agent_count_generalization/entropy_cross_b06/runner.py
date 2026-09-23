"""Zero-fit crossing of four frozen SET policies over the A/B final-world panels."""
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
    reset_all,
    seed_rng,
    write_json,
)


OBJECT_ID = "s1_entropy_cross_panel_b06"
TAG = OBJECT_ID
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
REPLAY_ATOL = 1e-10
REPLAY_RTOL = 0.0
PANELS = {"A": 1_200_000, "B": 1_500_000}


@dataclass(frozen=True)
class CrossSpec:
    test_ns: tuple[int, ...] = (4, 6, 8)
    horizon: int = 500
    eval_lanes: int = 16
    torch_threads: int = 4


DEFAULT_SPEC = CrossSpec()


@dataclass(frozen=True)
class AssetSpec:
    key: str
    policy_pair: str
    historical_panel: str
    seed: int
    tag: str
    source_sha: str
    summary_sha256: str
    checkpoint_sha256: str
    checkpoint_bytes: int
    object_id: str
    cell_key: str
    lambda_l: float


ASSETS = (
    AssetSpec(
        "a_l05", "A", "A", 943201, "s1_action_law_b03_set_clip_s943201",
        "89486d32ea569728f39d6e21b53f8a7c8854e74c",
        "2621fc884d2d6a9ea909ee4f483b4df1c2d9d6f8767826ef730b952a360422e3",
        "03f4f070e30b34fb61cd45820f1579ebde185c9417468689bd0c2e7ef60c0a3b",
        20_968_771, "s1_action_law_b03", "set_clip", .05,
    ),
    AssetSpec(
        "a_l0", "A", "A", 943201, "s1_entropy_b04_set_zero_s943201",
        "f4762ac67f04675136367fcc566327f0bf78a086",
        "83a51d84d3c802944be6ef61321aa4a0c83471cabca556e4101bad83a756f293",
        "9a1143798aab2e41a2290987b7fbca9403ef2dfdb0076bc30e3afd945c7f1359",
        20_968_771, "s1_entropy_b04", "set_zero", 0.0,
    ),
    AssetSpec(
        "b_l05", "B", "B", 953201, "s1_entropy_b05_set_l05_s953201",
        "e2ea736457e0992fb53cf21aa775fd15da3d8231",
        "136d090b32a8c5fec1eefad5dbaaefa9155d44ce4335c7fb0f07585d36cff4c4",
        "98062b5b338b684219c43b5c9a3dc13bf176322a948c439294beee1d52ae477e",
        20_968_771, "s1_entropy_b05", "set_l05", .05,
    ),
    AssetSpec(
        "b_l0", "B", "B", 953201, "s1_entropy_b05_set_l0_s953201",
        "e2ea736457e0992fb53cf21aa775fd15da3d8231",
        "1e0ecb08f66d99687d6811aa41332d542d7c46057de2f383326ddf20c51b7c91",
        "bbe00968cc56481fbd74123a1fc92205d6b67f480e8ec0d36fec0a5e564d67d2",
        20_968_771, "s1_entropy_b05", "set_l0", 0.0,
    ),
)


@dataclass
class LoadedAsset:
    spec: AssetSpec
    checkpoint: Path
    summary: dict[str, Any]
    summary_identity: dict[str, Any]
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
        if not bool(torch.isfinite(value).all()):
            raise ValueError(f"nonfinite {label}")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _finite_tree(item, f"{label}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _finite_tree(item, f"{label}[{index}]")
    elif isinstance(value, (float, np.floating)) and not np.isfinite(value):
        raise ValueError(f"nonfinite {label}")


def _fit_spec(summary: dict[str, Any]) -> FitSpec:
    recorded = summary.get("spec")
    if not isinstance(recorded, dict):
        raise ValueError("B06 source summary lacks the training spec")
    fields = {}
    for key, default in vars(TRAINING_SPEC).items():
        if key not in recorded:
            raise ValueError(f"B06 source summary spec is missing {key}")
        fields[key] = tuple(recorded[key]) if isinstance(default, tuple) else recorded[key]
    return FitSpec(**fields)


def _historical_panel(summary: dict[str, Any], n: int) -> dict[str, Any]:
    matches = [
        row for row in summary.get("panels", [])
        if row.get("after_rollout") == 45 and row.get("test_n") == n
    ]
    if len(matches) != 1 or matches[0].get("status") != "complete":
        raise ValueError(f"B06 source lacks one complete final N={n} panel")
    return matches[0]


def _read_summary(
    asset: AssetSpec, *, summary_root: Path, committed_summaries: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    relative = Path("runs") / DIRECTION / asset.tag / "summary.json"
    working_path = summary_root / asset.tag / "summary.json"
    if committed_summaries:
        raw = subprocess.run(
            ["git", "-C", str(REPOSITORY_ROOT), "show", f"HEAD:{relative.as_posix()}"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        if working_path.read_bytes() != raw:
            raise ValueError(f"B06 committed/working summary bytes differ for {asset.key}")
        binding = "HEAD git blob plus identical working bytes"
    else:
        raw = working_path.read_bytes()
        binding = "pytest fixture bytes"
    digest = hashlib.sha256(raw).hexdigest()
    if digest != asset.summary_sha256:
        raise ValueError(f"B06 summary SHA-256 mismatch for {asset.key}")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"B06 summary is not an object for {asset.key}")
    return value, {
        "path": str(working_path), "sha256": digest, "bytes": len(raw), "binding": binding,
    }


def _checkpoint_record(summary: dict[str, Any]) -> dict[str, Any]:
    matches = [row for row in summary.get("checkpoints", []) if row.get("path") == "checkpoint_45.pt"]
    if len(matches) != 1:
        raise ValueError("B06 summary must bind exactly one checkpoint_45.pt")
    return matches[0]


def _validate_summary(asset: AssetSpec, summary: dict[str, Any], cross: CrossSpec) -> FitSpec:
    expected = {
        "direction": DIRECTION, "object_id": asset.object_id, "arm": "SET",
        "seed": asset.seed, "tag": asset.tag, "launch_sha": asset.source_sha,
        "status": "complete", "training_action_law": "clip",
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"B06 summary {asset.key} {key} identity mismatch")
    if summary.get("fit_started") is not True:
        raise ValueError(f"B06 source fit is incomplete for {asset.key}")
    cell = summary.get("cell", {})
    if cell.get("key") != asset.cell_key or cell.get("tag") != asset.tag:
        raise ValueError(f"B06 source cell identity mismatch for {asset.key}")
    if cell.get("seed") != asset.seed or cell.get("arm") != "SET" or cell.get("law") != "clip":
        raise ValueError(f"B06 source cell contract mismatch for {asset.key}")
    if "lambda_l" in cell and cell["lambda_l"] != asset.lambda_l:
        raise ValueError(f"B06 source cell coefficient mismatch for {asset.key}")
    config = summary.get("config", {})
    if config.get("lambda_l") != asset.lambda_l or config.get("seed") != asset.seed:
        raise ValueError(f"B06 source config coefficient/seed mismatch for {asset.key}")
    if config.get("count_arm") != "SET" or config.get("n_agents") != 6:
        raise ValueError(f"B06 source config package/roster mismatch for {asset.key}")
    fit = _fit_spec(summary)
    summary_architecture = {
        "hidden_size": fit.hidden_size,
        "n_heads": fit.n_heads,
        "n_encoder_layers": fit.n_layers,
        "n_decoder_layers": fit.n_layers,
        "ppo_epochs": fit.ppo_epochs,
        "sequence_batch_size": fit.sequence_batch_size,
        "coordinator_batch_size": fit.coordinator_batch_size,
    }
    if any(config.get(key) != value for key, value in summary_architecture.items()):
        raise ValueError(f"B06 source summary config/architecture mismatch for {asset.key}")
    if (fit.horizon, fit.eval_lanes, fit.torch_threads) != (
        cross.horizon, cross.eval_lanes, cross.torch_threads,
    ):
        raise ValueError(f"B06 source runtime dimensions mismatch for {asset.key}")
    for n in cross.test_ns:
        panel = _historical_panel(summary, n)
        expected_worlds = list(range(PANELS[asset.historical_panel] + 45_000 + 100 * n,
                                     PANELS[asset.historical_panel] + 45_000 + 100 * n + cross.eval_lanes))
        if panel.get("world_seeds") != expected_worlds:
            raise ValueError(f"B06 historical panel worlds mismatch for {asset.key} N={n}")
        for field in ("J", "scalar_returns"):
            values = np.asarray(panel.get(field), dtype=np.float64)
            if values.shape != (cross.eval_lanes,) or not np.isfinite(values).all():
                raise ValueError(f"B06 historical {field} payload invalid for {asset.key} N={n}")
        components = panel.get("component_means", {})
        if set(components) != set(COMPONENTS):
            raise ValueError(f"B06 historical components invalid for {asset.key} N={n}")
        if any(
            np.asarray(components[name]).shape != (cross.eval_lanes,)
            or not np.isfinite(np.asarray(components[name], dtype=np.float64)).all()
            for name in COMPONENTS
        ):
            raise ValueError(f"B06 historical component width invalid for {asset.key} N={n}")
    record = _checkpoint_record(summary)
    if record.get("bytes") != asset.checkpoint_bytes or record.get("sha256") != asset.checkpoint_sha256:
        raise ValueError(f"B06 committed checkpoint identity mismatch for {asset.key}")
    return fit


def _validate_payload(asset: AssetSpec, payload: Any, fit: FitSpec) -> dict[str, Any]:
    required = {"schema", "direction", "launch_sha", "rollout", "config", "modules", "normalizers", "usage"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError(f"B06 checkpoint payload keys mismatch for {asset.key}")
    for key, value in {
        "schema": 1, "direction": DIRECTION, "launch_sha": asset.source_sha, "rollout": 45,
    }.items():
        if payload.get(key) != value:
            raise ValueError(f"B06 checkpoint {key} mismatch for {asset.key}")
    config = payload.get("config")
    if not isinstance(config, dict):
        raise ValueError(f"B06 checkpoint config missing for {asset.key}")
    expected = {
        "count_arm": "SET", "seed": asset.seed, "n_agents": 6, "n_uavs": 6,
        "lambda_l": asset.lambda_l, "hidden_size": fit.hidden_size,
        "n_heads": fit.n_heads, "n_encoder_layers": fit.n_layers,
        "n_decoder_layers": fit.n_layers, "ppo_epochs": fit.ppo_epochs,
        "sequence_batch_size": fit.sequence_batch_size,
        "coordinator_batch_size": fit.coordinator_batch_size,
    }
    if any(config.get(key) != value for key, value in expected.items()):
        raise ValueError(f"B06 checkpoint config/architecture mismatch for {asset.key}")
    modules = payload.get("modules")
    if not isinstance(modules, dict) or not modules:
        raise ValueError(f"B06 checkpoint modules missing for {asset.key}")
    for module_name, state in modules.items():
        if not isinstance(state, dict) or not state:
            raise ValueError(f"B06 checkpoint module state invalid: {asset.key}.{module_name}")
        for tensor_name, tensor in state.items():
            if not torch.is_tensor(tensor) or tensor.numel() == 0:
                raise ValueError(f"B06 checkpoint tensor invalid: {asset.key}.{module_name}.{tensor_name}")
            if not tensor.dtype.is_floating_point and tensor.dtype not in (
                torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8, torch.bool,
            ):
                raise ValueError(f"B06 checkpoint tensor dtype invalid: {asset.key}.{module_name}.{tensor_name}")
            if tensor.dtype.is_floating_point and not bool(torch.isfinite(tensor).all()):
                raise ValueError(f"B06 checkpoint tensor nonfinite: {asset.key}.{module_name}.{tensor_name}")
    normalizers = payload.get("normalizers")
    if not isinstance(normalizers, dict) or set(normalizers) != set(NORMALIZERS):
        raise ValueError(f"B06 checkpoint normalizer set mismatch for {asset.key}")
    _finite_tree(normalizers, f"{asset.key}.normalizers")
    return config


def load_assets(
    checkpoint_paths: Mapping[str, Path], *, assets: tuple[AssetSpec, ...] = ASSETS,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_summaries: bool = True, cross: CrossSpec = DEFAULT_SPEC,
    restore_log_root: Path | None = None,
) -> list[LoadedAsset]:
    if set(checkpoint_paths) != {asset.key for asset in assets}:
        raise ValueError("B06 requires exactly four named checkpoint paths")
    loaded = []
    for asset in assets:
        summary, identity = _read_summary(
            asset, summary_root=Path(summary_root), committed_summaries=committed_summaries,
        )
        fit = _validate_summary(asset, summary, cross)
        checkpoint = Path(checkpoint_paths[asset.key])
        if checkpoint.stat().st_size != asset.checkpoint_bytes:
            raise ValueError(f"B06 checkpoint byte-size mismatch for {asset.key}")
        digest = file_sha256(checkpoint)
        if digest != asset.checkpoint_sha256:
            raise ValueError(f"B06 checkpoint SHA-256 mismatch for {asset.key}")
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        _validate_payload(asset, payload, fit)
        record = LoadedAsset(asset, checkpoint, summary, identity, payload, fit)
        log_root = (
            Path(restore_log_root) if restore_log_root is not None
            else checkpoint.parent / "restore_validation_logs"
        )
        _validate_restore_compatibility(record, cross, log_root)
        loaded.append(record)
    return loaded


def _make_eval_config(record: LoadedAsset, envs: list[Any], n: int) -> Any:
    config = make_config("SET", envs, record.spec.seed, record.fit_spec)
    coefficient = record.spec.lambda_l
    config.lambda_l = config.lambda_l_initial = config.lambda_l_final = coefficient
    config.use_entropy_annealing = False
    config.use_entropy_targets = False
    config.validate_config()
    rebuilt = config_dict(config)
    saved = record.payload["config"]
    allowed = {"n_agents", "n_uavs", "batch_size", "discriminator_batch_size"}
    differences = {
        key: (saved.get(key), rebuilt.get(key))
        for key in set(saved) | set(rebuilt)
        if saved.get(key) != rebuilt.get(key) and key not in allowed
    }
    if differences:
        raise ValueError(f"B06 rebuilt config changed policy fields: {differences}")
    if rebuilt["n_agents"] != n or rebuilt["n_uavs"] != n:
        raise ValueError("B06 rebuilt config has wrong N-specific runtime")
    historical = _historical_panel(record.summary, n)["config"]
    common_differences = {
        key: (historical.get(key), rebuilt.get(key))
        for key in rebuilt if historical.get(key) != rebuilt.get(key)
    }
    if common_differences:
        raise ValueError(f"B06 rebuilt config differs from historical panel: {common_differences}")
    if any(float(value) != coefficient for value in (
        config.lambda_l, config.lambda_l_initial, config.lambda_l_final,
    )) or config.use_entropy_annealing or config.use_entropy_targets:
        raise ValueError("B06 actual evaluation entropy contract changed")
    return config


def _validate_restore_compatibility(
    record: LoadedAsset, cross: CrossSpec, log_root: Path,
) -> None:
    """Strictly bind every N-specific target before any panel evaluation begins."""
    for n in cross.test_ns:
        world_seed = PANELS[record.spec.historical_panel] + 45_000 + 100 * n
        envs = make_envs(cross.eval_lanes, world_seed, n, cross.horizon)
        target = None
        try:
            config = _make_eval_config(record, envs, n)
            target = build_agent(config, str(log_root / record.spec.key / f"n{n}"))
            restore_checkpoint(target, record.payload)
        finally:
            for env in envs:
                env.close()
            del target


def evaluate_policy(
    record: LoadedAsset, panel: str, n: int, out: Path, cross: CrossSpec,
    progress: Callable[[int, int, int, int], None] | None = None,
) -> dict[str, Any]:
    world_seed = PANELS[panel] + 45_000 + 100 * n
    seed_rng(world_seed + 51)
    envs = make_envs(cross.eval_lanes, world_seed, n, cross.horizon)
    target, hooks = None, []
    try:
        config = _make_eval_config(record, envs, n)
        target = build_agent(config, str(out / "logs" / f"{record.spec.key}_on_{panel}_n{n}"))
        restore_checkpoint(target, record.payload)
        for lane in range(cross.eval_lanes):
            target.reset_env_state(lane)
        calls, hooks = optimizer_counts(target)
        model_before = digest_agent(target)
        normalizers_before = _normalizer_record(target)
        states, observations = reset_all(envs)
        initial = []
        for lane in range(cross.eval_lanes):
            initial.append({
                "world_seed": world_seed + lane,
                "state_sha256": _array_digest(states[lane]),
                "observation_sha256": _array_digest(observations[lane]),
            })
        steps = np.zeros(cross.eval_lanes, dtype=np.int64)
        dones = np.zeros(cross.eval_lanes, dtype=bool)
        returns = np.zeros(cross.eval_lanes, dtype=np.float64)
        components = {name: np.zeros(cross.eval_lanes, dtype=np.float64) for name in COMPONENTS}
        action_min, action_max = float("inf"), float("-inf")
        mapping_unchanged = True
        with torch.no_grad():
            for t in range(cross.horizon):
                actions, _, data = target.step(
                    states, observations, steps, dones, deterministic=True,
                    return_step_data=True, build_infos=False,
                )
                if progress is not None:
                    progress(0, 0, n, 1)
                finite((actions, data), "B06 deterministic policy output")
                if actions.shape != (cross.eval_lanes, n, 3) or actions.dtype != np.float32:
                    raise ValueError("B06 policy action shape/dtype mismatch")
                rng_before_diagnostics = _rng_digest()
                before = actions.copy()
                executed = np.clip(actions, -1.0, 1.0)
                mapping_unchanged &= np.array_equal(actions, before)
                if _rng_digest() != rng_before_diagnostics:
                    raise ValueError("B06 diagnostics consumed global RNG state")
                action_min = min(action_min, float(executed.min()))
                action_max = max(action_max, float(executed.max()))
                next_states, next_observations = [], []
                for lane, env in enumerate(envs):
                    obs, reward, terminated, truncated, info = env.step(executed[lane])
                    done = bool(terminated or truncated)
                    if progress is not None:
                        progress(1, int(done), n, 0)
                    parts = native_components(info, reward, n)
                    returns[lane] += reward
                    for name in COMPONENTS:
                        components[name][lane] += parts[name]
                    next_states.append(info["next_state"])
                    next_observations.append(obs)
                    dones[lane] = done
                states, observations = np.stack(next_states), np.stack(next_observations)
                steps += 1
                if dones.any() and (t != cross.horizon - 1 or not dones.all()):
                    raise ValueError("unexpected B06 terminal boundary")
        if not dones.all():
            raise ValueError("B06 evaluation missed fixed terminal boundary")
        means = {name: values / cross.horizon for name, values in components.items()}
        j = n * returns / cross.horizon
        if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6):
            raise ValueError("B06 native J/component identity failed")
        if any(calls.values()) or digest_agent(target) != model_before:
            raise ValueError("B06 evaluation changed weights/normalizers or optimized")
        if _normalizer_record(target) != normalizers_before:
            raise ValueError("B06 evaluation changed learned normalizer state")
        if not mapping_unchanged or action_min < -1.0 or action_max > 1.0:
            raise ValueError("B06 clipped mapping contract failed")
        return {
            "status": "complete", "asset_key": record.spec.key,
            "policy_pair": record.spec.policy_pair, "coefficient": record.spec.lambda_l,
            "evaluation_panel": panel, "test_n": n,
            "world_seeds": list(range(world_seed, world_seed + cross.eval_lanes)),
            "runtime_seed": world_seed + 51,
            "steps": cross.eval_lanes * cross.horizon, "episodes": cross.eval_lanes,
            "J": j.tolist(), "scalar_returns": returns.tolist(),
            "component_means": jsonable(means), "initial_world_digests": initial,
            "optimizer_calls": calls.copy(), "frozen_weights_and_normalizers": True,
            "parameter_normalizer_digest_before": model_before,
            "parameter_normalizer_digest_after": digest_agent(target),
            "normalizers_before": normalizers_before,
            "normalizers_after": _normalizer_record(target),
            "executed_action_bounds": {"minimum": action_min, "maximum": action_max},
            "policy_outputs_unchanged_by_mapping": mapping_unchanged,
            "diagnostics_rng_unchanged": True,
            "config": {**config_dict(config),
                       "lambda_l_initial": float(config.lambda_l_initial),
                       "lambda_l_final": float(config.lambda_l_final),
                       "use_entropy_annealing": bool(config.use_entropy_annealing),
                       "use_entropy_targets": bool(config.use_entropy_targets)},
        }
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        del target


def compare_diagonal(current: dict[str, Any], historical: dict[str, Any]) -> dict[str, Any]:
    if current["world_seeds"] != historical.get("world_seeds"):
        raise ValueError("B06 diagonal world addresses differ")
    fields = {"scalar_returns": (current["scalar_returns"], historical.get("scalar_returns")),
              "J": (current["J"], historical.get("J"))}
    for name in COMPONENTS:
        fields[f"component_means.{name}"] = (
            current["component_means"][name], historical.get("component_means", {}).get(name),
        )
    comparisons = {}
    accepted = True
    for name, (observed, expected) in fields.items():
        left, right = np.asarray(observed, dtype=np.float64), np.asarray(expected, dtype=np.float64)
        if left.shape != right.shape:
            raise ValueError(f"B06 diagonal {name} shape differs")
        difference = np.abs(left - right)
        close = np.isclose(left, right, atol=REPLAY_ATOL, rtol=REPLAY_RTOL)
        comparisons[name] = {
            "exact_equality": bool(np.array_equal(left, right)),
            "maximum_absolute_difference": float(difference.max(initial=0.0)),
            "within_fixed_tolerance": bool(close.all()),
            "per_world_absolute_difference": difference.tolist(),
        }
        accepted &= bool(close.all())
    result = {"atol": REPLAY_ATOL, "rtol": REPLAY_RTOL,
              "all_absolute_outputs_match": accepted, "fields": comparisons}
    return result


def _pair_difference(l0: dict[str, Any], l05: dict[str, Any]) -> dict[str, Any]:
    if l0["world_seeds"] != l05["world_seeds"]:
        raise ValueError("B06 within-panel policy worlds differ")
    j = np.asarray(l0["J"], dtype=np.float64) - np.asarray(l05["J"], dtype=np.float64)
    components = {}
    for name in COMPONENTS:
        delta = np.asarray(l0["component_means"][name], dtype=np.float64) - np.asarray(
            l05["component_means"][name], dtype=np.float64
        )
        components[name] = {"per_world": delta.tolist(), "mean": float(delta.mean())}
    return {
        "world_seeds": l0["world_seeds"], "J_l0_minus_l05_per_world": j.tolist(),
        "J_l0_minus_l05_mean": float(j.mean()),
        "world_signs": {"positive": int((j > 0).sum()), "zero": int((j == 0).sum()),
                        "negative": int((j < 0).sum())},
        "component_l0_minus_l05": components,
    }


def _rct(cells: Mapping[str, float]) -> dict[str, float]:
    a, x, y, z = (float(cells[key]) for key in ("a", "x", "y", "z"))
    r = (a + x - y - z) / 2
    c = (a + y - x - z) / 2
    t = a - x - y + z
    return {
        "a": a, "x": x, "y": y, "z": z, "R": r, "C": c, "T": t,
        "R_plus_C": r + c, "a_minus_z": a - z,
        "R_minus_C": r - c, "x_minus_y": x - y,
        "R_plus_C_identity_residual": (r + c) - (a - z),
        "R_minus_C_identity_residual": (r - c) - (x - y),
    }


def compute_contrasts(panels: list[dict[str, Any]], test_ns: tuple[int, ...]) -> dict[str, Any]:
    indexed = {(row["asset_key"], row["evaluation_panel"], row["test_n"]): row for row in panels}
    differences = {}
    cell_sources = {
        "a": ("a_l0", "a_l05", "A"), "x": ("a_l0", "a_l05", "B"),
        "y": ("b_l0", "b_l05", "A"), "z": ("b_l0", "b_l05", "B"),
    }
    for cell, (zero, l05, panel) in cell_sources.items():
        differences[cell] = {
            str(n): _pair_difference(indexed[(zero, panel, n)], indexed[(l05, panel, n)])
            for n in test_ns
        }
    by_n = {
        str(n): _rct({cell: differences[cell][str(n)]["J_l0_minus_l05_mean"]
                      for cell in cell_sources})
        for n in test_ns
    }
    unseen = _rct({
        cell: float(np.mean([
            differences[cell]["4"]["J_l0_minus_l05_mean"],
            differences[cell]["8"]["J_l0_minus_l05_mean"],
        ])) for cell in cell_sources
    }) if 4 in test_ns and 8 in test_ns else None
    n6_costs = {
        cell: {
            "J_l0_minus_l05_mean": differences[cell]["6"]["J_l0_minus_l05_mean"],
            "coverage_l0_minus_l05_mean": differences[cell]["6"][
                "component_l0_minus_l05"
            ]["coverage_reward"]["mean"],
        } for cell in cell_sources
    } if 6 in test_ns else None
    return {"cell_definitions": {key: list(value) for key, value in cell_sources.items()},
            "differences": differences, "by_test_n": by_n,
            "U_equal_weight_N4_N8": unseen, "n6_J_and_coverage_costs": n6_costs,
            "scope": "finite frozen-policy/panel contrasts; not causal shares or training variance"}


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "scripts" / "run_agent_count_entropy_cross_b06.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b02/probe.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
    )


def _source_hashes() -> dict[str, str]:
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path) for path in _source_paths()}


def _expected_counts(cross: CrossSpec, asset_count: int = len(ASSETS)) -> dict[str, int]:
    panels = asset_count * len(PANELS) * len(cross.test_ns)
    team_steps = panels * cross.eval_lanes * cross.horizon
    uav_steps = asset_count * len(PANELS) * cross.eval_lanes * cross.horizon * sum(cross.test_ns)
    return {"training_team_steps": 0, "optimizer_updates": 0, "panels": panels,
            "evaluation_team_steps": team_steps, "evaluation_episodes": panels * cross.eval_lanes,
            "uav_steps": uav_steps, "batched_policy_step_calls": panels * cross.horizon}


def _checkpoint_identities(records: list[LoadedAsset]) -> dict[str, dict[str, Any]]:
    identities = {}
    for record in records:
        exists = record.checkpoint.is_file()
        identities[record.spec.key] = {
            "path": str(record.checkpoint),
            "exists": exists,
            "bytes": record.checkpoint.stat().st_size if exists else None,
            "sha256": file_sha256(record.checkpoint) if exists else None,
        }
    return identities


def run_study(
    out: Path, launch_sha: str, admission: dict[str, Any], checkpoint_paths: Mapping[str, Path],
    *, assets: tuple[AssetSpec, ...] = ASSETS, cross: CrossSpec = DEFAULT_SPEC,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_summaries: bool = True, command_start: float | None = None,
    evaluate_fn: Callable[..., dict[str, Any]] = evaluate_policy,
) -> int:
    out = Path(out)
    if out.name != TAG:
        raise ValueError(f"B06 output basename must be {TAG}")
    if (out / "summary.json").exists():
        raise ValueError("existing B06 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected_counts = _expected_counts(cross, len(assets))
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": TAG, "direction": DIRECTION,
        "launch_sha": launch_sha, "admission": admission, "status": "validating_assets",
        "zero_fit": True, "failure": None, "spec": jsonable(vars(cross)),
        "panel_seed_bases": PANELS, "replay_tolerance": {"atol": REPLAY_ATOL, "rtol": REPLAY_RTOL},
        "assets": [], "panels": [], "contrasts": None,
        "counts": {key: 0 for key in expected_counts},
        "expected_counts": expected_counts,
        "source_hashes_before": _source_hashes(),
        "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                    "device": "cpu", "dtype": "float32", "torch_threads": cross.torch_threads},
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
        torch.set_num_threads(cross.torch_threads)
        write_json(out / "config.json", {
            "launch_sha": launch_sha,
            "object_id": OBJECT_ID,
            "tag": TAG,
            "spec": jsonable(vars(cross)),
            "panel_seed_bases": PANELS,
            "replay_tolerance": {"atol": REPLAY_ATOL, "rtol": REPLAY_RTOL},
            "assets": [jsonable(vars(asset)) for asset in assets],
        })
        records = load_assets(
            checkpoint_paths, assets=assets, summary_root=summary_root,
            committed_summaries=committed_summaries, cross=cross,
            restore_log_root=out / "restore_validation_logs",
        )
        summary["assets"] = [{
            "key": row.spec.key, "policy_pair": row.spec.policy_pair,
            "historical_panel": row.spec.historical_panel, "seed": row.spec.seed,
            "tag": row.spec.tag, "source_sha": row.spec.source_sha,
            "lambda_l": row.spec.lambda_l, "summary": row.summary_identity,
            "checkpoint": {"path": str(row.checkpoint), "sha256": row.spec.checkpoint_sha256,
                           "bytes": row.spec.checkpoint_bytes},
        } for row in records]
        summary["checkpoint_identities_before"] = _checkpoint_identities(records)
        publish("all four assets validated")

        def progress(steps: int, episodes: int, n: int, calls: int) -> None:
            summary["counts"]["evaluation_team_steps"] += steps
            summary["counts"]["evaluation_episodes"] += episodes
            summary["counts"]["uav_steps"] += steps * n
            summary["counts"]["batched_policy_step_calls"] += calls

        diagonal_jobs = [(row, row.spec.historical_panel, n) for row in records for n in cross.test_ns]
        off_jobs = [
            (row, "B" if row.spec.historical_panel == "A" else "A", n)
            for row in records for n in cross.test_ns
        ]
        for phase, jobs in (("diagonal", diagonal_jobs), ("off_diagonal", off_jobs)):
            for record, panel, n in jobs:
                active_filename = f"panel_{phase}_{record.spec.key}_on_{panel}_n{n}.json"
                active_row = {
                    "status": "running", "phase": phase, "asset_key": record.spec.key,
                    "policy_pair": record.spec.policy_pair,
                    "coefficient": record.spec.lambda_l, "evaluation_panel": panel,
                    "test_n": n,
                    "world_seeds": list(range(
                        PANELS[panel] + 45_000 + 100 * n,
                        PANELS[panel] + 45_000 + 100 * n + cross.eval_lanes,
                    )),
                }
                summary["panels"].append(active_row)
                write_json(out / active_filename, active_row)
                publish(f"{phase} {record.spec.key} on {panel} N={n} starting")
                evaluated = evaluate_fn(record, panel, n, out, cross, progress)
                active_row.clear()
                active_row.update(evaluated, phase=phase)
                summary["counts"]["panels"] += 1
                if phase == "diagonal":
                    active_row["historical_replay"] = compare_diagonal(
                        active_row, _historical_panel(record.summary, n)
                    )
                write_json(out / active_filename, active_row)
                publish(f"{phase} {record.spec.key} on {panel} N={n} complete")
                if phase == "diagonal" and not active_row["historical_replay"][
                    "all_absolute_outputs_match"
                ]:
                    active_row["status"] = "failed_replay"
                    active_row["failure"] = (
                        "historical diagonal absolute-output replay mismatch"
                    )
                    write_json(out / active_filename, active_row)
                    publish(f"{phase} {record.spec.key} on {panel} N={n} replay rejected")
                    raise ValueError("B06 historical diagonal absolute-output replay mismatch")
                active_row = None
                active_filename = None
            if phase == "diagonal":
                publish("all 12 historical diagonals accepted before off-diagonals")

        grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for row in summary["panels"]:
            grouped.setdefault((row["evaluation_panel"], row["test_n"]), []).append(row)
        initial_matches = {}
        for (panel, n), rows in grouped.items():
            if len(rows) != 4:
                raise ValueError("B06 initial-state comparison lacks four policies")
            reference = rows[0]["initial_world_digests"]
            matched = all(row["initial_world_digests"] == reference for row in rows[1:])
            initial_matches[f"{panel}_N{n}"] = {
                "all_four_policies_match": matched, "per_world": reference,
            }
            if not matched:
                raise ValueError(f"B06 reset state/observation mismatch at {panel} N={n}")
        summary["initial_state_observation_matches"] = initial_matches
        summary["contrasts"] = compute_contrasts(summary["panels"], cross.test_ns)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B06 source bytes changed during evaluation")
        summary["checkpoint_identities_after"] = _checkpoint_identities(records)
        summary["checkpoint_inputs_unchanged"] = (
            summary["checkpoint_identities_before"] == summary["checkpoint_identities_after"]
        )
        if not summary["checkpoint_inputs_unchanged"]:
            raise ValueError("B06 checkpoint input bytes changed during evaluation")
        if summary["counts"] != expected_counts:
            raise ValueError(f"B06 fixed exposure mismatch: {summary['counts']} != {expected_counts}")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        if active_row is not None and active_row.get("status") == "running":
            active_row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
            if active_filename is not None:
                write_json(out / active_filename, active_row)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
        if records:
            summary["checkpoint_identities_after"] = _checkpoint_identities(records)
            summary["checkpoint_inputs_unchanged"] = (
                summary.get("checkpoint_identities_before")
                == summary["checkpoint_identities_after"]
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
