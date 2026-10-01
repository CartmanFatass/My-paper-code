"""Data-only reductions from persisted primitive and age/gap arrays."""

import math

import numpy as np

from .config import ARMS, PACKAGES, PROGRAMS, validate_rows


def describe(values):
    values = np.asarray(values, np.float64)
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("finite world sample required")
    mean = float(values.mean())
    sd = float(values.std(ddof=1)) if len(values) > 1 else 0.
    half = 1.96 * sd / math.sqrt(len(values))
    return dict(values=values.tolist(), n=len(values), mean=mean, sd=sd,
                descriptive_196se=[mean-half, mean+half],
                positive=int((values > 0).sum()), negative=int((values < 0).sum()),
                zero=int((values == 0).sum()))


def companions(raw, arrays, program):
    """Window ages inherit episode history; they are never restarted at tail entry."""
    h, delivery = int(raw["horizon"]), PACKAGES[program]["delivery"]
    result = {}
    for name, start, stop in (("startup", 0, delivery), ("final4", h-4, h)):
        weights = arrays["weights"][start:stop]
        ages, contacts = arrays["ages"][start:stop], arrays["contacts"][start:stop]
        window = dict(start=start, stop=stop, ticks=stop-start, payload_time=float(weights.sum()))
        for metric, field in (("J", "reward"), ("served", "served"), ("quality", "quality")):
            values = raw[field][start:stop]
            window["raw_"+metric] = float(values.mean())
            window["payload_"+metric] = float(np.mean(values*weights))
        window.update(mean_age=float(ages.mean()), max_age=int(ages.max()),
                      per_user_mean_age=ages.mean(axis=0).tolist(),
                      per_user_service_ticks=contacts.sum(axis=0).tolist(),
                      transmitter_on_ticks=sum(int(x).bit_count() for x in raw["mask"][start:stop]),
                      path_metres=float(np.linalg.norm(np.diff(raw["positions"][start:stop+1], axis=0), axis=2).sum()))
        result[name] = window
    last_report = h-4
    result["delivery"] = dict(startup_ticks=delivery, scored_suffix_ticks=h-delivery,
        suffix_payload_time=float(arrays["weights"][delivery:].sum()),
        last_report_tick=last_report, last_delivery_tick=last_report+delivery,
        last_candidate_ticks=h-last_report-delivery,
        arrival_refreshes=int(raw["refresh_completed"].sum()))
    if result["delivery"]["arrival_refreshes"] != h//4:
        raise ValueError("delivery refresh count differs")
    return result


def verify_companions(raw, arrays, program, saved):
    """Independent scalar window sums; uses no policy, radio or random generator."""
    h, d = int(raw["horizon"]), PACKAGES[program]["delivery"]
    expected = {}
    for name, start, stop in (("startup", 0, d), ("final4", h-4, h)):
        n = stop-start
        weights = [float(arrays["weights"][t]) for t in range(start, stop)]
        row = dict(start=start, stop=stop, ticks=n, payload_time=sum(weights))
        for metric, field in (("J", "reward"), ("served", "served"), ("quality", "quality")):
            values = [float(raw[field][t]) for t in range(start, stop)]
            row["raw_"+metric] = sum(values)/n
            row["payload_"+metric] = sum(v*w for v, w in zip(values, weights))/n
        per_age = [sum(int(arrays["ages"][t,u]) for t in range(start,stop))/n for u in range(50)]
        row.update(mean_age=sum(per_age)/50,
            max_age=max(int(arrays["ages"][t,u]) for t in range(start,stop) for u in range(50)),
            per_user_mean_age=per_age,
            per_user_service_ticks=[sum(bool(arrays["contacts"][t,u]) for t in range(start,stop)) for u in range(50)],
            transmitter_on_ticks=sum(bool(int(raw["mask"][t]) & (1<<i)) for t in range(start,stop) for i in range(5)),
            path_metres=sum(math.sqrt(sum(float(raw["positions"][t+1,i,k]-raw["positions"][t,i,k])**2 for k in range(3)))
                            for t in range(start,stop) for i in range(5)))
        expected[name] = row
    expected["delivery"] = dict(startup_ticks=d, scored_suffix_ticks=h-d,
        suffix_payload_time=sum(float(arrays["weights"][t]) for t in range(d,h)),
        last_report_tick=h-4, last_delivery_tick=h-4+d, last_candidate_ticks=4-d,
        arrival_refreshes=sum(bool(x) for x in raw["refresh_completed"]))
    close_tree(saved, expected)
    if expected["delivery"]["arrival_refreshes"] != h//4:
        raise ValueError("delivery refresh count differs")


def close_tree(actual, expected):
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError("reduction keys differ")
        for key in expected:
            close_tree(actual[key], expected[key])
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError("reduction length differs")
        for a, b in zip(actual, expected):
            close_tree(a, b)
    elif isinstance(expected, float):
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError("reduction float differs")
    elif actual != expected:
        raise ValueError("reduction value differs")


