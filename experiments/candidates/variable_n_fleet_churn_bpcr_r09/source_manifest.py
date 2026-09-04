"""Complete immutable source/dependency/native/shared preactivity inventory."""
from __future__ import annotations

import hashlib,json,platform,sys
from pathlib import Path
from typing import Final,Mapping

import numpy,torch

from .contracts import CARD_SHA256,NATIVE_ABI_VERSION,PUBLIC_LAW_SHA256,canonical_json_bytes

SHARED_SOURCE_PATH:Final[str]="envs/native/production_backend.py"
ACCEPTED_SHARED_SOURCE_SHA256:Final[str]="c378997ec45b599c19a34b7ce1c8cdecbd127f695aed7218a625dc8bebcf2e1b"
LIVE_SHARED_SOURCE_SHA256:Final[str]="c79a26e4a71678dcde16993a33a01cff735d90116d8ea70b6577232be39939ce"
MANIFEST_NAME:Final[str]="empirical_source_manifest.json"
MANIFEST_SHA256:Final[str]="89f5cd04753130288eb819ef56359e7a93e29ef9559fc65af8a7806e11164e3c"
TRANSITION_NAME:Final[str]="shared_source_alignment_transition.json"
TRANSITION_SCHEMA:Final[str]="VNFC_BPCR_R09_SHARED_SOURCE_ALIGNMENT_TRANSITION_V1"
TRANSITION_AUTHORITY:Final[str]="VALIDATION_ONLY_NO_ACTIVITY_OR_LEASE_AUTHORITY"
PRESERVED_COORDINATE_DIGEST:Final[str]="9a2a4affb03e4c2eb2ded763991fcbe9bfef18b6df19457b5ad67e2dce31e87b"
PRESERVED_MASTER_DIGEST:Final[str]="9e5927ca82fda74e557eb38cf4af3b0d149ac0fef0f0d89319796aed4c6a64a9"
PRESERVED_ORIGIN_LEASE_ID:Final[str]="VNFC-BPCR-R09-ROOT-TRAIN-20260821-01"
PRESERVED_RESULT_ROOT:Final[str]="C:\\Projects\\HMASD\\artifacts\\VNFC_BPCR_R09_FUTURE"
LOCAL_OVERRIDE_PATHS:Final[tuple[str,...]]=(
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/evaluation.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/source_manifest.py",
    "experiments/candidates/variable_n_fleet_churn_bpcr_r09/torch_models.py",
    "tests/experiments/candidates/variable_n_fleet_churn_bpcr_r09/test_empirical_preactivity.py",
)

class SourceManifestError(RuntimeError):pass

def _sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def _roots()->tuple[Path,Path,Path]:
    package=Path(__file__).resolve().parent;repo=package.parents[2];tests=repo/"tests/experiments/candidates/variable_n_fleet_churn_bpcr_r09";return repo,package,tests

def source_paths()->tuple[str,...]:
    repo,package,tests=_roots();paths=[]
    for root in (package,tests):
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.name!=MANIFEST_NAME and path.suffix in (".py",".cpp",".hpp"):
                paths.append(path.relative_to(repo).as_posix())
    paths.extend((SHARED_SOURCE_PATH,"docs/research/candidates/variable_n_fleet_churn/VNFC_UAV_BOUNDED_POST_CHURN_RECOVERY_SCIENCE_CARD.md","docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md","docs/research/candidates/variable_n_fleet_churn/VNFC_UAV_BOUNDED_POST_CHURN_RECOVERY_PUBLIC_PHYSICAL_LAW_BINDING.md"))
    return tuple(sorted(paths))

def build_manifest()->dict[str,object]:
    from .native_backend import native_artifact_identity
    repo,_,_=_roots();native=native_artifact_identity();files=[{"path":p,"sha256":_sha(repo/p)} for p in source_paths()]
    dependencies=[]
    for name,module in (("numpy",numpy),("torch",torch)):
        path=Path(module.__file__).resolve();dependencies.append({"name":name,"version":module.__version__,"module_path":str(path),"module_sha256":_sha(path)})
    return {"schema":"VNFC_BPCR_R09_EMPIRICAL_SOURCE_MANIFEST_V1","status":"FINAL","files":files,"dependencies":dependencies,"schemas":["VNFC_BPCR_R09_COORDINATE_PROPOSAL_V1","VNFC_BPCR_R09_ROOT_LEASE_V1","VNFC_BPCR_R09_BLINDED_FRONTIER_BINDINGS_V1","VNFC_BPCR_R09_COMPLETE_ATOMIC_MANIFEST_V1"],"runtime":{"python_executable":"C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","python_version":platform.python_version(),"byteorder":sys.byteorder,"cpu_only":True},"immutable":{"card_sha256":CARD_SHA256,"public_law_sha256":PUBLIC_LAW_SHA256,"shared_source_path":SHARED_SOURCE_PATH,"shared_source_sha256":ACCEPTED_SHARED_SOURCE_SHA256},"native":{"abi_version":NATIVE_ABI_VERSION,"build_key":native["build_key"],"source_sha256":native["native_source_sha256"],"artifact_sha256":native["artifact_sha256"],"artifact_size":native["artifact_size"],"abi_sizes":native["abi_sizes"],"compiler":native["toolchain"],"full_reset_step_cpp":native["full_reset_step_cpp"],"python_fallback":native["python_fallback"]}}

def manifest_bytes(value:Mapping[str,object])->bytes:return canonical_json_bytes(dict(value))+b"\n"

def manifest_digest(value:Mapping[str,object])->str:return hashlib.sha256(manifest_bytes(value)).hexdigest()

