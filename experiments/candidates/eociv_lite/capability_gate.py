"""Exact pre-PPO capability gate for the EOCIV sibling (ruling ingredient 6).

External ruling ``EOCIV_SIBLING_CAPABILITY_REQUIRED``:

    "No training budget should be released until a deterministic gate verifies:
     [ten checks].  Failure of items 5-7 is a capability failure, not a reason
     to begin PPO and hope training manufactures the missing estimand."

This module is that gate.  The ten checks, verbatim from the ruling, and where
each is implemented here:

 1. disabled-sibling projection reproduces base G32          -> check_1
 2. every opportunity has complete owner and spell receipts  -> check_2
 3. real and neutral both legal, sharing the fixed wrapper   -> check_3
 4. first post-event action after actuation, before outcome  -> check_4
 5. two latent states, identical W_minus, different optimal
    receiver actions                                         -> check_5
 6. real payload permits a strictly better oracle decision
    in critical cells                                        -> check_6
 7. neutral cells have zero (here: exactly zero) oracle
    reveal value                                             -> check_7
 8. focal-body mutations cannot reach selection, routing,
    control tape or neutral construction                     -> check_8
 9. pattern-only and payload-knockout controls executable    -> check_9
10. all four arms have positive support in each declared
    analysis stratum                                         -> check_10

ORACLE ARITHMETIC IS EXACT
--------------------------
Checks 5-7 are computed in ``fractions.Fraction`` end to end.  Every ledger
quantity involved (float32 capabilities, loads, mixes) is lifted exactly —
float32 values are dyadic rationals, so ``Fraction(float(x))`` is lossless.
The oracle receiver problem is:

    at lifecycle event k with focal receiver i, every non-focal active member
    plays the blind-constructive action (effort = published load, mix =
    published mix — the base environment's exact optimum family), and the
    receiver picks a per-step effort from the candidate set {0, load, 1} with
    mix matched.  Under hidden shock state z the served/target algebra is

        served_1 = m * (l * (A_1 - c_i1) + e * c_i1)
        target_1 = c_z * l * m * A_1            (channel 2 analogous)
        reward   = clip(1 - mean_ch |served-target| / target, 0, 1)

    all in exact rationals.  The informed oracle knows z (the real payload
    carries it); the blind oracle knows only the registered cell prior.

A float-execution conformance check then drives the *actual* sibling
environment with the oracle actions and pins the float64 reward trace to the
rational values within ``CONFORMANCE_TOL`` — the science lives in the exact
model; the conformance bound is a wiring check, stated as such.

The gate is deterministic: registered seeds, registered population, no
sampling beyond the ledger's own seeded draws, no training.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import sibling_env as sib

RAW_OUTPUT_BINDING = "eociv_lite.capability_gate.v1"

#: Registered gate population: every training profile, eight episodes each.
GATE_PROFILES = roster_env.TRAIN_PROFILES
GATE_EPISODES = tuple(range(8))
MASTER_SEED = 20260807
SIBLING_SEED = 90731
TAPE_SEED = 41211

#: Wiring tolerance for the float-execution conformance check (not part of the
#: scientific claim, which is exact).  The base environment's served/target
#: kernel multiplies float32 quantities (numpy value-based casting keeps
#: float32 through ``(values + 1.0) / 2.0`` and the per-member products), so
#: each step reward carries relative error of order 2**-24 ~= 6e-8.  The bound
#: is set three decades above the exact model's smallest per-cell reveal value
#: and one decade above the float32 arithmetic floor; the gate separately
#: asserts that every reveal value exceeds this bound by a wide margin
#: (``REVEAL_DOMINANCE``), so conformance noise cannot manufacture item 6.
CONFORMANCE_TOL = 1e-6

#: Every critical cell's exact reveal value must exceed this exact floor —
#: 1000x the conformance bound — so wiring noise is immaterial to the claim.
REVEAL_FLOOR = Fraction(1, 1000)

CRITICAL_STATES = (sib.SHOCK_A, sib.SHOCK_B)


def _frac(value: float) -> Fraction:
    return Fraction(float(value))


def registered_learned_decision(w_minus_bytes: bytes) -> bool:
    """D_L for gate-support purposes: a registered W_minus-measurable rule.

    It reads the sealed pre-body view only — the payload body is not an input.
    Training may later replace the rule; the gate needs a member of the
    learned family that is executable and pre-outcome.
    """
    return bool(hashlib.sha256(w_minus_bytes).digest()[0] & 1)


# ---------------------------------------------------------------------------
# Episode driving helpers.
# ---------------------------------------------------------------------------

def _drive_to(env, time: int) -> None:
    """Advance an environment to ``time`` on blind-constructive actions."""
    while env.time < time:
        view = env.observe()
        env.step(roster_env.constructive_actions(view))


def _make_sibling(profile, episode_id: int, **kwargs) -> sib.EocivSiblingRosterEnv:
    ledger = roster_env.make_ledger(
        episode_id, master_seed=MASTER_SEED, profile=profile
    )
    return sib.EocivSiblingRosterEnv(ledger, sibling_seed=SIBLING_SEED, **kwargs)


# ---------------------------------------------------------------------------
# Exact oracle model for one critical/neutral segment.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SegmentOracle:
    """Exact per-cell oracle valuations for one focal opportunity."""

    event_index: int
    receiver_key: int
    candidate_switch_exists: bool
    switch_step: int | None
    informed_value: Fraction
    blind_value: Fraction
    reveal_value: Fraction
    optimal_actions: dict[str, tuple[Fraction, ...]]


def _step_reward_exact(
    *,
    effort: Fraction,
    load: Fraction,
    mix: Fraction,
    coefficient: Fraction,
    receiver_caps: tuple[Fraction, Fraction],
    aggregate: tuple[Fraction, Fraction],
) -> Fraction:
    served_1 = mix * (load * (aggregate[0] - receiver_caps[0]) + effort * receiver_caps[0])
    served_2 = (1 - mix) * (load * (aggregate[1] - receiver_caps[1]) + effort * receiver_caps[1])
    target_1 = coefficient * load * mix * aggregate[0]
    target_2 = coefficient * load * (1 - mix) * aggregate[1]
    error = (abs(served_1 - target_1) / target_1 + abs(served_2 - target_2) / target_2) / 2
    reward = 1 - error
    if reward < 0:
        return Fraction(0)
    if reward > 1:
        return Fraction(1)
    return reward


def _segment_frames(ledger, event_index: int) -> tuple[tuple[Fraction, Fraction], ...]:
    """(load, mix) per step of the event's held segment, lifted exactly."""
    start = sib.EVENT_TIMES[event_index]
    return tuple(
        (_frac(ledger.load[time]), _frac(ledger.target_mix[time]))
        for time in range(start, start + sib.SEGMENT_LENGTH)
    )


