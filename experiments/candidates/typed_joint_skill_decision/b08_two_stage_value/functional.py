"""Independent B=1 saved-state reconstruction and FP64 forward-error check.

Neither reader calls Scorer.forward. FP32 uses its bound flatten/mean primitives;
FP64 independently propagates absolute errors through each mathematical map.
The bounds cover FP32 roundoff, including dot/bias, sum/division, residual and
selected-member pooling. ReLU is 1-Lipschitz. Bounds never define score ties.
"""
import numpy as np
import torch
from torch.nn import functional as F

from .features import SHAPES
from .model import validate_inputs, validate_state


def menu_tensors(menu):
    """Copy a single padded numpy/torch menu into contiguous B=1 tensors."""
    if set(menu) != {*SHAPES, "valid"}:
        raise ValueError("B08 one-menu keys differ")
    result = {}
    for key, shape in {**SHAPES, "valid": (8,)}.items():
        value = menu[key]
        expected = torch.bool if key == "valid" else torch.float32
        if isinstance(value, torch.Tensor):
            if value.dtype != expected or value.device.type != "cpu" or tuple(value.shape) != shape:
                raise ValueError(f"invalid one-menu tensor: {key}")
            result[key] = value.detach().clone().contiguous().unsqueeze(0)
        else:
            array = np.asarray(value)
            if array.shape != shape or array.dtype != (np.bool_ if key == "valid" else np.float32):
                raise ValueError(f"invalid one-menu array: {key}")
            result[key] = torch.from_numpy(np.array(array, copy=True, order="C")).unsqueeze(0)
    validate_inputs(result)
    return result


def reconstruct(state, menu):
    """All eight FP32 scores, including padding, with no deployed-module call."""
    validate_state(state)
    x = menu_tensors(menu)

    def encode(value, name, count=2):
        shape = value.shape[:-1]
        value = value.reshape(-1, value.shape[-1])
        for i in range(count):
            prefix = f"{name}.{i}"
            value = F.linear(value, state[prefix + ".weight"], state.get(prefix + ".bias"))
            if (name, i) != ("readout", 2):
                value = F.relu(value)
        return value.reshape(*shape, value.shape[-1])

    with torch.no_grad():
        u = encode(x["U"], "u")
        y = encode(x["Y"], "y")
        user = encode(x["E_UY"], "uy").mean(dim=3)
        peer = encode(x["E_UU"], "uu").mean(dim=3)
        updated = F.relu(u + encode(torch.cat((u, user, peer), dim=-1), "update"))
        chosen = (updated * x["U"][..., 19:20]).sum(dim=2)
        readout = torch.cat((updated.mean(dim=2), chosen, y.mean(dim=2), x["S"]), dim=-1)
        return encode(readout, "readout", 3).squeeze(-1)[0].numpy().copy()


def gamma(n):
    """Standard FP32 gamma_n, unit roundoff 2**-24."""
    product = int(n) * 2. ** -24
    if not 0 <= product < 1:
        raise ValueError("invalid rounding-operation count")
    return product / (1. - product)


