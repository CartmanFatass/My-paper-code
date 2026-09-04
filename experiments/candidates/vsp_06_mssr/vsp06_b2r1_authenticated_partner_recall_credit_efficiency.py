
"""Self-contained VSP06-B2R1 authenticated partner-recall learning candidate.

No function in this module runs at import time.  The four-action toy and both
matched arms are local to this file and do not alter ``ha_ctse_process``.
Canonical catalog generation, selector invocation, and a registered full are
separate lifecycle stages; tests use only explicitly noncanonical rows.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path
import random
import stat
import traceback
from typing import Any, Iterable, Iterator, Mapping, Sequence


TREATMENT_ID = (
    "VSP06-B2R1-AUTHENTICATED-PARTNER-RECALL-CREDIT-EFFICIENCY-"
    "SOURCE-BOUND-EXACT-FEASIBILITY"
)
ENVIRONMENT_ID = "AuthenticatedPartnerRecallRelay-v0"
RESOURCE_CLASS = "B_TOY_LIGHT"
CANDIDATE_ARM = "MSSR_P_FIXED_VALIDITY_CARRIER"
GENERIC_ARM = "GENERIC_PROVENANCE_CONDITIONED_CARRIER"
ARMS = (CANDIDATE_ARM, GENERIC_ARM)
BRANCHES = ("KEEP", "RESET", "CURRENT")
ACTIONS = (0, 1, 2, 3)
CHECKPOINTS = (0, 512, 1024, 1536, 2048, 2560, 3072, 4096)
OBSERVATION_DIM = 32
CONTEXT_DIM = 64
CARRIER_DIM = 32
EPISODES_PER_BATCH = 128
PPO_EPOCHS = 4

SEEDS = {
    "calibration": {"environment": 8100501, "initialization": 8100502, "minibatch": 8100503, "evaluation": 8100504},
    "primary_1": {"environment": 8100611, "initialization": 8100612, "minibatch": 8100613, "evaluation": 8100614},
    "primary_2": {"environment": 8100621, "initialization": 8100622, "minibatch": 8100623, "evaluation": 8100624},
    "primary_3": {"environment": 8100631, "initialization": 8100632, "minibatch": 8100633, "evaluation": 8100634},
    "primary_4": {"environment": 8100641, "initialization": 8100642, "minibatch": 8100643, "evaluation": 8100644},
}

PPO = {
    "episodes_per_arm_seed": 4096,
    "episodes_per_batch": EPISODES_PER_BATCH,
    "epochs_per_batch": PPO_EPOCHS,
    "recurrent_truncation": False,
    "recurrent_detachment": False,
    "optimizer": "Adam",
    "lr": 0.0003,
    "epsilon": 0.00001,
    "weight_decay": 0,
    "max_gradient_norm": 0.5,
    "gamma": 1,
    "gae_lambda": 1,
    "clip": 0.2,
    "entropy_coefficient": 0.01,
    "value_coefficient": 0.5,
    "advantage_normalization": "per_complete_batch",
}

CAPS = {
    "model_fits": 10,
    "trainer_invocations": 10,
    "environment_episodes": 44300,
    "environment_transitions": 520000,
    "production_policy_forwards": 540000,
    "learner_updates": 1100,
    "optimizer_steps": 1100,
    "evaluator_calls": 75,
    "evaluation_episodes": 10500,
    "sweeps": 0,
    "retries": 0,
    "rescues": 0,
    "extra_roots": 0,
}

EXPECTED_FULL_ACTIVITY = {
    "model_fits": 10,
    "trainer_invocations": 10,
    "environment_episodes": 44288,
    "environment_transitions": 440320,
    "production_policy_forwards": 473280,
    "learner_updates": 1056,
    "optimizer_steps": 1056,
    "evaluator_calls": 74,
    "evaluation_episodes": 10496,
    "environment_rng_draws": 0,
    "action_rng_draws": 47584,
    "sweeps": 0,
    "retries": 0,
    "rescues": 0,
    "extra_roots": 0,
}
ACTIVITY_COUNTERS = {
    "canonical_generator_calls": 0, "canonical_rows_observed": 0, "canonical_ortools_processes": 0,
    "replicas": 0, "canonical_verifier_admissions": 0, "witnesses": 0, "manifests": 0,
    "model_fits": 0, "trainer_calls": 0, "environment_episodes": 0, "environment_transitions": 0,
    "policy_forwards": 0, "learner_updates": 0, "optimizer_steps": 0, "evaluator_calls": 0,
    "evaluation_episodes": 0, "environment_rng_calls": 0, "action_rng_calls": 0,
}
DIRECTION_ID = "CAND-VSP-06-MSSR"
CANDIDATE_ID = "CAND-VSP-06-MSSR@adversarial-revision-v8"
SCIENTIFIC_PARENT = "898af9e848ce45f3510560a96ae454651a9f0736"
SYNTHETIC_DOMAIN = "VSP06-B2R1-SYNTHETIC-NONCANONICAL-V1"
SYNTHETIC_SUCCESS = "SYNTHETIC_STRUCTURAL_VALID_ONLY"
UNIVERSE_SPEC_ID = "VSP06-B2R1-INDEPENDENT-CANONICAL-UNIVERSE-SPEC-V1"
SOURCE_CONFIG_RELATIVE_PATHS = (
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_source_bound_exact_feasibility.py",
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_independent_exact_manifest_verifier.py",
    "experiments/candidates/vsp_06_mssr/vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "scripts/run_vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "tests/experiments/candidates/vsp_06_mssr/test_vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    "docs/research/legacy/directions/vsp_06_mssr/VSP06_B2R1_CONSTRAINT_TARGET_LEDGER_V1.json",
    "docs/research/legacy/directions/vsp_06_mssr/VSP06_B2R1_CODE_SCIENCE_INDEX.md",
)


def validate_stage2_authorization(value: Mapping[str, Any]) -> None:
    from_ids = {
        "direction": DIRECTION_ID, "candidate": CANDIDATE_ID, "treatment_id": TREATMENT_ID,
        "selector_id": "VSP06-B2R1-SB-EF-CP-SAT-V1",
        "verifier_id": "VSP06-B2R1-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1",
        "scientific_parent": SCIENTIFIC_PARENT, "formal": False, "synthetic_only": False,
    }
    required = set(from_ids) | {
        "final_commit", "source_build_read_allowlist", "source_config_digest_map",
        "source_config_digest_map_sha256", "zero_start_activity",
        "full_environment_receipt_path", "full_environment_receipt_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != required or any(
        type(value.get(k)) is not type(v) or value.get(k) != v
        for k, v in from_ids.items()
    ):
        raise B2ContractError("missing or invalid Stage-2 authorization binding")
    commit = value.get("final_commit")
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise B2ContractError("invalid Stage-2 final commit binding")
    activity = value.get("zero_start_activity")
    if (
        not isinstance(value.get("source_build_read_allowlist"), list)
        or not value["source_build_read_allowlist"]
        or not isinstance(activity, Mapping) or set(activity) != set(ACTIVITY_COUNTERS)
        or any(not isinstance(item, int) or isinstance(item, bool) or item != 0 for item in activity.values())
    ):
        raise B2ContractError("invalid Stage-2 allowlist or zero-start binding")
    environment_path = value.get("full_environment_receipt_path")
    environment_digest = value.get("full_environment_receipt_sha256")
    if (
        not isinstance(environment_path, str) or not Path(environment_path).is_absolute()
        or ".." in Path(environment_path).parts or any(char in environment_path for char in "*?[")
        or not isinstance(environment_digest, str) or len(environment_digest) != 64
        or any(char not in "0123456789abcdef" for char in environment_digest)
    ):
        raise B2ContractError("invalid external full-environment receipt anchor")
    digest_map = value.get("source_config_digest_map")
    digest_map_digest = value.get("source_config_digest_map_sha256")
    if (
        not isinstance(digest_map, Mapping)
        or set(digest_map) != set(SOURCE_CONFIG_RELATIVE_PATHS)
        or any(
            not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            for digest in digest_map.values()
        )
        or not isinstance(digest_map_digest, str) or len(digest_map_digest) != 64
        or any(char not in "0123456789abcdef" for char in digest_map_digest)
        or digest_map_digest != hashlib.sha256(_json_bytes(dict(digest_map))).hexdigest()
    ):
        raise B2ContractError("invalid Explorer-audited source/config digest map")


def reject_synthetic_envelope_for_full(envelope: Mapping[str, Any]) -> None:
    if isinstance(envelope, Mapping) and (envelope.get("synthetic_only") is True or envelope.get("domain") == SYNTHETIC_DOMAIN or envelope.get("status") == SYNTHETIC_SUCCESS):
        raise B2ContractError("synthetic verification cannot unlock the registered full")
    raise B2ContractError("registered full requires Stage-2 file bindings")

THRESHOLDS = {
    "navigation_band": 0.08,
    "candidate_final_keep_floor": 0.55,
    "selected_p_mediation": 0.20,
    "cross_swap_follow_rate": 0.80,
    "candidate_decoy_accuracy_change": 0.02,
    "candidate_decoy_kernel_tv_change": 0.02,
    "current_arm_aulc_gap": 0.05,
    "reset_stale_target_rate": 0.15,
}

INVALID = "B2R1_INVALID_CONTRACT_ACTIVITY_CAP_OR_PROVENANCE"
NAVIGATION_FAIL = "B2R1_NAVIGATION_OR_CANDIDATE_FINAL_KEEP_GATE_FAILS"
MEDIATION_FAIL = "B2R1_SELECTED_P_MEDIATION_GATE_FAILS"
CROSS_SWAP_FAIL = "B2R1_SELECTED_P_CROSS_SWAP_GATE_FAILS"
DECOY_FAIL = "B2R1_DECOY_INVARIANCE_GATE_FAILS"
CURRENT_RESET_FAIL = "B2R1_CURRENT_OR_RESET_CONTROL_GATE_FAILS"
NO_EFFICIENCY = "B2R1_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_NOT_SUPPORTED"
SUPPORTED = "B2R1_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_SUPPORTED"


class B2ContractError(RuntimeError):
    """Fail-closed B2 candidate contract error."""


_STAGE2_RUNTIME_AUTHORIZED = False
_BOUND_FULL_ENVIRONMENT: tuple[Mapping[str, Any], Mapping[str, Any]] | None = None


def _torch() -> Any:
    if not _STAGE2_RUNTIME_AUTHORIZED or _BOUND_FULL_ENVIRONMENT is None:
        raise B2ContractError("Torch/model/RNG activity requires validated Stage-2 full authorization")
    try:
        import torch
    except ImportError as exc:
        raise B2ContractError("PyTorch is required only for learner/full execution") from exc
    authorization, receipt = _BOUND_FULL_ENVIRONMENT
    _validate_live_torch(torch, authorization, receipt)
    return torch


def _validate_live_torch(
    torch: Any, authorization: Mapping[str, Any], receipt: Mapping[str, Any],
) -> None:
    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector

    try:
        distribution = importlib.metadata.distribution("torch")
    except importlib.metadata.PackageNotFoundError as exc:
        raise B2ContractError("torch==2.7.0 distribution is absent") from exc
    artifacts = []
    inventory = sorted(str(item) for item in (distribution.files or ()))
    for item in sorted(distribution.files or (), key=lambda entry: str(entry)):
        if Path(str(item)).suffix.lower() not in {".pyd", ".so", ".dll"}:
            continue
        artifact = selector.authorize_read_path(
            authorization, Path(distribution.locate_file(item)).resolve()
        )
        artifacts.append([str(artifact), selector.sha256_authorized_file(authorization, artifact)])
    actual = {
        "torch_distribution_version": distribution.version,
        "torch_build_version": str(torch.__version__),
        "torch_cpu_only": getattr(torch.version, "cuda", None) is None,
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "torch_deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
        "torch_deterministic_warn_only": bool(torch.is_deterministic_algorithms_warn_only_enabled()),
        "torch_num_threads": int(torch.get_num_threads()),
        "torch_num_interop_threads": int(torch.get_num_interop_threads()),
        "torch_native_artifacts": artifacts,
        "torch_native_artifact_set_sha256": selector.sha256_bytes(selector._canonical_json_bytes(artifacts)),
        "torch_distribution_inventory_sha256": selector.sha256_bytes(
            selector._canonical_json_bytes(inventory)
        ),
        "torch_build_config_sha256": selector.sha256_bytes(
            str(torch.__config__.show()).encode("utf-8")
        ),
        "thread_environment": {name: os.environ.get(name) for name in selector.THREAD_ENVIRONMENT},
    }
    if (
        distribution.version != selector.REQUIRED_TORCH
        or str(torch.__version__).split("+", 1)[0] != selector.REQUIRED_TORCH
        or not artifacts
        or any(receipt.get(name) != value for name, value in actual.items())
    ):
        raise B2ContractError("live CPU-only Torch build/determinism/thread binding differs from external receipt")


def bind_full_environment(
    authorization: Mapping[str, Any], receipt: Mapping[str, Any],
) -> None:
    """Bind the exact CPU-only Torch environment before catalog/manifest observation."""

    global _BOUND_FULL_ENVIRONMENT
    validate_stage2_authorization(authorization)
    try:
        import torch
    except ImportError as exc:
        raise B2ContractError("PyTorch is required for full-environment readiness") from exc
    _validate_live_torch(torch, authorization, receipt)
    _BOUND_FULL_ENVIRONMENT = (authorization, dict(receipt))


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class EpisodeSpec:
    consumer: str
    seed_row: str
    panel: str
    branch: str
    retention_length: int
    y: int
    reset_y: int
    target_identity: int
    target_version: int
    event_type: str
    decoy_sequence: tuple[tuple[int, int, int, bool], ...]
    current_bytes: str
    roster: str
    legal_mask: str
    clock: str
    rng_binding: str
    quartet_base: str
    nonce: int

    @classmethod
    def from_manifest_row(cls, row: Mapping[str, Any]) -> "EpisodeSpec":
        if not isinstance(row, Mapping):
            raise B2ContractError("manifest tuple is not an object")
        try:
            result = cls(
                consumer=str(row["consumer"]), seed_row=str(row["seed_row"]),
                panel=str(row["panel"]), branch=str(row["branch"]),
                retention_length=int(row["retention_length"]), y=int(row["y"]),
                reset_y=int(row["reset_y"]), target_identity=int(row["target_identity"]),
                target_version=int(row["target_version"]), event_type=str(row["event_type"]),
                decoy_sequence=tuple(tuple(item) for item in row["decoy_sequence"]),
                current_bytes=str(row["current_bytes"]), roster=str(row["roster"]),
                legal_mask=str(row["legal_mask"]), clock=str(row["clock"]),
                rng_binding=str(row["rng_binding"]), quartet_base=str(row["quartet_base"]),
                nonce=int(row["nonce"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise B2ContractError("manifest tuple cannot be decoded") from exc
        result.validate()
        return result


    def validate(self) -> None:
        if self.branch not in BRANCHES or self.retention_length not in {4, 6, 8}:
            raise B2ContractError("episode branch/length is outside the frozen toy")
        if self.y not in ACTIONS or self.reset_y not in ACTIONS:
            raise B2ContractError("episode payload is outside the four-action alphabet")
        if self.target_identity not in ACTIONS or self.target_version not in ACTIONS:
            raise B2ContractError("episode identity/version is outside the frozen domain")
        if self.roster != "P0,P1,P2,P3,focal" or self.legal_mask != "1111":
            raise B2ContractError("episode roster/action mask changed")
        if len(self.decoy_sequence) != 4 or any(
            len(item) != 4 or item[0] not in ACTIONS or item[1] not in ACTIONS
            or item[2] not in ACTIONS or not isinstance(item[3], bool)
            for item in self.decoy_sequence
        ):
            raise B2ContractError("ordered decoy provenance/content changed")


@dataclass(frozen=True)
class Step:
    observation: tuple[float, ...]
    write: int
    reset: int
    phase: str


@dataclass(frozen=True)
class ToyEpisode:
    steps: tuple[Step, ...]
    terminal_target: int
    historical_target: int
    selected_identity: int
    selected_version: int
    branch: str


def branch_terminal_contract(spec: EpisodeSpec) -> tuple[int, int, int, int | None]:
    """Pure KEEP/RESET/CURRENT terminal target and routing contract."""

    spec.validate()
    if spec.branch == "RESET":
        return spec.reset_y, 1, 1, spec.reset_y
    if spec.branch == "CURRENT":
        return spec.y, 1, 0, spec.y
    return spec.y, 0, 0, None


class AuthenticatedPartnerRecallRelay:
    """Four-action, one-focal/four-scripted-partner deterministic toy builder."""

    phases = ("SELECT", "ACQUIRE", "RETAIN", "REJOIN", "ACT")
    event_types = ("target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster")

    @staticmethod
    def _observation(
        *, phase: str, event_type: str, source: int, version: int,
        authenticated: bool, selected: bool, payload: int | None,
        clock: int, branch: str,
    ) -> tuple[float, ...]:
        vector = [0.0] * OBSERVATION_DIM
        vector[AuthenticatedPartnerRecallRelay.phases.index(phase)] = 1.0
        if event_type in AuthenticatedPartnerRecallRelay.event_types:
            vector[5 + AuthenticatedPartnerRecallRelay.event_types.index(event_type)] = 1.0
        if source in ACTIONS:
            vector[9 + source] = 1.0
        vector[13] = float(version) / 3.0
        vector[14] = float(authenticated)
        vector[15] = float(selected)
        if payload in ACTIONS:
            vector[16 + int(payload)] = 1.0
        vector[20] = float(clock) / 8.0
        vector[21 + BRANCHES.index(branch)] = 1.0
        vector[24:28] = [1.0, 1.0, 1.0, 1.0]
        vector[28] = 1.0
        vector[29] = float(source == 4)
        vector[30] = float(phase == "ACT")
        vector[31] = 1.0
        return tuple(vector)

    def build(self, spec: EpisodeSpec) -> ToyEpisode:
        spec.validate()
        identity, version = spec.target_identity, spec.target_version
        steps = [Step(self._observation(
            phase="SELECT", event_type="dummy_roster", source=identity,
            version=version, authenticated=True, selected=True, payload=None,
            clock=0, branch=spec.branch,
        ), write=0, reset=1, phase="SELECT")]
        steps.append(Step(self._observation(
            phase="ACQUIRE", event_type="target_absent_payload", source=identity,
            version=version, authenticated=True, selected=True, payload=spec.y,
            clock=0, branch=spec.branch,
        ), write=1, reset=0, phase="ACQUIRE"))
        for clock in range(spec.retention_length):
            decoy = spec.decoy_sequence[clock % 4]
            event_type = self.event_types[clock % 4]
            source = decoy[0]
            authenticated = decoy[3]
            selected = source == identity and authenticated and decoy[1] == version
            # Frozen decoys never authenticate as the selected identity/version.
            if selected:
                authenticated = False
            steps.append(Step(self._observation(
                phase="RETAIN", event_type=event_type, source=source,
                version=decoy[1], authenticated=authenticated, selected=False,
                payload=decoy[2] if event_type in {"target_absent_payload", "unauth_target_decoy"} else None,
                clock=clock + 1, branch=spec.branch,
            ), write=0, reset=0, phase="RETAIN"))
        terminal_target, write, reset, rejoin_payload = branch_terminal_contract(spec)
        if spec.branch == "RESET":
            version = (version + 1) % 4
        steps.append(Step(self._observation(
            phase="REJOIN", event_type="target_absent_payload", source=identity,
            version=version, authenticated=True, selected=True,
            payload=rejoin_payload, clock=spec.retention_length,
            branch=spec.branch,
        ), write=write, reset=reset, phase="REJOIN"))
        steps.append(Step(self._observation(
            phase="ACT", event_type="dummy_roster", source=identity,
            version=version, authenticated=True, selected=True, payload=None,
            clock=spec.retention_length, branch=spec.branch,
        ), write=0, reset=0, phase="ACT"))
        return ToyEpisode(
            steps=tuple(steps), terminal_target=terminal_target,
            historical_target=spec.y, selected_identity=identity,
            selected_version=version, branch=spec.branch,
        )


def build_policy(arm: str, initialization_seed: int) -> Any:
    """Build either arm with byte-identical shapes and initialization law."""

    torch = _torch()
    if arm not in ARMS:
        raise B2ContractError("unknown B2 arm")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(initialization_seed))

        class MatchedPolicy(torch.nn.Module):
            def __init__(self, arm_name: str) -> None:
                super().__init__()
                self.arm_name = arm_name
                self.encoder = torch.nn.Sequential(
                    torch.nn.Linear(OBSERVATION_DIM, CONTEXT_DIM), torch.nn.Tanh()
                )
                self.context_gru = torch.nn.GRUCell(CONTEXT_DIM, CONTEXT_DIM)
                self.carrier_gru = torch.nn.GRUCell(CONTEXT_DIM, CARRIER_DIM)
                # Shape-matched three-way keep/reset/write route.  The
                # candidate uses authenticated parameter-free controls; the
                # generic arm must infer all three choices from visible input.
                self.routing_gate = torch.nn.Linear(CONTEXT_DIM + CARRIER_DIM, 3)
                self.action_head = torch.nn.Linear(CONTEXT_DIM + CARRIER_DIM, 4)
                self.value_head = torch.nn.Linear(CONTEXT_DIM + CARRIER_DIM, 1)

            def initial_state(self, batch: int, *, device: Any = None) -> tuple[Any, Any]:
                parameter = next(self.parameters())
                target_device = parameter.device if device is None else device
                return (
                    torch.zeros(batch, CONTEXT_DIM, device=target_device),
                    torch.zeros(batch, CARRIER_DIM, device=target_device),
                )

            def step(self, observation: Any, state: tuple[Any, Any], write: Any, reset: Any) -> tuple[Any, Any, tuple[Any, Any], Any]:
                context, carrier = state
                encoded = self.encoder(observation)
                next_context = self.context_gru(encoded, context)
                learned_route = torch.softmax(
                    self.routing_gate(torch.cat((next_context, carrier), dim=-1)),
                    dim=-1,
                )
                if self.arm_name == CANDIDATE_ARM:
                    reset_carrier = carrier * (1.0 - reset)
                    proposed = self.carrier_gru(encoded, reset_carrier)
                    next_carrier = write * proposed + (1.0 - write) * reset_carrier
                else:
                    # No external write/reset oracle enters the generic state
                    # transition.  It learns keep, reset-to-zero, or write from
                    # the same visible provenance-bearing observation.
                    proposed = self.carrier_gru(encoded, carrier)
                    next_carrier = (
                        learned_route[:, 0:1] * carrier
                        + learned_route[:, 1:2] * torch.zeros_like(carrier)
                        + learned_route[:, 2:3] * proposed

                    )
                combined = torch.cat((next_context, next_carrier), dim=-1)
                return self.action_head(combined), self.value_head(combined).squeeze(-1), (next_context, next_carrier), learned_route

            def episode(self, observations: Any, writes: Any, resets: Any) -> tuple[Any, Any, Any]:
                state = self.initial_state(observations.shape[0], device=observations.device)
                gate_trace = []
                logits = values = None
                for step_index in range(observations.shape[1]):
                    logits, values, state, learned = self.step(
                        observations[:, step_index], state,
                        writes[:, step_index], resets[:, step_index],
                    )
                    gate_trace.append(learned)
                assert logits is not None and values is not None
                return logits, values, torch.stack(gate_trace, dim=1)

        return MatchedPolicy(arm)


def trainable_contract(model: Any) -> dict[str, Any]:
    torch = _torch()
    if not isinstance(model, torch.nn.Module):
        raise B2ContractError("policy is not a torch module")
    shapes = {name: list(parameter.shape) for name, parameter in model.named_parameters()}
    return {
        "parameter_shapes": shapes,
        "trainable_scalar_count": sum(int(parameter.numel()) for parameter in model.parameters() if parameter.requires_grad),
        "recurrent_state_elements": CONTEXT_DIM + CARRIER_DIM,
        "context_recurrence": CONTEXT_DIM,
        "carrier_recurrence": CARRIER_DIM,
        "action_head_actions": 4,
        "value_head_outputs": 1,
    }


def paired_models(seed_row: str) -> tuple[Any, Any]:
    if seed_row not in SEEDS:
        raise B2ContractError("unknown frozen seed row")
    seed = SEEDS[seed_row]["initialization"]
    candidate = build_policy(CANDIDATE_ARM, seed)
    generic = build_policy(GENERIC_ARM, seed)
    left = trainable_contract(candidate)
    right = trainable_contract(generic)
    if left != right:
        raise B2ContractError("arm shapes/counts/recurrent-state contract mismatch")
    torch = _torch()
    if any(not torch.equal(a, b) for a, b in zip(candidate.state_dict().values(), generic.state_dict().values())):
        raise B2ContractError("paired arm initialization bytes differ")
    return candidate, generic


def tensor_batch(
    specs: Sequence[EpisodeSpec], *, activity: dict[str, int] | None = None,
    lifecycle_activity: dict[str, int] | None = None,
    count_environment: bool = False,
) -> tuple[Any, Any, Any, Any, list[ToyEpisode]]:
    torch = _torch()
    episodes = []
    for spec in specs:
        episode = AuthenticatedPartnerRecallRelay().build(spec)
        episodes.append(episode)
        if count_environment:
            if activity is None or lifecycle_activity is None:
                raise B2ContractError("environment accounting target is absent")
            _increment_activity(activity, lifecycle_activity, "environment_episodes")
            _increment_activity(
                activity, lifecycle_activity, "environment_transitions",
                len(episode.steps),
            )
    lengths = {len(episode.steps) for episode in episodes}
    if len(lengths) != 1:
        raise B2ContractError("one PPO batch must have a common complete trajectory length")
    observations = torch.tensor([[step.observation for step in episode.steps] for episode in episodes], dtype=torch.float32)
    writes = torch.tensor([[step.write for step in episode.steps] for episode in episodes], dtype=torch.float32).unsqueeze(-1)
    resets = torch.tensor([[step.reset for step in episode.steps] for episode in episodes], dtype=torch.float32).unsqueeze(-1)
    targets = torch.tensor([episode.terminal_target for episode in episodes], dtype=torch.long)
    return observations, writes, resets, targets, episodes


def ppo_complete_batch(
    model: Any, optimizer: Any, specs: Sequence[EpisodeSpec], action_seed: int,
    *, activity: dict[str, int], lifecycle_activity: dict[str, int],
) -> dict[str, float]:
    """Four PPO epochs, recomputing each complete recurrent trajectory."""

    torch = _torch()
    if len(specs) != EPISODES_PER_BATCH:
        raise B2ContractError("PPO accepts only one complete 128-episode batch")
    observations, writes, resets, targets, episodes = tensor_batch(
        specs, activity=activity, lifecycle_activity=lifecycle_activity,
        count_environment=True,
    )
    transition_count = sum(len(episode.steps) for episode in episodes)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(action_seed))
    with torch.no_grad():
        old_logits, old_values, _ = model.episode(observations, writes, resets)
        _increment_activity(
            activity, lifecycle_activity, "production_policy_forwards",
            transition_count,
        )
        probabilities = torch.softmax(old_logits, dim=-1)
        actions = torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)
        _increment_activity(
            activity, lifecycle_activity, "action_rng_draws", len(specs)
        )
        rewards = torch.where(actions == targets, 1.0, -1.0)
        old_log_prob = torch.log_softmax(old_logits, dim=-1).gather(1, actions[:, None]).squeeze(1)
        advantages = rewards - old_values
        advantages = (advantages - advantages.mean()) / advantages.std(unbiased=False).clamp_min(1e-8)
        returns = rewards
    last = {}
    for _epoch in range(PPO_EPOCHS):
        logits, values, _ = model.episode(observations, writes, resets)
        distribution = torch.distributions.Categorical(logits=logits)
        log_prob = distribution.log_prob(actions)
        ratio = torch.exp(log_prob - old_log_prob)
        unclipped = ratio * advantages
        clipped = torch.clamp(ratio, 1.0 - PPO["clip"], 1.0 + PPO["clip"]) * advantages
        policy_loss = -torch.minimum(unclipped, clipped).mean()
        value_loss = (values - returns).pow(2).mean()
        entropy = distribution.entropy().mean()
        loss = policy_loss + PPO["value_coefficient"] * value_loss - PPO["entropy_coefficient"] * entropy
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), PPO["max_gradient_norm"])
        _optimizer_step_with_accounting(
            optimizer, activity, lifecycle_activity
        )
        last = {"loss": float(loss.detach()), "policy_loss": float(policy_loss.detach()), "value_loss": float(value_loss.detach()), "entropy": float(entropy.detach())}
    return last


def terminal_reward(action: int, target: int) -> int:
    if action not in ACTIONS or target not in ACTIONS:
        raise B2ContractError("terminal action/target outside legal mask")
    return 1 if action == target else -1


def normalized_keep_aulc(checkpoint_accuracy: Sequence[float]) -> float:
    if len(checkpoint_accuracy) != len(CHECKPOINTS) or any(not 0.0 <= value <= 1.0 for value in checkpoint_accuracy):
        raise B2ContractError("KEEP curve does not match fixed checkpoints")
    normalized = [(value - 0.25) / 0.75 for value in checkpoint_accuracy]
    area = sum(
        (CHECKPOINTS[i + 1] - CHECKPOINTS[i]) * (normalized[i] + normalized[i + 1]) / 2.0
        for i in range(len(CHECKPOINTS) - 1)
    )
    return area / 4096.0


def classify_result(evidence: Mapping[str, Any]) -> str:
    required_bool = {
        "contract_valid", "activity_nonzero", "caps_valid", "paired_exposure",
        "matched_shapes_counts_state", "terminal_ppo_only", "no_side_channel",
    }
    required_number = {
        "candidate_minus_generic_keep_aulc", "candidate_final_keep",
        "selected_p_mediation", "cross_swap_follow_rate",
        "candidate_decoy_accuracy_change", "candidate_decoy_kernel_tv_change",
        "current_arm_aulc_gap", "reset_stale_target_rate",
    }
    domains = {
        "candidate_minus_generic_keep_aulc": (-4.0 / 3.0, 4.0 / 3.0),
        "candidate_final_keep": (0.0, 1.0),
        "selected_p_mediation": (-1.0, 1.0),
        "cross_swap_follow_rate": (0.0, 1.0),
        "candidate_decoy_accuracy_change": (-1.0, 1.0),
        "candidate_decoy_kernel_tv_change": (0.0, 1.0),
        "current_arm_aulc_gap": (0.0, 4.0 / 3.0),
        "reset_stale_target_rate": (0.0, 1.0),
    }
    if (
        not isinstance(evidence, Mapping) or set(evidence) != required_bool | required_number
        or any(not isinstance(evidence[name], bool) or not evidence[name] for name in required_bool)
        or any(isinstance(evidence[name], bool) or not isinstance(evidence[name], (int, float)) or not math.isfinite(float(evidence[name])) for name in required_number)
    ):
        return INVALID
    if any(not low <= float(evidence[name]) <= high for name, (low, high) in domains.items()):
        return INVALID
    if evidence["candidate_final_keep"] < THRESHOLDS["candidate_final_keep_floor"]:
        return NAVIGATION_FAIL
    if evidence["selected_p_mediation"] < THRESHOLDS["selected_p_mediation"]:
        return MEDIATION_FAIL
    if evidence["cross_swap_follow_rate"] < THRESHOLDS["cross_swap_follow_rate"]:
        return CROSS_SWAP_FAIL
    if abs(evidence["candidate_decoy_accuracy_change"]) > THRESHOLDS["candidate_decoy_accuracy_change"] or abs(evidence["candidate_decoy_kernel_tv_change"]) > THRESHOLDS["candidate_decoy_kernel_tv_change"]:
        return DECOY_FAIL
    if abs(evidence["current_arm_aulc_gap"]) > THRESHOLDS["current_arm_aulc_gap"] or evidence["reset_stale_target_rate"] > THRESHOLDS["reset_stale_target_rate"]:
        return CURRENT_RESET_FAIL
    if evidence["candidate_minus_generic_keep_aulc"] < THRESHOLDS["navigation_band"]:
        return NO_EFFICIENCY
    return SUPPORTED


def validate_manifest(manifest: Mapping[str, Any], expected_digest: str) -> tuple[EpisodeSpec, ...]:
    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector

    if _digest(manifest) != expected_digest:
        raise B2ContractError("manifest content digest mismatch")
    if manifest.get("treatment") != TREATMENT_ID or manifest.get("selector_identity") != selector.SELECTOR_ID:
        raise B2ContractError("manifest identity mismatch")
    selected = manifest.get("selected_rows")
    if not isinstance(selected, list) or manifest.get("selected_count") != len(selected):
        raise B2ContractError("manifest selected rows/count mismatch")
    specs = tuple(EpisodeSpec.from_manifest_row(item["tuple"]) for item in selected)
    order = _digest([item["tuple_sha256"] for item in selected])
    if manifest.get("common_two_arm_order_digest") != order:
        raise B2ContractError("common two-arm manifest order mismatch")
    return specs


def _decoy_patterns() -> tuple[list[list[Any]], ...]:
    base = [[0, 0, 1, False], [1, 1, 2, True], [2, 2, 3, False], [3, 3, 0, True]]
    return tuple(base[index:] + base[:index] for index in range(4))


def _raw_row(
    *, consumer: str, seed_row: str, panel: str, branch: str,
    retention_length: int, y: int, logical_index: int, nonce: int,
) -> dict[str, Any]:
    feature = logical_index % 4

    identity = feature
    version = (logical_index // 4) % 4
    event_index = (logical_index // 16) % 4
    decoy_index = (logical_index // 64) % 4
    event_types = ("target_absent_payload", "unauth_target_decoy", "renewal_marker", "dummy_roster")
    quartet = f"{seed_row}_q{logical_index // 4:04d}" if consumer == "final_keep" else f"{consumer}_{seed_row}_{panel}_{branch}_{retention_length}_{logical_index:06d}"
    binding = _digest([consumer, seed_row, panel, branch, retention_length, y, logical_index])
    return {
        "consumer": consumer, "seed_row": seed_row, "panel": panel,
        "branch": branch, "retention_length": retention_length, "y": y,
        # A distinct balanced source axis: unlike the plausible-wrong version
        # alias, this Latin combination is pairwise balanced against identity,
        # version, event, and ordered-decoy provenance.
        "reset_y": (identity + version + event_index + decoy_index) % 4,
        "target_identity": identity, "target_version": version,
        "event_type": event_types[event_index], "decoy_sequence": _decoy_patterns()[decoy_index],
        "current_bytes": _digest(["current", quartet]),
        "roster": "P0,P1,P2,P3,focal", "legal_mask": "1111",
        "clock": f"L={retention_length}", "rng_binding": binding,
        "quartet_base": quartet, "nonce": nonce,
    }


def canonical_universe_spec(
    stage2_authorization: Mapping[str, Any], *, claim_continuation: object,
) -> dict[str, Any]:
    """Return the compact declarative recipe, never the emitted catalog rows."""

    validate_stage2_authorization(stage2_authorization)
    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector
    selector.validate_claim_continuation(stage2_authorization, claim_continuation)
    primary = ["primary_1", "primary_2", "primary_3", "primary_4"]
    return {
        "universe_id": UNIVERSE_SPEC_ID,
        "schema_version": 1,
        "salt": "8100799/",
        "tuple_fields": [
            "consumer", "seed_row", "panel", "branch", "retention_length", "y",
            "reset_y", "target_identity", "target_version", "event_type",
            "decoy_sequence", "current_bytes", "roster", "legal_mask", "clock",
            "rng_binding", "quartet_base", "nonce",
        ],
        "actions": [0, 1, 2, 3],
        "primary_seeds": primary,
        "checkpoints": list(CHECKPOINTS),
        "regular_pools": [
            {
                "consumer": "primary_fit", "seed_rows": primary, "panels": ["fit"],
                "branch_targets": {"KEEP": 384, "RESET": 64, "CURRENT": 64},
                "retention_lengths": [4, 8], "required_split": "train",
                "oversupply_multiplier": 4, "reset_multiplier": 4,
            },
            {
                "consumer": "calibration_fit", "seed_rows": ["calibration"],
                "panels": ["fit"], "branch_targets": {"CURRENT": 128},
                "retention_lengths": [4], "required_split": "calibration",
                "oversupply_multiplier": 32, "reset_multiplier": 4,
            },
            {
                "consumer": "calibration_check", "seed_rows": ["calibration"],
                "panels": ["check"], "branch_targets": {"CURRENT": 32},
                "retention_lengths": [4], "required_split": "calibration",
                "oversupply_multiplier": 32, "reset_multiplier": 4,
            },
            {
                "consumer": "checkpoint", "seed_rows": primary,
                "panels": [str(value) for value in CHECKPOINTS],
                "branch_targets": {"KEEP": 16, "RESET": 8, "CURRENT": 8},
                "retention_lengths": [6], "required_split": "evaluation",
                "oversupply_multiplier": 32, "reset_multiplier": 4,
            },
        ],
        "final_keep": {
            "consumer": "final_keep", "seed_rows": primary,
            "panel": "4096_keep_extra", "branch": "KEEP", "retention_length": 6,
            "quartets_per_seed": 64, "nonce_start": 0, "nonce_stop": 256,
            "required_split": "evaluation", "first_matching_nonce": True,
            "reset_y": 0,
        },
        "derivation": {
            "row_formula": "VSP06-B2R1-RAW-ROW-V1",
            "final_keep_formula": "VSP06-B2R1-FINAL-KEEP-FIRST-EVAL-V1",
            "bucket_formula": "sha256(utf8(salt)||canonical_tuple_bytes)[0]%8",
        },
    }


def canonical_catalog_rows(
    stage2_authorization: Mapping[str, Any], *, catalog_capability: object,
) -> Iterator[dict[str, Any]]:
    """Enumerate the frozen catalog; callers must never use it to tune CP-SAT."""

    validate_stage2_authorization(stage2_authorization)
    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector
    selector.consume_catalog_generation_capability(
        stage2_authorization, catalog_capability
    )
    return _canonical_catalog_rows_iter(
        stage2_authorization, catalog_capability=catalog_capability
    )


def _canonical_catalog_rows_iter(
    stage2_authorization: Mapping[str, Any], *, catalog_capability: object,
) -> Iterator[dict[str, Any]]:
    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector

    def emit_pool(consumer: str, seed: str, panel: str, branch: str, length: int, y: int, target: int, split: str) -> Iterator[dict[str, Any]]:
        # The fixed source pool is deliberately overcomplete.  Bucket filtering
        # is part of catalog eligibility, never a selector retry or objective.
        multiplier = 4 if split == "train" else 32
        if branch == "RESET":
            multiplier *= 4
        for logical in range(target * multiplier):
            row = _raw_row(consumer=consumer, seed_row=seed, panel=panel, branch=branch, retention_length=length, y=y, logical_index=logical, nonce=logical)
            if selector.split_for_bucket(selector.bucket_for_tuple(selector.canonical_tuple_bytes(row))) == split:
                yield row

    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for branch, per_length_y in (("KEEP", 384), ("RESET", 64), ("CURRENT", 64)):
            for length in (4, 8):
                for y in ACTIONS:
                    yield from emit_pool("primary_fit", seed, "fit", branch, length, y, per_length_y, "train")
    for consumer, panel, per_y in (("calibration_fit", "fit", 128), ("calibration_check", "check", 32)):
        for y in ACTIONS:
            yield from emit_pool(consumer, "calibration", panel, "CURRENT", 4, y, per_y, "calibration")
    for seed in ("primary_1", "primary_2", "primary_3", "primary_4"):
        for panel in map(str, CHECKPOINTS):
            for branch, per_y in (("KEEP", 16), ("RESET", 8), ("CURRENT", 8)):
                for y in ACTIONS:
                    yield from emit_pool("checkpoint", seed, panel, branch, 6, y, per_y, "evaluation")
        yield from canonical_final_keep_rows(
            seed, stage2_authorization, catalog_capability=catalog_capability
        )
    selector.finish_catalog_generation(catalog_capability)


def canonical_final_keep_rows(
    seed: str, stage2_authorization: Mapping[str, Any], *,
    catalog_capability: object,
) -> Iterator[dict[str, Any]]:
    validate_stage2_authorization(stage2_authorization)
    """Generate one seed's balanced source-level final-KEEP support."""

    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector
    selector.validate_catalog_generation_in_progress(
        stage2_authorization, catalog_capability
    )

    if seed not in {"primary_1", "primary_2", "primary_3", "primary_4"}:
        raise B2ContractError("final-KEEP support requires a primary seed")
    # Exactly 64 complete Y quartets are admitted.  Each row's nonce is the
    # first fixed-domain nonce mapping it to evaluation; no outcome exists.
    for quartet_index in range(64):
        identity = quartet_index % 4
        version = (quartet_index // 4) % 4
        event_index = (quartet_index // 16) % 4
        decoy_index = (identity + version + event_index) % 4
        for y in ACTIONS:
            logical = quartet_index
            for nonce in range(256):
                row = _raw_row(consumer="final_keep", seed_row=seed, panel="4096_keep_extra", branch="KEEP", retention_length=6, y=y, logical_index=logical, nonce=nonce)
                row["quartet_base"] = f"{seed}_q{quartet_index:04d}"
                row["target_identity"] = identity
                row["target_version"] = version
                row["event_type"] = AuthenticatedPartnerRecallRelay.event_types[event_index]
                row["decoy_sequence"] = _decoy_patterns()[decoy_index]
                row["current_bytes"] = _digest(["current", row["quartet_base"]])
                row["rng_binding"] = _digest(["quartet", row["quartet_base"]])
                row["reset_y"] = 0
                if selector.split_for_bucket(selector.bucket_for_tuple(selector.canonical_tuple_bytes(row))) == "evaluation":
                    yield row
                    break
            else:
                raise B2ContractError("fixed final-KEEP catalog domain lacks an evaluation row")


def readiness_contract() -> dict[str, Any]:
    """Zero-activity source/config readiness facts; this is not acceptance."""

    return {
        "treatment": TREATMENT_ID,
        "environment": ENVIRONMENT_ID,
        "resource_class": RESOURCE_CLASS,
        "arms": list(ARMS),
        "seeds": SEEDS,
        "ppo": PPO,
        "checkpoints": list(CHECKPOINTS),
        "thresholds": THRESHOLDS,
        "caps": CAPS,
        "activity_counts": {name: 0 for name in (
            "environment_episodes", "environment_transitions", "production_policy_forwards",
            "learner_updates", "optimizer_steps", "evaluator_calls", "evaluation_episodes",
            "model_fits", "trainer_invocations")},
        "canonical_selector_executed": False,
        "registered_full_executed": False,
        "result_claim": None,
    }


class ManifestGate:
    """Reload and reverify the immutable manifest before every consumer."""

    def __init__(
        self, path: Path, content_digest: str, *, session_root: Path,
        selector_receipt_path: Path, verifier_report_path: Path,
        stage2_authorization: Mapping[str, Any],
        selector_receipt_sha256: str,
    ) -> None:
        from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector

        validate_stage2_authorization(stage2_authorization)
        selector.verify_authorized_source_config(stage2_authorization)
        self.authorization = stage2_authorization
        canonical = selector.stage2_paths()
        if session_root != canonical["session_root"]:
            raise B2ContractError("full admission used an alternate Stage-2 root")
        self.session_root = canonical["session_root"]
        self.path = selector.authorize_read_path(stage2_authorization, path)
        self.content_digest = content_digest
        self.selector_receipt_path = selector.authorize_read_path(
            stage2_authorization, selector_receipt_path
        )
        self.verifier_report_path = selector.authorize_read_path(
            stage2_authorization, verifier_report_path
        )
        if (
            self.path != canonical["manifest"].resolve()
            or self.selector_receipt_path != canonical["receipt"].resolve()
            or self.verifier_report_path != canonical["verifier_report"].resolve()
        ):
            raise B2ContractError("full admission artifacts are outside the exact canonical session locator")
        if (
            not isinstance(selector_receipt_sha256, str)
            or len(selector_receipt_sha256) != 64
            or any(char not in "0123456789abcdef" for char in selector_receipt_sha256)
            or selector.sha256_authorized_file(
                stage2_authorization, self.selector_receipt_path
            ) != selector_receipt_sha256
        ):
            raise B2ContractError("external selector receipt digest anchor mismatch")
        if not self.path.exists() or self.path.stat().st_mode & stat.S_IWUSR:
            raise B2ContractError("verified manifest is absent or writable")
        self.file_digest = selector.sha256_authorized_file(stage2_authorization, self.path)
        self.order_digest = ""
        self.consumer_receipts: list[dict[str, str]] = []
        self.reload("preclaim")
        receipt = selector.authorized_json(stage2_authorization, self.selector_receipt_path)
        selector.validate_selector_receipt_schema(receipt)
        self.selector_activity_counts = selector.validate_activity_counts(
            receipt.get("activity_counts")
        )
        report = selector.authorized_json(stage2_authorization, self.verifier_report_path)
        bindings = selector.authorized_json(stage2_authorization, canonical["bindings"])
        witness = selector.authorized_json(stage2_authorization, canonical["witness"])
        manifest = selector.authorized_json(stage2_authorization, self.path)
        catalog_path = selector.authorize_read_path(stage2_authorization, canonical["catalog"])
        ledger_path = selector.authorize_read_path(stage2_authorization, canonical["ledger"])
        universe_path = selector.authorize_read_path(stage2_authorization, canonical["universe_spec"])
        expected = bindings.get("expected")
        authorization_digest = _digest(stage2_authorization)
        if (
            receipt.get("branch") != selector.VALID
            or receipt.get("final_commit") != stage2_authorization["final_commit"]
            or receipt.get("stage2_authorization_sha256") != authorization_digest
            or type(receipt.get("replica_count")) is not int
            or receipt.get("replica_count") != 2
            or receipt.get("replica_2_role") != "prospective_determinism_gate_not_retry"
            or not selector._exact_json_equal(
                receipt.get("activity_accounting"),
                {"sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0},
            )
            or receipt.get("manifest_path") != str(self.path)
            or receipt.get("verifier_report_path") != str(self.verifier_report_path)
            or receipt.get("bindings_path") != str(canonical["bindings"].resolve())
            or receipt.get("witness_path") != str(canonical["witness"].resolve())
            or receipt.get("manifest_file_sha256") != self.file_digest
            or receipt.get("manifest_content_sha256") != self.content_digest
            or receipt.get("verifier_report_sha256") != selector.sha256_authorized_file(stage2_authorization, self.verifier_report_path)
            or receipt.get("bindings_sha256") != selector.sha256_authorized_file(stage2_authorization, canonical["bindings"])
            or receipt.get("witness_sha256") != selector.sha256_authorized_file(stage2_authorization, canonical["witness"])
            or receipt.get("catalog_sha256") != selector.sha256_authorized_file(stage2_authorization, catalog_path)
            or receipt.get("universe_spec_sha256") != selector.sha256_authorized_file(stage2_authorization, universe_path)
            or receipt.get("ledger_sha256") != selector.sha256_authorized_file(stage2_authorization, ledger_path)
        ):
            raise B2ContractError("selector success receipt binding mismatch")
        if not isinstance(expected, Mapping) or bindings.get("synthetic_only") is not False:
            raise B2ContractError("synthetic or incomplete binding cannot admit a full")
        if (
            report.get("verdict") != "VERIFIED"
            or report.get("synthetic_only") is not False
            or report.get("final_commit") != stage2_authorization["final_commit"]
            or report.get("stage2_authorization_sha256") != authorization_digest
            or report.get("manifest_sha256") != self.content_digest
            or report.get("catalog_sha256") != expected.get("catalog_sha256")

            or report.get("ledger_sha256") != expected.get("ledger_sha256")
            or report.get("universe_spec_sha256") != expected.get("universe_spec_sha256")
            or report.get("source_config_digest_map_sha256") != expected.get("source_config_digest_map_sha256")
            or report.get("selector_source_sha256") != expected.get("selector_source_sha256")
            or report.get("solver_artifact_set_sha256") != expected.get("solver_artifact_set_sha256")
            or report.get("sat_parameters_sha256") != expected.get("sat_parameters_sha256")
            or report.get("python_executable_sha256") != expected.get("python_executable_sha256")
            or report.get("full_environment_receipt_sha256")
            != expected.get("full_environment_receipt_sha256")
            or report.get("verifier_source_sha256") != expected.get("verifier_source_sha256")
            or report.get("membership_witness_sha256") != selector.sha256_authorized_file(stage2_authorization, canonical["witness"])
            or report.get("membership_vector_sha256") != witness.get("membership_vector_sha256")
            or report.get("common_two_arm_order_digest") != self.order_digest
            or report.get("global_rank_claim") is not False
        ):
            raise B2ContractError("independent VERIFIED report binding mismatch")
        if manifest.get("bindings") != expected or manifest.get("rank_claim") is not False:
            raise B2ContractError("manifest source/build binding or rank nonclaim mismatch")
        if (
            expected.get("final_commit") != stage2_authorization["final_commit"]
            or expected.get("stage2_authorization_sha256") != authorization_digest
            or expected.get("source_config_digest_map") != stage2_authorization["source_config_digest_map"]
            or expected.get("source_config_digest_map_sha256") != stage2_authorization["source_config_digest_map_sha256"]
            or receipt.get("source_config_digest_map") != expected.get("source_config_digest_map")
            or receipt.get("source_config_digest_map_sha256") != expected.get("source_config_digest_map_sha256")
        ):
            raise B2ContractError("incoming authorization is not the manifest-sealed authorization")
        sealed_schema = expected.get("sealed_path_schema")
        sealed_objects = receipt.get("sealed_objects")
        if (
            not isinstance(sealed_schema, Mapping)
            or not isinstance(sealed_schema.get("stage2_authorization"), str)
            or sealed_schema != selector._sealed_path_schema(
                canonical,
                authorization_path=Path(sealed_schema["stage2_authorization"]),
                authorization=stage2_authorization,
            )
            or receipt.get("sealed_path_schema") != sealed_schema
            or receipt.get("sealed_path_schema_sha256") != _digest(sealed_schema)
            or not isinstance(sealed_objects, Mapping)
            or set(sealed_objects) != set(selector.SELECTOR_SEALED_OBJECT_NAMES)
            or receipt.get("receipt_path") != sealed_schema.get("receipt")
            or receipt.get("receipt_self_digest_is_external") is not True
            or receipt.get("full_environment_receipt_path")
            != stage2_authorization["full_environment_receipt_path"]
            or receipt.get("full_environment_receipt_sha256")
            != stage2_authorization["full_environment_receipt_sha256"]
        ):
            raise B2ContractError("complete sealed-object path schema mismatch")
        for name, item in sealed_objects.items():
            if not isinstance(item, Mapping) or set(item) != {"path", "sha256"}:
                raise B2ContractError("sealed-object envelope mismatch")
            if item["path"] != sealed_schema[name]:
                raise B2ContractError("sealed-object locator mismatch")
            sealed_path = selector.authorize_read_path(stage2_authorization, Path(item["path"]))
            if item["sha256"] != selector.sha256_authorized_file(stage2_authorization, sealed_path):
                raise B2ContractError("sealed-object digest mismatch")
        executable = selector.authorize_read_path(
            stage2_authorization, Path(str(expected.get("python_executable", "")))
        )
        if expected.get("python_executable_sha256") != selector.sha256_authorized_file(stage2_authorization, executable):
            raise B2ContractError("sealed interpreter executable mismatch")
        for artifact in expected.get("solver_artifacts", []):
            if not isinstance(artifact, list) or len(artifact) != 2:
                raise B2ContractError("sealed solver artifact envelope mismatch")
            artifact_path = selector.authorize_read_path(stage2_authorization, Path(artifact[0]))
            if artifact[1] != selector.sha256_authorized_file(stage2_authorization, artifact_path):
                raise B2ContractError("sealed solver artifact mismatch")
        selected = manifest.get("selected_rows")
        if not isinstance(selected, list):
            raise B2ContractError("manifest selected rows are absent")
        for item in selected:
            if not isinstance(item, Mapping) or set(item) != {"tuple", "tuple_sha256", "bucket", "split"}:
                raise B2ContractError("manifest selected-row envelope mismatch")
            tuple_bytes = selector.canonical_tuple_bytes(item["tuple"])
            tuple_sha = hashlib.sha256(tuple_bytes).hexdigest()
            bucket = selector.bucket_for_tuple(tuple_bytes)
            if (
                item["tuple_sha256"] != tuple_sha
                or item["bucket"] != bucket
                or item["split"] != selector.split_for_bucket(bucket)
            ):
                raise B2ContractError("manifest tuple hash/bucket/split mismatch")

    def reload(self, consumer: str) -> tuple[EpisodeSpec, ...]:
        from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector

        payload = selector.authorized_read_bytes(self.authorization, self.path)
        if hashlib.sha256(payload).hexdigest() != self.file_digest:
            raise B2ContractError("manifest file bytes changed after fixation")
        manifest = selector._strict_json_loads(payload.decode("utf-8"))
        specs = validate_manifest(manifest, self.content_digest)
        order = str(manifest["common_two_arm_order_digest"])
        if self.order_digest and order != self.order_digest:
            raise B2ContractError("manifest common two-arm order changed")
        self.order_digest = order
        self.consumer_receipts.append({
            "consumer": consumer,
            "manifest_file_sha256": self.file_digest,
            "manifest_content_sha256": self.content_digest,
            "common_two_arm_order_digest": order,
        })
        return specs


def _spec_digest(spec: EpisodeSpec) -> str:
    return _digest({
        **spec.__dict__,
        "decoy_sequence": [list(item) for item in spec.decoy_sequence],
    })


def _activity_template() -> dict[str, int]:
    return {
        "model_fits": 0, "trainer_invocations": 0,
        "environment_episodes": 0, "environment_transitions": 0,
        "production_policy_forwards": 0, "learner_updates": 0,
        "optimizer_steps": 0, "evaluator_calls": 0,
        "evaluation_episodes": 0, "environment_rng_draws": 0,
        "action_rng_draws": 0,
        "sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0,
    }


_SCIENTIFIC_TO_LIFECYCLE = {
    "model_fits": "model_fits", "trainer_invocations": "trainer_calls",
    "environment_episodes": "environment_episodes",
    "environment_transitions": "environment_transitions",
    "production_policy_forwards": "policy_forwards",
    "learner_updates": "learner_updates", "optimizer_steps": "optimizer_steps",
    "evaluator_calls": "evaluator_calls", "evaluation_episodes": "evaluation_episodes",
    "environment_rng_draws": "environment_rng_calls",
    "action_rng_draws": "action_rng_calls",
}


def _increment_activity(
    scientific: dict[str, int], lifecycle: dict[str, int],
    name: str, amount: int = 1,
) -> None:
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise B2ContractError("activity increment is invalid")
    scientific[name] += amount
    lifecycle_name = _SCIENTIFIC_TO_LIFECYCLE.get(name)
    if lifecycle_name is not None:
        lifecycle[lifecycle_name] += amount


def _optimizer_step_with_accounting(
    optimizer: Any, scientific: dict[str, int], lifecycle: dict[str, int],
) -> None:
    """Count only optimizer/learner steps that actually returned successfully."""

    optimizer.step()
    _increment_activity(scientific, lifecycle, "learner_updates")
    _increment_activity(scientific, lifecycle, "optimizer_steps")


def _training_batches(specs: Sequence[EpisodeSpec], seed: int) -> list[list[EpisodeSpec]]:
    by_length: dict[int, list[EpisodeSpec]] = {}
    for spec in specs:
        by_length.setdefault(spec.retention_length, []).append(spec)
    rng = random.Random(int(seed))
    chunks: dict[int, list[list[EpisodeSpec]]] = {}
    for length, rows in sorted(by_length.items()):
        rng.shuffle(rows)
        if len(rows) % EPISODES_PER_BATCH:
            raise B2ContractError("fit rows do not form complete trajectory batches")
        chunks[length] = [rows[index:index + EPISODES_PER_BATCH] for index in range(0, len(rows), EPISODES_PER_BATCH)]
    batches: list[list[EpisodeSpec]] = []
    while any(chunks.values()):
        for length in sorted(chunks):
            if chunks[length]:
                batches.append(chunks[length].pop(0))
    return batches


def _new_optimizer(model: Any) -> Any:
    torch = _torch()
    return torch.optim.Adam(
        model.parameters(), lr=PPO["lr"], eps=PPO["epsilon"],
        weight_decay=PPO["weight_decay"],
    )


def _fit(
    *, model: Any, specs: Sequence[EpisodeSpec], seed_row: str, arm: str,
    gate: ManifestGate, activity: dict[str, int], lifecycle_activity: dict[str, int],
    stop_after_batches: int | None = None,
) -> tuple[list[dict[str, float]], list[list[EpisodeSpec]]]:
    gate.reload(f"fit/{seed_row}/{arm}")
    batches = _training_batches(specs, SEEDS[seed_row]["minibatch"])
    if stop_after_batches is not None:
        batches = batches[:stop_after_batches]
    _increment_activity(activity, lifecycle_activity, "model_fits")
    _increment_activity(activity, lifecycle_activity, "trainer_invocations")
    optimizer = _new_optimizer(model)
    losses = []
    for batch_index, batch in enumerate(batches):
        losses.append(ppo_complete_batch(
            model, optimizer, batch,
            SEEDS[seed_row]["environment"] + batch_index,
            activity=activity, lifecycle_activity=lifecycle_activity,
        ))
    return losses, batches


def _continue_fit(
    *, model: Any, optimizer: Any, batches: Sequence[Sequence[EpisodeSpec]],
    seed_row: str, start_index: int, activity: dict[str, int],
    lifecycle_activity: dict[str, int],
) -> list[dict[str, float]]:
    losses = []
    for offset, batch in enumerate(batches):
        index = start_index + offset
        losses.append(ppo_complete_batch(
            model, optimizer, batch, SEEDS[seed_row]["environment"] + index,
            activity=activity, lifecycle_activity=lifecycle_activity,
        ))
    return losses


def _write_checkpoint(
    path: Path, model: Any, metadata: Mapping[str, Any],
    stage2_authorization: Mapping[str, Any],
) -> str:
    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector

    torch = _torch()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        stream = path.open("xb")
    except FileExistsError as exc:
        raise B2ContractError("checkpoint destination already exists") from exc
    with stream:
        torch.save({"state_dict": model.state_dict(), "metadata": dict(metadata)}, stream)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(
        selector.authorized_read_bytes(stage2_authorization, path)
    ).hexdigest()


def _reload_checkpoint(
    path: Path, expected_digest: str, model: Any,
    stage2_authorization: Mapping[str, Any],
) -> None:
    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector

    torch = _torch()
    payload = selector.authorized_read_bytes(stage2_authorization, path)
    if hashlib.sha256(payload).hexdigest() != expected_digest:
        raise B2ContractError("checkpoint digest changed")
    checkpoint = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["state_dict"])


def _policy_panel(
    model: Any, specs: Sequence[EpisodeSpec], action_seed: int,
    *, observations: Any | None = None, writes: Any | None = None,
    resets: Any | None = None, targets: Any | None = None,
    activity: dict[str, int], lifecycle_activity: dict[str, int],
    count_environment: bool = False,
) -> dict[str, Any]:
    torch = _torch()
    base_observations, base_writes, base_resets, base_targets, episodes = tensor_batch(
        specs, activity=activity, lifecycle_activity=lifecycle_activity,
        count_environment=count_environment,
    )
    observations = base_observations if observations is None else observations
    writes = base_writes if writes is None else writes
    resets = base_resets if resets is None else resets
    targets = base_targets if targets is None else targets
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(action_seed))
    with torch.no_grad():
        logits, values, gates = model.episode(observations, writes, resets)
        transition_count = sum(len(episode.steps) for episode in episodes)
        _increment_activity(
            activity, lifecycle_activity, "production_policy_forwards",
            transition_count,
        )
        probabilities = torch.softmax(logits, dim=-1)
        actions = torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)
        _increment_activity(
            activity, lifecycle_activity, "action_rng_draws", len(specs)
        )
    correct = actions == targets
    by_branch = {}
    for branch in BRANCHES:
        mask = torch.tensor([spec.branch == branch for spec in specs], dtype=torch.bool)
        if bool(mask.any()):
            by_branch[branch] = float(correct[mask].float().mean())
    return {
        "accuracy": float(correct.float().mean()),
        "by_branch": by_branch,
        "actions": actions,
        "probabilities": probabilities,
        "values": values,
        "gates": gates,
        "targets": targets,
        "historical_targets": torch.tensor([episode.historical_target for episode in episodes], dtype=torch.long),
        "transition_count": transition_count,
        "action_seed": int(action_seed),
    }


