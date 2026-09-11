from fractions import Fraction as F
from itertools import product
import json
import os
import sys

import pytest

from experiments.candidates.variable_n_fleet_churn_causal_headroom.e01 import (
    group_options, member_commands, policy_values, project_cost,
)
from experiments.candidates.variable_n_fleet_churn_causal_headroom.solver import (
    Option, Policy, solve_epochs, solve_separated_epoch,
)


def exhaustive(epoch, classes):
    keys = sorted(classes)
    return [Policy(epoch, tuple((key, option.command) for key, option in zip(keys, choices)),
                   tuple(sum((option.zone_totals[z] for option in choices), F(0)) for z in (0, 1)),
                   sum(not option.is_baseline for option in choices))
            for choices in product(*(classes[key] for key in keys))]


def test_separated_four_maps_global_epoch_and_all_ties():
    # Different from the formal fixture: tiny exact negative/sub-float advantages.
    panels, policies = [], []
    for epoch, gains in enumerate(((F(3, 11), F(1, 11)), (F(1, 11), F(3, 11)),
                                   (F(2, 11), F(2, 11)))):
        classes, zones = {}, {}
        for z, gain in enumerate(gains):
            def option(command, value, baseline=False):
                pair = [F(0), F(0)]
                pair[z] = value
                return Option((command, 255, 255, 255), tuple(pair), baseline)
            key = str(z)
            zones[key] = z
            classes[key] = [option(9, 0, True), option(2, gain), option(1, gain),
                            option(0, -F(1, 10**40))]
        panels.append(solve_separated_epoch(epoch, classes, zones))
        policies.extend(exhaustive(epoch, classes))
    actual = solve_epochs(reversed(panels))
    tail = lambda p: (p.deviations, p.epoch, p.action_map)
    assert actual.robust == min(policies, key=lambda p: (-p.robust, -p.aggregate, *tail(p)))
    assert actual.aggregate == min(policies, key=lambda p: (-p.aggregate, *tail(p)))
    assert actual.robust.epoch == 2
    for z in (0, 1):
        assert actual.zones[z] == min(policies, key=lambda p: (-p.zone_means[z], *tail(p)))
        other = dict(actual.zones[z].action_map)[str(1 - z)]
        assert other[0] == 9  # Other-zone tie selects BCRH despite its larger serialization.


def test_raw_endpoint_pairing_shared_history_complete_support_and_members():
    records = []
    for world, endpoint in (("one", (2, 7)), ("two", (3, 7))):
        for command, result in ((9, (1, 7)), (2, endpoint)):
            records.append(dict(epoch=0, world=world, zone=1,
                history={"public_failed_zone": 2, "observation": [3, 5]},
                baseline_command=(9, 255, 255, 255), command=(command, 255, 255, 255),
                baseline=(1, 7), endpoint=result))
    panels, groups = group_options(records)
    epoch, classes, zones = panels[0]
    assert len(classes) == 1
    options = next(iter(classes.values()))
    assert options[0].zone_totals == (F(0), F(3, 7))
    solution = solve_separated_epoch(epoch, classes, zones)
    assignments = member_commands(solution, groups)
    assert len(assignments) == 8
    assert all(row["command"][0] == 9 for row in assignments if row["map"] == "zone0")
    with pytest.raises(AssertionError, match="incomplete"):
        group_options(records[:-1])
    changed = [dict(row) for row in records]
    changed[-1]["zone"] = 0
    with pytest.raises(AssertionError, match="crossed zones"):
        group_options(changed)


def test_full_cost_law_uses_complete_batch_envelope_and_cpu_setup():
    # Rule numbers only, not observations or reported E01 timing.
    unit = dict(wall_seconds=2.0, cpu_seconds=3.0)
    batch = [dict(width=8, candidate=unit, input=unit, assembly=unit),
             dict(width=1, candidate=unit, input=unit, assembly=unit)]
    path = [dict(candidate=dict(reset=unit, stages=[dict(unit, ticks=20),
                                                    dict(unit, input_records=1)]))]
    selection = dict(candidate=unit, input=unit, endpoint_records=94128)
    publication = [dict(unit, bytes=100)] * 3
    result = project_cost(batch, path, selection, publication,
                          dict(full_call=100, history=100, maps=100),
                          dict(unit, startup_cpu_seconds=7), dict(unit, records=2))
    assert result["candidate_batches_upper"] == 47232
    assert result["other_singletons_upper"] == 176
    assert result["cpu_fixed_setup_seconds"] == 10
    assert result["terms"]["wall_seconds"]["record_group_construction"] == 94128
    assert result["terms"]["cpu_seconds"]["record_group_construction"] == 141192
    assert result["projected_cpu_work_seconds"] == 10 + 2 * sum(result["terms"]["cpu_seconds"].values())
    assert result["projected_wall_seconds"] == 60 + 2 * sum(result["terms"]["wall_seconds"].values())
    assert result["status"] == "BLOCKED_WALL_CAP"
    assert result["full_census_cpu_budget"] is None


@pytest.mark.skipif(sys.platform != "linux" or os.environ.get("HMASD_E01_NATIVE_SMOKE") != "1",
                    reason="one committed-source native smoke is dispatched separately")
def test_native_nonformal_runner_and_publication(tmp_path):
    from scripts.run_vnfc_causal_headroom import main
    assert main(["--mode", "e01-smoke", "--launch-sha", "nonformal-smoke",
                 "--out", str(tmp_path)]) == 0
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["result"]["widths"] == list(range(1, 9))
    assert summary["result"]["every_weight_field_checked"]
    assert summary["native_target_worlds"] == summary["new_rng_draws"] == 0
