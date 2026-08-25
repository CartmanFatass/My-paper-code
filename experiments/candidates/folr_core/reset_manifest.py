"""FOLR erase-and-reinitialize reset constructor and canonical manifest.

Sequence 01, component 3 of the object graph External Pro required in ruling
``FOLR_S03_BINDING_SELECTED``.

WHY NEITHER EXISTING RESET WOULD DO
-----------------------------------
Pro examined both and rejected both:

    reset_event_runtime() creates a new environment but does not reset or
    rebuild an existing core.

    clear_rollout_ledgers() clears only four ledgers and leaves records, hidden
    state, skills, gaps, transactions, boundary state, counters and RNG states
    intact.

    Checkpoint restoration faithfully preserves all of those objects and all
    three PCG64 states; it is an appropriate common-snapshot cloning mechanism,
    not a reset.

    A valid complete reset must construct a fresh runtime rather than partially
    clear a historical one.

So ``construct_reset_runtime`` takes a ``ResetManifest`` and returns a brand new
``VariableRosterEventCore``.  It has no parameter through which a historical core
could be passed, which makes "this is not restoration" a fact about the
signature rather than a promise in a comment.  Pro's other half --

    Copying historical records from the common checkpoint would be restoration,
    not reset.

-- follows: every ``LifecycleRecord`` is built from manifest values, and the
four ledgers, the pending transaction and the observation-state boundary start
empty because a fresh core starts them empty.

THE TWO REGISTERED NORMALIZATION PROFILES
-----------------------------------------
Pro gave two admissible readings of the provenance branch ``B``:

    Therefore B must either: be a provenance/history label fully erased at the
    actor-read boundary; or use two histories that are reconstructed into the
    same event flags, observations, skills, ages, active set and summary
    preimage.

They differ in what may still differ between ``b = 0`` and ``b = 1`` at capture
time, and they interact with freshness condition §5D, which asks that "all three
PCG64 pre-states match the common manifest":

``PROVENANCE_LABEL``
    Normalize everything the manifest fixes, RNG states included.  The residual
    difference is the high-ledger and closed-row contents.  §5D reads literally
    against one common manifest.

``RECONSTRUCTED_HISTORY``
    Normalize only the actor-read set.  RNG consumption states, other owners'
    ``high_hidden``, and ``last_policy_event_time`` are left as each history left
    them, so the null tests far more.  §5D's PCG64 condition must then be read
    per branch rather than against one common manifest.

Both are implemented and neither is selected here.  Which one is registered is
an estimand-level choice, and it goes to Pro with the frozen registration before
any kernel is observed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process import variable_roster_event as vre
from ha_ctse_process.variable_roster_event_types import (
    BoundaryMember,
    BoundarySnapshot,
)

from experiments.candidates.folr_core import branch_snapshot as bs

RAW_OUTPUT_BINDING = "folr_core.reset_manifest.v1"

#: See the module docstring.  Registered by name so the choice travels with the
#: result rather than living in a reviewer's memory.
PROVENANCE_LABEL = "PROVENANCE_LABEL"
RECONSTRUCTED_HISTORY = "RECONSTRUCTED_HISTORY"
NORMALIZATION_PROFILES = (PROVENANCE_LABEL, RECONSTRUCTED_HISTORY)

#: The actor-read set: what BOTH profiles normalize.  Everything the commitment
#: policy consumes for the target's first token is either here or supplied by
#: the boundary snapshot.
ACTOR_READ_RECORD_FIELDS = (
    "status",
    "membership_epoch",
    "active_skill",
    "skill_active_age",
    "is_genuine_join",
    "is_rejoin",
)

#: Additionally normalized under PROVENANCE_LABEL only.  ``last_policy_event_time``
#: is handled separately: the manifest carries no value for it because its
#: canonical value is the reset value ``None`` (Pro's §4 erasure list), not a
#: registered actor input.
PROVENANCE_ONLY_RECORD_FIELDS = ("high_hidden",)


@dataclass(frozen=True)
class OwnerManifest:
    """One owner's canonical reinstalled state."""

    lifecycle_key: str
    membership_epoch: int
    status: str
    active_skill: int | None
    skill_active_age: int
    active_gap_remaining: int
    is_genuine_join: bool
    is_rejoin: bool
    #: Pro §4: "non-S03 hidden-state values".  For the target this slot carries
    #: h_neutral; the branches overwrite it with the registered payload.
    high_hidden: np.ndarray
    observation: np.ndarray
    critic_member_features: np.ndarray


