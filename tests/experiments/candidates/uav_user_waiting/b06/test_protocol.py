"""Input-byte and before-query binding checks with synthetic files only."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.uav_user_waiting.b06 import protocol as p


def inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(p, 'SEEDS', (17, 18))
    monkeypatch.setattr(p, 'WORLDS', 2)
    staged = tmp_path / 'staged'
    staged.mkdir()
    originals, fair_rows, records = [], [], {}
    for seed in p.SEEDS:
        raw = staged / f'S_{seed}.npz'
        np.savez(raw, world_seed=np.array(seed))
        identity = p.file_identity(raw)
        identity['path'] = f'/remote/unique/S_{seed}.npz'
        originals.append(dict(seed=seed, arm='S', raw=identity))
        for package in p.REFERENCES:
            program = package.split(':')[0]
            fair_rows.append(dict(package=package, seed=seed, program=program))
            records[f'{program}:{seed}'] = dict(shared=dict(inherited=dict(mean_path_length_m=17.)))
    source = tmp_path / 'experiments/synthetic.py'
    source.parent.mkdir()
    source.write_text('synthetic = True\n')
    source_id = p.relative_identity(source, tmp_path)
    documents = (
        (p.B04_RESULT, 'B04_SHA256', dict(status='VERIFIED_COMPLETE', launch_sha=p.B04_SOURCE,
             rows=originals, config=dict(source_identities=[source_id]))),
        (p.B05_RESULT, 'B05_SHA256', dict(status='VERIFIED_COMPLETE', launch_sha=p.B05_SOURCE,
             rows=fair_rows, path_records=records, config=dict(source_identities=[]))),
    )
    for relative, key, document in documents:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document))
        monkeypatch.setattr(p, key, hashlib.sha256(path.read_bytes()).hexdigest())
    return staged, source


def test_complete_verified_references_and_staged_bytes(tmp_path, monkeypatch):
    staged, _ = inputs(tmp_path, monkeypatch)
    old, fair, mapping, metadata = p.load_baselines(staged, root=tmp_path)
    assert len(old) == 2 and len(fair) == 6 and len(mapping) == 2
    assert fair['S:LRS', 17]['inherited']['mean_path_length_m'] == 17.
    assert mapping[17]['canonical_path'] == '/remote/unique/S_17.npz'
    assert mapping[17]['path'] == str(staged / 'S_17.npz')
    assert p.load_raw(mapping[17])['world_seed'] == 17


@pytest.mark.parametrize('corrupt', ['staged', 'source', 'bound_json', 'missing_staged'])
def test_input_mutation_rejected_without_original_location_fallback(tmp_path, monkeypatch, corrupt):
    staged, source = inputs(tmp_path, monkeypatch)
    if corrupt == 'staged':
        (staged / 'S_17.npz').write_bytes(b'changed')
    elif corrupt == 'source':
        source.write_text('synthetic = False\n')
    elif corrupt == 'bound_json':
        (tmp_path / p.B05_RESULT).write_text('{}')
    else:
        (staged / 'S_17.npz').unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        p.load_baselines(staged, root=tmp_path)


def test_same_descriptor_raw_digest_checked_before_decompression(tmp_path):
    path = tmp_path / 'synthetic.npz'
    np.savez(path, safe=np.arange(3))
    identity = p.file_identity(path)
    np.savez(path, safe=np.arange(4))
    with pytest.raises(ValueError, match='identity mismatch'):
        p.load_raw(identity)


def test_snapshot_input_location_uses_canonical_output_not_source_root(tmp_path):
    output = tmp_path / 'author/runs/uav_user_waiting/b06_fair_model_a01'
    expected = tmp_path / 'author/temp/directions/uav_user_waiting/b06/baseline_s'
    assert p.baseline_directory(output) == expected
    assert p.baseline_directory(output.with_name('b06_fair_model_read_a01')) == expected
    for bad in ('runs/uav_user_waiting/b06_fair_model_a01', tmp_path / 'author/runs/other_direction/tag'):
        with pytest.raises(ValueError, match='canonical absolute'):
            p.baseline_directory(bad)
