"""Bounded recent-transition ring and the failure bundle writer (plan section 11).

Why this module exists: when a scientific run fails, the useful thing to hand to a reviewer is a
small, self-describing package of *identities and evidence*, not a copy of the experiment. This
module builds that package and enforces the three properties that make it safe to write and safe to
read:

1. **The diagnostic ring is off unless somebody turned it on.** Under the default profile
   :class:`RecentTransitionRing` performs no copy, no hash and no append; the buffer object does not
   even exist. Ordinary training therefore pays nothing for the possibility of a later bundle.
2. **A bundle is inert.** ``reproduce_command.txt`` is text, and this module deliberately provides
   no function that executes a command found in a bundle, a log or a README. Reproduction is a
   separate explicit act by a person, in a separate process.
3. **A bundle never over-promises.** Action replay, policy re-evaluation and exact
   checkpoint/runtime resume are three *separate* recorded statuses. When the saved variates and
   runtime conditions needed for bitwise policy sampling were not recorded, the bundle says
   ``exact_policy_reproduction_unavailable``; a seed alone is never reported as exactness. Every
   truncation is stated, never silent.

Contents are restricted to what the caller explicitly passes: identities, configuration, schema,
the failure itself, the ring snapshot, runtime versions, and the named log files. There is no
directory walk, no environment-variable dump, no credential, token, key or browser profile, and no
dataset or checkpoint payload. Failure *classification* of pytest output lives in
``recommend_tests``; this module stays free of that dependency so it can be imported inside a
scientific process.
"""

from __future__ import annotations

import collections
import importlib.metadata as importlib_metadata
import os
import platform
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Deque, Mapping, Sequence

import numpy as np

from .records import Measured, Validity, content_hash, dumps, file_hash

#: Bundle schema. Bump the minor number for an additive field.
FAILURE_BUNDLE_SCHEMA = "research_support.failure_bundle.1"

#: Files whose contents are payload, not evidence: a bundle records their identity, never a copy.
PAYLOAD_SUFFIXES = frozenset(
    {
        ".pt",
        ".pth",
        ".ckpt",
        ".safetensors",
        ".bin",
        ".npz",
        ".npy",
        ".h5",
        ".hdf5",
        ".parquet",
        ".pkl",
        ".pickle",
    }
)

#: Packages whose version is worth recording. Only metadata is read; nothing is imported, so
#: writing a bundle cannot initialise torch, CUDA or a renderer.
RUNTIME_PACKAGES = ("numpy", "torch", "pytest", "scipy", "matplotlib", "gymnasium", "pettingzoo")


# --------------------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------------------

#: A user home directory, in Windows or POSIX form. Only the account name is replaced, so the
#: remaining path shape stays readable evidence.
_HOME_PATTERNS = (
    re.compile(r"(?i)([A-Za-z]:[\\/]Users[\\/])([^\\/\r\n\"'<>|]+)"),
    re.compile(r"(/home/)([^/\r\n\"' ]+)"),
    re.compile(r"(/Users/)([^/\r\n\"' ]+)"),
)

#: ``key: value`` / ``key=value`` shapes whose value must not leave the machine.
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[-_]?key|apikey|token|secret|password|passwd|pwd|authorization|auth[-_]?token"
    r"|access[-_]?key|private[-_]?key|client[-_]?secret|session[-_]?key)\b"
    r"(\s*[:=]\s*\"?|\"\s*:\s*\")"
    r"([^\s\"',}\r\n]+)"
)

#: Key names whose *string* value is treated as a credential in a structured record.
_SECRET_KEY_NAME = re.compile(
    r"(?i)(api[-_]?key|apikey|token|secret|password|passwd|pwd|authorization|auth[-_]?token"
    r"|access[-_]?key|private[-_]?key|client[-_]?secret|session[-_]?key|credential)"
)

#: Token shapes that are secret whatever they are called.
_SECRET_TOKENS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"\bssh-(?:rsa|ed25519|dss)\s+[A-Za-z0-9+/=]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


