"""Executable actuation edge for the EOCIV sibling (Pro's Material Issue A).

The loop-6 ruling (`EOCIV_SIBLING_CORRECTIONS_REQUIRED`) held that the sibling's
receiver-ingestion channel was "not yet executable end to end": the slot existed
as bytes in an ``Actuation``, but no policy input consumed it and ``step()``
never verified an actuation binding.  This module supplies the required objects:

- ``ActuationReceipt`` — immutable, single-use, created at the event boundary,
  binding the opportunity identity, tick, route, decision source, slot digest
  and ingestion cost.  The RUNNER enforces single use and fails closed on
  missing, stale, duplicate, post-action, or wrong-owner receipts.
- ``CommonPolicy`` — ONE registered payload-aware policy graph shared by every
  arm (fixed registered weights; recurrent per-member state; the receiver slot
  is ingested ONCE at the boundary and carried through the receiver recurrence
  for the segment — republishing per step would define a different channel).
- ``ArmEpisodeRunner`` — drives a whole episode for one arm through the real
  environment: W_minus -> D_L/D_C -> receipt -> slot placed only in the focal
  receiver's actor input -> common policy forward -> binding verified ->
  ``step()``.  It records byte-level traces (policy inputs, action kernels,
  sampled actions under common noise, recurrent writes) so the gate can prove
  LR/CR byte-identity and A/B slot reachability.

The policy is untrained: its weights are drawn once from a registered seed.
The gate's propositions are about the executable path and the environment
mechanism, not about learned behavior.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import sibling_env as sib

RAW_OUTPUT_BINDING = "eociv_lite.actuation_runtime.v2"

#: Registered weights seed for the one common policy graph.
POLICY_WEIGHT_SEED = 730_101
#: Registered member-owned action-noise seed (reuses the base env's
#: member-owned noise construction, so common-noise blocks are well defined).
ACTION_NOISE_SEED = 730_202
#: Recurrent width and noise scale of the registered policy.
HIDDEN_DIM = 8
NOISE_SIGMA = np.float32(0.05)
SLOT_DIM = sib.PAYLOAD_SLOT_BYTES


class ReceiptError(RuntimeError):
    """A fail-closed actuation-receipt violation."""


@dataclass(frozen=True)
class ActuationReceipt:
    """Immutable single-use record binding an actuation to its boundary.

    Single-use enforcement is TRAJECTORY-SCOPED: each ``ArmEpisodeRunner``
    tracks consumption for its own trajectory (the registered design is one
    runner per arm-episode).  Cross-runner replay at a DIFFERENT tick is
    stopped by the staleness check; a harness that shared one receipt across
    two runners at the same physical tick would need its own global registry
    — do not build such a harness against this type.
    """

    opportunity_identity: sib.EdgeIdentity
    physical_tick: int
    route: str
    decision_source: str
    slot_digest: str
    ingestion_cost: int


@dataclass(frozen=True)
class ActionReceipt:
    """Immutable receipt for the exact policy input and resulting writes."""

    opportunity_identity: sib.EdgeIdentity
    physical_tick: int
    route: str
    decision_source: str
    ingestion_cost: int
    policy_input_digest: str
    kernel_digest: str
    sampled_action_digest: str
    recurrent_write_digest: str


def make_receipt(opportunity: sib.Opportunity, actuation: sib.Actuation) -> ActuationReceipt:
    return ActuationReceipt(
        opportunity_identity=opportunity.identity,
        physical_tick=opportunity.physical_tick,
        route=actuation.route,
        decision_source=actuation.decision_source,
        slot_digest=hashlib.sha256(actuation.slot).hexdigest(),
        ingestion_cost=actuation.ingestion_cost,
    )


def slot_features(slot: bytes) -> np.ndarray:
    """The fixed-width receiver ingestion features: slot bytes scaled to [0,1]."""
    if len(slot) != sib.PAYLOAD_SLOT_BYTES:
        raise ValueError("slot width violates the registered envelope")
    return (np.frombuffer(slot, dtype=np.uint8).astype(np.float32)) / np.float32(255.0)


class CommonPolicy:
    """The single registered payload-aware policy graph (untrained).

    forward() is a pure float32 computation:

        h'      = tanh(obs @ Wx + h @ Wh + slot @ Ws + b)      (active rows)
        kernel  = h' @ Wa
        action  = tanh(kernel + NOISE_SIGMA * noise)

    Inactive rows keep their recurrent state and emit the zero action, which
    is exactly the base environment's inactive-action convention.
    """

    def __init__(self, capacity: int):
        rng = np.random.default_rng(POLICY_WEIGHT_SEED)
        scale = np.float32(0.25)
        self.capacity = int(capacity)
        self.w_obs = (rng.standard_normal((roster_env.OBSERVATION_DIM, HIDDEN_DIM)) * scale).astype(np.float32)
        self.w_hidden = (rng.standard_normal((HIDDEN_DIM, HIDDEN_DIM)) * scale).astype(np.float32)
        self.w_slot = (rng.standard_normal((SLOT_DIM, HIDDEN_DIM)) * scale).astype(np.float32)
        self.bias = (rng.standard_normal(HIDDEN_DIM) * scale).astype(np.float32)
        self.w_action = (rng.standard_normal((HIDDEN_DIM, roster_env.ACTION_DIM)) * scale).astype(np.float32)

    def initial_state(self) -> np.ndarray:
        return np.zeros((self.capacity, HIDDEN_DIM), dtype=np.float32)

    def forward(
        self,
        observations: np.ndarray,
        active_mask: np.ndarray,
        slot_block: np.ndarray,
        hidden: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns (actions, kernel, new_hidden), all float32."""
        pre = (
            observations.astype(np.float32) @ self.w_obs
            + hidden @ self.w_hidden
            + slot_block.astype(np.float32) @ self.w_slot
            + self.bias
        )
        candidate = np.tanh(pre).astype(np.float32)
        new_hidden = np.where(active_mask[:, None], candidate, hidden).astype(np.float32)
        kernel = (new_hidden @ self.w_action).astype(np.float32)
        actions = np.tanh(kernel + NOISE_SIGMA * noise.astype(np.float32)).astype(np.float32)
        actions = np.where(active_mask[:, None], actions, np.float32(0.0)).astype(np.float32)
        return actions, kernel, new_hidden


