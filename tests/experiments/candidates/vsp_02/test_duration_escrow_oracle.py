from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from dataclasses import fields, replace
from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest

from experiments.candidates.vsp_02 import duration_escrow_oracle as oracle


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "experiments/candidates/vsp_02/duration_escrow_oracle.py"
INDEX = ROOT / "docs/research/candidates/vsp_02/CODE_SCIENCE_INDEX.md"


@pytest.fixture(scope="module")
def audit() -> oracle.OracleAudit:
    return oracle.run_oracle()


def _valid_pair(audit: oracle.OracleAudit, spec: oracle.CaseSpec):
    key = (
        spec.world, spec.context, spec.close_mode, spec.cutoff, spec.owner_departure
    )
    return [
        case for case in audit.cases
        if case.valid and (
            case.spec.world, case.spec.context, case.spec.close_mode,
            case.spec.cutoff, case.spec.owner_departure,
        ) == key
    ]


def _nested(case, collection, **changes):
    records = list(getattr(case, collection))
    records[0] = replace(records[0], **changes)
    return replace(case, **{collection: tuple(records)})


def _expected_rewards(spec):
    r0 = Fraction(1, 2) if spec.context is oracle.Context.F else Fraction(3, 2)
    r1 = Fraction(1)
    if spec.close_mode is oracle.CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL:
        r0, r1 = r0 + Fraction(1, 32), r1 + Fraction(1, 16)
    if spec.owner_departure:
        r0, r1 = r0 + Fraction(1, 64), r1 + Fraction(1, 32)
    if spec.cutoff is oracle.Cutoff.SIMULTANEOUS_TERMINAL_HORIZON:
        r0, r1 = r0 + Fraction(1, 16), r1 + Fraction(1, 8)
    else:
        r0 -= Fraction(1, 8)
    if spec.world is oracle.World.POSITIVE and spec.action is oracle.Action.LONG:
        if spec.context is oracle.Context.F:
            r0, r1 = r0 - Fraction(1, 8), r1 - Fraction(1, 4)
        else:
            r0, r1 = r0 + Fraction(1, 16), r1 + Fraction(1, 8)
    return r0, r1


def _mutation_case(audit):
    return next(
        case for case in audit.cases
        if case.valid and case.spec.world is oracle.World.POSITIVE
        and case.spec.context is oracle.Context.F
        and case.spec.action is oracle.Action.LONG
        and case.spec.close_mode is oracle.CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL
        and case.spec.cutoff is oracle.Cutoff.SIMULTANEOUS_TERMINAL_HORIZON
        and case.spec.owner_departure
    )


def test_exact_128_factorization_and_literal_total_transducer(audit):
    assert len(audit.cases) == 128
    counts = Counter((case.spec.world, case.spec.behavior_version) for case in audit.cases)
    assert counts == {
        (world, version): 32
        for world in oracle.World
        for version in (oracle.CURRENT_VERSION, oracle.CURRENT_VERSION - 1)
    }
    observed = {
        (
            case.spec.world, case.spec.context, case.spec.action,
            case.spec.close_mode, case.spec.cutoff, case.spec.owner_departure,
            case.spec.behavior_version,
        )
        for case in audit.cases
    }
    expected = set(product(
        oracle.World, oracle.Context, oracle.Action, oracle.CloseMode,
        oracle.Cutoff, (False, True),
        (oracle.CURRENT_VERSION, oracle.CURRENT_VERSION - 1),
    ))
    assert observed == expected
    assert {state.value for state in oracle.State} == {
        "VACANT", "OPEN_ACTIVE", "OPEN_NATURAL", "OPEN_INTERRUPTED",
        "TERMINAL_READY", "HORIZON_READY", "RELEASED", "INVALID",
    }
    assert all(
        isinstance(oracle.transition(state, event), oracle.State)
        for state, event in product(oracle.State, oracle.Event)
    )


