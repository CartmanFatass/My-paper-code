from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from itertools import product
import json

import pytest

from experiments.candidates.ucope import exact_enumerator as ucope


def _find(rows, bits):
    return next(row for row in rows if row.bits == bits)


def _scalar_signature(rows):
    return tuple(
        (
            row.bits,
            row.rho,
            row.hazard_s,
            row.hazard_l,
            row.ucope_s,
            row.ucope_l,
            row.cb_auc_action,
            row.sg_rate_action,
            row.action,
            row.expected_auc,
        )
        for row in rows
    )


def test_registered_audit_passes_exact_narrow_count_state_contract():
    result = ucope.run_registered_audit()

    assert result.terminal is ucope.Terminal.PASS
    assert len(result.rows) == 16
    assert result.expected_ucope_auc == Fraction(26571, 20000)
    assert result.expected_cb_auc == 1
    assert result.delta_auc == Fraction(6571, 20000)
    assert all(passed for _, passed in result.invariants)
    assert tuple(name for name, _ in result.invariants) == (
        "effective_period_quotient",
        "matched_history_h_s",
        "matched_history_h_l",
        "h_s_margin",
        "h_l_margin",
        "cb_auc_matched_actions",
        "exact_expected_auc",
        "exact_delta_auc",
        "homogeneous_boundary",
        "independent_redraw_boundary",
        "alias_split_merge",
        "censor_is_unknown",
        "pre_outcome_tape",
        "state_clone_order",
        "recurrence_version_closure",
        "partner_label_permutation",
    )


def test_matched_histories_have_exact_posterior_hazards_actions_and_margins():
    rows = ucope.enumerate_histories(ucope.build_family())
    h_s = _find(rows, (1, 1, 0, 0))
    h_l = _find(rows, (0, 0, 1, 1))

    assert h_s.ledger.opportunities == (1, 1, 1, 1)
    assert h_s.ledger.hits == (1, 1, 0, 0)
    assert h_s.outcomes == ("c1", "c2", None, None)
    assert h_s.rho == Fraction(6561, 6562)
    assert (h_s.hazard_s, h_s.hazard_l) == (
        Fraction(5905, 6562),
        Fraction(657, 6562),
    )
    assert h_s.action == ucope.S
    assert h_s.margin == Fraction(11153, 6562)

    assert h_l.ledger.hits == (0, 0, 1, 1)
    assert h_l.rho == Fraction(1, 6562)
    assert (h_l.hazard_s, h_l.hazard_l) == (
        Fraction(657, 6562),
        Fraction(5905, 6562),
    )
    assert h_l.action == ucope.L
    assert h_l.margin == Fraction(4591, 6562)
    assert h_s.cb_auc_action == h_l.cb_auc_action == ucope.S
    assert h_s.sg_rate_action == ucope.S
    assert h_l.sg_rate_action == ucope.L


def test_all_histories_are_exact_complete_and_canonical_output_is_byte_stable():
    family = ucope.build_family()
    rows = ucope.enumerate_histories(family)
    result = ucope.run_registered_audit()

    assert tuple(row.bits for row in rows) == tuple(product((0, 1), repeat=4))
    assert sum(row.prior_probability for row in rows) == 1
    assert all(row.cb_auc_action == ucope.S for row in rows)
    assert result.to_bytes() == ucope.run_registered_audit().to_bytes()

    payload = json.loads(result.to_bytes())
    assert payload["terminal"] == "PASS_NARROW_COUNT_STATE_RELEVANCE"
    assert payload["expected_ucope_auc"] == "26571/20000"
    assert payload["expected_cb_auc"] == "1"
    assert payload["delta_auc"] == "6571/20000"
    assert len(payload["rows"]) == 16
    assert set(payload["rows"][0]) == {
        "CB_AUC",
        "CB_AUC_action",
        "E",
        "N",
        "SG_RATE_action",
        "UCOPE",
        "action",
        "expected_fifth_trial_AUC",
        "hazards",
        "history",
        "history_bits",
        "margin",
        "prior_probability",
        "rho",
    }


