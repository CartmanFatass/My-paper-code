"""Private gate paths and the read-only DENSE proposal distribution."""
import torch
from torch import nn

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import Actor, Critic, generator
from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import NativeGeometryActor


class GatePath(nn.Module):
    def __init__(self, residual=False):
        super().__init__()
        self.residual = residual
        self.encoder = nn.Linear(108, 32)
        self.gru = nn.GRU(32, 32)
        self.head = nn.Sequential(nn.Linear(156 if residual else 48, 32), nn.Tanh(), nn.Linear(32, 1))
        nn.init.zeros_(self.head[-1].weight)
        nn.init.zeros_(self.head[-1].bias)

    def forward(self, x, b, z, hidden):
        recurrent, hidden = self.gru(self.encoder(x).tanh(), hidden)
        pieces = (recurrent, x, b, z) if self.residual else (recurrent, b, z)
        return self.head(torch.cat(pieces, -1)).squeeze(-1), hidden


class Gate(nn.Module):
    def __init__(self, common, residual=None):
        super().__init__()
        self.common = common
        self.residual = residual

    def initial_state(self, agents=5):
        return torch.zeros(2 if self.residual is not None else 1, agents, 32)

    def forward(self, x, b, z, hidden):
        logits, hc = self.common(x, b, z, hidden[:1])
        if self.residual is None:
            return logits, hc
        extra, hr = self.residual(x, b, z, hidden[1:])
        return logits + extra, torch.cat((hc, hr), 0)


def build_learned(seed, arm):
    base = seed * 100000
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(base + 11)
        common = GatePath()
        torch.manual_seed(base + 12)
        critic = Critic()
        residual = None
        if arm == "G":
            torch.manual_seed(base + 13)
            residual = GatePath(residual=True)
    return Gate(common, residual), critic


def base_architecture(seed):
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed * 100000 + 14)
        base = NativeGeometryActor(Actor(), "DENSE", seed * 100000 + 14)
    return base


def load_base(path, seed):
    base = base_architecture(seed)
    base.load_state_dict(torch.load(path, map_location="cpu", weights_only=False)["actor"])
    return base.requires_grad_(False).eval()


def action_generators(seed, arm, phase, episode):
    a = ("T", "G", "C", "F", "dwell").index(arm)
    base = seed * 100000
    if phase == "train":
        proposal, gate = base + 10000 + 1000 * a + episode, base + 20000 + 1000 * a + episode
    else:
        proposal, gate = base + 30000 + 100 * a + episode, base + 40000 + 100 * a + episode
    return generator(proposal), generator(gate)


def proposal_sample(base, mean, rng):
    # Five ordered, three-dimensional Normal draws, as frozen in the facts file.
    noise = torch.stack([torch.randn(3, generator=rng) for _ in range(5)])
    u = mean + base.log_std.clamp(-5, 2).exp() * noise
    return u, u.tanh()


def gate_sample(logits, mask, rng):
    choices = torch.zeros_like(logits)
    for i in range(5):
        if mask[i]:
            choices[i] = torch.bernoulli(logits[i].sigmoid(), generator=rng)
    return choices


def gate_terms(logits, choices, mask):
    distribution = torch.distributions.Bernoulli(logits=logits)
    return (torch.where(mask, distribution.log_prob(choices), 0),
            torch.where(mask, distribution.entropy(), 0).sum(-1))


def snapshot(gate, critic):
    groups = {"gate": list(gate.parameters()), "critic": list(critic.parameters())}
    for name, path in (("common", gate.common), ("residual", gate.residual)):
        if path is not None:
            groups[name] = list(path.parameters())
            groups[name + "_final"] = list(path.head[-1].parameters())
    return {k: torch.cat([p.detach().flatten() for p in ps]).clone() for k, ps in groups.items()}


def displacement(initial, gate, critic):
    final = snapshot(gate, critic)
    return {k: {"parameters": v.numel(), "initial_norm": float(v.norm()),
                "final_norm": float(final[k].norm()), "displacement": float((final[k] - v).norm()),
                "relative_displacement": float((final[k] - v).norm() / v.norm()) if v.norm() else None}
            for k, v in initial.items()}
