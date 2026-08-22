"""Blinded create-only resumable frontier and indivisible completion barrier."""
from __future__ import annotations

from dataclasses import asdict,dataclass
import hashlib,json
from pathlib import Path
from typing import Callable,Mapping,Sequence

from .contracts import CARD_SHA256,PUBLIC_LAW_SHA256,canonical_json_bytes
from .empirical_contract import LEARNED_ARMS,PANEL_COUNTS,REPLICATE_ROLES
from .lease import ActivityPermit
from .lifecycle import write_once

class FrontierError(RuntimeError):pass
COMPLETE_CATEGORIES=("checkpoints_optimizers","training_validation_roles_coordinate_map","conclusion_rollouts","public_traces_masks_commands","direct_diagnostics","cut_association","bcrh_certificates_64","replicate_matrix_efficacy","replicate_matrix_non_harm","replicate_matrix_training_gain","replicate_matrix_competence","replicate_matrix_mechanism","point_reductions","exact_inference","gates","branches","dependency_bytes")
CATEGORY_CARDINALITIES={"checkpoints_optimizers":128,"training_validation_roles_coordinate_map":139264,"conclusion_rollouts":4096,"public_traces_masks_commands":860160,"direct_diagnostics":18432,"cut_association":1024,"bcrh_certificates_64":1088,"replicate_matrix_efficacy":192,"replicate_matrix_non_harm":384,"replicate_matrix_training_gain":128,"replicate_matrix_competence":448,"replicate_matrix_mechanism":288,"point_reductions":90,"exact_inference":90,"gates":9,"branches":2,"dependency_bytes":40}

def freeze_preactivity_template(path:Path,bindings:Mapping[str,str],*,failure_hook:Callable[[str],None]|None=None)->str:
    required={"source_manifest_sha256","coordinate_digest","native_artifact_sha256","native_source_sha256","shared_source_sha256","card_sha256","public_law_sha256"}
    if set(bindings)!=required or any(len(value)!=64 for value in bindings.values()):raise FrontierError("preactivity binding template differs")
    payload={"schema":"VNFC_BPCR_R09_PREACTIVITY_FRONTIER_TEMPLATE_V1","materialized":False,"master_digest":None,"origin_lease_id":None,"replacement_lease_id":None,"bindings":dict(sorted(bindings.items())),"same_coordinate_resume":True,"scientific_values_exposed":False}
    return write_once(Path(path),canonical_json_bytes(payload),failure_hook=failure_hook)

def validate_preactivity_template(path:Path,bindings:Mapping[str,str])->None:
    value=_load(Path(path));expected={"schema":"VNFC_BPCR_R09_PREACTIVITY_FRONTIER_TEMPLATE_V1","materialized":False,"master_digest":None,"origin_lease_id":None,"replacement_lease_id":None,"bindings":dict(sorted(bindings.items())),"same_coordinate_resume":True,"scientific_values_exposed":False}
    if value!=expected:raise FrontierError("preactivity resume binding differs")

@dataclass(frozen=True)
class FrontierBindings:
    source_manifest_sha256:str;coordinate_digest:str;master_digest:str;native_artifact_sha256:str;native_source_sha256:str;shared_source_sha256:str;card_sha256:str=CARD_SHA256;public_law_sha256:str=PUBLIC_LAW_SHA256
    def validate(self)->None:
        for value in asdict(self).values():
            if not isinstance(value,str) or len(value)!=64:raise FrontierError("frontier binding digest invalid")

