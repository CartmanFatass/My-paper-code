from __future__ import annotations
import ast
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import pytest
from experiments.candidates.vsp_06_mssr import vsp06_b2r1_source_bound_exact_feasibility as selector
from experiments.candidates.vsp_06_mssr import vsp06_b2r1_independent_exact_manifest_verifier as verifier
from experiments.candidates.vsp_06_mssr import vsp06_b2r1_authenticated_partner_recall_credit_efficiency as toy

ROOT = Path(__file__).resolve().parents[4]
LEDGER = ROOT / "docs/research/candidates/vsp_06_mssr/VSP06_B2R1_CONSTRAINT_TARGET_LEDGER_V1.json"
RUNNER = ROOT / "scripts/run_vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py"
SOURCE_PATHS = (
    ROOT / "experiments/candidates/vsp_06_mssr/vsp06_b2r1_source_bound_exact_feasibility.py",
    ROOT / "experiments/candidates/vsp_06_mssr/vsp06_b2r1_independent_exact_manifest_verifier.py",
    ROOT / "experiments/candidates/vsp_06_mssr/vsp06_b2r1_authenticated_partner_recall_credit_efficiency.py",
    RUNNER,
)
DOMAIN = "VSP06-B2R1-SYNTHETIC-NONCANONICAL-V1"
TOKEN = "SYNTHETIC_STRUCTURAL_VALID_ONLY"

def row(y: int = 0, nonce: int = 0, base: str = "q", branch: str = "KEEP") -> dict[str, object]:
    return {"consumer":"synthetic","seed_row":"s","panel":"p","branch":branch,"retention_length":6,
            "y":y,"reset_y":0,"target_identity":0,"target_version":0,"event_type":"e",
            "decoy_sequence":[[0,1,2,False]],"current_bytes":"c","roster":"r","legal_mask":"1111",
            "clock":"clock","rng_binding":"none","quartet_base":base,"nonce":nonce}

def authorization(paths: list[str] | None = None) -> dict[str, object]:
    return {"direction":"CAND-VSP-06-MSSR","candidate":"CAND-VSP-06-MSSR@adversarial-revision-v8",
            "treatment_id":selector.TREATMENT_ID,"selector_id":selector.SELECTOR_ID,"verifier_id":selector.VERIFIER_ID,
            "scientific_parent":"898af9e848ce45f3510560a96ae454651a9f0736","final_commit":"a"*40,
            "source_build_read_allowlist":paths or [str(SOURCE_PATHS[0])],"formal":False,"synthetic_only":False,
            "zero_start_activity":dict(toy.ACTIVITY_COUNTERS)}

def load_runner():
    spec=importlib.util.spec_from_file_location("b2r1_runner",RUNNER); assert spec and spec.loader
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def test_exact_fresh_identities_salt_seed_and_real_nul() -> None:
    assert selector.SELECTOR_ID == "VSP06-B2R1-SB-EF-CP-SAT-V1"
    assert selector.VERIFIER_ID == "VSP06-B2R1-INDEPENDENT-EXACT-MANIFEST-VERIFIER-V1"
    assert selector.CATALOG_ID == "VSP06-B2R1-AUTHENTICATED-PARTNER-RECALL-CATALOG-V1"
    assert selector.LEDGER_ID == "VSP06-B2R1-CONSTRAINT-TARGET-LEDGER-V1"
    assert selector.SALT == "8100799/" and selector.PARAMETER_ASSIGNMENTS["random_seed"] == 8100699
    assert selector.DECISION_PREFIX.endswith(b"\0") and not selector.DECISION_PREFIX.endswith(b"\\0")

def test_hand_calculated_golden_tuple_bytes_digest_bucket_and_decision() -> None:
    expected=b'["synthetic","s","p","KEEP",6,0,0,0,0,"e",[[0,1,2,false]],"c","r","1111","clock","none","q",0]'
    assert selector.canonical_tuple_bytes(row()) == expected
    assert verifier._tuple_bytes(row()) == expected
    assert hashlib.sha256(expected).hexdigest() == "5c6791e7221c6428060537a05f0a3a4483006187c86570287e4ecf8140449257"
    assert selector.bucket_for_tuple(expected) == 2
    assert selector.decision_key(expected).hex() == "2974802fc55c88e86dbb30cbf63be4104f168531b235c9d1f105e539bbaf2d1c"