def _evaluate(
    *, model: Any, specs: Sequence[EpisodeSpec], seed_row: str, arm: str,
    panel: str, gate: ManifestGate, activity: dict[str, int],
    lifecycle_activity: dict[str, int], count_episode: bool = True,
    action_seed: int | None = None,
) -> dict[str, Any]:
    gate.reload(f"evaluation/{seed_row}/{arm}/{panel}")
    if action_seed is None:
        action_seed = SEEDS[seed_row]["evaluation"] + int(hashlib.sha256(panel.encode()).hexdigest()[:8], 16)
    if count_episode:
        _increment_activity(activity, lifecycle_activity, "evaluator_calls")
        _increment_activity(
            activity, lifecycle_activity, "evaluation_episodes", len(specs)
        )
    result = _policy_panel(
        model, specs, action_seed, activity=activity,
        lifecycle_activity=lifecycle_activity,
        count_environment=count_episode,
    )
    return result


def _cross_swap_indices(
    specs: Sequence[EpisodeSpec], *, expected_quartets: int,
) -> tuple[int, ...]:
    groups: dict[str, list[int]] = {}
    for index, spec in enumerate(specs):
        if spec.branch != "KEEP":
            raise B2ContractError("cross-swap input contains a non-KEEP row")
        groups.setdefault(spec.quartet_base, []).append(index)
    if len(groups) != expected_quartets or len(specs) != expected_quartets * 4:
        raise B2ContractError("cross-swap quartet cardinality mismatch")
    source_for_destination = [-1] * len(specs)
    structural_fields = tuple(
        field for field in EpisodeSpec.__dataclass_fields__ if field not in {"y", "nonce"}
    )
    for base, indices in groups.items():
        by_y = {specs[index].y: index for index in indices}
        if len(indices) != 4 or set(by_y) != set(ACTIONS):
            raise B2ContractError(f"cross-swap quartet is incomplete: {base}")
        reference = tuple(getattr(specs[indices[0]], field) for field in structural_fields)
        if any(tuple(getattr(specs[index], field) for field in structural_fields) != reference for index in indices[1:]):
            raise B2ContractError(f"cross-swap quartet pairing mismatch: {base}")
        for y, destination in by_y.items():
            source = by_y[(y + 1) % 4]
            if source == destination or specs[source].y == specs[destination].y:
                raise B2ContractError("cross-swap permutation has a fixed point")
            source_for_destination[destination] = source
    if -1 in source_for_destination or len(set(source_for_destination)) != len(specs):
        raise B2ContractError("cross-swap is not a complete permutation")
    return tuple(source_for_destination)


