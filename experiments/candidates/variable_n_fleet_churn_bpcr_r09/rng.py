"""Counter/HMAC registry with no master sampler and no implicit entropy."""
from __future__ import annotations

import hashlib,hmac,struct
import math
import numpy as np
from dataclasses import dataclass
from datetime import datetime

from .contracts import CARD_REVISION
from .empirical_contract import DOMAIN_LABELS,REPLICATE_ROLES
from .lease import ActivityPermit,LeaseError

class RNGContractError(RuntimeError):pass

def _field(value:str|int)->bytes:
    raw=str(value).encode("ascii");return len(raw).to_bytes(4,"big")+raw

@dataclass(frozen=True)
class Coordinate:
    replicate_role:str;domain:str;purpose:str;roster_size:int;failed_zone:int;update_or_panel_row:int;episode_row:int;physical_time:int;draw:int
    def encode(self)->bytes:
        if self.replicate_role not in REPLICATE_ROLES or self.domain not in DOMAIN_LABELS:raise RNGContractError("unregistered replicate/domain")
        if self.roster_size not in (3,5,7) or self.failed_zone not in (1,2) or min(self.update_or_panel_row,self.episode_row,self.draw)<0 or self.physical_time not in range(-120,101,20):raise RNGContractError("coordinate field outside registry")
        return b"".join(_field(x) for x in (CARD_REVISION,self.replicate_role,self.domain,self.purpose,self.roster_size,self.failed_zone,self.update_or_panel_row,self.episode_row,self.physical_time,self.draw))

def address(**fields:object)->Coordinate:return Coordinate(**fields)  # type: ignore[arg-type]

@dataclass(frozen=True,repr=False)
class EmpiricalRNG:
    _master:bytes;_permit:ActivityPermit
    @classmethod
    def from_external_master(cls,master:bytes,permit:ActivityPermit,*,now:datetime)->"EmpiricalRNG":
        permit.require_active(now=now)
        if len(master)!=32:raise RNGContractError("external master must be exactly 256 bits")
        return cls(bytes(master),permit)
    @property
    def master_digest(self)->str:return hashlib.sha256(self._master).hexdigest()
    def word(self,coordinate:Coordinate,*,now:datetime)->int:
        self._permit.require_active(now=now)
        return struct.unpack(">Q",hmac.new(self._master,coordinate.encode(),hashlib.sha256).digest()[:8])[0]
    def normal_array(self,shape:tuple[int,...],coordinate_builder:object,*,now:datetime)->np.ndarray:
        count=math.prod(shape);out=[];scale=float(1<<64)
        for pair in range((count+1)//2):
            a=coordinate_builder(2*pair);b=coordinate_builder(2*pair+1)  # type: ignore[operator]
            u1=(self.word(a,now=now)+0.5)/scale;u2=(self.word(b,now=now)+0.5)/scale;radius=math.sqrt(-2.0*math.log(u1));angle=2.0*math.pi*u2;out.extend((radius*math.cos(angle),radius*math.sin(angle)))
        return np.asarray(out[:count],dtype=np.float64).reshape(shape)
    def require_frontier_binding(self,bindings:object)->None:
        if getattr(bindings,"master_digest",None)!=self.master_digest or getattr(bindings,"coordinate_digest",None)!=self._permit.coordinate_digest or getattr(bindings,"source_manifest_sha256",None)!=self._permit.source_manifest_sha256:raise RNGContractError("HMAC master/coordinate/source differs from frontier receipt")

def domain_registry()->dict[str,object]:
    return {"schema":"VNFC_BPCR_R09_HMAC_DOMAIN_REGISTRY_V1","derivation":"HMAC-SHA256","prefix":CARD_REVISION,"roles":list(REPLICATE_ROLES),"domains":list(DOMAIN_LABELS),"unique":len(DOMAIN_LABELS)==len(set(DOMAIN_LABELS)),"master":None,"sampled_values":[]}
