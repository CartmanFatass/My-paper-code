"""Registered RECCT-A1 five-transition directed-edge binding audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import ha_ctse_process.continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process.anchored_residual_g19 import AnchoredRosterTrajectory
from experiments.candidates.recct_lite import directed_edge_masked_update as a1


INITIALIZATION_SEED = 20_260_809
LEARNER_INSTANCE = "recct-a1-g40-learner-instance-0"
POLICY_GENERATION = "g40-recct-a1-generation-0"
ROSTER_EPOCH = 1


def _sealed_n3_pretreatment_batch(model: g40.G40NativeSixPolicy) -> AnchoredRosterTrajectory:
    """One fixed zero-environment learner batch; no policy/environment call."""

    time, batch, members = 2, 2, 3
    observation_rows = torch.tensor(
        [
            [
                [[-0.80, 0.10, 0.30, -0.20, 0.40, 0.60],
                 [0.25, -0.65, 0.45, 0.15, -0.35, 0.75],
                 [0.70, 0.35, -0.55, 0.50, 0.05, -0.45]],
                [[-0.45, 0.55, 0.20, 0.65, -0.10, 0.30],
                 [0.60, -0.15, -0.70, 0.25, 0.80, -0.05],
                 [0.05, 0.85, -0.25, -0.60, 0.35, 0.40]],
            ],
            [
                [[-0.30, 0.75, -0.10, 0.20, 0.55, -0.65],
                 [0.85, -0.40, 0.15, -0.55, 0.10, 0.45],
                 [0.20, 0.05, 0.90, 0.35, -0.75, -0.15]],
                [[-0.70, -0.05, 0.65, 0.45, 0.20, -0.30],
                 [0.40, 0.95, -0.35, -0.10, 0.60, 0.25],
                 [0.75, -0.25, 0.05, 0.80, -0.40, 0.10]],
            ],
        ],
        dtype=torch.float32,
    )
    if observation_rows.shape != (time, batch, members, model.policy.observation_dim):
        raise RuntimeError("registered RECCT-A1 observation fixture left G40 schema")
    action_dim = model.policy.action_dim
    pre_tanh = torch.tensor(
        [
            [[[-0.35, 0.10], [0.20, -0.45], [0.55, 0.30]],
             [[0.15, 0.50], [-0.60, 0.25], [0.40, -0.20]]],
            [[[0.45, -0.15], [-0.25, 0.65], [0.10, -0.55]],
             [[-0.50, 0.35], [0.70, -0.05], [-0.10, 0.60]]],
        ],
        dtype=torch.float32,
    )
    if pre_tanh.shape[-1] != action_dim:
        raise RuntimeError("registered RECCT-A1 action fixture left G40 schema")
    rewards = torch.tensor(
        [[1.0, -0.5], [-0.25, 1.25]], dtype=torch.float32
    )
    active = torch.ones((time, batch, members), dtype=torch.bool)
    hidden = torch.zeros(
        (time, batch, members, model.hidden_dim), dtype=torch.float32
    )
    actions = torch.tanh(pre_tanh)
    return AnchoredRosterTrajectory(
        observations=observation_rows,
        active_mask=active,
        critic_states=torch.tensor(
            [
                [[0.10, -0.20, 0.30, -0.40, 0.50, -0.60],
                 [-0.15, 0.25, -0.35, 0.45, -0.55, 0.65]],
                [[0.20, 0.30, -0.40, -0.50, 0.60, 0.70],
                 [-0.25, -0.35, 0.45, 0.55, -0.65, -0.75]],
            ],
            dtype=torch.float32,
        ),
        actions=actions,
        pre_tanh_actions=pre_tanh,
        old_log_probs=torch.zeros((time, batch, members), dtype=torch.float32),
        old_values=torch.zeros((time, batch), dtype=torch.float32),
        old_immediate_baselines=torch.zeros((time, batch), dtype=torch.float32),
        old_successor_baselines=torch.zeros((time, batch), dtype=torch.float32),
        rewards=rewards,
        hidden_before=hidden,
        hidden_after=hidden.clone(),
        prefix_action_sums=torch.zeros(
            (time, batch, members, action_dim), dtype=torch.float32
        ),
        outcomes=(),
        ledgers=(),
        terminal_hidden_reset_mask=torch.zeros(
            (time, batch, members), dtype=torch.bool
        ),
    )


def build_registered_capsule() -> tuple[
    a1.DirectedEdgeMaskedLearner,
    a1.SealedLearnerCapsule,
    tuple[a1.OpaqueDirectedHandle, a1.OpaqueDirectedHandle],
]:
    model = g40.make_model(3, initialization_seed=INITIALIZATION_SEED)
    optimizer = torch.optim.Adam(
        model.actor_credit_parameters(), lr=g40.LEARNING_RATE
    )
    trajectory = _sealed_n3_pretreatment_batch(model)
    config = a1.LearnerConfig(
        learning_rate=float(optimizer.param_groups[0]["lr"]),
        betas=tuple(float(row) for row in optimizer.param_groups[0]["betas"]),
        eps=float(optimizer.param_groups[0]["eps"]),
        weight_decay=float(optimizer.param_groups[0]["weight_decay"]),
        amsgrad=bool(optimizer.param_groups[0]["amsgrad"]),
        maximize=bool(optimizer.param_groups[0].get("maximize", False)),
    )
    learner = a1.DirectedEdgeMaskedLearner(LEARNER_INSTANCE)
    ancestry = a1.RosterEpochAncestry(
        roster_epoch=ROSTER_EPOCH,
        policy_generation=POLICY_GENERATION,
        learner_checkpoint_digest=a1.model_digest(model),
        optimizer_checkpoint_digest=a1.optimizer_digest(model, optimizer),
        pretreatment_batch_digest=a1.trajectory_digest(trajectory),
        parent_epoch_digest=hashlib.sha256(
            b"recct-a1-pretreatment-parent-epoch-v1"
        ).hexdigest(),
    )
    disabled = {
        name: a1.DisabledUpdateState(name)
        for name in (
            "scheduler",
            "scaler",
            "gradient_clipping",
            "gradient_accumulation",
        )
    }
    capsule = learner.seal_capsule(
        model=model,
        optimizer=optimizer,
        trajectory=trajectory,
        roster=(
            a1.AgentInstance("agent-instance-a", 0),
            a1.AgentInstance("agent-instance-b", 1),
            a1.AgentInstance("agent-instance-c", 2),
        ),
        ancestry=ancestry,
        frozen_selection=a1.FrozenSelectionState(
            support=(True, True),
            rho=(0.6, 0.6),
            predictor_digest=hashlib.sha256(
                b"recct-a1-frozen-pretreatment-predictor-v1"
            ).hexdigest(),
            selected_mask="10",
        ),
        rng_plan=a1.SiteKeyedRNGPlan(
            (("learner/replay", 0), ("optimizer/adam", 0))
        ),
        learner_config=config,
        scheduler_state=disabled["scheduler"],
        scaler_state=disabled["scaler"],
        clipping_state=disabled["gradient_clipping"],
        accumulation_state=disabled["gradient_accumulation"],
    )
    handles = (
        learner.handle(capsule, "agent-instance-a", "agent-instance-b"),
        learner.handle(capsule, "agent-instance-b", "agent-instance-a"),
    )
    return learner, capsule, handles


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the registered RECCT-A1 four-shadow plus fresh-commit audit."
        )
    )
    parser.parse_args(argv)
    learner, capsule, handles = build_registered_capsule()
    result = a1.run_five_transition_audit(learner, capsule, handles)
    print(json.dumps(result.to_dict(), separators=(",", ":"), sort_keys=True))
    return 0 if result.branch == a1.A1_DIRECTED_EDGE_BINDING_PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
