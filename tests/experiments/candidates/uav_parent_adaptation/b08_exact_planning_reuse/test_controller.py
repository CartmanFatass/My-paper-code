"""Selector and sink checks using synthetic menus, transitions and rewards."""
from copy import deepcopy
import inspect

import numpy as np
import pytest

from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse import controller as candidate, segment
from experiments.candidates.uav_fleet_transmission.b04 import controller as frozen
from experiments.candidates.uav_fleet_transmission.b03 import controller as first
from test_segment import history, synthetic, decode


def bank(start=40):
    c, _ = history(start)
    counts = {k:0 for k in segment.COUNT_KEYS}
    commands=np.zeros((10,8,3),np.float32)
    commands[0,7,0]=1
    destination=c.positions.copy(); destination[7,0]+=30
    plan = dict(start_t=start,initiated=True,member=7,site=0,duration=10,arrival_t=start+10,
        commands=commands.tolist(), predicted_destination=destination.tolist(),
        predicted_mask=128, selected=dict(path=0.,member=7,site=0,duration=10),
        predicted_total_J=0.,predicted_total_served=0,stay_total_J=0.,stay_total_served=0,
        counts=dict(counts,model_ticks=10),candidate_count=1,candidate_digest='synthetic',digest_layout=[])
    return dict(original_R=plan,champions=[plan],candidate_rows=np.zeros((1,40),dtype='<f8'))


def install(monkeypatch,plan_motion=False):
    deps, calls, scores = synthetic(monkeypatch,plan_motion=plan_motion)
    # All controller/model dependencies are synthetic; no paid worlds or C queries.
    monkeypatch.setattr(first,'Program',deps.program)
    monkeypatch.setattr(frozen,'OptionProgram',deps.program)
    for mod in (candidate.b03,candidate.cycle):
        monkeypatch.setattr(mod,'Program',deps.program)
        monkeypatch.setattr(mod,'_Scores',deps.scorer)
        monkeypatch.setattr(mod,'predict_next',deps.predict)
    monkeypatch.setattr(first,'enumerate_champions',lambda *args:bank())
    monkeypatch.setattr(frozen,'enumerate_champions',lambda p,u,m,t,h:bank(t))
    adapter = segment.simulate_segment
    monkeypatch.setattr(segment,'simulate_segment',lambda *a,**kw:adapter(*a,**kw,dependencies=deps))
    return calls,scores


@pytest.mark.parametrize('arm',['G2','A2'])
@pytest.mark.parametrize('reuse',[False,True])
@pytest.mark.parametrize('plan_motion',[False,True])
def test_all_clock_outputs_catalog_banks_and_sinks_match_frozen(monkeypatch,arm,reuse,plan_motion):
    install(monkeypatch,plan_motion)
    expected_branches, actual_branches, certificates = {},{},{}
    expected_candidates,actual_candidates = {},{}
    expected=frozen.TemporalProgram(arm,branch_sink=lambda key,p:expected_branches.setdefault(key,deepcopy(p)),
        candidate_sink=lambda key,rows:expected_candidates.setdefault(key,rows.copy()))
    def segment_sink(key,payload):
        certificates[key]=deepcopy(payload)
        payload['certificate']['terminal']['next_t']=-99
        payload['summary']['total_J']=1e99
        payload['arrays']['positions'][:]=-99
        payload['decisions'][0]['t']=-99
    def branch_sink(key,payload):
        actual_branches[key]=deepcopy(payload)
        assert set(payload)=={'arrays','summary','decisions'}
        payload['summary']['total_J']=1e99
        payload['arrays']['positions'][:]=-99
    def candidate_sink(key,rows):
        actual_candidates[key]=rows.copy()
        rows[:]=-99
    actual=candidate.TemporalProgram(arm,branch_sink=branch_sink,candidate_sink=candidate_sink,
        reuse=reuse,segment_sink=segment_sink)
    for t in range(500):
        report=history(t)[1] if t%10==0 else None
        out=actual.select(t,report,1)
        ref=expected.select(t,report,1)
        assert out[0].tobytes()==ref[0].tobytes()
        assert out[1:]==ref[1:]
        assert actual.controller.next_t==t+1
        for field in ('positions','users','commands'):
            assert getattr(actual.controller,field).tobytes()==getattr(expected.controller,field).tobytes()
    assert actual.plan==expected.plan
    assert actual.plans==expected.plans
    assert actual.selections==expected.selections
    assert actual.plan['initiated']==plan_motion
    assert actual.banks==expected.banks
    assert set(actual_branches)==set(expected_branches)
    for key,payload in actual_branches.items():
        ref=expected_branches[key]
        assert payload['summary']==ref['summary']
        assert payload['decisions']==ref['decisions']
        for name,value in payload['arrays'].items():
            assert value.dtype==ref['arrays'][name].dtype
            assert value.tobytes()==ref['arrays'][name].tobytes()
    for key,rows in actual_candidates.items():
        assert rows.tobytes()==expected_candidates[key].tobytes()
    if arm=='G2':
        assert set(certificates)==set(actual_branches)
        if reuse:
            assert certificates['actual/t40/branch/stay']['certificate']['reuse']['key_layout']==candidate.cycle.KEY_LAYOUT
    else:
        assert set(certificates)=={
            'a2/first/stay/prefix','a2/first/m7_s0/prefix',
            'a2/first/stay/inner/stay','a2/first/stay/inner/m7_s0',
            'a2/first/m7_s0/inner/stay','a2/first/m7_s0/inner/m7_s0',
            'a2/first/stay/suffix','a2/first/m7_s0/suffix',
            'actual/t120/branch/stay','actual/t120/branch/m7_s0'}
        for local in ('stay','m7_s0'):
            outer=actual_branches[f'a2/first/{local}/outer']
            prefix=certificates[f'a2/first/{local}/prefix']
            suffix=certificates[f'a2/first/{local}/suffix']
            for name in ('actions','masks','reward_components'):
                assert prefix['arrays'][name].tobytes()==outer['arrays'][name][:80].tobytes()
                assert suffix['arrays'][name].tobytes()==outer['arrays'][name][80:].tobytes()
            assert prefix['certificate']['terminal']==suffix['certificate']['entry']
    for key,payload in certificates.items():
        cert=payload['certificate']
        assert cert['entry']['next_t']==cert['start_t']
        assert cert['terminal']['next_t']==cert['end_t']
        assert decode(cert['terminal']['commands']).tobytes()==payload['arrays']['actions'][-1].tobytes()
        assert decode(cert['terminal']['positions']).tobytes()==payload['arrays']['controller_estimates'][-1].tobytes()
        if not reuse:
            assert cert['reuse']['computed_ticks']==cert['end_t']-cert['start_t']
            assert cert['reuse']['reused_ticks']==0
        assert 'certificate' not in payload['summary'] and 'reuse' not in payload['summary']


