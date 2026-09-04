"""Read-only preactivity identities for the HEADLAND-90 full-panel stage.

This module can compile and load the frozen native library.  It cannot bind a
CAL/HOLD manifest, encode a production coordinate, materialize a random word,
or execute a host transition.
"""

from __future__ import annotations

import hashlib
import functools
import json
from pathlib import Path
import platform
import sys
from types import ModuleType
from typing import Callable, Mapping

from envs.native.production_backend import ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST

from .config import CARD_REVISION, HOST_ID, PRODUCTION_NAMESPACE
from .controllers import (
    CONTROLLER_REGISTRY,
    LOGICAL_HELD_OUT_TAGS,
    coordinate_schema_facts,
)
from .event_transform import event_transform_bits, reachable_rate_fractions
from .native_backend import (
    NATIVE_ABI_VERSION,
    native_artifact_identity,
    native_toolchain_identity,
    require_cpp_batched_backend,
    source_sha256,
)


DIRECTION_ID = "opportunity_normalized_lease_gated_rebinding"
STAGE = "ONLGR-HEADLAND90-R03-CAL-HOLD-FULL-PANEL"
SCHEMA_VERSION = "ONLGR-HEADLAND90-R03-PREACTIVITY-IDENTITY-v1"
SHARED_GUARD = "envs.native.production_backend.require_cpp_batched_production"
SERIALIZER_ID = "UTF8-CANONICAL-JSON-SORTED-COMPACT-LF-v1"
COORDINATE_PROPOSAL_ID = "ONLGR-HEADLAND90-CAL-HOLD-COORDINATE-PROPOSAL-v1"

_PACKAGE = Path(__file__).resolve().parent
_NATIVE_SOURCE = _PACKAGE / "native" / "headland90_backend.cpp"
_EVENT_HEADER = _PACKAGE / "native" / "event_transform_table.h"
_EVENT_PYTHON = _PACKAGE / "event_transform.py"


