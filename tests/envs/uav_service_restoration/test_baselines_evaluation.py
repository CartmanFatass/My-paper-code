"""Diagnostic controllers and the counterfactual evaluator.

These controllers exist to make the environment's behaviour legible, not to be good.  The
checks below are mostly about the *evaluation*: that every controller sees only the
information the learner would, that the references do not depend on the evaluated policy,
and that an automatic repair is never credited to a UAV.
"""

from __future__ import annotations

import copy
import json

import numpy as np
import pytest

from envs.uav_service_restoration import UAVServiceRestorationEnv, config_from_dict
from envs.uav_service_restoration.baselines import CONTROLLER_NAMES, build_controller
from envs.uav_service_restoration.evaluation import (
    ServiceTrace,
    affected_demand_mask,
    evaluate_rollout,
    healthy_schedule,
    recovery_report,
    rollout_controller,
    simulate_no_uav_trace,
)
from envs.uav_service_restoration.events import schedule_from_events
from envs.uav_service_restoration.network import demand_positions_from_xy
from envs.uav_service_restoration.types import EventType, NetworkEvent


def _offered(env) -> np.ndarray:
    return np.stack(
        [np.asarray(row, dtype=np.float64) for row in env.accumulator.offered_series_mbps]
    )


def _references(config, env):
    """The two policy-independent traces, computed exactly as the evaluator does."""

    episode = env.episode_descriptor
    layout = env.demand_layout
    positions = demand_positions_from_xy(layout.positions_m, 0.0)
    failed = simulate_no_uav_trace(
        config, env.demand_source, episode, env.event_schedule, layout, positions
    )
    healthy = simulate_no_uav_trace(
        config,
        env.demand_source,
        episode,
        healthy_schedule(env.event_schedule),
        layout,
        positions,
    )
    return healthy, failed


# --------------------------------------------------------------------------------------
# Controller contract and information condition
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", CONTROLLER_NAMES)
def test_every_controller_emits_valid_actions_from_the_policy_view(name, short_config):
    """A controller may read only ``get_current_state()`` and must return legal actions."""

    env = UAVServiceRestorationEnv(short_config)
    controller = build_controller(name, short_config, seed=3)
    controller.reset()
    env.reset(seed=11)
    space = env.action_space(env.agents[0])
    while env.agents:
        view = env.get_current_state()
        actions = controller.act(view, list(env.agents))
        assert set(actions) == set(env.agents)
        for action in actions.values():
            assert action.shape == space.shape
            assert action.dtype == space.dtype
            assert np.all(np.isfinite(action))
            assert space.contains(action)
        env.step(actions)


def test_the_controller_view_carries_no_ground_truth(short_config):
    """The baselines run under the learner's information condition, not above it.

    Whatever a controller infers about a failure it must infer from the same delayed,
    masked view; the true demand and the true site states stay in the privileged channel.
    """

    env = UAVServiceRestorationEnv(short_config)
    env.reset(seed=11)
    view = env.get_current_state()
    privileged = env.get_privileged_diagnostics()
    for forbidden in (
        "true_demand_mbps",
        "site_states",
        "exogenous_events",
        "episode_id",
        "dataset_hash",
        "alert_time_s",
    ):
        assert forbidden not in view, f"{forbidden} must stay out of the policy view"
    # The separation is real, not vacuous: the evaluator channel does carry the episode
    # identity and the exogenous event list, and the true site states are reachable only
    # through the privileged schedule object.
    for expected in ("episode_id", "dataset_hash", "exogenous_events", "alert_time_s"):
        assert expected in privileged
    assert env.event_schedule.site_states(0.0) is not None


def test_static_controller_never_requests_motion(short_config):
    """The reference controller is exactly "do nothing": all-zero velocity requests."""

    env = UAVServiceRestorationEnv(short_config)
    controller = build_controller("static_uav", short_config)
    controller.reset()
    env.reset(seed=7)
    start = env.uav_positions_m.copy()
    while env.agents:
        actions = controller.act(env.get_current_state(), list(env.agents))
        for action in actions.values():
            assert np.all(action == 0.0)
        env.step(actions)
    assert np.allclose(env.uav_positions_m, start)


