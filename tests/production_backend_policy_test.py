from __future__ import annotations

import ctypes
import hashlib
import math
from pathlib import Path
from types import ModuleType

import pytest

from envs.native import production_backend as policy


def _fake_native_module(path: Path, name: str = "fake_native") -> ModuleType:
    path.write_bytes(b"native-test-artifact")
    module = ModuleType(name)
    module.__file__ = str(path)
    return module


def test_registry_truthfully_separates_native_slices_from_full_environments() -> None:
    capabilities = {
        row["component"]: row for row in policy.backend_capabilities()
    }

    roster = capabilities[policy.CONTINUOUS_ROSTER_TOY]
    assert roster["production_supported"] is True
    assert roster["production_backend"] == "cpp"
    assert roster["batch_api"] is True
    assert roster["minimum_production_batch_width"] == 8
    assert roster["full_reset_step_cpp"] is False

    geometry = capabilities[policy.UAV_RELAY_GEOMETRY]
    assert geometry["production_supported"] is True
    assert geometry["production_backend"] == "cpp"
    assert geometry["batch_api"] is True
    assert geometry["minimum_production_batch_width"] == 1
    assert geometry["full_reset_step_cpp"] is False
    assert "sinr_tensors" in geometry["native_boundary"]

    onlgr = capabilities[policy.ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST]
    assert onlgr["production_supported"] is True
    assert onlgr["production_backend"] == "cpp"
    assert onlgr["batch_api"] is True
    assert onlgr["minimum_production_batch_width"] == 1
    assert onlgr["full_reset_step_cpp"] is True
    assert "reset_to_terminal_cpp_kernel" in onlgr["native_boundary"]
    assert "fixture_only_python_input_adapter" in onlgr["native_boundary"]

    scdmp = capabilities[policy.SCDMP_UAV_SP_ORDER_VALUE_R02_FULL_HOST]
    assert scdmp["production_supported"] is True
    assert scdmp["production_backend"] == "cpp"
    assert scdmp["batch_api"] is True
    assert scdmp["minimum_production_batch_width"] == 1
    assert scdmp["full_reset_step_cpp"] is True
    assert (
        scdmp["native_boundary"]
        == "complete_tri_uav_sling_corridor_36m_v1_reset_to_terminal_cpp_kernel_"
        "over_materialized_inputs_with_fixture_only_python_input_adapter"
    )

    vnfc = capabilities[policy.VNFC_BPCR_R09_FULL_HOST]
    assert vnfc["production_supported"] is True
    assert vnfc["production_backend"] == "cpp"
    assert vnfc["batch_api"] is True
    assert vnfc["minimum_production_batch_width"] == 1
    assert vnfc["full_reset_step_cpp"] is True
    assert (
        vnfc["native_boundary"]
        == "complete_bpcr_r09_cpp_host_with_batched_interactive_reset_"
        "observation_conditioned_step_close_and_reset_to_terminal_episode"
    )

    risp = capabilities[policy.RISP_G_INIT_REACH_R01_FULL_HOST]
    assert risp["production_supported"] is True
    assert risp["production_backend"] == "cpp"
    assert risp["batch_api"] is True
    assert risp["minimum_production_batch_width"] == 1
    assert risp["full_reset_step_cpp"] is True
    assert (
        risp["native_boundary"]
        == "complete_g_init_r01_cpp_host_with_batched_interactive_reset_raw_"
        "prefix_motion_ack_step_close_and_no_python_environment_fallback"
    )

    tbvuus = capabilities[policy.ONLGR_TBVUUS_R03_FULL_HOST]
    assert tbvuus["production_supported"] is True
    assert tbvuus["production_backend"] == "cpp"
    assert tbvuus["batch_api"] is True
    assert tbvuus["minimum_production_batch_width"] == 1
    assert tbvuus["full_reset_step_cpp"] is True
    assert (
        tbvuus["native_boundary"]
        == "complete_tbvuus_r03_four_arm_reset_to_terminal_cpp_host_over_"
        "explicit_deterministic_tapes_with_no_python_execution_fallback"
    )

    rcle = capabilities[policy.RCLE_TBCFV_R04_FULL_HOST]
    assert rcle["component"] == "rcle.tbcfv.r04.full_host"
    assert rcle["production_supported"] is True
    assert rcle["production_backend"] == "cpp"
    assert rcle["batch_api"] is True
    assert rcle["minimum_production_batch_width"] == 1
    assert rcle["supported_batch_widths"] == (1, 8, 32)
    assert rcle["full_reset_step_cpp"] is True
    assert (
        rcle["native_boundary"]
        == "complete_tbcfv_r04_abi2_cpp_host_with_batched_interactive_reset_"
        "step_atomic_event_apply_terminal_close_and_runtime_only_transport_keys"
    )

    tbcc = capabilities[policy.SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST]
    assert tbcc["component"] == "scdmp.tbcc_order_value.r02.full_host"
    assert tbcc["production_supported"] is True
    assert tbcc["production_backend"] == "cpp"
    assert tbcc["batch_api"] is True
    assert tbcc["minimum_production_batch_width"] == 8
    assert tbcc["supported_batch_widths"] == (8, 12, 32, 120, 144)
    assert tbcc["full_reset_step_cpp"] is True
    assert (
        tbcc["native_boundary"]
        == "complete_quad_uav_pallet_gantry_24p5m_v1_tbcc_r02_abi2_cpp_"
        "host_with_batched_reset_renew_native_13_reward_trace_terminal_close"
    )

    for component in (
        policy.UAV_RELAY_FULL_ENVIRONMENT,
        policy.RIDGEGATE_2Z_FULL_ENVIRONMENT,
    ):
        declaration = capabilities[component]
        assert declaration["production_supported"] is False
        assert declaration["production_backend"] is None
        assert declaration["batch_api"] is False
        assert declaration["minimum_production_batch_width"] is None
        assert declaration["unsupported_reason"]


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_preactivity_guard_requires_cpp_batch_and_native_load(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, batch_width: int
) -> None:
    artifact = tmp_path / f"native-{batch_width}.pyd"
    calls: list[object] = []

    def load(*, build_root):
        calls.append(build_root)
        return _fake_native_module(artifact)

    monkeypatch.setitem(
        policy._LOADERS,
        "uav_relay_geometry",
        load,
    )
    result = policy.require_cpp_batched_production(
        policy.UAV_RELAY_GEOMETRY,
        backend="cpp",
        batch_width=batch_width,
        build_root=tmp_path / "build",
    )

    assert calls == [tmp_path / "build"]
    assert result["schema"] == "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1"
    assert result["backend"] == "cpp"
    assert result["batch_width"] == batch_width
    assert result["python_fallback"] is False
    assert result["full_reset_step_cpp"] is False
    assert result["native"]["artifact"] == str(artifact.resolve())
    assert len(result["native"]["artifact_sha256"]) == 64


