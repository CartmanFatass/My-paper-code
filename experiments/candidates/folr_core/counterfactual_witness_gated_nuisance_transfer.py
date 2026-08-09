"""Frozen train/evaluate/analyze package for FOLR-B2.

This module has no formal-run authority.  Its only non-full mode is an
explicitly technical smoke that can never admit a scientific decision.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import math
import os
import re
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
import torch
from torch import nn

from experiments.candidates.folr_core.counterfactual_witness_gated_nuisance_transfer_host import (
    ARMS,
    COMPLETE_RESET,
    HOST_IDENTIFIER,
    ISOMORPHIC_GENERIC_MEMORY,
    OWNER_EPOCH,
    OWNER_KEY,
    TYPED_WITNESS_S03_S04,
    CounterfactualWitnessHost,
    HostDimensions,
    StateProvenance,
    derive_counterfactual_lineage,
)


RAW_OUTPUT_BINDING = "folr_core.counterfactual_witness_gated_nuisance_transfer.v1"
SCHEMA_VERSION = 1
MASTER_SEEDS = tuple(range(94031, 94039))
REGIMES = ("DIAGONAL", "CHANGED")
PARTNER_KEYS = ("partner_a", "partner_b", "partner_c", "partner_d")
PARTNER_ROLES = ("SCOUT", "RELAY")
DECISIONS = (
    "B2_INVALID",
    "RESET_LEAK_OR_NEW_PARTNER_CALIBRATION_FAILED",
    "GENERIC_CAPACITY_CONTROL_FAILED",
    "TYPED_ROUTE_FAILED_ON_SUPPORT",
    "HOST_LOCAL_TYPED_FILTER_VALUE_SUPPORTED",
    "GENERIC_MEMORY_SUFFICIENT_AT_CAP",
    "GENERIC_OUTGENERALIZES_TYPED",
    "OOD_LEARNABILITY_UNRESOLVED_AT_CAP",
    "INDETERMINATE_AT_CAP",
)
TECHNICAL_DECISION = "TECHNICAL_ONLY_NO_SCIENTIFIC_DECISION"
EXCLUSIONS = {
    "b1_weight_state_or_checkpoint_reuse": False,
    "critic": False,
    "recurrence_outside_memory_interface": False,
    "attention": False,
    "replay_or_history_stack": False,
    "cached_action_kernel_or_logits": False,
    "pending_action": False,
    "update_between_event_and_choice": False,
    "checkpoint_selection": False,
    "preliminary_scientific_run": False,
    "retry_rescue_sweep": False,
    "extra_seed_composition_or_arm": False,
    "hypothetical_environment_transition": False,
}


@dataclass(frozen=True)
class ExperimentConfig:
    host_identifier: str
    arms: tuple[str, ...]
    master_seeds: tuple[int, ...]
    regimes: tuple[str, ...]
    memory_dim: int
    s03_dim: int
    s04_dim: int
    reader_hidden_dim: int
    descriptor_dim: int
    batches: int
    batch_size: int
    train_examples_per_cell: int
    eval_episodes_per_regime: int
    eval_examples_per_cell: int
    learning_rate: float
    entropy_coefficient: float
    gamma: float
    baseline: str
    optimizer: str
    updates_per_batch: int
    transitions_per_episode: int
    policy_calls_per_episode: int
    k_search: int
    hypothetical_transitions: int
    technical_only: bool

    def to_json(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("arms", "master_seeds", "regimes"):
            value[key] = list(value[key])
        return value


def registered_config() -> ExperimentConfig:
    return ExperimentConfig(
        host_identifier=HOST_IDENTIFIER,
        arms=ARMS,
        master_seeds=MASTER_SEEDS,
        regimes=REGIMES,
        memory_dim=16,
        s03_dim=8,
        s04_dim=8,
        reader_hidden_dim=32,
        descriptor_dim=15,
        batches=32,
        batch_size=64,
        train_examples_per_cell=16,
        eval_episodes_per_regime=512,
        eval_examples_per_cell=128,
        learning_rate=0.003,
        entropy_coefficient=0.01,
        gamma=1.0,
        baseline="batch_mean_terminal_external_reward",
        optimizer="Adam",
        updates_per_batch=1,
        transitions_per_episode=3,
        policy_calls_per_episode=3,
        k_search=0,
        hypothetical_transitions=0,
        technical_only=False,
    )


def technical_smoke_config() -> ExperimentConfig:
    value = registered_config().to_json()
    value.update(
        {
            "arms": ARMS,
            "master_seeds": (MASTER_SEEDS[0],),
            "regimes": REGIMES,
            "batches": 1,
            "batch_size": 16,
            "train_examples_per_cell": 4,
            "eval_episodes_per_regime": 16,
            "eval_examples_per_cell": 4,
            "technical_only": True,
        }
    )
    return ExperimentConfig(**value)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(_canonical_bytes(value) + b"\n")
    os.replace(temporary, path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_binding(path: Path, *, rows: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "path": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }
    if rows is not None:
        value["rows"] = int(rows)
    return value


def _derive_seed(master_seed: int, stream: str) -> int:
    digest = hashlib.sha256(f"FOLR-B2|{int(master_seed)}|{stream}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _rng_identity(master_seed: int, stream: str) -> dict[str, Any]:
    return {
        "derivation": "sha256(FOLR-B2|master_seed|stream)[:8]-big-endian",
        "master_seed": int(master_seed),
        "stream": str(stream),
        "derived_seed": _derive_seed(master_seed, stream),
        "generator": "numpy.PCG64",
    }


def _state_digest(state: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("utf-8"))
        digest.update(tensor.numpy().tobytes(order="C"))
    return digest.hexdigest()


class MatchedWitnessActor(nn.Module):
    """Identical learned machinery instantiated freshly for every arm."""

    CALL_TRACE = (
        "t1:survivor_writer",
        "t1:partner_writer",
        "t1:wait_head",
        "event:event_update",
        "t2:partner_writer",
        "t2:event_update",
        "t2:wait_head",
        "t3:memory_reader",
        "t3:action_head",
    )

    def __init__(self, *, config: ExperimentConfig, initialization_seed: int) -> None:
        super().__init__()
        self.config = config
        self.survivor_writer = nn.Linear(2, config.s03_dim)
        self.partner_writer = nn.Linear(2, config.s04_dim)
        self.event_update = nn.Linear(
            config.memory_dim + config.memory_dim + config.descriptor_dim,
            config.memory_dim,
        )
        self.wait_head = nn.Linear(config.memory_dim, 1)
        self.memory_reader = nn.Linear(config.memory_dim, config.reader_hidden_dim)
        self.action_head = nn.Linear(config.reader_hidden_dim, 4)
        generator = torch.Generator(device="cpu")
        generator.manual_seed(int(initialization_seed) % (2**63 - 1))
        for module in (
            self.survivor_writer,
            self.partner_writer,
            self.event_update,
            self.wait_head,
            self.memory_reader,
            self.action_head,
        ):
            nn.init.xavier_uniform_(module.weight, generator=generator)
            nn.init.zeros_(module.bias)

    @staticmethod
    def _bits(bits: torch.Tensor) -> torch.Tensor:
        return torch.nn.functional.one_hot(bits.to(torch.int64), num_classes=2).to(torch.float32)

    def transition_one(self, s: torch.Tensor, n_old: torch.Tensor) -> tuple[torch.Tensor, ...]:
        survivor = torch.tanh(self.survivor_writer(self._bits(s)))
        partner = torch.tanh(self.partner_writer(self._bits(n_old)))
        initial = torch.cat((survivor, partner), dim=-1)
        wait = self.wait_head(initial)
        return survivor, partner, initial, wait

    def learned_update(
        self, memory: torch.Tensor, ordinary_write: torch.Tensor, descriptor: torch.Tensor
    ) -> torch.Tensor:
        return torch.tanh(self.event_update(torch.cat((memory, ordinary_write, descriptor), dim=-1)))

    def new_partner_write(self, n_new: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.partner_writer(self._bits(n_new)))

    def wait_policy(self, memory: torch.Tensor) -> torch.Tensor:
        return self.wait_head(memory)

    def choice_policy(self, memory: torch.Tensor) -> torch.Tensor:
        return self.action_head(torch.tanh(self.memory_reader(memory)))

    def parameter_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "shape": list(parameter.shape),
                "dtype": str(parameter.dtype),
                "numel": int(parameter.numel()),
            }
            for name, parameter in self.named_parameters()
        ]

    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())


def _identity_features(key: str) -> list[float]:
    return [float(key == candidate) for candidate in PARTNER_KEYS]


def _role_features(role: str) -> list[float]:
    return [float(role == candidate) for candidate in PARTNER_ROLES]


def _descriptor(row: Mapping[str, Any], *, phase: str) -> list[float]:
    if phase not in ("replacement", "post_event"):
        raise ValueError("unknown descriptor phase")
    value = (
        [1.0]
        + _identity_features(str(row["old_partner_key"]))
        + _identity_features(str(row["new_partner_key"]))
        + _role_features(str(row["old_partner_role"]))
        + _role_features(str(row["new_partner_role"]))
        + [float(phase == "replacement"), float(phase == "post_event")]
    )
    if len(value) != 15:
        raise RuntimeError("descriptor shape drift")
    return value


def _writer_provenance(row: Mapping[str, Any], *, state_kind: str) -> StateProvenance:
    if state_kind == "survivor_private":
        writer = "survivor_writer"
        source_partner = None
        dependencies: tuple[str, ...] = ()
        writer_descriptor = {
            "phase": "t1",
            "writer": writer,
            "state_scope": state_kind,
            "owner_lifecycle_key": OWNER_KEY,
            "owner_membership_epoch": OWNER_EPOCH,
            "source_partner_key": None,
            "partner_dependencies": [],
        }
    elif state_kind == "partner_scoped":
        writer = "partner_writer"
        source_partner = str(row["old_partner_key"])
        dependencies = (source_partner,)
        writer_descriptor = {
            "phase": "t1",
            "writer": writer,
            "state_scope": state_kind,
            "owner_lifecycle_key": OWNER_KEY,
            "owner_membership_epoch": OWNER_EPOCH,
            "source_partner_key": source_partner,
            "partner_dependencies": [source_partner],
            "source_partner_role": str(row["old_partner_role"]),
        }
    else:
        raise ValueError("unknown writer state scope")
    return StateProvenance(
        state_kind=state_kind,
        owner_lifecycle_key=OWNER_KEY,
        owner_membership_epoch=OWNER_EPOCH,
        source_partner_key=source_partner,
        partner_dependencies=dependencies,
        writer_call_identity=(
            f"t1:{writer}:{int(row['master_seed'])}:{int(row['episode'])}"
        ),
        descriptor_digest=hashlib.sha256(_canonical_bytes(writer_descriptor)).hexdigest(),
    )


def _ordinary_t1_writer_emissions(
    actor: MatchedWitnessActor,
    *,
    s: torch.Tensor,
    n_old: torch.Tensor,
    rows: Sequence[Mapping[str, Any]],
) -> tuple[
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    list[StateProvenance],
    list[StateProvenance],
]:
    """Emit learned candidates and immutable provenance in the same call boundary."""

    survivor, partner, initial, wait = actor.transition_one(s, n_old)
    if len(rows) != int(survivor.shape[0]):
        raise ValueError("writer emission/provenance cardinality mismatch")
    survivor_provenance = [
        _writer_provenance(row, state_kind="survivor_private") for row in rows
    ]
    partner_provenance = [
        _writer_provenance(row, state_kind="partner_scoped") for row in rows
    ]
    return (
        survivor,
        partner,
        initial,
        wait,
        survivor_provenance,
        partner_provenance,
    )


def _manifest_row(
    *,
    seed: int,
    phase: str,
    episode: int,
    batch: int | None,
    regime: str | None,
    pair_index: int | None,
    root: int,
    s: int,
    n_old: int,
    n_new: int,
    old_partner_key: str,
    new_partner_key: str,
    old_partner_role: str,
    new_partner_role: str,
    uniform: float,
) -> dict[str, Any]:
    return {
        "master_seed": int(seed),
        "phase": str(phase),
        "episode": int(episode),
        "batch": None if batch is None else int(batch),
        "regime": regime,
        "counterfactual_pair_index": pair_index,
        "root": int(root),
        "s": int(s),
        "n_old": int(n_old),
        "n_new": int(n_new),
        "old_partner_key": str(old_partner_key),
        "new_partner_key": str(new_partner_key),
        "old_partner_role": str(old_partner_role),
        "new_partner_role": str(new_partner_role),
        "action_uniform": float(uniform),
        "rng_identity": {
            "environment": f"{seed}:environment:{phase}",
            "composition": f"{seed}:composition:{phase}",
            "identity": f"{seed}:identity:{phase}",
            "action_sampling": f"{seed}:action_sampling:{phase}",
            "trainer": f"{seed}:trainer:{phase}",
        },
    }


def build_frozen_manifest(
    *, config: ExperimentConfig, source_commit: str, run_id: str
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", str(source_commit)):
        raise ValueError("source_commit must be a lowercase 40-hex Git identity")
    if not str(run_id):
        raise ValueError("run_id must be non-empty")
    training: dict[str, list[list[dict[str, Any]]]] = {}
    evaluation: dict[str, dict[str, list[dict[str, Any]]]] = {}
    streams: dict[str, Any] = {}
    initialization_digests: dict[str, str] = {}
    parameter_schema: list[dict[str, Any]] | None = None
    parameter_count: int | None = None
    for seed in config.master_seeds:
        streams[str(seed)] = {
            name: _rng_identity(seed, name)
            for name in (
                "environment:train",
                "composition:train",
                "identity:train",
                "action_sampling:train",
                "trainer:train",
                "environment:evaluate",
                "composition:evaluate",
                "identity:evaluate",
                "action_sampling:evaluate",
                "trainer:evaluate",
                "initialization",
            )
        }
        actor = MatchedWitnessActor(config=config, initialization_seed=_derive_seed(seed, "initialization"))
        initialization_digests[str(seed)] = _state_digest(actor.state_dict())
        parameter_schema = parameter_schema or actor.parameter_schema()
        parameter_count = parameter_count or actor.parameter_count()
        env_rng = np.random.default_rng(_derive_seed(seed, "environment:train"))
        order_rng = np.random.default_rng(_derive_seed(seed, "trainer:train"))
        action_rng = np.random.default_rng(_derive_seed(seed, "action_sampling:train"))
        batches: list[list[dict[str, Any]]] = []
        episode = 0
        for batch in range(config.batches):
            rows: list[dict[str, Any]] = []
            for s in (0, 1):
                for diagonal in (0, 1):
                    for occurrence in range(config.train_examples_per_cell):
                        old_index = (occurrence + batch) % len(PARTNER_KEYS)
                        new_index = (old_index + 1 + (occurrence // len(PARTNER_KEYS)) % 2) % len(PARTNER_KEYS)
                        rows.append(
                            _manifest_row(
                                seed=seed,
                                phase="train",
                                episode=-1,
                                batch=batch,
                                regime=None,
                                pair_index=None,
                                root=int(env_rng.integers(0, 2**62)),
                                s=s,
                                n_old=diagonal,
                                n_new=diagonal,
                                old_partner_key=PARTNER_KEYS[old_index],
                                new_partner_key=PARTNER_KEYS[new_index],
                                old_partner_role=PARTNER_ROLES[(occurrence + batch) % 2],
                                new_partner_role=PARTNER_ROLES[(occurrence + batch + 1) % 2],
                                uniform=float(action_rng.random()),
                            )
                        )
            if len(rows) != config.batch_size:
                raise RuntimeError("training cell balance does not fill one batch")
            order = order_rng.permutation(len(rows)).tolist()
            frozen: list[dict[str, Any]] = []
            for index in order:
                row = dict(rows[int(index)])
                row["episode"] = episode
                episode += 1
                frozen.append(row)
            batches.append(frozen)
        training[str(seed)] = batches

        eval_env = np.random.default_rng(_derive_seed(seed, "environment:evaluate"))
        eval_action = np.random.default_rng(_derive_seed(seed, "action_sampling:evaluate"))
        eval_order = np.random.default_rng(_derive_seed(seed, "trainer:evaluate"))
        all_rows: dict[str, list[dict[str, Any]]] = {regime: [] for regime in REGIMES}
        episode = 0
        # A complete 2x2x2 cube shares root, uniform, identity and role for each
        # replicate.  Consequently every required paired kernel is observational,
        # never an additional environment transition.
        for occurrence in range(config.eval_examples_per_cell):
            root = int(eval_env.integers(0, 2**62))
            uniform = float(eval_action.random())
            old_index = occurrence % len(PARTNER_KEYS)
            new_index = (old_index + 1 + (occurrence // len(PARTNER_KEYS)) % 2) % len(PARTNER_KEYS)
            for s in (0, 1):
                for n_old in (0, 1):
                    for n_new in (0, 1):
                        regime = "DIAGONAL" if n_old == n_new else "CHANGED"
                        all_rows[regime].append(
                            _manifest_row(
                                seed=seed,
                                phase="evaluate",
                                episode=episode,
                                batch=None,
                                regime=regime,
                                pair_index=occurrence,
                                root=root,
                                s=s,
                                n_old=n_old,
                                n_new=n_new,
                                old_partner_key=PARTNER_KEYS[old_index],
                                new_partner_key=PARTNER_KEYS[new_index],
                                old_partner_role=PARTNER_ROLES[occurrence % 2],
                                new_partner_role=PARTNER_ROLES[(occurrence + 1) % 2],
                                uniform=uniform,
                            )
                        )
                        episode += 1
        for regime in REGIMES:
            if len(all_rows[regime]) != config.eval_episodes_per_regime:
                raise RuntimeError("evaluation regime count drift")
            order = eval_order.permutation(len(all_rows[regime])).tolist()
            all_rows[regime] = [all_rows[regime][int(index)] for index in order]
        evaluation[str(seed)] = all_rows
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B2_FROZEN_MANIFEST",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "run_id": str(run_id),
        "source_commit": str(source_commit),
        "config": config.to_json(),
        "architecture": {
            "class": "MatchedWitnessActor",
            "feed_forward": True,
            "critic": False,
            "total_memory_dim": config.memory_dim,
            "s03_slice": [0, config.s03_dim],
            "s04_slice": [config.s03_dim, config.memory_dim],
            "parameter_schema": parameter_schema,
            "parameter_count": parameter_count,
            "learned_call_trace": list(MatchedWitnessActor.CALL_TRACE),
            "initialization_digests_by_master_seed": initialization_digests,
            "learned_arm_isomorphism": {
                "ordered_parameter_names_shapes_dtypes": True,
                "total_state_dimension": True,
                "writer_event_update_reader_wait_head_action_head": True,
                "initialization_tensors": True,
                "information_descriptors": True,
                "data_order_uniforms": True,
                "optimizer_hyperparameters_and_empty_state": True,
                "sole_delta": "fixed_lifecycle_routing_after_identical_learned_candidates",
            },
        },
        "optimizer": {
            "class": config.optimizer,
            "learning_rate": config.learning_rate,
            "initial_state": {},
            "updates_per_batch": config.updates_per_batch,
        },
        "rng_streams": streams,
        "training": training,
        "evaluation": evaluation,
        "composition_contract": {
            "training": "diagonal_only_exact_four_cells",
            "evaluation": "DIAGONAL_and_CHANGED_complete_cube",
            "identities_and_roles_counterbalanced_independently_of_bits": True,
            "every_identity_role_and_bit_seen_in_training": True,
        },
    }
    manifest["content_sha256"] = hashlib.sha256(_canonical_bytes(manifest)).hexdigest()
    return manifest


class _GzipJsonlWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._raw = path.open("wb")
        self._gzip = gzip.GzipFile(filename="", mode="wb", fileobj=self._raw, mtime=0)
        self.rows = 0

    def write(self, value: Mapping[str, Any]) -> None:
        self._gzip.write(_canonical_bytes(dict(value)) + b"\n")
        self.rows += 1

    def close(self) -> None:
        self._gzip.close()
        self._raw.close()

    def __enter__(self) -> "_GzipJsonlWriter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()


def _read_jsonl_gz(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def _sample_actions(
    probabilities: torch.Tensor,
    uniforms: Sequence[float],
    captured_kernels: Sequence[Mapping[str, Any]],
) -> tuple[torch.Tensor, list[dict[str, Any]]]:
    if len(captured_kernels) != int(probabilities.shape[0]):
        raise ValueError("every sampled row requires one prior kernel capture")
    witnesses: list[dict[str, Any]] = []
    for index, kernel in enumerate(captured_kernels):
        current = np.asarray(probabilities[index].detach().cpu(), dtype="<f4").tobytes(order="C")
        if base64.b64encode(current).decode("ascii") != kernel["probabilities_base64"]:
            raise RuntimeError("probability tensor changed after kernel capture")
        witnesses.append(
            {
                "chronology_token": kernel["chronology_token"],
                "kernel_capture_sequence": int(kernel["capture_sequence"]),
                "action_sampling_sequence": 1,
                "capture_precedes_sampling": int(kernel["capture_sequence"]) < 1,
            }
        )
    values = torch.as_tensor(uniforms, dtype=probabilities.dtype, device=probabilities.device)
    cumulative = probabilities.cumsum(dim=1)
    actions = (values[:, None] > cumulative).sum(dim=1).clamp_max(3).to(torch.int64)
    return actions, witnesses


def _kernel_payload(
    logits: torch.Tensor,
    probabilities: torch.Tensor,
    *,
    chronology_context: Mapping[str, Any],
) -> dict[str, Any]:
    logits_np = np.asarray(logits.detach().cpu(), dtype="<f4")
    probabilities_np = np.asarray(probabilities.detach().cpu(), dtype="<f4")
    probability_bytes = probabilities_np.tobytes(order="C")
    logits_bytes = logits_np.tobytes(order="C")
    chronology_token = hashlib.sha256(
        b"FOLR-B2-KERNEL-CAPTURE\0"
        + _manifest_projection(chronology_context)
        + b"\0"
        + logits_bytes
        + b"\0"
        + probability_bytes
    ).hexdigest()
    return {
        "dtype": "float32",
        "shape": [4],
        "byte_order": "little",
        "logits": logits_np.astype(float).tolist(),
        "probabilities": probabilities_np.astype(float).tolist(),
        "logits_base64": base64.b64encode(logits_bytes).decode("ascii"),
        "probabilities_base64": base64.b64encode(probability_bytes).decode("ascii"),
        "logits_sha256": hashlib.sha256(logits_bytes).hexdigest(),
        "probabilities_sha256": hashlib.sha256(probability_bytes).hexdigest(),
        "chronology_token": chronology_token,
        "capture_sequence": 0,
        "complete": True,
        "captured_before_sampling": True,
    }


def _episode_batch(
    *,
    actor: MatchedWitnessActor,
    arm: str,
    rows: Sequence[Mapping[str, Any]],
    dimensions: HostDimensions,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, list[dict[str, Any]]]:
    s = torch.as_tensor([int(row["s"]) for row in rows], dtype=torch.int64)
    n_old = torch.as_tensor([int(row["n_old"]) for row in rows], dtype=torch.int64)
    n_new = torch.as_tensor([int(row["n_new"]) for row in rows], dtype=torch.int64)
    (
        survivor,
        old_partner,
        initial,
        wait_one,
        survivor_provenance,
        old_partner_provenance,
    ) = _ordinary_t1_writer_emissions(actor, s=s, n_old=n_old, rows=rows)
    hosts: list[CounterfactualWitnessHost] = []
    transition_one_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        host = CounterfactualWitnessHost(
            arm=arm,
            root=int(row["root"]),
            old_partner_key=str(row["old_partner_key"]),
            new_partner_key=str(row["new_partner_key"]),
            old_partner_role=str(row["old_partner_role"]),
            new_partner_role=str(row["new_partner_role"]),
            dimensions=dimensions,
        )
        transition_one_rows.append(
            host.transition_one(
                survivor_candidate=survivor[index],
                old_partner_candidate=old_partner[index],
                survivor_provenance=survivor_provenance[index],
                old_partner_provenance=old_partner_provenance[index],
                wait_logit=wait_one[index],
            )
        )
        hosts.append(host)
    replacement_descriptors = torch.as_tensor(
        [_descriptor(row, phase="replacement") for row in rows], dtype=torch.float32
    )
    zero_writes = torch.zeros_like(initial)
    event_candidates = actor.learned_update(initial, zero_writes, replacement_descriptors)
    replacement_witnesses: list[dict[str, Any]] = []
    routed_memories: list[torch.Tensor] = []
    for index, host in enumerate(hosts):
        witness = host.apply_replacement(
            host.replacement_transaction(), learned_event_candidate=event_candidates[index]
        )
        replacement_witnesses.append(asdict(witness))
        routed_memories.append(host._memory())
    routed = torch.stack(routed_memories)
    new_partner = actor.new_partner_write(n_new)
    ordinary_post_write = torch.cat((torch.zeros_like(new_partner), new_partner), dim=-1)
    post_descriptors = torch.as_tensor(
        [_descriptor(row, phase="post_event") for row in rows], dtype=torch.float32
    )
    post_candidates = actor.learned_update(routed, ordinary_post_write, post_descriptors)
    transition_two_rows: list[dict[str, Any]] = []
    post_t2_witnesses: list[dict[str, Any]] = []
    choice_memories: list[torch.Tensor] = []
    choice_public_views: list[dict[str, Any]] = []
    for index, host in enumerate(hosts):
        transition_two_rows.append(
            host.transition_two(
                new_partner_candidate=new_partner[index],
                learned_post_candidate=post_candidates[index],
                wait_logit=actor.wait_policy(post_candidates[index : index + 1])[0],
            )
        )
        post_t2_witnesses.append(dict(host.routing_witness()))
        choice_public_views.append(host.public_view())
        choice_memories.append(host.choice_memory())
    memory = torch.stack(choice_memories)
    logits = actor.choice_policy(memory)
    probabilities = torch.softmax(logits, dim=-1)
    # Capture complete float32 logits/probabilities before action sampling.
    captured_kernels = [
        _kernel_payload(
            logits[index], probabilities[index], chronology_context=rows[index]
        )
        for index in range(len(rows))
    ]
    actions, sampling_witnesses = _sample_actions(
        probabilities,
        [float(row["action_uniform"]) for row in rows],
        captured_kernels,
    )
    rewards: list[float] = []
    evidence_rows: list[dict[str, Any]] = []
    for index, (host, source) in enumerate(zip(hosts, rows)):
        terminal = host.terminal_transition(
            action=int(actions[index]), s=int(source["s"]), n_new=int(source["n_new"])
        )
        kernel = captured_kernels[index]
        correct_action = int(terminal["correct_action"])
        rewards.append(float(terminal["reward"]))
        evidence_rows.append(
            {
                **dict(source),
                "arm": arm,
                "host_identifier": HOST_IDENTIFIER,
                "owner_key": OWNER_KEY,
                "owner_epoch": OWNER_EPOCH,
                "backend": host.backend_schema(),
                "transition_one": transition_one_rows[index],
                "membership_transaction": replacement_witnesses[index],
                "post_t2_routing_witness": post_t2_witnesses[index],
                "transition_two": transition_two_rows[index],
                "choice_public_view": choice_public_views[index],
                "final_kernel": kernel,
                "sampling_chronology": sampling_witnesses[index],
                "correct_action_probability": float(probabilities[index, correct_action].detach()),
                "action": int(actions[index]),
                "correct_action": correct_action,
                "survivor_component_correct": bool(int(actions[index]) // 2 == int(source["s"])),
                "new_partner_component_correct": bool(int(actions[index]) % 2 == int(source["n_new"])),
                "reward": float(terminal["reward"]),
                "terminal": terminal,
                "policy_calls": 3,
                "environment_transitions": 3,
                "learned_call_trace": list(MatchedWitnessActor.CALL_TRACE),
                "public_bit_input": False,
                "arm_regime_or_answer_label_input": False,
                "bit_correlated_rng": False,
                "cached_choice_path": False,
                "pending_action": False,
                "update_between_event_and_choice": False,
            }
        )
    return torch.as_tensor(rewards, dtype=torch.float32), actions, probabilities, evidence_rows


def _checkpoint_path(root: Path, arm: str, seed: int) -> Path:
    return root / "checkpoints" / f"{arm.lower()}_{int(seed)}_final.pt"


def _status(root: Path, *, phase: str, state: str, detail: Mapping[str, Any] | None = None) -> None:
    _write_json(
        root / "phase_status.json",
        {"schema_version": 1, "phase": phase, "state": state, "detail": dict(detail or {})},
    )


def train(
    *, output_root: str | Path, source_commit: str, run_id: str, technical_smoke: bool = False
) -> dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    config = technical_smoke_config() if technical_smoke else registered_config()
    manifest = build_frozen_manifest(config=config, source_commit=source_commit, run_id=run_id)
    manifest_path = root / "frozen_manifest.json"
    _write_json(manifest_path, manifest)
    manifest_binding = _file_binding(manifest_path)
    dimensions = HostDimensions(
        memory_dim=config.memory_dim, s03_dim=config.s03_dim, s04_dim=config.s04_dim
    )
    train_sidecar = root / "train_episodes.jsonl.gz"
    arm_runs: list[dict[str, Any]] = []
    initialization_by_seed: dict[int, str] = {}
    parameter_schema: list[dict[str, Any]] | None = None
    _status(root, phase="train", state="RUNNING")
    with _GzipJsonlWriter(train_sidecar) as writer:
        for arm in config.arms:
            for seed in config.master_seeds:
                initialization_seed = _derive_seed(seed, "initialization")
                actor = MatchedWitnessActor(config=config, initialization_seed=initialization_seed)
                schema = actor.parameter_schema()
                if parameter_schema is None:
                    parameter_schema = schema
                elif schema != parameter_schema:
                    raise RuntimeError("ordered trainable parameter schema drifted across arms")
                initial_digest = _state_digest(actor.state_dict())
                if initial_digest != manifest["architecture"]["initialization_digests_by_master_seed"][str(seed)]:
                    raise RuntimeError("fresh initialization differs from frozen manifest")
                if initialization_by_seed.setdefault(seed, initial_digest) != initial_digest:
                    raise RuntimeError("matched arm initialization is not tensor-exact")
                optimizer = torch.optim.Adam(actor.parameters(), lr=config.learning_rate)
                if optimizer.state_dict()["state"]:
                    raise RuntimeError("Adam state must start empty")
                curve: list[float] = []
                for batch_index, batch_rows in enumerate(manifest["training"][str(seed)]):
                    optimizer.zero_grad(set_to_none=True)
                    rewards, actions, probabilities, evidence_rows = _episode_batch(
                        actor=actor, arm=arm, rows=batch_rows, dimensions=dimensions
                    )
                    chosen = probabilities.gather(1, actions.reshape(-1, 1)).squeeze(1)
                    log_probability = torch.log(chosen.clamp_min(torch.finfo(chosen.dtype).tiny))
                    baseline = rewards.mean()
                    advantage = rewards - baseline
                    entropy = -(
                        probabilities
                        * torch.log(probabilities.clamp_min(torch.finfo(probabilities.dtype).tiny))
                    ).sum(dim=1)
                    loss = -(advantage.detach() * log_probability).mean() - config.entropy_coefficient * entropy.mean()
                    if not bool(torch.isfinite(loss)):
                        raise RuntimeError("non-finite REINFORCE loss")
                    loss.backward()
                    optimizer.step()
                    curve.append(float(rewards.mean()))
                    for row in evidence_rows:
                        row.update(
                            {
                                "phase": "train",
                                "batch_update_index": batch_index,
                                "optimizer_updates_before_episode": batch_index,
                                "optimizer_updates_after_complete_batch": batch_index + 1,
                                "batch_mean_baseline": float(baseline),
                                "reinforce_loss": float(loss.detach()),
                                "entropy_mean": float(entropy.mean().detach()),
                            }
                        )
                        writer.write(row)
                checkpoint = _checkpoint_path(root, arm, seed)
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "schema_version": SCHEMA_VERSION,
                    "artifact_kind": "FOLR_B2_FINAL_CHECKPOINT",
                    "run_id": run_id,
                    "source_commit": source_commit,
                    "arm": arm,
                    "master_seed": seed,
                    "config": config.to_json(),
                    "parameter_schema": schema,
                    "parameter_count": actor.parameter_count(),
                    "initialization_seed": initialization_seed,
                    "initial_model_digest": initial_digest,
                    "final_model_digest": _state_digest(actor.state_dict()),
                    "model_state": actor.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "training_curve": curve,
                    "updates": config.batches,
                    "manifest_sha256": manifest_binding["sha256"],
                    "final_checkpoint_only": True,
                }
                torch.save(payload, checkpoint)
                episodes = config.batches * config.batch_size
                arm_runs.append(
                    {
                        "arm": arm,
                        "master_seed": seed,
                        "episodes": episodes,
                        "transitions": episodes * 3,
                        "policy_calls": episodes * 3,
                        "learner_calls": config.batches,
                        "trainer_calls": config.batches,
                        "optimizer_updates": config.batches,
                        "training_return_curve": curve,
                        "initial_model_digest": initial_digest,
                        "final_model_digest": payload["final_model_digest"],
                        "learned_call_trace": list(MatchedWitnessActor.CALL_TRACE),
                        "checkpoint": _file_binding(checkpoint),
                    }
                )
    actor_runs = len(config.arms) * len(config.master_seeds)
    train_episodes = actor_runs * config.batches * config.batch_size
    updates = actor_runs * config.batches
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B2_TRAIN_SUMMARY",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "run_id": run_id,
        "source_commit": source_commit,
        "technical_only": config.technical_only,
        "scientific_terminal_admitted": False,
        "config": config.to_json(),
        "manifest": manifest_binding,
        "train_sidecar": _file_binding(train_sidecar, rows=train_episodes),
        "parameter_schema": parameter_schema,
        "parameter_count": manifest["architecture"]["parameter_count"],
        "learned_arm_isomorphism": manifest["architecture"]["learned_arm_isomorphism"],
        "arm_runs": arm_runs,
        "activity_counts": {
            "actor_runs": actor_runs,
            "train_episodes": train_episodes,
            "environment_transitions": train_episodes * 3,
            "policy_calls": train_episodes * 3,
            "learner_calls": updates,
            "trainer_calls": updates,
            "optimizer_updates": updates,
            "k_search": 0,
            "hypothetical_transitions": 0,
        },
        "fidelity": {
            "typed_membership_transaction": True,
            "same_owner_record_and_epoch": True,
            "explicit_counterfactual_lineage_witness": True,
            "old_partner_invalidated_new_partner_rebuilt": True,
            "same_learned_candidate_computations_all_arms": True,
            "sole_learned_arm_delta_fixed_routing": True,
            "three_policy_calls_and_transitions_per_episode": True,
            "complete_kernel_before_sampling": True,
            "final_checkpoints_only": True,
        },
        "exclusions": EXCLUSIONS,
    }
    _write_json(root / "train_summary.json", summary)
    _status(root, phase="train", state="COMPLETE", detail=summary["activity_counts"])
    validate_train(root, require_full=not technical_smoke)
    return summary


def _load_checkpoint(root: Path, arm: str, seed: int) -> dict[str, Any]:
    return torch.load(_checkpoint_path(root, arm, seed), map_location="cpu", weights_only=False)


def evaluate(*, output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root)
    train_summary = validate_train(root, require_full=None)
    config = _config_from_json(train_summary["config"])
    manifest = _read_json(root / "frozen_manifest.json")
    dimensions = HostDimensions(
        memory_dim=config.memory_dim, s03_dim=config.s03_dim, s04_dim=config.s04_dim
    )
    eval_sidecar = root / "eval_episodes.jsonl.gz"
    arm_runs: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    _status(root, phase="evaluate", state="RUNNING")
    with _GzipJsonlWriter(eval_sidecar) as writer:
        for arm in config.arms:
            for seed in config.master_seeds:
                checkpoint = _load_checkpoint(root, arm, seed)
                actor = MatchedWitnessActor(config=config, initialization_seed=int(checkpoint["initialization_seed"]))
                actor.load_state_dict(checkpoint["model_state"], strict=True)
                actor.eval()
                for regime in config.regimes:
                    rows = manifest["evaluation"][str(seed)][regime]
                    with torch.no_grad():
                        rewards, _actions, _probabilities, evidence_rows = _episode_batch(
                            actor=actor, arm=arm, rows=rows, dimensions=dimensions
                        )
                    for row in evidence_rows:
                        row.update(
                            {
                                "phase": "evaluate",
                                "updates_enabled": False,
                                "interventions_enabled": False,
                                "final_checkpoint_only": True,
                            }
                        )
                        writer.write(row)
                    arm_runs.append(_metric_row(arm=arm, seed=seed, regime=regime, rows=evidence_rows))
                    group_rows.extend(
                        _group_metric_rows(
                            arm=arm, seed=seed, regime=regime, rows=evidence_rows
                        )
                    )
    eval_episodes = (
        len(config.arms)
        * len(config.master_seeds)
        * len(config.regimes)
        * config.eval_episodes_per_regime
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B2_EVALUATION_SUMMARY",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "run_id": train_summary["run_id"],
        "source_commit": train_summary["source_commit"],
        "technical_only": config.technical_only,
        "scientific_terminal_admitted": False,
        "config": config.to_json(),
        "manifest": train_summary["manifest"],
        "train_summary_sha256": _sha256_file(root / "train_summary.json"),
        "eval_sidecar": _file_binding(eval_sidecar, rows=eval_episodes),
        "arm_runs": arm_runs,
        "group_rows": group_rows,
        "activity_counts": {
            "eval_episodes": eval_episodes,
            "environment_transitions": eval_episodes * 3,
            "policy_calls": eval_episodes * 3,
            "learner_calls": 0,
            "trainer_calls": 0,
            "optimizer_updates": 0,
        },
        "paired_manifest_across_arms": True,
        "updates_enabled": False,
        "interventions_enabled": False,
    }
    _write_json(root / "evaluation_summary.json", summary)
    _status(root, phase="evaluate", state="COMPLETE", detail=summary["activity_counts"])
    validate_evaluation(root, require_full=not config.technical_only)
    return summary


def _metric_row(
    *, arm: str, seed: int, regime: str, rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    return {
        "arm": arm,
        "master_seed": int(seed),
        "regime": regime,
        "episodes": len(rows),
        "transitions": len(rows) * 3,
        "policy_calls": len(rows) * 3,
        "mean_return": float(np.mean([float(row["reward"]) for row in rows])),
        "survivor_component_accuracy": float(
            np.mean([bool(row["survivor_component_correct"]) for row in rows])
        ),
        "new_partner_component_accuracy": float(
            np.mean([bool(row["new_partner_component_correct"]) for row in rows])
        ),
        "mean_correct_action_probability": float(
            np.mean([float(row["correct_action_probability"]) for row in rows])
        ),
    }


def _group_metric_rows(
    *, arm: str, seed: int, regime: str, rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    groups: list[tuple[str, tuple[str, ...]]] = [
        ("composition", ("s", "n_old", "n_new")),
        ("old_identity", ("old_partner_key",)),
        ("new_identity", ("new_partner_key",)),
        ("old_role", ("old_partner_role",)),
        ("new_role", ("new_partner_role",)),
    ]
    output: list[dict[str, Any]] = []
    for kind, fields in groups:
        values = sorted(
            {tuple(row[field] for field in fields) for row in rows},
            key=lambda value: _canonical_bytes(value),
        )
        for value in values:
            selected = [
                row for row in rows if tuple(row[field] for field in fields) == value
            ]
            metric = _metric_row(arm=arm, seed=seed, regime=regime, rows=selected)
            output.append(
                {
                    **metric,
                    "group_kind": kind,
                    "group_fields": list(fields),
                    "group_value": list(value),
                }
            )
    return output


def _aggregate_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for arm in ARMS:
        output[arm] = {}
        for regime in REGIMES:
            selected = [row for row in rows if row["arm"] == arm and row["regime"] == regime]
            output[arm][regime] = {
                "J": float(np.mean([row["mean_return"] for row in selected])),
                "S": float(np.mean([row["survivor_component_accuracy"] for row in selected])),
                "N": float(np.mean([row["new_partner_component_accuracy"] for row in selected])),
                "correct_action_probability": float(
                    np.mean([row["mean_correct_action_probability"] for row in selected])
                ),
                "seeds": selected,
            }
    return output


def _build_paired_rows(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lookup: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for row in rows:
        key = (
            row["arm"], int(row["master_seed"]), int(row["counterfactual_pair_index"]),
            int(row["s"]), int(row["n_old"]), int(row["n_new"]),
        )
        if key in lookup:
            raise RuntimeError("duplicate evaluation cube cell")
        lookup[key] = row
    summaries: dict[str, Any] = {}
    pair_rows: list[dict[str, Any]] = []
    seeds = sorted({int(row["master_seed"]) for row in rows})
    for contrast, flip_field in (
        ("FLIP_N_OLD_FIXED_S_N_NEW", "n_old"),
        ("FLIP_S_FIXED_N_OLD_N_NEW", "s"),
        ("FLIP_N_NEW_FIXED_S_N_OLD", "n_new"),
    ):
        distances: dict[str, list[float]] = {arm: [] for arm in ARMS}
        correct_distances: dict[str, list[float]] = {arm: [] for arm in ARMS}
        exact: dict[str, int] = {arm: 0 for arm in ARMS}
        contrast_rows = 0
        for arm in ARMS:
            for seed in seeds:
                repetitions = sorted(
                    {
                        int(row["counterfactual_pair_index"])
                        for row in rows
                        if row["arm"] == arm and int(row["master_seed"]) == seed
                    }
                )
                fixed_fields = [field for field in ("s", "n_old", "n_new") if field != flip_field]
                for repetition in repetitions:
                    for first in (0, 1):
                        fixed = {fixed_fields[0]: first}
                        for second in (0, 1):
                            fixed[fixed_fields[1]] = second
                            bits0 = {"s": 0, "n_old": 0, "n_new": 0, **fixed, flip_field: 0}
                            bits1 = {**bits0, flip_field: 1}
                            left = lookup[(arm, seed, repetition, bits0["s"], bits0["n_old"], bits0["n_new"])]
                            right = lookup[(arm, seed, repetition, bits1["s"], bits1["n_old"], bits1["n_new"])]
                            p0 = np.asarray(left["final_kernel"]["probabilities"], dtype=np.float64)
                            p1 = np.asarray(right["final_kernel"]["probabilities"], dtype=np.float64)
                            distance = float(np.max(np.abs(p0 - p1)))
                            identical = left["final_kernel"]["probabilities_base64"] == right["final_kernel"]["probabilities_base64"]
                            correct_distance = abs(
                                float(left["correct_action_probability"])
                                - float(right["correct_action_probability"])
                            )
                            pair_rows.append(
                                {
                                    "contrast": contrast,
                                    "arm": arm,
                                    "master_seed": seed,
                                    "pair_index": repetition,
                                    "root": int(left["root"]),
                                    "old_partner_key": left["old_partner_key"],
                                    "new_partner_key": left["new_partner_key"],
                                    "old_partner_role": left["old_partner_role"],
                                    "new_partner_role": left["new_partner_role"],
                                    "left_regime": left["regime"],
                                    "right_regime": right["regime"],
                                    "fixed": dict(fixed),
                                    "left_bits": bits0,
                                    "right_bits": bits1,
                                    "left_kernel_sha256": left["final_kernel"]["probabilities_sha256"],
                                    "right_kernel_sha256": right["final_kernel"]["probabilities_sha256"],
                                    "kernel_byte_exact": identical,
                                    "max_probability_difference": distance,
                                    "correct_action_probability_difference": correct_distance,
                                }
                            )
                            distances[arm].append(distance)
                            correct_distances[arm].append(correct_distance)
                            exact[arm] += int(identical)
                            contrast_rows += 1
        summaries[contrast] = {
            arm: {
                "pairs": len(distances[arm]),
                "byte_exact_pairs": exact[arm],
                "all_kernel_byte_exact": exact[arm] == len(distances[arm]),
                "max_probability_difference": max(distances[arm], default=math.nan),
                "max_correct_action_probability_difference": max(
                    correct_distances[arm], default=math.nan
                ),
            }
            for arm in ARMS
        }
        summaries[contrast]["rows"] = contrast_rows
    return pair_rows, summaries


def _paired_tables(eval_sidecar: Path, output: Path) -> tuple[dict[str, Any], int]:
    pair_rows, summaries = _build_paired_rows(list(_read_jsonl_gz(eval_sidecar)))
    with _GzipJsonlWriter(output) as writer:
        for row in pair_rows:
            writer.write(row)
    return summaries, len(pair_rows)


def _summarize_pair_sidecar(path: Path) -> tuple[dict[str, Any], int]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    total = 0
    for row in _read_jsonl_gz(path):
        contrast = str(row["contrast"])
        arm = str(row["arm"])
        slot = grouped.setdefault(contrast, {}).setdefault(
            arm,
            {"pairs": 0, "byte_exact_pairs": 0, "max_probability_difference": 0.0,
             "max_correct_action_probability_difference": 0.0},
        )
        slot["pairs"] += 1
        slot["byte_exact_pairs"] += int(bool(row["kernel_byte_exact"]))
        slot["max_probability_difference"] = max(
            slot["max_probability_difference"], float(row["max_probability_difference"])
        )
        slot["max_correct_action_probability_difference"] = max(
            slot["max_correct_action_probability_difference"],
            float(row["correct_action_probability_difference"]),
        )
        total += 1
    summaries: dict[str, Any] = {}
    for contrast, by_arm in grouped.items():
        summaries[contrast] = {}
        for arm in ARMS:
            slot = by_arm.get(arm)
            if slot is None:
                raise ValueError("paired counterfactual sidecar omits an arm")
            summaries[contrast][arm] = {
                **slot,
                "all_kernel_byte_exact": slot["pairs"] == slot["byte_exact_pairs"],
            }
        summaries[contrast]["rows"] = sum(by_arm[arm]["pairs"] for arm in ARMS)
    return summaries, total


def _decision(metrics: Mapping[str, Any], pairs: Mapping[str, Any], *, valid: bool) -> tuple[str, dict[str, bool]]:
    typed = metrics[TYPED_WITNESS_S03_S04]
    generic = metrics[ISOMORPHIC_GENERIC_MEMORY]
    reset = metrics[COMPLETE_RESET]
    reset_ok = True
    for regime in REGIMES:
        row = reset[regime]
        reset_ok &= 0.47 <= row["J"] <= 0.53 and 0.47 <= row["S"] <= 0.53 and row["N"] >= 0.90
        reset_ok &= sum(0.44 <= seed["mean_return"] <= 0.56 for seed in row["seeds"]) >= 7
    reset_ok &= pairs["FLIP_S_FIXED_N_OLD_N_NEW"][COMPLETE_RESET]["all_kernel_byte_exact"]
    generic_diag = generic["DIAGONAL"]["J"] >= 0.80 and sum(
        seed["mean_return"] >= 0.75 for seed in generic["DIAGONAL"]["seeds"]
    ) >= 7
    typed_diag = typed["DIAGONAL"]["J"] >= 0.80 and sum(
        seed["mean_return"] >= 0.75 for seed in typed["DIAGONAL"]["seeds"]
    ) >= 7
    typed_invariant = pairs["FLIP_N_OLD_FIXED_S_N_NEW"][TYPED_WITNESS_S03_S04]["all_kernel_byte_exact"]
    typed_changed = (
        typed["CHANGED"]["J"] >= 0.80
        and typed["CHANGED"]["S"] >= 0.90
        and typed["CHANGED"]["N"] >= 0.90
        and sum(
            seed["mean_return"] >= 0.75
            and seed["survivor_component_accuracy"] >= 0.85
            and seed["new_partner_component_accuracy"] >= 0.85
            for seed in typed["CHANGED"]["seeds"]
        ) >= 7
    )
    typed_changed_seed = {int(row["master_seed"]): row for row in typed["CHANGED"]["seeds"]}
    generic_changed_seed = {int(row["master_seed"]): row for row in generic["CHANGED"]["seeds"]}
    typed_diag_seed = {int(row["master_seed"]): row for row in typed["DIAGONAL"]["seeds"]}
    generic_diag_seed = {int(row["master_seed"]): row for row in generic["DIAGONAL"]["seeds"]}
    common = sorted(set(typed_changed_seed) & set(generic_changed_seed))
    delta_changed = typed["CHANGED"]["J"] - generic["CHANGED"]["J"]
    delta_diag = typed["DIAGONAL"]["J"] - generic["DIAGONAL"]["J"]
    typed_value = (
        delta_changed >= 0.20
        and sum(
            typed_changed_seed[seed]["mean_return"] - generic_changed_seed[seed]["mean_return"] >= 0.10
            for seed in common
        ) >= 7
        and delta_diag >= -0.05
        and sum(
            typed_diag_seed[seed]["mean_return"] - generic_diag_seed[seed]["mean_return"] >= -0.10
            for seed in common
        ) >= 7
    )
    both_changed = all(
        row["CHANGED"]["J"] >= 0.75 and row["CHANGED"]["S"] >= 0.85 and row["CHANGED"]["N"] >= 0.85
        for row in (typed, generic)
    )
    material_gap = Decimal("0.08")
    exact_changed_gap = Decimal(str(typed["CHANGED"]["J"])) - Decimal(
        str(generic["CHANGED"]["J"])
    )
    generic_equivalence = (
        both_changed
        and abs(exact_changed_gap) < material_gap
        and sum(
            abs(typed_changed_seed[seed]["mean_return"] - generic_changed_seed[seed]["mean_return"]) <= 0.12
            for seed in common
        ) >= 7
        and pairs["FLIP_N_OLD_FIXED_S_N_NEW"][ISOMORPHIC_GENERIC_MEMORY]["max_correct_action_probability_difference"] <= 0.05
    )
    generic_changed = generic["CHANGED"]["J"] >= 0.75 and generic["CHANGED"]["S"] >= 0.85 and generic["CHANGED"]["N"] >= 0.85
    generic_out = generic_changed and (
        not typed_changed or -exact_changed_gap >= material_gap
    )
    both_fail_changed = generic_diag and typed_diag and not typed_changed and not generic_changed
    gates = {
        "admission_valid": bool(valid),
        "reset_valid": bool(reset_ok),
        "generic_diagonal_calibrated": bool(generic_diag),
        "typed_diagonal_calibrated": bool(typed_diag),
        "typed_old_partner_kernel_invariant": bool(typed_invariant),
        "typed_changed_success": bool(typed_changed),
        "typed_value_margin": bool(typed_value),
        "generic_equivalence": bool(generic_equivalence),
        "generic_changed_threshold": bool(generic_changed),
        "generic_outgeneralizes": bool(generic_out),
        "both_learned_fail_changed": bool(both_fail_changed),
        "terminal_predicates": {
            "HOST_LOCAL_TYPED_FILTER_VALUE_SUPPORTED": bool(typed_changed and typed_value),
            "GENERIC_MEMORY_SUFFICIENT_AT_CAP": bool(generic_equivalence),
            "GENERIC_OUTGENERALIZES_TYPED": bool(generic_out),
            "OOD_LEARNABILITY_UNRESOLVED_AT_CAP": bool(both_fail_changed),
        },
    }
    if not valid:
        return "B2_INVALID", gates
    if not reset_ok:
        return "RESET_LEAK_OR_NEW_PARTNER_CALIBRATION_FAILED", gates
    if not generic_diag:
        return "GENERIC_CAPACITY_CONTROL_FAILED", gates
    if not typed_diag or not typed_invariant:
        return "TYPED_ROUTE_FAILED_ON_SUPPORT", gates
    if typed_changed and typed_value:
        return "HOST_LOCAL_TYPED_FILTER_VALUE_SUPPORTED", gates
    if generic_equivalence:
        return "GENERIC_MEMORY_SUFFICIENT_AT_CAP", gates
    if generic_out:
        return "GENERIC_OUTGENERALIZES_TYPED", gates
    if both_fail_changed:
        return "OOD_LEARNABILITY_UNRESOLVED_AT_CAP", gates
    return "INDETERMINATE_AT_CAP", gates


def analyze(*, output_root: str | Path, result_path: str | Path | None = None) -> dict[str, Any]:
    root = Path(output_root)
    evaluation = validate_evaluation(root, require_full=None)
    train_summary = _read_json(root / "train_summary.json")
    config = _config_from_json(evaluation["config"])
    metrics = _aggregate_metrics(evaluation["arm_runs"])
    pair_path = root / "counterfactual_pairs.jsonl.gz"
    pairs, pair_rows = _paired_tables(root / "eval_episodes.jsonl.gz", pair_path)
    full_identity = _config_matches_registered(config.to_json())
    unique_decision, gates = _decision(metrics, pairs, valid=full_identity)
    decision = unique_decision if full_identity else TECHNICAL_DECISION
    train_counts = train_summary["activity_counts"]
    eval_counts = evaluation["activity_counts"]
    total_counts = {
        "actor_runs": train_counts["actor_runs"],
        "train_episodes": train_counts["train_episodes"],
        "eval_episodes": eval_counts["eval_episodes"],
        "total_episodes": train_counts["train_episodes"] + eval_counts["eval_episodes"],
        "train_transitions_policy_calls": train_counts["environment_transitions"],
        "eval_transitions_policy_calls": eval_counts["environment_transitions"],
        "total_environment_transitions": train_counts["environment_transitions"] + eval_counts["environment_transitions"],
        "total_policy_calls": train_counts["policy_calls"] + eval_counts["policy_calls"],
        "learner_calls": train_counts["learner_calls"],
        "trainer_calls": train_counts["trainer_calls"],
        "optimizer_updates": train_counts["optimizer_updates"],
        "k_search": 0,
        "hypothetical_transitions": 0,
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B2_COUNTERFACTUAL_WITNESS_GATED_NUISANCE_TRANSFER_RESULT",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "run_id": evaluation["run_id"],
        "source_commit": evaluation["source_commit"],
        "technical_only": config.technical_only,
        "scientific_terminal_admitted": bool(full_identity),
        "decision": decision,
        "unique_frozen_branch": unique_decision if full_identity else None,
        "config": config.to_json(),
        "activity_counts": total_counts,
        "metrics": metrics,
        "paired_counterfactual_tables": pairs,
        "paired_counterfactual_sidecar": _file_binding(pair_path, rows=pair_rows),
        "gates": gates,
        "admission": {
            "revision_v5_rule_bound": True,
            "typed_generic_exact_isomorphism": True,
            "fixed_routing_sole_treatment_delta": True,
            "owner_epoch_and_atomic_replacement": True,
            "complete_and_within_cap": full_identity,
        },
        "smallest_supported_proposition_boundary": "finite_budget_host_local_only",
        "strongest_alternative": "An isomorphic generic memory may acquire the same routing with more optimization; the diagonal-to-changed split favors pre-specified typed structure.",
        "exclusions": EXCLUSIONS,
        "bindings": {
            "manifest": train_summary["manifest"],
            "train_summary": _file_binding(root / "train_summary.json"),
            "train_sidecar": train_summary["train_sidecar"],
            "evaluation_summary": _file_binding(root / "evaluation_summary.json"),
            "eval_sidecar": evaluation["eval_sidecar"],
        },
    }
    canonical_target = root / "result.json"
    _write_json(canonical_target, result)
    _status(root, phase="analyze", state="COMPLETE", detail={"decision": decision})
    validate_result(canonical_target, require_full=full_identity, output_root=root)
    if result_path is not None:
        external_target = Path(result_path)
        if external_target.resolve() != canonical_target.resolve():
            _write_json(external_target, result)
            validate_result(
                external_target,
                require_full=full_identity,
                output_root=root,
            )
    return result


def _config_from_json(value: Mapping[str, Any]) -> ExperimentConfig:
    data = dict(value)
    for key in ("arms", "master_seeds", "regimes"):
        data[key] = tuple(data[key])
    return ExperimentConfig(**data)


def _config_matches_registered(value: Mapping[str, Any]) -> bool:
    return dict(value) == registered_config().to_json()


def _config_matches_smoke(value: Mapping[str, Any]) -> bool:
    return dict(value) == technical_smoke_config().to_json()


def _validate_binding(root: Path, binding: Mapping[str, Any]) -> Path:
    path = root / str(binding["path"])
    if not path.is_file() or path.stat().st_size != int(binding["size_bytes"]):
        raise ValueError(f"artifact binding missing or size mismatch: {path}")
    if _sha256_file(path) != binding["sha256"]:
        raise ValueError(f"artifact digest mismatch: {path}")
    return path


def _expected_counts(config: ExperimentConfig) -> dict[str, int]:
    actor_runs = len(config.arms) * len(config.master_seeds)
    train_episodes = actor_runs * config.batches * config.batch_size
    eval_episodes = actor_runs * len(config.regimes) * config.eval_episodes_per_regime
    return {
        "actor_runs": actor_runs,
        "train_episodes": train_episodes,
        "train_transitions": train_episodes * 3,
        "updates": actor_runs * config.batches,
        "eval_episodes": eval_episodes,
        "eval_transitions": eval_episodes * 3,
        "total_episodes": train_episodes + eval_episodes,
        "total_transitions": (train_episodes + eval_episodes) * 3,
    }


def _validate_mode(config: ExperimentConfig, require_full: bool | None) -> None:
    registered = _config_matches_registered(config.to_json())
    smoke = _config_matches_smoke(config.to_json())
    if not registered and not smoke:
        raise ValueError("configuration is neither registered full nor exact technical smoke")
    if require_full is True and not registered:
        raise ValueError("registered full configuration required")
    if require_full is False and not smoke:
        raise ValueError("exact technical smoke configuration required")


def _validate_manifest(manifest: Mapping[str, Any], config: ExperimentConfig) -> None:
    content = dict(manifest)
    digest = content.pop("content_sha256", None)
    if digest != hashlib.sha256(_canonical_bytes(content)).hexdigest():
        raise ValueError("frozen manifest content digest mismatch")
    if manifest["artifact_kind"] != "FOLR_B2_FROZEN_MANIFEST" or manifest["config"] != config.to_json():
        raise ValueError("manifest binding or config mismatch")
    iso = manifest["architecture"]["learned_arm_isomorphism"]
    if not all(value is True for key, value in iso.items() if key != "sole_delta"):
        raise ValueError("learned-arm isomorphism admission failed")
    if iso["sole_delta"] != "fixed_lifecycle_routing_after_identical_learned_candidates":
        raise ValueError("treatment delta is not uniquely frozen")
    for seed in config.master_seeds:
        batches = manifest["training"][str(seed)]
        if len(batches) != config.batches:
            raise ValueError("training batch count mismatch")
        seen: dict[tuple[str, str], set[tuple[int, int]]] = {}
        for batch in batches:
            counts: dict[tuple[int, int, int], int] = {}
            for row in batch:
                cell = (int(row["s"]), int(row["n_old"]), int(row["n_new"]))
                counts[cell] = counts.get(cell, 0) + 1
                if cell[1] != cell[2] or row["regime"] is not None:
                    raise ValueError("training contains a non-diagonal composition")
                seen.setdefault((row["old_partner_key"], row["old_partner_role"]), set()).add((cell[1], cell[0]))
            expected = {(s, n, n): config.train_examples_per_cell for s in (0, 1) for n in (0, 1)}
            if counts != expected:
                raise ValueError("training batch is not exact four-cell balance")
        if {row["old_partner_key"] for batch in batches for row in batch} != set(PARTNER_KEYS):
            raise ValueError("training does not cover every partner identity")
        if {row["old_partner_role"] for batch in batches for row in batch} != set(PARTNER_ROLES):
            raise ValueError("training does not cover every partner role")
        if {row["new_partner_key"] for batch in batches for row in batch} != set(PARTNER_KEYS):
            raise ValueError("training does not cover every new-partner identity")
        if {row["new_partner_role"] for batch in batches for row in batch} != set(PARTNER_ROLES):
            raise ValueError("training does not cover every new-partner role")
        for regime in REGIMES:
            rows = manifest["evaluation"][str(seed)][regime]
            counts: dict[tuple[int, int, int], int] = {}
            for row in rows:
                cell = (int(row["s"]), int(row["n_old"]), int(row["n_new"]))
                counts[cell] = counts.get(cell, 0) + 1
                if (regime == "DIAGONAL") != (cell[1] == cell[2]):
                    raise ValueError("evaluation regime/composition mismatch")
            allowed = (
                {(s, n, n): config.eval_examples_per_cell for s in (0, 1) for n in (0, 1)}
                if regime == "DIAGONAL"
                else {(s, n, 1 - n): config.eval_examples_per_cell for s in (0, 1) for n in (0, 1)}
            )
            if counts != allowed:
                raise ValueError("evaluation regime is not exact four-cell balance")
        _validate_identity_role_independence(
            [row for batch in batches for row in batch], context=f"train:{seed}"
        )
        _validate_identity_role_independence(
            [
                row
                for regime in REGIMES
                for row in manifest["evaluation"][str(seed)][regime]
            ],
            context=f"evaluate:{seed}",
        )


MANIFEST_ROW_FIELDS = (
    "phase",
    "episode",
    "batch",
    "regime",
    "counterfactual_pair_index",
    "root",
    "s",
    "n_old",
    "n_new",
    "old_partner_key",
    "new_partner_key",
    "old_partner_role",
    "new_partner_role",
    "action_uniform",
    "rng_identity",
)


def _manifest_projection(row: Mapping[str, Any]) -> bytes:
    return _canonical_bytes({field: row[field] for field in MANIFEST_ROW_FIELDS})


def _manifest_row_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["arm"]),
        int(row["master_seed"]),
        str(row["phase"]),
        row["batch"],
        row["regime"],
        int(row["episode"]),
    )


def _expected_sidecar_rows(
    manifest: Mapping[str, Any], config: ExperimentConfig, *, phase: str
) -> dict[tuple[Any, ...], bytes]:
    expected: dict[tuple[Any, ...], bytes] = {}
    for arm in config.arms:
        for seed in config.master_seeds:
            if phase == "train":
                source_rows = [row for batch in manifest["training"][str(seed)] for row in batch]
            elif phase == "evaluate":
                source_rows = [
                    row
                    for regime in config.regimes
                    for row in manifest["evaluation"][str(seed)][regime]
                ]
            else:
                raise ValueError("unknown manifest phase")
            for source in source_rows:
                row = {**source, "arm": arm}
                key = _manifest_row_key(row)
                if key in expected:
                    raise ValueError("frozen manifest contains a duplicate row identity")
                expected[key] = _manifest_projection(row)
    return expected


def _validate_identity_role_independence(
    rows: Sequence[Mapping[str, Any]], *, context: str
) -> None:
    for position, identity_field, role_field in (
        ("old", "old_partner_key", "old_partner_role"),
        ("new", "new_partner_key", "new_partner_role"),
    ):
        expected_identities = set(PARTNER_KEYS)
        expected_roles = set(PARTNER_ROLES)
        for bit_field in ("s", "n_old", "n_new"):
            for bit_value in (0, 1):
                selected = [row for row in rows if int(row[bit_field]) == bit_value]
                identities = {str(row[identity_field]) for row in selected}
                roles = {str(row[role_field]) for row in selected}
                if identities != expected_identities:
                    raise ValueError(
                        f"{context} {position} identity is not independent of {bit_field}={bit_value}"
                    )
                if roles != expected_roles:
                    raise ValueError(
                        f"{context} {position} role is not independent of {bit_field}={bit_value}"
                    )


def _validate_episode(row: Mapping[str, Any]) -> None:
    if row["host_identifier"] != HOST_IDENTIFIER or row["owner_key"] != OWNER_KEY or int(row["owner_epoch"]) != OWNER_EPOCH:
        raise ValueError("host or owner binding mismatch")
    if int(row["policy_calls"]) != 3 or int(row["environment_transitions"]) != 3:
        raise ValueError("episode activity differs from frozen H=3")
    if row["public_bit_input"] or row["arm_regime_or_answer_label_input"] or row["bit_correlated_rng"]:
        raise ValueError("forbidden information path recorded")
    if row["cached_choice_path"] or row["pending_action"] or row["update_between_event_and_choice"]:
        raise ValueError("forbidden alternate answer path recorded")
    if row["learned_call_trace"] != list(MatchedWitnessActor.CALL_TRACE):
        raise ValueError("learned module call trace drift")
    for name in ("transition_one", "transition_two"):
        transition = row[name]
        if transition["action"] != "WAIT" or transition["reward"] != 0.0 or transition["wait_kernel"] != [1.0]:
            raise ValueError("WAIT transition fidelity failed")
    witness = row["membership_transaction"]
    required = (
        "typed_transaction", "exact_atomic_deltas", "same_owner_record",
        "uninterrupted_owner_epoch", "old_partner_terminal", "old_partner_memory_cleared",
        "new_partner_join",
        "survivor_witness_passes", "old_partner_witness_fails",
    )
    if not all(witness[name] for name in required):
        raise ValueError("lifecycle or lineage witness failed")
    if witness["new_s04_rebuilt_after_event"] or witness["memory_digest_after_new_partner_write"] is not None:
        raise ValueError("pre-t2 witness incorrectly claims new S04 already exists")
    post_t2 = row["post_t2_routing_witness"]
    if not post_t2["new_s04_rebuilt_after_event"] or not post_t2["memory_digest_after_new_partner_write"]:
        raise ValueError("post-t2 witness does not prove new S04 rebuild timing")
    for immutable in (
        "survivor_lineage", "old_partner_lineage", "survivor_witness_passes",
        "old_partner_witness_fails", "memory_digest_pre_event",
        "memory_digest_after_replacement",
    ):
        if post_t2[immutable] != witness[immutable]:
            raise ValueError("post-t2 witness changed immutable replacement evidence")
    transition_one = row["transition_one"]
    expected_survivor = _writer_provenance(row, state_kind="survivor_private")
    expected_partner = _writer_provenance(row, state_kind="partner_scoped")
    if _canonical_bytes(transition_one["survivor_provenance"]) != _canonical_bytes(asdict(expected_survivor)):
        raise ValueError("survivor writer provenance mismatch")
    if _canonical_bytes(transition_one["old_partner_provenance"]) != _canonical_bytes(asdict(expected_partner)):
        raise ValueError("old-partner writer provenance mismatch")
    for name, provenance in (
        ("survivor_lineage", expected_survivor),
        ("old_partner_lineage", expected_partner),
    ):
        derived = derive_counterfactual_lineage(
            provenance,
            departed_partner_key=str(row["old_partner_key"]),
            joined_partner_key=str(row["new_partner_key"]),
            post_owner_key=OWNER_KEY,
            post_owner_epoch=OWNER_EPOCH,
        )
        if _canonical_bytes(witness[name]) != _canonical_bytes(asdict(derived)):
            raise ValueError("serialized lineage does not derive from writer provenance")
    if witness["second_information_carrier"] or witness["cached_action_kernel_or_logits"]:
        raise ValueError("second carrier/cache detected")
    arm = row["arm"]
    if arm == TYPED_WITNESS_S03_S04 and not (
        witness["s03_retained"] and witness["old_s04_invalidated"]
    ):
        raise ValueError("typed route did not retain S03 and invalidate old S04")
    if not row["terminal"]["all_memory_cleared"]:
        raise ValueError("terminal memory was not fully cleared")
    kernel = row["final_kernel"]
    if kernel["dtype"] != "float32" or kernel["shape"] != [4] or not kernel["complete"]:
        raise ValueError("final kernel encoding mismatch")
    probability_bytes = base64.b64decode(kernel["probabilities_base64"], validate=True)
    logits_bytes = base64.b64decode(kernel["logits_base64"], validate=True)
    probabilities = np.frombuffer(probability_bytes, dtype="<f4")
    logits = np.frombuffer(logits_bytes, dtype="<f4")
    if (
        probabilities.shape != (4,)
        or logits.shape != (4,)
        or not np.isfinite(probabilities).all()
        or not np.isfinite(logits).all()
    ):
        raise ValueError("non-finite or incomplete final kernel")
    if hashlib.sha256(probability_bytes).hexdigest() != kernel["probabilities_sha256"]:
        raise ValueError("final kernel byte digest mismatch")
    if hashlib.sha256(logits_bytes).hexdigest() != kernel["logits_sha256"]:
        raise ValueError("final logits byte digest mismatch")
    if not np.allclose(probabilities, np.asarray(kernel["probabilities"], dtype=np.float32), rtol=0, atol=0):
        raise ValueError("numeric and byte kernel representations differ")
    if not np.allclose(logits, np.asarray(kernel["logits"], dtype=np.float32), rtol=0, atol=0):
        raise ValueError("numeric and byte logits representations differ")
    token = hashlib.sha256(
        b"FOLR-B2-KERNEL-CAPTURE\0"
        + _manifest_projection(row)
        + b"\0"
        + logits_bytes
        + b"\0"
        + probability_bytes
    ).hexdigest()
    chronology = row["sampling_chronology"]
    if (
        kernel["chronology_token"] != token
        or chronology["chronology_token"] != token
        or int(kernel["capture_sequence"]) != 0
        or int(chronology["kernel_capture_sequence"]) != 0
        or int(chronology["action_sampling_sequence"]) != 1
        or not chronology["capture_precedes_sampling"]
    ):
        raise ValueError("kernel capture/action sampling chronology mismatch")
    if abs(float(probabilities.sum()) - 1.0) > 2e-6 or (probabilities < 0).any():
        raise ValueError("invalid categorical kernel")
    correct = 2 * int(row["s"]) + int(row["n_new"])
    if int(row["correct_action"]) != correct or int(row["terminal"]["correct_action"]) != correct:
        raise ValueError("correct action mapping drift")
    expected_reward = float(int(row["action"]) == correct)
    if float(row["reward"]) != expected_reward or float(row["terminal"]["reward"]) != expected_reward:
        raise ValueError("reward does not match exact two-component action")
    if bool(row["survivor_component_correct"]) != (int(row["action"]) // 2 == int(row["s"])):
        raise ValueError("survivor component decoding mismatch")
    if bool(row["new_partner_component_correct"]) != (int(row["action"]) % 2 == int(row["n_new"])):
        raise ValueError("new-partner component decoding mismatch")
    if float(row["correct_action_probability"]) != float(probabilities[correct]):
        raise ValueError("correct-action probability was not decoded from full kernel")
    expected_action = min(
        int((float(row["action_uniform"]) > np.cumsum(probabilities)).sum()), 3
    )
    if int(row["action"]) != expected_action:
        raise ValueError("recorded action does not follow captured kernel and uniform")
    public = row["choice_public_view"]
    if set(public) != {"physical_time", "active_keys", "observation", "legal_actions"}:
        raise ValueError("choice public observation contains an unexpected field")
    if public["legal_actions"] != [0, 1, 2, 3] or len(public["observation"]) != 4:
        raise ValueError("final observation or legal mask drift")


def validate_train(output_root: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root)
    summary = _read_json(root / "train_summary.json")
    if summary["artifact_kind"] != "FOLR_B2_TRAIN_SUMMARY" or summary["raw_output_binding"] != RAW_OUTPUT_BINDING:
        raise ValueError("train artifact binding mismatch")
    config = _config_from_json(summary["config"])
    _validate_mode(config, require_full)
    manifest_path = _validate_binding(root, summary["manifest"])
    sidecar_path = _validate_binding(root, summary["train_sidecar"])
    manifest = _read_json(manifest_path)
    _validate_manifest(manifest, config)
    expected_manifest_rows = _expected_sidecar_rows(manifest, config, phase="train")
    expected = _expected_counts(config)
    counts = summary["activity_counts"]
    exact = {
        "actor_runs": expected["actor_runs"],
        "train_episodes": expected["train_episodes"],
        "environment_transitions": expected["train_transitions"],
        "policy_calls": expected["train_transitions"],
        "learner_calls": expected["updates"],
        "trainer_calls": expected["updates"],
        "optimizer_updates": expected["updates"],
        "k_search": 0,
        "hypothetical_transitions": 0,
    }
    if counts != exact or int(summary["train_sidecar"]["rows"]) != expected["train_episodes"]:
        raise ValueError("training activity count mismatch")
    initial: dict[int, str] = {}
    for run in summary["arm_runs"]:
        seed = int(run["master_seed"])
        if initial.setdefault(seed, run["initial_model_digest"]) != run["initial_model_digest"]:
            raise ValueError("arm initialization mismatch")
        if run["learned_call_trace"] != list(MatchedWitnessActor.CALL_TRACE):
            raise ValueError("arm learned call trace mismatch")
        checkpoint = _validate_binding(root / "checkpoints", run["checkpoint"])
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if not payload["final_checkpoint_only"] or payload["updates"] != config.batches:
            raise ValueError("checkpoint is not final-only or update-complete")
        if payload["parameter_schema"] != summary["parameter_schema"] or int(payload["parameter_count"]) != int(summary["parameter_count"]):
            raise ValueError("checkpoint parameter isomorphism drift")
    checkpoint_files = list((root / "checkpoints").glob("*.pt"))
    if len(checkpoint_files) != expected["actor_runs"] or any("_final.pt" not in path.name for path in checkpoint_files):
        raise ValueError("checkpoint directory is not final-only exact cardinality")
    row_count = 0
    cell_counts: dict[tuple[str, int, int, int, int, int], int] = {}
    observed_manifest_rows: dict[tuple[Any, ...], bytes] = {}
    for row in _read_jsonl_gz(sidecar_path):
        _validate_episode(row)
        key = (
            row["arm"], int(row["master_seed"]), int(row["batch"]),
            int(row["s"]), int(row["n_old"]), int(row["n_new"]),
        )
        cell_counts[key] = cell_counts.get(key, 0) + 1
        manifest_key = _manifest_row_key(row)
        if manifest_key in observed_manifest_rows:
            raise ValueError("training sidecar contains a duplicate manifest row")
        observed_manifest_rows[manifest_key] = _manifest_projection(row)
        row_count += 1
    if row_count != expected["train_episodes"] or any(value != config.train_examples_per_cell for value in cell_counts.values()):
        raise ValueError("training sidecar completeness/balance mismatch")
    if observed_manifest_rows != expected_manifest_rows:
        raise ValueError("training sidecar does not exactly reproduce the frozen manifest")
    return summary


def validate_evaluation(output_root: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root)
    summary = _read_json(root / "evaluation_summary.json")
    if summary["artifact_kind"] != "FOLR_B2_EVALUATION_SUMMARY" or summary["raw_output_binding"] != RAW_OUTPUT_BINDING:
        raise ValueError("evaluation artifact binding mismatch")
    train_summary = validate_train(root, require_full=require_full)
    config = _config_from_json(summary["config"])
    _validate_mode(config, require_full)
    if summary["train_summary_sha256"] != _sha256_file(root / "train_summary.json"):
        raise ValueError("evaluation does not bind current train summary")
    sidecar_path = _validate_binding(root, summary["eval_sidecar"])
    manifest = _read_json(root / "frozen_manifest.json")
    expected_manifest_rows = _expected_sidecar_rows(manifest, config, phase="evaluate")
    expected = _expected_counts(config)
    counts = summary["activity_counts"]
    if counts != {
        "eval_episodes": expected["eval_episodes"],
        "environment_transitions": expected["eval_transitions"],
        "policy_calls": expected["eval_transitions"],
        "learner_calls": 0,
        "trainer_calls": 0,
        "optimizer_updates": 0,
    }:
        raise ValueError("evaluation activity count mismatch")
    rows = list(_read_jsonl_gz(sidecar_path))
    if len(rows) != expected["eval_episodes"] or int(summary["eval_sidecar"]["rows"]) != len(rows):
        raise ValueError("evaluation sidecar row count mismatch")
    cells: dict[tuple[str, int, str, int, int, int], int] = {}
    public_by_cube: dict[tuple[str, int, int, int], set[str]] = {}
    observed_manifest_rows: dict[tuple[Any, ...], bytes] = {}
    for row in rows:
        _validate_episode(row)
        key = (
            row["arm"], int(row["master_seed"]), row["regime"],
            int(row["s"]), int(row["n_old"]), int(row["n_new"]),
        )
        cells[key] = cells.get(key, 0) + 1
        cube = (row["arm"], int(row["master_seed"]), int(row["counterfactual_pair_index"]), int(row["root"]))
        public_by_cube.setdefault(cube, set()).add(
            json.dumps(row["choice_public_view"], sort_keys=True, separators=(",", ":"))
        )
        manifest_key = _manifest_row_key(row)
        if manifest_key in observed_manifest_rows:
            raise ValueError("evaluation sidecar contains a duplicate manifest row")
        observed_manifest_rows[manifest_key] = _manifest_projection(row)
    if any(value != config.eval_examples_per_cell for value in cells.values()):
        raise ValueError("evaluation cell balance mismatch")
    if any(len(values) != 1 for values in public_by_cube.values()):
        raise ValueError("public observation or mask depends on answer bits")
    if observed_manifest_rows != expected_manifest_rows:
        raise ValueError("evaluation sidecar does not exactly reproduce the frozen manifest")
    if len(summary["arm_runs"]) != len(config.arms) * len(config.master_seeds) * len(config.regimes):
        raise ValueError("evaluation seed/regime summary incomplete")
    recomputed_arm_runs: list[dict[str, Any]] = []
    recomputed_groups: list[dict[str, Any]] = []
    for arm in config.arms:
        for seed in config.master_seeds:
            for regime in config.regimes:
                selected = [
                    row
                    for row in rows
                    if row["arm"] == arm
                    and int(row["master_seed"]) == int(seed)
                    and row["regime"] == regime
                ]
                recomputed_arm_runs.append(
                    _metric_row(arm=arm, seed=seed, regime=regime, rows=selected)
                )
                recomputed_groups.extend(
                    _group_metric_rows(
                        arm=arm, seed=seed, regime=regime, rows=selected
                    )
                )
    if summary["arm_runs"] != recomputed_arm_runs:
        raise ValueError("evaluation arm/seed/regime metrics do not recompute from sidecar")
    if summary.get("group_rows") != recomputed_groups:
        raise ValueError("evaluation composition/identity/role rows do not recompute from sidecar")
    if train_summary["source_commit"] != summary["source_commit"] or train_summary["run_id"] != summary["run_id"]:
        raise ValueError("train/evaluation identity mismatch")
    return summary


def validate_result(
    result_path: str | Path,
    *,
    require_full: bool | None,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(result_path)
    result = _read_json(path)
    if result["artifact_kind"] != "FOLR_B2_COUNTERFACTUAL_WITNESS_GATED_NUISANCE_TRANSFER_RESULT":
        raise ValueError("result artifact kind mismatch")
    config = _config_from_json(result["config"])
    _validate_mode(config, require_full)
    full = _config_matches_registered(config.to_json())
    root = Path(output_root) if output_root is not None else path.parent
    evaluation = validate_evaluation(root, require_full=require_full)
    recomputed_metrics = _aggregate_metrics(evaluation["arm_runs"])
    if result["metrics"] != recomputed_metrics:
        raise ValueError("result metrics do not recompute from evaluation summary")
    pair_path = _validate_binding(root, result["paired_counterfactual_sidecar"])
    eval_sidecar = _validate_binding(root, evaluation["eval_sidecar"])
    expected_pair_rows, recomputed_pairs = _build_paired_rows(
        list(_read_jsonl_gz(eval_sidecar))
    )
    actual_pair_rows = list(_read_jsonl_gz(pair_path))
    if actual_pair_rows != expected_pair_rows:
        raise ValueError("paired counterfactual sidecar does not reconstruct from evaluation cube")
    if result["paired_counterfactual_tables"] != recomputed_pairs:
        raise ValueError("paired counterfactual summaries do not recompute from sidecar")
    if len(actual_pair_rows) != int(result["paired_counterfactual_sidecar"]["rows"]):
        raise ValueError("paired counterfactual sidecar row count mismatch")
    recomputed_branch, recomputed_gates = _decision(
        recomputed_metrics, recomputed_pairs, valid=full
    )
    if result["gates"] != recomputed_gates:
        raise ValueError("frozen gates do not recompute")
    if full:
        if (
            result["decision"] not in DECISIONS
            or result["unique_frozen_branch"] != result["decision"]
            or result["decision"] != recomputed_branch
        ):
            raise ValueError("full result does not contain one frozen decision")
        if not result["scientific_terminal_admitted"] or result["technical_only"]:
            raise ValueError("full result admission flags mismatch")
        expected = _expected_counts(config)
        counts = result["activity_counts"]
        if counts != {
            "actor_runs": 24,
            "train_episodes": 49152,
            "eval_episodes": 24576,
            "total_episodes": 73728,
            "train_transitions_policy_calls": 147456,
            "eval_transitions_policy_calls": 73728,
            "total_environment_transitions": 221184,
            "total_policy_calls": 221184,
            "learner_calls": 768,
            "trainer_calls": 768,
            "optimizer_updates": 768,
            "k_search": 0,
            "hypothetical_transitions": 0,
        } or expected["total_transitions"] != 221184:
            raise ValueError("registered full cap mismatch")
    else:
        if result["decision"] != TECHNICAL_DECISION or result["unique_frozen_branch"] is not None:
            raise ValueError("technical smoke emitted a scientific decision")
        if result["scientific_terminal_admitted"] or not result["technical_only"]:
            raise ValueError("technical smoke admission flags mismatch")
    for binding in result["bindings"].values():
        _validate_binding(root, binding)
    return result


def summarize_artifacts(output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root)
    return {
        "manifest": _file_binding(root / "frozen_manifest.json"),
        "train_summary": _file_binding(root / "train_summary.json"),
        "evaluation_summary": _file_binding(root / "evaluation_summary.json"),
        "result": _file_binding(root / "result.json"),
    }
