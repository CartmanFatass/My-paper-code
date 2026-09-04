"""Complete resumable RUN-01 stage orchestration over the real native host."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import hashlib
import json
import math
from pathlib import Path
import struct
from typing import Callable, Iterable, Mapping

from .analysis import HeldoutAnalysis, HeldoutCell, analyze_heldout_panel
from .artifacts import freeze_action_map, open_heldout_namespace
from .contracts import (
    CURVE_UPDATES,
    STATE_SPECS,
    TRAINING_SEEDS,
    RunManifest,
)
from .foundation import (
    CompetenceGate,
    ImmutableBatchedFoundationPolicy,
    analyze_competence,
    freeze_foundation_actor,
    materialize_foundation,
)
from .frontier import FrontierController
from .native_backend import (
    ReachableStatePanelNotEstablished,
    construct_reachable_twins,
    disturbance_tape_sha256,
    evaluate_twin_branches,
    persistent_normalized_bytes,
    NativeSession,
    verify_native_transition,
)
from .native_state import (
    ReachableTwins, SourceCandidateWitness, SourceRenewalWitness, SourceScanReceipt,
    TapeAddress, TapeNamespace,
)
from .orchestration import (
    Attempt,
    AttemptError,
    WorkLedger,
    atomic_create_json,
    load_checkpoint_training_receipt,
    load_foundation_checkpoint,
    write_foundation_checkpoint,
)
from .rng import (
    CounterRNG,
    development_tape_address,
    materialize_disturbance_tape,
    source_reset_values,
    source_tape_address,
)
from .selection import DevelopmentCell, DevelopmentMapping, freeze_development_mapping
from .training import ExactAdamW
from .workload import (
    MissionEndpoint,
    competence_records,
    evaluate_foundation_missions,
    execute_training_update,
)


PIPELINE_SCHEMA = "SCDMP_MF_RS_MK_B01_PRODUCTION_PIPELINE_V1"


@dataclass(frozen=True, slots=True)
class PipelineOutcome:
    branch: str
    ledger: WorkLedger
    source_states: int
    ppo_updates: int
    analysis: HeldoutAnalysis | None
    complete_full_chain: bool


class ValidScientificStop(RuntimeError):
    def __init__(self, outcome: PipelineOutcome) -> None:
        super().__init__(outcome.branch)
        self.outcome = outcome


class SourcePanelFailure(RuntimeError):
    def __init__(
        self,
        completed: tuple[ReachableTwins, ...],
        failure: ReachableStatePanelNotEstablished,
    ) -> None:
        super().__init__(str(failure))
        self.completed = completed
        self.failure = failure


@dataclass(frozen=True, slots=True)
class FoundationBundle:
    seed: int
    model: object
    optimizer: ExactAdamW
    curve_rows: tuple[MissionEndpoint, ...]
    competence_rows: tuple[MissionEndpoint, ...]


def _read_json(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AttemptError(f"production artifact is missing or unreadable: {path.name}") from error
    if not isinstance(value, dict):
        raise AttemptError(f"production artifact is not a JSON object: {path.name}")
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if raw != canonical:
        raise AttemptError(f"production artifact is not canonical direct JSON: {path.name}")
    return value


def _endpoint_value(row: MissionEndpoint) -> dict[str, object]:
    return asdict(row)


def _load_endpoints(
    path: Path,
    *,
    manifest: RunManifest,
    expected_seed: int,
    expected_stage: str,
    expected_update: int,
    missions_per_cell: int,
) -> tuple[MissionEndpoint, ...]:
    value = _read_json(path)
    raw_rows = value.get("rows")
    if (
        value.get("schema") != PIPELINE_SCHEMA
        or value.get("run_binding") != manifest.to_dict()
        or value.get("seed") != expected_seed
        or value.get("update") != expected_update
        or not isinstance(raw_rows, list)
    ):
        raise AttemptError("mission endpoint artifact schema differs")
    try:
        rows = tuple(MissionEndpoint(
            **{**row, "failures": tuple(row.get("failures", ()))},
        ) for row in raw_rows if isinstance(row, dict))
    except TypeError as error:
        raise AttemptError("mission endpoint fields differ") from error
    expected_addresses = {
        (graph, k, mission)
        for graph in ("HR", "RH") for k in (7, 13) for mission in range(missions_per_cell)
    }
    addresses = {(row.graph, row.k, row.mission) for row in rows}
    allowed_failures = ("cable_overload", "gantry_contact", "attitude_loss", "formation_loss")
    valid_rows = all(
        row.seed == expected_seed
        and row.stage == expected_stage
        and row.update == expected_update
        and row.terminal is True
        and row.graph in ("HR", "RH") and row.k in (7, 13)
        and isinstance(row.mission, int) and not isinstance(row.mission, bool)
        and 0 <= row.mission < missions_per_cell
        and isinstance(row.safe_dock, bool) and isinstance(row.timeout, bool)
        and row.failures == tuple(label for label in allowed_failures if label in row.failures)
        and len(set(row.failures)) == len(row.failures)
        and all(math.isfinite(value) for value in (row.utility, row.external_reward, row.energy))
        and 0.0 <= row.utility <= 1.0
        and row.allocated_slots == 364
        and isinstance(row.transitions, int) and not isinstance(row.transitions, bool)
        and 0 <= row.transitions <= 364
        and isinstance(row.policy_queries, int) and not isinstance(row.policy_queries, bool)
        and row.policy_queries >= 0
        and (
            (row.safe_dock and isinstance(row.dock_tick, int) and not isinstance(row.dock_tick, bool)
             and 1 <= row.dock_tick <= 364 and not row.timeout and not row.failures
             and row.utility == 1.0 - row.dock_tick / 364.0)
            or (not row.safe_dock and row.dock_tick is None and (row.timeout or bool(row.failures))
                and row.utility == 0.0)
        )
        for row in rows
    )
    if (
        len(rows) != 4 * missions_per_cell
        or len(raw_rows) != len(rows)
        or len(addresses) != len(rows)
        or addresses != expected_addresses
        or not valid_rows
    ):
        raise AttemptError("mission endpoint inventory differs")
    return rows


def _checkpoint_path(root: Path, seed: int, update: int) -> Path:
    return root / "foundations" / str(seed) / "checkpoints" / f"update-{update:03d}.json"


def _curve_path(root: Path, seed: int, update: int) -> Path:
    return root / "foundations" / str(seed) / "curves" / f"update-{update:03d}.json"


def _contiguous_checkpoint_frontier(root: Path, seed: int) -> int:
    directory = root / "foundations" / str(seed) / "checkpoints"
    observed = []
    if directory.is_dir():
        for path in directory.glob("update-*.json"):
            try:
                observed.append(int(path.stem.removeprefix("update-")))
            except ValueError as error:
                raise AttemptError("foundation checkpoint filename differs") from error
    if not observed:
        return -1
    frontier = max(observed)
    if sorted(observed) != list(range(frontier + 1)) or frontier > 160:
        raise AttemptError("foundation checkpoint frontier is not contiguous")
    return frontier


def _execute_foundation(
    attempt: Attempt,
    seed: int,
    *,
    scratch_observer: Callable[[Path], None] | None,
    frontier_controller: FrontierController | None,
) -> FoundationBundle:
    root = attempt.root
    checkpoint_frontier = _contiguous_checkpoint_frontier(root, seed)
    if checkpoint_frontier < 0:
        source = CounterRNG(seed)
        model = materialize_foundation(source)
        optimizer = ExactAdamW(tuple(model.named_parameters()))
        write_foundation_checkpoint(
            _checkpoint_path(root, seed, 0), model=model, optimizer=optimizer, update=0,
            run_manifest=attempt.run_manifest, scratch_observer=scratch_observer,
        )
        checkpoint_frontier = 0
    if frontier_controller is not None:
        for update in range(1, checkpoint_frontier + 1):
            frontier_controller.unit(f"training-{seed}-update-{update:03d}", created=False)
    model, optimizer = load_foundation_checkpoint(
        _checkpoint_path(root, seed, checkpoint_frontier), expected_seed=seed,
        run_manifest=attempt.run_manifest,
    )
    source = CounterRNG(seed)
    for update in range(checkpoint_frontier + 1, 161):
        observed = execute_training_update(model, optimizer, source, update=update)
        write_foundation_checkpoint(
            _checkpoint_path(root, seed, update), model=model, optimizer=optimizer,
            update=update, run_manifest=attempt.run_manifest,
            training_receipt=observed.receipt, scratch_observer=scratch_observer,
        )
        if frontier_controller is not None:
            frontier_controller.unit(f"training-{seed}-update-{update:03d}", created=True)

    curve_rows = []
    for update in CURVE_UPDATES:
        path = _curve_path(root, seed, update)
        created = not path.exists()
        if not created:
            rows = _load_endpoints(
                path, manifest=attempt.run_manifest, expected_seed=seed,
                expected_stage="CURVE", expected_update=update, missions_per_cell=8,
            )
        else:
            curve_model, _ = load_foundation_checkpoint(
                _checkpoint_path(root, seed, update), expected_seed=seed,
                run_manifest=attempt.run_manifest,
            )
            rows = evaluate_foundation_missions(
                curve_model, CounterRNG(seed), stage="CURVE", update=update,
                missions_per_cell=8,
            )
            atomic_create_json(path, {
                "schema": PIPELINE_SCHEMA,
                "run_binding": attempt.run_manifest.to_dict(),
                "seed": seed,
                "update": update,
                "rows": [_endpoint_value(row) for row in rows],
            }, scratch_observer=scratch_observer)
        if frontier_controller is not None:
            frontier_controller.unit(f"curve-{seed}-update-{update:03d}", created=created)
        curve_rows.extend(rows)

    competence_path = root / "foundations" / str(seed) / "competence.json"
    competence_created = not competence_path.exists()
    if not competence_created:
        competence_rows = _load_endpoints(
            competence_path, manifest=attempt.run_manifest, expected_seed=seed,
            expected_stage="COMPETENCE", expected_update=160, missions_per_cell=32,
        )
    else:
        competence_rows = evaluate_foundation_missions(
            model, source, stage="COMPETENCE", update=160, missions_per_cell=32,
        )
        atomic_create_json(competence_path, {
            "schema": PIPELINE_SCHEMA,
            "run_binding": attempt.run_manifest.to_dict(),
            "seed": seed,
            "update": 160,
            "rows": [_endpoint_value(row) for row in competence_rows],
        }, scratch_observer=scratch_observer)
    if frontier_controller is not None:
        frontier_controller.unit(f"competence-{seed}", created=competence_created)
    return FoundationBundle(seed, model, optimizer, tuple(curve_rows), tuple(competence_rows))


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: object) -> bytes:
    if not isinstance(value, str):
        raise AttemptError("native POD bytes must be canonical base64")
    try:
        direct = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        raise AttemptError("native POD bytes cannot be decoded") from error
    if _b64(direct) != value:
        raise AttemptError("native POD base64 is noncanonical")
    return direct


def _checkpoint_binding(root: Path, seed: int) -> dict[str, object]:
    path = _checkpoint_path(root, seed, 160)
    try:
        direct = path.read_bytes()
    except OSError as error:
        raise AttemptError("source witness final foundation checkpoint is unavailable") from error
    return {
        "relative_path": path.relative_to(root).as_posix(),
        "byte_size": len(direct),
        "sha256": hashlib.sha256(direct).hexdigest(),
    }


def _transition_proof(row: SourceRenewalWitness, tape) -> dict[str, object]:
    proof = verify_native_transition(
        pre_state_bytes=row.pre_state_bytes,
        action=row.foundation_action,
        active=True,
        disturbance_hold=tape[row.renewal_index],
        expected_post_state_bytes=row.post_state_bytes,
    )
    if proof.get("matched") is not True:
        raise AttemptError("source witness native transition proof differs")
    return proof


def _renewal_value(row: SourceRenewalWitness, tape) -> dict[str, object]:
    return {
        "candidate_index": row.candidate_index,
        "renewal_index": row.renewal_index,
        "public_input_b64": _b64(row.public_input_bytes),
        "foundation_action": row.foundation_action,
        "pre_state_b64": _b64(row.pre_state_bytes),
        "post_state_b64": _b64(row.post_state_bytes),
        "transition_proof": _transition_proof(row, tape),
    }


def _candidate_value(row: SourceCandidateWitness) -> dict[str, object]:
    tape = materialize_disturbance_tape(row.address)
    return {
        "candidate_index": row.candidate_index,
        "address": {
            "namespace": row.address.namespace.value,
            "seed": row.address.seed,
            "tape_id": row.address.tape_id,
        },
        "reset_values": list(row.reset_values),
        "tape_sha256": row.tape_sha256,
        "reset_state_b64": _b64(row.reset_state_bytes),
        "renewals": [_renewal_value(item, tape) for item in row.renewals],
        "receipt": asdict(row.receipt),
    }


def _load_candidate_witnesses(
    raw: object,
    *,
    manifest: RunManifest,
    state_spec,
    prefix_policy,
    expect_success: bool,
    validation_counts: dict[str, int] | None = None,
) -> tuple[SourceCandidateWitness, ...]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= 8:
        raise AttemptError("source candidate witness inventory differs")
    q_pre = manifest.q_by_cell[STATE_SPECS.index(state_spec)]
    result = []
    for candidate_index, value in enumerate(raw):
        if not isinstance(value, dict) or value.get("candidate_index") != candidate_index:
            raise AttemptError("source candidate chronology differs")
        canonical_address = source_tape_address(state_spec, candidate_index)
        address_value = value.get("address")
        if address_value != {
            "namespace": canonical_address.namespace.value,
            "seed": canonical_address.seed,
            "tape_id": canonical_address.tape_id,
        }:
            raise AttemptError("source candidate canonical address differs")
        reset_values = source_reset_values(canonical_address)
        if value.get("reset_values") != list(reset_values):
            raise AttemptError("source candidate reset values differ")
        tape = materialize_disturbance_tape(canonical_address)
        if value.get("tape_sha256") != disturbance_tape_sha256(tape):
            raise AttemptError("source candidate tape identity differs")
        reset_bytes = _unb64(value.get("reset_state_b64"))
        reset_state = NativeSession.from_state_bytes((reset_bytes,)).states()[0]
        if (
            reset_state.event_phase != "PRE_EVENT"
            or reset_state.latent_assignment != (1, 2, 3, 4)
            or reset_state.latent_q != q_pre
            or reset_state.output.tick != 0
            or reset_state.output.terminal
        ):
            raise AttemptError("source candidate reset POD differs")
        raw_renewals = value.get("renewals")
        if not isinstance(raw_renewals, list) or not raw_renewals:
            raise AttemptError("source candidate renewal witness is empty")
        renewals = []
        previous_post = reset_bytes
        transitions = 0
        for renewal_index, renewal_value in enumerate(raw_renewals):
            if (
                not isinstance(renewal_value, dict)
                or renewal_value.get("candidate_index") != candidate_index
                or renewal_value.get("renewal_index") != renewal_index
            ):
                raise AttemptError("source renewal canonical address differs")
            pre_bytes = _unb64(renewal_value.get("pre_state_b64"))
            post_bytes = _unb64(renewal_value.get("post_state_b64"))
            if pre_bytes != previous_post:
                raise AttemptError("source renewal POD chronology is not contiguous")
            pre = NativeSession.from_state_bytes((pre_bytes,)).states()[0]
            post = NativeSession.from_state_bytes((post_bytes,)).states()[0]
            public_bytes = _unb64(renewal_value.get("public_input_b64"))
            if public_bytes != struct.pack("<18d", *pre.output.observation):
                raise AttemptError("source renewal public policy input bytes differ")
            selected = tuple(prefix_policy((pre.output.observation,)))
            if validation_counts is not None:
                validation_counts["resume_validation_policy_forwards"] += 1
            action = renewal_value.get("foundation_action")
            if selected != (action,):
                raise AttemptError("source foundation action differs from persisted public input")
            if (
                post.event_phase != "PRE_EVENT"
                or post.latent_assignment != (1, 2, 3, 4)
                or post.latent_q != q_pre
                or post.output.tick - pre.output.tick != post.output.ticks_advanced
                or not 1 <= post.output.ticks_advanced <= state_spec.k
            ):
                raise AttemptError("source renewal typed POD transition facts differ")
            proof = verify_native_transition(
                pre_state_bytes=pre_bytes, action=int(action), active=True,
                disturbance_hold=tape[renewal_index], expected_post_state_bytes=post_bytes,
            )
            if validation_counts is not None:
                validation_counts["resume_validation_transition_proofs"] += 1
            if proof.get("matched") is not True or renewal_value.get("transition_proof") != proof:
                raise AttemptError("source renewal pure native transition proof differs")
            eligible_now = (
                not post.output.terminal
                and post.output.tick >= state_spec.target_tick
                and post.output.tick + state_spec.k <= 364
            )
            if eligible_now and renewal_index != len(raw_renewals) - 1:
                raise AttemptError("source witness skipped a first-eligible boundary")
            transitions += post.output.ticks_advanced
            renewals.append(SourceRenewalWitness(
                candidate_index, renewal_index, public_bytes, int(action), pre_bytes, post_bytes,
            ))
            previous_post = post_bytes
        final_state = NativeSession.from_state_bytes((previous_post,)).states()[0]
        receipt_value = value.get("receipt")
        eligible = (
            not final_state.output.terminal
            and final_state.output.tick >= state_spec.target_tick
            and final_state.output.tick + state_spec.k <= 364
        )
        receipt = SourceScanReceipt(
            candidate_index, eligible, len(renewals), transitions, len(renewals),
            final_state.output.terminal,
        )
        if receipt_value != asdict(receipt):
            raise AttemptError("source candidate receipt differs from complete witness")
        if candidate_index < len(raw) - 1 and (eligible or not final_state.output.terminal):
            raise AttemptError("source candidate chronology is not exhaustive")
        result.append(SourceCandidateWitness(
            candidate_index, canonical_address, reset_values, disturbance_tape_sha256(tape),
            reset_bytes, tuple(renewals), receipt,
        ))
    if expect_success:
        if not result[-1].receipt.eligible:
            raise AttemptError("source success witness lacks a first-eligible candidate")
    elif len(result) != 8 or any(row.receipt.eligible or not row.receipt.terminal for row in result):
        raise AttemptError("source exhaustion witness is not eight complete terminal candidates")
    return tuple(result)


def _twins_value(
    twins: ReachableTwins,
    manifest: RunManifest,
    *,
    checkpoint_binding: dict[str, object],
) -> dict[str, object]:
    return {
        "schema": PIPELINE_SCHEMA,
        "run_binding": manifest.to_dict(),
        "source_foundation_checkpoint": checkpoint_binding,
        "state_id": twins.state_id,
        "k": twins.k,
        "target_tick": twins.target_tick,
        "boundary_tick": twins.boundary_tick,
        "source_seed": twins.source_seed,
        "source_address": {
            "namespace": twins.source_address.namespace.value,
            "seed": twins.source_address.seed,
            "tape_id": twins.source_address.tape_id,
        },
        "pre_event_p": list(twins.pre_event_p),
        "pre_event_q": twins.pre_event_q,
        "source_snapshot_b64": _b64(twins.source_snapshot_bytes),
        "hr_state_b64": _b64(twins.hr.state_bytes),
        "rh_state_b64": _b64(twins.rh.state_bytes),
        "hr_public_b64": _b64(twins.hr_public_bytes),
        "rh_public_b64": _b64(twins.rh_public_bytes),
        "selected_tape_index": twins.selected_tape_index,
        "source_renewal_index": twins.source_renewal_index,
        "source_scan_receipts": [asdict(row) for row in twins.source_scan_receipts],
        "transitions": twins.transitions,
        "policy_queries": twins.policy_queries,
        "persistent_twin_bytes_equal": twins.persistent_twin_bytes_equal,
        "source_candidate_witnesses": [
            _candidate_value(row) for row in twins.source_candidate_witnesses
        ],
    }


def _load_twins(
    path: Path,
    manifest: RunManifest,
    *,
    state_spec,
    prefix_policy,
    checkpoint_binding: dict[str, object],
    validation_counts: dict[str, int] | None = None,
) -> ReachableTwins:
    value = _read_json(path)
    if state_spec not in STATE_SPECS:
        raise AttemptError("reachable-state witness spec differs")
    if (
        value.get("schema") != PIPELINE_SCHEMA
        or value.get("run_binding") != manifest.to_dict()
        or value.get("source_foundation_checkpoint") != checkpoint_binding
        or value.get("state_id") != state_spec.cell
        or value.get("k") != state_spec.k
        or value.get("target_tick") != state_spec.target_tick
        or value.get("source_seed") != state_spec.source_seed
    ):
        raise AttemptError("reachable-state witness binding differs")
    witnesses = _load_candidate_witnesses(
        value.get("source_candidate_witnesses"), manifest=manifest,
        state_spec=state_spec, prefix_policy=prefix_policy, expect_success=True,
        validation_counts=validation_counts,
    )
    selected = len(witnesses) - 1
    final_renewal = witnesses[-1].renewals[-1]
    source_bytes = _unb64(value.get("source_snapshot_b64"))
    if source_bytes != final_renewal.post_state_bytes:
        raise AttemptError("source snapshot differs from first-eligible witness frontier")
    try:
        source = NativeSession.from_state_bytes((source_bytes,)).states()[0]
    except Exception as error:
        raise AttemptError("reachable source POD validation failed") from error
    hr_bytes = _unb64(value.get("hr_state_b64"))
    rh_bytes = _unb64(value.get("rh_state_b64"))
    try:
        hr, rh = NativeSession.from_state_bytes((hr_bytes, rh_bytes)).states()
    except Exception as error:
        raise AttemptError("reachable twin POD validation failed") from error
    hr_public = _unb64(value.get("hr_public_b64"))
    rh_public = _unb64(value.get("rh_public_b64"))
    q_pre = manifest.q_by_cell[STATE_SPECS.index(state_spec)]
    persistent_equal = (
        persistent_normalized_bytes(source_bytes)
        == persistent_normalized_bytes(hr_bytes)
        == persistent_normalized_bytes(rh_bytes)
    )
    if (
        value.get("selected_tape_index") != selected
        or value.get("source_renewal_index") != len(witnesses[-1].renewals) - 1
        or value.get("boundary_tick") != source.output.tick
        or value.get("pre_event_p") != [1, 2, 3, 4]
        or value.get("pre_event_q") != q_pre
        or source.latent_assignment != (1, 2, 3, 4) or source.latent_q != q_pre
        or hr.latent_assignment != (4, 2, 1, 3) or hr.latent_q != 1
        or rh.latent_assignment != (1, 4, 2, 3) or rh.latent_q != 0
        or hr_public != struct.pack("<18d", *hr.output.observation)
        or rh_public != struct.pack("<18d", *rh.output.observation)
        or hr_public != rh_public
        or value.get("persistent_twin_bytes_equal") is not True
        or not persistent_equal
        or value.get("source_scan_receipts") != [asdict(row.receipt) for row in witnesses]
        or value.get("transitions") != sum(row.receipt.transitions for row in witnesses)
        or value.get("policy_queries") != sum(row.receipt.policy_queries for row in witnesses)
    ):
        raise AttemptError("reachable-state complete POD/public/persistent witness differs")
    address = source_tape_address(state_spec, selected)
    if value.get("source_address") != {
        "namespace": address.namespace.value, "seed": address.seed, "tape_id": address.tape_id,
    }:
        raise AttemptError("reachable-state selected source address differs")
    return ReachableTwins(
        state_id=state_spec.cell, k=state_spec.k, target_tick=state_spec.target_tick,
        boundary_tick=source.output.tick, source_seed=state_spec.source_seed,
        source_address=address, pre_event_p=source.latent_assignment, pre_event_q=q_pre,
        source_tape=materialize_disturbance_tape(address), source_snapshot_bytes=source_bytes,
        hr=hr, rh=rh, hr_public_bytes=hr_public, rh_public_bytes=rh_public,
        hr_assignment=hr.latent_assignment, rh_assignment=rh.latent_assignment,
        eligible=True, selected_tape_index=selected,
        source_renewal_index=len(witnesses[-1].renewals) - 1,
        source_scan_receipts=tuple(row.receipt for row in witnesses),
        persistent_twin_bytes_equal=True,
        transitions=sum(row.receipt.transitions for row in witnesses),
        policy_queries=sum(row.receipt.policy_queries for row in witnesses),
        source_candidate_witnesses=witnesses,
    )


def _execute_sources(
    attempt: Attempt,
    foundations: Mapping[int, FoundationBundle],
    *,
    scratch_observer: Callable[[Path], None] | None,
    frontier_controller: FrontierController | None,
) -> tuple[ReachableTwins, ...]:
    rows = []
    validation_counts = {
        "resume_validation_policy_forwards": 0,
        "resume_validation_transition_proofs": 0,
    }

    def publish_validation_counts() -> None:
        if not any(validation_counts.values()):
            return
        atomic_create_json(
            attempt.root / "resume-validation" / f"invocation-{attempt.invocation_index:06d}.json",
            {
                "schema": "SCDMP_MF_RS_MK_B01_RESUME_SOURCE_VALIDATION_V1",
                "run_binding": attempt.run_manifest.to_dict(),
                "invocation_index": attempt.invocation_index,
                **validation_counts,
                "scientific_missions": 0,
                "scientific_allocated_slots": 0,
            },
            scratch_observer=scratch_observer,
        )

    for spec in STATE_SPECS:
        path = attempt.root / "source-states" / f"{spec.cell}.json"
        failure_path = attempt.root / "source-states" / f"{spec.cell}-not-established.json"
        bundle = foundations[spec.source_seed]
        policy = ImmutableBatchedFoundationPolicy(freeze_foundation_actor(bundle.model))
        checkpoint_binding = _checkpoint_binding(attempt.root, spec.source_seed)
        if path.exists() and failure_path.exists():
            raise AttemptError("source success and exhaustion artifacts cannot coexist")
        if failure_path.exists():
            value = _read_json(failure_path)
            if (
                value.get("schema") != PIPELINE_SCHEMA
                or value.get("run_binding") != attempt.run_manifest.to_dict()
                or value.get("state_id") != spec.cell
                or value.get("source_foundation_checkpoint") != checkpoint_binding
                or value.get("scientific_polarity") is not None
            ):
                raise AttemptError("source exhaustion witness binding differs")
            witnesses = _load_candidate_witnesses(
                value.get("source_candidate_witnesses"), manifest=attempt.run_manifest,
                state_spec=spec, prefix_policy=policy, expect_success=False,
                validation_counts=validation_counts,
            )
            receipts = tuple(row.receipt for row in witnesses)
            error = ReachableStatePanelNotEstablished(receipts, witnesses)
            if (
                value.get("receipts") != [asdict(row) for row in receipts]
                or value.get("transitions") != error.transitions
                or value.get("policy_queries") != error.policy_queries
            ):
                raise AttemptError("source exhaustion witness counts differ")
            if frontier_controller is not None:
                frontier_controller.unit(f"source-{spec.cell}", created=False)
            publish_validation_counts()
            raise SourcePanelFailure(tuple(rows), error)
        if path.exists():
            twins = _load_twins(
                path, attempt.run_manifest, state_spec=spec, prefix_policy=policy,
                checkpoint_binding=checkpoint_binding, validation_counts=validation_counts,
            )
            created = False
        else:
            created = True
            try:
                twins = construct_reachable_twins(
                    run_manifest=attempt.run_manifest, state_spec=spec, prefix_policy=policy,
                )
            except ReachableStatePanelNotEstablished as error:
                atomic_create_json(attempt.root / "source-states" / f"{spec.cell}-not-established.json", {
                    "schema": PIPELINE_SCHEMA,
                    "run_binding": attempt.run_manifest.to_dict(),
                    "state_id": spec.cell,
                    "source_foundation_checkpoint": checkpoint_binding,
                    "receipts": [asdict(row) for row in error.receipts],
                    "source_candidate_witnesses": [
                        _candidate_value(row) for row in error.witnesses
                    ],
                    "transitions": error.transitions,
                    "policy_queries": error.policy_queries,
                    "scientific_polarity": None,
                }, scratch_observer=scratch_observer)
                if frontier_controller is not None:
                    frontier_controller.unit(f"source-{spec.cell}", created=True)
                publish_validation_counts()
                raise SourcePanelFailure(tuple(rows), error) from error
            atomic_create_json(
                path, _twins_value(
                    twins, attempt.run_manifest, checkpoint_binding=checkpoint_binding,
                ),
                scratch_observer=scratch_observer,
            )
        if frontier_controller is not None:
            frontier_controller.unit(f"source-{spec.cell}", created=created)
        rows.append(twins)
    publish_validation_counts()
    return tuple(rows)


def _failure_labels(output) -> tuple[str, ...]:
    return tuple(label for label, present in (
        ("cable_overload", output.cable_overload),
        ("gantry_contact", output.gantry_contact),
        ("attitude_loss", output.attitude_loss),
        ("formation_loss", output.formation_loss),
    ) if present)


def _development_cell(seed, twins, tape, graph, action, evaluation, lane) -> DevelopmentCell:
    output = evaluation.outputs[lane]
    spec = next(row for row in STATE_SPECS if row.cell == twins.state_id)
    return DevelopmentCell(
        seed, twins.state_id, spec.k, spec.stratum, tape, graph, action,
        output.completion_value, output.terminal, output.safe_dock, output.dock_tick,
        output.timeout, _failure_labels(output), output.cumulative_reward,
        output.cumulative_energy, 364, evaluation.transitions_by_lane[lane],
        evaluation.policy_queries_by_lane[lane],
    )


def _load_development(
    path: Path, *, manifest: RunManifest, seed: int, state_id: str, q_pre: int,
) -> tuple[DevelopmentCell, ...]:
    value = _read_json(path)
    raw = value.get("rows")
    if (
        value.get("schema") != PIPELINE_SCHEMA
        or value.get("run_binding") != manifest.to_dict()
        or value.get("seed") != seed or value.get("state_id") != state_id
        or value.get("realized_q_pre") != q_pre
        or not isinstance(raw, list)
    ):
        raise AttemptError("development unit artifact differs")
    try:
        rows = tuple(DevelopmentCell(
            **{**row, "failures": tuple(row.get("failures", ()))},
        ) for row in raw if isinstance(row, dict))
    except TypeError as error:
        raise AttemptError("development unit fields differ") from error
    if len(rows) != 288 or len(raw) != len(rows):
        raise AttemptError("development unit inventory differs")
    return rows


def _execute_development(
    attempt: Attempt,
    foundations: Mapping[int, FoundationBundle],
    twins_rows: tuple[ReachableTwins, ...],
    *,
    scratch_observer: Callable[[Path], None] | None,
    frontier_controller: FrontierController | None,
) -> DevelopmentMapping:
    all_cells = []
    by_state = {row.state_id: row for row in twins_rows}
    for seed in TRAINING_SEEDS:
        policy = ImmutableBatchedFoundationPolicy(freeze_foundation_actor(foundations[seed].model))
        for spec in STATE_SPECS:
            path = attempt.root / "development" / str(seed) / f"{spec.cell}.json"
            q_pre = attempt.run_manifest.q_by_cell[STATE_SPECS.index(spec)]
            created = not path.exists()
            if not created:
                cells = _load_development(
                    path, manifest=attempt.run_manifest, seed=seed,
                    state_id=spec.cell, q_pre=q_pre,
                )
            else:
                cells = []
                twins = by_state[spec.cell]
                for tape in range(8):
                    address = development_tape_address(spec.cell, tape)
                    for action in range(18):
                        evaluation = evaluate_twin_branches(
                            twins, forced_actions=(action, action),
                            evaluation_address=address, foundation_policy=policy,
                        )
                        cells.append(_development_cell(seed, twins, tape, "HR", action, evaluation, 0))
                        cells.append(_development_cell(seed, twins, tape, "RH", action, evaluation, 1))
                atomic_create_json(path, {
                    "schema": PIPELINE_SCHEMA,
                    "run_binding": attempt.run_manifest.to_dict(),
                    "seed": seed,
                    "state_id": spec.cell,
                    "realized_q_pre": q_pre,
                    "rows": [asdict(row) for row in cells],
                }, scratch_observer=scratch_observer)
                cells = tuple(cells)
            if frontier_controller is not None:
                frontier_controller.unit(
                    f"development-{seed}-{spec.cell}", created=created,
                )
            all_cells.extend(cells)
    mapping = freeze_development_mapping(all_cells)
    action_map = attempt.root / "development-action-map.json"
    if action_map.exists():
        if action_map.read_bytes() != mapping.serialized_bytes:
            raise AttemptError("persisted action map differs from complete development raw cells")
    else:
        freeze_action_map(action_map, mapping, scratch_observer=scratch_observer)
    return mapping


def _heldout_cell(seed, twins, tape, graph, arm, action, evaluation, lane) -> HeldoutCell:
    output = evaluation.outputs[lane]
    spec = next(row for row in STATE_SPECS if row.cell == twins.state_id)
    return HeldoutCell(
        seed, twins.state_id, spec.k, spec.stratum, tape, graph, arm, action,
        output.completion_value, output.terminal, output.safe_dock, output.dock_tick,
        output.timeout, _failure_labels(output), output.cumulative_reward,
        output.cumulative_energy, 364, evaluation.transitions_by_lane[lane],
        evaluation.policy_queries_by_lane[lane],
    )


def _load_heldout(
    path: Path, *, manifest: RunManifest, seed: int, state_id: str, q_pre: int,
) -> tuple[HeldoutCell, ...]:
    value = _read_json(path)
    raw = value.get("rows")
    if (
        value.get("schema") != PIPELINE_SCHEMA
        or value.get("run_binding") != manifest.to_dict()
        or value.get("seed") != seed or value.get("state_id") != state_id
        or value.get("realized_q_pre") != q_pre
        or not isinstance(raw, list)
    ):
        raise AttemptError("held-out unit artifact differs")
    try:
        rows = tuple(HeldoutCell(
            **{**row, "failures": tuple(row.get("failures", ()))},
        ) for row in raw if isinstance(row, dict))
    except TypeError as error:
        raise AttemptError("held-out unit fields differ") from error
    if len(rows) != 96 or len(raw) != len(rows):
        raise AttemptError("held-out unit inventory differs")
    return rows


def _execute_heldout(
    attempt: Attempt,
    foundations: Mapping[int, FoundationBundle],
    twins_rows: tuple[ReachableTwins, ...],
    mapping: DevelopmentMapping,
    *,
    scratch_observer: Callable[[Path], None] | None,
) -> HeldoutAnalysis:
    namespace = open_heldout_namespace(attempt.root / "development-action-map.json", mapping)
    by_state = {row.state_id: row for row in twins_rows}
    all_cells = []
    for seed in TRAINING_SEEDS:
        policy = ImmutableBatchedFoundationPolicy(freeze_foundation_actor(foundations[seed].model))
        for spec in STATE_SPECS:
            path = attempt.root / "heldout" / str(seed) / f"{spec.cell}.json"
            q_pre = attempt.run_manifest.q_by_cell[STATE_SPECS.index(spec)]
            if path.exists():
                cells = _load_heldout(
                    path, manifest=attempt.run_manifest, seed=seed,
                    state_id=spec.cell, q_pre=q_pre,
                )
            else:
                cells = []
                twins = by_state[spec.cell]
                hr = mapping.action_for(seed, spec.cell, "HR")
                rh = mapping.action_for(seed, spec.cell, "RH")
                common = mapping.common_for(seed, spec.cell)
                arms = (("MATCHED", (hr, rh)), ("SWAPPED", (rh, hr)), ("COMMON", (common, common)))
                for tape in range(16):
                    permit = namespace.address(spec.cell, tape)
                    for arm, actions in arms:
                        evaluation = evaluate_twin_branches(
                            twins, forced_actions=actions, evaluation_address=permit,
                            foundation_policy=policy,
                        )
                        cells.append(_heldout_cell(seed, twins, tape, "HR", arm, actions[0], evaluation, 0))
                        cells.append(_heldout_cell(seed, twins, tape, "RH", arm, actions[1], evaluation, 1))
                atomic_create_json(path, {
                    "schema": PIPELINE_SCHEMA,
                    "run_binding": attempt.run_manifest.to_dict(),
                    "seed": seed,
                    "state_id": spec.cell,
                    "realized_q_pre": q_pre,
                    "rows": [asdict(row) for row in cells],
                }, scratch_observer=scratch_observer)
                cells = tuple(cells)
            all_cells.extend(cells)
    analysis = analyze_heldout_panel(mapping, all_cells)
    q_by_state = {
        spec.cell: attempt.run_manifest.q_by_cell[index]
        for index, spec in enumerate(STATE_SPECS)
    }
    q_strata = {}
    for q_pre in (0, 1):
        units = tuple(row for row in analysis.tape_units if q_by_state[row.state_id] == q_pre)
        if not units:
            raise AttemptError("realized-q analysis stratum is empty")
        q_strata[str(q_pre)] = {
            "state_ids": [spec.cell for spec in STATE_SPECS if q_by_state[spec.cell] == q_pre],
            "tape_units": len(units),
            "mean_delta_swap": math.fsum(row.delta_swap for row in units) / len(units),
            "mean_delta_common": math.fsum(row.delta_common for row in units) / len(units),
        }
    analysis_value = {
        "schema": PIPELINE_SCHEMA,
        "run_binding": attempt.run_manifest.to_dict(),
        "realized_q_by_cell": q_by_state,
        "q_strata_descriptive_only": q_strata,
        "q_inference_authorized": False,
        "analysis": asdict(analysis),
    }
    path = attempt.root / "heldout-analysis.json"
    if path.exists():
        observed = _read_json(path)
        if observed != analysis_value:
            raise AttemptError("persisted held-out analysis differs from complete raw cells")
    else:
        atomic_create_json(path, analysis_value, scratch_observer=scratch_observer)
    return analysis


def _ledger(
    attempt: Attempt,
    foundations: Mapping[int, FoundationBundle],
    sources: tuple[ReachableTwins, ...],
    development: DevelopmentMapping | None,
    analysis: HeldoutAnalysis | None,
    *,
    include_source_stage: bool,
    failed_source: ReachableStatePanelNotEstablished | None = None,
) -> WorkLedger:
    ledger = WorkLedger()
    training_receipts = [
        load_checkpoint_training_receipt(_checkpoint_path(attempt.root, seed, update))
        for seed in TRAINING_SEEDS for update in range(1, 161)
    ]
    ledger.record(
        "foundation_training", missions=3_840, allocated_slots=3_840 * 364,
        transitions=sum(int(row["transitions"]) for row in training_receipts if row),
        policy_queries=sum(int(row["records"]) for row in training_receipts if row),
        optimizer_steps=3_840, evaluator_calls=0,
    )
    curves = tuple(row for bundle in foundations.values() for row in bundle.curve_rows)
    competence = tuple(row for bundle in foundations.values() for row in bundle.competence_rows)
    ledger.record(
        "fixed_learning_curves", missions=len(curves), allocated_slots=576 * 364,
        transitions=sum(row.transitions for row in curves),
        policy_queries=sum(row.policy_queries for row in curves), optimizer_steps=0,
        evaluator_calls=18,
    )
    ledger.record(
        "final_competence", missions=len(competence), allocated_slots=256 * 364,
        transitions=sum(row.transitions for row in competence),
        policy_queries=sum(row.policy_queries for row in competence), optimizer_steps=0,
        evaluator_calls=2,
    )
    if include_source_stage:
        ledger.record(
            "reachable_state_source_scans",
            missions=sum(len(row.source_scan_receipts) for row in sources)
            + (len(failed_source.receipts) if failed_source is not None else 0),
            allocated_slots=48 * 364,
            transitions=sum(row.transitions for row in sources)
            + (failed_source.transitions if failed_source is not None else 0),
            policy_queries=sum(row.policy_queries for row in sources)
            + (failed_source.policy_queries if failed_source is not None else 0),
            optimizer_steps=0, evaluator_calls=0,
        )
    if development is not None:
        ledger.record(
            "development", missions=len(development.raw_cells), allocated_slots=3_456 * 364,
            transitions=sum(row.transitions for row in development.raw_cells),
            policy_queries=sum(row.policy_queries for row in development.raw_cells),
            optimizer_steps=0, evaluator_calls=1_728,
        )
    if analysis is not None:
        ledger.record(
            "heldout", missions=len(analysis.raw_cells), allocated_slots=1_152 * 364,
            transitions=sum(row.transitions for row in analysis.raw_cells),
            policy_queries=sum(row.policy_queries for row in analysis.raw_cells),
            optimizer_steps=0, evaluator_calls=576,
        )
    return ledger


def execute_full_pipeline(
    attempt: Attempt,
    *,
    scratch_observer: Callable[[Path], None] | None = None,
    frontier_controller: FrontierController | None = None,
) -> PipelineOutcome:
    """Execute or validate every legal stage without publishing a final fact."""

    foundations = {
        seed: _execute_foundation(
            attempt, seed, scratch_observer=scratch_observer,
            frontier_controller=frontier_controller,
        )
        for seed in TRAINING_SEEDS
    }
    competence_rows = tuple(
        row for bundle in foundations.values() for row in competence_records(bundle.competence_rows)
    )
    gate = analyze_competence(competence_rows)
    gate_path = attempt.root / "foundation-competence-gate.json"
    gate_value = {"schema": PIPELINE_SCHEMA, "run_binding": attempt.run_manifest.to_dict(),
                  "gate": asdict(gate),
                  "records": [asdict(row) for row in competence_rows]}
    gate_created = not gate_path.exists()
    if not gate_created:
        if _read_json(gate_path) != gate_value:
            raise AttemptError("foundation competence gate differs from raw endpoints")
    else:
        atomic_create_json(gate_path, gate_value, scratch_observer=scratch_observer)
    if frontier_controller is not None:
        frontier_controller.unit("competence-inventory", created=gate_created)
    if not gate.passed:
        # This is a valid early scientific branch, not an engineering failure.
        ledger = _ledger(
            attempt, foundations, (), None, None, include_source_stage=False,
        )
        outcome = PipelineOutcome(
            "FOUNDATION_COMPETENCE_NOT_ESTABLISHED", ledger, 0, 320, None, False,
        )
        ledger.reconcile_for_branch(
            branch=outcome.branch, source_states=0, ppo_updates=320,
        )
        return outcome

    try:
        sources = _execute_sources(
            attempt, foundations, scratch_observer=scratch_observer,
            frontier_controller=frontier_controller,
        )
    except SourcePanelFailure as error:
        ledger = _ledger(
            attempt, foundations, error.completed, None, None,
            include_source_stage=True, failed_source=error.failure,
        )
        outcome = PipelineOutcome(
            "REACHABLE_STATE_PANEL_NOT_ESTABLISHED", ledger,
            len(error.completed), 320, None, False,
        )
        ledger.reconcile_for_branch(
            branch=outcome.branch, source_states=len(error.completed), ppo_updates=320,
        )
        return outcome
    development = _execute_development(
        attempt, foundations, sources, scratch_observer=scratch_observer,
        frontier_controller=frontier_controller,
    )
    if development.entirely_nondiscriminating:
        outcome = PipelineOutcome(
            "ACTION_CONSTRUCTION_NONDISCRIMINATING",
            _ledger(
                attempt, foundations, sources, development, None,
                include_source_stage=True,
            ), 6, 320, None, False,
        )
        outcome.ledger.reconcile_for_branch(
            branch=outcome.branch, source_states=6, ppo_updates=320,
        )
        return outcome
    analysis = _execute_heldout(
        attempt, foundations, sources, development, scratch_observer=scratch_observer,
    )
    ledger = _ledger(
        attempt, foundations, sources, development, analysis,
        include_source_stage=True,
    )
    ledger.reconcile_for_publication(source_states=6, ppo_updates=320)
    outcome = PipelineOutcome(analysis.branch, ledger, 6, 320, analysis, True)
    ledger.reconcile_for_branch(branch=analysis.branch, source_states=6, ppo_updates=320)
    return outcome


__all__ = [
    "PIPELINE_SCHEMA", "FoundationBundle", "PipelineOutcome", "ValidScientificStop",
    "execute_full_pipeline",
]