def test_reference_unknown_and_unsupported_paths_fail_before_native_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(**_kwargs):
        raise AssertionError("native loader must not run")

    monkeypatch.setitem(policy._LOADERS, "uav_relay_geometry", unexpected)
    with pytest.raises(policy.ProductionBackendUnsupported, match="backend='cpp'"):
        policy.require_cpp_batched_production(
            policy.UAV_RELAY_GEOMETRY,
            backend="python_reference",
            batch_width=8,
        )
    with pytest.raises(policy.ProductionBackendUnsupported, match="not production-supported"):
        policy.require_cpp_batched_production(
            policy.UAV_RELAY_FULL_ENVIRONMENT,
            backend="cpp",
            batch_width=8,
        )
    with pytest.raises(policy.ProductionBackendUnsupported, match="no production backend"):
        policy.require_cpp_batched_production(
            "unknown.environment",
            backend="cpp",
            batch_width=8,
        )


@pytest.mark.parametrize("backend", ("python_reference", "python", "cuda"))
def test_onlgr_wrong_backend_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "onlgr_headland90_r03_cal_hold_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="backend='cpp'"):
        policy.require_cpp_batched_production(
            policy.ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
            backend=backend,
            batch_width=1,
        )


def test_ctypes_cdll_identity_uses_existing_named_artifact(tmp_path: Path) -> None:
    artifact = tmp_path / "headland90-test.dll"
    artifact.write_bytes(b"headland90-test-artifact")
    library = ctypes.CDLL.__new__(ctypes.CDLL)
    library._name = str(artifact)

    identity = policy._module_identity(library)

    assert identity["binding_kind"] == "ctypes_cdll"
    assert identity["artifact"] == str(artifact.resolve())
    assert len(identity["artifact_sha256"]) == 64


def test_ctypes_cdll_without_name_fails_closed() -> None:
    library = ctypes.CDLL.__new__(ctypes.CDLL)

    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="without an artifact path",
    ):
        policy._module_identity(library)


def test_ctypes_cdll_with_missing_named_artifact_fails_closed(
    tmp_path: Path,
) -> None:
    library = ctypes.CDLL.__new__(ctypes.CDLL)
    library._name = str(tmp_path / "missing-headland90.dll")

    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="artifact is missing",
    ):
        policy._module_identity(library)


def test_onlgr_build_root_override_is_wrapped_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="native build/load preflight failed",
    ) as raised:
        policy.require_cpp_batched_production(
            policy.ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
            backend="cpp",
            batch_width=1,
            build_root=tmp_path / "unsupported-build-root",
        )

    assert isinstance(raised.value.__cause__, ValueError)
    assert "does not accept a build_root override" in str(raised.value.__cause__)


@pytest.mark.parametrize("backend", ("python_reference", "python", "cuda"))
def test_scdmp_uav_order_value_wrong_backend_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "scdmp_uav_sp_order_value_r02_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="backend='cpp'"):
        policy.require_cpp_batched_production(
            policy.SCDMP_UAV_SP_ORDER_VALUE_R02_FULL_HOST,
            backend=backend,
            batch_width=1,
        )


