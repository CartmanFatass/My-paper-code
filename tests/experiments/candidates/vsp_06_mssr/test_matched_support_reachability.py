"""Focused tests for the MSSR matched-support single-partner coupling proof."""

from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import pathlib
import sys

from experiments.candidates.vsp_06_mssr import matched_support_reachability as mssr


def test_terminal_is_current_source_coupling_witness():
    result = mssr.proof()
    # Pro's licensed reading (revision 2503340b): a CURRENT-source coupling
    # witness, not any matched-support impossibility theorem.
    assert result["terminal"] == "MSSR_CURRENT_SOURCE_SINGLE_PARTNER_COUPLING_WITNESS"
    assert result["raw_output_binding"] == "vsp_06_mssr.matched_support_reachability.v1"


def test_carrier_retains_history_difference_is_nonzero():
    check = mssr.carrier_retains_history()
    assert check.passed
    # A matched current payload leaves a nonzero prior-driven gap.
    assert check.numbers["difference"] != 0.0
    # The two priors were genuinely distinct before the matched write.
    assert check.numbers["prior_p_a"] != check.numbers["prior_p_b"]
    assert check.numbers["current_p_a"] != check.numbers["current_p_b"]


def test_single_partner_variation_moves_all_three_channels():
    check = mssr.single_partner_variation_moves_owner_context()
    assert check.passed
    # (a) the alignment channel moved, (b) the summary moved, (c) high_hidden moved.
    assert check.numbers["alignment_delta"] != 0.0
    assert check.numbers["summary_l2_delta"] != 0.0
    assert check.numbers["high_hidden_l2_delta"] != 0.0


def test_encoder_has_full_column_rank():
    check = mssr.encoder_has_no_obs_nullspace()
    assert check.passed
    obs_dim = check.numbers["obs_dim"]
    assert check.numbers["rank"] == obs_dim
    assert check.numbers["jacobian_cols"] == obs_dim
    # Full column rank requires a strictly positive smallest singular value.
    assert check.numbers["smallest_singular_value"] > 0.0


def test_partner_is_always_a_summary_member():
    check = mssr.partner_source_is_a_summary_member()
    assert check.passed
    assert check.numbers["owner_writes_checked"] > 0.0
    assert check.numbers["violations"] == 0.0


def test_scope_is_honestly_bounded():
    scope = mssr.proof()["scope"]
    assert "licenses no scientific claim" in scope
    # Pins Pro's temporal correction: this is the CURRENT source, a different
    # object from the HISTORICAL retained P_t, and asserts no unreachability.
    assert "CURRENT source" in scope
    assert "HISTORICAL" in scope
    assert "different temporal object" in scope
    assert "asserts NO unreachability" in scope
    # The sum-fiber route is explicitly demoted to the wrong temporal object.
    assert "sum-fiber" in scope


def test_module_imports_without_side_effects():
    path = (
        pathlib.Path(mssr.__file__).resolve()
    )
    probe_name = "_mssr_import_probe"
    spec = importlib.util.spec_from_file_location(probe_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Register before exec so dataclass module resolution succeeds (standard
    # importlib idiom); this is import machinery, not a module side effect.
    sys.modules[probe_name] = module
    stream = io.StringIO()
    try:
        with contextlib.redirect_stdout(stream):
            spec.loader.exec_module(module)
    finally:
        sys.modules.pop(probe_name, None)
    # Import alone runs no check and prints nothing (the json dump is __main__ only).
    assert stream.getvalue() == ""
    assert callable(module.proof)
    assert hasattr(module, "RAW_OUTPUT_BINDING")
