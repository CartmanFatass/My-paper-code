import collections,hashlib,json,math,pathlib,sys,time
import torch
torch.set_num_threads(1)
root=pathlib.Path(sys.argv[1]); destination=pathlib.Path(sys.argv[2])
s=json.loads((root/'summary.json').read_text()); master=hashlib.sha256(b'DISH-RECEIPT-BYPASS-B09/seed/149').hexdigest()
assert s['status']=='COMPLETE' and s['primary']['status']=='COMPLETE'
assert s['master_hex']==master and s['seed']==149
assert s['launch_sha']=='3a749256d2aaf16345308827518283c8d2b91ad7'
initial=torch.load(root/'shared/initial_state.pt',map_location='cpu',weights_only=False)
assert all(int(initial['welford'][k].count)==0 for k in ('actor','snapshot','critic'))
assert not initial['optimizer']['state']
resets=json.loads((root/'shared/resets.json').read_text())
assert resets==s['resets'] and len(resets)==4
facts={'object':s['object'],'master_hex':master,'status':'CHECKED_RECORDED_BYTES_ONLY','source_sha':s['launch_sha'],'initial_optimizer_states':len(initial['optimizer']['state']),'initial_welford_counts':{k:int(initial['welford'][k].count) for k in ('actor','snapshot','critic')},'arms':{},'new_scientific_execution':0}
for mode in ('REPLACE','BYPASS'):
 a=s['arms'][mode]; path=root/mode.lower()/'checkpoint_update16.pt'
 c=torch.load(path,map_location='cpu',weights_only=False)
 assert c['arrival_bridge_mode']==mode and a['arrival_bridge_mode']==mode
 assert a['completed_updates']==16 and a['ordinary_training_transitions']==65536 and a['optimizer_steps']==512
 assert len(a['curves'])==16 and [v['update'] for v in a['curves']]==list(range(1,17))
 assert all(v['losses_finite'] and v['gradient_norms_finite'] and v['learning_rates']==[3e-5,3e-5] for v in a['curves'])
 assert [g['lr'] for g in c['optimizer']['param_groups']]==[3e-5,3e-5]
 assert set(c['model'])==set(initial['model'])
 assert all(torch.isfinite(v).all().item() for v in c['model'].values())
 assert {str(v.dtype) for v in c['model'].values()}=={'torch.float32'}
 assert len(a['evaluation_rows'])==4 and {r['coordinate'] for r in a['evaluation_rows']}==set(resets)
 assert all(r['complete'] and r['reset']==resets[r['coordinate']] and r['arrival_bridge_mode']==mode for r in a['evaluation_rows'])
 d2=sum(float((c['model'][k].double()-v.double()).square().sum()) for k,v in initial['model'].items())
 n2=sum(float(v.double().square().sum()) for v in initial['model'].values())
 relative=math.sqrt(d2/n2); assert math.isclose(relative,a['parameter_movement']['relative_l2_displacement'],rel_tol=1e-10)
 snapshot={k:bool(torch.equal(c['model'][k],v)) for k,v in initial['model'].items() if k.startswith(('snapshot_encoder.','snapshot_bridge.'))}
 if mode=='BYPASS': assert all(snapshot.values())
 facts['arms'][mode]={'updates':a['completed_updates'],'transitions':a['ordinary_training_transitions'],'optimizer_calls':a['optimizer_steps'],'final_mode':c['arrival_bridge_mode'],'welford_counts':{k:int(c['welford'][k].count) for k in ('actor','snapshot','critic')},'optimizer_parameter_step_distribution':dict(collections.Counter(int(v['step']) for v in c['optimizer']['state'].values())), 'relative_l2_movement':relative,'snapshot_parameters_equal_initializer':snapshot,'model_parameter_count':sum(v.numel() for v in c['model'].values()),'checkpoint_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'evaluation_rows':a['evaluation_rows']}
rows={m:{r['coordinate']:r for r in s['arms'][m]['evaluation_rows']} for m in ('REPLACE','BYPASS')}
deltas=[rows['BYPASS'][k]['service_ticks']-rows['REPLACE'][k]['service_ticks'] for k in resets]
means={m:sum(v['service_ticks'] for v in rows[m].values())/4 for m in rows}
assert sum(deltas)/4==s['primary']['Delta_bypass'] and means==s['primary']['means']
facts.update(means=means,condition_order=list(resets),condition_deltas=deltas,Delta_bypass=sum(deltas)/4,band='PLUS24' if sum(deltas)/4>=24 else 'MINUS24' if sum(deltas)/4<=-24 else 'WITHIN',primary=s['primary'],actual_exposure=s['actual_exposure'],cost_before_write=s['cost'])
destination.write_text(json.dumps(facts,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'status':facts['status'],'means':means,'deltas':deltas,'Delta_bypass':facts['Delta_bypass'],'band':facts['band'],'arms':{m:{k:v for k,v in a.items() if k!='evaluation_rows'} for m,a in facts['arms'].items()}},indent=2))