def test_valid_lifecycle_schemas_clocks_tapes_and_owner_departure(audit):
    valid = [case for case in audit.cases if case.valid]
    stale = [case for case in audit.cases if not case.valid]
    assert len(valid) == len(stale) == 64
    assert all(
        len(case.events) == 4
        and len(case.scores) == len(case.releases) == len(case.tombstones) == 1
        and case.final_state is oracle.State.RELEASED
        for case in valid
    )
    assert all(
        case.final_state is oracle.State.INVALID
        and not case.scores and not case.releases
        and len(case.tombstones) == 1
        for case in stale
    )
    assert [field.name for field in fields(oracle.DecisionIdentity)] == [
        "episode_id", "source_owner_epoch", "own_boundary_index", "behavior_version"
    ]
    assert all(
        event.policy_clock == case.identity.own_boundary_index
        and event.environment_clock >= 100
        for case in valid for event in case.events
    )
    assert all(case.physical.primitive_tape is oracle.PRIMITIVE_TAPE for case in valid)
    assert all(case.physical.partner_tape is oracle.PARTNER_TAPE for case in valid)
    departed = [case for case in valid if case.spec.owner_departure]
    assert all(
        case.identity.source_owner_epoch == 7 and case.physical.final_owner_epoch == 8
        for case in departed
    )
    assert audit.report["timing_tensor"] == {
        "axes": ["world", "context", "action", "close", "cutoff", "owner_departure"],
        "shape": [2, 2, 2, 2, 2, 2], "entries": 64,
        "tau_values": [100, 104], "frozen": True,
    }


def test_absolute_target_deltas_raw_scores_and_w0_physical_equality(audit):
    valid = [case for case in audit.cases if case.valid]
    assert all(case.target == oracle.absolute_target(case.physical) for case in valid)
    expected_delta = {
        (oracle.World.POSITIVE, oracle.Context.F): -oracle.GAMMA / 2,
        (oracle.World.POSITIVE, oracle.Context.P): oracle.GAMMA / 4,
        (oracle.World.ZERO, oracle.Context.F): Fraction(0),
        (oracle.World.ZERO, oracle.Context.P): Fraction(0),
    }
    for case in valid:
        if case.spec.action is not oracle.Action.SHORT:
            continue
        short, long = sorted(
            _valid_pair(audit, case.spec), key=lambda item: item.spec.action.value, reverse=True
        )
        assert short.spec.action is oracle.Action.SHORT
        assert long.spec.action is oracle.Action.LONG
        delta = long.target - short.target
        assert delta == expected_delta[(case.spec.world, case.spec.context)]
        p = Fraction(1, 4) if case.spec.context is oracle.Context.F else Fraction(3, 4)
        mu = Fraction(2, 5) if case.spec.context is oracle.Context.F else Fraction(3, 5)
        raw = mu * ((1 - p) * short.scores[0].score + p * long.scores[0].score)
        assert raw == mu * p * (1 - p) * delta
        if case.spec.world is oracle.World.ZERO:
            assert short.physical == long.physical
            assert raw == 0
    assert audit.report["deltas"] == {
        "W+|F": "-1/4", "W+|P": "1/8", "W0|F": "0", "W0|P": "0", "psi": "3/8"
    }


def test_explicit_physical_rewards_are_independent_and_two_step(audit):
    assert not hasattr(oracle, "_desired_target")
    valid = [case for case in audit.cases if case.valid]
    assert all(case.physical.rewards == _expected_rewards(case.spec) for case in valid)
    assert all(case.physical.rewards[1] != 0 for case in valid)
    assert all(case.target == oracle.absolute_target(case.physical) for case in valid)
    horizon = next(case for case in valid if case.spec.cutoff is oracle.Cutoff.HORIZON)
    terminal = next(
        case for case in valid
        if case.spec.cutoff is oracle.Cutoff.SIMULTANEOUS_TERMINAL_HORIZON
    )
    assert oracle.GAMMA**2 * horizon.physical.vbar == Fraction(1, 8)
    assert terminal.physical.terminal_time == terminal.physical.tau + oracle.HORIZON
    assert audit.report["invariants"]["explicit_nonzero_second_reward_kernel"] is True


def test_aggregate_invariants_fail_closed(monkeypatch):
    wrong = dict(oracle.EXPECTED_DELTAS)
    wrong[(oracle.World.POSITIVE, oracle.Context.F)] = Fraction(0)
    monkeypatch.setattr(oracle, "EXPECTED_DELTAS", wrong)
    with pytest.raises(ValueError, match="frozen_deltas_exact"):
        oracle.run_oracle()


