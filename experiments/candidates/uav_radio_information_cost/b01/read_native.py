"""Arm-specific complete native reading on unchanged independent RF physics helpers.

Audit saved true physical state in both arms, but only FULL has acquired sensor fields.
No environment reset/step or unexecuted policy is run by this reader.
"""
from __future__ import annotations
from collections import Counter
import numpy as np
from envs.pettingzoo.uav_radio import service_metrics
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from experiments.candidates.uav_radio_uncertainty.b01.read_native import (
    _require, _equal, _array, _integer, _identity, _geometry, _innovation,
    _losses, _radio, _counter_witness, _expected_counters, _packet_bytes,
    _grid_commands, _mask, _REPORT, _COMMAND, _GRID, _LOW, _HIGH,
    verify_constructor,
)


def _wire(record, raw, index, actual, entering_mask, counts):
    """Check recorded report/command work; do not finish any interrupted calculation."""
    tick = index*4
    arm = str(raw["arm"])
    full = arm == "P_FULL"
    delivery, report_size, deadline = (3,75,1.336) if full else (2,25,1.436)
    horizon = int(raw["horizon"])
    member = index % 5
    proposed = _grid_commands(raw["proposals"][index], "current C proposal")
    nav = raw["post_c_nav"][index]
    _require(np.all(nav <= 9), "post-C navigation range")
    proposal_q = int(np.flatnonzero(np.all(_GRID == proposed[member], axis=1))[0])
    for key, expected in (("tick",tick),("horizon",horizon),("member",member),
                          ("proposal_q",proposal_q),("length",min(4,horizon-tick-delivery)),
                          ("current_mask",entering_mask),("world",int(raw["world"])),
                          ("arm",str(raw["arm"]))):
        _require(record[key] == expected, "decision identity "+key)
    _require(record["error"] is None, "complete episode has manager error")
    packets = np.asarray(record["report_packets"])
    _require(packets.dtype == np.uint8 and packets.shape in ((0,report_size),(5,report_size)), "report array")
    sent, decoded = record["report_sent"], record["decoded"]
    _require(isinstance(sent, bool) and isinstance(decoded, bool), "report validity flags")
    _require(not sent or packets.shape == (5,report_size), "sent reports absent")
    _require(not decoded or sent, "decoded unsent reports")
    xyz = np.rint(raw["observations"][tick,:,:3].astype(np.float64)
                  * (1000.,1000.,100.) + (0.,0.,50.)).astype(np.int64)
    # Reconstruct only reports actually encoded, not a late entry's unexecuted packets.
    if len(packets):
        for row in range(5):
            counts["reference_native_report_packets_attempted"] += 1
            packet = _REPORT.pack(6,row,4,delivery,index,tick,*xyz[row].tolist(),
                                  *actual[row].astype(int).tolist(),
                                  *proposed[row].astype(int).tolist(),int(nav[row]))
            if full:
                packet += raw["loss_codes"][index,row].tobytes()
            _require(_packet_bytes(packets[row],report_size,"report") == packet, "report bytes")
            counts["reference_native_report_packets"] += 1
            counts["reference_native_report_bytes"] += report_size
    if decoded:
        for name, expected in (("decoded_positions",xyz.astype(np.float64)),
            ("decoded_actual",actual.astype(np.float64)),
            ("decoded_proposals",proposed.astype(np.float64)),("decoded_nav",nav),
            ("decoded_losses",40.+.5*raw["loss_codes"][index].astype(np.float64) if full else np.empty((0,50),np.float64))):
            _equal(record[name], expected, name)
    else:
        for name, shape, dtype in (("decoded_positions",(0,3),np.float64),
            ("decoded_actual",(0,3),np.float64),("decoded_proposals",(0,3),np.float64),
            ("decoded_nav",(0,),np.uint8),("decoded_losses",(0,50),np.float64)):
            _array(record,name,shape,dtype)
    timely = record["timely"]
    _require(isinstance(timely, bool) and record["command_sent"] == timely, "command delivery flags")
    wall, cpu = float(record["wall_seconds"]), float(record["cpu_seconds"])
    _require(np.isfinite(wall) and np.isfinite(cpu) and wall >= 0 and cpu >= 0, "decision timing")
    _require(timely == (wall <= deadline), "whole-decision deadline classification")
    _equal(raw["round_wall"][index], wall, "round wall timing")
    _equal(raw["round_cpu"][index], cpu, "round CPU timing")
    command = np.asarray(record["command_packet"])
    _require(command.dtype == np.uint8 and command.shape in ((0,),(16,)), "command packet array")
    pair = record["selected_before_deadline"]
    expected = actual.copy()
    output_mask = entering_mask
    if command.size:
        counts["reference_native_command_packets_attempted"] += 1
        _require(pair is not None and len(pair) == 2, "encoded command without requested choice")
        q, requested_mask = map(int, pair)
        _require(0 <= q < 27, "requested motion index")
        _mask(requested_mask)
        packet = _COMMAND.pack(6, requested_mask, 4, member, index, tick+delivery, q)
        _require(_packet_bytes(command,16,"command") == packet, "command bytes")
        counts["reference_native_command_packets"] += 1
        counts["reference_native_command_bytes"] += 16
    if timely:
        _require(decoded and command.size == 16 and record["selected_pair"] == pair,
                 "timely complete command")
        q, output_mask = map(int, pair)
        expected = proposed.copy()
        expected[member] = _GRID[q]
    else:
        _require(record["selected_pair"] is None, "late selected pair")
    _equal(record["executed_commands"], expected, "atomic returned commands")
    _require(record["executed_mask"] == output_mask, "atomic returned mask")
    wire_counts = record["counts"]
    encoded_report_bytes = len(packets)*report_size
    sent_report_bytes = 5*report_size if sent else 0
    encoded_command_bytes = command.size
    for name, value in (("report_bytes_encoded",encoded_report_bytes),
        ("report_bytes_sent",sent_report_bytes),("command_bytes_encoded",encoded_command_bytes),
        ("command_bytes_sent",16 if timely else 0)):
        _require(wire_counts.get(name,0) == value, "wire count "+name)
    _require(record["attempted_bytes"] == encoded_report_bytes+encoded_command_bytes
             and record["sent_bytes"] == sent_report_bytes+(16 if timely else 0), "round byte accounting")
    return expected.astype(np.float32), output_mask


