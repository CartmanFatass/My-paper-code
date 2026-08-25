"""Three-transition typed roster-substitution host for frozen FOLR-B2.

The host owns lifecycle truth and fixed routing only.  Learned candidate
computations live in the paired actor module; this adapter applies the
pre-existing revision-v5 rule: survivor-private state may remain in S03 only
when roster/partner substitution leaves its lineage unchanged, while partner
state is invalidated and reconstructed in S04.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Final, Mapping

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

HOST_IDENTIFIER: Final = "folr_counterfactual_witness_substitution_v1"
OWNER_KEY: Final = "owner_t"
OWNER_EPOCH: Final = 0
TYPED_WITNESS_S03_S04: Final = "TYPED_WITNESS_S03_S04"
ISOMORPHIC_GENERIC_MEMORY: Final = "ISOMORPHIC_GENERIC_MEMORY"
COMPLETE_RESET: Final = "COMPLETE_RESET"
ARMS: Final = (
    TYPED_WITNESS_S03_S04,
    ISOMORPHIC_GENERIC_MEMORY,
    COMPLETE_RESET,
)


def _zeros(size: int) -> np.ndarray:
    return np.zeros(int(size), dtype=np.float32)


def tensor_digest(value: torch.Tensor | np.ndarray) -> str:
    array = (
        value.detach().cpu().contiguous().numpy()
        if isinstance(value, torch.Tensor)
        else np.ascontiguousarray(np.asarray(value))
    )
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("utf-8"))
    digest.update(str(tuple(array.shape)).encode("utf-8"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True)
class HostDimensions:
    observation_dim: int = 4
    critic_member_dim: int = 1
    critic_global_dim: int = 1
    memory_dim: int = 16
    s03_dim: int = 8
    s04_dim: int = 8

    def __post_init__(self) -> None:
        if self.memory_dim != self.s03_dim + self.s04_dim:
            raise ValueError("S03 and S04 slices must exactly cover memory")


@dataclass(frozen=True)
class StateProvenance:
    state_kind: str
    owner_lifecycle_key: str
    owner_membership_epoch: int
    source_partner_key: str | None
    partner_dependencies: tuple[str, ...]
    writer_call_identity: str
    descriptor_digest: str


@dataclass(frozen=True)
class CounterfactualLineage:
    original_provenance: Mapping[str, Any]
    substituted_provenance: Mapping[str, Any]
    departed_partner_key: str
    joined_partner_key: str
    owner_binding_survives: bool
    source_binding_survives: bool
    dependency_bindings_survive: bool
    roster_substitution_invariant: bool
    partner_substitution_invariant: bool

    @property
    def witness_passes(self) -> bool:
        return bool(
            self.owner_binding_survives
            and self.source_binding_survives
            and self.dependency_bindings_survive
            and self.roster_substitution_invariant
            and self.partner_substitution_invariant
        )


def derive_counterfactual_lineage(
    provenance: StateProvenance,
    *,
    departed_partner_key: str,
    joined_partner_key: str,
    post_owner_key: str,
    post_owner_epoch: int,
) -> CounterfactualLineage:
    """Apply the actual binding substitution and derive invariance predicates."""

    original = asdict(provenance)
    substituted = dict(original)
    if substituted["source_partner_key"] == departed_partner_key:
        substituted["source_partner_key"] = joined_partner_key
    substituted["partner_dependencies"] = tuple(
        joined_partner_key if key == departed_partner_key else key
        for key in provenance.partner_dependencies
    )
    owner_survives = bool(
        provenance.owner_lifecycle_key == post_owner_key
        and int(provenance.owner_membership_epoch) == int(post_owner_epoch)
    )
    source_survives = provenance.source_partner_key != departed_partner_key
    dependencies_survive = departed_partner_key not in provenance.partner_dependencies
    # State is counterfactually invariant only when applying the concrete
    # substitution leaves every state-defining provenance binding unchanged.
    partner_invariant = original == substituted
    roster_invariant = bool(owner_survives and source_survives and dependencies_survive)
    return CounterfactualLineage(
        original_provenance=original,
        substituted_provenance=substituted,
        departed_partner_key=str(departed_partner_key),
        joined_partner_key=str(joined_partner_key),
        owner_binding_survives=owner_survives,
        source_binding_survives=source_survives,
        dependency_bindings_survive=dependencies_survive,
        roster_substitution_invariant=roster_invariant,
        partner_substitution_invariant=partner_invariant,
    )


@dataclass(frozen=True)
class RoutingWitness:
    typed_transaction: bool
    exact_atomic_deltas: bool
    pre_keys: tuple[str, ...]
    post_keys: tuple[str, ...]
    owner_key: str
    owner_epoch_before: int
    owner_epoch_after: int
    same_owner_record: bool
    uninterrupted_owner_epoch: bool
    old_partner_terminal: bool
    old_partner_memory_cleared: bool
    new_partner_join: bool
    survivor_lineage: Mapping[str, Any]
    old_partner_lineage: Mapping[str, Any]
    survivor_witness_passes: bool
    old_partner_witness_fails: bool
    s03_retained: bool
    old_s04_invalidated: bool
    new_s04_rebuilt_after_event: bool
    second_information_carrier: bool
    cached_action_kernel_or_logits: bool
    update_between_event_and_choice: bool
    memory_digest_pre_event: str
    learned_event_candidate_digest: str
    memory_digest_after_replacement: str
    memory_digest_after_new_partner_write: str | None
    public_pre_digest: str
    public_post_digest: str


class CounterfactualWitnessHost:
    """One real three-transition episode with a typed atomic replacement."""

    def __init__(
        self,
        *,
        arm: str,
        root: int,
        old_partner_key: str,
        new_partner_key: str,
        old_partner_role: str,
        new_partner_role: str,
        dimensions: HostDimensions,
    ) -> None:
        if arm not in ARMS:
            raise ValueError(f"unknown arm {arm!r}")
        if old_partner_key == new_partner_key or OWNER_KEY in (old_partner_key, new_partner_key):
            raise ValueError("replacement must use two distinct non-owner partner keys")
        self.arm = str(arm)
        self.root = int(root)
        self.old_partner_key = str(old_partner_key)
        self.new_partner_key = str(new_partner_key)
        self.old_partner_role = str(old_partner_role)
        self.new_partner_role = str(new_partner_role)
        self.dimensions = dimensions
        self.physical_time = 0
        self.records: dict[str, LifecycleRecord] = {
            OWNER_KEY: self._new_record(OWNER_KEY),
            self.old_partner_key: self._new_record(self.old_partner_key),
        }
        self._choice_consumed = False
        self._new_partner_write_done = False
        self._witness: RoutingWitness | None = None

    def _new_record(self, key: str) -> LifecycleRecord:
        return LifecycleRecord(
            lifecycle_key=str(key),
            status=ACTIVE,
            membership_epoch=0,
            low_actor_hidden=_zeros(0),
            low_critic_hidden=_zeros(0),
            high_hidden=(
                torch.zeros(self.dimensions.memory_dim, dtype=torch.float32)
                if key == OWNER_KEY
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

    def _memory(self) -> torch.Tensor:
        value = self.owner.high_hidden
        if not isinstance(value, torch.Tensor):
            raise RuntimeError("owner memory is not the differentiable authority")
        if tuple(value.shape) != (self.dimensions.memory_dim,) or not bool(torch.isfinite(value).all()):
            raise RuntimeError("owner memory is malformed")
        return value

    def _public_observation(self) -> np.ndarray:
        # Bits, arm, regime, partner keys and roles are deliberately absent.
        x = ((self.root % 1009) / 504.0) - 1.0
        y = (((self.root // 1009) % 1013) / 506.0) - 1.0
        return np.asarray([x, y, float(self.physical_time), 1.0], dtype=np.float32)

    def public_view(self) -> dict[str, Any]:
        legal = ["WAIT"] if self.physical_time in (0, 1) else [0, 1, 2, 3]
        return {
            "physical_time": int(self.physical_time),
            "active_keys": [key for key, row in self.records.items() if row.status == ACTIVE],
            "observation": self._public_observation().tolist(),
            "legal_actions": legal,
        }

    @staticmethod
    def _snapshot_digest(snapshot: BoundarySnapshot) -> str:
        value = {
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
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

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

    def transition_one(
        self,
        *,
        survivor_candidate: torch.Tensor,
        old_partner_candidate: torch.Tensor,
        survivor_provenance: StateProvenance,
        old_partner_provenance: StateProvenance,
        wait_logit: torch.Tensor,
    ) -> dict[str, Any]:
        if self.physical_time != 0:
            raise RuntimeError("transition one may execute exactly once")
        if tuple(survivor_candidate.shape) != (self.dimensions.s03_dim,):
            raise ValueError("survivor writer shape drift")
        if tuple(old_partner_candidate.shape) != (self.dimensions.s04_dim,):
            raise ValueError("old-partner writer shape drift")
        memory = torch.cat((survivor_candidate, old_partner_candidate), dim=0)
        if not bool(torch.isfinite(memory).all()) or int(wait_logit.numel()) != 1:
            raise ValueError("non-finite writer output or malformed WAIT kernel")
        self.owner.high_hidden = memory
        self._survivor_provenance = survivor_provenance
        self._old_partner_provenance = old_partner_provenance
        view = self.public_view()
        self.physical_time = 1
        return {
            "transition": 1,
            "action": "WAIT",
            "reward": 0.0,
            "public_view": view,
            "survivor_writer_digest": tensor_digest(survivor_candidate),
            "old_partner_writer_digest": tensor_digest(old_partner_candidate),
            "survivor_provenance": asdict(survivor_provenance),
            "old_partner_provenance": asdict(old_partner_provenance),
            "memory_digest": tensor_digest(memory),
            "wait_kernel": [1.0],
        }

    def replacement_transaction(self) -> MembershipTransaction:
        if self.physical_time != 1:
            raise RuntimeError("replacement belongs after transition one")
        pre = BoundarySnapshot.make(
            self.physical_time,
            (self._member(OWNER_KEY), self._member(self.old_partner_key)),
            _zeros(self.dimensions.critic_global_dim),
            critic_global_dim=self.dimensions.critic_global_dim,
            frontier=(),
        )
        joined = BoundaryMember.make(
            self.new_partner_key,
            0,
            self._public_observation(),
            _zeros(self.dimensions.critic_member_dim),
            obs_dim=self.dimensions.observation_dim,
            critic_member_dim=self.dimensions.critic_member_dim,
        )
        post = BoundarySnapshot.make(
            self.physical_time,
            (self._member(OWNER_KEY), joined),
            _zeros(self.dimensions.critic_global_dim),
            critic_global_dim=self.dimensions.critic_global_dim,
            frontier=(self.new_partner_key,),
        )
        return MembershipTransaction(
            pre_membership_boundary_snapshot=pre,
            atomic_membership_delta=(
                MembershipDelta(TERMINAL_LEAVE, self.old_partner_key, 0),
                MembershipDelta(JOIN, self.new_partner_key, 0),
            ),
            post_membership_pre_policy_snapshot=post,
        )

    def apply_replacement(
        self,
        transaction: MembershipTransaction,
        *,
        learned_event_candidate: torch.Tensor,
    ) -> RoutingWitness:
        if not isinstance(transaction, MembershipTransaction):
            raise TypeError("replacement requires typed MembershipTransaction")
        if tuple(learned_event_candidate.shape) != (self.dimensions.memory_dim,):
            raise ValueError("learned event candidate shape drift")
        expected = (
            (TERMINAL_LEAVE, self.old_partner_key, 0),
            (JOIN, self.new_partner_key, 0),
        )
        actual = tuple(
            (row.kind, row.lifecycle_key, int(row.expected_membership_epoch))
            for row in transaction.atomic_membership_delta
        )
        pre = transaction.pre_membership_boundary_snapshot
        post = transaction.post_membership_pre_policy_snapshot
        if actual != expected or pre.keys != (OWNER_KEY, self.old_partner_key):
            raise ValueError("atomic replacement differs from frozen host")
        if post.keys != (OWNER_KEY, self.new_partner_key) or post.frontier != (self.new_partner_key,):
            raise ValueError("post-replacement roster differs from frozen host")
        owner_record_id = id(self.owner)
        owner_epoch_before = int(self.owner.membership_epoch)
        memory_before = self._memory()
        survivor_lineage = derive_counterfactual_lineage(
            self._survivor_provenance,
            departed_partner_key=self.old_partner_key,
            joined_partner_key=self.new_partner_key,
            post_owner_key=OWNER_KEY,
            post_owner_epoch=int(self.owner.membership_epoch),
        )
        partner_lineage = derive_counterfactual_lineage(
            self._old_partner_provenance,
            departed_partner_key=self.old_partner_key,
            joined_partner_key=self.new_partner_key,
            post_owner_key=OWNER_KEY,
            post_owner_epoch=int(self.owner.membership_epoch),
        )
        survivor_provenance = self._survivor_provenance
        partner_provenance = self._old_partner_provenance
        survivor_semantics_valid = bool(
            survivor_provenance.state_kind == "survivor_private"
            and survivor_provenance.owner_lifecycle_key == OWNER_KEY
            and int(survivor_provenance.owner_membership_epoch) == OWNER_EPOCH
            and survivor_provenance.source_partner_key is None
            and not survivor_provenance.partner_dependencies
        )
        partner_semantics_valid = bool(
            partner_provenance.state_kind == "partner_scoped"
            and partner_provenance.owner_lifecycle_key == OWNER_KEY
            and int(partner_provenance.owner_membership_epoch) == OWNER_EPOCH
            and partner_provenance.source_partner_key == self.old_partner_key
            and self.old_partner_key in partner_provenance.partner_dependencies
        )
        survivor_passes = bool(survivor_semantics_valid and survivor_lineage.witness_passes)
        partner_passes = bool(partner_semantics_valid and partner_lineage.witness_passes)
        if self.arm == TYPED_WITNESS_S03_S04 and (
            not survivor_semantics_valid
            or not partner_semantics_valid
            or not survivor_lineage.witness_passes
            or partner_lineage.witness_passes
        ):
            raise RuntimeError("typed provenance does not derive the frozen retain/invalidate route")
        old_row = self.records[self.old_partner_key].clone()
        old_row.status = TERMINAL
        old_row.high_hidden = _zeros(0)
        old_row.low_actor_hidden = _zeros(0)
        old_row.low_critic_hidden = _zeros(0)
        new_row = self._new_record(self.new_partner_key)
        self.records = {OWNER_KEY: self.owner, self.old_partner_key: old_row, self.new_partner_key: new_row}
        if self.arm == TYPED_WITNESS_S03_S04:
            routed = torch.cat(
                (
                    memory_before[: self.dimensions.s03_dim]
                    if survivor_passes
                    else torch.zeros_like(memory_before[: self.dimensions.s03_dim]),
                    memory_before[self.dimensions.s03_dim :]
                    if partner_passes
                    else torch.zeros_like(memory_before[self.dimensions.s03_dim :]),
                ),
                dim=0,
            )
        elif self.arm == ISOMORPHIC_GENERIC_MEMORY:
            routed = learned_event_candidate
        else:
            routed = torch.zeros_like(memory_before)
        self.owner.high_hidden = routed
        witness = RoutingWitness(
            typed_transaction=True,
            exact_atomic_deltas=True,
            pre_keys=pre.keys,
            post_keys=post.keys,
            owner_key=OWNER_KEY,
            owner_epoch_before=owner_epoch_before,
            owner_epoch_after=int(self.owner.membership_epoch),
            same_owner_record=id(self.owner) == owner_record_id,
            uninterrupted_owner_epoch=int(self.owner.membership_epoch) == OWNER_EPOCH,
            old_partner_terminal=old_row.status == TERMINAL,
            old_partner_memory_cleared=np.asarray(old_row.high_hidden).size == 0,
            new_partner_join=new_row.status == ACTIVE and new_row.is_genuine_join,
            survivor_lineage=asdict(survivor_lineage),
            old_partner_lineage=asdict(partner_lineage),
            survivor_witness_passes=survivor_passes,
            old_partner_witness_fails=bool(
                partner_semantics_valid and not partner_lineage.witness_passes
            ),
            s03_retained=self.arm == TYPED_WITNESS_S03_S04 and survivor_passes,
            old_s04_invalidated=self.arm in (TYPED_WITNESS_S03_S04, COMPLETE_RESET)
            and not partner_passes,
            new_s04_rebuilt_after_event=False,
            second_information_carrier=False,
            cached_action_kernel_or_logits=False,
            update_between_event_and_choice=False,
            memory_digest_pre_event=tensor_digest(memory_before),
            learned_event_candidate_digest=tensor_digest(learned_event_candidate),
            memory_digest_after_replacement=tensor_digest(routed),
            memory_digest_after_new_partner_write=None,
            public_pre_digest=self._snapshot_digest(pre),
            public_post_digest=self._snapshot_digest(post),
        )
        self._witness = witness
        return witness

    def transition_two(
        self,
        *,
        new_partner_candidate: torch.Tensor,
        learned_post_candidate: torch.Tensor,
        wait_logit: torch.Tensor,
    ) -> dict[str, Any]:
        if self.physical_time != 1 or self._witness is None or self._new_partner_write_done:
            raise RuntimeError("transition two requires one committed replacement")
        if tuple(new_partner_candidate.shape) != (self.dimensions.s04_dim,):
            raise ValueError("new-partner writer shape drift")
        if tuple(learned_post_candidate.shape) != (self.dimensions.memory_dim,):
            raise ValueError("learned post-event candidate shape drift")
        if self.arm == TYPED_WITNESS_S03_S04:
            memory = torch.cat((self._memory()[: self.dimensions.s03_dim], new_partner_candidate), dim=0)
        elif self.arm == ISOMORPHIC_GENERIC_MEMORY:
            memory = learned_post_candidate
        else:
            memory = torch.cat((torch.zeros_like(new_partner_candidate), new_partner_candidate), dim=0)
        if not bool(torch.isfinite(memory).all()) or int(wait_logit.numel()) != 1:
            raise ValueError("non-finite post-event output or malformed WAIT kernel")
        self.owner.high_hidden = memory
        self._new_partner_write_done = True
        self._witness = RoutingWitness(
            **{
                **asdict(self._witness),
                "new_s04_rebuilt_after_event": True,
                "memory_digest_after_new_partner_write": tensor_digest(memory),
            }
        )
        view = self.public_view()
        self.physical_time = 2
        return {
            "transition": 2,
            "action": "WAIT",
            "reward": 0.0,
            "public_view": view,
            "new_partner_writer_digest": tensor_digest(new_partner_candidate),
            "memory_digest": tensor_digest(memory),
            "wait_kernel": [1.0],
        }

    def choice_memory(self) -> torch.Tensor:
        if self.physical_time != 2 or not self._new_partner_write_done or self._choice_consumed:
            raise RuntimeError("choice reads one fresh post-event memory")
        self._choice_consumed = True
        return self._memory()

    def terminal_transition(self, *, action: int, s: int, n_new: int) -> dict[str, Any]:
        if not self._choice_consumed or self.physical_time != 2:
            raise RuntimeError("terminal transition requires the final choice")
        correct_action = 2 * int(s) + int(n_new)
        if int(action) not in range(4) or int(s) not in (0, 1) or int(n_new) not in (0, 1):
            raise ValueError("action or component bit out of range")
        reward = float(int(action) == correct_action)
        for row in self.records.values():
            row.status = TERMINAL
            row.high_hidden = _zeros(0)
            row.low_actor_hidden = _zeros(0)
            row.low_critic_hidden = _zeros(0)
        self.physical_time = 3
        return {
            "transition": 3,
            "correct_action": correct_action,
            "action": int(action),
            "reward": reward,
            "terminated": True,
            "all_memory_cleared": all(np.asarray(row.high_hidden).size == 0 for row in self.records.values()),
        }

    def routing_witness(self) -> Mapping[str, Any]:
        if self._witness is None:
            raise RuntimeError("routing witness is not complete")
        return asdict(self._witness)

    def backend_schema(self) -> Mapping[str, Any]:
        return {
            "arm": self.arm,
            "authority": "LifecycleRecord.high_hidden",
            "total_memory_dim": self.dimensions.memory_dim,
            "s03_slice": [0, self.dimensions.s03_dim],
            "s04_slice": [self.dimensions.s03_dim, self.dimensions.memory_dim],
            "second_information_carrier": False,
            "cached_action_kernel_or_logits": False,
        }