@dataclass(frozen=True)
class BoundaryRecord:
    """What the runner did at one lifecycle boundary."""

    receipt: ActuationReceipt
    action_receipt: ActionReceipt
    w_minus: bytes
    actuation_route: str
    slot: bytes


@dataclass(frozen=True)
class StepTrace:
    """Byte-level digests of one policy step (for identity proofs)."""

    time: int
    input_digest: str
    kernel_digest: str
    action_digest: str
    hidden_digest: str


def _digest(*arrays: np.ndarray) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


class ArmEpisodeRunner:
    """Drives one arm's whole episode through the executable actuation path."""

    def __init__(
        self,
        env: sib.EocivSiblingRosterEnv,
        arm: str,
        *,
        tape_seed: int,
        d_learned_fn,
        body_override: bytes | None = None,
        policy=None,
        d_control_fn=None,
    ):
        if arm not in sib.ARMS:
            raise ValueError(f"unknown arm: {arm}")
        self.env = env
        self.arm = arm
        self.tape_seed = int(tape_seed)
        self.d_learned_fn = d_learned_fn
        self.d_control_fn = d_control_fn
        self.body_override = body_override
        capacity = env.ledger.member_capacity
        # The Stage-0 capability path retains CommonPolicy as its exact
        # default.  Candidate-local experiments may inject an object with the
        # same initial_state/forward surface; no runner or receipt semantics
        # change when the seam is unused.
        self.policy = CommonPolicy(capacity) if policy is None else policy
        self.hidden = self.policy.initial_state()
        self.action_noise_seed_identity = sib.profile_stream_identity(
            sib.ACTION_NOISE_STREAM,
            ACTION_NOISE_SEED,
            env.ledger.profile.name,
        )
        self.noise = roster_env.make_action_noise(
            [env.ledger.episode_id],
            action_seed=self.action_noise_seed_identity,
            member_capacity=capacity,
        )[:, 0, :, :]
        self._consumed: set[tuple] = set()
        self.boundary_records: list[BoundaryRecord] = []
        self.step_traces: list[StepTrace] = []

    # -- receipt discipline --------------------------------------------------

    def _verify_pre_receipt(
        self,
        receipt: ActuationReceipt | None,
        opportunity: sib.Opportunity,
        actuation: sib.Actuation,
        slot_block: np.ndarray,
    ) -> None:
        if receipt is None:
            raise ReceiptError("missing actuation receipt at a boundary step")
        if receipt.physical_tick != self.env.time:
            raise ReceiptError(
                f"stale or post-action receipt: tick {receipt.physical_tick} "
                f"vs env time {self.env.time}"
            )
        if receipt.opportunity_identity != opportunity.identity:
            raise ReceiptError("wrong or cross-runner opportunity identity")
        if receipt.physical_tick != opportunity.physical_tick:
            raise ReceiptError("receipt tick does not match opportunity")
        if (
            receipt.route != actuation.route
            or receipt.decision_source != actuation.decision_source
            or receipt.ingestion_cost != actuation.ingestion_cost
        ):
            raise ReceiptError("receipt route/source/cost does not match actuation")
        if hashlib.sha256(actuation.slot).hexdigest() != receipt.slot_digest:
            raise ReceiptError("slot digest does not match the bound receipt")
        expected_shape = (self.env.ledger.member_capacity, SLOT_DIM)
        if slot_block.shape != expected_shape or slot_block.dtype != np.float32:
            raise ReceiptError("policy slot block has wrong shape or dtype")
        focal = opportunity.identity.receiver_member_key
        if not np.array_equal(slot_block[focal], slot_features(actuation.slot)):
            raise ReceiptError("actual focal row differs from receipt-bound slot")
        nonfocal = slot_block.copy()
        nonfocal[focal, :] = np.float32(0.0)
        if np.any(nonfocal != np.float32(0.0)):
            raise ReceiptError("actual policy input contains nonzero non-focal row")
        key = (receipt.opportunity_identity, receipt.physical_tick)
        if key in self._consumed:
            raise ReceiptError("duplicate receipt consumption for one opportunity")

    def _consume(self, receipt: ActuationReceipt) -> None:
        key = (receipt.opportunity_identity, receipt.physical_tick)
        if key in self._consumed:
            raise ReceiptError("duplicate receipt consumption for one opportunity")
        self._consumed.add(key)

    def verify_action_receipt(
        self,
        receipt: ActionReceipt,
        *,
        opportunity: sib.Opportunity,
        actuation: sib.Actuation,
        observations: np.ndarray,
        active_mask: np.ndarray,
        slot_block: np.ndarray,
        hidden: np.ndarray,
        kernel: np.ndarray,
        actions: np.ndarray,
        new_hidden: np.ndarray,
    ) -> None:
        expected = ActionReceipt(
            opportunity_identity=opportunity.identity,
            physical_tick=opportunity.physical_tick,
            route=actuation.route,
            decision_source=actuation.decision_source,
            ingestion_cost=actuation.ingestion_cost,
            policy_input_digest=_digest(observations, active_mask, slot_block, hidden),
            kernel_digest=_digest(kernel),
            sampled_action_digest=_digest(actions),
            recurrent_write_digest=_digest(new_hidden),
        )
        if receipt != expected:
            raise ReceiptError("action receipt does not match executed digest material")

    def bound_step(
        self,
        *,
        receipt: ActuationReceipt | None,
        opportunity: sib.Opportunity,
        actuation: sib.Actuation,
        observations: np.ndarray,
        active_mask: np.ndarray,
        slot_block: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, ActionReceipt]:
        """Validate input, execute the common policy, seal writes, then consume."""
        self._verify_pre_receipt(receipt, opportunity, actuation, slot_block)
        actions, kernel, new_hidden = self.policy.forward(
            observations, active_mask, slot_block, self.hidden, noise
        )
        action_receipt = ActionReceipt(
            opportunity_identity=opportunity.identity,
            physical_tick=opportunity.physical_tick,
            route=actuation.route,
            decision_source=actuation.decision_source,
            ingestion_cost=actuation.ingestion_cost,
            policy_input_digest=_digest(observations, active_mask, slot_block, self.hidden),
            kernel_digest=_digest(kernel),
            sampled_action_digest=_digest(actions),
            recurrent_write_digest=_digest(new_hidden),
        )
        self.verify_action_receipt(
            action_receipt,
            opportunity=opportunity,
            actuation=actuation,
            observations=observations,
            active_mask=active_mask,
            slot_block=slot_block,
            hidden=self.hidden,
            kernel=kernel,
            actions=actions,
            new_hidden=new_hidden,
        )
        if receipt is None:  # guarded above; keeps the type boundary explicit.
            raise ReceiptError("missing actuation receipt at consumption")
        self._consume(receipt)
        return actions, kernel, new_hidden, action_receipt

    # -- the drive -----------------------------------------------------------

    def _boundary(
        self, event_index: int
    ) -> tuple[
        np.ndarray, ActuationReceipt, sib.Opportunity, sib.Actuation, bytes
    ]:
        env = self.env
        opportunity = env.opportunity(event_index)
        view = env.observe()
        w_bytes = sib.w_minus(view, opportunity)
        body = self.body_override if self.body_override is not None else env.focal_payload(event_index)
        d_learned = bool(self.d_learned_fn(w_bytes))
        d_control = (
            sib.control_tape_open(
                env.ledger.profile.name,
                env.ledger.episode_id,
                event_index,
                tape_seed=self.tape_seed,
            )
            if self.d_control_fn is None
            else bool(self.d_control_fn(w_bytes))
        )
        actuation = sib.actuate(
            self.arm, opportunity, body, d_learned=d_learned, d_control=d_control
        )
        receipt = make_receipt(opportunity, actuation)
        capacity = env.ledger.member_capacity
        slot_block = np.zeros((capacity, SLOT_DIM), dtype=np.float32)
        focal = opportunity.identity.receiver_member_key
        slot_block[focal, :] = slot_features(actuation.slot)
        return slot_block, receipt, opportunity, actuation, w_bytes

    def run_episode(self) -> float:
        env = self.env
        capacity = env.ledger.member_capacity
        while env.time < roster_env.HORIZON:
            time = env.time
            event_index = (
                sib.EVENT_TIMES.index(time) if time in sib.EVENT_TIMES else None
            )
            if event_index is not None:
                slot_block, receipt, opportunity, actuation, w_bytes = self._boundary(
                    event_index
                )
            else:
                slot_block = np.zeros((capacity, SLOT_DIM), dtype=np.float32)
            view = env.observe()
            if event_index is not None:
                actions, kernel, new_hidden, action_receipt = self.bound_step(
                    receipt=receipt,
                    opportunity=opportunity,
                    actuation=actuation,
                    observations=view.observations,
                    active_mask=view.active_mask,
                    slot_block=slot_block,
                    noise=self.noise[time],
                )
                self.boundary_records.append(
                    BoundaryRecord(
                        receipt,
                        action_receipt,
                        w_bytes,
                        actuation.route,
                        actuation.slot,
                    )
                )
            else:
                actions, kernel, new_hidden = self.policy.forward(
                    view.observations,
                    view.active_mask,
                    slot_block,
                    self.hidden,
                    self.noise[time],
                )
            self.step_traces.append(
                StepTrace(
                    time=time,
                    input_digest=_digest(view.observations, view.active_mask, slot_block, self.hidden),
                    kernel_digest=_digest(kernel),
                    action_digest=_digest(actions),
                    hidden_digest=_digest(new_hidden),
                )
            )
            self.hidden = new_hidden
            env.step(actions)
        return env.episode_total()
