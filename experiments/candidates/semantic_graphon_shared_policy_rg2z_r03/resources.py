"""Static, non-executing request for the frozen RG2Z r03 panel."""

from __future__ import annotations

from .authorization import ACTION, ARMS
from .config import COUNTER_ROOT, DEVICE, DIRECTION, EVALUATION_EPISODES, REVISION, SEEDS, TRAINING_UPDATES




def resource_proposal() -> dict[str, object]:
    """Return only registered static cost/identity metadata; create no coordinates."""
    return {
        "direction": DIRECTION,
        "revision": REVISION,
        "action": ACTION,
        "run_class": "formal_train_evaluate_analyze_requires_root_compute_lease",
        "registered_seed_count": len(SEEDS),
        "registered_seeds": list(SEEDS),
        "counter_root": COUNTER_ROOT,
        "device": str(DEVICE),
        "requested_concurrency": 4,
        "requested_cpu_cores": 4,
        "torch_intraop_threads": 1,
        "torch_interop_threads": 1,
        "training_updates": TRAINING_UPDATES,
        "evaluation_episodes_per_roster_seed": EVALUATION_EPISODES,
        "learned_arm_count": len(ARMS),
        "unique_training_worlds": 786432, "learned_training_unrolls": 1572864,
        "training_transitions": 18874368, "training_actor_agent_slot_steps": 226492416,
        "full_batch_backward_calls": 24576, "evaluation_worlds": 24576,
        "intact_learned_evaluation_unrolls": 49152, "uniform_evaluation_unrolls": 12288,
        "rotated_evaluation_unrolls": 24576, "total_evaluation_trajectories": 86016,
        "evaluation_transitions": 1032192, "intact_learned_actor_steps": 7520256,
        "rotated_actor_steps": 3981312, "shadow_actor_steps": 1990656,
        "uniform_decisions": 1769472, "total_trajectory_transitions": 19906560,
        "total_learned_actor_steps": 239984640,
        "projected_cpu_core_hours": {"lower": 35, "upper": 100},
        "projected_ram_gib_per_worker": {"lower": 1, "upper": 2},
        "projected_retained_storage_gib": {"lower": 0.1, "upper": 0.5},
        "requested_scratch_gib_total": 8,
        "checkpoint_identity": "only_evaluable_state_immediately_after_update_512",
        "atomic_seed_frontier": "one temporary directory is renamed only after the complete seed packet",
        "admission_note": "Static proposal only. A current exact Root lease is required before any training or evaluation.",
    }
