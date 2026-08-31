import ctypes

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.host import (
    NativeBackendUnavailable, NativeContract, TestOnlyNativeBackend, Trajectory,
    admit_native_backend, native_endpoint,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts import core


def test_endpoint_formula_and_strict_support():
    assert native_endpoint(3, 3, 0) == pytest.approx(1.0)
    assert native_endpoint(0, 0, 1) == 0.0
    with pytest.raises(ValueError):
        native_endpoint(3.1, 1, 0)


def test_endpoint_is_reduced_per_episode_not_from_averaged_components():
    episode_mean = (native_endpoint(3, 0, 0) + native_endpoint(0, 3, 0)) / 2
    endpoint_of_means = 0.65 * 3 / 6 + 0.25 * 1.5 / 3 + 0.10
    assert episode_mean != endpoint_of_means
    with pytest.raises(ValueError, match="integer counts"):
        native_endpoint(1.5, 1.5, 0)


def test_production_rejects_python_and_test_only_fallback(tmp_path):
    backend = TestOnlyNativeBackend()
    with pytest.raises(NativeBackendUnavailable, match="TEST_ONLY"):
        admit_native_backend(backend, production=True)
    assert admit_native_backend(backend, production=False) is backend

    class PythonFake:
        contract = NativeContract(
            core.HOST_ID, core.SOURCE_ID, core.NATIVE_COMPONENT, core.NATIVE_ABI,
            "FRRIE_NATIVE_CTYPES_V1", 8, 1, 1,
        )
        native_entrypoint = staticmethod(lambda: None)

        @staticmethod
        def preflight(resources):
            return {}

        @staticmethod
        def rollout(request):
            return {}

    with pytest.raises(NativeBackendUnavailable, match="package-owned"):
        admit_native_backend(PythonFake(), production=True)

    callback = ctypes.CFUNCTYPE(ctypes.c_int)(lambda: 0)
    callback.__name__ = "frrie_ridgegate2z_rollout_v1"

    class CallbackFake(PythonFake):
        native_entrypoint = callback

    with pytest.raises(NativeBackendUnavailable, match="package-owned"):
        admit_native_backend(CallbackFake(), production=True)


def test_shadow_requires_direct_native_state_noninterference():
    backend = TestOnlyNativeBackend()
    request = {
        "trajectory_kind": "SHADOW", "purpose": "TEST_ONLY",
        "intervention": "TEST_ONLY", "roster": 3,
        "seed_block": "TEST_ONLY", "update": 0, "episode": 0,
        "tape_contract": {
            "schema": "FRRIE_ADDRESSED_TAPE_V1", "seed_block": "TEST_ONLY",
            "purpose": "TEST_ONLY", "roster": 3, "update": 0, "episode": 0,
        },
    }
    result = backend.rollout(request)
    Trajectory.from_backend(result, "SHADOW", request)
    result["state_after"] = {"schema": "TEST_ONLY_NATIVE_STATE_V1", "step": 99}
    with pytest.raises(ValueError, match="changed native state"):
        Trajectory.from_backend(result, "SHADOW", request)


def test_architecture_shapes_and_count():
    from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import architecture_parameter_count, architecture_shapes
    assert architecture_parameter_count() == 35_513
    assert architecture_shapes()["message_encoder.weight_ih"] == (64, 22)
    assert architecture_shapes()["gru.weight_input_zrn"] == (192, 55)
    assert architecture_shapes()["beta"] == (3, 3, 2)
