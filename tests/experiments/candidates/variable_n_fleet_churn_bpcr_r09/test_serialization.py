from experiments.candidates.variable_n_fleet_churn_bpcr_r09.fixtures import deterministic_general_bcrh
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import run_native_bcrh_batch
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.serialization import decode_bcrh_records,encode_bcrh_records,storage_contract


def test_every_bcrh_comparison_has_canonical_compact_roundtrip() -> None:
    records=run_native_bcrh_batch((deterministic_general_bcrh(0),),include_candidate_records=True)[0]["candidate_records"]
    packet=encode_bcrh_records(records);decoded=decode_bcrh_records(packet)
    assert decoded==records
    contract=storage_contract()
    assert contract["bcrh_candidate_record_bytes"]==108
    assert contract["maximum_candidate_record_bytes"]==1_301_400_000
