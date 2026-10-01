"""Harness and admission tests with a fully synthetic, query-free controller."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse import inputs, reader, run, study


def install_toy(monkeypatch, failure=None):
    states = np.zeros((501, 133), np.float32)
    states[:, -1] = np.arange(501, dtype=np.float32)/500
    commands = np.zeros((500, 8, 3), np.float32)
    decisions = [dict(t=t, old_mask=255, issued_mask=255, phase='ordinary') for t in range(500)]
    catalog = dict(plans={'40': {'a': 1}, '120': {'b': 2}},
                   selections={'40': {'c': 3}, '120': {'d': 4}}, banks={},
                   model_branches=[], candidate_banks=[])
    original_row = dict(raw={'path': 'synthetic'}, metrics={'synthetic': True},
                        costs={key: 0 for key in inputs.LOGICAL_COSTS},
                        native_candidate_counts=study._counts(), calls={kind: 0 for kind in inputs.KINDS},
                        position_predictions=0)
    expected_segment = dict(arrays={'test': np.ones(1, np.float64)}, summary={}, decisions=[])
    reference = SimpleNamespace(native=dict(states=states, actions=commands, mask=np.full(500, 255, np.int64)),
                                decisions=decisions, catalog=catalog, row=original_row,
                                segment=lambda identifier: SimpleNamespace(payload=expected_segment))
    calls = []

    class Toy:
        def __init__(self, arm, *, branch_sink, candidate_sink, reuse, segment_sink):
            self.controller = SimpleNamespace(next_t=0, positions=np.zeros((8, 3), np.float64),
                                              users=np.zeros((50, 2), np.float64), commands=commands[0].copy())
            self.plans = {40: {'a': 1}, 120: {'b': 2}}
            self.selections = {40: {'c': 3}, 120: {'d': 4}}
            self.banks = {}
            self.segment_sink = segment_sink

        def select(self, t, state, old_mask):
            calls.append(t)
            assert (state is not None) == (t % 10 == 0)
            if state is not None:
                inputs.same_array(state, states[t], 'only current lawful report')
            if failure == 'segment' and t == 40:
                self.segment_sink('actual/t40/branch/stay',
                                  dict(arrays={'test': np.zeros(1, np.float64)}, summary={}, decisions=[], certificate={}))
                raise AssertionError('mismatched segment returned to policy')
            command = commands[t].copy()
            if failure == 'command' and t == 23:
                command = command.astype(np.float64)
                command[0, 0] = np.nextafter(np.float64(0), np.float64(1))
            self.controller.commands = command.copy()
            self.controller.next_t = t+1
            return command, old_mask, deepcopy(decisions[t])

    monkeypatch.setattr(study, 'TemporalProgram', Toy)
    monkeypatch.setattr(study, 'execution_context', lambda: {'synthetic': True})
    return SimpleNamespace(episode=lambda *args: reference), calls


def test_full500_clock_harness_normalizes_two_clock_catalog_and_preserves_outputs(monkeypatch, tmp_path):
    originals, calls = install_toy(monkeypatch)
    row = study.replay_history('G2_original', 1, tmp_path, originals)
    assert calls == list(range(500)) and row['steps'] == 500 and row['complete'] is True
    assert row['error'] is None and row['timing']['cpu_seconds'] > 0
    catalog = inputs.load_catalog(inputs.checked_file(tmp_path, row['evidence_catalog']))
    assert catalog['plans'] == {'40': {'a': 1}, '120': {'b': 2}}
    assert row['final_history']['next_t'] == 500
    assert inputs.load_trace(inputs.checked_file(tmp_path, row['decisions']))[-1]['t'] == 499


@pytest.mark.parametrize('failure,last_clock', [('command', 23), ('segment', 40)])
def test_first_mismatch_stops_and_retains_unique_partial_bits(monkeypatch, tmp_path, failure, last_clock):
    originals, calls = install_toy(monkeypatch, failure)
    with pytest.raises(ValueError, match='mismatch'):
        study.replay_history('A2_reuse', 1, tmp_path, originals)
    assert calls == list(range(last_clock+1))
    row = json.loads((tmp_path/'first-failure.json').read_text())
    assert row['complete'] is False and row['error'].startswith('ValueError')
    root = tmp_path/'raw/n8_A2_reuse_w1/first-mismatch'
    if failure == 'command':
        arrays = inputs.load_arrays(root/'command_t23.npz')
        assert arrays['actual'].dtype == np.float64
        assert arrays['actual'][0, 0] == np.nextafter(np.float64(0), np.float64(1))
        assert arrays['expected'].dtype == np.float32
        assert row['steps'] == 24
    else:
        arrays = inputs.load_arrays(root/'actual/t40/branch/stay.npz')
        assert arrays['test'].tobytes() == np.zeros(1, np.float64).tobytes()
        assert row['steps'] == 40


def test_terminal_pair_mismatch_stops_before_next_history(monkeypatch, tmp_path):
    originals = SimpleNamespace(config={'source_bindings': {}}, sources={}, binding=lambda: {})
    monkeypatch.setattr(study, 'OriginalInputs', lambda *args: originals)
    monkeypatch.setattr(study, 'fixed_config', lambda value: {})
    monkeypatch.setattr(study.torch, 'set_num_threads', lambda value: None)
    monkeypatch.setattr(study.torch, 'set_num_interop_threads', lambda value: None)
    monkeypatch.setattr(study, 'execution_context', lambda: {})
    calls = []

    def replay(variant, world, out, inputs):
        calls.append((variant, world))
        return dict(variant=variant, arm=variant.split('_')[0], world_id=world,
                    final_history={'private_estimate': len(calls)}, timing={'cpu_seconds': 0})

    monkeypatch.setattr(study, 'replay_history', replay)
    with pytest.raises(ValueError, match='terminal-history pair'):
        study.run_study(tmp_path, 'a'*40, {'command_sha256': 'digest'}, 'records', 'bulk')
    assert calls == [('G2_original', inputs.WORLD_IDS[0]), ('G2_reuse', inputs.WORLD_IDS[0])]
    summary = json.loads((tmp_path/'summary.json').read_text())
    assert summary['status'] == 'failed' and len(summary['histories']) == 2


@pytest.mark.parametrize('mode', ['refused', 'wrong_sha', 'accepted'])
def test_entry_admission_precedes_output_or_study_effects(monkeypatch, tmp_path, mode):
    from scripts import hmasd_admission
    out = tmp_path/inputs.TAG
    monkeypatch.setattr(sys, 'argv', ['run.py', '--out', str(out), '--launch-sha', 'a'*40,
                                     '--seed', str(inputs.SEED), '--original-records', str(tmp_path/'original'),
                                     '--original-bulk', str(tmp_path/'bulk')])
    events = []

    def admission(script, *, direction):
        events.append('admission')
        assert Path(script) == Path(run.__file__) and direction == inputs.DIRECTION
        assert not out.exists()
        if mode == 'refused':
            raise ValueError('synthetic refusal')
        return dict(sha=('b' if mode == 'wrong_sha' else 'a')*40, command_sha256='synthetic')

    def execute(*args, **kwargs):
        events.append('study')
        assert len(args) == 5 and kwargs['entry_mark'][0] > 0
        assert not out.exists()

    monkeypatch.setattr(hmasd_admission, 'require_admission', admission)
    monkeypatch.setattr(study, 'run_study', execute)
    if mode == 'accepted':
        run.main()
        assert events == ['admission', 'study']
    else:
        with pytest.raises(ValueError):
            run.main()
        assert events == ['admission']
    assert not out.exists()