@dataclass(frozen=True)
class ResetManifest:
    """Pro's §4 "State that must be frozen or canonically reinstalled", exactly."""

    # architecture mode, dimensions, runtime mode, device, numerical config
    architecture: Mapping[str, Any]
    # byte-identical model parameters
    model_states: Mapping[str, Any]
    # The CORE's RNG episode id, master seeds and stream ids -- plus the exact
    # PCG64 states below.  An earlier comment here called this "immutable
    # environment ledger and episode identity"; Pro caught that the label was
    # overbroad ("No environment ledger is present"), and it was: this manifest
    # is core-only by design, per the registered OBJECT_GRAPH_SCOPE.
    rng_identity: Mapping[str, int]
    rng_states: Mapping[str, Any]
    # physical event time and policy version
    physical_time: int
    policy_version: int
    # active keys, presentation order, statuses, membership epochs, skills, ages,
    # event flags, post-event observations and critic features, non-S03 hidden
    owners: tuple[OwnerManifest, ...]
    critic_global_features: np.ndarray
    # target owner identity, frontier and target token order
    target_lifecycle_key: str
    frontier: tuple[str, ...]
    target_token_order: tuple[str, ...]
    # legal action support
    legal_action_support: np.ndarray

    def __post_init__(self) -> None:
        keys = [owner.lifecycle_key for owner in self.owners]
        if len(keys) != len(set(keys)):
            raise ValueError("FOLR reset manifest repeats a lifecycle key")
        if self.target_lifecycle_key not in keys:
            raise ValueError("FOLR reset manifest target is not an owner")
        if set(self.frontier) - set(keys):
            raise ValueError("FOLR reset manifest frontier names an unknown owner")
        if tuple(self.target_token_order) and self.target_token_order[0] != (
            self.target_lifecycle_key
        ):
            raise ValueError("FOLR target token order must place the target first")
        if set(self.target_token_order) != set(self.frontier):
            raise ValueError("FOLR token order is not a permutation of the frontier")
        if not bool(np.all(self.legal_action_support)):
            # The pinned runtime builds an all-ones mask; a manifest that
            # registered anything else would be describing a different runtime.
            raise ValueError(
                "FOLR legal action support must match the pinned runtime's mask"
            )

    def owner(self, lifecycle_key: str) -> OwnerManifest:
        for candidate in self.owners:
            if candidate.lifecycle_key == lifecycle_key:
                return candidate
        raise KeyError(lifecycle_key)

    def presentation_order(self) -> tuple[str, ...]:
        return tuple(owner.lifecycle_key for owner in self.owners)

    def digest(self) -> str:
        hasher = hashlib.sha256()
        hasher.update(RAW_OUTPUT_BINDING.encode("utf-8"))
        hasher.update(
            bs.digest_of(
                {
                    "architecture": {
                        name: (str(value) if name == "device" else value)
                        for name, value in dict(self.architecture).items()
                    },
                    "model_states": dict(self.model_states),
                    "rng_identity": dict(self.rng_identity),
                    "rng_states": dict(self.rng_states),
                    "physical_time": self.physical_time,
                    "policy_version": self.policy_version,
                    "owners": self.owners,
                    "critic_global_features": self.critic_global_features,
                    "target_lifecycle_key": self.target_lifecycle_key,
                    "frontier": self.frontier,
                    "target_token_order": self.target_token_order,
                    "legal_action_support": self.legal_action_support,
                }
            ).encode("utf-8")
        )
        return hasher.hexdigest()

    def with_target_hidden(self, payload: np.ndarray) -> "ResetManifest":
        """A manifest identical except for the target's installed payload."""
        owners = tuple(
            replace(owner, high_hidden=np.asarray(payload, dtype=np.float32).copy())
            if owner.lifecycle_key == self.target_lifecycle_key
            else owner
            for owner in self.owners
        )
        return replace(self, owners=owners)


