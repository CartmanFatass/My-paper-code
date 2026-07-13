from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import torch

import ha_ctse_process.r27_g2_collector as collector
import ha_ctse_process.r27_g2_runtime as runtime
from ha_ctse_process.r27_g2_collector import (
    ACTION_DIM,
    BRANCH_COUNT,
    BRANCH_STEPS,
    DIAGNOSTIC_SLOT_COUNT,
    R27G2ResetArtifact,
    build_branch_specs,
    build_diagnostic_slots,
    prefix_policy_seed_for_reset,
    prefix_steps_for_reset,
    validate_agent_source_contract,
)
from ha_ctse_process.r27_g2_runtime import R27G2ContractError
from ha_ctse_process.standalone_agent import (
    StandaloneProcessAgent,
    StrictHMASDMAPPOLowLevelPolicy,
)


def test_prefix_allocation_and_exact_environment_step_budget():
    prefixes = [prefix_steps_for_reset(reset_id) for reset_id in range(64)]

    assert prefixes.count(50) == 22
    assert prefixes.count(150) == 21
    assert prefixes.count(250) == 21
    assert sum(prefixes) == 9500
    assert sum(prefix + 55 * (prefix + 50) for prefix in prefixes) == 708000
    assert [prefix_policy_seed_for_reset(i) for i in (0, 7, 63)] == [
        27100,
        27107,
        27163,
    ]


def test_branch_and_diagnostic_slot_matrices_are_exact():
    roster = np.array([0, 1, 2, 3, 0, 1], dtype=np.int64)
    branches = build_branch_specs(roster)
    branch_ids, agent_ids = build_diagnostic_slots(branches)

    assert len(branches) == BRANCH_COUNT
    assert sum(item.kind == "reference" for item in branches) == 1
    assert sum(item.kind == "hold" for item in branches) == 24
    assert sum(item.kind == "pulse" for item in branches) == 18
    assert sum(item.kind == "inactive" for item in branches) == 12
    assert all(
        item.target_skill != item.natural_skill
        for item in branches
        if item.kind == "pulse"
    )
    assert branch_ids.shape == (DIAGNOSTIC_SLOT_COUNT,)
    assert agent_ids.shape == (DIAGNOSTIC_SLOT_COUNT,)
    assert np.sum(branch_ids == 0) == 6
    assert set(agent_ids[branch_ids == 0]) == set(range(6))
    pulse = next(item for item in branches if item.kind == "pulse")
    assert pulse.executed_skill(9) == pulse.target_skill
    assert pulse.executed_skill(10) == pulse.natural_skill


def make_artifact() -> R27G2ResetArtifact:
    roster = np.array([0, 1, 2, 3, 0, 1], dtype=np.int64)
    branches = build_branch_specs(roster)
    artifact = R27G2ResetArtifact.allocate(
        reset_id=0,
        prefix_steps=50,
        obs_dim=9,
        hidden_dim=5,
        state_dim=13,
        branches=branches,
    )
    artifact.prefix_skill[:] = roster
    artifact.calibration_action[:] = np.tanh(
        artifact.prefix_pre_tanh_mean[-50:]
    ).astype(np.float32)
    return artifact


def test_reset_artifact_roundtrip_is_typed_and_pickle_free(tmp_path):
    expected = make_artifact()
    path = expected.write(tmp_path / "reset_0000.npz")
    actual = R27G2ResetArtifact.read(path)

    assert actual.step_valid.shape == (BRANCH_COUNT, BRANCH_STEPS)
    assert actual.diagnostic_active_new_hidden.shape == (
        DIAGNOSTIC_SLOT_COUNT,
        BRANCH_STEPS,
        4,
        5,
    )
    for name in expected.__dataclass_fields__:
        np.testing.assert_array_equal(getattr(actual, name), getattr(expected, name))
        assert np.asarray(getattr(actual, name)).dtype != object


def test_reset_artifact_rejects_nonfinite_and_branch_reordering():
    nonfinite = make_artifact()
    nonfinite.local_observation[0, 0, 0, 0] = np.nan
    with pytest.raises(R27G2ContractError, match="non-finite"):
        nonfinite.validate()

    reordered = make_artifact()
    reordered.branch_target_skill[[1, 2]] = reordered.branch_target_skill[[2, 1]]
    with pytest.raises(R27G2ContractError, match="branch ordering"):
        reordered.validate()


