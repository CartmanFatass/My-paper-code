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


def test_the_cell_isolates_the_focal_coordinate():
    """The weight witness must reflect the surgery that was actually applied."""
    registration = reg.development_registration()
    witness = registration.weight_witness
    assert witness["focal_coordinate"] == reg.FOCAL_COORDINATE
    assert not witness["gate_reads_focal_hidden"]
    assert witness["decoder_rows_reading_focal"] == 1
    assert witness["update_gate_slope_shortfall"] < 1e-8
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
            evidence["rng_states_before"]["action_rng"]["state"]
            == evidence["rng_states_after"]["action_rng"]["state"]
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
    return oc.decide(
        results=development["results"],
        contrasts=contrasts,
        certificates=development["certificates"],
        registration=development["registration"],
    )


def test_the_development_cell_can_never_yield_a_scientific_conclusion(development):
    report = _decide(development)
    assert report["terminal"] == oc.INTERFACE_INSUFFICIENT
    assert report["harness_terminal"] == oc.NARROW_CLAIM_SUPPORTED
    assert "development_only_override" in report
    assert report["explicitly_forbidden"] == oc.FORBIDDEN[oc.INTERFACE_INSUFFICIENT]


def test_a_null_against_an_analytic_guarantee_is_an_engineering_failure(development):
    """Pro's §6 qualification -- the routing rule that is easy to invert."""
    report = _decide(development, payload_contrast={"b0": 0.0, "b1": 0.0})
    assert report["harness_terminal"] == oc.INTERFACE_INSUFFICIENT
    assert "contradicts the construction" in report["reason"]
    assert "refut" not in report["reason"].split("rather than")[0]


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
    report = oc.decide(
        results=development["results"],
        contrasts=development["contrasts"],
        certificates=certificates,
        registration=development["registration"],
    )
    assert report["harness_terminal"] == oc.INTERFACE_INSUFFICIENT
    assert report["reason"] == "interface validity failed"


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
