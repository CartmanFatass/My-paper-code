"""B01 REL/DENSE actors with the reviewed UCOPE actor boundary unchanged."""

import copy
import math

import torch
from torch import nn

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Actor, Critic, templates


REL = "REL"
DENSE = "DENSE"
INPUT_SIZE = 108
HIDDEN_SIZE = 64
USER_ROWS = 20
USER_WIDTH = 3
UAV_ROWS = 10
UAV_WIDTH = 4


def _fan_in_uniform(module, fan_in):
    """Use the card's zero-mean +/-1/sqrt(fan-in) private initialization."""
    bound = 1.0 / math.sqrt(fan_in)
    nn.init.uniform_(module.weight, -bound, bound)


class RelationResidualEncoder(nn.Module):
    """Typed nonlinear row maps pooled into the full raw residual path."""

    def __init__(self):
        super().__init__()
        self.raw = nn.Linear(INPUT_SIZE, HIDDEN_SIZE)
        self.user_map = nn.Linear(USER_WIDTH, 20, bias=False)
        self.uav_map = nn.Linear(UAV_WIDTH, 21, bias=False)
        self.context = nn.Linear(41, HIDDEN_SIZE, bias=False)

    def forward(self, observations):
        flat = observations.reshape(-1, INPUT_SIZE)
        users = flat[:, 3:3 + USER_ROWS * USER_WIDTH].reshape(-1, USER_ROWS, USER_WIDTH)
        uavs = flat[:, 3 + USER_ROWS * USER_WIDTH:
                     3 + USER_ROWS * USER_WIDTH + UAV_ROWS * UAV_WIDTH]
        uavs = uavs.reshape(-1, UAV_ROWS, UAV_WIDTH)
        user_context = torch.tanh(self.user_map(users)).mean(dim=1)
        uav_context = torch.tanh(self.uav_map(uavs)).mean(dim=1)
        residual = self.context(torch.cat((user_context, uav_context), dim=-1))
        return (self.raw(flat) + residual).reshape(observations.shape[:-1] + (HIDDEN_SIZE,))


class DenseResidualEncoder(nn.Module):
    """Unstructured nonlinear branch with the same additional parameter count."""

    def __init__(self):
        super().__init__()
        self.raw = nn.Linear(INPUT_SIZE, HIDDEN_SIZE)
        self.hidden = nn.Linear(INPUT_SIZE, 16)
        self.context = nn.Linear(16, HIDDEN_SIZE, bias=False)

    def forward(self, observations):
        flat = observations.reshape(-1, INPUT_SIZE)
        residual = self.context(torch.tanh(self.hidden(flat)))
        return (self.raw(flat) + residual).reshape(observations.shape[:-1] + (HIDDEN_SIZE,))


class NativeGeometryActor(nn.Module):
    """UCOPE Actor-compatible wrapper using REL or DENSE as ``encoder``."""

    def __init__(self, common_actor, kind, branch_seed):
        if kind not in (REL, DENSE):
            raise ValueError(f"unknown B01 actor kind: {kind}")
        super().__init__()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(branch_seed)
            self.encoder = (RelationResidualEncoder() if kind == REL
                            else DenseResidualEncoder())
            if kind == REL:
                _fan_in_uniform(self.encoder.user_map, USER_WIDTH)
                _fan_in_uniform(self.encoder.uav_map, UAV_WIDTH)
                _fan_in_uniform(self.encoder.context, 41)
            else:
                _fan_in_uniform(self.encoder.hidden, INPUT_SIZE)
                nn.init.zeros_(self.encoder.hidden.bias)
                _fan_in_uniform(self.encoder.context, 16)
            nn.init.zeros_(self.encoder.context.weight)

        # The raw path and every downstream policy component are copied from
        # the reviewed source template. Only the private branch differs.
        self.encoder.raw.load_state_dict(common_actor.encoder.state_dict())
        self.gru = copy.deepcopy(common_actor.gru)
        self.mean = copy.deepcopy(common_actor.mean)
        self.log_std = nn.Parameter(common_actor.log_std.detach().clone())
        self.duration = None
        self.duration_conditioned = False
        self.kind = kind

    def forward(self, observations, hidden):
        output, hidden = self.gru(torch.tanh(self.encoder(observations)), hidden)
        return self.mean(output), output, hidden

    @property
    def branch_parameters(self):
        if self.kind == REL:
            return (self.encoder.user_map.weight,
                    self.encoder.uav_map.weight,
                    self.encoder.context.weight)
        return (self.encoder.hidden.weight, self.encoder.hidden.bias,
                self.encoder.context.weight)


def parameter_count(actor, critic=None):
    """Return actor parameters, or complete learner parameters when given a critic."""
    parameters = list(actor.parameters())
    if critic is not None:
        parameters.extend(critic.parameters())
    return sum(parameter.numel() for parameter in parameters)


def build_pair(seed):
    """Create common source components and paired B01 actors.

    The common source template uses ``100000*seed+11``. Both private branches
    use the separate card stream ``100000*seed+12`` while their output
    projections start at zero, making initial policies identical.
    """
    common_actor, common_critic = templates(seed)
    branch_seed = 100000 * seed + 12
    rel = NativeGeometryActor(common_actor, REL, branch_seed)
    dense = NativeGeometryActor(common_actor, DENSE, branch_seed)
    rel_critic = copy.deepcopy(common_critic)
    dense_critic = copy.deepcopy(common_critic)
    return {
        REL: (rel, rel_critic),
        DENSE: (dense, dense_critic),
        "common": (common_actor, common_critic),
    }


def parameter_summary(pair):
    """Expose arithmetic needed by the focused acceptance checks."""
    return {
        kind: {
            "actor": parameter_count(pair[kind][0], pair[kind][1]),
            "branch": sum(parameter.numel() for parameter in pair[kind][0].branch_parameters),
        }
        for kind in (REL, DENSE)
    }
