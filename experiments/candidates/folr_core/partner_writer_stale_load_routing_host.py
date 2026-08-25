"""Real three-transition host for the frozen FOLR-B3 treatment.

The host owns lifecycle truth.  Models may emit candidate state, but the
atomic q0 -> q1 replacement and owner_t@0 continuity are checked here with the
public typed membership DTOs.  No arm label, target bit, cached action, or
kernel is exposed through the public observation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Final

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

OWNER_KEY: Final = "owner_t"
OWNER_EPOCH: Final = 0
OLD_PARTNER_KEY: Final = "inert_partner_q0"
NEW_PARTNER_KEY: Final = "inert_partner_q1"

TYPED_OWNER_EPOCH_ROUTING: Final = "TYPED_OWNER_EPOCH_ROUTING"
ISOMORPHIC_GENERIC_UPDATE: Final = "ISOMORPHIC_GENERIC_UPDATE"
COMPLETE_RESET: Final = "COMPLETE_RESET"
PHASE_P_CALIBRATION: Final = "PHASE_P_CALIBRATION"
ARMS: Final = (
    TYPED_OWNER_EPOCH_ROUTING,
    ISOMORPHIC_GENERIC_UPDATE,
    COMPLETE_RESET,
)


def _zeros(size: int) -> np.ndarray:
    return np.zeros(int(size), dtype=np.float32)


def tensor_digest(value: torch.Tensor) -> str:
    array = value.detach().cpu().contiguous().numpy()
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
    owner_state_dim: int = 2
    partner_state_dim: int = 2
    new_partner_state_dim: int = 4


@dataclass(frozen=True)
class PartnerWriteDTO:
    """Immutable binding metadata plus a detached writer payload.

    ``payload`` is cloned at construction and consumers receive another clone,
    so a routed arm cannot mutate the authoritative writer output shared by
    the three phase-R arms.
    """

    owner_lifecycle_key: str
    owner_membership_epoch: int
    partner_lifecycle_key: str
    partner_membership_epoch: int
    writer_call_identity: str
    source_bit: int
    payload_digest: str
    _payload_bytes: bytes
    _payload_shape: tuple[int, ...]

    @classmethod
    def make(
        cls,
        *,
        writer_call_identity: str,
        source_bit: int,
        payload: torch.Tensor,
    ) -> "PartnerWriteDTO":
        if int(source_bit) not in (0, 1):
            raise ValueError("partner writer source must be binary")
        value = payload.detach().cpu().to(torch.float32).contiguous()
        if value.ndim != 1 or not bool(torch.isfinite(value).all()):
            raise ValueError("partner writer payload must be one finite vector")
        return cls(
            owner_lifecycle_key=OWNER_KEY,
            owner_membership_epoch=OWNER_EPOCH,
            partner_lifecycle_key=NEW_PARTNER_KEY,
            partner_membership_epoch=0,
            writer_call_identity=str(writer_call_identity),
            source_bit=int(source_bit),
            payload_digest=tensor_digest(value),
            _payload_bytes=value.numpy().tobytes(order="C"),
            _payload_shape=tuple(value.shape),
        )

    def materialize(self, *, device: torch.device) -> torch.Tensor:
        array = np.frombuffer(self._payload_bytes, dtype=np.float32).copy()
        value = torch.from_numpy(array.reshape(self._payload_shape)).to(device=device)
        if tensor_digest(value) != self.payload_digest:
            raise RuntimeError("partner writer DTO payload digest drifted")
        return value


@dataclass(frozen=True)
class ReplacementWitness:
    typed_transaction: bool
    exact_deltas: bool
    pre_keys: tuple[str, ...]
    post_keys: tuple[str, ...]
    owner_record_preserved: bool
    owner_epoch_preserved: bool
    old_partner_terminated: bool
    new_partner_joined: bool
    old_partner_state_invalidated: bool
    public_pre_digest: str
    public_post_digest: str


class PartnerWriterStaleLoadHost:
    """One physical episode with three complete transitions."""

    def __init__(self, *, root: int, regime: str, dimensions: HostDimensions) -> None:
        if regime not in ("CLEAN", "STALE_LOAD", "CALIBRATION"):
            raise ValueError(f"unknown regime {regime!r}")
        self.root = int(root)
        self.regime = str(regime)
        self.dimensions = dimensions
        self.physical_time = 0
        self._writer_dto: PartnerWriteDTO | None = None
        self._choice_consumed = False
        self.records: dict[str, LifecycleRecord] = {
            OWNER_KEY: self._new_record(OWNER_KEY),
            OLD_PARTNER_KEY: self._new_record(OLD_PARTNER_KEY),
        }

    def _new_record(self, key: str) -> LifecycleRecord:
        size = (
            self.dimensions.owner_state_dim
            if key == OWNER_KEY
            else self.dimensions.partner_state_dim
        )
        return LifecycleRecord(
            lifecycle_key=key,
            status=ACTIVE,
            membership_epoch=0,
            low_actor_hidden=_zeros(0),
            low_critic_hidden=_zeros(0),
            high_hidden=torch.zeros(size, dtype=torch.float32),
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

    def public_observation(self) -> np.ndarray:
        # Root and time are nuisance-only. Bits, arm and regime are absent.
        x = ((self.root % 997) / 498.0) - 1.0
        y = (((self.root // 997) % 997) / 498.0) - 1.0
        return np.asarray([x, y, float(self.physical_time)], dtype=np.float32)

    def _member(self, key: str) -> BoundaryMember:
        row = self.records[key]
        return BoundaryMember.make(
            key,
            row.membership_epoch,
            self.public_observation(),
            _zeros(self.dimensions.critic_member_dim),
            obs_dim=self.dimensions.observation_dim,
            critic_member_dim=self.dimensions.critic_member_dim,
        )

    @staticmethod
    def _snapshot_digest(snapshot: BoundarySnapshot) -> str:
        value = {
            "physical_time": int(snapshot.physical_time),
            "frontier": list(snapshot.frontier),
            "keys": list(snapshot.keys),
            "epochs": [int(row.membership_epoch) for row in snapshot.members],
        }
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def transition_one(
        self,
        *,
        owner_state: torch.Tensor,
        obsolete_partner_state: torch.Tensor,
    ) -> dict[str, object]:
        if self.physical_time != 0:
            raise RuntimeError("transition one may execute exactly once")
        owner = owner_state.reshape(-1)
        obsolete = obsolete_partner_state.reshape(-1)
        if tuple(owner.shape) != (self.dimensions.owner_state_dim,):
            raise ValueError("owner state has wrong shape")
        if tuple(obsolete.shape) != (self.dimensions.partner_state_dim,):
            raise ValueError("obsolete partner state has wrong shape")
        if self.regime in ("CLEAN", "CALIBRATION"):
            obsolete = torch.zeros_like(obsolete)
        # Host lifecycle evidence is an observation boundary, never an
        # autograd carrier. The actor retains its own differentiable candidates.
        self.owner.high_hidden = owner.detach().clone()
        self.records[OLD_PARTNER_KEY].high_hidden = obsolete.detach().clone()
        self.physical_time = 1
        return {
            "transition": 1,
            "action": "WAIT",
            "reward": 0.0,
            "owner_state_digest": tensor_digest(owner),
            "obsolete_partner_state_digest": tensor_digest(obsolete),
            "public_observation": self.public_observation().tolist(),
        }

    def replacement_transaction(self) -> MembershipTransaction:
        if self.physical_time != 1:
            raise RuntimeError("replacement belongs after transition one")
        pre = BoundarySnapshot.make(
            self.physical_time,
            (self._member(OWNER_KEY), self._member(OLD_PARTNER_KEY)),
            _zeros(self.dimensions.critic_global_dim),
            critic_global_dim=self.dimensions.critic_global_dim,
            frontier=(),
        )
        new_member = BoundaryMember.make(
            NEW_PARTNER_KEY,
            0,
            self.public_observation(),
            _zeros(self.dimensions.critic_member_dim),
            obs_dim=self.dimensions.observation_dim,
            critic_member_dim=self.dimensions.critic_member_dim,
        )
        post = BoundarySnapshot.make(
            self.physical_time,
            (self._member(OWNER_KEY), new_member),
            _zeros(self.dimensions.critic_global_dim),
            critic_global_dim=self.dimensions.critic_global_dim,
            frontier=(NEW_PARTNER_KEY,),
        )
        return MembershipTransaction(
            pre_membership_boundary_snapshot=pre,
            atomic_membership_delta=(
                MembershipDelta(TERMINAL_LEAVE, OLD_PARTNER_KEY, 0),
                MembershipDelta(JOIN, NEW_PARTNER_KEY, 0),
            ),
            post_membership_pre_policy_snapshot=post,
        )

    def apply_replacement(self, transaction: MembershipTransaction) -> ReplacementWitness:
        if not isinstance(transaction, MembershipTransaction):
            raise TypeError("replacement must use MembershipTransaction")
        expected = (
            (TERMINAL_LEAVE, OLD_PARTNER_KEY, 0),
            (JOIN, NEW_PARTNER_KEY, 0),
        )
        actual = tuple(
            (row.kind, row.lifecycle_key, int(row.expected_membership_epoch))
            for row in transaction.atomic_membership_delta
        )
        pre = transaction.pre_membership_boundary_snapshot
        post = transaction.post_membership_pre_policy_snapshot
        if actual != expected or pre.keys != (OWNER_KEY, OLD_PARTNER_KEY):
            raise ValueError("replacement transaction differs from frozen q0->q1 contract")
        if post.keys != (OWNER_KEY, NEW_PARTNER_KEY) or post.frontier != (NEW_PARTNER_KEY,):
            raise ValueError("replacement post snapshot differs from frozen roster")
        owner_record = self.owner
        owner_id = id(owner_record)
        owner_epoch = int(owner_record.membership_epoch)
        old = self.records[OLD_PARTNER_KEY].clone()
        old.status = TERMINAL
        old.high_hidden = _zeros(0)
        new = self._new_record(NEW_PARTNER_KEY)
        self.records = {OWNER_KEY: owner_record, OLD_PARTNER_KEY: old, NEW_PARTNER_KEY: new}
        witness = ReplacementWitness(
            typed_transaction=True,
            exact_deltas=actual == expected,
            pre_keys=pre.keys,
            post_keys=post.keys,
            owner_record_preserved=id(self.owner) == owner_id,
            owner_epoch_preserved=int(self.owner.membership_epoch) == owner_epoch == OWNER_EPOCH,
            old_partner_terminated=self.records[OLD_PARTNER_KEY].status == TERMINAL,
            new_partner_joined=self.records[NEW_PARTNER_KEY].status == ACTIVE,
            old_partner_state_invalidated=np.asarray(old.high_hidden).size == 0,
            public_pre_digest=self._snapshot_digest(pre),
            public_post_digest=self._snapshot_digest(post),
        )
        if not all(
            (
                witness.owner_record_preserved,
                witness.owner_epoch_preserved,
                witness.old_partner_terminated,
                witness.new_partner_joined,
                witness.old_partner_state_invalidated,
            )
        ):
            raise RuntimeError("atomic replacement failed lifecycle invariants")
        return witness

    def transition_two(self, writer_dto: PartnerWriteDTO) -> dict[str, object]:
        if self.physical_time != 1 or self._writer_dto is not None:
            raise RuntimeError("transition two may execute exactly once after replacement")
        if (
            writer_dto.owner_lifecycle_key != OWNER_KEY
            or int(writer_dto.owner_membership_epoch) != OWNER_EPOCH
            or writer_dto.partner_lifecycle_key != NEW_PARTNER_KEY
            or int(writer_dto.partner_membership_epoch) != 0
        ):
            raise ValueError("partner writer DTO is not bound to owner_t@0 and q1@0")
        payload = writer_dto.materialize(device=torch.device("cpu"))
        if tuple(payload.shape) != (self.dimensions.new_partner_state_dim,):
            raise ValueError("new partner writer payload has wrong shape")
        self.records[NEW_PARTNER_KEY].high_hidden = payload
        self._writer_dto = writer_dto
        self.physical_time = 2
        return {
            "transition": 2,
            "action": "WAIT",
            "reward": 0.0,
            "writer_binding": {
                "owner": f"{OWNER_KEY}@{OWNER_EPOCH}",
                "partner": f"{NEW_PARTNER_KEY}@0",
                "writer_call_identity": writer_dto.writer_call_identity,
                "payload_digest": writer_dto.payload_digest,
            },
            "public_observation": self.public_observation().tolist(),
        }

    def routed_inputs(self) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if self.physical_time != 2 or self._writer_dto is None:
            raise RuntimeError("routed inputs require the completed partner write")
        owner = self.owner.high_hidden
        old = self.records[OLD_PARTNER_KEY].high_hidden
        new = self.records[NEW_PARTNER_KEY].high_hidden
        if not isinstance(owner, torch.Tensor) or not isinstance(new, torch.Tensor):
            raise RuntimeError("active routed state is not tensor-backed")
        if np.asarray(old).size != 0:
            raise RuntimeError("departed partner lifecycle still owns live state")
        # The obsolete candidate is supplied separately by the runner; lifecycle
        # ownership is gone. This method returns a neutral placeholder to ensure
        # nobody can recover it from q0 after commit.
        return owner, torch.zeros(self.dimensions.partner_state_dim), new

    def terminal_transition(self, *, action: int, target: int, action_count: int) -> dict[str, object]:
        if self.physical_time != 2 or self._choice_consumed:
            raise RuntimeError("terminal choice must be fresh and unique")
        if not 0 <= int(action) < int(action_count) or not 0 <= int(target) < int(action_count):
            raise ValueError("action or target outside legal set")
        self._choice_consumed = True
        reward = float(int(action) == int(target))
        for row in self.records.values():
            row.status = TERMINAL
            row.high_hidden = _zeros(0)
        self.physical_time = 3
        return {
            "transition": 3,
            "action": int(action),
            "target": int(target),
            "reward": reward,
            "all_memory_cleared": all(np.asarray(row.high_hidden).size == 0 for row in self.records.values()),
        }
