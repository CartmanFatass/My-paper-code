from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

import envs.pettingzoo.uav_cpp_backend as backend
from envs.pettingzoo.uav_cpp_backend import step_geometry_batch


def _a2g(
    airborne: np.ndarray,
    ground: np.ndarray,
    *,
    frequency: float,
    los_a: float,
    los_b: float,
    eta_los: float,
    eta_nlos: float,
) -> float:
    delta = airborne - ground
    distance_3d = np.sqrt(np.sum(delta**2))
    distance_2d = np.sqrt(delta[0] ** 2 + delta[1] ** 2)
    safe_distance_3d = max(distance_3d, 1e-6)
    safe_distance_2d = max(distance_2d, 1e-6)
    elevation_angle = np.degrees(np.arctan(abs(delta[2]) / safe_distance_2d))
    p_los = 1.0 / (1.0 + los_a * np.exp(-los_b * (elevation_angle - los_a)))
    p_los = np.clip(p_los, 0.0, 1.0)
    fspl = 20.0 * np.log10(safe_distance_3d) + 20.0 * np.log10(frequency) - 147.55
    pl_los_linear = 10.0 ** (-(fspl + eta_los) / 10.0)
    pl_nlos_linear = 10.0 ** (-(fspl + eta_nlos) / 10.0)
    return float(
        -10.0
        * np.log10(p_los * pl_los_linear + (1.0 - p_los) * pl_nlos_linear)
    )


def _a2a(first: np.ndarray, second: np.ndarray, frequency: float) -> float:
    distance = np.sqrt(np.sum((first - second) ** 2))
    return float(
        20.0 * np.log10(max(distance, 1e-6))
        + 20.0 * np.log10(frequency)
        - 147.55
    )


