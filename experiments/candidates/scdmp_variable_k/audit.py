from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import torch

from .actor import (
    LearnedActionPanel, candidate_factors_from_action_states, cycle_extreme,
    factor_score, learned_action_panel,
)
from .config import COMPOSITION_SPLITS
from .corpus import Corpus
from .dgp import factorized_true_panel, joint_action_index
from .evaluation import AuditInstance, audit_denominators, audit_instances
from .model import SCDMPModel


ResourceCheck = Callable[[], None]


@dataclass(frozen=True)
class TrueAuditPanel:
    instance: AuditInstance
    word_kind: str
    context_word: tuple[str, ...]
    terminal: np.ndarray       # [4,3,2], analytically repeated over joint actions
    node_reward: np.ndarray    # [4,3]
    edge_reward: np.ndarray    # [4,3,3]
    node_score: np.ndarray     # [4,3]
    edge_score: np.ndarray     # [4,3,3]
    oracle_action: tuple[int, int, int, int]
    oracle_score: float


def build_true_audit_panels(
    algorithm_seed: int, resource_check: ResourceCheck | None = None,
) -> tuple[list[TrueAuditPanel], dict[str, int], dict[str, int]]:
    instances, warmup_microsteps = audit_instances(algorithm_seed)
    panels: list[TrueAuditPanel] = []
    target_microsteps = 0
    reverse_microsteps = 0
    physical_factor_steps = {"audit_target_words": 0, "audit_reverse_twins": 0}
    for instance in instances:
        for word_kind, context_word in (
            ("target", instance.target_word), ("reverse", instance.reverse_word),
        ):
            if resource_check is not None:
                resource_check()
            terminals, node, edge, node_score, edge_score, factor_steps = factorized_true_panel(
                instance.state, context_word,
            )
            oracle_action, oracle_score = cycle_extreme(node_score, edge_score)
            panels.append(TrueAuditPanel(
                instance=instance, word_kind=word_kind, context_word=context_word,
                terminal=terminals, node_reward=node, edge_reward=edge,
                node_score=node_score, edge_score=edge_score,
                oracle_action=oracle_action, oracle_score=oracle_score,
            ))
            if word_kind == "target":
                target_microsteps += 81 * instance.duration
                physical_factor_steps["audit_target_words"] += factor_steps
            else:
                reverse_microsteps += 81 * instance.duration
                physical_factor_steps["audit_reverse_twins"] += factor_steps
    return panels, {
        "common_audit_warmup": warmup_microsteps,
        "audit_target_words": target_microsteps,
        "audit_reverse_twins": reverse_microsteps,
    }, physical_factor_steps


def _direct_from_factor_panel(panel: LearnedActionPanel) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return panel.terminal, panel.node_reward, panel.edge_reward


