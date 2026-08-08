"""EOCIV sibling environment: G32 base + directed focal payload with hidden shock.

Sequence 07 sibling implementation.  External ruling
``EOCIV_SIBLING_CAPABILITY_REQUIRED`` (archived at
``local_research/pro_reviews/eociv_population_v1/``) selected population C —
directed, active teammate-payload edges at the three post-membership lifecycle
boundaries t in {12, 24, 36} — and held that the unchanged continuous-roster
environment cannot carry the EOCIV outcome claim: its optimum needs no teammate
information, and its policy interface exposes no first-class directed payload
gate.  Pro's words: "This is not a park: the lifecycle population is identified,
and the missing capability has a bounded construction."

This module is that bounded construction: a separately registered sibling that
wraps — never replaces — ``RuntimeCapacityRosterEnv``, adding exactly the six
ruling ingredients and nothing else.

THE SIX INGREDIENTS, ONE FOR ONE
--------------------------------
1. *Exact base projection.*  ``intervention_enabled=False`` reproduces the base
   environment exactly — same lifecycle schedule, active masks, member keys,
   observations, action legality, reward trace, termination and seeded ledger.
   The wrapper holds a real ``RuntimeCapacityRosterEnv`` and, when disabled,
   passes its views and rewards through untouched.

2. *Explicit focal receiver-ingestion channel.*  Before any active-set
   aggregation a policy might perform, the sibling exposes one directed
   source-to-receiver payload per lifecycle event:

       source owner receipt -> source payload body -> EOCIV actuation
       -> receiver ingestion -> fixed aggregation/routing -> actor action

   Routing order, edge cardinality and nonfocal content are computed from the
   ledger and the lifecycle receipts only — never from the focal body or the
   valve decision, so masking cannot signal through topology.

3. *Payoff-relevant but owner-agnostic hidden context.*  A deterministic,
   ledger-seeded, segment-persistent anonymous route-demand shock: in a
   CRITICAL cell the segment's service target is multiplied by a registered
   coefficient c_z for a hidden state z in {A, B}; in a NEUTRAL cell z is
   deterministically NONE (multiplier 1).  The shock is not disclosed in any
   member's observation nor in ``W_minus`` — observations keep publishing the
   base (unshocked) load and mix.  The focal source receives the legitimate
   pre-action signal (the payload body carries z); the shock law is independent
   of member identity, and the signal-carrying owner is assigned by the ledger,
   not by an owner-specific reward branch.

4. *Registered native neutral.*  ``NEUTRALIZE_FOCAL_PAYLOAD`` replaces only the
   focal body with the canonical no-information token ``NEUTRAL_TOKEN``, keeping
   the same active mask, directed-edge envelope, routing order, tensor shape,
   timing and declared ingestion cost as the real branch.  The token carries no
   source key, epoch, event kind, age, payload label, reward, outcome or gate
   decision.  It is part of the sibling's support — a legal receiver input, not
   a post-hoc zero tensor.

5. *Four independent arm routes.*  LS / LR / CS / CR, with ``D_C`` a
   precommitted propensity-bearing control tape keyed only by pre-outcome
   cluster identifiers (episode id, lifecycle event index).  The tape may not
   read the payload body, reward, post-event state or learned decision — its
   key type makes that structural.

6. *Exact pre-PPO capability gate.*  ``capability_gate.py`` — ten deterministic
   checks; no training budget before it passes.

LIFECYCLE FSM (the epoch correction)
------------------------------------
Pro's explicit correction: "Do not use the environment's age field as the
epoch."  Spell epochs are derived by a fail-closed FSM over the
``MembershipChange`` receipts: initial/fresh activation opens the first spell;
temporary leave closes the current spell; rejoin opens a NEW spell for the same
persistent member key; terminal leave closes the final spell.  Unknown
transitions raise instead of guessing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping

import numpy as np

from envs.continuous_roster import runtime_capacity as roster_env

RAW_OUTPUT_BINDING = "eociv_lite.sibling_env.v1"

ARMS = ("LS", "LR", "CS", "CR")

#: Segment boundaries: lifecycle event k (t = EVENT_TIMES[k]) holds its
#: open/neutral decision for [EVENT_TIMES[k], EVENT_TIMES[k] + SEGMENT_LENGTH).
SEGMENT_LENGTH = roster_env.HORIZON // 4
EVENT_TIMES = roster_env.EVENT_TIMES

#: Hidden shock states and their registered target coefficients.  NONE is the
#: predeclared neutral-cell state; A and B are the critical-cell states.
SHOCK_NONE = "NONE"
SHOCK_A = "A"
SHOCK_B = "B"
SHOCK_COEFF: Mapping[str, Fraction] = {
    SHOCK_NONE: Fraction(1),
    SHOCK_A: Fraction(1, 2),
    SHOCK_B: Fraction(3, 2),
}
#: Prior over the critical-cell states.  Registered, uniform, identity-free.
CRITICAL_PRIOR = {SHOCK_A: Fraction(1, 2), SHOCK_B: Fraction(1, 2)}

#: Predeclared cell classes per lifecycle event index (0 -> t=12, 1 -> t=24,
#: 2 -> t=36).  EOCIV needs both critical-positive and neutral-negative
#: support; making every payload useful would test universal communication.
CELL_CLASS = ("CRITICAL", "NEUTRAL", "CRITICAL")

#: The canonical no-information token (ingredient 4) and the pattern token
#: (gate item 9's pattern-only control).  Fixed bytes; carry nothing.
NEUTRAL_TOKEN = b"EOCIV-NATIVE-NEUTRAL-V1"
PATTERN_TOKEN = b"EOCIV-PATTERN-ONLY-V1"

#: Declared ingestion cost, identical for real and neutral branches.
INGESTION_COST = 1

#: Fixed payload tensor slot width.  Real, neutral and pattern bodies are all
#: padded to this length so the receiver-side tensor shape cannot signal the
#: branch.
PAYLOAD_SLOT_BYTES = 32

#: Sibling-owned seed namespace.  The base ledger uses streams 0, 1, 3, 4,
#: 100+key and 200+key; UCOPE's sibling reserved 0x5C09E03/900001-900002.  The
#: EOCIV sibling reserves its own domain word and streams far outside both.
_SIBLING_SEED_DOMAIN = 0x_E0C_1_F
#: Per-purpose stream bases are strided far wider than the number of lifecycle
#: events, so the ``base + event_index`` ranges can never overlap across
#: purposes.  (An earlier revision used consecutive bases 910_001..910_004,
#: which aliased e.g. receiver(event 0) with carrier(event 1) and shock(event
#: 2) at the shared sibling seed — the hidden context must be independent of
#: identity assignment, so the ranges are now disjoint by construction.)
_SHOCK_STREAM = 910_000
_CARRIER_STREAM = 920_000
_RECEIVER_STREAM = 930_000
_CONTROL_TAPE_STREAM = 940_000


class LifecycleError(RuntimeError):
    """The fail-closed lifecycle FSM saw an inadmissible transition."""


def _sibling_rng(seed: int, episode_id: int, stream: int) -> np.random.Generator:
    return np.random.default_rng(
        (_SIBLING_SEED_DOMAIN, int(seed), int(episode_id), int(stream))
    )


# ---------------------------------------------------------------------------
# Lifecycle FSM: authoritative spell epochs from MembershipChange receipts.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpellReceipt:
    """One member's authenticated lifecycle state at an event boundary."""

    member_key: int
    active: bool
    spell_epoch: int
    opened_at: int
    just_departed: bool


