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
        self.assertIn("contracted read-only Git observations", profile)
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
        role = compact(read(".agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md"))
        skill = compact(read(".agents/skills/hmasd-agentify-transport/SKILL.md"))
        profile = compact(read(".codex/agents/hmasd-agentify-transport.toml"))
        for surface in (role, skill):
            for term in (
                "context_path",
                "context brief",
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
                self.assertIn(term, surface)

        # The dependent send is ordered after the visible post-switch check.
        self.assertIn("shows Pro after the action", role)
        self.assertIn("shows Pro after that action", skill)
        self.assertIn("partial response fragment", role)
        self.assertIn("response fragment", skill)
        switch = skill.index("Inspect the current composer model")
        send = skill.index("Call `agentify_query`")
        visible_pro = skill.index("shows Pro after that action")
        self.assertLess(switch, send)
        self.assertLess(visible_pro, send)
        self.assertIn("natural-language", profile)
        self.assertNotIn("Use page, conversation and natural-language judgment", profile)

    def test_requester_descriptions_bind_context_path(self) -> None:
        cpm = read(".agents/roles/CODE_PROJECT_MANAGER.md")
        agile = read(".agents/skills/hmasd-agile-research-development/SKILL.md")
        for surface in (cpm, agile):
            self.assertIn("provider|context_path|question_paths", surface)
            self.assertIn("AGENTIFY_REVIEW_BATCH_ASSIGNMENT", surface)

    def test_specialized_profiles_declare_background_fork_context(self) -> None:
        profiles = (
            ".codex/agents/hmasd-cpm-mechanical.toml",
            ".codex/agents/hmasd-experiment-operator.toml",
            ".codex/agents/hmasd-verifier.toml",
            ".codex/agents/hmasd-agentify-transport.toml",
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


if __name__ == "__main__":
    unittest.main()
