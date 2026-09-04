"""Frozen estimands, confidence bounds, support checks, and branch precedence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

import numpy as np
import torch

from .config import FrozenConfig, HELDOUT_N, REGIMES
from .evaluation import CheckpointPanels, ReplayEpisode


def cvar10(values: torch.Tensor) -> float:
    """Registered empirical lower ten-percent mean for exactly 128 episodes."""
    ordered = torch.sort(values.flatten()).values
    if ordered.numel() != 128:
        raise ValueError("B1 CVaR10 is registered only for 128 episodes")
    return float((ordered[:12].sum() + 0.8 * ordered[12]).div(12.8))


def registered_even_median(values: torch.Tensor) -> float:
    """The card's fixed arithmetic mean of the 64th and 65th ordered 128 values."""
    ordered = torch.sort(values.flatten()).values
    if ordered.numel() != 128:
        raise ValueError("registered volume support uses exactly 128 episodes")
    return float((ordered[63] + ordered[64]).mul(0.5))


def student_t_bound(values: Iterable[float], confidence: float, side: Literal["lower", "upper"]) -> float:
    """One-sided Student-t bound over the fixed 12 independent training seeds."""
    from scipy.stats import t as student_t

    x = np.asarray(tuple(values), dtype=np.float64)
    if x.size != 12:
        raise ValueError("all registered seed-level bounds use exactly twelve seeds")
    sem = x.std(ddof=1) / np.sqrt(x.size)
    critical = student_t.ppf(confidence, x.size - 1)
    return float(x.mean() - critical * sem if side == "lower" else x.mean() + critical * sem)


def endpoint_headroom(learned_panels: Iterable[CheckpointPanels], endpoint: Literal["P", "R"]) -> bool:
    """Check the registered equal-seed mean oracle headroom in every held-out cell."""
    rows = tuple(learned_panels)
    if len(rows) != 12:
        raise ValueError("oracle headroom has one mean over exactly twelve seed-level summaries")
    for n in HELDOUT_N:
        for regime in REGIMES:
            summaries = [_mean_and_cvar(panel, n, regime)[0 if endpoint == "P" else 1] for panel in rows]
            if float(np.mean(summaries)) > 0.94:
                return False
    return True


@dataclass(frozen=True, slots=True)
class SeedMetrics:
    performance: float
    robustness: float
    quadrature: float
    return_contribution: float
    action_tv: float
    gamma: float
    noise: float
    self_attenuation: dict[int, float]
    architecture_attenuation: dict[int, float]
    bypass: dict[int, float]
    association_tv: dict[int, float | None]
    association_return: dict[int, float | None]


def _mean_and_cvar(panels: CheckpointPanels, n: int, regime: str) -> tuple[float, float]:
    values = panels.ordinary_intact[(n, regime)]
    return float(values.mean()), cvar10(values)


def _cut_normalized_error(record: ReplayEpisode) -> float:
    return float((record.cut_raw_mass.sub(record.true_local_mass).abs().div(record.local_volume[None, :])).mean())


def _spearman(x: list[float], y: list[float]) -> float | None:
    from scipy.stats import spearmanr

    if np.ptp(np.asarray(x)) == 0.0 or np.ptp(np.asarray(y)) == 0.0:
        return None
    return float(spearmanr(x, y).statistic)


def seed_metrics(vqfp: CheckpointPanels, learned: CheckpointPanels) -> SeedMetrics:
    """Compute only the preregistered seed-level quantities, before inference."""
    differences: dict[tuple[int, str], tuple[float, float]] = {}
    for n in (4, 6, 10, 14):
        for regime in REGIMES:
            vm, vr = _mean_and_cvar(vqfp, n, regime)
            lm, lr = _mean_and_cvar(learned, n, regime)
            differences[(n, regime)] = (vm - lm, vr - lr)
    performance = min(differences[(n, regime)][0] for n in HELDOUT_N for regime in REGIMES)
    robustness = min(differences[(n, regime)][1] for n in HELDOUT_N for regime in REGIMES)
    heldout = np.mean([differences[(n, regime)][0] for n in HELDOUT_N for regime in REGIMES])
    train = np.mean([differences[(n, regime)][0] for n in (6, 10) for regime in REGIMES])
    self_attenuation: dict[int, float] = {}
    architecture_attenuation: dict[int, float] = {}
    bypass: dict[int, float] = {}
    association_tv: dict[int, float | None] = {}
    association_return: dict[int, float | None] = {}
    quadrature_by_n, tv_by_n = [], []
    for n in HELDOUT_N:
        v_records, l_records = vqfp.conflict_replay[n], learned.conflict_replay[n]
        intact_error = np.mean([float((r.intact_raw_mass.sub(r.true_local_mass).abs().div(r.local_volume[None, :])).mean()) for r in v_records])
        cut_error = np.mean([_cut_normalized_error(r) for r in v_records])
        quadrature_by_n.append(cut_error - intact_error)
        self_attenuation[n] = float(vqfp.conflict_intact[n].mean() - vqfp.conflict_cut[n].mean())
        architecture_attenuation[n] = float((vqfp.conflict_intact[n].mean() - learned.conflict_intact[n].mean())
                                           - (vqfp.conflict_cut[n].mean() - learned.conflict_cut[n].mean()))
        learned_cut_error = np.mean([_cut_normalized_error(r) for r in l_records])
        bypass[n] = cut_error - learned_cut_error
        tv_by_n.append(float(torch.stack([r.action_tv for r in v_records]).mean()))
        d_error = [float(r.quadrature_error_delta) for r in v_records]
        d_tv = [float(r.action_tv) for r in v_records]
        d_return = [float(r.intact_return - r.cut_return) for r in v_records]
        association_tv[n] = _spearman(d_error, d_tv)
        association_return[n] = _spearman(d_error, d_return)
    noise = min(float(vqfp.noisy[n].mean() - learned.noisy[n].mean()) for n in HELDOUT_N)
    return SeedMetrics(performance, robustness, min(quadrature_by_n),
                       min(min(self_attenuation.values()), min(architecture_attenuation.values())),
                       min(tv_by_n), float(heldout - train), noise, self_attenuation,
                       architecture_attenuation, bypass, association_tv, association_return)


