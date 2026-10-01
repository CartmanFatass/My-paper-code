"""Complete native/payload readings; episodes, never particles, are replicates."""

from __future__ import annotations

import math

import numpy as np

from . import contract as c
from . import protocol as p


METRICS = ("payload_J", "raw_J", "mean_served", "payload_served", "mean_quality", "payload_quality",
    "mean_age", "F_user", "max_unserved_gap", "mean_user_max_gap", "max_closed_gap",
    "max_left_censored_gap", "max_right_censored_gap", "never_served", "age_p95",
    "terminal_mean_age", "terminal_max_age", "service_p10", "min_served", "zero_service_steps",
    "longest_zero_service", "mean_path_length_m", "transmitter_on_ticks", "mask_flips",
    "deadline_misses", "delivered_command_changes", "delivered_mask_changes",
    "round_cpu_seconds", "round_wall_seconds", "round_max_wall_seconds", "c_cpu_seconds",
    "report_bytes_sent", "command_bytes_sent", "attempted_bytes", "sent_bytes",
    "candidate_plans", "candidate_fleet_scores", "candidate_sinr_entries", "model_normal_values")


def gap_rows(contacts):
    rows = []
    h,u = contacts.shape
    for user in range(u):
        denied = ~contacts[:,user]
        edges = np.diff(np.r_[False,denied,False].astype(np.int8))
        starts, ends = np.flatnonzero(edges==1), np.flatnonzero(edges==-1)
        rows.extend((user,int(a),int(b),int(b-a),int(a==0),int(b==h)) for a,b in zip(starts,ends))
    return np.asarray(rows,np.int64).reshape(-1,6)


def outcomes(raw, records):
    h = int(raw["completed_steps"])
    p.require(h == int(raw["horizon"]),"outcome requires complete episode")
    contacts = raw["connections"].any(axis=1)
    tick = np.arange(h)[:,None]
    last = np.maximum.accumulate(np.where(contacts,tick,-1),axis=0)
    ages = (tick-last).astype(np.int16)
    gaps = gap_rows(contacts)
    per_mean_age = ages.mean(axis=0)
    user_max = np.asarray([max((row[3] for row in gaps if row[0]==user),default=0) for user in range(c.N_USERS)])
    per_path = np.linalg.norm(np.diff(raw["positions"],axis=0),axis=2).sum(axis=0)
    weights = np.asarray([c.payload_weight(t) for t in range(h)])
    outage_gaps = gap_rows((raw["served"]>0)[:,None])
    model_counts = {}
    for record in records:
        for key,value in record["counts"].items():
            model_counts[key] = model_counts.get(key,0)+value
    value = dict(payload_J=float(np.mean(raw["reward"]*weights)),raw_J=float(raw["reward"].mean()),
        mean_served=float(raw["served"].mean()),payload_served=float(np.mean(raw["served"]*weights)),
        mean_quality=float(raw["quality"].mean()),payload_quality=float(np.mean(raw["quality"]*weights)),
        mean_age=float(ages.mean()),F_user=float(per_mean_age.max()),max_unserved_gap=int(user_max.max()),
        mean_user_max_gap=float(user_max.mean()),never_served=int((~contacts.any(axis=0)).sum()),
        age_p95=float(np.quantile(ages,.95)),terminal_mean_age=float(ages[-1].mean()),terminal_max_age=int(ages[-1].max()),
        service_p10=float(np.quantile(raw["served"],.1)),min_served=int(raw["served"].min()),
        zero_service_steps=int((raw["served"]==0).sum()),longest_zero_service=int(max(outage_gaps[:,3],default=0)),
        mean_path_length_m=float(per_path.mean()),transmitter_on_ticks=sum(int(x).bit_count() for x in raw["mask"]),
        mask_flips=sum(int(a^b).bit_count() for a,b in zip(raw["mask"][:-1],raw["mask"][1:])),
        deadline_misses=sum(not r["timely"] for r in records),
        delivered_command_changes=sum(r["timely"] and not np.array_equal(r["executed_commands"],raw["commands"][r["tick"]]) for r in records),
        delivered_mask_changes=sum(r["timely"] and r["executed_mask"] != int(raw["mask"][r["tick"]]) for r in records),
        round_cpu_seconds=float(raw["round_cpu"].sum()),round_wall_seconds=float(raw["round_wall"].sum()),
        round_max_wall_seconds=float(raw["round_wall"].max()),c_cpu_seconds=float(raw["c_cpu"].sum()),
        attempted_bytes=sum(r["attempted_bytes"] for r in records),sent_bytes=sum(r["sent_bytes"] for r in records),
        payload_time=float(weights.sum()),pilot_slots=int(raw["pilot_attempted"].sum())*c.PILOT_SLOTS,
        pilot_seconds=int(raw["pilot_attempted"].sum())*c.PILOT_SECONDS,
        map_bytes=int(raw["map_packet"].nbytes),
        per_user_mean_age=per_mean_age.tolist(),per_user_max_gap=user_max.tolist(),
        per_user_service_ticks=contacts.sum(axis=0).tolist(),per_uav_path_metres=per_path.tolist(),
        per_uav_transmitter_ticks=[sum(bool(int(mask)&(1<<i)) for mask in raw["mask"]) for i in range(c.N_UAVS)],
        sensor_saturation={key:int(raw[key].sum()) for key in ("clipped_low","clipped_high","edge_low","edge_high")})
    for key in ("report_bytes_sent","command_bytes_sent","candidate_plans","candidate_fleet_scores",
                "candidate_sinr_entries","model_normal_values"):
        value[key] = model_counts.get(key,0)
    for name,selected in (("closed",(gaps[:,4]==0)&(gaps[:,5]==0)),
                          ("left_censored",gaps[:,4]==1),("right_censored",gaps[:,5]==1)):
        value["max_"+name+"_gap"] = int(max(gaps[selected,3],default=0))
    return value,dict(contacts=contacts,ages=ages,gaps=gaps,per_user_mean_age=per_mean_age,
                      per_user_max_gap=user_max,per_uav_path_metres=per_path,weights=weights)


def describe(values):
    values = np.asarray(values,np.float64)
    p.require(len(values)>0 and np.isfinite(values).all(),"finite descriptive sample required")
    mean = float(values.mean())
    sd = float(values.std(ddof=1)) if len(values)>1 else 0.
    half = 1.96*sd/math.sqrt(len(values))
    return dict(values=values.tolist(),n=len(values),mean=mean,sd=sd,descriptive_196se=[mean-half,mean+half],
                positive=int((values>0).sum()),negative=int((values<0).sum()),zero=int((values==0).sum()))


def paired(rows):
    by = {(row["arm"],row["world"]):row["outcome"] for row in rows}
    p.require(len(by)==len(rows) and set(by)=={(arm,world) for arm in c.ARMS for world in c.WORLD_SEEDS},
              "complete fixed paired panel required")
    levels = {arm:{key:describe([by[arm,world][key] for world in c.WORLD_SEEDS]) for key in METRICS} for arm in c.ARMS}
    contrast = {key:describe([by["U32",world][key]-by["P",world][key] for world in c.WORLD_SEEDS]) for key in METRICS}
    return dict(worlds=list(c.WORLD_SEEDS),levels=levels,contrast_U32_minus_P=contrast,
                primary="payload_J; positive favors U32",scope="32 paired worlds; descriptive 1.96SE, zero fits; particles are nested")