def test_random_controller_is_seed_reproducible(short_config):
    """Two identically seeded random controllers produce identical action sequences."""

    sequences = []
    for _ in range(2):
        env = UAVServiceRestorationEnv(short_config)
        controller = build_controller("random", short_config, seed=99)
        controller.reset()
        env.reset(seed=4)
        seen = []
        while env.agents:
            actions = controller.act(env.get_current_state(), list(env.agents))
            seen.append(np.stack([actions[agent] for agent in env.agents]))
            env.step(actions)
        sequences.append(np.stack(seen))
    assert np.array_equal(sequences[0], sequences[1])


def test_unknown_controller_name_is_rejected(short_config):
    with pytest.raises(ValueError, match="unknown controller"):
        build_controller("oracle", short_config)


# --------------------------------------------------------------------------------------
# Counterfactual references
# --------------------------------------------------------------------------------------


def test_references_are_policy_independent(smoke_config):
    """Two different controllers must produce identical healthy and failed references.

    The references are computed from the exogenous world alone, so this is exact
    equality, not an approximation.
    """

    references = []
    for name in ("static_uav", "backhaul_aware_greedy"):
        env = UAVServiceRestorationEnv(smoke_config)
        controller = build_controller(name, smoke_config, seed=1)
        controller.reset()
        env.reset(seed=21)
        while env.agents:
            env.step(controller.act(env.get_current_state(), list(env.agents)))
        healthy, failed = _references(smoke_config, env)
        references.append((healthy.delivered_mbit.copy(), failed.delivered_mbit.copy()))
    assert np.array_equal(references[0][0], references[1][0])
    assert np.array_equal(references[0][1], references[1][1])


def test_the_healthy_reference_dominates_the_failed_one(smoke_config):
    """Removing the failure cannot reduce delivered service anywhere in this model."""

    env = UAVServiceRestorationEnv(smoke_config)
    env.reset(seed=21)
    healthy, failed = _references(smoke_config, env)
    assert healthy.delivered_mbit.sum() > failed.delivered_mbit.sum()
    assert np.all(healthy.delivered_mbit >= failed.delivered_mbit - 1e-9)


def test_the_affected_set_is_the_eastern_column_only(smoke_config):
    """The affected set follows from the reference gap, not from any UAV trajectory.

    In the smoke fixture the failed site is the eastern one at x = 2400 m and only the
    three eastern demand points depend on it; the rest stay inside the western site's
    access radius.
    """

    env = UAVServiceRestorationEnv(smoke_config)
    env.reset(seed=21)
    healthy, failed = _references(smoke_config, env)
    affected = affected_demand_mask(healthy, failed)
    positions = env.demand_layout.positions_m
    assert int(affected.sum()) == 3
    assert np.all(positions[affected, 0] > 2000.0)
    assert np.all(positions[~affected, 0] < 2000.0)


# --------------------------------------------------------------------------------------
# Recovery semantics, on hand-built traces
# --------------------------------------------------------------------------------------


def _trace(starts, durations, rates) -> ServiceTrace:
    rate_array = np.asarray(rates, dtype=np.float64).reshape(len(starts), -1)
    return ServiceTrace(
        start_s=np.asarray(starts, dtype=np.float64),
        duration_s=np.asarray(durations, dtype=np.float64),
        offered_mbps=np.zeros_like(rate_array),
        delivered_mbps=rate_array,
    )


def _recovery_config(config_doc, **evaluation):
    document = copy.deepcopy(config_doc)
    document.setdefault("evaluation", {}).update(evaluation)
    return config_from_dict(document)


def test_a_zero_healthy_reference_is_skipped_not_divided_by(config_doc):
    """Instants where the healthy reference delivers nothing carry no evidence.

    They must not be divided by, must not open a sustain window, and must be counted so
    the reader can see how much of the episode was uninformative.  Here the only instant
    that can open a window is t = 20 s: t = 0 s fails the threshold and t = 10 s has a
    zero healthy reference.
    """

    config = _recovery_config(config_doc, recovery_fraction_rho=0.9, recovery_sustain_s=20.0)
    starts, durations = [0.0, 10.0, 20.0, 30.0], [10.0, 10.0, 10.0, 10.0]
    healthy = _trace(starts, durations, [[10.0], [0.0], [10.0], [10.0]])
    failed = _trace(starts, durations, [[0.0], [0.0], [0.0], [0.0]])
    controller = _trace(starts, durations, [[2.0], [0.0], [9.5], [10.0]])
    schedule = schedule_from_events(
        [NetworkEvent(EventType.FULL_SITE_FAILURE, 1, 0.0, None, 0.0, 0.0)], 2
    )
    report = recovery_report(
        config, healthy, failed, controller, schedule, np.array([True])
    )
    assert report["applicable"] is True
    assert report["not_applicable_instants"] == 1
    assert report["recovery_time_s"] == pytest.approx(20.0)
    assert report["censored"] is False
    assert np.isfinite(report["fraction_of_lost_service_restored"])