def test_scdmp_uav_order_value_build_root_override_is_wrapped_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="native build/load preflight failed",
    ) as raised:
        policy.require_cpp_batched_production(
            policy.SCDMP_UAV_SP_ORDER_VALUE_R02_FULL_HOST,
            backend="cpp",
            batch_width=1,
            build_root=tmp_path / "unsupported-build-root",
        )

    assert isinstance(raised.value.__cause__, ValueError)
    assert "does not accept a build_root override" in str(raised.value.__cause__)


@pytest.mark.parametrize("backend", ("python_reference", "python", "cuda"))
def test_vnfc_bpcr_wrong_backend_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "vnfc_bpcr_r09_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="backend='cpp'"):
        policy.require_cpp_batched_production(
            policy.VNFC_BPCR_R09_FULL_HOST,
            backend=backend,
            batch_width=1,
        )


def test_vnfc_bpcr_build_root_override_is_wrapped_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="native build/load preflight failed",
    ) as raised:
        policy.require_cpp_batched_production(
            policy.VNFC_BPCR_R09_FULL_HOST,
            backend="cpp",
            batch_width=1,
            build_root=tmp_path / "unsupported-build-root",
        )

    assert isinstance(raised.value.__cause__, ValueError)
    assert "does not accept build_root override" in str(raised.value.__cause__)


@pytest.mark.parametrize("backend", ("python_reference", "python", "cuda"))
def test_risp_g_init_wrong_backend_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "risp_g_init_reach_r01_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="backend='cpp'"):
        policy.require_cpp_batched_production(
            policy.RISP_G_INIT_REACH_R01_FULL_HOST,
            backend=backend,
            batch_width=1,
        )


def test_risp_g_init_real_shared_loader_uses_source_keyed_build_root(
    tmp_path: Path,
) -> None:
    from experiments.candidates.renewal_indexed_score_plasticity import (
        g_init_r01_native_backend as native_backend,
    )

    result = policy.require_cpp_batched_production(
        policy.RISP_G_INIT_REACH_R01_FULL_HOST,
        backend="cpp",
        batch_width=1,
        build_root=tmp_path,
    )
    cache_root, build_key = native_backend._current_loader_cache_key(tmp_path)
    library = native_backend.require_cpp_batched_backend(build_root=tmp_path)
    artifact = Path(vars(library)["_name"]).resolve()

    assert cache_root == str(tmp_path.resolve())
    assert artifact.parent == tmp_path.resolve() / build_key
    assert result["native"]["artifact"] == str(artifact)
    assert result["native"]["artifact_sha256"] == hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_risp_g_init_real_shared_preflight_reports_exact_abi_without_fallback(
    batch_width: int,
) -> None:
    from experiments.candidates.renewal_indexed_score_plasticity import (
        g_init_r01_native_backend as native_backend,
    )

    result = policy.require_cpp_batched_production(
        policy.RISP_G_INIT_REACH_R01_FULL_HOST,
        backend="cpp",
        batch_width=batch_width,
    )
    library = native_backend.require_cpp_batched_backend()
    artifact = Path(vars(library)["_name"]).resolve()

    assert result["component"] == policy.RISP_G_INIT_REACH_R01_FULL_HOST
    assert result["batch_width"] == batch_width
    assert result["full_reset_step_cpp"] is True
    assert result["python_fallback"] is False
    assert result["native"]["binding_kind"] == "ctypes_cdll"
    assert Path(result["native"]["artifact"]).resolve() == artifact
    assert result["native"]["artifact_sha256"] == hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()
    assert library.risp_g_init_r01_abi_version() == native_backend.NATIVE_ABI_VERSION
    assert {
        "reset_input": library.risp_g_init_r01_sizeof_reset_input(),
        "step_input": library.risp_g_init_r01_sizeof_step_input(),
        "extended_step_input": library.risp_g_init_r01_sizeof_extended_step_input(),
        "transition_output": library.risp_g_init_r01_sizeof_transition_output(),
    } == {
        "reset_input": 160,
        "step_input": 64,
        "extended_step_input": 288,
        "transition_output": 104,
    }


@pytest.mark.parametrize("backend", ("python_reference", "python", "cuda"))
def test_onlgr_tbvuus_wrong_backend_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "onlgr_tbvuus_r03_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="backend='cpp'"):
        policy.require_cpp_batched_production(
            policy.ONLGR_TBVUUS_R03_FULL_HOST,
            backend=backend,
            batch_width=1,
        )


