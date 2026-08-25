"""Identity-free revision-09 empirical preactivity contract."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final

from .contracts import CARD_REVISION,CARD_SHA256,PUBLIC_LAW_SHA256,canonical_json_bytes

EMPIRICAL_STAGE:Final[str]="VNFC-BPCR-R09-FULL-EMPIRICAL-PANEL"
REPLICATE_ROLES:Final[tuple[str,...]]=tuple(f"BPCR-REP-{i:02d}" for i in range(16))
LEARNED_ARMS:Final[tuple[str,...]]=("MAPR","DIRECT")
CONCLUSION_ARMS:Final[tuple[str,...]]=("MAPR","DIRECT","BCRH","CUT")
DOMAIN_LABELS:Final[tuple[str,...]]=(
    "model-initialization/base","model-initialization/direct-residual",
    "training/world","training/presentation","training/action",
    "training/minibatch-permutation","validation/world","validation/presentation",
    "conclusion/world","conclusion/presentation","conclusion/cut-derangement",
)
PANEL_COUNTS:Final[dict[str,int]]={
    "replicates":16,"learned_arms":2,"updates_per_arm":256,
    "episodes_per_update":16,"decisions_per_episode":6,"epochs_per_update":4,
    "minibatches_per_epoch":4,"training_episodes":131072,
    "learned_joint_decisions":786432,"optimizer_minibatch_steps":131072,
    "validation_rollouts":8192,"conclusion_rollouts":4096,"bcrh_rollouts":1024,
    "initial_final_checkpoint_slots":64,"optimizer_state_slots":64,
    "inference_coordinates":90,"canonical_partition_visits":2949120,
    "complementary_subset_means":5898060,"exact_rational_comparison_ceiling":79626150,
    "logical_operation_ceiling":27715520000,"deterministic_certificate_fixtures":64,
}
FAMILY_SPECS:Final[tuple[tuple[str,int,int],...]]=(("efficacy",12,28),("non_harm",24,14),("training_gain",8,41),("competence",28,12),("mechanism",18,19))

def coordinate_proposal(source_manifest_sha256:str|None=None)->dict[str,object]:
    proposal={"schema":"VNFC_BPCR_R09_COORDINATE_PROPOSAL_V1","materialized":False,"stage":EMPIRICAL_STAGE,"card_revision":CARD_REVISION,"card_sha256":CARD_SHA256,"public_law_sha256":PUBLIC_LAW_SHA256,"replicate_roles":list(REPLICATE_ROLES),"machine_labels":None,"rng":{"derivation":"HMAC-SHA256","master_bits":256,"master":None,"master_digest":None,"address_prefix":CARD_REVISION,"fields":["replicate_role","domain","purpose","roster_size","failed_zone","update_or_panel_row","episode_row","physical_time","draw"],"domains":list(DOMAIN_LABELS),"sampled_values":[]},"arms":{"learned":list(LEARNED_ARMS),"conclusion":list(CONCLUSION_ARMS),"common_training_world_roles":True,"independent_action_domains":True,"shared_base_initialization":True,"direct_residual_initial_output":"exact_zero"},"counts":dict(PANEL_COUNTS),"families":[{"name":name,"m":m,"q":q} for name,m,q in FAMILY_SPECS],"barriers":{"all_training_slots_before_external_cm_checkpoint_acceptance":True,"evaluation_after_external_acceptance_only":True,"one_indivisible_complete_manifest":True,"partial_interpretation":False},"source_manifest_sha256":source_manifest_sha256}
    return proposal

def coordinate_proposal_digest(source_manifest_sha256:str|None=None)->str:
    return hashlib.sha256(canonical_json_bytes(coordinate_proposal(source_manifest_sha256))).hexdigest()

def lease_request(source_manifest_sha256:str,coordinate_digest:str,native_binding:dict[str,object],*,repository_root:Path,result_root:Path,phase:str)->dict[str,object]:
    repo=Path(repository_root).resolve();root=Path(result_root).resolve()
    try:root.relative_to(repo)
    except ValueError as error:raise ValueError("requested result root must be inside repository") from error
    if phase not in ("TRAIN","EVALUATE"):raise ValueError("lease request phase differs")
    lease_path=repo/"temp/leases"/f"VNFC_BPCR_R09_ROOT_{phase}_LEASE.json";module="experiments.candidates.variable_n_fleet_churn_bpcr_r09"
    paths={"result_root":str(root),"frontier_root":str(root/"frontiers"),"train_terminal_path":str(root/"TRAIN_COMPLETE.json"),"evaluation_terminal_path":str(root/"EVALUATION_COMPLETE.json"),"run_identity_path":str(root/"RUN_IDENTITY.json"),"preactivity_acceptance_path":str(root/"CM_PREACTIVITY_ACCEPTANCE.json"),"checkpoint_acceptance_path":str(root/"CM_CHECKPOINT_ACCEPTANCE.json"),"complete_manifest_path":str(root/"COMPLETE_MANIFEST.json")}
    return {"schema":"VNFC_BPCR_R09_ROOT_LEASE_REQUEST_V1","authority":"REQUEST_ONLY","lease_issued":False,"stage":EMPIRICAL_STAGE,"phase":phase,"source_manifest_sha256":source_manifest_sha256,"coordinate_proposal_digest":coordinate_digest,"card_sha256":CARD_SHA256,"public_law_sha256":PUBLIC_LAW_SHA256,"native_binding":native_binding,"paths":paths,"execution":{"python_executable":"C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","module":module,"argv":["C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe","-m",module,"--phase",phase,"--lease",str(lease_path)]},"resources":{"cpu_only":True,"gpu_count":0,"max_independent_workers":32,"cpu_core_hours_upper":1500,"ram_gib":64,"scratch_gib":60,"durable_artifacts_gib":30,"validity_hours":168},"counts":dict(PANEL_COUNTS),"complete_panel_only":True,"replacement_lease_preserves_coordinate_and_master":True,"production_launch":False}
