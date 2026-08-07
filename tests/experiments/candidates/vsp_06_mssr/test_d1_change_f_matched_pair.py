"""Tests for the MSSR-D1 CHANGE_F post-commit matched-pair harness.

These are proof-sized and deterministic. The expensive full registered search
runs at most once (``test_terminal_present_on_sourced_pair``); every other test
operates on the frozen sourced pair, whose two arms are each a single
teacher-forced rollout.
"""

from __future__ import annotations

import ast
import functools
import inspect

import numpy as np

from experiments.candidates.vsp_06_mssr import d1_change_f_matched_pair as d1
from experiments.candidates.vsp_06_mssr.d1_change_f_matched_pair import (
    ACTIVE,
    CHANGE_F_MASK,
    FROZEN_SOURCED_PAIR,
    TERMINAL_PRESENT,
    capture_post_change_f,
    evaluate_pair,
    exposure_positive,
    first_logits_report,
    make_change_f_preframe,
    make_core,
    make_environment,
    proof,
    read_partner_rows,
    znp_post_change_f_digest,
    _drive,
)
from experiments.candidates.vsp_06_mssr.preaction_closure_certificate import (
    LEGAL_MASKS,
    STATE_ORDER,
    validate_mask,
)

PAIR = FROZEN_SOURCED_PAIR


@functools.lru_cache(maxsize=1)
def _evaluation() -> dict:
    return evaluate_pair(PAIR)


@functools.lru_cache(maxsize=1)
def _head() -> dict:
    evaluation = _evaluation()
    return first_logits_report(evaluation["cap_minus"], evaluation["cap_plus"])


@functools.lru_cache(maxsize=1)
def _proof() -> dict:
    return proof()


def test_change_f_resets_f_preserves_s_and_p():
    """CHANGE_F zeros the target's F, leaves P and all other records untouched;
    the applied mask is exactly D0's CHANGE_F = (F=0, S=1, P=1)."""
    change = make_change_f_preframe(PAIR.target_key, PAIR.physical_time)
    box: dict = {}

    def probe(core) -> None:
        if int(core.physical_time) != PAIR.physical_time or "done" in box:
            return
        record = core.records.get(PAIR.target_key)
        if record is None or record.status != ACTIVE:
            return
        history = record.partner_interaction_history
        before_hidden = np.asarray(record.high_hidden, dtype=np.float32).copy()
        before_p = None if history is None else float(history.current_p)
        others_before = {
            key: np.asarray(value.high_hidden, dtype=np.float32).copy()
            for key, value in core.records.items()
            if key != PAIR.target_key
        }
        change(core)  # apply the real CHANGE_F op
        after_history = record.partner_interaction_history
        box.update(
            before_hidden=before_hidden,
            after_hidden=np.asarray(record.high_hidden, dtype=np.float32).copy(),
            before_p=before_p,
            after_p=None if after_history is None else float(after_history.current_p),
            others_before=others_before,
            others_after={
                key: np.asarray(value.high_hidden, dtype=np.float32).copy()
                for key, value in core.records.items()
                if key != PAIR.target_key
            },
        )
        box["done"] = True

    core = make_core(0)
    env = make_environment()
    _drive(core, env, PAIR.base_tape(), preframe=probe, sink=None)

    assert box.get("done"), "target token at the frozen physical_time never fired"
    # F was reset to the registered zeros initializer...
    assert np.array_equal(box["after_hidden"], np.zeros(core.high_hidden_dim, np.float32))
    # ...and it was a REAL reset (F was non-zero beforehand).
    assert np.linalg.norm(box["before_hidden"]) > 0.0
    # P (the retained partner-interaction value) is preserved.
    assert box["after_p"] == box["before_p"]
    assert box["before_p"] is not None
    # Every other record's F is untouched (S / non-descendants preserved).
    assert set(box["others_before"]) == set(box["others_after"])
    for key in box["others_before"]:
        assert np.array_equal(box["others_before"][key], box["others_after"][key])
    # The applied mask equals D0's CHANGE_F over STATE_ORDER = (F, S, P).
    assert tuple(STATE_ORDER) == ("F", "S", "P")
    assert tuple(CHANGE_F_MASK) == LEGAL_MASKS["CHANGE_F"] == (0, 1, 1)
    assert validate_mask(CHANGE_F_MASK) == "CHANGE_F"


