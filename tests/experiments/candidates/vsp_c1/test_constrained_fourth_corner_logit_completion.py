"""Proof-sized wrong-implementation tests for frozen VSPC1-A1 semantics."""

from __future__ import annotations

from copy import deepcopy
import io
import math
from pathlib import Path
from unittest.mock import MagicMock, mock_open

import pytest

from experiments.candidates.vsp_c1 import constrained_fourth_corner_logit_completion as audit


def _manifest() -> dict:
    common_state = {
        field: f"{index:02x}"
        for index, field in enumerate(audit.PORT_FREE_STATE_FIELDS, start=1)
    }
    selected = {"i0": "identity-a", "i1": "identity-b", "p0": "period-0", "p1": "period-1"}
    pairs = {
        "i0p0": (selected["i0"], selected["p0"]),
        "i0p1": (selected["i0"], selected["p1"]),
        "i1p0": (selected["i1"], selected["p0"]),
        "i1p1": (selected["i1"], selected["p1"]),
    }
    return {
        "schema_version": audit.SCHEMA_VERSION,
        "design_id": audit.DESIGN_ID,
        "treatment_id": audit.TREATMENT_ID,
        "candidate_version": audit.CANDIDATE_VERSION,
        "host_contract_id": audit.HOST_CONTRACT_ID,
        "checkpoint_id": "checkpoint-1",
        "roster_id": "roster-1",
        "boundary_state_id": "boundary-1",
        "metadata_factor_order": {
            "identity_levels": ["identity-a", "identity-b", "identity-c"],
            "period_levels": ["period-0", "period-1", "period-2"],
        },
        "selected_factors": selected,
        "training_cells": list(audit.T_CELLS),
        "heldout_cell": audit.H_CELL,
        "legal_action_order": ["left", "right"],
        "clones": [
            {
                "cell": cell,
                "identity": identity,
                "period": period,
                "port_free_state_bytes": deepcopy(common_state),
                "legal_action_order": ["left", "right"],
                "source_binding": {
                    "cell": cell,
                    "clone_handle_id": f"clone-{cell}",
                    "reader_id": f"reader-{cell}",
                    "kernel_source_id": f"kernel-source-{cell}",
                    "model_graph_id": f"model-graph-{cell}",
                    "nonfactor_state_sha256": audit.nonfactor_state_sha256(common_state),
                },
            }
            for cell, (identity, period) in pairs.items()
        ],
        "joint_key_witness": {
            "predictor_read_paths": ["identity", "period"],
            "joint_identity_period_key_paths": [],
            "joint_identity_period_descendant_paths": [],
        },
        "selection_receipt": {
            "metadata_order_used": True,
            "kernel_reads_before_selection": 0,
            "return_information_used": False,
            "outcome_conditioned_selection": False,
        },
        "freeze_receipt": {
            "event_ordinal": 0,
            "kernel_reads_before_freeze": 0,
            "frozen_objects": [
                "checkpoint",
                "roster",
                "boundary state",
                "metadata factor order",
                "i0 i1 p0 p1",
                "three-cell T",
                "heldout H=i1p1",
                "legal-action order",
                "state-equality manifest",
            ],
        },
    }


def _kernel(probabilities: list[float]) -> dict:
    return {
        "probabilities": probabilities,
        "legal_action_order": ["left", "right"],
        "legal_mask": [True, True],
    }


def _supported_kernels() -> dict[str, dict]:
    return {
        "i0p0": _kernel([0.5, 0.5]),
        "i0p1": _kernel([0.8, 0.2]),
        "i1p0": _kernel([0.8, 0.2]),
        # Exact constrained fourth corner: softmax([logit(.8)-logit(.5)] * 2).
        "i1p1": _kernel([16.0 / 17.0, 1.0 / 17.0]),
    }


class _CloneHandle:
    def __init__(self, clone: dict) -> None:
        binding = clone["source_binding"]
        self.clone_handle_id = binding["clone_handle_id"]
        self.model_graph_id = binding["model_graph_id"]
        self.model_graph_handle = object()
        self.port_free_state_bytes = deepcopy(clone["port_free_state_bytes"])


