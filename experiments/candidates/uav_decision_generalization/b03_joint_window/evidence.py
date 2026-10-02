"""Bound saved evidence, strict model state and actual process/event accounting."""
import ast
import contextlib
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import time
import numpy as np
from . import contract as c

OPTIMIZERS=tuple(c.OPTIMIZER_TOTALS['H'])
NORMALIZERS=('obs_norm','state_norm','value_norm_coordinator','value_norm_discoverer')
MODULES=('skill_coordinator','skill_discoverer','team_discriminator','individual_discriminator')


def jsonable(value):
    if isinstance(value,dict):return {str(k):jsonable(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [jsonable(v) for v in value]
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    if hasattr(value,'detach'):return value.detach().cpu().numpy().tolist()
    if isinstance(value,Path):return str(value)
    if isinstance(value,float) and np.isinf(value):return 'inf' if value>0 else '-inf'
    return value


def finite(value,label):
    if isinstance(value,dict):
        for k,v in value.items():finite(v,label+'.'+str(k))
    elif isinstance(value,(list,tuple)):
        for v in value:finite(v,label)
    elif value is not None:
        if hasattr(value,'detach'):value=value.detach().cpu().numpy()
        if isinstance(value,(np.ndarray,np.number,float)) and not np.isfinite(value).all():raise ValueError('nonfinite '+label)


def hash_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def identity(path,root=None):
    path=Path(path)
    return {'path':str(path.relative_to(root)) if root is not None else str(path),'bytes':path.stat().st_size,'sha256':hash_file(path)}


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);partial=path.with_suffix(path.suffix+'.tmp')
    partial.write_text(json.dumps(jsonable(value),sort_keys=True,allow_nan=False,separators=(',',':'))+'\n');partial.replace(path)


def write_npz(path,arrays):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise FileExistsError('no duplicate scientific trace')
    for key,value in arrays.items():
        if np.asarray(value).dtype==object:raise ValueError('no object/pickle raw data: '+key)
        finite(value,key)
    partial=path.with_suffix('.partial.npz');np.savez_compressed(partial,**arrays);partial.replace(path)


def bound_json(path,sha):
    if hash_file(path)!=sha:raise ValueError('bound input bytes changed')
    return json.loads(Path(path).read_bytes())


def modules(agent):return {name:getattr(agent,name) for name in MODULES if getattr(agent,name,None) is not None}


def digest_agent(agent):
    h=hashlib.sha256()
    for name,module in modules(agent).items():
        for key,value in module.state_dict().items():
            array=value.detach().cpu().contiguous().numpy();h.update(f'{name}.{key}|{array.dtype}|{array.shape}'.encode());h.update(array.tobytes())
    for name in NORMALIZERS:
        norm=getattr(agent,name,None)
        if norm is not None:h.update(json.dumps(jsonable(vars(norm)),sort_keys=True,allow_nan=False).encode())
    return h.hexdigest()


def array_digest(*arrays):
    h=hashlib.sha256()
    for value in arrays:
        array=np.ascontiguousarray(value);h.update(f'{array.dtype}|{array.shape}'.encode());h.update(array.tobytes())
    return h.hexdigest()


def seed_rng(seed):
    import torch
    random.seed(int(seed));np.random.seed(int(seed));torch.manual_seed(int(seed))


def rng_state():
    import torch
    return {'python':jsonable(random.getstate()),'numpy':jsonable(np.random.get_state()),'torch':torch.get_rng_state().tolist()}


def restore_rng(value):
    import torch
    def tuples(x):return tuple(tuples(v) for v in x) if isinstance(x,list) else x
    random.setstate(tuples(value['python']));n=value['numpy'];np.random.set_state((n[0],np.asarray(n[1],dtype=np.uint32),int(n[2]),int(n[3]),float(n[4])))
    torch.set_rng_state(torch.tensor(value['torch'],dtype=torch.uint8))


class Meter:
    def __init__(self,prior):
        if set(prior)!={'schema','prior_cpu_seconds','prior_counts'} or prior['schema']!=1 or not np.isfinite(prior['prior_cpu_seconds']) or prior['prior_cpu_seconds']<0 or not isinstance(prior['prior_counts'],dict):raise ValueError('cumulative input cost ledger')
        if any(type(v)!=int or v<0 for v in prior['prior_counts'].values()):raise ValueError('nonnegative prior count ledger')
        self.prior=prior;self.counts={};self.calls={};self.phase='entry';self.started_wall=time.perf_counter();self.constructions=[]
    def add(self,key,amount=1):self.counts[key]=self.counts.get(key,0)+int(amount)
    def observe_forward(self,key,args):
        arrays=[a for a in args if hasattr(a,'shape')]
        shapes=[list(a.shape) for a in arrays];rows=int(arrays[0].shape[0]) if arrays and arrays[0].ndim else 1
        address=self.phase+'|'+key;item=self.calls.setdefault(address,{'calls':0,'leading_rows':0,'input_shapes':{}})
        item['calls']+=1;item['leading_rows']+=rows;shape=json.dumps(shapes);item['input_shapes'][shape]=item['input_shapes'].get(shape,0)+1
        if key=='discoverer_actor.evaluate_actions':
            # Native PPO calls this method directly, bypassing Module.__call__.
            # Its recurrent observations are [T,B,F], so leading_rows is not
            # the number of agent-tick presentations.
            contexts=int(np.prod(arrays[0].shape[:-1]))
            item['agent_tick_contexts']=item.get('agent_tick_contexts',0)+contexts
            self.add('direct_actor_evaluate_calls');self.add('direct_actor_evaluate_agent_tick_contexts',contexts)
        if self.phase.startswith('intrinsic/') and key in ('team_discriminator','individual_discriminator'):
            self.add('intrinsic_reward_'+key+'_forward_calls');self.add('intrinsic_reward_'+key+'_forward_contexts',rows)
    def resources(self):
        usage=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN);cpu=usage.ru_utime+usage.ru_stime+child.ru_utime+child.ru_stime
        return {'cpu_seconds':cpu,'cumulative_cpu_seconds':self.prior['prior_cpu_seconds']+cpu,'wall_seconds':time.perf_counter()-self.started_wall,
                'peak_rss_kib':usage.ru_maxrss,'GPU_seconds':0,'cpu_scope':'entry/import/self+finished children; terminal self-report write excluded'}
    def report(self):return {'prior':self.prior,'counts':self.counts,'forward_calls':self.calls,'model_constructions':self.constructions,'resources':self.resources()}


