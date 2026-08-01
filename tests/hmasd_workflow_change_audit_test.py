from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
CHECKER_PATH = (
    REPO
    / ".agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py"
)
SPEC = importlib.util.spec_from_file_location("check_hmasd_agent_harness", CHECKER_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture_repo(root: Path) -> Path:
    _write(
        root / ".codex/config.toml",
        '[agents]\nmax_threads = 1\n\n[agents."Worker"]\n'
        'config_file = "./agents/worker.toml"\n',
    )
    _write(
        root / ".codex/agents/worker.toml",
        'name = "worker"\n'
        'model = "gpt-test"\n'
        'model_reasoning_effort = "low"\n'
        'sandbox_mode = "read-only"\n'
        'approval_policy = "never"\n'
        'developer_instructions = "Read .agents/roles/WORKER.md."\n',
    )
    _write(
        root / ".agents/roles/WORKER.md",
        "```text\nrole=worker\ncallable_agent_type=worker\n```\n",
    )
    _write(
        root / ".agents/skills/demo/SKILL.md",
        "---\nname: demo\n---\n# Demo\n",
    )
    _write(
        root / "AGENTS.md",
        "Use `.agents/roles/WORKER.md` and `.agents/skills/demo/SKILL.md`.\n"
        "superpowers_execution=disabled\nworkflow_hash_validation=disabled\n",
    )
    return root


def _write_control_plane_budget_files(root: Path, first_file_lines: int) -> None:
    for index, relative in enumerate(CHECKER.CONTROL_PLANE_BUDGET_PATHS):
        line_count = first_file_lines if index == 0 else 1
        _write(root / relative, "x\n" * line_count)


def test_control_plane_line_budget_accepts_exact_limit(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    _write_control_plane_budget_files(repo, CHECKER.CONTROL_PLANE_LINE_BUDGET - 5)
    errors = CHECKER.audit_repo(repo)
    assert not any("control-plane line budget exceeded" in error for error in errors), errors


def test_control_plane_line_budget_rejects_one_line_over(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    _write_control_plane_budget_files(repo, CHECKER.CONTROL_PLANE_LINE_BUDGET - 4)
    errors = CHECKER.audit_repo(repo)
    assert any("control-plane line budget exceeded: 1001>1000" in error for error in errors), errors


def _add_benchmark_group(root: Path, *, drift: bool) -> None:
    with (root / ".codex/config.toml").open("a", encoding="utf-8") as handle:
        for variant in ("a", "b", "c"):
            handle.write(
                f'\n[agents."Benchmark{variant.upper()}"]\n'
                f'config_file = "./agents/hmasd-benchmark-implementer-{variant}.toml"\n'
            )
    _write(
        root / ".agents/roles/BENCHMARK_IMPLEMENTER.md",
        "```text\nrole=benchmark_implementer\n"
        "callable_agent_type=hmasd-benchmark-implementer\n```\n",
    )
    with (root / "AGENTS.md").open("a", encoding="utf-8") as handle:
        handle.write("Use `.agents/roles/BENCHMARK_IMPLEMENTER.md`.\n")
    for index, variant in enumerate(("a", "b", "c")):
        instructions = "Frozen benchmark task. Read .agents/roles/BENCHMARK_IMPLEMENTER.md."
        if drift and index == 2:
            instructions += " Extra behavior."
        _write(
            root / f".codex/agents/hmasd-benchmark-implementer-{variant}.toml",
            f'name = "hmasd-benchmark-implementer-{variant}"\n'
            f'description = "Variant {variant}"\n'
            f'model = "model-{variant}"\n'
            f'model_reasoning_effort = "{variant}"\n'
            'sandbox_mode = "workspace-write"\n'
            'approval_policy = "never"\n'
            f'nickname_candidates = ["Variant {variant}"]\n'
            f'developer_instructions = """{instructions}"""\n',
        )


def test_live_repository_harness_is_closed() -> None:
    assert CHECKER.audit_repo(REPO) == []


def test_default_scan_stays_inside_workflow_design_surfaces() -> None:
    assert "docs/project/CURRENT_WORK.md" not in CHECKER.DEFAULT_ACTIVE_PATHS
    assert "docs/project/AGENT_CONTEXT.md" not in CHECKER.DEFAULT_ACTIVE_PATHS


@pytest.mark.parametrize("breakage, expected", [
    ("missing_role", "references missing role"),
    ("orphan_profile", "unregistered profile"),
    ("orphan_role", "unrouted role charter"),
    ("forbidden_marker", "forbidden active marker"),
    ("broken_script", "broken active path reference"),
    ("benchmark_drift", "developer_instructions differ byte-for-byte"),
])
def test_checker_fails_closed_on_cross_surface_omissions(
    tmp_path: Path, breakage: str, expected: str
) -> None:
    repo = _fixture_repo(tmp_path)
    if breakage == "missing_role":
        (repo / ".agents/roles/WORKER.md").unlink()
    elif breakage == "orphan_profile":
        _write(repo / ".codex/agents/orphan.toml", 'name = "orphan"\n')
    elif breakage == "orphan_role":
        _write(repo / ".agents/roles/ORPHAN.md", "```text\nrole=orphan\n```\n")
    elif breakage == "forbidden_marker":
        with (repo / "AGENTS.md").open("a", encoding="utf-8") as handle:
            handle.write("superpowers_execution=enabled\n")
    elif breakage == "broken_script":
        with (repo / "AGENTS.md").open("a", encoding="utf-8") as handle:
            handle.write("Use `scripts/missing_harness.py`.\n")
    else:
        _add_benchmark_group(repo, drift=True)

    errors = CHECKER.audit_repo(repo)
    assert any(expected in error for error in errors), errors
