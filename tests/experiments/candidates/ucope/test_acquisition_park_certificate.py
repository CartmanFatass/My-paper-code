from __future__ import annotations

from fractions import Fraction
import json

from experiments.candidates.ucope import acquisition_park_certificate as cert
from experiments.candidates.ucope import exact_enumerator as d1


def test_certificate_confirms_park_with_all_invariants():
    result = cert.run_certificate()

    assert result.terminal is cert.Terminal.PARK
    assert all(passed for _, passed in result.invariants)
    assert tuple(name for name, _ in result.invariants) == (
        "lemma1_action_equivalent_signals",
        "lemma2_posterior_law_coupling",
        "lemma3_passive_dominance",
        "lemma3_greedy_dominance",
        "lemma4_no_horizon_rescue",
        "lemma4_regret_decomposition",
        "lemma4_regret_nonnegative_pointwise",
        "lemma4_partial_regret_paths_agree",
        "lemma4_bound_dominates_prefix_horizons",
        "exact_cal_table",
        "exact_cb_table",
        "exact_greedy_anchor",
        "commitment_signs",
        "exact_information_table",
        "decision_phase_learning_table",
        "full_tree_cross_check",
        "homogeneous_boundary_corrected",
        "independent_redraw_boundary_corrected",
        "severance_boundary_ties_g",
        "tie_unreachable",
        "greedy_rule_is_sign_rule",
        "no_identity_fields",
        "ceiling_containment",
    )


def test_exact_policy_value_tables_match_review_algebra():
    assert cert.v_cal(0) == 3
    assert cert.v_cal(1) == Fraction(86571, 20000)
    assert cert.v_cal(2) == Fraction(2834139, 500000)
    assert cert.v_cal(3) == Fraction(7011651, 1000000)
    assert cert.v_cal(4) == Fraction(41791887, 5000000)
    assert all(cert.v_cb(T) == 4 + T for T in cert.REGISTERED_T)
    assert cert.v_greedy(0) == Fraction(24107, 5000)
    assert cert.v_greedy(1) == Fraction(122999, 20000)
    assert cert.v_greedy(2) == Fraction(3744839, 500000)
    assert cert.v_greedy(3) == Fraction(8833051, 1000000)
    assert cert.v_greedy(4) == Fraction(50898887, 5000000)


def test_dominance_identities_hold_for_every_registered_horizon():
    for T in cert.REGISTERED_T:
        assert cert.v_cal(T) - cert.v_passive(T) == -1
        assert cert.v_cal(T) - cert.v_greedy(T) == Fraction(-9107, 5000)


def test_commitment_contrast_signs_and_threshold_are_exact():
    deltas = {T: cert.v_cal(T) - cert.v_cb(T) for T in cert.REGISTERED_T}
    assert deltas[0] == -1
    assert deltas[1] == Fraction(-13429, 20000)
    assert deltas[2] == Fraction(-165861, 500000)
    assert deltas[3] == Fraction(11651, 1000000)
    assert deltas[4] == Fraction(1791887, 5000000)
    assert min(T for T in (1, 2, 3, 4) if deltas[T] > 0) == 3


def test_gross_and_net_information_values_are_exact_and_never_recover_cost():
    expected = {
        0: Fraction(0),
        1: Fraction(6571, 20000),
        2: Fraction(219139, 500000),
        3: Fraction(506651, 1000000),
        4: Fraction(2684887, 5000000),
    }
    for T, value in expected.items():
        g = cert.gross_information_value(T)
        assert g == value
        assert g - 1 < 0
    assert cert.no_horizon_rescue_bound() < 1
    assert cert.cumulative_regret(cert.TAIL_T0) <= Fraction(5, 8)
    assert Fraction(5, 8) <= cert.no_horizon_rescue_bound()


def test_regret_machinery_is_pinned_exactly_and_nonnegative():
    assert cert.cumulative_regret(0) == 0
    assert cert.cumulative_regret(1) == Fraction(7, 20)
    assert cert.cumulative_regret(cert.TAIL_T0) == Fraction(
        156117267899, 250000000000
    )
    assert cert._exact_partial_regret(cert.TAIL_T0) == cert.cumulative_regret(
        cert.TAIL_T0
    )
    bound = cert.no_horizon_rescue_bound()
    for T in range(cert.TAIL_T0 + 3):
        value = cert.cumulative_regret(T)
        assert 0 <= value <= bound
    for T in cert.REGISTERED_T:
        law = cert.prefix_belief_law("SSLL")
        for (theta, z) in law:
            oracle = max(cert.reward(theta, action) for action in (cert.S, cert.L))
            assert T * oracle - cert._value(theta, z, (None,) * T, cert.PRIMARY) >= 0


