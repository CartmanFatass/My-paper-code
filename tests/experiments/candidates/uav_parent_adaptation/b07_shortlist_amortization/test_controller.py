"""Synthetic menus and mocked continuations: no native/model execution."""
from copy import deepcopy
import hashlib
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b03.option import branch_id, stationary_rank
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import controller as original
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import learning
from experiments.candidates.uav_parent_adaptation.b07_shortlist_amortization import controller as c


def public_report():
    r = np.ones(133, dtype=np.float32)
    r[:24] = np.tile([.5, .5, .5], 8)
    r[32:132] = .4
    r[-1] = .08
    return r


def fitted(intercept=0., duration_weight=0.):
    beta = [float(intercept)] + [0.] * 12
    beta[4] = duration_weight
    return dict(schema=learning.ARTIFACT_SCHEMA, beta=beta, means=[0.] * 12,
                scales=[1.] * 12, feature_names=list(learning.FEATURE_NAMES), penalty=.1)


def synthetic_bank(m=3):
    positions, _ = c.decode_public_state(public_report(), 8)
    counts = dict(requested_candidates=123, scored_candidates=100, cached_candidates=23,
                  geometry_rows_computed=42, geometry_rows_reused=3, model_ticks=60)
    stay = dict(J=2., served=20., quality=.5, energy_penalty=.1)
    champions = []
    for i in range(m):
        duration = [40, 10, 20][i]
        command = np.zeros((duration, 8, 3), dtype=np.float32)
        command[:, i + 1, 0] = 1
        selected = dict(member=i+1, site=i, path=100., duration=duration,
            predicted_total_J=[930.,960.,945.][i], predicted_total_served=9300.,
            predicted_destination=positions.tolist(), predicted_mask=1 | (1 << (i+1)),
            tail_score=dict(quality=.8))
        p = dict(initiated=True, member=i+1, site=i, commands=command.tolist(), duration=duration,
            arrival_t=40+duration, selected=selected, stay_score=stay.copy(),
            candidate_count=100*m, candidate_digest='synthetic-bank', counts=counts.copy(),
            predicted_destination=positions.tolist(), predicted_mask=selected['predicted_mask'])
        champions.append(p)
    original_R = (deepcopy(max(champions, key=lambda p: stationary_rank(p['selected'])))
                  if m else c._plan(None, positions, stay, 'synthetic-bank', counts, 0))
    return dict(original_R=original_R, champions=champions, candidate_rows=np.zeros((100*m,40)))


def install(monkeypatch, bank, values=None, served=None):
    queries, banks = [], []
    def enumerate_bank(positions, users, old_mask):
        assert positions.shape == (8,3) and users.shape == (50,2) and old_mask == 1
        banks.append(True)
        return deepcopy(bank)
    def simulator(mode):
        def run(controller, state, old_mask, plan, horizon):
            bid = branch_id(plan)
            assert state.dtype == np.float32 and old_mask == 1 and horizon == 500
            queries.append((mode,bid,controller))
            return dict(arrays={'mock':np.array([len(queries)])}, decisions=[{'mock':True}],
                summary=dict(total_J=(values or {}).get(bid,0.),
                             total_served=(served or {}).get(bid,0.), total_path=0.))
        return run
    monkeypatch.setattr(c,'enumerate_champions',enumerate_bank)
    monkeypatch.setattr(c,'simulate_reference',simulator('reference'))
    monkeypatch.setattr(c,'simulate_continuation',simulator('cycle'))
    return queries, banks, enumerate_bank, simulator('reference')


@pytest.mark.parametrize('arm',['R','T_E','K2_E'])
@pytest.mark.parametrize('reference',[False,True])
def test_factory_baselines_are_exact_original_objects(arm,reference):
    p = c.make_program(arm,reference=reference)
    assert type(p) is original.AmortizedProgram
    assert p.arm == arm and p.reference is reference and p.artifact is None
    assert p.selection is p.selection_timing is p.pending is None


@pytest.mark.parametrize('arm,artifact',[('L',None),('other',None),('L2_E',None),
    ('R',fitted()),('T_E',fitted()),('K2_E',fitted())])
def test_factory_rejects_wrong_arm_artifact_boundary(arm,artifact):
    with pytest.raises(ValueError): c.make_program(arm,artifact)


