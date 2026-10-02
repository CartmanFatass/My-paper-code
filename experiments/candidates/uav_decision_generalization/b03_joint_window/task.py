"""Pure registry/features/window bookkeeping; no host or model query."""
import numpy as np


def world_registry(world):
    centers=np.array([[2500,2500],[500,500],[4500,500],[4500,4500],[500,4500]],dtype=np.float64)
    centers[1:]+=np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(world),1]))).uniform(-50,50,(4,2))
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(world),2])))
    users=[]
    for center in centers:
        for _ in range(10):
            u,v=rng.uniform(0,1,2);angle=2*np.pi*v
            users.append(np.rint(center+100*np.sqrt(u)*np.array([np.cos(angle),np.sin(angle)])))
    users=np.asarray(users,dtype='<i4')
    schedule=np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(world),3]))).permutation(4).astype(np.uint8)
    packet=np.frombuffer(users.tobytes(order='C')+schedule.tobytes(),dtype=np.uint8).copy()
    return users,schedule,packet


def decode_packet(packet):
    packet=np.asarray(packet)
    if packet.shape!=(404,) or packet.dtype!=np.uint8:raise ValueError('exact404-byte registry required')
    users=np.frombuffer(packet[:400].tobytes(),dtype='<i4').reshape(50,2).copy();schedule=packet[400:].copy()
    if sorted(schedule.tolist())!=[0,1,2,3]:raise ValueError('each far cluster exactly once')
    return users,schedule


def task_features(schedule,tick):
    if type(tick)!=int or not 0<=tick<=500:raise ValueError('primitive state time0..500 required')
    schedule=np.asarray(schedule,dtype=np.uint8)
    if schedule.shape!=(4,) or sorted(schedule.tolist())!=[0,1,2,3]:raise ValueError('fixed4-cluster permutation required')
    onehot=np.eye(4,dtype=np.float32)[schedule].reshape(16)
    active=np.zeros(4,dtype=np.float32);remaining=0.
    if tick<500:active[schedule[tick//125]]=1.;remaining=(125-tick%125)/125
    return np.concatenate([onehot,active,np.asarray([remaining],dtype=np.float32)])


def augmented_observations(original,users,schedule,tick):
    original=np.asarray(original,dtype=np.float32)
    if original.shape!=(6,90):raise ValueError('original six90-row contract required')
    block=np.concatenate([np.asarray(users,dtype=np.float32).reshape(100)/5000,task_features(schedule,tick)])
    return np.concatenate([original,np.broadcast_to(block,(6,121))],axis=1).astype(np.float32,copy=False)


def augmented_state(original,schedule,tick):
    original=np.asarray(original,dtype=np.float32)
    if original.shape!=(133,):raise ValueError('original133 count-state required')
    return np.concatenate([original,task_features(schedule,tick)]).astype(np.float32,copy=False)


class WindowLedger:
    def __init__(self,schedule):
        self.schedule=np.asarray(schedule,dtype=np.uint8).copy();task_features(self.schedule,0)
        self.tick=0;self.run=0;self.paid=np.zeros(4,dtype=bool)
    def advance(self,connections,routed):
        if self.tick>=500:raise ValueError('one transition per primitive action; mission exhausted')
        connections=np.asarray(connections)
        routed=np.asarray(routed,dtype=bool)
        if connections.shape!=(6,50) or connections.dtype!=np.bool_ or routed.shape!=(6,):raise ValueError('post-routing native mask dimensions')
        n=self.tick;j=n//125
        if n%125==0:self.run=0
        mask=(connections&routed[:,None]).any(axis=0);cluster=int(self.schedule[j]);q=int(mask[10+10*cluster:20+10*cluster].sum())
        self.run=self.run+1 if q>=8 else 0
        payment=float(self.run==20 and not self.paid[j])
        if payment:self.paid[j]=True
        self.tick+=1
        return {'window':j,'active_cluster':cluster,'active_count':q,'run_length':self.run,'paid':self.paid.copy(),
                'payment':payment,'external_scalar':payment/6,'routed_user_mask':mask,'associated_user_mask':connections.any(axis=0)}
