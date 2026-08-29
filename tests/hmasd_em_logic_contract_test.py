from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / ".omp" / "skills" / "hmasd-em-direction-cycle" / "SKILL.md"
CYCLE_BOUNDARIES = (
    "FRESH_MATERIAL_CYCLE",
    "CONTINUATION",
    "CM_RESULT_INTERPRETATION",
    "EVIDENCE_INTAKE",
    "TERMINAL_GAP_DISPOSITION",
)


def _skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, heading
    return match.group("body")


def _compact(text: str) -> str:
    return " ".join(text.lower().split())


def test_cycle_boundary_inventory_and_material_cycle_guard() -> None:
    text = _skill()
    section = _section(text, "Classify the cycle boundary")
    assert tuple(re.findall(r"^- `([A-Z_]+)`$", section, re.MULTILINE)) == CYCLE_BOUNDARIES

    compact = _compact(section)
    for trigger in (
        "new scientific object",
        "mechanism",
        "comparator",
        "discriminator",
        "possible claim increase",
        "overturns a core frozen assumption",
        "explicit portfolio reevaluation",
    ):
        assert trigger in compact
    assert "a new cycle cannot be opened merely to reset external operation budget" in compact
    assert "cm interpretation" in compact
    assert "evidence intake" in compact
    assert "claim narrowing" in compact
    assert "cannot be relabelled to obtain another send" in compact


def test_fresh_cycle_freezes_the_complete_scientific_object() -> None:
    section = _compact(_section(_skill(), "Freeze the full scientific object"))
    for requirement in (
        "scientific question",
        "decision relevance",
        "explicit non-goals",
        "scientific object",
        "finite claim ceiling",
        "estimand",
        "treatment and comparator",
        "observational unit",
        "exposure clock",
        "strongest simple null",
        "competing explanations",
        "distinct measurable prediction",
        "smallest proposed discriminator",
        "positive, negative, null, ambiguous, or invalid outcome",
        "baseline commit",
        "configuration",
        "data identity/provenance",
        "rng identity and seed policy",
        "checkpoint/bit-identity requirements",
        "protected numerical and external-effect semantics",
        "maximum observation rounds",
        "resource/effect bound",
        "early-stop rule",
        "scope-invalidating condition",
        "owned paths",
        "exact evidence refs",
    ):
        assert requirement in section
    assert "a changed scientific object ends the current cycle" in section


def test_local_routes_are_neutral_gap_driven_and_evidence_separated() -> None:
    section = _compact(_section(_skill(), "Neutral local routes and synthesis"))
    for requirement in (
        "same neutral freeze",
        "do not disclose em's favored answer",
        "another route's result",
        "actual information gaps",
        "not a fixed leaf quota",
        "two specialists by default",
        "up to four",
        "no_material_insight",
        "local-route-<route-id>.md",
        "synthesis.md",
        "`fact`, `inference`, and `speculation` sections",
        "search coverage, not independent evidence",
        "self-critique may open a route, but cannot change the claim ceiling",
    ):
        assert requirement in section
    synthesis_path = "`docs/research/candidates/<direction-id>/evidence/<cycle-id>-synthesis.md`"
    assert section.index(synthesis_path) < section.index("before authoring or requesting convergence")


def test_pro_innovator_and_convergence_are_default_independent_challenges() -> None:
    section = _compact(_section(_skill(), "Default Pro Innovator and Pro Convergence"))
    assert "every `fresh_material_cycle` defaults to one `pro innovator` operation and one `pro convergence` operation" in section
    assert "exact waiver for that exact still-unsent operation" in section
    assert "a waiver for one stage does not waive the other" in section
    assert "does not replace either default pro stage" in section
    assert "local em synthesis is a hard barrier before convergence" in section
    assert "only after the synthesis artifact exists" in section
    assert "without copying the innovator transcript as a substitute for synthesis" in section
    assert "disposition every material objection against evidence" in section


def test_browser_transport_is_root_mediated_and_scientifically_non_authoritative() -> None:
    section = _section(_skill(), "Root-mediated BrowserTransport")
    compact = _compact(section)
    for requirement in (
        "em never sends a provider request",
        "contacts or spawns browsertransport",
        "`next_action.owner=transport`",
        "root alone mediates the singleton logical service `browsertransport`",
        "agent type `hmasd-browser-transport`",
        "provider `chatgpt` or `gemini`",
        "agentify idempotency key and fingerprint",
        "unknown commitment never authorizes resend",
        "browsertransport owns only transport facts",
        "em owns the prompt and all scientific interpretation",
        "transport completion alone is not `review_resolved` or accepted science",
        "provider availability, absence, or agreement alone never changes the claim ceiling",
    ):
        assert requirement in compact
    for transport_fact in (
        "send was attempted or committed",
        "provider/model/conversation observations",
        "operation and archive refs",
        "readability",
        "exact transport state",
    ):
        assert transport_fact in compact


