from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_contract import (
    CLAIM_ROWS, ResourceCeilings, complete_claim_inventory, complete_contract,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_reducer import (
    BRANCHES, MATERIAL_MARGINS, NONINFERIORITY_MARGINS, SIGNS, BranchEvidence,
    CompleteClaimAccounting, EndpointRows, NonharmObservation, first_match_branch, signed_benefit,
)


def test_source_factored_complete_inventory_preserves_no_trigger_rows() -> None:
    rows = complete_claim_inventory()
    assert len(rows) == CLAIM_ROWS == 6_912
    assert len({row.key() for row in rows}) == 6_912
    accounting = CompleteClaimAccounting()
    for index, row in enumerate(rows):
        accounting.put(row, trigger_present=index % 17 == 0)
    sealed = accounting.seal_scaffold()
    assert sealed["row_count"] == 6_912
    assert sealed["no_trigger_rows"] > 0
    assert sealed["question_relevant_output"] is False
    assert complete_contract()["training_jobs"] == 24
    assert ResourceCeilings().io_gib == 68.14


def test_source_factored_endpoint_signs_margins_nonharm_and_first_match() -> None:
    service = np.ones((10, 100), dtype=np.int8); service[0, :20] = 0
    endpoint = EndpointRows(service).reduce()
    assert tuple(endpoint) == ("MEAN", "TAIL", "DEFICIT", "DELAY")
    assert SIGNS == {"MEAN": 1, "TAIL": 1, "DEFICIT": -1, "DELAY": -1}
    assert MATERIAL_MARGINS == {"MEAN": .03, "TAIL": .05, "DEFICIT": .25, "DELAY": .5}
    assert NONINFERIORITY_MARGINS == {"MEAN": .01, "TAIL": .02, "DEFICIT": .25, "DELAY": .5}
    assert signed_benefit({"MEAN": 1, "TAIL": 1, "DEFICIT": 0, "DELAY": 0},
                          {"MEAN": 0, "TAIL": 0, "DEFICIT": 1, "DELAY": 1}) == {
                              "MEAN": 1.0, "TAIL": 1.0, "DEFICIT": 1.0, "DELAY": 1.0}
    assert NonharmObservation(0, 0, 0, 0, 0, 0, 0, 15.0, -.01, True).passes()
    invalid_service = service.astype(np.float64); invalid_service[0, 0] = 0.5
    with pytest.raises(Exception, match="endpoint rows differ"):
        EndpointRows(invalid_service).reduce()
    invalid_service[0, 0] = np.nan
    with pytest.raises(Exception, match="endpoint rows differ"):
        EndpointRows(invalid_service).reduce()
    fixtures = (
        BranchEvidence(protocol_and_measurement_valid=False, shadow_specific_material=True),
        BranchEvidence(competence_opportunity_support=False), BranchEvidence(answerable_and_precise=False),
        BranchEvidence(nonharm_pass=False), BranchEvidence(replay_absorbs_shadow=True),
        BranchEvidence(shadow_specific_material=True), BranchEvidence(generic_transfer_material=True),
        BranchEvidence(target_specific_nonmaterial=True), BranchEvidence(),
    )
    assert tuple(first_match_branch(row) for row in fixtures) == BRANCHES
