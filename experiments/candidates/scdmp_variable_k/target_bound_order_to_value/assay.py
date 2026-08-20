from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from .config import ACTIONS, K_TARGET, STATE_SCALE
from .corpus import Row, SeedCorpus, complete_word_examples, complete_word_truth_mean
from .dgp import (
    all_action_truth, event_indices, factor_words, lexargmax, oracle,
    order_blind_oracle, words,
)
from .model import SegmentModel, model_state_digest

ORIENTATIONS = ("F", "R")


@dataclass(frozen=True)
class PredictionPopulation:
    true_f: np.ndarray       # [base, orientation, action, 9]
    true_g: np.ndarray       # [base, orientation, action]
    direct_f: np.ndarray
    direct_g: np.ndarray
    correct_f: np.ndarray
    correct_g: np.ndarray
    reversed_f: np.ndarray
    reversed_g: np.ndarray


def _predict(model: SegmentModel, states: np.ndarray, actions: np.ndarray,
             token_words: np.ndarray, lengths: np.ndarray,
             batch_size: int = 4_096) -> tuple[np.ndarray, np.ndarray]:
    outputs_f, outputs_g = [], []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(states), batch_size):
            stop = min(start + batch_size, len(states))
            predicted_f, predicted_g = model(
                torch.as_tensor(states[start:stop], dtype=torch.float32),
                torch.as_tensor(actions[start:stop], dtype=torch.float32),
                torch.as_tensor(token_words[start:stop], dtype=torch.long),
                torch.as_tensor(lengths[start:stop], dtype=torch.long),
            )
            outputs_f.append(predicted_f.cpu().numpy().astype(np.float64))
            outputs_g.append(predicted_g.cpu().numpy().astype(np.float64))
    return np.concatenate(outputs_f), np.concatenate(outputs_g)


def _fixed_word_tensor(word: tuple[str, ...], count: int) -> tuple[np.ndarray, np.ndarray]:
    values = np.repeat(event_indices(word)[None, :], count, axis=0)
    return values, np.full(count, len(word), dtype=np.int64)


def target_population(model: SegmentModel, rows: tuple[Row, ...], k: int) \
        -> PredictionPopulation:
    count = len(rows) * 2 * len(ACTIONS)
    states = np.empty((count, 9), dtype=np.float64)
    actions = np.empty((count, 4), dtype=np.float32)
    tokens = np.empty((count, k), dtype=np.int64)
    lengths = np.full(count, k, dtype=np.int64)
    true_f = np.empty((len(rows), 2, len(ACTIONS), 9), dtype=np.float64)
    true_g = np.empty((len(rows), 2, len(ACTIONS)), dtype=np.float64)
    cursor = 0
    for base, row in enumerate(rows):
        forward, reverse = words(k, row.sigma, row.gamma)
        for orientation, word in enumerate((forward, reverse)):
            terminal, reward = all_action_truth(row.state, word)
            true_f[base, orientation] = terminal
            true_g[base, orientation] = reward
            stop = cursor + len(ACTIONS)
            states[cursor:stop] = row.state
            actions[cursor:stop] = np.asarray(ACTIONS, dtype=np.float32)
            tokens[cursor:stop] = event_indices(word)
            cursor = stop
    direct_f_flat, direct_g_flat = _predict(model, states, actions, tokens, lengths)
    direct_f = direct_f_flat.reshape(len(rows), 2, len(ACTIONS), 9)
    direct_g = direct_g_flat.reshape(len(rows), 2, len(ACTIONS))

    correct_f = np.empty_like(direct_f)
    correct_g = np.empty_like(direct_g)
    reversed_f = np.empty_like(direct_f)
    reversed_g = np.empty_like(direct_g)
    cursor = 0
    for base, row in enumerate(rows):
        p_word, q_word = factor_words(k, row.sigma, row.gamma)
        for orientation in range(2):
            correct_pair = (p_word, q_word) if orientation == 0 else (q_word, p_word)
            reversed_pair = (q_word, p_word) if orientation == 0 else (p_word, q_word)
            base_states = np.repeat(row.state[None, :], len(ACTIONS), axis=0)
            action_array = np.asarray(ACTIONS, dtype=np.float32)
            for destination_f, destination_g, pair in (
                (correct_f, correct_g, correct_pair),
                (reversed_f, reversed_g, reversed_pair),
            ):
                first_tokens, first_lengths = _fixed_word_tensor(pair[0], len(ACTIONS))
                first_f, first_g = _predict(
                    model, base_states, action_array, first_tokens, first_lengths,
                )
                second_tokens, second_lengths = _fixed_word_tensor(pair[1], len(ACTIONS))
                second_f, second_g = _predict(
                    model, first_f, action_array, second_tokens, second_lengths,
                )
                destination_f[base, orientation] = second_f
                destination_g[base, orientation] = first_g + second_g
            cursor += len(ACTIONS)
    return PredictionPopulation(
        true_f, true_g, direct_f, direct_g,
        correct_f, correct_g, reversed_f, reversed_g,
    )