def test_source_contract_rejects_wrong_duration_family():
    actor = SimpleNamespace(
        actor_team_film=None,
        actor_act=SimpleNamespace(
            action_out=type("TanhDiagGaussian", (), {})()
        ),
    )
    agent = SimpleNamespace(
        n_agents=6,
        n_skills=4,
        action_dim=ACTION_DIM,
        num_envs=1,
        action_space_type="continuous",
        use_recurrent_low_level=True,
        low=actor,
        duration_candidates=(3, 7, 13, 24),
    )
    with pytest.raises(R27G2ContractError, match="source contract"):
        validate_agent_source_contract(agent)


class FakeScenario:
    def __init__(self):
        self.np_random = np.random.RandomState(0)
        self.counter = 0
        self.observation = np.zeros((6, 4), dtype=np.float32)
        self.state = np.zeros(5, dtype=np.float32)
        self.last_action = np.zeros((6, 4), dtype=np.float32)


class FakeAdapter:
    def __init__(self):
        self.env = FakeScenario()
        self.np_random = np.random.default_rng(0)
        self.closed = False

    def _info(self):
        return {
            "state": self.env.state.copy(),
            "uav_failed": np.zeros(6, dtype=np.bool_),
            "counter": int(self.env.counter),
        }

    def reset(self, *, seed):
        self.env.np_random = np.random.RandomState(int(seed))
        self.np_random = np.random.default_rng(int(seed) + 1000)
        self.env.counter = 0
        self.env.observation.fill(0.0)
        self.env.state.fill(0.0)
        self.env.last_action.fill(0.0)
        self.closed = False
        return self.env.observation.copy(), self._info()

    def step(self, action):
        value = np.asarray(action, dtype=np.float32)
        assert value.shape == (6, 4)
        self.env.np_random.random_sample()
        self.np_random.random()
        self.env.counter += 1
        self.env.last_action = value.copy()
        self.env.observation = (
            self.env.observation + 0.01 * value
        ).astype(np.float32)
        self.env.state = (
            self.env.state
            + np.array(
                [value.mean(), value.std(), value.min(), value.max(), 0.01],
                dtype=np.float32,
            )
        ).astype(np.float32)
        return self.env.observation.copy(), 0.0, False, False, self._info()

    def close(self):
        self.closed = True


class FakeAgent:
    def __init__(self):
        torch.manual_seed(27190)
        self.device = torch.device("cpu")
        self.num_envs = 1
        self.n_agents = 6
        self.n_skills = 4
        self.action_dim = 4
        self.obs_dim = 4
        self.state_dim = 5
        self.action_space_type = "continuous"
        self.use_recurrent_low_level = True
        self.team_intent_k = 8
        self.duration_candidates = (1, 2, 3, 4)
        self.low = StrictHMASDMAPPOLowLevelPolicy(
            obs_dim=4,
            state_dim=5,
            n_skills=4,
            num_team_codes=2,
            action_dim=4,
            hidden_dim=4,
            action_space_type="continuous",
            continuous_action_distribution="tanh_gaussian",
            actor_condition_on_team_code=False,
            device="cpu",
        ).eval()
        self.low_value_norm = None
        self.high_value_norm = None
        self._initialize_runtime()

    def _initialize_runtime(self):
        self.active_skills = np.array([[0, 1, 2, 3, 0, 1]], dtype=np.int64)
        self.active_duration_indices = np.zeros((1, 6), dtype=np.int64)
        self.duration_remaining = np.full((1, 6), 10, dtype=np.int64)
        self.skill_age = np.zeros((1, 6), dtype=np.int64)
        self.has_active_skill = np.ones((1, 6), dtype=np.bool_)
        self.active_team_codes = np.array([1], dtype=np.int64)
        self.team_intent_remaining = np.array([80], dtype=np.int64)
        self.team_intent_age = np.array([0], dtype=np.int64)
        self.low_actor_hxs = np.zeros((1, 6, 4), dtype=np.float32)
        self.low_critic_hxs = np.zeros((1, 6, 4), dtype=np.float32)
        self._last_low_context = [None]
        self.segments = SimpleNamespace(active=[[None for _ in range(6)]])
        self.situation_debouncer = {"stable": 0}
        self.per_agent_situation_debouncer = {"stable": [0] * 6}
        self.situation_hazard_guard = {"events": []}
        self._last_situation_state = [None]
        self._last_agent_situation_state = [[None for _ in range(6)]]
        self._team_transition_open = [None]
        self._team_transition_closed = []
        self._team_transition_env_steps = [0]
        self._team_intent_boundary_count = 0
        self._team_intent_boundary_trunc_fracs = []
        self._team_intent_boundary_trunc_by_duration = {}
        self._team_intent_dwell_checks = []
        self._team_intent_age_check_samples = []
        self._situation_diag_events = []
        self._agent_situation_diag_events = []
        self._situation_hazard_forced_renewals = 0
        self._situation_hazard_events = 0

    def reset_env_state(self, env_id):
        assert env_id == 0
        self._initialize_runtime()

    def maybe_assign_skills(self, *_args, **_kwargs):
        return None

    def act_low(self, obs, *, env_id, deterministic, state):
        context = {
            "state": np.asarray(state, dtype=np.float32).copy(),
            "team_code": int(self.active_team_codes[env_id]),
            "actor_hxs": self.low_actor_hxs[env_id].copy(),
            "critic_hxs": self.low_critic_hxs[env_id].copy(),
        }
        obs_t = torch.as_tensor(obs, dtype=torch.float32)
        skills = torch.as_tensor(self.active_skills[env_id], dtype=torch.long)
        state_t = torch.as_tensor(state, dtype=torch.float32).reshape(1, -1).expand(6, -1)
        team = torch.full((6,), int(self.active_team_codes[env_id]), dtype=torch.long)
        with torch.no_grad():
            action, logp, _, value, actor_h, critic_h = self.low.act(
                obs_t,
                skills,
                torch.as_tensor(self.low_actor_hxs[env_id]),
                state_t,
                team,
                torch.as_tensor(self.low_critic_hxs[env_id]),
                deterministic=deterministic,
            )
        self.low_actor_hxs[env_id] = actor_h.numpy().astype(np.float32)
        self.low_critic_hxs[env_id] = critic_h.numpy().astype(np.float32)
        self._last_low_context[env_id] = context
        return (
            action.numpy().astype(np.float32),
            logp.numpy().astype(np.float32),
            value.numpy().astype(np.float32),
        )

    def r27_g2_audit_step(self, *args, **kwargs):
        return StandaloneProcessAgent.r27_g2_audit_step(self, *args, **kwargs)


