"""The native communication kernel must reproduce OUR environment, bit for bit.

`step_communication_batch` replaces `step_geometry_batch`: ONE native call now
computes every communication matrix a step consumes (path losses,
interference-plus-noise, and link capacities), not just UAV-user path loss.
This is the oracle for that surface: every element of every output is compared
against the environment's own methods, as raw bits
(`np.float64(x).tobytes()`), never a tolerance.

Measured 2026-07-29 at commit 7af5d964, on the geometry-only predecessor:
312/312 elements bitwise identical across access (8x30), air (8x8) and base
(8x1), max_ulp 0. This file re-establishes that bar for the ten-output
communication kernel.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

backend = pytest.importorskip("ha_ctse_process.uav_cpp_backend")


def _build(*, seed: int = 20260725):
    """Build through the audit's PINNED path, not raw construction + reset.

    Identical to `tests/native_geometry_integration_test.py::_build`'s reasoning:
    `UAVEnergyAwareRelayEnv(...)` followed by `reset(seed=...)` does NOT fully
    determine the user world (two such environments diverge in
    `user_positions` before either is stepped). `build_pinned_env` takes an
    explicit `user_world_seed` and is the only construction path with a proven
    fingerprint. See `tests/env_user_population_determinism_test.py` and
    `docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_PREFIX_REPLAY_IS_NOT_FIXED_HISTORY.md`.

    The native flag stays OFF here: this file compares the kernel, called
    directly, against the environment's OWN Python methods -- the flag and the
    cache-wired accessors are a different file's concern
    (`tests/native_geometry_integration_test.py`).
    """
    import audit_d7_s_event_aligned as audit

    config = audit.build_config()
    coords, coord_hash = audit.build_topology_template(config, topology_seed=seed)
    env = audit.build_pinned_env(
        config, episode_seed=seed, coords=coords, coord_hash=coord_hash,
        energy_stage="S3", user_world_seed=seed)
    env.use_native_geometry = False
    # No cache may short-circuit any reference computation below; every
    # `_compute_*`/`_get_link_capacity` call must take the genuine Python path.
    env._disable_step_communication_cache = True
    return env


@pytest.fixture(scope="module", name="env_and_backend")
def _env_and_backend():
    """Build the kernel and the reference env once. Skip if no toolchain.

    A missing MSVC/Ninja is a provisioning fact about the machine, not a defect
    in the kernel, and turning it into a red test would train people to ignore
    this file on every box that cannot build.
    """
    try:
        backend.load_uav_cpp_backend()
    except backend.UAVCppBackendUnavailable as error:
        pytest.skip(f"native CPU toolchain unavailable: {error}")
    env = _build()
    return env


def _bits(value) -> bytes:
    return np.float64(value).tobytes()


def _mcs_arrays(env):
    thresholds = np.ascontiguousarray(
        [float(threshold) for threshold, _ in env.mcs_table], dtype=np.float64
    )
    efficiencies = np.ascontiguousarray(
        [float(efficiency) for _, efficiency in env.mcs_table], dtype=np.float64
    )
    return thresholds, efficiencies


def _call_kernel(env, *, uav_positions, use_fdma, aclr_linear):
    uavs = np.ascontiguousarray(uav_positions, dtype=np.float64)
    users = np.ascontiguousarray(np.asarray(env.user_positions, dtype=np.float64))
    bases = np.ascontiguousarray(np.asarray(env.ground_bs_positions, dtype=np.float64))
    thresholds, efficiencies = _mcs_arrays(env)
    return backend.step_communication_batch(
        uav_positions=uavs[None, ...],
        user_positions=users[None, ...],
        ground_bs_positions=bases[None, ...],
        carrier_frequency=float(env.carrier_frequency),
        environment_type=str(getattr(env, "environment_type", "urban")),
        tx_power=float(env.tx_power),
        ground_bs_tx_power=float(env.ground_bs_tx_power),
        noise_power_linear_mw=float(env._noise_power_linear_mw()),
        interference_radius=float(env._compute_interference_radius()),
        use_fdma=bool(use_fdma),
        aclr_linear=float(aclr_linear),
        bandwidth=float(env.bandwidth),
        min_sinr=float(env.min_sinr),
        mcs_thresholds=thresholds,
        mcs_efficiencies=efficiencies,
    )


def _compare_all_outputs(env, result) -> list:
    """Op-for-op replication of every output against the environment's own
    methods, called on `env` exactly as it stands (positions, use_fdma, ...).
    Returns the mismatch list; empty means bitwise identical throughout.
    """
    uavs = env.uav_positions
    users = env.user_positions
    bases = env.ground_bs_positions
    n_uavs = env.n_uavs
    n_users = env.n_users
    n_bases = env.n_ground_bs

    mismatches = []

    def check(name, indices, actual, expected):
        if _bits(actual) != _bits(expected):
            mismatches.append((name, indices, actual, expected))

    # 1: access_path_loss[i, j] = A2G(uav_i, user_j)
    for i in range(n_uavs):
        for j in range(n_users):
            expected = env._compute_air_to_ground_path_loss(uavs[i], users[j])
            check("access_path_loss", (i, j), result.access_path_loss[0, i, j], expected)

    # 2: air_path_loss[i, k] = A2A(uav_i, uav_k), including the diagonal
    for i in range(n_uavs):
        for k in range(n_uavs):
            expected = env._compute_air_to_air_path_loss(uavs[i], uavs[k])
            check("air_path_loss", (i, k), result.air_path_loss[0, i, k], expected)

    # 3: base_path_loss[i, g] = A2G(uav_i, bs_g)
    for i in range(n_uavs):
        for g in range(n_bases):
            expected = env._compute_air_to_ground_path_loss(uavs[i], bases[g])
            check("base_path_loss", (i, g), result.base_path_loss[0, i, g], expected)

    # 4: user_ipn_dbm[i, j] -- rx_power - _compute_uav_to_user_sinr(i, j, rx_power)
    for i in range(n_uavs):
        for j in range(n_users):
            pl = env._compute_air_to_ground_path_loss(uavs[i], users[j])
            rx_power = env.tx_power - pl
            sinr = env._compute_uav_to_user_sinr(i, j, rx_power)
            expected = rx_power - sinr
            check("user_ipn_dbm", (i, j), result.user_ipn_dbm[0, i, j], expected)

    # 5: uav_uav_ipn_dbm[s, r]. NOT `rx_power - _compute_link_sinr(...)` here:
    # for the diagonal (s == r) that round trip loses its last bit. The 1e-6
    # clamp gives the self-link an rx_power around +100 dBm larger than its
    # real magnitude, and `a - (a - b)` is not guaranteed to reproduce `b`
    # bit-for-bit once `a` and `b` differ that much in scale -- MEASURED:
    # rx_power=104.52940008672039, sinr=157.4646771138294,
    # `rx_power - sinr` = -52.93527702710901, one ULP off the true ipn
    # -52.935277027109 that both the kernel and a direct sum agree on
    # (cross-checked against `_get_link_capacity`, which never round-trips
    # through this subtraction and matches the kernel exactly at this cell).
    # This computes the same interference-plus-noise term `_compute_link_sinr`
    # (scenario_base.py:4638, tx_type=rx_type="uav") does internally, straight
    # from the frozen spec's own wording, without that lossy detour.
    def _uav_uav_ipn_reference(s, r):
        radius = env._compute_interference_radius()
        rx_pos = uavs[r]
        powers = []
        for k in range(n_uavs):
            if k == s or k == r:
                continue
            interferer_pos = uavs[k]
            if env._compute_distance(interferer_pos, rx_pos) > radius:
                continue
            pl = env._compute_air_to_air_path_loss(interferer_pos, rx_pos)
            p = 10 ** ((env.tx_power - pl) / 10)
            if env.use_fdma:
                p = p * env.aclr_linear
            powers.append(p)
        total = np.sum(powers)
        noise = env._noise_power_linear_mw()
        return 10 * np.log10(noise + total)

    for s in range(n_uavs):
        for r in range(n_uavs):
            expected = _uav_uav_ipn_reference(s, r)
            check("uav_uav_ipn_dbm", (s, r), result.uav_uav_ipn_dbm[0, s, r], expected)

    # 6: uav_bs_ipn_dbm[i, g]
    for i in range(n_uavs):
        for g in range(n_bases):
            pl = env._compute_air_to_ground_path_loss(uavs[i], bases[g])
            rx_power = env.tx_power - pl
            sinr = env._compute_link_sinr("uav", i, "ground_bs", g, rx_power)
            expected = rx_power - sinr
            check("uav_bs_ipn_dbm", (i, g), result.uav_bs_ipn_dbm[0, i, g], expected)

    # 7: bs_uav_ipn_dbm[r] -- verified independent of g in the source; use g=0
    for r in range(n_uavs):
        pl = env._compute_ground_to_air_path_loss(bases[0], uavs[r])
        rx_power = env.ground_bs_tx_power - pl
        sinr = env._compute_link_sinr("ground_bs", 0, "uav", r, rx_power)
        expected = rx_power - sinr
        check("bs_uav_ipn_dbm", (r,), result.bs_uav_ipn_dbm[0, r], expected)

    # 8: cap_uav_uav[s, r]
    for s in range(n_uavs):
        for r in range(n_uavs):
            expected = float(env._get_link_capacity("uav", s, "uav", r))
            check("cap_uav_uav", (s, r), result.cap_uav_uav[0, s, r], expected)

    # 9: cap_uav_bs[i, g]
    for i in range(n_uavs):
        for g in range(n_bases):
            expected = float(env._get_link_capacity("uav", i, "ground_bs", g))
            check("cap_uav_bs", (i, g), result.cap_uav_bs[0, i, g], expected)

    # 10: cap_bs_uav[r, g] -- note the [r, g] storage (Python cache key order
    # is ("ground_bs", g, "uav", r))
    for r in range(n_uavs):
        for g in range(n_bases):
            expected = float(env._get_link_capacity("ground_bs", g, "uav", r))
            check("cap_bs_uav", (r, g), result.cap_bs_uav[0, r, g], expected)

    return mismatches


def test_the_bit_comparison_can_actually_fail() -> None:
    """Otherwise every assertion below is decorative."""
    same = np.float64(1.5)
    assert _bits(same) == _bits(same)
    nudged = np.nextafter(same, np.inf)
    assert _bits(same) != _bits(nudged)


def test_environment_type_default_is_shared_by_both_sides(env_and_backend) -> None:
    """The match below is only meaningful if both sides picked the same branch.

    Our environment does not set `environment_type`, so its path-loss methods
    fall to their own `urban` default while the kernel call passes `urban` in
    explicitly. If that ever diverges, every comparison compares two different
    environments and still passes.
    """
    env = env_and_backend
    assert not hasattr(env, "environment_type"), (
        "environment_type is now set; the kernel call must pass it through "
        "rather than relying on both sides defaulting to urban"
    )


@pytest.mark.parametrize("use_fdma", [False, True])
def test_all_ten_outputs_match_the_environment(env_and_backend, use_fdma) -> None:
    env = env_and_backend
    env.use_fdma = bool(use_fdma)
    result = _call_kernel(
        env,
        uav_positions=env.uav_positions,
        use_fdma=use_fdma,
        aclr_linear=float(env.aclr_linear),
    )
    mismatches = _compare_all_outputs(env, result)
    total = (
        env.n_uavs * env.n_users  # access_path_loss + user_ipn_dbm
        + env.n_uavs * env.n_uavs  # air_path_loss + uav_uav_ipn_dbm + cap_uav_uav
        + env.n_uavs * env.n_ground_bs  # base_path_loss + uav_bs_ipn_dbm + cap_uav_bs + cap_bs_uav
    )
    assert total > 0, "the built env is degenerate; this test asserted nothing"
    assert not mismatches, (
        f"{len(mismatches)} mismatches under use_fdma={use_fdma}; "
        f"first 5: {mismatches[:5]}"
    )


def test_degenerate_identical_uav_positions_still_match(env_and_backend) -> None:
    """Two UAVs at the identical position drive A2A distance to exactly 0,
    exercising the 1e-6 clamp both sides share. Still bitwise identical."""
    env = env_and_backend
    original_positions = np.array(env.uav_positions, copy=True)
    original_fdma = env.use_fdma
    degenerate = original_positions.copy()
    degenerate[1] = degenerate[0]
    env.use_fdma = False
    try:
        env.uav_positions = degenerate
        assert env._compute_distance(degenerate[0], degenerate[1]) == 0.0, (
            "the fixture did not actually reach the clamp path"
        )
        result = _call_kernel(
            env, uav_positions=degenerate, use_fdma=False, aclr_linear=float(env.aclr_linear)
        )
        mismatches = _compare_all_outputs(env, result)
        assert not mismatches, f"{len(mismatches)} mismatches; first 5: {mismatches[:5]}"
    finally:
        env.uav_positions = original_positions
        env.use_fdma = original_fdma


def test_one_ulp_perturbation_changes_at_least_one_output(env_and_backend) -> None:
    """The paired negative: otherwise the equality tests above are decoration.

    Perturb one uav position coordinate by one ULP and confirm SOME output
    element changes -- proving the comparison has resolution at all.
    """
    env = env_and_backend
    env.use_fdma = False
    baseline_positions = np.array(env.uav_positions, copy=True)
    baseline = _call_kernel(
        env, uav_positions=baseline_positions, use_fdma=False, aclr_linear=float(env.aclr_linear)
    )

    # Index (1, 1) is not special: it is one of several (uav, axis) pairs
    # MEASURED to actually move at least one output under a single-ULP nudge on
    # this fixture -- most coordinates do NOT, because a path loss around
    # magnitude ~100 needs roughly a 1e-14 absolute change in distance to move
    # by 1 ULP, and 20*log10(1+eps) for eps ~ 2e-16 falls under that floor for
    # most positions here (e.g. (0, 0) changes nothing at all, checked
    # directly against `_compute_air_to_ground_path_loss`/`_compute_air_to_air_
    # path_loss` for every user and every uav). Picking a coordinate at random
    # would make this negative flaky against the fixture rather than a stable
    # proof of resolution.
    perturbed_positions = baseline_positions.copy()
    perturbed_positions[1, 1] = np.nextafter(perturbed_positions[1, 1], np.inf)
    assert perturbed_positions[1, 1] != baseline_positions[1, 1], (
        "the perturbation did not take, so this negative proves nothing"
    )
    perturbed = _call_kernel(
        env, uav_positions=perturbed_positions, use_fdma=False, aclr_linear=float(env.aclr_linear)
    )

    fields = (
        "access_path_loss", "air_path_loss", "base_path_loss", "user_ipn_dbm",
        "uav_uav_ipn_dbm", "uav_bs_ipn_dbm", "bs_uav_ipn_dbm", "cap_uav_uav",
        "cap_uav_bs", "cap_bs_uav",
    )
    changed = any(
        not np.array_equal(np.asarray(getattr(baseline, field)), np.asarray(getattr(perturbed, field)))
        for field in fields
    )
    assert changed, (
        "a one-ULP change to a uav position changed no output; the comparison "
        "in the tests above is not reading a live quantity"
    )