def test_constructor_inherits_original_interface_and_retains_artifact():
    a = fitted(-1)
    p = c.make_program('L2_E',a,True)
    assert type(p) is c.ShortlistProgram and isinstance(p,original.AmortizedProgram)
    assert p.artifact is a and p.arm == 'L2_E' and p.reference is True
    assert c.ShortlistProgram.select is original.AmortizedProgram.select
    assert c.ShortlistProgram.take_artifacts is original.AmortizedProgram.take_artifacts
    assert p.controller is p.base.controller and p.plan is p.base.plan


@pytest.mark.parametrize('reference',[False,True])
def test_all_negative_predictions_still_query_exactly_two_plus_stay(monkeypatch,reference):
    b = synthetic_bank()
    queries,banks,_,_ = install(monkeypatch,b,{'m2_s1':1.,'m3_s2':3.,'m1_s0':99.})
    p = c.make_program('L2_E',fitted(-1),reference)
    p._decide(public_report(),1)
    s = p.selection
    assert all(v < 0 for v in s['learner']['predicted_advantages'])
    assert s['learner']['initiated'] is False  # direct choice was ignored
    assert s['ordered_champion_indices'] == [1,2,0] and s['shortlist_indices'] == [1,2]
    assert s['ordered_champion_ids'] == ['m2_s1','m3_s2','m1_s0']
    assert s['shortlist_ids'] == ['m2_s1','m3_s2']
    assert [q[1] for q in queries] == ['stay','m2_s1','m3_s2']
    assert all(q[0] == ('reference' if reference else 'cycle') for q in queries)
    assert all(q[2] is p.controller for q in queries) and len(banks) == 1
    assert s['selected_branch'] == 'm3_s2' and p.plan['commands'] == b['champions'][2]['commands']
    assert s['bank_counts'] == b['original_R']['counts']
    assert len(s['learner']['features']) == len(s['learner']['standardized_features']) == 3
    assert s['learner']['coefficient_products'] == 39
    assert s['learner']['feature_distance_pairs'] == 50 + 3*(100+1)
    assert all(v >= 0 for v in p.selection_timing.values())
    assert set(p.selection_timing) == {'cpu_seconds','wall_seconds','bank_cpu_seconds','bank_wall_seconds',
        'feature_cpu_seconds','feature_wall_seconds','inference_cpu_seconds','inference_wall_seconds',
        'shortlist_cpu_seconds','shortlist_wall_seconds'}
    pending = p.take_artifacts()
    assert pending['candidate_rows'].shape == (300,40)
    assert [bid for bid,result in pending['branches']] == ['stay','m2_s1','m3_s2']
    assert all('arrays' in result and 'decisions' in result for bid,result in pending['branches'])
    assert p.take_artifacts() is None


def test_learned_order_can_differ_from_stationary_with_same_budget(monkeypatch):
    b = synthetic_bank()
    queries,_,_,_ = install(monkeypatch,b,{'m1_s0':2.,'m3_s2':1.})
    p = c.make_program('L2_E',fitted(duration_weight=1),True)
    p._decide(public_report(),1)
    assert p.selection['shortlist_ids'] == ['m1_s0','m3_s2']
    assert [q[1] for q in queries] == ['stay','m1_s0','m3_s2']
    assert p.selection['selected_branch'] == 'm1_s0'


@pytest.mark.parametrize('m',[0,1,3])
def test_zero_beta_exact_K2_menu_parity_and_matched_counts(monkeypatch,m):
    b = synthetic_bank(m)
    # A huge stay value collapses all stationary advantages after subtraction.
    # The exact stationary key, rather than those rounded scores, must rank.
    b['original_R']['stay_score']['J'] = 1e20
    queries,_,enum,sim = install(monkeypatch,b)
    monkeypatch.setattr(original,'enumerate_champions',enum)
    monkeypatch.setattr(original,'simulate_reference',sim)
    ordinary = c.make_program('K2_E',reference=True)
    learned = c.make_program('L2_E',fitted(),True)
    ordinary._decide(public_report(),1)
    ordinary_queries = [q[1] for q in queries]
    queries.clear()
    learned._decide(public_report(),1)
    assert [q[1] for q in queries] == ordinary_queries
    assert len(queries) == 1 + min(2,m)
    assert learned.selection['branches'] == ordinary.selection['branches']
    assert learned.selection['selected_branch'] == ordinary.selection['selected_branch'] == 'stay'
    assert learned.selection['learner']['zero_beta_fallback'] is True
    if m == 3:
        assert len(set(learned.selection['learner']['predicted_advantages'])) == 1
        assert learned.selection['shortlist_indices'] == [1,2]


