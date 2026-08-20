from __future__ import annotations

from .config import ARMS, EVAL_SIZES, REGISTERED, SEEDS, TRAIN_SIZES


def resource_proposal() -> dict[str, object]:
    training = len(SEEDS) * len(ARMS) * REGISTERED.train_updates * 4 * REGISTERED.train_episodes_per_cell
    ordinary = len(SEEDS) * len(ARMS) * len(EVAL_SIZES) * 2 * REGISTERED.eval_episodes_per_cell
    cuts = len(SEEDS) * 2 * REGISTERED.eval_episodes_per_cell
    training_decisions = len(SEEDS) * len(ARMS) * REGISTERED.train_updates * REGISTERED.train_episodes_per_cell * 2 * sum((5, 5, 7, 7))
    ordinary_decisions = len(SEEDS) * len(ARMS) * REGISTERED.eval_episodes_per_cell * 2 * 2 * sum(EVAL_SIZES)
    cut_decisions = len(SEEDS) * 2 * REGISTERED.eval_episodes_per_cell * 2 * 9
    return {
        "run_class": "exact CPC-r04 full frozen train-evaluate-analyze requires Root direction lease",
        "requested_cpu_cores": 1,
        "requested_gpu_count": 0,
        "requested_concurrency": 1,
        "requested_peak_memory_mib": 2048,
        "registered_wall_minutes": REGISTERED.max_wall_minutes,
        "training_episodes": training,
        "ordinary_evaluation_episodes": ordinary,
        "cut_episodes": cuts,
        "total_registered_episodes": training + ordinary + cuts,
        "training_agent_decisions": training_decisions,
        "ordinary_evaluation_agent_decisions": ordinary_decisions,
        "cut_agent_decisions": cut_decisions,
        "total_agent_decisions": training_decisions + ordinary_decisions + cut_decisions,
        "optimizer_steps": len(SEEDS) * len(ARMS) * REGISTERED.train_updates,
        "active_seed_parameters": len(ARMS) * REGISTERED.parameters_per_arm,
        "atomic_frontier": "one complete three-arm seed packet; incomplete seed remains non-analyzable temporary state",
    }
