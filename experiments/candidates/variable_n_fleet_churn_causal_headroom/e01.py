"""Complete deterministic E01 assessment; no panel, RNG or target endpoints."""

import ctypes as ct
from dataclasses import asdict
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter

from ..variable_n_fleet_churn_bpcr_r09.contracts import FIXTURE_MAGIC, NATIVE_ABI_VERSION
from ..variable_n_fleet_churn_bpcr_r09.native_backend import (
    _BCRHInput, _BCRHOutput, _EpisodeInput, _GeneralAgentInput, _InteractiveOutput,
)
from .solver import Option, solve_epoch, solve_epochs, solve_separated_epoch
from .calibration import CALLS, CONTINUATIONS, SCORED_ROWS, TICKS

FIXTURE = Path(__file__).with_name("e01_fixture.json")
WEIGHT_FIELDS = ("epoch", "failed_zone", "demand_1", "demand_2", "blocked_1",
                 "blocked_2", "accrued_total_demand", "accrued_fail_demand")


def stamp():
    import resource
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return perf_counter(), own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def elapsed(start):
    now = stamp()
    return dict(wall_seconds=now[0] - start[0], cpu_seconds=now[1] - start[1])


def values(value):
    """Decode named ABI fields, including every limb and unused record slot.

    Padding is not an output field and is deliberately not compared.
    """
    if isinstance(value, ct.Structure):
        return {name: values(getattr(value, name)) for name, _ in value._fields_}
    if isinstance(value, ct.Array):
        return [values(item) for item in value]
    return value


def weight_key(record):
    return tuple(getattr(record, name) for name in WEIGHT_FIELDS)


def direct_inputs(spec, epoch, energies, demand):
    result = (_BCRHInput * len(energies))()
    for output, energy in zip(result, energies):
        output.magic, output.abi = FIXTURE_MAGIC, NATIVE_ABI_VERSION
        output.epoch, output.failed_zone = epoch, spec["failed_zone"]
        output.active_count = len(spec["agents"])
        for index, agent in enumerate(spec["agents"]):
            output.agents[index] = _GeneralAgentInput(*agent[:-1], energy)
        output.clearance[:] = spec["clearance"]
        for name in ("accrued_fail_delivered", "accrued_fail_demand",
                     "accrued_total_delivered", "accrued_total_demand",
                     "demand_2", "blocked_1", "blocked_2"):
            setattr(output, name, spec[name])
        output.demand_1 = demand
    return result


def episode_input(fixture):
    spec = fixture["trajectory"]
    result = _EpisodeInput()
    result.magic, result.abi = FIXTURE_MAGIC, NATIVE_ABI_VERSION
    result.failed_zone, result.active_count = spec["failed_zone"], 8
    for index, agent in enumerate(fixture["direct"]["agents"] + [spec["eighth_agent"]]):
        result.agents[index] = _GeneralAgentInput(*agent)
    for name in ("demand_1", "demand_2", "blocked_1", "blocked_2"):
        getattr(result, name)[:] = spec[name]
    result.post_presentation[:] = spec["presentation"] * 6
    return result


def build_and_load(out):
    # Always compile in this invocation, single compiler command and no job pool.
    binary = out / "e01.so"
    source = Path(__file__).with_name("native") / "e01.cpp"
    include = source.parents[2] / "variable_n_fleet_churn_headroom/native"
    subprocess.run([os.environ.get("CXX", "c++"), "-std=c++20", "-O2",
                    "-fPIC", "-shared", "-pthread", "-fno-fast-math",
                    "-ffp-contract=off", f"-I{include}", str(source), "-o", str(binary)], check=True)
    library = ct.CDLL(str(binary))
    signatures = {
        "vnfc_e01_batch": [ct.POINTER(_BCRHInput), ct.c_int, ct.POINTER(_BCRHOutput), ct.POINTER(ct.c_int)],
        "vnfc_bpcr_r09_run_bcrh_batch": [ct.POINTER(_BCRHInput), ct.c_int, ct.POINTER(_BCRHOutput)],
        "vnfc_bpcr_r09_interactive_reset_batch": [ct.POINTER(_EpisodeInput), ct.c_int, ct.POINTER(ct.c_void_p), ct.POINTER(_InteractiveOutput)],
        "vnfc_bpcr_r09_interactive_step_batch": [ct.POINTER(ct.c_void_p), ct.POINTER(ct.c_int32), ct.c_int, ct.POINTER(_InteractiveOutput)],
        "vnfc_bpcr_r09_interactive_close_batch": [ct.POINTER(ct.c_void_p), ct.c_int],
        "vnfc_e01_session_input": [ct.c_void_p, ct.POINTER(_BCRHInput), ct.POINTER(ct.c_int64)],
    }
    for name, arguments in signatures.items():
        function = getattr(library, name)
        function.argtypes = arguments
        function.restype = None if name == "vnfc_e01_session_input" else ct.c_int
    return library


