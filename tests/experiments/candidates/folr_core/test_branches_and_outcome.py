"""Proof-sized tests for the FOLR branches, certificates and outcome controller.

Three tests carry the design.

``test_the_analytic_guarantee_matches_the_runtime`` checks External Pro's
central objection to the naive prototype: opposite head weights guarantee
nothing unless the payload really moves decoder coordinate zero through the GRU.
The cell's closed-form prediction ``2 * (GELU(2) - GELU(0))`` is compared to what
the actual actor path produces.  If the derivation in ``registration.py`` were
wrong, this is where it shows.

``test_the_write_hook_does_not_perturb_an_uninstrumented_run`` protects the
runtime change.  A hook that altered the path would invalidate every branch it
was supposed to witness.

``test_a_null_against_an_analytic_guarantee_is_an_engineering_failure`` pins
Pro's §6 qualification, which is the one routing rule that is easy to get
backwards: in a cell whose sensitivity is built in, no effect means the harness
is broken, not that the runtime lacks the access.
"""

from __future__ import annotations

import importlib.util
import math
import pathlib

import numpy as np
import pytest
import torch

from experiments.candidates.folr_core import branches as br
from experiments.candidates.folr_core import certificates as ct
from experiments.candidates.folr_core import outcome as oc
from experiments.candidates.folr_core import registration as reg
from experiments.candidates.folr_core import reset_manifest as rm
from ha_ctse_process import variable_roster_event as vre

_HELPER_PATH = (
    pathlib.Path(__file__).resolve().parents[4]
    / "tests"
    / "process"
    / "variable_roster"
    / "ha_ctse_process_variable_roster_event_test.py"
)
_spec = importlib.util.spec_from_file_location("_folr_vre_helpers", _HELPER_PATH)
_helpers = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_helpers)


@pytest.fixture(scope="module")
def development():
    registration = reg.development_registration()
    results = br.execute_all(registration)
    return {
        "registration": registration,
        "results": results,
        "contrasts": br.contrasts(results),
        "certificates": ct.certify_all(results, registration=registration),
    }


# --------------------------------------------------------------------------
# The runtime write point
# --------------------------------------------------------------------------


def test_the_write_hook_does_not_perturb_an_uninstrumented_run():
    """With no hook installed the path must be byte-identical to before."""
    plain = _helpers.make_core()
    _helpers.initial_join(plain)

    hooked = _helpers.make_core()
    hooked.install_preframe_intervention(lambda core: None)
    _helpers.initial_join(hooked)

    assert len(plain.high_ledger) == len(hooked.high_ledger)
    for left, right in zip(plain.high_ledger, hooked.high_ledger):
        assert left.combined_action == right.combined_action
        assert left.sampled_order == right.sampled_order
        assert left.sampled_replacement_gap == right.sampled_replacement_gap
        assert left.old_token_log_probability == right.old_token_log_probability
        assert np.array_equal(left.pre_token_high_hidden, right.pre_token_high_hidden)


def test_the_write_hook_fires_once_after_the_commit_and_before_any_token():
    """Pro's registered temporal boundary, checked rather than assumed."""
    core = _helpers.make_core()
    observed: list[dict[str, object]] = []

    def intervention(hooked: vre.VariableRosterEventCore) -> None:
        observed.append(
            {
                # committed: the joining records already exist
                "records": tuple(sorted(hooked.records)),
                # and no token has been processed yet
                "ledger_rows": len(hooked.high_ledger),
            }
        )

    core.install_preframe_intervention(intervention)
    _helpers.initial_join(core, keys=("a", "b"))

    assert len(observed) == 1, "the hook must fire exactly once per transaction"
    assert observed[0]["records"] == ("a", "b"), "membership was not yet committed"
    assert observed[0]["ledger_rows"] == 0, "a token was processed before the hook"
    assert len(core.high_ledger) == 2


def test_clearing_the_write_hook_restores_the_unmodified_path():
    core = _helpers.make_core()
    core.install_preframe_intervention(lambda c: None)
    core.install_preframe_intervention(None)
    assert core._preframe_intervention is None
    _helpers.initial_join(core)
    assert len(core.high_ledger) == 2


# --------------------------------------------------------------------------
# The cell
# --------------------------------------------------------------------------


def test_the_analytic_guarantee_matches_the_runtime(development):
    """Pro: opposite head weights alone guarantee nothing.

    The registered cell claims, in closed form, that swapping h0 for h1 moves
    ``logit_0 - logit_1`` by exactly ``2 * (GELU(2) - GELU(0))``.  This compares
    that derivation to what the real actor path produces.
    """
    results = development["results"]

    def separation(name: str) -> float:
        logits = results[name].kernel.masked_logits
        return float(logits[0] - logits[1])

    measured = separation("K_1_0") - separation("K_0_0")
    assert measured == pytest.approx(reg.ANALYTIC_LOGIT_SEPARATION, abs=1e-5)
    # ...and the same holds in the other provenance branch.
    assert separation("K_1_1") - separation("K_0_1") == pytest.approx(
        reg.ANALYTIC_LOGIT_SEPARATION, abs=1e-5
    )


