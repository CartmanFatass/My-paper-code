"""The native geometry kernel must reproduce OUR environment, bit for bit.

`UAV_CPP_BATCH_ENV_BACKEND.md` describes a "proof-sized semantic oracle" as work
to be done, and it was never done: it carries `active_environment_integration=
false`, and `tests/uav_cpp_backend_test.py` -- the kernel's own suite -- never
constructs an environment. It validates shapes, dtypes, fail-closed payloads and
cross-process module reuse against hand-written inputs. All of that can pass
while the kernel computes different physics from the environment it replaces.

So this is the missing half: a real `UAVEnergyAwareRelayEnv`, its actual UAV,
user and ground-station positions, and every path-loss matrix element compared
against the environment's own methods.

The standard is the design doc's own, and it is not a tolerance: "Float evidence
targets bitwise equality by preserving dtype and reduction order. A numeric
tolerance is not a default escape hatch." These assert zero ULP.

Measured 2026-07-29 at commit 7af5d964: 312/312 elements bitwise identical
across access (8x30), air (8x8) and base (8x1), max_ulp 0.
"""
from __future__ import annotations

import numpy as np
import pytest

from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv

backend = pytest.importorskip("ha_ctse_process.uav_cpp_backend")


@pytest.fixture(scope="module", name="native_and_env")
def _native_and_env():
    """Build the kernel once. Skip -- never fail -- if no toolchain is present.

    A missing MSVC/Ninja is a provisioning fact about the machine, not a defect
    in the kernel, and turning it into a red test would train people to ignore
    this file on every box that cannot build.
    """

    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import audit_d7_s_event_aligned as audit

    try:
        backend.load_uav_cpp_backend()
    except backend.UAVCppBackendUnavailable as error:
        pytest.skip(f"native CPU toolchain unavailable: {error}")

    env = UAVEnergyAwareRelayEnv(config=audit.build_config(), energy_stage="S3")
    env.np_random = np.random.RandomState(20260725)
    env.reset(seed=20260725)

    uavs = np.ascontiguousarray(np.asarray(env.uav_positions, dtype=np.float64))
    users = np.ascontiguousarray(np.asarray(env.user_positions, dtype=np.float64))
    bases = np.ascontiguousarray(np.asarray(env.ground_bs_positions, dtype=np.float64))

    geometry = backend.step_geometry_batch(
        uav_positions=uavs[None, ...],
        user_positions=users[None, ...],
        ground_bs_positions=bases[None, ...],
        prepared_velocities=np.zeros((1,) + uavs.shape, dtype=np.float32),
        movable_mask=np.zeros((1, uavs.shape[0]), dtype=np.bool_),
        time_step=float(env.time_step),
        area_size=float(env.area_size),
        height_range=tuple(float(v) for v in env.height_range),
        carrier_frequency=float(env.carrier_frequency),
        environment_type=str(getattr(env, "environment_type", "urban")),
    )
    return env, geometry, uavs, users, bases


def _ulp(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ia = np.ascontiguousarray(a, dtype=np.float64).ravel().view(np.int64).copy()
    ib = np.ascontiguousarray(b, dtype=np.float64).ravel().view(np.int64).copy()
    ia[ia < 0] = np.int64(np.iinfo(np.int64).min) - ia[ia < 0]
    ib[ib < 0] = np.int64(np.iinfo(np.int64).min) - ib[ib < 0]
    return np.abs(ia - ib)


def test_the_ulp_comparison_can_actually_fail() -> None:
    """Otherwise the three assertions below are decorative."""

    same = np.array([1.0, -2.5, 1e9], dtype=np.float64)
    assert int(_ulp(same, same.copy()).max()) == 0
    nudged = same.copy()
    nudged[1] = np.nextafter(nudged[1], np.inf)
    assert int(_ulp(same, nudged).max()) == 1


def test_access_path_loss_matches_the_environment(native_and_env) -> None:
    env, geometry, uavs, users, _ = native_and_env
    expected = np.array(
        [
            [env._compute_air_to_ground_path_loss(uavs[i], users[j]) for j in range(users.shape[0])]
            for i in range(uavs.shape[0])
        ],
        dtype=np.float64,
    )
    assert expected.size == uavs.shape[0] * users.shape[0]
    assert int(_ulp(expected, geometry.access_path_loss[0]).max()) == 0


def test_air_to_air_path_loss_matches_the_environment(native_and_env) -> None:
    env, geometry, uavs, _, _ = native_and_env
    expected = np.array(
        [
            [env._compute_air_to_air_path_loss(uavs[i], uavs[j]) for j in range(uavs.shape[0])]
            for i in range(uavs.shape[0])
        ],
        dtype=np.float64,
    )
    assert int(_ulp(expected, geometry.air_path_loss[0]).max()) == 0


def test_base_path_loss_matches_the_environment(native_and_env) -> None:
    env, geometry, uavs, _, bases = native_and_env
    expected = np.array(
        [
            [env._compute_air_to_ground_path_loss(uavs[i], bases[j]) for j in range(bases.shape[0])]
            for i in range(uavs.shape[0])
        ],
        dtype=np.float64,
    )
    assert int(_ulp(expected, geometry.base_path_loss[0]).max()) == 0


def test_zero_velocity_does_not_move_a_uav(native_and_env) -> None:
    _, geometry, uavs, _, _ = native_and_env
    assert np.array_equal(geometry.next_uav_positions[0], uavs)


def test_environment_type_default_is_shared_by_both_sides(native_and_env) -> None:
    """The match above is only meaningful if both sides picked the same branch.

    Our environment does not set `environment_type`, so its path-loss method
    falls to its own `urban` default while the caller passes `urban` in. If that
    ever diverges, every assertion above compares two different environments and
    still passes.
    """

    env, _, _, _, _ = native_and_env
    assert not hasattr(env, "environment_type"), (
        "environment_type is now set; the oracle must pass it through rather "
        "than relying on both sides defaulting to urban"
    )