def test_a_gapless_healthy_reference_gives_a_not_a_number_fraction(config_doc):
    """When the failure cost nothing there is nothing to restore: NaN, not a division."""

    config = _recovery_config(config_doc, recovery_sustain_s=10.0)
    starts, durations = [0.0, 10.0], [10.0, 10.0]
    healthy = _trace(starts, durations, [[10.0], [10.0]])
    failed = _trace(starts, durations, [[10.0], [10.0]])
    controller = _trace(starts, durations, [[10.0], [10.0]])
    schedule = schedule_from_events(
        [NetworkEvent(EventType.FULL_SITE_FAILURE, 1, 0.0, None, 0.0, 0.0)], 2
    )
    report = recovery_report(
        config, healthy, failed, controller, schedule, np.array([True])
    )
    assert np.isnan(report["fraction_of_lost_service_restored"])


def test_a_threshold_first_met_after_repair_is_censored(config_doc):
    """A site that repairs itself must not be scored as a restoration by the UAVs.

    The controller never reaches the threshold while the site is down; service returns at
    the repair instant because the site came back.  The report must censor the episode
    with that reason rather than return the repair time as a recovery time.
    """

    config = _recovery_config(config_doc, recovery_fraction_rho=0.9, recovery_sustain_s=20.0)
    starts, durations = [0.0, 20.0, 40.0, 60.0, 80.0], [20.0] * 5
    healthy = _trace(starts, durations, [[10.0]] * 5)
    failed = _trace(starts, durations, [[0.0], [0.0], [10.0], [10.0], [10.0]])
    controller = _trace(starts, durations, [[1.0], [1.0], [10.0], [10.0], [10.0]])
    schedule = schedule_from_events(
        [NetworkEvent(EventType.FULL_SITE_FAILURE, 1, 0.0, 40.0, 0.0, 0.0)], 2
    )
    report = recovery_report(
        config, healthy, failed, controller, schedule, np.array([True])
    )
    assert report["first_repair_s"] == pytest.approx(40.0)
    assert report["recovery_time_s"] is None
    assert report["censored"] is True
    assert report["censoring_reason"] == "threshold_first_met_after_automatic_repair"


def test_a_recovery_before_repair_is_credited(config_doc):
    """The same schedule, but the controller restores service before the site returns."""

    config = _recovery_config(config_doc, recovery_fraction_rho=0.9, recovery_sustain_s=20.0)
    starts, durations = [0.0, 20.0, 40.0, 60.0, 80.0], [20.0] * 5
    healthy = _trace(starts, durations, [[10.0]] * 5)
    failed = _trace(starts, durations, [[0.0], [0.0], [10.0], [10.0], [10.0]])
    controller = _trace(starts, durations, [[9.5], [9.5], [10.0], [10.0], [10.0]])
    schedule = schedule_from_events(
        [NetworkEvent(EventType.FULL_SITE_FAILURE, 1, 0.0, 40.0, 0.0, 0.0)], 2
    )
    report = recovery_report(
        config, healthy, failed, controller, schedule, np.array([True])
    )
    assert report["recovery_time_s"] == pytest.approx(0.0)
    assert report["time_to_recovery_s"] == pytest.approx(0.0)
    assert report["censored"] is False


def test_recovery_is_not_applicable_without_a_capability_loss(config_doc):
    """No failure means "not applicable", not a recovery time of zero."""

    config = _recovery_config(config_doc)
    starts, durations = [0.0, 10.0], [10.0, 10.0]
    trace = _trace(starts, durations, [[10.0], [10.0]])
    report = recovery_report(
        config, trace, trace, trace, schedule_from_events([], 2), np.array([True])
    )
    assert report["applicable"] is False
    assert report["recovery_time_s"] is None
    assert "no capability loss" in report["reason"]


