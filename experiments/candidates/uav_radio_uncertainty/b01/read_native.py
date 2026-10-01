"""Saved-native reconstruction, without an environment or production noise helper.

Only complete episodes are accepted. Reference work follows the recorded constructor,
reset, physical steps and arrival refreshes; it never generates a policy/future state.
C replay and modeled candidate/search replay belong to the other reader components.
"""

from __future__ import annotations

from collections import Counter
from itertools import product
import struct

import numpy as np

from envs.pettingzoo.uav_radio import (
    greedy_connection_assignment, service_metrics, user_sinr_from_path_loss,
)
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from . import contract as c


_COUNTER_NAMES = (
    "constructor_calls_attempted", "constructor_calls_completed",
    "constructor_reset_calls_attempted", "constructor_reset_calls_completed",
    "explicit_reset_calls_attempted", "explicit_reset_calls_completed",
    "native_step_calls_attempted", "native_step_calls_completed",
    "physical_normal_blocks_attempted", "physical_normal_blocks_completed",
    "physical_normal_values_attempted", "physical_normal_values_completed",
    "physical_initializations", "physical_updates",
)
_REPORT = struct.Struct("<BBBBIIhhhbbbbbbB")
_COMMAND = struct.Struct("<BBBBIII")
_GRID = np.array(sorted(product((-1, 0, 1), repeat=3),
                        key=lambda q: (sum(v*v for v in q), q)), np.float32)
_LOW = np.array((0., 0., 50.))
_HIGH = np.array((1000., 1000., 150.))


def _require(condition, message):
    if not condition:
        raise ValueError("native audit: " + message)


def _equal(actual, expected, label, *, atol=0.):
    actual, expected = np.asarray(actual), np.asarray(expected)
    _require(actual.shape == expected.shape, label + " shape")
    okay = (np.array_equal(actual, expected) if atol == 0. else
            np.allclose(actual, expected, rtol=0., atol=atol, equal_nan=False))
    _require(okay, label + " values")


def _array(raw, name, shape, dtype):
    value = np.asarray(raw[name])
    _require(value.shape == shape and value.dtype == np.dtype(dtype), name + " shape/dtype")
    return value


def _integer(raw, name, *, minimum=0, maximum=None):
    value = np.asarray(raw[name])
    _require(value.shape == () and value.dtype.kind in "iu", name + " integer scalar")
    value = int(value)
    _require(value >= minimum and (maximum is None or value <= maximum), name + " range")
    return value


def _identity(raw):
    _require(np.__version__ == c.NUMPY_VERSION, "NumPy version")
    world = _integer(raw, "world", maximum=2**32-1)
    horizon = _integer(raw, "horizon", minimum=8, maximum=256)
    _require(horizon % 4 == 0, "horizon four-tick boundary")
    value = np.asarray(raw["sigma"])
    _require(value.shape == () and value.dtype.kind == "f" and np.isfinite(value)
             and float(value) >= 0., "sigma scalar")
    return world, horizon, float(value)


def _geometry(world, counts):
    counts["reference_native_geometry_resets_attempted"] += 1
    rng = np.random.RandomState(world)
    positions = np.empty((5, 3), np.float64)
    users = np.empty((50, 2), np.float64)
    # Preserve native scalar draw order, including interleaved UAV x/y/height.
    for row in range(5):
        for col, bounds in enumerate(((0., 1000.), (0., 1000.), (50., 150.))):
            counts["reference_native_geometry_uniform_values"] += 1
            positions[row, col] = rng.uniform(*bounds)
    for row in range(50):
        for col in range(2):
            counts["reference_native_geometry_uniform_values"] += 1
            users[row, col] = rng.uniform(0., 1000.)
    counts["reference_native_geometry_resets"] += 1
    return positions, users


def _innovation(world, tick, counts):
    counts["reference_native_normal_blocks_attempted"] += 1
    counts["reference_native_normal_values_attempted"] += 250
    # Deliberately independent of environment.py/randomness.py and their helpers.
    rng = np.random.Generator(np.random.Philox(np.random.SeedSequence(
        [0x52465048, 29640001, world, tick])))
    values = rng.standard_normal(size=(5, 50), dtype=np.float64)
    counts["reference_native_normal_blocks"] += 1
    counts["reference_native_normal_values"] += values.size
    return values


