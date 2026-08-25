"""Fail-closed future production admission for the exact SCDMP UAV host."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from .config import CARD_REVISION, COMPONENT, CONSTRUCTION_OBJECT, HOST_ID
from .native_backend import (
    SCIENCE_CARD_PATH,
    SCIENCE_CARD_SHA256,
    native_artifact_identity,
    require_cpp_batched_backend,
)


class PreactivityError(RuntimeError):
    pass


def require_direction_cpp_batched_production(
    *,
    batch_width: int,
    build_root: str | Path | None = None,
    shared_guard: Callable[..., Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Call the shared policy guard and cross-check the exact loaded artifact."""

    if build_root is not None:
        raise PreactivityError("the source-keyed SCDMP UAV loader forbids build_root overrides")
    if shared_guard is None:
        from envs.native.production_backend import require_cpp_batched_production

        shared_guard = require_cpp_batched_production
    receipt = dict(
        shared_guard(
            COMPONENT,
            backend="cpp",
            batch_width=batch_width,
            build_root=None,
        )
    )
    if (
        receipt.get("component") != COMPONENT
        or receipt.get("backend") != "cpp"
        or receipt.get("full_reset_step_cpp") is not True
        or receipt.get("python_fallback") is not False
    ):
        raise PreactivityError("shared production receipt is not the exact full-native SCDMP host")
    native = receipt.get("native")
    if not isinstance(native, Mapping):
        raise PreactivityError("shared production receipt lacks native artifact identity")
    local = native_artifact_identity()
    science_card = local.get("science_card")
    if (
        not isinstance(science_card, Mapping)
        or Path(str(science_card.get("path", ""))).resolve() != SCIENCE_CARD_PATH.resolve()
        or science_card.get("sha256") != SCIENCE_CARD_SHA256
    ):
        raise PreactivityError("candidate native identity is not bound to the immutable revision-02 science card")
    if (
        Path(str(native.get("artifact", ""))).resolve()
        != Path(str(local["artifact_path"])).resolve()
        or native.get("artifact_sha256") != local["artifact_sha256"]
        or local.get("python_fallback") is not False
    ):
        raise PreactivityError("shared and candidate-local native artifact identities differ")
    library = require_cpp_batched_backend()
    if library.scdmp_uav_sp_abi_version() != local["abi_version"]:
        raise PreactivityError("loaded candidate-local ABI identity changed after shared admission")
    return {
        "schema": "SCDMP_UAV_SP_R02_CPP_BATCHED_PREACTIVITY_V1",
        "component": COMPONENT,
        "host": HOST_ID,
        "card_revision": CARD_REVISION,
        "construction_object": CONSTRUCTION_OBJECT,
        "backend": "cpp",
        "full_reset_step_cpp": True,
        "python_fallback": False,
        "shared": receipt,
        "direction_native": local,
        "science_card": dict(science_card),
    }
