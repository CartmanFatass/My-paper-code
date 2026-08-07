"""MSSR-D2 P x action support-native value crossover (zero training).

External Pro's loop-4 ruling (``MSSR_D1_INTERFACE_PRESENT_D2_ACTION_VALUE_
CROSSOVER_REQUIRED``) funded exactly one next unit: determine whether the
ISOLATED historical P changes which action is VALUABLE under support-native
task return -- not whether a head can be trained to react to it.

Registered design (from the ruling, operationalized here):

* POPULATION -- the post-CHANGE_F D1 matched population: the frozen D1 pair as
  the primary proof-sized cell, and the remaining exposure-positive,
  P-different sourced pairs as prespecified replication cells.  No selection on
  downstream return.
* FIXED EXECUTOR -- D1 runs ``SUPPLIED_EXECUTOR_RUNTIME``, where the event
  skill has no necessary environment effect; D2 freezes the deterministic
  support-native executor ``skill 0 -> IDLE, skill 1 -> PERSIST, skill 2 ->
  SHORT`` (Pro's example mapping; the three primitives are the environment's
  entire primitive vocabulary, and PERSIST/SHORT are the two duty channels of
  the terminal utility).  The executor is identical across P arms and NEVER
  reads P.  It binds ONLY the target owner's primitives from the boundary event
  onward, keyed on the target's most recently committed event skill; every
  partner stays on the base-family script (the matched precommitted future
  branch tape).
* CROSSED CELLS at the matched post-CHANGE_F boundary: historical P arm
  (P-/P+) x boundary event skill action (a0/a1/a2) x memory read mode
  (KEEP_P / REBUILD_P / P_NULL).
* ESTIMAND -- the action-value interaction
  ``Psi = [Q(P+,a1)-Q(P+,a0)] - [Q(P-,a1)-Q(P-,a0)]`` (and the a2 analogue),
  where ``Q`` is the support-native task return (the terminal utility; rewards
  are terminal-only in this environment) of the episode with the boundary
  action forced and the future branch precommitted.  The stronger decision
  quantity is the value of a P-aware selector (argmax of the harness
  ``first_logits`` at the matched boundary preimage under the memory mode's P
  read) against the BEST P-blind constant selector under the same support and
  future branch law.

Load-bearing MECHANICAL source fact (reported, not judged): in the production
runtime ``partner_interaction_history`` is WRITTEN at exactly one site
(``variable_roster_event.py`` ``_write_partner_interaction``) and READ by
nothing; the only consumer of P in the codebase is the harness-only
``first_logits`` head.  Under this registered harness, P can therefore reach
the return ONLY through the boundary selector.  The forced-action Q table does
NOT probe that channel (its actions are forced, so it is P-independent by
construction): it measures the ACTION channel and the residual environment
asymmetry (arm main effects), and CONFIRMS by measurement the P-independence
of forced-action returns across arms and memory modes.  The P->return channel
itself is probed by the boundary-selector comparison; the interaction estimand
cancels arm-common and action-common effects.

Decision outcomes (Pro's vocabulary, decided by the registered mechanical rule
below; the READING of the outcome stays with External Pro):

* ``MSSR_D2_P_ACTION_VALUE_PRESENT`` -- some registered cell shows a nonzero
  action-value interaction, or the P-aware selector strictly beats the best
  P-blind constant selector.
* ``MSSR_D2_P_INTERFACE_PRESENT_VALUE_NULL`` -- the crossed population is
  valid and every interaction and selector margin is exactly null within
  TAU_VALUE.
* ``MSSR_D2_VALUE_POPULATION_NOT_CLOSED`` -- the environment/executor does not
  provide a valid crossed opportunity population.

This module wires ``first_logits`` ONLY as the harness boundary selector;
production execution and replay still call ``.logits()``.  It licenses no
scientific or value claim.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Sequence

import torch

from ha_ctse_process.dynamic_roster_testbed import IDLE, PERSIST, SHORT

from experiments.candidates.vsp_06_mssr.history_reconvergence_search import (
    Tape,
    make_core,
    make_environment,
)
from experiments.candidates.vsp_06_mssr.d1_change_f_matched_pair import (
    FROZEN_SOURCED_PAIR,
    SourcedPair,
    TERMINAL_PRESENT as D1_TERMINAL_PRESENT,
    capture_post_change_f,
    make_change_f_preframe,
    proof as d1_proof,
    reconstruct_actor_inputs,
    source_exposure_positive_candidates,
)

torch.set_num_threads(1)

RAW_OUTPUT_BINDING = "vsp_06_mssr.d2_p_action_value_crossover.v1"

ACTIVE = "ACTIVE"

# --- Terminals (Pro's decision vocabulary). ----------------------------------
TERMINAL_VALUE_PRESENT = "MSSR_D2_P_ACTION_VALUE_PRESENT"
TERMINAL_VALUE_NULL = "MSSR_D2_P_INTERFACE_PRESENT_VALUE_NULL"
TERMINAL_NOT_CLOSED = "MSSR_D2_VALUE_POPULATION_NOT_CLOSED"

#: Exact-null tolerance for returns: the terminal utility is a ratio of small
#: integer counters, and every registered rollout is deterministic, so a real
#: effect moves it by a quantized amount many orders above this floor.
TAU_VALUE = 1e-12

# --- The frozen support-native executor (Pro's example mapping). -------------
EXECUTOR_SKILL_TO_PRIMITIVE: dict[int, int] = {0: IDLE, 1: PERSIST, 2: SHORT}

#: The three boundary event-skill actions (the model's full skill vocabulary).
BOUNDARY_ACTIONS: tuple[int, ...] = (0, 1, 2)

# --- Memory read modes (registered ops at the boundary). ---------------------
MODE_KEEP_P = "KEEP_P"
MODE_REBUILD_P = "REBUILD_P"
MODE_P_NULL = "P_NULL"
MEMORY_MODES: tuple[str, ...] = (MODE_KEEP_P, MODE_REBUILD_P, MODE_P_NULL)


def make_memory_mode_preframe(mode: str, target_key: str, physical_time: int):
    """The registered boundary memory op for one arm (fires with CHANGE_F).

    ``KEEP_P`` is the identity.  ``REBUILD_P`` drops the target's accumulated
    history object at the boundary, so the retained value restarts from the
    current (post-boundary) writes only.  ``P_NULL`` zeroes the retained scalar
    while keeping the row provenance.  Each op touches ONLY the target record's
    ``partner_interaction_history`` at the single registered physical time;
    production reads nothing from P, so these ops are also how the boundary
    selector's P read is defined (KEEP_P -> the retained value; REBUILD_P and
    P_NULL -> 0.0 at the boundary).
    """
    if mode not in MEMORY_MODES:
        raise ValueError(f"unknown memory mode {mode!r}")
    target = str(target_key)
    phys = int(physical_time)

    def fn(c) -> None:
        if int(c.physical_time) != phys:
            return
        record = c.records.get(target)
        if record is None or record.status != ACTIVE:
            return
        if mode == MODE_KEEP_P:
            return
        history = record.partner_interaction_history
        if history is None:
            return
        if mode == MODE_REBUILD_P:
            record.partner_interaction_history = None
        else:  # MODE_P_NULL
            record.partner_interaction_history = type(history)(
                current_p=0.0, rows=history.rows
            )

    return fn


def _drive_with_boundary_action(
    core,
    env,
    tape: Tape,
    *,
    target_key: str,
    boundary_time: int,
    boundary_action: int,
    memory_mode: str,
) -> dict:
    """Run one crossed-cell rollout and return its support-native outcome.

    Replays the arm's legal history exactly as the D1 harness does
    (teacher-forced events, scripted primitives), with four registered
    differences from ``d1_change_f_matched_pair._drive``:

    * the CHANGE_F preframe and the memory-mode preframe fire at the boundary;
    * at the boundary event the TARGET's teacher token is ``boundary_action``
      instead of the base-script token (every other member, and every other
      event, keeps the base script -- the matched precommitted future tape);
    * from the boundary step onward the TARGET's primitive comes from the
      frozen executor keyed on the target's most recently committed event
      skill (partners keep the base-script primitives; before the boundary the
      target keeps them too);
    * per-step rewards are accumulated from the boundary step onward
      (support-native task return; rewards are terminal-only, so this equals
      the terminal utility).
    """
    target = str(target_key)
    boundary = int(boundary_time)
    change_f = make_change_f_preframe(target, boundary)
    memory_op = make_memory_mode_preframe(memory_mode, target, boundary)

    def preframe(c) -> None:
        change_f(c)
        memory_op(c)

    core.install_preframe_intervention(preframe)
    base = tape.base_script()
    perturbation = tape.perturbation_map()
    state = {
        "boundary_committed": False,
        "target_last_skill": None,
        "return_from_boundary": 0.0,
        "total_return": 0.0,
    }

    def handle(bound) -> None:
        post = bound.post_membership_pre_policy_snapshot
        frontier = tuple(post.frontier)
        order = tuple(sorted((str(key) for key in frontier), key=int))
        teacher = {str(key): base.token(str(key)) for key in frontier}
        if int(core.physical_time) == boundary and target in teacher:
            teacher[target] = int(boundary_action)
            state["boundary_committed"] = True
        if target in teacher:
            state["target_last_skill"] = int(teacher[target])
        core.apply_transaction(
            bound,
            teacher_actions=teacher,
            teacher_order=order,
            deterministic_policy=True,
        )

    transaction = env.reset_event_runtime(tape.episode_id)
    handle(core.bind_due_frontier(transaction))
    while True:
        active = tuple(env.environment.active_keys)
        actions = {int(key): base.primitive(int(key)) for key in active}
        for (step, key), value in perturbation.items():
            if int(step) == int(core.physical_time) and int(key) in actions:
                actions[int(key)] = int(value)
        if (
            state["boundary_committed"]
            and int(core.physical_time) >= boundary
            and int(target) in actions
            and state["target_last_skill"] is not None
        ):
            actions[int(target)] = EXECUTOR_SKILL_TO_PRIMITIVE[
                state["target_last_skill"]
            ]
        at_or_after_boundary = int(core.physical_time) >= boundary
        step_result = env.step_event_runtime(actions)
        reward = float(step_result.reward)
        state["total_return"] += reward
        if at_or_after_boundary and state["boundary_committed"]:
            state["return_from_boundary"] += reward
        core.complete_primitive_transition(reward)
        if step_result.terminated:
            core.close_terminal()
            break
        handle(core.bind_due_frontier(step_result.next_transaction))
    return state


def cell_return(
    pair: SourcedPair,
    *,
    perturbed_arm: bool,
    boundary_action: int,
    memory_mode: str,
) -> dict:
    """Q for one crossed cell: one arm, one forced boundary action, one mode."""
    tape = pair.perturbed_tape() if perturbed_arm else pair.base_tape()
    core = make_core(0)
    env = make_environment()
    outcome = _drive_with_boundary_action(
        core,
        env,
        tape,
        target_key=pair.target_key,
        boundary_time=pair.physical_time,
        boundary_action=int(boundary_action),
        memory_mode=memory_mode,
    )
    if not outcome["boundary_committed"]:
        raise RuntimeError(
            f"target {pair.target_key} had no boundary event at physical_time "
            f"{pair.physical_time}"
        )
    return outcome


def q_table(pair: SourcedPair, *, memory_mode: str) -> dict:
    """The full Q table for one pair under one memory mode."""
    table: dict[str, float] = {}
    for perturbed_arm in (False, True):
        arm = "plus" if perturbed_arm else "minus"
        for action in BOUNDARY_ACTIONS:
            outcome = cell_return(
                pair,
                perturbed_arm=perturbed_arm,
                boundary_action=action,
                memory_mode=memory_mode,
            )
            table[f"q_{arm}_a{action}"] = float(outcome["return_from_boundary"])
    return table


def interactions(table: dict) -> dict:
    """Pro's estimand: the P x action interaction for a1 and a2 against a0,
    plus the per-action arm main effects (residual environment asymmetry)."""
    psi_a1 = (table["q_plus_a1"] - table["q_plus_a0"]) - (
        table["q_minus_a1"] - table["q_minus_a0"]
    )
    psi_a2 = (table["q_plus_a2"] - table["q_plus_a0"]) - (
        table["q_minus_a2"] - table["q_minus_a0"]
    )
    return {
        "psi_a1_vs_a0": float(psi_a1),
        "psi_a2_vs_a0": float(psi_a2),
        "arm_main_effect_by_action": {
            f"a{action}": float(
                table[f"q_plus_a{action}"] - table[f"q_minus_a{action}"]
            )
            for action in BOUNDARY_ACTIONS
        },
        "action_effect_minus_arm": {
            f"a{action}_vs_a0": float(
                table[f"q_minus_a{action}"] - table["q_minus_a0"]
            )
            for action in BOUNDARY_ACTIONS
        },
    }


def boundary_selector(pair: SourcedPair, *, memory_mode: str) -> dict:
    """The P-aware boundary selector at the matched post-CHANGE_F preimage.

    Reconstructs the D1 matched actor inputs for both arms (byte-identical
    non-P quotient) and evaluates the harness ``first_logits`` with the memory
    mode's P read (KEEP_P -> each arm's retained P; REBUILD_P / P_NULL -> 0.0),
    returning the argmax skill per arm.  Zero training; the untrained head is
    the registered D1 interface, and the selector's VALUE (not its wiring) is
    the question.
    """
    cap_minus = capture_post_change_f(
        pair.base_tape(), pair.target_key, pair.physical_time
    )
    cap_plus = capture_post_change_f(
        pair.perturbed_tape(), pair.target_key, pair.physical_time
    )
    core = make_core(0)
    model = core.commitment_model
    selections: dict[str, int] = {}
    logits_report: dict[str, list[float]] = {}
    for arm, captured in (("minus", cap_minus), ("plus", cap_plus)):
        member_embedding, selected_summary, pre_hidden = reconstruct_actor_inputs(
            model, captured
        )
        p_read = (
            float(captured["current_p"]) if memory_mode == MODE_KEEP_P else 0.0
        )
        with torch.no_grad():
            logits, _ = model.first_logits(
                member_embedding, selected_summary, pre_hidden, partner_p=p_read
            )
        selections[arm] = int(torch.argmax(logits).item())
        logits_report[arm] = logits.numpy().tolist()
    return {
        "memory_mode": memory_mode,
        "selected_skill_minus": selections["minus"],
        "selected_skill_plus": selections["plus"],
        "first_logits_minus": logits_report["minus"],
        "first_logits_plus": logits_report["plus"],
        "p_read_minus": (
            float(cap_minus["current_p"]) if memory_mode == MODE_KEEP_P else 0.0
        ),
        "p_read_plus": (
            float(cap_plus["current_p"]) if memory_mode == MODE_KEEP_P else 0.0
        ),
    }


def selector_values(table: dict, selector: dict) -> dict:
    """P-aware selector value against the BEST P-blind constant selector."""
    aware = 0.5 * (
        table[f"q_minus_a{selector['selected_skill_minus']}"]
        + table[f"q_plus_a{selector['selected_skill_plus']}"]
    )
    blind_values = {
        f"a{action}": 0.5
        * (table[f"q_minus_a{action}"] + table[f"q_plus_a{action}"])
        for action in BOUNDARY_ACTIONS
    }
    best_blind = max(blind_values.values())
    return {
        "p_aware_value": float(aware),
        "p_blind_values": {k: float(v) for k, v in blind_values.items()},
        "best_p_blind_value": float(best_blind),
        "p_aware_margin": float(aware - best_blind),
    }


def _pair_identity(pair: SourcedPair) -> tuple:
    """Dedup key for sourced pairs: the design identity WITHOUT the float
    ``delta_p``, so an ULP-level change in the P computation cannot silently
    double-process the frozen primary pair as a replication cell."""
    return (
        pair.base_family,
        pair.target_key,
        pair.partner_key,
        tuple(pair.window),
        pair.physical_time,
    )


SCOPE = (
    "Zero-training SUPPORT-NATIVE value crossover on the post-CHANGE_F D1 "
    "matched population, as directed by External Pro's loop-4 ruling. SCOPE / "
    "honesty clauses: "
    "(1) POPULATION -- the frozen D1 pair is the primary proof-sized cell and "
    "the remaining exposure-positive P-different sourced pairs are prespecified "
    "replication cells; the frozen pair's |dP| is a SELECTED MAXIMUM among the "
    "sourced candidates, not a representative effect. No cell is selected on "
    "downstream return. "
    "(2) FIXED EXECUTOR -- skill 0 -> IDLE, skill 1 -> PERSIST, skill 2 -> "
    "SHORT, frozen before any Q was observed, identical across P arms, never "
    "reading P; it binds only the target's primitives from the boundary event "
    "onward, keyed on the target's most recently committed event skill. The "
    "boundary action's DIFFERENTIAL window ends at the target's next scripted "
    "event, if one occurs (the base script recommits the scripted skill "
    "there); if the boundary is the target's final event, the boundary skill "
    "binds to episode end. Either way the executor logic is IDENTICAL across "
    "every cell of the crossing, so cells differ only in the boundary action "
    "and the P arm. Partners stay on the base script: the future branch tape "
    "is matched and precommitted. "
    "(3) Q is the support-native task return from the boundary onward -- the "
    "environment's terminal utility (rewards are terminal-only) -- under "
    "CONTROLLED legal arms; no stochastic behavior law, no overlap claim. "
    "(4) MECHANICAL SOURCE FACT (reported, not judged): production writes P at "
    "one site and reads it nowhere; the only P consumer is the harness-only "
    "first_logits head, so P can reach the return only through the boundary "
    "selector. The forced-action Q table does NOT probe that channel (forced "
    "actions make it P-independent by construction); it measures the action "
    "channel and the residual environment asymmetry, and CONFIRMS by "
    "measurement the P-independence of forced-action returns; the P->return "
    "channel itself is probed by the boundary-selector comparison. "
    "(5) The interaction estimand Psi cancels arm-common effects (residual "
    "environment asymmetry between the two legal histories, reported "
    "separately as arm main effects) and action-common effects; a nonzero "
    "arm main effect is NOT a P effect. "
    "(6) MEMORY MODES are registered boundary ops on the target's history "
    "record only (KEEP_P identity; REBUILD_P drops the history object; P_NULL "
    "zeroes the retained scalar, keeping row provenance) and define the "
    "selector's P read; production consumes none of them. "
    "(7) The boundary selector is the UNTRAINED registered D1 interface head; "
    "its selections are a registered read, not a learned policy, and a null "
    "selector margin licenses no impossibility claim about trained heads -- "
    "symmetrically, Pro's ruling records that funding a trained-sensitivity "
    "test is NOT the next unit. "
    "(8) The terminal decision rule is MECHANICAL (registered below); the "
    "READING of the outcome -- value present / interface-present-value-null / "
    "population-not-closed, and what follows for the observation-alignment "
    "payload redirect or parking -- belongs to External Pro. "
    "(9) first_logits is wired ONLY in this harness (boundary selector); "
    "production execution and replay still call .logits(). No production "
    "policy effect of P is claimed."
)


@functools.lru_cache(maxsize=1)
def proof() -> dict:
    """Run the registered crossover and return the crossed tables + terminal."""
    report: dict = {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "scope": SCOPE,
        "executor": {str(k): int(v) for k, v in EXECUTOR_SKILL_TO_PRIMITIVE.items()},
        "boundary_actions": list(BOUNDARY_ACTIONS),
        "memory_modes": list(MEMORY_MODES),
        "tau_value": TAU_VALUE,
    }

    # The D1 gate must hold before any value question is asked of the pair.
    d1_report = d1_proof()
    report["d1_terminal"] = d1_report["terminal"]
    if d1_report["terminal"] != D1_TERMINAL_PRESENT:
        report["terminal"] = TERMINAL_NOT_CLOSED
        report["not_closed_reason"] = "D1 matched pair no longer PRESENT"
        return report

    # Population manifest: the primary cell and the prespecified replication
    # cells (every exposure-positive, P-different sourced pair).
    candidates, counts = source_exposure_positive_candidates()
    report["population_manifest"] = {
        "sourcing_counts": counts,
        "primary": {
            "base_family": FROZEN_SOURCED_PAIR.base_family,
            "target_key": FROZEN_SOURCED_PAIR.target_key,
            "partner_key": FROZEN_SOURCED_PAIR.partner_key,
            "window": list(FROZEN_SOURCED_PAIR.window),
            "physical_time": FROZEN_SOURCED_PAIR.physical_time,
            "delta_p": FROZEN_SOURCED_PAIR.delta_p,
        },
        "replication": [
            {
                "base_family": pair.base_family,
                "target_key": pair.target_key,
                "partner_key": pair.partner_key,
                "window": list(pair.window),
                "physical_time": pair.physical_time,
                "delta_p": pair.delta_p,
            }
            for pair in candidates
            if _pair_identity(pair) != _pair_identity(FROZEN_SOURCED_PAIR)
        ],
    }
    if not candidates:
        report["terminal"] = TERMINAL_NOT_CLOSED
        report["not_closed_reason"] = "no exposure-positive P-different pairs"
        return report

    try:
        # Primary cell: full memory-mode x action crossing.
        primary: dict = {}
        for mode in MEMORY_MODES:
            table = q_table(FROZEN_SOURCED_PAIR, memory_mode=mode)
            selector = boundary_selector(FROZEN_SOURCED_PAIR, memory_mode=mode)
            primary[mode] = {
                "q": table,
                "interactions": interactions(table),
                "selector": selector,
                "selector_value": selector_values(table, selector),
            }
        report["primary"] = primary

        # Replication cells: KEEP_P crossing only (prespecified).
        replication: list[dict] = []
        for pair in candidates:
            if _pair_identity(pair) == _pair_identity(FROZEN_SOURCED_PAIR):
                continue
            table = q_table(pair, memory_mode=MODE_KEEP_P)
            replication.append(
                {
                    "base_family": pair.base_family,
                    "target_key": pair.target_key,
                    "partner_key": pair.partner_key,
                    "window": list(pair.window),
                    "physical_time": pair.physical_time,
                    "delta_p": pair.delta_p,
                    "q": table,
                    "interactions": interactions(table),
                }
            )
        report["replication"] = replication
    except RuntimeError as error:
        report["terminal"] = TERMINAL_NOT_CLOSED
        report["not_closed_reason"] = str(error)
        return report

    # Mechanical decision rule (registered; reading belongs to Pro).
    all_interactions: list[float] = []
    margins: list[float] = []
    for mode in MEMORY_MODES:
        cell = primary[mode]
        all_interactions.append(abs(cell["interactions"]["psi_a1_vs_a0"]))
        all_interactions.append(abs(cell["interactions"]["psi_a2_vs_a0"]))
        margins.append(cell["selector_value"]["p_aware_margin"])
    for cell in replication:
        all_interactions.append(abs(cell["interactions"]["psi_a1_vs_a0"]))
        all_interactions.append(abs(cell["interactions"]["psi_a2_vs_a0"]))
    value_present = bool(
        max(all_interactions) > TAU_VALUE
        or max(margins) > TAU_VALUE
    )
    report["decision_inputs"] = {
        "max_abs_interaction": max(all_interactions),
        "max_selector_margin": max(margins),
    }
    report["terminal"] = (
        TERMINAL_VALUE_PRESENT if value_present else TERMINAL_VALUE_NULL
    )
    return report


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(proof(), indent=2, default=str))
