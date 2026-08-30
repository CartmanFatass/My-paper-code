#!/usr/bin/env python3
"""Deterministic one-shot executor for one Root-dispatched HMASD Clerk packet.

The packet file is inert until ``execute --packet`` is invoked with
``HMASD_CLERK_DISPATCH``, which binds the exact packet bytes, accepted
authorizer result, and complete accepted producer-evidence set. Harness
configuration owns exact-model/no-fallback resolution before this process
starts; child-authored environment text is never accepted as proof.

The executor invokes only the public HMASD state/worktree command surfaces. It
never schedules, watches, retries, runs an arbitrary command, or edits semantic
content.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import os
import re
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from scripts import hmasd_state, hmasd_worktree
except ImportError:  # Direct ``python scripts/hmasd_clerk.py`` execution.
    import hmasd_state  # type: ignore[no-redef]
    import hmasd_worktree  # type: ignore[no-redef]


DISPATCH_ENV = "HMASD_CLERK_DISPATCH"
RECEIPT_SCHEMA = "hmasd.clerk-receipt/v1"
CLAIM_SCHEMA = "hmasd.clerk-claim/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

OPERATIONS = {
    "STATE_CAS",
    "WORKTREE_PROVISION",
    "WORKTREE_INSPECT",
    "WORKTREE_RELEASE",
    "PATCH_APPLY",
    "CANDIDATE_CREATE",
    "GIT_RECORD",
    "GIT_PREPARE",
    "GIT_INTEGRATE_PUSH",
}

OPERATION_MUTATION_CLASS = {
    "STATE_CAS": "STATE_PATH",
    "WORKTREE_PROVISION": "WORKTREE_REGISTRY",
    "WORKTREE_INSPECT": "READ_ONLY",
    "WORKTREE_RELEASE": "WORKTREE_REGISTRY",
    "PATCH_APPLY": "WORKTREE_CONTENT",
    "CANDIDATE_CREATE": "WORKTREE_CONTENT",
    "GIT_RECORD": "WORKTREE_REGISTRY",
    "GIT_PREPARE": "WORKTREE_REGISTRY",
    "GIT_INTEGRATE_PUSH": "GIT_TARGET",
}
MUTATING_WORKTREE_OPERATIONS = {
    "WORKTREE_PROVISION",
    "WORKTREE_RELEASE",
    "PATCH_APPLY",
    "CANDIDATE_CREATE",
    "GIT_RECORD",
    "GIT_PREPARE",
    "GIT_INTEGRATE_PUSH",
}


class ClerkRefusal(RuntimeError):
    """A fail-closed, known-zero-effect terminal condition."""

    def __init__(self, code: str, message: str, *, effect_state: str = "NOT_ATTEMPTED") -> None:
        super().__init__(message)
        self.code = code
        self.effect_state = effect_state


class ClerkUnknown(RuntimeError):
    """An operation whose effect outcome cannot be proven safely."""

    def __init__(self, code: str, message: str, observations: Sequence[Any] = ()) -> None:
        super().__init__(message)
        self.code = code
        self.observations = list(observations)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return hmasd_state.canonical_bytes(value)


def _json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ClerkRefusal("INVALID_ATTESTATION", f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ClerkRefusal("INVALID_ATTESTATION", f"{label} must be a JSON object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        detail: list[str] = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if extra:
            detail.append("unexpected " + ", ".join(extra))
        raise ClerkRefusal("INVALID_ATTESTATION", f"{label} has {'; '.join(detail)}")


def _require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ClerkRefusal("INVALID_BINDING", f"{label} must be a lowercase SHA-256")
    return value


def _require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or ID_RE.fullmatch(value) is None or value in {".", ".."}:
        raise ClerkRefusal("INVALID_PACKET", f"{label} is not a valid identifier")
    return value


def _reject_symlink_chain(path: Path, label: str, *, require_existing: bool = True) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    parts = absolute.parts[1:] if absolute.anchor else absolute.parts
    for index, part in enumerate(parts):
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if require_existing or index != len(parts) - 1:
                raise ClerkRefusal("NONCANONICAL_PATH", f"{label} does not exist: {current}")
            return
        if os.path.islink(current):
            raise ClerkRefusal("NONCANONICAL_PATH", f"{label} traverses a symlink: {current}")
        del info


def _canonical_existing(raw: Any, label: str, *, directory: bool = False) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise ClerkRefusal("NONCANONICAL_PATH", f"{label} must be a canonical absolute path")
    path = Path(raw)
    if not path.is_absolute() or path != Path(os.path.normpath(raw)):
        raise ClerkRefusal("NONCANONICAL_PATH", f"{label} must be lexical canonical absolute")
    _reject_symlink_chain(path, label)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ClerkRefusal("NONCANONICAL_PATH", f"cannot resolve {label}") from exc
    if resolved != path:
        raise ClerkRefusal("NONCANONICAL_PATH", f"{label} is not canonical")
    if directory and not path.is_dir():
        raise ClerkRefusal("NONCANONICAL_PATH", f"{label} is not a directory")
    if not directory and not path.is_file():
        raise ClerkRefusal("NONCANONICAL_PATH", f"{label} is not a file")
    return path


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _repo_path(repo: Path, raw: Any, label: str, *, must_exist: bool = True) -> Path:
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\\" in raw:
        raise ClerkRefusal("NONCANONICAL_PATH", f"{label} is not a canonical path")
    candidate = Path(raw)
    if candidate.is_absolute():
        path = candidate
    else:
        if any(part in {"", ".", ".."} for part in candidate.parts):
            raise ClerkRefusal("NONCANONICAL_PATH", f"{label} is not repository-relative canonical")
        path = repo / candidate
    path = Path(os.path.normpath(path))
    if not _under(path, repo):
        raise ClerkRefusal("NONCANONICAL_PATH", f"{label} escapes the canonical repository")
    _reject_symlink_chain(path, label, require_existing=must_exist)
    if must_exist and not path.is_file():
        raise ClerkRefusal("NONCANONICAL_PATH", f"{label} is not a file")
    return path


def _relative_ref(repo: Path, path: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError as exc:
        raise ClerkRefusal("NONCANONICAL_PATH", "receipt path escapes repository") from exc


def _load_packet(packet_raw: str) -> tuple[Path, dict[str, Any], bytes, str]:
    packet_path = _canonical_existing(packet_raw, "packet")
    try:
        raw = packet_path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClerkRefusal("INVALID_PACKET", "packet is not readable canonical UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ClerkRefusal("INVALID_PACKET", "packet must be a JSON object")
    if raw != _canonical_bytes(value):
        raise ClerkRefusal("NONCANONICAL_PACKET", "packet bytes are not canonical HMASD JSON")
    packet_sha = value.get("packet_sha256")
    unsigned = dict(value)
    unsigned.pop("packet_sha256", None)
    expected_packet_sha = _sha256(_canonical_bytes(unsigned))
    if packet_sha != expected_packet_sha:
        raise ClerkRefusal("PACKET_HASH_MISMATCH", "packet_sha256 does not bind canonical packet content")
    try:
        hmasd_state.validate_document("clerk_operation", value)
    except hmasd_state.StateError as exc:
        raise ClerkRefusal("INVALID_PACKET_SCHEMA", str(exc)) from exc
    return packet_path, value, raw, _sha256(raw)


def _dispatch_binding(
    packet_path: Path,
    repo: Path,
    packet: Mapping[str, Any],
    file_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    dispatch_raw = os.environ.get(DISPATCH_ENV)
    if dispatch_raw is None:
        raise ClerkRefusal("MISSING_ATTESTATION", "Root dispatch binding is required")

    dispatch = _json_object(dispatch_raw, DISPATCH_ENV)
    _exact_keys(
        dispatch,
        {
            "packet_ref",
            "accepted_authorizer_result",
            "accepted_producer_results",
        },
        "Root dispatch",
    )
    packet_ref = dispatch["packet_ref"]
    accepted = dispatch["accepted_authorizer_result"]
    if not isinstance(packet_ref, dict) or not isinstance(accepted, dict):
        raise ClerkRefusal("INVALID_ATTESTATION", "Root dispatch members must be objects")
    _exact_keys(packet_ref, {"path", "sha256"}, "packet_ref")
    _exact_keys(
        accepted,
        {"logical_identity", "generation", "assignment_id", "result_sha256"},
        "accepted_authorizer_result",
    )
    expected_packet_path = _relative_ref(repo, packet_path)
    if (
        packet_ref["path"] != expected_packet_path
        or _require_sha(packet_ref["sha256"], "packet_ref.sha256") != file_sha256
    ):
        raise ClerkRefusal(
            "DISPATCH_PACKET_MISMATCH",
            "Root dispatch does not bind the exact packet path and bytes",
        )
    authorizer = packet["authorizer"]
    for key in ("logical_identity", "generation", "assignment_id"):
        if accepted[key] != authorizer[key]:
            raise ClerkRefusal(
                "DISPATCH_AUTHORIZER_MISMATCH",
                f"accepted authorizer {key} does not match packet",
            )
    if (
        not isinstance(accepted["generation"], int)
        or isinstance(accepted["generation"], bool)
        or accepted["generation"] < 1
    ):
        raise ClerkRefusal(
            "INVALID_ATTESTATION", "accepted authorizer generation is invalid"
        )
    _require_sha(
        accepted["result_sha256"],
        "accepted_authorizer_result.result_sha256",
    )
    producer_results = dispatch["accepted_producer_results"]
    if not isinstance(producer_results, list):
        raise ClerkRefusal(
            "INVALID_ATTESTATION",
            "accepted_producer_results must be a closed array",
        )
    executor = packet["executor"]
    if (
        executor.get("role") != "hmasd-clerk"
        or executor.get("logical_identity")
        != f"Clerk-{packet['clerk_assignment_id']}"
    ):
        raise ClerkRefusal(
            "EXECUTOR_ASSIGNMENT_MISMATCH",
            "packet executor identity does not match the Clerk assignment",
        )
    return dispatch, dict(executor)


def _packet_repo(packet: Mapping[str, Any], packet_path: Path) -> Path:
    target = packet.get("target")
    if not isinstance(target, Mapping):
        raise ClerkRefusal("INVALID_PACKET", "packet target is absent")
    repo_raw = target.get("canonical_repo_path")
    if repo_raw is not None:
        repo = _canonical_existing(repo_raw, "target.canonical_repo_path", directory=True)
    else:
        repo = next(
            (
                parent
                for parent in (packet_path.parent, *packet_path.parents)
                if (parent / ".git").exists()
            ),
            None,
        )
        if repo is None:
            repo = next(
                (
                    parent
                    for parent in (packet_path.parent, *packet_path.parents)
                    if (parent / ".omp").is_dir()
                ),
                None,
            )
        if repo is None:
            raise ClerkRefusal("INVALID_REPOSITORY", "STATE_CAS packet is not inside an HMASD repository")
        repo = _canonical_existing(str(repo), "packet repository", directory=True)
    if not ((repo / ".git").exists() or (repo / ".omp").is_dir()):
        raise ClerkRefusal("INVALID_REPOSITORY", "canonical repository is not an HMASD repository")
    return repo


def _verify_content_ref(repo: Path, ref: Any, label: str) -> tuple[Path, dict[str, str]]:
    if not isinstance(ref, Mapping) or set(ref) != {"path", "sha256"}:
        raise ClerkRefusal("INVALID_PRECONDITION", f"{label} must be an exact content reference")
    expected = _require_sha(ref["sha256"], f"{label}.sha256")
    path = _repo_path(repo, ref["path"], label)
    try:
        actual = hmasd_state.sha256_file(path)
    except OSError as exc:
        raise ClerkRefusal("MISSING_PRECONDITION", f"cannot read {label}") from exc
    if actual != expected:
        raise ClerkRefusal("CONTENT_DIGEST_CHANGED", f"{label} bytes do not match the frozen digest")
    return path, {"path": _relative_ref(repo, path), "sha256": actual}


def _verify_refs_in(value: Any, repo: Path, label: str, observed: list[dict[str, str]]) -> None:
    if isinstance(value, Mapping):
        if set(value) == {"path", "sha256"}:
            _, normalized = _verify_content_ref(repo, value, label)
            observed.append(normalized)
            return
        for key, child in value.items():
            _verify_refs_in(child, repo, f"{label}.{key}", observed)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _verify_refs_in(child, repo, f"{label}[{index}]", observed)


def _verify_authority_dependencies(packet: Mapping[str, Any], repo: Path) -> None:
    for index, dependency in enumerate(packet.get("requires", [])):
        if not isinstance(dependency, Mapping) or "authority_ref" not in dependency:
            continue
        path, _ = _verify_content_ref(
            repo,
            dependency["authority_ref"],
            f"requires[{index}].authority_ref",
        )
        checkpoint = dependency["revision_or_checkpoint"]
        if isinstance(checkpoint, int) and not isinstance(checkpoint, bool):
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ClerkRefusal(
                    "INVALID_PRECONDITION",
                    f"requires[{index}] authority revision cannot be observed",
                ) from exc
            if not isinstance(document, Mapping) or document.get("revision") != checkpoint:
                raise ClerkRefusal(
                    "STALE_PRECONDITION",
                    f"requires[{index}] authority revision changed",
                )

def _normalized_evidence_refs(value: Any, label: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ClerkRefusal("PRODUCER_EVIDENCE_MISMATCH", f"{label} must be an array")
    refs: list[dict[str, str]] = []
    for index, ref in enumerate(value):
        if not isinstance(ref, Mapping) or set(ref) != {"path", "sha256"}:
            raise ClerkRefusal(
                "PRODUCER_EVIDENCE_MISMATCH",
                f"{label}[{index}] is not an exact content reference",
            )
        path = ref["path"]
        if not isinstance(path, str) or not path:
            raise ClerkRefusal(
                "PRODUCER_EVIDENCE_MISMATCH",
                f"{label}[{index}].path is invalid",
            )
        refs.append(
            {
                "path": path,
                "sha256": _require_sha(
                    ref["sha256"], f"{label}[{index}].sha256"
                ),
            }
        )
    paths = [ref["path"] for ref in refs]
    if len(paths) != len(set(paths)):
        raise ClerkRefusal(
            "PRODUCER_EVIDENCE_MISMATCH",
            f"{label} contains duplicate paths",
        )
    return sorted(refs, key=lambda ref: ref["path"])


def _normalized_producer_evidence(
    value: Any,
    label: str,
    *,
    dependency: bool,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ClerkRefusal("PRODUCER_EVIDENCE_MISMATCH", f"{label} must be an object")
    expected_keys = (
        {
            "producer",
            "result_sha256",
            "required_status",
            "required_payload_kind",
            "required_refs",
        }
        if dependency
        else {"producer", "result_sha256", "status", "payload_kind", "refs"}
    )
    if set(value) != expected_keys:
        raise ClerkRefusal(
            "PRODUCER_EVIDENCE_MISMATCH",
            f"{label} has an invalid closed shape",
        )
    producer = value["producer"]
    if not isinstance(producer, Mapping) or set(producer) != {
        "logical_identity",
        "generation",
        "assignment_id",
    }:
        raise ClerkRefusal(
            "PRODUCER_EVIDENCE_MISMATCH",
            f"{label}.producer is not an exact NodeKey",
        )
    generation = producer["generation"]
    if (
        not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 1
    ):
        raise ClerkRefusal(
            "PRODUCER_EVIDENCE_MISMATCH",
            f"{label}.producer generation is invalid",
        )
    status_key = "required_status" if dependency else "status"
    payload_key = "required_payload_kind" if dependency else "payload_kind"
    refs_key = "required_refs" if dependency else "refs"
    return {
        "producer": dict(producer),
        "result_sha256": _require_sha(
            value["result_sha256"], f"{label}.result_sha256"
        ),
        "status": value[status_key],
        "payload_kind": value[payload_key],
        "refs": _normalized_evidence_refs(value[refs_key], f"{label}.{refs_key}"),
    }


def _verify_producer_dependencies(
    packet: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> None:
    dependencies = [
        _normalized_producer_evidence(
            dependency,
            f"requires[{index}]",
            dependency=True,
        )
        for index, dependency in enumerate(packet.get("requires", []))
        if isinstance(dependency, Mapping) and "producer" in dependency
    ]
    accepted = [
        _normalized_producer_evidence(
            evidence,
            f"accepted_producer_results[{index}]",
            dependency=False,
        )
        for index, evidence in enumerate(dispatch["accepted_producer_results"])
    ]
    sort_key = lambda item: (
        item["producer"]["logical_identity"],
        item["producer"]["generation"],
        item["producer"]["assignment_id"],
        item["result_sha256"],
    )
    dependencies.sort(key=sort_key)
    accepted.sort(key=sort_key)
    if len(accepted) != len({json.dumps(item, sort_keys=True) for item in accepted}):
        raise ClerkRefusal(
            "PRODUCER_EVIDENCE_MISMATCH",
            "Root dispatch contains duplicate accepted producer evidence",
        )
    if accepted != dependencies:
        raise ClerkRefusal(
            "PRODUCER_EVIDENCE_MISMATCH",
            "Root dispatch does not exactly prove every producer dependency edge",
        )



def _verify_preconditions(
    packet: Mapping[str, Any],
    repo: Path,
) -> list[dict[str, str]]:
    observed: list[dict[str, str]] = []
    _verify_refs_in(packet.get("requires", []), repo, "requires", observed)
    _verify_refs_in(packet.get("acceptance_refs", []), repo, "acceptance_refs", observed)
    _verify_refs_in(packet.get("target", {}), repo, "target", observed)
    _verify_authority_dependencies(packet, repo)
    return observed


def _authority_actor_or_writer(packet: Mapping[str, Any]) -> str | None:
    authority = packet["authority"]
    return authority.get("git_actor") or authority.get("document_writer")


def _expected_operation_resources(
    operation: str,
    target: Mapping[str, Any],
    repo: Path,
) -> list[dict[str, str]]:
    runtime_worktrees = {
        "kind": "RUNTIME_WORKTREES_STATE",
        "key": str(repo / ".omp" / "runtime" / "worktrees.json"),
    }
    if operation == "STATE_CAS":
        state_path = _repo_path(
            repo,
            target["canonical_target_path"],
            "target.canonical_target_path",
        )
        resources = [{"kind": "STATE_PATH", "key": str(state_path)}]
    elif operation == "WORKTREE_INSPECT":
        resources = []
    elif operation == "WORKTREE_PROVISION":
        resources = [
            runtime_worktrees,
            {"kind": "CONTAINER", "key": target["canonical_container_path"]},
        ]
    else:
        resources = [
            runtime_worktrees,
            {"kind": "WORKTREE", "key": target["canonical_worktree_path"]},
        ]
        if operation == "GIT_INTEGRATE_PUSH":
            repository = _repository_facts(repo)
            resources.extend(
                [
                    {
                        "kind": "GIT_TARGET",
                        "key": repository["target_lock_key"],
                    },
                    {
                        "kind": "REMOTE_TARGET",
                        "key": (
                            f"{repository['common_path']}:remote:"
                            f"{target['remote_name']}:"
                            f"{target['target_remote_ref']}"
                        ),
                    },
                ]
            )
    resources.sort(key=lambda resource: (resource["kind"], resource["key"]))
    return resources


def _validate_operation_binding(packet: Mapping[str, Any], repo: Path) -> None:
    operation = packet.get("operation")
    if operation not in OPERATIONS:
        raise ClerkRefusal(
            "UNSUPPORTED_OPERATION",
            "packet does not discriminate one supported operation enum",
        )
    mutation = packet.get("mutation")
    effect = packet.get("effect")
    if not isinstance(mutation, Mapping) or not isinstance(effect, Mapping):
        raise ClerkRefusal("INVALID_PACKET", "mutation/effect bindings are absent")
    if mutation.get("class") != OPERATION_MUTATION_CLASS[operation]:
        raise ClerkRefusal(
            "MUTATION_DOMAIN_MISMATCH",
            "operation and mutation class span unrelated domains",
        )
    resources = mutation.get("resources")
    if not isinstance(resources, list):
        raise ClerkRefusal(
            "MUTATION_DOMAIN_MISMATCH",
            "mutation resources must be a closed canonical array",
        )
    normalized_resources: list[dict[str, str]] = []
    for index, resource in enumerate(resources):
        if (
            not isinstance(resource, Mapping)
            or set(resource) != {"kind", "key"}
            or not isinstance(resource["kind"], str)
            or not isinstance(resource["key"], str)
            or not resource["key"]
        ):
            raise ClerkRefusal(
                "MUTATION_DOMAIN_MISMATCH",
                f"mutation.resources[{index}] is invalid",
            )
        normalized_resources.append(
            {"kind": resource["kind"], "key": resource["key"]}
        )
    canonical_resources = sorted(
        normalized_resources, key=lambda resource: (resource["kind"], resource["key"])
    )
    identities = [
        (resource["kind"], resource["key"]) for resource in normalized_resources
    ]
    if len(identities) != len(set(identities)):
        raise ClerkRefusal(
            "MUTATION_DOMAIN_MISMATCH",
            "mutation resources contain duplicates",
        )
    if normalized_resources != canonical_resources:
        raise ClerkRefusal(
            "MUTATION_DOMAIN_MISMATCH",
            "mutation resources are not in canonical order",
        )
    if (
        effect.get("attempt") != 1
        or effect.get("unknown_outcome") != "OBSERVE_ONLY_NO_AUTOMATIC_RETRY"
    ):
        raise ClerkRefusal(
            "INVALID_ATTEMPT",
            "packet must authorize one attempt and observe-only unknown handling",
        )
    _require_sha(effect.get("attempt_token"), "effect.attempt_token")
    expected_effects: list[str] = (
        [] if operation == "WORKTREE_INSPECT" else [operation]
    )
    if effect.get("authorized_effects") != expected_effects:
        raise ClerkRefusal(
            "EFFECT_BUDGET_MISMATCH",
            "authorized_effects must name only this packet operation",
        )
    if normalized_resources != _expected_operation_resources(
        operation,
        packet["target"],
        repo,
    ):
        raise ClerkRefusal(
            "MUTATION_DOMAIN_MISMATCH",
            "mutation resources do not expose the complete exact operation footprint",
        )


def _lease_args(packet: Mapping[str, Any], repo: Path) -> list[str]:
    target = packet["target"]
    lease = target.get("mutation_lease")
    if not isinstance(lease, Mapping):
        raise ClerkRefusal("PHYSICAL_LEASE_UNAVAILABLE", "mutating worktree operation lacks an exact physical lease")
    expected_keys = {
        "manager_assignment_id",
        "clerk_assignment_id",
        "handoff_ref",
        "lease_token",
    }
    if set(lease) != expected_keys:
        raise ClerkRefusal("PHYSICAL_LEASE_INVALID", "mutation_lease has an invalid closed shape")
    if lease["clerk_assignment_id"] != packet["clerk_assignment_id"]:
        raise ClerkRefusal("PHYSICAL_LEASE_MISMATCH", "physical lease belongs to another Clerk assignment")
    handoff_path, handoff_ref = _verify_content_ref(repo, lease["handoff_ref"], "target.mutation_lease.handoff_ref")
    manager_assignment = _require_id(lease["manager_assignment_id"], "mutation_lease.manager_assignment_id")
    lease_token = _require_sha(lease["lease_token"], "mutation_lease.lease_token")
    return [
        "--manager-assignment-id",
        manager_assignment,
        "--clerk-assignment-id",
        packet["clerk_assignment_id"],
        "--handoff-ref",
        _relative_ref(repo, handoff_path),
        "--handoff-sha256",
        handoff_ref["sha256"],
        "--lease-token",
        lease_token,
    ]


def _validated_helper_observation(
    code: int,
    value: Mapping[str, Any],
) -> dict[str, Any]:
    observation: dict[str, Any] = {"helper_code": code}
    operation = value.get("operation")
    if isinstance(operation, str) and operation in {
        "provision",
        "inspect",
        "release",
        "retain",
        "apply-patch",
        "create-candidate",
        "record-candidate",
        "prepare-integration",
        "integrate-push",
    }:
        observation["operation"] = operation
    for key in (
        "candidate_sha",
        "integrated_sha",
        "expected_target_predecessor_sha",
        "expected_remote_predecessor_sha",
        "remote_prefetch_sha",
        "remote_post_observation_sha",
        "local_sha",
    ):
        candidate = value.get(key)
        if candidate is None:
            if key in value:
                observation[key] = None
        elif isinstance(candidate, str) and re.fullmatch(
            r"(?:[0-9a-f]{40}|[0-9a-f]{64})", candidate
        ):
            observation[key] = candidate
    policy = value.get("integration_policy")
    if policy in {"EXACT_HANDOFF", "ORTHOGONAL_DIRECTION"}:
        observation["integration_policy"] = policy
    phase = value.get("integration_phase")
    if (
        isinstance(phase, str)
        and 1 <= len(phase) <= 64
        and re.fullmatch(r"[A-Z][A-Z0-9_]*", phase)
    ):
        observation["integration_phase"] = phase
    for key in (
        "reconciliation_observations",
        "push_attempts",
        "local_apply_attempts",
        "registry_revision",
    ):
        count = value.get(key)
        if (
            isinstance(count, int)
            and not isinstance(count, bool)
            and 0 <= count <= (1 if key != "registry_revision" else 2**63 - 1)
        ):
            observation[key] = count
    for key in ("status", "lifecycle", "worktree_ref", "candidate_ref"):
        fact = value.get(key)
        if isinstance(fact, str) and 1 <= len(fact) <= 512 and "\x00" not in fact:
            observation[key] = fact
    return observation


def _invoke_worktree(argv: Sequence[str]) -> dict[str, Any]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        try:
            code = hmasd_worktree.main(argv)
        except SystemExit as exc:
            raise ClerkRefusal("UNSUPPORTED_PRIMITIVE", "worktree helper rejected the frozen operation interface") from exc
    text = output.getvalue().strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ClerkUnknown("PRIMITIVE_OUTPUT_UNKNOWN", "worktree helper returned an unreadable result") from exc
    if not isinstance(value, dict):
        raise ClerkUnknown("PRIMITIVE_OUTPUT_UNKNOWN", "worktree helper returned a non-object result")
    if code == 0 and value.get("ok") is True:
        return value
    safe_observation = _validated_helper_observation(code, value)
    if code == getattr(hmasd_worktree.UnknownApply, "code", 1):
        raise ClerkUnknown(
            "PRIMITIVE_OUTCOME_UNKNOWN",
            "worktree helper reported an unknown outcome",
            [safe_observation],
        )
    raise ClerkRefusal(
        "PRIMITIVE_REFUSED",
        "worktree helper refused the exact operation",
        effect_state="NOT_LANDED",
    )


def _repository_facts(
    repo: Path,
    *,
    remote_name: str | None = None,
    remote_ref: str | None = None,
) -> dict[str, Any]:
    argv = [
        "inspect-repository",
        "--repo",
        str(repo),
        "--target",
        hmasd_worktree.TARGET_BRANCH,
    ]
    if remote_name is not None or remote_ref is not None:
        if remote_name is None or remote_ref is None:
            raise ClerkRefusal(
                "INVALID_REMOTE_BINDING",
                "remote name and ref must be supplied together",
            )
        argv.extend(["--remote-name", remote_name, "--remote-ref", remote_ref])
    result = _invoke_worktree(argv)
    common_path = result.get("common_path")
    target_lock_key = result.get("target_lock_key")
    target_sha = result.get("target_sha")
    if (
        not isinstance(common_path, str)
        or not Path(common_path).is_absolute()
        or "\x00" in common_path
        or not isinstance(target_lock_key, str)
        or target_lock_key != f"{common_path}:refs/heads/{hmasd_worktree.TARGET_BRANCH}"
        or (
            target_sha is not None
            and (
                not isinstance(target_sha, str)
                or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", target_sha)
                is None
            )
        )
    ):
        raise ClerkRefusal(
            "PRIMITIVE_RESULT_MISMATCH",
            "repository inspection returned invalid target facts",
        )
    return result


def _validated_integration_policy(
    value: Mapping[str, Any],
    *,
    after_effect: bool = False,
) -> str:
    policy = value.get("integration_policy")
    if policy in {"EXACT_HANDOFF", "ORTHOGONAL_DIRECTION"}:
        return str(policy)
    if after_effect:
        raise ClerkUnknown(
            "PRIMITIVE_RESULT_MISMATCH",
            "public primitive returned an invalid integration policy",
        )
    raise ClerkRefusal(
        "WORKTREE_AUTHORITY_DRIFT",
        "registered worktree has no current integration policy",
    )


def _target_ref_path(repo: Path, target: Mapping[str, Any], key: str) -> Path:
    path, _ = _verify_content_ref(repo, target[key], f"target.{key}")
    return path


def _resolve_operation_receipt(
    repo: Path,
    operation_id: str,
    expected_sha256: str,
) -> tuple[Path, dict[str, Any]]:
    claim_path, _ = _claim_paths(repo, _require_id(operation_id, "receipt binding operation_id"))
    try:
        claim = _load_claim(claim_path)
        if claim is None or claim["state"] != "SUCCEEDED" or not isinstance(claim["receipt_ref"], Mapping):
            raise ClerkRefusal("MISSING_PRIOR_RECEIPT", "prior operation has no successful terminal receipt")
        receipt, normalized = _read_receipt(repo, claim["receipt_ref"])
    except ClerkUnknown as exc:
        raise ClerkRefusal(
            "PRIOR_RECEIPT_UNKNOWN",
            "prior operation receipt cannot be interpreted safely",
        ) from exc
    if normalized["sha256"] != _require_sha(expected_sha256, "prior receipt SHA-256"):
        raise ClerkRefusal("PRIOR_RECEIPT_MISMATCH", "prior operation receipt digest does not match packet")
    return _repo_path(repo, normalized["path"], "prior receipt"), receipt


def _prior_output(
    repo: Path,
    binding: Mapping[str, Any],
) -> tuple[Any, dict[str, Any]]:
    expected_keys = {"operation_id", "receipt_sha256", "output_field"}
    if set(binding) != expected_keys:
        raise ClerkRefusal("INVALID_PRIOR_BINDING", "prior receipt binding has an invalid closed shape")
    _, receipt = _resolve_operation_receipt(
        repo,
        binding["operation_id"],
        binding["receipt_sha256"],
    )
    output_field = binding["output_field"]
    if output_field == "receipt_ref":
        refs = receipt.get("receipt_refs")
        if not isinstance(refs, list) or len(refs) != 1 or not isinstance(refs[0], Mapping):
            raise ClerkRefusal("MISSING_PRIOR_OUTPUT", "prior receipt has no unique receipt_ref output")
        path, _ = _verify_content_ref(repo, refs[0], "prior receipt_ref output")
        return path, receipt
    matches: list[Any] = []
    for observation in receipt.get("observation_refs", []):
        if isinstance(observation, Mapping) and output_field in observation:
            matches.append(observation[output_field])
    if len(matches) != 1:
        raise ClerkRefusal(
            "MISSING_PRIOR_OUTPUT",
            f"prior receipt has no unique {output_field} output",
        )
    return matches[0], receipt


def _candidate_sha(repo: Path, binding: Mapping[str, Any]) -> str:
    direct = binding.get("candidate_sha")
    if isinstance(direct, str):
        return direct
    receipt_binding = binding.get("receipt_binding")
    if not isinstance(receipt_binding, Mapping):
        raise ClerkRefusal("INVALID_CANDIDATE_BINDING", "candidate binding is absent")
    if receipt_binding.get("output_field") != "candidate_sha":
        raise ClerkRefusal("INVALID_CANDIDATE_BINDING", "candidate output field must be exact")
    candidate, _ = _prior_output(repo, receipt_binding)
    if isinstance(candidate, str):
        return candidate
    raise ClerkRefusal("MISSING_CANDIDATE_OUTPUT", "prior receipt candidate_sha is invalid")


def _canonical_packet_refs(value: Any, label: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ClerkRefusal("INVALID_PACKET", f"{label} must be an array")
    refs: list[dict[str, str]] = []
    for index, ref in enumerate(value):
        if not isinstance(ref, Mapping) or set(ref) != {"path", "sha256"}:
            raise ClerkRefusal(
                "INVALID_PACKET", f"{label}[{index}] is not a content reference"
            )
        refs.append({"path": str(ref["path"]), "sha256": str(ref["sha256"])})
    paths = [ref["path"] for ref in refs]
    if len(paths) != len(set(paths)):
        raise ClerkRefusal("INVALID_PACKET", f"{label} contains duplicate paths")
    return sorted(refs, key=lambda ref: ref["path"])


def _validate_registered_authority(
    packet: Mapping[str, Any],
    entry: Mapping[str, Any],
) -> None:
    if packet["operation"] not in {
        "PATCH_APPLY",
        "CANDIDATE_CREATE",
        "GIT_RECORD",
        "GIT_PREPARE",
        "GIT_INTEGRATE_PUSH",
    }:
        return
    authority = packet["authority"]
    direction = entry.get("direction_id")
    kind = entry.get("kind")
    if (
        authority.get("direction_id") != direction
        or authority.get("worktree_kind") != kind
    ):
        raise ClerkRefusal(
            "AUTHORITY_DRIFT",
            "packet direction and kind must exactly match the registered worktree",
        )
    role = {"research": "em", "engineering": "cm"}.get(str(kind))
    manager_role = {"research": "hmasd-em", "engineering": "hmasd-cm"}.get(
        str(kind)
    )
    manager_identity = {"research": "EM", "engineering": "CM"}.get(str(kind))
    expected_actor = f"{role}:{direction}" if role is not None else None
    actor = authority.get("git_actor")
    authorizer = packet["authorizer"]
    scope = authority.get("assignment_authority")
    if actor == "root":
        if (
            scope not in {"SHARED", "RECOVERY"}
            or authorizer.get("role") != "root"
            or authorizer.get("logical_identity") != "Root"
        ):
            raise ClerkRefusal(
                "ACTOR_MISMATCH",
                "Root actor requires explicit shared or recovery assignment authority",
            )
        return
    if (
        scope != "DIRECTION"
        or actor != expected_actor
        or authorizer.get("role") != manager_role
        or authorizer.get("logical_identity")
        != f"{manager_identity}-{direction}"
    ):
        raise ClerkRefusal(
            "ACTOR_MISMATCH",
            "packet actor/authorizer does not own the registered direction and kind",
        )


def _common_worktree_binding(
    packet: Mapping[str, Any],
    repo: Path,
) -> tuple[
    list[str],
    list[str],
    dict[str, Any] | None,
    dict[str, Any] | None,
]:
    target = packet["target"]
    operation = packet["operation"]
    expected = [
        "--expected-registry-revision",
        str(target["expected_registry_revision"]),
        "--expected-lifecycle",
        target["expected_lifecycle"],
        "--expected-worktree-path",
        target["canonical_worktree_path"],
        "--expected-container-path",
        target["canonical_container_path"],
    ]
    expected_receipt = target["expected_receipt_sha256"]
    if expected_receipt is not None:
        expected.extend(["--expected-receipt-sha256", expected_receipt])
    prior = target.get("prior_operation_receipt")
    if prior is not None:
        if not isinstance(prior, Mapping):
            raise ClerkRefusal(
                "INVALID_PRIOR_BINDING",
                "prior operation receipt binding is invalid",
            )
        _prior_output(repo, prior)
    lease = [] if operation == "WORKTREE_INSPECT" else _lease_args(packet, repo)
    entry: dict[str, Any] | None = None
    inspection: dict[str, Any] | None = None
    if operation != "WORKTREE_PROVISION":
        try:
            inspection = _invoke_worktree(
                [
                    "inspect",
                    "--repo",
                    str(repo),
                    "--worktree-ref",
                    target["worktree_ref"],
                    *expected,
                ]
            )
        except ClerkRefusal as exc:
            raise ClerkRefusal(
                "WORKTREE_PRECONDITION_REFUSED",
                "public worktree inspection rejected frozen preconditions",
            ) from exc
        observed_entry = inspection.get("worktree")
        if not isinstance(observed_entry, Mapping):
            raise ClerkRefusal(
                "PRIMITIVE_RESULT_MISMATCH",
                "public worktree inspection omitted the registered entry",
            )
        entry = dict(observed_entry)
        _validate_registered_authority(packet, entry)
        frozen = {
            "canonical_absolute_path": target["canonical_worktree_path"],
            "integration_policy": target["policy"],
            "required_handoff_sha": target["required_handoff_sha"],
            "required_dependency_refs": _canonical_packet_refs(
                target["required_dependency_refs"],
                "target.required_dependency_refs",
            ),
        }
        optional_entry_fields = {
            "direction_id": "direction_id",
            "worktree_kind": "kind",
            "base_sha": "base_sha",
        }
        for target_key, entry_key in optional_entry_fields.items():
            if target_key in target:
                frozen[entry_key] = target[target_key]
        observed = {
            **entry,
            "integration_policy": _validated_integration_policy(entry),
            "required_handoff_sha": entry.get("required_handoff_sha"),
            "required_dependency_refs": _canonical_packet_refs(
                entry.get("required_dependency_refs", []),
                "registry.required_dependency_refs",
            ),
        }
        for key, value in frozen.items():
            if observed.get(key) != value:
                raise ClerkRefusal(
                    "WORKTREE_AUTHORITY_DRIFT",
                    f"registered worktree {key} differs from packet",
                )
    return expected, lease, entry, inspection


def _validate_git_packet_target(
    repo: Path,
    target: Mapping[str, Any],
    entry: Mapping[str, Any],
    candidate: str,
) -> None:
    if target["base_sha"] != entry["base_sha"]:
        raise ClerkRefusal("BASE_MISMATCH", "packet base differs from registered worktree")
    if target.get("target_ref", target.get("target_local_ref")) != hmasd_worktree.TARGET_BRANCH:
        raise ClerkRefusal("TARGET_MISMATCH", "packet target must be exactly omp/workflow")
    if candidate != target.get("candidate_sha", candidate):
        raise ClerkRefusal("CANDIDATE_MISMATCH", "candidate binding differs from packet")
    argv = [
        "validate-candidate",
        "--repo",
        str(repo),
        "--base",
        target["base_sha"],
        "--candidate",
        candidate,
        *sum((["--allowed-path", path] for path in target["allowed_paths"]), []),
        *sum(
            (["--expected-changed-path", path] for path in target["changed_paths"]),
            [],
        ),
        "--expected-diff-sha256",
        target["diff_sha256"],
    ]
    try:
        _invoke_worktree(argv)
    except ClerkRefusal as exc:
        raise ClerkRefusal(
            "CANDIDATE_INVALID",
            "public candidate validation rejected frozen tree facts",
        ) from exc


def _worktree_command(packet: Mapping[str, Any], repo: Path) -> list[str]:
    target = packet["target"]
    operation = packet["operation"]
    common = ["--repo", str(repo)]
    expected, lease, entry, inspection = _common_worktree_binding(packet, repo)
    if operation == "WORKTREE_PROVISION":
        authority = packet["authority"]
        direction = target["direction_id"]
        kind = target["worktree_kind"]
        role = {"research": "em", "engineering": "cm"}[kind]
        authorizer_role = {"research": "hmasd-em", "engineering": "hmasd-cm"}[kind]
        authorizer_identity = {"research": "EM", "engineering": "CM"}[kind]
        actor = authority.get("git_actor")
        authorizer = packet["authorizer"]
        if (
            authority.get("direction_id") != direction
            or authority.get("worktree_kind") != kind
        ):
            raise ClerkRefusal(
                "AUTHORITY_DRIFT",
                "provision authority differs from its frozen target",
            )
        if actor == "root":
            valid_actor = (
                authority.get("assignment_authority") in {"SHARED", "RECOVERY"}
                and authorizer.get("role") == "root"
                and authorizer.get("logical_identity") == "Root"
            )
        else:
            valid_actor = (
                authority.get("assignment_authority") == "DIRECTION"
                and actor == f"{role}:{direction}"
                and authorizer.get("role") == authorizer_role
                and authorizer.get("logical_identity")
                == f"{authorizer_identity}-{direction}"
            )
        if not valid_actor:
            raise ClerkRefusal(
                "ACTOR_MISMATCH",
                "provision actor does not own the exact assignment authority",
            )
        manifest = target["parallel_set_manifest_ref"]
        argv = [
            "provision",
            *common,
            "--container",
            target["canonical_container_path"],
            "--direction",
            target["direction_id"],
            "--kind",
            target["worktree_kind"],
            "--assignment",
            target["mutation_lease"]["manager_assignment_id"],
            "--base",
            target["base_sha"],
            "--integration-policy",
            target["integration_policy"],
        ]
        if target["required_handoff_sha"] is not None:
            argv.extend(
                ["--required-handoff-sha", target["required_handoff_sha"]]
            )
        for ref in target["required_dependency_refs"]:
            argv.extend(
                [
                    "--required-dependency-ref",
                    f"{ref['path']}={ref['sha256']}",
                ]
            )
        if manifest is not None:
            path, _ = _verify_content_ref(repo, manifest, "target.parallel_set_manifest_ref")
            argv.extend(["--parallel-set-manifest", _relative_ref(repo, path)])
        return [*argv, *lease, *expected]
    if operation == "WORKTREE_INSPECT":
        return ["inspect", *common, "--worktree-ref", target["worktree_ref"], *expected]
    if operation == "WORKTREE_RELEASE":
        authority = packet["authority"]
        if (
            _authority_actor_or_writer(packet) != "root"
            or authority.get("assignment_authority") not in {"SHARED", "RECOVERY"}
            or packet["authorizer"].get("logical_identity") != "Root"
        ):
            raise ClerkRefusal(
                "ACTOR_MISMATCH",
                "release requires explicit Root shared or recovery authority",
            )
        if target["ignored_artifacts"] == "refuse":
            raise ClerkRefusal(
                "RELEASE_DISPOSITION_REFUSED",
                "release disposition refuse authorizes zero effect",
            )
        return [
            "release",
            *common,
            "--worktree-ref",
            target["worktree_ref"],
            "--actor",
            "root",
            "--ignored-artifacts",
            target["ignored_artifacts"],
            *lease,
            *expected,
        ]
    assert entry is not None
    if operation == "PATCH_APPLY":
        patch_path, patch_ref = _verify_content_ref(repo, target["patch_ref"], "target.patch_ref")
        return [
            "apply-patch",
            *common,
            "--worktree-ref",
            target["worktree_ref"],
            "--base",
            target["base_sha"],
            "--baseline-tree",
            target["baseline_tree_sha"],
            "--patch",
            str(patch_path),
            "--patch-sha256",
            patch_ref["sha256"],
            *sum((["--allowed-path", path] for path in target["allowed_paths"]), []),
            *sum((["--expected-changed-path", path] for path in target["expected_changed_paths"]), []),
            "--expected-diff-sha256",
            target["expected_post_apply_diff_sha256"],
            "--expected-result-tree",
            target["expected_result_tree_sha"],
            *lease,
            *expected,
        ]
    if operation == "CANDIDATE_CREATE":
        metadata_path, metadata_ref = _verify_content_ref(
            repo, target["commit_metadata_ref"], "target.commit_metadata_ref"
        )
        prepared_value, _ = _prior_output(
            repo, target["prepared_tree_receipt_binding"]
        )
        prepared_path, prepared_ref = _verify_content_ref(
            repo, prepared_value, "target.prepared_tree_receipt_binding"
        )
        return [
            "create-candidate",
            *common,
            "--worktree-ref",
            target["worktree_ref"],
            "--base",
            target["declared_base_sha"],
            "--prepared-tree-receipt",
            str(prepared_path),
            "--prepared-tree-receipt-sha256",
            prepared_ref["sha256"],
            *sum((["--allowed-path", path] for path in target["allowed_paths"]), []),
            *sum((["--expected-changed-path", path] for path in target["expected_changed_paths"]), []),
            "--expected-diff-sha256",
            target["expected_diff_sha256"],
            "--expected-tree",
            target["expected_tree_sha"],
            "--metadata",
            str(metadata_path),
            "--metadata-sha256",
            metadata_ref["sha256"],
            *lease,
            *expected,
        ]
    if operation == "GIT_RECORD":
        candidate = _candidate_sha(repo, target["candidate"])
        _validate_git_packet_target(repo, target, entry, candidate)
        return [
            "record-candidate",
            *common,
            "--worktree-ref",
            target["worktree_ref"],
            "--candidate",
            candidate,
            *lease,
            *expected,
        ]
    if operation == "GIT_PREPARE":
        candidate = _candidate_sha(repo, target["candidate"])
        _validate_git_packet_target(repo, target, entry, candidate)
        repository = _repository_facts(repo)
        if repository["target_sha"] != target["expected_target_sha"]:
            raise ClerkRefusal(
                "TARGET_PREDECESSOR_MISMATCH",
                "local target differs from frozen predecessor",
            )
        if target["policy"] == "ORTHOGONAL_DIRECTION":
            if (
                target["common_epoch_sha"] != target["base_sha"]
                or target["parallel_authorization_ref"] is None
            ):
                raise ClerkRefusal(
                    "PARALLEL_AUTHORITY_MISMATCH",
                    "orthogonal prepare requires its exact common epoch and authorization",
                )
            direction = (
                inspection.get("parallel_direction")
                if isinstance(inspection, Mapping)
                else None
            )
            if not isinstance(direction, Mapping):
                raise ClerkRefusal(
                    "PARALLEL_AUTHORITY_MISMATCH",
                    "public worktree inspection omitted parallel authority",
                )
            if sorted(target["dependency_paths"]) != direction.get(
                "dependency_paths"
            ):
                raise ClerkRefusal(
                    "DEPENDENCY_FOOTPRINT_MISMATCH",
                    "orthogonal dependency paths differ from authorization",
                )
            auth_ref = target["parallel_authorization_ref"]
            registered_authority = entry["parallel_set_authorization"]
            registered_ref = {
                "path": registered_authority["manifest_path"],
                "sha256": registered_authority["manifest_sha256"],
            }
            if auth_ref != registered_ref:
                raise ClerkRefusal(
                    "PARALLEL_AUTHORITY_MISMATCH",
                    "parallel authorization ref differs from registry",
                )
        elif (
            target["common_epoch_sha"] is not None
            or target["parallel_authorization_ref"] is not None
            or target["dependency_paths"]
        ):
            raise ClerkRefusal(
                "AUTHORITY_DRIFT",
                "exact prepare cannot carry orthogonal authority or dependency paths",
            )
        verification_paths = [
            _relative_ref(
                repo,
                _verify_content_ref(repo, ref, "target.verification_refs")[0],
            )
            for ref in target["verification_refs"]
        ]
        return [
            "prepare-integration",
            *common,
            "--worktree-ref",
            target["worktree_ref"],
            "--target",
            target["target_ref"],
            *sum((["--allowed-path", path] for path in target["allowed_paths"]), []),
            *sum((["--verification-ref", path] for path in verification_paths), []),
            *lease,
            *expected,
        ]
    if operation == "GIT_INTEGRATE_PUSH":
        candidate = _candidate_sha(repo, target["candidate"])
        _validate_git_packet_target(repo, target, entry, candidate)
        prepared_binding = target["prepared_receipt_binding"]
        if prepared_binding["output_field"] != "receipt_ref":
            raise ClerkRefusal("INVALID_PRIOR_BINDING", "prepared output field must be receipt_ref")
        prepared_path, _ = _prior_output(repo, prepared_binding)
        if not isinstance(prepared_path, Path):
            raise ClerkRefusal("MISSING_PRIOR_OUTPUT", "prepared receipt path is invalid")
        if target["git_actor"] != _authority_actor_or_writer(packet):
            raise ClerkRefusal("ACTOR_MISMATCH", "target Git actor differs from packet authority")
        return [
            "integrate-push",
            "--receipt",
            str(prepared_path),
            "--actor",
            target["git_actor"],
            "--policy",
            target["policy"],
            "--candidate",
            candidate,
            "--base",
            target["base_sha"],
            "--target-local-ref",
            target["target_local_ref"],
            "--target-remote-ref",
            target["target_remote_ref"],
            "--remote-name",
            target["remote_name"],
            "--expected-target-predecessor",
            target["expected_target_predecessor_sha"],
            "--expected-remote-predecessor",
            target["expected_remote_predecessor_sha"],
            "--prepared-operation-id",
            prepared_binding["operation_id"],
            "--prepared-receipt-sha256",
            prepared_binding["receipt_sha256"],
            *sum((["--allowed-path", path] for path in target["allowed_paths"]), []),
            *sum((["--changed-path", path] for path in target["changed_paths"]), []),
            *sum((["--dependency-path", path] for path in target["dependency_paths"]), []),
            "--diff-sha256",
            target["diff_sha256"],
            *sum(
                (
                    ["--verification-content-ref", f"{ref['path']}={ref['sha256']}"]
                    for ref in target["verification_refs"]
                ),
                [],
            ),
            "--push-authorization-ref",
            target["push_authorization_ref"]["path"],
            "--push-authorization-sha256",
            target["push_authorization_ref"]["sha256"],
            *lease,
            *expected,
        ]
    raise ClerkRefusal("UNSUPPORTED_PRIMITIVE", f"{operation} has no documented public primitive")

def _validate_primitive_result(
    packet: Mapping[str, Any],
    repo: Path,
    result: Mapping[str, Any],
) -> None:
    operation = packet["operation"]
    target = packet["target"]
    expected_operation = {
        "WORKTREE_PROVISION": "provision",
        "WORKTREE_INSPECT": "inspect",
        "WORKTREE_RELEASE": "release",
        "PATCH_APPLY": "apply-patch",
        "CANDIDATE_CREATE": "create-candidate",
        "GIT_RECORD": "record-candidate",
        "GIT_PREPARE": "prepare-integration",
        "GIT_INTEGRATE_PUSH": "integrate-push",
    }[operation]
    if result.get("operation") != expected_operation:
        raise ClerkUnknown(
            "PRIMITIVE_RESULT_MISMATCH",
            "public primitive result names a different operation",
        )
    worktree = result.get("worktree")
    if not isinstance(worktree, Mapping):
        raise ClerkUnknown(
            "PRIMITIVE_RESULT_MISMATCH",
            "public primitive result omits exact worktree facts",
        )
    expected_policy = target.get("policy", target.get("integration_policy"))
    frozen = {
        "worktree_ref": target["worktree_ref"],
        "canonical_absolute_path": target["canonical_worktree_path"],
        "integration_policy": expected_policy,
        "required_handoff_sha": target["required_handoff_sha"],
        "required_dependency_refs": _canonical_packet_refs(
            target["required_dependency_refs"],
            "target.required_dependency_refs",
        ),
    }
    optional = {
        "direction_id": "direction_id",
        "worktree_kind": "kind",
        "base_sha": "base_sha",
    }
    for target_key, result_key in optional.items():
        if target_key in target:
            frozen[result_key] = target[target_key]
    if (
        operation == "CANDIDATE_CREATE"
        and worktree.get("base_sha") != target["declared_base_sha"]
    ):
        raise ClerkUnknown(
            "PRIMITIVE_RESULT_MISMATCH",
            "created candidate result changed the declared base",
        )
    observed = {
        **worktree,
        "integration_policy": _validated_integration_policy(
            worktree,
            after_effect=True,
        ),
        "required_handoff_sha": worktree.get("required_handoff_sha"),
        "required_dependency_refs": _canonical_packet_refs(
            worktree.get("required_dependency_refs", []),
            "primitive.required_dependency_refs",
        ),
    }
    for key, value in frozen.items():
        if observed.get(key) != value:
            raise ClerkUnknown(
                "PRIMITIVE_RESULT_MISMATCH",
                f"public primitive result changed frozen {key}",
            )
    if operation == "WORKTREE_INSPECT":
        expected_lifecycle = target["expected_lifecycle"]
    elif operation == "WORKTREE_RELEASE":
        expected_lifecycle = (
            "RETAINED_FOR_RECOVERY"
            if target["ignored_artifacts"] == "retain"
            else "RELEASED"
        )
    else:
        expected_lifecycle = {
            "WORKTREE_PROVISION": "PROVISIONED",
            "PATCH_APPLY": "PATCHED",
            "CANDIDATE_CREATE": "CANDIDATE_READY",
            "GIT_RECORD": "CANDIDATE_READY",
            "GIT_PREPARE": "PREPARED_FOR_INTEGRATION",
            "GIT_INTEGRATE_PUSH": "INTEGRATED",
        }[operation]
    if worktree.get("lifecycle") != expected_lifecycle:
        raise ClerkUnknown(
            "PRIMITIVE_RESULT_MISMATCH",
            "public primitive result lifecycle differs from the exact contract",
        )
    if operation == "PATCH_APPLY":
        prepared_ref = result.get("prepared_tree_receipt_ref")
        if not isinstance(prepared_ref, Mapping):
            raise ClerkUnknown(
                "PRIMITIVE_RESULT_MISMATCH",
                "apply-patch result omits its immutable prepared-tree receipt",
            )
        _verify_content_ref(repo, prepared_ref, "prepared-tree receipt result")
        if (
            result.get("result_tree_sha") != target["expected_result_tree_sha"]
            or result.get("diff_sha256")
            != target["expected_post_apply_diff_sha256"]
            or result.get("changed_paths")
            != sorted(target["expected_changed_paths"])
        ):
            raise ClerkUnknown(
                "PRIMITIVE_RESULT_MISMATCH",
                "apply-patch result differs from frozen tree or delta",
            )
    if operation in {"CANDIDATE_CREATE", "GIT_RECORD"}:
        if operation == "GIT_RECORD":
            candidate = _candidate_sha(repo, target["candidate"])
        else:
            candidate = result.get("candidate_sha")
            if not isinstance(candidate, str) or re.fullmatch(
                r"(?:[0-9a-f]{40}|[0-9a-f]{64})", candidate
            ) is None:
                raise ClerkUnknown(
                    "PRIMITIVE_RESULT_MISMATCH",
                    "created candidate result has no full candidate SHA",
                )
            if worktree.get("candidate_sha") != candidate:
                raise ClerkUnknown(
                    "PRIMITIVE_RESULT_MISMATCH",
                    "created candidate result and worktree disagree",
                )
        if result.get("candidate_sha") != candidate:
            raise ClerkUnknown(
                "PRIMITIVE_RESULT_MISMATCH",
                "candidate result differs from exact binding",
            )
        if operation == "CANDIDATE_CREATE":
            prepared_value, _ = _prior_output(
                repo, target["prepared_tree_receipt_binding"]
            )
            _, expected_prepared_ref = _verify_content_ref(
                repo, prepared_value, "candidate prepared-tree receipt"
            )
            if (
                result.get("tree_sha") != target["expected_tree_sha"]
                or result.get("diff_sha256") != target["expected_diff_sha256"]
                or result.get("changed_paths")
                != sorted(target["expected_changed_paths"])
                or result.get("prepared_tree_receipt_ref")
                != expected_prepared_ref
            ):
                raise ClerkUnknown(
                    "PRIMITIVE_RESULT_MISMATCH",
                    "created candidate result differs from frozen tree, delta, or receipt",
                )
    if (
        operation == "GIT_PREPARE"
        and result.get("changed_paths") != sorted(target["changed_paths"])
    ):
        raise ClerkUnknown(
            "PRIMITIVE_RESULT_MISMATCH",
            "prepared result changed the frozen path set",
        )
    if operation == "GIT_INTEGRATE_PUSH":
        candidate = _candidate_sha(repo, target["candidate"])
        prepared = target["prepared_receipt_binding"]
        validated = result.get("validated_contract")
        if not isinstance(validated, Mapping):
            raise ClerkUnknown(
                "PRIMITIVE_RESULT_MISMATCH",
                "integrate-push result omits validated frozen contract",
            )
        expected_contract = {
            "policy": target["policy"],
            "candidate_sha": candidate,
            "base_sha": target["base_sha"],
            "target_local_ref": target["target_local_ref"],
            "target_remote_ref": target["target_remote_ref"],
            "remote_name": target["remote_name"],
            "expected_target_predecessor_sha": target[
                "expected_target_predecessor_sha"
            ],
            "expected_remote_predecessor_sha": target[
                "expected_remote_predecessor_sha"
            ],
            "prepared_operation_id": prepared["operation_id"],
            "prepared_receipt_sha256": prepared["receipt_sha256"],
            "allowed_paths": sorted(target["allowed_paths"]),
            "changed_paths": sorted(target["changed_paths"]),
            "dependency_paths": sorted(target["dependency_paths"]),
            "diff_sha256": target["diff_sha256"],
            "verification_refs": _canonical_packet_refs(
                target["verification_refs"], "target.verification_refs"
            ),
            "push_authorization_ref": target["push_authorization_ref"],
        }
        for key, value in expected_contract.items():
            if validated.get(key) != value:
                raise ClerkUnknown(
                    "PRIMITIVE_RESULT_MISMATCH",
                    f"integrate-push result changed frozen {key}",
                )
        if result.get("integrated_sha") != candidate:
            raise ClerkUnknown(
                "PRIMITIVE_RESULT_MISMATCH",
                "integrate-push result changed the candidate identity",
            )


def _execute_primitive(packet: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    operation = packet["operation"]
    target = packet["target"]
    if operation == "STATE_CAS":
        input_path = _target_ref_path(repo, target, "input_ref")
        state_path = _repo_path(
            repo,
            target["canonical_target_path"],
            "target.canonical_target_path",
        )
        try:
            document = hmasd_state.replace(
                target["state_kind"],
                state_path,
                target["expected_document_writer"],
                target["expected_revision"],
                input_path,
            )
        except hmasd_state.StateError as exc:
            raise ClerkRefusal("STATE_CAS_REFUSED", str(exc), effect_state="NOT_LANDED") from exc
        return {
            "ok": True,
            "operation": "state-cas",
            "revision": document.get("revision"),
            "path": _relative_ref(repo, state_path),
            "sha256": hmasd_state.sha256_file(state_path),
        }
    result = _invoke_worktree(_worktree_command(packet, repo))
    _validate_primitive_result(packet, repo, result)
    return result


def _claim_paths(repo: Path, operation_id: str) -> tuple[Path, Path]:
    root = repo / ".omp" / "runtime" / "clerk"
    identity = _sha256(operation_id.encode("utf-8"))
    return root / "claims" / f"{identity}.json", root / "locks" / f"{identity}.lock"

@contextlib.contextmanager
def _operation_lock(path: Path) -> Generator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_chain(path.parent, "Clerk lock directory")
    try:
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags, 0o600)
        handle = os.fdopen(descriptor, "a+b")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    except OSError as exc:
        raise ClerkRefusal("CLAIM_UNAVAILABLE", "cannot acquire operation claim lock") from exc
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _atomic_create(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_chain(path.parent, "Clerk ledger directory")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".new", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short Clerk ledger write")
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        try:
            os.link(temp_path, path)
        except FileExistsError:
            _reject_symlink_chain(path, "Clerk ledger path")
            if path.read_bytes() != data:
                raise ClerkRefusal("CLAIM_COLLISION", "content-addressed ledger path already contains different bytes")
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        with contextlib.suppress(FileNotFoundError):
            temp_path.unlink()


def _load_claim(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ClerkRefusal("CLAIM_UNAVAILABLE", "cannot read operation claim") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClerkUnknown("CLAIM_CORRUPT", "operation claim cannot be interpreted safely") from exc
    if not isinstance(value, dict) or raw != _canonical_bytes(value):
        raise ClerkUnknown("CLAIM_CORRUPT", "operation claim is not canonical")
    expected = {
        "schema",
        "operation_id",
        "packet_file_sha256",
        "state",
        "attempt",
        "receipt_ref",
    }
    if set(value) != expected or value["schema"] != CLAIM_SCHEMA or value["state"] not in {
        "PENDING",
        "STARTED",
        "SUCCEEDED",
        "REFUSED",
        "UNKNOWN",
    }:
        raise ClerkUnknown("CLAIM_CORRUPT", "operation claim has an invalid closed shape")
    return value


def _write_claim(path: Path, claim: Mapping[str, Any], *, create: bool = False) -> None:
    data = _canonical_bytes(claim)
    if create:
        _atomic_create(path, data)
    else:
        hmasd_state.atomic_write(path, data)


def _receipt_core(
    packet: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    executor: Mapping[str, Any],
    *,
    outcome: str,
    effect_state: str,
    code: str,
    message: str,
    receipt_refs: Sequence[Mapping[str, str]] = (),
    observation_refs: Sequence[Any] = (),
) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "operation_id": packet["operation_id"],
        "clerk_assignment_id": packet["clerk_assignment_id"],
        "packet_ref": dict(dispatch["packet_ref"]),
        "accepted_authorizer_result_sha256": dispatch[
            "accepted_authorizer_result"
        ]["result_sha256"],
        "accepted_producer_results": list(dispatch["accepted_producer_results"]),
        "executor_identity": executor["logical_identity"],
        "executor_generation": executor["generation"],
        "authorizer": dict(packet["authorizer"]),
        "operation": packet["operation"],
        "authority_actor_or_writer": _authority_actor_or_writer(packet),
        "resources": [dict(resource) for resource in packet["mutation"]["resources"]],
        "attempt": 1,
        "outcome": outcome,
        "effect_state": effect_state,
        "reason": {"code": code, "message": message},
        "receipt_refs": [dict(ref) for ref in receipt_refs],
        "observation_refs": list(observation_refs),
    }


def _primitive_observations(
    repo: Path,
    result: Mapping[str, Any],
) -> tuple[list[dict[str, str]], list[Any]]:
    receipts: list[dict[str, str]] = []
    receipt_path = result.get("receipt")
    if isinstance(receipt_path, str):
        path = _repo_path(repo, receipt_path, "primitive receipt")
        receipts.append(
            {
                "path": _relative_ref(repo, path),
                "sha256": hmasd_state.sha256_file(path),
            }
        )
    scalar_keys = (
        "operation",
        "registry_revision",
        "revision",
        "candidate_sha",
        "candidate_ref",
        "integrated_sha",
        "result_tree_sha",
        "tree_sha",
        "diff_sha256",
        "integration_policy",
        "integration_phase",
        "status",
        "orphaned",
        "orphan_reason",
        "path",
        "sha256",
    )
    facts = {
        key: result[key]
        for key in scalar_keys
        if key in result
        and isinstance(result[key], (str, int, bool, type(None)))
    }
    prepared_ref = result.get("prepared_tree_receipt_ref")
    if isinstance(prepared_ref, Mapping):
        _, normalized = _verify_content_ref(
            repo, prepared_ref, "primitive prepared-tree receipt"
        )
        facts["prepared_tree_receipt_ref"] = normalized
    changed_paths = result.get("changed_paths")
    if isinstance(changed_paths, list) and all(
        isinstance(path, str) for path in changed_paths
    ):
        facts["changed_paths"] = sorted(changed_paths)
    observations: list[Any] = [facts] if facts else []
    return receipts, observations


def _persist_receipt(repo: Path, packet_file_sha256: str, receipt: Mapping[str, Any]) -> dict[str, str]:
    data = _canonical_bytes(receipt)
    digest = _sha256(data)
    path = repo / ".omp" / "runtime" / "clerk" / "receipts" / packet_file_sha256 / f"{digest}.json"
    _atomic_create(path, data)
    return {"path": _relative_ref(repo, path), "sha256": digest}


def _read_receipt(repo: Path, ref: Any) -> tuple[dict[str, Any], dict[str, str]]:
    try:
        path, normalized = _verify_content_ref(repo, ref, "claim.receipt_ref")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ClerkRefusal, OSError, json.JSONDecodeError) as exc:
        raise ClerkUnknown("RECEIPT_CORRUPT", "terminal receipt cannot be read safely") from exc
    if not isinstance(value, dict) or _canonical_bytes(value) != path.read_bytes():
        raise ClerkUnknown("RECEIPT_CORRUPT", "terminal receipt is not canonical")
    return value, normalized


def _emit(receipt: Mapping[str, Any], receipt_ref: Mapping[str, str] | None) -> int:
    outcome = str(receipt.get("outcome"))
    status = {
        "SUCCEEDED": "COMPLETED",
        "REFUSED": "BLOCKED",
        "UNKNOWN": "PARTIAL",
    }.get(outcome, "FAILED")
    raw_receipt_refs = (
        [dict(receipt_ref)] if receipt_ref is not None else []
    )
    primitive_refs = [
        dict(ref)
        for ref in receipt.get("receipt_refs", [])
        if isinstance(ref, Mapping)
    ]
    all_receipt_refs = [*raw_receipt_refs, *primitive_refs]
    operation = receipt.get("operation")
    effect_state = receipt.get("effect_state")
    materiality = (
        "NONE"
        if outcome == "REFUSED"
        or (outcome == "SUCCEEDED" and operation == "WORKTREE_INSPECT")
        else "LOCAL"
    )
    reason = receipt.get("reason")
    summary = (
        str(reason.get("message"))
        if isinstance(reason, Mapping) and reason.get("message")
        else f"Clerk operation {operation} ended {outcome}"
    )
    payload = {
        "kind": "clerk",
        "operation_id": receipt.get("operation_id"),
        "packet_ref": (
            dict(receipt["packet_ref"])
            if isinstance(receipt.get("packet_ref"), Mapping)
            else None
        ),
        "executor_identity": receipt["executor_identity"],
        "authorizer": (
            dict(receipt["authorizer"])
            if isinstance(receipt.get("authorizer"), Mapping)
            else None
        ),
        "operation": operation,
        "authority_actor_or_writer": receipt.get("authority_actor_or_writer"),
        "resources": [
            dict(resource) for resource in receipt.get("resources", [])
        ],
        "attempt": 1,
        "outcome": outcome,
        "effect_state": effect_state,
        "receipt_refs": all_receipt_refs,
        "observation_refs": list(receipt.get("observation_refs", [])),
    }
    value = {
        "schema_version": 2,
        "role": "hmasd-clerk",
        "logical_identity": receipt["executor_identity"],
        "generation": receipt["executor_generation"],
        "assignment_id": receipt["clerk_assignment_id"],
        "status": status,
        "materiality": materiality,
        "summary": summary,
        "changed_paths": [],
        "state_refs": primitive_refs,
        "artifact_refs": raw_receipt_refs,
        "checkpoint_sha": (
            receipt_ref["sha256"] if receipt_ref is not None else None
        ),
        "decision_requests": [],
        "next_actions": [],
        "payload": payload,
    }
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if outcome == "SUCCEEDED" else 6 if outcome == "UNKNOWN" else 2


def _terminal(
    repo: Path,
    claim_path: Path,
    claim: dict[str, Any],
    packet: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    attestation: Mapping[str, Any],
    packet_file_sha256: str,
    *,
    outcome: str,
    effect_state: str,
    code: str,
    message: str,
    receipt_refs: Sequence[Mapping[str, str]] = (),
    observation_refs: Sequence[Any] = (),
) -> int:
    receipt = _receipt_core(
        packet,
        dispatch,
        attestation,
        outcome=outcome,
        effect_state=effect_state,
        code=code,
        message=message,
        receipt_refs=receipt_refs,
        observation_refs=observation_refs,
    )
    receipt_ref = _persist_receipt(repo, packet_file_sha256, receipt)
    claim["state"] = outcome
    claim["receipt_ref"] = receipt_ref
    _write_claim(claim_path, claim)
    return _emit(receipt, receipt_ref)


def _collision_receipt(
    repo: Path,
    packet: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    attestation: Mapping[str, Any],
    packet_file_sha256: str,
) -> int:
    receipt = _receipt_core(
        packet,
        dispatch,
        attestation,
        outcome="REFUSED",
        effect_state="NOT_ATTEMPTED",
        code="OPERATION_ID_COLLISION",
        message="operation_id is already claimed by different packet bytes",
    )
    data = _canonical_bytes(receipt)
    digest = _sha256(data)
    identity = _sha256(str(packet["operation_id"]).encode("utf-8"))
    path = repo / ".omp" / "runtime" / "clerk" / "collisions" / identity / packet_file_sha256 / f"{digest}.json"
    _atomic_create(path, data)
    return _emit(receipt, {"path": _relative_ref(repo, path), "sha256": digest})


def _operation_observation(
    packet: Mapping[str, Any],
    repo: Path,
) -> dict[str, Any]:
    observation: dict[str, Any] = {
        "operation": packet["operation"],
        "observation_count": 1,
    }
    try:
        target = packet["target"]
        if packet["operation"] == "STATE_CAS":
            path = _repo_path(
                repo,
                target["canonical_target_path"],
                "orphan state target",
            )
            raw = path.read_bytes()
            document = json.loads(raw.decode("utf-8"))
            observation["state"] = {
                "path": _relative_ref(repo, path),
                "sha256": _sha256(raw),
                "revision": (
                    document.get("revision")
                    if isinstance(document, Mapping)
                    else None
                ),
            }
            return observation

        worktree_facts = _invoke_worktree(
            [
                "observe",
                "--repo",
                str(repo),
                "--worktree-ref",
                target["worktree_ref"],
            ]
        )
        registry = worktree_facts.get("registry")
        worktree = worktree_facts.get("worktree")
        if isinstance(registry, Mapping):
            observation["registry"] = dict(registry)
        if isinstance(worktree, Mapping):
            observation["worktree"] = dict(worktree)
        integration = worktree_facts.get("integration")
        if isinstance(integration, Mapping):
            observation["integration"] = _validated_helper_observation(
                0,
                integration,
            )
        if packet["operation"] == "GIT_INTEGRATE_PUSH":
            repository = _repository_facts(
                repo,
                remote_name=target["remote_name"],
                remote_ref=target["target_remote_ref"],
            )
            remote_target = repository.get("remote_target")
            if isinstance(remote_target, Mapping):
                observation["target_remote"] = dict(remote_target)
    except Exception as exc:
        observation["observation_error"] = type(exc).__name__
    return observation


def build_packet(repo_raw: str, draft_raw: str, output_raw: str) -> int:
    repo = _canonical_existing(
        str(Path(repo_raw).resolve(strict=True)),
        "repository",
        directory=True,
    )
    draft_path = _canonical_existing(
        str(Path(draft_raw).resolve(strict=True)),
        "packet draft",
    )
    try:
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClerkRefusal("INVALID_PACKET", "packet draft is not valid UTF-8 JSON") from exc
    if not isinstance(draft, dict):
        raise ClerkRefusal("INVALID_PACKET", "packet draft must be a JSON object")
    expected_keys = {
        "operation_id",
        "clerk_assignment_id",
        "authorizer",
        "authority",
        "operation",
        "requires",
        "target",
        "acceptance_refs",
    }
    if set(draft) != expected_keys:
        missing = sorted(expected_keys - set(draft))
        extra = sorted(set(draft) - expected_keys)
        detail = [
            *(f"missing {key}" for key in missing),
            *(f"unexpected {key}" for key in extra),
        ]
        raise ClerkRefusal(
            "INVALID_PACKET",
            "packet draft has " + ", ".join(detail),
        )
    operation = draft["operation"]
    if operation not in OPERATIONS:
        raise ClerkRefusal("UNSUPPORTED_OPERATION", "packet draft operation is unsupported")
    operation_id = _require_id(draft["operation_id"], "operation_id")
    clerk_assignment_id = _require_id(
        draft["clerk_assignment_id"],
        "clerk_assignment_id",
    )
    target = draft["target"]
    if not isinstance(target, Mapping):
        raise ClerkRefusal("INVALID_PACKET", "packet draft target must be an object")
    effect_seed = {
        "operation_id": operation_id,
        "clerk_assignment_id": clerk_assignment_id,
        "operation": operation,
        "target": target,
    }
    packet: dict[str, Any] = {
        "schema_version": 1,
        "kind": "clerk_operation",
        "operation_id": operation_id,
        "clerk_assignment_id": clerk_assignment_id,
        "executor": {
            "role": "hmasd-clerk",
            "logical_identity": f"Clerk-{clerk_assignment_id}",
            "generation": 1,
        },
        "authorizer": draft["authorizer"],
        "operation": operation,
        "requires": draft["requires"],
        "authority": draft["authority"],
        "mutation": {
            "class": OPERATION_MUTATION_CLASS[operation],
            "resources": _expected_operation_resources(operation, target, repo),
        },
        "effect": {
            "attempt": 1,
            "attempt_token": _sha256(_canonical_bytes(effect_seed)),
            "authorized_effects": (
                [] if operation == "WORKTREE_INSPECT" else [operation]
            ),
            "unknown_outcome": "OBSERVE_ONLY_NO_AUTOMATIC_RETRY",
        },
        "target": target,
        "acceptance_refs": draft["acceptance_refs"],
        "postconditions": {
            "success": ["exact public primitive postcondition observed"],
            "refusal": ["no unauthorized effect landed"],
            "unknown": "OBSERVE_ONLY_NO_AUTOMATIC_RETRY",
        },
        "stop_condition": "Return one terminal Clerk fact without retry.",
        "return_owner": "ROOT",
    }
    packet["packet_sha256"] = _sha256(_canonical_bytes(packet))
    try:
        hmasd_state.validate_document("clerk_operation", packet)
    except hmasd_state.StateError as exc:
        raise ClerkRefusal("INVALID_PACKET", str(exc)) from exc
    _validate_operation_binding(packet, repo)

    output_candidate = Path(output_raw)
    output_path = (
        output_candidate
        if output_candidate.is_absolute()
        else repo / output_candidate
    )
    output_path = Path(os.path.normpath(output_path))
    if not _under(output_path, repo):
        raise ClerkRefusal("NONCANONICAL_PATH", "packet output escapes repository")
    data = _canonical_bytes(packet)
    created = True
    if output_path.exists():
        _reject_symlink_chain(output_path, "packet output")
        if output_path.read_bytes() != data:
            raise ClerkRefusal(
                "PACKET_IDENTITY_COLLISION",
                "packet output already contains different bytes",
            )
        created = False
    else:
        _atomic_create(output_path, data)
    result = {
        "ok": True,
        "operation": "build",
        "created": created,
        "operation_id": operation_id,
        "packet_ref": {
            "path": _relative_ref(repo, output_path),
            "sha256": _sha256(data),
        },
        "mutation": packet["mutation"],
    }
    print(json.dumps(result, sort_keys=True))
    return 0


def execute(packet_raw: str) -> int:
    packet_path, packet, _, packet_file_sha256 = _load_packet(packet_raw)
    repo = _packet_repo(packet, packet_path)
    if not _under(packet_path, repo):
        raise ClerkRefusal("NONCANONICAL_PACKET", "packet must be inside its canonical repository")
    dispatch, attestation = _dispatch_binding(
        packet_path,
        repo,
        packet,
        packet_file_sha256,
    )
    _require_id(packet["operation_id"], "operation_id")
    _validate_operation_binding(packet, repo)

    claim_path, lock_path = _claim_paths(repo, packet["operation_id"])
    with _operation_lock(lock_path):
        try:
            claim = _load_claim(claim_path)
        except ClerkUnknown as exc:
            receipt = _receipt_core(
                packet,
                dispatch,
                attestation,
                outcome="UNKNOWN",
                effect_state="UNKNOWN",
                code=exc.code,
                message=str(exc),
            )
            return _emit(receipt, None)
        if claim is not None:
            if claim["operation_id"] != packet["operation_id"] or claim["packet_file_sha256"] != packet_file_sha256:
                return _collision_receipt(repo, packet, dispatch, attestation, packet_file_sha256)
            if claim["state"] in {"SUCCEEDED", "REFUSED", "UNKNOWN"}:
                try:
                    receipt, receipt_ref = _read_receipt(repo, claim["receipt_ref"])
                except ClerkUnknown as exc:
                    unknown = _receipt_core(
                        packet,
                        dispatch,
                        attestation,
                        outcome="UNKNOWN",
                        effect_state="UNKNOWN",
                        code=exc.code,
                        message=str(exc),
                    )
                    return _emit(unknown, None)
                return _emit(receipt, receipt_ref)
            if claim["state"] == "STARTED":
                return _terminal(
                    repo,
                    claim_path,
                    claim,
                    packet,
                    dispatch,
                    attestation,
                    packet_file_sha256,
                    outcome="UNKNOWN",
                    effect_state="UNKNOWN",
                    code="ORPHAN_STARTED",
                    message="prior STARTED claim has no terminal receipt; observation only, no retry",
                    observation_refs=[_operation_observation(packet, repo)],
                )
        else:
            claim = {
                "schema": CLAIM_SCHEMA,
                "operation_id": packet["operation_id"],
                "packet_file_sha256": packet_file_sha256,
                "state": "PENDING",
                "attempt": 1,
                "receipt_ref": None,
            }
            _write_claim(claim_path, claim, create=True)

        try:
            _verify_producer_dependencies(packet, dispatch)
            precondition_refs = _verify_preconditions(packet, repo)
            # Building argv validates primitive availability and the physical lease
            # before the durable STARTED transition.
            if packet["operation"] != "STATE_CAS":
                _worktree_command(packet, repo)
        except ClerkRefusal as exc:
            return _terminal(
                repo,
                claim_path,
                claim,
                packet,
                dispatch,
                attestation,
                packet_file_sha256,
                outcome="REFUSED",
                effect_state=exc.effect_state,
                code=exc.code,
                message=str(exc),
            )

        claim["state"] = "STARTED"
        _write_claim(claim_path, claim)
        try:
            result = _execute_primitive(packet, repo)
        except ClerkRefusal as exc:
            return _terminal(
                repo,
                claim_path,
                claim,
                packet,
                dispatch,
                attestation,
                packet_file_sha256,
                outcome="REFUSED",
                effect_state=exc.effect_state,
                code=exc.code,
                message=str(exc),
                observation_refs=precondition_refs,
            )
        except ClerkUnknown as exc:
            return _terminal(
                repo,
                claim_path,
                claim,
                packet,
                dispatch,
                attestation,
                packet_file_sha256,
                outcome="UNKNOWN",
                effect_state="UNKNOWN",
                code=exc.code,
                message=str(exc),
                observation_refs=[*precondition_refs, *exc.observations],
            )
        except Exception as exc:  # After STARTED, ambiguity is always observe-only UNKNOWN.
            return _terminal(
                repo,
                claim_path,
                claim,
                packet,
                dispatch,
                attestation,
                packet_file_sha256,
                outcome="UNKNOWN",
                effect_state="UNKNOWN",
                code="UNCLASSIFIED_PRIMITIVE_OUTCOME",
                message=f"primitive outcome cannot be proven: {type(exc).__name__}",
                observation_refs=[
                    *precondition_refs,
                    _operation_observation(packet, repo),
                ],
            )
        primitive_receipts, primitive_observations = _primitive_observations(repo, result)
        effect_state = "NOT_APPLICABLE" if packet["operation"] == "WORKTREE_INSPECT" else "LANDED"
        return _terminal(
            repo,
            claim_path,
            claim,
            packet,
            dispatch,
            attestation,
            packet_file_sha256,
            outcome="SUCCEEDED",
            effect_state=effect_state,
            code="COMPLETED",
            message="exact authorized primitive completed once",
            receipt_refs=primitive_receipts,
            observation_refs=[*precondition_refs, *primitive_observations],
        )


def _transient_refusal(packet_raw: str, exc: ClerkRefusal) -> int:
    operation_id: str | None = None
    assignment_id = "transient"
    executor_identity = "Clerk-transient"
    executor_generation = 1
    packet_ref: dict[str, str] | None = None
    authorizer: dict[str, Any] | None = None
    operation: str | None = None
    resources: list[dict[str, str]] = []
    try:
        path = Path(packet_raw)
        raw = path.read_bytes()
        packet = json.loads(raw.decode("utf-8"))
        if isinstance(packet, Mapping):
            operation_id = (
                packet.get("operation_id")
                if isinstance(packet.get("operation_id"), str)
                else None
            )
            assignment_id = (
                packet.get("clerk_assignment_id")
                if isinstance(packet.get("clerk_assignment_id"), str)
                else assignment_id
            )
            executor = packet.get("executor")
            if isinstance(executor, Mapping):
                if isinstance(executor.get("logical_identity"), str):
                    executor_identity = executor["logical_identity"]
                if (
                    isinstance(executor.get("generation"), int)
                    and not isinstance(executor.get("generation"), bool)
                ):
                    executor_generation = executor["generation"]
            if isinstance(packet.get("authorizer"), Mapping):
                authorizer = dict(packet["authorizer"])
            if packet.get("operation") in OPERATIONS:
                operation = packet["operation"]
            mutation = packet.get("mutation")
            if isinstance(mutation, Mapping) and isinstance(
                mutation.get("resources"), list
            ):
                resources = [
                    dict(resource)
                    for resource in mutation["resources"]
                    if isinstance(resource, Mapping)
                    and set(resource) == {"kind", "key"}
                ]
            repo = _packet_repo(packet, path)
            packet_ref = {
                "path": _relative_ref(repo, path),
                "sha256": _sha256(raw),
            }
    except Exception:
        pass
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "operation_id": operation_id,
        "clerk_assignment_id": assignment_id,
        "packet_ref": packet_ref,
        "executor_identity": executor_identity,
        "executor_generation": executor_generation,
        "authorizer": authorizer,
        "operation": operation,
        "authority_actor_or_writer": None,
        "resources": resources,
        "attempt": 1,
        "outcome": "REFUSED",
        "effect_state": exc.effect_state,
        "reason": {"code": exc.code, "message": str(exc)},
        "receipt_refs": [],
        "observation_refs": [],
    }
    return _emit(receipt, None)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--repo", default=".")
    build_parser.add_argument("--draft", required=True)
    build_parser.add_argument("--output", required=True)
    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--packet", required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "build":
            return build_packet(args.repo, args.draft, args.output)
        if args.command == "execute":
            return execute(args.packet)
        raise ClerkRefusal("UNSUPPORTED_COMMAND", "unsupported Clerk command")
    except ClerkRefusal as exc:
        if args.command == "execute":
            return _transient_refusal(args.packet, exc)
        print(
            json.dumps(
                {
                    "ok": False,
                    "operation": "build",
                    "error": {"code": exc.code, "message": str(exc)},
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