def test_simultaneous_priorities_and_ambiguous_illegal_mutations(audit):
    assert oracle.resolve_close(natural=True, interrupt=True) is oracle.Event.INTERRUPT_NATURAL
    assert oracle.resolve_cutoff(horizon=True, terminal=True) is oracle.Event.TERMINAL_HORIZON
    assert oracle.transition(
        oracle.State.OPEN_ACTIVE, oracle.Event.INTERRUPT_NATURAL
    ) is oracle.State.OPEN_INTERRUPTED
    assert oracle.transition(
        oracle.State.OPEN_NATURAL, oracle.Event.TERMINAL_HORIZON
    ) is oracle.State.TERMINAL_READY
    with pytest.raises(ValueError, match="ambiguous close"):
        oracle.resolve_close(natural=False, interrupt=False)
    with pytest.raises(ValueError, match="ambiguous cutoff"):
        oracle.resolve_cutoff(horizon=False, terminal=False)
    assert oracle.transition(oracle.State.OPEN_ACTIVE, oracle.Event.HORIZON) is oracle.State.INVALID
    simultaneous = next(
        case for case in audit.cases
        if case.valid
        and case.spec.close_mode is oracle.CloseMode.SIMULTANEOUS_INTERRUPT_NATURAL
        and case.spec.cutoff is oracle.Cutoff.SIMULTANEOUS_TERMINAL_HORIZON
    )
    natural = replace(
        simultaneous.events[1], event=oracle.Event.NATURAL,
        after=oracle.State.OPEN_NATURAL,
    )
    events = list(simultaneous.events)
    events[1] = natural
    events[2] = replace(events[2], before=oracle.State.OPEN_NATURAL)
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(replace(simultaneous, events=tuple(events)))
    illegal = replace(simultaneous.events[1], event=oracle.Event.ILLEGAL, after=oracle.State.INVALID)
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(replace(simultaneous, events=(simultaneous.events[0], illegal)))


def test_target_score_release_tombstone_and_terminal_bootstrap_mutations(audit):
    case = next(case for case in audit.cases if case.valid)
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(replace(case, target=case.target + 1))
    for scores in ((), case.scores + case.scores):
        with pytest.raises(ValueError, match="case record"):
            oracle.verify_case(replace(case, scores=scores))
    for releases in ((), case.releases + case.releases):
        with pytest.raises(ValueError, match="case record"):
            oracle.verify_case(replace(case, releases=releases))
    for tombstones in ((), case.tombstones + case.tombstones):
        with pytest.raises(ValueError, match="case record"):
            oracle.verify_case(replace(case, tombstones=tombstones))
    terminal = next(
        item for item in audit.cases
        if item.valid and item.spec.cutoff is oracle.Cutoff.SIMULTANEOUS_TERMINAL_HORIZON
    )
    with pytest.raises(ValueError, match="forbids bootstrap"):
        oracle.absolute_target(terminal.physical, bootstrap_on_terminal=True)


def test_stale_version_parameter_separation_and_record_shape(audit):
    stale = next(case for case in audit.cases if not case.valid)
    oracle.verify_case(stale)
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(replace(stale, spec=replace(stale.spec, behavior_version=oracle.CURRENT_VERSION)))
    shared = oracle.PolicyParameter("shared")
    with pytest.raises(ValueError, match="shared policy/bootstrap"):
        oracle.validate_parameter_separation(shared, shared)
    with pytest.raises(ValueError, match="frozen"):
        oracle.validate_parameter_separation(shared, oracle.PolicyParameter("trainable_v"))
    assert audit.report["bookkeeping"] == {
        "scope": "PER_REALIZATION_RECORD_SHAPE_ONLY",
        "valid_record_counts": {"events": 4, "scores": 1, "releases": 1, "tombstones": 1},
        "stale_record_counts": {"events": 1, "scores": 0, "releases": 0, "tombstones": 1},
    }
    corpus = "".join(path.read_text(encoding="utf-8") for path in (
        SOURCE, Path(__file__), INDEX,
    ))
    retired = (
        "Version" + "Record", "_version" + "_record", '"ver' + 'sions"',
        "can_" + "advance", "exactly_" + "once", "version_" + "barrier",
        "same_" + "information",
    )
    assert all(token not in corpus for token in retired)