def test_metric_state_and_nested_failure_checks_fail_closed():
    with pytest.raises(runtime.R27G2ContractError, match="non-finite"):
        collector._assert_finite_evidence(
            {"reward_components": {"coverage": np.asarray([np.nan])}},
            "fixture.info",
        )
    assert collector._focal_failed(
        {"state_info": {"uav_failed": [False, True, False]}}, 1
    )
    assert collector._focal_failed(
        {"state_info": {"uav_failed": [False, True, False]}}, -1
    )
    with pytest.raises(runtime.R27G2ContractError, match="did not expose global state"):
        collector._state_from_info({})


def test_registered_source_contract_rejects_cpu_runtime():
    with pytest.raises(runtime.R27G2ContractError, match="cuda_device"):
        collector.validate_agent_source_contract(FakeAgent())


def test_artifact_validation_rejects_failed_direct_restoration_evidence():
    roster = np.asarray([0, 1, 2, 3, 0, 1], dtype=np.int64)
    artifact = R27G2ResetArtifact.allocate(
        reset_id=0,
        prefix_steps=50,
        obs_dim=4,
        hidden_dim=4,
        state_dim=5,
        branches=build_branch_specs(roster),
    )
    artifact.prefix_skill[:] = roster
    artifact.branch_completed[0] = True
    artifact.step_valid[0] = True
    artifact.executed_focal_skill[0] = 0
    artifact.replay_global_rng_equal[0] = True
    artifact.replay_info_equal[0] = True
    artifact.replay_environment_equal[0] = True
    artifact.replay_environment_rng_equal[0] = True
    artifact.module_state_equal[...] = True
    artifact.value_norm_state_equal[...] = True
    artifact.frozen_runtime_unchanged[0] = True

    with pytest.raises(runtime.R27G2ContractError, match="restored-runtime"):
        artifact.validate()

    artifact.runtime_restored_equal[0] = True
    with pytest.raises(runtime.R27G2ContractError, match="global-RNG preservation"):
        artifact.validate()


