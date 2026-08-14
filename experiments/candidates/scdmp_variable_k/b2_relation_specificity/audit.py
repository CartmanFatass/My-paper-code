from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import torch

from ..actor import candidate_factors_from_action_states, cycle_extreme, factor_score, learned_action_panel
from ..dgp import factorized_true_panel, joint_action_from_index
from ..evaluation import AuditInstance
from .config import ARMS, COMPOSITION_SPLITS
from .corpus import Corpus
from .evaluation import audit_instances
from .model import SCDMPModel
from .relations import arrays, model_call_batch

ResourceCheck = Callable[[], None]
ACTIONS81 = tuple(joint_action_from_index(i) for i in range(81))


@dataclass(frozen=True)
class TruePanel:
    instance: AuditInstance
    word_kind: str
    word: tuple[str, ...]
    terminal: np.ndarray
    node: np.ndarray
    edge: np.ndarray
    node_score: np.ndarray
    edge_score: np.ndarray
    oracle_action: tuple[int, int, int, int]
    oracle_score: float


def _expand(terminal: np.ndarray, node: np.ndarray, edge: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    f = np.empty((81, 4, 2), dtype=np.float64)
    n = np.empty((81, 4), dtype=np.float64)
    e = np.empty((81, 4), dtype=np.float64)
    for index, action in enumerate(ACTIONS81):
        digits = tuple(a + 1 for a in action)
        for slot in range(4):
            f[index, slot] = terminal[slot, digits[slot]]
            n[index, slot] = node[slot, digits[slot]]
            e[index, slot] = edge[slot, digits[slot], digits[(slot + 1) % 4]]
    return f, n, e


def _recursive(model: SCDMPModel, instance: AuditInstance, word: tuple[str, ...],
    split: int, reverse_order: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    left, right = word[:split], word[split:]
    first_word, second_word = (right, left) if reverse_order else (left, right)
    first = learned_action_panel(model, instance.state, first_word)
    _, _, outer_f, outer_n, outer_e = candidate_factors_from_action_states(
        model, first.terminal[..., 0], first.terminal[..., 1], instance.state.q, second_word)
    return outer_f, first.node_reward + outer_n, first.edge_reward + outer_e


def _composite(records: list[dict[str, object]], key: str, scales: tuple[object, object, object]) -> dict[str, object]:
    components: dict[str, float] = {}
    for family, scale in zip(("F", "node", "edge"), scales):
        arrays = [np.asarray(r[key][family], dtype=np.float64) for r in records]  # type: ignore[index]
        values = np.concatenate([a.reshape(-1, 2) if family == "F" else a.reshape(-1, 1) for a in arrays], axis=0)
        divisor = np.asarray(scale, dtype=np.float64) if family == "F" else float(scale)
        components[family] = float(np.sqrt(np.mean(np.square(values / divisor))))
    return {"components": components, "composite": float(np.mean(list(components.values())))}


def _mean_ref_composite(records: list[dict[str, object]], corpus: Corpus) -> float:
    residuals = []
    for r in records:
        truth = r["truth"]
        residuals.append({"F": np.asarray([corpus.means["e"], corpus.means["v"]]) - truth["F"],
                          "node": corpus.means["node_reward"] - truth["node"],
                          "edge": corpus.means["edge_reward"] - truth["edge"]})
    scales = (np.asarray((corpus.scales.e, corpus.scales.v)), corpus.scales.node_reward, corpus.scales.edge_reward)
    return float(_composite([{"residual": x} for x in residuals], "residual", scales)["composite"])


def _support(corpus: Corpus, instances: list[AuditInstance]) -> dict[str, object]:
    fit = [r for d in (2, 4, 8) for r in corpus.endpoint_banks[d]]
    min_e = np.min(np.stack([r.initial.e for r in fit]), axis=0)
    max_e = np.max(np.stack([r.initial.e for r in fit]), axis=0)
    min_v = np.min(np.stack([r.initial.v for r in fit]), axis=0)
    max_v = np.max(np.stack([r.initial.v for r in fit]), axis=0)
    flags = [bool(np.all((x.state.e >= min_e) & (x.state.e <= max_e)) and
                  np.all((x.state.v >= min_v) & (x.state.v <= max_v))) for x in instances]
    q_ok = all(set(x.state.q.tolist()).issubset({-1.0, 1.0}) for x in instances)
    return {"states": 64, "states_all_e_v_coordinates_in_range": int(sum(flags)),
            "required": 61, "continuous_gate_pass": sum(flags) >= 61,
            "q_exact_membership_pass": q_ok,
            "coordinatewise_fit_minmax": {"e_min": min_e.tolist(), "e_max": max_e.tolist(),
                                           "v_min": min_v.tolist(), "v_max": max_v.tolist()}}


def _dhom(model: SCDMPModel, corpus: Corpus) -> dict[str, object]:
    pair_mse = {x: [] for x in ("F", "node", "edge")}
    counts: dict[str, int] = {}
    with torch.no_grad():
        for duration in (4, 8):
            rows = corpus.homogeneous_probe[duration]
            counts[str(duration)] = len(rows)
            e, v, q, actions, words = arrays(rows)
            split = duration // 2
            halves = [w[:split] for w in words]
            direct = model_call_batch(model, e, v, q, actions, words)
            first = model_call_batch(model, e, v, q, actions, halves)
            outer = model_call_batch(model, first[0][:, :, 0], first[0][:, :, 1], q, actions, halves)
            residuals = (direct[0] - outer[0], direct[1] - first[1] - outer[1],
                         direct[2] - first[2] - outer[2])
            scales = (torch.tensor((corpus.scales.e, corpus.scales.v)), corpus.scales.node_reward,
                      corpus.scales.edge_reward)
            for name, residual, scale in zip(pair_mse, residuals, scales):
                pair_mse[name].append(float(torch.mean(torch.square(residual / scale)).item()))
    rms = {name: float(np.sqrt(np.mean(values))) for name, values in pair_mse.items()}
    return {"row_certificate": counts, "total_rows": sum(counts.values()),
            "component_rmse": rms, "Dhom": float(np.mean(list(rms.values()))),
            "descriptive_only": True}


def analyze_audit(algorithm_seed: int, models: dict[str, SCDMPModel], corpus: Corpus,
    resource_check: ResourceCheck | None = None) -> tuple[dict[str, object], dict[str, int]]:
    instances, warmup = audit_instances(algorithm_seed)
    true_panels: list[TruePanel] = []
    factor_steps = {"target": 0, "reverse": 0}
    for instance in instances:
        for kind, word in (("target", instance.target_word), ("reverse", instance.reverse_word)):
            terminal, node, edge, node_score, edge_score, steps = factorized_true_panel(instance.state, word)
            action, score = cycle_extreme(node_score, edge_score)
            true_panels.append(TruePanel(instance, kind, word, terminal, node, edge,
                                         node_score, edge_score, action, score))
            factor_steps[kind] += steps
    if factor_steps != {"target": 6_912, "reverse": 6_912}:
        raise RuntimeError(f"B2 scalar-agent factor-transition mismatch: {factor_steps}")
    records: dict[str, list[dict[str, object]]] = {arm: [] for arm in ARMS}
    with torch.no_grad():
        for truth in true_panels:
            true_expanded = _expand(truth.terminal, truth.node, truth.edge)
            for arm in ARMS:
                if resource_check is not None:
                    resource_check()
                panel = learned_action_panel(models[arm], truth.instance.state, truth.word)
                direct = (panel.terminal, panel.node_reward, panel.edge_reward)
                direct_expanded = _expand(*direct)
                corr, wrong = [], []
                for split, _ in COMPOSITION_SPLITS[truth.instance.duration]:
                    corr.append(_expand(*_recursive(models[arm], truth.instance, truth.word, split, False)))
                    wrong.append(_expand(*_recursive(models[arm], truth.instance, truth.word, split, True)))
                corr_res = {name: np.stack([direct_expanded[i] - x[i] for x in corr])
                            for i, name in enumerate(("F", "node", "edge"))}
                wrong_res = {name: np.stack([direct_expanded[i] - x[i] for x in wrong])
                             for i, name in enumerate(("F", "node", "edge"))}
                pred_res = {name: direct_expanded[i] - true_expanded[i]
                            for i, name in enumerate(("F", "node", "edge"))}
                regret = (truth.oracle_score - factor_score(truth.node_score, truth.edge_score,
                                                             panel.selected_action)) / truth.instance.duration
                records[arm].append({"global_index": truth.instance.global_index,
                    "class": truth.instance.dynamics_class, "kind": truth.word_kind,
                    "duration": truth.instance.duration, "selected_action": panel.selected_action,
                    "oracle_regret": float(max(0.0, regret)), "score_range": panel.score_range,
                    "corr": corr_res, "wrong": wrong_res, "pred": pred_res,
                    "truth": {name: true_expanded[i] for i, name in enumerate(("F", "node", "edge"))},
                    "predicted_F": direct_expanded[0]})
    scales = (np.asarray((corpus.scales.e, corpus.scales.v)), corpus.scales.node_reward, corpus.scales.edge_reward)
    arm_reports: dict[str, object] = {}
    for arm in ARMS:
        by_class = {}
        for cls in ("REAL", "SHAM"):
            chosen = [r for r in records[arm] if r["class"] == cls]
            corr = _composite(chosen, "corr", scales)
            wrong = _composite(chosen, "wrong", scales)
            pred = _composite(chosen, "pred", scales)
            ref = _mean_ref_composite(chosen, corpus)
            if not np.isfinite(ref) or ref <= 1e-12:
                raise RuntimeError("invalid target MEAN-REF denominator")
            by_class[cls] = {"Dcorr": corr["composite"], "Dcorr_components": corr["components"],
                "Dwrong": wrong["composite"], "Dwrong_components": wrong["components"],
                "Epred": pred["composite"], "Epred_components": pred["components"],
                "mean_ref_rmse": ref, "competence_ratio": float(pred["composite"]) / ref,
                "Q": float(np.mean([r["oracle_regret"] for r in chosen])),
                "oracle_regret_fraction_ge_0_015": float(np.mean([r["oracle_regret"] >= .015 for r in chosen])),
                "score_range_pass_fraction": float(np.mean([r["score_range"] >= .015 * r["duration"] for r in chosen]))}
        real = [r for r in records[arm] if r["class"] == "REAL"]
        predicted = np.stack([r["predicted_F"] for r in real])
        true = np.stack([r["truth"]["F"] for r in real])
        ratios: dict[str, float] = {}
        denominator_valid = True
        for slot in range(4):
            for coord, name in enumerate(("e", "v")):
                denom = np.var(true[:, :, slot, coord], ddof=0)
                denominator_valid &= bool(np.isfinite(denom) and denom > 0)
                ratios[f"slot{slot+1}_{name}"] = float(np.var(predicted[:, :, slot, coord], ddof=0) / denom) if denom > 0 else float("nan")
        bound_hits = np.logical_or(np.abs(predicted[..., 0]) == 1.5, np.abs(predicted[..., 1]) == .6)
        arm_reports[arm] = {"by_class": by_class, "variance_ratios": ratios,
            "true_variance_denominators_valid": denominator_valid,
            "F_bound_hit_fraction": float(np.mean(bound_hits)), "Dhom": _dhom(models[arm], corpus)}
    paired = {}
    base = {(r["global_index"], r["kind"]): r for r in records["SCDMP-CORRECT"] if r["class"] == "REAL"}
    for control in ("FREE-DIRECT", "SCDMP-ORDER-SHUFFLE"):
        other = {(r["global_index"], r["kind"]): r for r in records[control] if r["class"] == "REAL"}
        paired[control] = float(np.mean([base[k]["selected_action"] != other[k]["selected_action"] for k in base]))
    reversal = {}
    for cls in ("REAL", "SHAM"):
        diffs, changed = [], []
        class_panels = [p for p in true_panels if p.instance.dynamics_class == cls]
        for index in sorted({p.instance.global_index for p in class_panels}):
            target = next(p for p in class_panels if p.instance.global_index == index and p.word_kind == "target")
            reverse = next(p for p in class_panels if p.instance.global_index == index and p.word_kind == "reverse")
            dn = (target.node_score - reverse.node_score) / target.instance.duration
            de = (target.edge_score - reverse.edge_score) / target.instance.duration
            _, pos = cycle_extreme(dn, de); _, neg = cycle_extreme(-dn, -de)
            diffs.append(max(pos, neg)); changed.append(target.oracle_action != reverse.oracle_action)
        reversal[cls] = {"twins": len(diffs), "median_max_score_difference_per_step": float(np.median(diffs)),
                         "maximum_absolute_score_difference_per_step": float(np.max(diffs)),
                         "oracle_action_difference_fraction": float(np.mean(changed)),
                         "oracle_actions_identical": not any(changed)}
    return {"algorithm_seed": algorithm_seed, "denominators": {"physical_states": 64,
            "real_word_states": 64, "sham_word_states": 64, "joint_actions": 81},
            "support": _support(corpus, instances), "physical_order": reversal,
            "arms": arm_reports, "correct_action_disagreement": paired,
            "factorized_evaluation": {"target_scalar_agent_transitions": factor_steps["target"],
                                      "reverse_scalar_agent_transitions": factor_steps["reverse"]}}, {
            "common_audit_warmup": warmup, "audit_target_words": 46_656,
            "audit_reverse_twins": 46_656}
