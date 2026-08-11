"""Proof-sized contracts for the repaired CPM child-context boundaries."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def compact(value: str) -> str:
    """Normalize prose wrapping while retaining punctuation/ordering."""
    return " ".join(value.split())


class SpecializedChildContextTest(unittest.TestCase):
    def test_mechanical_brief_and_conclusion_are_not_json_acceptance(self) -> None:
        role = compact(read(".agents/roles/CPM_MECHANICAL_OPERATOR.md"))
        profile = compact(read(".codex/agents/hmasd-cpm-mechanical.toml"))
        for term in (
            "natural-language mechanical brief",
            "semantic task authority",
            "CPM consumers",
            "protected",
            "at most one",
            "read-only observation recovery",
            "automatic repair or retry",
            "natural-language mechanical conclusion",
            "direct consequence",
            "residual uncertainty",
            "JSON result and status fields follow",
            "`COMPLETE` means",
            "never means CPM accepted",
        ):
            self.assertIn(term, role)
        self.assertIn("natural-language brief", profile)
        self.assertIn("deterministic execution anchor", profile)
        self.assertIn("use direct Git commands or mutate Git", profile)
        self.assertIn("contracted dispatcher observations", profile)
        self.assertNotIn("readiness/Agentify, use Git, decide acceptance", profile)
        self.assertNotIn("schema_version=1", profile)
        self.assertNotIn("hmasd_cpm_mechanical.py run --spec", profile)

    def test_experiment_and_verifier_keep_recovery_and_acceptance_boundaries(self) -> None:
        experiment = compact(read(".agents/roles/EXPERIMENT_OPERATOR.md"))
        experiment_profile = compact(read(".codex/agents/hmasd-experiment-operator.toml"))
        for term in (
            "natural-language assignment brief",
            "artifact consumers",
            "protected",
            "conflicting runtime evidence",
            "train -> evaluate -> analyze",
            "one assignment-defined",
            "read-only identity/run-root observation recovery",
            "never changes a command",
            "concise operational",
            "direct artifact or consumer consequence",
            "residual uncertainty",
            "not result acceptance",
        ):
            self.assertIn(term, experiment)
        self.assertIn("natural-language brief", experiment_profile)
        self.assertNotIn("Execute train", experiment_profile)
        self.assertNotIn("Do not emit commentary", experiment_profile)

        verifier = compact(read(".agents/roles/VERIFIER.md"))
        verifier_profile = compact(read(".codex/agents/hmasd-verifier.toml"))
        for term in (
            "natural-language assignment is the source",
            "readiness exercise matters to its consumers",
            "protected candidate/readiness semantics",
            "at most one",
            "bounded, read-only observation recovery",
            "six-phase execution-readiness spec",
            "conclusion-first",
            "never accept code",
        ):
            self.assertIn(term, verifier)
        self.assertIn("natural-language brief", verifier_profile)
        self.assertNotIn("run --spec", verifier_profile)
        self.assertNotIn("finalize --spec", verifier_profile)

    def test_agentify_requires_real_model_switch_and_answer_evidence(self) -> None:
        role = compact(read(".agents/roles/CPM_AGENTIFY_TRANSPORT_OPERATOR.md"))
        skill = compact(read(".agents/skills/hmasd-agentify-transport/SKILL.md"))
        profile = compact(
            read(".codex/agents/hmasd-cpm-agentify-transport.toml")
        )

        for term in (
            "role=cpm_agentify_transport_operator",
            "callable_agent_type=hmasd-cpm-agentify-transport",
            "parent=code_project_manager",
            "requester_partition_root=temp/sessions/agentify_transport_operator/code_project_manager/<assignment>/",
            "acceptance_authority=none",
            "technical_acceptance_authority=none",
            "cross_branch_transport=none",
            "returns one conclusion-first result to CPM",
            "Do not contact Root",
            "route across owners",
        ):
            self.assertIn(term, role)

        for term in (
            "AGENTIFY_REVIEW_BATCH_ASSIGNMENT",
            "batch_path=",
            "results_path=",
            "context_path",
            "context brief",
            "owning requester",
            "permitted action",
            "frozen/protected meaning",
            "bounded non-duplicating recovery",
            "completion evidence",
            "current composer model",
            "open the model picker",
            "select Pro",
            "composer visibly",
            "expectedModel=Pro",
            "recognition metadata alone",
            "tool `COMPLETE` token",
            "provider-home URL",
            "full nonempty",
            "concrete",
            "natural-language conclusion",
        ):
            self.assertIn(term, skill)

        self.assertIn("hmasd-cpm-agentify-transport", profile)
        self.assertIn("parent-specific Role", profile)
        self.assertIn("no routing or acceptance authority", profile)
        self.assertIn("Root", profile)

        # The dependent send is ordered after the visible post-switch check.
        self.assertIn("shows Pro after that action", skill)
        self.assertIn("response fragment", skill)
        switch = skill.index("Inspect the current composer model")
        send = skill.index("Call `agentify_query`")
        visible_pro = skill.index("shows Pro after that action")
        self.assertLess(switch, send)
        self.assertLess(visible_pro, send)
        self.assertIn("conclusion-first transport evidence", profile)
        self.assertNotIn("Use page, conversation and natural-language judgment", profile)

    def test_requester_descriptions_bind_batch_and_result_contract(self) -> None:
        cpm = compact(read(".agents/roles/CODE_PROJECT_MANAGER.md"))
        agile = compact(read(".agents/skills/hmasd-agile-research-development/SKILL.md"))
        self.assertIn("agentify_transport_child=hmasd-cpm-agentify-transport", cpm)
        self.assertIn(
            "agentify_transport_assignment=AGENTIFY_REVIEW_BATCH_ASSIGNMENT",
            cpm,
        )
        self.assertIn("agentify_transport_assignment_fields=batch_path|results_path", cpm)
        self.assertIn("agentify_transport_result=AGENTIFY_REVIEW_BATCH_RESULT", cpm)
        self.assertIn("agentify_transport_result_fields=status|results_path|error", cpm)
        self.assertIn("AGENTIFY_REVIEW_BATCH_ASSIGNMENT", agile)
        self.assertIn("hmasd-cpm-agentify-transport", agile)

    def test_specialized_profiles_declare_background_fork_context(self) -> None:
        profiles = (
            ".codex/agents/hmasd-cpm-mechanical.toml",
            ".codex/agents/hmasd-experiment-operator.toml",
            ".codex/agents/hmasd-verifier.toml",
            ".codex/agents/hmasd-cpm-agentify-transport.toml",
        )
        for relative in profiles:
            self.assertIn(
                "fork_turns=none; forked context is background only.",
                compact(read(relative)),
            )

        mechanical = compact(read(".codex/agents/hmasd-cpm-mechanical.toml"))
        self.assertIn("execution scope is one", mechanical)
        self.assertIn("semantic task authority", mechanical)
        self.assertIn("deterministic I/O anchors only", mechanical)

    def test_multi_cpm_scope_and_no_runtime_pool_contract(self) -> None:
        """Pin the active multi-CPM boundary without exercising runtime code."""
        agents = compact(read("AGENTS.md"))
        cpm = compact(read(".agents/roles/CODE_PROJECT_MANAGER.md"))
        agile = compact(read(".agents/skills/hmasd-agile-research-development/SKILL.md"))

        active = " ".join((agents, cpm, agile))
        for term in (
            "multiple_scoped_instances_per_root_tree=true",
            "cpm_instance_identity=code_scope_key",
            "root_scope_dispatch=fork_turns=1|self_contained_assignment",
            "scoped_cpm_l2_fanout=registered_l2_within_depth_2",
            "scope_technical_acceptance=code_project_manager",
            "convergence_cpm=fresh_root_dispatch_after_scope_integration",
            "convergence_assignment=self_contained_union",
            "convergence_acceptance=overall_technical_and_runtime",
            "root_lifecycle_git_relay=exclusive",
            "tracked_writer_worktree=one_root_managed_worktree_per_writable_l1_assignment",
            "parallel_l2_writers_same_base_disjoint_paths=share_l1_worktree",
            "parallel_cpm_assignments_worktrees=independent",
            "integration_worktree=separate_root_managed_worktree",
            "worktree_l2_lifecycle=forbidden",
            "technical_acceptance_authority=exclusive",
            "runtime_authority=scope_local_technical_runtime_judgment",
            "runtime_unit_accounting=none",
            "runtime_pool=none",
            "runtime_class_quota=none",
            "runtime_reservation=none",
            "runtime_admission_ledger=none",
            "runtime_observation_owner=root_mechanical",
            "runtime_observation_facts=live_processes|cpu|memory|concrete_resource_conflicts",
            "runtime_judgment_owner=code_project_manager_scope_local",
            "high_cost_runtime_authorization=explicit_user_task_via_root",
            "max_threads=20",
            "max_threads_semantics=agent_concurrency_ceiling_only",
            "max_threads_runtime_authorization=none",
            "parallelism_runtime_authorization=none",
        ):
            self.assertIn(term, active)

        for retired in (
            "runtime_capacity_pool_units=3",
            "three-unit runtime pool",
            "runtime_admission_observation=stateless_per_admission",
            "runtime_admission_judgment=admit|up-class|pending_runtime_capacity",
            "reserved and free units",
            "requested/free units",
            "runtime admission ledger",
        ):
            self.assertNotIn(retired, active)


if __name__ == "__main__":
    unittest.main()
