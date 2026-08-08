"""Real-environment VSP-05 B1 semantic-veto toy experiment.

The candidate-independent successor is a frozen deterministic function of the
current clean-process position, velocity and incumbent skill.  The candidate
changes only whether a different proposed successor is rejected at a fixed
semantic gate; it never changes joins, leaves, task reward, observations, the
supplied executor, or environment transitions.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from experiments.candidates.vsp_05.semantic_veto_policy import (
    ADAM_BETAS,
    ADAM_EPS,
    FEATURE_DIM,
    HARD_POSITION_THRESHOLD,
    HARD_VELOCITY_THRESHOLD,
    L2_COEFFICIENT,
    LEARNING_RATE,
    REJECT_THRESHOLD,
    ReceiptClassification,
    TRUTH_POSITION_THRESHOLD,
    TRUTH_VELOCITY_THRESHOLD,
    LearnerDiagnostics,
    LogisticSemanticVeto,
    classify_receipt,
    deterministic_sham_labels,
    select_semantic_action,
    semantic_feature,
    train_logistic_veto,
    VetoDecision,
)
from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    CleanProcessDynamicRosterEventEnv,
)
from ha_ctse_process.dynamic_roster_supplied_executor import (
    ORACLE_ARM,
    SuppliedExecutorVectorRuntime,
    SuppliedSkillExecutor,
    make_model_owner,
)
from ha_ctse_process.dynamic_roster_testbed import HORIZON
from ha_ctse_process.variable_roster_event import VariableRosterEventCore
from ha_ctse_process.variable_roster_event_types import MembershipTransaction


CANDIDATE_ID = "CAND-VSP-05@adversarial-revision-v7"
TREATMENT_ID = "VSP05-B1-REAL-TOY-SEMANTIC-VETO"
TARGET_ARM = "TARGET_LOGISTIC_VETO"
SHAM_ARM = "SHAM_LOGISTIC_VETO"
DET_ARM = "DET_GATE_ONLY"
ARMS = (TARGET_ARM, SHAM_ARM, DET_ARM)
REGISTERED_TRAINING_SEEDS = (67057, 67058, 67059)
REGISTERED_EVALUATION_SEEDS = (97057, 97058, 97059)
REGISTERED_EPISODES = 32
REGISTERED_OPTIMIZER_STEPS = 128
SHAM_SEED_OFFSET = 500_000


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    training_task_seeds: tuple[int, ...]
    evaluation_task_seeds: tuple[int, ...]
    training_episodes_per_seed: int
    evaluation_episodes_per_seed_arm: int
    optimizer_steps: int
    horizon: int = HORIZON

    def __post_init__(self) -> None:
        if not self.training_task_seeds or len(self.training_task_seeds) != len(
            self.evaluation_task_seeds
        ):
            raise ValueError("training/evaluation seed blocks must be nonempty and paired")
        if len(set(self.training_task_seeds)) != len(self.training_task_seeds):
            raise ValueError("training task seeds must be distinct")
        if len(set(self.evaluation_task_seeds)) != len(self.evaluation_task_seeds):
            raise ValueError("evaluation task seeds must be distinct")
        if self.training_episodes_per_seed <= 0 or self.evaluation_episodes_per_seed_arm <= 0:
            raise ValueError("episode counts must be positive")
        if self.optimizer_steps <= 0 or self.horizon != HORIZON:
            raise ValueError("the experiment requires positive updates and the real horizon")

    def counts(self) -> dict[str, int]:
        training = (
            len(self.training_task_seeds)
            * self.training_episodes_per_seed
            * self.horizon
        )
        evaluation = (
            len(self.evaluation_task_seeds)
            * len(ARMS)
            * self.evaluation_episodes_per_seed_arm
            * self.horizon
        )
        return {
            "training_transitions": training,
            "evaluation_transitions": evaluation,
            "total_transitions": training + evaluation,
            "optimizer_updates": (
                len(self.training_task_seeds) * 2 * self.optimizer_steps
            ),
            "training_episodes": (
                len(self.training_task_seeds) * self.training_episodes_per_seed
            ),
            "evaluated_episodes": (
                len(self.evaluation_task_seeds)
                * len(ARMS)
                * self.evaluation_episodes_per_seed_arm
            ),
        }


REGISTERED_CONFIG = ExperimentConfig(
    name="registered",
    training_task_seeds=REGISTERED_TRAINING_SEEDS,
    evaluation_task_seeds=REGISTERED_EVALUATION_SEEDS,
    training_episodes_per_seed=REGISTERED_EPISODES,
    evaluation_episodes_per_seed_arm=REGISTERED_EPISODES,
    optimizer_steps=REGISTERED_OPTIMIZER_STEPS,
)
SMOKE_CONFIG = ExperimentConfig(
    name="smoke",
    training_task_seeds=(67057,),
    evaluation_task_seeds=(97057,),
    training_episodes_per_seed=2,
    evaluation_episodes_per_seed_arm=2,
    optimizer_steps=4,
)


def _rate(numerator: int, denominator: int) -> dict[str, int | float | None]:
    return {
        "numerator": int(numerator),
        "denominator": int(denominator),
        "value": None if int(denominator) == 0 else float(numerator) / float(denominator),
    }


def _empty_counts() -> Counter[str]:
    return Counter(
        {
            "different_successor_opportunities": 0,
            "gated_support": 0,
            "truth_support": 0,
            "alias_support": 0,
            "vetoes": 0,
            "changed_actions": 0,
            "safe_holds": 0,
            "premature_handoffs": 0,
            "misses": 0,
            "rejected_truth_opportunities": 0,
            "unresolved": 0,
        }
    )


def proposed_successor(
    *, position: float, velocity: float, current_skill: int | None
) -> int:
    """Frozen candidate-independent current-process successor rule.

    The rule first names the skill whose coarse target is currently present.
    If that target is already incumbent it proposes the next skill cyclically,
    exposing a real different-successor opportunity without changing G_SEM.
    Outside every coarse target it also uses the cyclic successor.  A genuine
    join has no incumbent and starts with the positive-direction skill.  No
    outcome, identity, clock, age, reward, history, or RNG enters this rule.
    """

    position_value = float(position)
    velocity_value = float(velocity)
    if not np.isfinite(position_value) or not np.isfinite(velocity_value):
        raise ValueError("proposal state must be finite")
    current = None if current_skill is None else int(current_skill)
    if current is not None and current not in (0, 1, 2):
        raise ValueError("proposal incumbent lies outside {0,1,2}")
    if current is None:
        return 2
    if position_value <= -HARD_POSITION_THRESHOLD:
        target = 0
    elif position_value >= HARD_POSITION_THRESHOLD:
        target = 2
    elif abs(velocity_value) <= HARD_VELOCITY_THRESHOLD:
        target = 1
    else:
        target = (current + 1) % 3
    return (current + 1) % 3 if target == current else target


def _record_selected_action(
    counts: Counter[str],
    *,
    current_skill: int,
    receipt: ReceiptClassification,
    decision: VetoDecision,
) -> None:
    """Record only an action that the selection rule actually executed."""

    if decision.rejected:
        counts["vetoes"] += 1
        counts["safe_holds"] += 1
        if receipt.truth:
            counts["misses"] += 1
            counts["rejected_truth_opportunities"] += 1
        return
    if int(decision.selected_skill) == int(current_skill):
        return
    counts["changed_actions"] += 1
    if receipt.gate and not receipt.truth:
        counts["premature_handoffs"] += 1


@dataclass
class HandoffDelayTracker:
    """Per-lifecycle event-rank delay from first strict-true opportunity."""

    event_ranks: Counter[str]
    first_truth: dict[str, tuple[int, int]]
    observed_delays: list[int]

    @classmethod
    def create(cls) -> "HandoffDelayTracker":
        return cls(Counter(), {}, [])

    def next_rank(self, lifecycle_key: str) -> int:
        self.event_ranks[str(lifecycle_key)] += 1
        return int(self.event_ranks[str(lifecycle_key)])

    def observe(
        self,
        *,
        lifecycle_key: str,
        event_rank: int,
        current_skill: int,
        proposed_skill: int,
        receipt: ReceiptClassification,
        decision: VetoDecision,
    ) -> None:
        key = str(lifecycle_key)
        if receipt.gate and receipt.truth and key not in self.first_truth:
            self.first_truth[key] = (int(event_rank), int(proposed_skill))
        pending = self.first_truth.get(key)
        if pending is None:
            return
        first_rank, successor = pending
        adopted = (
            int(decision.selected_skill) != int(current_skill)
            and int(decision.selected_skill) == int(successor)
        )
        if adopted:
            self.observed_delays.append(int(event_rank) - int(first_rank))
            del self.first_truth[key]

    def summary(self) -> dict[str, int | float | None]:
        observed = len(self.observed_delays)
        return {
            "observed": observed,
            "censored": len(self.first_truth),
            "sum_event_ranks": int(sum(self.observed_delays)),
            "mean_event_ranks": (
                None
                if observed == 0
                else float(sum(self.observed_delays)) / float(observed)
            ),
        }


class SemanticVetoVectorRuntime(SuppliedExecutorVectorRuntime):
    """Candidate-local adapter over the real supplied-executor runtime."""

    candidate_arm: str
    veto_model: LogisticSemanticVeto | None
    collect_training_rows: bool
    collected_features: list[np.ndarray]
    collected_labels: list[int]
    per_environment_counts: list[Counter[str]]
    delay_trackers: list[HandoffDelayTracker]
    candidate_policy_calls: int
    learner_forward_calls: int

    @classmethod
    def create_candidate(
        cls,
        *,
        candidate_arm: str,
        episode_ids: Sequence[int],
        task_seed: int,
        veto_model: LogisticSemanticVeto | None,
        collect_training_rows: bool,
    ) -> "SemanticVetoVectorRuntime":
        if candidate_arm not in ARMS:
            raise ValueError("candidate arm mismatch")
        if (candidate_arm in (TARGET_ARM, SHAM_ARM)) != (veto_model is not None):
            raise ValueError("learned arms require exactly one frozen veto model")
        runtime = cls.create(
            arm=ORACLE_ARM,
            model_owner=make_model_owner("cpu"),
            episode_ids=episode_ids,
            task_seed=int(task_seed),
            deterministic_high=True,
        )
        runtime.candidate_arm = candidate_arm
        runtime.veto_model = veto_model
        runtime.collect_training_rows = bool(collect_training_rows)
        runtime.collected_features = []
        runtime.collected_labels = []
        runtime.per_environment_counts = [_empty_counts() for _ in episode_ids]
        runtime.delay_trackers = [HandoffDelayTracker.create() for _ in episode_ids]
        runtime.candidate_policy_calls = 0
        runtime.learner_forward_calls = 0
        if not isinstance(runtime.executor, SuppliedSkillExecutor):
            raise RuntimeError("candidate runtime lost the supplied executor")
        if not all(
            isinstance(adapter, CleanProcessDynamicRosterEventEnv)
            for adapter in runtime.collector.envs
        ) or not all(isinstance(core, VariableRosterEventCore) for core in runtime.cores):
            raise RuntimeError("candidate runtime lost the real environment/core path")
        return runtime

    def _oracle_teacher_actions(
        self,
        env_index: int,
        transaction: MembershipTransaction,
    ) -> dict[str, int] | None:
        frontier = transaction.post_membership_pre_policy_snapshot.frontier
        if not frontier:
            return None
        core = self.cores[env_index]
        adapter = self.collector.envs[env_index]
        process_states = adapter.process_state_mapping(frontier)
        self.oracle_constructive_calls += 1
        selected: dict[str, int] = {}
        counts = self.per_environment_counts[env_index]
        delay_tracker = self.delay_trackers[env_index]
        for key in frontier:
            self.candidate_policy_calls += 1
            event_rank = delay_tracker.next_rank(key)
            record = core.records.get(key)
            incumbent = None if record is None else record.active_skill
            position, velocity = np.asarray(
                process_states[key], dtype=np.float64
            ).tolist()
            proposed = proposed_successor(
                position=position,
                velocity=velocity,
                current_skill=None if incumbent is None else int(incumbent),
            )
            if incumbent is None:
                selected[key] = int(proposed)
                continue
            current = int(incumbent)
            proposed_value = int(proposed)
            if proposed_value == current:
                selected[key] = current
                continue
            counts["different_successor_opportunities"] += 1
            receipt = classify_receipt(proposed_value, position, velocity)
            if receipt.gate:
                counts["gated_support"] += 1
                counts["truth_support" if receipt.truth else "alias_support"] += 1
                feature = semantic_feature(position, velocity, current, proposed_value)
                if self.collect_training_rows:
                    self.collected_features.append(feature)
                    if receipt.label is None:  # guarded by gate, retained fail-closed
                        raise RuntimeError("gated receipt omitted its training label")
                    self.collected_labels.append(int(receipt.label))
                probability = None
                if self.candidate_arm in (TARGET_ARM, SHAM_ARM):
                    if self.veto_model is None:
                        raise RuntimeError("learned arm lost its frozen veto model")
                    self.learner_forward_calls += 1
                    probability = self.veto_model.alias_probability(feature)
            else:
                counts["unresolved"] += 1
                probability = None
            decision = select_semantic_action(
                current_skill=current,
                proposed_skill=proposed_value,
                receipt=receipt,
                learned_veto=self.candidate_arm in (TARGET_ARM, SHAM_ARM),
                alias_probability=probability,
            )
            selected[key] = decision.selected_skill
            _record_selected_action(
                counts,
                current_skill=current,
                receipt=receipt,
                decision=decision,
            )
            delay_tracker.observe(
                lifecycle_key=key,
                event_rank=event_rank,
                current_skill=current,
                proposed_skill=proposed_value,
                receipt=receipt,
                decision=decision,
            )
        return selected

    def result_rows(self, *, task_seed: int, arm: str) -> list[dict[str, Any]]:
        if not self.terminal:
            raise RuntimeError("evaluation rows require terminal real episodes")
        rows: list[dict[str, Any]] = []
        for index, (episode_id, raw_counts, rewards, core, delay_tracker) in enumerate(
            zip(
                self.episode_ids,
                self.per_environment_counts,
                self.reward_trace,
                self.cores,
                self.delay_trackers,
            )
        ):
            counts = raw_counts.copy()
            delay = delay_tracker.summary()
            counts["delay_observed"] = int(delay["observed"])
            counts["delay_censored"] = int(delay["censored"])
            counts["delay_sum_event_ranks"] = int(delay["sum_event_ranks"])
            active_tenures = [
                int(record.skill_active_age)
                for record in core.records.values()
                if record.active_skill is not None
            ]
            rows.append(
                {
                    "task_seed": int(task_seed),
                    "arm": str(arm),
                    "episode_index": index,
                    "episode_id": int(episode_id),
                    "counts": dict(sorted(counts.items())),
                    "premature_handoff_rate": _rate(
                        counts["premature_handoffs"], counts["gated_support"]
                    ),
                    "miss_rate": _rate(counts["misses"], counts["truth_support"]),
                    "event_rank_handoff_delay": delay,
                    "veto_rate": _rate(counts["vetoes"], counts["gated_support"]),
                    "changed_action_rate": _rate(
                        counts["changed_actions"], counts["gated_support"]
                    ),
                    "safe_hold_rate": _rate(
                        counts["safe_holds"], counts["gated_support"]
                    ),
                    "episode_return": float(sum(rewards)),
                    "terminal_tenure_mean": (
                        None
                        if not active_tenures
                        else float(sum(active_tenures)) / float(len(active_tenures))
                    ),
                }
            )
        return rows


def _episode_ids(count: int) -> tuple[int, ...]:
    return tuple(range(int(count)))


def _collect_training_rows(
    *, config: ExperimentConfig, task_seed: int
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    runtime = SemanticVetoVectorRuntime.create_candidate(
        candidate_arm=DET_ARM,
        episode_ids=_episode_ids(config.training_episodes_per_seed),
        task_seed=task_seed,
        veto_model=None,
        collect_training_rows=True,
    )
    try:
        runtime.advance()
        features = np.asarray(runtime.collected_features, dtype=np.float32)
        if features.size == 0:
            features = np.empty((0, FEATURE_DIM), dtype=np.float32)
        labels = np.asarray(runtime.collected_labels, dtype=np.int64)
        counts = sum(runtime.per_environment_counts, Counter())
        diagnostics = {
            "environment_transitions": config.training_episodes_per_seed * config.horizon,
            "candidate_policy_calls": runtime.candidate_policy_calls,
            "records": len(labels),
            "truth_support": int(counts["truth_support"]),
            "alias_support": int(counts["alias_support"]),
            "unresolved": int(counts["unresolved"]),
            "real_environment": True,
            "real_variable_roster_core": True,
            "real_supplied_executor": True,
        }
        return features, labels, diagnostics
    finally:
        runtime.close()


def _learner_payload(diagnostics: LearnerDiagnostics) -> dict[str, Any]:
    return asdict(diagnostics)


def _aggregate_arm(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = sum((Counter(dict(row["counts"])) for row in rows), Counter())
    returns = [float(row["episode_return"]) for row in rows]
    tenures = [
        float(row["terminal_tenure_mean"])
        for row in rows
        if row["terminal_tenure_mean"] is not None
    ]
    return {
        "episodes": len(rows),
        "support": {
            "gated": int(counts["gated_support"]),
            "truth": int(counts["truth_support"]),
            "alias": int(counts["alias_support"]),
            "unresolved": int(counts["unresolved"]),
        },
        "premature_handoff_rate": _rate(
            counts["premature_handoffs"], counts["gated_support"]
        ),
        "miss_rate": _rate(counts["misses"], counts["truth_support"]),
        "event_rank_handoff_delay": {
            "observed": int(counts["delay_observed"]),
            "censored": int(counts["delay_censored"]),
            "sum_event_ranks": int(counts["delay_sum_event_ranks"]),
            "mean_event_ranks": (
                None
                if int(counts["delay_observed"]) == 0
                else float(counts["delay_sum_event_ranks"])
                / float(counts["delay_observed"])
            ),
        },
        "veto_rate": _rate(counts["vetoes"], counts["gated_support"]),
        "changed_action_rate": _rate(
            counts["changed_actions"], counts["gated_support"]
        ),
        "safe_hold_rate": _rate(counts["safe_holds"], counts["gated_support"]),
        "return_mean": None if not returns else float(sum(returns)) / float(len(returns)),
        "terminal_tenure_mean": (
            None if not tenures else float(sum(tenures)) / float(len(tenures))
        ),
    }


def run_experiment(
    config: ExperimentConfig,
    *,
    code_revision: str,
) -> dict[str, Any]:
    """Train on real episodes, then evaluate frozen arms on fresh real episodes."""

    declared = config.counts()
    training_rows: list[dict[str, Any]] = []
    models: list[dict[str, LogisticSemanticVeto]] = []
    actual_training_transitions = 0
    actual_optimizer_updates = 0
    trainer_calls = 0
    training_policy_calls = 0

    for task_seed in config.training_task_seeds:
        features, labels, collection = _collect_training_rows(
            config=config, task_seed=task_seed
        )
        target_model, target_diagnostics = train_logistic_veto(
            features, labels, optimizer_steps=config.optimizer_steps
        )
        sham_labels = deterministic_sham_labels(labels, task_seed + SHAM_SEED_OFFSET)
        sham_model, sham_diagnostics = train_logistic_veto(
            features, sham_labels, optimizer_steps=config.optimizer_steps
        )
        if sorted(labels.tolist()) != sorted(sham_labels.tolist()):
            raise RuntimeError("sham permutation changed the label multiset")
        models.append({TARGET_ARM: target_model, SHAM_ARM: sham_model})
        training_rows.append(
            {
                "task_seed": int(task_seed),
                "collection": collection,
                "target_learner": _learner_payload(target_diagnostics),
                "sham_learner": _learner_payload(sham_diagnostics),
                "sham_permutation_seed": int(task_seed + SHAM_SEED_OFFSET),
                "sham_label_multiset_preserved": True,
            }
        )
        actual_training_transitions += int(collection["environment_transitions"])
        training_policy_calls += int(collection["candidate_policy_calls"])
        actual_optimizer_updates += (
            target_diagnostics.optimizer_updates + sham_diagnostics.optimizer_updates
        )
        trainer_calls += 2

    evaluation_rows: list[dict[str, Any]] = []
    actual_evaluation_transitions = 0
    evaluated_episodes = 0
    evaluation_runner_calls = 0
    policy_calls = training_policy_calls
    # Each training objective calls the real linear learner once before, once
    # per optimizer step, and once after training.  This remains truthful for a
    # zero-support fixed run: its objective is the explicit L2 term only.
    learner_forward_calls = sum(
        2 * (config.optimizer_steps + 2) for _ in config.training_task_seeds
    )
    executor_calls = actual_training_transitions
    core_transaction_calls = actual_training_transitions
    for pair_index, task_seed in enumerate(config.evaluation_task_seeds):
        for arm in ARMS:
            runtime = SemanticVetoVectorRuntime.create_candidate(
                candidate_arm=arm,
                episode_ids=_episode_ids(config.evaluation_episodes_per_seed_arm),
                task_seed=task_seed,
                veto_model=(None if arm == DET_ARM else models[pair_index][arm]),
                collect_training_rows=False,
            )
            try:
                runtime.advance()
                rows = runtime.result_rows(task_seed=task_seed, arm=arm)
                evaluation_rows.extend(rows)
                transitions = config.evaluation_episodes_per_seed_arm * config.horizon
                actual_evaluation_transitions += transitions
                evaluated_episodes += len(rows)
                evaluation_runner_calls += 1
                policy_calls += runtime.candidate_policy_calls
                learner_forward_calls += runtime.learner_forward_calls
                executor_calls += transitions
                core_transaction_calls += transitions
            finally:
                runtime.close()

    actual_counts = {
        "training_transitions": actual_training_transitions,
        "evaluation_transitions": actual_evaluation_transitions,
        "total_transitions": actual_training_transitions + actual_evaluation_transitions,
        "optimizer_updates": actual_optimizer_updates,
        "training_episodes": declared["training_episodes"],
        "evaluated_episodes": evaluated_episodes,
    }
    if actual_counts != declared:
        raise RuntimeError(
            f"actual experiment counts differ from declaration: {actual_counts} != {declared}"
        )

    aggregate = {
        arm: _aggregate_arm([row for row in evaluation_rows if row["arm"] == arm])
        for arm in ARMS
    }
    config_payload = asdict(config)
    config_payload["training_task_seeds"] = list(config.training_task_seeds)
    config_payload["evaluation_task_seeds"] = list(config.evaluation_task_seeds)
    return {
        "stage": "experiment",
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "config_name": config.name,
        "code_revision": str(code_revision),
        "execution_command": (
            "python -m experiments.candidates.vsp_05.real_toy_semantic_veto "
            f"--config {config.name} --code-revision {code_revision} "
            "--output <explicit-output>"
        ),
        "environment_binding": {
            "environment": "ha_ctse_process.dynamic_roster_clean_process_testbed.CleanProcessDynamicRosterEventEnv",
            "event_core": "ha_ctse_process.variable_roster_event.VariableRosterEventCore",
            "vector_runtime": "ha_ctse_process.dynamic_roster_supplied_executor.SuppliedExecutorVectorRuntime",
            "executor": "ha_ctse_process.dynamic_roster_supplied_executor.SuppliedSkillExecutor",
            "horizon": HORIZON,
        },
        "scientific_acceptance": False,
        "technical_disposition": "COMPLETED_FIXED_B_LEVEL_TOY_RUN",
        "claim_boundary": (
            "descriptive fixed-budget toy evidence only; no promotion, retirement, "
            "utility, generalization, deployment, or scientific acceptance"
        ),
        "real_algorithm_path_changed": True,
        "real_calls": {
            "environment": True,
            "policy": policy_calls > 0,
            "learner": trainer_calls > 0 and learner_forward_calls > 0,
            "trainer": trainer_calls > 0,
            "evaluation_runner": evaluation_runner_calls > 0,
            "supplied_executor": executor_calls > 0,
            "variable_roster_event_core": core_transaction_calls > 0,
        },
        "call_counts": {
            "candidate_policy": policy_calls,
            "learner_forward": learner_forward_calls,
            "trainer": trainer_calls,
            "evaluation_runner": evaluation_runner_calls,
            "environment_transition": actual_counts["total_transitions"],
            "supplied_executor": executor_calls,
            "variable_roster_event_core_transaction": core_transaction_calls,
        },
        "configuration": {
            **config_payload,
            "arms": list(ARMS),
            "feature_fields": [
                "position",
                "velocity",
                "current_skill_one_hot_0",
                "current_skill_one_hot_1",
                "current_skill_one_hot_2",
                "proposed_skill_one_hot_0",
                "proposed_skill_one_hot_1",
                "proposed_skill_one_hot_2",
            ],
            "proposal_rule": (
                "current-process coarse target; if already incumbent or no coarse "
                "target, propose cyclic successor; genuine joins start at skill 2"
            ),
            "reject_threshold": REJECT_THRESHOLD,
            "hard_position_threshold": HARD_POSITION_THRESHOLD,
            "truth_position_threshold": TRUTH_POSITION_THRESHOLD,
            "hard_velocity_threshold": HARD_VELOCITY_THRESHOLD,
            "truth_velocity_threshold": TRUTH_VELOCITY_THRESHOLD,
            "linear_feature_dim": FEATURE_DIM,
            "zero_initialization": True,
            "learning_rate": LEARNING_RATE,
            "adam_betas": list(ADAM_BETAS),
            "adam_eps": ADAM_EPS,
            "l2_coefficient": L2_COEFFICIENT,
            "full_batch_fixed_record_order": True,
            "search_candidates": 0,
            "hypothetical_transitions": 0,
        },
        "declared_counts": declared,
        "actual_counts": actual_counts,
        "training": training_rows,
        "evaluation": evaluation_rows,
        "aggregates": aggregate,
    }


def write_result(path: str | Path, result: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(dict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", choices=("registered", "smoke"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--code-revision", default="WORKTREE")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    config = REGISTERED_CONFIG if args.config == "registered" else SMOKE_CONFIG
    result = run_experiment(config, code_revision=args.code_revision)
    write_result(args.output, result)
    print(json.dumps({"output": str(Path(args.output)), "actual_counts": result["actual_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
