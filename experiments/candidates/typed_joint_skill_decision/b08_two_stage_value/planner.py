"""Fixed B08 allocations around the read-only B03/B04/B08 kernels.

Only a first menu is allocated. Every anticipated and actual second menu is
complete. Sinks receive detached evidence; segment sinks may retain certificates
and refer prefix/suffix arrays to the subsequently emitted outer branch slices.
No model cache is shared between calls to the inherited segment kernels.
"""
from copy import deepcopy

import numpy as np

from experiments.candidates.uav_fleet_transmission.b03 import surrogate as b03
from experiments.candidates.uav_fleet_transmission.b03.controller import (
    continuation_rank, modeled_execution_identity,
)
from experiments.candidates.uav_fleet_transmission.b03.option import stationary_rank
from experiments.candidates.uav_fleet_transmission.b04 import controller as frozen
from experiments.candidates.uav_fleet_transmission.b04.option import (
    branch_id, decline, physical_identity,
)
from experiments.candidates.uav_fleet_transmission.b04.surrogate import (
    concatenate, encode_model_report,
)
from experiments.candidates.uav_fleet_transmission.control import decode_public_state
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import cycle
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse import (
    controller as inherited, segment,
)

# Local bindings also permit synthetic substitution without patching frozen modules.
simulate_segment = segment.simulate_segment
simulate_c_only = cycle.simulate_continuation
simulate_c_only_full = b03.simulate_continuation
certify = segment.certify


def _finite_summary(result):
    if not all(np.isfinite(result["summary"][key]) for key in ("total_J", "total_served")):
        raise ValueError("nonfinite complete model value")


def _choice(branches, plans):
    keys = [continuation_rank(b["summary"], p) for b, p in zip(branches, plans)]
    if not all(np.isfinite(key).all() for key in keys):
        raise ValueError("nonfinite complete choice key")
    best = max(range(len(branches)), key=lambda i: keys[i])
    # Service cannot overturn the original strict J improvement requirement.
    if branches[best]["summary"]["total_J"] <= branches[0]["summary"]["total_J"]:
        best = 0
    for branch, key in zip(branches, keys):
        branch["choice_key"] = list(key)
    return best


