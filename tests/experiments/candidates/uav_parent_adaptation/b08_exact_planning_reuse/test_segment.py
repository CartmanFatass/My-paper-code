"""Constructed histories with synthetic transition/scorer work only."""
from copy import deepcopy
import hashlib

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.control import OrdinaryController, decode_public_state, predict_next
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse import segment


def history(start=40):
    report = np.zeros(133, np.float32)
    report[:24].reshape(8, 3)[:, :2] = .5
    report[24:32] = 1
    report[32:132] = np.linspace(.1, .9, 100, dtype=np.float32)
    report[-1] = np.float32(start/500)
    controller = OrdinaryController(8)
    controller.positions, controller.users = decode_public_state(report, 8)
    controller.next_t = start
    return controller, report


def decode(value):
    return np.frombuffer(bytes.fromhex(value['hex']), dtype=value['dtype']).reshape(value['shape']).copy()


def synthetic(monkeypatch, *, clipping=False, drift=False, plan_motion=False):
    calls, scores = [], []
    last_t = [None]
    def predict(positions, command):
        moved = predict_next(positions, command)
        if drift:
            moved[0, 1] += 1e-10
        return moved

    class Program:
        def __init__(self, arm, horizon=500):
            self.controller = OrdinaryController(8)
            self.plan = None
            self.option_old_mask = None
        def select(self, t, state, old_mask):
            c = self.controller
            assert t == c.next_t
            assert (state is not None) == (t % 10 == 0)
            calls.append(t)
            last_t[0] = t
            if state is not None:
                c.positions, c.users = decode_public_state(state, 8)
            command = np.zeros((8, 3), np.float32)
            command[:, 1] = np.float32(-0.)
            if plan_motion and self.plan is not None and self.plan['initiated'] and t < self.plan['arrival_t']:
                command = np.asarray(self.plan['commands'][t-self.plan.get('start_t',40)],np.float32).copy()
            if clipping:
                command[:, 0] = -1
            c.commands = command.copy()
            c.positions = predict(c.positions, command)
            c.next_t += 1
            phase = 'ordinary'
            if self.plan is not None and self.plan['initiated']:
                phase = 'transit' if t < self.plan['arrival_t'] else 'arrival' if t == self.plan['arrival_t'] else 'ordinary'
            counts = dict(requested_candidates=2, scored_candidates=2, cached_candidates=0,
                          geometry_rows_computed=8, geometry_rows_reused=8)
            decision = dict(t=t, old_mask=int(old_mask), issued_mask=int(old_mask), phase=phase,
                motion=dict(counts, member_order=[(t+j) % 8 for j in range(8)], nested={'mutable':[t%40]}))
            if t % 10 == 0:
                decision['mask'] = dict(counts)
            return command, old_mask, decision

    class Scores:
        def __init__(self, users):
            self.counts = {key:0 for key in segment.COUNT_KEYS}
        def score(self, positions, masks):
            scores.append(last_t[0])
            self.counts.update(requested_candidates=1, scored_candidates=1, geometry_rows_computed=8)
            j = 1.+float(positions[7,0])/1000. if plan_motion else [1e16, 1., -1e16, .1][last_t[0]%4]
            return [dict(J=j, served=1, quality=.1, energy_penalty=.00375)]

    # Only tests substitute frozen module dependencies. Production has explicit bindings.
    monkeypatch.setattr(segment.b04, 'OptionProgram', Program)
    monkeypatch.setattr(segment.b04, '_Scores', Scores)
    monkeypatch.setattr(segment.b04, 'predict_next', predict)
    return segment.SegmentDependencies(Program, predict, Scores), calls, scores


def assert_equal(left, right):
    for key in left['arrays']:
        assert left['arrays'][key].dtype == right['arrays'][key].dtype
        assert left['arrays'][key].shape == right['arrays'][key].shape
        assert left['arrays'][key].tobytes() == right['arrays'][key].tobytes()
    assert left['summary'] == right['summary']
    assert left['decisions'] == right['decisions']
    assert left['certificate']['entry'] == right['certificate']['entry']
    assert left['certificate']['terminal'] == right['certificate']['terminal']