@pytest.mark.parametrize(
    "field,value",
    [
        ("world", oracle.World.ZERO), ("context", oracle.Context.P),
        ("action", oracle.Action.SHORT), ("close_mode", oracle.CloseMode.NATURAL),
        ("cutoff", oracle.Cutoff.HORIZON), ("owner_departure", False),
        ("behavior_version", oracle.CURRENT_VERSION - 1), ("base_index", 999),
    ],
)
def test_verify_rejects_every_spec_mutation(audit, field, value):
    case = _mutation_case(audit)
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(replace(case, spec=replace(case.spec, **{field: value})))


@pytest.mark.parametrize("container", ["case", "events", "scores", "releases", "tombstones"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("episode_id", "mutated"), ("source_owner_epoch", 99),
        ("own_boundary_index", 99), ("behavior_version", 99),
    ],
)
def test_verify_rejects_every_nested_identity_mutation(audit, container, field, value):
    case = _mutation_case(audit)
    record = case.identity if container == "case" else getattr(case, container)[0].identity
    bad_identity = replace(record, **{field: value})
    mutated = replace(case, identity=bad_identity) if container == "case" else _nested(
        case, container, identity=bad_identity
    )
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(mutated)


@pytest.mark.parametrize(
    "field",
    ["event_id", "slot_index", "event", "before", "after", "policy_clock", "environment_clock"],
)
def test_verify_rejects_every_event_field_mutation(audit, field):
    case = _mutation_case(audit)
    event = case.events[0]
    values = {
        "event_id": "mutated", "slot_index": event.slot_index + 1,
        "event": oracle.Event.ILLEGAL, "before": oracle.State.INVALID,
        "after": oracle.State.INVALID, "policy_clock": event.policy_clock + 1,
        "environment_clock": event.environment_clock + 1,
    }
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(_nested(case, "events", **{field: values[field]}))


@pytest.mark.parametrize("field", ["target", "score", "action"])
def test_verify_rejects_every_score_field_mutation(audit, field):
    case = _mutation_case(audit)
    score = case.scores[0]
    values = {"target": score.target + 1, "score": score.score + 1, "action": oracle.Action.SHORT}
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(_nested(case, "scores", **{field: values[field]}))


@pytest.mark.parametrize("field", ["target", "release_clock"])
def test_verify_rejects_every_release_field_mutation(audit, field):
    case = _mutation_case(audit)
    release = case.releases[0]
    value = release.target + 1 if field == "target" else release.release_clock + 1
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(_nested(case, "releases", **{field: value}))


@pytest.mark.parametrize("field", ["final_state", "target", "reason"])
def test_verify_rejects_every_tombstone_field_mutation(audit, field):
    case = _mutation_case(audit)
    tombstone = case.tombstones[0]
    values = {
        "final_state": oracle.State.INVALID, "target": tombstone.target + 1,
        "reason": "MUTATED",
    }
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(_nested(case, "tombstones", **{field: values[field]}))


@pytest.mark.parametrize(
    "field",
    [
        "tau", "horizon", "terminal_time", "rewards", "vbar", "close_outcome",
        "cutoff_outcome", "final_owner_epoch", "primitive_tape", "partner_tape", "timing",
    ],
)
def test_verify_rejects_every_physical_field_mutation(audit, field):
    case = _mutation_case(audit)
    trace = case.physical
    values = {
        "tau": trace.tau + 1, "horizon": trace.horizon + 1,
        "terminal_time": trace.terminal_time + 1,
        "rewards": (trace.rewards[0] + 1, trace.rewards[1]), "vbar": trace.vbar + 1,
        "close_outcome": "MUTATED", "cutoff_outcome": "MUTATED",
        "final_owner_epoch": trace.final_owner_epoch + 1,
        "primitive_tape": ("mutated",), "partner_tape": ("mutated",),
        "timing": (0, 0, 0, 0),
    }
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(replace(case, physical=replace(trace, **{field: values[field]})))


@pytest.mark.parametrize("field", ["slot_index", "valid", "final_state", "target", "target_recomputed"])
def test_verify_rejects_case_surface_mutations(audit, field):
    case = _mutation_case(audit)
    values = {
        "slot_index": case.slot_index + 1, "valid": False,
        "final_state": oracle.State.INVALID, "target": case.target + 1,
        "target_recomputed": case.target_recomputed + 1,
    }
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(replace(case, **{field: values[field]}))


