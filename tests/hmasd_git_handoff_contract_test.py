from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GIT_SKILL = ROOT / ".omp" / "skills" / "hmasd-git-integration" / "SKILL.md"
CLERK_SKILL = ROOT / ".omp" / "skills" / "hmasd-clerk" / "SKILL.md"
CLERK_SCRIPT = ROOT / "scripts" / "hmasd_clerk.py"


def compact(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


def test_stable_clerk_integration_contract_is_one_bounded_job() -> None:
    skill = compact(GIT_SKILL)
    for requirement in (
        "stable logical `clerk`",
        "one concise frozen integration job",
        "one git-visible writer owns the target during the job",
        "there is no json input, build step, persisted integration graph",
        "one non-merge commit whose sole parent is the source base",
        "exact changed-path set to equal the nonempty allowlist",
        "temporary detached worktree",
        "refuse any apply conflict or post-apply path drift",
        "fetch the configured remote target immediately before push",
        "push the one frozen integration commit exactly once",
        "one read-only fetch and comparison",
        "observation grants no retry authority",
    ):
        assert requirement in skill


def test_integrate_candidate_exposes_only_ordinary_flags() -> None:
    source = CLERK_SCRIPT.read_text(encoding="utf-8")
    assert 'OPERATION = "integrate-candidate"' in source
    for flag in (
        "--job-id",
        "--repo",
        "--source-base",
        "--candidate",
        "--target-branch",
        "--expected-predecessor",
        "--actor",
        "--commit-message",
        "--allowed-path",
    ):
        assert f'add_argument("{flag}"' in source
    for obsolete in (
        'add_parser("build")',
        'add_parser("execute")',
        'add_argument("--draft"',
        'add_argument("--packet"',
        "packet_sha256",
        "ClerkOperationPacket",
    ):
        assert obsolete not in source


def test_push_is_single_attempt_with_observe_only_ambiguity() -> None:
    source = CLERK_SCRIPT.read_text(encoding="utf-8")
    assert '"--force-with-lease=' in source
    assert '"push"' in source
    assert '"push-attempt"' in source
    assert '"attempts": 1' in source
    assert '"push-observation"' in source
    assert "_observe_ambiguous_push" in source
    assert "while" not in source[source.index("push_args ="):]


def test_obsolete_integration_schema_and_json_draft_are_absent() -> None:
    assert not (ROOT / "scripts/schemas/hmasd_clerk_operation.schema.json").exists()
    clerk = compact(CLERK_SKILL)
    assert "there is no json input or build step" in clerk
    assert "writes no protocol artifact" in clerk


def test_external_commitment_boundary_remains_unchanged() -> None:
    skill = compact(GIT_SKILL)
    assert "agentify remains the sole external submission ledger" in skill
    assert "unknown-never-resend semantics are unchanged" in skill
    assert "external ambiguous outcome remains observe-only" in skill
