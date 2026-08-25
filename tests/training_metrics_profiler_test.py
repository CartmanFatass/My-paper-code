from types import SimpleNamespace

import numpy as np

from train_multiproc_config_1 import (
    EnhancedRewardTracker,
    TrainingProfiler,
    count_skill_switches_for_metrics,
    uses_process_high_level_flow,
)


def make_tracker(tmp_path):
    config = SimpleNamespace(
        rollout_length=4,
        paper_data_level="standard",
        enable_data_sampling=False,
        collect_step_rewards=False,
        collect_reward_components=False,
        paper_data_dir=None,
    )
    return EnhancedRewardTracker(str(tmp_path), config, n_users=10)


def test_training_metrics_levels(tmp_path):
    tracker = make_tracker(tmp_path)
    info = {
        "reward_info": {
            "coverage_ratio": 0.5,
            "effective_connected_users": 5,
            "system_throughput_mbps": 12.0,
            "quality_shaping_reward": 3.0,
        }
    }

    tracker.log_training_step(1, 0, 1.0, info=info, metrics_level="light")
    assert tracker.training_rewards["total_steps"] == 1
    assert tracker.step_metric_buffer[0][0]["coverage_ratio"] == 0.5
    assert tracker.performance_metrics["served_users"][-1]["served_users"] == 5

    light_records = len(tracker.step_metric_buffer[0])
    tracker.log_training_step(2, 0, 1.0, info=info, metrics_level="minimal")
    assert tracker.training_rewards["total_steps"] == 2
    assert len(tracker.step_metric_buffer[0]) == light_records

    tracker.log_training_step(3, 0, 1.0, info=info, metrics_level="off")
    assert tracker.training_rewards["total_steps"] == 3
    assert len(tracker.step_metric_buffer[0]) == light_records


def test_training_metrics_light_batch_path(tmp_path):
    tracker = make_tracker(tmp_path)
    infos = [
        {"reward_info": {"coverage_ratio": 0.25, "effective_connected_users": 2}},
        {"reward_info": {"coverage_ratio": 0.75, "effective_connected_users": 7}},
    ]

    tracker.log_training_step_batch(10, [1.0, 2.0], infos, metrics_level="light")

    assert tracker.training_rewards["total_steps"] == 2
    assert tracker.step_metric_buffer[0][0]["coverage_ratio"] == 0.25
    assert tracker.step_metric_buffer[1][0]["coverage_ratio"] == 0.75
    assert tracker.performance_metrics["served_users"][-1]["served_users"] == 7


def test_training_profiler_disabled_is_noop():
    profiler = TrainingProfiler(enabled=False)
    profiler.start_rollout()
    profiler.add("agent_step", 1.0)
    assert profiler.current == {}


def test_skill_switch_counter_uses_hactse_active_skills():
    assert count_skill_switches_for_metrics(None, fallback_changed=False) == 0
    assert count_skill_switches_for_metrics({}, fallback_changed=True) == 1
    assert count_skill_switches_for_metrics(
        {
            "active_skill_prev": np.array([-1, -1]),
            "active_skill": np.array([0, 1]),
            "initial_assignment_mask": np.array([1.0, 1.0]),
        },
        fallback_changed=True,
    ) == 0
    assert count_skill_switches_for_metrics(
        {
            "active_skill_prev": np.array([0, 1, 2]),
            "active_skill": np.array([0, 2, 0]),
            "initial_assignment_mask": np.array([0.0, 0.0, 0.0]),
        },
        fallback_changed=True,
    ) == 2


def test_process_high_level_flow_detection():
    assert uses_process_high_level_flow(
        SimpleNamespace(use_process_exploration=True, use_discrete_skill_lifetimes=True)
    )
    assert not uses_process_high_level_flow(
        SimpleNamespace(use_process_exploration=True, use_discrete_skill_lifetimes=False)
    )
    assert not uses_process_high_level_flow(SimpleNamespace())


def test_log_skill_usage_accepts_switch_count(tmp_path):
    tracker = make_tracker(tmp_path)
    tracker.log_skill_usage(1, 0, [0, 1], switch_count=2)
    tracker.log_skill_usage(2, 0, [0, 1], skill_changed=False)
    assert tracker.skill_usage["skill_switches"] == 2