def selected_p_cross_swap_plan(
    specs: Sequence[EpisodeSpec], *, expected_quartets: int,
) -> tuple[dict[str, int | str], ...]:
    """Pure destination-fixed plan; only the selected-P payload is sourced."""

    indices = _cross_swap_indices(specs, expected_quartets=expected_quartets)
    return tuple({
        "destination_index": destination,
        "source_index": source,
        "quartet_base": specs[destination].quartet_base,
        "destination_payload": specs[destination].y,
        "swapped_payload": specs[source].y,
    } for destination, source in enumerate(indices))


def validate_payload_only_cross_swap(
    destination_specs: Sequence[EpisodeSpec], projected_specs: Sequence[EpisodeSpec],
    swapped_payloads: Sequence[int], *, expected_quartets: int,
) -> None:
    """Reject an intact observation/control/target co-permutation."""

    plan = selected_p_cross_swap_plan(
        destination_specs, expected_quartets=expected_quartets
    )
    if tuple(projected_specs) != tuple(destination_specs):
        raise B2ContractError("cross-swap destination controls were co-permuted")
    expected = tuple(int(item["swapped_payload"]) for item in plan)
    if tuple(swapped_payloads) != expected:
        raise B2ContractError("cross-swap changed more or less than selected-P payload")


def paired_control_action_seeds(seed_row: str) -> dict[str, int]:
    if seed_row not in SEEDS or seed_row == "calibration":
        raise B2ContractError("paired control action seed requires a primary seed")
    seed = SEEDS[seed_row]["evaluation"] + 101
    return {
        "baseline": seed, "selected_p_zero": seed,
        "cross_swap": seed, "decoy_accuracy_delta": seed,
    }


