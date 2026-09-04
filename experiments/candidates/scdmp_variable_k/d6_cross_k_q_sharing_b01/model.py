"""Float32 D6/D8 learners and prospective exposure measurement."""

from __future__ import annotations

import math

import torch
from torch import nn

from .rng import xavier_values


SKILLS = (0, 10, 12)


def _fill(linear: nn.Linear, seed: int, address: tuple[object, ...]) -> None:
    values = xavier_values(
        seed, address, linear.weight.numel(), linear.in_features, linear.out_features,
    )
    with torch.no_grad():
        linear.weight.copy_(torch.tensor(values, dtype=torch.float32).reshape_as(linear.weight))
        linear.bias.zero_()


class ValueModel(nn.Module):
    def __init__(self, arm: str, seed: int) -> None:
        super().__init__()
        self.arm = arm
        self.encoder = nn.Sequential(
            nn.Linear(21, 96), nn.SiLU(), nn.Linear(96, 96), nn.SiLU(),
        )
        _fill(self.encoder[0], seed, ("common-encoder", 0))
        _fill(self.encoder[2], seed, ("common-encoder", 2))
        if arm == "D6":
            self.head = nn.Sequential(nn.Linear(97, 96), nn.SiLU(), nn.Linear(96, 1))
            _fill(self.head[0], seed, ("D6-head", 0))
            _fill(self.head[2], seed, ("D6-head", 2))
        elif arm == "D8":
            self.head_7 = nn.Sequential(nn.Linear(96, 96), nn.SiLU(), nn.Linear(96, 1))
            self.head_13 = nn.Sequential(nn.Linear(96, 96), nn.SiLU(), nn.Linear(96, 1))
            for k, head in ((7, self.head_7), (13, self.head_13)):
                _fill(head[0], seed, ("D8-head", k, 0))
                _fill(head[2], seed, ("D8-head", k, 2))
        else:
            raise ValueError("arm must be D6 or D8")

    def forward(self, observation: torch.Tensor, z: int, k: int) -> torch.Tensor:
        one_hot = torch.zeros((observation.shape[0], 3), dtype=torch.float32)
        one_hot[:, SKILLS.index(z)] = 1.0
        hidden = self.encoder(torch.cat((observation.to(torch.float32), one_hot), dim=1))
        if self.arm == "D6":
            k_norm = torch.full((hidden.shape[0], 1), (k - 7) / 6, dtype=torch.float32)
            return self.head(torch.cat((hidden, k_norm), dim=1))
        return (self.head_7 if k == 7 else self.head_13)(hidden)

    def score(self, observation: list[float], z: int, k: int) -> float:
        with torch.no_grad():
            row = torch.tensor(observation, dtype=torch.float32).reshape(1, 18)
            return float(self(row, z, k).item())

    def _selected(self, head: bool) -> dict[str, torch.Tensor]:
        result = {}
        for name, value in self.named_parameters():
            is_head = name.startswith("head")
            if is_head == head:
                result[name] = value.detach().clone()
        return result

    def initial_snapshots(self) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
        return self._selected(True), self._selected(False)


def displacement(
    model: ValueModel, initial: dict[str, torch.Tensor], *, head: bool,
) -> dict[str, object]:
    current = model._selected(head)
    if set(current) != set(initial):
        return {"valid": False}
    numerator = 0.0
    denominator = 0.0
    tensors = []
    for name in sorted(current):
        now = current[name].detach().to(torch.float64)
        before = initial[name].detach().to(torch.float64)
        if now.shape != before.shape:
            return {"valid": False}
        numerator += float(torch.sum((now - before) ** 2).item())
        denominator += float(torch.sum(before ** 2).item())
        tensors.append({
            "name": name, "shape": list(now.shape),
            "stored_dtype": str(current[name].dtype),
        })
    ratio = math.sqrt(numerator / denominator) if denominator > 0.0 else float("nan")
    return {
        "valid": math.isfinite(ratio), "tensors": tensors,
        "numerator": numerator, "denominator": denominator, "ratio": ratio,
    }


def optimizer(model: ValueModel) -> torch.optim.AdamW:
    return torch.optim.AdamW(
        model.parameters(), lr=3e-4, betas=(0.9, 0.999), eps=1e-8, weight_decay=1e-5,
    )


__all__ = ["SKILLS", "ValueModel", "displacement", "optimizer"]