def test_declared_order_nfc_integer_boolean_and_duplicates() -> None:
    with pytest.raises(selector.SelectorInvalid, match="declared order"):
        selector.canonical_tuple_bytes(dict(reversed(tuple(row().items()))))
    bad=row(); bad["nonce"]=True
    with pytest.raises(selector.SelectorInvalid): selector.canonical_tuple_bytes(bad)
    bad=row(); bad["consumer"]="e\u0301"
    with pytest.raises(selector.SelectorInvalid): selector.canonical_tuple_bytes(bad)
    raw={"catalog_id":selector.CATALOG_ID,"salt":selector.SALT,"rows":[row(),row()]}
    with pytest.raises(selector.SelectorInvalid, match="unique"): selector.parse_catalog(raw)

def test_digest_collision_uses_tuple_byte_tie_break() -> None:
    a=selector.CatalogRow(0,row(0,0),b"b","",0,"train",bytes(32))
    b=selector.CatalogRow(1,row(1,1),b"a","",0,"train",bytes(32))
    assert selector.canonical_order((a,b)) == (1,0)

def test_exact_ledger_counts_and_independent_wire_defaults() -> None:
    raw=json.loads(LEDGER.read_text(encoding="utf-8")); equations=selector.parse_ledger(raw)
    expected={"split_bucket_disjointness":3,"primary_counts":144,"calibration_counts":10,
              "checkpoint_counts":660,"y_conditional_marginals":6048,"reset_fresh_y_independence":3200,
              "keep_quartets":16,"anti_lookup_coverage":60,"structural_eligibility":5}
    assert raw["family_counts"] == expected and len(equations) == 10146
    assert verifier._parse_ledger(raw) and verifier._expected_sat_parameter_bytes()
    assert hashlib.sha256(verifier._expected_sat_parameter_bytes()).hexdigest()

def replica(status: str) -> dict[str, object]:
    return {"selector_identity":selector.SELECTOR_ID,"terminal_status":status,"membership_vector":[1,0],
            "membership_vector_sha256":"x","selected_tuple_sha256":["y"],"manifest":{},"manifest_sha256":"z"}

def test_replica_complete_status_must_match() -> None:
    assert selector.compare_replicas(replica("FEASIBLE"),replica("FEASIBLE"))["terminal_status"] == "FEASIBLE"
    with pytest.raises(selector.SelectorInvalid, match="disagree"):
        selector.compare_replicas(replica("FEASIBLE"),replica("OPTIMAL"))
    source=inspect.getsource(verifier.verify)
    assert "terminal_status" in source and "replica reports disagree" in source

def selected(values: list[dict[str, object]]) -> list[dict[str, object]]:
    return [{"tuple":value,"bytes":selector.canonical_tuple_bytes(value),"tuple_sha256":"x","bucket":0,"split":"train"} for value in values]

