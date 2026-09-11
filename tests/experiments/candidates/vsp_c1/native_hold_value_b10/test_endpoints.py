"""No native/model fixtures: fixed endpoint orchestration over stateful stubs."""
import json
import statistics
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01 import environment, learner, policy
from experiments.candidates.vsp_c1.native_hold_value_b01 import critic, study
from .test_binding import OBJECT, CARD


@pytest.mark.parametrize("cap_midpoint", [False, True])
def test_continuous_training_separate_eval_and_publication(monkeypatch, tmp_path, cap_midpoint):
    envs, rngs, pairs, opts, calls = [], [], [], [], []
    now = [0.]
    class Model:
        def __init__(self, n):
            self.n, self.updates = n, 0
        def parameters(self):
            return [torch.zeros(self.n)]
        def state_dict(self):
            return {"stub_updates": torch.tensor(self.updates)}
    def models(common, arm, **kwargs):
        assert kwargs == dict(second_mlp_width=133, extra_init_seed=850100012)
        pair = Model(1), Model(34817 if arm == "GATED-V" else 34827)
        pairs.append(pair)
        return pair
    def factory(seed):
        env = SimpleNamespace(seed=seed, resets=[])
        envs.append(env)
        return env
    def generator(seed):
        rng = SimpleNamespace(seed=seed, uses=0)
        rngs.append(rng)
        return rng
    def optimizer(*models):
        opt = SimpleNamespace(models=models, updates=0)
        opts.append(opt)
        return opt
    def forbidden(*args, **kwargs):
        pytest.fail("real scientific model/environment constructor invoked")
    def collect(env, actor, value, horizon, reset_seed, velocity, duration, metadata,
                check, counts, emit, diagnostic, limits, **options):
        check()
        arm, phase, e = metadata['arm'], metadata['phase'], metadata['episode']
        n = metadata.get('training_episodes')
        assert horizon == 256 and metadata['pair_master'] == 8501
        arm_index = 0 if arm == 'GATED-V' else 1
        if phase == 'train':
            assert env is envs[2*arm_index]
            assert n is None and e == len(env.resets)
            assert velocity.uses == duration.uses == e
            assert actor.updates == value.updates == e//2
            assert opts[arm_index].updates == e//2
            assert reset_seed == 850101000+e
        else:
            assert env is envs[2*arm_index+1] and reset_seed == 850102000+e
            if arm != 'H':
                assert n in (512,768) and actor.updates == value.updates == n//2
                assert len(envs[2*arm_index].resets) == n
                assert opts[arm_index].updates == n//2
                assert velocity.uses == duration.uses == 0
            else:
                assert n == 0 and actor is value is velocity is duration is None
        if arm != 'H':
            assert velocity.seed == (850100021 if phase == 'train' else 850103000+e)
            assert duration.seed == (850100022 if phase == 'train' else 850104000+e)
            velocity.uses += 1
            duration.uses += 1
            m = options['value_moments']
            expected = e//2 if phase == 'train' else n//2
            assert m.updates == expected and m.n == 512*expected
        env.resets.append(reset_seed)
        calls.append((arm,phase,e,n))
        for k,v in {'explicit_resets':1,'step_calls':256,'scientific_uav_calls':256,
                    'team_steps':256,phase+'_team_steps':256,phase+'_episodes':1,
                    'completed_episode_steps':256,'duration_decisions':5 if actor else 0}.items():
            counts[k] += v
        score = (.02 if n == 512 else .05) if arm == 'GATED-V' else 0.
        emit(dict(metadata, reset_seed=reset_seed, steps=256, reward_sum=score*256, J=score))
        if cap_midpoint and phase == 'eval' and n == 512 and e == 31:
            now[0] = 1801.
        check()
        return dict(critic=torch.zeros(256,136), reward=torch.ones(256), episode=e, actor=actor)
    def update(actor, value, opt, episodes, chunk, check, counts, **kwargs):
        assert opt.models == (actor,value) and opt.updates == actor.updates
        assert [e['episode'] for e in episodes] == [2*opt.updates,2*opt.updates+1]
        assert all(e['actor'] is actor for e in episodes)
        kwargs['value_moments'].update(learner.returns_to_go(torch.stack([e['reward'] for e in episodes])))
        opt.updates += 1
        actor.updates += 1
        value.updates += 1
        counts['optimizer_steps'] += 4
        return [dict(epoch=e, value_loss_units='normalized_squared') for e in range(4)]
    for name in ('Actor','Critic'):
        monkeypatch.setattr(policy,name,forbidden)
    monkeypatch.setattr(environment,'make_real',forbidden)
    monkeypatch.setattr(environment,'SyntheticAdapter',forbidden)
    monkeypatch.setattr(critic,'models',models)
    monkeypatch.setattr(policy,'templates',lambda seed: object())
    monkeypatch.setattr(policy,'snapshot',lambda *args: {})
    monkeypatch.setattr(critic,'movement',lambda initial,actor,value: dict(updates=actor.updates))
    monkeypatch.setattr(policy,'generator',generator)
    monkeypatch.setattr(learner,'optimizer_for',optimizer)
    monkeypatch.setattr(learner,'collect_episode',collect)
    monkeypatch.setattr(learner,'update',update)
    result=study.run_pair(study.Config(seed=8501,train_episodes=768),tmp_path,0.,clock=lambda:now[0],
                          factory=factory,object_id=OBJECT,card=CARD,normalize_value=True,
                          second_mlp_width=133,extra_init_seed=850100012,fixed_endpoints=True)
    if cap_midpoint:
        assert result['status']=='CAP_BREACH' and not result['primary']['complete']
        assert len(opts)==1 and opts[0].updates==256
        assert result['counts']['team_steps']==(512+32)*256
        assert not any(c[1]=='train' and c[2]>=512 for c in calls)
        return
    assert result['status']=='COMPLETE' and result['publication_readback']=='complete'
    assert [e.seed for e in envs]==[850101000,850102000,850101000,850102000]
    assert len(rngs)==260 and len({id(r) for r in rngs})==260
    assert [o.updates for o in opts]==[384,384]
    assert result['counts']['team_steps']==434176 and result['counts']['optimizer_steps']==3072
    assert result['counts']['eval_episodes']==160 and result['counts']['constructors']==4
    assert result['counts']['train_team_steps']==393216 and result['counts']['eval_team_steps']==40960
    expected=[]
    for arm in study.ARMS:
        expected += [(arm,'train',e,None) for e in range(512)]
        expected += [(arm,'eval',e,512) for e in range(32)]
        expected += [(arm,'train',e,None) for e in range(512,768)]
        expected += [(arm,'eval',e,768) for e in range(32)]
    expected += [('H','eval',e,0) for e in range(32)]
    assert calls==expected
    assert result['primary']['reading']=='CHANGE_UP'
    assert result['primary']['change']['mean']==pytest.approx(.03)
    for arm,info in result['arms'].items():
        assert info['training_counts']['eval_episodes']==0
        assert info['training_counts']['train_episodes']==768
        assert info['moments_after_hover']==info['value_moments'] if arm=='MLP-V' else True
        for n in (512,768):
            ep=info['endpoints'][str(n)]
            assert ep['complete'] and ep['training_episodes']==n
            assert ep['training_counts']['train_episodes']==n and ep['training_counts']['optimizer_steps']==n*2
            assert ep['training_counts']['eval_episodes']==0
            assert ep['exposure']['updates']==n//2
            m=ep['value_moments']
            assert m['n']==n*256 and m['updates']==n//2
            assert m==ep['moments_before_evaluation']==ep['moments_after_evaluation']
            saved=torch.load(tmp_path/ep['checkpoint'],weights_only=True)
            assert saved['training_episodes']==n and saved['configuration']['train_episodes']==768
            assert saved['value_moments']==m and saved['actor']['stub_updates'].item()==n//2
    assert json.loads((tmp_path/'summary.json').read_text())['primary']==result['primary']


