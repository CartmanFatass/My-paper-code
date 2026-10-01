"""Worker FP64 readout and ordered finite normalized update."""
import numpy as np
from .contract import dimension

LIMIT=np.log(2.)

def head(logits,hidden,theta,family):
    theta=np.asarray(theta)
    if theta.dtype!=np.float64 or theta.shape!=(dimension(family),) or not np.isfinite(theta).all():
        raise ValueError('finite FP64 head parameters required')
    h=np.asarray(hidden,dtype=np.float64)
    l=np.asarray(logits,dtype=np.float64)
    if h.shape!=(128,) or l.shape!=(27,) or not np.isfinite(h).all() or not np.isfinite(l).all():
        raise FloatingPointError('invalid paid P0 values')
    hbar=h/max(1.,float(np.linalg.norm(h)))
    residual=theta[1:28].copy()
    if family=='CONT': residual+=theta[28:].reshape(27,128)@hbar
    answer=l/np.exp(np.clip(theta[0],-LIMIT,LIMIT))+np.tanh(residual)
    if not np.isfinite(answer).all(): raise FloatingPointError('nonfinite head')
    return answer,hbar

def perturbation(protocol,b,f,i,k):
    return np.random.default_rng(np.random.SeedSequence([protocol.perturbation_root,b,f,i,k])).standard_normal(dimension(('CAL','CONT')[f]))

def update(center,deltas,fitness):
    if fitness.shape!=(len(deltas),2) or not np.isfinite(fitness).all():
        raise FloatingPointError('invalid complete signed fitness')
    diff=fitness[:,0]-fitness[:,1]
    d=diff/2.
    scale=max(float(np.sqrt(np.sum(d*d,dtype=np.float64)/len(deltas))),1e-8)
    acc=np.zeros_like(center,dtype=np.float64)
    for k in range(len(deltas)): acc+=diff[k]*deltas[k]
    result=center+.02/(len(deltas)*scale)*acc
    result[0]=np.clip(result[0],-LIMIT,LIMIT)
    if not np.isfinite(result).all(): raise FloatingPointError('nonfinite updated center')
    return result,dict(scale=scale,diff=diff,accumulator=acc)
