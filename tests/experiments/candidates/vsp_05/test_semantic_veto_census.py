from __future__ import annotations

import ast
import inspect
import json
import re
from collections import deque
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest

from experiments.candidates.vsp_05 import semantic_veto_census as svc


ROOT = Path(__file__).parents[4]
SOURCE = ROOT / "experiments/candidates/vsp_05/semantic_veto_census.py"
INDEX = ROOT / "docs/research/candidates/vsp_05/CODE_SCIENCE_INDEX.md"


@pytest.fixture(scope="module")
def registry() -> svc.Registry:
    return svc.build_registry()


@pytest.fixture(scope="module")
def prepared(registry: svc.Registry) -> tuple[dict[str, object], dict[tuple[bool, ...], list[int]], tuple[svc.Tape, ...]]:
    report = svc.census(registry)
    return report, report["_counts"], report["_tapes"]


def test_registry_contains_immutable_physical_records_and_two_audit_exclusions(registry: svc.Registry) -> None:
    source = inspect.getsource(svc.build_registry)
    assert not ({"physical_y", "label", "outcome"} & {node.id for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Name)})
    assert "POSITIVE_X" not in source
    assert len(registry.grid) == 243 and registry.schema == svc.FIELDS
    assert registry.lineage_registry == svc.FOLDS and len(set(svc.FOLDS)) == 6
    assert registry.x_star == tuple(product((False, True), repeat=6))
    assert registry.raw_x_tape == svc.RAW_X_TAPE and registry.q_kappa_tape is svc.Q_KAPPA_TAPE
    constructor_source = source + inspect.getsource(svc.physical_records)
    assert "X_STAR.index" not in constructor_source and "POSITIVE_X" not in constructor_source
    assert "zip(raw_tape, Q_KAPPA_TAPE)" in constructor_source
    assert len(registry.records) == 243 * 6 * 64 + 2
    valid = [record for record in registry.records if record.transaction_identity == "kappa_focal_001" and record.owner_epoch_valid]
    assert len(valid) == 93_312
    assert len({record.opportunity_identity for record in registry.records}) == len(registry.records)
    assert all(record.fold in svc.FOLDS and record.cell in registry.grid for record in registry.records)
    with pytest.raises(FrozenInstanceError):
        valid[0].physical_index = 2
    with pytest.raises(FrozenInstanceError):
        valid[0].raw_sources.e_local = True


def test_physical_record_to_x_and_y_are_separate_sources(registry: svc.Registry) -> None:
    admitted, _ = svc.admit_records(registry, registry.records)
    positives = [record for record in admitted[:64] if svc.physical_y(record)]
    assert [record.physical_index for record in positives] == [61, 62, 63]
    assert [svc.x_key(svc.extract_x(record)) for record in positives] == ["111101", "111110", "111111"]
    assert [record.q_kappa_state for record in positives] == [(0, 1), (1, 1), (1, 1)]
    positive = positives[0]
    raw_mutation = replace(positive, raw_sources=replace(positive.raw_sources, e_local=False))
    assert svc.extract_x(raw_mutation) != svc.extract_x(positive)
    assert svc.physical_y(raw_mutation) == svc.physical_y(positive) == 1
    assert svc.physical_y(replace(positives[1], q_kappa_state=(1, 0))) == 0
    assert svc.physical_y(replace(positive, transaction_identity="other_kappa")) == 0
    assert svc.physical_y(replace(positive, owner_epoch_valid=False)) == 0
    assert "extract_x" not in inspect.getsource(svc.physical_y)
    assert "physical_y" not in inspect.getsource(svc.extract_x)