def test_post_change_f_znp_byte_identical_across_arms():
    """Z_not_P captured post-CHANGE_F at the real target token is byte-identical."""
    evaluation = _evaluation()
    assert evaluation["digest_match"]
    assert evaluation["digest_minus"] == evaluation["digest_plus"]
    # The captured pre-token F is the zeros initializer in both arms.
    assert evaluation["pre_high_hidden_is_initializer"]
    # Recompute the digests from scratch to confirm they are a pure function of
    # the captured preimage (not an artefact of a shared object).
    assert (
        znp_post_change_f_digest(evaluation["cap_minus"])
        == znp_post_change_f_digest(evaluation["cap_plus"])
    )
    # The digest attests the actor identity: both arms captured the same model
    # parameter checksum (Pro Step-1 "model digest"), equal by measurement.
    assert (
        evaluation["cap_minus"]["model_param_checksum"]
        == evaluation["cap_plus"]["model_param_checksum"]
    )
    assert len(evaluation["cap_minus"]["model_param_checksum"]) == 64


def test_retained_p_differs():
    """The retained partner-interaction value differs across arms; |dP| > 0."""
    evaluation = _evaluation()
    assert evaluation["current_p_minus"] != evaluation["current_p_plus"]
    assert evaluation["abs_delta_p"] > 0.0
    # Provenance: the frozen record's |dP| is reproduced.
    assert abs(evaluation["abs_delta_p"] - PAIR.delta_p) < 1e-9


def test_exposure_positive_provenance():
    """The two arms' target partner-interaction rows differ in payload or partner
    at some position -- a prior differing partner write actually reached both
    owners' histories (not merely a downstream reconvergence)."""
    base_rows = read_partner_rows(
        PAIR.base_tape(), PAIR.target_key, PAIR.physical_time
    )
    perturbed_rows = read_partner_rows(
        PAIR.perturbed_tape(), PAIR.target_key, PAIR.physical_time
    )
    assert len(base_rows) > 0 and len(perturbed_rows) > 0
    assert exposure_positive(base_rows, perturbed_rows)
    differing = [
        (base_row, pert_row)
        for base_row, pert_row in zip(base_rows, perturbed_rows)
        if base_row[1] != pert_row[1] or base_row[2] != pert_row[2]
    ]
    assert differing, "no aligned row pair differs in payload or partner"


def test_without_change_f_control():
    """CAUSAL CONTROL: without CHANGE_F the same two arms captured at the same
    post-commit token DIFFER, the difference is confined to F (their
    Z_not_P-minus-F digests match), and the retained P per arm is identical with
    and without the op -- the byte-identical match is established BY CHANGE_F,
    and CHANGE_F's observed effect is exactly the F reset with P preserved."""
    evaluation = _evaluation()
    assert evaluation["without_change_f_digests_differ"]
    assert evaluation["without_change_f_only_high_hidden_differs"]
    assert evaluation["without_change_f_high_hidden_l2_gap"] > 0.0
    assert evaluation["without_change_f_p_preserved"]
    # Direct re-derivation independent of evaluate_pair's own booleans: one raw
    # control arm carries a non-initializer F at the capture point...
    nocf = capture_post_change_f(
        PAIR.base_tape(), PAIR.target_key, PAIR.physical_time, change_f=False
    )
    assert np.linalg.norm(nocf["pre_token_high_hidden"]) > 0.0
    # ...and the minus-F digest is a REAL quotient: excluding F changes the
    # digest of the very same captured arm.
    assert znp_post_change_f_digest(nocf) != znp_post_change_f_digest(
        nocf, include_high_hidden=False
    )


def test_first_logits_consumes_p():
    """first_logits reads P: the two-arm logit difference is non-zero, and the
    reconstruction is byte-faithful (BOTH arms) to the production .logits()."""
    head = _head()
    assert head["faithfulness_ok"], "reconstruction did not reproduce masked_logits"
    assert head["faithfulness_minus_ok"] and head["faithfulness_plus_ok"]
    assert head["non_p_inputs_match_across_arms"]
    assert head["arm_l2"] > 0.0


def test_hardened_gate_conditions():
    """Pro loop-4 C1 hardening: the effect is NONCONSTANT (centered-logit norm
    above TAU_NUMERIC), kernel-visible (softmax total variation above
    TAU_KERNEL), the fresh head model is byte-identical to the model both arms
    ran (three-way checksum equality), and the first head precedes the
    recurrent update in the executed source."""
    head = _head()
    assert head["centered_arm_l2"] > d1.TAU_NUMERIC
    assert head["centered_arm_l2_exceeds_tau"]
    assert head["kernel_tv"] > d1.TAU_KERNEL
    assert head["kernel_tv_exceeds_tau"]
    # An action-constant shift would give centered_arm_l2 == 0 with arm_l2 > 0;
    # the observed effect is genuinely nonconstant, bounded by raw L2.
    assert head["centered_arm_l2"] <= head["arm_l2"] + 1e-12
    assert head["model_checksum_match_across_arms"]
    assert len(head["fresh_model_checksum"]) == 64
    assert head["first_head_before_recurrence_fingerprint"]
    assert head["tau_numeric"] == d1.TAU_NUMERIC
    assert head["tau_kernel"] == d1.TAU_KERNEL
    assert head["tau_null"] == 0.0