def test_onlgr_tbvuus_build_root_override_is_wrapped_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="native build/load preflight failed",
    ) as raised:
        policy.require_cpp_batched_production(
            policy.ONLGR_TBVUUS_R03_FULL_HOST,
            backend="cpp",
            batch_width=1,
            build_root=tmp_path / "unsupported-build-root",
        )

    assert isinstance(raised.value.__cause__, ValueError)
    assert "does not accept a build_root override" in str(raised.value.__cause__)


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_onlgr_tbvuus_real_shared_preflight_reports_current_exact_artifact(
    batch_width: int,
) -> None:
    from experiments.candidates.opportunity_normalized_lease_gated_rebinding.tbvuus_r03 import (
        native_backend,
    )

    result = policy.require_cpp_batched_production(
        policy.ONLGR_TBVUUS_R03_FULL_HOST,
        backend="cpp",
        batch_width=batch_width,
    )
    identity = native_backend.native_artifact_identity()
    library = native_backend.require_cpp_batched_backend()

    assert result["component"] == policy.ONLGR_TBVUUS_R03_FULL_HOST
    assert result["batch_width"] == batch_width
    assert result["full_reset_step_cpp"] is True
    assert result["python_fallback"] is False
    assert result["native"]["binding_kind"] == "ctypes_cdll"
    assert Path(result["native"]["artifact"]).resolve() == Path(
        identity["path"]
    ).resolve()
    assert result["native"]["artifact_sha256"] == identity["sha256"]
    assert identity["source_sha256"] == (
        "86e49d53b6e7cbeb8661c80fc30280be048436153e86384734f07e6c2b4dcbfa"
    )
    assert identity["build_key"] == (
        "0c0651c7bf47c9a1dc21048c30afb57558b5ed2df98fb745f62dc73ecb683072"
    )
    assert identity["sha256"] == (
        "2e4394929a61ee5f62f2e70370ff5fa5f10ba82650fd6ae8be4becd447f5bc0d"
    )
    assert library.tbvuus_abi_version() == native_backend.NATIVE_ABI_VERSION
    assert {
        "input_size": library.tbvuus_input_size(),
        "tick_size": library.tbvuus_tick_size(),
        "output_size": library.tbvuus_output_size(),
    } == {
        "input_size": 12760,
        "tick_size": 760,
        "output_size": 109504,
    }


@pytest.mark.parametrize("backend", ("python_reference", "python", "cuda"))
def test_rcle_tbcfv_wrong_backend_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "rcle_tbcfv_r04_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="backend='cpp'"):
        policy.require_cpp_batched_production(
            policy.RCLE_TBCFV_R04_FULL_HOST,
            backend=backend,
            batch_width=1,
        )


def test_rcle_tbcfv_unvalidated_width_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "rcle_tbcfv_r04_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="one of"):
        policy.require_cpp_batched_production(
            policy.RCLE_TBCFV_R04_FULL_HOST,
            backend="cpp",
            batch_width=2,
        )


def test_rcle_tbcfv_real_explicit_build_root_is_source_keyed(
    tmp_path: Path,
) -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (
        native_backend,
    )

    result = policy.require_cpp_batched_production(
        policy.RCLE_TBCFV_R04_FULL_HOST,
        backend="cpp",
        batch_width=1,
        build_root=tmp_path,
    )
    identity = native_backend.native_artifact_identity(build_root=tmp_path)

    assert identity["resolved_build_root"] == str(tmp_path.resolve())
    assert Path(identity["path"]).parent == tmp_path.resolve() / identity["build_key"]
    assert Path(result["native"]["artifact"]).resolve() == Path(
        identity["path"]
    ).resolve()
    assert result["native"]["artifact_sha256"] == identity["sha256"]


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_rcle_tbcfv_real_default_receipt_reports_exact_abi_magic_and_artifact(
    batch_width: int,
) -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (
        native_backend,
    )

    result = policy.require_cpp_batched_production(
        policy.RCLE_TBCFV_R04_FULL_HOST,
        backend="cpp",
        batch_width=batch_width,
    )
    identity = native_backend.native_artifact_identity()
    library = native_backend.require_cpp_batched_backend()

    assert result["component"] == policy.RCLE_TBCFV_R04_FULL_HOST
    assert result["batch_width"] == batch_width
    assert result["full_reset_step_cpp"] is True
    assert result["python_fallback"] is False
    assert result["native"]["binding_kind"] == "ctypes_cdll"
    assert Path(result["native"]["artifact"]).resolve() == Path(
        identity["path"]
    ).resolve()
    assert result["native"]["artifact_sha256"] == identity["sha256"]
    assert identity["source_sha256"] == (
        "ddb14c33d822924b21b872713745f242fee92f16b4329efed439a1e2b816a910"
    )
    assert identity["build_key"] == (
        "8e80ba3cf3ba026c486d75d330aa9a99f820fe60803334dce7841032a48a5f91"
    )
    assert identity["sha256"] == (
        "023eecbc0a69710ee6a4fe06aa8e1b0b5165870bbcfc5a7ae2198e86372baf15"
    )
    assert identity["size"] == 156160
    assert identity["sha256"] != (
        "69563e66d594f1ed40a249d7433699fd9529236c76e8eaa799a3f57517799790"
    )
    assert library.rcle_tbcfv_abi_version() == 2
    assert library.rcle_tbcfv_abi_version() != 1
    assert library.rcle_tbcfv_fixture_magic() == 0x52434C4554424347
    assert library.rcle_tbcfv_fixture_magic() != 0x52434C4554424346
    assert {
        "fixture_input": library.rcle_tbcfv_sizeof_fixture_input(),
        "step_input": library.rcle_tbcfv_sizeof_step_input(),
        "event_input": library.rcle_tbcfv_sizeof_event_input(),
        "snapshot": library.rcle_tbcfv_sizeof_snapshot(),
    } == {
        "fixture_input": 224,
        "step_input": 64,
        "event_input": 64,
        "snapshot": 464,
    }
    assert callable(library.rcle_tbcfv_apply_event_batch)