def _errors(predicted_f: np.ndarray, predicted_g: np.ndarray,
            true_f: np.ndarray, true_g: np.ndarray,
            scale_f: np.ndarray, scale_g: np.float32) -> float:
    state = np.mean(np.square((predicted_f - true_f) / scale_f), dtype=np.float64)
    reward = np.mean(np.square((predicted_g - true_g) / float(scale_g)), dtype=np.float64)
    return float(np.sqrt(0.5 * (state + reward)))


def _mean_errors(mean_f: np.ndarray, mean_g: float, true_f: np.ndarray, true_g: np.ndarray,
                 scale_f: np.ndarray, scale_g: np.float32) -> float:
    predicted_f = np.broadcast_to(mean_f, true_f.shape)
    predicted_g = np.full(true_g.shape, mean_g, dtype=np.float64)
    return _errors(predicted_f, predicted_g, true_f, true_g, scale_f, scale_g)


def fit_support_ratio(model: SegmentModel, rows: tuple[Row, ...],
                      fit_mean_f: np.ndarray, fit_mean_g: float,
                      scale_f: np.ndarray, scale_g: np.float32) -> dict[str, float | bool]:
    examples = complete_word_examples(rows)
    predicted_f, predicted_g = _predict(
        model, examples.states, examples.actions, examples.words, examples.lengths,
    )
    e_model = _errors(predicted_f, predicted_g, examples.terminal, examples.reward,
                      scale_f, scale_g)
    e_mean = _mean_errors(fit_mean_f, fit_mean_g, examples.terminal, examples.reward,
                          scale_f, scale_g)
    ratio = e_model / e_mean if np.isfinite(e_mean) and e_mean > 0.0 else float("nan")
    return {"E_model": e_model, "E_mean": e_mean, "ratio": ratio,
            "passed": bool(np.isfinite(ratio) and ratio <= 0.65)}


def competence(model: SegmentModel, corpus: SeedCorpus,
               populations: dict[int, PredictionPopulation],
               scale_f: np.ndarray, scale_g: np.float32) -> dict[str, object]:
    fit_mean_f, fit_mean_g = complete_word_truth_mean(corpus.fit)
    fit_gate = fit_support_ratio(
        model, corpus.fit_support, fit_mean_f, fit_mean_g, scale_f, scale_g,
    )
    true_f = np.concatenate([populations[k].true_f.reshape(-1, 9) for k in K_TARGET])
    true_g = np.concatenate([populations[k].true_g.reshape(-1) for k in K_TARGET])
    predicted_f = np.concatenate([populations[k].direct_f.reshape(-1, 9) for k in K_TARGET])
    predicted_g = np.concatenate([populations[k].direct_g.reshape(-1) for k in K_TARGET])
    target_e_model = _errors(predicted_f, predicted_g, true_f, true_g, scale_f, scale_g)
    target_e_mean = _mean_errors(fit_mean_f, fit_mean_g, true_f, true_g, scale_f, scale_g)
    target_ratio = target_e_model / target_e_mean \
        if np.isfinite(target_e_mean) and target_e_mean > 0.0 else float("nan")

    variance: list[dict[str, object]] = []
    sensitivity: list[dict[str, object]] = []
    for k in K_TARGET:
        population = populations[k]
        for coordinate in range(9):
            predicted_var = float(np.var(population.direct_f[..., coordinate], ddof=0))
            true_var = float(np.var(population.true_f[..., coordinate], ddof=0))
            ratio = predicted_var / true_var if np.isfinite(true_var) and true_var > 0.0 \
                else float("nan")
            variance.append({
                "k": k, "coordinate": coordinate,
                "predicted_variance": predicted_var, "true_variance": true_var,
                "ratio": ratio,
                "passed": bool(np.isfinite(ratio) and 0.25 <= ratio <= 4.0),
            })
        eligible = 0
        sensitive = 0
        for base in range(len(corpus.targets[k])):
            for orientation in range(2):
                _action, _gap, qualifies = oracle(population.true_g[base, orientation], k)
                if qualifies:
                    eligible += 1
                    score_range = float(np.max(population.direct_g[base, orientation])
                                        - np.min(population.direct_g[base, orientation]))
                    sensitive += int(score_range >= 0.03 * k)
        fraction = sensitive / eligible if eligible else float("nan")
        sensitivity.append({
            "k": k, "eligible": eligible, "sensitive": sensitive, "fraction": fraction,
            "passed": bool(eligible > 0 and fraction >= 0.90),
        })
    return {
        "fit_support": fit_gate,
        "target": {"E_model": target_e_model, "E_mean": target_e_mean,
                   "ratio": target_ratio},
        "coordinate_variance": variance,
        "action_sensitivity": sensitivity,
        "local_gates_passed": bool(
            fit_gate["passed"] and all(row["passed"] for row in variance)
            and all(row["passed"] for row in sensitivity)
            and np.isfinite(target_ratio)
        ),
    }