def _active_keys_in_segment(ledger, event_index: int) -> tuple[int, ...]:
    """Active member keys during segment ``event_index`` (constant within it)."""
    active = set(ledger.initial_keys)
    if event_index >= 0:
        active -= set(ledger.temporarily_absent)
    if event_index >= 1:
        active |= set(ledger.temporarily_absent) | set(ledger.fresh_join)
    if event_index >= 2:
        active -= set(ledger.terminal_leave)
    return tuple(sorted(active))


def segment_oracle(ledger, event_index: int, receiver_key: int) -> SegmentOracle:
    cell_class = sib.CELL_CLASS[event_index]
    states = CRITICAL_STATES if cell_class == "CRITICAL" else (sib.SHOCK_NONE,)
    prior = (
        {state: sib.CRITICAL_PRIOR[state] for state in states}
        if cell_class == "CRITICAL"
        else {sib.SHOCK_NONE: Fraction(1)}
    )
    keys = _active_keys_in_segment(ledger, event_index)
    if receiver_key not in keys:
        raise ValueError("oracle receiver is not active in the segment")
    receiver_caps = (
        _frac(ledger.capabilities[receiver_key, 0]),
        _frac(ledger.capabilities[receiver_key, 1]),
    )
    aggregate = (
        sum((_frac(ledger.capabilities[key, 0]) for key in keys), Fraction(0)),
        sum((_frac(ledger.capabilities[key, 1]) for key in keys), Fraction(0)),
    )
    frames = _segment_frames(ledger, event_index)

    def candidates(load: Fraction) -> tuple[Fraction, ...]:
        return (Fraction(0), load, Fraction(1))

    optimal: dict[str, list[Fraction]] = {state: [] for state in states}
    informed_value = Fraction(0)
    switch_step: int | None = None
    for step_index, (load, mix) in enumerate(frames):
        per_state_best: dict[str, tuple[Fraction, Fraction]] = {}
        for state in states:
            best: tuple[Fraction, Fraction] | None = None
            for effort in candidates(load):
                value = _step_reward_exact(
                    effort=effort, load=load, mix=mix,
                    coefficient=sib.SHOCK_COEFF[state],
                    receiver_caps=receiver_caps, aggregate=aggregate,
                )
                if best is None or value > best[0] or (value == best[0] and effort < best[1]):
                    best = (value, effort)
            assert best is not None
            per_state_best[state] = best
            optimal[state].append(best[1])
        if len(states) == 2 and switch_step is None:
            if per_state_best[states[0]][1] != per_state_best[states[1]][1]:
                switch_step = step_index
        informed_value += sum(
            prior[state] * per_state_best[state][0] for state in states
        )

    blind_value = Fraction(0)
    for load, mix in frames:
        best_blind: tuple[Fraction, Fraction] | None = None
        for effort in candidates(load):
            expected = sum(
                (
                    prior[state]
                    * _step_reward_exact(
                        effort=effort, load=load, mix=mix,
                        coefficient=sib.SHOCK_COEFF[state],
                        receiver_caps=receiver_caps, aggregate=aggregate,
                    )
                    for state in states
                ),
                Fraction(0),
            )
            if best_blind is None or expected > best_blind[0] or (
                expected == best_blind[0] and effort < best_blind[1]
            ):
                best_blind = (expected, effort)
        assert best_blind is not None
        blind_value += best_blind[0]

    return SegmentOracle(
        event_index=event_index,
        receiver_key=receiver_key,
        candidate_switch_exists=switch_step is not None,
        switch_step=switch_step,
        informed_value=informed_value,
        blind_value=blind_value,
        reveal_value=informed_value - blind_value,
        optimal_actions={state: tuple(values) for state, values in optimal.items()},
    )