def verify_native(raw, counts: Counter):
    """Audit every recorded native state of one complete correlated episode."""
    world, horizon, sigma = _identity(raw)
    arm = str(raw["arm"])
    _require(sigma == 4.14 and arm in ("P_FULL","P_PRIOR"), "scientific episode law/arm")
    full = arm == "P_FULL"
    delivery = 3 if full else 2
    _require(_integer(raw,"completed_steps") == horizon
             and _integer(raw,"completed_reports") == horizon//4, "incomplete episode")
    _require(str(raw["failure_type"]) == "" and str(raw["failure_message"]) == "", "episode failure")
    k = horizon//4
    floats = dict(positions=(horizon+1,5,3),residual=(horizon+1,5,50),loss=(horizon+1,5,50),
        state_sinr=(horizon+1,5,50),peer_sinr=(horizon+1,5,5),sinr=(horizon,5,50),
        reward=(horizon,),quality=(horizon,),served=(horizon,),c_wall=(k,),c_cpu=(k,),
        round_wall=(k,),round_cpu=(k,))
    for name, shape in floats.items():
        value = _array(raw,name,shape,np.float64)
        _require(not np.isnan(value).any(), name+" unfinished values")
        if name not in ("state_sinr","peer_sinr","sinr"):
            _require(np.isfinite(value).all(), name+" nonfinite")
    for name, shape in dict(observations=(horizon+1,5,104),postmove_observations=(horizon,5,104),
                            commands=(horizon,5,3),proposals=(k,5,3)).items():
        _require(np.isfinite(_array(raw,name,shape,np.float32)).all(), name+" nonfinite")
    for name, shape in dict(connections=(horizon,5,50),state_connections=(horizon+1,5,50),
        c_attempted=(k,5),c_completed=(k,5),sensor_completed=(k,),pilot_attempted=(k,),
        refresh_attempted=(horizon+1,),refresh_completed=(horizon+1,)).items():
        _array(raw,name,shape,bool)
    _array(raw,"mask",(horizon,),np.int64)
    _array(raw,"state_mask",(horizon+1,),np.int64)
    _array(raw,"post_c_nav",(k,5),np.uint8)
    sensor_names = ("loss_codes","clipped_low","clipped_high","edge_low","edge_high")
    if full:
        _array(raw,"loss_codes",(k,5,50),np.uint8)
        for name in sensor_names[1:]:
            _array(raw,name,(k,5,50),bool)
    else:
        _require(not any(name in raw for name in sensor_names), "PRIOR has sensor evidence")
    for name in ("c_attempted","c_completed"):
        _require(np.asarray(raw[name]).all(), name+" complete work")
    for name in ("sensor_completed","pilot_attempted"):
        _equal(raw[name],np.full(k,full,bool),name+" arm acquisition boundary")
    _require(np.all(raw["c_wall"] >= 0) and np.all(raw["c_cpu"] >= 0), "C timing")
    refresh = np.zeros(horizon+1,bool)
    refresh[delivery:horizon+1:4] = True
    _equal(raw["refresh_attempted"],refresh,"refresh attempts")
    _equal(raw["refresh_completed"],refresh,"refresh completions")
    physical = _counter_witness(raw, _expected_counters(horizon))
    saved = unpack_records(raw)
    records = saved["decisions"]
    _require(isinstance(records,list) and len(records) == k, "one decision per report")
    positions, users = _geometry(world,counts)
    _equal(_array(raw,"users",(50,2),np.float64),users,"reset users")
    _equal(_array(raw,"positions",(horizon+1,5,3),np.float64)[0],positions,"reset positions")
    map_packet = _packet_bytes(raw["map_packet"],400,"map")
    _require(map_packet == np.rint(users).astype('<i4').tobytes(), "provisioned map")
    counts["reference_native_map_bytes"] += 400
    residual = sigma * _innovation(world,0,counts)
    loss, air = _losses(positions,users,residual,counts)
    radio = _radio(loss,air,31,positions,users,0,horizon,counts)
    actual = np.zeros((5,3),np.float32)
    mask, pending = 31, None
    reconstructed_observations = np.empty((horizon+1,5,104),np.float32)

    def check_state(tick, radio):
        sinr, peer, grants, observation = radio
        for name, expected in (("positions",positions),("residual",residual),("loss",loss),
            ("state_sinr",sinr),("peer_sinr",peer),("state_connections",grants),
            ("observations",observation)):
            _equal(raw[name][tick],expected,name+" boundary "+str(tick))
        _require(int(raw["state_mask"][tick]) == mask,"state mask "+str(tick))
        reconstructed_observations[tick] = observation

    check_state(0,radio)
    for tick in range(horizon):
        if tick % 4 == 0:
            index = tick//4
            if full:
                counts["reference_native_pilot_reports"] += 1
                counts["reference_native_pilot_slots"] += 50
                counts["reference_native_sensor_link_entries"] += 250
                rounded = np.rint((loss-40.)/.5)
                codes = np.clip(rounded,0,255).astype(np.uint8)
                _equal(raw["loss_codes"][index],codes,"sensor codes")
                for name, expected in (("clipped_low",rounded < 0),("clipped_high",rounded > 255),
                                        ("edge_low",codes == 0),("edge_high",codes == 255)):
                    _equal(raw[name][index],expected,name+" sensor flags")
            if tick == 0:
                actual = _grid_commands(raw["proposals"][0],"startup C").copy()
            commands, delivered_mask = _wire(records[index],raw,index,actual,mask,counts)
            _require(pending is None,"overlapping delivery")
            pending = (tick+delivery,commands,delivered_mask)
        _equal(raw["commands"][tick],actual,"delivered command "+str(tick))
        _require(int(raw["mask"][tick]) == mask,"delivered mask "+str(tick))
        counts["reference_native_movement_ticks_attempted"] += 1
        # Native float32 velocity multiplication precedes addition to float64 geometry.
        velocity = actual * 30.
        moved = np.clip(positions + velocity*1.,_LOW,_HIGH)
        displacement = np.linalg.norm(moved-positions,axis=1)
        rho = np.exp(-displacement/17.62)[:,None]
        residual = rho*residual + sigma*np.sqrt(1.-rho*rho)*_innovation(world,tick+1,counts)
        positions = moved
        counts["reference_native_movement_ticks"] += 1
        loss, air = _losses(positions,users,residual,counts)
        radio = _radio(loss,air,mask,positions,users,tick+1,horizon,counts)
        _equal(raw["sinr"][tick],radio[0],"postmove sinr "+str(tick))
        _equal(raw["connections"][tick],radio[2],"postmove grants "+str(tick))
        _equal(raw["postmove_observations"][tick],radio[3],"postmove observation "+str(tick))
        counts["reference_native_service_calls_attempted"] += 1
        metric = service_metrics(radio[0],radio[2],3.)
        counts["reference_native_service_calls"] += 1
        _equal(raw["served"][tick],metric["served"],"native served")
        _equal(raw["quality"][tick],metric["quality"],"native quality",atol=1e-12)
        _equal(raw["reward"][tick],metric["J"],"native team reward",atol=1e-12)
        if pending is not None and tick+1 == pending[0]:
            actual, mask = pending[1],pending[2]
            pending = None
            counts["reference_native_arrival_refreshes_attempted"] += 1
            # Same loss and residual: refresh is radio-only, with no innovation/geometry.
            radio = _radio(loss,air,mask,positions,users,tick+1,horizon,counts)
            counts["reference_native_arrival_refreshes"] += 1
        check_state(tick+1,radio)
    _require(pending is None,"undelivered final command")
    counts["reference_native_episodes_verified"] += 1
    return dict(world=world,arm=str(raw["arm"]),horizon=horizon,sigma=sigma,verified=True,
                steps=horizon,reports=k,pilot_slots=k*50 if full else 0,refreshes=k,physical_counts=physical,
                reconstructed_observations=reconstructed_observations)