def make_completed_artifact() -> R27G2ResetArtifact:
    artifact = make_artifact()
    branches = build_branch_specs(artifact.prefix_skill[-1])
    artifact.branch_completed[:] = True
    artifact.step_valid[:] = True
    artifact.runtime_restored_equal[:] = True
    artifact.replay_global_rng_equal[:] = True
    artifact.replay_info_equal[:] = True
    artifact.replay_environment_equal[:] = True
    artifact.replay_environment_rng_equal[:] = True
    artifact.frozen_runtime_unchanged[:] = True
    artifact.environment_rng_equal_reference[:] = True
    artifact.identity_actor_equal[:] = True
    artifact.identity_critic_equal[:] = True
    artifact.identity_info_equal[:] = True
    artifact.identity_environment_equal[:] = True
    artifact.module_state_equal[...] = True
    artifact.value_norm_state_equal[...] = True
    artifact.global_rng_unchanged[:] = True
    for branch_id, branch in enumerate(branches):
        focal_agent = 0 if branch.kind == "reference" else branch.focal_agent
        for step in range(BRANCH_STEPS):
            artifact.executed_focal_skill[branch_id, step] = (
                int(artifact.prefix_skill[-1, focal_agent])
                if branch.kind == "reference"
                else branch.executed_skill(step)
            )
    artifact.validate()
    return artifact


def test_completed_artifact_enforces_matched_rng_through_exact_h40():
    artifact = make_completed_artifact()
    branch_id = int(np.flatnonzero(artifact.branch_kind == "pulse")[0])
    artifact.environment_rng_equal_reference[branch_id, 41] = False
    artifact.validate()

    artifact.environment_rng_equal_reference[branch_id, 40] = False
    with pytest.raises(runtime.R27G2ContractError, match="RNG differs through H40"):
        artifact.validate()


@pytest.mark.parametrize(
    ("field_name", "message"),
    [
        ("identity_actor_equal", "actor"),
        ("identity_critic_equal", "critic"),
        ("identity_info_equal", "info"),
        ("identity_environment_equal", "environment"),
    ],
)
def test_completed_artifact_enforces_every_identity_equality(field_name, message):
    artifact = make_completed_artifact()
    same_label = np.flatnonzero(
        (artifact.branch_kind == "hold")
        & (artifact.branch_target_skill == artifact.branch_natural_skill)
    )
    branch_id = int(same_label[0])
    getattr(artifact, field_name)[branch_id, -1] = False
    with pytest.raises(
        runtime.R27G2ContractError,
        match=f"identity branch differs: {message}",
    ):
        artifact.validate()


def test_full_fake_reset_collection_executes_exact_matrix_without_rng_leak(
    monkeypatch, tmp_path
):
    runtime_capture_count = 0
    capture_runtime_snapshot = runtime.capture_runtime_snapshot

    def counted_runtime_snapshot(agent):
        nonlocal runtime_capture_count
        runtime_capture_count += 1
        return capture_runtime_snapshot(agent)

    monkeypatch.setattr(
        collector,
        "capture_global_rng_state",
        lambda: runtime.capture_global_rng_state(
            require_cuda=False, include_cuda=False
        ),
    )
    monkeypatch.setattr(collector, "validate_agent_source_contract", lambda _agent: None)
    monkeypatch.setattr(
        collector, "capture_runtime_snapshot", counted_runtime_snapshot
    )
    monkeypatch.setattr(
        runtime, "capture_runtime_snapshot", counted_runtime_snapshot
    )
    checkpoint = tmp_path / "fixture.pt"
    checkpoint.write_bytes(b"r27-g2-fixture")
    agent = FakeAgent()
    result = collector.collect_reset_evidence(
        env_factory=FakeAdapter,
        agent=agent,
        reset_id=0,
        checkpoint_id="fixture",
        checkpoint_update=32,
        checkpoint_path=checkpoint,
    )

    assert result.manifest["status"] == "OK"
    assert result.manifest["environment_steps"] == 5550
    assert result.artifact.branch_completed.all()
    assert result.artifact.step_valid.all()
    assert result.artifact.global_rng_unchanged.all()
    assert result.artifact.runtime_restored_equal.all()
    assert result.artifact.replay_global_rng_equal.all()
    assert result.artifact.replay_info_equal.all()
    assert result.artifact.replay_environment_equal.all()
    assert result.artifact.replay_environment_rng_equal.all()
    assert result.artifact.module_state_equal.all()
    assert result.artifact.value_norm_state_equal.all()
    assert result.artifact.frozen_runtime_unchanged.all()
    assert result.artifact.environment_rng_equal_reference.all()
    identity = np.asarray(
        [branch.is_identity_branch for branch in build_branch_specs(result.artifact.prefix_skill[-1])]
    )
    assert result.artifact.identity_actor_equal[identity].all()
    assert result.artifact.identity_critic_equal[identity].all()
    assert result.artifact.identity_info_equal[identity].all()
    assert result.artifact.identity_environment_equal[identity].all()
    assert float(result.artifact.reference_act_low_parity_abs_error.max()) <= 1e-6
    assert float(result.artifact.live_diagnostic_abs_error.max()) <= 1e-6
    assert runtime_capture_count == 256
