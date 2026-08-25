"""Train/evaluate/analyze package for frozen FOLR-B1.

The package has no formal-run authority.  ``technical_smoke=True`` creates a
small, explicitly non-scientific exercise; the registered configuration is the
only configuration admitted to a scientific terminal by the validators.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import numpy as np
import torch
from torch import nn

from experiments.candidates.folr_core.owner_epoch_survivor_bit_host import (
    ARMS,
    COMPLETE_RESET,
    HOST_IDENTIFIER,
    ONE_BIT_OWNER_EPOCH_LATCH,
    OWNER_EPOCH,
    OWNER_KEY,
    S03_KEEP,
    HostDimensions,
    OwnerEpochSurvivorBitHost,
)


RAW_OUTPUT_BINDING = "folr_core.owner_epoch_survivor_bit_learnability.v1"
SCHEMA_VERSION = 1
MASTER_SEEDS = tuple(range(93031, 93039))
DECISIONS = (
    "B1_INVALID",
    "BIT_LEAK_OR_SHORTCUT",
    "S03_LEARNED_USE_WITH_GENERIC_CAPACITY_CONFIRMED",
    "S03_LEARNED_USE_LATCH_ANOMALY",
    "GENERIC_MEMORY_ONLY_AT_CAP",
    "LEARNABILITY_CONTROL_FAILED",
    "INDETERMINATE_AT_CAP",
)
EXCLUSIONS = {
    "a1_payload_transplantation": False,
    "constructed_sensitivity_weights": False,
    "hand_aligned_head": False,
    "critic": False,
    "recurrence_outside_memory_reader": False,
    "attention": False,
    "auxiliary_loss": False,
    "replay": False,
    "history_or_frame_stack": False,
    "update_between_cue_and_choice": False,
    "cached_logits_kernel_or_action": False,
    "checkpoint_selection": False,
    "sweep_retry_rescue": False,
    "extra_arm": False,
}


@dataclass(frozen=True)
class ExperimentConfig:
    host_identifier: str
    arms: tuple[str, ...]
    master_seeds: tuple[int, ...]
    memory_dim: int
    reader_hidden_dim: int
    batches: int
    batch_size: int
    zeros_per_batch: int
    ones_per_batch: int
    eval_episodes: int
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
        data = asdict(self)
        data["arms"] = list(self.arms)
        data["master_seeds"] = list(self.master_seeds)
        return data


def registered_config() -> ExperimentConfig:
    return ExperimentConfig(
        host_identifier=HOST_IDENTIFIER,
        arms=ARMS,
        master_seeds=MASTER_SEEDS,
        memory_dim=8,
        reader_hidden_dim=16,
        batches=32,
        batch_size=64,
        zeros_per_batch=32,
        ones_per_batch=32,
        eval_episodes=512,
        learning_rate=0.003,
        entropy_coefficient=0.01,
        gamma=1.0,
        baseline="batch_mean_terminal_external_reward",
        optimizer="Adam",
        updates_per_batch=1,
        transitions_per_episode=2,
        policy_calls_per_episode=2,
        k_search=0,
        hypothetical_transitions=0,
        technical_only=False,
    )


def technical_smoke_config() -> ExperimentConfig:
    return ExperimentConfig(
        **{
            **registered_config().to_json(),
            "arms": ARMS,
            "master_seeds": (MASTER_SEEDS[0],),
            "batches": 2,
            "batch_size": 8,
            "zeros_per_batch": 4,
            "ones_per_batch": 4,
            "eval_episodes": 16,
            "technical_only": True,
        }
    )


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
    digest = hashlib.sha256(f"FOLR-B1|{int(master_seed)}|{stream}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _rng_identity(master_seed: int, stream: str) -> dict[str, Any]:
    return {
        "derivation": "sha256(FOLR-B1|master_seed|stream)[:8]-big-endian",
        "master_seed": int(master_seed),
        "stream": str(stream),
        "derived_seed": _derive_seed(master_seed, stream),
        "generator": "numpy.PCG64",
    }


def _array_digest(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("utf-8"))
    digest.update(str(tuple(array.shape)).encode("utf-8"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _state_digest(state: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("utf-8"))
        digest.update(tensor.numpy().tobytes(order="C"))
    return digest.hexdigest()


class SurvivorBitActor(nn.Module):
    """Fresh feed-forward actor shared exactly across all three backends."""

    def __init__(self, *, memory_dim: int, hidden_dim: int, initialization_seed: int) -> None:
        super().__init__()
        self.memory_dim = int(memory_dim)
        self.hidden_dim = int(hidden_dim)
        self.cue_encoder = nn.Linear(2, self.memory_dim)
        self.wait_head = nn.Linear(self.memory_dim, 1)
        self.memory_reader = nn.Linear(self.memory_dim, self.hidden_dim)
        self.action_head = nn.Linear(self.hidden_dim, 2)
        generator = torch.Generator(device="cpu")
        generator.manual_seed(int(initialization_seed) % (2**63 - 1))
        for module in (self.cue_encoder, self.wait_head, self.memory_reader, self.action_head):
            nn.init.xavier_uniform_(module.weight, generator=generator)
            nn.init.zeros_(module.bias)

    def cue_policy_call(self, bits: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        one_hot = torch.nn.functional.one_hot(bits.to(torch.int64), num_classes=2).to(torch.float32)
        activation = torch.tanh(self.cue_encoder(one_hot))
        wait_logits = self.wait_head(activation)
        return wait_logits, activation

    def choice_policy_call(self, memory: torch.Tensor) -> torch.Tensor:
        hidden = torch.tanh(self.memory_reader(memory))
        return self.action_head(hidden)

    def parameter_schema(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "shape": list(parameter.shape), "dtype": str(parameter.dtype)}
            for name, parameter in self.named_parameters()
        ]


def _manifest_row(
    *, seed: int, phase: str, episode: int, batch: int | None, root: int, bit: int, uniform: float
) -> dict[str, Any]:
    return {
        "master_seed": int(seed),
        "phase": str(phase),
        "episode": int(episode),
        "batch": None if batch is None else int(batch),
        "root": int(root),
        "bit": int(bit),
        "action_uniform": float(uniform),
        "rng_identity": {
            "environment": f"{seed}:environment:{phase}",
            "bit": f"{seed}:bit:{phase}",
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
    streams: dict[str, Any] = {}
    initialization_digests: dict[str, str] = {}
    training: dict[str, list[list[dict[str, Any]]]] = {}
    evaluation: dict[str, list[dict[str, Any]]] = {}
    for seed in config.master_seeds:
        streams[str(seed)] = {
            name: _rng_identity(seed, name)
            for name in (
                "environment:train",
                "bit:train",
                "action_sampling:train",
                "trainer:train",
                "environment:evaluate",
                "bit:evaluate",
                "action_sampling:evaluate",
                "trainer:evaluate",
                "initialization",
            )
        }
        frozen_actor = SurvivorBitActor(
            memory_dim=config.memory_dim,
            hidden_dim=config.reader_hidden_dim,
            initialization_seed=_derive_seed(seed, "initialization"),
        )
        initialization_digests[str(seed)] = _state_digest(frozen_actor.state_dict())
        env_train = np.random.default_rng(_derive_seed(seed, "environment:train"))
        bit_train = np.random.default_rng(_derive_seed(seed, "bit:train"))
        action_train = np.random.default_rng(_derive_seed(seed, "action_sampling:train"))
        batches: list[list[dict[str, Any]]] = []
        episode = 0
        for batch in range(config.batches):
            bits = np.asarray(
                [0] * config.zeros_per_batch + [1] * config.ones_per_batch,
                dtype=np.int64,
            )
            bit_train.shuffle(bits)
            roots = env_train.integers(0, 2**62, size=config.batch_size, dtype=np.int64)
            uniforms = action_train.random(config.batch_size)
            rows: list[dict[str, Any]] = []
            for index in range(config.batch_size):
                rows.append(
                    _manifest_row(
                        seed=seed,
                        phase="train",
                        episode=episode,
                        batch=batch,
                        root=int(roots[index]),
                        bit=int(bits[index]),
                        uniform=float(uniforms[index]),
                    )
                )
                episode += 1
            batches.append(rows)
        training[str(seed)] = batches

        # Evaluation is 256 matched roots.  Each root appears once with each bit
        # and uses the same sampling uniform in both rows.  A separate trainer
        # stream permutes episode presentation identically across arms.
        env_eval = np.random.default_rng(_derive_seed(seed, "environment:evaluate"))
        action_eval = np.random.default_rng(_derive_seed(seed, "action_sampling:evaluate"))
        trainer_eval = np.random.default_rng(_derive_seed(seed, "trainer:evaluate"))
        roots = env_eval.integers(0, 2**62, size=config.eval_episodes // 2, dtype=np.int64)
        uniforms = action_eval.random(config.eval_episodes // 2)
        paired: list[tuple[int, int, float]] = []
        for root, uniform in zip(roots.tolist(), uniforms.tolist()):
            paired.extend(((int(root), 0, float(uniform)), (int(root), 1, float(uniform))))
        order = trainer_eval.permutation(len(paired))
        evaluation[str(seed)] = [
            _manifest_row(
                seed=seed,
                phase="evaluate",
                episode=index,
                batch=None,
                root=paired[int(source_index)][0],
                bit=paired[int(source_index)][1],
                uniform=paired[int(source_index)][2],
            )
            for index, source_index in enumerate(order.tolist())
        ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B1_FROZEN_MANIFEST",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "run_id": str(run_id),
        "source_commit": str(source_commit),
        "config": config.to_json(),
        "model_contract": {
            "class": "SurvivorBitActor",
            "feed_forward": True,
            "critic": False,
            "parameter_schema": SurvivorBitActor(
                memory_dim=config.memory_dim,
                hidden_dim=config.reader_hidden_dim,
                initialization_seed=_derive_seed(config.master_seeds[0], "initialization"),
            ).parameter_schema(),
            "initialization_digests_by_master_seed": initialization_digests,
            "optimizer": {
                "class": config.optimizer,
                "learning_rate": config.learning_rate,
                "updates_per_complete_batch": config.updates_per_batch,
            },
        },
        "rng_streams": streams,
        "training": training,
        "evaluation": evaluation,
        "paired_across_arms": True,
        "evaluation_root_bit_pairs_share_action_uniform": True,
    }
    manifest["content_sha256"] = hashlib.sha256(_canonical_bytes(manifest)).hexdigest()
    return manifest


class _GzipJsonlWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._raw = self.path.open("wb")
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


def _sample_actions(probabilities: torch.Tensor, uniforms: Sequence[float]) -> torch.Tensor:
    values = torch.as_tensor(uniforms, dtype=probabilities.dtype, device=probabilities.device)
    return torch.where(values < probabilities[:, 0], 0, 1).to(torch.int64)


def _episode_batch(
    *,
    actor: SurvivorBitActor,
    arm: str,
    rows: Sequence[Mapping[str, Any]],
    dimensions: HostDimensions,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, list[dict[str, Any]]]:
    bits = torch.as_tensor([int(row["bit"]) for row in rows], dtype=torch.int64)
    wait_logits, cue_activations = actor.cue_policy_call(bits)
    if tuple(wait_logits.shape) != (len(rows), 1):
        raise RuntimeError("cue policy call did not produce the one-action WAIT kernel")
    hosts: list[OwnerEpochSurvivorBitHost] = []
    cue_rows: list[dict[str, Any]] = []
    transaction_rows: list[dict[str, Any]] = []
    choice_public_views: list[dict[str, object]] = []
    memories: list[torch.Tensor] = []
    for index, row in enumerate(rows):
        host = OwnerEpochSurvivorBitHost(
            arm=arm,
            root=int(row["root"]),
            dimensions=dimensions,
        )
        cue = host.cue_transition(int(row["bit"]), cue_activations[index])
        transaction = host.replacement_transaction()
        witness = host.apply_replacement(transaction)
        choice_public_views.append(host.public_view())
        memories.append(host.choice_memory())
        hosts.append(host)
        cue_rows.append(cue)
        transaction_rows.append(asdict(witness))
    memory = torch.stack(memories, dim=0)
    logits = actor.choice_policy_call(memory)
    probabilities = torch.softmax(logits, dim=-1)
    actions = _sample_actions(probabilities, [float(row["action_uniform"]) for row in rows])
    episode_rows: list[dict[str, Any]] = []
    rewards: list[float] = []
    for index, (host, source) in enumerate(zip(hosts, rows)):
        terminal = host.terminal_transition(action=int(actions[index]), bit=int(source["bit"]))
        rewards.append(float(terminal["reward"]))
        episode_rows.append(
            {
                **dict(source),
                "arm": arm,
                "host_identifier": HOST_IDENTIFIER,
                "owner_key": OWNER_KEY,
                "owner_epoch": OWNER_EPOCH,
                "backend": host.backend_schema(),
                "cue": cue_rows[index],
                "membership_transaction": transaction_rows[index],
                "choice_public_view": choice_public_views[index],
                "post_event_kernel": {
                    "logits": [float(x) for x in logits[index].detach().cpu().tolist()],
                    "probabilities": [float(x) for x in probabilities[index].detach().cpu().tolist()],
                    "complete": True,
                    "captured_before_sampling": True,
                },
                "action": int(actions[index]),
                "reward": float(terminal["reward"]),
                "terminal": terminal,
                "policy_calls": 2,
                "environment_transitions": 2,
                "update_between_cue_and_choice": False,
                "cached_choice_path": False,
                "public_bit_input": False,
                "bit_correlated_rng": False,
            }
        )
    return (
        torch.as_tensor(rewards, dtype=torch.float32),
        actions,
        probabilities,
        episode_rows,
    )


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
    dimensions = HostDimensions(memory_dim=config.memory_dim)
    train_sidecar = root / "train_episodes.jsonl.gz"
    arm_runs: list[dict[str, Any]] = []
    parameter_schema: list[dict[str, Any]] | None = None
    initialization_by_seed: dict[int, str] = {}
    _status(root, phase="train", state="RUNNING")
    with _GzipJsonlWriter(train_sidecar) as writer:
        for arm in config.arms:
            for seed in config.master_seeds:
                init_seed = _derive_seed(seed, "initialization")
                actor = SurvivorBitActor(
                    memory_dim=config.memory_dim,
                    hidden_dim=config.reader_hidden_dim,
                    initialization_seed=init_seed,
                )
                schema = actor.parameter_schema()
                if parameter_schema is None:
                    parameter_schema = schema
                elif schema != parameter_schema:
                    raise RuntimeError("trainable parameter schema drifted across arms")
                init_digest = _state_digest(actor.state_dict())
                if init_digest != manifest["model_contract"]["initialization_digests_by_master_seed"][str(seed)]:
                    raise RuntimeError("fresh initialization differs from the pre-frozen manifest")
                previous = initialization_by_seed.setdefault(seed, init_digest)
                if previous != init_digest:
                    raise RuntimeError("matched arm initialization is not exact")
                optimizer = torch.optim.Adam(actor.parameters(), lr=config.learning_rate)
                curve: list[float] = []
                updates = 0
                episodes = 0
                for batch_index, batch_rows in enumerate(manifest["training"][str(seed)]):
                    optimizer.zero_grad(set_to_none=True)
                    rewards, actions, probabilities, evidence_rows = _episode_batch(
                        actor=actor,
                        arm=arm,
                        rows=batch_rows,
                        dimensions=dimensions,
                    )
                    chosen = probabilities.gather(1, actions.reshape(-1, 1)).squeeze(1)
                    log_probability = torch.log(chosen.clamp_min(torch.finfo(chosen.dtype).tiny))
                    baseline = rewards.mean()
                    advantages = rewards - baseline
                    entropy = -(probabilities * torch.log(probabilities.clamp_min(torch.finfo(probabilities.dtype).tiny))).sum(dim=1)
                    loss = -(advantages.detach() * log_probability).mean() - config.entropy_coefficient * entropy.mean()
                    if not bool(torch.isfinite(loss)):
                        raise RuntimeError("non-finite REINFORCE loss")
                    loss.backward()
                    optimizer.step()
                    updates += 1
                    curve.append(float(rewards.mean()))
                    for row in evidence_rows:
                        row.update(
                            {
                                "phase": "train",
                                "batch_update_index": int(batch_index),
                                "optimizer_updates_before_choice": int(batch_index),
                                "optimizer_updates_after_complete_batch": int(batch_index + 1),
                                "batch_mean_baseline": float(baseline),
                                "reinforce_loss": float(loss.detach()),
                                "entropy_mean": float(entropy.mean().detach()),
                            }
                        )
                        writer.write(row)
                    episodes += len(batch_rows)
                checkpoint = _checkpoint_path(root, arm, seed)
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "schema_version": SCHEMA_VERSION,
                    "artifact_kind": "FOLR_B1_FINAL_CHECKPOINT",
                    "run_id": run_id,
                    "source_commit": source_commit,
                    "arm": arm,
                    "master_seed": seed,
                    "config": config.to_json(),
                    "parameter_schema": parameter_schema,
                    "initialization_seed": init_seed,
                    "initial_model_digest": init_digest,
                    "final_model_digest": _state_digest(actor.state_dict()),
                    "model_state": actor.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "training_curve": curve,
                    "updates": updates,
                    "manifest_sha256": manifest_binding["sha256"],
                    "final_checkpoint_only": True,
                }
                torch.save(payload, checkpoint)
                arm_runs.append(
                    {
                        "arm": arm,
                        "master_seed": seed,
                        "episodes": episodes,
                        "transitions": episodes * 2,
                        "policy_calls": episodes * 2,
                        "learner_calls": updates,
                        "trainer_calls": updates,
                        "optimizer_updates": updates,
                        "training_return_curve": curve,
                        "initial_model_digest": init_digest,
                        "final_model_digest": payload["final_model_digest"],
                        "checkpoint": _file_binding(checkpoint),
                    }
                )
    train_episodes = len(config.arms) * len(config.master_seeds) * config.batches * config.batch_size
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B1_TRAIN_SUMMARY",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "run_id": run_id,
        "source_commit": source_commit,
        "technical_only": config.technical_only,
        "scientific_terminal_admitted": False,
        "config": config.to_json(),
        "manifest": manifest_binding,
        "train_sidecar": _file_binding(train_sidecar, rows=train_episodes),
        "parameter_schema": parameter_schema,
        "arm_runs": arm_runs,
        "activity_counts": {
            "actor_runs": len(config.arms) * len(config.master_seeds),
            "train_episodes": train_episodes,
            "environment_transitions": train_episodes * 2,
            "policy_calls": train_episodes * 2,
            "learner_calls": len(config.arms) * len(config.master_seeds) * config.batches,
            "trainer_calls": len(config.arms) * len(config.master_seeds) * config.batches,
            "optimizer_updates": len(config.arms) * len(config.master_seeds) * config.batches,
            "k_search": 0,
            "hypothetical_transitions": 0,
        },
        "fidelity": {
            "typed_membership_transaction": True,
            "atomic_terminal_leave_plus_join": True,
            "owner_t_epoch_uninterrupted": True,
            "ordinary_cue_writer_all_arms": True,
            "same_parameter_schema_all_arms": True,
            "matched_initialization_all_arms": True,
            "one_update_after_complete_batch": True,
            "only_terminal_external_reward": True,
            "latch_schema_exact": ["lifecycle_key", "membership_epoch", "bit"],
            "reset_clears_only_s03": True,
            "complete_kernel_before_sampling": True,
            "single_registered_s03_authority": True,
            "reward_gradient_crosses_committed_s03": True,
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
    config = ExperimentConfig(
        **{
            **train_summary["config"],
            "arms": tuple(train_summary["config"]["arms"]),
            "master_seeds": tuple(train_summary["config"]["master_seeds"]),
        }
    )
    manifest = _read_json(root / "frozen_manifest.json")
    dimensions = HostDimensions(memory_dim=config.memory_dim)
    eval_sidecar = root / "eval_episodes.jsonl.gz"
    arm_runs: list[dict[str, Any]] = []
    _status(root, phase="evaluate", state="RUNNING")
    with _GzipJsonlWriter(eval_sidecar) as writer:
        for arm in config.arms:
            for seed in config.master_seeds:
                checkpoint = _load_checkpoint(root, arm, seed)
                actor = SurvivorBitActor(
                    memory_dim=config.memory_dim,
                    hidden_dim=config.reader_hidden_dim,
                    initialization_seed=int(checkpoint["initialization_seed"]),
                )
                actor.load_state_dict(checkpoint["model_state"], strict=True)
                actor.eval()
                rows = manifest["evaluation"][str(seed)]
                with torch.no_grad():
                    rewards, _actions, _probabilities, evidence_rows = _episode_batch(
                        actor=actor,
                        arm=arm,
                        rows=rows,
                        dimensions=dimensions,
                    )
                by_bit = {
                    str(bit): float(
                        np.mean([row["reward"] for row in evidence_rows if int(row["bit"]) == bit])
                    )
                    for bit in (0, 1)
                }
                action_one_by_bit = {
                    str(bit): float(
                        np.mean([int(row["action"] == 1) for row in evidence_rows if int(row["bit"]) == bit])
                    )
                    for bit in (0, 1)
                }
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
                arm_runs.append(
                    {
                        "arm": arm,
                        "master_seed": seed,
                        "episodes": len(rows),
                        "transitions": len(rows) * 2,
                        "policy_calls": len(rows) * 2,
                        "mean_return": float(rewards.mean()),
                        "per_bit_return": by_bit,
                        "per_bit_correct_action_probability": by_bit,
                        "per_bit_action_one_probability": action_one_by_bit,
                        "checkpoint_sha256": _sha256_file(_checkpoint_path(root, arm, seed)),
                    }
                )
    eval_episodes = len(config.arms) * len(config.master_seeds) * config.eval_episodes
    summary = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B1_EVALUATION_SUMMARY",
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
        "activity_counts": {
            "eval_episodes": eval_episodes,
            "environment_transitions": eval_episodes * 2,
            "policy_calls": eval_episodes * 2,
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


def _normalized_auc(curve: Sequence[float]) -> float:
    if not curve:
        raise ValueError("training curve is empty")
    if len(curve) == 1:
        return float(curve[0])
    return float(np.trapz(np.asarray(curve, dtype=np.float64), dx=1.0) / (len(curve) - 1))


def _seed_map(rows: Sequence[Mapping[str, Any]], arm: str) -> dict[int, Mapping[str, Any]]:
    return {int(row["master_seed"]): row for row in rows if row["arm"] == arm}


def _pass(j: float, delta: float, seed_j: Sequence[float], seed_delta: Sequence[float]) -> bool:
    stable = sum(float(a) >= 0.75 and float(b) >= 0.20 for a, b in zip(seed_j, seed_delta))
    return bool(j >= 0.80 and delta >= 0.25 and stable >= 7)


def _null(j: float, delta: float, seed_j: Sequence[float]) -> bool:
    stable = sum(float(value) <= 0.65 for value in seed_j)
    return bool(j <= 0.60 and delta <= 0.10 and stable >= 7)


def _reset_kernel_evidence(eval_sidecar: Path) -> dict[str, Any]:
    reset_rows = [row for row in _read_jsonl_gz(eval_sidecar) if row["arm"] == COMPLETE_RESET]
    groups: dict[tuple[int, int], dict[int, Mapping[str, Any]]] = {}
    for row in reset_rows:
        groups.setdefault((int(row["master_seed"]), int(row["root"])), {})[int(row["bit"])] = row
    complete_pairs = len(groups) == len(reset_rows) // 2 and all(set(pair) == {0, 1} for pair in groups.values())
    exact = complete_pairs
    uniform_exact = complete_pairs
    first_mismatch: dict[str, Any] | None = None
    for key, pair in groups.items():
        if set(pair) != {0, 1}:
            exact = False
            uniform_exact = False
            first_mismatch = {"seed_root": list(key), "reason": "missing_bit_pair"}
            break
        p0 = pair[0]["post_event_kernel"]
        p1 = pair[1]["post_event_kernel"]
        if _canonical_bytes(p0) != _canonical_bytes(p1):
            exact = False
            first_mismatch = {"seed_root": list(key), "reason": "kernel_bytes_differ"}
            break
        if float(pair[0]["action_uniform"]) != float(pair[1]["action_uniform"]):
            uniform_exact = False
            first_mismatch = {"seed_root": list(key), "reason": "uniform_differs"}
            break
    b0 = [int(row["action"] == 1) for row in reset_rows if int(row["bit"]) == 0]
    b1 = [int(row["action"] == 1) for row in reset_rows if int(row["bit"]) == 1]
    dependence = abs(float(np.mean(b1)) - float(np.mean(b0)))
    return {
        "matched_root_pairs": len(groups),
        "complete_bit_pairs": complete_pairs,
        "exact_complete_kernel_equality": exact,
        "paired_action_uniform_equality": uniform_exact,
        "empirical_absolute_action_dependence_on_bit": dependence,
        "first_mismatch": first_mismatch,
    }


def analyze(*, output_root: str | Path, result_path: str | Path | None = None) -> dict[str, Any]:
    root = Path(output_root)
    evaluation = validate_evaluation(root, require_full=None)
    train_summary = _read_json(root / "train_summary.json")
    config = evaluation["config"]
    technical_only = bool(config["technical_only"])
    eval_maps = {arm: _seed_map(evaluation["arm_runs"], arm) for arm in ARMS}
    seedwise: list[dict[str, Any]] = []
    for seed in config["master_seeds"]:
        reset = float(eval_maps[COMPLETE_RESET][int(seed)]["mean_return"])
        s03 = float(eval_maps[S03_KEEP][int(seed)]["mean_return"])
        latch = float(eval_maps[ONE_BIT_OWNER_EPOCH_LATCH][int(seed)]["mean_return"])
        seedwise.append(
            {
                "master_seed": int(seed),
                "J_S03_KEEP": s03,
                "J_COMPLETE_RESET": reset,
                "J_ONE_BIT_OWNER_EPOCH_LATCH": latch,
                "Delta_S": s03 - reset,
                "Delta_L": latch - reset,
                "G": s03 - latch,
            }
        )
    j = {
        arm: float(np.mean([row["mean_return"] for row in eval_maps[arm].values()]))
        for arm in ARMS
    }
    delta_s = j[S03_KEEP] - j[COMPLETE_RESET]
    delta_l = j[ONE_BIT_OWNER_EPOCH_LATCH] - j[COMPLETE_RESET]
    g = j[S03_KEEP] - j[ONE_BIT_OWNER_EPOCH_LATCH]
    reset_kernel = _reset_kernel_evidence(root / "eval_episodes.jsonl.gz")
    reset_seed_values = [row["J_COMPLETE_RESET"] for row in seedwise]
    reset_valid = bool(
        0.47 <= j[COMPLETE_RESET] <= 0.53
        and sum(0.44 <= value <= 0.56 for value in reset_seed_values) >= 7
        and reset_kernel["empirical_absolute_action_dependence_on_bit"] <= 0.06
        and reset_kernel["exact_complete_kernel_equality"]
        and reset_kernel["paired_action_uniform_equality"]
    )
    s03_values = [row["J_S03_KEEP"] for row in seedwise]
    latch_values = [row["J_ONE_BIT_OWNER_EPOCH_LATCH"] for row in seedwise]
    delta_s_values = [row["Delta_S"] for row in seedwise]
    delta_l_values = [row["Delta_L"] for row in seedwise]
    pass_s03 = _pass(j[S03_KEEP], delta_s, s03_values, delta_s_values)
    pass_latch = _pass(j[ONE_BIT_OWNER_EPOCH_LATCH], delta_l, latch_values, delta_l_values)
    null_s03 = _null(j[S03_KEEP], delta_s, s03_values)
    null_latch = _null(j[ONE_BIT_OWNER_EPOCH_LATCH], delta_l, latch_values)
    if technical_only:
        decision = "TECHNICAL_SMOKE_ONLY"
    elif not reset_valid:
        decision = "BIT_LEAK_OR_SHORTCUT"
    elif pass_s03 and pass_latch:
        decision = "S03_LEARNED_USE_WITH_GENERIC_CAPACITY_CONFIRMED"
    elif pass_s03 and null_latch:
        decision = "S03_LEARNED_USE_LATCH_ANOMALY"
    elif null_s03 and pass_latch:
        decision = "GENERIC_MEMORY_ONLY_AT_CAP"
    elif null_s03 and null_latch:
        decision = "LEARNABILITY_CONTROL_FAILED"
    else:
        decision = "INDETERMINATE_AT_CAP"
    curves = {
        f"{row['arm']}:{row['master_seed']}": {
            "values": row["training_return_curve"],
            "normalized_auc": _normalized_auc(row["training_return_curve"]),
            "definition": "trapezoid over batch means divided by batches_minus_one",
        }
        for row in train_summary["arm_runs"]
    }
    per_bit = {
        f"{row['arm']}:{row['master_seed']}": {
            "return": row["per_bit_return"],
            "correct_action_probability": row["per_bit_correct_action_probability"],
            "action_one_probability": row["per_bit_action_one_probability"],
        }
        for row in evaluation["arm_runs"]
    }
    train_counts = train_summary["activity_counts"]
    eval_counts = evaluation["activity_counts"]
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "FOLR_B1_RESULT",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "run_id": evaluation["run_id"],
        "source_commit": evaluation["source_commit"],
        "technical_only": technical_only,
        "scientific_terminal_admitted": not technical_only,
        "decision": decision,
        "config": config,
        "estimands": {
            "J": j,
            "Delta_S": delta_s,
            "Delta_L": delta_l,
            "G": g,
        },
        "seedwise_paired_contrasts": seedwise,
        "thresholds": {
            "PASS_S03_KEEP": pass_s03,
            "NULL_S03_KEEP": null_s03,
            "PASS_ONE_BIT_OWNER_EPOCH_LATCH": pass_latch,
            "NULL_ONE_BIT_OWNER_EPOCH_LATCH": null_latch,
            "RESET_VALID": reset_valid,
            "definition": {
                "PASS": "J>=0.80 and paired_delta>=0.25 and >=7/8 seeds J>=0.75 and delta>=0.20",
                "NULL": "J<=0.60 and delta<=0.10 and >=7/8 seeds J<=0.65",
                "RESET_VALID": "J_reset in [0.47,0.53], >=7/8 seeds in [0.44,0.56], action dependence<=0.06, exact paired kernels",
            },
        },
        "reset_evidence": reset_kernel,
        "per_bit_metrics": per_bit,
        "training_curves_and_auc": curves,
        "activity_counts": {
            "actor_runs": train_counts["actor_runs"],
            "train_episodes": train_counts["train_episodes"],
            "eval_episodes": eval_counts["eval_episodes"],
            "total_episodes": train_counts["train_episodes"] + eval_counts["eval_episodes"],
            "train_environment_transitions": train_counts["environment_transitions"],
            "eval_environment_transitions": eval_counts["environment_transitions"],
            "total_environment_transitions": train_counts["environment_transitions"] + eval_counts["environment_transitions"],
            "train_policy_calls": train_counts["policy_calls"],
            "eval_policy_calls": eval_counts["policy_calls"],
            "total_policy_calls": train_counts["policy_calls"] + eval_counts["policy_calls"],
            "learner_calls": train_counts["learner_calls"],
            "trainer_calls": train_counts["trainer_calls"],
            "optimizer_updates": train_counts["optimizer_updates"],
            "k_search": 0,
            "hypothetical_transitions": 0,
        },
        "artifacts": {
            "manifest": train_summary["manifest"],
            "train_sidecar": train_summary["train_sidecar"],
            "eval_sidecar": evaluation["eval_sidecar"],
            "train_summary_sha256": _sha256_file(root / "train_summary.json"),
            "evaluation_summary_sha256": _sha256_file(root / "evaluation_summary.json"),
            "checkpoints": [row["checkpoint"] for row in train_summary["arm_runs"]],
        },
        "fidelity": train_summary["fidelity"],
        "exclusions": EXCLUSIONS,
        "decision_precedence": list(DECISIONS),
        "claim_boundary": (
            "Only learned return-bearing owner_t@0 memory use in this exact two-transition "
            "host and finite seed panel; no cross-task/epoch generalization, delayed-credit, "
            "coordination, sample-efficiency, typed-memory superiority, promotion, C, or formal claim."
        ),
    }
    destination = Path(result_path) if result_path is not None else root / "raw_result.json"
    _write_json(destination, result)
    _status(root, phase="analyze", state="COMPLETE", detail={"decision": decision})
    validate_result(destination, require_full=not technical_only)
    return result


def _validate_binding(root: Path, binding: Mapping[str, Any]) -> Path:
    path = root / str(binding["path"])
    if not path.is_file():
        raise ValueError(f"bound artifact is absent: {path}")
    if path.stat().st_size != int(binding["size_bytes"]):
        raise ValueError(f"bound artifact size mismatch: {path}")
    if _sha256_file(path) != binding["sha256"]:
        raise ValueError(f"bound artifact SHA mismatch: {path}")
    return path


def _expected_train_counts(config: Mapping[str, Any]) -> dict[str, int]:
    actor_runs = len(config["arms"]) * len(config["master_seeds"])
    episodes = actor_runs * int(config["batches"]) * int(config["batch_size"])
    updates = actor_runs * int(config["batches"])
    return {
        "actor_runs": actor_runs,
        "train_episodes": episodes,
        "environment_transitions": episodes * 2,
        "policy_calls": episodes * 2,
        "learner_calls": updates,
        "trainer_calls": updates,
        "optimizer_updates": updates,
        "k_search": 0,
        "hypothetical_transitions": 0,
    }


def _config_matches_registered(config: Mapping[str, Any]) -> bool:
    return dict(config) == registered_config().to_json()


def _config_matches_smoke(config: Mapping[str, Any]) -> bool:
    return dict(config) == technical_smoke_config().to_json()


def _validate_episode_fidelity(row: Mapping[str, Any]) -> None:
    arm = str(row["arm"])
    if arm not in ARMS or int(row["policy_calls"]) != 2 or int(row["environment_transitions"]) != 2:
        raise ValueError("episode arm/activity drift")
    tx = row["membership_transaction"]
    if (
        not tx["typed_transaction"]
        or not tx["exact_deltas"]
        or tx["pre_keys"] != [OWNER_KEY, "inert_q0"]
        or tx["post_keys"] != [OWNER_KEY, "inert_q1"]
        or tx["owner_status_before"] != "ACTIVE"
        or tx["owner_status_after"] != "ACTIVE"
        or int(tx["owner_epoch_before"]) != OWNER_EPOCH
        or int(tx["owner_epoch_after"]) != OWNER_EPOCH
    ):
        raise ValueError("typed transaction/owner epoch witness failed")
    if tx["owner_s03_digest_before"] != tx["owner_s03_digest_after_commit"]:
        raise ValueError("membership commit mutated owner S03")
    if (
        not tx["same_owner_record_through_commit"]
        or not tx["same_s03_carrier_through_commit"]
        or not tx["choice_reads_committed_registered_s03"]
        or tx["second_information_bearing_s03_carrier"]
    ):
        raise ValueError("registered S03 authority did not cross the typed commit directly")
    if tx["owner_non_s03_digest_before_backend"] != tx["owner_non_s03_digest_after_backend"]:
        raise ValueError("memory backend changed non-S03 owner state")
    if bool(tx["complete_reset_applied"]) != (arm == COMPLETE_RESET):
        raise ValueError("complete-reset backend witness drift")
    if not tx["latch_bound_exactly_to_owner_epoch"]:
        raise ValueError("one-bit latch owner/epoch witness failed")
    cue = row["cue"]
    if not cue["cue_writer_called"] or bool(cue["s03_write_effective"]) != (arm != ONE_BIT_OWNER_EPOCH_LATCH):
        raise ValueError("ordinary cue writer/backend routing witness failed")
    if "bit" in cue["public_view"] or "bit" in row["choice_public_view"]:
        raise ValueError("private bit leaked into a public view")
    if cue["public_view"]["legal_mask"] != [True] or row["choice_public_view"]["legal_mask"] != [True, True]:
        raise ValueError("frozen legal masks drifted")
    backend = row["backend"]
    if (
        backend["arm"] != arm
        or backend["registered_s03_field"] != "LifecycleRecord.high_hidden"
        or not backend["single_tensor_backed_s03_authority"]
        or backend["differentiable_owner_epoch_mirror"]
        or backend["second_information_bearing_s03_carrier"]
        or backend["latch_fields"] != ["lifecycle_key", "membership_epoch", "bit"]
        or backend["latch_extra_fields"] != []
    ):
        raise ValueError("memory backend schema drift")
    if row["update_between_cue_and_choice"] or row["cached_choice_path"] or row["public_bit_input"] or row["bit_correlated_rng"]:
        raise ValueError("freshness/shortcut witness failed")
    kernel = row["post_event_kernel"]
    probabilities = np.asarray(kernel["probabilities"], dtype=np.float64)
    logits = np.asarray(kernel["logits"], dtype=np.float64)
    if (
        tuple(probabilities.shape) != (2,)
        or tuple(logits.shape) != (2,)
        or not np.all(np.isfinite(probabilities))
        or not np.all(np.isfinite(logits))
        or np.any(probabilities < 0.0)
        or abs(float(probabilities.sum()) - 1.0) > 1e-6
        or not kernel["complete"]
        or not kernel["captured_before_sampling"]
    ):
        raise ValueError("complete numerical pre-sampling kernel witness failed")
    if int(row["action"]) not in (0, 1) or float(row["reward"]) not in (0.0, 1.0):
        raise ValueError("terminal action/reward is invalid")
    if not row["terminal"]["terminated"] or not row["terminal"]["memory_cleared"] or not row["terminal"]["latch_expired"]:
        raise ValueError("episode memory did not expire")


def _manifest_fields_equal(row: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
    fields = ("master_seed", "phase", "episode", "batch", "root", "bit", "action_uniform", "rng_identity")
    return all(_canonical_bytes(row[field]) == _canonical_bytes(expected[field]) for field in fields)


def validate_train(output_root: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root)
    summary = _read_json(root / "train_summary.json")
    if summary.get("artifact_kind") != "FOLR_B1_TRAIN_SUMMARY" or summary.get("raw_output_binding") != RAW_OUTPUT_BINDING:
        raise ValueError("train summary schema/binding mismatch")
    config = summary["config"]
    if require_full is True and not _config_matches_registered(config):
        raise ValueError("full train artifact does not match registered configuration")
    if require_full is False and not _config_matches_smoke(config):
        raise ValueError("technical train artifact does not match frozen smoke configuration")
    if require_full is None and not (_config_matches_registered(config) or _config_matches_smoke(config)):
        raise ValueError("train artifact is neither registered full nor frozen technical smoke")
    if tuple(config["arms"]) != ARMS or int(config["transitions_per_episode"]) != 2 or int(config["policy_calls_per_episode"]) != 2:
        raise ValueError("host/arm/call roster drift")
    if int(config["zeros_per_batch"]) != int(config["ones_per_batch"]) or int(config["batch_size"]) != int(config["zeros_per_batch"]) + int(config["ones_per_batch"]):
        raise ValueError("batch balance drift")
    if summary["activity_counts"] != _expected_train_counts(config):
        raise ValueError("train activity counts drift")
    manifest_path = _validate_binding(root, summary["manifest"])
    manifest = _read_json(manifest_path)
    content = dict(manifest)
    declared = content.pop("content_sha256")
    if hashlib.sha256(_canonical_bytes(content)).hexdigest() != declared:
        raise ValueError("frozen manifest content digest mismatch")
    if manifest["config"] != config or not manifest["paired_across_arms"]:
        raise ValueError("manifest/config/matching drift")
    if manifest["model_contract"]["parameter_schema"] != summary["parameter_schema"]:
        raise ValueError("pre-frozen model parameter order/shape drift")
    expected_rows = {
        (arm, int(seed), int(row["episode"])): row
        for arm in config["arms"]
        for seed in config["master_seeds"]
        for batch in manifest["training"][str(seed)]
        for row in batch
    }
    sidecar = _validate_binding(root, summary["train_sidecar"])
    rows = 0
    batches: dict[tuple[str, int, int], int] = {}
    seen: set[tuple[str, int, int]] = set()
    for row in _read_jsonl_gz(sidecar):
        rows += 1
        _validate_episode_fidelity(row)
        identity = (str(row["arm"]), int(row["master_seed"]), int(row["episode"]))
        if identity in seen or identity not in expected_rows or not _manifest_fields_equal(row, expected_rows[identity]):
            raise ValueError("training sidecar/manifest synchronization failed")
        seen.add(identity)
        key = (str(row["arm"]), int(row["master_seed"]), int(row["batch"]))
        batches[key] = batches.get(key, 0) + 1
    if rows != int(summary["train_sidecar"]["rows"]):
        raise ValueError("train sidecar row count mismatch")
    if set(batches.values()) != {int(config["batch_size"])}:
        raise ValueError("train sidecar batch completeness mismatch")
    if seen != set(expected_rows):
        raise ValueError("training sidecar does not cover the complete frozen manifest")
    if summary["exclusions"] != EXCLUSIONS:
        raise ValueError("frozen exclusions drift")
    boolean_fidelity = {key: value for key, value in summary["fidelity"].items() if key != "latch_schema_exact"}
    if not all(value is True for value in boolean_fidelity.values()) or summary["fidelity"]["latch_schema_exact"] != ["lifecycle_key", "membership_epoch", "bit"]:
        raise ValueError("fidelity summary drift")
    if len(summary["arm_runs"]) != int(summary["activity_counts"]["actor_runs"]):
        raise ValueError("actor-run summary is incomplete")
    schema = summary["parameter_schema"]
    initialization: dict[int, str] = {}
    for run in summary["arm_runs"]:
        seed = int(run["master_seed"])
        prior = initialization.setdefault(seed, run["initial_model_digest"])
        if prior != run["initial_model_digest"]:
            raise ValueError("matched initialization drift")
        if run["initial_model_digest"] != manifest["model_contract"]["initialization_digests_by_master_seed"][str(seed)]:
            raise ValueError("run initialization differs from frozen manifest")
        checkpoint = _validate_binding(root / "checkpoints", run["checkpoint"])
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if payload["parameter_schema"] != schema or payload["arm"] != run["arm"] or int(payload["master_seed"]) != seed:
            raise ValueError("checkpoint identity/schema drift")
        if not payload["final_checkpoint_only"] or int(payload["updates"]) != int(config["batches"]):
            raise ValueError("checkpoint selection/update count drift")
    return summary


def validate_evaluation(output_root: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    root = Path(output_root)
    summary = _read_json(root / "evaluation_summary.json")
    train_summary = validate_train(root, require_full=require_full)
    if summary.get("artifact_kind") != "FOLR_B1_EVALUATION_SUMMARY" or summary.get("raw_output_binding") != RAW_OUTPUT_BINDING:
        raise ValueError("evaluation summary schema/binding mismatch")
    if summary["config"] != train_summary["config"] or not summary["paired_manifest_across_arms"]:
        raise ValueError("evaluation config/manifest mismatch")
    config = summary["config"]
    expected_episodes = len(config["arms"]) * len(config["master_seeds"]) * int(config["eval_episodes"])
    expected = {
        "eval_episodes": expected_episodes,
        "environment_transitions": expected_episodes * 2,
        "policy_calls": expected_episodes * 2,
        "learner_calls": 0,
        "trainer_calls": 0,
        "optimizer_updates": 0,
    }
    if summary["activity_counts"] != expected or summary["updates_enabled"] or summary["interventions_enabled"]:
        raise ValueError("evaluation activity/update/intervention drift")
    sidecar = _validate_binding(root, summary["eval_sidecar"])
    rows = list(_read_jsonl_gz(sidecar))
    if len(rows) != expected_episodes:
        raise ValueError("evaluation sidecar row count mismatch")
    manifest = _read_json(root / "frozen_manifest.json")
    expected_rows = {
        (arm, int(seed), int(row["episode"])): row
        for arm in config["arms"]
        for seed in config["master_seeds"]
        for row in manifest["evaluation"][str(seed)]
    }
    seen: set[tuple[str, int, int]] = set()
    public_by_root: dict[tuple[int, int], tuple[bytes, bytes, str, str]] = {}
    for row in rows:
        if row["phase"] != "evaluate" or row["updates_enabled"] or row["interventions_enabled"]:
            raise ValueError("evaluation row is not frozen/no-update")
        _validate_episode_fidelity(row)
        identity = (str(row["arm"]), int(row["master_seed"]), int(row["episode"]))
        if identity in seen or identity not in expected_rows or not _manifest_fields_equal(row, expected_rows[identity]):
            raise ValueError("evaluation sidecar/manifest synchronization failed")
        seen.add(identity)
        root_identity = (int(row["master_seed"]), int(row["root"]))
        public = (
            _canonical_bytes(row["cue"]["public_view"]),
            _canonical_bytes(row["choice_public_view"]),
            str(row["membership_transaction"]["public_pre_digest"]),
            str(row["membership_transaction"]["public_post_digest"]),
        )
        prior = public_by_root.setdefault(root_identity, public)
        if prior != public:
            raise ValueError("matched public view depends on bit or arm")
    if seen != set(expected_rows):
        raise ValueError("evaluation sidecar does not cover the complete frozen manifest")
    return summary


def validate_result(result_path: str | Path, *, require_full: bool | None) -> dict[str, Any]:
    path = Path(result_path)
    result = _read_json(path)
    if result.get("artifact_kind") != "FOLR_B1_RESULT" or result.get("raw_output_binding") != RAW_OUTPUT_BINDING:
        raise ValueError("result schema/binding mismatch")
    technical = bool(result["technical_only"])
    if require_full is True:
        if technical or not result["scientific_terminal_admitted"] or not _config_matches_registered(result["config"]):
            raise ValueError("result is not an admitted registered full artifact")
        if result["decision"] not in DECISIONS:
            raise ValueError("full result decision is outside frozen precedence")
        expected = {
            "actor_runs": 24,
            "train_episodes": 49152,
            "eval_episodes": 12288,
            "total_episodes": 61440,
            "train_environment_transitions": 98304,
            "eval_environment_transitions": 24576,
            "total_environment_transitions": 122880,
            "train_policy_calls": 98304,
            "eval_policy_calls": 24576,
            "total_policy_calls": 122880,
            "learner_calls": 768,
            "trainer_calls": 768,
            "optimizer_updates": 768,
            "k_search": 0,
            "hypothetical_transitions": 0,
        }
        if result["activity_counts"] != expected:
            raise ValueError("registered result counts drift")
    if require_full is False and (not technical or result["scientific_terminal_admitted"] or result["decision"] != "TECHNICAL_SMOKE_ONLY"):
        raise ValueError("technical smoke result crossed scientific terminal")
    if result["exclusions"] != EXCLUSIONS or result["decision_precedence"] != list(DECISIONS):
        raise ValueError("result exclusions/precedence drift")
    values = list(result["estimands"]["J"].values()) + [
        result["estimands"]["Delta_S"],
        result["estimands"]["Delta_L"],
        result["estimands"]["G"],
    ]
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("result contains a non-finite estimand")
    return result


def summarize_artifacts(output_root: str | Path) -> dict[str, Any]:
    root = Path(output_root)
    return {
        "train": validate_train(root, require_full=None),
        "evaluation": validate_evaluation(root, require_full=None),
        "result": validate_result(root / "raw_result.json", require_full=None),
    }