# ---------------------------------------------------------------------------
# The ten checks.
# ---------------------------------------------------------------------------

def check_1_disabled_projection() -> dict[str, object]:
    """Disabled sibling == base G32, step by step, over the full population."""
    episodes = 0
    for profile in GATE_PROFILES:
        for episode_id in GATE_EPISODES:
            ledger = roster_env.make_ledger(
                episode_id, master_seed=MASTER_SEED, profile=profile
            )
            base = roster_env.RuntimeCapacityRosterEnv(ledger)
            disabled = sib.EocivSiblingRosterEnv(
                ledger, sibling_seed=SIBLING_SEED, intervention_enabled=False
            )
            for _ in range(roster_env.HORIZON):
                base_view = base.observe()
                sib_view = disabled.observe()
                if not (
                    base_view.time == sib_view.time
                    and np.array_equal(base_view.observations, sib_view.observations)
                    and np.array_equal(base_view.active_mask, sib_view.active_mask)
                    and base_view.load == sib_view.load
                    and base_view.target_mix == sib_view.target_mix
                    and base_view.membership_change == sib_view.membership_change
                ):
                    return {"passed": False, "detail": f"view drift ep={episode_id}"}
                actions = roster_env.constructive_actions(base_view)
                base_reward, base_done, _ = base.step(actions)
                sib_reward, sib_done, _ = disabled.step(actions)
                if base_reward != sib_reward or base_done != sib_done:
                    return {"passed": False, "detail": f"reward drift ep={episode_id}"}
            if base.outcome().reward_trace != tuple(disabled.reward_trace):
                return {"passed": False, "detail": f"trace drift ep={episode_id}"}
            episodes += 1
    return {"passed": True, "episodes_compared": episodes}


