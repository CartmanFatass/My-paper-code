"""Calibration tests for `scripts/assert_vk0d_order_conjugacy.py` (A-VD-5).

The gate is the hard precondition A-VD-5 puts in front of every
conclusion-bearing PRIMARY result, so each test here is present because failing
it would make that gate certify something it did not check:

* `test_panel_state_count_matches_the_independent_bound` and
  `test_panel_completeness_catches_a_missing_class` -- a panel that silently
  omits a reachable class would report PASS over a proper subset of the frozen
  support. The expected count is written as the A-VD-5 arithmetic and as the
  literal 8964, and cross-checked against the V-K0C driver's independent
  reachable-state accounting.
* `test_swap_state_is_a_byte_exact_involution` and
  `test_swap_state_covers_every_agent_indexed_component` -- a swap that misses
  one physical-agent-indexed component would certify a weaker equality than
  A-VD-5's. Each component is proven covered by leaving exactly it unswapped
  and watching the check go red.
* `test_gate_passes_on_the_fresh_conjugate_config` /
  `test_gate_rejects_the_constructed_negative_witness` -- the paired positive
  and deliberate negative. A conjugacy gate that cannot go red is not a gate.
* `test_witness_schema_is_stable` / `test_witness_is_write_once` -- the V-K0D
  analyzer consumes this JSON by key.

The gate's own panel is 8,964 states; these tests run it over a bounded set of
checks (`check_indices`, a test-only parameter with no CLI knob) because their
subject is the gate's machinery, not the arm's full certification. The full
panel is exercised by the driver run recorded in the task report.
"""

import itertools
import json
import math
import sys
from pathlib import Path

