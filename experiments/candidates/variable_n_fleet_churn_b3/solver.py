from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .host import evaluate_physical


class CertificateMiss(RuntimeError):
    def __init__(self, message: str, calls: list[dict[str, object]] | None = None):
        super().__init__(message)
        self.calls = list(calls or [])


@dataclass(frozen=True)
class SolveResult:
    assignment: dict[str, int]
    objective: float
    mip_status: int
    absolute_gap: float


@dataclass(frozen=True)
class CertificateResult:
    keep_history: dict[str, int]
    switch_history: dict[str, int]
    by_variant: dict[str, dict[str, object]]
    calls: list[dict[str, object]]


def _solve(c: np.ndarray, integrality: np.ndarray, lb: np.ndarray, ub: np.ndarray,
           rows: list[dict[int, float]], lower: list[float], upper: list[float]):
    rr: list[int] = []
    cc: list[int] = []
    vv: list[float] = []
    for row_index, row in enumerate(rows):
        for column, value in row.items():
            if value:
                rr.append(row_index); cc.append(column); vv.append(float(value))
    matrix = coo_matrix((vv, (rr, cc)), shape=(len(rows), len(c))).tocsr()
    solved = milp(
        c=c, integrality=integrality, bounds=Bounds(lb, ub),
        constraints=LinearConstraint(matrix, np.asarray(lower), np.asarray(upper)),
        options={"time_limit": 10.0, "mip_rel_gap": 0.0, "presolve": True},
    )
    if int(solved.status) == 2:
        raise CertificateMiss(str(solved.message))
    if not solved.success or solved.x is None:
        raise RuntimeError(f"offline MILP failed status={solved.status}: {solved.message}")
    dual = float(getattr(solved, "mip_dual_bound", solved.fun))
    gap = abs(float(solved.fun) - dual)
    if gap > 1e-9:
        raise RuntimeError(f"offline MILP absolute objective gap {gap} exceeds 1e-9")
    return solved, gap


def solve_reward_complete(
    handles: Sequence[str], capacities: np.ndarray, demand: np.ndarray,
    previous_roles: Mapping[str, int], fixed_roles: Mapping[str, int] | None = None,
    *, service_only: bool = False,
) -> SolveResult:
    """Offline reward-complete MIP; this module is never imported by SP-RDA."""
    n = len(handles)
    x_count, s0, w0 = 4 * n, 4 * n, 4 * n + 9
    variables = 4 * n + 18
    c = np.zeros(variables)
    c[s0:s0 + 9] = -1.0 / 9.0
    if not service_only:
        c[w0:w0 + 9] = 0.10 / 9.0
    integrality = np.zeros(variables, dtype=np.int8); integrality[:x_count] = 1
    lb = np.zeros(variables); ub = np.ones(variables)
    rows: list[dict[int, float]] = []; lower: list[float] = []; upper: list[float] = []
    for i in range(n):
        rows.append({4 * i + role: 1.0 for role in range(4)}); lower.append(1.0); upper.append(1.0)
    for tick in range(3):
        for task in range(3):
            service_row = {s0 + 3 * tick + task: 1.0}
            waste_row = {w0 + 3 * tick + task: -1.0}
            for i, handle in enumerate(handles):
                switched = handle in previous_roles and int(previous_roles[handle]) != task
                factor = 0.0 if switched and tick == 0 else float(capacities[i, task] / demand[task])
                service_row[4 * i + task] = -factor
                waste_row[4 * i + task] = factor
            rows.append(service_row); lower.append(-np.inf); upper.append(0.0)
            rows.append(waste_row); lower.append(-np.inf); upper.append(1.0)
    index = {h: i for i, h in enumerate(handles)}
    for handle, role in (fixed_roles or {}).items():
        i = index[handle]
        for candidate in range(4):
            lb[4 * i + candidate] = ub[4 * i + candidate] = float(candidate == role)
    solved, gap = _solve(c, integrality, lb, ub, rows, lower, upper)
    assignment = {h: int(np.argmax(solved.x[4 * i:4 * i + 4])) for i, h in enumerate(handles)}
    if service_only:
        delivered = np.zeros(3)
        for i, h in enumerate(handles):
            role = assignment[h]
            if role < 3:
                delivered[role] += capacities[i, role]
        value = float(np.minimum(delivered / demand, 1.0).mean())
    else:
        value = evaluate_physical(handles, capacities, demand, previous_roles, assignment).J
    return SolveResult(assignment, value, int(solved.status), gap)