def pair_actions(left, right):
    by = {str(raw["program"]): raw for raw in (left, right)}
    if set(by) != set(PROGRAMS):
        raise ValueError("action pair program alias")
    full, prior = by["U32_FULL"], by["P_PRIOR"]
    for program, raw in by.items():
        if str(raw["arm"]) != ARMS[program]:
            raise ValueError("action pair arm alias")
    if int(full["world"]) != int(prior["world"]) or int(full["horizon"]) != int(prior["horizon"]):
        raise ValueError("action pair identity differs")
    for field in ("users", "map_packet"):
        np.testing.assert_array_equal(full[field], prior[field])
    for field in ("positions", "residual"):
        np.testing.assert_array_equal(full[field][0], prior[field][0])
    command = np.any(full["commands"] != prior["commands"], axis=2)
    proposal = np.any(full["proposals"] != prior["proposals"], axis=2)
    return dict(world=int(full["world"]),
        command_difference_ticks=int(command.any(axis=1).sum()),
        command_difference_uav_ticks=int(command.sum()),
        mask_difference_ticks=int((full["mask"] != prior["mask"]).sum()),
        transmitter_bit_difference_ticks=sum(int(a^b).bit_count() for a,b in zip(full["mask"],prior["mask"])),
        proposal_difference_reports=int(proposal.any(axis=1).sum()),
        proposal_difference_uav_reports=int(proposal.sum()),
        post_c_nav_difference_entries=int((full["post_c_nav"] != prior["post_c_nav"]).sum()),
        physical_innovation_address=[0x52465048,29640001,int(full["world"]),"state_tick"],
        paired_initial_state=True)


def verify_actions(left, right, saved):
    by = {str(raw["program"]):raw for raw in (left,right)}
    full, prior = by["U32_FULL"], by["P_PRIOR"]
    h = int(full["horizon"])
    expected = dict(world=int(full["world"]),
        command_difference_ticks=sum(any(full["commands"][t,i,k] != prior["commands"][t,i,k] for i in range(5) for k in range(3)) for t in range(h)),
        command_difference_uav_ticks=sum(any(full["commands"][t,i,k] != prior["commands"][t,i,k] for k in range(3)) for t in range(h) for i in range(5)),
        mask_difference_ticks=sum(int(a) != int(b) for a,b in zip(full["mask"],prior["mask"])),
        transmitter_bit_difference_ticks=sum(bool(int(a)&(1<<i)) != bool(int(b)&(1<<i)) for a,b in zip(full["mask"],prior["mask"]) for i in range(5)),
        proposal_difference_reports=sum(any(full["proposals"][r,i,k] != prior["proposals"][r,i,k] for i in range(5) for k in range(3)) for r in range(h//4)),
        proposal_difference_uav_reports=sum(any(full["proposals"][r,i,k] != prior["proposals"][r,i,k] for k in range(3)) for r in range(h//4) for i in range(5)),
        post_c_nav_difference_entries=sum(full["post_c_nav"][r,i] != prior["post_c_nav"][r,i] for r in range(h//4) for i in range(5)),
        physical_innovation_address=[0x52465048,29640001,int(full["world"]),"state_tick"], paired_initial_state=True)
    close_tree(saved, expected)
    # Pairing checks only initial state, never later path-dependent residual equality.
    pair_actions(left,right)


def paired(rows, spec):
    validate_rows(rows, spec)
    by = {(r["program"],r["world"]):r for r in rows}
    worlds = spec["worlds"]
    metrics = [key for key,value in rows[0]["outcome"].items() if isinstance(value,(int,float))]

    def panel(get):
        keys = list(get(rows[0]))
        return dict(levels={p:{k:describe([get(by[p,w])[k] for w in worlds]) for k in keys} for p in PROGRAMS},
            contrast_U32_FULL_minus_PRIOR={k:describe([get(by["U32_FULL",w])[k]-get(by["P_PRIOR",w])[k] for w in worlds]) for k in keys})

    result = dict(worlds=worlds, independent_units="worlds; users and particles nested",
        primary="complete payload_J = sum(payload_weight * native_J) / H; positive favors U32_FULL",
        complete=panel(lambda r:{k:r["outcome"][k] for k in metrics}), companions={})
    for window in ("startup", "final4"):
        keys = [k for k,v in rows[0]["companions"][window].items()
                if isinstance(v,(int,float)) and k not in ("start","stop","ticks")]
        result["companions"][window] = panel(lambda r:{k:r["companions"][window][k] for k in keys})
    result["per_world_user_differences"] = [dict(world=w, **{
        key:[a-b for a,b in zip(by["U32_FULL",w]["outcome"][key],by["P_PRIOR",w]["outcome"][key])]
        for key in ("per_user_mean_age","per_user_service_ticks","per_user_max_gap")}) for w in worlds]
    return result


def verify_pairing(rows, spec, saved):
    """Scalar independent world means and intervals, including window companions."""
    validate_rows(rows, spec)
    by = {(r["program"],r["world"]):r for r in rows}
    n = len(spec["worlds"])
    for section, get in [(saved["complete"], lambda r:r["outcome"])] + [
            (saved["companions"][name], lambda r,name=name:r["companions"][name]) for name in ("startup","final4")]:
        for program, descriptions in section["levels"].items():
            for key,description in descriptions.items():
                values = [get(by[program,w])[key] for w in spec["worlds"]]
                _verify_description(description, values, n)
        for key,description in section["contrast_U32_FULL_minus_PRIOR"].items():
            values = [get(by["U32_FULL",w])[key]-get(by["P_PRIOR",w])[key] for w in spec["worlds"]]
            _verify_description(description, values, n)
    close_tree(saved, paired(rows,spec))


def _verify_description(description, values, n):
    mean = sum(values)/n
    sd = math.sqrt(sum((v-mean)**2 for v in values)/(n-1)) if n>1 else 0.
    half = 1.96*sd/math.sqrt(n)
    close_tree(description, dict(values=values,n=n,mean=mean,sd=sd,
        descriptive_196se=[mean-half,mean+half],positive=sum(v>0 for v in values),
        negative=sum(v<0 for v in values),zero=sum(v==0 for v in values)))
