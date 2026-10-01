"""Independent conditional trajectories and original scalar native allocation.

Only logged completed units are reconstructed. An interrupted request is never
finished; saved scores are used solely to audit the deterministic request order.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from envs.pettingzoo.uav_radio import (free_space_user_path_loss,
    user_sinr_from_path_loss, greedy_connection_assignment, service_metrics)
from . import contract as c
from . import protocol as p


def _move(position, command):
    after = np.clip(position + command * 30., (0.,0.,50.), (1000.,1000.,150.))
    distance = np.sqrt(np.sum((after-position)**2,axis=-1))
    return after,np.exp(-distance/17.62)


def _conditional(arm, state, rho, innovation=None):
    if arm == "P":
        mu,var = state
        coefficient = rho[:,None]
        square = coefficient*coefficient
        return coefficient*mu, square*var + 4.14**2*(1.-square)
    coefficient = rho[None,:,None]
    return coefficient*state + 4.14*np.sqrt(np.maximum(0.,1.-coefficient*coefficient))*innovation


def _losses(arm, nominal, state):
    if arm == "P":
        mu,var = state
        a = np.log(10.)/10.
        power = 10.**((23.-nominal)/10.)
        power = power*np.exp(-a*mu+.5*a*a*var)
        return (23.-10.*np.log10(power))[None,:,:]
    return nominal[None,:,:]+state


class _StopSavedPrefix(Exception):
    pass


def _audit_search(record):
    pairs = np.asarray(record["request_pairs"])
    index = 0
    computed = {tuple(pair):i for i,pair in enumerate(record["computed_pairs"])}

    def rank(q,mask,value):
        return (float(value[0]),float(value[1]),int(q==record["proposal_q"]),int(mask).bit_count(),-mask,-q)

    def score(q,mask):
        nonlocal index
        if index == len(pairs):
            raise _StopSavedPrefix
        np.testing.assert_array_equal(pairs[index],(q,mask))
        item = int(record["request_indices"][index])
        index += 1
        if item == -1:
            assert index == len(pairs) and (q,mask) not in computed
            raise _StopSavedPrefix
        assert computed[q,mask] == item
        return record["scores"][item]

    def best_q(mask):
        ranked = [(rank(q,mask,score(q,mask)),q) for q in range(27)]
        return max(ranked)[1]

    def best_mask(q):
        ranked = [(rank(q,mask,score(q,mask)),mask) for mask in range(1,32)]
        return max(ranked)[1]

    selected = None
    try:
        q1 = best_q(int(record["current_mask"]))
        m1 = best_mask(q1)
        m2 = best_mask(int(record["proposal_q"]))
        q2 = best_q(m2)
        left = rank(q1,m1,record["scores"][computed[q1,m1]])
        right = rank(q2,m2,record["scores"][computed[q2,m2]])
        selected = (q1,m1) if left>=right else (q2,m2)
    except _StopSavedPrefix:
        pass
    assert index == len(pairs)
    if record["selected_before_deadline"] is not None:
        assert tuple(record["selected_before_deadline"]) == selected
    if record["timely"]:
        assert selected is not None and tuple(record["selected_pair"]) == selected
    return selected


def verify_decision(record, sites, counts):
    arm,tick,world = record["arm"],int(record["tick"]),int(record["world"])
    assert arm in c.ARMS and record["error"] is None
    particles = 1 if arm=="P" else 32
    length = min(4,int(record["horizon"])-tick-3)
    assert record["length"] == length and record["member"] == (tick//4)%5
    expected = Counter()
    packet_bytes = np.asarray(record["report_packets"],np.uint8)
    expected["report_bytes_encoded"] = packet_bytes.size
    expected["report_bytes_sent"] = 375 if record["report_sent"] else 0
    expected["command_bytes_encoded"] = np.asarray(record["command_packet"]).size
    expected["command_bytes_sent"] = 16 if record["command_sent"] else 0
    assert packet_bytes.shape in ((0,75),(5,75))
    assert not record["report_sent"] or packet_bytes.shape == (5,75)
    assert bool(record["command_sent"]) == bool(record["timely"])
    assert record["attempted_bytes"] == expected["report_bytes_encoded"]+expected["command_bytes_encoded"]
    assert record["sent_bytes"] == expected["report_bytes_sent"]+expected["command_bytes_sent"]
    assert bool(record["timely"]) == (record["wall_seconds"]<=c.COMPUTE_SECONDS)
    position = state = noise = None
    if record["decoded"]:
        assert record["report_sent"]
        decoded = p.decode_reports(tuple(row.tobytes() for row in packet_bytes),tick)
        for key,value in zip(("decoded_positions","decoded_actual","decoded_proposals","decoded_nav","decoded_losses"),decoded):
            np.testing.assert_array_equal(record[key],value)
        position,actual,proposed,_,loss = decoded
        assert record["proposal_q"] == p.command_index(proposed[record["member"]])
    else:
        assert not record["anchor_hash"] and not record["noise_hash"]
    if record["anchor_hash"]:
        assert record["decoded"]
        counts["reference_anchor_geometry_attempts"] += 1
        nominal = free_space_user_path_loss(position,sites,2.e9)
        counts.update(reference_anchor_geometry_snapshots=1,reference_anchor_link_entries=250)
        mean,variance = loss-nominal,np.zeros_like(loss)
        assert p.array_digest(nominal,mean,variance) == record["anchor_hash"]
        state = (mean,variance) if arm=="P" else np.broadcast_to(mean,(32,5,50)).copy()
        expected.update(anchor_geometry_attempts=1,anchor_geometry_snapshots=1,anchor_geometry_link_entries=250)
    if record["noise_hash"]:
        assert arm=="U32" and np.__version__==c.NUMPY_VERSION and record["anchor_hash"]
        address = [c.MODEL_NAMESPACE,c.MODEL_ROOT,world,tick]
        assert record["noise_address"] == address
        counts.update(reference_model_normal_blocks_attempted=1,reference_model_normal_values_attempted=28000)
        base = np.random.Generator(np.random.Philox(np.random.SeedSequence(address))).standard_normal((16,7,5,50),dtype=np.float64)
        counts.update(reference_model_normal_blocks=1,reference_model_normal_values=28000)
        assert p.array_digest(base) == record["noise_hash"]
        noise = np.concatenate((base,-base),axis=0)
        expected.update(model_normal_blocks_attempted=1,model_normal_blocks=1,
                        model_normal_values=28000,model_signed_normal_values=56000)
        counts["reference_model_signed_values"] += 56000
    else:
        assert not record["noise_address"]
    for offset,digest in enumerate(record["prefix_hashes"]):
        assert offset<3 and state is not None and (arm=="P" or noise is not None)
        counts["reference_prefix_update_attempts"] += 1
        position,rho = _move(position,actual)
        state = _conditional(arm,state,rho,None if noise is None else noise[:,offset])
        arrays = (position,rho,*state) if arm=="P" else (position,rho,state)
        counts.update(reference_prefix_kinematic_ticks=1,reference_prefix_fleet_updates=particles)
        assert p.array_digest(*arrays) == digest
        expected.update(prefix_updates_attempted=1,prefix_kinematic_ticks=1,prefix_conditional_fleet_updates=particles)
    geometry,trajectory_state = {},{}
    for q,slot,digest in record["geometry_units"]:
        q,slot = int(q),int(slot)
        assert len(record["prefix_hashes"])==3 and 0<=q<27 and 0<=slot<length
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
        conditional = _conditional(arm,conditional,rho,None if noise is None else noise[:,3+slot])
        losses = _losses(arm,nominal,conditional)
        arrays = (at,rho,nominal,*conditional,losses) if arm=="P" else (at,rho,nominal,conditional,losses)
        counts.update(reference_candidate_kinematic_ticks=1,reference_candidate_geometry_snapshots=1,
                      reference_candidate_geometry_link_entries=250,reference_candidate_fleet_updates=particles)
        assert p.array_digest(*arrays)==digest
        geometry[q].append(losses)
        trajectory_state[q] = (at,conditional)
        expected.update(candidate_geometry_attempts=1,candidate_kinematic_ticks=1,candidate_geometry_snapshots=1,
                        candidate_geometry_link_entries=250,candidate_conditional_fleet_updates=particles)
    computed = np.asarray(record["computed_pairs"])
    assert computed.shape==(len(record["scores"]),2) and len(record["candidate_hashes"])==len(computed)
    assert len(set(map(tuple,computed)))==len(computed)
    weights = np.array([c.payload_weight(tick+3+k) for k in range(length)])
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