def test_independently_registered_raw_and_q_tapes_are_bidirectionally_invariant(registry: svc.Registry) -> None:
    event, cell = registry.event_registry[0], registry.grid[0]
    baseline = svc.physical_records((cell,), event, svc.RAW_X_TAPE)[:64]
    raw_mutation = list(svc.RAW_X_TAPE)
    raw_mutation[0], raw_mutation[1] = raw_mutation[1], raw_mutation[0]
    raw_changed = svc.physical_records((cell,), event, tuple(raw_mutation))[:64]
    assert svc.extract_x(raw_changed[0]) != svc.extract_x(baseline[0])
    assert [record.q_kappa_state for record in raw_changed] == [record.q_kappa_state for record in baseline]
    assert [svc.physical_y(record) for record in raw_changed] == [svc.physical_y(record) for record in baseline]
    q_changed = tuple(replace(record, q_kappa_state=(0, 0)) if record.physical_index == 61 else record for record in baseline)
    assert [svc.extract_x(record) for record in q_changed] == [svc.extract_x(record) for record in baseline]
    assert [svc.physical_y(record) for record in q_changed] != [svc.physical_y(record) for record in baseline]
    with pytest.raises(ValueError):
        svc.physical_records((cell,), event, svc.RAW_X_TAPE[:-1] + (svc.RAW_X_TAPE[0],))
    with pytest.raises(ValueError, match="not bound to canonical tape position"):
        svc.materialize_tapes(registry, q_changed)


def test_noncanonical_q_tape_or_record_fails_closed_before_positive_terminal(monkeypatch: pytest.MonkeyPatch, registry: svc.Registry) -> None:
    noncanonical_tape = tuple(list(svc.Q_KAPPA_TAPE))
    monkeypatch.setattr(svc, "build_registry", lambda: replace(registry, q_kappa_tape=noncanonical_tape))
    with pytest.raises(ValueError, match="canonical Q_KAPPA_TAPE object"):
        svc.build_report()
    inconsistent_records = list(registry.records)
    inconsistent_records[61] = replace(inconsistent_records[61], q_kappa_state=(0, 0))
    monkeypatch.setattr(svc, "build_registry", lambda: replace(registry, records=tuple(inconsistent_records)))
    with pytest.raises(ValueError, match="not bound to canonical tape position"):
        svc.build_report()


def test_label_blind_admission_exercises_both_reasons_before_y(monkeypatch: pytest.MonkeyPatch, registry: svc.Registry) -> None:
    monkeypatch.setattr(svc, "physical_y", lambda record: (_ for _ in ()).throw(AssertionError("Y called during admission")))
    admitted, exclusions = svc.admit_records(registry, registry.records)
    assert len(admitted) == 93_312
    assert exclusions == {"invalid_owner_epoch": 1, "transaction_mismatch": 1}
    assert all(record.owner_epoch_valid and record.transaction_identity == "kappa_focal_001" for record in admitted)


def test_materialization_sorts_deduplicates_and_reextracts_x(registry: svc.Registry, prepared: tuple[dict[str, object], dict, tuple[svc.Tape, ...]]) -> None:
    report, counts, tapes = prepared
    assert report["admission"] == {"admitted": 93_312, "exclusions_before_y": {"invalid_owner_epoch": 1, "transaction_mismatch": 1}}
    assert report["deduplication"] == {"duplicate_identity_count": 0, "unique_records": 93_312}
    assert report["opportunities"] == 93_312 and report["positive_labels"] == 4_374
    assert report["contradictions"] == report["support_exits"] == []
    assert report["unique_tape_signature_count"] == 1
    assert report["tape_signatures"][0]["multiplicity"] == 1_458
    assert len(tapes) == 1_458
    assert all(tuple(record.physical_time for record in tape.records) == tuple(sorted(record.physical_time for record in tape.records)) for tape in tapes)
    assert all(tape.xs == tuple(svc.extract_x(record) for record in tape.records) for tape in tapes)
    sample = tapes[0]
    assert sample.ys[-3:] == (1, 1, 1)
    unique, duplicates = svc.deduplicate_records(reversed(sample.records + (sample.records[0],)))
    assert duplicates == 1 and len(unique) == 64
    assert set(counts) == set(svc.X_STAR) and all(sum(values) == 1_458 for values in counts.values())
    for key in ("111101", "111110", "111111"):
        assert report["x_by_y"][key] == {"y0": 0, "y1": 1_458}


