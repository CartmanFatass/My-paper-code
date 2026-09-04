from __future__ import annotations

import numpy as np

from experiments.candidates.variable_n_fleet_churn_bpcr_r09.association import (
    consistent_relabel,
    row_cut,
)
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.models import (
    PublicObservation,
    audit_direct,
    decode_mapr,
    direct_parameter_shapes,
    embed_mapr,
    exact_binary64_mean,
    mapr_parameter_shapes,
    strictness_witness,
)


def _zero_parameters(shapes):
    return {name: np.zeros(shape, dtype=np.float64) for name, shape in shapes.items()}


def _observation() -> PublicObservation:
    return PublicObservation(
        agents=np.zeros((3, 38), dtype=np.float64),
        zones=np.zeros((2, 15), dtype=np.float64),
        globals=np.zeros(4, dtype=np.float64),
        legal_masks=np.ones((3, 4), dtype=np.float64),
        opaque_ranks=(3, 1, 2),
    )


def test_exact_mapr_embedding_and_decoded_audit() -> None:
    mapr = _zero_parameters(mapr_parameter_shapes())
    direct = embed_mapr(mapr)
    audit = audit_direct(_observation(), direct)
    assert decode_mapr(_observation(), mapr) == audit.full_command == audit.zero_residual_command
    assert audit.i_res_active == 0 and audit.i_res_change == 0
    assert all(item.tv_distance == 0 for item in audit.token_audits)
    assert strictness_witness()["strict"]


def test_mapr_and_direct_preserve_multiedge_fixed_occupants() -> None:
    observation=_observation()
    masks=np.array(observation.legal_masks,copy=True);masks[:,0]=0;masks[:,2]=0
    fixed=PublicObservation(observation.agents,observation.zones,observation.globals,masks,observation.opaque_ranks,(1,None,2,None))
    mapr=_zero_parameters(mapr_parameter_shapes());direct=embed_mapr(mapr)
    mapr_command=decode_mapr(fixed,mapr);audit=audit_direct(fixed,direct)
    assert mapr_command==audit.full_command==audit.zero_residual_command
    assert mapr_command[0]==1 and mapr_command[2]==2
    assert 1 not in mapr_command[1:] and 2 not in (mapr_command[1],mapr_command[3])
    assert tuple(x.token for x in audit.token_audits)==(1,3)


def test_exact_pooling_is_bitwise_presentation_order_independent() -> None:
    rows=np.array([[1e100,1.0],[-1e100,2.0],[3.0,3.0],[4.0,4.0]],dtype=np.float64)
    first=exact_binary64_mean(rows)
    second=exact_binary64_mean(rows[[2,0,3,1]])
    assert np.array_equal(first.view(np.uint64),second.view(np.uint64))


def test_row_cut_preserves_multiset_and_relabel_recomputes_raw_records() -> None:
    rows=np.arange(16,dtype=np.float64).reshape(4,4)
    cut=row_cut(rows,(("fast",2,15),("fast",2,15),("std",1,7),("std",1,7)),lambda block:block[1:]+block[:1])
    assert cut.opportunity == 1
    assert sorted(map(tuple,cut.reassigned_rows)) == sorted(map(tuple,rows))
    raw=np.array([[4.0],[1.0],[3.0]])
    decoder=lambda presented:(int(np.argmin(presented[:,0])),None,None,None)
    ordinary=consistent_relabel(raw,(0,1,2),decoder)
    relabeled=consistent_relabel(raw,(2,0,1),decoder)
    assert ordinary == relabeled == (1,None,None,None)
