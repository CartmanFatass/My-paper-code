"""E/B public-law resource assignment inside the unchanged single C act.

Columns are original solver labels, never coordinate-inferred identities. The
law bundle is lazy and survives reset; no tracker, RF or private model is used.
Saved-prefix replay reconstructs completed effects only, preserving the omitted
failed attempt in its original record and reporting the reader work separately.
"""
from __future__ import annotations
from copy import deepcopy
from itertools import permutations
import math
import numpy as np
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import controller as b10
from experiments.candidates.uav_joint_transition.motion import legal_start
from .energy import PublicLaw, flight_edge, target_return, permutation_criterion
from .trace import CANDIDATE_DTYPE, EDGE_DTYPE, RETURN_DTYPE, blank

TOTALS = b10.TOTALS
ReplayBoundary = b10.ReplayBoundary


def padded(value, shape, *, dtype=np.float64, fill=np.nan):
    result = np.full(shape, fill, dtype=dtype)
    array = np.asarray(value, dtype=dtype)
    result[tuple(slice(0, length) for length in array.shape)] = array
    return result


def select_records(policy, records, base_columns, *, counters=None):
    """Rank saved complete criteria, with full-vector B then E/base/columns."""
    if policy not in ("E", "B") or len(records) == 0:
        raise ValueError("selection requires E/B and nonempty complete candidates")
    m = int(records[0]["m"])
    base = tuple(int(x) for x in np.asarray(base_columns)[:m])
    if not 2 <= m <= 6 or len(set(base)) != m:
        raise ValueError("invalid base service columns")
    best, best_slacks, best_key, base_index = None, None, None, None
    for index, row in enumerate(records):
        if counters is not None:
            b10.bump(counters, "ranking_rows")
        columns = tuple(int(x) for x in row["columns"][:m])
        slacks = tuple(float(x) for x in row["slacks"][:m])
        energy = float(row["energy"])
        if (not row["completed"] or int(row["m"]) != m or sorted(columns) != sorted(base)
                or not math.isfinite(energy) or not all(math.isfinite(x) for x in slacks)
                or slacks != tuple(sorted(slacks))):
            raise ValueError("invalid recorded complete criterion")
        is_base = columns == base
        if is_base:
            if base_index is not None:
                raise ValueError("duplicate base permutation")
            base_index = index
        key = (energy, not is_base, columns)
        if (best is None or (policy == "B" and slacks > best_slacks)
                or ((policy == "E" or slacks == best_slacks) and key < best_key)):
            best, best_slacks, best_key = index, slacks, key
    if base_index is None:
        raise ValueError("base absent from permutation table")
    return int(best), int(base_index)


