from __future__ import annotations

from .config import ALL_SIZES, ARMS, EDGE_ARMS, HELDOUT_SIZES, REGIMES, REGISTERED, SEEDS


def resource_proposal() -> dict[str, object]:
    train_worlds_per_seed = REGISTERED.train_updates * REGISTERED.train_batch_worlds
    evaluation_worlds_per_seed = len(ALL_SIZES) * len(REGIMES) * REGISTERED.eval_worlds_per_cell
    intact_calls = evaluation_worlds_per_seed * len(ARMS)
    identity_intact_calls = intact_calls
    reassociation_calls = (
        len(HELDOUT_SIZES) * REGISTERED.eval_worlds_per_cell * len(EDGE_ARMS)
    )
    identity_reassociation_calls = reassociation_calls
    center_swap_calls = len(HELDOUT_SIZES) * REGISTERED.eval_worlds_per_cell
    identity_center_swap_calls = center_swap_calls
    evaluation_policy_calls = (
        intact_calls + identity_intact_calls + reassociation_calls
        + identity_reassociation_calls + center_swap_calls
        + identity_center_swap_calls
    )
    training_arm_world_forwards = train_worlds_per_seed * len(ARMS)
    backward_calls = REGISTERED.train_updates * len(ARMS)
    checkpoint_dense_audit_policy_calls = 7
    seed_count = len(SEEDS)
    return {
        "direction": "semantic_graphon_shared_policy",
        "revision": "SGSP-B1-SCIENCE-20260814-06",
        "run_class": "formal_train_evaluate_analyze_requires_root_compute_lease",
        "requested_concurrency": REGISTERED.max_workers,
        "requested_cpu_cores": 1,
        "requested_gpu_count": 0,
        "torch_intraop_threads": 1,
        "torch_interop_threads": 1,
        "device": "CPU",
        "dtype": REGISTERED.dtype,
        "formal_wall_clock_hard_cap_hours": REGISTERED.max_formal_wall_clock_hours,
        "projected_one_cpu_wall_clock_hours": {
            "lower": 1.5,
            "upper": 4.5,
            "basis": "static operation count only; no benchmark or rehearsal authorized",
        },
        "projected_peak_rss_mib": 1024,
        "requested_peak_rss_cap_mib": 1536,
        "projected_retained_storage_mib": 100,
        "requested_storage_cap_mib": 250,
        "requested_lease_validity": "8 continuous hours from issuance",
        "registered_seed_count": seed_count,
        "train_worlds_per_seed": train_worlds_per_seed,
        "train_arm_world_forwards_per_seed": training_arm_world_forwards,
        "backward_calls_per_seed": backward_calls,
        "evaluation_worlds_per_seed": evaluation_worlds_per_seed,
        "intact_policy_calls_per_seed": intact_calls,
        "identity_intact_policy_calls_per_seed": identity_intact_calls,
        "sender_reassociation_policy_calls_per_seed": reassociation_calls,
        "identity_reassociation_policy_calls_per_seed": identity_reassociation_calls,
        "sgsp_center_swap_policy_calls_per_seed": center_swap_calls,
        "identity_center_swap_policy_calls_per_seed": identity_center_swap_calls,
        "evaluation_policy_calls_per_seed": evaluation_policy_calls,
        "checkpoint_dense_audit_policy_calls_per_seed": checkpoint_dense_audit_policy_calls,
        "registered_train_worlds_total": train_worlds_per_seed * seed_count,
        "registered_train_arm_world_forwards_total": training_arm_world_forwards * seed_count,
        "registered_backward_calls_total": backward_calls * seed_count,
        "registered_evaluation_worlds_total": evaluation_worlds_per_seed * seed_count,
        "registered_evaluation_policy_calls_total": evaluation_policy_calls * seed_count,
        "registered_policy_forwards_total": (
            training_arm_world_forwards + evaluation_policy_calls
            + checkpoint_dense_audit_policy_calls
        ) * seed_count,
        "hypothetical_trajectory_candidates": 0,
        "hypothetical_transitions": 0,
        "deployed_aggregation_time": "O(2N)",
        "deployed_input_storage": "O(N)",
        "learned_dense_pairwise_objects": 0,
        "fixed_small_dense_reference": "deterministic simulator/audit only; N<=16",
        "atomic_seed_frontier": "one temp directory renamed only after complete four-arm packet",
        "admission_note": (
            "Proposal only: a valid exact-revision Root lease token is required; terminate "
            "inside the first lease's eight-hour continuous cumulative window and retain no "
            "partial seed as evidence."
        ),
    }