def assert_counts(result):
    cert = result['certificate']
    reuse, summary = cert['reuse'], result['summary']
    ticks = cert['end_t']-cert['start_t']
    assert reuse['computed_ticks']+reuse['reused_ticks'] == ticks
    assert reuse['logical_controller_calls'] == reuse['logical_reward_calls'] == ticks
    assert reuse['actual_controller_calls'] == reuse['actual_reward_calls'] == reuse['computed_ticks']
    assert reuse['logical_controller_counts'] == summary['controller_counts']
    assert reuse['logical_reward_counts'] == summary['reward_counts']
    assert reuse['logical_report_calls'] == reuse['actual_report_calls'] == len(result['arrays']['reports'])
    assert reuse['actual_requested_candidates'] == reuse['actual_controller_requests']+reuse['actual_reward_requests']
    assert reuse['actual_requested_candidates'] <= reuse['logical_requested_candidates']
    for t, source in zip(range(cert['start_t'], cert['end_t']), reuse['source_times']):
        assert source <= t
        if source != t:
            assert source > reuse['eligibility_after_t'] and source % 40 == t % 40
            assert reuse['source_times'][source-cert['start_t']] == source


@pytest.mark.parametrize('start,end', [(40,120),(120,500),(120,200)])
def test_exact_period40_reports_terminal_bits_and_ordered_reductions(monkeypatch, start, end):
    deps, calls, scores = synthetic(monkeypatch)
    c, report = history(start)
    initial = deepcopy(c)
    original = segment.simulate_segment(c, report, 1, start_t=start, end_t=end)
    calls.clear(); scores.clear()
    result = segment.simulate_segment(c, report, 1, start_t=start, end_t=end, reuse=True, dependencies=deps)
    assert_equal(original, result)
    assert_counts(result)
    work = result['certificate']['reuse']
    # First issued negative zero differs from the initial positive-zero history.
    assert work['first_repeat']['source_t'] == start+1
    assert work['first_repeat']['repeat_t'] == start+41
    assert work['first_repeat']['period'] == 40
    assert calls == scores == list(range(start,start+41))
    witness = deepcopy(c); witness.commands[:,1] = np.float32(-0.)
    key = segment.recurrence_key(start+1, result['arrays']['positions'][1], witness, 1, report)
    assert work['first_repeat']['key_sha256'] == hashlib.sha256(key).hexdigest()
    for report_t, state in zip(result['arrays']['report_times'], result['arrays']['reports']):
        assert state[-1] == np.float32(report_t/500)
        assert state[32:132].tobytes() == report[32:132].tobytes()
    assert [d['t'] for d in result['decisions']] == list(range(start,end))
    terminal = result['certificate']['terminal']
    assert terminal['next_t'] == end and terminal['n_uavs'] == 8 and terminal['mask'] == 1
    assert decode(terminal['positions']).tobytes() == result['arrays']['controller_estimates'][-1].tobytes()
    assert decode(terminal['commands']).tobytes() == result['arrays']['actions'][-1].tobytes()
    assert decode(terminal['physical']).tobytes() == result['arrays']['positions'][-1].tobytes()
    assert decode(terminal['users']).tobytes() == c.users.tobytes()
    expected = 0.
    for t in range(start,end):
        expected += [1e16,1.,-1e16,.1][t%4]
    assert result['summary']['total_J'] == expected
    assert c.next_t == initial.next_t and c.commands.tobytes() == initial.commands.tobytes()
    result['decisions'][41]['motion']['nested']['mutable'][0] = -1
    assert result['decisions'][1]['motion']['nested']['mutable'][0] != -1


def test_no_repeat_and_clipped_issued_history(monkeypatch):
    deps, calls, _ = synthetic(monkeypatch, drift=True)
    c, report = history()
    original = segment.simulate_segment(c, report, 1, end_t=120)
    calls.clear()
    result = segment.simulate_segment(c, report, 1, end_t=120, reuse=True, dependencies=deps)
    assert_equal(original,result)
    assert calls == list(range(40,120))
    assert result['certificate']['reuse']['reused_ticks'] == 0
    deps, _, _ = synthetic(monkeypatch, clipping=True)
    c,report=history(120)
    report[:24].reshape(8,3)[:,0] = 0
    c.positions,c.users = decode_public_state(report,8)
    result = segment.simulate_segment(c,report,1,start_t=120,reuse=True,dependencies=deps)
    assert np.all(result['arrays']['actions'][:,:,0] == -1)
    assert np.all(result['arrays']['positions'][:,:,0] == 0)
    assert result['summary']['total_path'] == 0
    assert np.all(decode(result['certificate']['terminal']['commands'])[:,0] == -1)


