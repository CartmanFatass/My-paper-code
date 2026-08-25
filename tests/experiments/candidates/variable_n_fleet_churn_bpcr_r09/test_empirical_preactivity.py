from __future__ import annotations

from datetime import datetime,timezone
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.branch_reducer import exhaustive_branch_table,reduce_branches,reduce_from_intervals,ASSOCIATION_KEYS,VALUE_KEYS
from fractions import Fraction
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.empirical_contract import DOMAIN_LABELS,FAMILY_SPECS,PANEL_COUNTS,REPLICATE_ROLES,coordinate_proposal,coordinate_proposal_digest,lease_request
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import deterministic_general_episode
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.frontier import AtomicFrontier,CATEGORY_CARDINALITIES,COMPLETE_CATEGORIES,CheckpointReceipt,FrontierBindings,FrontierError,freeze_preactivity_template,validate_checkpoint_barrier_preidentity,validate_preactivity_template
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.inference import inference_contract
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.lease import LeaseError,_replacement_resume_binding,validate_root_lease
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import native_artifact_identity
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.rng import domain_registry,address,Coordinate
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.runner import prepare_activity_authority,run_interactive_conformance
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.source_manifest import SourceManifestError,validate_manifest
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.services import validation_addresses,conclusion_addresses,ConcretePanelService
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.bcrh_exception import exception_certificate,exception_certificate_digest
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.torch_models import MAPR4,DirectSetAR,ModelContractError,model_structure_contract,initial_learned_availability,variable_prefix_mask
import torch
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.training import work_count_contract
from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import evaluation
from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import runner
from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import lease as lease_module
from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import source_manifest as source_manifest_module
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.contracts import CARD_SHA256,NATIVE_ABI_VERSION,PUBLIC_LAW_SHA256,SHARED_COMPONENT
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.evaluation import AtomicCategoryPayload,EvaluationError,ExactPanelReducer,PanelPlan,family_coordinate_names,full_panel_plan,publish_categories,run_bcrh_batch

def test_identity_free_coordinate_and_disjoint_hmac_registry()->None:
    manifest=validate_manifest();proposal=coordinate_proposal(manifest["sha256"]);registry=domain_registry()
    assert proposal["materialized"] is False and proposal["machine_labels"] is None
    assert proposal["rng"]["master"] is None and proposal["rng"]["master_digest"] is None and proposal["rng"]["sampled_values"]==[]
    assert tuple(proposal["replicate_roles"])==REPLICATE_ROLES and len(set(DOMAIN_LABELS))==len(DOMAIN_LABELS)
    assert all(any(domain.startswith(prefix) for domain in DOMAIN_LABELS) for prefix in ("model-initialization/","training/","validation/","conclusion/"))
    assert registry["unique"] and registry["master"] is None
    coordinate=address(replicate_role="BPCR-REP-00",domain="training/action",purpose="fixture",roster_size=3,failed_zone=1,update_or_panel_row=0,episode_row=0,physical_time=0,draw=0)
    assert isinstance(coordinate,Coordinate) and coordinate.encode().startswith(b"\x00\x00")

def test_source_manifest_and_native_shared_bindings_are_complete()->None:
    manifest=validate_manifest();identity=native_artifact_identity();value=json.loads(Path(manifest["path"]).read_text("ascii"))
    transition_path=Path(manifest["path"]).with_name(source_manifest_module.TRANSITION_NAME);raw=transition_path.read_bytes();transition=json.loads(raw.decode("ascii"))
    assert value["status"]=="FINAL" and manifest["file_count"]==len(value["files"]) and manifest["sha256"]=="89f5cd04753130288eb819ef56359e7a93e29ef9559fc65af8a7806e11164e3c"
    assert raw==source_manifest_module.manifest_bytes(transition) and transition["manifest"]["sha256"]==manifest["sha256"]
    assert transition["authority"]=="VALIDATION_ONLY_NO_ACTIVITY_OR_LEASE_AUTHORITY"
    assert transition["resume_fence"]=={"coordinate_digest":"9a2a4affb03e4c2eb2ded763991fcbe9bfef18b6df19457b5ad67e2dce31e87b","master_digest":"9e5927ca82fda74e557eb38cf4af3b0d149ac0fef0f0d89319796aed4c6a64a9","origin_lease_id":"VNFC-BPCR-R09-ROOT-TRAIN-20260821-01","result_root":"C:\\Projects\\HMASD\\artifacts\\VNFC_BPCR_R09_FUTURE","frontier_shared_source_sha256":"c378997ec45b599c19a34b7ce1c8cdecbd127f695aed7218a625dc8bebcf2e1b","scientific_values_exposed":False,"partial_inspection_permitted":False}
    assert value["immutable"]["shared_source_sha256"]=="c378997ec45b599c19a34b7ce1c8cdecbd127f695aed7218a625dc8bebcf2e1b"
    assert transition["shared_source"]=={"path":"envs/native/production_backend.py","old_sha256":"c378997ec45b599c19a34b7ce1c8cdecbd127f695aed7218a625dc8bebcf2e1b","new_sha256":"c79a26e4a71678dcde16993a33a01cff735d90116d8ea70b6577232be39939ce"}
    assert tuple(row["path"] for row in transition["candidate_local_overrides"])==source_manifest_module.LOCAL_OVERRIDE_PATHS
    repo=Path(manifest["path"]).resolve().parents[3]
    assert all(hashlib.sha256((repo/row["path"]).read_bytes()).hexdigest()==row["new_sha256"] for row in transition["candidate_local_overrides"])
    assert value["native"]["artifact_sha256"]==identity["artifact_sha256"] and value["native"]["abi_version"]==1
    paths={row["path"] for row in value["files"]};assert "envs/native/production_backend.py" in paths and any(path.endswith("bpcr_checker.hpp") for path in paths)
    assert any(path.endswith("VNFC_UAV_BOUNDED_POST_CHURN_RECOVERY_PUBLIC_PHYSICAL_LAW_BINDING.md") for path in paths) and any(path.endswith("/__main__.py") for path in paths)

