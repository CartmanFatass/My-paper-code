"""Read completed B09 data only; no environment, model forward, optimizer, or writes."""
from pathlib import Path
import hashlib,json,statistics
import numpy as np
import torch

torch.set_num_threads(1)
ROOT=Path(__file__).resolve().parents[3]
SOURCE='a20583ee128bb04e2e638804a0b5493322a3edf6'
MASTERS=(8961,8962,8963)
MODES=('normalized','scalar','ordinary')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(state):
 d=hashlib.sha256()
 for key,value in sorted(state.items()):
  value=value.detach().cpu().contiguous()
  d.update(key.encode()+b'\0');d.update(str(value.dtype).encode()+b'\0')
  d.update(str(tuple(value.shape)).encode()+b'\0');d.update(value.numpy().tobytes())
 return d.hexdigest()
def stats(values):
 a=np.asarray(values,dtype=np.float64)
 return {'mean':float(a.mean()),'min':float(a.min()),'max':float(a.max()),'q10_median_q90':np.quantile(a,[.1,.5,.9]).tolist(),'std':float(a.std())}

summaries={m:json.loads((ROOT/f'runs/ucope/normalized_distance_gate_b09_{m}/summary.json').read_text()) for m in MASTERS}
assert all(s['status']=='COMPLETE' for s in summaries.values()),'Do not inspect scores before the fixed batch completes'
report=[]
for master,s in summaries.items():
 root=ROOT/f'runs/ucope/normalized_distance_gate_b09_{master}'
 assert s['launch_sha']==SOURCE and s['foundation_unchanged'] and s['foundation_optimizer_steps']==0
 assert s['configuration']['master']==master and s['configuration']['horizon']==256
 assert s['configuration']['train_episodes']==2048 and s['configuration']['eval_episodes']==64
 assert s['foundation']['foundation_master']==master-20
 assert s['fit_accounting']['started_new_gate_fits']==s['fit_accounting']['completed_new_gate_fits']==2
 for name,identity in s['artifacts'].items():
  path=root/name
  assert path.stat().st_size==identity['bytes'] and sha(path)==identity['sha256'],(master,name)
 source=json.loads((root/'source.json').read_text())
 for relative,identity in source['files'].items():
  assert sha(ROOT/relative)==identity['sha256'],relative
 original=torch.load(root/'inherited_checkpoint.pt',map_location='cpu',weights_only=True)
 assert digest(original['actor'])==s['foundation_final_digest']
 for inherited,key,filename in [('checkpoint','checkpoint','Ghalf_final.pt'),('summary','summary','summary.json'),('source','source','source.json')]:
  path=ROOT/f'runs/ucope/gaussian_scale_initialization_b06_{master-20}'/filename
  assert sha(path)==s['foundation']['files'][key]['sha256']
 expected={'train_team_steps':1048576,'eval_team_steps':49152,'team_steps':1097728,
           'train_episodes':4096,'eval_episodes':192,'gate_optimizer_steps':16384,
           'critic_optimizer_steps':16384,'optimizer_steps':32768,'max_minibatch':256}
 for key,value in expected.items():assert s['counts'][key]==value,(master,key,s['counts'][key])
 episodes=[json.loads(x) for x in (root/'episodes.jsonl').read_text().splitlines()]
 updates=[json.loads(x) for x in (root/'updates.jsonl').read_text().splitlines()]
 assert len(episodes)==4288 and len(updates)==2048
 for row in episodes:
  assert row['steps']==256
  assert row['world_seed']==100000*master+(10000 if row['phase']=='train' else 30000)+row['episode']
 behavior={}; panels={}; coins={}; contexts={}
 for mode in MODES:
  record=s['arms'][mode]
  assert record['eval_complete'] and all(record['evaluation_immutability'].values())
  with np.load(root/f'{mode}_evaluation.npz',allow_pickle=False) as z:
   assert z['reward'].shape==(64,256) and z['reward'].dtype==np.float64
   assert all(np.isfinite(z[k]).all() for k in z.files)
   assert z['commands'].shape==z['means'].shape==z['previous'].shape==(64,256,5,3)
   np.testing.assert_array_equal(z['previous'][:,1:],z['commands'][:,:-1])
   assert not z['previous'][:,0].any()
   assert not z['eligible'][:,0].any() and not (z['keep'] & ~z['eligible']).any()
   if mode=='ordinary':assert not z['keep'].any() and not z['eligible'].any()
   else:
    np.testing.assert_array_equal(z['eligible'][:,1:],~z['keep'][:,:-1])
    np.testing.assert_array_equal(z['keep'],z['eligible'] & (z['gate_uniforms'] < z['keep_probability']))
   fresh=torch.tanh(torch.from_numpy(z['means'].copy())).numpy()
   commanded=np.where(z['keep'][...,None],z['previous'],fresh)
   np.testing.assert_allclose(z['commands'],commanded,rtol=1e-6,atol=1e-7)
   panels[mode]=z['reward'].sum(1)/256
   np.testing.assert_allclose(panels[mode],s['final_panel']['world_scores'][mode],rtol=0,atol=1e-15)
   coins[mode]=z['gate_uniforms'].copy()
   contexts[mode]=z['context'].copy()
   ids=z['context_episode_ids']
   np.testing.assert_array_equal(contexts[mode][...,104:107],z['previous'][ids])
   np.testing.assert_allclose(contexts[mode][...,107:110],fresh[ids],rtol=1e-6,atol=1e-7)
   c=torch.from_numpy(contexts[mode])
   reconstructed_distance=((c[...,107:110]-c[...,104:107]).square().sum(-1)/12).numpy()
   np.testing.assert_array_equal(contexts[mode][...,-1],reconstructed_distance)
   eligible=z['eligible'];probs=z['keep_probability'][eligible]
   b={'J':float(panels[mode].mean()),'keep_probability':stats(probs) if probs.size else None,'keep_rate':float(z['keep'].sum()/eligible.sum()) if eligible.any() else None,'copy_fraction_all_ticks':float(z['keep'].mean())}
   if mode!='ordinary':
    ck=torch.load(root/f'{mode}_final.pt',map_location='cpu',weights_only=True)
    assert ck['object']=='UCOPE_NORMALIZED_DISTANCE_GATE_B09' and ck['launch_sha']==SOURCE
    assert ck['foundation']['distance_scale']==s['distance_scale']
    assert float(ck['gate']['median'])==float(np.float32(s['distance_scale']['median']))
    assert float(ck['gate']['scale'])==float(np.float32(s['distance_scale']['scale']))
    assert len(ck['gate_optimizer']['state'])==(2 if mode=='normalized' else 1)
    for opt in ('gate_optimizer','critic_optimizer'):
     assert all(float(v['step'])==8192 for v in ck[opt]['state'].values())
    assert ck['counts']['optimizer_steps']==16384
    assert set(ck['gate'])=={'b0','b1','median','scale'}
    intercept=float(ck['gate']['b0']); slope=float(ck['gate']['b1'])
    assert record['final_affine']=={'b0':intercept,'b1':slope}
    b['affine']={'intercept':intercept,'slope_scaled':slope,'intercept_raw':intercept-slope*float(ck['gate']['median'])/float(ck['gate']['scale']),'slope_raw':slope/float(ck['gate']['scale'])}
    context=torch.from_numpy(z['context'].copy())
    distances=context[..., -1]
    m=ck['gate']['median']; scale=ck['gate']['scale']
    logits=ck['gate']['b0']+(ck['gate']['b1']*((distances-m)/scale) if mode=='normalized' else torch.zeros_like(distances))
    prediction=torch.sigmoid(logits).numpy()
    ids=z['context_episode_ids']
    np.testing.assert_allclose(prediction,z['keep_probability'][ids],rtol=1e-6,atol=1e-7)
    assert ids.tolist()==list(range(0,64,8))
    b['movement']=record['movement']
    qrows=[row for row in episodes if row['arm']==mode and row['phase']=='train']
    assert len(qrows)==2048
    b['training_quarters']=[{'J':statistics.mean(row['J'] for row in qrows[i:i+512]),'mean_eligible_pkeep':statistics.mean(row['keep_probability_mean'] for row in qrows[i:i+512])} for i in range(0,2048,512)]
    statrows=[stat for update in updates if update['arm']==mode for stat in update['statistics']]
    assert len(statrows)==8192
    b['first_last_update_statistics']={'first':statrows[0],'last':statrows[-1]}
   behavior[mode]=b
 np.testing.assert_array_equal(coins['normalized'],coins['scalar'])
 np.testing.assert_array_equal(contexts['normalized'][:,:2],contexts['scalar'][:,:2])
 np.testing.assert_array_equal(contexts['normalized'][:,:2],contexts['ordinary'][:,:2])
 assert not coins['ordinary'].any()
 contrasts={}
 for a,b in [('normalized','scalar'),('normalized','ordinary'),('scalar','ordinary')]:
  delta=panels[a]-panels[b]
  key=a+'_minus_'+b
  np.testing.assert_allclose(delta,s['final_panel'][key]['differences'],rtol=0,atol=1e-15)
  contrasts[key]={'mean':float(delta.mean()),'conditional_world_se':float(delta.std(ddof=1)/8),'positive':int((delta>0).sum()),'negative':int((delta<0).sum()),'range':[float(delta.min()),float(delta.max())]}
 report.append({'master':master,'summary_sha256':sha(root/'summary.json'),'behavior':behavior,'contrasts':contrasts,'cost':{k:s[k] for k in ('counts','fit_accounting','wall_seconds','process_cpu_seconds','process_peak_rss_kib')}})
summary={'object':'UCOPE_NORMALIZED_DISTANCE_GATE_B09_REDUCTION','source_sha':SOURCE,'blocks':report,'all_checks_passed':True,'native_steps_added':0,'foundation_forwards_added':0,'critic_forwards_added':0,'saved_context_gate_probability_reconstructions':61440,'optimizer_steps_added':0}
summary['contrasts_mean_of_blocks']={key:statistics.mean(r['contrasts'][key]['mean'] for r in report) for key in report[0]['contrasts']}
summary['continuation_rule_passes']=all(all(r['contrasts'][key]['mean']>0 for r in report) and summary['contrasts_mean_of_blocks'][key]>=.01 for key in ('normalized_minus_scalar','normalized_minus_ordinary'))
print(json.dumps(summary,indent=2,allow_nan=False))
