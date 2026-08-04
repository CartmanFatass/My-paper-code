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


def test_stale_version_parameter_separation_and_slot_alias(audit):
    stale = next(case for case in audit.cases if not case.valid)
    oracle.verify_case(stale)
    with pytest.raises(ValueError, match="case record"):
        oracle.verify_case(replace(stale, spec=replace(stale.spec, behavior_version=oracle.CURRENT_VERSION)))
    assert audit.report["versions"] == {
        "current": {
            "behavior_version": 9, "record_count": 64, "released_count": 64,
            "invalid_count": 0, "can_advance": True,
        },
        "stale": {
            "behavior_version": 8, "record_count": 64, "released_count": 0,
            "invalid_count": 64, "can_advance": False,
        },
    }
    shared = oracle.PolicyParameter("shared")
    with pytest.raises(ValueError, match="shared policy/bootstrap"):
        oracle.validate_parameter_separation(shared, shared)
    with pytest.raises(ValueError, match="frozen"):
        oracle.validate_parameter_separation(shared, oracle.PolicyParameter("trainable_v"))
    registry = oracle.EscrowRegistry()
    registry.claim(stale.identity, 0)
    with pytest.raises(ValueError, match="slot cannot alias"):
        registry.claim(stale.identity, 99)
    registry.release(stale.identity)
    with pytest.raises(ValueError, match="duplicate release"):
        registry.release(stale.identity)


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


def test_strongest_null_exactly_nests_and_reproduces_mapping(audit):
    null = oracle.horizon_flush_tabular_duration_null()
    candidate = {
        (
            case.spec.world.value, case.spec.context.value, case.spec.close_mode.value,
            case.spec.cutoff.value, case.spec.owner_departure, case.spec.action.value,
        ): case.target
        for case in audit.cases if case.valid
    }
    assert len(null) == len(candidate) == 64
    assert set(candidate).issubset(null)
    assert candidate == null
    assert audit.report["null"] == {
        "name": "HORIZON_FLUSH_TABULAR_DURATION_NULL",
        "same_information": True, "full_horizon": True,
        "finite_predecision_keys": 32, "action_entries": 64,
        "candidate_entries": 64, "candidate_nested": True,
        "exact_reproduction": True,
    }
    assert audit.report["terminal"] == "ADAPTIVE_DURATION_RETIRED"
    assert audit.report["disposition"] == "BOOKKEEPING_TRANSPORT_CONFORMANCE_ONLY"


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
