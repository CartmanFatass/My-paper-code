"""Compact numeric bank shards; train view cannot address fresh labels."""
from __future__ import annotations
import hashlib
import json
from collections import OrderedDict
from . import contract as c, evidence as e


def identity(env):
    from .native import rng_identity
    return e.plain({'world':int(env.world_seed),'initial_positions_xyz':env.uav_positions.copy(),
                   'user_positions_xy':env.user_positions.copy(),'bs_xyz':env.ground_bs_positions[0].copy(),
                   'native_rng_sha256':rng_identity(env),'agents':list(env.agents),
                   'transmitter_mask':env._transmitter_mask.copy(),'current_step':env.current_step})


def prepare(native, world):
    import numpy as np
    import time
    t = time.perf_counter()
    env = native.host.make_host(world, area_size=5000)
    original = identity(env)
    rng = np.random.default_rng(world)
    report = {}
    raw = native.p.build_candidates(env, rng, allow_a2a=True, report=report)
    if not 1 <= len(raw) <= 221 or [r['index'] for r in raw] != list(range(len(raw))):
        raise ValueError('complete original ordered raw pool required')
    features = {'users_xy':original['user_positions_xy'],'bs_xyz':original['bs_xyz'],
                'layouts_xyz':[r['positions_xyz'].tolist() for r in raw],
                'kinds':[r['kind'] for r in raw],'ks':[int(r['k']) for r in raw]}
    c.validate_features(features)
    construction = {'report':e.plain(report),'rng_type':type(rng.bit_generator).__name__,
                    'rng_state_sha256':hashlib.sha256(e.encoded(rng.bit_generator.state)).hexdigest(),
                    'raw_metadata':[e.plain({k:v for k,v in r.items() if k!='positions_xyz'}) for r in raw]}
    return env, original, raw, features, construction, time.perf_counter()-t


def features(record):
    if 'features' in record:
        return record['features']
    return {'users_xy':record['identity']['user_positions_xy'],'bs_xyz':record['identity']['bs_xyz'],
            'layouts_xyz':record['layouts_xyz'],'kinds':[r['kind'] for r in record['construction']['raw_metadata']],
            'ks':[int(r['k']) for r in record['construction']['raw_metadata']]}


def rewards(record):
    return record['J'] if 'J' in record else [v['contract_reward'] for v in record['infos']]


def build_bank(store, native, split):
    import numpy as np
    start,count = (c.TRAIN_START,c.TRAIN_COUNT) if split=='train' else (c.FRESH_START,c.FRESH_COUNT)
    for offset in range(0,count,64):
        records=[];layouts=[];users=[];initial=[];bases=[];boundaries=[0]
        partial=e.relative_path(store.root,f'raw/bank/{split}/{offset//64:04d}-partial.jsonl.gz')
        journal=e.Trace(partial,store.bill)
        try:
            for world in range(start+offset,start+min(offset+64,count)):
                env, original, raw, f, construction, seconds = prepare(native,world)
                journal.write({'type':'prepared','identity':original,'features':f,'construction':construction,
                               'source_sha':store.launch_sha,'input_sha256':store.input_sha256})
                before=store.bill.snapshot()['counters']['static_calls'];infos=[]
                for i,r in enumerate(raw):
                    info=e.plain(native.host.static_evaluate(env,r['positions_xyz'],allow_a2a=True))
                    infos.append(info)
                    journal.write({'type':'label','world':world,'raw_index':i,'info':info})
                js=[v['contract_reward'] for v in infos]
                best=max(range(len(js)),key=lambda i:(js[i],-i))
                store.bill.charge('bank_worlds')
                geometry={'initial_positions_xyz','user_positions_xy','bs_xyz'}
                records.append({'identity':{k:v for k,v in original.items() if k not in geometry},
                                'construction':construction,'infos':infos,'best':best,'prepare_seconds':seconds,
                                'static_attempts':store.bill.snapshot()['counters']['static_calls']-before,
                                'source_sha':store.launch_sha,'input_sha256':store.input_sha256})
                layouts.extend(f['layouts_xyz']);boundaries.append(len(layouts))
                users.append(original['user_positions_xy']);initial.append(original['initial_positions_xyz']);bases.append(original['bs_xyz'])
            arrays={'layouts':np.asarray(layouts,dtype=np.float64),'users':np.asarray(users,dtype=np.float64),
                    'initial':np.asarray(initial,dtype=np.float64),'bs':np.asarray(bases,dtype=np.float64),
                    'offsets':np.asarray(boundaries,dtype=np.int64),'metadata':np.asarray(e.encoded(records).decode('ascii'))}
            e.npz_write(store,f'raw/bank/{split}/{offset//64:04d}.npz',arrays)
        finally:
            journal.close()
        # Only the in-flight shard is journaled; successful compact evidence replaces it.
        partial.unlink()
        store.progress('bank_'+split,completed_worlds=offset+len(records),total_worlds=count)