def test_fingerprint_predicate_negative_cases():
    """The AST fingerprint is falsifiable: inverted ordering and missing names
    return False (never vacuously True), and the real model source returns
    True."""
    good = (
        "def first_logits(self, x):\n"
        '    """docstring mentioning new_hidden and high_rnn early."""\n'
        "    first = self.first_head(x)\n"
        "    new_hidden = self.high_rnn(x)\n"
        "    return first, new_hidden\n"
    )
    assert d1.first_head_precedes_recurrence(good)
    inverted = (
        "def first_logits(self, x):\n"
        "    new_hidden = self.high_rnn(x)\n"
        "    first = self.first_head(new_hidden)\n"
        "    return first, new_hidden\n"
    )
    assert not d1.first_head_precedes_recurrence(inverted)
    missing_head = (
        "def first_logits(self, x):\n"
        "    new_hidden = self.high_rnn(x)\n"
        "    return new_hidden\n"
    )
    assert not d1.first_head_precedes_recurrence(missing_head)
    missing_rnn = (
        "def first_logits(self, x):\n"
        "    return self.first_head(x)\n"
    )
    assert not d1.first_head_precedes_recurrence(missing_rnn)
    # The executed model's real source passes.
    import inspect as _inspect

    real = _inspect.getsource(
        type(d1.make_core(0).commitment_model).first_logits
    )
    assert d1.first_head_precedes_recurrence(real)


def test_p_null_ablation_removes_difference():
    """Setting partner_p=0 on both arms collapses the logit difference to EXACTLY
    0 -- raw, centered, and kernel measures; the gated collapse boolean holds."""
    head = _head()
    assert head["ablation_l2"] == 0.0
    assert head["ablation_centered_l2"] == 0.0
    assert head["ablation_kernel_tv"] == 0.0
    assert head["p_null_collapse_ok"]


def test_first_logits_replayable_and_pure():
    """The read is replayable (identical inputs -> identical logits) and pure
    (RNG bit-generator states and the model parameter checksum are unchanged)."""
    head = _head()
    assert head["replay_identical"]
    assert head["rng_unchanged"]
    assert head["param_unchanged"]


def test_first_logits_precedes_recurrence_trace():
    """The SYMBOLIC D0 trace contract validates (first_logits_tick <
    recurrent_update_tick) and is labelled as symbolic, not as an empirical
    measurement of the run; structurally, first_head runs before high_rnn."""
    head = _head()
    trace = head["d0_trace_contract"]
    assert trace["symbolic_contract_validated"]
    assert trace["first_logits_tick"] < trace["recurrent_update_tick"]
    assert "symbolic" in trace["note"]
    # Structural ground: in first_logits, first_head is applied before high_rnn.
    source = inspect.getsource(
        d1.make_core(0).commitment_model.first_logits.__func__
    )
    assert source.index("first_head") < source.index("high_rnn")


def test_terminal_present_on_sourced_pair():
    """proof() sources an exposure-positive, post-commit-matched pair and returns
    the SUCCESS terminal; the sourced pair is the frozen record."""
    report = _proof()
    assert report["terminal"] == TERMINAL_PRESENT
    sourced = report["sourced_pair"]
    assert sourced["base_family"] == PAIR.base_family
    assert sourced["target_key"] == PAIR.target_key
    assert sourced["partner_key"] == PAIR.partner_key
    assert tuple(sourced["window"]) == PAIR.window
    assert sourced["physical_time"] == PAIR.physical_time
    # The success record carries a matched digest, a P difference, and the
    # without-CHANGE_F causal control.
    assert report["post_change_f"]["digest_match"]
    assert report["post_change_f"]["abs_delta_p"] > 0.0
    assert report["post_change_f"]["without_change_f_digests_differ"]
    assert report["post_change_f"]["without_change_f_only_high_hidden_differs"]
    assert report["post_change_f"]["without_change_f_p_preserved"]
    assert report["post_change_f"]["pre_high_hidden_is_initializer"]
    assert report["first_logits"]["arm_l2"] > 0.0
    assert report["first_logits"]["ablation_l2"] == 0.0
    # Hardened gate facts travel in the success record (Pro loop-4 C1).
    head = report["first_logits"]
    assert head["faithfulness_minus_ok"] and head["faithfulness_plus_ok"]
    assert head["centered_arm_l2_exceeds_tau"]
    assert head["kernel_tv_exceeds_tau"]
    assert head["p_null_collapse_ok"]
    assert head["model_checksum_match_across_arms"]
    assert head["first_head_before_recurrence_fingerprint"]
    # Sourcing counts are machine-visible and non-vacuous.
    counts = report["sourcing_counts"]
    assert counts["exposure_positive"] >= 1
    assert counts["reconverged_and_p_different"] >= counts["exposure_positive"]