def panel(change):
    return [dict(arm=arm,phase='eval',episode=e,reset_seed=850102000+e,
                 training_episodes=n,J=(change if n==768 and arm=='GATED-V' else 0.))
            for n in (512,768) for arm in study.ARMS for e in range(32)]


@pytest.mark.parametrize('change,reading',[(-.02,'CHANGE_DOWN'),(-.01,'CHANGE_WITHIN'),
                                          (.0,'CHANGE_WITHIN'),(.01,'CHANGE_WITHIN'),(.02,'CHANGE_UP')])
def test_paired_change_rules_without_hover(change,reading):
    result=study.paired_change_from_rows(panel(change),32,850102000)
    assert result['complete'] and not result['hover_complete'] and result['reading']==reading
    assert result['change']['mean']==change


def test_pairing_conditional_se_and_missing_dependency():
    rows=panel(.02)
    for row in rows:
        if row['arm']=='GATED-V':
            row['J'] += row['episode']*.001*(1 if row['training_episodes']==512 else 2)
    result=study.paired_change_from_rows(list(reversed(rows)),32,850102000)
    expected=[.02+e*.001 for e in range(32)]
    assert result['change']['differences']==pytest.approx(expected)
    assert result['change']['conditional_se']==pytest.approx(statistics.stdev(expected)/32**.5)
    incomplete=study.paired_change_from_rows(rows[:-1],32,850102000)
    assert not incomplete['complete'] and incomplete['reading'] is None
    assert incomplete['endpoints']['512']['complete']
    duplicate=study.paired_change_from_rows(rows+[rows[-1]],32,850102000)
    assert not duplicate['complete']
