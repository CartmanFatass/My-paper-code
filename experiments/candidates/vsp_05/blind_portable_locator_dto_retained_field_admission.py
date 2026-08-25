"""Blind structural admission of the immutable VSP05-A1 retained-row DTO.

The artifact is located from a caller-supplied checkout root, hashed as opaque
bytes, and then scanned once for JSON structure.  Row scalar values are never
materialized.  Slot meaning can enter only through the authenticated embedded
``vsp05_a4_retained_field_self_description`` object.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence, TextIO


CANDIDATE_ID = "CAND-VSP-05@adversarial-revision-v7"
TREATMENT_ID = "VSP05-A4-BLIND-PORTABLE-LOCATOR-DTO-RETAINED-FIELD-ADMISSION-AUDIT"
SCHEMA_VERSION = 1
PORTABLE_LOCATOR = "logs/vsp05_a1_truth_reachability_1a09bccf_r1/raw_result.json"
EXPECTED_SHA256 = "d4ba7e00ae65c4f0cfd6f84b37c300e9e580868c42bd3c3f02eff20b0b3a3f2e"
EXPECTED_ROW_CONTAINERS = 15_971
ACCEPTED_SOURCE_COMMIT = "1a09bccf9bd64c756865531bc55a871afa286dd3"
ACCEPTED_PUBLICATION_COMMIT = "9f3c57f809a0c0ee11868e025adbeea762832a46"
ROW_CONTAINER_KEY = "real_frontier_rows"
ROW_CONTAINER_POINTER = "/real_frontier_rows"
SELF_DESCRIPTION_KEY = "vsp05_a4_retained_field_self_description"
SELF_DESCRIPTION_KIND = "VSP05_A4_RETAINED_FIELD_SELF_DESCRIPTION"
PUBLIC_RESULT_LOCATOR = "docs/research/candidates/vsp_05/VSP05_A4_BLIND_PORTABLE_LOCATOR_DTO_RETAINED_FIELD_ADMISSION_RESULT.json"
PUBLIC_INDEX_LOCATOR = "docs/research/candidates/vsp_05/VSP05_A4_CODE_SCIENCE_INDEX.md"

TERMINAL_BRANCHES = (
    "A4_BLINDNESS_OR_SCOPE_VIOLATION",
    "A4_IMMUTABLE_SOURCE_OR_PORTABLE_LOCATOR_INVALID",
    "A4_DTO_SEMANTIC_BINDING_UNAVAILABLE",
    "A4_REQUIRED_RETENTION_INCOMPLETE",
    "A4_BLIND_ADMISSION_SUFFICIENT",
)

REQUIRED_SLOTS: dict[str, tuple[str, ...]] = {
    "same_subject_current_frontier": (
        "current membership/lifecycle category including no-incumbent or JOIN",
        "actual persisted incumbent i",
        "unchanged actual proposal q",
        "same-current-time hard gate G_i",
        "same-current-time strict truth T_i",
        "same-current-time hard gate G_q",
        "same-current-time strict truth T_q",
    ),
    "temporal_same_lifecycle": (
        "complete row identity",
        "cell identity",
        "seed",
        "episode identity",
        "time index or frontier ordinal",
        "lifecycle key",
        "explicit incumbent epoch",
        "explicit linkage keys spanning frontier handoff and executor",
    ),
    "actual_handoff": (
        "completion-latch state supplied to handoff",
        "pending state",
        "pending successor q",
        "commit-event field",
        "persisted incumbent immediately before commit",
        "persisted incumbent immediately after commit",
        "handoff event identity/order and lifecycle linkage",
    ),
    "actual_executor": (
        "supplied-executor event identity/order and lifecycle linkage",
        "supplied-executor identity where represented",
        "actual executor input subject/skill",
        "real primitive command",
    ),
    "closed_handoff_allowlist": (
        "explicit schema-declared enumeration of every causally prior allowlist input/flag",
        "one serialized field for every enumerated member",
        "causal-prior order/linkage metadata",
    ),
}

HARD_CAPS = {
    "registered_admission_audits": 1,
    "locator_resolutions": 1,
    "opaque_hash_passes": 1,
    "structural_schema_passes": 1,
    "row_schema_envelopes": EXPECTED_ROW_CONTAINERS,
    "row_semantic_values_read": 0,
    "row_samples_or_presence_vectors_emitted": 0,
    "code_semantics_reads": 0,
    "new_trace_or_hypothetical_activity": 0,
    "environment_policy_executor_learning_training_optimizer_evaluation_activity": 0,
    "retry_rescue_or_fallback": 0,
}

_JSON_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_JSON_TYPES = frozenset({"array", "boolean", "integer", "null", "number", "object", "string"})


class ContractViolation(ValueError):
    """A fail-closed portable-locator, source, parser, or result violation."""


class BindingUnavailable(ValueError):
    """The immutable DTO does not provide one unambiguous self-description."""


class StructuralParseFailure(ContractViolation):
    """A structural failure carrying the exact completed row-envelope count."""

    def __init__(self, message: str, row_count: int) -> None:
        super().__init__(message)
        self.row_count = row_count


@dataclass
class _PathStats:
    present_rows: int = 0
    observed_json_types: set[str] = field(default_factory=set)


@dataclass
class StructuralReceipt:
    row_count: int
    manifest: dict[str, _PathStats]
    self_description: Any


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractViolation(message)


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _pointer_join(parent: str, key: str) -> str:
    return f"{parent}/{_pointer_token(key)}" if parent else f"/{_pointer_token(key)}"


def _portable_parts(locator: str) -> tuple[str, ...]:
    _require(isinstance(locator, str), "portable locator must be a string")
    _require(locator == PORTABLE_LOCATOR, "alternate or re-encoded locator rejected")
    _require("\\" not in locator, "portable locator must use POSIX separators")
    pure = PurePosixPath(locator)
    _require(not pure.is_absolute(), "absolute locator rejected")
    _require(all(part not in {"", ".", ".."} for part in pure.parts), "locator traversal rejected")
    _require(pure.as_posix() == locator, "locator normalization or re-encoding rejected")
    return pure.parts


def resolve_portable_locator(checkout_root: str | Path, locator: str = PORTABLE_LOCATOR) -> Path:
    """Resolve the exact registered POSIX locator once under an explicit root."""

    root = Path(checkout_root)
    _require(root.is_absolute(), "checkout root must be absolute; cwd substitution is forbidden")
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise ContractViolation("verified checkout root unavailable") from exc
    _require(resolved_root.is_dir(), "verified checkout root is not a directory")
    parts = _portable_parts(locator)
    try:
        resolved_input = resolved_root.joinpath(*parts).resolve(strict=True)
    except OSError as exc:
        raise ContractViolation("exact portable locator unavailable") from exc
    try:
        resolved_input.relative_to(resolved_root)
    except ValueError as exc:
        raise ContractViolation("portable locator escapes checkout root through traversal or symlink") from exc
    _require(resolved_input.is_file(), "portable locator does not identify a regular file")
    return resolved_input


def _opaque_sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
                total += len(chunk)
    except OSError as exc:
        raise ContractViolation("opaque hash pass failed") from exc
    return digest.hexdigest(), total


class _JsonReader:
    """Small streaming JSON parser that can discard scalar lexemes without storing them."""

    def __init__(self, handle: TextIO) -> None:
        self._handle = handle
        self._buffer = ""
        self._buffer_index = 0
        self.offset = 0

    def peek(self) -> str:
        if self._buffer_index >= len(self._buffer):
            # This transport buffer is never tokenized into or retained as row
            # scalar values; it only amortizes the streaming reader call cost.
            self._buffer = self._handle.read(64 * 1024)
            self._buffer_index = 0
        return self._buffer[self._buffer_index] if self._buffer else ""

    def take(self) -> str:
        value = self.peek()
        if value:
            self._buffer_index += 1
            self.offset += 1
        return value

    def whitespace(self) -> None:
        while self.peek() in {" ", "\t", "\r", "\n"}:
            self.take()

    def expect(self, expected: str) -> None:
        actual = self.take()
        if actual != expected:
            raise ContractViolation(f"invalid JSON structure at character {self.offset}: expected {expected!r}")

    def string(self, *, materialize: bool) -> str | None:
        self.expect('"')
        output: list[str] | None = [] if materialize else None
        while True:
            char = self.take()
            if char == "":
                raise ContractViolation("unterminated JSON string")
            if char == '"':
                return "".join(output) if output is not None else None
            if ord(char) < 0x20:
                raise ContractViolation("unescaped control character in JSON string")
            if char != "\\":
                if output is not None:
                    output.append(char)
                continue
            escape = self.take()
            if escape in {'"', "\\", "/"}:
                if output is not None:
                    output.append(escape)
            elif escape in {"b", "f", "n", "r", "t"}:
                if output is not None:
                    output.append({"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}[escape])
            elif escape == "u":
                digits = "".join(self.take() for _ in range(4))
                if len(digits) != 4 or any(c not in "0123456789abcdefABCDEF" for c in digits):
                    raise ContractViolation("invalid Unicode escape in JSON string")
                if output is not None:
                    output.append(chr(int(digits, 16)))
            else:
                raise ContractViolation("invalid escape in JSON string")

    def scalar_type(self) -> str:
        char = self.peek()
        if char == '"':
            self.string(materialize=False)
            return "string"
        if char and char in "-0123456789":
            return self._discard_number()
        for literal, kind in (("true", "boolean"), ("false", "boolean"), ("null", "null")):
            if char == literal[0]:
                for expected in literal:
                    self.expect(expected)
                return kind
        raise ContractViolation(f"invalid JSON value at character {self.offset}")

    def _discard_number(self) -> str:
        """Validate a number lexeme without ever constructing its scalar value."""

        if self.peek() == "-":
            self.take()
        if self.peek() == "0":
            self.take()
            if self.peek() and self.peek().isdigit():
                raise ContractViolation("invalid leading zero in JSON number")
        elif self.peek() and self.peek() in "123456789":
            self.take()
            while self.peek() and self.peek().isdigit():
                self.take()
        else:
            raise ContractViolation("invalid JSON number")
        kind = "integer"
        if self.peek() == ".":
            kind = "number"
            self.take()
            if not self.peek() or not self.peek().isdigit():
                raise ContractViolation("invalid JSON fraction")
            while self.peek() and self.peek().isdigit():
                self.take()
        if self.peek() in {"e", "E"}:
            kind = "number"
            self.take()
            if self.peek() in {"+", "-"}:
                self.take()
            if not self.peek() or not self.peek().isdigit():
                raise ContractViolation("invalid JSON exponent")
            while self.peek() and self.peek().isdigit():
                self.take()
        return kind

    def materialized(self) -> Any:
        self.whitespace()
        char = self.peek()
        if char == '"':
            return self.string(materialize=True)
        if char == "{":
            result: dict[str, Any] = {}
            self.take()
            self.whitespace()
            if self.peek() == "}":
                self.take()
                return result
            while True:
                key = self.string(materialize=True)
                assert key is not None
                if key in result:
                    raise ContractViolation("duplicate key in embedded self-description")
                self.whitespace(); self.expect(":")
                result[key] = self.materialized()
                self.whitespace()
                delimiter = self.take()
                if delimiter == "}":
                    return result
                if delimiter != ",":
                    raise ContractViolation("invalid embedded self-description object")
                self.whitespace()
        if char == "[":
            result_list: list[Any] = []
            self.take(); self.whitespace()
            if self.peek() == "]":
                self.take()
                return result_list
            while True:
                result_list.append(self.materialized())
                self.whitespace()
                delimiter = self.take()
                if delimiter == "]":
                    return result_list
                if delimiter != ",":
                    raise ContractViolation("invalid embedded self-description array")
                self.whitespace()
        if char and char in "-0123456789":
            token: list[str] = []
            while self.peek() and self.peek() in "-+0123456789.eE":
                token.append(self.take())
            text = "".join(token)
            if _JSON_NUMBER.fullmatch(text) is None:
                raise ContractViolation("invalid embedded JSON number")
            return float(text) if any(c in text for c in ".eE") else int(text)
        for literal, value in (("true", True), ("false", False), ("null", None)):
            if char == literal[0]:
                for expected in literal:
                    self.expect(expected)
                return value
        raise ContractViolation("invalid embedded self-description value")


class _StructuralScanner:
    def __init__(self, reader: _JsonReader) -> None:
        self.reader = reader
        self.manifest: dict[str, _PathStats] = {}
        self.row_count = 0
        self.self_description: Any = None
        self._self_description_seen = False
        self._row_container_seen = False

    def _observe(self, path: str, kind: str, row_seen: set[str]) -> None:
        receipt = self.manifest.setdefault(path, _PathStats())
        receipt.observed_json_types.add(kind)
        if path not in row_seen:
            receipt.present_rows += 1
            row_seen.add(path)

    def _discard(self) -> None:
        self.reader.whitespace()
        char = self.reader.peek()
        if char == "{":
            self.reader.take(); self.reader.whitespace()
            if self.reader.peek() == "}":
                self.reader.take(); return
            seen: set[str] = set()
            while True:
                key = self.reader.string(materialize=True)
                assert key is not None
                if key in seen:
                    raise ContractViolation("duplicate JSON object key")
                seen.add(key)
                self.reader.whitespace(); self.reader.expect(":")
                self._discard(); self.reader.whitespace()
                delimiter = self.reader.take()
                if delimiter == "}": return
                if delimiter != ",": raise ContractViolation("invalid JSON object delimiter")
                self.reader.whitespace()
        elif char == "[":
            self.reader.take(); self.reader.whitespace()
            if self.reader.peek() == "]":
                self.reader.take(); return
            while True:
                self._discard(); self.reader.whitespace()
                delimiter = self.reader.take()
                if delimiter == "]": return
                if delimiter != ",": raise ContractViolation("invalid JSON array delimiter")
                self.reader.whitespace()
        else:
            self.reader.scalar_type()

    def _row_value(self, path: str, row_seen: set[str]) -> str:
        self.reader.whitespace()
        char = self.reader.peek()
        if char == "{":
            kind = "object"; self._observe(path, kind, row_seen)
            self.reader.take(); self.reader.whitespace()
            if self.reader.peek() == "}": self.reader.take(); return kind
            keys: set[str] = set()
            while True:
                key = self.reader.string(materialize=True)
                assert key is not None
                if key in keys: raise ContractViolation("duplicate key in retained row object")
                keys.add(key)
                self.reader.whitespace(); self.reader.expect(":")
                self._row_value(_pointer_join(path, key), row_seen)
                self.reader.whitespace(); delimiter = self.reader.take()
                if delimiter == "}": return kind
                if delimiter != ",": raise ContractViolation("invalid retained row object delimiter")
                self.reader.whitespace()
        if char == "[":
            kind = "array"; self._observe(path, kind, row_seen)
            wildcard = f"{path}/*"
            self.reader.take(); self.reader.whitespace()
            if self.reader.peek() == "]": self.reader.take(); return kind
            while True:
                self._row_value(wildcard, row_seen)
                self.reader.whitespace(); delimiter = self.reader.take()
                if delimiter == "]": return kind
                if delimiter != ",": raise ContractViolation("invalid retained row array delimiter")
                self.reader.whitespace()
        kind = self.reader.scalar_type()
        self._observe(path, kind, row_seen)
        return kind

    def _rows(self) -> None:
        self.reader.whitespace(); self.reader.expect("["); self.reader.whitespace()
        if self.reader.peek() == "]": self.reader.take(); return
        while True:
            _require(self.reader.peek() == "{", "each retained row schema envelope must be an object")
            self._row_value("", set())
            self.row_count += 1
            self.reader.whitespace(); delimiter = self.reader.take()
            if delimiter == "]": return
            if delimiter != ",": raise ContractViolation("invalid retained row-container delimiter")
            self.reader.whitespace()

    def scan(self) -> StructuralReceipt:
        self.reader.whitespace(); self.reader.expect("{"); self.reader.whitespace()
        root_keys: set[str] = set()
        if self.reader.peek() == "}": self.reader.take()
        else:
            while True:
                key = self.reader.string(materialize=True)
                assert key is not None
                if key in root_keys: raise ContractViolation("duplicate root JSON key")
                root_keys.add(key)
                self.reader.whitespace(); self.reader.expect(":")
                if key == ROW_CONTAINER_KEY:
                    self._row_container_seen = True
                    self._rows()
                elif key == SELF_DESCRIPTION_KEY:
                    self._self_description_seen = True
                    self.self_description = self.reader.materialized()
                else:
                    self._discard()
                self.reader.whitespace(); delimiter = self.reader.take()
                if delimiter == "}": break
                if delimiter != ",": raise ContractViolation("invalid root object delimiter")
                self.reader.whitespace()
        self.reader.whitespace()
        _require(self.reader.peek() == "", "trailing content after root JSON object")
        _require(self._row_container_seen, f"required row container {ROW_CONTAINER_KEY!r} is absent")
        return StructuralReceipt(self.row_count, self.manifest, self.self_description)


def scan_structural_schema(path: Path) -> StructuralReceipt:
    scanner: _StructuralScanner | None = None
    try:
        with path.open("r", encoding="utf-8", errors="strict", newline="") as handle:
            scanner = _StructuralScanner(_JsonReader(handle))
            return scanner.scan()
    except (OSError, UnicodeError, ContractViolation) as exc:
        count = scanner.row_count if scanner is not None else 0
        detail = str(exc) if isinstance(exc, ContractViolation) else type(exc).__name__
        raise StructuralParseFailure(f"streaming structural parse failed: {detail}", count) from exc


def _blank_slot_receipts() -> dict[str, dict[str, dict[str, Any]]]:
    return {
        group: {
            slot: {
                "source_path": None,
                "binding_basis": None,
                "declared_types": None,
                "nullable": None,
                "presence": "unbound",
            }
            for slot in slots
        }
        for group, slots in REQUIRED_SLOTS.items()
    }


def _binding_paths(binding: Mapping[str, Any]) -> tuple[str, list[str], str]:
    kind = binding.get("binding_kind")
    if kind == "direct_field":
        _require(set(binding) == {"binding_kind", "path", "declared_types", "nullable"}, "direct binding keys are not exact")
        path = binding.get("path")
        if not isinstance(path, str) or not path.startswith("/") or "*" in path or "{" in path:
            raise BindingUnavailable("direct binding must declare one exact JSON pointer")
        return path, [path], kind
    if kind == "subject_indexed_field":
        _require(
            set(binding) == {"binding_kind", "path_template", "subject_keys", "subject_role", "declared_types", "nullable"},
            "subject-indexed binding keys are not exact",
        )
        template = binding.get("path_template")
        subjects = binding.get("subject_keys")
        role = binding.get("subject_role")
        if not isinstance(template, str) or template.count("{subject}") != 1 or not template.startswith("/"):
            raise BindingUnavailable("subject-indexed binding needs one explicit path template")
        if not isinstance(subjects, list) or not subjects or any(not isinstance(x, str) or not x for x in subjects):
            raise BindingUnavailable("subject-indexed binding needs explicit subject keys")
        if len(set(subjects)) != len(subjects) or role not in {"actual_persisted_incumbent", "unchanged_actual_proposal"}:
            raise BindingUnavailable("subject-indexed binding is ambiguous")
        paths = [template.replace("{subject}", _pointer_token(subject)) for subject in subjects]
        return template, paths, kind
    raise BindingUnavailable("binding kind is missing or ambiguous")


def _declared_envelope(binding: Mapping[str, Any]) -> tuple[set[str], bool]:
    types = binding.get("declared_types")
    nullable = binding.get("nullable")
    if not isinstance(types, list) or not types or any(not isinstance(x, str) for x in types):
        raise BindingUnavailable("binding declared_types must be a nonempty literal list")
    declared = set(types)
    if len(declared) != len(types) or not declared <= (_JSON_TYPES - {"null"}) or type(nullable) is not bool:
        raise BindingUnavailable("binding type/nullability declaration is ambiguous")
    return declared, nullable


def _presence_receipt(
    paths: Sequence[str], declared: set[str], nullable: bool,
    manifest: Mapping[str, _PathStats], row_count: int,
) -> tuple[str, list[dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    complete = True
    for path in paths:
        stats = manifest.get(path, _PathStats())
        non_null = stats.observed_json_types - {"null"}
        path_complete = (
            stats.present_rows == row_count
            and non_null <= declared
            and (nullable or "null" not in stats.observed_json_types)
        )
        complete &= path_complete
        details.append({
            "path": path,
            "present_rows": stats.present_rows,
            "complete_presence": stats.present_rows == row_count,
            "observed_json_types": sorted(stats.observed_json_types),
            "declared_type_compatible": non_null <= declared,
            "nullability_compatible": nullable or "null" not in stats.observed_json_types,
        })
    return ("complete" if complete else "incomplete"), details


def bind_self_description(receipt: StructuralReceipt) -> dict[str, Any]:
    slots = _blank_slot_receipts()
    base = {
        "embedded_key": SELF_DESCRIPTION_KEY,
        "authenticated_by_immutable_sha256": True,
        "status": "unavailable",
        "slots": slots,
        "closed_handoff_allowlist": {"status": "unbound", "closed": None, "members": []},
        "first_failure": None,
    }
    description = receipt.self_description
    if description is None:
        base["first_failure"] = "authenticated embedded self-description is absent"
        return base
    try:
        if not isinstance(description, Mapping):
            raise BindingUnavailable("embedded self-description is not an object")
        if set(description) != {"schema_kind", "schema_version", "row_container", "slots", "closed_handoff_allowlist"}:
            raise BindingUnavailable("embedded self-description envelope is ambiguous")
        if description.get("schema_kind") != SELF_DESCRIPTION_KIND or description.get("schema_version") != 1:
            raise BindingUnavailable("embedded self-description identity is unrecognized")
        if description.get("row_container") != ROW_CONTAINER_POINTER:
            raise BindingUnavailable("embedded self-description binds another row container")
        described_slots = description.get("slots")
        if not isinstance(described_slots, Mapping) or set(described_slots) != set(REQUIRED_SLOTS):
            raise BindingUnavailable("required slot groups are missing or ambiguous")
        any_incomplete = False
        for group, required in REQUIRED_SLOTS.items():
            group_bindings = described_slots[group]
            if not isinstance(group_bindings, Mapping) or set(group_bindings) != set(required):
                raise BindingUnavailable(f"required slots for {group} are missing or ambiguous")
            for slot in required:
                binding = group_bindings[slot]
                if not isinstance(binding, Mapping):
                    raise BindingUnavailable(f"slot {group}/{slot} is unbound")
                source_path, paths, basis = _binding_paths(binding)
                declared, nullable = _declared_envelope(binding)
                presence, details = _presence_receipt(paths, declared, nullable, receipt.manifest, receipt.row_count)
                any_incomplete |= presence != "complete"
                slots[group][slot] = {
                    "source_path": source_path,
                    "binding_basis": basis,
                    "declared_types": sorted(declared),
                    "nullable": nullable,
                    "presence": presence,
                    "schema_evidence": details,
                }
        allowlist = description.get("closed_handoff_allowlist")
        if not isinstance(allowlist, Mapping) or set(allowlist) != {"closed", "members"} or allowlist.get("closed") is not True:
            raise BindingUnavailable("closed handoff allowlist is unbound")
        members = allowlist.get("members")
        if not isinstance(members, list):
            raise BindingUnavailable("closed handoff allowlist members are not explicitly enumerated")
        member_receipts: list[dict[str, Any]] = []
        names: set[str] = set()
        for member in members:
            if not isinstance(member, Mapping) or set(member) != {"member", "binding"}:
                raise BindingUnavailable("allowlist member declaration is ambiguous")
            name = member.get("member")
            binding = member.get("binding")
            if not isinstance(name, str) or not name or name in names or not isinstance(binding, Mapping):
                raise BindingUnavailable("allowlist member identity or binding is ambiguous")
            names.add(name)
            source_path, paths, basis = _binding_paths(binding)
            declared, nullable = _declared_envelope(binding)
            presence, details = _presence_receipt(paths, declared, nullable, receipt.manifest, receipt.row_count)
            any_incomplete |= presence != "complete"
            member_receipts.append({
                "member": name, "source_path": source_path, "binding_basis": basis,
                "declared_types": sorted(declared), "nullable": nullable,
                "presence": presence, "schema_evidence": details,
            })
        base["closed_handoff_allowlist"] = {
            "status": "complete" if all(x["presence"] == "complete" for x in member_receipts) else "incomplete",
            "closed": True,
            "members": member_receipts,
        }
        base["status"] = "authenticated_incomplete" if any_incomplete else "authenticated_complete"
        base["first_failure"] = (
            "authenticated binding exists but required retained schema is incomplete"
            if any_incomplete else None
        )
        return base
    except (BindingUnavailable, ContractViolation) as exc:
        base["first_failure"] = str(exc)
        return base


def _manifest_result(receipt: StructuralReceipt) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "present_rows": stats.present_rows,
            "complete_presence": stats.present_rows == receipt.row_count,
            "observed_json_types": sorted(stats.observed_json_types),
            "nullable_observed": "null" in stats.observed_json_types,
        }
        for path, stats in sorted(receipt.manifest.items())
        if path
    ]


def _caps_violated(counters: Mapping[str, Any], expected_rows: int) -> list[str]:
    caps = dict(HARD_CAPS)
    caps["row_schema_envelopes"] = expected_rows
    violations: list[str] = []
    for name, cap in caps.items():
        value = counters.get(name)
        if type(value) is not int or value < 0 or value > cap:
            violations.append(name)
    return violations


def _select_branch(result: Mapping[str, Any], expected_rows: int) -> tuple[str, str | None]:
    violations = _caps_violated(result["counters"], expected_rows)
    if result.get("scope_violations") or violations:
        reason = (result.get("scope_violations") or [f"hard cap exceeded: {violations[0]}"])[0]
        return TERMINAL_BRANCHES[0], reason
    source = result["source_binding"]
    if source.get("status") != "valid":
        return TERMINAL_BRANCHES[1], source.get("first_failure")
    binding = result["dto_binding"]
    if binding.get("status") == "unavailable":
        return TERMINAL_BRANCHES[2], binding.get("first_failure")
    if binding.get("status") == "authenticated_incomplete":
        return TERMINAL_BRANCHES[3], binding.get("first_failure")
    return TERMINAL_BRANCHES[4], None


def _branch_boundary(branch: str) -> tuple[str, str]:
    return {
        TERMINAL_BRANCHES[0]: (
            "a compliant blind audit might remain mechanically possible, but this one-shot treatment cannot rerun",
            "scope violation prevents every source, DTO, retention, and scientific inference",
        ),
        TERMINAL_BRANCHES[1]: (
            "the intended immutable DTO might be structurally sufficient despite this source or locator failure",
            "no DTO binding or retention conclusion follows because immutable source admission failed",
        ),
        TERMINAL_BRANCHES[2]: (
            "the bytes might retain useful fields, but no authenticated self-description binds them to required slots",
            "field names and values cannot resolve the missing or ambiguous semantic binding",
        ),
        TERMINAL_BRANCHES[3]: (
            "a separately motivated future host or data-acquisition object might retain the missing envelope",
            "the authenticated current DTO binding is incomplete and no reconstruction is allowed",
        ),
        TERMINAL_BRANCHES[4]: (
            "all required slots are structurally addressable in the authenticated immutable DTO",
            "structural admission does not establish any row-level scientific predicate",
        ),
    }[branch]


def _base_result(locator: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": "VSP05_A4_BLIND_PORTABLE_LOCATOR_DTO_RETAINED_FIELD_ADMISSION",
        "formal": False,
        "candidate_id": CANDIDATE_ID,
        "treatment_id": TREATMENT_ID,
        "terminal_branch": None,
        "first_failure": None,
        "branch_precedence_applied": list(TERMINAL_BRANCHES),
        "source_binding": {
            "status": "invalid",
            "first_failure": None,
            "portable_locator_kind": "repository_relative_posix",
            "expected_locator": PORTABLE_LOCATOR,
            "normalized_relative_locator": None,
            "verified_checkout_root_supplied": False,
            "root_containment": False,
            "absolute_path_emitted": False,
            "expected_sha256": EXPECTED_SHA256,
            "observed_sha256": None,
            "opaque_bytes_read": 0,
            "parser_status": "not_started",
            "row_container_pointer": ROW_CONTAINER_POINTER,
            "expected_row_containers": EXPECTED_ROW_CONTAINERS,
            "observed_row_containers": 0,
            "accepted_source_commit": ACCEPTED_SOURCE_COMMIT,
            "accepted_publication_commit": ACCEPTED_PUBLICATION_COMMIT,
        },
        "dto_binding": {
            "embedded_key": SELF_DESCRIPTION_KEY,
            "authenticated_by_immutable_sha256": False,
            "status": "unavailable",
            "slots": _blank_slot_receipts(),
            "closed_handoff_allowlist": {"status": "unbound", "closed": None, "members": []},
            "first_failure": "structural schema pass was not reached",
        },
        "schema_presence_manifest": [],
        "scope_violations": [],
        "counters": {name: 0 for name in HARD_CAPS},
        "attestations": {
            "semantic_values_read": 0,
            "row_samples_or_presence_vectors_emitted": 0,
            "code_semantic_inference_used": False,
            "reconstruction_used": False,
            "fallback_or_alternate_used": False,
            "source_reopened_after_structural_pass": False,
            "environment_specific_absolute_identity_emitted": False,
        },
        "publication": {
            "public_result_locator": PUBLIC_RESULT_LOCATOR,
            "public_index_locator": PUBLIC_INDEX_LOCATOR,
            "operator_receipt": None,
        },
        "strongest_alternative": "immutable bytes may be valid while DTO semantic binding remains unavailable",
        "residual_uncertainty": "a blind schema admission cannot establish any row-level scientific predicate",
        "claim_boundary": "retention addressability only; no semantic audit, learner, successor, promotion, or retirement",
        "scientific_disposition": None,
        "successor_selected": False,
    }


def _run_component_audit(
    checkout_root: str | Path,
    *,
    portable_locator: str = PORTABLE_LOCATOR,
    expected_sha256: str = EXPECTED_SHA256,
    expected_row_containers: int = EXPECTED_ROW_CONTAINERS,
) -> dict[str, Any]:
    """Run one blind audit; component overrides support opaque proof fixtures only."""

    result = _base_result(portable_locator)
    counters = result["counters"]
    source = result["source_binding"]
    counters["registered_admission_audits"] = 1
    source["expected_sha256"] = expected_sha256
    source["expected_row_containers"] = expected_row_containers
    source["verified_checkout_root_supplied"] = Path(checkout_root).is_absolute()
    try:
        _require(
            type(expected_row_containers) is int
            and 0 <= expected_row_containers <= EXPECTED_ROW_CONTAINERS,
            "component row-cardinality bound exceeds the registered hard cap",
        )
        _require(
            isinstance(expected_sha256, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None,
            "expected opaque SHA-256 is invalid",
        )
        counters["locator_resolutions"] = 1
        input_path = resolve_portable_locator(checkout_root, portable_locator)
        source["normalized_relative_locator"] = portable_locator
        source["root_containment"] = True
        counters["opaque_hash_passes"] = 1
        observed_sha, byte_count = _opaque_sha256(input_path)
        source["observed_sha256"] = observed_sha
        source["opaque_bytes_read"] = byte_count
        _require(observed_sha == expected_sha256, "immutable source SHA-256 mismatch")
        counters["structural_schema_passes"] = 1
        receipt = scan_structural_schema(input_path)
        counters["row_schema_envelopes"] = receipt.row_count
        source["parser_status"] = "valid"
        source["observed_row_containers"] = receipt.row_count
        _require(receipt.row_count == expected_row_containers, "row-container cardinality mismatch")
        source["status"] = "valid"
        source["first_failure"] = None
        result["schema_presence_manifest"] = _manifest_result(receipt)
        result["dto_binding"] = bind_self_description(receipt)
    except StructuralParseFailure as exc:
        counters["row_schema_envelopes"] = exc.row_count
        source["observed_row_containers"] = exc.row_count
        source["first_failure"] = str(exc)
        source["parser_status"] = "invalid"
    except ContractViolation as exc:
        source["first_failure"] = str(exc)
        if counters["structural_schema_passes"]:
            source["parser_status"] = "invalid"
    branch, first_failure = _select_branch(result, expected_row_containers)
    result["terminal_branch"] = branch
    result["first_failure"] = first_failure
    result["strongest_alternative"], result["residual_uncertainty"] = _branch_boundary(branch)
    _validate_component_result(result, expected_row_containers=expected_row_containers)
    return result


def run_admission_audit(checkout_root: str | Path) -> dict[str, Any]:
    """Run the registered audit with immutable locator, digest, and cardinality."""

    return _run_component_audit(
        checkout_root,
        portable_locator=PORTABLE_LOCATOR,
        expected_sha256=EXPECTED_SHA256,
        expected_row_containers=EXPECTED_ROW_CONTAINERS,
    )


def _validate_binding_receipt(receipt: Mapping[str, Any], row_count: int, context: str) -> None:
    expected_fields = {"source_path", "binding_basis", "declared_types", "nullable", "presence"}
    if receipt.get("presence") == "unbound":
        _require(set(receipt) == expected_fields, f"{context} unbound receipt fields drifted")
        _require(all(receipt.get(name) is None for name in expected_fields - {"presence"}), f"{context} fabricated an unbound declaration")
        return
    expected_fields.add("schema_evidence")
    _require(set(receipt) == expected_fields, f"{context} bound receipt fields drifted")
    _require(receipt.get("presence") in {"complete", "incomplete"}, f"{context} presence drifted")
    _require(isinstance(receipt.get("source_path"), str) and receipt["source_path"].startswith("/"), f"{context} source path drifted")
    _require(receipt.get("binding_basis") in {"direct_field", "subject_indexed_field"}, f"{context} binding basis drifted")
    declared = receipt.get("declared_types")
    _require(isinstance(declared, list) and all(isinstance(kind, str) for kind in declared), f"{context} declared type envelope drifted")
    _require(declared == sorted(set(declared)) and set(declared) <= (_JSON_TYPES - {"null"}), f"{context} declared type envelope drifted")
    _require(type(receipt.get("nullable")) is bool, f"{context} declared nullability drifted")
    evidence = receipt.get("schema_evidence")
    _require(isinstance(evidence, list) and evidence, f"{context} schema evidence is absent")
    evidence_complete = True
    for item in evidence:
        _require(isinstance(item, Mapping) and set(item) == {"path", "present_rows", "complete_presence", "observed_json_types", "declared_type_compatible", "nullability_compatible"}, f"{context} schema evidence fields drifted")
        present = item.get("present_rows")
        observed = item.get("observed_json_types")
        _require(isinstance(item.get("path"), str) and item["path"].startswith("/"), f"{context} schema evidence path drifted")
        _require(type(present) is int and 0 <= present <= row_count, f"{context} schema evidence count drifted")
        _require(item.get("complete_presence") is (present == row_count), f"{context} schema evidence completeness drifted")
        _require(isinstance(observed, list) and all(isinstance(kind, str) for kind in observed) and observed == sorted(set(observed)) and set(observed) <= _JSON_TYPES, f"{context} observed type envelope drifted")
        _require(type(item.get("declared_type_compatible")) is bool and type(item.get("nullability_compatible")) is bool, f"{context} compatibility receipts drifted")
        evidence_complete &= bool(item["complete_presence"] and item["declared_type_compatible"] and item["nullability_compatible"])
    _require(receipt.get("presence") == ("complete" if evidence_complete else "incomplete"), f"{context} aggregate presence drifted")


def _validate_component_result(
    result: Mapping[str, Any], *, expected_row_containers: int
) -> None:
    """Validate one internally authorized opaque component fixture receipt."""

    _require(
        type(expected_row_containers) is int
        and 0 <= expected_row_containers <= EXPECTED_ROW_CONTAINERS,
        "result row-cardinality bound exceeds the registered hard cap",
    )
    _require(set(result) == set(_base_result(PORTABLE_LOCATOR)), "top-level result envelope drifted")
    _require(result.get("schema_version") == SCHEMA_VERSION, "result schema version drifted")
    _require(result.get("artifact_kind") == "VSP05_A4_BLIND_PORTABLE_LOCATOR_DTO_RETAINED_FIELD_ADMISSION", "artifact kind drifted")
    _require(result.get("formal") is False and result.get("candidate_id") == CANDIDATE_ID and result.get("treatment_id") == TREATMENT_ID, "treatment identity drifted")
    _require(result.get("branch_precedence_applied") == list(TERMINAL_BRANCHES), "branch precedence receipt drifted")
    counters = result.get("counters")
    _require(isinstance(counters, Mapping) and set(counters) == set(HARD_CAPS), "counter envelope drifted")
    _require(all(type(value) is int and value >= 0 for value in counters.values()), "counter values must be nonnegative integers")
    attestations = result.get("attestations")
    _require(isinstance(attestations, Mapping), "attestation envelope is absent")
    _require(set(attestations) == set(_base_result(PORTABLE_LOCATOR)["attestations"]), "attestation fields drifted")
    _require(attestations.get("semantic_values_read") == counters["row_semantic_values_read"] == 0, "semantic-value blindness drifted")
    _require(attestations.get("row_samples_or_presence_vectors_emitted") == counters["row_samples_or_presence_vectors_emitted"] == 0, "row sample/presence-vector blindness drifted")
    _require(attestations.get("code_semantic_inference_used") is False and counters["code_semantics_reads"] == 0, "code-semantic blindness drifted")
    _require(attestations.get("reconstruction_used") is False, "reconstruction attestation drifted")
    _require(attestations.get("fallback_or_alternate_used") is False and counters["retry_rescue_or_fallback"] == 0, "fallback/retry attestation drifted")
    _require(attestations.get("source_reopened_after_structural_pass") is False, "source-reopen attestation drifted")
    _require(attestations.get("environment_specific_absolute_identity_emitted") is False, "absolute-identity attestation drifted")
    source = result.get("source_binding")
    _require(isinstance(source, Mapping), "source binding envelope is absent")
    _require(set(source) == set(_base_result(PORTABLE_LOCATOR)["source_binding"]), "source binding fields drifted")
    _require(source.get("expected_locator") == PORTABLE_LOCATOR, "registered portable locator drifted")
    _require(source.get("status") in {"valid", "invalid"}, "source stage status drifted")
    _require(source.get("absolute_path_emitted") is False, "absolute environment identity was emitted")
    _require(source.get("accepted_source_commit") == ACCEPTED_SOURCE_COMMIT, "accepted source commit drifted")
    _require(source.get("accepted_publication_commit") == ACCEPTED_PUBLICATION_COMMIT, "accepted publication commit drifted")
    _require(counters["locator_resolutions"] == 1, "executed audit must attempt exactly one locator resolution")
    _require(counters["structural_schema_passes"] <= counters["opaque_hash_passes"] <= counters["locator_resolutions"], "source pass counter order drifted")
    if source.get("root_containment") is True:
        _require(source.get("verified_checkout_root_supplied") is True, "contained source lacks a verified caller root")
        _require(source.get("normalized_relative_locator") == PORTABLE_LOCATOR, "contained source locator stage drifted")
        _require(counters["opaque_hash_passes"] == 1, "contained source lacks its one opaque hash pass")
    else:
        _require(source.get("root_containment") is False, "root containment receipt is not boolean")
        _require(source.get("normalized_relative_locator") is None, "uncontained source fabricated a normalized locator")
        _require(counters["opaque_hash_passes"] == 0, "hash pass began before root containment")
    if counters["opaque_hash_passes"] == 0:
        _require(source.get("observed_sha256") is None and source.get("opaque_bytes_read") == 0, "pre-hash source stage drifted")
    if (
        counters["opaque_hash_passes"] == 1
        and source.get("observed_sha256") == source.get("expected_sha256")
    ):
        _require(
            counters["structural_schema_passes"] == 1,
            "matching immutable SHA must advance exactly one structural pass",
        )
    if counters["structural_schema_passes"] == 0:
        _require(source.get("parser_status") == "not_started", "parser started without a structural pass")
        _require(counters["row_schema_envelopes"] == source.get("observed_row_containers") == 0, "pre-parse row counters drifted")
        _require(result.get("schema_presence_manifest") == [], "pre-parse result fabricated a schema manifest")
    else:
        _require(counters["opaque_hash_passes"] == 1 and source.get("root_containment") is True, "structural pass lacks contained opaque source")
        _require(source.get("observed_sha256") == source.get("expected_sha256"), "structural pass began before immutable SHA admission")
        _require(source.get("parser_status") in {"valid", "invalid"}, "structural parser stage drifted")
        _require(counters["row_schema_envelopes"] == source.get("observed_row_containers"), "structural row counter drifted")
    if source.get("status") == "invalid":
        _require(isinstance(source.get("first_failure"), str) and source["first_failure"], "invalid source lacks its first failure")
        _require(source.get("parser_status") != "valid", "invalid source claims a valid completed parser stage")
        _require(result.get("schema_presence_manifest") == [], "invalid source fabricated a schema manifest")
        _require(result.get("dto_binding", {}).get("authenticated_by_immutable_sha256") is False, "invalid source fabricated DTO authentication")
    publication = result.get("publication")
    _require(isinstance(publication, Mapping), "publication envelope is absent")
    _require(set(publication) == {"public_result_locator", "public_index_locator", "operator_receipt"}, "publication fields drifted")
    _require(publication.get("public_result_locator") == PUBLIC_RESULT_LOCATOR, "public result locator drifted")
    _require(publication.get("public_index_locator") == PUBLIC_INDEX_LOCATOR, "public index locator drifted")
    _require(publication.get("operator_receipt") is None, "component fabricated an Operator receipt")
    _require(result.get("scientific_disposition") is None and result.get("successor_selected") is False, "component crossed the scientific decision boundary")
    if source.get("status") == "valid":
        _require(source.get("first_failure") is None, "valid source retains a failure receipt")
        _require(source.get("normalized_relative_locator") == PORTABLE_LOCATOR, "normalized locator binding drifted")
        _require(source.get("root_containment") is True and source.get("verified_checkout_root_supplied") is True, "root containment receipt drifted")
        _require(source.get("observed_sha256") == source.get("expected_sha256"), "immutable SHA binding drifted")
        _require(source.get("parser_status") == "valid", "valid source lacks valid parser receipt")
        _require(source.get("expected_row_containers") == expected_row_containers, "expected row cardinality drifted")
        _require(source.get("observed_row_containers") == expected_row_containers, "observed row cardinality drifted")
        _require(counters["locator_resolutions"] == counters["opaque_hash_passes"] == counters["structural_schema_passes"] == 1, "valid source pass counters drifted")
        _require(counters["row_schema_envelopes"] == expected_row_containers, "row schema-envelope counter drifted")
        dto = result.get("dto_binding")
        _require(isinstance(dto, Mapping) and dto.get("authenticated_by_immutable_sha256") is True, "DTO authentication receipt drifted")
        slot_groups = dto.get("slots")
        _require(isinstance(slot_groups, Mapping) and set(slot_groups) == set(REQUIRED_SLOTS), "DTO slot-group envelope drifted")
        for group, slots in REQUIRED_SLOTS.items():
            _require(isinstance(slot_groups[group], Mapping) and set(slot_groups[group]) == set(slots), f"DTO slot roster drifted for {group}")
    manifest = result.get("schema_presence_manifest")
    _require(isinstance(manifest, list), "schema-presence manifest is not a list")
    manifest_paths: set[str] = set()
    for entry in manifest:
        _require(isinstance(entry, Mapping) and set(entry) == {"path", "present_rows", "complete_presence", "observed_json_types", "nullable_observed"}, "schema-presence manifest entry drifted")
        path = entry.get("path")
        types = entry.get("observed_json_types")
        present = entry.get("present_rows")
        _require(isinstance(path, str) and path.startswith("/") and path not in manifest_paths, "schema-presence path is invalid or duplicated")
        manifest_paths.add(path)
        _require(type(present) is int and 0 <= present <= counters["row_schema_envelopes"], "schema-presence count exceeds row envelopes")
        _require(entry.get("complete_presence") is (present == counters["row_schema_envelopes"]), "schema-presence completeness drifted")
        _require(isinstance(types, list) and all(isinstance(item, str) for item in types), "schema-presence type envelope drifted")
        _require(types == sorted(set(types)) and set(types) <= _JSON_TYPES, "schema-presence type envelope drifted")
        _require(entry.get("nullable_observed") is ("null" in types), "schema-presence nullability drifted")
    dto = result.get("dto_binding")
    _require(isinstance(dto, Mapping) and set(dto) == {"embedded_key", "authenticated_by_immutable_sha256", "status", "slots", "closed_handoff_allowlist", "first_failure"}, "DTO binding envelope drifted")
    _require(dto.get("embedded_key") == SELF_DESCRIPTION_KEY and dto.get("status") in {"unavailable", "authenticated_incomplete", "authenticated_complete"}, "DTO binding identity/status drifted")
    slot_groups = dto.get("slots")
    _require(isinstance(slot_groups, Mapping) and set(slot_groups) == set(REQUIRED_SLOTS), "DTO slot-group envelope drifted")
    for group, slots in REQUIRED_SLOTS.items():
        _require(isinstance(slot_groups[group], Mapping) and set(slot_groups[group]) == set(slots), f"DTO slot roster drifted for {group}")
        for slot in slots:
            slot_receipt = slot_groups[group][slot]
            _require(isinstance(slot_receipt, Mapping), f"DTO slot receipt is invalid for {group}/{slot}")
            _validate_binding_receipt(slot_receipt, counters["row_schema_envelopes"], f"DTO slot {group}/{slot}")
    allowlist = dto.get("closed_handoff_allowlist")
    _require(isinstance(allowlist, Mapping) and set(allowlist) == {"status", "closed", "members"}, "closed-allowlist envelope drifted")
    _require(allowlist.get("status") in {"unbound", "complete", "incomplete"} and isinstance(allowlist.get("members"), list), "closed-allowlist status drifted")
    if allowlist.get("status") == "unbound":
        _require(allowlist.get("closed") is None and allowlist.get("members") == [], "unbound allowlist fabricated a declaration")
    else:
        _require(allowlist.get("closed") is True, "bound allowlist is not closed")
        names: set[str] = set()
        for member in allowlist["members"]:
            _require(isinstance(member, Mapping) and set(member) == {"member", "source_path", "binding_basis", "declared_types", "nullable", "presence", "schema_evidence"}, "allowlist member receipt fields drifted")
            name = member.get("member")
            _require(isinstance(name, str) and name and name not in names, "allowlist member identity drifted")
            names.add(name)
            binding_receipt = {key: value for key, value in member.items() if key != "member"}
            _validate_binding_receipt(binding_receipt, counters["row_schema_envelopes"], f"allowlist member {name}")
        aggregate = "complete" if all(member["presence"] == "complete" for member in allowlist["members"]) else "incomplete"
        _require(allowlist.get("status") == aggregate, "closed-allowlist aggregate status drifted")
    branch, first_failure = _select_branch(result, expected_row_containers)
    _require(result.get("terminal_branch") == branch, "terminal branch precedence drifted")
    _require(result.get("first_failure") == first_failure, "first-failure receipt drifted")
    alternative, uncertainty = _branch_boundary(branch)
    _require(result.get("strongest_alternative") == alternative, "strongest-alternative receipt drifted")
    _require(result.get("residual_uncertainty") == uncertainty, "residual-uncertainty receipt drifted")
    if branch == TERMINAL_BRANCHES[4]:
        _require(source.get("status") == "valid", "sufficient branch lacks valid source binding")
        _require(result.get("dto_binding", {}).get("status") == "authenticated_complete", "sufficient branch lacks complete authenticated DTO binding")


def validate_result(result: Mapping[str, Any]) -> None:
    """Validate a production/publication artifact against frozen A4 identity."""

    source = result.get("source_binding")
    counters = result.get("counters")
    _require(isinstance(source, Mapping), "production source binding is absent")
    _require(isinstance(counters, Mapping), "production counters are absent")
    _require(source.get("expected_sha256") == EXPECTED_SHA256, "production expected SHA-256 drifted")
    _require(source.get("expected_row_containers") == EXPECTED_ROW_CONTAINERS, "production expected row cardinality drifted")
    _require(counters.get("registered_admission_audits") == 1, "production artifact is not one executed registered admission audit")
    _validate_component_result(
        result, expected_row_containers=EXPECTED_ROW_CONTAINERS
    )


def write_result_once(path: str | Path, result: Mapping[str, Any]) -> None:
    """Atomically install one canonical result without overwrite or retry."""

    validate_result(result)
    _install_result_once(path, result)


def _install_result_once(path: str | Path, result: Mapping[str, Any]) -> None:
    """Install an already validated result; component tests exercise mechanics here."""

    destination = Path(path)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite one-shot A4 artifact: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(dict(result), indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        os.link(temporary, destination)
        temporary.unlink()
    except BaseException:
        try: temporary.unlink()
        except FileNotFoundError: pass
        raise


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout-root", required=True, help="caller-verified absolute checkout/worktree root")
    parser.add_argument("--output", required=True, help="new one-shot A4 JSON artifact")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_admission_audit(args.checkout_root)
    write_result_once(args.output, result)
    print(json.dumps({
        "output": str(Path(args.output)),
        "terminal_branch": result["terminal_branch"],
        "row_schema_envelopes": result["counters"]["row_schema_envelopes"],
        "semantic_values_read": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
