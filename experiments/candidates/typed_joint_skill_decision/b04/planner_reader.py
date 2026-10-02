"""Independent original control/plateau replay on paid ordered query-state responses."""
from __future__ import annotations
import itertools
from . import evidence as e


def assignment(initial,targets,bill):
    import numpy as np
    bill.charge('matching_calls')
    initial,targets=np.asarray(initial,dtype=np.float64),np.asarray(targets,dtype=np.float64)
    distance=np.sqrt(np.sum((initial[:,None,:]-targets[None,:,:])**2,axis=-1))
    best=None;perm=None
    for p in itertools.permutations(range(6)):
        ds=distance[np.arange(6),p];key=(float(ds.max()),float(ds.sum()))
        if best is None or key<best:
            best,perm=key,p
    bill.charge('matching_completed')
    return list(perm)


class CachedQueries:
    def __init__(self,rows,env):
        self.rows,self.env,self.used=iter(rows),env,0
    def evaluate(self,position,allow):
        import numpy as np
        row=next(self.rows)
        if e.encoded(row['positions_xyz'])!=e.encoded(position) or row['allow_a2a']!=allow:
            raise AssertionError('P exact ordered request mismatch')
        self.used+=1
        self.env.uav_positions=np.asarray(row['state']['positions_xyz'],dtype=float)
        self.env.connections=np.asarray(row['state']['connections'],dtype=bool)
        self.env.routing_paths={int(k):v for k,v in row['state']['routing_paths'].items()}
        self.env.uav_connections=np.asarray(row['state']['uav_connections'],dtype=bool)
        self.env.uav_bs_connections=np.asarray(row['state']['uav_bs_connections'],dtype=bool)
        return row['info']
    def finish(self):
        if next(self.rows,None) is not None:
            raise AssertionError('P cache contains unconsumed queries')


def replay_search(env,p,cache,world,allow,extra=None):
    import numpy as np
    report={}
    candidates=p.build_candidates(env,np.random.default_rng(world),allow_a2a=allow,report=report)
    if extra is not None:
        candidates.append({'index':len(candidates),'kind':'flat_result_incumbent','k':None,'positions_xyz':extra})
    used=0
    def potential():
        routed={int(i) for i in env.routing_paths}
        nodes=[env.ground_bs_positions[0]]+([env.uav_positions[i] for i in sorted(routed)] if allow else [])
        nodes=np.asarray(nodes,dtype=float)
        return sum(float(np.min(np.linalg.norm(nodes-env.uav_positions[i],axis=1))) for i in range(6) if i not in routed)
    def query(x):
        nonlocal used
        info=cache.evaluate(x,allow);used+=1
        return info,potential()
    for candidate in candidates:
        info,pot=query(candidate['positions_xyz']);candidate.update(J=info['contract_reward'],C=info['coverage_backhauled'],potential=pot)
    ranks=sorted(range(len(candidates)),key=lambda i:(-candidates[i]['J'],i))[:3]
    remaining=3000-used;shares=[remaining//len(ranks)+int(i<remaining%len(ranks)) for i in range(len(ranks))]
    best=None
    for rank,index in enumerate(ranks):
        candidate=candidates[index];position=np.array(candidate['positions_xyz'],dtype=float)
        reward,pot=candidate['J'],candidate['potential'];limit=used+shares[rank];stage=0
        while used<limit:
            moved=False;step=(100.,50.,25.)[stage]
            moves=((step,0.,0.),(-step,0.,0.),(0.,step,0.),(0.,-step,0.),(0.,0.,50.),(0.,0.,-50.))
            for uav in range(6):
                for move in moves:
                    if used>=limit:
                        break
                    trial=position.copy();trial[uav]+=move
                    trial[:,:2]=np.clip(trial[:,:2],0,5000);trial[:,2]=np.clip(trial[:,2],50,150)
                    if np.array_equal(trial,position):
                        continue
                    info,trial_pot=query(trial);value=float(info['contract_reward'])
                    if value>reward+1e-12 or (abs(value-reward)<=1e-12 and trial_pot<pot-1e-9):
                        position,reward,pot=trial,value,trial_pot;moved=True
                if used>=limit:
                    break
            if used>=limit:
                break
            if not moved:
                if stage==2:
                    break
                stage+=1
        if best is None or reward>best['J']+1e-12:
            best={'positions_xyz':position,'J':reward,'candidate':candidate,'rank':rank}
    best['evaluations']=used
    return best


def replay(env,p,query_path,decision,bill):
    import numpy as np
    cache=CachedQueries(e.read_trace(query_path),env)
    flat=replay_search(env,p,cache,decision['world'],False)
    relay=replay_search(env,p,cache,decision['world'],True,flat['positions_xyz'])
    chosen=relay['candidate']
    source='generator:'+chosen['kind']
    if chosen['kind']=='flat_result_incumbent':
        chosen=flat['candidate'];source='flat_result_incumbent<-flat generator:'+chosen['kind']
    if chosen.get('roles') is not None:
        roles=list(chosen['roles'])
    elif chosen['kind']=='kmeans_plain':
        k=int(chosen['k']);targets=list(chosen['relay_targets'])
        roles=[f'service:{i}' for i in range(k)]+[f'relay:{int(targets[r])}:{r//k}' for r in range(6-k)]
        source=source.replace('generator:kmeans_plain','generator:kmeans_plain(relay_targets)')
    else:
        raise AssertionError('P role rule mismatch')
    permutation=assignment(decision['initial_positions_xyz'],relay['positions_xyz'],bill)
    cache.evaluate(relay['positions_xyz'],True)
    relays={int(node) for path in env.routing_paths.values() for kind,node in path[1:-1] if kind=='uav'}
    connected=np.asarray(env.connections,dtype=bool).any(axis=1)
    routing_roles=['relay' if i in relays else 'service' if connected[i] else 'idle' for i in range(6)]
    cache.finish()
    menu=decision['P_menu']
    if (e.encoded(relay['positions_xyz'])!=e.encoded(decision['positions_xyz']) or permutation!=decision['target_permutation']
        or roles!=menu['roles'] or source!=menu['role_source'] or routing_roles!=menu['routing_roles_diagnostic']
        or [flat['evaluations'],relay['evaluations']]!=menu['static']['evaluations']):
        raise AssertionError('P independent complete output/control identity mismatch')
    return {'query_rows':cache.used,'complete_consumption':True,'new_physics_queries':0,
            'trust':'independent control replay of pinned construction and paid response/state cache, not independent physics'}