@pytest.mark.parametrize(
    "mutation",
    ["event", "event_before", "event_after", "tombstone_state", "tombstone_target",
     "tombstone_reason", "score", "release", "valid", "final_state"],
)
def test_verify_rejects_stale_record_semantic_mutations(audit, mutation):
    case = next(item for item in audit.cases if not item.valid)
    if mutation == "event":
        bad = _nested(case, "events", event=oracle.Event.ILLEGAL)
    elif mutation == "event_before":
        bad = _nested(case, "events", before=oracle.State.OPEN_ACTIVE)
    elif mutation == "event_after":
        bad = _nested(case, "events", after=oracle.State.RELEASED)
    elif mutation == "tombstone_state":
        bad = _nested(case, "tombstones", final_state=oracle.State.RELEASED)
    elif mutation == "tombstone_target":
        bad = _nested(case, "tombstones", target=Fraction(0))
    elif mutation == "tombstone_reason":
        bad = _nested(case, "tombstones", reason="MUTATED")
    elif mutation == "score":
        bad = replace(case, scores=(oracle.ScoreRecord(case.identity, Fraction(0), Fraction(0), oracle.Action.SHORT),))
    elif mutation == "release":
        bad = replace(case, releases=(oracle.ReleaseRecord(case.identity, Fraction(0), 100),))
    elif mutation == "valid":
        bad = replace(case, valid=True)
    else:
        bad = replace(case, final_state=oracle.State.RELEASED)
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(bad)


def test_registered_z0_branch_law_selector_and_integrated_values(audit):
    expected_branches = set(product(
        oracle.World, oracle.CloseMode, oracle.Cutoff, (False, True)
    ))
    assert isinstance(oracle.BRANCH_LAW, tuple) and len(oracle.BRANCH_LAW) == 16
    assert {branch.key() for branch in oracle.BRANCH_LAW} == expected_branches
    assert all(branch.weight == Fraction(1, 16) > 0 for branch in oracle.BRANCH_LAW)
    assert sum(branch.weight for branch in oracle.BRANCH_LAW) == 1
    valid = [case for case in audit.cases if case.valid]
    assert all(
        len([case for case in valid if (case.spec.context, case.spec.action) == key]) == 16
        for key in product(oracle.Context, oracle.Action)
    )
    candidate = oracle.candidate_integrated_values(valid)
    comparator = oracle.comparator_integrated_values()
    assert set(candidate) == set(comparator) == set(product(oracle.Context, oracle.Action))
    assert candidate == comparator == {
        (oracle.Context.F, oracle.Action.SHORT): Fraction(71, 64),
        (oracle.Context.F, oracle.Action.LONG): Fraction(63, 64),
        (oracle.Context.P, oracle.Action.SHORT): Fraction(135, 64),
        (oracle.Context.P, oracle.Action.LONG): Fraction(139, 64),
    }
    assert all(
        oracle.candidate_selector(context, tape)
        is oracle.comparator_selector(context, tape)
        for context, tape in product(oracle.Context, oracle.REGISTERED_SELECTOR_TAPE)
    )
    assert oracle.SELECTOR_TAPE == oracle.REGISTERED_SELECTOR_TAPE == (
        Fraction(0), Fraction(1, 8), Fraction(1, 4), Fraction(3, 8),
        Fraction(1, 2), Fraction(5, 8), Fraction(3, 4), Fraction(7, 8),
    )
    report = audit.report["comparator"]
    full = ["context", "tau", "remaining_horizon", "focal_execution_phase", "public_partner_phase", "legal_duration_mask", "behavior_version"]
    ignored = full[1:]
    assert report["z0_full_fields"] == full
    assert report["candidate_z0_used_fields"] == report["comparator_z0_used_fields"] == ["context"]
    assert report["candidate_ignored_legal_fields"] == report["comparator_ignored_legal_fields"] == ignored
    assert report["registered_remaining_horizon"] == oracle.HORIZON == 2
    assert report["used_is_strict_subset_of_full"] is report["same_used_selector_information"] is True
    assert report["branch_variables_marginalized_only"] is True
    assert report["branch_law"]["branches_per_z0_action"] == 16
    assert report["branch_law"]["normalized_full_support"] is True
    assert report["selector"] == {
        "runtime_tape_cells": 8, "registered_tape_cells": 8,
        "runtime_tape_ordered_exact": True, "runtime_tape_length_exact": True,
        "runtime_tape_unique_exact": True, "registered_entries": 16,
        "registered_domain_exact": True, "threshold": "LONG iff tape < p",
        "candidate_entries": 16, "comparator_entries": 16,
        "candidate_domain_exact": True, "comparator_domain_exact": True,
        "candidate_nested": True, "equal_keys": True, "exact_reproduction": True,
    }
    assert report["values"]["scope"] == "REGISTERED_16_BRANCH_SYNTHETIC_MIXTURE"
    assert report["values"]["conditions_on_full_z0"] is False
    assert report["values"]["marginalized_fields"] == [
        "world", "close_mode", "cutoff", "owner_departure", "associated_tau",
    ]
    assert report["values"]["marginalized_owner_departure_tau_values"] == [100, 104]
    assert report["values"]["key_fields"] == ["context", "action"]
    assert all(report["values"][key] is True for key in (
        "candidate_domain_exact", "comparator_domain_exact",
        "candidate_nested", "equal_keys", "exact_reproduction",
    ))
    assert report["terminal_gate"] is True
    assert audit.report["terminal"] == "REGISTERED_Z0_SELECTOR_VALUE_CONFORMANCE"
    assert audit.report["disposition"] == "NO_INCREMENT_OVER_REGISTERED_Z0_COMPARATOR"


