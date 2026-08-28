#!/usr/bin/env python3
"""Read-only discovery and validation for HMASD scientific capabilities."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 project environment
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "configs" / "scientific-capabilities-v1.toml"
EVIDENCE_SCHEMA = ROOT / "scripts" / "schemas" / "hmasd_instrument_evidence_v1.schema.json"
OBSERVATION_SCHEMA = (
    ROOT / "scripts" / "schemas" / "hmasd_instrument_observation_v1.schema.json"
)
SECRET_NAME_RE = re.compile(
    r"(?:secret|token|password|credential|private[_-]?key|api[_-]?key|authorization|cookie)",
    re.I,
)
SECRET_VALUE_RE = re.compile(
    r"(?:\b(?:sk|ghp|glpat)-[A-Za-z0-9_-]{4,}\b|"
    r"\bbearer\s+[A-Za-z0-9._~-]{12,}\b|"
    r"\bAKIA[A-Z0-9]{16}\b|"
    r"\bgithub_pat_[A-Za-z0-9_]{12,}\b)",
    re.I,
)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CATALOG_FIELDS = {
    "capability_id",
    "status",
    "question_types",
    "owner_roles",
    "leaf_roles",
    "skill_name",
    "skill_path",
    "environment_id",
    "manifest_ref",
    "entrypoints",
    "effect_class",
    "invocation_kinds",
    "tool_name",
    "tool_version",
    "source_id",
    "source_sha256",
    "limitations",
    "unavailable_reason",
}
INSTRUMENT_LEAF_ROLES = {
    "hmasd-research-scout",
    "hmasd-research-critic",
    "hmasd-research-principles-analyst",
    "hmasd-research-innovator",
    "hmasd-implementer",
    "hmasd-implementer-terra",
    "hmasd-verifier",
}
GENERIC_INTERPRETERS = {
    "bash",
    "bash.exe",
    "bun",
    "bun.exe",
    "cmd",
    "cmd.exe",
    "cscript",
    "cscript.exe",
    "deno",
    "deno.exe",
    "java",
    "java.exe",
    "node",
    "node.exe",
    "nodejs",
    "nodejs.exe",
    "perl",
    "perl.exe",
    "php",
    "php.exe",
    "powershell",
    "powershell.exe",
    "pwsh",
    "pwsh.exe",
    "py",
    "py.exe",
    "python",
    "python.exe",
    "pythonw.exe",
    "ruby",
    "ruby.exe",
    "sh",
    "sh.exe",
    "wscript",
    "wscript.exe",
    "zsh",
    "zsh.exe",
}


class CapabilityError(ValueError):
    """The declared capability surface is invalid or cannot be observed."""


def _load_catalog(path: Path) -> dict[str, Any]:
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise CapabilityError(f"cannot read capability catalog: {exc}") from exc
    if set(value) != {"schema_version", "catalog_id", "capabilities"}:
        raise CapabilityError("unsupported or malformed capability catalog fields")
    if (
        value.get("schema_version") != 1
        or value.get("catalog_id") != "hmasd-scientific-capabilities-v1"
        or not isinstance(value.get("capabilities"), list)
        or not value["capabilities"]
    ):
        raise CapabilityError("unsupported or malformed capability catalog")
    observed_ids: set[str] = set()
    for index, item in enumerate(value["capabilities"]):
        location = f"capabilities[{index}]"
        if not isinstance(item, dict) or set(item) != CATALOG_FIELDS:
            raise CapabilityError(f"{location} has missing or unknown fields")
        capability_id = item["capability_id"]
        if not isinstance(capability_id, str) or not ID_RE.fullmatch(capability_id):
            raise CapabilityError(f"{location}.capability_id is invalid")
        if capability_id in observed_ids:
            raise CapabilityError(f"duplicate capability_id: {capability_id}")
        observed_ids.add(capability_id)
        if item["status"] not in {"candidate", "active", "unavailable"}:
            raise CapabilityError(f"{location}.status is invalid")
        for field in (
            "question_types",
            "owner_roles",
            "leaf_roles",
            "limitations",
            "invocation_kinds",
        ):
            entries = item[field]
            if (
                not isinstance(entries, list)
                or not entries
                or any(not isinstance(entry, str) or not entry for entry in entries)
                or len(entries) != len(set(entries))
            ):
                raise CapabilityError(f"{location}.{field} must contain unique strings")
        if not set(item["owner_roles"]) <= {"EM", "CM"}:
            raise CapabilityError(f"{location}.owner_roles contains an unknown role")
        if not set(item["leaf_roles"]) <= INSTRUMENT_LEAF_ROLES:
            raise CapabilityError(f"{location}.leaf_roles contains an unknown leaf role")
        if not isinstance(item["skill_name"], str) or (
            item["skill_name"] and not item["skill_name"].startswith("hmasd-")
        ):
            raise CapabilityError(f"{location}.skill_name is invalid")
        if item["status"] != "unavailable" and not item["skill_name"]:
            raise CapabilityError(f"{location}.skill_name is required")
        expected_skill_path = (
            f".agents/skills/{item['skill_name']}/SKILL.md" if item["skill_name"] else ""
        )
        if item["status"] == "active":
            if item["skill_path"] != expected_skill_path:
                raise CapabilityError(f"{location}.skill_path is not the active skill path")
            if not (ROOT / item["skill_path"]).is_file():
                raise CapabilityError(f"{location}.skill_path does not exist")
        elif item["skill_path"] != "":
            raise CapabilityError(f"{location}.skill_path must be empty until activation")
        if (
            not isinstance(item["environment_id"], str)
            or not item["environment_id"]
            or not isinstance(item["manifest_ref"], str)
        ):
            raise CapabilityError(f"{location} has an invalid environment reference")
        if item["environment_id"] == "none" and item["manifest_ref"]:
            raise CapabilityError(f"{location}.manifest_ref must be empty for environment none")
        if item["environment_id"] != "none" and not item["manifest_ref"]:
            raise CapabilityError(f"{location}.manifest_ref is required")
        if not isinstance(item["entrypoints"], list) or any(
            not isinstance(entrypoint, str) or not entrypoint
            for entrypoint in item["entrypoints"]
        ):
            raise CapabilityError(f"{location}.entrypoints must be strings")
        if item["effect_class"] not in {
            "local_read_only",
            "external_read_only",
            "external_provider",
        }:
            raise CapabilityError(f"{location}.effect_class is invalid")
        if not set(item["invocation_kinds"]) <= {"command", "api", "manual"}:
            raise CapabilityError(f"{location}.invocation_kinds is invalid")
        executable_kinds = set(item["invocation_kinds"]) & {"command", "api"}
        if item["status"] == "active" and executable_kinds:
            if not item["entrypoints"]:
                raise CapabilityError(
                    f"{location}.entrypoints requires a dedicated repo entrypoint"
                )
            entrypoint_root = f".agents/skills/{item['skill_name']}/scripts"
            for entrypoint_index, entrypoint in enumerate(item["entrypoints"]):
                entrypoint_label = f"{location}.entrypoints[{entrypoint_index}]"
                if Path(entrypoint).name.lower() in GENERIC_INTERPRETERS:
                    raise CapabilityError(
                        f"{entrypoint_label} must be a dedicated repo entrypoint"
                    )
                try:
                    _resolve_within_exact_root(
                        entrypoint,
                        entrypoint_root,
                        entrypoint_label,
                        expect_file=True,
                    )
                except CapabilityError as exc:
                    raise CapabilityError(
                        f"{entrypoint_label} must be a dedicated repo entrypoint: {exc}"
                    ) from exc
        for field in ("tool_name", "tool_version"):
            if not isinstance(item[field], str) or not item[field]:
                raise CapabilityError(f"{location}.{field} is invalid")
        if not isinstance(item["source_id"], str) or not ID_RE.fullmatch(item["source_id"]):
            raise CapabilityError(f"{location}.source_id is invalid")
        if not isinstance(item["source_sha256"], str) or not SHA256_RE.fullmatch(
            item["source_sha256"]
        ):
            raise CapabilityError(f"{location}.source_sha256 is invalid")
        reason = item["unavailable_reason"]
        if not isinstance(reason, str) or bool(reason) != (item["status"] == "unavailable"):
            raise CapabilityError(f"{location}.unavailable_reason is inconsistent with status")
    return value


def _list_capabilities(
    catalog: dict[str, Any], *, role: str | None, question_type: str | None
) -> dict[str, Any]:
    rows = []
    for item in catalog["capabilities"]:
        if role is not None and role not in item.get("owner_roles", []):
            continue
        if question_type is not None and question_type not in item.get("question_types", []):
            continue
        rows.append(
            {
                "capability_id": item["capability_id"],
                "effect_class": item["effect_class"],
                "environment_id": item["environment_id"],
                "skill_name": item["skill_name"],
                "status": item["status"],
            }
        )
    rows.sort(key=lambda row: row["capability_id"])
    return {"capabilities": rows, "schema_version": 1}


def _show_capability(catalog: dict[str, Any], capability_id: str) -> dict[str, Any]:
    matches = [
        item for item in catalog["capabilities"]
        if item.get("capability_id") == capability_id
    ]
    if len(matches) != 1:
        raise CapabilityError(
            f"capability id must select exactly one declaration: {capability_id}"
        )
    return {"capability": matches[0], "schema_version": 1}


def _doctor_capability(catalog: dict[str, Any], capability_id: str) -> dict[str, Any]:
    item = _show_capability(catalog, capability_id)["capability"]
    observations = []
    all_found = True
    if item["skill_path"]:
        skill_path = ROOT / item["skill_path"]
        if skill_path.is_file():
            observations.append(f"skill found: {item['skill_path']}")
        else:
            all_found = False
            observations.append(f"skill not found: {item['skill_path']}")
    if item["environment_id"] == "none" and item["status"] == "active":
        observations.append("environment: none")
    elif item["manifest_ref"]:
        manifest_path = ROOT / item["manifest_ref"]
        if not manifest_path.is_file():
            all_found = False
            observations.append(f"manifest not found: {item['manifest_ref']}")
        else:
            observations.append(f"manifest found: {item['manifest_ref']}")
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                all_found = False
                observations.append(f"manifest unreadable: {exc}")
            else:
                version = manifest.get("python", {}).get("version")
                if version:
                    observations.append(f"manifest python version: {version}")
    if not item.get("entrypoints") and item["status"] == "active":
        observations.append("entrypoints: none")
    for entrypoint in item.get("entrypoints", []):
        declared = Path(entrypoint)
        if not declared.is_absolute():
            declared = ROOT.joinpath(*PurePosixPath(entrypoint).parts)
        observed = str(declared) if declared.is_file() else shutil.which(entrypoint)
        if observed is None:
            all_found = False
            observations.append(f"executable not found: {entrypoint}")
        else:
            observations.append(f"executable found: {entrypoint}")
    return {
        "available": bool(item["status"] == "active" and all_found),
        "capability_id": capability_id,
        "declared_status": item["status"],
        "observations": observations,
        "schema_version": 1,
    }


def _reject_secret_like(value: Any, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if SECRET_NAME_RE.search(str(key)):
                raise CapabilityError(f"secret-like field is forbidden at {location}.{key}")
            _reject_secret_like(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_secret_like(item, f"{location}[{index}]")
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        raise CapabilityError(f"secret-like value is forbidden at {location}")


def _reject_cross_direction_refs(value: Any, direction_id: str, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_cross_direction_refs(item, direction_id, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_cross_direction_refs(item, direction_id, f"{location}[{index}]")
    elif isinstance(value, str):
        parts = value.replace("\\", "/").split("/")
        foreign = any(
            parts[index:index + 3] == ["docs", "research", "candidates"]
            and index + 3 < len(parts)
            and parts[index + 3] != direction_id
            for index in range(len(parts))
        ) or any(
            parts[index:index + 2] == ["temp", "directions"]
            and index + 2 < len(parts)
            and parts[index + 2] != direction_id
            for index in range(len(parts))
        )
        if foreign:
            raise CapabilityError(f"cross-direction locator is forbidden at {location}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _strict_repo_relative_path(relative: str, label: str) -> PurePosixPath:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise CapabilityError(f"{label} is not a canonical repository-relative path")
    parsed = PurePosixPath(relative)
    if (
        parsed.is_absolute()
        or parsed.as_posix() != relative
        or any(part in {".", ".."} for part in parsed.parts)
    ):
        raise CapabilityError(f"{label} is not a canonical repository-relative path")
    return parsed


def _resolve_within_exact_root(
    relative: str,
    exact_root_relative: str,
    label: str,
    *,
    expect_file: bool = False,
    expect_directory: bool = False,
) -> Path:
    if expect_file and expect_directory:
        raise ValueError("a path cannot be both a file and a directory")
    base = ROOT.resolve()
    target_parts = _strict_repo_relative_path(relative, label)
    root_parts = _strict_repo_relative_path(
        exact_root_relative, f"{label} exact root"
    )
    lexical_root = base.joinpath(*root_parts.parts)
    lexical_target = base.joinpath(*target_parts.parts)
    try:
        lexical_target.relative_to(lexical_root)
    except ValueError as exc:
        raise CapabilityError(f"{label} is outside the exact root") from exc

    resolved_root = lexical_root.resolve(strict=False)
    if resolved_root != lexical_root:
        raise CapabilityError(f"{label} redirects the exact root")
    resolved_target = lexical_target.resolve(strict=False)
    try:
        resolved_target.relative_to(lexical_root)
    except ValueError as exc:
        raise CapabilityError(f"{label} resolves outside the exact root") from exc
    if expect_file and not resolved_target.is_file():
        raise CapabilityError(f"{label} file does not exist")
    if expect_directory and not resolved_target.is_dir():
        raise CapabilityError(f"{label} directory does not exist")
    return resolved_target


def _resolve_repo_path(relative: str, label: str, *, expect_directory: bool = False) -> Path:
    parts = PurePosixPath(relative).parts
    target = ROOT if relative == "." else (ROOT.joinpath(*parts)).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise CapabilityError(f"{label} escapes the repository root") from exc
    expected = target.is_dir() if expect_directory else target.is_file()
    if not expected:
        kind = "directory" if expect_directory else "file"
        raise CapabilityError(f"{label} {kind} does not exist")
    return target


def _validate_content_ref(ref: dict[str, Any], label: str) -> Path:
    target = _resolve_repo_path(ref["path"], label)
    if _sha256(target) != ref["sha256"]:
        raise CapabilityError(f"{label} sha256 does not match repository content")
    return target


def _validate_exact_content_ref(
    ref: dict[str, Any], exact_root_relative: str, label: str
) -> Path:
    target = _resolve_within_exact_root(
        ref["path"], exact_root_relative, label, expect_file=True
    )
    if _sha256(target) != ref["sha256"]:
        raise CapabilityError(f"{label} sha256 does not match repository content")
    return target


def _validate_capability_binding(
    value: dict[str, Any], catalog: dict[str, Any]
) -> None:
    capability_id = value["capability"]["capability_id"]
    item = _show_capability(catalog, capability_id)["capability"]
    if value["outcome"]["status"] != "UNAVAILABLE" and item["status"] != "active":
        raise CapabilityError(
            f"capability {capability_id} is not active for an observed or failed operation"
        )
    if value["owner_role"] not in item["owner_roles"]:
        raise CapabilityError("instrument evidence owner_role is not allowed by the catalog")
    if value["producer_leaf"] not in item["leaf_roles"]:
        raise CapabilityError("instrument evidence producer_leaf is not allowed by the catalog")
    if value["capability"]["effect_class"] != item["effect_class"]:
        raise CapabilityError("instrument evidence effect_class does not match the catalog")
    if value["capability"]["tool"] != item["tool_name"]:
        raise CapabilityError("instrument evidence tool does not match the catalog")
    if value["capability"]["tool_version"] != item["tool_version"]:
        raise CapabilityError("instrument evidence tool_version does not match the catalog")
    invocation = value["invocation"]
    if invocation["kind"] not in item["invocation_kinds"]:
        raise CapabilityError("instrument evidence invocation kind does not match the catalog")
    if invocation["kind"] in {"command", "api"}:
        if not invocation["argv"] or invocation["argv"][0] not in item["entrypoints"]:
            raise CapabilityError(
                "instrument evidence argv[0] is not a cataloged entrypoint"
            )
        entrypoint_ref = invocation["entrypoint_ref"]
        if entrypoint_ref is None or entrypoint_ref["path"] != invocation["argv"][0]:
            raise CapabilityError(
                "instrument evidence entrypoint_ref does not bind argv[0]"
            )
        _validate_exact_content_ref(
            entrypoint_ref,
            f".agents/skills/{item['skill_name']}/scripts",
            "instrument evidence entrypoint_ref",
        )
    elif invocation["kind"] == "manual" and invocation["argv"]:
        raise CapabilityError("manual instrument evidence invocation argv must be empty")
    elif invocation["kind"] == "manual" and invocation["entrypoint_ref"] is not None:
        raise CapabilityError("manual instrument evidence entrypoint_ref must be null")
    _resolve_repo_path(invocation["cwd"], "instrument evidence invocation cwd", expect_directory=True)

    skill_ref = value["capability"]["skill_ref"]
    if item["skill_path"]:
        if skill_ref is None or skill_ref["path"] != item["skill_path"]:
            raise CapabilityError("instrument evidence skill_ref path does not match the catalog")
        _validate_content_ref(skill_ref, "instrument evidence skill_ref")
    elif skill_ref is not None:
        raise CapabilityError("instrument evidence skill_ref must be null for this capability")

    environment_ref = value["capability"]["environment_ref"]
    if item["environment_id"] == "none":
        if environment_ref is not None:
            raise CapabilityError(
                "instrument evidence environment_ref must be null for environment none"
            )
    elif item["status"] == "active":
        if environment_ref is None or environment_ref["path"] != item["manifest_ref"]:
            raise CapabilityError(
                "instrument evidence environment_ref path does not match the catalog"
            )
        _validate_content_ref(environment_ref, "instrument evidence environment_ref")


def _validate_evidence(
    path: Path, direction_id: str, catalog: dict[str, Any]
) -> dict[str, Any]:
    candidate_path = Path(os.path.abspath(path))
    try:
        candidate_relative = candidate_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise CapabilityError(
            "instrument evidence candidate path escapes the repository root"
        ) from exc
    try:
        value = json.loads(candidate_path.read_text(encoding="utf-8"))
        schema = json.loads(EVIDENCE_SCHEMA.read_text(encoding="utf-8"))
        observation_schema = json.loads(OBSERVATION_SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityError(f"cannot read instrument evidence: {exc}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise CapabilityError(f"instrument evidence schema error at {location}: {error.message}")
    _reject_secret_like(value)
    if value["direction_id"] != direction_id:
        raise CapabilityError("instrument evidence direction_id does not match --direction-id")
    _reject_cross_direction_refs(value, direction_id)
    expected_sidecar = (
        f"docs/research/candidates/{direction_id}/evidence/{value['evidence_id']}.json"
    )
    if value["sidecar_path"] != expected_sidecar:
        raise CapabilityError("instrument evidence sidecar_path is not the exact durable path")
    _resolve_within_exact_root(
        expected_sidecar,
        f"docs/research/candidates/{direction_id}/evidence",
        "instrument evidence sidecar destination",
    )
    _validate_capability_binding(value, catalog)
    for index, ref in enumerate(value["frozen_operation"]["input_refs"]):
        _validate_content_ref(ref, f"instrument evidence input_refs[{index}]")
    _validate_content_ref(
        value["manager_interpretation"]["target_ref"],
        "instrument evidence manager target_ref",
    )
    artifact_roots = (
        f"temp/directions/{direction_id}/exp/instruments/{value['evidence_id']}",
        f"temp/directions/{direction_id}/test/instruments/{value['evidence_id']}",
    )
    observation_artifacts = []
    for artifact in value["artifacts"]:
        artifact_root = next(
            (
                root
                for root in artifact_roots
                if PurePosixPath(artifact["path"]).is_relative_to(PurePosixPath(root))
            ),
            None,
        )
        if artifact_root is None:
            raise CapabilityError(
                "instrument artifact path must remain under the exact direction/evidence root"
            )
        artifact_path = _validate_exact_content_ref(
            artifact, artifact_root, "instrument artifact"
        )
        if PurePosixPath(artifact["path"]).name == "observation.json":
            observation_artifacts.append(artifact_path)
    if len(observation_artifacts) != 1:
        raise CapabilityError("instrument evidence requires exactly one observation.json artifact")
    try:
        raw = json.loads(observation_artifacts[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityError(f"cannot read typed observation artifact: {exc}") from exc
    _reject_secret_like(raw, "$.artifact")
    observation_errors = sorted(
        Draft202012Validator(observation_schema).iter_errors(raw),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if observation_errors:
        error = observation_errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise CapabilityError(
            f"typed observation schema error at {location}: {error.message}"
        )
    observation = raw.get("instrument_observation") if isinstance(raw, dict) else None
    expected_identity = {
        "evidence_id": value["evidence_id"],
        "capability_id": value["capability"]["capability_id"],
        "outcome": value["outcome"]["status"],
    }
    if not isinstance(observation, dict) or any(
        observation.get(key) != expected for key, expected in expected_identity.items()
    ):
        raise CapabilityError("typed observation identity does not match instrument evidence")
    if observation.get("core_observations") != value["outcome"]["core_observations"]:
        raise CapabilityError(
            "typed observation core_observations do not match instrument evidence"
        )
    if (
        value["capability"]["capability_id"] == "scientific-critical-thinking"
        and value["outcome"]["status"] == "OBSERVED"
        and observation.get("claim_ceiling")
        != value["manager_interpretation"]["claim_ceiling"]
    ):
        raise CapabilityError(
            "typed observation claim_ceiling does not match manager interpretation"
        )
    candidate_root = next(
        (
            root
            for root in artifact_roots
            if PurePosixPath(candidate_relative).is_relative_to(PurePosixPath(root))
        ),
        None,
    )
    if candidate_root is None:
        raise CapabilityError(
            "instrument evidence candidate path must be under the exact instrument temp root"
        )
    _resolve_within_exact_root(
        candidate_relative,
        candidate_root,
        "instrument evidence candidate path",
        expect_file=True,
    )
    return {
        "content_sha256": _sha256(candidate_path),
        "direction_id": direction_id,
        "evidence_id": value["evidence_id"],
        "schema_version": 1,
        "sidecar_path": value["sidecar_path"],
        "valid": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--role", choices=("EM", "CM"))
    listing.add_argument("--question-type")
    show = commands.add_parser("show")
    show.add_argument("--id", required=True)
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--id", required=True)
    evidence = commands.add_parser("validate-evidence")
    evidence.add_argument("--path", type=Path, required=True)
    evidence.add_argument("--direction-id", required=True)
    args = parser.parse_args(argv)

    try:
        catalog = _load_catalog(DEFAULT_CATALOG.resolve())
        if args.command == "validate-evidence":
            result = _validate_evidence(args.path, args.direction_id, catalog)
        if args.command == "list":
            result = _list_capabilities(
                catalog,
                role=args.role,
                question_type=args.question_type,
            )
        elif args.command == "show":
            result = _show_capability(catalog, args.id)
        elif args.command == "doctor":
            result = _doctor_capability(catalog, args.id)
    except CapabilityError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