import pytest
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _p in (PROJECT_ROOT, PROJECT_ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import assert_vk0d_order_conjugacy as gate  # noqa: E402
import audit_vk0c_order_transport as vk0c  # noqa: E402
from ha_ctse_process.r30_fixed_clock import FixedClockAREditPolicy  # noqa: E402

CONJUGATE_CONFIG = "config_d7_2b_toy_conjugate_keep"
FRESH_SEED = 2026080101

# A-VD-5's panel arithmetic, written out rather than imported: four sign pairs
# times (one INITIAL state + sum over checks 1..7 of 16 physical skill pairs
# times c**2 reachable age pairs).
EXPECTED_PANEL_TOTAL = 4 * (1 + (16 * 1) + (16 * 4) + (16 * 9) + (16 * 16) + (16 * 25) + (16 * 36) + (16 * 49))
EXPECTED_PANEL_TOTAL_LITERAL = 8964


# --------------------------------------------------------------- the panel ---


def test_panel_state_count_matches_the_independent_bound():
    panel = gate.enumerate_panel()
    gate.assert_panel_complete(panel)

    assert EXPECTED_PANEL_TOTAL == EXPECTED_PANEL_TOTAL_LITERAL
    assert len(panel) == EXPECTED_PANEL_TOTAL_LITERAL
    # Independent accounting: the V-K0C propagation sweep's own reachable-state
    # bound (1 + sum_c 16*c**2 = 2241 per sign pair), reached by a different
    # code path and frozen before this gate existed.
    assert len(panel) == 4 * vk0c.reachable_state_bound()

    inventory = gate.panel_inventory(panel)
    assert inventory["initial_states"] == 4
    assert inventory["active_states"] == EXPECTED_PANEL_TOTAL_LITERAL - 4
    assert inventory["orders"] == 2
    assert inventory["age_pairs_per_check"] == {
        "0": 1, "1": 1, "2": 4, "3": 9, "4": 16, "5": 25, "6": 36, "7": 49,
    }
    # Every panel state is distinct.
    assert len({s.key() for s in panel}) == len(panel)


@pytest.mark.parametrize(
    "mutation,expected_fragment",
    [
        ("drop_last_check", "sign pairs"),
        ("drop_one_sign_pair", "sign pairs"),
        ("drop_one_skill_pair", "ACTIVE states, expected"),
        ("drop_one_age_pair", "ACTIVE states, expected"),
        ("drop_initial_class", "sign pairs"),
        ("extra_initial_state", "INITIAL class carries"),
        ("corrupt_initial_class", "not the frozen A-VD-5 class"),
        ("duplicate_a_state", "duplicate states"),
        ("unreachable_age", "age pairs"),
    ],
)
def test_panel_completeness_catches_a_missing_class(mutation, expected_fragment):
    """Predicted failure mode (a): a panel that silently omits a class. Each
    mutation below plants exactly that defect and requires
    `assert_panel_complete` -- not the enumerator that produced the panel -- to
    reject it."""
    panel = gate.enumerate_panel()
    gate.assert_panel_complete(panel)  # fixture check: unmutated panel is accepted

    if mutation == "drop_last_check":
        mutated = [s for s in panel if s.check_index != 7]
        # Dropping a whole check leaves a structurally consistent panel of a
        # smaller support, so the count against the frozen total is what
        # catches it; assert that separately from the structural checker.
        gate.assert_panel_complete(mutated)
        assert len(mutated) != EXPECTED_PANEL_TOTAL_LITERAL
        return
    if mutation == "drop_one_sign_pair":
        mutated = [s for s in panel if not (s.check_index == 3 and tuple(s.signs) == (1, -1))]
    elif mutation == "drop_one_skill_pair":
        mutated = [s for s in panel if not (s.check_index == 3 and tuple(s.skills) == (2, 3))]
    elif mutation == "drop_one_age_pair":
        mutated = [s for s in panel if not (s.check_index == 4 and tuple(s.ages) == (10, 15))]
    elif mutation == "drop_initial_class":
        mutated = [s for s in panel if not (s.check_index == 0 and tuple(s.signs) == (-1, 1))]
    elif mutation == "extra_initial_state":
        mutated = list(panel) + [
            gate.PanelState(signs=(1, 1), check_index=0, skills=(-1, -1), ages=(0, 0), active=(True, True))
        ]
    elif mutation == "corrupt_initial_class":
        mutated = list(panel)
        victim = next(i for i, s in enumerate(mutated) if s.check_index == 0)
        mutated[victim] = gate.PanelState(
            signs=mutated[victim].signs,
            check_index=0,
            skills=(0, 1),
            ages=(0, 0),
            active=(False, False),
        )
    elif mutation == "duplicate_a_state":
        mutated = list(panel) + [panel[-1]]
    elif mutation == "unreachable_age":
        mutated = list(panel)
        victim = next(i for i, s in enumerate(mutated) if s.check_index == 2 and tuple(s.ages) == (5, 10))
        mutated[victim] = gate.PanelState(
            signs=mutated[victim].signs,
            check_index=2,
            skills=mutated[victim].skills,
            # 40 is not in {5, 10}, the ages reachable at check 2.
            ages=(5, 40),
            active=(True, True),
        )
    else:  # pragma: no cover - parametrization guard
        raise AssertionError(mutation)

    with pytest.raises(gate.Vk0dGateError) as excinfo:
        gate.assert_panel_complete(mutated)
    assert expected_fragment in str(excinfo.value)


def test_reachable_ages_follow_the_frozen_ageing_rule():
    """A-VC-4: SET -> age 0 at the edit and K0 at the next check, KEEP ->
    age + K0. Written as literals from the rule, not recomputed from the code."""
    assert gate.reachable_active_ages(0) == ()
    assert gate.reachable_active_ages(1) == (5,)
    assert gate.reachable_active_ages(2) == (5, 10)
    assert gate.reachable_active_ages(7) == (5, 10, 15, 20, 25, 30, 35)
    assert len(gate.reachable_age_pairs(7)) == 49
    assert gate.reachable_age_pairs(2) == ((5, 5), (5, 10), (10, 5), (10, 10))


# ------------------------------------------------------------- swap(x) -------


def _synthetic_state(active=(True, True), skills=(0, 2), ages=(5, 20)):
    """One decision state whose every physical-agent-indexed component differs
    between the two agents, so no equality below can be satisfied by an
    accidentally symmetric fixture."""
    torch.manual_seed(4242)
    return {
        "joint_obs": torch.tensor([[0.9, -0.3, 0.4, 1.7], [-1.1, 0.6, -0.8, 0.2]]),
        "compact": torch.randn(1, 3),
        "team_vector": torch.randn(1, 3),
        "omega": torch.randn(1, 2),
        "agent_relevance": torch.tensor([[[0.2, -0.7], [1.3, 0.5]]]),
        "skills": tuple(skills),
        "ages": tuple(ages),
        "active": tuple(active),
    }


def _synthetic_agent(conjugate=True, seed=1234):
    """A `FixedClockAREditPolicy` matching `_synthetic_state`'s dimensions,
    wrapped so `enumerate_order` can reach it as `agent.high`.

    `keep_head` ships zero-initialized, which would make `keep_mass` an
    input-independent constant and leave half of every comparison trivially
    satisfied; perturbing it (the technique `tests/vk0c_token_mass_test.py`
    already uses) makes both the KEEP and the SET component discriminate.
    """
    import types

    torch.manual_seed(seed)
    policy = FixedClockAREditPolicy(
        obs_dim=4,
        n_agents=2,
        n_skills=4,
        hidden_dim=16,
        compact_dim=3,
        team_code_dim=3,
        omega_dim=2,
        agent_relevance_dim=2,
        conjugate_context=conjugate,
    )
    torch.manual_seed(77)
    torch.nn.init.normal_(policy.keep_head.weight, std=1.0)
    policy.eval()
    return types.SimpleNamespace(high=policy)


def _tensors_equal(a, b):
    if a is None or b is None:
        return a is None and b is None
    return a.dtype == b.dtype and a.shape == b.shape and a.detach().numpy().tobytes() == b.detach().numpy().tobytes()


def test_swap_state_is_a_byte_exact_involution():
    x = _synthetic_state()
    y = gate.swap_state(x)
    z = gate.swap_state(y)

    assert set(z) == set(x)
    for key in ("joint_obs", "compact", "team_vector", "omega", "agent_relevance"):
        assert _tensors_equal(z[key], x[key]), key
    for key in ("skills", "ages", "active"):
        assert z[key] == x[key], key

    # Fixture check: the single swap really moved the agent-indexed components,
    # so the involution above is not the trivial identity.
    assert not _tensors_equal(y["joint_obs"], x["joint_obs"])
    assert not _tensors_equal(y["agent_relevance"], x["agent_relevance"])
    assert y["skills"] == tuple(reversed(x["skills"]))
    assert y["ages"] == tuple(reversed(x["ages"]))
    # ...and left the anonymous global state alone.
    for key in ("compact", "team_vector", "omega"):
        assert _tensors_equal(y[key], x[key]), key


def test_swap_state_declares_every_agent_indexed_token_context_input():
    """`_token_context`'s agent-indexed inputs, enumerated from its body:
    `joint_obs[agent_id]`, `working_skills/_ages/_active[agent_id]` and
    `agent_relevance[:, agent_id, :]`. `compact`, `team_vector` and `omega`
    reach `_hidden` whole and carry no agent axis."""
    declared = {c["name"] for c in gate.SWAPPED_COMPONENTS}
    assert declared == {
        "joint_obs",
        "working_skills",
        "working_ages",
        "working_active",
        "agent_relevance",
    }
    assert {c["name"] for c in gate.UNSWAPPED_COMPONENTS} == {"compact", "team_vector", "omega"}
    assert all(c["agent_axis"] is None for c in gate.UNSWAPPED_COMPONENTS)


def test_full_swap_satisfies_conjugacy_on_the_asymmetric_synthetic_state():
    """Positive control for the coverage test below: with the complete swap the
    conjugate encoder agrees bit-exactly on a state that is asymmetric in every
    component."""
    agent = _synthetic_agent(conjugate=True)
    assert gate.check_state_conjugacy(agent, _synthetic_state(), "float32") is None
    assert gate.check_state_conjugacy(agent, _synthetic_state(active=(True, False)), "float32") is None


@pytest.mark.parametrize(
    "omitted,state_kwargs",
    [
        ("joint_obs", {}),
        ("skills", {}),
        ("ages", {}),
        ("agent_relevance", {}),
        ("active", {"active": (True, False)}),
    ],
)
def test_swap_state_covers_every_agent_indexed_component(omitted, state_kwargs):
    """Leave exactly one physical-agent-indexed component unswapped and require
    the conjugacy check to reject the result.

    Without this, a `swap_state` that quietly skipped a component would still
    report PASS -- certifying a weaker equality than A-VD-5's while reading as
    covered. The `active` case needs an asymmetric mask, which the frozen panel
    never carries, so it is supplied here.
    """
    agent = _synthetic_agent(conjugate=True)
    x = _synthetic_state(**state_kwargs)
    broken = dict(gate.swap_state(x))
    value = x[omitted]
    broken[omitted] = value.clone() if torch.is_tensor(value) else value

    record = gate.check_state_conjugacy(agent, x, "float32", swapped=broken)
    assert record is not None, f"leaving {omitted!r} unswapped must break conjugacy"
    assert record["reason"] == gate.REASON_CONJUGACY_BIT_EXACTNESS_FAILED
    assert record["disagreeing_outcomes"]


def test_absolute_encoder_fails_the_same_state_the_conjugate_encoder_passes():
    """Fixture check on the whole check: the equality above is enforced by the
    anonymous-OTHER encoder, not by the synthetic state already having it."""
    x = _synthetic_state()
    assert gate.check_state_conjugacy(_synthetic_agent(conjugate=True), x, "float32") is None
    record = gate.check_state_conjugacy(_synthetic_agent(conjugate=False), x, "float32")
    assert record is not None
    assert record["reason"] == gate.REASON_CONJUGACY_BIT_EXACTNESS_FAILED


# ------------------------------------------------- canonical accumulation ----


def test_conjugate_relabel_and_canonical_accumulation_are_order_free():
    """Predicted failure mode (b): comparing p-hat across orders under
    different accumulation orders. The relabel happens BEFORE normalization, so
    both sides run `math.fsum` over the identical sorted key sequence.

    The expected values here are literals, not a recomputation of
    `canonical_phat`'s own arithmetic."""
    masses = {(0, 1): 0.25, (1, 0): 0.5, (1, 1): 0.25}
    relabelled = gate.conjugate_relabel({(1, 0): 0.25, (0, 1): 0.5, (1, 1): 0.25})
    assert relabelled == masses

    canon = gate.canonical_phat(masses, "float32")
    assert canon["raw_joint_mass_sum"] == 1.0
    assert canon["within_tolerance"] is True
    assert canon["phat"] == {(0, 1): 0.25, (1, 0): 0.5, (1, 1): 0.25}
    assert canon["mass_tolerance"] == 32.0 * float(torch.finfo(torch.float32).eps)


def test_canonical_phat_rejects_a_mass_sum_outside_tolerance():
    """Planted violation: a mass vector that does not sum to one within
    32*eps(float32) must be flagged, not silently normalized away."""
    canon = gate.canonical_phat({(0, 0): 0.5, (1, 1): 0.25}, "float32")
    assert canon["within_tolerance"] is False
    assert math.isclose(canon["raw_joint_mass_sum"], 0.75)
    with pytest.raises(gate.Vk0dGateError):
        gate.canonical_phat({(0, 0): 0.0}, "float32")


# -------------------------------------------------------- the gate itself ----


BOUNDED_CHECKS = (0, 1, 2)


@pytest.fixture(scope="module")
def bounded_fresh_witness():
    return gate.run_gate(
        mode=gate.MODE_FRESH,
        config_module_name=CONJUGATE_CONFIG,
        training_seed=FRESH_SEED,
        check_indices=BOUNDED_CHECKS,
    )


def test_gate_passes_on_the_fresh_conjugate_config(bounded_fresh_witness):
    witness = bounded_fresh_witness
    assert witness["verdict"] == gate.VERDICT_PASS
    assert witness["controller"] == "r30_fixed_clock_ar_edit_conjugate"
    assert witness["pure_check"]["mismatches"] == []
    assert witness["executed_control"]["mismatches"] == []
    # 4 signs x (1 initial + 16 skill pairs x 1 age pair + 16 x 4 age pairs)
    assert witness["pure_check"]["states_checked"] == 4 * (1 + 16 + 64)
    assert witness["pure_check"]["states_checked"] == witness["panel"]["total_states"]
    # Executed control: 4 signs x 3 states x 16 legal joint assignments.
    assert witness["executed_control"]["states"] == 12
    assert witness["executed_control"]["assignments"] == 4 * 3 * 16


def test_gate_rejects_the_constructed_negative_witness():
    """A-VD-5's deliberate negative. The absolute-ID encoder is restored and its
    two identity blocks are made deterministically consequential by hand-setting
    the input-layer weight columns that read them; the gate must reject it, and
    the disagreement must be material rather than a rounding-scale artefact."""
    witness = gate.run_gate(
        mode=gate.MODE_NEGATIVE_WITNESS,
        check_indices=(0, 1),
        run_executed=False,
    )
    assert witness["verdict"] == gate.VERDICT_NEGATIVE_WITNESS_REJECTED
    assert witness["config_module"] == gate.NEGATIVE_WITNESS_CONFIG
    assert witness["controller"] == "r30_fixed_clock_ar_edit"
    mismatches = witness["pure_check"]["mismatches"]
    assert mismatches, "the constructed witness must be rejected"
    record = mismatches[0]
    assert record["reason"] == gate.REASON_CONJUGACY_BIT_EXACTNESS_FAILED
    assert record["disagreeing_outcomes"]

    gap = max(
        abs(record["p01"][key] - record["p10_conjugate"][key]) for key in record["p01"]
    )
    assert gap > 0.05, f"the identity blocks are not materially consequential: max gap {gap}"


def test_negative_witness_perturbation_is_deterministic_and_targets_the_identity_blocks():
    """The witness is a construction, not a lucky draw: two builds at the same
    seed are byte-identical, only the two absolute identity-slot column blocks
    differ from the unperturbed policy, and the two slots receive different
    constants (one shared constant would leave the slots interchangeable and the
    witness would stay green for the wrong reason)."""
    a = gate.build_negative_witness_agent(FRESH_SEED).high
    b = gate.build_negative_witness_agent(FRESH_SEED).high
    for key in a.state_dict():
        assert _tensors_equal(a.state_dict()[key], b.state_dict()[key]), key

    clean = vk0c.build_fresh_agent(gate.NEGATIVE_WITNESS_CONFIG, FRESH_SEED).high
    blocks = gate._identity_block_columns(a)
    assert len(blocks) == 2
    delta = (a.input[1].weight - clean.input[1].weight).detach()
    touched = torch.zeros(delta.shape[1], dtype=torch.bool)
    for slot, (lo, hi) in enumerate(blocks):
        touched[lo:hi] = True
        expected = float(gate.NEGATIVE_WITNESS_IDENTITY_SLOT_BIAS[slot])
        assert torch.equal(delta[:, lo:hi], torch.full_like(delta[:, lo:hi], expected))
    assert torch.equal(delta[:, ~touched], torch.zeros_like(delta[:, ~touched]))
    assert len(set(gate.NEGATIVE_WITNESS_IDENTITY_SLOT_BIAS)) == len(gate.NEGATIVE_WITNESS_IDENTITY_SLOT_BIAS)

    # Every other parameter is untouched.
    for key in clean.state_dict():
        if key == "input.1.weight":
            continue
        assert _tensors_equal(a.state_dict()[key], clean.state_dict()[key]), key


# -------------------------------------------------------------- witness ------


WITNESS_TOP_LEVEL_KEYS = {
    "gate_version",
    "mode",
    "config_module",
    "resolved_config_hash",
    "controller",
    "seed",
    "checkpoint_sha256",
    "panel",
    "swapped_components",
    "pure_check",
    "executed_control",
    "verdict",
    "torch_version",
    "dtype",
}


def test_witness_schema_is_stable(tmp_path, bounded_fresh_witness):
    out = tmp_path / "witness.json"
    gate.write_witness(out, bounded_fresh_witness)
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert set(payload) == WITNESS_TOP_LEVEL_KEYS
    assert payload["gate_version"] == "vk0d-conjugacy-1"
    assert payload["mode"] == gate.MODE_FRESH
    assert payload["config_module"] == CONJUGATE_CONFIG
    assert payload["seed"] == FRESH_SEED
    assert payload["checkpoint_sha256"] is None
    assert len(payload["resolved_config_hash"]) == 64
    assert set(payload["panel"]) == {
        "initial_states",
        "active_states",
        "age_pairs_per_check",
        "total_states",
        "orders",
    }
    assert set(payload["pure_check"]) == {"states_checked", "mismatches"}
    assert set(payload["executed_control"]) == {"states", "assignments", "mismatches"}
    assert payload["verdict"] in {
        gate.VERDICT_PASS,
        gate.VERDICT_FAIL,
        gate.VERDICT_NEGATIVE_WITNESS_REJECTED,
    }
    assert payload["dtype"] == "float32"
    assert payload["torch_version"] == str(torch.__version__)
    for component in payload["swapped_components"]:
        assert set(component) == {"name", "agent_axis", "swap", "token_context_use"}


def test_witness_is_write_once(tmp_path, bounded_fresh_witness):
    out = tmp_path / "witness.json"
    gate.write_witness(out, bounded_fresh_witness)
    with pytest.raises(gate.Vk0dGateError):
        gate.write_witness(out, bounded_fresh_witness)


def test_resolved_config_hash_separates_the_two_arms():
    """The witness's config identity must actually distinguish PRIMARY from the
    absolute-ID arm; an identity that collided would let a checkpoint recheck be
    filed under the wrong arm."""
    import importlib

    primary = gate._resolved_config_hash(CONJUGATE_CONFIG, importlib.import_module(CONJUGATE_CONFIG).Config())
    reference = gate._resolved_config_hash(
        gate.NEGATIVE_WITNESS_CONFIG, importlib.import_module(gate.NEGATIVE_WITNESS_CONFIG).Config()
    )
    assert primary != reference


def test_executed_control_subpanel_is_the_frozen_inventory():
    subpanel = gate.executed_control_subpanel()
    assert len(subpanel) == 4 * 8  # four sign pairs x (INITIAL + one per check 1..7)
    assert len({s.key() for s in subpanel}) == len(subpanel)
    for state in subpanel:
        if state.check_index == 0:
            assert tuple(state.active) == (False, False)
            continue
        assert tuple(state.skills) == (0, 1)
        assert tuple(state.ages) == (5, 5 * state.check_index)
        assert set(state.ages) <= set(gate.reachable_active_ages(state.check_index))
    assert {tuple(s.signs) for s in subpanel} == set(itertools.product((-1, 1), (-1, 1)))
