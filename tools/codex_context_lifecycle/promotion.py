"""Promotion kinds, owner matrix, and lifecycle helpers.

The promotion subsystem never edits canonical files. It records proposals and
applied references only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from tools.codex_semantic_mvp.actor_models import ActorKind, actor_context_from_row
from tools.codex_semantic_mvp.models import ObligationKind
from tools.codex_semantic_mvp.store import SemanticStore, _json, _new_id, _now

from .authority import AuthorityError, default_repo_root, require_same_actor, touch_actor_workflow

from .models import (
    ContextSourceKind,
    PromotionKind,
    PromotionProposal,
    PromotionState,
)
from .precedence import assert_authoritative_source, precedence_for_kind

ALLOWED_ORIGINS = frozenset(
    {
        ContextSourceKind.USER_AUTHORITY,
        ContextSourceKind.CANONICAL_OWNER_ARTIFACT,
        ContextSourceKind.PLAN_EPOCH,
        ContextSourceKind.TYPED_PACKET,
        ContextSourceKind.TYPED_REPORT,
        ContextSourceKind.STAGE_OR_PORTFOLIO_CONTRACT,
        ContextSourceKind.ROLE_CONTRACT,
        ContextSourceKind.ROUTER,
    }
)
FORBIDDEN_ORIGINS = frozenset(
    {
        ContextSourceKind.RAW_CONVERSATION,
        ContextSourceKind.TOOL_OUTPUT,
        ContextSourceKind.COMPACTION_SUMMARY,
        ContextSourceKind.AUTOMATIC_MEMORY,
    }
)

VALID_TRANSITIONS = {
    PromotionState.PROPOSED: {
        PromotionState.OWNER_ACCEPTED,
        PromotionState.OWNER_REJECTED,
        PromotionState.CARRIED_FORWARD,
    },
    PromotionState.CARRIED_FORWARD: {
        PromotionState.OWNER_ACCEPTED,
        PromotionState.OWNER_REJECTED,
    },
    PromotionState.OWNER_ACCEPTED: {PromotionState.APPLIED},
}

DEFAULT_TARGETS = {
    PromotionKind.AUTHORITY_RULE: "AGENTS.md or Role",
    PromotionKind.ROLE_CONTRACT: "Role",
    PromotionKind.PROCEDURE: "Skill",
    PromotionKind.REPOSITORY_NAVIGATION: "PROJECT_MAP or CURRENT_WORK",
    PromotionKind.SHARED_ARCHITECTURE_DECISION: "ADR",
    PromotionKind.SCIENTIFIC_ARTIFACT: "existing direction artifact",
    PromotionKind.TECHNICAL_ARTIFACT: "existing technical artifact",
    PromotionKind.PORTFOLIO_ARTIFACT: "portfolio adjudication",
    PromotionKind.CURRENT_WORK_POINTER: "partitioned current-work record",
    PromotionKind.EPHEMERAL: "none",
}


class PromotionError(ValueError):
    """Raised when a promotion proposal is unauthorized or malformed."""


def default_target_system(kind: PromotionKind | str) -> str:
    value = kind if isinstance(kind, PromotionKind) else PromotionKind(str(kind))
    return DEFAULT_TARGETS[value]


def _kind(value: PromotionKind | str) -> PromotionKind:
    return value if isinstance(value, PromotionKind) else PromotionKind(str(value))


def _actor_kind(value: ActorKind | str) -> ActorKind:
    return value if isinstance(value, ActorKind) else ActorKind(str(value))


def validate_promotion_owner(
    kind: PromotionKind | str,
    owner_actor_kind: ActorKind | str,
    target_ref: str | None = None,
    source_kind: ContextSourceKind | str | None = None,
) -> None:
    promotion_kind = _kind(kind)
    actor_kind = _actor_kind(owner_actor_kind)
    if source_kind is not None:
        origin = (
            source_kind
            if isinstance(source_kind, ContextSourceKind)
            else ContextSourceKind(str(source_kind))
        )
        if origin in FORBIDDEN_ORIGINS:
            raise PromotionError(f"{origin.value} cannot propose promotion")
        if origin not in ALLOWED_ORIGINS:
            raise PromotionError(f"{origin.value} is not an allowed promotion origin")
        assert_authoritative_source(origin, "create_promotion_proposal")
    target = (target_ref or "").replace("\\", "/")
    if promotion_kind is PromotionKind.EPHEMERAL:
        if actor_kind not in {
            ActorKind.PORTFOLIO,
            ActorKind.OPERATIONAL_ROOT,
            ActorKind.EM,
            ActorKind.CM,
            ActorKind.LEAF,
        }:
            raise PromotionError("unknown actor cannot keep ephemeral notes")
        if target:
            raise PromotionError("EPHEMERAL target_ref must be empty")
        return
    if actor_kind is ActorKind.LEAF:
        raise PromotionError("leaf cannot promote any canonical artifact")
    if promotion_kind is PromotionKind.AUTHORITY_RULE:
        if actor_kind is not ActorKind.OPERATIONAL_ROOT:
            raise PromotionError("only Operational Root may propose AUTHORITY_RULE")
        if target not in {"AGENTS.md", ".agents/roles/ROOT.md"} and not target.startswith(
            ".agents/roles/"
        ):
            raise PromotionError("AUTHORITY_RULE target_ref must be AGENTS.md or a Role path")
        return
    if promotion_kind is PromotionKind.ROLE_CONTRACT:
        role_owners = {
            ActorKind.OPERATIONAL_ROOT: ".agents/roles/ROOT.md",
            ActorKind.EM: ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md",
            ActorKind.CM: ".agents/roles/CODE_PROJECT_MANAGER.md",
        }
        expected = role_owners.get(actor_kind)
        if expected is None or target != expected:
            raise PromotionError("ROLE_CONTRACT owner must match the exact Role path")
        return
    if promotion_kind is PromotionKind.PROCEDURE:
        if not target.startswith(".agents/skills/") or not target.endswith("/SKILL.md"):
            raise PromotionError("PROCEDURE target_ref must be a Skill path")
        return
    if promotion_kind is PromotionKind.REPOSITORY_NAVIGATION:
        if target == "docs/project/PROJECT_MAP.md":
            if actor_kind is not ActorKind.CM:
                raise PromotionError("only CM may promote PROJECT_MAP navigation")
            return
        if target.startswith("docs/project/CURRENT_WORK") or target.startswith(
            "docs/project/current-work/"
        ):
            if actor_kind is not ActorKind.OPERATIONAL_ROOT:
                raise PromotionError("only Root may promote CURRENT_WORK pointers")
            return
        raise PromotionError("REPOSITORY_NAVIGATION target must already be PROJECT_MAP or CURRENT_WORK")
    if promotion_kind is PromotionKind.SHARED_ARCHITECTURE_DECISION:
        if actor_kind is not ActorKind.OPERATIONAL_ROOT:
            raise PromotionError("only Operational Root/user may propose an ADR")
        if target and not target.startswith("docs/project/decisions/ADR-"):
            raise PromotionError("ADR target_ref must be empty while proposed or an ADR path")
        return
    if promotion_kind is PromotionKind.SCIENTIFIC_ARTIFACT:
        if actor_kind is not ActorKind.EM:
            raise PromotionError("Root cannot promote direction science on EM's behalf")
        if target and not target.startswith("docs/research/candidates/"):
            raise PromotionError("scientific destination must be an existing direction artifact")
        return
    if promotion_kind is PromotionKind.TECHNICAL_ARTIFACT:
        if actor_kind is not ActorKind.CM:
            raise PromotionError("only a scoped CM may promote technical acceptance")
        return
    if promotion_kind is PromotionKind.PORTFOLIO_ARTIFACT:
        if actor_kind is not ActorKind.PORTFOLIO:
            raise PromotionError("CM cannot promote portfolio allocation")
        return
    if promotion_kind is PromotionKind.CURRENT_WORK_POINTER:
        if actor_kind is not ActorKind.OPERATIONAL_ROOT:
            raise PromotionError("CURRENT_WORK_POINTER owner must be the current-work owner")
        if not (
            target.startswith("docs/project/CURRENT_WORK")
            or target.startswith("docs/project/current-work/")
        ):
            raise PromotionError("CURRENT_WORK_POINTER must target a partitioned current-work record")
        return
    raise PromotionError(f"unknown promotion kind: {promotion_kind}")


REGISTRY_OWNER_KIND = {
    "em": ActorKind.EM,
    "cm": ActorKind.CM,
    "operational_root": ActorKind.OPERATIONAL_ROOT,
    "root": ActorKind.OPERATIONAL_ROOT,
    "portfolio": ActorKind.PORTFOLIO,
}

TECHNICAL_FORBIDDEN_PREFIXES = (
    "AGENTS.md",
    ".agents/",
    "docs/project/",
    "docs/research/workflow-runs/",
)
TECHNICAL_ALLOWED_PREFIXES = (
    "ha_ctse_process/",
    "hmasd/",
    "gnn_hmasd/",
    "manifold_hmasd/",
    "envs/",
    "experiments/",
    "tests/",
    "tools/",
    "scripts/",
)


def normalize_repo_relpath(path: str) -> str:
    text = (path or "").replace("\\", "/").strip()
    if not text:
        raise PromotionError("target must be a repository-relative path")
    if text.startswith("/") or (len(text) > 1 and text[1] == ":"):
        raise PromotionError("absolute path is forbidden")
    if any(part == ".." for part in text.split("/")):
        raise PromotionError("parent traversal is forbidden")
    return text


def resolve_inside_repo(repo_root: Path, rel: str) -> Path:
    root = Path(repo_root).resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PromotionError("target escapes repository root") from exc
    return target


def _proposal_from_row(row: Mapping[str, Any]) -> PromotionProposal:
    return PromotionProposal(
        promotion_id=str(row["promotion_id"]),
        actor_context_id=str(row["actor_context_id"]),
        epoch_id=str(row["epoch_id"]),
        promotion_kind=PromotionKind(str(row["promotion_kind"])),
        target_ref=row["target_ref"],
        summary=str(row["summary"]),
        rationale=str(row["rationale"]),
        source_refs=tuple(json.loads(row["source_refs_json"] or "[]")),
        owner_actor_context_id=str(row["owner_actor_context_id"]),
        state=PromotionState(str(row["state"])),
        disposition=json.loads(row["disposition_json"]) if row["disposition_json"] else None,
        canonical_ref=row["canonical_ref"],
        writer_actor_context_id=row["writer_actor_context_id"] if "writer_actor_context_id" in row.keys() else None,
        carried_to_epoch_id=row["carried_to_epoch_id"] if "carried_to_epoch_id" in row.keys() else None,
    )


def _actor_row(store: SemanticStore, actor_context_id: str):
    row = store.connection.execute(
        "SELECT * FROM actor_contexts WHERE actor_context_id = ?",
        (actor_context_id,),
    ).fetchone()
    if row is None:
        raise KeyError(f"unknown actor: {actor_context_id}")
    return actor_context_from_row(row)


def _actor_kind_for(store: SemanticStore, actor_context_id: str) -> ActorKind:
    return _actor_row(store, actor_context_id).actor_kind


def _workflow_id(store: SemanticStore, actor_context_id: str) -> str | None:
    workflow = store.current_actor_workflow(actor_context_id)
    return str(workflow["workflow_id"]) if workflow else None


def _procedure_owner_kind(target: str, repo_root: Path | None) -> ActorKind | None:
    if repo_root is None:
        return None
    registry_path = Path(repo_root) / "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
    if not registry_path.is_file():
        return None
    from .source_registry import load_registry

    registry = load_registry(registry_path)
    for source in registry.sources:
        if source.path.replace("\\", "/") == target:
            return REGISTRY_OWNER_KIND.get(source.owner)
    return None


def validate_promotion_target(
    store: SemanticStore,
    *,
    kind: PromotionKind,
    owner_actor_context_id: str,
    target_ref: str | None,
    repo_root: Path | None = None,
) -> str | None:
    if kind is PromotionKind.EPHEMERAL:
        if target_ref:
            raise PromotionError("EPHEMERAL target_ref must be empty")
        return None
    if not target_ref:
        if kind is PromotionKind.SHARED_ARCHITECTURE_DECISION:
            return None
        raise PromotionError("target_ref is required")
    target = normalize_repo_relpath(target_ref)
    if repo_root is not None:
        resolve_inside_repo(repo_root, target)
    owner = _actor_row(store, owner_actor_context_id)
    if kind is PromotionKind.SCIENTIFIC_ARTIFACT:
        direction = owner.direction_id or ""
        prefix = f"docs/research/candidates/{direction}/"
        if not direction or not target.startswith(prefix):
            raise PromotionError("scientific destination must match the EM direction")
    elif kind is PromotionKind.TECHNICAL_ARTIFACT:
        if target in TECHNICAL_FORBIDDEN_PREFIXES or any(
            target.startswith(prefix) for prefix in TECHNICAL_FORBIDDEN_PREFIXES
        ):
            raise PromotionError("technical destination is outside the CM assignment")
        direction = owner.direction_id or ""
        other_direction = (
            target.startswith("docs/research/candidates/")
            and direction
            and not target.startswith(f"docs/research/candidates/{direction}/")
        )
        allowed = any(target.startswith(prefix) for prefix in TECHNICAL_ALLOWED_PREFIXES)
        same_direction = bool(direction) and target.startswith(
            f"docs/research/candidates/{direction}/"
        )
        if other_direction or not (allowed or same_direction):
            raise PromotionError("technical destination is outside the CM assignment")
    elif kind is PromotionKind.PROCEDURE:
        expected = _procedure_owner_kind(target, repo_root or default_repo_root())
        if expected is not None and owner.actor_kind is not expected:
            raise PromotionError("PROCEDURE owner must match the registered procedure owner")
    return target


def create_promotion_proposal(
    store: SemanticStore,
    *,
    actor_context_id: str,
    epoch_id: str,
    promotion_kind: PromotionKind | str,
    summary: str,
    rationale: str,
    source_refs: list[str] | tuple[str, ...],
    owner_actor_context_id: str,
    target_ref: str | None = None,
    source_kind: ContextSourceKind | str = ContextSourceKind.PLAN_EPOCH,
    requester_actor_context_id: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    kind = _kind(promotion_kind)
    requester = requester_actor_context_id or owner_actor_context_id
    require_same_actor(requester, owner_actor_context_id, "promotion owner")
    require_same_actor(actor_context_id, owner_actor_context_id, "proposal actor")
    epoch = store.connection.execute(
        "SELECT epoch_id, actor_context_id, state FROM plan_epochs WHERE epoch_id = ?",
        (epoch_id,),
    ).fetchone()
    if epoch is None:
        raise KeyError(f"unknown epoch: {epoch_id}")
    if str(epoch["actor_context_id"]) != actor_context_id:
        raise PromotionError("epoch does not belong to this actor")
    if str(epoch["state"]) != "OPEN":
        raise PromotionError("epoch is not open")
    owner_kind = _actor_kind_for(store, owner_actor_context_id)
    origin = (
        source_kind
        if isinstance(source_kind, ContextSourceKind)
        else ContextSourceKind(str(source_kind))
    )
    if target_ref:
        target_ref = normalize_repo_relpath(target_ref)
    validate_promotion_owner(kind, owner_kind, target_ref, origin)
    target = validate_promotion_target(
        store,
        kind=kind,
        owner_actor_context_id=owner_actor_context_id,
        target_ref=target_ref,
        repo_root=repo_root,
    )
    now = _now()
    promotion_id = _new_id("promo")
    workflow_id = _workflow_id(store, owner_actor_context_id)
    with store._lock, store.connection:
        store.connection.execute(
            """INSERT INTO promotion_proposals (
                promotion_id, actor_context_id, epoch_id, promotion_kind, target_ref,
                summary, rationale, source_refs_json, owner_actor_context_id, state,
                disposition_json, canonical_ref, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)""",
            (
                promotion_id,
                actor_context_id,
                epoch_id,
                kind.value,
                target,
                summary,
                rationale,
                _json(list(source_refs)),
                owner_actor_context_id,
                PromotionState.PROPOSED.value,
                now,
                now,
            ),
        )
        if workflow_id:
            store._insert_obligation(
                store.connection,
                workflow_id,
                ObligationKind.PROMOTION_REVIEW_REQUIRED,
                owner_actor_context_id,
                promotion_id,
                "owner review required before promotion",
                promotion_id,
                owner_actor_context_id=owner_actor_context_id,
            )
            store._append_event(
                workflow_id,
                "OBLIGATION_OPENED",
                promotion_id,
                {"kind": ObligationKind.PROMOTION_REVIEW_REQUIRED.value},
                f"OBLIGATION_OPENED:{promotion_id}",
            )
        touch_actor_workflow(store, owner_actor_context_id)
        row = store.connection.execute(
            "SELECT * FROM promotion_proposals WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        return dict(_proposal_from_row(row).__dict__) | {"promotion_id": promotion_id}


def resolve_promotion_proposal(
    store: SemanticStore,
    *,
    promotion_id: str,
    next_state: PromotionState | str,
    disposition: Mapping[str, Any] | None = None,
    requester_actor_context_id: str | None = None,
    source_kind: ContextSourceKind | str = ContextSourceKind.ROLE_CONTRACT,
) -> dict[str, Any]:
    desired = (
        next_state if isinstance(next_state, PromotionState) else PromotionState(str(next_state))
    )
    if desired in {PromotionState.OWNER_ACCEPTED, PromotionState.OWNER_REJECTED}:
        assert_authoritative_source(source_kind, "create_owner_decision")
    origin = (
        source_kind
        if isinstance(source_kind, ContextSourceKind)
        else ContextSourceKind(str(source_kind))
    )
    if origin in FORBIDDEN_ORIGINS:
        raise PromotionError(f"{origin.value} cannot resolve promotion")
    with store._lock, store.connection:
        row = store.connection.execute(
            "SELECT * FROM promotion_proposals WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown promotion: {promotion_id}")
        owner_id = str(row["owner_actor_context_id"])
        if requester_actor_context_id is None:
            raise AuthorityError("requester_actor_context_id is required")
        require_same_actor(requester_actor_context_id, owner_id, "promotion owner")
        current = PromotionState(str(row["state"]))
        allowed = VALID_TRANSITIONS.get(current, set())
        if desired not in allowed:
            raise PromotionError(f"invalid promotion transition {current.value} -> {desired.value}")
        store.connection.execute(
            """UPDATE promotion_proposals
            SET state = ?, disposition_json = ?, updated_at = ?
            WHERE promotion_id = ?""",
            (desired.value, _json(dict(disposition or {})), _now(), promotion_id),
        )
        if desired in {PromotionState.OWNER_ACCEPTED, PromotionState.OWNER_REJECTED}:
            obligation = store.connection.execute(
                """SELECT obligation_id, workflow_id FROM obligations
                WHERE kind = ? AND subject = ? AND state = 'OPEN'""",
                (ObligationKind.PROMOTION_REVIEW_REQUIRED.value, promotion_id),
            ).fetchone()
            if obligation is not None:
                store.connection.execute(
                    """UPDATE obligations SET state = 'RESOLVED', resolution_json = ?, resolved_at = ?
                    WHERE obligation_id = ? AND state = 'OPEN'""",
                    (_json({"state": desired.value}), _now(), obligation["obligation_id"]),
                )
                store._append_event(
                    str(obligation["workflow_id"]),
                    "OBLIGATION_RESOLVED",
                    str(obligation["obligation_id"]),
                    {"state": desired.value},
                    f"OBLIGATION_RESOLVED:{obligation['obligation_id']}",
                )
        touch_actor_workflow(store, owner_id)
        updated = store.connection.execute(
            "SELECT * FROM promotion_proposals WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        return dict(_proposal_from_row(updated).__dict__)


def _canonical_scope_ok(kind: PromotionKind, canonical_ref: str) -> bool:
    path = canonical_ref.replace("\\", "/")
    if kind is PromotionKind.SHARED_ARCHITECTURE_DECISION:
        return path.startswith("docs/project/decisions/ADR-") and path.endswith(".md")
    if kind is PromotionKind.REPOSITORY_NAVIGATION:
        return path in {
            "docs/project/PROJECT_MAP.md",
            "docs/project/CURRENT_WORK.md",
        } or path.startswith("docs/project/current-work/")
    if kind is PromotionKind.PROCEDURE:
        return path.startswith(".agents/skills/") and path.endswith("/SKILL.md")
    if kind is PromotionKind.SCIENTIFIC_ARTIFACT:
        return path.startswith("docs/research/candidates/")
    if kind is PromotionKind.PORTFOLIO_ARTIFACT:
        return "PORTFOLIO" in path.upper() or path.startswith(
            "docs/research/workflow-runs/2026-08-11_five-round-research-team/"
        )
    if kind is PromotionKind.AUTHORITY_RULE:
        return path == "AGENTS.md" or path.startswith(".agents/roles/")
    if kind is PromotionKind.ROLE_CONTRACT:
        return path.startswith(".agents/roles/") and path.endswith(".md")
    if kind is PromotionKind.CURRENT_WORK_POINTER:
        return path.startswith("docs/project/CURRENT_WORK") or path.startswith(
            "docs/project/current-work/"
        )
    if kind is PromotionKind.TECHNICAL_ARTIFACT:
        return bool(path) and not Path(path).is_absolute()
    return False


def mark_promotion_applied(
    store: SemanticStore,
    *,
    promotion_id: str,
    canonical_ref: str,
    repo_root: Path | None = None,
    requester_actor_context_id: str | None = None,
    writer_actor_context_id: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else default_repo_root()
    target = normalize_repo_relpath(canonical_ref)
    resolved = resolve_inside_repo(root, target)
    if not resolved.is_file():
        raise PromotionError("canonical target file does not exist")
    with store._lock, store.connection:
        row = store.connection.execute(
            "SELECT * FROM promotion_proposals WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown promotion: {promotion_id}")
        owner_id = str(row["owner_actor_context_id"])
        requester = requester_actor_context_id or writer_actor_context_id
        if requester is None:
            raise AuthorityError("requester_actor_context_id is required")
        require_same_actor(requester, owner_id, "promotion owner")
        writer = writer_actor_context_id or requester
        require_same_actor(writer, owner_id, "authorized writer")
        current = PromotionState(str(row["state"]))
        if current is not PromotionState.OWNER_ACCEPTED:
            raise PromotionError("only OWNER_ACCEPTED promotions may be applied")
        proposed = (row["target_ref"] or "").replace("\\", "/")
        if proposed != target:
            raise PromotionError("canonical_ref must equal the proposed target_ref")
        kind = PromotionKind(str(row["promotion_kind"]))
        if not _canonical_scope_ok(kind, target):
            raise PromotionError(f"canonical_ref is outside {kind.value} scope")
        disposition = json.loads(row["disposition_json"] or "{}")
        if not disposition:
            raise PromotionError("owner disposition is required before apply")
        store.connection.execute(
            """UPDATE promotion_proposals
            SET state = ?, canonical_ref = ?, writer_actor_context_id = ?, updated_at = ?
            WHERE promotion_id = ?""",
            (PromotionState.APPLIED.value, target, writer, _now(), promotion_id),
        )
        touch_actor_workflow(store, owner_id)
        updated = store.connection.execute(
            "SELECT * FROM promotion_proposals WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        result = dict(_proposal_from_row(updated).__dict__)
        result["writer_actor_context_id"] = writer
        result["disposition_id"] = disposition.get("id") or disposition.get("owner")
        return result


def promotion_proposals_for_epoch(
    store: SemanticStore, epoch_id: str
) -> list[dict[str, Any]]:
    with store._lock:
        rows = store.connection.execute(
            """SELECT * FROM promotion_proposals WHERE epoch_id = ?
            ORDER BY created_at, promotion_id""",
            (epoch_id,),
        ).fetchall()
    return [dict(_proposal_from_row(row).__dict__) for row in rows]
