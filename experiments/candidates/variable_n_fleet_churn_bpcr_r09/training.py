"""Pure identity-free PPO/GAE/minibatch/AdamW-decay contract functions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math

import numpy as np
import torch

from .numeric import canonical_stiefel


def gae_terminal(values: torch.Tensor, terminal_objective: torch.Tensor) -> tuple[torch.Tensor,torch.Tensor]:
    """Exact six-decision gamma=1, lambda=.95 frozen backward recursion."""
    if values.shape[-1]!=6 or terminal_objective.shape!=values.shape[:-1]:raise ValueError("GAE requires six values and one terminal objective per episode")
    stopped=values.detach();target=terminal_objective.detach();advantages=torch.empty_like(stopped);next_value=torch.zeros_like(target);next_adv=torch.zeros_like(target)
    for j in range(5,-1,-1):
        reward=target if j==5 else torch.zeros_like(target)
        delta=reward+next_value-stopped[...,j]
        next_adv=delta if j==5 else delta+0.95*next_adv
        advantages[...,j]=next_adv;next_value=stopped[...,j]
    returns=advantages+stopped
    return advantages.detach(),returns.detach()


def normalize_advantages(advantages: torch.Tensor) -> torch.Tensor:
    flat=advantages.reshape(-1);mean=flat.mean();variance=((flat-mean)**2).mean()
    if bool(variance==0):return torch.zeros_like(advantages)
    return ((advantages-mean)/torch.sqrt(variance)).detach()


def frozen_minibatches(permutation: Sequence[int]) -> tuple[tuple[int,...],...]:
    p=tuple(int(x) for x in permutation)
    if len(p)!=96 or sorted(p)!=list(range(96)):raise ValueError("each epoch needs one exact permutation of 96 addresses")
    return tuple(tuple(p[start:start+24]) for start in range(0,96,24))


def ppo_loss(
    logpi: torch.Tensor,
    old_logpi: torch.Tensor,
    advantages: torch.Tensor,
    values: torch.Tensor,
    returns: torch.Tensor,
    token_entropies: torch.Tensor,
    token_is_variable: torch.Tensor,
) -> dict[str,torch.Tensor]:
    tensors=(logpi,old_logpi,advantages,values,returns)
    if len({tuple(x.shape) for x in tensors})!=1:raise ValueError("PPO decision tensors must share shape")
    if token_entropies.shape!=(*logpi.shape,4) or token_is_variable.shape!=token_entropies.shape:raise ValueError("entropy requires four serialized token slots")
    ratio=torch.exp(logpi-old_logpi.detach());adv=advantages.detach();clipped=torch.clamp(ratio,0.8,1.2)
    actor=-torch.minimum(ratio*adv,clipped*adv).mean();value=((values-returns.detach())**2).mean()
    entropy=(token_entropies*token_is_variable).sum(dim=-1).div(4.0).mean()
    total=actor+0.5*value-0.01*entropy
    return {"actor":actor,"value":value,"entropy":entropy,"total":total}


def adamw_decay_groups(parameters: Mapping[str,torch.Tensor]) -> dict[str,tuple[str,...]]:
    decay=[];no_decay=[]
    for name,value in parameters.items():
        if not isinstance(value,torch.Tensor):raise TypeError("optimizer surface requires tensors")
        (decay if value.ndim>=2 else no_decay).append(name)
    return {"decay_1e-4":tuple(sorted(decay)),"decay_zero":tuple(sorted(no_decay))}


def explicit_stiefel_fixture(source: np.ndarray, logical_shape: tuple[int,int], gain: float) -> np.ndarray:
    if not math.isfinite(gain) or gain<=0:raise ValueError("initialization gain must be finite and positive")
    return canonical_stiefel(source,logical_shape)*gain


def work_count_contract() -> dict[str,int]:
    counts={"training_episodes":16*2*256*16,"learned_joint_decisions":16*2*256*16*6,"optimizer_minibatch_steps":16*2*256*4*4,"validation_rollouts":16*2*2*4*32,"conclusion_rollouts":16*64*4,"bcrh_rollouts":16*64}
    expected={"training_episodes":131072,"learned_joint_decisions":786432,"optimizer_minibatch_steps":131072,"validation_rollouts":8192,"conclusion_rollouts":4096,"bcrh_rollouts":1024}
    if counts!=expected:raise AssertionError("revision-09 work counts differ")
    return counts