class BudgetedProgram(inherited.TemporalProgram):
    """H500 G2/A2/K2-C/K2-S/L2, with caller-owned scoring and persistence.

    ``scorer(report, controller_history, mask, bank, plans)`` returns exactly
    one finite FP32 score per valid candidate, including stay. ``menu_sink``
    receives the legal first menu as detached keyword arguments before scoring.
    ``prepare_first`` records the root choice without installing or issuing it;
    acquisition must end there, and its clock cannot subsequently be reused.
    """

    def __init__(self, arm, horizon=500, branch_sink=None, candidate_sink=None,
                 *, reuse=True, segment_sink=None, menu_sink=None, scorer=None):
        if arm not in ("G2", "A2", "K2-C", "K2-S", "L2") or horizon != 500:
            raise ValueError("B08 requires a fixed G2/A2/K2-C/K2-S/L2 H500 arm")
        if arm == "L2" and scorer is None:
            raise ValueError("L2 requires its frozen injected scorer")
        super().__init__("G2" if arm == "G2" else "A2", horizon,
                         branch_sink, candidate_sink, reuse=reuse,
                         segment_sink=segment_sink)
        self.arm, self.menu_sink, self.scorer = arm, menu_sink, scorer
        self._first_attempted = False

    def _simulate(self, identifier, controller, report, mask, plan, **kwargs):
        result = simulate_segment(controller, report, mask, plan,
                                  reuse=self.reuse, **kwargs)
        _finite_summary(result)
        self._emit_segment(identifier, result)
        return result

    def _c_only(self, identifier, report, mask, plan):
        simulator = simulate_c_only if self.reuse else simulate_c_only_full
        result = simulator(self.controller, report, mask, plan, self.horizon)
        work = result.pop("reuse", None)
        certify(result, self.controller, report, mask, plan, 40,
                self.horizon, reuse=work)
        _finite_summary(result)
        self._emit_segment(identifier, result)
        return result

    def _first_menu(self, report, mask):
        identifier = "actual/t40/bank" if self.arm == "G2" else "a2/first/bank"
        bank = self._bank(self.controller, report, mask, 40, identifier)
        plans = [None, *bank["champions"]]
        if len(plans) > 8:
            raise ValueError("first menu exceeds the fixed eight valid candidates")
        if self.menu_sink is not None:
            self.menu_sink(start_t=40, report=deepcopy(report),
                commands=self.controller.commands.copy(), history=deepcopy(self.controller),
                mask=int(mask), bank=deepcopy(bank), plans=deepcopy(plans))
        return identifier, bank, plans

    def _allocation(self, report, mask, bank, plans):
        all_ids = [branch_id(p) for p in plans]
        rows = []
        for plan in plans[1:]:
            key = stationary_rank(plan["selected"])
            if not np.isfinite(key).all():
                raise ValueError("nonfinite stationary allocation key")
            rows.append(dict(id=branch_id(plan), stationary_key=list(key)))
        if self.arm in ("A2", "G2"):
            rule, ranked, retained = "all", all_ids[1:], all_ids
        else:
            if self.arm == "K2-C":
                rule = "c_only_original_continuation_rank"
                for row, plan in zip(rows, plans[1:]):
                    identifier = "k2-c/rank/t40/branch/" + row["id"]
                    result = self._c_only(identifier, report, mask, plan)
                    identity = dict(tree="k2-c", stage="rank_t40", first=row["id"], second=None)
                    row.update(score=float(result["summary"]["total_J"]),
                        served=int(result["summary"]["total_served"]),
                        model_branch=identifier, summary=deepcopy(result["summary"]),
                        physical_identity=physical_identity(plan),
                        modeled_execution_identity=modeled_execution_identity(result["arrays"]))
                    row["allocation_key"] = list(continuation_rank(result["summary"], plan))
                    self._emit_branch(identifier, result, identity)
            elif self.arm == "K2-S":
                rule = "original_stationary"
                for row in rows:
                    row["score"] = row["stationary_key"][0]
                    row["allocation_key"] = row["stationary_key"].copy()
            else:
                rule = "fp32_score_then_original_stationary"
                # Each callback gets a separate copy, including the scorer's bank.
                scores = np.asarray(self.scorer(deepcopy(report), deepcopy(self.controller),
                    int(mask), deepcopy(bank), deepcopy(plans)))
                if scores.dtype != np.float32 or scores.shape != (len(plans),) or not np.isfinite(scores).all():
                    raise ValueError("scorer must return one finite FP32 score per valid candidate")
                scores = scores.copy()
                for row, score in zip(rows, scores[1:]):
                    row["score"] = float(score)
                    row["allocation_key"] = [float(score), *row["stationary_key"]]
            ranked = [row["id"] for row in sorted(rows, key=lambda row: tuple(row["allocation_key"]), reverse=True)]
            chosen = set(ranked[:2])
            # Preserve the original menu order in the paid nested branch traversal.
            retained = ["stay", *[identifier for identifier in all_ids[1:] if identifier in chosen]]
        for row in rows:
            row["retained"] = row["id"] in retained
        allocation = dict(rule=rule, candidates=rows, all_first_ids=all_ids,
            ranked_nonstay_ids=ranked, retained_first_ids=retained,
            excluded_first_ids=[identifier for identifier in all_ids if identifier not in retained])
        if self.arm == "L2":
            allocation["scores"] = scores.tolist()
        return [p for p in plans if branch_id(p) in retained], allocation

    def _g2_selection(self, report, mask, bank_id, bank, plans, allocation):
        branches = []
        for plan in plans:
            local = branch_id(plan)
            identifier = "actual/t40/branch/" + local
            result = self._c_only(identifier, report, mask, plan)
            branches.append(dict(id=local, physical_identity=physical_identity(plan),
                modeled_execution_identity=modeled_execution_identity(result["arrays"]),
                plan=deepcopy(plan), summary=deepcopy(result["summary"])))
            self._emit_branch(identifier, result,
                dict(tree="actual", stage="t40", first=local, second=None))
        best = _choice(branches, plans)
        positions, _ = decode_public_state(report, 8)
        selected = deepcopy(plans[best]) if best else decline(bank, positions)
        original_id = branch_id(bank["original_R"])
        original = next(b for b in branches if b["id"] == original_id)
        global_physical = bank["original_R"]["selected"]
        continuation = dict(original_R=deepcopy(bank["original_R"]),
            branches=[{k: deepcopy(v) for k, v in b.items() if k != "choice_key"} for b in branches],
            selected_branch=branches[best]["id"], original_R_branch=original_id,
            best_stationary_physical_branch=None if global_physical is None else
                f"m{global_physical['member']}_s{global_physical['site']}",
            selected_physical_identity=branches[best]["physical_identity"],
            original_R_physical_identity=physical_identity(bank["original_R"]),
            strict_model_improvement_over_stay=best != 0,
            model_J_gain_over_R=branches[best]["summary"]["total_J"]-original["summary"]["total_J"])
        self._first.continuation = continuation
        for branch in branches:
            branch["model_branch"] = "actual/t40/branch/"+branch["id"]
        record = dict(continuation, start_t=40, bank_id=bank_id, branches=branches,
            selected_plan=deepcopy(selected),
            selected_model_branch="actual/t40/branch/"+branches[best]["id"], allocation=allocation)
        return selected, record

    def _anticipated_selection(self, report, mask):
        if self._first_attempted:
            raise ValueError("first selection cannot be prepared or selected twice")
        self._first_attempted = True
        bank_id, bank, full_plans = self._first_menu(report, mask)
        plans, allocation = self._allocation(report, mask, bank, full_plans)
        if self.arm == "G2":
            return self._g2_selection(report, mask, bank_id, bank, plans, allocation)
        positions, _ = decode_public_state(report, 8)
        branches = []
        for plan in plans:
            first = branch_id(plan)
            prefix = self._simulate(f"a2/first/{first}/prefix", self.controller,
                report, mask, plan, start_t=40, end_t=120)
            outer_physical = prefix["arrays"]["positions"][-1].copy()
            report120 = encode_model_report(outer_physical, report, 120, self.horizon)
            selected120, inner = self._ordinary_selection(prefix["terminal_controller"],
                report120, prefix["terminal_mask"], 120, f"a2/first/{first}/inner", first=first)
            suffix = self._simulate(f"a2/first/{first}/suffix", prefix["terminal_controller"],
                report120, prefix["terminal_mask"], selected120, start_t=120,
                physical_positions=outer_physical)
            result = concatenate(prefix, suffix)
            _finite_summary(result)
            result["summary"]["inner_selection"] = frozen._compact(inner)
            result["decisions"][80]["predicted_temporal_selection"] = frozen._compact(inner)
            identifier = f"a2/first/{first}/outer"
            identity = dict(tree="a2", stage="outer", first=first, second=inner["selected_branch"])
            summary = deepcopy(result["summary"])
            summary["identity"] = identity
            branches.append(dict(id=first, model_branch=identifier, plan=deepcopy(plan), summary=summary,
                physical_identity=physical_identity(plan),
                modeled_execution_identity=modeled_execution_identity(result["arrays"]),
                inner_selection=deepcopy(inner)))
            self._emit_branch(identifier, result, identity)
        best = _choice(branches, plans)
        selected = deepcopy(plans[best]) if best else decline(bank, positions)
        record = dict(start_t=40, bank_id=bank_id, original_R=deepcopy(bank["original_R"]),
            branches=branches, selected_branch=branches[best]["id"],
            selected_model_branch=branches[best]["model_branch"], selected_plan=deepcopy(selected),
            selected_physical_identity=branches[best]["physical_identity"],
            strict_model_improvement_over_stay=best != 0, allocation=allocation,
            Q2={b["id"]: b["summary"]["total_J"] for b in branches})
        return selected, record

    def _ordinary_selection(self, *args, **kwargs):
        selected, record = super()._ordinary_selection(*args, **kwargs)
        # Complete second-stage work and choices are inherited, with full keys
        # retained for reconstruction in addition to the original compact record.
        for branch in record["branches"]:
            key = continuation_rank(branch["summary"], branch["plan"])
            if not np.isfinite(key).all():
                raise ValueError("nonfinite second-stage choice key")
            branch["choice_key"] = list(key)
        return selected, record

    def prepare_first(self, report, mask):
        if self.controller.next_t != 40 or report is None or 40 in self._selections:
            raise ValueError("prepare_first requires the unused lawful t40 boundary")
        selected, record = self._anticipated_selection(report, mask)
        self._selections[40], self._plans[40] = deepcopy(record), deepcopy(selected)
        return deepcopy(selected), deepcopy(record)

    def select(self, t, report, old_mask):
        if self.arm != "G2" or t >= 120:
            return super().select(t, report, old_mask)
        if t != self.controller.next_t or ((report is not None) != (t % 10 == 0)):
            raise ValueError("temporal program skipped/repeated a clock or public report")
        if t == 40:
            if 40 in self._selections:
                raise ValueError("scheduled selection repeated")
            selected, record = self._anticipated_selection(report, old_mask)
            # G2 uses the original B02 execution object through its first stage.
            self.base.plan, self.base.option_old_mask = deepcopy(selected), int(old_mask)
            self._selections[40], self._plans[40] = deepcopy(record), deepcopy(selected)
        command, mask, decision = self.base.select(t, report, old_mask)
        if t == 40:
            decision["option"] = deepcopy(self.base.plan)
            decision["continuation"] = deepcopy(self._first.continuation)
        return command, mask, decision
