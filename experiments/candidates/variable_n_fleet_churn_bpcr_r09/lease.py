"""Future Root-lease validation; this module cannot issue a permit."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib,json
from pathlib import Path
from typing import Final,Mapping

from .contracts import CARD_SHA256,NATIVE_ABI_VERSION,PUBLIC_LAW_SHA256,SHARED_COMPONENT
from .empirical_contract import EMPIRICAL_STAGE,PANEL_COUNTS,coordinate_proposal_digest
from .source_manifest import validate_manifest

LEASE_SCHEMA:Final[str]="VNFC_BPCR_R09_ROOT_LEASE_V1"
_PERMIT_SEAL:Final[object]=object()
class LeaseError(PermissionError):pass

@dataclass(frozen=True,repr=False)
class ActivityPermit:
    lease_id:str;origin_lease_id:str;replacement_of:str|None;phase:str;source_manifest_sha256:str;coordinate_digest:str;preserved_master_digest:str|None;result_root:str;paths:dict[str,str];issued_at:str;expires_at:str;_seal:object|None=None
    def require_active(self,*,now:datetime)->None:
        if self._seal is not _PERMIT_SEAL:raise LeaseError("unvalidated permit")
        end=datetime.fromisoformat(self.expires_at.replace("Z","+00:00"))
        if now.tzinfo is None or now>=end:raise LeaseError("Root lease is expired")

def _replacement_resume_binding(lease:Mapping[str,object],paths:Mapping[str,Path])->tuple[str,str]:
    try:
        identity=json.loads(paths["run_identity_path"].read_text("ascii"));frontier=json.loads((paths["frontier_root"]/"bindings.json").read_text("ascii"))
    except (OSError,UnicodeError,json.JSONDecodeError) as error:raise LeaseError("replacement resume identity/frontier binding is absent") from error
    identity_keys={"schema","coordinate_digest","origin_lease_id","master_digest","sealed_master","partial_inspection_permitted"}
    frontier_keys={"schema","source_manifest_sha256","coordinate_digest","master_digest","native_artifact_sha256","native_source_sha256","shared_source_sha256","card_sha256","public_law_sha256","origin_lease_id","scientific_values_exposed","partial_inspection_permitted"}
    if set(identity)!=identity_keys or identity.get("schema")!="VNFC_BPCR_R09_BLINDED_RUN_IDENTITY_V1" or identity.get("partial_inspection_permitted") is not False:raise LeaseError("replacement RUN_IDENTITY schema differs")
    if set(frontier)!=frontier_keys or frontier.get("schema")!="VNFC_BPCR_R09_BLINDED_FRONTIER_BINDINGS_V1" or frontier.get("scientific_values_exposed") is not False or frontier.get("partial_inspection_permitted") is not False:raise LeaseError("replacement frontier binding schema differs")
    coordinate=identity.get("coordinate_digest");master=identity.get("master_digest");origin=identity.get("origin_lease_id")
    if not all(isinstance(value,str) and len(value)==64 for value in (coordinate,master)) or not isinstance(origin,str) or not origin:raise LeaseError("replacement stored coordinate/master/origin differs")
    if (frontier.get("coordinate_digest"),frontier.get("master_digest"),frontier.get("origin_lease_id"))!=(coordinate,master,origin):raise LeaseError("replacement RUN_IDENTITY/frontier binding differs")
    if lease.get("coordinate_proposal_digest")!=coordinate or lease.get("preserved_master_digest")!=master or lease.get("origin_lease_id")!=origin or lease.get("replacement_of")!=origin:raise LeaseError("replacement lease changes coordinate/master/origin lineage")
    return coordinate,master

def validate_root_lease(lease_path:Path,*,now:datetime)->ActivityPermit:
    manifest=validate_manifest()
    try:raw=Path(lease_path).read_bytes();lease=json.loads(raw.decode("ascii"))
    except (OSError,UnicodeError,json.JSONDecodeError) as error:raise LeaseError("external Root lease is absent") from error
    required={"schema","issuer","lease_id","origin_lease_id","activity_authorized","stage","phase","issued_at","expires_at","source_manifest_sha256","coordinate_proposal_digest","card_sha256","public_law_sha256","component","abi_version","native_binding","complete_panel_only","python_environment_loop","python_action_loop","python_fallback","replacement_of","preserve_coordinate_digest","preserve_master_digest","preserved_master_digest","paths","execution","resources","counts"}
    if set(lease)!=required:raise LeaseError("Root lease field inventory differs")
    exact={"schema":LEASE_SCHEMA,"issuer":"Operational Root","activity_authorized":True,"stage":EMPIRICAL_STAGE,"source_manifest_sha256":manifest["sha256"],"card_sha256":CARD_SHA256,"public_law_sha256":PUBLIC_LAW_SHA256,"component":SHARED_COMPONENT,"abi_version":NATIVE_ABI_VERSION,"complete_panel_only":True,"python_environment_loop":False,"python_action_loop":False,"python_fallback":False,"counts":PANEL_COUNTS,"resources":{"cpu_only":True,"gpu_count":0,"max_independent_workers":32,"cpu_core_hours_upper":1500,"ram_gib":64,"scratch_gib":60,"durable_artifacts_gib":30,"validity_hours":168}}
    for key,value in exact.items():
        if lease.get(key)!=value:raise LeaseError(f"Root lease binding differs: {key}")
    if lease["phase"] not in ("TRAIN","EVALUATE"):raise LeaseError("lease phase differs")
    native=lease.get("native_binding")
    manifest_value=json.loads(Path(manifest["path"]).read_text("ascii"));expected_native={key:manifest_value["native"][key] for key in ("abi_version","artifact_sha256","source_sha256","build_key")}
    if native!=expected_native:raise LeaseError("lease native binding differs")
    paths=lease.get("paths");path_fields={"result_root","frontier_root","train_terminal_path","evaluation_terminal_path","run_identity_path","preactivity_acceptance_path","checkpoint_acceptance_path","complete_manifest_path"}
    if not isinstance(paths,dict) or set(paths)!=path_fields:raise LeaseError("lease path inventory differs")
    repo=Path(__file__).resolve().parents[3];resolved={key:Path(value).resolve() for key,value in paths.items() if isinstance(value,str) and Path(value).is_absolute()}
    if set(resolved)!=path_fields:raise LeaseError("lease paths must be absolute")
    root=resolved["result_root"]
    try:root.relative_to(repo)
    except ValueError as error:raise LeaseError("lease result root escapes repository") from error
    if len(set(resolved.values()))!=len(resolved) or any(key!="result_root" and not path.is_relative_to(root) for key,path in resolved.items()):raise LeaseError("lease output paths escape/equal result root")
    module="experiments.candidates.variable_n_fleet_churn_bpcr_r09";expected_execution={"python_executable":"C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","module":module,"argv":["C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","-m",module,"--phase",lease["phase"],"--lease",str(Path(lease_path).resolve())]}
    if lease.get("execution")!=expected_execution:raise LeaseError("lease executable/argv differs")
    try:start=datetime.fromisoformat(str(lease["issued_at"]).replace("Z","+00:00"));end=datetime.fromisoformat(str(lease["expires_at"]).replace("Z","+00:00"))
    except ValueError as error:raise LeaseError("lease time is invalid") from error
    if now.tzinfo is None or not start<=now<end or (end-start).total_seconds()>168*3600:raise LeaseError("Root lease is inactive or exceeds validity cap")
    replacement=lease["replacement_of"]
    if replacement is None:
        coordinate=coordinate_proposal_digest(manifest["sha256"])
        if lease.get("coordinate_proposal_digest")!=coordinate or lease["origin_lease_id"]!=lease["lease_id"] or lease["preserved_master_digest"] is not None:raise LeaseError("initial lease origin/source-bound coordinate/master fields differ")
    else:
        if lease["preserve_coordinate_digest"] is not True or lease["preserve_master_digest"] is not True or lease["origin_lease_id"]==lease["lease_id"] or not isinstance(lease["preserved_master_digest"],str) or len(lease["preserved_master_digest"])!=64:raise LeaseError("replacement lease changes same-coordinate identity")
        coordinate,_=_replacement_resume_binding(lease,resolved)
    return ActivityPermit(str(lease["lease_id"]),str(lease["origin_lease_id"]),replacement,str(lease["phase"]),manifest["sha256"],coordinate,lease["preserved_master_digest"],str(root),{k:str(v) for k,v in resolved.items()},str(lease["issued_at"]),str(lease["expires_at"]),_PERMIT_SEAL)

def lease_file_digest(path:Path)->str:return hashlib.sha256(Path(path).read_bytes()).hexdigest()
