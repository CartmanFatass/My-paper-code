from __future__ import annotations

import inspect
import json
import os
import re
import sys
import threading
import uuid
from pathlib import Path

import pytest

from tools.hmasd_control_plane import long_effect
from tools.hmasd_control_plane.long_effect import (
    RunRootConflict,
    SpecValidationError,
    observe_long_effect,
    run_long_effect,
    validate_spec,
)


EXPECTED_FILES = {
    "experiment.json",
    "owner.json",
    "stdout.log",
    "stderr.log",
    "terminal.json",
}


def _spec(tmp_path: Path, code: str, *, component: str = "test") -> dict[str, object]:
    return {
        "schema": "HMASD_LONG_EFFECT_V1",
        "experiment_id": str(uuid.uuid4()),
        "component": component,
        "working_directory": str(tmp_path.resolve()),
        "argv": [sys.executable, "-c", code],
        "input_refs": [{"name": "input", "path": str(tmp_path / "input.txt")}],
        "output_refs": [{"name": "secret-result", "path": str(tmp_path / "result.json")}],
        "metadata": {"direction_id": None, "stage": None, "effect_id": None},
    }


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_validate_spec_rejects_noncanonical_or_shell_shaped_inputs(tmp_path: Path) -> None:
    spec = _spec(tmp_path, "pass")
    spec["experiment_id"] = "not-a-uuid"
    with pytest.raises(SpecValidationError):
        validate_spec(spec)

    spec = _spec(tmp_path, "pass")
    spec["working_directory"] = "."
    with pytest.raises(SpecValidationError):
        validate_spec(spec)

    spec = _spec(tmp_path, "pass")
    spec["argv"] = "program --flag"
    with pytest.raises(SpecValidationError):
        validate_spec(spec)