@dataclass(frozen=True)
class CheckpointReceipt:
    replicate_role:str;arm:str;initial_checkpoint_path:str;initial_checkpoint_sha256:str;final_checkpoint_path:str;final_checkpoint_sha256:str;initial_optimizer_path:str;initial_optimizer_sha256:str;final_optimizer_path:str;final_optimizer_sha256:str;update:int;source_manifest_sha256:str;coordinate_digest:str;master_digest:str;origin_lease_id:str;externally_accepted:bool
    def validate_preidentity(self,result_root:Path,source_manifest_sha256:str,coordinate_digest:str)->None:
        if self.replicate_role not in REPLICATE_ROLES or self.arm not in LEARNED_ARMS or self.update!=256 or self.externally_accepted is not True:raise FrontierError("checkpoint receipt slot/state differs")
        if (self.source_manifest_sha256,self.coordinate_digest)!=(source_manifest_sha256,coordinate_digest) or len(self.master_digest)!=64 or not self.origin_lease_id:raise FrontierError("checkpoint receipt preidentity binding differs")
        paths=(self.initial_checkpoint_path,self.final_checkpoint_path,self.initial_optimizer_path,self.final_optimizer_path);digests=(self.initial_checkpoint_sha256,self.final_checkpoint_sha256,self.initial_optimizer_sha256,self.final_optimizer_sha256)
        root=Path(result_root).resolve()
        for raw,digest in zip(paths,digests):
            if not Path(raw).is_absolute():raise FrontierError("checkpoint artifact path is not absolute")
            path=Path(raw).resolve()
            try:path.relative_to(root)
            except ValueError as error:raise FrontierError("checkpoint artifact escapes result root") from error
            if len(digest)!=64 or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise FrontierError("checkpoint artifact/hash differs")
    def validate(self,result_root:Path,bindings:FrontierBindings)->None:
        self.validate_preidentity(result_root,bindings.source_manifest_sha256,bindings.coordinate_digest)
        if self.master_digest!=bindings.master_digest:raise FrontierError("checkpoint receipt master binding differs")

def _load(path:Path)->dict[str,object]:return json.loads(path.read_text(encoding="ascii"))

@dataclass(frozen=True)
class ValidatedCheckpointBarrier:
    path:str;sha256:str;receipts:tuple[CheckpointReceipt,...];source_manifest_sha256:str;coordinate_digest:str;master_digest:str;origin_lease_id:str
    def validate_binding(self,result_root:Path,bindings:FrontierBindings)->tuple[CheckpointReceipt,...]:
        if (self.source_manifest_sha256,self.coordinate_digest,self.master_digest)!=(bindings.source_manifest_sha256,bindings.coordinate_digest,bindings.master_digest):raise FrontierError("checkpoint barrier runtime binding differs")
        for receipt in self.receipts:receipt.validate(result_root,bindings)
        return self.receipts

def validate_checkpoint_barrier_preidentity(path:Path,result_root:Path,source_manifest_sha256:str,coordinate_digest:str)->ValidatedCheckpointBarrier:
    target=Path(path).resolve()
    try:raw=target.read_bytes();value=json.loads(raw.decode("ascii"))
    except (OSError,UnicodeError,json.JSONDecodeError) as error:raise FrontierError("external CM checkpoint barrier is absent or invalid") from error
    rows=value.get("receipts");required={(role,arm) for role in REPLICATE_ROLES for arm in LEARNED_ARMS}
    if value.get("schema")!="VNFC_BPCR_R09_CM_GLOBAL_CHECKPOINT_ACCEPTANCE_V1" or value.get("issuer")!="CM_variable_n_fleet_churn_b4" or value.get("technically_accepted") is not True or value.get("source_manifest_sha256")!=source_manifest_sha256 or value.get("coordinate_digest")!=coordinate_digest or value.get("accepted_slots")!=32 or value.get("checkpoint_artifacts")!=64 or value.get("optimizer_artifacts")!=64 or not isinstance(rows,list):raise FrontierError("external CM checkpoint barrier differs")
    try:receipts=tuple(CheckpointReceipt(**row) for row in rows)
    except TypeError as error:raise FrontierError("checkpoint receipt schema differs") from error
    if len(receipts)!=32 or {(r.replicate_role,r.arm) for r in receipts}!=required:raise FrontierError("checkpoint slot inventory differs")
    for receipt in receipts:receipt.validate_preidentity(result_root,source_manifest_sha256,coordinate_digest)
    checkpoint_paths=tuple(Path(path).resolve() for receipt in receipts for path in (receipt.initial_checkpoint_path,receipt.final_checkpoint_path))
    optimizer_paths=tuple(Path(path).resolve() for receipt in receipts for path in (receipt.initial_optimizer_path,receipt.final_optimizer_path))
    if len(set(checkpoint_paths))!=64 or len(set(optimizer_paths))!=64 or len(set(checkpoint_paths+optimizer_paths))!=128:raise FrontierError("checkpoint/optimizer artifact paths are not unique")
    masters={receipt.master_digest for receipt in receipts};origins={receipt.origin_lease_id for receipt in receipts}
    if len(masters)!=1 or len(origins)!=1:raise FrontierError("checkpoint barrier master/origin inventory differs")
    return ValidatedCheckpointBarrier(str(target),hashlib.sha256(raw).hexdigest(),receipts,source_manifest_sha256,coordinate_digest,next(iter(masters)),next(iter(origins)))

