"""Immutable public tapes and evaluator-only views for CBSC-OMRC-B01."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import TYPE_CHECKING, Mapping, Sequence

from .addressing import B0_RUN, EVAL_MOTIF, EVAL_STOCHASTIC, TRAIN, Address
from .contract import Action, EPISODE_TRANSITIONS, OPPORTUNITY_COUNT
from .ledger import NativeLedger
from .token import LITERAL_TOKEN_CODEC, LearnerProjection, PrimitiveToken

if TYPE_CHECKING:
    from .host import DecisionTruth, DynamicHost


@dataclass(frozen=True)
class TapeIdentity:
    run_name: str
    seed: int
    split: str
    episode_id: int


@dataclass(frozen=True)
class MotifDescriptor:
    tape_id: int
    family: int
    target_receiver: int
    presented_slot: int

    def __post_init__(self) -> None:
        if not 0 <= self.tape_id < 32:
            raise ValueError("motif tape_id must be in [0, 31]")
        if self.tape_id != 4 * self.family + 2 * self.target_receiver + self.presented_slot:
            raise ValueError("motif tape_id does not match 4*m + 2*r + s")


@dataclass(frozen=True)
class TapeGenerationAudit:
    owner_tokens_consumed: int
    epoch_tokens_consumed: int
    draw_count: int
    draw_digest: str
    draw_addresses: tuple[Address, ...]

    def __post_init__(self) -> None:
        if not 2 <= self.owner_tokens_consumed <= 26:
            raise ValueError("OWNER pool consumption is outside the 24-opportunity bound")
        if not 2 <= self.epoch_tokens_consumed <= 26:
            raise ValueError("epoch pool consumption is outside the 24-opportunity bound")
        if self.draw_count != len(self.draw_addresses):
            raise ValueError("draw_count does not match unique audited addresses")


@dataclass(frozen=True)
class EpisodeTape:
    """One action-independent 152-token episode.

    ``learner_tokens`` exposes only immutable 17-byte public projections.  The
    host state, validity, oracle, ledger, and motif labels are accessible only
    by explicitly requesting the evaluator view.
    """

    identity: TapeIdentity
    public_tokens: tuple[PrimitiveToken, ...]
    _packed_tokens: tuple[bytes, ...]
    _decision_truth: tuple["DecisionTruth", ...]
    generation_audit: TapeGenerationAudit
    motif: MotifDescriptor | None = None

    def __post_init__(self) -> None:
        if len(self.public_tokens) != EPISODE_TRANSITIONS:
            raise ValueError("an episode tape must contain exactly 152 public tokens")
        if len(self._packed_tokens) != EPISODE_TRANSITIONS:
            raise ValueError("packed-token count must equal public-token count")
        if any(not isinstance(item, bytes) or len(item) != 17 for item in self._packed_tokens):
            raise ValueError("every packed public token must contain exactly 17 bytes")
        canonical = tuple(LITERAL_TOKEN_CODEC.pack(token) for token in self.public_tokens)
        if self._packed_tokens != canonical:
            raise ValueError("packed learner bytes do not match the canonical public tokens")
        if len(self._decision_truth) != OPPORTUNITY_COUNT:
            raise ValueError("an episode tape must contain exactly 24 evaluator decisions")
        if sum(item[0] == 0x20 for item in self._packed_tokens) != OPPORTUNITY_COUNT:
            raise ValueError("an episode tape must contain exactly 24 DECISION tokens")
        if sum(item[0] == 0x21 for item in self._packed_tokens) != OPPORTUNITY_COUNT:
            raise ValueError("an episode tape must contain exactly 24 SETTLEMENT tokens")
        if self.identity.split == EVAL_MOTIF:
            if self.motif is None or self.identity.episode_id != self.motif.tape_id:
                raise ValueError("EVAL_MOTIF tapes require the matching motif descriptor")
        elif self.motif is not None:
            raise ValueError("motif metadata is evaluator-only and exclusive to EVAL_MOTIF")

    def learner_tokens(self) -> tuple[LearnerProjection, ...]:
        return tuple(LearnerProjection(item) for item in self._packed_tokens)

    def evaluator(self) -> "EpisodeEvaluator":
        return EpisodeEvaluator(self._decision_truth, self.motif)

    @property
    def primitive_digest(self) -> str:
        hasher = hashlib.sha256()
        for packed in self._packed_tokens:
            hasher.update(packed)
        return hasher.hexdigest()

    @property
    def transition_count(self) -> int:
        return len(self.public_tokens)

    @property
    def decision_count(self) -> int:
        return len(self._decision_truth)


class EpisodeEvaluator:
    """Deliberately separate evaluator-only truth and exact ledger surface."""

    __slots__ = ("_truth", "motif")

    def __init__(
        self, truth: tuple["DecisionTruth", ...], motif: MotifDescriptor | None
    ) -> None:
        self._truth = truth
        self.motif = motif

    def truth(self, opportunity_index: int) -> "DecisionTruth":
        if isinstance(opportunity_index, bool) or not isinstance(opportunity_index, int):
            raise TypeError("opportunity_index must be int")
        return self._truth[opportunity_index]

    def ledger(self, opportunity_index: int, action: Action) -> NativeLedger:
        return self.truth(opportunity_index).ledger(action)


@dataclass(frozen=True)
class PrimitiveParityAudit:
    passed: bool
    compared_arms: tuple[str, ...]
    episode_count: int
    mismatches: tuple[str, ...]


def primitive_history_parity(
    tapes_by_arm: Mapping[str, Sequence[EpisodeTape]],
) -> PrimitiveParityAudit:
    arms = tuple(sorted(tapes_by_arm))
    if not arms:
        raise ValueError("at least one arm is required for parity")
    reference = tuple(tapes_by_arm[arms[0]])
    mismatches: list[str] = []
    for arm in arms[1:]:
        candidate = tuple(tapes_by_arm[arm])
        if len(candidate) != len(reference):
            mismatches.append(f"{arm}:episode_count")
            continue
        for index, (left, right) in enumerate(zip(reference, candidate)):
            if left.identity != right.identity or left.primitive_digest != right.primitive_digest:
                mismatches.append(f"{arm}:episode_{index}")
    return PrimitiveParityAudit(not mismatches, arms, len(reference), tuple(mismatches))


@dataclass(frozen=True)
class B0TapePanel:
    train: tuple[EpisodeTape, ...]
    eval_stochastic: tuple[EpisodeTape, ...]
    eval_motif: tuple[EpisodeTape, ...]

    def __post_init__(self) -> None:
        if len(self.train) != 8 or len(self.eval_stochastic) != 4 or len(self.eval_motif) != 4:
            raise ValueError("B0 panel must be 8 TRAIN + 4 stochastic + 4 motif tapes")
        if tuple(t.identity.episode_id for t in self.train) != tuple(range(8)):
            raise ValueError("B0 TRAIN roots must be episode_id 0..7")
        if tuple(t.identity.episode_id for t in self.eval_stochastic) != (0, 1, 2, 3):
            raise ValueError("B0 stochastic roots must be episode_id 0..3")
        if tuple(t.identity.episode_id for t in self.eval_motif) != (0, 12, 20, 28):
            raise ValueError("B0 motif roots must be tape_id 0,12,20,28")
        address_sets = [
            {address for tape in group for address in tape.generation_audit.draw_addresses}
            for group in (self.train, self.eval_stochastic, self.eval_motif)
        ]
        if any(address_sets[i] & address_sets[j] for i in range(3) for j in range(i + 1, 3)):
            raise ValueError("TRAIN and held-out address spaces must be disjoint")

    @property
    def execution_count(self) -> int:
        return len(self.train) + len(self.eval_stochastic) + len(self.eval_motif)


def motif_descriptor(tape_id: int) -> MotifDescriptor:
    if isinstance(tape_id, bool) or not isinstance(tape_id, int) or not 0 <= tape_id < 32:
        raise ValueError("motif tape_id must be in [0, 31]")
    family, residual = divmod(tape_id, 4)
    receiver, slot = divmod(residual, 2)
    return MotifDescriptor(tape_id, family, receiver, slot)


def build_motif_panel(host: "DynamicHost") -> tuple[EpisodeTape, ...]:
    return tuple(host.build_motif(tape_id) for tape_id in range(32))


def build_b0_panel(host: "DynamicHost") -> B0TapePanel:
    if host.run_name != B0_RUN or host.seed != 21001:
        raise ValueError("B0 panel requires CBSC-OMRC-B0-INSTRUMENT seed 21001")
    return B0TapePanel(
        train=tuple(host.build_stochastic(TRAIN, episode_id) for episode_id in range(8)),
        eval_stochastic=tuple(
            host.build_stochastic(EVAL_STOCHASTIC, episode_id) for episode_id in range(4)
        ),
        eval_motif=tuple(host.build_motif(tape_id) for tape_id in (0, 12, 20, 28)),
    )
