"""Evaluate final H6/SET policies with three explicit count scalars fixed at N6."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import resource
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
from experiments.candidates.agent_count_generalization.action_law_b03.runner import runtime_state_digest
from experiments.candidates.agent_count_generalization.adapter import MAX_UAVS, make_envs
from experiments.candidates.agent_count_generalization.configuration import DIRECTION, FitSpec
from experiments.candidates.agent_count_generalization.initial_policy_b08 import runner as b08
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


OBJECT_ID = "s1_fixed_count_b09"
TAG = OBJECT_ID
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
POLICY_STAGE = 45
WORLD_PANEL_STAGE = 45
PRIOR_TRAINING_TEAM_STEPS = 360_000
FIXED_COUNT_SCALAR = 6.0 / float(MAX_UAVS)

EvalSpec = b08.EvalSpec
DEFAULT_SPEC = b08.DEFAULT_SPEC


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
    checkpoint_sha256: str
    checkpoint_bytes: int
    initial_digest: str
    final_digest: str
    final_panel_sha256: tuple[str, str, str]


ASSETS = (
    AssetSpec(
        "h6", "H6", 952201, "s1_bounded_package_b07_h6_l05_s952201",
        "0a9e3fde40659fdcc1d05922c9920c5c04b2ab23", "s1_bounded_package_b07",
        "h6_l05", "9d7f90523b74ea0fb4b9d7720086baefff13c22cdb41547c2b793764273b550a",
        "65cfcc9f6afc69bae78712a4dd15bc772e2d3b56c82797504e27555a814ef398",
        23_073_626,
        "6d71f3023e5593a801b4d618f7eece93df1a15575f8a71d769566190ba6498df",
        23_073_626, "1d55b8320256e589e6b88ae4b7873d97d54a536de85d6a33df46fa87a521c733",
        "ea1de5234aba1683f182b6f36a3260ecf8fdd68779df0e313a6bc040b9458c1d",
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
        20_968_771,
        "98062b5b338b684219c43b5c9a3dc13bf176322a948c439294beee1d52ae477e",
        20_968_771, "b6d466c143157fdb052df6f16f27351516e1e6b8f6e77789b1fa75ecf5876854",
        "9f183501f97c021be1919d6da925a7ca981736dbeb6ec9dc0e1e67583d0a177b",
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
    return b08.file_sha256(path)


def _world_seed(n: int) -> int:
    return b08._world_seed(n)


def _tensor_digest(value: torch.Tensor) -> str:
    tensor = value.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(tensor.dtype).encode("ascii"))
    digest.update(repr(tuple(tensor.shape)).encode("ascii"))
    digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _tree_tensor_digest(value: Any) -> str:
    digest = hashlib.sha256()

    def visit(item: Any, label: str) -> None:
        digest.update(label.encode("utf-8"))
        if torch.is_tensor(item):
            digest.update(_tensor_digest(item).encode("ascii"))
        elif isinstance(item, Mapping):
            for key in sorted(item):
                visit(item[key], f"{label}.{key}")
        elif isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                visit(child, f"{label}[{index}]")
        elif item is None or isinstance(item, (str, int, float, bool)):
            digest.update(repr(item).encode("utf-8"))
        else:
            raise TypeError(f"unsupported shadow input type {type(item).__name__}")

    visit(value, "root")
    return digest.hexdigest()


def _clone_tree(value: Any) -> Any:
    if torch.is_tensor(value):
        return value.detach().clone()
    if isinstance(value, tuple):
        return tuple(_clone_tree(item) for item in value)
    if isinstance(value, list):
        return [_clone_tree(item) for item in value]
    if isinstance(value, dict):
        return {key: _clone_tree(item) for key, item in value.items()}
    return value


class CountScalarIntervention:
    """Per-agent hooks that replace only the three declared affine-input scalars."""

    def __init__(self, agent: Any, arm: str, n: int):
        self.arm = arm
        self.n = int(n)
        self.enabled = True
        self.mode = "actual"
        self.handles: list[Any] = []
        self.sites: dict[str, dict[str, Any]] = {}
        self.targets: dict[str, torch.nn.Linear] = {}
        if arm == "SET":
            base = agent.skill_discoverer.actor.base
            row_width = int(base.row_encoder[0].out_features)
            state_width = int(base.state_encoder.uav_encoder[2].out_features)
            self._add("set_actor_direct_fusion_count", base.fusion[0], 2 * row_width)
            self._add(
                "set_actor_nested_state_encoder_pooled_count",
                base.state_encoder.output[0], 2 * state_width,
            )
        elif arm == "H6":
            encoder = agent.skill_coordinator.state_embedding
            state_width = int(encoder.uav_encoder[2].out_features)
            self._add(
                "h6_coordinator_state_embedding_pooled_count",
                encoder.output[0], 2 * state_width,
            )
        else:
            raise ValueError(f"unsupported B09 arm {arm}")

    def _add(self, name: str, layer: Any, index: int) -> None:
        if not isinstance(layer, torch.nn.Linear) or not 0 <= index < layer.in_features:
            raise ValueError(f"B09 hook target/index invalid for {name}")
        row = {
            "path": name,
            "affine_in_features": int(layer.in_features),
            "scalar_index": int(index),
            "expected_original": self.n / float(MAX_UAVS),
            "replacement": FIXED_COUNT_SCALAR,
            "actual_calls": 0,
            "actual_rows": 0,
            "shadow_calls": 0,
            "shadow_rows": 0,
            "original_values": [],
            "replacement_values": [],
            "other_columns_unchanged": True,
            "input_was_cloned": True,
        }
        self.sites[name] = row
        self.targets[name] = layer

        def pre_hook(_module: Any, args: tuple[Any, ...]) -> tuple[Any, ...]:
            if not args or not torch.is_tensor(args[0]):
                raise ValueError(f"B09 hook {name} received no tensor input")
            original = args[0]
            expected = original.new_full(original[..., index].shape, self.n / float(MAX_UAVS))
            if not torch.equal(original[..., index], expected):
                raise ValueError(f"B09 hook {name} observed wrong original count scalar")
            key = f"{self.mode}_calls"
            rows_key = f"{self.mode}_rows"
            row[key] += 1
            row[rows_key] += int(original[..., index].numel())
            observed = float(original[..., index].reshape(-1)[0].item())
            if observed not in row["original_values"]:
                row["original_values"].append(observed)
            if not self.enabled:
                return args
            replaced = original.clone()
            replaced[..., index] = FIXED_COUNT_SCALAR
            replacement = float(replaced[..., index].reshape(-1)[0].item())
            if replacement not in row["replacement_values"]:
                row["replacement_values"].append(replacement)
            left_same = torch.equal(replaced[..., :index], original[..., :index])
            right_same = torch.equal(replaced[..., index + 1:], original[..., index + 1:])
            row["other_columns_unchanged"] &= bool(left_same and right_same)
            if not torch.equal(replaced[..., index], replaced.new_full(
                replaced[..., index].shape, FIXED_COUNT_SCALAR
            )):
                raise ValueError(f"B09 hook {name} failed exact replacement")
            return (replaced, *args[1:])

        self.handles.append(layer.register_forward_pre_hook(pre_hook))

    @contextmanager
    def original_shadow(self):
        previous = self.enabled, self.mode
        self.enabled, self.mode = False, "shadow"
        try:
            yield
        finally:
            self.enabled, self.mode = previous

    def evidence(self) -> dict[str, Any]:
        expected_sites = 2 if self.arm == "SET" else 1
        if len(self.sites) != expected_sites:
            raise ValueError("B09 intervention installed wrong site count")
        return {
            "arm": self.arm,
            "test_n": self.n,
            "fixed_scalar": FIXED_COUNT_SCALAR,
            "true_n_unchanged": True,
            "site_count": len(self.sites),
            "sites": jsonable(self.sites),
        }

    def close(self) -> None:
        for handle in self.handles:
            handle.remove()
        self.handles.clear()


class ActorCallCapture:
    def __init__(self, actor: Any):
        self.enabled = True
        self.inputs: tuple[Any, Any] | None = None
        self.output: Any = None

        def pre(_module: Any, args: tuple[Any, ...], kwargs: dict[str, Any]):
            if self.enabled:
                self.inputs = (_clone_tree(args), _clone_tree(kwargs))

        def post(
            _module: Any, _args: tuple[Any, ...], _kwargs: dict[str, Any], output: Any,
        ):
            if self.enabled:
                self.output = _clone_tree(output)

        self.handles = [
            actor.register_forward_pre_hook(pre, with_kwargs=True),
            actor.register_forward_hook(post, with_kwargs=True),
        ]

    def close(self) -> None:
        for handle in self.handles:
            handle.remove()
        self.handles.clear()


def _new_set_shadow() -> dict[str, Any]:
    return {
        "route": "same R_Actor input, previous hidden state, mask and skill",
        "actual_forwards": 0,
        "shadow_forwards": 0,
        "raw_coordinates": 0,
        "raw_changed_coordinates": 0,
        "raw_abs_difference_sum": 0.0,
        "raw_max_abs_difference": 0.0,
        "clipped_coordinates": 0,
        "clipped_changed_coordinates": 0,
        "clipped_abs_difference_sum": 0.0,
        "clipped_max_abs_difference": 0.0,
        "next_hidden_coordinates": 0,
        "next_hidden_changed_coordinates": 0,
        "next_hidden_abs_difference_sum": 0.0,
        "next_hidden_max_abs_difference": 0.0,
        "calls_with_raw_change_but_no_clipped_change": 0,
        "calls_with_next_hidden_change_but_no_clipped_change": 0,
        "held_snapshot_sha256_by_step": [],
        "held_snapshot_refresh_steps": [],
        "held_snapshot_expected_refresh_steps": [],
        "held_snapshot_stable_between_reselections": True,
        "runtime_preserved": True,
        "parameters_normalizers_preserved": True,
        "inputs_preserved": True,
        "rng_preserved": True,
    }


def _accumulate_difference(row: dict[str, Any], prefix: str, actual: Any, shadow: Any) -> bool:
    a = np.asarray(actual, dtype=np.float64)
    b = np.asarray(shadow, dtype=np.float64)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError(f"B09 {prefix} shadow shape/nonfinite mismatch")
    delta = np.abs(b - a)
    changed = delta != 0.0
    row[f"{prefix}_coordinates"] += int(delta.size)
    row[f"{prefix}_changed_coordinates"] += int(changed.sum())
    row[f"{prefix}_abs_difference_sum"] += float(delta.sum())
    row[f"{prefix}_max_abs_difference"] = max(
        row[f"{prefix}_max_abs_difference"], float(delta.max(initial=0.0))
    )
    return bool(changed.any())


def _finish_set_shadow(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    for prefix in ("raw", "clipped", "next_hidden"):
        count = result[f"{prefix}_coordinates"]
        result[f"{prefix}_mean_abs_difference"] = (
            result[f"{prefix}_abs_difference_sum"] / count if count else None
        )
    return result


def _run_set_shadow(
    agent: Any, capture: ActorCallCapture, intervention: CountScalarIntervention,
    actual_actions: np.ndarray, telemetry: dict[str, Any],
    step_index: int, on_shadow_return: Callable[[], None] | None = None,
) -> None:
    if capture.inputs is None or capture.output is None:
        raise ValueError("B09 SET actor capture missing")
    args, kwargs = capture.inputs
    actual_output = capture.output
    actor_input = args[0]
    state_dim = int(agent.config.state_dim)
    obs_dim = int(agent.config.obs_dim)
    n_agents = int(agent.config.n_agents)
    held_end = obs_dim + state_dim + n_agents * obs_dim
    snapshot_digest = _tensor_digest(actor_input[..., obs_dim:held_end])
    snapshots = telemetry["held_snapshot_sha256_by_step"]
    if step_index % int(agent.config.k) == 0:
        telemetry["held_snapshot_expected_refresh_steps"].append(int(step_index))
    elif snapshots and snapshots[-1] != snapshot_digest:
        telemetry["held_snapshot_stable_between_reselections"] = False
        raise ValueError("B09 SET held snapshot changed between k10 reselections")
    if not snapshots or snapshots[-1] != snapshot_digest:
        telemetry["held_snapshot_refresh_steps"].append(int(step_index))
    snapshots.append(snapshot_digest)
    if not np.array_equal(actual_output[0].detach().cpu().numpy().reshape(actual_actions.shape), actual_actions):
        raise ValueError("B09 captured SET actor output differs from executed policy output")
    input_before = _tree_tensor_digest((args, kwargs))
    runtime_before = runtime_state_digest(agent)
    model_before = digest_agent(agent)
    norms_before = _normalizer_record(agent)
    rng_before = _rng_digest()
    capture.enabled = False
    try:
        with preserve_rng(), intervention.original_shadow(), torch.no_grad():
            shadow_output = agent.skill_discoverer.actor(*args, **kwargs)
            if on_shadow_return is not None:
                on_shadow_return()
    finally:
        capture.enabled = True
    rng_after = _rng_digest()
    runtime_after = runtime_state_digest(agent)
    model_after = digest_agent(agent)
    norms_after = _normalizer_record(agent)
    input_after = _tree_tensor_digest((args, kwargs))
    telemetry["actual_forwards"] += 1
    telemetry["shadow_forwards"] += 1
    raw_changed = _accumulate_difference(
        telemetry, "raw", actual_output[0].detach().cpu().numpy(),
        shadow_output[0].detach().cpu().numpy(),
    )
    clipped_changed = _accumulate_difference(
        telemetry, "clipped",
        np.clip(actual_output[0].detach().cpu().numpy(), -1.0, 1.0),
        np.clip(shadow_output[0].detach().cpu().numpy(), -1.0, 1.0),
    )
    hidden_changed = _accumulate_difference(
        telemetry, "next_hidden", actual_output[2].detach().cpu().numpy(),
        shadow_output[2].detach().cpu().numpy(),
    )
    telemetry["calls_with_raw_change_but_no_clipped_change"] += int(
        raw_changed and not clipped_changed
    )
    telemetry["calls_with_next_hidden_change_but_no_clipped_change"] += int(
        hidden_changed and not clipped_changed
    )
    telemetry["runtime_preserved"] &= runtime_before == runtime_after
    telemetry["parameters_normalizers_preserved"] &= (
        model_before == model_after and norms_before == norms_after
    )
    telemetry["inputs_preserved"] &= input_before == input_after
    telemetry["rng_preserved"] &= rng_before == rng_after
    if not all(telemetry[key] for key in (
        "runtime_preserved", "parameters_normalizers_preserved", "inputs_preserved", "rng_preserved",
    )):
        raise ValueError("B09 SET shadow changed protected state/input/RNG")


def _new_h6_shadow() -> dict[str, Any]:
    return {
        "route": "complete assign_and_value_batch with shadow-selected team and autoregressive prefix",
        "actual_selection_forwards": 0,
        "shadow_selection_forwards": 0,
        "selected_environment_rows": 0,
        "team_choice_disagreements": 0,
        "individual_choice_coordinates": 0,
        "individual_choice_disagreements": 0,
        "selection_comparisons": [],
        "autoregressive_prefix_verified": True,
        "prefix_lengths": [],
        "runtime_preserved": True,
        "parameters_normalizers_preserved": True,
        "inputs_preserved": True,
        "rng_preserved": True,
    }


def _run_h6_shadow(
    agent: Any, intervention: CountScalarIntervention, states: np.ndarray,
    observations: np.ndarray, selected: np.ndarray, actual_data: dict[str, Any],
    telemetry: dict[str, Any], step_index: int,
    on_shadow_return: Callable[[], None] | None = None,
) -> None:
    indices = np.where(selected)[0]
    if not len(indices):
        return
    state_np = np.asarray(agent._normalize_states(states[indices]), dtype=np.float32)
    obs_np = np.asarray(agent._normalize_observations(observations[indices]), dtype=np.float32)
    state = torch.as_tensor(state_np, dtype=torch.float32, device=agent.device)
    obs = torch.as_tensor(obs_np, dtype=torch.float32, device=agent.device)
    input_before = _tree_tensor_digest((state, obs))
    runtime_before = runtime_state_digest(agent)
    model_before = digest_agent(agent)
    norms_before = _normalizer_record(agent)
    rng_before = _rng_digest()
    trace: list[tuple[int, Any, Any]] = []

    def decoder_pre(_module: Any, args: tuple[Any, ...], kwargs: dict[str, Any]):
        step = int(kwargs.get("step", 0))
        team = args[2].detach().clone() if len(args) > 2 and torch.is_tensor(args[2]) else None
        prefix = args[3].detach().clone() if len(args) > 3 and torch.is_tensor(args[3]) else None
        trace.append((step, team, prefix))

    handle = agent.skill_coordinator.skill_decoder.register_forward_pre_hook(
        decoder_pre, with_kwargs=True
    )
    try:
        with preserve_rng(), intervention.original_shadow(), torch.no_grad():
            shadow = agent.skill_coordinator.assign_and_value_batch(
                state, obs, deterministic=True,
            )
            if on_shadow_return is not None:
                on_shadow_return()
    finally:
        handle.remove()
    rng_after = _rng_digest()
    runtime_after = runtime_state_digest(agent)
    model_after = digest_agent(agent)
    norms_after = _normalizer_record(agent)
    input_after = _tree_tensor_digest((state, obs))
    expected_trace = agent.config.n_agents + 1
    prefix_ok = len(trace) == expected_trace and trace[0][0] == 0
    prefix_lengths = []
    if prefix_ok:
        for agent_index, (step, team, prefix) in enumerate(trace[1:]):
            expected_prefix = None if agent_index == 0 else shadow["agent_skills"][:, :agent_index]
            prefix_lengths.append(0 if prefix is None else int(prefix.shape[1]))
            prefix_ok &= step == agent_index + 1
            prefix_ok &= torch.equal(team, shadow["team_skills"])
            prefix_ok &= (
                prefix is None if expected_prefix is None else torch.equal(prefix, expected_prefix)
            )
    actual_team = np.asarray(actual_data["team_skills"])[indices]
    actual_individual = np.asarray(actual_data["agent_skills"])[indices]
    shadow_team = shadow["team_skills"].detach().cpu().numpy()
    shadow_individual = shadow["agent_skills"].detach().cpu().numpy()
    telemetry["actual_selection_forwards"] += 1
    telemetry["shadow_selection_forwards"] += 1
    telemetry["selected_environment_rows"] += int(len(indices))
    telemetry["team_choice_disagreements"] += int((actual_team != shadow_team).sum())
    telemetry["individual_choice_coordinates"] += int(actual_individual.size)
    telemetry["individual_choice_disagreements"] += int(
        (actual_individual != shadow_individual).sum()
    )
    telemetry["selection_comparisons"].append({
        "step": int(step_index),
        "selected_environment_indices": indices.tolist(),
        "actual_team": actual_team.tolist(),
        "shadow_team": shadow_team.tolist(),
        "actual_individual": actual_individual.tolist(),
        "shadow_individual": shadow_individual.tolist(),
        "team_disagreements": int((actual_team != shadow_team).sum()),
        "individual_disagreements": int((actual_individual != shadow_individual).sum()),
    })
    telemetry["autoregressive_prefix_verified"] &= bool(prefix_ok)
    for length in prefix_lengths:
        if length not in telemetry["prefix_lengths"]:
            telemetry["prefix_lengths"].append(length)
    telemetry["runtime_preserved"] &= runtime_before == runtime_after
    telemetry["parameters_normalizers_preserved"] &= (
        model_before == model_after and norms_before == norms_after
    )
    telemetry["inputs_preserved"] &= input_before == input_after
    telemetry["rng_preserved"] &= rng_before == rng_after
    if not all(telemetry[key] for key in (
        "autoregressive_prefix_verified", "runtime_preserved",
        "parameters_normalizers_preserved", "inputs_preserved", "rng_preserved",
    )):
        raise ValueError("B09 H6 shadow route or isolation failed")


def _source_asset(asset: AssetSpec) -> b08.AssetSpec:
    return b08.AssetSpec(
        asset.key, asset.arm, asset.seed, asset.tag, asset.source_sha,
        asset.object_id, asset.cell_key, asset.summary_sha256,
        asset.checkpoint00_sha256, asset.checkpoint00_bytes,
        asset.checkpoint_sha256, asset.checkpoint_bytes,
        asset.initial_digest, asset.final_panel_sha256,
    )


def _validate_payload(asset: AssetSpec, payload: Any, fit: FitSpec) -> None:
    required = {"schema", "direction", "launch_sha", "rollout", "config", "modules", "normalizers", "usage"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError(f"B09 checkpoint payload keys mismatch for {asset.key}")
    expected_identity = {
        "schema": 1, "direction": DIRECTION, "launch_sha": asset.source_sha,
        "rollout": POLICY_STAGE,
    }
    if any(payload.get(key) != value for key, value in expected_identity.items()):
        raise ValueError(f"B09 checkpoint identity/stage mismatch for {asset.key}")
    config = payload.get("config", {})
    expected_config = {
        "count_arm": asset.arm, "seed": asset.seed, "n_agents": 6, "n_uavs": 6,
        "lambda_l": .05, "hidden_size": fit.hidden_size, "n_heads": fit.n_heads,
        "n_encoder_layers": fit.n_layers, "n_decoder_layers": fit.n_layers,
        "ppo_epochs": fit.ppo_epochs, "sequence_batch_size": fit.sequence_batch_size,
        "coordinator_batch_size": fit.coordinator_batch_size,
    }
    if any(config.get(key) != value for key, value in expected_config.items()):
        raise ValueError(f"B09 checkpoint config/architecture mismatch for {asset.key}")
    modules = payload.get("modules")
    if not isinstance(modules, dict) or not modules:
        raise ValueError(f"B09 checkpoint modules missing for {asset.key}")
    for module_name, state in modules.items():
        if not isinstance(state, dict) or not state:
            raise ValueError(f"B09 checkpoint module invalid: {asset.key}.{module_name}")
        for tensor_name, tensor in state.items():
            if not torch.is_tensor(tensor) or tensor.numel() == 0:
                raise ValueError(f"B09 checkpoint tensor invalid: {module_name}.{tensor_name}")
            if tensor.dtype.is_floating_point and not bool(torch.isfinite(tensor).all()):
                raise ValueError(f"B09 checkpoint tensor nonfinite: {module_name}.{tensor_name}")
    normalizers = payload.get("normalizers")
    if not isinstance(normalizers, dict) or set(normalizers) != set(NORMALIZERS):
        raise ValueError(f"B09 checkpoint normalizers invalid for {asset.key}")
    b08._finite_tree(normalizers, f"{asset.key}.normalizers")


def _make_eval_config(record: LoadedAsset, envs: list[Any], n: int) -> Any:
    return b08._make_eval_config(record, envs, n)


def load_assets(
    checkpoint_paths: Mapping[str, Path], *, assets: tuple[AssetSpec, ...] = ASSETS,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_sources: bool = True, eval_spec: EvalSpec = DEFAULT_SPEC,
    restore_log_root: Path | None = None,
) -> list[LoadedAsset]:
    if set(checkpoint_paths) != {asset.key for asset in assets}:
        raise ValueError("B09 requires exactly H6 and SET final45 checkpoint paths")
    loaded = []
    for asset in assets:
        source = _source_asset(asset)
        summary, summary_identity, panels, panel_ids, fit = b08._validate_summary_and_final_panels(
            source, summary_root=summary_root, committed=committed_sources, eval_spec=eval_spec,
        )
        checkpoint = Path(checkpoint_paths[asset.key])
        if not checkpoint.is_file() or checkpoint.stat().st_size != asset.checkpoint_bytes:
            raise ValueError(f"B09 final checkpoint byte-size mismatch for {asset.key}")
        if file_sha256(checkpoint) != asset.checkpoint_sha256:
            raise ValueError(f"B09 final checkpoint SHA-256 mismatch for {asset.key}")
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        _validate_payload(asset, payload, fit)
        record = LoadedAsset(
            asset, checkpoint, summary, summary_identity, panels, panel_ids, payload, fit,
        )
        log_root = Path(restore_log_root or checkpoint.parent / "b09_restore_validation_logs")
        for n in eval_spec.test_ns:
            envs = make_envs(eval_spec.eval_lanes, _world_seed(n), n, eval_spec.horizon)
            target = None
            try:
                config = _make_eval_config(record, envs, n)
                target = build_agent(config, str(log_root / asset.key / f"n{n}"))
                restore_checkpoint(target, payload)
                if digest_agent(target) != asset.final_digest:
                    raise ValueError(f"B09 restored final digest mismatch for {asset.key} N={n}")
            finally:
                for env in envs:
                    env.close()
                del target
        loaded.append(record)
    return loaded


def _n6_identity(row: dict[str, Any], original: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "J": (row["J"], original["J"]),
        "scalar_returns": (row["scalar_returns"], original["scalar_returns"]),
    }
    for component in COMPONENTS:
        fields[f"component_means.{component}"] = (
            row["component_means"][component], original["component_means"][component],
        )
    evidence = {}
    for name, (actual, expected) in fields.items():
        left = np.asarray(actual)
        right = np.asarray(expected)
        exact = left.shape == right.shape and np.array_equal(left, right)
        evidence[name] = {"exact": bool(exact), "max_abs_difference": (
            float(np.max(np.abs(left.astype(np.float64) - right.astype(np.float64)), initial=0.0))
            if left.shape == right.shape else None
        )}
    evidence["all_exact"] = all(item["exact"] for item in evidence.values())
    return evidence


def _reset_envs_counted(
    envs: list[Any], n: int,
    progress: Callable[[int, int, int, int, int, int, int], None] | None,
) -> tuple[np.ndarray, np.ndarray]:
    pairs = []
    for env in envs:
        pair = env.reset()
        pairs.append(pair)
        if progress is not None:
            progress(0, 0, n, 0, 1, 0, 0)
    return (
        np.stack([info["state"] for observation, info in pairs]),
        np.stack([observation for observation, info in pairs]),
    )


def evaluate_policy(
    record: LoadedAsset, n: int, out: Path, eval_spec: EvalSpec,
    progress: Callable[[int, int, int, int, int, int, int], None] | None = None,
) -> dict[str, Any]:
    world_seed = _world_seed(n)
    rng_before = _rng_digest()
    row: dict[str, Any]
    n6_mismatch = False
    with preserve_rng():
        seed_rng(world_seed + 51)
        envs = make_envs(eval_spec.eval_lanes, world_seed, n, eval_spec.horizon)
        target, intervention, capture, hooks = None, None, None, []
        try:
            config = _make_eval_config(record, envs, n)
            target = build_agent(config, str(out / "evaluation_logs" / f"{record.spec.key}_n{n}"))
            restore_checkpoint(target, record.payload)
            for lane in range(eval_spec.eval_lanes):
                target.reset_env_state(lane)
            calls, hooks = optimizer_counts(target)
            model_before = digest_agent(target)
            if model_before != record.spec.final_digest:
                raise ValueError("B09 loader/final digest mismatch")
            norms_before = _normalizer_record(target)
            runtime_before = runtime_state_digest(target)
            intervention = CountScalarIntervention(target, record.spec.arm, n)
            if record.spec.arm == "SET" and n in (4, 8):
                capture = ActorCallCapture(target.skill_discoverer.actor)
            states, observations = _reset_envs_counted(envs, n, progress)
            initial = [{
                "world_seed": world_seed + lane,
                "state_sha256": b08._array_digest(states[lane]),
                "observation_sha256": b08._array_digest(observations[lane]),
            } for lane in range(eval_spec.eval_lanes)]
            steps = np.zeros(eval_spec.eval_lanes, dtype=np.int64)
            dones = np.zeros(eval_spec.eval_lanes, dtype=bool)
            returns = np.zeros(eval_spec.eval_lanes, dtype=np.float64)
            components = {name: np.zeros(eval_spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
            set_shadow = _new_set_shadow() if record.spec.arm == "SET" and n in (4, 8) else None
            h6_shadow = _new_h6_shadow() if record.spec.arm == "H6" and n in (4, 8) else None
            action_min, action_max = float("inf"), float("-inf")
            mapping_unchanged = True
            diagnostics_rng_unchanged = True
            with torch.no_grad():
                for t in range(eval_spec.horizon):
                    states_before = states.copy()
                    observations_before = observations.copy()
                    actions, _, data = target.step(
                        states, observations, steps, dones, deterministic=True,
                        return_step_data=True, build_infos=False,
                    )
                    if progress is not None:
                        progress(0, 0, n, 1, 0, 0, 0)
                    finite((actions, data), "B09 deterministic policy output")
                    if actions.shape != (eval_spec.eval_lanes, n, 3) or actions.dtype != np.float32:
                        raise ValueError("B09 action shape/dtype mismatch")
                    if not np.array_equal(states, states_before) or not np.array_equal(
                        observations, observations_before
                    ):
                        raise ValueError("B09 policy call mutated supplied environment inputs")
                    if set_shadow is not None:
                        _run_set_shadow(
                            target, capture, intervention, actions, set_shadow,
                            step_index=t,
                            on_shadow_return=(
                                (lambda: progress(0, 0, n, 0, 0, 1, 0))
                                if progress is not None else None
                            ),
                        )
                    if h6_shadow is not None and bool(np.asarray(data["skill_changed"]).any()):
                        selected = np.asarray(data["skill_changed"], dtype=bool)
                        _run_h6_shadow(
                            target, intervention, states_before, observations_before,
                            selected, data, h6_shadow, step_index=t,
                            on_shadow_return=(
                                (lambda: progress(0, 0, n, 0, 0, 0, 1))
                                if progress is not None else None
                            ),
                        )
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
                            progress(1, int(done), n, 0, 0, 0, 0)
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
                        raise ValueError("unexpected B09 terminal boundary")
            if not dones.all():
                raise ValueError("B09 evaluation missed fixed terminal boundary")
            means = {name: values / eval_spec.horizon for name, values in components.items()}
            j = n * returns / eval_spec.horizon
            native = .7 * means["coverage_reward"] + .3 * means["quality_reward"] - means["energy_penalty"]
            if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6) or not np.allclose(
                j, native, atol=1e-7, rtol=1e-6
            ):
                raise ValueError("B09 native J/component identity failed")
            model_after = digest_agent(target)
            norms_after = _normalizer_record(target)
            runtime_after = runtime_state_digest(target)
            if any(calls.values()) or model_after != model_before or norms_after != norms_before:
                raise ValueError("B09 evaluation changed weights/normalizers or optimized")
            if not mapping_unchanged or not diagnostics_rng_unchanged or action_min < -1.0 or action_max > 1.0:
                raise ValueError("B09 deterministic clip/diagnostic contract failed")
            row = {
                "status": "complete", "asset_key": record.spec.key, "arm": record.spec.arm,
                "seed": record.spec.seed, "policy_stage": POLICY_STAGE,
                "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS,
                "world_panel_stage": WORLD_PANEL_STAGE, "test_n": n,
                "world_seeds": list(range(world_seed, world_seed + eval_spec.eval_lanes)),
                "runtime_seed": world_seed + 51,
                "steps": eval_spec.eval_lanes * eval_spec.horizon,
                "episodes": eval_spec.eval_lanes, "actual_policy_step_calls": eval_spec.horizon,
                "J": j.tolist(), "scalar_returns": returns.tolist(),
                "component_means": jsonable(means), "initial_world_digests": initial,
                "optimizer_calls": calls.copy(), "frozen_weights_and_normalizers": True,
                "parameter_normalizer_digest_before": model_before,
                "parameter_normalizer_digest_after": model_after,
                "restored_digest_matches_original_final": model_before == record.spec.final_digest,
                "normalizers_before": norms_before, "normalizers_after": norms_after,
                "runtime_digest_before": runtime_before, "runtime_digest_after": runtime_after,
                "runtime_evolved": runtime_before != runtime_after,
                "executed_action_bounds": {"minimum": action_min, "maximum": action_max},
                "policy_outputs_unchanged_by_mapping": mapping_unchanged,
                "diagnostics_rng_unchanged": diagnostics_rng_unchanged,
                "intervention": intervention.evidence(),
                "set_actor_shadow": _finish_set_shadow(set_shadow) if set_shadow else None,
                "h6_coordinator_shadow": h6_shadow,
                "config": b08._config_record(config),
            }
            if n == 6:
                row["n6_original_array_identity"] = _n6_identity(row, record.final_panels[n])
                n6_mismatch = not row["n6_original_array_identity"]["all_exact"]
            if set_shadow is not None and set_shadow["held_snapshot_refresh_steps"] != set_shadow[
                "held_snapshot_expected_refresh_steps"
            ]:
                raise ValueError("B09 SET held snapshot did not refresh exactly at k10 boundaries")
        finally:
            if capture is not None:
                capture.close()
            if intervention is not None:
                intervention.close()
            for hook in hooks:
                hook.remove()
            for env in envs:
                env.close()
            del target
    rng_after = _rng_digest()
    if rng_after != rng_before:
        raise ValueError("B09 evaluation changed global RNG state")
    row["global_rng_isolation"] = {
        "digest_before": rng_before, "digest_after": rng_after, "preserved": True,
    }
    if n6_mismatch:
        row.update(
            status="failed",
            failure="ValueError: B09 N6 unchanged-feature arrays differ from original final45",
        )
        write_json(
            out / f"panel_{record.spec.key}_policy45_fixed075_world45_n{n}.json",
            row,
        )
        raise ValueError("B09 N6 unchanged-feature arrays differ from original final45")
    return row


def _quantity_reading(
    h_original: Any, h_clamped: Any, s_original: Any, s_clamped: Any,
) -> dict[str, Any]:
    values = [np.asarray(item, dtype=np.float64) for item in (
        h_original, h_clamped, s_original, s_clamped,
    )]
    if len({item.shape for item in values}) != 1 or not all(np.isfinite(item).all() for item in values):
        raise ValueError("B09 reading shape/nonfinite mismatch")
    ho, hc, so, sc = values
    f_h6, f_set = hc - ho, sc - so
    gamma = f_set - f_h6
    g_original, g_clamped = ho - so, hc - sc
    residual = g_clamped - (g_original - gamma)
    return {
        "absolute": {
            "H6_original_per_world": ho.tolist(), "H6_original_mean": float(ho.mean()),
            "H6_clamped_per_world": hc.tolist(), "H6_clamped_mean": float(hc.mean()),
            "SET_original_per_world": so.tolist(), "SET_original_mean": float(so.mean()),
            "SET_clamped_per_world": sc.tolist(), "SET_clamped_mean": float(sc.mean()),
        },
        "package_effects": {
            "F_SET_per_world": f_set.tolist(), "F_SET_mean": float(f_set.mean()),
            "F_H6_per_world": f_h6.tolist(), "F_H6_mean": float(f_h6.mean()),
        },
        "selectivity": {"Gamma_F_SET_minus_F_H6_per_world": gamma.tolist(),
                        "Gamma_mean": float(gamma.mean())},
        "package_gaps": {
            "G_original_H6_minus_SET_per_world": g_original.tolist(),
            "G_original_mean": float(g_original.mean()),
            "G_clamped_H6_minus_SET_per_world": g_clamped.tolist(),
            "G_clamped_mean": float(g_clamped.mean()),
            "G_original_minus_Gamma_per_world": (g_original - gamma).tolist(),
            "identity_residual_per_world": residual.tolist(),
            "identity_max_abs_residual": float(np.abs(residual).max(initial=0.0)),
        },
    }


def compute_readings(
    panels: list[dict[str, Any]], records: list[LoadedAsset], test_ns: tuple[int, ...],
) -> dict[str, Any]:
    actual = {(row["asset_key"], row["test_n"]): row for row in panels}
    sources = {row.spec.key: row for row in records}
    by_n = {}
    for n in test_ns:
        hc, sc = actual[("h6", n)], actual[("set", n)]
        ho, so = sources["h6"].final_panels[n], sources["set"].final_panels[n]
        worlds = hc["world_seeds"]
        if any(row["world_seeds"] != worlds for row in (sc, ho, so)):
            raise ValueError(f"B09 source join worlds differ at N={n}")
        quantities = {"J": _quantity_reading(ho["J"], hc["J"], so["J"], sc["J"])}
        for component in COMPONENTS:
            quantities[component] = _quantity_reading(
                ho["component_means"][component], hc["component_means"][component],
                so["component_means"][component], sc["component_means"][component],
            )
        coverage = quantities["coverage_reward"]
        coverage["users_per_step"] = {}
        for section in ("absolute", "package_effects", "selectivity", "package_gaps"):
            for key, value in coverage[section].items():
                if key.endswith("_mean"):
                    coverage["users_per_step"][key] = 50 * value
        by_n[str(n)] = {"test_n": n, "world_seeds": worlds, "quantities": quantities}
    unseen = {}
    if 4 in test_ns and 8 in test_ns:
        for quantity in ("J", *COMPONENTS):
            unseen[quantity] = {}
            for section in ("absolute", "package_effects", "selectivity", "package_gaps"):
                for key, value in by_n["4"]["quantities"][quantity][section].items():
                    if key.endswith("_mean"):
                        unseen[quantity][key] = float(np.mean([
                            value, by_n["8"]["quantities"][quantity][section][key]
                        ]))
            if quantity == "coverage_reward":
                unseen[quantity]["users_per_step"] = {
                    key: 50 * value for key, value in unseen[quantity].items()
                }
    return {
        "reading_order": ["absolute", "F_SET", "F_H6", "Gamma", "package_gaps"],
        "by_test_n": by_n, "U_equal_weight_N4_N8": unseen,
        "n6_unchanged_feature_control": by_n.get("6"),
        "positive_energy_penalty_change_is_unfavorable": True,
        "scope": "fixed-feature deployment comparison, not component-matched causal attribution",
    }


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "scripts/run_agent_count_fixed_count_b09.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/initial_policy_b08/runner.py",
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
        summary = Path(record.summary_identity["path"])
        panels = {str(n): {
            "path": identity["path"], "bytes": Path(identity["path"]).stat().st_size,
            "sha256": file_sha256(Path(identity["path"])),
        } for n, identity in record.final_panel_identities.items()}
        result[record.spec.key] = {
            "summary": {"path": str(summary), "bytes": summary.stat().st_size,
                        "sha256": file_sha256(summary)},
            "checkpoint45": {"path": str(record.checkpoint), "bytes": record.checkpoint.stat().st_size,
                             "sha256": file_sha256(record.checkpoint)},
            "final_panels": panels,
        }
    return result


def _expected_counts(eval_spec: EvalSpec, asset_count: int = len(ASSETS)) -> dict[str, int]:
    panels = asset_count * len(eval_spec.test_ns)
    team_steps = panels * eval_spec.eval_lanes * eval_spec.horizon
    unseen = len(set(eval_spec.test_ns) & {4, 8})
    return {
        "fits": 0, "training_team_steps": 0, "stored_training_steps": 0,
        "optimizer_calls": 0, "panels": panels,
        "evaluation_team_steps": team_steps,
        "evaluation_uav_steps": asset_count * eval_spec.eval_lanes * eval_spec.horizon * sum(eval_spec.test_ns),
        "evaluation_episodes": panels * eval_spec.eval_lanes,
        "evaluation_resets": panels * eval_spec.eval_lanes,
        "actual_batched_policy_step_calls": panels * eval_spec.horizon,
        "set_actor_shadow_forwards": unseen * eval_spec.horizon,
        "h6_coordinator_shadow_forwards": unseen * ((eval_spec.horizon + 9) // 10),
        "shadow_environment_steps": 0,
        "reused_original_evaluation_steps": 0,
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
        raise ValueError(f"B09 output basename must be {TAG}")
    if (out / "summary.json").exists():
        raise ValueError("existing B09 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected = _expected_counts(eval_spec, len(assets))
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "tag": TAG, "direction": DIRECTION,
        "launch_sha": launch_sha, "admission": admission, "status": "validating_assets",
        "zero_fit": True, "failure": None, "spec": jsonable(vars(eval_spec)),
        "policy_stage": POLICY_STAGE, "world_panel_stage": WORLD_PANEL_STAGE,
        "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS,
        "fixed_count_scalar": FIXED_COUNT_SCALAR,
        "assets": [], "panels": [], "readings": None,
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
    active_filename: str | None = None
    publish("admitted")
    try:
        torch.set_num_threads(eval_spec.torch_threads)
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "object_id": OBJECT_ID, "tag": TAG,
            "spec": jsonable(vars(eval_spec)), "policy_stage": POLICY_STAGE,
            "world_panel_stage": WORLD_PANEL_STAGE,
            "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS,
            "fixed_count_scalar": FIXED_COUNT_SCALAR,
            "assets": [jsonable(vars(asset)) for asset in assets],
        })
        records = load_assets(
            checkpoint_paths, assets=assets, summary_root=summary_root,
            committed_sources=committed_sources, eval_spec=eval_spec,
            restore_log_root=out / "restore_validation_logs",
        )
        summary["assets"] = [{
            "key": row.spec.key, "arm": row.spec.arm, "seed": row.spec.seed,
            "tag": row.spec.tag, "source_sha": row.spec.source_sha,
            "policy_stage": POLICY_STAGE, "final_digest": row.spec.final_digest,
            "summary": row.summary_identity,
            "checkpoint45": {"path": str(row.checkpoint), "sha256": row.spec.checkpoint_sha256,
                             "bytes": row.spec.checkpoint_bytes},
            "original_final_panel_sources": row.final_panel_identities,
        } for row in records]
        summary["input_identities_before"] = _input_identities(records)
        publish("both final45 assets and independent original arrays validated")

        def progress(
            steps: int, episodes: int, n: int, policy_calls: int, resets: int,
            set_shadows: int, h6_shadows: int,
        ) -> None:
            summary["counts"]["evaluation_team_steps"] += steps
            summary["counts"]["evaluation_uav_steps"] += steps * n
            summary["counts"]["evaluation_episodes"] += episodes
            summary["counts"]["evaluation_resets"] += resets
            summary["counts"]["actual_batched_policy_step_calls"] += policy_calls
            summary["counts"]["set_actor_shadow_forwards"] += set_shadows
            summary["counts"]["h6_coordinator_shadow_forwards"] += h6_shadows

        for record in records:
            for n in eval_spec.test_ns:
                active_filename = f"panel_{record.spec.key}_policy45_fixed075_world45_n{n}.json"
                active = {
                    "status": "running", "asset_key": record.spec.key, "arm": record.spec.arm,
                    "seed": record.spec.seed, "policy_stage": POLICY_STAGE,
                    "prior_training_team_steps": PRIOR_TRAINING_TEAM_STEPS,
                    "world_panel_stage": WORLD_PANEL_STAGE, "test_n": n,
                    "world_seeds": list(range(_world_seed(n), _world_seed(n) + eval_spec.eval_lanes)),
                }
                summary["panels"].append(active)
                write_json(out / active_filename, active)
                publish(f"{record.spec.key} final45 fixed-count N={n} starting")
                evaluated = evaluate_fn(record, n, out, eval_spec, progress)
                active.clear()
                active.update(evaluated)
                summary["counts"]["panels"] += 1
                write_json(out / active_filename, active)
                publish(f"{record.spec.key} final45 fixed-count N={n} complete")
                active = None
                active_filename = None
        grouped: dict[int, list[dict[str, Any]]] = {}
        for row in summary["panels"]:
            grouped.setdefault(int(row["test_n"]), []).append(row)
        matches = {}
        for n, rows in grouped.items():
            if len(rows) != 2:
                raise ValueError(f"B09 initial reset comparison lacks both packages at N={n}")
            same = rows[0]["initial_world_digests"] == rows[1]["initial_world_digests"]
            matches[str(n)] = {"both_packages_match": same,
                               "per_world": rows[0]["initial_world_digests"]}
            if not same:
                raise ValueError(f"B09 initial environment mismatch at N={n}")
        summary["initial_state_observation_matches"] = matches
        summary["readings"] = compute_readings(summary["panels"], records, eval_spec.test_ns)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        summary["input_identities_after"] = _input_identities(records)
        summary["input_identities_unchanged"] = summary["input_identities_before"] == summary["input_identities_after"]
        if not summary["source_hashes_unchanged"] or not summary["input_identities_unchanged"]:
            raise ValueError("B09 source/checkpoint inputs changed during evaluation")
        if summary["counts"] != expected:
            raise ValueError(f"B09 exposure mismatch: {summary['counts']} != {expected}")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        if active is not None and active.get("status") == "running":
            if active_filename is not None and (out / active_filename).is_file():
                retained = json.loads((out / active_filename).read_text(encoding="utf-8"))
                if isinstance(retained, dict) and retained.get("J") is not None:
                    active.clear()
                    active.update(retained)
            active.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
            if active_filename is not None:
                write_json(out / active_filename, active)
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