def test_source_certificate_self_containment():
    """Pro loop-4 C3: the success report carries the loop-3 antecedent linkage
    -- source design identity, the matched znp-minus-hidden antecedent digests,
    the per-arm full digests (which DIFFER: the raw arms are unmatched without
    CHANGE_F), source P values, and the registration constants including the
    model registration checksum the arms attested."""
    report = _proof()
    cert = report["source_certificate"]
    assert cert["source_binding"] == "vsp_06_mssr.history_reconvergence_search.v1"
    design = cert["source_design"]
    assert design["base_family"] == PAIR.base_family
    assert design["target_key"] == PAIR.target_key
    assert design["partner_key"] == PAIR.partner_key
    assert design["window"] == list(PAIR.window)
    assert design["physical_time"] == PAIR.physical_time
    # The antecedent quotient (minus-hidden) matched -- that is what sourced
    # the pair -- while the full antecedent digests differ (F differs raw).
    assert cert["antecedent_znp_minus_hidden_match"]
    assert (
        cert["antecedent_znp_minus_hidden_digest_minus"]
        == cert["antecedent_znp_minus_hidden_digest_plus"]
    )
    assert len(cert["antecedent_znp_minus_hidden_digest_minus"]) == 64
    assert not cert["antecedent_znp_full_match"]
    assert (
        cert["antecedent_znp_full_digest_minus"]
        != cert["antecedent_znp_full_digest_plus"]
    )
    # Source P values reproduce the frozen |dP|.
    assert abs(
        abs(cert["source_p_minus"] - cert["source_p_plus"]) - PAIR.delta_p
    ) < 1e-12
    # Registration constants and the model identity chain to the captured arms.
    registration = cert["registration"]
    assert registration["model_seed"] == 57057
    assert (
        registration["model_registration_checksum"]
        == report["first_logits"]["fresh_model_checksum"]
    )


def test_scope_states_required_caveats():
    """SCOPE carries the honesty clauses: post-commit, controlled, quotient,
    materiality/small, first_logits-only, and no P_t=f(high_hidden_t)."""
    scope = d1.SCOPE.lower()
    assert "post-commit" in scope
    assert "controlled" in scope
    assert "quotient" in scope
    assert "materiality" in scope or "small" in scope
    assert "first_logits is wired only in this harness" in scope
    assert ".logits()" in d1.SCOPE  # execution / replay still use .logits()
    assert "p_t = f(high_hidden_t)" in scope
    assert "without-change_f causal control" in scope
    # Pro loop-4 C2/C4/C1 clauses: capture-point naming, member_embedding
    # non-input, hardened terminal, selected-maximum caveat.
    assert "not a pre-head-execution capture" in scope
    assert "not a direct first-action-head input" in scope
    assert "hardened terminal" in scope
    assert "selected maximum" in scope
    # Terminal vocabulary is present and bounded terminals never assert nullity.
    assert d1.TERMINAL_PRESENT.endswith("MATCHED_PAIR_PRESENT")
    assert "budget" in d1.TERMINAL_NO_EXPOSURE.lower()
    assert "budget" in d1.TERMINAL_NO_POSTCOMMIT.lower()


def test_boundary_ha_ctse_process_unmodified():
    """Boundary guard, scoped to what it actually enforces: (a) no AST-level
    attribute assignment onto the ha_ctse_process MODULE name (record-field
    writes inside the registered preframe are the CHANGE_F intervention itself,
    not patching -- object-level `obj.attr = ...` on runtime objects is outside
    this AST rule and covered by review); (b) only the two registered public
    hook installers are referenced; (c) no mock machinery imported, no
    setattr/monkeypatch called anywhere; (d) the production runtime source
    contains no first_logits call site -- execution/replay still use .logits()."""
    source = inspect.getsource(d1)
    # No attribute assignment onto ha_ctse_process modules/objects.
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                # Reject `core.<attr> = ...` / `model.<attr> = ...` style patches
                # on the runtime, EXCEPT record-field writes the hooks are for.
                if isinstance(target, ast.Attribute) and isinstance(
                    target.value, ast.Name
                ):
                    assert target.value.id not in {
                        "ha_ctse_process"
                    }, "must not patch ha_ctse_process attributes"
    # The harness references only the two registered public hook installers.
    assert "install_kernel_capture" in source
    assert "install_preframe_intervention" in source
    # Behaviorally: no patching machinery is imported or called (checked on the
    # AST so that documentation prose mentioning these words does not trip us).
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "unittest.mock" not in imported and "mock" not in imported
    called_names = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "setattr" not in called_names
    assert "monkeypatch" not in called_names
    # first_logits is the harness's own head call; production runtime uses .logits.
    runtime_source = inspect.getsource(type(make_core(0)))
    assert "first_logits" not in runtime_source
    assert ".logits(" in runtime_source
