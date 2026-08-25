from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from envs.native.production_backend import (
    ProductionBackendUnsupported,
    VQFP_VNPA_R03_FULL_CHAIN,
    backend_capability,
    require_cpp_batched_production,
)
from experiments.candidates.vqfp_vnpa_r03.contract import EXACT_REVISION, SCIENCE_CARD_SHA256
from experiments.candidates.vqfp_vnpa_r03.contract import validate_cost_collapse_limits
from experiments.candidates.vqfp_vnpa_r03.lifecycle import (
    COMPETENCE_FIELDS, LifecycleError, PrivateGeneration, WorkRange, input_identity,
)
from experiments.candidates.vqfp_vnpa_r03.native_backend import (
    NativeBackendError, addressed_uniform, artifact_identity,
    canonical_resample_position, encode_address, exact_rational_binary,
    fixture_audit, geometry_offsets, injected_rejection, little_endian_u32,
    markov_next, philox_words, production_execute_guard, synthetic_benchmark,
    cost_collapse_slice,
)
from experiments.candidates.vqfp_vnpa_r03.reference_oracle import (
    _geometry as reference_geometry, fixture_audit as reference_fixture_audit, philox as reference_philox,
    uniform as reference_uniform,
    stage_literal_audit,
)


def test_published_philox_zero_vector_and_independent_reference():
    assert philox_words(0,(0,0,0,0)) == (0x6627E8D5,0xE169C58D,0xBC57AC4C,0x9B00DBD8)
    cases=[(202608230200,(0,1,2,0x01000000)),(202608232004,(7,31,4,0x21000000)),(202608239999,(0,19999,47,0x410000FF))]
    for root,counter in cases:assert philox_words(root,counter)==reference_philox(root,counter)


@pytest.mark.parametrize("root,c1,c2,c3,m",[
    (202608230200,1,0,0x01000000,129),(202608230201,2047,3,0x02000000,129),
    (202608231004,31,4,0x10000003,5),(202608231004,31,31,0x11000000,10),
    (202608232008,127,8,0x20000007,5),(202608232008,127,31,0x21000000,10),
    (202608239012,511,9,0x3000000B,5),(202608239012,511,31,0x31000000,10),
    (202608239999,19999,11,0x40000000,12),(202608239999,19999,143,0x41000055,86),
])
def test_all_ten_address_families(root,c1,c2,c3,m):
    assert addressed_uniform(root,c1,c2,c3,m)==reference_uniform(root,c1,c2,c3,m)


def test_numeric_root_collision_is_separated_by_purpose_family():
    root=202608232004
    assert philox_words(root,(0,0,0,0x10000000)) != philox_words(root,(0,0,0,0x20000000))


def test_rejection_address_widths_fail_before_counter_wrap():
    with pytest.raises(ValueError,match="wrap c0"):
        addressed_uniform(0,0,0,0,5,max_rho=1<<34)
    with pytest.raises(ValueError,match="counter word"):
        addressed_uniform(0,1<<32,0,0,5)
    with pytest.raises(ValueError,match="target size"):
        addressed_uniform(0,0,0,0,1<<32)


def test_literal_ten_family_encoders_and_field_packing():
    assert encode_address("treatment",1,3)==(202608230200,1,3,0x01000000,129)
    assert encode_address("free",2047,0)==(202608230201,2047,0,0x02000000,129)
    assert encode_address("development_geometry",10,4,31,7,3)==(202608232004,31,7,0x10000003,5)
    assert encode_address("development_markov",10,4,31,19)==(202608232004,31,19,0x11000000,10)
    assert encode_address("validation_geometry",0,4,127,9,3)==(202608232004,127,9,0x20000003,5)
    assert encode_address("validation_markov",0,4,127,31)==(202608232004,127,31,0x21000000,10)
    assert encode_address("evaluation_geometry",11,12,511,13,11)==(202608240112,511,13,0x3000000B,5)
    assert encode_address("evaluation_markov",11,12,511,1)==(202608240112,511,1,0x31000000,10)
    assert encode_address("bootstrap_block",19999,11)==(202608239999,19999,11,0x40000000,12)
    assert encode_address("bootstrap_episode",19999,11,12,5,85)==(202608239999,19999,287,0x41000055,0)
    with pytest.raises(ValueError):encode_address("treatment",0,0)


