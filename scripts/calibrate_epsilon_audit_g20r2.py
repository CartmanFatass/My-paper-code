"""Measure `epsilon_audit` via the registered replicate-split null calibration.

Implements the frozen procedure in
``docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2.md``, section 11,
subsection "`epsilon_audit` is not yet registered -- the screen is withheld".

Section 2 gates Stage A identification on ``LCB95(S_source) > epsilon_audit^2``,
where ``epsilon_audit`` is *only* the numerical / paired-rollout resolution
floor of the audit estimator -- never a chosen effect size. Section 11 records
why the obvious null is wrong: probing the factual action against itself under
exact common random numbers makes both arms bit-identical and returns exactly
zero, which would register a floor no source could ever fail. The registered
null instead measures the estimator's own resolution directly:

For a fixed history (one audited decision point) and a fixed pair of distinct
probe actions -- drawn by the exact same seeded mechanism
(``collect_audit_clusters``) Stage A itself uses, so common random numbers stay
intact -- estimate the oracle contrast

    Delta(h, a, a') = Gbar(h, a) - Gbar(h, a')

**twice**, from two disjoint suffix-replicate sets, each of the registered
size ``AUDIT_SUFFIX_REPLICATES``. Because both estimates target the exact same
fixed history and the exact same fixed action pair, their true difference is
exactly zero; the observed difference ``d = Delta_1 - Delta_2`` is therefore
pure estimator resolution, not signal. ``|d| / sqrt(2)`` converts that
doubled-noise difference back to the resolution of one single full-size
(``AUDIT_SUFFIX_REPLICATES``-replicate) estimate -- each half draws its own
full ``AUDIT_SUFFIX_REPLICATES`` suffix replicates from disjoint replicate-index
blocks, so ``Var(d) = 2 * Var(one full-size estimate)`` and
``Var(|d| / sqrt(2)) = Var(one full-size estimate)`` exactly.

`epsilon_audit` is registered as the *upper tail* of the pooled
``|d| / sqrt(2)`` distribution across every audited decision point (clustered
per episode-ledger, matching design section 5's clustering convention) --
concretely the larger of the raw 95th-percentile point estimate and a
clustered-bootstrap 95th-percentile upper bound, so a small audit sample does
not undershoot the floor.

Three conditions the design requires for the number to be meaningful, all
honored here by using this module's own configured constants as defaults:
run at the configured audit scale (``AUDIT_EPISODES``, ``K=8``, the registered
``AUDIT_SUFFIX_REPLICATES``); measure per source (G17 and G18 have different
return scales); and never write the result back into the design document --
this script only measures and reports.

No training of any kind happens here, and nothing in this module calls
``run_screen``. The declared suffix policy this calibration probes is the same
freshly constructed, untrained anchor model
``scripts.screen_anchor_action_advantage_g20r2.make_model`` would build at the
start of ``_train_source`` (identical seeding via ``configure_runtime``) --
Stage A's floor is a property of the environment's own suffix-noise
resolution under a fixed policy, not of a trained critic or actor, and no
training compute is authorized by this task.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Callable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchor_action_advantage_g20r2 import FastAnchorActionAdvantagePolicy
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner
from scripts.screen_anchor_action_advantage_g20r2 import (
    AUDIT_EPISODES,
    AUDIT_PROBE_POINTS_PER_EPISODE,
    AUDIT_SUFFIX_REPLICATES,
    BASELINE_SAMPLES_K_CONFIGURED,
    GAMMA,
    SEEDS,
    _audit_probe_points,
    _episode_active_counts,
    make_model,
    paired_replay_return,
)

# Design section 11: "Raise the number of calibration points well above the
# screen's ~24" (``AUDIT_EPISODES * AUDIT_PROBE_POINTS_PER_EPISODE`` = 8 * 3).
# The per-estimate Monte Carlo budget (K, AUDIT_SUFFIX_REPLICATES) stays at
# its configured value -- only ``audit_episodes`` is raised here, since
# ``_audit_probe_points`` always returns exactly ``AUDIT_PROBE_POINTS_PER_
# EPISODE`` points per episode (the screen's own per-episode budget is not a
# calibration knob); more episodes is the only lever that raises the total
# point count without touching resolution. 40 episodes * 3 points/episode =
# 120 points per source, five times the screen's own count.
CALIBRATION_AUDIT_EPISODES = 40

if CALIBRATION_AUDIT_EPISODES <= AUDIT_EPISODES:
    raise ValueError(
        "G20R2 epsilon_audit calibration must sample well above the screen's "
        f"own audit_episodes={AUDIT_EPISODES} (design section 11); "
        f"CALIBRATION_AUDIT_EPISODES={CALIBRATION_AUDIT_EPISODES} does not"
    )


def _source_geometry(source: str) -> tuple[int, int, int]:
    """``(horizon, capacity, action_dim)`` -- identical to the screen's own dims."""

    if source == "g17":
        return g17_source.HORIZON, g17_source.CAPACITY, g17_source.ACTION_DIM
    if source == "g18":
        return battery_source.HORIZON, battery_source.CAPACITY, battery_source.ACTION_DIM
    raise ValueError(f"unknown G20R2 source: {source}")


