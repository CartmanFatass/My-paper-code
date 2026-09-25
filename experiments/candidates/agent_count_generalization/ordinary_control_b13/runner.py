"""Evaluate four frozen final45 policies on one fixed N8/N6 native panel."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import resource
import subprocess
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
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC as TRAINING_SPEC,
    DIRECTION,
    FitSpec,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.initial_policy_b08.runner import (
    _finite_tree,
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
    seed_rng,
    write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import runner as b11


OBJECT_ID = "s1_ordinary_control_b13"
TAG = "s1_ordinary_control_b13_a02"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
POLICY_STAGE = 45
PRIOR_TRAINING_TEAM_STEPS = 360_000
EVALUATION_ORDER = (8, 6)
WORLD_SEED_BASES = {8: 1_645_800, 6: 1_645_600}
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
    seed: int
    tag: str
    source_sha: str
    object_id: str
    cell_key: str
    summary_sha256: str
    checkpoint_sha256: str
    checkpoint_bytes: int
    final_digest: str
    panel_sha256: tuple[str, str] | None = None
    trace_sha256: tuple[str, str] | None = None


ASSETS = (
    AssetSpec(
        "s1", "SET", 963201, "s1_training_condition_b11_t6_s963201",
        "dc1bc1f2718b1e4ff9510030ad26c287c76b03ac", "s1_training_condition_b11", "t6",
        "7046f2a8341f4dfb6049bf00aa97afafd34150e1840d94a66875a4936d437d63",
        "36f6bc8afbc414df1f84c2b414180821bf30e14b90d7f44928db35ce2ab74c0a",
        20_968_771, "9b160c67aa3aaa50403a6d860f7ccf8ba724e77e1251851fcc38b1d9fd19b1c6",
        (
            "7c79cc6556bcc9d0b285549704f4ee7edc6fe77130073f931b1b5bc494649573",
            "1335b9c1b6d89f30dd58cf35dc06c239dcb4ea79e37de606abc3e5def6ccd82a",
        ),
        (
            "cf3b2969f9994cf86862155eb98b670e39c50b4ed8cf7214d32ec38c10b4dee1",
            "287b9f6251a5e8dc39138266170a3cbfe0c9bd01a9ae3192fb1644cedcf32aa6",
        ),
    ),
    AssetSpec(
        "s2", "SET", 963401, "s1_training_recurrence_b12_t6_s963401",
        "762359c024f097827d0ef4f165635848de6bc667", "s1_training_recurrence_b12", "t6",
        "9765f6518fad19e3c3426ae1d181cb329343623cf3628b0fd23dee4714744564",
        "34987032207299209832a9fcaa6dcd807a3cc00e5b4682725a8b52d0ca89c8d3",
        20_968_771, "c1e408b4ae8eb55e02463ab641b16e02aa7ac165a9556a2275333ce1ab4e9ffb",
        (
            "4aa6151329f33ebd612843b997110449bc3713057f6a48931e7a25c64a900486",
            "1124284bc07601b4d4f4b2154946226ea8a3c9878b3734541e60e4677102ff06",
        ),
        (
            "2ed3e0ead1717f1e36dca74f515ffdbb4a36b7d1b7a7d5abf87c88dc43d2b7dd",
            "f621595ddcc21fc6e4772809a48d1a6d73ed3f691fafdcc0708f112dbc6401a9",
        ),
    ),
    AssetSpec(
        "h1", "H6", 942201, "s1_action_law_b03_h6_clip_s942201",
        "89486d32ea569728f39d6e21b53f8a7c8854e74c", "s1_action_law_b03", "h6_clip",
        "55a994c81f49a9b97b52efa4ddaea82579e1068ea3a7ddbd11c8b7645bf88921",
        "98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343",
        23_073_626, "6f773c16a0b33f8c59cf035cfbf51cc970a958730df9193a614fc472a296e57c",
    ),
    AssetSpec(
        "h2", "H6", 952201, "s1_bounded_package_b07_h6_l05_s952201",
        "0a9e3fde40659fdcc1d05922c9920c5c04b2ab23", "s1_bounded_package_b07", "h6_l05",
        "9d7f90523b74ea0fb4b9d7720086baefff13c22cdb41547c2b793764273b550a",
        "6d71f3023e5593a801b4d618f7eece93df1a15575f8a71d769566190ba6498df",
        23_073_626, "ea1de5234aba1683f182b6f36a3260ecf8fdd68779df0e313a6bc040b9458c1d",
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
    reference_panels: dict[int, dict[str, Any]]
    reference_traces: dict[int, dict[str, np.ndarray]]
    reference_identities: dict[int, dict[str, Any]]
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


def _world_seed(n: int) -> int:
    try:
        return WORLD_SEED_BASES[int(n)]
    except KeyError as exc:
        raise ValueError(f"B13 has no world panel for N={n}") from exc


def _config_record(config: Any) -> dict[str, Any]:
    return {
        **config_dict(config),
        "lambda_l_initial": float(config.lambda_l_initial),
        "lambda_l_final": float(config.lambda_l_final),
        "use_entropy_annealing": bool(config.use_entropy_annealing),
        "use_entropy_targets": bool(config.use_entropy_targets),
    }


def _read_bound_bytes(
    path: Path, expected_sha256: str, *, relative: Path, committed: bool,
    repository_root: Path = REPOSITORY_ROOT,
) -> tuple[bytes, dict[str, Any]]:
    path = Path(path)
    repository_root = Path(repository_root)
    if committed:
        locator = f"HEAD:{relative.as_posix()}"
        raw = subprocess.run(
            ["git", "-C", str(repository_root), "show", locator],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        working_present = path.is_file()
        working_raw = path.read_bytes() if working_present else None
        if working_raw is not None and working_raw != raw:
            raise ValueError(f"B13 committed/working source bytes differ: {relative}")
        binding = (
            "authoritative HEAD git blob plus identical working bytes"
            if working_present else "authoritative HEAD git blob; working file absent from sparse checkout"
        )
        authoritative_source = "git_blob"
    else:
        working_raw = path.read_bytes()
        working_present = True
        raw = working_raw
        locator = None
        binding = "pytest fixture bytes"
        authoritative_source = "working_file"
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"B13 source SHA-256 mismatch: {relative}")
    return raw, {
        "path": str(path), "working_path": str(path), "working_present": working_present,
        "working_bytes": len(working_raw) if working_raw is not None else None,
        "working_sha256": (
            hashlib.sha256(working_raw).hexdigest() if working_raw is not None else None
        ),
        "repository_root": str(repository_root), "relative_path": relative.as_posix(),
        "git_locator": locator, "authoritative_source": authoritative_source,
        "committed": bool(committed), "sha256": digest, "bytes": len(raw),
        "binding": binding,
    }


def _read_bound_json(
    path: Path, expected_sha256: str, *, relative: Path, committed: bool,
    repository_root: Path = REPOSITORY_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw, identity = _read_bound_bytes(
        path, expected_sha256, relative=relative, committed=committed,
        repository_root=repository_root,
    )
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"B13 source JSON is not an object: {relative}")
    return value, identity


def _read_bound_npz(
    path: Path, expected_sha256: str, *, relative: Path, committed: bool,
    repository_root: Path = REPOSITORY_ROOT,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    raw, identity = _read_bound_bytes(
        path, expected_sha256, relative=relative, committed=committed,
        repository_root=repository_root,
    )
    with np.load(io.BytesIO(raw), allow_pickle=False) as source:
        arrays = {name: source[name].copy() for name in source.files}
    return arrays, identity


def _fit_spec(summary: dict[str, Any]) -> FitSpec:
    source = summary.get("spec")
    if not isinstance(source, dict):
        raise ValueError("B13 source summary lacks training spec")
    fields = {}
    for key, default in vars(TRAINING_SPEC).items():
        if key not in source:
            raise ValueError(f"B13 source spec missing {key}")
        fields[key] = tuple(source[key]) if isinstance(default, tuple) else source[key]
    return FitSpec(**fields)


def _validate_summary(asset: AssetSpec, summary: dict[str, Any], fit: FitSpec) -> None:
    expected = {
        "schema": 1, "direction": DIRECTION, "object_id": asset.object_id,
        "tag": asset.tag, "arm": asset.arm, "seed": asset.seed,
        "launch_sha": asset.source_sha, "status": "complete",
    }
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError(f"B13 source summary identity mismatch for {asset.key}")
    cell = summary.get("cell", {})
    if cell.get("key") != asset.cell_key or cell.get("arm") != asset.arm \
            or cell.get("law") != "clip" or cell.get("seed") != asset.seed:
        raise ValueError(f"B13 source cell mismatch for {asset.key}")
    if summary.get("fit_started") is not True or summary.get("final_parameter_normalizer_digest") != asset.final_digest:
        raise ValueError(f"B13 incomplete source fit/final digest mismatch for {asset.key}")
    if (fit.train_n, fit.horizon, fit.rollouts, fit.hidden_size, fit.n_heads, fit.n_layers,
            fit.ppo_epochs, fit.sequence_batch_size, fit.coordinator_batch_size) != (
            6, 500, 45, 256, 8, 2, 15, 32, 1280):
        raise ValueError(f"B13 source training spec mismatch for {asset.key}")
    config = summary.get("config", {})
    expected_config = {
        "count_arm": asset.arm, "seed": asset.seed, "n_agents": 6, "n_uavs": 6,
        "n_users": 50, "num_envs": 16, "rollout_length": 500, "episode_length": 500,
        "k": 10, "state_dim": 133, "obs_dim": 104, "action_dim": 3,
        "hidden_size": 256, "n_heads": 8, "n_encoder_layers": 2,
        "n_decoder_layers": 2, "ppo_epochs": 15, "sequence_batch_size": 32,
        "coordinator_batch_size": 1280, "policy_interruption_mode": "off",
        "use_central_snapshot_in_flat_actor": asset.arm == "SET", "lambda_l": .05,
    }
    if any(config.get(key) != value for key, value in expected_config.items()):
        raise ValueError(f"B13 source config mismatch for {asset.key}")
    checkpoints = {row.get("path"): row for row in summary.get("checkpoints", [])}
    final = checkpoints.get("checkpoint_45.pt")
    if final is None or final.get("sha256") != asset.checkpoint_sha256 \
            or final.get("bytes") != asset.checkpoint_bytes:
        raise ValueError(f"B13 source checkpoint record mismatch for {asset.key}")


def _validate_payload(asset: AssetSpec, payload: Any, summary: dict[str, Any]) -> None:
    required = {"schema", "direction", "launch_sha", "rollout", "config", "modules", "normalizers", "usage"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError(f"B13 checkpoint payload keys mismatch for {asset.key}")
    expected = {
        "schema": 1, "direction": DIRECTION, "launch_sha": asset.source_sha,
        "rollout": POLICY_STAGE,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise ValueError(f"B13 checkpoint identity/stage mismatch for {asset.key}")
    saved_config = payload.get("config")
    source_config = summary["config"]
    if not isinstance(saved_config, dict) or set(saved_config) != set(config_dict(type("C", (), source_config)())):
        # Historical save_checkpoint stores exactly config_dict, not the later summary-only fields.
        expected_keys = set(config_dict(type("C", (), source_config)()))
        if not isinstance(saved_config, dict) or set(saved_config) != expected_keys:
            raise ValueError(f"B13 checkpoint config fields mismatch for {asset.key}")
    if any(saved_config.get(key) != source_config.get(key) for key in saved_config):
        raise ValueError(f"B13 checkpoint/source config mismatch for {asset.key}")
    expected_modules = (
        {"skill_coordinator", "skill_discoverer", "team_discriminator", "individual_discriminator"}
        if asset.arm == "H6" else {"skill_coordinator", "skill_discoverer"}
    )
    modules = payload.get("modules")
    if not isinstance(modules, dict) or set(modules) != expected_modules:
        raise ValueError(f"B13 checkpoint module set mismatch for {asset.key}")
    for module_name, state in modules.items():
        if not isinstance(state, dict) or not state:
            raise ValueError(f"B13 checkpoint module state invalid: {asset.key}.{module_name}")
        for tensor_name, tensor in state.items():
            if not torch.is_tensor(tensor) or tensor.numel() == 0:
                raise ValueError(f"B13 checkpoint tensor invalid: {module_name}.{tensor_name}")
            if tensor.dtype.is_floating_point and not bool(torch.isfinite(tensor).all()):
                raise ValueError(f"B13 checkpoint tensor nonfinite: {module_name}.{tensor_name}")
    normalizers = payload.get("normalizers")
    if not isinstance(normalizers, dict) or set(normalizers) != set(NORMALIZERS):
        raise ValueError(f"B13 checkpoint normalizer set mismatch for {asset.key}")
    _finite_tree(normalizers, f"{asset.key}.normalizers")
    if payload.get("usage") != "Evaluation weights; no training resume contract or optimizer restoration.":
        raise ValueError(f"B13 checkpoint is not the evaluation-only payload for {asset.key}")


def _load_reference(
    asset: AssetSpec, n: int, run_root: Path, relative_root: Path, committed: bool,
    summary: dict[str, Any], eval_spec: EvalSpec,
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, Any]]:
    if asset.panel_sha256 is None or asset.trace_sha256 is None:
        raise ValueError(f"B13 SET source lacks reproduction bindings for {asset.key}")
    index = EVALUATION_ORDER.index(n)
    panel_path = run_root / f"panel_45_n{n}.json"
    panel, panel_identity = _read_bound_json(
        panel_path, asset.panel_sha256[index], relative=relative_root / panel_path.name,
        committed=committed,
    )
    matches = [
        row for row in summary.get("panels", [])
        if row.get("after_rollout") == POLICY_STAGE and row.get("test_n") == n
    ]
    if len(matches) != 1 or matches[0] != panel:
        raise ValueError(f"B13 source summary/panel disagreement for {asset.key} N={n}")
    worlds = list(range(_world_seed(n), _world_seed(n) + eval_spec.eval_lanes))
    if panel.get("status") != "complete" or panel.get("world_seeds") != worlds \
            or panel.get("steps") != eval_spec.eval_lanes * eval_spec.horizon \
            or panel.get("episodes") != eval_spec.eval_lanes or panel.get("resets") != eval_spec.eval_lanes:
        raise ValueError(f"B13 source panel exposure mismatch for {asset.key} N={n}")
    if panel.get("execution_law") != "clip" or panel.get("frozen_weights_and_normalizers") is not True \
            or panel.get("training_storage_calls") != 0 or any(panel.get("optimizer_calls", {}).values()):
        raise ValueError(f"B13 source panel evaluation contract mismatch for {asset.key} N={n}")
    trace_path = run_root / f"trace_45_n{n}.npz"
    trace, trace_identity = _read_bound_npz(
        trace_path, asset.trace_sha256[index], relative=relative_root / trace_path.name,
        committed=committed,
    )
    trace_record = panel.get("trace", {})
    if trace_record.get("sha256") != trace_identity["sha256"] \
            or trace_record.get("bytes") != trace_identity["bytes"]:
        raise ValueError(f"B13 source trace identity mismatch for {asset.key} N={n}")
    expected_names = set(b11._new_trace(eval_spec, n)) | {"initial_states", "initial_observations"}
    if set(trace) != expected_names:
        raise ValueError(f"B13 source trace schema mismatch for {asset.key} N={n}")
    return panel, trace, {"panel": panel_identity, "trace": trace_identity}


def load_assets(
    checkpoint_paths: Mapping[str, Path], *, assets: tuple[AssetSpec, ...] = ASSETS,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_sources: bool = True, eval_spec: EvalSpec = DEFAULT_SPEC,
    restore_log_root: Path | None = None, construction_seed: int = 0,
) -> list[LoadedAsset]:
    if tuple(asset.key for asset in assets) != ("s1", "s2", "h1", "h2"):
        raise ValueError("B13 asset execution order must be S1, S2, H1, H2")
    if set(checkpoint_paths) != {asset.key for asset in assets}:
        raise ValueError("B13 requires exactly four explicit final45 checkpoint paths")
    if eval_spec.test_ns != EVALUATION_ORDER or eval_spec.horizon != 500 or eval_spec.eval_lanes != 32:
        raise ValueError("B13 fixed evaluation contract is N8 then N6, horizon500, 32 lanes")
    loaded = []
    for asset in assets:
        run_root = Path(summary_root) / asset.tag
        relative_root = Path("runs") / DIRECTION / asset.tag
        summary, summary_identity = _read_bound_json(
            run_root / "summary.json", asset.summary_sha256,
            relative=relative_root / "summary.json", committed=committed_sources,
        )
        fit = _fit_spec(summary)
        _validate_summary(asset, summary, fit)
        checkpoint = Path(checkpoint_paths[asset.key])
        if not checkpoint.is_file() or checkpoint.stat().st_size != asset.checkpoint_bytes:
            raise ValueError(f"B13 checkpoint byte-size mismatch for {asset.key}")
        if file_sha256(checkpoint) != asset.checkpoint_sha256:
            raise ValueError(f"B13 checkpoint SHA-256 mismatch for {asset.key}")
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        _validate_payload(asset, payload, summary)
        panels, traces, identities = {}, {}, {}
        if asset.arm == "SET":
            for n in eval_spec.test_ns:
                panels[n], traces[n], identities[n] = _load_reference(
                    asset, n, run_root, relative_root, committed_sources, summary, eval_spec,
                )
        record = LoadedAsset(
            asset, checkpoint, summary, summary_identity, payload, fit,
            panels, traces, identities, {},
        )
        if restore_log_root is not None:
            record.restore_validation = _strict_restore_all_ns(
                record, eval_spec, Path(restore_log_root), construction_seed,
            )
        loaded.append(record)
    return loaded


def _make_eval_config(record: LoadedAsset, envs: list[Any], n: int) -> Any:
    config = make_config(record.spec.arm, envs, record.spec.seed, record.fit_spec)
    source = record.summary["config"]
    if "lambda_l_initial" in source:
        config.lambda_l = float(source["lambda_l"])
        config.lambda_l_initial = float(source["lambda_l_initial"])
        config.lambda_l_final = float(source["lambda_l_final"])
        config.use_entropy_annealing = bool(source["use_entropy_annealing"])
        config.use_entropy_targets = bool(source["use_entropy_targets"])
        config.validate_config()
    rebuilt = _config_record(config)
    allowed = {
        "n_agents", "n_uavs", "num_envs", "batch_size", "discriminator_batch_size",
        "high_level_buffer_size",
    }
    changed = {
        key: (source.get(key), rebuilt.get(key))
        for key in source if key not in allowed and source.get(key) != rebuilt.get(key)
    }
    if changed:
        raise ValueError(f"B13 rebuilt config changed original policy fields for {record.spec.key}: {changed}")
    if (rebuilt["n_agents"], rebuilt["n_uavs"], rebuilt["num_envs"]) != (n, n, len(envs)):
        raise ValueError(f"B13 rebuilt config has wrong roster/lanes for {record.spec.key} N={n}")
    expected_changed = {
        "num_envs", "batch_size", "discriminator_batch_size", "high_level_buffer_size",
    }
    if n != int(source["n_agents"]):
        expected_changed.update(("n_agents", "n_uavs"))
    observed_changed = {key for key in allowed if source.get(key) != rebuilt.get(key)}
    if observed_changed != expected_changed:
        raise ValueError(
            f"B13 constructor differences are not exactly roster/lanes for {record.spec.key}: "
            f"{sorted(observed_changed)}"
        )
    return config


def _assert_native_envs(envs: list[Any], n: int) -> None:
    for env in envs:
        native = env.env.env
        if int(native.n_uavs) != n or int(native.n_users) != 50 \
                or int(native.max_connections) != 10 or float(native.min_sinr) != 0.0:
            raise ValueError("B13 native N/c10/SINR contract changed")


def _strict_restore_all_ns(
    record: LoadedAsset, eval_spec: EvalSpec, log_root: Path, construction_seed: int,
) -> dict[int, dict[str, Any]]:
    evidence = {}
    with preserve_rng():
        for n in eval_spec.test_ns:
            seed_rng(int(construction_seed))
            envs = make_envs(eval_spec.eval_lanes, _world_seed(n), n, eval_spec.horizon)
            target = None
            try:
                _assert_native_envs(envs, n)
                config = _make_eval_config(record, envs, n)
                target = build_agent(config, str(log_root / record.spec.key / f"n{n}"))
                restore_checkpoint(target, record.payload)
                observed = digest_agent(target)
                if observed != record.spec.final_digest:
                    raise ValueError(
                        f"B13 strict restored digest mismatch for {record.spec.key} N={n}"
                    )
                if np.any(target.rollout_buffer.env_lengths):
                    raise ValueError("B13 strict restore target has nonempty rollout storage")
                evidence[n] = {
                    "test_n": n, "restored_digest": observed,
                    "module_names": sorted(record.payload["modules"]),
                    "normalizer_names": sorted(record.payload["normalizers"]),
                    "rollout_storage_env_lengths": target.rollout_buffer.env_lengths.tolist(),
                    "config": _config_record(config),
                }
            finally:
                for env in envs:
                    env.close()
                del target
    return evidence


class _InferenceCounter:
    """Read-only hooks for actual coordinator and autoregressive decoder work."""

    def __init__(self, agent: Any, arm: str, n: int):
        self.arm, self.n = arm, int(n)
        self.data = {
            "coordinator_batched_calls": 0, "coordinator_rows": 0,
            "coordinator_batch_sizes": [], "decoder_team_calls": 0,
            "decoder_team_rows": 0, "decoder_individual_calls": 0,
            "decoder_individual_rows": 0, "team_selections": 0,
            "individual_selections": 0,
            "team_choice_counts": [0] * int(agent.config.n_Z),
            "individual_choice_counts": [0] * int(agent.config.n_z),
            "set_snapshot_refresh_steps": 0, "set_snapshot_lane_refreshes": 0,
        }
        self.handles = [
            agent.skill_coordinator.encoder.register_forward_hook(self._coordinator_hook),
            agent.skill_coordinator.skill_decoder.register_forward_hook(
                self._decoder_hook, with_kwargs=True,
            ),
        ]

    def _coordinator_hook(self, _module: Any, args: tuple[Any, ...], _output: Any) -> None:
        rows = int(args[0].shape[0])
        self.data["coordinator_batched_calls"] += 1
        self.data["coordinator_rows"] += rows
        self.data["coordinator_batch_sizes"].append(rows)

    def _decoder_hook(
        self, _module: Any, args: tuple[Any, ...], kwargs: dict[str, Any], _output: Any,
    ) -> None:
        rows = int(args[0].shape[0])
        if kwargs.get("step") is None:
            self.data["decoder_team_calls"] += 1
            self.data["decoder_team_rows"] += rows
        else:
            self.data["decoder_individual_calls"] += 1
            self.data["decoder_individual_rows"] += rows

    def observe_choices(self, data: dict[str, Any]) -> None:
        selected = np.asarray(data["skill_changed"], dtype=bool)
        teams = np.asarray(data["team_skills"], dtype=np.int64)[selected]
        individuals = np.asarray(data["agent_skills"], dtype=np.int64)[selected]
        self.data["team_selections"] += int(teams.size)
        self.data["individual_selections"] += int(individuals.size)
        for value, count in enumerate(np.bincount(teams, minlength=len(self.data["team_choice_counts"]))):
            self.data["team_choice_counts"][value] += int(count)
        for value, count in enumerate(np.bincount(
            individuals.reshape(-1), minlength=len(self.data["individual_choice_counts"]),
        )):
            self.data["individual_choice_counts"][value] += int(count)
        if self.arm == "SET":
            self.data["set_snapshot_refresh_steps"] += int(selected.any())
            self.data["set_snapshot_lane_refreshes"] += int(selected.sum())

    def finish(self, eval_spec: EvalSpec) -> dict[str, Any]:
        expected_calls = eval_spec.horizon // 10
        expected_rows = expected_calls * eval_spec.eval_lanes
        expected = {
            "coordinator_batched_calls": expected_calls,
            "coordinator_rows": expected_rows,
            "decoder_team_calls": expected_calls,
            "decoder_team_rows": expected_rows,
            "decoder_individual_calls": expected_calls * self.n,
            "decoder_individual_rows": expected_rows * self.n,
            "team_selections": expected_rows,
            "individual_selections": expected_rows * self.n,
        }
        if any(self.data[key] != value for key, value in expected.items()) \
                or self.data["coordinator_batch_sizes"] != [eval_spec.eval_lanes] * expected_calls:
            raise ValueError(f"B13 incomplete coordinator/decoder counts: {self.data} != {expected}")
        if sum(self.data["team_choice_counts"]) != expected_rows \
                or sum(self.data["individual_choice_counts"]) != expected_rows * self.n:
            raise ValueError("B13 selection histograms do not account for every choice")
        if self.arm == "SET" and (
            self.data["set_snapshot_refresh_steps"] != expected_calls
            or self.data["set_snapshot_lane_refreshes"] != expected_rows
        ):
            raise ValueError("B13 SET held-snapshot refresh count changed")
        result = dict(self.data)
        if self.arm != "SET":
            result["set_snapshot_refresh_steps"] = None
            result["set_snapshot_lane_refreshes"] = None
        return result

    def close(self) -> None:
        for handle in self.handles:
            handle.remove()


def _array_comparison(actual: Any, expected: Any, *, exact: bool) -> dict[str, Any]:
    left, right = np.asarray(actual), np.asarray(expected)
    if left.shape != right.shape:
        return {"match": False, "actual_shape": list(left.shape), "expected_shape": list(right.shape),
                "max_abs_difference": None}
    if exact:
        match = bool(np.array_equal(left, right))
        rule = "exact array equality"
    else:
        match = bool(np.allclose(left, right, atol=ATOL, rtol=RTOL))
        rule = f"numpy allclose atol={ATOL} rtol={RTOL}"
    if np.issubdtype(left.dtype, np.number) and np.issubdtype(right.dtype, np.number):
        difference = np.abs(left.astype(np.float64) - right.astype(np.float64))
        maximum = float(difference.max(initial=0.0))
    else:
        maximum = 0.0 if match else 1.0
    return {
        "match": match, "shape": list(left.shape), "max_abs_difference": maximum,
        "rule": rule,
    }


def compare_set_reproduction(
    row: dict[str, Any], trace: Mapping[str, np.ndarray], record: LoadedAsset, n: int,
) -> dict[str, Any]:
    reference = record.reference_panels[n]
    if row["world_seeds"] != reference.get("world_seeds"):
        raise ValueError(f"B13 SET reproduction world identities differ for {record.spec.key} N={n}")
    arrays = {
        "J": _array_comparison(row["J"], reference["J"], exact=False),
        "scalar_returns": _array_comparison(
            row["scalar_returns"], reference["scalar_returns"], exact=False,
        ),
    }
    for name in COMPONENTS:
        arrays[f"component_means.{name}"] = _array_comparison(
            row["component_means"][name], reference["component_means"][name], exact=False,
        )
    trace_checks = {}
    reference_trace = record.reference_traces[n]
    if set(trace) != set(reference_trace):
        raise ValueError(f"B13 SET reproduction trace schema differs for {record.spec.key} N={n}")
    for name in trace:
        array = np.asarray(trace[name])
        exact = name in {"initial_states", "initial_observations"} or not np.issubdtype(
            array.dtype, np.floating,
        )
        trace_checks[name] = _array_comparison(trace[name], reference_trace[name], exact=exact)
    result = {
        "atol": ATOL, "rtol": RTOL,
        "continuous_rule": "numpy allclose over CPU float32 outputs accumulated in float64",
        "exact_rule": (
            "numpy array_equal for initial_states, initial_observations, and every integer/boolean trace"
        ),
        "panel_arrays": arrays, "numeric_trace_arrays": trace_checks,
        "source_identities": record.reference_identities[n],
    }
    result["all_match"] = all(item["match"] for item in (*arrays.values(), *trace_checks.values()))
    return result


def evaluate_policy(
    record: LoadedAsset, n: int, out: Path, eval_spec: EvalSpec,
    construction_seed: int,
    progress: Callable[[int, int, int, int, int], None] | None = None,
) -> dict[str, Any]:
    world_seed = _world_seed(n)
    rng_before = _rng_digest()
    row: dict[str, Any] = {}
    trace: dict[str, np.ndarray] | None = None
    with preserve_rng():
        seed_rng(int(construction_seed))
        envs = make_envs(eval_spec.eval_lanes, world_seed, n, eval_spec.horizon)
        _assert_native_envs(envs, n)
        target, counter, hooks = None, None, []
        original_store = None
        storage_calls = 0
        try:
            config = _make_eval_config(record, envs, n)
            target = build_agent(config, str(out / "evaluation_logs" / f"{record.spec.key}_n{n}"))
            restore_checkpoint(target, record.payload)
            target.train(False)
            for lane in range(eval_spec.eval_lanes):
                target.reset_env_state(lane)
            calls, hooks = optimizer_counts(target)
            before = digest_agent(target)
            if before != record.spec.final_digest:
                raise ValueError(f"B13 restored final digest mismatch for {record.spec.key} N={n}")
            normalizers_before = _normalizer_record(target)
            runtime_before = runtime_state_digest(target)
            original_store = target.store_transition_batch

            def reject_store(_target: Any, *args: Any, **kwargs: Any) -> None:
                nonlocal storage_calls
                storage_calls += 1
                raise ValueError("B13 evaluation attempted training storage")

            target.store_transition_batch = MethodType(reject_store, target)
            counter = _InferenceCounter(target, record.spec.arm, n)
            # The caller seed affects only overwritten construction state.  Runtime
            # evaluation keeps the original fixed per-panel RNG address.
            seed_rng(world_seed + 51)
            pairs = []
            for env in envs:
                pairs.append(env.reset())
                if progress is not None:
                    progress(0, 0, n, 0, 1)
            states = np.stack([info["state"] for observation, info in pairs])
            observations = np.stack([observation for observation, info in pairs])
            steps = np.zeros(eval_spec.eval_lanes, dtype=np.int64)
            dones = np.zeros(eval_spec.eval_lanes, dtype=bool)
            returns = np.zeros(eval_spec.eval_lanes, dtype=np.float64)
            sums = {name: np.zeros(eval_spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
            trace = b11._new_trace(eval_spec, n)
            trace["initial_states"] = states.copy()
            trace["initial_observations"] = observations.copy()
            action_min, action_max = float("inf"), float("-inf")
            with torch.no_grad():
                for t in range(eval_spec.horizon):
                    raw_actions, _, data = target.step(
                        states, observations, steps, dones, deterministic=True,
                        return_step_data=True, build_infos=False,
                    )
                    if progress is not None:
                        progress(0, 0, n, 1, 0)
                    finite((raw_actions, data), "B13 deterministic policy output")
                    if raw_actions.shape != (eval_spec.eval_lanes, n, 3) or raw_actions.dtype != np.float32:
                        raise ValueError("B13 action shape/dtype mismatch")
                    counter.observe_choices(data)
                    raw_before = raw_actions.copy()
                    executed = map_training_actions(raw_actions, "clip")
                    if not np.array_equal(raw_actions, raw_before):
                        raise ValueError("B13 clip changed raw policy output")
                    action_min = min(action_min, float(executed.min()))
                    action_max = max(action_max, float(executed.max()))
                    next_states, next_observations = [], []
                    for lane, env in enumerate(envs):
                        observation, reward, terminated, truncated, info = env.step(executed[lane])
                        done = bool(terminated or truncated)
                        if progress is not None:
                            progress(1, int(done), n, 0, 0)
                        parts = native_components(info, reward, n)
                        returns[lane] += reward
                        for name in COMPONENTS:
                            sums[name][lane] += parts[name]
                        b11._observe_post_transition(trace, t, lane, env, reward, parts, n)
                        next_states.append(info["next_state"])
                        next_observations.append(observation)
                        dones[lane] = done
                    states, observations = np.stack(next_states), np.stack(next_observations)
                    steps += 1
                    if dones.any() and (t != eval_spec.horizon - 1 or not dones.all()):
                        raise ValueError("unexpected B13 terminal boundary")
            if not dones.all():
                raise ValueError("B13 evaluation missed fixed terminal boundary")
            means = {name: values / eval_spec.horizon for name, values in sums.items()}
            j = n * returns / eval_spec.horizon
            native_j = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
            if not np.allclose(j, means["total_reward"], atol=ATOL, rtol=RTOL) \
                    or not np.allclose(j, native_j, atol=ATOL, rtol=RTOL):
                raise ValueError("B13 native J/component identity failed")
            service = trace["served_user_counts"].mean(axis=0)
            eligibility = trace["eligible_user_counts"].mean(axis=0)
            unserved = trace["eligible_unserved_user_counts"].mean(axis=0)
            if not np.allclose(service, 50.0 * means["coverage_reward"], atol=ATOL, rtol=RTOL) \
                    or not np.allclose(unserved, eligibility - service, atol=ATOL, rtol=RTOL):
                raise ValueError("B13 native C/S or E/S/U identity failed")
            counts = counter.finish(eval_spec)
            model_after = digest_agent(target)
            normalizers_after = _normalizer_record(target)
            runtime_after = runtime_state_digest(target)
            if any(calls.values()) or storage_calls or model_after != before \
                    or normalizers_after != normalizers_before:
                raise ValueError("B13 evaluation optimized, stored, or changed weights/normalizers")
            if np.any(target.rollout_buffer.env_lengths):
                raise ValueError("B13 evaluation populated training rollout storage")
            trace_path = out / f"trace_{record.spec.key}_n{n}.npz"
            trace_identity = b11._write_trace(trace_path, trace)
            row = {
                "status": "complete", "asset_key": record.spec.key, "arm": record.spec.arm,
                "seed": record.spec.seed, "policy_stage": POLICY_STAGE,
                "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS, "test_n": n,
                "world_seeds": list(range(world_seed, world_seed + eval_spec.eval_lanes)),
                "runtime_seed": world_seed + 51, "construction_seed": int(construction_seed),
                "steps": eval_spec.eval_lanes * eval_spec.horizon,
                "episodes": eval_spec.eval_lanes, "resets": eval_spec.eval_lanes,
                "policy_step_calls": eval_spec.horizon,
                "J": j.tolist(), "scalar_returns": returns.tolist(),
                "component_means": jsonable(means),
                "service_arrays": {
                    "E_eligible_users_per_step": eligibility.tolist(),
                    "S_served_users_per_step": service.tolist(),
                    "U_eligible_unserved_users_per_step": unserved.tolist(),
                },
                "optimizer_calls": calls.copy(), "training_storage_calls": storage_calls,
                "rollout_storage_env_lengths": target.rollout_buffer.env_lengths.tolist(),
                "frozen_weights_and_normalizers": True,
                "parameter_normalizer_digest_before": before,
                "parameter_normalizer_digest_after": model_after,
                "restored_digest_matches_original_final": before == record.spec.final_digest,
                "normalizers_before": normalizers_before, "normalizers_after": normalizers_after,
                "runtime_digest_before": runtime_before, "runtime_digest_after": runtime_after,
                "runtime_evolved": runtime_before != runtime_after,
                "executed_action_bounds": {"minimum": action_min, "maximum": action_max},
                "inference_counts": counts, "trace": trace_identity,
                "config": _config_record(config), "post_transition_semantics": True,
                "actual_sinr_threshold": float(envs[0].env.env.min_sinr),
                "max_connections_per_uav": int(envs[0].env.env.max_connections),
                "height_range": [float(value) for value in envs[0].env.env.height_range],
                "n_users": int(envs[0].env.env.n_users),
            }
            if record.spec.arm == "SET":
                row["original_reproduction"] = compare_set_reproduction(row, trace, record, n)
                if not row["original_reproduction"]["all_match"]:
                    row.update(
                        status="failed",
                        failure="ValueError: B13 SET original arrays/traces failed fixed reproduction tolerance",
                    )
                    raise PanelFailure(row["failure"], row)
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
    rng_after = _rng_digest()
    if rng_after != rng_before:
        raise ValueError("B13 evaluation changed global RNG state")
    row["global_rng_isolation"] = {
        "digest_before": rng_before, "digest_after": rng_after, "preserved": True,
    }
    return row


def _quantity_arrays(row: dict[str, Any]) -> dict[str, np.ndarray]:
    return {
        "J": np.asarray(row["J"], dtype=np.float64),
        "C": np.asarray(row["component_means"]["coverage_reward"], dtype=np.float64),
        "Q": np.asarray(row["component_means"]["quality_reward"], dtype=np.float64),
        "P": np.asarray(row["component_means"]["energy_penalty"], dtype=np.float64),
        "E": np.asarray(row["service_arrays"]["E_eligible_users_per_step"], dtype=np.float64),
        "S": np.asarray(row["service_arrays"]["S_served_users_per_step"], dtype=np.float64),
        "U": np.asarray(row["service_arrays"]["U_eligible_unserved_users_per_step"], dtype=np.float64),
    }


def _stats(values: np.ndarray, worlds: list[int]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (len(worlds),) or not np.isfinite(array).all():
        raise ValueError("B13 reading array shape/nonfinite mismatch")
    minimum, maximum = int(np.argmin(array)), int(np.argmax(array))
    return {
        "per_world": array.tolist(), "mean": float(array.mean()),
        "median": float(np.median(array)),
        "signs": {
            "positive": int((array > 0).sum()), "zero": int((array == 0).sum()),
            "negative": int((array < 0).sum()),
        },
        "minimum": {"value": float(array[minimum]), "world_seed": worlds[minimum]},
        "maximum": {"value": float(array[maximum]), "world_seed": worlds[maximum]},
    }


def compute_readings(panels: list[dict[str, Any]], test_ns: tuple[int, ...]) -> dict[str, Any]:
    joined = {(row["asset_key"], row["test_n"]): row for row in panels}
    if set(joined) != {(key, n) for key in ("s1", "s2", "h1", "h2") for n in test_ns}:
        raise ValueError("B13 reading does not contain exactly eight fixed panels")
    result = {}
    contrasts = (("h1", "s1"), ("h1", "s2"), ("h2", "s1"), ("h2", "s2"))
    for n in test_ns:
        rows = {key: joined[(key, n)] for key in ("s1", "s2", "h1", "h2")}
        worlds = rows["s1"]["world_seeds"]
        if any(row["world_seeds"] != worlds for row in rows.values()):
            raise ValueError(f"B13 common-world join failed at N={n}")
        quantities = {key: _quantity_arrays(row) for key, row in rows.items()}
        absolute = {
            key: {name: _stats(values, worlds) for name, values in quantities[key].items()}
            for key in quantities
        }
        differences = {}
        for left, right in contrasts:
            name = f"{left}_minus_{right}"
            differences[name] = {
                quantity: _stats(quantities[left][quantity] - quantities[right][quantity], worlds)
                for quantity in quantities[left]
            }
        dependence = {}
        for quantity in quantities["h1"]:
            residual = (
                (quantities["h1"][quantity] - quantities["s1"][quantity])
                - (quantities["h1"][quantity] - quantities["s2"][quantity])
                - (quantities["h2"][quantity] - quantities["s1"][quantity])
                + (quantities["h2"][quantity] - quantities["s2"][quantity])
            )
            # Seven rounded subtraction/addition operations establish this residual.
            # A 16*eps*sum-magnitude envelope is a conservative first-order float64
            # forward-error bound (more than twice gamma_7 at this operation count).
            source_scale = sum(np.abs(quantities[key][quantity]) for key in quantities)
            roundoff_bound = 16.0 * np.finfo(np.float64).eps * np.maximum(1.0, source_scale)
            within_bound = np.abs(residual) <= roundoff_bound
            dependence[quantity] = {
                "per_world_residual": residual.tolist(),
                "max_abs_residual": float(np.abs(residual).max(initial=0.0)),
                "per_world_roundoff_bound": roundoff_bound.tolist(),
                "max_roundoff_bound": float(roundoff_bound.max(initial=0.0)),
                "all_within_roundoff_bound": bool(within_bound.all()),
                "bound_basis": (
                    "16 * float64 epsilon * max(1, sum absolute H1/H2/S1/S2 values) "
                    "for seven rounded arithmetic operations"
                ),
            }
            if not bool(within_bound.all()):
                raise ValueError(
                    f"B13 four-contrast algebraic residual exceeds float64 roundoff bound "
                    f"for {quantity} N={n}"
                )
        result[str(n)] = {
            "test_n": n, "world_seeds": worlds, "absolute": absolute,
            "h6_minus_set_contrasts": differences,
            "algebraic_dependence": dependence,
            "worst_paired_J_S_losses": {
                name: {quantity: differences[name][quantity]["minimum"] for quantity in ("J", "S")}
                for name in differences
            },
            "minimum_absolute_J_S": {
                key: {quantity: absolute[key][quantity]["minimum"] for quantity in ("J", "S")}
                for key in absolute
            },
        }
    return {
        "quantity_units": {
            "J": "N * scalar_return / 500", "C": "coverage fraction", "Q": "quality reward",
            "P": "height energy penalty", "E": "eligible users per step",
            "S": "served users per step = 50*C", "U": "eligible unserved users per step = E-S",
        },
        "by_test_n": result, "cross_n_aggregate": None,
        "scope": "four retained policies on finite common worlds; contrasts are algebraically dependent",
    }


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "scripts" / "run_agent_count_ordinary_control_b13.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b02/probe.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/training_condition_b11/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
    )


def _source_hashes() -> dict[str, str]:
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path) for path in _source_paths()}


def _input_identities(records: list[LoadedAsset]) -> dict[str, Any]:
    def reread(identity: Mapping[str, Any]) -> dict[str, Any]:
        return _read_bound_bytes(
            Path(identity["working_path"]), str(identity["sha256"]),
            relative=Path(identity["relative_path"]),
            committed=bool(identity["committed"]),
            repository_root=Path(identity["repository_root"]),
        )[1]

    result = {}
    for record in records:
        references = {
            str(n): {
                name: reread(identity) for name, identity in identities.items()
            }
            for n, identities in record.reference_identities.items()
        }
        checkpoint_sha256 = file_sha256(record.checkpoint)
        if checkpoint_sha256 != record.spec.checkpoint_sha256:
            raise ValueError(f"B13 checkpoint SHA-256 changed for {record.spec.key}")
        result[record.spec.key] = {
            "summary": reread(record.summary_identity),
            "checkpoint45": {
                "path": str(record.checkpoint), "sha256": checkpoint_sha256,
                "bytes": record.checkpoint.stat().st_size,
                "authoritative_source": "external physical file",
                "working_present": record.checkpoint.is_file(),
            },
            "reference": references,
        }
    return result


def _expected_counts(eval_spec: EvalSpec) -> dict[str, int]:
    panels = 4 * len(eval_spec.test_ns)
    team_steps = panels * eval_spec.eval_lanes * eval_spec.horizon
    return {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_calls": 0, "panels": panels, "evaluation_team_steps": team_steps,
        "evaluation_uav_steps": 4 * eval_spec.eval_lanes * eval_spec.horizon * sum(eval_spec.test_ns),
        "evaluation_episodes": panels * eval_spec.eval_lanes,
        "evaluation_resets": panels * eval_spec.eval_lanes,
        "batched_policy_step_calls": panels * eval_spec.horizon,
        "h6_coordinator_batched_calls": 2 * len(eval_spec.test_ns) * (eval_spec.horizon // 10),
        "h6_lane_assignments": 2 * len(eval_spec.test_ns) * (eval_spec.horizon // 10) * eval_spec.eval_lanes,
    }


def run_study(
    out: Path, launch_sha: str, admission: dict[str, Any], checkpoint_paths: Mapping[str, Path],
    construction_seed: int, *, assets: tuple[AssetSpec, ...] = ASSETS,
    eval_spec: EvalSpec = DEFAULT_SPEC,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_sources: bool = True, command_start: float | None = None,
    evaluate_fn: Callable[..., dict[str, Any]] = evaluate_policy,
) -> int:
    out = Path(out)
    if out.name != TAG:
        raise ValueError(f"B13 output basename must be {TAG}")
    if (out / "summary.json").exists():
        raise ValueError("existing B13 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected = _expected_counts(eval_spec)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": TAG, "direction": DIRECTION,
        "launch_sha": launch_sha, "admission": admission, "status": "validating_assets",
        "zero_fit": True, "failure": None, "spec": jsonable(vars(eval_spec)),
        "construction_seed": int(construction_seed), "policy_stage": POLICY_STAGE,
        "prior_training_team_steps_per_asset": PRIOR_TRAINING_TEAM_STEPS,
        "evaluation_order": ["s1", "s2", "h1", "h2"],
        "world_seed_bases": WORLD_SEED_BASES, "assets": [], "panels": [], "readings": None,
        "counts": {key: 0 for key in expected}, "expected_counts": expected,
        "source_hashes_before": _source_hashes(),
        "runtime": {
            "python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
            "device": "cpu", "dtype": "float32", "torch_threads": eval_spec.torch_threads,
        },
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_study_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    records: list[LoadedAsset] = []
    active: dict[str, Any] | None = None
    active_path: Path | None = None
    publish("admitted")
    try:
        torch.set_num_threads(eval_spec.torch_threads)
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "object_id": OBJECT_ID, "tag": TAG,
            "spec": jsonable(vars(eval_spec)), "construction_seed": int(construction_seed),
            "evaluation_order": [asset.key for asset in assets],
            "world_seed_bases": WORLD_SEED_BASES, "assets": [jsonable(vars(asset)) for asset in assets],
        })
        records = load_assets(
            checkpoint_paths, assets=assets, summary_root=summary_root,
            committed_sources=committed_sources, eval_spec=eval_spec,
            restore_log_root=out / "restore_validation_logs",
            construction_seed=construction_seed,
        )
        summary["assets"] = [{
            "key": record.spec.key, "arm": record.spec.arm, "seed": record.spec.seed,
            "tag": record.spec.tag, "source_sha": record.spec.source_sha,
            "summary": record.summary_identity,
            "checkpoint45": {
                "path": str(record.checkpoint), "sha256": record.spec.checkpoint_sha256,
                "bytes": record.spec.checkpoint_bytes,
            },
            "final_digest": record.spec.final_digest,
            "reference_identities": record.reference_identities,
            "strict_restore_validation": record.restore_validation,
        } for record in records]
        summary["input_identities_before"] = _input_identities(records)
        publish("four final45 assets and SET reproduction sources validated")

        def progress(steps: int, episodes: int, n: int, calls: int, resets: int) -> None:
            summary["counts"]["evaluation_team_steps"] += steps
            summary["counts"]["evaluation_uav_steps"] += steps * n
            summary["counts"]["evaluation_episodes"] += episodes
            summary["counts"]["evaluation_resets"] += resets
            summary["counts"]["batched_policy_step_calls"] += calls

        for record in records:
            for n in eval_spec.test_ns:
                active_path = out / f"panel_{record.spec.key}_n{n}.json"
                active = {
                    "status": "running", "asset_key": record.spec.key, "arm": record.spec.arm,
                    "seed": record.spec.seed, "policy_stage": POLICY_STAGE, "test_n": n,
                    "world_seeds": list(range(_world_seed(n), _world_seed(n) + eval_spec.eval_lanes)),
                }
                summary["panels"].append(active)
                write_json(active_path, active)
                publish(f"{record.spec.key} N={n} starting")
                try:
                    evaluated = evaluate_fn(
                        record, n, out, eval_spec, construction_seed, progress,
                    )
                except PanelFailure as exc:
                    active.clear()
                    active.update(exc.row)
                    write_json(active_path, active)
                    raise
                active.clear()
                active.update(evaluated)
                summary["counts"]["panels"] += 1
                if record.spec.arm == "H6":
                    inference = active["inference_counts"]
                    summary["counts"]["h6_coordinator_batched_calls"] += inference[
                        "coordinator_batched_calls"
                    ]
                    summary["counts"]["h6_lane_assignments"] += inference["coordinator_rows"]
                write_json(active_path, active)
                publish(f"{record.spec.key} N={n} complete")
                active = None
                active_path = None
        initial_matches = {}
        for n in eval_spec.test_ns:
            traces = {}
            for row in summary["panels"]:
                if row["test_n"] == n:
                    with np.load(row["trace"]["path"], allow_pickle=False) as source:
                        traces[row["asset_key"]] = (
                            source["initial_states"].copy(), source["initial_observations"].copy(),
                        )
            reference = traces["s1"]
            matches = {
                key: bool(np.array_equal(value[0], reference[0]) and np.array_equal(value[1], reference[1]))
                for key, value in traces.items()
            }
            initial_matches[str(n)] = matches
            if not all(matches.values()):
                raise ValueError(f"B13 common initial states/observations differ at N={n}")
        summary["common_initial_state_observation_matches"] = initial_matches
        summary["readings"] = compute_readings(summary["panels"], eval_spec.test_ns)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        summary["input_identities_after"] = _input_identities(records)
        summary["input_identities_unchanged"] = (
            summary["input_identities_before"] == summary["input_identities_after"]
        )
        if not summary["source_hashes_unchanged"] or not summary["input_identities_unchanged"]:
            raise ValueError("B13 source or checkpoint inputs changed during evaluation")
        if summary["counts"] != expected:
            raise ValueError(f"B13 exposure mismatch: {summary['counts']} != {expected}")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        if active is not None and active.get("status") == "running":
            active.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
            if active_path is not None:
                write_json(active_path, active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if records:
            try:
                summary["input_identities_after"] = _input_identities(records)
                summary["input_identities_unchanged"] = (
                    summary.get("input_identities_before") == summary["input_identities_after"]
                )
            except Exception as identity_exc:
                summary["input_identities_after"] = None
                summary["input_identities_unchanged"] = False
                summary["input_identity_recheck_failure"] = (
                    f"{type(identity_exc).__name__}: {identity_exc}"
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
