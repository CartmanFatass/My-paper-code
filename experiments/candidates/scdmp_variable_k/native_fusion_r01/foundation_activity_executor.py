"""CLOSED-R01 foundation activity executor and address-stable primitives."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import tempfile
from typing import Final, Mapping

import torch
from torch import Tensor, nn

from .contract import EventOrder, TaskState, decode_action, public_observation
from .foundation_activity_contract import update_allocation
from .foundation_network import TechnicalFoundation, build_technical_foundation
from .foundation_optimizer import (
    build_adamw,
    clip_global_gradients,
    duration_correct_batch,
    fisher_yates_fixture,
    partition_permutation,
    ppo_losses,
)
from .foundation_run_manifest import (
    HMAC_DOMAINS,
    NAMESPACE_PREFIX,
    canonical_json_bytes,
)


_DOMAIN_SET: Final[frozenset[str]] = frozenset(HMAC_DOMAINS)


def foundation_namespace(replicate_index: int) -> str:
    if (
        isinstance(replicate_index, bool)
        or not isinstance(replicate_index, int)
        or not 0 <= replicate_index < 24
    ):
        raise ValueError("replicate_index must be in [0,24)")
    return f"{NAMESPACE_PREFIX}/{replicate_index.to_bytes(4, 'big').hex()}"


class AddressBook:
    def __init__(self, *, master: bytes, registered: bool) -> None:
        if not isinstance(master, bytes) or len(master) != 32:
            raise ValueError("master must contain exactly 256 bits")
        if not isinstance(registered, bool):
            raise TypeError("registered must be bool")
        self._master = master
        self.registered = registered

    def digest(
        self, domain: str, replicate_index: int, *coordinates: int
    ) -> bytes:
        if domain not in _DOMAIN_SET:
            raise ValueError("HMAC domain is not registered by CLOSED R01")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            for value in coordinates
        ):
            raise ValueError("address coordinates must be nonnegative integers")
        namespace = foundation_namespace(replicate_index)
        coordinate_bytes = b"/".join(
            str(value).encode("ascii") for value in coordinates
        )
        message = (
            domain.encode("ascii")
            + b"\0"
            + namespace.encode("ascii")
            + b"\0"
            + coordinate_bytes
        )
        return hmac.new(self._master, message, hashlib.sha256).digest()

    def uniform(
        self, domain: str, replicate_index: int, *coordinates: int
    ) -> float:
        digest = self.digest(domain, replicate_index, *coordinates)
        return int.from_bytes(digest[:8], "big") / float(1 << 64)


@dataclass(frozen=True)
class ExecutionProfile:
    replicate_count: int
    update_count: int
    registered_required: bool

    @classmethod
    def production(cls) -> "ExecutionProfile":
        return cls(24, 192, True)

    @classmethod
    def technical_single_foundation(cls) -> "ExecutionProfile":
        return cls(1, 1, False)

    @classmethod
    def technical(cls, *, replicates: int, updates: int) -> "ExecutionProfile":
        if (
            isinstance(replicates, bool)
            or not isinstance(replicates, int)
            or not 1 <= replicates <= 24
            or isinstance(updates, bool)
            or not isinstance(updates, int)
            or not 1 <= updates <= 192
        ):
            raise ValueError("technical profile is outside the CLOSED-R01 maxima")
        return cls(replicates, updates, False)


@dataclass
class FoundationRuntime:
    replicate_index: int
    foundation: TechnicalFoundation
    optimizer: torch.optim.AdamW
    completed_updates: int = 0
    global_one_based_step: int = 0


@dataclass(frozen=True)
class FoundationUpdateEvidence:
    replicate_index: int
    update_index: int
    episodes: int
    allocated_primitive_slots: int
    integrated_primitive_ticks: int
    policy_queries: int
    adamw_steps: int
    episode_balance: dict[str, int]
    immutable_old_state_sha256: str
    updated_state_sha256: str
    registered_identity_present: bool
    question_relevant_value_visible: bool


@dataclass(frozen=True)
class TransactionOutcome:
    status: str
    complete: bool
    checkpoint_count: int
    output_root: str


@dataclass(frozen=True)
class _RenewalRecord:
    observation: Tensor
    action: int
    primitive_rewards: Tensor
    nonterminal: bool
    old_value: float
    next_old_value: float
    old_log_probability: float


def _foundation_sha256(foundation: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, parameter in foundation.named_parameters():
        tensor = parameter.detach().cpu().contiguous()
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(b"\0")
        digest.update(tensor.numpy().tobytes(order="C"))
    return digest.hexdigest()


def _write_json_atomic(path: Path, value: Mapping[str, object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _read_canonical_json(path: Path) -> dict[str, object]:
    payload = Path(path).read_bytes()
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("resume JSON is malformed") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != payload:
        raise RuntimeError("resume JSON is not canonical")
    return value


def _save_runtime_atomic(path: Path, runtime: FoundationRuntime) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        torch.save(
            {
                "replicate_index": runtime.replicate_index,
                "completed_updates": runtime.completed_updates,
                "global_one_based_step": runtime.global_one_based_step,
                "foundation_state": runtime.foundation.state_dict(),
                "optimizer_state": runtime.optimizer.state_dict(),
            },
            temporary,
        )
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _copy_checkpoint_create_only(source: Path, target: Path) -> None:
    temporary_name: str | None = None
    try:
        with source.open("rb") as source_stream, tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", delete=False
        ) as temporary:
            shutil.copyfileobj(source_stream, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.link(temporary_name, target)
    except FileExistsError as exc:
        raise RuntimeError("resume checkpoint slot already exists") from exc
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def _initialize_foundation(
    address_book: AddressBook, replicate_index: int
) -> TechnicalFoundation:
    foundation = build_technical_foundation()
    with torch.no_grad():
        for parameter_index, (name, parameter) in enumerate(
            foundation.named_parameters()
        ):
            if name.endswith("bias"):
                parameter.zero_()
                continue
            if parameter.ndim != 2:
                raise RuntimeError("foundation affine tensor shape differs")
            fan_out, fan_in = parameter.shape
            bound = math.sqrt(6.0 / float(fan_in + fan_out))
            values = [
                (
                    2.0
                    * address_book.uniform(
                        "foundation/initialization",
                        replicate_index,
                        parameter_index,
                        flat_index,
                    )
                    - 1.0
                )
                * bound
                for flat_index in range(parameter.numel())
            ]
            parameter.copy_(
                torch.tensor(values, dtype=torch.float32).reshape_as(parameter)
            )
    return foundation


def _initial_state(
    book: AddressBook,
    *,
    replicate_index: int,
    update_index: int,
    pair_index: int,
    order: str,
) -> TaskState:
    initial_v = 0.04 * book.uniform(
        "foundation/training", replicate_index, update_index, pair_index, 0
    )
    initial_phi = -0.015 + 0.03 * book.uniform(
        "foundation/training", replicate_index, update_index, pair_index, 1
    )
    return TaskState(
        x=0.0,
        v=initial_v,
        phi=initial_phi,
        omega=0.0,
        z=0.0,
        f=0.0,
        tensions=(0.0, 0.0, 0.0),
        previous=(0, 0, 0),
        hidden_d=0.55 if order == EventOrder.RG.value else 0.0,
        mode=1,
        n=0,
    )


def _primitive_step(
    state: TaskState,
    control: tuple[int, int, int],
    *,
    eta_v: float,
    eta_omega: float,
) -> tuple[TaskState, float, bool]:
    old_x = state.x
    mean_command = sum(control) / 3.0
    dispersion = max(abs(value - mean_command) for value in control)
    tensions = tuple(
        0.42
        + 0.17 * value
        + 0.11 * abs(value - mean_command)
        + 0.20 * state.hidden_d * mean_command**2
        + 0.07 * abs(state.phi)
        for value in control
    )
    capacity = 1.04 - 0.16 * state.hidden_d
    excess = max(0.0, max(tensions) - capacity)
    omega = (
        0.90 * state.omega
        - 0.12 * state.phi
        + 0.055 * dispersion
        + 0.035 * state.hidden_d * mean_command
        + eta_omega
    )
    phi = min(0.70, max(-0.70, state.phi + 0.1 * omega))
    velocity = min(
        1.8,
        max(
            0.0,
            0.94 * state.v
            + 0.06 * mean_command
            - 0.018 * state.hidden_d * mean_command**2
            - 0.025 * abs(phi)
            + eta_v,
        ),
    )
    position = state.x + 0.1 * velocity
    overload_state = 0.86 * state.z + excess
    formation_state = 0.84 * state.f + 0.09 * dispersion + 0.08 * abs(phi)
    tick = state.n + 1
    physical_failure = (
        overload_state > 0.55
        or abs(phi) > 0.48
        or formation_state > 0.42
    )
    delivery = not physical_failure and position >= 36.0
    timeout = not physical_failure and not delivery and tick >= 420
    terminal = physical_failure or delivery or timeout
    reward = (
        0.02 * (position - old_x)
        - 0.001 * sum(value * value for value in control) / 3.0
        - 0.002 * phi**2
        - 0.002 * formation_state**2
    )
    reward += 1.0 if delivery else -1.0 if physical_failure else -0.5 if timeout else 0.0
    return (
        TaskState(
            position,
            velocity,
            phi,
            omega,
            overload_state,
            formation_state,
            tensions,
            control,
            state.hidden_d,
            state.mode,
            tick,
        ),
        reward,
        terminal,
    )


class FoundationActivityExecutor:
    def __init__(
        self, *, address_book: AddressBook, profile: ExecutionProfile
    ) -> None:
        if profile.registered_required and not address_book.registered:
            raise PermissionError("production execution requires a registered address book")
        self.address_book = address_book
        self.profile = profile

    def new_runtime(self, *, replicate_index: int) -> FoundationRuntime:
        if not 0 <= replicate_index < self.profile.replicate_count:
            raise ValueError("replicate_index is outside the execution profile")
        foundation = _initialize_foundation(self.address_book, replicate_index)
        return FoundationRuntime(
            replicate_index=replicate_index,
            foundation=foundation,
            optimizer=build_adamw(foundation.parameters()),
        )

    def _episode(
        self,
        runtime: FoundationRuntime,
        *,
        update_index: int,
        slot_index: int,
        k: int,
        order: str,
    ) -> tuple[list[_RenewalRecord], int]:
        pair_index = slot_index % 4
        state = _initial_state(
            self.address_book,
            replicate_index=runtime.replicate_index,
            update_index=update_index,
            pair_index=pair_index,
            order=order,
        )
        records: list[_RenewalRecord] = []
        integrated_ticks = 0
        terminal = False
        renewal_index = 0
        while state.n < 420 and not terminal:
            observation = torch.tensor(
                public_observation(state, k), dtype=torch.float32
            )
            with torch.no_grad():
                logits = runtime.foundation.actor(observation.unsqueeze(0))[0]
                log_probabilities = torch.log_softmax(logits, dim=0)
                probabilities = torch.softmax(logits, dim=0)
                old_value = runtime.foundation.critic(observation.unsqueeze(0))[0]
            uniform = self.address_book.uniform(
                "action/uniforms",
                runtime.replicate_index,
                update_index,
                slot_index,
                renewal_index,
            )
            action = int(
                torch.searchsorted(
                    torch.cumsum(probabilities, dim=0),
                    torch.tensor(uniform, dtype=torch.float32),
                    right=True,
                ).item()
            )
            action = min(action, 26)
            control = decode_action(action)
            rewards: list[float] = []
            for _hold_offset in range(k):
                if state.n >= 420 or terminal:
                    break
                eta_v = (
                    -0.004
                    if self.address_book.uniform(
                        "disturbances",
                        runtime.replicate_index,
                        update_index,
                        pair_index,
                        state.n,
                        0,
                    )
                    < 0.5
                    else 0.004
                )
                eta_omega = (
                    -0.006
                    if self.address_book.uniform(
                        "disturbances",
                        runtime.replicate_index,
                        update_index,
                        pair_index,
                        state.n,
                        1,
                    )
                    < 0.5
                    else 0.006
                )
                state, reward, terminal = _primitive_step(
                    state, control, eta_v=eta_v, eta_omega=eta_omega
                )
                rewards.append(reward)
                integrated_ticks += 1
            nonterminal = not terminal
            if nonterminal:
                next_observation = torch.tensor(
                    public_observation(state, k), dtype=torch.float32
                )
                with torch.no_grad():
                    next_value = runtime.foundation.critic(
                        next_observation.unsqueeze(0)
                    )[0]
            else:
                next_value = torch.tensor(0.0, dtype=torch.float32)
            records.append(
                _RenewalRecord(
                    observation,
                    action,
                    torch.tensor(rewards, dtype=torch.float32),
                    nonterminal,
                    float(old_value.item()),
                    float(next_value.item()),
                    float(log_probabilities[action].item()),
                )
            )
            renewal_index += 1
        return records, integrated_ticks

    def run_next_update(
        self, runtime: FoundationRuntime
    ) -> FoundationUpdateEvidence:
        if runtime.completed_updates >= self.profile.update_count:
            raise RuntimeError("execution profile update budget is complete")
        update_index = runtime.completed_updates + 1
        old_sha = _foundation_sha256(runtime.foundation)
        allocation = update_allocation(update_index)
        records: list[_RenewalRecord] = []
        integrated_ticks = 0
        balance: Counter[str] = Counter()
        for slot in allocation.slots:
            episode_records, episode_ticks = self._episode(
                runtime,
                update_index=update_index,
                slot_index=slot.slot_index,
                k=slot.k,
                order=slot.order,
            )
            records.extend(episode_records)
            integrated_ticks += episode_ticks
            balance[f"k{slot.k}_{slot.order}"] += 1
        observations = torch.stack([record.observation for record in records])
        actions = torch.tensor(
            [record.action for record in records], dtype=torch.int64
        )
        duration_batch = duration_correct_batch(
            primitive_rewards=tuple(record.primitive_rewards for record in records),
            nonterminal=torch.tensor(
                [record.nonterminal for record in records], dtype=torch.bool
            ),
            old_values=torch.tensor(
                [record.old_value for record in records], dtype=torch.float32
            ),
            next_old_values=torch.tensor(
                [record.next_old_value for record in records], dtype=torch.float32
            ),
            old_log_prob=torch.tensor(
                [record.old_log_probability for record in records],
                dtype=torch.float32,
            ),
        )
        adamw_steps = 0
        for epoch in range(4):
            choices = tuple(
                int(
                    self.address_book.uniform(
                        "minibatch/permutations",
                        runtime.replicate_index,
                        update_index,
                        epoch,
                        upper,
                    )
                    * (upper + 1)
                )
                for upper in range(len(records) - 1, 0, -1)
            )
            permutation = fisher_yates_fixture(
                len(records), swap_indices=choices
            )
            for indices in partition_permutation(permutation):
                batch_indices = torch.tensor(indices, dtype=torch.int64)
                batch_observations = observations[batch_indices]
                batch_actions = actions[batch_indices]
                logits = runtime.foundation.actor(batch_observations)
                log_probabilities = torch.log_softmax(logits, dim=1)
                probabilities = torch.softmax(logits, dim=1)
                new_log_probability = log_probabilities.gather(
                    1, batch_actions.unsqueeze(1)
                ).squeeze(1)
                entropy = -torch.sum(probabilities * log_probabilities, dim=1)
                values = runtime.foundation.critic(batch_observations)
                losses = ppo_losses(
                    new_log_prob=new_log_probability,
                    old_log_prob=duration_batch.old_log_prob[batch_indices],
                    normalized_advantage=duration_batch.normalized_advantages[
                        batch_indices
                    ],
                    value=values,
                    target=duration_batch.targets[batch_indices],
                    entropy=entropy,
                )
                runtime.optimizer.zero_grad(set_to_none=True)
                losses.total.backward()
                clip_global_gradients(runtime.foundation.parameters())
                runtime.optimizer.step()
                adamw_steps += 1
        runtime.completed_updates = update_index
        runtime.global_one_based_step += adamw_steps
        return FoundationUpdateEvidence(
            replicate_index=runtime.replicate_index,
            update_index=update_index,
            episodes=16,
            allocated_primitive_slots=16 * 420,
            integrated_primitive_ticks=integrated_ticks,
            policy_queries=len(records),
            adamw_steps=adamw_steps,
            episode_balance=dict(sorted(balance.items())),
            immutable_old_state_sha256=old_sha,
            updated_state_sha256=_foundation_sha256(runtime.foundation),
            registered_identity_present=self.address_book.registered,
            question_relevant_value_visible=False,
        )

    def _load_runtime(self, path: Path, replicate_index: int) -> FoundationRuntime:
        try:
            saved = torch.load(path, map_location="cpu", weights_only=False)
        except (OSError, RuntimeError, ValueError) as exc:
            raise RuntimeError("resume checkpoint is unreadable") from exc
        if (
            not isinstance(saved, Mapping)
            or saved.get("replicate_index") != replicate_index
        ):
            raise RuntimeError("resume checkpoint identity differs")
        runtime = self.new_runtime(replicate_index=replicate_index)
        runtime.foundation.load_state_dict(saved["foundation_state"])
        runtime.optimizer.load_state_dict(saved["optimizer_state"])
        runtime.completed_updates = int(saved["completed_updates"])
        runtime.global_one_based_step = int(saved["global_one_based_step"])
        if (
            not 0 <= runtime.completed_updates <= self.profile.update_count
            or runtime.global_one_based_step != runtime.completed_updates * 16
        ):
            raise RuntimeError("resume checkpoint persistent clock differs")
        return runtime

    def run_transaction(
        self,
        *,
        output_root: Path,
        resume_root: Path,
        run_manifest: Mapping[str, object] | None = None,
        interrupt_after_updates: int | None = None,
    ) -> TransactionOutcome:
        output = Path(output_root).resolve(strict=False)
        resume = Path(resume_root).resolve(strict=False)
        if output.exists():
            raise FileExistsError(output)
        if output == resume or output.parent != resume.parent:
            raise ValueError("output and resume roots must be distinct siblings")
        if interrupt_after_updates is not None:
            if self.address_book.registered:
                raise PermissionError("registered execution has no stopping option")
            if (
                isinstance(interrupt_after_updates, bool)
                or not isinstance(interrupt_after_updates, int)
                or interrupt_after_updates < 1
            ):
                raise ValueError("technical interrupt count must be positive")
        profile_value = {
            "replicate_count": self.profile.replicate_count,
            "update_count": self.profile.update_count,
            "registered_required": self.profile.registered_required,
        }
        fingerprint = self.address_book.digest(
            "foundation/training", 0, 0, 0, 0
        ).hex()
        transaction_id = (
            hashlib.sha256(canonical_json_bytes(run_manifest)).hexdigest()
            if run_manifest is not None
            else hashlib.sha256(
                canonical_json_bytes(
                    {
                        "fixture": "TECHNICAL_NONREGISTERED",
                        "fingerprint": fingerprint,
                        "profile": profile_value,
                    }
                )
            ).hexdigest()
        )
        progress_path = resume / "progress.json"
        runtime_path = resume / "runtime.pt"
        if resume.exists() and progress_path.is_file():
            if not resume.is_dir():
                raise RuntimeError("resume root is incomplete")
            progress = _read_canonical_json(progress_path)
            if (
                progress.get("transaction_id") != transaction_id
                or progress.get("master_fingerprint") != fingerprint
                or progress.get("profile") != profile_value
            ):
                raise RuntimeError("resume identity differs")
        else:
            if resume.exists():
                if (
                    not resume.is_dir()
                    or {path.name for path in resume.iterdir()} != {"master.bin"}
                ):
                    raise RuntimeError("resume root is incomplete")
            else:
                resume.mkdir(parents=True, exist_ok=False)
            progress = {
                "schema": "SCDMP_NATIVE_FUSION_R01_FOUNDATION_RESUME_V1",
                "transaction_id": transaction_id,
                "master_fingerprint": fingerprint,
                "profile": profile_value,
                "current_replicate": 0,
                "evidence_rows": [],
                "checkpoint_rows": [],
                "registered_identity_present": self.address_book.registered,
                "question_relevant_value_visible": False,
            }
            _write_json_atomic(progress_path, progress)
        processed_this_call = 0
        while int(progress["current_replicate"]) < self.profile.replicate_count:
            replicate_index = int(progress["current_replicate"])
            checkpoint_dir = resume / "checkpoints"
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            checkpoint_name = f"foundation-{replicate_index:08d}.pt"
            checkpoint_path = checkpoint_dir / checkpoint_name
            if checkpoint_path.exists():
                if not checkpoint_path.is_file() or checkpoint_path.is_symlink():
                    raise RuntimeError("resume checkpoint slot is not a regular file")
                recovered = self._load_runtime(checkpoint_path, replicate_index)
                if recovered.completed_updates != self.profile.update_count:
                    raise RuntimeError("resume checkpoint is incomplete")
                if (
                    runtime_path.is_file()
                    and hashlib.sha256(runtime_path.read_bytes()).hexdigest()
                    != hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
                ):
                    raise RuntimeError("runtime and checkpoint bytes differ")
            else:
                runtime = (
                    self._load_runtime(runtime_path, replicate_index)
                    if runtime_path.is_file()
                    else self.new_runtime(replicate_index=replicate_index)
                )
                while runtime.completed_updates < self.profile.update_count:
                    evidence = self.run_next_update(runtime)
                    _save_runtime_atomic(runtime_path, runtime)
                    progress["evidence_rows"].append(asdict(evidence))
                    _write_json_atomic(progress_path, progress)
                    processed_this_call += 1
                    if (
                        interrupt_after_updates is not None
                        and processed_this_call >= interrupt_after_updates
                    ):
                        return TransactionOutcome(
                            "INTERRUPTED_FOR_RESUME",
                            False,
                            len(progress["checkpoint_rows"]),
                            output.as_posix(),
                        )
                _copy_checkpoint_create_only(runtime_path, checkpoint_path)
            checkpoint_sha = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
            if any(
                int(row["replicate_index"]) == replicate_index
                for row in progress["checkpoint_rows"]
            ):
                raise RuntimeError("resume checkpoint progress is duplicated")
            progress["checkpoint_rows"].append(
                {
                    "replicate_index": replicate_index,
                    "path": f"checkpoints/{checkpoint_name}",
                    "sha256": checkpoint_sha,
                    "completed_updates": self.profile.update_count,
                    "persistent_step_index": self.profile.update_count * 16,
                    "eligible": self.profile == ExecutionProfile.production(),
                    "technically_accepted": True,
                }
            )
            runtime_path.unlink(missing_ok=True)
            progress["current_replicate"] = replicate_index + 1
            _write_json_atomic(progress_path, progress)

        publication = resume / "publication"
        if publication.exists():
            if publication.resolve().parent != resume:
                raise RuntimeError("publication staging escaped resume root")
            shutil.rmtree(publication)
        (publication / "checkpoints").mkdir(parents=True)
        for row in progress["checkpoint_rows"]:
            source = resume / str(row["path"])
            destination = publication / str(row["path"])
            shutil.copyfile(source, destination)
            if hashlib.sha256(destination.read_bytes()).hexdigest() != row["sha256"]:
                raise RuntimeError("published checkpoint bytes differ")
        evidence_rows = progress["evidence_rows"]
        evidence_document = {
            "schema": "SCDMP_NATIVE_FUSION_R01_FOUNDATION_ACTIVITY_EVIDENCE_V1",
            "complete": True,
            "replicate_count": self.profile.replicate_count,
            "update_count": len(evidence_rows),
            "episode_count": sum(int(row["episodes"]) for row in evidence_rows),
            "allocated_primitive_slots": sum(
                int(row["allocated_primitive_slots"]) for row in evidence_rows
            ),
            "integrated_primitive_ticks": sum(
                int(row["integrated_primitive_ticks"]) for row in evidence_rows
            ),
            "policy_queries": sum(
                int(row["policy_queries"]) for row in evidence_rows
            ),
            "adamw_steps": sum(int(row["adamw_steps"]) for row in evidence_rows),
            "registered_identity_present": self.address_book.registered,
            "question_relevant_value_visible": False,
        }
        checkpoint_document = {
            "schema": "SCDMP_NATIVE_FUSION_R01_FOUNDATION_CHECKPOINT_MANIFEST_V1",
            "complete": True,
            "checkpoints": progress["checkpoint_rows"],
            "checkpoint_count": len(progress["checkpoint_rows"]),
            "question_relevant_value_visible": False,
        }
        terminal_document = {
            "schema": "SCDMP_NATIVE_FUSION_R01_FOUNDATION_TERMINAL_V1",
            "status": "COMPLETE",
            "complete_only": True,
            "rerun_permitted": False,
            "checkpoint_count": len(progress["checkpoint_rows"]),
            "question_relevant_value_visible": False,
        }
        _write_json_atomic(publication / "checkpoint-manifest.json", checkpoint_document)
        _write_json_atomic(publication / "evidence.json", evidence_document)
        _write_json_atomic(publication / "terminal.json", terminal_document)
        if run_manifest is not None:
            _write_json_atomic(publication / "run-manifest.json", run_manifest)
        os.replace(publication, output)
        if resume.exists() and resume.resolve().parent == output.parent:
            shutil.rmtree(resume)
        return TransactionOutcome(
            "COMPLETE",
            True,
            len(progress["checkpoint_rows"]),
            output.as_posix(),
        )


def execute_registered_foundation_activity(
    *,
    manifest_sha256: str,
    output_root: Path,
    run_manifest: Mapping[str, object],
) -> TransactionOutcome:
    if (
        not isinstance(manifest_sha256, str)
        or len(manifest_sha256) != 64
        or any(character not in "0123456789abcdef" for character in manifest_sha256)
    ):
        raise ValueError("manifest_sha256 is invalid")
    output = Path(output_root).resolve(strict=False)
    if output.exists():
        raise FileExistsError(output)
    resume = output.parent / f".{output.name}.resume-{manifest_sha256[:16]}"
    master_path = resume / "master.bin"
    if resume.exists():
        if not master_path.is_file():
            raise RuntimeError("registered resume master is absent")
        master = master_path.read_bytes()
    else:
        resume.mkdir(parents=True, exist_ok=False)
        master = secrets.token_bytes(32)
        descriptor = os.open(
            master_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
            0o600,
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(master)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            master_path.unlink(missing_ok=True)
            raise
    if len(master) != 32:
        raise RuntimeError("registered resume master is malformed")
    executor = FoundationActivityExecutor(
        address_book=AddressBook(master=master, registered=True),
        profile=ExecutionProfile.production(),
    )
    return executor.run_transaction(
        output_root=output,
        resume_root=resume,
        run_manifest=run_manifest,
    )
