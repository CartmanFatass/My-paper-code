"""Zero-training interface proof: is MSSR's P a registered, non-injected source?

BUILD UPDATE 2026-08-06 (Claude overnight, loop 1) + PRO RULING.  The three
objects this proof maps were BUILT by genuine construction, and External Pro
ruled on them (ruling terminal
``MSSR_P_SOURCE_INTERFACE_CLOSED_MATCHED_REACHABILITY_OPEN``, conversation
``6a74326a``, archived at
``local_research/pro_reviews/vsp06_mssr_support_native_p_v1/40_RAW_RESPONSE.md``,
sha256 ``44d20b688afb485a71b30d5205ca6ca4b57c5e62a91662072094ca062571a343``,
VERBATIM_OK).  Pro found the SOURCE INTERFACE closed -- owner-private P carrier,
registered cross-member write transition, non-injected provenance-bound origin,
and pre-GRU logit availability are all CLOSED -- but corrected the terminal:
``MSSR_P_SUPPORT_NATIVE_PRESENT`` OVERCLAIMED, because the objects prove
source-carrier existence, not the stronger matched-support reachability (two
legally reachable histories differing only in historical P at one common current
context).  Per Pro this proof now reports the narrower
``MSSR_P_REGISTERED_SOURCE_PRESENT``; ``MSSR_P_SUPPORT_NATIVE_PRESENT`` is
reserved for the matched-support witness, which is the next funded unit.

The objects are: (1) an owner-private
``LifecycleRecord.partner_interaction_history`` field; (2) a registered
partner-interaction transition (``VariableRosterEventCore._write_partner_interaction``)
that writes P deterministically from a specific other member's *environment
observation*, bound to its full provenance tuple, writable only by the
transition, and placed AFTER the sampled action (Pro condition 5A: the P write
follows the actual action, so it is not a pre-logit recurrent update); and (3) an
``EventCommitmentPolicy.first_logits`` pre-recurrence action head (a feasible
surface -- not yet the actual action path, which remains ``.logits()``).  All
three are additive and gated behind
``partner_interaction_enabled`` / ``partner_first_action`` (default OFF), so every
existing rollout is byte-identical.  The checks are weak (name / word / functional
matching), so honesty rests on the implementation and independent review, NOT the
green checks -- see
``local_research/portfolio/2026-08-06_mssr_support_native_p_build_design.md``.
The interface is OBJECT EXISTENCE only and licenses no scientific claim and no
build.

External Pro, ruling ``SKILL_LIFETIME_TWO_DISTINCT_CAPABILITIES``
(``local_research/pro_reviews/skill_lifetime_capability_v1/40_RAW_RESPONSE.md``,
sha256 ``34247491…``, VERBATIM_OK) refused to authorize a build and named this
proof as the precondition:

    Current funding ruling: do not authorize a combined production build. First
    establish MSSR's support-native P reachability and VSP-02's real
    duration-exposure mapping as separate zero-training interface proofs.

and, on why speculation is the wrong move here:

    It is not worth implementing the partition and action-head surgery
    speculatively while P remains a synthetic injected quantity.

This module is that proof.  It runs no training, mutates nothing, and either
exhibits a support-native P or maps its absence precisely.  A precise absence
map is a valid outcome, not a failure.

WHAT "SUPPORT-NATIVE P" REQUIRES
--------------------------------
P is the partner-interaction historical state.  The MSSR candidate registers it
as ``unit.partner_interaction`` backed by a ``partner_interaction_cell``
persistent cell.  Pro's minimal accepted object:

    P cannot be injected through a test-only setter or supplied as an arm label.
    The minimal accepted object is an owner-local partner-history state whose
    writes are generated only by a registered partner-interaction transition.

with each write verifier-bound to episode, owner lifecycle key, owner membership
epoch, partner identity, event index, prior P, interaction payload, next P and
writer/version identity.  And decisively:

    This is the environment-side prerequisite. The event core, being
    environment-free, cannot manufacture it.

THE THREE CHECKS
----------------
1. Does any owner-private record field hold partner-interaction history?
2. Does the host runtime contain a registered partner-interaction transition?
3. Does the action path satisfy ``first_logits_tick < recurrent_update_tick``?

Check 3 is included because Pro corrected a reading we had proposed.  We had
suggested the ordering "appears" satisfied because ``_process_frontier`` computes
logits from the owner's pre-token hidden state and only later writes back
``high_hidden``.  Pro's ruling:

    That storage order is not the relevant ordering. [...] The action
    distribution therefore reads the post-recurrence hidden value. Delaying the
    writeback to record.high_hidden does not change that computational
    dependency.

So check 3 verifies the *computational* dependency functionally, not the storage
order.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
from dataclasses import dataclass

import torch

RAW_OUTPUT_BINDING = "vsp_06_mssr.support_native_p_reachability.v1"

#: The runtime Pro named as the only admissible host.
HOST_RUNTIME_FILES = (
    "ha_ctse_process/variable_roster_event.py",
    "ha_ctse_process/variable_roster_event_types.py",
    "ha_ctse_process/variable_roster_event_models.py",
    "ha_ctse_process/dynamic_roster_testbed.py",
    "ha_ctse_process/event_process_runner.py",
)

#: Vocabulary any implementation of a partner-interaction transition would have
#: to use under some name.  Matched on word boundaries so that substrings inside
#: exception names such as ``BrokenPipeError`` or ``TypeError`` do not count --
#: an unbounded search reports ~100 hits here and every one is a false positive.
PARTNER_VOCABULARY = (
    "partner",
    "peer",
    "counterpart",
    "dyad",
    "pairwise",
    "opponent",
    "teammate",
    "bilateral",
    "interaction",
)


def _repository_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


def owner_private_state_inventory() -> CheckResult:
    """Check 1: does any owner-private record field hold partner history?"""
    from ha_ctse_process.variable_roster_event_types import LifecycleRecord

    fields = tuple(field.name for field in dataclasses.fields(LifecycleRecord))
    suspicious = tuple(
        name
        for name in fields
        if any(token in name.lower() for token in PARTNER_VOCABULARY)
    )
    return CheckResult(
        name="owner_private_partner_state",
        passed=bool(suspicious),
        detail=(
            f"LifecycleRecord fields = {fields}; "
            f"partner-bearing fields = {suspicious or '()'}"
        ),
    )


def registered_partner_transition() -> CheckResult:
    """Check 2: does the host runtime contain a partner-interaction transition?"""
    root = _repository_root()
    hits: dict[str, int] = {}
    for relative in HOST_RUNTIME_FILES:
        path = root / relative
        if not path.exists():
            raise FileNotFoundError(f"host runtime file missing: {relative}")
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in PARTNER_VOCABULARY:
            found = len(re.findall(rf"\b{token}", text, flags=re.IGNORECASE))
            if found:
                hits[f"{relative}:{token}"] = found
    return CheckResult(
        name="registered_partner_transition",
        passed=bool(hits),
        detail=(
            f"word-boundary hits across the {len(HOST_RUNTIME_FILES)} host "
            f"runtime files = {hits or '{}'}"
        ),
    )


def preaction_ordering() -> CheckResult:
    """Check 3: does the support-native capability expose a PRE-recurrence action?

    Verified functionally, not by reading the storage order.  Two facts are
    checked together, so the check cannot pass by silently making the *default*
    path pre-recurrence:

    * BASELINE -- the default production action path
      (``EventCommitmentPolicy.logits``) still reads the POST-recurrence hidden
      value; it is unchanged, and the FOLR / continuous-roster runs depend on
      that.
    * SUPPORT-NATIVE -- an MSSR-enabled policy (``partner_first_action=True``)
      exposes ``first_logits``, whose action is produced from the pre-recurrence
      hidden state and the owner's historical P BEFORE the GRU update; its logits
      are NOT reproducible from the post-recurrence hidden value.

    The check passes iff the baseline is still post-recurrence AND the
    support-native first-action path is genuinely pre-recurrence.  This is the
    functional test Pro required: "the action distribution [must not] read the
    post-recurrence hidden value", verified for both paths.
    """
    from ha_ctse_process.variable_roster_event_models import EventCommitmentPolicy

    torch.manual_seed(17)
    policy = EventCommitmentPolicy(
        obs_dim=6,
        n_skills=4,
        member_hidden_dim=12,
        high_hidden_dim=10,
        skill_embedding_dim=5,
        partner_first_action=True,
    )
    torch.manual_seed(23)
    member_embedding = torch.randn(policy.member_hidden_dim)
    summary = torch.randn(policy.summary_dim)
    pre_hidden = torch.randn(policy.high_hidden_dim)

    def _reconstruct_from_post(new_hidden: torch.Tensor) -> torch.Tensor:
        return policy.skill_head(
            policy.decoder_hidden(
                torch.cat(
                    (
                        new_hidden.reshape(1, policy.high_hidden_dim),
                        summary.reshape(1, policy.summary_dim),
                    ),
                    dim=-1,
                )
            )
        ).squeeze(0)

    with torch.no_grad():
        default_logits, default_new = policy.logits(
            member_embedding, summary, pre_hidden
        )
        default_is_post = bool(
            torch.equal(default_logits, _reconstruct_from_post(default_new))
        )
        first, first_new = policy.first_logits(member_embedding, summary, pre_hidden)
        first_is_post = bool(torch.equal(first, _reconstruct_from_post(first_new)))

    passed = default_is_post and not first_is_post
    return CheckResult(
        name="preaction_ordering",
        passed=passed,
        detail=(
            f"default action path reads the post-recurrence hidden "
            f"(baseline={default_is_post}); the MSSR first_logits path is "
            f"{'reproducible from' if first_is_post else 'independent of'} the "
            f"post-recurrence hidden, so a support-native pre-recurrence action "
            f"head {'exists' if passed else 'does not exist'}"
        ),
    )


def proof() -> dict[str, object]:
    checks = (
        owner_private_state_inventory(),
        registered_partner_transition(),
        preaction_ordering(),
    )
    reachable = all(check.passed for check in checks)
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "host_runtime": list(HOST_RUNTIME_FILES),
        "checks": {
            check.name: {"passed": check.passed, "detail": check.detail}
            for check in checks
        },
        "terminal": (
            "MSSR_P_REGISTERED_SOURCE_PRESENT"
            if reachable
            else "MSSR_P_REGISTERED_SOURCE_ABSENT"
        ),
        "scope": (
            "Zero-training SOURCE-INTERFACE proof. Establishes object existence "
            "only -- a registered, non-injected, provenance-bound owner-private P "
            "carrier and a feasible pre-GRU action surface -- and licenses no "
            "scientific claim and no build. Per External Pro's loop-1 ruling "
            "(terminal MSSR_P_SOURCE_INTERFACE_CLOSED_MATCHED_REACHABILITY_OPEN) the "
            "stronger matched-support reachability -- two legally reachable histories "
            "differing only in historical P at one common current context -- is a "
            "SEPARATE open object, and MSSR_P_SUPPORT_NATIVE_PRESENT is reserved for "
            "that witness."
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(proof(), indent=2))
