from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
CANDIDATE = ROOT / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
LAUNCHER = CANDIDATE / "durable_b3_r03_launcher.py"
LEASE = ROOT / "temp" / "leases" / "RISP_B3_R03_ROOT_PRODUCTION_LEASE_RENEWAL_20260819.json"


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
    receipt_directory = tmp_path / "receipts"
    receipt_directory.mkdir()
    command = [sys.executable, str(LAUNCHER), "observe", "--run-root", str(tmp_path / "unused")]
    return {
        "direction": "renewal_indexed_score_plasticity",
        "revision": "RISP-B3-TRG-SCIENCE-20260815-03",
        "repository_root": str(ROOT),
        "lease_path": str(tmp_path / "fixture-lease.json"),
        "lease_sha256": "lease-digest",
        "certificate_path": str(tmp_path / "certificate.json"),
        "certificate_sha256": "certificate-digest",
        "frontier_path": str(tmp_path / "frontier"),
        "result_root": str(receipt_directory),
        "result_path": str(receipt_directory / "complete.json"),
        "receipt_directory": str(receipt_directory),
        "command": command,
        "command_sha256": "command-digest",
        "lease_not_after": "fixture",
    }


def _config(module, tmp_path: Path, binding: dict[str, object]) -> tuple[Path, Path]:
    run_root = tmp_path / "run"
    run_root.mkdir()
    config = {
        "schema": module.SCHEMA,
        "launch_id": "11111111-1111-4111-8111-111111111111",
        "run_root": str(run_root),
        "lease_path": binding["lease_path"],
        "lease_sha256": binding["lease_sha256"],
        "binding": binding,
    }
    config_path = run_root / module.CONFIG_NAME
    config_path.write_text(json.dumps(config), encoding="utf-8")
    (run_root / module.STATE_NAME).write_text(
        json.dumps({"status": "LAUNCH_REQUESTED", "launch_id": config["launch_id"]}), encoding="utf-8"
    )
    return run_root, config_path


class _FakeChild:
    pid = 4242

    def __init__(self, wait_action=None):
        self._wait_action = wait_action

    def wait(self) -> int:
        if self._wait_action is not None:
            self._wait_action()
        return 0


def _patch_fixture_supervisor(monkeypatch, module, binding: dict[str, object], fake_popen) -> None:
    monkeypatch.setattr(module, "_validate_lease", lambda _path: binding)
    monkeypatch.setattr(module, "_assert_detached_supervisor", lambda: None)
    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)


def _capture_supervise(module, config_path: Path, errors: list[BaseException]) -> None:
    try:
        module._supervise(config_path)
    except BaseException as error:  # pragma: no cover - only populated on failure
        errors.append(error)


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
    assert binding["revision"] == module.REVISION
    assert binding["repository_root"] == str(ROOT)
    assert binding["command"][1] == str(CANDIDATE / "run_b3_r03_resume.py")
    assert binding["frontier_path"].endswith("RISP_B3_R03_RESUME_20260815_03")
    assert binding["result_path"].endswith("RISP_B3_R03_20260815_03.json")
    assert binding["receipt_directory"] == str(CANDIDATE / "RISP_B3_R03_RESUME_20260815_03" / "slice_receipts")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"direction": "other"}, "direction/revision"),
        ({"production_command": "cmd /c echo unsafe"}, "production command"),
        ({"preactivity_certificate_sha256": "0" * 64}, "certificate hash"),
        ({"max_workers": 2}, "resource binding"),
    ],
)
def test_mismatched_lease_fails_before_runtime_root(tmp_path: Path, change: dict[str, object], message: str) -> None:
    module = _module()
    lease = _fresh_lease(tmp_path, **change)
    _trust_fixture_lease(module, lease)
    run_root = tmp_path / "run"
    with pytest.raises(RuntimeError, match=message):
        module._launch(argparse.Namespace(lease=lease, run_root=run_root))
    assert not run_root.exists()


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


