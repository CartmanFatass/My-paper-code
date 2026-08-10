"""Frozen two-phase FOLR-B3 partner-writer/stale-load treatment.

This module intentionally owns the complete train -> evaluate -> analyze
artifact lifecycle.  Phase P calibrates one ordinary reward-trained partner
writer.  Phase R starts only after the frozen calibration gates pass and uses
byte-identical frozen writer clones in three architecture-matched arms.
"""

from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
from typing import Any, Final, Iterable, Iterator, Mapping, Sequence

import numpy as np
import torch
from torch import nn

from experiments.candidates.folr_core.partner_writer_stale_load_routing_host import (
    ARMS,
    COMPLETE_RESET,
    ISOMORPHIC_GENERIC_UPDATE,
    TYPED_OWNER_EPOCH_ROUTING,
    HostDimensions,
    PartnerWriteDTO,
    PartnerWriterStaleLoadHost,
    tensor_digest,
)


SCHEMA_VERSION: Final = 1
MASTER_SEEDS: Final = tuple(range(95031, 95039))
REGIMES: Final = ("CLEAN", "STALE_LOAD")
BRANCHES: Final = (
    "B3_INVALID_CONTRACT",
    "B3_PARTNER_WRITE_CALIBRATION_FAILED",
    "B3_RESET_OR_CLEAN_CAPACITY_FAILED",
    "B3_TYPED_ROUTING_FAILED",
    "B3_GENERIC_SUFFICIENT_AT_CAP",
    "B3_LOCAL_TYPED_ROUTING_VALUE_SUPPORTED",
    "B3_INDETERMINATE_AT_CAP",
)
TECHNICAL_DECISION: Final = "TECHNICAL_ONLY_NO_SCIENTIFIC_DECISION"


@dataclass(frozen=True)
class ExperimentConfig:
    master_seeds: tuple[int, ...]
    p_train_batches: int
    p_train_batch_size: int
    p_eval_episodes: int
    r_train_batches: int
    r_train_batch_size: int
    r_eval_episodes_per_regime: int
    learning_rate: float
    technical_only: bool

    def to_json(self) -> dict[str, Any]:
        value = asdict(self)
        value["master_seeds"] = list(self.master_seeds)
        return value


def registered_config() -> ExperimentConfig:
    return ExperimentConfig(
        master_seeds=MASTER_SEEDS,
        p_train_batches=32,
        p_train_batch_size=64,
        p_eval_episodes=512,
        r_train_batches=32,
        r_train_batch_size=64,
        r_eval_episodes_per_regime=512,
        learning_rate=0.025,
        technical_only=False,
    )


def technical_smoke_config() -> ExperimentConfig:
    return ExperimentConfig(
        master_seeds=(MASTER_SEEDS[0],),
        p_train_batches=2,
        p_train_batch_size=8,
        p_eval_episodes=16,
        r_train_batches=1,
        r_train_batch_size=16,
        r_eval_episodes_per_regime=8,
        learning_rate=0.025,
        technical_only=True,
    )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(f"write-once artifact already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"write-once temporary already exists: {temporary.name}")
    with temporary.open("xb") as handle:
        handle.write(_canonical_bytes(value) + b"\n")
    temporary.replace(path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_binding(path: Path, *, rows: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "path": path.name,
        "sha256": _sha256_file(path),
        "bytes": path.stat().st_size,
    }
    if rows is not None:
        value["rows"] = int(rows)
    return value


def _derive_seed(master_seed: int, namespace: str) -> int:
    payload = f"FOLR-B3\0{int(master_seed)}\0{namespace}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little") % (2**31 - 1)


def _rng_identity(master_seed: int, namespace: str) -> dict[str, Any]:
    return {
        "scheme": "sha256/FOLR-B3/master-seed/namespace/v1",
        "master_seed": int(master_seed),
        "namespace": namespace,
        "derived_seed": _derive_seed(master_seed, namespace),
    }


def _initialize(module: nn.Module, seed: int) -> None:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(seed))
        for item in module.modules():
            if isinstance(item, nn.Linear):
                nn.init.xavier_uniform_(item.weight)
                nn.init.zeros_(item.bias)


def _bit_tensor(values: Sequence[int]) -> torch.Tensor:
    return torch.tensor([[-1.0 if int(v) == 0 else 1.0] for v in values], dtype=torch.float32)


class OrdinaryPartnerWriter(nn.Module):
    """The only phase-P target-bearing state path."""

    def __init__(self, *, initialization_seed: int) -> None:
        super().__init__()
        self.pre_event_wait = nn.Linear(1, 1)
        self.writer = nn.Linear(1, 4)
        self.readout = nn.Linear(4, 2)
        _initialize(self, initialization_seed)

    def write(self, bit: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.writer(bit))

    def wait_logit(self, public_nuisance: torch.Tensor) -> torch.Tensor:
        return self.pre_event_wait(public_nuisance)

    def logits(self, bit: torch.Tensor) -> torch.Tensor:
        return self.readout(self.write(bit))


