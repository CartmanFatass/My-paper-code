import json

import numpy as np
import pytest

from experiments.candidates.uav_registered_service.b01 import study, read, metrics, run
from experiments.candidates.uav_registered_service.b01.scheduler import Scheduler
from experiments.candidates.uav_radio_activation.b03 import study as old


def collect(tmp_path,arm,seed=9801,horizon=8,**kwargs):
    env=study.factory(seed)
    env.env.max_steps=horizon
    out=tmp_path/arm
    (out/'raw').mkdir(parents=True)
    counts=dict(explicit_resets=0,native_step_calls=0,team_steps=0,complete_episodes=0)
    try:
        row=study.collect_episode(env,arm,seed,out,counts,horizon=horizon,**kwargs)
    finally:
        env.close()
    with np.load(row['raw']['path'],allow_pickle=False) as saved:
        raw={key:saved[key].copy() for key in saved.files}
    return row,raw,counts


@pytest.mark.parametrize('arm',study.ARMS)
def test_full_small_fixture_reader_and_native_contract(tmp_path,arm):
    row,raw,counts=collect(tmp_path,arm)
    assert counts['team_steps']==8 and counts['complete_episodes']==1
    result=read.verify_episode(row,raw)
    assert result['verified_steps']==8 and result['max_native_J_error']<1e-12
    assert row['F']==sum(row['per_window_coverage'])
    if arm in ('O','P'):
        assert raw['terminal_history_complete'] and raw['model_valid'].all()
        assert result['verified_model_transitions']==8
        assert row['history_reductions']+row['terminal_history_reductions']==8
        assert raw['forecast_lengths'].tolist()==[4,2]
        assert np.isnan(raw['forecast'][-1,:,2:]).all()
        corrupt={key:value.copy() for key,value in raw.items()}
        q,m=corrupt['candidate_order'][0,0]
        corrupt['ordering_keys'][0,q,m,0]+=1
        with pytest.raises(AssertionError):
            read.verify_episode(row,corrupt)


@pytest.mark.parametrize('arm', ['R','S2','T2'])
def test_retained_exact_fixture_behavior(tmp_path,arm):
    row,raw,_=collect(tmp_path,arm,seed=9802)
    env=old.factory(9802)
    env.env.max_steps=8
    out=tmp_path/'frozen'
    (out/'raw').mkdir(parents=True)
    counts=dict(explicit_resets=0,native_step_calls=0,team_steps=0,complete_episodes=0)
    try:
        retained=old.collect_episode(env,arm,9802,out,counts,horizon=8)
    finally:
        env.close()
    with np.load(retained['raw']['path']) as saved:
        for key in saved.files:
            if key not in ('c_wall','c_cpu','scheduler_wall','scheduler_cpu'):
                np.testing.assert_array_equal(raw[key],saved[key])
    assert row['J']==retained['J'] and row['controller_counts']==retained['controller_counts']


def test_continuous_gap_contact0_and127_and_window_edges():
    contacts=np.zeros((256,50),bool)
    contacts[[0,127],0]=True
    contacts[[63,64,255],1]=True
    result=metrics.periodic_metrics(contacts)
    assert result['F']==5 and result['per_window_coverage']==[2,2,0,1]
    assert result['satisfied_window_histogram']==[48,0,1,1,0]
    _,gaps=metrics.contact_gaps(contacts)
    assert [0,1,127,126,0,0] in gaps.tolist()
    assert [0,128,256,128,0,1] in gaps.tolist()
    assert [1,0,63,63,1,0] in gaps.tolist()
    assert [2,0,256,256,1,1] in gaps.tolist()
    assert result['never_served']==48


def test_panel_orders_no_ceiling_and_pair_refusal():
    assert study.SEED==29308000 and study.WORLDS==64
    assert len(study.ARM_ORDERS)==10
    for position in range(5):
        assert all(sum(order[position]==arm for order in study.ARM_ORDERS)==2 for arm in study.ARMS)
    assert not hasattr(study,'CPU_LIMIT_SECONDS') and not hasattr(run,'resource')
    with pytest.raises(ValueError):
        study.paired_reading([], [9803])


def test_admission_before_effects_and_wrong_seed(tmp_path,monkeypatch):
    from scripts import hmasd_admission
    def refuse(*args,**kwargs):
        assert kwargs['direction']=='uav_registered_service'
        raise RuntimeError('fixture refusal')
    monkeypatch.setattr(hmasd_admission,'require_admission',refuse)
    with pytest.raises(RuntimeError,match='fixture refusal'):
        run.main(['--out',str(tmp_path/'absent'),'--launch-sha','fixture','--seed','29308000'])
    assert not (tmp_path/'absent').exists()
    with pytest.raises(SystemExit):
        run.main(['--out',str(tmp_path/'absent'),'--launch-sha','fixture','--seed','9803'])


def test_incomplete_evidence_no_pair_read(tmp_path):
    class Broken:
        def reset(self,**kwargs):
            raise RuntimeError('fixture reset failure')
        def close(self):
            pass
    result=study.run_batch(tmp_path/'broken','fixture',make_env=lambda seed:Broken(),seeds=(9804,),horizon=8)
    assert result['status']=='INCOMPLETE_TECHNICAL_FAILURE'
    assert result['counts']['team_steps']==0 and 'paired' not in result
    assert result['config']['cpu_limit_seconds'] is None
    with pytest.raises(ValueError):
        read.read_result(tmp_path/'broken')