def _control_partitions(
    final_panel: Sequence[EpisodeSpec], *, expected_current: int,
    expected_reset: int, expected_changed_reset: int, expected_joint: int,
) -> tuple[tuple[EpisodeSpec, ...], tuple[EpisodeSpec, ...]]:
    current = tuple(spec for spec in final_panel if spec.branch == "CURRENT")
    reset = tuple(spec for spec in final_panel if spec.branch == "RESET")
    changed_reset = tuple(spec for spec in reset if spec.reset_y != spec.y)
    if (
        len(current) != expected_current or len(reset) != expected_reset
        or len(changed_reset) != expected_changed_reset or not changed_reset
    ):
        raise B2ContractError("CURRENT/RESET control cardinality mismatch")
    if any(spec.consumer != "checkpoint" or spec.panel != "4096" for spec in current + reset):
        raise B2ContractError("CURRENT/RESET controls are not paired to the final checkpoint panel")
    if {y: sum(spec.y == y for spec in current) for y in ACTIONS} != {
        y: expected_current // 4 for y in ACTIONS
    }:
        raise B2ContractError("CURRENT control Y pairing mismatch")
    if any(
        sum(spec.y == y and spec.reset_y == reset_y for spec in reset) != expected_joint
        for y in ACTIONS for reset_y in ACTIONS
    ):
        raise B2ContractError("RESET control Y/reset_y pairing mismatch")
    return current, changed_reset