def test_source_alignment_transition_and_live_hash_tampering_fail_closed(monkeypatch:pytest.MonkeyPatch,tmp_path:Path)->None:
    canonical=Path(__file__).resolve().parents[4]/"experiments/candidates/variable_n_fleet_churn_bpcr_r09/shared_source_alignment_transition.json";value=json.loads(canonical.read_text("ascii"))
    value["shared_source"]["new_sha256"]="0"*64;tampered=tmp_path/"tampered-transition.json";tampered.write_bytes(source_manifest_module.manifest_bytes(value))
    with monkeypatch.context() as patch:
        patch.setattr(source_manifest_module,"TRANSITION_NAME",str(tampered))
        with pytest.raises(SourceManifestError,match="transition shared binding differs"):validate_manifest()
    value=json.loads(canonical.read_text("ascii"));value["resume_fence"]["partial_inspection_permitted"]=True;tampered_fence=tmp_path/"tampered-fence.json";tampered_fence.write_bytes(source_manifest_module.manifest_bytes(value))
    with monkeypatch.context() as patch:
        patch.setattr(source_manifest_module,"TRANSITION_NAME",str(tampered_fence))
        with pytest.raises(SourceManifestError,match="preserved resume fence differs"):validate_manifest()
    real_sha=source_manifest_module._sha;repo=Path(__file__).resolve().parents[4]
    authorized=tuple((repo/path).resolve() for path in (source_manifest_module.SHARED_SOURCE_PATH,*source_manifest_module.LOCAL_OVERRIDE_PATHS))
    for source in authorized:
        with monkeypatch.context() as patch:
            patch.setattr(source_manifest_module,"_sha",lambda path,source=source:"0"*64 if path.resolve()==source else real_sha(path))
            with pytest.raises(SourceManifestError,match="transition-authorized live source differs"):validate_manifest()

