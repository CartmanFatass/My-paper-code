"""Explicit simulator bindings around frozen B03/B04 selection algorithms.

Only methods with model calls are copied; actual execution/properties remain
inherited from B04. No frozen module or shared global is patched at runtime.
"""
from copy import deepcopy

from experiments.candidates.uav_fleet_transmission.b03 import controller as first
from experiments.candidates.uav_fleet_transmission.b03 import surrogate as b03
from experiments.candidates.uav_fleet_transmission.b04 import controller as frozen
from experiments.candidates.uav_fleet_transmission.b04.surrogate import concatenate, encode_model_report
from experiments.candidates.uav_fleet_transmission.b04.option import branch_id, decline, physical_identity
from experiments.candidates.uav_fleet_transmission.control import decode_public_state
from experiments.candidates.uav_fleet_transmission.b03.controller import continuation_rank, modeled_execution_identity
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization import cycle
from . import segment


class _BoundFirst(first.ContinuationProgram):
    def __init__(self, owner):
        super().__init__(owner.horizon, branch_sink=owner._original_branch, candidate_sink=owner._original_bank)
        self.owner = owner

    def _simulate(self, controller, report, mask, plan, horizon):
        simulator = cycle.simulate_continuation if self.owner.reuse else b03.simulate_continuation
        result = simulator(controller, report, mask, plan, horizon)
        work = result.pop("reuse", None)
        segment.certify(result, controller, report, mask, plan, 40, horizon, reuse=work)
        self.owner._emit_segment("actual/t40/branch/" + first.branch_id(plan), result)
        return result

    def select(self, t, state, old_mask):
        shortlist = None
        if t == 40:
            if self.continuation is not None or self.controller.next_t != 40:
                raise ValueError("T selection repeated or reached with wrong clock")
            positions, users = decode_public_state(state, 8)
            shortlist = first.enumerate_champions(positions, users, old_mask)
            if self.candidate_sink is not None:
                self.candidate_sink(shortlist["candidate_rows"])
            plans = [None, *shortlist["champions"]]
            branches = []
            for plan in plans:
                result = self._simulate(self.controller, state, old_mask, plan, self.horizon)
                identifier = first.branch_id(plan)
                branches.append({"id": identifier, "physical_identity": first.physical_identity(plan),
                    "modeled_execution_identity": modeled_execution_identity(result["arrays"]),
                    "plan": deepcopy(plan), "summary": result["summary"]})
                if self.branch_sink is not None:
                    self.branch_sink(identifier, result)
            best = max(range(len(branches)), key=lambda i: continuation_rank(branches[i]["summary"], plans[i]))
            # Full-score ties always decline, regardless of a service tie-break.
            if branches[best]["summary"]["total_J"] <= branches[0]["summary"]["total_J"]:
                best = 0
            selected = deepcopy(plans[best])
            if selected is None:
                selected = deepcopy(shortlist["original_R"])
                selected.update(initiated=False, member=None, site=None, offsets=None, commands=[],
                    duration=0, arrival_t=None, predicted_destination=positions.tolist(), predicted_mask=None,
                    predicted_total_J=selected["stay_total_J"], predicted_total_served=selected["stay_total_served"])
            self.base.plan, self.base.option_old_mask = selected, int(old_mask)
            original_id = first.branch_id(shortlist["original_R"])
            if original_id not in {b["id"] for b in branches}:
                raise ValueError("original R complete program missing from retained branches")
            original = next(b for b in branches if b["id"] == original_id)
            if branches[best]["summary"]["total_J"] < original["summary"]["total_J"]:
                raise ValueError("selected model value below represented original R")
            global_physical = shortlist["original_R"]["selected"]
            self.continuation = {"original_R": shortlist["original_R"], "branches": branches,
                "selected_branch": branches[best]["id"], "original_R_branch": original_id,
                "best_stationary_physical_branch": None if global_physical is None else
                    f"m{global_physical['member']}_s{global_physical['site']}",
                "selected_physical_identity": branches[best]["physical_identity"],
                "original_R_physical_identity": first.physical_identity(shortlist["original_R"]),
                "strict_model_improvement_over_stay": best != 0,
                "model_J_gain_over_R": branches[best]["summary"]["total_J"] - original["summary"]["total_J"]}
        command, new_mask, decision = self.base.select(t, state, old_mask)
        if shortlist is not None:
            decision["option"] = deepcopy(self.base.plan)
            decision["continuation"] = self.continuation
        return command, new_mask, decision


