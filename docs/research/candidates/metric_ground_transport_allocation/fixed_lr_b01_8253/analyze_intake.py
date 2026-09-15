"""Data-only fixed8253 intake recomputation; no environment or learner invocation."""
import json, math, statistics, collections
from pathlib import Path
root=Path('temp/directions/metric_ground_transport_allocation/exp/fixed_lr_b01_8253_20260914')
s=json.loads((root/'summary.json').read_text())
rows=[json.loads(x) for x in (root/'episodes.jsonl').read_text().splitlines()]
rolls=[json.loads(x) for x in (root/'rollouts.jsonl').read_text().splitlines()]
assert s['launch_sha']=='390aa2711245a10c13af7fbd0d1a24ff3237d5da'
assert s['status']=='COMPLETE' and not s['limits'] and not s['partial_fits']
assert len(rows)==576 and len(rolls)==256 and len(s['fits'])==2
panels={}
for arm in ('COND','DENSE'):
    train=[r for r in rows if r['arm']==arm and r['phase']=='train']
    final=sorted([r for r in rows if r['arm']==arm and r['phase']=='eval'],key=lambda r:r['episode'])
    assert len(train)==256 and {r['episode'] for r in train}==set(range(256))
    assert len(final)==32 and [r['episode'] for r in final]==list(range(32))
    assert all(r['steps']==256 and math.isfinite(r['J']) for r in train+final)
    for r in train+final:
        e=r['episode']; base=825300000; training=r['phase']=='train'
        assert r['object']=='MGTAP-FIXED-LR-B01' and r['stage']=='fixed'
        assert r['pair_master']==8253 and r['lr_key']=='slow' and r['learning_rate']==1e-4
        assert r['reset_seed']==base+(1000 if training else 2000)+e
        assert r['velocity_seed']==base+(21 if training else 3000+e)
        assert r['duration_seed']==base+(4000 if training else 5000)+e
    arm_rolls=[r for r in rolls if r['arm']==arm]
    assert [r['rollout'] for r in arm_rolls]==list(range(128))
    assert all(r['optimizer_steps']==4 and len(r['epochs'])==4 and r['steps']==512 for r in arm_rolls)
    fit=next(f for f in s['fits'] if f['arm']==arm)
    assert fit['counts']['train_team_steps']==65536 and fit['counts']['eval_team_steps']==8192
    assert fit['counts']['optimizer_steps']==sum(r['optimizer_steps'] for r in arm_rolls)==512
    assert not fit['limits']
    for key in ('common_actor','critic','total','encoder','recurrent','branch_inner','branch_projection'):
        assert math.isfinite(fit['exposure'][key]['displacement']) and fit['exposure'][key]['displacement']>0
    panels[arm]=[r['J'] for r in final]
d=[x-y for x,y in zip(panels['COND'],panels['DENSE'])]
delta=statistics.mean(d); se=statistics.stdev(d)/math.sqrt(32)
assert panels==s['primary']['J_by_arm'] and d==s['primary']['ordered_COND_minus_DENSE']
assert delta==s['primary']['delta_J'] and se==s['primary']['conditional_panel_se']
reading='COND_ABOVE_MEI' if delta>.01 else 'COND_ADVERSE' if delta<-.01 else 'INSIDE_MEI'
assert s['primary']['reading']==reading
result={'object':s['object'],'source':s['launch_sha'],'mean_J_by_arm':{a:statistics.mean(p) for a,p in panels.items()},'delta_J':delta,'conditional_panel_se':se,'positive_worlds':sum(x>0 for x in d),'negative_worlds':sum(x<0 for x in d),'zero_worlds':sum(x==0 for x in d),'positive_indices':[i for i,x in enumerate(d) if x>0],'positive_values':[x for x in d if x>0],'reading':s['primary']['reading'],'independent_new_training_pairs':1,'training_run_sd':None,'raw_episode_rows':len(rows),'raw_rollout_rows':len(rolls),'total_exposure':s['planned_exposure']['total'],'body_fit_sum_seconds':sum(f['fit_body_wall'] for f in s['fits']),'study_body_wall_seconds':s['study_body_wall_before_summary'],'whole_command_wall_seconds':178.86,'peak_rss_kib':568040,'peak_rss_mib':568040/1024,'new_command_exit':0,'prior_lr_study_plus_this_native_wall_seconds':658.02+178.86,'resource_scope':'Native-command walls only; not lifetime or support/provider totals','checks':'all raw counts/bindings/finite learner and branch displacements/final scores/signs/primary recomputed from original files; no new learning'}
print(json.dumps(result,indent=2))
