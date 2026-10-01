"""B09 frozen-trunk ego-only adaptation of B04's fixed group update."""
from collections.abc import Mapping
from numbers import Real

import torch
from torch import nn

from experiments.candidates.uav_fleet_adaptation.b04_native_development import learning as b04
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Critic

_COUNT_KEYS = ("head_optimizer_steps", "critic_optimizer_steps", "head_replay_rows",
               "critic_replay_rows", "density_identity_rows")


class ResponseHead(nn.Module):
    """One identical CPU FP32 deployment/replay row; no actor/trunk ownership."""
    def __init__(self):
        super().__init__()
        self.W = nn.Parameter(torch.zeros((27, 259), dtype=torch.float32, device="cpu"))
        self.b = nn.Parameter(torch.zeros(27, dtype=torch.float32, device="cpu"))
        if sum(p.numel() for p in self.parameters()) != 7020:
            raise AssertionError("response head parameter contract changed")

    def forward(self, context, base_logits):
        for value, shape in ((context, (259,)), (base_logits, (27,))):
            if (not isinstance(value, torch.Tensor) or value.shape != shape or
                    value.dtype != torch.float32 or value.device.type != "cpu"):
                raise ValueError("head accepts one CPU FP32 context/base-logit row")
            if not torch.isfinite(value).all():
                raise FloatingPointError("nonfinite response context")
        b04._finite_parameters(list(self.parameters()))
        # NumPy-backed rows and offsets within replay stacks can have different
        # alignment. Own contiguous row storage in both paths so CPU GEMV uses
        # the identical reduction program after the head is no longer zero.
        context = context.clone(memory_format=torch.contiguous_format)
        base_logits = base_logits.clone(memory_format=torch.contiguous_format)
        preactivation = torch.mv(self.W, context) + self.b
        if not torch.isfinite(preactivation).all():
            raise FloatingPointError("nonfinite head preactivation")
        result = base_logits + .5 * torch.tanh(preactivation)
        if not torch.isfinite(result).all():
            raise FloatingPointError("nonfinite head logits")
        return result


def fresh_critic(seed):
    return b04.fresh_critic(seed)


def make_optimizers(head, critic):
    if not isinstance(head, ResponseHead) or not isinstance(critic, Critic):
        raise ValueError("optimizers require ResponseHead and original Critic136")
    return b04.make_optimizers(head, critic)


def _rollout(episodes, horizon):
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0 or horizon % 4:
        raise ValueError("horizon must be a positive multiple of four")
    if len(episodes) != 2:
        raise ValueError("exactly two complete episodes required")
    clocks = horizon // 4
    contract = {
        "contexts": ((clocks, 259), torch.float32),
        "base_logits": ((clocks, 27), torch.float32),
        "logits": ((clocks, 27), torch.float32),
        "probabilities": ((clocks, 27), torch.float64),
        "action_index": ((clocks,), torch.int64),
        "logp": ((clocks,), torch.float64),
        "critic_features": ((clocks, 136), torch.float32),
        "values": ((clocks,), torch.float32),
        "macro_rewards": ((clocks,), torch.float64),
    }
    rows = {key: [] for key in contract}
    for episode in episodes:
        if not isinstance(episode, Mapping):
            raise ValueError("episode must be a mapping")
        for key, (shape, dtype) in contract.items():
            if key not in episode:
                raise ValueError(f"missing episode field {key}")
            value = torch.as_tensor(episode[key]).detach().clone()
            if value.shape != shape or value.dtype != dtype or value.device.type != "cpu":
                raise ValueError(f"{key} requires CPU {dtype} with shape {shape}")
            if not torch.isfinite(value).all():
                raise FloatingPointError(f"nonfinite {key}")
            rows[key].append(value)
    rollout = {key: torch.stack(values) for key, values in rows.items()}
    actions, probabilities = rollout["action_index"], rollout["probabilities"]
    if ((actions < 0) | (actions >= 27)).any():
        raise ValueError("action_index must be in [0,27)")
    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("invalid saved probabilities")
    if (probabilities.sum(-1) - 1).abs().max() > 1e-12:
        raise ValueError("saved probabilities must sum to one")
    chosen = probabilities.gather(-1, actions[..., None]).squeeze(-1)
    if (chosen <= 0).any():
        raise ValueError("chosen saved probability must be positive")
    if (chosen.log() - rollout["logp"]).abs().max() > 1e-10:
        raise ValueError("saved chosen probability and independent logp disagree")
    return rollout, chosen


