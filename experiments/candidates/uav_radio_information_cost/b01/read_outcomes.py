"""Scalar native service/age readings and two independent current-C passes."""

from __future__ import annotations

from collections import Counter
import math

import numpy as np

from . import contract as c


from experiments.candidates.uav_radio_uncertainty.b01.read_outcomes import equal_tree, verify_c


def verify_outcomes(raw,records,outcome,arrays,counts):
    h = int(raw["horizon"])
    contacts = np.empty((h,50),bool)
    ages = np.empty((h,50),np.int16)
    rows, per_mean, per_max, service_ticks = [],[],[],[]
    for user in range(50):
        age,start,maximum,total,hits = 0,None,0,0,0
        for tick in range(h):
            contact = any(bool(raw["connections"][tick,i,user]) for i in range(5))
            contacts[tick,user] = contact
            if contact:
                if start is not None:
                    gap = tick-start
                    rows.append((user,start,tick,gap,int(start==0),0))
                    maximum = max(maximum,gap)
                    start = None
                age = 0
                hits += 1
            else:
                if start is None:
                    start = tick
                age += 1
            ages[tick,user] = age
            total += age
        if start is not None:
            gap = h-start
            rows.append((user,start,h,gap,int(start==0),1))
            maximum = max(maximum,gap)
        per_mean.append(total/h)
        per_max.append(maximum)
        service_ticks.append(hits)
    gaps = np.asarray(rows,np.int64).reshape(-1,6)
    path = [sum(math.sqrt(sum(float(raw["positions"][t+1,i,d]-raw["positions"][t,i,d])**2 for d in range(3))) for t in range(h)) for i in range(5)]
    weights = np.asarray([.9 if str(raw["arm"])=="P_FULL" and t%4==0 else 1. for t in range(h)])
    for key,value in dict(contacts=contacts,ages=ages,gaps=gaps,per_user_mean_age=np.asarray(per_mean),
                          per_user_max_gap=np.asarray(per_max),weights=weights).items():
        np.testing.assert_array_equal(arrays[key],value)
    np.testing.assert_allclose(arrays["per_uav_path_metres"],path,rtol=0,atol=1e-9)
    longest=run=0
    for served in raw["served"]:
        run = run+1 if served==0 else 0
        longest=max(longest,run)
    counts_model = Counter()
    for record in records:
        counts_model.update(record["counts"])
    # Independent positive summation order can differ by a few float64 ulps.
    expected = dict(payload_J=sum(float(raw["reward"][t])*weights[t] for t in range(h))/h,
        raw_J=sum(map(float,raw["reward"]))/h,mean_served=sum(map(float,raw["served"]))/h,
        payload_served=sum(float(raw["served"][t])*weights[t] for t in range(h))/h,
        mean_quality=sum(map(float,raw["quality"]))/h,
        payload_quality=sum(float(raw["quality"][t])*weights[t] for t in range(h))/h,
        mean_age=sum(int(x) for x in ages.flat)/(h*50),F_user=max(per_mean),max_unserved_gap=max(per_max),
        mean_user_max_gap=sum(per_max)/50,never_served=sum(x==0 for x in service_ticks),
        age_p95=float(np.quantile(ages,.95)),terminal_mean_age=sum(map(int,ages[-1]))/50,
        terminal_max_age=max(map(int,ages[-1])),service_p10=float(np.quantile(raw["served"],.1)),
        min_served=min(map(int,raw["served"])),zero_service_steps=sum(x==0 for x in raw["served"]),
        longest_zero_service=longest,mean_path_length_m=sum(path)/5,
        transmitter_on_ticks=sum(int(x).bit_count() for x in raw["mask"]),
        mask_flips=sum(int(a^b).bit_count() for a,b in zip(raw["mask"][:-1],raw["mask"][1:])),
        deadline_misses=sum(not r["timely"] for r in records),
        delivered_command_changes=sum(bool(r["timely"]) and not np.array_equal(r["executed_commands"],raw["commands"][r["tick"]]) for r in records),
        delivered_mask_changes=sum(bool(r["timely"]) and r["executed_mask"]!=raw["mask"][r["tick"]] for r in records),
        round_cpu_seconds=sum(map(float,raw["round_cpu"])),round_wall_seconds=sum(map(float,raw["round_wall"])),
        round_max_wall_seconds=max(map(float,raw["round_wall"])),c_cpu_seconds=sum(map(float,raw["c_cpu"])),
        attempted_bytes=sum(r["attempted_bytes"] for r in records),sent_bytes=sum(r["sent_bytes"] for r in records),
        payload_time=sum(weights),pilot_slots=int(raw["pilot_attempted"].sum())*50,
        pilot_seconds=int(raw["pilot_attempted"].sum())*.1,map_bytes=400,
        per_user_mean_age=per_mean,per_user_max_gap=per_max,per_user_service_ticks=service_ticks,
        per_uav_path_metres=path,per_uav_transmitter_ticks=[sum(bool(int(mask)&(1<<i)) for mask in raw["mask"]) for i in range(5)],
        sensor_saturation={key:int(raw[key].sum()) for key in ("clipped_low","clipped_high","edge_low","edge_high")} if str(raw["arm"])=="P_FULL" else {})
    for key in ("report_bytes_sent","command_bytes_sent","candidate_plans","candidate_fleet_scores","candidate_sinr_entries","model_normal_values"):
        expected[key]=counts_model[key]
    expected["max_closed_gap"] = max((row[3] for row in rows if not row[4] and not row[5]),default=0)
    expected["max_left_censored_gap"] = max((row[3] for row in rows if row[4]),default=0)
    expected["max_right_censored_gap"] = max((row[3] for row in rows if row[5]),default=0)
    assert set(outcome)==set(expected)
    for key,value in expected.items():
        if key in ("per_uav_path_metres","mean_path_length_m"):
            np.testing.assert_allclose(outcome[key],value,rtol=0,atol=1e-9)
        elif isinstance(value,(float,np.floating)):
            assert abs(outcome[key]-value)<=1e-10, key
        else:
            equal_tree(outcome[key],value)
    counts["reference_user_age_updates"] += h*50
    counts["reference_gap_rows"] += len(gaps)
    return expected