def test_launch_interface_has_no_arbitrary_command_or_directory_inputs() -> None:
    module = _module()
    parser = module._parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["launch", "--lease", str(LEASE), "--run-root", "run", "--working-directory", str(ROOT)])
    with pytest.raises(SystemExit):
        parser.parse_args(["launch", "--lease", str(LEASE), "--run-root", "run", "--", sys.executable, "-c", "pass"])


def test_duplicate_launch_refuses_fresh_root_without_second_supervisor(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    binding = _fixture_binding(tmp_path)
    started: list[list[str]] = []
    monkeypatch.setattr(module, "_validate_lease", lambda _path: binding)
    monkeypatch.setattr(module, "_spawn_detached", lambda command: started.append(command) or _FakeChild())
    args = argparse.Namespace(lease=Path(str(binding["lease_path"])), run_root=tmp_path / "control")
    assert module._launch(args) == 0
    with pytest.raises(RuntimeError, match="must be fresh"):
        module._launch(args)
    assert len(started) == 1
    assert json.loads((args.run_root / module.STATE_NAME).read_text(encoding="utf-8"))["status"] == "LAUNCH_REQUESTED"


def test_supervisor_recomputes_binding_before_child_creation(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    binding = _fixture_binding(tmp_path)
    run_root, config_path = _config(module, tmp_path, binding)
    changed = {**binding, "command_sha256": "changed"}
    created = False

    def forbidden_popen(*args, **kwargs):
        nonlocal created
        created = True
        raise AssertionError("child creation must not occur")

    monkeypatch.setattr(module, "_validate_lease", lambda _path: changed)
    monkeypatch.setattr(module, "_assert_detached_supervisor", lambda: None)
    monkeypatch.setattr(module.subprocess, "Popen", forbidden_popen)
    with pytest.raises(RuntimeError, match="binding mismatch"):
        module._supervise(config_path)
    assert created is False
    assert json.loads((run_root / module.TERMINAL_NAME).read_text(encoding="utf-8"))["status"] == "SUPERVISOR_ERROR"


@pytest.mark.parametrize("status", ["RUNNING", "TERMINAL_RECORDED"])
def test_replay_state_without_claim_is_refused_without_observability_write(tmp_path: Path, monkeypatch, status: str) -> None:
    module = _module()
    binding = _fixture_binding(tmp_path)
    run_root, config_path = _config(module, tmp_path, binding)
    state = {"status": status, "launch_id": "11111111-1111-4111-8111-111111111111", "sentinel": "preserve"}
    (run_root / module.STATE_NAME).write_text(json.dumps(state), encoding="utf-8")
    terminal_before = None
    if status == "TERMINAL_RECORDED":
        terminal_before = b'{"status":"EXITED","sentinel":"preserve"}'
        (run_root / module.TERMINAL_NAME).write_bytes(terminal_before)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("child must not be created"))
    with pytest.raises(RuntimeError, match="one-use requested state"):
        module._supervise(config_path)
    assert json.loads((run_root / module.STATE_NAME).read_text(encoding="utf-8")) == state
    assert not (run_root / module.CLAIM_NAME).exists()
    if terminal_before is not None:
        assert (run_root / module.TERMINAL_NAME).read_bytes() == terminal_before
    else:
        assert not (run_root / module.TERMINAL_NAME).exists()


def test_active_duplicate_claim_never_starts_child_or_overwrites_observability(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    binding = _fixture_binding(tmp_path)
    run_root, config_path = _config(module, tmp_path, binding)
    release = threading.Event()
    child_created = threading.Event()
    calls = 0

    def fake_popen(*args, **kwargs):
        nonlocal calls
        calls += 1
        child_created.set()
        return _FakeChild(lambda: release.wait(5))

    _patch_fixture_supervisor(monkeypatch, module, binding, fake_popen)
    errors: list[BaseException] = []
    thread = threading.Thread(target=lambda: _capture_supervise(module, config_path, errors))
    thread.start()
    assert child_created.wait(2)
    active_state = (run_root / module.STATE_NAME).read_bytes()
    with pytest.raises(RuntimeError, match="already claimed"):
        module._supervise(config_path)
    assert calls == 1
    assert (run_root / module.STATE_NAME).read_bytes() == active_state
    assert not (run_root / module.TERMINAL_NAME).exists()
    release.set()
    thread.join(5)
    assert not errors
    terminal_before = (run_root / module.TERMINAL_NAME).read_bytes()
    with pytest.raises(RuntimeError, match="already claimed"):
        module._supervise(config_path)
    assert calls == 1
    assert (run_root / module.TERMINAL_NAME).read_bytes() == terminal_before


def test_receipt_delta_uses_names_only_and_terminal_is_immutable(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    binding = _fixture_binding(tmp_path)
    receipt_directory = Path(str(binding["receipt_directory"]))
    (receipt_directory / "before.json").write_text("partial fixture must not be opened", encoding="utf-8")
    run_root, config_path = _config(module, tmp_path, binding)

    def wait_action() -> None:
        (receipt_directory / "after.json").write_text("{}", encoding="utf-8")

    _patch_fixture_supervisor(monkeypatch, module, binding, lambda *args, **kwargs: _FakeChild(wait_action))
    assert module._supervise(config_path) == 0
    terminal = json.loads((run_root / module.TERMINAL_NAME).read_text(encoding="utf-8"))
    assert terminal["receipt_names_before"] == ["before.json"]
    assert terminal["receipt_names_after"] == ["after.json", "before.json"]
    assert terminal["new_receipt_names"] == ["after.json"]


def test_terminal_survives_later_state_mirror_failure(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    binding = _fixture_binding(tmp_path)
    run_root, config_path = _config(module, tmp_path, binding)
    _patch_fixture_supervisor(monkeypatch, module, binding, lambda *args, **kwargs: _FakeChild())
    original_atomic_write = module._atomic_write

    def fail_terminal_mirror(path: Path, payload: dict[str, object]) -> None:
        if path.name == module.STATE_NAME and payload.get("status") == "TERMINAL_RECORDED":
            raise RuntimeError("fixture mirror failure")
        original_atomic_write(path, payload)

    monkeypatch.setattr(module, "_atomic_write", fail_terminal_mirror)
    assert module._supervise(config_path) == 0
    terminal = json.loads((run_root / module.TERMINAL_NAME).read_text(encoding="utf-8"))
    assert terminal["status"] == "EXITED"
    assert terminal["exit_code"] == 0


@pytest.mark.skipif(os.name != "nt", reason="Windows Job lifetime contract")
def test_detached_worker_survives_parent_teardown_or_fails_before_worker(tmp_path: Path) -> None:
    marker = tmp_path / "survived.txt"
    refusal = tmp_path / "refused.txt"
    worker = tmp_path / "worker.py"
    parent = tmp_path / "parent.py"
    worker.write_text(
        "import importlib.util,time\n"
        f"s=importlib.util.spec_from_file_location('launcher',r'{LAUNCHER}')\n"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
        "try:\n"
        " m._assert_detached_supervisor()\n"
        "except BaseException as e:\n"
        f" open(r'{refusal}','w',encoding='utf-8').write(type(e).__name__+': '+str(e))\n"
        " raise\n"
        "time.sleep(.5)\n"
        f"open(r'{marker}','w',encoding='utf-8').write('survived')\n",
        encoding="utf-8",
    )
    parent.write_text(
        "import importlib.util,sys\n"
        f"s=importlib.util.spec_from_file_location('launcher',r'{LAUNCHER}')\n"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
        f"m._spawn_detached([sys.executable,r'{worker}'])\n",
        encoding="utf-8",
    )
    result = subprocess.run([sys.executable, str(parent)], capture_output=True, text=True)
    deadline = time.monotonic() + 5
    while result.returncode == 0 and not marker.exists() and not refusal.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    if result.returncode == 0:
        assert marker.exists() != refusal.exists()
        if marker.exists():
            assert marker.read_text(encoding="utf-8") == "survived"
        else:
            assert "Windows Job" in refusal.read_text(encoding="utf-8")
    else:
        assert not marker.exists()
        assert "PermissionError" in result.stderr or "WinError" in result.stderr
