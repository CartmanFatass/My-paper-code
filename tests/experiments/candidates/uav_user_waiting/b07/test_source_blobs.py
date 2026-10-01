"""Pinned source reads in synthetic Git repositories; no scientific queries."""
import hashlib
import json
import subprocess

import pytest

from experiments.candidates.uav_user_waiting.b07 import protocol as p, study


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()


@pytest.fixture
def repository(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'user.email', 'synthetic@example.invalid')
    git(tmp_path, 'config', 'user.name', 'Synthetic fixture')
    path = tmp_path / p.B06_RESULT
    path.parent.mkdir(parents=True)
    data = b'{"evidence":"original"}\n'
    path.write_bytes(data)
    git(tmp_path, 'add', p.B06_RESULT)
    git(tmp_path, 'commit', '-qm', 'original')
    source_sha = git(tmp_path, 'rev-parse', 'HEAD')
    path.write_text('{"evidence":"replacement"}\n')
    git(tmp_path, 'add', p.B06_RESULT)
    git(tmp_path, 'commit', '-qm', 'later')
    return tmp_path, path, data, source_sha


@pytest.mark.parametrize('working_file', ['modified', 'absent'])
def test_accepted_blob_ignores_later_head_and_working_files(repository, working_file):
    root, path, data, sha = repository
    if working_file == 'absent':
        path.unlink()
    else:
        path.write_text('not JSON and not the accepted bytes')
    reads = []
    value, identity = p._bound_source_json(p.B06_RESULT, hashlib.sha256(data).hexdigest(),
                                          root=root, source_sha=sha, source_reads=reads)
    assert value == json.loads(data) and identity['source_commit'] == sha
    assert identity['bytes'] == len(data) and reads[0]['status'] == 'VERIFIED'
    assert all(reads[0][key] >= 0 for key in ('wall_seconds', 'self_cpu_seconds', 'child_cpu_seconds'))


@pytest.mark.parametrize('failure', ['wrong_hash', 'wrong_commit', 'mutable_head', 'missing_commit'])
def test_no_commit_or_content_substitution_and_failure_is_charged(repository, failure):
    root, path, data, sha = repository
    digest = hashlib.sha256(data).hexdigest()
    if failure == 'wrong_hash':
        digest = '0' * 64
    elif failure == 'wrong_commit':
        sha = git(root, 'rev-parse', 'HEAD')
    elif failure == 'mutable_head':
        sha = 'HEAD'
    else:
        sha = '0' * 40
    reads = []
    with pytest.raises(ValueError):
        p._bound_source_json(p.B06_RESULT, digest, root=root, source_sha=sha, source_reads=reads)
    assert len(reads) == 1 and reads[0]['status'] == 'FAILED'
    assert reads[0]['source_commit'] == sha
    assert all(reads[0][key] >= 0 for key in ('wall_seconds', 'self_cpu_seconds', 'child_cpu_seconds'))


def test_worker_retains_source_failure_before_any_environment_call(monkeypatch, tmp_path):
    monkeypatch.setattr(study.torch, 'set_num_threads', lambda n: None)
    monkeypatch.setattr(study.torch, 'set_num_interop_threads', lambda n: None)
    def unavailable(baseline, *, source_sha, source_reads):
        assert source_sha == 'a' * 40
        source_reads.append(dict(status='FAILED', source_commit=source_sha))
        raise ValueError('missing accepted blob')
    monkeypatch.setattr(p, 'load_baselines', unavailable)
    def forbidden(seed):
        pytest.fail('reference failure must precede all native/controller work')
    monkeypatch.setattr(study, 'factory', forbidden)
    result = study.run_batch(tmp_path, 'synthetic', 'a' * 40)
    assert result['status'] == 'INCOMPLETE_TECHNICAL_FAILURE'
    assert result['reference_source_reads'] == [dict(status='FAILED', source_commit='a' * 40)]
    assert result['counts']['constructor_attempts'] == result['counts']['native_step_calls'] == 0
    assert json.loads((tmp_path / 'summary.json').read_text())['reference_source_reads'] == result['reference_source_reads']


def test_timed_out_git_retains_unverified_captured_prefix_and_diagnostics(monkeypatch, tmp_path):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 55, output=b'prefix', stderr=b'partial stderr')
    monkeypatch.setattr(p.subprocess, 'run', timeout)
    reads = []
    with pytest.raises(subprocess.TimeoutExpired):
        p._bound_source_json(p.B06_RESULT, 'a' * 64, root=tmp_path,
                             source_sha='b' * 40, source_reads=reads)
    assert reads[0]['status'] == 'FAILED' and reads[0]['bytes'] == len(b'prefix')
    assert reads[0]['observed_sha256'] == hashlib.sha256(b'prefix').hexdigest()
    assert reads[0]['stderr'] == 'partial stderr'
    assert not reads[0]['stdout_complete'] and reads[0]['timed_out']
    assert reads[0]['returncode'] is None
