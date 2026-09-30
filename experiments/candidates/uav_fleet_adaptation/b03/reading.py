"""The unchanged point rules, with explicit retained-control provenance."""
from __future__ import annotations

import copy

from experiments.candidates.uav_fleet_adaptation.b02.reading import read_comparisons as original_comparisons


def read_comparisons(rows, retained, worlds, *, actual_learning):
    result = original_comparisons(rows + retained["rows"], worlds, actual_learning=actual_learning)
    result["scope"] = (
        "one new independently fitted lineage on the existing exposed development panel and fixed sampling "
        "innovations; four newly evaluated neural arms plus two source-bound retained ordinary controls; "
        "the unchanged exploratory point screens are not noninferiority, confirmation or training-population "
        "inference; retained control timing was measured in the prior operation, not contemporaneously"
    )
    result["recurrence"] = {
        "previous_summary_sha256": retained["binding"]["files"]["summary.json"]["sha256"],
        "previous_screens": copy.deepcopy(retained["previous_screens"]),
        "current_screens": copy.deepcopy(result["screens"]),
        "training_lineages_observed": 2,
        "evaluation_panel": "shared previously exposed development worlds; no new confirmation panel",
        "selection": "no checkpoint or decoder selection; no automatic additional repeat or reward continuation",
    }
    return result