def checked_call(function, *arguments):
    status = function(*arguments)
    if status:
        raise RuntimeError(f"{function.__name__}: status {status}")


def full_batch(library, inputs, candidate, expected=None):
    start = stamp()
    outputs = (_BCRHOutput * len(inputs))()
    unique = ct.c_int()
    if candidate:
        status = library.vnfc_e01_batch(inputs, len(inputs), outputs, ct.byref(unique))
        if status:
            raise RuntimeError(f"E01 logical batch status {status}; item statuses "
                               f"{[row.status for row in outputs]}")
    else:
        checked_call(library.vnfc_bpcr_r09_run_bcrh_batch, inputs, len(inputs), outputs)
    decoded = values(outputs)
    for row in decoded:
        if not (row["scorer_checker_equal"] and row["independent_enumerator_equal"]
                and all(record["exact_match"] for record in row["records"][:row["candidate_count"]])):
            raise AssertionError("complete independent BCRH record agreement")
    if expected is not None and decoded != expected:
        raise AssertionError("serial/candidate complete BCRH output mismatch")
    timing = elapsed(start)
    timing.update(items=len(inputs), rows=sum(row["candidate_count"] for row in decoded),
                  unique_weights=unique.value if candidate else len(inputs),
                  reference_equal=expected is not None)
    return decoded, timing


def public_input(record):
    return {key: value for key, value in values(record).items() if key not in ("magic", "abi")}


def trajectory(library, fixture, path, candidate, reference=None):
    input_record = episode_input(fixture)
    handle, snapshot = ct.c_void_p(), _InteractiveOutput()
    start = stamp()
    checked_call(library.vnfc_bpcr_r09_interactive_reset_batch,
                 ct.byref(input_record), 1, ct.byref(handle), ct.byref(snapshot))
    reset = values(snapshot)
    reset_cost = elapsed(start)
    rows, costs, history, commands = [], [], [], []
    try:
        for epoch in range(6):
            start = stamp()
            current, totals = _BCRHInput(), (ct.c_int64 * 5)()
            library.vnfc_e01_session_input(handle, ct.byref(current), totals)
            history.append({"observation": values(snapshot.next_observation),
                            "bcrh_input": public_input(current)})
            costs.append(dict(elapsed(start), input_records=1))
            expected = None if reference is None else [reference["epochs"][epoch]["bcrh"]]
            facts, cost = full_batch(library, (_BCRHInput * 1)(current), candidate, expected)
            facts = facts[0]
            costs.append(cost)
            command = facts["scorer_command"]
            if epoch == path["deviation_epoch"]:
                command = facts["records"][path["canonical_legal_index"]]["command"]
            start = stamp()
            admitted = {"prehistory_commands": reset["prehistory_commands"],
                        "public_history": list(history), "prior_commands": list(commands)}
            history_key = json.dumps(admitted, sort_keys=True, separators=(",", ":"))
            # This is the same record construction for every continuation, with
            # admitted prefix separated from later public trajectory evidence.
            commands.append(command)
            checked_call(library.vnfc_bpcr_r09_interactive_step_batch,
                         ct.byref(handle), (ct.c_int32 * 4)(*command), 1, ct.byref(snapshot))
            next_state = _BCRHInput()
            library.vnfc_e01_session_input(handle, ct.byref(next_state), totals)
            row = dict(epoch=epoch, admitted_history=admitted, history_key=history_key, bcrh=facts,
                       command=command, after=values(snapshot),
                       physical_state=public_input(next_state), zone_accounting=values(totals))
            if reference is not None and row != reference["epochs"][epoch]:
                raise AssertionError("complete serial/candidate trajectory mismatch")
            rows.append(row)
            costs.append(dict(elapsed(start), ticks=20, history_records=1))
        if not (snapshot.terminal and snapshot.epoch == 6 and
                snapshot.integrated_ticks == 240 and not snapshot.safety_violation and
                not snapshot.exclusivity_violation):
            raise AssertionError("full 120-second post-loss terminal")
        if reference is not None and reset != reference["reset"]:
            raise AssertionError("serial/candidate prehistory mismatch")
        return dict(name=path["name"], reset=reset, epochs=rows), dict(reset=reset_cost, stages=costs)
    finally:
        checked_call(library.vnfc_bpcr_r09_interactive_close_batch, ct.byref(handle), 1)