@dataclass(frozen=True, slots=True)
class Inference:
    lower_performance: float
    lower_robustness: float
    upper_performance: float
    upper_robustness: float
    lower_quadrature: float
    lower_return_contribution: float
    lower_action_tv: float
    upper_noise: float


def infer(metrics: Iterable[SeedMetrics]) -> Inference:
    rows = tuple(metrics)
    return Inference(
        student_t_bound((r.performance for r in rows), 0.975, "lower"),
        student_t_bound((r.robustness for r in rows), 0.975, "lower"),
        student_t_bound((r.performance for r in rows), 0.975, "upper"),
        student_t_bound((r.robustness for r in rows), 0.975, "upper"),
        student_t_bound((r.quadrature for r in rows), 0.98333333, "lower"),
        student_t_bound((r.return_contribution for r in rows), 0.98333333, "lower"),
        student_t_bound((r.action_tv for r in rows), 0.98333333, "lower"),
        student_t_bound((r.noise for r in rows), 0.95, "upper"),
    )


def binding_support(vqfp_panels: CheckpointPanels, learned_panels: CheckpointPanels,
                    config: FrozenConfig) -> bool:
    """VQFP supplies support facts; both arms must pass the structural nulls."""
    for n in HELDOUT_N:
        for panel in ("CLUSTER", "MEASURE-CONFLICT"):
            if registered_even_median(vqfp_panels.volume_cv[(n, panel)]) < 0.25:
                return False
        if float(vqfp_panels.association_conflict[n].mean()) < 0.08:
            return False
        actions = torch.cat([record.intact_actions.flatten() for record in vqfp_panels.conflict_replay[n]])
        if int(torch.sum(torch.bincount(actions, minlength=3).float() / actions.numel() >= 0.05)) < 2:
            return False
        if not all(result.passed for (control_n, _), result in vqfp_panels.controls.items() if control_n == n):
            return False
        if not all(result.passed for (control_n, _), result in learned_panels.controls.items() if control_n == n):
            return False
    return True


def aggregate_associations(metrics: Iterable[SeedMetrics], field: Literal["association_tv", "association_return"]) -> float | None:
    """Fisher-z aggregate separately for the two fixed associations, never dropping a cell."""
    rows = tuple(metrics)
    values = [getattr(row, field)[n] for row in rows for n in HELDOUT_N]
    if any(value is None for value in values):
        return None
    clipped = np.clip(np.asarray(values, dtype=float), -1 + 1e-12, 1 - 1e-12)
    return float(np.tanh(np.mean(np.arctanh(clipped))))


def direct_classification(inference: Inference, *, p_available: bool, r_available: bool,
                          binding_ok: bool, noisy_reversal: bool) -> str:
    """Apply the registered branch precedence; U_P/U_R appear only where authorized."""
    p_positive, r_positive = p_available and inference.lower_performance > 0.03, r_available and inference.lower_robustness > 0.03
    p_reverse, r_reverse = p_available and inference.upper_performance < -0.03, r_available and inference.upper_robustness < -0.03
    if (p_positive and r_reverse) or (r_positive and p_reverse):
        return "DIRECT_ENDPOINT_TRADEOFF"
    if p_positive or r_positive:
        return "DIRECT_VALUE_PLUS_CORRECTED_BINDING" if binding_ok else "DIRECT_VALUE_WITHOUT_BINDING"
    if p_reverse or r_reverse:
        return "MATERIAL_COMPARATOR_ADVANTAGE"
    if p_available and r_available and inference.upper_performance < 0.03 and inference.upper_robustness < 0.03:
        return "FAMILY_DELETE"
    return "STATISTICALLY_INDETERMINATE"
