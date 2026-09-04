from __future__ import annotations

import math
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from experiments.candidates.variable_n_fleet_churn_r02.fixtures import (
    actual_path_fixture_plan,
    all_actual_path_fixture_plans,
    direct_fixture,
    expected_host_call_ledger,
    fresh_cell_identity,
    mapr_fixture,
    validate_host_call_ledger,
)
from experiments.candidates.variable_n_fleet_churn_r02.real_adapter import (
    AdapterError,
    R02ActualPathAdapter,
    load_committed_adapter,
    load_committed_components,
)
from experiments.candidates.variable_n_fleet_churn_r02.autodiff import ScalarTape
from experiments.candidates.variable_n_fleet_churn_r02.runner import (
    RunnerError,
    bind_exact_backward_capability,
    orchestrate_presentation_evaluations,
    run_with_components,
)
from experiments.candidates.variable_n_fleet_churn_r02 import artifact, panel
from experiments.candidates.variable_n_fleet_churn_r02.model import (
    PublicObservation,
    canonicalize,
    containment_predicates,
    exact_synthetic_step,
    forced_replay,
    forward,
    trace_fingerprint,
)


class MathKernel:
    def sigmoid_R02(self, value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    def exp_R02(self, value: float) -> float:
        return math.exp(value)

    def log_R02(self, value: float) -> float:
        return math.log(value)

    def sqrt_R02(self, value: float) -> float:
        return math.sqrt(value)


def _observation(reverse: bool = False) -> PublicObservation:
    handles = (11, 22)
    rows = ((0.0,) * 38, (0.0,) * 38)
    legal = ((True, False, False, False), (True, False, False, False))
    ranks = (2, 1)
    if reverse:
        handles = handles[::-1]
        rows = rows[::-1]
        legal = legal[::-1]
        ranks = ranks[::-1]
    return PublicObservation(
        handles, rows, ((0.0,) * 15, (0.0,) * 15), (0.0,) * 4,
        legal, ranks, (None, None, None, None),
    )


def test_canonicalizer_removes_external_presentation_before_numeric_use() -> None:
    left = canonicalize(_observation(False))
    right = canonicalize(_observation(True))
    assert left.canonical_bytes() == right.canonical_bytes()
    assert left.opaque_ranks == (1, 2)
    assert left.entity_handles == (22, 11)


def test_zero_residual_forward_containment_and_forced_replay_are_presentation_equal() -> None:
    kernel = MathKernel()
    mapr = mapr_fixture("F_ZERO_TIE_V1")
    direct = direct_fixture("F_ZERO_TIE_V1")
    canonical_mapr = forward(_observation(False), mapr, "MAPR", kernel)
    reverse_mapr = forward(_observation(True), mapr, "MAPR", kernel)
    canonical_direct = forward(_observation(False), direct, "DIRECT", kernel)
    reverse_direct = forward(_observation(True), direct, "DIRECT", kernel)
    assert trace_fingerprint(canonical_mapr) == trace_fingerprint(reverse_mapr)
    assert trace_fingerprint(canonical_direct) == trace_fingerprint(reverse_direct)
    assert all(containment_predicates(canonical_mapr, canonical_direct).values())
    left = forced_replay(
        _observation(False), mapr, "MAPR", kernel,
        physical_command=canonical_mapr.physical_command,
        old_logp=canonical_mapr.joint_log_probability,
    )
    right = forced_replay(
        _observation(True), mapr, "MAPR", kernel,
        physical_command=canonical_mapr.physical_command,
        old_logp=canonical_mapr.joint_log_probability,
    )
    assert left.total_loss.hex() == right.total_loss.hex()
    assert left.ratio.hex() == 1.0.hex()


def test_fixture_plan_and_host_ledger_are_exact_and_effect_free() -> None:
    plan = actual_path_fixture_plan(5, 2, "diagnostic_null_tie")
    assert plan.failed_entity == 5
    assert plan.demand_1[6] == plan.demand_2[6] == 1
    assert plan.blocked_1[6] == plan.blocked_2[6] == 0
    assert plan.native_batch_presentations == (
        "canonical", "canonical", "reverse", "reverse",
        "cyclic", "cyclic", "seed_fixed_random", "seed_fixed_random",
    )
    validate_host_call_ledger(expected_host_call_ledger())
    assert len(expected_host_call_ledger()) == 24
    identity = fresh_cell_identity(5, 2)
    presentations = dict(identity.presentations)
    assert tuple(presentations) == ("canonical", "reverse", "cyclic", "seed_fixed_random")
    assert presentations["reverse"] == tuple(reversed(presentations["canonical"]))
    assert presentations["cyclic"] == presentations["canonical"][1:] + presentations["canonical"][:1]
    assert len(set(presentations.values())) == 4


@dataclass(frozen=True)
class _Fixture:
    failed_zone: int
    agents: tuple[object, ...]
    demand_1: tuple[int, ...]
    demand_2: tuple[int, ...]
    blocked_1: tuple[int, ...]
    blocked_2: tuple[int, ...]
    commands: tuple[object, ...]
    presentations: tuple[tuple[int, ...], ...]


class _FakeNative:
    def __init__(self) -> None:
        self.last = ()

    @staticmethod
    def _row(fixture: _Fixture, later: bool = False):
        handles = fixture.presentations[0][:-1]
        return {
            "entity_handles": handles,
            "agents": tuple((0.0,) * 38 for _ in handles),
            "zones": ((0.0,) * 15, (0.0,) * 15),
            "global_row": (0.0,) * 4,
            "legal": tuple((True, False, False, False) for _ in handles),
            "fixed_occupant_rows": (None, None, None, None),
            "physical_token_states": (1 if later else 0, 0, 0, 0),
        }

    def reset(self, fixtures):
        self.last = tuple(fixtures)
        return tuple(self._row(row) for row in self.last)

    def bcrh(self, observations):
        return ((None, None, None, None),) * len(observations)

    def step(self, commands):
        return tuple(self._row(row, True) for row in self.last)


def test_injected_actual_adapter_enforces_six_width_eight_transactions_and_24_calls() -> None:
    native = _FakeNative()
    adapter = R02ActualPathAdapter(
        general_agent_state=lambda *args: tuple(args),
        episode_fixture=lambda *args: _Fixture(*args),
        native=native,
        observation_constructor=lambda row: row,
    )
    plans = all_actual_path_fixture_plans()
    for offset in range(0, len(plans), 3):
        cell = adapter.construct_cell(plans[offset:offset + 3])
        assert len(cell["t0"]) == len(cell["later_fixed_or_acquiring"]) == len(cell["diagnostic_null_tie"]) == 8
    assert len(adapter.require_complete_host_call_ledger()) == 24


def test_runner_refuses_before_calling_panel_without_exact_backward_capability() -> None:
    class Forbidden:
        capability = "not-frozen"

        def evaluate(self, request):
            raise AssertionError("runner reached evaluation despite missing capability")

    with pytest.raises(RunnerError, match="backward-order"):
        run_with_components(gate_receipt={"schema": "TEST"}, backward_engine=Forbidden(), panel_request={})


def test_fake_scalar_tape_bound_engine_exercises_all_292_independent_clones() -> None:
    class FakeIntegratedEvaluator:
        exact_backward_api = ScalarTape

        def __init__(self) -> None:
            self.seen = []

        def evaluate_clone(self, plan, prestate):
            assert prestate == {"comparison_key": plan.comparison_key, "step": 0}
            self.seen.append((plan.top_address, id(prestate)))
            base = plan.top_address.encode("ascii")
            import hashlib
            return {
                "replay_sha256": hashlib.sha256(base + b"/replay").hexdigest(),
                "raw_gradient_sha256": hashlib.sha256(base + b"/raw").hexdigest(),
                "clipped_gradient_sha256": hashlib.sha256(base + b"/clipped").hexdigest(),
                "optimizer_sha256": hashlib.sha256(base + b"/optimizer").hexdigest(),
                "node_table_sha256": hashlib.sha256(base + b"/nodes").hexdigest(),
            }

    plans = panel.evaluations()
    prestates = {key: {"comparison_key": key, "step": 0} for key in {row.comparison_key for row in plans}}
    evaluator = FakeIntegratedEvaluator()
    records = orchestrate_presentation_evaluations(prestates, bind_exact_backward_capability(evaluator))
    assert len(records) == len(evaluator.seen) == 292
    assert len({address for address, _ in evaluator.seen}) == 292
    artifact._validate_evaluations(list(records))
    for key, prestate in prestates.items():
        assert prestate == {"comparison_key": key, "step": 0}


def test_exact_dense_scalar_tape_step_preserves_presentation_and_zero_residual_base_gradients() -> None:
    kernel = MathKernel()
    handles = (1, 2, 3, 4)
    rows = tuple(tuple((row * 38 + column - 50) / 100 for column in range(38)) for row in range(4))
    legal = (
        (True, False, False, False),
        (False, False, False, False),
        (False, False, False, False),
        (False, False, False, False),
    )
    canonical = PublicObservation(handles, rows, ((0.0,) * 15, (0.0,) * 15), (0.0,) * 4, legal, (1, 2, 3, 4), (None, 2, 3, 4))
    reverse = PublicObservation(handles[::-1], rows[::-1], ((0.0,) * 15, (0.0,) * 15), (0.0,) * 4, legal[::-1], (4, 3, 2, 1), (None, 2, 3, 4))
    mapr = mapr_fixture("F_DYADIC_DENSE_V1")
    direct = direct_fixture("F_DYADIC_DENSE_V1")
    collection = forward(canonical, mapr, "MAPR", kernel)
    canonical_step = exact_synthetic_step(
        canonical, mapr, "MAPR", kernel,
        physical_command=collection.physical_command,
        old_logp=collection.joint_log_probability,
    )
    reverse_step = exact_synthetic_step(
        reverse, mapr, "MAPR", kernel,
        physical_command=collection.physical_command,
        old_logp=collection.joint_log_probability,
    )
    direct_step = exact_synthetic_step(
        canonical, direct, "DIRECT", kernel,
        physical_command=collection.physical_command,
        old_logp=collection.joint_log_probability,
    )
    assert canonical_step.replay.total_loss.hex() == reverse_step.replay.total_loss.hex() == direct_step.replay.total_loss.hex()
    assert canonical_step.raw_gradients == reverse_step.raw_gradients
    assert canonical_step.clipped_gradients == reverse_step.clipped_gradients
    assert canonical_step.updated_parameters == reverse_step.updated_parameters
    assert canonical_step.optimizer_state == reverse_step.optimizer_state
    assert canonical_step.raw_base_gradients == direct_step.raw_base_gradients
    assert any(
        value != 0.0
        for gradient in direct_step.raw_gradients
        if gradient.name.startswith("residual.out")
        for value in gradient.values
    )
    direct_base_parameters = tuple(
        (row.name[5:], row.shape, row.values)
        for row in direct_step.updated_parameters
        if row.name.startswith("base.")
    )
    mapr_parameters = tuple((row.name, row.shape, row.values) for row in canonical_step.updated_parameters)
    assert direct_base_parameters == mapr_parameters
    assert canonical_step.optimizer_state.step == reverse_step.optimizer_state.step == direct_step.optimizer_state.step == 1


def test_committed_component_binding_is_lazy_exact_and_rejects_missing_callable() -> None:
    requested = []

    def importer(name):
        requested.append(name)
        if name.endswith("fixtures"):
            return SimpleNamespace(GeneralAgentState=lambda *args: args, EpisodeFixture=lambda *args: args)
        if name.endswith("native_backend"):
            return SimpleNamespace(NativeInteractiveBatch=lambda rows: rows)
        return SimpleNamespace(_model_inputs=lambda trace, fixture, failed: ())

    components = load_committed_components(importer)
    assert callable(components.general_agent_state)
    assert requested == [
        "experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures",
        "experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend",
        "experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_training",
    ]

    def missing(name):
        return SimpleNamespace()

    with pytest.raises(AdapterError, match="callable"):
        load_committed_components(missing)


def test_lazy_committed_bridge_maps_exact_interactive_api_without_native_execution() -> None:
    class FakeCommittedBatch:
        instances = []

        def __init__(self, fixtures):
            self.fixtures = tuple(fixtures)
            self.closed = False
            self.initial = tuple({
                "failed_rank": fixture.post_presentations[0][-1],
                "next_observation": {"epoch": 0, "token_state": (0, 0, 0, 0)},
            } for fixture in self.fixtures)
            self.__class__.instances.append(self)

        def bcrh(self, include_candidate_records=False):
            assert include_candidate_records is False
            return tuple({
                "scorer_command": (None, None, None, None),
                "scorer_checker_equal": True,
                "independent_enumerator_equal": True,
            } for _ in self.fixtures)

        def step(self, commands):
            assert len(tuple(commands)) == 8
            return tuple({"next_observation": {"epoch": 1, "token_state": (1, 0, 0, 0)}} for _ in self.fixtures)

        def close(self):
            self.closed = True

    def model_inputs(trace, fixture, failed):
        active = tuple(rank for rank in fixture.post_presentations[int(trace["epoch"])] if rank != failed)
        n = len(active)
        return (
            [[list((0.0,) * 38) for _ in range(n)]],
            [[list((0.0,) * 15), list((0.0,) * 15)]],
            [[0.0, 0.0, 0.0, 0.0]],
            [[[1.0, 0.0, 0.0, 0.0] for _ in range(n)]],
            [[-1, -1, -1, -1]],
            [[index + 1 for index in range(n)]],
        )

    modules = {
        "experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures": SimpleNamespace(
            GeneralAgentState=lambda *args: tuple(args),
            EpisodeFixture=lambda *args: SimpleNamespace(
                failed_zone=args[0], agents=args[1], demand_1=args[2], demand_2=args[3],
                blocked_1=args[4], blocked_2=args[5], post_commands=args[6], post_presentations=args[7],
            ),
        ),
        "experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend": SimpleNamespace(
            NativeInteractiveBatch=FakeCommittedBatch,
        ),
        "experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_training": SimpleNamespace(
            _model_inputs=model_inputs,
        ),
    }
    adapter = load_committed_adapter(modules.__getitem__)
    plans = all_actual_path_fixture_plans()[:3]
    cell = adapter.construct_cell(plans)
    assert len(cell["t0"]) == len(cell["later_fixed_or_acquiring"]) == len(cell["diagnostic_null_tie"]) == 8
    assert len(FakeCommittedBatch.instances) == 2
    assert FakeCommittedBatch.instances[0].closed is True
    adapter.close()
    assert FakeCommittedBatch.instances[1].closed is True