def _losses(positions, users, residual, counts):
    counts["reference_native_free_space_snapshots_attempted"] += 1
    dx = positions[:, 0, None] - users[None, :, 0]
    dy = positions[:, 1, None] - users[None, :, 1]
    dz = positions[:, 2, None] - np.zeros((1, 50), dtype=float)
    distance = np.sqrt(dx*dx + dy*dy + dz*dz)
    constant = 20 * np.log10(4 * np.pi / (3e8 / 2e9))
    loss = 20 * np.log10(np.maximum(distance, 1e-6)) + constant + residual
    counts["reference_native_free_space_snapshots"] += 1
    counts["reference_native_free_space_link_entries"] += 250
    counts["reference_native_a2a_snapshots_attempted"] += 1
    difference = positions[:, None, :] - positions[None, :, :]
    distance = np.sqrt(difference[:, :, 0]*difference[:, :, 0]
                       + difference[:, :, 1]*difference[:, :, 1]
                       + difference[:, :, 2]*difference[:, :, 2])
    air = 20 * np.log10(np.maximum(distance, 1e-6)) + constant
    np.fill_diagonal(air, 0.)
    counts["reference_native_a2a_snapshots"] += 1
    counts["reference_native_a2a_link_entries"] += 25
    return loss, air


def _mask(value):
    _require(isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_))
             and 1 <= value <= 31, "nonempty mask")
    return np.array([bool(int(value) & (1 << row)) for row in range(5)])


def _peer_sinr(air, active, counts):
    counts["reference_native_peer_sinr_calls_attempted"] += 1
    linear = 10 ** ((23. - air) / 10)
    np.fill_diagonal(linear, 0.)
    linear[~active] = 0.
    interference = np.zeros_like(air)
    for sender in range(5):
        accumulator = np.zeros(5, dtype=air.dtype)
        for other in range(5):
            if other != sender:
                accumulator += linear[other]
        interference[sender] = accumulator
    positive = interference > 0
    safe = np.where(positive, interference, 1.)
    dbm = 10 * np.log10(safe)
    denominator = np.where(positive, 10 * np.log10(10 ** (-80. / 10)
                           + 10 ** (dbm / 10)), -80.)
    result = 23. - air - denominator
    result[~(active[:, None] & active[None, :])] = -np.inf
    counts["reference_native_peer_sinr_calls"] += 1
    counts["reference_native_peer_sinr_entries"] += 25
    return result


def _observation(positions, users, sinr, peer, tick, horizon, counts):
    counts["reference_native_observation_fleets_attempted"] += 1
    result = np.empty((5, 104), np.float32)
    for member in range(5):
        counts["reference_native_observation_rows_attempted"] += 1
        own = positions[member]
        normalized = own / 1000.
        normalized[2] = (own[2]-50.)/100.
        user_block = np.zeros((20, 3))
        # Eligibility, rather than the allocated ten, defines the native top twenty.
        eligible = [u for u in range(50) if sinr[member, u] >= 3.]
        eligible.sort(key=lambda u: -sinr[member, u])
        chosen = eligible[:20]
        if chosen:
            user_block[:len(chosen), :2] = (users[chosen]-own[:2])/1000.
            user_block[:len(chosen), 2] = np.clip((sinr[member, chosen]+10.)/50., 0., 1.)
        peer_block = np.zeros((10, 4))
        eligible = [u for u in range(5) if u != member and peer[member, u] >= 3.]
        eligible.sort(key=lambda u: -peer[member, u])
        if eligible:
            relative = positions[eligible]-own
            peer_block[:len(eligible), :2] = relative[:, :2]/1000.
            peer_block[:len(eligible), 2] = relative[:, 2]/100.
            peer_block[:len(eligible), 3] = np.clip((peer[member, eligible]+10.)/50., 0., 1.)
        result[member] = np.concatenate((normalized, user_block.ravel(), peer_block.ravel(),
                                         np.array([tick/horizon]))).astype(np.float32)
        counts["reference_native_observation_rows"] += 1
    counts["reference_native_observation_fleets"] += 1
    return result


