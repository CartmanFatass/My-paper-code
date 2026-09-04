from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    ProductionBackendError, decode_promotion_source_receipt,
    source_factored_mismatch_test_fixture, source_factored_test_fixture,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_contract import TestAuthority as R06TestAuthority
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_fork import clone_test_only
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_fork import PolicyStateMode, fork_policy_state


def test_source_factored_native_three_way_clone_is_atomic_and_truthful() -> None:
    batch, rows = source_factored_test_fixture(3, R06TestAuthority())
    parent = batch.snapshot_bytes()
    branches, observations, metadata = clone_test_only(
        native=batch, step_rows=rows,
    )
    assert batch.snapshot_bytes() == parent
    assert set(branches) == {"RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW"}
    assert metadata["parent_byte_immutable"] is True
    assert metadata["receipt_bytes"] == 24
    assert metadata["transaction_energy"] == 0.48
    assert metadata["application_latency_ticks"] == 1
    assert all(len(metadata["raw_receipts"][name][0]) == 24 for name in branches)
    decoded = {name: [decode_promotion_source_receipt(row) for row in metadata["raw_receipts"][name]] for name in branches}
    assert [decoded[name][0]["source_mode"] for name in branches] == [0, 1, 2]
    assert [row["owner_before"] for row in decoded["RETAIN"]] == [0, 1, 0]
    assert [row["owner_after"] for row in decoded["RETAIN"]] == [0, 1, 0]
    assert [row["owner_after"] for row in decoded["TRANSFER_COPY"]] == [1, 0, 1]
    assert len(metadata["linearization_tuples"][0]["controller_hidden"]) == 512
    assert all(np.array_equal(observations[name]["tick"], np.full(3, 100)) for name in branches)
    assert all(np.array_equal(branches[name].observe()["actor"], observations[name]["actor"]) for name in branches)
    assert np.array_equal(observations["RETAIN"]["owner"], np.array([0, 1, 0]))
    assert np.array_equal(observations["RETAIN"]["actuator_owner"], np.array([0, 1, 0]))
    assert np.array_equal(observations["RETAIN"]["cas_applied"], np.zeros(3))
    for name in ("TRANSFER_COPY", "TRANSFER_SHADOW"):
        assert np.array_equal(observations[name]["owner"], np.array([1, 0, 1]))
        assert np.array_equal(observations[name]["actuator_owner"], np.array([1, 0, 1]))
        assert np.array_equal(observations[name]["cas_applied"], np.ones(3))
    for branch in branches.values():
        state = branch._states[0]
        observation = branch.observe()
        assert observation["owner"][0] == state.owner
        assert observation["service_epoch"][0] == state.service_epoch
        assert observation["protocol_bytes"][0] == state.protocol_bytes
        assert observation["total_energy"][0] == state.total_energy
        assert state.pending_intent == 0 and state.handover_used == 1
        assert list(state.lineage_lock) == [0, 0]
        assert state.service_epoch == 1 and state.invalid_commit == 0


def test_source_factored_native_alpha_equivalence_and_combined_predicate() -> None:
    batch, rows = source_factored_test_fixture(1, R06TestAuthority())
    raw = batch.clone_promotion_source(rows)[0]
    copy_hidden = np.asarray(raw["transfer_copy_state"]["controller_hidden"])
    shadow_hidden = np.asarray(raw["transfer_shadow_state"]["controller_hidden"])
    retain_hidden = np.asarray(raw["retain_state"]["controller_hidden"])
    assert np.array_equal(copy_hidden[256:384], retain_hidden[:128])
    assert np.array_equal(shadow_hidden[256:384], retain_hidden[384:512])
    assert not np.array_equal(copy_hidden[256:384], shadow_hidden[256:384])
    bounded = rows.copy(); bounded["controller_hidden"][0, 0] = 1.5; bounded["controller_hidden"][0, 384] = -1.5
    bounded_raw = batch.clone_promotion_source(bounded)[0]
    policy = bounded["controller_hidden"].reshape(1, 4, 128)
    assert np.array_equal(
        np.asarray(bounded_raw["transfer_copy_state"]["controller_hidden"])[256:384],
        fork_policy_state(policy, [0], PolicyStateMode.COPY)[0, 2],
    )
    assert np.array_equal(
        np.asarray(bounded_raw["transfer_shadow_state"]["controller_hidden"])[256:384],
        fork_policy_state(policy, [0], PolicyStateMode.SHADOW)[0, 2],
    )
    mismatch = rows.copy(); mismatch["controller_hidden"][0, 7] = np.nan
    with pytest.raises(ProductionBackendError, match="rejected batch"):
        batch.clone_promotion_source(mismatch)
    for mismatch_code in range(1, 25):
        invalid, invalid_rows = source_factored_mismatch_test_fixture(1, mismatch_code, R06TestAuthority())
        with pytest.raises(ProductionBackendError, match="rejected batch"):
            invalid.clone_promotion_source(invalid_rows)


def test_source_factored_signed_zero_allowlist_and_direct_call_graph() -> None:
    batch, rows = source_factored_test_fixture(2, R06TestAuthority())
    rows["controller_hidden"][0, 0] = -0.0; rows["controller_hidden"][0, 384] = 0.0
    raw = batch.clone_promotion_source(rows)
    assert np.signbit(raw[0]["transfer_copy_state"]["controller_hidden"][256])
    assert not np.signbit(raw[0]["transfer_shadow_state"]["controller_hidden"][256])
    differing = {
        name for name in raw.dtype["transfer_copy_state"].names
        if not np.array_equal(raw["transfer_copy_state"][name], raw["transfer_shadow_state"][name])
    }
    assert differing == {"controller_hidden"}
    for lane in range(2):
        parent_hash = batch._states[lane].protocol_wire_hash
        assert raw[lane]["retain_state"]["protocol_wire_hash"] == parent_hash
        assert raw[lane]["transfer_copy_state"]["protocol_wire_hash"] == parent_hash
        assert raw[lane]["transfer_shadow_state"]["protocol_wire_hash"] == parent_hash

    source_path = Path("experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp")
    source = source_path.read_text(encoding="utf-8")
    names = ("source_factored_combined_predicate", "promote_source_factored", "source_factored_receipt", "clone_promotion_source_one")
    fragments = []
    for name in names:
        start = source.index(f"inline ", source.index(name) - 80)
        end = source.index("\n}\n", source.index(name)) + 3
        fragments.append(source[start:end])
    call_graph = "\n".join(fragments)
    for forbidden in ("result_wire", "finish_wire", "account_wire", "protocol_wire_hash", "Sha256", "digest", "hashlib"):
        assert forbidden not in call_graph
    assert "promote_recurrent_state(out.transfer" not in call_graph
