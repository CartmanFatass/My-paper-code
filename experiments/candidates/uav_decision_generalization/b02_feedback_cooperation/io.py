"""Admission-bound outputs, immutable external files and cumulative CPU accounting."""
import hashlib
import json
import os
from pathlib import Path
import resource
import time
from . import contract as c


def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def identity(path):
    path=Path(path)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':hash_file(path)}


def bound_json(path,expected):
    if hash_file(path)!=expected:raise ValueError('external input hash changed')
    return json.loads(Path(path).read_bytes())


def write_json(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n')
    temporary.replace(path)


def source_identity(root):
    root=Path(root);result={}
    for relative,expected in c.SOURCE_SHA256.items():
        if hash_file(root/relative)!=expected:raise ValueError('frozen dependency changed: '+relative)
        result[relative]=expected
    own=root/'experiments/candidates/uav_decision_generalization/b02_feedback_cooperation'
    for path in sorted(own.glob('*.py')):result[str(path.relative_to(root))]=hash_file(path)
    return result


def verify_calibration(root):
    path=Path(root)/c.CALIBRATION['reading_path']
    value=bound_json(path,c.CALIBRATION['reading_sha256'])
    if (value['status']!='VERIFIED' or value['launch_sha']!=c.CALIBRATION['launch_sha']
            or [(x['lineage'],x['winner']) for x in value['calibrations']]!=list(enumerate(c.CALIBRATION['winners']))):
        raise ValueError('paid Bstar temperature/source identity changed')
    return c.CALIBRATION


def asset_records(path,sha):
    value=bound_json(path,sha)
    if set(value)!={'schema','assets'} or value['schema']!=1 or value['assets']!=list(c.ASSETS):
        raise ValueError('canonical actor identity changed')
    for record in value['assets']:
        p=Path(record['path'])
        if not p.is_absolute() or p.resolve()!=p:raise ValueError('canonical actor path changed')
        if p.stat().st_size!=record['bytes'] or hash_file(p)!=record['sha256']:raise ValueError('canonical actor file changed')
    return value['assets']


def load_actors(records):
    import torch
    from experiments.candidates.uav_fleet_adaptation.b02.model import make_student,state_digest
    models=[]
    for lineage,record in enumerate(records):
        payload=torch.load(record['path'],map_location='cpu',weights_only=True)
        expected={'endpoint':'S','launch_sha':record['launch_sha'],'architecture':[114,128,128,27],
                  'activation':'relu','dtype':'float32','optimizer_steps':8000,'state_sha256':record['state_sha256']}
        if any(payload.get(k)!=v for k,v in expected.items()):raise ValueError('frozen actor payload identity changed')
        state=payload['state_dict']
        if (state_digest(state)!=record['state_sha256'] or any(t.dtype!=torch.float32 or not torch.isfinite(t).all() for t in state.values())):
            raise ValueError('frozen actor tensor identity changed')
        model=make_student(c.ACTOR_SEEDS[lineage]);model.load_state_dict(state,strict=True)
        model.eval().requires_grad_(False);models.append(model)
    verify_actors(models,records)
    return models


def verify_actors(models,records):
    from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
    if len(models)!=2 or len(records)!=2:raise ValueError('both immutable actor lineages required')
    for model,record in zip(models,records):
        if state_digest(model.state_dict())!=record['state_sha256'] or hash_file(record['path'])!=record['sha256']:
            raise ValueError('frozen actor changed during reading/execution')


class Budget:
    def __init__(self,prior):
        if (set(prior)!={'schema','prior_cpu_seconds','synthetic'} or prior['schema']!=1
                or type(prior['prior_cpu_seconds']) not in (float,int) or not 0<=prior['prior_cpu_seconds']<c.MAX_CPU_SECONDS
                or set(prior['synthetic'])!=set(c.SYNTHETIC_LIMITS)):
            raise ValueError('invalid cumulative CPU/synthetic ledger')
        for key,value in prior['synthetic'].items():
            if type(value)!=int or not 0<=value<=c.SYNTHETIC_LIMITS[key]:raise ValueError('synthetic allowance exceeded')
        self.prior=prior;self.started_wall=time.perf_counter();self.synthetic=prior['synthetic'].copy()
    def pay(self,key):
        if key not in self.synthetic or self.synthetic[key]>=c.SYNTHETIC_LIMITS[key]:raise RuntimeError('synthetic allowance exhausted before call: '+key)
        self.check();self.synthetic[key]+=1
    def cpu(self):
        return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
    def check(self):
        if self.prior['prior_cpu_seconds']+self.cpu()>=c.MAX_CPU_SECONDS:
            raise RuntimeError('cumulative one-CPU-hour boundary reached; preserve prefix, no automatic retry')
    def snapshot(self):
        return {'process_and_finished_children_cpu_seconds':self.cpu(),
                'cumulative_cpu_seconds':self.prior['prior_cpu_seconds']+self.cpu(),
                'wall_seconds_since_budget':time.perf_counter()-self.started_wall,'synthetic':self.synthetic.copy(),
                'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'GPU_seconds':0,
                'scope':'process entry/import included in CPU; current high-water RSS; terminal self-report tail excluded'}


def accepted_output(script,args,admission,paths):
    root=Path(script).resolve().parents[4];out=args.out.absolute()
    if (args.launch_sha!=admission['sha'] or str(root)!=paths.get('source_root')
            or str(out)!=paths.get('output_root') or out.resolve()!=out):raise ValueError('admitted source/output/sha mismatch')
    launch=json.loads((out/'launch-manifest.json').read_bytes())
    if any(launch.get(k)!=v for k,v in {'source_root':str(root),'output_root':str(out),'direction':c.DIRECTION,
                                     'sha':admission['sha'],'command_sha256':admission['command_sha256']}.items()):
        raise ValueError('admitted launch invocation mismatch')
    if (out/'config.json').exists() or (out/'raw').exists() or (out/'summary.json').exists():raise FileExistsError('no repeat of prior scientific output')
    budget=Budget(bound_json(args.budget_ledger,args.budget_ledger_sha256))
    budget.check()
    return root,out,budget


def allocated_bytes(root):
    root=Path(root);total=0
    for directory,folders,files in os.walk(root):
        total+=Path(directory).lstat().st_blocks*512
        total+=sum((Path(directory)/name).lstat().st_blocks*512 for name in files)
    return total