def _composition_residuals(
    model: SCDMPModel,
    true_panel: TrueAuditPanel,
    direct: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    instance = true_panel.instance
    residual_f: list[np.ndarray] = []
    residual_node: list[np.ndarray] = []
    residual_edge: list[np.ndarray] = []
    all_recursive_terminal: list[np.ndarray] = []
    for prefix_length, _suffix_length in COMPOSITION_SPLITS[instance.duration]:
        prefix_word = true_panel.context_word[:prefix_length]
        suffix_word = true_panel.context_word[prefix_length:]
        prefix_panel = learned_action_panel(model, instance.state, prefix_word)
        prefix_terminal, prefix_node, prefix_edge = _direct_from_factor_panel(prefix_panel)
        (_suffix_node_score, _suffix_edge_score, suffix_terminal,
         suffix_node, suffix_edge) = candidate_factors_from_action_states(
            model, prefix_terminal[..., 0], prefix_terminal[..., 1],
            instance.state.q, suffix_word,
        )
        composed_terminal = suffix_terminal
        composed_node = prefix_node + suffix_node
        composed_edge = prefix_edge + suffix_edge
        residual_f.append(direct[0] - composed_terminal)
        residual_node.append(direct[1] - composed_node)
        residual_edge.append(direct[2] - composed_edge)
        all_recursive_terminal.extend((
            prefix_terminal,
            composed_terminal,
        ))
    return (
        np.stack(residual_f), np.stack(residual_node), np.stack(residual_edge),
        np.stack(all_recursive_terminal),
    )


def _rmse(residuals: list[np.ndarray], scale: np.ndarray | float) -> float:
    values = np.concatenate([item.reshape(-1) for item in residuals]).astype(np.float64, copy=False)
    scales = np.asarray(scale, dtype=np.float64)
    if scales.ndim == 1 and residuals[0].shape[-1] == scales.size:
        shaped = np.concatenate([item.reshape(-1, scales.size) for item in residuals], axis=0)
        return float(np.sqrt(np.mean(np.square(shaped / scales))))
    return float(np.sqrt(np.mean(np.square(values / float(scales)))))


def _class_metrics(
    records: list[dict[str, object]], corpus: Corpus, dynamics_class: str,
) -> dict[str, object]:
    selected = [row for row in records if row["dynamics_class"] == dynamics_class]
    f_scale = np.asarray((corpus.scales.e, corpus.scales.v), dtype=np.float64)
    pred_components = {
        "F": _rmse([row["prediction_f"] for row in selected], f_scale),
        "node": _rmse([row["prediction_node"] for row in selected], corpus.scales.node_reward),
        "edge": _rmse([row["prediction_edge"] for row in selected], corpus.scales.edge_reward),
    }
    comp_components = {
        "F": _rmse([row["composition_f"] for row in selected], f_scale),
        "node": _rmse([row["composition_node"] for row in selected], corpus.scales.node_reward),
        "edge": _rmse([row["composition_edge"] for row in selected], corpus.scales.edge_reward),
    }
    raw_comp = {
        "F": _rmse([row["composition_f"] for row in selected], 1.0),
        "node": _rmse([row["composition_node"] for row in selected], 1.0),
        "edge": _rmse([row["composition_edge"] for row in selected], 1.0),
    }
    regrets = np.asarray([row["oracle_regret_per_step"] for row in selected], dtype=np.float64)
    sensitivity = np.asarray([row["score_sensitive"] for row in selected], dtype=np.float64)
    return {
        "word_state_instances": len(selected),
        "action_panels": len(selected) * 81,
        "E_pred_component_rmse": pred_components,
        "E_pred": float(np.mean(list(pred_components.values()))),
        "D_comp_component_rmse": comp_components,
        "D_comp": float(np.mean(list(comp_components.values()))),
        "direct_vs_recursive_raw_rmse": raw_comp,
        "oracle_headroom_fraction_ge_0_02": float(np.mean(regrets >= 0.02)),
        "oracle_mean_regret_per_step": float(np.mean(regrets)),
        "oracle_regret_per_word_state": regrets.tolist(),
        "candidate_score_sensitivity_fraction": float(np.mean(sensitivity)),
        "candidate_score_ranges": [float(row["candidate_score_range"]) for row in selected],
    }


def _support_report(corpus: Corpus, panels: list[TrueAuditPanel]) -> dict[str, object]:
    fit_rows = [row for duration in (2, 4, 8) for row in corpus.endpoint_banks[duration]]
    fit = {
        "e": np.concatenate([row.initial.e / 1.5 for row in fit_rows]),
        "v": np.concatenate([row.initial.v / 0.6 for row in fit_rows]),
        "q": np.concatenate([row.initial.q for row in fit_rows]),
    }
    states = [panel.instance.state for panel in panels if panel.word_kind == "target"]
    coordinate_pass: dict[str, list[bool]] = {"e": [], "v": [], "q": []}
    for state in states:
        values = {"e": state.e / 1.5, "v": state.v / 0.6, "q": state.q}
        for name in coordinate_pass:
            coordinate_pass[name].append(bool(
                np.all(values[name] >= np.min(fit[name])) and np.all(values[name] <= np.max(fit[name]))
            ))
    physical_pass = [all(coordinate_pass[name][index] for name in ("e", "v"))
                for index in range(len(states))]
    return {
        "physical_states": len(states),
        "fit_input_atom_counts": {name: int(values.size) for name, values in fit.items()},
        "fit_normalized_min_max": {
            name: [float(np.min(values)), float(np.max(values))] for name, values in fit.items()
        },
        "fraction_states_in_range_by_coordinate": {
            name: float(np.mean(values)) for name, values in coordinate_pass.items()
        },
        "fraction_states_all_normalized_physical_coordinates_in_range": float(np.mean(physical_pass)),
        "gate_coordinates": ["e", "v"],
        "q_role": "reported_sign_support_diagnostic_only",
        "required_fraction": 0.90,
    }


def analyze_audit(
    algorithm_seed: int,
    models: dict[str, SCDMPModel],
    corpus: Corpus,
    resource_check: ResourceCheck | None = None,
) -> tuple[dict[str, object], dict[str, int]]:
    true_panels, microsteps, physical_factor_steps = build_true_audit_panels(
        algorithm_seed, resource_check,
    )
    learned_records: dict[str, list[dict[str, object]]] = {arm: [] for arm in models}
    nonfinite: dict[str, bool] = {arm: False for arm in models}
    direct_bound_hits: dict[str, list[np.ndarray]] = {arm: [] for arm in models}
    all_bound_hits: dict[str, list[np.ndarray]] = {arm: [] for arm in models}
    variance_values: dict[str, dict[str, list[np.ndarray]]] = {
        arm: {"predicted": [], "true": []} for arm in models
    }
    with torch.no_grad():
        for true_panel in true_panels:
            if resource_check is not None:
                resource_check()
            for arm, model in models.items():
                factors = learned_action_panel(model, true_panel.instance.state, true_panel.context_word)
                direct = _direct_from_factor_panel(factors)
                comp_f, comp_node, comp_edge, recursive_terminal = _composition_residuals(
                    model, true_panel, direct,
                )
                selected_index = joint_action_index(factors.selected_action)
                regret = (
                    true_panel.oracle_score - factor_score(
                        true_panel.node_score, true_panel.edge_score, factors.selected_action,
                    )
                ) / float(true_panel.instance.duration)
                prediction_f = direct[0] - true_panel.terminal
                prediction_node = direct[1] - true_panel.node_reward
                prediction_edge = direct[2] - true_panel.edge_reward
                learned_records[arm].append({
                    "global_index": true_panel.instance.global_index,
                    "word_kind": true_panel.word_kind,
                    "duration": true_panel.instance.duration,
                    "dynamics_class": true_panel.instance.dynamics_class,
                    "word_row": true_panel.instance.word_row,
                    "selected_action": list(factors.selected_action),
                    "selected_action_index": selected_index,
                    "oracle_action": list(true_panel.oracle_action),
                    "oracle_action_index": joint_action_index(true_panel.oracle_action),
                    "oracle_regret_per_step": float(regret),
                    "candidate_score_range": factors.score_range,
                    "score_sensitive": bool(
                        factors.score_range >= 0.02 * true_panel.instance.duration
                    ),
                    "prediction_f": prediction_f,
                    "prediction_node": prediction_node,
                    "prediction_edge": prediction_edge,
                    "composition_f": comp_f,
                    "composition_node": comp_node,
                    "composition_edge": comp_edge,
                })
                arrays = (direct[0], direct[1], direct[2], factors.node_factors,
                          factors.edge_factors,
                          comp_f, comp_node, comp_edge, recursive_terminal)
                nonfinite[arm] = nonfinite[arm] or any(not np.all(np.isfinite(item)) for item in arrays)
                direct_hit = np.logical_or(
                    np.abs(direct[0][..., 0]) == 1.5, np.abs(direct[0][..., 1]) == 0.6,
                )
                recursive_hit = np.logical_or(
                    np.abs(recursive_terminal[..., 0]) == 1.5,
                    np.abs(recursive_terminal[..., 1]) == 0.6,
                )
                direct_bound_hits[arm].append(direct_hit)
                all_bound_hits[arm].extend((direct_hit, recursive_hit))
                variance_values[arm]["predicted"].append(direct[0])
                variance_values[arm]["true"].append(true_panel.terminal)

    reversal: dict[str, object] = {}
    for dynamics_class in ("REAL", "SHAM"):
        differences: list[float] = []
        oracle_changes: list[bool] = []
        for global_index in range(64):
            pair = [panel for panel in true_panels
                    if panel.instance.global_index == global_index
                    and panel.instance.dynamics_class == dynamics_class]
            if not pair:
                continue
            target = next(panel for panel in pair if panel.word_kind == "target")
            reverse = next(panel for panel in pair if panel.word_kind == "reverse")
            node_difference = (target.node_score - reverse.node_score) / target.instance.duration
            edge_difference = (target.edge_score - reverse.edge_score) / target.instance.duration
            _positive_action, positive_max = cycle_extreme(node_difference, edge_difference)
            _negative_action, negative_max = cycle_extreme(-node_difference, -edge_difference)
            differences.append(float(max(positive_max, negative_max)))
            oracle_changes.append(target.oracle_action != reverse.oracle_action)
        reversal[dynamics_class] = {
            "twins": len(differences),
            "max_score_difference_per_step_by_twin": differences,
            "median_max_score_difference_per_step": float(np.median(differences)),
            "oracle_action_difference_fraction": float(np.mean(oracle_changes)),
            "maximum_absolute_difference": float(np.max(differences)),
        }

    arms: dict[str, object] = {}
    for arm in ("SCDMP", "SCDMP-NOCOMP"):
        records = learned_records[arm]
        class_reports = {
            dynamics_class: _class_metrics(records, corpus, dynamics_class)
            for dynamics_class in ("REAL", "SHAM")
        }
        # Pooled uses a separate reduction, never an average of class summaries.
        pooled_records = [dict(row, dynamics_class="POOLED") for row in records]
        class_reports["POOLED"] = _class_metrics(pooled_records, corpus, "POOLED")
        predicted = np.concatenate(variance_values[arm]["predicted"], axis=0)
        true = np.concatenate(variance_values[arm]["true"], axis=0)
        variance_ratio = {
            "e": float(np.var(predicted[..., 0], ddof=0) / np.var(true[..., 0], ddof=0)),
            "v": float(np.var(predicted[..., 1], ddof=0) / np.var(true[..., 1], ddof=0)),
        }
        direct_hits = np.concatenate([item.reshape(-1) for item in direct_bound_hits[arm]])
        all_hits = np.concatenate([item.reshape(-1) for item in all_bound_hits[arm]])
        arms[arm] = {
            "by_class": class_reports,
            "nonfinite_output_present": nonfinite[arm],
            "direct_F_bound_hit_fraction": float(np.mean(direct_hits)),
            "direct_and_recursive_F_bound_hit_fraction": float(np.mean(all_hits)),
            "F_output_variance_ratio": variance_ratio,
        }

    by_key = {
        arm: {(int(row["global_index"]), str(row["word_kind"])): row
              for row in learned_records[arm]}
        for arm in models
    }
    real_keys = [key for key, row in by_key["SCDMP"].items() if row["dynamics_class"] == "REAL"]
    sham_keys = [key for key, row in by_key["SCDMP"].items() if row["dynamics_class"] == "SHAM"]
    def disagreement(keys: list[tuple[int, str]]) -> float:
        return float(np.mean([
            by_key["SCDMP"][key]["selected_action_index"]
            != by_key["SCDMP-NOCOMP"][key]["selected_action_index"] for key in keys
        ]))

    return {
        "algorithm_seed": algorithm_seed,
        "denominators": audit_denominators(),
        "state_support": _support_report(corpus, true_panels),
        "physical_order_and_sham_identity": reversal,
        "arms": arms,
        "actor_disagreement": {
            "REAL": disagreement(real_keys),
            "SHAM": disagreement(sham_keys),
            "POOLED": disagreement(real_keys + sham_keys),
        },
        "true_panel_evaluation": {
            "method": (
                "12 deterministic slot-action trajectories; four node and four-by-nine "
                "directed-edge factors; exact cycle DP without joint-action trajectory enumeration"
            ),
            "physical_factor_steps": physical_factor_steps,
            "registered_analytic_panel_microsteps": {
                name: value for name, value in microsteps.items() if name != "common_audit_warmup"
            },
            "joint_action_panel_denominator": 81,
            "directly_rolled_candidates_per_word_state": 12,
            "reversal_max_absolute_method": (
                "max cycle score of target-minus-reverse factors and reverse-minus-target factors"
            ),
        },
    }, microsteps
