import ast
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest
from experiments.candidates.uav_episode_policy_search.b01.contract import FROZEN,CONTRASTS
from experiments.candidates.uav_episode_policy_search.b01.search import head,update,perturbation,LIMIT
from experiments.candidates.uav_episode_policy_search.b01.policies import Policy
from experiments.candidates.uav_episode_policy_search.b01.reference import ReferencePolicy
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student
from experiments.candidates.uav_fleet_adaptation.b02.policies import categorical_probabilities,categorical_index

def test_frozen_exact_exposure_and_order():
    e=FROZEN.expected()
    assert e['fits']==4 and e['training_episodes']==4096 and e['evaluation_episodes']==736
    assert e['native_steps']==1236992 and e['native_uav_ticks']==6184960
    assert e['head_requests']==1392640 and e['zero_head_requests']==81920
    assert e['motion_requests']==1546240 and e['motion_draws']==1536000
    assert e['normal_coordinates']==1798144 and e['directions']==1024 and e['updates']==64
    assert e['bootstrap_integers']==640000 and len(CONTRASTS)==37
    order=list(FROZEN.identities())
    assert [(r['program'],r['sign'],r['world_index']) for r in order[:8]]==[('CAL0',1,0),('CAL0',1,1),('CAL0',-1,0),('CAL0',-1,1),('CONT0',1,0),('CONT0',1,1),('CONT0',-1,0),('CONT0',-1,1)]
    assert len({r['world'] for r in order if r['kind']=='training'})==1024
    assert order[4096]['world']==40163000 and order[4096]['program']=='P0_A'
    assert order[-1]['program']=='CONT1' and order[-1]['tape']==1

@pytest.mark.parametrize('family,width',[('CAL',28),('CONT',3484)])
def test_head_zero_norm_temperature_residual_and_nonfinite(family,width):
    l=np.linspace(-2,2,27,dtype=np.float32);h=np.arange(128,dtype=np.float32)/128
    theta=np.zeros(width,dtype=np.float64)
    result,normalized=head(l,h,theta,family)
    np.testing.assert_array_equal(result,l.astype(np.float64))
    np.testing.assert_allclose(np.linalg.norm(normalized),1,atol=2e-16,rtol=0)
    t=theta.copy();t[0]=100;t[1:28]=np.linspace(-1,1,27)
    if family=='CONT': t[28:]=.1
    expected=l.astype(np.float64)/2+np.tanh(t[1:28]+(.1*normalized.sum() if family=='CONT' else 0))
    np.testing.assert_allclose(head(l,h,t,family)[0],expected,rtol=0,atol=5e-16)
    t[0]=-100
    assert np.all(np.isfinite(head(l,np.zeros(128,dtype=np.float32),t,family)[0]))
    t[1]=np.nan
    with pytest.raises(ValueError):head(l,h,t,family)
    with pytest.raises(ValueError):head(l,h,np.zeros(width,dtype=np.float32),family)

def test_fp64_ordered_update_projection_zero_diff_and_all_directions():
    c=np.zeros(28,dtype=np.float64);ds=np.zeros((3,28),dtype=np.float64)
    ds[:,0]=[100,2,-3];ds[:,1]=[1,2,3]
    f=np.array([[3,1],[2,1],[1,2]],dtype=np.float64)
    result,diag=update(c,ds,f)
    scale=np.sqrt((1+.25+.25)/3)
    acc=2*ds[0]+ds[1]-ds[2]
    expected=.02/(3*scale)*acc;expected[0]=LIMIT
    np.testing.assert_array_equal(result,expected)
    assert diag['scale']==scale
    np.testing.assert_array_equal(update(c,ds,np.ones((3,2)))[0],c)
    assert update(c,ds,np.ones((3,2)))[1]['scale']==1e-8
    f[0,0]=np.inf
    with pytest.raises(FloatingPointError):update(c,ds,f)

def test_exact_address_one_normal_vector_and_distinct_domains(monkeypatch):
    calls=[]
    class Generator:
        def standard_normal(self,n):calls.append(n);return np.arange(n,dtype=np.float64)
    def generator(seed):
        assert seed.entropy==[40165000,1,1,3,4];return Generator()
    monkeypatch.setattr(np.random,'default_rng',generator)
    assert perturbation(FROZEN,1,1,3,4).shape==(3484,)
    assert calls==[3484]
    with pytest.raises(ValueError):replace(FROZEN,worlds=(40161000,)).validate()

def test_cdf_edges_all_categories():
    p=categorical_probabilities(np.zeros(27));cdf=np.cumsum(p);cdf[-1]=1
    for i in range(27):assert categorical_index(p,0 if i==0 else cdf[i-1])==i
    assert categorical_index(p,np.nextafter(1.,0.))==26

@pytest.mark.parametrize('family,width',[('CAL',28),('CONT',3484)])
def test_original_one_row_forward_cache_and_separate_reader(family,width):
    actor=make_student(811).eval().requires_grad_(False)
    row=np.zeros(104,dtype=np.float32);row[:3]=[.3,.4,.5]
    theta=np.linspace(-.1,.1,width,dtype=np.float64)
    worker=Policy('P0',actor,world=812,agent=1,sampling_root=813,family=family,theta=theta,zero_check=True)
    reader=ReferencePolicy('P0',actor,world=812,agent=1,sampling_root=813,family=family,theta=theta,zero_check=True)
    calls=[];handle=actor.register_forward_pre_hook(lambda model,args:calls.append(args[0].shape))
    try:
        for tick,nav in ((0,0),(4,0),(8,1)):
            row[-1]=tick/256
            a=worker.query(row,tick,nav);b=reader.query(row,tick,nav)
            for key in a:
                if key in ('hbar','head_logits','probabilities','entropy'):np.testing.assert_allclose(a[key],b[key],atol=5e-14,rtol=0)
                else:np.testing.assert_array_equal(a[key],b[key])
        assert worker.counters==reader.counters
        assert worker.counters['neural_rows']==2 and worker.counters['sampled_draws']==3
        assert worker.counters['head_requests']==worker.counters['zero_head_requests']==3
        assert calls==[__import__('torch').Size([1,114])]*4
        assert not actor.network[3]._forward_hooks
    finally:handle.remove()

def test_reference_arithmetic_does_not_import_candidate_answers():
    from experiments.candidates.uav_episode_policy_search.b01 import reference,read
    for module in (reference,read):
        tree=ast.parse(Path(module.__file__).read_text())
        assert not any(isinstance(n,ast.ImportFrom) and (n.module or '') in ('search','policies','collect') for n in ast.walk(tree))
