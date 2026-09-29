"""Pure adverse-event serialization; no environment or native transitions."""

import json

from experiments.candidates.uav_persistent_service.b04.audit import release_reason_counts


def test_mixed_released_censored_and_partial_events_serialize():
    events = [{"release_reason": "full", "end_kind": "release"},
              {"release_reason": None, "end_kind": "censored"},
              {"release_reason": None, "end_kind": "partial"}]
    counts = release_reason_counts(events)
    assert counts == {"full": 1, "censored": 1, "partial": 1}
    assert json.loads(json.dumps(counts, sort_keys=True)) == counts
    assert events[1]["release_reason"] is None