def physical_and_relation(corpus: SeedCorpus,
                          populations: dict[int, PredictionPopulation]) -> dict[str, object]:
    physical: dict[str, float] = {}
    per_k: dict[str, dict[str, float]] = {}
    for k in K_TARGET:
        population = populations[k]
        distance = np.sqrt(np.mean(
            np.square((population.true_f[:, 0] - population.true_f[:, 1])
                      / np.asarray(STATE_SCALE)), axis=-1,
        ))
        t_value = float(np.median(distance))
        r_value = float(np.median(np.abs(population.true_g[:, 0] - population.true_g[:, 1])) / k)
        oracle_actions = np.empty((len(corpus.targets[k]), 2), dtype=np.int64)
        gaps = np.empty((len(corpus.targets[k]), 2), dtype=np.float64)
        eligible = np.zeros((len(corpus.targets[k]), 2), dtype=bool)
        blind = np.empty(len(corpus.targets[k]), dtype=np.int64)
        for base in range(len(corpus.targets[k])):
            for orientation in range(2):
                action, gap, qualifies = oracle(population.true_g[base, orientation], k)
                oracle_actions[base, orientation] = action
                gaps[base, orientation] = gap
                eligible[base, orientation] = qualifies
            blind[base] = order_blind_oracle(population.true_g[base, 0], population.true_g[base, 1])
        both = np.all(eligible, axis=1)
        reversal = both & (oracle_actions[:, 0] != oracle_actions[:, 1])
        f_value = float(np.mean(reversal[both])) if np.any(both) else 0.0
        g_value = float(np.mean(np.min(gaps[reversal], axis=1)) / k) if np.any(reversal) else 0.0
        aware = 0.5 * (
            population.true_g[np.arange(len(blind)), 0, oracle_actions[:, 0]]
            + population.true_g[np.arange(len(blind)), 1, oracle_actions[:, 1]]
        )
        unaware = 0.5 * (
            population.true_g[np.arange(len(blind)), 0, blind]
            + population.true_g[np.arange(len(blind)), 1, blind]
        )
        h_value = float(np.mean(aware - unaware) / k)
        a_value = min(f_value / 0.30, g_value / 0.04, h_value / 0.08)
        physical.update({f"T_k{k}": t_value, f"R_k{k}": r_value, f"A_k{k}": a_value})

        relation_metrics: dict[str, float] = {}
        for label, predicted_f, predicted_g in (
            ("C", population.correct_f, population.correct_g),
            ("R", population.reversed_f, population.reversed_g),
        ):
            rmse = float(np.sqrt(np.mean(
                np.square((predicted_f - population.true_f) / np.asarray(STATE_SCALE)),
                dtype=np.float64,
            )))
            mae = float(np.mean(np.abs(predicted_g - population.true_g), dtype=np.float64) / k)
            regrets = []
            for base in range(len(corpus.targets[k])):
                for orientation in range(2):
                    predicted_action = lexargmax(predicted_g[base, orientation])
                    true_action = int(oracle_actions[base, orientation])
                    regrets.append(
                        (population.true_g[base, orientation, true_action]
                         - population.true_g[base, orientation, predicted_action]) / k
                    )
            relation_metrics[f"RMSE_{label}"] = rmse
            relation_metrics[f"MAE_{label}"] = mae
            relation_metrics[f"REG_{label}"] = float(np.mean(regrets, dtype=np.float64))
        if t_value > 0.0 and r_value > 0.0 and h_value > 0.0 \
                and all(np.isfinite((t_value, r_value, h_value))):
            relation_metrics.update({
                "dF": (relation_metrics["RMSE_R"] - relation_metrics["RMSE_C"]) / t_value,
                "dR": (relation_metrics["MAE_R"] - relation_metrics["MAE_C"]) / r_value,
                "dQ": (relation_metrics["REG_R"] - relation_metrics["REG_C"]) / h_value,
            })
        else:
            relation_metrics.update({"dF": float("nan"), "dR": float("nan"),
                                     "dQ": float("nan")})
        relation_metrics.update({"f": f_value, "g": g_value, "h": h_value})
        per_k[str(k)] = relation_metrics
    pooled = {
        component: float(np.mean([per_k[str(k)][component] for k in K_TARGET], dtype=np.float64))
        for component in ("dF", "dR", "dQ")
    }
    pooled["S_order"] = min(pooled["dF"] / 0.20,
                            pooled["dR"] / 0.20, pooled["dQ"] / 0.10)
    return {"physical": physical, "per_k": per_k, "pooled": pooled}


def evaluate_seed(model: SegmentModel, corpus: SeedCorpus,
                  scale_f: np.ndarray, scale_g: np.float32) -> dict[str, object]:
    populations = {k: target_population(model, corpus.targets[k], k) for k in K_TARGET}
    return {
        "seed_index": corpus.seed_index,
        "checkpoint_digest": model_state_digest(model),
        "scales": {"F": [float(value) for value in scale_f], "G": float(scale_g)},
        "competence": competence(model, corpus, populations, scale_f, scale_g),
        **physical_and_relation(corpus, populations),
    }