class _CellReader:
    def __init__(
        self,
        cell: str,
        kernel: dict,
        binding: dict,
        calls: list[str],
        *,
        forbid_h: bool = False,
    ) -> None:
        self.cell = cell
        self.kernel = kernel
        self.capture_binding = deepcopy(binding)
        self.reader_id = binding["reader_id"]
        self.kernel_source_id = binding["kernel_source_id"]
        self.kernel_source_handle = object()
        self.calls = calls
        self.forbid_h = forbid_h

    def __call__(self) -> dict:
        if self.cell == audit.H_CELL and self.forbid_h:
            raise AssertionError("H was read before the pre-reveal gate terminated")
        self.calls.append(self.cell)
        return {**deepcopy(self.kernel), "capture_source_binding": deepcopy(self.capture_binding)}


def _cell_sources(
    manifest: dict,
    kernels: dict[str, dict],
    *,
    forbid_h: bool = False,
) -> tuple[dict[str, dict], list[str]]:
    calls: list[str] = []
    clones = {row["cell"]: row for row in manifest["clones"]}
    sources = {}
    for cell in audit.ALL_CELLS:
        binding = clones[cell]["source_binding"]
        sources[cell] = {
            "clone_handle": _CloneHandle(clones[cell]),
            "reader": _CellReader(
                cell,
                kernels[cell],
                binding,
                calls,
                forbid_h=forbid_h,
            ),
        }
    return sources, calls


def _supported_result() -> dict:
    manifest = _manifest()
    sources, calls = _cell_sources(manifest, _supported_kernels())
    result = audit.execute_complete_rectangle(manifest, sources)
    assert calls == list(audit.ALL_CELLS)
    assert result["terminal_branch"] == audit.SUPPORTED
    return result


def test_registered_host_observation_fails_closed_without_constructing_a_substitute() -> None:
    observation = audit.observe_registered_host()
    assert observation["status"] == "unreachable"
    assert observation["constructor_count"] == 0
    assert observation["qualified_constructor"] is None
    assert observation["rejected_substitutions"] == ["toy", "ORBIT", "lifecycle", "MSSR"]
    result = audit.build_unreachable_result(observation)
    audit.validate_audit_result(result)
    assert result["terminal_branch"] == audit.HOST_UNREACHABLE
    assert result["activity_counts"]["registered_audits"] == 1
    assert all(
        value == 0
        for name, value in result["activity_counts"].items()
        if name != "registered_audits"
    )
    assert result["kernels"] == {}
    assert result["state_equality_manifest"] is None


def test_complete_predictors_use_exact_three_d_capacity_and_seal_before_h() -> None:
    result = _supported_result()
    audit.validate_audit_result(result, allow_retained_fixture=True)
    assert result["predictor_fits"]["candidate"]["fitted_scalar_count"] == 6
    assert result["predictor_fits"]["null"]["fitted_scalar_count"] == 6
    assert result["predictor_fits"]["candidate"]["scalar_dtype"] == "float64"
    assert result["predictor_fits"]["null"]["scalar_dtype"] == "float64"
    assert result["predictor_fits"]["null"]["fourth_cell_parameter"] is False
    assert result["pre_reveal_js"] >= audit.PRE_REVEAL_JS_THRESHOLD
    assert result["estimands"]["D_C"] == pytest.approx(0.0, abs=1e-15)
    assert result["estimands"]["Delta"] >= audit.SUPPORT_DELTA_THRESHOLD
    transcript = result["event_transcript"]
    assert [row["event"] for row in transcript] == [
        "freeze", "kernel_read", "kernel_read", "kernel_read", "seal", "seal", "h_reveal"
    ]
    assert result["activity_counts"]["focused_production_kernel_calls"] == 4


def test_pre_reveal_nondiscrimination_never_reads_h() -> None:
    kernels = {cell: _kernel([0.5, 0.5]) for cell in audit.ALL_CELLS}
    manifest = _manifest()
    sources, calls = _cell_sources(manifest, kernels, forbid_h=True)
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.NONDISCRIMINATING
    assert calls == list(audit.T_CELLS)
    assert set(result["kernels"]) == set(audit.T_CELLS)
    assert result["activity_counts"]["focused_production_kernel_calls"] == 3
    assert all(value is None for value in result["estimands"].values())
    audit.validate_audit_result(result, allow_retained_fixture=True)


def test_port_free_clone_mismatch_fails_before_any_kernel_call() -> None:
    manifest = _manifest()
    manifest["clones"][-1]["port_free_state_bytes"]["rng_inputs"] = "ff"
    manifest["clones"][-1]["source_binding"]["nonfactor_state_sha256"] = (
        audit.nonfactor_state_sha256(manifest["clones"][-1]["port_free_state_bytes"])
    )
    sources, calls = _cell_sources(manifest, _supported_kernels())
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.INVALID
    assert calls == []
    assert "byte-identical" in result["construction_failures"][0]