def test_source_mismatch_and_absent_external_lease_fail_before_master_or_activity(tmp_path:Path)->None:
    manifest_path=Path(validate_manifest()["path"]);value=json.loads(manifest_path.read_text("ascii"));value["files"][0]["sha256"]="0"*64;bad=tmp_path/"bad.json";bad.write_text(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n",encoding="ascii")
    with pytest.raises(SourceManifestError):validate_manifest(bad)
    copied=tmp_path/"copied-frozen-manifest.json";copied.write_bytes(manifest_path.read_bytes())
    with pytest.raises(SourceManifestError):validate_manifest(copied)
    value=json.loads(manifest_path.read_text("ascii"));value["files"].append({"path":"experiments/candidates/variable_n_fleet_churn_bpcr_r09/new_production.py","sha256":"0"*64});extra=tmp_path/"extra.json";extra.write_text(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n",encoding="ascii")
    with pytest.raises(SourceManifestError):validate_manifest(extra)
    with pytest.raises(LeaseError):validate_root_lease(tmp_path/"no-root-lease.json",now=datetime.now(timezone.utc))
    with pytest.raises(LeaseError):prepare_activity_authority(tmp_path/"no-root-lease.json",tmp_path/"no-cm.json",now=datetime.now(timezone.utc))

def test_counts_barriers_models_inference_and_exhaustive_branch_map()->None:
    assert work_count_contract()["training_episodes"]==PANEL_COUNTS["training_episodes"]
    assert PANEL_COUNTS["validation_rollouts"]==8192 and PANEL_COUNTS["conclusion_rollouts"]==4096 and PANEL_COUNTS["bcrh_rollouts"]==1024
    assert len(validation_addresses())==8192 and len(conclusion_addresses())==4096
    assert tuple((x[1],x[2]) for x in FAMILY_SPECS)==((12,28),(24,14),(8,41),(28,12),(18,19))
    assert inference_contract()["all_coordinate_partition_visits"]==2949120
    contract=model_structure_contract();assert contract["shared_base"]=="bitwise_copy" and contract["direct_residual_output"]=="exact_zero" and not contract["random_default_initializer"]
    with pytest.raises(TypeError):MAPR4()  # type: ignore[call-arg]
    with pytest.raises(TypeError):DirectSetAR()  # type: ignore[call-arg]
    table=exhaustive_branch_table();assert len(table)==8192
    flags={key:False for key in ASSOCIATION_KEYS+VALUE_KEYS};assert reduce_branches(flags)==("ASSOCIATION_NONIDENTIFIED_PRECISION","NONIDENTIFIED_PRECISION")
    availability=initial_learned_availability(torch.tensor([[-1,-1,-1,2],[1,-1,3,-1]],dtype=torch.int64),5)
    assert not availability[0,2] and availability[0,0] and not availability[1,1] and not availability[1,3]
    assert variable_prefix_mask(torch.tensor([[-1,-1,-1,2]]),3,torch.tensor([2]),5).tolist()==[False] and variable_prefix_mask(torch.tensor([[-1,-1,-1,2]]),0,torch.tensor([1]),5).tolist()==[True]
    certificate=exception_certificate();assert certificate["materialized_coordinates"]==0 and certificate["candidate_ceiling_per_boundary"]==1961 and certificate["real_boundaries"]==6 and not certificate["tail"]["recursive"] and len(exception_certificate_digest())==64

def test_evaluation_only_teacher_forcing_distinguishes_support_from_probability_underflow()->None:
    class UnderflowMAPR(MAPR4):
        def candidate_logits(self,encoded:torch.Tensor,summary:torch.Tensor,token:int)->tuple[torch.Tensor,torch.Tensor]:
            batch,n,_=encoded.shape;assert n==2
            logits=torch.tensor((0.0,-1000.0,-2000.0),dtype=torch.float64).expand(batch,-1)
            return logits,torch.zeros((batch,n+1,64),dtype=torch.float64)
    model=UnderflowMAPR({name:torch.zeros(shape,dtype=torch.float64) for name,shape in MAPR4.SHAPES.items()})
    inputs=(torch.zeros((1,2,38),dtype=torch.float64),torch.zeros((1,2,15),dtype=torch.float64),torch.zeros((1,4),dtype=torch.float64),torch.ones((1,2,4),dtype=torch.bool),torch.full((1,4),-1,dtype=torch.int64),torch.tensor(((0,1),),dtype=torch.int64))
    supported=torch.tensor(((1,0,2,2),),dtype=torch.int64)
    with pytest.raises(ModelContractError,match="outside masked support"):model(*inputs,forced_commands=supported)
    diagnostic=model(*inputs,forced_commands=supported,_evaluation_support_valid_forcing=True)
    assert diagnostic["token_probabilities"][0,0,1]==0 and torch.isfinite(diagnostic["log_probability"]).all()
    unsupported=torch.tensor(((0,0,2,2),),dtype=torch.int64)
    with pytest.raises(ModelContractError,match="outside masked support"):model(*inputs,forced_commands=unsupported,_evaluation_support_valid_forcing=True)
    with pytest.raises(ModelContractError,match="requires teacher commands"):model(*inputs,_evaluation_support_valid_forcing=True)
    ordinary=torch.tensor(((0,1,2,2),),dtype=torch.int64)
    default=model(*inputs,forced_commands=ordinary);explicit_default=model(*inputs,forced_commands=ordinary,_evaluation_support_valid_forcing=False)
    assert all(torch.equal(default[key],explicit_default[key]) for key in default)
    uniforms=torch.tensor(((0.0,0.5,0.5,0.5),),dtype=torch.float64)
    free=model(*inputs,uniforms);explicit_free=model(*inputs,uniforms,_evaluation_support_valid_forcing=False)
    assert all(torch.equal(free[key],explicit_free[key]) for key in free)
    assert Path(evaluation.__file__).read_text("utf-8").count("_evaluation_support_valid_forcing=True")==1

def test_deterministic_decoder_separates_null_rank_from_nonbest_sentinel_and_stays_in_support()->None:
    parameters={name:torch.zeros(shape,dtype=torch.float64) for name,shape in MAPR4.SHAPES.items()}
    inputs=(torch.zeros((1,2,38),dtype=torch.float64),torch.zeros((1,2,15),dtype=torch.float64),torch.zeros((1,4),dtype=torch.float64),torch.ones((1,2,4),dtype=torch.bool),torch.full((1,4),-1,dtype=torch.int64),torch.tensor(((1,0),),dtype=torch.int64))
    tied=MAPR4(parameters);tied_default=tied(*inputs);tied_explicit=tied(*inputs,_evaluation_support_valid_forcing=False)
    assert tied_default["command"].tolist()==[[1,0,2,2]]
    assert all(torch.equal(tied_default[key],tied_explicit[key]) for key in tied_default)
    class NullBestMAPR(MAPR4):
        def candidate_logits(self,encoded:torch.Tensor,summary:torch.Tensor,token:int)->tuple[torch.Tensor,torch.Tensor]:
            batch,n,_=encoded.shape;assert n==2
            return torch.tensor((-2.0,-1.0,0.0),dtype=torch.float64).expand(batch,-1),torch.zeros((batch,n+1,64),dtype=torch.float64)
    null_best=NullBestMAPR(parameters)(*inputs)
    assert null_best["command"].tolist()==[[2,2,2,2]]
    class AgentBestMAPR(MAPR4):
        def candidate_logits(self,encoded:torch.Tensor,summary:torch.Tensor,token:int)->tuple[torch.Tensor,torch.Tensor]:
            batch,n,_=encoded.shape;assert n==2
            return torch.tensor((1.0,0.0,-2.0),dtype=torch.float64).expand(batch,-1),torch.zeros((batch,n+1,64),dtype=torch.float64)
    agent_best=AgentBestMAPR(parameters)(*inputs)
    assert agent_best["command"].tolist()==[[0,1,2,2]]
    for output in (tied_default,null_best,agent_best):
        available=initial_learned_availability(inputs[4],2)
        for token,choice in enumerate(output["command"][0]):
            support=torch.cat((available&inputs[3][:,:,token],torch.ones((1,1),dtype=torch.bool)),1)
            assert bool(support[0,choice])
            if choice<2:available[0,choice]=False

def test_fixed_sufficiency_requires_registered_reverse_mission_nonharm()->None:
    intervals={};pops=("aggregate","zone1","zone2")
    for a,b in (("MAPR","DIRECT"),("MAPR","BCRH"),("MAPR","CUT"),("DIRECT","BCRH")):
        for pop in pops:
            intervals[f"fail/{a}-{b}/{pop}"]=(Fraction(-1,20),Fraction(1,20));intervals[f"total/{a}-{b}/{pop}"]=(Fraction(-1,100),Fraction(1,100));intervals[f"intact/{a}-{b}/{pop}"]=(Fraction(-1,100),Fraction(1,100))
    for z in ("zone1","zone2"):intervals[f"gate/action_sensitivity/{z}"]=(Fraction(1,2),Fraction(1,1));intervals[f"gate/association_opportunity/{z}"]=(Fraction(1,2),Fraction(1,1));intervals[f"gate/association_change/{z}"]=(Fraction(1,2),Fraction(1,1))
    for arm in ("MAPR","DIRECT"):
        for n in (3,5):
            for z in (1,2):intervals[f"gate/training_gain/{arm}/N{n}/zone{z}"]=(Fraction(1,2),Fraction(1,1))
        for cell in ("N3z1","N3z2","N5z1","N5z2","heldz1","heldz2"):
            for endpoint in ("fail","total"):intervals[f"gate/competence/{arm}/{cell}/{endpoint}"]=(Fraction(4,5),Fraction(1,1))
    for z in (1,2):
        for endpoint in ("fail","total"):intervals[f"gate/competence/BCRH/heldz{z}/{endpoint}"]=(Fraction(4,5),Fraction(1,1))
    for kind in ("residual_active","command_change"):
        for cell in ("N3z1","N3z2","N5z1","N5z2","heldz1","heldz2"):intervals[f"gate/direct_{kind}/{cell}"]=(Fraction(1,2),Fraction(1,1))
    assert reduce_from_intervals(intervals,{"overall_valid":True,"association_valid":True})[1]=="FIXED_SUFFICIENCY"
    intervals["total/MAPR-BCRH/aggregate"]=(Fraction(-1,100),Fraction(1,10))
    assert reduce_from_intervals(intervals,{"overall_valid":True,"association_valid":True})[1]!="FIXED_SUFFICIENCY"

def test_preactivity_frontier_atomic_crash_and_resume_binding(tmp_path:Path)->None:
    manifest=validate_manifest();native=native_artifact_identity();bindings={"source_manifest_sha256":manifest["sha256"],"coordinate_digest":coordinate_proposal_digest(manifest["sha256"]),"native_artifact_sha256":native["artifact_sha256"],"native_source_sha256":native["native_source_sha256"],"shared_source_sha256":"c378997ec45b599c19a34b7ce1c8cdecbd127f695aed7218a625dc8bebcf2e1b","card_sha256":native["immutable_inputs"]["science_card_sha256"],"public_law_sha256":native["immutable_inputs"]["public_law_sha256"]}
    final=tmp_path/"template.json";freeze_preactivity_template(final,bindings);validate_preactivity_template(final,bindings)
    changed=dict(bindings);changed["coordinate_digest"]="0"*64
    with pytest.raises(FrontierError):validate_preactivity_template(final,changed)
    failed=tmp_path/"failed.json"
    with pytest.raises(RuntimeError):freeze_preactivity_template(failed,bindings,failure_hook=lambda phase:(_ for _ in ()).throw(RuntimeError("crash")) if phase=="temp_fsynced" else None)
    assert not failed.exists()

@pytest.mark.parametrize("width",[8,32])
def test_runner_adapter_uses_interactive_cpp_without_python_fallback(width:int)->None:
    rows=run_interactive_conformance(tuple(deterministic_general_episode(1+i%2) for i in range(width)))
    assert len(rows)==width and all(row["terminal"] and row["integrated_ticks"]==240 for row in rows)

def test_concrete_evaluate_service_tiny_dry_run_and_full_plan_wiring()->None:
    fixtures=tuple(deterministic_general_episode(1+i%2) for i in range(8));receipt=ConcretePanelService.dry_run(fixtures)
    assert receipt["boundaries"]==6 and receipt["certificates"]==64 and receipt["validation_plan"]==8192 and receipt["conclusion_plan"]==4096 and not receipt["question_relevant_values_retained"]

def test_resource_request_is_proposal_only_and_no_old_route_names()->None:
    manifest=validate_manifest();native=native_artifact_identity();repo=Path(__file__).resolve().parents[4];request=lease_request(manifest["sha256"],coordinate_proposal_digest(manifest["sha256"]),{"abi_version":1,"artifact_sha256":native["artifact_sha256"],"source_sha256":native["native_source_sha256"],"build_key":native["build_key"]},repository_root=repo,result_root=repo/"artifacts/VNFC_BPCR_R09_FUTURE",phase="TRAIN")
    assert request["authority"]=="REQUEST_ONLY" and request["lease_issued"] is False and request["production_launch"] is False
    assert request["execution"]["argv"][:3]==["C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","-m","experiments.candidates.variable_n_fleet_churn_bpcr_r09"] and request["resources"]["max_independent_workers"]==32
    package=Path(__file__).resolve().parents[4]/"experiments/candidates/variable_n_fleet_churn_bpcr_r09"
    text="\n".join(path.read_text("utf-8").lower() for path in package.rglob("*.py"))
    assert all(name not in text for name in ("vnfc-tepr","fixed-fh","global-exact","full-graph"))


def test_full_evaluate_plan_and_noninjectable_service_wiring(monkeypatch:pytest.MonkeyPatch,tmp_path:Path)->None:
    plan=full_panel_plan();assert plan.full and len(plan.validation)==8192 and len(plan.conclusion)==4096
    assert sum(row[1]=="BCRH" for row in plan.conclusion)==1024
    observed={}
    def fake_execute_plan(**kwargs:object)->Path:observed.update(kwargs);return tmp_path/"COMPLETE_MANIFEST.json"
    monkeypatch.setattr(evaluation,"execute_plan",fake_execute_plan)
    frontier=SimpleNamespace();authority=SimpleNamespace();rng=SimpleNamespace();barrier=SimpleNamespace(path=str(tmp_path/"CM_CHECKPOINT_ACCEPTANCE.json"),receipts=())
    result=ConcretePanelService(frontier).execute(authority,rng,barrier,now=datetime.now(timezone.utc))
    assert result==tmp_path/"COMPLETE_MANIFEST.json" and observed["plan"].full and observed["frontier"] is frontier
    assert observed["checkpoint_barrier"] is barrier and "callback" not in ConcretePanelService.execute.__annotations__


def test_smaller_evaluate_plan_requires_private_construction_seal()->None:
    plan=PanelPlan((("BPCR-REP-00","MAPR",0,3,1,0),),(("BPCR-REP-00","MAPR",1,0),),False)
    with pytest.raises(EvaluationError,match="construction-test-only"):
        evaluation.execute_plan(plan=plan,authority=SimpleNamespace(),rng=SimpleNamespace(),frontier=SimpleNamespace(),checkpoint_barrier=SimpleNamespace(),now=datetime.now(timezone.utc))


def test_missing_evaluate_barrier_precedes_identity_frontier_and_native_guard(monkeypatch:pytest.MonkeyPatch,tmp_path:Path)->None:
    result_root=tmp_path/"future-result"
    permit=SimpleNamespace(phase="EVALUATE",source_manifest_sha256="1"*64,coordinate_digest="2"*64,result_root=str(result_root),paths={"checkpoint_acceptance_path":str(result_root/"CM_CHECKPOINT_ACCEPTANCE.json")})
    authority=SimpleNamespace(permit=permit,_seal=runner._AUTHORITY_SEAL)
    monkeypatch.setattr(runner,"_prepare_activity_authority_before_native",lambda *args,**kwargs:authority)
    touched=[]
    def forbidden(*args:object,**kwargs:object)->None:touched.append(True);raise AssertionError("post-barrier mutation was reached")
    monkeypatch.setattr(runner,"require_native_production",forbidden)
    monkeypatch.setattr(runner,"open_or_create_run_rng",forbidden)
    monkeypatch.setattr(runner,"native_artifact_identity",forbidden)
    with pytest.raises(FrontierError,match="absent or invalid"):
        runner.concrete_phase_main(tmp_path/"missing-lease.json","EVALUATE",now=datetime.now(timezone.utc))
    assert not touched and not result_root.exists() and not any(tmp_path.rglob("*"))


def _checkpoint_barrier_fixture(root:Path)->tuple[Path,dict[str,object]]:
    result=root/"result";result.mkdir();receipts=[]
    for index,(role,arm) in enumerate((role,arm) for role in REPLICATE_ROLES for arm in ("MAPR","DIRECT")):
        fields={}
        for kind in ("initial_checkpoint","final_checkpoint","initial_optimizer","final_optimizer"):
            path=result/f"{index:02d}.{kind}.bin";path.write_bytes(f"{index}:{kind}".encode("ascii"));fields[f"{kind}_path"]=str(path.resolve());fields[f"{kind}_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        receipts.append(asdict(CheckpointReceipt(role,arm,**fields,update=256,source_manifest_sha256="1"*64,coordinate_digest="2"*64,master_digest="3"*64,origin_lease_id="construction-origin",externally_accepted=True)))
    value={"schema":"VNFC_BPCR_R09_CM_GLOBAL_CHECKPOINT_ACCEPTANCE_V1","issuer":"CM_variable_n_fleet_churn_b4","technically_accepted":True,"source_manifest_sha256":"1"*64,"coordinate_digest":"2"*64,"accepted_slots":32,"checkpoint_artifacts":64,"optimizer_artifacts":64,"receipts":receipts}
    path=result/"CM_CHECKPOINT_ACCEPTANCE.json";path.write_text(json.dumps(value,sort_keys=True,separators=(",",":")),encoding="ascii");return path,value


@pytest.mark.parametrize("kind",["initial_checkpoint","initial_optimizer"])
def test_checkpoint_barrier_rejects_cross_slot_path_reuse(tmp_path:Path,kind:str)->None:
    path,value=_checkpoint_barrier_fixture(tmp_path);barrier=validate_checkpoint_barrier_preidentity(path,path.parent,"1"*64,"2"*64);assert len(barrier.receipts)==32
    rows=value["receipts"];assert isinstance(rows,list)
    rows[1][f"{kind}_path"]=rows[0][f"{kind}_path"];rows[1][f"{kind}_sha256"]=rows[0][f"{kind}_sha256"]
    bad=path.parent/f"BAD_{kind}.json";bad.write_text(json.dumps(value,sort_keys=True,separators=(",",":")),encoding="ascii")
    with pytest.raises(FrontierError,match="not unique"):validate_checkpoint_barrier_preidentity(bad,path.parent,"1"*64,"2"*64)


def test_replacement_resume_preserves_prior_coordinate_master_origin_without_new_files(tmp_path:Path)->None:
    result=tmp_path/"construction-result";frontier_root=result/"frontiers";frontier_root.mkdir(parents=True)
    coordinate="1"*64;master="2"*64;origin="construction-origin";shared="3"*64
    current=FrontierBindings("4"*64,coordinate,master,"5"*64,"6"*64,shared)
    stored={"schema":"VNFC_BPCR_R09_BLINDED_FRONTIER_BINDINGS_V1",**asdict(current),"source_manifest_sha256":"7"*64,"native_artifact_sha256":"8"*64,"native_source_sha256":"9"*64,"origin_lease_id":origin,"scientific_values_exposed":False,"partial_inspection_permitted":False}
    (frontier_root/"bindings.json").write_text(json.dumps(stored,sort_keys=True,separators=(",",":")),encoding="ascii")
    identity_path=result/"identity.fixture.json";identity_path.write_text(json.dumps({"schema":"VNFC_BPCR_R09_BLINDED_RUN_IDENTITY_V1","coordinate_digest":coordinate,"origin_lease_id":origin,"master_digest":master,"sealed_master":"construction-fixture","partial_inspection_permitted":False},sort_keys=True,separators=(",",":")),encoding="ascii")
    paths={"run_identity_path":identity_path,"frontier_root":frontier_root};lease={"coordinate_proposal_digest":coordinate,"preserved_master_digest":master,"origin_lease_id":origin,"replacement_of":origin}
    before={path.relative_to(result).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in result.rglob("*") if path.is_file()}
    assert _replacement_resume_binding(lease,paths)==(coordinate,master)
    permit=SimpleNamespace(replacement_of=origin,preserved_master_digest=master,origin_lease_id=origin,source_manifest_sha256=current.source_manifest_sha256,coordinate_digest=coordinate,require_active=lambda **_:None)
    resumed=AtomicFrontier.resume(frontier_root,current,permit,now=datetime.now(timezone.utc));assert resumed.bindings==current
    for field,bad in (("coordinate_proposal_digest","a"*64),("preserved_master_digest","b"*64),("origin_lease_id","other-origin"),("replacement_of","other-lease")):
        changed=dict(lease);changed[field]=bad
        with pytest.raises(LeaseError,match="lineage"):_replacement_resume_binding(changed,paths)
    after={path.relative_to(result).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in result.rglob("*") if path.is_file()}
    assert after==before


def test_root_lease_initial_coordinate_is_source_bound_but_replacement_uses_stored_binding(monkeypatch:pytest.MonkeyPatch,tmp_path:Path)->None:
    manifest_sha="a"*64;coordinate="1"*64;master="2"*64;origin="construction-origin";native={"abi_version":1,"artifact_sha256":"3"*64,"source_sha256":"4"*64,"build_key":"5"*64}
    manifest_file=tmp_path/"manifest.fixture.json";manifest_file.write_text(json.dumps({"native":native}),encoding="ascii");monkeypatch.setattr(lease_module,"validate_manifest",lambda:{"sha256":manifest_sha,"path":str(manifest_file)})
    monkeypatch.setattr(lease_module,"__file__",str(tmp_path/"a/b/c/lease.py"));result=tmp_path/"result";frontier_root=result/"frontiers";frontier_root.mkdir(parents=True)
    identity=result/"RUN_IDENTITY.json";identity.write_text(json.dumps({"schema":"VNFC_BPCR_R09_BLINDED_RUN_IDENTITY_V1","coordinate_digest":coordinate,"origin_lease_id":origin,"master_digest":master,"sealed_master":"construction-fixture","partial_inspection_permitted":False},sort_keys=True,separators=(",",":")),encoding="ascii")
    bindings=FrontierBindings("6"*64,coordinate,master,"7"*64,"8"*64,"9"*64);(frontier_root/"bindings.json").write_text(json.dumps({"schema":"VNFC_BPCR_R09_BLINDED_FRONTIER_BINDINGS_V1",**asdict(bindings),"origin_lease_id":origin,"scientific_values_exposed":False,"partial_inspection_permitted":False},sort_keys=True,separators=(",",":")),encoding="ascii")
    paths={"result_root":str(result.resolve()),"frontier_root":str(frontier_root.resolve()),"train_terminal_path":str((result/"TRAIN_COMPLETE.json").resolve()),"evaluation_terminal_path":str((result/"EVALUATION_COMPLETE.json").resolve()),"run_identity_path":str(identity.resolve()),"preactivity_acceptance_path":str((result/"CM_PREACTIVITY_ACCEPTANCE.json").resolve()),"checkpoint_acceptance_path":str((result/"CM_CHECKPOINT_ACCEPTANCE.json").resolve()),"complete_manifest_path":str((result/"COMPLETE_MANIFEST.json").resolve())}
    now=datetime(2026,8,20,12,tzinfo=timezone.utc);lease_path=tmp_path/"replacement.json";module="experiments.candidates.variable_n_fleet_churn_bpcr_r09"
    value={"schema":"VNFC_BPCR_R09_ROOT_LEASE_V1","issuer":"Operational Root","lease_id":"replacement-1","origin_lease_id":origin,"activity_authorized":True,"stage":"VNFC-BPCR-R09-FULL-EMPIRICAL-PANEL","phase":"TRAIN","issued_at":"2026-08-20T11:00:00Z","expires_at":"2026-08-20T13:00:00Z","source_manifest_sha256":manifest_sha,"coordinate_proposal_digest":coordinate,"card_sha256":CARD_SHA256,"public_law_sha256":PUBLIC_LAW_SHA256,"component":SHARED_COMPONENT,"abi_version":NATIVE_ABI_VERSION,"native_binding":native,"complete_panel_only":True,"python_environment_loop":False,"python_action_loop":False,"python_fallback":False,"replacement_of":origin,"preserve_coordinate_digest":True,"preserve_master_digest":True,"preserved_master_digest":master,"paths":paths,"execution":{"python_executable":"C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","module":module,"argv":["C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","-m",module,"--phase","TRAIN","--lease",str(lease_path.resolve())]},"resources":{"cpu_only":True,"gpu_count":0,"max_independent_workers":32,"cpu_core_hours_upper":1500,"ram_gib":64,"scratch_gib":60,"durable_artifacts_gib":30,"validity_hours":168},"counts":PANEL_COUNTS}
    before={path.relative_to(result).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in result.rglob("*") if path.is_file()};lease_path.write_text(json.dumps(value),encoding="ascii");permit=validate_root_lease(lease_path,now=now);assert permit.source_manifest_sha256==manifest_sha and permit.coordinate_digest==coordinate and permit.preserved_master_digest==master
    initial=dict(value);initial.update({"lease_id":origin,"origin_lease_id":origin,"replacement_of":None,"preserved_master_digest":None,"coordinate_proposal_digest":coordinate_proposal_digest(manifest_sha)});initial_path=tmp_path/"initial.json";initial["execution"]={**initial["execution"],"argv":["C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","-m",module,"--phase","TRAIN","--lease",str(initial_path.resolve())]};initial_path.write_text(json.dumps(initial),encoding="ascii");assert validate_root_lease(initial_path,now=now).coordinate_digest==coordinate_proposal_digest(manifest_sha)
    after={path.relative_to(result).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in result.rglob("*") if path.is_file()};assert after==before


def test_evaluate_native_route_rejects_sub_b8_before_model_or_host()->None:
    with pytest.raises(EvaluationError,match="B>=8"):run_bcrh_batch((object(),)*7,mapr_relabel_model=None,relabel_permutations=())  # type: ignore[arg-type]


def _synthetic_evaluate_panel()->tuple[list[dict[str,object]],list[dict[str,object]]]:
    validation=[];conclusion=[];arm_fail={"MAPR":60,"DIRECT":50,"BCRH":40,"CUT":45}
    for replicate in range(16):
        role=f"BPCR-REP-{replicate:02d}"
        for arm in ("MAPR","DIRECT"):
            for checkpoint in (0,256):
                for roster in (3,5):
                    for zone in (1,2):
                        for row in range(32):validation.append({"replicate_role":role,"arm":arm,"checkpoint":checkpoint,"roster_size":roster,"failed_zone":zone,"panel_row":row,"fail_endpoint":((30 if checkpoint==0 else 50)+replicate,100),"total_endpoint":(80+replicate,100),"intact_endpoint":(75+replicate,100),"residual_active":(1,)*6 if arm=="DIRECT" else (),"residual_change":(1,)*6 if arm=="DIRECT" else ()})
        for arm in ("MAPR","DIRECT","BCRH","CUT"):
            for zone in (1,2):
                for row in range(32):conclusion.append({"replicate_role":role,"arm":arm,"failed_zone":zone,"panel_row":row,"fail_endpoint":(arm_fail[arm]+replicate,100),"total_endpoint":(80+replicate,100),"intact_endpoint":(75+replicate,100),"residual_active":(1,)*6 if arm=="DIRECT" else (),"residual_change":(1,)*6 if arm=="DIRECT" else (),"action_sensitive":arm=="MAPR","association_opportunity":int(arm=="MAPR"),"association_change":int(arm=="MAPR")})
    return validation,conclusion


def test_evaluate_replicate_first_reducer_builds_five_registered_matrices()->None:
    validation,conclusion=_synthetic_evaluate_panel();matrices=ExactPanelReducer(validation,conclusion).matrices()
    assert {name:(len(rows),len(rows[0])) for name,rows in matrices.items()}=={"efficacy":(16,12),"non_harm":(16,24),"training_gain":(16,8),"competence":(16,28),"mechanism":(16,18)}
    assert matrices["efficacy"][0][0]==pytest.approx(.1) and matrices["training_gain"][0][0]==pytest.approx(.2)
    assert matrices["mechanism"][0]==[1.0]*18 and sum(map(len,family_coordinate_names().values()))==90


def test_evaluate_atomic_categories_check_cardinality_and_are_idempotent(tmp_path:Path)->None:
    frontier=SimpleNamespace(root=tmp_path,bindings=FrontierBindings(*(("0"*64,)*6)))
    values={name:AtomicCategoryPayload(CATEGORY_CARDINALITIES[name],{"construction_fixture":name}) for name in COMPLETE_CATEGORIES}
    first=publish_categories(frontier,values);second=publish_categories(frontier,values);assert first==second and len(first)==len(COMPLETE_CATEGORIES)
    bad=dict(values);bad["gates"]=AtomicCategoryPayload(8,())
    with pytest.raises(FrontierError,match="logical cardinality"):publish_categories(frontier,bad)


def test_evaluate_coordinator_has_atomic_seal_and_no_placeholder_handle()->None:
    source=Path(evaluation.__file__).read_text("utf-8")
    assert ".seal_complete(PANEL_COUNTS" in source and "FULL_PANEL_EXECUTION_HANDLE" not in source and "partial_interpretation" not in source