def test_branch_weight_probability_threshold_and_value_mutations_fail_closed(audit, monkeypatch):
    valid = [case for case in audit.cases if case.valid]
    changed = list(oracle.BRANCH_LAW)
    changed[0] = replace(changed[0], weight=Fraction(1, 32))
    changed[1] = replace(changed[1], weight=Fraction(3, 32))
    branch_report = oracle.registered_z0_conformance(valid, tuple(changed))
    assert branch_report["branch_law"]["normalized_full_support"] is False
    assert branch_report["terminal_gate"] is False
    probabilities = {oracle.Context.F: Fraction(3, 8), oracle.Context.P: Fraction(3, 4)}
    probability_report = oracle.registered_z0_conformance(valid, probabilities=probabilities)
    assert probability_report["selector"]["exact_reproduction"] is False
    assert probability_report["terminal_gate"] is False
    inclusive = lambda context, tape, table: (
        oracle.Action.LONG if tape <= table[context] else oracle.Action.SHORT
    )
    threshold_report = oracle.registered_z0_conformance(valid, comparator_select=inclusive)
    assert threshold_report["selector"]["exact_reproduction"] is False
    original = oracle.comparator_integrated_values
    def mutated_values(law=oracle.BRANCH_LAW):
        values = original(law)
        values[(oracle.Context.F, oracle.Action.SHORT)] += 1
        return values
    monkeypatch.setattr(oracle, "comparator_integrated_values", mutated_values)
    value_report = oracle.registered_z0_conformance(valid)
    assert value_report["values"]["exact_reproduction"] is False
    assert value_report["terminal_gate"] is False
    with pytest.raises(ValueError, match="registered_z0_selector_value_conformance"):
        oracle.run_oracle()


def test_identical_extra_future_value_keys_fail_exact_domain(audit, monkeypatch):
    original_candidate = oracle.candidate_integrated_values
    original_comparator = oracle.comparator_integrated_values
    extra = (oracle.Context.F, oracle.Action.SHORT, oracle.World.POSITIVE)
    def candidate_with_extra(cases, law=oracle.BRANCH_LAW):
        values = original_candidate(cases, law)
        values[extra] = Fraction(71, 64)
        return values
    def comparator_with_extra(law=oracle.BRANCH_LAW):
        values = original_comparator(law)
        values[extra] = Fraction(71, 64)
        return values
    monkeypatch.setattr(oracle, "candidate_integrated_values", candidate_with_extra)
    monkeypatch.setattr(oracle, "comparator_integrated_values", comparator_with_extra)
    report = oracle.registered_z0_conformance(case for case in audit.cases if case.valid)
    assert report["values"]["candidate_entries"] == report["values"]["comparator_entries"] == 5
    assert report["values"]["exact_reproduction"] is True
    assert report["values"]["candidate_domain_exact"] is False
    assert report["values"]["comparator_domain_exact"] is False
    assert report["same_used_selector_information"] is True
    assert report["terminal_gate"] is False
    assert set(report["values"]["candidate"]) == {"F|SHORT", "F|LONG", "P|SHORT", "P|LONG"}