def test_the_gelu_witness_is_the_erf_form_torch_uses():
    """A tanh-approximated GELU would make the closed form subtly wrong."""
    for value in (-1.0, 0.0, 0.5, 2.0, 3.0):
        assert reg._gelu(value) == pytest.approx(
            float(torch.nn.functional.gelu(torch.tensor(value, dtype=torch.float64))),
            abs=1e-12,
        )


def test_the_payload_vectors_differ_only_in_the_focal_coordinate():
    """Pro: complementary coordinates must be controlled, not left to chance."""
    h0, h1, neutral = reg.payload_vectors(10)
    for other in (h1, neutral):
        assert np.array_equal(
            np.delete(h0, reg.FOCAL_COORDINATE), np.delete(other, reg.FOCAL_COORDINATE)
        )
    assert h0[reg.FOCAL_COORDINATE] != h1[reg.FOCAL_COORDINATE]
    # ...and h0 is not the record's default all-zero hidden state, so a payload
    # that silently failed to install could not masquerade as h0.
    assert np.any(h0 != 0.0)


def test_the_gate_witness_is_the_gate_the_gru_actually_evaluates():
    """The defect Pro found: a bias-only witness is not the update gate.

    ``weight_hh[:, 0] = 0`` stops h_0 reaching any gate but leaves the rest of
    the focal update-gate ROW intact, so the preactivation is

        20 + sum_{j>=1} W_hh[0, j] * h_j

    and the nonfocal payload coordinates are deliberately nonzero.  The old
    witness reported ``sigmoid(bias_ih + bias_hh)`` and called it z0, which
    omits that term entirely -- it happened to be right and was not proved.

    The input row must be zero for this to be certifiable at all: with a
    nonzero ``W_ih[row, :]`` the preactivation would depend on the member
    embedding, and no registration-only witness could establish it.
    """
    registration = reg.development_registration()
    gate = registration.weight_witness["focal_update_gate"]

    assert gate["update_gate_input_row_is_zero"], (
        "with a nonzero input row the gate depends on the member embedding"
    )
    assert gate["update_gate_bias_sum"] == pytest.approx(reg.UPDATE_GATE_BIAS)
    assert len(gate["focal_update_gate_recurrent_row"]) == 10
    assert gate["focal_update_gate_recurrent_row"][reg.FOCAL_COORDINATE] == 0.0

    # The recurrent term is REAL -- if it were identically zero the old
    # bias-only witness would have been correct by accident and this test would
    # not be testing anything.
    contributions = {
        row["recurrent_contribution"] for row in gate["per_payload"].values()
    }
    assert contributions != {0.0}
    # ...and identical across the three payloads, which differ only in the
    # focal column that the recurrent row zeroes.
    assert len(contributions) == 1
    assert gate["preactivation_equal_across_payloads"]

    assert set(gate["per_payload"]) == {"h0", "h1", "h_neutral"}
    for row in gate["per_payload"].values():
        assert row["z0"] == 1.0
        assert row["z0_is_bitwise_one"]
    assert gate["exact_carry_established"]
    assert gate["preactivation_headroom_over_threshold"] > 0.0


def test_the_analytic_separation_refuses_a_gate_that_does_not_carry_exactly():
    """Fail closed: the exact-carry number must not survive its premise."""
    registration = reg.development_registration()
    gate = dict(registration.weight_witness["focal_update_gate"])
    gate["exact_carry_established"] = False
    with pytest.raises(reg.ExactCarryNotEstablished, match="re-derived"):
        reg.analytic_logit_separation({"focal_update_gate": gate})


def test_the_cell_isolates_the_focal_coordinate():
    """The weight witness must reflect the surgery that was actually applied."""
    registration = reg.development_registration()
    witness = registration.weight_witness
    assert witness["focal_coordinate"] == reg.FOCAL_COORDINATE
    assert not witness["gate_reads_focal_hidden"]
    assert witness["decoder_rows_reading_focal"] == 1
    column = witness["skill_head_focal_column"]
    assert column[0] == pytest.approx(1.0)
    assert column[1] == pytest.approx(-1.0)
    assert all(value == 0.0 for value in column[2:])


# --------------------------------------------------------------------------
# The eight branches
# --------------------------------------------------------------------------


def test_there_are_exactly_four_transplant_two_reset_and_two_wrong_owner():
    kinds = [spec.kind for spec in br.BRANCHES]
    assert kinds.count(br.TRANSPLANT) == 4
    assert kinds.count(br.RESET) == 2
    assert kinds.count(br.WRONG_OWNER) == 2
    assert len(br.BRANCHES) == 8


