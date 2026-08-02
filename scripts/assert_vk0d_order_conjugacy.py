"""V-K0D order-conjugacy assertion gate.

Contract: `docs/research/designs/VK0D_REALIZATION_DECISION_LEDGER.md`, VD-5 as
amended by **A-VD-5** (complete finite conjugacy panel; deliberate negative;
post-training recheck) and constrained by **A-VD-2** (the certified property is
permutation conjugacy `P01(a0,a1|x) = P10(a1,a0|swap(x))`, NOT same-state
serialization invariance `P01(a0,a1|x) = P10(a0,a1|x)`, which need not hold
while the second mover conditions on the first mover's realized edit).

What this module certifies, and nothing else:

1. **Pure check, complete finite panel.** At every panel state, the exact
   16-outcome joint distribution under order `[0,1]` at `x` and under order
   `[1,0]` at `swap(x)` agree bit-exactly in float64 after an identical,
   canonical accumulation order. Every probability comes from
   `FixedClockAREditPolicy.token_mass(...)` and every within-check roster
   advance from `advance_working_state(...)` -- reached through
   `audit_vk0c_order_transport.enumerate_order`, which is the single
   probability-authority chain. There is deliberately no second
   logits-to-probability path here.
2. **Executed prescribed-assignment control.** On a bounded subpanel, both
   agents are forced to each legal joint assignment under each order and five
   real primitive steps are rolled; physical-agent final skills, primitive
   actions, reward vector, match vectors and post-window state must be
   identical across the two orders. This is the reality anchor for the pure
   check -- the full panel is covered by the pure check alone.
3. **Deliberate negative witness.** `--mode negative-witness` restores the
   absolute-ID encoder and makes its two identity blocks deterministically
   consequential by hand-setting the input-layer weight columns that read them.
   The gate must return FAIL on that construction; the driver reports the mode
   as `NEGATIVE_WITNESS_REJECTED`. A random fresh reference that happens to
   fail is not the sensitivity proof (A-VD-5).

The panel is the COMPLETE finite support of A-VD-5, never natural
fresh-policy states:

* INITIAL class -- check 0, `active=[False, False]`, no incumbents,
  `ages=[0, 0]`, all four sign pairs;
* ACTIVE classes -- checks 1..7 x all four sign pairs x all 16 physical joint
  skill pairs x every age pair reachable at that check, `active=[True, True]`.

Reachability is A-VC-4's ageing rule (KEEP -> age + K0, SET -> age 0 at the
edit and K0 at the next check), so an active agent's pre-decision age at check
`c` lies in `{K0*m : m = 1..c}` and the reachable age pairs at check `c` number
`c**2`. Total panel: `4 * (1 + sum_{c=1..7} 16 * c**2) = 8964` states, each
compared under both order views. That equals `4 *
audit_vk0c_order_transport.reachable_state_bound()`, the same reachable-state
accounting the V-K0C propagation sweep uses; `assert_panel_complete` enforces
the structural shape and the driver records both counts in the witness.

There is no CLI knob that shrinks the panel: `check_indices` exists for the
focused tests only, so a witness written by this CLI is always over the
complete panel.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import itertools
import json
import math
import sys
import time
import types
from pathlib import Path
from typing import Any, Iterator, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
for _p in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np
import torch

from ha_ctse_process.r30_fixed_clock import INVALID_SKILL
from ha_ctse_process.standalone_agent import StandaloneProcessAgent

import audit_vk0b_r30_access as vk0b
import audit_vk0c_order_transport as vk0c
import run_vk0b_training as vk0b_training


# =============================================================================
# Frozen identity
# =============================================================================

GATE_VERSION = "vk0d-conjugacy-1"

MODE_FRESH = "fresh"
MODE_CHECKPOINT = "checkpoint"
MODE_NEGATIVE_WITNESS = "negative-witness"

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_NEGATIVE_WITNESS_REJECTED = "NEGATIVE_WITNESS_REJECTED"

REASON_CONJUGACY_BIT_EXACTNESS_FAILED = "CONJUGACY_BIT_EXACTNESS_FAILED"
REASON_MASS_SUM_OUT_OF_TOLERANCE = "MASS_SUM_OUT_OF_TOLERANCE"

# Toy geometry, re-used from the V-K0C driver rather than redefined.
K0 = vk0c.K0                      # 5
WINDOW = vk0c.WINDOW              # 5
N_SKILLS = vk0c.N_SKILLS          # 4
N_AGENTS = vk0c.N_AGENTS          # 2
TOTAL_CHECKS = vk0c.TOTAL_CHECKS  # 8
N_OUTCOMES = vk0c.N_OUTCOMES      # 16

ORDER_CANONICAL = vk0c.ORDER_CANONICAL   # "canonical"  -> (0, 1)
ORDER_REVERSED = vk0c.ORDER_REVERSED     # "reversed"   -> (1, 0)

SIGN_PAIRS: tuple[tuple[int, int], ...] = ((-1, -1), (-1, 1), (1, -1), (1, 1))

# A-VD-5's paired negative is the ABSOLUTE-ID encoder, i.e. the V-K0D
# REFERENCE/CONTROL config module. Frozen here rather than taken from `--config`
# so the sensitivity proof cannot be pointed at a different arm.
NEGATIVE_WITNESS_CONFIG = "config_d7_2b_toy_learned_keep"
NEGATIVE_WITNESS_DEFAULT_SEED = 2026080101

# The deterministic perturbation that makes the two absolute identity blocks
# consequential: a fixed, distinct constant added to the input-layer weight
# columns reading identity slot 0 and identity slot 1. Distinct per slot is what
# matters -- one shared constant would leave the two slots interchangeable and
# the witness would stay green for the wrong reason. Nothing is trained and
# nothing is randomized.
NEGATIVE_WITNESS_IDENTITY_SLOT_BIAS: tuple[float, ...] = (25.0, -25.0)

# The executed control's frozen representative ACTIVE state at check `c`:
# an asymmetric skill pair and an asymmetric age pair, both reachable at `c`
# (age K0 is reachable at every check >= 1; age K0*c is the oldest reachable
# age at check c).
EXECUTED_CONTROL_SKILLS: tuple[int, int] = (0, 1)

# Fixed torch/numpy seed installed before EVERY executed window, so both order
# views of one (state, assignment) start from an identical stream position and
# any difference they show is the order, not the sampler.
EXECUTED_CONTROL_STREAM_SEED = 20260802

# Every agent-indexed input `FixedClockAREditPolicy._token_context` takes, and
# what `swap_state` does to it. Read off that method's signature and body:
# `joint_obs[agent_id]`, `working_skills[agent_id]`, `working_ages[agent_id]`,
# `working_active[agent_id]` and `agent_relevance[:, agent_id, :]` are indexed
# by physical agent; `compact`, `team_vector` and `omega` are handed to
# `_hidden` whole and carry no agent axis, so they are the anonymous global
# state A-VD-5 leaves unchanged.
SWAPPED_COMPONENTS: tuple[dict[str, Any], ...] = (
    {
        "name": "joint_obs",
        "agent_axis": 0,
        "swap": "exchange the two agents' observation rows",
        "token_context_use": "joint_obs[agent_id:agent_id+1]",
    },
    {
        "name": "working_skills",
        "agent_axis": 0,
        "swap": "exchange the two agents' skill entries",
        "token_context_use": "working_skills[agent_id]",
    },
    {
        "name": "working_ages",
        "agent_axis": 0,
        "swap": "exchange the two agents' age entries",
        "token_context_use": "working_ages[agent_id]",
    },
    {
        "name": "working_active",
        "agent_axis": 0,
        "swap": "exchange the two agents' active-mask entries",
        "token_context_use": "working_active[agent_id]",
    },
    {
        "name": "agent_relevance",
        "agent_axis": 1,
        "swap": "exchange the two agents' relevance rows",
        "token_context_use": "agent_relevance[:, agent_id, :]",
    },
)

UNSWAPPED_COMPONENTS: tuple[dict[str, Any], ...] = (
    {
        "name": "compact",
        "agent_axis": None,
        "swap": "unchanged -- anonymous global state (A-VD-5)",
        "token_context_use": "compact",
    },
    {
        "name": "team_vector",
        "agent_axis": None,
        "swap": "unchanged -- anonymous global state (A-VD-5)",
        "token_context_use": "team_vector",
    },
    {
        "name": "omega",
        "agent_axis": None,
        "swap": "unchanged -- passed to _hidden whole, no agent axis",
        "token_context_use": "omega",
    },
)


class Vk0dGateError(Exception):
    """A structural violation that means this gate's own machinery is wrong
    (a duplicated outcome coordinate, a non-finite mass, a panel that is not
    the frozen shape) rather than that the POLICY failed conjugacy. A policy
    failure is recorded as a mismatch and turns into a FAIL verdict."""


# =============================================================================
# The frozen finite panel (A-VD-5)
# =============================================================================


def reachable_active_ages(check_index: int) -> tuple[int, ...]:
    """Pre-decision ages an ACTIVE agent can carry at `check_index`.

    A-VC-4's ageing rule: a skill SET at check `j` has age 0 at the edit, K0 at
    check `j+1`, and K0*(c-j) at check `c` under KEEPs. The earliest possible
    edit is check 0, so at check `c >= 1` the reachable set is
    `{K0*m : m = 1..c}` -- `c` values, and `c**2` ordered pairs.
    """
    check_index = int(check_index)
    if check_index < 1:
        return ()
    return tuple(K0 * m for m in range(1, check_index + 1))


def reachable_age_pairs(check_index: int) -> tuple[tuple[int, int], ...]:
    ages = reachable_active_ages(check_index)
    return tuple(itertools.product(ages, ages))


class PanelState(types.SimpleNamespace):
    """One panel entry: `(signs, check_index, skills, ages, active)`."""

    def identity(self) -> dict[str, Any]:
        return {
            "check_index": int(self.check_index),
            "initial_signs": [int(x) for x in self.signs],
            "skills": [int(x) for x in self.skills],
            "ages": [int(x) for x in self.ages],
            "active": [bool(x) for x in self.active],
        }

    def key(self) -> tuple:
        return (
            int(self.check_index),
            tuple(int(x) for x in self.signs),
            tuple(int(x) for x in self.skills),
            tuple(int(x) for x in self.ages),
            tuple(bool(x) for x in self.active),
        )


def enumerate_panel(check_indices: Sequence[int] | None = None) -> list[PanelState]:
    """The COMPLETE finite panel of A-VD-5, in a fixed deterministic order.

    `check_indices` exists for the focused tests only and is not reachable from
    the CLI; a CLI run always enumerates checks 0..TOTAL_CHECKS-1.
    """
    checks = list(range(TOTAL_CHECKS)) if check_indices is None else [int(c) for c in check_indices]
    states: list[PanelState] = []
    for check_index in checks:
        for signs in SIGN_PAIRS:
            if check_index == 0:
                states.append(
                    PanelState(
                        signs=tuple(signs),
                        check_index=0,
                        skills=(INVALID_SKILL, INVALID_SKILL),
                        ages=(0, 0),
                        active=(False, False),
                    )
                )
                continue
            for skill0 in range(N_SKILLS):
                for skill1 in range(N_SKILLS):
                    for age0, age1 in reachable_age_pairs(check_index):
                        states.append(
                            PanelState(
                                signs=tuple(signs),
                                check_index=int(check_index),
                                skills=(int(skill0), int(skill1)),
                                ages=(int(age0), int(age1)),
                                active=(True, True),
                            )
                        )
    return states


def panel_inventory(states: Sequence[PanelState]) -> dict[str, Any]:
    initial = [s for s in states if s.check_index == 0]
    active = [s for s in states if s.check_index != 0]
    age_pairs_per_check: dict[str, int] = {}
    for check_index in sorted({int(s.check_index) for s in states}):
        if check_index == 0:
            age_pairs_per_check["0"] = 1
        else:
            age_pairs_per_check[str(check_index)] = len(
                {tuple(int(x) for x in s.ages) for s in states if s.check_index == check_index}
            )
    return {
        "initial_states": len(initial),
        "active_states": len(active),
        "age_pairs_per_check": age_pairs_per_check,
        "total_states": len(states),
        "orders": 2,
    }


def assert_panel_complete(states: Sequence[PanelState]) -> None:
    """Structural completeness of the enumerated panel against A-VD-5.

    Fail-closed on: a duplicate state, a missing sign pair, a missing physical
    skill pair, a missing or unreachable age pair, a wrong active mask, or a
    per-check count that is not the frozen `4 * 16 * c**2`. A silently omitted
    class is exactly predicted failure mode (a) of this gate, so this is not
    plumbing coverage -- it is the tripwire.
    """
    keys = [s.key() for s in states]
    if len(set(keys)) != len(keys):
        raise Vk0dGateError(f"panel carries duplicate states: {len(keys) - len(set(keys))} duplicates")

    by_check: dict[int, list[PanelState]] = {}
    for state in states:
        by_check.setdefault(int(state.check_index), []).append(state)

    for check_index, group in sorted(by_check.items()):
        signs_seen = {tuple(int(x) for x in s.signs) for s in group}
        if signs_seen != set(SIGN_PAIRS):
            raise Vk0dGateError(
                f"check {check_index}: sign pairs {sorted(signs_seen)} != the frozen four {list(SIGN_PAIRS)}"
            )
        if check_index == 0:
            if len(group) != len(SIGN_PAIRS):
                raise Vk0dGateError(
                    f"INITIAL class carries {len(group)} states, expected exactly {len(SIGN_PAIRS)}"
                )
            for state in group:
                if (
                    tuple(int(x) for x in state.skills) != (INVALID_SKILL, INVALID_SKILL)
                    or tuple(int(x) for x in state.ages) != (0, 0)
                    or tuple(bool(x) for x in state.active) != (False, False)
                ):
                    raise Vk0dGateError(f"INITIAL class state {state.identity()} is not the frozen A-VD-5 class")
            continue

        expected_ages = set(reachable_age_pairs(check_index))
        expected_count = len(SIGN_PAIRS) * (N_SKILLS**2) * len(expected_ages)
        if len(group) != expected_count:
            raise Vk0dGateError(
                f"check {check_index}: {len(group)} ACTIVE states, expected "
                f"{len(SIGN_PAIRS)} signs x {N_SKILLS ** 2} skill pairs x {len(expected_ages)} age pairs "
                f"= {expected_count}"
            )
        for signs in SIGN_PAIRS:
            per_sign = [s for s in group if tuple(int(x) for x in s.signs) == signs]
            skills_seen = {tuple(int(x) for x in s.skills) for s in per_sign}
            expected_skills = set(itertools.product(range(N_SKILLS), repeat=N_AGENTS))
            if skills_seen != expected_skills:
                raise Vk0dGateError(
                    f"check {check_index} signs {signs}: skill pairs {sorted(skills_seen)} != all "
                    f"{len(expected_skills)} physical joint pairs"
                )
            for skills in expected_skills:
                ages_seen = {
                    tuple(int(x) for x in s.ages)
                    for s in per_sign
                    if tuple(int(x) for x in s.skills) == skills
                }
                if ages_seen != expected_ages:
                    raise Vk0dGateError(
                        f"check {check_index} signs {signs} skills {skills}: age pairs "
                        f"{sorted(ages_seen)} != the {len(expected_ages)} reachable pairs "
                        f"{sorted(expected_ages)}"
                    )
            for state in per_sign:
                if tuple(bool(x) for x in state.active) != (True, True):
                    raise Vk0dGateError(f"ACTIVE class state {state.identity()} does not carry active [True, True]")


# =============================================================================
# swap(x) -- A-VD-5, explicit over every physical-agent-indexed component
# =============================================================================


def swap_state(state: dict[str, Any]) -> dict[str, Any]:
    """Exchange every physical-agent-indexed component of a decision state.

    Swapped (see `SWAPPED_COMPONENTS`): the two agents' observation rows, skill
    entries, age entries, active-mask entries and `agent_relevance` rows.
    Unchanged (see `UNSWAPPED_COMPONENTS`): `compact`, `team_vector` and
    `omega` -- the anonymous global target/sign state, which A-VD-5 holds
    fixed. `omega` is checked against `_token_context`'s body rather than
    assumed: it is handed to `_hidden` whole and carries no agent axis.

    `swap_state` is an involution on this representation:
    `swap_state(swap_state(x))` reproduces `x` byte-exactly.
    """
    out: dict[str, Any] = dict(state)
    joint_obs = state["joint_obs"]
    out["joint_obs"] = joint_obs.flip(0).clone()
    relevance = state.get("agent_relevance")
    out["agent_relevance"] = None if relevance is None else relevance.flip(1).clone()
    for key in ("compact", "team_vector", "omega"):
        value = state.get(key)
        out[key] = None if value is None else value.clone()
    out["skills"] = tuple(reversed(tuple(int(x) for x in state["skills"])))
    out["ages"] = tuple(reversed(tuple(int(x) for x in state["ages"])))
    out["active"] = tuple(reversed(tuple(bool(x) for x in state["active"])))
    return out


# =============================================================================
# The conjugacy check per panel state (A-VC-7-style validity, one canonical p̂)
# =============================================================================


def joint_masses(agent, state: dict[str, Any], order_code: str) -> dict[tuple[int, int], float]:
    """Raw float64 joint masses keyed by the physical final-skill pair.

    Delegates the whole probability chain to
    `audit_vk0c_order_transport.enumerate_order` -- `token_mass` for every
    probability, `advance_working_state` for every roster advance, its own
    A-VC-1 branch-semantics assertions (same-label SET mass exactly zero, KEEP
    mass exactly zero with no incumbent, every mass finite and non-negative),
    its 16-distinct-coordinate assertion and its no-RNG-consumed assertion.
    Nothing here recomputes a probability.
    """
    outcomes = vk0c.enumerate_order(
        agent,
        state,
        tuple(int(x) for x in state["skills"]),
        tuple(int(x) for x in state["ages"]),
        tuple(bool(x) for x in state["active"]),
        order_code,
    )
    masses: dict[tuple[int, int], float] = {}
    for outcome in outcomes:
        key = (int(outcome.final_skills[0]), int(outcome.final_skills[1]))
        if key in masses:
            raise Vk0dGateError(f"duplicate final-skill coordinate {key} in the {order_code} enumeration")
        # float64 multiplication is exactly commutative, so the two order views
        # multiply the identical operand pair to the identical float64 value
        # regardless of which agent moved first.
        value = float(np.float64(outcome.raw_first_mass) * np.float64(outcome.raw_second_mass))
        if not np.isfinite(value) or value < 0.0:
            raise Vk0dGateError(f"joint mass at {key} is {value!r}, must be finite and non-negative")
        masses[key] = value
    if len(masses) != N_OUTCOMES:
        raise Vk0dGateError(f"{order_code} enumeration produced {len(masses)} coordinates, expected {N_OUTCOMES}")
    return masses


def conjugate_relabel(masses: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
    """`P10(z1,z0|swap(x))` re-expressed in the original physical labelling.

    Doing the relabel BEFORE normalization is what makes the two accumulations
    canonical: both then run `math.fsum` over the identical sorted key sequence
    of the identical float64 values, so bit-exact equality is a statement about
    the policy and never about summation order (predicted failure mode (b)).
    """
    return {(int(key[1]), int(key[0])): float(value) for key, value in masses.items()}


def canonical_phat(masses: dict[tuple[int, int], float], dtype_name: str) -> dict[str, Any]:
    """A-VC-7: validate, then ONE canonical normalized distribution."""
    keys = sorted(masses)
    raw_sum = math.fsum(masses[key] for key in keys)
    if not np.isfinite(raw_sum) or raw_sum <= 0.0:
        raise Vk0dGateError(f"raw joint mass sum {raw_sum!r} is not positive and finite")
    tolerance = vk0c.mass_tolerance(dtype_name)
    within = bool(abs(raw_sum - 1.0) <= tolerance)
    phat = {key: float(np.float64(masses[key]) / np.float64(raw_sum)) for key in keys}
    return {
        "phat": phat,
        "raw_joint_mass_sum": float(raw_sum),
        "normalization_correction": float(1.0 - raw_sum),
        "mass_tolerance": float(tolerance),
        "within_tolerance": within,
    }


def _phat_json(phat: dict[tuple[int, int], float]) -> dict[str, float]:
    return {f"{key[0]},{key[1]}": float(value) for key, value in sorted(phat.items())}


def check_state_conjugacy(
    agent,
    state: dict[str, Any],
    dtype_name: str,
    swapped: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """One panel state. Returns `None` on agreement, or a mismatch record.

    `P01(z0,z1|x)` from order `[0,1]` at `x`; `P10(z1,z0|swap(x))` from order
    `[1,0]` at `swap(x)`, relabelled into `x`'s physical labelling. Equality is
    bit-exact float64. It is never loosened.

    `swapped` is a test-only hook (never reachable from the CLI, and never
    passed by `run_pure_check`) that substitutes a deliberately incomplete
    swap, so a focused test can prove each agent-indexed component is actually
    covered by driving this check red.
    """
    swapped = swap_state(state) if swapped is None else swapped
    masses_01 = joint_masses(agent, state, ORDER_CANONICAL)
    masses_10 = conjugate_relabel(joint_masses(agent, swapped, ORDER_REVERSED))

    canon_01 = canonical_phat(masses_01, dtype_name)
    canon_10 = canonical_phat(masses_10, dtype_name)

    for label, canon in (("P01", canon_01), ("P10_conjugate", canon_10)):
        if not canon["within_tolerance"]:
            return {
                "reason": REASON_MASS_SUM_OUT_OF_TOLERANCE,
                "distribution": label,
                "raw_joint_mass_sum": canon["raw_joint_mass_sum"],
                "mass_tolerance": canon["mass_tolerance"],
                "p01": _phat_json(canon_01["phat"]),
                "p10_conjugate": _phat_json(canon_10["phat"]),
            }

    phat_01 = canon_01["phat"]
    phat_10 = canon_10["phat"]
    if set(phat_01) != set(phat_10):
        raise Vk0dGateError(
            f"the two order views enumerate different outcome supports: "
            f"{sorted(set(phat_01) ^ set(phat_10))}"
        )
    disagreeing = [key for key in sorted(phat_01) if phat_01[key] != phat_10[key]]
    if not disagreeing:
        return None
    return {
        "reason": REASON_CONJUGACY_BIT_EXACTNESS_FAILED,
        "disagreeing_outcomes": [f"{k[0]},{k[1]}" for k in disagreeing],
        "first_disagreeing_outcome": f"{disagreeing[0][0]},{disagreeing[0][1]}",
        "p01": _phat_json(phat_01),
        "p10_conjugate": _phat_json(phat_10),
    }


def run_pure_check(
    *,
    agent: StandaloneProcessAgent,
    kernel: vk0c.WindowKernel,
    states: Sequence[PanelState],
    dtype_name: str,
) -> dict[str, Any]:
    """The pure conjugacy check over the panel.

    Fail-fast: A-VD-5 requires the gate to fail "with the state identity and
    both distributions recorded", so the sweep stops at the first mismatching
    state and records exactly that one. `states_checked` against
    `panel.total_states` therefore tells an analyzer mechanically whether the
    panel was completed.
    """
    contexts: dict[tuple[tuple[int, int], int], dict[str, Any]] = {}
    mismatches: list[dict[str, Any]] = []
    checked = 0
    for panel_state in states:
        key = (tuple(int(x) for x in panel_state.signs), int(panel_state.check_index))
        context = contexts.get(key)
        if context is None:
            obs, env_state = kernel.policy_inputs_at(key[0], key[1])
            context = vk0c.policy_context(agent, obs, env_state)
            contexts[key] = context
        state = {
            **context,
            "skills": tuple(int(x) for x in panel_state.skills),
            "ages": tuple(int(x) for x in panel_state.ages),
            "active": tuple(bool(x) for x in panel_state.active),
        }
        record = check_state_conjugacy(agent, state, dtype_name)
        checked += 1
        if record is not None:
            record["state"] = panel_state.identity()
            mismatches.append(record)
            break
    return {"states_checked": int(checked), "mismatches": mismatches}


# =============================================================================
# Executed prescribed-assignment control (A-VD-5 item 2 / VC-D2 semantics)
# =============================================================================


def executed_control_subpanel(check_indices: Sequence[int] | None = None) -> list[PanelState]:
    """All four sign pairs x the INITIAL class and one frozen representative
    ACTIVE state per check.

    The representative at check `c` is `skills=(0, 1)`, `ages=(K0, K0*c)` --
    asymmetric in both components (for `c >= 2`) and reachable at `c` by
    `reachable_active_ages`. Frozen here so the subpanel is a constant of the
    gate, never a per-run choice.
    """
    checks = list(range(TOTAL_CHECKS)) if check_indices is None else [int(c) for c in check_indices]
    states: list[PanelState] = []
    for check_index in checks:
        for signs in SIGN_PAIRS:
            if check_index == 0:
                states.append(
                    PanelState(
                        signs=tuple(signs),
                        check_index=0,
                        skills=(INVALID_SKILL, INVALID_SKILL),
                        ages=(0, 0),
                        active=(False, False),
                    )
                )
                continue
            ages = (K0, K0 * int(check_index))
            reachable = set(reachable_active_ages(check_index))
            if not set(ages) <= reachable:
                raise Vk0dGateError(
                    f"executed-control representative ages {ages} are not reachable at check {check_index} "
                    f"({sorted(reachable)})"
                )
            states.append(
                PanelState(
                    signs=tuple(signs),
                    check_index=int(check_index),
                    skills=EXECUTED_CONTROL_SKILLS,
                    ages=ages,
                    active=(True, True),
                )
            )
    return states


def _executed_window(
    *,
    agent: StandaloneProcessAgent,
    config,
    wrapped_env,
    env_seed: int,
    panel_state: PanelState,
    targets: tuple[int, int],
    order_code: str,
) -> dict[str, Any]:
    """Force BOTH agents onto `targets` under `order_code` and roll exactly
    five executed primitive steps.

    The env is rebuilt at `(steps = check_index * K0, signs)` by zero-action
    stepping, exactly as `audit_vk0c_order_transport` does (the toy's clock
    advances unconditionally and `_targets()` reads only `steps` and the two
    reset-drawn signs), and the case's pre-decision roster is installed
    directly the way `execute_one_window_transition` installs it.

    The torch/numpy streams are re-seeded to the same fixed value before every
    window so the two order views start from an identical stream position:
    otherwise a difference in `act_low`'s draws would be indistinguishable from
    a difference caused by the order.
    """
    torch.manual_seed(int(EXECUTED_CONTROL_STREAM_SEED))
    np.random.seed(vk0b._legacy_numpy_seed(int(EXECUTED_CONTROL_STREAM_SEED)))

    obs, info = wrapped_env.reset(seed=int(env_seed))
    state = info.get("state")
    agent.reset_env_state(0)
    for _ in range(int(panel_state.check_index) * K0):
        obs, _reward, _term, _trunc, info = wrapped_env.step(vk0c._zero_joint_action())
        state = info.get("next_state", state)

    observed_signs = (
        int(np.sign(wrapped_env.env._initial_slow_sign)),
        int(np.sign(wrapped_env.env._initial_fast_sign)),
    )
    if observed_signs != tuple(int(x) for x in panel_state.signs):
        raise Vk0dGateError(
            f"executed control landed on signs {observed_signs}, expected {tuple(panel_state.signs)}"
        )

    agent.active_skills[0, :] = np.asarray(
        [max(int(s), 0) for s in panel_state.skills], dtype=agent.active_skills.dtype
    )
    agent.skill_age[0, :] = np.asarray(panel_state.ages, dtype=agent.skill_age.dtype)
    agent.has_active_skill[0, :] = np.asarray(panel_state.active, dtype=bool)
    agent.steps_to_check[0] = 0

    forced = {
        i: vk0c.forced_token_for_target(
            int(panel_state.skills[i]), bool(panel_state.active[i]), int(targets[i])
        )
        for i in range(N_AGENTS)
    }
    agent.maybe_assign_skills(
        obs,
        state=state,
        step=int(panel_state.check_index) * K0,
        k=K0,
        env_id=0,
        deterministic=False,
        collect_r31=False,
        forced_tokens=forced,
        agent_order=np.asarray(vk0c.ORDER_SEQUENCES[order_code], dtype=np.int64),
    )
    realized = (int(agent.active_skills[0][0]), int(agent.active_skills[0][1]))

    rewards: list[float] = []
    slow: list[int] = []
    fast: list[int] = []
    actions_log: list[list[list[float]]] = []
    step = int(panel_state.check_index) * K0
    max_steps = int(config.max_steps)
    for _ in range(WINDOW):
        actions, _logp, _values = agent.act_low(obs, env_id=0, deterministic=False, state=state)
        actions_arr = np.asarray(actions, dtype=np.float32).reshape(N_AGENTS, -1)
        actions_log.append([[float(x) for x in row] for row in actions_arr])
        obs, reward, terminated, truncated, info = wrapped_env.step(actions)
        state = info.get("next_state", state)
        metrics = info.get("reward_info") or {}
        rewards.append(float(reward))
        slow.append(vk0b._binary_match(metrics.get("r39_toy_slow_match", 0.0)))
        fast.append(vk0b._binary_match(metrics.get("r39_toy_fast_match", 0.0)))
        step += 1
        done = bool(terminated or truncated) or step >= max_steps
        agent.record_environment_step(
            0, reward=float(reward), next_obs=obs, next_state=state, done=done, collect_r31=False
        )
        if done:
            break
    if len(rewards) != WINDOW:
        raise Vk0dGateError(f"executed control rolled {len(rewards)} steps, expected exactly {WINDOW}")

    return {
        "realized_skills": [int(x) for x in realized],
        "primitive_actions": actions_log,
        "reward_vector": rewards,
        "slow_match_vector": slow,
        "fast_match_vector": fast,
        "post_window_state_hash": vk0c.hash_bytes(np.asarray(state, dtype=np.float32).tobytes()),
    }


EXECUTED_CONTROL_COMPARED_FIELDS: tuple[str, ...] = (
    "realized_skills",
    "primitive_actions",
    "reward_vector",
    "slow_match_vector",
    "fast_match_vector",
    "post_window_state_hash",
)


def run_executed_control(
    *,
    agent: StandaloneProcessAgent,
    config,
    kernel: vk0c.WindowKernel,
    states: Sequence[PanelState],
) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    assignments = 0
    sign_seeds = kernel.sign_seeds()
    for signs in SIGN_PAIRS:
        env_seed = int(sign_seeds[tuple(signs)])
        subpanel = [s for s in states if tuple(int(x) for x in s.signs) == tuple(signs)]
        if not subpanel:
            continue
        wrapped_env = vk0b.make_env(config, env_seed)
        try:
            for panel_state in subpanel:
                for target0 in range(N_SKILLS):
                    for target1 in range(N_SKILLS):
                        targets = (int(target0), int(target1))
                        per_order = {
                            order_code: _executed_window(
                                agent=agent,
                                config=config,
                                wrapped_env=wrapped_env,
                                env_seed=env_seed,
                                panel_state=panel_state,
                                targets=targets,
                                order_code=order_code,
                            )
                            for order_code in (ORDER_CANONICAL, ORDER_REVERSED)
                        }
                        assignments += 1
                        for order_code, outcome in per_order.items():
                            if outcome["realized_skills"] != [int(x) for x in targets]:
                                mismatches.append(
                                    {
                                        "state": panel_state.identity(),
                                        "assignment": [int(x) for x in targets],
                                        "field": "realized_skills_vs_forced",
                                        "order_code": order_code,
                                        "observed": outcome["realized_skills"],
                                        "expected": [int(x) for x in targets],
                                    }
                                )
                        for field in EXECUTED_CONTROL_COMPARED_FIELDS:
                            left = per_order[ORDER_CANONICAL][field]
                            right = per_order[ORDER_REVERSED][field]
                            if left != right:
                                mismatches.append(
                                    {
                                        "state": panel_state.identity(),
                                        "assignment": [int(x) for x in targets],
                                        "field": field,
                                        "canonical": left,
                                        "reversed": right,
                                    }
                                )
        finally:
            wrapped_env.close()
    return {"states": len(states), "assignments": int(assignments), "mismatches": mismatches}


# =============================================================================
# Agent construction, including the deliberate negative witness
# =============================================================================


def _identity_block_columns(policy) -> tuple[tuple[int, int], ...]:
    """Input-layer weight column ranges reading each absolute identity slot.

    `_hidden` concatenates `[obs, skill_onehot, age_feature, compact,
    team_vector, (omega), (relevance), roster]`, so the roster prefix is the
    LAST `ar_prefix_dim` columns; within it, `encode_working_roster` lays out
    `[count block (n_skills), identity block (n_agents * n_skills), age block
    (n_agents * n_skills)]`.
    """
    linear = policy.input[1]
    prefix_start = int(linear.in_features) - int(policy.ar_prefix_dim)
    identity_offset = prefix_start + int(policy.n_skills)
    return tuple(
        (identity_offset + slot * int(policy.n_skills), identity_offset + (slot + 1) * int(policy.n_skills))
        for slot in range(int(policy.n_agents))
    )


def build_negative_witness_agent(training_seed: int) -> StandaloneProcessAgent:
    """A-VD-5's deliberate negative: the ABSOLUTE-ID encoder with its two
    identity blocks made deterministically consequential.

    A fresh policy of `NEGATIVE_WITNESS_CONFIG` is loaded, then a fixed, large,
    per-slot-distinct constant is ADDED to the input-layer weight columns that
    read identity slot 0 and identity slot 1. Nothing is trained and nothing is
    randomized, so the witness is a construction rather than a lucky draw:
    the identity slot an agent's roster fact lands in now materially moves the
    logits, and `swap(x)` moves that fact between slots.
    """
    agent = vk0c.build_fresh_agent(NEGATIVE_WITNESS_CONFIG, int(training_seed))
    policy = agent.high
    if bool(getattr(policy, "conjugate_context", False)):
        raise Vk0dGateError(
            "the negative witness must be built on the ABSOLUTE-ID encoder; "
            f"{NEGATIVE_WITNESS_CONFIG} resolved to conjugate_context=True"
        )
    if len(NEGATIVE_WITNESS_IDENTITY_SLOT_BIAS) != int(policy.n_agents):
        raise Vk0dGateError(
            f"negative-witness bias has {len(NEGATIVE_WITNESS_IDENTITY_SLOT_BIAS)} entries for "
            f"n_agents={policy.n_agents}"
        )
    with torch.no_grad():
        for slot, (lo, hi) in enumerate(_identity_block_columns(policy)):
            policy.input[1].weight[:, lo:hi] += float(NEGATIVE_WITNESS_IDENTITY_SLOT_BIAS[slot])
    policy.eval()
    return agent


def _resolved_config_hash(config_module_name: str, config) -> str:
    args = types.SimpleNamespace(
        seed=0,
        output_root="<gate>",
        config=str(config_module_name),
        nonscientific=False,
    )
    return vk0b_training.resolved_config_hash(vk0b_training.resolve_manifest(config, args))


# =============================================================================
# Gate driver
# =============================================================================


def run_gate(
    *,
    mode: str,
    config_module_name: str | None = None,
    training_seed: int | None = None,
    checkpoint_path: str | None = None,
    check_indices: Sequence[int] | None = None,
    run_executed: bool = True,
) -> dict[str, Any]:
    """Build the arm's agent, run the panel, and return the witness payload."""
    if mode == MODE_NEGATIVE_WITNESS:
        config_module_name = NEGATIVE_WITNESS_CONFIG
        seed = NEGATIVE_WITNESS_DEFAULT_SEED if training_seed is None else int(training_seed)
        agent = build_negative_witness_agent(seed)
        checkpoint_sha256 = None
    elif mode == MODE_FRESH:
        if config_module_name is None or training_seed is None:
            raise Vk0dGateError("--mode fresh requires --config and --seed")
        seed = int(training_seed)
        agent = vk0c.build_fresh_agent(str(config_module_name), seed)
        checkpoint_sha256 = None
    elif mode == MODE_CHECKPOINT:
        if config_module_name is None or checkpoint_path is None:
            raise Vk0dGateError("--mode checkpoint requires --config and --checkpoint")
        seed = None
        path = Path(checkpoint_path)
        if not path.is_file():
            raise Vk0dGateError(f"checkpoint not found at {path}")
        checkpoint_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        agent = vk0b.build_agent(importlib.import_module(str(config_module_name)).Config(), checkpoint_path=str(path))
    else:
        raise Vk0dGateError(f"unknown mode {mode!r}")

    config_module = importlib.import_module(str(config_module_name))
    config = config_module.Config()
    kernel = vk0c.WindowKernel(config)
    dtype_name = vk0c.policy_probability_dtype(agent)

    states = enumerate_panel(check_indices)
    assert_panel_complete(states)
    inventory = panel_inventory(states)

    pure = run_pure_check(agent=agent, kernel=kernel, states=states, dtype_name=dtype_name)

    if run_executed:
        executed = run_executed_control(
            agent=agent,
            config=config,
            kernel=kernel,
            states=executed_control_subpanel(check_indices),
        )
    else:
        executed = {"states": 0, "assignments": 0, "mismatches": []}

    failed = bool(pure["mismatches"]) or bool(executed["mismatches"])
    if mode == MODE_NEGATIVE_WITNESS:
        if not failed:
            # The witness passed the gate: the gate cannot go red, so it is not
            # a gate. Report FAIL-of-the-mode by declaring the verdict PASS,
            # which the driver treats as a hard error.
            verdict = VERDICT_PASS
        else:
            verdict = VERDICT_NEGATIVE_WITNESS_REJECTED
    else:
        verdict = VERDICT_FAIL if failed else VERDICT_PASS

    return {
        "gate_version": GATE_VERSION,
        "mode": str(mode),
        "config_module": str(config_module_name),
        "resolved_config_hash": _resolved_config_hash(str(config_module_name), config),
        "controller": str(config.high_controller),
        "seed": None if seed is None else int(seed),
        "checkpoint_sha256": checkpoint_sha256,
        "panel": inventory,
        "swapped_components": [dict(c) for c in SWAPPED_COMPONENTS]
        + [dict(c) for c in UNSWAPPED_COMPONENTS],
        "pure_check": pure,
        "executed_control": executed,
        "verdict": verdict,
        "torch_version": str(torch.__version__),
        "dtype": str(dtype_name),
    }


