from __future__ import annotations

import copy
import hashlib
import io
import inspect
from collections.abc import Iterator
from pathlib import Path

import pytest
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47 as g47,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)


ANCHOR_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/research/cdc/EVIDENCE_NOTES/fixtures/"
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/"
    "replicate_0_common_native6_fast_anchor.pt"
)
ANCHOR_SHA256 = "d6920e8ab958b776ee0b25a5d2a1b120528b69abc87d4eacc2a6deee2351b521"


class _CriticStateReadTrap:
    """Expose every actor field while rejecting baseline-only state reads."""

    def __init__(self, trajectory: g40.AnchoredRosterTrajectory) -> None:
        self._trajectory = trajectory

    @property
    def critic_states(self) -> torch.Tensor:
        raise AssertionError("reduced G47 path read critic_states")

    def __getattr__(self, name: str) -> object:
        return getattr(self._trajectory, name)


@pytest.fixture(scope="module")
def accepted_anchor_batch() -> Iterator[
    tuple[g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory]
]:
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        payload = ANCHOR_FIXTURE.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == ANCHOR_SHA256
        anchor = g41.load_accepted_g40_anchor_checkpoint(
            torch.load(io.BytesIO(payload), map_location="cpu", weights_only=False),
            accepted_anchor_replicate=0,
        )
        trajectory = g40.collect_g40_trajectory(
            anchor,
            episode_ids=range(8),
            ledger_seed=11_453_000,
            action_seed=11_453_000,
            device=torch.device("cpu"),
        )
        assert trajectory.rewards.numel() == 384
        yield anchor, trajectory
    finally:
        torch.set_num_threads(previous_threads)


def _project(
    anchor: g40.G40NativeSixPolicy,
) -> tuple[
    dict[str, g47.G47Model],
    dict[str, torch.optim.Adam],
]:
    models = g47.project_g47_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    return models, g47.make_g47_optimizers(models)


