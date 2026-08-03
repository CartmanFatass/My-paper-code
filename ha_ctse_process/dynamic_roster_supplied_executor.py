"""Clean-process F1 high path with a parameterless supplied executor.

The high event policy and critic are the existing variable-roster F1 graph.
Skill IDs are executed literally as the primitive IDLE/PERSIST/SHORT actions;
there is no low-policy likelihood, replay, optimizer, update, or gradient path.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import io
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process.collectors import SyncEnvCollector
from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    CleanProcessDynamicRosterEventEnv,
    audit_clean_process_contract,
)
from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    HORIZON,
    IDLE,
    OBSERVATION_DIM,
    PERSIST,
    SHORT,
    constructive_actions,
)
from ha_ctse_process.variable_roster_event import (
    ACTIVE,
    EVENT_ARCHITECTURE_SCHEMA_VERSION,
    JOIN,
    OPPORTUNITY_GAP_HIGH,
    OPPORTUNITY_GAP_LOW,
    REJOIN,
    SUPPLIED_EXECUTOR_RUNTIME,
    TEMPORARILY_ABSENT,
    TEMPORARY_LEAVE,
    TERMINAL,
    TERMINAL_LEAVE,
    VariableRosterEventCore,
    apply_event_high_ppo_update,
    event_high_ppo_losses_from_packed,
    pack_event_high_ppo_data,
)
from ha_ctse_process.variable_roster_event_types import (
    EventTransactionResult,
    MembershipTransaction,
    PackedEventHighPPOData,
)


PACKAGE_NAME = "clean_supplied_executor_high_path_g0"
PACKAGE_SCHEMA_VERSION = 1
HIGH_CHECKPOINT_SCHEMA_VERSION = 1

LEARNED_HIGH_ARM = "learned_high"
FROZEN_HIGH_ARM = "frozen_high"
ORACLE_ARM = "routing_oracle"
ARMS = (LEARNED_HIGH_ARM, FROZEN_HIGH_ARM, ORACLE_ARM)

FORMAL_NUM_ENVS = 16
FORMAL_HORIZON = HORIZON
FORMAL_UPDATES = 250
PPO_PASSES_PER_UPDATE = 4
FORMAL_TRANSITIONS = FORMAL_NUM_ENVS * FORMAL_HORIZON * FORMAL_UPDATES
FORMAL_HIGH_OPTIMIZER_STEPS = FORMAL_UPDATES * PPO_PASSES_PER_UPDATE
FORMAL_EVAL_EPISODES = 256
BOOTSTRAP_REPETITIONS = 10_000

MODEL_SEED = 57_057
TRAIN_TASK_SEED = 67_057
OPPORTUNITY_FRONTIER_SEED = 77_057
ACTION_SEED = 87_057
EVALUATION_TASK_SEED = 97_057
BOOTSTRAP_SEED = 107_057
OPPORTUNITY_STREAM_ID = 0
FRONTIER_STREAM_ID = 1
ACTION_STREAM_ID = 0
HIGH_LEARNING_RATE = 3.0e-4
HIGH_ADAM_BETAS = (0.9, 0.999)
HIGH_ADAM_EPS = 1.0e-8
HIGH_ADAM_WEIGHT_DECAY = 0.0

SEED_CONTRACT = {
    "model": MODEL_SEED,
    "training_task": TRAIN_TASK_SEED,
    "opportunity_frontier": OPPORTUNITY_FRONTIER_SEED,
    "opportunity_stream": OPPORTUNITY_STREAM_ID,
    "frontier_stream": FRONTIER_STREAM_ID,
    "action": ACTION_SEED,
    "action_stream": ACTION_STREAM_ID,
    "evaluation_task": EVALUATION_TASK_SEED,
    "bootstrap": BOOTSTRAP_SEED,
}

HIGH_COUNTER_FIELDS = {
    "update_index",
    "step_in_update",
    "ppo_passes_in_update",
    "environment_transitions",
    "high_optimizer_steps",
    "next_episode_id",
    "episodes_completed",
}

CORE_RUNTIME_FIELDS = {
    "environment_index",
    "architecture_state",
    "runtime_mode",
    "rng_ledger",
    "lifecycle_records",
    "opportunity_rng_state",
    "frontier_rng_state",
    "action_rng_state",
    "high_ledger",
    "closed_event_rows",
    "policy_version",
    "physical_time",
    "current_observation_state_boundary",
    "pending_membership_transaction",
    "low_path_state",
}

CHECKPOINT_FIELDS = {
    "checkpoint_schema_version",
    "package",
    "package_schema_version",
    "arm",
    "runtime_mode",
    "architecture_mode",
    "event_architecture_schema_version",
    "shape_contract",
    "seed_contract",
    "model_state",
    "optimizer_state",
    "runtime_cores",
    "collector_snapshot",
    "current_transactions",
    "runtime_diagnostics",
    "counters",
    "torch_rng_state",
}


class SuppliedSkillExecutor:
    """Pure identity execution of skill IDs 0/1/2 as primitive actions."""

    support = (IDLE, PERSIST, SHORT)

    @staticmethod
    def parameter_count() -> int:
        return 0

    def parameters(self):
        return iter(())

    def execute(self, active_skills: Mapping[str, int]) -> dict[str, int]:
        if not isinstance(active_skills, Mapping):
            raise TypeError("supplied executor requires an active-skill mapping")
        actions: dict[str, int] = {}
        for raw_key, raw_skill in active_skills.items():
            key = str(raw_key)
            if not key:
                raise ValueError("supplied executor received an empty lifecycle key")
            if key in actions:
                raise ValueError("supplied executor received duplicate lifecycle keys")
            if isinstance(raw_skill, (bool, np.bool_)):
                raise ValueError("supplied executor skill IDs must be integers")
            skill = int(raw_skill)
            if skill != raw_skill or skill not in self.support:
                raise ValueError("supplied executor skill lies outside {0,1,2}")
            actions[key] = skill
        return actions

    def __call__(self, active_skills: Mapping[str, int]) -> dict[str, int]:
        return self.execute(active_skills)


def _fork_devices(device: torch.device) -> list[int]:
    if device.type != "cuda":
        return []
    return [torch.cuda.current_device() if device.index is None else int(device.index)]


def make_model_owner(device: str | torch.device) -> VariableRosterEventCore:
    """Create the sole learned graph without perturbing caller Torch RNG state."""

    selected = torch.device(device)
    with torch.random.fork_rng(devices=_fork_devices(selected)):
        torch.manual_seed(MODEL_SEED)
        if selected.type == "cuda":
            torch.cuda.manual_seed_all(MODEL_SEED)
        return VariableRosterEventCore(
            architecture_mode="f1",
            runtime_mode=SUPPLIED_EXECUTOR_RUNTIME,
            obs_dim=OBSERVATION_DIM,
            critic_member_dim=OBSERVATION_DIM,
            critic_global_dim=8,
            n_skills=ACTION_COUNT,
            action_dim=ACTION_COUNT,
            environment_index=0,
            opportunity_seed=OPPORTUNITY_FRONTIER_SEED,
            frontier_seed=OPPORTUNITY_FRONTIER_SEED,
            action_seed=ACTION_SEED,
            rng_episode_id=0,
            opportunity_stream_id=OPPORTUNITY_STREAM_ID,
            frontier_stream_id=FRONTIER_STREAM_ID,
            action_stream_id=ACTION_STREAM_ID,
            device=selected,
        )


def high_parameters(core: VariableRosterEventCore) -> tuple[torch.nn.Parameter, ...]:
    return tuple(core.commitment_model.parameters()) + tuple(
        core.event_critic.parameters()
    )


def make_high_optimizer(core: VariableRosterEventCore) -> torch.optim.Adam:
    return torch.optim.Adam(
        high_parameters(core),
        lr=HIGH_LEARNING_RATE,
        betas=HIGH_ADAM_BETAS,
        eps=HIGH_ADAM_EPS,
        weight_decay=HIGH_ADAM_WEIGHT_DECAY,
        amsgrad=False,
        foreach=False,
        maximize=False,
        capturable=False,
        differentiable=False,
        fused=False,
    )


def clone_high_state(core: VariableRosterEventCore) -> dict[str, dict[str, torch.Tensor]]:
    return {
        "commitment_model": {
            name: tensor.detach().cpu().clone()
            for name, tensor in core.commitment_model.state_dict().items()
        },
        "event_critic": {
            name: tensor.detach().cpu().clone()
            for name, tensor in core.event_critic.state_dict().items()
        },
    }


def serialize_high_state(state: Mapping[str, Any]) -> bytes:
    buffer = io.BytesIO()
    torch.save(deepcopy(dict(state)), buffer)
    return buffer.getvalue()


def deserialize_high_state(payload: bytes) -> dict[str, dict[str, torch.Tensor]]:
    value = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=False)
    if not isinstance(value, Mapping) or set(value) != {
        "commitment_model",
        "event_critic",
    }:
        raise ValueError("serialized update-zero high payload has the wrong schema")
    return deepcopy(dict(value))


def _validate_tensor_mapping(
    actual: Mapping[str, Any], expected: Mapping[str, torch.Tensor], name: str
) -> None:
    if set(actual) != set(expected):
        raise ValueError(f"{name} tensor field mismatch")
    for key, reference in expected.items():
        value = actual[key]
        if not isinstance(value, torch.Tensor):
            raise ValueError(f"{name} tensor payload contains a non-tensor")
        if value.shape != reference.shape or value.dtype != reference.dtype:
            raise ValueError(f"{name} tensor shape or dtype mismatch: {key}")
        if not bool(torch.isfinite(value).all().item()):
            raise ValueError(f"{name} tensor payload contains a non-finite value")


def load_high_state(
    core: VariableRosterEventCore, state: Mapping[str, Any]
) -> None:
    value = dict(state)
    if set(value) != {"commitment_model", "event_critic"}:
        raise ValueError("high state requires exact actor/critic fields")
    _validate_tensor_mapping(
        dict(value["commitment_model"]),
        core.commitment_model.state_dict(),
        "commitment model",
    )
    _validate_tensor_mapping(
        dict(value["event_critic"]),
        core.event_critic.state_dict(),
        "event critic",
    )
    core.commitment_model.load_state_dict(value["commitment_model"], strict=True)
    core.event_critic.load_state_dict(value["event_critic"], strict=True)


def high_states_byte_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if set(left) != set(right):
        return False
    for module_name in left:
        lhs = dict(left[module_name])
        rhs = dict(right[module_name])
        if set(lhs) != set(rhs):
            return False
        for name in lhs:
            if (
                lhs[name].dtype != rhs[name].dtype
                or lhs[name].shape != rhs[name].shape
                or not torch.equal(lhs[name].cpu(), rhs[name].cpu())
            ):
                return False
    return True


def high_state_l2_drift(
    initial: Mapping[str, Any], current: Mapping[str, Any]
) -> float:
    total = 0.0
    for module_name in initial:
        for name, tensor in dict(initial[module_name]).items():
            delta = dict(current[module_name])[name].double().cpu() - tensor.double().cpu()
            total += float(torch.sum(delta * delta).item())
    return math.sqrt(total)


def _make_runtime_core(
    model_owner: VariableRosterEventCore,
    *,
    environment_index: int,
    episode_id: int,
) -> VariableRosterEventCore:
    return VariableRosterEventCore(
        architecture_mode="f1",
        runtime_mode=SUPPLIED_EXECUTOR_RUNTIME,
        obs_dim=OBSERVATION_DIM,
        critic_member_dim=OBSERVATION_DIM,
        critic_global_dim=8,
        n_skills=ACTION_COUNT,
        action_dim=ACTION_COUNT,
        environment_index=int(environment_index),
        opportunity_seed=OPPORTUNITY_FRONTIER_SEED,
        frontier_seed=OPPORTUNITY_FRONTIER_SEED,
        action_seed=ACTION_SEED,
        rng_episode_id=int(episode_id),
        opportunity_stream_id=OPPORTUNITY_STREAM_ID,
        frontier_stream_id=FRONTIER_STREAM_ID,
        action_stream_id=ACTION_STREAM_ID,
        device=model_owner.device,
        shared_models_from=model_owner,
    )


@dataclass
class SuppliedExecutorVectorRuntime:
    """One vector of paired clean episodes at an unprocessed event boundary."""

    arm: str
    model_owner: VariableRosterEventCore
    collector: SyncEnvCollector
    cores: list[VariableRosterEventCore]
    episode_ids: tuple[int, ...]
    current_transactions: list[MembershipTransaction | None]
    deterministic_high: bool
    executor: SuppliedSkillExecutor = field(default_factory=SuppliedSkillExecutor)
    step_index: int = 0
    decision_trace: list[list[dict[str, Any]]] = field(default_factory=list)
    primitive_action_trace: list[list[dict[str, int]]] = field(default_factory=list)
    reward_trace: list[list[float]] = field(default_factory=list)
    last_infos: list[dict[str, Any]] = field(default_factory=list)
    oracle_constructive_calls: int = 0
    lifecycle_audit: dict[str, Any] = field(default_factory=dict)
    training_episode_ledger: list[int] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        arm: str,
        model_owner: VariableRosterEventCore,
        episode_ids: Sequence[int],
        task_seed: int,
        deterministic_high: bool,
    ) -> "SuppliedExecutorVectorRuntime":
        selected_arm = str(arm)
        if selected_arm not in ARMS:
            raise ValueError("supplied-executor arm mismatch")
        ids = tuple(int(value) for value in episode_ids)
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("runtime requires distinct episode IDs")
        envs = [
            CleanProcessDynamicRosterEventEnv(task_master_seed=int(task_seed))
            for _ in ids
        ]
        collector = SyncEnvCollector(envs)
        transactions = collector.reset_event_runtime(ids)
        cores = [
            _make_runtime_core(
                model_owner,
                environment_index=index,
                episode_id=episode_id,
            )
            for index, episode_id in enumerate(ids)
        ]
        runtime = cls(
            arm=selected_arm,
            model_owner=model_owner,
            collector=collector,
            cores=cores,
            episode_ids=ids,
            current_transactions=list(transactions),
            deterministic_high=bool(deterministic_high),
            decision_trace=[[] for _ in ids],
            primitive_action_trace=[[] for _ in ids],
            reward_trace=[[] for _ in ids],
            last_infos=[{} for _ in ids],
            lifecycle_audit={
                "genuine_join_zero_high_state": True,
                "temporary_leave_freeze": True,
                "rejoin_survivor_high_continuity": True,
                "terminal_leave_state": True,
                "survivor_high_continuity": True,
                "frozen_absent_high": {},
            },
        )
        runtime._bind_current_state()
        return runtime

    def _bind_current_state(self) -> None:
        for core, transaction in zip(self.cores, self.current_transactions):
            core.pending_membership_transaction = deepcopy(transaction)
            core.current_observation_state_boundary = (
                None
                if transaction is None
                else deepcopy(transaction.post_membership_pre_policy_snapshot)
            )

    @property
    def terminal(self) -> bool:
        return self.step_index == HORIZON

    def _oracle_teacher_actions(
        self,
        env_index: int,
        transaction: MembershipTransaction,
    ) -> dict[str, int] | None:
        frontier = transaction.post_membership_pre_policy_snapshot.frontier
        if not frontier:
            return None
        adapter = self.collector.envs[env_index]
        environment = adapter.environment
        if environment is None:
            raise RuntimeError("oracle clean environment is not initialized")
        view = environment.observe()
        constructive = constructive_actions(environment, view)
        self.oracle_constructive_calls += 1
        return {key: int(constructive[int(key)]) for key in frontier}

    def advance_one(self) -> None:
        if self.terminal:
            raise RuntimeError("cannot advance a terminal supplied-executor batch")
        results: list[EventTransactionResult] = []
        routed_actions: list[dict[str, int]] = []
        with torch.no_grad():
            for index, (core, raw_transaction) in enumerate(
                zip(self.cores, self.current_transactions)
            ):
                if raw_transaction is None:
                    raise RuntimeError("active batch is missing an event transaction")
                transaction = core.bind_due_frontier(raw_transaction)
                mutated = {
                    delta.lifecycle_key
                    for delta in transaction.atomic_membership_delta
                }
                frontier = set(
                    transaction.post_membership_pre_policy_snapshot.frontier
                )
                survivor_before = {
                    key: record.high_hidden.copy()
                    for key, record in core.records.items()
                    if record.status == ACTIVE
                    and key not in mutated
                    and key not in frontier
                }
                for delta in transaction.atomic_membership_delta:
                    key = delta.lifecycle_key
                    if delta.kind == TEMPORARY_LEAVE:
                        self.lifecycle_audit["frozen_absent_high"][
                            f"{index}:{key}"
                        ] = core.records[key].high_hidden.copy()
                    elif delta.kind == REJOIN:
                        frozen = self.lifecycle_audit["frozen_absent_high"].get(
                            f"{index}:{key}"
                        )
                        self.lifecycle_audit[
                            "rejoin_survivor_high_continuity"
                        ] &= frozen is not None and np.array_equal(
                            core.records[key].high_hidden, frozen
                        )
                teacher_actions = (
                    self._oracle_teacher_actions(index, transaction)
                    if self.arm == ORACLE_ARM
                    else None
                )
                result = core.apply_transaction(
                    transaction,
                    teacher_actions=teacher_actions,
                    deterministic_policy=(
                        self.deterministic_high or self.arm == ORACLE_ARM
                    ),
                )
                for row in result.token_rows:
                    if any(
                        delta.kind == JOIN
                        and delta.lifecycle_key == row.owner_lifecycle_key
                        for delta in transaction.atomic_membership_delta
                    ):
                        self.lifecycle_audit[
                            "genuine_join_zero_high_state"
                        ] &= np.array_equal(
                            row.pre_token_high_hidden,
                            np.zeros(core.high_hidden_dim, dtype=np.float32),
                        )
                for key, before in survivor_before.items():
                    self.lifecycle_audit["survivor_high_continuity"] &= np.array_equal(
                        core.records[key].high_hidden, before
                    )
                for delta in transaction.atomic_membership_delta:
                    if delta.kind == TERMINAL_LEAVE:
                        record = core.records[delta.lifecycle_key]
                        self.lifecycle_audit["terminal_leave_state"] &= (
                            record.status == TERMINAL
                            and record.high_hidden.size == 0
                            and record.active_skill is None
                        )
                for key, record in core.records.items():
                    if record.status == TEMPORARILY_ABSENT:
                        frozen = self.lifecycle_audit["frozen_absent_high"].get(
                            f"{index}:{key}"
                        )
                        self.lifecycle_audit["temporary_leave_freeze"] &= (
                            frozen is not None
                            and np.array_equal(record.high_hidden, frozen)
                        )
                results.append(result)
                actions = self.executor(core.active_skills())
                expected_keys = set(
                    transaction.post_membership_pre_policy_snapshot.keys
                )
                if set(actions) != expected_keys:
                    raise RuntimeError("supplied executor emitted a non-active action")
                routed_actions.append(actions)

        steps = self.collector.step_event_runtime(routed_actions)
        next_transactions: list[MembershipTransaction | None] = []
        for index, (core, result, actions, step) in enumerate(
            zip(self.cores, results, routed_actions, steps)
        ):
            core.complete_primitive_transition(float(step.reward))
            if core.low_ledger or core.low_chunk_boundaries:
                raise RuntimeError("supplied execution created low replay state")
            if step.terminated:
                core.close_terminal()
                next_transaction = None
            else:
                if step.next_transaction is None:
                    raise RuntimeError("nonterminal clean step omitted its next boundary")
                # Keep the environment-owned structural transaction pending.
                # Its private due frontier is bound exactly once immediately
                # before the next high event, including after checkpoint resume.
                next_transaction = step.next_transaction
            self.decision_trace[index].append(
                {
                    "time": self.step_index,
                    "frontier": list(result.sampled_order),
                    "high_actions": {
                        row.owner_lifecycle_key: int(row.combined_action)
                        for row in result.token_rows
                    },
                }
            )
            self.primitive_action_trace[index].append(dict(actions))
            self.reward_trace[index].append(float(step.reward))
            self.last_infos[index] = deepcopy(dict(step.info))
            next_transactions.append(next_transaction)
        self.step_index += 1
        self.current_transactions = next_transactions
        self._bind_current_state()

    def advance(self, steps: int | None = None) -> None:
        count = HORIZON - self.step_index if steps is None else int(steps)
        if count < 0 or self.step_index + count > HORIZON:
            raise ValueError("supplied-executor advance exceeds the episode horizon")
        for _ in range(count):
            self.advance_one()

    def outcomes(self) -> list[dict[str, float]]:
        if not self.terminal:
            raise RuntimeError("outcomes require a terminal vector runtime")
        rows: list[dict[str, float]] = []
        for adapter in self.collector.envs:
            if adapter.environment is None:
                raise RuntimeError("terminal clean environment is unavailable")
            outcome = adapter.environment.outcome()
            rows.append(
                {
                    "persistent": float(outcome.persistent_score),
                    "short": float(outcome.short_score),
                    "utility": float(outcome.utility),
                }
            )
        return rows

    def close(self) -> None:
        self.collector.close()


def _optimizer_parameter_ids(optimizer: torch.optim.Optimizer) -> set[int]:
    return {
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
    }


def _validate_high_optimizer(
    core: VariableRosterEventCore, optimizer: torch.optim.Optimizer
) -> None:
    if type(optimizer) is not torch.optim.Adam:
        raise ValueError("high optimizer must be the frozen Adam implementation")
    expected_parameters = high_parameters(core)
    if _optimizer_parameter_ids(optimizer) != {
        id(parameter) for parameter in expected_parameters
    }:
        raise ValueError(
            "high optimizer must own exactly commitment actor and event critic"
        )
    if len(optimizer.param_groups) != 1:
        raise ValueError("high optimizer contract mismatch")
    group = optimizer.param_groups[0]
    expected_fields = {
        "params",
        "lr",
        "betas",
        "eps",
        "weight_decay",
        "amsgrad",
        "maximize",
        "foreach",
        "capturable",
        "differentiable",
        "fused",
    }
    if "decoupled_weight_decay" in group:
        expected_fields.add("decoupled_weight_decay")
    if set(group) != expected_fields or len(group["params"]) != len(
        expected_parameters
    ) or any(
        actual is not expected
        for actual, expected in zip(group["params"], expected_parameters)
    ):
        raise ValueError("high optimizer parameter-group schema mismatch")
    expected_hyperparameters = {
        "lr": HIGH_LEARNING_RATE,
        "betas": HIGH_ADAM_BETAS,
        "eps": HIGH_ADAM_EPS,
        "weight_decay": HIGH_ADAM_WEIGHT_DECAY,
        "amsgrad": False,
        "maximize": False,
        "foreach": False,
        "capturable": False,
        "differentiable": False,
        "fused": False,
    }
    if "decoupled_weight_decay" in group:
        expected_hyperparameters["decoupled_weight_decay"] = False
    if any(group[name] != expected for name, expected in expected_hyperparameters.items()):
        raise ValueError("high optimizer frozen hyperparameter mismatch")


def _validate_optimizer_state_schema(
    state: Mapping[str, Any],
    *,
    core: VariableRosterEventCore,
    optimizer: torch.optim.Optimizer,
    expected_steps: int,
) -> None:
    value = dict(state)
    if set(value) != {"state", "param_groups"}:
        raise ValueError("high optimizer state field mismatch")
    _validate_high_optimizer(core, optimizer)
    serialized_groups = list(value["param_groups"])
    if len(serialized_groups) != 1 or not isinstance(
        serialized_groups[0], Mapping
    ):
        raise ValueError("high optimizer serialized parameter-group mismatch")
    serialized_group = dict(serialized_groups[0])
    live_group = optimizer.param_groups[0]
    if set(serialized_group) != set(live_group):
        raise ValueError("high optimizer serialized group field mismatch")
    parameters = high_parameters(core)
    expected_ids = list(range(len(parameters)))
    if list(serialized_group["params"]) != expected_ids:
        raise ValueError("high optimizer serialized parameter ordering mismatch")
    for name in set(live_group) - {"params"}:
        if not _recursive_equal(serialized_group[name], live_group[name]):
            raise ValueError(f"high optimizer serialized hyperparameter mismatch: {name}")

    serialized_state = dict(value["state"])
    expected = int(expected_steps)
    if expected == 0:
        if serialized_state:
            raise ValueError("high optimizer/counter mismatch at update zero")
        return
    if set(serialized_state) != set(expected_ids):
        raise ValueError("high optimizer state is incomplete for model parameters")
    for index, parameter in enumerate(parameters):
        item = dict(serialized_state[index])
        if set(item) != {"step", "exp_avg", "exp_avg_sq"}:
            raise ValueError("high optimizer per-parameter state schema mismatch")
        step = item["step"]
        if (
            not isinstance(step, torch.Tensor)
            or step.numel() != 1
            or not bool(torch.isfinite(step).item())
            or int(step.item()) != expected
        ):
            raise ValueError("high optimizer/counter step mismatch")
        for name in ("exp_avg", "exp_avg_sq"):
            tensor = item[name]
            if (
                not isinstance(tensor, torch.Tensor)
                or tensor.shape != parameter.shape
                or tensor.dtype != parameter.dtype
                or not bool(torch.isfinite(tensor).all().item())
            ):
                raise ValueError(
                    f"high optimizer {name} tensor shape/dtype mismatch"
                )
        if bool(torch.any(item["exp_avg_sq"] < 0).item()):
            raise ValueError("high optimizer second moment is invalid")


def _shape_contract(
    model_owner: VariableRosterEventCore, *, num_envs: int, horizon: int
) -> dict[str, Any]:
    return {
        "num_envs": int(num_envs),
        "horizon": int(horizon),
        "architecture_state": deepcopy(model_owner.architecture_state()),
        "commitment_model_shapes": {
            name: tuple(tensor.shape)
            for name, tensor in model_owner.commitment_model.state_dict().items()
        },
        "event_critic_shapes": {
            name: tuple(tensor.shape)
            for name, tensor in model_owner.event_critic.state_dict().items()
        },
    }


def _rng_ledger(core: VariableRosterEventCore) -> dict[str, Any]:
    return {
        "episode_id": int(core.rng_episode_id),
        "opportunity": {
            "master_seed": int(core.opportunity_master_seed),
            "stream_id": int(core.opportunity_stream_id),
        },
        "frontier": {
            "master_seed": int(core.frontier_master_seed),
            "stream_id": int(core.frontier_stream_id),
        },
        "action": {
            "master_seed": int(core.action_master_seed),
            "stream_id": int(core.action_stream_id),
        },
    }


def _core_runtime_payload(core: VariableRosterEventCore) -> dict[str, Any]:
    if core.runtime_mode != SUPPLIED_EXECUTOR_RUNTIME:
        raise ValueError("checkpoint core is not in supplied-executor mode")
    if core.low_ledger or core.low_chunk_boundaries:
        raise ValueError("high-only checkpoint rejects low replay state")
    if (
        tuple(core.low_actor.parameters())
        or tuple(core.low_critic.parameters())
        or core.low_actor.state_dict()
        or core.low_critic.state_dict()
        or any(
            record.low_actor_hidden.size != 0
            or record.low_critic_hidden.size != 0
            for record in core.records.values()
        )
    ):
        raise ValueError("high-only checkpoint rejects low graph or recurrent state")
    return {
        "environment_index": int(core.environment_index),
        "architecture_state": deepcopy(core.architecture_state()),
        "runtime_mode": core.runtime_mode,
        "rng_ledger": _rng_ledger(core),
        "lifecycle_records": {
            key: core._record_to_state(record)
            for key, record in core.records.items()
        },
        "opportunity_rng_state": deepcopy(core.opportunity_rng.bit_generator.state),
        "frontier_rng_state": deepcopy(core.frontier_rng.bit_generator.state),
        "action_rng_state": deepcopy(core.action_rng.bit_generator.state),
        "high_ledger": deepcopy(core.high_ledger),
        "closed_event_rows": deepcopy(core.closed_event_rows),
        "policy_version": int(core.policy_version),
        "physical_time": int(core.physical_time),
        "current_observation_state_boundary": deepcopy(
            core.current_observation_state_boundary
        ),
        "pending_membership_transaction": deepcopy(
            core.pending_membership_transaction
        ),
        "low_path_state": {
            "low_ledger_rows": 0,
            "low_chunk_boundaries": 0,
            "low_optimizer_steps": 0,
        },
    }


def _torch_rng_payload() -> dict[str, Any]:
    return {
        "cpu": torch.get_rng_state().clone(),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda": (
            [state.clone() for state in torch.cuda.get_rng_state_all()]
            if torch.cuda.is_available()
            else []
        ),
    }


def _validate_counters(
    counters: Mapping[str, Any], *, num_envs: int, horizon: int
) -> dict[str, int]:
    if set(counters) != HIGH_COUNTER_FIELDS:
        raise ValueError("high-only checkpoint counter field mismatch")
    value = {name: int(counters[name]) for name in HIGH_COUNTER_FIELDS}
    if any(item < 0 for item in value.values()):
        raise ValueError("high-only checkpoint counters must be nonnegative")
    step = value["step_in_update"]
    passes = value["ppo_passes_in_update"]
    update = value["update_index"]
    if step > int(horizon) or passes > PPO_PASSES_PER_UPDATE:
        raise ValueError("high-only checkpoint counter range mismatch")
    if step < int(horizon) and passes != 0:
        raise ValueError("PPO passes cannot precede a full-horizon collection")
    expected_transitions = (
        update * int(num_envs) * int(horizon) + step * int(num_envs)
    )
    if value["environment_transitions"] != expected_transitions:
        raise ValueError("high-only checkpoint transition counter mismatch")
    if value["high_optimizer_steps"] != (
        update * PPO_PASSES_PER_UPDATE + passes
    ):
        raise ValueError("high-only checkpoint optimizer counter mismatch")
    if value["next_episode_id"] != (update + 1) * int(num_envs):
        raise ValueError("high-only checkpoint episode-allocation counter mismatch")
    completed_in_active = int(step == int(horizon)) * int(num_envs)
    if value["episodes_completed"] != update * int(num_envs) + completed_in_active:
        raise ValueError("high-only checkpoint episode completion counter mismatch")
    return value


def high_only_checkpoint_payload(
    runtime: SuppliedExecutorVectorRuntime,
    *,
    optimizer: torch.optim.Optimizer,
    counters: Mapping[str, Any],
    horizon: int = HORIZON,
) -> dict[str, Any]:
    """Capture exact live high/core/collector/counter/Torch RNG state."""

    if runtime.arm != LEARNED_HIGH_ARM:
        raise ValueError("live high-only checkpoints are learned-arm only")
    if runtime.model_owner.runtime_mode != SUPPLIED_EXECUTOR_RUNTIME:
        raise ValueError("checkpoint model owner has the wrong runtime mode")
    if len(runtime.cores) != len(runtime.episode_ids):
        raise ValueError("checkpoint runtime vector shape mismatch")
    _validate_high_optimizer(runtime.model_owner, optimizer)
    counter_value = _validate_counters(
        counters, num_envs=len(runtime.cores), horizon=int(horizon)
    )
    expected_episode_ids = tuple(
        range(
            counter_value["update_index"] * len(runtime.cores),
            (counter_value["update_index"] + 1) * len(runtime.cores),
        )
    )
    if runtime.episode_ids != expected_episode_ids:
        raise ValueError("checkpoint active episode IDs are not canonical")
    expected_completed_ledger = list(
        range(counter_value["episodes_completed"])
    )
    if runtime.training_episode_ledger != expected_completed_ledger:
        raise ValueError("checkpoint completed episode ledger mismatch")
    optimizer_state = deepcopy(optimizer.state_dict())
    _validate_optimizer_state_schema(
        optimizer_state,
        core=runtime.model_owner,
        optimizer=optimizer,
        expected_steps=counter_value["high_optimizer_steps"],
    )
    if int(runtime.step_index) != counter_value["step_in_update"]:
        raise ValueError("runtime/checkpoint step counter mismatch")
    if tuple(core.environment_index for core in runtime.cores) != tuple(
        range(len(runtime.cores))
    ):
        raise ValueError("checkpoint environment indices are not canonical")
    if tuple(core.rng_episode_id for core in runtime.cores) != runtime.episode_ids:
        raise ValueError("checkpoint runtime episode ledger mismatch")
    for core in runtime.cores:
        if (
            core.commitment_model is not runtime.model_owner.commitment_model
            or core.event_critic is not runtime.model_owner.event_critic
        ):
            raise ValueError("checkpoint runtimes do not share one high graph")
    collector_snapshot = runtime.collector.snapshot_event_runtime()
    diagnostics = {
        "episode_ids": tuple(runtime.episode_ids),
        "step_index": int(runtime.step_index),
        "deterministic_high": bool(runtime.deterministic_high),
        "decision_trace": deepcopy(runtime.decision_trace),
        "primitive_action_trace": deepcopy(runtime.primitive_action_trace),
        "reward_trace": deepcopy(runtime.reward_trace),
        "last_infos": deepcopy(runtime.last_infos),
        "oracle_constructive_calls": int(runtime.oracle_constructive_calls),
        "lifecycle_audit": deepcopy(runtime.lifecycle_audit),
        "training_episode_ledger": list(runtime.training_episode_ledger),
    }
    return {
        "checkpoint_schema_version": HIGH_CHECKPOINT_SCHEMA_VERSION,
        "package": PACKAGE_NAME,
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "arm": runtime.arm,
        "runtime_mode": SUPPLIED_EXECUTOR_RUNTIME,
        "architecture_mode": "f1",
        "event_architecture_schema_version": EVENT_ARCHITECTURE_SCHEMA_VERSION,
        "shape_contract": _shape_contract(
            runtime.model_owner,
            num_envs=len(runtime.cores),
            horizon=int(horizon),
        ),
        "seed_contract": deepcopy(SEED_CONTRACT),
        "model_state": clone_high_state(runtime.model_owner),
        "optimizer_state": optimizer_state,
        "runtime_cores": [
            _core_runtime_payload(core) for core in runtime.cores
        ],
        "collector_snapshot": deepcopy(collector_snapshot),
        "current_transactions": deepcopy(runtime.current_transactions),
        "runtime_diagnostics": diagnostics,
        "counters": counter_value,
        "torch_rng_state": _torch_rng_payload(),
    }


def _validate_rng_state(value: Any, name: str) -> None:
    if not isinstance(value, Mapping) or value.get("bit_generator") != "PCG64":
        raise ValueError(f"high-only checkpoint {name} is not exact PCG64 state")


def _validate_core_runtime_payload(
    core: VariableRosterEventCore, payload: Mapping[str, Any]
) -> None:
    if set(payload) != CORE_RUNTIME_FIELDS:
        raise ValueError("high-only checkpoint core runtime field mismatch")
    if int(payload["environment_index"]) != int(core.environment_index):
        raise ValueError("high-only checkpoint environment index mismatch")
    if dict(payload["architecture_state"]) != core.architecture_state():
        raise ValueError("high-only checkpoint core shape mismatch")
    if payload["runtime_mode"] != SUPPLIED_EXECUTOR_RUNTIME:
        raise ValueError("high-only checkpoint core mode mismatch")
    if dict(payload["rng_ledger"]) != _rng_ledger(core):
        raise ValueError("high-only checkpoint core seed ledger mismatch")
    _validate_rng_state(payload["opportunity_rng_state"], "opportunity RNG")
    _validate_rng_state(payload["frontier_rng_state"], "frontier RNG")
    _validate_rng_state(payload["action_rng_state"], "action RNG")
    if dict(payload["low_path_state"]) != {
        "low_ledger_rows": 0,
        "low_chunk_boundaries": 0,
        "low_optimizer_steps": 0,
    }:
        raise ValueError("high-only checkpoint contains low-path state")
    lifecycle_records = dict(payload["lifecycle_records"])
    if any(
        not isinstance(state, Mapping)
        or np.asarray(state.get("low_actor_hidden", ())).size != 0
        or np.asarray(state.get("low_critic_hidden", ())).size != 0
        for state in lifecycle_records.values()
    ):
        raise ValueError("high-only checkpoint contains low recurrent state")
    if int(payload["physical_time"]) < 0 or int(payload["physical_time"]) > HORIZON:
        raise ValueError("high-only checkpoint physical-time mismatch")


def _restore_core_runtime(
    core: VariableRosterEventCore, payload: Mapping[str, Any]
) -> None:
    core.records = {
        str(key): core._record_from_state(state)
        for key, state in dict(payload["lifecycle_records"]).items()
    }
    core.opportunity_rng.bit_generator.state = deepcopy(
        payload["opportunity_rng_state"]
    )
    core.frontier_rng.bit_generator.state = deepcopy(payload["frontier_rng_state"])
    core.action_rng.bit_generator.state = deepcopy(payload["action_rng_state"])
    core.high_ledger = deepcopy(list(payload["high_ledger"]))
    core.closed_event_rows = deepcopy(list(payload["closed_event_rows"]))
    core.low_ledger = []
    core.low_chunk_boundaries = []
    core.policy_version = int(payload["policy_version"])
    core.physical_time = int(payload["physical_time"])
    core.current_observation_state_boundary = deepcopy(
        payload["current_observation_state_boundary"]
    )
    core.pending_membership_transaction = deepcopy(
        payload["pending_membership_transaction"]
    )


def restore_high_only_checkpoint(
    payload: Mapping[str, Any],
    runtime: SuppliedExecutorVectorRuntime,
    *,
    optimizer: torch.optim.Optimizer,
    expected_arm: str = LEARNED_HIGH_ARM,
    horizon: int = HORIZON,
) -> dict[str, int]:
    """Strictly restore a live supplied-executor vector runtime."""

    value = dict(payload)
    if set(value) != CHECKPOINT_FIELDS:
        raise ValueError("high-only checkpoint top-level field mismatch")
    scalar_expected = {
        "checkpoint_schema_version": HIGH_CHECKPOINT_SCHEMA_VERSION,
        "package": PACKAGE_NAME,
        "package_schema_version": PACKAGE_SCHEMA_VERSION,
        "arm": str(expected_arm),
        "runtime_mode": SUPPLIED_EXECUTOR_RUNTIME,
        "architecture_mode": "f1",
        "event_architecture_schema_version": EVENT_ARCHITECTURE_SCHEMA_VERSION,
    }
    for name, expected in scalar_expected.items():
        if value[name] != expected:
            raise ValueError(f"high-only checkpoint header mismatch: {name}")
    if runtime.arm != expected_arm:
        raise ValueError("restore target arm mismatch")
    if dict(value["seed_contract"]) != SEED_CONTRACT:
        raise ValueError("high-only checkpoint seed contract mismatch")
    expected_shape = _shape_contract(
        runtime.model_owner,
        num_envs=len(runtime.cores),
        horizon=int(horizon),
    )
    if dict(value["shape_contract"]) != expected_shape:
        raise ValueError("high-only checkpoint shape contract mismatch")
    _validate_high_optimizer(runtime.model_owner, optimizer)
    counters = _validate_counters(
        dict(value["counters"]),
        num_envs=len(runtime.cores),
        horizon=int(horizon),
    )
    expected_episode_ids = tuple(
        range(
            counters["update_index"] * len(runtime.cores),
            (counters["update_index"] + 1) * len(runtime.cores),
        )
    )
    if runtime.episode_ids != expected_episode_ids:
        raise ValueError("restore target episode IDs are not counter-canonical")
    core_payloads = list(value["runtime_cores"])
    transactions = list(value["current_transactions"])
    if len(core_payloads) != len(runtime.cores) or len(transactions) != len(
        runtime.cores
    ):
        raise ValueError("high-only checkpoint runtime vector length mismatch")
    for core, core_payload in zip(runtime.cores, core_payloads):
        if not isinstance(core_payload, Mapping):
            raise ValueError("high-only checkpoint core payload is malformed")
        _validate_core_runtime_payload(core, core_payload)
    for core_payload, transaction in zip(core_payloads, transactions):
        expected_boundary = (
            None
            if transaction is None
            else transaction.post_membership_pre_policy_snapshot
        )
        if not _recursive_equal(
            core_payload["pending_membership_transaction"], transaction
        ) or not _recursive_equal(
            core_payload["current_observation_state_boundary"],
            expected_boundary,
        ):
            raise ValueError(
                "high-only checkpoint current-boundary transaction mismatch"
            )
    model_state = dict(value["model_state"])
    if set(model_state) != {"commitment_model", "event_critic"}:
        raise ValueError("high-only checkpoint model field mismatch")
    _validate_tensor_mapping(
        dict(model_state["commitment_model"]),
        runtime.model_owner.commitment_model.state_dict(),
        "commitment model",
    )
    _validate_tensor_mapping(
        dict(model_state["event_critic"]),
        runtime.model_owner.event_critic.state_dict(),
        "event critic",
    )
    diagnostics = dict(value["runtime_diagnostics"])
    required_diagnostics = {
        "episode_ids",
        "step_index",
        "deterministic_high",
        "decision_trace",
        "primitive_action_trace",
        "reward_trace",
        "last_infos",
        "oracle_constructive_calls",
        "lifecycle_audit",
        "training_episode_ledger",
    }
    if set(diagnostics) != required_diagnostics:
        raise ValueError("high-only checkpoint diagnostic state mismatch")
    if tuple(int(item) for item in diagnostics["episode_ids"]) != runtime.episode_ids:
        raise ValueError("high-only checkpoint diagnostic episode mismatch")
    restored_episode_ledger = [
        int(item) for item in diagnostics["training_episode_ledger"]
    ]
    if restored_episode_ledger != list(range(counters["episodes_completed"])):
        raise ValueError("high-only checkpoint completed episode ledger mismatch")
    if int(diagnostics["step_index"]) != counters["step_in_update"]:
        raise ValueError("high-only checkpoint diagnostic counter mismatch")
    if bool(diagnostics["deterministic_high"]) != bool(
        runtime.deterministic_high
    ):
        raise ValueError("high-only checkpoint deterministic-mode mismatch")
    step_index = int(diagnostics["step_index"])
    for name in ("decision_trace", "primitive_action_trace", "reward_trace"):
        rows = list(diagnostics[name])
        if len(rows) != len(runtime.cores) or any(
            len(row) != step_index for row in rows
        ):
            raise ValueError("high-only checkpoint runtime trace length mismatch")
    if len(list(diagnostics["last_infos"])) != len(runtime.cores):
        raise ValueError("high-only checkpoint runtime info length mismatch")
    collector_snapshot = dict(value["collector_snapshot"])
    pending = list(collector_snapshot.get("pending_membership_transaction", ()))
    workers = list(collector_snapshot.get("workers", ()))
    if len(pending) != len(transactions) or len(workers) != len(transactions):
        raise ValueError("high-only checkpoint collector vector mismatch")
    if not _recursive_equal(pending, transactions) or any(
        not isinstance(worker, Mapping)
        or not _recursive_equal(
            worker.get("pending_membership_transaction"), transaction
        )
        for worker, transaction in zip(workers, transactions)
    ):
        raise ValueError("high-only checkpoint collector transaction mismatch")
    optimizer_state = dict(value["optimizer_state"])
    _validate_optimizer_state_schema(
        optimizer_state,
        core=runtime.model_owner,
        optimizer=optimizer,
        expected_steps=counters["high_optimizer_steps"],
    )
    torch_rng = dict(value["torch_rng_state"])
    if set(torch_rng) != {"cpu", "cuda_available", "cuda"}:
        raise ValueError("high-only checkpoint Torch RNG field mismatch")
    if (
        not isinstance(torch_rng["cpu"], torch.Tensor)
        or torch_rng["cpu"].dtype != torch.uint8
        or torch_rng["cpu"].ndim != 1
    ):
        raise ValueError("high-only checkpoint CPU Torch RNG is malformed")
    if bool(torch_rng["cuda_available"]) != bool(torch.cuda.is_available()):
        raise ValueError("high-only checkpoint CUDA RNG availability mismatch")
    cuda_states = list(torch_rng["cuda"])
    if torch.cuda.is_available() and len(cuda_states) != torch.cuda.device_count():
        raise ValueError("high-only checkpoint CUDA RNG device-count mismatch")
    if not torch.cuda.is_available() and cuda_states:
        raise ValueError("CPU checkpoint unexpectedly contains CUDA RNG state")

    # All schema, mode, arm, shape, seed and counter checks precede mutation.
    load_high_state(runtime.model_owner, model_state)
    optimizer.load_state_dict(deepcopy(optimizer_state))
    _validate_high_optimizer(runtime.model_owner, optimizer)
    for core, core_payload in zip(runtime.cores, core_payloads):
        _restore_core_runtime(core, core_payload)
    runtime.collector.restore_event_runtime(deepcopy(value["collector_snapshot"]))
    runtime.current_transactions = deepcopy(transactions)
    runtime.step_index = int(diagnostics["step_index"])
    runtime.deterministic_high = bool(diagnostics["deterministic_high"])
    runtime.decision_trace = deepcopy(list(diagnostics["decision_trace"]))
    runtime.primitive_action_trace = deepcopy(
        list(diagnostics["primitive_action_trace"])
    )
    runtime.reward_trace = deepcopy(list(diagnostics["reward_trace"]))
    runtime.last_infos = deepcopy(list(diagnostics["last_infos"]))
    runtime.oracle_constructive_calls = int(
        diagnostics["oracle_constructive_calls"]
    )
    runtime.lifecycle_audit = deepcopy(dict(diagnostics["lifecycle_audit"]))
    runtime.training_episode_ledger = restored_episode_ledger
    runtime._bind_current_state()
    torch.set_rng_state(torch_rng["cpu"].cpu())
    if torch.cuda.is_available():
        torch.cuda.set_rng_state_all([state.cpu() for state in cuda_states])
    return counters


def atomic_torch_save(payload: Mapping[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    torch.save(dict(payload), temporary)
    temporary.replace(target)


def atomic_bytes_save(payload: bytes, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(target)


def _recursive_equal(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
        return isinstance(left, torch.Tensor) and isinstance(
            right, torch.Tensor
        ) and torch.equal(left.cpu(), right.cpu())
    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        return isinstance(left, np.ndarray) and isinstance(
            right, np.ndarray
        ) and np.array_equal(left, right)
    if isinstance(left, Mapping) or isinstance(right, Mapping):
        if not isinstance(left, Mapping) or not isinstance(right, Mapping):
            return False
        return set(left) == set(right) and all(
            _recursive_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        if not isinstance(left, (list, tuple)) or not isinstance(
            right, (list, tuple)
        ):
            return False
        return len(left) == len(right) and all(
            _recursive_equal(lhs, rhs) for lhs, rhs in zip(left, right)
        )
    if hasattr(left, "__dict__") or hasattr(right, "__dict__"):
        return type(left) is type(right) and _recursive_equal(
            vars(left), vars(right)
        )
    return bool(left == right)


def _runtime_contract_audit(
    runtime: SuppliedExecutorVectorRuntime,
) -> dict[str, bool]:
    no_low = all(
        not core.low_ledger
        and not core.low_chunk_boundaries
        and not tuple(core.low_actor.parameters())
        and not tuple(core.low_critic.parameters())
        and not core.low_actor.state_dict()
        and not core.low_critic.state_dict()
        and all(
            record.low_actor_hidden.size == 0
            and record.low_critic_hidden.size == 0
            for record in core.records.values()
        )
        for core in runtime.cores
    )
    support_exact = True
    active_only = True
    owner_credit = True
    opportunity_range = True
    for core_index, core in enumerate(runtime.cores):
        rewards = runtime.reward_trace[core_index]
        for token in core.high_ledger:
            support_exact &= (
                token.exact_legal_mask.shape == (ACTION_COUNT,)
                and bool(np.all(token.exact_legal_mask))
                and int(token.combined_action) in (IDLE, PERSIST, SHORT)
            )
            active_only &= (
                len(token.active_lifecycle_keys)
                == len(set(token.active_lifecycle_keys))
                == len(token.active_membership_epochs)
                == token.active_observations.shape[0]
                == token.active_critic_member_features.shape[0]
                == token.active_high_hidden.shape[0]
            )
            opportunity_range &= OPPORTUNITY_GAP_LOW <= int(
                token.sampled_replacement_gap
            ) <= OPPORTUNITY_GAP_HIGH
        for row in core.closed_event_rows:
            owner_credit &= int(row.elapsed_physical_time) == int(
                row.end_time - row.start_time
            )
            expected = sum(
                (core.gamma ** offset) * float(rewards[row.start_time + offset])
                for offset in range(row.elapsed_physical_time)
            )
            owner_credit &= math.isclose(
                float(row.discounted_reward),
                float(expected),
                rel_tol=0.0,
                abs_tol=1.0e-9,
            )
            owner_credit &= math.isclose(
                float(row.bootstrap_discount),
                (
                    0.0
                    if row.boundary_kind == "terminal_boundary"
                    else core.gamma ** row.elapsed_physical_time
                ),
                rel_tol=0.0,
                abs_tol=1.0e-12,
            )
    lifecycle = {
        key: bool(value)
        for key, value in runtime.lifecycle_audit.items()
        if key != "frozen_absent_high"
    }
    return {
        "zero_low_graph_state_and_rows": bool(no_low),
        "exact_all_three_action_support": bool(support_exact),
        "active_only_routing_and_masks": bool(active_only),
        "owner_local_physical_time_credit": bool(owner_credit),
        "private_opportunity_gap_range": bool(opportunity_range),
        **lifecycle,
    }


def _merge_boolean_audits(
    aggregate: dict[str, bool], current: Mapping[str, bool]
) -> None:
    for name, value in current.items():
        aggregate[name] = bool(aggregate.get(name, True) and bool(value))


def checkpoint_roundtrip_audit(device: str | torch.device = "cpu") -> dict[str, bool]:
    """Exercise strict restore and exact continuation from an open segment."""

    owner = make_model_owner(device)
    optimizer = make_high_optimizer(owner)
    runtime = SuppliedExecutorVectorRuntime.create(
        arm=LEARNED_HIGH_ARM,
        model_owner=owner,
        episode_ids=(0,),
        task_seed=TRAIN_TASK_SEED,
        deterministic_high=False,
    )
    runtime.advance(7)
    open_trace = any(
        record.open_event_trace is not None for record in runtime.cores[0].records.values()
    )
    counters = {
        "update_index": 0,
        "step_in_update": 7,
        "ppo_passes_in_update": 0,
        "environment_transitions": 7,
        "high_optimizer_steps": 0,
        "next_episode_id": 1,
        "episodes_completed": 0,
    }
    payload = high_only_checkpoint_payload(
        runtime, optimizer=optimizer, counters=counters
    )
    model_at_checkpoint = clone_high_state(owner)
    optimizer_at_checkpoint = deepcopy(optimizer.state_dict())
    runtime.advance(9)
    expected_core = _core_runtime_payload(runtime.cores[0])
    expected_collector = runtime.collector.snapshot_event_runtime()
    expected_diagnostics = (
        deepcopy(runtime.decision_trace),
        deepcopy(runtime.primitive_action_trace),
        deepcopy(runtime.reward_trace),
    )

    restored_owner = make_model_owner(device)
    restored_optimizer = make_high_optimizer(restored_owner)
    restored = SuppliedExecutorVectorRuntime.create(
        arm=LEARNED_HIGH_ARM,
        model_owner=restored_owner,
        episode_ids=(0,),
        task_seed=TRAIN_TASK_SEED,
        deterministic_high=False,
    )
    restored_counters = restore_high_only_checkpoint(
        payload,
        restored,
        optimizer=restored_optimizer,
    )
    model_exact = high_states_byte_equal(
        model_at_checkpoint, clone_high_state(restored_owner)
    )
    optimizer_exact = _recursive_equal(
        optimizer_at_checkpoint, restored_optimizer.state_dict()
    )
    restored.advance(9)
    continuation_exact = (
        _recursive_equal(expected_core, _core_runtime_payload(restored.cores[0]))
        and _recursive_equal(
            expected_collector, restored.collector.snapshot_event_runtime()
        )
        and _recursive_equal(
            expected_diagnostics,
            (
                restored.decision_trace,
                restored.primitive_action_trace,
                restored.reward_trace,
            ),
        )
    )

    missing_rejected = False
    missing = deepcopy(payload)
    del missing["torch_rng_state"]
    try:
        restore_high_only_checkpoint(
            missing, restored, optimizer=restored_optimizer
        )
    except ValueError:
        missing_rejected = True
    mismatch_rejected = False
    mismatch = deepcopy(payload)
    mismatch["seed_contract"]["action"] += 1
    try:
        restore_high_only_checkpoint(
            mismatch, restored, optimizer=restored_optimizer
        )
    except ValueError:
        mismatch_rejected = True
    counter_rejected = False
    bad_counter = deepcopy(payload)
    bad_counter["counters"]["environment_transitions"] += 1
    try:
        restore_high_only_checkpoint(
            bad_counter, restored, optimizer=restored_optimizer
        )
    except ValueError:
        counter_rejected = True
    runtime.close()
    restored.close()
    return {
        "open_mid_segment_checkpoint": bool(open_trace),
        "checkpoint_model_round_trip": bool(model_exact),
        "checkpoint_optimizer_round_trip": bool(optimizer_exact),
        "exact_open_segment_continuation": bool(continuation_exact),
        "checkpoint_missing_field_fail_closed": bool(missing_rejected),
        "checkpoint_seed_mismatch_fail_closed": bool(mismatch_rejected),
        "checkpoint_counter_mismatch_fail_closed": bool(counter_rejected),
        "checkpoint_counter_round_trip": restored_counters == counters,
    }


def oracle_tensor_independence_audit(
    update_zero_serialized: bytes,
    *,
    device: str | torch.device = "cpu",
) -> bool:
    baseline_state = deserialize_high_state(update_zero_serialized)
    perturbed_state = deepcopy(baseline_state)
    for module in perturbed_state.values():
        for name, tensor in module.items():
            module[name] = tensor + torch.full_like(tensor, 0.125)

    traces: list[Any] = []
    for state in (baseline_state, perturbed_state):
        owner = make_model_owner(device)
        load_high_state(owner, state)
        owner.commitment_model.eval()
        owner.event_critic.eval()
        runtime = SuppliedExecutorVectorRuntime.create(
            arm=ORACLE_ARM,
            model_owner=owner,
            episode_ids=(0,),
            task_seed=EVALUATION_TASK_SEED,
            deterministic_high=True,
        )
        with torch.no_grad():
            runtime.advance()
        traces.append(
            (
                deepcopy(runtime.primitive_action_trace),
                deepcopy(runtime.decision_trace),
                runtime.outcomes(),
            )
        )
        runtime.close()
    return _recursive_equal(traces[0], traces[1])


def _evaluate_arm(
    *,
    arm: str,
    high_state: Mapping[str, Any],
    episode_ids: Sequence[int],
    batch_size: int,
    device: str | torch.device,
) -> dict[str, Any]:
    ids = tuple(int(value) for value in episode_ids)
    if not ids:
        raise ValueError("evaluation requires at least one episode")
    owner = make_model_owner(device)
    load_high_state(owner, high_state)
    state_before = clone_high_state(owner)
    owner.commitment_model.eval()
    owner.event_critic.eval()
    outcomes: list[dict[str, float]] = []
    audit: dict[str, bool] = {}
    constructive_calls = 0
    with torch.no_grad():
        for start in range(0, len(ids), int(batch_size)):
            batch_ids = ids[start : start + int(batch_size)]
            runtime = SuppliedExecutorVectorRuntime.create(
                arm=arm,
                model_owner=owner,
                episode_ids=batch_ids,
                task_seed=EVALUATION_TASK_SEED,
                deterministic_high=True,
            )
            runtime.advance()
            outcomes.extend(runtime.outcomes())
            _merge_boolean_audits(audit, _runtime_contract_audit(runtime))
            constructive_calls += runtime.oracle_constructive_calls
            runtime.close()
    array = np.asarray(
        [
            (row["persistent"], row["short"], row["utility"])
            for row in outcomes
        ],
        dtype=np.float64,
    )
    return {
        "arm": arm,
        "episode_ids": list(ids),
        "persistent": array[:, 0].tolist(),
        "short": array[:, 1].tolist(),
        "utility": array[:, 2].tolist(),
        "persistent_mean": float(array[:, 0].mean()),
        "short_mean": float(array[:, 1].mean()),
        "utility_mean": float(array[:, 2].mean()),
        "no_grad": True,
        "optimizer_steps": 0,
        "high_tensor_drift": high_state_l2_drift(
            state_before, clone_high_state(owner)
        ),
        "oracle_constructive_calls": int(constructive_calls),
        "audit": audit,
    }


def paired_bootstrap_ci95(
    values: Sequence[float], *, seed: int = BOOTSTRAP_SEED
) -> list[float]:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError("paired bootstrap requires finite non-empty values")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(seed)])))
    selected = rng.integers(
        0,
        array.size,
        size=(BOOTSTRAP_REPETITIONS, array.size),
        dtype=np.int64,
    )
    means = array[selected].mean(axis=1)
    return [
        float(np.quantile(means, 0.025)),
        float(array.mean()),
        float(np.quantile(means, 0.975)),
    ]


@dataclass
class LearnedTrainingArtifacts:
    model_owner: VariableRosterEventCore
    optimizer: torch.optim.Optimizer
    update_zero_serialized: bytes
    initial_high_state: dict[str, dict[str, torch.Tensor]]
    final_high_state: dict[str, dict[str, torch.Tensor]]
    metrics: dict[str, Any]


def _training_checkpoint_counters(
    *,
    update_index: int,
    step_in_update: int,
    ppo_passes_in_update: int,
    num_envs: int,
) -> dict[str, int]:
    return {
        "update_index": int(update_index),
        "step_in_update": int(step_in_update),
        "ppo_passes_in_update": int(ppo_passes_in_update),
        "environment_transitions": (
            int(update_index) * int(num_envs) * HORIZON
            + int(step_in_update) * int(num_envs)
        ),
        "high_optimizer_steps": (
            int(update_index) * PPO_PASSES_PER_UPDATE
            + int(ppo_passes_in_update)
        ),
        "next_episode_id": (int(update_index) + 1) * int(num_envs),
        "episodes_completed": (
            int(update_index) * int(num_envs)
            + int(step_in_update == HORIZON) * int(num_envs)
        ),
    }


def train_learned_high(
    *,
    device: str | torch.device,
    num_envs: int,
    updates: int,
    checkpoint_path: str | Path | None = None,
    resume_payload: Mapping[str, Any] | None = None,
) -> LearnedTrainingArtifacts:
    if int(num_envs) <= 0 or int(updates) <= 0:
        raise ValueError("training counts must be positive")
    owner = make_model_owner(device)
    initial_state = clone_high_state(owner)
    update_zero_serialized = serialize_high_state(initial_state)
    optimizer = make_high_optimizer(owner)
    aggregate_audit: dict[str, bool] = {}
    first_logp_error = 0.0
    first_value_error = 0.0
    finite_updates = True
    high_rows = 0
    high_optimizer_steps = 0
    environment_transitions = 0
    last_checkpoint: dict[str, Any] | None = None
    start_update = 0
    training_episode_ledger: list[int] = []

    def finish_runtime(
        runtime: SuppliedExecutorVectorRuntime,
        *,
        update_index: int,
        passes_already: int = 0,
    ) -> None:
        nonlocal first_logp_error, first_value_error, finite_updates
        nonlocal high_rows, high_optimizer_steps, environment_transitions
        nonlocal last_checkpoint, training_episode_ledger
        if runtime.step_index < HORIZON:
            remaining = HORIZON - runtime.step_index
            runtime.advance(remaining)
            environment_transitions += remaining * int(num_envs)
        if not runtime.terminal:
            raise RuntimeError("full-horizon update did not reach terminal")
        _merge_boolean_audits(aggregate_audit, _runtime_contract_audit(runtime))
        packed: PackedEventHighPPOData = pack_event_high_ppo_data(runtime.cores)
        high_rows += len(packed.high)
        if int(passes_already) == 0:
            replay = event_high_ppo_losses_from_packed(packed)
            first_logp_error = max(
                first_logp_error, float(replay.high_logp_max_error)
            )
            first_value_error = max(
                first_value_error, float(replay.high_value_max_error)
            )
        final_metrics: dict[str, float] = {}
        for _pass in range(int(passes_already), PPO_PASSES_PER_UPDATE):
            final_metrics = apply_event_high_ppo_update(
                packed, high_optimizer=optimizer
            )
            high_optimizer_steps += 1
            finite_updates &= all(
                np.isfinite(float(value))
                for name, value in final_metrics.items()
                if name
                in {
                    "high_loss",
                    "high_policy_loss",
                    "high_value_loss",
                    "high_entropy",
                    "high_gradient_norm",
                }
            )
        counters = _training_checkpoint_counters(
            update_index=update_index,
            step_in_update=HORIZON,
            ppo_passes_in_update=PPO_PASSES_PER_UPDATE,
            num_envs=num_envs,
        )
        expected_active_ids = tuple(
            range(
                int(update_index) * int(num_envs),
                (int(update_index) + 1) * int(num_envs),
            )
        )
        if runtime.episode_ids != expected_active_ids:
            raise RuntimeError("training runtime episode IDs are not canonical")
        runtime.training_episode_ledger = list(
            range(counters["episodes_completed"])
        )
        training_episode_ledger = list(runtime.training_episode_ledger)
        last_checkpoint = high_only_checkpoint_payload(
            runtime,
            optimizer=optimizer,
            counters=counters,
        )
        if checkpoint_path is not None:
            atomic_torch_save(last_checkpoint, checkpoint_path)

    if resume_payload is not None:
        raw_counters = _validate_counters(
            dict(resume_payload.get("counters", {})),
            num_envs=int(num_envs),
            horizon=HORIZON,
        )
        diagnostics = dict(resume_payload.get("runtime_diagnostics", {}))
        resume_ids = tuple(
            range(
                raw_counters["update_index"] * int(num_envs),
                (raw_counters["update_index"] + 1) * int(num_envs),
            )
        )
        if tuple(
            int(value) for value in diagnostics.get("episode_ids", ())
        ) != resume_ids:
            raise ValueError("resume checkpoint episode/counter mismatch")
        resumed = SuppliedExecutorVectorRuntime.create(
            arm=LEARNED_HIGH_ARM,
            model_owner=owner,
            episode_ids=resume_ids,
            task_seed=TRAIN_TASK_SEED,
            deterministic_high=False,
        )
        restored_counters = restore_high_only_checkpoint(
            resume_payload,
            resumed,
            optimizer=optimizer,
        )
        training_episode_ledger = list(resumed.training_episode_ledger)
        update_index = restored_counters["update_index"]
        if update_index >= int(updates):
            raise ValueError("resume checkpoint lies beyond requested updates")
        high_optimizer_steps = (
            update_index * PPO_PASSES_PER_UPDATE
            + restored_counters["ppo_passes_in_update"]
        )
        environment_transitions = (
            update_index * int(num_envs) * HORIZON
            + restored_counters["step_in_update"] * int(num_envs)
        )
        finish_runtime(
            resumed,
            update_index=update_index,
            passes_already=restored_counters["ppo_passes_in_update"],
        )
        resumed.close()
        start_update = update_index + 1

    for update_index in range(start_update, int(updates)):
        episode_ids = tuple(
            range(
                update_index * int(num_envs),
                (update_index + 1) * int(num_envs),
            )
        )
        runtime = SuppliedExecutorVectorRuntime.create(
            arm=LEARNED_HIGH_ARM,
            model_owner=owner,
            episode_ids=episode_ids,
            task_seed=TRAIN_TASK_SEED,
            deterministic_high=False,
        )
        runtime.advance()
        environment_transitions += int(num_envs) * HORIZON
        finish_runtime(runtime, update_index=update_index)
        runtime.close()

    expected_steps = int(num_envs) * HORIZON * int(updates)
    expected_optimizer_steps = PPO_PASSES_PER_UPDATE * int(updates)
    if environment_transitions != expected_steps:
        raise RuntimeError("training transition count mismatch")
    if high_optimizer_steps != expected_optimizer_steps:
        raise RuntimeError("training high optimizer count mismatch")
    if training_episode_ledger != list(range(int(num_envs) * int(updates))):
        raise RuntimeError("training episode ledger is incomplete or non-canonical")
    low_gradients_absent = all(
        parameter.grad is None
        for module in (owner.low_actor, owner.low_critic)
        for parameter in module.parameters()
    )
    final_state = clone_high_state(owner)
    metrics = {
        "counts": {
            "environment_transitions": environment_transitions,
            "high_optimizer_steps": high_optimizer_steps,
            "low_optimizer_steps": 0,
            "low_rows": 0,
            "low_likelihood_evaluations": 0,
            "episodes": len(training_episode_ledger),
        },
        "episode_ids": list(training_episode_ledger),
        "first_pass_replay": {
            "high_logp_max_error": first_logp_error,
            "high_value_max_error": first_value_error,
        },
        "runtime_audit": aggregate_audit,
        "finite_updates": bool(finite_updates),
        "low_gradients_absent": bool(low_gradients_absent),
        "high_rows": int(high_rows),
        "learned_high_drift": high_state_l2_drift(initial_state, final_state),
        "last_checkpoint_present": last_checkpoint is not None,
    }
    return LearnedTrainingArtifacts(
        model_owner=owner,
        optimizer=optimizer,
        update_zero_serialized=update_zero_serialized,
        initial_high_state=initial_state,
        final_high_state=final_state,
        metrics=metrics,
    )


def executor_and_rng_audit() -> dict[str, bool]:
    executor = SuppliedSkillExecutor()
    numpy_before = deepcopy(np.random.get_state())
    torch_before = torch.get_rng_state().clone()
    mapped = executor({"idle": IDLE, "persist": PERSIST, "short": SHORT})
    numpy_after = np.random.get_state()
    torch_after = torch.get_rng_state()
    return {
        "executor_exact_identity": mapped
        == {"idle": IDLE, "persist": PERSIST, "short": SHORT},
        "executor_parameter_count_zero": executor.parameter_count() == 0
        and tuple(executor.parameters()) == (),
        "executor_consumes_no_numpy_rng": _recursive_equal(
            numpy_before, numpy_after
        ),
        "executor_consumes_no_torch_rng": torch.equal(
            torch_before, torch_after
        ),
    }


def classify_result(
    *,
    implementation_valid: bool,
    learned: Mapping[str, Any],
    frozen: Mapping[str, Any],
    oracle: Mapping[str, Any],
    learned_minus_frozen_utility_ci95: Sequence[float],
) -> str:
    if not implementation_valid:
        return "INVALID_CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0"
    if not (
        float(oracle["persistent_mean"]) >= 0.95
        and float(oracle["short_mean"]) >= 0.95
        and float(oracle["utility_mean"]) >= 0.95
    ):
        return "INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT"
    if (
        float(frozen["utility_mean"]) >= 0.60
        and float(frozen["persistent_mean"]) >= 0.55
        and float(frozen["short_mean"]) >= 0.55
    ):
        return "FROZEN_HIGH_SUFFICIENT_CLEAN_SUPPLIED_EXECUTOR"
    if (
        float(learned["utility_mean"]) >= 0.60
        and float(learned["persistent_mean"]) >= 0.55
        and float(learned["short_mean"]) >= 0.55
        and float(learned_minus_frozen_utility_ci95[0]) > 0.10
    ):
        return "PASS_CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0"
    return "VALID_FAIL_CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0"


def run_clean_supplied_executor_high_path(
    *,
    device: str | torch.device,
    num_envs: int,
    updates: int,
    eval_episodes: int,
    smoke: bool,
    checkpoint_path: str | Path | None = None,
    update_zero_path: str | Path | None = None,
    resume_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected_device = torch.device(device)
    if not smoke:
        if selected_device.type != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("formal supplied-executor evidence requires CUDA")
        if (
            int(num_envs) != FORMAL_NUM_ENVS
            or int(updates) != FORMAL_UPDATES
            or int(eval_episodes) != FORMAL_EVAL_EPISODES
        ):
            raise ValueError("formal supplied-executor counts are frozen")
    elif int(num_envs) <= 0 or int(updates) <= 0 or int(eval_episodes) <= 0:
        raise ValueError("smoke counts must be positive")

    carrier_audit = audit_clean_process_contract()
    executor_audit = executor_and_rng_audit()
    checkpoint_audit = checkpoint_roundtrip_audit(selected_device)
    training = train_learned_high(
        device=selected_device,
        num_envs=int(num_envs),
        updates=int(updates),
        checkpoint_path=checkpoint_path,
        resume_payload=resume_payload,
    )
    if update_zero_path is not None:
        atomic_bytes_save(training.update_zero_serialized, update_zero_path)
    update_zero_state = deserialize_high_state(training.update_zero_serialized)
    update_zero_equal = high_states_byte_equal(
        training.initial_high_state, update_zero_state
    )
    frozen_owner = make_model_owner(selected_device)
    load_high_state(frozen_owner, update_zero_state)
    frozen_loaded_equal = high_states_byte_equal(
        update_zero_state, clone_high_state(frozen_owner)
    )

    eval_ids = tuple(range(int(eval_episodes)))
    learned_eval = _evaluate_arm(
        arm=LEARNED_HIGH_ARM,
        high_state=training.final_high_state,
        episode_ids=eval_ids,
        batch_size=int(num_envs),
        device=selected_device,
    )
    frozen_eval = _evaluate_arm(
        arm=FROZEN_HIGH_ARM,
        high_state=update_zero_state,
        episode_ids=eval_ids,
        batch_size=int(num_envs),
        device=selected_device,
    )
    oracle_eval = _evaluate_arm(
        arm=ORACLE_ARM,
        high_state=update_zero_state,
        episode_ids=eval_ids,
        batch_size=int(num_envs),
        device=selected_device,
    )
    oracle_independent = oracle_tensor_independence_audit(
        training.update_zero_serialized,
        device=selected_device,
    )
    utility_difference = np.asarray(
        learned_eval["utility"], dtype=np.float64
    ) - np.asarray(frozen_eval["utility"], dtype=np.float64)
    paired_ci = paired_bootstrap_ci95(utility_difference)

    combined_runtime_audit: dict[str, bool] = {}
    for audit in (
        training.metrics["runtime_audit"],
        learned_eval["audit"],
        frozen_eval["audit"],
        oracle_eval["audit"],
    ):
        _merge_boolean_audits(combined_runtime_audit, audit)
    counts = training.metrics["counts"]
    formal_header = {
        "num_envs": FORMAL_NUM_ENVS,
        "horizon": FORMAL_HORIZON,
        "updates": FORMAL_UPDATES,
        "environment_transitions": FORMAL_TRANSITIONS,
        "ppo_passes_per_update": PPO_PASSES_PER_UPDATE,
        "high_optimizer_steps": FORMAL_HIGH_OPTIMIZER_STEPS,
        "low_optimizer_steps": 0,
        "evaluation_episodes_per_arm": FORMAL_EVAL_EPISODES,
        "training_episode_ids": [0, 3_999],
        "evaluation_episode_ids": [0, 255],
        "bootstrap_resamples": BOOTSTRAP_REPETITIONS,
    }
    m0 = {
        "clean_carrier_audit": all(bool(value) for value in carrier_audit.values()),
        **executor_audit,
        "zero_low_likelihood_rows_updates_gradients": (
            int(counts["low_likelihood_evaluations"]) == 0
            and int(counts["low_rows"]) == 0
            and int(counts["low_optimizer_steps"]) == 0
            and bool(training.metrics["low_gradients_absent"])
        ),
        "learned_frozen_update_zero_tensors_byte_equal": bool(
            update_zero_equal and frozen_loaded_equal
        ),
        "learned_only_nonzero_high_drift": (
            float(training.metrics["learned_high_drift"]) > 0.0
            and float(frozen_eval["high_tensor_drift"]) == 0.0
            and float(oracle_eval["high_tensor_drift"]) == 0.0
        ),
        "frozen_never_optimizer_step": int(frozen_eval["optimizer_steps"]) == 0,
        "oracle_high_tensor_independence": bool(oracle_independent),
        "formal_count_arithmetic": (
            FORMAL_NUM_ENVS * FORMAL_HORIZON * FORMAL_UPDATES
            == FORMAL_TRANSITIONS
            and PPO_PASSES_PER_UPDATE * FORMAL_UPDATES
            == FORMAL_HIGH_OPTIMIZER_STEPS
        ),
        "seed_contract_exact": SEED_CONTRACT
        == {
            "model": 57_057,
            "training_task": 67_057,
            "opportunity_frontier": 77_057,
            "opportunity_stream": 0,
            "frontier_stream": 1,
            "action": 87_057,
            "action_stream": 0,
            "evaluation_task": 97_057,
            "bootstrap": 107_057,
        },
        "actual_training_episode_ledger_exact": training.metrics["episode_ids"]
        == list(range(int(num_envs) * int(updates))),
        "paired_evaluation_episode_ledgers_exact": (
            learned_eval["episode_ids"]
            == frozen_eval["episode_ids"]
            == oracle_eval["episode_ids"]
            == list(eval_ids)
        ),
        "exact_optimizer_exposure": (
            int(counts["environment_transitions"])
            == int(num_envs) * HORIZON * int(updates)
            and int(counts["high_optimizer_steps"])
            == PPO_PASSES_PER_UPDATE * int(updates)
        ),
        "first_pass_high_replay": max(
            float(training.metrics["first_pass_replay"]["high_logp_max_error"]),
            float(training.metrics["first_pass_replay"]["high_value_max_error"]),
        )
        <= 1.0e-6,
        "finite_high_updates": bool(training.metrics["finite_updates"]),
        **combined_runtime_audit,
        **checkpoint_audit,
    }
    implementation_valid = all(bool(value) for value in m0.values())
    scientific_status = classify_result(
        implementation_valid=implementation_valid,
        learned=learned_eval,
        frozen=frozen_eval,
        oracle=oracle_eval,
        learned_minus_frozen_utility_ci95=paired_ci,
    )
    status = (
        scientific_status
        if not smoke or not implementation_valid
        else "SMOKE_COMPLETE"
    )
    return {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "package": PACKAGE_NAME,
        "status": status,
        "scientific_status": scientific_status if not smoke else None,
        "formal_evidence": not smoke,
        "implementation_valid": implementation_valid,
        "m0": m0,
        "m1": {
            "oracle": {
                "persistent_mean": oracle_eval["persistent_mean"],
                "short_mean": oracle_eval["short_mean"],
                "utility_mean": oracle_eval["utility_mean"],
            },
            "frozen": {
                "persistent_mean": frozen_eval["persistent_mean"],
                "short_mean": frozen_eval["short_mean"],
                "utility_mean": frozen_eval["utility_mean"],
            },
            "learned": {
                "persistent_mean": learned_eval["persistent_mean"],
                "short_mean": learned_eval["short_mean"],
                "utility_mean": learned_eval["utility_mean"],
            },
            "paired_learned_minus_frozen_utility_ci95": paired_ci,
        },
        "contract": {
            "formal": formal_header,
            "actual": {
                "num_envs": int(num_envs),
                "horizon": HORIZON,
                "updates": int(updates),
                "environment_transitions": int(
                    counts["environment_transitions"]
                ),
                "ppo_passes_per_update": PPO_PASSES_PER_UPDATE,
                "high_optimizer_steps": int(counts["high_optimizer_steps"]),
                "evaluation_episodes_per_arm": int(eval_episodes),
            },
            "seed_contract": deepcopy(SEED_CONTRACT),
            "arms": list(ARMS),
            "runtime_mode": SUPPLIED_EXECUTOR_RUNTIME,
            "architecture_mode": "f1",
            "n_skills": ACTION_COUNT,
            "primitive_mapping": {
                "0": "IDLE",
                "1": "PERSIST",
                "2": "SHORT",
            },
            "optimizer": {
                "members": ["EventCommitmentPolicy", "EventHighCritic"],
                "learning_rate": HIGH_LEARNING_RATE,
                "low_policy_present": False,
            },
        },
        "carrier_audit": carrier_audit,
        "training": training.metrics,
        "evaluation": {
            "learned": learned_eval,
            "frozen": frozen_eval,
            "oracle": oracle_eval,
        },
        "thresholds": {
            "oracle_persistent_short_utility_min": 0.95,
            "frozen_utility_min": 0.60,
            "frozen_persistent_short_min": 0.55,
            "learned_utility_min": 0.60,
            "learned_persistent_short_min": 0.55,
            "learned_minus_frozen_utility_lcb95_exclusive": 0.10,
            "first_pass_replay_max": 1.0e-6,
        },
        "runner_selects_successor": False,
    }