class LifecycleFsm:
    """Fail-closed spell tracker driven only by MembershipChange receipts."""

    _INACTIVE = "INACTIVE"
    _ACTIVE = "ACTIVE"
    _CLOSED = "CLOSED"

    def __init__(self, capacity: int):
        self._state = [self._INACTIVE] * capacity
        self._epoch = [0] * capacity
        self._opened_at = [-1] * capacity
        self._departed_at: dict[int, int] = {}

    def apply(self, change: roster_env.MembershipChange, time: int) -> None:
        for key in change.joined:
            if self._state[key] == self._CLOSED:
                raise LifecycleError(f"fresh join over a closed spell: member {key}")
            if self._state[key] == self._ACTIVE:
                raise LifecycleError(f"join of an active member: member {key}")
            self._state[key] = self._ACTIVE
            self._epoch[key] += 1
            self._opened_at[key] = time
        for key in change.rejoined:
            if self._state[key] != self._CLOSED:
                raise LifecycleError(f"rejoin without a closed spell: member {key}")
            self._state[key] = self._ACTIVE
            self._epoch[key] += 1
            self._opened_at[key] = time
        for key in change.temporarily_left:
            if self._state[key] != self._ACTIVE:
                raise LifecycleError(f"temporary leave of inactive member {key}")
            self._state[key] = self._CLOSED
            self._departed_at[key] = time
        for key in change.terminally_left:
            if self._state[key] != self._ACTIVE:
                raise LifecycleError(f"terminal leave of inactive member {key}")
            self._state[key] = self._CLOSED
            self._departed_at[key] = time

    def receipt(self, member_key: int, time: int) -> SpellReceipt:
        return SpellReceipt(
            member_key=int(member_key),
            active=self._state[member_key] == self._ACTIVE,
            spell_epoch=self._epoch[member_key],
            opened_at=self._opened_at[member_key],
            just_departed=self._departed_at.get(member_key) == time,
        )