def test_the_two_provenance_histories_really_differ(development):
    """If the histories were identical the fixed-payload nulls prove nothing."""
    registration = development["registration"]
    left = br.common_snapshot(registration, branch=0)
    right = br.common_snapshot(registration, branch=1)
    assert left.digest() != right.digest(), (
        "the provenance branches must leave a real residue, or K_{p,0}=K_{p,1} "
        "is a tautology"
    )


def test_the_histories_are_erased_at_the_actor_read_boundary(development):
    """...and the residue must not reach the actor. Certified, not assumed."""
    results = development["results"]
    assert (
        results["K_0_0"].kernel.actor_preimage_digest
        == results["K_0_1"].kernel.actor_preimage_digest
    )
    assert (
        results["K_1_0"].kernel.actor_preimage_digest
        == results["K_1_1"].kernel.actor_preimage_digest
    )


def test_no_randomness_is_consumed_before_the_capture(development):
    """teacher order + teacher actions must leave the action RNG untouched."""
    for result in development["results"].values():
        evidence = result.evidence
        assert evidence["policy_action_uniform"] is None
        assert (
            ct.rng_state_digest(evidence["rng_states_before"]["action_rng"])
            == ct.rng_state_digest(evidence["rng_states_after"]["action_rng"])
        )
        assert evidence["token_position"] == 0
        assert evidence["sampled_order"][0] == (
            development["registration"].binding.target_lifecycle_key
        )


def test_the_wrong_owner_payload_reaches_the_critic_but_not_the_target(development):
    """The non-vacuity check for W_0 = W_1, and a correction to an assumption.

    Pro warned that "the event critic does read the active high-hidden array
    before the target logits are calculated", and required the comparison to be
    on the target's probability vector rather than on every row field.  That
    caution is sound, but the runtime turns out to be *stricter* than it needs
    to be: ``EventHighCritic.values`` concatenates each row's own
    ``high_hidden`` into that row's value input, and set-aggregates only the
    encoded critic-member features.  So the shadow's payload moves the SHADOW's
    value and leaves the TARGET's value bit-identical.

    The test asserts both halves, because the interesting one is easy to lose:
    if the shadow's value did not move, the payload never reached the critic at
    all and W_0 = W_1 would be vacuous.
    """
    registration = development["registration"]
    target = registration.binding.target_lifecycle_key
    shadow = registration.binding.shadow_lifecycle_key

    values = {}
    for name in ("W_0", "W_1"):
        core = development["results"][name].evidence["core"]
        rows = {row.owner_lifecycle_key: row for row in core.high_ledger}
        values[name] = (rows[target].old_owner_value, rows[shadow].old_owner_value)

    assert values["W_0"][1] != values["W_1"][1], (
        "the shadow payload never reached the critic; the null is vacuous"
    )
    assert values["W_0"][0] == values["W_1"][0], (
        "the shadow payload reached the target's critic value"
    )
    assert development["contrasts"]["wrong_owner_null"]["probabilities_bitwise_equal"]


def test_the_reset_branches_hold_the_target_at_the_neutral_payload(development):
    registration = development["registration"]
    neutral = registration.binding.payload("h_neutral")
    for name in ("R_0", "R_1"):
        row = development["results"][name].row
        assert np.array_equal(row.pre_token_high_hidden, neutral)


# --------------------------------------------------------------------------
# Certificates
# --------------------------------------------------------------------------


def test_every_branch_is_fresh_and_replays(development):
    certificates = development["certificates"]
    assert certificates["all_direct_replay_agree"]
    assert set(certificates["freshness_terminals"].values()) == {"FRESH"}


def test_the_reconstructed_history_profile_leaves_condition_nine_unresolved():
    """It must not pass vacuously under a reading Pro has not selected."""
    registration = reg.build_registration(
        cell_identifier="DEVELOPMENT_ONLY_profile_probe",
        target="dev_target",
        shadow="dev_shadow",
        model_seed=1_234_567,
        normalization_profile=rm.RECONSTRUCTED_HISTORY,
        development_only=True,
    )
    result = br.execute_branch(registration, br.BRANCHES[0])
    certificate = ct.freshness_certificate(
        result.evidence, registration=registration
    )
    assert certificate["terminal"] == "FRESHNESS_UNRESOLVED"
    assert certificate["unresolved"] == [
        "pcg64_pre_states_match_the_common_manifest"
    ]
    assert not certificate["failed"]


def test_the_freshness_certificate_names_the_condition_that_failed(development):
    evidence = dict(development["results"]["K_0_0"].evidence)
    evidence["token_position"] = 3
    certificate = ct.freshness_certificate(
        evidence, registration=development["registration"]
    )
    assert certificate["terminal"] == "NOT_FRESH"
    assert certificate["failed"] == ["token_position_is_zero"]


# --------------------------------------------------------------------------
# The outcome controller
# --------------------------------------------------------------------------