class PreactivityError(RuntimeError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    """The frozen packet serializer; non-finite or unsupported values fail."""
    try:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise PreactivityError("preactivity identity is not canonical JSON") from error


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_identity(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    content = resolved.read_bytes()
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "bytes": len(content),
        "sha256": _sha256_bytes(content),
        "mtime_ns": stat.st_mtime_ns,
    }


def _controller_registry_digest() -> str:
    digest = hashlib.sha256(b"ONLGR-HEADLAND90-CONTROLLER-REGISTRY-v1\0")
    for ordinal, controller in enumerate(CONTROLLER_REGISTRY):
        digest.update(ordinal.to_bytes(4, "big"))
        for value in (
            controller.alpha_short,
            controller.alpha_long,
            controller.beta_short,
            controller.beta_long,
            controller.gamma_short,
            controller.gamma_long,
        ):
            digest.update(int(value).to_bytes(4, "big", signed=True))
    return digest.hexdigest()


def _event_transform_digest() -> str:
    digest = hashlib.sha256(b"ONLGR-HEADLAND90-EVENT-TRANSFORM-v1\0")
    for rate in _reachable_rates():
        digest.update(rate.numerator.to_bytes(8, "big", signed=True))
        digest.update(rate.denominator.to_bytes(8, "big"))
        for bits in event_transform_bits(rate):
            digest.update(bits.to_bytes(8, "big"))
    return digest.hexdigest()


@functools.lru_cache(maxsize=1)
def _reachable_rates():
    return reachable_rate_fractions()


def _python_platform_identity() -> dict[str, object]:
    executable = Path(sys.executable).resolve()
    stat = executable.stat()
    return {
        "executable": str(executable),
        "executable_sha256": _sha256_bytes(executable.read_bytes()),
        "executable_size": stat.st_size,
        "executable_mtime_ns": stat.st_mtime_ns,
        "version": sys.version,
        "implementation": platform.python_implementation(),
        "cache_tag": sys.implementation.cache_tag,
        "byteorder": sys.byteorder,
        "float_mant_dig": sys.float_info.mant_dig,
        "float_rounds": sys.float_info.rounds,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "system": platform.system(),
        "release": platform.release(),
    }


def coordinate_binding_proposal() -> dict[str, object]:
    """Return schema/count/digest procedure only, with no coordinate rows."""
    schema = coordinate_schema_facts()
    proposal: dict[str, object] = {
        "proposal_id": COORDINATE_PROPOSAL_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "bound": False,
        "production_rows_present": False,
        "production_words_present": False,
        "splits": {
            "CAL": {
                "replicates": 48,
                "controller_maps": 192,
                "controller_replicates": 9216,
                "blocks_per_replicate": 20,
                "encounters_per_block": 2,
                "physical_ticks_per_controller_replicate": 3840,
            },
            "HOLD": {
                "replicates": 128,
                "logical_tags": list(LOGICAL_HELD_OUT_TAGS),
                "logical_controller_replicates": 640,
                "maximum_unique_maps": 5,
                "blocks_per_replicate": 20,
                "encounters_per_block": 2,
                "physical_ticks_per_controller_replicate": 3840,
            },
        },
        "total_controller_replicates": 9856,
        "total_physical_ticks": 37847040,
        "coordinate_schema": schema,
        "cross_field_laws": {
            "template": "(replicate+3*block) mod 4",
            "order": "SHORT,LONG iff (replicate+block) even; otherwise LONG,SHORT",
            "state_stream_terminal_tick": True,
            "link_action_terminal_tick": False,
            "controller_identity_in_disturbance_key": False,
        },
        "future_binding_digest_procedure": {
            "domain_separator": "ONLGR-HEADLAND90-CAL-HOLD-BINDING-v1\\0",
            "row_encoding": (
                "validated coordinate fields encoded as decimal/UTF-8, each preceded "
                "by decimal byte length and colon, joined by ASCII |"
            ),
            "ordering": "strict unsigned-byte lexicographic order of encoded rows",
            "uniqueness": "duplicate encoded rows forbidden",
            "framing": "8-byte unsigned big-endian row length followed by row bytes",
            "digest": "SHA-256 over domain separator followed by every framed row",
            "atomicity": "digest is computed only after the complete required row set exists",
        },
    }
    proposal["proposal_schema_sha256"] = _sha256_bytes(canonical_json_bytes(proposal))
    return proposal


def _serializer_schema_identity() -> dict[str, object]:
    shape = {
        "schema_version": SCHEMA_VERSION,
        "top_level": ["identity", "identity_sha256", "compile_observation", "activity_boundary"],
        "serializer": SERIALIZER_ID,
        "allow_nan": False,
        "encoding": "UTF-8",
        "terminal": "single LF",
    }
    return {
        **shape,
        "schema_sha256": _sha256_bytes(canonical_json_bytes(shape)),
    }


def collect_preactivity_identity() -> dict[str, object]:
    """Collect exact environment/build facts without coordinates or host ticks."""
    toolchain = native_toolchain_identity()
    if "/fp:strict" not in toolchain["compile_flags"]:
        raise PreactivityError("native toolchain is not frozen to /fp:strict")
    artifact = native_artifact_identity()
    if artifact["python_fallback"] is not False:
        raise PreactivityError("native artifact identity admitted a Python fallback")
    rates = _reachable_rates()
    identity = {
        "schema_version": SCHEMA_VERSION,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "toolchain": toolchain,
        "native_sources": {
            "aggregate_sha256": source_sha256(),
            "cpp": _file_identity(_NATIVE_SOURCE),
            "event_table_header": _file_identity(_EVENT_HEADER),
        },
        "native_artifact": {
            key: value
            for key, value in artifact.items()
            if key not in ("first_compile_seconds", "compile_time_status")
        },
        "event_table": {
            "python_source": _file_identity(_EVENT_PYTHON),
            "reachable_rate_count": len(rates),
            "maximum_denominator": max(rate.denominator for rate in rates),
            "generation_precision_decimal_digits": 220,
            "rounding_order": (
                "exact rational to binary64 q; correctly-rounded log1p; binary64 /4; "
                "binary64 *0.25; correctly-rounded expm1; exact sign change"
            ),
            "reachable_vectors_sha256": _event_transform_digest(),
        },
        "controller_registry": {
            "members": len(CONTROLLER_REGISTRY),
            "lookup_members": 64,
            "timing_members": 128,
            "ordered_content_sha256": _controller_registry_digest(),
        },
        "python_platform": _python_platform_identity(),
        "serializer_schema": _serializer_schema_identity(),
        "coordinate_binding_proposal": coordinate_binding_proposal(),
        "shared_production_guard": {
            "component": ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
            "callable": SHARED_GUARD,
            "registered_by_this_stage": False,
        },
    }
    return {
        "identity": identity,
        "identity_sha256": _sha256_bytes(canonical_json_bytes(identity)),
        "compile_observation": {
            "status": artifact["compile_time_status"],
            "first_compile_seconds": artifact["first_compile_seconds"],
        },
        "activity_boundary": {
            "preactivity_only": True,
            "production_coordinate_rows_bound": False,
            "production_random_words_materialized": False,
            "production_controller_ticks_executed": False,
            "calibration_or_hold_manifest_created": False,
        },
    }


def load_headland90_cpp_backend(*, build_root: str | Path | None = None) -> ModuleType:
    """Future shared-registry loader: exact C++ artifact, never a fallback."""
    if build_root is not None:
        raise PreactivityError("HEADLAND-90 uses its frozen source-keyed build root")
    library = require_cpp_batched_backend()
    artifact = native_artifact_identity()
    module = ModuleType("headland90_cpp_batched_backend")
    module.__file__ = str(artifact["artifact_path"])
    module.library = library  # type: ignore[attr-defined]
    module.abi_version = NATIVE_ABI_VERSION  # type: ignore[attr-defined]
    module.python_fallback = False  # type: ignore[attr-defined]
    return module


def require_direction_cpp_batched_production(
    *,
    batch_width: int,
    build_root: str | Path | None = None,
    shared_guard: Callable[..., Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Require shared admission first; unknown/unregistered state fails closed."""
    if shared_guard is None:
        from envs.native.production_backend import require_cpp_batched_production

        shared_guard = require_cpp_batched_production
    receipt = dict(
        shared_guard(
            ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
            backend="cpp",
            batch_width=batch_width,
            build_root=build_root,
        )
    )
    if (
        receipt.get("component") != ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST
        or receipt.get("backend") != "cpp"
        or receipt.get("python_fallback") is not False
        or receipt.get("full_reset_step_cpp") is not True
    ):
        raise PreactivityError("shared production guard receipt is not HEADLAND-90 full-native")
    local = native_artifact_identity()
    return {
        "shared": receipt,
        "direction_native": local,
        "python_fallback": False,
    }