class Redactor:
    """Replaces user identities and secret shapes, remembering what it replaced.

    The mapping is only ever returned to the caller; :func:`write_failure_bundle` writes it to disk
    exclusively for an explicitly requested shareable copy, so an ordinary local bundle contains no
    way back to the original secret.
    """

    def __init__(self, *, enabled: bool = True) -> None:
        self._enabled = bool(enabled)
        self._mapping: dict[str, str] = {}
        self._reverse: dict[str, str] = {}
        self._counter = 0

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def mapping(self) -> dict[str, str]:
        """Placeholder -> original text. Empty when redaction is disabled."""

        return dict(self._mapping)

    @property
    def placeholders(self) -> list[str]:
        return sorted(self._mapping)

    def _placeholder(self, original: str, kind: str) -> str:
        existing = self._reverse.get(original)
        if existing is not None:
            return existing
        self._counter += 1
        placeholder = f"<REDACTED_{kind}_{self._counter}>"
        self._mapping[placeholder] = original
        self._reverse[original] = placeholder
        return placeholder

    def text(self, value: str) -> str:
        if not self._enabled or not value:
            return value
        redacted = value
        for pattern in _HOME_PATTERNS:

            def _home(match: re.Match[str]) -> str:
                return match.group(1) + self._placeholder(match.group(2), "USER")

            redacted = pattern.sub(_home, redacted)

        def _assignment(match: re.Match[str]) -> str:
            return match.group(1) + match.group(2) + self._placeholder(match.group(3), "SECRET")

        redacted = _SECRET_ASSIGNMENT.sub(_assignment, redacted)
        for pattern in _SECRET_TOKENS:

            def _token(match: re.Match[str]) -> str:
                return self._placeholder(match.group(0), "SECRET")

            redacted = pattern.sub(_token, redacted)
        return redacted

    def structure(self, value: Any) -> Any:
        """Redact strings inside a JSON-shaped structure, keys included.

        A structured configuration splits ``api_key = "..."`` into a key string and a value string,
        so the text pattern for an assignment never sees it. A *string* value under a secret-looking
        key is therefore replaced wholesale. Non-string values are left alone on purpose: a
        hyperparameter such as ``token_dim: 64`` is evidence, not a credential.
        """

        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, Mapping):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                name = str(key)
                if self._enabled and _SECRET_KEY_NAME.search(name) and isinstance(item, str):
                    redacted[self.text(name)] = self._placeholder(item, "SECRET")
                else:
                    redacted[self.text(name)] = self.structure(item)
            return redacted
        if isinstance(value, (list, tuple)):
            return [self.structure(v) for v in value]
        if isinstance(value, Path):
            return self.text(str(value))
        return value


# --------------------------------------------------------------------------------------
# Recent transition ring
# --------------------------------------------------------------------------------------


class RecentTransitionRing:
    """Disabled by default; under ``profile=off`` nothing is copied, hashed or appended.

    When disabled there is no buffer at all (``_buffer is None``): :meth:`append` returns ``False``
    before it touches the argument, so a producer cannot pay for a diagnostic it did not enable and
    a mutation-detecting mapping passed to a disabled ring records no access.

    When enabled, appended transitions are copied. Array values are copied with
    ``np.array(..., copy=True)`` so a later in-place update of the producer's own buffer cannot
    rewrite recorded history.
    """

    def __init__(self, size: int = 16, *, enabled: bool = False) -> None:
        if int(size) < 1:
            raise ValueError(f"ring size must be at least 1, got {size!r}")
        self._size = int(size)
        self._enabled = bool(enabled)
        self._buffer: Deque[dict[str, Any]] | None = (
            collections.deque(maxlen=self._size) if self._enabled else None
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def size(self) -> int:
        return self._size

    def append(self, transition: Mapping[str, Any]) -> bool:
        """Record one transition. Returns ``False`` immediately when the ring is disabled."""

        if not self._enabled:
            return False
        assert self._buffer is not None  # enabled implies a buffer
        self._buffer.append({str(key): _own_copy(value) for key, value in transition.items()})
        return True

    def snapshot(self) -> list[dict[str, Any]]:
        """Oldest-first copy of the retained transitions; empty when disabled."""

        if self._buffer is None:
            return []
        return [dict(item) for item in self._buffer]

    def clear(self) -> None:
        if self._buffer is not None:
            self._buffer.clear()

    def __len__(self) -> int:
        return 0 if self._buffer is None else len(self._buffer)


def _own_copy(value: Any) -> Any:
    """Return a value the ring owns, so producer-side reuse cannot rewrite recorded history."""

    if isinstance(value, np.ndarray):
        return np.array(value, copy=True)
    if isinstance(value, (list, tuple)):
        return [_own_copy(item) for item in value]
    if isinstance(value, Mapping):
        return {str(k): _own_copy(v) for k, v in value.items()}
    return value


# --------------------------------------------------------------------------------------
# Failure context
# --------------------------------------------------------------------------------------


@dataclass
class FailureContext:
    """The failure itself, including what about it is incomplete."""

    exception_type: str
    message: str
    stack: str
    phase: str  # e.g. "collection" | "update" | "environment_step" | "report"
    truncated_stack: bool = False
    incomplete_output: bool = False
    boundary_semantics: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "exception_type": self.exception_type,
            "message": self.message,
            "stack": self.stack,
            "stack_content_hash": content_hash(self.stack),
            "phase": self.phase,
            "truncated_stack": bool(self.truncated_stack),
            "incomplete_output": bool(self.incomplete_output),
            "boundary_semantics": dict(self.boundary_semantics),
        }


