from __future__ import annotations

from .config import ARMS, EVAL_SIZES, REGISTERED, SEEDS, TRAIN_SIZES


def resource_proposal() -> dict[str, object]:
    training_episodes = len(SEEDS) * len(ARMS) * len(TRAIN_SIZES) * REGISTERED.train_updates * 16
    ordinary_episodes = len(SEEDS) * len(ARMS) * len(EVAL_SIZES) * REGISTERED.eval_campaigns_per_size * 4
    cut_episodes = len(SEEDS) * 2 * len(EVAL_SIZES) * REGISTERED.eval_campaigns_per_size * 4
    training_decisions = len(SEEDS) * len(ARMS) * REGISTERED.train_updates * (
        16 * 4 * 2 + 16 * 8 * 2
    )
    ordinary_decisions = len(SEEDS) * len(ARMS) * REGISTERED.eval_campaigns_per_size * 4 * 2 * sum(EVAL_SIZES)
    cut_decisions = len(SEEDS) * 2 * REGISTERED.eval_campaigns_per_size * 4 * 2 * sum(EVAL_SIZES)
    return {
        "run_class": "full_frozen_train_evaluate_analyze_requires_direction_compute_lease",
        "requested_cpu_cores": 1,
        "requested_gpu_count": 0,
        "requested_concurrency": 1,
        "requested_peak_memory_mib": REGISTERED.max_memory_mib,
        "registered_wall_minutes": REGISTERED.max_wall_minutes,
        "training_episodes": training_episodes,
        "ordinary_evaluation_episodes": ordinary_episodes,
        "cut_episodes": cut_episodes,
        "total_registered_episodes": training_episodes + ordinary_episodes + cut_episodes,
        "training_agent_decisions": training_decisions,
        "ordinary_evaluation_agent_decisions": ordinary_decisions,
        "cut_agent_decisions": cut_decisions,
        "total_agent_decisions": training_decisions + ordinary_decisions + cut_decisions,
        "actor_optimizer_steps": len(SEEDS) * len(ARMS) * REGISTERED.train_updates,
        "posterior_optimizer_steps": len(SEEDS) * len(ARMS) * REGISTERED.train_updates,
        "active_seed_actor_parameters": len(ARMS) * REGISTERED.actor_parameters,
        "active_seed_posterior_parameters": len(ARMS) * REGISTERED.posterior_parameters,
        "atomic_frontier": "one complete all-four-arm seed packet; interrupted seed replays identical addresses result-blind",
        "measured_wall_seconds": None,
        "measured_peak_memory_mib": None,
    }