def test_recovery_is_not_applicable_when_the_failure_harmed_nothing(config_doc):
    """A failure with an empty affected set is reported as such, not as a failed recovery."""

    config = _recovery_config(config_doc)
    starts, durations = [0.0, 10.0], [10.0, 10.0]
    trace = _trace(starts, durations, [[10.0], [10.0]])
    schedule = schedule_from_events(
        [NetworkEvent(EventType.FULL_SITE_FAILURE, 1, 0.0, None, 0.0, 0.0)], 2
    )
    report = recovery_report(
        config, trace, trace, trace, schedule, np.array([False])
    )
    assert report["applicable"] is False
    assert "harmed no demand point" in report["reason"]


# --------------------------------------------------------------------------------------
# Rollout record
# --------------------------------------------------------------------------------------


def test_a_static_rollout_is_censored_not_scored_zero(smoke_config):
    """A static controller cannot restore the east, so the episode must be censored."""

    env = UAVServiceRestorationEnv(smoke_config)
    record = rollout_controller(env, build_controller("static_uav", smoke_config), seed=21)
    recovery = record["recovery"]
    assert recovery["applicable"] is True
    assert recovery["recovery_time_s"] is None
    assert recovery["censored"] is True
    assert recovery["censoring_reason"] == "threshold_not_reached_within_episode"
    assert recovery["fraction_of_lost_service_restored"] == pytest.approx(0.0, abs=1e-9)


def test_the_rollout_record_reports_zero_updates_and_its_provenance(smoke_config):
    """A diagnostic rollout must state that it trained nothing and that it is fixture-based."""

    env = UAVServiceRestorationEnv(smoke_config)
    record = rollout_controller(env, build_controller("demand_greedy", smoke_config), seed=21)
    assert record["controller"]["optimizer_updates"] == 0
    assert record["controller"]["information_condition"] == smoke_config.observations.mode
    assert record["episode"]["is_real_activity_data"] is False
    assert record["episode"]["provenance"] == "fixture_based"
    assert record["episode_summary"]["energy_joules"] is None
    assert record["episode_summary"]["energy_status"].startswith("unavailable")
    assert json.dumps(record)  # the whole record is JSON-serialisable as written


def test_controllers_are_separated_by_the_evaluator(smoke_config):
    """The evaluator resolves the configured controllers into distinct outcomes.

    This is a recorded property of the *fixture*, so that a later change which flattens
    every controller onto the same number becomes visible.  It is not evidence about any
    algorithm, and the greedy controllers are not tuned.
    """

    results = {}
    for name in CONTROLLER_NAMES:
        env = UAVServiceRestorationEnv(smoke_config)
        record = rollout_controller(env, build_controller(name, smoke_config, seed=5), seed=21)
        results[name] = (
            record["references"]["controller_satisfaction"],
            record["recovery"]["fraction_of_lost_service_restored"],
        )
    assert results["backhaul_aware_greedy"][0] > results["static_uav"][0] + 1e-3
    assert results["backhaul_aware_greedy"][1] > results["static_uav"][1] + 1e-3
    # The naive greedy reads only *reported* unmet demand, so the unsensed eastern column
    # never enters its target set and it behaves exactly like the static reference.
    assert results["demand_greedy"][0] == pytest.approx(results["static_uav"][0], rel=1e-9)


def test_evaluate_rollout_matches_a_hand_assembled_call(smoke_config):
    """``rollout_controller`` is exactly loop + ``evaluate_rollout``, with nothing hidden."""

    env = UAVServiceRestorationEnv(smoke_config)
    controller = build_controller("backhaul_aware_greedy", smoke_config)
    controller.reset()
    env.reset(seed=21)
    while env.agents:
        env.step(controller.act(env.get_current_state(), list(env.agents)))
    manual = evaluate_rollout(smoke_config, env, env.accumulator, _offered(env))

    other = UAVServiceRestorationEnv(smoke_config)
    through_api = rollout_controller(
        other, build_controller("backhaul_aware_greedy", smoke_config), seed=21
    )
    assert manual["references"] == through_api["references"]
    assert manual["recovery"] == through_api["recovery"]
    assert manual["affected_points"] == through_api["affected_points"]


def test_a_rollout_performs_no_optimizer_step_and_loads_no_torch(smoke_config):
    """Forward-only by construction: the rollout path must not even import torch."""

    import sys

    assert "torch" not in sys.modules or True  # pytest itself may have imported it
    env = UAVServiceRestorationEnv(smoke_config)
    before = dict(sys.modules)
    rollout_controller(env, build_controller("static_uav", smoke_config), seed=21)
    newly = set(sys.modules) - set(before)
    assert not {name for name in newly if name.split(".")[0] == "torch"}