def synthetic_bundle() -> dict[str,object]:
    rows=[row(0,0),row(1,1),row(2,2),row(3,3)]
    for value in rows: value["consumer"]="final_keep"
    cases=((0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3),(2,0),(2,1),(2,2),(2,3),(3,0),(3,1),(3,2),(3,3))
    events=("target_absent_payload","unauth_target_decoy","renewal_marker","dummy_roster")
    for index,(y,fresh) in enumerate(cases):
        value=row(y,4+index,"reset-"+str(index),"RESET"); value["reset_y"]=fresh
        value["target_identity"]=(y+fresh)%4; value["target_version"]=(2*y+fresh)%4
        value["event_type"]=events[(y+fresh)%4]
        value["decoy_sequence"]=[[(y+fresh)%4,(y+fresh+1)%4,(y+fresh+2)%4,bool((y+fresh)%2)]]
        rows.append(value)
    catalog={"catalog_id":selector.CATALOG_ID,"salt":selector.SALT,"synthetic_only":True,"domain":DOMAIN,"rows":rows}
    universe={"universe_id":"VSP06-B2R1-INDEPENDENT-SYNTHETIC-UNIVERSE-V1","salt":selector.SALT,"synthetic_only":True,"domain":DOMAIN,"rows":[dict(value) for value in rows]}
    templates=[{"name_template":"synthetic/"+family,"family":family,"axes":{},
        "terms":[{"coefficient":1,"predicate":{"in":{"branch":["KEEP","RESET","CURRENT"]}}}],"rhs":20}
        for family in verifier.CANONICAL_FAMILY_COUNTS]
    body={"ledger_id":selector.LEDGER_ID,"equation_semantics":"sum(integer_coefficient * selected_row_indicator) == integer_rhs",
        "equation_templates":templates,"family_counts":{family:1 for family in verifier.CANONICAL_FAMILY_COUNTS}}
    ledger={**body,"ledger_digest":hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()}
    payloads=[json.dumps([value[field] for field in selector.TUPLE_FIELDS],separators=(",",":"),ensure_ascii=False,allow_nan=False).encode() for value in rows]
    selected_entries=[{"tuple_sha256":hashlib.sha256(payload).hexdigest(),"tuple_bytes_hex":payload.hex()} for payload in sorted(payloads)]
    witness={"synthetic_only":True,"domain":DOMAIN,"selected_count":20,"vector":[1]*20,"selected":selected_entries}
    prefix=b"VSP06-B2R1-SB-EF-CP-SAT-V1/decision-order/v1"+bytes((0,))
    ordered=sorted(payloads,key=lambda payload:(hashlib.sha256(prefix+payload).digest(),payload))
    manifest={"verifier_id":verifier.VERIFIER_ID,"selector_id":verifier.SELECTOR_ID,"synthetic_only":True,"domain":DOMAIN,
        "catalog_digest":hashlib.sha256(json.dumps(catalog,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest(),
        "universe_digest":hashlib.sha256(json.dumps(universe,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest(),
        "ledger_digest":ledger["ledger_digest"],"selected_count":20,
        "entries":[{"tuple_sha256":hashlib.sha256(payload).hexdigest(),"tuple_bytes_hex":payload.hex(),"arm":arm}
            for payload in ordered for arm in (toy.CANDIDATE_ARM,toy.GENERIC_ARM)]}
    manifest_digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    replicas=[{"status":"FEASIBLE","complete":True,"synthetic_only":True,"domain":DOMAIN,"vector":[1]*20,
        "selected":[dict(item) for item in selected_entries],"manifest_digest":manifest_digest} for _ in range(2)]
    return {"catalog":catalog,"universe_spec":universe,"ledger":ledger,"witness":witness,"replicas":replicas,"proposed_manifest":manifest}

def test_synthetic_complete_quartet_and_duplicate_or_incomplete_rejection() -> None:
    complete=[row(0,0),row(1,1),row(2,2),row(3,3)]
    for value in complete: value["consumer"]="final_keep"
    verifier._check_quartets(selected(complete))
    duplicate=[row(0,0),row(0,1),row(2,2),row(3,3)]
    incomplete=[row(0,0),row(1,1),row(2,2)]
    for value in duplicate+incomplete: value["consumer"]="final_keep"
    with pytest.raises(verifier.VerificationError, match="incomplete/duplicate"):
        verifier._check_quartets(selected(duplicate))
    with pytest.raises(verifier.VerificationError, match="incomplete/duplicate"):
        verifier._check_quartets(selected(incomplete))

def test_synthetic_success_is_only_structural_and_all_nine_families_are_checked() -> None:
    report=verifier.verify_synthetic(**synthetic_bundle())
    assert report["status"]==TOKEN and report["synthetic_only"] is True and report["canonical_rank_claim"] is False
    assert set(report["constraint_families"])==set(verifier.CANONICAL_FAMILY_COUNTS)

@pytest.mark.parametrize("family",tuple(verifier.CANONICAL_FAMILY_COUNTS))
def test_synthetic_each_family_corruption_fails(family: str) -> None:
    bundle=synthetic_bundle(); ledger=bundle["ledger"]
    next(item for item in ledger["equation_templates"] if item["family"]==family)["rhs"]=5
    body={key:value for key,value in ledger.items() if key!="ledger_digest"}
    ledger["ledger_digest"]=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    with pytest.raises(verifier.VerificationError,match="equation mismatch"):
        verifier.verify_synthetic(**bundle)

def test_synthetic_completeness_replica_manifest_and_admission_negatives() -> None:
    partial=synthetic_bundle(); partial["witness"]["vector"].pop()
    with pytest.raises(verifier.VerificationError,match="partial"): verifier.verify_synthetic(**partial)
    mutated=synthetic_bundle(); mutated["catalog"]["rows"][0]["nonce"]=999
    with pytest.raises(verifier.VerificationError,match="missing, mutated"): verifier.verify_synthetic(**mutated)
    outside=synthetic_bundle(); outside["universe_spec"]["rows"].pop()
    with pytest.raises(verifier.VerificationError,match="independent universe"): verifier.verify_synthetic(**outside)
    mismatch=synthetic_bundle(); mismatch["replicas"][1]["status"]="OPTIMAL"
    with pytest.raises(verifier.VerificationError,match="replica"): verifier.verify_synthetic(**mismatch)
    corrupt=synthetic_bundle(); corrupt["proposed_manifest"]["entries"].reverse()
    with pytest.raises(verifier.VerificationError,match="manifest"): verifier.verify_synthetic(**corrupt)
    report=verifier.verify_synthetic(**synthetic_bundle())
    with pytest.raises(verifier.VerificationError,match="synthetic"): verifier.reject_synthetic_for_canonical(report)
    with pytest.raises(toy.B2ContractError,match="synthetic"): toy.reject_synthetic_envelope_for_full(report)

def test_same_claimed_digest_unequal_bytes_rejected_separately() -> None:
    first=b"first"; digest=hashlib.sha256(first).hexdigest()
    entries=[{"tuple_sha256":digest,"tuple_bytes_hex":first.hex()},{"tuple_sha256":digest,"tuple_bytes_hex":b"second".hex()}]
    with pytest.raises(verifier.VerificationError,match="same claimed digest"):
        verifier._claimed_entries(entries,"synthetic")

def test_canonical_quartet_source_requires_64_groups_per_primary_seed() -> None:
    for source in (inspect.getsource(selector.validate_final_keep_support),inspect.getsource(verifier._check_canonical_catalog_support)):
        assert "64" in source and "256" in source and "primary_1" in source
        assert "quartet" in source and "y" in source

def test_authorization_contract_and_guards_precede_canonical_work(tmp_path: Path) -> None:
    selector.validate_stage2_authorization(authorization()); toy.validate_stage2_authorization(authorization())
    for bad in ({}, {**authorization(),"synthetic_only":True},{**authorization(),"final_commit":"short"}):
        with pytest.raises(selector.SelectorInvalid): selector.validate_stage2_authorization(bad)
        with pytest.raises(toy.B2ContractError): toy.validate_stage2_authorization(bad)
    runner=load_runner()
    missing=tmp_path/"missing-authorization.json"
    with pytest.raises(FileNotFoundError): runner.prepare_catalog(tmp_path/"catalog.json",tmp_path/"universe.json",missing)
    assert not (tmp_path/"catalog.json").exists()
    assert "stage2_authorization" in inspect.signature(selector.solve_replica).parameters
    assert "stage2_authorization_path" in inspect.signature(selector.run_two_replica_sequence).parameters
    assert "stage2_authorization" in inspect.signature(toy.run_registered_full).parameters

def test_exact_allowlist_glob_predecessor_link_and_valid_read_guards(tmp_path: Path,monkeypatch: pytest.MonkeyPatch) -> None:
    good=(tmp_path/"good.json"); good.write_text("{}",encoding="utf-8")
    other=(tmp_path/"other.json"); other.write_text("{}",encoding="utf-8")
    auth=authorization([str(good)])
    assert selector.authorize_read_path(auth,good)==good
    assert verifier.authorize_read_path(auth,good)==good
    with pytest.raises(selector.SelectorInvalid,match="authorized"): selector.authorize_read_path(auth,other)
    with pytest.raises(selector.SelectorInvalid,match="glob"): selector.safe_existing_path(tmp_path/"*.json")
    predecessor=tmp_path/("vsp06_"+"b2_"+"artifact.json"); predecessor.write_text("{}",encoding="utf-8")
    with pytest.raises(selector.SelectorInvalid,match="predecessor"): selector.safe_existing_path(predecessor)
    link=tmp_path/"link"; link.mkdir(); linked=link/"value.json"; linked.write_text("{}",encoding="utf-8")
    monkeypatch.setattr(selector,"_is_reparse",lambda path:path.name=="link")
    with pytest.raises(selector.SelectorInvalid,match="link/junction/reparse"): selector.safe_existing_path(linked)
    auth_path=tmp_path/"authorization.json"
    auth_value=authorization([str(auth_path),str(good)])
    auth_path.write_text(json.dumps(auth_value),encoding="utf-8")
    assert load_runner()._authorization(auth_path)==auth_value

def test_forbidden_verifier_import_and_preexisting_exclusive_output(tmp_path: Path) -> None:
    tree=ast.parse(SOURCE_PATHS[1].read_text(encoding="utf-8"))
    imported=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): imported.extend(alias.name for alias in node.names)
        elif isinstance(node,ast.ImportFrom): imported.append(node.module or "")
    assert not any(name.startswith(("ortools","torch","experiments")) for name in imported)
    output=tmp_path/"exclusive.json"; selector.write_exclusive(output,b"{}")
    with pytest.raises(selector.SelectorInvalid,match="already exists"): selector.write_exclusive(output,b"{}")

def episode_spec(branch: str) -> toy.EpisodeSpec:
    value=row(2,0,"q",branch); value.update({"consumer":"synthetic_only","seed_row":"synthetic",
        "target_identity":1,"target_version":1,"reset_y":3,"roster":"P0,P1,P2,P3,focal",
        "decoy_sequence":[[0,0,1,False],[1,1,2,False],[2,2,3,False],[3,3,0,False]]})
    return toy.EpisodeSpec.from_manifest_row(value)

@pytest.mark.parametrize("branch,target,write,reset",[("KEEP",2,0,0),("RESET",3,1,1),("CURRENT",2,1,0)])
def test_pure_keep_reset_current_semantics_without_training(branch: str,target: int,write:int,reset:int) -> None:
    episode=toy.AuthenticatedPartnerRecallRelay().build(episode_spec(branch))
    rejoin=next(step for step in episode.steps if step.phase=="REJOIN")
    assert episode.terminal_target==target and rejoin.write==write and rejoin.reset==reset
    assert toy.terminal_reward(target,target)==1 and toy.terminal_reward((target+1)%4,target)==-1

def test_control_and_equal_capacity_routing_structure_without_torch() -> None:
    controls=inspect.getsource(toy._controls)
    for literal in ("selected_p_zero","current_only_rebuild","cross_swap","decoy_replay","reset_stale_target"):
        assert literal in controls
    build=inspect.getsource(toy.build_policy)
    assert "CANDIDATE_ARM" in build and "ARMS" in build and "routing_gate" in build
    assert toy.CONTEXT_DIM==64 and toy.CARRIER_DIM==32 and toy.ARMS==(toy.CANDIDATE_ARM,toy.GENERIC_ARM)
    with pytest.raises(toy.B2ContractError,match="Stage-2"): toy.build_policy(toy.CANDIDATE_ARM,1)
    assert toy.SEEDS["calibration"]=={"environment":8100501,"initialization":8100502,"minibatch":8100503,"evaluation":8100504}
    assert toy.THRESHOLDS["current_arm_aulc_gap"]==0.05

def test_future_implementations_are_complete_not_stubs() -> None:
    assert "CpModel" in inspect.getsource(selector.solve_replica)
    assert "Popen" in inspect.getsource(selector._run_cold_replica)
    assert "for replica_index in (1, 2)" in inspect.getsource(selector.run_two_replica_sequence)
    assert "optimizer" in inspect.getsource(toy.run_registered_full)
    assert "yield" in inspect.getsource(toy.canonical_catalog_rows)
    assert toy.CAPS == {"model_fits":10,"trainer_invocations":10,"environment_episodes":44300,
        "environment_transitions":520000,"production_policy_forwards":540000,"learner_updates":1100,
        "optimizer_steps":1100,"evaluator_calls":75,"evaluation_episodes":10500,
        "sweeps":0,"retries":0,"rescues":0,"extra_roots":0}
    assert toy.EXPECTED_FULL_ACTIVITY["model_fits"] == 10 and len(toy.SEEDS) == 5

def passing() -> dict[str, object]:
    return {"contract_valid":True,"activity_nonzero":True,"caps_valid":True,"paired_exposure":True,
        "matched_shapes_counts_state":True,"terminal_ppo_only":True,"no_side_channel":True,
        "candidate_minus_generic_keep_aulc":.08,"candidate_final_keep":.55,"selected_p_mediation":.2,
        "cross_swap_follow_rate":.8,"candidate_decoy_accuracy_change":.02,"candidate_decoy_kernel_tv_change":.02,
        "current_arm_aulc_gap":.05,"reset_stale_target_rate":.15}

@pytest.mark.parametrize("name,value",[("candidate_final_keep",math.nan),("selected_p_mediation",math.inf),
    ("cross_swap_follow_rate",-0.1),("candidate_decoy_kernel_tv_change",1.1),
    ("reset_stale_target_rate",-0.01),("current_arm_aulc_gap",[0.0])])
def test_malformed_nonfinite_out_of_domain_evidence_is_invalid(name: str,value: object) -> None:
    evidence=passing(); evidence[name]=value; assert toy.classify_result(evidence) == toy.INVALID

@pytest.mark.parametrize("update,branch",[
    ({"contract_valid":False,"candidate_final_keep":0},toy.INVALID),
    ({"candidate_final_keep":.54,"selected_p_mediation":0},toy.NAVIGATION_FAIL),
    ({"selected_p_mediation":.19,"cross_swap_follow_rate":0},toy.MEDIATION_FAIL),
    ({"cross_swap_follow_rate":.79,"candidate_decoy_accuracy_change":1},toy.CROSS_SWAP_FAIL),
    ({"candidate_decoy_accuracy_change":.03,"reset_stale_target_rate":1},toy.DECOY_FAIL),
    ({"current_arm_aulc_gap":.06,"candidate_minus_generic_keep_aulc":0},toy.CURRENT_RESET_FAIL),
    ({"candidate_minus_generic_keep_aulc":.07},toy.NO_EFFICIENCY)])
def test_exact_gate_precedence(update: dict[str,object],branch: str) -> None:
    evidence=passing(); evidence.update(update); assert toy.classify_result(evidence) == branch

def test_aulc_and_toy_arithmetic_without_training() -> None:
    assert toy.normalized_keep_aulc([.25]*8) == pytest.approx(0)
    assert toy.normalized_keep_aulc([1.0]*8) == pytest.approx(1)
    assert toy.terminal_reward(2,2)==1 and toy.terminal_reward(1,2)==-1

def test_stage1_status_static_guards_zero_activity_and_reserved_absence() -> None:
    runner=load_runner(); status=runner.stage1_status()
    assert status["synthetic_only"] is True and status["domain"]==DOMAIN and status["success_token"]==TOKEN
    assert status["K_search"]==0 and status["hypothetical_transitions"]==0
    assert status["reserved_paths_absent"] is True and all(value==0 for value in status["activity"].values())
    assert len(status["activity"])==18
    sources="\n".join(path.read_text(encoding="utf-8") for path in SOURCE_PATHS)
    top_imports=[]
    for path in SOURCE_PATHS:
        tree=ast.parse(path.read_text(encoding="utf-8"))
        top_imports.extend(node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom)))
    rendered="\n".join(ast.unparse(node) for node in top_imports)
    assert "torch" not in rendered and "ortools" not in rendered
    assert ("vsp06_"+"b2_") not in sources and (str(selector.PARAMETER_ASSIGNMENTS["random_seed"])+"/") not in sources
    runtime_sources="\n".join(path.read_text(encoding="utf-8") for path in SOURCE_PATHS[:4])
    assert ".glob(" not in runtime_sources and ".rglob(" not in runtime_sources

def test_index_is_synthetic_only_and_does_not_overclaim() -> None:
    text=(ROOT/"docs/research/candidates/vsp_06_mssr/VSP06_B2R1_CODE_SCIENCE_INDEX.md").read_text(encoding="utf-8")
    assert DOMAIN in text and TOKEN in text and "no canonical feasibility" in text.lower()
    assert "dormant" in text.lower() and "stage 2" in text.lower()
