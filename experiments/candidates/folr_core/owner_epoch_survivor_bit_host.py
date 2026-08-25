"""Exact two-transition host for FOLR-B1 owner-epoch memory learnability.

This candidate-local adapter deliberately uses the public typed membership DTOs
without invoking :class:`VariableRosterEventCore`: that runtime would add an
event-policy call, critic inference, and an opportunity-gap draw that are not
part of the frozen two-call host.  The adapter performs the same transactional
validation/commit responsibilities needed by this experiment and exposes a
small, auditable lifecycle state surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

import numpy as np
import torch

from ha_ctse_process.variable_roster_event_types import (
    BoundaryMember,
    BoundarySnapshot,
    LifecycleRecord,
    MembershipDelta,
    MembershipTransaction,
)


ACTIVE: Final = "ACTIVE"
TERMINAL: Final = "TERMINAL"
JOIN: Final = "JOIN"
TERMINAL_LEAVE: Final = "TERMINAL_LEAVE"

HOST_IDENTIFIER: Final = "folr_owner_epoch_survivor_bit_v1"
OWNER_KEY: Final = "owner_t"
OWNER_EPOCH: Final = 0
INERT_Q0_KEY: Final = "inert_q0"
INERT_Q1_KEY: Final = "inert_q1"

S03_KEEP: Final = "S03_KEEP"
COMPLETE_RESET: Final = "COMPLETE_RESET"
ONE_BIT_OWNER_EPOCH_LATCH: Final = "ONE_BIT_OWNER_EPOCH_LATCH"
ARMS: Final = (S03_KEEP, COMPLETE_RESET, ONE_BIT_OWNER_EPOCH_LATCH)


def _zeros(size: int) -> np.ndarray:
    return np.zeros(int(size), dtype=np.float32)


def _digest_array(value: np.ndarray | torch.Tensor) -> str:
    import hashlib

    if isinstance(value, torch.Tensor):
        array = value.detach().cpu().contiguous().numpy()
    else:
        array = np.ascontiguousarray(np.asarray(value))
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("utf-8"))
    digest.update(str(tuple(array.shape)).encode("utf-8"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True)
class HostDimensions:
    observation_dim: int = 3
    critic_member_dim: int = 1
    critic_global_dim: int = 1
    memory_dim: int = 8


@dataclass(frozen=True)
class OwnerEpochBitLatch:
    """The whole latch schema: one key, one epoch, and one raw bit."""

    lifecycle_key: str
    membership_epoch: int
    bit: int

    def __post_init__(self) -> None:
        if self.lifecycle_key != OWNER_KEY or int(self.membership_epoch) != OWNER_EPOCH:
            raise ValueError("latch must bind exactly to owner_t@0")
        if int(self.bit) not in (0, 1):
            raise ValueError("latch payload must be one raw bit")

    def project(self, *, memory_dim: int, device: torch.device) -> torch.Tensor:
        # Fixed, parameter-free and invertible for a raw bit.  This is the
        # positive-capacity backend input, not a learned or action-bearing path.
        value = -1.0 if int(self.bit) == 0 else 1.0
        return torch.full((int(memory_dim),), value, dtype=torch.float32, device=device)


@dataclass(frozen=True)
class TransactionWitness:
    typed_transaction: bool
    exact_deltas: bool
    pre_keys: tuple[str, ...]
    post_keys: tuple[str, ...]
    owner_status_before: str
    owner_status_after: str
    owner_epoch_before: int
    owner_epoch_after: int
    owner_s03_digest_before: str
    owner_s03_digest_after_commit: str
    owner_s03_digest_after_backend: str
    owner_non_s03_digest_before_backend: str
    owner_non_s03_digest_after_backend: str
    complete_reset_applied: bool
    latch_bound_exactly_to_owner_epoch: bool
    same_owner_record_through_commit: bool
    same_s03_carrier_through_commit: bool
    choice_reads_committed_registered_s03: bool
    second_information_bearing_s03_carrier: bool
    public_pre_digest: str
    public_post_digest: str


class OwnerEpochSurvivorBitHost:
    """One episode of the frozen host.

    ``LifecycleRecord.high_hidden`` itself is the differentiable owner-private
    state for ``owner_t@0``.  The typed commit retains that exact owner record
    and tensor object.  Digest/serialization views detach only while observing
    bytes; no second information-bearing tensor exists.
    """

    def __init__(self, *, arm: str, root: int, dimensions: HostDimensions) -> None:
        if arm not in ARMS:
            raise ValueError(f"unknown arm {arm!r}")
        self.arm = str(arm)
        self.root = int(root)
        self.dimensions = dimensions
        self.physical_time = 0
        self.records: dict[str, LifecycleRecord] = {
            OWNER_KEY: self._new_record(OWNER_KEY),
            INERT_Q0_KEY: self._new_record(INERT_Q0_KEY),
        }
        self._latch: OwnerEpochBitLatch | None = None
        self._cue_writer_called = False
        self._choice_consumed = False

    def _new_record(self, key: str) -> LifecycleRecord:
        return LifecycleRecord(
            lifecycle_key=str(key),
            status=ACTIVE,
            membership_epoch=0,
            low_actor_hidden=_zeros(0),
            low_critic_hidden=_zeros(0),
            high_hidden=(
                torch.zeros(self.dimensions.memory_dim, dtype=torch.float32)
                if str(key) == OWNER_KEY
                else _zeros(self.dimensions.memory_dim)
            ),
            active_skill=None,
            skill_active_age=0,
            active_gap_remaining=0,
            last_policy_event_time=None,
            open_event_trace=None,
            policy_version=0,
            is_genuine_join=True,
            is_rejoin=False,
        )

    @property
    def owner(self) -> LifecycleRecord:
        return self.records[OWNER_KEY]

    @property
    def latch(self) -> OwnerEpochBitLatch | None:
        return self._latch

    def _public_observation(self) -> np.ndarray:
        # Root is the only varying public quantity; bit is deliberately absent.
        x = ((self.root % 997) / 498.0) - 1.0
        y = (((self.root // 997) % 997) / 498.0) - 1.0
        return np.asarray([x, y, float(self.physical_time)], dtype=np.float32)

    def public_view(self) -> dict[str, object]:
        active = tuple(key for key, row in self.records.items() if row.status == ACTIVE)
        return {
            "physical_time": int(self.physical_time),
            "active_keys": active,
            "observation": self._public_observation().tolist(),
            "legal_mask": [True] if self.physical_time == 0 else [True, True],
        }

    def cue_transition(self, bit: int, cue_activation: torch.Tensor) -> dict[str, object]:
        if self.physical_time != 0 or self._cue_writer_called:
            raise RuntimeError("cue transition may execute exactly once at t=0")
        if int(bit) not in (0, 1):
            raise ValueError("private cue must be one bit")
        activation = (
            cue_activation
            if tuple(cue_activation.shape) == (self.dimensions.memory_dim,)
            else cue_activation.reshape(-1)
        )
        if tuple(activation.shape) != (self.dimensions.memory_dim,):
            raise ValueError("cue activation has the wrong S03 shape")
        if not bool(torch.isfinite(activation).all()):
            raise ValueError("cue activation is non-finite")
        self._cue_writer_called = True
        if self.arm in (S03_KEEP, COMPLETE_RESET):
            self.owner.high_hidden = activation
        else:
            # The ordinary writer is called, but this backend keeps registered
            # S03 neutral and stores only the raw owner/epoch bit.
            self.owner.high_hidden = torch.zeros_like(activation)
            self._latch = OwnerEpochBitLatch(OWNER_KEY, OWNER_EPOCH, int(bit))
        before = self.public_view()
        self.physical_time = 1
        return {
            "transition": 1,
            "legal_actions": ["WAIT"],
            "action": "WAIT",
            "reward": 0.0,
            "cue_writer_called": True,
            "cue_activation_digest": _digest_array(activation),
            "s03_write_effective": self.arm in (S03_KEEP, COMPLETE_RESET),
            "public_view": before,
        }

    def _member(self, key: str) -> BoundaryMember:
        row = self.records[key]
        return BoundaryMember.make(
            key,
            row.membership_epoch,
            self._public_observation(),
            _zeros(self.dimensions.critic_member_dim),
            obs_dim=self.dimensions.observation_dim,
            critic_member_dim=self.dimensions.critic_member_dim,
        )

    def replacement_transaction(self) -> MembershipTransaction:
        if self.physical_time != 1:
            raise RuntimeError("replacement transaction belongs between the two transitions")
        pre = BoundarySnapshot.make(
            self.physical_time,
            (self._member(OWNER_KEY), self._member(INERT_Q0_KEY)),
            _zeros(self.dimensions.critic_global_dim),
            critic_global_dim=self.dimensions.critic_global_dim,
            frontier=(),
        )
        # The post snapshot is constructed independently, as an environment DTO,
        # and checked against the simulated lifecycle result during commit.
        q1 = BoundaryMember.make(
            INERT_Q1_KEY,
            0,
            self._public_observation(),
            _zeros(self.dimensions.critic_member_dim),
            obs_dim=self.dimensions.observation_dim,
            critic_member_dim=self.dimensions.critic_member_dim,
        )
        post = BoundarySnapshot.make(
            self.physical_time,
            (self._member(OWNER_KEY), q1),
            _zeros(self.dimensions.critic_global_dim),
            critic_global_dim=self.dimensions.critic_global_dim,
            frontier=(INERT_Q1_KEY,),
        )
        return MembershipTransaction(
            pre_membership_boundary_snapshot=pre,
            atomic_membership_delta=(
                MembershipDelta(TERMINAL_LEAVE, INERT_Q0_KEY, 0),
                MembershipDelta(JOIN, INERT_Q1_KEY, 0),
            ),
            post_membership_pre_policy_snapshot=post,
        )

    @staticmethod
    def _snapshot_digest(snapshot: BoundarySnapshot) -> str:
        import hashlib
        import json

        data = {
            "physical_time": int(snapshot.physical_time),
            "frontier": list(snapshot.frontier),
            "members": [
                {
                    "key": row.lifecycle_key,
                    "epoch": int(row.membership_epoch),
                    "observation": row.observation.tolist(),
                    "critic": row.critic_member_features.tolist(),
                }
                for row in snapshot.members
            ],
            "global": snapshot.critic_global_features.tolist(),
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _non_s03_owner_digest(record: LifecycleRecord) -> str:
        import hashlib
        import json

        value = {
            "lifecycle_key": record.lifecycle_key,
            "status": record.status,
            "membership_epoch": int(record.membership_epoch),
            "low_actor_hidden": record.low_actor_hidden.tolist(),
            "low_critic_hidden": record.low_critic_hidden.tolist(),
            "active_skill": record.active_skill,
            "skill_active_age": int(record.skill_active_age),
            "active_gap_remaining": record.active_gap_remaining,
            "last_policy_event_time": record.last_policy_event_time,
            "open_event_trace": record.open_event_trace is not None,
            "policy_version": int(record.policy_version),
            "is_genuine_join": bool(record.is_genuine_join),
            "is_rejoin": bool(record.is_rejoin),
        }
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def apply_replacement(self, transaction: MembershipTransaction) -> TransactionWitness:
        if not isinstance(transaction, MembershipTransaction):
            raise TypeError("replacement must use the typed MembershipTransaction")
        expected_deltas = ((TERMINAL_LEAVE, INERT_Q0_KEY, 0), (JOIN, INERT_Q1_KEY, 0))
        actual_deltas = tuple(
            (row.kind, row.lifecycle_key, int(row.expected_membership_epoch))
            for row in transaction.atomic_membership_delta
        )
        if actual_deltas != expected_deltas:
            raise ValueError("replacement transaction does not contain the frozen atomic deltas")
        pre = transaction.pre_membership_boundary_snapshot
        post = transaction.post_membership_pre_policy_snapshot
        if pre.keys != (OWNER_KEY, INERT_Q0_KEY) or post.keys != (OWNER_KEY, INERT_Q1_KEY):
            raise ValueError("transaction active rosters differ from the frozen host")
        if int(pre.physical_time) != self.physical_time or int(post.physical_time) != self.physical_time:
            raise ValueError("transaction time does not match host time")
        for member in pre.members:
            current = self.records.get(member.lifecycle_key)
            if current is None or current.status != ACTIVE:
                raise ValueError("pre snapshot references a non-active lifecycle")
            if int(current.membership_epoch) != int(member.membership_epoch):
                raise ValueError("pre snapshot carries a stale membership epoch")

        owner_before = self.owner
        owner_record_identity_before = id(owner_before)
        owner_s03_carrier_identity_before = id(owner_before.high_hidden)
        owner_status_before = str(owner_before.status)
        owner_epoch_before = int(owner_before.membership_epoch)
        q0 = self.records[INERT_Q0_KEY].clone()
        q0.status = TERMINAL
        q0.high_hidden = _zeros(0)
        q0.low_actor_hidden = _zeros(0)
        q0.low_critic_hidden = _zeros(0)
        q0.active_skill = None
        q0.active_gap_remaining = None
        q1 = self._new_record(INERT_Q1_KEY)
        # The owner is not cloned: the same authoritative record and its same
        # tensor-backed S03 cross the typed transaction commit.
        trial: dict[str, LifecycleRecord] = {OWNER_KEY: owner_before, INERT_Q0_KEY: q0, INERT_Q1_KEY: q1}
        active_trial = tuple(key for key, row in trial.items() if row.status == ACTIVE)
        if active_trial != post.keys:
            raise ValueError("post snapshot does not match the typed lifecycle deltas")
        for member in post.members:
            if int(member.membership_epoch) != int(trial[member.lifecycle_key].membership_epoch):
                raise ValueError("post snapshot carries a stale membership epoch")
        if post.frontier != (INERT_Q1_KEY,):
            raise ValueError("post frontier must contain only the genuine join")

        owner_s03_before = _digest_array(owner_before.high_hidden)
        self.records = trial
        owner_after_commit = self.owner
        if owner_after_commit.status != ACTIVE or owner_after_commit.membership_epoch != OWNER_EPOCH:
            raise RuntimeError("owner_t did not survive with uninterrupted epoch")
        if _digest_array(owner_after_commit.high_hidden) != owner_s03_before:
            raise RuntimeError("transaction mutated owner S03")

        owner_s03_after_commit = _digest_array(owner_after_commit.high_hidden)
        same_owner_record = id(owner_after_commit) == owner_record_identity_before
        same_s03_carrier = id(owner_after_commit.high_hidden) == owner_s03_carrier_identity_before
        if not same_owner_record or not same_s03_carrier:
            raise RuntimeError("typed commit did not preserve the authoritative owner S03 carrier")
        non_s03_before_backend = self._non_s03_owner_digest(self.owner)
        if self.arm == COMPLETE_RESET:
            self.owner.high_hidden = torch.zeros_like(self._require_s03())
        non_s03_after_backend = self._non_s03_owner_digest(self.owner)
        witness = TransactionWitness(
            typed_transaction=True,
            exact_deltas=True,
            pre_keys=pre.keys,
            post_keys=post.keys,
            owner_status_before=owner_status_before,
            owner_status_after=owner_after_commit.status,
            owner_epoch_before=owner_epoch_before,
            owner_epoch_after=int(owner_after_commit.membership_epoch),
            owner_s03_digest_before=owner_s03_before,
            owner_s03_digest_after_commit=owner_s03_after_commit,
            owner_s03_digest_after_backend=_digest_array(self.owner.high_hidden),
            owner_non_s03_digest_before_backend=non_s03_before_backend,
            owner_non_s03_digest_after_backend=non_s03_after_backend,
            complete_reset_applied=self.arm == COMPLETE_RESET,
            latch_bound_exactly_to_owner_epoch=(
                self.arm != ONE_BIT_OWNER_EPOCH_LATCH
                or (
                    self._latch is not None
                    and self._latch.lifecycle_key == OWNER_KEY
                    and int(self._latch.membership_epoch) == OWNER_EPOCH
                )
            ),
            same_owner_record_through_commit=same_owner_record,
            same_s03_carrier_through_commit=same_s03_carrier,
            choice_reads_committed_registered_s03=True,
            second_information_bearing_s03_carrier=False,
            public_pre_digest=self._snapshot_digest(pre),
            public_post_digest=self._snapshot_digest(post),
        )
        self.physical_time = 2
        return witness

    def _require_s03(self) -> torch.Tensor:
        if self.owner.status != ACTIVE or int(self.owner.membership_epoch) != OWNER_EPOCH:
            raise RuntimeError("registered owner_t@0 S03 is outside its active epoch")
        value = self.owner.high_hidden
        if not isinstance(value, torch.Tensor):
            raise RuntimeError("registered owner_t@0 S03 is not the tensor-backed authority")
        if tuple(value.shape) != (self.dimensions.memory_dim,) or not bool(torch.isfinite(value).all()):
            raise RuntimeError("registered owner_t@0 S03 is malformed")
        return value

    def choice_memory(self) -> torch.Tensor:
        if self.physical_time != 2 or self._choice_consumed:
            raise RuntimeError("choice memory may be read exactly once after replacement")
        self._choice_consumed = True
        if self.arm == ONE_BIT_OWNER_EPOCH_LATCH:
            if self._latch is None:
                raise RuntimeError("latch arm has no owner-epoch bit")
            if (
                self.owner.status != ACTIVE
                or self._latch.lifecycle_key != self.owner.lifecycle_key
                or int(self._latch.membership_epoch) != int(self.owner.membership_epoch)
            ):
                self._latch = None
                raise RuntimeError("latch expired on owner/epoch mismatch")
            return self._latch.project(
                memory_dim=self.dimensions.memory_dim,
                device=self._require_s03().device,
            )
        return self._require_s03()

    def terminal_transition(self, *, action: int, bit: int) -> dict[str, object]:
        if not self._choice_consumed or self.physical_time != 2:
            raise RuntimeError("terminal transition requires one fresh choice call")
        if int(action) not in (0, 1) or int(bit) not in (0, 1):
            raise ValueError("choice action and private bit must be binary")
        reward = float(int(action) == int(bit))
        for row in self.records.values():
            row.status = TERMINAL
            row.high_hidden = _zeros(0)
            row.low_actor_hidden = _zeros(0)
            row.low_critic_hidden = _zeros(0)
        self._latch = None
        self.physical_time = 3
        return {
            "transition": 2,
            "legal_actions": [0, 1],
            "action": int(action),
            "reward": reward,
            "terminated": True,
            "memory_cleared": True,
            "latch_expired": self._latch is None,
        }

    def backend_schema(self) -> Mapping[str, object]:
        return {
            "arm": self.arm,
            "registered_s03_field": "LifecycleRecord.high_hidden",
            "single_tensor_backed_s03_authority": True,
            "differentiable_owner_epoch_mirror": False,
            "second_information_bearing_s03_carrier": False,
            "latch_fields": ["lifecycle_key", "membership_epoch", "bit"],
            "latch_extra_fields": [],
        }
