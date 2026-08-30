"""Static contract pressure for the layered OMP Git writer handoff."""

from __future__ import annotations
import json

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GIT_SKILL = ROOT / ".omp" / "skills" / "hmasd-git-integration" / "SKILL.md"
CLERK_SCHEMA = ROOT / "scripts" / "schemas" / "hmasd_clerk_operation.schema.json"
WORKTREE_SCRIPT = ROOT / "scripts" / "hmasd_worktree.py"


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
        "one candidate/push attempt to `omp/workflow`",
        "no automatic retry",
        "compare the exact remote ref once",
        "leave `omp/workflow` unchanged on pre-effect refusal",
        "stale or non-handoff bases refuse",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits fetch/compare/push safeguards: {missing}"


def test_current_policies_and_same_direction_exact_handoffs_are_explicit() -> None:
    skill = _skill_text()
    required = (
        "exactly two explicit current provision-time policies",
        "`exact_handoff` preserves direct-child",
        "`orthogonal_direction`",
        "missing or any other policy is invalid",
        "same-direction em→cm and cm→em always use this policy",
        "accepted `integrated_sha` is the exact cm base",
        "cm begins only from that integrated sha",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits current policies or exact handoff: {missing}"


def test_repository_global_target_mutex_has_one_lock_order() -> None:
    skill = _skill_text()
    required = (
        "canonical git common directory plus `refs/heads/omp/workflow`",
        "independent of worktree container locks",
        "target lock → worktree lock → state cas",
        "unrelated safe worktree/state operations do not acquire it",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits target mutex contract: {missing}"


def test_orthogonal_policy_requires_lineage_dependency_and_structural_delta_proofs() -> None:
    skill = _skill_text()
    required = (
        "every first-parent commit in `b..t`",
        "another authorized sibling",
        "same-direction, shared, recovery, unreceipted",
        "renames disabled",
        "length-prefixed record binds path, old mode",
        "authority/input/interface dependency footprint",
        "construct prospective merge tree `m` without moving a ref",
        "canonical_delta(t,i)==canonical_delta(b,c)",
        "sole parent `t`",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits orthogonal proof obligations: {missing}"


def test_phase_receipts_allow_one_observation_but_no_second_effect() -> None:
    skill = _skill_text()
    required = (
        "`integration_object_created`",
        "`push_attempted`",
        "`remote_push_unknown`",
        "`reconciled_not_committed`",
        "`local_apply_unknown`",
        "exactly one fetch and compare",
        "does not authorize resend",
        "never regenerate or re-push `i`",
        "duplicate terminal operation identity returns the existing receipt",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits idempotent phase semantics: {missing}"


def test_public_patch_candidate_and_remote_first_surfaces_are_exact() -> None:
    skill = _skill_text()
    required = (
        "apply-patch",
        "temporary index",
        "immutable prepared-tree receipt",
        "manager worktree bytes, index, branch, and head are never changed",
        "create-candidate",
        "exact prior prepared-tree receipt",
        "hmasd.candidate-metadata/v1",
        "dedicated immutable candidate ref",
        "one deterministic single-parent candidate",
        "integrate-push",
        "creates no alternate object",
        "exact force-with-lease",
        "there is no local-only `apply` command",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits exact public mechanical surfaces: {missing}"


def test_git_skill_is_policy_not_an_obsolete_result_producer() -> None:
    skill = _skill_text()
    assert "not an active result producer" in skill
    assert "sole common-v2 mechanical result" in skill
    assert "no obsolete common git payload is returned" in skill


def test_remote_first_phase_journal_distinguishes_unknown_without_fallback() -> None:
    skill = _skill_text()
    required = (
        "push_attempted",
        "remote_push_committed",
        "remote_push_rejected",
        "remote_push_unknown",
        "reconciled_committed",
        "reconciled_not_committed",
        "reconciled_conflicted",
        "local_apply_attempted",
        "local_apply_committed",
        "local_apply_unknown",
        "one fetch reconciliation",
        "never a second push",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"Git Skill omits exact remote phase semantics: {missing}"


def test_packet_schema_is_current_only_and_exposes_complete_resources() -> None:
    schema = json.loads(CLERK_SCHEMA.read_text(encoding="utf-8"))
    definitions = schema["$defs"]
    assert definitions["git_policy"]["enum"] == [
        "EXACT_HANDOFF",
        "ORTHOGONAL_DIRECTION",
    ]
    assert set(definitions["state_cas_target"]["properties"]["state_kind"]["enum"]).isdisjoint(
        {"runtime_worktrees", "runtime_browser_assignments", "external_review_index"}
    )
    for name in (
        "read_only_mutation",
        "state_path_mutation",
        "worktree_content_mutation",
        "worktree_registry_mutation",
        "git_target_mutation",
    ):
        assert definitions[name]["required"] == ["class", "resources"]
        assert "lock_key" not in definitions[name]["properties"]
    assert (
        definitions["candidate_create_target"]["properties"][
            "prepared_tree_receipt_binding"
        ]["properties"]["output_field"]["const"]
        == "prepared_tree_receipt_ref"
    )


def test_no_owned_git_or_clerk_surface_retains_legacy_policy_or_apply_command() -> None:
    worktree_text = WORKTREE_SCRIPT.read_text(encoding="utf-8")
    schema_text = CLERK_SCHEMA.read_text(encoding="utf-8")
    assert "OBSOLETE_EXACT_POLICY" not in worktree_text
    assert "OBSOLETE_EXACT_POLICY" not in schema_text
    assert 'sub.add_parser("apply")' not in worktree_text
