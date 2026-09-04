"""FP32 Bellman-basis learners with optional paired 64x64 residuals."""

from __future__ import annotations

from typing import Any

from .contract import ARM_IDS, FLEX_ARMS
from .rng import glorot


def _torch():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("UCOPE scout training requires PyTorch") from exc
    return torch


def x_features(*, phase_tail: bool, action_probe: bool, period: int, belief: float, cost: float, linked: bool, reliability: float) -> tuple[float, ...]:
    if type(phase_tail) is not bool or type(action_probe) is not bool or type(period) is not int:
        raise ValueError("feature flags/period require exact types")
    if not 0 <= period <= 9 or action_probe and period != 0 or phase_tail and action_probe:
        raise ValueError("invalid stage/action feature combination")
    k = period / 9.0
    return (1.0, float(phase_tail), float(action_probe), k, float(belief), float(cost), float(linked), float(reliability), float(linked) * float(reliability))


def tail_basis(*, belief: float, period: int) -> tuple[float, ...]:
    k = period / 9.0
    return (1.0, belief, k, belief * k, k * k)


def root_basis(*, action_probe: bool, period: int, cost: float, linked: bool, reliability: float) -> tuple[float, ...]:
    a = float(action_probe)
    k = period / 9.0
    return (1.0, (1.0 - a) * k, (1.0 - a) * k * k, a, a * cost, a * float(linked), a * float(linked) * reliability)


def tensors_for_record(record: Any, *, stage: str, action_probe: bool, period: int, belief: float):
    torch = _torch()
    x = x_features(
        phase_tail=stage == "tail",
        action_probe=action_probe,
        period=period,
        belief=belief,
        cost=float(record.total_cost),
        linked=record.link == "LINKED",
        reliability=float(record.reliability),
    )
    z = tail_basis(belief=belief, period=period) if stage == "tail" else root_basis(action_probe=action_probe, period=period, cost=float(record.total_cost), linked=record.link == "LINKED", reliability=float(record.reliability))
    return torch.tensor(x, dtype=torch.float32), torch.tensor(z, dtype=torch.float32)


class BellmanScorer:
    """Factory namespace; returns an nn.Module without importing torch at module import."""

    @staticmethod
    def build(stage: str, flexible: bool, init_key: str):
        if stage not in {"root", "tail"}:
            raise ValueError("scorer stage must be root or tail")
        torch = _torch()
        nn = torch.nn
        basis_dim = 7 if stage == "root" else 5

        class Module(nn.Module):
            def __init__(self):
                super().__init__()
                self.beta = nn.Parameter(torch.empty(basis_dim, dtype=torch.float32))
                self.residual = None
                if flexible:
                    self.residual = nn.Sequential(
                        nn.Linear(9, 64, dtype=torch.float32),
                        nn.ReLU(),
                        nn.Linear(64, 64, dtype=torch.float32),
                        nn.ReLU(),
                        nn.Linear(64, 1, dtype=torch.float32),
                    )
                with torch.no_grad():
                    beta_values = glorot(1, basis_dim, "bellman", init_key, stage, namespace="flex-init" if flexible else "bc-init")[0]
                    self.beta.copy_(torch.tensor(beta_values, dtype=torch.float32))
                    if self.residual is not None:
                        linear_index = 0
                        for layer in self.residual:
                            if isinstance(layer, nn.Linear):
                                values = glorot(layer.out_features, layer.in_features, "residual", init_key, stage, linear_index, namespace="flex-init")
                                layer.weight.copy_(torch.tensor(values, dtype=torch.float32))
                                layer.bias.zero_()
                                linear_index += 1

            def forward(self, x, z):
                if x.dtype != torch.float32 or z.dtype != torch.float32 or x.shape[-1] != 9 or z.shape[-1] != basis_dim:
                    raise ValueError("scorer requires FP32 frozen feature dimensions")
                value = (z * self.beta).sum(dim=-1)
                if self.residual is not None:
                    value = value + self.residual(x).squeeze(-1)
                return value

        with torch.random.fork_rng(devices=[]):
            return Module()


def build_arm(arm_id: str, seed_id: str, fold_id: int):
    if arm_id not in ARM_IDS or fold_id not in (0, 1):
        raise ValueError("unknown arm/fold")
    flexible = arm_id in FLEX_ARMS
    # Both FLEX arms deliberately share this key, making initial tensors exactly paired.
    init_key = f"{seed_id}|fold-{fold_id}|{'FLEX' if flexible else 'BC'}"
    root = BellmanScorer.build("root", flexible, init_key)
    tail = BellmanScorer.build("tail", flexible, init_key)
    validate_arm(root, tail, flexible=flexible)
    return root, tail


def validate_arm(root, tail, *, flexible: bool) -> None:
    torch = _torch()
    for stage, scorer, dim in (("root", root, 7), ("tail", tail, 5)):
        parameters = dict(scorer.named_parameters())
        if "beta" not in parameters or tuple(parameters["beta"].shape) != (dim,):
            raise ValueError(f"{stage} Bellman basis drift")
        residual_names = [name for name in parameters if name.startswith("residual.")]
        if bool(residual_names) != flexible:
            raise ValueError("BC residual prohibition or FLEX residual requirement violated")
        if any(parameter.dtype != torch.float32 or not torch.isfinite(parameter).all().item() for parameter in parameters.values()):
            raise ValueError("model parameters must be finite FP32")


def optimizer_for(scorer, learning_rate: float = 3e-4):
    """AdamW at the caller's declared exposure.

    The default is the frozen B1/ASSESS learning rate; the exposure-ladder object passes its
    own declared rung rate. Every other optimizer literal is unchanged.
    """
    torch = _torch()
    if type(learning_rate) is not float or not 0.0 < learning_rate < 1.0:
        raise ValueError("learning rate must be a positive float below one")
    return torch.optim.AdamW(scorer.parameters(), lr=learning_rate, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0)
