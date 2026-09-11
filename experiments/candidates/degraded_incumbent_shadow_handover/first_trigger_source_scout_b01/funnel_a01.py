"""Read-only stage counts on the original retained-checkpoint prefix path."""

from collections import Counter
import math
import time

import numpy as np
import torch

from .study import _DeterministicSampler, _reset_row, panel, seed_master
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    _B01PreparedTick, _State, native_batch_from_rows,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_evaluator import prepare_b01_application
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, RecurrentRolloutState,
)

OBJECT = "DISH-PREFIX-TRIGGER-FUNNEL-A01"
PREFIX_TICKS = 1_200
CAP_SECONDS = 600.0
REFERENCE = {"seed": 11, "rows": 16, "triggered_rows": 0, "completed_ticks": 19_200}
INPUT_SOURCE = "e0541d0cb3e9e63731c72f4dacb10b44d268fd39"
INPUT_SHA256 = "0020137d98e23f06a71048daf5906d7835545fd38cc8a1399bbeee15e11df4fa"
EVENTS = (
    "live", "terminal_padding", "live_renewal", "prepare_proposal", "commit_proposal",
    "prepared_latch", "completion_latch", "common_source", "snapshot_delivery",
    "readiness_delivery", "snapshot_accepted", "readiness_accepted", "version_ready",
    "version_ready_renewal", "version_ready_renewal_completion_latch",
    "version_ready_renewal_completion_latch_commit", "prepare_with_prepared_latch",
    "prepare_with_version_ready", "commit_with_prepared_latch", "commit_with_version_ready",
    "pending_prepared", "pending_low_margin", "pending_high_margin",
    "pending_low_margin_certificate", "pending_low_margin_no_certificate",
    "pending_high_margin_certificate", "pending_high_margin_no_certificate",
    "intent_emitted", "origin_valid", "cas_applied", "service", "invalid_commit",
    "terminal",
)


def compact_state(state: _State, action_tick: int, boundary: str) -> dict:
    """Copy only times, identity, support and physical facts needed for first occurrences."""
    names = (
        "tick", "owner", "actuator_owner", "terminal", "prepare_latched", "warmup",
        "snapshot_accepted", "snapshot_tick", "readiness_accepted", "readiness_tick",
        "readiness_snapshot_tick", "pending_intent", "intent_origin_tick",
        "intent_readiness_tick", "intent_snapshot_tick", "intent_certificate",
        "intent_owner", "intent_epoch", "service_epoch", "k_epoch", "intent_k_epoch",
        "next_payload_sequence", "intent_next_sequence", "application_reason", "cas_applied",
    )
    return {
        "action_tick": action_tick, "boundary": boundary,
        **{name: int(getattr(state, name)) for name in names},
        "standby": 1 - int(state.owner),
        "copy_order": ["U0-I", "U0-S", "U1-I", "U1-S"],
        "source_exists": list(state.source_exists), "source_sequence": list(state.source_sequence),
        "source_tick": list(state.source_tick), "pending_intent_margin": state.pending_intent_margin,
        "battery": list(state.battery), "min_separation": state.min_separation,
        "separation": math.hypot(state.p[0] - state.p[2], state.p[1] - state.p[3]),
    }


def row_label(counts: dict, triggered: bool) -> tuple[str, str | None]:
    if triggered:
        return "APPLICATION_VALID", None
    if not counts["live_renewal"]:
        return "NO_LIVE_RENEWAL", None
    if not counts["prepare_proposal"]:
        return "NO_PREPARE_PROPOSAL", None
    for name, present in (
        ("latch", counts["prepared_latch"] + counts["completion_latch"]),
        ("snapshot_delivery", counts["snapshot_delivery"]),
        ("version_ready", counts["version_ready"]),
    ):
        if not present:
            return "PREPARATION_SUPPORT_GAP", name
    if not counts["commit_proposal"]:
        return "NO_COMMIT_PROPOSAL", None
    if not counts["intent_emitted"]:
        return "NO_EMITTED_INTENT", None
    return "PENDING_INTENT_NOT_APPLICATION_VALID", None


