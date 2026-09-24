"""Frozen double-bank B09 H/R deployment evaluator.

R replays the unchanged B07 uniform evaluator law.  H consumes the same PCG64
proposals, including team proposals, but holds each lane/agent's first individual
label for the full episode.  Neither mode trains or mutates the restored agents.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import traceback
from typing import Any, Mapping

import numpy as np
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b04.learning import TrainingLawAgent
from experiments.candidates.complementary_skill_learning.b05 import runner as b05
from experiments.candidates.complementary_skill_learning.b07 import runner as b07


DIRECTION = "complementary_skill_learning"
OBJECT = "complementary_skill_b09"
FIXED_SEED = 260924051  # batch identity only; never used as an RNG address
NON_LABEL_SEED = 260924105
R_SEEDS = {f"R{i}": 262625201 + i for i in range(4)}
BANK_ORDER = ("B07", "B08")
STREAM_ORDER = tuple(f"R{i}" for i in range(4))
PANEL_ORDER = tuple(
    f"{bank}_{mode}{stream[1:]}"
    for mode in ("R", "H")
    for bank in BANK_ORDER
    for stream in STREAM_ORDER
)
UNIFORM_LOG_FACTOR = np.float32(-math.log(6.0))
OLD_TRAJECTORY_KEYS = (
    "states",
    "observations",
    "team_labels",
    "individual_labels",
    "renewal",
    "team_factor_log_probs",
    "individual_factor_log_probs",
    "renewal_order",
    "raw_mean_actions",
    "clipped_actions",
    "rewards",
    "coverage_reward",
    "quality_reward",
    "energy_penalty",
    "total_reward",
    "episode_ends",
)


@dataclass(frozen=True)
class ArtifactContract:
    relative_path: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class BankContract:
    bank: str
    source_launch_sha: str
    adapter_protocol_id: str | None
    source_spec: Mapping[str, Any]
    final_native_digest: str
    final_frozen_digest: str
    artifacts: tuple[ArtifactContract, ...]

    def artifact(self, relative_path: str) -> ArtifactContract:
        matches = [item for item in self.artifacts if item.relative_path == relative_path]
        if len(matches) != 1:
            raise ValueError(f"{self.bank} contract does not contain exactly one {relative_path}")
        return matches[0]


_B07_SPEC = asdict(b07.DEFAULT_SPEC)
_B08_SPEC = {
    **_B07_SPEC,
    "init_seed": 260924041,
    "head_seed": 260924042,
    "train_rng_seed": 260924043,
    "aux_seed": 260924044,
    "low_action_seed": 260924045,
    "high_collection_seed": 260924046,
    "high_update_seed": 260924047,
    "train_world_base": 2400000,
}


PRODUCTION_CONTRACTS = {
    "B07": BankContract(
        bank="B07",
        source_launch_sha="455536ebd0e6e23466ed40244bcf1e5ab6462826",
        adapter_protocol_id=None,
        source_spec=_B07_SPEC,
        final_native_digest="5aebd0e6e99fd1bf696b51ec47418df22fd143b70131e60722e43d7efb196796",
        final_frozen_digest="0127e56c6cb2526f702feb130be23db28cf150f467f235308ff21a03dc8b8087",
        artifacts=(
            ArtifactContract("config.json", 736, "a804b516ef7e3793daed7c571dc58f13c5713f0bf140d3cd35a3c7a214318a3e"),
            ArtifactContract("summary.json", 674029, "db3cfff475493898f120d8875cb13780fcf28ca1313f0064fd16248c850f0071"),
            ArtifactContract("final.pt", 26931903, "5224552930ba84ed3082dade9ffaff4f1946a5edd66a6baf85cb9d5637d2ed5e"),
            ArtifactContract("raw/final_R0.json", 11233, "8759fa97d8a621d2d7a97a5401e5621e0791f4e6768ca6309cda9cd540cd71de"),
            ArtifactContract("raw/final_R0_trajectory.npz", 10831741, "4c9022131ed80b00f43b9452f435df5151caefeb3a2af9e2501c8f59268a0765"),
            ArtifactContract("raw/final_R1.json", 11229, "2c974edab50b7a26fb172482a3c0eea8034fa71e050bed3b3bc1adbad7fbc61b"),
            ArtifactContract("raw/final_R1_trajectory.npz", 10882288, "3422272c864d54bb119320d2842fe459648d1fadee8487ec50c7553d6d216f82"),
            ArtifactContract("raw/final_R2.json", 11166, "65f2ff482750f8739f0a6e0f4f60b7b1f0e9cdae84cac3a0e0a2f4cbb0135a45"),
            ArtifactContract("raw/final_R2_trajectory.npz", 10868313, "f4938fa7e426a8df31076e0aed4680591057f3560d3a5b82c2da2c631af80f1e"),
            ArtifactContract("raw/final_R3.json", 11243, "0b27b86f77420ab4bbb216222e04b6d639607e10a04f399e52d6255da7cdcf6d"),
            ArtifactContract("raw/final_R3_trajectory.npz", 10832350, "1fdd66b3a1d8c4fc056c0f62470ec5641586ee37f509acc8fa64ef5521eba414"),
        ),
    ),
    "B08": BankContract(
        bank="B08",
        source_launch_sha="c9217f0ae5b32aa2a13e228cc87899f545a0111b",
        adapter_protocol_id="complementary_skill_b08",
        source_spec=_B08_SPEC,
        final_native_digest="e157afae86ff2b287242ef6ec46b71b5a1ae7f547363e1ab0c9ae76f7a6b7863",
        final_frozen_digest="46c1975444592979dd4679709c1ea183c8fe61973db0f0d541c28f8eb649faa4",
        artifacts=(
            ArtifactContract("config.json", 1727, "b837606dcfe6d6ee18d65bb1f9eca9889332c33c2316d614c02281efe9d3aa49"),
            ArtifactContract("summary.json", 674922, "6a7cf0407f142c4b7dfffd5e03f3eebbe0607625b6677d25c7ba4836116764a0"),
            ArtifactContract("final.pt", 26931967, "b74920de0e5548662fa37ead0a862ab26d7865e003084dba13e6a12ff5198978"),
            ArtifactContract("raw/final_R0.json", 11256, "0ba27de1a047ebc5a4d7e9ee01933eb1705c8338aaf46f5a6c3110b009a775cc"),
            ArtifactContract("raw/final_R0_trajectory.npz", 10853982, "a7fd88838834786bcf9c2981ddcc3d392d646d59b9467b0fadad949b4b6431fe"),
            ArtifactContract("raw/final_R1.json", 11149, "2c710872b970999cdc50a2d91e5c820f8c39d5d87f4999fbc0d2349527f776be"),
            ArtifactContract("raw/final_R1_trajectory.npz", 10747283, "aeb407451f38710e09555d82ad04a68a28020e9e4d1510fd347bae1ed6b2c890"),
            ArtifactContract("raw/final_R2.json", 11257, "045d2aed5cb9e4318509b8235c9bc0f710b1b4aecd34762be0b255df6677f835"),
            ArtifactContract("raw/final_R2_trajectory.npz", 10763521, "b1f72bcd1f61c3562f9d5179198ec6642096d8eaf3348487a533de68a812cffa"),
            ArtifactContract("raw/final_R3.json", 11208, "947199db1e7ab6c5376ae70e33e7a8e44515c236064ab1acb67d73bb8696ea1a"),
            ArtifactContract("raw/final_R3_trajectory.npz", 10795371, "9c73632b0b6f504a5e82e61a9e5ced11801902c7195ad8bebea98d685baa275c"),
        ),
    ),
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_identity(path: Path, relative_path: str | None = None) -> dict[str, Any]:
    return {
        "path": relative_path or path.name,
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _array_identity(array: np.ndarray) -> dict[str, Any]:
    value = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(value.dtype.str.encode())
    digest.update(json.dumps(list(value.shape), separators=(",", ":")).encode())
    digest.update(value.tobytes())
    return {"shape": list(value.shape), "dtype": value.dtype.str, "sha256": digest.hexdigest()}


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    try:
        with np.load(path, allow_pickle=False) as loaded:
            return {name: loaded[name].copy() for name in loaded.files}
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid trajectory NPZ: {path}") from exc


def _validate_source_semantics(
    contract: BankContract,
    source_summary: Mapping[str, Any],
    source_config: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
) -> None:
    expected_spec = dict(contract.source_spec)
    for name, body in (("summary", source_summary), ("config", source_config)):
        if body.get("object_id") != b07.OBJECT or body.get("arm") != "U":
            raise ValueError(f"{contract.bank} {name} is not the frozen B07-engine U asset")
        if body.get("launch_sha") != contract.source_launch_sha:
            raise ValueError(f"{contract.bank} {name} source SHA differs")
        if body.get("spec") != expected_spec:
            raise ValueError(f"{contract.bank} {name} Spec differs")
    if source_summary.get("status") != "complete":
        raise ValueError(f"{contract.bank} source summary is incomplete")
    for body_name, body in (("summary", source_summary), ("config", source_config)):
        protocol = body.get("adapter_protocol")
        if contract.adapter_protocol_id is None:
            if protocol is not None:
                raise ValueError(f"{contract.bank} {body_name} has unexpected adapter provenance")
        elif not isinstance(protocol, Mapping) or (
            protocol.get("protocol_id") != contract.adapter_protocol_id
            or protocol.get("launch_sha") != contract.source_launch_sha
            or protocol.get("spec") != expected_spec
        ):
            raise ValueError(f"{contract.bank} {body_name} adapter provenance differs")
    final = source_summary.get("checkpoints", {}).get("final", {})
    final_contract = contract.artifact("final.pt")
    if (
        final.get("sha256") != final_contract.sha256
        or final.get("bytes") != final_contract.bytes
        or final.get("native_digest") != contract.final_native_digest
        or final.get("frozen_digest") != contract.final_frozen_digest
    ):
        raise ValueError(f"{contract.bank} summary final checkpoint binding differs")
    if (
        checkpoint.get("object_id") != b07.OBJECT
        or checkpoint.get("arm") != "U"
        or checkpoint.get("stage") != expected_spec["rollouts"]
        or checkpoint.get("config") != source_summary.get("learner_config")
    ):
        raise ValueError(f"{contract.bank} checkpoint source/arm/stage/config differs")
    if set(checkpoint.get("native", {})) != set(b01.MODULES):
        raise ValueError(f"{contract.bank} checkpoint native module set differs")
    if set(checkpoint.get("normalizers", {})) != set(b01.NORMALIZERS):
        raise ValueError(f"{contract.bank} checkpoint normalizer set differs")
    if checkpoint.get("rng", {}).get("schema") != "complementary_skill_b04_rng_v1":
        raise ValueError(f"{contract.bank} checkpoint RNG schema differs")
    for stream in STREAM_ORDER:
        panel = source_summary.get("panels", {}).get(f"final_{stream}", {})
        trajectory = contract.artifact(f"raw/final_{stream}_trajectory.npz")
        if (
            panel.get("status") != "complete"
            or panel.get("stage") != "final"
            or panel.get("panel") != stream
            or panel.get("trajectory", {}).get("sha256") != trajectory.sha256
            or panel.get("trajectory", {}).get("bytes") != trajectory.bytes
        ):
            raise ValueError(f"{contract.bank} saved final {stream} binding differs")


def validate_bank_input(
    root: Path | str, contract: BankContract
) -> dict[str, Any]:
    """Hash and validate one complete source before any output/native work."""

    root = Path(root)
    identities: dict[str, Any] = {}
    for artifact in contract.artifacts:
        path = root / artifact.relative_path
        if not path.is_file():
            raise ValueError(f"{contract.bank} required input is absent: {artifact.relative_path}")
        identity = _file_identity(path, artifact.relative_path)
        if identity["bytes"] != artifact.bytes or identity["sha256"] != artifact.sha256:
            raise ValueError(f"{contract.bank} input identity differs: {artifact.relative_path}")
        identities[artifact.relative_path] = identity
    try:
        source_summary = json.loads((root / "summary.json").read_text())
        source_config = json.loads((root / "config.json").read_text())
        checkpoint = torch.load(root / "final.pt", map_location="cpu", weights_only=False)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{contract.bank} source artifact is unreadable") from exc
    _validate_source_semantics(contract, source_summary, source_config, checkpoint)
    expected_keys: tuple[str, ...] | None = None
    for stream in STREAM_ORDER:
        arrays = _load_npz(root / "raw" / f"final_{stream}_trajectory.npz")
        keys = tuple(arrays)
        if keys != OLD_TRAJECTORY_KEYS or (expected_keys is not None and keys != expected_keys):
            raise ValueError(f"{contract.bank} saved {stream} trajectory schema differs")
        expected_keys = keys
    return {
        "root": str(root.resolve()),
        "contract": contract,
        "identities": identities,
        "summary": source_summary,
        "config": source_config,
        "checkpoint": checkpoint,
    }


def validate_inputs(
    b07_input_root: Path | str,
    b08_input_root: Path | str,
    contracts: Mapping[str, BankContract] = PRODUCTION_CONTRACTS,
) -> dict[str, Any]:
    if tuple(contracts) != BANK_ORDER:
        raise ValueError("B09 bank contract order differs")
    inputs = {
        "B07": validate_bank_input(b07_input_root, contracts["B07"]),
        "B08": validate_bank_input(b08_input_root, contracts["B08"]),
    }
    eval_fields = ("n_agents", "n_users", "k", "horizon", "eval_lanes", "eval_world_base")
    b07_spec, b08_spec = (inputs[name]["contract"].source_spec for name in BANK_ORDER)
    if any(b07_spec[name] != b08_spec[name] for name in eval_fields):
        raise ValueError("B09 source banks do not share the fixed evaluation protocol")
    if (
        b07_spec["n_agents"] != 6
        or b07_spec["n_users"] != 50
        or b07_spec["k"] != 10
        or b07_spec["horizon"] != 500
        or b07_spec["eval_lanes"] != 32
        or b07_spec["eval_world_base"] != 1700200
    ) and not (b07_spec.get("small_model") and b08_spec.get("small_model")):
        raise ValueError("B09 production evaluation protocol differs")
    return inputs


def _restore_agent(
    input_info: Mapping[str, Any], out: Path, device: torch.device
) -> tuple[TrainingLawAgent, b07.Spec, dict[str, Any]]:
    contract: BankContract = input_info["contract"]
    spec = b07.Spec(**dict(contract.source_spec))
    envs = b07.make_envs(spec, 1, spec.eval_world_base)
    try:
        config = b07.make_config(spec, envs, "U")
    finally:
        for env in envs:
            env.close()
    config_snapshot = effective_config(config)
    if config_snapshot != input_info["summary"].get("learner_config"):
        raise ValueError(f"{contract.bank} constructed config differs from source")
    b07.seed_rng(spec.init_seed)
    agent = b07._build_agent(spec, config, "U", out / f"{contract.bank}_learner", device)
    if agent.config.n_Z != 6 or agent.config.n_z != 6:
        raise ValueError(f"{contract.bank} restored skill cardinality differs from six")
    checkpoint = input_info["checkpoint"]
    for name in b01.MODULES:
        getattr(agent, name).load_state_dict(checkpoint["native"][name], strict=True)
    for name in b01.NORMALIZERS:
        setattr(agent, name, copy.deepcopy(checkpoint["normalizers"][name]))
    agent.load_auxiliary_state_dict(checkpoint["auxiliary"])
    rng = checkpoint["rng"]
    agent.load_rng_stream_state_dict(rng["private_streams"])
    agent.load_sampler_rng_state_dict(rng["rollout_samplers"])
    b07._restore_process_rng_state(rng["default_process"])
    if not b05._nested_equal(b07._capture_process_rng_state(), rng["default_process"]):
        raise ValueError(f"{contract.bank} restored process RNG differs")
    agent.train(False)
    for name in (*b01.MODULES, "g_head", "p_head"):
        module = getattr(agent, name, None)
        if module is not None:
            module.eval()
            for parameter in module.parameters():
                parameter.requires_grad_(False)
    native = b07.native_digest(agent)
    frozen = b07.frozen_digest(agent)
    if native != contract.final_native_digest or frozen != contract.final_frozen_digest:
        raise ValueError(f"{contract.bank} restored native/frozen digest differs")
    if agent.rng_stream_telemetry() != input_info["summary"].get("final_private_rng_streams"):
        raise ValueError(f"{contract.bank} restored private RNG streams differ")
    if agent.sampler_rng_telemetry() != input_info["summary"].get("final_sampler_rng_streams"):
        raise ValueError(f"{contract.bank} restored sampler RNG streams differ")
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
        raise ValueError(f"{contract.bank} fresh native optimizers are not idle")
    auxiliary_optimizer_entries = {
        name: len(optimizer.state_dict()["state"])
        for name in ("g_head_optimizer", "p_head_optimizer", "auxiliary_trunk_optimizer")
        for optimizer in (getattr(agent, name, None),)
        if optimizer is not None
    }
    return agent, spec, {
        "native_digest": native,
        "frozen_digest": frozen,
        "private_rng_streams": agent.rng_stream_telemetry(),
        "sampler_rng_streams": agent.sampler_rng_telemetry(),
        "optimizer_restore": {
            "native": {
                "checkpoint_state_present": False,
                "handling": "fresh idle native optimizers; source checkpoint has no native optimizer state",
                "state_entries": native_optimizer_entries,
            },
            "auxiliary": {
                "checkpoint_state_present": True,
                "handling": "restored serialized auxiliary optimizer state",
                "state_entries": auxiliary_optimizer_entries,
            },
        },
    }


def _hash_array(value: np.ndarray) -> bytes:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest().encode()


def _save_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> dict[str, Any]:
    np.savez_compressed(path, **arrays)
    return {
        **_file_identity(path, str(path.parent.name + "/" + path.name)),
        "arrays": {name: _array_identity(value) for name, value in arrays.items()},
    }


def _proposal_arrays(spec: b07.Spec) -> dict[str, np.ndarray]:
    renewals = spec.horizon // spec.k
    return {
        "renewal_steps": np.arange(renewals, dtype=np.int32) * spec.k,
        "team_proposals": np.empty((renewals, spec.eval_lanes), np.int16),
        "individual_proposals": np.empty((renewals, spec.eval_lanes, spec.n_agents), np.int16),
        "team_proposal_log_probs": np.full((renewals, spec.eval_lanes), UNIFORM_LOG_FACTOR, np.float32),
        "individual_proposal_log_probs": np.full(
            (renewals, spec.eval_lanes, spec.n_agents), UNIFORM_LOG_FACTOR, np.float32
        ),
        "delivered_team_labels": np.empty((renewals, spec.eval_lanes), np.int16),
        "delivered_individual_labels": np.empty(
            (renewals, spec.eval_lanes, spec.n_agents), np.int16
        ),
        "delivered_team_log_probs": np.full(
            (renewals, spec.eval_lanes), UNIFORM_LOG_FACTOR, np.float32
        ),
        "delivered_individual_log_probs": np.empty(
            (renewals, spec.eval_lanes, spec.n_agents), np.float32
        ),
    }


def evaluate_panel(
    agent: TrainingLawAgent,
    spec: b07.Spec,
    bank: str,
    mode: str,
    stream: str,
    out: Path,
    *,
    counter: dict[str, int],
    call_audit: b05.EvaluationCallAudit,
) -> dict[str, Any]:
    """Evaluate one R or H panel with the frozen original low-policy path."""

    if bank not in BANK_ORDER or mode not in {"R", "H"} or stream not in STREAM_ORDER:
        raise ValueError(f"invalid B09 panel {bank}_{mode}_{stream}")
    arrays = b05._allocate_trajectory(
        spec, agent.config.state_dim, agent.config.obs_dim, agent.config.action_dim
    )
    proposals = _proposal_arrays(spec)
    flow = {
        "hidden_input_sha256": np.empty(spec.horizon, dtype="S64"),
        "hidden_output_sha256": np.empty(spec.horizon, dtype="S64"),
        "hidden_input_l2": np.empty((spec.horizon, spec.eval_lanes, spec.n_agents), np.float32),
        "hidden_output_l2": np.empty((spec.horizon, spec.eval_lanes, spec.n_agents), np.float32),
    }
    panel_key = f"{bank}_{mode}{stream[1:]}"
    trajectory_path = out / "raw" / f"{panel_key}_trajectory.npz"
    proposal_path = out / "raw" / f"{panel_key}_proposal_delivery.npz"
    flow_path = out / "raw" / f"{panel_key}_recurrent_flow.npz"
    panel_path = out / "raw" / f"{panel_key}.json"
    r_rng = np.random.Generator(np.random.PCG64(R_SEEDS[stream]))
    label_digest, initial_digest = hashlib.sha256(), hashlib.sha256()
    audit_before = call_audit.snapshot()
    envs: list[Any] = []
    completed_steps = saturation = action_coordinates = completed_renewals = 0
    held_individual: np.ndarray | None = None
    try:
        with b07._frozen_evaluation(agent) as frozen_before:
            b07.seed_rng(NON_LABEL_SEED)
            envs = b07.make_envs(spec, spec.eval_lanes, spec.eval_world_base)
            states, observations = b01.native._reset_all(envs)
            b07.update_digest(initial_digest, states, observations)
            hidden = np.zeros(
                (spec.eval_lanes, spec.n_agents, agent.config.gru_hidden_size), np.float32
            )
            arrays["states"][0] = states
            arrays["observations"][0] = observations
            team = individual = None
            for t in range(spec.horizon):
                if t % spec.k == 0:
                    renewal = t // spec.k
                    proposed_team = r_rng.integers(
                        0, 6, size=spec.eval_lanes, dtype=np.int64
                    )
                    proposed_individual = r_rng.integers(
                        0, 6, size=(spec.eval_lanes, spec.n_agents), dtype=np.int64
                    )
                    if held_individual is None:
                        held_individual = proposed_individual.copy()
                    team = proposed_team
                    individual = (
                        proposed_individual if mode == "R" else held_individual
                    )
                    delivered_individual_lp = np.full(
                        (spec.eval_lanes, spec.n_agents),
                        UNIFORM_LOG_FACTOR if renewal == 0 or mode == "R" else 0.0,
                        np.float32,
                    )
                    order = np.broadcast_to(
                        np.arange(spec.n_agents, dtype=np.int64),
                        (spec.eval_lanes, spec.n_agents),
                    ).copy()
                    proposals["team_proposals"][renewal] = proposed_team
                    proposals["individual_proposals"][renewal] = proposed_individual
                    proposals["delivered_team_labels"][renewal] = team
                    proposals["delivered_individual_labels"][renewal] = individual
                    proposals["delivered_individual_log_probs"][renewal] = delivered_individual_lp
                    arrays["renewal"][t] = True
                    arrays["team_factor_log_probs"][t] = UNIFORM_LOG_FACTOR
                    arrays["individual_factor_log_probs"][t] = delivered_individual_lp
                    arrays["renewal_order"][t] = order
                    b07.update_digest(
                        label_digest, np.asarray([t], np.int64), team, individual
                    )
                    completed_renewals = renewal + 1
                    counter["proposal_batches"] += 1
                    counter["team_proposals"] += spec.eval_lanes
                    counter["individual_proposals"] += spec.eval_lanes * spec.n_agents
                if team is None or individual is None:
                    raise RuntimeError("B09 labels were not assigned before low control")
                arrays["team_labels"][t] = team
                arrays["individual_labels"][t] = individual
                flow["hidden_input_sha256"][t] = _hash_array(hidden)
                flow["hidden_input_l2"][t] = np.linalg.norm(hidden, axis=-1)
                raw_actions, hidden = b01.low_actions(
                    agent, observations, individual, hidden, deterministic=True
                )
                counter["low_action_forward_batches"] += 1
                flow["hidden_output_sha256"][t] = _hash_array(hidden)
                flow["hidden_output_l2"][t] = np.linalg.norm(hidden, axis=-1)
                clipped = np.clip(raw_actions, -1.0, 1.0)
                arrays["raw_mean_actions"][t] = raw_actions
                arrays["clipped_actions"][t] = clipped
                saturation += int((np.abs(raw_actions) > 1).sum())
                action_coordinates += raw_actions.size
                next_states, next_observations = [], []
                for lane, env in enumerate(envs):
                    state, observation, reward, done, parts, executed = b01.physical_step(
                        env, raw_actions[lane]
                    )
                    if not np.array_equal(executed, clipped[lane]):
                        raise RuntimeError("B09 recorded clip differs from physical action")
                    if done != (t == spec.horizon - 1):
                        raise ValueError("unexpected B09 evaluation episode boundary")
                    next_states.append(state)
                    next_observations.append(observation)
                    arrays["rewards"][t, lane] = reward
                    arrays["episode_ends"][t, lane] = done
                    for component in b01.COMPONENTS:
                        arrays[component][t, lane] = parts[component]
                    counter["evaluation_transitions"] += 1
                    counter["evaluation_agent_transitions"] += spec.n_agents
                    counter["evaluation_episodes"] += int(done)
                    counter[f"{mode}_transitions"] += 1
                    counter[f"{mode}_agent_transitions"] += spec.n_agents
                states, observations = np.stack(next_states), np.stack(next_observations)
                arrays["states"][t + 1] = states
                arrays["observations"][t + 1] = observations
                completed_steps = t + 1
            panel_summary = b05._panel_summary_from_trajectory(
                stream, spec, arrays, label_digest, initial_digest, saturation, action_coordinates
            )
            panel_summary.update(
                panel=panel_key,
                bank=bank,
                mode=mode,
                stream=stream,
                law=(
                    "original independent-uniform k10 team and individual redraw"
                    if mode == "R"
                    else "original k10 PCG64 proposals; team redraw delivered; opening individual labels held H500"
                ),
                frozen_state_before=frozen_before,
            )
    except BaseException as exc:
        partial = {
            "status": "failed",
            "panel": panel_key,
            "completed_steps": completed_steps,
            "completed_renewals": completed_renewals,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "actual_counts_at_failure": dict(counter),
        }
        if completed_steps:
            partial["trajectory"] = b05._save_npz(trajectory_path, arrays, completed_steps)
            partial["proposal_delivery"] = _save_npz(
                proposal_path,
                {name: value[:completed_renewals] for name, value in proposals.items()},
            )
            partial["recurrent_flow"] = _save_npz(
                flow_path, {name: value[:completed_steps] for name, value in flow.items()}
            )
        b07.write_json(panel_path, partial)
        raise
    finally:
        for env in envs:
            env.close()
    mutation_delta = b05._counter_delta(call_audit.snapshot(), audit_before)
    if any(mutation_delta.values()):
        raise RuntimeError("B09 evaluation reached a prohibited mutation path")
    panel_summary["observed_mutation_calls"] = mutation_delta
    panel_summary["label_rng"] = {
        "kind": "PCG64",
        "seed": R_SEEDS[stream],
        "draw_order": "team[eval_lanes] then individual[eval_lanes,n_agents] at each k10 renewal",
        "proposal_log_probability": float(UNIFORM_LOG_FACTOR),
        "delivery_law": (
            "proposal equals delivery"
            if mode == "R"
            else "team proposal delivered; opening individual proposal uniform, later individual delivery deterministic conditional on opening vector"
        ),
        "later_H_delivered_individual_log_probability": 0.0 if mode == "H" else None,
    }
    panel_summary["non_label_rng_seed"] = NON_LABEL_SEED
    panel_summary["trajectory"] = b05._save_npz(trajectory_path, arrays, completed_steps)
    panel_summary["proposal_delivery"] = _save_npz(proposal_path, proposals)
    panel_summary["recurrent_flow"] = _save_npz(flow_path, flow)
    b07.write_json(panel_path, panel_summary)
    return panel_summary


def _compare_saved_r(
    actual_path: Path, reference_path: Path
) -> dict[str, Any]:
    actual, reference = _load_npz(actual_path), _load_npz(reference_path)
    if tuple(actual) != tuple(reference):
        raise RuntimeError("B09 regenerated R array keys differ from the saved source")
    arrays: dict[str, Any] = {}
    for name in reference:
        left, right = actual[name], reference[name]
        left_identity, right_identity = _array_identity(left), _array_identity(right)
        exact = left_identity == right_identity
        arrays[name] = {
            "actual": left_identity,
            "reference": right_identity,
            "exact": exact,
        }
        if not exact:
            raise RuntimeError(f"B09 regenerated R array differs: {name}")
    return {"exact": True, "array_keys": list(actual), "arrays": arrays}


def _step_changed(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if left.shape != right.shape or left.shape[0] != right.shape[0]:
        raise ValueError("B09 paired arrays have incompatible step axes")
    return np.asarray(
        [not np.array_equal(left[index], right[index]) for index in range(left.shape[0])],
        np.bool_,
    )


def _pair_divergence(out: Path, bank: str, stream: str, k: int) -> dict[str, Any]:
    r_key, h_key = f"{bank}_R{stream[1:]}", f"{bank}_H{stream[1:]}"
    r, h = (_load_npz(out / "raw" / f"{key}_trajectory.npz") for key in (r_key, h_key))
    rp, hp = (
        _load_npz(out / "raw" / f"{key}_proposal_delivery.npz")
        for key in (r_key, h_key)
    )
    rf, hf = (
        _load_npz(out / "raw" / f"{key}_recurrent_flow.npz")
        for key in (r_key, h_key)
    )
    for name in (
        "renewal_steps",
        "team_proposals",
        "individual_proposals",
        "team_proposal_log_probs",
        "individual_proposal_log_probs",
    ):
        if _array_identity(rp[name]) != _array_identity(hp[name]):
            raise RuntimeError(f"B09 H/R proposal stream differs: {bank} {stream} {name}")
    first_k = {
        "team_labels": (r["team_labels"][:k], h["team_labels"][:k]),
        "individual_labels": (r["individual_labels"][:k], h["individual_labels"][:k]),
        "raw_mean_actions": (r["raw_mean_actions"][:k], h["raw_mean_actions"][:k]),
        "clipped_actions": (r["clipped_actions"][:k], h["clipped_actions"][:k]),
        "states": (r["states"][: k + 1], h["states"][: k + 1]),
        "observations": (r["observations"][: k + 1], h["observations"][: k + 1]),
        "hidden_input": (rf["hidden_input_sha256"][:k], hf["hidden_input_sha256"][:k]),
        "hidden_output": (rf["hidden_output_sha256"][:k], hf["hidden_output_sha256"][:k]),
    }
    first_k_exact = {
        name: _array_identity(left) == _array_identity(right)
        for name, (left, right) in first_k.items()
    }
    if not all(first_k_exact.values()):
        raise RuntimeError(f"B09 H/R first-k identity differs: {bank} {stream}")
    changed = {
        "individual_labels": _step_changed(r["individual_labels"], h["individual_labels"]),
        "raw_mean_actions": _step_changed(r["raw_mean_actions"], h["raw_mean_actions"]),
        "clipped_actions": _step_changed(r["clipped_actions"], h["clipped_actions"]),
        "physical_states": _step_changed(r["states"][1:], h["states"][1:]),
        "observations": _step_changed(r["observations"][1:], h["observations"][1:]),
        "hidden_input": rf["hidden_input_sha256"] != hf["hidden_input_sha256"],
        "hidden_output": rf["hidden_output_sha256"] != hf["hidden_output_sha256"],
        "rewards": _step_changed(r["rewards"], h["rewards"]),
        "coverage": _step_changed(r["coverage_reward"], h["coverage_reward"]),
        "quality": _step_changed(r["quality_reward"], h["quality_reward"]),
        "height": _step_changed(r["energy_penalty"], h["energy_penalty"]),
    }
    path = out / "raw" / f"{bank}_H{stream[1:]}_vs_R{stream[1:]}_divergence.npz"
    locator = _save_npz(path, changed)
    summary: dict[str, Any] = {
        "first_k": k,
        "first_k_exact": first_k_exact,
        "proposal_stream_exact": True,
        "trace": locator,
        "changed_step_counts": {},
        "first_changed_step": {},
    }
    for name, values in changed.items():
        indices = np.flatnonzero(values)
        summary["changed_step_counts"][name] = int(indices.size)
        summary["first_changed_step"][name] = int(indices[0]) if indices.size else None
    return summary


def aggregate_bank(
    panels: Mapping[str, Mapping[str, Any]], bank: str, spec: b07.Spec
) -> dict[str, Any]:
    worlds = np.arange(spec.eval_world_base, spec.eval_world_base + spec.eval_lanes)
    result: dict[str, Any] = {"worlds": worlds}
    for metric in ("J", "users", "coverage", "quality", "height"):
        r_streams = np.stack(
            [b05._metric_arrays(panels[f"{bank}_R{i}"])[metric] for i in range(4)]
        )
        h_streams = np.stack(
            [b05._metric_arrays(panels[f"{bank}_H{i}"])[metric] for i in range(4)]
        )
        mean_r, mean_h = r_streams.mean(axis=0), h_streams.mean(axis=0)
        delta = mean_h - mean_r
        result[metric] = {
            "world_mean_R4": mean_r,
            "world_mean_H4": mean_h,
            "H_minus_R_world": delta,
            "mean_R4": float(mean_r.mean()),
            "mean_H4": float(mean_h.mean()),
            "H_minus_R": float(delta.mean()),
            "R_stream_world_values": {f"R{i}": r_streams[i] for i in range(4)},
            "H_stream_world_values": {f"H{i}": h_streams[i] for i in range(4)},
            "paired_stream_H_minus_R_world": {
                f"H{i}_minus_R{i}": h_streams[i] - r_streams[i] for i in range(4)
            },
        }
    return result


def _directory_bytes(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _resource_row(
    started: float, cpu_started: resource.struct_rusage, out: Path, device: torch.device
) -> dict[str, Any]:
    current = resource.getrusage(resource.RUSAGE_SELF)
    row = {
        "wall_seconds": time.perf_counter() - started,
        "user_cpu_seconds": current.ru_utime - cpu_started.ru_utime,
        "system_cpu_seconds": current.ru_stime - cpu_started.ru_stime,
        "peak_rss_bytes": int(current.ru_maxrss * (1024 if sys.platform != "darwin" else 1)),
        "peak_rss_scope": "process lifetime as reported by getrusage(RUSAGE_SELF)",
        "output_bytes": _directory_bytes(out),
        "peak_scratch_bytes": None,
        "shared_node_occupancy": None,
        "resources_unmeasured": ["peak_scratch_bytes", "shared_node_occupancy"],
    }
    if device.type == "cuda" and torch.cuda.is_initialized():
        row.update(
            peak_cuda_allocated_bytes=int(torch.cuda.max_memory_allocated(device)),
            peak_cuda_reserved_bytes=int(torch.cuda.max_memory_reserved(device)),
            cuda_scope="both restored banks and all fixed panels in this process",
        )
    else:
        row.update(peak_cuda_allocated_bytes=None, peak_cuda_reserved_bytes=None)
    return row


def _write_progress(out: Path, summary: Mapping[str, Any]) -> None:
    b07.write_json(
        out / "progress.json",
        {
            "object_id": OBJECT,
            "status": summary["status"],
            "panel_order": summary["panel_order"],
            "completed_panels": summary["completed_panels"],
            "r_reproduction_gate": summary["r_reproduction_gate"],
            "counts": summary["counts"],
            "failure": summary.get("failure"),
        },
    )


def run_evaluation(
    b07_input_root: Path | str,
    b08_input_root: Path | str,
    out: Path | str,
    launch_sha: str,
    *,
    device: str | torch.device = "cuda",
    admission: Mapping[str, Any] | None = None,
    contracts: Mapping[str, BankContract] = PRODUCTION_CONTRACTS,
) -> dict[str, Any]:
    """Run the fixed eight-R-then-eight-H batch once."""

    inputs = validate_inputs(b07_input_root, b08_input_root, contracts)
    device = torch.device(device)
    if contracts is PRODUCTION_CONTRACTS:
        if admission is None:
            raise ValueError("B09 production evaluation requires native admission")
        if admission.get("sha") != launch_sha:
            raise ValueError("B09 launch SHA differs from native admission")
        if device.type != "cuda":
            raise ValueError("B09 production evaluation requires original CUDA semantics")
    out = b05.prepare_output_root(out, admission)
    (out / "raw").mkdir()
    threads = int(inputs["B07"]["contract"].source_spec["threads"])
    torch.set_num_threads(threads)
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
        "evaluation_agent_transitions": 0,
        "evaluation_episodes": 0,
        "R_transitions": 0,
        "R_agent_transitions": 0,
        "H_transitions": 0,
        "H_agent_transitions": 0,
        "low_action_forward_batches": 0,
        "proposal_batches": 0,
        "team_proposals": 0,
        "individual_proposals": 0,
    }
    source_view = {
        bank: {
            "root": inputs[bank]["root"],
            "source_launch_sha": inputs[bank]["contract"].source_launch_sha,
            "adapter_protocol_id": inputs[bank]["contract"].adapter_protocol_id,
            "source_spec": inputs[bank]["contract"].source_spec,
            "files": inputs[bank]["identities"],
        }
        for bank in BANK_ORDER
    }
    summary: dict[str, Any] = {
        "object_id": OBJECT,
        "direction": DIRECTION,
        "batch_seed_identity": FIXED_SEED,
        "launch_sha": launch_sha,
        "status": "incomplete",
        "device": str(device),
        "admission": admission,
        "panel_order": list(PANEL_ORDER),
        "completed_panels": [],
        "counts": counts,
        "sources": source_view,
        "restored": {},
        "panels": {},
        "r_reproductions": {},
        "r_reproduction_gate": {"required": 8, "passed": 0, "released_H": False},
        "pair_divergence": {},
        "zero_learning": {
            "new_fits": 0,
            "training_transitions": 0,
            "optimizer_updates": 0,
            "storage_calls": 0,
            "normalizer_updates": 0,
        },
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "torch": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "model_dtype": "float32",
            "reward_and_aggregate_dtype": "float64",
            "torch_threads": torch.get_num_threads(),
            "thread_environment": {
                key: os.environ.get(key)
                for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
            },
            "cuda_matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
            "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        },
    }
    config = {
        "object_id": OBJECT,
        "batch_seed_identity": FIXED_SEED,
        "launch_sha": launch_sha,
        "device": str(device),
        "panel_order": list(PANEL_ORDER),
        "source_roots": {bank: inputs[bank]["root"] for bank in BANK_ORDER},
        "source_launch_shas": {
            bank: inputs[bank]["contract"].source_launch_sha for bank in BANK_ORDER
        },
        "evaluation": {
            "worlds": list(range(
                int(inputs["B07"]["contract"].source_spec["eval_world_base"]),
                int(inputs["B07"]["contract"].source_spec["eval_world_base"])
                + int(inputs["B07"]["contract"].source_spec["eval_lanes"]),
            )),
            "non_label_seed": NON_LABEL_SEED,
            "R_seeds": R_SEEDS,
            "H": "hold each lane/agent opening individual label H500; preserve every k10 proposal",
            "R": "original independent-uniform k10 delivery",
            "low_action": "current local observation and recurrent state; deterministic mean then physical clip[-1,1]",
        },
    }
    b07.write_json(out / "config.json", config)
    b07.write_json(out / "source.json", source_view)
    b07.write_json(out / "summary.json", summary)
    _write_progress(out, summary)
    agents: dict[str, TrainingLawAgent] = {}
    specs: dict[str, b07.Spec] = {}
    initial_optimizer: dict[str, Any] = {}
    initial_state: dict[str, Any] = {}
    audits: dict[str, b05.EvaluationCallAudit] = {}
    try:
        for bank in BANK_ORDER:
            agent, spec, restored = _restore_agent(inputs[bank], out, device)
            agents[bank], specs[bank] = agent, spec
            summary["restored"][bank] = restored
            counts["model_constructions"] += 1
            counts["checkpoint_loads"] += 1
            initial_optimizer[bank] = b05._optimizer_states(agent)
            audits[bank] = b05.EvaluationCallAudit(agent)
            audits[bank].__enter__()
        # Process RNG is global.  The second restore deliberately installs its
        # serialized process state, so the common no-leak baseline is taken
        # only after both checkpoints have been restored.
        initial_state = {
            bank: b07._evaluation_state(agents[bank]) for bank in BANK_ORDER
        }
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        for bank in BANK_ORDER:
            for stream in STREAM_ORDER:
                key = f"{bank}_{stream}"
                panel = evaluate_panel(
                    agents[bank], specs[bank], bank, "R", stream, out,
                    counter=counts, call_audit=audits[bank],
                )
                summary["panels"][key] = panel
                comparison = _compare_saved_r(
                    out / "raw" / f"{key}_trajectory.npz",
                    Path(inputs[bank]["root"]) / "raw" / f"final_{stream}_trajectory.npz",
                )
                summary["r_reproductions"][key] = comparison
                summary["r_reproduction_gate"]["passed"] += 1
                summary["completed_panels"].append(key)
                b07.write_json(out / "summary.json", summary)
                _write_progress(out, summary)
        if summary["r_reproduction_gate"]["passed"] != 8:
            raise RuntimeError("B09 did not pass all eight R reconstructions")
        summary["r_reproduction_gate"]["released_H"] = True
        b07.write_json(out / "summary.json", summary)
        _write_progress(out, summary)
        for bank in BANK_ORDER:
            for stream in STREAM_ORDER:
                key = f"{bank}_H{stream[1:]}"
                panel = evaluate_panel(
                    agents[bank], specs[bank], bank, "H", stream, out,
                    counter=counts, call_audit=audits[bank],
                )
                summary["panels"][key] = panel
                summary["pair_divergence"][key] = _pair_divergence(
                    out, bank, stream, specs[bank].k
                )
                summary["completed_panels"].append(key)
                b07.write_json(out / "summary.json", summary)
                _write_progress(out, summary)
        observed_mutations: dict[str, Any] = {}
        for bank in BANK_ORDER:
            observed_mutations[bank] = audits[bank].snapshot()
            if any(observed_mutations[bank].values()):
                raise RuntimeError(f"B09 {bank} reached a prohibited mutation path")
            if not b05._nested_equal(b05._optimizer_states(agents[bank]), initial_optimizer[bank]):
                raise RuntimeError(f"B09 {bank} changed optimizer state")
            if b07._evaluation_state(agents[bank]) != initial_state[bank]:
                raise RuntimeError(f"B09 {bank} changed frozen agent state")
        summary["observed_mutation_calls"] = observed_mutations
        summary["frozen_after"] = {
            bank: b07._evaluation_state(agents[bank]) for bank in BANK_ORDER
        }
        summary["aggregates"] = {
            bank: aggregate_bank(summary["panels"], bank, specs[bank])
            for bank in BANK_ORDER
        }
        summary["aggregate_metric_definitions"] = {
            "J": "native team score; streams averaged within world, then worlds equally",
            "users": "connected users per step; streams averaged within world, then worlds equally",
            "coverage": "coverage_reward per step",
            "quality": "quality_reward per step",
            "height": "energy_penalty per step (historical report label)",
        }
        expected_transitions = sum(
            8 * spec.eval_lanes * spec.horizon for spec in specs.values()
        )
        expected = {
            "started_fits": 0,
            "model_constructions": 2,
            "checkpoint_loads": 2,
            "training_transitions": 0,
            "stored_transitions": 0,
            "native_updates": 0,
            "optimizer_calls": 0,
            "normalizer_updates": 0,
            "evaluation_transitions": expected_transitions,
            "evaluation_agent_transitions": expected_transitions
            * specs["B07"].n_agents,
            "evaluation_episodes": sum(8 * spec.eval_lanes for spec in specs.values()),
            "R_transitions": expected_transitions // 2,
            "R_agent_transitions": expected_transitions
            * specs["B07"].n_agents
            // 2,
            "H_transitions": expected_transitions // 2,
            "H_agent_transitions": expected_transitions
            * specs["B07"].n_agents
            // 2,
            "low_action_forward_batches": sum(8 * spec.horizon for spec in specs.values()),
            "proposal_batches": sum(
                8 * spec.horizon // spec.k for spec in specs.values()
            ),
            "team_proposals": sum(
                8 * spec.horizon // spec.k * spec.eval_lanes for spec in specs.values()
            ),
            "individual_proposals": sum(
                8 * spec.horizon // spec.k * spec.eval_lanes * spec.n_agents
                for spec in specs.values()
            ),
        }
        if counts != expected:
            raise RuntimeError(f"B09 fixed counts differ: {counts}")
        summary["status"] = "complete"
    except BaseException as exc:
        summary["status"] = "failed"
        summary["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "failed_after_completed_panels": list(summary["completed_panels"]),
        }
        raise
    finally:
        for audit in reversed(list(audits.values())):
            audit.__exit__(None, None, None)
        summary["resources"] = _resource_row(started, cpu_started, out, device)
        b07.write_json(out / "summary.json", summary)
        _write_progress(out, summary)
        for _ in range(3):
            measured = _directory_bytes(out)
            if summary["resources"]["output_bytes"] == measured:
                break
            summary["resources"]["output_bytes"] = measured
            b07.write_json(out / "summary.json", summary)
    return summary


__all__ = [
    "ArtifactContract",
    "BANK_ORDER",
    "BankContract",
    "FIXED_SEED",
    "NON_LABEL_SEED",
    "OBJECT",
    "PANEL_ORDER",
    "PRODUCTION_CONTRACTS",
    "R_SEEDS",
    "STREAM_ORDER",
    "aggregate_bank",
    "evaluate_panel",
    "run_evaluation",
    "validate_bank_input",
    "validate_inputs",
]
