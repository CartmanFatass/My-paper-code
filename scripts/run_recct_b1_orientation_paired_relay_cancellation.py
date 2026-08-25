"""Train, evaluate, and analyze RECCT-B1 orientation-paired relay cancellation.

The default lifecycle is a reduced ``technical_only`` exercise whose analysis
suppresses every scientific branch.  The unique full schedule is available
only through an explicit ``--full`` train invocation with a source identity
and CPM authorization token; this module never retries, sweeps, rescues,
selects checkpoints, or adds seeds or arms.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np
import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from experiments.candidates.recct_lite import orientation_paired_relay_cancellation as recct
from experiments.candidates.recct_lite import orientation_paired_relay_host as host


ALGORITHM_ID = "RECCT-B1-ORIENTATION-PAIRED-RELAY-CANCELLATION-V1"
FULL_AUTHORIZATION_TOKEN = "RECCT-B1-UNIQUE-FULL-AUTHORIZED"
MASTER_SEEDS = (1701, 1702, 1703, 1704)
EVALUATION_SEEDS = tuple(range(9701, 9717))
FULL_ACTIVITY_CAPS = {
    "named_full_runs": 1,
    "train_episodes": 1024,
    "evaluation_episodes": 512,
    "joint_environment_transitions_train": 32768,
    "joint_environment_transitions_evaluation": 16384,
    "joint_environment_transitions_total": 49152,
    "policy_calls_train": 81920,
    "policy_calls_evaluation": 40960,
    "policy_calls_total": 122880,
    "committed_live_updates": 1024,
    "pure_shadow_transition_calls": 4096,
    "learner_update_calls": 5120,
    "optimizer_transition_calls": 5120,
    "model_fits": 32,
    "sweeps_retries_rescues_early_stops": 0,
}
BRANCH_PRECEDENCE = (
    "B_NOT_RUN_READINESS_FAILURE",
    "B_CONTRACT_OR_ACTIVITY_INVALID",
    "B_INFORMATION_LEAKAGE_OR_SPLIT_INVALID",
    "B_HOST_GEOMETRY_NONIDENTIFYING",
    "B_RESOURCE_OR_UPDATE_NORM_CONFOUNDED",
    "B_DIRECTION_INSENSITIVE_MASKING",
    "B_GENERIC_SPARSIFICATION_EQUIVALENCE",
    "B_FINITE_LOOKUP_OR_ROSTER_NONTRANSFER",
    "B_DIRECTED_SELECTION_WITHOUT_UTILITY",
    "B_DIRECTED_CREDIT_EXPLORATORY_SIGNAL",
    "B_NULL_OR_ADVERSE_SIGNAL",
)
TECHNICAL_ONLY_BRANCH = "TECHNICAL_ONLY_SCIENTIFIC_BRANCH_SUPPRESSED"


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _artifact_digest(path: Path) -> str:
    return _digest_bytes(path.read_bytes())


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


@dataclass(frozen=True)
class RunConfiguration:
    technical_only: bool
    master_seeds: tuple[int, ...]
    arms: tuple[str, ...]
    orientation_replicas: tuple[int, ...]
    train_episodes_per_replica: int
    evaluation_seeds: tuple[int, ...]
    training_pool: tuple[str, ...] = host.TRAINING_POOL
    evaluation_pool: tuple[str, ...] = host.EVALUATION_POOL

    @classmethod
    def full(cls) -> "RunConfiguration":
        return cls(False, MASTER_SEEDS, recct.ARMS, (1, -1), 32, EVALUATION_SEEDS)

    @classmethod
    def technical(cls) -> "RunConfiguration":
        return cls(True, (1701,), recct.ARMS, (1, -1), 1, (9701,))

    def validate(self) -> None:
        if (
            self.arms != recct.ARMS
            or self.orientation_replicas != (1, -1)
            or set(self.training_pool).intersection(self.evaluation_pool)
            or len(self.training_pool) != 8
            or len(self.evaluation_pool) != 8
        ):
            raise ValueError("run configuration changed arms, pairing, or split")
        if self.technical_only:
            if (
                self.master_seeds != (1701,)
                or self.train_episodes_per_replica != 1
                or self.evaluation_seeds != (9701,)
            ):
                raise ValueError("technical-only lifecycle left its reduced fixture")
        elif self != RunConfiguration.full():
            raise ValueError("full lifecycle differs from the frozen schedule")


@dataclass(frozen=True)
class ValidatedUpdate:
    episode_index: int
    episode_seed: int
    omega: int
    exogenous_digest: str
    selected_mask: str
    direction_code: int
    committed_update_l2_norm: float
    optimizer_moment_delta_norm: float
    clipping_indicator: bool
    active_port_count: int
    factorial_gradient_residual: float
    fresh_commit_matches_selected_shadow: bool
    shadow_calls: int
    learner_calls: int
    optimizer_transitions: int


@dataclass(frozen=True)
class ValidatedFit:
    arm: str
    master_seed: int
    orientation_replica: int
    updates: tuple[ValidatedUpdate, ...]
    checkpoint: str


@dataclass(frozen=True)
class ValidatedEvaluationEpisode:
    evaluation_seed: int
    omega: int
    exogenous_digest: str
    episode_metric: float


@dataclass(frozen=True)
class ValidatedEvaluationCell:
    arm: str
    master_seed: int
    orientation_replica: int
    episodes: tuple[ValidatedEvaluationEpisode, ...]
    checkpoint: str


@dataclass(frozen=True)
class ValidatedRetainedArtifacts:
    configuration: RunConfiguration
    fits: tuple[ValidatedFit, ...]
    cells: tuple[ValidatedEvaluationCell, ...]
    activity_counts: Mapping[str, int]
    readiness: bool
    host_geometry_identifying: bool


class SiteKeyedRNG:
    """Order-insensitive RNG; each semantic call site has an explicit counter."""

    def __init__(self, seed: int) -> None:
        self.seed = int(seed)
        self.counters: dict[str, int] = {}

    def uniform(self, site: str) -> float:
        if not site or "seed" in site.lower() or "orientation" in site.lower():
            raise ValueError("RNG site must be semantic and outcome-free")
        counter = self.counters.get(site, 0)
        self.counters[site] = counter + 1
        payload = _json_bytes((self.seed, site, counter))
        integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
        return (integer + 0.5) / float(2**64)


def _counts(configuration: RunConfiguration) -> dict[str, int]:
    fits = (
        len(configuration.master_seeds)
        * len(configuration.arms)
        * len(configuration.orientation_replicas)
    )
    train_episodes = fits * configuration.train_episodes_per_replica
    evaluation_episodes = fits * len(configuration.evaluation_seeds)
    train_transitions = train_episodes * host.JOINT_STEPS
    evaluation_transitions = evaluation_episodes * host.JOINT_STEPS
    policy_calls_per_episode = sum(host.ACTIVE_COUNT_BY_EPOCH) * host.PHASES_PER_EPOCH
    return {
        "named_full_runs": 0 if configuration.technical_only else 1,
        "train_episodes": train_episodes,
        "evaluation_episodes": evaluation_episodes,
        "joint_environment_transitions_train": train_transitions,
        "joint_environment_transitions_evaluation": evaluation_transitions,
        "joint_environment_transitions_total": train_transitions + evaluation_transitions,
        "policy_calls_train": train_episodes * policy_calls_per_episode,
        "policy_calls_evaluation": evaluation_episodes * policy_calls_per_episode,
        "policy_calls_total": (train_episodes + evaluation_episodes) * policy_calls_per_episode,
        "committed_live_updates": train_episodes,
        "pure_shadow_transition_calls": train_episodes * 4,
        "learner_update_calls": train_episodes * 5,
        "optimizer_transition_calls": train_episodes * 5,
        "model_fits": fits,
        "sweeps_retries_rescues_early_stops": 0,
    }


def _sample_action(logits: torch.Tensor, rng: SiteKeyedRNG, site: str) -> torch.Tensor:
    probabilities = torch.softmax(logits.detach(), dim=-1)
    rows = []
    for index, row in enumerate(probabilities):
        draw = rng.uniform(f"{site}/row-{index}")
        rows.append(0 if draw < float(row[0]) else 1)
    return torch.tensor(rows, dtype=torch.int64)


def _rollout_episode(
    model: recct.RelayPolicy,
    plan: host.EpisodePlan,
    rng: SiteKeyedRNG,
    *,
    deterministic: bool,
    pool_kind: str,
) -> recct.EpisodeBatch:
    environment = host.OrientationPairedRelayHost()
    current = environment.reset(plan)
    hidden_by_occupant: dict[str, torch.Tensor] = {}
    steps = []
    terminal_rewards = []
    while not current.done:
        hidden_rows = []
        for token, reset in zip(current.occupant_tokens, current.state_reset):
            if reset or token not in hidden_by_occupant:
                hidden_by_occupant[token] = torch.zeros((32,), dtype=torch.float32)
            hidden_rows.append(hidden_by_occupant[token])
        with torch.no_grad():
            message, prediction, _, _, next_hidden = model.forward_roster(
                torch.from_numpy(current.observations.copy()),
                current.active_roles,
                torch.stack(hidden_rows),
            )
        if deterministic:
            message_action = message.argmax(dim=-1)
            prediction_action = prediction.argmax(dim=-1)
        else:
            base = f"episode-step-{current.epoch * 4 + current.phase}"
            message_action = _sample_action(message, rng, f"{base}/message")
            prediction_action = _sample_action(prediction, rng, f"{base}/prediction")
        actions = torch.stack((message_action, prediction_action), dim=1)
        for token, state in zip(current.occupant_tokens, next_hidden):
            hidden_by_occupant[token] = state.detach()
        following = environment.step(actions.numpy())
        steps.append(
            recct.EpisodeStep(
                observations=torch.from_numpy(current.observations.copy()),
                roles=current.active_roles,
                occupant_tokens=current.occupant_tokens,
                state_reset=current.state_reset,
                actions=actions,
                rewards=torch.from_numpy(following.rewards.copy()),
                epoch=current.epoch,
                phase=current.phase,
            )
        )
        if current.phase == 3:
            terminal_rewards.append(float(following.terminal_reward))
        current = following
    batch = recct.EpisodeBatch(
        steps=tuple(steps),
        episode_metric=sum(terminal_rewards) / 8.0,
        exogenous_digest=plan.exogenous_digest,
        pool_kind=pool_kind,
    )
    batch.validate()
    return batch


def _orientation(episode_index: int, replica: int) -> int:
    base = 1 if episode_index % 2 == 0 else -1
    return base if replica == 0 else -base


def _json_value(value: object) -> object:
    return json.loads(_json_bytes(value).decode("utf-8"))


def _retained_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"retained artifact {label} must be a string-keyed object")
    return value


def _retained_rows(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"retained artifact {label} must be an ordered row list")
    return value


def _exact_keys(row: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(row) != expected:
        raise ValueError(f"retained artifact {label} fields are incomplete or mislabeled")


def _exact_int(value: object, expected: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value != expected:
        raise ValueError(f"retained artifact {label} is not the reconstructed integer")
    return value


def _finite_float(value: object, label: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"retained artifact {label} is not numeric")
    result = float(value)
    if not math.isfinite(result) or (minimum is not None and result < minimum):
        raise ValueError(f"retained artifact {label} is outside its finite domain")
    return result


def _reconstruct_credit_receipt(
    credit: Mapping[str, Any], label: str
) -> recct.CreditReceipt:
    conditionals: dict[str, tuple[float, ...]] = {}
    for edge in ("lr", "rl"):
        _exact_int(credit[f"support_{edge}"], 4, f"{label} support {edge}")
        conditional_rows = _retained_rows(
            credit[f"conditional_{edge}"], f"{label} conditional {edge}"
        )
        if len(conditional_rows) != 4:
            raise ValueError(f"retained artifact {label} conditional support is invalid")
        conditionals[edge] = tuple(
            _finite_float(value, f"{label} conditional {edge}")
            for value in conditional_rows
        )

    def sign(value: float) -> int:
        return 1 if value > 0.0 else (-1 if value < 0.0 else 0)

    reconstructed_credit: dict[str, float] = {}
    reconstructed_rho: dict[str, float] = {}
    for edge in ("lr", "rl"):
        values = conditionals[edge]
        mean = sum(values) / 4.0
        rho = sum(sign(value) == sign(mean) for value in values) / 4.0
        claimed_credit = _finite_float(credit[f"credit_{edge}"], f"{label} credit {edge}")
        claimed_rho = _finite_float(credit[f"rho_{edge}"], f"{label} rho {edge}")
        if (
            not math.isclose(claimed_credit, mean, rel_tol=0.0, abs_tol=1e-12)
            or not math.isclose(claimed_rho, rho, rel_tol=0.0, abs_tol=1e-12)
        ):
            raise ValueError(
                f"retained artifact {label} credit/rho disagrees with conditional evidence"
            )
        reconstructed_credit[edge] = mean
        reconstructed_rho[edge] = rho
    return recct.CreditReceipt(
        credit_lr=reconstructed_credit["lr"],
        credit_rl=reconstructed_credit["rl"],
        support_lr=4,
        support_rl=4,
        rho_lr=reconstructed_rho["lr"],
        rho_rl=reconstructed_rho["rl"],
        conditional_lr=conditionals["lr"],
        conditional_rl=conditionals["rl"],
    )


def validate_retained_artifacts(
    configuration_row: Mapping[str, Any],
    training: Mapping[str, Any],
    evaluation: Mapping[str, Any],
) -> ValidatedRetainedArtifacts:
    """Purely reconstruct and validate every result-bearing retained row.

    Producer activity totals and direction labels are checked for consistency
    but never used as evidence.  The returned immutable rows contain only
    independently scheduled identities and validated primitive measurements.
    """

    technical_only = training.get("technical_only")
    if not isinstance(technical_only, bool):
        raise ValueError("retained artifact lifecycle identity is missing")
    configuration = (
        RunConfiguration.technical() if technical_only else RunConfiguration.full()
    )
    configuration.validate()
    expected_configuration = {
        **asdict(configuration),
        "algorithm": ALGORITHM_ID,
        "activity_caps": FULL_ACTIVITY_CAPS,
        "branch_precedence": BRANCH_PRECEDENCE,
        "retry_sweep_rescue_early_stop": 0,
    }
    expected_configuration = _json_value(expected_configuration)
    assert isinstance(expected_configuration, dict)
    expected_configuration_digest = _digest_bytes(_json_bytes(expected_configuration))
    expected_configuration_row = {
        **expected_configuration,
        "configuration_digest": expected_configuration_digest,
    }
    if _json_value(configuration_row) != expected_configuration_row:
        raise ValueError("retained artifact configuration is not the frozen schedule")

    training = _retained_mapping(training, "training")
    evaluation = _retained_mapping(evaluation, "evaluation")
    _exact_keys(
        training,
        {
            "schema_version",
            "algorithm",
            "stage",
            "status",
            "technical_only",
            "scientific_branch_suppressed",
            "source_commit",
            "configuration_digest",
            "configuration_manifest_digest",
            "readiness",
            "geometry",
            "activity_counts",
            "retry_recovery_history",
            "fits",
        },
        "training manifest",
    )
    _exact_keys(
        evaluation,
        {
            "schema_version",
            "algorithm",
            "stage",
            "status",
            "technical_only",
            "configuration_digest",
            "train_manifest_digest",
            "activity_counts",
            "cells",
        },
        "evaluation manifest",
    )
    if (
        training["schema_version"] != 1
        or training["algorithm"] != ALGORITHM_ID
        or training["stage"] != "train"
        or training["status"] != "COMPLETE"
        or training["scientific_branch_suppressed"] is not technical_only
        or not isinstance(training["source_commit"], str)
        or not training["source_commit"]
        or training["configuration_digest"] != expected_configuration_digest
        or training["retry_recovery_history"] != []
    ):
        raise ValueError("retained artifact training identity is invalid")
    if (
        evaluation["schema_version"] != 1
        or evaluation["algorithm"] != ALGORITHM_ID
        or evaluation["stage"] != "evaluate"
        or evaluation["status"] != "COMPLETE"
        or evaluation["technical_only"] is not technical_only
        or evaluation["configuration_digest"] != expected_configuration_digest
    ):
        raise ValueError("retained artifact evaluation identity is invalid")

    expected_geometry = _json_value(recct.geometry_receipt(recct.make_model(MASTER_SEEDS[0])))
    if _json_value(training["geometry"]) != expected_geometry:
        raise ValueError("retained artifact host geometry receipt is invalid")
    expected_readiness = bool(expected_geometry["identifying"])  # type: ignore[index]
    if training["readiness"] is not expected_readiness:
        raise ValueError("retained artifact readiness disagrees with reconstructed geometry")

    expected_fit_keys = [
        (arm, master_seed, replica)
        for master_seed in configuration.master_seeds
        for arm in configuration.arms
        for replica in range(2)
    ]
    raw_fits = _retained_rows(training["fits"], "training fits")
    if len(raw_fits) != len(expected_fit_keys):
        raise ValueError("retained artifact fit schedule is incomplete or duplicated")
    validated_fits: list[ValidatedFit] = []
    raw_fit_by_key: dict[tuple[str, int, int], Mapping[str, Any]] = {}
    fit_fields = {
        "arm",
        "master_seed",
        "orientation_replica",
        "initialization_seed",
        "trainer_rng_seed",
        "selector_rng_seed",
        "updates",
        "checkpoint",
        "checkpoint_sidecar",
        "model_fits",
    }
    update_fields = {
        "episode_index",
        "episode_seed",
        "omega",
        "exogenous_digest",
        "selected_mask",
        "direction_code",
        "credit",
        "balanced_coin",
        "committed_update_l2_norm",
        "optimizer_moment_delta_norm",
        "clipping_indicator",
        "active_port_count",
        "factorial_gradient_residual",
        "fresh_commit_matches_selected_shadow",
        "shadow_calls",
        "learner_calls",
        "optimizer_transitions",
    }
    direction_by_mask = {"10": 1, "01": -1, "00": 0, "11": 0}
    for position, (raw_fit, expected_key) in enumerate(zip(raw_fits, expected_fit_keys)):
        fit = _retained_mapping(raw_fit, f"fit {position}")
        _exact_keys(fit, fit_fields, f"fit {position}")
        arm, master_seed, replica = expected_key
        if (
            fit["arm"] != arm
            or fit["master_seed"] != master_seed
            or fit["orientation_replica"] != replica
            or fit["initialization_seed"] != master_seed
            or fit["trainer_rng_seed"] != 2_000_000 + master_seed
            or fit["selector_rng_seed"] != 3_000_000 + master_seed
            or fit["model_fits"] != 1
        ):
            raise ValueError("retained artifact fit seed/arm/replica label is invalid")
        checkpoint = (
            Path("checkpoints") / arm / f"seed-{master_seed}" / f"orientation-{replica}.pt"
        ).as_posix()
        if fit["checkpoint"] != checkpoint or fit["checkpoint_sidecar"] != checkpoint[:-3] + ".json":
            raise ValueError("retained artifact checkpoint fit identity is invalid")
        raw_updates = _retained_rows(fit["updates"], f"fit {expected_key} updates")
        if len(raw_updates) != configuration.train_episodes_per_replica:
            raise ValueError("retained artifact per-fit update schedule is incomplete")
        selector_rng = SiteKeyedRNG(3_000_000 + master_seed)
        validated_updates: list[ValidatedUpdate] = []
        current_mask = "00"
        for episode_index, raw_update in enumerate(raw_updates):
            update = _retained_mapping(raw_update, f"fit {expected_key} update {episode_index}")
            _exact_keys(update, update_fields, f"fit {expected_key} update {episode_index}")
            episode_seed = 1_000_000 + 1000 * master_seed + episode_index
            omega = _orientation(episode_index, replica)
            expected_plan = host.make_episode_plan(
                episode_seed, omega, configuration.training_pool
            )
            expected_coin = int(
                selector_rng.uniform(f"update-{episode_index}/balanced-coin") >= 0.5
            )
            if (
                update["episode_index"] != episode_index
                or update["episode_seed"] != episode_seed
                or update["omega"] != omega
                or update["exogenous_digest"] != expected_plan.exogenous_digest
                or update["balanced_coin"] != expected_coin
            ):
                raise ValueError("retained artifact training schedule or exogenous digest is invalid")
            selected_mask = update["selected_mask"]
            if not isinstance(selected_mask, str) or selected_mask not in recct.MASKS:
                raise ValueError("retained artifact selected mask is invalid")
            shadow_calls = _exact_int(update["shadow_calls"], 4, "shadow calls")
            learner_calls = _exact_int(update["learner_calls"], 5, "learner calls")
            optimizer_transitions = _exact_int(
                update["optimizer_transitions"], 5, "optimizer transitions"
            )
            if not isinstance(update["clipping_indicator"], bool) or not isinstance(
                update["fresh_commit_matches_selected_shadow"], bool
            ):
                raise ValueError("retained artifact update predicates are not booleans")
            credit = _retained_mapping(update["credit"], "credit receipt")
            _exact_keys(
                credit,
                {
                    "credit_lr",
                    "credit_rl",
                    "support_lr",
                    "support_rl",
                    "rho_lr",
                    "rho_rl",
                    "conditional_lr",
                    "conditional_rl",
                },
                "credit receipt",
            )
            reconstructed_credit = _reconstruct_credit_receipt(
                credit, f"fit {expected_key} update {episode_index}"
            )
            if arm == "G_SD" and any(
                value < 0.0
                for value in (
                    *reconstructed_credit.conditional_lr,
                    *reconstructed_credit.conditional_rl,
                )
            ):
                raise ValueError("retained artifact G_SD credit is not sign-destroyed")
            if arm == "G_AGG_SYM" and (
                reconstructed_credit.conditional_lr
                != reconstructed_credit.conditional_rl
                or len(set(reconstructed_credit.conditional_lr)) != 1
                or reconstructed_credit.credit_lr < 0.0
            ):
                raise ValueError("retained artifact G_AGG_SYM credit is not direction-blind")
            if arm == "G_AGG_SYM":
                expected_selected_mask = "10" if expected_coin == 0 else "01"
            elif arm == "ALL_11":
                expected_selected_mask = "11"
            else:
                expected_selected_mask = recct.select_credit_mask(
                    reconstructed_credit, current_mask
                )
            if selected_mask != expected_selected_mask:
                raise ValueError(
                    "retained artifact selected mask disagrees with reconstructed selector"
                )
            current_mask = expected_selected_mask
            direction_code = direction_by_mask[expected_selected_mask]
            _exact_int(
                update["direction_code"],
                direction_code,
                f"fit {expected_key} update {episode_index} direction code",
            )
            active_port_count = _exact_int(
                update["active_port_count"],
                expected_selected_mask.count("1"),
                f"fit {expected_key} update {episode_index} active ports",
            )
            validated_updates.append(
                ValidatedUpdate(
                    episode_index=episode_index,
                    episode_seed=episode_seed,
                    omega=omega,
                    exogenous_digest=expected_plan.exogenous_digest,
                    selected_mask=selected_mask,
                    direction_code=direction_code,
                    committed_update_l2_norm=_finite_float(
                        update["committed_update_l2_norm"], "committed update norm", minimum=0.0
                    ),
                    optimizer_moment_delta_norm=_finite_float(
                        update["optimizer_moment_delta_norm"], "optimizer moment delta", minimum=0.0
                    ),
                    clipping_indicator=update["clipping_indicator"],
                    active_port_count=active_port_count,
                    factorial_gradient_residual=_finite_float(
                        update["factorial_gradient_residual"], "factorial gradient residual", minimum=0.0
                    ),
                    fresh_commit_matches_selected_shadow=update[
                        "fresh_commit_matches_selected_shadow"
                    ],
                    shadow_calls=shadow_calls,
                    learner_calls=learner_calls,
                    optimizer_transitions=optimizer_transitions,
                )
            )
        validated_fit = ValidatedFit(
            arm=arm,
            master_seed=master_seed,
            orientation_replica=replica,
            updates=tuple(validated_updates),
            checkpoint=checkpoint,
        )
        validated_fits.append(validated_fit)
        if expected_key in raw_fit_by_key:
            raise ValueError("retained artifact fit identity is duplicated")
        raw_fit_by_key[expected_key] = fit

    for arm in configuration.arms:
        for master_seed in configuration.master_seeds:
            left = next(
                fit for fit in validated_fits
                if (fit.arm, fit.master_seed, fit.orientation_replica) == (arm, master_seed, 0)
            )
            right = next(
                fit for fit in validated_fits
                if (fit.arm, fit.master_seed, fit.orientation_replica) == (arm, master_seed, 1)
            )
            for left_update, right_update in zip(left.updates, right.updates):
                if (
                    left_update.episode_seed != right_update.episode_seed
                    or left_update.omega != -right_update.omega
                    or left_update.exogenous_digest != right_update.exogenous_digest
                ):
                    raise ValueError("retained artifact training orientation pair is not complemented")
                plus_update, minus_update = (
                    (left_update, right_update)
                    if left_update.omega == 1
                    else (right_update, left_update)
                )
                plus = host.make_episode_plan(
                    plus_update.episode_seed, plus_update.omega, configuration.training_pool
                )
                minus = host.make_episode_plan(
                    minus_update.episode_seed, minus_update.omega, configuration.training_pool
                )
                host.validate_orientation_pair(plus, minus)

    raw_cells = _retained_rows(evaluation["cells"], "evaluation cells")
    if len(raw_cells) != len(expected_fit_keys):
        raise ValueError("retained artifact evaluation cell schedule is incomplete or duplicated")
    validated_cells: list[ValidatedEvaluationCell] = []
    cell_fields = {
        "arm", "master_seed", "orientation_replica", "episodes", "checkpoint"
    }
    episode_fields = {
        "evaluation_seed", "omega", "exogenous_digest", "episode_metric", "learner_updates"
    }
    for position, (raw_cell, expected_key) in enumerate(zip(raw_cells, expected_fit_keys)):
        cell = _retained_mapping(raw_cell, f"evaluation cell {position}")
        _exact_keys(cell, cell_fields, f"evaluation cell {position}")
        arm, master_seed, replica = expected_key
        fit = validated_fits[position]
        if (
            cell["arm"] != arm
            or cell["master_seed"] != master_seed
            or cell["orientation_replica"] != replica
            or cell["checkpoint"] != fit.checkpoint
        ):
            raise ValueError("retained artifact evaluation cell identity is invalid")
        raw_episodes = _retained_rows(cell["episodes"], f"evaluation cell {expected_key}")
        if len(raw_episodes) != len(configuration.evaluation_seeds):
            raise ValueError("retained artifact evaluation rows are incomplete")
        validated_episodes: list[ValidatedEvaluationEpisode] = []
        for index, (raw_episode, evaluation_seed) in enumerate(
            zip(raw_episodes, configuration.evaluation_seeds)
        ):
            episode = _retained_mapping(raw_episode, f"evaluation episode {expected_key}/{index}")
            _exact_keys(episode, episode_fields, f"evaluation episode {expected_key}/{index}")
            omega = _orientation(index, replica)
            expected_plan = host.make_episode_plan(
                evaluation_seed, omega, configuration.evaluation_pool
            )
            if (
                episode["evaluation_seed"] != evaluation_seed
                or episode["omega"] != omega
                or episode["exogenous_digest"] != expected_plan.exogenous_digest
                or episode["learner_updates"] != 0
            ):
                raise ValueError("retained artifact evaluation schedule or digest is invalid")
            episode_metric = _finite_float(episode["episode_metric"], "evaluation episode metric")
            if not 0.0 <= episode_metric <= 1.0:
                raise ValueError("retained artifact evaluation metric is outside [0,1]")
            validated_episodes.append(
                ValidatedEvaluationEpisode(
                    evaluation_seed=evaluation_seed,
                    omega=omega,
                    exogenous_digest=expected_plan.exogenous_digest,
                    episode_metric=episode_metric,
                )
            )
        validated_cells.append(
            ValidatedEvaluationCell(
                arm=arm,
                master_seed=master_seed,
                orientation_replica=replica,
                episodes=tuple(validated_episodes),
                checkpoint=fit.checkpoint,
            )
        )

    for arm in configuration.arms:
        for master_seed in configuration.master_seeds:
            pair = [
                cell for cell in validated_cells
                if cell.arm == arm and cell.master_seed == master_seed
            ]
            if [cell.orientation_replica for cell in pair] != [0, 1]:
                raise ValueError("retained artifact evaluation pair is incomplete or duplicated")
            for left, right in zip(pair[0].episodes, pair[1].episodes):
                if (
                    left.evaluation_seed != right.evaluation_seed
                    or left.omega != -right.omega
                    or left.exogenous_digest != right.exogenous_digest
                ):
                    raise ValueError("retained artifact evaluation orientation pair is not complemented")
                plus_episode, minus_episode = (
                    (left, right) if left.omega == 1 else (right, left)
                )
                plus = host.make_episode_plan(
                    plus_episode.evaluation_seed,
                    plus_episode.omega,
                    configuration.evaluation_pool,
                )
                minus = host.make_episode_plan(
                    minus_episode.evaluation_seed,
                    minus_episode.omega,
                    configuration.evaluation_pool,
                )
                host.validate_orientation_pair(plus, minus)

    policy_calls_per_episode = sum(host.ACTIVE_COUNT_BY_EPOCH) * host.PHASES_PER_EPOCH
    update_rows = [update for fit in validated_fits for update in fit.updates]
    evaluation_rows = [episode for cell in validated_cells for episode in cell.episodes]
    reconstructed_counts = {
        "named_full_runs": 0 if configuration.technical_only else 1,
        "train_episodes": len(update_rows),
        "evaluation_episodes": len(evaluation_rows),
        "joint_environment_transitions_train": len(update_rows) * host.JOINT_STEPS,
        "joint_environment_transitions_evaluation": len(evaluation_rows) * host.JOINT_STEPS,
        "joint_environment_transitions_total": (len(update_rows) + len(evaluation_rows))
        * host.JOINT_STEPS,
        "policy_calls_train": len(update_rows) * policy_calls_per_episode,
        "policy_calls_evaluation": len(evaluation_rows) * policy_calls_per_episode,
        "policy_calls_total": (len(update_rows) + len(evaluation_rows))
        * policy_calls_per_episode,
        "committed_live_updates": len(update_rows),
        "pure_shadow_transition_calls": sum(update.shadow_calls for update in update_rows),
        "learner_update_calls": sum(update.learner_calls for update in update_rows),
        "optimizer_transition_calls": sum(
            update.optimizer_transitions for update in update_rows
        ),
        "model_fits": len(validated_fits),
        "sweeps_retries_rescues_early_stops": 0,
    }
    expected_counts = _counts(configuration)
    if (
        reconstructed_counts != expected_counts
        or training["activity_counts"] != expected_counts
        or evaluation["activity_counts"] != expected_counts
        or (not configuration.technical_only and reconstructed_counts != FULL_ACTIVITY_CAPS)
    ):
        raise ValueError("retained artifact activity evidence is incomplete or producer-count-only")
    return ValidatedRetainedArtifacts(
        configuration=configuration,
        fits=tuple(validated_fits),
        cells=tuple(validated_cells),
        activity_counts=reconstructed_counts,
        readiness=expected_readiness,
        host_geometry_identifying=expected_readiness,
    )


def _save_checkpoint(
    run_root: Path,
    *,
    model: recct.RelayPolicy,
    arm: str,
    master_seed: int,
    replica: int,
    configuration_digest: str,
    source_commit: str,
) -> tuple[str, str]:
    relative = Path("checkpoints") / arm / f"seed-{master_seed}" / f"orientation-{replica}.pt"
    target = run_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict()}, target)
    sidecar = target.with_suffix(".json")
    _write_json(
        sidecar,
        {
            "algorithm": ALGORITHM_ID,
            "arm": arm,
            "master_seed": master_seed,
            "orientation_replica": replica,
            "source_commit": source_commit,
            "configuration_digest": configuration_digest,
            "checkpoint_digest": _artifact_digest(target),
            "checkpoint_selection": "none",
            "checkpoint_kind": "final",
        },
    )
    return relative.as_posix(), sidecar.relative_to(run_root).as_posix()


def _load_checkpoint(run_root: Path, row: Mapping[str, object], configuration_digest: str) -> recct.RelayPolicy:
    checkpoint = run_root / str(row["checkpoint"])
    sidecar = _read_json(run_root / str(row["checkpoint_sidecar"]))
    validate_checkpoint_sidecar(
        sidecar,
        checkpoint_digest=_artifact_digest(checkpoint),
        configuration_digest=configuration_digest,
    )
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model = recct.RelayPolicy()
    model.load_state_dict(payload["model"], strict=True)
    model.eval()
    return model


def validate_checkpoint_sidecar(
    sidecar: Mapping[str, object],
    *,
    checkpoint_digest: str,
    configuration_digest: str,
) -> None:
    if (
        sidecar.get("checkpoint_digest") != checkpoint_digest
        or sidecar.get("configuration_digest") != configuration_digest
        or sidecar.get("checkpoint_selection") != "none"
        or sidecar.get("checkpoint_kind") != "final"
    ):
        raise ValueError("checkpoint sidecar validation failed")


def _train_fit(
    run_root: Path,
    configuration: RunConfiguration,
    configuration_digest: str,
    source_commit: str,
    arm: str,
    master_seed: int,
    replica: int,
) -> dict[str, object]:
    model = recct.make_model(master_seed)
    optimizer = recct.make_optimizer(model)
    learner = recct.OrientationPairedRelayLearner(
        f"{arm}/seed-{master_seed}/orientation-{replica}"
    )
    trainer_rng = SiteKeyedRNG(2_000_000 + master_seed)
    selector_rng = SiteKeyedRNG(3_000_000 + master_seed)
    current_mask = "00"
    parent_digest = _digest_bytes(_json_bytes((source_commit, arm, master_seed, replica)))
    updates = []
    for episode_index in range(configuration.train_episodes_per_replica):
        omega = _orientation(episode_index, replica)
        episode_seed = 1_000_000 + 1000 * master_seed + episode_index
        plan = host.make_episode_plan(episode_seed, omega, configuration.training_pool)
        if replica == 1:
            plus = host.make_episode_plan(episode_seed, -omega, configuration.training_pool)
            if plus.orientation != 1:
                plus = plus.complemented()
            host.validate_orientation_pair(plus, plus.complemented())
        batch = _rollout_episode(
            model, plan, trainer_rng, deterministic=False, pool_kind="training"
        )
        capsule = learner.seal_capsule(
            model=model,
            optimizer=optimizer,
            batch=batch,
            policy_generation=f"episode-{episode_index}",
            parent_digest=parent_digest,
            rng_counters=(
                ("learner/replay", episode_index * 5),
                ("optimizer/adam", episode_index * 5),
                ("selector/balanced_coin", episode_index),
            ),
        )
        handles = (
            learner.handle(capsule, "L", "R"),
            learner.handle(capsule, "R", "L"),
        )
        coin = 0 if selector_rng.uniform(f"update-{episode_index}/balanced-coin") < 0.5 else 1
        shadows, selection, commit = recct.run_update(
            learner,
            capsule,
            handles,
            arm,
            current_mask,
            coin,
            live_model=model,
            live_optimizer=optimizer,
        )
        selected_shadow = shadows[selection.selected_mask]
        predicate_equal = all(
            left == right if not isinstance(left, tuple) else _tuple_equal(left, right)
            for left, right in zip(selected_shadow.transition_predicate(), commit.transition_predicate())
        )
        updates.append(
            {
                "episode_index": episode_index,
                "episode_seed": episode_seed,
                "omega": omega,
                "exogenous_digest": plan.exogenous_digest,
                "selected_mask": selection.selected_mask,
                "direction_code": {"10": 1, "01": -1, "00": 0, "11": 0}[selection.selected_mask],
                "credit": asdict(selection.credit),
                "balanced_coin": coin,
                "committed_update_l2_norm": commit.committed_update_l2_norm,
                "optimizer_moment_delta_norm": commit.optimizer_moment_delta_norm,
                "clipping_indicator": commit.clipping_indicator,
                "active_port_count": commit.active_port_count,
                "factorial_gradient_residual": recct.factorial_gradient_residual(shadows),
                "fresh_commit_matches_selected_shadow": predicate_equal,
                "shadow_calls": 4,
                "learner_calls": 5,
                "optimizer_transitions": 5,
            }
        )
        current_mask = selection.selected_mask
        parent_digest = commit.after_model_digest
    checkpoint, sidecar = _save_checkpoint(
        run_root,
        model=model,
        arm=arm,
        master_seed=master_seed,
        replica=replica,
        configuration_digest=configuration_digest,
        source_commit=source_commit,
    )
    if learner.learner_calls != configuration.train_episodes_per_replica * 5:
        raise RuntimeError("learner call accounting mismatch")
    return {
        "arm": arm,
        "master_seed": master_seed,
        "orientation_replica": replica,
        "initialization_seed": master_seed,
        "trainer_rng_seed": 2_000_000 + master_seed,
        "selector_rng_seed": 3_000_000 + master_seed,
        "updates": updates,
        "checkpoint": checkpoint,
        "checkpoint_sidecar": sidecar,
        "model_fits": 1,
    }


def _tuple_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return bool(torch.equal(left, right))
    if isinstance(left, tuple) and isinstance(right, tuple) and len(left) == len(right):
        return all(_tuple_equal(a, b) for a, b in zip(left, right))
    return bool(left == right)


def train(
    *,
    run_root: Path,
    source_commit: str,
    full: bool,
    authorization_token: str | None,
) -> dict[str, object]:
    configuration = RunConfiguration.full() if full else RunConfiguration.technical()
    configuration.validate()
    if full and authorization_token != FULL_AUTHORIZATION_TOKEN:
        raise ValueError("unique RECCT-B1 full requires the exact CPM authorization token")
    if not source_commit:
        raise ValueError("source commit identity is required")
    if not configuration.technical_only and (
        len(source_commit) != 40
        or any(row not in "0123456789abcdef" for row in source_commit.lower())
    ):
        raise ValueError("full lifecycle requires one exact 40-hex source commit")
    if run_root.exists() and any(run_root.iterdir()):
        raise FileExistsError("run root is not empty; retries and shared roots are forbidden")
    run_root.mkdir(parents=True, exist_ok=True)
    configuration_payload = {
        **asdict(configuration),
        "algorithm": ALGORITHM_ID,
        "activity_caps": FULL_ACTIVITY_CAPS,
        "branch_precedence": BRANCH_PRECEDENCE,
        "retry_sweep_rescue_early_stop": 0,
    }
    configuration_digest = _digest_bytes(_json_bytes(configuration_payload))
    _write_json(
        run_root / "configuration_manifest.json",
        {**configuration_payload, "configuration_digest": configuration_digest},
    )
    geometry = recct.geometry_receipt(recct.make_model(MASTER_SEEDS[0]))
    fits = []
    for master_seed in configuration.master_seeds:
        for arm in configuration.arms:
            for replica in range(2):
                fits.append(
                    _train_fit(
                        run_root,
                        configuration,
                        configuration_digest,
                        source_commit,
                        arm,
                        master_seed,
                        replica,
                    )
                )
    result = {
        "schema_version": 1,
        "algorithm": ALGORITHM_ID,
        "stage": "train",
        "status": "COMPLETE",
        "technical_only": configuration.technical_only,
        "scientific_branch_suppressed": configuration.technical_only,
        "source_commit": source_commit,
        "configuration_digest": configuration_digest,
        "configuration_manifest_digest": _artifact_digest(run_root / "configuration_manifest.json"),
        "readiness": bool(geometry["identifying"]),
        "geometry": geometry,
        "activity_counts": _counts(configuration),
        "retry_recovery_history": [],
        "fits": fits,
    }
    _write_json(run_root / "train_manifest.json", result)
    return result


def evaluate(*, run_root: Path) -> dict[str, object]:
    training = _read_json(run_root / "train_manifest.json")
    configuration_row = _read_json(run_root / "configuration_manifest.json")
    technical_only = bool(training["technical_only"])
    configuration = RunConfiguration.technical() if technical_only else RunConfiguration.full()
    configuration.validate()
    if (
        training.get("configuration_digest") != configuration_row.get("configuration_digest")
        or training.get("configuration_manifest_digest")
        != _artifact_digest(run_root / "configuration_manifest.json")
    ):
        raise ValueError("training/configuration digest binding failed")
    cells = []
    for fit in training["fits"]:
        model = _load_checkpoint(run_root, fit, str(training["configuration_digest"]))
        replica = int(fit["orientation_replica"])
        episodes = []
        for index, evaluation_seed in enumerate(configuration.evaluation_seeds):
            omega = _orientation(index, replica)
            plan = host.make_episode_plan(evaluation_seed, omega, configuration.evaluation_pool)
            rng = SiteKeyedRNG(2_000_000 + int(fit["master_seed"]))
            batch = _rollout_episode(
                model, plan, rng, deterministic=True, pool_kind="evaluation"
            )
            episodes.append(
                {
                    "evaluation_seed": evaluation_seed,
                    "omega": omega,
                    "exogenous_digest": plan.exogenous_digest,
                    "episode_metric": batch.episode_metric,
                    "learner_updates": 0,
                }
            )
        cells.append(
            {
                "arm": fit["arm"],
                "master_seed": fit["master_seed"],
                "orientation_replica": replica,
                "episodes": episodes,
                "checkpoint": fit["checkpoint"],
            }
        )
    result = {
        "schema_version": 1,
        "algorithm": ALGORITHM_ID,
        "stage": "evaluate",
        "status": "COMPLETE",
        "technical_only": technical_only,
        "configuration_digest": training["configuration_digest"],
        "train_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "activity_counts": _counts(configuration),
        "cells": cells,
    }
    _write_json(run_root / "evaluation_manifest.json", result)
    return result


def _mean(rows: Sequence[float]) -> float:
    return sum(rows) / len(rows) if rows else 0.0


def _analysis_metrics(validated: ValidatedRetainedArtifacts) -> dict[str, object]:
    fits = validated.fits
    cells = validated.cells
    alignment: dict[str, float] = {}
    crossing: dict[str, float] = {}
    heldout: dict[str, float] = {}
    for arm in recct.ARMS:
        arm_fits = [row for row in fits if row.arm == arm]
        products = [
            float(update.omega) * float(update.direction_code)
            for fit in arm_fits
            for update in fit.updates
        ]
        alignment[arm] = _mean(products)
        crossing_rows = []
        by_key = {
            (row.master_seed, row.orientation_replica): row
            for row in arm_fits
        }
        for seed in sorted({key[0] for key in by_key}):
            left = by_key[(seed, 0)].updates
            right = by_key[(seed, 1)].updates
            for a, b in zip(left, right):
                if a.direction_code != 0 and b.direction_code != 0:
                    crossing_rows.append(a.direction_code == -b.direction_code)
        crossing[arm] = _mean([float(row) for row in crossing_rows])
        heldout[arm] = _mean(
            [
                episode.episode_metric
                for cell in cells
                if cell.arm == arm
                for episode in cell.episodes
            ]
        )
    contrasts = {
        control: heldout["RECCT_SIGNED"] - heldout[control]
        for control in ("G_SD", "G_AGG_SYM", "ALL_11")
    }
    cell_returns = {
        (cell.arm, cell.master_seed, cell.orientation_replica): _mean(
            [row.episode_metric for row in cell.episodes]
        )
        for cell in cells
    }
    positive_seed_pairs = {}
    for control in ("G_SD", "G_AGG_SYM"):
        count = 0
        for seed in sorted({key[1] for key in cell_returns}):
            signed = _mean(
                [cell_returns[("RECCT_SIGNED", seed, replica)] for replica in (0, 1)]
            )
            null = _mean([cell_returns[(control, seed, replica)] for replica in (0, 1)])
            count += int(signed - null > 0.0)
        positive_seed_pairs[control] = count
    negative_orientation_halves = 0
    for seed in sorted({key[1] for key in cell_returns}):
        for replica in (0, 1):
            signed = cell_returns[("RECCT_SIGNED", seed, replica)]
            if any(
                signed - cell_returns[(control, seed, replica)] < 0.0
                for control in ("G_SD", "G_AGG_SYM", "ALL_11")
            ):
                negative_orientation_halves += 1
    return {
        "alignment": alignment,
        "crossing_rate": crossing,
        "heldout_return": heldout,
        "primary_return_contrasts": contrasts,
        "positive_seed_pairs": positive_seed_pairs,
        "negative_orientation_halves": negative_orientation_halves,
    }


def _matching_gates(validated: ValidatedRetainedArtifacts) -> dict[str, object]:
    diagnostics: dict[str, dict[str, float]] = {}
    for arm in recct.ARMS:
        updates = [
            update for fit in validated.fits if fit.arm == arm for update in fit.updates
        ]
        diagnostics[arm] = {
            "update_norm": _mean([row.committed_update_l2_norm for row in updates]),
            "active_ports": _mean([float(row.active_port_count) for row in updates]),
            "clipping_frequency": _mean([float(row.clipping_indicator) for row in updates]),
        }
    signed_norm = diagnostics["RECCT_SIGNED"]["update_norm"]
    ratios = {}
    for control in ("G_SD", "G_AGG_SYM"):
        denominator = diagnostics[control]["update_norm"]
        ratios[control] = signed_norm / denominator if denominator > 0 else float("inf")
    cardinality = {
        control: abs(diagnostics["RECCT_SIGNED"]["active_ports"] - diagnostics[control]["active_ports"])
        for control in ("G_SD", "G_AGG_SYM")
    }
    orientation_rows = {}
    clipping_rows = {}
    for arm in recct.ARMS:
        plus = [
            update.committed_update_l2_norm
            for fit in validated.fits if fit.arm == arm
            for update in fit.updates if update.omega == 1
        ]
        minus = [
            update.committed_update_l2_norm
            for fit in validated.fits if fit.arm == arm
            for update in fit.updates if update.omega == -1
        ]
        denominator = _mean(minus)
        orientation_rows[arm] = abs(_mean(plus) / denominator - 1.0) if denominator > 0 else float("inf")
        plus_clip = [
            float(update.clipping_indicator)
            for fit in validated.fits if fit.arm == arm
            for update in fit.updates if update.omega == 1
        ]
        minus_clip = [
            float(update.clipping_indicator)
            for fit in validated.fits if fit.arm == arm
            for update in fit.updates if update.omega == -1
        ]
        clipping_rows[arm] = abs(_mean(plus_clip) - _mean(minus_clip))
    passed = (
        all(0.90 <= row <= 1.10 for row in ratios.values())
        and all(row <= 0.10 for row in cardinality.values())
        and all(row <= 0.05 for row in orientation_rows.values())
        and all(row <= 0.05 for row in clipping_rows.values())
    )
    return {
        "diagnostics": diagnostics,
        "signed_to_control_norm_ratio": ratios,
        "active_port_count_difference": cardinality,
        "within_arm_orientation_norm_change": orientation_rows,
        "within_arm_clipping_frequency_change": clipping_rows,
        "passed": passed,
    }


def select_branch(validity: Mapping[str, bool], metrics: Mapping[str, object]) -> str:
    if not validity["readiness"]:
        return BRANCH_PRECEDENCE[0]
    if not validity["contract_activity"]:
        return BRANCH_PRECEDENCE[1]
    if not validity["information_split"]:
        return BRANCH_PRECEDENCE[2]
    if not validity["host_geometry"]:
        return BRANCH_PRECEDENCE[3]
    if not validity["matching"]:
        return BRANCH_PRECEDENCE[4]
    alignment = metrics["alignment"]
    crossing = metrics["crossing_rate"]
    heldout = metrics["heldout_return"]
    contrasts = metrics["primary_return_contrasts"]
    positive_pairs = metrics["positive_seed_pairs"]
    if alignment["RECCT_SIGNED"] < 0.50 or crossing["RECCT_SIGNED"] < 0.75:
        return BRANCH_PRECEDENCE[5]
    if (
        alignment["RECCT_SIGNED"] - alignment["G_SD"] < 0.25
        or alignment["RECCT_SIGNED"] - alignment["G_AGG_SYM"] < 0.25
    ):
        return BRANCH_PRECEDENCE[6]
    if int(metrics["negative_orientation_halves"]) > 0:
        return BRANCH_PRECEDENCE[7]
    if (
        heldout["RECCT_SIGNED"] < 0.65
        or any(row < 0.10 for row in contrasts.values())
        or int(positive_pairs["G_SD"]) < 3
        or int(positive_pairs["G_AGG_SYM"]) < 3
    ):
        return BRANCH_PRECEDENCE[8]
    if (
        alignment["RECCT_SIGNED"] >= 0.50
        and crossing["RECCT_SIGNED"] >= 0.75
        and heldout["RECCT_SIGNED"] >= 0.65
        and all(row >= 0.10 for row in contrasts.values())
        and int(positive_pairs["G_SD"]) >= 3
        and int(positive_pairs["G_AGG_SYM"]) >= 3
        and int(metrics["negative_orientation_halves"]) == 0
    ):
        return BRANCH_PRECEDENCE[9]
    return BRANCH_PRECEDENCE[10]


def analyze(*, run_root: Path) -> dict[str, object]:
    training = _read_json(run_root / "train_manifest.json")
    evaluation = _read_json(run_root / "evaluation_manifest.json")
    configuration_row = _read_json(run_root / "configuration_manifest.json")
    artifact_binding_valid = (
        evaluation.get("configuration_digest") == training.get("configuration_digest")
        and evaluation.get("train_manifest_digest")
        == _artifact_digest(run_root / "train_manifest.json")
        and training.get("configuration_manifest_digest")
        == _artifact_digest(run_root / "configuration_manifest.json")
    )
    if not artifact_binding_valid:
        raise ValueError("retained artifact digest binding failed")
    validated = validate_retained_artifacts(configuration_row, training, evaluation)
    configuration = validated.configuration
    metrics = _analysis_metrics(validated)
    matching = _matching_gates(validated)
    all_updates = [update for fit in validated.fits for update in fit.updates]
    validity = {
        "readiness": validated.readiness,
        "contract_activity": all(
            row.shadow_calls == 4
            and row.learner_calls == 5
            and row.optimizer_transitions == 5
            and row.fresh_commit_matches_selected_shadow
            and row.factorial_gradient_residual <= 1e-5
            for row in all_updates
        ),
        "information_split": (
            set(configuration.training_pool).isdisjoint(configuration.evaluation_pool)
            and host.observation_schema()["forbidden"] == host.FORBIDDEN_OBSERVATION_FIELDS
        ),
        "host_geometry": validated.host_geometry_identifying,
        "matching": True if configuration.technical_only else bool(matching["passed"]),
        "fresh_commit": all(row.fresh_commit_matches_selected_shadow for row in all_updates),
        "preaggregation": all(row.factorial_gradient_residual <= 1e-5 for row in all_updates),
    }
    if configuration.technical_only:
        branch = TECHNICAL_ONLY_BRANCH
    else:
        branch = select_branch(validity, metrics)
    result = {
        "schema_version": 1,
        "algorithm": ALGORITHM_ID,
        "stage": "analyze",
        "status": "COMPLETE" if all(validity.values()) else "INVALID",
        "technical_only": configuration.technical_only,
        "scientific_branch_suppressed": configuration.technical_only,
        "branch": branch,
        "validity": validity,
        "matching": matching,
        "scientific_matching_gate_evaluated": not configuration.technical_only,
        "metrics": metrics,
        "activity_counts": dict(validated.activity_counts),
        "activity_caps": FULL_ACTIVITY_CAPS,
        "retry_recovery_history": training["retry_recovery_history"],
        "configuration_digest": training["configuration_digest"],
        "train_manifest_digest": _artifact_digest(run_root / "train_manifest.json"),
        "evaluation_manifest_digest": _artifact_digest(run_root / "evaluation_manifest.json"),
    }
    _write_json(run_root / "analysis_result.json", result)
    return result


def exercise(*, run_root: Path, source_commit: str) -> dict[str, object]:
    train(
        run_root=run_root,
        source_commit=source_commit,
        full=False,
        authorization_token=None,
    )
    evaluate(run_root=run_root)
    return analyze(run_root=run_root)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("train", "evaluate", "analyze", "exercise"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--authorization-token")
    args = parser.parse_args(argv)
    if args.stage == "train":
        if args.source_commit is None:
            raise ValueError("train requires --source-commit")
        train(
            run_root=args.run_root,
            source_commit=args.source_commit,
            full=args.full,
            authorization_token=args.authorization_token,
        )
    elif args.stage == "evaluate":
        if args.full or args.authorization_token:
            raise ValueError("evaluate derives lifecycle identity from train manifest")
        evaluate(run_root=args.run_root)
    elif args.stage == "analyze":
        if args.full or args.authorization_token:
            raise ValueError("analyze derives lifecycle identity from retained manifests")
        analyze(run_root=args.run_root)
    else:
        if args.source_commit is None or args.full or args.authorization_token:
            raise ValueError("exercise is technical-only and requires only --source-commit")
        exercise(run_root=args.run_root, source_commit=args.source_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
