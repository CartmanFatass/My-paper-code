"""Static contract pressure for the layered OMP Git writer handoff."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GIT_SKILL = ROOT / ".omp" / "skills" / "hmasd-git-integration" / "SKILL.md"


def _skill_text() -> str:
    assert GIT_SKILL.is_file(), f"missing Git integration Skill: {GIT_SKILL}"
    return " ".join(GIT_SKILL.read_text(encoding="utf-8").lower().split())


def test_omp_workflow_is_the_only_final_transfer_target_with_exact_ownership() -> None:
    skill = _skill_text()
    required = (
        "`omp/workflow` is the transfer spine and the final target",
        "any final target other than `omp/workflow`",
        "exact assignment-owned path allowlist",
        "every changed path is assignment-owned",
        "actor, direction, and kind to match exactly",
        "`em:<direction>` may integrate a research worktree",
        "`cm:<direction>` may integrate an engineering worktree",
        "stage only paths in the canonical exact allowlist",
        "never use `git add -a`",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits OMP target or ownership contracts: {missing}"


def test_integrated_sha_transfers_the_single_direction_writer_phase_in_order() -> None:
    skill = _skill_text()
    ordered = (
        "em commits its exact allowlist and ends its overlapping git-visible writer phase",
        "accepted `integrated_sha` is the exact cm base",
        "cm begins only from that integrated sha",
        "cm `integrated_sha` is then the exact base that em must observe",
        "resuming its writer phase",
    )
    positions = [skill.find(term) for term in ordered]
    assert all(position >= 0 for position in positions), {
        term: position for term, position in zip(ordered, positions, strict=True)
    }
    assert positions == sorted(positions)
    assert "only one em or cm git-visible writer phase may own overlapping paths at a time" in skill
    assert "overlapping writer phases" in skill


def test_fetch_compare_push_is_bounded_and_fails_closed_without_blind_retry() -> None:
    skill = _skill_text()
    required = (
        "fetch the intended remote immediately before push",
        "compare its observed tip with the candidate's required predecessor",
        "push only the verified integration to `omp/workflow`",
        "one candidate/apply/push attempt to `omp/workflow`",
        "no automatic retry",
        "fetch and compare the exact remote ref",
        "never retry blindly",
        "leave `omp/workflow` unchanged on pre-apply refusal",
        "stale bases",
        "non-handoff bases",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits fetch/compare/push safeguards: {missing}"
