"""The fixed network scheduler: a small-scale path-flow linear program.

This component is **not** learned.  Every control policy - random, static, greedy, or any
future RL agent - is evaluated through this same scheduler at whatever positions it
produces.  Routes, flow splits and resource shares computed here are decisions of a fixed
network-control component and must never be reported as behaviour learned by RL.

Variables
    ``x[k] >= 0`` in Mbps, one per candidate path ``k`` (see
    :func:`envs.uav_service_restoration.network.enumerate_paths`).

Constraints
    1. ``sum_{k serves i} x[k] <= d_i`` for every demand point - service never exceeds
       offered demand, so two UAVs serving one demand point cannot double-count it.
    2. ``sum_{k: l in k} x[k] <= C_l`` for every shared physical edge.
    3. ``sum_k (sum_{l in k and l in g} 1 / C_l) x[k] <= 1`` for every resource domain
       ``g``.  A path that uses two links of the same domain is charged for both, which is
       what makes a half-duplex relay hop cost twice.
    4. ``sum_k x[k] <= core_total_egress_mbps`` when a total core budget is configured.

Every flow is charged once to every resource it traverses; nothing is charged twice and
nothing is skipped.

Objective
    Primary: maximise total delivered traffic.  Secondary (``epsilon_resource``): among
    near-optimal solutions prefer the one using least normalised radio airtime, by adding
    ``secondary_weight * normalised_resource_cost`` to each path's cost.  Because the
    normalised cost lies in ``[0, 1]``, the delivered total is within a *relative*
    ``secondary_weight`` of the true optimum - the documented tolerance for the
    monotonicity property.  ``secondary_rule='none'`` removes the perturbation entirely at
    the price of an arbitrary choice among ties.

There is no fallback approximation.  In particular the scheduler never sums per-path
bottleneck capacities: that overcounts shared edges and is exactly the error these
constraints exist to prevent.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.optimize import linprog

from .config import SchedulerConfig
from .types import (
    NetworkSnapshot,
    SchedulerResult,
    SchedulerSizeLimitError,
    SchedulerSolveError,
    SchedulerStatus,
)


def _empty_result(snapshot: NetworkSnapshot, reason: str) -> SchedulerResult:
    n_demand = int(snapshot.demand_mbps.shape[0])
    return SchedulerResult(
        status=SchedulerStatus.TRIVIAL_ZERO,
        delivered_mbps_per_demand=np.zeros(n_demand, dtype=np.float64),
        delivered_mbps_total=0.0,
        path_flows_mbps=np.zeros(0, dtype=np.float64),
        link_flow_mbps={},
        domain_utilization={domain.domain_id: 0.0 for domain in snapshot.resource_domains},
        gateway_utilization={index: 0.0 for index in snapshot.gateway_egress_capacity_mbps},
        max_constraint_residual=0.0,
        n_variables=0,
        n_constraints=0,
        solver_message=reason,
    )


def _resource_cost_per_path(snapshot: NetworkSnapshot) -> np.ndarray:
    """Normalised radio airtime consumed per Mbps carried on each path."""

    capacity = {link.link_id: link.capacity_mbps for link in snapshot.links}
    wireless = {link.link_id for link in snapshot.links if link.link_class.is_wireless}
    cost = np.zeros(len(snapshot.paths), dtype=np.float64)
    for index, path in enumerate(snapshot.paths):
        total = 0.0
        for link_id in path.link_ids:
            if link_id in wireless:
                total += 1.0 / capacity[link_id]
        cost[index] = total
    peak = float(cost.max()) if cost.size else 0.0
    if peak > 0.0:
        cost = cost / peak
    return cost


#: Exact HiGHS algorithms, tried in this order.  Each solves the *same* linear program;
#: they differ only in algorithm, so falling through the list is never an approximation.
#: The method that succeeded is reported in ``SchedulerResult.solver_method_used``.
_EXACT_METHOD_LADDER = ("highs", "highs-ds", "highs-ipm")


def _method_ladder(preferred: str) -> tuple[str, ...]:
    rest = tuple(name for name in _EXACT_METHOD_LADDER if name != preferred)
    return (preferred, *rest)


def _solve_exact(objective, a_ub, b_ub, config: SchedulerConfig):
    """Solve the LP, retrying the identical model with the other exact HiGHS algorithms.

    A retry changes the algorithm, never the model: the constraint matrix, the bounds and
    the objective are the same arrays.  This exists because HiGHS's default simplex was
    observed to return an ``Unknown`` model status on ordinary well-posed instances of
    this program, where the interior-point algorithm solves it without difficulty.
    """

    last = None
    for method in _method_ladder(str(config.solver_method)):
        solution = linprog(
            c=objective, A_ub=a_ub, b_ub=b_ub, bounds=(0, None), method=method
        )
        setattr(solution, "hmasd_method", method)
        if solution.success:
            return solution
        last = solution
    return last


def solve(snapshot: NetworkSnapshot, config: SchedulerConfig) -> SchedulerResult:
    """Solve one instant's allocation.

    Returns a structured result.  A failure is reported through
    :attr:`SchedulerResult.status`; it is never replaced by an approximation.
    """

    n_paths = len(snapshot.paths)
    n_demand = int(snapshot.demand_mbps.shape[0])
    if n_paths == 0:
        return _empty_result(snapshot, "no candidate path reaches any demand point")

    offered = np.asarray(snapshot.demand_mbps, dtype=np.float64)
    if not np.isfinite(offered).all() or (offered < 0.0).any():
        raise SchedulerSolveError("offered demand must be finite and non-negative")

    capacity_by_link = {link.link_id: float(link.capacity_mbps) for link in snapshot.links}

    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    values: list[np.ndarray] = []
    b_ub: list[float] = []
    row_labels: list[str] = []

    def add_row(coefficients: dict[int, float], bound: float, label: str) -> None:
        if not coefficients:
            return
        row_index = len(b_ub)
        indices = np.fromiter(coefficients.keys(), dtype=np.int64, count=len(coefficients))
        data = np.fromiter(coefficients.values(), dtype=np.float64, count=len(coefficients))
        rows.append(np.full(indices.shape, row_index, dtype=np.int64))
        cols.append(indices)
        values.append(data)
        b_ub.append(float(bound))
        row_labels.append(label)

    # 1. Offered-demand ceilings.
    paths_by_demand: list[list[int]] = [[] for _ in range(n_demand)]
    for index, path in enumerate(snapshot.paths):
        paths_by_demand[int(path.demand_index)].append(index)
    for demand_index, path_indices in enumerate(paths_by_demand):
        if not path_indices:
            continue
        add_row(
            {index: 1.0 for index in path_indices},
            float(offered[demand_index]),
            f"demand:{demand_index}",
        )

    # 2. Per-edge capacities.
    paths_by_link: dict[int, list[int]] = {}
    for index, path in enumerate(snapshot.paths):
        for link_id in path.link_ids:
            paths_by_link.setdefault(int(link_id), []).append(index)
    for link_id in sorted(paths_by_link):
        coefficients: dict[int, float] = {}
        for index in paths_by_link[link_id]:
            # A path visits a given directed edge at most once (paths are cycle-free).
            coefficients[index] = coefficients.get(index, 0.0) + 1.0
        add_row(coefficients, capacity_by_link[link_id], f"link:{link_id}")

    # 3. Shared radio-resource domains (time sharing / half duplex).
    for domain in snapshot.resource_domains:
        domain_links = set(int(link_id) for link_id in domain.link_ids)
        coefficients: dict[int, float] = {}
        for index, path in enumerate(snapshot.paths):
            share = 0.0
            for link_id in path.link_ids:
                if int(link_id) in domain_links:
                    share += 1.0 / capacity_by_link[int(link_id)]
            if share > 0.0:
                coefficients[index] = share
        add_row(coefficients, 1.0, f"domain:{domain.domain_id}")

    # 4. Optional aggregate core budget (every path crosses exactly one wired core edge).
    if snapshot.core_total_egress_mbps is not None:
        add_row(
            {index: 1.0 for index in range(n_paths)},
            float(snapshot.core_total_egress_mbps),
            "core_total",
        )

    n_constraints = len(b_ub)
    if n_paths > int(config.max_variables):
        raise SchedulerSizeLimitError(
            f"{n_paths} path variables exceed scheduler.max_variables "
            f"({config.max_variables}); the problem was not truncated"
        )
    if n_constraints > int(config.max_constraints):
        raise SchedulerSizeLimitError(
            f"{n_constraints} constraints exceed scheduler.max_constraints "
            f"({config.max_constraints}); the problem was not truncated"
        )

    a_ub = sparse.csr_matrix(
        (
            np.concatenate(values) if values else np.zeros(0),
            (
                np.concatenate(rows) if rows else np.zeros(0, dtype=np.int64),
                np.concatenate(cols) if cols else np.zeros(0, dtype=np.int64),
            ),
        ),
        shape=(max(n_constraints, 1), n_paths),
        dtype=np.float64,
    )
    bounds_vector = np.asarray(b_ub, dtype=np.float64) if b_ub else np.zeros(1, dtype=np.float64)

    objective = -np.ones(n_paths, dtype=np.float64)
    if config.secondary_rule == "epsilon_resource" and config.secondary_weight > 0.0:
        objective = objective + float(config.secondary_weight) * _resource_cost_per_path(snapshot)

    # Path rates are bounded below by zero and above only by the constraint rows.  A
    # per-path cap of ``d_i`` would be redundant - the demand row plus non-negativity
    # already implies it - and, combined with the epsilon-perturbed objective, it was
    # observed to drive the HiGHS simplex to an Unknown model status on ordinary
    # instances.  Dropping a redundant bound changes the feasible set not at all.
    solution = _solve_exact(objective, a_ub, bounds_vector, config)

    if not solution.success:
        status = (
            SchedulerStatus.INFEASIBLE
            if getattr(solution, "status", -1) == 2
            else SchedulerStatus.SOLVER_FAILED
        )
        return SchedulerResult(
            status=status,
            delivered_mbps_per_demand=np.zeros(n_demand, dtype=np.float64),
            delivered_mbps_total=0.0,
            path_flows_mbps=np.zeros(n_paths, dtype=np.float64),
            link_flow_mbps={},
            domain_utilization={},
            gateway_utilization={},
            max_constraint_residual=float("nan"),
            n_variables=n_paths,
            n_constraints=n_constraints,
            solver_message=(
                "every exact method in "
                f"{_method_ladder(str(config.solver_method))} failed; last message: "
                + str(getattr(solution, "message", "linprog reported failure"))
            ),
            solver_method_used="",
        )

    flows = np.asarray(solution.x, dtype=np.float64)
    if not np.isfinite(flows).all():
        return SchedulerResult(
            status=SchedulerStatus.NON_FINITE,
            delivered_mbps_per_demand=np.zeros(n_demand, dtype=np.float64),
            delivered_mbps_total=0.0,
            path_flows_mbps=flows,
            link_flow_mbps={},
            domain_utilization={},
            gateway_utilization={},
            max_constraint_residual=float("nan"),
            n_variables=n_paths,
            n_constraints=n_constraints,
            solver_message="linprog returned non-finite path flows",
        )
    # HiGHS may return tiny negative values at the bound; clip without hiding real error.
    tolerance = float(config.feasibility_tolerance)
    if (flows < -max(tolerance, 1e-9)).any():
        return SchedulerResult(
            status=SchedulerStatus.NON_FINITE,
            delivered_mbps_per_demand=np.zeros(n_demand, dtype=np.float64),
            delivered_mbps_total=0.0,
            path_flows_mbps=flows,
            link_flow_mbps={},
            domain_utilization={},
            gateway_utilization={},
            max_constraint_residual=float(np.min(flows)),
            n_variables=n_paths,
            n_constraints=n_constraints,
            solver_message="linprog returned materially negative path flows",
        )
    flows = np.clip(flows, 0.0, None)

    delivered = np.zeros(n_demand, dtype=np.float64)
    for demand_index, path_indices in enumerate(paths_by_demand):
        if path_indices:
            delivered[demand_index] = float(flows[path_indices].sum())

    link_flow = {
        link_id: float(flows[path_indices].sum())
        for link_id, path_indices in sorted(paths_by_link.items())
    }
    domain_utilization: dict[str, float] = {}
    for domain in snapshot.resource_domains:
        usage = 0.0
        for link_id in domain.link_ids:
            usage += link_flow.get(int(link_id), 0.0) / capacity_by_link[int(link_id)]
        domain_utilization[domain.domain_id] = float(usage)
    gateway_utilization: dict[int, float] = {}
    for site_index, gateway_capacity in snapshot.gateway_egress_capacity_mbps.items():
        used = 0.0
        for link in snapshot.links:
            if (
                link.link_class.name == "WIRED_CORE"
                and int(link.target.index) == int(site_index)
            ):
                used += link_flow.get(int(link.link_id), 0.0)
        gateway_utilization[int(site_index)] = (
            float(used / gateway_capacity) if gateway_capacity > 0.0 else 0.0
        )

    residual = 0.0
    if n_constraints:
        lhs = np.asarray(a_ub.dot(flows)).reshape(-1)
        residual = float(np.max(lhs - bounds_vector))

    return SchedulerResult(
        status=SchedulerStatus.OPTIMAL,
        delivered_mbps_per_demand=delivered,
        delivered_mbps_total=float(delivered.sum()),
        path_flows_mbps=flows,
        link_flow_mbps=link_flow,
        domain_utilization=domain_utilization,
        gateway_utilization=gateway_utilization,
        max_constraint_residual=residual,
        n_variables=n_paths,
        n_constraints=n_constraints,
        solver_message=str(getattr(solution, "message", "")),
        solver_method_used=str(getattr(solution, "hmasd_method", config.solver_method)),
    )


def solve_or_raise(snapshot: NetworkSnapshot, config: SchedulerConfig) -> SchedulerResult:
    """Solve, raising :class:`SchedulerSolveError` on any non-successful status."""

    result = solve(snapshot, config)
    if not result.ok:
        raise SchedulerSolveError(
            f"scheduler failed with status {result.status.value}: {result.solver_message}",
            result=result,
        )
    if np.isfinite(result.max_constraint_residual) and (
        result.max_constraint_residual > max(float(config.feasibility_tolerance), 1e-9) * 1e3
    ):
        raise SchedulerSolveError(
            "scheduler solution violates a constraint beyond tolerance: residual "
            f"{result.max_constraint_residual:.3e}",
            result=result,
        )
    return result
