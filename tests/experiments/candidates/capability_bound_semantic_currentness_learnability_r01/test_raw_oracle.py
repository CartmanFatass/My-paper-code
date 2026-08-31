from __future__ import annotations

import itertools

import torch

from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.codecs import (
    CODEC_SCHEDULES, CodecArm, encode_bits,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.contract import (
    ACTIVE_PARAMETERS,
    FIELD_LAYOUT,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.oracle import (
    assert_static_raw_oracle,
    compile_raw_oracle,
    raw_inverted_shear_targets,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.support import _pack_bits


def _case(*, need: int, gated: int, neutral: int, owner: int, association: int,
          epoch: int, address: int, source: int, content: int) -> tuple[int, ...]:
    fields = {name: 0 for name, _offset, _width in FIELD_LAYOUT}
    physical = 37
    fields.update(
        physical_receiver=physical,
        owner_predecessor=19,
        owner_current=19 if owner else 23,
        body_epoch=41,
        current_epoch=41 if epoch else 43,
        associated_carrier_issued_to=physical if association else 47,
        execution_carrier_issued_to=physical,
        body_addressed_receiver=physical if address else 53,
        payload_source_receiver=physical if source else 59,
        focal_need_active=need,
        access_binding_gated=gated,
        body_native_neutral=neutral,
        body_content_bit=1,
        focal_need_bit=1 if content else 0,
    )
    return encode_bits(_pack_bits(fields), CodecArm.RAW)


def _expected(case: tuple[int, ...]) -> tuple[float, float, float]:
    need, gated, neutral, owner, association, epoch, address, source, content = case
    serve_open = need and not neutral and not gated and epoch and address and source and content
    serve_gated = need and not neutral and gated and owner and association and epoch and address and source and content
    serve = int(bool(serve_open or serve_gated))
    return (float(serve), float(need - serve), float(1 - need))


def test_sparse_raw_oracle_common_shape_and_exhaustive_boolean_rule() -> None:
    model = compile_raw_oracle()
    assert sum(parameter.numel() for parameter in model.parameters()) == ACTIVE_PARAMETERS
    assert all(not parameter.requires_grad for parameter in model.parameters())
    cases = list(itertools.product((0, 1), repeat=9))
    inputs = torch.tensor(
        [_case(need=c[0], gated=c[1], neutral=c[2], owner=c[3], association=c[4],
               epoch=c[5], address=c[6], source=c[7], content=c[8]) for c in cases],
        dtype=torch.float32,
    )
    with torch.no_grad():
        outputs = model(inputs)
    assert_static_raw_oracle(outputs)
    assert outputs.tolist() == [list(_expected(case)) for case in cases]


def test_output_head_is_zero_for_fresh_learned_model_only() -> None:
    from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.model import DenseLearner

    learned = DenseLearner()
    learned.zero_output_head()
    assert torch.count_nonzero(learned.layers[-1].weight).item() == 0
    assert torch.count_nonzero(learned.layers[-1].bias).item() == 0


def test_sparse_oracle_compilation_preserves_ambient_torch_rng() -> None:
    torch.manual_seed(314159)
    before = torch.random.get_rng_state().clone()
    compile_raw_oracle()
    assert torch.equal(torch.random.get_rng_state(), before)


def test_sparse_oracle_l1_realizes_all_49_raw_inverse_targets() -> None:
    fields = {
        name: ((index * 37 + 11) % (2**width))
        for index, (name, _offset, width) in enumerate(FIELD_LAYOUT)
    }
    original = _pack_bits(fields)
    encoded = encode_bits(original, CodecArm.RAW)
    model = compile_raw_oracle()
    recovered = raw_inverted_shear_targets(
        model, torch.tensor([encoded], dtype=torch.float32),
    )[0]
    targets = [target for target, _source in CODEC_SCHEDULES[CodecArm.RAW]]
    assert len(targets) == len(set(targets)) == 49
    assert recovered.tolist() == [float(original[target]) for target in targets]