def test_effective_period_alias_split_and_merge_are_execution_equivalent():
    split = ucope.build_family(split_long_alias=True)
    merged = ucope.build_family(split_long_alias=False)

    assert ucope.validate_family(split) == ()
    assert split.nominal("ell").effective == split.nominal("ell_prime").effective == ucope.L
    assert split.nominal("ell").duration == split.nominal("ell_prime").duration == 2
    assert split.nominal("ell").execution_law == split.nominal("ell_prime").execution_law
    assert _scalar_signature(ucope.enumerate_histories(split)) == _scalar_signature(
        ucope.enumerate_histories(merged)
    )

    broken_alias = replace(
        split.nominal("ell_prime"), execution_law=b"different-execution-law"
    )
    malformed = replace(split, nominals=(*split.nominals[:2], broken_alias))
    assert any("execution-law aliases" in issue for issue in ucope.validate_family(malformed))


def test_censoring_is_unknown_and_ledgers_are_immutable_and_version_closed():
    family = ucope.build_family()
    empty = ucope.Ledger.empty(family.version)
    censored = ucope.update_ledger(family, empty, family.trials[0], None)
    miss = ucope.update_ledger(family, empty, family.trials[0], False)
    hit = ucope.update_ledger(family, empty, family.trials[0], True)

    assert censored is empty
    assert empty.opportunities == empty.hits == (0, 0, 0, 0)
    assert miss.opportunities == (1, 0, 0, 0)
    assert miss.hits == (0, 0, 0, 0)
    assert hit.opportunities == hit.hits == (1, 0, 0, 0)
    with pytest.raises(ValueError, match="version mismatch"):
        ucope.update_ledger(
            family,
            ucope.Ledger.empty("other-version"),
            family.trials[0],
            True,
        )


def test_homogeneous_and_independent_redraw_boundaries_are_exact_zero_effect():
    homogeneous = ucope.enumerate_histories(
        ucope.build_family(homogeneous_hazards=True)
    )
    family = ucope.build_family()
    redraw = ucope.enumerate_histories(family, independent_redraw=True)

    for rows in (homogeneous, redraw):
        assert all(row.rho == Fraction(1, 2) for row in rows)
        assert all(row.hazard_s == row.hazard_l == Fraction(1, 2) for row in rows)
        assert all(row.action == ucope.S for row in rows)
        assert sum(row.prior_probability * row.expected_auc for row in rows) == 1
        assert sum(
            row.prior_probability * row.cb_auc_s for row in rows
        ) == 1


def test_pre_outcome_tape_state_clone_and_partner_labels_cannot_change_result():
    family = ucope.build_family()
    histories = tuple(product((0, 1), repeat=4))
    forward = ucope.enumerate_histories(family, history_order=histories)
    reverse = ucope.enumerate_histories(
        family, history_order=tuple(reversed(histories))
    )
    renamed = ucope.enumerate_histories(
        ucope.build_family(cells=("anonymous_y", "anonymous_x"))
    )

    assert _scalar_signature(forward) == _scalar_signature(reverse)
    assert _scalar_signature(forward) == _scalar_signature(renamed)
    assert tuple(trial.forced_nominal for trial in family.trials) == (
        "s",
        "s",
        "ell",
        "ell_prime",
        None,
    )
    assert all(
        row.ledger.version == family.version and row.ledger.opportunities == (1, 1, 1, 1)
        for row in forward
    )


@pytest.mark.parametrize(
    "malformed",
    (
        replace(ucope.build_family(), version=""),
        replace(ucope.build_family(), weights=(Fraction(1), Fraction(0))),
        replace(ucope.build_family(), structural_support=()),
        replace(ucope.build_family(), persistent_theta=False),
        replace(
            ucope.build_family(),
            trials=(
                replace(ucope.build_family().trials[0], limit=0),
                *ucope.build_family().trials[1:],
            ),
        ),
    ),
)
def test_family_contract_failures_stop_before_enumeration(malformed):
    assert ucope.validate_family(malformed)
    with pytest.raises(ValueError):
        ucope.enumerate_histories(malformed)
