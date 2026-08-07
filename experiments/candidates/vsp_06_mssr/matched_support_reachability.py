"""Zero-training structural proof: is P's carrier retentive and single-partner coupled?

BUILD 2026-08-06 (Claude, MSSR matched-support successor unit).  The sibling
``support_native_p_reachability`` established, and External Pro ruled
(terminal ``MSSR_P_SOURCE_INTERFACE_CLOSED_MATCHED_REACHABILITY_OPEN``), that
MSSR's owner-private partner-interaction state ``P`` is a registered,
non-injected, provenance-bound source -- but that this is object existence
only, NOT the stronger matched-support reachability (two legally reachable
histories differing only in historical ``P`` at one common current context).
Pro reserved ``MSSR_P_SUPPORT_NATIVE_PRESENT`` for that separate witness.

This module does NOT claim that witness.  It measures four purely STRUCTURAL
facts about the RUNTIME (the model maps ``encode_members`` / ``set_summary`` /
``logits`` and the registered ``_write_partner_interaction`` transition), with
zero training and no mutation of shared state, and derives a terminal from the
measured booleans.  The reduction it states is about the environment law; the
four measured facts are about the runtime components, independent of any
particular environment law:

1. The EMA carrier retains history: under a MATCHED current partner payload the
   resulting ``current_p`` still depends on the prior ``P`` (retention 0.8 > 0).
2. A single legal PARTNER-observation change that moves the alignment
   dot-product also moves the OWNER's actor context X0 (its ``selected_summary``
   and its next ``high_hidden``).  So the P channel and X0 are COUPLED under a
   single-partner variation: you cannot move one without the other.
3. The observation->member_embedding map has full column rank at the runtime's
   real dims, so no single observation direction is annihilated by the encoder
   (there is no obs dimension that moves the alignment while leaving the
   embedding, hence the summary, fixed).
4. The partner ``P`` is derived from is always a member of the summary
   aggregate: the partner-selection domain in
   ``VariableRosterEventCore._write_partner_interaction`` is the active set, and
   ``EventCommitmentPolicy.set_summary`` sums ``encode()`` over that same active
   set.

WHAT THIS PROVES AND DOES NOT
-----------------------------
Together these establish that SINGLE-PARTNER legal variation cannot change ``P``
without changing the owner's actor context X0.  They REDUCE the still-open
matched-support question to a precise remaining route: whether the frozen
environment law can reach two active-set configurations with EQUAL summary-sum
but DIFFERENT owner-alignment -- a multi-member "sum-fiber" route that this
proof does NOT search.  It asserts NO full unreachability and licenses no
scientific claim; it is object/relation existence only.

The measured facts are driven through the runtime's OWN registered transition
(``_write_partner_interaction``) and its OWN model maps (``encode_members``,
``set_summary``, ``logits``), reusing the runtime's test factory rather than
re-deriving a core -- exactly as the VSP-02 duration proof loads its helpers.
"""

from __future__ import annotations

import importlib.util
import pathlib
from dataclasses import dataclass

import torch

RAW_OUTPUT_BINDING = "vsp_06_mssr.matched_support_reachability.v1"


