"""B06 optimizer split with retained B05 recurrent PPO updates."""

import torch

from experiments.candidates.uav_message_content.b05.update import update_motion
from .model import CalibrationActor, ResidualActor


def optimizers_for(actor, critic):
    if isinstance(actor, CalibrationActor):
        actor_lr = 3e-3
    elif isinstance(actor, ResidualActor):
        actor_lr = 3e-4
    else:
        raise TypeError("B06 actor must be K or D")
    options = dict(betas=(.9, .999), eps=1e-8, weight_decay=0,
                   amsgrad=False, foreach=False, fused=False)
    actor_parameters = [parameter for parameter in actor.parameters() if parameter.requires_grad]
    return (torch.optim.Adam(actor_parameters, lr=actor_lr, **options),
            torch.optim.Adam(critic.parameters(), lr=3e-4, **options))
