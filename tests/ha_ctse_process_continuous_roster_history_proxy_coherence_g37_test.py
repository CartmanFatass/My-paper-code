from __future__ import annotations

import numpy as np

from ha_ctse_process import continuous_roster_history_proxy_free_cs_g36 as g36
from ha_ctse_process import continuous_roster_history_proxy_coherence_g37 as g37


def test_factorized_tape_uses_exact_independent_column_streams() -> None:
    bank = g36.G36HistoryProxyDonorBank.build()
    tape = g37.G37FactorizedHistoryProxyTape(
        bank, replicate=1, capacity=8, formal=True
    )
    mask = np.array([True, True, True, True, False, False, False, False])
    bundle = tape.bundle_for(
        episode_id=17, physical_call_position=9, active_mask=mask
    )
    source = bank.snapshots(4)
    expected = np.zeros((8, 4), dtype=np.float32)
    for coordinate in range(4):
        selected_rng = np.random.default_rng(
            np.random.SeedSequence(
                [tape.seed, 8, 17, 9, 4, 2 * coordinate]
            )
        )
        permutation_rng = np.random.default_rng(
            np.random.SeedSequence(
                [tape.seed, 8, 17, 9, 4, 2 * coordinate + 1]
            )
        )
        snapshot = source[int(selected_rng.integers(0, len(source)))]
        expected[mask, coordinate] = snapshot[
            permutation_rng.permutation(4), coordinate
        ]
    assert np.array_equal(bundle, expected)
    assert np.array_equal(
        bundle,
        tape.bundle_for(
            episode_id=17, physical_call_position=9, active_mask=mask
        ),
    )
    assert tape.target_history_read_count == 0
    assert g37.validate_g37_factorized_marginals(
        bank,
        bundle,
        episode_id=17,
        physical_call_position=9,
        active_mask=mask,
        replicate=1,
        capacity=8,
        formal=True,
    )


def test_nonformal_offset_and_inactive_rows_are_exact() -> None:
    bank = g36.G36HistoryProxyDonorBank.build()
    formal = g37.G37FactorizedHistoryProxyTape(
        bank, replicate=0, capacity=6, formal=True
    )
    nonformal = g37.G37FactorizedHistoryProxyTape(
        bank, replicate=0, capacity=6, formal=False
    )
    mask = np.array([False, True, True, True, False, False])
    assert nonformal.seed - formal.seed == g37.NONFORMAL_SEED_OFFSET
    bundle = nonformal.bundle_for(
        episode_id=3, physical_call_position=4, active_mask=mask
    )
    assert not np.any(bundle[~mask])
    assert np.isfinite(bundle[mask]).all()
    assert np.all((bundle[mask] >= 0.0) & (bundle[mask] <= 1.0))


def test_factorized_tape_rejects_invalid_identity_and_mask() -> None:
    bank = g36.G36HistoryProxyDonorBank.build()
    for replicate, capacity in ((-1, 6), (3, 6), (0, 7)):
        try:
            g37.G37FactorizedHistoryProxyTape(
                bank, replicate=replicate, capacity=capacity, formal=True
            )
        except ValueError:
            pass
        else:
            raise AssertionError("invalid G37 tape identity was accepted")
    tape = g37.G37FactorizedHistoryProxyTape(
        bank, replicate=0, capacity=6, formal=True
    )
    try:
        tape.bundle_for(
            episode_id=0,
            physical_call_position=0,
            active_mask=np.ones(5, dtype=bool),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid G37 mask was accepted")
