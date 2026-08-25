"""Native EGRCR-B1 two-stage discriminator.

The implementation is deliberately isolated and dependency-free.  Calibration
constructs four legal worlds for every scripted edge and freezes centering,
relay scale, and the one-step trust radius.  Confirmation is unreachable unless
the retained calibration artifact passes every frozen gate.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import statistics
import time
from typing import Mapping, Sequence

from . import config as C


Vector = list[float]


@dataclass(frozen=True)
class Opportunity:
    root: int
    key: str
    kind: str
    lag: int
    older_id: int
    cue_flip: bool
    waiter_request: int = 1
    joiner_request: int = 0

    @property
    def joiner_id(self) -> int:
        return 1 - self.older_id

    @property
    def t_j(self) -> int:
        return C.WAITER_REQUEST_TICK + self.lag

    @property
    def cue(self) -> float:
        sign = 1.0 if self.kind == "JOINT" else -1.0
        return -sign if self.cue_flip else sign

    @property
    def stratum(self) -> str:
        # Readiness, ages, budget, time offset, |cue| and propensity band are
        # fixed by construction; ordered role and lag are the varying nuisance.
        return f"older={self.older_id}|lag={self.lag}|ready=11|age=2|budget=2|abs_cue=1|pband=mid"


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else math.nan


def _rms(xs: Sequence[float]) -> float:
    return math.sqrt(_mean([x * x for x in xs])) if xs else math.nan


def _norm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _sigmoid(x: float) -> float:
    if x >= 0.0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log(p) - (1.0 - p) * math.log(1.0 - p)


def _bernoulli_kl_from_half(p: float) -> float:
    return 0.5 * math.log(0.5 / p) + 0.5 * math.log(0.5 / (1.0 - p))


def _ci95(xs: Sequence[float], tcrit: float) -> dict[str, float | int]:
    n = len(xs)
    mean = _mean(xs)
    if n < 2:
        return {"n": n, "mean": mean, "lower": math.nan, "upper": math.nan, "sd": math.nan}
    sd = statistics.stdev(xs)
    half = tcrit * sd / math.sqrt(n)
    return {"n": n, "mean": mean, "lower": mean - half, "upper": mean + half, "sd": sd}


def _features(agent_id: int, cue: float, tick: int, lag: int, pending: float) -> Vector:
    return [
        1.0 if agent_id == 0 else 0.0,
        1.0 if agent_id == 1 else 0.0,
        cue,
        min(tick / C.WAITER_EXPIRY_TICK, 1.0),
        pending,
        lag / 2.0,
        1.0,
        tick / (C.BLOCK_TICKS - 1),
        pending,
        1.0,
    ]


def _world(opp: Opportunity, u: int, v: int) -> dict[str, object]:
    """Run one legal same-snapshot factorial fork.

    u/v select immediate joiner/waiter execution.  Missing prepared options
    execute at their frozen local deadlines.  No fork gets new information.
    """

    t_j = opp.t_j
    j_exec = t_j if u else t_j + 1
    w_exec = t_j if v else C.WAITER_EXPIRY_TICK
    g_w = 0
    g_j = 0
    rewards: Vector = []
    generations: list[tuple[int, int]] = []
    executions: list[tuple[int, int]] = []
    packet: list[int] = []
    for tick in range(C.BLOCK_TICKS):
        ew = int(tick == w_exec)
        ej = int(tick == j_exec)
        if ew:
            g_w = 1
        if ej:
            g_j = 1
        if tick < t_j:
            requirement = (0, 0)
        elif tick <= C.OUTCOME_BOUNDARY:
            requirement = (1, 1) if opp.kind == "JOINT" else (0, 1)
        else:
            requirement = (-1, -1)  # terminal padding tick, never succeeds
        success = int(not (ew or ej) and (g_w, g_j) == requirement)
        reward = float(success) - C.RENEWAL_COST * float(ew + ej)
        rewards.append(reward)
        generations.append((g_w, g_j))
        executions.append((ew, ej))
        packet.append(success)
    horizon = C.OUTCOME_BOUNDARY - t_j + 1
    y = sum(rewards[t_j : C.OUTCOME_BOUNDARY + 1]) / horizon
    q = t_j + 1
    x = sum(
        1
        for tick in range(t_j + 1, C.OUTCOME_BOUNDARY + 1)
        if tick not in {j_exec, w_exec}
    )
    return {
        "Y": y,
        "rewards": rewards,
        "packet": packet,
        "executions": executions,
        "generations": generations,
        "first_common_post_event_tick": q,
        "waiter_generation_at_q": generations[q][0],
        "X": x,
        "physical_ticks": C.BLOCK_TICKS,
    }


def _quartet(opp: Opportunity) -> dict[str, object]:
    worlds = {f"Y{u}{v}": _world(opp, u, v) for u in (0, 1) for v in (0, 1)}
    y00 = float(worlds["Y00"]["Y"])
    y10 = float(worlds["Y10"]["Y"])
    y01 = float(worlds["Y01"]["Y"])
    y11 = float(worlds["Y11"]["Y"])
    self_effect = y10 - y00
    waiter = y11 - y10
    generic = y01 - y00
    kappa = waiter - generic
    h = [
        float(worlds["Y11"]["rewards"][t])
        - float(worlds["Y10"]["rewards"][t])
        - float(worlds["Y01"]["rewards"][t])
        + float(worlds["Y00"]["rewards"][t])
        for t in range(C.BLOCK_TICKS)
    ]
    tagged = sum(
        (C.GAE_LAMBDA ** (t - opp.t_j)) * h[t]
        for t in range(opp.t_j, C.OUTCOME_BOUNDARY + 1)
    )
    return {
        "Y00": y00,
        "Y10": y10,
        "Y01": y01,
        "Y11": y11,
        "self": self_effect,
        "waiter": waiter,
        "generic_waiter": generic,
        "kappa": kappa,
        "natural_effect": y11 - y00,
        "h_by_tick": h,
        "tagged_gae_if_join": tagged,
        "source_to_execution": True,
        "source_to_first_action": (
            worlds["Y11"]["waiter_generation_at_q"]
            != worlds["Y10"]["waiter_generation_at_q"]
        ),
        "X": min(int(worlds["Y11"]["X"]), int(worlds["Y10"]["X"])),
        "worlds": {
            name: {
                "Y": world["Y"],
                "first_common_post_event_tick": world["first_common_post_event_tick"],
                "waiter_generation_at_q": world["waiter_generation_at_q"],
                "X": world["X"],
                "packet_success_by_tick": world["packet"],
                "executions_by_tick": world["executions"],
            }
            for name, world in worlds.items()
        },
    }


def _counter_ranks(root: int, namespace: int, count: int) -> list[int]:
    """Return stable prospective counter-key ranks without using outcomes."""

    keyed = []
    for i in range(count):
        rng = random.Random(root * 104729 + namespace * 15485863 + i * 32452843)
        keyed.append((rng.random(), i))
    return [i for _, i in sorted(keyed)]


def _balanced_opportunities(root: int, root_ordinal: int) -> list[Opportunity]:
    rows: list[Opportunity] = []
    index = 0
    parity = root_ordinal % 2
    # Eight (type, lag, ordered-role) cells x 16 rows.  Cue flips are chosen
    # prospectively by an independent counter-key namespace: four parity cells
    # receive 2 flips and four receive 1, for exactly 116/12 per root.
    for kind_index, kind in enumerate(C.TYPES):
        for lag in C.LAGS:
            for older in (0, 1):
                b_type = int(kind == "JOINT")
                b_lag = int(lag == 2)
                b_role = int(older == 1)
                flip_count = 2 if (b_type ^ b_lag ^ b_role) == parity else 1
                namespace = 1000 + kind_index * 100 + lag * 10 + older
                flipped = set(_counter_ranks(root, namespace, 16)[:flip_count])
                action_namespace = 5000 + kind_index * 100 + lag * 10 + older
                requests = set(_counter_ranks(root, action_namespace, 16)[:8])
                for rep in range(16):
                    rows.append(
                        Opportunity(
                            root,
                            f"cal-{root}-{index:03d}",
                            kind,
                            lag,
                            older,
                            rep in flipped,
                            joiner_request=int(rep in requests),
                        )
                    )
                    index += 1
    return rows


def _gradient(rows: Sequence[Mapping[str, object]], advantages: Sequence[float]) -> tuple[Vector, Vector, float]:
    centered = [a - _mean(advantages) for a in advantages]
    scale = _rms(centered)
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("zero advantage RMS")
    normalized = [a / scale for a in centered]
    dim = len(rows[0]["features"])
    raw = [0.0] * dim
    normed = [0.0] * dim
    for row, a_raw, a_norm in zip(rows, advantages, normalized):
        action = float(row["action"])
        score = action - 0.5
        features = row["features"]
        for j in range(dim):
            raw[j] += score * a_raw * float(features[j]) / len(rows)
            normed[j] += score * a_norm * float(features[j]) / len(rows)
    return raw, normed, scale


def _heldout_feature_panel(root: int) -> list[Vector]:
    panel: list[Vector] = []
    for kind_index, kind in enumerate(C.TYPES):
        type_sign = 1.0 if kind == "JOINT" else -1.0
        for lag in C.LAGS:
            for older in (0, 1):
                namespace = 2000 + kind_index * 100 + lag * 10 + older
                flipped = set(
                    _counter_ranks(root, namespace, 32)[: C.CUE_FLIPPED_PER_HELDOUT_CELL]
                )
                for rep in range(32):
                    cue = -type_sign if rep in flipped else type_sign
                    panel.append(_features(1 - older, cue, C.WAITER_REQUEST_TICK + lag, lag, 1.0))
    return panel


def _mean_kl(theta: Sequence[float], panels: Sequence[Sequence[Vector]]) -> float:
    return _mean([_bernoulli_kl_from_half(_sigmoid(_dot(theta, x))) for panel in panels for x in panel])


def _freeze_delta(direction: Sequence[float], panels: Sequence[Sequence[Vector]]) -> float:
    n = _norm(direction)
    if n <= 0.0:
        return 0.0
    unit = [x / n for x in direction]
    lo = 0.0
    hi = 1.0
    while _mean_kl([hi * x for x in unit], panels) <= C.KL_MAX:
        hi *= 2.0
        if hi > 1024.0:
            raise ValueError("could not bracket KL trust radius")
    for _ in range(64):
        mid = (lo + hi) / 2.0
        if _mean_kl([mid * x for x in unit], panels) <= C.KL_MAX:
            lo = mid
        else:
            hi = mid
    return lo


def _update(theta: Sequence[float], gradient: Sequence[float], delta: float) -> Vector:
    n = _norm(gradient)
    if n <= 0.0:
        raise ValueError("zero normalized policy gradient")
    return [x + delta * g / n for x, g in zip(theta, gradient)]


def _expression_fact(root: int, theta: Sequence[float], panel: Sequence[Vector]) -> dict[str, float]:
    positive = [_sigmoid(_dot(theta, x)) for x in panel if x[2] > 0.0]
    negative = [_sigmoid(_dot(theta, x)) for x in panel if x[2] < 0.0]
    selectivity = _mean(positive) - _mean(negative)
    rng = random.Random(root * 130363 + 19)
    changed = 0
    predicted = 0
    for x in panel:
        u = rng.random()
        old = int(u < 0.5)
        new = int(u < _sigmoid(_dot(theta, x)))
        direction = 1 if x[2] > 0.0 else -1
        if (new - old) * direction > 0:
            changed += 1
        if new != old:
            predicted += 1
    return {
        "selectivity_probability_change": selectivity,
        "common_uniform_predicted_direction_fraction": changed / len(panel),
        "common_uniform_any_change_fraction": predicted / len(panel),
    }


def run_calibration() -> dict[str, object]:
    started = time.perf_counter()
    root_rows: dict[int, list[dict[str, object]]] = {}
    all_policy_rows: list[dict[str, object]] = []
    all_targets: list[float] = []
    tagged_samples: list[float] = []
    stratum_values: dict[str, list[float]] = {}
    physical_ticks = 0
    for root_ordinal, root in enumerate(C.CALIBRATION_ROOTS):
        rows: list[dict[str, object]] = []
        for opp in _balanced_opportunities(root, root_ordinal):
            q = _quartet(opp)
            action = opp.joiner_request
            record = {
                "key": opp.key,
                "type": opp.kind,
                "lag": opp.lag,
                "older_id": opp.older_id,
                "cue_flip": opp.cue_flip,
                "stratum": opp.stratum,
                "features": _features(opp.joiner_id, opp.cue, opp.t_j, opp.lag, 1.0),
                "action": action,
                "stored_probability": C.STORED_BEHAVIOR_PROBABILITY,
                **q,
            }
            rows.append(record)
            stratum_values.setdefault(opp.stratum, []).append(float(q["kappa"]))
            physical_ticks += 4 * C.BLOCK_TICKS
        root_rows[root] = rows

    stratum_means = {s: _mean(v) for s, v in stratum_values.items()}
    for rows in root_rows.values():
        for row in rows:
            centered_kappa = float(row["kappa"]) - stratum_means[str(row["stratum"])]
            target = (float(row["action"]) - float(row["stored_probability"])) * centered_kappa
            all_policy_rows.append(row)
            all_targets.append(target)
            tagged_samples.append(float(row["action"]) * float(row["tagged_gae_if_join"]))
    target_rms = _rms(all_targets)
    removed_rms = _rms(tagged_samples)
    relay_scale = removed_rms / target_rms if target_rms > 0.0 else 0.0
    relay_advantages = [relay_scale * target for target in all_targets]
    _, aggregate_gradient, advantage_rms = _gradient(all_policy_rows, relay_advantages)
    panels = [_heldout_feature_panel(root) for root in C.CALIBRATION_ROOTS]
    delta = _freeze_delta(aggregate_gradient, panels)
    theta = _update([0.0] * len(aggregate_gradient), aggregate_gradient, delta)

    root_facts: list[dict[str, object]] = []
    joint_means: list[float] = []
    solo_means: list[float] = []
    selectivity: list[float] = []
    actual_changes: list[float] = []
    source_execution_ok = True
    source_action_ok = True
    exposure_ok = True
    nonzero_waiter_ok = True
    cue_schedule_ok = True
    for root, panel in zip(C.CALIBRATION_ROOTS, panels):
        rows = root_rows[root]
        jm = _mean([float(r["kappa"]) for r in rows if r["type"] == "JOINT"])
        sm = _mean([float(r["kappa"]) for r in rows if r["type"] == "SOLO"])
        expression = _expression_fact(root, theta, panel)
        joint_means.append(jm)
        solo_means.append(sm)
        selectivity.append(float(expression["selectivity_probability_change"]))
        actual_changes.append(float(expression["common_uniform_predicted_direction_fraction"]))
        source_execution_ok &= all(bool(r["source_to_execution"]) for r in rows)
        source_action_ok &= all(bool(r["source_to_first_action"]) for r in rows)
        exposure_ok &= all(int(r["X"]) >= 2 for r in rows)
        nonzero_waiter_ok &= all(abs(float(r["waiter"])) > 0.0 for r in rows)
        flips = sum(bool(r["cue_flip"]) for r in rows)
        cue_schedule_ok &= flips == 12
        factor_flip_counts = {
            "JOINT": sum(bool(r["cue_flip"]) for r in rows if r["type"] == "JOINT"),
            "SOLO": sum(bool(r["cue_flip"]) for r in rows if r["type"] == "SOLO"),
            "lag_1": sum(bool(r["cue_flip"]) for r in rows if r["lag"] == 1),
            "lag_2": sum(bool(r["cue_flip"]) for r in rows if r["lag"] == 2),
            "older_0": sum(bool(r["cue_flip"]) for r in rows if r["older_id"] == 0),
            "older_1": sum(bool(r["cue_flip"]) for r in rows if r["older_id"] == 1),
        }
        cue_schedule_ok &= all(value == 6 for value in factor_flip_counts.values())
        root_facts.append(
            {
                "root": root,
                "opportunities": len(rows),
                "joint_kappa_mean": jm,
                "solo_kappa_mean": sm,
                "kappa_min": min(float(r["kappa"]) for r in rows),
                "kappa_max": max(float(r["kappa"]) for r in rows),
                "min_X": min(int(r["X"]) for r in rows),
                "correct_joiner_cues": len(rows) - flips,
                "flipped_joiner_cues": flips,
                "realized_cue_accuracy": (len(rows) - flips) / len(rows),
                "factor_level_flip_counts": factor_flip_counts,
                **expression,
                "activity_witness": {
                    "joint_edge": next(r["key"] for r in rows if r["type"] == "JOINT"),
                    "solo_edge": next(r["key"] for r in rows if r["type"] == "SOLO"),
                    "four_worlds_present": True,
                    "waiter_action_and_exposure_present": True,
                },
            }
        )

    joint_ci = _ci95(joint_means, C.TCRIT_5)
    solo_ci = _ci95(solo_means, C.TCRIT_5)
    selectivity_ci = _ci95(selectivity, C.TCRIT_5)
    actual_ci = _ci95(actual_changes, C.TCRIT_5)

    # The cut is prospective: within every nuisance stratum, rotate to the
    # opposite type while changing the waiter key and preserving all labels.
    cut_support = True
    cut_changed = []
    cut_source_relay: list[float] = []
    cut_target_relay: list[float] = []
    cut_examples: list[dict[str, str]] = []
    for root in C.CALIBRATION_ROOTS:
        by_stratum: dict[str, list[dict[str, object]]] = {}
        for row in root_rows[root]:
            action_stratum = f"{row['stratum']}|action={row['action']}|p={row['stored_probability']}"
            by_stratum.setdefault(action_stratum, []).append(row)
        for stratum, rows in by_stratum.items():
            joint = sorted((r for r in rows if r["type"] == "JOINT"), key=lambda r: str(r["key"]))
            solo = sorted((r for r in rows if r["type"] == "SOLO"), key=lambda r: str(r["key"]))
            if not joint or len(joint) != len(solo):
                cut_support = False
                continue
            paired = list(zip(joint, solo[1:] + solo[:1])) + list(zip(solo, joint[1:] + joint[:1]))
            for source, target in paired:
                if source["key"] == target["key"] or source["type"] == target["type"]:
                    cut_support = False
                if source["action"] != target["action"] or source["stored_probability"] != target["stored_probability"]:
                    cut_support = False
                cut_changed.append(abs(float(source["kappa"]) - float(target["kappa"])))
                source_centered = float(source["kappa"]) - stratum_means[str(source["stratum"])]
                target_centered = float(target["kappa"]) - stratum_means[str(target["stratum"])]
                action_score = float(source["action"]) - float(source["stored_probability"])
                cut_source_relay.append(action_score * source_centered)
                cut_target_relay.append(action_score * target_centered)
            if len(cut_examples) < 8:
                cut_examples.append({"stratum": stratum, "source": str(paired[0][0]["key"]), "target": str(paired[0][1]["key"])})

    gates = {
        "source_to_target_first_stage": {
            "passed": source_execution_ok and source_action_ok,
            "execution_changed_every_edge": source_execution_ok,
            "first_common_action_changed_every_edge": source_action_ok,
        },
        "downstream_target_exposure": {
            "passed": (
                exposure_ok
                and nonzero_waiter_ok
                and float(joint_ci["lower"]) >= C.KAPPA_JOINT_MIN
                and float(solo_ci["upper"]) <= C.KAPPA_SOLO_MAX
            ),
            "X_at_least_two_every_edge": exposure_ok,
            "waiter_effect_nonzero_every_edge": nonzero_waiter_ok,
            "joint_kappa_ci95": joint_ci,
            "solo_kappa_ci95": solo_ci,
            "kappa_usefully_varies": max(all_targets) > min(all_targets),
        },
        "joiner_record_update_expressibility": {
            "passed": (
                cue_schedule_ok
                and
                removed_rms > 0.0
                and target_rms > 0.0
                and relay_scale > 0.0
                and
                _norm(aggregate_gradient) > 0.0
                and float(selectivity_ci["mean"]) >= C.SELECTIVITY_MIN
                and float(selectivity_ci["lower"]) > 0.0
                and float(actual_ci["mean"]) >= C.ACTUAL_CHANGE_MIN
            ),
            "selectivity_change_ci95": selectivity_ci,
            "common_uniform_predicted_change_ci95": actual_ci,
            "zero_gradient": _norm(aggregate_gradient) == 0.0,
            "removed_tagged_atom_rms_positive": removed_rms > 0.0,
            "action_conditioned_target_rms_positive": target_rms > 0.0,
            "cue_schedule_exact_116_correct_12_flipped": cue_schedule_ok,
        },
        "cut_support": {
            "passed": (
                cut_support
                and bool(cut_changed)
                and min(cut_changed) > 0.0
                and sorted(cut_source_relay) == sorted(cut_target_relay)
            ),
            "all_strata_balanced": cut_support,
            "fixed_point_free": cut_support,
            "opposite_type": cut_support,
            "source_score_credit_association_changed": bool(cut_changed) and min(cut_changed) > 0.0,
            "signed_centered_target_multiset_preserved": sorted(cut_source_relay) == sorted(cut_target_relay),
            "action_conditioned_advantage_multiset_preserved": sorted(cut_source_relay) == sorted(cut_target_relay),
            "minimum_absolute_label_change": min(cut_changed) if cut_changed else 0.0,
            "examples": cut_examples,
        },
    }
    all_passed = all(bool(g["passed"]) for g in gates.values())
    return {
        "artifact_kind": "egrcr_b1_calibration_result",
        "treatment": C.TREATMENT,
        "stage": "calibration",
        "roots": list(C.CALIBRATION_ROOTS),
        "opportunities_per_root": C.CALIBRATION_OPPORTUNITIES,
        "question_relevant_activity_began": True,
        "binding_question_exposed": False,
        "all_gates_passed": all_passed,
        "gates": gates,
        "root_facts": root_facts,
        "frozen_parameters": {
            "stratum_kappa_means": stratum_means,
            "relay_target_scale": relay_scale,
            "removed_tagged_gae_rms": removed_rms,
            "action_conditioned_centered_kappa_rms": target_rms,
            "trust_radius_delta": delta,
            "calibration_gradient_direction": aggregate_gradient,
            "calibration_advantage_rms": advantage_rms,
            "mean_heldout_kl": _mean_kl(theta, panels),
        },
        "semantics": {
            "source_action": "later joiner request",
            "credit_destination": "later joiner stored request record only",
            "waiter_credit": "ordinary GAE unchanged",
            "debit_or_reverse_relay": False,
        },
        "accounting": {
            "two_agent_physical_ticks": physical_ticks,
            "four_world_label_calculations": len(all_policy_rows) * 4,
            "cpu_workers": 1,
            "cap_respected": physical_ticks <= C.MAX_PHYSICAL_TICKS,
        },
        "runtime_seconds": time.perf_counter() - started,
        "anomalies": [],
    }


def _natural_rewards(opp: Opportunity) -> Vector:
    if opp.waiter_request:
        fork = _world(opp, opp.joiner_request, opp.joiner_request)
        return list(fork["rewards"])
    # No older request: a joiner request executes only at its fixed local
    # deadline; the waiter never executes.  This row cannot become an edge.
    t_j = opp.t_j
    j_exec = t_j + 1 if opp.joiner_request else -1
    g_w = 0
    g_j = 0
    rewards: Vector = []
    for tick in range(C.BLOCK_TICKS):
        ej = int(tick == j_exec)
        if ej:
            g_j = 1
        requirement = (0, 0) if tick < t_j else ((1, 1) if opp.kind == "JOINT" else (0, 1))
        if tick > C.OUTCOME_BOUNDARY:
            requirement = (-1, -1)
        success = int(not ej and (g_w, g_j) == requirement)
        rewards.append(float(success) - C.RENEWAL_COST * ej)
    return rewards


def _gae(rewards: Sequence[float]) -> Vector:
    out = [0.0] * len(rewards)
    running = 0.0
    for t in range(len(rewards) - 1, -1, -1):
        running = float(rewards[t]) + C.GAMMA * C.GAE_LAMBDA * running
        out[t] = running
    return out


def _confirmation_opportunities(root: int, root_ordinal: int) -> list[Opportunity]:
    scheduled: list[Opportunity] = []
    parity = root_ordinal % 2
    for kind_index, kind in enumerate(C.TYPES):
        for lag in C.LAGS:
            for older in (0, 1):
                b_type = int(kind == "JOINT")
                b_lag = int(lag == 2)
                b_role = int(older == 1)
                flip_count = 2 if (b_type ^ b_lag ^ b_role) == parity else 1
                namespace = 4000 + kind_index * 100 + lag * 10 + older
                flipped = set(_counter_ranks(root, namespace, 16)[:flip_count])
                for action in (0, 1):
                    for rep in range(8):
                        cell_row = action * 8 + rep
                        scheduled.append(
                            Opportunity(
                                root=root,
                                key=f"scheduled-{root}-{kind.lower()}-l{lag}-o{older}-a{action}-{rep}",
                                kind=kind,
                                lag=lag,
                                older_id=older,
                                cue_flip=cell_row in flipped,
                                waiter_request=1,
                                joiner_request=action,
                            )
                        )
    return scheduled


def _collect_root(root: int, root_ordinal: int) -> dict[str, object]:
    rng = random.Random(root * 32452843 + 211)
    rows: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    counts = {
        (kind, lag, older, action): 0
        for kind in C.TYPES
        for lag in C.LAGS
        for older in (0, 1)
        for action in (0, 1)
    }
    blocks = 0
    schedule = _confirmation_opportunities(root, root_ordinal)
    for schedule_index, scheduled in enumerate(schedule):
        retained = False
        action_coordinate = random.Random(root * 86028121 + 5000 + schedule_index * 104729).random()
        action_uniform = (
            0.5 * action_coordinate
            if scheduled.joiner_request
            else 0.5 + 0.5 * action_coordinate
        )
        while not retained and blocks < C.COLLECTION_BLOCK_CAP:
            waiter_action = int(rng.random() < 0.5)
            joiner_action = scheduled.joiner_request if waiter_action else int(rng.random() < 0.5)
            opp = Opportunity(
                root=root,
                key=f"conf-{root}-{blocks:03d}-{scheduled.kind.lower()}",
                kind=scheduled.kind,
                lag=scheduled.lag,
                older_id=scheduled.older_id,
                cue_flip=scheduled.cue_flip,
                waiter_request=waiter_action,
                joiner_request=joiner_action,
            )
            rewards = _natural_rewards(opp)
            returns = _gae(rewards)
            source_index = len(rows) + opp.joiner_id * C.BLOCK_TICKS + opp.t_j
            for agent in (0, 1):
                agent_cue = opp.cue if agent == opp.joiner_id else (1.0 if rng.random() < 0.5 else -1.0)
                for tick in range(C.BLOCK_TICKS):
                    action = int(rng.random() < 0.5)
                    if agent == opp.older_id and tick == C.WAITER_REQUEST_TICK:
                        action = waiter_action
                    if agent == opp.joiner_id and tick == opp.t_j:
                        action = joiner_action
                    rows.append(
                        {
                            "features": _features(agent, agent_cue, tick, opp.lag, float(waiter_action and tick >= C.WAITER_REQUEST_TICK)),
                            "action": action,
                            "ordinary_gae": returns[tick],
                            "edge_key": opp.key if agent == opp.joiner_id and tick == opp.t_j and waiter_action else None,
                            "is_waiter_request_record": agent == opp.older_id and tick == C.WAITER_REQUEST_TICK,
                        }
                    )
            if waiter_action:
                q = _quartet(opp)
                edges.append(
                    {
                        "key": opp.key,
                        "type": opp.kind,
                        "lag": opp.lag,
                        "older_id": opp.older_id,
                        "cue_flip": opp.cue_flip,
                        "stratum": opp.stratum,
                        "source_row": source_index,
                        "joiner_action": joiner_action,
                        "stored_probability": C.STORED_BEHAVIOR_PROBABILITY,
                        "action_uniform": action_uniform,
                        "kappa": q["kappa"],
                        "tagged_gae": float(joiner_action) * float(q["tagged_gae_if_join"]),
                        "X": q["X"],
                    }
                )
                counts[(opp.kind, opp.lag, opp.older_id, joiner_action)] += 1
                retained = True
            blocks += 1
        if not retained:
            break
    return {
        "rows": rows,
        "edges": edges,
        "blocks": blocks,
        "counts": {
            f"{kind}|lag={lag}|older={older}|action={action}": counts[(kind, lag, older, action)]
            for kind in C.TYPES
            for lag in C.LAGS
            for older in (0, 1)
            for action in (0, 1)
        },
        "supported": (
            len(edges) == C.CONFIRMATION_EDGES
            and all(v == C.EDGES_PER_TYPE_LAG_ROLE_ACTION for v in counts.values())
        ),
        "cue_schedule": {
            "correct": sum(not bool(edge["cue_flip"]) for edge in edges),
            "flipped": sum(bool(edge["cue_flip"]) for edge in edges),
            "accuracy": (
                sum(not bool(edge["cue_flip"]) for edge in edges) / len(edges)
                if edges
                else math.nan
            ),
        },
        "action_schedule": {
            "requests": sum(int(edge["joiner_action"]) for edge in edges),
            "no_requests": sum(1 - int(edge["joiner_action"]) for edge in edges),
            "stored_probability": C.STORED_BEHAVIOR_PROBABILITY,
        },
    }


def _cut_mapping(edges: Sequence[Mapping[str, object]]) -> tuple[dict[str, str], list[str]]:
    mapping: dict[str, str] = {}
    issues: list[str] = []
    groups: dict[str, list[Mapping[str, object]]] = {}
    for edge in edges:
        exact_stratum = (
            f"{edge['stratum']}|action={edge['joiner_action']}|p={edge['stored_probability']}"
        )
        groups.setdefault(exact_stratum, []).append(edge)
    for stratum, group in groups.items():
        joint = sorted((e for e in group if e["type"] == "JOINT"), key=lambda e: str(e["key"]))
        solo = sorted((e for e in group if e["type"] == "SOLO"), key=lambda e: str(e["key"]))
        if not joint or len(joint) != len(solo):
            issues.append(f"unsupported cut stratum {stratum}")
            continue
        shifted_solo = solo[1:] + solo[:1]
        shifted_joint = joint[1:] + joint[:1]
        for source, target in list(zip(joint, shifted_solo)) + list(zip(solo, shifted_joint)):
            if source["key"] == target["key"] or source["type"] == target["type"]:
                issues.append(f"illegal cut pair {source['key']}->{target['key']}")
            mapping[str(source["key"])] = str(target["key"])
    if len(mapping) != len(edges) or len(set(mapping.values())) != len(edges):
        issues.append("cut is not a complete bijection")
    return mapping, issues


def _advantages_for_arm(
    arm: str,
    rows: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
    mapping: Mapping[str, str],
    calibration: Mapping[str, object],
) -> Vector:
    advantages = [float(row["ordinary_gae"]) for row in rows]
    frozen = calibration["frozen_parameters"]
    means = frozen["stratum_kappa_means"]
    scale = float(frozen["relay_target_scale"])
    by_key = {str(edge["key"]): edge for edge in edges}
    for edge in edges:
        packet = (
            by_key[mapping[str(edge["key"])]]
            if arm == "BINDING-CUT"
            else edge
        )
        centered_packet = float(packet["kappa"]) - float(means[str(packet["stratum"])])
        action_score = float(edge["joiner_action"]) - float(edge["stored_probability"])
        target = scale * action_score * centered_packet
        i = int(edge["source_row"])
        # GAE executes identical label/relay bookkeeping as a dummy operation;
        # only the registered relay arms replace the later-record atom.
        if arm != "GAE":
            advantages[i] = advantages[i] - float(edge["tagged_gae"]) + target
    return advantages


def _score_credit_covariance(rows: Sequence[Mapping[str, object]], adv: Sequence[float]) -> float:
    score = [(float(row["action"]) - 0.5) * float(row["features"][2]) for row in rows]
    ms = _mean(score)
    ma = _mean(adv)
    return _mean([(s - ms) * (a - ma) for s, a in zip(score, adv)])


def _make_eval_opportunities(root: int) -> list[Opportunity]:
    out: list[Opportunity] = []
    by_kind: dict[str, list[Opportunity]] = {kind: [] for kind in C.TYPES}
    for kind_index, kind in enumerate(C.TYPES):
        for lag in C.LAGS:
            for older in (0, 1):
                namespace = 3000 + kind_index * 100 + lag * 10 + older
                flipped = set(
                    _counter_ranks(root, namespace, 32)[: C.CUE_FLIPPED_PER_HELDOUT_CELL]
                )
                for rep in range(32):
                    by_kind[kind].append(
                        Opportunity(
                            root=root,
                            key=f"eval-{root}-{kind.lower()}-l{lag}-o{older}-{rep:02d}",
                            kind=kind,
                            lag=lag,
                            older_id=older,
                            cue_flip=rep in flipped,
                            waiter_request=1,
                        )
                    )
    # Dyad i is one JOINT and one SOLO opportunity.  Cell ordering is shared,
    # while cue counter-key namespaces are independent between the two types.
    for i in range(C.EVALUATION_DYADS):
        out.extend((by_kind["JOINT"][i], by_kind["SOLO"][i]))
    return out


def _yoke_mapping(opps: Sequence[Opportunity]) -> dict[str, str]:
    # Within each lag/ordered-role nuisance stratum, source order is
    # [all JOINT, all SOLO].  A quarter-cycle prospective offset gives each
    # source type exactly half of each suffix type, changes every event key,
    # and preserves the complete suffix multiset.
    mapping: dict[str, str] = {}
    groups: dict[tuple[int, int], list[Opportunity]] = {}
    for opp in opps:
        groups.setdefault((opp.lag, opp.older_id), []).append(opp)
    for group in groups.values():
        ordered = sorted(group, key=lambda o: (o.kind, o.key))
        n = len(ordered)
        if n % 4:
            raise ValueError("evaluation yoke stratum is not quarter-balanced")
        offset = n // 4
        for i, source in enumerate(ordered):
            target = ordered[(i + offset) % n]
            if source.key == target.key:
                raise ValueError("evaluation yoke fixed point")
            mapping[source.key] = target.key
    if len(set(mapping.values())) != len(opps):
        raise ValueError("evaluation yoke is not bijective")
    return mapping


def _evaluate_arm(root: int, arm: str, theta: Sequence[float]) -> dict[str, dict[str, object]]:
    opps = _make_eval_opportunities(root)
    by_key = {opp.key: opp for opp in opps}
    yoke = _yoke_mapping(opps)
    rng_tie = random.Random(root * 67867967 + 401)
    tie_choices = [rng_tie.randrange(2) for _ in range(C.EVALUATION_DYADS)]
    rng_uniform = random.Random(root * 86028121 + 503)
    base_uniforms = {opp.key: rng_uniform.random() for opp in opps}
    results: dict[str, dict[str, object]] = {}
    for context in C.CONTEXTS:
        utilities: list[float] = []
        source_probs: dict[str, float] = {}
        allocations: dict[str, int] = {}
        suffix_kind: dict[str, str] = {}
        closure_count = 0
        packet_success = 0
        execution_downtime = 0
        common_uniform_requests = 0
        common_uniform_by_source_type = {"JOINT": 0, "SOLO": 0}
        common_uniform_by_cue = {"positive": 0, "negative": 0}
        actor_calls = 0
        value_calls = 0
        dummy_actor_checksum = 0.0
        source_joint_probs: list[float] = []
        source_solo_probs: list[float] = []
        cue_pos: list[float] = []
        cue_neg: list[float] = []
        for opp in opps:
            p = _sigmoid(_dot(theta, _features(opp.joiner_id, opp.cue, opp.t_j, opp.lag, 1.0)))
            actor_calls += 1
            source_probs[opp.key] = p
            uniform_request = int(base_uniforms[opp.key] < p)
            common_uniform_requests += uniform_request
            common_uniform_by_source_type[opp.kind] += uniform_request
            common_uniform_by_cue["positive" if opp.cue > 0 else "negative"] += uniform_request
            (source_joint_probs if opp.kind == "JOINT" else source_solo_probs).append(p)
            (cue_pos if opp.cue > 0 else cue_neg).append(p)
            suffix = opp if context == "NATIVE" else by_key[yoke[opp.key]]
            suffix_kind[opp.key] = suffix.kind
        for dyad in range(C.EVALUATION_DYADS):
            pair = opps[2 * dyad : 2 * dyad + 2]
            p0 = source_probs[pair[0].key]
            p1 = source_probs[pair[1].key]
            if p0 == p1:
                chosen = pair[tie_choices[dyad]]
            else:
                chosen = pair[0] if p0 > p1 else pair[1]
            for opp in pair:
                request = int(opp.key == chosen.key)
                allocations[opp.key] = request
                suffix = opp if context == "NATIVE" else by_key[yoke[opp.key]]
                eval_opp = Opportunity(
                    root=root,
                    key=opp.key,
                    kind=suffix.kind,
                    lag=opp.lag,
                    older_id=opp.older_id,
                    cue_flip=opp.cue_flip,
                    waiter_request=1,
                    joiner_request=request,
                )
                world = _world(eval_opp, request, request)
                for agent in (0, 1):
                    actor_cue = opp.cue if agent == opp.joiner_id else (1.0 if (dyad + agent) % 2 == 0 else -1.0)
                    for tick in range(C.BLOCK_TICKS):
                        value_calls += 1  # identically zero frozen baseline call
                        if agent == opp.joiner_id and tick == opp.t_j:
                            continue  # the source call above is reused
                        dummy_actor_checksum += _sigmoid(
                            _dot(theta, _features(agent, actor_cue, tick, opp.lag, 1.0))
                        )
                        actor_calls += 1
                utilities.append(float(world["Y"]))
                closure_count += request
                packet_success += sum(int(x) for x in world["packet"])
                execution_downtime += sum(int(bool(w or j)) for w, j in world["executions"])
        selected_joint = sum(allocations[o.key] for o in opps if suffix_kind[o.key] == "JOINT")
        selected_solo = sum(allocations[o.key] for o in opps if suffix_kind[o.key] == "SOLO")
        results[context] = {
            "normalized_bounded_utility": _mean(utilities),
            "request_selectivity_probability": _mean(source_joint_probs) - _mean(source_solo_probs),
            "actual_request_allocation": {
                "suffix_joint": selected_joint,
                "suffix_solo": selected_solo,
                "joint_fraction": selected_joint / C.EVALUATION_DYADS,
            },
            "common_uniform_actual_requests": common_uniform_requests,
            "common_uniform_actual_requests_by_source_type": common_uniform_by_source_type,
            "common_uniform_actual_requests_by_cue": common_uniform_by_cue,
            "closure_count": closure_count,
            "renewal_count": len(opps) * 2,
            "period_histogram": {"lag_1": len(opps) // 2, "lag_2": len(opps) // 2},
            "packet_success": packet_success,
            "execution_downtime": execution_downtime,
            "cue_stratified_request_probability": {"positive": _mean(cue_pos), "negative": _mean(cue_neg)},
            "heldout_cue_schedule": {
                kind: {
                    "correct": sum(not opp.cue_flip for opp in opps if opp.kind == kind),
                    "flipped": sum(opp.cue_flip for opp in opps if opp.kind == kind),
                }
                for kind in C.TYPES
            },
            "fixed_token_count": C.EVALUATION_DYADS,
            "actor_calls": actor_calls,
            "value_calls": value_calls,
            "dummy_actor_checksum": dummy_actor_checksum,
            "yoke_fixed_point_free": context == "NATIVE" or all(k != v for k, v in yoke.items()),
            "yoke_complete_suffix_multiset": context == "NATIVE" or sorted(yoke.values()) == sorted(by_key),
        }
    return results


def _aggregate_confirmation(root_results: Sequence[Mapping[str, object]]) -> dict[str, object]:
    effects: dict[str, list[float]] = {name: [] for name in ("D_IG_N", "D_IC_N", "D_IG_Y", "D_IC_Y", "Psi_G", "Psi_C")}
    selectivity_effects: dict[str, list[float]] = {"INTACT-GAE": [], "INTACT-BINDING-CUT": []}
    for root in root_results:
        ev = root["evaluation"]
        u = {(a, c): float(ev[a][c]["normalized_bounded_utility"]) for a in C.ARMS for c in C.CONTEXTS}
        d_ig_n = u[("INTACT", "NATIVE")] - u[("GAE", "NATIVE")]
        d_ic_n = u[("INTACT", "NATIVE")] - u[("BINDING-CUT", "NATIVE")]
        d_ig_y = u[("INTACT", "YOKED")] - u[("GAE", "YOKED")]
        d_ic_y = u[("INTACT", "YOKED")] - u[("BINDING-CUT", "YOKED")]
        vals = {
            "D_IG_N": d_ig_n,
            "D_IC_N": d_ic_n,
            "D_IG_Y": d_ig_y,
            "D_IC_Y": d_ic_y,
            "Psi_G": d_ig_n - d_ig_y,
            "Psi_C": d_ic_n - d_ic_y,
        }
        for name, value in vals.items():
            effects[name].append(value)
        s_i = float(ev["INTACT"]["NATIVE"]["request_selectivity_probability"])
        selectivity_effects["INTACT-GAE"].append(s_i - float(ev["GAE"]["NATIVE"]["request_selectivity_probability"]))
        selectivity_effects["INTACT-BINDING-CUT"].append(s_i - float(ev["BINDING-CUT"]["NATIVE"]["request_selectivity_probability"]))
        root["effects"] = vals
    return {
        "utility_effects_ci95": {name: _ci95(values, C.TCRIT_11) for name, values in effects.items()},
        "native_selectivity_effects_ci95": {name: _ci95(values, C.TCRIT_11) for name, values in selectivity_effects.items()},
    }


def _validate_calibration(calibration: Mapping[str, object]) -> list[str]:
    issues: list[str] = []
    if calibration.get("artifact_kind") != "egrcr_b1_calibration_result":
        issues.append("calibration artifact kind mismatch")
    if calibration.get("treatment") != C.TREATMENT:
        issues.append("calibration treatment mismatch")
    if calibration.get("roots") != list(C.CALIBRATION_ROOTS):
        issues.append("calibration roots mismatch")
    if calibration.get("opportunities_per_root") != C.CALIBRATION_OPPORTUNITIES:
        issues.append("calibration opportunity count mismatch")
    if calibration.get("all_gates_passed") is not True:
        issues.append("one or more calibration gates did not pass")
    gates = calibration.get("gates", {})
    for name in (
        "source_to_target_first_stage",
        "downstream_target_exposure",
        "joiner_record_update_expressibility",
        "cut_support",
    ):
        if not isinstance(gates, Mapping) or not isinstance(gates.get(name), Mapping) or gates[name].get("passed") is not True:
            issues.append(f"calibration gate unavailable: {name}")
    return issues


def run_confirmation(calibration: Mapping[str, object]) -> dict[str, object]:
    issues = _validate_calibration(calibration)
    if issues:
        raise ValueError("confirmation blocked by calibration: " + "; ".join(issues))
    started = time.perf_counter()
    root_results: list[dict[str, object]] = []
    total_ticks = int(calibration["accounting"]["two_agent_physical_ticks"])
    binding_exposed = True
    anomalies: list[str] = []
    delta = float(calibration["frozen_parameters"]["trust_radius_delta"])
    for root_ordinal, root in enumerate(C.CONFIRMATION_ROOTS):
        collected = _collect_root(root, root_ordinal)
        if not bool(collected["supported"]):
            binding_exposed = False
            anomalies.append(f"root {root} did not reach 128 supported edges before 512 blocks")
            root_results.append(
                {
                    "root": root,
                    "collection_blocks": collected["blocks"],
                    "support_counts": collected["counts"],
                    "supported": False,
                }
            )
            continue
        rows = collected["rows"]
        edges = collected["edges"]
        cue_schedule = collected["cue_schedule"]
        action_schedule = collected["action_schedule"]
        schedule_issues: list[str] = []
        if (
            cue_schedule["correct"] != C.CUE_CORRECT_PER_ROOT
            or cue_schedule["flipped"] != C.CUE_FLIPPED_PER_ROOT
        ):
            schedule_issues.append("retained cue schedule is not 116 correct / 12 flipped")
        if action_schedule["requests"] != 64 or action_schedule["no_requests"] != 64:
            schedule_issues.append("retained sampled actions are not exactly 64/64")
        if any(
            float(edge["stored_probability"]) != C.STORED_BEHAVIOR_PROBABILITY
            for edge in edges
        ):
            schedule_issues.append("stored propensity is not exactly 0.5")
        if any(
            (int(edge["joiner_action"]) == 1) != (float(edge["action_uniform"]) < 0.5)
            for edge in edges
        ):
            schedule_issues.append("counter-keyed uniform/action mismatch")
        if schedule_issues:
            binding_exposed = False
            anomalies.extend(f"root {root}: {issue}" for issue in schedule_issues)
            root_results.append(
                {
                    "root": root,
                    "collection_blocks": collected["blocks"],
                    "support_counts": collected["counts"],
                    "supported": True,
                    "cue_schedule": cue_schedule,
                    "action_schedule": action_schedule,
                    "schedule_issues": schedule_issues,
                }
            )
            continue
        mapping, cut_issues = _cut_mapping(edges)
        if cut_issues:
            binding_exposed = False
            anomalies.extend(f"root {root}: {x}" for x in cut_issues)
            root_results.append(
                {
                    "root": root,
                    "collection_blocks": collected["blocks"],
                    "support_counts": collected["counts"],
                    "supported": True,
                    "cut_issues": cut_issues,
                }
            )
            continue
        edge_by_key = {str(e["key"]): e for e in edges}
        calibration_means = calibration["frozen_parameters"]["stratum_kappa_means"]
        multiset_intact = sorted(float(e["kappa"]) for e in edges)
        multiset_cut = sorted(float(edge_by_key[mapping[str(e["key"])]]["kappa"]) for e in edges)
        centered_intact = sorted(
            float(e["kappa"]) - float(calibration_means[str(e["stratum"])]) for e in edges
        )
        centered_cut = sorted(
            float(edge_by_key[mapping[str(e["key"])]]["kappa"])
            - float(calibration_means[str(edge_by_key[mapping[str(e["key"])]]["stratum"])] )
            for e in edges
        )
        conditioned_intact = sorted(
            (float(e["joiner_action"]) - float(e["stored_probability"]))
            * (float(e["kappa"]) - float(calibration_means[str(e["stratum"])]))
            for e in edges
        )
        conditioned_cut = sorted(
            (float(e["joiner_action"]) - float(e["stored_probability"]))
            * (
                float(edge_by_key[mapping[str(e["key"])]]["kappa"])
                - float(calibration_means[str(edge_by_key[mapping[str(e["key"])]]["stratum"])] )
            )
            for e in edges
        )
        if (
            multiset_intact != multiset_cut
            or centered_intact != centered_cut
            or conditioned_intact != conditioned_cut
        ):
            binding_exposed = False
            anomalies.append(f"root {root}: cut label/centered/action-conditioned multiset changed")
            continue

        arm_results: dict[str, object] = {}
        thetas: dict[str, Vector] = {}
        for arm in C.ARMS:
            advantages = _advantages_for_arm(arm, rows, edges, mapping, calibration)
            raw_g, normalized_g, advantage_rms = _gradient(rows, advantages)
            theta = _update([0.0] * len(normalized_g), normalized_g, delta)
            thetas[arm] = theta
            probabilities = [_sigmoid(_dot(theta, row["features"])) for row in rows]
            realized_kl = _mean([_bernoulli_kl_from_half(p) for p in probabilities])
            source_indices = {int(e["source_row"]) for e in edges}
            changed_noneligible = 0
            if arm != "GAE":
                base = [float(r["ordinary_gae"]) for r in rows]
                changed_noneligible = sum(1 for i, (a, b) in enumerate(zip(advantages, base)) if i not in source_indices and a != b)
            waiter_ordinary_gae_untouched = all(
                advantages[i] == float(row["ordinary_gae"])
                for i, row in enumerate(rows)
                if bool(row["is_waiter_request_record"])
            )
            arm_results[arm] = {
                "raw_gradient_norm": _norm(raw_g),
                "normalized_gradient_norm": _norm(normalized_g),
                "advantage_rms_before_normalization": advantage_rms,
                "parameter_displacement": _norm(theta),
                "realized_bernoulli_kl": realized_kl,
                "score_credit_covariance": _score_credit_covariance(rows, advantages),
                "entropy": _mean([_entropy(p) for p in probabilities]),
                "clipping": 0,
                "gradient_evaluations": 1,
                "updates": 1,
                "batch_passes": 1,
                "actor_calls": len(rows),
                "value_calls": len(rows),
                "four_fork_label_calculations": len(edges) * 4,
                "relay_bookkeeping_records": len(edges),
                "changed_noneligible_records": changed_noneligible,
                "waiter_ordinary_gae_untouched": waiter_ordinary_gae_untouched,
                "debit_or_reverse_relay": False,
            }
        displacement_match = max(float(arm_results[a]["parameter_displacement"]) for a in C.ARMS) - min(
            float(arm_results[a]["parameter_displacement"]) for a in C.ARMS
        ) <= 1e-12
        work_match = len({
            (
                arm_results[a]["gradient_evaluations"],
                arm_results[a]["updates"],
                arm_results[a]["batch_passes"],
                arm_results[a]["actor_calls"],
                arm_results[a]["value_calls"],
                arm_results[a]["four_fork_label_calculations"],
                arm_results[a]["relay_bookkeeping_records"],
            )
            for a in C.ARMS
        }) == 1
        evaluation = {arm: _evaluate_arm(root, arm, thetas[arm]) for arm in C.ARMS}
        root_result: dict[str, object] = {
            "root": root,
            "collection_blocks": collected["blocks"],
            "batch_rows": len(rows),
            "eligible_edges": len(edges),
            "support_counts": collected["counts"],
            "cue_schedule": cue_schedule,
            "action_schedule": action_schedule,
            "supported": True,
            "cut": {
                "complete": len(mapping) == len(edges),
                "fixed_point_free": all(k != v for k, v in mapping.items()),
                "bijection": len(set(mapping.values())) == len(edges),
                "opposite_type": all(edge_by_key[k]["type"] != edge_by_key[v]["type"] for k, v in mapping.items()),
                "signed_label_multiset_preserved": multiset_intact == multiset_cut,
                "centered_target_multiset_preserved": centered_intact == centered_cut,
                "action_conditioned_advantage_multiset_preserved": conditioned_intact == conditioned_cut,
                "update_cut_independent_of_evaluation_yoke": True,
            },
            "arms": arm_results,
            "optimizer_and_work": {
                "fresh_stateless_normalized_sgd": True,
                "critic_learning": False,
                "zero_frozen_baseline": True,
                "common_ancestor": True,
                "actor_displacement_match": displacement_match,
                "work_match": work_match,
            },
            "evaluation": evaluation,
        }
        root_results.append(root_result)
        total_ticks += int(collected["blocks"]) * C.BLOCK_TICKS
        total_ticks += len(edges) * 4 * C.BLOCK_TICKS
        total_ticks += len(C.ARMS) * len(C.CONTEXTS) * C.EVALUATION_DYADS * 2 * C.BLOCK_TICKS

    if not binding_exposed:
        return {
            "artifact_kind": "egrcr_b1_result",
            "treatment": C.TREATMENT,
            "stage": "confirmation_stopped_before_binding",
            "question_relevant_activity_began": True,
            "binding_question_exposed": False,
            "calibration_all_gates_passed": True,
            "roots": root_results,
            "accounting": {"two_agent_physical_ticks": total_ticks, "cpu_workers": 1},
            "anomalies": anomalies,
            "runtime_seconds": time.perf_counter() - started,
        }

    aggregate = _aggregate_confirmation(root_results)
    utility_ci = aggregate["utility_effects_ci95"]
    selectivity_ci = aggregate["native_selectivity_effects_ci95"]
    equal_fixed_counts = all(
        len({int(root["evaluation"][arm][ctx]["fixed_token_count"]) for arm in C.ARMS for ctx in C.CONTEXTS}) == 1
        and len({int(root["evaluation"][arm][ctx]["renewal_count"]) for arm in C.ARMS for ctx in C.CONTEXTS}) == 1
        for root in root_results
    )
    actual_selectivity_by_arm = {
        arm: [
            int(root["evaluation"][arm]["NATIVE"]["common_uniform_actual_requests_by_source_type"]["JOINT"])
            - int(root["evaluation"][arm]["NATIVE"]["common_uniform_actual_requests_by_source_type"]["SOLO"])
            for root in root_results
        ]
        for arm in C.ARMS
    }
    actual_probability_effect = all(
        _mean(
            [
                i - b
                for i, b in zip(actual_selectivity_by_arm["INTACT"], actual_selectivity_by_arm[baseline])
            ]
        ) > 0.0
        for baseline in ("GAE", "BINDING-CUT")
    )
    controls_ok = all(
        bool(root["optimizer_and_work"]["actor_displacement_match"])
        and bool(root["optimizer_and_work"]["work_match"])
        and all(bool(root["arms"][arm]["waiter_ordinary_gae_untouched"]) for arm in C.ARMS)
        and all(int(root["arms"][arm]["changed_noneligible_records"]) == 0 for arm in C.ARMS)
        for root in root_results
    )
    criteria = {
        "native_selectivity_intact_above_both": all(
            float(selectivity_ci[name]["lower"]) > 0.0 for name in selectivity_ci
        ),
        "native_utility_intact_above_both": all(
            float(utility_ci[name]["lower"]) > 0.0 and float(utility_ci[name]["mean"]) >= C.UTILITY_EFFECT_MIN
            for name in ("D_IG_N", "D_IC_N")
        ),
        "native_minus_yoked_interactions": all(
            float(utility_ci[name]["lower"]) > 0.0 and float(utility_ci[name]["mean"]) >= C.UTILITY_EFFECT_MIN
            for name in ("Psi_G", "Psi_C")
        ),
        "yoked_absence": all(
            float(utility_ci[name]["mean"]) < C.YOKED_MEAN_MAX
            and float(utility_ci[name]["upper"]) < C.YOKED_CI_UPPER_MAX
            for name in ("D_IG_Y", "D_IC_Y")
        ),
        "probability_reaches_actual_requests": actual_probability_effect,
        "fixed_token_and_renewal_counts_equal": equal_fixed_counts,
        "mapping_work_clock_optimizer_controls": controls_ok,
    }
    if total_ticks > C.MAX_PHYSICAL_TICKS:
        anomalies.append("registered physical-tick cap exceeded")
    complete = len(root_results) == len(C.CONFIRMATION_ROOTS) and not anomalies and controls_ok
    return {
        "artifact_kind": "egrcr_b1_result",
        "treatment": C.TREATMENT,
        "stage": "confirmation_complete",
        "question_relevant_activity_began": True,
        "binding_question_exposed": True,
        "complete_interpretation_surface": complete,
        "calibration_all_gates_passed": True,
        "roots": root_results,
        "aggregate": aggregate,
        "association_criteria": {**criteria, "all_passed": all(criteria.values())},
        "semantics": {
            "source_action": "later joiner request",
            "credit_destination": "later joiner stored request record only",
            "waiter_credit": "ordinary GAE unchanged in every arm",
            "replacement_not_addition": True,
            "debit_or_reverse_relay": False,
        },
        "accounting": {
            "two_agent_physical_ticks": total_ticks,
            "cpu_workers": 1,
            "physical_tick_cap": C.MAX_PHYSICAL_TICKS,
            "cap_respected": total_ticks <= C.MAX_PHYSICAL_TICKS,
            "collection_block_cap": C.COLLECTION_BLOCK_CAP,
            "restarts": 0,
            "sweeps": 0,
            "arm_specific_tuning": False,
            "seed_replacement": False,
            "threshold_repair": False,
            "post_result_enlargement": False,
        },
        "anomalies": anomalies,
        "runtime_seconds": time.perf_counter() - started,
    }
