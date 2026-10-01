"""Constructed certificate and immutable-byte failures; no scientific queries."""
from copy import deepcopy
from dataclasses import replace

import numpy as np
import pytest

from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse import inputs, reader, segment
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import cycle
from test_segment import history, synthetic


def certificate_fixture(monkeypatch, *, reuse=True, first=False, arrival=False):
    deps, _, _ = synthetic(monkeypatch, plan_motion=arrival)

    class Scores:
        def __init__(self, users):
            self.counts = {key: 0 for key in inputs.COUNT_KEYS}

        def score(self, positions, masks):
            unique = len({row.tobytes() for row in positions})
            self.counts.update(requested_candidates=1, scored_candidates=1,
                               geometry_rows_computed=unique, geometry_rows_reused=8-unique)
            return [dict(J=.3, served=1, quality=.2, energy_penalty=0.)]

    deps = replace(deps, scorer=Scores)
    monkeypatch.setattr(segment.b04, '_Scores', Scores)
    start, end = (40, 500) if first else (120, 240)
    c, report = history(start)
    plan = None
    if arrival:
        plan = dict(initiated=True, start_t=start, arrival_t=start+40, duration=40,
                    member=7, site=9, commands=np.zeros((40, 8, 3), np.float32).tolist(),
                    predicted_destination=c.positions.tolist())
    local = 'm7_s9' if arrival else 'stay'
    identifier = f'actual/t{start}/branch/{local}'
    if first:
        assert not arrival
        for module in (cycle, segment.b03):
            monkeypatch.setattr(module, 'Program', deps.program)
            monkeypatch.setattr(module, '_Scores', Scores)
            monkeypatch.setattr(module, 'predict_next', deps.predict)
        original = segment.b03.simulate_continuation(c, report, 1)
        result = cycle.simulate_continuation(c, report, 1) if reuse else deepcopy(original)
        work = result.pop('reuse', None)
        segment.certify(result, c, report, 1, None, start, end, reuse=work)
    else:
        original = segment.simulate_segment(c, report, 1, plan, start_t=start, end_t=end)
        result = segment.simulate_segment(c, report, 1, plan, start_t=start, end_t=end,
                                          reuse=reuse, dependencies=deps)
    inputs.same_payload(result, original, 'independent synthetic original')
    reference = inputs.SegmentReference(original, start, end, c.commands.copy(), 1,
                                         c.users.copy(), 'actual', {})
    record = dict(id=identifier, certificate=deepcopy(result['certificate']),
                  scientific=inputs.payload_binding(result))
    return identifier, record, reference


@pytest.mark.parametrize('first,reuse,arrival', [(False, False, False), (False, True, False),
                                               (False, True, True), (True, False, False), (True, True, False)])
def test_independent_certificate_accepts_exact_synthetic_state_and_ledgers(monkeypatch, first, reuse, arrival):
    identifier, record, reference = certificate_fixture(monkeypatch, first=first, reuse=reuse, arrival=arrival)
    result = reader.verify_certificate(identifier, record, reference, reuse)
    assert result['computed_ticks'] + result['reused_ticks'] == reference.end-reference.start
    assert (result['reused_ticks'] > 0) is reuse
    if first and reuse:
        # This C-only continuation crosses numeric120 with its same cache.
        assert record['certificate']['reuse']['source_times'][120-40] < 120
        assert record['certificate']['reuse']['key_layout'] == reader.B06_KEY_LAYOUT


@pytest.mark.parametrize('field', ['terminal_command', 'terminal_clock', 'entry_physical',
                                  'barrier', 'source_clock', 'actual_reward_count', 'first_hash', 'schema'])
def test_tampered_terminal_key_source_or_ledger_is_rejected(monkeypatch, field):
    identifier, record, reference = certificate_fixture(monkeypatch)
    cert = record['certificate']
    if field == 'terminal_command':
        cert['terminal']['commands']['hex'] = np.zeros((8, 3), np.float32).tobytes().hex()
    elif field == 'terminal_clock':
        cert['terminal']['next_t'] -= 1
    elif field == 'entry_physical':
        value = reference.payload['arrays']['positions'][0].copy()
        value[0, 0] = np.nextafter(value[0, 0], np.inf)
        cert['entry']['physical'] = segment.encode_array(value)
    elif field == 'barrier':
        cert['reuse']['eligibility_after_t'] = 40
    elif field == 'source_clock':
        cert['reuse']['source_times'][41] = 120
    elif field == 'actual_reward_count':
        cert['reuse']['actual_reward_counts']['requested_candidates'] += 1
    elif field == 'first_hash':
        cert['reuse']['first_repeat']['key_sha256'] = '0'*64
    else:
        cert['reuse']['key_layout'] = reader.B06_KEY_LAYOUT
    with pytest.raises(ValueError):
        reader.verify_certificate(identifier, record, reference, True)


def test_arrival_barrier_and_public_report_clock_are_independent(monkeypatch):
    identifier, record, reference = certificate_fixture(monkeypatch, arrival=True)
    record['certificate']['plan']['arrival_t'] -= 10
    with pytest.raises(ValueError, match='arrival boundary'):
        reader.verify_certificate(identifier, record, reference, True)


def test_recoverable_full_plan_metadata_is_bound(monkeypatch):
    identifier, record, reference = certificate_fixture(monkeypatch, arrival=True)
    reference.plan_bound = True
    reference.expected_plan = deepcopy(record['certificate']['plan'])
    record['certificate']['plan']['predicted_destination'][0][0] += 1.
    with pytest.raises(ValueError, match='full recoverable original plan'):
        reader.verify_certificate(identifier, record, reference, True)
    identifier, record, reference = certificate_fixture(monkeypatch)
    reference.payload['arrays']['reports'][1, -1] = np.float32(.5)
    record['scientific'] = inputs.payload_binding(reference.payload)
    with pytest.raises(ValueError, match='absolute report'):
        reader.verify_certificate(identifier, record, reference, True)


