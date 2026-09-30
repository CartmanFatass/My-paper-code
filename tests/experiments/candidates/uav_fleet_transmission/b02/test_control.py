import copy
import gzip
import json

import numpy as np
import pytest

from envs.pettingzoo import uav_radio
from experiments.candidates.uav_fleet_transmission.control import COMMANDS, OrdinaryController, choose_mask, decode_public_state, predict_next
from experiments.candidates.uav_fleet_transmission.host import MatchedWorld, mask_bits, runtime_seed, world as old_world
from experiments.candidates.uav_fleet_transmission.reader import _public_state
from experiments.candidates.uav_fleet_transmission.study import artifact, make_env as old_env
from experiments.candidates.uav_fleet_transmission.b02 import option
from experiments.candidates.uav_fleet_transmission.b02.controller import Program, joint_select
from experiments.candidates.uav_fleet_transmission.b02.host import WORLD_IDS, bound_worlds, make_env, seed
from experiments.candidates.uav_fleet_transmission.b02.reader import validate_worker, verify_episode
from experiments.candidates.uav_fleet_transmission.b02.study import evaluate_episode, verify_prefixes


def fixture():
    scene = old_world(29310000)
    return scene.uav_positions.copy(), scene.user_positions.copy()


def scalar_native_score(positions, users, mask):
    loss = uav_radio.free_space_user_path_loss(positions, users)
    sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=mask_bits(mask,8))
    connections = uav_radio.greedy_connection_assignment(sinr,0.,10)
    served = int(connections.sum())
    quality = sum(float(np.clip(sinr[i,j]/30,0,1)) for i in range(8) for j in range(50)
                  if connections[i,j]) / max(served,1)
    penalty = .1*((positions[:,2].mean()-50)/100)
    return .7*(served/50)+.3*quality-penalty, served


def test_initial_arrays_are_committed_and_independent():
    # Initial arrays only: no policy, reward or rollout on new result worlds.
    scenes=bound_worlds()
    assert tuple(scenes)==WORLD_IDS
    assert len({s.user_positions.tobytes() for s in scenes.values()})==16
    assert len({seed(w,3,8) for w in WORLD_IDS})==16
    assert not np.array_equal(scenes[WORLD_IDS[0]].user_positions,old_world(29310000).user_positions)


def test_original_c_host_and_r_prefix_exact(tmp_path):
    scene=old_world(29310000)
    rs=runtime_seed(scene.world_id,8)
    old,new=old_env(8,scene.world_id,40),make_env(scene,40,rs)
    c=Program("C",40)
    ordinary=OrdinaryController(8)
    old_mask=255
    try:
        old_obs,old_info=old.reset(seed=rs)
        obs,info=new.reset(seed=rs)
        np.testing.assert_array_equal(obs,old_obs)
        state=np.asarray(info["state"])
        for t in range(40):
            action,mask,decision=c.select(t,state if t%10==0 else None,old_mask)
            expected,predicted,_=ordinary.select(t,state if t%10==0 else None,old_mask)
            expected_mask=old_mask
            if t%10==0:
                expected_mask,_=choose_mask(ordinary.users,predicted,old_mask)
                old.env.env.set_transmitter_mask(mask_bits(expected_mask,8))
                new.env.env.set_transmitter_mask(mask_bits(mask,8))
            np.testing.assert_array_equal(action,expected)
            assert mask==expected_mask
            a=old.step(expected);b=new.step(action)
            np.testing.assert_array_equal(a[0],b[0])
            np.testing.assert_array_equal(old.env.env.uav_positions,new.env.env.uav_positions)
            assert a[1:4]==b[1:4]
            state=np.asarray(b[4]["next_state"])
            old_mask=mask
    finally:
        old.close();new.close()
    rows=[evaluate_episode(a,scene,40,rs,tmp_path) for a in ("C","R")]
    verify_prefixes(tmp_path,rows)
    for row in rows:
        verify_episode(row,tmp_path,scene=scene,horizon=40)
    # A changed saved choice with a valid new artifact hash must still be refused.
    row=copy.deepcopy(rows[0]);p=tmp_path/row["decisions"]["path"]
    with gzip.open(p,"rt") as f: decisions=[json.loads(line) for line in f]
    decisions[4]["issued_mask"]=1
    with gzip.open(p,"wt") as f:
        for d in decisions:f.write(json.dumps(d)+"\n")
    row["decisions"]=artifact(p,tmp_path)
    with pytest.raises(ValueError,match="reconstruction"):
        verify_episode(row,tmp_path,scene=scene,horizon=40)