@pytest.mark.parametrize(
    "mutation, message",
    [
        (
            lambda manifest: manifest["joint_key_witness"]["joint_identity_period_key_paths"].append("lookup.identity_period"),
            "joint identity-period",
        ),
        (
            lambda manifest: manifest["selection_receipt"].__setitem__("kernel_reads_before_selection", 1),
            "prospectively frozen",
        ),
        (
            lambda manifest: manifest["selected_factors"].__setitem__("i0", "identity-b"),
            "first two frozen",
        ),
    ],
)
def test_joint_key_and_post_kernel_selection_loopholes_fail_before_reads(mutation, message: str) -> None:
    manifest = _manifest()
    mutation(manifest)
    sources, calls = _cell_sources(manifest, _supported_kernels())
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.INVALID
    assert calls == []
    assert message in result["construction_failures"][0]


def test_common_support_nonfinite_and_wrong_action_order_fail_closed() -> None:
    for bad_kernel in (
        {"probabilities": [1.0, 0.0], "legal_action_order": ["left", "right"], "legal_mask": [True, True]},
        {"probabilities": [0.5, 0.5], "legal_action_order": ["right", "left"], "legal_mask": [True, True]},
        {"probabilities": [float("nan"), 0.5], "legal_action_order": ["left", "right"], "legal_mask": [True, True]},
    ):
        kernels = _supported_kernels()
        kernels["i0p0"] = bad_kernel
        manifest = _manifest()
        sources, calls = _cell_sources(manifest, kernels)
        result = audit.execute_complete_rectangle(manifest, sources)
        assert result["terminal_branch"] == audit.INVALID
        assert calls == ["i0p0"]
        assert result["activity_counts"]["focused_production_kernel_calls"] == 1
        assert result["attempted_kernel_reads"] == [
            {
                "attempt_ordinal": 1,
                "cell": "i0p0",
                "kernel_source_id": "kernel-source-i0p0",
            }
        ]
        audit.validate_audit_result(result, allow_retained_fixture=True)


@pytest.mark.parametrize("aliased_field", ["clone_handle", "reader"])
def test_four_live_cell_sources_reject_object_aliasing_before_t(aliased_field: str) -> None:
    manifest = _manifest()
    sources, calls = _cell_sources(manifest, _supported_kernels())
    sources["i0p1"][aliased_field] = sources["i0p0"][aliased_field]
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.INVALID
    assert calls == []
    assert result["activity_counts"]["focused_production_kernel_calls"] == 0
    assert "distinct source objects" in result["construction_failures"][0]


def test_sequential_one_model_reuse_and_live_binding_drift_fail_before_t() -> None:
    manifest = _manifest()
    manifest["clones"][1]["source_binding"]["model_graph_id"] = (
        manifest["clones"][0]["source_binding"]["model_graph_id"]
    )
    sources, calls = _cell_sources(manifest, _supported_kernels())
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.INVALID
    assert calls == []
    assert "model graphs must be distinct" in result["construction_failures"][0]

    manifest = _manifest()
    sources, calls = _cell_sources(manifest, _supported_kernels())
    sources["i0p1"]["clone_handle"].model_graph_handle = (
        sources["i0p0"]["clone_handle"].model_graph_handle
    )
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.INVALID
    assert calls == []
    assert "sequential one-model reuse" in result["construction_failures"][0]

    manifest = _manifest()
    sources, calls = _cell_sources(manifest, _supported_kernels())
    sources["i0p0"]["reader"].kernel_source_id = "different-live-source"
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.INVALID
    assert calls == []
    assert "live handle/reader identity differs" in result["construction_failures"][0]

    manifest = _manifest()
    sources, calls = _cell_sources(manifest, _supported_kernels())
    sources["i0p0"]["clone_handle"].port_free_state_bytes["rng_inputs"] = "ff"
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.INVALID
    assert calls == []
    assert "captured nonfactor bytes differ" in result["construction_failures"][0]


