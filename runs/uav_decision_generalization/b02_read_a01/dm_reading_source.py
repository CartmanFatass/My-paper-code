"""Post-hoc raw arithmetic only; no policy/model/environment imports or queries."""
import collections
import hashlib
import json
import os
from pathlib import Path
import resource
import time
import numpy as np

base=Path('/home/wu/projects/HMASD/runs/uav_decision_generalization')
worker=base/'b02_cooperation_a01';reader=base/'b02_read_a01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p,root):return {'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)}
def allocated(p):return sum(Path(d).lstat().st_blocks*512+sum((Path(d)/f).lstat().st_blocks*512 for f in fs) for d,_,fs in os.walk(p))
wsummary=json.loads((worker/'summary.json').read_bytes());summary=json.loads((reader/'summary.json').read_bytes())
assert sha(worker/'episodes.json')==wsummary['episodes']['sha256']
assert sha(reader/'reading.json')==summary['reading']['sha256']
reading=json.loads((reader/'reading.json').read_bytes());rows=json.loads((worker/'episodes.json').read_bytes())['rows']
main=[r for r in rows if r['phase']=='main'];assert len(main)==480
arms=('C','G','ZG','SL0','ZSL0','SL1','ZSL1','Bstar0');worlds=reading['comparisons']['worlds']
by={(r['arm'],r['world'],r['tape']):r for r in main};comps=reading['comparisons']
def episode_values(arm,world):return [by[arm,world,t] for t in ((-1,) if arm=='C' else (0,1))]
fields=('J','mean_served','service_p10','team_zero_ticks','longest_team_zero_run','first_segment_team_zero_ticks','subsequent_team_zero_ticks','never_served_users','mean_user_longest_gap','p90_user_longest_gap','max_user_longest_gap','mean_path_length_m','mean_sinr_quality','takeovers')
levels={a:{f:float(np.mean([np.mean([r['metrics'][f] for r in episode_values(a,w)]) for w in worlds])) for f in fields} for a in arms}
for a in arms:
 for f in fields:assert np.isclose(levels[a][f],comps['levels'][a][f]['mean'],rtol=0,atol=1e-12),(a,f)
pair_checks=0
for name,table in {**comps['all28_pairs'],**comps['primary']}.items():
 a,b=name.split('-')
 for f in fields:
  vector=np.array([np.mean([r['metrics'][f] for r in episode_values(a,w)])-np.mean([r['metrics'][f] for r in episode_values(b,w)]) for w in worlds])
  assert np.array_equal(vector,table[f]['world_values']),(name,f)
  pair_checks+=1
zero_episodes=[];raw_reductions=0
raw_summary={}
for row in main:
 p=worker/row['raw']['path'];assert identity(p,worker)==row['raw']
 with np.load(p,allow_pickle=False) as z:
  reward=z['reward'];served=z['served'];m=z['user_service_mask'];con=z['connections'];positions=z['positions'];quality=z['sinr_quality']
  assert np.array_equal(m,con.any(axis=1)) and np.array_equal(served,m.sum(axis=1))
  assert np.allclose(reward,.7*served/50+.3*quality,rtol=0,atol=1e-12)
  longest=[];leading=[];trailing=[];never=0
  for u in range(50):
   indices=np.flatnonzero(m[:,u]);gaps=np.diff(np.r_[-1,indices,256])-1
   longest.append(int(gaps.max()));leading.append(int(gaps[0]));trailing.append(int(gaps[-1]));never+=int(len(indices)==0)
   original=row['metrics']['user_service'][u]
   assert (original['served_ticks'],original['longest_gap'],original['leading_gap'],original['trailing_gap'])==(len(indices),longest[-1],leading[-1],trailing[-1])
  zero=served==0;edges=np.flatnonzero(np.diff(np.r_[False,zero,False].astype(int)))
  ranges=[{'start':int(a),'stop':int(b),'length':int(b-a)} for a,b in zip(edges[::2],edges[1::2])]
  metric={'J':float(reward.mean()),'mean_served':float(served.mean()),'service_p10':float(np.quantile(served,.1)),
          'team_zero_ticks':int(zero.sum()),'first_segment_team_zero_ticks':int(zero[:4].sum()),'subsequent_team_zero_ticks':int(zero[4:].sum()),
          'longest_team_zero_run':max([r['length'] for r in ranges],default=0),'never_served_users':never,
          'mean_user_longest_gap':float(np.mean(longest)),'p90_user_longest_gap':float(np.quantile(longest,.9)),'max_user_longest_gap':max(longest),
          'mean_path_length_m':float(np.linalg.norm(np.diff(positions,axis=0),axis=-1).sum(axis=0).mean()),'mean_sinr_quality':float(quality.mean())}
  for f,v in metric.items():assert np.isclose(v,row['metrics'][f],rtol=0,atol=1e-12),(row['arm'],row['world'],f)
  raw_reductions+=len(metric)
  key=(row['arm'],row['world'],row['tape']);raw_summary[key]={**metric,'mean_leading_gap':float(np.mean(leading)),'mean_trailing_gap':float(np.mean(trailing))}
  if ranges:zero_episodes.append({'arm':row['arm'],'world':row['world'],'tape':row['tape'],'runs':ranges,**metric})