def _decide(development, **overrides):
    contrasts = {**development["contrasts"], **overrides}
    registration = development["registration"]
    return oc.decide(
        results=development["results"],
        contrasts=contrasts,
        certificates=development["certificates"],
        registration=registration,
        # Pro §6C: an accepting terminal requires the executed registration to
        # equal the approved one, so every decide() call must name it.
        expected_registration_digest=registration.registration_digest(),
    )


def test_the_development_cell_can_never_yield_a_scientific_conclusion(development):
    report = _decide(development)
    assert report["terminal"] == oc.INTERFACE_INSUFFICIENT
    assert report["harness_terminal"] == oc.NARROW_CLAIM_SUPPORTED
    assert "development_only_override" in report
    assert report["explicitly_forbidden"] == oc.FORBIDDEN[oc.INTERFACE_INSUFFICIENT]


def test_a_bitwise_null_is_an_engineering_failure_but_not_a_contradiction(development):
    """Pro's §6 qualification, with the overreach removed.

    The first pass called a null a *contradiction* of the analytic construction.
    Pro rejected that: the derivation bounds a logit displacement, and

        it may be called a mathematical contradiction only after adding a
        finite-precision probability-separation witness that rules out softmax
        saturation, underflow, and rounding

    which this registration does not carry.  So the terminal is unchanged and
    the WORDING is the thing under test.
    """
    report = _decide(development, payload_contrast={"b0": 0.0, "b1": 0.0})
    assert report["harness_terminal"] == oc.INTERFACE_INSUFFICIENT
    assert "inconsistent with the intended positive-control realization" in (
        report["reason"]
    )
    assert "may NOT be called a mathematical contradiction" in report["reason"]


def test_a_sub_margin_contrast_is_neither_a_refutation_nor_a_contradiction(development):
    """The band Pro added: nonzero dependence below the materiality threshold.

    Routing this to engineering failure is right; routing it there *because the
    logit construction was contradicted* is not, because a third dominant logit
    can hold both softmax vectors within 1e-3 while logit_0 - logit_1 moves by
    3.909.
    """
    margin = development["registration"].delta_cell
    report = _decide(
        development, payload_contrast={"b0": margin / 2.0, "b1": margin / 3.0}
    )
    assert report["harness_terminal"] == oc.PAYLOAD_DEPENDENCE_BELOW_MATERIALITY
    assert "below the prospectively registered probability-space materiality" in (
        report["reason"]
    )
    assert "neither a refutation nor a contradiction" in report["reason"]
    assert "contradict" not in report["reason"].split("neither")[0]


def test_the_sub_margin_terminal_is_not_an_engineering_failure():
    """Pro §6: routing a genuine sub-threshold effect there was inconsistent.

    ``INTERFACE_OR_INSTANCE_INSUFFICIENT`` has ceiling "Engineering failure or
    unexecuted design only" and forbids any scientific positive, while the
    sub-margin reason asserts that the cell DOES exhibit payload dependence.
    Both cannot describe one result, so the band has its own terminal.
    """
    ceiling = oc.MAXIMUM_CONCLUSION[oc.PAYLOAD_DEPENDENCE_BELOW_MATERIALITY]
    assert "kernels differ" in ceiling
    assert "Engineering failure" not in ceiling
    forbidden = oc.FORBIDDEN[oc.PAYLOAD_DEPENDENCE_BELOW_MATERIALITY]
    assert "NARROW_CLAIM_SUPPORTED" in forbidden
    assert "materially large" in forbidden


def test_the_positive_terminal_uses_the_minimum_over_b(development):
    """min_b, not "b0 happens to be large": one weak arm must block the claim."""
    margin = development["registration"].delta_cell
    report = _decide(development, payload_contrast={"b0": 1.0, "b1": margin / 2.0})
    assert report["harness_terminal"] == oc.PAYLOAD_DEPENDENCE_BELOW_MATERIALITY


def test_a_null_without_an_analytic_guarantee_is_a_refutation(development):
    """Only a cell that guarantees nothing can support the negative terminal."""
    from dataclasses import replace

    registration = replace(
        development["registration"], analytic_logit_separation=0.0
    )
    report = oc.decide(
        results=development["results"],
        contrasts={**development["contrasts"], "payload_contrast": {"b0": 0.0, "b1": 0.0}},
        certificates=development["certificates"],
        registration=registration,
        # The replaced registration is a DIFFERENT registration, so its own
        # digest is the precommitment here -- not the unmodified one.
        expected_registration_digest=registration.registration_digest(),
    )
    assert report["harness_terminal"] == oc.PAYLOAD_ACCESS_REFUTED


def test_a_broken_closure_control_outranks_the_payload_contrast(development):
    """Precedence: closure controls are checked before the contrast."""
    broken = [
        {**entry, "probabilities_bitwise_equal": False}
        for entry in development["contrasts"]["fixed_payload_nulls"]
    ]
    report = _decide(development, fixed_payload_nulls=broken)
    assert report["harness_terminal"] == oc.FIXED_PAYLOAD_NULL_FAILURE


