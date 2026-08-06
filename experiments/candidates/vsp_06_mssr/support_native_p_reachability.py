"""Zero-training interface proof: is MSSR's P support-native and reachable?

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


def preaction_ordering(model=None) -> CheckResult:
    """Check 3: is ``first_logits_tick < recurrent_update_tick``?

    Verified functionally, not by reading the storage order.  If the returned
    logits can be reproduced exactly from the POST-recurrence hidden value, then
    the action distribution depends on the recurrent update and the required
    strict ordering is violated.
    """
    if model is None:
        from ha_ctse_process.variable_roster_event_models import (
            EventCommitmentPolicy,
        )

        torch.manual_seed(17)
        # summary_dim is derived by the model as member_hidden_dim + 1.
        model = EventCommitmentPolicy(
            obs_dim=6,
            n_skills=4,
            member_hidden_dim=12,
            high_hidden_dim=10,
            skill_embedding_dim=5,
        )

    torch.manual_seed(23)
    member_embedding = torch.randn(model.member_hidden_dim)
    summary = torch.randn(model.summary_dim)
    pre_hidden = torch.randn(model.high_hidden_dim)

    with torch.no_grad():
        logits, new_hidden = model.logits(member_embedding, summary, pre_hidden)
        # Recompute the decoder/head path from the POST-recurrence hidden value.
        reconstructed = model.skill_head(
            model.decoder_hidden(
                torch.cat(
                    (
                        new_hidden.reshape(1, model.high_hidden_dim),
                        summary.reshape(1, model.summary_dim),
                    ),
                    dim=-1,
                )
            )
        ).squeeze(0)

    depends_on_post_recurrence = bool(torch.equal(logits, reconstructed))
    return CheckResult(
        name="preaction_ordering",
        # The contract wants logits BEFORE recurrence, so the check passes only
        # if the logits are NOT reproducible from the post-recurrence hidden.
        passed=not depends_on_post_recurrence,
        detail=(
            "logits are bitwise reproducible from the post-recurrence hidden "
            "state, so first_logits_tick > recurrent_update_tick"
            if depends_on_post_recurrence
            else "logits do not depend on the post-recurrence hidden state"
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
            "MSSR_P_SUPPORT_NATIVE_PRESENT"
            if reachable
            else "MSSR_P_SUPPORT_NATIVE_ABSENT"
        ),
        "scope": (
            "Zero-training interface proof. Establishes object existence only; "
            "it licenses no scientific claim about MSSR and no build."
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(proof(), indent=2))