def source_manifest(root):
    """Static local import closure plus all direction files, including DM's reader."""
    root=Path(root);direction=root/'experiments/candidates/uav_decision_generalization/b03_joint_window'
    pending=list(direction.glob('*.py'));seen={}
    pending += [root/'experiments/candidates/coupled_host_joint_skills_stage1'/x for x in ('host.py','adapter.py','configuration.py','models.py','runner.py')]
    def paths(module):
        p=root/Path(*module.split('.'))
        return [p.with_suffix('.py'),p/'__init__.py']
    while pending:
        path=pending.pop()
        if not path.is_file() or path in seen:continue
        seen[path]=hash_file(path);tree=ast.parse(path.read_text());package=list(path.relative_to(root).parts[:-1])
        for node in ast.walk(tree):
            names=[]
            if isinstance(node,ast.Import):names=[x.name for x in node.names]
            elif isinstance(node,ast.ImportFrom):
                base='.'.join(package[:len(package)-node.level+1]) if node.level else ''
                module='.'.join(x for x in (base,node.module or '') if x)
                names=[module]+['.'.join(x for x in (module,a.name) if x) for a in node.names]
            for name in names:
                for p in paths(name):
                    if p.is_file():
                        pending.append(p)
                        for parent in p.relative_to(root).parents:
                            init=root/parent/'__init__.py'
                            if init.is_file():pending.append(init)
    return {str(p.relative_to(root)):sha for p,sha in sorted(seen.items())}


def build_agent(arm,lanes,log_dir,meter):
    import torch
    from .configuration import make_config
    from .models import build_agent as factory
    cfg=make_config(arm,lanes);start=time.process_time();before=meter.phase;meter.phase='construction/'+arm
    seen={};hook=torch.nn.modules.module.register_module_forward_pre_hook(lambda module,args:meter.observe_forward('constructor.'+type(module).__name__,args))
    init=torch.nn.modules.module.register_module_module_registration_hook(lambda module,name,child:seen.setdefault(id(child),child))
    try:agent=factory(cfg,str(log_dir))
    finally:hook.remove();init.remove();meter.phase=before
    meter.add('model_constructions');meter.constructions.append({'arm':arm,'lanes':lanes,'cpu_seconds':time.process_time()-start,
        'registered_modules':len(seen),'parameters_final':{k:sum(p.numel() for p in v.parameters()) for k,v in modules(agent).items()},
        'parameters_constructed_unique':sum(p.numel() for p in {id(p):p for m in seen.values() for p in m.parameters()}.values())})
    return agent,cfg