def test_joint_first_coordinate_matches_scalar_native_exhaustion():
    positions,users=fixture()
    state=_public_state(positions,users,0,500)
    positions,users=decode_public_state(state,8)
    controller=OrdinaryController(8)
    command,mask,trace=joint_select(controller,0,state,255)
    best=None
    for command_index,move in enumerate(COMMANDS):
        commands=np.zeros((8,3),dtype=np.float32);commands[0]=move
        predicted=predict_next(positions,commands)
        distance=float(np.linalg.norm(predicted-positions,axis=1).sum())
        for candidate_mask in range(1,256):
            j,served=scalar_native_score(predicted,users,candidate_mask)
            rank=(j,served,-distance,bool(np.array_equal(move,np.zeros(3)) and candidate_mask==255),
                  -command_index,-candidate_mask)
            if best is None or rank>best[0]:best=(rank,command_index,candidate_mask)
    first=trace["choices"][0]
    assert first["selected"]==COMMANDS[best[1]].tolist()
    assert first["selected_mask"]==best[2]
    assert first["selected_score"]["J"]==best[0][0]
    assert first["selected_score"]["served"]==best[0][1]
    assert trace["requested_candidates"]==8*27*255
    assert trace["requested_candidates"]==trace["scored_candidates"]+trace["cached_candidates"]
    assert controller.next_t==1
    np.testing.assert_array_equal(controller.commands,command)
    np.testing.assert_array_equal(controller.positions,predict_next(positions,command))
    assert 1<=mask<=255


def test_option_execution_preserves_actual_history_and_mask_clock(monkeypatch):
    positions,users=fixture()
    p=Program("R")
    p.controller.next_t=40
    p.controller.commands=np.ones((8,3),dtype=np.float32)
    commands=np.zeros((10,8,3),dtype=np.float32)
    commands[:3,1,0]=1
    destination=positions.copy()
    for a in commands:destination=predict_next(destination,a)
    plan={"initiated":True,"member":1,"site":0,"commands":commands.tolist(),
          "duration":10,"arrival_t":50,"predicted_destination":destination.tolist()}
    monkeypatch.setattr(option,"plan_option",lambda *args,**kwargs:plan)
    monkeypatch.setattr(option,"arrival_mask",lambda *args:(3,{"fixture":True}))
    for t in range(40,51):
        state=_public_state(positions,users,t,500) if t%10==0 else None
        action,mask,trace=p.select(t,state,1)
        expected=commands[t-40] if t<50 else np.zeros((8,3),dtype=np.float32)
        np.testing.assert_array_equal(action,expected)
        assert mask==(1 if t<50 else 3)
        positions=predict_next(positions,action)
    assert p.controller.next_t==51
    np.testing.assert_array_equal(p.controller.commands,np.zeros((8,3),dtype=np.float32))
    reference=OrdinaryController(8)
    reference.next_t=51
    reference.positions=p.controller.positions.copy();reference.users=p.controller.users.copy()
    expected,_,_=reference.select(51,None,3)
    actual,mask,trace=p.select(51,None,3)
    np.testing.assert_array_equal(actual,expected)
    assert mask==3 and trace["phase"]=="ordinary" and "mask" not in trace
    with pytest.raises(ValueError,match="cadence"):
        p.select(52,_public_state(positions,users,52,500),3)


def test_noninitiation_preserves_c_at_t40(monkeypatch):
    positions,users=fixture()
    state=_public_state(positions,users,40,500)
    c,r=Program("C"),Program("R")
    for p in (c,r):
        p.controller.next_t=40
        p.controller.commands=np.ones((8,3),dtype=np.float32)
    monkeypatch.setattr(option,"plan_option",lambda *args,**kwargs:{"initiated":False})
    a,am,ad=c.select(40,state,7);b,bm,bd=r.select(40,state,7)
    np.testing.assert_array_equal(a,b)
    assert am==bm and ad["motion"]==bd["motion"] and ad["mask"]==bd["mask"]


def test_reader_refuses_incomplete_worker_before_any_replay():
    with pytest.raises(ValueError,match="not completed"):
        validate_worker({"config":{},"worker_status":"incomplete"})


@pytest.mark.parametrize("arm,horizon",[("J",11),("R",500)])
def test_new_controller_native_saved_data_roundtrip_on_old_fixture(arm,horizon,tmp_path):
    # Old B01 / constructed corner fixtures; never a new B02 result cell.
    scene=old_world(29310000)
    rs=runtime_seed(scene.world_id,8)
    if arm=="R":
        users=np.repeat(np.asarray([[0.,0.],[0.,1000.],[1000.,0.],[1000.,1000.]]),[12,13,12,13],axis=0)
        positions=np.tile([1000.,1000.,50.],(8,1));positions[0]=[0.,0.,50.]
        scene=MatchedWorld(-1,41,42,users,positions)
        rs=43
    row=evaluate_episode(arm,scene,horizon,rs,tmp_path)
    verify_episode(row,tmp_path,scene=scene,horizon=horizon)
    assert row["steps"]==horizon
    if arm=="R":
        assert row["calls"]["option"]==1
        assert row["option"]["initiated"] is True
        assert row["calls"]["arrival"]==1
        assert row["calls"]["motion"]==500-row["option"]["duration"]-1
        assert row["calls"]["mask"]==50-row["option"]["duration"]//10-1
    else:
        assert row["calls"]["joint"]==2 and row["calls"]["mask"]==0