def test_a_broken_reset_null_is_reported_separately(development):
    report = _decide(
        development,
        reset_null={
            **development["contrasts"]["reset_null"],
            "probabilities_bitwise_equal": False,
        },
    )
    assert report["harness_terminal"] == oc.RESET_NULL_FAILURE


def test_interface_validity_outranks_everything(development):
    certificates = {
        **development["certificates"],
        "all_direct_replay_agree": False,
    }
    registration = development["registration"]
    report = oc.decide(
        results=development["results"],
        contrasts=development["contrasts"],
        certificates=certificates,
        registration=registration,
        expected_registration_digest=registration.registration_digest(),
    )
    assert report["harness_terminal"] == oc.INTERFACE_INSUFFICIENT
    # The reason names WHICH gate failed; a bare "interface validity failed"
    # sends the reader back to the gate list to find out what broke.
    assert report["reason"] == (
        "interface validity failed: ['direct_replay_agree']"
    )


def test_an_unnamed_precommitment_cannot_reach_an_accepting_terminal(development):
    """Pro §6C: the executed registration must equal the approved one.

    Omitting the precommitted digest is not a neutral default -- it means
    nothing pinned which registration was approved, so the run cannot accept.
    """
    report = oc.decide(
        results=development["results"],
        contrasts=development["contrasts"],
        certificates=development["certificates"],
        registration=development["registration"],
    )
    assert report["harness_terminal"] == oc.INTERFACE_INSUFFICIENT
    assert "registration_digest_equals_the_precommitment" in report["reason"]


def test_an_amended_registration_fails_against_the_old_precommitment(development):
    """The gate has to catch a real amendment, not just a missing argument."""
    from dataclasses import replace

    amended = replace(development["registration"], delta_cell=1e-2)
    assert amended.registration_digest() != (
        development["registration"].registration_digest()
    )
    report = oc.decide(
        results=development["results"],
        contrasts=development["contrasts"],
        certificates=development["certificates"],
        registration=amended,
        expected_registration_digest=(
            development["registration"].registration_digest()
        ),
    )
    assert report["harness_terminal"] == oc.INTERFACE_INSUFFICIENT
    assert "registration_digest_equals_the_precommitment" in report["reason"]


# --------------------------------------------------------------------------
# Pro's bounded amendment, §6A--§6G
# --------------------------------------------------------------------------


def test_the_identifying_closure_holds_at_fixed_b(development):
    """§6A, which Pro called "the most important missing gate".

    The fixed-payload nulls vary B at a held payload.  This one varies the
    payload at a held B, and it is the one that licenses attributing the
    contrast to S03: if anything other than the payload differed between
    K_0_b and K_1_b, the contrast would not be identified.
    """
    entries = development["contrasts"]["payload_closure"]
    assert [entry["pair"] for entry in entries] == [
        ["K_0_0", "K_1_0"],
        ["K_0_1", "K_1_1"],
    ]
    for entry in entries:
        assert entry["actor_preimage_digests_equal"], entry["pair"]
        assert entry["common_snapshot_digests_equal"], entry["pair"]
        assert entry["model_state_digests_equal"], entry["pair"]
        assert entry["legal_masks_equal"], entry["pair"]
        assert entry["target_identity_equal"], entry["pair"]


def test_the_fixed_b_closure_is_not_vacuous(development):
    """It must be able to fail, and it must outrank the contrast when it does.

    ``actor_preimage_digest`` excludes ``pre_token_high_hidden`` by design --
    otherwise the payload arms could never compare equal and the gate would be
    a tautology in the other direction.  So the assertion worth making is that
    a broken closure changes the terminal.
    """
    broken = [
        {**entry, "actor_preimage_digests_equal": False}
        for entry in development["contrasts"]["payload_closure"]
    ]
    report = _decide(development, payload_closure=broken)
    assert report["harness_terminal"] == oc.FIXED_PAYLOAD_NULL_FAILURE


def test_the_preimage_digest_would_notice_a_non_s03_difference():
    """Sanity on the instrument: the digest is not blind to everything.

    Equality across the payload arms only means something if the digest moves
    when a genuinely different actor input is present.  S03 is excluded on
    purpose -- everything else must register.
    """
    import experiments.candidates.folr_core.s03_binding as sb

    base = {
        "pre_token_high_hidden": np.zeros(4, dtype=np.float32),
        "observations": np.asarray([[0.1, 0.2]], dtype=np.float32),
        "working_skills": (1,),
        "owner_lifecycle_key": "dev_target",
    }
    assert sb.actor_preimage_digest(base) == sb.actor_preimage_digest(
        {**base, "pre_token_high_hidden": np.ones(4, dtype=np.float32)}
    ), "S03 must be excluded, or the closure certificate is a tautology"
    assert sb.actor_preimage_digest(base) != sb.actor_preimage_digest(
        {**base, "working_skills": (2,)}
    )
    assert sb.actor_preimage_digest(base) != sb.actor_preimage_digest(
        {**base, "observations": np.asarray([[0.1, 0.3]], dtype=np.float32)}
    )


