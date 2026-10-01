"""The four prospectively fixed H8 episodes and their complete offline reading."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
import time
import traceback
from unittest.mock import patch

import numpy as np
import torch

from envs.pettingzoo.uav_env import MultiUAVEnv
from envs.pettingzoo.uav_radio import service_metrics
from experiments.candidates.uav_radio_activation.b01.study import factory as old_factory
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from . import contract as c
from . import protocol as p
from .collect import empty_raw,save_state,collect_episode,constructor_witness
from .environment import make_env
from .io import write_json,save_evidence,artifact_bytes,resources
from .metrics import outcomes
from .read_native import _geometry,_innovation,_losses,_radio,verify_constructor
from .reader import verify_episode


def old_snapshot(env):
    base=env.env
    return dict(world=int(base.seed_val),tick=int(base.current_step),positions=base.uav_positions.copy(),
        users=base.user_positions.copy(),residual=np.zeros((5,50)),user_loss=base._uav_user_path_loss_matrix.copy(),
        sinr=base.sinr_matrix.copy(),peer_sinr=base.uav_sinr_matrix.copy(),connections=base.connections.copy(),
        transmitter_mask=base.transmitter_mask)


def fixed_commands():
    return np.asarray([[p.COMMANDS[(3*t+5*i)%27] for i in range(5)] for t in range(8)],np.float32)


def fixed_episode(env,correlated):
    raw=empty_raw(8,c.FIXTURE_SEED,"sigma0" if correlated else "old_free_space",0.)
    counts=Counter(reset_attempts=1,reset_calls=0,native_step_attempts=0,native_steps=0,mask_refresh_attempts=0,mask_refreshes=0)
    before=env.env.physical_counters if correlated else None
    snapshot=lambda: env.env.physical_snapshot() if correlated else old_snapshot(env)
    failure=None
    try:
        obs,_=env.reset(seed=c.FIXTURE_SEED)
        counts["reset_calls"]+=1
        state=snapshot()
        raw["users"]=state["users"]
        mask=31
        save_state(raw,0,state,obs,mask)
        for tick,command in enumerate(fixed_commands()):
            raw["commands"][tick],raw["mask"][tick]=command,mask
            counts["native_step_attempts"]+=1
            obs,_,done,truncated,info=env.step(command.copy())
            counts["native_steps"]+=1
            state=snapshot()
            raw["completed_steps"][...]=tick+1
            save_state(raw,tick+1,state,obs,mask)
            raw["sinr"][tick],raw["connections"][tick]=state["sinr"],state["connections"]
            raw["postmove_observations"][tick]=obs
            metric=service_metrics(state["sinr"],state["connections"])
            raw["reward"][tick]=sum(map(float,info["rewards_dict"].values()))
            raw["served"][tick],raw["quality"][tick]=metric["served"],metric["quality"]
            assert bool(done or truncated)==(tick==7)
            if tick+1 in (3,7):
                mask=5 if tick+1==3 else 18
                counts["mask_refresh_attempts"]+=1
                raw["refresh_attempted"][tick+1]=True
                refreshed=env.env.set_transmitter_mask(p.mask_array(mask))
                counts["mask_refreshes"]+=1
                raw["refresh_completed"][tick+1]=True
                obs=env._dict_to_array(refreshed)
                state=snapshot()
                save_state(raw,tick+1,state,obs,mask)
    except Exception as exc:
        failure=exc
    finally:
        raw["failure_type"]=np.array("" if failure is None else type(failure).__name__)
        raw["failure_message"]=np.array("" if failure is None else str(failure))
        if correlated:
            after=env.env.physical_counters
            raw["physical_counter_names"]=np.asarray(sorted(after))
            raw["physical_counter_values"]=np.asarray([after[k]-before.get(k,0) for k in sorted(after)],np.int64)
    return raw,dict(counts),failure


def check_old_constructor(raw,counts):
    world=int(raw["world"])
    positions,users=_geometry(world,counts)
    residual=np.zeros((5,50))
    loss,air=_losses(positions,users,residual,counts)
    radio=_radio(loss,air,31,positions,users,0,int(raw["horizon"]),counts)
    for key,value in dict(positions=positions,users=users,residual=residual,user_loss=loss,
        sinr=radio[0],peer_sinr=radio[1],connections=radio[2],observations=radio[3],transmitter_mask=np.ones(5,bool)).items():
        np.testing.assert_array_equal(raw[key],value)
    assert int(raw["constructor_reset_calls"])==1 and int(raw["tick"])==0
    counts["reference_native_constructors_verified"]+=1


def check_fixed(raw,correlated,counts):
    assert int(raw["completed_steps"])==8 and str(raw["failure_type"])==""
    positions,users=_geometry(c.FIXTURE_SEED,counts)
    np.testing.assert_array_equal(raw["users"],users)
    residual=0.*_innovation(c.FIXTURE_SEED,0,counts) if correlated else np.zeros((5,50))
    loss,air=_losses(positions,users,residual,counts)
    mask=31
    radio=_radio(loss,air,mask,positions,users,0,8,counts)

    def state(tick):
        for name,value in dict(positions=positions,residual=residual,loss=loss,state_sinr=radio[0],
            peer_sinr=radio[1],state_connections=radio[2],observations=radio[3]).items():
            np.testing.assert_array_equal(raw[name][tick],value)
        assert int(raw["state_mask"][tick])==mask

    state(0)
    for tick,command in enumerate(fixed_commands()):
        np.testing.assert_array_equal(raw["commands"][tick],command)
        assert int(raw["mask"][tick])==mask
        moved=np.clip(positions+command*30.,(0.,0.,50.),(1000.,1000.,150.))
        if correlated:
            rho=np.exp(-np.linalg.norm(moved-positions,axis=1)/17.62)[:,None]
            residual=rho*residual+0.*np.sqrt(1.-rho*rho)*_innovation(c.FIXTURE_SEED,tick+1,counts)
        positions=moved
        loss,air=_losses(positions,users,residual,counts)
        radio=_radio(loss,air,mask,positions,users,tick+1,8,counts)
        for name,value in (("sinr",radio[0]),("connections",radio[2]),("postmove_observations",radio[3])):
            np.testing.assert_array_equal(raw[name][tick],value)
        metric=service_metrics(radio[0],radio[2])
        counts["reference_native_service_calls"]+=1
        for name,key in (("reward","J"),("quality","quality"),("served","served")):
            assert abs(raw[name][tick]-metric[key])<=1e-12
        if tick+1 in (3,7):
            mask=5 if tick+1==3 else 18
            radio=_radio(loss,air,mask,positions,users,tick+1,8,counts)
            counts["reference_native_arrival_refreshes"]+=1
        state(tick+1)
    expected=np.zeros(9,bool)
    expected[[3,7]]=True
    for key in ("refresh_attempted","refresh_completed"):
        np.testing.assert_array_equal(raw[key],expected)
    if correlated:
        from .read_native import _counter_witness,_expected_counters
        _counter_witness(raw,_expected_counters(8))
    counts["reference_native_episodes_verified"]+=1


def run_correctness(out,launch_sha,admission,entry_started):
    out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    with (out/"started.json").open("x",encoding="utf-8") as stream:
        stream.write('{"fixed_H8_episodes":4}\n')
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    counts=Counter()
    result=dict(status="RUNNING",launch_sha=launch_sha,admission=admission,counts=counts,rows=[],constructors=[],artifacts=[])
    envs=[]
    try:
        captured=[]
        original_reset=MultiUAVEnv.reset

        def capture(base,*args,**kwargs):
            value=original_reset(base,*args,**kwargs)
            captured.append(deepcopy(value))
            return value

        # Capture the unchanged factory's discarded actual return, with no extra
        # reset/observation. Its constructor remains H256; only the fixed episode
        # horizon is set to H8 afterward, before the explicit reset.
        counts["worker_constructor_attempts"]+=1
        with patch.object(MultiUAVEnv,"reset",capture):
            old=old_factory(c.FIXTURE_CONSTRUCTOR_SEEDS[0])
        envs.append(old)
        counts["worker_constructors"]+=1
        assert len(captured)==1
        old_ctor=dict(old_snapshot(old),observations=old._dict_to_array(captured[0][0]),
                      horizon=np.array(256),sigma=np.array(0.),constructor_reset_calls=np.array(1))
        old_ctor_id={}
        result["constructors"].append(old_ctor_id)
        save_evidence(out/"raw"/"constructor_old.npz",old_ctor,result["artifacts"],old_ctor_id)
        check_old_constructor(old_ctor,counts)
        old.env.max_steps=8
        counts["worker_constructor_attempts"]+=1
        zero=make_env(c.FIXTURE_CONSTRUCTOR_SEEDS[1],horizon=8,sigma=0.)
        envs.append(zero)
        counts["worker_constructors"]+=1
        zero_ctor=constructor_witness(zero)
        binding={}
        result["constructors"].append(binding)
        save_evidence(out/"raw"/"constructor_sigma0.npz",zero_ctor,result["artifacts"],binding)
        verify_constructor(zero_ctor,counts)
        fixed=[]
        for env,correlated in ((old,False),(zero,True)):
            raw,actual,failure=fixed_episode(env,correlated)
            binding={}
            result["rows"].append(dict(arm=str(raw["arm"]),raw=binding,actual_counts=actual))
            save_evidence(out/"raw"/(str(raw["arm"])+".npz"),raw,result["artifacts"],binding)
            if failure is not None:
                raise failure
            check_fixed(raw,correlated,counts)
            fixed.append(raw)
        for key in ("users","positions","loss","state_sinr","peer_sinr","sinr","state_connections",
                    "connections","observations","postmove_observations","commands","mask","reward","served","quality"):
            np.testing.assert_array_equal(fixed[0][key],fixed[1][key])
        counts["worker_constructor_attempts"]+=1
        shared=make_env(c.FIXTURE_CONSTRUCTOR_SEEDS[2],horizon=8)
        envs.append(shared)
        counts["worker_constructors"]+=1
        ctor=constructor_witness(shared)
        binding={}
        result["constructors"].append(binding)
        save_evidence(out/"raw"/"constructor_correlated.npz",ctor,result["artifacts"],binding)
        verify_constructor(ctor,counts)
        for arm in c.ARMS:
            raw,row,failure=collect_episode(shared,c.FIXTURE_SEED,arm,horizon=8)
            row["raw"]={}
            result["rows"].append(row)
            save_evidence(out/"raw"/(arm+".npz"),raw,result["artifacts"],row["raw"])
            if failure is not None:
                raise failure
            row["outcome"],arrays=outcomes(raw,unpack_records(raw)["decisions"])
            row["outcome_arrays"]={}
            save_evidence(out/"outcomes"/(arm+".npz"),arrays,result["artifacts"],row["outcome_arrays"])
            row["reading"]=verify_episode(raw,row,arrays,counts)
        assert counts["reference_native_normal_values"]==7250
        assert counts["reference_native_geometry_uniform_values"]==805
        assert counts["reference_native_user_sinr_calls"]==47
        assert counts["reference_current_c_calls"]==40
        result.update(status="VERIFIED_COMPLETE",actual_exposure=dict(constructors=3,constructor_resets=3,
            explicit_resets=4,native_steps=32,current_c_calls=20,physical_normal_values=7250,
            geometry_uniform_values=805,pilot_slots=200,mask_refreshes=8,fits=0,optimizer_updates=0))
    except Exception as exc:
        result.update(status="INCOMPLETE_TECHNICAL_FAILURE",error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    finally:
        for env in envs:
            try:
                env.close()
            except Exception as exc:
                result.setdefault("close_errors",[]).append(dict(type=type(exc).__name__,message=str(exc)))
                result["status"]="INCOMPLETE_TECHNICAL_FAILURE"
        result["physical_lifetime_counts"]=[env.env.physical_counters for env in envs if hasattr(env.env,"physical_counters")]
        result["resources"]=dict(resources(),wall_seconds=time.perf_counter()-entry_started,
                                canonical_artifact_bytes=artifact_bytes(result["artifacts"]))
        write_json(out/"summary.json",result)
    return result
