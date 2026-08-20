from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
CANDIDATE = ROOT / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
LAUNCHER = CANDIDATE / "durable_b3_r03_launcher.py"
LEASE = ROOT / "temp" / "leases" / "RISP_B3_R03_ROOT_PRODUCTION_LEASE_POST_RECON_20260820.json"


def _module():
    specification = importlib.util.spec_from_file_location("risp_durable_launcher_test", LAUNCHER)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _fresh_lease(tmp_path: Path, **changes: object) -> Path:
    lease = json.loads(LEASE.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    lease["issued_at"] = (now - timedelta(minutes=1)).isoformat()
    lease["not_after"] = (now + timedelta(hours=6)).isoformat()
    lease.update(changes)
    path = tmp_path / "lease.json"
    path.write_text(json.dumps(lease), encoding="utf-8")
    return path


def _trust_fixture_lease(module, lease: Path) -> None:
    module.ROOT_LEASE_PATH = lease.resolve()
    module.ROOT_LEASE_SHA256 = module._sha256_file(lease)


def _fixture_binding(tmp_path: Path) -> dict[str, object]:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    sources = []
    for index in range(5):
        source = inputs / f"source-{index}.py"
        source.write_text("fixture", encoding="utf-8")
        sources.append(str(source))
    return {
        "direction": "renewal_indexed_score_plasticity", "revision": "RISP-B3-TRG-SCIENCE-20260815-03",
        "repository_root": str(ROOT), "lease_path": str(inputs / "lease.json"), "lease_sha256": "lease-digest",
        "certificate_path": str(inputs / "certificate.json"), "certificate_sha256": "certificate-digest",
        "science_card_path": str(inputs / "science-card.md"), "external_pro_closed_intake_path": str(inputs / "pro.md"),
        "portfolio_authorization_path": str(inputs / "portfolio.md"), "source_paths": sources,
        "frontier_path": str(tmp_path / "frontier"), "result_root": str(receipts),
        "result_path": str(receipts / "complete.json"), "receipt_directory": str(receipts),
        "command": [sys.executable, str(LAUNCHER), "observe", "--run-root", str(tmp_path / "unused")],
        "command_sha256": "command-digest", "lease_not_after": "fixture",
    }


def test_lease_derives_exact_frozen_binding_without_opening_result_files(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    lease = _fresh_lease(tmp_path)
    _trust_fixture_lease(module, lease)
    original_open = Path.open
    def guarded_open(path: Path, *args, **kwargs):
        if "RISP_B3_R03_RESULTS" in str(path):
            raise AssertionError("partial scientific result must not be opened")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded_open)
    binding = module._validate_lease(lease)
    assert binding["direction"] == module.DIRECTION
    assert binding["command"][1] == str(CANDIDATE / "run_b3_r03_resume.py")
    assert binding["frontier_path"].endswith("RISP_B3_R03_RESUME_20260815_03")
    assert binding["result_path"].endswith("RISP_B3_R03_20260815_03.json")
    assert len(binding["source_paths"]) == 5


@pytest.mark.parametrize(("change", "message"), [
    ({"direction": "other"}, "direction/revision"),
    ({"production_command": "cmd /c echo unsafe"}, "production command"),
    ({"preactivity_certificate_sha256": "0" * 64}, "certificate hash"),
    ({"max_workers": 2}, "resource binding"),
])
def test_mismatched_lease_fails_before_shared_effect(tmp_path: Path, monkeypatch, change: dict[str, object], message: str) -> None:
    module = _module()
    lease = _fresh_lease(tmp_path, **change)
    _trust_fixture_lease(module, lease)
    called = False
    def forbidden_effect(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("shared effect must not run")
    monkeypatch.setattr(module.long_effect, "run_long_effect", forbidden_effect)
    with pytest.raises(RuntimeError, match=message):
        module._launch(argparse.Namespace(lease=lease, run_root=tmp_path / "run"))
    assert called is False


def test_non_root_lease_path_and_changed_root_lease_bytes_are_rejected(tmp_path: Path) -> None:
    module = _module()
    copied = _fresh_lease(tmp_path)
    with pytest.raises(RuntimeError, match="exact Root lease path"):
        module._validate_lease(copied)
    module.ROOT_LEASE_PATH = copied.resolve()
    with pytest.raises(RuntimeError, match="Root lease hash"):
        module._validate_lease(copied)


def test_expired_and_future_lease_are_rejected(tmp_path: Path) -> None:
    module = _module()
    now = datetime.now(timezone.utc)
    expired = _fresh_lease(tmp_path, issued_at=(now - timedelta(hours=2)).isoformat(), not_after=(now - timedelta(hours=1)).isoformat())
    _trust_fixture_lease(module, expired)
    with pytest.raises(RuntimeError, match="not currently valid"):
        module._validate_lease(expired)
    future = _fresh_lease(tmp_path, issued_at=(now + timedelta(hours=1)).isoformat(), not_after=(now + timedelta(hours=2)).isoformat())
    _trust_fixture_lease(module, future)
    with pytest.raises(RuntimeError, match="not currently valid"):
        module._validate_lease(future)


def test_launch_constructs_exact_shared_spec_and_delegates(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    binding = _fixture_binding(tmp_path)
    captured: list[tuple[dict[str, object], Path]] = []
    monkeypatch.setattr(module, "_validate_lease", lambda _path: binding)
    monkeypatch.setattr(module.long_effect, "run_long_effect", lambda spec, root: captured.append((spec, root)) or {"exit_code": 0})
    run_root = tmp_path / "control"
    assert module._launch(argparse.Namespace(lease=Path(str(binding["lease_path"])), run_root=run_root)) == 0
    spec, received_root = captured[0]
    assert received_root == run_root
    assert spec["schema"] == module.long_effect.SPEC_SCHEMA
    assert str(uuid.UUID(spec["experiment_id"])) == spec["experiment_id"]
    assert spec["working_directory"] == str(ROOT)
    assert spec["argv"] == binding["command"]
    assert spec["metadata"] == {"direction_id": module.DIRECTION, "stage": module.STAGE, "effect_id": None}
    assert {item["name"] for item in spec["input_refs"]} == {
        "root_lease", "preactivity_certificate", "science_card", "external_pro_closed_intake", "portfolio_authorization", "resume_frontier",
        "accepted_source_1", "accepted_source_2", "accepted_source_3", "accepted_source_4", "accepted_source_5",
    }
    assert spec["output_refs"] == [
        {"name": "resume_frontier", "path": binding["frontier_path"]}, {"name": "complete_result_root", "path": binding["result_root"]},
        {"name": "complete_result", "path": binding["result_path"]}, {"name": "slice_receipts", "path": binding["receipt_directory"]},
    ]


def test_pre_child_terminal_maps_to_stable_nonzero_wrapper_exit(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    binding = _fixture_binding(tmp_path)
    monkeypatch.setattr(module, "_validate_lease", lambda _path: binding)
    monkeypatch.setattr(module.long_effect, "run_long_effect", lambda _spec, _root: {"phase": "PRE_CHILD_ERROR", "exit_code": None})
    assert module._launch(argparse.Namespace(lease=Path(str(binding["lease_path"])), run_root=tmp_path / "control")) == 1


def test_observe_delegates_without_reading_scientific_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _module()
    run_root = tmp_path / "control"
    expected = {"schema": "HMASD_LONG_EFFECT_OBSERVATION_V1", "terminal": None}
    monkeypatch.setattr(module.long_effect, "observe_long_effect", lambda root: expected if root == run_root else pytest.fail("wrong root"))
    assert module._observe(argparse.Namespace(run_root=run_root)) == 0
    assert json.loads(capsys.readouterr().out) == expected


def test_interface_and_source_contain_no_duplicate_process_lifecycle() -> None:
    module = _module()
    parser = module._parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["launch", "--lease", str(LEASE), "--run-root", "run", "--working-directory", str(ROOT)])
    with pytest.raises(SystemExit):
        parser.parse_args(["launch", "--lease", str(LEASE), "--run-root", "run", "--", sys.executable, "-c", "pass"])
    with pytest.raises(SystemExit):
        parser.parse_args(["supervise", "--experiment", "record.json"])
    source = LAUNCHER.read_text(encoding="utf-8")
    for forbidden in ("subprocess.Popen", "def _supervise", "def _exclusive_write", "def _claim_owner", "owner.json", "terminal.json"):
        assert forbidden not in source