def test_engineering_request_is_durable_meaning_complete_and_root_routed() -> None:
    section = _section(_skill(), "Durable EM-to-CM engineering request")
    compact = _compact(section)
    assert "docs/research/candidates/<direction-id>/workflow/research/engineering-request.md" in section
    for requirement in (
        "scientific question and decision relevance",
        "competing explanations",
        "different prediction",
        "discriminator and observable acceptance",
        "explicit non-goals",
        "protected scientific, numerical, rng, checkpoint, bit-identity, and external-effect semantics",
        "baseline commit",
        "configuration",
        "data/provenance",
        "rng/seed policy",
        "exact owned paths",
        "resource bounds",
        "committed/permitted effects",
        "run plan without launching it",
        "positive, negative, null, ambiguous, and invalid observation branches",
        "required commands/tests/observations and artifact destinations",
        "known limitations",
        "meaning of technical failure",
        "`not_observed`",
    ):
        assert requirement in compact
    assert "expected revision/cas" in compact
    assert "`engineering_request.scope_ref`" in compact
    assert "payload `engineering_request_ref`" in compact
    assert "`next_action.input_refs`" in compact
    assert "`next_action.owner=cm`, to root" in compact
    assert "em does not directly spawn or contact cm" in compact
    assert "cm, code, tests, and commands do not decide science; em interprets every observation" in compact
    assert "program or test success is not scientific acceptance" in compact


def test_standard_em_artifacts_and_ref_locations_are_explicit() -> None:
    text = _skill()
    section = _section(text, "Durable milestones and refs")
    expected_paths = (
        "docs/research/candidates/<direction-id>/evidence/<cycle-id>-scope-freeze.md",
        "docs/research/candidates/<direction-id>/evidence/<cycle-id>-local-route-<route-id>.md",
        "docs/research/candidates/<direction-id>/evidence/<cycle-id>-synthesis.md",
        "docs/research/candidates/<direction-id>/evidence/<cycle-id>-terminal-gap.md",
        "docs/research/candidates/<direction-id>/evidence/<cycle-id>-handoff.md",
        "docs/research/candidates/<direction-id>/workflow/research/engineering-request.md",
    )
    for path in expected_paths:
        assert path in section
    for external_name in (
        "<cycle-id>-innovator-prompt.md",
        "<cycle-id>-convergence-prompt.md",
        "<cycle-id>-convergence-disposition.md",
    ):
        assert f"docs/research/candidates/<direction-id>/external/{external_name}" in text

    compact = _compact(section)
    assert "every durable ref is `{path, sha256}`" in compact
    assert "common envelope's `artifact_refs`" in compact
    assert "`conclusion_refs`" in compact
    assert "`next_action.input_refs`" in compact
    for handoff_meaning in (
        "mechanism-level conclusion",
        "decision impact",
        "finite claim ceiling",
        "strongest support and contradiction",
        "surviving alternative",
        "next discriminator",
        "recommendation",
        "shared dependencies",
        "limitations",
        "reentry condition",
    ):
        assert handoff_meaning in compact


def test_common_v1_em_payload_exposes_cycle_and_durable_request_ref() -> None:
    text = _skill()
    purpose = _compact(_section(text, "Purpose"))
    assert "omp `task` or hub carrier" in purpose
    assert "common v1 result envelope" in purpose
    assert "not omp routing authority" in purpose

    returned = _section(text, "Returned result envelope")
    match = re.search(r"```json\n(?P<payload>.*?)\n```", returned, re.DOTALL)
    assert match is not None
    payload = json.loads(match.group("payload"))
    assert payload == {
        "kind": "em",
        "direction_id": "<direction-id>",
        "cycle_id": "<stable-cycle-id>",
        "cycle_boundary": "FRESH_MATERIAL_CYCLE",
        "question_sha256": "<sha256>",
        "evidence_set_sha256": "<sha256>",
        "conclusion_refs": [],
        "engineering_request_ref": None,
    }
    compact = _compact(returned)
    for route in (
        "`next_action.owner=em`",
        "`cm` with the durable engineering request",
        "`transport` with the frozen external request",
        "`root` for completed direction reconciliation",
        "`user` only for a genuine decision/waiver boundary",
    ):
        assert route in compact
    assert "exact next-action input refs" in compact


def test_terminal_gap_preserves_science_without_converting_technical_failure() -> None:
    milestones = _compact(_section(_skill(), "Durable milestones and refs"))
    failure = _compact(_section(_skill(), "Failure handling"))
    assert "only after all committed effects have a terminal transport or technical fact" in milestones
    assert "preserve the unsynthesized evidence gap" in milestones
    assert "preserve the bounded synthesis and its decision impact" in milestones
    assert "independent convergence unresolved" in milestones
    assert "technical or transport failure cannot become a negative scientific result or lifecycle recommendation" in milestones
    assert "do not open a new material cycle for recovery" in failure
    assert "transport failure is excluded from that judgment" in failure
    assert "silently convert speculation into a claim" in failure
