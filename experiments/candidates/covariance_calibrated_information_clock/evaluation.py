"""Paired fixed-tape evaluation for all eight full-rollout arms."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp, log

import numpy as np

from .config import (
    ACTIONS,
    EPSILON_SUPPORT,
    EVAL_K,
    EVAL_N,
    HORIZON,
    MU,
    OVERLAP,
    Phase,
    REGIMES,
    ROLLOUT_ARMS,
    STREAMS,
    analytic_information,
    legal_actions,
    shuffled_class,
)
from .core import (
    OriginKey,
    Packet,
    analytic_q_j,
    batch_rows,
    hmm_transition,
    latent_tape,
    normalized_loss,
    quotient_new_rows,
    select_public_action,
)
from .reference import NumericalReference
from .rng import uniform
from .training import TrainedSeed

ACTION_INDEX = {name: index for index, name in enumerate(ACTIONS)}


@dataclass(frozen=True)
class EpisodeResult:
    loss_norm: float
    commit_tick: int
    senses: int
    relays: int
    task_error: int
    posterior_nll_mean: float
    posterior_brier_mean: float
    decision_posterior_nll_mean: float
    decision_posterior_brier_mean: float
    commit_posterior_nll: float
    commit_posterior_brier: float
    q_mean: float
    j_mean: float
    unique_count_mean: float
    received_count_mean: float
    analytic_q_abs_error_mean: float
    analytic_j_abs_error_mean: float
    packet_real_symbols: int
    packet_metadata_bits: int
    complete_all_gather_row_deliveries: int
    fusion_calls: int
    actor_calls_per_agent: int
    scalar_operation_count: int | None
    peak_temporary_state: int | None
    work_count_basis: str
    plan_probability_mean: tuple[float, ...]
    selected_plan_counts: tuple[int, ...]
    trajectory: tuple[int, ...]
    decision_states: tuple[tuple[float, float, float, tuple[float, ...]], ...]


def _posterior_scores(ell: float, y: int) -> tuple[float, float]:
    probability_plus = 1.0 / (1.0 + exp(-max(-700.0, min(700.0, ell))))
    probability_true = probability_plus if y == 1 else 1.0 - probability_plus
    target = 1.0 if y == 1 else 0.0
    return -log(max(probability_true, np.finfo(np.float64).tiny)), (probability_plus - target) ** 2


def _online_work(arm: str, n: int, m: int) -> tuple[int, int] | None:
    if arm in ("CCIC", "J-SHUFFLE", "J-CLAMP"):
        return 14 * n + 392 * m + 8, 22 + 6 * m
    if arm == "RI-STRONG-v2":
        return 14 * n + 357 * m + 7, 24 + 6 * m
    return None


def _template(n: int, regime: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    m = 1 if regime == "DUP" else n
    return (
        np.zeros(m, dtype=np.float64),
        np.full(m, OVERLAP[regime], dtype=np.float64),
        np.ones(m, dtype=np.float64),
    )


def _ccic_template_j(trained: TrainedSeed, n: int, regime: str) -> float:
    z, overlap, quality = _template(n, regime)
    return trained.ccic.fusion(z, overlap, quality)[1]


def _learned_ccic_training_grand_mean(trained: TrainedSeed) -> float:
    # Equal mean over all 12 frozen (N,k,regime) cells; k is deliberately
    # present twice even though the metadata-only template does not depend on k.
    values = [
        _ccic_template_j(trained, n, regime)
        for n in (2, 5)
        for k in (1, 3)
        for regime in REGIMES
    ]
    return float(np.mean(values, dtype=np.float64))


def _prospective_j(arm: str, trained: TrainedSeed, n: int, k: int, regime: str, t: int, ell: float) -> float:
    z, overlap, quality = _template(n, regime)
    if arm in ("CCIC",):
        return trained.ccic.fusion(z, overlap, quality)[1]
    if arm == "ESS-SCALAR":
        return trained.ess.fusion(z, OVERLAP[regime])[1]
    if arm == "RI-STRONG-v2":
        return trained.ri.forward(z, OVERLAP[regime], t, k)[1]
    if arm == "INFO-FLEX":
        ccic_j = trained.ccic.fusion(z, overlap, quality)[1]
        return trained.info.forward(hmm_transition(ell, k), 0.0, ccic_j, k)[1]
    if arm == "ORIGIN-COUNT":
        return MU * MU * z.size
    if arm == "J-SHUFFLE":
        successor_n, successor_regime = shuffled_class(n, regime)
        return _ccic_template_j(trained, successor_n, successor_regime)
    if arm == "J-CLAMP":
        return _learned_ccic_training_grand_mean(trained)
    if arm == "NUMERICAL-REFERENCE":
        return analytic_information(n, regime)
    raise ValueError(arm)


def _actor_probabilities(
    arm: str,
    trained: TrainedSeed,
    reference: NumericalReference,
    n: int,
    k: int,
    regime: str,
    t: int,
    ell: float,
    legal_indices: tuple[int, ...],
) -> tuple[np.ndarray, float]:
    j_next = _prospective_j(arm, trained, n, k, regime, t, ell)
    if arm == "NUMERICAL-REFERENCE":
        selected = reference.action(n, k, regime, t, ell)
        probabilities = np.zeros(4, dtype=np.float64)
        probabilities[list(legal_indices)] = EPSILON_SUPPORT / len(legal_indices)
        probabilities[selected] += 1.0 - EPSILON_SUPPORT
    else:
        probabilities = trained.actor.probabilities(ell, j_next, t, k, legal_indices)
    return probabilities, j_next


def _evidence_update(
    arm: str,
    trained: TrainedSeed,
    ell_minus: float,
    new_rows: list[Packet],
    k: int,
    t: int,
    regime: str,
) -> tuple[float, float, float, float, float]:
    z = np.asarray([row.z for row in new_rows], dtype=np.float64)
    overlap = np.asarray([row.overlap_code for row in new_rows], dtype=np.float64)
    quality = np.ones(z.size, dtype=np.float64)
    exact_q, exact_j = analytic_q_j(z, regime)
    if arm in ("CCIC", "J-SHUFFLE", "J-CLAMP"):
        q_hat, j_hat = trained.ccic.fusion(z, overlap, quality)
        posterior = ell_minus + 2.0 * q_hat
    elif arm == "ESS-SCALAR":
        q_hat, j_hat = trained.ess.fusion(z, OVERLAP[regime])
        posterior = ell_minus + 2.0 * q_hat
    elif arm == "RI-STRONG-v2":
        delta_ell, j_hat = trained.ri.forward(z, OVERLAP[regime], t, k)
        q_hat = delta_ell / 2.0
        posterior = ell_minus + delta_ell
    elif arm == "INFO-FLEX":
        q_hat, ccic_j = trained.ccic.fusion(z, overlap, quality)
        if z.size:
            posterior, j_hat = trained.info.forward(ell_minus, q_hat, ccic_j, k)
        else:
            # The INFO-FLEX fusion call still occurs on the empty event, but
            # relay-only evidence has the frozen zero increment by definition.
            trained.info.forward(ell_minus, 0.0, 0.0, k)
            posterior, q_hat, j_hat = ell_minus, 0.0, 0.0
    elif arm == "ORIGIN-COUNT":
        q_hat, j_hat = MU * float(np.sum(z)), MU * MU * z.size
        posterior = ell_minus + 2.0 * q_hat
    elif arm == "NUMERICAL-REFERENCE":
        q_hat, j_hat = exact_q, exact_j
        posterior = ell_minus + 2.0 * exact_q
    else:
        raise ValueError(arm)
    if z.size == 0:
        posterior, q_hat, j_hat = ell_minus, 0.0, 0.0
    if not all(np.isfinite(value) for value in (posterior, q_hat, j_hat)):
        raise FloatingPointError(f"nonfinite {arm} evidence update")
    return posterior, q_hat, j_hat, exact_q, exact_j


def run_episode(
    trained: TrainedSeed,
    reference: NumericalReference,
    arm: str,
    n: int,
    k: int,
    regime: str,
    episode: int,
) -> EpisodeResult:
    hidden = latent_tape(trained.seed, episode)
    ell = 0.0
    ledger: set[OriginKey] = set()
    last_rows = [Packet.null(OVERLAP[regime]) for _ in range(n)]
    t = 0
    senses = 0
    relays = 0
    packet_rows = 0
    # The initial decision consumes the valid-null/empty-ledger table through
    # the declared arm fusion before its actor call. Each later decision uses
    # the fusion performed on the preceding block's received table.
    ell, last_q, last_j, initial_exact_q, initial_exact_j = _evidence_update(
        arm, trained, ell, [], k, t, regime
    )
    fusion_calls = 1
    initial_work = _online_work(arm, n, 0)
    online_operations = initial_work[0] if initial_work is not None else None
    online_peak = initial_work[1] if initial_work is not None else None
    actor_calls = 0
    trajectory: list[int] = []
    decision_states: list[tuple[float, float, float, tuple[float, ...]]] = []
    plan_probabilities: list[np.ndarray] = []
    selected_counts = np.zeros(4, dtype=np.int64)
    nll_values: list[float] = []
    brier_values: list[float] = []
    decision_nll_values: list[float] = []
    decision_brier_values: list[float] = []
    commit_nll = 0.0
    commit_brier = 0.0
    q_values: list[float] = [last_q]
    j_values: list[float] = [last_j]
    unique_counts: list[int] = []
    received_counts: list[int] = []
    q_errors: list[float] = [abs(last_q - initial_exact_q)]
    j_errors: list[float] = [abs(last_j - initial_exact_j)]
    while True:
        nll, brier = _posterior_scores(ell, hidden[t])
        nll_values.append(nll)
        brier_values.append(brier)
        legal_names = legal_actions(t, k)
        legal_indices = tuple(ACTION_INDEX[name] for name in legal_names)
        probabilities, j_next = _actor_probabilities(arm, trained, reference, n, k, regime, t, ell, legal_indices)
        actor_calls += 1
        plan_probabilities.append(probabilities.copy())
        decision_states.append((last_q, last_j, ell, tuple(float(value) for value in probabilities)))
        action_u = uniform(trained.seed, Phase.EVAL, STREAMS["EVAL_ACTION"], episode, t)
        action = select_public_action(probabilities, action_u, legal_indices)
        selected_counts[action] += 1
        trajectory.append(action)
        if action in (ACTION_INDEX["COMMIT_MINUS"], ACTION_INDEX["COMMIT_PLUS"]):
            commit_nll, commit_brier = nll, brier
            commit_sign = -1 if action == ACTION_INDEX["COMMIT_MINUS"] else 1
            break
        decision_nll_values.append(nll)
        decision_brier_values.append(brier)
        next_t = t + k
        ell_minus = hmm_transition(ell, k)
        if action == ACTION_INDEX["SENSE"]:
            rows = batch_rows(trained.seed, episode, next_t, n, regime, hidden[next_t])
            last_rows = rows
            senses += 1
        else:
            rows = list(last_rows)
            relays += 1
        # A valid null relay is communicated and accounted but is not an
        # evidence origin. All other valid keys are quotient-assimilated once.
        packet_rows += len(rows)
        new_rows, ledger = quotient_new_rows(rows, ledger)
        received_counts.append(len(rows))
        unique_counts.append(len(new_rows))
        fusion_calls += 1
        current_work = _online_work(arm, n, len(new_rows))
        if current_work is not None:
            if online_operations is None or online_peak is None:
                raise AssertionError("online work accounting changed basis within episode")
            online_operations += current_work[0]
            online_peak = max(online_peak, current_work[1])
        ell, q_hat, j_hat, exact_q, exact_j = _evidence_update(
            arm, trained, ell_minus, new_rows, k, t, regime
        )
        q_values.append(q_hat)
        j_values.append(j_hat)
        q_errors.append(abs(q_hat - exact_q))
        j_errors.append(abs(j_hat - exact_j))
        last_q, last_j = q_hat, j_hat
        t = next_t
    loss = normalized_loss(commit_sign, hidden[t], t, senses, relays)
    mean = lambda values: float(np.mean(values, dtype=np.float64)) if values else 0.0
    return EpisodeResult(
        loss,
        t,
        senses,
        relays,
        int(commit_sign != hidden[t]),
        mean(nll_values),
        mean(brier_values),
        mean(decision_nll_values),
        mean(decision_brier_values),
        commit_nll,
        commit_brier,
        mean(q_values),
        mean(j_values),
        mean(unique_counts),
        mean(received_counts),
        mean(q_errors),
        mean(j_errors),
        packet_rows,
        packet_rows * 64,
        packet_rows * n,
        fusion_calls,
        actor_calls,
        online_operations,
        online_peak,
        "frozen expanded grammar" if online_operations is not None else "not claim-relevant to CCIC-vs-RI-v2 work gate",
        tuple(float(value) for value in np.mean(np.vstack(plan_probabilities), axis=0, dtype=np.float64)),
        tuple(int(value) for value in selected_counts),
        tuple(trajectory),
        tuple(decision_states),
    )


def _cell_summary(results: list[EpisodeResult], reference_losses: np.ndarray) -> dict:
    scalar_fields = [
        "loss_norm",
        "commit_tick",
        "senses",
        "relays",
        "task_error",
        "posterior_nll_mean",
        "posterior_brier_mean",
        "decision_posterior_nll_mean",
        "decision_posterior_brier_mean",
        "commit_posterior_nll",
        "commit_posterior_brier",
        "q_mean",
        "j_mean",
        "unique_count_mean",
        "received_count_mean",
        "analytic_q_abs_error_mean",
        "analytic_j_abs_error_mean",
        "packet_real_symbols",
        "packet_metadata_bits",
        "complete_all_gather_row_deliveries",
        "fusion_calls",
        "actor_calls_per_agent",
    ]
    summary = {
        field: float(np.mean([getattr(result, field) for result in results], dtype=np.float64))
        for field in scalar_fields
    }
    losses = np.asarray([result.loss_norm for result in results], dtype=np.float64)
    summary["excess_loss_vs_numerical_reference"] = float(np.mean(losses - reference_losses, dtype=np.float64))
    summary["actor_plan_probability_mean"] = np.mean(
        np.asarray([result.plan_probability_mean for result in results], dtype=np.float64), axis=0
    ).tolist()
    total_selected = np.sum(
        np.asarray([result.selected_plan_counts for result in results], dtype=np.int64), axis=0
    )
    summary["selected_plan_counts"] = total_selected.tolist()
    summary["selected_plan_distribution"] = (total_selected / np.sum(total_selected)).tolist()
    work_values = [result.scalar_operation_count for result in results]
    peak_values = [result.peak_temporary_state for result in results]
    if all(value is not None for value in work_values) and all(value is not None for value in peak_values):
        summary["scalar_operation_count_mean_per_episode"] = float(np.mean(work_values, dtype=np.float64))
        summary["scalar_operation_count_total"] = int(sum(work_values))
        summary["peak_temporary_state_max"] = int(max(peak_values))
        summary["work_count_basis"] = "frozen expanded grammar; endogenous realized calls"
    else:
        summary["scalar_operation_count_mean_per_episode"] = None
        summary["scalar_operation_count_total"] = None
        summary["peak_temporary_state_max"] = None
        summary["work_count_basis"] = "not claim-relevant to CCIC-vs-RI-v2 work gate"
    return summary


def evaluate_seed(trained: TrainedSeed, reference: NumericalReference, resource_check=None) -> tuple[dict, dict]:
    cell_table: dict[str, dict] = {}
    exact_copy_records: dict[str, dict] = {}
    for n in EVAL_N:
        for k in EVAL_K:
            for regime in REGIMES:
                key = f"N={n}|k={k}|rho={regime}"
                by_arm: dict[str, list[EpisodeResult]] = {}
                for arm in ROLLOUT_ARMS:
                    by_arm[arm] = []
                    for episode in range(256):
                        if resource_check is not None and episode % 16 == 0:
                            resource_check()
                        by_arm[arm].append(run_episode(trained, reference, arm, n, k, regime, episode))
                reference_losses = np.asarray(
                    [result.loss_norm for result in by_arm["NUMERICAL-REFERENCE"]], dtype=np.float64
                )
                cell_table[key] = {
                    arm: _cell_summary(results, reference_losses)
                    for arm, results in by_arm.items()
                }
                if regime == "DUP" and k in (1, 3):
                    exact_copy_records[key] = {
                        "CCIC": [
                            {
                                "loss_norm": result.loss_norm,
                                "trajectory": result.trajectory,
                                "decision_states": result.decision_states,
                            }
                            for result in by_arm["CCIC"]
                        ]
                    }
    return cell_table, exact_copy_records
