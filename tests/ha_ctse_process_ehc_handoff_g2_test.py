from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path

import pytest
import torch

from ha_ctse_process.ehc_handoff_g2 import (
    ARM_NAMES,
    HIDDEN_WIDTH,
    PPO_PASSES,
    HandoffPolicy,
    assert_replay_equal,
    collect_rollout,
    initialize_matched_arms,
    load_checkpoint,
    optimize_rollout,
    replay_rollout,
    save_checkpoint,
    validate_rollout,
)


def _flat_parameters(model: torch.nn.Module) -> torch.Tensor:
    return torch.cat([parameter.detach().reshape(-1) for parameter in model.parameters()])


def test_arms_have_matched_initialization_and_exact_logit_links() -> None:
    states = initialize_matched_arms(replicate=0)
    assert tuple(states) == ARM_NAMES
    reference = states[ARM_NAMES[0]].model.state_dict()
    for state in states.values():
        assert state.model.state_dict().keys() == reference.keys()
        for name, value in state.model.state_dict().items():
            assert torch.equal(value, reference[name]), name

    model = HandoffPolicy()
    member = torch.randn(2, HIDDEN_WIDTH)
    team = torch.randn(2, HIDDEN_WIDTH)
    mark = torch.tensor([-1.0, 1.0])
    base = model.primitive_logits("DUM", member, team, mark)
    assert torch.equal(base, model.primitive_head(member))
    assert torch.allclose(
        model.primitive_logits("TEAM_REC", member, team, mark) - base,
        model.team_treatment(team),
    )
    expected_mark = model.mark_treatment(mark.unsqueeze(-1) * model.mark_embedding)
    assert torch.allclose(
        model.primitive_logits("EHC", member, team, mark) - base,
        expected_mark,
    )


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_collection_replay_ppo_and_gradient_paths_are_finite(arm: str) -> None:
    state = initialize_matched_arms(replicate=1)[arm]
    batch = collect_rollout(state, environments=2, horizon=24, update_index=0)
    validate_rollout(batch, arm=arm)
    replay = replay_rollout(state.model, arm, batch)
    errors = assert_replay_equal(batch, replay)
    assert max(errors.values()) <= 1e-6
    assert batch.create_mask.sum().item() >= 2
    assert batch.dones.sum().item() >= 2
    assert batch.episode_records

    before = _flat_parameters(state.model)
    report = optimize_rollout(state, batch)
    after = _flat_parameters(state.model)
    assert report["optimizer_steps"] == PPO_PASSES
    assert math.isfinite(report["loss"])
    assert not torch.equal(before, after)

    team_change = float(report["team_treatment_gradient_norm"])
    mark_change = float(report["mark_treatment_gradient_norm"])
    if arm == "TEAM_REC":
        assert team_change > 0
        assert mark_change == 0
    elif arm == "EHC":
        assert team_change == 0
        assert mark_change > 0
    else:
        assert team_change == mark_change == 0


def test_replay_corruption_and_checkpoint_identity_fail_closed(tmp_path: Path) -> None:
    state = initialize_matched_arms(replicate=2)["EHC"]
    batch = collect_rollout(state, environments=2, horizon=16, update_index=0)
    corrupted = deepcopy(batch)
    corrupted.old_primitive_logp[0, 0] += 0.1
    with pytest.raises(ValueError, match="primitive replay"):
        assert_replay_equal(corrupted, replay_rollout(state.model, "EHC", corrupted))

    checkpoint = tmp_path / "ehc.pt"
    save_checkpoint(
        checkpoint,
        state,
        source_commit="b" * 40,
        update=1,
    )
    loaded = load_checkpoint(
        checkpoint,
        expected_source_commit="b" * 40,
        expected_arm="EHC",
        expected_replicate=2,
    )
    for name, value in state.model.state_dict().items():
        assert torch.equal(value, loaded.model.state_dict()[name])
    with pytest.raises(ValueError, match="source commit"):
        load_checkpoint(
            checkpoint,
            expected_source_commit="c" * 40,
            expected_arm="EHC",
            expected_replicate=2,
        )
