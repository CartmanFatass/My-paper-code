"""Nonregistered S1 fixture identity and byte-immutability witnesses."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

from torch import nn

from .foundation_contract import REPLICATE_COUNT, S1_SLICE


class FoundationMutationError(ValueError):
    pass


@dataclass(frozen=True)
class TechnicalReplicateIdentity:
    schema: str
    namespace: str
    replicate_index: int
    registered: bool
    eligible: bool
    activity_authorized: bool


@dataclass(frozen=True)
class FoundationImmutabilityWitness:
    schema: str
    identity_sha256: str
    foundation_sha256: str


def technical_replicate_identity(replicate_index: int) -> TechnicalReplicateIdentity:
    if (
        isinstance(replicate_index, bool)
        or not isinstance(replicate_index, int)
        or not 0 <= replicate_index < REPLICATE_COUNT
    ):
        raise ValueError("replicate_index must be an integer in [0,24)")
    return TechnicalReplicateIdentity(
        schema="SCDMP_NATIVE_FUSION_R01_S1_TECHNICAL_REPLICATE_IDENTITY_V1",
        namespace=f"{S1_SLICE}/nonregistered-technical-fixture/{replicate_index:08d}",
        replicate_index=replicate_index,
        registered=False,
        eligible=False,
        activity_authorized=False,
    )


def _identity_digest(identity: TechnicalReplicateIdentity) -> str:
    payload = json.dumps(
        asdict(identity), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _foundation_digest(foundation: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, parameter in foundation.named_parameters():
        tensor = parameter.detach().cpu().contiguous()
        digest.update(name.encode("ascii"))
        digest.update(b"\0")
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(b"\0")
        digest.update(json.dumps(list(tensor.shape), separators=(",", ":")).encode("ascii"))
        digest.update(b"\0")
        digest.update(tensor.numpy().tobytes(order="C"))
    return digest.hexdigest()


def seal_technical_foundation(
    foundation: nn.Module, identity: TechnicalReplicateIdentity
) -> FoundationImmutabilityWitness:
    if identity.registered or identity.eligible or identity.activity_authorized:
        raise ValueError("S1 technical identity must remain nonregistered and ineligible")
    foundation.requires_grad_(False)
    return FoundationImmutabilityWitness(
        schema="SCDMP_NATIVE_FUSION_R01_S1_FOUNDATION_IMMUTABILITY_V1",
        identity_sha256=_identity_digest(identity),
        foundation_sha256=_foundation_digest(foundation),
    )


def verify_immutability(
    foundation: nn.Module,
    identity: TechnicalReplicateIdentity,
    witness: FoundationImmutabilityWitness,
) -> None:
    if _identity_digest(identity) != witness.identity_sha256:
        raise FoundationMutationError("technical replicate identity changed")
    if _foundation_digest(foundation) != witness.foundation_sha256:
        raise FoundationMutationError("foundation bytes changed after sealing")
    if any(parameter.requires_grad for parameter in foundation.parameters()):
        raise FoundationMutationError("sealed foundation trainability changed")