@pytest.mark.parametrize('m',[0,1])
def test_nonzero_small_menu_includes_stay_and_all_available_champions(monkeypatch,m):
    queries,_,_,_ = install(monkeypatch,synthetic_bank(m))
    p = c.make_program('L2_E',fitted(-100))
    p._decide(public_report(),1)
    assert len(queries) == m+1 and len(p.selection['shortlist_indices']) == m
    assert p.selection['selected_branch'] == 'stay' and p.plan['initiated'] is False


@pytest.mark.parametrize('field,low,high,winner',[
    ('predicted_total_served',9300.,9400.,1),('path',50.,100.,0),
    ('duration',10,20,0),('member',1,2,0),('site',2,3,0)])
def test_prediction_tie_order(monkeypatch,field,low,high,winner):
    b = synthetic_bank(2)
    for p in b['champions']:
        p['selected'].update(predicted_total_J=930., path=100., duration=20, member=1,site=2)
    b['champions'][0]['selected'][field] = low
    b['champions'][1]['selected'][field] = high
    install(monkeypatch,b)
    p = c.make_program('L2_E',fitted(-1))
    p._decide(public_report(),1)
    assert p.selection['ordered_champion_indices'][0] == winner
    assert len(p.selection['shortlist_indices']) == 2


def test_final_model_J_tie_declines_despite_higher_service(monkeypatch):
    b = synthetic_bank()
    install(monkeypatch,b,{'stay':10.,'m2_s1':10.,'m3_s2':10.}, {'m2_s1':100.,'m3_s2':200.})
    p = c.make_program('L2_E',fitted(-1))
    p._decide(public_report(),1)
    assert p.selection['selected_branch'] == 'stay' and p.selection['initiated'] is False
    assert p.plan['initiated'] is False and p.plan['commands'] == []


def test_model_service_tie_break_after_strict_improvement(monkeypatch):
    install(monkeypatch,synthetic_bank(),{'m2_s1':10.,'m3_s2':10.}, {'m2_s1':100.,'m3_s2':200.})
    p = c.make_program('L2_E',fitted(-1))
    p._decide(public_report(),1)
    assert p.selection['selected_branch'] == 'm3_s2'


def test_inherited_select_calls_commitment_after_decision_and_copies_records(monkeypatch):
    install(monkeypatch,synthetic_bank(),{'m2_s1':1.})
    p = c.make_program('L2_E',fitted(-1),True)
    p.controller.next_t = 40
    observed = []
    def select(t,state,mask):
        observed.append((t,p.base.plan,p.base.option_old_mask))
        return np.zeros((8,3),dtype=np.float32),mask,{'t':t,'phase':'mock-commitment'}
    monkeypatch.setattr(p.base,'select',select)
    command,mask,decision = p.select(40,public_report(),1)
    assert observed[0][1] is p.plan and observed[0][2] == 1
    assert decision['selection'] == p.selection and decision['option'] == p.plan
    decision['option']['commands'][0][0][0] = 9
    decision['selection']['learner']['features'][0][0] = 9
    assert p.plan['commands'][0][0][0] == 0 and p.selection['learner']['features'][0][0] != 9
    with pytest.raises(ValueError): p.select(40,public_report(),1)


def test_inherited_select_rejects_wrong_clock_before_any_bank_query(monkeypatch):
    queries,banks,_,_ = install(monkeypatch,synthetic_bank())
    p = c.make_program('L2_E',fitted(-1))
    with pytest.raises(ValueError): p.select(40,public_report(),1)
    assert queries == banks == []


def test_source_and_rng_unchanged_by_synthetic_selection(monkeypatch):
    sources = [Path(original.__file__),Path(learning.__file__)]
    before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in sources]
    rng = np.random.get_state()
    install(monkeypatch,synthetic_bank())
    c.make_program('L2_E',fitted(-1),True)._decide(public_report(),1)
    after = np.random.get_state()
    assert rng[0] == after[0] and rng[2:] == after[2:]
    np.testing.assert_array_equal(rng[1],after[1])
    assert before == [hashlib.sha256(path.read_bytes()).hexdigest() for path in sources]
