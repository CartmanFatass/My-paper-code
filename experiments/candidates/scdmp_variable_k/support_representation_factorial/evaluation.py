from __future__ import annotations

import numpy as np
import torch

from experiments.candidates.scdmp_variable_k.target_bound_order_to_value.dgp import (
    all_action_truth,
    event_indices,
    oracle,
    words,
)

from .config import ACTIONS, K_TARGET
from .corpus import (
    Row,
    SeedCorpus,
    complete_word_examples,
    complete_word_truth_mean,
)
from .model import SegmentModel, model_state_digest


def _predict(
    model: SegmentModel,
    states: np.ndarray,
    actions: np.ndarray,
    token_words: np.ndarray,
    lengths: np.ndarray,
    *,
    batch_size: int = 4_096,
) -> tuple[np.ndarray, np.ndarray]:
    outputs_f: list[np.ndarray] = []
    outputs_g: list[np.ndarray] = []
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


def target_population(
    model: SegmentModel, rows: tuple[Row, ...], k: int,
) -> dict[str, np.ndarray]:
    example_count = len(rows) * 2 * len(ACTIONS)
    states = np.empty((example_count, 9), dtype=np.float64)
    actions = np.empty((example_count, 4), dtype=np.float32)
    tokens = np.empty((example_count, k), dtype=np.int64)
    lengths = np.full(example_count, k, dtype=np.int64)
    true_f = np.empty((len(rows), 2, len(ACTIONS), 9), dtype=np.float64)
    true_g = np.empty((len(rows), 2, len(ACTIONS)), dtype=np.float64)
    cursor = 0
    for base_index, row in enumerate(rows):
        forward, reverse = words(k, row.sigma, row.gamma)
        for orientation, word in enumerate((forward, reverse)):
            terminal, reward = all_action_truth(row.state, word)
            true_f[base_index, orientation] = terminal
            true_g[base_index, orientation] = reward
            stop = cursor + len(ACTIONS)
            states[cursor:stop] = row.state
            actions[cursor:stop] = np.asarray(ACTIONS, dtype=np.float32)
            tokens[cursor:stop] = event_indices(word)
            cursor = stop
    predicted_f, predicted_g = _predict(model, states, actions, tokens, lengths)
    return {
        "true_f": true_f,
        "true_g": true_g,
        "predicted_f": predicted_f.reshape(len(rows), 2, len(ACTIONS), 9),
        "predicted_g": predicted_g.reshape(len(rows), 2, len(ACTIONS)),
    }


def _errors(
    predicted_f: np.ndarray,
    predicted_g: np.ndarray,
    true_f: np.ndarray,
    true_g: np.ndarray,
    scale_f: np.ndarray,
    scale_g: np.float32,
) -> float:
    state_error = np.mean(
        np.square((predicted_f - true_f) / scale_f), dtype=np.float64,
    )
    reward_error = np.mean(
        np.square((predicted_g - true_g) / float(scale_g)), dtype=np.float64,
    )
    return float(np.sqrt(0.5 * (state_error + reward_error)))


def _mean_errors(
    mean_f: np.ndarray,
    mean_g: float,
    true_f: np.ndarray,
    true_g: np.ndarray,
    scale_f: np.ndarray,
    scale_g: np.float32,
) -> float:
    return _errors(
        np.broadcast_to(mean_f, true_f.shape),
        np.full(true_g.shape, mean_g, dtype=np.float64),
        true_f,
        true_g,
        scale_f,
        scale_g,
    )


def fit_support_ratio(
    model: SegmentModel,
    rows: tuple[Row, ...],
    fit_mean_f: np.ndarray,
    fit_mean_g: float,
    scale_f: np.ndarray,
    scale_g: np.float32,
) -> dict[str, float | bool]:
    examples = complete_word_examples(rows)
    predicted_f, predicted_g = _predict(
        model, examples.states, examples.actions, examples.words, examples.lengths,
    )
    e_model = _errors(
        predicted_f, predicted_g, examples.terminal, examples.reward, scale_f, scale_g,
    )
    e_mean = _mean_errors(
        fit_mean_f, fit_mean_g, examples.terminal, examples.reward, scale_f, scale_g,
    )
    ratio = e_model / e_mean if np.isfinite(e_mean) and e_mean > 0.0 else float("nan")
    return {
        "E_model": e_model,
        "E_mean": e_mean,
        "ratio": ratio,
        "denominator_valid": bool(np.isfinite(e_mean) and e_mean > 0.0),
        "passed": bool(np.isfinite(ratio) and ratio <= 0.65),
    }