def test_success_records_exact_files_and_separate_logs(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    terminal = run_long_effect(
        _spec(
            tmp_path,
            "import sys; print('public-out'); print('private-err', file=sys.stderr)",
        ),
        run_root,
    )

    assert terminal["phase"] == "CHILD_EXITED"
    assert terminal["exit_code"] == 0
    assert terminal["exception_category"] is None
    assert {path.name for path in run_root.iterdir()} == EXPECTED_FILES
    assert run_root.joinpath("stdout.log").read_text(encoding="utf-8") == "public-out\n"
    assert run_root.joinpath("stderr.log").read_text(encoding="utf-8") == "private-err\n"
    assert set(_load(run_root / "terminal.json")) == {
        "phase",
        "pid",
        "started_at",
        "finished_at",
        "exit_code",
        "exception_category",
    }
    for name in ("experiment.json", "owner.json", "terminal.json"):
        assert isinstance(_load(run_root / name), dict)


def test_nonzero_exit_is_recorded_without_interpretation(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    terminal = run_long_effect(_spec(tmp_path, "raise SystemExit(7)"), run_root)
    assert terminal["phase"] == "CHILD_EXITED"
    assert terminal["exit_code"] == 7
    assert terminal["exception_category"] is None


def test_pre_child_error_is_terminal_and_does_not_add_files(tmp_path: Path) -> None:
    spec = _spec(tmp_path, "pass")
    spec["argv"] = [str(tmp_path / "missing-executable")]
    run_root = tmp_path / "run"
    terminal = run_long_effect(spec, run_root)
    assert terminal["phase"] == "PRE_CHILD_ERROR"
    assert terminal["pid"] is None
    assert terminal["exit_code"] is None
    assert terminal["exception_category"] == "FileNotFoundError"
    assert {path.name for path in run_root.iterdir()} == EXPECTED_FILES


def test_post_child_error_is_recorded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakeChild:
        pid = 8123
        returncode = None

        def wait(self) -> int:
            raise OSError("simulated wait failure")

    monkeypatch.setattr(long_effect.subprocess, "Popen", lambda *args, **kwargs: FakeChild())
    terminal = run_long_effect(_spec(tmp_path, "pass"), tmp_path / "run")
    assert terminal["phase"] == "POST_CHILD_ERROR"
    assert terminal["pid"] == 8123
    assert terminal["exit_code"] is None
    assert terminal["exception_category"] == "OSError"


def test_operator_interrupt_is_propagated_after_child_is_reaped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class InterruptOnceChild:
        pid = 8125
        returncode = None
        wait_count = 0

        def wait(self) -> int:
            self.wait_count += 1
            if self.wait_count == 1:
                raise KeyboardInterrupt()
            self.returncode = 0
            return 0

    child = InterruptOnceChild()
    monkeypatch.setattr(long_effect.subprocess, "Popen", lambda *args, **kwargs: child)
    run_root = tmp_path / "run"

    with pytest.raises(KeyboardInterrupt):
        run_long_effect(_spec(tmp_path, "pass"), run_root)

    assert child.wait_count == 2
    assert child.returncode == 0
    assert run_root.joinpath("owner.json").is_file()
    assert not run_root.joinpath("terminal.json").exists()


def test_concurrent_claim_starts_only_one_child(tmp_path: Path) -> None:
    counter = tmp_path / "starts.txt"
    run_root = tmp_path / "run"
    spec = _spec(
        tmp_path,
        f"from pathlib import Path; Path({str(counter)!r}).open('a').write('start\\n')",
    )
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def invoke() -> None:
        barrier.wait()
        try:
            run_long_effect(spec, run_root)
        except RunRootConflict:
            outcomes.append("conflict")
        else:
            outcomes.append("ran")

    threads = [threading.Thread(target=invoke), threading.Thread(target=invoke)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert sorted(outcomes) == ["conflict", "ran"]
    assert counter.read_text(encoding="utf-8").splitlines() == ["start"]
    assert {path.name for path in run_root.iterdir()} == EXPECTED_FILES


def test_owner_is_published_before_child_creation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run_root = tmp_path / "run"

    class FakeChild:
        pid = 8124
        returncode = 0

        def wait(self) -> int:
            return 0

    def checked_popen(*args, **kwargs):
        assert _load(run_root / "owner.json")["owner_pid"] == os.getpid()
        assert _load(run_root / "experiment.json")["schema"] == "HMASD_LONG_EFFECT_V1"
        return FakeChild()

    monkeypatch.setattr(long_effect.subprocess, "Popen", checked_popen)
    terminal = run_long_effect(_spec(tmp_path, "pass"), run_root)
    assert terminal["phase"] == "CHILD_EXITED"


@pytest.mark.parametrize("name", ["experiment.json", "owner.json", "terminal.json"])
def test_immutable_json_final_path_is_never_partially_visible(
    name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    final_path = tmp_path / name
    link_reached = threading.Event()
    release_link = threading.Event()
    original_link = long_effect.os.link

    def delayed_link(source, destination):
        link_reached.set()
        assert release_link.wait(timeout=5)
        return original_link(source, destination)

    monkeypatch.setattr(long_effect.os, "link", delayed_link)
    failure: list[BaseException] = []

    def publish() -> None:
        try:
            long_effect._publish_json_no_overwrite(final_path, {"complete": True})
        except BaseException as exc:  # pragma: no cover - retained for assertion
            failure.append(exc)

    thread = threading.Thread(target=publish)
    thread.start()
    assert link_reached.wait(timeout=5)
    assert final_path.exists() is False
    release_link.set()
    thread.join(timeout=5)

    assert failure == []
    assert _load(final_path) == {"complete": True}


def test_reentry_preserves_every_published_byte(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    spec = _spec(tmp_path, "print('once')")
    run_long_effect(spec, run_root)
    before = {path.name: path.read_bytes() for path in run_root.iterdir()}

    with pytest.raises(RunRootConflict):
        run_long_effect(spec, run_root)

    after = {path.name: path.read_bytes() for path in run_root.iterdir()}
    assert after == before


def test_observe_reports_owner_without_terminal_without_reading_outputs(tmp_path: Path) -> None:
    run_root = tmp_path / "incomplete"
    run_root.mkdir()
    spec = _spec(tmp_path, "pass", component="visible-component")
    (run_root / "experiment.json").write_text(json.dumps(spec), encoding="utf-8")
    (run_root / "owner.json").write_text(
        json.dumps({"owner_pid": 1, "acquired_at": "2026-01-01T00:00:00Z"}),
        encoding="utf-8",
    )
    (run_root / "stdout.log").write_text("sensitive stdout", encoding="utf-8")
    (run_root / "stderr.log").write_text("sensitive stderr", encoding="utf-8")
    secret_output = Path(spec["output_refs"][0]["path"])
    secret_output.write_text("sensitive science value 12345", encoding="utf-8")

    observed = observe_long_effect(run_root)
    rendered = json.dumps(observed)
    assert observed["owner_without_terminal"] is True
    assert observed["terminal"] is None
    assert observed["experiment"] == {
        "schema": "HMASD_LONG_EFFECT_V1",
        "experiment_id": spec["experiment_id"],
        "component": "visible-component",
        "metadata": spec["metadata"],
    }
    assert "output_refs" not in rendered
    assert "sensitive" not in rendered
    assert "12345" not in rendered


def test_observe_reports_invalid_metadata_by_category_only(tmp_path: Path) -> None:
    run_root = tmp_path / "damaged"
    run_root.mkdir()
    (run_root / "experiment.json").write_bytes(b"{partial")
    observed = observe_long_effect(run_root)
    assert observed["record_errors"] == {"experiment.json": "JSONDecodeError"}
    assert observed["owner_without_terminal"] is False


def test_implementation_contains_no_forbidden_process_mechanisms() -> None:
    source = inspect.getsource(long_effect).lower()
    forbidden_words = ("detach", "heartbeat", "retry", "ready", "cancelled")
    for word in forbidden_words:
        assert re.search(rf"\b{word}\b", source) is None
    assert "creationflags" not in source
    assert "start_new_session" not in source
    assert "shell=false" in source
    assert "os.link" in source


def test_environment_is_inherited_but_not_serialized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HMASD_LONG_EFFECT_TEST_SECRET", "inherited-value")
    run_root = tmp_path / "run"
    run_long_effect(
        _spec(
            tmp_path,
            "import os; print(os.environ['HMASD_LONG_EFFECT_TEST_SECRET'])",
        ),
        run_root,
    )
    assert run_root.joinpath("stdout.log").read_text(encoding="utf-8") == "inherited-value\n"
    for name in ("experiment.json", "owner.json", "terminal.json"):
        assert b"inherited-value" not in run_root.joinpath(name).read_bytes()