def _rcle_claim_rows(pre_n: int, post_n: int, salt: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple((rank + clock + salt) % 6 for rank in range(pre_n if clock < 6 else post_n))
        for clock in range(16)
    )


def _rcle_expansion_case():
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import (
        ACTIVE_CONTINUATION,
        EpisodeTape,
        FixtureSpec,
    )

    keys = tuple(range(100, 107))
    return EpisodeTape(
        FixtureSpec(
            initial_keys=keys,
            initial_positions=(3, 19, 34, 52, 68, 87, 103),
            after_keys=keys + (107, 108),
            after_positions=(-1,) * 7 + (-2, -2),
            event_condition=ACTIVE_CONTINUATION,
        ),
        _rcle_claim_rows(7, 9, 0),
        event_newcomer_positions=(43, 116),
    )


def _rcle_contraction_case():
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import (
        EpisodeTape,
        FixtureSpec,
        NEW_EPOCH,
    )

    keys = tuple(range(200, 209))
    return EpisodeTape(
        FixtureSpec(
            initial_keys=keys,
            initial_positions=(1, 14, 28, 41, 55, 70, 84, 99, 113),
            after_keys=(200, 201, 203, 204, 206, 207, 208),
            after_positions=(-1,) * 7,
            event_condition=NEW_EPOCH,
            omega_plus=10,
            kappa_plus=3,
        ),
        _rcle_claim_rows(9, 7, 2),
    )


def _rcle_crossing_case():
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import (
        EpisodeTape,
        FixtureSpec,
    )

    keys = tuple(range(400, 406))
    claims = [(3, 0, 2, 3, 4, 5)]
    claims.extend((0, 1, 2, 3, 4, 5) for _ in range(15))
    return EpisodeTape(
        FixtureSpec(
            initial_keys=keys,
            initial_positions=(0, 1, 40, 60, 80, 100),
            after_keys=keys,
            after_positions=(-1,) * 6,
        ),
        tuple(claims),
    )


