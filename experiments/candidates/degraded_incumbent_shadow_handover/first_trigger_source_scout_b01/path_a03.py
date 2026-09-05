"""Ordinary paired-host observation, adoption, proposal and consequence measurements."""

from collections import Counter
import json
import math
import time

import numpy as np
import torch

from . import study
from .native_a03 import HOSTS, PointBatch, load_host
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_backend as backend
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, RecurrentRolloutState,
)

MAX_TICKS = 1_200
HOST_CAP = 300.0
PAIR_CAP = 600.0
EVENTS = (
    "camera_u0", "camera_u1", "source_u0_adoption", "source_u1_adoption", "common_source",
    "snapshot_delivery", "readiness_delivery", "snapshot_accepted", "readiness_accepted",
    "version_ready", "renewal", "prepare", "commit", "latch", "intent_emitted",
    "intent_certificate", "origin_valid", "legal_transfer", "relay_emitted", "base_adoption",
    "service", "service_before_transfer", "service_at_or_after_transfer",
    "service_after_transfer_old_or_other_packet", "qualified_service", "terminal",
    "invalid_commit", "separation_breach", "command_slew_breach", "token_gap",
    "dual_owner", "dual_payload", "buffer_clear",
)


def state_values(s):
    scalars = (
        "tick", "terminal", "owner", "actuator_owner", "service_epoch", "initial_owner",
        "next_payload_sequence", "k_epoch", "countdown", "prepare_latched", "warmup",
        "pending_source_exists", "pending_source_sequence", "pending_source_tick",
        "pending_relay_exists", "pending_relay_sender", "pending_relay_tick",
        "pending_relay_source_sequence", "pending_relay_source_tick",
        "base_exists", "base_source_sequence", "base_source_tick", "base_relay_tick",
        "pending_snapshot", "pending_snapshot_tick", "snapshot_accepted", "snapshot_tick",
        "pending_readiness", "pending_readiness_tick", "readiness_accepted", "readiness_tick",
        "readiness_snapshot_tick", "pending_intent", "intent_owner", "intent_origin_tick",
        "intent_certificate", "intent_readiness_tick", "intent_snapshot_tick", "intent_epoch",
        "intent_next_sequence", "intent_k_epoch", "application_reason", "cas_applied",
        "invalid_commit", "service_ticks", "separation_breach", "command_slew_breach",
        "token_gap", "dual_owner", "dual_payload", "buffer_clear", "handover_used",
    )
    arrays = (
        "p", "v", "a", "battery", "filter_mean", "filter_covariance", "source_exists",
        "source_sequence", "source_tick", "pending_source_margin", "lineage_lock", "lineage_sequence",
        "accepted_readiness_candidate",
    )
    return {
        **{name: int(getattr(s, name)) for name in scalars},
        **{name: list(getattr(s, name)) for name in arrays},
        "pending_relay_first_margin": s.pending_relay_first_margin,
        "pending_relay_second_margin": s.pending_relay_second_margin,
        "pending_intent_margin": s.pending_intent_margin,
        "base_first_margin": s.base_first_margin, "base_second_margin": s.base_second_margin,
        "total_energy": s.total_energy, "min_separation": s.min_separation,
        "separation": math.hypot(s.p[0] - s.p[2], s.p[1] - s.p[3]),
        "source_age_ticks": [s.tick - s.source_tick[i] if s.source_exists[i] else None for i in range(2)],
        "base_source_age_ticks": s.tick - s.base_source_tick if s.base_exists else None,
        "base_relay_age_ticks": s.tick - s.base_relay_tick if s.base_exists else None,
    }


def source_key(s, i):
    return s.source_exists[i], s.source_sequence[i], s.source_tick[i]


def base_key(s):
    return s.base_exists, s.base_source_sequence, s.base_source_tick, s.base_relay_tick