# --------------------------------------------------------------------------------------
# Reproduction status
# --------------------------------------------------------------------------------------

#: Keys whose presence is evidence that recorded actions exist.
_ACTION_KEYS = ("action", "actions", "executed_action", "executed_actions", "requested_action")

#: Keys whose presence is evidence that a checkpoint can be re-evaluated.
_CHECKPOINT_KEYS = (
    "checkpoint_identity",
    "checkpoint_id",
    "checkpoint_path",
    "checkpoint_hash",
)

#: Keys whose presence is evidence that exact stochastic policy sampling could be reproduced.
_VARIATE_KEYS = (
    "saved_variates",
    "policy_variates",
    "rng_state",
    "numpy_rng_state",
    "torch_rng_state",
    "python_rng_state",
    "generator_state",
)

EXACT_POLICY_REPRODUCTION_UNAVAILABLE = "exact_policy_reproduction_unavailable"


def _is_present(value: Any) -> bool:
    """True when a recorded field actually holds something.

    Written without a truth test on the value itself: ``bool(numpy_array)`` raises for any array
    with more than one element, and a transition field is normally an array.
    """

    if value is None:
        return False
    if isinstance(value, np.ndarray):
        return value.size > 0
    if isinstance(value, (str, bytes, list, tuple, dict, set, frozenset)):
        return len(value) > 0
    return True


def _has_any_key(payload: Mapping[str, Any], keys: Sequence[str]) -> bool:
    for key in keys:
        if key in payload and _is_present(payload[key]):
            return True
    return False