def _read_canonical_object(path:Path,label:str)->tuple[bytes,dict[str,object]]:
    try:raw=path.read_bytes();value=json.loads(raw.decode("ascii"))
    except (OSError,UnicodeError,json.JSONDecodeError) as error:raise SourceManifestError(f"{label} cannot be read") from error
    if not isinstance(value,dict) or raw!=manifest_bytes(value):raise SourceManifestError(f"{label} bytes are not canonical")
    return raw,value

def _transition_hashes(repo:Path,package:Path,manifest:dict[str,object],rows:dict[str,dict[str,object]])->dict[str,str]:
    _,transition=_read_canonical_object(package/TRANSITION_NAME,"shared-source alignment transition")
    if set(transition)!={"schema","status","authority","manifest","shared_source","candidate_local_overrides","resume_fence"} or transition.get("schema")!=TRANSITION_SCHEMA or transition.get("status")!="FINAL" or transition.get("authority")!=TRANSITION_AUTHORITY:raise SourceManifestError("shared-source alignment transition envelope differs")
    manifest_binding=transition.get("manifest")
    if not isinstance(manifest_binding,dict) or set(manifest_binding)!={"path","sha256"} or manifest_binding.get("path")!=f"experiments/candidates/variable_n_fleet_churn_bpcr_r09/{MANIFEST_NAME}" or manifest_binding.get("sha256")!=MANIFEST_SHA256:raise SourceManifestError("shared-source alignment transition manifest binding differs")
    shared=transition.get("shared_source")
    immutable=manifest.get("immutable")
    if not isinstance(shared,dict) or set(shared)!={"path","old_sha256","new_sha256"} or shared.get("path")!=SHARED_SOURCE_PATH or shared.get("old_sha256")!=ACCEPTED_SHARED_SOURCE_SHA256 or shared.get("new_sha256")!=LIVE_SHARED_SOURCE_SHA256:raise SourceManifestError("shared-source alignment transition shared binding differs")
    if not isinstance(immutable,dict) or immutable.get("shared_source_path")!=SHARED_SOURCE_PATH or immutable.get("shared_source_sha256")!=ACCEPTED_SHARED_SOURCE_SHA256 or rows.get(SHARED_SOURCE_PATH,{}).get("sha256")!=ACCEPTED_SHARED_SOURCE_SHA256:raise SourceManifestError("frozen shared-source provenance binding differs")
    resume_fence=transition.get("resume_fence")
    expected_fence={"coordinate_digest":PRESERVED_COORDINATE_DIGEST,"master_digest":PRESERVED_MASTER_DIGEST,"origin_lease_id":PRESERVED_ORIGIN_LEASE_ID,"result_root":PRESERVED_RESULT_ROOT,"frontier_shared_source_sha256":ACCEPTED_SHARED_SOURCE_SHA256,"scientific_values_exposed":False,"partial_inspection_permitted":False}
    if resume_fence!=expected_fence:raise SourceManifestError("shared-source alignment preserved resume fence differs")
    overrides=transition.get("candidate_local_overrides")
    if not isinstance(overrides,list) or tuple(row.get("path") if isinstance(row,dict) else None for row in overrides)!=LOCAL_OVERRIDE_PATHS:raise SourceManifestError("shared-source alignment local override inventory differs")
    live_hashes={SHARED_SOURCE_PATH:LIVE_SHARED_SOURCE_SHA256}
    for override in overrides:
        if not isinstance(override,dict) or set(override)!={"path","old_sha256","new_sha256"}:raise SourceManifestError("shared-source alignment local override row differs")
        path=override["path"];old=override["old_sha256"];new=override["new_sha256"]
        if not isinstance(path,str) or not isinstance(old,str) or not isinstance(new,str) or len(new)!=64 or any(ch not in "0123456789abcdef" for ch in new) or rows.get(path,{}).get("sha256")!=old or old==new:raise SourceManifestError("shared-source alignment local override binding differs")
        live_hashes[path]=new
    if set(live_hashes)!={SHARED_SOURCE_PATH,*LOCAL_OVERRIDE_PATHS}:raise SourceManifestError("shared-source alignment authorization scope differs")
    for path,expected in live_hashes.items():
        source=repo/path
        if not source.is_file() or _sha(source)!=expected:raise SourceManifestError(f"transition-authorized live source differs: {path}")
    return live_hashes

def validate_manifest(path:Path|None=None)->dict[str,object]:
    _,package,_=_roots();canonical=path is None;target=package/MANIFEST_NAME if canonical else Path(path)
    raw,value=_read_canonical_object(target,"empirical source manifest")
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:raise SourceManifestError("empirical source manifest provenance identity differs")
    repo,_,_=_roots();expected_paths=source_paths();rows=value.get("files")
    if not isinstance(rows,list) or any(not isinstance(row,dict) or set(row)!={"path","sha256"} for row in rows) or tuple(row["path"] for row in rows)!=expected_paths:raise SourceManifestError("empirical source path inventory changed")
    row_map={row["path"]:row for row in rows}
    live_hashes=_transition_hashes(repo,package,value,row_map) if canonical else {}
    for row in rows:
        source=repo/row["path"]
        expected=live_hashes.get(row["path"],row["sha256"])
        if not source.is_file() or _sha(source)!=expected:raise SourceManifestError(f"empirical source changed before native guard: {row.get('path')}")
    current=build_manifest()
    if set(value)!={"schema","status","files","dependencies","schemas","runtime","immutable","native"} or any(value.get(key)!=current.get(key) for key in ("schema","status","dependencies","schemas","runtime","immutable","native")):raise SourceManifestError("empirical dependency/native/card/public inventory changed")
    return {"path":str(target.resolve()),"sha256":MANIFEST_SHA256,"file_count":len(value["files"]),"status":"FINAL"}
