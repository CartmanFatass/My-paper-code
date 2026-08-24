"""Fail-closed registry for production environment backend capabilities.

The registry describes implementation facts only.  It does not authorize an
experiment, allocate compute, or promote a scientific direction.  Production
entry points use :func:`require_cpp_batched_production` after their ordinary
science-card and lease checks.  Reference implementations remain available as
test/debug oracles but are never admitted by this guard.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import ctypes
import hashlib
from importlib.machinery import EXTENSION_SUFFIXES
from pathlib import Path
from types import ModuleType
from typing import Callable, Final, Mapping


CONTINUOUS_ROSTER_TOY: Final[str] = "continuous_roster.toy"
UAV_RELAY_GEOMETRY: Final[str] = "pettingzoo.uav_relay.geometry"
UAV_RELAY_FULL_ENVIRONMENT: Final[str] = "pettingzoo.uav_relay.full_environment"
RIDGEGATE_2Z_FULL_ENVIRONMENT: Final[str] = (
    "semantic_graphon.ridgegate2z.full_environment"
)
ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST: Final[str] = (
    "onlgr.headland90.r03_cal_hold.full_host"
)
SCDMP_UAV_SP_ORDER_VALUE_R02_FULL_HOST: Final[str] = (
    "scdmp.uav_sp_order_value.r02.full_host"
)
VNFC_BPCR_R09_FULL_HOST: Final[str] = "vnfc.bpcr.r09.full_host"
RISP_G_INIT_REACH_R01_FULL_HOST: Final[str] = "risp.g_init_reach.r01.full_host"
ONLGR_TBVUUS_R03_FULL_HOST: Final[str] = "onlgr.tbvuus.r03.full_host"
RCLE_TBCFV_R04_FULL_HOST: Final[str] = "rcle.tbcfv.r04.full_host"
SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST: Final[str] = (
    "scdmp.tbcc_order_value.r02.full_host"
)
VQFP_VNPA_R03_FULL_CHAIN: Final[str] = "vqfp.vnpa.r03.full_chain"
UCOPE_VARIABLE_K_PAID_PROBE_R01_R03_FULL_HOST: Final[str] = (
    "ucope.variable_k_paid_probe.r01_r03.full_host"
)


class ProductionBackendError(RuntimeError):
    """Base class for fail-closed production backend admission errors."""


class ProductionBackendUnsupported(ProductionBackendError):
    """The requested component has no truthful supported native boundary."""


class ProductionBackendUnavailable(ProductionBackendError):
    """A declared native implementation could not be built or loaded."""


@dataclass(frozen=True)
class BackendCapability:
    component: str
    production_supported: bool
    production_backend: str | None
    reference_backend: str
    native_boundary: str | None
    batch_api: bool
    minimum_production_batch_width: int | None
    full_reset_step_cpp: bool
    loader_key: str | None
    unsupported_reason: str | None
    supported_batch_widths: tuple[int, ...] | None = None


_CAPABILITIES: Final[Mapping[str, BackendCapability]] = {
    CONTINUOUS_ROSTER_TOY: BackendCapability(
        component=CONTINUOUS_ROSTER_TOY,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary="synchronous_observation_and_reward_hot_path",
        batch_api=True,
        minimum_production_batch_width=8,
        full_reset_step_cpp=False,
        loader_key="continuous_roster_toy",
        unsupported_reason=None,
    ),
    UAV_RELAY_GEOMETRY: BackendCapability(
        component=UAV_RELAY_GEOMETRY,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary=(
            "position_integration_a2g_a2a_path_loss_and_access_air_base_sinr_tensors"
        ),
        batch_api=True,
        minimum_production_batch_width=1,
        full_reset_step_cpp=False,
        loader_key="uav_relay_geometry",
        unsupported_reason=None,
    ),
    UAV_RELAY_FULL_ENVIRONMENT: BackendCapability(
        component=UAV_RELAY_FULL_ENVIRONMENT,
        production_supported=False,
        production_backend=None,
        reference_backend="python_reference",
        native_boundary=(
            "position_integration_path_loss_and_sinr_tensors_only"
        ),
        batch_api=False,
        minimum_production_batch_width=None,
        full_reset_step_cpp=False,
        loader_key=None,
        unsupported_reason=(
            "the complete reset/step lifecycle, routing, reward, observation, and "
            "RNG state remain Python-owned and have no batched C++ entry point"
        ),
    ),
    RIDGEGATE_2Z_FULL_ENVIRONMENT: BackendCapability(
        component=RIDGEGATE_2Z_FULL_ENVIRONMENT,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_torch_reference",
        native_boundary="complete_ridgegate2z_reset_to_terminal_and_full_suffix_cpp_host",
        batch_api=True,
        minimum_production_batch_width=32,
        full_reset_step_cpp=True,
        loader_key="sgsp_rscf_r01_full_host",
        unsupported_reason=None,
        supported_batch_widths=(32, 64, 128, 256),
    ),
    ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST: BackendCapability(
        component=ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary=(
            "complete_headland90_reset_to_terminal_cpp_kernel_over_materialized_"
            "inputs_with_fixture_only_python_input_adapter"
        ),
        batch_api=True,
        # native_backend.run_native_batch accepts every non-empty materialized
        # fixture sequence and passes its length directly to headland90_run_batch.
        minimum_production_batch_width=1,
        full_reset_step_cpp=True,
        loader_key="onlgr_headland90_r03_cal_hold_full_host",
        unsupported_reason=None,
    ),
    SCDMP_UAV_SP_ORDER_VALUE_R02_FULL_HOST: BackendCapability(
        component=SCDMP_UAV_SP_ORDER_VALUE_R02_FULL_HOST,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary=(
            "complete_tri_uav_sling_corridor_36m_v1_reset_to_terminal_cpp_kernel_"
            "over_materialized_inputs_with_fixture_only_python_input_adapter"
        ),
        batch_api=True,
        minimum_production_batch_width=1,
        full_reset_step_cpp=True,
        loader_key="scdmp_uav_sp_order_value_r02_full_host",
        unsupported_reason=None,
    ),
    VNFC_BPCR_R09_FULL_HOST: BackendCapability(
        component=VNFC_BPCR_R09_FULL_HOST,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary=(
            "complete_bpcr_r09_cpp_host_with_batched_interactive_reset_"
            "observation_conditioned_step_close_and_reset_to_terminal_episode"
        ),
        batch_api=True,
        minimum_production_batch_width=1,
        full_reset_step_cpp=True,
        loader_key="vnfc_bpcr_r09_full_host",
        unsupported_reason=None,
    ),
    RISP_G_INIT_REACH_R01_FULL_HOST: BackendCapability(
        component=RISP_G_INIT_REACH_R01_FULL_HOST,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary=(
            "complete_g_init_r01_cpp_host_with_batched_interactive_reset_raw_"
            "prefix_motion_ack_step_close_and_no_python_environment_fallback"
        ),
        batch_api=True,
        minimum_production_batch_width=1,
        full_reset_step_cpp=True,
        loader_key="risp_g_init_reach_r01_full_host",
        unsupported_reason=None,
    ),
    ONLGR_TBVUUS_R03_FULL_HOST: BackendCapability(
        component=ONLGR_TBVUUS_R03_FULL_HOST,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary=(
            "complete_tbvuus_r03_four_arm_reset_to_terminal_cpp_host_over_"
            "explicit_deterministic_tapes_with_no_python_execution_fallback"
        ),
        batch_api=True,
        minimum_production_batch_width=1,
        full_reset_step_cpp=True,
        loader_key="onlgr_tbvuus_r03_full_host",
        unsupported_reason=None,
    ),
    RCLE_TBCFV_R04_FULL_HOST: BackendCapability(
        component=RCLE_TBCFV_R04_FULL_HOST,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary=(
            "complete_tbcfv_r04_abi2_cpp_host_with_batched_interactive_reset_"
            "step_atomic_event_apply_terminal_close_and_runtime_only_transport_keys"
        ),
        batch_api=True,
        minimum_production_batch_width=1,
        full_reset_step_cpp=True,
        loader_key="rcle_tbcfv_r04_full_host",
        unsupported_reason=None,
        supported_batch_widths=(1, 8, 32),
    ),
    SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST: BackendCapability(
        component=SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST,
        production_supported=True,
        production_backend="cpp",
        reference_backend="python_reference",
        native_boundary=(
            "complete_quad_uav_pallet_gantry_24p5m_v1_tbcc_r02_abi2_cpp_"
            "host_with_batched_reset_renew_native_13_reward_trace_terminal_close"
        ),
        batch_api=True,
        minimum_production_batch_width=8,
        full_reset_step_cpp=True,
        loader_key="scdmp_tbcc_order_value_r02_full_host",
        unsupported_reason=None,
        supported_batch_widths=(8, 12, 32, 120, 144),
    ),
    VQFP_VNPA_R03_FULL_CHAIN: BackendCapability(
        component=VQFP_VNPA_R03_FULL_CHAIN,
        production_supported=False,
        production_backend=None,
        reference_backend="fixture_only_python_fraction_oracle",
        native_boundary=(
            "partial_vqfp_vnpa_r03_exact_philox_rational_geometry_policy_lr_"
            "fixture_and_result_blind_benchmark_only"
        ),
        batch_api=False,
        minimum_production_batch_width=None,
        full_reset_step_cpp=False,
        loader_key=None,
        unsupported_reason=(
            "the native candidate does not yet implement the complete frozen host, "
            "search, evaluation, resampling, terminal, and atomic resume chain"
        ),
        supported_batch_widths=None,
    ),
    UCOPE_VARIABLE_K_PAID_PROBE_R01_R03_FULL_HOST: BackendCapability(
        component=UCOPE_VARIABLE_K_PAID_PROBE_R01_R03_FULL_HOST,
        production_supported=True,
        production_backend="cpp",
        reference_backend="test_only_python_scalar_oracle",
        native_boundary=(
            "complete_ucope_r01_r03_batched_reset_root_probe_tail_terminal_close_"
            "cpp_host_with_counter_addressed_fp32_transitions_potential_population_"
            "and_all_six_arm_semantic_primitives_with_no_python_fallback"
        ),
        batch_api=True,
        minimum_production_batch_width=8,
        full_reset_step_cpp=True,
        loader_key="ucope_variable_k_paid_probe_r01_r03_full_host",
        unsupported_reason=None,
        supported_batch_widths=(8, 32, 256, 768),
    ),
}


def backend_capabilities() -> tuple[dict[str, object], ...]:
    """Return a stable, serializable view of every explicit declaration."""

    return tuple(asdict(_CAPABILITIES[name]) for name in sorted(_CAPABILITIES))


def backend_capability(component: str) -> BackendCapability:
    """Return one declaration; unknown components fail closed."""

    try:
        return _CAPABILITIES[str(component)]
    except KeyError as error:
        raise ProductionBackendUnsupported(
            f"no production backend declaration exists for {component!r}"
        ) from error


def _continuous_roster_loader(*, build_root: str | Path | None) -> ModuleType:
    from envs.continuous_roster.cpp_backend import (
        load_continuous_roster_toy_cpp_backend,
    )

    return load_continuous_roster_toy_cpp_backend(build_root=build_root)


def _uav_geometry_loader(*, build_root: str | Path | None) -> ModuleType:
    from envs.pettingzoo.uav_cpp_backend import load_uav_cpp_backend

    return load_uav_cpp_backend(build_root=build_root)


def _sgsp_rscf_r01_loader(*, build_root: str | Path | None) -> ModuleType:
    from experiments.candidates.semantic_graphon_shared_policy_rscf_r01.native_loader import (
        require_cpp_batched_backend,
    )

    return require_cpp_batched_backend(build_root=build_root)


def _onlgr_headland90_loader(*, build_root: str | Path | None) -> ctypes.CDLL:
    if build_root is not None:
        raise ValueError(
            "the source-keyed HEADLAND-90 loader does not accept a build_root override"
        )
    from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.native_backend import (
        require_cpp_batched_backend,
    )

    # Do not call production_preflight(): it additionally evaluates direction
    # activity authority, while this shared guard verifies implementation only.
    return require_cpp_batched_backend()


def _scdmp_uav_sp_order_value_loader(
    *, build_root: str | Path | None
) -> ctypes.CDLL:
    if build_root is not None:
        raise ValueError(
            "the source-keyed SCDMP UAV order-value loader does not accept a "
            "build_root override"
        )
    from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.native_backend import (
        require_cpp_batched_backend,
    )

    # Do not call production_preflight(): it additionally evaluates direction
    # activity authority, while this shared guard verifies implementation only.
    return require_cpp_batched_backend()


def _vnfc_bpcr_r09_loader(*, build_root: str | Path | None) -> ctypes.CDLL:
    from experiments.candidates.variable_n_fleet_churn_bpcr_r09.native_backend import (
        require_cpp_batched_backend,
    )

    return require_cpp_batched_backend(build_root=build_root)


def _risp_g_init_reach_r01_loader(
    *, build_root: str | Path | None
) -> ctypes.CDLL:
    from experiments.candidates.renewal_indexed_score_plasticity.g_init_r01_native_backend import (
        require_cpp_batched_backend,
    )

    # This is the functional implementation guard only.  The candidate-owned
    # production preflight additionally carries direction activity authority.
    return require_cpp_batched_backend(build_root=build_root)


def _onlgr_tbvuus_r03_loader(*, build_root: str | Path | None) -> ctypes.CDLL:
    if build_root is not None:
        raise ValueError(
            "the source-keyed ONLGR TBVUUS r03 loader does not accept a "
            "build_root override"
        )
    from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03.native_backend import (
        require_cpp_batched_backend,
    )

    return require_cpp_batched_backend()


def _rcle_tbcfv_r04_loader(*, build_root: str | Path | None) -> ctypes.CDLL:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.native_backend import (
        require_cpp_batched_backend,
    )

    return require_cpp_batched_backend(build_root=build_root)


def _scdmp_tbcc_order_value_r02_loader(
    *, build_root: str | Path | None
) -> ctypes.CDLL:
    from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.native_backend import (
        require_cpp_batched_backend,
    )

    return require_cpp_batched_backend(build_root=build_root)


def _vqfp_vnpa_r03_loader(*, build_root: str | Path | None) -> ctypes.CDLL:
    from experiments.candidates.vqfp_vnpa_r03.native_backend import (
        require_cpp_batched_backend,
    )

    return require_cpp_batched_backend(build_root=build_root)


def _ucope_variable_k_paid_probe_r01_r03_loader(
    *, build_root: str | Path | None
) -> ctypes.CDLL:
    from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.native_backend import (
        require_cpp_batched_backend,
    )

    return require_cpp_batched_backend(build_root=build_root)


_LOADERS: Final[Mapping[str, Callable[..., object]]] = {
    "continuous_roster_toy": _continuous_roster_loader,
    "uav_relay_geometry": _uav_geometry_loader,
    "sgsp_rscf_r01_full_host": _sgsp_rscf_r01_loader,
    "onlgr_headland90_r03_cal_hold_full_host": _onlgr_headland90_loader,
    "scdmp_uav_sp_order_value_r02_full_host": _scdmp_uav_sp_order_value_loader,
    "vnfc_bpcr_r09_full_host": _vnfc_bpcr_r09_loader,
    "risp_g_init_reach_r01_full_host": _risp_g_init_reach_r01_loader,
    "onlgr_tbvuus_r03_full_host": _onlgr_tbvuus_r03_loader,
    "rcle_tbcfv_r04_full_host": _rcle_tbcfv_r04_loader,
    "scdmp_tbcc_order_value_r02_full_host": _scdmp_tbcc_order_value_r02_loader,
    "vqfp_vnpa_r03_full_chain": _vqfp_vnpa_r03_loader,
    "ucope_variable_k_paid_probe_r01_r03_full_host": (
        _ucope_variable_k_paid_probe_r01_r03_loader
    ),
}


def _module_identity(module: object) -> dict[str, object]:
    if isinstance(module, ModuleType):
        path_value = getattr(module, "__file__", None)
        binding_kind = "extension_module"
    elif isinstance(module, ctypes.CDLL):
        # ctypes exposes an ``<uninitialized>`` class placeholder; only an
        # instance-owned name proves that a concrete library was loaded.
        path_value = vars(module).get("_name")
        binding_kind = "ctypes_cdll"
    else:
        raise ProductionBackendUnavailable(
            "native build/load preflight returned neither an extension module nor "
            "a ctypes CDLL"
        )
    if not path_value:
        raise ProductionBackendUnavailable(
            "native build/load preflight returned a native binding without an "
            "artifact path"
        )
    path = Path(path_value).resolve()
    if not path.is_file():
        raise ProductionBackendUnavailable(
            f"native build/load preflight artifact is missing: {path}"
        )
    if binding_kind == "extension_module" and not any(
        str(path).endswith(suffix) for suffix in EXTENSION_SUFFIXES
    ):
        raise ProductionBackendUnavailable(
            f"native extension module artifact has an invalid suffix: {path}"
        )
    return {
        "module": str(getattr(module, "__name__", type(module).__name__)),
        "binding_kind": binding_kind,
        "artifact": str(path),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def require_cpp_batched_production(
    component: str,
    *,
    backend: str,
    batch_width: int,
    build_root: str | Path | None = None,
) -> dict[str, object]:
    """Require a declared batched C++ boundary and load it before activity.

    This is deliberately a preactivity check rather than an implicit fallback.
    A positive width records the caller's declared production width; it does
    not claim that the entire environment is native when only a hot path is.
    """

    capability = backend_capability(component)
    if not capability.production_supported:
        raise ProductionBackendUnsupported(
            f"{component} is not production-supported: "
            f"{capability.unsupported_reason}"
        )
    if str(backend) != "cpp" or capability.production_backend != "cpp":
        raise ProductionBackendUnsupported(
            f"{component} production requires backend='cpp'; reference backends "
            "are test/debug oracles only"
        )
    if isinstance(batch_width, bool) or not isinstance(batch_width, int):
        raise TypeError("production batch_width must be an integer")
    if batch_width <= 0:
        raise ValueError("production batch_width must be positive")
    minimum_width = capability.minimum_production_batch_width
    if minimum_width is not None and batch_width < minimum_width:
        raise ProductionBackendUnsupported(
            f"{component} production batch_width must be >= {minimum_width}; "
            f"declared width was {batch_width}"
        )
    supported_widths = capability.supported_batch_widths
    if supported_widths is not None and batch_width not in supported_widths:
        raise ProductionBackendUnsupported(
            f"{component} production batch_width must be one of "
            f"{supported_widths}; declared width was {batch_width}"
        )
    if not capability.batch_api or capability.loader_key is None:
        raise ProductionBackendUnsupported(
            f"{component} has no declared batched native loader"
        )
    loader = _LOADERS[capability.loader_key]
    try:
        module = loader(build_root=build_root)
        identity = _module_identity(module)
    except ProductionBackendError:
        raise
    except Exception as error:
        raise ProductionBackendUnavailable(
            f"{component} native build/load preflight failed"
        ) from error
    return {
        "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
        "component": capability.component,
        "backend": "cpp",
        "batch_width": batch_width,
        "native_boundary": capability.native_boundary,
        "full_reset_step_cpp": capability.full_reset_step_cpp,
        "python_fallback": False,
        "native": identity,
    }