class TemporalProgram(frozen.TemporalProgram):
    def __init__(self, arm, horizon=500, branch_sink=None, candidate_sink=None, *, reuse=False, segment_sink=None):
        if arm not in ("G2", "A2") or horizon != 500:
            raise ValueError("the reuse comparison is fixed at G2/A2 H500")
        super().__init__(arm, horizon, branch_sink, candidate_sink)
        self.reuse, self.segment_sink = bool(reuse), segment_sink
        if arm == "G2":
            self._first = _BoundFirst(self)
            self.base = self._first.base

    def _emit_segment(self, identifier, result):
        if self.segment_sink is not None:
            self.segment_sink(identifier, deepcopy({key: result[key] for key in ("arrays", "summary", "decisions", "certificate")}))

    def _simulate(self, identifier, controller, report, mask, plan, **kwargs):
        result = segment.simulate_segment(controller, report, mask, plan, reuse=self.reuse, **kwargs)
        self._emit_segment(identifier, result)
        return result

    def _ordinary_selection(self, controller, report, mask, start_t, scope, first=None):
        bank_id = scope+"/bank" if first is None else f"a2/first/{first}/t120/bank"
        bank = self._bank(controller, report, mask, start_t, bank_id)
        positions, _ = decode_public_state(report, 8)
        plans = [None, *bank["champions"]]
        branches = []
        for plan in plans:
            local = branch_id(plan)
            identifier = scope+"/branch/"+local if first is None else scope+"/"+local
            result = self._simulate(identifier, controller, report, mask, plan, start_t=start_t)
            identity = dict(tree="actual" if first is None else "a2", stage=f"t{start_t}",
                            first=(local if start_t == 40 else self._selections.get(40, {}).get("selected_branch"))
                                if first is None else first, second=local if start_t == 120 else None)
            summary = deepcopy(result["summary"])
            summary["identity"] = identity
            branches.append(dict(id=local, model_branch=identifier, plan=deepcopy(plan), summary=summary,
                physical_identity=physical_identity(plan), modeled_execution_identity=modeled_execution_identity(result["arrays"])))
            self._emit_branch(identifier, result, identity)
        best = max(range(len(branches)), key=lambda i: continuation_rank(branches[i]["summary"], plans[i]))
        if branches[best]["summary"]["total_J"] <= branches[0]["summary"]["total_J"]:
            best = 0
        selected = deepcopy(plans[best]) if best else decline(bank, positions)
        original_id = branch_id(bank["original_R"])
        if original_id not in {b["id"] for b in branches}:
            raise ValueError("original R is absent from its fixed menu")
        record = dict(start_t=start_t, bank_id=bank_id, original_R=bank["original_R"], branches=branches,
            selected_branch=branches[best]["id"], selected_model_branch=branches[best]["model_branch"],
            selected_plan=deepcopy(selected), selected_physical_identity=branches[best]["physical_identity"],
            original_R_branch=original_id, strict_model_improvement_over_stay=best != 0)
        return selected, record

    def _anticipated_selection(self, report, mask):
        bank_id = "a2/first/bank"
        bank = self._bank(self.controller, report, mask, 40, bank_id)
        positions, _ = decode_public_state(report, 8)
        plans, branches = [None, *bank["champions"]], []
        for plan in plans:
            first = branch_id(plan)
            prefix = self._simulate(f"a2/first/{first}/prefix", self.controller, report, mask, plan, start_t=40, end_t=120)
            # Neither the inner search nor its returned states may see/replace
            # the existing unrounded outer physical state.
            outer_physical = prefix["arrays"]["positions"][-1].copy()
            report120 = encode_model_report(outer_physical, report, 120, self.horizon)
            selected120, inner = self._ordinary_selection(prefix["terminal_controller"], report120,
                prefix["terminal_mask"], 120, f"a2/first/{first}/inner", first=first)
            suffix = self._simulate(f"a2/first/{first}/suffix", prefix["terminal_controller"], report120, prefix["terminal_mask"],
                selected120, start_t=120, physical_positions=outer_physical)
            result = concatenate(prefix, suffix)
            result["summary"]["inner_selection"] = frozen._compact(inner)
            result["decisions"][80]["predicted_temporal_selection"] = frozen._compact(inner)
            identifier = f"a2/first/{first}/outer"
            identity = dict(tree="a2", stage="outer", first=first, second=inner["selected_branch"])
            summary = deepcopy(result["summary"])
            summary["identity"] = identity
            branches.append(dict(id=first, model_branch=identifier, plan=deepcopy(plan), summary=summary,
                physical_identity=physical_identity(plan), modeled_execution_identity=modeled_execution_identity(result["arrays"])))
            self._emit_branch(identifier, result, identity)
        best = max(range(len(branches)), key=lambda i: continuation_rank(branches[i]["summary"], plans[i]))
        if branches[best]["summary"]["total_J"] <= branches[0]["summary"]["total_J"]:
            best = 0
        selected = deepcopy(plans[best]) if best else decline(bank, positions)
        return selected, dict(start_t=40, bank_id=bank_id, original_R=bank["original_R"], branches=branches,
            selected_branch=branches[best]["id"], selected_model_branch=branches[best]["model_branch"],
            selected_plan=deepcopy(selected), selected_physical_identity=branches[best]["physical_identity"],
            strict_model_improvement_over_stay=best != 0)