def validate_checkpoint_barrier(path:Path,result_root:Path,bindings:FrontierBindings)->tuple[CheckpointReceipt,...]:
    barrier=validate_checkpoint_barrier_preidentity(path,result_root,bindings.source_manifest_sha256,bindings.coordinate_digest)
    return barrier.validate_binding(result_root,bindings)

class AtomicFrontier:
    def __init__(self,root:Path,bindings:FrontierBindings):self.root=Path(root);self.bindings=bindings
    @classmethod
    def create(cls,root:Path,bindings:FrontierBindings,permit:ActivityPermit,*,now:object)->"AtomicFrontier":
        permit.require_active(now=now);bindings.validate()  # type: ignore[arg-type]
        if bindings.source_manifest_sha256!=permit.source_manifest_sha256 or bindings.coordinate_digest!=permit.coordinate_digest:raise FrontierError("permit/frontier binding differs")
        if permit.replacement_of is not None:raise FrontierError("replacement lease cannot originate a new frontier")
        root=Path(root);root.mkdir(parents=True,exist_ok=False);write_once(root/"bindings.json",canonical_json_bytes({"schema":"VNFC_BPCR_R09_BLINDED_FRONTIER_BINDINGS_V1",**asdict(bindings),"origin_lease_id":permit.origin_lease_id,"scientific_values_exposed":False,"partial_inspection_permitted":False}));return cls(root,bindings)
    @classmethod
    def resume(cls,root:Path,bindings:FrontierBindings,permit:ActivityPermit,*,now:object)->"AtomicFrontier":
        permit.require_active(now=now)  # type: ignore[arg-type]
        stored=_load(Path(root)/"bindings.json");required={"schema","source_manifest_sha256","coordinate_digest","master_digest","native_artifact_sha256","native_source_sha256","shared_source_sha256","card_sha256","public_law_sha256","origin_lease_id","scientific_values_exposed","partial_inspection_permitted"}
        if set(stored)!=required or stored.get("schema")!="VNFC_BPCR_R09_BLINDED_FRONTIER_BINDINGS_V1" or stored.get("scientific_values_exposed") is not False or stored.get("partial_inspection_permitted") is not False:raise FrontierError("stored frontier binding schema differs")
        if permit.replacement_of is None:
            expected={"schema":"VNFC_BPCR_R09_BLINDED_FRONTIER_BINDINGS_V1",**asdict(bindings),"origin_lease_id":permit.origin_lease_id,"scientific_values_exposed":False,"partial_inspection_permitted":False}
            if stored!=expected:raise FrontierError("same-lease resume binding differs")
        else:
            stable=("coordinate_digest","master_digest","shared_source_sha256","card_sha256","public_law_sha256")
            if any(stored.get(key)!=getattr(bindings,key) for key in stable) or stored.get("origin_lease_id")!=permit.origin_lease_id or bindings.source_manifest_sha256!=permit.source_manifest_sha256 or bindings.coordinate_digest!=permit.coordinate_digest or permit.preserved_master_digest!=bindings.master_digest:raise FrontierError("replacement resume changed coordinate/master/origin binding")
        return cls(Path(root),bindings)
    def append_generation(self,slot:str,generation:int,*,previous_generation_sha256:str|None,state_path:str,state_sha256:str,optimizer_step:int,training_episodes_completed:int,joint_decisions_completed:int)->str:
        if not slot or generation<0:raise ValueError("frontier generation address invalid")
        if previous_generation_sha256 is not None and len(previous_generation_sha256)!=64:raise FrontierError("frontier predecessor digest differs")
        state=(self.root/state_path).resolve()
        try:state.relative_to(self.root.resolve())
        except ValueError as error:raise FrontierError("resume state escapes frontier") from error
        if len(state_sha256)!=64 or not state.is_file() or hashlib.sha256(state.read_bytes()).hexdigest()!=state_sha256:raise FrontierError("resume state digest differs")
        body={"schema":"VNFC_BPCR_R09_BLINDED_GENERATION_V1","slot":slot,"generation":generation,"previous_generation_sha256":previous_generation_sha256,"bindings_sha256":hashlib.sha256((self.root/"bindings.json").read_bytes()).hexdigest(),"state_path":state_path,"state_sha256":state_sha256,"optimizer_step":optimizer_step,"training_episodes_completed":training_episodes_completed,"joint_decisions_completed":joint_decisions_completed,"scientific_values_exposed":False,"partial_inspection_permitted":False}
        return write_once(self.root/f"{slot}.g{generation:04d}.json",canonical_json_bytes(body))
    def _validate_category_node(self,path:Path,category:str,expected:int)->None:
        try:value=_load(path)
        except (OSError,json.JSONDecodeError) as error:raise FrontierError("category index cannot be read") from error
        if set(value)!={"schema","category","bindings","cardinality","children"} or value["schema"]!="VNFC_BPCR_R09_ATOMIC_CATEGORY_INDEX_V1" or value["category"]!=category or value["bindings"]!=asdict(self.bindings) or value["cardinality"]!=expected or not isinstance(value["children"],list):raise FrontierError("category index schema/binding/cardinality differs")
        total=0
        for child in value["children"]:
            if set(child)!={"path","sha256","cardinality"}:raise FrontierError("category child schema differs")
            target=(path.parent/child["path"]).resolve()
            try:target.relative_to(self.root.resolve())
            except ValueError as error:raise FrontierError("category child escapes result root") from error
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=child["sha256"] or not isinstance(child["cardinality"],int) or child["cardinality"]<1:raise FrontierError("category child hash/cardinality differs")
            try:payload=_load(target)
            except (OSError,json.JSONDecodeError) as error:raise FrontierError("category payload cannot be read") from error
            expected_payload={"schema":"VNFC_BPCR_R09_BLINDED_CATEGORY_PAYLOAD_V1","category":category,"bindings":asdict(self.bindings),"logical_cardinality":child["cardinality"]}
            if any(payload.get(key)!=expected_value for key,expected_value in expected_payload.items()) or set(payload)!={"schema","category","bindings","logical_cardinality","value"}:raise FrontierError("category payload schema/binding/cardinality differs")
            total+=child["cardinality"]
        if total!=expected:raise FrontierError("recursive category cardinality differs")
    def seal_complete(self,inventory:Mapping[str,int],artifact_rows:Sequence[Mapping[str,object]],checkpoint_barrier:ValidatedCheckpointBarrier,frontier_predecessors:Mapping[str,str],*,failure_hook:Callable[[str],None]|None=None)->Path:
        if dict(inventory)!=PANEL_COUNTS:raise FrontierError("complete panel count inventory differs")
        checkpoint_barrier.validate_binding(self.root.parent,self.bindings)
        if len(artifact_rows)!=len(COMPLETE_CATEGORIES) or {row.get("category") for row in artifact_rows}!=set(COMPLETE_CATEGORIES) or any(set(row)!={"category","path","sha256","cardinality"} for row in artifact_rows):raise FrontierError("complete atomic category inventory differs")
        required_slots={f"{role}.{arm}" for role in REPLICATE_ROLES for arm in LEARNED_ARMS}
        if set(frontier_predecessors)!=required_slots or any(len(value)!=64 for value in frontier_predecessors.values()):raise FrontierError("complete manifest frontier predecessor inventory differs")
        for slot,digest in frontier_predecessors.items():
            predecessor=self.root/f"{slot}.g0256.json"
            if not predecessor.is_file() or hashlib.sha256(predecessor.read_bytes()).hexdigest()!=digest:raise FrontierError("complete manifest frontier predecessor hash differs")
        for row in artifact_rows:
            category=str(row["category"]);path=self.root/str(row["path"])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row["sha256"]:raise FrontierError("atomic artifact inventory differs")
            if row["cardinality"]!=CATEGORY_CARDINALITIES[category]:raise FrontierError("atomic category cardinality differs")
            self._validate_category_node(path,category,CATEGORY_CARDINALITIES[category])
        manifest={"schema":"VNFC_BPCR_R09_COMPLETE_ATOMIC_MANIFEST_V1","bindings":asdict(self.bindings),"counts":dict(inventory),"checkpoint_barrier_sha256":checkpoint_barrier.sha256,"frontier_predecessors":dict(sorted(frontier_predecessors.items())),"artifacts":list(artifact_rows),"complete":True,"partial_interpretation_permitted":False}
        final=self.root.parent/"COMPLETE_MANIFEST.json";write_once(final,canonical_json_bytes(manifest),failure_hook=failure_hook);return final
