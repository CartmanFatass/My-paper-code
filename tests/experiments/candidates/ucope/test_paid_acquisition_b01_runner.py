"""Tests for the ``UCOPE-B-EXPLORE-PAID-ACQUISITION-B01`` runner.

The load-bearing ones are `test_a_paid_is_the_frozen_predicate_minus_competence`, which pins the
branch statistic to the frozen `acquisition_pass` on every input where they may differ, and
`test_a_perturbed_published_tail_quarantines_the_run`, which exercises the §6.2 path behind the
1e-6 tail-reproduction gate.
"""

from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

numpy = pytest.importorskip("numpy")
torch = pytest.importorskip("torch")

from experiments.candidates.ucope.competence_first_scout_r01.contract import (  # noqa: E402
    B1_SEEDS,
    CONTEXTS,
    K_EVAL,
    K_TRAIN,
    TARGET_CONTEXT_ID,
    context_id,
)
from experiments.candidates.ucope.competence_first_scout_r01.oracle import (  # noqa: E402
    build_oracle,
)


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load("ucope_paid_acquisition_b01", "run_ucope_paid_acquisition_b01.py")
RM = RUNNER.RM
RC = RUNNER.RC
CR = RUNNER.CR
SELECTION = CR._n_selection()

CARD_TEST = _load  # kept for symmetry; the card loader lives in the card test module
SMALL_EPISODES = 320
SMALL_TAIL_UPDATES = 4
SMALL_ROOT_UPDATES = 8