def _radio(loss, air, mask, positions, users, tick, horizon, counts):
    active = _mask(mask)
    counts["reference_native_user_sinr_calls_attempted"] += 1
    sinr = user_sinr_from_path_loss(loss, 23., -80., False, active)
    counts["reference_native_user_sinr_calls"] += 1
    counts["reference_native_user_sinr_entries"] += 250
    peer = _peer_sinr(air, active, counts)
    counts["reference_native_grant_calls_attempted"] += 1
    connections = greedy_connection_assignment(sinr, 3., 10)
    counts["reference_native_grant_calls"] += 1
    observations = _observation(positions, users, sinr, peer, tick, horizon, counts)
    return sinr, peer, connections, observations


def _counter_witness(raw, expected, *, constructor=False):
    names_key, values_key = (("counter_names", "counter_values") if constructor else
                             ("physical_counter_names", "physical_counter_values"))
    names = np.asarray(raw[names_key])
    values = _array(raw, values_key, (14,), np.int64)
    _require(names.shape == (14,) and names.dtype.kind == "U", "physical counter names")
    names = names.tolist()
    _require(len(set(names)) == 14 and set(names) == set(_COUNTER_NAMES),
             "all fourteen physical counters required")
    actual = dict(zip(names, values.tolist()))
    _require(actual == expected, "physical counter totals/deltas")
    return actual


def _expected_counters(horizon=None):
    expected = dict.fromkeys(_COUNTER_NAMES, 0)
    constructor = horizon is None
    for suffix in ("attempted", "completed"):
        if constructor:
            expected["constructor_calls_"+suffix] = 1
            expected["constructor_reset_calls_"+suffix] = 1
        else:
            expected["explicit_reset_calls_"+suffix] = 1
            expected["native_step_calls_"+suffix] = horizon
        expected["physical_normal_blocks_"+suffix] = 1 if constructor else horizon+1
        expected["physical_normal_values_"+suffix] = 250 if constructor else (horizon+1)*250
    expected["physical_initializations"] = 1
    expected["physical_updates"] = 0 if constructor else horizon
    return expected


def verify_constructor(raw, counts: Counter):
    """Verify one saved implicit reset and its cumulative constructor counters."""
    world, horizon, sigma = _identity(raw)
    _require(_integer(raw, "tick") == 0, "constructor tick")
    positions, users = _geometry(world, counts)
    _equal(_array(raw, "positions", (5, 3), np.float64), positions, "constructor positions")
    _equal(_array(raw, "users", (50, 2), np.float64), users, "constructor users")
    residual = sigma * _innovation(world, 0, counts)
    _equal(_array(raw, "residual", (5, 50), np.float64), residual, "constructor residual")
    loss, air = _losses(positions, users, residual, counts)
    _equal(_array(raw, "user_loss", (5, 50), np.float64), loss, "constructor user loss")
    _equal(_array(raw, "transmitter_mask", (5,), bool), np.ones(5, bool), "constructor mask")
    sinr, peer, grants, observation = _radio(loss, air, 31, positions, users, 0, horizon, counts)
    for name, expected, dtype in (("sinr",sinr,np.float64), ("peer_sinr",peer,np.float64),
                                  ("connections",grants,bool), ("observations",observation,np.float32)):
        _equal(_array(raw, name, expected.shape, dtype), expected, "constructor "+name)
    physical = _counter_witness(raw, _expected_counters(), constructor=True)
    counts["reference_native_constructors_verified"] += 1
    return dict(world=world, horizon=horizon, sigma=sigma, verified=True, physical_counts=physical)


def _packet_bytes(value, size, name):
    array = np.asarray(value)
    _require(array.dtype == np.uint8 and array.shape == (size,), name + " packet shape/dtype")
    return array.tobytes()


def _grid_commands(value, label):
    commands = np.asarray(value)
    _require(commands.shape == (5, 3) and np.isfinite(commands).all()
             and np.isin(commands, (-1, 0, 1)).all(), label + " grid commands")
    return commands