def construct_reset_runtime(manifest: ResetManifest) -> vre.VariableRosterEventCore:
    """Build a FRESH runtime from the manifest.

    There is deliberately no parameter for a historical core, and nothing in
    this function reads one.  ``reset_event_runtime`` and
    ``clear_rollout_ledgers`` are never called -- Pro ruled both insufficient,
    and ``test_the_reset_constructor_never_clears_a_historical_core`` pins that
    they are absent from this module's source.
    """
    architecture = dict(manifest.architecture)
    identity = dict(manifest.rng_identity)
    core = vre.VariableRosterEventCore(
        architecture_mode=architecture["architecture_mode"],
        runtime_mode=architecture["runtime_mode"],
        obs_dim=architecture["obs_dim"],
        critic_member_dim=architecture["critic_member_dim"],
        critic_global_dim=architecture["critic_global_dim"],
        n_skills=architecture["n_skills"],
        action_dim=architecture["action_dim"],
        member_hidden_dim=architecture["member_hidden_dim"],
        high_hidden_dim=architecture["high_hidden_dim"],
        low_hidden_dim=architecture["low_hidden_dim"],
        skill_embedding_dim=architecture["skill_embedding_dim"],
        action_space_type=architecture["action_space_type"],
        gamma=architecture["gamma"],
        gae_lambda=architecture["gae_lambda"],
        environment_index=architecture["environment_index"],
        device=architecture["device"],
        rng_episode_id=identity["rng_episode_id"],
        opportunity_seed=identity["opportunity_master_seed"],
        frontier_seed=identity["frontier_master_seed"],
        action_seed=identity["action_master_seed"],
        opportunity_stream_id=identity["opportunity_stream_id"],
        frontier_stream_id=identity["frontier_stream_id"],
        action_stream_id=identity["action_stream_id"],
    )
    for name in bs.MODEL_FIELDS:
        getattr(core, name).load_state_dict(
            {
                key: value.clone() if isinstance(value, torch.Tensor) else value
                for key, value in dict(manifest.model_states[name]).items()
            },
            strict=True,
        )
    core.physical_time = int(manifest.physical_time)
    core.policy_version = int(manifest.policy_version)
    core.records = {
        owner.lifecycle_key: _record_from_manifest(core, owner)
        for owner in manifest.owners
    }
    for name, generator in (
        ("opportunity_rng_state", core.opportunity_rng),
        ("frontier_order_rng_state", core.frontier_rng),
        ("policy_action_rng_state", core.action_rng),
    ):
        generator.bit_generator.state = _copy_state(manifest.rng_states[name])
    return core


