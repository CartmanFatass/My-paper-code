from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / ".omp" / "skills" / "hmasd-em-direction-cycle" / "SKILL.md"
EXTERNAL_REVIEW_SKILL = (
    REPO_ROOT / ".omp" / "skills" / "hmasd-scientific-external-review" / "SKILL.md"
)
CYCLE_BOUNDARIES = (
    "FRESH_MATERIAL_CYCLE",
    "CONTINUATION",
    "CM_RESULT_INTERPRETATION",
    "EVIDENCE_INTAKE",
    "TERMINAL_GAP_DISPOSITION",
)


def _skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _external_review() -> str:
    return EXTERNAL_REVIEW_SKILL.read_text(encoding="utf-8")


def _compact(text: str) -> str:
    return " ".join(text.lower().split())


def test_cycle_boundary_inventory_preserves_the_frozen_scientific_object() -> None:
    text = _skill()
    compact = _compact(text)

    assert tuple(re.findall(r"^- `([A-Z_]+)`$", text, re.MULTILINE)) == CYCLE_BOUNDARIES
    for trigger in (
        "new scientific object",
        "mechanism",
        "comparator",
        "discriminator",
        "possible claim increase",
        "overturning a core frozen assumption",
        "explicit portfolio reevaluation",
    ):
        assert trigger in compact
    for preserved_boundary in (
        "a changed object ends the current cycle",
        "continuation reopen neither pro stage",
        "never relabel work to obtain another external operation",
    ):
        assert preserved_boundary in compact


def test_fresh_cycle_freezes_the_complete_scientific_object() -> None:
    compact = _compact(_skill())

    for requirement in (
        "question, decision relevance and non-goals",
        "object; estimand, treatment/comparator",
        "observational unit and exposure clock",
        "finite claim ceiling",
        "strongest simple null and competing explanations",
        "distinct predictions",
        "smallest discriminator and every outcome branch",
        "baseline commit, configuration, data/provenance and rng/seed identity",
        "protected numerical, checkpoint, bit-identity and external-effect semantics",
        "observation/resource bound, early stop, invalidation condition, owned paths",
        "exact evidence refs",
        "a non-fresh boundary reuses this freeze without silently changing it",
    ):
        assert requirement in compact


def test_local_routes_are_information_gap_driven_neutral_and_negative_complete() -> None:
    compact = _compact(_skill())

    for requirement in (
        "distinct named information gaps determine whether any leaf is needed, its task family, and the specialist mix",
        "counts, quotas, votes, and quorum never do",
        "zero qualifying gaps dispatches zero leaves",
        "choose the task family that matches the product needed, not a persona",
        "theorem/proof derivation",
        "concept/principles validation",
        "counterexample/adversarial search",
        "source/evidence retrieval",
        "different-family innovation",
        "same neutral freeze and keep each blind to favored routes, em conclusions, and sibling outputs",
        "substantive product or `no_material_insight`",
        "synthesize mechanisms and discriminators, never response counts",
        "agreement is coverage rather than independent evidence",
        "`no_material_insight` is a successful negative-complete analytical product",
        "technical execution status therefore remain independently queryable",
    ):
        assert requirement in compact


def test_pro_innovator_and_convergence_are_exactly_ordered() -> None:
    em = _compact(_skill())
    review = _compact(_external_review())

    assert (
        "exactly one pro innovator from the neutral freeze before or alongside "
        "local work and exactly one pro convergence after local synthesis"
    ) in em
    assert em.index("exactly one pro innovator") < em.index(
        "exactly one pro convergence"
    )
    assert (
        "innovator remains blind to em conclusions, favored answers, and local results"
    ) in em
    for requirement in (
        "no convergence prompt may be authored or requested before its durable ref exists",
        "innovator output cannot substitute for synthesis",
        "one fresh cycle has only these two pro operations",
        "unless exactly waived",
    ):
        assert requirement in review


def test_browser_transport_is_root_mediated_and_scientifically_non_authoritative() -> None:
    em = _compact(_skill())
    review = _compact(_external_review())

    for requirement in (
        "em returns frozen requests through root",
        "never sends, performs browser mechanics, contacts, or spawns browsertransport",
    ):
        assert requirement in em
    for requirement in (
        "singleton root-mediated `browsertransport`",
        "`next_action.owner=transport`",
        "provider: chatgpt",
        "exact pro model",
        "only the strict agentify review surface may send",
        "browsertransport owns only transport facts",
        "provider completion is not accepted science",
        "unknown commitment is terminal for sending",
        "never resend",
    ):
        assert requirement in review


def test_engineering_request_is_durable_meaning_complete_and_root_routed() -> None:
    compact = _compact(_skill())

    for requirement in (
        "when executable evidence is the smallest remaining discriminator",
        "docs/research/candidates/<direction-id>/workflow/research/engineering-request.md",
        "scientific question and decision relevance",
        "competing predictions",
        "discriminator and observable acceptance",
        "protected scientific, numerical, rng, checkpoint, bit-identity, and external-effect semantics",
        "exact baseline, configuration, data/provenance, seed policy, and owned paths",
        "resource/effect bounds and stop rule",
        "run plan without launching it",
        "positive, negative, null, ambiguous, invalid, and technical-failure branches",
        "hash the request",
        "expected-revision cas",
        "`engineering_request_ref` and `next_action.input_refs`",
        "`next_action.owner=cm`",
        "em never directly spawns or contacts cm",
        "program or test success is not scientific acceptance",
    ):
        assert requirement in compact


def test_material_records_preserve_costly_evidence_and_common_v1_return() -> None:
    compact = _compact(_skill())

    for requirement in (
        "create artifacts only at material milestones",
        "there is no fixed document bundle",
        "a separate local-route file is optional",
        "never a default document tax",
        "write a terminal-gap note only when needed",
        "every durable ref is `{path, sha256}`",
        "one concise evidence note when a tool or cm observation materially changes or constrains judgment",
        "return the common v1 envelope as `hmasd-em` / `em-<direction-id>`",
        "payload fields defined by `.omp/agents.md`",
        "owner `em` for local work or interpretation",
        "`cm` for the durable engineering request",
        "`transport` for a frozen pro request",
    ):
        assert requirement in compact


def test_terminal_gap_preserves_science_without_converting_technical_failure() -> None:
    em = _compact(_skill())
    review = _compact(_external_review())

    for requirement in (
        "never merge a late result into a newer checkpoint",
        "reinterpret transport text as fact",
        "convert speculation into a claim",
        "never open a fresh cycle for recovery",
        "transport failure is excluded",
        "return `partial` for an evidence or terminal gap",
        "missing review, test, dashboard, advisor, or provider availability is an evidence gap",
    ):
        assert requirement in em
    assert "preserve the scientific stage reached" in review