events={a:[] for a in ('ZG','ZSL0','ZSL1')};checkfiles=[]
for item in reading['results']:
 p=reader/item['checks']['path'];assert identity(p,reader)==item['checks'];checkfiles.append(item['checks'])
 check=json.loads(p.read_bytes());assert check['raw']==item['raw'] and check['work']==item['work']
 spec=check['spec']
 for event in check['takeover_comparisons']:
  events[spec['arm']].append({**spec,**event})
assert len(checkfiles)==480
eventstats={}
for a,items in events.items():
 counts=collections.Counter('none' if e['first_regained_contact_offset'] is None else str(e['first_regained_contact_offset']) for e in items)
 eventstats[a]={'takeovers':len(items),'worlds':len({e['world'] for e in items}),'episodes':len({(e['world'],e['tape']) for e in items}),
   'category_changed':sum(e['category_changed'] for e in items),'motion_changed':sum(e['motion_changed'] for e in items),
   'next4_first_contact_offset':dict(counts),'by_agent':dict(collections.Counter(e['agent'] for e in items)),
   'by_world':dict(collections.Counter(e['world'] for e in items))}
 assert len(items)==sum(r['metrics']['takeovers'] for r in main if r['arm']==a)
for a in arms:
 episodes=[r for r in main if r['arm']==a]
 levels[a].update(episodes=len(episodes),team_zero_episodes=sum(r['metrics']['team_zero_ticks']>0 for r in episodes),
   never_served_range=[min(r['metrics']['never_served_users'] for r in episodes),max(r['metrics']['never_served_users'] for r in episodes)],
   mean_leading_gap=float(np.mean([raw_summary[a,r['world'],r['tape']]['mean_leading_gap'] for r in episodes])),
   mean_trailing_gap=float(np.mean([raw_summary[a,r['world'],r['tape']]['mean_trailing_gap'] for r in episodes])),
   episode_cpu_seconds=float(np.mean([r['episode_cpu_seconds'] for r in episodes])),
   gate_query_cpu_seconds=float(np.mean([r['times']['gate_query_cpu_seconds'] for r in episodes])),
   native_step_cpu_seconds=float(np.mean([r['times']['native_step_cpu_seconds'] for r in episodes])),
   raw_write_cpu_seconds=float(np.mean([r['times']['raw_write_cpu_seconds'] for r in episodes])))
selected=set(r['world'] for r in zero_episodes)
extremes={}
for name in comps['primary']:
 values=comps['primary'][name]['J']['world_values'];order=np.argsort(values)
 extremes[name]={'lowest':[(worlds[int(i)],values[int(i)]) for i in order[:3]],'highest':[(worlds[int(i)],values[int(i)]) for i in order[-3:]]}
 selected.add(worlds[int(order[0])]);selected.add(worlds[int(order[-1])])
cases=[]
for world in sorted(selected):
 case={'world':world,'episodes':[]}
 for a in arms:
  for row in episode_values(a,world):
   case['episodes'].append({'arm':a,'tape':row['tape'],**raw_summary[a,world,row['tape']],
      'takeovers':row['metrics']['takeovers'],'fallback_decisions':row['metrics']['fallback_decisions']})
 cases.append(case)
def compact(table):return {name:{f:{k:v for k,v in stat.items() if k!='world_values'} for f,stat in sub.items() if f in fields} for name,sub in table.items()}
out={'status':'INDEPENDENT_RAW_ARITHMETIC_VERIFIED','worker_root':str(worker),'reader_root':str(reader),
 'worker_summary_sha256':sha(worker/'summary.json'),'reading_sha256':sha(reader/'reading.json'),
 'scope':'Post-hoc all480 main raw arithmetic and stored-query evidence; no controller, model, environment or counterfactual reward queries. Selected examples are descriptive extrema, not a new test panel.',
 'all480_raw_files_verified':True,'all480_reader_check_files_verified':True,'native_metric_reductions':raw_reductions,'all_user_gap_records_verified':480*50,'paired_vector_checks':pair_checks,
 'levels':levels,'primary':compact(comps['primary']),'interactions':compact(comps['interactions']),
 'event_stats':eventstats,'all_team_zero_episodes':zero_episodes,'J_extremes':extremes,'selected_world_cases':cases,
 'reader_inventory':{'checks':checkfiles,'allocated_bytes':allocated(reader),'compact':[identity(reader/n,reader) for n in ('reading.json','summary.json','config.json','launch-manifest.json','process-exit.json')]},
 'scientific_queries':0,'new_native_steps':0,'new_actor_forwards':0,'new_C_calls':0,
 'scoped_cpu_seconds':sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN))),
 'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'observed_epoch':time.time()}
print(json.dumps(out,sort_keys=True,indent=2,allow_nan=False))