@pytest.mark.parametrize("source", svc.FORBIDDEN_FAMILIES + tuple(svc.FORBIDDEN_PROXIES.values()))
def test_executable_firewall_rejects_every_forbidden_injection(source: str, registry: svc.Registry) -> None:
    record = registry.records[0]
    values = dict(zip(svc.FIELDS, svc.extract_x(record)))
    values[source] = False
    with pytest.raises(ValueError):
        svc.raw_sources_from_input(values)
    with pytest.raises(ValueError):
        svc.extract_x(record, dependencies=svc.FIELDS + (source,))
    with pytest.raises(ValueError):
        svc.freeze_lookup(svc.saturated_lookup(), ("tuple", source))
    artifact = svc.freeze_lookup(svc.saturated_lookup())
    with pytest.raises(ValueError):
        svc.runtime_decision(svc.extract_x(record), artifact, dependencies=("tuple", "artifact", source))


def test_frozen_artifact_actual_runtime_path_and_firewall_report(registry: svc.Registry) -> None:
    artifact = svc.freeze_lookup(svc.saturated_lookup())
    positive = next(record for record in registry.records if svc.extract_x(record) == svc.POSITIVE_X and record.owner_epoch_valid)
    assert svc.runtime_decision(svc.extract_x(positive), artifact) == 1
    with pytest.raises(FrozenInstanceError):
        artifact.table = ()
    report = svc.firewall_report(positive, artifact)
    assert report["actual_path"] == "physical_record->X_extractor->frozen_lookup_artifact->tuple_only_runtime_decision"
    assert (report["clean"], report["injections_rejected"], report["injections_required"]) == (True, 104, 104)
    sequential_source = inspect.getsource(svc.sequential_fact)
    assert "runtime_decision(extract_x(record), artifact)" in sequential_source


def test_sequential_objective_uses_physical_tapes_and_first_latch_survival(prepared: tuple[dict, dict, tuple[svc.Tape, ...]]) -> None:
    _, counts, tapes = prepared
    rules, objective = svc.registered_rules(tapes)
    best = rules["BEST_DETERMINISTIC_TUPLE_ONLY_RULE"]
    assert objective["lexicographic_order"] == ["false_alias", "missed_positive", "capture_delay", "action_count"]
    assert objective["selected_score"] == [0, 0, 0, 1]
    assert best == svc.saturated_lookup() and best != svc.derive_pointwise_rule(counts)
    facts = {name: svc.sequential_fact(tapes[0], rule) for name, rule in rules.items()}
    assert facts["NO_VETO"]["first_latch_false_alias"] == 1
    assert facts["NO_VETO"]["positive_captures"] == facts["NO_VETO"]["missed_positives"] == 0
    assert facts["ALWAYS_VETO"]["missed_positives"] == 3
    assert facts["SATURATED_ALLOWLIST_LOOKUP"]["positive_captures"] == 1
    late = replace(tapes[0], records=tapes[0].records[:2], xs=tapes[0].xs[:2], ys=(1, 1))
    late_rule = {x: 0 for x in svc.X_STAR}
    late_rule[late.xs[1]] = 1
    late_facts = svc.sequential_fact(late, late_rule)
    assert (late_facts["missed_positives"], late_facts["positive_captures"], late_facts["capture_delay"]) == (1, 1, 1)


