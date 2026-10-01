"""Independent executed-candidate audit of two expected-power packages.

The original scalar native radio/allocator checks every computed candidate. Partial
records stop at their actual completed unit; no model noise or native transition is used.
"""
from __future__ import annotations
from collections import Counter
import numpy as np
from envs.pettingzoo.uav_radio import (free_space_user_path_loss,
    user_sinr_from_path_loss,greedy_connection_assignment,service_metrics)
from experiments.candidates.uav_radio_uncertainty.b01.read_model import (
    _move, _conditional, _losses, _audit_search,
)
from . import contract as c
from . import protocol as p


def verify_decision(record, sites, counts):
    arm,tick,world = record["arm"],int(record["tick"]),int(record["world"])
    assert arm in c.ARMS and record["error"] is None
    full = arm == "P_FULL"
    particles = 1
    delivery, report_size, deadline = (3,75,1.336) if full else (2,25,1.436)
    length = min(4,int(record["horizon"])-tick-delivery)
    settings = dict(delivery=delivery,compute_seconds=deadline,report_bytes=report_size,
        round_bytes=5*report_size+16,pilot_slots=50 if full else 0,
        pilot_seconds=.1 if full else 0.,payload_report_weight=.9 if full else 1.)
    for key,value in settings.items():
        assert record[key] == value, key
    assert record["effective_tick"] == tick+delivery
    assert record["communication_seconds"] == (5*report_size+16)*8/2000
    assert record["acquisition_seconds"] == (.1 if full else 0.)
    assert not record["noise_hash"] and not record["noise_address"]
    assert record["finalization_started"]
    assert record["length"] == length and record["member"] == (tick//4)%5
    expected = Counter()
    packet_bytes = np.asarray(record["report_packets"],np.uint8)
    expected["report_bytes_encoded"] = packet_bytes.size
    expected["report_bytes_sent"] = 5*report_size if record["report_sent"] else 0
    expected["command_bytes_encoded"] = np.asarray(record["command_packet"]).size
    expected["command_bytes_sent"] = 16 if record["command_sent"] else 0
    assert packet_bytes.shape in ((0,report_size),(5,report_size))
    assert not record["report_sent"] or packet_bytes.shape == (5,report_size)
    assert bool(record["command_sent"]) == bool(record["timely"])
    assert record["attempted_bytes"] == expected["report_bytes_encoded"]+expected["command_bytes_encoded"]
    assert record["sent_bytes"] == expected["report_bytes_sent"]+expected["command_bytes_sent"]
    assert bool(record["timely"]) == (record["wall_seconds"]<=deadline)
    if full and len(packet_bytes):
        expected["report_loss_codes_encoded"] = 250
    position = state = None
    if record["decoded"]:
        assert record["report_sent"]
        decoded = p.decode_reports(arm,tuple(row.tobytes() for row in packet_bytes),tick)
        for key,value in zip(("decoded_positions","decoded_actual","decoded_proposals","decoded_nav"),decoded[:4]):
            np.testing.assert_array_equal(record[key],value)
        if full:
            np.testing.assert_array_equal(record["decoded_losses"],decoded[4])
            expected["report_loss_codes_decoded"] = 250
        else:
            assert decoded[4] is None
            assert np.asarray(record["decoded_losses"]).shape == (0,50)
        position,actual,proposed,_,loss = decoded
        assert record["proposal_q"] == p.command_index(proposed[record["member"]])
    else:
        assert not record["anchor_hash"] and not record["prior_hash"]
        assert not record["prior_initialized"]
    if record["anchor_hash"]:
        assert full and record["decoded"] and not record["prior_initialized"]
        counts["reference_anchor_geometry_attempts"] += 1
        nominal = free_space_user_path_loss(position,sites,2.e9)
        counts.update(reference_anchor_geometry_snapshots=1,reference_anchor_link_entries=250)
        mean,variance = loss-nominal,np.zeros_like(loss)
        assert p.array_digest(nominal,mean,variance) == record["anchor_hash"]
        state = (mean,variance)
        expected.update(anchor_geometry_attempts=1,anchor_geometry_snapshots=1,anchor_geometry_link_entries=250)
    if full:
        assert not record["prior_initialized"] and not record["prior_hash"]
    else:
        assert not record["anchor_hash"]
        assert np.asarray(record["decoded_losses"]).shape == (0,50)
        assert bool(record["prior_hash"]) == bool(record["prior_initialized"])
        if record["prior_initialized"]:
            assert record["decoded"]
            # Exact stationary reference, not a posterior from adaptive history.
            mean,variance = np.zeros((5,50),np.float64),np.full((5,50),4.14**2,np.float64)
            assert p.array_digest(mean,variance) == record["prior_hash"]
            state = (mean,variance)
            expected.update(prior_initializations=1,prior_initialized_link_pairs=250)
            counts.update(reference_prior_initializations=1,reference_prior_initialized_link_pairs=250)
    for offset,digest in enumerate(record["prefix_hashes"]):
        assert offset<delivery and state is not None
        counts["reference_prefix_update_attempts"] += 1
        position,rho = _move(position,actual)
        if full:
            state = _conditional("P",state,rho)
            expected["prefix_conditional_fleet_updates"] += 1
            counts["reference_prefix_fleet_updates"] += 1
        else:
            expected.update(prefix_prior_prediction_fleets=1,prefix_prior_stationary_reuses=1)
            counts.update(reference_prefix_prior_prediction_fleets=1,reference_prefix_prior_stationary_reuses=1)
        arrays = (position,rho,*state)
        counts.update(reference_prefix_kinematic_ticks=1)
        assert p.array_digest(*arrays) == digest
        expected.update(prefix_updates_attempted=1,prefix_kinematic_ticks=1)
    geometry,trajectory_state = {},{}
    for q,slot,digest in record["geometry_units"]:
        q,slot = int(q),int(slot)
        assert len(record["prefix_hashes"])==delivery and 0<=q<27 and 0<=slot<length
        if q not in geometry:
            assert slot==0
            geometry[q] = []
            trajectory_state[q] = (position.copy(),state)
        assert slot==len(geometry[q])
        at,conditional = trajectory_state[q]
        command = proposed.copy()
        command[record["member"]] = p.COMMANDS[q]
        counts["reference_candidate_geometry_attempts"] += 1
        at,rho = _move(at,command)
        nominal = free_space_user_path_loss(at,sites,2.e9)
        if full:
            conditional = _conditional("P",conditional,rho)
            expected["candidate_conditional_fleet_updates"] += 1
            counts["reference_candidate_fleet_updates"] += 1
        else:
            expected.update(candidate_prior_prediction_fleets=1,candidate_prior_stationary_reuses=1)
            counts.update(reference_candidate_prior_prediction_fleets=1,reference_candidate_prior_stationary_reuses=1)
        losses = _losses("P",nominal,conditional)
        arrays = (at,rho,nominal,*conditional,losses)
        counts.update(reference_candidate_kinematic_ticks=1,reference_candidate_geometry_snapshots=1,
                      reference_candidate_geometry_link_entries=250)
        assert p.array_digest(*arrays)==digest
        geometry[q].append(losses)
        trajectory_state[q] = (at,conditional)
        expected.update(candidate_geometry_attempts=1,candidate_kinematic_ticks=1,candidate_geometry_snapshots=1,
                        candidate_geometry_link_entries=250)
    computed = np.asarray(record["computed_pairs"])
    assert computed.shape==(len(record["scores"]),2) and len(record["candidate_hashes"])==len(computed)
    assert len(set(map(tuple,computed)))==len(computed)
    weights = np.array([.9 if full and (tick+delivery+k)%4==0 else 1. for k in range(length)])
    for index,(q,mask) in enumerate(computed):
        assert q in geometry and len(geometry[q])==length and 1<=mask<=31
        losses = np.stack(geometry[q],axis=0).reshape(-1,5,50)
        native = np.empty((length*particles,3),np.float64)
        sinr = np.empty_like(losses)
        grants = np.empty(losses.shape,bool)
        active = (int(mask)&(1<<np.arange(5)))!=0
        counts["reference_candidate_plans_attempted"] += 1
        # Deliberately use the original global stable greedy algorithm for every
        # actual particle, rather than the producer's disjoint-row shortcut.
        for item,one in enumerate(losses):
            counts["reference_candidate_user_sinr_calls_attempted"] += 1
            sinr[item] = user_sinr_from_path_loss(one,23.,-80.,False,active)
            counts["reference_candidate_user_sinr_calls"] += 1
            counts["reference_candidate_sinr_entries"] += 250
            counts["reference_candidate_grant_calls_attempted"] += 1
            grants[item] = greedy_connection_assignment(sinr[item],3.,10)
            counts["reference_candidate_grant_calls"] += 1
            counts["reference_candidate_service_calls_attempted"] += 1
            metrics = service_metrics(sinr[item],grants[item],3.)
            counts["reference_candidate_service_calls"] += 1
            native[item] = metrics["J"],metrics["served"],metrics["quality"]
            counts["reference_candidate_fleet_scores"] += 1
        native = native.reshape(length,particles,3)
        counts["reference_candidate_plans"] += 1
        assert p.array_digest(native,sinr,grants)==record["candidate_hashes"][index]
        score = np.mean(np.mean(native,axis=1)*weights[:,None],axis=0)
        np.testing.assert_array_equal(score,record["scores"][index])
        expected.update(candidate_batch_attempts=1,candidate_batch_calls=1,candidate_plans=1,
                        candidate_fleet_scores=length*particles,candidate_sinr_entries=length*particles*250)
    pairs = np.asarray(record["request_pairs"])
    assert pairs.shape==(len(record["request_indices"]),2)
    seen = set()
    for index,pair in enumerate(pairs):
        pair = tuple(pair)
        expected["candidate_requests"] += 1
        if pair in seen:
            expected["candidate_cache_hits"] += 1
        else:
            expected["candidate_uncached_requests"] += 1
            seen.add(pair)
        if record["request_indices"][index] < 0:
            assert index==len(pairs)-1
    _audit_search(record)
    assert {key:int(value) for key,value in record["counts"].items() if value} == {key:int(value) for key,value in expected.items() if value}
    counts["reference_decisions"] += 1
    counts["reference_partial_decisions"] += int(not record["timely"])
    return dict(tick=tick,arm=arm,plans=len(computed),fleet_scores=expected["candidate_fleet_scores"],timely=bool(record["timely"]))
