"""Narrow original-schema producer and independent complete data-only reader."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import zlib
from . import contract as c,evidence as e


def teacher(infos):
    values=[v['contract_reward'] for v in infos]
    if not values or not all(math.isfinite(v) for v in values):raise ValueError('finite complete teacher labels required')
    return max(range(len(values)),key=lambda i:(values[i],-i))


def arrays(records):
    import numpy as np
    geometry={'initial_positions_xyz','user_positions_xy','bs_xyz'}
    metadata=[];layouts=[];offsets=[0]
    for r in records:
        metadata.append({k:v for k,v in r.items() if k!='layouts_xyz' and k!='features'})
        metadata[-1]['identity']={k:v for k,v in r['identity'].items() if k not in geometry}
        layouts.extend(r['layouts_xyz']);offsets.append(len(layouts))
    return {'layouts':np.asarray(layouts,dtype=np.float64),
        'users':np.asarray([r['identity']['user_positions_xy'] for r in records],dtype=np.float64),
        'initial':np.asarray([r['identity']['initial_positions_xyz'] for r in records],dtype=np.float64),
        'bs':np.asarray([r['identity']['bs_xyz'] for r in records],dtype=np.float64),
        'offsets':np.asarray(offsets,dtype=np.int64),'metadata':np.asarray(c.encoded(metadata).decode('ascii'))}


def load_shard(path,expected,start,source_sha,input_sha):
    import numpy as np
    c.verify_file(path,expected)
    with np.load(path,allow_pickle=False) as z:
        if set(z.files)!={'layouts','users','initial','bs','offsets','metadata'}:raise ValueError('original compact shard schema required')
        a={k:z[k] for k in z.files}
    metadata=json.loads(str(a['metadata']));n=len(metadata)
    if n!=64 or a['offsets'].dtype!=np.int64 or a['offsets'].shape!=(65,) or a['offsets'][0]!=0 or a['offsets'][-1]!=len(a['layouts']):
        raise ValueError('complete 64-world shard offsets required')
    for key,shape in (('layouts',(len(a['layouts']),6,3)),('users',(64,50,2)),('initial',(64,6,3)),('bs',(64,3))):
        if a[key].dtype!=np.float64 or a[key].shape!=shape or not np.isfinite(a[key]).all():raise ValueError('fixed finite float64 shard geometry')
    records=[]
    for i,r in enumerate(metadata):
        left,right=map(int,a['offsets'][i:i+2])
        if not 1<=right-left<=221:raise ValueError('full lawful raw pool boundaries')
        r['identity']={**r['identity'],'initial_positions_xyz':a['initial'][i].tolist(),
            'user_positions_xy':a['users'][i].tolist(),'bs_xyz':a['bs'][i].tolist()}
        r['layouts_xyz']=a['layouts'][left:right].tolist()
        if r['identity']['world']!=start+i or r['source_sha']!=source_sha or r['input_sha256']!=input_sha:
            raise ValueError('world/source/input shard identity mismatch')
        if len(r['infos'])!=right-left or teacher(r['infos'])!=r['best']:raise ValueError('complete labels and lower-index teacher required')
        records.append(r)
    return records


def partial_records(path,descriptor,source_sha,input_sha):
    c.verify_file(path,descriptor);decoder=zlib.decompressobj(31)
    raw=decoder.decompress(Path(path).read_bytes(),descriptor['complete_bytes']+1)
    if (len(raw)!=descriptor['complete_bytes'] or hashlib.sha256(raw).hexdigest()!=descriptor['complete_sha256']
        or decoder.eof!=descriptor['gzip_eof'] or decoder.unconsumed_tail or decoder.unused_data or not raw.endswith(b'\n')):
        raise ValueError('unchanged complete partial prefix required; no footer/tail repair')
    rows=raw.splitlines()
    if len(rows)!=descriptor['complete_rows']:raise ValueError('partial row denominator changed')
    return parse_partial([json.loads(line) for line in rows],descriptor,source_sha,input_sha)


def parse_partial(rows,descriptor,source_sha,input_sha):
    records=[];current=None
    for row in rows:
        if row['type']=='prepared':
            if current is not None:records.append(current)
            if row['source_sha']!=source_sha or row['input_sha256']!=input_sha:raise ValueError('old partial producer identity mismatch')
            current={'identity':row['identity'],'construction':row['construction'],'features':row['features'],
                'layouts_xyz':row['features']['layouts_xyz'],'infos':[],'source_sha':source_sha,'input_sha256':input_sha}
        elif row['type']=='label':
            if current is None or row['world']!=current['identity']['world'] or row['raw_index']!=len(current['infos']):
                raise ValueError('partial labels out of world/raw chronology')
            current['infos'].append(row['info'])
        else:raise ValueError('unexpected original partial record')
    if current is not None:records.append(current)
    if [r['identity']['world'] for r in records]!=descriptor['complete_worlds']+[descriptor['incomplete_world']]:
        raise ValueError('original partial world denominator changed')
    for record in records[:-1]:
        if len(record['infos'])!=len(record['layouts_xyz']):raise ValueError('incomplete old world cannot enter compatibility')
        record['best']=teacher(record['infos'])
    last=records[-1]
    if len(last['infos'])!=descriptor['incomplete_labels'] or len(last['layouts_xyz'])!=descriptor['incomplete_candidates']:
        raise ValueError('original excluded incomplete world changed')
    return records[:-1],{'world':last['identity']['world'],'retained_labels':len(last['infos']),
        'candidates':len(last['layouts_xyz']),'excluded_from_complete_compatibility':True}


def exact(a,b,name,diagnostics):
    okay=c.encoded(a)==c.encoded(b)
    row={'check':name,'passed':okay,'comparison':'exact original serialized identity'}
    if not okay:row.update(actual=a,expected=b)
    diagnostics.write(row)
    if not okay:raise AssertionError('exact data identity mismatch: '+name)


def physical(actual,expected,name,diagnostics):
    """All keys, floats at frozen tolerance; integer/string/bool discrete fields exact."""
    errors=[];numeric=[];discrete=[]
    def visit(a,b,path):
        if isinstance(a,dict) and isinstance(b,dict):
            if set(a)!=set(b):errors.append({'field':path,'reason':'key set'});return
            for key in sorted(a):visit(a[key],b[key],path+'.'+key)
        elif isinstance(a,list) and isinstance(b,list):
            if len(a)!=len(b):errors.append({'field':path,'reason':'shape'});return
            for i,(x,y) in enumerate(zip(a,b)):visit(x,y,f'{path}[{i}]')
        elif type(a) is float and type(b) is float:
            error=abs(a-b);okay=math.isfinite(a) and math.isfinite(b) and error<=1e-10+1e-10*abs(b)
            numeric.append({'field':path,'max_abs_error':error if math.isfinite(error) else None})
            if not okay:errors.append({'field':path,'reason':'finite float atol=rtol=1e-10'})
        else:
            discrete.append(path)
            if type(a) is not type(b) or a!=b:errors.append({'field':path,'reason':'exact discrete/type'})
    visit(actual,expected,'info')
    row={'check':name,'passed':not errors,'numeric':numeric,'discrete_fields':discrete,'errors':errors,
        'atol':1e-10,'rtol':1e-10,'equal_nan':False}
    if errors:row.update(actual=actual,expected=expected)
    diagnostics.write(row)
    if errors:raise AssertionError('physical data mismatch: '+name)


def compare_world(actual,saved,bank_module,diagnostics,label):
    exact(actual['identity'],saved['identity'],label+' world identity',diagnostics)
    exact(bank_module.features(actual),bank_module.features(saved),label+' ordered outcome-free features',diagnostics)
    exact(actual['construction'],saved['construction'],label+' raw metadata/RNG',diagnostics)
    exact(len(actual['infos']),len(saved['infos']),label+' complete candidate count',diagnostics)
    for i,(a,b) in enumerate(zip(actual['infos'],saved['infos'])):
        diagnostics.bill.charge('compatibility_label_attempts')
        physical(a,b,f'{label}/{i} physical fields',diagnostics)
        diagnostics.bill.charge('compatibility_labels')
    exact(teacher(actual['infos']),saved['best'],label+' lower-index teacher',diagnostics)


def acquire(store,native,bank_module,source_sha,input_sha):
    import numpy as np
    from experiments.candidates.typed_joint_skill_decision.b04 import evidence as original
    split,local,worlds=c.shard(store.index);records=[]
    partial=store.data_prefix+'-partial.jsonl.gz';journal=e.Trace(store.allowed(partial),store.bill)
    try:
        for world in worlds:
            store.bill.check();store.bill.shared.locate('producer',store.index,world)
            store.bill.charge('producer_worlds_attempted')
            env,identity,raw,f,construction,seconds=bank_module.prepare(native,world)
            journal.write({'type':'prepared','identity':identity,'features':f,'construction':construction,
                'source_sha':source_sha,'input_sha256':input_sha})
            before=store.bill.counter_snapshot()['static_calls'];infos=[]
            for i,r in enumerate(raw):
                store.bill.shared.locate('producer',store.index,world,i)
                info=original.plain(native.host.static_evaluate(env,r['positions_xyz'],allow_a2a=True));infos.append(info)
                journal.write({'type':'label','world':world,'raw_index':i,'info':info})
            records.append({'identity':identity,'layouts_xyz':f['layouts_xyz'],'construction':construction,'infos':infos,
                'best':teacher(infos),'prepare_seconds':seconds,'static_attempts':store.bill.counter_snapshot()['static_calls']-before,
                'source_sha':source_sha,'input_sha256':input_sha})
            store.bill.charge('producer_worlds_completed');store.bill.shared.flush()
        original.npz_write(store,store.data_prefix+'.npz',arrays(records))
    finally:journal.close()
    Path(store.allowed(partial)).unlink()
    store.bill.charge('producer_shards_completed')
    return {'split':split,'shard':local,'worlds':64,'labels':sum(len(r['infos']) for r in records),
        'world_candidate_counts':[[r['identity']['world'],len(r['infos']),r['best']] for r in records],'journal_instrumentation':journal.timing()}


def rebuild(store,native,bank_module,saved,value,root):
    import numpy as np
    from experiments.candidates.typed_joint_skill_decision.b04 import evidence as original
    split,local,worlds=c.shard(store.index)
    diagnostic_name=store.data_prefix+'-checks.jsonl.gz';diagnostics=e.Trace(store.allowed(diagnostic_name),store.bill,diagnostics=True)
    partial=store.data_prefix+'-partial.jsonl.gz';journal=e.Trace(store.allowed(partial),store.bill)
    rebuilt=[];checks=[];compatibility=[];excluded=None
    try:
        if store.index<39:
            r=value['reference'];name=f'raw/bank/train/{local:04d}.npz'
            compatibility=load_shard(c.relative(r['root'],name),r['files'][name],worlds.start,r['old_source_sha'],r['old_input_sha256'])
        elif store.index==39:
            r=value['reference'];compatibility,excluded=partial_records(c.partial_path(root,value),r['partial'],r['old_source_sha'],r['old_input_sha256'])
        for n,world in enumerate(worlds):
            store.bill.check();store.bill.shared.locate('reader',store.index,world);store.bill.charge('reader_worlds_attempted')
            env,identity,raw,f,construction,_=bank_module.prepare(native,world)
            current={'identity':identity,'features':f,'layouts_xyz':f['layouts_xyz'],'construction':construction,'infos':[]}
            record=saved[n]
            exact(identity,record['identity'],f'{world} independent reset/RNG/geometry',diagnostics)
            exact(f,bank_module.features(record),f'{world} ordered raw features',diagnostics)
            exact(construction,record['construction'],f'{world} construction',diagnostics)
            for i,r in enumerate(raw):
                store.bill.shared.locate('reader',store.index,world,i)
                info=original.plain(native.host.static_evaluate(env,r['positions_xyz'],allow_a2a=True));current['infos'].append(info)
                journal.write({'world':world,'raw_index':i,'positions_xyz':r['positions_xyz'].tolist(),'info':info})
                physical(info,record['infos'][i],f'{world}/{i} independent physical fields',diagnostics)
                rebuilt.append([info['contract_reward'],info['coverage_backhauled'],info['frontend_capacity_with_path_mbps']])
            best=teacher(current['infos']);exact(best,record['best'],f'{world} lower-index teacher',diagnostics)
            if n<len(compatibility):
                store.bill.charge('compatibility_attempts')
                compare_world(current,compatibility[n],bank_module,diagnostics,f'{world} old compatibility')
                store.bill.charge('compatibility_worlds')
            checks.append({'world':world,'M':len(raw),'teacher':best,'attempts':len(raw),'completed':len(raw)})
            store.bill.charge('reader_worlds_completed');store.bill.shared.flush()
        if store.index==0:
            permutations=[]
            for record in saved[:4]:
                world=record['identity']['world'];store.bill.shared.locate('reader',0,world)
                env=native.host.make_host(world,area_size=5000);x=np.asarray(record['layouts_xyz'][record['best']],dtype=np.float64)
                orders=[list(range(6)),list(reversed(range(6))),[1,2,3,4,5,0],sorted(range(6),key=lambda i:tuple(x[i]))]
                for order in orders:
                    store.bill.charge('permutation_reads')
                    info=original.plain(native.host.static_evaluate(env,x[order],allow_a2a=True));store.bill.charge('permutation_completed')
                    permutations.append({'world':world,'teacher':record['best'],'row_permutation':order,'static':info,
                        'raw_J':record['infos'][record['best']]['contract_reward'],'difference_J':info['contract_reward']-record['infos'][record['best']]['contract_reward'],
                        'scope':'row-permutation differences retained as science; no invariance gate'})
            store.gzip('raw/engineering/static-permutations.json.gz',permutations)
        original.npz_write(store,store.data_prefix+'.npz',{'J_C_frontend':np.asarray(rebuilt,dtype=np.float64),'records':np.asarray(c.encoded(checks).decode('ascii'))})
    finally:
        journal.close();diagnostics.close()
        store.register(diagnostic_name,content_format='gzip-jsonl',record_count=diagnostics.rows)
    Path(store.allowed(partial)).unlink();store.bill.charge('reader_shards_completed')
    return {'split':split,'shard':local,'worlds':64,'labels':len(rebuilt),'compatibility_worlds':len(compatibility),
        'compatibility_labels':sum(len(r['infos']) for r in compatibility),'excluded_old_partial':excluded,
        'checks':diagnostics.rows,'worlds_read':checks,'journal_instrumentation':journal.timing(),'diagnostic_instrumentation':diagnostics.timing(),
        'trust':'fresh source-pinned rebuild; independent saved-data comparisons, not independent radio physics; fresh bank sealed for future evaluation'}
