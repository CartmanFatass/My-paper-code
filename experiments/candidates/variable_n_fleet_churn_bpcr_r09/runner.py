"""Lease/CM-gated empirical adapter over the interactive ABI-1 C++ host."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Sequence
import base64,ctypes,hashlib,os,secrets

from .empirical_contract import LEARNED_ARMS,REPLICATE_ROLES
from .lease import ActivityPermit,validate_root_lease
from .native_backend import NativeInteractiveBatch
from .production import require_native_production
from .rng import EmpiricalRNG
from .source_manifest import validate_manifest
from .frontier import AtomicFrontier,FrontierBindings,ValidatedCheckpointBarrier,validate_checkpoint_barrier_preidentity
from .empirical_training import ConcreteTrainSlotService
from .source_manifest import ACCEPTED_SHARED_SOURCE_SHA256
from .native_backend import native_artifact_identity
from .lifecycle import write_once

class RunnerError(PermissionError):pass
_AUTHORITY_SEAL=object()

@dataclass(frozen=True,repr=False)
class ActivityAuthority:
    permit:ActivityPermit;cm_acceptance_sha256:str;_seal:object|None=None

def _validate_cm_acceptance(path:Path,permit:ActivityPermit)->str:
    import hashlib
    try:raw=Path(path).read_bytes();value=json.loads(raw.decode("ascii"))
    except (OSError,UnicodeError,json.JSONDecodeError) as error:raise RunnerError("future external CM acceptance is absent") from error
    exact={"schema":"VNFC_BPCR_R09_CM_PREACTIVITY_ACCEPTANCE_V1","issuer":"CM_variable_n_fleet_churn_b4","stage":"VNFC-BPCR-R09-FULL-EMPIRICAL-PANEL","technically_accepted":True,"activity_observed":False,"source_manifest_sha256":permit.source_manifest_sha256,"coordinate_digest":permit.coordinate_digest}
    if any(value.get(k)!=v for k,v in exact.items()):raise RunnerError("external CM acceptance binding differs")
    return hashlib.sha256(raw).hexdigest()

def prepare_activity_authority(lease_path:Path,cm_acceptance_path:Path,*,now:datetime)->ActivityAuthority:
    validate_manifest()  # source/shared/native mismatch must fail before lease/master/guard
    permit=validate_root_lease(lease_path,now=now);acceptance_digest=_validate_cm_acceptance(cm_acceptance_path,permit);require_native_production(batch_width=32);return ActivityAuthority(permit,acceptance_digest,_AUTHORITY_SEAL)

def _prepare_activity_authority_before_native(lease_path:Path,*,now:datetime)->ActivityAuthority:
    validate_manifest()
    permit=validate_root_lease(lease_path,now=now)
    acceptance_digest=_validate_cm_acceptance(Path(permit.paths["preactivity_acceptance_path"]),permit)
    return ActivityAuthority(permit,acceptance_digest,_AUTHORITY_SEAL)

def open_external_rng(authority:ActivityAuthority,master:bytes,*,now:datetime)->EmpiricalRNG:
    if authority._seal is not _AUTHORITY_SEAL:raise RunnerError("validated external authority is required")
    return EmpiricalRNG.from_external_master(master,authority.permit,now=now)

def execute_training(authority:ActivityAuthority,rng:EmpiricalRNG,frontier:AtomicFrontier,*,now:datetime)->tuple[object,...]:
    if authority._seal is not _AUTHORITY_SEAL:raise RunnerError("validated external authority is required")
    if authority.permit.phase!="TRAIN":raise RunnerError("TRAIN Root lease required")
    service=ConcreteTrainSlotService(frontier);return tuple(service.train_slot(authority,rng,role,arm,now=now) for role in REPLICATE_ROLES for arm in LEARNED_ARMS)

def require_global_checkpoint_barrier(path:Path,authority:ActivityAuthority)->ValidatedCheckpointBarrier:
    if authority._seal is not _AUTHORITY_SEAL:raise RunnerError("validated external authority is required")
    expected=Path(authority.permit.paths["checkpoint_acceptance_path"]).resolve()
    if Path(path).resolve()!=expected:raise RunnerError("checkpoint barrier path differs from Root lease")
    return validate_checkpoint_barrier_preidentity(expected,Path(authority.permit.result_root),authority.permit.source_manifest_sha256,authority.permit.coordinate_digest)

def execute_evaluation(authority:ActivityAuthority,rng:EmpiricalRNG,frontier:AtomicFrontier,checkpoint_barrier:ValidatedCheckpointBarrier,*,now:datetime)->Path:
    if authority._seal is not _AUTHORITY_SEAL or authority.permit.phase!="EVALUATE":raise RunnerError("EVALUATE Root lease required")
    receipts=checkpoint_barrier.validate_binding(Path(authority.permit.result_root),frontier.bindings)
    from .services import ConcretePanelService
    return ConcretePanelService(frontier).execute(authority,rng,checkpoint_barrier,now=now)

class _Blob(ctypes.Structure):_fields_=[("size",ctypes.c_ulong),("data",ctypes.POINTER(ctypes.c_ubyte))]
def _dpapi(value:bytes,entropy:bytes,protect:bool)->bytes:
    if os.name!="nt":raise RunnerError("Windows DPAPI is required with no plaintext fallback")
    def blob(raw:bytes):buffer=ctypes.create_string_buffer(raw);return _Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte))),buffer
    source,sb=blob(value);extra,eb=blob(entropy);out=_Blob();function=ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData;ok=function(ctypes.byref(source),None,ctypes.byref(extra),None,None,1,ctypes.byref(out));_=sb,eb
    if not ok:raise RunnerError("DPAPI master operation failed")
    result=ctypes.string_at(out.data,out.size);ctypes.windll.kernel32.LocalFree(out.data);return result

def open_or_create_run_rng(authority:ActivityAuthority,*,now:datetime)->EmpiricalRNG:
    if authority._seal is not _AUTHORITY_SEAL:raise RunnerError("validated external authority is required")
    path=Path(authority.permit.paths["run_identity_path"]);context=(authority.permit.coordinate_digest+authority.permit.origin_lease_id).encode("ascii")
    if path.exists():
        value=json.loads(path.read_text("ascii"));master=_dpapi(base64.b64decode(value["sealed_master"]),context,False)
        if hashlib.sha256(master).hexdigest()!=value["master_digest"]:raise RunnerError("sealed master digest differs")
        if value["coordinate_digest"]!=authority.permit.coordinate_digest or value["origin_lease_id"]!=authority.permit.origin_lease_id:raise RunnerError("run identity resume binding differs")
    else:
        if authority.permit.replacement_of is not None:raise RunnerError("replacement lease cannot sample a new master")
        master=secrets.token_bytes(32);payload={"schema":"VNFC_BPCR_R09_BLINDED_RUN_IDENTITY_V1","coordinate_digest":authority.permit.coordinate_digest,"origin_lease_id":authority.permit.origin_lease_id,"master_digest":hashlib.sha256(master).hexdigest(),"sealed_master":base64.b64encode(_dpapi(master,context,True)).decode("ascii"),"partial_inspection_permitted":False};write_once(path,json.dumps(payload,sort_keys=True,separators=(",",":")).encode("ascii"))
    if authority.permit.preserved_master_digest is not None and hashlib.sha256(master).hexdigest()!=authority.permit.preserved_master_digest:raise RunnerError("replacement lease master binding differs")
    return open_external_rng(authority,master,now=now)

def concrete_phase_main(lease_path:Path,phase:str,*,now:datetime)->object:
    authority=_prepare_activity_authority_before_native(lease_path,now=now)
    if authority.permit.phase!=phase:raise RunnerError("CLI phase differs from Root lease")
    checkpoint_barrier=None
    if phase=="EVALUATE":
        checkpoint_barrier=require_global_checkpoint_barrier(Path(authority.permit.paths["checkpoint_acceptance_path"]),authority)
    require_native_production(batch_width=32)
    rng=open_or_create_run_rng(authority,now=now);native=native_artifact_identity();bindings=FrontierBindings(authority.permit.source_manifest_sha256,authority.permit.coordinate_digest,rng.master_digest,native["artifact_sha256"],native["native_source_sha256"],ACCEPTED_SHARED_SOURCE_SHA256);frontier_root=Path(authority.permit.paths["frontier_root"]);frontier=AtomicFrontier.resume(frontier_root,bindings,authority.permit,now=now) if frontier_root.exists() else AtomicFrontier.create(frontier_root,bindings,authority.permit,now=now)
    if phase=="TRAIN":return execute_training(authority,rng,frontier,now=now)
    assert checkpoint_barrier is not None
    return execute_evaluation(authority,rng,frontier,checkpoint_barrier,now=now)

def run_interactive_conformance(fixtures:Sequence[object])->tuple[dict[str,object],...]:
    """Construction fixtures only; this is not an empirical activity path."""
    materialized=tuple(fixtures)
    if len(materialized) not in (8,32):raise ValueError("runner conformance is frozen at B=8 or B=32")
    require_native_production(batch_width=len(materialized));batch=NativeInteractiveBatch(materialized)
    try:
        observations=tuple(row["next_observation"] for row in batch.initial)
        for _ in range(6):
            commands=tuple(fixture.post_commands[int(observation["epoch"])] for fixture,observation in zip(materialized,observations));rows=batch.step(commands);observations=tuple(row["next_observation"] for row in rows)
        if not all(row["terminal"] and row["integrated_ticks"]==240 for row in rows):raise RunnerError("interactive construction conformance failed")
        return rows
    finally:batch.close()