@pytest.mark.parametrize('start,end',[(40,120),(120,500)])
def test_arrival_strict_barrier_and_new_call_cache(monkeypatch,start,end):
    deps,calls,_ = synthetic(monkeypatch)
    c,report = history(start)
    plan = dict(start_t=start,initiated=True,duration=40,arrival_t=start+40,member=1,
        commands=np.zeros((40,8,3),np.float32),predicted_destination=c.positions.copy())
    original_plan=deepcopy(plan)
    result=segment.simulate_segment(c,report,1,plan,start_t=start,end_t=end,reuse=True,dependencies=deps)
    assert_counts(result)
    assert result['certificate']['reuse']['eligibility_after_t'] == start+40
    if end == 120:
        assert result['certificate']['reuse']['first_repeat'] is None
    else:
        assert result['certificate']['reuse']['first_repeat']['source_t'] == start+41
        assert result['certificate']['reuse']['first_repeat']['repeat_t'] == start+81
    assert calls == list(range(start,min(end,start+81)))
    calls.clear()
    segment.simulate_segment(c,report,1,plan,start_t=start,end_t=end,reuse=True,dependencies=deps)
    assert calls == list(range(start,min(end,start+81)))
    assert plan['commands'].tobytes() == original_plan['commands'].tobytes()


def test_all_recurrence_bits_and_exact_envelopes():
    c,report=history()
    pos=c.positions.copy()
    key=segment.recurrence_key(41,pos,c,1,report)
    assert key == segment.recurrence_key(81,pos,c,1,report)
    assert key != segment.recurrence_key(42,pos,c,1,report)
    assert key != segment.recurrence_key(41,pos,c,2,report)
    for field in ('physical','positions','users','commands','report'):
        for perturb in ('ulp','negative_zero'):
            local=deepcopy(c); p=pos.copy(); r=report.copy()
            value={'physical':p,'positions':local.positions,'users':local.users,'commands':local.commands,'report':r[32:132]}[field]
            value.flat[0] = np.nextafter(value.flat[0],np.array(np.inf,dtype=value.dtype)) if perturb=='ulp' else -0.
            assert key != segment.recurrence_key(41,p,local,1,r)
            assert decode(segment.encode_array(value)).tobytes() == value.tobytes()
    changed=report.copy(); changed[-1]=.9
    assert key == segment.recurrence_key(41,pos,c,1,changed)


def test_outer_unrounded_inner_decoded_and_invalid_entry(monkeypatch):
    deps,_,_=synthetic(monkeypatch)
    c,report=history(120)
    physical=c.positions.copy(); physical[0,0]=np.nextafter(physical[0,0],np.inf)
    outer=segment.simulate_segment(c,report,1,start_t=120,end_t=161,physical_positions=physical,reuse=True,dependencies=deps)
    inner=segment.simulate_segment(c,report,1,start_t=120,end_t=161,reuse=True,dependencies=deps)
    assert outer['arrays']['positions'][0].tobytes() == physical.tobytes()
    assert outer['certificate']['entry']['physical'] != inner['certificate']['entry']['physical']
    assert outer['certificate']['entry']['positions'] == inner['certificate']['entry']['positions']
    c.users[0,0]=np.nextafter(c.users[0,0],np.inf)
    with pytest.raises(ValueError,match='static public users'):
        segment.simulate_segment(c,report,1,start_t=120,reuse=True,dependencies=deps)


@pytest.mark.parametrize('kwargs',[{'start_t':80},{'end_t':40},{'end_t':501},{'end_t':500},{'report_horizon':120},{'start_t':True}])
def test_invalid_segment_contract(kwargs):
    c,report=history()
    with pytest.raises(ValueError):
        segment.simulate_segment(c,report,1,reuse=True,**kwargs)


@pytest.mark.parametrize('field,change',[
    ('positions','dtype'),('positions','shape'),('positions','finite'),
    ('users','dtype'),('users','shape'),('users','finite'),
    ('commands','dtype'),('commands','shape'),('commands','finite'),('commands','ternary')])
@pytest.mark.parametrize('reuse',[False,True])
def test_rejects_invalid_full_entry_before_model_work(monkeypatch,field,change,reuse):
    deps,calls,scores=synthetic(monkeypatch)
    c,report=history(120)
    value=getattr(c,field)
    if change=='dtype':
        value=value.astype(np.float64 if field=='commands' else np.float32)
    elif change=='shape':
        value=value[:-1]
    else:
        value=value.copy()
        value.flat[0]=np.nan if change=='finite' else .5
    setattr(c,field,value)
    with pytest.raises(ValueError):
        segment.simulate_segment(c,report,1,start_t=120,reuse=reuse,dependencies=deps)
    assert calls==scores==[]
