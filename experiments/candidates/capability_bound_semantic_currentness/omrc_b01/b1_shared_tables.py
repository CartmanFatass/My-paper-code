"""Canonical arm-independent raw tables for OMRC B1/B2 publication.

The builders accept frozen :class:`EpisodeTape` instances only.  No worker
summary, policy output, action difference, rate, or scientific judgement is a
valid input to this module.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
import hashlib
import json
from typing import Any, Sequence

from .addressing import (
    B1_RUN,
    B2_RUN,
    EVAL_MOTIF,
    EVAL_STOCHASTIC,
    OBJECT_ID,
    TRAIN,
)
from .contract import Action, EventKind, OPPORTUNITY_COUNT
from .tapes import EpisodeTape


SHARED_TABLES_SCHEMA = "cbsc_omrc_b01_shared_truth_tables_v1"
RUN_ORDER = {B1_RUN: 0, B2_RUN: 1}
SPLIT_ORDER = {TRAIN: 0, EVAL_STOCHASTIC: 1, EVAL_MOTIF: 2}
SCIENTIFIC_ACTION_ORDER = {
    Action.SERVE: 0,
    Action.REFRESH: 1,
    Action.SAFE_FALLBACK: 2,
}
RUN_SEEDS = {
    B1_RUN: (21101, 21121, 21143),
    B2_RUN: (21161, 21179),
}
SPLIT_EPISODE_COUNTS = {TRAIN: 384, EVAL_STOCHASTIC: 32, EVAL_MOTIF: 32}


class B1SharedTableError(ValueError):
    """A shared raw-table input is incomplete or noncanonical."""


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise B1SharedTableError("shared tables must be finite canonical JSON") from exc


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _require_sha256(name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1SharedTableError(f"{name} must be 64 lowercase hexadecimal characters")
    return value


def _validated_tapes(tapes: Sequence[EpisodeTape]) -> tuple[EpisodeTape, ...]:
    if isinstance(tapes, (str, bytes, bytearray)) or not isinstance(tapes, Sequence):
        raise B1SharedTableError("tapes must be a sequence of canonical EpisodeTape values")
    values = tuple(tapes)
    if not values or any(type(tape) is not EpisodeTape for tape in values):
        raise B1SharedTableError("tapes must contain canonical EpisodeTape values only")
    identities = [
        (tape.identity.run_name, tape.identity.seed, tape.identity.split, tape.identity.episode_id)
        for tape in values
    ]
    if len(set(identities)) != len(identities):
        raise B1SharedTableError("duplicate tape identity")
    run_names = {tape.identity.run_name for tape in values}
    if len(run_names) != 1 or not run_names <= set(RUN_ORDER):
        raise B1SharedTableError("shared tables require exactly one canonical B1 or B2 run")
    if any(tape.identity.split not in SPLIT_ORDER for tape in values):
        raise B1SharedTableError("tape split is outside the canonical publication order")
    for tape in values:
        identity = tape.identity
        if type(identity.seed) is not int or identity.seed not in RUN_SEEDS[identity.run_name]:
            raise B1SharedTableError("tape seed is outside the frozen run seed panel")
        if (
            type(identity.episode_id) is not int
            or not 0 <= identity.episode_id < SPLIT_EPISODE_COUNTS[identity.split]
        ):
            raise B1SharedTableError("tape episode_id is outside the frozen split panel")
        # Rebuild from the frozen host address space.  This prevents a caller
        # from presenting an EpisodeTape-shaped summary with altered private
        # evaluator truth while retaining valid public token bytes.
        from .host import DynamicHost

        host = DynamicHost(identity.run_name, identity.seed)
        rebuilt = (
            host.build_motif(identity.episode_id)
            if identity.split == EVAL_MOTIF
            else host.build_stochastic(identity.split, identity.episode_id)
        )
        if (
            tape.identity != rebuilt.identity
            or tape.public_tokens != rebuilt.public_tokens
            or tape.learner_tokens() != rebuilt.learner_tokens()
            or tape.generation_audit != rebuilt.generation_audit
            or tape.motif != rebuilt.motif
            or any(
                tape.evaluator().truth(index) != rebuilt.evaluator().truth(index)
                for index in range(OPPORTUNITY_COUNT)
            )
        ):
            raise B1SharedTableError("tape differs from canonical host reconstruction")
    return tuple(
        sorted(
            values,
            key=lambda tape: (
                RUN_ORDER[tape.identity.run_name],
                tape.identity.seed,
                SPLIT_ORDER[tape.identity.split],
                tape.identity.episode_id,
            ),
        )
    )


def _shared_transition_rows(
    tapes: Sequence[EpisodeTape],
    *,
    attempt_id: str,
    literal_binding_spec_sha256: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tape in tapes:
        motif = tape.motif
        for transition_index, (token, projection) in enumerate(
            zip(tape.public_tokens, tape.learner_tokens())
        ):
            packed = projection.packed
            rows.append(
                {
                    "run_order": RUN_ORDER[tape.identity.run_name],
                    "seed": tape.identity.seed,
                    "split_order": SPLIT_ORDER[tape.identity.split],
                    "object_id": OBJECT_ID,
                    "literal_binding_spec_sha256": literal_binding_spec_sha256,
                    "run_name": tape.identity.run_name,
                    "attempt_id": attempt_id,
                    "split": tape.identity.split,
                    "episode_id": tape.identity.episode_id,
                    "tape_id": tape.identity.episode_id,
                    "tape_sha256": tape.primitive_digest,
                    "motif_family": None if motif is None else motif.family,
                    "motif_receiver": None if motif is None else motif.target_receiver,
                    "motif_slot": None if motif is None else motif.presented_slot,
                    "transition_index": transition_index,
                    "opportunity_id": (
                        -1 if token.opportunity_index == 255 else token.opportunity_index
                    ),
                    "event_order_position": token.event_order_position,
                    "event_kind": int(token.event_kind),
                    "primitive_token_bytes": list(packed),
                    "primitive_token_sha256": hashlib.sha256(packed).hexdigest(),
                }
            )
    return rows


def _fraction(value: Fraction) -> dict[str, int]:
    if not isinstance(value, Fraction):
        raise B1SharedTableError("native ledger values must be exact Fraction values")
    return {"numerator": value.numerator, "denominator": value.denominator}


def _body_fields(
    prefix: str,
    body: object,
    provenance: tuple[int, int],
) -> dict[str, Any]:
    return {
        f"{prefix}_body_owner": body.issuance_owner,
        f"{prefix}_body_epoch": body.issuance_epoch,
        f"{prefix}_carrier": int(body.carrier),
        f"{prefix}_addressed_receiver": int(body.addressed_receiver),
        f"{prefix}_payload_source_receiver": (
            None
            if body.payload_source_receiver is None
            else int(body.payload_source_receiver)
        ),
        f"{prefix}_content": body.content,
        f"{prefix}_native_neutral": body.native_neutral,
        f"{prefix}_issue_opportunity": provenance[0],
        f"{prefix}_issue_event_position": provenance[1],
    }


def _presented_body_fields(body: object, provenance: tuple[int, int]) -> dict[str, Any]:
    return {
        "presented_body_owner": body.issuance_owner,
        "presented_body_epoch": body.issuance_epoch,
        "presented_body_carrier": int(body.carrier),
        "presented_body_addressed_receiver": int(body.addressed_receiver),
        "presented_body_payload_source_receiver": (
            None
            if body.payload_source_receiver is None
            else int(body.payload_source_receiver)
        ),
        "presented_body_content": body.content,
        "presented_body_native_neutral": body.native_neutral,
        "presented_body_issue_opportunity": provenance[0],
        "presented_body_issue_event_position": provenance[1],
    }


def _event_facts(tokens: Sequence[object]) -> dict[str, Any]:
    definitions = {
        "owner": (EventKind.OWNER, EventKind.NOOP_OWNER, "subject_receiver"),
        "semantic": (EventKind.SEMANTIC, EventKind.NOOP_SEMANTIC, "subject_receiver"),
        "capability": (
            EventKind.CAPABILITY,
            EventKind.NOOP_CAPABILITY,
            "carrier",
        ),
        "body": (EventKind.BODY, EventKind.NOOP_BODY, "slot"),
    }
    facts: dict[str, Any] = {}
    for family, (realized_kind, noop_kind, value_field) in definitions.items():
        matching = [
            token for token in tokens if token.event_kind in {realized_kind, noop_kind}
        ]
        if len(matching) != 1:
            raise B1SharedTableError(
                f"opportunity must contain exactly one {family} family event"
            )
        token = matching[0]
        realized = token.event_kind == realized_kind
        noun = {
            "owner": "subject",
            "semantic": "subject",
            "capability": "carrier",
            "body": "slot",
        }[family]
        facts[f"{family}_event_realized"] = realized
        facts[f"{family}_event_{noun}"] = (
            int(getattr(token, value_field)) if realized else None
        )
        facts[f"{family}_event_position"] = token.event_order_position
    return facts


def _evaluator_truth_rows(
    tapes: Sequence[EpisodeTape],
    *,
    attempt_id: str,
    literal_binding_spec_sha256: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tape in tapes:
        initial_body_tokens = tape.public_tokens[6:8]
        if tuple(token.event_kind for token in initial_body_tokens) != (
            EventKind.INIT_BODY,
            EventKind.INIT_BODY,
        ):
            raise B1SharedTableError("canonical tape preamble body rows differ")
        body_provenance = {
            token.slot: (-1, token.event_order_position) for token in initial_body_tokens
        }
        if set(body_provenance) != {0, 1}:
            raise B1SharedTableError("canonical tape preamble body coverage differs")
        last_owner_change = {0: -1, 1: -1}
        last_semantic_change = {0: -1, 1: -1}
        evaluator = tape.evaluator()
        motif = tape.motif
        for opportunity_id in range(OPPORTUNITY_COUNT):
            start = 8 + 6 * opportunity_id
            preaction_tokens = tape.public_tokens[start : start + 4]
            if len(preaction_tokens) != 4:
                raise B1SharedTableError("canonical opportunity preaction coverage differs")
            for token in preaction_tokens:
                if token.event_kind == EventKind.OWNER:
                    last_owner_change[token.subject_receiver] = opportunity_id
                elif token.event_kind == EventKind.SEMANTIC:
                    last_semantic_change[token.subject_receiver] = opportunity_id
                elif token.event_kind == EventKind.BODY:
                    body_provenance[token.slot] = (
                        opportunity_id,
                        token.event_order_position,
                    )
            truth = evaluator.truth(opportunity_id)
            state = truth.state
            decision = truth.decision
            slot_0 = state.body(type(decision.presented_slot)(0))
            slot_1 = state.body(type(decision.presented_slot)(1))
            presented = state.body(decision.presented_slot)
            target = state.receiver(decision.target_receiver)
            presented_carrier_receiver = state.carrier(
                presented.carrier
            ).permitted_receiver
            nonneutral = not presented.native_neutral
            address_match = presented.addressed_receiver is decision.target_receiver
            payload_source_match = (
                presented.payload_source_receiver is decision.target_receiver
            )
            content_match = presented.content is target.current_need
            owner_match = presented.issuance_owner == target.current_owner
            epoch_match = presented.issuance_epoch == target.current_epoch
            capability_match = (
                decision.access_mode.value == "OPEN"
                or presented_carrier_receiver is decision.target_receiver
            )
            overall_valid = bool(
                decision.request_active
                and nonneutral
                and address_match
                and payload_source_match
                and content_match
                and owner_match
                and epoch_match
                and capability_match
            )
            if overall_valid is not truth.valid:
                raise B1SharedTableError("mechanical validity predicates differ from evaluator")
            ledgers = {
                action: truth.ledger(action) for action in SCIENTIFIC_ACTION_ORDER
            }
            oracle = truth.oracle_action
            presented_issue = body_provenance[int(decision.presented_slot)]
            row = {
                "run_order": RUN_ORDER[tape.identity.run_name],
                "seed": tape.identity.seed,
                "split_order": SPLIT_ORDER[tape.identity.split],
                "object_id": OBJECT_ID,
                "literal_binding_spec_sha256": literal_binding_spec_sha256,
                "run_name": tape.identity.run_name,
                "attempt_id": attempt_id,
                "split": tape.identity.split,
                "episode_id": tape.identity.episode_id,
                "tape_id": tape.identity.episode_id,
                "tape_sha256": tape.primitive_digest,
                "opportunity_id": opportunity_id,
                "motif_family": truth.motif_family,
                "motif_receiver": None if motif is None else motif.target_receiver,
                "motif_slot": None if motif is None else motif.presented_slot,
                "motif_side": truth.motif_side,
                "designated_diagnostic_member": truth.designated_comparison,
                "target_receiver": int(decision.target_receiver),
                "presented_slot": int(decision.presented_slot),
                "current_owner_0": state.receivers[0].current_owner,
                "current_owner_1": state.receivers[1].current_owner,
                "current_epoch_0": state.receivers[0].current_epoch,
                "current_epoch_1": state.receivers[1].current_epoch,
                "current_need_0": state.receivers[0].current_need,
                "current_need_1": state.receivers[1].current_need,
                "carrier_0_receiver": int(state.carriers[0].permitted_receiver),
                "carrier_1_receiver": int(state.carriers[1].permitted_receiver),
                **_body_fields("slot_0", slot_0, body_provenance[0]),
                **_body_fields("slot_1", slot_1, body_provenance[1]),
                **_presented_body_fields(presented, presented_issue),
                "request_active": decision.request_active,
                "request_need": decision.request_need,
                "access_gated": decision.access_mode.value == "GATED",
                "presented_carrier_current_receiver": int(presented_carrier_receiver),
                "nonneutral_truth": nonneutral,
                "address_match_truth": address_match,
                "payload_source_match_truth": payload_source_match,
                "content_match_truth": content_match,
                "owner_match_truth": owner_match,
                "epoch_match_truth": epoch_match,
                "capability_match_truth": capability_match,
                "overall_valid_truth": overall_valid,
            }
            for prefix, action in (
                ("serve", Action.SERVE),
                ("refresh", Action.REFRESH),
                ("safe_fallback", Action.SAFE_FALLBACK),
            ):
                ledger = ledgers[action]
                row[f"{prefix}_decision_reward"] = _fraction(ledger.decision_reward)
                row[f"{prefix}_settlement_reward"] = _fraction(ledger.settlement_reward)
                row[f"{prefix}_total_value"] = _fraction(ledger.undiscounted_total)
            row.update(
                {
                    "oracle_action": SCIENTIFIC_ACTION_ORDER[oracle],
                    "oracle_value": _fraction(ledgers[oracle].undiscounted_total),
                    **_event_facts(preaction_tokens),
                    "presented_body_age_opportunities": (
                        opportunity_id - presented_issue[0]
                    ),
                    "last_target_owner_change_opportunity": last_owner_change[
                        int(decision.target_receiver)
                    ],
                    "last_target_semantic_change_opportunity": last_semantic_change[
                        int(decision.target_receiver)
                    ],
                }
            )
            rows.append(row)
    return rows


_INTERVENTION_FAMILY = {
    0: "OWNER_CHANGE",
    1: "SEMANTIC_CHANGE",
    2: "CAPABILITY_ACCESS",
    3: "PAYLOAD_SOURCE",
    4: "REQUEST_ACTIVE",
    5: "OWNER_BODY_ORDER",
    6: "SEMANTIC_BODY_ORDER",
    7: "RETENTION_GAP",
}


def _motif_twin_rows(tapes: Sequence[EpisodeTape]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tape in tapes:
        motif = tape.motif
        if motif is None:
            continue
        evaluator = tape.evaluator()
        pair_count = 3 if motif.family == 7 else 12
        for pair_index in range(pair_count):
            if motif.family == 7:
                base = pair_index * 8
                members = (("GAP1", base + 1), ("GAP6", base + 6))
            else:
                members = (("A", 2 * pair_index), ("B", 2 * pair_index + 1))
            for member_index, (member_role, opportunity_id) in enumerate(members):
                _, counterpart_opportunity_id = members[1 - member_index]
                truth = evaluator.truth(opportunity_id)
                if truth.motif_family != motif.family or truth.motif_side != member_role:
                    raise B1SharedTableError("motif evaluator member identity differs")
                rows.append(
                    {
                        "run_order": RUN_ORDER[tape.identity.run_name],
                        "run_name": tape.identity.run_name,
                        "seed": tape.identity.seed,
                        "tape_id": tape.identity.episode_id,
                        "motif_family": motif.family,
                        "motif_receiver": motif.target_receiver,
                        "motif_slot": motif.presented_slot,
                        "pair_id": f"{tape.identity.seed}:{tape.identity.episode_id}:{pair_index}",
                        "member_role": member_role,
                        "member_tape_id": tape.identity.episode_id,
                        "member_opportunity_id": opportunity_id,
                        "counterpart_tape_id": tape.identity.episode_id,
                        "counterpart_opportunity_id": counterpart_opportunity_id,
                        "intervention_family": _INTERVENTION_FAMILY[motif.family],
                        "intervention_side": member_role,
                        "designated_diagnostic_member": truth.designated_comparison,
                        "pair_complete": True,
                    }
                )
    return rows


_SUPPORT_SIGNATURE_FIELDS = (
    "split",
    "motif_family_or_null",
    "motif_side_or_null",
    "request_active",
    "access_gated",
    "presented_body_native_neutral",
    "address_match_truth",
    "payload_source_match_truth",
    "content_match_truth",
    "owner_match_truth",
    "epoch_match_truth",
    "capability_match_truth",
    "overall_valid_truth",
    "oracle_action",
    "presented_body_age_opportunities",
)


def _support_signature_rows(truth_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[Any, ...]] = Counter()
    identity: dict[tuple[Any, ...], tuple[int, str, int]] = {}
    for row in truth_rows:
        if row["split_order"] != SPLIT_ORDER.get(row["split"]):
            raise B1SharedTableError("truth split and split_order differ")
        signature_values = {
            "split": row["split"],
            "motif_family_or_null": row["motif_family"],
            "motif_side_or_null": row["motif_side"],
            **{name: row[name] for name in _SUPPORT_SIGNATURE_FIELDS[3:]},
        }
        signature = tuple(signature_values[name] for name in _SUPPORT_SIGNATURE_FIELDS)
        key = (row["run_order"], row["seed"], signature)
        counts[key] += 1
        identity[key] = (row["run_order"], row["run_name"], row["seed"])

    def sort_key(item: tuple[Any, ...]) -> tuple[Any, ...]:
        run_order, seed, signature = item
        normalized = tuple(-1 if value is None else value for value in signature)
        return (run_order, seed, *normalized)

    output: list[dict[str, Any]] = []
    for key in sorted(counts, key=sort_key):
        run_order, run_name, seed = identity[key]
        signature = key[2]
        output.append(
            {
                "run_order": run_order,
                "run_name": run_name,
                "seed": seed,
                "split_order": SPLIT_ORDER[signature[0]],
                **dict(zip(_SUPPORT_SIGNATURE_FIELDS, signature)),
                "support_count": counts[key],
            }
        )
    return output


def _motif_pair_support_rows(
    tapes: Sequence[EpisodeTape], motif_rows: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    run_seed = sorted(
        {
            (RUN_ORDER[tape.identity.run_name], tape.identity.run_name, tape.identity.seed)
            for tape in tapes
        }
    )
    pair_members: Counter[tuple[int, int, int, str]] = Counter(
        (
            row["run_order"],
            row["seed"],
            row["motif_family"],
            row["pair_id"],
        )
        for row in motif_rows
    )
    output: list[dict[str, Any]] = []
    for run_order, run_name, seed in run_seed:
        for family in range(8):
            expected = 12 if family == 7 else 48
            relevant = {
                pair_id: count
                for (candidate_run, candidate_seed, candidate_family, pair_id), count
                in pair_members.items()
                if (candidate_run, candidate_seed, candidate_family)
                == (run_order, seed, family)
            }
            complete = sum(count == 2 for count in relevant.values())
            duplicate = sum(max(0, count - 2) for count in relevant.values())
            output.append(
                {
                    "run_order": run_order,
                    "run_name": run_name,
                    "seed": seed,
                    "motif_family": family,
                    "expected_pair_count": expected,
                    "complete_pair_count": complete,
                    "missing_pair_count": expected - complete,
                    "duplicate_member_count": duplicate,
                }
            )
    return output


def build_b1_shared_truth_tables(
    tapes: Sequence[EpisodeTape],
    *,
    attempt_id: str,
    literal_binding_spec_sha256: str,
) -> dict[str, Any]:
    """Build sorted arm/checkpoint-independent rows from canonical host tapes."""

    canonical_tapes = _validated_tapes(tapes)
    if type(attempt_id) is not str or not attempt_id:
        raise B1SharedTableError("attempt_id must be a nonempty string")
    spec_sha256 = _require_sha256(
        "literal_binding_spec_sha256", literal_binding_spec_sha256
    )
    transitions = _shared_transition_rows(
        canonical_tapes,
        attempt_id=attempt_id,
        literal_binding_spec_sha256=spec_sha256,
    )
    truth_rows = _evaluator_truth_rows(
        canonical_tapes,
        attempt_id=attempt_id,
        literal_binding_spec_sha256=spec_sha256,
    )
    motif_rows = _motif_twin_rows(canonical_tapes)
    support_rows = _support_signature_rows(truth_rows)
    pair_support_rows = _motif_pair_support_rows(canonical_tapes, motif_rows)
    tables: dict[str, list[dict[str, Any]]] = {
        "shared_tape_transitions": transitions,
        "evaluator_decision_truth": truth_rows,
        "motif_twin_index": motif_rows,
        "support_signature_counts": support_rows,
        "motif_pair_support_counts": pair_support_rows,
    }
    return {
        "schema": SHARED_TABLES_SCHEMA,
        "object_id": OBJECT_ID,
        "literal_binding_spec_sha256": spec_sha256,
        "run_name": canonical_tapes[0].identity.run_name,
        "attempt_id": attempt_id,
        **tables,
        "table_counts": {name: len(rows) for name, rows in tables.items()},
        "table_sha256": {name: _sha256_json(rows) for name, rows in tables.items()},
    }


__all__ = [
    "B1SharedTableError",
    "RUN_ORDER",
    "RUN_SEEDS",
    "SHARED_TABLES_SCHEMA",
    "SPLIT_ORDER",
    "build_b1_shared_truth_tables",
]
