from fractions import Fraction

import pytest

from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.contract import (
    make_test_history,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.native_backend import (
    MAX_HISTORY_EVENTS,
    NATIVE_REGISTRY_KEY,
    REFERENCE_FALLBACK_KEY,
    NativeBackendError,
    assert_native_reference_equivalent,
    evaluate_history,
    native_status,
)
from experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01.reference_host import (
    choose_action,
    history_path_mass,
    q_values,
    replay_full_bayes,
)


def _history(event_count=3):
    pattern = ((4, "LEFT", "+"), (8, "CENTER", "-"), (12, "RIGHT", "+"))
    rows = tuple(pattern[index % len(pattern)] for index in range(event_count))
    return make_test_history(
        "TEST_ONLY_NATIVE",
        tuple(row[0] for row in rows),
        tuple(row[1] for row in rows),
        tuple(row[2] for row in rows),
    )


def test_backend_result_equals_reference_on_test_only_fixture():
    history = _history()
    result = evaluate_history(history)
    posterior = replay_full_bayes(history)
    values = q_values(posterior, 4)
    action, value = choose_action(values)
    assert result.backend in {NATIVE_REGISTRY_KEY, REFERENCE_FALLBACK_KEY}
    assert result.history_mass == history_path_mass(history) > 0
    assert result.posterior == posterior
    assert result.q_values() == values
    assert (result.action, result.value) == (action, value)
    assert all(isinstance(item, Fraction) for item in result.posterior + result.q)


def test_compiled_backend_is_bit_exact_when_available():
    status = native_status()
    if not status["available"]:
        pytest.skip(str(status["failure"]))
    assert status["registry_key"] == NATIVE_REGISTRY_KEY
    assert_native_reference_equivalent(_history())


def test_exact_fallback_is_explicit_and_tightly_bounded():
    with pytest.raises(NativeBackendError, match=str(MAX_HISTORY_EVENTS)):
        evaluate_history(_history(MAX_HISTORY_EVENTS + 1))
