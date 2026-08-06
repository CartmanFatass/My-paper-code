"""FOLR S03 binding manifest and direct-kernel capture sink.

Sequence 01, components 1 and 4 of the object graph External Pro required in
ruling ``FOLR_S03_BINDING_SELECTED``
(``local_research/pro_reviews/folr_core_v6_s03_binding_v1/40_RAW_RESPONSE.md``,
sha256 ``9ca274d2…``, VERBATIM_OK).

THE BINDING, VERBATIM
---------------------
    S03 must bind to: The complete float32 value of LifecycleRecord.high_hidden
    for one registered (lifecycle_key, membership_epoch), as materialized into
    pre_hidden for that owner's first target token.

and on the registry:

    It is permissible for only one coordinate to differ, but the registry must
    own and hash the entire vectors, not merely state that "coordinate zero
    contains the bit." This prevents uncontrolled complementary coordinates.

``S03Binding`` is that registry.  It hashes ``h0``, ``h1`` and ``h_neutral``
whole, and refuses vectors that differ in shape or dtype.

WHY THE CAPTURE SINK EXISTS
---------------------------
Pro rejected replay alone as the freshness witness:

    Capture the full masked probability vector inside _process_frontier: after
    masked_logits is constructed; after softmax; before action selection; before
    action-RNG consumption; before opportunity-gap sampling; for target token
    position zero.

    The current row records only the selected action's log probability, not the
    complete directly produced kernel.

``KernelCaptureSink`` is installed on the core through
``VariableRosterEventCore.install_kernel_capture`` and fills the optional
``EventTokenRow`` witness fields at exactly that point.  With no sink installed
the core's execution path is unchanged; computing a softmax consumes no RNG, so
an installed sink cannot perturb determinism either.

WHAT THIS MODULE DOES NOT DO
----------------------------
It does not decide anything.  It records.  The reset constructor, the branch
cloner, the eight branches, the freshness certificate and the outcome controller
are separate components, and the scientific reading of any kernel difference
belongs to External Pro.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import torch

RAW_OUTPUT_BINDING = "folr_core.s03_binding.v1"

#: The registered payload slots.  ``NEUTRAL`` is the target-neutral value the
#: wrong-owner branches hold the target at.
PAYLOAD_ZERO = "h0"
PAYLOAD_ONE = "h1"
PAYLOAD_NEUTRAL = "h_neutral"
PAYLOAD_SLOTS = (PAYLOAD_ZERO, PAYLOAD_ONE, PAYLOAD_NEUTRAL)


def _digest_array(array: np.ndarray) -> str:
    """Content digest over dtype, shape and exact bytes."""
    contiguous = np.ascontiguousarray(array)
    hasher = hashlib.sha256()
    hasher.update(str(contiguous.dtype).encode("utf-8"))
    hasher.update(str(contiguous.shape).encode("utf-8"))
    hasher.update(contiguous.tobytes())
    return hasher.hexdigest()


#: Public name for the same digest.  Pro's payload-read certificate asks for
#: "whole-vector dtype/shape/byte digests", which is exactly what
#: ``_digest_array`` computes, so the certificate reuses it rather than
#: introducing a second hashing convention that could drift from the registry's.
vector_digest = _digest_array


def _as_float32(value: Any) -> np.ndarray:
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()
    array = np.asarray(value, dtype=np.float32)
    return np.ascontiguousarray(array)


@dataclass(frozen=True)
class S03Binding:
    """The registered S03 payload set for one target owner.

    ``h0``/``h1`` are the contrasted payloads; ``h_neutral`` is the value the
    target is held at in the wrong-owner branches.  All three are complete
    float32 vectors and all three are hashed whole.
    """

    target_lifecycle_key: str
    target_membership_epoch: int
    shadow_lifecycle_key: str
    shadow_membership_epoch: int
    h0: np.ndarray
    h1: np.ndarray
    h_neutral: np.ndarray

    def __post_init__(self) -> None:
        vectors = (self.h0, self.h1, self.h_neutral)
        shapes = {vector.shape for vector in vectors}
        dtypes = {vector.dtype for vector in vectors}
        if len(shapes) != 1:
            raise ValueError("FOLR payload vectors must share one shape")
        if dtypes != {np.dtype(np.float32)}:
            raise ValueError("FOLR payload vectors must be float32")
        if _digest_array(self.h0) == _digest_array(self.h1):
            raise ValueError("FOLR h0 and h1 must differ or the contrast is empty")
        if self.target_lifecycle_key == self.shadow_lifecycle_key:
            raise ValueError("FOLR shadow owner must differ from the target")

    @classmethod
    def build(
        cls,
        *,
        target_lifecycle_key: str,
        target_membership_epoch: int,
        shadow_lifecycle_key: str,
        shadow_membership_epoch: int,
        h0: Any,
        h1: Any,
        h_neutral: Any,
    ) -> "S03Binding":
        return cls(
            target_lifecycle_key=str(target_lifecycle_key),
            target_membership_epoch=int(target_membership_epoch),
            shadow_lifecycle_key=str(shadow_lifecycle_key),
            shadow_membership_epoch=int(shadow_membership_epoch),
            h0=_as_float32(h0),
            h1=_as_float32(h1),
            h_neutral=_as_float32(h_neutral),
        )

    def payload(self, slot: str) -> np.ndarray:
        if slot not in PAYLOAD_SLOTS:
            raise ValueError(f"unregistered payload slot {slot!r}")
        return {
            PAYLOAD_ZERO: self.h0,
            PAYLOAD_ONE: self.h1,
            PAYLOAD_NEUTRAL: self.h_neutral,
        }[slot].copy()

    def manifest_digest(self) -> str:
        """Digest of the WHOLE registry, not of the differing coordinate."""
        hasher = hashlib.sha256()
        hasher.update(RAW_OUTPUT_BINDING.encode("utf-8"))
        hasher.update(self.target_lifecycle_key.encode("utf-8"))
        hasher.update(str(self.target_membership_epoch).encode("utf-8"))
        hasher.update(self.shadow_lifecycle_key.encode("utf-8"))
        hasher.update(str(self.shadow_membership_epoch).encode("utf-8"))
        for slot in PAYLOAD_SLOTS:
            hasher.update(slot.encode("utf-8"))
            hasher.update(_digest_array(self.payload(slot)).encode("utf-8"))
        return hasher.hexdigest()

    def registry(self) -> dict[str, object]:
        return {
            "raw_output_binding": RAW_OUTPUT_BINDING,
            "target": [self.target_lifecycle_key, self.target_membership_epoch],
            "shadow": [self.shadow_lifecycle_key, self.shadow_membership_epoch],
            "payload_digests": {
                slot: _digest_array(self.payload(slot)) for slot in PAYLOAD_SLOTS
            },
            "payload_shape": list(self.h0.shape),
            "manifest_digest": self.manifest_digest(),
        }


def model_state_digest(model: torch.nn.Module) -> str:
    hasher = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        hasher.update(name.encode("utf-8"))
        hasher.update(_digest_array(tensor.detach().cpu().numpy()).encode("utf-8"))
    return hasher.hexdigest()


def actor_preimage_digest(preimage: Mapping[str, Any]) -> str:
    """Digest the complete actor-read preimage OTHER THAN S03.

    ``pre_token_high_hidden`` is deliberately excluded: it *is* S03, and a
    digest that included it could never be equal across the payload contrast,
    which would make the closure certificate vacuous.
    """
    hasher = hashlib.sha256()
    for name in sorted(preimage):
        if name == "pre_token_high_hidden":
            continue
        value = preimage[name]
        hasher.update(name.encode("utf-8"))
        if isinstance(value, (str, int)):
            hasher.update(str(value).encode("utf-8"))
        elif isinstance(value, (tuple, list)) and (
            not value or isinstance(value[0], (str, int))
        ):
            hasher.update(repr(tuple(value)).encode("utf-8"))
        else:
            hasher.update(_digest_array(_as_float32(value)).encode("utf-8"))
    return hasher.hexdigest()


@dataclass(frozen=True)
class DirectKernel:
    """One directly captured kernel, at Pro's exact capture point."""

    owner_lifecycle_key: str
    membership_epoch: int
    token_position: int
    masked_logits: np.ndarray
    probabilities: np.ndarray
    actor_preimage_digest: str
    model_state_digest: str
    common_snapshot_digest: str
    intervention_manifest_digest: str

    def row_fields(self) -> dict[str, object]:
        """The optional ``EventTokenRow`` witness fields."""
        return {
            "direct_masked_logits": self.masked_logits,
            "direct_probabilities": self.probabilities,
            "actor_preimage_digest": self.actor_preimage_digest,
            "model_state_digest": self.model_state_digest,
            "common_snapshot_digest": self.common_snapshot_digest,
            "intervention_manifest_digest": self.intervention_manifest_digest,
        }