def test_the_shadow_payload_never_enters_the_targets_actor_preimage(development):
    """A stronger owner-locality statement than the ruling assumed was needed.

    Pro's §5 kept the wrong-owner branches after finding that the critic reads
    each row's own ``high_hidden``.  Measured here: K_0_0 and W_0 -- which
    differ in the target's payload AND in the shadow's private recurrent field
    -- produce the SAME non-S03 actor preimage digest.  The shadow's payload
    does not reach the target's actor inputs at all; only the shadow's encoded
    member features do, and those are unchanged.

    This is why the wrong-owner null is a test of the runtime rather than of
    the digest: the two W branches are compared on the target's probability
    vector, and the preimage equality is a control that cannot fail for the
    trivial reason that the digest ignores the difference -- it ignores it
    because the actor does.
    """
    kernels = {
        name: development["results"][name].kernel
        for name in ("K_0_0", "W_0", "W_1")
    }
    assert kernels["W_0"].actor_preimage_digest == kernels["W_1"].actor_preimage_digest
    assert (
        kernels["K_0_0"].actor_preimage_digest == kernels["W_0"].actor_preimage_digest
    )
    # ...and the kernels themselves still differ, because K_0_0 carries h0 in
    # the TARGET's field while W_0 holds the target at h_neutral.
    assert not np.array_equal(
        development["results"]["K_0_0"].kernel.probabilities,
        development["results"]["W_0"].kernel.probabilities,
    )


def test_the_payload_read_certificate_covers_all_eight_branches(development):
    """§6B: which vector actually reached the token, not which was registered."""
    certificates = development["certificates"]
    assert certificates["all_payload_reads_certified"]
    assert set(certificates["payload_read_terminals"]) == {
        spec.name for spec in br.BRANCHES
    }
    expected = {
        "K_0_0": "h0", "K_1_0": "h1", "K_0_1": "h0", "K_1_1": "h1",
        "R_0": "h_neutral", "R_1": "h_neutral",
        "W_0": "h_neutral", "W_1": "h_neutral",
    }
    for name, slot in expected.items():
        entry = certificates["branches"][name]["payload_read"]
        assert entry["expected_target_slot"] == slot
        assert entry["terminal"] == "PAYLOAD_READ_CERTIFIED"


def test_the_wrong_owner_branches_certify_the_shadow_payload(development):
    """W_p is only information-matched if h_p really reached the SHADOW."""
    binding = development["registration"].binding
    import experiments.candidates.folr_core.s03_binding as sb

    for name, slot in (("W_0", "h0"), ("W_1", "h1")):
        entry = development["certificates"]["branches"][name]["payload_read"]
        assert entry["shadow_active_hidden_digest"] == sb.vector_digest(
            binding.payload(slot)
        )


def test_a_wrong_payload_read_is_caught(development):
    """Relabel K_0_0 as a K_1 branch: the certificate must refuse it."""
    from dataclasses import replace

    result = development["results"]["K_0_0"]
    mislabelled = replace(
        result, spec=replace(result.spec, name="K_1_0", payload_slot="h1")
    )
    certificate = ct.payload_read_certificate(
        mislabelled, registration=development["registration"]
    )
    assert certificate["terminal"] == "PAYLOAD_READ_NOT_CERTIFIED"
    assert certificate["failed"] == ["target_pre_hidden_is_the_registered_payload"]


def test_the_shadow_row_is_bound_by_key_and_epoch(development):
    """Pro §5: certifying a hidden vector without certifying whose it is.

    ``keys.index(shadow)`` finds a row; it does not establish that the row
    belongs to the registered shadow *epoch*.  The identity is now read as the
    (key, epoch) pair at that same index, so the vector and the identity
    provably come from one row.
    """
    binding = development["registration"].binding
    for name, entry in development["certificates"]["branches"].items():
        condition = entry["payload_read"]["conditions"][
            "shadow_row_is_the_registered_owner_and_epoch"
        ]
        assert condition["state"] == "PASS", name

    for evidence in (r.evidence for r in development["results"].values()):
        keys = tuple(evidence["active_lifecycle_keys"])
        epochs = tuple(evidence["active_membership_epochs"])
        assert len(keys) == len(epochs)
        index = keys.index(binding.shadow_lifecycle_key)
        assert epochs[index] == binding.shadow_membership_epoch