def _controls(
    *, model: Any, final_keep: Sequence[EpisodeSpec], final_panel: Sequence[EpisodeSpec],
    seed_row: str, gate: ManifestGate, activity: dict[str, int],
    lifecycle_activity: dict[str, int], baseline: Mapping[str, Any],
) -> dict[str, float]:
    torch = _torch()
    observations, writes, resets, targets, _episodes = tensor_batch(final_keep)
    paired_seeds = paired_control_action_seeds(seed_row)
    if baseline.get("action_seed") != paired_seeds["baseline"]:
        raise B2ContractError("baseline/control action randomness is not explicitly paired")
    zero_writes = torch.zeros_like(writes)
    gate.reload(f"controls/{seed_row}/{CANDIDATE_ARM}/selected_p_zero")
    selected_zero = _policy_panel(
        model, final_keep, paired_seeds["selected_p_zero"],
        observations=observations, writes=zero_writes, resets=resets, targets=targets,
        activity=activity, lifecycle_activity=lifecycle_activity,
    )
    current_specs, reset_specs = _control_partitions(
        final_panel, expected_current=32, expected_reset=32,
        expected_changed_reset=24, expected_joint=2,
    )
    gate.reload(f"controls/{seed_row}/{CANDIDATE_ARM}/current_only_rebuild")
    current_observations, current_writes, current_resets, current_targets, _current_episodes = tensor_batch(current_specs)
    rebuild_writes = torch.zeros_like(current_writes)
    rebuild_writes[:, -2] = 1.0
    current_rebuild = _policy_panel(
        model, current_specs, SEEDS[seed_row]["evaluation"] + 102,
        observations=current_observations, writes=rebuild_writes,
        resets=current_resets, targets=current_targets,
        activity=activity, lifecycle_activity=lifecycle_activity,
    )
    gate.reload(f"controls/{seed_row}/{CANDIDATE_ARM}/cross_swap")
    cross_indices = list(_cross_swap_indices(final_keep, expected_quartets=64))
    validate_payload_only_cross_swap(
        final_keep, final_keep, [final_keep[index].y for index in cross_indices],
        expected_quartets=64,
    )
    cross_observations = observations.clone()
    cross_observations[:, 1, 16:20] = observations[cross_indices, 1, 16:20]
    cross_writes = writes
    cross_resets = resets
    cross_targets = targets[cross_indices]
    cross = _policy_panel(
        model, final_keep, paired_seeds["cross_swap"],
        observations=cross_observations, writes=cross_writes, resets=cross_resets,
        targets=cross_targets,
        activity=activity, lifecycle_activity=lifecycle_activity,
    )
    gate.reload(f"controls/{seed_row}/{CANDIDATE_ARM}/decoy_replay")
    decoy_observations = observations.clone()
    if decoy_observations.shape[1] > 4:
        decoy_observations[:, 2:-2, 16:20] = decoy_observations[:, 2:-2, 16:20].roll(1, dims=-1)
    decoy = _policy_panel(
        model, final_keep, paired_seeds["decoy_accuracy_delta"],
        observations=decoy_observations, writes=writes, resets=resets, targets=targets,
        activity=activity, lifecycle_activity=lifecycle_activity,
    )
    baseline_probabilities = baseline["probabilities"]
    tv = 0.5 * torch.abs(baseline_probabilities - decoy["probabilities"]).sum(dim=-1).mean()
    gate.reload(f"controls/{seed_row}/{CANDIDATE_ARM}/reset_stale_target")
    reset_panel = _policy_panel(
        model, reset_specs, SEEDS[seed_row]["evaluation"] + 105,
        activity=activity, lifecycle_activity=lifecycle_activity,
    )
    stale = (reset_panel["actions"] == reset_panel["historical_targets"]).float().mean()
    return {
        "selected_p_mediation": float(baseline["accuracy"] - selected_zero["accuracy"]),
        "current_only_rebuild_accuracy": float(current_rebuild["accuracy"]),
        "cross_swap_follow_rate": float(cross["accuracy"]),
        "decoy_accuracy_change": float(decoy["accuracy"] - baseline["accuracy"]),
        "decoy_kernel_tv_change": float(tv),
        "reset_stale_target_rate": float(stale),
    }


