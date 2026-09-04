"""FOLR common-snapshot branch cloner.

Sequence 01, component 2 of the object graph External Pro required in ruling
``FOLR_S03_BINDING_SELECTED``
(``local_research/pro_reviews/folr_core_v6_s03_binding_v1/40_RAW_RESPONSE.md``,
sha256 ``9ca274d2…``, VERBATIM_OK).

WHY A CLONER AT ALL
-------------------
Every branch of the design begins from one shared pretreatment state:

    Restore the same common pretreatment snapshot.

and the fixed-payload nulls ``K_{p,0} = K_{p,1}`` are only evidence if the two
branches really did start identically apart from the registered difference.  Pro
was explicit that checkpoint restoration is the right *mechanism* for this:

    Checkpoint restoration faithfully preserves all of those objects and all
    three PCG64 states; it is an appropriate common-snapshot cloning mechanism,
    not a reset.

``VariableRosterEventCore.checkpoint_payload`` is that mechanism, but it demands
a collector, optimizer states and normalizer states which this experiment does
not have, and it routes through ``collector.restore_event_runtime``.  So this
module reproduces its *core-side* field set directly.  Which raises the obvious
risk, and the reason for the closure guard below.

THE CLOSURE GUARD IS THE LOAD-BEARING PART
------------------------------------------
A cloner that silently misses one mutable field would not fail loudly -- it
would make the fixed-payload nulls pass for the wrong reason, because the
branches would share whatever the cloner forgot.  That is a fabricated null, and
it is the single worst failure this component can have.

So the field partition is declared explicitly and
``test_the_partition_covers_every_core_attribute`` asserts that

    vars(core) == ARCHITECTURE | MODELS | HOOKS | MUTABLE_STATE

exactly.  A future field added to the runtime lands in none of the four sets and
breaks that test, rather than quietly escaping the clone.

DIGESTS REFUSE WHAT THEY CANNOT ENCODE
--------------------------------------
``snapshot_digest`` raises on any type it does not know how to canonicalize.
The alternative -- falling back to ``repr()`` -- would embed CPython object
addresses in the digest, so a snapshot would compare unequal to itself across
processes and equal to nothing.  Failing closed is the only safe default for an
object whose whole job is to certify sameness.
"""

from __future__ import annotations

import dataclasses
import hashlib
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
import torch

from ha_ctse_process.variable_roster_event import VariableRosterEventCore

RAW_OUTPUT_BINDING = "folr_core.branch_snapshot.v1"

#: Fixed at construction and *validated* rather than assigned by
#: ``restore_checkpoint_payload``; a branch that differed here would not be the
#: same experiment at all.
ARCHITECTURE_FIELDS = (
    "architecture_mode",
    "runtime_mode",
    "partner_interaction_enabled",
    "obs_dim",
    "critic_member_dim",
    "critic_global_dim",
    "n_skills",
    "action_dim",
    "member_hidden_dim",
    "high_hidden_dim",
    "low_hidden_dim",
    "skill_embedding_dim",
    "action_space_type",
    "gamma",
    "gae_lambda",
    "environment_index",
    "device",
)

#: Cloned through ``state_dict``.  Pro requires "byte-identical model
#: parameters" across branches and a model digest in the witness.
MODEL_FIELDS = ("commitment_model", "event_critic", "low_actor", "low_critic")

#: Experiment instrumentation.  Deliberately NOT part of the snapshot: the
#: harness installs a fresh sink per branch, and cloning a sink would carry one
#: branch's captures into the next.
HOOK_FIELDS = ("_kernel_capture", "_preframe_intervention")

#: Everything the runtime mutates.  Mirrors the core-side field set of
#: ``checkpoint_payload``; the RNG generators are cloned by their exact PCG64
#: ``bit_generator.state``, as Pro requires.
MUTABLE_STATE_FIELDS = (
    "rng_episode_id",
    "opportunity_master_seed",
    "frontier_master_seed",
    "action_master_seed",
    "opportunity_stream_id",
    "frontier_stream_id",
    "action_stream_id",
    "policy_version",
    "physical_time",
    "records",
    "high_ledger",
    "closed_event_rows",
    "low_ledger",
    "low_chunk_boundaries",
    "current_observation_state_boundary",
    "pending_membership_transaction",
)

RNG_FIELDS = ("opportunity_rng", "frontier_rng", "action_rng")


# ---------------------------------------------------------------------------
# Canonical encoding
# ---------------------------------------------------------------------------


class UnencodableState(TypeError):
    """Raised rather than digesting something address-dependent."""


