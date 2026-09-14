"""The selected two-channel FP64 rule; no rollout, RNG or baseline ownership."""
import torch


def unit_direction(vector):
    """Scale-safe whole-vector L2 direction, with represented zero kept zero."""
    if not bool(torch.isfinite(vector).all()):
        raise RuntimeError("nonfinite score-channel vector")
    scale = vector.abs().max()
    if bool(scale == 0):
        return torch.zeros_like(vector)
    scaled = vector / scale
    return scaled / torch.sqrt(scaled.square().sum())


def step_from_losses(parameters, manager_loss, claim_loss, progress=None):
    """Differentiate the same graph twice, then apply exactly one combined step."""
    parameters = tuple(parameters)
    progress = {} if progress is None else progress
    if sum(p.numel() for p in parameters) != 26161:
        raise ValueError("equal-unit update requires the complete 26161-scalar inventory")
    if any(p.dtype != torch.float64 or p.device.type != "cpu" for p in parameters):
        raise ValueError("equal-unit update requires CPU FP64 parameters")
    if not all(bool(torch.isfinite(loss)) for loss in (manager_loss, claim_loss)):
        raise RuntimeError("nonfinite score-channel loss")
    progress["derivative_attempts"] = 1
    manager = torch.autograd.grad(manager_loss, parameters, retain_graph=True, allow_unused=True)
    progress["derivatives_completed"] = 1
    progress["derivative_attempts"] = 2
    claim = torch.autograd.grad(claim_loss, parameters, allow_unused=True)
    progress["derivatives_completed"] = 2

    def flatten(gradients):
        return torch.cat([(torch.zeros_like(p) if g is None else g.detach()).reshape(-1)
                          for p, g in zip(parameters, gradients)])

    manager_vector, claim_vector = flatten(manager), flatten(claim)
    direction = unit_direction(manager_vector) + unit_direction(claim_vector)
    nonzero = bool(torch.count_nonzero(direction))
    delta = -.02 * unit_direction(direction)
    before = torch.cat([p.detach().reshape(-1) for p in parameters])
    offset = 0
    progress["parameter_step_attempts"] = 1
    with torch.no_grad():
        if nonzero:
            for parameter in parameters:
                count = parameter.numel()
                parameter.add_(delta[offset:offset + count].reshape_as(parameter))
                offset += count
    progress["parameter_steps_completed"] = 1
    progress["nonzero_steps"] = int(nonzero)
    after = torch.cat([p.detach().reshape(-1) for p in parameters])
    return {
        "manager_loss": float(manager_loss.detach()), "claim_loss": float(claim_loss.detach()),
        "manager_max_abs_gradient": float(manager_vector.abs().max()),
        "claim_max_abs_gradient": float(claim_vector.abs().max()),
        "combined_unit_direction_norm": float(torch.linalg.vector_norm(direction)),
        "score_channel_derivative_traversals": 2,
        "nonzero": nonzero,
        "parameter_delta_norm": float(torch.linalg.vector_norm(delta)),
        "measured_parameter_delta_norm": float(torch.linalg.vector_norm(after - before)),
    }