def _copy_state(state: Mapping[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, value in dict(state).items():
        if isinstance(value, Mapping):
            copied[key] = dict(value)
        elif isinstance(value, np.ndarray):
            copied[key] = value.copy()
        else:
            copied[key] = value
    return copied


def _record_from_manifest(
    core: vre.VariableRosterEventCore, owner: OwnerManifest
) -> vre.LifecycleRecord:
    """A canonically reinitialized record. No historical field is read."""
    return vre.LifecycleRecord(
        lifecycle_key=str(owner.lifecycle_key),
        status=str(owner.status),
        membership_epoch=int(owner.membership_epoch),
        low_actor_hidden=np.zeros(core.low_hidden_dim, dtype=np.float32),
        low_critic_hidden=np.zeros(core.low_hidden_dim, dtype=np.float32),
        high_hidden=np.asarray(owner.high_hidden, dtype=np.float32).copy(),
        active_skill=None if owner.active_skill is None else int(owner.active_skill),
        skill_active_age=int(owner.skill_active_age),
        active_gap_remaining=int(owner.active_gap_remaining),
        # Pro §4 erasure list: open traces, join/rejoin flags and last-policy
        # metadata are canonical, never carried.
        last_policy_event_time=None,
        open_event_trace=None,
        policy_version=int(core.policy_version),
        is_genuine_join=bool(owner.is_genuine_join),
        is_rejoin=bool(owner.is_rejoin),
    )


def boundary_snapshot(
    manifest: ResetManifest,
    *,
    physical_time: int | None = None,
    frontier: Sequence[str] | None = None,
) -> BoundarySnapshot:
    """The post-event boundary the capture transaction is applied at.

    ``physical_time`` and ``frontier`` may be overridden so the *provenance
    histories* can be driven from the same registered observations and critic
    features as the capture boundary.  Holding those fixed across the histories
    is what lets the actor-read preimage be normalized back afterwards.
    """
    architecture = dict(manifest.architecture)
    members = [
        BoundaryMember.make(
            owner.lifecycle_key,
            int(owner.membership_epoch),
            np.asarray(owner.observation, dtype=np.float32),
            np.asarray(owner.critic_member_features, dtype=np.float32),
            obs_dim=architecture["obs_dim"],
            critic_member_dim=architecture["critic_member_dim"],
        )
        for owner in manifest.owners
        if owner.status == vre.ACTIVE
    ]
    return BoundarySnapshot.make(
        int(manifest.physical_time if physical_time is None else physical_time),
        members,
        np.asarray(manifest.critic_global_features, dtype=np.float32),
        critic_global_dim=architecture["critic_global_dim"],
        frontier=tuple(manifest.frontier if frontier is None else frontier),
    )


def normalize_to_manifest(
    core: vre.VariableRosterEventCore,
    manifest: ResetManifest,
    *,
    profile: str,
) -> None:
    """Erase the provenance branch at the actor-read boundary.

    This is what makes ``K_{p,0} = K_{p,1}`` a test of leakage rather than a
    tautology: the histories really ran, and only the registered actor-read
    fields are put back.  What survives depends on the registered profile --
    see the module docstring.
    """
    if profile not in NORMALIZATION_PROFILES:
        raise ValueError(f"unregistered normalization profile {profile!r}")
    core.physical_time = int(manifest.physical_time)
    core.policy_version = int(manifest.policy_version)
    fields = ACTOR_READ_RECORD_FIELDS + (
        PROVENANCE_ONLY_RECORD_FIELDS if profile == PROVENANCE_LABEL else ()
    )
    for owner in manifest.owners:
        record = core.records[owner.lifecycle_key]
        for name in fields:
            value = getattr(owner, name)
            if isinstance(value, np.ndarray):
                value = value.astype(np.float32).copy()
            setattr(record, name, value)
        record.active_gap_remaining = int(owner.active_gap_remaining)
        if profile == PROVENANCE_LABEL:
            record.last_policy_event_time = None
        # A capture must not be preceded by an open trace: Pro requires it
        # outright for the wrong-owner branches, and it keeps `_close_trace`
        # from appending a branch-dependent row before the kernel is produced.
        record.open_event_trace = None
    if profile == PROVENANCE_LABEL:
        for name, generator in (
            ("opportunity_rng_state", core.opportunity_rng),
            ("frontier_order_rng_state", core.frontier_rng),
            ("policy_action_rng_state", core.action_rng),
        ):
            generator.bit_generator.state = _copy_state(manifest.rng_states[name])


def manifest_from_core(
    core: vre.VariableRosterEventCore,
    *,
    target_lifecycle_key: str,
    frontier: Sequence[str],
    target_token_order: Sequence[str],
    observations: Mapping[str, np.ndarray],
    critic_member_features: Mapping[str, np.ndarray],
    critic_global_features: np.ndarray,
) -> ResetManifest:
    """Read a canonical manifest off a core in a state chosen as canonical.

    Registration, not restoration: the values are copied out ONCE, frozen, and
    from then on the manifest is the authority.  ``construct_reset_runtime``
    never sees the core they came from.
    """
    snapshot = bs.capture(core)
    owners = tuple(
        OwnerManifest(
            lifecycle_key=key,
            membership_epoch=int(record.membership_epoch),
            status=str(record.status),
            active_skill=(
                None if record.active_skill is None else int(record.active_skill)
            ),
            skill_active_age=int(record.skill_active_age),
            active_gap_remaining=int(record.active_gap_remaining or 0),
            is_genuine_join=bool(record.is_genuine_join),
            is_rejoin=bool(record.is_rejoin),
            high_hidden=np.asarray(record.high_hidden, dtype=np.float32).copy(),
            observation=np.asarray(observations[key], dtype=np.float32).copy(),
            critic_member_features=np.asarray(
                critic_member_features[key], dtype=np.float32
            ).copy(),
        )
        for key, record in core.records.items()
    )
    return ResetManifest(
        architecture=dict(snapshot.architecture),
        model_states=dict(snapshot.model_states),
        rng_identity={
            name: int(getattr(core, name))
            for name in (
                "rng_episode_id",
                "opportunity_master_seed",
                "frontier_master_seed",
                "action_master_seed",
                "opportunity_stream_id",
                "frontier_stream_id",
                "action_stream_id",
            )
        },
        rng_states={
            "opportunity_rng_state": snapshot.rng_states["opportunity_rng"],
            "frontier_order_rng_state": snapshot.rng_states["frontier_rng"],
            "policy_action_rng_state": snapshot.rng_states["action_rng"],
        },
        physical_time=int(core.physical_time),
        policy_version=int(core.policy_version),
        owners=owners,
        critic_global_features=np.asarray(
            critic_global_features, dtype=np.float32
        ).copy(),
        target_lifecycle_key=str(target_lifecycle_key),
        frontier=tuple(frontier),
        target_token_order=tuple(target_token_order),
        legal_action_support=np.ones(core.n_skills, dtype=np.bool_),
    )