def _joint_history_solve(
    pre_handles: tuple[str, ...], post_handles: tuple[str, ...], demand: np.ndarray,
    variants: Mapping[str, tuple[np.ndarray, np.ndarray]], pre_bounds: Mapping[str, float],
    mode: str, *, keep_floor: float | None = None, keep_history: Mapping[str, int] | None = None,
    q_ceiling: float | None = None,
) -> tuple[dict[str, int], float, float]:
    """Calls 5--8: shared history with exact maximin-KEEP or minimax-Q law."""
    npre = len(pre_handles)
    survivor_set = set(post_handles).intersection(pre_handles)
    survivor_indices = [i for i, h in enumerate(pre_handles) if h in survivor_set]
    joiners = [h for h in post_handles if h not in survivor_set]
    columns = 4 * npre
    x0 = 0
    # Variant-specific joiner assignments are present only for the KEEP objective.
    join_offsets: dict[str, int] = {}
    if mode in ("max_keep", "rank_keep"):
        for name in variants:
            join_offsets[name] = columns; columns += 4 * len(joiners)
    pre_s_offsets: dict[str, int] = {}
    for name in variants:
        pre_s_offsets[name] = columns; columns += 3
    keep_s_offsets: dict[str, int] = {}; keep_w_offsets: dict[str, int] = {}
    q_s_offsets: dict[str, int] = {}; q_y_offsets: dict[str, int] = {}
    if mode in ("max_keep", "rank_keep"):
        for name in variants:
            keep_s_offsets[name] = columns; columns += 9
            keep_w_offsets[name] = columns; columns += 9
    else:
        for name in variants:
            q_s_offsets[name] = columns; columns += 3
            q_y_offsets[name] = columns; columns += 3
    scalar = columns; columns += 1

    c = np.zeros(columns); integrality = np.zeros(columns, dtype=np.int8)
    lb = np.zeros(columns); ub = np.ones(columns)
    integrality[:4 * npre] = 1
    if mode in ("max_keep", "rank_keep"):
        for offset in join_offsets.values(): integrality[offset:offset + 4 * len(joiners)] = 1
    else:
        for offset in q_y_offsets.values(): integrality[offset:offset + 3] = 1
    if mode == "max_keep": c[scalar] = -1.0; lb[scalar] = -1.0
    elif mode == "min_q": c[scalar] = 1.0
    else:
        for i in range(npre):
            place = 4 ** (npre - 1 - i)
            for role in range(4): c[4 * i + role] = float(role * place)

    rows: list[dict[int, float]] = []; lower: list[float] = []; upper: list[float] = []
    for i in range(npre):
        rows.append({4 * i + role: 1.0 for role in range(4)}); lower.append(1.0); upper.append(1.0)
    for name, (pre_cap, post_cap) in variants.items():
        # S_pre >= S_star-0.02, with service auxiliaries upper-bounded by min(load,1).
        ps = pre_s_offsets[name]
        for task in range(3):
            row = {ps + task: 1.0}
            for i in range(npre): row[4 * i + task] = -float(pre_cap[i, task] / demand[task])
            rows.append(row); lower.append(-np.inf); upper.append(0.0)
        rows.append({ps + task: 1.0 / 3.0 for task in range(3)})
        lower.append(float(pre_bounds[name])); upper.append(np.inf)

        post_index = {h: i for i, h in enumerate(post_handles)}
        if mode in ("max_keep", "rank_keep"):
            jo = join_offsets[name]
            for j in range(len(joiners)):
                rows.append({jo + 4 * j + role: 1.0 for role in range(4)})
                lower.append(1.0); upper.append(1.0)
            ks, kw = keep_s_offsets[name], keep_w_offsets[name]
            jindex = {h: j for j, h in enumerate(joiners)}
            for tick in range(3):
                for task in range(3):
                    srow = {ks + 3 * tick + task: 1.0}
                    wrow = {kw + 3 * tick + task: -1.0}
                    for i, h in enumerate(pre_handles):
                        if h in post_index:
                            factor = float(post_cap[post_index[h], task] / demand[task])
                            srow[4 * i + task] = -factor; wrow[4 * i + task] = factor
                    for h in joiners:
                        factor = float(post_cap[post_index[h], task] / demand[task])
                        idx = jo + 4 * jindex[h] + task
                        srow[idx] = -factor; wrow[idx] = factor
                    rows.append(srow); lower.append(-np.inf); upper.append(0.0)
                    rows.append(wrow); lower.append(-np.inf); upper.append(1.0)
            jrow = {ks + k: 1.0 / 9.0 for k in range(9)}
            jrow.update({kw + k: -0.10 / 9.0 for k in range(9)})
            if mode == "max_keep":
                jrow[scalar] = -1.0; rows.append(jrow); lower.append(0.0); upper.append(np.inf)
            else:
                rows.append(jrow); lower.append(float(keep_floor)); upper.append(np.inf)
        else:
            qs, qy = q_s_offsets[name], q_y_offsets[name]
            for task in range(3):
                delivered: dict[int, float] = {}
                for i in survivor_indices:
                    h = pre_handles[i]
                    delivered[4 * i + task] = float(post_cap[post_index[h], task] / demand[task])
                # s=min(delivered,1), exact big-M branch (delivered is <4 here).
                row1 = {qs + task: 1.0, **{k: -v for k, v in delivered.items()}}
                rows.append(row1); lower.append(-np.inf); upper.append(0.0)
                row2 = {qs + task: 1.0, qy + task: -4.0, **{k: -v for k, v in delivered.items()}}
                rows.append(row2); lower.append(-4.0); upper.append(np.inf)
                rows.append({qs + task: 1.0, qy + task: 4.0}); lower.append(1.0); upper.append(np.inf)
            qrow = {scalar: 1.0, **{qs + task: -1.0 / 3.0 for task in range(3)}}
            rows.append(qrow); lower.append(0.0); upper.append(np.inf)
            if q_ceiling is not None:
                rows.append({qs + task: 1.0 / 3.0 for task in range(3)})
                lower.append(-np.inf); upper.append(float(q_ceiling))

    if keep_history is not None:
        rows.append({4 * i + int(keep_history[pre_handles[i]]): 1.0 for i in survivor_indices})
        lower.append(-np.inf); upper.append(float(len(survivor_indices) - 1))

    solved, gap = _solve(c, integrality, lb, ub, rows, lower, upper)
    history = {h: int(np.argmax(solved.x[4 * i:4 * i + 4])) for i, h in enumerate(pre_handles)}
    objective = -float(solved.fun) if mode == "max_keep" else float(solved.x[scalar] if mode == "min_q" else solved.fun)
    return history, objective, gap