def test_capture_source_mismatch_counts_the_attempted_invocation() -> None:
    manifest = _manifest()
    sources, calls = _cell_sources(manifest, _supported_kernels())
    sources["i0p0"]["reader"].capture_binding["kernel_source_id"] = "aliased-capture"
    result = audit.execute_complete_rectangle(manifest, sources)
    assert result["terminal_branch"] == audit.INVALID
    assert calls == ["i0p0"]
    assert result["activity_counts"]["focused_production_kernel_calls"] == 1
    assert result["attempted_kernel_reads"][0]["kernel_source_id"] == "kernel-source-i0p0"
    assert "capture source does not match" in result["construction_failures"][0]
    audit.validate_audit_result(result, allow_retained_fixture=True)


@pytest.mark.parametrize(
    "tamper, message",
    [
        (
            lambda result: result["sealed_prediction_receipts"]["candidate"].__setitem__("fitted_scalar_count", 8),
            "sealed prediction receipt",
        ),
        (
            lambda result: result["kernels"]["i1p1"]["centered_logits"].__setitem__(0, 999.0),
            "centered logits",
        ),
        (
            lambda result: result["event_transcript"].__setitem__(4, result["event_transcript"][6]),
            "H was not read exactly once",
        ),
        (
            lambda result: result.__setitem__("terminal_branch", audit.AMBIGUOUS),
            "terminal branch precedence",
        ),
        (
            lambda result: result["activity_counts"].__setitem__("focused_production_kernel_calls", 3),
            "activity counts",
        ),
        (
            lambda result: result["bound_identities"].__setitem__("i1", "identity-a"),
            "bound checkpoint/roster/state/factor/action identities",
        ),
        (
            lambda result: result["publication_binding"].__setitem__("accepted_source_commit", "fabricated"),
            "publication acceptance binding",
        ),
        (
            lambda result: result["kernels"]["i1p1"]["capture_source_binding"].__setitem__(
                "kernel_source_id", "wrong-source"
            ),
            "capture source does not match",
        ),
    ],
)
def test_independent_validator_rejects_seal_logit_order_branch_and_counter_tamper(tamper, message: str) -> None:
    result = _supported_result()
    tamper(result)
    with pytest.raises(audit.ContractViolation, match=message):
        audit.validate_audit_result(result, allow_retained_fixture=True)


def test_terminal_precedence_uses_literal_frozen_boundaries() -> None:
    assert audit.select_terminal_branch(construction_valid=False, host_reachable=False) == audit.INVALID
    assert audit.select_terminal_branch(construction_valid=True, host_reachable=False, pre_reveal_js=1.0) == audit.HOST_UNREACHABLE
    below_pre = math.nextafter(audit.PRE_REVEAL_JS_THRESHOLD, -math.inf)
    above_pre = math.nextafter(audit.PRE_REVEAL_JS_THRESHOLD, math.inf)
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=below_pre,
        d_candidate=0.02, d_null=0.02,
    ) == audit.NONDISCRIMINATING
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True,
        pre_reveal_js=audit.PRE_REVEAL_JS_THRESHOLD,
        d_candidate=0.02, d_null=0.02,
    ) == audit.AMBIGUOUS
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=above_pre,
        d_candidate=0.02, d_null=0.02,
    ) == audit.AMBIGUOUS

    below_falsification = math.nextafter(audit.FALSIFICATION_D_C_THRESHOLD, -math.inf)
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=0.02,
        d_candidate=below_falsification, d_null=below_falsification,
    ) == audit.AMBIGUOUS
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=0.02,
        d_candidate=audit.FALSIFICATION_D_C_THRESHOLD,
        d_null=audit.FALSIFICATION_D_C_THRESHOLD,
    ) == audit.FALSIFIED

    below_relative = math.nextafter(audit.FALSIFICATION_RELATIVE_THRESHOLD, -math.inf)
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=0.02,
        d_candidate=below_relative, d_null=0.0,
    ) == audit.AMBIGUOUS
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=0.02,
        d_candidate=audit.FALSIFICATION_RELATIVE_THRESHOLD, d_null=0.0,
    ) == audit.FALSIFIED

    above_support_d_c = math.nextafter(audit.SUPPORT_D_C_THRESHOLD, math.inf)
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=0.02,
        d_candidate=audit.SUPPORT_D_C_THRESHOLD, d_null=0.04,
    ) == audit.SUPPORTED
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=0.02,
        d_candidate=above_support_d_c, d_null=0.04,
    ) == audit.AMBIGUOUS

    below_delta = math.nextafter(audit.SUPPORT_DELTA_THRESHOLD, -math.inf)
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=0.02,
        d_candidate=0.0, d_null=below_delta,
    ) == audit.AMBIGUOUS
    assert audit.select_terminal_branch(
        construction_valid=True, host_reachable=True, pre_reveal_js=0.02,
        d_candidate=0.0, d_null=audit.SUPPORT_DELTA_THRESHOLD,
    ) == audit.SUPPORTED


