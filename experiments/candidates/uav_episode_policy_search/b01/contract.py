"""Frozen B01 identities. Smaller Protocol values are only explicit synthetic fixtures."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.contract import source_identities as inherited_sources, array_digest

OBJECT = 'UAV-EPISODE-POLICY-SEARCH-B01'
SEED = 40160000
FAMILIES = ('CAL', 'CONT')
REFERENCES = ('P0_A', 'Bstar0_A', 'Hdirect_A', 'G_A', 'C_A', 'P0_ZERO', 'Bstar0_ZERO', 'Hdirect_ZERO')
LEARNERS = ('CAL0', 'CONT0', 'CAL1', 'CONT1')
PROGRAMS = (*REFERENCES, *LEARNERS)
NEURAL = ('P0', 'Bstar0', 'Hdirect')
CONTRASTS = tuple((learner, ref) for learner in LEARNERS for ref in REFERENCES) + (('CONT0', 'CAL0'), ('CONT1', 'CAL1')) + tuple((p+'_ZERO', p+'_A') for p in NEURAL)
assert len(CONTRASTS) == 37

@dataclass(frozen=True)
class Protocol:
    blocks: int = 2
    iterations: int = 16
    directions: int = 16
    training_bases: tuple = (40161000, 40162000)
    training_motion_roots: tuple = (40164100, 40164101)
    perturbation_root: int = 40165000
    worlds: tuple = tuple(range(40163000, 40163032))
    evaluation_motion_roots: tuple = (40166000, 40166001)
    bootstrap_seed: int = 40167000
    constructor_seed: int = 40168000
    bootstrap_resamples: int = 20000
    horizon: int = 256
    period: int = 4
    n_agents: int = 5

    def validate(self):
        if (self.blocks != 2 or self.iterations <= 0 or self.directions <= 0 or self.period != 4
                or self.n_agents != 5 or self.horizon <= 0 or self.horizon % 4 or not self.worlds
                or len(self.training_bases) != 2 or len(self.training_motion_roots) != 2
                or len(self.evaluation_motion_roots) != 2 or self.bootstrap_resamples <= 0):
            raise ValueError('invalid fixed episode domains')
        train = [self.world(b,i,k,j) for b in range(2) for i in range(self.iterations)
                 for k in range(self.directions) for j in range(2)]
        roots = (*self.training_motion_roots, self.perturbation_root, *self.evaluation_motion_roots,
                 self.bootstrap_seed, self.constructor_seed)
        if len(set((*train, *self.worlds))) != len(train)+len(self.worlds) or len(set(roots)) != len(roots):
            raise ValueError('overlapping worlds or random domains')
        if any(type(v) is not int or v < 0 for v in (*train,*self.worlds,*roots)):
            raise ValueError('invalid RNG addresses')
        return self

    def world(self,b,i,k,j):
        return self.training_bases[b]+2*self.directions*i+2*k+j

    def episode_order(self, index=0):
        return tuple((p,t) for p in PROGRAMS for t in ((None,) if p=='C_A' else (0,1)))

    def identities(self):
        for b in range(2):
            for i in range(self.iterations):
                for k in range(self.directions):
                    for f in FAMILIES:
                        for sign in (1,-1):
                            for j in range(2):
                                yield dict(kind='training',program=f+str(b),block=b,iteration=i,direction=k,
                                           family=f,sign=sign,world_index=j,world=self.world(b,i,k,j),tape=None,
                                           motion_root=self.training_motion_roots[b])
        for w in self.worlds:
            for p,t in self.episode_order():
                yield dict(kind='evaluation',program=p,block=None,iteration=None,direction=None,
                           family=p[:-1] if p in LEARNERS else None,sign=None,world_index=None,world=w,tape=t,
                           motion_root=None if p=='C_A' else self.evaluation_motion_roots[t])

    def expected(self):
        train=2*self.iterations*self.directions*2*2*2
        final=len(self.worlds)*23
        clocks=self.horizon//4
        return dict(fits=4,training_episodes=train,evaluation_episodes=final,complete_episodes=train+final,
                    native_steps=(train+final)*self.horizon,native_uav_ticks=(train+final)*self.horizon*5,
                    explicit_resets=train+final,constructor_resets=1,mask_installs=(train+final)*clocks,
                    motion_requests=(train+final)*clocks*5,motion_draws=(train+final-len(self.worlds))*clocks*5,
                    head_requests=(train+len(self.worlds)*8)*clocks*5,
                    zero_head_requests=2*self.directions*8*clocks*5,
                    directions=4*self.iterations*self.directions,
                    normal_coordinates=2*self.iterations*self.directions*(28+3484),updates=4*self.iterations,
                    bootstrap_integers=self.bootstrap_resamples*len(self.worlds))

    def to_dict(self): return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls,d):
        d=dict(d)
        for key in ('training_bases','training_motion_roots','worlds','evaluation_motion_roots'): d[key]=tuple(d[key])
        return cls(**d).validate()

FROZEN=Protocol().validate()

def dimension(family):
    if family not in FAMILIES: raise ValueError('unknown head')
    return 28 if family=='CAL' else 3484

def episode_id(identity):
    if identity['kind']=='training':
        return 'training_%s_i%d_k%d_s%d_j%d_w%d'%(identity['program'],identity['iteration'],identity['direction'],identity['sign'],identity['world_index'],identity['world'])
    return 'evaluation_%s_w%d_t%s'%(identity['program'],identity['world'],identity['tape'])

def source_identities(repo):
    result=inherited_sources(repo)
    for path in sorted((Path(repo)/'experiments/candidates/uav_episode_policy_search/b01').glob('*.py')):
        result[str(path.relative_to(repo))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result

INHERITED_COST = dict(
    P0=dict(fits=1,total_steps=114688,labels=81920,optimizer_updates=8000,presentations=4096000,
            worker_reader_cpu_seconds=107.543822),
    Bstar0=dict(calibration_episodes=256,calibration_steps=65536,final_worlds=32,
                lineage_two_calibrations_cpu_seconds=139.828009,attributable_single_calibration_cpu_seconds=None),
    fleet_B02_B10_total=dict(fits=22,calibrations=2,steps=4055080),
    scope='P0 and Bstar0 are components of the fleet lineage total, not additions. Earlier B01 and actual-S2 parent attempts '
          'and failures remain additional; Hdirect/G/ZERO acquisition and ongoing queries remain charged. '
          'No attributable half of the two-calibration CPU bill is inferred.')


def validate_identity(identity,protocol):
    kind=identity.get('kind');name=identity.get('program')
    if kind=='training':
        b,i,k,j=(identity.get(x) for x in ('block','iteration','direction','world_index'))
        f=identity.get('family')
        if (type(b) is not int or not 0<=b<2 or type(i) is not int or not 0<=i<protocol.iterations
                or type(k) is not int or not 0<=k<protocol.directions or type(j) is not int or not 0<=j<2
                or f not in FAMILIES or name!=f+str(b) or identity.get('sign') not in (1,-1)
                or identity.get('tape') is not None or identity.get('world')!=protocol.world(b,i,k,j)
                or identity.get('motion_root')!=protocol.training_motion_roots[b]):
            raise ValueError('training episode address outside fixed domains')
    elif kind=='evaluation':
        if (name not in PROGRAMS or identity.get('world') not in protocol.worlds
                or any(identity.get(key) is not None for key in ('block','iteration','direction','sign','world_index'))
                or identity.get('family')!=(name[:-1] if name in LEARNERS else None)
                or identity.get('tape') not in ((None,) if name=='C_A' else (0,1))):
            raise ValueError('evaluation episode outside fixed domains')
        root=None if name=='C_A' else protocol.evaluation_motion_roots[identity['tape']]
        if identity.get('motion_root')!=root: raise ValueError('evaluation action domain changed')
    else: raise ValueError('undeclared episode kind')