def _make_ledger(source: str, episode_id: int) -> Any:
    """Identical ledger construction to ``collect_audit_clusters`` per source."""

    if source == "g17":
        return g17_source.make_ledger(
            episode_id,
            master_seed=SEEDS["g17"]["audit"],
            profiles=g17_source.TRAIN_PROFILES,
        )
    if source == "g18":
        return battery_source.make_ledger(
            battery_source.GATE_SLOT_ORDERS[
                episode_id % len(battery_source.GATE_SLOT_ORDERS)
            ]
        )
    raise ValueError(f"unknown G20R2 source: {source}")


def _env_factory(source: str, ledger: Any) -> Callable[[], Any]:
    if source == "g17":
        return lambda: g17_source.ContinuousServiceRosterEnv(ledger)
    if source == "g18":
        return lambda: battery_source.BatteryRosterEnv(ledger)
    raise ValueError(f"unknown G20R2 source: {source}")


@dataclass
class ProbePointDelta:
    """One audited decision point's replicate-split resolution measurement."""

    source: str
    episode_id: int
    point_index: int
    intervention_time: int
    intervention_position: int
    delta_set_a: float
    delta_set_b: float
    d: float
    d_over_sqrt2: float


def _replicate_set_return(
    model: FastAnchorActionAdvantagePolicy,
    env_factory: Callable[[], Any],
    *,
    horizon: int,
    capacity: int,
    action_dim: int,
    intervention_time: int,
    intervention_position: int,
    probe_action: torch.Tensor,
    prefix_noise: torch.Tensor,
    audit_seed: int,
    episode_id: int,
    point_index: int,
    replicate_offset: int,
    num_replicates: int,
) -> float:
    """Mean discounted return over ``num_replicates`` disjoint suffix draws.

    Replicate indices span ``replicate_offset .. replicate_offset +
    num_replicates - 1``. Seeding is byte-identical to
    ``collect_audit_clusters``'s own suffix-generator convention
    (``SeedSequence([audit_seed, episode_id, 703, point_index, replicate])``)
    for any replicate index a real screen run would also draw
    (``< AUDIT_SUFFIX_REPLICATES``), and is a disjoint extension of that same
    stream for indices beyond it -- so the "first" replicate set this
    function can build for a real screen's own replicate count is bit-for-bit
    what that screen would compute, and the "second" set never overlaps it.
    """

    returns: list[float] = []
    for offset in range(int(num_replicates)):
        replicate = replicate_offset + offset
        suffix_generator = np.random.default_rng(
            np.random.SeedSequence(
                [int(audit_seed), int(episode_id), 703, point_index, replicate]
            )
        )
        suffix_noise = prefix_noise.clone()
        suffix_noise[intervention_time:] = torch.as_tensor(
            suffix_generator.standard_normal(
                (horizon - intervention_time, capacity, action_dim)
            ).astype(np.float32)
        )
        returned, *_ = paired_replay_return(
            model,
            env_factory,
            horizon=horizon,
            capacity=capacity,
            hidden_dim=model.hidden_dim,
            gamma=GAMMA,
            intervention_time=intervention_time,
            intervention_position=intervention_position,
            probe_action=probe_action,
            noise=suffix_noise,
        )
        returns.append(returned)
    return float(np.mean(returns))


def _assert_distinct_pair(
    action_a: torch.Tensor,
    action_b: torch.Tensor,
    *,
    source: str,
    episode_id: int,
    point_index: int,
) -> None:
    """Refuse a degenerate identical pair rather than silently measuring it.

    Design section 11 records the naive null's exact failure: probing the
    factual action against itself under exact common random numbers makes
    both arms bit-identical and returns exactly zero, registering a floor no
    source could ever fail. This is the same failure shape one routing
    position removed -- an (accidentally) identical probe pair here would
    silently manufacture the same degenerate zero, so it fails closed instead.
    """

    if torch.allclose(action_a, action_b):
        raise ValueError(
            "G20R2 epsilon_audit calibration requires a genuinely distinct "
            f"probe pair at source={source} episode={episode_id} "
            f"point={point_index} -- got two (numerically) identical probes, "
            "which would reproduce the degenerate self-vs-self null design "
            "section 11 explicitly retires"
        )


