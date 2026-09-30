"""Bookkeeping/identity checks only; fake collection never constructs a native host."""

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from experiments.candidates.uav_user_waiting.b02_continuation import study
from experiments.candidates.uav_user_waiting.b02_continuation.read import validate_summary


def write(path, value):
    path.write_text(json.dumps(value))
    return study.original.file_identity(path)['sha256']


@pytest.fixture
def parent(tmp_path, monkeypatch):
    """Mock bound artifacts, preserving the production prefix and source contract."""
    path = tmp_path / 'parent'
    (path / 'raw').mkdir(parents=True)
    monkeypatch.setattr(study, 'PARENT', path)
    artifacts = []
    for arm, seed in study.PLAN[:7]:
        raw = path / 'raw' / f'{arm}_{seed}.npz'
        raw.write_bytes(f'fake raw {arm} {seed}'.encode())
        artifacts.append(study.original.file_identity(raw))
    config = study.original.frozen_config(study.ORIGINAL_SHA)
    rows = [dict(arm=arm, seed=seed, steps=256, raw=artifacts[i])
            for i, (arm, seed) in enumerate(study.PLAN[:6])]
    summary = dict(status='INCOMPLETE_TECHNICAL_FAILURE', scientific_invocation=True,
        launch_sha=study.ORIGINAL_SHA, config=config, counts=study.PRIOR_COUNTS.copy(), rows=rows, artifacts=artifacts)
    values = {'summary.json': summary, 'config.json': config, 'process-exit.json': dict(exit_code=1),
              'launch-manifest.json': dict(sha=study.ORIGINAL_SHA, output_root=str(path),
                  operation_ref=study.PARENT_OPERATION, node='wsl_4070', acceptance='accepted')}
    hashes = {name: write(path / name, value) for name, value in values.items()}
    monkeypatch.setattr(study, 'PARENT_HASHES', hashes)
    proof = tmp_path / 'proof.json'
    proof_hash = write(proof, dict(status='READ_INCOMPLETE_TECHNICAL_COLLECTION',
        summary_sha256=hashes['summary.json'], verified_native_steps=1648, native_steps_added=0, fits_added=0,
        complete_rows=[dict(arm=a, seed=s, verified_steps=256) for a, s in study.PLAN[:6]],
        partial=dict(arm='R', seed=29322001, verified_steps=112)))
    monkeypatch.setattr(study, 'PROOF', proof)
    monkeypatch.setattr(study, 'PROOF_HASH', proof_hash)
    return summary


def test_bound_parent_and_proof_reject_tamper(parent):
    assert study.validate_parent() == parent
    path = Path(parent['artifacts'][-1]['path'])
    path.write_bytes(path.read_bytes() + b'changed partial')
    with pytest.raises(RuntimeError, match='raw identity'):
        study.validate_parent()


def test_bound_parent_rejects_changed_original_source(parent, monkeypatch):
    original = study.original.frozen_config
    monkeypatch.setattr(study.original, 'frozen_config', lambda sha: {**original(sha), 'deadline_seconds': 999})
    with pytest.raises(RuntimeError, match='scientific inputs changed'):
        study.validate_parent()


def mock_collection(monkeypatch, parent, *, fail=False):
    called, captures = [], []
    monkeypatch.setattr(study, 'verify_parent_stopped', lambda: {'execution': {'state': 'exited'}})
    monkeypatch.setattr(study.torch, 'set_num_threads', lambda n: None)
    monkeypatch.setattr(study.torch, 'set_num_interop_threads', lambda n: None)
    monkeypatch.setattr(study.original, 'factory', lambda seed: SimpleNamespace(env=SimpleNamespace(), close=lambda: None))

    def collect(env, arm, seed, out, counts):
        called.append((arm, seed))
        counts['explicit_resets'] += 1
        counts['native_step_calls'] += 112 if fail else 256
        counts['team_steps'] += 112 if fail else 256
        if fail:
            (out / 'raw' / f'{arm}_{seed}.npz').write_bytes(b'partial second attempt')
            raise TypeError('synthetic original failure')
        counts['complete_episodes'] += 1
        return dict(arm=arm, seed=seed, steps=256, mean_user_max_unserved_gap=0, deadline_misses=0), None

    def save(out, row, raw):
        path = out / 'raw' / f"{row['arm']}_{row['seed']}.npz"
        path.write_bytes(b'new synthetic row')
        row['raw'] = study.original.file_identity(path)

    monkeypatch.setattr(study.original, 'collect_episode', collect)
    monkeypatch.setattr(study.original, 'save_episode', save)
    monkeypatch.setattr(study.original, 'paired_reading', lambda *args: {'mock': True})
    monkeypatch.setattr(study, 'capture_failure', lambda exc, out: captures.append((type(exc), str(exc))) or {'mock': True})
    return called, captures


