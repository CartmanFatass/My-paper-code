"""B01 REL/DENSE actors with the reviewed UCOPE actor boundary unchanged."""

import copy
import math

import torch
from torch import nn

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import snapshot, templates


REL = "REL"
COND = "COND"
TOP = "TOP"
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


class ConditionalResidualEncoder(RelationResidualEncoder):
    """Visible-UAV-conditioned user pooling, with the intact raw affine path."""

    def _partner_query(self, uav_embeddings, uav_count):
        return uav_embeddings[..., :20].sum(dim=1) / uav_count.clamp_min(1)

    def forward(self, observations):
        flat = observations.reshape(-1, INPUT_SIZE)
        users = flat[:, 3:63].reshape(-1, USER_ROWS, USER_WIDTH)
        uavs = flat[:, 63:103].reshape(-1, UAV_ROWS, UAV_WIDTH)
        user_mask = users[..., 2] > 0
        uav_mask = uavs[..., 3] > 0
        user_embeddings = torch.tanh(self.user_map(users))
        uav_embeddings = torch.tanh(self.uav_map(uavs)) * uav_mask[..., None]
        user_count = user_mask.sum(dim=1, keepdim=True)
        uav_count = uav_mask.sum(dim=1, keepdim=True)
        query = self._partner_query(uav_embeddings, uav_count)
        scores = (user_embeddings * query[:, None, :]).sum(dim=-1) / math.sqrt(20)
        scores = scores.masked_fill(~user_mask, -torch.inf)
        # Empty rows use a harmless finite softmax input, then exactly zero weights.
        scores = torch.where(user_count > 0, scores, torch.zeros_like(scores))
        weights = scores.softmax(dim=1).masked_fill(~user_mask, 0)
        user_context = (weights[..., None] * user_embeddings).sum(dim=1)
        user_context = user_context * (user_count / USER_ROWS)
        uav_context = uav_embeddings.sum(dim=1) / UAV_ROWS
        residual = self.context(torch.cat((user_context, uav_context), dim=-1))
        return (self.raw(flat) + residual).reshape(observations.shape[:-1] + (HIDDEN_SIZE,))


class TopResidualEncoder(ConditionalResidualEncoder):
    """Use the source-ranked first visible partner; retain all-partner context."""

    def _partner_query(self, uav_embeddings, uav_count):
        # Embeddings are already masked; native packing puts visible rows first.
        return uav_embeddings[:, 0, :20]


def make_encoder(kind, branch_seed, raw_state):
    """Build only the selected encoder, preserving the B01 private RNG law."""
    if kind not in (REL, COND, TOP, DENSE):
        raise ValueError(f"unknown native geometry actor kind: {kind}")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(branch_seed)
        if kind == REL:
            encoder = RelationResidualEncoder()
        elif kind == COND:
            encoder = ConditionalResidualEncoder()
        elif kind == TOP:
            encoder = TopResidualEncoder()
        else:
            encoder = DenseResidualEncoder()
        if kind in (REL, COND, TOP):
            _fan_in_uniform(encoder.user_map, USER_WIDTH)
            _fan_in_uniform(encoder.uav_map, UAV_WIDTH)
            _fan_in_uniform(encoder.context, 41)
        else:
            _fan_in_uniform(encoder.hidden, INPUT_SIZE)
            nn.init.zeros_(encoder.hidden.bias)
            _fan_in_uniform(encoder.context, 16)
        nn.init.zeros_(encoder.context.weight)
    encoder.raw.load_state_dict(raw_state)
    return encoder


class NativeGeometryActor(nn.Module):
    """UCOPE Actor-compatible wrapper; COND is separately bound from old B01."""

    def __init__(self, common_actor, kind, branch_seed):
        super().__init__()
        # The raw path and every downstream policy component are copied from
        # the reviewed source template. Only the private branch differs.
        self.encoder = make_encoder(kind, branch_seed, common_actor.encoder.state_dict())
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
        if self.kind in (REL, COND, TOP):
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


def geometry_snapshot(actor, critic):
    result = snapshot(actor, critic)
    for name, parameters in (("encoder", actor.encoder.parameters()),
                             ("recurrent", actor.gru.parameters()),
                             ("branch_inner", actor.branch_parameters[:-1]),
                             ("branch_projection", actor.branch_parameters[-1:])):
        result[name] = torch.cat([p.detach().flatten() for p in parameters]).clone()
    return result


def geometry_exposure(initial, actor, critic):
    final = geometry_snapshot(actor, critic)
    result = {}
    for name, start in initial.items():
        norm = float(start.norm())
        displacement = float((final[name] - start).norm())
        result[name] = {"parameters": start.numel(), "initial_norm": norm,
                        "final_norm": float(final[name].norm()), "displacement": displacement,
                        "relative_displacement": displacement / (norm + 1e-12) if norm else None}
    return result
