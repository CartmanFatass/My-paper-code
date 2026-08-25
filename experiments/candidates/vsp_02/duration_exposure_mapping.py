"""Zero-training interface proof: does a selected duration map to real exposure?

External Pro, ruling ``SKILL_LIFETIME_TWO_DISTINCT_CAPABILITIES``, refused to
authorize a build and named this proof as one of two preconditions:

    First establish MSSR's support-native P reachability and VSP-02's real
    duration-exposure mapping as separate zero-training interface proofs.

It also stated the two gaps it expected this proof to find:

    active_gap_remaining is currently sampled exogenously after the skill
    action. It is not an owner-selected duration.

    OpenEventTrace is attached to the current LifecycleRecord, and an
    ordinary/leave/terminal boundary closes it directly. It is not yet the
    detached claim -> close -> cutoff -> release object required by VSP-02.

This module verifies both **functionally** rather than by reading the source,
because the question is a causal one -- does the owner's action determine the
duration? -- and only an intervention answers that.

THE TWO INTERVENTIONS
---------------------
1. *Hold the RNG fixed, vary the action.*  If the realized gap is unchanged,
   the duration is not selected by the owner.
2. *Hold the action fixed, vary the opportunity RNG.*  If the realized gap
   changes, the duration is exogenous.

Together these establish ``gap ⊥ action`` and ``gap ~ RNG``: the runtime has a
duration-like quantity, but nothing selects it.

A third check compares the runtime's registered boundary vocabulary against the
escrow lifecycle the accepted VSP-02 oracle requires.

Zero training, no mutation of any shared object, and a precise absence map is a
valid outcome.
"""

from __future__ import annotations

import importlib.util
import pathlib
from dataclasses import dataclass

RAW_OUTPUT_BINDING = "vsp_02.duration_exposure_mapping.v1"


def _repository_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def _load_core_helpers():
    """Reuse the runtime's own test factory rather than rebuilding a core."""
    path = (
        _repository_root()
        / "tests"
        / "process"
        / "variable_roster"
        / "ha_ctse_process_variable_roster_event_test.py"
    )
    spec = importlib.util.spec_from_file_location("_vsp02_vre_helpers", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


def _realized_gaps(*, opportunity_seed: int, actions: dict[str, int]) -> dict[str, int]:
    helpers = _load_core_helpers()
    core = helpers.make_core(opportunity_seed=opportunity_seed)
    keys = tuple(actions)
    helpers.initial_join(core, keys=keys, order=keys, actions=actions)
    return {
        row.owner_lifecycle_key: int(row.sampled_replacement_gap)
        for row in core.high_ledger
    }


def duration_is_owner_selected() -> CheckResult:
    """Intervention 1: hold the RNG fixed and vary the action."""
    # Both action assignments lie inside the registered support (n_skills = 3).
    low = _realized_gaps(opportunity_seed=142, actions={"a": 0, "b": 1})
    high = _realized_gaps(opportunity_seed=142, actions={"a": 2, "b": 0})
    responds = low != high
    return CheckResult(
        name="duration_is_owner_selected",
        passed=responds,
        detail=(
            f"same opportunity RNG, different skill actions -> gaps {low} vs "
            f"{high}; the realized duration "
            + ("responds to" if responds else "is independent of")
            + " the owner's action"
        ),
    )


def duration_is_exogenous() -> CheckResult:
    """Intervention 2: hold the action fixed and vary the opportunity RNG."""
    first = _realized_gaps(opportunity_seed=142, actions={"a": 0, "b": 1})
    second = _realized_gaps(opportunity_seed=997, actions={"a": 0, "b": 1})
    driven_by_rng = first != second
    return CheckResult(
        name="duration_is_exogenous",
        # This check "passes" when the duration is NOT exogenous.
        passed=not driven_by_rng,
        detail=(
            f"same action, different opportunity RNG -> gaps {first} vs "
            f"{second}; the realized duration is "
            + ("drawn from the RNG" if driven_by_rng else "RNG-independent")
        ),
    )


def escrow_lifecycle_present() -> CheckResult:
    """Does the runtime implement claim -> close -> cutoff -> release?"""
    from ha_ctse_process import variable_roster_event_support as support

    from experiments.candidates.vsp_02 import duration_escrow_oracle as oracle

    runtime_kinds = tuple(support.BOUNDARY_KINDS)
    required_events = tuple(event.value for event in oracle.Event)
    required_states = tuple(state.value for state in oracle.State)

    # The oracle's escrow needs a RELEASE step distinct from the close, and a
    # cutoff distinct from both.  Look for any runtime vocabulary carrying them.
    missing = tuple(
        name
        for name in ("CLAIM", "RELEASE", "TERMINAL_HORIZON")
        if not any(name in kind.upper() for kind in runtime_kinds)
    )
    return CheckResult(
        name="escrow_lifecycle_present",
        passed=not missing,
        detail=(
            f"runtime boundary kinds = {runtime_kinds}; oracle requires "
            f"{len(required_states)} states and {len(required_events)} events; "
            f"absent from the runtime vocabulary = {missing}"
        ),
    )


def proof() -> dict[str, object]:
    checks = (
        duration_is_owner_selected(),
        duration_is_exogenous(),
        escrow_lifecycle_present(),
    )
    mapped = all(check.passed for check in checks)
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "checks": {
            check.name: {"passed": check.passed, "detail": check.detail}
            for check in checks
        },
        "terminal": (
            "VSP02_DURATION_EXPOSURE_MAPPED"
            if mapped
            else "VSP02_DURATION_EXPOSURE_ABSENT"
        ),
        "scope": (
            "Zero-training interface proof. Establishes object existence only; "
            "it licenses no scientific claim about VSP-02 and no build."
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(proof(), indent=2))
