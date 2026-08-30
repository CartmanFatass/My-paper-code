from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any
from scripts import hmasd_local_check as local_check


ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.email", "local-check@example.invalid")
    _git(repo, "config", "user.name", "Local Check")
    (repo / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "--quiet", "-m", "baseline")
    return repo


def _commit(repo: Path, *paths: str) -> None:
    _git(repo, "add", *paths)
    _git(repo, "commit", "--quiet", "-m", "fixture")


def _invoke(capsys, *argv: str) -> tuple[int, dict[str, Any]]:
    code = local_check.main(list(argv))
    payload = json.loads(capsys.readouterr().out)
    return code, payload


def _checks(payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {check["name"]: check for check in payload["checks"]}


def _working_tree_bytes(repo: Path) -> dict[str, bytes]:
    return {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in repo.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(repo).parts
    }


def test_established_state_paths_are_classified() -> None:
    assert (
        local_check.state_kind(
            "docs/research/candidates/example/workflow/research/state.json"
        )
        == "research_state"
    )
    assert (
        local_check.state_kind(
            "docs/research/candidates/example/workflow/engineering/state.json"
        )
        == "engineering_state"
    )
    assert (
        local_check.state_kind(
            "docs/research/candidates/example/workflow/external-review/index.json"
        )
        == "external_review_index"
    )


def test_no_change_passes_and_checks_present_core_state(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    registry = ROOT / "tests" / "fixtures" / "hmasd_phase0" / "portfolio_registry.json"
    target = repo / "docs/research/portfolio/workflow/registry.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(registry.read_bytes())
    _commit(repo, "docs/research/portfolio/workflow/registry.json")

    code, payload = _invoke(capsys, "--repo", str(repo), "--no-tests")

    assert code == 0
    assert payload["status"] == "PASS"
    assert payload["changed_paths"] == []
    checks = _checks(payload)
    assert checks["git_diff_check"]["status"] == "PASS"
    assert checks["state:docs/research/portfolio/workflow/registry.json"]["status"] == "PASS"
    assert checks["state:.omp/runtime/agents.json"]["status"] == "SKIPPED"
    assert checks["state:.omp/runtime/worktrees.json"]["status"] == "SKIPPED"


def test_invalid_repository_emits_json_and_exit_two(tmp_path: Path, capsys) -> None:
    code, payload = _invoke(capsys, "--repo", str(tmp_path / "missing"))

    assert code == 2
    assert payload == {
        "changed_paths": [],
        "checks": [],
        "failures": [f"repo: not a directory: {tmp_path / 'missing'}"],
        "selected_tests": [],
        "status": "INVALID_INPUT",
    }


def test_changed_research_state_is_validated_without_selecting_a_suite(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    source = ROOT / "tests" / "fixtures" / "hmasd_phase0" / "research_state.json"
    target = repo / "docs/research/candidates/example-direction/workflow/research/state.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(source.read_bytes())

    code, payload = _invoke(capsys, "--repo", str(repo))

    assert code == 0
    assert payload["status"] == "PASS"
    assert payload["selected_tests"] == []
    assert _checks(payload)[f"state:{target.relative_to(repo).as_posix()}"]["status"] == "PASS"
    assert _checks(payload)["focused_tests"]["status"] == "SKIPPED"


def test_python_syntax_failure_is_path_specific(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    target = repo / "scripts/broken.py"
    target.parent.mkdir()
    target.write_text("def broken(:\n", encoding="utf-8")

    code, payload = _invoke(capsys, "--repo", str(repo), "--no-tests")

    assert code == 1
    assert payload["status"] == "FAIL"
    assert _checks(payload)["compile:scripts/broken.py"]["status"] == "FAIL"
    assert any(failure.startswith("scripts/broken.py:") for failure in payload["failures"])


def test_whitespace_failure_is_reported(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    target = repo / "notes.txt"
    target.write_text("initial\n", encoding="utf-8")
    _commit(repo, "notes.txt")
    target.write_text("trailing space \n", encoding="utf-8")

    code, payload = _invoke(capsys, "--repo", str(repo), "--no-tests")

    assert code == 1
    assert _checks(payload)["git_diff_check"]["status"] == "FAIL"
    assert any("trailing whitespace" in failure for failure in payload["failures"])


def test_directly_mapped_script_selects_only_its_focused_test(tmp_path: Path, capsys, monkeypatch) -> None:
    repo = _repo(tmp_path)
    script = repo / "scripts/hmasd_local_check.py"
    test = repo / "tests/hmasd_local_check_test.py"
    script.parent.mkdir()
    test.parent.mkdir()
    script.write_text("value = 1\n", encoding="utf-8")
    test.write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    seen: list[list[str]] = []
    original = local_check._run_command

    def stub(argv, *, cwd, env=None):
        if list(argv)[1:3] == ["-m", "pytest"]:
            seen.append(list(argv))
            return subprocess.CompletedProcess(list(argv), 0, "focused pass\n", "")
        return original(argv, cwd=cwd, env=env)

    monkeypatch.setattr(local_check, "_run_command", stub)

    code, payload = _invoke(capsys, "--repo", str(repo))

    assert code == 0
    assert payload["selected_tests"] == ["tests/hmasd_local_check_test.py"]
    assert seen == [[local_check.sys.executable, "-m", "pytest", "-q", "tests/hmasd_local_check_test.py"]]
    assert _checks(payload)["focused_tests"] == {
        "name": "focused_tests",
        "status": "PASS",
        "output": "focused pass\n",
    }


def test_focused_tests_fall_back_to_uv_when_pytest_is_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(local_check.importlib.util, "find_spec", lambda _name: None)
    monkeypatch.setattr(local_check.shutil, "which", lambda _name: "/usr/bin/uv")

    assert local_check._pytest_argv(["tests/focused_test.py"]) == [
        "/usr/bin/uv",
        "run",
        "--with",
        "pytest",
        "--with",
        "jsonschema",
        "pytest",
        "-q",
        "tests/focused_test.py",
    ]


def test_no_tests_preserves_selection_without_launching_pytest(tmp_path: Path, capsys, monkeypatch) -> None:
    repo = _repo(tmp_path)
    script = repo / "scripts/hmasd_local_check.py"
    test = repo / "tests/hmasd_local_check_test.py"
    script.parent.mkdir()
    test.parent.mkdir()
    script.write_text("value = 1\n", encoding="utf-8")
    test.write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")

    original = local_check._run_command

    def stub(argv, *, cwd, env=None):
        if list(argv)[1:3] == ["-m", "pytest"]:
            raise AssertionError("pytest must not run with --no-tests")
        return original(argv, cwd=cwd, env=env)
    monkeypatch.setattr(local_check, "_run_command", stub)

    code, payload = _invoke(capsys, "--repo", str(repo), "--no-tests")

    assert code == 0
    assert payload["selected_tests"] == ["tests/hmasd_local_check_test.py"]
    assert _checks(payload)["focused_tests"] == {
        "name": "focused_tests",
        "status": "SKIPPED",
        "output": "disabled",
    }


def test_scope_filters_changed_paths_and_compilation(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    (repo / "inside.py").write_text("value = 1\n", encoding="utf-8")
    (repo / "outside.py").write_text("def broken(:\n", encoding="utf-8")

    code, payload = _invoke(capsys, "--repo", str(repo), "--scope", "inside.py", "--no-tests")

    assert code == 0
    assert payload["changed_paths"] == ["inside.py"]
    assert "compile:inside.py" in _checks(payload)
    assert "compile:outside.py" not in _checks(payload)


def test_check_does_not_mutate_repository_bytes(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    target = repo / "scripts/changed.py"
    target.parent.mkdir()
    target.write_text("value = 1\n", encoding="utf-8")
    before = _working_tree_bytes(repo)

    code, payload = _invoke(capsys, "--repo", str(repo), "--no-tests")

    assert code == 0
    assert payload["status"] == "PASS"
    assert _working_tree_bytes(repo) == before
    assert not (target.parent / "__pycache__").exists()
