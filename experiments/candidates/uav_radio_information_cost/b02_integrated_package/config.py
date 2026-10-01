"""Fixed B02 identities, with separate main and paired integration exposure."""

DIRECTION = "uav_radio_information_cost"
PROGRAMS = ("U32_FULL", "P_PRIOR")
ARMS = {"U32_FULL": "U32", "P_PRIOR": "P_PRIOR"}
SOURCES = {
    "U32_FULL": "9b6f493b343c2939b374a1ce21384266d3257456",
    "P_PRIOR": "a80e2be9e3341b3bebfa743dacfda5e4ff13d977",
}
PACKAGES = {
    "U32_FULL": dict(protocol=5, delivery=3, compute_seconds=1.336,
                     round_bytes=391, pilot_seconds=.1, payload_report_weight=.9),
    "P_PRIOR": dict(protocol=6, delivery=2, compute_seconds=1.436,
                    round_bytes=141, pilot_seconds=0., payload_report_weight=1.),
}


def specification(kind):
    if kind == "main":
        worlds, horizon, constructor = list(range(29661000, 29661032)), 256, 29661999
    elif kind == "check":
        worlds, horizon, constructor = [29661900], 8, 29661998
    else:
        raise ValueError("unknown B02 exposure")
    order = [(PROGRAMS if index % 2 == 0 else PROGRAMS[::-1])
             for index in range(len(worlds))]
    return dict(direction=DIRECTION, kind=kind, worlds=worlds, horizon=horizon,
                constructor_seed=constructor, programs=list(PROGRAMS), arms=dict(ARMS),
                order=[list(pair) for pair in order], inherited_sources=dict(SOURCES),
                packages=PACKAGES, numpy="1.26.3", fits=0, optimizer_updates=0,
                physical_address=[0x52465048, 29640001, "world", "state_tick"],
                model_address=[0x52464d43, 29640002, "world", "report_tick"],
                base_particles=16, signed_particles=32)


def expected_order(spec):
    return [(program, world) for world, pair in zip(spec["worlds"], spec["order"])
            for program in pair]


def validate_rows(rows, spec):
    if [(row["program"], row["world"]) for row in rows] != expected_order(spec):
        raise ValueError("missing, duplicate or reordered program/world")
    for row in rows:
        if row["arm"] != ARMS[row["program"]]:
            raise ValueError("literal arm alias")
        if row["steps"] != spec["horizon"] or row["failure"] is not None:
            raise ValueError("incomplete episode")