def test_action_count_is_survival_weighted_executed_actions(prepared: tuple[dict, dict, tuple[svc.Tape, ...]]) -> None:
    _, _, tapes = prepared
    tape = tapes[0]
    metrics = ("first_latch_false_alias", "missed_positives", "capture_delay", "action_count")
    r_single = {x: int(x == tape.xs[61]) for x in svc.X_STAR}
    r_three = {x: int(x in {tape.xs[61], tape.xs[62], tape.xs[63]}) for x in svc.X_STAR}
    single_facts = svc.sequential_fact(tape, r_single)
    three_facts = svc.sequential_fact(tape, r_three)
    assert [single_facts[name] for name in metrics] == [0, 0, 0, 1]
    assert [three_facts[name] for name in metrics] == [0, 0, 0, 1]
    assert {k: v for k, v in single_facts.items() if k != "action_decisions"} == {k: v for k, v in three_facts.items() if k != "action_decisions"}
    assert sum(r_three.values()) == 3 and sum(r_single.values()) == 1
    rules, objective = svc.registered_rules(tapes)
    facts = {name: svc.sequential_fact(tape, rule) for name, rule in rules.items()}
    assert facts["NO_VETO"]["action_count"] == 1 and sum(rules["NO_VETO"].values()) == 64
    assert facts["ALWAYS_VETO"]["action_count"] == 0
    early_pair = {x: int(x in {tape.xs[0], tape.xs[5]}) for x in svc.X_STAR}
    assert svc.sequential_fact(tape, early_pair)["action_count"] == 1
    for subset in ((61,), (61, 62), (61, 63), (61, 62, 63)):
        member = {x: int(x in {tape.xs[i] for i in subset}) for x in svc.X_STAR}
        assert [svc.sequential_fact(tape, member)[name] for name in metrics] == [0, 0, 0, 1]
    assert sum(rules["BEST_DETERMINISTIC_TUPLE_ONLY_RULE"].values()) == 1
    assert objective["representation_convention"] == "minimal_lookup_support_among_frozen_score_minimizers_not_part_of_frozen_objective"
    assert "tie-break" not in objective["derivation"]


@pytest.mark.parametrize("support", ((61,), (61, 62), (61, 63), (61, 62, 63)))
def test_every_frozen_score_minimizer_traverses_clone_and_physical_terminal(
    monkeypatch: pytest.MonkeyPatch,
    support: tuple[int, ...],
    registry: svc.Registry,
    prepared: tuple[dict[str, object], dict[tuple[bool, ...], list[int]], tuple[svc.Tape, ...]],
) -> None:
    original_derive = svc.derive_best_rule
    cached_report, counts, tapes = prepared
    public_report = {name: value for name, value in cached_report.items() if name not in {"_counts", "_tapes"}}

    def derive_minimizer(tapes: tuple[svc.Tape, ...]) -> tuple[dict[tuple[bool, ...], int], dict[str, object]]:
        _, objective = original_derive(tapes)
        selected = {tapes[0].xs[index] for index in support}
        return {x: int(x in selected) for x in svc.X_STAR}, objective

    monkeypatch.setattr(svc, "build_registry", lambda: registry)
    monkeypatch.setattr(svc, "census", lambda _registry: {**public_report, "_counts": counts, "_tapes": tapes})
    monkeypatch.setattr(svc, "derive_best_rule", derive_minimizer)
    monkeypatch.setattr(svc, "rule_summary", lambda _tapes, _rules: {})
    report = svc.build_report()
    assert report["clone_invariance"] == {
        "registered_clone_cases": 27,
        "physical_record_clones": 64 * 27,
        "comparisons": 64 * 27 * 4,
        "decision_drifts": [],
        "negative_allowlisted_source_mutation": {
            "detected": True,
            "source": "e_local",
            "x_before": "111101",
            "x_after": "011101",
            "decision_before": 1,
            "decision_after": 0,
        },
    }
    assert report["terminals"]["physical_census_tuple_only_first_latch"]
    assert report["conclusion"]["finite_support_lookup_conformance_holds_in_fixed_synthetic_instance"]


def test_physical_clone_invariance_and_allowed_source_negative_control(prepared: tuple[dict, dict, tuple[svc.Tape, ...]]) -> None:
    _, _, tapes = prepared
    rules, _ = svc.registered_rules(tapes)
    report = svc.clone_report(tapes[0], rules)
    assert report["registered_clone_cases"] == 27
    assert report["physical_record_clones"] == 64 * 27
    assert report["comparisons"] == 64 * 27 * 4
    assert report["decision_drifts"] == []
    assert report["negative_allowlisted_source_mutation"]["detected"]