def reference(state, menu):
    """Return (FP64 mathematical scores[8], data-dependent FP32 bounds[8]).

    A bound node is (FP64 value, nonnegative absolute error). Dot propagation
    adds abs(W)*input_error and gamma_(n+1)*(abs(W)*abs(input)+abs(bias)
    + propagated_error). Means bound n-term summation and division by n using
    gamma_(n+1). This deliberately covers more operations than optimized kernels.
    Inputs and weights are exact FP32 numbers promoted to FP64. A conservative
    FP64 computation guard is included in every operation's gamma factor.
    """
    validate_state(state)
    tensors = menu_tensors(menu)
    x = {k: (v.double(), torch.zeros_like(v, dtype=torch.float64))
         for k, v in tensors.items() if k != "valid"}

    def rounding(n):
        # Accounts for reference/bound arithmetic too, rather than silently
        # treating computed FP64 dot sums as exact real numbers.
        double_product = (2 * n + 8) * 2. ** -53
        return gamma(n) + 4. * double_product / (1. - double_product)

    def affine(node, prefix):
        value, error = node
        shape = value.shape[:-1]
        value = value.reshape(-1, value.shape[-1])
        error = error.reshape_as(value)
        weight = state[prefix + ".weight"].double()
        bias = state.get(prefix + ".bias")
        bias = bias.double() if bias is not None else None
        result = F.linear(value, weight, bias)
        inherited = F.linear(error, weight.abs())
        magnitude = F.linear(value.abs(), weight.abs(), None if bias is None else bias.abs())
        # Absolute underflow term also covers gradual-underflow FP32 kernels.
        underflow = (2 * value.shape[-1] + 2) * 2. ** -150
        bound = inherited + rounding(value.shape[-1] + 1) * (magnitude + inherited) + underflow
        return result.reshape(*shape, result.shape[-1]), bound.reshape(*shape, bound.shape[-1])

    def relu(node):
        return F.relu(node[0]), node[1]

    def encode(node, name, layers=2):
        for i in range(layers):
            node = affine(node, f"{name}.{i}")
            if (name, i) != ("readout", 2):
                node = relu(node)
        return node

    def mean(node, axis):
        value, error = node
        inherited = error.mean(dim=axis)
        return value.mean(dim=axis), inherited + rounding(value.shape[axis] + 1) * (
            value.abs().mean(dim=axis) + inherited) + (value.shape[axis] + 1) * 2. ** -150

    def concatenate(nodes):
        return tuple(torch.cat([node[i] for node in nodes], dim=-1) for i in range(2))

    def add(left, right):
        inherited = left[1] + right[1]
        return left[0] + right[0], inherited + rounding(1) * (left[0].abs() + right[0].abs() + inherited) + 2. ** -150

    with torch.no_grad():
        u = encode(x["U"], "u")
        y = encode(x["Y"], "y")
        uy = mean(encode(x["E_UY"], "uy"), 3)
        uu = mean(encode(x["E_UU"], "uu"), 3)
        updated = relu(add(u, encode(concatenate((u, uy, uu)), "update")))
        selector = x["U"][0][..., 19:20]
        # This multiplication is exact only for lawful zero/one indicators.
        if not ((selector == 0) | (selector == 1)).all():
            raise ValueError("selected-member indicators must be zero/one")
        selected_values, selected_errors = updated[0] * selector, updated[1] * selector
        inherited = selected_errors.sum(dim=2)
        selected = (selected_values.sum(dim=2), inherited + rounding(8) * (
            selected_values.abs().sum(dim=2) + inherited) + 8 * 2. ** -150)
        result, bounds = encode(concatenate((mean(updated, 2), selected, mean(y, 2), x["S"])), "readout", 3)
        result, bounds = result[0, :, 0].numpy().copy(), bounds[0, :, 0].numpy().copy()
    if not np.isfinite(result).all() or not np.isfinite(bounds).all() or np.any(bounds < 0):
        raise FloatingPointError("nonfinite FP64 reference/error bounds")
    return result, bounds


def verify(state, menu, deployed_scores):
    """Check all padded FP32 bits and FP64 bounds; failure stops the reader.

    Shortlist reconstruction belongs to the planner's unchanged stationary tie
    rule. Equality of every finite score bit preserves that rule exactly.
    """
    deployed = np.asarray(deployed_scores)
    if deployed.shape != (8,) or deployed.dtype != np.float32 or not np.isfinite(deployed).all():
        raise ValueError("finite deployed FP32[8] required")
    rebuilt = reconstruct(state, menu)
    if not np.array_equal(deployed.view(np.uint32), rebuilt.view(np.uint32)):
        raise ArithmeticError("functional FP32 score bits differ")
    mathematical, bounds = reference(state, menu)
    difference = np.abs(rebuilt.astype(np.float64) - mathematical)
    if np.any(difference > bounds):
        raise ArithmeticError("FP32 score exceeds propagated forward-error bound")
    return {"fp32_bits_equal": True, "within_bounds": True,
            "prediction_bits": rebuilt.view(np.uint32).tolist(),
            "reference_fp64": mathematical.tolist(), "absolute_error": difference.tolist(),
            "forward_error_bound": bounds.tolist(),
            "valid": np.asarray(menu["valid"]).tolist()}
