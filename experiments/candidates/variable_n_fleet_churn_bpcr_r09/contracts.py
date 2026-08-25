"""Frozen implementation contracts for the BPCR revision-09 construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Final


DIRECTION_ID: Final[str] = "variable_n_fleet_churn_b4"
STAGE: Final[str] = "VNFC-BPCR-R09-NATIVE-CONSTRUCTION-AND-CONFORMANCE"
CARD_REVISION: Final[str] = "VNFC-BPCR-SCIENCE-20260820-09"
CARD_SHA256: Final[str] = "39b20b0655cef10ff4d3bc3c0550cd286ade922074f73dfd9cba1b62f8f977bf"
PUBLIC_LAW_SHA256: Final[str] = "be15c98e59e2e8b95bccc51e00c755d943627cc59e482c136892809ab717fe64"

SHARED_COMPONENT: Final[str] = "vnfc.bpcr.r09.full_host"
SHARED_LOADER_KEY: Final[str] = "vnfc_bpcr_r09_full_host"
NATIVE_ABI_VERSION: Final[int] = 1
FIXTURE_MAGIC: Final[int] = 0x564E464342504352

MSVC_COMPILE_FLAGS: Final[tuple[str, ...]] = (
    "/nologo",
    "/std:c++20",
    "/O2",
    "/EHsc",
    "/LD",
    "/fp:strict",
    "/permissive-",
)


@dataclass(frozen=True)
class NumericContract:
    physical_energy_storage: str = "signed int64 fifth-units"
    physical_time_storage: str = "signed int32 seconds"
    count_storage: str = "unsigned uint64"
    rational_storage: str = "boost::multiprecision::cpp_int normalized numerator/denominator"
    binary64_pooling: str = "fixed 2048-bin exact binary superaccumulator; one correctly-rounded divide"
    counter_to_normal: str = (
        "two uint64 words -> u=(word+0.5)/2^64 -> strict-binary64 Box-Muller; "
        "first normal used, second cached at the adjacent named lane"
    )
    qr: str = (
        "Householder QR in binary64; process columns left-to-right; positive diagonal; "
        "zero diagonal oriented by first nonzero Q entry positive; logical out<=in uses "
        "row-Stiefel via QR(A.T).T, logical out>in uses column-Stiefel via QR(A)"
    )
    record_encoding: str = "little-endian fixed-width records with explicit schema/version fields"
    compression: str = "zlib level=9, wbits=15, no dictionary; SHA-256 covers uncompressed canonical bytes"


NUMERIC_CONTRACT: Final[NumericContract] = NumericContract()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def implementation_contract() -> dict[str, object]:
    return {
        "schema": "VNFC-BPCR-R09-IMPLEMENTATION-CONTRACT-v1",
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "card_revision": CARD_REVISION,
        "card_sha256": CARD_SHA256,
        "public_law_sha256": PUBLIC_LAW_SHA256,
        "shared_component": SHARED_COMPONENT,
        "shared_loader_key": SHARED_LOADER_KEY,
        "native_abi_version": NATIVE_ABI_VERSION,
        "compiler": "MSVC x64",
        "compile_flags": list(MSVC_COMPILE_FLAGS),
        "numeric": asdict(NUMERIC_CONTRACT),
        "python_environment_loop": False,
        "python_action_loop": False,
        "python_fallback": False,
    }


def contract_sha256() -> str:
    return hashlib.sha256(canonical_json_bytes(implementation_contract())).hexdigest()


def verify_immutable_inputs(repository_root: Path) -> dict[str, object]:
    card = repository_root / "docs/research/candidates/variable_n_fleet_churn/VNFC_UAV_BOUNDED_POST_CHURN_RECOVERY_SCIENCE_CARD.md"
    public_law = repository_root / "docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md"
    observed = {
        "science_card": hashlib.sha256(card.read_bytes()).hexdigest(),
        "public_law": hashlib.sha256(public_law.read_bytes()).hexdigest(),
    }
    if observed != {"science_card": CARD_SHA256, "public_law": PUBLIC_LAW_SHA256}:
        raise RuntimeError("immutable BPCR science-card or public-law bytes differ")
    return {
        "schema": "VNFC-BPCR-R09-IMMUTABLE-INPUTS-v1",
        "science_card_path": str(card.resolve()),
        "science_card_sha256": observed["science_card"],
        "public_law_path": str(public_law.resolve()),
        "public_law_sha256": observed["public_law"],
    }