_add = b04._add
_finite_parameters = b04._finite_parameters
_norm = b04._norm
_step_values = b04._step_values
_summary = b04._summary


def _update_group(head, critic, head_optimizer, critic_optimizer, episodes, counts, *, horizon=256, live_record=None):
    """Consume one fixed group, retaining counts for every completed paid operation.

    Saved tensors, targets and collected-value advantages stay detached and fixed
    throughout all four epochs. No sampling or additional diagnostic forward occurs.
    """
    result = {} if live_record is None else live_record
    if any(key in result for key in ("epochs", "initial_identity", "target_summary", "advantage_summary")):
        raise ValueError("live group diagnostics must start empty")
    result.update(status="INCOMPLETE", epochs=[])
    rollout, old_chosen = _rollout(episodes, horizon)
    for key in _COUNT_KEYS:
        value = counts.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, Real) or not torch.isfinite(torch.tensor(value)).item() or value < 0:
            raise ValueError(f"invalid count {key}")
    head_parameters, critic_parameters = list(head.parameters()), list(critic.parameters())
    if not head_parameters or not critic_parameters or set(head_parameters) & set(critic_parameters):
        raise ValueError("head and critic must have separate nonempty parameter sets")
    for optimizer, parameters in ((head_optimizer, head_parameters), (critic_optimizer, critic_parameters)):
        owned = [p for group in optimizer.param_groups for p in group["params"]]
        if len(owned) != len(parameters) or set(owned) != set(parameters):
            raise ValueError("optimizer must own exactly its model's parameters")
        _finite_parameters(parameters)
    initial_head = [p.detach().clone() for p in head_parameters]
    initial_critic = [p.detach().clone() for p in critic_parameters]
    rewards = rollout["macro_rewards"].float()
    targets = (rewards.flip(-1).cumsum(-1).flip(-1) / horizon).detach()
    raw_advantage = targets - rollout["values"]
    advantages = ((raw_advantage - raw_advantage.mean()) /
                  (raw_advantage.std(unbiased=False) + 1e-8)).detach()
    if not torch.isfinite(targets).all() or not torch.isfinite(advantages).all():
        raise FloatingPointError("nonfinite targets or advantages")
    head.train()
    critic.train()
    result.update(target_summary=_summary(targets), advantage_summary=_summary(advantages))
    records = result["epochs"]
    identity = None
    for epoch in range(4):
        _finite_parameters(head_parameters)
        outputs = []
        for context, base in zip(rollout["contexts"].reshape(-1, 259),
                                 rollout["base_logits"].reshape(-1, 27)):
            output = head(context, base)
            _add(counts, "head_replay_rows", 1)
            if output.shape != (27,) or output.dtype != torch.float32:
                raise ValueError("head replay must yield one FP32 27-logit row")
            outputs.append(output)
        logits = torch.stack(outputs).reshape(rollout["logits"].shape)
        if not torch.isfinite(logits).all():
            raise FloatingPointError("nonfinite head replay")
        z = logits.double()
        weights = (z - z.max(-1, keepdim=True).values).exp()
        probabilities = weights / weights.sum(-1, keepdim=True)
        chosen = probabilities.gather(-1, rollout["action_index"][..., None]).squeeze(-1)
        ratio = chosen / old_chosen
        logp = chosen.log()
        if not torch.isfinite(probabilities).all() or not torch.isfinite(ratio).all() or not torch.isfinite(logp).all():
            raise FloatingPointError("nonfinite replay density")
        if epoch == 0:
            _add(counts, "density_identity_rows", ratio.numel())
            identity = dict(logits_exact=bool(torch.equal(logits.detach(), rollout["logits"])),
                            max_probability_abs=float((probabilities.detach() - rollout["probabilities"]).abs().max()),
                            max_chosen_logp_abs=float((logp.detach() - rollout["logp"]).abs().max()),
                            max_ratio_from_one=float((ratio.detach() - 1).abs().max()), rows=ratio.numel())
            result["initial_identity"] = identity
            if (not identity["logits_exact"] or identity["max_probability_abs"] > 5e-14 or
                    identity["max_chosen_logp_abs"] > 1e-10 or identity["max_ratio_from_one"] > 1e-10):
                raise ValueError("initial replay density identity failed")
        advantage = advantages
        head_loss = -torch.minimum(ratio * advantage, ratio.clamp(.8, 1.2) * advantage).mean()
        if not torch.isfinite(head_loss):
            raise FloatingPointError("nonfinite head loss")
        record = dict(epoch=epoch, head_loss=float(head_loss.detach()),
                      head_step_completed=False, critic_step_completed=False,
                      ratio_min=float(ratio.detach().min()), ratio_max=float(ratio.detach().max()),
                      ratio_mean=float(ratio.detach().mean()),
                      clip_fraction=float(((ratio.detach() < .8) | (ratio.detach() > 1.2)).double().mean()),
                      old_logp_mean=float(rollout["logp"].mean()), new_logp_mean=float(logp.detach().mean()))
        records.append(record)
        head_optimizer.zero_grad(set_to_none=True)
        head_loss.backward()
        head_norm = torch.nn.utils.clip_grad_norm_(head_parameters, .5, error_if_nonfinite=True, foreach=False)
        record["head_grad_norm"] = float(head_norm)
        record["head_clipped_grad_norm"] = _norm([p.grad for p in head_parameters if p.grad is not None])
        head_optimizer.step()
        _add(counts, "head_optimizer_steps", 1)
        record.update(head_step_completed=True,
                      head_movement_l2=_norm([p - p0 for p, p0 in zip(head_parameters, initial_head)]),
                      head_optimizer_step_values=_step_values(head_optimizer, head_parameters))
        _finite_parameters(head_parameters)

        _finite_parameters(critic_parameters)
        predicted = critic(rollout["critic_features"])
        _add(counts, "critic_replay_rows", targets.numel())
        if predicted.shape != targets.shape or predicted.dtype != torch.float32:
            raise ValueError("critic replay must yield FP32 team-row values")
        critic_loss = .5 * (predicted - targets).square().mean()
        if not torch.isfinite(critic_loss):
            raise FloatingPointError("nonfinite critic loss")
        record["critic_loss"] = float(critic_loss.detach())
        critic_optimizer.zero_grad(set_to_none=True)
        critic_loss.backward()
        critic_norm = torch.nn.utils.clip_grad_norm_(critic_parameters, .5, error_if_nonfinite=True, foreach=False)
        record.update(critic_loss=float(critic_loss.detach()), critic_grad_norm=float(critic_norm),
                      critic_clipped_grad_norm=_norm([p.grad for p in critic_parameters if p.grad is not None]))
        critic_optimizer.step()
        _add(counts, "critic_optimizer_steps", 1)
        record["critic_step_completed"] = True
        _finite_parameters(critic_parameters)
        record.update(head_movement_l2=_norm([p - p0 for p, p0 in zip(head_parameters, initial_head)]),
                      critic_movement_l2=_norm([p - p0 for p, p0 in zip(critic_parameters, initial_critic)]),
                      head_optimizer_step_values=_step_values(head_optimizer, head_parameters),
                      critic_optimizer_step_values=_step_values(critic_optimizer, critic_parameters))
    result.update(status="COMPLETE", head_optimizer_step_values=_step_values(head_optimizer, head_parameters),
                  critic_optimizer_step_values=_step_values(critic_optimizer, critic_parameters))
    return result