def write_witness(path: Path, payload: dict[str, Any]) -> None:
    """Write-once: an existing witness is never overwritten."""
    path = Path(path)
    if path.exists():
        raise Vk0dGateError(f"witness {path} already exists; the gate writes once")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="V-K0D order-conjugacy assertion gate.")
    parser.add_argument("--mode", required=True, choices=[MODE_FRESH, MODE_CHECKPOINT, MODE_NEGATIVE_WITNESS])
    parser.add_argument("--config", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    torch.set_num_threads(1)

    if args.mode == MODE_NEGATIVE_WITNESS and args.config not in (None, NEGATIVE_WITNESS_CONFIG):
        raise SystemExit(
            f"--mode negative-witness is frozen to {NEGATIVE_WITNESS_CONFIG}; refusing --config {args.config!r}"
        )

    started = time.perf_counter()
    witness = run_gate(
        mode=str(args.mode),
        config_module_name=args.config,
        training_seed=args.seed,
        checkpoint_path=args.checkpoint,
    )
    elapsed = time.perf_counter() - started
    write_witness(Path(args.out), witness)

    print(f"VK0D_CONJUGACY_VERDICT={witness['verdict']}")
    print(f"VK0D_CONJUGACY_PANEL={witness['panel']}")
    print(f"VK0D_CONJUGACY_PURE_STATES_CHECKED={witness['pure_check']['states_checked']}")
    print(f"VK0D_CONJUGACY_PURE_MISMATCHES={len(witness['pure_check']['mismatches'])}")
    print(
        "VK0D_CONJUGACY_EXECUTED="
        f"{witness['executed_control']['states']} states / "
        f"{witness['executed_control']['assignments']} assignments / "
        f"{len(witness['executed_control']['mismatches'])} mismatches"
    )
    print(f"VK0D_CONJUGACY_ELAPSED_SECONDS={elapsed:.1f}")
    print(f"VK0D_CONJUGACY_OUT={Path(args.out)}")

    if args.mode == MODE_NEGATIVE_WITNESS:
        if witness["verdict"] != VERDICT_NEGATIVE_WITNESS_REJECTED:
            raise SystemExit(
                "NEGATIVE WITNESS NOT REJECTED: the constructed absolute-ID witness passed the "
                "conjugacy gate, so the gate cannot go red"
            )
        return
    if witness["verdict"] != VERDICT_PASS:
        raise SystemExit(f"VK0D_CONJUGACY_GATE_FAILED: {witness['pure_check']['mismatches'][:1]}")


if __name__ == "__main__":
    main()