class PrefixCounts:
    """A01's two fixed observation boundaries; never writes into native or policy state."""

    def __init__(self):
        self.counts = dict.fromkeys(EVENTS, 0)
        self.first = dict.fromkeys(EVENTS)
        self.inspected = 0
        self.completed = 0
        self.maximum_warmup = 0
        self.reasons = Counter()

    def record(self, event, present, state, tick, boundary, amount=1):
        if present:
            self.counts[event] += amount
            if self.first[event] is None:
                self.first[event] = compact_state(state, tick, boundary)

    def prepared(self, prepared):
        s = prepared.state
        t = int(s.tick)
        self.inspected += 1
        live = not bool(s.terminal)
        renew = live and bool(prepared.observation.renew)
        version = bool(s.readiness_accepted and s.readiness_tick == t - 1
                       and s.readiness_snapshot_tick == s.snapshot_tick)
        common = bool(s.source_exists[0] and s.source_exists[1]
                      and s.source_sequence[0] == s.source_sequence[1])
        next_intent = bool(s.pending_intent and t == s.intent_origin_tick + 1)
        observations = {
            "live": live, "terminal_padding": not live,
            "terminal": not live and self.first["terminal"] is None,
            "live_renewal": renew, "prepared_latch": live and bool(s.prepare_latched),
            "common_source": live and common, "snapshot_delivery": bool(prepared.snapshot_delivered),
            "readiness_delivery": bool(prepared.readiness_delivered),
            "snapshot_accepted": live and bool(s.snapshot_accepted),
            "readiness_accepted": live and bool(s.readiness_accepted),
            "version_ready": live and version, "version_ready_renewal": renew and version,
            "pending_prepared": next_intent, "origin_valid": bool(prepared.origin_valid),
        }
        if next_intent:
            margin = "low" if s.pending_intent_margin < 6.0 else "high"
            certificate = "certificate" if s.intent_certificate else "no_certificate"
            observations[f"pending_{margin}_margin"] = True
            observations[f"pending_{margin}_margin_{certificate}"] = True
        for event, present in observations.items():
            self.record(event, present, s, t, "prepared")
        if live:
            self.maximum_warmup = max(self.maximum_warmup, int(s.warmup))
        return live, renew, version

    def completion(self, prepared, rows, state, output, live, renew, version):
        s = prepared.state
        t = int(s.tick)
        self.completed += 1
        prepare = renew and bool(rows["prepare"][0, s.owner])
        commit = renew and bool(rows["commit"][0, s.owner])
        for event, present in {
            "prepare_proposal": prepare, "commit_proposal": commit,
            "prepare_with_prepared_latch": prepare and bool(s.prepare_latched),
            "prepare_with_version_ready": prepare and version,
            "commit_with_prepared_latch": commit and bool(s.prepare_latched),
            "commit_with_version_ready": commit and version,
        }.items():
            self.record(event, present, s, t, "policy_output")
        latch = live and bool(state.prepare_latched)
        for event, present in {
            "completion_latch": latch,
            "version_ready_renewal_completion_latch": renew and version and latch,
            "version_ready_renewal_completion_latch_commit": commit and version and latch,
            "intent_emitted": live and bool(state.pending_intent) and state.intent_origin_tick == t,
            "cas_applied": bool(output["cas_applied"][0]),
            "service": bool(output["service"][0]),
            "terminal": bool(state.terminal) and self.first["terminal"] is None,
        }.items():
            self.record(event, present, state, t, "completion")
        delta = int(state.invalid_commit) - int(s.invalid_commit)
        self.record("invalid_commit", delta != 0, state, t, "completion", delta)
        self.reasons[int(output["application_reason"][0])] += 1
        if live:
            self.maximum_warmup = max(self.maximum_warmup, int(state.warmup))

    def result(self):
        triggered = bool(self.counts["origin_valid"])
        label, missing = row_label(self.counts, triggered)
        return {
            "triggered": triggered, "label": label, "missing_stage": missing,
            "inspected_boundaries": self.inspected, "completed_ticks": self.completed,
            "counts": self.counts, "first_occurrences": self.first,
            "maximum_warmup": self.maximum_warmup,
            "application_reason_histogram": dict(self.reasons),
        }