def _public_panel(panel: Mapping[str, Any]) -> dict[str, Any]:
    return {"accuracy": panel["accuracy"], "by_branch": dict(panel["by_branch"])}


def _caps_valid(activity: Mapping[str, int]) -> bool:
    return (
        set(activity) == set(EXPECTED_FULL_ACTIVITY)
        and set(CAPS).issubset(activity)
        and all(
            isinstance(activity[name], int) and not isinstance(activity[name], bool)
            and activity[name] <= cap
            for name, cap in CAPS.items()
        )
    )


def run_registered_full(
    *, manifest_path: Path, manifest_content_digest: str,
    session_root: Path, selector_receipt_path: Path,
    verifier_report_path: Path, run_root: Path, result_path: Path,
    stage2_authorization: Mapping[str, Any],
    selector_receipt_sha256: str,
    selector_activity_counts: Mapping[str, Any],
) -> dict[str, Any]:
    """Execute the unique manifest-gated full; never called by readiness/tests."""

    global _STAGE2_RUNTIME_AUTHORIZED
    validate_stage2_authorization(stage2_authorization)
    from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector
    selector_start_activity = selector.validate_activity_counts(selector_activity_counts)
    lifecycle_activity = dict(selector_start_activity)
    _environment_path, environment_receipt = selector.load_full_environment_receipt(
        stage2_authorization
    )
    selector.validate_selector_environment_receipt(
        stage2_authorization, environment_receipt
    )
    bind_full_environment(stage2_authorization, environment_receipt)
    expected_run_root = selector.STAGE2_SESSION_ROOT / "registered_full"
    expected_result = selector.PROJECT_ROOT / "docs/research/candidates/vsp_06_mssr/VSP06_B2R1_AUTHENTICATED_PARTNER_RECALL_CREDIT_EFFICIENCY_RESULT.json"
    if run_root != expected_run_root or result_path != expected_result:
        raise B2ContractError("registered full used an alternate root or result destination")
    try:
        selector.validate_absent_destination(run_root)
        selector.validate_absent_destination(result_path)
    except selector.SelectorInvalid as exc:
        raise B2ContractError("registered full destination is not safely absent") from exc
    os.mkdir(run_root)
    claim_path = run_root / "registered_full_claim.json"
    claim = selector.exact_claim(stage2_authorization, phase="registered_full")
    selector.write_exclusive(claim_path, _json_bytes(claim) + b"\n")
    reloaded_claim = selector.authorized_json(stage2_authorization, claim_path)
    selector.validate_exact_claim(
        reloaded_claim, stage2_authorization, phase="registered_full"
    )
    activity = _activity_template()
    checkpoint_receipts: list[dict[str, Any]] = []
    _STAGE2_RUNTIME_AUTHORIZED = True
    try:
        selector.persist_activity_snapshot(
            stage2_authorization, selector.stage2_paths(), "full_claim",
            lifecycle_activity,
        )
        manifest_path = selector.authorize_read_path(stage2_authorization, manifest_path)
        selector_receipt_path = selector.authorize_read_path(stage2_authorization, selector_receipt_path)
        verifier_report_path = selector.authorize_read_path(stage2_authorization, verifier_report_path)
        gate = ManifestGate(
            manifest_path, manifest_content_digest, session_root=session_root,
            selector_receipt_path=selector_receipt_path,
            verifier_report_path=verifier_report_path,
            stage2_authorization=stage2_authorization,
            selector_receipt_sha256=selector_receipt_sha256,
        )
        if gate.selector_activity_counts != lifecycle_activity:
            raise B2ContractError("full lifecycle was not seeded from durable selector activity")
        specs = gate.reload("postclaim_complete_manifest")
        by_consumer: dict[str, list[EpisodeSpec]] = {}
        for spec in specs:
            by_consumer.setdefault(spec.consumer, []).append(spec)
        expected = {"primary_fit": 16384, "calibration_fit": 512, "calibration_check": 128, "checkpoint": 4096, "final_keep": 1024}
        if {name: len(rows) for name, rows in by_consumer.items()} != expected:
            raise B2ContractError("manifest consumer counts changed")

        calibration_models = dict(zip(ARMS, paired_models("calibration")))
        calibration = {}
        for arm in ARMS:
            losses, batches = _fit(
                model=calibration_models[arm], specs=by_consumer["calibration_fit"],
                seed_row="calibration", arm=arm, gate=gate, activity=activity,
                lifecycle_activity=lifecycle_activity,
            )
            if len(batches) != 4:
                raise B2ContractError("calibration fit must contain four complete batches")
            panel = _evaluate(
                model=calibration_models[arm], specs=by_consumer["calibration_check"],
                seed_row="calibration", arm=arm, panel="calibration_check",
                gate=gate, activity=activity,
                lifecycle_activity=lifecycle_activity,
            )
            calibration[arm] = {"losses": losses, "check": _public_panel(panel)}
        if abs(calibration[CANDIDATE_ARM]["check"]["accuracy"] - calibration[GENERIC_ARM]["check"]["accuracy"]) > THRESHOLDS["current_arm_aulc_gap"]:
            raise B2ContractError("calibration CURRENT matched-arm gate failed")
        selector.persist_activity_snapshot(
            stage2_authorization, selector.stage2_paths(), "full_calibration",
            lifecycle_activity,
        )

        seed_results: dict[str, Any] = {}
        candidate_aulcs = []
        generic_aulcs = []
        final_keep_values = []
        control_rows = []
        current_gaps = []
        for seed_row in ("primary_1", "primary_2", "primary_3", "primary_4"):
            models = dict(zip(ARMS, paired_models(seed_row)))
            optimizers = {arm: _new_optimizer(models[arm]) for arm in ARMS}
            fit_specs = [spec for spec in by_consumer["primary_fit"] if spec.seed_row == seed_row]
            batches = _training_batches(fit_specs, SEEDS[seed_row]["minibatch"])
            if len(batches) != 32:
                raise B2ContractError("primary fit must contain 32 complete batches")
            for arm in ARMS:
                gate.reload(f"fit/{seed_row}/{arm}")
                _increment_activity(activity, lifecycle_activity, "model_fits")
                _increment_activity(activity, lifecycle_activity, "trainer_invocations")
            panels_by_arm = {arm: [] for arm in ARMS}
            losses_by_arm = {arm: [] for arm in ARMS}
            checkpoint_specs_all = [spec for spec in by_consumer["checkpoint"] if spec.seed_row == seed_row]
            for checkpoint_index, checkpoint in enumerate(CHECKPOINTS):
                if checkpoint_index:
                    start = (checkpoint_index - 1) * 4
                    interval = batches[start:start + 4]
                    for arm in ARMS:
                        losses_by_arm[arm].extend(_continue_fit(
                            model=models[arm], optimizer=optimizers[arm], batches=interval,
                            seed_row=seed_row, start_index=start, activity=activity,
                            lifecycle_activity=lifecycle_activity,
                        ))
                panel_specs = [spec for spec in checkpoint_specs_all if spec.panel == str(checkpoint)]
                if len(panel_specs) != 128:
                    raise B2ContractError("fixed checkpoint panel count changed")
                for arm in ARMS:
                    gate.reload(f"checkpoint/{seed_row}/{arm}/{checkpoint}")
                    checkpoint_path = run_root / "checkpoints" / seed_row / arm / f"episodes_{checkpoint}.pt"
                    checkpoint_digest = _write_checkpoint(checkpoint_path, models[arm], {
                        "seed_row": seed_row, "arm": arm, "episodes": checkpoint,
                        "manifest_content_sha256": gate.content_digest,
                        "common_two_arm_order_digest": gate.order_digest,
                        "trainable_contract": trainable_contract(models[arm]),
                    }, stage2_authorization)
                    _reload_checkpoint(
                        checkpoint_path, checkpoint_digest, models[arm],
                        stage2_authorization,
                    )
                    checkpoint_receipts.append({
                        "path": str(checkpoint_path), "sha256": checkpoint_digest,
                        "seed_row": seed_row, "arm": arm, "episodes": checkpoint,
                    })
                    panel = _evaluate(
                        model=models[arm], specs=panel_specs, seed_row=seed_row,
                        arm=arm, panel=str(checkpoint), gate=gate, activity=activity,
                        lifecycle_activity=lifecycle_activity,
                    )
                    panels_by_arm[arm].append(_public_panel(panel))
            final_specs = [spec for spec in by_consumer["final_keep"] if spec.seed_row == seed_row]
            final_panels = {}
            raw_final = {}
            control_seeds = paired_control_action_seeds(seed_row)
            for arm in ARMS:
                raw_final[arm] = _evaluate(
                    model=models[arm], specs=final_specs, seed_row=seed_row,
                    arm=arm, panel="4096_keep_extra", gate=gate, activity=activity,
                    lifecycle_activity=lifecycle_activity,
                    action_seed=control_seeds["baseline"],
                )
                final_panels[arm] = _public_panel(raw_final[arm])
            controls = _controls(
                model=models[CANDIDATE_ARM], final_keep=final_specs,
                final_panel=[spec for spec in checkpoint_specs_all if spec.panel == "4096"],
                seed_row=seed_row, gate=gate, activity=activity,
                lifecycle_activity=lifecycle_activity,
                baseline=raw_final[CANDIDATE_ARM],
            )
            candidate_curve = [panel["by_branch"]["KEEP"] for panel in panels_by_arm[CANDIDATE_ARM]]
            generic_curve = [panel["by_branch"]["KEEP"] for panel in panels_by_arm[GENERIC_ARM]]
            candidate_current = [panel["by_branch"]["CURRENT"] for panel in panels_by_arm[CANDIDATE_ARM]]
            generic_current = [panel["by_branch"]["CURRENT"] for panel in panels_by_arm[GENERIC_ARM]]
            candidate_aulc = normalized_keep_aulc(candidate_curve)
            generic_aulc = normalized_keep_aulc(generic_curve)
            candidate_aulcs.append(candidate_aulc)
            generic_aulcs.append(generic_aulc)
            final_keep_values.append(final_panels[CANDIDATE_ARM]["accuracy"])
            control_rows.append(controls)
            current_gaps.append(abs(normalized_keep_aulc(candidate_current) - normalized_keep_aulc(generic_current)))
            seed_results[seed_row] = {
                "panels": panels_by_arm, "final_keep": final_panels,
                "controls": controls, "keep_aulc": {
                    CANDIDATE_ARM: candidate_aulc, GENERIC_ARM: generic_aulc,
                    "candidate_minus_generic": candidate_aulc - generic_aulc,
                }, "losses": losses_by_arm,
            }
            selector.persist_activity_snapshot(
                stage2_authorization, selector.stage2_paths(),
                f"full_{seed_row}", lifecycle_activity,
            )

        exact_activity = activity == EXPECTED_FULL_ACTIVITY
        expected_lifecycle = dict(selector_start_activity)
        for scientific_name, lifecycle_name in _SCIENTIFIC_TO_LIFECYCLE.items():
            expected_lifecycle[lifecycle_name] += activity[scientific_name]
        lifecycle_valid = lifecycle_activity == expected_lifecycle
        caps_valid = _caps_valid(activity)
        evidence = {
            "contract_valid": exact_activity and lifecycle_valid, "activity_nonzero": all(activity[name] > 0 for name in (
                "environment_episodes", "production_policy_forwards", "learner_updates",
                "trainer_invocations", "optimizer_steps", "evaluator_calls")),
            "caps_valid": caps_valid, "paired_exposure": True,
            "matched_shapes_counts_state": True, "terminal_ppo_only": True,
            "no_side_channel": True,
            "candidate_minus_generic_keep_aulc": sum(c - g for c, g in zip(candidate_aulcs, generic_aulcs)) / 4.0,
            "candidate_final_keep": sum(final_keep_values) / 4.0,
            "selected_p_mediation": sum(row["selected_p_mediation"] for row in control_rows) / 4.0,
            "cross_swap_follow_rate": sum(row["cross_swap_follow_rate"] for row in control_rows) / 4.0,
            "candidate_decoy_accuracy_change": sum(row["decoy_accuracy_change"] for row in control_rows) / 4.0,
            "candidate_decoy_kernel_tv_change": sum(row["decoy_kernel_tv_change"] for row in control_rows) / 4.0,
            "current_arm_aulc_gap": max(current_gaps),
            "reset_stale_target_rate": sum(row["reset_stale_target_rate"] for row in control_rows) / 4.0,
        }
        branch = classify_result(evidence)
        result = {
            "treatment": TREATMENT_ID, "environment": ENVIRONMENT_ID,
            "branch": branch, "evidence": evidence, "calibration": calibration,
            "paired_seed_results": seed_results,
            "activity_counts": dict(lifecycle_activity),
            "scientific_activity_counts": activity,
            "caps": CAPS, "checkpoints": checkpoint_receipts,
            "manifest": {
                "path": str(gate.path), "file_sha256": gate.file_digest,
                "content_sha256": gate.content_digest,
                "common_two_arm_order_digest": gate.order_digest,
                "consumer_reload_receipts": gate.consumer_receipts,
            },
            "lifecycle": {
                "claim_path": str(claim_path), "full_ordinal": 1,
                "sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0,
                "result_write_once": True,
            },
            "limitations": "One manifest-conditioned four-seed toy full; no global-rank, deployment, promotion, retirement, sibling-direction, or generality claim.",

        }
        result_path.parent.mkdir(parents=True, exist_ok=True)
        selector.persist_activity_snapshot(
            stage2_authorization, selector.stage2_paths(), "full_complete",
            lifecycle_activity,
        )
        persisted_result = selector.write_json_exclusive_verified(
            stage2_authorization, result_path, result
        )
        result_path.chmod(0o444)
        _STAGE2_RUNTIME_AUTHORIZED = False
        return dict(persisted_result)
    except Exception as exc:
        _STAGE2_RUNTIME_AUTHORIZED = False
        failure = {
            "branch": "B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY",
            "error_type": type(exc).__name__, "error": str(exc),
            "traceback": traceback.format_exc(),
            "activity_counts": dict(lifecycle_activity),
            "scientific_activity_counts": activity,
            "retry_authorized": False, "rescue_authorized": False,
            "sweeps": 0, "retries": 0, "rescues": 0, "extra_roots": 0,
        }
        failure_path = run_root / "registered_full_failure.json"
        if not selector.path_lexists(failure_path):
            selector.write_json_exclusive_verified(
                stage2_authorization, failure_path, failure
            )
        persisted = selector.authorized_json(stage2_authorization, failure_path)
        if not selector._exact_json_equal(dict(persisted), failure):
            raise B2ContractError("registered-full terminal receipt reload mismatch")
        return dict(persisted)


__all__ = [
    "EpisodeSpec", "Step", "ToyEpisode", "AuthenticatedPartnerRecallRelay",
    "build_policy", "paired_models", "trainable_contract", "tensor_batch",
    "ppo_complete_batch", "terminal_reward", "normalized_keep_aulc",
    "classify_result", "validate_manifest", "canonical_catalog_rows",
    "canonical_final_keep_rows", "canonical_universe_spec",
    "branch_terminal_contract", "selected_p_cross_swap_plan",
    "validate_payload_only_cross_swap", "paired_control_action_seeds",
    "readiness_contract", "B2ContractError", "TREATMENT_ID", "ENVIRONMENT_ID",
    "ManifestGate", "run_registered_full",
    "CANDIDATE_ARM", "GENERIC_ARM", "SEEDS", "PPO", "CAPS", "THRESHOLDS",
    "EXPECTED_FULL_ACTIVITY",
]