def test_original_bindings_and_emission_before_terminal_consumption(monkeypatch):
    install(monkeypatch)
    b03_sim=candidate.b03.simulate_continuation
    b04_sim=segment.b04.simulate_segment
    calls=[]
    def original_first(*a,**kw):
        calls.append('b03')
        return b03_sim(*a,**kw)
    def original_segment(*a,**kw):
        calls.append('b04')
        return b04_sim(*a,**kw)
    def forbidden(*a,**kw):
        raise AssertionError('reuse path called in original mode')
    monkeypatch.setattr(candidate.b03,'simulate_continuation',original_first)
    monkeypatch.setattr(segment.b04,'simulate_segment',original_segment)
    monkeypatch.setattr(candidate.cycle,'simulate_continuation',forbidden)
    emitted=[]
    def sink(key,payload):
        emitted.append(key)
        # Emitted prefix must precede the first inner selection; suffix must
        # follow that inner search and retain the previously certified entry.
        if key.endswith('/inner/stay'):
            assert key.replace('/inner/stay','/prefix') in emitted
        if key.endswith('/suffix'):
            assert key.replace('/suffix','/inner/stay') in emitted
    g=candidate.TemporalProgram('G2',segment_sink=sink)
    g.base.controller=history(40)[0]
    g.select(40,history(40)[1],1)
    assert calls==['b03','b03']
    a=candidate.TemporalProgram('A2',segment_sink=sink)
    a.base.controller=history(40)[0]
    a.select(40,history(40)[1],1)
    assert calls[2:]==['b04']*8
    # Binding verification never alters frozen source/module call references.
    assert frozen.simulate_segment is not segment.simulate_segment
    assert inspect.signature(candidate.TemporalProgram).parameters['reuse'].kind==inspect.Parameter.KEYWORD_ONLY


def test_sink_observes_unrounded_outer_and_decoded_inner(monkeypatch):
    install(monkeypatch)
    adapter=segment.simulate_segment
    def inject_rounding(*a,**kw):
        result=adapter(*a,**kw)
        if kw.get('end_t')==120:
            result['arrays']['positions'][-1,0,0]=np.nextafter(result['arrays']['positions'][-1,0,0],np.inf)
            # Update synthetic prefix terminal physical certificate consistently.
            result['certificate']['terminal']['physical']=segment.encode_array(result['arrays']['positions'][-1])
        return result
    monkeypatch.setattr(segment,'simulate_segment',inject_rounding)
    emitted={}
    a=candidate.TemporalProgram('A2',reuse=True,segment_sink=lambda k,v:emitted.setdefault(k,deepcopy(v)))
    a.base.controller=history(40)[0]
    a.select(40,history(40)[1],1)
    for local in ('stay','m7_s0'):
        prefix=emitted[f'a2/first/{local}/prefix']['certificate']
        inner=emitted[f'a2/first/{local}/inner/stay']['certificate']
        suffix=emitted[f'a2/first/{local}/suffix']['certificate']
        assert suffix['entry']['physical']==prefix['terminal']['physical']
        assert inner['entry']['physical']!=prefix['terminal']['physical']
        assert suffix['entry']['positions']==inner['entry']['positions']


@pytest.mark.parametrize('arm,horizon',[('T',500),('G2',120),('bad',500)])
def test_fixed_public_contract(arm,horizon):
    with pytest.raises(ValueError):
        candidate.TemporalProgram(arm,horizon)