class Bank:
    def __init__(self, root, files, split, launch_sha, input_sha):
        if split not in ('train','fresh'):
            raise ValueError('explicit bank identity')
        self.root,self.files,self.split,self.launch_sha,self.input_sha=root,files,split,launch_sha,input_sha
        self.cache=OrderedDict()

    def load(self, world):
        import numpy as np
        start,count=(c.TRAIN_START,c.TRAIN_COUNT) if self.split=='train' else (c.FRESH_START,c.FRESH_COUNT)
        if not start<=world<start+count:
            raise ValueError('bank split leakage/address refusal')
        shard=(world-start)//64;relative=f'raw/bank/{self.split}/{shard:04d}.npz'
        if shard not in self.cache:
            if relative not in self.files or e.sha(e.relative_path(self.root,relative))!=self.files[relative]['sha256']:
                raise ValueError('unbound or modified bank shard')
            with np.load(e.relative_path(self.root,relative),allow_pickle=False) as z:
                arrays={k:z[k] for k in z.files}
            arrays['records']=json.loads(str(arrays.pop('metadata')))
            self.cache[shard]=arrays
            if len(self.cache)>4:
                self.cache.popitem(last=False)
        self.cache.move_to_end(shard)
        a=self.cache[shard];i=(world-start)%64
        r={**a['records'][i]};r['identity']={**r['identity'],'initial_positions_xyz':a['initial'][i].tolist(),
                                           'user_positions_xy':a['users'][i].tolist(),'bs_xyz':a['bs'][i].tolist()}
        r['layouts_xyz']=a['layouts'][a['offsets'][i]:a['offsets'][i+1]].tolist()
        if r['identity']['world']!=world or r['source_sha']!=self.launch_sha or r['input_sha256']!=self.input_sha:
            raise ValueError('bank world/source/input identity mismatch')
        return r


class TrainingBank:
    """One train-only numeric view; no outcome dictionaries or expanded relations."""
    def __init__(self, original):
        import numpy as np
        if original.split != 'train':
            raise ValueError('training cache may contain only the declared train bank')
        self.layouts = np.empty((c.TRAIN_COUNT,221,6,3),dtype=np.float64)
        self.users = np.empty((c.TRAIN_COUNT,50,2),dtype=np.float64)
        self.bases = np.empty((c.TRAIN_COUNT,3),dtype=np.float64)
        self.J = np.empty((c.TRAIN_COUNT,221),dtype=np.float64)
        self.kind = np.empty((c.TRAIN_COUNT,221),dtype=np.uint8)
        self.k = np.empty((c.TRAIN_COUNT,221),dtype=np.uint8)
        self.counts = np.empty(c.TRAIN_COUNT,dtype=np.uint16)
        for i in range(c.TRAIN_COUNT):
            r = original.load(c.TRAIN_START+i)
            f = features(r); m = c.validate_features(f)
            self.counts[i] = m
            self.layouts[i,:m] = f['layouts_xyz']
            self.users[i] = f['users_xy']; self.bases[i] = f['bs_xyz']
            self.J[i,:m] = rewards(r)
            self.kind[i,:m] = [c.KINDS.index(v) for v in f['kinds']]
            self.k[i,:m] = f['ks']
        for value in vars(self).values():
            value.flags.writeable = False
        original.cache.clear()

    def load(self, world):
        i = world-c.TRAIN_START
        if not 0 <= i < c.TRAIN_COUNT:
            raise ValueError('train-only numeric cache refuses fresh world')
        m = int(self.counts[i])
        return {'identity':{'world':world}, 'J':self.J[i,:m],
                'features':{'users_xy':self.users[i], 'bs_xyz':self.bases[i],
                            'layouts_xyz':self.layouts[i,:m],
                            'kinds':[c.KINDS[int(v)] for v in self.kind[i,:m]],
                            'ks':[int(v) for v in self.k[i,:m]]}}
