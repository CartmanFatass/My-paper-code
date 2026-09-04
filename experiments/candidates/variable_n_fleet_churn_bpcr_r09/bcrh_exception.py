"""Zero-coordinate nonprecedential BCRH reference/complexity certificate."""
from __future__ import annotations
import hashlib
from .contracts import CARD_SHA256,PUBLIC_LAW_SHA256,canonical_json_bytes

def exception_certificate()->dict[str,object]:
    return {"schema":"VNFC_BPCR_R09_BCRH_REFERENCE_EXCEPTION_V1","materialized_coordinates":0,"nonprecedential":True,"card_sha256":CARD_SHA256,"public_law_sha256":PUBLIC_LAW_SHA256,"candidate_ceiling_per_boundary":1961,"real_boundaries":6,"tail":{"commands_per_candidate":1,"deterministic":True,"nonbranching":True,"persistent":True,"recursive":False,"nested":False,"tree_search":False},"implementations":["scorer","independent_checker"],"operations_per_decision_ceiling":4415000,"total_logical_operations_ceiling":27715520000,"storage":{"candidate_record_bytes":120,"candidate_records_per_batch_item_ceiling":1961,"encoding":"little-endian fixed-width","compression":"zlib-9/wbits15/no-dictionary","hash":"SHA-256 over canonical uncompressed bytes"},"cost":{"engineer_days":[24,38],"cpu_core_hours":[200,1500],"compute_days":[2,8],"retained_gib":[8,30],"scratch_gib":[20,60]},"changes_science":False,"grants_activity":False}

def exception_certificate_digest()->str:return hashlib.sha256(canonical_json_bytes(exception_certificate())).hexdigest()