class PathCounts:
    def __init__(self):
        self.counts = dict.fromkeys(EVENTS, 0)
        self.first = dict.fromkeys(EVENTS)
        self.base_sender = None
        self.transfer_tick = None
        self.promoted_owner = None
        self.inspected = 0
        self.completed = 0
        self.live = 0
        self.reasons = Counter()

    def add(self, event, tick, present=True, amount=1):
        if present:
            self.counts[event] += amount
            if self.first[event] is None:
                self.first[event] = tick

    def arrivals(self, before, prepared):
        s = prepared.state
        t = int(s.tick)
        self.inspected += 1
        live = not bool(s.terminal)
        self.live += int(live)
        adopted = [bool(live and s.source_exists[i] and source_key(before, i) != source_key(s, i))
                   for i in range(2)]
        base_adopted = bool(live and s.base_exists and base_key(before) != base_key(s))
        if base_adopted:
            self.base_sender = int(before.pending_relay_sender)
        for i in range(2):
            self.add(f"camera_u{i}", t, live and bool(prepared.physics.camera_present[i]))
            self.add(f"source_u{i}_adoption", t, adopted[i])
        for name, present in {
            "common_source": live and s.source_exists[0] and s.source_exists[1]
                             and s.source_sequence[0] == s.source_sequence[1],
            "snapshot_delivery": prepared.snapshot_delivered,
            "readiness_delivery": prepared.readiness_delivered,
            "snapshot_accepted": live and s.snapshot_accepted,
            "readiness_accepted": live and s.readiness_accepted,
            "version_ready": live and s.readiness_accepted and s.readiness_tick == t - 1
                             and s.readiness_snapshot_tick == s.snapshot_tick,
            "origin_valid": prepared.origin_valid, "base_adoption": base_adopted,
            "terminal": not live,
        }.items():
            self.add(name, t, present)
        return {"source_adopted": adopted, "base_adopted": base_adopted,
                "adopted_base_sender": self.base_sender,
                "common_source": bool(s.source_exists[0] and s.source_exists[1]
                                      and s.source_sequence[0] == s.source_sequence[1]),
                "version_ready": bool(s.readiness_accepted and s.readiness_tick == t - 1
                                      and s.readiness_snapshot_tick == s.snapshot_tick),
                "renewal": bool(prepared.observation.renew)}

    def completion(self, prepared, rows, after, output):
        s = prepared.state
        t = int(s.tick)
        self.completed += 1
        renew = bool(prepared.observation.renew)
        legal = bool(output["cas_applied"][0] and after.owner == 1 - s.owner
                     and after.actuator_owner == after.owner and after.service_epoch == s.service_epoch + 1)
        if legal:
            self.transfer_tick = t
            self.promoted_owner = int(after.owner)
        service = bool(output["service"][0])
        post_transfer = self.transfer_tick is not None
        qualified = bool(service and post_transfer and after.base_exists
                         and after.base_relay_tick >= self.transfer_tick
                         and self.base_sender == self.promoted_owner)
        for name, present in {
            "renewal": renew, "prepare": renew and rows["prepare"][0, s.owner],
            "commit": renew and rows["commit"][0, s.owner], "latch": after.prepare_latched,
            "intent_emitted": after.pending_intent and after.intent_origin_tick == t,
            "intent_certificate": after.pending_intent and after.intent_origin_tick == t and after.intent_certificate,
            "legal_transfer": legal, "relay_emitted": after.pending_relay_exists and after.pending_relay_tick == t,
            "service": service, "service_before_transfer": service and not post_transfer,
            "service_at_or_after_transfer": service and post_transfer,
            "service_after_transfer_old_or_other_packet": service and post_transfer and not qualified,
            "qualified_service": qualified, "terminal": after.terminal,
        }.items():
            self.add(name, t, present)
        for name in ("invalid_commit", "separation_breach", "command_slew_breach",
                     "token_gap", "dual_owner", "dual_payload", "buffer_clear"):
            delta = int(getattr(after, name)) - int(getattr(s, name))
            self.add(name, t, delta != 0, delta)
        self.reasons[int(output["application_reason"][0])] += 1
        return {"legal_transfer": legal, "service": service, "qualified_service": qualified,
                "base_sender": self.base_sender, "transfer_tick": self.transfer_tick,
                "promoted_owner": self.promoted_owner}


def read_rule(counts):
    access = ("camera_u0", "camera_u1", "source_u0_adoption", "source_u1_adoption", "common_source")
    downstream = ("snapshot_delivery", "readiness_delivery", "origin_valid", "legal_transfer")
    absent = [key for key in access if not counts[key]]
    if absent:
        result = "A03-ACCESS-NOT-RESTORED"
    else:
        absent = [key for key in downstream if not counts[key]]
        if absent:
            result = "A03-DOWNSTREAM-STAGE-GAP"
        elif not counts["qualified_service"]:
            result, absent = "A03-CONSEQUENCE-NOT-REACHED", ["qualified_service"]
        else:
            result = "A03-BOUNDED-PATH-QUALIFIED"
    return {"result": result, "absent_stages": absent, "earliest_absent_stage": absent[0] if absent else None}


def parameters(model):
    return {name: value.detach().to(torch.float64).clone() for name, value in model.named_parameters()}


def displacement(before, model):
    after = parameters(model)
    initial = math.sqrt(sum(float(value.square().sum()) for value in before.values()))
    final = math.sqrt(sum(float(value.square().sum()) for value in after.values()))
    moved = math.sqrt(sum(float((after[name] - value).square().sum()) for name, value in before.items()))
    return {"initial_norm": initial, "final_norm": final, "l2_displacement": moved,
            "relative_displacement": moved / initial}


