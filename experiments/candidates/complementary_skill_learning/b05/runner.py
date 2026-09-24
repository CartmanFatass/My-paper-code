"""Fixed nine-panel frozen-M O/S/R deployment evaluator.

The production entry point has no scientific degrees of freedom.  Tests may
pass a smaller :class:`Spec` and a matching artificial :class:`InputContract`
directly to :func:`run_evaluation`; the admitted CLI always uses the constants
in this module.
"""
from __future__ import annotations

import contextlib
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import pickle
import random
import resource
import sys
import time
import traceback
from typing import Any, Iterator, Mapping

import numpy as np
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b04.learning import (
    TrainingLawAgent,
    _capture_process_rng_state,
    _restore_process_rng_state,
)
from experiments.candidates.complementary_skill_learning.b04 import runner as b04


DIRECTION = "complementary_skill_learning"
OBJECT = "complementary_skill_b05"
PANELS = ("O", "R0", "S0", "R1", "S1", "R2", "S2", "R3", "S3")
S_SEEDS = {f"S{i}": 260923951 + i for i in range(4)}
R_SEEDS = {f"R{i}": 262624105 + i for i in range(4)}
NON_LABEL_SEED = 262624105
UNIFORM_LOG_FACTOR = -math.log(6.0)
EXPECTED_PHYSICAL_SHA256 = "b36474bb458d4c72efb2feed5b6653583cf0cbaf02fa264e097111209827d6d1"
EXPECTED_R0_LABEL_SHA256 = "a45d59f80fca20321df3803745068bb841f30e6c25b6b8c01dd7d0d250a67190"


@dataclass(frozen=True)
class Spec:
    n_agents: int = 6
    n_users: int = 50
    k: int = 10
    horizon: int = 500
    eval_lanes: int = 32
    training_lanes: int = 16
    training_rollouts: int = 45
    world_base: int = 1700200
    threads: int = 4
    small_model: bool = False  # direct technical fixtures only; absent from the CLI


@dataclass(frozen=True)
class InputContract:
    final_bytes: int
    final_sha256: str
    summary_bytes: int
    summary_sha256: str
    config_bytes: int
    config_sha256: str
    native_digest: str
    frozen_digest: str
    physical_sha256: str
    r0_label_sha256: str


DEFAULT_SPEC = Spec()
PRODUCTION_INPUT = InputContract(
    final_bytes=27_128_511,
    final_sha256="df222836fca1b4a4aaf87408d4f024fbb796e7107c004a40f1f5ecc64201c39f",
    summary_bytes=4_952_932,
    summary_sha256="248d3e04c32b4684738676aa5491dc4da5848874c243e5f6e34bb11ba5bb1299",
    config_bytes=650,
    config_sha256="3135dcb1ac17f10208375b6705d0f3b9c5e4ac2f376f1f058cd598fc9887787f",
    native_digest="d6b22033f9c84901db42015d01b7c58238002ea5ba301a0daf5d919035dc4058",
    frozen_digest="7e9ee5542474cca2ba0281ebeb5000bc3947e254a6cf48b80e59d33010bd17f0",
    physical_sha256=EXPECTED_PHYSICAL_SHA256,
    r0_label_sha256=EXPECTED_R0_LABEL_SHA256,
)


