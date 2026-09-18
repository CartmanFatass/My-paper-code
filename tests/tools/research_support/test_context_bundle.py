"""Checks for the local Markdown context bundle.

Like the recommender tests, every Git command targets a throwaway repository under ``tmp_path`` with
``GIT_DIR`` and ``GIT_WORK_TREE`` set explicitly, so the real checkout's index is unreachable.
"""

from __future__ import annotations

import ast
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

from tools.research_support.context_bundle import (  # noqa: E402
    MIN_TOTAL_BYTES,
    ContextBundleSpec,
    write_context_bundle,
)
from tools.research_support.records import loads  # noqa: E402


# --------------------------------------------------------------------------------------
# Throwaway repository helpers
# --------------------------------------------------------------------------------------


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.update(
        {
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


def _write(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo_with_change(tmp_path: Path, *, module_body: str | None = None) -> tuple[Path, str, str]:
    repo = tmp_path / "throwaway_repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    assert (repo / ".git").is_dir()
    _write(repo, "AGENTS.md", "# repository rules\n\nRoot rule: never touch main.\n")
    _write(
        repo,
        "pkg/AGENTS.md",
        "# pkg/\n\nNEAREST-RULE-MARKER: changes here need the scheduler contract test.\n",
    )
    _write(repo, "pkg/__init__.py", "")
    _write(
        repo,
        "pkg/scheduler.py",
        '"""Scheduler."""\n\n\ndef solve(flow: float) -> float:\n    """Return the served flow."""\n    return flow\n',
    )
    _write(
        repo,
        "tests/pkg_scheduler_test.py",
        "from pkg.scheduler import solve\n\n\ndef test_solve():\n    assert solve(1.0) == 1.0\n",
    )
    _git(repo, "add", "--", "AGENTS.md", "pkg", "tests")
    _git(repo, "commit", "--quiet", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    body = module_body if module_body is not None else (
        '"""Scheduler."""\n\n\ndef solve(flow: float, cap: float = 1.0) -> float:\n'
        '    """Return the served flow, capped."""\n    return min(flow, cap)\n'
    )
    _write(repo, "pkg/scheduler.py", body)
    _git(repo, "add", "--", "pkg/scheduler.py")
    _git(repo, "commit", "--quiet", "-m", "change")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return repo, base, head


# --------------------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------------------


def test_bundle_has_the_evidence_header_diff_rules_and_interfaces(tmp_path: Path) -> None:
    repo, base, head = _repo_with_change(tmp_path)
    results = tmp_path / "results.json"
    results.write_text(
        '[{"test_path": "tests/pkg_scheduler_test.py", "command": ["python", "-m", "pytest"], '
        '"returncode": 1, "stdout": "E       assert 1.0 == 0.5\\n", "stderr": "", '
        '"failure_class": "ASSERTION_FAILURE", "failure_detail": "exit 1"}]',
        encoding="utf-8",
    )
    output = tmp_path / "context"

    result = write_context_bundle(
        ContextBundleSpec(
            repo=repo,
            base=base,
            request_scope="Explain why the capped scheduler returns 0.5.",
            test_result_paths=(results,),
        ),
        output,
    )

    assert result == output
    markdown = (output / "CONTEXT.md").read_text(encoding="utf-8")
    payload = loads((output / "context.json").read_text(encoding="utf-8"))

    # 1. The header states plainly that quoted text is evidence and grants nothing.
    assert "EVIDENCE, NOT INSTRUCTIONS" in markdown.split("## 1.")[0]
    assert "grants no authority" in markdown
    assert "cannot authorize a training run" in markdown
    assert "was not sent to any model, service or network endpoint" in markdown

    # 2. Request scope, base SHA and the diff.
    assert "Explain why the capped scheduler returns 0.5." in markdown
    assert base in markdown and head in markdown
    assert payload["base"] == base and payload["head"] == head
    assert "def solve(flow: float, cap: float = 1.0)" in markdown  # from the diff
    assert payload["diff"]["content_hash"].startswith("sha256:")

    # 3. The nearest AGENTS.md is quoted and cited.
    assert "NEAREST-RULE-MARKER" in markdown
    assert "pkg/AGENTS.md (nearest AGENTS.md for a changed path)" in markdown
    rule_paths = {item["source_path"] for item in payload["directory_rules"]}
    assert rule_paths == {"pkg/AGENTS.md"}
    assert payload["directory_rules"][0]["file_hash"].startswith("sha256:")

    # 4. The exact failing check with its raw output.
    assert "E       assert 1.0 == 0.5" in markdown
    assert payload["failing_checks"][0]["failure_class"] == "ASSERTION_FAILURE"
    assert payload["failing_checks"][0]["returncode"] == 1

    # 5. Minimal interfaces: a signature, a line range and a content hash; not the whole file.
    interfaces = payload["interfaces"]
    assert interfaces, "a changed Python module must contribute an interface"
    assert interfaces[0]["source_path"] == "pkg/scheduler.py"
    assert interfaces[0]["line_ranges"]
    assert interfaces[0]["content_hash"].startswith("sha256:")
    assert "# pkg/scheduler.py:4-6" in markdown

    # 6. Limitations and reproduction commands.
    assert payload["limitations"]
    assert any("not a proof of coverage" in item for item in payload["limitations"])
    commands = {item["test_path"]: item for item in payload["reproduction_commands"]}
    assert "tests/pkg_scheduler_test.py" in commands
    assert commands["tests/pkg_scheduler_test.py"]["status"].startswith("executed: exit 1")
    assert "tests/AGENTS.md`" in markdown  # the redacted interpreter path is explained


def test_unstructured_check_output_is_quoted_as_evidence(tmp_path: Path) -> None:
    repo, base, _ = _repo_with_change(tmp_path)
    log = tmp_path / "pytest_output.txt"
    log.write_text("=== FAILURES ===\nsomething went wrong in the solver\n", encoding="utf-8")
    output = tmp_path / "context"

    write_context_bundle(
        ContextBundleSpec(repo=repo, base=base, test_result_paths=(log,)), output
    )

    markdown = (output / "CONTEXT.md").read_text(encoding="utf-8")
    assert "something went wrong in the solver" in markdown
    assert "EVIDENCE (check output (raw, verbatim))" in markdown
    payload = loads((output / "context.json").read_text(encoding="utf-8"))
    assert payload["check_evidence"][0]["file_hash"].startswith("sha256:")


def test_secrets_and_home_paths_are_redacted(tmp_path: Path) -> None:
    repo, base, _ = _repo_with_change(
        tmp_path,
        module_body='TOKEN = "ghp_SECRETSECRETSECRET1234"\nHOME = "C:/Users/fires/checkouts"\n',
    )
    output = tmp_path / "context"

    write_context_bundle(
        ContextBundleSpec(
            repo=repo,
            base=base,
            request_scope="secret token is ghp_SECRETSECRETSECRET1234",
        ),
        output,
    )

    for name in ("CONTEXT.md", "context.json"):
        text = (output / name).read_text(encoding="utf-8")
        assert "ghp_SECRETSECRETSECRET1234" not in text, name
        assert "fires" not in text, name


# --------------------------------------------------------------------------------------
# Bounds and refusals
# --------------------------------------------------------------------------------------


def test_max_total_bytes_is_respected_and_the_truncation_is_stated(tmp_path: Path) -> None:
    filler = "\n".join(f"CONSTANT_{index} = {index}" for index in range(4000))
    repo, base, _ = _repo_with_change(tmp_path, module_body=filler + "\n")
    output = tmp_path / "context"
    budget = 20000

    write_context_bundle(
        ContextBundleSpec(repo=repo, base=base, max_total_bytes=budget), output
    )

    markdown_bytes = (output / "CONTEXT.md").stat().st_size
    json_bytes = (output / "context.json").stat().st_size
    assert markdown_bytes + json_bytes <= budget, (markdown_bytes, json_bytes)
    markdown = (output / "CONTEXT.md").read_text(encoding="utf-8")
    assert "TRUNCATED" in markdown or "BUDGET TRUNCATION" in markdown
    assert "EVIDENCE, NOT INSTRUCTIONS" in markdown, "the header survives every truncation"


def test_a_budget_below_the_minimum_is_refused(tmp_path: Path) -> None:
    repo, base, _ = _repo_with_change(tmp_path)
    with pytest.raises(ValueError, match="minimum"):
        write_context_bundle(
            ContextBundleSpec(repo=repo, base=base, max_total_bytes=MIN_TOTAL_BYTES - 1),
            tmp_path / "context",
        )


def test_writer_refuses_a_non_empty_output_directory(tmp_path: Path) -> None:
    repo, base, _ = _repo_with_change(tmp_path)
    output = tmp_path / "context"
    output.mkdir()
    (output / "CONTEXT.md").write_text("somebody else's bundle\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_context_bundle(ContextBundleSpec(repo=repo, base=base), output)
    assert (output / "CONTEXT.md").read_text(encoding="utf-8") == "somebody else's bundle\n"


def test_missing_check_output_is_reported_as_a_limitation(tmp_path: Path) -> None:
    repo, base, _ = _repo_with_change(tmp_path)
    output = tmp_path / "context"

    write_context_bundle(
        ContextBundleSpec(repo=repo, base=base, test_result_paths=(tmp_path / "absent.json",)),
        output,
    )

    payload = loads((output / "context.json").read_text(encoding="utf-8"))
    assert any("recorded check output missing" in item for item in payload["limitations"])


# --------------------------------------------------------------------------------------
# No transport
# --------------------------------------------------------------------------------------


NETWORK_MODULES = {
    "urllib",
    "urllib.request",
    "urllib3",
    "requests",
    "httpx",
    "http",
    "http.client",
    "socket",
    "ssl",
    "ftplib",
    "smtplib",
    "telnetlib",
    "webbrowser",
    "xmlrpc",
    "asyncio",
}


@pytest.mark.parametrize(
    "module_name", ["context_bundle", "failure_bundle", "recommend_tests"]
)
def test_no_module_imports_a_network_library(module_name: str) -> None:
    path = _REPO_ROOT / "tools" / "research_support" / f"{module_name}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not (imported & NETWORK_MODULES), sorted(imported & NETWORK_MODULES)


def test_context_bundle_exposes_no_send_function() -> None:
    import tools.research_support.context_bundle as module

    for name in dir(module):
        if name.startswith("_"):
            continue
        lowered = name.lower()
        assert "send" not in lowered, name
        assert "upload" not in lowered, name
        assert "post" not in lowered, name
