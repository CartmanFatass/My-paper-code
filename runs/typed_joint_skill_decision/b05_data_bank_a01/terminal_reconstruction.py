"""Read existing B05 records only; no NumPy, host, teacher, RNG or model execution."""
from pathlib import Path
import ast, collections, datetime, gzip, hashlib, json, math, resource, struct, time, zipfile
ROOT=Path(__file__).resolve().parent
START=time.process_time();WALL=time.monotonic()
def load(path):return json.loads(Path(path).read_bytes())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def plain_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def array_bytes(z,name):
    b=z.read(name+'.npy');assert b[:6]==b'\x93NUMPY'
    version=tuple(b[6:8]);start,size=(10,struct.unpack_from('<H',b,8)[0]) if version==(1,0) else (12,struct.unpack_from('<I',b,8)[0])
    header=ast.literal_eval(b[start:start+size].decode('latin1'));return header,b[start+size:]
def existing_world(path,local):
    with zipfile.ZipFile(path) as z:
        h,b=array_bytes(z,'metadata');assert h['shape']==() and h['descr'].startswith('<U')
        row=json.loads(b.decode('utf-32-le').rstrip('\0'))[local]
        h,o=array_bytes(z,'offsets');assert h['descr']=='<i8';offsets=struct.unpack('<'+str(len(o)//8)+'q',o)
        h,b=array_bytes(z,'layouts');assert h['descr']=='<f8' and h['shape'][1:]==(6,3)
        def layout(i):
            flat=struct.unpack_from('<18d',b,(offsets[local]+i)*18*8)
            return [list(flat[j:j+3]) for j in range(0,18,3)]
        layouts=[layout(i) for i in range(offsets[local+1]-offsets[local])]
        extras={}
        for key,perworld in (('users',100),('initial',18),('bs',3)):
            h,b=array_bytes(z,key);assert h['descr']=='<f8'
            extras[key]=list(struct.unpack_from('<'+str(perworld)+'d',b,local*perworld*8))
    return row,layouts,extras
summary=load(ROOT/'summary.json');manifest=load(ROOT/'artifact-manifest.json')
assert summary['status']=='partial_or_failed' and summary['last_child']==['reader',9]
children=[];producer_worlds=[];last_reaped=0.0;phase_cpu=collections.defaultdict(float)
for stage,count in (('producer',258),('reader',10)):
    for index in range(count):
        base=ROOT/f'raw/process/{stage}/{index:04d}'
        s=load(base/'summary.json');x=load(base/'process-exit.json');ctx=load(base/'context.json')
        assert s['stage']==stage and s['shard']==index and s['launch_sha']==summary['launch_sha'] and s['input_sha256']==summary['input_sha256']
        assert x['terminal_status']=='reaped' and x['child_identity']==s['config']['child_identity']
        assert x['context_sha256']==sha(base/'context.json')
        assert not s['imports_after']['forbidden_modules'] and not s['config']['imports_before_hosts']['forbidden_modules']
        wanted=2 if stage=='reader' and index==9 else 0
        assert x['exit_code']==wanted and (s['error'] is not None)==bool(wanted)
        reaped=x['aggregate_cpu_after_reap']['reaped_children_seconds'];delta=reaped-last_reaped;assert delta>=0;last_reaped=reaped;phase_cpu[stage]+=delta
        children.append({'stage':stage,'shard':index,'pid_identity':x['child_identity'],'exit':x['exit_code'],'status':s['status'],'reaped_cpu_increment_seconds':delta,'child_last_record_cpu_seconds':s['bill']['cpu']['self_seconds'],'child_wall_seconds':s['bill']['wall_seconds'],'max_rss_kib':s['bill']['cpu']['self_peak_rss_kib'],'error':s['error']})
        if stage=='producer':
            assert s['result']['worlds']==64
            producer_worlds.extend(s['result']['world_candidate_counts'])
assert [r[0] for r in producer_worlds]==list(range(109400000,109416000))+list(range(109420000,109420512))
assert sum(x[1] for x in producer_worlds)==summary['producer_labels']==2844367
checks={'rows':0,'passed':0,'failed':[],'scope_max_abs_errors':{},'failure_world_max_abs_errors':{},'failure_world_exact_checks':[]}
for index in range(10):
    p=ROOT/f'raw/label-reader/train/{index:04d}-checks.jsonl.gz'
    with gzip.open(p,'rt') as stream:
        for line in stream:
            row=json.loads(line);checks['rows']+=1;checks['passed']+=bool(row['passed'])
            if not row['passed']:checks['failed'].append({'path':str(p.relative_to(ROOT)),'row':row})
            scope='old_compatibility' if 'old compatibility' in row['check'] else 'new_bank_reconstruction'
            group=checks['scope_max_abs_errors'].setdefault(scope,{})
            for item in row.get('numeric',[]):
                key=item['field'];v=item['max_abs_error'];assert v is not None
                group[key]=max(group.get(key,0),v)
                if row['check'].startswith('109400630 '):
                    g=checks['failure_world_max_abs_errors'].setdefault(scope,{})
                    g[key]=max(g.get(key,0),v)
            if row['check'].startswith('109400630 ') and 'numeric' not in row:
                checks['failure_world_exact_checks'].append(row)
assert checks['rows']==summary['bill']['counters']['reader_checks']==222547 and len(checks['failed'])==1
oldpath=Path('/home/fires/hmasd-wsl/temp/directions/typed_joint_skill_decision/b05-data-reference/raw/bank/train/0009.npz');newpath=ROOT/'raw/bank/train/0009.npz'
old,ox,og=existing_world(oldpath,54);new,nx,ng=existing_world(newpath,54)
assert old['identity']['world']==new['identity']['world']==109400630 and len(nx)==169
assert old['identity']==new['identity'] and old['construction']==new['construction'] and ox==nx and og==ng
values={}
for label,record in (('old',old),('new_producer',new)):
    js=[r['contract_reward'] for r in record['infos']];top=max(js)
    assert max(range(len(js)),key=lambda i:(js[i],-i))==record['best']
    values[label]={'source_sha':record['source_sha'],'input_sha256':record['input_sha256'],'teacher':record['best'],'candidate_count':len(js),'exact_maximizers':[i for i,x in enumerate(js) if x==top],'top_J_repr':repr(top),'top_J_hex':top.hex(),'J_57_minus_50':js[57]-js[50],'J_57_minus_50_in_top_ULPs':(js[57]-js[50])/math.ulp(top),'top_nonmax_gap':top-max(x for x in js if x<top),'selected_candidates':{str(i):{'J_repr':repr(js[i]),'J_hex':js[i].hex(),'info':record['infos'][i],'raw_metadata':record['construction']['raw_metadata'][i],'layout_xyz':nx[i]} for i in (50,57)}}
reader_infos=[]
with gzip.open(ROOT/'raw/label-reader/train/0009-partial.jsonl.gz','rt') as f:
    for line in f:
        row=json.loads(line)
        if row['world']==109400630:
            assert row['raw_index']==len(reader_infos);reader_infos.append(row['info'])
assert len(reader_infos)==169 and reader_infos==new['infos']
perms=load if False else None
with gzip.open(ROOT/'raw/engineering/static-permutations.json.gz','rt') as f:perms=json.load(f)
for p in perms:assert p['scope'].startswith('row-permutation')
output={'schema':1,'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_reader_sha256':sha(__file__),'artifact_manifest_sha256':sha(ROOT/'artifact-manifest.json'),'scope':'all existing child witnesses/check rows plus failed-world stored arithmetic only; zero regenerated worlds/static/native/model/fit','operation_status':summary['status'],'counts':summary['bill']['counters'],'producer_worlds':len(producer_worlds),'producer_labels':sum(x[1] for x in producer_worlds),'producer_M_range':[min(x[1] for x in producer_worlds),max(x[1] for x in producer_worlds)],'phase_reaped_cpu_seconds':dict(phase_cpu),'phase_cpu_scope':'increments in recorded cumulative RUSAGE_CHILDREN; first increment includes any prior setup child CPU; parent final-write tail separately unknown','children':children,'full_recorded_diagnostics':checks,'failure_world':{'world':109400630,'old_file_sha256':sha(oldpath),'new_file_sha256':sha(newpath),'identities_exact':True,'initial_user_bs_geometry_exact':True,'ordered_layouts_exact':True,'construction_RNG_exact':True,'candidate_50_57_identical_ordered_layout':nx[50]==nx[57],'candidate_50_57_same_sorted_sites':sorted(nx[50])==sorted(nx[57]),'new_reader_all169_infos_exact_to_new_producer':True,'metadata_identity':new['identity'],'layout_sha256':plain_sha(nx),'observed':values,'causal_boundary':'stored old/new numeric values differ within fixed float tolerance yet exact argmax changes; version/node/process changes not causally separated; no tolerance/tie repair or new query'},'permutation_reads':perms,'remaining':{'reader_worlds_not_constructed':16512-631,'reader_worlds_not_counted_complete':16512-630,'reader_shards_not_completed':258-9,'old_compatibility_worlds_unattempted':2501-631,'old_compatibility_worlds_not_passed':2501-630,'fresh_reader_worlds_unattempted':512},'reader_cpu_seconds':time.process_time()-START,'reader_wall_seconds':time.monotonic()-WALL,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'unmeasured_support':'unknown, not zero'}
(ROOT/'terminal-reconstruction.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({k:output[k] for k in ('producer_worlds','producer_labels','producer_M_range','phase_reaped_cpu_seconds','remaining','reader_cpu_seconds','reader_wall_seconds','max_rss_kib')},indent=2))
print(json.dumps({'check_rows':checks['rows'],'failed':checks['failed'],'failure_world_max_errors':checks['failure_world_max_abs_errors'],'J_values':{k:{x:v[x] for x in ('teacher','exact_maximizers','top_J_repr','top_J_hex','J_57_minus_50','J_57_minus_50_in_top_ULPs','top_nonmax_gap')} for k,v in values.items()},'same_sites':output['failure_world']['candidate_50_57_same_sorted_sites']},indent=2))