def _probe_point_delta(
    model: FastAnchorActionAdvantagePolicy,
    source: str,
    ledger: Any,
    *,
    episode_id: int,
    point_index: int,
    intervention_time: int,
    intervention_position: int,
    k: int,
    suffix_replicates: int,
) -> ProbePointDelta:
    horizon, capacity, action_dim = _source_geometry(source)
    env_factory = _env_factory(source, ledger)
    audit_seed = SEEDS[source]["audit"]

    # Prefix noise: identical seeding to `collect_audit_clusters` (stream 701)
    # so the factual history up to the intervention is bit-for-bit what a
    # real Stage A audit would replay.
    prefix_generator = np.random.default_rng(
        np.random.SeedSequence([int(audit_seed), int(episode_id), 701])
    )
    prefix_noise = torch.as_tensor(
        prefix_generator.standard_normal((horizon, capacity, action_dim)).astype(
            np.float32
        )
    )

    # Anchor mean/std at the intervention, then K anchor-resampled probes:
    # identical seeding to `collect_audit_clusters` (streams 700/702) so this
    # calibration draws the *same* probe-action pairing Stage A itself would.
    std = torch.exp(model.log_std.clamp(-5.0, 2.0)).detach()
    _, _raw0, mean_at_intervention, _std, _active = paired_replay_return(
        model,
        env_factory,
        horizon=horizon,
        capacity=capacity,
        hidden_dim=model.hidden_dim,
        gamma=GAMMA,
        intervention_time=intervention_time,
        intervention_position=intervention_position,
        probe_action=torch.tanh(torch.zeros(action_dim)),
        noise=prefix_noise,
    )
    probe_generator = np.random.default_rng(
        np.random.SeedSequence([int(audit_seed), int(episode_id), 702, point_index])
    )
    probe_actions: list[torch.Tensor] = []
    for _ in range(int(k)):
        eps = torch.as_tensor(
            probe_generator.standard_normal(action_dim).astype(np.float32)
        )
        probe_actions.append(torch.tanh(mean_at_intervention + std * eps))

    if len(probe_actions) < 2:
        raise ValueError(
            "G20R2 epsilon_audit calibration requires at least 2 anchor "
            "probes to form a fixed pair of distinct probe actions"
        )
    action_a, action_b = probe_actions[0], probe_actions[1]
    _assert_distinct_pair(
        action_a, action_b, source=source, episode_id=episode_id, point_index=point_index
    )

    def _set_delta(replicate_offset: int) -> float:
        return_a = _replicate_set_return(
            model,
            env_factory,
            horizon=horizon,
            capacity=capacity,
            action_dim=action_dim,
            intervention_time=intervention_time,
            intervention_position=intervention_position,
            probe_action=action_a,
            prefix_noise=prefix_noise,
            audit_seed=audit_seed,
            episode_id=episode_id,
            point_index=point_index,
            replicate_offset=replicate_offset,
            num_replicates=suffix_replicates,
        )
        return_b = _replicate_set_return(
            model,
            env_factory,
            horizon=horizon,
            capacity=capacity,
            action_dim=action_dim,
            intervention_time=intervention_time,
            intervention_position=intervention_position,
            probe_action=action_b,
            prefix_noise=prefix_noise,
            audit_seed=audit_seed,
            episode_id=episode_id,
            point_index=point_index,
            replicate_offset=replicate_offset,
            num_replicates=suffix_replicates,
        )
        return return_a - return_b

    delta_set_a = _set_delta(0)
    delta_set_b = _set_delta(int(suffix_replicates))
    d = delta_set_a - delta_set_b
    return ProbePointDelta(
        source=source,
        episode_id=episode_id,
        point_index=point_index,
        intervention_time=intervention_time,
        intervention_position=intervention_position,
        delta_set_a=delta_set_a,
        delta_set_b=delta_set_b,
        d=d,
        d_over_sqrt2=abs(d) / math.sqrt(2.0),
    )


