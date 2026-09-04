import copy
from fractions import Fraction

import pytest

from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.analysis import (
    AnalysisError,
    validate_registered_literal_inventory,
)

from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.contract import (
    NATIVE_REGISTRY_KEY,
    SPEC_SCHEMA,
    ContractError,
    canonical_json_bytes,
    parse_fraction_pair,
    registered_spec,
    structural_check,
    validate_public_history,
    validate_registered_spec,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.controllers import (
    last_ack_g_masses,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.reachable_twins import (
    full_bayes_k_erased_view,
    full_bayes_k_view,
    last_ack_bayes_view,
    last_ack_g_view,
    registered_twins,
)


def test_registered_spec_literal_histories_and_zero_learning_contract():
    spec = registered_spec()
    assert validate_registered_spec(spec) == spec
    assert spec["schema"] == SPEC_SCHEMA
    assert spec["native_registry_key"] == NATIVE_REGISTRY_KEY
    assert spec["zero_learning"] == {
        "scientific_rng_draws": 0,
        "seeds": [],
        "optimizers": 0,
        "updates": 0,
        "checkpoints": 0,
        "sampling": 0,
    }
    prior, duration = registered_twins(spec)
    assert [
        [(event["action"], event["ack"], event["completed_duration"]) for event in row.history["events"]]
        for row in prior.rows
    ] == [
        [("CENTER", "+", 4), ("CENTER", "+", 4), ("LEFT", "+", 4)],
        [("CENTER", "+", 4), ("CENTER", "-", 4), ("LEFT", "+", 4)],
    ]
    assert [
        [event["completed_duration"] for event in row.history["events"]]
        for row in duration.rows
    ] == [[4, 4, 12, 8], [4, 12, 4, 8]]
    assert all(row.population_weight == Fraction(1, 2) for twin in (prior, duration) for row in twin.rows)


def test_structural_check_never_reports_action_or_return_evaluation():
    receipt = structural_check(registered_spec())
    assert receipt["status"] == "STRUCTURALLY_VALID_PRE_RESULT_ONLY"
    assert receipt["controller_actions_evaluated"] == 0
    assert receipt["controller_returns_evaluated"] == 0
    assert receipt["result_bearing"] is False
    assert receipt["certification_executed"] is False


def test_views_drop_exactly_the_forbidden_information_without_reconstruction():
    prior, duration = registered_twins(registered_spec())
    assert full_bayes_k_view(duration.rows[0].history) != full_bayes_k_view(duration.rows[1].history)
    assert full_bayes_k_erased_view(duration.rows[0].history) == full_bayes_k_erased_view(duration.rows[1].history)
    erased = full_bayes_k_erased_view(duration.rows[0].history)
    assert 28 not in erased
    assert (4, 4, 12, 8) not in erased
    assert (4, 12, 4, 8) not in erased
    assert last_ack_bayes_view(prior.rows[0].history) == last_ack_bayes_view(prior.rows[1].history)
    assert last_ack_g_view(prior.rows[0].history) == last_ack_g_view(duration.rows[0].history)


def test_last_ack_g_exact_fractions_on_separate_test_only_packets():
    from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.contract import make_test_history

    positive = make_test_history("TEST_ONLY_G_POS", (8,), ("RIGHT",), ("+",))
    negative = make_test_history("TEST_ONLY_G_NEG", (12,), ("CENTER",), ("-",))
    assert last_ack_g_masses(positive) == (
        Fraction(17, 171),
        Fraction(17, 171),
        Fraction(137, 171),
    )
    assert last_ack_g_masses(negative) == (
        Fraction(52, 121),
        Fraction(17, 121),
        Fraction(52, 121),
    )


def test_schema_and_reduced_rational_validation_fail_closed():
    assert parse_fraction_pair([0, 1], "zero") == 0
    with pytest.raises(ContractError, match="reduced"):
        parse_fraction_pair([2, 6], "bad")
    spec = registered_spec()
    spec["support"]["twins"][0]["rows"][0]["population_weight"] = [2, 4]
    with pytest.raises(ContractError):
        validate_registered_spec(spec)


def test_clock_event_and_next_credit_fields_are_distinct_and_canonical():
    history = registered_twins(registered_spec())[0].rows[0].history
    assert validate_public_history(history)["history_id"] == "PRIOR_HISTORY_ACK_TWIN_A"
    event = history["events"][0]
    assert [
        event["action_event_index"],
        event["hold_completion_event_index"],
        event["motion_event_index"],
        event["ack_event_index"],
        event["private_update_event_index"],
    ] == [0, 1, 2, 3, 4]
    decision = history["decision"]
    assert decision["primitive_time"] == decision["next_hold_credit"]["primitive_start"]
    assert canonical_json_bytes(copy.deepcopy(history)) == canonical_json_bytes(history)


def test_registered_literal_inventory_rejects_substitute_prefix_before_arithmetic():
    spec = registered_spec()
    rows = []
    summaries = []
    for twin in spec["support"]["twins"]:
        summaries.append(
            {
                "twin_id": twin["twin_id"],
                "coarsened_controller": twin["coarsened_controller"],
            }
        )
        for row in twin["rows"]:
            rows.append(
                {
                    "twin_id": twin["twin_id"],
                    "side": row["side"],
                    "population_weight": row["population_weight"],
                    "expected_raw_action": row["expected_raw_action"],
                    "history": row["history"],
                }
            )
    validate_registered_literal_inventory(rows, summaries)
    substitute = copy.deepcopy(rows)
    substitute[0]["history"]["events"][0]["action"] = "RIGHT"
    with pytest.raises(AnalysisError, match="differs from specification"):
        validate_registered_literal_inventory(substitute, summaries)
