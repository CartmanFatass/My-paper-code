from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.host import NativeBackendUnavailable
from experiments.candidates.finite_resource_relational_inductive_efficiency.native_adapter import (
    package_native_artifact_path,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency import native_adapter as native_adapter_module
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import performance_readiness
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import recon as recon_module
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.recon import (
    _AReconProcessTreeMonitor, validate_recon_evidence,
)


def test_vcvars_environment_prefers_path_candidate_that_resolves_cl_case_insensitively(monkeypatch):
    stale = r"C:\\host\\bin"
    live = r"C:\\BuildTools\\VC\\bin;C:\\Windows\\System32"
    looked_up = []

    def fake_which(name, *, path=None):
        looked_up.append((name, path))
        return r"C:\\BuildTools\\VC\\bin\\cl.exe" if path == live else None

    monkeypatch.setattr(native_adapter_module.shutil, "which", fake_which)
    compiler, environment = native_adapter_module._select_vcvars_environment(
        {"Path": stale, "TEMP": r"C:\\Temp"},
        f"PATH={live}\nPath={stale}\nTEMP=C:\\VCVARSTemp\n",
    )
    assert compiler.endswith("cl.exe")
    assert environment["PATH"] == live
    assert environment["TEMP"] == r"C:\VCVARSTemp"
    assert [key for key in environment if key.casefold() == "path"] == ["PATH"]
    assert ("cl.exe", live) in looked_up


def test_vcvars_environment_skips_stale_path_then_selects_later_live_alias(monkeypatch):
    stale = r"C:\\host\\bin"
    live = r"C:\\BuildTools\\VC\\bin"

    monkeypatch.setattr(
        native_adapter_module.shutil, "which",
        lambda name, *, path=None: r"C:\\BuildTools\\VC\\bin\\cl.exe" if path == live else None,
    )
    compiler, environment = native_adapter_module._select_vcvars_environment(
        {"Path": r"C:\\inherited"}, f"PATH={stale}\nPath={live}\n",
    )
    assert compiler.endswith("cl.exe")
    assert environment["PATH"] == live


def test_vcvars_environment_two_live_paths_choose_first_and_other_duplicates_first_win(monkeypatch):
    first = r"C:\\VS1\\VC\\bin"
    second = r"C:\\VS2\\VC\\bin"
    monkeypatch.setattr(
        native_adapter_module.shutil, "which",
        lambda name, *, path=None: path + r"\cl.exe" if path in (first, second) else None,
    )
    compiler, environment = native_adapter_module._select_vcvars_environment(
        {"TEMP": r"C:\\inherited"},
        f"Path={first}\nPATH={second}\nTEMP=C:\\first\nTemp=C:\\second\n",
    )
    assert compiler == first + r"\cl.exe"
    assert environment["PATH"] == first
    assert environment["TEMP"] == r"C:\first"


def test_vcvars_compiler_must_resolve_inside_corresponding_vc_tools_tree(tmp_path):
    vcvars = tmp_path / "VS" / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    vcvars.parent.mkdir(parents=True)
    vcvars.write_text("@echo off", encoding="ascii")
    inside = tmp_path / "VS" / "VC" / "Tools" / "MSVC" / "x64" / "cl.exe"
    inside.parent.mkdir(parents=True)
    inside.write_bytes(b"TEST")
    assert native_adapter_module._validate_vcvars_compiler(vcvars, str(inside)) == inside.resolve()
    outside = tmp_path / "host" / "cl.exe"
    outside.parent.mkdir()
    outside.write_bytes(b"TEST")
    with pytest.raises(NativeBackendUnavailable, match="outside.*VC/Tools"):
        native_adapter_module._validate_vcvars_compiler(vcvars, str(outside))


def test_process_tree_monitor_retains_exited_child_cpu_and_io(tmp_path):
    scratch = tmp_path / "scratch"
    durable = tmp_path / "durable"
    scratch.mkdir()
    durable.mkdir()
    output = scratch / "child-output.bin"
    byte_count = 1024 * 1024
    monitor = _AReconProcessTreeMonitor(
        scratch_root=scratch, durable_root=durable, interval_seconds=0.002,
    )
    monitor.set_stage("SHORT_CHILD")
    monitor.start()
    completed = subprocess.run(
        [
            sys.executable, "-c",
            (
                "import pathlib,time; "
                f"pathlib.Path({str(output)!r}).write_bytes(b'x'*{byte_count}); "
                "end=time.perf_counter()+0.35; value=0; "
                "exec(\"while time.perf_counter()<end:\\n value=(value+1)%1000003\")"
            ),
        ],
        check=False, capture_output=True, text=True, timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    telemetry = monitor.stop()["end_to_end"]
    assert telemetry["peak_process_count"] >= 2
    assert telemetry["peak_thread_count"] >= 2
    assert telemetry["cpu_seconds"] > 0.0
    assert telemetry["cpu_core_equivalents"] == (
        telemetry["cpu_seconds"] / telemetry["wall_seconds"]
    )
    assert telemetry["host_cpu_occupancy_fraction"] == (
        telemetry["cpu_core_equivalents"] / telemetry["logical_cpu_count"]
    )
    assert telemetry["io_write_transfer_bytes"] >= byte_count
    assert telemetry["scratch_peak_bytes"] >= byte_count


def test_recon_cli_quarantines_failed_staging_without_overwrite(tmp_path, monkeypatch):
    root = (tmp_path / "failed-root").resolve()
    staging = root.with_name(root.name + ".creating")

    def fail_after_staging(*, root):
        staging.mkdir()
        (staging / "direct-receipt.json").write_text("DIRECT", encoding="ascii")
        raise RuntimeError("injected technical failure")

    monkeypatch.setattr(recon_module, "run_test_recon", fail_after_staging)
    with pytest.raises(RuntimeError, match="injected technical failure"):
        recon_module.main(["--root", str(root)])
    incomplete = root.with_name(root.name + ".incomplete")
    assert not staging.exists()
    assert (incomplete / "direct-receipt.json").read_text(encoding="ascii") == "DIRECT"
    marker = json.loads((incomplete / "incomplete.json").read_text(encoding="utf-8"))
    assert marker["status"] == "INCOMPLETE_SUPERSEDED_TECHNICAL_ARTIFACT"
    assert marker["scientific_values"] is None


def test_actual_package_native_scalar_batch_and_worker_equivalence():
    artifact = package_native_artifact_path().resolve(strict=False)
    if artifact.exists():
        pytest.skip("unknown pre-existing package native artifact; test will not delete it")
    root = (
        Path("temp") / f"frrie_b01_a_recon_native_{os.getpid()}_{time.time_ns()}"
    ).resolve(strict=False)
    evidence_path = root / "evidence.json"
    completed = None
    evidence = None
    try:
        completed = subprocess.run(
            [
                sys.executable, "-m",
                "experiments.candidates.finite_resource_relational_inductive_efficiency.b01.recon",
                "--root", str(root),
            ],
            check=False, capture_output=True, text=True, timeout=120,
        )
        assert completed.returncode == 0, completed.stderr or completed.stdout
        evidence = validate_recon_evidence(json.loads(evidence_path.read_text(encoding="utf-8")))
        assert evidence["scalar_batch_direct_equal"] is True
        assert evidence["worker_1_2_4_direct_equal"] is True
        assert len(evidence["scalar_batch_rows"]) == 48
        assert len(evidence["worker_rows"]) == 24
        assert evidence["batch_work_ledger"]["environment_slots"] == 48
        assert (root / "admit-memory.json").is_file()
        refused = subprocess.run(
            [
                sys.executable, "-m",
                "experiments.candidates.finite_resource_relational_inductive_efficiency.b01.recon",
                "--root", str(root),
            ],
            check=False, capture_output=True, text=True, timeout=30,
        )
        assert refused.returncode != 0
        assert "not fresh" in (refused.stderr + refused.stdout)
    finally:
        if evidence is not None:
            generated = Path(evidence["native_artifact_path"]).resolve(strict=True)
            expected = package_native_artifact_path().resolve(strict=True)
            expected_bytes = base64.b64decode(
                evidence["native_artifact_bytes_b64"], validate=True,
            )
            assert generated == expected == artifact.resolve(strict=True)
            assert generated.read_bytes() == expected_bytes
            generated.unlink()
            assert not generated.exists()
        elif package_native_artifact_path().exists():
            # The fixed target was absent before this dedicated child transaction;
            # a child failure must not strand the artifact it just generated.
            package_native_artifact_path().unlink()


def test_performance_readiness_fails_closed_without_end_to_end_telemetry():
    assert performance_readiness({
        "schema": "FRRIE_B01_PERFORMANCE_TELEMETRY_V1",
        "disposition": "REPAIR_REQUIRED", "blocker": "END_TO_END_TELEMETRY_ABSENT",
        "measured_at": None, "end_to_end_wall_seconds": None,
        "scientific_slots": None, "slots_per_second": None, "cpu_seconds": None,
        "cpu_occupancy_fraction": None, "process_tree_peak_rss_bytes": None,
        "scratch_peak_bytes": None, "durable_peak_bytes": None,
        "read_bytes": None, "write_bytes": None, "worker_peak": None,
        "scalar_batch_equivalence": None, "worker_equivalence": None,
    }) == "REPAIR_REQUIRED"