def test_rejection_lane_advance_exhaustion_markov_resample_and_little_endian():
    assert injected_rejection(m=129,max_rho=8,forced_rejections=5,accepted_word=17)==(5,1,1)
    with pytest.raises(NativeBackendError,match="RNG_ADDRESS_EXHAUSTED"):
        injected_rejection(m=3,max_rho=7,forced_rejections=8,accepted_word=0)
    with pytest.raises(NativeBackendError,match="RNG_ADDRESS_EXHAUSTED"):
        injected_rejection(m=3,max_rho=7,forced_rejections=0,accepted_word=(1<<32)-1)
    for current in range(6):
        expected=[current]*5+[state for state in range(6) if state!=current]
        assert [markov_next(current,draw) for draw in range(10)]==expected
    counts=(86,86,85,85,85,85)
    assert canonical_resample_position(0,0,counts)==0
    assert canonical_resample_position(84,5,counts)==511
    assert little_endian_u32(0x12345678)==b"\x78\x56\x34\x12"


def _reference_geometry(purpose:str,block:int,roster:int,episode:int):
    family={"development":("development_geometry",0x10000000,202608231000),
            "validation":("validation_geometry",0x20000000,202608232000),
            "evaluation":("evaluation_geometry",0x30000000,202608239000)}[purpose]
    for outer in range(64):
        offsets=[]
        for i0 in range(roster):
            root=family[2]+100*block+roster
            value,_=reference_uniform(root,episode,outer,family[1]+i0,5)
            offsets.append(-48+24*value)
        _,_,_,v=reference_geometry(tuple(offsets))
        if max(v)-min(v)>=Fraction(1,64*roster):return tuple(offsets),outer
    raise AssertionError("reference fixture unexpectedly exhausted")


def test_complete_vector_geometry_attempt_and_bounded_exhaustion_seams():
    for cell in (("development",10,4,31),("validation",0,4,127),("evaluation",11,12,511)):
        assert geometry_offsets(*cell)==_reference_geometry(*cell)
    with pytest.raises(NativeBackendError,match="RNG_ADDRESS_EXHAUSTED"):
        geometry_offsets("development",0,4,0,test_max_g=2,test_flags=1)
    with pytest.raises(NativeBackendError,match="RNG_ADDRESS_EXHAUSTED"):
        geometry_offsets("development",0,4,0,test_max_g=2,test_flags=2)


def test_exact_fixture_covers_geometry_fields_lr_free_embed_and_order():
    native=fixture_audit();assert native==reference_fixture_audit()
    text=native.decode();assert text.count("\nH|")+text.startswith("H|")==6
    for row in (r for r in text.splitlines() if r.startswith("H|")):
        parts=row.split("|");assert parts[2]==parts[4] and parts[5]=="1"
        assert sum(map(int,parts[2].split(",")))==120
        assert sum(map(int,parts[3].split(",")))==120
    assert "ORDER|1|3|2|0" in text
    assert "\nBIG|" in text