def test_array_bits_and_records_preserve_signed_zero_dtype_and_order():
    zero = np.zeros((2, 3), np.float32)
    for changed in (zero.astype(np.float64), zero.reshape(3, 2), -zero):
        with pytest.raises(ValueError):
            inputs.same_array(changed, zero, 'required bits')
    inputs.same_record({'x': [1, 2], 'y': 0.}, {'y': 0., 'x': [1, 2]}, 'dict order ignored')
    for changed in ({'x': [2, 1], 'y': 0.}, {'x': [1, 2], 'y': -0.}, {'x': [1, 2], 'y': 0}):
        with pytest.raises(ValueError):
            inputs.same_record(changed, {'x': [1, 2], 'y': 0.}, 'scientific record')


def test_external_input_path_binding_refuses_tamper_and_escape(tmp_path):
    base = tmp_path/'bulk'; base.mkdir()
    original = base/'bound.bin'; original.write_bytes(b'original')
    binding = inputs.artifact(original, base)
    assert inputs.checked_file(base, binding) == original
    original.write_bytes(b'modified')
    with pytest.raises(ValueError):
        inputs.checked_file(base, binding)
    outside = tmp_path/'outside'; outside.write_bytes(b'original')
    (base/'link').symlink_to(outside)
    for name in ('link', '../outside', str(outside)):
        with pytest.raises(ValueError):
            inputs.checked_file(base, dict(binding, path=name))


def test_outer_split_recovers_index80_state_index79_command_and_removes_only_annotation():
    arrays = {
        'positions': np.arange(461*24, dtype=np.float64).reshape(461, 8, 3),
        'controller_estimates': np.arange(461*24, dtype=np.float64).reshape(461, 8, 3)+.5,
        'actions': np.arange(460*24, dtype=np.float32).reshape(460, 8, 3),
        'masks': np.arange(460, dtype=np.int64),
        'reward_components': np.zeros((460, 4), np.float64),
        'report_times': np.arange(40, 500, 10, dtype=np.int64),
        'reports': np.zeros((46, 133), np.float32)}
    arrays['reports'][:, 32:132] = .2
    decisions = [dict(t=t, sentinel=[t]) for t in range(40, 500)]
    selection = dict(selected_branch='stay', selected_plan={'initiated': False})
    decisions[80]['predicted_temporal_selection'] = deepcopy(selection)
    whole = dict(arrays=arrays, decisions=decisions,
                 summary={'segments': [{'start_t': 40}, {'start_t': 120}],
                          'inner_selection': selection})
    inner = deepcopy(whole)
    inner['arrays'] = {name: value[80:].copy() for name, value in arrays.items()
                       if name not in ('reports', 'report_times')}
    inner['arrays']['positions'][0, 0, 0] += 1.
    inner['summary'] = dict(start_t=120, end_t=500, horizon=500, identity={})
    ref = inputs.ReferenceEpisode.__new__(inputs.ReferenceEpisode)
    ref.native = dict(actions=np.zeros((500, 8, 3), np.float32),
                      mask=np.full(500, 255, np.int64), states=np.zeros((501, 133), np.float32))
    ref.branch = lambda identifier: whole if identifier.endswith('/outer') else inner
    ref.branches = {'a2/first/stay/outer': {}, 'a2/first/stay/inner/stay': {}}
    ref.catalog = dict(selections={'40': dict(branches=[dict(id='stay', plan=None)])})
    prefix = ref.segment('a2/first/stay/prefix')
    suffix = ref.segment('a2/first/stay/suffix')
    nested = ref.segment('a2/first/stay/inner/stay')
    assert prefix.payload['arrays']['positions'].shape == (81, 8, 3)
    assert suffix.payload['arrays']['positions'].shape == (381, 8, 3)
    inputs.same_array(suffix.entry_commands, arrays['actions'][79], 'entering commands')
    assert suffix.entry_mask == 79 and nested.entry_mask == 79
    inputs.same_array(suffix.payload['arrays']['controller_estimates'][0], arrays['controller_estimates'][80], 'entering estimate')
    assert suffix.payload['decisions'][0] == dict(t=120, sentinel=[120])
    assert 'predicted_temporal_selection' in whole['decisions'][80]
    assert nested.payload['arrays']['positions'][0, 0, 0] != suffix.payload['arrays']['positions'][0, 0, 0]
    assert prefix.plan_bound and prefix.expected_plan is None
    assert suffix.plan_bound and suffix.expected_plan == selection['selected_plan']
    assert nested.plan_bound and nested.expected_plan is None


def test_expected_segment_emission_order_inserts_only_prefix_and_suffix():
    ids = ['a2/first/stay/inner/stay', 'a2/first/stay/inner/m7_s9', 'a2/first/stay/outer',
           'a2/first/m7_s9/inner/stay', 'a2/first/m7_s9/outer', 'actual/t120/branch/stay']
    catalog = dict(model_branches=[dict(id=value) for value in ids])
    assert reader.expected_segments(catalog, 'A2') == [
        'a2/first/stay/prefix', *ids[:2], 'a2/first/stay/suffix',
        'a2/first/m7_s9/prefix', ids[3], 'a2/first/m7_s9/suffix', ids[-1]]


def test_reader_dependency_graph_has_no_scientific_query_imports():
    import ast
    from pathlib import Path
    for module in (reader, inputs):
        tree = ast.parse(Path(module.__file__).read_text())
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert all(name in {'copy', 'dataclasses', 'pathlib', 'inputs'} for name in imports)