def evaluate_cell(
    model: SegmentModel,
    corpus: SeedCorpus,
    cell: str,
    scale_f: np.ndarray,
    scale_g: np.float32,
) -> dict[str, object]:
    support = cell[:2]
    fit_mean_f, fit_mean_g = complete_word_truth_mean(corpus.train[support])
    fit_gate = fit_support_ratio(
        model, corpus.fit_support, fit_mean_f, fit_mean_g, scale_f, scale_g,
    )
    populations = {
        k: target_population(model, corpus.targets[k], k) for k in K_TARGET
    }
    true_f = np.concatenate([
        populations[k]["true_f"].reshape(-1, 9) for k in K_TARGET
    ])
    true_g = np.concatenate([
        populations[k]["true_g"].reshape(-1) for k in K_TARGET
    ])
    predicted_f = np.concatenate([
        populations[k]["predicted_f"].reshape(-1, 9) for k in K_TARGET
    ])
    predicted_g = np.concatenate([
        populations[k]["predicted_g"].reshape(-1) for k in K_TARGET
    ])
    target_e_model = _errors(
        predicted_f, predicted_g, true_f, true_g, scale_f, scale_g,
    )
    target_e_mean = _mean_errors(
        fit_mean_f, fit_mean_g, true_f, true_g, scale_f, scale_g,
    )
    target_ratio = target_e_model / target_e_mean \
        if np.isfinite(target_e_mean) and target_e_mean > 0.0 else float("nan")

    coordinate_variance: list[dict[str, object]] = []
    action_sensitivity: list[dict[str, object]] = []
    for k in K_TARGET:
        population = populations[k]
        for coordinate in range(9):
            predicted_variance = float(np.var(
                population["predicted_f"][..., coordinate], ddof=0,
            ))
            true_variance = float(np.var(
                population["true_f"][..., coordinate], ddof=0,
            ))
            ratio = predicted_variance / true_variance \
                if np.isfinite(true_variance) and true_variance > 0.0 else float("nan")
            coordinate_variance.append({
                "k": k,
                "coordinate": coordinate,
                "predicted_variance": predicted_variance,
                "true_variance": true_variance,
                "ratio": ratio,
                "passed": bool(np.isfinite(ratio) and 0.25 <= ratio <= 4.0),
            })
        eligible = 0
        sensitive = 0
        for base_index in range(len(corpus.targets[k])):
            for orientation in range(2):
                _action, _gap, qualifies = oracle(
                    population["true_g"][base_index, orientation], k,
                )
                if qualifies:
                    eligible += 1
                    score_range = float(
                        np.max(population["predicted_g"][base_index, orientation])
                        - np.min(population["predicted_g"][base_index, orientation])
                    )
                    sensitive += int(score_range >= 0.03 * k)
        fraction = sensitive / eligible if eligible else float("nan")
        action_sensitivity.append({
            "k": k,
            "eligible": eligible,
            "sensitive": sensitive,
            "fraction": fraction,
            "passed": bool(eligible > 0 and fraction >= 0.90),
        })

    return {
        "seed_index": corpus.seed_index,
        "cell": cell,
        "support": support,
        "representation": cell[2:],
        "evaluation_identity": corpus.evaluation_identity,
        "checkpoint_digest": model_state_digest(model),
        "scales": {"F": [float(value) for value in scale_f], "G": float(scale_g)},
        "fit_support": fit_gate,
        "target": {
            "E_model": target_e_model,
            "E_mean": target_e_mean,
            "ratio": target_ratio,
            "denominator_valid": bool(
                np.isfinite(target_e_mean) and target_e_mean > 0.0
            ),
        },
        "coordinate_variance": coordinate_variance,
        "action_sensitivity": action_sensitivity,
    }
