"""V-K0A exact renewal-urgency source-qualification oracle.

Contract: `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md` (VK-D1,
VK-D6, VK-D7, VK-D10, A-VK-D2, A-VK-D10), the ruling
`docs/external-review/rounds/20260801_variable_k_algorithm_direction/21_PRO_OPEN_RAW.md`
(MEASUREMENT sections 2-3, EVIDENCE_DESIGN Stage V-K0A), and the conformance
correction `docs/external-review/rounds/20260801_vk0_design_conformance/21_PRO_OPEN_RAW.md`
(VK-D2 correction) plus `22_PRO_CONVERGENCE.md` (clarification 1).

No training, no policy, no checkpoint. This computes the finite exhaustive
source estimand `U_src` on the real `TwoTimescaleRoleFreeActionsEnv` under the
fixed, zero-parameter `FixedSkillPrimitivePolicy` action table, for a frozen
112-row panel: 4 initial sign combinations x 2 permutation-equivariant
oracle-optimal incumbent tracks x 7 noninitial checks x 2 focal agents.

Nothing here reads or writes a checkpoint, an agent stack, or a learned
policy. Nothing here samples: every maximization is exhaustive over the legal
KEEP/SET support.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from envs.pettingzoo.two_timescale_role_free_actions import (
    TwoTimescaleRoleFreeActionsEnv,
)
from ha_ctse_process.standalone_agent import FixedSkillPrimitivePolicy

CONTRACT_ID = "VK0_TOY_RENEWAL_URGENCY"
PANEL_SCHEMA_VERSION = "vk0a-1"

ENV_FILE = PROJECT_ROOT / "envs" / "pettingzoo" / "two_timescale_role_free_actions.py"
ORACLE_FILE = Path(__file__).resolve()

N_SKILLS = 4
K0 = 5
NONINITIAL_CHECKS = 7          # check_index 1..7 (steps 5..35)
TOTAL_CHECKS = NONINITIAL_CHECKS + 1  # + the initial check (step 0)
WINDOW = 5                     # one k0 interval

# 0/1 are the x-axis (slow duty); 2/3 are the y-axis (fast duty). See
# config_d7_2b_toy_learned_keep.py's own comment on the action table.
SLOW_DUTY_SKILLS = (0, 1)
FAST_DUTY_SKILLS = (2, 3)

MATERIALITY = 0.5
FAST_ONLY_CHECK_INDICES = (1, 2, 3, 4, 5, 7)
JOINT_CHECK_INDEX = 6  # step 30: slow_block and fast_block both increment

VALID_VERDICT = "TOY_HETEROGENEOUS_RENEWAL_URGENCY_IDENTIFIED"
NOT_IDENTIFIED_VERDICT = "TOY_HETEROGENEOUS_RENEWAL_URGENCY_NOT_IDENTIFIED"
INVALID_VERDICT = "INVALID_RENEWAL_URGENCY_SOURCE_AUDIT"


class SourceAuditInvalid(Exception):
    """A corrupted legal-edit enumeration was detected before any further
    computation could rely on it. Raised at the point of detection so a
    malformed support (e.g. a same-label SET admitted, or an edit dropped)
    can never reach a downstream max() over an accidentally empty or
    mis-keyed candidate set -- fail fast and named, never a KeyError/
    ValueError surfacing from unrelated code three calls later."""


# --- git identity --------------------------------------------------------

def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def stage_commit() -> str:
    return _git("rev-parse", "HEAD")


def blob_sha(path: Path) -> str:
    return _git("hash-object", str(path))


# --- legality enumerator (a standalone, monkeypatchable symbol) ----------

def legal_options(incumbent: int, n_skills: int = N_SKILLS) -> list[tuple[str, int]]:
    """KEEP the incumbent, or SET to any of the n_skills-1 non-incumbent skills.

    This is the one place the noninitial legal joint action support is
    generated. A corrupted implementation (same-label SET admitted, or an
    edit dropped) is caught by `check_enumeration_exact` /
    `check_no_same_label_set` below, never silently absorbed.
    """
    incumbent = int(incumbent)
    opts = [("KEEP", incumbent)]
    for z in range(n_skills):
        if z != incumbent:
            opts.append(("SET", z))
    return opts


def check_enumeration_exact(opts: list[tuple[str, int]], n_skills: int = N_SKILLS) -> bool:
    return len(opts) == n_skills and len({skill for _, skill in opts}) == n_skills


def check_no_same_label_set(opts: list[tuple[str, int]], incumbent: int) -> bool:
    incumbent = int(incumbent)
    return all(not (kind == "SET" and skill == incumbent) for kind, skill in opts)


# --- permutation tracks (A-VK-D2) -----------------------------------------

def duty_allowed_skills(slot: int, track: int) -> tuple[int, int]:
    """`track`0: slot0=slow duty, slot1=fast duty. `track`1: mirrored."""
    if track not in (0, 1):
        raise ValueError(f"unknown track {track!r}")
    if track == 0:
        return SLOW_DUTY_SKILLS if slot == 0 else FAST_DUTY_SKILLS
    return FAST_DUTY_SKILLS if slot == 0 else SLOW_DUTY_SKILLS


def canonical_tuple(track: int, skill0: int, skill1: int) -> tuple[int, int]:
    """(skill_of_slow_duty_slot, skill_of_fast_duty_slot) -- never raw agent IDs."""
    if track == 0:
        return (int(skill0), int(skill1))
    return (int(skill1), int(skill0))


# --- environment plumbing --------------------------------------------------

def fingerprint(env: TwoTimescaleRoleFreeActionsEnv) -> tuple:
    state = env.get_current_state()
    return (
        int(state["current_step"]),
        tuple(round(float(x), 10) for x in state["r39_toy_slow_target"]),
        tuple(round(float(x), 10) for x in state["r39_toy_fast_target"]),
    )


def sign_of(vec, index: int) -> int:
    return 1 if float(vec[index]) > 0.0 else -1


def scan_sign_combinations(config) -> dict[tuple[int, int], int]:
    """reset(seed) over seed=0,1,2,... until all four (slow, fast) signs appear."""
    env = TwoTimescaleRoleFreeActionsEnv(config=config)
    found: dict[tuple[int, int], int] = {}
    seed = 0
    while len(found) < 4:
        env.reset(seed=seed)
        state = env.get_current_state()
        combo = (
            sign_of(state["r39_toy_slow_target"], 0),
            sign_of(state["r39_toy_fast_target"], 1),
        )
        if combo not in found:
            found[combo] = seed
        seed += 1
        if seed > 100_000:
            raise RuntimeError("could not find all four sign combinations within 100000 seeds")
    return found


class ValidityTracker:
    """AND-accumulates the eight named V-K0A validity predicates."""

    NAMES = (
        "identical_initial_state_across_branches",
        "no_check_crossed_within_window",
        "legal_edit_enumeration_exact",
        "same_label_set_excluded",
        "fixed_primitive_table_consistent",
        "only_external_reward_used",
        "permutation_relabels_only",
        "full_action_support_maximization_exhausted",
    )

    def __init__(self) -> None:
        self.results = {name: True for name in self.NAMES}
        self.violations: list[str] = []

    def mark(self, name: str, ok: bool, detail: str = "") -> None:
        if name not in self.results:
            raise KeyError(name)
        if not ok:
            self.results[name] = False
            self.violations.append(f"{name}: {detail}" if detail else name)

    def all_passed(self) -> bool:
        return all(self.results.values())


def evaluate_window(
    source_env: TwoTimescaleRoleFreeActionsEnv,
    skill0: int,
    skill1: int,
    action_table: np.ndarray,
    expected_table_hash: str,
    tracker: ValidityTracker | None,
    ref_fp: tuple,
) -> tuple[float, list[float]]:
    """Deep-copy `source_env`, step WINDOW times with the constant post-edit
    skills, return (total_reward, per-step rewards). Every named validity
    predicate that this call can evidence is checked in place.

    `ref_fp` is the ONE fingerprint the caller captured before its branch
    loop started (see `compute_incumbent_edit_results`) -- every branch's
    deepcopy-time fingerprint is compared against that single shared
    reference, never recomputed from `source_env` inside this same call
    (a same-call recomputation can never disagree with its own deepcopy and
    so could never evidence cross-branch corruption).

    `tracker=None` is for external callers (A-VK-D10: the V-K0B natural-check
    oracle invocation) that do not need V-K0A's bookkeeping -- the same
    computation still runs, only the `ValidityTracker.mark` calls are skipped."""
    table_hash = hashlib.sha256(np.ascontiguousarray(action_table).tobytes()).hexdigest()
    if tracker is not None:
        tracker.mark(
            "fixed_primitive_table_consistent",
            table_hash == expected_table_hash,
            "action table hash drifted between branches",
        )

    branch_env = copy.deepcopy(source_env)
    branch_fp = fingerprint(branch_env)
    if tracker is not None:
        tracker.mark(
            "identical_initial_state_across_branches",
            branch_fp == ref_fp,
            f"deepcopy fingerprint {branch_fp} != reference {ref_fp}",
        )

    start_step = int(branch_env.steps)
    action0 = action_table[int(skill0)]
    action1 = action_table[int(skill1)]
    rewards: list[float] = []
    for _ in range(WINDOW):
        _, step_rewards, _, _, infos = branch_env.step(
            {"agent_0": action0, "agent_1": action1}
        )
        same = step_rewards["agent_0"] == step_rewards["agent_1"]
        info0 = infos.get("agent_0", {}) or {}
        task_reward = (info0.get("reward_info") or {}).get("task_reward")
        matches_field = task_reward is not None and task_reward == step_rewards["agent_0"]
        if tracker is not None:
            tracker.mark(
                "only_external_reward_used",
                bool(same and matches_field),
                "stepped reward is not exactly the env's shared task_reward field",
            )
        rewards.append(float(step_rewards["agent_0"]))
    end_step = int(branch_env.steps)
    if tracker is not None:
        # Read the env's own clocks -- never assert against the module
        # constants alone -- and check that [start_step, end_step) never
        # crosses a fast_block or slow_block boundary, mirroring `_targets`'
        # own arithmetic exactly rather than re-deriving it from K0/WINDOW.
        branch_k0 = int(branch_env.k0)
        branch_slow_period_blocks = int(branch_env.slow_period_blocks)
        last_step_in_window = end_step - 1
        slow_period = branch_k0 * branch_slow_period_blocks
        no_crossed = (
            branch_k0 == K0
            and (end_step - start_step == WINDOW)
            and (start_step // branch_k0) == (last_step_in_window // branch_k0)
            and (start_step // slow_period) == (last_step_in_window // slow_period)
        )
        tracker.mark(
            "no_check_crossed_within_window",
            no_crossed,
            f"window [{start_step},{end_step}) crosses a fast_block or slow_block "
            f"boundary (env k0={branch_k0}, slow_period_blocks={branch_slow_period_blocks})",
        )
    return float(sum(rewards)), rewards


def r10(x) -> float:
    return round(float(x), 10)


def pair_dict(pair: tuple[int, int]) -> dict:
    return {"agent_0": int(pair[0]), "agent_1": int(pair[1])}


# --- exhaustive incumbent-conditional oracle (importable API; A-VK-D10) ------
#
# The single source of truth for the 16-edit legal enumeration and the
# per-focal V_K/V_S/U_src reduction. `run_track` below calls these for the
# panel; V-K0B's `audit_vk0b_r30_access.py` calls `compute_u_src` on each
# natural check's ACTUAL incumbent pair (never the panel's optimal track).
# Extracted from the panel builder verbatim -- the panel's own end-to-end
# determinism test (`tests/audit_vk0a_oracle_test.py`) still exercises this
# code path and pins that the refactor changed nothing about panel output.

def compute_incumbent_edit_results(
    env: TwoTimescaleRoleFreeActionsEnv,
    incumbent: tuple[int, int],
    action_table: np.ndarray,
    table_hash: str,
    tracker: ValidityTracker | None = None,
    check_index: int | None = None,
) -> dict[tuple[int, int], dict]:
    """Exhaustive enumeration of the 16 legal joint KEEP/SET edits at `env`'s
    current check state, given the ACTUAL incumbent pair. `env` itself is
    never mutated (each edit is evaluated on an internal deep copy by
    `evaluate_window`). Raises `SourceAuditInvalid` on any enumeration
    corruption, tracker or not -- fail-closed is not a V-K0A-only property."""
    opts0 = legal_options(incumbent[0])
    opts1 = legal_options(incumbent[1])
    enum_ok = check_enumeration_exact(opts0) and check_enumeration_exact(opts1)
    label_ok = check_no_same_label_set(opts0, incumbent[0]) and check_no_same_label_set(
        opts1, incumbent[1]
    )
    edits = [(o0, o1) for o0 in opts0 for o1 in opts1]
    result_pairs = {(o0[1], o1[1]) for o0, o1 in edits}
    cross_ok = len(edits) == 16 and len(result_pairs) == 16
    if tracker is not None:
        tracker.mark(
            "legal_edit_enumeration_exact",
            enum_ok and cross_ok,
            f"legal option enumeration corrupted at check {check_index}",
        )
        tracker.mark(
            "same_label_set_excluded",
            label_ok,
            f"same-label SET admitted at check {check_index}",
        )
    if not (enum_ok and label_ok and cross_ok):
        raise SourceAuditInvalid(
            f"legal edit enumeration corrupted at check {check_index}: "
            f"enum_ok={enum_ok} label_ok={label_ok} cross_ok={cross_ok}"
        )

    # B1: ONE reference fingerprint, captured before any of the 16 branches
    # runs. Every branch's deepcopy-time fingerprint is compared against
    # this same reference inside `evaluate_window`, and `env` itself is
    # re-compared against it again below once every branch has finished --
    # never a same-call recomputation, which could never disagree with its
    # own deepcopy.
    ref_fp = fingerprint(env)

    results_by_pair: dict[tuple[int, int], dict] = {}
    for (o0, o1) in edits:
        pair = (o0[1], o1[1])
        total, five = evaluate_window(
            env, pair[0], pair[1], action_table, table_hash, tracker, ref_fp
        )
        results_by_pair[pair] = {
            "total_return": total,
            "five_step_rewards": five,
            "kind0": o0[0],
            "kind1": o1[0],
        }

    if tracker is not None:
        post_loop_fp = fingerprint(env)
        tracker.mark(
            "identical_initial_state_across_branches",
            post_loop_fp == ref_fp,
            f"source_env fingerprint diverged after the 16-edit loop at check "
            f"{check_index}: {post_loop_fp} != reference {ref_fp}",
        )

    exhausted_ok = len(results_by_pair) == 16
    if tracker is not None:
        tracker.mark(
            "full_action_support_maximization_exhausted",
            exhausted_ok,
            f"only {len(results_by_pair)}/16 joint edits were evaluated at check {check_index}",
        )
    if not exhausted_ok:
        raise SourceAuditInvalid(
            f"only {len(results_by_pair)}/16 joint edits were evaluated at check {check_index}"
        )
    return results_by_pair


def compute_focal_u_src(
    results_by_pair: dict[tuple[int, int], dict],
    focal: int,
    tracker: ValidityTracker | None = None,
    check_index: int | None = None,
) -> dict:
    """Per-focal V_K / V_S / U_src / urgency_class from an exhaustive 16-edit
    `results_by_pair` (see `compute_incumbent_edit_results`)."""
    keep_pairs = [
        p for p, info in results_by_pair.items()
        if (info["kind0"] if focal == 0 else info["kind1"]) == "KEEP"
    ]
    set_pairs = [
        p for p, info in results_by_pair.items()
        if (info["kind0"] if focal == 0 else info["kind1"]) == "SET"
    ]
    branch_ok = len(keep_pairs) == 4 and len(set_pairs) == 12
    if tracker is not None:
        tracker.mark(
            "full_action_support_maximization_exhausted",
            branch_ok,
            f"focal={focal} KEEP/SET branch sizes wrong at check {check_index}",
        )
    if not branch_ok:
        raise SourceAuditInvalid(
            f"focal={focal} KEEP/SET branch sizes wrong at check {check_index}"
        )
    v_k = max(results_by_pair[p]["total_return"] for p in keep_pairs)
    v_s = max(results_by_pair[p]["total_return"] for p in set_pairs)
    u_src = max(0.0, v_s - v_k)
    argmax_k = [p for p in keep_pairs if results_by_pair[p]["total_return"] == v_k]
    argmax_s = [p for p in set_pairs if results_by_pair[p]["total_return"] == v_s]
    if u_src > MATERIALITY:
        urgency_class = "URGENT"
    elif u_src < MATERIALITY:
        urgency_class = "STABLE"
    else:
        urgency_class = "BOUNDARY"
    return {
        "V_K": v_k,
        "V_S": v_s,
        "U_src": u_src,
        "urgency_class": urgency_class,
        "argmax_K": argmax_k,
        "argmax_S": argmax_s,
        "tie_K": len(argmax_k) > 1,
        "tie_S": len(argmax_s) > 1,
    }


def compute_u_src(
    env: TwoTimescaleRoleFreeActionsEnv,
    incumbent: tuple[int, int],
    action_table: np.ndarray,
    table_hash: str,
) -> dict[int, dict]:
    """A-VK-D10: the exhaustive V-K0A oracle invoked on a check's ACTUAL
    pre-decision incumbent pair. For external callers (V-K0B) that must
    classify urgency from the real incumbent -- never from physical phase,
    skill axis, fast/stable labels, or the V-K0A oracle-optimal track.
    No tracker: a corrupted enumeration still raises `SourceAuditInvalid`
    (fail-closed); only V-K0A's own named-predicate bookkeeping is a caller
    responsibility. `env` is not mutated. Returns `{0: {...}, 1: {...}}`,
    each value the dict `compute_focal_u_src` returns."""
    results_by_pair = compute_incumbent_edit_results(env, incumbent, action_table, table_hash)
    return {focal: compute_focal_u_src(results_by_pair, focal) for focal in (0, 1)}


# --- one (sign combo, track) trajectory -------------------------------------

def run_track(
    config,
    seed: int,
    sign_combo: tuple[int, int],
    track: int,
    action_table: np.ndarray,
    table_hash: str,
    tracker: ValidityTracker,
) -> tuple[list[dict], dict, list[tuple]]:
    env = TwoTimescaleRoleFreeActionsEnv(config=config)
    env.reset(seed=seed)

    rows: list[dict] = []
    initial_meta: dict | None = None
    check_fps: list[tuple] = []
    incumbent: tuple[int, int] | None = None

    for check_index in range(TOTAL_CHECKS):
        step = check_index * K0
        if int(env.steps) != step:
            raise RuntimeError(
                f"check clock drift: expected step {step}, env.steps={env.steps}"
            )
        check_fps.append(fingerprint(env))

        if check_index == 0:
            candidates = [
                (s0, s1)
                for s0 in duty_allowed_skills(0, track)
                for s1 in duty_allowed_skills(1, track)
            ]
            results = []
            ref_fp = fingerprint(env)  # B1: one reference before the branch loop
            for (s0, s1) in candidates:
                total, _ = evaluate_window(
                    env, s0, s1, action_table, table_hash, tracker, ref_fp
                )
                results.append({"pair": (s0, s1), "total_return": total})
            if tracker is not None:
                post_loop_fp = fingerprint(env)
                tracker.mark(
                    "identical_initial_state_across_branches",
                    post_loop_fp == ref_fp,
                    f"source_env fingerprint diverged after the initial-check "
                    f"branch loop: {post_loop_fp} != reference {ref_fp}",
                )
            max_total = max(r["total_return"] for r in results)
            tied = [r["pair"] for r in results if r["total_return"] == max_total]
            chosen = min(tied, key=lambda p: canonical_tuple(track, p[0], p[1]))
            initial_meta = {
                "sign_combo": {"slow": sign_combo[0], "fast": sign_combo[1]},
                "seed": int(seed),
                "assignment_permutation": int(track),
                "check_index": 0,
                "primitive_step": 0,
                "candidates": [
                    {"pair": pair_dict(r["pair"]), "total_return": r10(r["total_return"])}
                    for r in results
                ],
                "chosen_pair": pair_dict(chosen),
                "tie": len(tied) > 1,
            }
            incumbent = chosen
        else:
            # Fail fast, named, before any downstream max() can be handed a
            # mis-keyed or accidentally empty candidate set (A-VK-D3: a
            # detected corruption invalidates, it is never silently dropped
            # and it must never surface as an unrelated crash instead) --
            # enforced inside `compute_incumbent_edit_results` itself.
            results_by_pair = compute_incumbent_edit_results(
                env, incumbent, action_table, table_hash, tracker, check_index
            )

            # Incumbent-advancement tie: computed here (before the rows for
            # this check are built) so the row payload can carry it, exactly
            # like the initial check's own "tie" flag already does. This is
            # a distinct tie from tie_K/tie_S (those are per-focal KEEP/SET
            # argmax ties inside `compute_focal_u_src`); this one is about
            # which duty-axis-restricted pair the trajectory itself advances
            # to next.
            allowed0 = duty_allowed_skills(0, track)
            allowed1 = duty_allowed_skills(1, track)
            restricted = {
                p: v["total_return"]
                for p, v in results_by_pair.items()
                if p[0] in allowed0 and p[1] in allowed1
            }
            max_r = max(restricted.values())
            tied_r = [p for p, v in restricted.items() if v == max_r]
            tie_incumbent_advance = len(tied_r) > 1
            chosen = min(tied_r, key=lambda p: canonical_tuple(track, p[0], p[1]))

            for focal in (0, 1):
                focal_result = compute_focal_u_src(results_by_pair, focal, tracker, check_index)
                rows.append(
                    {
                        "sign_combo": {"slow": sign_combo[0], "fast": sign_combo[1]},
                        "seed": int(seed),
                        "assignment_permutation": int(track),
                        "check_index": int(check_index),
                        "primitive_step": int(step),
                        "focal_slot": int(focal),
                        "incumbent_pair": pair_dict(incumbent),
                        "V_K": r10(focal_result["V_K"]),
                        "V_S": r10(focal_result["V_S"]),
                        "U_src": r10(focal_result["U_src"]),
                        "urgency_class": focal_result["urgency_class"],
                        "argmax_K": [pair_dict(p) for p in focal_result["argmax_K"]],
                        "argmax_S": [pair_dict(p) for p in focal_result["argmax_S"]],
                        "tie_K": focal_result["tie_K"],
                        "tie_S": focal_result["tie_S"],
                        "tie_incumbent_advance": tie_incumbent_advance,
                    }
                )

            incumbent = chosen

        action0 = action_table[int(incumbent[0])]
        action1 = action_table[int(incumbent[1])]
        for _ in range(WINDOW):
            env.step({"agent_0": action0, "agent_1": action1})

    assert initial_meta is not None
    return rows, initial_meta, check_fps


# --- acceptance --------------------------------------------------------------

def evaluate_acceptance(rows: list[dict]) -> tuple[bool, dict]:
    by_group: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row["sign_combo"]["slow"], row["sign_combo"]["fast"], row["assignment_permutation"], row["check_index"])
        by_group.setdefault(key, []).append(row)

    fast_only_ok = True
    joint_ok = True
    for key, group in by_group.items():
        check_index = key[3]
        classes = sorted(r["urgency_class"] for r in group)
        if check_index in FAST_ONLY_CHECK_INDICES:
            if classes != ["STABLE", "URGENT"]:
                fast_only_ok = False
        elif check_index == JOINT_CHECK_INDEX:
            if classes != ["URGENT", "URGENT"]:
                joint_ok = False

    by_combo_check: dict[tuple, dict[int, list[dict]]] = {}
    for row in rows:
        combo_key = (row["sign_combo"]["slow"], row["sign_combo"]["fast"], row["check_index"])
        by_combo_check.setdefault(combo_key, {}).setdefault(row["assignment_permutation"], []).append(row)
    tracks_agree = True
    for combo_key, per_track in by_combo_check.items():
        if 0 not in per_track or 1 not in per_track:
            tracks_agree = False
            continue
        values0 = sorted(r["U_src"] for r in per_track[0])
        values1 = sorted(r["U_src"] for r in per_track[1])
        if len(values0) != len(values1) or any(
            abs(a - b) > 1e-9 for a, b in zip(values0, values1)
        ):
            tracks_agree = False

    slot_both_classes = True
    for slot in (0, 1):
        urgent_seen = any(r["focal_slot"] == slot and r["urgency_class"] == "URGENT" for r in rows)
        stable_seen = any(r["focal_slot"] == slot and r["urgency_class"] == "STABLE" for r in rows)
        if not (urgent_seen and stable_seen):
            slot_both_classes = False

    no_boundary = all(r["urgency_class"] != "BOUNDARY" for r in rows)

    detail = {
        "fast_only_one_urgent_one_stable": fast_only_ok,
        "joint_check_both_urgent": joint_ok,
        "tracks_agree_unordered_values": tracks_agree,
        "each_slot_in_both_classes": slot_both_classes,
        "no_boundary_row": no_boundary,
    }
    return all(detail.values()), detail


def check_cross_track_relabel(
    all_check_fps: dict[tuple, list[tuple]], tracker: ValidityTracker
) -> None:
    """Cross-track source-state comparison. Not the named A-VK-D2 / validity
    (7) check (see `check_cross_track_incumbent_urgency_mirror` below for
    that) but kept as an additional signal into the same predicate -- it has
    caught real corruption before. For every sign combo the two tracks'
    actual trajectory env fingerprints (target signs and current step, at
    every check boundary) must be identical -- track choice only decides
    which physical agent does which duty, never the environment's own
    dynamics."""
    combos = {key[:2] for key in all_check_fps}
    for combo in combos:
        fp0 = all_check_fps.get((*combo, 0))
        fp1 = all_check_fps.get((*combo, 1))
        ok = fp0 is not None and fp1 is not None and fp0 == fp1
        tracker.mark(
            "permutation_relabels_only",
            ok,
            f"sign combo {combo}: track0 check states {fp0} != track1 {fp1}",
        )


def check_cross_track_incumbent_urgency_mirror(
    rows: list[dict], tracker: ValidityTracker
) -> None:
    """A-VK-D2 / validity (7), the anonymity check the ruling names:
    permutation must only relabel which physical agent holds which duty, it
    must never alter what the source contains. For every (sign combo,
    noninitial check): (a) track 1's incumbent pair must be the exact
    slot-swap of track 0's incumbent pair (agent_0<->agent_1), and (b) the
    urgency_class experienced by each *canonical duty* -- the slow-duty
    agent and the fast-duty agent, not each raw agent_slot -- must coincide
    across the two tracks. Either failing means the two tracks disagree
    about something a relabelling can never change."""
    by_key: dict[tuple, dict[int, dict[int, dict]]] = {}
    for row in rows:
        combo = (row["sign_combo"]["slow"], row["sign_combo"]["fast"])
        key = (*combo, row["check_index"])
        by_key.setdefault(key, {}).setdefault(row["assignment_permutation"], {})[
            row["focal_slot"]
        ] = row

    for key, per_track in by_key.items():
        if (
            0 not in per_track
            or 1 not in per_track
            or not {0, 1}.issubset(per_track[0])
            or not {0, 1}.issubset(per_track[1])
        ):
            tracker.mark(
                "permutation_relabels_only",
                False,
                f"{key}: missing track/focal-slot rows for the incumbent/urgency "
                "mirror check",
            )
            continue

        rows0, rows1 = per_track[0], per_track[1]
        incumbent0 = rows0[0]["incumbent_pair"]
        incumbent1 = rows1[0]["incumbent_pair"]
        swap_ok = (
            rows0[1]["incumbent_pair"] == incumbent0
            and rows1[1]["incumbent_pair"] == incumbent1
            and incumbent1
            == {"agent_0": incumbent0["agent_1"], "agent_1": incumbent0["agent_0"]}
        )
        tracker.mark(
            "permutation_relabels_only",
            swap_ok,
            f"{key}: track1 incumbent {incumbent1} is not the slot-swap of "
            f"track0 incumbent {incumbent0}",
        )

        urgency_ok = (
            rows0[0]["urgency_class"] == rows1[1]["urgency_class"]
            and rows0[1]["urgency_class"] == rows1[0]["urgency_class"]
        )
        tracker.mark(
            "permutation_relabels_only",
            urgency_ok,
            f"{key}: canonical-duty urgency classes diverge across tracks "
            f"(track0 slots=[{rows0[0]['urgency_class']},{rows0[1]['urgency_class']}], "
            f"track1 slots=[{rows1[0]['urgency_class']},{rows1[1]['urgency_class']}])",
        )


# --- artifact binding (B4) -------------------------------------------------

FROZEN_ENV_PREMISES = {
    "k0": K0,
    "total_checks": TOTAL_CHECKS,
    "window": WINDOW,
    "joint_check_index": JOINT_CHECK_INDEX,
    "max_steps": 40,
    "slow_period_blocks": 6,
}


def resolve_and_assert_env_premises(config, config_module_name: str) -> dict:
    """Bind the panel to the config that actually produced it, and fail hard
    -- before any window is evaluated -- if that config's own clocks do not
    match the frozen premises this oracle's whole 112-row panel construction
    and acceptance logic assume: K0=5, 8 total checks, a one-k0-wide window,
    the joint check at index 6, horizon 40, slow_period_blocks=6. This last
    one is not cosmetic: slow_period_blocks is the clock that determines
    where JOINT_CHECK_INDEX=6 (step 30) actually falls -- with
    slow_period_blocks=3 the true joint fast+slow transitions land at checks
    3 AND 6, not just 6, so a drifted slow_period_blocks silently passes a
    stale JOINT_CHECK_INDEX and produces a scientifically wrong
    NOT_IDENTIFIED verdict instead of aborting. This is a construction-time
    contract check, not a validity predicate: a mismatch means the run
    cannot mean what the oracle claims it means, so it must never produce an
    artifact at all (raise `SourceAuditInvalid` uncaught here, not the
    caught-and-reported INVALID_VERDICT path used once the panel is under
    way)."""
    probe_env = TwoTimescaleRoleFreeActionsEnv(config=config)
    resolved = {
        "config_module": config_module_name,
        "k0": int(probe_env.k0),
        "slow_period_blocks": int(probe_env.slow_period_blocks),
        "max_steps": int(probe_env.max_steps),
    }
    mismatches = []
    if resolved["k0"] != FROZEN_ENV_PREMISES["k0"]:
        mismatches.append(f"k0={resolved['k0']} != frozen {FROZEN_ENV_PREMISES['k0']}")
    if resolved["slow_period_blocks"] != FROZEN_ENV_PREMISES["slow_period_blocks"]:
        mismatches.append(
            f"slow_period_blocks={resolved['slow_period_blocks']} != frozen "
            f"{FROZEN_ENV_PREMISES['slow_period_blocks']}"
        )
    if resolved["max_steps"] != FROZEN_ENV_PREMISES["max_steps"]:
        mismatches.append(
            f"max_steps={resolved['max_steps']} != frozen {FROZEN_ENV_PREMISES['max_steps']}"
        )
    if TOTAL_CHECKS != FROZEN_ENV_PREMISES["total_checks"]:
        mismatches.append(
            f"TOTAL_CHECKS={TOTAL_CHECKS} != frozen {FROZEN_ENV_PREMISES['total_checks']}"
        )
    if WINDOW != FROZEN_ENV_PREMISES["window"]:
        mismatches.append(f"WINDOW={WINDOW} != frozen {FROZEN_ENV_PREMISES['window']}")
    if JOINT_CHECK_INDEX != FROZEN_ENV_PREMISES["joint_check_index"]:
        mismatches.append(
            f"JOINT_CHECK_INDEX={JOINT_CHECK_INDEX} != frozen "
            f"{FROZEN_ENV_PREMISES['joint_check_index']}"
        )
    if mismatches:
        raise SourceAuditInvalid(
            "config/module premises do not match the oracle's frozen assumptions: "
            + "; ".join(mismatches)
        )
    return resolved


# --- artifact ------------------------------------------------------------

def build_panel(config) -> dict:
    torch.set_num_threads(1)

    # B4: hard error, before any window is evaluated, if this config's own
    # clocks do not match the premises the whole panel construction assumes.
    config_module_name = type(config).__module__
    env_premises = resolve_and_assert_env_premises(config, config_module_name)

    policy = FixedSkillPrimitivePolicy(4, 2, "continuous")
    action_table = policy.action_table.detach().cpu().numpy().astype(np.float64)
    table_hash = hashlib.sha256(np.ascontiguousarray(action_table).tobytes()).hexdigest()

    seed_map = scan_sign_combinations(config)
    combos = list(itertools.product((-1, 1), (-1, 1)))

    tracker = ValidityTracker()
    all_rows: list[dict] = []
    initial_rows: list[dict] = []
    all_check_fps: dict[tuple, list[tuple]] = {}

    aborted_reason: str | None = None
    try:
        for combo in combos:
            seed = seed_map[combo]
            for track in (0, 1):
                rows, initial_meta, check_fps = run_track(
                    config, seed, combo, track, action_table, table_hash, tracker
                )
                all_rows.extend(rows)
                initial_rows.append(initial_meta)
                all_check_fps[(combo[0], combo[1], track)] = check_fps
        check_cross_track_relabel(all_check_fps, tracker)
        check_cross_track_incumbent_urgency_mirror(all_rows, tracker)
    except SourceAuditInvalid as exc:
        aborted_reason = str(exc)
        tracker.violations.append(f"aborted: {aborted_reason}")

    validity_passed = tracker.all_passed() and aborted_reason is None
    if validity_passed:
        acceptance_passed, acceptance_detail = evaluate_acceptance(all_rows)
        verdict = VALID_VERDICT if acceptance_passed else NOT_IDENTIFIED_VERDICT
    else:
        acceptance_detail = {}
        verdict = INVALID_VERDICT

    artifact = {
        "contract_id": CONTRACT_ID,
        "panel_schema_version": PANEL_SCHEMA_VERSION,
        "stage_commit": stage_commit(),
        "environment_blob_sha": blob_sha(ENV_FILE),
        "env_premises": env_premises,
        "action_table_hash": table_hash,
        "oracle_script_hash": blob_sha(ORACLE_FILE),
        "seed_to_sign_map": [
            {"seed": int(seed_map[c]), "slow_sign": int(c[0]), "fast_sign": int(c[1])}
            for c in combos
        ],
        "row_count": len(all_rows),
        "validity": {**tracker.results, "all_passed": validity_passed, "violations": tracker.violations},
        "acceptance": acceptance_detail,
        "rows": all_rows,
        "initial_check_metadata": initial_rows,
        "verdict": verdict,
    }
    return artifact


def write_artifact(artifact: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    panel_path = out_dir / "source_oracle_panel.json"
    payload = json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2)
    panel_path.write_bytes(payload.encode("utf-8"))
    digest = hashlib.sha256(panel_path.read_bytes()).hexdigest()
    sidecar_path = out_dir / "source_oracle_panel.sha256"
    sidecar_path.write_text(digest, encoding="utf-8")
    return panel_path, sidecar_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--config", default="config_d7_2b_toy_learned_keep")
    args = parser.parse_args()

    config = importlib.import_module(args.config).Config()
    artifact = build_panel(config)
    panel_path, sidecar_path = write_artifact(artifact, Path(args.out))

    print(f"VK0A_VERDICT={artifact['verdict']}")
    print(f"VK0A_ROW_COUNT={artifact['row_count']}")
    print(f"VK0A_VALIDITY_ALL_PASSED={artifact['validity']['all_passed']}")
    print(f"VK0A_PANEL={panel_path}")
    print(f"VK0A_SIDECAR_SHA256={sidecar_path.read_text(encoding='utf-8')}")


if __name__ == "__main__":
    main()