def _all_opportunities():
    for profile in GATE_PROFILES:
        for episode_id in GATE_EPISODES:
            env = _make_sibling(profile, episode_id)
            for event_index in range(len(sib.EVENT_TIMES)):
                _drive_to(env, sib.EVENT_TIMES[event_index])
                yield profile, episode_id, event_index, env, env.opportunity(event_index)


def check_2_receipts_complete() -> dict[str, object]:
    total = eligible = 0
    for _, _, _, _, opportunity in _all_opportunities():
        total += 1
        receipts = (opportunity.receiver_receipt, opportunity.source_receipt)
        if not all(
            receipt.active and receipt.spell_epoch >= 1 and receipt.opened_at >= 0
            for receipt in receipts
        ):
            return {
                "passed": False,
                "detail": f"incomplete receipt at {opportunity.identity}",
            }
        if opportunity.eligible:
            eligible += 1
    return {"passed": total == eligible and total > 0, "opportunities": total, "eligible": eligible}


def check_3_shared_wrapper() -> dict[str, object]:
    body = sib.real_payload_body(sib.SHOCK_A)
    env = _make_sibling(GATE_PROFILES[0], 0, shock_states=(sib.SHOCK_A, sib.SHOCK_NONE, sib.SHOCK_B))
    _drive_to(env, sib.EVENT_TIMES[0])
    opportunity = env.opportunity(0)
    w_before = sib.w_minus(env.observe(), opportunity)
    real = sib.actuate("LS", opportunity, body, d_learned=True, d_control=False)
    neutral = sib.actuate("LS", opportunity, body, d_learned=False, d_control=False)
    w_after = sib.w_minus(env.observe(), opportunity)
    shared = (
        real.route == "REAL"
        and neutral.route == "NEUTRAL"
        and len(real.slot) == len(neutral.slot) == sib.PAYLOAD_SLOT_BYTES
        and real.ingestion_cost == neutral.ingestion_cost == sib.INGESTION_COST
        and neutral.body == sib.NEUTRAL_TOKEN
        and not any(
            token in neutral.body
            for token in (b"SIGNAL", b"epoch", b"key", b"age", b"reward")
        )
        # The wrapper the two branches share is the sealed pre-body view:
        # active mask, routing order, edge envelope and timing all live in
        # W_minus, which actuation must leave byte-identical.  The branches
        # may differ only in the slot content.
        and w_before == w_after
        and real.slot != neutral.slot
    )
    return {"passed": bool(shared)}


def check_4_clock_ordering() -> dict[str, object]:
    env = _make_sibling(GATE_PROFILES[0], 0)
    _drive_to(env, sib.EVENT_TIMES[0])
    opportunity = env.opportunity(0)          # actuation point: at the boundary
    view = env.observe()                       # first post-event view
    post_event_action_time = view.time
    env.step(roster_env.constructive_actions(view))
    late_raises = False
    try:
        env.opportunity(0)                     # after the first post-event step
    except RuntimeError:
        late_raises = True
    outcome_unavailable = env.time < roster_env.HORIZON
    return {
        "passed": bool(
            opportunity.physical_tick == post_event_action_time
            and late_raises
            and outcome_unavailable
        )
    }