def _card_constants():
    spec = importlib.util.spec_from_file_location(
        "ucope_paid_acquisition_card_test",
        PROJECT_ROOT / "tests/experiments/candidates/ucope/test_paid_acquisition_b01_card.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_frozen_constants()


# --------------------------------------------------------------------------- frozen constants


def test_the_runner_matches_the_cards_frozen_constants():
    constants = _card_constants()
    assert RUNNER.OBJECT_ID == "UCOPE-B-EXPLORE-PAID-ACQUISITION-B01"
    assert RUNNER.EVIDENCE_CLASS == "B/EXPLORE"
    assert RUNNER.TARGET_CONTEXT_ID == constants["TARGET_CONTEXT_ID"] == TARGET_CONTEXT_ID
    assert RUNNER.DRAW_OFFSET == int(constants["draw_offset"]) == 2_000_000
    assert RUNNER.EPISODES_PER_CONTEXT == int(constants["episodes_per_context"]) == 40_960
    assert RUNNER.TAIL_ROWS_PER_POLICY == int(constants["tail_rows_per_policy"]) == 81_920
    assert RUNNER.TAIL_UPDATES == int(constants["tail_updates"]) == 1_600
    assert RUNNER.ROOT_UPDATES == int(constants["root_updates"]) == 3_200
    assert RUNNER.LEARNING_RATE == float(constants["learning_rate"]) == 3e-3
    assert RUNNER.HINGE_MARGIN == float(constants["hinge_margin"]) == 0.024022
    assert RUNNER.HINGE_WEIGHT == float(constants["hinge_weight"]) == 1.0
    assert list(RUNNER.HINGE_WITNESS_PAIR) == [
        int(v) for v in constants["hinge_witness_pair"].split(",")]
    assert RUNNER.TAIL_REPRODUCTION_TOLERANCE == float(
        constants["tail_reproduction_tolerance"]) == 1e-6
    assert RUNNER.EPS_L == float(constants["eps_L"]) == 0.10
    assert RUNNER.MAJORITY == int(constants["majority_threshold"]) == 4
    assert RUNNER.POLICIES == int(constants["policies"]) == 6
    assert RUNNER.THREAD_CAP == int(constants["thread_cap"]) == 1
    assert (RUNNER.TREATMENT, RUNNER.REFERENCE) == ("MARGIN-AWARE-TREATMENT", "EXACT-REFERENCE")


def test_the_treatment_learner_is_the_remedies_margin_aware_arm():
    margin_aware = RM.ARMS["MARGIN-AWARE"]
    assert RUNNER.TAIL_UPDATES == margin_aware["tail_updates"]
    assert RUNNER.EPISODES_PER_CONTEXT == margin_aware["episodes_per_context"]
    assert margin_aware["hinge"] is True
    assert RUNNER.HINGE_WITNESS_PAIR == RM.HINGE_WITNESS_PAIR
    assert set(RUNNER.HINGE_WITNESS_PAIR) <= set(K_TRAIN)
    assert not set(RUNNER.HINGE_WITNESS_PAIR) & set(K_EVAL)


def test_the_ledger_records_competence_and_never_gates_on_it():
    assert "competence_record_section_11_1" in RUNNER.LEDGER["recorded_not_gating"]
    assert not any("competence" in item for item in RUNNER.LEDGER["still_gating"])
    assert "tail_reproduction_within_1e-6" in RUNNER.LEDGER["still_gating"]
    assert "resource_telemetry_and_concurrent_load" in RUNNER.LEDGER["recorded_not_gating"]


# --------------------------------------------------------------------------- A_paid


def _audit(*, target="PROBE", others="IMMEDIATE", delta=0.01, probe=-0.05):
    actions = {context_id(c): others for c in CONTEXTS}
    actions[TARGET_CONTEXT_ID] = target
    return {"root_actions": actions, "target_delta_acquisition": delta,
            "direct_probe_component": probe,
            "oracle_root_match": target == "PROBE" and others == "IMMEDIATE"}


def test_a_paid_holds_only_when_all_four_conjuncts_hold():
    assert RUNNER.a_paid(_audit())["a_paid_pass"] is True
    assert RUNNER.a_paid(_audit(target="IMMEDIATE"))["a_paid_pass"] is False
    assert RUNNER.a_paid(_audit(others="PROBE"))["a_paid_pass"] is False
    assert RUNNER.a_paid(_audit(delta=0.0))["a_paid_pass"] is False
    assert RUNNER.a_paid(_audit(delta=-1e-9))["a_paid_pass"] is False
    assert RUNNER.a_paid(_audit(probe=0.0))["a_paid_pass"] is False


def test_a_paid_names_its_failing_conjunct():
    assert RUNNER.a_paid(_audit(target="IMMEDIATE"))["failing_conjuncts"] == ["pays_at_target"]
    assert RUNNER.a_paid(_audit(delta=-0.001))["failing_conjuncts"] == [
        "target_delta_acquisition_positive"]
    assert RUNNER.a_paid(_audit(others="PROBE"))["failing_conjuncts"] == [
        "refuses_everywhere_else"]
    assert set(RUNNER.a_paid(_audit())["conjuncts"]) == {
        "pays_at_target", "target_delta_acquisition_positive",
        "direct_probe_component_negative", "refuses_everywhere_else"}


@pytest.mark.parametrize("competence", (True, False))
@pytest.mark.parametrize("target", ("PROBE", "IMMEDIATE"))
@pytest.mark.parametrize("delta", (0.01, -0.01))
@pytest.mark.parametrize("others", ("IMMEDIATE", "PROBE"))
def test_a_paid_is_the_frozen_predicate_minus_competence(competence, target, delta, others):
    """A_paid must equal the frozen conjunction with competence forced true, on every input."""
    audit = _audit(target=target, others=others, delta=delta)
    frozen = bool(
        competence
        and audit["root_actions"][TARGET_CONTEXT_ID] == "PROBE"
        and audit["target_delta_acquisition"] > 0
        and audit["direct_probe_component"] < 0
        and all(action == "IMMEDIATE" for cell, action in audit["root_actions"].items()
                if cell != TARGET_CONTEXT_ID)
    )
    mine = RUNNER.a_paid(audit)["a_paid_pass"]
    assert mine == (frozen if competence else
                    bool(audit["root_actions"][TARGET_CONTEXT_ID] == "PROBE"
                         and audit["target_delta_acquisition"] > 0
                         and audit["direct_probe_component"] < 0
                         and all(action == "IMMEDIATE"
                                 for cell, action in audit["root_actions"].items()
                                 if cell != TARGET_CONTEXT_ID)))
    if competence:
        assert mine == frozen


def test_the_acquisition_measurements_use_the_frozen_oracle():
    oracle = build_oracle()[TARGET_CONTEXT_ID]
    row = RUNNER.acquisition_measurements(_audit(delta=0.01))
    assert row["oracle_baseline_at_target"] == float(oracle["baseline"]) == 0.794
    assert row["oracle_net_acquisition_at_target"] == float(oracle["net_acquisition"])
    assert row["learned_value_at_target"] == pytest.approx(0.01 + 0.794)
    assert row["acquisition_shortfall"] == pytest.approx(
        float(oracle["net_acquisition"]) - 0.01)


# --------------------------------------------------------------------------- reading rule


def _policies(treatment, reference):
    return [
        {"seed_id": "s", "fold_id": index % 2,
         "arms": {RUNNER.TREATMENT: {"a_paid": {"a_paid_pass": t}},
                  RUNNER.REFERENCE: {"a_paid": {"a_paid_pass": r}}}}
        for index, (t, r) in enumerate(zip(treatment, reference))
    ]


def test_rule_pa_a_when_the_treatment_pays_correctly_in_all_six():
    reading = RUNNER.apply_reading_rule(_policies([True] * 6, [False] * 6))
    assert reading["branch"] == "PA-A"
    assert reading["numbers"]["treatment_count"] == 6


def test_rule_pa_b_needs_a_majority_and_a_clean_reference():
    reading = RUNNER.apply_reading_rule(_policies([True] * 4 + [False] * 2, [True] * 6))
    assert reading["branch"] == "PA-B"
    reading = RUNNER.apply_reading_rule(_policies([True] * 5 + [False], [True] * 6))
    assert reading["branch"] == "PA-B"


def test_rule_pa_c_when_only_the_reference_pays_correctly():
    reading = RUNNER.apply_reading_rule(_policies([True] * 3 + [False] * 3, [True] * 6))
    assert reading["branch"] == "PA-C"


def test_rule_pa_d_when_the_reference_itself_falls_short():
    reading = RUNNER.apply_reading_rule(
        _policies([True] * 5 + [False], [True] * 5 + [False]))
    assert reading["branch"] == "PA-D"
    assert RUNNER.apply_reading_rule(
        _policies([True] * 6, [False] * 6))["branch"] == "PA-A", "PA-A precedes the reference test"


def test_the_branch_order_is_the_carded_order():
    source = (PROJECT_ROOT / "scripts/run_ucope_paid_acquisition_b01.py").read_text(
        encoding="utf-8")
    positions = [source.index(f'"branch": "{name}"')
                 for name in ("PA-A", "PA-B", "PA-C", "PA-D", "PA-E")]
    assert positions == sorted(positions)


def test_the_rule_declares_competence_recorded_not_gating():
    reading = RUNNER.apply_reading_rule(_policies([True] * 6, [True] * 6))
    assert reading["numbers"]["competence_recorded_not_gating"] is True
    assert "competence" not in reading["numbers"]["branch_statistic"]


# --------------------------------------------------------------------------- the reference record


def test_the_published_reference_is_validated(tmp_path):
    with pytest.raises(RUNNER.LaunchRefusal, match="reference missing"):
        RUNNER.published_margin_aware(tmp_path / "absent.json")
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"object_id": "OTHER", "policies": []}), encoding="utf-8")
    with pytest.raises(RUNNER.LaunchRefusal, match="not the remedies run record"):
        RUNNER.published_margin_aware(wrong)


