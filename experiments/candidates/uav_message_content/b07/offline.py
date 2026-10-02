"""Complete teacher-history unroll, old development selection and dictionary fitting."""

import numpy as np
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.policy import tanh_log_prob
from .codec import reconstruct
from .contract import FIELDS, increment, require
from .inputs import cache_addresses


def replay_inputs(episode, book=None, scales=None, temperature=None, counts=None):
    source = torch.from_numpy(episode["packet"][:, list(FIELDS)])
    decoded = source if book is None else reconstruct(source, book, scales, temperature, counts)[0]
    geometry = torch.stack([decoded[:, FIELDS.index(i)] if i in FIELDS else torch.zeros(len(source))
                            for i in range(7)], -1)
    geometry = torch.cat((torch.zeros(1, 7), geometry), 0)
    addresses = cache_addresses(episode)
    valid = addresses > 0
    sent = (addresses - 1).clamp_min(0).float() / 256
    age = torch.where(valid, torch.arange(len(source))[:, None, None] / 256 - sent, 0)
    records = torch.cat((geometry[addresses], valid[..., None].float(),
                         torch.where(valid, sent, 0)[..., None], age[..., None]), -1)
    # Private raw/previous commands and public channel/own pending are fixed teacher facts.
    old = torch.from_numpy(episode["actor_input"])
    return torch.cat((old[..., :121], records.reshape(len(source), 5, 50),
                      torch.zeros(len(source), 5, 15)), -1)


def replay(actor, episodes, book, scales, counts, phase, temperature=None):
    inputs = [replay_inputs(e, book, scales, temperature, counts) for e in episodes]
    horizon = len(inputs[0])
    require(all(len(x) == horizon for x in inputs), "replay horizon mismatch")
    hidden = torch.zeros(1, 5 * len(episodes), 64)
    result = []
    for t in range(horizon):
        x = torch.cat([value[t] for value in inputs], 0)
        mean, _, hidden = actor(x[None], hidden)
        increment(counts, f"{phase}_actor_rows", 5 * len(episodes))
        increment(counts, f"{phase}_actor_calls")
        require(bool(torch.isfinite(mean).all()), "nonfinite replay mean")
        result.append(mean[0].reshape(len(episodes), 5, 3))
    means = torch.stack(result, 1)
    targets = torch.stack([torch.from_numpy(e["composed_mean"]) for e in episodes])
    sigma = actor.log_std.clamp(-5, 2).exp()
    kl = .5 * ((means - targets) / sigma).square().sum(-1)
    return means, kl.mean()


@torch.no_grad()
def score(actor, episodes, book, scales, counts):
    # Same presentation batch (five actor rows) as binding and native inference.
    return float(torch.stack([replay(actor, [e], book, scales, counts, "dev")[1] for e in episodes]).mean())


@torch.no_grad()
def binding_replay(actor, episodes, counts):
    rows = []
    for e, episode in enumerate(episodes):
        x = replay_inputs(episode)
        require(torch.equal(x, torch.from_numpy(episode["actor_input"])), "uncompressed input binding")
        require(torch.equal(actor.log_std, torch.from_numpy(episode["log_std"])), "old variance binding")
        means, kl = replay(actor, [episode], None, None, counts, "binding")
        gap = (means[0] - torch.from_numpy(episode["composed_mean"])).double()
        density = tanh_log_prob(torch.from_numpy(episode["pre_tanh_motion"]), means[0], actor.log_std)
        old_density = torch.from_numpy(episode["sample_logp"])
        require(bool(torch.isfinite(density).all()), "nonfinite binding density")
        rows.append(dict(episode=e, gaussian_kl=float(kl), mean_gap_rms=float(gap.square().mean().sqrt()),
                         mean_gap_max=float(gap.abs().max()), density_gap_max=float((density - old_density).abs().max())))
    return dict(episodes=rows, gaussian_kl=float(np.mean([r["gaussian_kl"] for r in rows])),
                targets="original stored composed means, unchanged", subtraction=False)


def fit_learned(actor, episodes, initial_book, scales, seed, counts, progress=lambda _, __: None):
    book = torch.nn.Parameter(initial_book.clone())
    optimizer = torch.optim.Adam([book], lr=.001, betas=(.9, .999), eps=1e-8, weight_decay=0)
    rng = np.random.default_rng(seed + 10000)
    history = []
    for epoch in range(20):
        temperature = .25 * (.025 / .25) ** (epoch / 19)
        order = rng.permutation(24).tolist()
        require(len(episodes) == 24, "fixed fitting episodes")
        for offset in range(0, 24, 4):
            selected = order[offset:offset + 4]
            optimizer.zero_grad(set_to_none=True)
            _, loss = replay(actor, [episodes[i] for i in selected], book, scales, counts, "fit", temperature)
            require(bool(torch.isfinite(loss)), "nonfinite fit loss")
            loss.backward()
            require(book.grad is not None and bool(torch.isfinite(book.grad).all()), "nonfinite dictionary gradient")
            norm = torch.nn.utils.clip_grad_norm_([book], 1.)
            optimizer.step()
            increment(counts, "adam_updates")
            with torch.no_grad():
                book.clamp_(0, 1)
            require(all(p.grad is None and not p.requires_grad for p in actor.parameters()), "receiver gradient leakage")
            row = dict(epoch=epoch, batch=offset // 4, episodes=selected, temperature=temperature,
                       loss=float(loss.detach()), gradient_norm_before_clip=float(norm))
            history.append(row)
            progress(row, book.detach())
    return book.detach(), history