def selection_records(spec):
    """Fixed synthetic endpoint pairs, with membership outside public history."""
    for epoch in spec["epochs"]:
        for index in range(spec["class_count"]):
            zone = index % 2
            baseline_command = (spec["baseline_index"], *spec["command_suffix"])
            for action in range(spec["action_count"]):
                baseline = action == spec["baseline_index"]
                numerator = 0 if baseline else (action % 5) * spec["epoch_zone_multipliers"][epoch][zone]
                yield dict(epoch=epoch, world=index, zone=zone,
                           history={"public_failed_zone": zone + 1, "epoch": epoch,
                                    "synthetic_public_observation": index},
                           baseline_command=baseline_command, baseline=(0, 1),
                           command=(action, *spec["command_suffix"]),
                           endpoint=(numerator, spec["denominator"]))


def group_options(records):
    """Exact endpoint pairing, complete per-member support and causal grouping."""
    groups = {}
    for row in records:
        key = json.dumps(row["history"], sort_keys=True, separators=(",", ":"))
        group = groups.setdefault((row["epoch"], key), dict(
            zone=row["zone"], baseline=tuple(row["baseline_command"]), worlds={}))
        if group["zone"] != row["zone"] or group["baseline"] != tuple(row["baseline_command"]):
            raise AssertionError("public-history class crossed zones or BCRH commands")
        world = group["worlds"].setdefault(row["world"], {})
        command = tuple(row["command"])
        if command in world:
            raise AssertionError("duplicate world/epoch/command continuation")
        world[command] = Fraction(*row["endpoint"]) - Fraction(*row["baseline"])
    panels = {}
    for (epoch, key), group in sorted(groups.items()):
        worlds = list(group["worlds"].values())
        support = set(worlds[0])
        if group["baseline"] not in support or any(set(world) != support for world in worlds):
            raise AssertionError("incomplete identical-history legal support")
        if any(world[group["baseline"]] for world in worlds):
            raise AssertionError("BCRH paired advantage is not zero")
        classes, zones = panels.setdefault(epoch, ({}, {}))
        zones[key] = group["zone"]
        options = []
        for command in sorted(support):
            totals = [Fraction(0), Fraction(0)]
            totals[group["zone"]] = sum((world[command] for world in worlds), Fraction(0))
            options.append(Option(command, tuple(totals), command == group["baseline"]))
        classes[key] = options
    return [(epoch, *panel) for epoch, panel in sorted(panels.items())], groups


def member_commands(solution, groups):
    assignments = []
    for name, policy in (("robust", solution.robust), ("aggregate", solution.aggregate),
                         ("zone0", solution.zones[0]), ("zone1", solution.zones[1])):
        for key, command in policy.action_map:
            for member, support in groups[(policy.epoch, key)]["worlds"].items():
                if command not in support:
                    raise AssertionError("selected command absent from a class member")
                assignments.append(dict(map=name, epoch=policy.epoch, history=key,
                                        member=member, command=command))
    return assignments


def policy_values(solution):
    def policy(item):
        result = asdict(item)
        result["zone_totals"] = [str(value) for value in item.zone_totals]
        return result
    return dict(robust=policy(solution.robust), aggregate=policy(solution.aggregate),
                zones=[policy(item) for item in solution.zones])


