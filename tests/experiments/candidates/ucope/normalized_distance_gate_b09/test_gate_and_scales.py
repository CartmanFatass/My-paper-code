"""Focused B09 distinction and prospective input-binding checks; no native host."""
import hashlib
import io
import json

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.normalized_distance_gate_b09.gate import Gate
from experiments.candidates.ucope.normalized_distance_gate_b09 import scales


def test_policy_class_zero_initialization_and_true_scalar():
    rng = torch.get_rng_state().clone()
    g = Gate('normalized', 10, 1e-7, 1.7e-5)
    b = Gate('scalar', 10, 1e-7, 1.7e-5)
    x = torch.zeros(4, 5, 175)
    x[..., -1] = torch.linspace(0, 1, 20).reshape(4, 5)
    assert torch.equal(rng, torch.get_rng_state())
    assert sum(p.numel() for p in g.parameters()) == 2
    assert sum(p.numel() for p in b.parameters()) == 1
    assert torch.equal(g(x), torch.zeros(4, 5))
    assert torch.equal(b(x), torch.zeros(4, 5))
    with torch.no_grad():
        g.b0.fill_(.3); g.b1.fill_(-.12); b.b0.fill_(.3)
    expected = g.b0 - g.b1*g.median/g.scale + (g.b1/g.scale)*x[..., -1]
    torch.testing.assert_close(g(x), expected)
    torch.testing.assert_close(b(x), torch.full((4,5), .3))
    logp = g.log_prob(x, torch.ones(4,5,dtype=torch.bool))
    assert torch.isfinite(logp).all()
    logp.mean().backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in g.parameters())
    assert g.b0.grad != 0 and g.b1.grad != 0
    assert not g.median.requires_grad and not g.scale.requires_grad


@pytest.mark.parametrize('median,scale', [(0,0),(0,-1),(float('nan'),1),(0,float('inf'))])
def test_degenerate_scale_is_rejected(median,scale):
    with pytest.raises(ValueError):
        Gate('normalized', 0, median, scale)


def test_extraction_uses_all_worlds_nonreset_raw_means_and_ignores_rewards():
    means = np.linspace(-.6,.6,64*256*5*3,dtype=np.float32).reshape(64,256,5,3)
    previous = np.zeros_like(means)
    expected = ((torch.tanh(torch.from_numpy(means[:,1:].copy()))).square().sum(-1)/12).numpy().ravel()
    raw = io.BytesIO()
    np.savez(raw,means=means,previous=previous,reward=np.array([np.nan]))
    actual = scales.extract(raw.getvalue())
    q10,median,q90 = np.quantile(expected,[.1,.5,.9],method='linear')
    assert actual == dict(rows=81600,median=float(median),q10=float(q10),q90=float(q90),scale=float(q90-q10))
    means[:,0] = 10000
    raw2 = io.BytesIO(); np.savez(raw2,means=means,previous=previous)
    assert scales.extract(raw2.getvalue()) == actual
    zero = io.BytesIO(); np.savez(zero,means=np.zeros_like(means),previous=previous)
    with pytest.raises(ValueError,match='degenerate'):
        scales.extract(zero.getvalue())


def test_bad_input_digest_precedes_scale_arithmetic(tmp_path,monkeypatch):
    raw= b'changed'
    (tmp_path/'panel.npz').write_bytes(raw)
    definition=tmp_path/'scales.json'
    definition.write_text(json.dumps({'masters':{'8961':{'foundation_master':8941,'source_master':8951,
        'source_npz':'panel.npz','source_npz_sha256':hashlib.sha256(b'expected').hexdigest()}}}))
    monkeypatch.setattr(scales,'REPO',tmp_path)
    monkeypatch.setattr(scales,'DEFINITION',definition)
    called=[]
    monkeypatch.setattr(scales,'extract',lambda raw:called.append(raw))
    with pytest.raises(ValueError,match='digest mismatch'):
        scales.load(8961)
    assert called==[]
