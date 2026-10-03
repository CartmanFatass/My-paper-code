"""Two opportunities: retained C-only first ranking or candidate-clock anticipation."""

from copy import deepcopy
from experiments.candidates.uav_fleet_transmission.b03.controller import continuation_rank, modeled_execution_identity
from experiments.candidates.uav_fleet_transmission.b04 import controller as frozen
from experiments.candidates.uav_fleet_transmission.b04.surrogate import OptionProgram, concatenate, encode_model_report, validate_plan
from experiments.candidates.uav_fleet_transmission.control import decode_public_state
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.controller import _BoundFirst
from .option import enumerate_champions, decline, branch_id, physical_identity, second_clock
from . import segment


class TimingProgram(frozen.TemporalProgram):
    def __init__(self, arm, horizon=500, branch_sink=None, candidate_sink=None, *, reuse=True, segment_sink=None):
        if arm not in ("G_E", "A_E") or horizon != 500:
            raise ValueError("timing comparison is fixed at G_E/A_E H500")
        self.arm, self.horizon = arm, horizon
        self.branch_sink, self.candidate_sink = branch_sink, candidate_sink
        self.reuse, self.segment_sink = bool(reuse), segment_sink
        self._selections, self._plans, self._banks = {}, {}, {}
        self._second_t = None
        # The complete G2 first selector is retained without changing its C-only forecast.
        self._first = _BoundFirst(self) if arm == "G_E" else None
        self.base = self._first.base if self._first is not None else OptionProgram("C", horizon)

    @property
    def second_t(self):
        return self._second_t

    def _emit_segment(self, identifier, result):
        if self.segment_sink is not None:
            self.segment_sink(identifier, deepcopy({key: result[key] for key in ("arrays", "summary", "decisions", "certificate")}))

    def _simulate(self, identifier, controller, report, mask, plan, **kwargs):
        result = segment.simulate_segment(controller, report, mask, plan, reuse=self.reuse, **kwargs)
        self._emit_segment(identifier, result)
        return result

    def _bank(self, controller, report, mask, start_t, identifier):
        positions, users = decode_public_state(report, 8)
        bank = enumerate_champions(positions, users, mask, start_t, self.horizon)
        original = bank["original_R"]
        self._banks[identifier] = dict(start_t=start_t, counts=deepcopy(original["counts"]),
                                      candidate_count=original["candidate_count"], candidate_digest=original["candidate_digest"],
                                      digest_layout=deepcopy(original["digest_layout"]))
        if self.candidate_sink is not None:
            self.candidate_sink(identifier, bank["candidate_rows"].copy())
        return bank

    def _install(self, selected, old_mask):
        execution = OptionProgram("C", self.horizon)
        execution.controller = self.controller
        execution.plan, execution.option_old_mask = validate_plan(selected, old_mask, self.controller.next_t), int(old_mask)
        self.base = execution

    def _ordinary_selection(self, controller, report, mask, start_t, scope, first):
        bank = self._bank(controller, report, mask, start_t, scope + "/bank")
        positions, _ = decode_public_state(report, 8)
        plans, branches = [None, *bank["champions"]], []
        for plan in plans:
            local = branch_id(plan)
            identifier = scope + ("/inner/" if scope.startswith("ae/") else "/branch/") + local
            result = self._simulate(identifier, controller, report, mask, plan, start_t=start_t)
            identity = dict(tree="ae" if scope.startswith("ae/") else "actual", stage=f"t{start_t}",
                            first=first, second=local, second_t=start_t)
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
            raise ValueError("original stationary program is absent from its complete menu")
        return selected, dict(start_t=start_t, second_t=start_t, bank_id=scope + "/bank", original_R=deepcopy(bank["original_R"]),
                              branches=branches, selected_branch=branches[best]["id"],
                              selected_model_branch=branches[best]["model_branch"], selected_plan=deepcopy(selected),
                              selected_physical_identity=branches[best]["physical_identity"], original_R_branch=original_id,
                              strict_model_improvement_over_stay=best != 0)

    def _anticipated_selection(self, report, mask):
        bank_id = "ae/first/bank"
        bank = self._bank(self.controller, report, mask, 40, bank_id)
        positions, _ = decode_public_state(report, 8)
        plans, branches = [None, *bank["champions"]], []
        for plan in plans:
            first, t2 = branch_id(plan), second_clock(plan)
            scope = f"ae/first/{first}/t{t2}"
            prefix = self._simulate(scope + "/prefix", self.controller, report, mask, plan, start_t=40, end_t=t2)
            outer = prefix["arrays"]["positions"][-1].copy()
            inner_report = encode_model_report(outer, report, t2, self.horizon)
            # Inner simulation receives decoded FP32 coordinates and copied terminal history.
            # Its state and sink payloads cannot replace the unrounded outer branch.
            selected, inner = self._ordinary_selection(deepcopy(prefix["terminal_controller"]), inner_report.copy(),
                                                        prefix["terminal_mask"], t2, scope, first)
            suffix = self._simulate(scope + "/suffix", prefix["terminal_controller"], inner_report,
                                    prefix["terminal_mask"], selected, start_t=t2, physical_positions=outer)
            result = concatenate(prefix, suffix)
            result["summary"]["inner_selection"] = frozen._compact(inner)
            result["summary"]["second_t"] = t2
            result["decisions"][t2 - 40]["predicted_temporal_selection"] = frozen._compact(inner)
            identifier = scope + "/outer"
            identity = dict(tree="ae", stage="outer", first=first, second=inner["selected_branch"], second_t=t2)
            summary = deepcopy(result["summary"])
            summary["identity"] = identity
            branches.append(dict(id=first, model_branch=identifier, plan=deepcopy(plan), summary=summary, second_t=t2,
                                 physical_identity=physical_identity(plan), modeled_execution_identity=modeled_execution_identity(result["arrays"])))
            self._emit_branch(identifier, result, identity)
        best = max(range(len(branches)), key=lambda i: continuation_rank(branches[i]["summary"], plans[i]))
        if branches[best]["summary"]["total_J"] <= branches[0]["summary"]["total_J"]:
            best = 0
        selected = deepcopy(plans[best]) if best else decline(bank, positions)
        return selected, dict(start_t=40, second_t=second_clock(selected), bank_id=bank_id, original_R=deepcopy(bank["original_R"]),
                              branches=branches, selected_branch=branches[best]["id"],
                              selected_model_branch=branches[best]["model_branch"], selected_plan=deepcopy(selected),
                              selected_physical_identity=branches[best]["physical_identity"],
                              strict_model_improvement_over_stay=best != 0)

    def select(self, t, report, old_mask):
        if t != self.controller.next_t or ((report is not None) != (t % 10 == 0)):
            raise ValueError("timing program skipped/repeated its clock or public report")
        if self.arm == "G_E" and (self._second_t is None or t < self._second_t):
            command, mask, decision = self._first.select(t, report, old_mask)
            if t == 40:
                record = deepcopy(self._first.continuation)
                self._second_t = second_clock(self.base.plan)
                record.update(start_t=40, second_t=self._second_t, bank_id="actual/t40/bank", selected_plan=deepcopy(self.base.plan),
                              selected_model_branch="actual/t40/branch/" + record["selected_branch"])
                for branch in record["branches"]:
                    branch["model_branch"] = "actual/t40/branch/" + branch["id"]
                self._selections[40], self._plans[40] = record, deepcopy(self.base.plan)
                original = record["original_R"]
                self._banks["actual/t40/bank"].update(start_t=40, counts=deepcopy(original["counts"]),
                                                     digest_layout=deepcopy(original["digest_layout"]))
                decision["temporal"] = deepcopy(record)
            return command, mask, decision
        record = None
        if t == 40 or (self._second_t is not None and t == self._second_t):
            if t in self._selections:
                raise ValueError("scheduled selection repeated")
            if t == 40:
                selected, record = self._anticipated_selection(report, old_mask)
                self._second_t = second_clock(selected)
            else:
                first = self._selections[40]["selected_branch"]
                selected, record = self._ordinary_selection(self.controller, report, old_mask, t,
                                                             f"actual/t{t}/first/{first}", first)
            self._install(selected, old_mask)  # Retains actual history and expires the old plan even on stay.
            self._selections[t], self._plans[t] = deepcopy(record), deepcopy(selected)
        command, mask, decision = self.base.select(t, report, old_mask)
        if record is not None:
            decision["option"] = deepcopy(self.base.plan)
            decision["temporal"] = deepcopy(record)
        return command, mask, decision