def verify_pairing(rows,paired):
    """Scalar independent means/1.96SE and every fixed world-signed contrast."""
    assert paired["worlds"]==list(c.WORLD_SEEDS)
    by={(row["arm"],row["world"]):row["outcome"] for row in rows}

    def check(description,values):
        assert description["values"]==values and description["n"]==32
        mean=sum(values)/32
        sd=math.sqrt(sum((value-mean)**2 for value in values)/31)
        half=1.96*sd/math.sqrt(32)
        assert description["positive"]==sum(x>0 for x in values)
        assert description["negative"]==sum(x<0 for x in values)
        assert description["zero"]==sum(x==0 for x in values)
        for actual,expected in ((description["mean"],mean),(description["sd"],sd),
            (description["descriptive_196se"][0],mean-half),(description["descriptive_196se"][1],mean+half)):
            assert math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-10)

    for arm in c.ARMS:
        for key,description in paired["levels"][arm].items():
            check(description,[by[arm,world][key] for world in c.WORLD_SEEDS])
    for key,description in paired["contrast_FULL_minus_PRIOR"].items():
        check(description,[by["P_FULL",world][key]-by["P_PRIOR",world][key] for world in c.WORLD_SEEDS])


def verify_actions(left,right,saved):
    """Independent scalar reading; comparisons do not force shared later histories."""
    by = {str(raw["arm"]):raw for raw in (left,right)}
    full,prior = by["P_FULL"],by["P_PRIOR"]
    assert int(full["world"])==int(prior["world"])
    h=int(full["horizon"])
    command=[[any(full["commands"][t,i,d]!=prior["commands"][t,i,d] for d in range(3))
              for i in range(5)] for t in range(h)]
    proposal=[[any(full["proposals"][r,i,d]!=prior["proposals"][r,i,d] for d in range(3))
               for i in range(5)] for r in range(h//4)]
    expected=dict(world=int(full["world"]),command_difference_ticks=sum(any(row) for row in command),
        command_difference_uav_ticks=sum(sum(row) for row in command),
        mask_difference_ticks=sum(int(a)!=int(b) for a,b in zip(full["mask"],prior["mask"])),
        transmitter_bit_difference_ticks=sum(bool(int(a)&(1<<i))!=bool(int(b)&(1<<i))
            for a,b in zip(full["mask"],prior["mask"]) for i in range(5)),
        proposal_difference_reports=sum(any(row) for row in proposal),
        proposal_difference_uav_reports=sum(sum(row) for row in proposal),
        post_c_nav_difference_entries=sum(full["post_c_nav"][r,i]!=prior["post_c_nav"][r,i]
            for r in range(h//4) for i in range(5)))
    equal_tree(saved,expected)
