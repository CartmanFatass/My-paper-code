"""Complete B11 old-mask queries, one setter, four native held movements."""
from pathlib import Path
import time
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.records import add
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import DETERMINISTIC, PROGRAMS, array_digest
from .policies import Policy
from .schema import DECISIONS, dtype, check


def collect_episode(env, *, program, world, tape, parent, out, protocol, counts, inflight):
    wall0,cpu0=time.perf_counter(),time.process_time()
    if program not in PROGRAMS or world not in protocol.worlds or tape not in ((None,) if program in DETERMINISTIC else (0,1)) or env.n_uavs!=5:
        raise ValueError("fixed B11 episode identity required")
    root=None if tape is None else protocol.evaluation_motion_roots[tape]
    identifier=f"evaluation_{program}_w{world}_t{tape}"
    path=Path(out)/"raw"/(identifier+".npz")
    if path.exists():
        raise FileExistsError("episode evidence exists")
    times={f"{part}_{clock}_seconds":0. for part in ("reset","decision_query","mask_refresh","native_step","raw_write") for clock in ("wall","cpu")}
    def elapsed(part,w,c):
        times[part+"_wall_seconds"]+=time.perf_counter()-w
        times[part+"_cpu_seconds"]+=time.process_time()-c
    w,c=time.perf_counter(),time.process_time()
    add(counts,"explicit_reset_calls")
    obs,info=env.reset(seed=world)
    add(counts,"explicit_resets")
    add(counts,"native_dense_power_slots",275)
    base=env.env
    add(counts,"native_unique_distance_pairs",int(base._path_loss_cache_misses))
    positions=np.asarray(info["state_info"]["uav_positions"],dtype=np.float64).copy()
    users=np.asarray(info["state_info"]["user_positions"],dtype=np.float64).copy()
    ep,eu=original_layout(world)
    add(counts,"layout_verification_draws",115)
    if not np.array_equal(ep,positions) or not np.array_equal(eu,users) or base.current_step!=0 or not base.transmitter_mask.all():
        raise AssertionError("original reset/layout contract")
    obs=np.asarray(obs,dtype=np.float32)
    if obs.shape!=(5,104) or not np.isfinite(obs).all():
        raise AssertionError("finite reset local rows")
    elapsed("reset",w,c)
    initial=dict(initial_users=users,initial_sinr=base.sinr_matrix.copy(),initial_peer_sinr=base.uav_sinr_matrix.copy(),
        initial_connections=base.connections.copy(),initial_generation=np.asarray(base._path_loss_cache_generation,dtype=np.int64))
    navs=np.array([initial_nav(row) for row in obs],dtype=np.int64)
    policies=[Policy(program,parent,world=world,agent=i,sampling_root=root) for i in range(5)]
    inflight.update(id=identifier,program=program,world=world,tape=tape,policy_agents=[p.counters for p in policies],times=times)
    raw={key:[] for key in ("observations","commands","reward","served","sinr_quality","sinr","peer_sinr","connections",
        "transmitter_mask","terminated","truncated","step_generation","step_path_loss_misses")}
    raw["positions"]=[positions.copy()]
    decision={key:[] for key in ("nav_pre","nav_next",*DECISIONS)}
    if program=="Hdirect_ZERO":
        decision.update(logits=[],hidden=[],parent_probabilities=[])
    boundary={key:[] for key in ("old_decision_mask","installed_mask","eligible_agent","gate_count_boundary","gate_innovation",
        "gate_prediction_boundary","gate_requested_off","gate_off","gate_forced","refresh_sinr","refresh_peer_sinr",
        "refresh_connections","refresh_observations","refresh_generation","refresh_path_loss_misses")}
    commands=np.zeros((5,3),dtype=np.float32)
    for tick in range(protocol.horizon):
        inflight["tick"]=tick
        if tick%4==0:
            old=base.transmitter_mask.copy()
            eligible=(tick//4)%5
            if not old[eligible]:
                raise AssertionError("eligible must be old-mask ON")
            before=navs.copy()
            answers=[]
            w,c=time.perf_counter(),time.process_time()
            for i,policy in enumerate(policies):
                add(counts,"motion_request_calls")
                answer=policy.query(obs[i].copy(),tick,int(navs[i]))
                add(counts,"motion_requests")
                add(counts,"motion_draws",int(program not in DETERMINISTIC))
                if answer["pending_before"] and (old[i] or answer["requested_off"] or answer["c_available"]):
                    raise AssertionError("consume own old-silent row before setter")
                if not np.array_equal(answer["command"],COMMANDS[answer["motion_index"]]):
                    raise AssertionError("command category identity")
                commands[i]=answer["command"]
                navs[i]=answer["next_nav"]
                answers.append(answer)
            elapsed("decision_query",w,c)
            decision["nav_pre"].append(before)
            decision["nav_next"].append(navs.copy())
            for key in decision:
                if key not in ("nav_pre","nav_next"):
                    source={"policy_scores":"scores","policy_served":"served"}.get(key,key)
                    decision[key].append([answer[source] for answer in answers])
            chosen=answers[eligible]
            mask=np.ones(5,dtype=bool)
            mask[eligible]=not chosen["requested_off"]
            add(counts,"gate_opportunities")
            add(counts,"gate_opportunity_calls")
            generation,misses=base._path_loss_cache_generation,base._path_loss_cache_misses
            w,c=time.perf_counter(),time.process_time()
            add(counts,"mask_install_calls")
            refreshed=base.set_transmitter_mask(mask)
            add(counts,"mask_installs")
            add(counts,"mask_refresh_dense_sinr_slots",275)
            add(counts,"native_dense_power_slots",275)
            rows=env._dict_to_array(refreshed).astype(np.float32)
            refresh_misses=int(base._path_loss_cache_misses-misses)
            if base.current_step!=tick or base._path_loss_cache_generation!=generation or refresh_misses!=0 or not np.array_equal(base.uav_positions,positions) or not np.array_equal(base.transmitter_mask,mask):
                raise AssertionError("setter geometry/time/cache/mask invariant")
            elapsed("mask_refresh",w,c)
            for key,value in (("old_decision_mask",old),("installed_mask",mask.copy()),("eligible_agent",eligible),
                ("gate_count_boundary",chosen["gate_count"]),("gate_innovation",-1.),("gate_prediction_boundary",0.),
                ("gate_requested_off",chosen["requested_off"]),("gate_off",chosen["requested_off"]),("gate_forced",False),
                ("refresh_sinr",base.sinr_matrix.copy()),("refresh_peer_sinr",base.uav_sinr_matrix.copy()),
                ("refresh_connections",base.connections.copy()),("refresh_observations",rows.copy()),
                ("refresh_generation",generation),("refresh_path_loss_misses",refresh_misses)):
                boundary[key].append(value)
        raw["observations"].append(obs.copy())
        raw["commands"].append(commands.copy())
        raw["transmitter_mask"].append(base.transmitter_mask.copy())
        w,c=time.perf_counter(),time.process_time()
        add(counts,"native_step_calls")
        nxt,_,terminated,truncated,info=env.step(commands.copy())
        for key,amount in (("native_steps",1),("evaluation_native_steps",1),("native_uav_ticks",5),
                           ("native_dense_power_slots",275),("native_unique_distance_pairs",int(base._path_loss_cache_misses))):
            add(counts,key,amount)
        elapsed("native_step",w,c)
        reward,served,quality=native_reading(info)
        global_info=info["infos_dict"]["uav_0"]["global"]
        after=np.asarray(info["state_info"]["uav_positions"],dtype=np.float64).copy()
        if not np.array_equal(after,np.clip(positions+commands.astype(np.float64)*30.,[0.,0.,50.],[1000.,1000.,150.])):
            raise AssertionError("clipped held movement")
        raw["positions"].append(after)
        for key,value in (("reward",reward),("served",served),("sinr_quality",quality),
            ("sinr",np.asarray(global_info["sinr_matrix"]).copy()),("peer_sinr",base.uav_sinr_matrix.copy()),
            ("connections",np.asarray(global_info["connections"]).copy()),("terminated",bool(terminated)),
            ("truncated",bool(truncated)),("step_generation",int(base._path_loss_cache_generation)),
            ("step_path_loss_misses",int(base._path_loss_cache_misses))):
            raw[key].append(value)
        if bool(terminated)!=(tick+1==protocol.horizon) or bool(truncated):
            raise AssertionError("complete terminal clock")
        obs=np.asarray(nxt,dtype=np.float32)
        if obs.shape!=(5,104) or not np.isfinite(obs).all():
            raise AssertionError("finite next rows")
        positions=after
    arrays={key:np.asarray(value,dtype=dtype(key)) for key,value in {**raw,**decision,**boundary}.items()}
    arrays.update(initial,terminal_observation=obs.copy(),terminal_pending=np.array([p.pending is not None for p in policies]),
                  decision_ticks=np.arange(0,protocol.horizon,4,dtype=np.int64))
    check(arrays,protocol.horizon,program)
    w,c=time.perf_counter(),time.process_time()
    np.savez_compressed(path,**arrays)
    identity=file_identity(path)
    identity["path"]=str(path.relative_to(out))
    elapsed("raw_write",w,c)
    from .reading import episode_metrics
    row=dict(id=identifier,kind="evaluation",program=program,world=world,tape=tape,motion_root=root,raw=identity,
        **episode_metrics(arrays),**times,policy_counts=sum_counts(p.counters for p in policies),
        raw_array_bytes=sum(a.nbytes for a in arrays.values()),initial_state_sha256=array_digest(arrays["positions"][0],users),
        cpu_seconds=time.process_time()-cpu0,wall_seconds=time.perf_counter()-wall0,
        timing_scope="reset, old-mask private policy queries, setter, native steps, checks and raw write")
    add(counts,"complete_episodes")
    add(counts,"evaluation_episodes")
    inflight.clear()
    return row
