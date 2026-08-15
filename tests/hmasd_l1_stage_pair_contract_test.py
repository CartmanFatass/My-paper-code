"""Focused static and in-memory smoke checks for direction-stage L1 delegation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SURFACES = (
    "AGENTS.md",
    ".agents/roles/ROOT.md",
    ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md",
    ".agents/roles/CODE_PROJECT_MANAGER.md",
    ".agents/skills/hmasd-independent-research-exploration/SKILL.md",
    ".agents/skills/hmasd-independent-research-exploration/references/parallel-research-workflow.md",
    ".agents/skills/hmasd-explorer-project-validation/SKILL.md",
    ".agents/skills/hmasd-external-gemini/SKILL.md",
    "docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md",
    "docs/project/handoffs/README.md",
    ".codex/agents/hmasd-independent-research-explorer.toml",
    ".codex/agents/hmasd-code-project-manager.toml",
)


def _flat(*paths: str) -> str:
    text = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in paths)
    return " ".join(text.lower().split())


@dataclass(frozen=True)
class StageEnvelope:
    direction_id: str
    objective: str
    portfolio_rationale: str
    refinement_boundary: str
    protected_science: str
    provider_authority: str
    engineering_light_probe_boundary: str
    heavy_compute_class: str
    root_return_triggers: str
    em_task: str
    cm_task: str
    stage_id: str


@dataclass(frozen=True)
class ComputeLease:
    direction_id: str
    stage_id: str
    resource_limit: str
    concurrency: int
    valid_period: str


class RejectedMessage(ValueError):
    """The simulated control plane refused an authority or isolation violation."""


class StageChannel:
    EM_TO_CM = {
        "science_card",
        "scientific_clarification",
        "pro_closed_revision",
        "authorized_next_treatment",
    }
    CM_TO_EM = {
        "scientific_ambiguity",
        "technical_result_packet",
        "observed_condition_change_request",
    }
    ROOT_MILESTONE = "decision_milestone"

    def __init__(self, envelope: StageEnvelope, lease: ComputeLease | None = None) -> None:
        self.envelope = envelope
        self.lease = lease
        self.em_inbox: list[str] = []
        self.cm_inbox: list[str] = []
        self.root_inbox: list[str] = []
        self.followups: list[tuple[str, str]] = []

    def followup(self, task: str, label: str) -> None:
        if task not in {self.envelope.em_task, self.envelope.cm_task}:
            raise RejectedMessage("follow-up must reuse a canonical stage-pair task")
        self.followups.append((task, label))

    def direct(self, sender: str, recipient: str, direction_id: str, kind: str) -> None:
        if direction_id != self.envelope.direction_id:
            raise RejectedMessage("wrong direction_id")
        if sender == self.envelope.em_task and recipient == self.envelope.cm_task:
            if kind not in self.EM_TO_CM:
                raise RejectedMessage("EM payload is outside the bounded direct channel")
            self.cm_inbox.append(kind)
            return
        if sender == self.envelope.cm_task and recipient == self.envelope.em_task:
            if kind not in self.CM_TO_EM:
                raise RejectedMessage("CM payload is outside the bounded direct channel")
            self.em_inbox.append(kind)
            return
        raise RejectedMessage("cross-direction or unnamed sibling contact")

    def heavy_compute(self, direction_id: str, stage_id: str) -> None:
        if (
            self.lease is None
            or self.lease.direction_id != direction_id
            or self.lease.stage_id != stage_id
        ):
            raise RejectedMessage("heavy compute requires the matching Root lease")

    def root_return(self, sender: str, direction_id: str, kind: str, packet: dict[str, str]) -> None:
        if sender != self.envelope.em_task or direction_id != self.envelope.direction_id:
            raise RejectedMessage("only the paired EM returns its direction milestone")
        if kind != self.ROOT_MILESTONE:
            raise RejectedMessage("L1 cannot issue a portfolio decision")
        required = {
            "conclusion",
            "key_observation",
            "strongest_alternative",
            "claim_ceiling",
            "possible_portfolio_effect",
            "next_discriminator",
            "root_decision_requested",
        }
        if set(packet) != required:
            raise RejectedMessage("milestone packet must be compact and decision-complete")
        self.root_inbox.append(kind)


def _smoke_envelope() -> StageEnvelope:
    return StageEnvelope(
        direction_id="smoke-l1",
        objective="exercise routing only; no scientific computation",
        portfolio_rationale="contract smoke only",
        refinement_boundary="fixed synthetic message kinds",
        protected_science="no variables, hypothesis, claims, or cross-direction evidence",
        provider_authority="none",
        engineering_light_probe_boundary="in-memory messages only",
        heavy_compute_class="none",
        root_return_triggers="one synthetic decision milestone",
        em_task="/root/EM_smoke_l1",
        cm_task="/root/CM_smoke_l1",
        stage_id="routing-smoke",
    )


def test_static_contract_retains_root_macro_science_and_cross_direction_authority() -> None:
    root = _flat("AGENTS.md", ".agents/roles/ROOT.md")
    for phrase in (
        "problem-family discovery and screening",
        "discriminator-value judgment",
        "portfolio investment/pause/fusion decisions",
        "shared resource allocation",
        "cross-direction communication remains root-only",
        "root independently decides",
    ):
        assert phrase in root


def test_static_contract_defines_stage_pair_envelope_lease_and_milestone_filter() -> None:
    text = _flat(*SURFACES)
    for phrase in (
        "ordinary-language stage authority envelope",
        "counterpart canonical task name",
        "followup_task",
        "meaning-complete science card",
        "technically accepted result packet",
        "root-issued direction lease",
        "resource limits, concurrency, validity period and stage boundary",
        "first explicit-noncommit recovery",
        "cm -> same-direction em",
        "owning em may authorize exactly one later fresh-tab attempt",
        "conclusion, key observation, strongest alternative",
        "currently active vqfp treatment",
        "owner logging is direct",
    ):
        assert phrase in text


def test_static_contract_removes_root_only_sibling_relay_and_action_releases() -> None:
    text = _flat(*SURFACES)
    for obsolete in (
        "em -> root -> cm",
        "em->root->cm",
        "cm -> root -> same-direction em",
        "em and cm never communicate directly",
        "root relays between them",
        "root may explicitly authorize a later fresh-tab attempt",
        "request root release for each production attempt",
        "request root release for each provider batch",
    ):
        assert obsolete not in text


def test_l1_same_direction_direct_channel_and_followup_reuse_smoke() -> None:
    envelope = _smoke_envelope()
    channel = StageChannel(envelope)

    channel.direct(envelope.em_task, envelope.cm_task, envelope.direction_id, "science_card")
    channel.direct(
        envelope.cm_task,
        envelope.em_task,
        envelope.direction_id,
        "technical_result_packet",
    )
    channel.followup(envelope.em_task, "interpret the synthetic technical packet")
    channel.followup(envelope.cm_task, "handle the authorized synthetic next treatment")
    channel.direct(
        envelope.em_task,
        envelope.cm_task,
        envelope.direction_id,
        "authorized_next_treatment",
    )
    channel.direct(
        envelope.cm_task,
        envelope.em_task,
        envelope.direction_id,
        "technical_result_packet",
    )
    channel.root_return(
        envelope.em_task,
        envelope.direction_id,
        "decision_milestone",
        {
            "conclusion": "routing contract completed",
            "key_observation": "both direct handoffs reached the named counterpart",
            "strongest_alternative": "a message gate could have relayed through Root",
            "claim_ceiling": "control-plane smoke only",
            "possible_portfolio_effect": "none",
            "next_discriminator": "none",
            "root_decision_requested": "accept or reject the control-plane contract",
        },
    )

    assert channel.cm_inbox == ["science_card", "authorized_next_treatment"]
    assert channel.em_inbox == ["technical_result_packet", "technical_result_packet"]
    assert channel.followups == [
        ("/root/EM_smoke_l1", "interpret the synthetic technical packet"),
        ("/root/CM_smoke_l1", "handle the authorized synthetic next treatment"),
    ]
    assert channel.root_inbox == ["decision_milestone"]


def test_isolation_rejects_wrong_direction_cross_direction_portfolio_and_unleased_compute() -> None:
    envelope = _smoke_envelope()
    channel = StageChannel(envelope)

    with pytest.raises(RejectedMessage, match="wrong direction_id"):
        channel.direct(envelope.em_task, envelope.cm_task, "other", "science_card")
    with pytest.raises(RejectedMessage, match="cross-direction"):
        channel.direct(envelope.em_task, "/root/CM_other", envelope.direction_id, "science_card")
    with pytest.raises(RejectedMessage, match="portfolio decision"):
        channel.root_return(envelope.em_task, envelope.direction_id, "portfolio_decision", {})
    with pytest.raises(RejectedMessage, match="Root lease"):
        channel.heavy_compute(envelope.direction_id, envelope.stage_id)


def test_matching_compute_lease_allows_only_the_authorized_stage() -> None:
    envelope = _smoke_envelope()
    lease = ComputeLease(
        direction_id=envelope.direction_id,
        stage_id=envelope.stage_id,
        resource_limit="1 synthetic unit",
        concurrency=1,
        valid_period="this smoke invocation",
    )
    channel = StageChannel(envelope, lease)
    channel.heavy_compute(envelope.direction_id, envelope.stage_id)
    with pytest.raises(RejectedMessage, match="matching Root lease"):
        channel.heavy_compute(envelope.direction_id, "later-stage")