def update_group(head, critic, head_optimizer, critic_optimizer, episodes, counts, *, horizon=256, live_record=None):
    """Keep completed-operation evidence even if a later gradient/step fails."""
    if not isinstance(head, ResponseHead) or not isinstance(critic, Critic):
        raise ValueError("group requires ResponseHead and original Critic136")
    options = dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False)
    for optimizer in (head_optimizer, critic_optimizer):
        if not isinstance(optimizer, torch.optim.Adam):
            raise ValueError("group requires separate original Adam optimizers")
        if any(group.get(key) != value for group in optimizer.param_groups for key, value in options.items()):
            raise ValueError("optimizer conventions differ from B04")
    result = {} if live_record is None else live_record
    if any(key in result for key in ("epochs", "initial_identity", "target_summary", "advantage_summary")):
        raise ValueError("live group diagnostics must start empty")
    initial_head = [p.detach().clone() for p in head.parameters()]
    initial_critic = [p.detach().clone() for p in critic.parameters()]
    try:
        return _update_group(head, critic, head_optimizer, critic_optimizer, episodes, counts,
                             horizon=horizon, live_record=result)
    finally:
        result.update(head_optimizer_step_values=_step_values(head_optimizer, list(head.parameters())),
                      critic_optimizer_step_values=_step_values(critic_optimizer, list(critic.parameters())),
                      head_movement_l2=_norm([p-p0 for p, p0 in zip(head.parameters(), initial_head)]),
                      critic_movement_l2=_norm([p-p0 for p, p0 in zip(critic.parameters(), initial_critic)]),
                      completed_counts={key: counts.get(key, 0) for key in _COUNT_KEYS})