def test_vendor_free_arbitrary_width_rationals_match_fraction():
    cases = [
        ((2**192-1,2**128-1),(-(2**200+123),2**130+5)),
        ((-(2**257+17),2**193+9),((2**225+31),-(2**129+1))),
        ((2**521-1,2**127+1),(2**383+19,2**255-19)),
        ((-0,999999999999999999999999999999999999999),(7,-21)),
    ]
    cases.extend(
        (
            (((-1)**index)*((1<<(32*index+1))+17*index),(1<<(16*index+3))+2*index+1),
            (((1<<(24*index+5))-19*index),-((1<<(12*index+7))+2*index+1)),
        )
        for index in range(1,13)
    )
    for a,b in cases:
        fa,fb=Fraction(*a),Fraction(*b)
        expected={"add":fa+fb,"sub":fa-fb,"mul":fa*fb,"div":fa/fb}
        for operation,value in expected.items():
            assert exact_rational_binary(a,b,operation)==f"{value.numerator}/{value.denominator}"
        assert exact_rational_binary(a,b,"lt") is (fa<fb)
        assert exact_rational_binary(a,b,"eq") is (fa==fb)


def test_registry_admits_only_declared_native_widths(tmp_path):
    cap=backend_capability(VQFP_VNPA_R03_FULL_CHAIN)
    assert cap.production_supported is False and cap.production_backend is None and not cap.full_reset_step_cpp
    with pytest.raises(ProductionBackendUnsupported,match="not production-supported"):
        require_cpp_batched_production(VQFP_VNPA_R03_FULL_CHAIN,backend="cpp",batch_width=8,build_root=tmp_path)
    with pytest.raises(ProductionBackendUnsupported):require_cpp_batched_production(VQFP_VNPA_R03_FULL_CHAIN,backend="python",batch_width=8)
    with pytest.raises(ProductionBackendUnsupported):require_cpp_batched_production(VQFP_VNPA_R03_FULL_CHAIN,backend="cpp",batch_width=7)


def test_source_keyed_identity_and_synthetic_caps():
    identity=artifact_identity();assert identity["revision"]==EXACT_REVISION and identity["python_fallback"] is False
    row=synthetic_benchmark(width=32,candidates=4,episodes=8,draws=16)
    assert row["policy_cell_states"]==4*8*48 and row["resample_blocks"]==16*12
    with pytest.raises(ValueError):synthetic_benchmark(width=32,candidates=65,episodes=1,draws=1)


def test_production_guard_prevents_question_relevant_activity():
    with pytest.raises(NativeBackendError,match="ACTIVITY_AUTHORITY_REQUIRED"):production_execute_guard()


def test_atomic_resume_identity_and_no_partial_release(tmp_path):
    identity=input_identity(science_card_sha256=SCIENCE_CARD_SHA256);generation=PrivateGeneration(tmp_path,identity,synthetic_test=True)
    competence={field:True for field in COMPETENCE_FIELDS}
    a=WorkRange("development",0,4);b=WorkRange("development",4,8)
    generation.commit_range(a,opaque_digest=hashlib.sha256(b"a").hexdigest(),complete_count=4)
    assert generation.first_missing("development",8)==4
    with pytest.raises(LifecycleError,match="incomplete"):generation.publish_complete(expected_ranges=(a,b),competence=competence)
    generation.commit_range(b,opaque_digest=hashlib.sha256(b"b").hexdigest(),complete_count=4)
    bad=dict(competence);bad["evaluation_panel"]=False
    with pytest.raises(LifecycleError,match="competence"):generation.publish_complete(expected_ranges=(a,b),competence=bad)
    final=generation.publish_complete(expected_ranges=(a,b),competence=competence)
    payload=json.loads(final.read_text());assert payload["partial_release"] is False and "score" not in payload


def test_committed_range_is_immutable(tmp_path):
    generation=PrivateGeneration(tmp_path,input_identity(science_card_sha256=SCIENCE_CARD_SHA256),synthetic_test=True);work=WorkRange("resampling",0,2)
    generation.commit_range(work,opaque_digest="1"*64,complete_count=2)
    with pytest.raises(LifecycleError,match="cannot be replaced"):
        generation.commit_range(work,opaque_digest="2"*64,complete_count=2)


