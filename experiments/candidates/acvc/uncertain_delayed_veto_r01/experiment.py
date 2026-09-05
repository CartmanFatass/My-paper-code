"""Single-process ACVC uncertain/delayed veto R01 learner and evaluator."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, Callable

import numpy as np
from scipy.stats import t as student_t
import torch
from torch import nn
from torch.nn import functional as F


OBJECT_ID = "ACVC-B-EXPLORE-UNCERTAIN-DELAYED-VETO-R01"
EVIDENCE_CLASS = "B/EXPLORE"
BASE_SEED = 11
OPPORTUNITIES = 12
TRAIN_UPDATES = 128
TRAIN_BATCH = 64
EVAL_EPISODES = 4_096
LEARNING_RATE = 0.02
GRADIENT_CAP = 1.0
LEARNED_ARMS = ("ACVC-HISTORY-GATE", "RAW-GRU")
FIXED_ARMS = ("DET-CF", "AUTH-PROBE", "ALWAYS-EXECUTE", "ALWAYS-PROBE", "ALWAYS-VETO")
ARMS = LEARNED_ARMS + FIXED_ARMS
ACTION_NAMES = ("EXECUTE", "PROBE", "VETO")
REGIME_NAMES = ("UNINFORMATIVE", "CALIBRATED")
NAMESPACE_IDS = {
    "train_worlds": 101,
    "treatment_actions": 211,
    "treatment_initialization": 307,
    "gru_actions": 401,
    "gru_initialization": 503,
    "evaluation_worlds": 601,
    "fixed_policy_evaluation": 701,
}
TECHNICAL_SEED = 19_011
LEARNED_CAP_SECONDS = 600.0
FIXED_CAP_SECONDS = 120.0
HOST_LOAD_ALLOWANCE = 3.0


@dataclass(frozen=True)
class Blueprints:
    calibrated: np.ndarray
    issuance_unsafe: np.ndarray
    current_unsafe: np.ndarray
    confidence: np.ndarray
    age: np.ndarray
    verdict: np.ndarray

    @property
    def episodes(self) -> int:
        return int(self.verdict.shape[0])


class HistoryGate(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Linear(6, 8)
        self.policy = nn.Linear(8, 3)
        self.value = nn.Linear(8, 1)

    def forward(self, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = torch.tanh(self.encoder(inputs))
        return self.policy(hidden), self.value(hidden).squeeze(-1)


class RawGru(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.gru = nn.GRUCell(10, 8)
        self.policy = nn.Linear(8, 3)
        self.value = nn.Linear(8, 1)

    def forward(
        self, inputs: torch.Tensor, hidden: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        hidden = self.gru(inputs, hidden)
        return self.policy(hidden), self.value(hidden).squeeze(-1), hidden


def derived_seeds(base_seed: int) -> dict[str, int]:
    """Publish deterministic, independent SeedSequence namespaces."""
    return {
        name: int(np.random.SeedSequence([base_seed, namespace]).generate_state(1, np.uint64)[0])
        for name, namespace in NAMESPACE_IDS.items()
    }


def _make_model(arm: str, seed: int) -> nn.Module:
    ambient = torch.random.get_rng_state()
    torch.manual_seed(0)
    model: nn.Module = HistoryGate() if arm == LEARNED_ARMS[0] else RawGru()
    torch.random.set_rng_state(ambient)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            if "weight" in name:
                parameter.normal_(0.0, 0.05, generator=generator)
            else:
                parameter.zero_()
    return model.to(dtype=torch.float32, device="cpu")


def make_model(arm: str, *, base_seed: int = BASE_SEED) -> nn.Module:
    seeds = derived_seeds(base_seed)
    seed_name = "treatment_initialization" if arm == LEARNED_ARMS[0] else "gru_initialization"
    return _make_model(arm, seeds[seed_name])


def generate_blueprints(rng: np.random.Generator, episodes: int) -> Blueprints:
    calibrated = rng.random(episodes) < 0.5
    issuance = rng.random((episodes, OPPORTUNITIES)) < 0.12
    confidence = np.where(
        rng.integers(0, 2, size=(episodes, OPPORTUNITIES), dtype=np.int8) == 0, 0.7, 0.9,
    ).astype(np.float32)
    age = rng.integers(0, 3, size=(episodes, OPPORTUNITIES), dtype=np.int8)
    match_probability = np.where(calibrated[:, None], confidence, 0.5)
    matches = rng.random((episodes, OPPORTUNITIES)) < match_probability
    verdict = np.where(matches, issuance, np.logical_not(issuance))
    flips = rng.random((episodes, OPPORTUNITIES, 2)) < 0.10
    current = issuance.copy()
    current ^= flips[:, :, 0] & (age >= 1)
    current ^= flips[:, :, 1] & (age >= 2)
    return Blueprints(
        calibrated=calibrated,
        issuance_unsafe=issuance,
        current_unsafe=current,
        confidence=confidence,
        age=age,
        verdict=verdict,
    )


def _strength(confidence: torch.Tensor, age: torch.Tensor) -> torch.Tensor:
    return (2.0 * confidence - 1.0) * torch.pow(
        torch.full_like(confidence, 0.8), age.to(torch.float32)
    )


def _reward_and_reveal(
    action: torch.Tensor, unsafe: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    reward = torch.where(
        action == 0, torch.where(unsafe, -4.0, 1.0),
        torch.where(action == 1, torch.where(unsafe, -0.6, 0.4), 0.0),
    ).to(torch.float32)
    return reward, action != 2


def _treatment_inputs(
    bp: Blueprints, step: int, balance: torch.Tensor, revealed_count: torch.Tensor,
) -> torch.Tensor:
    return torch.stack((
        torch.from_numpy(bp.verdict[:, step]).to(torch.float32),
        torch.from_numpy(bp.confidence[:, step]),
        torch.from_numpy(bp.age[:, step]).to(torch.float32) / 2.0,
        torch.full((bp.episodes,), step / 11.0, dtype=torch.float32),
        balance / 3.0,
        revealed_count / 3.0,
    ), dim=1)


def _raw_inputs(
    bp: Blueprints, step: int, previous_action: torch.Tensor,
    previous_revealed: torch.Tensor, previous_truth: torch.Tensor,
) -> torch.Tensor:
    return torch.cat((
        torch.stack((
            torch.from_numpy(bp.verdict[:, step]).to(torch.float32),
            torch.from_numpy(bp.confidence[:, step]),
            torch.from_numpy(bp.age[:, step]).to(torch.float32) / 2.0,
            torch.full((bp.episodes,), step / 11.0, dtype=torch.float32),
        ), dim=1),
        F.one_hot(previous_action, num_classes=4).to(torch.float32),
        previous_revealed.to(torch.float32).unsqueeze(1),
        torch.where(previous_revealed, previous_truth, False).to(torch.float32).unsqueeze(1),
    ), dim=1)


def _update_summary(
    bp: Blueprints, step: int, revealed: torch.Tensor, balance: torch.Tensor,
    revealed_count: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    verdict = torch.from_numpy(bp.verdict[:, step])
    truth = torch.from_numpy(bp.current_unsafe[:, step])
    signed = torch.where(verdict == truth, 1.0, -1.0) * _strength(
        torch.from_numpy(bp.confidence[:, step]), torch.from_numpy(bp.age[:, step])
    )
    return (
        torch.clamp(balance + torch.where(revealed, signed, 0.0), -3.0, 3.0),
        torch.clamp(revealed_count + revealed.to(torch.float32), max=3.0),
    )


def _learner_rollout(
    arm: str, model: nn.Module, bp: Blueprints, *, action_generator: torch.Generator | None,
    greedy: bool,
) -> dict[str, Any]:
    batch = bp.episodes
    balance = torch.zeros(batch, dtype=torch.float32)
    revealed_count = torch.zeros(batch, dtype=torch.float32)
    previous_action = torch.zeros(batch, dtype=torch.int64)
    previous_revealed = torch.zeros(batch, dtype=torch.bool)
    previous_truth = torch.zeros(batch, dtype=torch.bool)
    hidden = torch.zeros(batch, 8, dtype=torch.float32)
    logits_rows, values, rewards, actions, entropies = [], [], [], [], []
    balance_rows, count_rows = [], []
    for step in range(OPPORTUNITIES):
        if arm == LEARNED_ARMS[0]:
            logits, value = model(_treatment_inputs(bp, step, balance, revealed_count))
        else:
            logits, value, hidden = model(
                _raw_inputs(bp, step, previous_action, previous_revealed, previous_truth), hidden,
            )
        probabilities = torch.softmax(logits, dim=-1)
        if not (
            bool(torch.isfinite(logits).all())
            and bool(torch.isfinite(value).all())
            and bool(torch.isfinite(probabilities).all())
            and bool(torch.isfinite(hidden).all())
        ):
            raise FloatingPointError(f"{arm} rollout quantity became nonfinite")
        action = (
            torch.argmax(logits, dim=-1)
            if greedy else torch.multinomial(probabilities, 1, generator=action_generator).squeeze(1)
        )
        unsafe = torch.from_numpy(bp.current_unsafe[:, step])
        reward, revealed = _reward_and_reveal(action, unsafe)
        balance, revealed_count = _update_summary(
            bp, step, revealed, balance, revealed_count,
        )
        entropy = -(probabilities * torch.log_softmax(logits, dim=-1)).sum(dim=-1)
        if not all(bool(torch.isfinite(value).all()) for value in (
            reward, balance, revealed_count, entropy,
        )):
            raise FloatingPointError(f"{arm} rollout quantity became nonfinite")
        logits_rows.append(logits)
        values.append(value)
        rewards.append(reward)
        actions.append(action)
        entropies.append(entropy)
        balance_rows.append(balance)
        count_rows.append(revealed_count)
        previous_action = action + 1
        previous_revealed = revealed
        previous_truth = unsafe
    return {
        "logits": torch.stack(logits_rows, dim=1),
        "values": torch.stack(values, dim=1),
        "rewards": torch.stack(rewards, dim=1),
        "actions": torch.stack(actions, dim=1),
        "entropies": torch.stack(entropies, dim=1),
        "balances": torch.stack(balance_rows, dim=1),
        "revealed_counts": torch.stack(count_rows, dim=1),
    }


def _flat_parameters(model: nn.Module) -> torch.Tensor:
    return torch.cat([parameter.detach().reshape(-1) for parameter in model.parameters()])


def initial_exposure(base_seed: int = BASE_SEED) -> dict[str, Any]:
    rows = {}
    for arm in LEARNED_ARMS:
        parameters = _flat_parameters(make_model(arm, base_seed=base_seed))
        count = int(parameters.numel())
        l2 = float(torch.linalg.vector_norm(parameters))
        rms = l2 / math.sqrt(count)
        ratio = 2.56 / l2 if l2 else math.inf
        rows[arm] = {
            "parameter_count": count,
            "initialized_parameter_l2": l2,
            "initialized_parameter_rms": rms,
            "nominal_clipped_gradient_path": 2.56,
            "path_to_initialized_l2_ratio": ratio,
        }
    valid = all(
        math.isfinite(row["initialized_parameter_l2"])
        and row["initialized_parameter_l2"] > 0.0
        and math.isfinite(row["path_to_initialized_l2_ratio"])
        and row["path_to_initialized_l2_ratio"] >= 0.5
        for row in rows.values()
    )
    return {"arms": rows, "valid": valid}


def train_arm(
    arm: str, *, base_seed: int = BASE_SEED, updates: int = TRAIN_UPDATES,
    batch_size: int = TRAIN_BATCH, deadline: float | None = None,
) -> tuple[nn.Module, dict[str, Any]]:
    seeds = derived_seeds(base_seed)
    model = make_model(arm, base_seed=base_seed)
    initial = _flat_parameters(model).clone()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, eps=1e-8)
    worlds = np.random.default_rng(seeds["train_worlds"])
    action_name = "treatment_actions" if arm == LEARNED_ARMS[0] else "gru_actions"
    action_rng = torch.Generator(device="cpu").manual_seed(seeds[action_name])
    nonzero_gradient_updates = 0
    entropy_sum = 0.0
    started = time.perf_counter()
    model.train()
    for _update in range(updates):
        rollout = _learner_rollout(
            arm, model, generate_blueprints(worlds, batch_size),
            action_generator=action_rng, greedy=False,
        )
        returns = torch.zeros_like(rollout["rewards"])
        running = torch.zeros(batch_size, dtype=torch.float32)
        for step in range(OPPORTUNITIES - 1, -1, -1):
            running = rollout["rewards"][:, step] + running
            returns[:, step] = running
        log_probs = torch.log_softmax(rollout["logits"], dim=-1)
        chosen = log_probs.gather(-1, rollout["actions"].unsqueeze(-1)).squeeze(-1)
        advantages = (returns - rollout["values"]).detach()
        loss = (
            -(chosen * advantages).mean()
            + 0.5 * (rollout["values"] - returns).square().mean()
            - 0.01 * rollout["entropies"].mean()
        )
        if not bool(torch.isfinite(loss)):
            raise FloatingPointError(f"{arm} loss became nonfinite")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), GRADIENT_CAP)
        if not bool(torch.isfinite(gradient_norm)):
            raise FloatingPointError(f"{arm} gradient became nonfinite")
        nonzero_gradient_updates += int(float(gradient_norm) > 0.0)
        optimizer.step()
        if any(not bool(torch.isfinite(parameter).all()) for parameter in model.parameters()):
            raise FloatingPointError(f"{arm} parameter became nonfinite")
        entropy_sum += float(rollout["entropies"].detach().sum())
        if deadline is not None and time.perf_counter() > deadline:
            raise RuntimeError(f"{arm} exceeded its wall cap at an optimizer update boundary")
    wall_seconds = time.perf_counter() - started
    final = _flat_parameters(model)
    displacement = final - initial
    count = int(initial.numel())
    initial_l2 = float(torch.linalg.vector_norm(initial))
    final_l2 = float(torch.linalg.vector_norm(final))
    displacement_l2 = float(torch.linalg.vector_norm(displacement))
    audit = {
        "parameter_count": count,
        "initial_l2": initial_l2,
        "final_l2": final_l2,
        "displacement_l2": displacement_l2,
        "displacement_rms": displacement_l2 / math.sqrt(count),
        "displacement_to_initial_l2": displacement_l2 / initial_l2,
        "displacement_rms_to_initial_rms": displacement_l2 / initial_l2,
        "nonzero_gradient_update_count": nonzero_gradient_updates,
        "action_entropy": entropy_sum / (updates * batch_size * OPPORTUNITIES),
        "optimizer_updates": updates,
        "training_episodes": updates * batch_size,
        "training_transitions": updates * batch_size * OPPORTUNITIES,
        "wall_seconds": wall_seconds,
    }
    if any(
        not math.isfinite(float(audit[key]))
        for key in (
            "initial_l2", "final_l2", "displacement_l2", "displacement_rms",
            "displacement_to_initial_l2", "displacement_rms_to_initial_rms", "action_entropy",
        )
    ):
        raise FloatingPointError(f"{arm} exposure became nonfinite")
    if displacement_l2 == 0.0 or nonzero_gradient_updates == 0:
        raise RuntimeError(f"{arm} learner did not move")
    return model.eval(), audit


def det_cf_actions(bp: Blueprints) -> np.ndarray:
    prior = 0.12
    accuracy = (bp.confidence.astype(np.float64) + 0.5) / 2.0
    p_issue_negative = prior * accuracy / (
        prior * accuracy + (1.0 - prior) * (1.0 - accuracy)
    )
    p_issue_positive = prior * (1.0 - accuracy) / (
        prior * (1.0 - accuracy) + (1.0 - prior) * accuracy
    )
    p_issue = np.where(bp.verdict, p_issue_negative, p_issue_positive)
    p_current = 0.5 + (p_issue - 0.5) * np.power(0.8, bp.age)
    values = np.stack((1.0 - 5.0 * p_current, 0.4 - p_current, np.zeros_like(p_current)), -1)
    return np.argmax(values, axis=-1).astype(np.int64)


def fixed_actions(arm: str, bp: Blueprints) -> np.ndarray:
    if arm == "DET-CF":
        return det_cf_actions(bp)
    if arm == "AUTH-PROBE":
        return np.where(bp.verdict, 1, 0).astype(np.int64)
    action = {"ALWAYS-EXECUTE": 0, "ALWAYS-PROBE": 1, "ALWAYS-VETO": 2}[arm]
    return np.full(bp.verdict.shape, action, dtype=np.int64)


def _fixed_rollout(arm: str, bp: Blueprints) -> dict[str, torch.Tensor]:
    actions = torch.from_numpy(fixed_actions(arm, bp))
    rewards, balances, counts = [], [], []
    balance = torch.zeros(bp.episodes, dtype=torch.float32)
    revealed_count = torch.zeros(bp.episodes, dtype=torch.float32)
    for step in range(OPPORTUNITIES):
        reward, revealed = _reward_and_reveal(
            actions[:, step], torch.from_numpy(bp.current_unsafe[:, step]),
        )
        balance, revealed_count = _update_summary(bp, step, revealed, balance, revealed_count)
        rewards.append(reward)
        balances.append(balance)
        counts.append(revealed_count)
    return {
        "actions": actions,
        "rewards": torch.stack(rewards, 1),
        "balances": torch.stack(balances, 1),
        "revealed_counts": torch.stack(counts, 1),
    }


def _mean_sd(values: np.ndarray) -> dict[str, float]:
    return {"mean": float(values.mean()), "sd": float(values.std(ddof=1))}


def _histogram(values: np.ndarray) -> dict[str, int]:
    rounded = np.round(values.astype(np.float64), 6)
    unique, counts = np.unique(rounded, return_counts=True)
    return {format(float(value), ".6g"): int(count) for value, count in zip(unique, counts)}


def summarize_evaluation(
    arm: str, bp: Blueprints, rollout: dict[str, torch.Tensor], wall_seconds: float,
) -> dict[str, Any]:
    rewards = rollout["rewards"].detach().cpu().numpy().astype(np.float64)
    actions = rollout["actions"].detach().cpu().numpy()
    balances = rollout["balances"].detach().cpu().numpy()
    counts = rollout["revealed_counts"].detach().cpu().numpy()
    episode_returns = rewards.sum(axis=1)
    unsafe = bp.current_unsafe
    safe = np.logical_not(unsafe)

    def safety(mask: np.ndarray) -> dict[str, Any]:
        selected_unsafe = unsafe & mask[:, None]
        selected_safe = safe & mask[:, None]
        selected = np.broadcast_to(mask[:, None], actions.shape)
        return {
            "unsafe_execution_rate": float(((actions == 0) & selected_unsafe).sum() / selected_unsafe.sum()),
            "clean_opportunity_loss": float((1.0 - rewards[selected_safe]).mean()),
            "action_rates": {
                ACTION_NAMES[index]: float(((actions == index) & selected).sum() / selected.sum())
                for index in range(3)
            },
        }

    subgroup: dict[str, dict[str, float]] = {}
    fields = {
        "confidence": bp.confidence,
        "age": bp.age,
        "verdict": bp.verdict.astype(np.int8),
        "opportunity_index": np.broadcast_to(np.arange(OPPORTUNITIES), rewards.shape),
    }
    for name, values in fields.items():
        subgroup[name] = {
            str(value): float(rewards[values == value].mean()) for value in np.unique(values)
        }
    by_regime = {}
    for flag, name in enumerate(REGIME_NAMES):
        mask = bp.calibrated == bool(flag)
        by_regime[name] = {
            **safety(mask),
            "return": _mean_sd(episode_returns[mask]),
            "revealed_history_count_distribution": _histogram(counts[mask, -1]),
            "consistency_balance_distribution": _histogram(balances[mask, -1]),
        }
    return {
        "episode_return": {**_mean_sd(episode_returns), "all": episode_returns.tolist()},
        **safety(np.ones(bp.episodes, dtype=bool)),
        "by_regime": by_regime,
        "return_by": subgroup,
        "evaluation_episodes": bp.episodes,
        "evaluation_transitions": bp.episodes * OPPORTUNITIES,
        "wall_seconds": wall_seconds,
    }


def evaluate_arm(
    arm: str, bp: Blueprints, model: nn.Module | None = None,
) -> dict[str, Any]:
    if arm in LEARNED_ARMS and any(
        not bool(torch.isfinite(parameter).all()) for parameter in model.parameters()
    ):
        raise FloatingPointError(f"{arm} evaluation parameter is nonfinite")
    started = time.perf_counter()
    with torch.no_grad():
        rollout = (
            _learner_rollout(arm, model, bp, action_generator=None, greedy=True)
            if arm in LEARNED_ARMS else _fixed_rollout(arm, bp)
        )
    return summarize_evaluation(arm, bp, rollout, time.perf_counter() - started)


def paired_interval(differences: np.ndarray) -> dict[str, float]:
    mean = float(differences.mean())
    se = float(differences.std(ddof=1) / math.sqrt(differences.size))
    critical = float(student_t.ppf(0.975, differences.size - 1))
    return {"mean": mean, "low": mean - critical * se, "high": mean + critical * se}


def apply_result_rule(arms: dict[str, dict[str, Any]]) -> dict[str, Any]:
    det = arms["DET-CF"]["episode_return"]["mean"]
    auth = arms["AUTH-PROBE"]["episode_return"]["mean"]
    fixed = "DET-CF" if det >= auth else "AUTH-PROBE"
    fixed_returns = np.asarray(arms[fixed]["episode_return"]["all"])
    treatment = np.asarray(arms[LEARNED_ARMS[0]]["episode_return"]["all"])
    gru = np.asarray(arms[LEARNED_ARMS[1]]["episode_return"]["all"])
    delta_a = float((treatment - fixed_returns).mean())
    delta_g = float((gru - fixed_returns).mean())
    delta_ag = float((treatment - gru).mean())

    def harm_compatible(arm: str) -> bool:
        return (
            arms[arm]["unsafe_execution_rate"] <= arms[fixed]["unsafe_execution_rate"] + 0.02
            and arms[arm]["clean_opportunity_loss"] <= arms[fixed]["clean_opportunity_loss"] + 0.05
        )

    harm_a = harm_compatible(LEARNED_ARMS[0])
    harm_g = harm_compatible(LEARNED_ARMS[1])
    if delta_a >= 0.25 and harm_a and delta_ag >= -0.10:
        branch = "B2-A / STRUCTURED_GATE_SIGNAL"
    elif delta_g >= 0.25 and harm_g:
        branch = "B2-B / GENERIC_RECURRENCE_ONLY"
    elif not ((delta_a >= 0.10 and harm_a) or (delta_g >= 0.10 and harm_g)):
        branch = "B2-C / FIXED_RULE_CONTAINS"
    else:
        branch = "B2-D / LEARNING_UNRESOLVED"
    return {
        "branch": branch,
        "fixed_comparator": fixed,
        "Delta_A": delta_a,
        "Delta_G": delta_g,
        "Delta_AG": delta_ag,
        "harm_compatible": {LEARNED_ARMS[0]: harm_a, LEARNED_ARMS[1]: harm_g},
        "paired_95pct_t_intervals": {
            "Delta_A": paired_interval(treatment - fixed_returns),
            "Delta_G": paired_interval(gru - fixed_returns),
            "Delta_AG": paired_interval(treatment - gru),
        },
    }


def _peak_rss_bytes() -> int | None:
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        psapi = ctypes.windll.psapi  # type: ignore[attr-defined]
        kernel32.GetCurrentProcess.argtypes = ()
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        process = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(
            process, ctypes.byref(counters), counters.cb,
        )
        return int(counters.PeakWorkingSetSize) if ok else None
    except (AttributeError, OSError):
        return None


def project_cost() -> dict[str, Any]:
    """Measure the frozen discarded technical workload and project per-arm wall cost."""
    started = time.perf_counter()
    torch.set_num_threads(1)
    technical_seeds = derived_seeds(TECHNICAL_SEED)
    learned = {}
    for arm in LEARNED_ARMS:
        model, train = train_arm(
            arm, base_seed=TECHNICAL_SEED, updates=2, batch_size=64, deadline=None,
        )
        eval_bp = generate_blueprints(np.random.default_rng(technical_seeds["evaluation_worlds"]), 512)
        evaluated = evaluate_arm(arm, eval_bp, model)
        train_seconds_per_decision = train["wall_seconds"] / (2 * 64 * OPPORTUNITIES)
        eval_seconds_per_decision = evaluated["wall_seconds"] / (512 * OPPORTUNITIES)
        projected = HOST_LOAD_ALLOWANCE * (
            train_seconds_per_decision * (TRAIN_UPDATES * TRAIN_BATCH * OPPORTUNITIES)
            + eval_seconds_per_decision * (EVAL_EPISODES * OPPORTUNITIES)
        )
        learned[arm] = {
            "measured_train_seconds": train["wall_seconds"],
            "measured_train_decisions": 2 * 64 * OPPORTUNITIES,
            "measured_train_seconds_per_decision": train_seconds_per_decision,
            "measured_eval_seconds": evaluated["wall_seconds"],
            "measured_eval_decisions": 512 * OPPORTUNITIES,
            "measured_eval_seconds_per_decision": eval_seconds_per_decision,
            "projected_seconds": projected,
            "cap_seconds": LEARNED_CAP_SECONDS,
            "within_cap": projected <= LEARNED_CAP_SECONDS,
        }
    fixed = {}
    eval_bp = generate_blueprints(np.random.default_rng(technical_seeds["evaluation_worlds"]), 512)
    for arm in FIXED_ARMS:
        evaluated = evaluate_arm(arm, eval_bp)
        per_decision = evaluated["wall_seconds"] / (512 * OPPORTUNITIES)
        projected = HOST_LOAD_ALLOWANCE * per_decision * (EVAL_EPISODES * OPPORTUNITIES)
        fixed[arm] = {
            "measured_eval_seconds": evaluated["wall_seconds"],
            "measured_eval_decisions": 512 * OPPORTUNITIES,
            "measured_eval_seconds_per_decision": per_decision,
            "projected_seconds": projected,
            "cap_seconds": FIXED_CAP_SECONDS,
            "within_cap": projected <= FIXED_CAP_SECONDS,
        }
    exposure = initial_exposure(BASE_SEED)
    return {
        "object_id": OBJECT_ID,
        "command": "project-cost",
        "result_blind": True,
        "technical_seed": TECHNICAL_SEED,
        "technical_rng_namespaces": technical_seeds,
        "discarded_work": {"updates_per_learned_arm": 2, "episodes_per_update": 64,
                           "eval_episodes_per_arm": 512},
        "formula": {
            "learned": "3 * (train_seconds_per_decision * 98304 + eval_seconds_per_decision * 49152)",
            "fixed": "3 * eval_seconds_per_decision * 49152",
        },
        "exposure_line": exposure,
        "learned_arms": learned,
        "fixed_arms": fixed,
        "all_within_caps": all(row["within_cap"] for row in (*learned.values(), *fixed.values())),
        "resources": {"wall_seconds": time.perf_counter() - started,
                      "peak_rss_bytes": _peak_rss_bytes()},
    }


def _launch_sha(project_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def run_object(
    output_root: str | Path, *, admission_receipt: str | Path, base_seed: int = BASE_SEED,
    updates: int = TRAIN_UPDATES, batch_size: int = TRAIN_BATCH,
    eval_episodes: int = EVAL_EPISODES, argv: tuple[str, ...] = (), toy: bool = False,
    project_cost_path: str | Path | None = None,
) -> Path:
    torch.set_num_threads(1)
    started = time.perf_counter()
    admission = json.loads(Path(admission_receipt).read_text(encoding="utf-8"))
    if not (
        admission.get("passed") and admission.get("physical_floor_pass")
        and admission.get("effective_floor_pass")
    ):
        raise RuntimeError("fresh 4 GiB physical/effective admission did not pass")
    cost_record = None
    if not toy:
        if project_cost_path is None:
            raise RuntimeError("formal run requires the measured project-cost JSON")
        cost_record = json.loads(Path(project_cost_path).read_text(encoding="utf-8"))
        learned_costs = cost_record.get("learned_arms", {})
        fixed_costs = cost_record.get("fixed_arms", {})
        if not (
            cost_record.get("object_id") == OBJECT_ID
            and cost_record.get("command") == "project-cost"
            and cost_record.get("result_blind") is True
            and cost_record.get("all_within_caps") is True
            and all(key in cost_record for key in (
                "discarded_work", "formula", "exposure_line", "learned_arms", "fixed_arms",
            ))
            and set(learned_costs) == set(LEARNED_ARMS)
            and set(fixed_costs) == set(FIXED_ARMS)
            and all(learned_costs[arm].get("within_cap") is True for arm in LEARNED_ARMS)
            and all(fixed_costs[arm].get("within_cap") is True for arm in FIXED_ARMS)
        ):
            raise RuntimeError("project-cost does not admit every frozen arm")
    project_root = Path(__file__).resolve().parents[4]
    launch_sha = _launch_sha(project_root)
    exposure = initial_exposure(base_seed)
    if not exposure["valid"]:
        raise RuntimeError("exposure line does not permit learner movement")
    seeds = derived_seeds(base_seed)
    evaluation_bp = generate_blueprints(
        np.random.default_rng(seeds["evaluation_worlds"]), eval_episodes,
    )
    arms = {}
    actual_exposure_rows = {}
    for arm in LEARNED_ARMS:
        arm_started = time.perf_counter()
        deadline = None if toy else arm_started + LEARNED_CAP_SECONDS
        model, training = train_arm(
            arm, base_seed=base_seed, updates=updates, batch_size=batch_size,
            deadline=deadline,
        )
        arm_record = evaluate_arm(arm, evaluation_bp, model)
        arm_record["training"] = training
        actual_exposure_rows[arm] = {
            key: training[key] for key in (
                "parameter_count", "initial_l2", "final_l2", "displacement_l2",
                "displacement_rms", "displacement_to_initial_l2",
                "displacement_rms_to_initial_rms", "nonzero_gradient_update_count",
                "action_entropy",
            )
        }
        arm_record["actual_total_wall_seconds"] = time.perf_counter() - arm_started
        arm_record["wall_cap_seconds"] = LEARNED_CAP_SECONDS
        arm_record["wall_cap_enforced"] = not toy
        if not toy and arm_record["actual_total_wall_seconds"] > LEARNED_CAP_SECONDS:
            raise RuntimeError(f"{arm} exceeded its combined train/evaluation wall cap")
        arms[arm] = arm_record
    actual_exposure = {
        "arms": actual_exposure_rows,
        "valid": all(
            all(math.isfinite(float(value)) for value in actual_exposure_rows[arm].values())
            and actual_exposure_rows[arm]["displacement_l2"] > 0.0
            and actual_exposure_rows[arm]["nonzero_gradient_update_count"] > 0
            for arm in LEARNED_ARMS
        ),
    }
    if not actual_exposure["valid"]:
        raise RuntimeError("actual learner exposure is incomplete or nonfinite")
    for arm in FIXED_ARMS:
        arm_started = time.perf_counter()
        arm_record = evaluate_arm(arm, evaluation_bp)
        arm_record["actual_total_wall_seconds"] = time.perf_counter() - arm_started
        arm_record["wall_cap_seconds"] = FIXED_CAP_SECONDS
        arm_record["wall_cap_enforced"] = not toy
        if not toy and arm_record["actual_total_wall_seconds"] > FIXED_CAP_SECONDS:
            raise RuntimeError(f"{arm} exceeded its evaluation wall cap")
        arms[arm] = arm_record
    reading = None if toy else apply_result_rule(arms)
    peak = _peak_rss_bytes()
    record = {
        "object_id": OBJECT_ID,
        "evidence_class": None if toy else EVIDENCE_CLASS,
        "complete": not toy,
        "result_bearing": not toy,
        "technical_only": toy,
        "toy": toy,
        "base_seed": base_seed,
        "rng_namespaces": seeds,
        "rng_ownership": {
            "train_worlds": "byte-identical blueprints at each learned-arm episode/update coordinate",
            "treatment_actions": "ACVC-HISTORY-GATE sampled actions",
            "gru_actions": "RAW-GRU sampled actions",
            "treatment_initialization": "ACVC-HISTORY-GATE parameters",
            "gru_initialization": "RAW-GRU parameters",
            "evaluation_worlds": "shared fresh evaluation blueprints for all seven arms",
            "fixed_policy_evaluation": "deterministic fixed-policy evaluation; zero random draws",
        },
        "launch_sha": launch_sha,
        "argv": list(argv),
        "admission": admission,
        "project_cost": None if toy else {
            key: cost_record[key] for key in (
                "discarded_work", "formula", "exposure_line", "learned_arms",
                "fixed_arms", "all_within_caps",
            )
        },
        "exposure_line": actual_exposure,
        "counts": {
            "optimizer_updates_per_learned_arm": updates,
            "training_episodes_per_learned_arm": updates * batch_size,
            "training_transitions_per_learned_arm": updates * batch_size * OPPORTUNITIES,
            "evaluation_episodes_per_arm": eval_episodes,
            "evaluation_transitions_per_arm": eval_episodes * OPPORTUNITIES,
            "model_selection_exposure": 0,
        },
        "arms": arms,
        "result_rule": reading,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "peak_rss_bytes": peak,
            "status": "measured" if peak is not None else "resources_unmeasured",
        },
    }
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    summary = output / "summary.json"
    summary.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