def trace_prefix(native, policy, *, max_ticks: int, deadline: float) -> dict:
    counts = PrefixCounts()
    sampler = _DeterministicSampler()
    for tick in range(max_ticks):
        if time.perf_counter() >= deadline:
            raise RuntimeError("incomplete A01: 600-second diagnostic cap reached")
        prepared, observation, _ = prepare_b01_application(native=native, policy=policy)
        copied = _B01PreparedTick.from_buffer_copy(prepared.snapshot_bytes())
        live, renew, version = counts.prepared(copied)
        if bool(prepared.origin_valid[0]):
            break
        rows = policy.step_rows(
            observation, sampler=sampler, global_tick=tick,
            deterministic=True, recurrent_prepared=True,
        )
        owner_before = np.asarray(observation["owner"], dtype=np.int64)
        after = native.complete_b01_tick(prepared, rows)
        policy.apply_native_promotion(owner_before=owner_before, step_rows=rows, observation_after=after)
        state = _State.from_buffer_copy(native.snapshot_bytes())
        counts.completion(copied, rows, state, after, live, renew, version)
    return counts.result()


def parameter_change(before, model) -> dict:
    norm_sq = displacement_sq = 0.0
    for name, final in model.named_parameters():
        initial = before[name].to(torch.float64)
        norm_sq += float(initial.square().sum())
        displacement_sq += float((final.detach().to(torch.float64) - initial).square().sum())
    return {"initial_norm": math.sqrt(norm_sq), "l2_displacement": math.sqrt(displacement_sq),
            "relative_displacement": math.sqrt(displacement_sq / norm_sq)}


def run_funnel(checkpoint: bytes) -> dict:
    started = time.perf_counter()
    deadline = started + CAP_SECONDS
    torch.set_num_threads(1)
    master = seed_master(11)
    rows = []
    changes = []
    for coordinate in panel():
        native = native_batch_from_rows((_reset_row(master, coordinate),))
        policy = BatchedRecurrentPolicy(
            arm="STRUCTURED", checkpoint_bytes=checkpoint,
            state=RecurrentRolloutState.fresh("STRUCTURED", width=1),
        )
        before = {name: value.detach().clone() for name, value in policy.model.named_parameters()}
        row = trace_prefix(native, policy, max_ticks=PREFIX_TICKS, deadline=deadline)
        rows.append({
            "coordinate": coordinate.canonical_key(), "package": coordinate.regime,
            "schedule": coordinate.schedule, "speed": coordinate.route_speed,
            "slot": coordinate.within_speed_slot, "initial_owner": coordinate.initial_owner,
            "original_trigger_reference": False, **row,
        })
        changes.append(parameter_change(before, policy.model))
    completed = sum(row["completed_ticks"] for row in rows)
    triggered = sum(row["triggered"] for row in rows)
    reference_match = len(rows) == 16 and completed == 19_200 and triggered == 0
    wall = time.perf_counter() - started
    return {
        "object": OBJECT, "seed": 11, "rows": rows, "reference": REFERENCE,
        "reference_match": reference_match,
        "result": "A01-PREFIX-FUNNEL-OBSERVED" if reference_match else "A01-REPLAY-DISCREPANCY",
        "observed_reference": {"rows": len(rows), "triggered_rows": triggered, "completed_ticks": completed},
        "label_counts": dict(Counter(row["label"] for row in rows)),
        "new_exposure": {"training_transitions": 0, "learner_updates": 0, "optimizer_steps": 0,
                         "parameter_change_by_row": changes,
                         "maximum_l2_displacement": max(row["l2_displacement"] for row in changes)},
        "inherited_exposure": {"optimizer_steps": 2_048, "initial_norm": 38.19731474061207,
                               "final_norm": 41.78517869974931, "relative_displacement": 0.42465718774783356},
        "wall_seconds": wall,
        "measured_cost": {"completed_prefix_ticks": completed, "wall_seconds": wall,
                          "seconds_per_completed_tick": wall / completed if completed else None},
    }