def test_science_card_identity_is_frozen_in_admission_and_lifecycle():
    assert artifact_identity()["science_card_sha256"]==SCIENCE_CARD_SHA256
    with pytest.raises(LifecycleError,match="science-card identity mismatch"):
        input_identity(science_card_sha256="0"*64)
    with pytest.raises(LifecycleError,match="address-table identity mismatch"):
        input_identity(science_card_sha256=SCIENCE_CARD_SHA256,address_table="changed")


def test_production_lifecycle_enforces_counts_competence_and_nonoverlap(tmp_path):
    identity=input_identity(science_card_sha256=SCIENCE_CARD_SHA256)
    production_generation=PrivateGeneration(tmp_path/"production",identity)
    with pytest.raises(LifecycleError,match="exceeds frozen"):
        production_generation.commit_range(WorkRange("resampling",0,20001),opaque_digest="3"*64,complete_count=20001)
    synthetic=PrivateGeneration(tmp_path/"synthetic",identity,synthetic_test=True)
    synthetic.commit_range(WorkRange("evaluation",0,4),opaque_digest="4"*64,complete_count=4)
    with pytest.raises(LifecycleError,match="overlap"):
        synthetic.commit_range(WorkRange("evaluation",2,6),opaque_digest="5"*64,complete_count=4)


def test_cost_collapse_native_matches_literal_reference_and_covers_six_slices():
    native, metrics = cost_collapse_slice(
        width=8, workers=2, candidates=2, host_episodes=4, draws=4,
    )
    assert native == stage_literal_audit(host_episodes=4, candidates=2, draws=4)
    assert metrics["host_episodes"] == 4
    assert metrics["tape_states"] == 4 * 32
    assert metrics["score_rows"] == 8
    assert metrics["paired_selections"] == 4 * 12 * 2 * 72
    assert metrics["j_reductions"] == metrics["r_reductions"] == 4 * 10 * 2 * 12
    for kernel in metrics["kernel_instrumentation"].values():
        assert kernel["operations"] > 0 and kernel["operands"] == 2 * kernel["operations"]
        assert kernel["fixed_width_hits"] + kernel["arbitrary_width_slow_paths"] == kernel["operands"]
        assert sum(kernel["operand_bit_length_bands"].values()) == kernel["operands"]
    assert metrics["kernel_instrumentation"]["controls_u_z_treatment_free_lr_oracle_order"]["arbitrary_width_slow_paths"] > 0
    assert metrics["kernel_instrumentation"]["paired_j_r_composite_rank_reducer"]["operations"] > 0
    host_rows = [row.split("|") for row in native.decode().splitlines() if row.startswith("H|")]
    assert all(len(row) == 6 and len(row[5].split(",")) == 32 for row in host_rows)
    assert all([row[5].split(",").count(str(state)) for state in range(6)] == list(map(int, row[4].split(","))) for row in host_rows)


def test_cost_collapse_tile_and_worker_schedule_are_byte_independent():
    expected = None
    for width in (8, 32, 64):
        for workers in (1, 2, 4, 8):
            payload, metrics = cost_collapse_slice(
                width=width, workers=workers, candidates=4,
                host_episodes=4, draws=8,
            )
            expected = payload if expected is None else expected
            assert payload == expected
            assert metrics["workers"] == workers
            assert metrics["tile_width"] == width


def test_cost_collapse_caps_fail_before_native_work():
    for kwargs in (
        dict(width=1, workers=1, candidates=1, host_episodes=1, draws=1),
        dict(width=8, workers=16, candidates=1, host_episodes=1, draws=1),
        dict(width=8, workers=1, candidates=513, host_episodes=1, draws=1),
        dict(width=8, workers=1, candidates=1, host_episodes=4097, draws=1),
        dict(width=8, workers=1, candidates=1, host_episodes=1, draws=4097),
        dict(width=8, workers=1, candidates=512, host_episodes=481, draws=1),
    ):
        with pytest.raises(ValueError):
            validate_cost_collapse_limits(**kwargs)