def run_host(host, reset, checkpoint, stream, pair_deadline):
    started = time.perf_counter()
    deadline = min(started + HOST_CAP, pair_deadline)
    native = PointBatch(load_host(host), reset)
    policy = BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=checkpoint,
                                   state=RecurrentRolloutState.fresh("STRUCTURED", width=1))
    before_parameters = parameters(policy.model)
    counts = PathCounts()
    publication_seconds = 0.0
    for _ in range(MAX_TICKS):
        if time.perf_counter() >= deadline:
            raise RuntimeError("incomplete A03: host/pair time cap reached")
        before = native.state_copy()
        prepared = native.prepare_b01_tick()
        p = backend._B01PreparedTick.from_buffer_copy(prepared.snapshot_bytes())
        observation = prepared.observe()
        arrival = counts.arrivals(before, p)
        tick = int(p.state.tick)
        record = {
            "host": host, "action_tick": tick, "before_prepare": state_values(before),
            "prepared": state_values(p.state), "arrivals": arrival,
            "physics": {"camera_present": list(p.physics.camera_present), "radio_margins": list(p.physics.radio),
                        "send_margin_eligible": [m >= 6 for m in p.physics.radio],
                        "source_xy": [p.physics.gx, p.physics.gy]},
            "actor_raw": observation["actor"].tolist(), "actor_normalized": None,
            "snapshot_delivery_mask": observation["snapshot_delivery_mask"].tolist(),
            "snapshot_input": observation["snapshot_payload"].tolist(),
            "readiness_delivery_mask": observation["readiness_delivery_mask"].tolist(),
            "origin_valid": bool(p.origin_valid), "policy_output": None, "completion": None,
        }
        if not p.state.terminal:
            policy.prepare_recurrent(observation)
            record["actor_normalized"] = policy.normalized_actor(observation).tolist()
            rows = policy.step_rows(observation, sampler=study._DeterministicSampler(), global_tick=tick,
                                    deterministic=True, recurrent_prepared=True)
            owner_before = np.asarray(observation["owner"], dtype=np.int64)
            output = native.complete_b01_tick(prepared, rows)
            policy.apply_native_promotion(owner_before=owner_before, step_rows=rows, observation_after=output)
            after = native.state_copy()
            record["policy_output"] = {name: rows[name][0].tolist() for name in (
                "raw_action", "prepare", "commit", "prediction_mean", "prediction_covariance", "service_q",
            )}
            record["completion"] = {"native": state_values(after),
                                    **counts.completion(p, rows, after, output)}
        write_started = time.perf_counter()
        stream.write(json.dumps(record, sort_keys=True) + "\n")
        publication_seconds += time.perf_counter() - write_started
        if p.state.terminal or after.terminal:
            break
    write_started = time.perf_counter()
    stream.flush()
    publication_seconds += time.perf_counter() - write_started
    movement = displacement(before_parameters, policy.model)
    if movement["l2_displacement"] != 0:
        raise RuntimeError("incomplete A03: retained policy parameters changed")
    wall = time.perf_counter() - started
    if time.perf_counter() >= deadline:
        raise RuntimeError("incomplete A03: host/pair time cap reached")
    final = native.state_copy()
    return {"host": host, "counts": counts.counts, "first_action_tick": counts.first,
            "inspected_boundaries": counts.inspected, "live_boundaries": counts.live,
            "completed_ticks": counts.completed, "final_native_tick": int(final.tick),
            "stop": "native_terminal" if final.terminal or p.state.terminal else "tick_limit",
            "stop_boundary": "prepared" if p.state.terminal else "completion",
            "application_reason_histogram": dict(counts.reasons), "parameter_change": movement,
            "final_state": state_values(final), "wall_seconds": wall,
            "trace_serialization_write_seconds": publication_seconds,
            "seconds_per_completed_tick": wall / counts.completed if counts.completed else None,
            **read_rule(counts.counts)}


def run_pair(checkpoint, output):
    started = time.perf_counter()
    torch.set_num_threads(1)
    coordinate = study.panel()[0]
    reset = study._reset_row(study.seed_master(11), coordinate)
    output.mkdir(parents=True)
    with (output / "trace.jsonl").open("w", encoding="utf-8") as stream:
        hosts = [run_host(host, reset, checkpoint, stream, started + PAIR_CAP) for host in HOSTS]
    return {"object": "DISH-GROUND-ENDPOINT-PATH-A03", "seed": 11,
            "coordinate": coordinate.canonical_key(), "hosts": hosts,
            "result": hosts[1]["result"],
            "candidate_minus_literal": {key: hosts[1]["counts"][key] - hosts[0]["counts"][key] for key in EVENTS},
            "new_exposure": {"policy_initializations": 2, "model_initializations": 2,
                             "optimizer_initializations": 0, "training_transitions": 0,
                             "learner_updates": 0, "optimizer_steps": 0,
                             "prepared_ticks": sum(h["inspected_boundaries"] for h in hosts),
                             "completed_ticks": sum(h["completed_ticks"] for h in hosts)},
            "inherited_exposure": {"training_transitions": 262_144, "updates": 64, "optimizer_steps": 2_048,
                                   "initial_norm": 38.19731474061207, "retained_norm": 41.78517869974931,
                                   "relative_displacement": 0.42465718774783356},
            "wall_seconds": time.perf_counter() - started}
