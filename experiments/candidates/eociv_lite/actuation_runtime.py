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

v2 (Pro's loop-7 C1 correction): the receipt verifier binds to the ACTUAL
slot tensor fed into ``CommonPolicy.forward`` (focal row equals
``slot_features(actuation.slot)``, all non-focal rows zero) and to the full
current opportunity identity, route, decision source and ingestion cost;
receipts carry the issuing runner's block identity so cross-runner receipts
at the same tick are rejected; and every boundary action carries an
``ActionReceipt`` (policy-input/kernel/action/recurrent-write digests) that
the registered ``bound_step`` wrapper verifies before ``step()``.
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

    Single-use enforcement is TRAJECTORY-SCOPED (the registered design is one
    runner per arm-episode), and ``runner_binding`` carries the issuing
    runner's full environment/block identity (arm, profile registration id,
    episode id), so a receipt from another runner at the SAME physical tick
    is rejected by identity, not merely documented as unsupported (Pro's
    loop-7 C1 correction).  Cross-tick replay is stopped by the staleness
    check.
    """

    opportunity_identity: sib.EdgeIdentity
    physical_tick: int
    route: str
    decision_source: str
    slot_digest: str
    ingestion_cost: int
    runner_binding: str


@dataclass(frozen=True)
class ActionReceipt:
    """Immutable record binding one boundary action to its actuation receipt.

    Created only after ``_verify_and_consume`` accepted the actuation receipt
    against the ACTUAL policy-input tensors.  ``bound_step`` refuses any
    boundary action that does not carry a matching one, so an action altered
    after the forward pass fails closed.
    """

    actuation_receipt_digest: str
    policy_input_digest: str
    kernel_digest: str
    sampled_action_digest: str
    recurrent_write_digest: str
    physical_tick: int


def receipt_digest(receipt: ActuationReceipt) -> str:
    return hashlib.sha256(repr(receipt).encode("utf-8")).hexdigest()


def make_receipt(
    opportunity: sib.Opportunity, actuation: sib.Actuation, *, runner_binding: str
) -> ActuationReceipt:
    return ActuationReceipt(
        opportunity_identity=opportunity.identity,
        physical_tick=opportunity.physical_tick,
        route=actuation.route,
        decision_source=actuation.decision_source,
        slot_digest=hashlib.sha256(actuation.slot).hexdigest(),
        ingestion_cost=actuation.ingestion_cost,
        runner_binding=str(runner_binding),
    )


def bound_step(
    env: sib.EocivSiblingRosterEnv,
    actions: np.ndarray,
    action_receipt: ActionReceipt | None,
) -> tuple[float, bool, dict[str, float]]:
    """The registered bound-step wrapper for boundary actions.

    Only an action carrying an ``ActionReceipt`` whose sampled-action digest
    matches the submitted tensor at the current tick may enter ``step()``.
    The wrapper's contract is exactly (tick, sampled-action digest); the
    receipt's input/kernel/recurrent digests are provenance records — they
    are computed from the verified forward pass inside ``run_episode`` and
    bind the action to it there, not re-derived here (the wrapper has no
    access to the policy internals to recompute them).
    """
    if action_receipt is None:
        raise ReceiptError("missing action receipt at a bound step")
    if action_receipt.physical_tick != env.time:
        raise ReceiptError(
            f"action receipt tick {action_receipt.physical_tick} "
            f"vs env time {env.time}"
        )
    if _digest(actions) != action_receipt.sampled_action_digest:
        raise ReceiptError("action altered after the verified forward pass")
    return env.step(actions)


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
        action_noise_seed: int | None = None,
        runner_binding: str | None = None,
        d_control_fn=None,
    ):
        if arm not in sib.ARMS:
            raise ValueError(f"unknown arm: {arm}")
        self.env = env
        self.arm = arm
        self.tape_seed = int(tape_seed)
        self.d_learned_fn = d_learned_fn
        # D_C source.  Default: the gate-support Bernoulli probe
        # (sib.control_tape_open) under tape_seed — the CLOSED gate
        # population's registered control.  The Stage-0 outcome harness
        # passes its exact-rate permutation-tape decisions here instead; the
        # registered outcome design forbids the gate probe, and supplying
        # d_control_fn means the probe is never called on that path.
        self.d_control_fn = d_control_fn
        self.body_override = body_override
        # Full environment/block identity of this runner.  The default —
        # (arm, profile, episode) — is the block identity of the CLOSED gate
        # population (one runner per arm-episode).  The Stage-0 outcome
        # harness passes the COMPLETE registered block identity (pool, actor
        # training seed, profile, episode, arm, event scope, member/spell
        # epochs) through ``runner_binding`` instead, per the acceptance
        # ruling's 6.2.
        self.runner_binding = (
            runner_binding
            if runner_binding is not None
            else f"{arm}|{env.ledger.profile.name}|ep{env.ledger.episode_id}"
        )
        capacity = env.ledger.member_capacity
        # The policy must expose the CommonPolicy interface:
        # initial_state() and forward(obs, mask, slot_block, hidden, noise).
        # The default keeps the accepted gate probe; the Stage-0 harness
        # passes the trainable actor through the SAME verified path.
        self.policy = policy if policy is not None else CommonPolicy(capacity)
        self.hidden = self.policy.initial_state()
        self.noise = roster_env.make_action_noise(
            [env.ledger.episode_id],
            action_seed=(
                ACTION_NOISE_SEED if action_noise_seed is None
                else int(action_noise_seed)
            ),
            member_capacity=capacity,
        )[:, 0, :, :]
        self._consumed: set[tuple] = set()
        self.boundary_records: list[BoundaryRecord] = []
        self.action_receipts: list[ActionReceipt] = []
        self.step_traces: list[StepTrace] = []

    # -- receipt discipline --------------------------------------------------

    def _verify_and_consume(
        self,
        receipt: ActuationReceipt | None,
        opportunity: sib.Opportunity,
        actuation: sib.Actuation,
        slot_block: np.ndarray,
        focal_receiver: int,
    ) -> None:
        """Fail-closed binding of the receipt to the ACTUAL policy input.

        Pro's loop-7 C1 correction: the verifier must check the slot tensor
        that entered ``CommonPolicy.forward`` — not separately saved bytes —
        plus the complete current opportunity identity, route, decision
        source, ingestion cost, and the issuing runner's block identity.
        """
        if receipt is None:
            raise ReceiptError("missing actuation receipt at a boundary step")
        if receipt.runner_binding != self.runner_binding:
            raise ReceiptError(
                f"cross-runner receipt: issued by {receipt.runner_binding!r}, "
                f"consumed by {self.runner_binding!r}"
            )
        if receipt.physical_tick != self.env.time:
            raise ReceiptError(
                f"stale or post-action receipt: tick {receipt.physical_tick} "
                f"vs env time {self.env.time}"
            )
        if receipt.opportunity_identity != opportunity.identity:
            raise ReceiptError(
                "receipt identity does not match the current opportunity "
                "(profile/episode/event/spell-epoch/member binding)"
            )
        if receipt.opportunity_identity.receiver_member_key != focal_receiver:
            raise ReceiptError("wrong-owner receipt: focal receiver mismatch")
        if receipt.route != actuation.route:
            raise ReceiptError("receipt route does not match the actuation")
        if receipt.decision_source != actuation.decision_source:
            raise ReceiptError("receipt decision source does not match the actuation")
        if receipt.ingestion_cost != actuation.ingestion_cost:
            raise ReceiptError("receipt ingestion cost does not match the actuation")
        if hashlib.sha256(actuation.slot).hexdigest() != receipt.slot_digest:
            raise ReceiptError("slot digest does not match the bound receipt")
        if not np.array_equal(slot_block[focal_receiver], slot_features(actuation.slot)):
            raise ReceiptError(
                "the focal policy slot tensor does not match the receipted slot"
            )
        nonfocal = np.delete(slot_block, focal_receiver, axis=0)
        if np.count_nonzero(nonfocal):
            raise ReceiptError("nonzero non-focal slot rows in the policy input")
        key = (receipt.opportunity_identity, receipt.physical_tick)
        if key in self._consumed:
            raise ReceiptError("duplicate receipt consumption for one opportunity")
        self._consumed.add(key)

    # -- the drive -----------------------------------------------------------

    def _boundary(
        self, event_index: int
    ) -> tuple[np.ndarray, ActuationReceipt, int, sib.Opportunity, sib.Actuation]:
        env = self.env
        opportunity = env.opportunity(event_index)
        view = env.observe()
        w_bytes = sib.w_minus(view, opportunity)
        body = self.body_override if self.body_override is not None else env.focal_payload(event_index)
        d_learned = bool(self.d_learned_fn(w_bytes))
        d_control = (
            bool(self.d_control_fn(event_index))
            if self.d_control_fn is not None
            else sib.control_tape_open(
                env.ledger.profile.name, env.ledger.episode_id, event_index,
                tape_seed=self.tape_seed,
            )
        )
        actuation = sib.actuate(
            self.arm, opportunity, body, d_learned=d_learned, d_control=d_control
        )
        receipt = make_receipt(
            opportunity, actuation, runner_binding=self.runner_binding
        )
        capacity = env.ledger.member_capacity
        slot_block = np.zeros((capacity, SLOT_DIM), dtype=np.float32)
        focal = opportunity.identity.receiver_member_key
        slot_block[focal, :] = slot_features(actuation.slot)
        self.boundary_records.append(
            BoundaryRecord(receipt, w_bytes, actuation.route, actuation.slot)
        )
        return slot_block, receipt, focal, opportunity, actuation

    def run_episode(self) -> float:
        env = self.env
        capacity = env.ledger.member_capacity
        while env.time < roster_env.HORIZON:
            time = env.time
            event_index = (
                sib.EVENT_TIMES.index(time) if time in sib.EVENT_TIMES else None
            )
            if event_index is not None:
                slot_block, receipt, focal, opportunity, actuation = (
                    self._boundary(event_index)
                )
            else:
                slot_block, receipt, focal, opportunity, actuation = (
                    np.zeros((capacity, SLOT_DIM), dtype=np.float32),
                    None, None, None, None,
                )
            view = env.observe()
            actions, kernel, new_hidden = self.policy.forward(
                view.observations, view.active_mask, slot_block,
                self.hidden, self.noise[time],
            )
            trace = StepTrace(
                time=time,
                input_digest=_digest(view.observations, view.active_mask, slot_block, self.hidden),
                kernel_digest=_digest(kernel),
                action_digest=_digest(actions),
                hidden_digest=_digest(new_hidden),
            )
            self.step_traces.append(trace)
            self.hidden = new_hidden
            if event_index is not None:
                # The binding chain (Pro's C1): the actuation receipt is
                # verified against the ACTUAL slot tensor that entered the
                # forward pass, then the resulting action carries an
                # ActionReceipt, and only the bound-step wrapper may submit
                # it to the environment.
                self._verify_and_consume(
                    receipt, opportunity, actuation, slot_block, focal
                )
                action_receipt = ActionReceipt(
                    actuation_receipt_digest=receipt_digest(receipt),
                    policy_input_digest=trace.input_digest,
                    kernel_digest=trace.kernel_digest,
                    sampled_action_digest=trace.action_digest,
                    recurrent_write_digest=trace.hidden_digest,
                    physical_tick=time,
                )
                self.action_receipts.append(action_receipt)
                bound_step(env, actions, action_receipt)
            else:
                env.step(actions)
        return env.episode_total()
