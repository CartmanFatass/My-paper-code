from pathlib import Path
import hashlib,json,os,time,resource,zlib
import numpy as np
started=time.perf_counter();cpu0=time.process_time()
r=Path('/home/wu/projects/HMASD/runs/typed_joint_skill_decision/b04_a01')
manifest=json.loads((r/'artifact-manifest.json').read_bytes())['files']
config=json.loads((r/'config.json').read_bytes());source=config['launch_sha'];inp=config['input_sha256']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
shards=[];worlds=[];labels=0
for p in sorted((r/'raw/bank/train').glob('*.npz')):
 rel=str(p.relative_to(r));digest=sha(p);assert rel in manifest and digest==manifest[rel]['sha256']
 with np.load(p,allow_pickle=False) as z:
  records=json.loads(str(z['metadata']));off=z['offsets'];assert len(off)==65 and len(records)==64 and off[-1]==len(z['layouts'])
  assert z['layouts'].shape[1:]==(6,3) and np.isfinite(z['layouts']).all()
  count=0
  for i,v in enumerate(records):
   w=v['identity']['world'];m=len(v['infos']);assert w==109400000+len(worlds)
   assert v['source_sha']==source and v['input_sha256']==inp and m==off[i+1]-off[i] and 1<=m<=221 and v['static_attempts']==m
   assert [q['index'] for q in v['construction']['raw_metadata']]==list(range(m))
   js=[q['contract_reward'] for q in v['infos']];assert v['best']==max(range(m),key=lambda j:(js[j],-j))
   worlds.append(w);count+=m
  labels+=count
  shards.append({'path':rel,'sha256':digest,'bytes':p.stat().st_size,'worlds':64,'first_world':records[0]['identity']['world'],'last_world':records[-1]['identity']['world'],'complete_saved_labels':count})
partial=[];partial_labels=0;partial_complete_worlds=0
for p in sorted((r/'raw/bank/train').glob('*partial*')):
 data=p.read_bytes();d=zlib.decompressobj(16+zlib.MAX_WBITS);decoded=d.decompress(data)
 lines=decoded.split(b'\n');tail=lines.pop();valid=[];states=[];by={}
 for line in lines:
  if not line:continue
  v=json.loads(line);valid.append(v)
  if v['type']=='prepared':
   w=v['identity']['world'];assert v['source_sha']==source and v['input_sha256']==inp
   m=len(v['features']['layouts_xyz']);assert m==len(v['construction']['raw_metadata'])
   x={'world':w,'candidates':m,'saved_labels':0,'native_rng_sha256':v['identity']['native_rng_sha256']};states.append(x);by[w]=x
  else:
   assert v['type']=='label' and v['world'] in by
   x=by[v['world']];assert v['raw_index']==x['saved_labels'];x['saved_labels']+=1;partial_labels+=1
 for x in states:
  x['all_labels_saved']=x['saved_labels']==x['candidates'];partial_complete_worlds+=int(x['all_labels_saved'])
 partial.append({'path':str(p.relative_to(r)),'sha256':sha(p),'compressed_bytes':len(data),'gzip_complete':d.eof,'valid_json_records':len(valid),'decoded_unterminated_tail_bytes':len(tail),'worlds':states,'limitation':'valid decompressed JSON prefix only; absent trailer and lost process counters preclude exact final attempts or buffer contents'})
allocation=lambda p:sum(x.lstat().st_blocks*512 for x in [p,*p.rglob('*')] if not x.is_symlink())
actual={'canonical_run_allocated_bytes':allocation(r),'direction_runs_allocated_bytes':allocation(r.parent),'source_snapshot_allocated_bytes':allocation(Path(config['source_root']))}
model=Path(config['input_manifest_data']['disk_scope']['retained_model_root']);scratch=Path(config['input_manifest_data']['disk_scope']['own_scratch'])
actual['retained_model_allocated_bytes']=allocation(model);actual['direction_scratch_allocated_bytes']=allocation(scratch) if scratch.exists() else 0
actual['current_declared_scope_bytes']=sum(actual[k] for k in ['direction_runs_allocated_bytes','source_snapshot_allocated_bytes','retained_model_allocated_bytes','direction_scratch_allocated_bytes'])
print(json.dumps({'schema':1,'kind':'read_only_terminal_artifact_reconstruction','operation_source':source,'input_sha256':inp,'saved_shards':shards,'full_shard_worlds':len(worlds),'full_shard_labels':labels,'partial':partial,'partial_saved_labels':partial_labels,'partial_worlds_with_all_labels_saved':partial_complete_worlds,'retained_completed_label_lower_bound':labels+partial_labels,'fit_model_native_counts':0,'no_new_effect_queries':True,'actual_allocation':actual,'reader_support':{'wall_seconds':time.perf_counter()-started,'cpu_seconds':time.process_time()-cpu0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}},indent=2))
