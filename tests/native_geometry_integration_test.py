"""Turning the native geometry path on must change speed and nothing else.

`tests/uav_cpp_backend_oracle_test.py` proves the kernel's path-loss matrices are
bitwise identical to the environment's own methods. That is necessary and not
sufficient: it says the numbers agree, not that WIRING them in leaves the
environment's behaviour alone. The prefill populates a cache other call sites
read, and a step's SINR matrix, connections and handover statistics all descend
from it.

So these tests compare the environment against ITSELF with the flag off and on,
over real steps, on state that the prefill could plausibly disturb.

The first test is the one that matters most and it is not about equality: it
asserts the fast path was actually TAKEN. An equality test against a backend that
silently declined to load passes trivially and forever, and a benchmark run in
that state reports the Python path's own speed as the kernel's win.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv  # noqa: E402

backend = pytest.importorskip("ha_ctse_process.uav_cpp_backend")


def _build(*, native: bool, seed: int = 20260725):
    """Build through the audit's PINNED path, not raw construction + reset.

    MEASURED, and it cost a false failure: `UAVEnergyAwareRelayEnv(...)` followed
    by `reset(seed=...)` does NOT fully determine the user world. Two envs built
    that way, back to back with identical seeds, had **different
    `user_positions` before either was stepped** -- so the Nth env built in a
    process gets a different world, and the flag-off/flag-on comparison was
    comparing two different environments. It passed when this file's failing test
    ran alone (two constructions) and failed when four preceded it.

    `build_pinned_env` takes an explicit `user_world_seed`, and construction order
    was separately measured not to move its fingerprint. Comparing anything about
    the channel requires that both sides inhabit the same world first.

    This was NOT a new discovery, and the canonical record is
    `tests/env_user_population_determinism_test.py` plus
    `docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md`:
    the repository already pins "two freshly constructed environments carrying the
    same episode seed do not share a user population", and names
    `regenerate_user_world` after a pinned topology as the repair. I rediscovered
    it the expensive way by writing the obvious construction into a comparison.
    Read those two first before building an env for any comparison.
    """
    import audit_d7_s_event_aligned as audit

    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=seed)
    env = audit.build_pinned_env(
        config, episode_seed=seed, coords=coords, coord_hash=coord_hash,
        energy_stage="S3", user_world_seed=seed)
    env.use_native_geometry = bool(native)
    return env


@pytest.fixture(scope="module", name="toolchain")
def _toolchain():
    try:
        backend.load_uav_cpp_backend()
    except backend.UAVCppBackendUnavailable as error:
        pytest.skip(f"native CPU toolchain unavailable: {error}")
    return True


def test_the_prefill_actually_runs_when_enabled(toolchain) -> None:
    """Without this, every other test here can pass on the Python path."""

    env = _build(native=True)
    cache = env._refresh_step_communication_cache()
    assert cache is not None
    took_it = env._prefill_access_path_loss_natively(cache)
    assert took_it is True, "the native prefill declined; the rest of this file is vacuous"
    matrix = cache["user_path_loss_matrix"]
    assert matrix is not None, "prefill reported success but stored no matrix"
    assert matrix.shape == (env.n_uavs, env.n_users), (
        "prefill must cover the WHOLE matrix; a partial fill leaves misses that "
        "silently reintroduce the Python path")
    assert matrix.dtype == np.float64, (
        "a narrower dtype would round the value the environment reads")
    assert cache["user_path_loss"] == {}, (
        "the native result must stay an ndarray. Exploding it into the per-element "
        "dict re-pays the n_uavs*n_users Python loop the native call exists to "
        "retire, and measured 1.044x -- inside the bench box's noise.")


def test_the_prefill_declines_when_the_flag_is_off() -> None:
    """The paired negative for the flag itself. Default-off must mean off."""

    env = _build(native=False)
    cache = env._refresh_step_communication_cache()
    assert env._prefill_access_path_loss_natively(cache) is False
    assert cache["user_path_loss"] == {}
    assert cache["user_path_loss_matrix"] is None


def test_default_is_off_without_anyone_setting_it() -> None:
    import audit_d7_s_event_aligned as audit

    env = UAVEnergyAwareRelayEnv(config=audit.build_config(), energy_stage="S3")
    assert bool(getattr(env, "use_native_geometry", False)) is False, (
        "the native path must never be on by default -- a formal run would adopt "
        "it without anyone deciding to")


def test_the_two_sides_start_in_the_same_world() -> None:
    """The premise of every comparison below, and it was FALSE for the obvious
    construction path -- see `_build`. If this ever goes red, the equality tests
    are comparing two different environments and mean nothing."""

    off = _build(native=False)
    on = _build(native=True)
    assert np.array_equal(off.uav_positions, on.uav_positions)
    assert np.array_equal(off.user_positions, on.user_positions), (
        "the two envs inhabit different user worlds before either was stepped")
    assert np.array_equal(off.uav_battery_ratios, on.uav_battery_ratios)
    assert np.array_equal(off._communication_unavailable_mask(),
                          on._communication_unavailable_mask())


def test_prefilled_values_are_bitwise_what_the_python_path_would_cache(toolchain) -> None:
    """Every prefilled entry equals the value the miss path would have produced.

    Compared as raw bits, not with a tolerance: the design doc's standard, and
    the only comparison that proves the cache is indistinguishable.
    """

    env = _build(native=True)
    cache = env._refresh_step_communication_cache()
    assert env._prefill_access_path_loss_natively(cache) is True
    matrix = cache["user_path_loss_matrix"]

    mismatches = []
    total = 0
    for i in range(env.n_uavs):
        for j in range(env.n_users):
            total += 1
            # Read through the accessor the environment actually uses, so this
            # tests the wiring and not just the array's contents.
            cached = env._cached_user_path_loss(i, j, step_cache=cache)
            expected = env._compute_air_to_ground_path_loss(
                env.uav_positions[i], env.user_positions[j])
            if np.float64(cached).tobytes() != np.float64(expected).tobytes():
                mismatches.append(((i, j), cached, expected))
    assert total == matrix.size, "iterated a different extent than was stored"
    assert not mismatches, f"{len(mismatches)} of {total} differ: {mismatches[:3]}"


def test_a_full_step_produces_identical_channel_state(toolchain) -> None:
    """The integration test proper: step both environments and compare the state
    the prefill feeds -- SINR, connections, serving assignment."""

    off = _build(native=False)
    on = _build(native=True)

    for step_index in range(3):
        actions = {}
        for name in off.agents:
            space = off.action_space(name)
            actions[name] = np.zeros(space.shape, dtype=space.dtype)
        off.step(actions)
        on.step({k: v.copy() for k, v in actions.items()})

        assert np.array_equal(off.uav_positions, on.uav_positions), f"positions, step {step_index}"
        assert np.array_equal(off.sinr_matrix, on.sinr_matrix), (
            f"SINR matrix differs at step {step_index} -- the prefill changed physics")
        assert np.array_equal(off.connections, on.connections), f"connections, step {step_index}"
        assert np.array_equal(off.user_serving_uav, on.user_serving_uav), (
            f"serving assignment, step {step_index}")


def test_the_comparison_can_actually_fail(toolchain) -> None:
    """Otherwise the step comparison above is decoration.

    Perturb one cached path loss by a single ULP and confirm it propagates into
    the SINR matrix -- proving the assertions are reading a live quantity.
    """

    env = _build(native=True)
    env._update_channel_state()
    baseline = np.asarray(env.sinr_matrix).copy()

    cache = env._refresh_step_communication_cache()
    assert env._prefill_access_path_loss_natively(cache) is True
    # Perturb the ndarray the accessor now reads. Copy first: the native buffer
    # must not be assumed writeable, and a silent failure to mutate would make
    # this negative pass for the wrong reason.
    perturbed = np.array(cache["user_path_loss_matrix"], dtype=np.float64, copy=True)
    perturbed[0, 0] = np.nextafter(perturbed[0, 0], np.inf)
    assert perturbed[0, 0] != cache["user_path_loss_matrix"][0, 0], (
        "the perturbation did not take, so this negative proves nothing")
    cache["user_path_loss_matrix"] = perturbed
    env._channel_update_cache_active = True
    try:
        for j in range(env.n_users):
            env.sinr_matrix[0, j] = env._compute_sinr(0, j)
    finally:
        env._channel_update_cache_active = False

    assert not np.array_equal(baseline, np.asarray(env.sinr_matrix)), (
        "a one-ULP change to a cached path loss did not move the SINR matrix, so "
        "these tests are not reading what they claim to read")
