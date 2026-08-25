"""Phase 0 RED tests for HMASD durable state contracts.

These tests intentionally describe the contract before the implementation exists.
They are kept narrow so later phases can reuse the fixtures without importing
workflow behavior.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any



ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_state.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hmasd_phase0"
KINDS = (
    "portfolio_registry",
    "research_state",
    "engineering_state",
    "external_review_index",
    "run_manifest",
    "accepted_result",
    "external_archive",
    "agent_result",
    "runtime_agents",
    "runtime_worktrees",
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


def test_all_ten_schema_contracts_are_present_and_strict() -> None:
    schema_dir = ROOT / "scripts" / "schemas"
    for kind in KINDS:
        schema = json.loads(
            (schema_dir / f"hmasd_{kind}.schema.json").read_text(encoding="utf-8")
        )
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"]


def test_valid_phase0_fixtures_validate() -> None:
    for kind in KINDS:
        path = FIXTURES / f"{kind}.json"
        result = run_cli("validate", "--kind", kind, "--path", str(path))
        assert result.returncode == 0, (kind, result.stderr)

def test_portfolio_payload_is_root_owned_after_manager_merge(tmp_path: Path) -> None:
    document = fixture("agent_result")
    document.update(
        {
            "assignment_id": "root-portfolio-wake",
            "logical_identity": "Root",
            "materiality": "PORTFOLIO",
            "payload": {
                "kind": "portfolio",
                "direction_actions": [],
                "portfolio_ref": {
                    "path": "docs/research/portfolio/PORTFOLIO.md",
                    "sha256": "a" * 64,
                },
                "registry_revision": 1,
            },
            "role": "root",
            "summary": "Root reconciled portfolio lifecycle.",
        }
    )
    path = tmp_path / "root-portfolio.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 0, result.stderr

    document["role"] = "hmasd-portfolio"
    document["logical_identity"] = "Portfolio"
    path.write_text(json.dumps(document), encoding="utf-8")
    result = run_cli("validate", "--kind", "agent_result", "--path", str(path))
    assert result.returncode == 2


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

    worktree_current = fixture("runtime_worktrees")
    worktree_replacement = copy.deepcopy(worktree_current)
    worktree_replacement["revision"] = 2
    worktree_replacement["worktrees"][0]["canonical_absolute_path"] = "/tmp/other-worktree"
    assert_refused(
        "worktree-target",
        "runtime_worktrees",
        worktree_current,
        worktree_replacement,
        "Root",
        6,
    )

    worktree_ref_replacement = copy.deepcopy(worktree_current)
    worktree_ref_replacement["revision"] = 2
    worktree_ref_replacement["worktrees"][0]["worktree_ref"] = "wt-other"
    assert_refused(
        "worktree-ref",
        "runtime_worktrees",
        worktree_current,
        worktree_ref_replacement,
        "Root",
        6,
    )

    runtime_agents_current = fixture("runtime_agents")
    runtime_agents_replacement = copy.deepcopy(runtime_agents_current)
    runtime_agents_replacement["revision"] = 2
    runtime_agents_replacement["agents"][0]["runtime_ref"] = "runtime-other-em"
    assert_refused(
        "runtime-agent-ref",
        "runtime_agents",
        runtime_agents_current,
        runtime_agents_replacement,
        "Root",
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


def test_initialize_replace_and_migrate_are_revision_cas_and_byte_preserving(
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

    unsupported = fixture("research_state")
    unsupported["schema_version"] = 2
    unsupported_path = tmp_path / "unsupported.json"
    unsupported_path.write_text(json.dumps(unsupported), encoding="utf-8")
    migrate = run_cli(
        "migrate",
        "--kind",
        "research_state",
        "--path",
        str(unsupported_path),
        "--writer",
        "EM-example-direction",
        "--expected-revision",
        "1",
        "--to-version",
        "3",
    )
    assert migrate.returncode == 3
    assert unsupported_path.read_text(encoding="utf-8") == unsupported_path.read_text(encoding="utf-8")


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
        ".omp/WATCHDOG.md",
        ".omp/RULES.md",
        ".omp/skills/hmasd-root-control/SKILL.md",
        "docs/research/portfolio/PORTFOLIO.md",
        "docs/research/portfolio/workflow/registry.json",
        "docs/external-review/directions/example/round/GEMINI_DIVERGENT_PROMPT.md",
    )
    ignored = (".omp/runtime/agents.json", "temp/directions/example/manifest.json")
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
