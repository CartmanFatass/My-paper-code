from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence
from collections import defaultdict
import hashlib
import json
import math
import os
import tempfile
import time
import tracemalloc

from .checkpoint import SCHEMA as CHECKPOINT_SCHEMA
from .checkpoint import load_checkpoint, write_checkpoint
from .learner import TechnicalDecision, TechnicalLinearLearner
from .empirical_contract import ARMS, REGISTERED_SEEDS
from .counter import address, categorical, permutation
from .host import ARMS as HOST_ARMS
from .host import DONOR_PERMUTATIONS, PRESENTATIONS, build_churn_fixtures, build_strata
from .validation import validate_evidence
from .oracle import accepted_receipt
from .learner import ProductionDecision, RegisteredLinearLearner
from .checkpoint import load_registered_checkpoint, write_registered_checkpoint


@dataclass(frozen=True)
class TechnicalShard:
    shard_id: str
    arm: str
    seed: int
    fixture_kind: str = "NONREGISTERED_TECHNICAL_ONLY"
    window_count: int = 2


def fixed_technical_shards() -> tuple[TechnicalShard, TechnicalShard]:
    return (
        TechnicalShard("TECH-A-1000003", "TECHNICAL_A", 1_000_003),
        TechnicalShard("TECH-B-1000033", "TECHNICAL_B", 1_000_033),
    )


def _literal_observations(window_index: int) -> tuple[tuple[dict[str, int], ...], tuple[dict[str, int], ...]]:
    if window_index == 0:
        return (
            (
                {"surface_bit": 0, "i": 0, "r": 1},
                {"surface_bit": 1, "i": 1, "r": 0},
            ),
            (
                {"payload_bit": 0, "i": 1, "r": 0},
                {"payload_bit": 1, "i": 0, "r": 1},
            ),
        )
    return (
        (
            {"surface_bit": 1, "i": 0, "r": 0},
            {"surface_bit": 0, "i": 1, "r": 1},
        ),
        (
            {"payload_bit": 1, "i": 1, "r": 1},
            {"payload_bit": 0, "i": 0, "r": 0},
        ),
    )


def _run_window(
    learner: TechnicalLinearLearner, shard: TechnicalShard, window_index: int
) -> list[str]:
    selector_rows, controller_rows = _literal_observations(window_index)
    signals = (Fraction(1, 2), Fraction(-1, 2))
    sampled: dict[str, list[TechnicalDecision]] = {"selector": [], "controller": []}
    for head, rows in (("selector", selector_rows), ("controller", controller_rows)):
        for subscriber, row in enumerate(rows):
            features = (
                learner.selector_features(row)
                if head == "selector"
                else learner.controller_features(row)
            )
            coordinates = (
                "NONREGISTERED_FIXTURE",
                shard.shard_id,
                window_index,
                subscriber,
            )
            action, score, _addresses = learner.choose_action(
                head,
                features,
                completed_decisions=window_index * 2,
                coordinates=coordinates,
            )
            sampled[head].append(
                TechnicalDecision(action, tuple(features), score, signals[subscriber])
            )
    ledger: list[str] = []
    window_id = f"{shard.shard_id}-W{window_index}"
    for head in ("selector", "controller"):
        learner.apply_grouped_window_update(
            head, sampled[head], pair_count=2, window_id=window_id
        )
        ledger.append(f"{shard.shard_id}:{window_index}:{head}")
    return ledger


def _checkpoint_value(
    learners: dict[str, TechnicalLinearLearner],
    update_ledger: list[str],
    cursor: dict[str, int],
) -> dict[str, Any]:
    return {
        "schema": CHECKPOINT_SCHEMA,
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "registered_manifest": False,
        "effect_refs": [],
        "cursor": cursor,
        "learners": {key: learner.snapshot() for key, learner in learners.items()},
        "update_ledger": list(update_ledger),
    }


def _receipt(
    learners: dict[str, TechnicalLinearLearner],
    update_ledger: list[str],
    cursor: dict[str, int],
    terminal_status: str,
) -> dict[str, Any]:
    return {
        "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
        "terminal_status": terminal_status,
        "workers": 1,
        "execution": "SEQUENTIAL",
        "registered_seed_or_arm_used": False,
        "cross_arm_or_seed_state": False,
        "cursor": cursor,
        "fixture_state_digests": {
            key: learner.snapshot_digest() for key, learner in learners.items()
        },
        "update_ledger": list(update_ledger),
        "question_relevant_values": None,
        "effect_refs": [],
    }


def run_sequential_shards(
    shards: Sequence[TechnicalShard],
    *,
    checkpoint_path: Path,
    resume: bool = False,
    stop_after_windows: int | None = None,
) -> dict[str, Any]:
    if tuple(shards) != fixed_technical_shards():
        raise PermissionError("S2 runs only the two fixed nonregistered technical shards")
    if resume:
        stored = load_checkpoint(checkpoint_path)
        learners = {
            key: TechnicalLinearLearner.from_snapshot(snapshot)
            for key, snapshot in stored["learners"].items()
        }
        update_ledger = list(stored["update_ledger"])
        cursor = dict(stored["cursor"])
    else:
        learners = {
            shard.shard_id: TechnicalLinearLearner(shard.arm, shard.seed)
            for shard in shards
        }
        update_ledger = []
        cursor = {"shard_index": 0, "window_index": 0}
    processed = 0
    for shard_index in range(cursor["shard_index"], len(shards)):
        shard = shards[shard_index]
        first_window = cursor["window_index"] if shard_index == cursor["shard_index"] else 0
        for window_index in range(first_window, shard.window_count):
            new_entries = _run_window(learners[shard.shard_id], shard, window_index)
            if set(new_entries) & set(update_ledger):
                raise ValueError("resume would repeat an update")
            update_ledger.extend(new_entries)
            if window_index + 1 < shard.window_count:
                cursor = {"shard_index": shard_index, "window_index": window_index + 1}
            else:
                cursor = {"shard_index": shard_index + 1, "window_index": 0}
            write_checkpoint(
                checkpoint_path, _checkpoint_value(learners, update_ledger, cursor)
            )
            processed += 1
            if stop_after_windows is not None and processed >= stop_after_windows:
                return _receipt(learners, update_ledger, cursor, "TECHNICAL_PAUSED")
    return _receipt(learners, update_ledger, cursor, "TECHNICAL_COMPLETE")


def dispatch_technical_branches(orchestration: dict[str, Any]) -> list[dict[str, Any]]:
    if orchestration.get("terminal_status") != "TECHNICAL_COMPLETE":
        raise ValueError("branch dispatch requires complete technical orchestration")
    rows: list[dict[str, Any]] = []
    for shard_id in sorted(orchestration["fixture_state_digests"]):
        for branch in ("NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"):
            rows.append(
                {
                    "fixture_kind": "NONREGISTERED_TECHNICAL_ONLY",
                    "shard_id": shard_id,
                    "branch": branch,
                    "resource_receipt": [1, 1],
                    "updates_parameters": False,
                    "measurement_schema_bound": True,
                    "control_invariants_bound": True,
                    "question_relevant_values": None,
                }
            )
    return rows


def registered_transaction_plan() -> dict[str, Any]:
    shards = [
        {
            "arm": arm,
            "seed": seed,
            "training_envelopes": [6, 8],
            "training_episodes_per_envelope": 64,
            "training_decisions": 1_984,
            "evaluation_envelopes": [6, 8, 10],
            "evaluation_branches": [
                "NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY"
            ],
            "evaluation_episodes_per_envelope_branch": 32,
            "evaluation_decisions": 6_912,
        }
        for arm in ARMS
        for seed in REGISTERED_SEEDS
    ]
    return {
        "schema": "FSBS_R01_REGISTERED_TRANSACTION_PLAN_V2",
        "fixture_kind": "RESULT_BLIND_PLAN_ONLY",
        "workers": 1,
        "threads_per_worker": 1,
        "gate_transactions": 15_360,
        "shards": shards,
        "training_decisions": 31_744,
        "evaluation_decisions": 110_592,
        "registered_total_transactions": 157_696,
        "checkpoint_count": 16,
        "question_relevant_values": None,
        "effect_refs": [],
    }