def _forced_pair(profile, episode_id: int, event_index: int):
    """Two enabled siblings forced to the two critical states of one cell."""
    template = [
        sib.SHOCK_A if cell == "CRITICAL" else sib.SHOCK_NONE for cell in sib.CELL_CLASS
    ]
    states_a = list(template)
    states_b = list(template)
    states_a[event_index] = sib.SHOCK_A
    states_b[event_index] = sib.SHOCK_B
    env_a = _make_sibling(profile, episode_id, shock_states=tuple(states_a))
    env_b = _make_sibling(profile, episode_id, shock_states=tuple(states_b))
    _drive_to(env_a, sib.EVENT_TIMES[event_index])
    _drive_to(env_b, sib.EVENT_TIMES[event_index])
    return env_a, env_b


def check_5_action_switch() -> dict[str, object]:
    """Identical W_minus across the hidden pair; different optimal actions."""
    cells = []
    for profile in GATE_PROFILES:
        for episode_id in GATE_EPISODES:
            for event_index, cell_class in enumerate(sib.CELL_CLASS):
                if cell_class != "CRITICAL":
                    continue
                env_a, env_b = _forced_pair(profile, episode_id, event_index)
                opp_a = env_a.opportunity(event_index)
                opp_b = env_b.opportunity(event_index)
                w_a = sib.w_minus(env_a.observe(), opp_a)
                w_b = sib.w_minus(env_b.observe(), opp_b)
                if w_a != w_b or opp_a.identity != opp_b.identity:
                    return {
                        "passed": False,
                        "detail": f"W_minus differs across hidden states: {opp_a.identity}",
                    }
                oracle = segment_oracle(
                    env_a.ledger, event_index, opp_a.identity.receiver_member_key
                )
                cells.append(
                    {
                        "profile": profile.name,
                        "episode": episode_id,
                        "event": event_index,
                        "switch": oracle.candidate_switch_exists,
                        "switch_step": oracle.switch_step,
                    }
                )
    switches = sum(1 for cell in cells if cell["switch"])
    return {
        "passed": switches == len(cells) and len(cells) > 0,
        "critical_cells": len(cells),
        "cells_with_action_switch": switches,
    }


def check_6_critical_strict_value() -> dict[str, object]:
    """Informed strictly beats blind in every critical cell — exactly."""
    rows = []
    worst_conformance = 0.0
    for profile in GATE_PROFILES:
        for episode_id in GATE_EPISODES:
            for event_index, cell_class in enumerate(sib.CELL_CLASS):
                if cell_class != "CRITICAL":
                    continue
                env_a, env_b = _forced_pair(profile, episode_id, event_index)
                opportunity = env_a.opportunity(event_index)
                opportunity_b = env_b.opportunity(event_index)
                oracle = segment_oracle(
                    env_a.ledger, event_index, opportunity.identity.receiver_member_key
                )
                if oracle.reveal_value <= 0:
                    return {
                        "passed": False,
                        "detail": f"no strict oracle advantage at {opportunity.identity}",
                    }
                if oracle.reveal_value < REVEAL_FLOOR:
                    return {
                        "passed": False,
                        "detail": f"reveal value does not dominate wiring noise at {opportunity.identity}",
                    }
                # Both hidden branches are driven through the real environment:
                # A-optimal efforts against the A-shocked target on env_a, and
                # B-optimal efforts against the B-shocked target on env_b.
                worst_conformance = max(
                    worst_conformance,
                    _conformance_error(env_a, opportunity, oracle, sib.SHOCK_A),
                    _conformance_error(env_b, opportunity_b, oracle, sib.SHOCK_B),
                )
                rows.append(
                    {
                        "profile": profile.name,
                        "episode": episode_id,
                        "event": event_index,
                        "informed": str(oracle.informed_value),
                        "blind": str(oracle.blind_value),
                        "reveal_value": str(oracle.reveal_value),
                    }
                )
    return {
        "passed": len(rows) > 0 and worst_conformance <= CONFORMANCE_TOL,
        "critical_cells": len(rows),
        "max_execution_conformance_error": worst_conformance,
        "rows": rows,
    }