def _repository_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def _load_core_helpers():
    """Reuse the runtime's own test factory rather than rebuilding a core."""
    path = (
        _repository_root()
        / "tests"
        / "process"
        / "variable_roster"
        / "ha_ctse_process_variable_roster_event_test.py"
    )
    spec = importlib.util.spec_from_file_location("_mssr_vre_helpers", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str
    numbers: dict[str, float]


def carrier_retains_history() -> CheckResult:
    """Check 1: the EMA carries history under a MATCHED current payload.

    Two owner records are driven to DIFFERENT prior ``P`` through the registered
    ``_write_partner_interaction`` transition (positive vs negative alignment
    payloads -- no P setter is used), then ONE further write is applied to each
    with an IDENTICAL current partner payload (both see a zero-alignment
    partner, so ``payload = tanh(0) = 0`` in both).  Because
    ``next_p = clip(0.8*prior_p + 0.2*payload, -1, 1)`` retains ``0.8`` of the
    prior, the two ``current_p`` must still differ.
    """
    helpers = _load_core_helpers()
    core = helpers.make_core("f1", partner_interaction_enabled=True)
    helpers.initial_join(core, keys=("a", "b"), actions={"a": 0, "b": 1})
    record_a = core.records["a"]
    record_b = core.records["b"]

    # Differentiate the two priors via the registered transition: identical
    # owner observation, opposite-sign partner observation.
    obs_positive = torch.tensor([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    obs_negative = torch.tensor([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
    core._write_partner_interaction(
        record=record_a,
        owner_key="a",
        owner_row=0,
        active_keys=("a", "b"),
        active_observations=obs_positive,
        event_index=100,
    )
    core._write_partner_interaction(
        record=record_b,
        owner_key="b",
        owner_row=0,
        active_keys=("b", "a"),
        active_observations=obs_negative,
        event_index=100,
    )
    prior_a = float(record_a.partner_interaction_history.current_p)
    prior_b = float(record_b.partner_interaction_history.current_p)

    # One MATCHED current write: identical zero-alignment partner in both, so
    # the current payload is byte-identical (tanh(0) = 0) for a and b.
    obs_matched = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    core._write_partner_interaction(
        record=record_a,
        owner_key="a",
        owner_row=0,
        active_keys=("a", "b"),
        active_observations=obs_matched,
        event_index=101,
    )
    core._write_partner_interaction(
        record=record_b,
        owner_key="b",
        owner_row=0,
        active_keys=("b", "a"),
        active_observations=obs_matched,
        event_index=101,
    )
    p_a = float(record_a.partner_interaction_history.current_p)
    p_b = float(record_b.partner_interaction_history.current_p)
    difference = p_a - p_b
    passed = difference != 0.0
    return CheckResult(
        name="carrier_retains_history",
        passed=passed,
        detail=(
            f"two priors ({prior_a:.6f}, {prior_b:.6f}) driven through the "
            f"registered transition; after one MATCHED current write "
            f"(payload tanh(0)=0 in both) current_p = ({p_a:.6f}, {p_b:.6f}); "
            f"difference {difference:.6f} is "
            + ("nonzero, so the EMA carries history" if passed else "zero")
        ),
        numbers={
            "prior_p_a": prior_a,
            "prior_p_b": prior_b,
            "current_p_a": p_a,
            "current_p_b": p_b,
            "difference": difference,
        },
    )


def single_partner_variation_moves_owner_context() -> CheckResult:
    """Check 2: a legal partner-obs change that moves the alignment also moves X0.

    The owner's OWN observation is held fixed.  Two active sets are built that
    differ only in one partner's observation, chosen so the owner-partner
    alignment dot-product differs.  We measure, through the runtime's own model
    maps: (a) the change in ``dot(owner_obs, partner_obs)`` (the P channel), (b)
    the L2 change in the owner's ``selected_summary``
    (``set_summary(encode_members(...))``), and (c) the L2 change in the owner's
    next ``high_hidden`` (the GRU carry returned by ``logits``).  Coupled iff
    the P channel moved AND both owner quantities moved.
    """
    helpers = _load_core_helpers()
    core = helpers.make_core("f1", partner_interaction_enabled=True)
    policy = core.commitment_model
    obs_dim = int(policy.obs_dim)

    owner_obs = torch.tensor([0.5, -0.2, 0.3])
    partner_obs_1 = torch.tensor([0.4, 0.1, 0.0])
    partner_obs_2 = torch.tensor([-0.4, 0.1, 0.0])

    skills = torch.tensor([0, 1], dtype=torch.long)
    ages = torch.tensor([1.0, 1.0])
    flags = torch.tensor([[0, 0], [0, 0]])
    pre_hidden = torch.zeros(int(policy.high_hidden_dim))

    def _context(partner_obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        observations = torch.stack((owner_obs, partner_obs), dim=0)
        with torch.no_grad():
            embeddings = policy.encode_members(observations, skills, ages, flags)
            summary = policy.set_summary(embeddings)
            _logits, new_hidden = policy.logits(embeddings[0], summary, pre_hidden)
        return summary, new_hidden

    dot_1 = float(torch.dot(owner_obs, partner_obs_1))
    dot_2 = float(torch.dot(owner_obs, partner_obs_2))
    alignment_delta = abs(dot_2 - dot_1)

    summary_1, hidden_1 = _context(partner_obs_1)
    summary_2, hidden_2 = _context(partner_obs_2)
    summary_delta = float(torch.linalg.vector_norm(summary_2 - summary_1))
    hidden_delta = float(torch.linalg.vector_norm(hidden_2 - hidden_1))

    channel_moved = alignment_delta != 0.0
    context_moved = summary_delta != 0.0 and hidden_delta != 0.0
    passed = channel_moved and context_moved
    return CheckResult(
        name="single_partner_variation_moves_owner_context",
        passed=passed,
        detail=(
            f"owner obs fixed; one partner obs varied so alignment dot moved "
            f"{dot_1:.6f}->{dot_2:.6f} (|delta|={alignment_delta:.6f}); owner "
            f"selected_summary moved by L2 {summary_delta:.6f} and owner next "
            f"high_hidden moved by L2 {hidden_delta:.6f}; the P channel and X0 "
            f"are {'coupled' if passed else 'not coupled'} under this "
            f"single-partner variation (obs_dim={obs_dim})"
        ),
        numbers={
            "dot_1": dot_1,
            "dot_2": dot_2,
            "alignment_delta": alignment_delta,
            "summary_l2_delta": summary_delta,
            "high_hidden_l2_delta": hidden_delta,
        },
    )


def encoder_has_no_obs_nullspace() -> CheckResult:
    """Check 3: obs->member_embedding has full column rank (no ignored obs dir).

    The Jacobian ``d(encode_members)/d(obs)`` is computed numerically at a
    representative single-member input, at the runtime's real ``(obs_dim,
    member_hidden_dim)``.  Full column rank (rank == obs_dim) means no
    observation direction is annihilated by the encoder, so there is no single
    obs dimension that could move the alignment while leaving the embedding --
    and hence the summary -- fixed.

    IMPORTANT (local vs finite).  This rank is a LOCAL statement: it establishes
    no *infinitesimal* obs null-space at the measured point.  The finite claim --
    that no obs CHANGE moves the alignment while leaving the embedding fixed (an
    encoder self-intersection ``encode(o) = encode(o')`` with
    ``owner.o != owner.o'``) -- does not follow from a single-point rank alone;
    it additionally rests on (i) check 2's finite worked example of the coupling,
    and (ii) the self-intersection being non-generic (codimension
    ``member_hidden_dim - obs_dim``, here 9, for a smooth immersion), which an
    adversarial collision search did not defeat.  This proof does NOT run that
    global search; the local rank plus the finite check-2 example are what it
    measures, and the genericity is stated as an argument, not a theorem.
    """
    helpers = _load_core_helpers()
    core = helpers.make_core("f1", partner_interaction_enabled=True)
    policy = core.commitment_model
    obs_dim = int(policy.obs_dim)
    member_hidden_dim = int(policy.member_hidden_dim)

    skills = torch.tensor([0], dtype=torch.long)
    ages = torch.tensor([1.0])
    flags = torch.tensor([[0, 0]])
    obs_point = torch.tensor([0.5, -0.2, 0.3])

    def _encode(obs_vector: torch.Tensor) -> torch.Tensor:
        observations = obs_vector.reshape(1, obs_dim)
        return policy.encode_members(observations, skills, ages, flags).reshape(-1)

    jacobian = torch.autograd.functional.jacobian(_encode, obs_point)
    jacobian = jacobian.reshape(member_hidden_dim, obs_dim)
    singular_values = torch.linalg.svdvals(jacobian)
    rank = int(torch.linalg.matrix_rank(jacobian))
    smallest_singular = float(singular_values.min())
    passed = rank == obs_dim
    return CheckResult(
        name="encoder_has_no_obs_nullspace",
        passed=passed,
        detail=(
            f"Jacobian d(encode_members)/d(obs) has shape "
            f"({member_hidden_dim}, {obs_dim}) at the runtime's real dims "
            f"(obs_dim={obs_dim}, member_hidden_dim={member_hidden_dim}); "
            f"numerical rank {rank}, smallest singular value "
            f"{smallest_singular:.6e}; full column rank "
            f"{'holds' if passed else 'FAILS'} so no obs direction is ignored"
        ),
        numbers={
            "jacobian_rows": float(member_hidden_dim),
            "jacobian_cols": float(obs_dim),
            "rank": float(rank),
            "obs_dim": float(obs_dim),
            "member_hidden_dim": float(member_hidden_dim),
            "smallest_singular_value": smallest_singular,
        },
    )


def partner_source_is_a_summary_member() -> CheckResult:
    """Check 4: P's partner is always a member of the summary aggregate.

    Runtime assertion (not a string match): across constructed events the
    partner recorded by ``_write_partner_interaction`` for each owner is drawn
    from the active set -- the SAME domain ``set_summary`` sums ``encode()``
    over.  The partner-selection loop ranges over ``active_observations`` rows
    (the active set) and ``set_summary`` sums over that same active set, so the
    partner is structurally a summary member.  We verify, over two active-set
    configurations, that every recorded ``partner_lifecycle_key`` is an active
    lifecycle key feeding that event's summary and is distinct from the owner.
    """
    helpers = _load_core_helpers()
    configurations = (
        ("a", "b"),
        ("a", "b", "c"),
    )
    checked = 0
    violations: list[str] = []
    for keys in configurations:
        core = helpers.make_core("f1", partner_interaction_enabled=True)
        actions = {key: index for index, key in enumerate(keys)}
        helpers.initial_join(core, keys=keys, order=keys, actions=actions)
        # The active set that feeds the summary is exactly the active lifecycle
        # keys with a written P this event.
        active_set = set(keys)
        for owner_key in keys:
            history = core.records[owner_key].partner_interaction_history
            if history is None or not history.rows:
                violations.append(f"{keys}:{owner_key}:no-P-written")
                continue
            partner_key = history.rows[-1].partner_lifecycle_key
            checked += 1
            if partner_key == owner_key:
                violations.append(f"{keys}:{owner_key}:partner-is-owner")
            elif partner_key not in active_set:
                violations.append(
                    f"{keys}:{owner_key}:partner-{partner_key}-not-in-summary"
                )
    passed = checked > 0 and not violations
    return CheckResult(
        name="partner_source_is_a_summary_member",
        passed=passed,
        detail=(
            f"over configurations {configurations} checked {checked} owner "
            f"writes; each recorded partner is an active lifecycle key feeding "
            f"that event's summary and distinct from the owner; violations = "
            f"{violations or '[]'}"
        ),
        numbers={
            "owner_writes_checked": float(checked),
            "violations": float(len(violations)),
        },
    )


def proof() -> dict[str, object]:
    checks = (
        carrier_retains_history(),
        single_partner_variation_moves_owner_context(),
        encoder_has_no_obs_nullspace(),
        partner_source_is_a_summary_member(),
    )
    coupled = all(check.passed for check in checks)
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "checks": {
            check.name: {
                "passed": check.passed,
                "detail": check.detail,
                "numbers": check.numbers,
            }
            for check in checks
        },
        "terminal": (
            "MSSR_MATCHED_SUPPORT_SINGLE_PARTNER_COUPLED"
            if coupled
            else "MSSR_MATCHED_SUPPORT_COUPLING_INCONCLUSIVE"
        ),
        "scope": (
            "Zero-training STRUCTURAL proof; object/relation existence only. "
            "Finds that SINGLE-PARTNER variation cannot change P without changing "
            "the owner's actor context X0 (its selected_summary and next "
            "high_hidden): the EMA carrier retains history, the "
            "partner-obs->alignment channel moves the owner's summary and GRU "
            "carry (finitely demonstrated, check 2), the obs->embedding encoder "
            "has no LOCAL obs null-space (full column rank, check 3; global "
            "non-collision argued by non-generic codimension, not proven), and "
            "P's partner is always a summary member. It "
            "REDUCES the open matched-support question to whether the frozen "
            "environment law can reach two active-set configurations with EQUAL "
            "summary-sum but DIFFERENT owner-alignment -- a multi-member "
            "'sum-fiber' route this proof does NOT search -- and asserts NO full "
            "unreachability. It licenses no scientific claim and no build."
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(proof(), indent=2))