# ---------------------------------------------------------------------------
# Opportunity identity, W_minus, payloads, actuation.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EdgeIdentity:
    """Pro's complete edge identity tuple."""

    episode_id: int
    receiver_member_key: int
    receiver_active_spell_epoch: int
    source_member_key: int
    source_active_spell_epoch: int
    lifecycle_event_index: int


@dataclass(frozen=True)
class Opportunity:
    """One eligible focal opportunity at a lifecycle boundary."""

    identity: EdgeIdentity
    physical_tick: int
    cell_class: str
    cluster_id: str
    receiver_receipt: SpellReceipt
    source_receipt: SpellReceipt
    eligible: bool
    ineligibility_reason: str | None


@dataclass(frozen=True)
class Actuation:
    """The realized focal ingestion for one opportunity."""

    arm: str
    route: str            # REAL | NEUTRAL | SUPPRESSED
    decision_source: str  # D_L | D_C | ALWAYS_REAL | G=0
    body: bytes
    slot: bytes           # fixed-width receiver tensor content
    ingestion_cost: int


def _pad_slot(body: bytes) -> bytes:
    if len(body) > PAYLOAD_SLOT_BYTES:
        raise ValueError("payload body exceeds the registered slot width")
    return body + b"\x00" * (PAYLOAD_SLOT_BYTES - len(body))


def real_payload_body(shock_state: str) -> bytes:
    """The legitimate pre-action signal the ledger-assigned source carries."""
    if shock_state not in SHOCK_COEFF:
        raise ValueError(f"unregistered shock state: {shock_state!r}")
    return b"EOCIV-SIGNAL:" + shock_state.encode("ascii")


def knockout_payload_body() -> bytes:
    """Gate item 9's payload-knockout control: signal removed at the source."""
    return b"EOCIV-SIGNAL-KNOCKOUT"