def _conformance_error(env, opportunity, oracle: SegmentOracle, state: str) -> float:
    """Drive the real env through the segment on the oracle actions; compare."""
    receiver = opportunity.identity.receiver_member_key
    worst = 0.0
    for step_index in range(sib.SEGMENT_LENGTH):
        view = env.observe()
        actions = roster_env.constructive_actions(view)
        effort = oracle.optimal_actions[state][step_index]
        actions[receiver, 0] = np.float32(2.0 * float(effort) - 1.0)
        reward, _, _ = env.step(actions)
        load = _frac(view.load)
        mix = _frac(view.target_mix)
        keys = np.flatnonzero(view.active_mask)
        aggregate = (
            sum((_frac(env.ledger.capabilities[int(k), 0]) for k in keys), Fraction(0)),
            sum((_frac(env.ledger.capabilities[int(k), 1]) for k in keys), Fraction(0)),
        )
        receiver_caps = (
            _frac(env.ledger.capabilities[receiver, 0]),
            _frac(env.ledger.capabilities[receiver, 1]),
        )
        exact = _step_reward_exact(
            effort=effort, load=load, mix=mix,
            coefficient=sib.SHOCK_COEFF[state],
            receiver_caps=receiver_caps, aggregate=aggregate,
        )
        worst = max(worst, abs(reward - float(exact)))
    return worst


def check_7_neutral_zero_reveal() -> dict[str, object]:
    rows = []
    for profile in GATE_PROFILES:
        for episode_id in GATE_EPISODES:
            for event_index, cell_class in enumerate(sib.CELL_CLASS):
                if cell_class != "NEUTRAL":
                    continue
                env = _make_sibling(profile, episode_id)
                _drive_to(env, sib.EVENT_TIMES[event_index])
                opportunity = env.opportunity(event_index)
                oracle = segment_oracle(
                    env.ledger, event_index, opportunity.identity.receiver_member_key
                )
                if oracle.reveal_value != 0:
                    return {
                        "passed": False,
                        "detail": f"nonzero neutral reveal at {opportunity.identity}",
                    }
                rows.append(
                    {
                        "profile": profile.name,
                        "episode": episode_id,
                        "event": event_index,
                        "reveal_value": str(oracle.reveal_value),
                    }
                )
    return {"passed": len(rows) > 0, "neutral_cells": len(rows)}


def check_8_mutation_isolation() -> dict[str, object]:
    """The focal body cannot reach selection, routing, tape or neutral."""
    profile, episode_id, event_index = GATE_PROFILES[0], 1, 0
    env_a, env_b = _forced_pair(profile, episode_id, event_index)
    opp_a = env_a.opportunity(event_index)
    opp_b = env_b.opportunity(event_index)
    body_a = env_a.focal_payload(event_index)
    body_b = env_b.focal_payload(event_index)
    tape = sib.control_tape_open(episode_id, event_index, tape_seed=TAPE_SEED)
    tape_again = sib.control_tape_open(episode_id, event_index, tape_seed=TAPE_SEED)
    neutral_a = sib.actuate("CS", opp_a, body_a, d_learned=True, d_control=False)
    neutral_b = sib.actuate("CS", opp_b, body_b, d_learned=True, d_control=False)
    passed = (
        body_a != body_b                       # the mutation is real
        and opp_a.identity == opp_b.identity   # selection unreached
        and sib.w_minus(env_a.observe(), opp_a) == sib.w_minus(env_b.observe(), opp_b)
        and tape == tape_again                 # tape keyed by cluster ids only
        and neutral_a.slot == neutral_b.slot   # neutral construction unreached
        and neutral_a.body == neutral_b.body == sib.NEUTRAL_TOKEN
    )
    return {"passed": bool(passed)}


