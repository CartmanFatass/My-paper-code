"""Matched P/U32 two-order search with atomic three-tick fallback."""

from __future__ import annotations

from collections import Counter
import time

import numpy as np

from experiments.candidates.uav_radio_activation.b02.scheduler import sequential_search
from . import contract as c
from . import model
from . import protocol as p
from .randomness import model_normals


class DeadlineExceeded(Exception):
    """A completed unit of work crossed the fixed whole-decision allowance."""


class Scheduler:
    def __init__(self, arm, map_packet, world, *, horizon=c.HORIZON,
                 clock=time.perf_counter, cpu_clock=time.process_time):
        p.require(arm in c.ARMS and isinstance(world, (int, np.integer)) and world >= 0,
                  "invalid controller identity")
        p.require(isinstance(horizon, (int, np.integer)) and 8 <= horizon <= c.HORIZON
                  and horizon % c.HOLD == 0, "invalid fixed horizon")
        self.arm, self.world, self.horizon = arm, int(world), int(horizon)
        self.sites = p.decode_map(map_packet)
        self.clock, self.cpu_clock = clock, cpu_clock
        self.last_record = None

    def decide(self, own_observation, actual, proposals, tick, current_mask, nav_indices,
               loss_codes, *, started=None, cpu_started=None):
        start = self.clock() if started is None else started
        cpu_start = self.cpu_clock() if cpu_started is None else cpu_started
        p.report_tick(tick, self.horizon)
        p.mask_array(current_mask)
        actual = np.array(p.checked_commands(actual), dtype=np.float32, copy=True)
        proposals = np.array(p.checked_commands(proposals), dtype=np.float32, copy=True)
        member = (tick // c.HOLD) % c.N_UAVS
        proposal_q = p.command_index(proposals[member])
        length = min(c.HOLD, self.horizon - tick - c.DELIVERY)
        particles = 1 if self.arm == "P" else c.PARTICLES
        counts = Counter()
        record = dict(arm=self.arm, world=self.world, tick=int(tick), horizon=self.horizon,
            member=member, proposal_q=proposal_q, length=length, current_mask=int(current_mask),
            report_packets=np.empty((0, c.REPORT_BYTES), dtype=np.uint8),
            command_packet=np.empty(0, dtype=np.uint8), report_sent=False, command_sent=False,
            decoded=False, decoded_positions=np.empty((0, 3)), decoded_actual=np.empty((0, 3)),
            decoded_proposals=np.empty((0, 3)), decoded_nav=np.empty(0, dtype=np.uint8),
            decoded_losses=np.empty((0, c.N_USERS)), anchor_hash="", noise_hash="",
            noise_address=[], prefix_hashes=[], geometry_units=[], candidate_hashes=[],
            request_pairs=[], request_indices=[], computed_pairs=[], scores=[],
            selected_pair=None, selected_before_deadline=None, timely=False,
            cutoff="entry", checks=0, counts=counts, error=None)
        self.last_record = record
        phase = "entry"
        geometry, cache = {}, {}
        output_commands, output_mask = actual.copy(), int(current_mask)
        selected = None
        noise = None

        def check():
            record["checks"] += 1
            record["cutoff"] = phase
            if self.clock() - start > c.COMPUTE_SECONDS:
                raise DeadlineExceeded

        try:
            check()
            phase = "reports_encode"
            packets = p.encode_reports(own_observation, actual, proposals, tick, nav_indices, loss_codes)
            record["report_packets"] = np.array([np.frombuffer(x, np.uint8) for x in packets])
            counts["report_bytes_encoded"] += sum(map(len, packets))
            check()
            record["report_sent"] = True
            counts["report_bytes_sent"] += c.N_UAVS * c.REPORT_BYTES
            phase = "reports_decode"
            positions, actual_wire, proposed_wire, nav, decoded_losses = p.decode_reports(packets, tick)
            record.update(decoded=True, decoded_positions=positions.copy(), decoded_actual=actual_wire.copy(),
                          decoded_proposals=proposed_wire.copy(), decoded_nav=nav.copy(),
                          decoded_losses=decoded_losses.copy())
            check()
            phase = "anchor"
            counts["anchor_geometry_attempts"] += 1
            nominal = model.nominal_loss(positions, self.sites)
            mean = decoded_losses - nominal
            variance = np.zeros_like(mean)
            counts["anchor_geometry_snapshots"] += 1
            counts["anchor_geometry_link_entries"] += c.N_UAVS * c.N_USERS
            record["anchor_hash"] = p.array_digest(nominal, mean, variance)
            check()
            if self.arm == "U32":
                phase = "model_noise"
                record["noise_address"] = [c.MODEL_NAMESPACE, c.MODEL_ROOT, self.world, int(tick)]
                counts["model_normal_blocks_attempted"] += 1
                base = model_normals(self.world, int(tick))
                counts["model_normal_blocks"] += 1
                counts["model_normal_values"] += int(base.size)
                record["noise_hash"] = p.array_digest(base)
                noise = np.concatenate((base, -base), axis=0)
                counts["model_signed_normal_values"] += int(noise.size)
                residual = np.broadcast_to(mean, (particles, c.N_UAVS, c.N_USERS)).copy()
                check()
            else:
                residual = None
            position = positions.copy()
            for offset in range(c.DELIVERY):
                phase = "prefix"
                check()
                counts["prefix_updates_attempted"] += 1
                position, rho = model.move(position, actual_wire)
                if self.arm == "P":
                    mean, variance = model.moments_step(mean, variance, rho)
                    digest = p.array_digest(position, rho, mean, variance)
                else:
                    residual = model.particles_step(residual, rho, noise[:, offset])
                    digest = p.array_digest(position, rho, residual)
                counts["prefix_kinematic_ticks"] += 1
                counts["prefix_conditional_fleet_updates"] += particles
                record["prefix_hashes"].append(digest)
                check()
            prefix_position = position.copy()
            prefix_mean, prefix_variance = mean.copy(), variance.copy()
            prefix_residual = None if residual is None else residual.copy()
            weights = np.array([c.payload_weight(tick + c.DELIVERY + k) for k in range(length)])

            def score(q, mask):
                nonlocal phase
                record["request_pairs"].append((int(q), int(mask)))
                record["request_indices"].append(-1)
                counts["candidate_requests"] += 1
                if (q, mask) in cache:
                    counts["candidate_cache_hits"] += 1
                    index = cache[q, mask]
                    record["request_indices"][-1] = index
                    return record["scores"][index]
                counts["candidate_uncached_requests"] += 1
                if q not in geometry:
                    geometry[q] = []
                    command = proposed_wire.copy()
                    command[member] = p.COMMANDS[q]
                    at = prefix_position.copy()
                    mu, var = prefix_mean.copy(), prefix_variance.copy()
                    z = None if prefix_residual is None else prefix_residual.copy()
                    for slot in range(length):
                        phase = "candidate_geometry"
                        check()
                        counts["candidate_geometry_attempts"] += 1
                        at, rho = model.move(at, command)
                        nominal = model.nominal_loss(at, self.sites)
                        if self.arm == "P":
                            mu, var = model.moments_step(mu, var, rho)
                            losses = model.expected_loss(nominal, mu, var)[None, :, :]
                            digest = p.array_digest(at, rho, nominal, mu, var, losses)
                        else:
                            z = model.particles_step(z, rho, noise[:, c.DELIVERY + slot])
                            losses = nominal[None, :, :] + z
                            digest = p.array_digest(at, rho, nominal, z, losses)
                        geometry[q].append(losses)
                        record["geometry_units"].append((int(q), slot, digest))
                        counts["candidate_kinematic_ticks"] += 1
                        counts["candidate_geometry_snapshots"] += 1
                        counts["candidate_geometry_link_entries"] += c.N_UAVS * c.N_USERS
                        counts["candidate_conditional_fleet_updates"] += particles
                        check()
                phase = "candidate_radio"
                check()
                losses = np.stack(geometry[q], axis=0).reshape(length * particles, c.N_UAVS, c.N_USERS)
                counts["candidate_batch_attempts"] += 1
                native, sinr, assigned = model.native_batch(losses, int(mask))
                counts["candidate_batch_calls"] += 1
                counts["candidate_fleet_scores"] += length * particles
                counts["candidate_sinr_entries"] += length * particles * c.N_UAVS * c.N_USERS
                native = native.reshape(length, particles, 3)
                # Average particles at each tick, then the payload-weighted block.
                value = np.mean(np.mean(native, axis=1) * weights[:, None], axis=0)
                index = len(record["computed_pairs"])
                record["computed_pairs"].append((int(q), int(mask)))
                record["scores"].append(value)
                record["candidate_hashes"].append(p.array_digest(native, sinr, assigned))
                cache[q, mask] = index
                record["request_indices"][-1] = index
                counts["candidate_plans"] += 1
                check()
                return value

            phase = "search"
            selected = sequential_search(score, int(current_mask), proposal_q)
            record["selected_before_deadline"] = tuple(map(int, selected))
            phase = "search_complete"
            check()
            phase = "command_encode"
            packet = p.encode_command(selected[1], member, selected[0], tick)
            record["command_packet"] = np.frombuffer(packet, dtype=np.uint8).copy()
            counts["command_bytes_encoded"] += len(packet)
            received_mask, received_member, received_q = p.decode_command(packet, tick)
            pending_commands = proposed_wire.copy()
            pending_commands[received_member] = p.COMMANDS[received_q]
            check()
            output_commands, output_mask = pending_commands.astype(np.float32), int(received_mask)
        except DeadlineExceeded:
            selected = None
        except Exception as exc:
            record["error"] = {"type": type(exc).__name__, "message": str(exc)}
            raise
        finally:
            # Record finalization is manager work and precedes the last deadline check.
            record["request_pairs"] = np.asarray(record["request_pairs"], dtype=np.int64).reshape(-1, 2)
            record["request_indices"] = np.asarray(record["request_indices"], dtype=np.int64)
            record["computed_pairs"] = np.asarray(record["computed_pairs"], dtype=np.int64).reshape(-1, 2)
            record["scores"] = np.asarray(record["scores"], dtype=np.float64).reshape(-1, 3)
            # Construct BOTH atomic outcomes before classifying the deadline. The
            # final boundary performs only pointer/scalar assignments; array copies,
            # count materialization and output dictionaries are inside the budget.
            attempted = int(counts["report_bytes_encoded"] + counts["command_bytes_encoded"])
            fallback_commands = actual.copy()
            fallback_record = dict(record, timely=False, selected_pair=None,
                executed_commands=fallback_commands.copy(), executed_mask=int(current_mask),
                attempted_bytes=attempted, sent_bytes=int(counts["report_bytes_sent"]),
                counts=dict(counts), wall_seconds=0., cpu_seconds=0.)
            fallback = dict(commands=fallback_commands, mask=int(current_mask),
                            timely=False, record=fallback_record)
            selected_tuple = None if selected is None else tuple(map(int, selected))
            success_counts = dict(counts)
            success_counts["command_bytes_sent"] = c.COMMAND_BYTES
            success_record = dict(record, timely=True, selected_pair=selected_tuple,
                command_sent=True, executed_commands=output_commands.copy(), executed_mask=output_mask,
                attempted_bytes=attempted, sent_bytes=int(counts["report_bytes_sent"] + c.COMMAND_BYTES),
                counts=success_counts, wall_seconds=0., cpu_seconds=0.)
            success = dict(commands=output_commands, mask=output_mask, timely=True, record=success_record)
            cpu_elapsed = self.cpu_clock() - cpu_start
            elapsed = self.clock() - start
            result = (success if selected is not None and record["error"] is None
                      and elapsed <= c.COMPUTE_SECONDS else fallback)
            result["record"]["wall_seconds"] = elapsed
            result["record"]["cpu_seconds"] = cpu_elapsed
            self.last_record = result["record"]
        return result