def assess_selection(spec):
    start = stamp()
    records = list(selection_records(spec))
    panels, groups = group_options(records)
    input_cost = elapsed(start)
    start = stamp()
    references = solve_epochs(solve_epoch(epoch, classes) for epoch, classes, _ in panels)
    reference_cost = elapsed(start)
    start = stamp()
    selected = solve_epochs(solve_separated_epoch(epoch, classes, zones)
                            for epoch, classes, zones in panels)
    maps = policy_values(selected)
    assignments = member_commands(selected, groups)
    if maps != policy_values(references):
        raise AssertionError("four exact maps/global epoch mismatch")
    candidate_cost = elapsed(start)
    classes, zones = {}, {}
    for row in spec["tie_case"]:
        zones[row["key"]] = row["zone"]
        classes[row["key"]] = [Option((command, 255, 255, 255),
            (Fraction(value), Fraction(0)) if row["zone"] == 0 else (Fraction(0), Fraction(value)),
            baseline) for command, value, baseline in row["options"]]
    expected = solve_epochs(solve_epoch(epoch, classes) for epoch in (0, 2))
    actual = solve_epochs(solve_separated_epoch(epoch, classes, zones) for epoch in (2, 0))
    if policy_values(actual) != policy_values(expected):
        raise AssertionError("canonical, deviation, epoch or other-zone tie mismatch")
    return dict(scale_maps=maps, member_commands=assignments, tie_maps=policy_values(actual)), dict(
        input=input_cost, reference=reference_cost, candidate=candidate_cost,
        classes=selected.stats.class_count, action_records=selected.stats.action_records,
        endpoint_records=len(records))


def trajectory_options(trajectories):
    """Exercise the same pairing/group path on the two non-target native paths."""
    baseline, deviation = trajectories
    original = baseline["epochs"][1]
    original_end = baseline["epochs"][-1]["after"]
    rows = []
    for path in (baseline, deviation):
        row, end = path["epochs"][1], path["epochs"][-1]["after"]
        if row["admitted_history"] != original["admitted_history"]:
            raise AssertionError("one-deviation prefix changed before its fixed epoch")
        if any(previous["command"] == row["command"] for previous in rows):
            continue
        rows.append(dict(epoch=1, world="non-target", zone=0,
                         history=row["admitted_history"], baseline_command=original["command"],
                         command=row["command"],
                         baseline=(original_end["fail_delivered"], original_end["fail_demand"]),
                         endpoint=(end["fail_delivered"], end["fail_demand"])))
    panels, groups = group_options(rows)
    epoch, classes, zones = panels[0]
    # This is only the prospectively fixed pair, not a native optimal map.
    return dict(endpoint_pairs=rows, classes=len(classes), legal_pair_size=len(rows),
                paired_advantages={key: [str(o.zone_totals[0]) for o in options]
                                   for key, options in classes.items()})


def publish(path, data):
    start = stamp()
    encoded = json.dumps(data, separators=(",", ":"), sort_keys=True) + "\n"
    path.write_text(encoded, encoding="utf-8")
    if json.loads(path.read_text(encoding="utf-8")) != json.loads(encoded):
        raise AssertionError(f"publication readback: {path.name}")
    return dict(elapsed(start), bytes=path.stat().st_size)


