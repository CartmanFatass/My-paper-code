"""The sole eight-episode check, called only inside the selected invocation."""
import numpy as np
import torch

from .b02 import rollout, rule_actions, objective, write_json


def focused_check(model, out, deadline, activity):
    # 0 release/exclusion/tie; 1 reversed phase; 2 first service sample fails;
    # 3 last service sample fails; 4 t26 blocks phase-zero's final t32;
    # 5 forced-wait latch/reentry; 6/7 same world R yields / R0 submits at t8.
    draws = np.full((8, 40, 2), 0.99, dtype=np.float64)
    phase = np.array([0, 1, 0, 0, 0, 0, 0, 0])
    draws[2, 4, 0] = 0
    draws[3, 11, 0] = 0
    draws[5, [4, 5], 0] = 0
    draws[6:8, [0, 1], 0] = 0
    submit_times = np.array([[4, 14], [10, 0], [4, 14], [4, 14],
                             [-1, 26], [12, 2], [20, 10], [-1, 18]])
    checked_rules = {}

    def scripted(ids, t, own, x):
        action = submit_times[ids, own] == t
        if t == 4 and 0 in ids:
            row = x[ids == 0]
            assert row[0, 5] == row[0, 10] == 1
            assert row[0, 2] == row[0, 7]
            assert rule_actions(row, "R")[0]
            checked_rules["tie_submits"] = True
        if t == 8:
            for ep, rule in ((6, "R"), (7, "R0")):
                pos = np.flatnonzero(ids == ep)[0]
                row = x[pos:pos + 1]
                assert row[0, 5] == row[0, 10] == 1
                assert row[0, 7] > row[0, 2]
                assert not rule_actions(row, "R")[0]
                assert rule_actions(row, "R0")[0]
                action[pos] = rule_actions(row, rule)[0]
                checked_rules[rule] = bool(action[pos])
        return action

    batch = rollout(draws, phase, scripted=scripted, deadline=deadline,
                    activity=activity, trace=True)
    expected = np.array([[186, 176], [180, 190], [-14, 176], [-14, 176],
                         [-40, 164], [178, 188], [170, 180], [182, 172]])
    assert np.array_equal(batch["units"], expected)
    assert np.array_equal(batch["interval_units"].sum(axis=1), expected.sum(axis=1))
    for ep, t, prefix, value in zip(batch["episode_ids"], batch["times"],
                                    batch["prefixes"], batch["returns"]):
        assert prefix == batch["interval_units"][ep, :t].sum()
        assert np.isclose(value, batch["interval_units"][ep, t:].sum() / 400, atol=1e-7)
    by_time = {r["t"]: r for r in batch["trace"]}
    assert by_time[10]["blocked"][0] and by_time[12]["free_before"][0]
    assert by_time[10]["blocked"][2] and by_time[12]["free_before"][2]
    assert by_time[14]["eligible"][0]
    assert by_time[28]["blocked"][4] and by_time[32]["blocked"][4]
    assert batch["rows"][4]["blocked_final_clocks"] == 1
    assert by_time[8]["blocked"][5]
    assert by_time[8]["a_before"][5, 0] and by_time[8]["e_before"][5, 0]
    assert not by_time[8]["b_before"][5, 0]
    assert by_time[12]["b_before"][5, 0]
    for r in batch["trace"]:
        actual = batch["episode_ids"][batch["times"] == r["t"]]
        assert np.array_equal(actual, np.flatnonzero(r["eligible"]))
    assert sum(r["fixed_clocks"] for r in batch["rows"]) == 136
    loss, info = objective(model, batch, 1)
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    model.zero_grad(set_to_none=True)
    result = {"episodes": 8, "team_ticks": 320, "target_transitions": 640,
              "valid_rows": batch["decision_rows"], "gradient_rows": batch["decision_rows"],
              "backward_calls": 1, "optimizer_steps": 0, "rule_checks": checked_rules,
              "loss": info, "rows": batch["rows"]}
    write_json(out / "focused_check.json", result)
    return result
