"""One shared two-scorer FP32 BELIEF model and the frozen feature map."""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping
import math

from .contract import FEATURE_NAMES, as_fraction, validate_context
from .oracle import posterior_short
from .rng import glorot_values


def feature_vector(
    context: Mapping[str, Any],
    *,
    belief_short: Fraction | float = Fraction(1, 2),
    action_is_probe: bool,
    period: int,
) -> tuple[float, ...]:
    validate_context(context)
    link = context.get("link")
    if link not in ("LINKED", "SEVERED"):
        raise ValueError("unknown linkage")
    p = as_fraction(context["reliability"])
    cost = as_fraction(context["total_cost"])
    if type(action_is_probe) is not bool:
        raise ValueError("action_is_probe must be an exact bool")
    if type(period) is not int:
        raise ValueError("period must be an exact integer")
    if period < 0 or period > 9:
        raise ValueError("period feature outside [0,9]")
    if action_is_probe and period != 0:
        raise ValueError("PROBE feature must have zero period coordinates")
    if not action_is_probe and period == 0:
        raise ValueError("COMMIT feature requires a period in 1..9")
    if isinstance(belief_short, bool):
        raise ValueError("belief must be numeric, not bool")
    belief = float(belief_short)
    if not math.isfinite(belief) or not 0.0 <= belief <= 1.0:
        raise ValueError("belief outside [0,1]")
    scaled = period / 9.0
    values = (
        1.0 if link == "LINKED" else 0.0,
        float(p),
        -0.03,
        -float(cost - Fraction(3, 100)),
        belief,
        1.0 - belief,
        1.0 if action_is_probe else 0.0,
        scaled,
        scaled * scaled,
    )
    if len(values) != len(FEATURE_NAMES):
        raise AssertionError("feature shape drift")
    return values


def displayed_belief(link: str, reliability: Fraction, displayed_short_count: int) -> Fraction:
    if link == "SEVERED":
        return Fraction(1, 2)
    if link != "LINKED":
        raise ValueError("unknown linkage")
    if not isinstance(displayed_short_count, int) or isinstance(displayed_short_count, bool) or not 0 <= displayed_short_count <= 6:
        raise ValueError("displayed count outside 0..6")
    return posterior_short(reliability, displayed_short_count)


def _torch():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - dependency error is explicit at use site
        raise RuntimeError("training requires PyTorch") from exc
    return torch


def build_shared_model(seed_slot: str):
    """Construct the sole shared root/tail model with counter-keyed initialization."""
    from .contract import SEED_SLOTS
    if seed_slot not in SEED_SLOTS:
        raise ValueError("unknown frozen seed slot")
    torch = _torch()
    nn = torch.nn

    class Scorer(nn.Module):
        def __init__(self, scorer_name: str):
            super().__init__()
            self.layers = nn.Sequential(nn.Linear(9, 64, dtype=torch.float32), nn.ReLU(), nn.Linear(64, 64, dtype=torch.float32), nn.ReLU(), nn.Linear(64, 1, dtype=torch.float32))
            linear_index = 0
            with torch.no_grad():
                for module in self.layers:
                    if isinstance(module, nn.Linear):
                        values = glorot_values(module.out_features, module.in_features, seed_slot, scorer_name, linear_index)
                        module.weight.copy_(torch.tensor(values, dtype=torch.float32))
                        module.bias.zero_()
                        linear_index += 1

        def forward(self, features):
            if features.dtype != torch.float32 or features.shape[-1] != 9:
                raise ValueError("scorer requires FP32 [...,9] features")
            return self.layers(features).squeeze(-1)

    class SharedBeliefModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.root = Scorer("root")
            self.tail = Scorer("tail")

        def score_root(self, features):
            return self.root(features)

        def score_tail(self, features):
            return self.tail(features)

    # nn.Linear performs default random initialization before our counter-keyed overwrite.
    # Forking the CPU RNG makes even that discarded work externally side-effect free.
    with torch.random.fork_rng(devices=[]):
        model = SharedBeliefModel()
    if any(parameter.dtype != torch.float32 for parameter in model.parameters()):
        raise AssertionError("model must be entirely FP32")
    return model


build_model = build_shared_model


def validate_shared_model(model: Any) -> None:
    expected = {}
    for scorer in ("root", "tail"):
        expected.update({f"{scorer}.layers.0.weight": (64,9), f"{scorer}.layers.0.bias": (64,), f"{scorer}.layers.2.weight": (64,64), f"{scorer}.layers.2.bias": (64,), f"{scorer}.layers.4.weight": (1,64), f"{scorer}.layers.4.bias": (1,)})
    parameters = dict(model.named_parameters())
    if set(parameters) != set(expected):
        raise ValueError("model parameter key inventory mismatch")
    torch = _torch()
    for name, parameter in parameters.items():
        if tuple(parameter.shape) != expected[name] or parameter.dtype != torch.float32 or not torch.isfinite(parameter).all().item():
            raise ValueError(f"invalid shared model parameter: {name}")