def test_static_projection_deletes_only_baseline_and_proves_factorization(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, _ = accepted_anchor_batch
    rng_before = torch.random.get_rng_state().clone()
    models, optimizers = _project(anchor)
    reference = models[g47.REFERENCE_ARM]
    reduced = models[g47.REDUCED_ARM]

    assert torch.equal(rng_before, torch.random.get_rng_state())
    assert hasattr(reference, "credit_baselines")
    assert not hasattr(reduced, "credit_baselines")
    assert not hasattr(reduced, "baseline_values")
    assert "critic_state" not in inspect.signature(
        g47._actor_only_step
    ).parameters
    assert all("credit_baselines" not in key for key in reduced.state_dict())
    assert g47._state_equal(
        g47._actor_state(reference), g47._actor_state(reduced)
    )

    boundary = g47.branch_boundary_audit(models, optimizers)
    assert boundary["passed"] is True, boundary
    assert boundary["actor_Adam_projection_equal"] is True
    assert boundary["shared_tensor_storage_count"] == 0
    assert boundary["reference_optimizer_parameter_names"] == (
        boundary["actor_parameter_names"]
        + boundary["reference_baseline_parameter_names"]
    )
    assert boundary["reduced_optimizer_parameter_names"] == boundary[
        "actor_parameter_names"
    ]

    certificate = g47.reconstruct_static_certificate(models, optimizers)
    assert g47.validate_static_certificate(certificate), certificate
    assert certificate["static_certificate_first"] is True
    assert all(
        value == 0 for value in certificate["static_predicates"].values()
    )
    assert certificate["static_predicates"][
        "baseline_true_state_read_into_reduced_actor_gradient"
    ] == 0
    assert certificate["static_predicates"][
        "baseline_true_state_read_into_reduced_actor_action_or_logprob"
    ] == 0
    assert certificate["static_predicates"][
        "baseline_true_state_read_into_reduced_evaluation"
    ] == 0
    assert all(
        certificate["baseline_true_state_reads_by_component"][name] == []
        for name in ("actor_gradient", "action_or_logprob", "evaluation")
    )
    assert certificate["optimizer_predicates"] == {
        "actor_optimizer_class_equal": True,
        "actor_hyperparameters_equal": True,
        "actor_parameter_order_equal": True,
        "actor_step_counters_equal": True,
        "actor_exp_avg_equal": True,
        "actor_exp_avg_sq_equal": True,
        "global_gradient_clipping": False,
        "joint_actor_baseline_normalization": False,
        "loss_count_dependent_scaling": False,
        "optimizer_wide_scheduler": False,
        "global_optimizer_state_count": 0,
    }

    forged = copy.deepcopy(certificate)
    forged["static_predicates"]["baseline_to_action_or_logprob_paths"] = 1
    assert not g47.validate_static_certificate(forged)


def test_one_shared_batch_is_bitwise_equal_and_checkpoint_rejects_baseline_leakage(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models, optimizers = _project(anchor)
    reduced_model = models[g47.REDUCED_ARM]
    assert isinstance(reduced_model, g47.G47NoBaselineProjection)
    trapped = _CriticStateReadTrap(trajectory)
    monkeypatch.setattr(g47, "_actor_only_trajectory_view", lambda _: trapped)
    replay = g47.actor_only_replay(reduced_model, trapped)  # type: ignore[arg-type]
    assert replay.log_probs.shape == trajectory.old_log_probs.shape
    assert g47.actor_trace(reduced_model, trapped)[  # type: ignore[arg-type]
        "token_log_probability_digest"
    ]
    record = g47.optimize_shadow_baseline_module_reduction_update(
        models, optimizers, trajectory
    )
    assert g47.validate_dynamic_equivalence(record), record
    assert record["real_transitions"] == 384
    assert record["D_G47"] == 0
    assert record["formal_statistical_run"] is False
    assert len(record["pass_records"]) == 2
    assert all(
        row["actor_gradient_bytes_equal"]
        and row["actor_parameter_bytes_equal"]
        and row["actor_Adam_bytes_equal"]
        and row["pre_tanh_bytes_equal"]
        and row["action_bytes_equal"]
        and row["token_logprob_bytes_equal"]
        and row["joint_logprob_bytes_equal"]
        and row["cross_gradient_audit"][
            "baseline_loss_gradient_into_actor_count"
        ]
        == 0
        and row["cross_gradient_audit"][
            "actor_loss_gradient_into_baseline_count"
        ]
        == 0
        for row in record["pass_records"]
    )

    checkpoints = g47.build_final_checkpoints(models, optimizers, record)
    assert g47.validate_checkpoint_pair(checkpoints)
    reference = checkpoints[g47.REFERENCE_ARM]
    reduced = checkpoints[g47.REDUCED_ARM]
    assert any("credit_baselines" in key for key in reference["model_state"])
    assert all("credit_baselines" not in key for key in reduced["model_state"])
    assert reduced["baseline_true_state_input_schema"] == []
    assert reduced["baseline_output_schema"] == []
    assert (
        g47.canonical_actor_projection(reference)["actor_state_digest"]
        == g47.canonical_actor_projection(reduced)["actor_state_digest"]
    )
    payload = io.BytesIO()
    torch.save(checkpoints, payload)
    payload.seek(0)
    reloaded = torch.load(payload, map_location="cpu", weights_only=False)
    assert g47.validate_checkpoint_pair(reloaded)

    extra_baseline = copy.deepcopy(checkpoints)
    extra_baseline[g47.REDUCED_ARM]["model_state"][
        "credit_baselines.synthetic"
    ] = torch.zeros(1)
    extra_baseline[g47.REDUCED_ARM]["model_state_digest"] = g47._state_digest(
        extra_baseline[g47.REDUCED_ARM]["model_state"]
    )
    assert not g47.validate_checkpoint_pair(extra_baseline)

    missing_actor = copy.deepcopy(checkpoints)
    missing_key = next(iter(missing_actor[g47.REDUCED_ARM]["model_state"]))
    del missing_actor[g47.REDUCED_ARM]["model_state"][missing_key]
    missing_actor[g47.REDUCED_ARM]["model_state_digest"] = g47._state_digest(
        missing_actor[g47.REDUCED_ARM]["model_state"]
    )
    assert not g47.validate_checkpoint_pair(missing_actor)

    ordinal_remap = copy.deepcopy(checkpoints)
    optimizer = ordinal_remap[g47.REDUCED_ARM]["optimizer_state_by_parameter"]
    first = next(iter(optimizer))
    optimizer[f"ordinal.0.{first}"] = optimizer.pop(first)
    ordinal_remap[g47.REDUCED_ARM]["optimizer_state_digest"] = (
        g47._optimizer_state_digest(optimizer)
    )
    assert not g47.validate_checkpoint_pair(ordinal_remap)
