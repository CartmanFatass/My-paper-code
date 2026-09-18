"""Checks for change-aware test recommendation and failure classification.

Every Git command in this file targets a throwaway repository created under ``tmp_path``. ``GIT_DIR``
and ``GIT_WORK_TREE`` are set explicitly on every invocation, so even a failed ``git init`` cannot
let a later command walk up into the real checkout and touch its shared index.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
# "tests/tools" is itself a namespace portion called "tools". If it precedes the checkout root on
# sys.path, "tools.research_support" binds to this test directory instead of the real package, so
# the checkout root is forced to the front and a wrongly bound package is dropped.
while str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT))
_bound = sys.modules.get("tools.research_support")
if _bound is not None and not str(getattr(_bound, "__file__", "")).startswith(
    str(_REPO_ROOT / "tools")
):
    for _name in [n for n in list(sys.modules) if n == "tools" or n.startswith("tools.")]:
        del sys.modules[_name]

from tools.research_support.recommend_tests import (  # noqa: E402
    CONTROL_PLANE_INTERPRETER,
    SCIENTIFIC_INTERPRETER,
    FailureClass,
    GitCommandRefused,
    RecommendationError,
    SelectionRefused,
    classify_failure,
    interpreter_for_test,
    main,
    recommend_tests,
    run_read_only_git,
    run_recommended,
)


# --------------------------------------------------------------------------------------
# Throwaway repository helpers
# --------------------------------------------------------------------------------------


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run one Git command that can only ever see the throwaway repository."""

    environment = dict(os.environ)
    environment.update(
        {
            # Explicit paths: git never searches upward, so the real checkout is unreachable.
            "GIT_DIR": str(repo / ".git"),
            "GIT_WORK_TREE": str(repo),
            "GIT_CEILING_DIRECTORIES": str(repo.parent),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(repo / "absent-gitconfig"),
            "GIT_AUTHOR_NAME": "research support test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "research support test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return subprocess.run(
        ["git", *arguments],
        cwd=str(repo),
        env=environment,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def _write(repo: Path, relative: str, text: str) -> Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "throwaway_repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    assert (repo / ".git").is_dir(), "git init did not create the throwaway repository"
    return repo


def _commit(repo: Path, paths: list[str], message: str) -> str:
    _git(repo, "add", "--", *paths)
    _git(repo, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _base_repo(tmp_path: Path) -> tuple[Path, str]:
    """A repository whose first commit contains the test files the mapping table expects."""

    repo = _init_repo(tmp_path)
    _write(repo, "AGENTS.md", "# root rules\n")
    _write(repo, "tools/research_support/failure_bundle.py", "VALUE = 1\n")
    _write(
        repo,
        "tests/tools/research_support/test_failure_bundle.py",
        "from tools.research_support import failure_bundle\n\n\ndef test_placeholder():\n    assert True\n",
    )
    _write(repo, "tests/skills/test_control_alignment.py", "def test_placeholder():\n    assert True\n")
    _write(repo, "envs/pettingzoo/uav_cpp_backend.py", "BACKEND = 'native'\n")
    _write(repo, "tests/uav_cpp_backend_test.py", "def test_placeholder():\n    assert True\n")
    base = _commit(
        repo,
        [
            "AGENTS.md",
            "tools/research_support/failure_bundle.py",
            "tests/tools/research_support/test_failure_bundle.py",
            "tests/skills/test_control_alignment.py",
            "envs/pettingzoo/uav_cpp_backend.py",
            "tests/uav_cpp_backend_test.py",
        ],
        "base",
    )
    return repo, base


# --------------------------------------------------------------------------------------
# Diff resolution and mapping
# --------------------------------------------------------------------------------------


def test_mapped_test_is_found_with_shas_and_the_exact_git_command(tmp_path: Path) -> None:
    repo, base = _base_repo(tmp_path)
    _write(repo, "tools/research_support/failure_bundle.py", "VALUE = 2\n")
    head = _commit(repo, ["tools/research_support/failure_bundle.py"], "change")

    report = recommend_tests(repo, base=base, head="HEAD")

    assert report.base == base
    assert report.head == head
    assert len(report.base) == 40 and len(report.head) == 40
    assert report.changed_files == ["tools/research_support/failure_bundle.py"]
    mapped = {
        r.test_path: r for r in report.recommendations if r.confidence == "direct_mapping"
    }
    assert "tests/tools/research_support/test_failure_bundle.py" in mapped
    recommendation = mapped["tests/tools/research_support/test_failure_bundle.py"]
    assert "tools/research_support/**" in recommendation.reason
    assert recommendation.interpreter == SCIENTIFIC_INTERPRETER

    # The exact command, with its exit code, is preserved for the reader.
    diff_commands = [c for c in report.git_commands if "diff" in c["command"]]
    assert diff_commands, report.git_commands
    assert diff_commands[0]["command"] == [
        "git",
        "-C",
        str(repo),
        "--no-pager",
        "diff",
        "--name-only",
        f"{base}..{head}",
    ]
    assert diff_commands[0]["returncode"] == 0
    assert any("diff resolved with: git -C" in note for note in report.notes)
    assert any("not a proof of coverage" in note for note in report.notes)
    assert report.to_json()["coverage_claim"].startswith("none")


def test_import_dependency_is_reported_when_no_mapping_matches(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write(repo, "pkg/__init__.py", "")
    _write(repo, "pkg/solver.py", "def solve():\n    return 1\n")
    _write(
        repo,
        "tests/pkg_solver_test.py",
        "from pkg.solver import solve\n\n\ndef test_solve():\n    assert solve() == 1\n",
    )
    base = _commit(repo, ["pkg/__init__.py", "pkg/solver.py", "tests/pkg_solver_test.py"], "base")
    _write(repo, "pkg/solver.py", "def solve():\n    return 2\n")
    _commit(repo, ["pkg/solver.py"], "change")

    report = recommend_tests(repo, base=base)

    by_path = {r.test_path: r for r in report.recommendations}
    assert "tests/pkg_solver_test.py" in by_path
    assert by_path["tests/pkg_solver_test.py"].confidence == "import_dependency"
    assert "imports pkg.solver directly" in by_path["tests/pkg_solver_test.py"].reason


def test_one_hop_import_dependency_is_reported(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write(repo, "pkg/__init__.py", "")
    _write(repo, "pkg/kernel.py", "STEP = 1\n")
    _write(repo, "pkg/facade.py", "from pkg.kernel import STEP\n")
    _write(
        repo,
        "tests/facade_test.py",
        "import pkg.facade\n\n\ndef test_facade():\n    assert pkg.facade.STEP == 1\n",
    )
    base = _commit(
        repo,
        ["pkg/__init__.py", "pkg/kernel.py", "pkg/facade.py", "tests/facade_test.py"],
        "base",
    )
    _write(repo, "pkg/kernel.py", "STEP = 2\n")
    _commit(repo, ["pkg/kernel.py"], "change")

    report = recommend_tests(repo, base=base)

    by_path = {r.test_path: r for r in report.recommendations}
    assert "tests/facade_test.py" in by_path
    assert by_path["tests/facade_test.py"].confidence == "import_dependency"
    assert "one hop" in by_path["tests/facade_test.py"].reason


def test_filename_heuristic_is_labelled_as_such(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write(repo, "widgets/scheduler_policy.py", "RATE = 1\n")
    # No import edge: the test loads the module dynamically, which static analysis cannot follow.
    _write(
        repo,
        "tests/scheduler_policy_test.py",
        "import importlib.util\n\n\ndef test_dynamic():\n    assert importlib.util is not None\n",
    )
    base = _commit(
        repo, ["widgets/scheduler_policy.py", "tests/scheduler_policy_test.py"], "base"
    )
    _write(repo, "widgets/scheduler_policy.py", "RATE = 2\n")
    _commit(repo, ["widgets/scheduler_policy.py"], "change")

    report = recommend_tests(repo, base=base)

    by_path = {r.test_path: r for r in report.recommendations}
    assert by_path["tests/scheduler_policy_test.py"].confidence == "heuristic"
    assert any("dynamically" in item for item in report.unresolved_coverage)


# --------------------------------------------------------------------------------------
# Unresolved coverage
# --------------------------------------------------------------------------------------


def test_native_backend_change_lands_in_unresolved_coverage(tmp_path: Path) -> None:
    repo, base = _base_repo(tmp_path)
    _write(repo, "envs/pettingzoo/uav_cpp_backend.py", "BACKEND = 'native2'\n")
    _commit(repo, ["envs/pettingzoo/uav_cpp_backend.py"], "native change")

    report = recommend_tests(repo, base=base)

    assert "tests/uav_cpp_backend_test.py" in report.selected_paths()
    native_statements = [
        item for item in report.unresolved_coverage if "uav_cpp_backend.py" in item
    ]
    assert any("native" in item or "compiled" in item for item in native_statements), (
        report.unresolved_coverage
    )
    assert any("cross-route" in item for item in report.unresolved_coverage)
    artifacts = {
        artifact
        for r in report.recommendations
        for artifact in r.external_artifacts
    }
    assert any("cpp_extension" in artifact for artifact in artifacts), artifacts


def test_unmapped_change_is_reported_as_unknown_coverage(tmp_path: Path) -> None:
    repo, base = _base_repo(tmp_path)
    _write(repo, "docs/notes/unrelated.txt", "text\n")
    _commit(repo, ["docs/notes/unrelated.txt"], "unmapped change")

    report = recommend_tests(repo, base=base)

    assert any(
        "docs/notes/unrelated.txt" in item and "coverage for this change is unknown" in item
        for item in report.unresolved_coverage
    ), report.unresolved_coverage


# --------------------------------------------------------------------------------------
# Interpreter resolution (tests/AGENTS.md)
# --------------------------------------------------------------------------------------


def test_control_plane_and_scientific_interpreters_are_resolved_per_path(tmp_path: Path) -> None:
    repo, base = _base_repo(tmp_path)
    _write(repo, ".agents/skills/hmasd-research-engineering/SKILL.md", "# method\n")
    _write(repo, "tools/research_support/failure_bundle.py", "VALUE = 3\n")
    _commit(
        repo,
        [".agents/skills/hmasd-research-engineering/SKILL.md", "tools/research_support/failure_bundle.py"],
        "control plane and scientific change",
    )

    report = recommend_tests(repo, base=base)
    by_path = {r.test_path: r for r in report.recommendations}

    assert by_path["tests/skills/test_control_alignment.py"].interpreter == CONTROL_PLANE_INTERPRETER
    assert (
        by_path["tests/tools/research_support/test_failure_bundle.py"].interpreter
        == SCIENTIFIC_INTERPRETER
    )
    assert by_path["tests/skills/test_control_alignment.py"].to_json()["command"][0] == (
        CONTROL_PLANE_INTERPRETER
    )


def test_interpreter_for_test_follows_the_documented_rule() -> None:
    assert interpreter_for_test("tests/skills/test_scientific_tools.py") == CONTROL_PLANE_INTERPRETER
    assert interpreter_for_test("tests/hmasd_run_test.py") == SCIENTIFIC_INTERPRETER
    assert interpreter_for_test("tests\\envs\\uav_service_restoration\\test_env_lifecycle.py") == (
        SCIENTIFIC_INTERPRETER
    )


# --------------------------------------------------------------------------------------
# Read-only Git guard
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("subcommand", ["add", "commit", "checkout", "stash", "reset", "clean"])
def test_mutating_git_subcommands_are_refused(tmp_path: Path, subcommand: str) -> None:
    repo = _init_repo(tmp_path)
    with pytest.raises(GitCommandRefused) as error:
        run_read_only_git(repo, [subcommand, "--", "."])
    assert subcommand in str(error.value)


def test_an_unresolvable_revision_fails_loudly_with_the_exact_command(tmp_path: Path) -> None:
    repo, _ = _base_repo(tmp_path)
    with pytest.raises(RecommendationError) as error:
        recommend_tests(repo, base="no-such-revision")
    message = str(error.value)
    assert "no-such-revision" in message
    assert "rev-parse" in message, "the exact failing command is preserved"


# --------------------------------------------------------------------------------------
# Failure classification
# --------------------------------------------------------------------------------------


def test_each_claimed_failure_class_is_detected() -> None:
    cases = {
        FailureClass.ASSERTION_FAILURE: "E       AssertionError: assert 1 == 2\n1 failed",
        FailureClass.COLLECTION_ERROR: "ERROR collecting tests/foo_test.py\n1 error",
        FailureClass.MISSING_EXTERNAL_ARTIFACT: (
            "E   FileNotFoundError: [Errno 2] missing checkpoint: runs/x/model.pt"
        ),
        FailureClass.MISSING_OPTIONAL_DEPENDENCY: (
            "ImportError while importing test module\nE   ModuleNotFoundError: No module named 'gymnasium'"
        ),
        FailureClass.UNSUPPORTED_RUNTIME: "E   ModuleNotFoundError: No module named 'tomllib'",
        FailureClass.TOOL_PERMISSION_REFUSAL: (
            "E   PermissionError: [WinError 5] Access is denied: 'temp/out'"
        ),
    }
    for expected, text in cases.items():
        observed, detail = classify_failure(text, "", 1)
        assert observed is expected, (expected, observed, detail)
        assert "exit 1" in detail


def test_unrecognised_failure_is_unclassified_with_raw_text_preserved() -> None:
    raw = "the solver emitted a wobbly frobnicator and stopped\n"
    observed, detail = classify_failure(raw, "", 7)
    assert observed is FailureClass.UNCLASSIFIED
    assert "exit 7" in detail
    assert "wobbly frobnicator" in detail


def test_classification_never_turns_a_failure_into_a_success() -> None:
    observed, detail = classify_failure("1 failed, 2 passed", "", 1)
    assert observed is not FailureClass.UNCLASSIFIED or "exit 1" in detail
    assert observed.value != "PASSED"
    zero, zero_detail = classify_failure("2 passed", "", 0)
    assert zero is FailureClass.UNCLASSIFIED
    assert "does not certify success" in zero_detail


# --------------------------------------------------------------------------------------
# Explicit execution
# --------------------------------------------------------------------------------------


def test_run_recommended_refuses_a_path_that_was_not_recommended(tmp_path: Path) -> None:
    repo, base = _base_repo(tmp_path)
    _write(repo, "tools/research_support/failure_bundle.py", "VALUE = 4\n")
    _commit(repo, ["tools/research_support/failure_bundle.py"], "change")
    report = recommend_tests(repo, base=base)

    with pytest.raises(SelectionRefused):
        run_recommended(report, selected=["tests"], repo=repo)
    with pytest.raises(SelectionRefused):
        run_recommended(report, selected=["tests/not_recommended_test.py"], repo=repo)


@pytest.mark.skipif(
    not Path(SCIENTIFIC_INTERPRETER).exists(),
    reason=f"the scientific interpreter {SCIENTIFIC_INTERPRETER} is not present on this host",
)
def test_run_recommended_executes_only_the_selected_path_and_preserves_the_exit_code(
    tmp_path: Path,
) -> None:
    repo, base = _base_repo(tmp_path)
    _write(
        repo,
        "tests/tools/research_support/test_failure_bundle.py",
        "def test_deliberate_failure():\n    assert 1 == 2\n",
    )
    _write(repo, "tools/research_support/failure_bundle.py", "VALUE = 5\n")
    _commit(
        repo,
        [
            "tools/research_support/failure_bundle.py",
            "tests/tools/research_support/test_failure_bundle.py",
        ],
        "change",
    )
    report = recommend_tests(repo, base=base)
    selected = "tests/tools/research_support/test_failure_bundle.py"
    assert selected in report.selected_paths()

    results = run_recommended(report, selected=[selected], repo=repo, timeout_s=300.0)

    assert len(results) == 1, "only the selected path may run"
    result = results[0]
    assert result["test_path"] == selected
    assert result["command"] == [SCIENTIFIC_INTERPRETER, "-m", "pytest", "-q", selected]
    assert result["returncode"] == 1
    assert result["failure_class"] == FailureClass.ASSERTION_FAILURE.value
    assert "assert 1 == 2" in result["stdout"]  # raw output preserved verbatim
    assert "pip" not in " ".join(result["command"])


def test_exhausted_time_budget_is_reported_as_not_run(tmp_path: Path) -> None:
    repo, base = _base_repo(tmp_path)
    _write(repo, "tools/research_support/failure_bundle.py", "VALUE = 6\n")
    _commit(repo, ["tools/research_support/failure_bundle.py"], "change")
    report = recommend_tests(repo, base=base)
    selected = "tests/tools/research_support/test_failure_bundle.py"

    results = run_recommended(report, selected=[selected], repo=repo, timeout_s=0.0)

    assert results[0]["executed"] is False
    assert results[0]["status"] == "not_run_time_budget_exhausted"
    assert results[0]["returncode"] is None


def test_cli_reports_without_running_anything(tmp_path: Path, capsys) -> None:
    repo, base = _base_repo(tmp_path)
    _write(repo, "tools/research_support/failure_bundle.py", "VALUE = 7\n")
    _commit(repo, ["tools/research_support/failure_bundle.py"], "change")

    exit_code = main(["--repo", str(repo), "--base", base])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert "results" not in payload
    assert payload["report"]["base"] == base
    assert payload["report"]["recommendations"]
