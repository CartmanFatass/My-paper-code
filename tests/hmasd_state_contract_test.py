"""Current HMASD durable state contract tests."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest



ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_state.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hmasd_state"
KINDS = (
    "portfolio_registry",
    "research_state",
    "engineering_state",
    "external_review_index",
    "run_manifest",
    "accepted_result",
    "external_archive",
)


def fixture(kind: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{kind}.json").read_text(encoding="utf-8"))


def run_cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def test_retained_schema_contracts_are_present_and_strict() -> None:
    schema_dir = ROOT / "scripts" / "schemas"
    for kind in KINDS:
        schema = json.loads(
            (schema_dir / f"hmasd_{kind}.schema.json").read_text(encoding="utf-8")
        )
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"]


def test_current_state_fixtures_validate() -> None:
    for kind in KINDS:
        path = FIXTURES / f"{kind}.json"
        result = run_cli("validate", "--kind", kind, "--path", str(path))
        assert result.returncode == 0, (kind, result.stderr)


@pytest.mark.parametrize(
    "kind",
    ["agent_result", "runtime_agents", "runtime_tasks", "runtime_worktrees"],
)
def test_retired_runtime_state_kinds_are_rejected(kind: str) -> None:
    from scripts import hmasd_state

    with pytest.raises(hmasd_state.ValidationError, match="unknown state kind"):
        hmasd_state.normalize_kind(kind)


def test_state_lock_key_is_stable_for_relative_and_absolute_spellings() -> None:
    """Relative CLI paths must not bypass a lock held for their absolute form."""

    from scripts import hmasd_state

    relative = Path("temp") / "directions" / "workflow-codex-migration" / "test" / "state.json"
    absolute = Path.cwd() / relative
    lock_path = hmasd_state._lock_path(relative)
    assert lock_path == hmasd_state._lock_path(absolute)
    assert lock_path.parts[-4:-1] == (".codex", "runtime", "locks")
    assert ".omp" not in lock_path.parts

def test_unknown_version_extra_key_and_invalid_path_are_refused_without_rewrite(
    tmp_path: Path,
) -> None:
    source = fixture("research_state")
    path = tmp_path / "state.json"
    path.write_bytes(json.dumps(source, indent=2, sort_keys=True).encode() + b"\n")

    original = path.read_bytes()
    unknown = dict(source, schema_version=2)
    unknown_path = tmp_path / "unknown.json"
    unknown_path.write_bytes(json.dumps(unknown, indent=2, sort_keys=True).encode() + b"\n")
    result = run_cli("validate", "--kind", "research_state", "--path", str(unknown_path))
    assert result.returncode == 3
    assert unknown_path.read_bytes() == original.replace(b'"schema_version": 1', b'"schema_version": 2')

    extra_path = tmp_path / "extra.json"
    extra_path.write_bytes(
        json.dumps(dict(source, unexpected=True), indent=2, sort_keys=True).encode() + b"\n"
    )
    result = run_cli("validate", "--kind", "research_state", "--path", str(extra_path))
    assert result.returncode == 2
    assert extra_path.read_bytes().endswith(b"\n")

    invalid_path = dict(source)
    invalid_path["direction_ref"] = dict(source["direction_ref"], path="../outside.md")
    invalid_path_file = tmp_path / "invalid-path.json"
    invalid_path_file.write_bytes(
        json.dumps(invalid_path, indent=2, sort_keys=True).encode() + b"\n"
    )
    result = run_cli("validate", "--kind", "research_state", "--path", str(invalid_path_file))
    assert result.returncode == 2


@pytest.mark.parametrize(
    ("path", "detail"),
    [
        ("scripts/a.py:stream", "contains a colon or Windows ADS component"),
        ("scripts/a.py.", "contains a Windows-ambiguous trailing dot or space"),
        ("scripts/a.py ", "contains a Windows-ambiguous trailing dot or space"),
        ("scripts/a\x1f.py", "contains a control character"),
        ("scripts\\a.py", "must be a repository-relative POSIX path"),
        ("/absolute.py", "must be a repository-relative POSIX path"),
        ("C:/absolute.py", "must not have an absolute drive prefix"),
        ("scripts//a.py", "contains an alias component"),
        ("./scripts/a.py", "contains an alias component"),
        ("scripts/../a.py", "contains an alias component"),
    ],
)
def test_state_relative_paths_translate_canonical_path_policy_failures(
    path: str, detail: str,
) -> None:
    from scripts import hmasd_path_policy, hmasd_state

    with pytest.raises(hmasd_path_policy.PathPolicyError, match=detail):
        hmasd_path_policy.normalize_repo_path(path, label="state path")
    with pytest.raises(hmasd_state.ValidationError, match=detail):
        hmasd_state._ensure_path(path, "state path")


@pytest.mark.parametrize(
    "path",
    [
        "scripts/a.py",
        "docs/research/candidates/ucope/DIRECTION.md",
    ],
)
def test_state_relative_paths_accept_canonical_policy_paths(path: str) -> None:
    from scripts import hmasd_path_policy, hmasd_state

    assert hmasd_path_policy.normalize_repo_path(path, label="state path") == path
    hmasd_state._ensure_path(path, "state path")


def test_state_absolute_runtime_path_rules_remain_caller_specific() -> None:
    from scripts import hmasd_state

    hmasd_state._ensure_path("C:\\temp\\run.log", "runtime path", absolute=True)
    hmasd_state._ensure_path("/tmp/run.log", "runtime path", absolute=True)
    with pytest.raises(hmasd_state.ValidationError, match="must be absolute"):
        hmasd_state._ensure_path("temp/run.log", "runtime path", absolute=True)
    with pytest.raises(hmasd_state.ValidationError, match="contains NUL"):
        hmasd_state._ensure_path("C:\\temp\\run\x00.log", "runtime path", absolute=True)


def test_state_document_paths_keep_the_shared_platform_alias_seam(monkeypatch) -> None:
    from scripts import hmasd_state

    alias = ROOT / "docs" / "research" / "candidates"
    observed: list[Path] = []

    def reports_alias(path: Path, *_args: object) -> bool:
        candidate = Path(path)
        observed.append(candidate)
        return candidate == alias

    monkeypatch.setattr(
        hmasd_state.hmasd_platform,
        "is_reparse_or_symlink",
        reports_alias,
    )
    with pytest.raises(hmasd_state.OwnershipError, match="symlink or reparse"):
        hmasd_state.validate_document("research_state", fixture("research_state"))
    assert alias in observed


def test_state_authority_path_resolution_preserves_error_classification(
    tmp_path: Path, monkeypatch,
) -> None:
    from scripts import hmasd_state

    repo = tmp_path / "repo"
    evidence = repo / "docs" / "evidence.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("evidence\n", encoding="utf-8")

    assert hmasd_state._resolve_authority_path(
        repo, "docs/evidence.md", "evidence", require_file=True
    ) == evidence
    with pytest.raises(hmasd_state.ValidationError, match="not an existing regular file"):
        hmasd_state._resolve_authority_path(
            repo, "docs/missing.md", "evidence", require_file=True
        )
    with pytest.raises(hmasd_state.ValidationError, match="alias component"):
        hmasd_state._resolve_authority_path(repo, "docs/../outside.md", "evidence")

    alias = repo / "docs"
    monkeypatch.setattr(
        hmasd_state.hmasd_platform,
        "is_reparse_or_symlink",
        lambda path, *_args: Path(path) == alias,
    )
    with pytest.raises(
        hmasd_state.OwnershipError, match="traverses a symlink or reparse point"
    ):
        hmasd_state._resolve_authority_path(repo, "docs/evidence.md", "evidence")


def test_writer_and_path_ownership_are_enforced(tmp_path: Path) -> None:
    state = fixture("research_state")
    wrong_writer = tmp_path / "wrong-writer.json"
    wrong_writer.write_bytes(json.dumps(dict(state, writer="CM-example-direction")).encode())
    result = run_cli("validate", "--kind", "research_state", "--path", str(wrong_writer))
    assert result.returncode == 5

    wrong_ref = tmp_path / "wrong-ref.json"
    bad = dict(state)
    bad["direction_ref"] = dict(state["direction_ref"], path="docs/research/candidates/other/DIRECTION.md")
    wrong_ref.write_bytes(json.dumps(bad).encode())
    result = run_cli("validate", "--kind", "research_state", "--path", str(wrong_ref))
    assert result.returncode == 5


def test_replace_refuses_cross_writer_and_immutable_record_rewrites(tmp_path: Path) -> None:
    """A CAS replacement may advance facts, never reassign their durable record."""

    def assert_refused(
        label: str,
        kind: str,
        current: dict[str, Any],
        replacement: dict[str, Any],
        writer: str,
        expected_code: int,
    ) -> None:
        target = tmp_path / f"{label}.json"
        initial_path = tmp_path / f"{label}-initial.json"
        replacement_path = tmp_path / f"{label}-replacement.json"
        initial_path.write_text(json.dumps(current, sort_keys=True), encoding="utf-8")
        initialized = run_cli(
            "initialize",
            "--kind",
            kind,
            "--path",
            str(target),
            "--writer",
            current["writer"],
            "--input",
            str(initial_path),
        )
        assert initialized.returncode == 0, initialized.stderr
        before = target.read_bytes()
        replacement_path.write_text(json.dumps(replacement, sort_keys=True), encoding="utf-8")
        result = run_cli(
            "replace",
            "--kind",
            kind,
            "--path",
            str(target),
            "--writer",
            writer,
            "--expected-revision",
            "1",
            "--input",
            str(replacement_path),
        )
        assert result.returncode == expected_code, (label, result.stdout, result.stderr)
        assert target.read_bytes() == before

    direction_current = fixture("research_state")
    direction_replacement = copy.deepcopy(direction_current)
    direction_replacement.update(
        {
            "revision": 2,
            "writer": "EM-other-direction",
            "direction_id": "other-direction",
        }
    )
    direction_replacement["direction_ref"]["path"] = (
        "docs/research/candidates/other-direction/DIRECTION.md"
    )
    assert_refused(
        "direction-takeover",
        "research_state",
        direction_current,
        direction_replacement,
        "EM-other-direction",
        5,
    )

    run_current = fixture("run_manifest")
    run_replacement = copy.deepcopy(run_current)
    run_replacement.update(
        {
            "revision": 2,
            "run_id": "other-run",
            "command": ["python3", "evaluate.py", "--seed", "7"],
        }
    )
    run_replacement["command_sha256"] = hashlib.sha256(
        "\0".join(run_replacement["command"]).encode("utf-8")
    ).hexdigest()
    assert_refused(
        "run-command",
        "run_manifest",
        run_current,
        run_replacement,
        "Operator-example-run",
        6,
    )

    operator_replacement = copy.deepcopy(run_current)
    operator_replacement.update(
        {
            "revision": 2,
            "writer": "Operator-other-run",
            "operator_identity": "Operator-other-run",
        }
    )
    assert_refused(
        "operator-takeover",
        "run_manifest",
        run_current,
        operator_replacement,
        "Operator-other-run",
        5,
    )

    external_current = fixture("external_review_index")
    provider = {
        "operation_id": "operation-a",
        "idempotency_key": "idempotency-a",
        "session_ref": "session-a",
        "terminal_state": "COMPLETED",
        "archive_ref": None,
        "handoff_ref": None,
        "completed_at": "2026-08-24T00:01:00Z",
    }
    external_current["rounds"][0]["providers"]["pro_divergent"] = provider
    external_replacement = copy.deepcopy(external_current)
    external_replacement["revision"] = 2
    external_replacement["rounds"][0]["providers"]["pro_divergent"]["operation_id"] = "operation-b"
    assert_refused(
        "external-operation",
        "external_review_index",
        external_current,
        external_replacement,
        "EM-example-direction",
        6,
    )

    external_round_replacement = copy.deepcopy(external_current)
    external_round_replacement["revision"] = 2
    external_round_replacement["rounds"][0]["question_sha256"] = "e" * 64
    external_round_replacement["rounds"][0]["round_id"] = hashlib.sha256(
        (
            external_round_replacement["direction_id"]
            + "\n"
            + external_round_replacement["rounds"][0]["question_sha256"]
            + "\n"
            + external_round_replacement["rounds"][0]["evidence_set_sha256"]
            + "\n"
            + external_round_replacement["workflow_version"]
        ).encode("utf-8")
    ).hexdigest()[:20]
    assert_refused(
        "external-round",
        "external_review_index",
        external_current,
        external_round_replacement,
        "EM-example-direction",
        6,
    )

    result_current = fixture("accepted_result")
    result_replacement = copy.deepcopy(result_current)
    result_replacement.update(
        {
            "revision": 2,
            "result_id": "other-result",
            "conclusion_path": "docs/research/candidates/example-direction/results/other-result.md",
        }
    )
    assert_refused(
        "result-identity",
        "accepted_result",
        result_current,
        result_replacement,
        "EM-example-direction",
        6,
    )

    terminal_current = copy.deepcopy(run_current)
    terminal_current["status"] = "SUCCEEDED"
    terminal_current["process"].update(
        {
            "execution_token": "token-a",
            "pid": 123,
            "process_group_id": 123,
            "linux_boot_id": "boot-a",
            "proc_start_ticks": 99,
            "started_at": "2026-08-24T00:00:00Z",
            "ended_at": "2026-08-24T00:01:00Z",
            "exit_code": 0,
            "terminal_reason": "CHILD_EXIT_0",
        }
    )
    terminal_replacement = copy.deepcopy(terminal_current)
    terminal_replacement["revision"] = 2
    terminal_replacement["process"]["terminal_reason"] = "REWRITTEN"
    assert_refused(
        "terminal-provenance",
        "run_manifest",
        terminal_current,
        terminal_replacement,
        "Operator-example-run",
        6,
    )

def test_registry_enforces_uniqueness_dependencies_and_active_limit(tmp_path: Path) -> None:
    registry = fixture("portfolio_registry")
    registry["directions"] = registry["directions"] * 9
    for index, direction in enumerate(registry["directions"]):
        direction["id"] = f"direction-{index}"
        direction["abbreviation"] = f"D{index}"
        direction["path"] = f"docs/research/candidates/direction-{index}"
        direction["lifecycle_decision_ref"]["heading"] = f"Direction direction-{index}"
        direction["agent"]["logical_identity"] = f"EM-direction-{index}"
        direction["agent"]["job_name"] = f"EMDirection{index}"
        direction["research_state_path"] = f"docs/research/candidates/direction-{index}/workflow/research/state.json"
        direction["engineering_state_path"] = f"docs/research/candidates/direction-{index}/workflow/engineering/state.json"
        direction["external_review_index_path"] = f"docs/research/candidates/direction-{index}/workflow/external-review/index.json"
        direction["lifecycle"] = "ACTIVE"
        direction["dependencies"] = []
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(path))
    assert result.returncode == 2

    cyclic = fixture("portfolio_registry")
    cyclic["directions"][0]["dependencies"] = ["example-direction"]
    cyclic["directions"].append(dict(cyclic["directions"][0], id="second-direction", dependencies=["example-direction"]))
    cyclic["directions"][0]["dependencies"] = ["second-direction"]
    cyclic_path = tmp_path / "cyclic.json"
    cyclic_path.write_text(json.dumps(cyclic), encoding="utf-8")
    result = run_cli("validate", "--kind", "portfolio_registry", "--path", str(cyclic_path))
    assert result.returncode == 2


def test_foreign_archive_has_native_schema_and_exact_completion_hash(tmp_path: Path) -> None:
    archive = fixture("external_archive")
    assert "schema_version" not in archive
    assert "revision" not in archive
    assert "writer" not in archive
    archive_path = tmp_path / "archive.json"
    archive_path.write_text(json.dumps(archive), encoding="utf-8")
    result = run_cli("validate", "--kind", "external_archive", "--path", str(archive_path))
    assert result.returncode == 0, result.stderr

    archive["responseText"] = "tampered"
    archive_path.write_text(json.dumps(archive), encoding="utf-8")
    result = run_cli("validate", "--kind", "external_archive", "--path", str(archive_path))
    assert result.returncode == 2


def test_initialize_and_replace_are_revision_cas_and_byte_preserving(
    tmp_path: Path,
) -> None:
    source = FIXTURES / "research_state.json"
    target = tmp_path / "state.json"
    result = run_cli(
        "initialize",
        "--kind",
        "research_state",
        "--path",
        str(target),
        "--writer",
        "EM-example-direction",
        "--input",
        str(source),
    )
    assert result.returncode == 0, result.stderr
    original = target.read_bytes()

    replacement = fixture("research_state")
    replacement["revision"] = 2
    replacement["next_action"] = {"kind": "WAIT", "input_refs": []}
    replacement_path = tmp_path / "replacement.json"
    replacement_path.write_text(json.dumps(replacement), encoding="utf-8")
    stale = run_cli(
        "replace",
        "--kind",
        "research_state",
        "--path",
        str(target),
        "--writer",
        "EM-example-direction",
        "--expected-revision",
        "99",
        "--input",
        str(replacement_path),
    )
    assert stale.returncode == 4
    assert target.read_bytes() == original



def test_state_cli_exposes_only_current_v3_operations() -> None:
    from scripts import hmasd_state

    parser = hmasd_state._parser()
    subparsers = next(
        action
        for action in parser._actions
        if action.__class__.__name__ == "_SubParsersAction"
    )

    assert set(subparsers.choices) == {
        "validate",
        "initialize",
        "replace",
        "portfolio-apply",
    }


def test_concurrent_initialize_has_one_winner_and_losers_preserve_bytes(tmp_path: Path) -> None:
    source = FIXTURES / "research_state.json"
    target = tmp_path / "concurrent.json"

    def initialize() -> int:
        return run_cli(
            "initialize",
            "--kind",
            "research_state",
            "--path",
            str(target),
            "--writer",
            "EM-example-direction",
            "--input",
            str(source),
        ).returncode

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: initialize(), range(2)))
    assert sorted(outcomes) == [0, 4]
    assert target.read_bytes() == source.read_bytes()


def test_ignore_query_exposes_tracked_contracts_and_keeps_runtime_ignored() -> None:
    tracked = (
        "AGENTS.md",
        "CONTEXT.md",
        ".agents/skills/hmasd-root-control/SKILL.md",
        "docs/research/portfolio/PORTFOLIO.md",
        "docs/research/portfolio/workflow/registry.json",
        "docs/external-review/directions/example/round/GEMINI_DIVERGENT_PROMPT.md",
    )
    ignored = (
        "temp/directions/example/manifest.json",
    )
    for path in tracked:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, (path, result.stdout, result.stderr)
    for path in ignored:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (path, result.stdout, result.stderr)