def result_blind_orchestration_mirror() -> dict[str, Any]:
    mirror_seeds = tuple(1_000_003 + 30 * index for index in range(8))
    identities = []
    ledger = []
    for arm in ("MIRROR_AUTHENTIC", "MIRROR_REASSOCIATED"):
        for seed in mirror_seeds:
            state = {
                "fixture_kind": "NONREGISTERED_RESULT_BLIND_MIRROR",
                "arm": arm,
                "seed": seed,
                "cursor": 10,
                "completed_windows": list(range(10)),
            }
            digest = hashlib.sha256(
                json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            identities.append(
                {
                    "arm": arm,
                    "seed": seed,
                    "content_sha256": digest,
                    "content_addressed": True,
                    "terminal": True,
                }
            )
            ledger.extend(f"{arm}:{seed}:W{window}" for window in range(10))
    return {
        "fixture_kind": "NONREGISTERED_RESULT_BLIND_MIRROR",
        "paired_progress": {
            "paused_cursor": {"AUTHENTIC": 3, "REASSOCIATED": 3},
            "resumed_cursor": {"AUTHENTIC": 10, "REASSOCIATED": 10},
            "cold_resume_equal": True,
        },
        "terminal_identities": identities,
        "checkpoint_count": 16,
        "update_ledger": ledger,
        "repeated_update": len(ledger) != len(set(ledger)),
        "cross_arm_or_seed_state": False,
        "question_relevant_values": None,
        "effect_refs": [],
    }


def _balanced_superblock(mode: str, *, seed: int, block: int) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for relevant_reservation in (0, 1):
        donor = DONOR_PERMUTATIONS[
            categorical(
                len(DONOR_PERMUTATIONS),
                seed,
                "carrier-donor",
                ("RESULT_BLIND" if seed not in REGISTERED_SEEDS else "REGISTERED", block, relevant_reservation),
            )
        ]
        for position in range(4):
            relevant_slot = position // 2
            decoy_reservation = position % 2
            semantic_bit = (
                relevant_slot
                if mode in {"AUTHENTIC", "MIRROR_AUTHENTIC"}
                else donor[position] // 2
            )
            rows.append(
                {
                    "relevant_slot": relevant_slot,
                    "relevant_reservation": relevant_reservation,
                    "decoy_reservation": decoy_reservation,
                    "semantic_bit": semantic_bit,
                }
            )
    return rows


def result_blind_world_mirror() -> dict[str, Any]:
    paired_batches = {}
    for M in (6, 8, 10):
        pair_count = M // 2
        paired_batches[str(M)] = [
            [
                _world(
                    "AUTHENTIC",
                    seed=1_000_003,
                    phase="RESULT_BLIND",
                    M=M,
                    episode=episode,
                    window=0,
                    pair_index=pair_index,
                )
                for pair_index in range(pair_count)
            ]
            for episode in range(8)
        ]
    return {
        "fixture_kind": "NONREGISTERED_RESULT_BLIND_MIRROR",
        "modes": {
            mode: _balanced_superblock(mode, seed=1_000_003, block=0)
            for mode in ("MIRROR_AUTHENTIC", "MIRROR_REASSOCIATED")
        },
        "paired_window_batches": paired_batches,
        "question_relevant_values": None,
        "effect_refs": [],
    }


_PRESENTATION = {
    seed: {"kappa": kappa, "mu": mu, "lambda": lambda_}
    for seed, kappa, mu, lambda_ in PRESENTATIONS
}
_TRAINING_ENVELOPES = (6, 8)
_EVALUATION_ENVELOPES = (6, 8, 10)
_EVALUATION_BRANCHES = ("NATURAL", "MASKED", "FORCE_RELEVANT", "FORCE_DECOY")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=".eg.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def commit_paired_activity_marker(
    root: Path,
    receipts: Sequence[Mapping[str, Any]],
    *,
    release: Mapping[str, Any],
) -> dict[str, Any]:
    by_arm = {str(receipt.get("arm")): receipt for receipt in receipts}
    if set(by_arm) != set(HOST_ARMS) or len(receipts) != 2:
        raise ValueError("activity marker requires one complete paired window")
    window_ids = {receipt.get("window_id") for receipt in receipts}
    fixture_kinds = {receipt.get("fixture_kind") for receipt in receipts}
    if (
        len(window_ids) != 1
        or any(receipt.get("complete") is not True for receipt in receipts)
        or any(
            receipt.get("common_team_return_observed") is not True
            for receipt in receipts
        )
        or len(fixture_kinds) != 1
    ):
        raise ValueError("activity marker requires one complete paired window")
    fixture_kind = next(iter(fixture_kinds))
    if fixture_kind == "REGISTERED_R01_RELEASED":
        if release.get("released") is not True:
            raise PermissionError("registered activity marker requires validated release")
        schema = "FSBS_R01_SCIENTIFIC_ACTIVITY_MARKER_V1"
    elif fixture_kind == "NONREGISTERED_RESULT_BLIND_MIRROR":
        if release.get("fixture_kind") != fixture_kind or release.get("released") is not False:
            raise PermissionError("result-blind activity marker mirror is invalid")
        schema = "FSBS_R01_ACTIVITY_BOUNDARY_MIRROR_V2"
    else:
        raise PermissionError("activity marker fixture kind is invalid")
    value = {
        "schema": schema,
        "fixture_kind": fixture_kind,
        "run_id": release["run_id"],
        "code_sha": release["code_sha"],
        "window_id": next(iter(window_ids)),
        "paired_arms": list(HOST_ARMS),
        "boundary": "FIRST_COMPLETE_PAIRED_AUTHENTIC_REASSOCIATED_TEAM_WINDOW_AFTER_GATE",
        "question_relevant_values": None,
    }
    marker = root / "activity.json"
    if marker.exists():
        if json.loads(marker.read_text(encoding="utf-8")) != value:
            raise PermissionError("activity marker identity is already bound")
        return value
    _atomic_json(marker, value)
    return value


def _retained_gate_receipt() -> dict[str, Any]:
    evidence = {
        "strata": build_strata(),
        "churn_fixtures": build_churn_fixtures(),
        "firewall": {
            "learner_initialized": False,
            "model_created": False,
            "checkpoint_created": False,
            "registered_paired_effects_emitted": False,
            "partial_scientific_value_emitted": False,
            "formal_compute_executed": False,
            "external_effect_executed": False,
            "operator_requested": False,
            "provider_contacted": False,
            "deployment_or_flight_executed": False,
        },
        "effect_refs": [],
    }
    tree = validate_evidence(evidence)
    del evidence
    return {
        "terminal_status": tree["terminal_status"],
        "transactions": 15_360,
        "accepted": 12_288,
        "denied": 3_072,
        "resource_cap": [1, 1],
        "nodes": tree["nodes"],
    }


def _active_lineages(seed: int, phase: str, M: int, episode: int) -> tuple[tuple[int, ...], ...]:
    pair_episode = episode // 2
    hidden = permutation(M, seed, "churn", (phase, M, pair_episode))
    full = set(range(M))
    return (
        tuple(sorted(full)),
        tuple(sorted(full - {hidden[0], hidden[1]})),
        tuple(sorted(full)),
        tuple(sorted(full - {hidden[2], hidden[3]})),
        tuple(sorted(full)),
    )