def w_minus(view: roster_env.CapacityRosterView, opportunity: Opportunity) -> bytes:
    """The sealed pre-body view.  Payload body and shock state are excluded.

    Everything here is derived from the base view and lifecycle receipts, both
    of which are identical across hidden shock states by construction — the
    capability gate verifies that equality byte-for-byte (gate item 5's
    "identical W_minus" premise).
    """
    return json.dumps(
        {
            "time": view.time,
            "observations_sha": _array_hex(view.observations),
            "active_mask": view.active_mask.astype(int).tolist(),
            "load": view.load,
            "target_mix": view.target_mix,
            "receiver": _receipt_fields(opportunity.receiver_receipt),
            "source": _receipt_fields(opportunity.source_receipt),
            "cluster_id": opportunity.cluster_id,
            "cell_class": opportunity.cell_class,
            "envelope": {
                "slot_bytes": PAYLOAD_SLOT_BYTES,
                "ingestion_cost": INGESTION_COST,
                "routing_order": "ledger-key-ascending",
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _receipt_fields(receipt: SpellReceipt) -> dict[str, object]:
    return {
        "member_key": receipt.member_key,
        "active": receipt.active,
        "spell_epoch": receipt.spell_epoch,
        "opened_at": receipt.opened_at,
    }


def _array_hex(values: np.ndarray) -> str:
    import hashlib

    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def control_tape_open(episode_id: int, event_index: int, *, tape_seed: int) -> bool:
    """D_C: precommitted propensity draw keyed ONLY by pre-outcome cluster ids.

    The function signature is the guarantee: no payload body, reward,
    post-event state or learned decision can reach it, because none of them is
    a parameter.
    """
    rng = _sibling_rng(tape_seed, episode_id, _CONTROL_TAPE_STREAM + event_index)
    return bool(rng.random() < 0.5)


def actuate(
    arm: str,
    opportunity: Opportunity,
    body: bytes,
    *,
    d_learned: bool,
    d_control: bool,
) -> Actuation:
    """Map (arm, eligibility, decisions) to the realized ingestion route."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    if not opportunity.eligible:
        return Actuation(arm, "SUPPRESSED", "G=0", b"", _pad_slot(b""), 0)
    if arm in ("LR", "CR"):
        return Actuation(arm, "REAL", "ALWAYS_REAL", body, _pad_slot(body), INGESTION_COST)
    decision = d_learned if arm == "LS" else d_control
    source = "D_L" if arm == "LS" else "D_C"
    if decision:
        return Actuation(arm, "REAL", source, body, _pad_slot(body), INGESTION_COST)
    return Actuation(
        arm, "NEUTRAL", source, NEUTRAL_TOKEN, _pad_slot(NEUTRAL_TOKEN), INGESTION_COST
    )


# ---------------------------------------------------------------------------
# The sibling environment.
# ---------------------------------------------------------------------------

class EocivSiblingRosterEnv:
    """The registered EOCIV sibling.  Wraps, never replaces, the base env."""

    def __init__(
        self,
        ledger: roster_env.CapacityRosterLedger,
        *,
        sibling_seed: int,
        intervention_enabled: bool = True,
        shock_states: tuple[str, str, str] | None = None,
    ):
        self._base = roster_env.RuntimeCapacityRosterEnv(ledger)
        self.ledger = ledger
        self.sibling_seed = int(sibling_seed)
        self.intervention_enabled = bool(intervention_enabled)
        self._fsm = LifecycleFsm(ledger.member_capacity)
        # The base env's constructor records the initial join, but its
        # _prepare_membership overwrites that change with an empty one on the
        # first observe(), so the initial activation never surfaces as a view
        # receipt.  The ledger's initial inventory is the authoritative record
        # of the first spell openings; the FSM consumes it directly.
        self._fsm.apply(
            roster_env.MembershipChange(joined=ledger.initial_keys), 0
        )
        self._fsm_time: int | None = None
        if shock_states is None:
            self._shock_states = self._draw_shock_states()
        else:
            # Gate-only forcing knob: the capability gate must evaluate both
            # hidden branches of a critical cell.  A forced state must respect
            # the predeclared cell classes — NEUTRAL cells are NONE by
            # registration and cannot be forced critical.
            if len(shock_states) != len(CELL_CLASS):
                raise ValueError("one shock state per lifecycle event required")
            for state, cell_class in zip(shock_states, CELL_CLASS):
                if state not in SHOCK_COEFF:
                    raise ValueError(f"unregistered shock state: {state!r}")
                if cell_class == "NEUTRAL" and state != SHOCK_NONE:
                    raise ValueError("a NEUTRAL cell is NONE by registration")
                if cell_class == "CRITICAL" and state == SHOCK_NONE:
                    raise ValueError("a CRITICAL cell draws from {A, B}")
            self._shock_states = tuple(shock_states)
        self.reward_trace: list[float] = []

    # -- registered hidden context ------------------------------------------

    def _draw_shock_states(self) -> tuple[str, str, str]:
        states: list[str] = []
        for event_index, cell_class in enumerate(CELL_CLASS):
            if cell_class == "NEUTRAL":
                states.append(SHOCK_NONE)
                continue
            rng = _sibling_rng(
                self.sibling_seed, self.ledger.episode_id, _SHOCK_STREAM + event_index
            )
            states.append(SHOCK_A if rng.random() < float(CRITICAL_PRIOR[SHOCK_A]) else SHOCK_B)
        return tuple(states)

    def shock_state_at(self, time: int) -> str:
        """The segment-persistent hidden state governing the service target."""
        if not self.intervention_enabled or time < EVENT_TIMES[0]:
            return SHOCK_NONE
        for event_index in reversed(range(len(EVENT_TIMES))):
            if time >= EVENT_TIMES[event_index]:
                return self._shock_states[event_index]
        return SHOCK_NONE

    # -- lifecycle bookkeeping ----------------------------------------------

    @property
    def time(self) -> int:
        return self._base.time

    def _sync_fsm(self, view: roster_env.CapacityRosterView) -> None:
        if self._fsm_time == view.time:
            return
        self._fsm.apply(view.membership_change, view.time)
        self._fsm_time = view.time

    # -- population ----------------------------------------------------------

    def opportunity(self, event_index: int) -> Opportunity:
        """The focal opportunity for lifecycle event ``event_index``.

        Must be called when ``self.time == EVENT_TIMES[event_index]``, i.e. at
        the event boundary, before the first post-event step.  The focal edge
        is selected pre-outcome by ledger-seeded draws over the post-change
        active roster; all other eligible edges remain hard-open by
        declaration.
        """
        tick = EVENT_TIMES[event_index]
        if self.time != tick:
            raise RuntimeError(
                f"opportunity {event_index} requested at t={self.time}, not t={tick}"
            )
        view = self.observe_base()
        self._sync_fsm(view)
        active_keys = [int(k) for k in np.flatnonzero(view.active_mask)]
        if len(active_keys) < 2:
            raise RuntimeError("EOCIV opportunity requires two active members")

        carrier_rng = _sibling_rng(
            self.sibling_seed, self.ledger.episode_id, _CARRIER_STREAM + event_index
        )
        source_key = int(active_keys[carrier_rng.integers(len(active_keys))])
        receiver_rng = _sibling_rng(
            self.sibling_seed, self.ledger.episode_id, _RECEIVER_STREAM + event_index
        )
        receiver_candidates = [key for key in active_keys if key != source_key]
        receiver_key = int(receiver_candidates[receiver_rng.integers(len(receiver_candidates))])

        receiver_receipt = self._fsm.receipt(receiver_key, tick)
        source_receipt = self._fsm.receipt(source_key, tick)

        eligible = True
        reason: str | None = None
        if not receiver_receipt.active or not source_receipt.active:
            eligible, reason = False, "endpoint_inactive"
        elif receiver_receipt.just_departed or source_receipt.just_departed:
            eligible, reason = False, "just_departed_owner_suppressed"
        elif source_receipt.spell_epoch <= 0 or receiver_receipt.spell_epoch <= 0:
            eligible, reason = False, "unauthenticated_spell_epoch"

        identity = EdgeIdentity(
            episode_id=self.ledger.episode_id,
            receiver_member_key=receiver_key,
            receiver_active_spell_epoch=receiver_receipt.spell_epoch,
            source_member_key=source_key,
            source_active_spell_epoch=source_receipt.spell_epoch,
            lifecycle_event_index=event_index,
        )
        return Opportunity(
            identity=identity,
            physical_tick=tick,
            cell_class=CELL_CLASS[event_index],
            cluster_id=f"ep{self.ledger.episode_id}-ev{event_index}",
            receiver_receipt=receiver_receipt,
            source_receipt=source_receipt,
            eligible=eligible,
            ineligibility_reason=reason,
        )

    def focal_payload(self, event_index: int) -> bytes:
        """The real focal body: the source's legitimate pre-action signal."""
        if not self.intervention_enabled:
            raise RuntimeError("the disabled projection has no payload channel")
        return real_payload_body(self._shock_states[event_index])

    # -- views and dynamics ---------------------------------------------------

    def observe_base(self) -> roster_env.CapacityRosterView:
        """The base view.  Under intervention it is identical by construction:
        the shock is never written into observations, so there is nothing to
        withhold — the capability gate pins that equality."""
        return self._base.observe()

    def observe(self) -> roster_env.CapacityRosterView:
        return self.observe_base()

    def step(self, actions: np.ndarray) -> tuple[float, bool, dict[str, float]]:
        """Base step semantics with the shocked service target.

        The action legality rules are the base environment's own.  The only
        dynamical change is the target multiplier c_z during post-event
        segments of the enabled sibling.
        """
        view = self.observe_base()
        self._sync_fsm(view)
        if not self.intervention_enabled:
            reward, terminated, info = self._base.step(actions)
            self.reward_trace.append(reward)
            return reward, terminated, info

        values = np.asarray(actions, dtype=np.float32)
        expected = (self.ledger.member_capacity, roster_env.ACTION_DIM)
        if values.shape != expected or not np.isfinite(values).all():
            raise ValueError("EOCIV sibling action shape/finite mismatch")
        if np.any(np.abs(values) > 1.0) or np.count_nonzero(values[~view.active_mask]):
            raise ValueError("EOCIV sibling action support mismatch")

        keys = np.flatnonzero(view.active_mask)
        effort = (values[keys, 0] + 1.0) / 2.0
        mix = (values[keys, 1] + 1.0) / 2.0
        capabilities = self.ledger.capabilities[keys]
        served = np.asarray((
            np.sum(effort * mix * capabilities[:, 0], dtype=np.float64),
            np.sum(effort * (1.0 - mix) * capabilities[:, 1], dtype=np.float64),
        ))
        aggregate = capabilities.sum(axis=0, dtype=np.float64)
        coefficient = float(SHOCK_COEFF[self.shock_state_at(view.time)])
        target = np.asarray((
            coefficient * view.load * view.target_mix * aggregate[0],
            coefficient * view.load * (1.0 - view.target_mix) * aggregate[1],
        ))
        relative_error = np.abs(served - target) / np.maximum(target, 1e-8)
        reward = float(np.clip(1.0 - relative_error.mean(), 0.0, 1.0))

        # Advance the base roster identically so lifecycle, ages and
        # membership evolve exactly as in the base environment.
        self._base.previous_actions[keys] = values[keys]
        self._base.age[keys] += 1
        self._base.reward_trace.append(reward)
        self._base.roster_sizes.append(len(keys))
        self._base.time += 1
        self._base._prepared_time = None
        self._base._change = roster_env.MembershipChange()
        self._base._terminated = self._base.time == roster_env.HORIZON

        self.reward_trace.append(reward)
        return reward, self._base._terminated, {"service_utility": reward}

    def episode_total(self) -> float:
        return float(sum(self.reward_trace))