def certify_shared_histories(
    pre_handles: tuple[str, ...], post_handles: tuple[str, ...], demand: np.ndarray,
    variants: Mapping[str, tuple[np.ndarray, np.ndarray]],
) -> CertificateResult:
    """Execute exactly the registered 24 logical calls for one shared raw base."""
    calls: list[dict[str, object]] = []
    order = ("FIXED-SEPARABLE", "FIXED-COUPLED", "REAL-SEPARABLE", "REAL-COUPLED")
    sstar: dict[str, float] = {}
    for name in order:
        solved = solve_reward_complete(pre_handles, variants[name][0], demand, {}, service_only=True)
        sstar[name] = solved.objective
        calls.append({"call": len(calls) + 1, "kind": "S_STAR", "variant": name,
                      "objective": solved.objective, "absolute_gap": solved.absolute_gap})
    bounds = {name: sstar[name] - 0.02 for name in order}
    try:
        keep0, tstar, gap = _joint_history_solve(pre_handles, post_handles, demand, variants, bounds, "max_keep")
    except CertificateMiss as error:
        calls.append({"call": 5, "kind": "KEEP_MAXIMIN", "status": "INFEASIBLE"})
        raise CertificateMiss(str(error), calls) from error
    calls.append({"call": 5, "kind": "KEEP_MAXIMIN", "objective": tstar, "absolute_gap": gap})
    keep, rank_value, gap = _joint_history_solve(
        pre_handles, post_handles, demand, variants, bounds, "rank_keep", keep_floor=tstar - 1e-9,
    )
    calls.append({"call": 6, "kind": "KEEP_RANK", "objective": rank_value, "absolute_gap": gap})
    try:
        switch0, qstar, gap = _joint_history_solve(
            pre_handles, post_handles, demand, variants, bounds, "min_q", keep_history=keep,
        )
    except CertificateMiss as error:
        calls.append({"call": 7, "kind": "SWITCH_MINIMAX_Q", "status": "INFEASIBLE"})
        raise CertificateMiss(str(error), calls) from error
    calls.append({"call": 7, "kind": "SWITCH_MINIMAX_Q", "objective": qstar, "absolute_gap": gap})
    switch, rank_value, gap = _joint_history_solve(
        pre_handles, post_handles, demand, variants, bounds, "rank_q", keep_history=keep,
        q_ceiling=qstar + 1e-9,
    )
    calls.append({"call": 8, "kind": "SWITCH_RANK", "objective": rank_value, "absolute_gap": gap})
    del keep0, switch0

    survivors = set(pre_handles).intersection(post_handles)
    by_variant: dict[str, dict[str, object]] = {}
    for name in order:
        _, post_cap = variants[name]
        values: dict[str, object] = {"S_star": sstar[name]}
        for history_name, history in (("KEEP", keep), ("SWITCH", switch)):
            survivor_history = {h: int(history[h]) for h in survivors}
            for kind, fixed in (("R", None), ("K", survivor_history)):
                solved = solve_reward_complete(post_handles, post_cap, demand, survivor_history, fixed_roles=fixed)
                values[f"{kind}_{history_name}"] = solved.objective
                if kind == "R": values[f"{kind}_{history_name}_assignment"] = solved.assignment
                calls.append({"call": len(calls) + 1, "kind": f"{kind}_{history_name}", "variant": name,
                              "objective": solved.objective, "absolute_gap": solved.absolute_gap})
        by_variant[name] = values
    if len(calls) != 24:
        raise RuntimeError(f"certificate routine executed {len(calls)} logical calls, expected 24")

    post_index = {h: i for i, h in enumerate(post_handles)}
    for name in order:
        values = by_variant[name]
        _, post_cap = variants[name]
        for history in (keep, switch):
            if any(history[h] != 3 and post_cap[post_index[h], history[h]] <= 0.0 for h in survivors):
                raise CertificateMiss("old survivor role lacks positive post-event capability", calls)
        if float(values["R_KEEP"]) - float(values["K_KEEP"]) > 0.01 + 1e-9:
            raise CertificateMiss("KEEP gap exceeds 0.01", calls)
        if float(values["R_SWITCH"]) - float(values["K_SWITCH"]) < 0.10 - 1e-9:
            raise CertificateMiss("SWITCH gap below 0.10", calls)
    if all(keep[h] == switch[h] for h in survivors):
        raise CertificateMiss("KEEP and SWITCH histories do not differ on a survivor", calls)
    return CertificateResult(keep, switch, by_variant, calls)