def project_cost(batches, paths, selection, publication, record_sizes, setup, pairing):
    """Empirical full8 envelope, not measured widths2..7 or a runtime theorem.

    A natural tail has at most eight items, at most two calls per lane, and
    the same tuple within a world/deviation/post-epoch group. Full calls retain
    complete checks. Measured construction/verification are inside batch costs.
    """
    groups = 16 * (5 + 4 + 3)
    batch_upper = groups * ((1961 + 7) // 8)
    singleton_upper = 176
    tick_stages = [stage for path in paths for stage in path["candidate"]["stages"] if "ticks" in stage]
    resets = [path["candidate"]["reset"] for path in paths]
    input_stages = [stage for path in paths for stage in path["candidate"]["stages"]
                    if "input_records" in stage]
    sizes = record_sizes
    bytes_upper = CALLS * sizes["full_call"] + CONTINUATIONS * sizes["history"] + sizes["maps"]
    terms = {}
    for clock in ("wall_seconds", "cpu_seconds"):
        batch_unit = max(row["candidate"][clock] for row in batches)
        tail_unit = max(row["candidate"][clock] for row in batches if row["width"] == 1)
        terms[clock] = {
            "complete_bcrh_batches": batch_upper * batch_unit + singleton_upper * tail_unit,
            "batch_assembly": (batch_upper + singleton_upper) * max(row["assembly"][clock] for row in batches),
            "ticks_and_history_construction": TICKS * max(row[clock] / row["ticks"] for row in tick_stages),
            "prehistory": 96 * max(row[clock] / 6 for row in resets),
            "public_input_construction": CALLS * max(
                [row[clock] for row in input_stages] +
                [row["input"][clock] / row["width"] for row in batches]),
            "record_group_construction": CONTINUATIONS * max(
                selection["input"][clock] / selection["endpoint_records"],
                pairing[clock] / pairing["records"]),
            "selection": selection["candidate"][clock],
            "publication_and_readback": (
                CALLS * sizes["full_call"] * publication[0][clock] / publication[0]["bytes"] +
                CONTINUATIONS * sizes["history"] * publication[1][clock] / publication[1]["bytes"] +
                publication[2][clock]),
        }
    wall = 60 + 2 * sum(terms["wall_seconds"].values())
    cpu = setup["cpu_seconds"] + setup["startup_cpu_seconds"] + 2 * sum(terms["cpu_seconds"].values())
    return dict(native_ticks_upper=TICKS, full_calls_upper=CALLS,
                scored_rows_upper=SCORED_ROWS, continuations_upper=CONTINUATIONS,
                candidate_groups_upper=groups, candidate_batches_upper=batch_upper,
                other_singletons_upper=singleton_upper, publication_bytes_upper=bytes_upper,
                terms=terms, projected_wall_seconds=wall, projected_cpu_work_seconds=cpu,
                cpu_fixed_setup_seconds=setup["cpu_seconds"] + setup["startup_cpu_seconds"],
                full_census_cpu_budget=None,
                factor=2, fixed_wall_allowance=60, cap_seconds=2700,
                tail_basis="unmeasured widths2..7 use empirical full8 envelope; no tail timing claim",
                weight_basis="batch-lifetime scorer reuse only; construction included; checker independent",
                status="BELOW_WALL_CAP" if wall < 2700 else "BLOCKED_WALL_CAP")


def assess(out):
    start = stamp()
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    library = build_and_load(out)
    setup = elapsed(start)
    setup["startup_cpu_seconds"] = start[1]
    batches, records = [], []
    spec = fixture["direct"]
    for epoch in spec["epochs"]:
        for energies, demand in ((spec["full_batch_energies"], spec["demand_1"]),
                                 (spec["tail_energies"], spec["tail_demand_1"])):
            start_input = stamp()
            inputs = direct_inputs(spec, epoch, energies, demand)
            input_cost = elapsed(start_input)
            reference, reference_cost = full_batch(library, inputs, False)
            candidate, candidate_cost = full_batch(library, inputs, True, reference)
            if len(inputs) == 8 and candidate_cost["unique_weights"] != 1:
                raise AssertionError("immutable same-tuple reuse did not occur")
            start_assembly = stamp()
            batches.append(dict(epoch=epoch, width=len(inputs), reference=reference_cost,
                                candidate=candidate_cost, input=input_cost))
            records.append(dict(inputs=values(inputs), outputs=candidate, reference_equal=True))
            batches[-1]["assembly"] = elapsed(start_assembly)
    trajectories, paths = [], []
    for path in fixture["trajectory"]["paths"]:
        reference, reference_cost = trajectory(library, fixture, path, False)
        candidate, candidate_cost = trajectory(library, fixture, path, True, reference)
        trajectories.append(candidate)
        paths.append(dict(name=path["name"], reference=reference_cost, candidate=candidate_cost))
    maps, selection = assess_selection(fixture["selection"])
    pairing_start = stamp()
    pairing = trajectory_options(trajectories)
    pairing_cost = elapsed(pairing_start)
    pairing_cost["records"] = len(pairing["endpoint_pairs"])
    maps["non_target_pairing"] = pairing
    publication = [publish(out / "records.json", records),
                   publish(out / "trajectories.json", trajectories),
                   publish(out / "maps.json", maps)]
    full_call_bytes = max(len(json.dumps(dict(input=record, output=row, reference_equal=True),
                                        separators=(",", ":")))
                          for batch in records for record, row in zip(batch["inputs"], batch["outputs"]))
    history_bytes = max(len(json.dumps(
        {**path, "epochs": [{key: value for key, value in row.items() if key != "bcrh"}
                            for row in path["epochs"]]}, separators=(",", ":")))
                        for path in trajectories)
    sizes = dict(full_call=full_call_bytes, history=history_bytes, maps=publication[-1]["bytes"])
    through_readback = elapsed(start)
    covered = [setup, selection["input"], selection["reference"], selection["candidate"], pairing_cost]
    covered += publication
    covered += [row[name] for row in batches for name in ("input", "reference", "candidate", "assembly")]
    covered += [path[version]["reset"] for path in paths for version in ("reference", "candidate")]
    covered += [stage for path in paths for version in ("reference", "candidate")
                for stage in path[version]["stages"]]
    fixed_other = {clock: through_readback[clock] - sum(row[clock] for row in covered)
                   for clock in ("wall_seconds", "cpu_seconds")}
    # Remaining finite work includes record-size encoding, session close, ties
    # and Python assembly between stages. Keep it visible under the fixed60s
    # allowance, whose adequacy additionally requires the external full60s pass.
    projection_setup = dict(setup)
    projection_setup["cpu_seconds"] += fixed_other["cpu_seconds"]
    projection = project_cost(batches, paths, selection, publication, sizes, projection_setup, pairing_cost)
    return dict(setup=setup, batches=batches, trajectories=paths, selection=selection,
                non_target_pairing=pairing_cost,
                fixed_other_work=fixed_other,
                publication=publication, record_sizes=sizes, projection=projection,
                coverage=dict(direct_calls=54, trajectory_calls=24, prehistory_decisions=24,
                              postloss_ticks=480, full_records_equal=True, four_maps_equal=True,
                              distinct_native_deviation=len(pairing["endpoint_pairs"]) == 2,
                              native_target_worlds=0, rng_draws=0),
                assessment_through_record_readback=through_readback)


def assess_smoke(out):
    """Separate small interface/rule fixture; never opens the formal fixture."""
    library = build_and_load(out)
    spec = dict(failed_zone=2, agents=[[1, 1, 0, 1, 0, -1, -1, 0, 0, -1, 0, 0, 800]],
                clearance=[0, 0, 0, 0], accrued_fail_delivered=0, accrued_fail_demand=120,
                accrued_total_delivered=0, accrued_total_demand=200,
                demand_1=1, demand_2=1, blocked_1=0, blocked_2=0)
    results = []
    for width in range(1, 9):
        inputs = direct_inputs(spec, 5, [800] * width, 1)
        if width > 1:
            inputs[-1].demand_1 = 2
        reference, _ = full_batch(library, inputs, False)
        candidate, facts = full_batch(library, inputs, True, reference)
        assert facts["unique_weights"] == min(width, 2)
        results.append(dict(width=width, outputs=candidate))
    for name in WEIGHT_FIELDS:
        inputs = direct_inputs(spec, 5, [800, 800], 1)
        old = getattr(inputs[1], name)
        setattr(inputs[1], name, old - 1 if name in ("epoch", "failed_zone") else old + 1)
        reference, _ = full_batch(library, inputs, False)
        _, facts = full_batch(library, inputs, True, reference)
        assert facts["unique_weights"] == 2
    # Two valid weight inputs with invalid roster counts fail in logical order.
    inputs = direct_inputs(spec, 5, [800] * 4, 1)
    inputs[1].active_count = inputs[3].active_count = 0
    outputs, unique = (_BCRHOutput * 4)(), ct.c_int()
    assert library.vnfc_e01_batch(inputs, 4, outputs, ct.byref(unique)) == 1001
    assert [item.status for item in outputs] == [0, 1, 0, 1]
    publication = publish(out / "records.json", results)
    return dict(nonformal_smoke=True, widths=list(range(1, 9)),
                every_weight_field_checked=True, deterministic_errors=True, publication=publication)
