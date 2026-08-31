from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_backend import (
    PhasedSidecarError,
    test_only_two_owner_batch,
)


def test_phased_sidecar_is_nonmutating_and_promotes_exact_post_arrival_source() -> None:
    native = test_only_two_owner_batch()
    parent = native.snapshot_bytes()

    prepared = native.begin_tick()

    assert native.snapshot_bytes() == parent
    assert prepared.owner.tolist() == [0, 1]
    assert prepared.application_tick.tolist() == [100, 100]
    assert prepared.snapshot_assimilation_requested.tolist() == [True, True]
    assert prepared.snapshot_recipient.tolist() == [1, 0]
    assert prepared.phase == "POST_ARRIVAL_PRE_CAS"
    prepared_payload = prepared.snapshot_bytes()

    pre_arrival = prepared.pre_bridge_hidden.copy()
    post_arrival = pre_arrival.copy()
    # The Python checkpoint/snapshot bridge owns this mutation.  Native receives
    # the resulting immutable cut and must not clip or repair it.
    post_arrival[0, 3, 0] = -0.9375
    post_arrival[1, 1, 0] = 0.8125
    handoff = prepared.recurrent_handoff(pre_arrival, post_arrival)
    handoff_payload = handoff.snapshot_bytes()
    fork = prepared.clone_prepared(handoff)

    assert prepared.snapshot_bytes() == prepared_payload
    assert handoff.snapshot_bytes() == handoff_payload
    assert fork.prepared_input_immutable is True
    assert fork.handoff_bytes_before == fork.handoff_bytes_after
    assert fork.phase == "BRANCH_OBSERVATION_READY_PRE_FORWARD"
    assert fork.forward_count.tolist() == [0, 0]
    assert tuple(fork.branches) == ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
    retain = fork.branches["RETAIN"]
    copy = fork.branches["TRANSFER_COPY"]
    shadow = fork.branches["TRANSFER_SHADOW"]

    assert retain.owner.tolist() == [0, 1]
    assert copy.owner.tolist() == [1, 0]
    assert shadow.owner.tolist() == [1, 0]
    assert np.array_equal(retain.hidden, post_arrival)

    # lane 0: old owner U0, new owner U1; lane 1: old owner U1, new owner U0.
    assert np.array_equal(copy.hidden[0, 2], post_arrival[0, 0])
    assert np.array_equal(shadow.hidden[0, 2], post_arrival[0, 3])
    assert np.array_equal(copy.hidden[0, 1], post_arrival[0, 0])
    assert np.array_equal(shadow.hidden[0, 1], post_arrival[0, 0])
    assert np.array_equal(copy.hidden[1, 0], post_arrival[1, 2])
    assert np.array_equal(shadow.hidden[1, 0], post_arrival[1, 1])
    assert np.array_equal(copy.hidden[1, 3], post_arrival[1, 2])
    assert np.array_equal(shadow.hidden[1, 3], post_arrival[1, 2])

    # Observations are materialized after the transaction and before any policy
    # forward.  Actor row 3 is self_is_owner and critic rows 46-47 are owner bits.
    assert retain.actor[:, :, 2].tolist() == [[1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0]]
    assert shadow.actor[:, :, 2].tolist() == [[0.0, 0.0, 1.0, 1.0], [1.0, 1.0, 0.0, 0.0]]
    assert retain.critic[:, 45:47].tolist() == [[1.0, 0.0], [0.0, 1.0]]
    assert shadow.critic[:, 45:47].tolist() == [[0.0, 1.0], [1.0, 0.0]]


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf, 1.0000001, -1.0000001])
def test_phased_sidecar_rejects_malformed_source_state_without_clipping(bad_value: float) -> None:
    prepared = test_only_two_owner_batch().begin_tick()
    pre_arrival = prepared.pre_bridge_hidden.copy()
    post_arrival = pre_arrival.copy()
    post_arrival[0, 3, 0] = bad_value
    handoff = prepared.recurrent_handoff(pre_arrival, post_arrival)
    with pytest.raises(PhasedSidecarError, match="finite.*\[-1,1\]"):
        prepared.clone_prepared(handoff)


def test_phased_sidecar_rejects_reuse_and_does_not_accept_application_raw_action() -> None:
    prepared = test_only_two_owner_batch().begin_tick()
    assert not hasattr(prepared, "raw_action")
    assert "raw_action" not in prepared.public_fields
    pre_arrival = prepared.pre_bridge_hidden.copy()
    post_arrival = pre_arrival.copy()
    post_arrival[0, 3, 0] = -0.9375
    post_arrival[1, 1, 0] = 0.8125
    handoff = prepared.recurrent_handoff(pre_arrival, post_arrival)
    prepared.clone_prepared(handoff)
    with pytest.raises(PhasedSidecarError, match="exactly once"):
        prepared.clone_prepared(handoff)


def test_phased_sidecar_native_rejects_swapped_stale_or_wrong_copy_handoff() -> None:
    prepared = test_only_two_owner_batch().begin_tick()
    pre_arrival = prepared.pre_bridge_hidden.copy()
    post_arrival = pre_arrival.copy()
    post_arrival[0, 3, 0] = -0.9375
    post_arrival[1, 1, 0] = 0.8125
    handoff = prepared.recurrent_handoff(pre_arrival, post_arrival)

    swapped = handoff.test_only_permute_lanes((1, 0))
    with pytest.raises(PhasedSidecarError, match="linearization"):
        prepared.clone_prepared(swapped)

    prepared = test_only_two_owner_batch().begin_tick()
    handoff = prepared.recurrent_handoff(pre_arrival, post_arrival)
    stale = handoff.test_only_replace(lane=0, field="snapshot_version", value=999)
    with pytest.raises(PhasedSidecarError, match="linearization"):
        prepared.clone_prepared(stale)

    prepared = test_only_two_owner_batch().begin_tick()
    wrong_copy = post_arrival.copy()
    wrong_copy[0, 0, 0] += 0.125  # only lane-0 U1-S (copy 3) may assimilate
    handoff = prepared.recurrent_handoff(pre_arrival, wrong_copy)
    with pytest.raises(PhasedSidecarError, match="snapshot recipient"):
        prepared.clone_prepared(handoff)


def test_row54_source_and_top_lineage_tamper_remove_current_shadow_record() -> None:
    def clone(prepared):
        pre = prepared.pre_bridge_hidden.copy()
        post = pre.copy()
        post[0, 3, 0] = -0.9375
        post[1, 1, 0] = 0.8125
        return prepared.clone_prepared(prepared.recurrent_handoff(pre, post))

    baseline = clone(test_only_two_owner_batch().begin_tick())
    assert baseline.branches["TRANSFER_SHADOW"].actor[0, 3, 53] == 1.0

    source_tampered = test_only_two_owner_batch().begin_tick().test_only_replace_causal(
        lane=0, physical=0, field="source_sequence", value=999
    )
    assert clone(source_tampered).branches["TRANSFER_SHADOW"].actor[0, 3, 53] == 0.0

    lineage_tampered = test_only_two_owner_batch().begin_tick().test_only_replace_lineage(
        lane=0, physical=0, value=999
    )
    assert clone(lineage_tampered).branches["TRANSFER_SHADOW"].actor[0, 3, 53] == 0.0