def check_9_controls_executable() -> dict[str, object]:
    env = _make_sibling(GATE_PROFILES[0], 2)
    _drive_to(env, sib.EVENT_TIMES[0])
    opportunity = env.opportunity(0)
    pattern = sib.actuate(
        "LR", opportunity, sib.PATTERN_TOKEN, d_learned=False, d_control=False
    )
    knockout = sib.actuate(
        "LR", opportunity, sib.knockout_payload_body(), d_learned=False, d_control=False
    )
    passed = (
        pattern.route == "REAL"
        and knockout.route == "REAL"
        and len(pattern.slot) == len(knockout.slot) == sib.PAYLOAD_SLOT_BYTES
        and pattern.body == sib.PATTERN_TOKEN
        and knockout.body == sib.knockout_payload_body()
    )
    return {"passed": bool(passed)}


def registered_arm(episode_id: int, event_index: int) -> str:
    """The precommitted arm assignment, keyed by pre-outcome cluster ids."""
    return sib.ARMS[(int(episode_id) + int(event_index)) % len(sib.ARMS)]


def check_10_arm_support() -> dict[str, object]:
    support: dict[tuple[str, str], int] = {}
    branch: dict[tuple[str, str, str], int] = {}
    for _, episode_id, event_index, env, opportunity in _all_opportunities():
        arm = registered_arm(episode_id, event_index)
        stratum = opportunity.cell_class
        support[(stratum, arm)] = support.get((stratum, arm), 0) + 1
        body = env.focal_payload(event_index)
        w_bytes = sib.w_minus(env.observe(), opportunity)
        actuation = sib.actuate(
            arm,
            opportunity,
            body,
            d_learned=registered_learned_decision(w_bytes),
            d_control=sib.control_tape_open(episode_id, event_index, tape_seed=TAPE_SEED),
        )
        key = (stratum, arm, actuation.route)
        branch[key] = branch.get(key, 0) + 1
    strata = sorted({stratum for stratum, _ in support})
    complete = all(
        support.get((stratum, arm), 0) > 0 for stratum in strata for arm in sib.ARMS
    )
    return {
        "passed": bool(complete and strata),
        "support": {f"{stratum}/{arm}": count for (stratum, arm), count in sorted(support.items())},
        "routes": {
            f"{stratum}/{arm}/{route}": count
            for (stratum, arm, route), count in sorted(branch.items())
        },
    }


# ---------------------------------------------------------------------------
# The gate.
# ---------------------------------------------------------------------------

def gate() -> dict[str, object]:
    checks = {
        "1_disabled_projection_reproduces_base": check_1_disabled_projection(),
        "2_owner_and_spell_receipts_complete": check_2_receipts_complete(),
        "3_real_neutral_share_fixed_wrapper": check_3_shared_wrapper(),
        "4_action_after_actuation_before_outcome": check_4_clock_ordering(),
        "5_identical_w_minus_different_optimal_actions": check_5_action_switch(),
        "6_real_payload_strictly_better_in_critical_cells": check_6_critical_strict_value(),
        "7_neutral_cells_zero_reveal_value": check_7_neutral_zero_reveal(),
        "8_focal_body_mutations_isolated": check_8_mutation_isolation(),
        "9_pattern_and_knockout_controls_executable": check_9_controls_executable(),
        "10_four_arms_positive_support_per_stratum": check_10_arm_support(),
    }
    passed = all(bool(result["passed"]) for result in checks.values())
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "registration": {
            "profiles": [profile.name for profile in GATE_PROFILES],
            "episodes": list(GATE_EPISODES),
            "master_seed": MASTER_SEED,
            "sibling_seed": SIBLING_SEED,
            "tape_seed": TAPE_SEED,
            "cell_classes": list(sib.CELL_CLASS),
            "shock_coefficients": {k: str(v) for k, v in sib.SHOCK_COEFF.items()},
            "critical_prior": {k: str(v) for k, v in sib.CRITICAL_PRIOR.items()},
            "conformance_tol": CONFORMANCE_TOL,
        },
        "checks": checks,
        "terminal": (
            "EOCIV_SIBLING_CAPABILITY_PRESENT"
            if passed
            else "EOCIV_SIBLING_CAPABILITY_ABSENT"
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(gate(), indent=2, default=str))