def _miniature_reference(path: Path) -> Path:
    """Build a MARGIN-AWARE reference at the miniature scale, the way the real one was built."""
    saved = SELECTION.OFFSET
    SELECTION.OFFSET = RUNNER.DRAW_OFFSET
    policies = []
    try:
        for seed in B1_SEEDS:
            ordered, _labels = CR.canonical_order(
                SELECTION.generate_columns(seed, SMALL_EPISODES))
            for fold in (0, 1):
                blocks = CR.stage_designs(ordered, fold)
                white = CR.whitening(blocks["tail"]["design64"], stage="tail")
                hinge = RM.hinge_directions(
                    ordered["belief"][(ordered["fold"] == (1 - fold)) & ordered["probe"]])
                beta_tail, _init = RM.train_tail(
                    seed_id=seed, fold_id=fold, blocks=blocks, white=white,
                    updates=SMALL_TAIL_UPDATES, hinge_design=hinge,
                    activity=CR._fresh_activity())
                policies.append({
                    "seed_id": seed, "fold_id": fold,
                    "arms": {"MARGIN-AWARE": {
                        "beta_tail": beta_tail,
                        "competence": {"competence_pass": False},
                        "agreement_within_gate": False,
                        "margin": {"count0_gap": RM.margin_record(beta_tail)["count0_gap"]},
                    }},
                })
    finally:
        SELECTION.OFFSET = saved
    path.write_text(json.dumps({
        "object_id": "UCOPE-B-EXPLORE-TAIL-MARGIN-REMEDIES-R01", "policies": policies,
    }), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- end to end


def test_a_miniature_run_produces_a_complete_record(tmp_path, monkeypatch):
    monkeypatch.setattr(CR, "_configure_topology", lambda cap: None)
    reference = _miniature_reference(tmp_path / "reference.json")
    path = RUNNER.run_object(
        tmp_path / "mini", thread_cap=1, episodes_per_context=SMALL_EPISODES,
        tail_updates=SMALL_TAIL_UPDATES, root_updates=SMALL_ROOT_UPDATES,
        remedies_record=reference, concurrent_load="unit test, no concurrent load")
    record = json.loads(Path(path).read_text(encoding="utf-8"))

    assert record["complete"] is True
    assert record["object_id"] == "UCOPE-B-EXPLORE-PAID-ACQUISITION-B01"
    assert record["branch_statistic"] == "A_paid"
    assert record["competence_policy"].startswith("recorded, not required")
    assert record["index_law"]["offset"] == 2_000_000
    assert record["odd_training_even_held_out_separation"][
        "held_out_periods_used_in_training"] == []
    assert record["oracle_probe_contexts"] == [TARGET_CONTEXT_ID]
    assert record["oracle_at_target"]["net_acquisition"] == pytest.approx(0.021437, abs=5e-7)
    assert len(record["policies"]) == 6
    assert record["counts"]["environment_episodes"] == 3 * SMALL_EPISODES * len(CONTEXTS)
    assert record["counts"]["acquisition_audits"] == 12
    assert record["counts"]["exact_solves"] == 6 * 3
    assert record["counts"]["nonfinite_events"] == 0
    assert record["reading_rule"]["branch"] in {"PA-A", "PA-B", "PA-C", "PA-D", "PA-E"}
    assert record["admission"]["passed"] is True
    assert record["resource_telemetry"]["gating"] is False
    assert record["resource_telemetry"]["concurrent_load_declared"]

    for policy in record["policies"]:
        assert set(policy["arms"]) == {RUNNER.TREATMENT, RUNNER.REFERENCE}
        treatment = policy["arms"][RUNNER.TREATMENT]
        assert treatment["tail_reproduction"]["pass"] is True
        assert treatment["tail_reproduction"]["max_abs_difference"] <= 1e-6
        assert policy["arms"][RUNNER.REFERENCE]["d_learned_tail"] == 0.0
        for arm in policy["arms"].values():
            assert set(arm["a_paid"]["conjuncts"]) == {
                "pays_at_target", "target_delta_acquisition_positive",
                "direct_probe_component_negative", "refuses_everywhere_else"}
            assert arm["a_paid"]["conjuncts"]["direct_probe_component_negative"] is True
            assert arm["competence_record"]["gating"] is False
            assert arm["competence_record"]["recorded_under"].endswith("#11.1")
            assert arm["frozen_conditional_acquisition"]["gating"] is False
            assert isinstance(arm["frozen_conditional_acquisition"]["acquisition_pass"], bool)
            assert arm["acquisition"]["oracle_baseline_at_target"] == 0.794
            for stage in ("tail", "root"):
                check = policy["whitening"][stage]
                assert check["cholesky_reconstruction_max_abs"] <= 1e-10
                assert check["gram_smallest_eigenvalue"] > 1e-6

    exposure = record["exposure_line"]
    assert {row["arm"] for row in exposure["rows"]} == {RUNNER.TREATMENT}
    assert len(exposure["rows"]) == 12
    assert exposure["learner_can_move_in_its_budget"] is True
    assert SELECTION.OFFSET == 1_000_000


def test_a_perturbed_published_tail_quarantines_the_run(tmp_path, monkeypatch):
    monkeypatch.setattr(CR, "_configure_topology", lambda cap: None)
    reference = _miniature_reference(tmp_path / "reference.json")
    payload = json.loads(reference.read_text(encoding="utf-8"))
    payload["policies"][0]["arms"]["MARGIN-AWARE"]["beta_tail"][0] += 1e-3
    reference.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RUNNER.LaunchRefusal, match="tail-reproduction integrity item failed"):
        RUNNER.run_object(
            tmp_path / "mini2", thread_cap=1, episodes_per_context=SMALL_EPISODES,
            tail_updates=SMALL_TAIL_UPDATES, root_updates=SMALL_ROOT_UPDATES,
            remedies_record=reference)
    quarantines = list((tmp_path / "mini2").glob("quarantine-*/failure.json"))
    assert len(quarantines) == 1
    failure = json.loads(quarantines[0].read_text(encoding="utf-8"))
    assert failure["quarantined"] is True
    assert failure["quarantine_rule"] == "MARL_EMPIRICAL_EVIDENCE_SPEC.md#6.2"
    assert failure["no_rerun_with_changes"] is True
    assert not (tmp_path / "mini2" / "complete").exists()
    assert SELECTION.OFFSET == 1_000_000


def test_the_output_root_is_create_once(tmp_path):
    (tmp_path / "taken").mkdir()
    with pytest.raises(RUNNER.LaunchRefusal, match="create-once"):
        RUNNER.run_object(tmp_path / "taken")
