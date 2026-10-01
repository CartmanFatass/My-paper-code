"""Qualified per-episode API dispatch; outer labels never become packet arms."""

from importlib import import_module
from pathlib import Path

from .config import ARMS
from .source import ROOT

PREFIXES = {
    "U32_FULL": "experiments.candidates.uav_radio_uncertainty.b01",
    "P_PRIOR": "experiments.candidates.uav_radio_information_cost.b01",
}


def module(program, component):
    name = PREFIXES[program] + "." + component
    result = import_module(name)
    if Path(result.__file__).resolve() != ROOT / (name.replace(".", "/") + ".py"):
        raise ValueError("inherited module origin differs")
    return result


def collect(env, world, program, horizon):
    raw, row, failure = module(program, "collect").collect_episode(
        env, world, ARMS[program], horizon=horizon)
    if row["arm"] != ARMS[program] or str(raw["arm"]) != ARMS[program]:
        raise ValueError("collector changed literal arm")
    # Extra outer metadata does not modify any original packet or decoder.
    import numpy as np
    raw["program"] = np.array(program)
    row["program"] = program
    return raw, row, failure


def outcomes(program, raw, records):
    return module(program, "metrics").outcomes(raw, records)


def verify_episode(program, raw, row, arrays, counts):
    if (row["program"] != program or str(raw["program"]) != program
            or row["arm"] != ARMS[program] or str(raw["arm"]) != ARMS[program]):
        raise ValueError("program/raw/row arm identity differs")
    return module(program, "reader").verify_episode(raw, row, arrays, counts)
