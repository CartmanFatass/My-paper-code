"""Artifact and admission binding without model, fit or environment calls."""
import sys
from types import SimpleNamespace

import pytest

from experiments.candidates.uav_user_waiting.b03_reader import run
from scripts import hmasd_admission


def arguments(path, *, sha='reader-sha'):
    return ['--out', str(path.parent / 'reader'), '--generic-summary', str(path),
            '--worker-summary-sha256', 'a' * 64, '--launch-sha', sha,
            '--seed', '29423000']


def test_admitted_adapter_keeps_producer_and_reader_identity_separate(tmp_path, monkeypatch):
    summary = tmp_path / 'summary.json'
    summary.write_text('{}')
    events = []

    def admit(path, *, direction):
        events.append(('admit', path, direction))
        return {'sha': 'reader-sha', 'child_pid': 123}

    def read(parent, **kwargs):
        events.append(('read', parent, kwargs))
        return {'status': 'VERIFIED_COMPLETE'}

    monkeypatch.setattr(hmasd_admission, 'require_admission', admit)
    monkeypatch.setitem(sys.modules, 'experiments.candidates.uav_user_waiting.b03.read',
                        SimpleNamespace(read_result=read))
    assert run.main(arguments(summary)) == {'status': 'VERIFIED_COMPLETE'}
    assert events[0] == ('admit', run.__file__, 'uav_user_waiting')
    assert events[1] == ('read', tmp_path, {
        'reading_out': tmp_path / 'reader',
        'admission': {'sha': 'reader-sha', 'child_pid': 123},
        'expected_summary_sha256': 'a' * 64,
        'expected_launch_sha': 'a045bc9b4e3ba9ef211474293c4bc43ad8b16b08',
    })


def test_source_mismatch_stops_before_reading(tmp_path, monkeypatch):
    summary = tmp_path / 'summary.json'
    summary.write_text('{}')
    monkeypatch.setattr(hmasd_admission, 'require_admission',
                        lambda *a, **k: {'sha': 'different-sha'})
    monkeypatch.setitem(sys.modules, 'experiments.candidates.uav_user_waiting.b03.read',
                        SimpleNamespace(read_result=lambda *a, **k: pytest.fail('reader called')))
    with pytest.raises(RuntimeError, match='admission/source mismatch'):
        run.main(arguments(summary))


@pytest.mark.parametrize('name,digest', [('other.json', 'a' * 64), ('summary.json', 'X' * 64)])
def test_invalid_artifact_arguments_stop_before_admission(tmp_path, monkeypatch, name, digest):
    monkeypatch.setattr(hmasd_admission, 'require_admission',
                        lambda *a, **k: pytest.fail('admission called'))
    argv = arguments(tmp_path / name)
    argv[argv.index('--worker-summary-sha256') + 1] = digest
    with pytest.raises(SystemExit) as exc:
        run.main(argv)
    assert exc.value.code == 2