def test_posterior_law_coupling_makes_prefix_actions_informationally_equal():
    ssll = cert.prefix_belief_law("SSLL")
    ssss = cert.prefix_belief_law("SSSS")
    greedy = cert.prefix_belief_law("GREEDY")
    assert ssll == ssss == greedy
    assert sum(ssll.values()) == 1
    assert {z for _, z in ssll} == {-4, -2, 0, 2, 4}
    for theta in cert.THETAS:
        assert cert.PRIMARY.evidence_up(theta, cert.S) == cert.PRIMARY.evidence_up(
            theta, cert.L
        )


def test_corrected_boundaries_replace_the_false_pairwise_zero_claims():
    for T in cert.REGISTERED_T:
        assert cert.v_cal(T, cert.HOMOGENEOUS) == 3 + T
        assert cert.v_passive(T, cert.HOMOGENEOUS) == 4 + T
        assert cert.v_greedy(T, cert.HOMOGENEOUS) == 4 + T
        assert cert.v_cb(T, cert.HOMOGENEOUS) == 4 + T
        assert cert.gross_information_value(T, cert.HOMOGENEOUS) == 0
        assert cert.v_cal(T, reset_belief=True) == 3 + T
        assert cert.v_greedy(T, reset_belief=True) == 4 + T
        assert cert.v_cal(T) - cert.v_cal_severed(T) == cert.gross_information_value(T)


def test_full_tree_enumeration_cross_checks_the_dynamic_program():
    for T in (0, 2, 4):
        for schedule in (
            cert.PREFIX_CAL + (None,) * T,
            cert.PREFIX_PASSIVE + (None,) * T,
            (None,) * (4 + T),
        ):
            value, mass = cert.full_tree_value(schedule)
            assert mass == 1
            assert value == cert._policy_value(schedule)


def test_greedy_rule_is_total_sign_rule_with_unreachable_tie():
    for z in range(-12, 13):
        assert cert.rule_action(z) == (cert.S if z >= 0 else cert.L)
    assert cert._reachable_tie_is_absent()


def test_tie_helper_actually_detects_a_forced_tie(monkeypatch):
    forced_rho = Fraction(7, 24)
    real_posterior = cert.posterior_s

    def tied_posterior(z, family=cert.PRIMARY):
        return forced_rho if z == 2 else real_posterior(z, family)

    monkeypatch.setattr(cert, "posterior_s", tied_posterior)
    score = cert._scores(forced_rho, cert.PRIMARY)
    assert score[cert.S] == score[cert.L]
    assert cert._reachable_tie_is_absent() is False


def test_certificate_binds_to_the_aligned_d1_family_constants():
    family = d1.build_family()
    assert family.hazards.s_given_s == cert.PRIMARY.aligned
    assert family.hazards.l_given_s == cert.PRIMARY.misaligned
    assert family.horizon == cert.HORIZON
    assert family.prior_s == cert.PRIOR_S
    assert family.nominal("s").duration == cert.DURATION[cert.S]
    assert family.nominal("ell").duration == cert.DURATION[cert.L]
    assert family.nominal("ell").execution_law == family.nominal("ell_prime").execution_law


def test_certificate_reproduces_the_externally_accepted_d1_numbers():
    audit = d1.run_registered_audit()
    assert audit.terminal is d1.Terminal.PASS
    assert cert.v_cal(1) - cert.v_cal(0) == audit.expected_ucope_auc
    assert cert.gross_information_value(1) == audit.delta_auc
    assert cert.v_cb(1) - cert.v_cb(0) == audit.expected_cb_auc


def test_canonical_output_is_byte_stable_compact_and_park_terminal():
    result = cert.run_certificate()
    raw = result.to_bytes()
    assert raw == cert.run_certificate().to_bytes()
    assert b", " not in raw and b": " not in raw
    payload = json.loads(raw)
    assert payload["binding"] == "ucope.acquisition_park_certificate.v1"
    assert payload["terminal"] == "PARK_CONFIRMED_FORCED_BALANCED_ACQUISITION_ROUTE"
    assert payload["no_rescue_bound"] == "156978910907/250000000000"
    assert [row["CAL_minus_CB"] for row in payload["commitment_value_vs_count_blind_S"]] == [
        "-1",
        "-13429/20000",
        "-165861/500000",
        "11651/1000000",
        "1791887/5000000",
    ]
    assert [row["N"] for row in payload["information"]] == [
        "-1",
        "-13429/20000",
        "-280861/500000",
        "-493349/1000000",
        "-2315113/5000000",
    ]
    for token in (b"partner", b"owner", b"roster", b"epoch"):
        assert token not in raw


def test_perturbed_noncomplementary_hazards_break_action_equivalence():
    perturbed = cert.HazardFamily(Fraction(9, 10), Fraction(2, 10))
    assert any(
        perturbed.evidence_up(theta, cert.S) != perturbed.evidence_up(theta, cert.L)
        for theta in cert.THETAS
    )