def _epsilon_audit_from_deltas(
    rows_by_episode: dict[int, list[ProbePointDelta]],
    *,
    quantile: float = 0.95,
    num_resamples: int = 2000,
    seed: int,
) -> dict[str, Any]:
    """Upper-tail `|d| / sqrt(2)` statistic, clustered per episode-ledger.

    Registers `epsilon_audit` as the larger of the raw pooled quantile point
    estimate and a clustered-bootstrap upper bound on that same quantile, so
    a small audit sample does not undershoot the resolution floor -- the same
    conservative-by-construction spirit as every other clustered-bootstrap
    gate in this design (design section 5).
    """

    clusters = [
        torch.tensor([row.d_over_sqrt2 for row in rows], dtype=torch.float64)
        for rows in rows_by_episode.values()
        if rows
    ]
    if len(clusters) < 2:
        raise ValueError(
            "G20R2 epsilon_audit calibration requires at least 2 episode "
            "clusters with observations"
        )
    pooled = torch.cat(clusters)
    point_quantile = float(torch.quantile(pooled, quantile))

    generator = torch.Generator()
    generator.manual_seed(int(seed))
    n = len(clusters)
    resampled = torch.empty(int(num_resamples), dtype=torch.float64)
    for index in range(int(num_resamples)):
        pick = torch.randint(0, n, (n,), generator=generator)
        pooled_resample = torch.cat([clusters[int(i)] for i in pick])
        resampled[index] = torch.quantile(pooled_resample, quantile)
    cluster_bootstrap_upper = float(torch.quantile(resampled, quantile))

    epsilon_audit = max(point_quantile, cluster_bootstrap_upper)
    return {
        "epsilon_audit": epsilon_audit,
        "upper_tail_quantile": quantile,
        "point_quantile": point_quantile,
        "cluster_bootstrap_upper": cluster_bootstrap_upper,
        "num_clusters": n,
        "num_observations": int(pooled.numel()),
        "min_abs_d_over_sqrt2": float(pooled.min()),
        "mean_abs_d_over_sqrt2": float(pooled.mean()),
        "median_abs_d_over_sqrt2": float(torch.quantile(pooled, 0.5)),
        "max_abs_d_over_sqrt2": float(pooled.max()),
        "pooled_d_over_sqrt2_by_episode": {
            str(episode_id): [row.d_over_sqrt2 for row in rows]
            for episode_id, rows in rows_by_episode.items()
        },
    }


def calibrate_source(
    source: str,
    *,
    audit_episodes: int = CALIBRATION_AUDIT_EPISODES,
    points_per_episode: int = AUDIT_PROBE_POINTS_PER_EPISODE,
    suffix_replicates: int = AUDIT_SUFFIX_REPLICATES,
    k: int = BASELINE_SAMPLES_K_CONFIGURED,
) -> dict[str, Any]:
    """Run the replicate-split null calibration for one source.

    ``suffix_replicates`` and ``k`` default to the module's own configured
    per-estimate Monte Carlo budget, matching design section 11's "the null
    must run at the configured audit scale" condition for the number that
    *sets resolution*. ``audit_episodes`` defaults to
    ``CALIBRATION_AUDIT_EPISODES`` (well above the screen's own
    ``AUDIT_EPISODES``), because the number of calibration *points* is a
    separate knob from that budget (design section 11) and the screen's own
    ~24 points is too few to estimate a stable 95th-percentile tail. Smaller
    overrides exist only for tests exercising the wiring at trivial scale; a
    value intended for registration must use the defaults.
    """

    g17_runner.configure_runtime(int(SEEDS[source]["model"]))
    model = make_model(source)
    horizon, capacity, action_dim = _source_geometry(source)

    rows_by_episode: dict[int, list[ProbePointDelta]] = {}
    for episode_id in range(int(audit_episodes)):
        ledger = _make_ledger(source, episode_id)
        active_counts = _episode_active_counts(
            horizon=horizon,
            capacity=capacity,
            action_dim=action_dim,
            env_factory=_env_factory(source, ledger),
        )
        point_generator = np.random.default_rng(
            np.random.SeedSequence(
                [int(SEEDS[source]["audit"]), int(episode_id), 700]
            )
        )
        # `_audit_probe_points` always returns the module's full configured
        # list (length AUDIT_PROBE_POINTS_PER_EPISODE), restricted to the C1
        # action support; slicing to `points_per_episode` reuses that exact,
        # unmodified point-selection function -- including G18's forced t=0
        # pivotal point -- rather than reimplementing it, and only ever
        # narrows the set a real Stage A audit would also visit.
        points = _audit_probe_points(source, point_generator, active_counts)[
            : int(points_per_episode)
        ]
        rows: list[ProbePointDelta] = []
        for point_index, (intervention_time, intervention_position) in enumerate(
            points
        ):
            rows.append(
                _probe_point_delta(
                    model,
                    source,
                    ledger,
                    episode_id=episode_id,
                    point_index=point_index,
                    intervention_time=intervention_time,
                    intervention_position=intervention_position,
                    k=k,
                    suffix_replicates=suffix_replicates,
                )
            )
        rows_by_episode[episode_id] = rows

    statistic = _epsilon_audit_from_deltas(
        rows_by_episode, seed=int(SEEDS[source]["audit"]) + 900
    )
    return {
        "source": source,
        "audit_episodes": int(audit_episodes),
        "points_per_episode": int(points_per_episode),
        "suffix_replicates": int(suffix_replicates),
        "k": int(k),
        **statistic,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        choices=("g17", "g18", "both"),
        default="both",
    )
    return parser.parse_args()


def main() -> None:
    arguments = _parse_args()
    sources: Sequence[str] = ("g17", "g18") if arguments.source == "both" else (
        arguments.source,
    )
    results = {source: calibrate_source(source) for source in sources}
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