@pytest.mark.parametrize(
    "field,value",
    [
        ("Z0_FULL_FIELDS", oracle.Z0_FULL_FIELDS[:-1]),
        ("Z0_FULL_FIELDS", oracle.Z0_FULL_FIELDS + ("extra",)),
        ("Z0_FULL_FIELDS", oracle.Z0_FULL_FIELDS + ("behavior_version",)),
        ("Z0_FULL_FIELDS", ("tau", "context") + oracle.Z0_FULL_FIELDS[2:]),
        ("Z0_FULL_FIELDS", oracle.Z0_FULL_FIELDS[:2] + ("altered",) + oracle.Z0_FULL_FIELDS[3:]),
        ("CANDIDATE_Z0_USED_FIELDS", ()),
        ("CANDIDATE_Z0_USED_FIELDS", ("context", "tau")),
        ("CANDIDATE_Z0_USED_FIELDS", ("context", "context")),
        ("CANDIDATE_Z0_USED_FIELDS", ("altered",)),
        ("COMPARATOR_Z0_USED_FIELDS", ()),
        ("COMPARATOR_Z0_USED_FIELDS", ("context", "tau")),
        ("COMPARATOR_Z0_USED_FIELDS", ("context", "context")),
        ("COMPARATOR_Z0_USED_FIELDS", ("altered",)),
        *[(field, value) for field in ("CANDIDATE_IGNORED_LEGAL_FIELDS", "COMPARATOR_IGNORED_LEGAL_FIELDS") for value in (
            oracle.CANDIDATE_IGNORED_LEGAL_FIELDS[:-1],
            oracle.CANDIDATE_IGNORED_LEGAL_FIELDS + ("extra",),
            oracle.CANDIDATE_IGNORED_LEGAL_FIELDS + ("behavior_version",),
            ("remaining_horizon", "tau") + oracle.CANDIDATE_IGNORED_LEGAL_FIELDS[2:],
            oracle.CANDIDATE_IGNORED_LEGAL_FIELDS[:1] + ("altered",) + oracle.CANDIDATE_IGNORED_LEGAL_FIELDS[2:],
        )],
    ],
)
def test_same_used_selector_information_mutations_fail_closed(audit, monkeypatch, field, value):
    monkeypatch.setattr(oracle, field, value)
    report = oracle.registered_z0_conformance(case for case in audit.cases if case.valid)
    assert report["same_used_selector_information"] is False
    assert report["terminal_gate"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        oracle.REGISTERED_SELECTOR_TAPE[:-1],
        oracle.REGISTERED_SELECTOR_TAPE + (Fraction(1),),
        oracle.REGISTERED_SELECTOR_TAPE[:-1] + (oracle.REGISTERED_SELECTOR_TAPE[-2],),
        oracle.REGISTERED_SELECTOR_TAPE[:-1] + (Fraction(15, 16),),
    ],
    ids=["missing", "extra", "duplicate", "altered"],
)
def test_runtime_selector_tape_mutations_fail_registered_terminal(audit, monkeypatch, mutation):
    monkeypatch.setattr(oracle, "SELECTOR_TAPE", mutation)
    report = oracle.registered_z0_conformance(case for case in audit.cases if case.valid)
    selector = report["selector"]
    assert selector["registered_entries"] == 16
    assert selector["registered_domain_exact"] is True
    assert selector["runtime_tape_ordered_exact"] is False
    assert selector["equal_keys"] is selector["exact_reproduction"] is True
    assert selector["candidate_entries"] == selector["comparator_entries"]
    assert report["terminal_gate"] is False


def test_candidate_probability_mutation_fails_selector_gate(audit, monkeypatch):
    monkeypatch.setattr(oracle, "_probability", lambda context: Fraction(1, 2))
    report = oracle.registered_z0_conformance(case for case in audit.cases if case.valid)
    assert report["selector"]["exact_reproduction"] is False
    assert report["terminal_gate"] is False


def test_cli_is_byte_stable_and_index_binds_raw_output():
    command = [sys.executable, "-B", str(SOURCE)]
    first = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
    second = subprocess.run(command, cwd=ROOT, check=True, capture_output=True).stdout
    assert first == second
    raw = first.decode("utf-8").rstrip("\r\n")
    json.loads(raw)
    marker = "```json\n"
    index = INDEX.read_text(encoding="utf-8")
    bound = index.split(marker, 1)[1].split("\n```", 1)[0]
    assert raw == bound
