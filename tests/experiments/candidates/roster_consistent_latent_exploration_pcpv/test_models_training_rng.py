import hashlib
import math

import numpy as np
import torch

from experiments.candidates.roster_consistent_latent_exploration_pcpv import rng
from experiments.candidates.roster_consistent_latent_exploration_pcpv.config import RNG_DOMAIN
from experiments.candidates.roster_consistent_latent_exploration_pcpv.host import (
    EntityState, PublicState, claim_encoding, sector_encoding,
)
from experiments.candidates.roster_consistent_latent_exploration_pcpv.models import (
    paired_policies, parameter_count,
)
from experiments.candidates.roster_consistent_latent_exploration_pcpv.training import (
    normal_log_density, normalized_sgd_step,
)


def _manual_uniform(*fields):
    def field(value):
        raw = str(value).encode()
        return len(raw).to_bytes(4, "big") + raw
    digest = hashlib.sha256(b"".join(field(x) for x in (RNG_DOMAIN, *fields))).digest()
    k = int.from_bytes(digest[:8], "big")
    return min((k + 0.5) / 2**64, math.nextafter(1.0, 0.0))


def test_fresh_sha_domain_separation_pairing_and_normal():
    fields = (rng.root_label(0), "common", "fixture", "scenario", 2)
    assert rng.uniform(*fields) == _manual_uniform(*fields)
    assert rng.uniform(*fields) == rng.uniform(*fields)
    assert rng.uniform(*fields, "action") != rng.uniform(*fields, "tie")
    assert rng.uniform(rng.root_label(0), *fields[1:]) != rng.uniform(
        rng.root_label(1), *fields[1:])
    assert math.isfinite(rng.normal(*fields, "normal"))


def test_exact_parameter_count_initialization_and_common_copy():
    keep, flex = paired_policies(3)
    assert parameter_count(keep) == parameter_count(flex) == 26_545
    assert all(p.dtype == torch.float64 for p in keep.parameters())
    for (name_a, a), (name_b, b) in zip(keep.named_parameters(),
                                        flex.named_parameters()):
        assert name_a == name_b
        assert torch.equal(a, b)
        if name_a.endswith("bias"):
            assert torch.count_nonzero(a) == 0
        elif name_a not in {"common_event.layers.1.weight",
                            "agent_event.layers.1.weight"}:
            fan_out, fan_in = a.shape
            bound = math.sqrt(6 / (fan_in + fan_out))
            assert float(a.abs().max()) <= bound
    assert torch.count_nonzero(keep.common_event.layers[-1].weight) == 0
    assert torch.count_nonzero(keep.agent_event.layers[-1].weight) == 0
    assert torch.count_nonzero(keep.common_event.layers[0].weight) > 0
    assert torch.count_nonzero(keep.agent_event.layers[0].weight) > 0


def test_encodings_zero_head_containment_and_strict_live_extension():
    keep, flex = paired_policies(0)
    entities = {i: EntityState(5 + i * 10, i % 4, i - 2, False)
                for i in range(5)}
    state = PublicState(20, 1, 1, entities, {i: (i + 1) / 7 for i in entities})
    summary = keep.public_summary(state)
    assert summary.shape == (68,)
    own = torch.as_tensor(state.own_features(0))
    old = torch.tensor((0.1, -0.2, 0.3, -0.4))
    noise = torch.tensor((0.5, 0.2, -0.1, 0.7))
    assert torch.equal(flex.event_plan(summary, own, old, noise), old)
    with torch.no_grad():
        flex.common_event.layers[-1].weight[0, 0] = 0.25
        flex.agent_event.layers[-1].weight[1, 1] = -0.2
    changed = flex.event_plan(summary, own, old, noise)
    assert not torch.equal(changed, old)
    logits = flex.action_logits(state, 0, summary, changed)
    (-torch.log_softmax(logits, -1)[0]).backward()
    assert flex.common_event.layers[-1].weight.grad.abs().sum() > 0
    assert flex.agent_event.layers[-1].weight.grad.abs().sum() > 0
    assert np.allclose(sector_encoding(0), (0.0, 1.0))
    assert claim_encoding(None) == (0.0, 0.0)
    assert np.allclose(claim_encoding(1), (1.0, 0.0), atol=1e-15)


def test_stopped_plan_score_and_exact_whole_tensor_update_norm():
    mean = torch.tensor((0.2, -0.1), requires_grad=True)
    log_scale = torch.tensor((-0.5, -0.5), requires_grad=True)
    sample = (mean + torch.exp(log_scale) * torch.tensor((0.3, -0.7))).detach()
    score = normal_log_density(sample, mean, log_scale)
    score.backward()
    assert sample.requires_grad is False
    assert mean.grad is not None and log_scale.grad is not None

    keep, _ = paired_policies(1)
    before = torch.cat([p.detach().flatten().clone() for p in keep.parameters()])
    loss = sum((p.square().sum() for p in keep.parameters()))
    reported = normalized_sgd_step(keep, loss)
    after = torch.cat([p.detach().flatten() for p in keep.parameters()])
    assert reported == 0.0005
    assert abs(float(torch.linalg.vector_norm(after - before)) - 0.0005) < 1e-12