class KernelCaptureSink:
    """Records the target's first kernel; ignores every other token.

    Installed via ``core.install_kernel_capture(sink)``.  It never mutates core
    state, never consumes RNG and never influences action selection.
    """

    def __init__(
        self,
        *,
        binding: S03Binding,
        model_digest: str,
        snapshot_digest: str,
        target_only: bool = True,
    ):
        self.binding = binding
        self.model_digest = str(model_digest)
        self.snapshot_digest = str(snapshot_digest)
        self.target_only = bool(target_only)
        self.captures: list[DirectKernel] = []

    def capture(
        self,
        *,
        owner_lifecycle_key: str,
        membership_epoch: int,
        token_position: int,
        masked_logits: torch.Tensor,
        probabilities: torch.Tensor,
        preimage: Mapping[str, Any],
    ) -> DirectKernel | None:
        if self.target_only and (
            owner_lifecycle_key != self.binding.target_lifecycle_key
            or int(membership_epoch) != self.binding.target_membership_epoch
        ):
            return None
        kernel = DirectKernel(
            owner_lifecycle_key=str(owner_lifecycle_key),
            membership_epoch=int(membership_epoch),
            token_position=int(token_position),
            # float32 throughout: Pro requires bitwise equality on the directly
            # captured float32 vector, not on a widened copy.
            masked_logits=masked_logits.detach().cpu().numpy().astype(np.float32).copy(),
            probabilities=probabilities.detach().cpu().numpy().astype(np.float32).copy(),
            actor_preimage_digest=actor_preimage_digest(preimage),
            model_state_digest=self.model_digest,
            common_snapshot_digest=self.snapshot_digest,
            intervention_manifest_digest=self.binding.manifest_digest(),
        )
        self.captures.append(kernel)
        return kernel

    def first(self) -> DirectKernel:
        if not self.captures:
            raise RuntimeError("FOLR capture sink recorded no target kernel")
        return self.captures[0]


def kernels_bitwise_equal(left: DirectKernel, right: DirectKernel) -> bool:
    """Pro: 'Use bitwise equality on the directly captured float32 vector.'"""
    return (
        left.probabilities.dtype == right.probabilities.dtype == np.dtype(np.float32)
        and left.probabilities.shape == right.probabilities.shape
        and left.probabilities.tobytes() == right.probabilities.tobytes()
    )


def kernel_infinity_norm(left: DirectKernel, right: DirectKernel) -> float:
    """The registered positive discriminator ||K1 - K0||_inf."""
    return float(
        np.max(np.abs(left.probabilities.astype(np.float64) - right.probabilities.astype(np.float64)))
    )