def _reference(
    uavs: np.ndarray,
    users: np.ndarray,
    bases: np.ndarray,
    velocities: np.ndarray,
    movable: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    time_step = 1.0
    frequency = 2.0e9
    next_uavs = uavs.copy()
    for batch_index in range(uavs.shape[0]):
        for uav_index in range(uavs.shape[1]):
            if movable[batch_index, uav_index]:
                candidate = (
                    uavs[batch_index, uav_index]
                    + velocities[batch_index, uav_index] * time_step
                )
            else:
                candidate = uavs[batch_index, uav_index].copy()
            candidate[0] = np.clip(candidate[0], 0.0, 1000.0)
            candidate[1] = np.clip(candidate[1], 0.0, 1000.0)
            candidate[2] = np.clip(candidate[2], 50.0, 200.0)
            next_uavs[batch_index, uav_index] = candidate

    access = np.empty(
        (uavs.shape[0], uavs.shape[1], users.shape[1]), dtype=np.float64
    )
    air = np.empty(
        (uavs.shape[0], uavs.shape[1], uavs.shape[1]), dtype=np.float64
    )
    base = np.empty(
        (uavs.shape[0], uavs.shape[1], bases.shape[1]), dtype=np.float64
    )
    los = dict(
        frequency=frequency,
        los_a=0.3,
        los_b=5e-4,
        eta_los=1.5,
        eta_nlos=25.0,
    )
    for batch_index in range(uavs.shape[0]):
        for uav_index in range(uavs.shape[1]):
            for user_index in range(users.shape[1]):
                access[batch_index, uav_index, user_index] = _a2g(
                    next_uavs[batch_index, uav_index],
                    users[batch_index, user_index],
                    **los,
                )
            for peer_index in range(uavs.shape[1]):
                air[batch_index, uav_index, peer_index] = _a2a(
                    next_uavs[batch_index, uav_index],
                    next_uavs[batch_index, peer_index],
                    frequency,
                )
            for base_index in range(bases.shape[1]):
                base[batch_index, uav_index, base_index] = _a2g(
                    next_uavs[batch_index, uav_index],
                    bases[batch_index, base_index],
                    **los,
                )
    return next_uavs, access, air, base


def _inputs() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    uavs = np.array(
        [
            [[5.0, 995.0, 55.0], [250.0, 300.0, 120.0], [800.0, 100.0, 195.0]],
            [[100.0, 200.0, 80.0], [500.0, 500.0, 150.0], [900.0, 900.0, 100.0]],
        ],
        dtype=np.float64,
    )
    users = np.array(
        [
            [[0.0, 0.0, 1.5], [400.0, 400.0, 1.5], [900.0, 50.0, 1.5]],
            [[50.0, 75.0, 1.5], [600.0, 400.0, 1.5], [999.0, 999.0, 1.5]],
        ],
        dtype=np.float64,
    )
    bases = np.array(
        [
            [[0.0, 500.0, 0.0], [1000.0, 500.0, 0.0]],
            [[500.0, 0.0, 0.0], [500.0, 1000.0, 0.0]],
        ],
        dtype=np.float64,
    )
    normalized_actions = np.array(
        [
            [[-1.0, 1.0, -1.0], [0.25, -0.5, 0.75], [1.0, 0.0, 1.0]],
            [[0.0, 0.0, 0.0], [-0.2, 0.4, -0.6], [0.8, -0.9, 0.1]],
        ],
        dtype=np.float32,
    )
    velocities = normalized_actions * np.float32(20.0)
    movable = np.array([[True, False, True], [True, True, False]], dtype=np.bool_)
    return uavs, users, bases, velocities, movable


def _run(
    uavs: np.ndarray,
    users: np.ndarray,
    bases: np.ndarray,
    velocities: np.ndarray,
    movable: np.ndarray,
):
    return step_geometry_batch(
        uav_positions=uavs,
        user_positions=users,
        ground_bs_positions=bases,
        prepared_velocities=velocities,
        movable_mask=movable,
        time_step=1.0,
        area_size=1000.0,
        height_range=(50.0, 200.0),
        carrier_frequency=2.0e9,
        environment_type="urban",
    )


def test_native_geometry_matches_independent_sequential_oracle_bitwise():
    inputs = _inputs()
    expected = _reference(*inputs)
    actual = _run(*inputs)
    for candidate, reference in zip(
        (
            actual.next_uav_positions,
            actual.access_path_loss,
            actual.air_path_loss,
            actual.base_path_loss,
        ),
        expected,
    ):
        assert np.array_equal(candidate, reference)


def test_nonbinary_time_step_preserves_float32_delta_and_clip_order():
    uavs = np.array(
        [
            [
                [999.97, 0.05, 199.90],
                [0.02, 999.95, 50.05],
                [123.456789, 654.321987, 111.111111],
            ]
        ],
        dtype=np.float64,
    )
    velocities = np.array(
        [
            [
                [0.10000001, -0.20000003, 0.30000004],
                [-0.10000001, 0.20000003, -0.30000004],
                [0.1234567, -0.7654321, 0.33333334],
            ]
        ],
        dtype=np.float32,
    )
    users = np.array([[[400.0, 500.0, 1.5]]], dtype=np.float64)
    bases = np.array([[[500.0, 500.0, 0.0]]], dtype=np.float64)
    movable = np.ones((1, 3), dtype=np.bool_)
    time_step = 0.37
    expected = uavs + velocities * time_step
    expected[..., 0] = np.clip(expected[..., 0], 0.0, 1000.0)
    expected[..., 1] = np.clip(expected[..., 1], 0.0, 1000.0)
    expected[..., 2] = np.clip(expected[..., 2], 50.0, 200.0)
    actual = step_geometry_batch(
        uav_positions=uavs,
        user_positions=users,
        ground_bs_positions=bases,
        prepared_velocities=velocities,
        movable_mask=movable,
        time_step=time_step,
        area_size=1000.0,
        height_range=(50.0, 200.0),
        carrier_frequency=2.0e9,
        environment_type="urban",
    )
    assert np.array_equal(actual.next_uav_positions, expected)


def test_inactive_action_mutation_cannot_change_geometry():
    uavs, users, bases, velocities, movable = _inputs()
    baseline = _run(uavs, users, bases, velocities, movable)
    mutated = velocities.copy()
    mutated[~movable] *= -1.0
    candidate = _run(uavs, users, bases, mutated, movable)
    assert np.array_equal(candidate.next_uav_positions, baseline.next_uav_positions)
    assert np.array_equal(candidate.access_path_loss, baseline.access_path_loss)
    assert np.array_equal(candidate.air_path_loss, baseline.air_path_loss)
    assert np.array_equal(candidate.base_path_loss, baseline.base_path_loss)


def test_python_boundary_passes_exact_arrays_and_validates_native_payload(monkeypatch):
    uavs, users, bases, velocities, movable = _inputs()
    captured = []

    class FakeNativeModule:
        def step_geometry_batch(self, *args):
            captured.extend(args)
            return (
                uavs.copy(),
                np.zeros((2, 3, 3), dtype=np.float64),
                np.zeros((2, 3, 3), dtype=np.float64),
                np.zeros((2, 3, 2), dtype=np.float64),
            )

    monkeypatch.setattr(
        backend, "load_uav_cpp_backend", lambda **_kwargs: FakeNativeModule()
    )
    result = _run(uavs, users, bases, velocities, movable)
    assert captured[0] is uavs
    assert captured[1] is users
    assert captured[2] is bases
    assert captured[3] is velocities
    assert captured[4] is movable
    assert captured[5:] == [
        1.0,
        1000.0,
        50.0,
        200.0,
        2.0e9,
        0.3,
        5e-4,
        1.5,
        25.0,
    ]
    assert result.next_uav_positions.dtype == np.float64


def test_python_boundary_rejects_native_shape_tamper(monkeypatch):
    class FakeNativeModule:
        def step_geometry_batch(self, *_args):
            return (
                np.zeros((2, 3, 3), dtype=np.float64),
                np.zeros((2, 3, 2), dtype=np.float64),
                np.zeros((2, 3, 3), dtype=np.float64),
                np.zeros((2, 3, 2), dtype=np.float64),
            )

    monkeypatch.setattr(
        backend, "load_uav_cpp_backend", lambda **_kwargs: FakeNativeModule()
    )
    with pytest.raises(RuntimeError, match="output 1"):
        _run(*_inputs())


def test_explicit_build_cache_is_reused_by_a_second_process():
    module = backend.load_uav_cpp_backend()
    artifact = Path(module.__file__).resolve()
    before = (artifact.stat().st_size, artifact.stat().st_mtime_ns)
    repository = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["MAX_JOBS"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        part
        for part in (str(repository), environment.get("PYTHONPATH", ""))
        if part
    )
    script = (
        "from envs.pettingzoo.uav_cpp_backend import load_uav_cpp_backend; "
        "print(load_uav_cpp_backend().__file__)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repository,
        env=environment,
        capture_output=True,
        check=True,
        text=True,
        timeout=300.0,
    )
    reported = Path(completed.stdout.strip().splitlines()[-1]).resolve()
    after = (artifact.stat().st_size, artifact.stat().st_mtime_ns)
    assert reported == artifact
    assert after == before


@pytest.mark.parametrize(
    ("mutation", "error"),
    (
        (lambda values: values.__setitem__(0, values[0].astype(np.float32)), TypeError),
        (lambda values: values.__setitem__(3, values[3][..., :2]), ValueError),
        (lambda values: values[3].__setitem__((0, 0, 0), np.nan), ValueError),
        (lambda values: values.__setitem__(4, values[4][:, :2]), ValueError),
    ),
)
def test_input_validation_fails_before_native_build(mutation, error):
    values = list(_inputs())
    mutation(values)
    with pytest.raises(error):
        _run(*values)