def test_a_shadow_at_the_wrong_epoch_fails_the_interface_gate(development):
    """The gate must catch a right-key/wrong-epoch row, not just a missing key."""
    tampered = {}
    for name, result in development["results"].items():
        evidence = dict(result.evidence)
        evidence["active_membership_epochs"] = tuple(
            epoch + 7 for epoch in evidence["active_membership_epochs"]
        )
        tampered[name] = type(result)(
            spec=result.spec, kernel=result.kernel, row=result.row, evidence=evidence
        )
    registration = development["registration"]
    report = oc.decide(
        results=tampered,
        contrasts=development["contrasts"],
        certificates=development["certificates"],
        registration=registration,
        expected_registration_digest=registration.registration_digest(),
    )
    assert report["harness_terminal"] == oc.INTERFACE_INSUFFICIENT
    assert "shadow_resolves_to_the_registered_owner_and_epoch" in report["reason"]


def test_the_complete_rng_state_is_compared_not_the_counter_subfield():
    """§6D. The cached-uint32 fields are part of the state and must count.

    Two PCG64 mappings can share the counter pair and still differ in
    ``has_uint32``/``uinteger`` -- which is the difference between "the next
    draw comes from a cached half-word" and "it does not".  The old comparison
    read only the nested "state" member and would have called these equal.
    """
    left = {
        "bit_generator": "PCG64",
        "state": {"state": 12345, "inc": 67890},
        "has_uint32": 0,
        "uinteger": 0,
    }
    right = {**left, "has_uint32": 1, "uinteger": 4_294_967_295}
    assert left["state"] == right["state"]
    assert ct.rng_state_digest(left) != ct.rng_state_digest(right)
    assert ct.rng_state_digest(left) == ct.rng_state_digest(dict(left))


def test_the_reset_control_closes_on_its_inputs_too(development):
    """§6F: equal kernels can come from cancellation over unequal inputs."""
    gates = oc._reset_gates(development["contrasts"])
    assert [gate.name for gate in gates] == [
        "reset_null_R_0_R_1",
        "reset_actor_preimage_digests_equal",
        "reset_common_snapshot_digests_equal",
    ]
    assert all(gate.passed for gate in gates)

    report = _decide(
        development,
        reset_null={
            **development["contrasts"]["reset_null"],
            # kernels still equal; the INPUTS disagree
            "common_snapshot_digests_equal": False,
        },
    )
    assert report["harness_terminal"] == oc.RESET_NULL_FAILURE


def test_the_executed_model_must_be_the_registered_one(development):
    """§4: eight branches could share the same WRONG model and pass identity."""
    registered = development["registration"].weight_witness["model_state_digest"]
    for result in development["results"].values():
        assert result.evidence["model_state_digest_before"] == registered


def test_the_object_graph_scope_is_inside_the_registration_digest():
    """§3/§6G: the scope must be frozen, not merely documented."""
    from dataclasses import replace

    registration = reg.development_registration()
    widened = replace(
        registration,
        object_graph_scope={
            **registration.object_graph_scope,
            "excludes": ("environment return",),
        },
    )
    assert widened.registration_digest() != registration.registration_digest()

    record = registration.frozen_record()
    assert record["object_graph_scope"]["excludes"] == [
        "DynamicRosterEventEnv",
        "environment return",
        "environment task dynamics",
    ]
    sentence = record["object_graph_scope"]["admissible_positive_sentence"]
    assert sentence.startswith("VariableRosterEventCore")
    assert "DynamicRosterEventEnv" not in sentence


def test_the_source_identity_covers_the_whole_executable_graph():
    """Two dependencies the first pass missed, both found by Pro.

    ``variable_roster_event_support.normalized_log_age`` is called by
    ``encode_members``, so a change there moves the member embedding, the set
    summary, the logits and the kernel without touching any of the three files
    that were fingerprinted.  And freezing the actor path while leaving
    ``branches.py`` / ``certificates.py`` / ``outcome.py`` free freezes the
    wrong half: the executable scientific proposition could change with the
    registration data intact.
    """
    registration = reg.development_registration()
    identity = registration.source_identity

    assert "ha_ctse_process/variable_roster_event_support.py" in (
        reg.ACTOR_PATH_SOURCES
    )
    for module in ("branches.py", "certificates.py", "outcome.py"):
        assert f"experiments/candidates/folr_core/{module}" in reg.HARNESS_SOURCES
    assert set(reg.SCIENTIFIC_GRAPH_SOURCES) == (
        set(reg.ACTOR_PATH_SOURCES) | set(reg.HARNESS_SOURCES)
    )

    assert len(identity["scientific_graph_fingerprint"]) == 64
    assert set(identity["registered_sources"]) == set(reg.SCIENTIFIC_GRAPH_SOURCES)
    for digest in identity["registered_sources"].values():
        assert len(digest) == 64
    # The finite-precision claims are library-dependent.
    assert identity["torch_version"] and identity["numpy_version"]
    # A commit hash from a dirty tree authenticates nothing, so the record has
    # to say which case it is instead of implying the stronger one -- and the
    # flag is named for what it measures, which is the registered sources and
    # not the whole tree.
    assert "source_tree_dirty" not in identity
    assert identity["commit_authenticates_the_registration"] is (
        identity["source_commit"] != "UNAVAILABLE"
        and identity["registered_sources_dirty"] is False
    )