def test_rcle_tbcfv_shared_abi2_event_boundary_is_batch_atomic_and_actor_hidden() -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (
        native_backend,
    )
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import (
        EventInput,
        StepInput,
    )

    active = _rcle_expansion_case()
    epoch = _rcle_contraction_case()
    cases = (active, epoch, active, epoch, active, epoch, active, epoch)
    batch = native_backend.reset_native_batch(tuple(case.fixture for case in cases))
    try:
        pending = batch.snapshots
        for tick in range(24):
            pending = batch.step(
                tuple(
                    StepInput(case.claims_by_clock[tick // 4])
                    if tick % 4 == 0
                    else StepInput()
                    for case in cases
                )
            )

        assert all(row.tick == 24 and row.event_input_required for row in pending)
        assert all(not row.claim_required for row in pending)
        with pytest.raises(RuntimeError, match="lifecycle metadata"):
            pending[0].public_observation()

        before = batch.snapshots
        malformed = [
            EventInput(case.event_newcomer_positions) for case in cases
        ]
        malformed[6] = EventInput((43,))
        with pytest.raises(native_backend.NativeBackendError, match="status -32"):
            batch.apply_event(malformed)
        assert batch.snapshots == before

        post = batch.apply_event(
            tuple(EventInput(case.event_newcomer_positions) for case in cases)
        )
        assert all(not row.event_input_required for row in post)
        assert all(row.claim_required and row.roster_event for row in post)
        assert [row.new_epoch for row in post[:2]] == [False, True]
        assert all(row.public_observation().tick == 24 for row in post)
    finally:
        batch.close()


def test_rcle_tbcfv_transport_keys_are_runtime_only_and_physically_continuous() -> None:
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (
        native_backend,
    )
    from experiments.candidates.roster_consistent_latent_exploration_tbcfv.host_oracle import (
        PublicObservation,
    )

    contract = native_backend.backend_contract()
    assert contract["stable_physical_agent_transport_keys"] is True
    assert contract["transport_keys_actor_model_visible"] is False
    assert contract["public_observation_excludes_transport_keys"] is True
    assert "transport_keys" not in PublicObservation.__dataclass_fields__

    crossing = _rcle_crossing_case()
    expansion = _rcle_expansion_case()
    traces = native_backend.run_native_trace_batch(
        (crossing, expansion, crossing, expansion, crossing, expansion, crossing, expansion)
    )
    crossing_trace, expansion_trace = traces[:2]
    assert crossing_trace[0].transport_keys[:2] == (400, 401)
    assert crossing_trace[1].transport_keys[:2] == (401, 400)
    crossing_by_key = dict(
        zip(crossing_trace[1].transport_keys, crossing_trace[1].positions)
    )
    assert crossing_by_key[400] == 3
    assert crossing_by_key[401] == 0

    before = set(expansion_trace[23].transport_keys)
    boundary = expansion_trace[24]
    terminal = expansion_trace[-1]
    assert before == set(range(100, 107))
    assert set(boundary.transport_keys) == set(range(100, 109))
    assert set(terminal.transport_keys) == set(range(100, 109))
    assert [
        boundary.transport_keys[index]
        for index, newcomer in enumerate(boundary.newcomers)
        if newcomer
    ] == [107, 108]
    public = boundary.public_observation()
    assert not hasattr(public, "transport_keys")
    assert public.positions == boundary.positions


@pytest.mark.parametrize("backend", ("python_reference", "python", "cuda"))
def test_scdmp_tbcc_wrong_backend_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch, backend: str
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "scdmp_tbcc_order_value_r02_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="backend='cpp'"):
        policy.require_cpp_batched_production(
            policy.SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST,
            backend=backend,
            batch_width=8,
        )


@pytest.mark.parametrize("batch_width", (1, 2))
def test_scdmp_tbcc_conformance_and_unvalidated_widths_fail_before_native_load(
    monkeypatch: pytest.MonkeyPatch, batch_width: int
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "scdmp_tbcc_order_value_r02_full_host",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match="batch_width"):
        policy.require_cpp_batched_production(
            policy.SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST,
            backend="cpp",
            batch_width=batch_width,
        )


def test_scdmp_tbcc_build_root_override_is_wrapped_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="native build/load preflight failed",
    ) as raised:
        policy.require_cpp_batched_production(
            policy.SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST,
            backend="cpp",
            batch_width=8,
            build_root=tmp_path / "unsupported-build-root",
        )

    assert isinstance(raised.value.__cause__, ValueError)
    assert "one fixed candidate build root" in str(raised.value.__cause__)


@pytest.mark.parametrize("batch_width", (8, 12, 32, 120, 144))
def test_scdmp_tbcc_real_receipts_bind_exact_host_abi_and_warm_artifact(
    batch_width: int,
) -> None:
    from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import (
        native_backend,
    )

    result = policy.require_cpp_batched_production(
        policy.SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST,
        backend="cpp",
        batch_width=batch_width,
    )
    first = native_backend.require_cpp_batched_backend()
    second = native_backend.require_cpp_batched_backend()
    identity = native_backend.native_artifact_identity()

    assert first is second
    assert result["component"] == policy.SCDMP_TBCC_ORDER_VALUE_R02_FULL_HOST
    assert result["batch_width"] == batch_width
    assert result["full_reset_step_cpp"] is True
    assert result["python_fallback"] is False
    assert result["native"]["binding_kind"] == "ctypes_cdll"
    assert Path(result["native"]["artifact"]).resolve() == Path(
        identity["artifact_path"]
    ).resolve()
    assert result["native"]["artifact_sha256"] == identity["artifact_sha256"]
    assert identity["component"] == "scdmp.tbcc_order_value.r02.full_host"
    assert identity["host"] == "QUAD-UAV-PALLET-GANTRY-24P5M-v1"
    assert identity["functional_batch_widths"] == [1, 8, 12, 32, 120, 144]
    assert identity["source_sha256"] == (
        "ea2149b187ba65c9229f0ada9c3bd55bd0f424ec5a5830de1f454585b488de38"
    )
    assert identity["source_sha256"] != (
        "6cbdd16c493cd6f0904e44421a087767bb7a79e7f39bfd8b3c13f9221731bf26"
    )
    assert identity["build_key"] == (
        "9a9801e94e1b02468df1e3d59e0c0055b85e2d02306c018bb275b69e0f718fe3"
    )
    assert identity["build_key"] != (
        "5669a6193a3799fef4ea0db48d2e23205ca85e8eeb8ef8b43bb29c2e0c548882"
    )
    assert identity["artifact_sha256"] == (
        "df1097603c3fd2e1f66875e5d3209fcc509609f870569a205efc83c607a7bb9d"
    )
    assert identity["artifact_sha256"] != (
        "30f4a848054f748f76944581c042b4b5de41926628c9e00d1df1f6746f5049f3"
    )
    assert identity["artifact_size"] == 177664
    assert identity["abi_version"] == 2
    assert identity["abi_version"] != 1
    assert identity["runtime_abi"]["struct_sizes"] == {
        "reset_input": 64,
        "renewal_input": 320,
        "host_output": 336,
        "setup_fixture_input": 24,
        "setup_fixture_output": 24,
        "primitive_fixture_input": 160,
    }
    assert identity["runtime_abi"]["struct_sizes"]["host_output"] != 224
    assert first.tbcc_r02_abi_version() == 2
    assert first.tbcc_r02_fixture_magic() == 6071489204069610049


def test_scdmp_tbcc_abi2_native_reward_trace_is_complete_and_canonical() -> None:
    from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import (
        NativeBatch,
        ResetLane,
        constant_disturbance_lane,
        native_artifact_identity,
    )
    from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.config import (
        FORMATION_ROTATE,
        HOOK_HANDOFF,
    )

    reset = ResetLane(
        middle_events=(HOOK_HANDOFF, FORMATION_ROTATE),
        k_initial=7,
        initial_v=0.017,
        initial_y=-0.004,
        initial_phi=0.006,
    )
    rows = tuple(constant_disturbance_lane(index % 18) for index in range(8))
    with NativeBatch((reset,) * 8) as batch:
        before = batch.initial
        outputs = batch.renew(rows)

    identity = native_artifact_identity()
    assert identity["python_plant_transition"] is False
    assert identity["python_fallback"] is False
    for prior, output in zip(before, outputs):
        assert output.last_hold_reward_count == output.ticks_advanced == 7
        prefix = output.last_hold_rewards[: output.last_hold_reward_count]
        tail = output.last_hold_rewards[output.last_hold_reward_count :]
        assert len(output.last_hold_rewards) == 13
        assert all(math.isfinite(value) for value in prefix)
        assert tail == (0.0,) * (13 - output.last_hold_reward_count)
        assert sum(prefix) == pytest.approx(
            output.cumulative_reward - prior.cumulative_reward,
            rel=0.0,
            abs=2e-14,
        )


def test_scdmp_tbcc_abi2_raw_guards_and_malformed_reward_traces_fail_closed() -> None:
    from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import (
        ResetLane,
    )
    from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value import (
        native_backend,
    )
    from experiments.candidates.scdmp_variable_k.target_bound_competent_controller_order_value.config import (
        FORMATION_ROTATE,
        HOOK_HANDOFF,
    )

    library = native_backend.require_cpp_batched_backend()
    reset = ResetLane(
        middle_events=(HOOK_HANDOFF, FORMATION_ROTATE),
        k_initial=7,
        initial_v=0.017,
        initial_y=-0.004,
        initial_phi=0.006,
    )

    for field, value in (
        ("abi_version", 1),
        ("magic", 6071489204069610048),
    ):
        raw = native_backend._reset_input(reset)
        setattr(raw, field, value)
        handles = (ctypes.c_uint64 * 1)()
        outputs = (native_backend._HostOutput * 1)()
        assert library.tbcc_r02_reset_batch(
            (native_backend._ResetInput * 1)(raw), 1, handles, outputs
        ) == 3
        assert handles[0] == 0

    valid = native_backend._reset_input(reset)
    handles = (ctypes.c_uint64 * 1)()
    outputs = (native_backend._HostOutput * 1)()
    assert library.tbcc_r02_reset_batch(
        (native_backend._ResetInput * 1)(valid), 0, handles, outputs
    ) == 1

    malformed = native_backend._HostOutput()
    malformed.status = 0
    malformed.ticks_advanced = 1
    malformed.last_hold_reward_count = 0
    with pytest.raises(native_backend.NativeBackendError, match="count"):
        native_backend._output(malformed)

    malformed.last_hold_reward_count = 1
    malformed.last_hold_rewards[0] = math.nan
    with pytest.raises(native_backend.NativeBackendError, match="nonfinite"):
        native_backend._output(malformed)

    malformed.last_hold_rewards[0] = 0.0
    malformed.last_hold_rewards[1] = 1.0
    with pytest.raises(native_backend.NativeBackendError, match="inactive tail"):
        native_backend._output(malformed)


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_vnfc_bpcr_real_shared_preflight_loads_exact_abi_without_fallback(
    batch_width: int,
) -> None:
    from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import (
        native_backend,
    )

    result = policy.require_cpp_batched_production(
        policy.VNFC_BPCR_R09_FULL_HOST,
        backend="cpp",
        batch_width=batch_width,
    )
    library = native_backend.require_cpp_batched_backend()
    artifact = Path(vars(library)["_name"]).resolve()

    assert result["component"] == policy.VNFC_BPCR_R09_FULL_HOST
    assert result["batch_width"] == batch_width
    assert result["full_reset_step_cpp"] is True
    assert result["python_fallback"] is False
    assert result["native"]["binding_kind"] == "ctypes_cdll"
    assert Path(result["native"]["artifact"]).resolve() == artifact
    assert result["native"]["artifact_sha256"] == hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()
    assert library.vnfc_bpcr_r09_abi_version() == native_backend.NATIVE_ABI_VERSION
    assert {
        "fixture_input": library.vnfc_bpcr_r09_sizeof_fixture_input(),
        "fixture_output": library.vnfc_bpcr_r09_sizeof_fixture_output(),
        "host_input": library.vnfc_bpcr_r09_sizeof_host_input(),
        "host_output": library.vnfc_bpcr_r09_sizeof_host_output(),
    } == {
        "fixture_input": 40,
        "fixture_output": 80,
        "host_input": 408,
        "host_output": 112,
    }


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_scdmp_real_shared_preflight_loads_exact_abi_without_fallback(
    batch_width: int,
) -> None:
    from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import (
        native_backend,
    )

    result = policy.require_cpp_batched_production(
        policy.SCDMP_UAV_SP_ORDER_VALUE_R02_FULL_HOST,
        backend="cpp",
        batch_width=batch_width,
    )
    local = native_backend.native_artifact_identity()
    library = native_backend.require_cpp_batched_backend()

    assert result["component"] == policy.SCDMP_UAV_SP_ORDER_VALUE_R02_FULL_HOST
    assert result["batch_width"] == batch_width
    assert result["full_reset_step_cpp"] is True
    assert result["python_fallback"] is False
    assert result["native"]["binding_kind"] == "ctypes_cdll"
    assert Path(result["native"]["artifact"]).resolve() == Path(
        local["artifact_path"]
    ).resolve()
    assert result["native"]["artifact_sha256"] == local["artifact_sha256"]
    assert library.scdmp_uav_sp_abi_version() == native_backend.NATIVE_ABI_VERSION


@pytest.mark.parametrize("batch_width", (1, 8, 32))
def test_onlgr_real_shared_preflight_does_not_consult_or_mutate_activity_authority(
    monkeypatch: pytest.MonkeyPatch, batch_width: int,
) -> None:
    from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90 import (
        native_backend,
    )
    from experiments.candidates.opportunity_normalized_lease_gated_rebinding.headland90.coordinates import (
        production_activity_permitted,
    )

    authority_before = production_activity_permitted()
    monkeypatch.setattr(
        native_backend,
        "production_preflight",
        lambda: (_ for _ in ()).throw(
            AssertionError("shared implementation guard must not consult activity authority")
        ),
    )
    result = policy.require_cpp_batched_production(
        policy.ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
        backend="cpp",
        batch_width=batch_width,
    )

    assert production_activity_permitted() is authority_before
    assert result["component"] == policy.ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST
    assert result["batch_width"] == batch_width
    assert result["full_reset_step_cpp"] is True
    assert result["python_fallback"] is False
    assert result["native"]["binding_kind"] == "ctypes_cdll"
    assert Path(result["native"]["artifact"]).is_file()


@pytest.mark.parametrize("batch_width", (0, -1))
def test_nonpositive_batch_width_fails_before_native_load(
    monkeypatch: pytest.MonkeyPatch, batch_width: int
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "continuous_roster_toy",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(ValueError, match="positive"):
        policy.require_cpp_batched_production(
            policy.CONTINUOUS_ROSTER_TOY,
            backend="cpp",
            batch_width=batch_width,
        )


def test_continuous_roster_rejects_benchmark_negative_width_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "continuous_roster_toy",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("must not load")),
    )
    with pytest.raises(policy.ProductionBackendUnsupported, match=">= 8"):
        policy.require_cpp_batched_production(
            policy.CONTINUOUS_ROSTER_TOY,
            backend="cpp",
            batch_width=1,
        )


@pytest.mark.parametrize("batch_width", (True, 1.5, "8"))
def test_noninteger_batch_width_is_rejected(batch_width) -> None:
    with pytest.raises(TypeError, match="integer"):
        policy.require_cpp_batched_production(
            policy.CONTINUOUS_ROSTER_TOY,
            backend="cpp",
            batch_width=batch_width,
        )


def test_native_build_or_load_failure_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(**_kwargs):
        raise RuntimeError("synthetic compiler failure")

    monkeypatch.setitem(policy._LOADERS, "continuous_roster_toy", unavailable)
    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="native build/load preflight failed",
    ) as raised:
        policy.require_cpp_batched_production(
            policy.CONTINUOUS_ROSTER_TOY,
            backend="cpp",
            batch_width=32,
        )
    assert isinstance(raised.value.__cause__, RuntimeError)


def test_native_module_without_durable_artifact_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        policy._LOADERS,
        "uav_relay_geometry",
        lambda **_kwargs: ModuleType("missing_artifact"),
    )
    with pytest.raises(
        policy.ProductionBackendUnavailable,
        match="without an artifact path",
    ):
        policy.require_cpp_batched_production(
            policy.UAV_RELAY_GEOMETRY,
            backend="cpp",
            batch_width=1,
        )
