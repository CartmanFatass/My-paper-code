"""Pure preflight gate; it never contacts subprocess or optimizer surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .foundation_run_manifest import PROSPECTIVE_OUTPUT_ROOT


class ActivityGateError(PermissionError):
    pass


@dataclass(frozen=True)
class CommandContract:
    required_options: tuple[str, ...]
    forbidden_options: tuple[str, ...]
    subprocess_contacted: bool
    optimizer_contacted: bool


@dataclass(frozen=True)
class GateReady:
    manifest_sha256: str
    code_sha256: str
    output_root: str
    subprocess_contacted: bool = False
    optimizer_contacted: bool = False


def command_contract() -> CommandContract:
    return CommandContract(
        required_options=("--run-manifest", "--code-sha256", "--output-root"),
        forbidden_options=(
            "--replicate",
            "--seed",
            "--threshold",
            "--stopping",
            "--retry",
            "--tuning",
            "--reward-inspection",
            "--partial-result",
        ),
        subprocess_contacted=False,
        optimizer_contacted=False,
    )


def technical_authorization_fixture(
    *, manifest_sha256: str, code_sha256: str
) -> dict[str, object]:
    return {
        "schema": "SCDMP_NATIVE_FUSION_R01_S3_NONREGISTERED_GATE_FIXTURE_V1",
        "status": "TECHNICAL_NONREGISTERED_FIXTURE",
        "fixture_only": True,
        "immutable": True,
        "manifest_sha256": manifest_sha256,
        "code_sha256": code_sha256,
        "output_root": PROSPECTIVE_OUTPUT_ROOT,
        "registered_identity_present": False,
        "activity_authorized": False,
        "operator_now": False,
        "effect_refs": [],
    }


class FoundationActivityGate:
    def preflight(
        self,
        *,
        manifest: Mapping[str, object] | None,
        observed_manifest_sha256: str,
        expected_manifest_sha256: str,
        observed_code_sha256: str,
        expected_code_sha256: str,
        output_root: str,
        output_root_exists: bool,
        options: Mapping[str, str],
    ) -> GateReady:
        contract = command_contract()
        if tuple(options) != contract.required_options:
            raise ActivityGateError("command options differ from the exact contract")
        if manifest is None:
            raise ActivityGateError("later immutable run manifest is absent")
        if observed_manifest_sha256 != expected_manifest_sha256:
            raise ActivityGateError("immutable run-manifest SHA differs")
        if observed_code_sha256 != expected_code_sha256:
            raise ActivityGateError("exact code SHA differs")
        if options["--code-sha256"] != observed_code_sha256:
            raise ActivityGateError("command code SHA differs")
        if (
            output_root != manifest.get("output_root")
            or options["--output-root"] != output_root
            or output_root_exists
        ):
            raise ActivityGateError("create-only output root does not byte-match")
        if manifest.get("immutable") is not True:
            raise ActivityGateError("run manifest is not immutable")
        if manifest.get("fixture_only") is True:
            raise ActivityGateError("S3 technical fixture cannot self-release activity")
        if (
            manifest.get("status") != "AUTHORIZED_IMMUTABLE"
            or manifest.get("activity_authorized") is not True
            or manifest.get("operator_now") is not True
        ):
            raise ActivityGateError("later activity authority is incomplete")
        return GateReady(observed_manifest_sha256, observed_code_sha256, output_root)