def test_all_team_late_fallback_collector_and_history_reader(tmp_path):
    class Late(Scheduler):
        def decide(self,*args,**kwargs):
            if args[3]>0:
                kwargs['started']-=10
            return super().decide(*args,**kwargs)
    row,raw,_=collect(tmp_path,'P',seed=9805,horizon=12,scheduler_type=Late)
    assert raw['timely'].tolist()==[True,False,False]
    np.testing.assert_array_equal(raw['commands'][2:],np.broadcast_to(raw['commitments'][0],(10,5,3)))
    assert not raw['decoded_anchor'][1:].any()
    assert read.verify_episode(row,raw)['verified_model_transitions']==12


def test_first_missing_report_no_hidden_history_in_raw(tmp_path):
    class FirstMissing(Scheduler):
        def decide(self,*args,**kwargs):
            if args[3]==0:
                kwargs['started']-=10
            return super().decide(*args,**kwargs)
    row,raw,_=collect(tmp_path,'O',seed=9806,horizon=12,scheduler_type=FirstMissing)
    assert raw['timely'].tolist()==[False,True,True]
    assert raw['fallback_reason'].tolist()==['deadline','','']
    assert not raw['model_valid'][:4].any() and raw['model_valid'][4:].all()
    assert raw['terminal_history_complete'] and raw['terminal_history_start']==4
    assert not raw['model_contacts'][:4].any()
    np.testing.assert_array_equal(raw['commands'][6:10],np.broadcast_to(raw['commitments'][1],(4,5,3)))
    assert read.verify_episode(row,raw)['verified_model_transitions']==8


def test_synthetic_fixed_fixture_batch_compact_summary_and_all10_pairs(tmp_path):
    def short_env(seed):
        env=study.factory(seed)
        env.env.max_steps=8
        return env
    result=study.run_batch(tmp_path/'fixture','synthetic-sha',make_env=short_env,seeds=(9807,),horizon=8)
    assert result['status']=='COMPLETE' and not result['scientific_invocation']
    assert result['counts']==dict(constructors=1,explicit_resets=5,native_step_calls=40,team_steps=40,complete_episodes=5,fit_started=0,optimizer_steps=0)
    assert len(result['paired']['comparisons'])==10 and result['paired']['primary']=='P-O'
    assert json.loads((tmp_path/'fixture'/'summary.json').read_text())==result
    assert result['config']['preferred_node']=='wsl_4070'
    for row in result['rows']:
        with np.load(row['raw']['path'],allow_pickle=False) as raw:
            assert read.verify_episode(row,raw)['verified_steps']==8
    with pytest.raises(ValueError):
        read.read_result(tmp_path/'fixture')


def test_interrupted_settlement_and_queued_anchors_read_back(tmp_path,monkeypatch):
    from experiments.candidates.uav_registered_service.b01 import history
    from experiments.candidates.uav_radio_activation.b03.scheduler import DeadlineExceeded
    original_settle=history.ExecutionHistory.settle
    # Deterministic injected deadline after two committed model transitions at t4.
    def interrupted(self,stop,check=lambda:None,evaluate=history.model):
        if stop==4:
            calls=[0]
            def interrupted_check():
                check()
                calls[0]+=1
                if calls[0]==4:
                    raise DeadlineExceeded
            return original_settle(self,stop,interrupted_check,evaluate)
        return original_settle(self,stop,check,evaluate)
    monkeypatch.setattr(history.ExecutionHistory,'settle',interrupted)
    row,raw,_=collect(tmp_path,'P',seed=9808,horizon=12)
    assert raw['decoded_anchor'].tolist()==[True,True,True]
    assert raw['history_after'].tolist()==[0,2,8]
    assert raw['history_reductions'].tolist()==[0,2,6]
    assert raw['timely'].tolist()==[True,False,True]
    assert read.verify_episode(row,raw)['verified_model_transitions']==12
    corrupt={key:value.copy() for key,value in raw.items()}
    corrupt['decoded_anchor'][0]=False
    with pytest.raises(AssertionError):
        read.verify_episode(row,corrupt)


@pytest.mark.parametrize('support_fails',[False,True])
def test_native_early_terminal_retains_original_failure_and_partial_raw(tmp_path,monkeypatch,support_fails):
    from experiments.candidates.uav_registered_service.b01 import history
    def early_env(seed):
        env=study.factory(seed)
        env.env.max_steps=1
        return env
    original=history.ExecutionHistory.settle
    def failed_support(self,stop,*args,**kwargs):
        if stop==1 and support_fails:
            raise ValueError('fixture terminal reader-support failure')
        return original(self,stop,*args,**kwargs)
    monkeypatch.setattr(history.ExecutionHistory,'settle',failed_support)
    env=early_env(9809)
    out=tmp_path/'early'
    (out/'raw').mkdir(parents=True)
    counts=dict(explicit_resets=0,native_step_calls=0,team_steps=0,complete_episodes=0)
    try:
        with pytest.raises(RuntimeError,match='unexpected native terminal boundary'):
            study.collect_episode(env,'P',9809,out,counts,horizon=8)
    finally:
        env.close()
    assert counts['team_steps']==1 and counts['complete_episodes']==0
    with np.load(out/'raw'/'P_9809.npz',allow_pickle=False) as raw:
        assert raw['completed_steps']==1
        assert raw['episode_failure_type']=='RuntimeError'
        if support_fails:
            assert raw['terminal_support_failure_type']=='ValueError'
            assert 'fixture terminal reader-support' in str(raw['terminal_support_failure_message'])
        else:
            assert raw['model_valid'][0] and raw['terminal_history_complete']
            assert 'terminal_support_failure_type' not in raw
        assert len(raw['actual_contacts'])==1
