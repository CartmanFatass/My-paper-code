"""Fail-closed S4 production entry surface; S4 itself cannot release activity."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import NoReturn

from .foundation_run_manifest import (
    HMAC_DOMAINS,
    PROSPECTIVE_OUTPUT_ROOT,
    S4_RUN_MANIFEST_PATH,
    build_prelaunch_manifest,
    canonical_json_bytes,
)


class PrelaunchRefusal(PermissionError):
    pass


@dataclass(frozen=True)
class ProductionInputs:
    run_manifest: str
    code_sha256: str
    output_root: str


@dataclass(frozen=True)
class ProductionPlan:
    manifest_sha256: str
    code_sha256: str
    output_root: str
    workload: Mapping[str, object]
    output_effect: Mapping[str, object]


def _valid_sha(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True


def parse_production_inputs(argv: Sequence[str]) -> ProductionInputs:
    tokens = tuple(argv)
    if (
        len(tokens) != 6
        or tokens[0] != "--run-manifest"
        or tokens[2] != "--code-sha256"
        or tokens[4] != "--output-root"
    ):
        raise PrelaunchRefusal("exact production argv differs")
    if (
        tokens[1] != S4_RUN_MANIFEST_PATH
        or not _valid_sha(tokens[3])
        or tokens[5] != PROSPECTIVE_OUTPUT_ROOT
    ):
        raise PrelaunchRefusal("exact production argv differs")
    return ProductionInputs(tokens[1], tokens[3].lower(), tokens[5])


def technical_run_manifest_fixture(
    *, manifest_sha256: str, code_sha256: str
) -> dict[str, object]:
    if not _valid_sha(manifest_sha256) or not _valid_sha(code_sha256):
        raise ValueError("technical fixture refs must be SHA-256 values")
    prelaunch = build_prelaunch_manifest(
        code_sha256=code_sha256,
        activity_estimate_sha256="0" * 64,
    )
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S4_NONREGISTERED_RUN_MANIFEST_FIXTURE_V1",
        "status": "TECHNICAL_NONREGISTERED_FIXTURE",
        "fixture_only": True,
        "immutable": True,
        "manifest_sha256": manifest_sha256.lower(),
        "code_sha256": code_sha256.lower(),
        "output_root": PROSPECTIVE_OUTPUT_ROOT,
        "workload": prelaunch["canonical_parameters"],
        "hmac_sha256_domains": list(HMAC_DOMAINS),
        "immutable_old_state_per_update": True,
        "complete_only": True,
        "rerun_permitted": False,
        "registered_master_present": False,
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }


def read_strict_manifest(path: Path) -> tuple[dict[str, object], str]:
    target = Path(path)
    try:
        payload = target.read_bytes()
        if payload.startswith(b"\xef\xbb\xbf"):
            raise PrelaunchRefusal("run manifest contains a UTF-8 BOM")
        value = json.loads(payload.decode("utf-8"))
    except PrelaunchRefusal:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PrelaunchRefusal("run manifest is absent or malformed") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != payload:
        raise PrelaunchRefusal("run manifest is not strict canonical UTF-8 JSON")
    return value, hashlib.sha256(payload).hexdigest()


class FoundationActivityProduction:
    def launch(
        self,
        *,
        inputs: ProductionInputs,
        manifest: Mapping[str, object],
        observed_manifest_sha256: str,
        expected_manifest_sha256: str,
        output_root_exists: bool,
        activity_executor: Callable[[ProductionPlan], object],
    ) -> object:
        if output_root_exists:
            raise PrelaunchRefusal("create-only output root already exists")
        if (
            not _valid_sha(observed_manifest_sha256)
            or observed_manifest_sha256 != expected_manifest_sha256
        ):
            raise PrelaunchRefusal("immutable run-manifest SHA differs")
        if (
            manifest.get("code_sha256") != inputs.code_sha256
            or manifest.get("output_root") != inputs.output_root
        ):
            raise PrelaunchRefusal("code SHA or output root differs")
        if manifest.get("fixture_only") is True:
            raise PrelaunchRefusal("nonregistered fixture cannot release activity")

        prelaunch = build_prelaunch_manifest(
            code_sha256=inputs.code_sha256,
            activity_estimate_sha256=manifest.get("activity_estimate_sha256", ""),
        )
        expected_effect = prelaunch["output_effect_template"]
        if (
            manifest.get("schema")
            != "SCDMP_NATIVE_FUSION_R01_FOUNDATION_ACTIVITY_RUN_MANIFEST_V1"
            or manifest.get("status") != "AUTHORIZED_IMMUTABLE"
            or manifest.get("immutable") is not True
            or manifest.get("workload") != prelaunch["canonical_parameters"]
            or manifest.get("hmac_sha256_domains") != list(HMAC_DOMAINS)
            or manifest.get("immutable_old_state_per_update") is not True
            or manifest.get("complete_only") is not True
            or manifest.get("rerun_permitted") is not False
            or manifest.get("registered_master_present") is not False
            or manifest.get("activity_authorized") is not True
            or manifest.get("operator_now") is not True
            or manifest.get("output_effect") != expected_effect
            or manifest.get("effect_refs") != [expected_effect]
        ):
            raise PrelaunchRefusal("later authority, workload, or Effect differs")
        stage_refs = manifest.get("accepted_stage_refs")
        if not isinstance(stage_refs, list) or len(stage_refs) != 4:
            raise PrelaunchRefusal("S0-S3 stage barrier is incomplete")
        if any(
            not isinstance(ref, Mapping)
            or not isinstance(ref.get("path"), str)
            or not _valid_sha(ref.get("sha256"))
            for ref in stage_refs
        ):
            raise PrelaunchRefusal("S0-S3 stage barrier is malformed")
        authority_ref = manifest.get("activity_authority_ref")
        if (
            not isinstance(authority_ref, Mapping)
            or not isinstance(authority_ref.get("path"), str)
            or not _valid_sha(authority_ref.get("sha256"))
        ):
            raise PrelaunchRefusal("separate activity authority is absent")
        return activity_executor(
            ProductionPlan(
                observed_manifest_sha256,
                inputs.code_sha256,
                inputs.output_root,
                manifest["workload"],
                expected_effect,
            )
        )


def _prelaunch_only_executor(_plan: ProductionPlan) -> NoReturn:
    raise PrelaunchRefusal("S4 prelaunch cannot self-release activity")


def main(argv: Sequence[str] | None = None) -> int:
    inputs = parse_production_inputs(tuple(sys.argv[1:] if argv is None else argv))
    manifest, observed_sha = read_strict_manifest(Path(inputs.run_manifest))
    FoundationActivityProduction().launch(
        inputs=inputs,
        manifest=manifest,
        observed_manifest_sha256=observed_sha,
        expected_manifest_sha256=observed_sha,
        output_root_exists=Path(inputs.output_root).exists(),
        activity_executor=_prelaunch_only_executor,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
