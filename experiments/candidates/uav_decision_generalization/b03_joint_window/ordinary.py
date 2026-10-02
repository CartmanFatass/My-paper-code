"""Declared lawful deadline ray chain and sticky-target programmes."""
import itertools
import numpy as np


def steer(positions,targets):
    delta=np.asarray(targets,dtype=np.float64)-np.asarray(positions,dtype=np.float64)
    return delta/np.maximum(30.,np.linalg.norm(delta,axis=-1))[:,None]


def ray_slots(users,clusters):
    bs=np.array([2500.,2500.]);slots=[]
    for cluster in clusters:
        mean=np.asarray(users,dtype=np.float64)[10+10*int(cluster):20+10*int(cluster)].mean(axis=0)
        for factor in (1/3,2/3):slots.append(np.r_[bs+factor*(mean-bs),100.])
    return np.asarray(slots)


class RayChain:
    def __init__(self,positions,users,schedule):
        self.schedule=np.asarray(schedule);self.users=np.asarray(users);self.slots=ray_slots(users,schedule[:3]);self.reassigned=False
        positions=np.asarray(positions,dtype=np.float64)
        distances=np.linalg.norm(positions[:,None,:]-self.slots[None,:,:],axis=-1);arrivals=np.ceil(distances/30).astype(np.int64)
        def key(p):
            times=arrivals[np.asarray(p),np.arange(6)];pairs=np.max(times.reshape(3,2),axis=1)
            return (*np.maximum(0,pairs-np.array([105,230,355])).tolist(),int(pairs.max()),int(times.sum()),tuple(p))
        self.assignment=min(itertools.permutations(range(6)),key=key);self.targets=np.empty((6,3),dtype=np.float64)
        self.targets[np.asarray(self.assignment)]=self.slots
        self.assignment_comparisons=720;self.slot_distances=36;self.reassignment=None
    def actions(self,tick,positions,held_positions):
        if tick==130:
            ids=self.assignment[:2];slots=ray_slots(self.users,self.schedule[3:4]);held=np.asarray(held_positions,dtype=np.float64)
            distances=np.linalg.norm(held[np.asarray(ids),None,:]-slots[None,:,:],axis=-1)
            def key(p):
                ds=np.array([distances[ids.index(p[j]),j] for j in range(2)])
                return (int(np.ceil(ds/30).max()),float(ds.sum()),tuple(p))
            self.reassignment=min(itertools.permutations(ids),key=key)
            self.targets[np.asarray(self.reassignment)]=slots;self.reassigned=True
            self.assignment_comparisons+=2;self.slot_distances+=4
        return steer(positions,self.targets)


class Sticky:
    def __init__(self,world):
        self.rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(world),4])));self.replacements=0;self.draws=0
        self.targets=np.asarray([self._target() for _ in range(6)])
    def _target(self):
        self.draws+=3
        return np.array([self.rng.uniform(0,5000),self.rng.uniform(0,5000),self.rng.uniform(50,150)])
    def actions(self,tick,positions,held_positions):
        if tick and tick%10==0:
            for agent in range(6):
                self.draws+=1
                if self.rng.random()>=.9:self.targets[agent]=self._target();self.replacements+=1
        return steer(positions,self.targets)