jsonable = b01.jsonable
write_json = b01.write_json
update_digest = b01.update_digest


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_identity(path: Path) -> dict[str, Any]:
    return {"file": path.name, "bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def _state_digest(value: Any) -> str:
    return hashlib.sha256(pickle.dumps(value, protocol=4)).hexdigest()


def _optimizer_states(agent: TrainingLawAgent) -> dict[str, Any]:
    return {
        name: copy.deepcopy(optimizer.state_dict())
        for name, optimizer in vars(agent).items()
        if name.endswith("_optimizer") and optimizer is not None
    }


def _nested_equal(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return bool(torch.equal(left, right))
    if isinstance(left, np.ndarray) and isinstance(right, np.ndarray):
        return bool(np.array_equal(left, right))
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return left.keys() == right.keys() and all(_nested_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, type(left)):
        return len(left) == len(right) and all(_nested_equal(a, b) for a, b in zip(left, right))
    return left == right


class EvaluationCallAudit:
    """Count and reject every training, storage, or normalizer mutation path."""

    def __init__(self, agent: TrainingLawAgent) -> None:
        self.agent = agent
        self.counts = {
            "native_update_calls": 0,
            "auxiliary_fit_calls": 0,
            "optimizer_steps": 0,
            "store_calls": 0,
            "normalizer_updates": 0,
        }
        self._patches: list[tuple[Any, str, bool, Any]] = []

    def _patch(self, obj: Any, name: str, counter: str) -> None:
        if obj is None or not hasattr(obj, name):
            return
        namespace = getattr(obj, "__dict__", {})
        had_instance = name in namespace
        old_instance = namespace.get(name)

        def prohibited(*_args: Any, **_kwargs: Any) -> None:
            self.counts[counter] += 1
            raise RuntimeError(f"B05 prohibited call reached {name}")

        self._patches.append((obj, name, had_instance, old_instance))
        setattr(obj, name, prohibited)

    def __enter__(self) -> "EvaluationCallAudit":
        for name in (
            "update",
            "update_coordinator",
            "update_coordinator_d2",
            "update_coordinator_ha_ctse",
            "update_discoverer_from_rollout",
            "update_discriminators",
            "update_process_exploration_from_segments",
        ):
            self._patch(self.agent, name, "native_update_calls")
        self._patch(self.agent, "_run_auxiliary_update", "auxiliary_fit_calls")
        for name in ("store_transition_batch", "store_transition", "store_rollout_step"):
            self._patch(self.agent, name, "store_calls")
        normalizer_classes = {
            type(normalizer)
            for name in b01.NORMALIZERS
            for normalizer in (getattr(self.agent, name, None),)
            if normalizer is not None
        }
        for normalizer_class in normalizer_classes:
            self._patch(normalizer_class, "update", "normalizer_updates")
        for name, optimizer in vars(self.agent).items():
            if name.endswith("_optimizer") and optimizer is not None:
                self._patch(optimizer, "step", "optimizer_steps")
        return self

    def __exit__(self, *_exc: Any) -> None:
        for obj, name, had_instance, old_instance in reversed(self._patches):
            if had_instance:
                setattr(obj, name, old_instance)
            else:
                delattr(obj, name)
        self._patches.clear()

    def snapshot(self) -> dict[str, int]:
        return dict(self.counts)


def _counter_delta(after: Mapping[str, int], before: Mapping[str, int]) -> dict[str, int]:
    return {key: int(after[key] - before[key]) for key in before}


_ADMITTED_METADATA = {
    "launch-status.json",
    "launch-manifest.json",
    "admission-preflight.json",
    "stdout.log",
    "stderr.log",
}


def prepare_output_root(out: Path | str, admission: Mapping[str, Any] | None) -> Path:
    """Accept a fresh technical root or the launcher's exact metadata-only root."""
    out = Path(out)
    if not out.exists():
        out.mkdir(parents=True)
        return out
    if not out.is_dir() or admission is None:
        raise FileExistsError("B05 never overwrites or reuses an output root")
    names = {path.name for path in out.iterdir()}
    if names != _ADMITTED_METADATA or any(not (out / name).is_file() for name in names):
        raise FileExistsError("B05 admitted output root contains non-launcher or scientific content")
    try:
        manifest = json.loads((out / "launch-manifest.json").read_text())
        status = json.loads((out / "launch-status.json").read_text())
        preflight = json.loads((out / "admission-preflight.json").read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FileExistsError("B05 admitted output metadata is unreadable") from exc
    expected = {
        "direction": admission.get("direction"),
        "sha": admission.get("sha"),
        "command_sha256": admission.get("command_sha256"),
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise FileExistsError("B05 output manifest differs from accepted admission")
    if Path(str(manifest.get("output_root", ""))).resolve(strict=False) != out.resolve(strict=False):
        raise FileExistsError("B05 output manifest binds another output root")
    claim_key = manifest.get("claim_key")
    if (
        not isinstance(claim_key, str)
        or status.get("claim_key") != claim_key
        or preflight.get("claim_key") != claim_key
        or preflight.get("direction") != admission.get("direction")
        or preflight.get("sha") != admission.get("sha")
        or preflight.get("passed") is not True
    ):
        raise FileExistsError("B05 launcher metadata is not one accepted operation")
    if status.get("status") not in {"release_unknown", "accepted"}:
        raise FileExistsError("B05 launcher has not released this output root")
    return out


def _torch_state_digest(cpu: torch.Tensor, cuda: list[torch.Tensor] | None) -> str:
    digest = hashlib.sha256(np.ascontiguousarray(cpu.cpu().numpy()).tobytes())
    for state in cuda or ():
        digest.update(np.ascontiguousarray(state.cpu().numpy()).tobytes())
    return digest.hexdigest()


class PersistentTorchRNG:
    """One private persistent CPU/CUDA Torch stream with outer restoration."""

    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        outer = self._capture()
        try:
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.seed)
            self.cpu, self.cuda = self._capture()
        finally:
            self._restore(*outer)
        self.uses = 0

    @staticmethod
    def _capture() -> tuple[torch.Tensor, list[torch.Tensor] | None]:
        return (
            torch.random.get_rng_state().clone(),
            [state.clone() for state in torch.cuda.get_rng_state_all()]
            if torch.cuda.is_available()
            else None,
        )

    @staticmethod
    def _restore(cpu: torch.Tensor, cuda: list[torch.Tensor] | None) -> None:
        torch.random.set_rng_state(cpu)
        if cuda is not None:
            torch.cuda.set_rng_state_all(cuda)

    @contextlib.contextmanager
    def use(self) -> Iterator[None]:
        outer = self._capture()
        self._restore(self.cpu, self.cuda)
        try:
            yield
        finally:
            self.cpu, self.cuda = self._capture()
            self.uses += 1
            self._restore(*outer)

    def telemetry(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "uses": self.uses,
            "cpu_state_bytes": int(self.cpu.numel()),
            "cuda_devices": 0 if self.cuda is None else len(self.cuda),
            "state_sha256": _torch_state_digest(self.cpu, self.cuda),
        }


def _process_telemetry() -> dict[str, Any]:
    state = _capture_process_rng_state()
    return {
        "state_sha256": b04.rng_state_digest(),
        "torch_cpu_state_bytes": int(state["torch_cpu"].numel()),
        "torch_cuda_devices": 0 if state["torch_cuda"] is None else len(state["torch_cuda"]),
    }


def validate_inputs(root: Path | str, contract: InputContract) -> dict[str, Any]:
    """Fail closed on every fixed source artifact before constructing outputs."""
    root = Path(root)
    expected = {
        "final.pt": (contract.final_bytes, contract.final_sha256),
        "summary.json": (contract.summary_bytes, contract.summary_sha256),
        "config.json": (contract.config_bytes, contract.config_sha256),
    }
    identities: dict[str, Any] = {}
    for name, (size, digest) in expected.items():
        path = root / name
        if not path.is_file():
            raise ValueError(f"required B04 input is absent: {name}")
        observed = _file_identity(path)
        if observed["bytes"] != size or observed["sha256"] != digest:
            raise ValueError(f"B04 input identity differs: {name}")
        identities[name] = observed
    try:
        source_summary = json.loads((root / "summary.json").read_text())
        source_config = json.loads((root / "config.json").read_text())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("B04 input JSON is invalid") from exc
    if source_summary.get("object_id") != "complementary_skill_b04" or source_summary.get("arm") != "M":
        raise ValueError("B05 input is not the original B04 M object")
    if source_summary.get("status") != "complete":
        raise ValueError("B04 input summary is incomplete")
    final = source_summary.get("checkpoints", {}).get("final", {})
    if (
        final.get("sha256") != contract.final_sha256
        or final.get("bytes") != contract.final_bytes
        or final.get("native_digest") != contract.native_digest
        or final.get("frozen_digest") != contract.frozen_digest
    ):
        raise ValueError("B04 summary does not bind the required final checkpoint")
    if source_config.get("object_id") != "complementary_skill_b04" or source_config.get("arm") != "M":
        raise ValueError("B04 config does not identify arm M")
    for panel in ("final_own", "final_uniform"):
        if panel not in source_summary.get("panels", {}):
            raise ValueError(f"B04 source reference panel is absent: {panel}")
    return {"root": str(root.resolve()), "files": identities, "summary": source_summary, "config": source_config}


def make_config(spec: Spec, envs: list[Any]):
    b04_spec = b04.Spec(
        n_agents=spec.n_agents,
        n_users=spec.n_users,
        k=spec.k,
        horizon=spec.horizon,
        lanes=spec.training_lanes,
        rollouts=spec.training_rollouts,
        eval_lanes=spec.eval_lanes,
        small_model=spec.small_model,
    )
    return b04.make_config(b04_spec, envs, "M")


def restore_agent(
    checkpoint_path: Path,
    spec: Spec,
    device: str | torch.device,
    log_dir: Path,
    source_summary: Mapping[str, Any],
    contract: InputContract,
) -> tuple[TrainingLawAgent, dict[str, Any]]:
    envs = b01.make_envs(spec, 1, spec.world_base)
    try:
        config = make_config(spec, envs)
    finally:
        for env in envs:
            env.close()
    config_snapshot = effective_config(config)
    if config_snapshot != source_summary.get("learner_config"):
        raise ValueError("constructed native config differs from the B04 checkpoint config")

    b01.seed_rng(260923931)
    agent = TrainingLawAgent(
        config=config,
        arm="M",
        head_seed=260923932,
        aux_seed=260923934,
        low_action_seed=260923935,
        high_collection_seed=260923936,
        high_update_seed=260923937,
        log_dir=str(log_dir),
        device=torch.device(device),
    )
    # Keep serialized RNG byte tensors on CPU.  load_state_dict moves module and
    # optimizer tensors to their already-constructed parameter device, whereas
    # torch.set_rng_state specifically requires a CPU ByteTensor.
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if (
        checkpoint.get("object_id") != "complementary_skill_b04"
        or checkpoint.get("arm") != "M"
        or int(checkpoint.get("stage", -1)) != spec.training_rollouts
        or checkpoint.get("config") != config_snapshot
    ):
        raise ValueError("B04 checkpoint schema, arm, stage or config differs")
    if set(checkpoint.get("native", {})) != set(b01.MODULES):
        raise ValueError("B04 checkpoint native module set differs")
    for name in b01.MODULES:
        getattr(agent, name).load_state_dict(checkpoint["native"][name], strict=True)
    if set(checkpoint.get("normalizers", {})) != set(b01.NORMALIZERS):
        raise ValueError("B04 checkpoint normalizer set differs")
    for name in b01.NORMALIZERS:
        setattr(agent, name, copy.deepcopy(checkpoint["normalizers"][name]))
    agent.load_auxiliary_state_dict(checkpoint["auxiliary"])
    rng = checkpoint.get("rng", {})
    if rng.get("schema") != "complementary_skill_b04_rng_v1":
        raise ValueError("B04 checkpoint RNG schema differs")
    agent.load_rng_stream_state_dict(rng["private_streams"])
    agent.load_sampler_rng_state_dict(rng["rollout_samplers"])
    _restore_process_rng_state(rng["default_process"])
    if not _nested_equal(_capture_process_rng_state(), rng["default_process"]):
        raise ValueError("restored B04 default process RNG state differs")
    agent.train(False)
    for name in (*b01.MODULES, "g_head", "p_head"):
        module = getattr(agent, name, None)
        if module is not None:
            module.eval()
            for parameter in module.parameters():
                parameter.requires_grad_(False)
    native = b04.native_digest(agent)
    frozen = b04.frozen_digest(agent)
    if native != contract.native_digest or frozen != contract.frozen_digest:
        raise ValueError("restored B04 tensor/normalizer/calibration digest differs")
    if agent.rng_stream_telemetry() != source_summary.get("final_private_rng_streams"):
        raise ValueError("restored B04 private RNG streams differ")
    if agent.sampler_rng_telemetry() != source_summary.get("final_sampler_rng_streams"):
        raise ValueError("restored B04 sampler streams differ")
    native_optimizer_entries = {
        name: len(getattr(agent, name).state_dict()["state"])
        for name in (
            "coordinator_optimizer",
            "discoverer_actor_optimizer",
            "discoverer_critic_optimizer",
            "team_discriminator_optimizer",
            "individual_discriminator_optimizer",
        )
    }
    if any(native_optimizer_entries.values()):
        raise ValueError("new native optimizers are not idle after checkpoint restore")
    auxiliary_optimizer_entries = {
        name: len(optimizer.state_dict()["state"])
        for name in ("g_head_optimizer", "p_head_optimizer", "auxiliary_trunk_optimizer")
        for optimizer in (getattr(agent, name, None),)
        if optimizer is not None
    }
    return agent, {
        "native_digest": native,
        "frozen_digest": frozen,
        "config": config_snapshot,
        "private_rng_streams": agent.rng_stream_telemetry(),
        "sampler_rng_streams": agent.sampler_rng_telemetry(),
        "default_process": _process_telemetry(),
        "optimizer_restore": {
            "native": {
                "checkpoint_state_present": False,
                "handling": "new idle optimizer state; original B04 checkpoint has no native optimizer state",
                "state_entries": native_optimizer_entries,
            },
            "auxiliary": {
                "checkpoint_state_present": True,
                "handling": "restored from checkpoint auxiliary optimizer state",
                "state_entries": auxiliary_optimizer_entries,
            },
        },
    }


def _agent_evaluation_state(agent: TrainingLawAgent) -> dict[str, Any]:
    return {
        "frozen_digest": b04.frozen_digest(agent),
        "private_rng": agent.rng_stream_telemetry(),
        "sampler_rng": agent.sampler_rng_telemetry(),
        "process_rng": _process_telemetry(),
        "training": bool(agent.training),
        "module_modes": {
            name: bool(getattr(agent, name).training)
            for name in (*b01.MODULES, "g_head", "p_head")
            if getattr(agent, name, None) is not None
        },
    }


@contextlib.contextmanager
def _frozen_panel_context(agent: TrainingLawAgent) -> Iterator[dict[str, Any]]:
    process = _capture_process_rng_state()
    before = _agent_evaluation_state(agent)
    try:
        with torch.no_grad():
            yield before
    finally:
        _restore_process_rng_state(process)
    after = _agent_evaluation_state(agent)
    if after != before:
        raise RuntimeError("B05 panel changed frozen agent, RNG, sampler, or module state")


def _select_learned(
    agent: TrainingLawAgent,
    states: np.ndarray,
    observations: np.ndarray,
    *,
    deterministic: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    batch, n_agents = observations.shape[:2]
    result = agent.skill_coordinator.assign_partial_batch(
        torch.as_tensor(states, dtype=torch.float32, device=agent.device),
        torch.as_tensor(observations, dtype=torch.float32, device=agent.device),
        torch.zeros(batch, dtype=torch.long, device=agent.device),
        torch.zeros((batch, n_agents), dtype=torch.long, device=agent.device),
        torch.ones(batch, dtype=torch.bool, device=agent.device),
        torch.ones((batch, n_agents), dtype=torch.bool, device=agent.device),
        deterministic=deterministic,
    )
    return tuple(
        result[name].detach().cpu().numpy()
        for name in ("team_skills", "agent_skills", "team_log_probs", "agent_log_probs", "order")
    )  # type: ignore[return-value]


def _select_labels(
    panel: str,
    agent: TrainingLawAgent,
    states: np.ndarray,
    observations: np.ndarray,
    r_rng: np.random.Generator | None,
    s_rng: PersistentTorchRNG | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    lanes, n_agents = observations.shape[:2]
    if panel == "O":
        return _select_learned(agent, states, observations, deterministic=True)
    if panel.startswith("S"):
        if s_rng is None:
            raise RuntimeError("S panel has no private Torch stream")
        with s_rng.use():
            return _select_learned(agent, states, observations, deterministic=False)
    if r_rng is None:
        raise RuntimeError("R panel has no private PCG64 stream")
    team = r_rng.integers(0, 6, size=lanes, dtype=np.int64)
    individual = r_rng.integers(0, 6, size=(lanes, n_agents), dtype=np.int64)
    return (
        team,
        individual,
        np.full(lanes, UNIFORM_LOG_FACTOR, np.float32),
        np.full((lanes, n_agents), UNIFORM_LOG_FACTOR, np.float32),
        np.broadcast_to(np.arange(n_agents, dtype=np.int64), (lanes, n_agents)).copy(),
    )


def _allocate_trajectory(spec: Spec, state_dim: int, obs_dim: int, action_dim: int) -> dict[str, np.ndarray]:
    t, b, n = spec.horizon, spec.eval_lanes, spec.n_agents
    return {
        # Row t is the pre-transition value and row t+1 is the post-transition
        # value.  This lossless representation avoids duplicating every native
        # state and joint observation in the large production trajectories.
        "states": np.empty((t + 1, b, state_dim), np.float64),
        "observations": np.empty((t + 1, b, n, obs_dim), np.float32),
        "team_labels": np.empty((t, b), np.int16),
        "individual_labels": np.empty((t, b, n), np.int16),
        "renewal": np.zeros(t, np.bool_),
        "team_factor_log_probs": np.full((t, b), np.nan, np.float32),
        "individual_factor_log_probs": np.full((t, b, n), np.nan, np.float32),
        "renewal_order": np.full((t, b, n), -1, np.int16),
        "raw_mean_actions": np.empty((t, b, n, action_dim), np.float32),
        "clipped_actions": np.empty((t, b, n, action_dim), np.float32),
        "rewards": np.empty((t, b), np.float64),
        "coverage_reward": np.empty((t, b), np.float64),
        "quality_reward": np.empty((t, b), np.float64),
        "energy_penalty": np.empty((t, b), np.float64),
        "total_reward": np.empty((t, b), np.float64),
        "episode_ends": np.empty((t, b), np.bool_),
    }


def _trajectory_manifest(arrays: Mapping[str, np.ndarray]) -> dict[str, Any]:
    return {
        name: {"shape": list(value.shape), "dtype": value.dtype.str}
        for name, value in arrays.items()
    }


def _save_npz(path: Path, arrays: Mapping[str, np.ndarray], steps: int) -> dict[str, Any]:
    saved = {
        name: value[: steps + 1] if name in {"states", "observations"} else value[:steps]
        for name, value in arrays.items()
    }
    np.savez_compressed(path, **saved)
    return {**_file_identity(path), "steps": steps, "arrays": _trajectory_manifest(saved)}


def _panel_summary_from_trajectory(
    panel: str,
    spec: Spec,
    trajectory: Mapping[str, np.ndarray],
    label_digest: hashlib._Hash,
    initial_digest: hashlib._Hash,
    saturation: int,
    action_coordinates: int,
) -> dict[str, Any]:
    returns = trajectory["rewards"].sum(axis=0, dtype=np.float64)
    components = {
        name: trajectory[name].sum(axis=0, dtype=np.float64) / spec.horizon
        for name in b01.COMPONENTS
    }
    scores = spec.n_agents * returns / spec.horizon
    # Preserve the frozen evaluator's operation order for bitwise O/R identity.
    users = (
        trajectory["coverage_reward"].sum(axis=0, dtype=np.float64)
        * spec.n_users
        / spec.horizon
    )
    np.testing.assert_allclose(scores, components["total_reward"], rtol=1e-7, atol=1e-7)
    np.testing.assert_allclose(
        scores,
        .7 * components["coverage_reward"] + .3 * components["quality_reward"] - components["energy_penalty"],
        rtol=0.0,
        atol=2e-12,
    )
    return {
        "status": "complete",
        "panel": panel,
        "law": "original_greedy" if panel == "O" else ("learned_stochastic" if panel.startswith("S") else "independent_uniform"),
        "low_actions": "deterministic_mean_then_physical_clip[-1,1]",
        "world_seeds": list(range(spec.world_base, spec.world_base + spec.eval_lanes)),
        "transitions": spec.eval_lanes * spec.horizon,
        "episodes": spec.eval_lanes,
        "renewals": spec.horizon // spec.k,
        "optimizer_calls": 0,
        "normalizer_updates": 0,
        "store_calls": 0,
        "returns_U": returns,
        "native_scores_J": scores,
        "mean_J": float(scores.mean()),
        "component_means": components,
        "connected_users_per_step": users,
        "raw_saturation_fraction": saturation / action_coordinates,
        "physical_initial_state_sha256": initial_digest.hexdigest(),
        "physical_initial_state_fields": ["native_state", "joint_observations"],
        "selected_label_stream_sha256": label_digest.hexdigest(),
        "selected_label_stream_order": "at each k10 renewal: int64 time, team[lanes], individual[lanes,n_agents]",
    }


def evaluate_panel(
    agent: TrainingLawAgent,
    spec: Spec,
    panel: str,
    out: Path,
    s_stream: PersistentTorchRNG | None = None,
    counter: dict[str, int] | None = None,
    call_audit: EvaluationCallAudit | None = None,
) -> dict[str, Any]:
    if panel not in PANELS:
        raise ValueError(panel)
    trajectory_path = out / f"panel_{panel}_trajectory.npz"
    panel_path = out / f"panel_{panel}.json"
    arrays = _allocate_trajectory(spec, agent.config.state_dim, agent.config.obs_dim, agent.config.action_dim)
    label_digest, initial_digest = hashlib.sha256(), hashlib.sha256()
    r_rng = np.random.Generator(np.random.PCG64(R_SEEDS[panel])) if panel.startswith("R") else None
    r_stream_before = _state_digest(r_rng.bit_generator.state) if r_rng is not None else None
    completed_steps = saturation = action_coordinates = 0
    envs: list[Any] = []
    stream_before = s_stream.telemetry() if s_stream is not None else None
    outer_before = _process_telemetry()
    audit_before = call_audit.snapshot() if call_audit is not None else None
    try:
        with _frozen_panel_context(agent) as frozen_before:
            b01.seed_rng(NON_LABEL_SEED)
            envs = b01.make_envs(spec, spec.eval_lanes, spec.world_base)
            states, observations = b01.native._reset_all(envs)
            update_digest(initial_digest, states, observations)
            hidden = np.zeros((spec.eval_lanes, spec.n_agents, agent.config.gru_hidden_size), np.float32)
            arrays["states"][0] = states
            arrays["observations"][0] = observations
            team = individual = None
            for t in range(spec.horizon):
                if t % spec.k == 0:
                    team, individual, team_lp, individual_lp, order = _select_labels(
                        panel, agent, states, observations, r_rng, s_stream
                    )
                    update_digest(label_digest, np.asarray([t], np.int64), team, individual)
                    arrays["renewal"][t] = True
                    arrays["team_factor_log_probs"][t] = team_lp
                    arrays["individual_factor_log_probs"][t] = individual_lp
                    arrays["renewal_order"][t] = order
                if team is None or individual is None:
                    raise RuntimeError("labels were not assigned before the low forward")
                arrays["team_labels"][t] = team
                arrays["individual_labels"][t] = individual
                raw, hidden = b01.low_actions(agent, observations, individual, hidden, deterministic=True)
                clipped = np.clip(raw, -1.0, 1.0)
                arrays["raw_mean_actions"][t] = raw
                arrays["clipped_actions"][t] = clipped
                saturation += int((np.abs(raw) > 1).sum())
                action_coordinates += raw.size
                next_states, next_observations = [], []
                for lane, env in enumerate(envs):
                    state, obs, reward, done, parts, executed = b01.physical_step(env, raw[lane])
                    if not np.array_equal(executed, clipped[lane]):
                        raise RuntimeError("native physical action differs from recorded clip")
                    if done != (t == spec.horizon - 1):
                        raise ValueError("unexpected B05 episode boundary")
                    next_states.append(state)
                    next_observations.append(obs)
                    arrays["rewards"][t, lane] = reward
                    arrays["episode_ends"][t, lane] = done
                    for name in b01.COMPONENTS:
                        arrays[name][t, lane] = parts[name]
                    if counter is not None:
                        counter["evaluation_transitions"] += 1
                        counter["evaluation_episodes"] += int(done)
                        counter[f"{panel[0]}_transitions"] += 1
                states, observations = np.stack(next_states), np.stack(next_observations)
                arrays["states"][t + 1] = states
                arrays["observations"][t + 1] = observations
                completed_steps = t + 1
            panel_summary = _panel_summary_from_trajectory(
                panel, spec, arrays, label_digest, initial_digest, saturation, action_coordinates
            )
            panel_summary["frozen_state_before"] = frozen_before
    except Exception as exc:
        partial = {
            "status": "failed",
            "panel": panel,
            "completed_steps": completed_steps,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "actual_counts_at_failure": dict(counter) if counter is not None else None,
            "observed_mutation_calls": (
                _counter_delta(call_audit.snapshot(), audit_before)
                if call_audit is not None and audit_before is not None
                else None
            ),
        }
        if completed_steps:
            partial["trajectory"] = _save_npz(trajectory_path, arrays, completed_steps)
        write_json(panel_path, partial)
        raise
    finally:
        for env in envs:
            env.close()
    outer_after = _process_telemetry()
    if outer_after != outer_before:
        raise RuntimeError("B05 panel leaked process RNG state")
    panel_summary["outer_process_rng"] = {
        "before": outer_before,
        "after": outer_after,
        "restored": True,
    }
    if s_stream is not None:
        panel_summary["label_rng"] = {
            "kind": "persistent_private_torch_cpu_and_active_cuda",
            "before": stream_before,
            "after": s_stream.telemetry(),
            "expected_uses": spec.horizon // spec.k,
        }
        if s_stream.uses != spec.horizon // spec.k:
            raise RuntimeError("S private Torch stream use count differs")
    elif r_rng is not None:
        panel_summary["label_rng"] = {
            "kind": type(r_rng.bit_generator).__name__,
            "seed": R_SEEDS[panel],
            "before_state_sha256": r_stream_before,
            "after_state_sha256": _state_digest(r_rng.bit_generator.state),
            "draw_order": "team[lanes] then individual[lanes,n_agents] at each renewal",
        }
    else:
        panel_summary["label_rng"] = {"kind": "none_deterministic"}
    panel_summary["non_label_rng_seed"] = NON_LABEL_SEED
    if call_audit is not None and audit_before is not None:
        panel_summary["observed_mutation_calls"] = _counter_delta(
            call_audit.snapshot(), audit_before
        )
        if any(panel_summary["observed_mutation_calls"].values()):
            raise RuntimeError("B05 panel reached a prohibited mutation path")
    panel_summary["trajectory"] = _save_npz(trajectory_path, arrays, completed_steps)
    panel_summary["trajectory"]["state_observation_sequence_semantics"] = (
        "row t is transition t pre-state/observation; row t+1 is its post-state/observation"
    )
    write_json(panel_path, panel_summary)
    return panel_summary


def _identity_comparison(actual: Mapping[str, Any], reference: Mapping[str, Any]) -> dict[str, Any]:
    fields = {
        "returns_U": (actual["returns_U"], reference["returns_U"]),
        "native_scores_J": (actual["native_scores_J"], reference["native_scores_J"]),
        "connected_users_per_step": (actual["connected_users_per_step"], reference["connected_users_per_step"]),
        "raw_saturation_fraction": (actual["raw_saturation_fraction"], reference["raw_saturation_fraction"]),
    }
    for name in b01.COMPONENTS:
        fields[f"component_means.{name}"] = (
            actual["component_means"][name], reference["component_means"][name]
        )
    numeric: dict[str, Any] = {}
    for name, (left, right) in fields.items():
        left_array, right_array = np.asarray(left), np.asarray(right)
        numeric[name] = {
            "exact": bool(np.array_equal(left_array, right_array)),
            "max_abs_difference": float(np.max(np.abs(left_array - right_array))),
        }
    hashes = {
        name: {"actual": actual[name], "reference": reference[name], "exact": actual[name] == reference[name]}
        for name in ("physical_initial_state_sha256", "selected_label_stream_sha256")
    }
    return {
        "numeric": numeric,
        "hashes": hashes,
        "exact": all(row["exact"] for row in numeric.values()) and all(row["exact"] for row in hashes.values()),
    }


def _metric_arrays(panel: Mapping[str, Any]) -> dict[str, np.ndarray]:
    return {
        "J": np.asarray(panel["native_scores_J"], np.float64),
        "users": np.asarray(panel["connected_users_per_step"], np.float64),
        "coverage": np.asarray(panel["component_means"]["coverage_reward"], np.float64),
        "quality": np.asarray(panel["component_means"]["quality_reward"], np.float64),
        "height": np.asarray(panel["component_means"]["energy_penalty"], np.float64),
    }


def _endpoint(values: np.ndarray, worlds: np.ndarray) -> dict[str, Any]:
    lo, hi = int(np.argmin(values)), int(np.argmax(values))
    return {
        "mean": float(values.mean()),
        "min": float(values[lo]),
        "min_world": int(worlds[lo]),
        "max": float(values[hi]),
        "max_world": int(worlds[hi]),
    }


def aggregate_panels(panels: Mapping[str, Mapping[str, Any]], spec: Spec) -> dict[str, Any]:
    if tuple(panels) != PANELS:
        raise ValueError("B05 aggregation panel order differs")
    worlds = np.arange(spec.world_base, spec.world_base + spec.eval_lanes)
    by_panel = {name: _metric_arrays(panels[name]) for name in PANELS}
    result: dict[str, Any] = {}
    for metric in ("J", "users", "coverage", "quality", "height"):
        s = np.stack([by_panel[f"S{i}"][metric] for i in range(4)])
        r = np.stack([by_panel[f"R{i}"][metric] for i in range(4)])
        r_new = r[1:]
        o = by_panel["O"][metric]
        mean_s, mean_r, mean_r_new = s.mean(axis=0), r.mean(axis=0), r_new.mean(axis=0)
        delta_sr4 = mean_s - mean_r
        delta_so = mean_s - o
        delta_srnew3 = mean_s - mean_r_new
        lhs = float(delta_sr4.mean() - delta_srnew3.mean())
        rhs = float((mean_r_new.mean() - r[0].mean()) / 4)
        if not np.isclose(lhs, rhs, rtol=0.0, atol=1e-12):
            raise ValueError(f"R0 sensitivity identity failed for {metric}")
        result[metric] = {
            "worlds": worlds,
            "world_mean_S4": mean_s,
            "world_mean_R4": mean_r,
            "world_mean_Rnew3": mean_r_new,
            "Delta_SR4_world": delta_sr4,
            "Delta_SO_world": delta_so,
            "Delta_SRnew3_world": delta_srnew3,
            "Delta_SR4": float(delta_sr4.mean()),
            "Delta_SO": float(delta_so.mean()),
            "Delta_SRnew3": float(delta_srnew3.mean()),
            "R0_sensitivity_identity": {"left": lhs, "right": rhs, "residual": lhs - rhs},
            "stream_32_world_means": {name: float(by_panel[name][metric].mean()) for name in PANELS},
            "absolute_endpoints": {name: _endpoint(by_panel[name][metric], worlds) for name in PANELS},
            "signed_delta_endpoints": {
                "Delta_SR4": _endpoint(delta_sr4, worlds),
                "Delta_SO": _endpoint(delta_so, worlds),
                "Delta_SRnew3": _endpoint(delta_srnew3, worlds),
            },
            "within_world_S4_range": np.ptp(s, axis=0),
            "within_world_S4_population_std": s.std(axis=0, ddof=0),
            "within_world_R4_range": np.ptp(r, axis=0),
            "within_world_R4_population_std": r.std(axis=0, ddof=0),
        }
    return result


def _directory_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _resource_row(started: float, cpu_started: resource.struct_rusage, out: Path, device: torch.device) -> dict[str, Any]:
    cpu = resource.getrusage(resource.RUSAGE_SELF)
    row = {
        "wall_seconds": time.perf_counter() - started,
        "user_cpu_seconds": cpu.ru_utime - cpu_started.ru_utime,
        "system_cpu_seconds": cpu.ru_stime - cpu_started.ru_stime,
        "peak_rss_bytes": int(cpu.ru_maxrss * (1024 if sys.platform != "darwin" else 1)),
        "peak_rss_scope": "process lifetime as reported by getrusage(RUSAGE_SELF)",
        "output_bytes": _directory_bytes(out),
        "output_bytes_scope": "all regular files in this output root at measurement time",
        "peak_scratch_bytes": None,
        "shared_node_occupancy": None,
        "resources_unmeasured": ["peak_scratch_bytes", "shared_node_occupancy"],
    }
    if device.type == "cuda":
        row.update(
            cuda_peak_allocated_bytes=int(torch.cuda.max_memory_allocated(device)),
            cuda_peak_reserved_bytes=int(torch.cuda.max_memory_reserved(device)),
            cuda_measurement_scope="after checkpoint restore through fixed evaluation",
        )
    else:
        row.update(cuda_peak_allocated_bytes=None, cuda_peak_reserved_bytes=None)
    return row


def run_evaluation(
    input_root: Path | str,
    out: Path | str,
    launch_sha: str,
    *,
    spec: Spec = DEFAULT_SPEC,
    contract: InputContract = PRODUCTION_INPUT,
    device: str | torch.device = "cuda",
    admission: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    input_info = validate_inputs(input_root, contract)
    out = prepare_output_root(out, admission)
    torch.set_num_threads(spec.threads)
    device = torch.device(device)
    started = time.perf_counter()
    cpu_started = resource.getrusage(resource.RUSAGE_SELF)
    counts = {
        "started_fits": 0,
        "model_constructions": 0,
        "checkpoint_loads": 0,
        "training_transitions": 0,
        "stored_transitions": 0,
        "native_updates": 0,
        "optimizer_calls": 0,
        "normalizer_updates": 0,
        "evaluation_transitions": 0,
        "evaluation_episodes": 0,
        "O_transitions": 0,
        "S_transitions": 0,
        "R_transitions": 0,
    }
    summary: dict[str, Any] = {
        "object_id": OBJECT,
        "direction": DIRECTION,
        "launch_sha": launch_sha,
        "status": "incomplete",
        "panel_order": list(PANELS),
        "spec": asdict(spec),
        "device": str(device),
        "admission": admission,
        "input": {"root": input_info["root"], "files": input_info["files"], "contract": asdict(contract)},
        "counts": counts,
        "panels": {},
        "completed_panels": [],
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "torch": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "torch_threads": torch.get_num_threads(),
            "thread_environment": {
                key: os.environ.get(key)
                for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
            },
            "model_dtype": "float32",
            "reward_and_aggregate_dtype": "float64",
            "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
            "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        },
    }
    write_json(out / "config.json", {
        "object_id": OBJECT,
        "launch_sha": launch_sha,
        "input_root": input_info["root"],
        "input_contract": asdict(contract),
        "spec": asdict(spec),
        "device": str(device),
        "panel_order": list(PANELS),
    })
    write_json(out / "summary.json", summary)
    agent: TrainingLawAgent | None = None
    try:
        agent, restored = restore_agent(
            Path(input_root) / "final.pt", spec, device, out / "learner_logs",
            input_info["summary"], contract,
        )
        counts["model_constructions"] = 1
        counts["checkpoint_loads"] = 1
        summary["restored"] = restored
        before_optimizer = _optimizer_states(agent)
        before_agent = _agent_evaluation_state(agent)
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        streams = {name: PersistentTorchRNG(seed) for name, seed in S_SEEDS.items()}
        summary["S_stream_initial"] = {name: stream.telemetry() for name, stream in streams.items()}
        with EvaluationCallAudit(agent) as call_audit:
            for panel in PANELS:
                result = evaluate_panel(
                    agent,
                    spec,
                    panel,
                    out,
                    streams.get(panel),
                    counter=counts,
                    call_audit=call_audit,
                )
                summary["panels"][panel] = result
                summary["completed_panels"].append(panel)
                write_json(out / "summary.json", summary)
            summary["observed_mutation_calls"] = call_audit.snapshot()
            if any(summary["observed_mutation_calls"].values()):
                raise RuntimeError("B05 reached a prohibited mutation path")
            counts["native_updates"] = call_audit.counts["native_update_calls"]
            counts["optimizer_calls"] = call_audit.counts["optimizer_steps"]
            counts["normalizer_updates"] = call_audit.counts["normalizer_updates"]
            counts["stored_transitions"] = call_audit.counts["store_calls"]
        physical_hashes = {
            name: summary["panels"][name]["physical_initial_state_sha256"]
            for name in PANELS
        }
        if len(set(physical_hashes.values())) != 1:
            raise RuntimeError("B05 panels did not reset the same physical worlds")
        summary["physical_initial_state_sha256_by_panel"] = physical_hashes
        if not _nested_equal(_optimizer_states(agent), before_optimizer):
            raise RuntimeError("B05 changed restored optimizer state")
        if _agent_evaluation_state(agent) != before_agent:
            raise RuntimeError("B05 changed restored agent state across evaluation")
        summary["S_stream_final"] = {name: stream.telemetry() for name, stream in streams.items()}
        summary["frozen_after"] = _agent_evaluation_state(agent)
        own_reference = input_info["summary"]["panels"]["final_own"]
        uniform_reference = input_info["summary"]["panels"]["final_uniform"]
        summary["identity_controls"] = {
            "O_vs_B04_final_own": _identity_comparison(summary["panels"]["O"], own_reference),
            "R0_vs_B04_final_uniform": _identity_comparison(summary["panels"]["R0"], uniform_reference),
            "fixed_physical_hash": {
                "actual": summary["panels"]["O"]["physical_initial_state_sha256"],
                "expected": contract.physical_sha256,
                "exact": summary["panels"]["O"]["physical_initial_state_sha256"] == contract.physical_sha256,
            },
            "fixed_R0_label_hash": {
                "actual": summary["panels"]["R0"]["selected_label_stream_sha256"],
                "expected": contract.r0_label_sha256,
                "exact": summary["panels"]["R0"]["selected_label_stream_sha256"] == contract.r0_label_sha256,
            },
        }
        controls_exact = all(
            row["exact"] for row in summary["identity_controls"].values()
        )
        summary["aggregates"] = aggregate_panels(summary["panels"], spec)
        summary["aggregate_metric_definitions"] = {
            "J": "native team score",
            "users": "connected users per step",
            "coverage": "coverage_reward per step",
            "quality": "quality_reward per step",
            "height": "energy_penalty per step (historical report label)",
        }
        expected_counts = {
            **{key: 0 for key in ("started_fits", "training_transitions", "stored_transitions", "native_updates", "optimizer_calls", "normalizer_updates")},
            "model_constructions": 1,
            "checkpoint_loads": 1,
            "evaluation_transitions": 9 * spec.eval_lanes * spec.horizon,
            "evaluation_episodes": 9 * spec.eval_lanes,
            "O_transitions": spec.eval_lanes * spec.horizon,
            "S_transitions": 4 * spec.eval_lanes * spec.horizon,
            "R_transitions": 4 * spec.eval_lanes * spec.horizon,
        }
        if counts != expected_counts:
            raise RuntimeError(f"B05 counts differ: {counts}")
        summary["scientific_reading_status"] = "valid" if controls_exact else "quarantined_identity_failure"
        summary["status"] = "complete" if controls_exact else "quarantined"
    except Exception as exc:
        summary["status"] = "failed"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        summary["traceback"] = traceback.format_exc()
        summary["failed_after_completed_panels"] = list(summary["completed_panels"])
        raise
    finally:
        summary["resources"] = _resource_row(started, cpu_started, out, device)
        write_json(out / "summary.json", summary)
        # Stabilize the inclusive output-byte count after rendering summary.json.
        for _ in range(3):
            measured = _directory_bytes(out)
            if summary["resources"]["output_bytes"] == measured:
                break
            summary["resources"]["output_bytes"] = measured
            write_json(out / "summary.json", summary)
    return summary


__all__ = [
    "DEFAULT_SPEC",
    "InputContract",
    "NON_LABEL_SEED",
    "PANELS",
    "PRODUCTION_INPUT",
    "PersistentTorchRNG",
    "R_SEEDS",
    "S_SEEDS",
    "Spec",
    "aggregate_panels",
    "evaluate_panel",
    "restore_agent",
    "run_evaluation",
    "validate_inputs",
]
