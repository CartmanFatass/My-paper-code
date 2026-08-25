from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.util
import io
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
    digest_map={relative:hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
        for relative in selector.SOURCE_CONFIG_RELATIVE_PATHS}
    digest_map_sha256=hashlib.sha256(json.dumps(
        digest_map,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False
    ).encode("utf-8")).hexdigest()
    environment_path=SOURCE_PATHS[0]
    return {"direction":"CAND-VSP-06-MSSR","candidate":"CAND-VSP-06-MSSR@adversarial-revision-v8",
            "treatment_id":selector.TREATMENT_ID,"selector_id":selector.SELECTOR_ID,"verifier_id":selector.VERIFIER_ID,
            "scientific_parent":"898af9e848ce45f3510560a96ae454651a9f0736","final_commit":"a"*40,
            "source_build_read_allowlist":paths or [str(SOURCE_PATHS[0])],"formal":False,"synthetic_only":False,
            "source_config_digest_map":digest_map,"source_config_digest_map_sha256":digest_map_sha256,
            "zero_start_activity":dict(toy.ACTIVITY_COUNTERS),
            "full_environment_receipt_path":str(environment_path),
            "full_environment_receipt_sha256":hashlib.sha256(environment_path.read_bytes()).hexdigest()}

def full_environment_receipt(artifact: Path) -> dict[str, object]:
    native=[[str(artifact.resolve()),hashlib.sha256(artifact.read_bytes()).hexdigest()]]
    digest=hashlib.sha256(json.dumps(native,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return {
        "schema_version":1,"python_implementation":"CPython","python_version":"3.11.0",
        "python_executable":str(artifact.resolve()),"python_executable_sha256":native[0][1],
        "ortools_version":"9.12.4544","ortools_source_tag":"v9.12",
        "solver_artifacts":native,"solver_artifact_set_sha256":digest,
        "sat_parameters_sha256":"0"*64,"sat_parameters_hex":"00",
        "sat_parameter_assignments":dict(selector.PARAMETER_ASSIGNMENTS),
        "sat_parameter_assignments_sha256":"1"*64,"os":"Windows","os_release":"test",
        "architecture":"AMD64","torch_distribution_version":"2.7.0",
        "torch_build_version":"2.7.0+cpu","torch_cpu_only":True,"torch_cuda_version":None,
        "torch_cuda_available":False,"torch_deterministic_algorithms":True,
        "torch_deterministic_warn_only":False,"torch_num_threads":1,
        "torch_num_interop_threads":1,"torch_native_artifacts":native,
        "torch_native_artifact_set_sha256":digest,
        "torch_distribution_inventory_sha256":"2"*64,
        "torch_build_config_sha256":"3"*64,
        "thread_environment":dict(selector.THREAD_ENVIRONMENT),
    }

def selector_receipt() -> dict[str, object]:
    value={key:None for key in selector.SELECTOR_RECEIPT_KEYS}
    value["replica_count"]=2
    value["activity_accounting"]={"sweeps":0,"retries":0,"rescues":0,"extra_roots":0}
    value["activity_counts"]=dict(toy.ACTIVITY_COUNTERS)
    return value

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
    universe={"universe_id":verifier.SYNTHETIC_UNIVERSE_SPEC_ID,"salt":selector.SALT,
        "synthetic_only":True,"domain":DOMAIN,
        "fixture_id":"VSP06-B2R1-HAND-AUTHORED-20-ROW-PROOF-V1",
        "parameters":{"keep_y":[0,1,2,3],"reset_cross_product":[0,1,2,3]}}
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
    incomplete=synthetic_bundle(); incomplete["catalog"]["rows"].pop()
    with pytest.raises(verifier.VerificationError,match="missing, mutated"): verifier.verify_synthetic(**incomplete)
    outside=synthetic_bundle(); outside["universe_spec"]["parameters"]["keep_y"].pop()
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
    with pytest.raises(FileNotFoundError): runner.orchestrate_stage2(missing)
    assert not selector.STAGE2_SESSION_ROOT.exists()
    assert "stage2_authorization" in inspect.signature(selector.solve_replica).parameters
    assert "stage2_authorization_path" in inspect.signature(selector.run_two_replica_sequence).parameters
    assert "stage2_authorization" in inspect.signature(toy.run_registered_full).parameters


@pytest.mark.parametrize(("field","value"),(
    ("formal",0),("formal",0.0),("synthetic_only",0),
))
def test_authorization_boolean_bindings_are_type_exact(
    field: str, value: object,
) -> None:
    bad={**authorization(),field:value}
    with pytest.raises(selector.SelectorInvalid):
        selector.validate_stage2_authorization(bad)
    with pytest.raises(verifier.VerificationError):
        verifier._validate_stage2_authorization(bad)
    with pytest.raises(toy.B2ContractError):
        toy.validate_stage2_authorization(bad)


def test_authoritative_json_loaders_reject_duplicate_keys(tmp_path: Path) -> None:
    duplicate=tmp_path/"duplicate.json"
    duplicate.write_text('{"formal":false,"formal":false}',encoding="utf-8")
    runner=load_runner()
    for loader,error in (
        (selector._load_json,selector.SelectorInvalid),
        (verifier._load,verifier.VerificationError),
        (runner._load,selector.SelectorInvalid),
    ):
        with pytest.raises(error,match="duplicate JSON"):
            loader(duplicate)


@pytest.mark.parametrize("field",(
    "schema_version","torch_num_threads","torch_num_interop_threads",
))
def test_environment_receipt_integer_fields_reject_float_substitution(
    field: str, tmp_path: Path,
) -> None:
    artifact=tmp_path/"native.dll"; artifact.write_bytes(b"native")
    receipt=full_environment_receipt(artifact); receipt[field]=1.0
    receipt_path=tmp_path/"full-environment.json"
    receipt_path.write_text(json.dumps(receipt,sort_keys=True,separators=(",",":")),encoding="utf-8")
    auth=authorization([str(receipt_path.resolve()),str(artifact.resolve())])
    auth["full_environment_receipt_path"]=str(receipt_path.resolve())
    auth["full_environment_receipt_sha256"]=hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    with pytest.raises(selector.SelectorInvalid,match="schema version|thread binding"):
        selector.load_full_environment_receipt(auth)


def test_explorer_audited_map_digest_and_live_source_drift_fail_closed() -> None:
    all_sources=[str((ROOT/relative).resolve()) for relative in selector.SOURCE_CONFIG_RELATIVE_PATHS]
    good=authorization(all_sources)
    assert selector.verify_authorized_source_config(good)==good["source_config_digest_map"]
    wrong_digest={**good,"source_config_digest_map_sha256":"0"*64}
    with pytest.raises(selector.SelectorInvalid,match="digest map"):
        selector.validate_stage2_authorization(wrong_digest)
    drift=copy.deepcopy(good)
    first=selector.SOURCE_CONFIG_RELATIVE_PATHS[0]
    drift["source_config_digest_map"][first]="0"*64
    drift["source_config_digest_map_sha256"]=hashlib.sha256(json.dumps(
        drift["source_config_digest_map"],sort_keys=True,separators=(",",":"),ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    with pytest.raises(selector.SelectorInvalid,match="differs from audited"):
        selector.verify_authorized_source_config(drift)


def test_runner_source_admission_precedes_claim_and_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    runner=load_runner(); events=[]
    monkeypatch.setattr(runner,"_authorization",lambda _path:authorization())
    def reject(_authorization: object) -> None:
        events.append("verify_source")
        raise selector.SelectorInvalid("synthetic source drift")
    monkeypatch.setattr(runner.selector,"verify_authorized_source_config",reject)
    monkeypatch.setattr(runner,"_claim_fixed_stage2_namespace",lambda _authorization:events.append("claim"))
    monkeypatch.setattr(runner.experiment,"canonical_universe_spec",lambda _authorization:events.append("universe"))
    monkeypatch.setattr(runner.experiment,"canonical_catalog_rows",lambda _authorization:events.append("catalog"))
    with pytest.raises(selector.SelectorInvalid,match="source drift"):
        runner.orchestrate_stage2(Path("synthetic-authorization-not-read.json"))
    assert events==["verify_source"]


def test_runner_secure_read_and_receipt_anchor_precede_receipt_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); receipt=tmp_path/"selector-receipt.json"
    receipt.write_text('{"manifest_content_sha256":"attacker-controlled"}',encoding="utf-8")
    auth=authorization([str(receipt.resolve())])
    calls=[]
    original=selector.authorized_json
    def tracked(value: object,path: Path) -> object:
        calls.append(path)
        return original(value,path)
    monkeypatch.setattr(runner.selector,"authorized_json",tracked)
    assert runner._authorized_load(auth,receipt)=={"manifest_content_sha256":"attacker-controlled"}
    assert calls==[receipt]
    monkeypatch.setattr(runner,"_authorization",lambda _path:auth)
    claim=tmp_path/"claim.json"; claim.write_text("{}",encoding="utf-8")
    failure=tmp_path/"failure.json"
    paths={"receipt":receipt,"claim":claim,"stage2_failure":failure}
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    monkeypatch.setattr(runner.selector,"verify_authorized_source_config",lambda *_args:None)
    monkeypatch.setattr(runner.selector,"load_full_environment_receipt",lambda *_args:(receipt,{}))
    monkeypatch.setattr(runner.selector,"safe_existing_path",lambda path:path)
    monkeypatch.setattr(runner.selector,"_require_exhaustive_allowlist",lambda *_args:None)
    monkeypatch.setattr(runner.selector,"validate_selector_environment_receipt",lambda *_args:None)
    monkeypatch.setattr(runner.experiment,"bind_full_environment",lambda *_args:None)
    monkeypatch.setattr(runner.selector,"authorized_json",lambda *_args:selector.exact_claim(auth,phase="stage2_selector_continuation"))
    monkeypatch.setattr(runner.selector,"validate_exact_claim",lambda *_args,**_kwargs:None)
    monkeypatch.setattr(runner,"_latest_stage2_activity",lambda *_args:dict(toy.ACTIVITY_COUNTERS))
    monkeypatch.setattr(runner,"_terminal_failure",lambda *_args,**_kwargs:{"branch":"terminal"})
    monkeypatch.setattr(runner,"_authorized_load",lambda *_args:pytest.fail("receipt fields read before digest anchor"))
    assert runner.run_full(Path("unused.json"),"0"*64)=={"branch":"terminal"}


def test_run_full_requires_external_receipt_digest_cli() -> None:
    runner=load_runner()
    with pytest.raises(SystemExit) as error:
        runner.main(["run-full","--stage2-authorization","unused.json"])
    assert error.value.code==2


def test_selector_receipt_schema_is_exact() -> None:
    exact=selector_receipt()
    selector.validate_selector_receipt_schema(exact)
    missing=dict(exact); missing.pop("manifest_content_sha256")
    with pytest.raises(selector.SelectorInvalid,match="key schema"):
        selector.validate_selector_receipt_schema(missing)
    extra={**exact,"unsealed_extra":None}
    with pytest.raises(selector.SelectorInvalid,match="key schema"):
        selector.validate_selector_receipt_schema(extra)
    float_count={**exact,"replica_count":2.0}
    with pytest.raises(selector.SelectorInvalid,match="exact integer"):
        selector.validate_selector_receipt_schema(float_count)

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


def test_independent_declarative_universe_is_not_a_catalog_row_copy() -> None:
    bundle=synthetic_bundle()
    assert "rows" not in bundle["universe_spec"]
    assert verifier._reconstruct_synthetic_universe(bundle["universe_spec"]) == bundle["catalog"]["rows"]
    wrong=synthetic_bundle(); wrong["universe_spec"]["fixture_id"]="wrong"
    with pytest.raises(verifier.VerificationError,match="universe specification"):
        verifier.verify_synthetic(**wrong)


def test_canonical_universe_recipe_every_field_family_is_exact_without_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(selector,"validate_claim_continuation",lambda *_args:None)
    spec=toy.canonical_universe_spec(authorization(),claim_continuation=object())
    verifier.validate_declarative_universe_spec(spec)
    assert "rows" not in spec
    mutations=[]
    for key in ("universe_id","schema_version","salt","tuple_fields","actions",
                "primary_seeds","checkpoints","derivation"):
        value=copy.deepcopy(spec); value[key]=None; mutations.append(value)
    for pool_index,pool in enumerate(spec["regular_pools"]):
        for key in pool:
            value=copy.deepcopy(spec); value["regular_pools"][pool_index][key]=None
            mutations.append(value)
    for key in spec["final_keep"]:
        value=copy.deepcopy(spec); value["final_keep"][key]=None; mutations.append(value)
    for mutated in mutations:
        with pytest.raises(verifier.VerificationError,match="frozen recipe"):
            verifier.validate_declarative_universe_spec(mutated)
    for path,value in (
        (("schema_version",),True),
        (("final_keep","nonce_start"),False),
        (("final_keep","reset_y"),False),
    ):
        mutated=copy.deepcopy(spec)
        target=mutated
        for key in path[:-1]: target=target[key]
        target[path[-1]]=value
        with pytest.raises(verifier.VerificationError,match="frozen recipe"):
            verifier.validate_declarative_universe_spec(mutated)


def test_fixed_root_exact_once_and_no_alternate_destination_cli(tmp_path: Path) -> None:
    runner=load_runner(); synthetic_root=tmp_path/"one-shot"
    receipt=runner.simulate_fixed_root_claim(synthetic_root)
    assert receipt["synthetic_only"] is True
    marker=json.loads((synthetic_root/"synthetic_namespace_claim.json").read_text(encoding="utf-8"))
    assert marker|{"sweeps":0,"retries":0,"rescues":0,"extra_roots":0} == marker
    with pytest.raises(runner.RunnerInvalid,match="absent"):
        runner.simulate_fixed_root_claim(synthetic_root)
    signature=inspect.signature(runner.orchestrate_stage2)
    assert tuple(signature.parameters)==("stage2_authorization_path",)
    source=inspect.getsource(runner.main)
    for alternate in ("--catalog","--universe","--work-root","--manifest","--result"):
        assert alternate not in source


@pytest.mark.parametrize("failure",(
    "source_map","allowlist","python","ortools","solver_artifact","torch_receipt",
    "live_torch",
))
def test_write_free_readiness_failures_precede_claim_catalog_and_leave_zero_activity(
    failure: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); auth=authorization(); events=[]
    monkeypatch.setattr(runner,"_authorization",lambda _path:auth)
    def step(name: str):
        events.append(name)
        if failure==name:
            raise runner.RunnerInvalid("synthetic readiness rejection: "+name)
    monkeypatch.setattr(runner.selector,"verify_authorized_source_config",lambda *_args:step("source_map"))
    def receipt_step(*_args):
        step("torch_receipt")
        return SOURCE_PATHS[0],full_environment_receipt(SOURCE_PATHS[0])
    monkeypatch.setattr(runner.selector,"load_full_environment_receipt",receipt_step)
    monkeypatch.setattr(runner.selector,"_require_exhaustive_allowlist",lambda *_args:step("allowlist"))
    def environment_step(*_args):
        if failure in {"python","ortools","solver_artifact"}: step(failure)
        else: events.append("environment")
    monkeypatch.setattr(runner.selector,"validate_selector_environment_receipt",environment_step)
    monkeypatch.setattr(runner.experiment,"bind_full_environment",lambda *_args:
        step("live_torch") if failure=="live_torch" else events.append("torch"))
    monkeypatch.setattr(runner.selector,"output_paths_must_be_absent",lambda *_args:events.append("destinations"))
    with pytest.raises(runner.RunnerInvalid,match="synthetic readiness rejection"):
        runner.stage2_readiness(Path("synthetic-authorization.json"))
    assert "claim" not in events and "catalog" not in events
    assert len(auth["zero_start_activity"])==18 and all(value==0 for value in auth["zero_start_activity"].values())
    assert all(not path.exists() for path in runner.RESERVED_PATHS)


def test_external_environment_receipt_anchor_and_exact_schema(tmp_path: Path) -> None:
    artifact=tmp_path/"native.dll"; artifact.write_bytes(b"native")
    receipt_path=tmp_path/"full-environment.json"
    receipt_path.write_text(json.dumps(full_environment_receipt(artifact),sort_keys=True,separators=(",",":")),encoding="utf-8")
    auth=authorization([str(receipt_path.resolve()),str(artifact.resolve())])
    auth["full_environment_receipt_path"]=str(receipt_path.resolve())
    auth["full_environment_receipt_sha256"]=hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    path,loaded=selector.load_full_environment_receipt(auth)
    assert path==receipt_path.resolve() and loaded["torch_distribution_version"]=="2.7.0"
    receipt_path.write_text(receipt_path.read_text(encoding="utf-8")+" ",encoding="utf-8")
    with pytest.raises(selector.SelectorInvalid,match="digest mismatch"):
        selector.load_full_environment_receipt(auth)


def test_exact_claim_schema_capability_and_truthful_terminal_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root=tmp_path/"stage2"; claim=root/"claim.json"; failure=tmp_path/"failure.json"
    auth=authorization([str(claim.resolve()),str(failure.resolve())])
    exact=selector.exact_claim(auth,phase="stage2_selector_continuation")
    monkeypatch.setattr(selector,"stage2_paths",lambda:{"session_root":root,"claim":claim})
    readiness=selector._issue_stage2_readiness_capability(auth,tmp_path/"authorization.json")
    capability=selector.claim_stage2_namespace(auth,readiness_capability=readiness)
    assert capability.selector_consumed is False
    second_readiness=selector._issue_stage2_readiness_capability(auth,tmp_path/"authorization.json")
    with pytest.raises(selector.SelectorInvalid,match="preconstructed"):
        selector.claim_stage2_namespace(auth,readiness_capability=second_readiness)
    for mutation in (None,"phase","ordinal","zero_start_activity"):
        bad=copy.deepcopy(exact)
        if mutation is None: bad.pop("phase")
        elif mutation=="phase": bad["phase"]="wrong"
        elif mutation=="ordinal": bad["ordinal"]=True
        else: bad["zero_start_activity"]["replicas"]=1
        with pytest.raises(selector.SelectorInvalid,match="claim"):
            selector.validate_exact_claim(bad,auth,phase="stage2_selector_continuation")
    runner=load_runner(); activity=dict(toy.ACTIVITY_COUNTERS)
    activity["canonical_generator_calls"]=1; activity["canonical_rows_observed"]=7
    terminal=runner._terminal_failure(auth,RuntimeError("injected post-claim failure"),activity,failure_path=failure)
    assert terminal["branch"]=="B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
    assert terminal["activity_counts"]["canonical_rows_observed"]==7
    assert selector.INVALID not in json.dumps(terminal)
    selector._ACTIVE_CLAIM_CONTINUATION=None
    selector._ACTIVE_READINESS_CAPABILITY=None


@pytest.mark.parametrize("phase",("catalog","replica","verifier"))
def test_injected_postclaim_failures_have_one_terminal_branch_and_truthful_counters(
    phase: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/phase
    paths={
        "session_root":root,"claim":root/"claim.json",
        "universe_spec":root/"universe.json","catalog":root/"catalog.json",
        "stage2_failure":root/"failure.json",
    }
    auth=authorization([str(paths["claim"].resolve()),str(paths["stage2_failure"].resolve())])
    monkeypatch.setattr(runner,"_preclaim_readiness",lambda _path:(auth,{},object()))
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    def claim(_authorization: object,_readiness: object,on_claim_created: object):
        root.mkdir()
        exact=selector.exact_claim(auth,phase="stage2_selector_continuation")
        selector.write_exclusive(paths["claim"],json.dumps(exact,sort_keys=True,separators=(",",":")).encode()+b"\n")
        on_claim_created()
        return object(),dict(toy.ACTIVITY_COUNTERS)
    monkeypatch.setattr(runner,"_claim_fixed_stage2_namespace",claim)
    monkeypatch.setattr(runner.experiment,"canonical_universe_spec",lambda _authorization,**_kwargs:{"synthetic_only":True})
    monkeypatch.setattr(runner.selector,"begin_catalog_generation",lambda *_args:object())
    def rows(_authorization: object,**_kwargs: object):
        yield row()
        if phase=="catalog": raise RuntimeError("injected catalog failure")
    monkeypatch.setattr(runner.experiment,"canonical_catalog_rows",rows)
    monkeypatch.setattr(runner.selector,"parse_catalog",lambda _catalog:None)
    monkeypatch.setattr(runner.selector,"persist_activity_snapshot",lambda *_args:None)
    monkeypatch.setattr(runner.selector,"validate_pre_replica_catalog_snapshot",lambda *_args:None)
    def sequence(**kwargs: object):
        activity=kwargs["activity_counts"]
        if phase in {"replica","verifier"}:
            activity["canonical_ortools_processes"]=2 if phase=="verifier" else 1
            activity["replicas"]=2 if phase=="verifier" else 1
        if phase=="verifier": activity["canonical_verifier_admissions"]=1
        raise RuntimeError("injected "+phase+" failure")
    monkeypatch.setattr(runner.selector,"run_two_replica_sequence",sequence)
    result=runner.orchestrate_stage2(Path("synthetic-authorization.json"))
    assert result["branch"]=="B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
    assert selector.INVALID not in json.dumps(result)
    assert result["activity_counts"]["canonical_generator_calls"]==1
    if phase=="catalog": assert result["activity_counts"]["canonical_rows_observed"]==1
    if phase in {"replica","verifier"}: assert result["activity_counts"]["replicas"]>=1
    if phase=="verifier": assert result["activity_counts"]["canonical_verifier_admissions"]==1


def test_complete_secure_read_set_covers_environment_claim_checkpoints_result_and_failures() -> None:
    paths=selector.stage2_paths()
    schema=selector._sealed_path_schema(
        paths,authorization_path=SOURCE_PATHS[0],authorization=authorization()
    )
    assert {"stage2_authorization","full_environment_receipt","claim","full_claim",
            "result","stage2_failure","full_failure"}.issubset(schema)
    assert len([name for name in schema if name.startswith("checkpoint_")])==64
    assert {"activity_full_claim","activity_full_calibration","activity_full_primary_1",
            "activity_full_primary_2","activity_full_primary_3","activity_full_primary_4",
            "activity_full_complete"}.issubset(schema)
    assert "authorized_read_bytes" in inspect.getsource(toy._reload_checkpoint)
    assert "authorized_json" in inspect.getsource(toy.run_registered_full)
    assert "authorized_read_bytes" in inspect.getsource(selector.load_full_environment_receipt)


@pytest.mark.parametrize("mode",("mutated","unreadable"))
def test_postclaim_mutated_or_unreadable_claim_cannot_escape_terminal_branch(
    mode: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/mode
    paths={"session_root":root,"claim":root/"claim.json",
           "stage2_failure":root/"failure.json"}
    auth=authorization([str(paths["claim"].resolve()),str(paths["stage2_failure"].resolve())])
    monkeypatch.setattr(runner,"_preclaim_readiness",lambda _path:(auth,{},object()))
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    def claim(_authorization: object,_readiness: object,on_claim_created: object):
        root.mkdir(); exact=selector.exact_claim(auth,phase="stage2_selector_continuation")
        selector.write_exclusive(paths["claim"],json.dumps(exact,sort_keys=True,separators=(",",":")).encode()+b"\n")
        on_claim_created()
        return object(),dict(toy.ACTIVITY_COUNTERS)
    monkeypatch.setattr(runner,"_claim_fixed_stage2_namespace",claim)
    monkeypatch.setattr(runner.selector,"persist_activity_snapshot",lambda *_args:None)
    original_authorized=selector.authorized_json
    if mode=="unreadable":
        monkeypatch.setattr(runner.selector,"authorized_json",lambda auth_value,path:
            (_ for _ in ()).throw(selector.SelectorInvalid("unreadable claim"))
            if path==paths["claim"] else original_authorized(auth_value,path))
    def fail_universe(_authorization: object,**_kwargs: object):
        if mode=="mutated":
            paths["claim"].chmod(0o666); paths["claim"].write_text("{mutated",encoding="utf-8")
            original_authorized(auth,paths["claim"])
        runner.selector.authorized_json(auth,paths["claim"])
        raise AssertionError("unreachable")
    monkeypatch.setattr(runner.experiment,"canonical_universe_spec",fail_universe)
    result=runner.orchestrate_stage2(Path("synthetic-authorization.json"))
    assert result["branch"]=="B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
    assert set(result["activity_counts"])==set(toy.ACTIVITY_COUNTERS)
    assert selector.INVALID not in json.dumps(result)


def test_claim_created_then_immediate_secure_reread_failure_is_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/"claim-reread"
    paths={"session_root":root,"claim":root/"claim.json",
           "stage2_failure":root/"failure.json"}
    auth=authorization([str(paths["claim"].resolve()),str(paths["stage2_failure"].resolve())])
    capability=selector._issue_stage2_readiness_capability(auth,tmp_path/"authorization.json")
    monkeypatch.setattr(runner,"_preclaim_readiness",lambda _path:(auth,{},capability))
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    original_authorized=selector.authorized_json
    monkeypatch.setattr(runner.selector,"authorized_json",lambda auth_value,path:
        (_ for _ in ()).throw(selector.SelectorInvalid("injected immediate claim reread failure"))
        if path==paths["claim"] else original_authorized(auth_value,path))
    result=runner.orchestrate_stage2(tmp_path/"authorization.json")
    assert result["branch"]=="B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
    assert root.is_dir() and paths["claim"].is_file()
    assert set(result["activity_counts"])==set(toy.ACTIVITY_COUNTERS)
    assert selector.INVALID not in json.dumps(result)


@pytest.mark.parametrize("durable_nonzero",(False,True))
def test_later_stage2_seal_with_prior_exact_claim_is_process_independent_terminal(
    durable_nonzero: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/("nonzero" if durable_nonzero else "zero")
    phases=("claim","catalog","replica_1","replica_2","witness","verifier","manifest")
    paths={"session_root":root,"claim":root/"claim.json",
           "stage2_failure":root/"failure.json"}
    paths.update({f"activity_{phase}":root/f"activity_{phase}.json" for phase in phases})
    allowlist=[str(path.resolve()) for name,path in paths.items() if name!="session_root"]
    auth=authorization(allowlist)
    root.mkdir()
    selector.write_exclusive(paths["claim"],json.dumps(
        selector.exact_claim(auth,phase="stage2_selector_continuation"),
        sort_keys=True,separators=(",",":")).encode()+b"\n")
    zero=dict(toy.ACTIVITY_COUNTERS)
    selector.write_exclusive(paths["activity_claim"],json.dumps(
        {"phase":"claim","activity_counts":zero},sort_keys=True,
        separators=(",",":")).encode()+b"\n")
    if durable_nonzero:
        nonzero=dict(zero); nonzero["canonical_generator_calls"]=1
        selector.write_exclusive(paths["activity_catalog"],json.dumps(
            {"phase":"catalog","activity_counts":nonzero},sort_keys=True,
            separators=(",",":")).encode()+b"\n")
    monkeypatch.setattr(runner,"_authorization",lambda _path:auth)
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    monkeypatch.setattr(runner,"_preclaim_readiness",lambda _path:
        pytest.fail("existing lifecycle must terminalize before readiness/replay"))
    result=runner.orchestrate_stage2(tmp_path/"authorization.json")
    assert result["branch"]=="B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
    assert result["activity_counts"]["canonical_generator_calls"]==int(durable_nonzero)
    assert result["retry_authorized"] is result["rescue_authorized"] is False
    assert paths["stage2_failure"].is_file()


@pytest.mark.parametrize("claim_mode",("malformed","missing"))
def test_malformed_or_missing_claim_with_zero_snapshot_is_terminal_no_retry(
    claim_mode: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/"malformed"; root.mkdir()
    phases=("claim","catalog","replica_1","replica_2","witness","verifier","manifest")
    paths={"session_root":root,"claim":root/"claim.json",
           "stage2_failure":root/"failure.json"}
    paths.update({f"activity_{phase}":root/f"activity_{phase}.json" for phase in phases})
    if claim_mode=="malformed":
        paths["claim"].write_text("{malformed",encoding="utf-8")
    zero=dict(toy.ACTIVITY_COUNTERS)
    paths["activity_claim"].write_text(json.dumps(
        {"phase":"claim","activity_counts":zero},sort_keys=True,separators=(",",":"),
    ),encoding="utf-8")
    allowlist=[str(path.resolve()) for name,path in paths.items() if name!="session_root"]
    auth=authorization(allowlist)
    monkeypatch.setattr(runner,"_authorization",lambda _path:auth)
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    monkeypatch.setattr(runner,"_preclaim_readiness",lambda _path:
        pytest.fail("malformed root must be classified before readiness"))
    result=runner.orchestrate_stage2(tmp_path/"authorization.json")
    assert result["branch"]=="B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
    assert result["activity_counts"]==zero
    assert result["retry_authorized"] is result["rescue_authorized"] is False


def test_run_full_missing_claim_is_technical_no_start_without_created_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/"absent-stage2"
    paths={"session_root":root,"claim":root/"claim.json","stage2_failure":root/"failure.json"}
    monkeypatch.setattr(runner,"_authorization",lambda _path:
        pytest.fail("missing-claim no-start must precede authorization reads"))
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    with pytest.raises(runner.RunnerInvalid,match="technical no-start"):
        runner.run_full(Path("synthetic-authorization.json"),"0"*64)
    assert not root.exists() and not paths["stage2_failure"].exists()


def test_cross_process_recovery_reads_all_full_phases_monotonically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/"full-recovery"; root.mkdir()
    phases=("claim","catalog","replica_1","replica_2","witness","verifier",
            "manifest","full_claim","full_calibration","full_primary_1",
            "full_primary_2","full_primary_3","full_primary_4","full_complete")
    paths={f"activity_{phase}":root/f"{phase}.json" for phase in phases}
    allowlist=[str(path.resolve()) for path in paths.values()]
    auth=authorization(allowlist)
    counts=dict(toy.ACTIVITY_COUNTERS)
    for index,phase in enumerate(phases):
        if phase.startswith("full_primary_"):
            counts["model_fits"]=index
        selector.write_exclusive(paths[f"activity_{phase}"],selector._canonical_json_bytes(
            {"phase":phase,"activity_counts":counts}
        )+b"\n")
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    recovered=runner._latest_stage2_activity(auth)
    assert recovered["model_fits"]==phases.index("full_primary_4")


@pytest.mark.parametrize("failure_name",("stage2_failure","full_failure"))
def test_existing_terminal_failure_blocks_full_even_with_selector_receipt(
    failure_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/"terminal"; root.mkdir()
    failure_path=root/f"{failure_name}.json"; receipt_path=root/"selector-receipt.json"
    claim_path=root/"claim.json"
    paths={"session_root":root,"claim":claim_path,
           "stage2_failure":root/"stage2-failure.json",
           "full_failure":root/"full-failure.json","receipt":receipt_path}
    paths[failure_name]=failure_path
    auth=authorization([str(failure_path.resolve()),str(receipt_path.resolve())])
    failure={"branch":"B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY",
             "error_type":"RuntimeError","error":"terminal",
             "activity_counts":dict(toy.ACTIVITY_COUNTERS),
             "retry_authorized":False,"rescue_authorized":False,
             "sweeps":0,"retries":0,"rescues":0,"extra_roots":0}
    selector.write_exclusive(failure_path,selector._canonical_json_bytes(failure)+b"\n")
    selector.write_exclusive(receipt_path,selector._canonical_json_bytes(selector_receipt())+b"\n")
    monkeypatch.setattr(runner,"_authorization",lambda _path:auth)
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    monkeypatch.setattr(runner.experiment,"run_registered_full",lambda **_kwargs:
        pytest.fail("terminal receipt must block the full"))
    returned=runner.run_full(tmp_path/"authorization.json",hashlib.sha256(receipt_path.read_bytes()).hexdigest())
    assert returned==failure
    assert failure_path.read_bytes()==selector._canonical_json_bytes(failure)+b"\n"


def test_verified_json_reload_rejects_result_type_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    result_path=tmp_path/"result.json"
    auth=authorization([str(result_path.resolve())])
    monkeypatch.setattr(selector,"authorized_read_bytes",lambda *_args:b'{"count":1.0}\n')
    with pytest.raises(selector.SelectorInvalid,match="raw-byte reload mismatch"):
        selector.write_json_exclusive_verified(auth,result_path,{"count":1})


def test_absent_destination_rejects_dangling_and_reparse_locators(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    dangling=tmp_path/"dangling-result.json"
    real_lexists=selector.path_lexists
    monkeypatch.setattr(selector,"path_lexists",lambda path:
        True if Path(path)==dangling else real_lexists(Path(path)))
    monkeypatch.setattr(selector,"_is_reparse",lambda path:Path(path)==dangling)
    with pytest.raises(selector.SelectorInvalid,match="dangling/link/junction/reparse"):
        selector.validate_absent_destination(dangling)
    monkeypatch.undo()
    junction=tmp_path/"junction"; junction.mkdir(); destination=junction/"result.json"
    monkeypatch.setattr(selector,"_is_reparse",lambda path:Path(path)==junction)
    with pytest.raises(selector.SelectorInvalid,match="link/junction/reparse"):
        selector.validate_absent_destination(destination)


def test_direct_claim_catalog_and_solve_apis_require_opaque_capabilities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root=tmp_path/"direct"; claim=root/"claim.json"
    auth=authorization([str(claim.resolve())])
    monkeypatch.setattr(selector,"stage2_paths",lambda:{"session_root":root,"claim":claim})
    with pytest.raises(selector.SelectorInvalid,match="readiness"):
        selector.claim_stage2_namespace(auth,readiness_capability=object())
    assert not root.exists()
    with pytest.raises(selector.SelectorInvalid,match="claim continuation"):
        toy.canonical_universe_spec(auth,claim_continuation=object())
    with pytest.raises(selector.SelectorInvalid,match="scoped claim"):
        next(toy.canonical_catalog_rows(auth,catalog_capability=object()))
    with pytest.raises(selector.SelectorInvalid,match="scoped claim"):
        next(toy.canonical_final_keep_rows("primary_1",auth,catalog_capability=object()))
    forged_catalog_capability=selector._CatalogGenerationCapability(
        selector.sha256_bytes(selector._canonical_json_bytes(auth)),"0"*64
    )
    with pytest.raises(selector.SelectorInvalid,match="scoped claim"):
        next(toy.canonical_catalog_rows(
            auth,catalog_capability=forged_catalog_capability
        ))
    root.mkdir(); selector.write_exclusive(claim,json.dumps(
        selector.exact_claim(auth,phase="stage2_selector_continuation"),
        sort_keys=True,separators=(",",":")).encode()+b"\n")
    with pytest.raises(selector.SelectorInvalid,match="start token"):
        selector.solve_replica(
            tmp_path/"never-catalog.json",tmp_path/"never-ledger.json",
            tmp_path/"never-bindings.json",auth,claim_path=claim,
            start_capability=object(),
        )


def test_catalog_capability_is_consumed_by_one_iteration_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth=authorization()
    capability=selector._CatalogGenerationCapability(
        selector.sha256_bytes(selector._canonical_json_bytes(auth)),"0"*64
    )
    selector._ACTIVE_CATALOG_GENERATION_CAPABILITY=capability
    monkeypatch.setattr(toy,"_canonical_catalog_rows_iter",lambda *_args,**_kwargs:iter(()))
    try:
        assert list(toy.canonical_catalog_rows(auth,catalog_capability=capability))==[]
        with pytest.raises(selector.SelectorInvalid,match="scoped claim"):
            toy.canonical_catalog_rows(auth,catalog_capability=capability)
    finally:
        selector._ACTIVE_CATALOG_GENERATION_CAPABILITY=None


def test_catalog_attempt_is_counted_before_pre_yield_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner=load_runner(); root=tmp_path/"pre-yield"
    paths={"session_root":root,"claim":root/"claim.json",
           "universe_spec":root/"universe.json","catalog":root/"catalog.json",
           "stage2_failure":root/"failure.json"}
    auth=authorization([str(paths["claim"].resolve()),str(paths["stage2_failure"].resolve())])
    monkeypatch.setattr(runner,"_preclaim_readiness",lambda _path:(auth,{},object()))
    monkeypatch.setattr(runner.selector,"stage2_paths",lambda:paths)
    def claim(_authorization: object,_readiness: object,on_claim_created: object):
        root.mkdir(); paths["claim"].write_text("{}",encoding="utf-8")
        on_claim_created(); return object(),dict(toy.ACTIVITY_COUNTERS)
    monkeypatch.setattr(runner,"_claim_fixed_stage2_namespace",claim)
    monkeypatch.setattr(runner.selector,"persist_activity_snapshot",lambda *_args:None)
    monkeypatch.setattr(runner.experiment,"canonical_universe_spec",lambda *_args,**_kwargs:{})
    monkeypatch.setattr(runner.selector,"begin_catalog_generation",lambda *_args:object())
    def fail_before_generator_return(*_args: object,**_kwargs: object):
        raise RuntimeError("injected pre-yield failure")
    monkeypatch.setattr(runner.experiment,"canonical_catalog_rows",fail_before_generator_return)
    result=runner.orchestrate_stage2(tmp_path/"authorization.json")
    assert result["branch"]=="B2R1_REGISTERED_FULL_TERMINAL_FAILURE_NO_RETRY"
    assert result["activity_counts"]["canonical_generator_calls"]==1
    assert result["activity_counts"]["canonical_rows_observed"]==0


def test_pre_replica_catalog_snapshot_rejects_forged_activity(
    tmp_path: Path,
) -> None:
    catalog_path=tmp_path/"catalog.json"; activity_path=tmp_path/"activity.json"
    paths={"catalog":catalog_path,"activity_catalog":activity_path}
    auth=authorization([str(catalog_path.resolve()),str(activity_path.resolve())])
    catalog={"catalog_id":selector.CATALOG_ID,"salt":selector.SALT,"rows":[row()]}
    forged=dict(toy.ACTIVITY_COUNTERS)
    forged["canonical_generator_calls"]=1
    forged["canonical_rows_observed"]=2
    selector.write_exclusive(catalog_path,json.dumps(
        catalog,sort_keys=False,separators=(",",":"),ensure_ascii=False
    ).encode()+b"\n")
    selector.write_exclusive(activity_path,selector._canonical_json_bytes(
        {"phase":"catalog","activity_counts":forged}
    )+b"\n")
    with pytest.raises(selector.SelectorInvalid,match="cardinality proof"):
        selector.validate_pre_replica_catalog_snapshot(auth,paths,catalog,forged)


def test_replica_cli_has_no_optional_start_token_bypass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth_path=tmp_path/"authorization.json"; claim=tmp_path/"claim.json"
    output=tmp_path/"replica.json"
    auth=authorization([str(auth_path.resolve()),str(claim.resolve()),str(output.resolve())])
    auth_path.write_text(json.dumps(auth),encoding="utf-8")
    selector.write_exclusive(claim,json.dumps(
        selector.exact_claim(auth,phase="stage2_selector_continuation"),
        sort_keys=True,separators=(",",":")).encode()+b"\n")
    monkeypatch.setattr(selector,"stage2_paths",lambda:{"claim":claim,"replica_1":output,"replica_2":tmp_path/"replica2.json"})
    monkeypatch.setattr(selector,"_self_memory_cap",lambda:None)
    class EmptyInput: buffer=io.BytesIO(b"")
    monkeypatch.setattr(selector.sys,"stdin",EmptyInput())
    monkeypatch.setattr(selector,"solve_replica",lambda *_args,**_kwargs:pytest.fail("solve reached without token"))
    args=argparse.Namespace(stage2_authorization=str(auth_path),output=str(output.resolve()),
        catalog="never",ledger="never",bindings="never")
    with pytest.raises(selector.SelectorInvalid,match="mandatory start-token"):
        selector._replica_cli(args)
    assert "await_start_token" not in inspect.getsource(selector._replica_cli)
    assert "--await-start-token" not in inspect.getsource(selector.main)


def test_failed_replica_popen_does_not_preincrement_activity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    events=[]
    monkeypatch.setattr(selector.subprocess,"Popen",lambda *_args,**_kwargs:
        (_ for _ in ()).throw(OSError("injected Popen failure")))
    with pytest.raises(OSError,match="Popen failure"):
        selector._run_cold_replica(
            selector_path=tmp_path/"selector.py",catalog_path=tmp_path/"catalog.json",
            ledger_path=tmp_path/"ledger.json",bindings_path=tmp_path/"bindings.json",
            output_path=tmp_path/"output.json",authorization_path=tmp_path/"authorization.json",
            authorization=authorization(),on_process_started=lambda:events.append("started"),
        )
    assert events==[]


def test_mid_ppo_failure_preserves_actual_partial_optimizer_progress() -> None:
    scientific=toy._activity_template(); lifecycle=dict(toy.ACTIVITY_COUNTERS)
    class FailingOptimizer:
        calls=0
        def step(self):
            self.calls+=1
            if self.calls==2: raise RuntimeError("injected mid-PPO failure")
    optimizer=FailingOptimizer()
    toy._optimizer_step_with_accounting(optimizer,scientific,lifecycle)
    with pytest.raises(RuntimeError,match="mid-PPO"):
        toy._optimizer_step_with_accounting(optimizer,scientific,lifecycle)
    assert scientific["optimizer_steps"]==scientific["learner_updates"]==1
    assert lifecycle["optimizer_steps"]==lifecycle["learner_updates"]==1
    assert set(lifecycle)==set(toy.ACTIVITY_COUNTERS)


@pytest.mark.parametrize("mode",("mutation","alias","reparse"))
def test_first_checkpoint_digest_uses_secure_reader_and_rejects_unsafe_paths(
    mode: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeTorch:
        @staticmethod
        def save(_payload: object,stream: object): stream.write(b"checkpoint")
    class FakeModel:
        @staticmethod
        def state_dict(): return {"x":1}
    monkeypatch.setattr(toy,"_torch",lambda:FakeTorch())
    if mode=="alias":
        (tmp_path/"sub").mkdir(); path=tmp_path/"sub"/".."/"alias.pt"
    elif mode=="reparse":
        (tmp_path/"junction").mkdir(); path=tmp_path/"junction"/"checkpoint.pt"
        monkeypatch.setattr(selector,"_is_reparse",lambda candidate:candidate.name=="junction")
    else: path=tmp_path/"mutation.pt"
    auth=authorization([str(path)])
    if mode=="mutation":
        monkeypatch.setattr(selector,"authorized_read_bytes",lambda *_args:
            (_ for _ in ()).throw(selector.SelectorInvalid("changed during secure read")))
    with pytest.raises(selector.SelectorInvalid):
        toy._write_checkpoint(path,FakeModel(),{},auth)

def episode_spec(branch: str) -> toy.EpisodeSpec:
    value=row(2,0,"q",branch); value.update({"consumer":"synthetic_only","seed_row":"synthetic",
        "target_identity":1,"target_version":1,"reset_y":3,"roster":"P0,P1,P2,P3,focal",
        "decoy_sequence":[[0,0,1,False],[1,1,2,False],[2,2,3,False],[3,3,0,False]]})
    return toy.EpisodeSpec.from_manifest_row(value)

@pytest.mark.parametrize("branch,target,write,reset",[("KEEP",2,0,0),("RESET",3,1,1),("CURRENT",2,1,0)])
def test_pure_keep_reset_current_semantics_without_training(branch: str,target: int,write:int,reset:int) -> None:
    actual_target,actual_write,actual_reset,_payload=toy.branch_terminal_contract(episode_spec(branch))
    assert actual_target==target and actual_write==write and actual_reset==reset
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


def test_selected_p_cross_swap_is_payload_only_and_action_rng_paired() -> None:
    values=[]
    for y in range(4):
        value=row(y,y,"quartet","KEEP")
        value.update({"consumer":"final_keep","seed_row":"primary_1","panel":"4096_keep_extra",
            "target_identity":3,"target_version":2,"reset_y":0,
            "roster":"P0,P1,P2,P3,focal",
            "decoy_sequence":[[0,0,1,False],[1,1,2,False],[2,2,3,False],[3,3,0,False]],
            "current_bytes":"fixed-context","rng_binding":"fixed-routing"})
        values.append(toy.EpisodeSpec.from_manifest_row(value))
    plan=toy.selected_p_cross_swap_plan(values,expected_quartets=1)
    assert [item["destination_index"] for item in plan]==[0,1,2,3]
    assert [item["swapped_payload"] for item in plan]==[1,2,3,0]
    assert all(values[int(item["destination_index"])].target_identity==3 for item in plan)
    toy.validate_payload_only_cross_swap(values,values,[1,2,3,0],expected_quartets=1)
    with pytest.raises(toy.B2ContractError,match="co-permuted"):
        toy.validate_payload_only_cross_swap(values,values[1:]+values[:1],[1,2,3,0],expected_quartets=1)
    seeds=toy.paired_control_action_seeds("primary_1")
    assert set(seeds)=={"baseline","selected_p_zero","cross_swap","decoy_accuracy_delta"}
    assert len(set(seeds.values()))==1
    controls=inspect.getsource(toy._controls)
    assert "cross_observations[:, 1, 16:20]" in controls
    assert "cross_writes = writes" in controls and "cross_resets = resets" in controls

def test_future_implementations_are_complete_not_stubs() -> None:
    assert "CpModel" in inspect.getsource(selector.solve_replica)
    assert "Popen" in inspect.getsource(selector._run_cold_replica)
    assert "for replica_index in (1, 2)" in inspect.getsource(selector.run_two_replica_sequence)
    assert "optimizer" in inspect.getsource(toy.run_registered_full)
    assert "yield" in inspect.getsource(toy._canonical_catalog_rows_iter)
    assert toy.CAPS == {"model_fits":10,"trainer_invocations":10,"environment_episodes":44300,
        "environment_transitions":520000,"production_policy_forwards":540000,"learner_updates":1100,
        "optimizer_steps":1100,"evaluator_calls":75,"evaluation_episodes":10500,
        "sweeps":0,"retries":0,"rescues":0,"extra_roots":0}
    assert toy.EXPECTED_FULL_ACTIVITY["model_fits"] == 10 and len(toy.SEEDS) == 5
    assert all(toy.EXPECTED_FULL_ACTIVITY[name]==0 for name in ("sweeps","retries","rescues","extra_roots"))
    missing=dict(toy.EXPECTED_FULL_ACTIVITY); missing.pop("sweeps")
    assert toy._caps_valid(missing) is False


def test_complete_seal_and_nonreplayable_admission_are_explicit() -> None:
    assert len(selector.SOURCE_CONFIG_RELATIVE_PATHS)==7
    assert set(selector.SOURCE_CONFIG_RELATIVE_PATHS)==set(verifier.SOURCE_CONFIG_RELATIVE_PATHS)
    selector_source=inspect.getsource(selector.run_two_replica_sequence)
    for literal in ("source_config_digest_map","sealed_objects","universe_spec_sha256",
                    "stage2_authorization_sha256","python_executable_sha256","solver_artifacts"):
        assert literal in selector_source
    gate_source=inspect.getsource(toy.ManifestGate)
    assert 'receipt.get("final_commit") != stage2_authorization["final_commit"]' in gate_source
    assert 'receipt.get("stage2_authorization_sha256") != authorization_digest' in gate_source
    assert "sealed_objects" in gate_source and "authorize_read_path" in gate_source
    for read_source in (inspect.getsource(selector.authorized_read_bytes),inspect.getsource(verifier._authorized_bytes)):
        assert read_source.count("authorize_read_path")>=2
        assert "O_NOFOLLOW" in read_source and "fstat" in read_source

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

@pytest.mark.parametrize("field",("contract_valid","activity_nonzero","caps_valid","paired_exposure"))
def test_completed_contract_activity_cap_or_provenance_violation_is_first_invalid_branch(field: str) -> None:
    evidence=passing(); evidence[field]=False
    assert toy.classify_result(evidence)=="B2R1_INVALID_CONTRACT_ACTIVITY_CAP_OR_PROVENANCE"

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