class MatchedRoutedActor(nn.Module):
    """Identical trainable architecture for all three phase-R arms."""

    def __init__(
        self,
        *,
        frozen_writer_state: Mapping[str, torch.Tensor],
        initialization_seed: int,
    ) -> None:
        super().__init__()
        self.owner_writer = nn.Linear(1, 2)
        self.obsolete_partner_writer = nn.Linear(1, 2)
        self.event_update = nn.Linear(8, 4)
        self.action_head = nn.Linear(4, 4)
        _initialize(self, initialization_seed)
        self.partner_writer = OrdinaryPartnerWriter(initialization_seed=0)
        self.partner_writer.load_state_dict(frozen_writer_state, strict=True)
        for parameter in self.partner_writer.parameters():
            parameter.requires_grad_(False)

    def pre_event(self, s: torch.Tensor, n_old: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        return torch.tanh(self.owner_writer(s)), torch.tanh(self.obsolete_partner_writer(n_old))

    def partner_write(self, n_new: torch.Tensor) -> torch.Tensor:
        return self.partner_writer.write(n_new)

    def routed_state(
        self,
        *,
        arm: str,
        owner_state: torch.Tensor,
        obsolete_state: torch.Tensor,
        partner_state: torch.Tensor,
        owner_epoch_valid: bool = True,
    ) -> torch.Tensor:
        if arm not in ARMS:
            raise ValueError(f"unknown arm {arm!r}")
        owner = owner_state if owner_epoch_valid and arm != COMPLETE_RESET else torch.zeros_like(owner_state)
        obsolete = obsolete_state if arm == ISOMORPHIC_GENERIC_UPDATE else torch.zeros_like(obsolete_state)
        candidate = torch.cat((owner, obsolete, partner_state), dim=-1)
        return torch.tanh(self.event_update(candidate))

    def logits(
        self,
        *,
        arm: str,
        s: torch.Tensor,
        n_old: torch.Tensor,
        n_new: torch.Tensor,
        owner_epoch_valid: bool = True,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        owner, obsolete = self.pre_event(s, n_old)
        partner = self.partner_write(n_new)
        routed = self.routed_state(
            arm=arm,
            owner_state=owner,
            obsolete_state=obsolete,
            partner_state=partner,
            owner_epoch_valid=owner_epoch_valid,
        )
        return self.action_head(routed), {
            "owner": owner,
            "obsolete": obsolete,
            "partner": partner,
            "routed": routed,
        }

    def trainable_schema(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "shape": list(parameter.shape), "count": parameter.numel()}
            for name, parameter in self.named_parameters()
            if parameter.requires_grad
        ]


def generic_class_nesting_witness(actor: MatchedRoutedActor) -> dict[str, Any]:
    """Construct the exact generic parameter mapping for the typed transition."""
    mapped = {name: value.detach().clone() for name, value in actor.state_dict().items()}
    mapped["event_update.weight"][:, 2:4] = 0.0
    source = actor.event_update.weight.detach()
    return {
        "mapping": {
            "event_update.weight[:,0:2]": "identity_copy_from_typed_owner_columns",
            "event_update.weight[:,2:4]": "exact_zero_for_obsolete_partner_columns",
            "event_update.weight[:,4:8]": "identity_copy_from_typed_new_partner_columns",
            "event_update.bias": "identity_copy",
            "owner_writer/*": "identity_copy",
            "obsolete_partner_writer/*": "arbitrary_but_masked_by_zero_columns",
            "action_head/*": "identity_copy",
            "partner_writer/*": "byte_identical_frozen_copy",
        },
        "typed_transition_formula": "tanh(W_owner*h_owner + W_new*h_new + bias)",
        "generic_transition_formula_after_mapping": "tanh(W_owner*h_owner + 0*h_old + W_new*h_new + bias)",
        "zeroed_source_columns_digest": tensor_digest(torch.zeros_like(source[:, 2:4])),
        "mapped_state_digest": _state_digest(mapped),
        "constructive_containment": True,
    }


def _state_digest(state: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        value = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tuple(value.shape)).encode("utf-8"))
        digest.update(value.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _root(seed: int, namespace: str, index: int) -> int:
    parts = namespace.split("/")
    if len(parts) == 3 and parts[0] == "R" and parts[1] in ARMS and parts[2] in ("train", "evaluate"):
        arm_ordinal = ARMS.index(parts[1]) + 1
        phase_ordinal = 1 if parts[2] == "train" else 2
        # Disjoint integer blocks make isolation constructive, rather than a
        # probabilistic property of a truncated hash.
        return int(seed) * 10_000_000 + arm_ordinal * 2_000_000 + phase_ordinal * 1_000_000 + int(index)
    return _derive_seed(seed, f"{namespace}/root/{index}")


def _p_rows(config: ExperimentConfig, seed: int, phase: str) -> list[dict[str, Any]]:
    total = (
        config.p_train_batches * config.p_train_batch_size
        if phase == "train"
        else config.p_eval_episodes
    )
    rows = []
    for index in range(total):
        rows.append(
            {
                "master_seed": seed,
                "phase": f"P_{phase}",
                "episode": index,
                "batch": index // config.p_train_batch_size if phase == "train" else None,
                "n_new": index % 2,
                "identity_variant": (index // 2) % 4,
                "unused_pre_event": (index // 8) % 2,
                "root": _root(seed, f"P/{phase}", index),
                "action_uniform": ((_derive_seed(seed, f"P/{phase}/action/{index}") % 999983) + 0.5) / 999984.0,
                "rng_identity": _rng_identity(seed, f"P/{phase}/episode/{index}"),
            }
        )
    return rows


def _r_rows(config: ExperimentConfig, seed: int, phase: str, arm: str) -> list[dict[str, Any]]:
    if arm not in ARMS:
        raise ValueError(f"unknown phase-R arm {arm!r}")
    rows: list[dict[str, Any]] = []
    if phase == "train":
        for batch in range(config.r_train_batches):
            if config.r_train_batch_size % 8:
                raise ValueError("phase-R batch size must be divisible by eight")
            cells: list[tuple[str, int, int, int]] = []
            # Half CLEAN: four (s,n_new) cells, repeated equally.
            for _ in range((config.r_train_batch_size // 2) // 4):
                for s in (0, 1):
                    for n_new in (0, 1):
                        cells.append(("CLEAN", s, 0, n_new))
            # Half STALE_LOAD: all eight cells.
            for _ in range((config.r_train_batch_size // 2) // 8):
                for s in (0, 1):
                    for n_old in (0, 1):
                        for n_new in (0, 1):
                            cells.append(("STALE_LOAD", s, n_old, n_new))
            if len(cells) != config.r_train_batch_size:
                raise RuntimeError("phase-R frozen batch construction drifted")
            for offset, (regime, s, n_old, n_new) in enumerate(cells):
                index = batch * config.r_train_batch_size + offset
                rows.append(
                    {
                        "master_seed": seed,
                        "phase": "R_train",
                        "episode": index,
                        "batch": batch,
                        "regime": regime,
                        "s": s,
                        "n_old": n_old,
                        "n_new": n_new,
                        "root": _root(seed, f"R/{arm}/train", index),
                        "action_uniform": ((_derive_seed(seed, f"R/{arm}/train/action/{index}") % 999983) + 0.5) / 999984.0,
                        "rng_identity": _rng_identity(seed, f"R/{arm}/train/episode/{index}"),
                    }
                )
    else:
        for regime_index, regime in enumerate(REGIMES):
            for index in range(config.r_eval_episodes_per_regime):
                s = index % 2
                n_new = (index // 2) % 2
                n_old = (index // 4) % 2 if regime == "STALE_LOAD" else 0
                absolute = regime_index * config.r_eval_episodes_per_regime + index
                rows.append(
                    {
                        "master_seed": seed,
                        "phase": "R_evaluate",
                        "episode": absolute,
                        "batch": None,
                        "regime": regime,
                        "s": s,
                        "n_old": n_old,
                        "n_new": n_new,
                        "root": _root(seed, f"R/{arm}/evaluate", absolute),
                        "action_uniform": ((_derive_seed(seed, f"R/{arm}/evaluate/action/{absolute}") % 999983) + 0.5) / 999984.0,
                        "rng_identity": _rng_identity(seed, f"R/{arm}/evaluate/episode/{absolute}"),
                    }
                )
    return rows


def _expected_counts(config: ExperimentConfig, *, phase_r_ran: bool, contract_valid: bool = True) -> dict[str, int]:
    seeds = len(config.master_seeds)
    p_train = seeds * config.p_train_batches * config.p_train_batch_size if contract_valid else 0
    p_eval = seeds * config.p_eval_episodes if contract_valid else 0
    r_train = len(ARMS) * seeds * config.r_train_batches * config.r_train_batch_size if phase_r_ran else 0
    r_eval = len(ARMS) * seeds * len(REGIMES) * config.r_eval_episodes_per_regime if phase_r_ran else 0
    updates = seeds * config.p_train_batches + (len(ARMS) * seeds * config.r_train_batches if phase_r_ran else 0)
    episodes = p_train + p_eval + r_train + r_eval
    return {
        "phase_p_train_episodes": p_train,
        "phase_p_evaluation_episodes": p_eval,
        "phase_r_train_episodes": r_train,
        "phase_r_evaluation_episodes": r_eval,
        "training_episodes": p_train + r_train,
        "evaluation_episodes": p_eval + r_eval,
        "complete_episodes": episodes,
        "environment_transitions": episodes * 3,
        "policy_calls": episodes * 3,
        "learner_calls": updates,
        "trainer_calls": updates,
        "optimizer_updates": updates,
        "final_checkpoints": seeds + (len(ARMS) * seeds if phase_r_ran else 0),
        "registered_fulls": 0 if config.technical_only else 1,
        "retries": 0,
        "rescues": 0,
        "sweeps": 0,
        "checkpoint_selections": 0,
        "hypothetical_transitions": 0,
        "stochastic_draws": episodes,
    }


def _real_event_contract_probe() -> dict[str, Any]:
    """Pure deterministic binding probe; it is not an experiment episode."""
    host = PartnerWriterStaleLoadHost(root=0, regime="CALIBRATION", dimensions=HostDimensions())
    host.transition_one(owner_state=torch.zeros(2), obsolete_partner_state=torch.zeros(2))
    replacement = host.apply_replacement(host.replacement_transaction())
    dto = PartnerWriteDTO.make(
        writer_call_identity="manifest/contract-probe",
        source_bit=0,
        payload=torch.zeros(4),
    )
    write = host.transition_two(dto)
    terminal = host.terminal_transition(action=0, target=0, action_count=2)
    return {
        "typed_transaction": replacement.typed_transaction,
        "exact_deltas": replacement.exact_deltas,
        "pre_keys": list(replacement.pre_keys),
        "post_keys": list(replacement.post_keys),
        "owner_record_preserved": replacement.owner_record_preserved,
        "owner_epoch_preserved": replacement.owner_epoch_preserved,
        "old_partner_terminated": replacement.old_partner_terminated,
        "new_partner_joined": replacement.new_partner_joined,
        "old_partner_state_invalidated": replacement.old_partner_state_invalidated,
        "writer_owner": write["writer_binding"]["owner"],
        "writer_partner": write["writer_binding"]["partner"],
        "all_memory_cleared": terminal["all_memory_cleared"],
    }


def _phase_r_root_isolation(manifest: Mapping[str, Any], config: ExperimentConfig) -> bool:
    for seed in config.master_seeds:
        all_sets: dict[tuple[str, str], set[int]] = {}
        for arm in ARMS:
            for phase in ("train", "evaluate"):
                roots = {int(row["root"]) for row in manifest["phase_r"][str(seed)][arm][phase]}
                rows = manifest["phase_r"][str(seed)][arm][phase]
                if len(roots) != len(rows):
                    return False
                all_sets[(arm, phase)] = roots
        keys = list(all_sets)
        for index, left in enumerate(keys):
            for right in keys[index + 1 :]:
                if all_sets[left].intersection(all_sets[right]):
                    return False
    return True


def _contract_evidence(manifest: Mapping[str, Any], config: ExperimentConfig) -> dict[str, Any]:
    architecture = manifest["architecture"]
    nesting = architecture["generic_class_nesting"]
    probe = manifest["real_event_contract_probe"]
    expected_counts = _expected_counts(config, phase_r_ran=True)
    predicates = {
        "C01_BINDING": manifest["owner_binding"] == "owner_t@0" and manifest["partner_replacement"] == "inert_partner_q0@0->inert_partner_q1@0",
        "C02_GENERIC_CLASS_NESTING": bool(nesting["constructive_containment"]) and nesting["mapping"]["event_update.weight[:,2:4]"] == "exact_zero_for_obsolete_partner_columns",
        "C03_ARM_MATCHING": bool(architecture["same_initialization_namespace_within_seed"]) and bool(architecture["same_writer_update_readout_burden"]) and architecture["trainable_parameter_count_each_phase_r_arm"] == sum(row["count"] for row in architecture["trainable_schema_each_phase_r_arm"]),
        "C04_REAL_EVENT_AND_WRITE": all(bool(probe[name]) for name in ("typed_transaction", "exact_deltas", "owner_record_preserved", "owner_epoch_preserved", "old_partner_terminated", "new_partner_joined", "old_partner_state_invalidated", "all_memory_cleared")) and probe["pre_keys"] == ["owner_t", "inert_partner_q0"] and probe["post_keys"] == ["owner_t", "inert_partner_q1"] and probe["writer_owner"] == "owner_t@0" and probe["writer_partner"] == "inert_partner_q1@0",
        "C05_SHORTCUT_FIREWALL": all(int(value) == 0 for value in manifest["firewalls"].values()),
        "C06_ACTIVITY_CAPS": all(expected_counts[name] <= int(limit) for name, limit in manifest["caps"].items()),
        "C07_ROOT_AND_ARTIFACT_ISOLATION": bool(manifest["run_id"]) and len(manifest["source_commit"]) == 40 and _phase_r_root_isolation(manifest, config),
    }
    first_failure = next((name for name, passed in predicates.items() if not passed), None)
    return {
        "evidence_kind": "FOLR_B3_STRUCTURED_CONTRACT_EVIDENCE",
        "predicates": predicates,
        "valid": first_failure is None,
        "first_failure_id": first_failure,
        "io_failures_are_contract_evidence": False,
    }


def _phase_p_not_run() -> dict[str, Any]:
    return {
        "status": "NOT_RUN_INVALID_CONTRACT",
        "aggregate_accuracy": None,
        "seed_metrics": [],
        "every_seed_at_least_0_90": False,
        "aggregate_at_least_0_95": False,
        "kernels_respond_to_n_new": False,
        "identity_unused_pre_event_invariant": False,
        "calibration_passed": False,
        "sidecar": None,
    }


def build_frozen_manifest(*, config: ExperimentConfig, source_commit: str, run_id: str) -> dict[str, Any]:
    if len(source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in source_commit.lower()):
        raise ValueError("source_commit must be a full hexadecimal Git identity")
    dimensions = HostDimensions()
    witness_writer = OrdinaryPartnerWriter(initialization_seed=_derive_seed(config.master_seeds[0], "P/initialization"))
    witness_actor = MatchedRoutedActor(
        frozen_writer_state=witness_writer.state_dict(),
        initialization_seed=_derive_seed(config.master_seeds[0], "R/initialization"),
    )
    schema = witness_actor.trainable_schema()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B3_FROZEN_MANIFEST",
        "treatment": "FOLR-B3-CALIBRATED-PARTNER-WRITER-STALE-LOAD-ROUTING",
        "direction": "CAND-VAP-FOLR-CORE@constructive-revision-v6",
        "source_commit": source_commit.lower(),
        "run_id": str(run_id),
        "technical_only": config.technical_only,
        "config": config.to_json(),
        "owner_binding": "owner_t@0",
        "partner_replacement": "inert_partner_q0@0->inert_partner_q1@0",
        "arms": list(ARMS),
        "regimes": list(REGIMES),
        "architecture": {
            "state_dimension": 8,
            "trainable_schema_each_phase_r_arm": schema,
            "trainable_parameter_count_each_phase_r_arm": sum(row["count"] for row in schema),
            "same_initialization_namespace_within_seed": True,
            "same_writer_update_readout_burden": True,
            "sole_treatment_difference": "fixed lifecycle input mask before identical event_update",
            "generic_class_nesting": generic_class_nesting_witness(witness_actor),
        },
        "phase_p": {str(seed): {"train": _p_rows(config, seed, "train"), "evaluate": _p_rows(config, seed, "evaluate")} for seed in config.master_seeds},
        "phase_r": {
            str(seed): {
                arm: {
                    "train": _r_rows(config, seed, "train", arm),
                    "evaluate": _r_rows(config, seed, "evaluate", arm),
                }
                for arm in ARMS
            }
            for seed in config.master_seeds
        },
        "caps": {
            "training_episodes": 65536,
            "evaluation_episodes": 28672,
            "complete_episodes": 94208,
            "environment_transitions": 282624,
            "policy_calls": 282624,
            "learner_calls": 1024,
            "trainer_calls": 1024,
            "optimizer_updates": 1024,
        },
        "firewalls": {
            "b2_artifacts_weights_schemas": 0,
            "direct_final_cue": 0,
            "auxiliary_supervision": 0,
            "critic_calls": 0,
            "recurrence": 0,
            "cached_action_or_kernel": 0,
            "extra_arm_seed_regime": 0,
            "retry_rescue_sweep_checkpoint_selection": 0,
        },
        "dimensions": asdict(dimensions),
        "real_event_contract_probe": _real_event_contract_probe(),
    }
    _validate_manifest(manifest, config)
    return manifest


def _sample_actions(probabilities: torch.Tensor, uniforms: Sequence[float]) -> torch.Tensor:
    cumulative = probabilities.detach().cpu().cumsum(dim=-1).numpy()
    actions = [int(np.searchsorted(row, float(uniform), side="right")) for row, uniform in zip(cumulative, uniforms)]
    return torch.tensor([min(action, probabilities.shape[-1] - 1) for action in actions], dtype=torch.long)


def _reinforce_update(logits: torch.Tensor, targets: torch.Tensor, uniforms: Sequence[float], optimizer: torch.optim.Optimizer) -> tuple[float, float, torch.Tensor]:
    probabilities = torch.softmax(logits, dim=-1)
    actions = _sample_actions(probabilities, uniforms)
    rewards = (actions == targets).to(torch.float32)
    selected = torch.log(torch.gather(probabilities, 1, actions[:, None]).clamp_min(1e-8)).squeeze(1)
    loss = -(rewards * selected).mean()
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()
    return float(loss.detach()), float(rewards.mean()), actions


def _kernel_payload(logits: torch.Tensor) -> dict[str, Any]:
    logits_cpu = logits.detach().cpu().to(torch.float32).contiguous()
    probabilities = torch.softmax(logits_cpu, dim=-1).contiguous()
    logit_bytes = logits_cpu.numpy().tobytes(order="C")
    probability_bytes = probabilities.numpy().tobytes(order="C")
    return {
        "logits": logits_cpu.tolist(),
        "probabilities": probabilities.tolist(),
        "logits_base64": base64.b64encode(logit_bytes).decode("ascii"),
        "probabilities_base64": base64.b64encode(probability_bytes).decode("ascii"),
        "logits_sha256": hashlib.sha256(logit_bytes).hexdigest(),
        "probabilities_sha256": hashlib.sha256(probability_bytes).hexdigest(),
    }


class _GzipJsonlWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle: Any = None

    def __enter__(self) -> "_GzipJsonlWriter":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise FileExistsError(f"write-once sidecar already exists: {self.path.name}")
        self.handle = gzip.open(self.path, "xt", encoding="utf-8", newline="\n")
        return self

    def write(self, value: Mapping[str, Any]) -> None:
        self.handle.write(_canonical_bytes(value).decode("utf-8") + "\n")

    def __exit__(self, *_: object) -> None:
        self.handle.close()


def _read_jsonl_gz(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def _checkpoint_path(root: Path, phase: str, seed: int, arm: str | None = None) -> Path:
    if phase == "P":
        return root / "checkpoints" / "phase_p" / f"seed_{seed}.pt"
    if arm is None:
        raise ValueError("phase-R checkpoint requires arm")
    return root / "checkpoints" / "phase_r" / arm / f"seed_{seed}.pt"


def _save_checkpoint(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"write-once checkpoint already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(dict(payload), path)


def _load_checkpoint(path: Path) -> dict[str, Any]:
    return torch.load(path, map_location="cpu", weights_only=False)


def _phase_p_train(config: ExperimentConfig, manifest: Mapping[str, Any], root: Path) -> tuple[list[dict[str, Any]], dict[int, dict[str, torch.Tensor]]]:
    seed_metrics: list[dict[str, Any]] = []
    states: dict[int, dict[str, torch.Tensor]] = {}
    for seed in config.master_seeds:
        model = OrdinaryPartnerWriter(initialization_seed=_derive_seed(seed, "P/initialization"))
        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
        train_rows = manifest["phase_p"][str(seed)]["train"]
        batch_metrics = []
        for batch in range(config.p_train_batches):
            rows = [row for row in train_rows if int(row["batch"]) == batch]
            bits = _bit_tensor([row["n_new"] for row in rows])
            payloads = model.write(bits)
            logits = model.readout(payloads)
            hosts = []
            for row, payload in zip(rows, payloads):
                host = PartnerWriterStaleLoadHost(root=int(row["root"]), regime="CALIBRATION", dimensions=HostDimensions())
                model.wait_logit(torch.tensor([[float(host.public_observation()[0])]], dtype=torch.float32))
                host.transition_one(owner_state=torch.zeros(2), obsolete_partner_state=torch.zeros(2))
                host.apply_replacement(host.replacement_transaction())
                host.transition_two(PartnerWriteDTO.make(writer_call_identity=f"P/train/{seed}/{row['episode']}", source_bit=int(row["n_new"]), payload=payload))
                hosts.append(host)
            loss, reward, actions = _reinforce_update(logits, torch.tensor([row["n_new"] for row in rows]), [row["action_uniform"] for row in rows], optimizer)
            for row, host, action in zip(rows, hosts, actions.tolist()):
                host.terminal_transition(action=int(action), target=int(row["n_new"]), action_count=2)
            batch_metrics.append({"batch": batch, "loss": loss, "mean_external_reward": reward})
        state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
        states[seed] = state
        path = _checkpoint_path(root, "P", seed)
        _save_checkpoint(path, {"phase": "P", "master_seed": seed, "final_only": True, "writer_state": state, "writer_state_digest": _state_digest(state)})
        seed_metrics.append({"master_seed": seed, "batches": batch_metrics, "checkpoint": path.relative_to(root).as_posix(), "writer_state_digest": _state_digest(state)})
    return seed_metrics, states


def _phase_p_evaluate(config: ExperimentConfig, manifest: Mapping[str, Any], root: Path, states: Mapping[int, Mapping[str, torch.Tensor]]) -> tuple[dict[str, Any], int]:
    sidecar = root / "phase_p_evaluation.jsonl.gz"
    seed_rows = []
    total_rows = 0
    with _GzipJsonlWriter(sidecar) as writer:
        for seed in config.master_seeds:
            model = OrdinaryPartnerWriter(initialization_seed=0)
            model.load_state_dict(states[seed], strict=True)
            eval_rows = manifest["phase_p"][str(seed)]["evaluate"]
            correct = 0
            response_tvs = []
            for row in eval_rows:
                bit = int(row["n_new"])
                host = PartnerWriterStaleLoadHost(root=int(row["root"]), regime="CALIBRATION", dimensions=HostDimensions())
                pre_event_wait_logit = float(model.wait_logit(torch.tensor([[float(host.public_observation()[0])]], dtype=torch.float32))[0, 0].detach())
                neutral_owner = torch.zeros(2)
                neutral_old = torch.zeros(2)
                t1 = host.transition_one(owner_state=neutral_owner, obsolete_partner_state=neutral_old)
                witness = host.apply_replacement(host.replacement_transaction())
                payload = model.write(_bit_tensor([bit]))[0]
                dto = PartnerWriteDTO.make(writer_call_identity=f"P/{seed}/{row['episode']}", source_bit=bit, payload=payload)
                t2 = host.transition_two(dto)
                logits = model.readout(dto.materialize(device=torch.device("cpu")))[None, :]
                probabilities = torch.softmax(logits, dim=-1)
                action = int(_sample_actions(probabilities, [row["action_uniform"]])[0])
                terminal = host.terminal_transition(action=action, target=bit, action_count=2)
                opposite = model.logits(_bit_tensor([1 - bit]))
                tv = 0.5 * float(torch.abs(probabilities - torch.softmax(opposite, dim=-1)).sum())
                response_tvs.append(tv)
                correct += int(action == bit)
                writer.write({**row, "pre_event_wait_logit": pre_event_wait_logit, "transition_one": t1, "replacement": asdict(witness), "transition_two": t2, "terminal": terminal, "kernel": _kernel_payload(logits), "n_new_flip_kernel": _kernel_payload(opposite), "action": action, "reward": terminal["reward"], "n_new_flip_tv": tv})
                total_rows += 1
            accuracy = correct / len(eval_rows)
            seed_rows.append({"master_seed": seed, "episodes": len(eval_rows), "accuracy": accuracy, "min_n_new_flip_tv": min(response_tvs)})
    summary = _summarize_phase_p_rows(list(_read_jsonl_gz(sidecar)))
    summary["sidecar"] = _file_binding(sidecar, rows=total_rows)
    return summary, total_rows


def _phase_p_identity_invariance(path: Path) -> bool:
    grouped: dict[tuple[int, int], set[str]] = {}
    for row in _read_jsonl_gz(path):
        grouped.setdefault((int(row["master_seed"]), int(row["n_new"])), set()).add(row["kernel"]["probabilities_base64"])
    return bool(grouped) and all(len(values) == 1 for values in grouped.values())


def _summarize_phase_p_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    seeds = sorted({int(row["master_seed"]) for row in rows})
    seed_rows = []
    for seed in seeds:
        selected = [row for row in rows if int(row["master_seed"]) == seed]
        seed_rows.append(
            {
                "master_seed": seed,
                "episodes": len(selected),
                "accuracy": sum(float(row["reward"]) for row in selected) / len(selected),
                "min_n_new_flip_tv": min(float(row["n_new_flip_tv"]) for row in selected),
            }
        )
    aggregate = sum(row["accuracy"] * row["episodes"] for row in seed_rows) / sum(row["episodes"] for row in seed_rows)
    grouped: dict[tuple[int, int], set[str]] = {}
    for row in rows:
        grouped.setdefault((int(row["master_seed"]), int(row["n_new"])), set()).add(row["kernel"]["probabilities_base64"])
    invariant = bool(grouped) and all(len(values) == 1 for values in grouped.values())
    summary = {
        "aggregate_accuracy": aggregate,
        "seed_metrics": seed_rows,
        "every_seed_at_least_0_90": all(row["accuracy"] >= 0.90 for row in seed_rows),
        "aggregate_at_least_0_95": aggregate >= 0.95,
        "kernels_respond_to_n_new": all(row["min_n_new_flip_tv"] > 0.0 for row in seed_rows),
        "identity_unused_pre_event_invariant": invariant,
    }
    summary["calibration_passed"] = all(
        (
            summary["every_seed_at_least_0_90"],
            summary["aggregate_at_least_0_95"],
            summary["kernels_respond_to_n_new"],
            summary["identity_unused_pre_event_invariant"],
        )
    )
    return summary


def _validate_lifecycle_witness(row: Mapping[str, Any], *, writer_call_identity: str) -> None:
    replacement = row["replacement"]
    required_true = (
        "typed_transaction",
        "exact_deltas",
        "owner_record_preserved",
        "owner_epoch_preserved",
        "old_partner_terminated",
        "new_partner_joined",
        "old_partner_state_invalidated",
    )
    if not all(replacement[name] is True for name in required_true):
        raise ValueError("retained replacement witness is incomplete")
    if tuple(replacement["pre_keys"]) != ("owner_t", "inert_partner_q0") or tuple(replacement["post_keys"]) != ("owner_t", "inert_partner_q1"):
        raise ValueError("retained replacement roster witness drifted")
    if len(replacement["public_pre_digest"]) != 64 or len(replacement["public_post_digest"]) != 64:
        raise ValueError("retained replacement snapshot digest is malformed")
    transition_one = row["transition_one"]
    transition_two = row["transition_two"]
    binding = transition_two["writer_binding"]
    if transition_one["transition"] != 1 or transition_one["action"] != "WAIT" or transition_one["reward"] != 0.0:
        raise ValueError("transition-one lifecycle witness drifted")
    if transition_two["transition"] != 2 or transition_two["action"] != "WAIT" or transition_two["reward"] != 0.0:
        raise ValueError("transition-two lifecycle witness drifted")
    if binding["owner"] != "owner_t@0" or binding["partner"] != "inert_partner_q1@0" or binding["writer_call_identity"] != writer_call_identity or len(binding["payload_digest"]) != 64:
        raise ValueError("retained partner-write binding drifted")


def _manifest_projection(row: Mapping[str, Any], *, phase_r: bool) -> dict[str, Any]:
    fields = ["master_seed", "phase", "episode", "batch", "root", "action_uniform", "rng_identity"]
    fields += ["regime", "s", "n_old", "n_new"] if phase_r else ["n_new", "identity_variant", "unused_pre_event"]
    return {name: row[name] for name in fields}


def _phase_r_train(config: ExperimentConfig, manifest: Mapping[str, Any], root: Path, writer_states: Mapping[int, Mapping[str, torch.Tensor]]) -> list[dict[str, Any]]:
    runs = []
    for seed in config.master_seeds:
        initialization_seed = _derive_seed(seed, "R/initialization")
        reference_state: Mapping[str, torch.Tensor] | None = None
        reference_schema: list[dict[str, Any]] | None = None
        for arm in ARMS:
            actor = MatchedRoutedActor(frozen_writer_state=writer_states[seed], initialization_seed=initialization_seed)
            if reference_state is None:
                reference_state = {name: value.detach().clone() for name, value in actor.state_dict().items()}
                reference_schema = actor.trainable_schema()
            else:
                if actor.trainable_schema() != reference_schema or any(not torch.equal(actor.state_dict()[name], value) for name, value in reference_state.items()):
                    raise RuntimeError("phase-R arms are not byte-identical at initialization")
            optimizer = torch.optim.Adam([p for p in actor.parameters() if p.requires_grad], lr=config.learning_rate)
            train_rows = manifest["phase_r"][str(seed)][arm]["train"]
            batch_metrics = []
            for batch in range(config.r_train_batches):
                rows = [row for row in train_rows if int(row["batch"]) == batch]
                s = _bit_tensor([row["s"] for row in rows])
                n_old = _bit_tensor([row["n_old"] for row in rows])
                n_new = _bit_tensor([row["n_new"] for row in rows])
                owner, obsolete = actor.pre_event(s, n_old)
                partner = actor.partner_write(n_new)
                effective_obsolete = obsolete.clone()
                clean_mask = torch.tensor([row["regime"] == "CLEAN" for row in rows], dtype=torch.bool)
                effective_obsolete[clean_mask] = 0.0
                routed = actor.routed_state(arm=arm, owner_state=owner, obsolete_state=effective_obsolete, partner_state=partner)
                logits = actor.action_head(routed)
                hosts = []
                for row, owner_row, obsolete_row, partner_row in zip(rows, owner, effective_obsolete, partner):
                    host = PartnerWriterStaleLoadHost(root=int(row["root"]), regime=str(row["regime"]), dimensions=HostDimensions())
                    host.transition_one(owner_state=owner_row, obsolete_partner_state=obsolete_row)
                    host.apply_replacement(host.replacement_transaction())
                    host.transition_two(PartnerWriteDTO.make(writer_call_identity=f"R/train/{arm}/{seed}/{row['episode']}", source_bit=int(row["n_new"]), payload=partner_row))
                    hosts.append(host)
                targets = torch.tensor([2 * int(row["s"]) + int(row["n_new"]) for row in rows])
                loss, reward, actions = _reinforce_update(logits, targets, [row["action_uniform"] for row in rows], optimizer)
                for row, host, action in zip(rows, hosts, actions.tolist()):
                    host.terminal_transition(action=int(action), target=2 * int(row["s"]) + int(row["n_new"]), action_count=4)
                batch_metrics.append({"batch": batch, "loss": loss, "mean_external_reward": reward})
            state = {name: value.detach().cpu().clone() for name, value in actor.state_dict().items()}
            checkpoint = _checkpoint_path(root, "R", seed, arm)
            nesting = generic_class_nesting_witness(actor)
            _save_checkpoint(checkpoint, {
                "phase": "R",
                "arm": arm,
                "master_seed": seed,
                "final_only": True,
                "actor_state": state,
                "trainable_schema": actor.trainable_schema(),
                "frozen_writer_state_digest": _state_digest(writer_states[seed]),
                "generic_class_nesting": nesting,
                "rng_identity": {
                    "namespace": f"R/{arm}/initialization/paired-within-seed",
                    "master_seed": seed,
                    "derived_seed": initialization_seed,
                    "paired_initialization": True,
                },
            })
            runs.append({"arm": arm, "master_seed": seed, "batches": batch_metrics, "checkpoint": checkpoint.relative_to(root).as_posix(), "frozen_writer_state_digest": _state_digest(writer_states[seed]), "generic_class_nesting": nesting})
    return runs


def train(*, output_root: str | Path, source_commit: str, run_id: str, technical_only: bool = False) -> dict[str, Any]:
    root = Path(output_root).resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("output root must be absent or empty for one-shot isolation")
    root.mkdir(parents=True, exist_ok=True)
    config = technical_smoke_config() if technical_only else registered_config()
    manifest = build_frozen_manifest(config=config, source_commit=source_commit, run_id=run_id)
    _write_json(root / "manifest.json", manifest)
    contract_evidence = _contract_evidence(manifest, config)
    if contract_evidence["valid"]:
        p_train, writer_states = _phase_p_train(config, manifest, root)
        p_evaluation, _ = _phase_p_evaluate(config, manifest, root, writer_states)
        phase_r_ran = bool(p_evaluation["calibration_passed"])
        r_train = _phase_r_train(config, manifest, root, writer_states) if phase_r_ran else []
    else:
        p_train, p_evaluation, phase_r_ran, r_train = [], _phase_p_not_run(), False, []
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B3_TRAIN_SUMMARY",
        "source_commit": source_commit.lower(),
        "run_id": run_id,
        "technical_only": technical_only,
        "stage": "TRAIN_COMPLETE" if contract_evidence["valid"] else "INVALID_CONTRACT_STOP",
        "contract_evidence": contract_evidence,
        "phase_p_train": p_train,
        "phase_p_evaluation": p_evaluation,
        "phase_r_ran": phase_r_ran,
        "phase_r_train": r_train,
        "activity_counts": _expected_counts(config, phase_r_ran=phase_r_ran, contract_valid=contract_evidence["valid"]),
        "manifest_binding": _file_binding(root / "manifest.json"),
    }
    _write_json(root / "train_summary.json", summary)
    validate_train(root, require_full=not technical_only)
    return summary


def _actor_from_checkpoint(checkpoint: Mapping[str, Any]) -> MatchedRoutedActor:
    state = checkpoint["actor_state"]
    writer_state = {name.removeprefix("partner_writer."): value for name, value in state.items() if name.startswith("partner_writer.")}
    actor = MatchedRoutedActor(frozen_writer_state=writer_state, initialization_seed=0)
    actor.load_state_dict(state, strict=True)
    actor.eval()
    return actor


def _evaluate_one(actor: MatchedRoutedActor, arm: str, row: Mapping[str, Any]) -> dict[str, Any]:
    s_value, old_value, new_value = int(row["s"]), int(row["n_old"]), int(row["n_new"])
    s, n_old, n_new = _bit_tensor([s_value]), _bit_tensor([old_value]), _bit_tensor([new_value])
    owner, obsolete = actor.pre_event(s, n_old)
    partner = actor.partner_write(n_new)
    effective_obsolete = torch.zeros_like(obsolete) if row["regime"] == "CLEAN" else obsolete
    host = PartnerWriterStaleLoadHost(root=int(row["root"]), regime=str(row["regime"]), dimensions=HostDimensions())
    t1 = host.transition_one(owner_state=owner[0], obsolete_partner_state=effective_obsolete[0])
    witness = host.apply_replacement(host.replacement_transaction())
    dto = PartnerWriteDTO.make(writer_call_identity=f"R/{arm}/{row['master_seed']}/{row['episode']}", source_bit=new_value, payload=partner[0])
    t2 = host.transition_two(dto)
    routed = actor.routed_state(arm=arm, owner_state=owner, obsolete_state=effective_obsolete, partner_state=partner)
    logits = actor.action_head(routed)
    probabilities = torch.softmax(logits, dim=-1)
    action = int(_sample_actions(probabilities, [row["action_uniform"]])[0])
    target = 2 * s_value + new_value
    terminal = host.terminal_transition(action=action, target=target, action_count=4)
    _, flipped_obsolete = actor.pre_event(s, _bit_tensor([1 - old_value]))
    if row["regime"] == "CLEAN":
        flipped_obsolete = torch.zeros_like(flipped_obsolete)
    flipped_old = actor.action_head(actor.routed_state(arm=arm, owner_state=owner, obsolete_state=flipped_obsolete, partner_state=partner))
    old_tv = 0.5 * float(torch.abs(probabilities - torch.softmax(flipped_old, dim=-1)).sum())
    flipped_owner, _ = actor.pre_event(_bit_tensor([1 - s_value]), n_old)
    flipped_s = actor.action_head(actor.routed_state(arm=arm, owner_state=flipped_owner, obsolete_state=effective_obsolete, partner_state=partner))
    s_tv = 0.5 * float(torch.abs(probabilities - torch.softmax(flipped_s, dim=-1)).sum())
    flipped_s_invalid = actor.action_head(actor.routed_state(arm=arm, owner_state=flipped_owner, obsolete_state=effective_obsolete, partner_state=partner, owner_epoch_valid=False))
    invalid_owner_logits = actor.action_head(actor.routed_state(arm=arm, owner_state=owner, obsolete_state=effective_obsolete, partner_state=partner, owner_epoch_valid=False))
    owner_key_tv = 0.5 * float(torch.abs(torch.softmax(flipped_s_invalid, dim=-1) - torch.softmax(invalid_owner_logits, dim=-1)).sum())
    return {
        **row,
        "arm": arm,
        "target": target,
        "action": action,
        "reward": terminal["reward"],
        "decoded_s": action // 2,
        "decoded_n_new": action % 2,
        "transition_one": t1,
        "replacement": asdict(witness),
        "transition_two": t2,
        "terminal": terminal,
        "kernel": _kernel_payload(logits),
        "do_n_old_flip_kernel": _kernel_payload(flipped_old),
        "do_n_old_flip_tv": old_tv,
        "do_s_flip_kernel": _kernel_payload(flipped_s),
        "do_s_flip_tv": s_tv,
        "owner_epoch_key_intervention_s_flip_tv": owner_key_tv,
        "owner_invalid_kernel": _kernel_payload(invalid_owner_logits),
        "owner_invalid_s_flip_kernel": _kernel_payload(flipped_s_invalid),
    }


def evaluate(*, output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root).resolve()
    if (root / "evaluation_summary.json").exists() or (root / "phase_r_evaluation.jsonl.gz").exists():
        raise FileExistsError("evaluation stage is write-once")
    train_summary = validate_train(root, require_full=None)
    if not train_summary["phase_r_ran"]:
        summary = {
            "schema_version": SCHEMA_VERSION,
            "artifact_kind": "FOLR_B3_EVALUATION_SUMMARY",
            "technical_only": train_summary["technical_only"],
            "source_commit": train_summary["source_commit"],
            "run_id": train_summary["run_id"],
            "stage": "EVALUATION_SKIPPED",
            "contract_evidence": train_summary["contract_evidence"],
            "phase_r_ran": False,
            "arm_runs": [],
            "activity_counts": train_summary["activity_counts"],
            "train_summary_binding": _file_binding(root / "train_summary.json"),
        }
        _write_json(root / "evaluation_summary.json", summary)
        validate_evaluation(root, require_full=None)
        return summary
    manifest = _read_json(root / "manifest.json")
    config = _config_from_json(manifest["config"])
    sidecar = root / "phase_r_evaluation.jsonl.gz"
    arm_runs = []
    row_count = 0
    with _GzipJsonlWriter(sidecar) as writer:
        for arm in ARMS:
            for seed in config.master_seeds:
                checkpoint = _load_checkpoint(_checkpoint_path(root, "R", seed, arm))
                actor = _actor_from_checkpoint(checkpoint)
                by_regime: dict[str, list[dict[str, Any]]] = {name: [] for name in REGIMES}
                for row in manifest["phase_r"][str(seed)][arm]["evaluate"]:
                    result = _evaluate_one(actor, arm, row)
                    writer.write(result)
                    by_regime[result["regime"]].append(result)
                    row_count += 1
                for regime in REGIMES:
                    arm_runs.append(_metric_row(arm, seed, regime, by_regime[regime]))
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B3_EVALUATION_SUMMARY",
        "technical_only": train_summary["technical_only"],
        "source_commit": train_summary["source_commit"],
        "run_id": train_summary["run_id"],
        "stage": "EVALUATION_COMPLETE",
        "contract_evidence": train_summary["contract_evidence"],
        "phase_r_ran": True,
        "arm_runs": arm_runs,
        "activity_counts": train_summary["activity_counts"],
        "train_summary_binding": _file_binding(root / "train_summary.json"),
        "phase_r_sidecar": _file_binding(sidecar, rows=row_count),
    }
    _write_json(root / "evaluation_summary.json", summary)
    validate_evaluation(root, require_full=None)
    return summary


def _metric_row(arm: str, seed: int, regime: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "arm": arm,
        "master_seed": seed,
        "regime": regime,
        "episodes": len(rows),
        "J": sum(float(row["reward"]) for row in rows) / len(rows),
        "survivor_accuracy": sum(int(row["decoded_s"] == row["s"]) for row in rows) / len(rows),
        "partner_accuracy": sum(int(row["decoded_n_new"] == row["n_new"]) for row in rows) / len(rows),
        "I_n_old": sum(float(row["do_n_old_flip_tv"]) for row in rows) / len(rows),
        "n_old_kernel_byte_exact": all(row["kernel"]["probabilities_base64"] == row["do_n_old_flip_kernel"]["probabilities_base64"] for row in rows),
        "s_kernel_byte_exact": all(row["kernel"]["probabilities_base64"] == row["do_s_flip_kernel"]["probabilities_base64"] for row in rows),
        "owner_epoch_key_intervention_removes_old_s": all(float(row["owner_epoch_key_intervention_s_flip_tv"]) == 0.0 for row in rows),
    }


def _aggregate_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for arm in ARMS:
        result[arm] = {}
        for regime in REGIMES:
            selected = [row for row in rows if row["arm"] == arm and row["regime"] == regime]
            result[arm][regime] = {
                "J": sum(row["J"] for row in selected) / len(selected),
                "survivor_accuracy": sum(row["survivor_accuracy"] for row in selected) / len(selected),
                "partner_accuracy": sum(row["partner_accuracy"] for row in selected) / len(selected),
                "I_n_old": sum(row["I_n_old"] for row in selected) / len(selected),
                "n_old_kernel_byte_exact": all(row["n_old_kernel_byte_exact"] for row in selected),
                "s_kernel_byte_exact": all(row["s_kernel_byte_exact"] for row in selected),
                "owner_epoch_key_intervention_removes_old_s": all(row["owner_epoch_key_intervention_removes_old_s"] for row in selected),
                "seeds": selected,
            }
    for arm in ARMS:
        result[arm]["D"] = result[arm]["CLEAN"]["J"] - result[arm]["STALE_LOAD"]["J"]
    result["Psi"] = result[ISOMORPHIC_GENERIC_UPDATE]["D"] - result[TYPED_OWNER_EPOCH_ROUTING]["D"]
    result["seedwise_Psi"] = [
        next(row for row in rows if row["arm"] == ISOMORPHIC_GENERIC_UPDATE and row["regime"] == "CLEAN" and row["master_seed"] == seed)["J"]
        - next(row for row in rows if row["arm"] == ISOMORPHIC_GENERIC_UPDATE and row["regime"] == "STALE_LOAD" and row["master_seed"] == seed)["J"]
        - next(row for row in rows if row["arm"] == TYPED_OWNER_EPOCH_ROUTING and row["regime"] == "CLEAN" and row["master_seed"] == seed)["J"]
        + next(row for row in rows if row["arm"] == TYPED_OWNER_EPOCH_ROUTING and row["regime"] == "STALE_LOAD" and row["master_seed"] == seed)["J"]
        for seed in sorted({int(row["master_seed"]) for row in rows})
    ]
    return result


def _strong(metric: Mapping[str, Any]) -> bool:
    return metric["J"] >= 0.80 and metric["survivor_accuracy"] >= 0.90 and metric["partner_accuracy"] >= 0.90 and sum(row["J"] >= 0.75 for row in metric["seeds"]) >= 7


def _decision(*, valid: bool, calibration_passed: bool, metrics: Mapping[str, Any] | None, contract_evidence: Mapping[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    if not valid:
        if contract_evidence is None or contract_evidence.get("valid") is not False or not contract_evidence.get("first_failure_id"):
            raise ValueError("invalid-contract branch requires structured contract evidence")
        return BRANCHES[0], {"first_failure": "contract", "first_failure_id": contract_evidence["first_failure_id"], "contract_predicates": contract_evidence["predicates"]}
    if not calibration_passed:
        return BRANCHES[1], {"first_failure": "phase_p_calibration"}
    assert metrics is not None
    reset_clean, reset_stale = metrics[COMPLETE_RESET]["CLEAN"], metrics[COMPLETE_RESET]["STALE_LOAD"]
    reset_ok = all(
        metric["partner_accuracy"] >= 0.95
        and 0.47 <= metric["survivor_accuracy"] <= 0.53
        and metric["s_kernel_byte_exact"]
        and abs(metric["J"] - 0.5 * metric["partner_accuracy"]) <= 0.02
        for metric in (reset_clean, reset_stale)
    )
    typed_clean, generic_clean = metrics[TYPED_OWNER_EPOCH_ROUTING]["CLEAN"], metrics[ISOMORPHIC_GENERIC_UPDATE]["CLEAN"]
    clean_ok = _strong(typed_clean) and _strong(generic_clean) and abs(typed_clean["J"] - generic_clean["J"]) <= 0.05
    if not reset_ok or not clean_ok:
        return BRANCHES[2], {"reset_ok": reset_ok, "clean_ok": clean_ok}
    typed_stale = metrics[TYPED_OWNER_EPOCH_ROUTING]["STALE_LOAD"]
    typed_ok = _strong(typed_stale) and metrics[TYPED_OWNER_EPOCH_ROUTING]["D"] <= 0.03 and typed_stale["n_old_kernel_byte_exact"] and typed_stale["owner_epoch_key_intervention_removes_old_s"]
    if not typed_ok:
        return BRANCHES[3], {"typed_ok": False}
    generic_stale = metrics[ISOMORPHIC_GENERIC_UPDATE]["STALE_LOAD"]
    psi = metrics["Psi"]
    generic_sufficient = _strong(generic_stale) and abs(psi) <= 0.05 and generic_stale["I_n_old"] < 0.05
    if generic_sufficient:
        return BRANCHES[4], {"generic_sufficient": True}
    typed_value = psi >= 0.10 and sum(value >= 0.05 for value in metrics["seedwise_Psi"]) >= 7 and typed_stale["I_n_old"] == 0.0 and generic_stale["I_n_old"] >= 0.05
    if typed_value:
        return BRANCHES[5], {"typed_value": True}
    return BRANCHES[6], {"valid_other_pattern": True}


def analyze(*, output_root: str | Path, result_path: str | Path | None = None) -> dict[str, Any]:
    root = Path(output_root).resolve()
    canonical_result = root / "result.json"
    if canonical_result.exists():
        raise FileExistsError("analysis stage is write-once")
    destination = Path(result_path).resolve() if result_path is not None else None
    if destination is not None and destination.exists():
        raise FileExistsError("external result destination is write-once")
    evaluation = validate_evaluation(root, require_full=None)
    train_summary = _read_json(root / "train_summary.json")
    technical = bool(train_summary["technical_only"])
    metrics = _aggregate_metrics(evaluation["arm_runs"]) if evaluation["phase_r_ran"] else None
    contract_evidence = train_summary["contract_evidence"]
    decision, gates = _decision(valid=bool(contract_evidence["valid"]), calibration_passed=train_summary["phase_p_evaluation"]["calibration_passed"], metrics=metrics, contract_evidence=contract_evidence)
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B3_RESULT",
        "source_commit": train_summary["source_commit"],
        "run_id": train_summary["run_id"],
        "technical_only": technical,
        "stage": "ANALYSIS_COMPLETE",
        "contract_evidence": contract_evidence,
        "scientific_terminal_admitted": not technical,
        "decision": TECHNICAL_DECISION if technical else decision,
        "unique_frozen_branch": None if technical else decision,
        "phase_p_calibration": train_summary["phase_p_evaluation"],
        "phase_r_ran": evaluation["phase_r_ran"],
        "metrics": metrics,
        "decision_gates": gates,
        "activity_counts": train_summary["activity_counts"],
        "bindings": {
            "manifest": _file_binding(root / "manifest.json"),
            "train_summary": _file_binding(root / "train_summary.json"),
            "evaluation_summary": _file_binding(root / "evaluation_summary.json"),
        },
        "claim_boundary": "host-local finite-budget typed-routing value only; no promotion, retirement, C, formal, or successor",
    }
    _write_json(canonical_result, result)
    validate_result(canonical_result, output_root=root, require_full=not technical)
    if destination is not None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with canonical_result.open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target)
        validate_result(destination, output_root=root, require_full=not technical)
    return result


def _config_from_json(value: Mapping[str, Any]) -> ExperimentConfig:
    return ExperimentConfig(
        master_seeds=tuple(int(seed) for seed in value["master_seeds"]),
        p_train_batches=int(value["p_train_batches"]),
        p_train_batch_size=int(value["p_train_batch_size"]),
        p_eval_episodes=int(value["p_eval_episodes"]),
        r_train_batches=int(value["r_train_batches"]),
        r_train_batch_size=int(value["r_train_batch_size"]),
        r_eval_episodes_per_regime=int(value["r_eval_episodes_per_regime"]),
        learning_rate=float(value["learning_rate"]),
        technical_only=bool(value["technical_only"]),
    )


def _validate_manifest(manifest: Mapping[str, Any], config: ExperimentConfig) -> None:
    if manifest["config"] != config.to_json() or tuple(manifest["arms"]) != ARMS or tuple(manifest["regimes"]) != REGIMES:
        raise ValueError("manifest frozen literals drifted")
    if not isinstance(manifest["owner_binding"], str) or not isinstance(manifest["partner_replacement"], str):
        raise ValueError("manifest lifecycle binding evidence is malformed")
    if not isinstance(manifest["architecture"]["generic_class_nesting"]["constructive_containment"], bool):
        raise ValueError("generic-class nesting evidence is malformed")
    if not manifest["run_id"] or len(manifest["source_commit"]) != 40:
        raise ValueError("manifest source/run identity is malformed")
    for seed in config.master_seeds:
        p_train = manifest["phase_p"][str(seed)]["train"]
        p_eval = manifest["phase_p"][str(seed)]["evaluate"]
        if len(p_train) != config.p_train_batches * config.p_train_batch_size or len(p_eval) != config.p_eval_episodes:
            raise ValueError("phase-P manifest count drifted")
        for arm in ARMS:
            r_train = manifest["phase_r"][str(seed)][arm]["train"]
            r_eval = manifest["phase_r"][str(seed)][arm]["evaluate"]
            if len(r_train) != config.r_train_batches * config.r_train_batch_size or len(r_eval) != len(REGIMES) * config.r_eval_episodes_per_regime:
                raise ValueError("phase-R manifest count drifted")
            if any(f"R/{arm}/" not in row["rng_identity"]["namespace"] for row in r_train + r_eval):
                raise ValueError("phase-R RNG namespace is not arm-isolated")
            for phase, rows in (("train", r_train), ("evaluate", r_eval)):
                for row in rows:
                    if int(row["root"]) != _root(seed, f"R/{arm}/{phase}", int(row["episode"])):
                        raise ValueError("phase-R root namespace drifted")
            for batch in range(config.r_train_batches):
                rows = [row for row in r_train if row["batch"] == batch]
                if sum(row["regime"] == "CLEAN" for row in rows) != config.r_train_batch_size // 2 or sum(row["regime"] == "STALE_LOAD" for row in rows) != config.r_train_batch_size // 2:
                    raise ValueError("phase-R CLEAN/STALE_LOAD batch balance drifted")
    if not config.technical_only:
        counts = _expected_counts(config, phase_r_ran=True)
        expected = {"training_episodes": 65536, "evaluation_episodes": 28672, "complete_episodes": 94208, "environment_transitions": 282624, "policy_calls": 282624, "learner_calls": 1024, "trainer_calls": 1024, "optimizer_updates": 1024}
        if any(counts[key] != value for key, value in expected.items()):
            raise ValueError("registered activity identity drifted")


def _validate_mode(config: ExperimentConfig, require_full: bool | None) -> None:
    if require_full is True and config != registered_config():
        raise ValueError("artifact is not the registered full configuration")
    if require_full is False and config != technical_smoke_config():
        raise ValueError("artifact is not the technical-only configuration")


def validate_train(output_root: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root).resolve()
    manifest = _read_json(root / "manifest.json")
    config = _config_from_json(manifest["config"])
    _validate_mode(config, require_full)
    _validate_manifest(manifest, config)
    summary = _read_json(root / "train_summary.json")
    contract_evidence = _contract_evidence(manifest, config)
    if summary["artifact_kind"] != "FOLR_B3_TRAIN_SUMMARY" or summary["technical_only"] != config.technical_only:
        raise ValueError("train summary identity drifted")
    if summary["source_commit"] != manifest["source_commit"] or summary["run_id"] != manifest["run_id"] or summary["contract_evidence"] != contract_evidence:
        raise ValueError("train source/run/contract identity drifted")
    expected_stage = "TRAIN_COMPLETE" if contract_evidence["valid"] else "INVALID_CONTRACT_STOP"
    if summary["stage"] != expected_stage:
        raise ValueError("train phase identity drifted")
    if summary["manifest_binding"]["sha256"] != _sha256_file(root / "manifest.json"):
        raise ValueError("train summary manifest binding drifted")
    phase_r_ran = bool(summary["phase_r_ran"])
    if phase_r_ran != bool(contract_evidence["valid"] and summary["phase_p_evaluation"]["calibration_passed"]):
        raise ValueError("phase-R execution did not follow the phase-P gate")
    if summary["activity_counts"] != _expected_counts(config, phase_r_ran=phase_r_ran, contract_valid=contract_evidence["valid"]):
        raise ValueError("train activity identity drifted")
    actual_checkpoints = {
        path.relative_to(root).as_posix()
        for path in (root / "checkpoints").rglob("*") if (root / "checkpoints").exists()
        if path.is_file()
    }
    if not contract_evidence["valid"]:
        if summary["phase_p_train"] or summary["phase_r_train"] or summary["phase_p_evaluation"] != _phase_p_not_run() or actual_checkpoints:
            raise ValueError("invalid-contract stop retained result-bearing artifacts")
        if (root / "phase_p_evaluation.jsonl.gz").exists() or (root / "phase_r_evaluation.jsonl.gz").exists():
            raise ValueError("invalid-contract stop retained an evaluation sidecar")
        return summary
    p_sidecar = root / "phase_p_evaluation.jsonl.gz"
    p_rows = list(_read_jsonl_gz(p_sidecar))
    if len(p_rows) != len(config.master_seeds) * config.p_eval_episodes or summary["phase_p_evaluation"]["sidecar"]["sha256"] != _sha256_file(p_sidecar):
        raise ValueError("phase-P evaluation sidecar drifted")
    expected_p_rows = [row for seed in config.master_seeds for row in manifest["phase_p"][str(seed)]["evaluate"]]
    if [_manifest_projection(row, phase_r=False) for row in p_rows] != [_manifest_projection(row, phase_r=False) for row in expected_p_rows]:
        raise ValueError("phase-P retained rows differ from the frozen manifest")
    reconstructed_phase_p = _summarize_phase_p_rows(p_rows)
    reconstructed_phase_p["sidecar"] = _file_binding(p_sidecar, rows=len(p_rows))
    if summary["phase_p_evaluation"] != reconstructed_phase_p:
        raise ValueError("phase-P calibration does not reconstruct from the retained sidecar")
    for row in p_rows:
        _validate_kernel(row["kernel"])
        _validate_kernel(row["n_new_flip_kernel"])
        probabilities = torch.tensor(row["kernel"]["probabilities"], dtype=torch.float32)
        expected_action = int(_sample_actions(probabilities, [row["action_uniform"]])[0])
        expected_tv = _payload_tv(row["kernel"], row["n_new_flip_kernel"])
        if row["action"] != expected_action or row["reward"] != float(expected_action == row["n_new"]) or not math.isclose(row["n_new_flip_tv"], expected_tv, rel_tol=0.0, abs_tol=1e-7):
            raise ValueError("phase-P action, reward, or intervention does not reconstruct")
        _validate_lifecycle_witness(row, writer_call_identity=f"P/{row['master_seed']}/{row['episode']}")
        terminal = row["terminal"]
        if terminal["transition"] != 3 or terminal["action"] != row["action"] or terminal["target"] != row["n_new"] or terminal["reward"] != row["reward"] or terminal["all_memory_cleared"] is not True:
            raise ValueError("phase-P terminal lifecycle witness drifted")
    phase_p_states: dict[int, Mapping[str, torch.Tensor]] = {}
    expected_checkpoints = set()
    if len(summary["phase_p_train"]) != len(config.master_seeds):
        raise ValueError("phase-P actor-run census drifted")
    for seed in config.master_seeds:
        path = _checkpoint_path(root, "P", seed)
        expected_checkpoints.add(path.relative_to(root).as_posix())
        checkpoint = _load_checkpoint(path)
        if checkpoint["phase"] != "P" or checkpoint["master_seed"] != seed or checkpoint["final_only"] is not True:
            raise ValueError("phase-P checkpoint identity drifted")
        actual_digest = _state_digest(checkpoint["writer_state"])
        if checkpoint["writer_state_digest"] != actual_digest:
            raise ValueError("phase-P final checkpoint drifted")
        p_summary = next(row for row in summary["phase_p_train"] if row["master_seed"] == seed)
        if p_summary["checkpoint"] != path.relative_to(root).as_posix() or p_summary["writer_state_digest"] != actual_digest or len(p_summary["batches"]) != config.p_train_batches:
            raise ValueError("phase-P train summary differs from final checkpoint")
        phase_p_states[seed] = checkpoint["writer_state"]
    if phase_r_ran:
        if len(summary["phase_r_train"]) != len(ARMS) * len(config.master_seeds):
            raise ValueError("phase-R actor-run count drifted")
        for seed in config.master_seeds:
            schemas = []
            for arm in ARMS:
                path = _checkpoint_path(root, "R", seed, arm)
                expected_checkpoints.add(path.relative_to(root).as_posix())
                checkpoint = _load_checkpoint(path)
                if checkpoint["phase"] != "R" or checkpoint["arm"] != arm or checkpoint["master_seed"] != seed or checkpoint["final_only"] is not True:
                    raise ValueError("phase-R checkpoint identity drifted")
                actor = _actor_from_checkpoint(checkpoint)
                schemas.append(actor.trainable_schema())
                actual_writer_state = {
                    name.removeprefix("partner_writer."): value
                    for name, value in checkpoint["actor_state"].items()
                    if name.startswith("partner_writer.")
                }
                if set(actual_writer_state) != set(phase_p_states[seed]) or any(not torch.equal(actual_writer_state[name], phase_p_states[seed][name]) for name in actual_writer_state):
                    raise ValueError("phase-R checkpoint writer tensors differ from phase-P final writer")
                actual_writer_digest = _state_digest(actual_writer_state)
                if checkpoint["frozen_writer_state_digest"] != actual_writer_digest:
                    raise ValueError("phase-R writer digest metadata differs from actual tensors")
                rederived_nesting = generic_class_nesting_witness(actor)
                if checkpoint["generic_class_nesting"] != rederived_nesting or not rederived_nesting["constructive_containment"]:
                    raise ValueError("phase-R checkpoint contract drifted")
                run_summary = next(row for row in summary["phase_r_train"] if row["arm"] == arm and row["master_seed"] == seed)
                if run_summary["generic_class_nesting"] != rederived_nesting or run_summary["frozen_writer_state_digest"] != actual_writer_digest or run_summary["checkpoint"] != path.relative_to(root).as_posix():
                    raise ValueError("phase-R train summary differs from final checkpoint")
            if not all(schema == schemas[0] for schema in schemas):
                raise ValueError("phase-R frozen writer/schema matching drifted")
    else:
        if summary["phase_r_train"] or (root / "phase_r_evaluation.jsonl.gz").exists():
            raise ValueError("natural calibration stop retained phase-R activity")
        phase_r_root = root / "checkpoints" / "phase_r"
        if phase_r_root.exists() and any(path.is_file() for path in phase_r_root.rglob("*")):
            raise ValueError("natural calibration stop retained phase-R checkpoints")
    if actual_checkpoints != expected_checkpoints:
        raise ValueError("final-only checkpoint census drifted")
    return summary


def validate_evaluation(output_root: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root).resolve()
    train_summary = validate_train(root, require_full=require_full)
    summary = _read_json(root / "evaluation_summary.json")
    if summary["artifact_kind"] != "FOLR_B3_EVALUATION_SUMMARY" or bool(summary["phase_r_ran"]) != bool(train_summary["phase_r_ran"]):
        raise ValueError("evaluation phase identity drifted")
    expected_stage = "EVALUATION_COMPLETE" if train_summary["phase_r_ran"] else "EVALUATION_SKIPPED"
    if summary["source_commit"] != train_summary["source_commit"] or summary["run_id"] != train_summary["run_id"] or summary["stage"] != expected_stage or summary["contract_evidence"] != train_summary["contract_evidence"] or summary["activity_counts"] != train_summary["activity_counts"]:
        raise ValueError("evaluation source/run/stage identity drifted")
    if summary["train_summary_binding"]["sha256"] != _sha256_file(root / "train_summary.json"):
        raise ValueError("evaluation train binding drifted")
    if not summary["phase_r_ran"]:
        if summary["arm_runs"] or (root / "phase_r_evaluation.jsonl.gz").exists() or "phase_r_sidecar" in summary:
            raise ValueError("phase-R rows exist after calibration stop")
        return summary
    manifest = _read_json(root / "manifest.json")
    config = _config_from_json(manifest["config"])
    sidecar = root / "phase_r_evaluation.jsonl.gz"
    rows = list(_read_jsonl_gz(sidecar))
    expected = len(ARMS) * len(config.master_seeds) * len(REGIMES) * config.r_eval_episodes_per_regime
    if len(rows) != expected or summary["phase_r_sidecar"]["sha256"] != _sha256_file(sidecar):
        raise ValueError("phase-R evaluation sidecar drifted")
    expected_rows = [
        {**row, "arm": arm}
        for arm in ARMS
        for seed in config.master_seeds
        for row in manifest["phase_r"][str(seed)][arm]["evaluate"]
    ]
    if [dict(_manifest_projection(row, phase_r=True), arm=row["arm"]) for row in rows] != [dict(_manifest_projection(row, phase_r=True), arm=row["arm"]) for row in expected_rows]:
        raise ValueError("phase-R retained rows differ from the frozen manifest")
    recomputed = []
    for arm in ARMS:
        for seed in config.master_seeds:
            for regime in REGIMES:
                selected = [row for row in rows if row["arm"] == arm and row["master_seed"] == seed and row["regime"] == regime]
                for row in selected:
                    _validate_kernel(row["kernel"])
                    _validate_kernel(row["do_n_old_flip_kernel"])
                    _validate_kernel(row["do_s_flip_kernel"])
                    _validate_kernel(row["owner_invalid_kernel"])
                    _validate_kernel(row["owner_invalid_s_flip_kernel"])
                    probabilities = torch.tensor(row["kernel"]["probabilities"], dtype=torch.float32)
                    expected_action = int(_sample_actions(probabilities, [row["action_uniform"]])[0])
                    expected_target = 2 * int(row["s"]) + int(row["n_new"])
                    if (
                        row["action"] != expected_action
                        or row["target"] != expected_target
                        or row["reward"] != float(expected_action == expected_target)
                        or row["decoded_s"] != expected_action // 2
                        or row["decoded_n_new"] != expected_action % 2
                        or not math.isclose(row["do_n_old_flip_tv"], _payload_tv(row["kernel"], row["do_n_old_flip_kernel"]), rel_tol=0.0, abs_tol=1e-7)
                        or not math.isclose(row["do_s_flip_tv"], _payload_tv(row["kernel"], row["do_s_flip_kernel"]), rel_tol=0.0, abs_tol=1e-7)
                        or not math.isclose(row["owner_epoch_key_intervention_s_flip_tv"], _payload_tv(row["owner_invalid_kernel"], row["owner_invalid_s_flip_kernel"]), rel_tol=0.0, abs_tol=1e-7)
                    ):
                        raise ValueError("phase-R action, reward, decode, or intervention does not reconstruct")
                    if row["replacement"]["owner_epoch_preserved"] is not True or row["terminal"]["all_memory_cleared"] is not True:
                        raise ValueError("episode lifecycle witness drifted")
                    _validate_lifecycle_witness(row, writer_call_identity=f"R/{arm}/{seed}/{row['episode']}")
                    terminal = row["terminal"]
                    if terminal["transition"] != 3 or terminal["action"] != row["action"] or terminal["target"] != row["target"] or terminal["reward"] != row["reward"] or terminal["all_memory_cleared"] is not True:
                        raise ValueError("retained terminal lifecycle witness drifted")
                recomputed.append(_metric_row(arm, seed, regime, selected))
    if recomputed != summary["arm_runs"]:
        raise ValueError("evaluation metrics do not reconstruct from lossless kernels")
    return summary


def _validate_kernel(payload: Mapping[str, Any]) -> None:
    logits = np.asarray(payload["logits"], dtype=np.float32)
    probabilities = np.asarray(payload["probabilities"], dtype=np.float32)
    if not np.isfinite(logits).all() or not np.isfinite(probabilities).all() or not np.allclose(probabilities.sum(axis=-1), 1.0, atol=1e-6):
        raise ValueError("kernel is malformed")
    if base64.b64encode(logits.tobytes(order="C")).decode("ascii") != payload["logits_base64"] or base64.b64encode(probabilities.tobytes(order="C")).decode("ascii") != payload["probabilities_base64"]:
        raise ValueError("kernel byte view drifted")
    shifted = logits - logits.max(axis=-1, keepdims=True)
    reconstructed = np.exp(shifted) / np.exp(shifted).sum(axis=-1, keepdims=True)
    if not np.allclose(reconstructed.astype(np.float32), probabilities, rtol=0.0, atol=1e-7):
        raise ValueError("kernel probabilities do not reconstruct from logits")


def _payload_tv(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    a = np.asarray(left["probabilities"], dtype=np.float32)
    b = np.asarray(right["probabilities"], dtype=np.float32)
    return 0.5 * float(np.abs(a - b).sum())


def validate_result(result_path: str | Path, *, output_root: str | Path, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root).resolve()
    evaluation = validate_evaluation(root, require_full=require_full)
    train_summary = _read_json(root / "train_summary.json")
    result = _read_json(Path(result_path).resolve())
    if result["artifact_kind"] != "FOLR_B3_RESULT" or result["activity_counts"] != train_summary["activity_counts"]:
        raise ValueError("result identity or activity counts drifted")
    if result["source_commit"] != train_summary["source_commit"] or result["run_id"] != train_summary["run_id"] or result["stage"] != "ANALYSIS_COMPLETE" or result["contract_evidence"] != train_summary["contract_evidence"] or result["phase_r_ran"] != evaluation["phase_r_ran"] or result["phase_p_calibration"] != train_summary["phase_p_evaluation"]:
        raise ValueError("result source/run/stage identity drifted")
    expected_metrics = _aggregate_metrics(evaluation["arm_runs"]) if evaluation["phase_r_ran"] else None
    contract_evidence = train_summary["contract_evidence"]
    decision, gates = _decision(valid=bool(contract_evidence["valid"]), calibration_passed=train_summary["phase_p_evaluation"]["calibration_passed"], metrics=expected_metrics, contract_evidence=contract_evidence)
    technical = bool(train_summary["technical_only"])
    if result["metrics"] != expected_metrics or result["decision_gates"] != gates:
        raise ValueError("result does not reconstruct from retained evidence")
    if technical:
        if result["decision"] != TECHNICAL_DECISION or result["unique_frozen_branch"] is not None or result["scientific_terminal_admitted"]:
            raise ValueError("technical result admitted a scientific branch")
    elif result["decision"] != decision or result["unique_frozen_branch"] != decision or not result["scientific_terminal_admitted"]:
        raise ValueError("registered result branch drifted")
    for name, filename in (("manifest", "manifest.json"), ("train_summary", "train_summary.json"), ("evaluation_summary", "evaluation_summary.json")):
        if result["bindings"][name]["sha256"] != _sha256_file(root / filename):
            raise ValueError(f"result {name} binding drifted")
    return result


def summarize_artifacts(output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root).resolve()
    value = {"train": validate_train(root, require_full=None)}
    if (root / "evaluation_summary.json").exists():
        value["evaluation"] = validate_evaluation(root, require_full=None)
    if (root / "result.json").exists():
        value["result"] = validate_result(root / "result.json", output_root=root, require_full=None)
    return value