def test_unreachable_artifact_writer_is_validated_and_one_shot(monkeypatch) -> None:
    result = audit.build_unreachable_result(audit.observe_registered_host())
    output = Path("result.json")
    validator = MagicMock()
    opened = mock_open()
    monkeypatch.setattr(audit, "validate_audit_result", validator)
    monkeypatch.setattr(Path, "exists", lambda self: False)
    monkeypatch.setattr(Path, "mkdir", lambda self, **kwargs: None)
    monkeypatch.setattr(Path, "open", opened)
    monkeypatch.setattr(audit.os, "fsync", lambda fileno: None)
    linked = MagicMock()
    monkeypatch.setattr(audit.os, "link", linked)
    monkeypatch.setattr(Path, "unlink", lambda self: None)
    audit.write_result_once(output, result)
    validator.assert_called_once_with(result)
    linked.assert_called_once()
    opened().write.assert_called_once()

    monkeypatch.setattr(Path, "exists", lambda self: True)
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        audit.write_result_once(output, result)


class _MemoryExclusiveHandle:
    def __init__(self) -> None:
        self.buffer = io.BytesIO()
        self.closed = False

    def seek(self, *args):
        return self.buffer.seek(*args)

    def truncate(self, *args):
        return self.buffer.truncate(*args)

    def write(self, value: bytes):
        return self.buffer.write(value)

    def flush(self) -> None:
        return None

    def fileno(self) -> int:
        return 1

    def close(self) -> None:
        self.closed = True


def test_output_and_shared_claim_are_exclusive_before_registered_source_execution(monkeypatch) -> None:
    files: dict[str, _MemoryExclusiveHandle] = {}

    def exclusive_open(path: Path, mode: str):
        assert mode == "x+b"
        key = str(path)
        if key in files:
            raise FileExistsError(key)
        handle = _MemoryExclusiveHandle()
        files[key] = handle
        return handle

    monkeypatch.setattr(Path, "mkdir", lambda self, **kwargs: None)
    monkeypatch.setattr(Path, "open", exclusive_open)
    monkeypatch.setattr(audit.os, "fsync", lambda fileno: None)

    result = audit.build_unreachable_result(audit.observe_registered_host())
    first_runner = MagicMock(return_value=result)
    observed = audit.claim_and_run_registered_audit(
        Path("first-result.json"),
        Path("one-audit.claim"),
        audit_runner=first_runner,
    )
    assert observed["terminal_branch"] == audit.HOST_UNREACHABLE
    first_runner.assert_called_once()

    existing_output_runner = MagicMock(side_effect=AssertionError("audit ran"))
    with pytest.raises(FileExistsError):
        audit.claim_and_run_registered_audit(
            Path("first-result.json"),
            Path("one-audit.claim"),
            audit_runner=existing_output_runner,
        )
    existing_output_runner.assert_not_called()

    distinct_output_runner = MagicMock(side_effect=AssertionError("audit ran"))
    with pytest.raises(FileExistsError):
        audit.claim_and_run_registered_audit(
            Path("different-result.json"),
            Path("one-audit.claim"),
            audit_runner=distinct_output_runner,
        )
    distinct_output_runner.assert_not_called()
    assert "different-result.json" in files


def test_registered_audit_cannot_start_without_active_reservation(monkeypatch) -> None:
    source_observation = MagicMock(side_effect=AssertionError("source inspection ran"))
    monkeypatch.setattr(audit, "_registered_constructor", source_observation)
    with pytest.raises(audit.ContractViolation, match="active pre-execution"):
        audit.run_registered_audit(None)
    source_observation.assert_not_called()


def test_unreachable_validator_rejects_hidden_kernel_or_scientific_activity() -> None:
    result = audit.build_unreachable_result(audit.observe_registered_host())
    result["kernels"]["i0p0"] = _kernel([0.5, 0.5])
    with pytest.raises(audit.ContractViolation, match="contains kernel"):
        audit.validate_audit_result(result)
    result = audit.build_unreachable_result(audit.observe_registered_host())
    result["activity_counts"]["model_fits"] = 1
    with pytest.raises(audit.ContractViolation, match="cap"):
        audit.validate_audit_result(result)
