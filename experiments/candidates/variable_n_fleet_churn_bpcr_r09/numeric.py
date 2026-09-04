"""Frozen counter/normal and canonical Haar-Stiefel QR construction helpers."""

from __future__ import annotations

import hashlib
import math
from typing import Iterable

import numpy as np


def counter_words(address: bytes, lanes: int) -> tuple[int, ...]:
    if lanes <= 0:
        raise ValueError("lane count must be positive")
    words=[]
    for lane in range(lanes):
        digest=hashlib.sha256(b"VNFC-BPCR-R09-COUNTER-v1\0"+len(address).to_bytes(4,"big")+address+lane.to_bytes(8,"big")).digest()
        words.append(int.from_bytes(digest[:8],"big"))
    return tuple(words)


def counter_normals(address: bytes, count: int) -> np.ndarray:
    """Frozen Box-Muller transform; construction helper, never an identity binder."""
    if count < 0:
        raise ValueError("normal count cannot be negative")
    words=counter_words(address,2*((count+1)//2));out=[]
    scale=float(1<<64)
    for i in range(0,len(words),2):
        u1=(words[i]+0.5)/scale;u2=(words[i+1]+0.5)/scale
        radius=math.sqrt(-2.0*math.log(u1));angle=2.0*math.pi*u2
        out.extend((radius*math.cos(angle),radius*math.sin(angle)))
    return np.asarray(out[:count],dtype=np.float64)


def canonical_stiefel(matrix: np.ndarray, logical_shape: tuple[int,int]) -> np.ndarray:
    """Apply the frozen orientation and sign-fixed Householder/QR convention."""
    out_dim,in_dim=logical_shape;a=np.asarray(matrix,dtype=np.float64)
    expected=(in_dim,out_dim) if out_dim<=in_dim else (out_dim,in_dim)
    if a.shape!=expected or not np.isfinite(a).all():raise ValueError("QR source shape differs")
    work=np.array(a,copy=True);m,n=work.shape;reflectors=[];diagonal=[]
    for column in range(n):
        x=work[column:,column].copy()
        norm=math.sqrt(math.fsum(float(value)*float(value) for value in x))
        if norm==0.0:
            reflectors.append((column,np.zeros_like(x),0.0));diagonal.append(0.0);continue
        alpha=-math.copysign(norm,float(x[0]));v=x;v[0]-=alpha
        vv=math.fsum(float(value)*float(value) for value in v);beta=2.0/vv
        for target in range(column,n):
            dot=math.fsum(float(v[i])*float(work[column+i,target]) for i in range(len(v)))
            work[column:,target]-=beta*v*dot
        work[column,column]=alpha;work[column+1:,column]=0.0
        reflectors.append((column,v,beta));diagonal.append(alpha)
    q=np.zeros((m,n),dtype=np.float64)
    for basis in range(n):
        y=np.zeros(m,dtype=np.float64);y[basis]=1.0
        for column,v,beta in reversed(reflectors):
            if beta==0.0:continue
            dot=math.fsum(float(v[i])*float(y[column+i]) for i in range(len(v)))
            y[column:]-=beta*v*dot
        q[:,basis]=y
    for column,diag in enumerate(diagonal):
        sign=1.0
        if diag<0:sign=-1.0
        elif diag==0:
            nz=np.flatnonzero(q[:,column]);sign=1.0 if len(nz)==0 or q[nz[0],column]>=0 else -1.0
        q[:,column]*=sign
    result=q.T if out_dim<=in_dim else q
    if result.shape!=logical_shape:raise AssertionError("canonical Stiefel orientation differs")
    return result