def _wire(record, raw, index, actual, entering_mask, counts):
    """Check recorded report/command work; do not finish any interrupted calculation."""
    tick = index*4
    horizon = int(raw["horizon"])
    member = index % 5
    proposed = _grid_commands(raw["proposals"][index], "current C proposal")
    nav = raw["post_c_nav"][index]
    _require(np.all(nav <= 9), "post-C navigation range")
    proposal_q = int(np.flatnonzero(np.all(_GRID == proposed[member], axis=1))[0])
    for key, expected in (("tick",tick),("horizon",horizon),("member",member),
                          ("proposal_q",proposal_q),("length",min(4,horizon-tick-3)),
                          ("current_mask",entering_mask),("world",int(raw["world"])),
                          ("arm",str(raw["arm"]))):
        _require(record[key] == expected, "decision identity "+key)
    _require(record["error"] is None, "complete episode has manager error")
    packets = np.asarray(record["report_packets"])
    _require(packets.dtype == np.uint8 and packets.shape in ((0,75),(5,75)), "report array")
    sent, decoded = record["report_sent"], record["decoded"]
    _require(isinstance(sent, bool) and isinstance(decoded, bool), "report validity flags")
    _require(not sent or packets.shape == (5,75), "sent reports absent")
    _require(not decoded or sent, "decoded unsent reports")
    xyz = np.rint(raw["observations"][tick,:,:3].astype(np.float64)
                  * (1000.,1000.,100.) + (0.,0.,50.)).astype(np.int64)
    # Reconstruct only reports actually encoded, not a late entry's unexecuted packets.
    if len(packets):
        for row in range(5):
            counts["reference_native_report_packets_attempted"] += 1
            packet = _REPORT.pack(5,row,4,3,index,tick,*xyz[row].tolist(),
                                  *actual[row].astype(int).tolist(),
                                  *proposed[row].astype(int).tolist(),int(nav[row]))
            packet += raw["loss_codes"][index,row].tobytes()
            _require(_packet_bytes(packets[row],75,"report") == packet, "report bytes")
            counts["reference_native_report_packets"] += 1
            counts["reference_native_report_bytes"] += 75
    if decoded:
        for name, expected in (("decoded_positions",xyz.astype(np.float64)),
            ("decoded_actual",actual.astype(np.float64)),
            ("decoded_proposals",proposed.astype(np.float64)),("decoded_nav",nav),
            ("decoded_losses",40.+.5*raw["loss_codes"][index].astype(np.float64))):
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
    _require(timely == (wall <= 1.336), "whole-decision deadline classification")
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
        packet = _COMMAND.pack(5, requested_mask, 4, member, index, tick+3, q)
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
    encoded_report_bytes = len(packets)*75
    sent_report_bytes = 375 if sent else 0
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
    _require(sigma == 4.14 and str(raw["arm"]) in ("P","U32"), "scientific episode law/arm")
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
        refresh_attempted=(horizon+1,),refresh_completed=(horizon+1,),clipped_low=(k,5,50),
        clipped_high=(k,5,50),edge_low=(k,5,50),edge_high=(k,5,50)).items():
        _array(raw,name,shape,bool)
    _array(raw,"mask",(horizon,),np.int64)
    _array(raw,"state_mask",(horizon+1,),np.int64)
    _array(raw,"post_c_nav",(k,5),np.uint8)
    _array(raw,"loss_codes",(k,5,50),np.uint8)
    for name in ("c_attempted","c_completed","sensor_completed","pilot_attempted"):
        _require(np.asarray(raw[name]).all(), name+" complete work")
    _require(np.all(raw["c_wall"] >= 0) and np.all(raw["c_cpu"] >= 0), "C timing")
    refresh = np.zeros(horizon+1,bool)
    refresh[3:horizon+1:4] = True
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
            pending = (tick+3,commands,delivered_mask)
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
                steps=horizon,reports=k,pilot_slots=k*50,refreshes=k,physical_counts=physical,
                reconstructed_observations=reconstructed_observations)