class ResourceController(b10.AssignmentController):
    def __init__(self, policy):
        if policy not in ("E", "B"):
            raise ValueError("resource policy must be E or B")
        self.policy_arm = policy
        self._cold_counts = b10.CostDict(law_constructions=0,
            constant_power_evaluations=0, constant_power_evaluations_completed=0)
        self.law = None
        super().__init__("C")

    def reset(self):
        super().reset()
        self.edges, self.returns = [], []
        self.replay_edge_prefix = None
        self.replay_return_prefix = None

    @property
    def cold_costs(self):
        return dict(self._cold_counts)

    @property
    def counters(self):
        return dict(self._counts) | self.cold_costs

    @property
    def last_decision(self):
        result = deepcopy(self._last_decision)
        if result is not None:
            for value in result.values():
                if isinstance(value, np.ndarray):
                    value.setflags(write=False)
        return result

    @last_decision.setter
    def last_decision(self, value):
        self._last_decision = value

    def _law(self):
        if self.law is None:
            self.law = PublicLaw(self._cold_counts)
        return self.law

    def audit_arrays(self):
        return dict(candidate_records=np.asarray(self.candidates, dtype=CANDIDATE_DTYPE),
            edge_records=np.asarray(self.edges, dtype=EDGE_DTYPE),
            return_records=np.asarray(self.returns, dtype=RETURN_DTYPE))

    def set_replay_prefix(self, raw):
        """Attach all three same-source audit vectors; never mutate saved arrays."""
        fields = (("candidate_records", CANDIDATE_DTYPE, "replay_prefix"),
                  ("edge_records", EDGE_DTYPE, "replay_edge_prefix"),
                  ("return_records", RETURN_DTYPE, "replay_return_prefix"))
        arrays = []
        for name, dtype, attribute in fields:
            value = np.asarray(raw[name])
            if value.ndim != 1 or value.dtype != dtype:
                raise ValueError("invalid replay schema: " + name)
            arrays.append((attribute, value))
        for attribute, value in arrays:
            setattr(self, attribute, value)

    def _perform(self, kind, dtype, inputs, effect, outputs):
        rows = {"candidate": self.candidates, "edge": self.edges, "return": self.returns}[kind]
        prefix = {"candidate": self.replay_prefix, "edge": self.replay_edge_prefix,
                  "return": self.replay_return_prefix}[kind]
        saved = None
        if prefix is not None:
            if prefix.dtype != dtype or prefix.ndim != 1:
                raise ValueError("invalid " + kind + " prefix schema")
            if len(rows) >= len(prefix):
                raise ReplayBoundary("recorded " + kind + " prefix exhausted")
            saved = prefix[len(rows)]
            if saved["completed"] and not saved["started"]:
                raise ValueError("completed unstarted " + kind)
            if kind == "candidate" and saved["selected"] and not saved["completed"]:
                raise ValueError("selected incomplete candidate")
            if saved["completed"]:
                for name in outputs:
                    value = saved[name][:int(saved["m"])] if name == "slacks" else saved[name]
                    if value.dtype.kind == "f" and not np.isfinite(value).all():
                        raise ValueError("non-finite saved " + kind + "/" + name)
        row = blank(dtype, **inputs)
        if saved is not None:
            for name in inputs:
                b10.equal(row[name], saved[name], kind + "/input/" + name)
        rows.append(row)
        decision = self._last_decision
        first = decision[kind + "_first"]
        decision[kind + "_count"] = len(rows) - first
        if saved is not None and not saved["completed"]:
            # Reconstructing the prepared input is not repeating a failed effect.
            raise ReplayBoundary("recorded incomplete " + kind + " effect")
        row["started"] = True
        result = effect()
        for name, value in zip(outputs, result):
            row[name] = value
        row["completed"] = True
        if saved is not None:
            for name in outputs:
                b10.equal(row[name], saved[name], kind + "/result/" + name)
        return row

    def _on_plan(self, observations, modes, plan):
        step = int(self.heuristic.calls)
        ordinary = self.heuristic.targets_xy.copy()
        roles = self.heuristic.assignment_role.copy()
        calls = self.heuristic.assignment_call.copy()
        assigned = self.heuristic.assignment_column.copy()
        eligible = ~modes & (roles == b10.ROLE_SERVICE) & np.isfinite(ordinary).all(axis=1)
        members = np.flatnonzero(eligible)
        m = len(members)
        if m > 6:
            raise ValueError("more than six C service members")
        base = assigned[members]
        columns = np.sort(base)
        if (len(np.unique(columns)) != m or np.any(columns < 0) or
                np.any(calls[members] != b10.CALL_PRIMARY)):
            raise ValueError("inconsistent actual service columns")
        order = np.argsort(base, kind="stable")
        target_xy = ordinary[members[order]].copy()
        if m and (np.any(columns >= len(plan["priority"])) or
                any(plan["kinds"][int(col)] != "service" for col in columns) or
                not np.array_equal(target_xy, plan["priority"][columns])):
            raise ValueError("solver service columns differ from actual C destinations")
        self._last_trace["plan_supplied_xy"] = plan["users"].copy()
        self._last_decision = dict(step=step, m=m, fallback=int(m < 2),
            candidate_first=len(self.candidates), candidate_count=0, selected=-1, base_index=-1,
            edge_first=len(self.edges), edge_count=0, return_first=len(self.returns), return_count=0,
            ordinary_targets=ordinary.copy(), plan_ordinary_targets=ordinary.copy(),
            assignment_role=roles, assignment_call=calls, assignment_column=assigned,
            eligible=eligible.copy(), eligible_uavs=padded(members, (6,), dtype=np.int8, fill=-1),
            target_columns=padded(columns, (6,), dtype=np.int8, fill=-1),
            base_columns=padded(base, (6,), dtype=np.int8, fill=-1),
            selected_columns=padded(base, (6,), dtype=np.int8, fill=-1),
            target_xy=padded(target_xy, (6, 2)), selected_targets=ordinary.copy(),
            edge_fly_wh=np.full((6, 6), np.nan), edge_slack=np.full((6, 6), np.nan),
            edge_arrival_ticks=np.full((6, 6), -1, dtype=np.int32), return_wh=np.full(6, np.nan),
            return_station=np.full(6, -1, dtype=np.int8), legal_xyz=np.full((8, 3), np.nan),
            legal_battery=np.full(8, np.nan), legal_stations=np.full((2, 3), np.nan),
            selected_alias=False, label_changed=False, criterion_changed=False,
            future_xy=np.empty((3, 0, 2)), current_velocities=np.empty((0, 2)),
            selected_pair=np.full(2, -1, dtype=np.int8))
        d = self._last_decision
        if m < 2:
            b10.bump(self._counts, "sparse_plans")
            return
        attached = (self.replay_prefix is not None, self.replay_edge_prefix is not None,
                    self.replay_return_prefix is not None)
        if any(attached) and not all(attached):
            raise ValueError("replay requires candidate, edge and return prefixes together")
        start = legal_start(observations)
        if not np.isfinite(start["xyz"]).all() or not np.isfinite(start["battery"]).all():
            raise ValueError("non-finite lawful resource start")
        d.update(legal_xyz=start["xyz"].copy(), legal_battery=start["battery"].copy(),
                 legal_stations=start["stations"].copy())
        targets = np.column_stack((target_xy, np.full(m, 100.0)))
        for col in range(m):
            row = self._perform("return", RETURN_DTYPE,
                dict(step=step, index=col, m=m, column=int(columns[col])),
                lambda col=col: target_return(targets[col], start["stations"], self._law(), counters=self._counts),
                ("station", "return_wh"))
            d["return_wh"][col], d["return_station"][col] = row["return_wh"], row["station"]
        for row_index, member in enumerate(members):
            for col in range(m):
                row = self._perform("edge", EDGE_DTYPE,
                    dict(step=step, index=row_index*m+col, m=m, row=row_index,
                         column=col, uav=int(member), target_column=int(columns[col])),
                    lambda member=member, col=col: flight_edge(start["xyz"][member], targets[col],
                        start["battery"][member], d["return_wh"][col], self._law(), counters=self._counts),
                    ("arrival_ticks", "fly_wh", "slack"))
                d["edge_arrival_ticks"][row_index, col] = row["arrival_ticks"]
                d["edge_fly_wh"][row_index, col], d["edge_slack"][row_index, col] = row["fly_wh"], row["slack"]
        local = {int(column): index for index, column in enumerate(columns)}
        for index, permutation in enumerate(permutations(columns.tolist())):
            self._perform("candidate", CANDIDATE_DTYPE,
                dict(step=step, index=index, m=m,
                     columns=padded(permutation, (6,), dtype=np.int8, fill=-1)),
                lambda permutation=permutation: self._criterion(d, m, tuple(local[int(col)] for col in permutation)),
                ("energy", "slacks"))
        first = d["candidate_first"]
        records = np.asarray(self.candidates[first:], dtype=CANDIDATE_DTYPE)
        if self.replay_prefix is not None:
            saved = self.replay_prefix[first:len(self.candidates)]
            if not saved["selected"].any():
                raise ReplayBoundary("recorded criteria end before actual selection")
        selected, base_index = select_records(self.policy_arm, records, base, counters=self._counts)
        self.candidates[first + selected]["selected"] = True
        if self.replay_prefix is not None:
            b10.equal(np.asarray(self.candidates[first:], dtype=CANDIDATE_DTYPE)["selected"],
                      saved["selected"], "candidate/actual-selection")
        winner = records[selected]
        committed = ordinary.copy()
        selected_columns = winner["columns"][:m]
        committed[members] = target_xy[[local[int(col)] for col in selected_columns]]
        changed = not np.array_equal(selected_columns, base)
        d.update(selected=selected, base_index=base_index,
            selected_columns=winner["columns"].copy(), selected_targets=committed.copy(),
            label_changed=changed, selected_alias=changed and np.array_equal(committed, ordinary, equal_nan=True),
            criterion_changed=bool(winner["energy"] != records[base_index]["energy"] or
                (self.policy_arm == "B" and not np.array_equal(winner["slacks"][:m], records[base_index]["slacks"][:m]))))
        # Actual C history, before one inherited act/clock. No shadow planner.
        self.heuristic.targets_xy = committed
        plan["targets"] = committed.copy()

    def _criterion(self, d, m, local_columns):
        energy, slacks = permutation_criterion(d["edge_fly_wh"][:m, :m],
            d["edge_slack"][:m, :m], local_columns, counters=self._counts)
        return energy, padded(slacks, (6,))


def make_controller(policy):
    return ResourceController(policy)