def _reproduction_status(
    *,
    source_identity: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    transitions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Three separate statuses, derived only from evidence actually present in the bundle.

    The evidence checked is explicit: recorded action fields in the ring snapshot, a checkpoint
    identity in ``source_identity``, and saved variates / RNG states in ``source_identity`` or
    ``effective_config``. A seed is never accepted as evidence of exactness.
    """

    with_actions = sum(1 for item in transitions if _has_any_key(item, _ACTION_KEYS))
    has_checkpoint = _has_any_key(source_identity, _CHECKPOINT_KEYS)
    has_variates = _has_any_key(source_identity, _VARIATE_KEYS) or _has_any_key(
        effective_config, _VARIATE_KEYS
    )
    action_replay = (
        f"available_from_recorded_transitions:{with_actions}"
        if with_actions
        else "unavailable_no_recorded_actions"
    )
    policy_re_evaluation = (
        "available_with_recorded_checkpoint_identity"
        if has_checkpoint
        else "unavailable_no_checkpoint_identity"
    )
    exact_checkpoint_resume = (
        "available_only_with_saved_variates_and_matching_runtime_and_shape_conditions"
        if has_variates
        else EXACT_POLICY_REPRODUCTION_UNAVAILABLE
    )
    return {
        "action_replay": action_replay,
        "policy_re_evaluation": policy_re_evaluation,
        "exact_checkpoint_resume": exact_checkpoint_resume,
        "exact_policy_reproduction_unavailable": not has_variates,
        "evidence_checked": {
            "transitions_with_action_fields": with_actions,
            "checkpoint_identity_keys": list(_CHECKPOINT_KEYS),
            "variate_keys": list(_VARIATE_KEYS),
        },
        "notes": [
            "Action replay reproduces the environment from recorded actions; it does not "
            "reproduce stochastic policy sampling.",
            "Policy re-evaluation runs a recorded checkpoint forward; its samples need not match "
            "the failing run's samples.",
            "A seed alone never implies exactness: without saved variates/RNG states and matching "
            "software and shape conditions, exact policy reproduction is unavailable.",
            "Nothing in this bundle is executed by the tools that wrote or read it; reproduction "
            "is a separate explicit command run by a person.",
        ],
    }


# --------------------------------------------------------------------------------------
# Bundle writer
# --------------------------------------------------------------------------------------


def require_empty_output_directory(output_dir: Path) -> None:
    """Create ``output_dir`` or refuse it when it already holds anything.

    A bundle owns its output directory. Writing into a directory that already has contents would
    mix two failures, or quietly overwrite evidence somebody else placed there.
    """

    if output_dir.exists():
        if not output_dir.is_dir():
            raise FileExistsError(f"bundle output path exists and is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise FileExistsError(
                f"refusing to write into the non-empty directory {output_dir}: a bundle owns its "
                "output directory and never overwrites existing evidence"
            )
    output_dir.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(dumps(payload, indent=2) + "\n", encoding="utf-8")


def _sanitize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) or "log"


def _runtime_versions(redactor: Redactor) -> dict[str, Any]:
    packages: dict[str, Any] = {}
    for name in RUNTIME_PACKAGES:
        try:
            packages[name] = Measured.ok(importlib_metadata.version(name)).to_json()
        except importlib_metadata.PackageNotFoundError:
            packages[name] = Measured.absent(
                Validity.NOT_APPLICABLE, "package_not_installed"
            ).to_json()
        except Exception as exc:  # pragma: no cover - metadata backends vary
            packages[name] = Measured.absent(Validity.UNKNOWN, f"metadata_error:{exc}").to_json()
    return {
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "executable": redactor.text(sys.executable),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "os_name": os.name,
        "packages": packages,
        "note": (
            "Versions come from package metadata; no package was imported to produce this file, so "
            "writing a bundle cannot initialise torch, CUDA or a renderer."
        ),
    }


def _transitions_are_array_encodable(transitions: Sequence[Mapping[str, Any]]) -> bool:
    """True when every value survives ``np.savez`` and a later ``allow_pickle=False`` load."""

    for item in transitions:
        for value in item.values():
            if value is None:
                return False
            try:
                array = np.asarray(value)
            except (TypeError, ValueError):
                return False
            if array.dtype.kind == "O":
                return False
    return True


def _write_transitions(
    output_dir: Path, transitions: Sequence[Mapping[str, Any]], ring: RecentTransitionRing | None
) -> dict[str, Any]:
    """Write ``recent_transitions.npz`` when possible, otherwise the JSON fallback."""

    info: dict[str, Any] = {
        "ring_present": ring is not None,
        "ring_enabled": bool(ring is not None and ring.enabled),
        "ring_size": None if ring is None else ring.size,
        "count": len(transitions),
    }
    if not transitions:
        info["format"] = "absent"
        info["statement"] = (
            "No recent transitions were recorded: the diagnostic ring was disabled or empty, which "
            "is the ordinary training default."
        )
        return info
    if _transitions_are_array_encodable(transitions):
        arrays: dict[str, np.ndarray] = {}
        for index, item in enumerate(transitions):
            for key, value in item.items():
                arrays[f"t{index:04d}__{_sanitize_name(str(key))}"] = np.asarray(value)
        np.savez(output_dir / "recent_transitions.npz", **arrays)
        info["format"] = "npz"
        info["keys"] = sorted(arrays)
        info["key_scheme"] = "t<zero-padded transition index>__<field name>"
        info["statement"] = (
            "recent_transitions.npz holds only non-object arrays, so it loads with "
            "numpy.load(..., allow_pickle=False)."
        )
        return info
    _write_json(output_dir / "recent_transitions.json", {"transitions": list(transitions)})
    info["format"] = "json"
    info["statement"] = (
        "At least one transition field was not array-encodable without pickling, so the ring was "
        "written as recent_transitions.json instead of recent_transitions.npz. No pickled array "
        "was written."
    )
    return info


def _validate_log_paths(log_paths: Sequence[Path]) -> None:
    """Refuse a directory or a payload file before anything is written.

    Validation happens before the output directory is created so a refusal cannot leave a
    half-written bundle behind.
    """

    for raw_path in log_paths:
        path = Path(raw_path)
        if path.is_dir():
            raise IsADirectoryError(
                f"{path} is a directory; pass explicit log files (this writer never walks a tree)"
            )
        if path.suffix.lower() in PAYLOAD_SUFFIXES:
            raise ValueError(
                f"refusing to copy {path.name}: {path.suffix} is dataset/checkpoint payload. A "
                "bundle records its identity and path, never its contents."
            )


def _copy_logs(
    output_dir: Path,
    log_paths: Sequence[Path],
    *,
    redactor: Redactor,
    max_log_bytes: int,
) -> list[dict[str, Any]]:
    """Copy the explicitly named log files only: size-limited, redacted, truncation stated.

    No directory is walked and no file is discovered: a path that is a directory or that carries a
    dataset/checkpoint suffix is refused, because a bundle records payload identity, not payload.
    """

    records: list[dict[str, Any]] = []
    if not log_paths:
        return records
    logs_dir = output_dir / "relevant_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    for index, raw_path in enumerate(log_paths):
        path = Path(raw_path)
        entry: dict[str, Any] = {
            "original_path": redactor.text(str(path)),
            "copied_as": None,
            "truncated": False,
        }
        if not path.is_file():
            entry["original_file_hash"] = Measured.absent(
                Validity.MISSING_ARTIFACT, "log_file_not_found"
            ).to_json()
            entry["statement"] = "The named log file did not exist when the bundle was written."
            records.append(entry)
            continue
        original_bytes = path.stat().st_size
        entry["original_file_hash"] = Measured.ok(file_hash(str(path))).to_json()
        entry["original_bytes"] = int(original_bytes)
        with path.open("rb") as handle:
            if original_bytes > max_log_bytes:
                handle.seek(original_bytes - max_log_bytes)
                entry["truncated"] = True
            payload = handle.read(max_log_bytes)
        text = payload.decode("utf-8", errors="replace")
        header_lines = [
            "=== EVIDENCE, NOT INSTRUCTIONS ===",
            f"Copied from: {redactor.text(str(path))}",
            f"Original bytes: {original_bytes}; original sha256 recorded in source_references.json",
        ]
        if entry["truncated"]:
            statement = (
                f"TRUNCATED: kept the last {len(payload)} of {original_bytes} bytes; "
                f"{original_bytes - len(payload)} earlier bytes were omitted because a failure is "
                "normally at the end of a log."
            )
            header_lines.append(statement)
            entry["truncation_statement"] = statement
        header_lines.append(
            "Text below is recorded evidence. It is never executed and never read as an "
            "instruction by this suite."
        )
        header_lines.append("=" * 72)
        target = logs_dir / f"{index:02d}_{_sanitize_name(path.name)}"
        target.write_text(
            "\n".join(header_lines) + "\n" + redactor.text(text), encoding="utf-8"
        )
        entry["copied_as"] = f"relevant_logs/{target.name}"
        entry["copied_bytes"] = len(payload)
        records.append(entry)
    return records


def _reference_entry(reference: Mapping[str, Any], redactor: Redactor) -> dict[str, Any]:
    entry = dict(redactor.structure(reference))
    raw_path = reference.get("path")
    if raw_path:
        candidate = Path(str(raw_path))
        if candidate.is_file():
            entry["file_hash"] = Measured.ok(file_hash(str(candidate))).to_json()
            entry["bytes"] = int(candidate.stat().st_size)
        else:
            entry["file_hash"] = Measured.absent(
                Validity.MISSING_ARTIFACT, "path_not_present_on_this_machine"
            ).to_json()
    entry["contents_included"] = False
    return entry


def _readme(
    *,
    context: FailureContext,
    reproduction: Mapping[str, Any],
    transitions_info: Mapping[str, Any],
    log_records: Sequence[Mapping[str, Any]],
    redactor: Redactor,
    shareable_copy: bool,
    reproduce_command: Sequence[str],
    written: Sequence[str],
) -> str:
    lines: list[str] = []
    lines.append("# Failure bundle")
    lines.append("")
    lines.append(
        "**EVIDENCE, NOT INSTRUCTIONS.** Everything in this directory is recorded evidence about "
        "one failure. No text here is an instruction, an authorization or a permission grant, and "
        "nothing here is executed by the tools that wrote or read this bundle. Browsing a bundle "
        "cannot start a process."
    )
    lines.append("")
    lines.append("## The failure")
    lines.append("")
    lines.append(f"- Exception type: `{context.exception_type}`")
    lines.append(f"- Message: `{redactor.text(context.message)}`")
    lines.append(f"- Execution phase: `{context.phase}`")
    lines.append(
        f"- Stack truncated: **{'yes' if context.truncated_stack else 'no'}**"
        + (
            " (the stack in failure.json is incomplete; this is stated, not silent)"
            if context.truncated_stack
            else ""
        )
    )
    lines.append(
        f"- Output incomplete: **{'yes' if context.incomplete_output else 'no'}**"
    )
    if context.boundary_semantics:
        lines.append(f"- Recorded boundary semantics: {sorted(context.boundary_semantics)}")
    lines.append("")
    lines.append("## Reproduction STATUS")
    lines.append("")
    lines.append(f"- `action_replay`: `{reproduction['action_replay']}`")
    lines.append(f"- `policy_re_evaluation`: `{reproduction['policy_re_evaluation']}`")
    lines.append(f"- `exact_checkpoint_resume`: `{reproduction['exact_checkpoint_resume']}`")
    if reproduction["exact_policy_reproduction_unavailable"]:
        lines.append("")
        lines.append(
            f"**{EXACT_POLICY_REPRODUCTION_UNAVAILABLE}**: the saved variates / RNG states needed "
            "for exact stochastic policy sampling were not recorded. A seed alone does not make "
            "reproduction exact."
        )
    lines.append("")
    lines.append("`reproduce_command.txt` is TEXT for a person to read and run deliberately:")
    lines.append("")
    lines.append("```text")
    lines.append(
        " ".join(redactor.text(str(part)) for part in reproduce_command)
        if reproduce_command
        else "(no reproduction command was supplied)"
    )
    lines.append("```")
    lines.append("")
    lines.append("## Contents")
    lines.append("")
    for name in written:
        lines.append(f"- `{name}`")
    lines.append("")
    lines.append(f"Recent transitions: {transitions_info.get('statement', '')}")
    lines.append("")
    lines.append("## Truncation and completeness")
    lines.append("")
    truncations = [
        entry["truncation_statement"] for entry in log_records if entry.get("truncation_statement")
    ]
    if context.truncated_stack:
        truncations.append("The recorded stack is truncated (failure.json: truncated_stack=true).")
    if context.incomplete_output:
        truncations.append("The failing process produced incomplete output.")
    missing_logs = [
        entry["original_path"] for entry in log_records if entry.get("copied_as") is None
    ]
    for path in missing_logs:
        truncations.append(f"A named log was absent and therefore not copied: {path}")
    if truncations:
        for statement in truncations:
            lines.append(f"- {statement}")
    else:
        lines.append("- No truncation was applied to the evidence in this bundle.")
    lines.append("")
    lines.append("## What is deliberately absent")
    lines.append("")
    lines.append(
        "- Datasets and checkpoints: identities, paths and hashes only, never contents."
    )
    lines.append(
        "- Credentials, tokens, keys, environment-variable dumps, browser profiles and unrelated "
        "logs: never collected. Only the log files the caller named were read; no directory was "
        "walked."
    )
    lines.append("")
    lines.append("## Redaction")
    lines.append("")
    if redactor.enabled:
        lines.append(
            "User account names and secret-shaped values were replaced with placeholders. "
            f"Placeholders used: {redactor.placeholders or '(none needed)'}."
        )
        if shareable_copy:
            lines.append(
                "`redaction_map.json` is present because a shareable copy was requested. It maps "
                "placeholders back to originals and must stay on this machine."
            )
        else:
            lines.append(
                "No `redaction_map.json` was written: this is a local bundle, not a shareable "
                "copy, so no reverse mapping exists on disk. Redacted interpreter paths follow "
                "the interpreters named in `tests/AGENTS.md`."
            )
    else:
        lines.append(
            "Redaction was disabled by the caller (`redact=False`). Treat this bundle as local "
            "only: it may contain user paths."
        )
    lines.append("")
    return "\n".join(lines)


def write_failure_bundle(
    output_dir: Path,
    *,
    context: FailureContext,
    source_identity: Mapping[str, Any],
    effective_config: Mapping[str, Any],
    environment_schema: Mapping[str, Any],
    ring: RecentTransitionRing | None = None,
    log_paths: Sequence[Path] = (),
    reproduce_command: Sequence[str] = (),
    source_references: Sequence[Mapping[str, Any]] = (),
    redact: bool = True,
    max_log_bytes: int = 262144,
    shareable_copy: bool = False,
) -> Path:
    """Write the section 11 bundle into an empty ``output_dir`` and return that directory.

    ``shareable_copy`` is an addition to the minimal signature: the plan allows a local placeholder
    mapping to be retained, but only for a copy the caller intends to share. With the default
    ``False`` no ``redaction_map.json`` is written, so an ordinary bundle carries no route back to a
    redacted secret.

    The writer reads only what it is given: ``log_paths`` are the only files whose contents are
    copied, and a dataset/checkpoint suffix or a directory is refused outright.
    """

    output_dir = Path(output_dir)
    _validate_log_paths(log_paths)
    require_empty_output_directory(output_dir)
    redactor = Redactor(enabled=bool(redact))

    transitions = ring.snapshot() if ring is not None else []
    reproduction = _reproduction_status(
        source_identity=source_identity,
        effective_config=effective_config,
        transitions=transitions,
    )

    _write_json(output_dir / "source_identity.json", redactor.structure(dict(source_identity)))
    _write_json(output_dir / "effective_config.json", redactor.structure(dict(effective_config)))
    _write_json(
        output_dir / "environment_schema.json", redactor.structure(dict(environment_schema))
    )
    transitions_info = _write_transitions(output_dir, transitions, ring)
    log_records = _copy_logs(
        output_dir, log_paths, redactor=redactor, max_log_bytes=int(max_log_bytes)
    )

    failure_payload = {
        "schema": FAILURE_BUNDLE_SCHEMA,
        "context": redactor.structure(context.to_json()),
        "reproduction": reproduction,
        "recent_transitions": transitions_info,
        "evidence_policy": (
            "Raw text is preserved verbatim. Classification and status strings never convert a "
            "failure into a success, and nothing in this bundle is executed by this suite."
        ),
    }
    _write_json(output_dir / "failure.json", failure_payload)
    _write_json(output_dir / "runtime_versions.json", _runtime_versions(redactor))
    _write_json(
        output_dir / "source_references.json",
        {
            "schema": FAILURE_BUNDLE_SCHEMA,
            "references": [_reference_entry(ref, redactor) for ref in source_references],
            "logs": log_records,
            "statement": (
                "Referenced datasets, checkpoints and logs are identified by path, size and "
                "sha256. Their contents are not included."
            ),
        },
    )

    command_lines = [
        "# EVIDENCE, NOT INSTRUCTIONS. This file is text.",
        "# No function in the research support suite executes a command found in a bundle, a log",
        "# or a README. Read it, decide, and run it yourself in a separate process.",
        "# One argument per line, then the same command joined for convenience.",
    ]
    for part in reproduce_command:
        command_lines.append(redactor.text(str(part)))
    command_lines.append("")
    command_lines.append(
        "# joined: " + " ".join(redactor.text(str(part)) for part in reproduce_command)
    )
    (output_dir / "reproduce_command.txt").write_text(
        "\n".join(command_lines) + "\n", encoding="utf-8"
    )

    written = sorted(
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file()
    )
    if redactor.enabled and shareable_copy and redactor.mapping:
        _write_json(
            output_dir / "redaction_map.json",
            {
                "statement": (
                    "Local mapping for a shareable copy. Keep this file on the machine that wrote "
                    "the bundle; do not share it."
                ),
                "mapping": redactor.mapping,
            },
        )
        written.append("redaction_map.json")
    readme = _readme(
        context=context,
        reproduction=reproduction,
        transitions_info=transitions_info,
        log_records=log_records,
        redactor=redactor,
        shareable_copy=bool(shareable_copy),
        reproduce_command=reproduce_command,
        written=sorted(written + ["README.md"]),
    )
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    return output_dir