def test_exact_suffix_and_composite_reader_counts(parent, tmp_path, monkeypatch):
    called, captures = mock_collection(monkeypatch, parent)
    out = tmp_path / 'new'
    original_rows = copy.deepcopy(parent['rows'])
    result = study.run_batch(out, 'a' * 40, entry_start=time.perf_counter(), admission={'sha': 'a' * 40})
    assert called == list(study.PLAN[6:]) and len(called) == 250
    assert called[0] == ('R', 29322001) and captures == []
    assert result['status'] == 'COMPLETE' and result['counts'] == study.NEW_COUNTS
    assert result['rows'][:6] == original_rows and study.validate_parent()['rows'] == original_rows
    assert result['exposure'] == dict(prior_result_steps=1648, new_result_steps=64000, total_result_steps=65648,
        valid_panel_steps=65536, valid_panel_episodes=256, reused_complete_steps=1536,
        failed_prefix_steps=112, fits=0, optimizer_updates=0)
    write(out / 'process-exit.json', dict(exit_code=0))
    write(out / 'launch-manifest.json', dict(sha='a' * 40, output_root=str(out), node='wsl_4070', acceptance='accepted'))
    assert validate_summary(out, result, parent) == result['rows']
    for mutation in ('count', 'old_row', 'order', 'failed_prefix', 'new_path'):
        broken = copy.deepcopy(result)
        if mutation == 'count':
            broken['counts']['team_steps'] -= 112
        elif mutation == 'old_row':
            broken['rows'][0]['steps'] = 255
        elif mutation == 'order':
            broken['rows'][6], broken['rows'][7] = broken['rows'][7], broken['rows'][6]
        elif mutation == 'failed_prefix':
            broken['exposure']['failed_prefix_steps'] = 0
        else:
            broken['rows'][-1]['raw']['path'] = str(study.PARENT / 'raw/forged.npz')
        with pytest.raises(RuntimeError):
            validate_summary(out, broken, parent)
    with pytest.raises(RuntimeError, match='already contains science'):
        study.run_batch(out, 'a' * 40, entry_start=time.perf_counter(), admission={})


def test_failure_preserves_original_and_does_not_retry(parent, tmp_path, monkeypatch):
    called, captures = mock_collection(monkeypatch, parent, fail=True)
    result = study.run_batch(tmp_path / 'failed', 'b' * 40, entry_start=time.perf_counter(), admission={})
    assert called == [('R', 29322001)]
    assert captures == [(TypeError, 'synthetic original failure')]
    assert result['status'] == 'INCOMPLETE_TECHNICAL_FAILURE' and result['parent_unchanged']
    assert result['counts']['team_steps'] == 112 and result['counts']['complete_episodes'] == 0
    assert result['rows'] == parent['rows'] and len(result['new_artifacts']) == 1
    assert result['exposure']['total_result_steps'] == 1760
    assert result['exposure']['failed_prefix_steps'] == 224
    assert study.validate_parent() == parent


def test_refuses_parent_as_output(parent):
    with pytest.raises(RuntimeError, match='overlaps protected parent'):
        study.run_batch(study.PARENT, 'c' * 40, entry_start=time.perf_counter(), admission={})


def test_proof_is_fixed_source_input_when_runs_is_omitted(tmp_path):
    # Native snapshots inherit sparse selection. This run input is absent from
    # the source worktree, and launcher output is a separate canonical path.
    snapshot = tmp_path / 'snapshot'
    package = snapshot / 'experiments/candidates/uav_user_waiting/b02_continuation'
    (package / 'inputs').mkdir(parents=True)
    canonical_out = tmp_path / 'canonical/runs/uav_user_waiting/b02_continuity_a03'
    canonical_out.mkdir(parents=True)
    source = package / 'study.py'
    source.write_bytes(Path(study.__file__).read_bytes())
    proof = package / 'inputs/parent-reading.json'
    proof.write_bytes(study.PROOF.read_bytes())
    assert not (snapshot / 'runs/uav_user_waiting/b02_continuity_a01/failure-reading.json').exists()
    assert not (canonical_out.parent / 'b02_continuity_a01/failure-reading.json').exists()
    spec = importlib.util.spec_from_file_location(
        'experiments.candidates.uav_user_waiting.b02_continuation.snapshot_scope', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == snapshot and module.PROOF == proof
    assert module.check_digest(module.PROOF, module.PROOF_HASH)['sha256'] == study.PROOF_HASH
    assert module.read_json(module.PROOF)['verified_native_steps'] == 1648
    # The same source-bound guard still fails closed on an altered proof.
    proof.write_bytes(proof.read_bytes() + b'\n')
    with pytest.raises(RuntimeError, match='digest mismatch'):
        module.check_digest(module.PROOF, module.PROOF_HASH)