def test_a_harness_change_moves_the_registration_digest():
    """The fingerprint must actually bind the harness, not just list it."""
    from dataclasses import replace

    registration = reg.development_registration()
    tampered = replace(
        registration,
        source_identity={
            **registration.source_identity,
            "scientific_graph_fingerprint": "a" * 64,
        },
    )
    assert tampered.registration_digest() != registration.registration_digest()


def test_the_registration_digest_does_not_move_with_the_commit():
    """It must be stable, or the precommitment gate fails on every later commit.

    The commit and dirty flag stay OUT of the digest; the content-addressed
    actor-path fingerprint is what the execution gate compares.
    """
    from dataclasses import replace

    registration = reg.development_registration()
    moved = replace(
        registration,
        source_identity={
            **registration.source_identity,
            "source_commit": "0" * 40,
            "registered_sources_dirty": True,
        },
    )
    assert moved.registration_digest() == registration.registration_digest()

    refingerprinted = replace(
        registration,
        source_identity={
            **registration.source_identity,
            "scientific_graph_fingerprint": "f" * 64,
        },
    )
    assert refingerprinted.registration_digest() != (
        registration.registration_digest()
    )

    # The library versions are inside the digest too, because the registered
    # construction makes finite-precision claims about GRUCell, GELU, sigmoid
    # and softmax.
    relibraried = replace(
        registration,
        source_identity={**registration.source_identity, "torch_version": "0.0.0"},
    )
    assert relibraried.registration_digest() != registration.registration_digest()


def test_the_positive_terminal_carries_the_core_only_sentence(development):
    """A positive result must not read as though the environment ran."""
    report = _decide(development)
    assert report["harness_terminal"] == oc.NARROW_CLAIM_SUPPORTED
    assert report["admissible_positive_sentence"].startswith(
        "VariableRosterEventCore"
    )
    assert "DynamicRosterEventEnv has been exercised" in (
        report["constructed_cell_exclusions"]
    )
    assert "DynamicRosterEventEnv" not in oc.MAXIMUM_CONCLUSION[
        oc.NARROW_CLAIM_SUPPORTED
    ]


def test_every_terminal_carries_a_forbidden_list():
    assert set(oc.MAXIMUM_CONCLUSION) == set(oc.FORBIDDEN)
    for terminal, text in oc.FORBIDDEN.items():
        assert text and isinstance(text, str), terminal


# --------------------------------------------------------------------------
# Prospective registration discipline
# --------------------------------------------------------------------------


def test_the_registered_cell_is_never_executed_by_the_test_suite():
    """Debugging on the registered cell would be an observation before freeze.

    Pro: "No cell may be selected, replaced or modified after observing any of
    the main, reset or wrong-owner kernels."  So the registered cell may be
    *constructed* here -- that is what freezes its digest -- but never run.
    """
    registered = reg.registered_cell()
    assert not registered.development_only
    assert registered.cell_identifier != reg.development_registration().cell_identifier

    # The needles are assembled at runtime so this scan does not match its own
    # source and pass or fail for the wrong reason.
    needles = [
        "execute_" + suffix + "(" + "registered"
        for suffix in ("all", "branch")
    ] + ["reg." + "registered_cell()"]
    suite = pathlib.Path(__file__).parent
    for path in suite.glob("test_*.py"):
        source = path.read_text(encoding="utf-8")
        if path.name == pathlib.Path(__file__).name:
            # This file constructs the registered cell above (that is what
            # freezes its digest) but must not execute it.
            needles_here = needles[:2]
        else:
            needles_here = needles
        for needle in needles_here:
            assert needle not in source, f"{path.name} executes the registered cell"


def test_the_registration_digest_covers_every_frozen_choice():
    from dataclasses import replace

    base = reg.development_registration()
    baseline = base.registration_digest()
    assert replace(base, delta_cell=2e-3).registration_digest() != baseline
    assert (
        replace(base, canonical_provenance_branch=1).registration_digest() != baseline
    )
    assert (
        replace(
            base, normalization_profile=rm.RECONSTRUCTED_HISTORY
        ).registration_digest()
        != baseline
    )
    assert (
        replace(base, teacher_actions={**base.teacher_actions, "dev_target": 1})
        .registration_digest()
        != baseline
    )


def test_the_registration_refuses_a_bare_inequality_gate():
    """Pro: "Do not use mere != as the formal positive gate"."""
    from dataclasses import replace

    with pytest.raises(ValueError, match="positive margin"):
        replace(reg.development_registration(), delta_cell=0.0)


def test_the_cli_refuses_to_run_the_registered_cell():
    source = pathlib.Path(br.__file__).read_text(encoding="utf-8")
    assert "--development-cell" in source
    assert "must not be executed before External Pro has" in source
