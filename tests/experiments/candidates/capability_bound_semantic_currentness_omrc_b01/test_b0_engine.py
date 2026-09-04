from __future__ import annotations

from dataclasses import replace
import inspect

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b0 import (
    B0_SEED,
    B0ContractError,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import (
    Action,
    EPISODE_TRANSITIONS,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.engine import (
    _ADAPTERS,
    assert_unchanged_state,
    b0_engine,
    build_observations,
    decision_action_traces,
    reward_row_evidence,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import DynamicHost


def test_observation_projection_is_firewalled_from_private_truth() -> None:
    tape = DynamicHost(addressing.B0_RUN, B0_SEED).build_stochastic(addressing.TRAIN, 0)
    poisoned = replace(tape, _decision_truth=tuple(object() for _ in range(24)))
    for factory in _ADAPTERS.values():
        expected, expected_work = build_observations(tape, factory)
        observed, observed_work = build_observations(poisoned, factory)
        assert torch.equal(observed, expected)
        assert observed_work == expected_work


def test_raw_training_action_trace_keeps_every_identity_and_24_action_names() -> None:
    host = DynamicHost(addressing.B0_RUN, B0_SEED)
    tapes = tuple(host.build_stochastic(addressing.TRAIN, episode_id) for episode_id in (0, 1))
    actions = torch.full((2, EPISODE_TRANSITIONS), int(Action.WAIT), dtype=torch.int64)
    expected = []
    legal = (Action.SERVE, Action.REFRESH, Action.SAFE_FALLBACK)
    for episode_index in range(2):
        names = []
        for opportunity in range(24):
            action = legal[(episode_index + opportunity) % len(legal)]
            actions[episode_index, 12 + 6 * opportunity] = int(action)
            names.append(action.name)
        expected.append(names)

    traces = decision_action_traces(tapes, actions)
    assert [trace["identity"]["episode_id"] for trace in traces] == [0, 1]
    assert [trace["identity"]["split"] for trace in traces] == [addressing.TRAIN] * 2
    assert [trace["decision_actions"] for trace in traces] == expected
    assert all(len(trace["decision_actions"]) == 24 for trace in traces)


def test_reward_evidence_exposes_only_observed_rows_for_independent_audit() -> None:
    tape = DynamicHost(addressing.B0_RUN, B0_SEED).build_stochastic(addressing.TRAIN, 0)
    rewards = torch.zeros((1, EPISODE_TRANSITIONS), dtype=torch.float32)
    rewards[0, 12] = -0.4
    rewards[0, 13] = 1.0
    evidence = reward_row_evidence((tape,), rewards)
    assert evidence[0]["decision_rewards"][0] == pytest.approx(-0.4)
    assert evidence[0]["settlement_rewards"][0] == 1.0
    assert evidence[0]["nonzero_outside_ledger_rows"] == []
    assert len(evidence[0]["decision_rewards"]) == 24
    assert len(evidence[0]["settlement_rewards"]) == 24

    rewards[0, 0] = 0.25
    contaminated = reward_row_evidence((tape,), rewards)
    assert contaminated[0]["nonzero_outside_ledger_rows"] == [0]


def test_heldout_state_guard_compares_raw_before_after_observations() -> None:
    assert_unchanged_state("model-before", "model-before", label="model")
    with pytest.raises(B0ContractError, match="changed model state"):
        assert_unchanged_state("model-before", "model-after", label="model")


def test_engine_has_no_online_q_or_replay_dependency_and_declares_complete_surface() -> None:
    import experiments.candidates.capability_bound_semantic_currentness.omrc_b01.engine as module

    source = inspect.getsource(module)
    assert "RecurrentQLearner" not in source
    assert "BoundedReplay" not in source
    assert "OnlineQTrainer" not in source
    assert ".online" not in source
    assert '"audits": {' not in source
    assert '"complete": True' not in source
    assert "validate_arm_result" not in source
    for raw_field in (
        '"training_actions"',
        '"evaluation_actions"',
        '"adapter_work_receipt"',
        '"heldout_state_observations"',
    ):
        assert raw_field in source
    declared = set(b0_engine().source_paths)
    for required in (
        "engine.py",
        "evaluator.py",
        "host.py",
        "model.py",
        "ppo.py",
        "checkpoint.py",
        "CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md",
        "run_cbsc_omrc_b01.py",
    ):
        assert any(path.endswith(required) for path in declared)