def _canonical(value: Any, hasher: "hashlib._Hash") -> None:
    """Feed ``value`` to ``hasher`` deterministically, or refuse."""
    if value is None:
        hasher.update(b"none")
    elif isinstance(value, bool):
        hasher.update(b"bool:" + str(value).encode("utf-8"))
    elif isinstance(value, (int, np.integer)):
        hasher.update(b"int:" + str(int(value)).encode("utf-8"))
    elif isinstance(value, (float, np.floating)):
        # repr of a float round-trips exactly in CPython; str() does not for
        # every value, and the digest must separate values that differ in the
        # last bit.
        hasher.update(b"float:" + repr(float(value)).encode("utf-8"))
    elif isinstance(value, str):
        hasher.update(b"str:" + value.encode("utf-8"))
    elif isinstance(value, bytes):
        hasher.update(b"bytes:" + value)
    elif isinstance(value, np.ndarray):
        contiguous = np.ascontiguousarray(value)
        hasher.update(b"ndarray:")
        hasher.update(str(contiguous.dtype).encode("utf-8"))
        hasher.update(str(contiguous.shape).encode("utf-8"))
        hasher.update(contiguous.tobytes())
    elif isinstance(value, torch.Tensor):
        _canonical(value.detach().cpu().numpy(), hasher)
    elif isinstance(value, torch.device):
        hasher.update(b"device:" + str(value).encode("utf-8"))
    elif isinstance(value, (list, tuple)):
        hasher.update(f"seq:{len(value)}:".encode("utf-8"))
        for item in value:
            _canonical(item, hasher)
    elif isinstance(value, Mapping):
        hasher.update(f"map:{len(value)}:".encode("utf-8"))
        for key in sorted(value, key=repr):
            _canonical(key, hasher)
            _canonical(value[key], hasher)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        hasher.update(b"dataclass:" + type(value).__qualname__.encode("utf-8"))
        for field in dataclasses.fields(value):
            hasher.update(field.name.encode("utf-8"))
            _canonical(getattr(value, field.name), hasher)
    else:
        raise UnencodableState(
            f"refusing to digest {type(value).__qualname__}: a repr() fallback "
            "would embed an object address and make the digest irreproducible"
        )


def digest_of(value: Any) -> str:
    hasher = hashlib.sha256()
    hasher.update(RAW_OUTPUT_BINDING.encode("utf-8"))
    _canonical(value, hasher)
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# The snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoreSnapshot:
    """One common pretreatment state, restorable into any matching core."""

    architecture: dict[str, Any]
    model_states: dict[str, Any]
    mutable_state: dict[str, Any]
    rng_states: dict[str, Any]

    def digest(self) -> str:
        """Digest over the WHOLE snapshot, architecture included."""
        return digest_of(
            {
                "architecture": {
                    name: (str(value) if name == "device" else value)
                    for name, value in self.architecture.items()
                },
                "model_states": self.model_states,
                "mutable_state": self.mutable_state,
                "rng_states": self.rng_states,
            }
        )


def capture(core: VariableRosterEventCore) -> CoreSnapshot:
    """Deep-copy the core's complete cloneable state."""
    return CoreSnapshot(
        architecture={name: getattr(core, name) for name in ARCHITECTURE_FIELDS},
        model_states={
            name: deepcopy(getattr(core, name).state_dict()) for name in MODEL_FIELDS
        },
        mutable_state={
            # Records go through the runtime's OWN serializer, so the clone
            # cannot drift from how the runtime itself round-trips a record.
            name: (
                {
                    key: VariableRosterEventCore._record_to_state(record)
                    for key, record in getattr(core, name).items()
                }
                if name == "records"
                else deepcopy(getattr(core, name))
            )
            for name in MUTABLE_STATE_FIELDS
        },
        rng_states={
            name: deepcopy(getattr(core, name).bit_generator.state)
            for name in RNG_FIELDS
        },
    )


def restore(core: VariableRosterEventCore, snapshot: CoreSnapshot) -> None:
    """Write a snapshot back into ``core``, refusing an architecture mismatch."""
    for name in ARCHITECTURE_FIELDS:
        current, wanted = getattr(core, name), snapshot.architecture[name]
        if str(current) != str(wanted):
            raise ValueError(
                f"FOLR snapshot architecture mismatch on {name}: "
                f"core={current!r} snapshot={wanted!r}"
            )
    for name in MODEL_FIELDS:
        getattr(core, name).load_state_dict(
            deepcopy(snapshot.model_states[name]), strict=True
        )
    for name in MUTABLE_STATE_FIELDS:
        value = snapshot.mutable_state[name]
        if name == "records":
            setattr(
                core,
                name,
                {
                    str(key): VariableRosterEventCore._record_from_state(state)
                    for key, state in value.items()
                },
            )
        else:
            setattr(core, name, deepcopy(value))
    for name in RNG_FIELDS:
        getattr(core, name).bit_generator.state = deepcopy(snapshot.rng_states[name])


def live_digest(core: VariableRosterEventCore) -> str:
    """Digest of the core's current state, without holding a snapshot."""
    return capture(core).digest()