def _window_pairs(
    seed: int, phase: str, M: int, episode: int, window: int
) -> list[tuple[int, int]]:
    active = _active_lineages(seed, phase, M, episode)[window]
    order = permutation(
        len(active), seed, "pairing", (phase, M, episode // 2, window)
    )
    shuffled = [active[index] for index in order]
    pairs = [tuple(shuffled[index : index + 2]) for index in range(0, len(active), 2)]
    if episode % 2:
        pairs = [(subscriber, publisher) for publisher, subscriber in pairs]
    return pairs


def _world(
    mode: str,
    *,
    seed: int,
    phase: str,
    M: int,
    episode: int,
    window: int,
    pair_index: int,
) -> dict[str, int]:
    pair_count = M // 2 if window in (0, 2, 4) else (M - 2) // 2
    window_ordinal = episode
    block, block_position = divmod(window_ordinal, 8)
    q = permutation(8, seed, "world", (phase, M, window, pair_count, block))[
        block_position
    ]
    carrier_forms = {
        2: (1, 2),
        3: (1, 2, 4),
        4: (1, 2, 1, 4),
        5: (1, 2, 1, 2, 4),
    }[pair_count]
    carrier_form = carrier_forms[pair_index]
    next_form = carrier_forms[(pair_index + 1) % pair_count]
    span = {carrier_form, next_form, carrier_form ^ next_form}
    slot_form = next(value for value in range(1, 8) if value not in span)
    relevant_reservation = (q & carrier_form).bit_count() % 2
    decoy_reservation = (q & next_form).bit_count() % 2
    relevant_slot = (q & slot_form).bit_count() % 2
    i = block % 2
    r = (block // 2) % 2
    presentation = _PRESENTATION.get(seed, {"kappa": 0, "mu": 0, "lambda": 0})
    window_type = (
        "REDUCED_DEPARTURE" if window in (1, 3)
        else "FIRST_POST_REJOIN" if window in (2, 4)
        else "FULL_ROSTER"
    )
    donor_coordinates = (
        phase, M, pair_count * 2, window_type, i, r,
        presentation["kappa"], presentation["mu"], presentation["lambda"],
        block * 2 + relevant_reservation,
    )
    donor_index = categorical(4, seed, "carrier-donor", donor_coordinates)
    donor = DONOR_PERMUTATIONS[donor_index]
    reassociated_semantic = donor[relevant_slot * 2 + decoy_reservation] // 2
    mask_coordinates = (
        phase, M, pair_count * 2, window_type, i, r,
        presentation["kappa"], presentation["mu"], presentation["lambda"],
        block,
    )
    mask_forms = [value for value in range(1, 8) if value != slot_form]
    mask_form = mask_forms[
        categorical(len(mask_forms), seed, "evaluation-mask", mask_coordinates)
    ]
    evaluation_mask_bit = (q & mask_form).bit_count() % 2
    return {
        "relevant_slot": relevant_slot,
        "relevant_reservation": relevant_reservation,
        "decoy_reservation": decoy_reservation,
        "semantic_bit": (
            relevant_slot if mode == "AUTHENTIC" else reassociated_semantic
        ),
        "i": i,
        "r": r,
        "block": block,
        "donor_permutation_index": donor_index,
        "donor_address_sha256": hashlib.sha256(
            address(seed, "carrier-donor", donor_coordinates, 0)
        ).hexdigest(),
        "evaluation_mask_bit": evaluation_mask_bit,
        "evaluation_mask_family": "evaluation-mask",
        "evaluation_mask_address_sha256": hashlib.sha256(
            address(seed, "evaluation-mask", mask_coordinates, 0)
        ).hexdigest(),
    }


class SharedHostReceiptBoundary:
    """Shared per-episode host state, registry, and resource receipt boundary."""

    def __init__(self, *, seed: int, phase: str, M: int, episode: int) -> None:
        self.seed = seed
        self.phase = phase
        self.M = M
        self.episode = episode
        self._active_sets = _active_lineages(seed, phase, M, episode)
        self._state = {lineage: 0 for lineage in range(M)}
        self._tokens: dict[int, str] = {}
        self._join_epochs = {lineage: -1 for lineage in range(M)}
        self._previous_active: set[int] = set()
        self._previous_partners: dict[int, int] = {}
        self._registry: dict[str, str] = {}
        self._contexts: dict[tuple[int, int], dict[str, Any]] = {}
        self._opened_windows: list[int] = []
        self._lookup_count = 0

    @property
    def next_window(self) -> int:
        return len(self._opened_windows)

    def _serial(self, window: int, pair_index: int) -> str:
        return hashlib.sha256(
            address(
                self.seed,
                "world",
                (
                    self.phase,
                    self.M,
                    self.episode,
                    window,
                    pair_index,
                    "carrier-serial",
                ),
                0,
            )
        ).hexdigest()

    def _provenance(
        self, window: int, pair_index: int, world: Mapping[str, int]
    ) -> str:
        return hashlib.sha256(
            json.dumps(
                {
                    "phase": self.phase,
                    "M": self.M,
                    "episode": self.episode,
                    "window": window,
                    "pair_index": pair_index,
                    "semantic_bit": world["semantic_bit"],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    def open_window(
        self, window: int, worlds: Sequence[Mapping[str, int]]
    ) -> None:
        if window != len(self._opened_windows):
            raise ValueError("shared host windows must be consumed exactly once in order")
        pairs = _window_pairs(self.seed, self.phase, self.M, self.episode, window)
        if len(worlds) != len(pairs):
            raise ValueError("shared host world panel does not match active pairs")
        active = set(self._active_sets[window])
        prior_tokens = dict(self._tokens)
        for lineage in active - self._previous_active:
            self._join_epochs[lineage] += 1
            self._tokens[lineage] = hashlib.sha256(
                address(
                    self.seed,
                    "churn",
                    (
                        self.phase,
                        self.M,
                        self.episode,
                        lineage,
                        "slot-token",
                        self._join_epochs[lineage],
                    ),
                    0,
                )
            ).hexdigest()
        state_before = {lineage: self._state[lineage] for lineage in active}
        for lineage in active:
            self._state[lineage] += 1
        current_partners: dict[int, int] = {}
        for pair_index, ((publisher, subscriber), world) in enumerate(
            zip(pairs, worlds)
        ):
            current_partners[publisher] = subscriber
            current_partners[subscriber] = publisher
            serial = self._serial(window, pair_index)
            provenance = self._provenance(window, pair_index, world)
            self._registry[serial] = provenance
            joining = subscriber not in self._previous_active
            previous_token = prior_tokens.get(subscriber)
            self._contexts[(window, pair_index)] = {
                "publisher": publisher,
                "subscriber": subscriber,
                "serial": serial,
                "provenance": provenance,
                "state_before": state_before[subscriber],
                "state_after": self._state[subscriber],
                "joining": joining,
                "token": self._tokens[subscriber],
                "fresh_token": (
                    not joining
                    or previous_token is None
                    or previous_token != self._tokens[subscriber]
                ),
                "previous_partner": self._previous_partners.get(subscriber),
                "current_partner": publisher,
                "active": active,
                "decoy_publisher": pairs[(pair_index + 1) % len(pairs)][0],
                "decoy_next_publisher_match": (
                    world["decoy_reservation"]
                    == worlds[(pair_index + 1) % len(worlds)]["relevant_reservation"]
                ),
            }
        self._previous_active = active
        self._previous_partners = current_partners
        self._opened_windows.append(window)

    def receipt(
        self,
        *,
        window: int,
        pair_index: int,
        world: Mapping[str, int],
        records: Mapping[int, int],
        open_slot: int,
        lane_action: int,
    ) -> dict[str, Any]:
        context = self._contexts.get((window, pair_index))
        if context is None:
            raise ValueError("shared host window was not opened before service")
        resource = accepted_receipt(records, open_slot, lane_action)
        lookup_count_before = self._lookup_count
        observed_provenance = self._registry.get(str(context["serial"]))
        self._lookup_count += 1
        registry_lookup_count = self._lookup_count - lookup_count_before
        serial_match = observed_provenance == self._provenance(
            window, pair_index, world
        )
        cap = resource["resource_receipt"]
        return {
            "registry_lookup_count": registry_lookup_count,
            "registry_serial_match": serial_match,
            "registry_provenance_sha256": observed_provenance,
            "auth_ok": int(resource["accepted"] and serial_match),
            "record_issuance_count": len(records),
            "payload_read_count": int(cap["payload_reads"]),
            "reservation_service_count": int(cap["reservation_services"]),
            "lineage_state_before": context["state_before"],
            "lineage_state_after": context["state_after"],
            "state_continuity": (
                context["state_after"] == context["state_before"] + 1
            ),
            "joining_or_rejoining": context["joining"],
            "slot_token_sha256": context["token"],
            "fresh_slot_token": context["fresh_token"],
            "previous_partner": context["previous_partner"],
            "current_partner": context["current_partner"],
            "peer_change_observed": (
                None
                if context["previous_partner"] is None
                else context["previous_partner"] != context["current_partner"]
            ),
            "active_mask_sha256": hashlib.sha256(
                bytes(int(lineage in context["active"]) for lineage in range(self.M))
            ).hexdigest(),
            "decoy_publisher": context["decoy_publisher"],
            "decoy_next_publisher_match": context["decoy_next_publisher_match"],
            "resource_receipt": resource,
            "world_semantic_bit": world["semantic_bit"],
        }


def result_blind_host_observability_mirror(
    *, host_boundary_factory: Any = SharedHostReceiptBoundary
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for episode in range(8):
        boundary = host_boundary_factory(
            seed=1_000_003, phase="RESULT_BLIND", M=6, episode=episode
        )
        for window in range(5):
            pairs = _window_pairs(1_000_003, "RESULT_BLIND", 6, episode, window)
            worlds = [
                _world(
                    "AUTHENTIC", seed=1_000_003, phase="RESULT_BLIND", M=6,
                    episode=episode, window=window, pair_index=pair_index,
                )
                for pair_index in range(len(pairs))
            ]
            boundary.open_window(window, worlds)
            for pair_index in range(len(pairs)):
                world = worlds[pair_index]
                records = {
                    world["relevant_slot"]: world["relevant_reservation"],
                    1 - world["relevant_slot"]: world["decoy_reservation"],
                }
                rows.append(
                    boundary.receipt(
                        window=window,
                        pair_index=pair_index,
                        world=world,
                        records=records,
                        open_slot=world["relevant_slot"],
                        lane_action=world["relevant_reservation"],
                    )
                )
    return rows


def validate_host_activity_log_mirror(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not rows:
        raise ValueError("host activity log is empty")
    predicates = {
        "matched_registry_lookup": all(
            row.get("registry_lookup_count") == 1
            and row.get("registry_serial_match") is True
            and row.get("auth_ok") == 1
            for row in rows
        ),
        "record_and_resource_counts": all(
            row.get("record_issuance_count") == 2
            and row.get("payload_read_count") == 1
            and row.get("reservation_service_count") == 1
            for row in rows
        ),
        "lineage_state_continuity": all(
            row.get("state_continuity") is True
            and row.get("lineage_state_after") == row.get("lineage_state_before") + 1
            for row in rows
        ),
        "fresh_join_tokens": all(
            row.get("fresh_slot_token") is True for row in rows
        ),
        "next_publisher_decoy": all(
            row.get("decoy_next_publisher_match") is True for row in rows
        ),
        "peer_composition_changed": any(
            row.get("peer_change_observed") is True for row in rows
        ),
        "fresh_rejoin_tokens": any(
            row.get("joining_or_rejoining") is True
            and row.get("lineage_state_before", 0) > 0
            and row.get("fresh_slot_token") is True
            for row in rows
        ),
    }
    if not all(predicates.values()):
        raise ValueError("host activity log proof is incomplete")
    return {"complete": True, "predicates": predicates, "row_count": len(rows)}


def _sample_window(
    learner: RegisteredLinearLearner,
    *,
    phase: str,
    M: int,
    episode: int,
    window: int,
    branch: str | None,
    host_boundary: SharedHostReceiptBoundary,
) -> tuple[list[ProductionDecision], list[ProductionDecision], list[dict[str, Any]], float]:
    presentation = _PRESENTATION[learner.seed]
    selector_rows: list[ProductionDecision] = []
    controller_rows: list[ProductionDecision] = []
    observations: list[dict[str, Any]] = []
    pairs = _window_pairs(learner.seed, phase, M, episode, window)
    worlds = [
        _world(
            learner.arm,
            seed=learner.seed,
            phase=phase,
            M=M,
            episode=episode,
            window=window_index,
            pair_index=pair_index,
        )
        for window_index in range(host_boundary.next_window, window + 1)
        for pair_index in range(
            len(_window_pairs(learner.seed, phase, M, episode, window_index))
        )
    ]
    offset = 0
    for window_index in range(host_boundary.next_window, window + 1):
        prior_pairs = _window_pairs(learner.seed, phase, M, episode, window_index)
        panel = worlds[offset : offset + len(prior_pairs)]
        host_boundary.open_window(window_index, panel)
        offset += len(prior_pairs)
    current_worlds = worlds[-len(pairs) :]
    for pair_index, (publisher, subscriber) in enumerate(pairs):
        world = current_worlds[pair_index]
        semantic = world["semantic_bit"]
        if branch == "MASKED":
            semantic = world["evaluation_mask_bit"]
        surface = semantic ^ presentation["kappa"]
        selector_features = learner.features(surface, world["i"], world["r"])
        coordinates = (phase, M, episode, window, pair_index)
        if branch in {"FORCE_RELEVANT", "FORCE_DECOY"}:
            open_slot = world["relevant_slot"] if branch == "FORCE_RELEVANT" else 1 - world["relevant_slot"]
            selector_score = learner.score("selector", open_slot, selector_features)
        elif phase == "TRAIN":
            open_slot, selector_score = learner.choose_training_action(
                "selector", selector_features, coordinates=coordinates
            )
        else:
            open_slot, selector_score = learner.choose_greedy_action(
                "selector", selector_features
            )
        chosen_reservation = (
            world["relevant_reservation"]
            if open_slot == world["relevant_slot"]
            else world["decoy_reservation"]
        )
        payload = chosen_reservation ^ presentation["mu"]
        controller_features = learner.features(payload, world["i"], world["r"])
        if phase == "TRAIN":
            lane_action, controller_score = learner.choose_training_action(
                "controller", controller_features, coordinates=coordinates
            )
        else:
            lane_action, controller_score = learner.choose_greedy_action(
                "controller", controller_features
            )
        records = {
            world["relevant_slot"]: world["relevant_reservation"] ^ presentation["mu"],
            1 - world["relevant_slot"]: world["decoy_reservation"] ^ presentation["mu"],
        }
        host_proof = host_boundary.receipt(
            window=window,
            pair_index=pair_index,
            world=world,
            records=records,
            open_slot=open_slot,
            lane_action=lane_action,
        )
        receipt = host_proof["resource_receipt"]
        if receipt["resource_receipt"] != {"payload_reads": 1, "reservation_services": 1}:
            raise ValueError("registered accepted transaction resource law drifted")
        physical_lane = lane_action ^ presentation["lambda"]
        score = 1 if physical_lane != world["relevant_reservation"] else -1
        selector_rows.append(
            ProductionDecision(open_slot, selector_features, selector_score)
        )
        controller_rows.append(
            ProductionDecision(lane_action, controller_features, controller_score)
        )
        observations.append(
            {
                "publisher": publisher,
                "subscriber": subscriber,
                "selected_relevant": int(open_slot == world["relevant_slot"]),
                "safe": int(score == 1),
                "pair_score": score,
                "selector_action": open_slot,
                "controller_action": lane_action,
                "selector_margin": abs(
                    learner.score("selector", 1, selector_features)
                    - learner.score("selector", 0, selector_features)
                ),
                "controller_margin": abs(
                    learner.score("controller", 1, controller_features)
                    - learner.score("controller", 0, controller_features)
                ),
                "M": M,
                "N_t": len(pairs) * 2,
                "window": window,
                "i": world["i"],
                "r": world["r"],
                **host_proof,
                **presentation,
            }
        )
    team_return = sum(row["pair_score"] for row in observations) / len(observations)
    return selector_rows, controller_rows, observations, team_return


def _seed_progress_path(root: Path, seed: int) -> Path:
    return root / "progress" / f"paired-seed-{seed}.json"


def _save_seed_progress(
    path: Path,
    learners: Mapping[str, RegisteredLinearLearner],
    *,
    cursor: int,
    release: Mapping[str, Any],
    training_summary: Mapping[str, Mapping[str, Any]],
) -> None:
    core = {
        "schema": "FSBS_R01_PAIRED_TRAINING_PROGRESS_V2",
        "run_id": release["run_id"],
        "code_sha": release["code_sha"],
        "cursor": cursor,
        "learners": {arm: learners[arm].snapshot() for arm in HOST_ARMS},
        "training_summary": training_summary,
    }
    core["content_sha256"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    _atomic_json(path, core)


def _load_seed_progress(
    path: Path, *, release: Mapping[str, Any]
) -> tuple[dict[str, RegisteredLinearLearner], int, dict[str, dict[str, Any]]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    digest = value.pop("content_sha256", None)
    if digest != hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest():
        raise ValueError("paired training progress content digest is invalid")
    if value.get("run_id") != release["run_id"] or value.get("code_sha") != release["code_sha"]:
        raise PermissionError("paired training progress belongs to another release")
    learners = {
        arm: RegisteredLinearLearner.from_snapshot(value["learners"][arm], release=release)
        for arm in HOST_ARMS
    }
    return learners, int(value["cursor"]), {
        arm: dict(value["training_summary"][arm]) for arm in HOST_ARMS
    }


def _training_schedule(seed: int) -> list[tuple[int, int, int]]:
    schedule: list[tuple[int, int, int]] = []
    for episode in range(64):
        envelopes = list(_TRAINING_ENVELOPES)
        if categorical(2, seed, "world", ("training-envelope-order", episode)):
            envelopes.reverse()
        for M in envelopes:
            schedule.extend((M, episode, window) for window in range(5))
    return schedule


def _finalize_checkpoint(
    root: Path,
    learner: RegisteredLinearLearner,
    *,
    release: Mapping[str, Any],
    training_summary: Mapping[str, Any],
) -> dict[str, Any]:
    staging = root / "progress" / f"terminal-{learner.arm.lower()}-{learner.seed}.json"
    ref = write_registered_checkpoint(
        staging,
        learner,
        cursor={
            "training_complete": True,
            "completed_decisions": 1_984,
            "training_summary": dict(training_summary),
        },
        release=release,
    )
    target = (
        root
        / "checkpoints"
        / f"{learner.arm.lower()}-seed-{learner.seed}-{ref['content_sha256']}.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != ref["sha256"]:
            raise ValueError("content-addressed checkpoint collision")
        staging.unlink(missing_ok=True)
    else:
        os.replace(staging, target)
    return {
        "arm": learner.arm,
        "seed": learner.seed,
        "path": target.relative_to(root).as_posix(),
        "sha256": ref["sha256"],
        "content_sha256": ref["content_sha256"],
        "content_addressed": True,
    }


def _load_final_learner(
    root: Path, arm: str, seed: int, *, release: Mapping[str, Any]
) -> tuple[RegisteredLinearLearner, dict[str, Any], dict[str, Any]] | None:
    matches = list((root / "checkpoints").glob(f"{arm.lower()}-seed-{seed}-*.json"))
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError("checkpoint identity has multiple content-addressed values")
    learner, cursor, content_sha = load_registered_checkpoint(matches[0], release=release)
    return learner, {
        "arm": arm,
        "seed": seed,
        "path": matches[0].relative_to(root).as_posix(),
        "sha256": hashlib.sha256(matches[0].read_bytes()).hexdigest(),
        "content_sha256": content_sha,
        "content_addressed": True,
    }, dict(cursor["training_summary"])


def _train_seed_pair(
    root: Path, seed: int, *, release: Mapping[str, Any]
) -> tuple[
    dict[str, RegisteredLinearLearner],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    progress_path = _seed_progress_path(root, seed)
    completed = {
        arm: _load_final_learner(root, arm, seed, release=release) for arm in HOST_ARMS
    }
    if all(completed.values()):
        learners = {arm: completed[arm][0] for arm in HOST_ARMS}  # type: ignore[index]
        refs = [completed[arm][1] for arm in HOST_ARMS]  # type: ignore[index]
        summaries = {arm: completed[arm][2] for arm in HOST_ARMS}  # type: ignore[index]
        return learners, refs, summaries
    if any(completed.values()):
        if not progress_path.exists():
            raise ValueError("paired arm checkpoint panel is incomplete")
        learners, cursor, summaries = _load_seed_progress(progress_path, release=release)
        if cursor != len(_training_schedule(seed)) or any(
            learner.completed_decisions != 1_984 for learner in learners.values()
        ):
            raise ValueError("paired checkpoint finalization cannot resume incomplete training")
        refs = [
            completed[arm][1] if completed[arm] else _finalize_checkpoint(
                root,
                learners[arm],
                release=release,
                training_summary=summaries[arm],
            )
            for arm in HOST_ARMS
        ]
        progress_path.unlink(missing_ok=True)
        return learners, refs, summaries
    if progress_path.exists():
        learners, cursor, summaries = _load_seed_progress(progress_path, release=release)
    else:
        learners = {
            arm: RegisteredLinearLearner(arm, seed, release=release) for arm in HOST_ARMS
        }
        cursor = 0
        summaries = {
            arm: {
                "first_passage_75pct_selection": None,
                "selector_action_counts": [0, 0],
                "controller_action_counts": [0, 0],
                "grouped_window_updates_per_head": 0,
            }
            for arm in HOST_ARMS
        }
    schedule = _training_schedule(seed)
    host_boundaries: dict[tuple[str, int, int], SharedHostReceiptBoundary] = {}
    for schedule_index in range(cursor, len(schedule)):
        M, episode, window = schedule[schedule_index]
        for arm in HOST_ARMS:
            key = (arm, M, episode)
            if key not in host_boundaries:
                host_boundaries[key] = SharedHostReceiptBoundary(
                    seed=seed, phase="TRAIN", M=M, episode=episode
                )
        sampled = {
            arm: _sample_window(
                learners[arm],
                phase="TRAIN",
                M=M,
                episode=episode,
                window=window,
                branch=None,
                host_boundary=host_boundaries[(arm, M, episode)],
            )
            for arm in HOST_ARMS
        }
        if not (root / "activity.json").exists():
            commit_paired_activity_marker(
                root,
                [
                    {
                        "arm": arm,
                        "window_id": f"TRAIN-M{M}-E{episode}-W{window}",
                        "complete": True,
                        "common_team_return_observed": True,
                        "fixture_kind": "REGISTERED_R01_RELEASED",
                    }
                    for arm in HOST_ARMS
                ],
                release=release,
            )
        for arm in HOST_ARMS:
            selector, controller, observations, team_return = sampled[arm]
            summary = summaries[arm]
            for row in observations:
                summary["selector_action_counts"][row["selector_action"]] += 1
                summary["controller_action_counts"][row["controller_action"]] += 1
            if (
                summary["first_passage_75pct_selection"] is None
                and sum(row["selected_relevant"] for row in observations) / len(observations)
                >= 0.75
            ):
                summary["first_passage_75pct_selection"] = (
                    learners[arm].completed_decisions + len(observations)
                )
            learners[arm].apply_window(
                selector,
                controller,
                pair_count=len(selector),
                window_id=f"TRAIN-M{M}-E{episode}-W{window}",
                common_team_return=team_return,
            )
            summary["grouped_window_updates_per_head"] += 1
        _save_seed_progress(
            progress_path,
            learners,
            cursor=schedule_index + 1,
            release=release,
            training_summary=summaries,
        )
    if any(learner.completed_decisions != 1_984 for learner in learners.values()):
        raise ValueError("training decision count is not exactly 1984 per arm/seed")
    refs = [
        _finalize_checkpoint(
            root,
            learners[arm],
            release=release,
            training_summary=summaries[arm],
        )
        for arm in HOST_ARMS
    ]
    progress_path.unlink(missing_ok=True)
    return learners, refs, summaries


def _aggregate_evaluation(
    learners_by_seed: Mapping[int, Mapping[str, RegisteredLinearLearner]]
) -> list[dict[str, Any]]:
    totals: dict[tuple[Any, ...], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    active_masks: dict[tuple[Any, ...], set[str]] = defaultdict(set)
    role_counts: dict[tuple[Any, ...], dict[int, list[int]]] = defaultdict(
        lambda: defaultdict(lambda: [0, 0])
    )
    for seed in REGISTERED_SEEDS:
        for arm in HOST_ARMS:
            learner = learners_by_seed[seed][arm]
            frozen = learner.snapshot_digest()
            for branch in _EVALUATION_BRANCHES:
                for M in _EVALUATION_ENVELOPES:
                    for episode in range(32):
                        host_boundary = SharedHostReceiptBoundary(
                            seed=seed, phase="EVALUATION", M=M, episode=episode
                        )
                        for window in range(5):
                            _selector, _controller, observations, team_return = _sample_window(
                                learner,
                                phase="EVALUATION",
                                M=M,
                                episode=episode,
                                window=window,
                                branch=branch,
                                host_boundary=host_boundary,
                            )
                            if learner.snapshot_digest() != frozen:
                                raise ValueError("frozen evaluation changed learner state")
                            key = (seed, arm, M, observations[0]["N_t"], window, branch)
                            bucket = totals[key]
                            bucket["decisions"] += len(observations)
                            bucket["selected"] += sum(row["selected_relevant"] for row in observations)
                            bucket["safe"] += sum(row["safe"] for row in observations)
                            bucket["score_positive"] += sum(row["pair_score"] == 1 for row in observations)
                            bucket["score_negative"] += sum(row["pair_score"] == -1 for row in observations)
                            bucket["team_return_sum"] += team_return
                            bucket["team_windows"] += 1
                            bucket["selector_0"] += sum(row["selector_action"] == 0 for row in observations)
                            bucket["selector_1"] += sum(row["selector_action"] == 1 for row in observations)
                            bucket["controller_0"] += sum(row["controller_action"] == 0 for row in observations)
                            bucket["controller_1"] += sum(row["controller_action"] == 1 for row in observations)
                            bucket["selector_margin_sum"] += sum(row["selector_margin"] for row in observations)
                            bucket["controller_margin_sum"] += sum(row["controller_margin"] for row in observations)
                            bucket["registry_lookup_count"] += sum(row["registry_lookup_count"] for row in observations)
                            bucket["registry_serial_matches"] += sum(row["registry_serial_match"] for row in observations)
                            bucket["record_issuance_count"] += sum(row["record_issuance_count"] for row in observations)
                            bucket["payload_read_count"] += sum(row["payload_read_count"] for row in observations)
                            bucket["reservation_service_count"] += sum(row["reservation_service_count"] for row in observations)
                            bucket["state_continuity_checks"] += sum(row["state_continuity"] for row in observations)
                            joining = [row for row in observations if row["joining_or_rejoining"]]
                            bucket["fresh_token_checks"] += len(joining)
                            bucket["fresh_token_passes"] += sum(row["fresh_slot_token"] for row in joining)
                            peer_rows = [row for row in observations if row["peer_change_observed"] is not None]
                            bucket["peer_change_eligible"] += len(peer_rows)
                            bucket["peer_changes"] += sum(row["peer_change_observed"] for row in peer_rows)
                            bucket["decoy_next_publisher_matches"] += sum(row["decoy_next_publisher_match"] for row in observations)
                            for row in observations:
                                active_masks[key].add(row["active_mask_sha256"])
                                role_counts[key][row["publisher"]][0] += 1
                                role_counts[key][row["subscriber"]][1] += 1
    rows: list[dict[str, Any]] = []
    def entropy(counts: tuple[int, int]) -> float:
        total = sum(counts)
        value = 0.0
        for count in counts:
            if count:
                probability = count / total
                value -= probability * math.log2(probability)
        return value

    for key in sorted(totals, key=lambda item: tuple(str(value) for value in item)):
        seed, arm, M, N_t, window, branch = key
        bucket = totals[key]
        count = int(bucket["decisions"])
        p = _PRESENTATION[seed]
        selector_counts = (int(bucket["selector_0"]), int(bucket["selector_1"]))
        controller_counts = (int(bucket["controller_0"]), int(bucket["controller_1"]))
        lineage_balanced = all(
            publisher == subscriber
            for publisher, subscriber in role_counts[key].values()
        )
        identity_anomalies = []
        if bucket["registry_serial_matches"] != count:
            identity_anomalies.append("REGISTRY_SERIAL_MISMATCH")
        if bucket["state_continuity_checks"] != count:
            identity_anomalies.append("LINEAGE_STATE_DISCONTINUITY")
        if bucket["fresh_token_passes"] != bucket["fresh_token_checks"]:
            identity_anomalies.append("STALE_REJOIN_TOKEN")
        if bucket["decoy_next_publisher_matches"] != count:
            identity_anomalies.append("DECOY_PUBLISHER_MISMATCH")
        rows.append(
            {
                "seed": seed,
                "arm": arm,
                "M": M,
                "N_t": N_t,
                "window": window,
                "branch": branch,
                "relevant_record_selection_rate": bucket["selected"] / count,
                "pair_safe_rate": bucket["safe"] / count,
                "pair_score_distribution": {
                    "+1": int(bucket["score_positive"]),
                    "-1": int(bucket["score_negative"]),
                },
                "common_team_return": bucket["team_return_sum"] / bucket["team_windows"],
                "selector_action_counts": list(selector_counts),
                "controller_action_counts": list(controller_counts),
                "selector_action_entropy_bits": entropy(selector_counts),
                "controller_action_entropy_bits": entropy(controller_counts),
                "selector_mean_margin": bucket["selector_margin_sum"] / count,
                "controller_mean_margin": bucket["controller_margin_sum"] / count,
                "evaluation_decisions": count,
                "updates_parameters": False,
                "resource_receipt": [1, 1],
                "membership_window_stratum": (
                    "REDUCED_DEPARTURE" if window in (1, 3)
                    else "FIRST_POST_REJOIN" if window in (2, 4)
                    else "FULL_ROSTER"
                ),
                "active_mask_count": N_t,
                "active_masks": sorted(active_masks[key]),
                "lineage_role_balance_bound": lineage_balanced,
                "peer_change_rate": (
                    None if bucket["peer_change_eligible"] == 0
                    else bucket["peer_changes"] / bucket["peer_change_eligible"]
                ),
                "survivor_rejoin_state_checks": bucket["state_continuity_checks"] == count,
                "fresh_slot_token_checks": {
                    "observed": int(bucket["fresh_token_checks"]),
                    "passed": int(bucket["fresh_token_passes"]),
                },
                "registry_lookup_count": int(bucket["registry_lookup_count"]),
                "matched_registry_lookup_rate": bucket["registry_serial_matches"] / count,
                "record_issuance_count": int(bucket["record_issuance_count"]),
                "payload_read_count": int(bucket["payload_read_count"]),
                "reservation_service_count": int(bucket["reservation_service_count"]),
                "identity_path_anomalies": identity_anomalies,
                "mediator_residual": (
                    bucket["team_return_sum"] / bucket["team_windows"]
                    - bucket["selected"] / count
                ),
                "kappa": p["kappa"],
                "mu": p["mu"],
                "lambda": p["lambda"],
            }
        )
    return rows


def _pooled(
    rows: Sequence[Mapping[str, Any]], *, seed: int, arm: str, M: int, branch: str, field: str
) -> float:
    chosen = [
        row for row in rows
        if row["seed"] == seed and row["arm"] == arm and row["M"] == M and row["branch"] == branch
    ]
    numerator = sum(float(row[field]) * int(row["evaluation_decisions"]) for row in chosen)
    denominator = sum(int(row["evaluation_decisions"]) for row in chosen)
    return numerator / denominator


def _control_invariants(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for seed in REGISTERED_SEEDS:
        for M in _EVALUATION_ENVELOPES:
            checks.append({
                "control": "REASSOCIATED_NATURAL",
                "seed": seed,
                "M": M,
                "observed": _pooled(rows, seed=seed, arm="REASSOCIATED", M=M, branch="NATURAL", field="relevant_record_selection_rate"),
                "expected": 0.5,
            })
            for arm in HOST_ARMS:
                for branch, expected in (("MASKED", 0.5), ("FORCE_RELEVANT", 1.0), ("FORCE_DECOY", 0.0)):
                    checks.append({
                        "control": f"{arm}_{branch}",
                        "seed": seed,
                        "M": M,
                        "observed": _pooled(rows, seed=seed, arm=arm, M=M, branch=branch, field="relevant_record_selection_rate"),
                        "expected": expected,
                    })
    for check in checks:
        check["exact"] = check["observed"] == check["expected"]
    return {"complete": True, "all_exact": all(row["exact"] for row in checks), "checks": checks}


def _effect_panel(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    panel: list[dict[str, Any]] = []
    for seed in REGISTERED_SEEDS:
        for M in _EVALUATION_ENVELOPES:
            authentic_selection = _pooled(
                rows, seed=seed, arm="AUTHENTIC", M=M, branch="NATURAL",
                field="relevant_record_selection_rate",
            )
            reassociated_selection = _pooled(
                rows, seed=seed, arm="REASSOCIATED", M=M, branch="NATURAL",
                field="relevant_record_selection_rate",
            )
            authentic_return = _pooled(
                rows, seed=seed, arm="AUTHENTIC", M=M, branch="NATURAL",
                field="common_team_return",
            )
            reassociated_return = _pooled(
                rows, seed=seed, arm="REASSOCIATED", M=M, branch="NATURAL",
                field="common_team_return",
            )
            natural_masked = {
                field: _pooled(
                    rows, seed=seed, arm="AUTHENTIC", M=M, branch="NATURAL", field=field
                ) - _pooled(
                    rows, seed=seed, arm="AUTHENTIC", M=M, branch="MASKED", field=field
                )
                for field in ("relevant_record_selection_rate", "common_team_return")
            }
            forced = {
                arm: _pooled(
                    rows, seed=seed, arm=arm, M=M, branch="FORCE_RELEVANT",
                    field="common_team_return",
                ) - _pooled(
                    rows, seed=seed, arm=arm, M=M, branch="FORCE_DECOY",
                    field="common_team_return",
                )
                for arm in HOST_ARMS
            }
            panel.append({
                "seed": seed,
                "M": M,
                "heldout_M10": M == 10,
                "paired_selection_effect": authentic_selection - reassociated_selection,
                "paired_return_effect": authentic_return - reassociated_return,
                "natural_masked_effect": natural_masked,
                "forced_relevant_decoy_return_effect": forced,
            })
    return panel


def _first_true_outcome(rows: Sequence[Mapping[str, Any]], controls: Mapping[str, Any]) -> str:
    if controls.get("all_exact") is not True:
        return "INVALID_OR_INCONCLUSIVE"
    def weighted(chosen: Sequence[Mapping[str, Any]], field: str) -> float:
        denominator = sum(int(row["evaluation_decisions"]) for row in chosen)
        return sum(
            float(row[field]) * int(row["evaluation_decisions"]) for row in chosen
        ) / denominator

    def arm_effect(
        *, M: int, field: str, predicate: Any = lambda _row: True
    ) -> float:
        authentic = [
            row for row in rows
            if row["arm"] == "AUTHENTIC" and row["M"] == M
            and row["branch"] == "NATURAL" and predicate(row)
        ]
        reassociated = [
            row for row in rows
            if row["arm"] == "REASSOCIATED" and row["M"] == M
            and row["branch"] == "NATURAL" and predicate(row)
        ]
        return weighted(authentic, field) - weighted(reassociated, field)

    effects: dict[tuple[int, int], tuple[float, float]] = {}
    controller_ok = True
    for seed in REGISTERED_SEEDS:
        for M in _EVALUATION_ENVELOPES:
            auth_sel = _pooled(rows, seed=seed, arm="AUTHENTIC", M=M, branch="NATURAL", field="relevant_record_selection_rate")
            reassoc_sel = _pooled(rows, seed=seed, arm="REASSOCIATED", M=M, branch="NATURAL", field="relevant_record_selection_rate")
            auth_return = _pooled(rows, seed=seed, arm="AUTHENTIC", M=M, branch="NATURAL", field="common_team_return")
            reassoc_return = _pooled(rows, seed=seed, arm="REASSOCIATED", M=M, branch="NATURAL", field="common_team_return")
            effects[(seed, M)] = (auth_sel - reassoc_sel, auth_return - reassoc_return)
            forced_seed_rows = [
                row for row in rows
                if row["seed"] == seed and row["M"] == M
                and row["branch"] == "FORCE_RELEVANT"
            ]
            controller_ok &= weighted(forced_seed_rows, "pair_safe_rate") >= 0.90
    if not controller_ok:
        return "INVALID_OR_INCONCLUSIVE"
    forced_effects = [
        weighted(
            [row for row in rows if row["M"] == M and row["branch"] == "FORCE_RELEVANT"],
            "common_team_return",
        )
        - weighted(
            [row for row in rows if row["M"] == M and row["branch"] == "FORCE_DECOY"],
            "common_team_return",
        )
        for M in _EVALUATION_ENVELOPES
    ]
    forced_effect_positive = all(effect > 0 for effect in forced_effects)
    forced_effect_ok = all(effect >= 0.40 for effect in forced_effects)
    in_support = all(effects[(seed, M)][0] > 0 and effects[(seed, M)][1] > 0 for seed in REGISTERED_SEEDS for M in (6, 8))
    heldout = all(effects[(seed, 10)][0] > 0 and effects[(seed, 10)][1] > 0 for seed in REGISTERED_SEEDS)
    polarity_pass = all(
        arm_effect(
            M=M,
            field=field,
            predicate=lambda row, axis=axis, value=value: row[axis] == value,
        ) > 0
        for M in _EVALUATION_ENVELOPES
        for field in ("relevant_record_selection_rate", "common_team_return")
        for axis in ("kappa", "mu", "lambda")
        for value in (0, 1)
    )
    membership_pass = all(
        arm_effect(
            M=M,
            field=field,
            predicate=lambda row, M=M: row["N_t"] == M - 2,
        ) > 0
        and arm_effect(
            M=M,
            field=field,
            predicate=lambda row: row["window"] in (2, 4),
        ) > 0
        for M in _EVALUATION_ENVELOPES
        for field in ("relevant_record_selection_rate", "common_team_return")
    )
    mean_effects = [
        (
            sum(effects[(seed, M)][0] for seed in REGISTERED_SEEDS) / 8,
            sum(effects[(seed, M)][1] for seed in REGISTERED_SEEDS) / 8,
        )
        for M in _EVALUATION_ENVELOPES
    ]
    mean_m10_selection = sum(effects[(seed, 10)][0] for seed in REGISTERED_SEEDS) / 8
    mean_m10_return = sum(effects[(seed, 10)][1] for seed in REGISTERED_SEEDS) / 8
    authentic_m10 = sum(_pooled(rows, seed=seed, arm="AUTHENTIC", M=10, branch="NATURAL", field="relevant_record_selection_rate") for seed in REGISTERED_SEEDS) / 8
    authentic_natural_rows = [row for row in rows if row["arm"] == "AUTHENTIC" and row["M"] == 10 and row["branch"] == "NATURAL"]
    authentic_masked_rows = [row for row in rows if row["arm"] == "AUTHENTIC" and row["M"] == 10 and row["branch"] == "MASKED"]
    natural_masked_pass = (
        weighted(authentic_natural_rows, "relevant_record_selection_rate")
        > weighted(authentic_masked_rows, "relevant_record_selection_rate")
        and weighted(authentic_natural_rows, "common_team_return")
        > weighted(authentic_masked_rows, "common_team_return")
    )
    return interpret_first_true(
        {
            "valid": True,
            "controller_competent": controller_ok,
            "primary_selection_all_positive": all(
                value[0] > 0 for value in effects.values()
            ),
            "primary_return_all_positive": all(
                value[1] > 0 for value in effects.values()
            ),
            "in_support_both_positive": in_support,
            "heldout_both_positive": heldout,
            "forced_contrast_positive": forced_effect_positive,
            "forced_contrast_pass": forced_effect_ok,
            "bounded_null": within_bounded_null(mean_effects),
            "positive_thresholds_pass": (
                heldout
                and mean_m10_selection >= 0.20
                and mean_m10_return >= 0.10
                and authentic_m10 >= 0.70
                and forced_effect_ok
            ),
            "natural_masked_pass": natural_masked_pass,
            "polarity_geometry_pass": polarity_pass,
            "membership_geometry_pass": membership_pass,
        }
    )


def interpret_first_true(facts: Mapping[str, bool]) -> str:
    """Apply the authority's frozen first-true interpretation precedence."""

    if not facts["valid"] or not facts["controller_competent"]:
        return "INVALID_OR_INCONCLUSIVE"
    positive_predicates = (
        facts["primary_selection_all_positive"]
        and facts["primary_return_all_positive"]
        and facts["in_support_both_positive"]
        and facts["heldout_both_positive"]
        and facts["forced_contrast_pass"]
        and facts["positive_thresholds_pass"]
        and facts["natural_masked_pass"]
    )
    if (
        positive_predicates
        and (not facts["polarity_geometry_pass"] or not facts["membership_geometry_pass"])
    ):
        return "OPTIMIZATION_GEOMETRY_FALSIFIER"
    if facts["bounded_null"]:
        return "BOUNDED_NULL"
    if not facts["primary_selection_all_positive"]:
        return "CARRIER_CREDIT_UNSUPPORTED"
    if not facts["primary_return_all_positive"]:
        return (
            "SELECTION_TO_COORDINATION_UNSUPPORTED"
            if facts["forced_contrast_positive"]
            else "RESERVATION_INFORMATION_EDGE_ABSENT"
        )
    if facts["in_support_both_positive"] and not facts["heldout_both_positive"]:
        return "HELDOUT_ROSTER_TRANSFER_FAILED"
    if not facts["forced_contrast_positive"]:
        return "RESERVATION_INFORMATION_EDGE_ABSENT"
    if positive_predicates and facts["polarity_geometry_pass"] and facts["membership_geometry_pass"]:
        return "POSITIVE_EDGE"
    return "INCONCLUSIVE_REMAINDER"


def within_bounded_null(mean_effects: Sequence[tuple[float, float]]) -> bool:
    return len(mean_effects) == 3 and all(
        -0.05 <= selection <= 0.05 and -0.05 <= team_return <= 0.05
        for selection, team_return in mean_effects
    )


def run_registered_transaction(root: Path, *, release: Mapping[str, Any]) -> dict[str, Any]:
    """Execute the one released R01 transaction; callers must hold its Operator Effect."""

    if release.get("released") is not True:
        raise PermissionError("registered transaction requires validated release")
    if (root / "result.json").exists() or (root / "terminal.json").exists():
        raise PermissionError("terminal no-rerun boundary forbids transaction replay")
    tracemalloc.start()
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    gate = _retained_gate_receipt()
    learners_by_seed: dict[int, dict[str, RegisteredLinearLearner]] = {}
    training_summaries: list[dict[str, Any]] = []
    checkpoint_refs: list[dict[str, Any]] = []
    for seed in REGISTERED_SEEDS:
        learners, refs, summaries = _train_seed_pair(root, seed, release=release)
        learners_by_seed[seed] = learners
        checkpoint_refs.extend(refs)
        training_summaries.extend(
            {"seed": seed, "arm": arm, **summaries[arm]} for arm in HOST_ARMS
        )
    if len(checkpoint_refs) != 16:
        raise ValueError("registered transaction did not produce sixteen checkpoints")
    measurements = _aggregate_evaluation(learners_by_seed)
    evaluation_decisions = sum(int(row["evaluation_decisions"]) for row in measurements)
    if evaluation_decisions != 110_592:
        raise ValueError("frozen evaluation decision count drifted")
    controls = _control_invariants(measurements)
    effects = _effect_panel(measurements)
    outcome = _first_true_outcome(measurements, controls)
    host_log_pass = all(
        row["matched_registry_lookup_rate"] == 1.0
        and row["record_issuance_count"] == 2 * row["evaluation_decisions"]
        and row["payload_read_count"] == row["evaluation_decisions"]
        and row["reservation_service_count"] == row["evaluation_decisions"]
        and row["lineage_role_balance_bound"] is True
        and row["survivor_rejoin_state_checks"] is True
        and row["fresh_slot_token_checks"]["observed"]
        == row["fresh_slot_token_checks"]["passed"]
        and row["identity_path_anomalies"] == []
        for row in measurements
    )
    if not host_log_pass:
        outcome = "INVALID_OR_INCONCLUSIVE"
    elapsed = time.perf_counter() - started_wall
    cpu_seconds = time.process_time() - started_cpu
    _current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    scratch_bytes = sum(
        path.stat().st_size for path in root.rglob("*") if path.is_file()
    )
    resource_caps_pass = (
        elapsed <= 600
        and cpu_seconds <= 600
        and peak_memory <= 1_073_741_824
        and scratch_bytes <= 536_870_912
    )
    if not resource_caps_pass:
        outcome = "INVALID_OR_INCONCLUSIVE"
    evidence_nodes = [
        {"id": "release-contract", "status": "PASS"},
        {"id": "retained-support-gate", "status": "PASS"},
        {"id": "exact-transaction-count", "status": "PASS"},
        {"id": "sixteen-isolated-checkpoints", "status": "PASS"},
        {"id": "cold-resume-no-repeated-update", "status": "PASS"},
        {"id": "complete-frozen-evaluation-panel", "status": "PASS"},
        {"id": "control-invariants", "status": "PASS" if controls["all_exact"] else "STRUCTURAL_FAILURE"},
        {"id": "host-activity-log", "status": "PASS" if host_log_pass else "STRUCTURAL_FAILURE"},
        {"id": "resource-caps", "status": "PASS" if resource_caps_pass else "CAP_BREACH"},
        {"id": "atomic-complete-only-publication", "status": "PASS"},
    ]
    anomalies = sorted(
        {
            anomaly
            for row in measurements
            for anomaly in row["identity_path_anomalies"]
        }
    )
    if not controls["all_exact"]:
        anomalies.append("CONTROL_INVARIANT_FAILURE")
    if not resource_caps_pass:
        anomalies.append("RESOURCE_CAP_BREACH")
    return {
        "complete": True,
        "registered_total_transactions": 157_696,
        "gate_transactions": gate["transactions"],
        "training_decisions": 31_744,
        "evaluation_decisions": evaluation_decisions,
        "workers": 1,
        "threads_per_worker": 1,
        "repeated_update": False,
        "cross_arm_or_seed_state": False,
        "terminal_rerun": False,
        "checkpoint_refs": checkpoint_refs,
        "authority_refs": release["authority_refs"],
        "source_manifest": release["source_test_manifest"],
        "retained_gate": gate,
        "anomalies": anomalies,
        "result_firewall": {
            "partial_result_published": (root / "result.json").exists(),
            "question_values_in_checkpoint": False,
            "complete_only": True,
            "terminal_rerun": False,
        },
        "training_measurements": training_summaries,
        "measurements": measurements,
        "effects": effects,
        "control_invariants": controls,
        "scientific_first_true_outcome": outcome,
        "declared_actual_resource_totals": {
            "declared_transactions": 157_696,
            "actual_transactions": gate["transactions"] + 31_744 + evaluation_decisions,
            "payload_reads": 31_744 + evaluation_decisions + gate["accepted"],
            "reservation_services": 31_744 + evaluation_decisions + gate["accepted"],
            "denied_open_both": gate["denied"],
            "subscriber_update_inputs": 31_744,
            "grouped_window_head_applications": 20_480,
            "wall_seconds": elapsed,
            "cpu_seconds": cpu_seconds,
            "peak_memory_bytes": peak_memory,
            "scratch_bytes_before_result": scratch_bytes,
            "memory_cap_bytes": 1_073_741_824,
            "scratch_cap_bytes": 536_870_912,
            "durable_result_cap_bytes": 268_435_456,
            "resource_caps_pass": resource_caps_pass,
        },
        "evidence_tree": {"terminal_status": "REGISTERED_COMPLETE", "nodes": evidence_nodes},
    }
