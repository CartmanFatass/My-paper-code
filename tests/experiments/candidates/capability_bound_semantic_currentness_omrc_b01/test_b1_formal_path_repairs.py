"""Pins for the formal-only defects that kept every B1 publication from running.

The unified profile test exercises the TEST-ONLY profile, whose constants and
audit handling differ from the formal ones, so each of these defects survived a
green suite and was only found by driving the formal path offline against
quarantined run evidence. Each test below pins one of them.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import subprocess

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b1
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    canonical_json_bytes,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_artifact import (
    _b0_leaf_rows,
    _canonical_key,
    _validate_rows,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_policy_assembly import (
    ONE_SLOT_EVALUATION_JOIN_RECORD_COUNT,
    ONE_SLOT_EXECUTION_MODE_RECORD_COUNT,
    ONE_SLOT_FORMAL_POLICY_CURVE_COUNT,
    ONE_SLOT_FORMAL_POLICY_DECISION_COUNT,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_production import (
    _b0_record_is_indexed,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_training_assembly import (
    _TABLE_AUDIT_KEY_FIELDS,
    _table_audit_rows,
)


# --------------------------------------------------------------------------
# 1. The audit's expected byte order must be the publication's byte order.
# --------------------------------------------------------------------------

def _minimal_row(fields, *, pair_id=None, tape_id=0):
    row = {}
    for field in fields:
        if field == "pair_id":
            row[field] = pair_id if pair_id is not None else "21101:0:0"
        elif field == "invocation_kind":
            row[field] = "TRAINING_SLICE"
        elif field == "member_role":
            row[field] = "A"
        elif field == "tape_id":
            row[field] = tape_id
        else:
            row[field] = 0
    return row


def _authority_tables(motif_rows):
    tables = {
        table: [_minimal_row(fields)]
        for table, fields in _TABLE_AUDIT_KEY_FIELDS.items()
        if table != "motif_twin_index"
    }
    tables["motif_twin_index"] = motif_rows
    return tables


def test_table_audit_expected_bytes_use_the_publication_canonical_order():
    """A string ``pair_id`` sorts numerically for publication, lexically raw.

    ``_canonical_key`` decodes "21101:0:10" into components, so the published
    motif_twin_index puts pair 2 before pair 10 while a raw string sort puts
    "…:10" first. Hashing the raw order produced an expected_sha256 over bytes
    the publication never writes, and every formal assembly refused with
    "materialized table reread binding differs: motif_twin_index".
    """
    fields = _TABLE_AUDIT_KEY_FIELDS["motif_twin_index"]
    motif = [
        _minimal_row(fields, pair_id="21101:0:2"),
        _minimal_row(fields, pair_id="21101:0:10"),
    ]
    raw_order = sorted(motif, key=lambda row: tuple(row[f] for f in fields))
    canonical_order = sorted(motif, key=lambda row: _canonical_key(row, fields))
    # The fixture is only meaningful if the two orders genuinely disagree.
    assert raw_order != canonical_order

    rows = _table_audit_rows(_authority_tables(motif))
    audit = next(row for row in rows if row["source_table"] == "motif_twin_index")
    expected_payload = b"".join(
        canonical_json_bytes(row) + b"\n" for row in canonical_order
    )
    assert audit["expected_sha256"] == hashlib.sha256(expected_payload).hexdigest()
    # The reported range stays raw, because the materialized reread reads the
    # values straight out of the row.
    assert audit["source_key_range"]["first_key"] == [
        canonical_order[0][f] for f in fields
    ]
    assert audit["source_key_range"]["last_key"] == [
        canonical_order[-1][f] for f in fields
    ]


# --------------------------------------------------------------------------
# 2. Table-authority binding is a two-pass construction.
# --------------------------------------------------------------------------

def _audit_row(**overrides):
    row = {
        "run_order": 0, "attempt_order": 0,
        "seed_or_minus_one": -1, "arm_or_minus_one": -1,
        "audit_code": "TABLE:raw_competence",
        "authority_type": "CANONICAL_TABLE_AUTHORITY",
        "source_table": "raw_competence",
        "source_key_range": {"key_fields": ["seed"], "first_key": [0], "last_key": [0]},
        "source_raw_slice": None, "fact_name": None,
        "expected": {"row_count": 1}, "observed": None,
        "expected_sha256": "a" * 64, "actual_sha256": None,
        "binding_status": "PENDING_MATERIALIZED_TABLE_REREAD",
        "source_relative_path": None, "json_pointer": None,
        "source_file_sha256": None, "payload_shape": None,
        "payload_dtype": None, "payload_nonzero_count": None,
    }
    row.update(overrides)
    return row


def test_preliminary_pass_tolerates_unbound_table_audits():
    """The preliminary pass encodes the tables the binding step must reread.

    Requiring BOUND_MATERIALIZED_TABLE_REREAD there demanded the output of a
    step that had not run yet, so no formal assembly could reach its own binding.
    """
    rows = [_audit_row()]
    assert _validate_rows(
        "audits", rows, allow_test_only=False, allow_pending_audits=True
    ) == rows


def test_strict_pass_still_refuses_unbound_table_audits():
    with pytest.raises(Exception, match="pending/unbound"):
        _validate_rows("audits", [_audit_row()], allow_test_only=False)


def test_direct_raw_fact_audits_stay_strict_in_both_passes():
    """Only the rows finalize_audit_table_bindings binds are exempt."""
    direct = _audit_row(
        authority_type="DIRECT_RAW_FACT_REREAD",
        audit_code="DIRECT:example",
        binding_status="PENDING_SOURCE_REREAD",
    )
    with pytest.raises(Exception, match="pending/unbound"):
        _validate_rows(
            "audits", [direct], allow_test_only=False, allow_pending_audits=True
        )


# --------------------------------------------------------------------------
# 3. Reviewed B0 evidence: which files are read, and what they must contain.
# --------------------------------------------------------------------------

def test_only_manifest_and_worker_results_are_read_from_reviewed_b0():
    """The preflight's raw receipt siblings are never canonical JSON.

    ``scripts/hmasd_resource_preflight.py`` writes them pretty-printed, so
    demanding canonical bytes of every ``.json`` under the reviewed B0 root
    refused every formal publication. Their bytes stay covered by the inventory
    and sha256 checks.
    """
    assert _b0_record_is_indexed("manifest.json")
    assert _b0_record_is_indexed("workers/00-STRUCT-CURRENTNESS-GRU/result.json")
    assert not _b0_record_is_indexed(
        "admissions/.00-STRUCT-CURRENTNESS-GRU-admission.json.raw-"
        "d3821c97eecb473a99fca4e59cc185c9.json"
    )
    assert not _b0_record_is_indexed("admissions/00-STRUCT-CURRENTNESS-GRU-admission.json")
    assert not _b0_record_is_indexed("workers/00-STRUCT-CURRENTNESS-GRU/request.json")


def test_b0_worker_result_without_a_diagnostics_subtree_yields_no_leaves():
    """A reviewed B0 worker result carries engine raw evidence, not diagnostics.

    Its ``records`` holds evaluation_actions / evaluation_tapes and has no
    ``diagnostics`` key; the evaluator view lives in the manifest. Requiring the
    subtree here demanded a shape B0 has never written.
    """
    worker = {
        "engine_evidence_schema": "cbsc_omrc_b01_engine_raw_evidence_v1",
        "records": {"evaluation_actions": [], "evaluation_tapes": []},
    }
    assert _b0_leaf_rows("workers/00-STRUCT-CURRENTNESS-GRU/result.json", worker) == []


def test_b0_manifest_without_arm_records_still_refuses():
    """The manifest branch, which is where the census comes from, stays strict."""
    with pytest.raises(Exception, match="arm_records are absent"):
        _b0_leaf_rows("manifest.json", {"arm_records": None})


# --------------------------------------------------------------------------
# 4. The formal per-slot replay counts come from the assembly constants.
# --------------------------------------------------------------------------

def test_formal_replay_counts_are_not_restated_literals():
    """The formal branch once hardcoded evaluation_join_records: 128 against a
    canonical 4, which the test-only profile could never exercise."""
    assert ONE_SLOT_FORMAL_POLICY_DECISION_COUNT == 6_144
    assert ONE_SLOT_FORMAL_POLICY_CURVE_COUNT == 64
    assert ONE_SLOT_EXECUTION_MODE_RECORD_COUNT == 4
    assert ONE_SLOT_EVALUATION_JOIN_RECORD_COUNT == 4
    source = inspect.getsource(b1.supervise_policy_replay_child)
    code = "".join(
        line for line in source.splitlines(keepends=True)
        if not line.lstrip().startswith("#")
    )
    assert "128" not in code
    for name in (
        "ONE_SLOT_FORMAL_POLICY_DECISION_COUNT",
        "ONE_SLOT_FORMAL_POLICY_CURVE_COUNT",
        "ONE_SLOT_EXECUTION_MODE_RECORD_COUNT",
        "ONE_SLOT_EVALUATION_JOIN_RECORD_COUNT",
    ):
        assert name in source


# --------------------------------------------------------------------------
# 5. A refused memory admission must say why.
# --------------------------------------------------------------------------

def test_memory_admission_failure_reports_the_preflight_reasons(monkeypatch, tmp_path):
    """admit-memory returns 6 with an EMPTY stderr on an ordinary floor refusal.

    The reasons go to stdout, so reporting stderr alone produced "exit 6: " with
    no reason -- which is how the fifth B1 attempt was refused.
    """
    payload = {
        "passed": False,
        "available_physical_bytes": 3_668_230_144,
        "failure_reasons": ["available physical memory is below 4 GiB"],
    }

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 6, stdout=json.dumps(payload), stderr=""
        )

    monkeypatch.setattr(b1.subprocess, "run", fake_run)
    with pytest.raises(
        b1.B1OrchestrationError, match="available physical memory is below 4 GiB"
    ) as excinfo:
        b1.run_memory_preflight(
            tmp_path / "admission.json", attempt_id="a" * 32,
            arm=b1.ARM_SEED_ORDER[0][1], seed=b1.ARM_SEED_ORDER[0][0],
            implementation_commit="c" * 40, source_conformance_sha256="d" * 64,
        )
    assert "exit 6" in str(excinfo.value)


def test_memory_admission_failure_still_reports_a_stderr_refusal(monkeypatch, tmp_path):
    """The other exit-6 path prints to stderr and writes no receipt."""

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 6, stdout="", stderr="resource preflight refused: bad --out"
        )

    monkeypatch.setattr(b1.subprocess, "run", fake_run)
    with pytest.raises(b1.B1OrchestrationError, match="resource preflight refused"):
        b1.run_memory_preflight(
            tmp_path / "admission.json", attempt_id="a" * 32,
            arm=b1.ARM_SEED_ORDER[0][1], seed=b1.ARM_SEED_ORDER[0][0],
            implementation_commit="c" * 40, source_conformance_sha256="d" * 64,
        )


@pytest.mark.skipif(not __import__("os").environ.get("CBSC_R05_FIXTURE"),
                    reason="requires frozen r05 offline evidence")
def test_r05_formal_publication_with_absent_resources(monkeypatch, tmp_path):
    """Offline historical admission context; never a current-source learner witness.

    CM verified the actual historical Windows interpreter bytes against the
    fixed SHA below before this remote check. Original receipt and learner bytes
    are preserved. Only a transient host/path copy goes through the unchanged
    production admission validator; original invocation, hashes, memory and
    consumer relocation checks all remain exercised.
    """
    import os
    import re
    import shutil
    import time
    import types
    from pathlib import Path, PureWindowsPath
    from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b1_metrics_production as production
    from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_artifact import make_b1_incident_lineage_witness
    from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_artifact import FORMAL_TABLE_ROW_COUNTS, validate_metrics_only_manifest

    started = time.monotonic()
    source = Path(os.environ["CBSC_R05_FIXTURE"])
    b0_root = tmp_path / "b0"
    shutil.copytree(Path(os.environ["CBSC_B0_FIXTURE"]), b0_root)
    historical_python = Path(os.environ["CBSC_HISTORICAL_PYTHON"]).read_bytes()
    assert hashlib.sha256(historical_python).hexdigest() == "7075cb605dd9d7596074b438b2640c7db0a33c436f0c7046a38c211ab257ad3b"
    staging, final = tmp_path / "offline-staging", tmp_path / "offline-publication"
    shutil.copytree(source, staging)
    commit = "4679e8dc86fb39b7b72fe7404f3f837f11ebbaad"
    conformance = "2f8dc132a1ca67138b26736094999d3771a0d2b841a399c9050cfc581b71fdd0"
    attempt = "b1-61d8b522f3fc4e8da6b48e0e01d24510"
    def historical_bytes(relative):
        return subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=b1.REPO_ROOT,
                              check=True, capture_output=True).stdout
    preflight_sha = hashlib.sha256(historical_bytes("scripts/hmasd_resource_preflight.py")).hexdigest()
    assert preflight_sha == "cb0525e9247f1c7262c198bf051e542282f5928982137b3023d36d5d69eda4dc"
    originals, relative_paths, raw_locations = {}, {}, {}
    admission_files = [*source.glob("admissions/*-admission.json"),
                       *source.glob("policy-replay/*/admission.json")]
    assert len(admission_files) == 48
    for path in admission_files:
        bound = json.loads(path.read_bytes())
        bound_path, raw_path = (PureWindowsPath(bound[key]) for key in ("bound_receipt_path", "raw_output_path"))
        assert bound["python_executable"] == r"C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe"
        assert bound["python_sha256"] == "7075cb605dd9d7596074b438b2640c7db0a33c436f0c7046a38c211ab257ad3b"
        assert bound["preflight_script_sha256"] == preflight_sha
        assert bound["exact_command"] == [bound["python_executable"], bound["preflight_script"],
                                           "admit-memory", "--out", str(raw_path)]
        assert raw_path.parent == bound_path.parent
        assert raw_path.name.startswith(f".{bound_path.name}.raw-")
        assert hashlib.sha256((path.parent / raw_path.name).read_bytes()).hexdigest() == bound["raw_receipt_sha256"]
        key = bound["bound_receipt_path"]
        originals[key] = bound
        relative_paths[key] = path.relative_to(source)
        if path.parent.parent.name == "policy-replay":
            raw_locations[bound["raw_output_path"]] = path.parent.relative_to(source) / raw_path.name
    assert len(raw_locations) == 12

    original_validate = b1.validate_bound_admission
    checked = set()
    def historical_admission(value, **kwargs):
        key = value["bound_receipt_path"]
        assert value == originals[key]
        root = staging if staging.exists() else final
        bound_path = root / relative_paths[key]
        raw_path = bound_path.parent / PureWindowsPath(value["raw_output_path"]).name
        assert bound_path.read_bytes() == (source / relative_paths[key]).read_bytes()
        # Context-only copies: persist no altered receipt and retain raw-byte checks.
        contextual = dict(value)
        executable = Path(os.path.abspath(__import__("sys").executable))
        contextual.update(python_executable=str(executable),
            python_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
            preflight_script=str(b1.CANONICAL_PREFLIGHT),
            preflight_script_sha256=hashlib.sha256(b1.CANONICAL_PREFLIGHT.read_bytes()).hexdigest(),
            bound_receipt_path=str(bound_path.resolve()), raw_output_path=str(raw_path.resolve()),
            exact_command=[str(executable), str(b1.CANONICAL_PREFLIGHT), "admit-memory", "--out", str(raw_path.resolve())])
        kwargs["expected_receipt_path"] = bound_path
        validated = original_validate(contextual, **kwargs)
        assert validated["receipt"]["available_physical_bytes"] >= 4 * 1024**3
        assert validated["receipt"]["effective_available_bytes"] >= 4 * 1024**3
        checked.add(key)
        return dict(value)
    monkeypatch.setattr(b1, "validate_bound_admission", historical_admission)
    # Preserve the consumer function's checks, using Windows names for its two
    # historical metadata paths and native paths for actual artifact reads.
    relocation = production._validate_relocated_training_admission
    historical_paths = {value[key] for value in originals.values()
                        for key in ("bound_receipt_path", "raw_output_path")}
    context = dict(relocation.__globals__)
    context["Path"] = lambda value: PureWindowsPath(value) if str(value) in historical_paths else Path(value)
    monkeypatch.setattr(production, "_validate_relocated_training_admission",
        types.FunctionType(relocation.__code__, context, relocation.__name__, relocation.__defaults__))
    confined = production.ensure_confined
    def locate(path, root):
        relative = raw_locations.get(str(path))
        return confined(staging / relative if relative is not None else path, root)
    monkeypatch.setattr(production, "ensure_confined", locate)

    groups = []
    for index, (seed, arm) in enumerate(production.B1_SLOT_ORDER):
        tag = f"{index:02d}-seed-{seed}-{arm}"
        group = [json.loads(path.read_bytes())["raw_evidence"]
                 for path in sorted((staging / "workers" / tag).glob("slice-*/result.json"))]
        assert len(group) == 3
        groups.append(group)
    # Delete only resource companions in this test's disposable copy.
    resource_files = [*staging.glob("workers/*/slice-*/telemetry.json"),
                      *staging.glob("policy-replay/*/telemetry.json")]
    assert len(resource_files) == 48
    for path in resource_files:
        path.unlink()
    laws = b1._law_digests({"files": [{"path": relative,
        "sha256": hashlib.sha256(historical_bytes(relative)).hexdigest()}
        for relative in re.findall(r'"((?:experiments/|docs/)[^"]+)"', inspect.getsource(b1._law_digests))]})
    replay = production.make_b1_policy_replay_batch_witness(staging_root=staging,
        allowed_root=tmp_path, attempt_id=attempt, implementation_commit=commit,
        source_conformance_sha256=conformance,
        literal_binding_spec_sha256=hashlib.sha256((b1.REPO_ROOT / production.LITERAL_BINDING_SPEC_RELATIVE_PATH).read_bytes()).hexdigest(),
        test_only=False)
    published = production._assemble_and_publish_b1_metrics(staging_root=staging,
        final_path=final, grouped_raw_slices=groups, implementation_commit=commit,
        source_conformance_sha256=conformance, b0_root=b0_root,
        b0_evidence=b1.locate_b0_evidence(b0_root), law_digests=laws,
        incident_lineage_witness=make_b1_incident_lineage_witness([], allowed_root=tmp_path),
        policy_replay_witness=replay, allowed_root=tmp_path, test_only=False)
    manifest = json.loads((published / "manifest.json").read_bytes())
    validate_metrics_only_manifest(manifest, root=published, allow_test_only=False)
    assert checked == set(originals)
    assert len(manifest["table_inventory"]) == 15
    counts = {row["table"]: row["row_count"] for row in manifest["table_inventory"]}
    assert all(counts[name] == count for name, count in FORMAL_TABLE_ROW_COUNTS.items())
    assert counts["telemetry"] == counts["resource_admissions"] == 48
    assert manifest["mechanical"]["mechanical_attempt_complete"] is True
    assert manifest["mechanical"]["mechanical_components"]["resource_caps"] is None
    telemetry = [json.loads(line) for line in (published / "metrics/raw/telemetry.jsonl").read_bytes().splitlines()]
    assert all(row["measurement"]["resources_unmeasured"] is True for row in telemetry)
    assert all(row["measurement"]["process_tree_peak_rss_bytes"] is None for row in telemetry)
    summary = json.loads((published / "summary.json").read_bytes())
    assert "descriptive_curves" in summary
    assert all(value is None for value in manifest["derived_fields"].values())
    assert all(manifest[field] is None for field in ("scientific_branch", "scientific_polarity",
                                                    "promotion_eligible", "b2_extension_trigger"))
    import resource
    print(json.dumps({"offline_formal_wall_seconds": time.monotonic() - started,
                      "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024}))
