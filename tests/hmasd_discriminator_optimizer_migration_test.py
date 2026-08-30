from __future__ import annotations

import copy

import pytest
import torch

from hmasd.agent import _split_legacy_discriminator_adam_state_dict


def _models() -> tuple[torch.nn.Module, torch.nn.Module]:
    torch.manual_seed(78123)
    return torch.nn.Linear(3, 2), torch.nn.Linear(4, 3)


def _losses(team: torch.nn.Module, individual: torch.nn.Module):
    team_input = torch.tensor(((0.2, -0.5, 0.7), (1.1, 0.3, -0.8)))
    individual_input = torch.tensor(
        ((0.1, 0.4, -0.2, 0.9), (-0.6, 0.8, 0.5, -0.3))
    )
    return team(team_input).square().sum(), individual(individual_input).square().sum()


def _legacy_step(optimizer, team, individual, mode: str) -> None:
    if mode == "fused":
        optimizer.zero_grad()
        team_loss, individual_loss = _losses(team, individual)
        (team_loss + individual_loss).backward()
        optimizer.step()
    else:
        for loss_index in range(2):
            optimizer.zero_grad()
            losses = _losses(team, individual)
            losses[loss_index].backward()
            optimizer.step()


def _split_step(team_optimizer, individual_optimizer, team, individual, mode: str) -> None:
    if mode == "fused":
        team_optimizer.zero_grad()
        individual_optimizer.zero_grad()
        team_loss, individual_loss = _losses(team, individual)
        (team_loss + individual_loss).backward()
        team_optimizer.step()
        individual_optimizer.step()
    else:
        team_optimizer.zero_grad()
        team_loss, _ = _losses(team, individual)
        team_loss.backward()
        team_optimizer.step()
        individual_optimizer.zero_grad()
        _, individual_loss = _losses(team, individual)
        individual_loss.backward()
        individual_optimizer.step()


@pytest.mark.parametrize("mode", ("fused", "sequential"))
def test_legacy_combined_adam_migrates_without_changing_next_update(mode: str) -> None:
    legacy_team, legacy_individual = _models()
    legacy_optimizer = torch.optim.Adam(
        tuple(legacy_team.parameters()) + tuple(legacy_individual.parameters()),
        lr=3e-4,
        weight_decay=1e-5,
    )
    _legacy_step(legacy_optimizer, legacy_team, legacy_individual, mode)

    split_team = copy.deepcopy(legacy_team)
    split_individual = copy.deepcopy(legacy_individual)
    team_optimizer = torch.optim.Adam(
        split_team.parameters(), lr=3e-4, weight_decay=1e-5
    )
    individual_optimizer = torch.optim.Adam(
        split_individual.parameters(), lr=3e-4, weight_decay=1e-5
    )
    team_state, individual_state = _split_legacy_discriminator_adam_state_dict(
        legacy_optimizer.state_dict(),
        split_team.parameters(),
        split_individual.parameters(),
    )
    team_optimizer.load_state_dict(team_state)
    individual_optimizer.load_state_dict(individual_state)

    _legacy_step(legacy_optimizer, legacy_team, legacy_individual, mode)
    _split_step(
        team_optimizer,
        individual_optimizer,
        split_team,
        split_individual,
        mode,
    )

    for expected, actual in zip(legacy_team.parameters(), split_team.parameters()):
        assert torch.equal(expected, actual)
    for expected, actual in zip(
        legacy_individual.parameters(), split_individual.parameters()
    ):
        assert torch.equal(expected, actual)
    assert team_optimizer.param_groups[0]["lr"] == legacy_optimizer.param_groups[0]["lr"]
    assert (
        individual_optimizer.param_groups[0]["lr"]
        == legacy_optimizer.param_groups[0]["lr"]
    )


def test_legacy_combined_adam_migration_rejects_state_shape_mismatch() -> None:
    team, individual = _models()
    optimizer = torch.optim.Adam(
        tuple(team.parameters()) + tuple(individual.parameters()), lr=3e-4
    )
    _legacy_step(optimizer, team, individual, "fused")
    state = optimizer.state_dict()
    first_id = state["param_groups"][0]["params"][0]
    state["state"][first_id]["exp_avg"] = torch.zeros(1)

    with pytest.raises(ValueError, match="shape does not match"):
        _split_legacy_discriminator_adam_state_dict(
            state, team.parameters(), individual.parameters()
        )


def test_split_schedulers_restore_the_legacy_schedule_without_lr_drift() -> None:
    legacy_team, legacy_individual = _models()
    legacy_optimizer = torch.optim.Adam(
        tuple(legacy_team.parameters()) + tuple(legacy_individual.parameters()),
        lr=3e-4,
    )
    legacy_scheduler = torch.optim.lr_scheduler.LinearLR(
        legacy_optimizer, start_factor=1.0, end_factor=0.2, total_iters=10
    )
    for _ in range(3):
        _legacy_step(
            legacy_optimizer, legacy_team, legacy_individual, mode="fused"
        )
        legacy_scheduler.step()

    split_team = copy.deepcopy(legacy_team)
    split_individual = copy.deepcopy(legacy_individual)
    team_optimizer = torch.optim.Adam(split_team.parameters(), lr=3e-4)
    individual_optimizer = torch.optim.Adam(split_individual.parameters(), lr=3e-4)
    team_scheduler = torch.optim.lr_scheduler.LinearLR(
        team_optimizer, start_factor=1.0, end_factor=0.2, total_iters=10
    )
    individual_scheduler = torch.optim.lr_scheduler.LinearLR(
        individual_optimizer, start_factor=1.0, end_factor=0.2, total_iters=10
    )
    team_state, individual_state = _split_legacy_discriminator_adam_state_dict(
        legacy_optimizer.state_dict(),
        split_team.parameters(),
        split_individual.parameters(),
    )
    team_optimizer.load_state_dict(team_state)
    individual_optimizer.load_state_dict(individual_state)
    team_scheduler.load_state_dict(legacy_scheduler.state_dict())
    individual_scheduler.load_state_dict(legacy_scheduler.state_dict())

    _legacy_step(legacy_optimizer, legacy_team, legacy_individual, mode="fused")
    _split_step(
        team_optimizer,
        individual_optimizer,
        split_team,
        split_individual,
        mode="fused",
    )
    legacy_scheduler.step()
    team_scheduler.step()
    individual_scheduler.step()

    assert team_optimizer.param_groups[0]["lr"] == legacy_optimizer.param_groups[0]["lr"]
    assert (
        individual_optimizer.param_groups[0]["lr"]
        == legacy_optimizer.param_groups[0]["lr"]
    )