def test_handoff_model_preserves_fixed_48_state_fsm() -> None:
    spec = svc.HandoffSpec()
    queue, states, transitions = deque([svc.HandoffState()]), {svc.HandoffState()}, 0
    while queue:
        state = queue.popleft()
        for action in svc.HANDOFF_ACTIONS:
            successor = svc.handoff_transition(state, action, spec)
            transitions += 1
            assert successor.commit_count <= 1
            assert not successor.sender_terminated or successor.public_commit
            assert not successor.receiver_active or successor.public_commit
            if successor not in states:
                states.add(successor); queue.append(successor)
    report = svc.handoff_model_check()
    assert len(states) == report["reachable_states"] == 48
    assert transitions == report["transitions_checked"] == 480
    assert report["invariant_violations"] == [] and report["exactly_once_handoff_safety"]
    assert all(report["negative_gate_checks"].values())


def test_report_is_deterministic_and_terminals_are_separate() -> None:
    first, second = svc.raw_json(), svc.raw_json()
    assert first == second and ": " not in first and ", " not in first
    report = json.loads(first)
    assert report["terminals"] == {"fixed_single_transaction_handoff": True, "physical_census_tuple_only_first_latch": True}
    assert report["conclusion"] == {"exactly_once_handoff_safety_holds_in_fixed_synthetic_instance": True, "finite_support_lookup_conformance_holds_in_fixed_synthetic_instance": True}
    assert not report["pointwise_diagnostic"]["handcrafted_64_row_lookup_equals_pointwise"]
    assert report["event"]["q_diagnostic"] == [0, 1, 1, 1]
    assert report["event"]["q_diagnostic_source"] == "Q_KAPPA_TAPE"
    assert report["physical_tape_registration"]["positive_physical_indices"] == [61, 62, 63]
    assert report["physical_tape_registration"]["q_current_suffix"] == "111"
    assert report["handoff"]["reachable_states"] == 48


def test_pointwise_diagnostic_cannot_control_physical_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "derive_pointwise_rule", lambda counts: {x: 0 for x in svc.X_STAR})
    report = svc.build_report()
    assert report["terminals"]["physical_census_tuple_only_first_latch"]
    assert not report["pointwise_diagnostic"]["handcrafted_64_row_lookup_equals_pointwise"]
    assert report["pointwise_diagnostic"]["derived_best_equals_handcrafted_lookup"]


def test_handcrafted_lookup_cannot_control_physical_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "saturated_lookup", lambda: {x: 0 for x in svc.X_STAR})
    report = svc.build_report()
    assert report["terminals"]["physical_census_tuple_only_first_latch"]
    assert not report["pointwise_diagnostic"]["derived_best_equals_handcrafted_lookup"]


def test_transition_only_label_cannot_reach_physical_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "physical_y", lambda record: int(record.q_kappa_state == (0, 1) and record.transaction_identity == "kappa_focal_001" and record.owner_epoch_valid))
    report = svc.build_report()
    assert report["census"]["positive_labels"] == 1_458
    assert not report["terminals"]["physical_census_tuple_only_first_latch"]


def test_source_has_no_forbidden_runtime_interfaces() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    imports = {alias.name.split(".")[0] for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Import) for alias in node.names}
    imports |= {node.module.split(".")[0] for node in ast.walk(ast.parse(text)) if isinstance(node, ast.ImportFrom) and node.module}
    assert imports <= {"__future__", "json", "collections", "dataclasses", "fractions", "itertools", "typing"}
    assert "torch" not in text and "tensorflow" not in text and "production" not in text.lower()


def test_code_science_index_contains_one_full_exact_raw_output_block() -> None:
    text = INDEX.read_text(encoding="utf-8")
    begin, end = "<!-- FULL_RAW_JSON_BEGIN -->", "<!-- FULL_RAW_JSON_END -->"
    assert text.count(begin) == text.count(end) == 1
    matches = re.findall(re.escape(begin) + r"\n```json\n([^\n]+)\n```\n" + re.escape(end), text)
    assert matches == [svc.raw_json()]
    assert svc.RAW_OUTPUT_BINDING in text
    assert "physical-census terminal" in text and "handoff terminal" in text
    assert "MLP was not run" in text