@contextlib.contextmanager
def instrument_agent(agent,meter):
    hooks=[];originals=[];optimizers={name:0 for name in OPTIMIZERS}
    def wrap(obj,name,key):
        original=getattr(obj,name)
        def counted(*args,**kwargs):meter.observe_forward(key,args);return original(*args,**kwargs)
        setattr(obj,name,counted);originals.append((obj,name,original))
    for root,module in modules(agent).items():
        for name,child in module.named_modules():
            if not name or child in (getattr(agent.skill_discoverer,'actor',None),getattr(agent.skill_discoverer,'critic',None)) or type(child).__name__ in ('StateSetEncoder','SetActorBase','R_Actor','R_Critic'):
                label=root+('.'+name if name else '')
                hooks.append(child.register_forward_pre_hook(lambda mod,args,key=label:meter.observe_forward(key,args)))
    for name in ('evaluate_held_batch','evaluate_training_batch','evaluate_training_batch_ordered'):
        if hasattr(agent.skill_coordinator,name):wrap(agent.skill_coordinator,name,'coordinator.'+name)
    if hasattr(agent.skill_discoverer.actor,'evaluate_actions'):
        wrap(agent.skill_discoverer.actor,'evaluate_actions','discoverer_actor.evaluate_actions')
    for name in ('_compute_high_level_bootstrap_values','_compute_high_level_bootstrap_values_d2','_compute_high_level_bootstrap_values_ha_ctse'):
        if hasattr(agent,name):wrap(agent,name,'agent.'+name)
    for name in OPTIMIZERS:
        optimizer=getattr(agent,name+'_optimizer',None)
        if optimizer is not None:
            def step(opt,args,kwargs,key=name):optimizers[key]+=1;meter.add('optimizer_'+key)
            hooks.append(optimizer.register_step_post_hook(step))
    try:yield optimizers
    finally:
        for hook in hooks:hook.remove()
        for obj,name,original in reversed(originals):setattr(obj,name,original)


def save_checkpoint(agent,config,path,arm,endpoint,launch_sha,meter):
    import torch
    from .configuration import config_dict
    if Path(path).exists():raise FileExistsError('checkpoint already exists')
    payload={'schema':1,'direction':c.DIRECTION,'object':c.OBJECT,'launch_sha':launch_sha,'arm':arm,'endpoint':endpoint,
             'config':config_dict(config),'modules':{k:v.state_dict() for k,v in modules(agent).items()},
             'normalizers':{name:jsonable(vars(getattr(agent,name))) if getattr(agent,name,None) is not None else None for name in NORMALIZERS},
             'state_digest':digest_agent(agent),'optimizer_counts':meter.counts.copy()}
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);partial=path.with_suffix('.partial.pt');torch.save(payload,partial);partial.replace(path)
    return identity(path)


def load_agent(checkpoint,arm,lanes,log_dir,meter):
    import torch
    payload=torch.load(checkpoint,map_location='cpu',weights_only=True)
    if payload.get('schema')!=1 or payload.get('object')!=c.OBJECT or payload['arm']!=arm and not (arm=='H-noD' and payload['arm']=='H' and payload['endpoint']=='initial'):raise ValueError('checkpoint lineage/endpoint identity')
    from .configuration import config_dict,make_config
    if payload['config']!=config_dict(make_config(payload['arm'],16)):raise ValueError('checkpoint frozen scientific configuration')
    agent,config=build_agent(arm,lanes,log_dir,meter)
    if set(payload['modules'])!=set(modules(agent)):raise ValueError('complete checkpoint modules')
    for name,module in modules(agent).items():module.load_state_dict(payload['modules'][name],strict=True)
    for name in NORMALIZERS:
        target=getattr(agent,name,None);state=payload['normalizers'][name]
        if (target is None)!=(state is None):raise ValueError('complete normalizer ownership')
        if target is not None:
            if set(vars(target))!=set(state):raise ValueError('normalizer complete state keys')
            for key,value in state.items():setattr(target,key,np.asarray(value,dtype=getattr(target,key).dtype) if isinstance(getattr(target,key),np.ndarray) else value)
    if digest_agent(agent)!=payload['state_digest']:raise ValueError('checkpoint full state digest')
    agent.train(False)
    return agent,config,payload
