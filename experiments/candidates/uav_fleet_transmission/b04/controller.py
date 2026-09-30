"""Fixed T/G2/A2 selectors, streaming each charged model branch once."""
from copy import deepcopy
import hashlib

import numpy as np

from ..b03.controller import ContinuationProgram, continuation_rank, modeled_execution_identity
from ..control import decode_public_state
from .option import enumerate_champions, decline, branch_id, physical_identity
from .surrogate import OptionProgram, simulate_segment, concatenate, encode_model_report, validate_plan


def _artifact(result, identity):
    # A sink may mutate its argument or return anything; neither can enter the
    # selector's retained plans, summaries, physical states or future decisions.
    value = deepcopy({key: result[key] for key in ("arrays", "summary", "decisions")})
    value["summary"]["identity"] = deepcopy(identity)
    return value


def _compact(record):
    return {key: deepcopy(record[key]) for key in (
        "start_t", "bank_id", "selected_branch", "selected_model_branch", "selected_plan",
        "selected_physical_identity", "strict_model_improvement_over_stay")}


class TemporalProgram:
    def __init__(self, arm, horizon=500, branch_sink=None, candidate_sink=None):
        if arm not in ("T", "G2", "A2") or horizon != 500:
            raise ValueError("the temporal comparison is fixed at T/G2/A2 H500")
        self.arm, self.horizon = arm, horizon
        self.branch_sink, self.candidate_sink = branch_sink, candidate_sink
        self._selections, self._plans, self._banks = {}, {}, {}
        self._first = ContinuationProgram(horizon,
            branch_sink=self._original_branch, candidate_sink=self._original_bank) if arm in ("T", "G2") else None
        self.base = self._first.base if self._first is not None else OptionProgram("C", horizon)

    @property
    def controller(self):
        return self.base.controller

    @property
    def plan(self):
        return deepcopy(self.base.plan)

    @property
    def selections(self):
        return deepcopy(self._selections)

    @property
    def plans(self):
        return deepcopy(self._plans)

    @property
    def banks(self):
        return deepcopy(self._banks)

    def _emit_branch(self, identifier, result, identity):
        if self.branch_sink is not None:
            self.branch_sink(identifier, _artifact(result, identity))

    def _original_branch(self, local, result):
        self._emit_branch(f"actual/t40/branch/{local}", result,
                          dict(tree="actual", stage="t40", first=local, second=None))

    def _original_bank(self, rows):
        identifier = "actual/t40/bank"
        self._banks[identifier] = dict(candidate_count=len(rows),
            candidate_digest=hashlib.sha256(np.asarray(rows, dtype="<f8").tobytes()).hexdigest())
        if self.candidate_sink is not None:
            self.candidate_sink(identifier, rows.copy())

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

    def _ordinary_selection(self, controller, report, mask, start_t, scope, first=None):
        bank_id = scope+"/bank" if first is None else f"a2/first/{first}/t120/bank"
        bank = self._bank(controller, report, mask, start_t, bank_id)
        positions, _ = decode_public_state(report, 8)
        plans = [None, *bank["champions"]]
        branches = []
        for plan in plans:
            local = branch_id(plan)
            identifier = scope+"/branch/"+local if first is None else scope+"/"+local
            result = simulate_segment(controller, report, mask, plan, start_t=start_t)
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
            prefix = simulate_segment(self.controller, report, mask, plan, start_t=40, end_t=120)
            # Neither the inner search nor its returned states may see/replace
            # the existing unrounded outer physical state.
            outer_physical = prefix["arrays"]["positions"][-1].copy()
            report120 = encode_model_report(outer_physical, report, 120, self.horizon)
            selected120, inner = self._ordinary_selection(prefix["terminal_controller"], report120,
                prefix["terminal_mask"], 120, f"a2/first/{first}/inner", first=first)
            suffix = simulate_segment(prefix["terminal_controller"], report120, prefix["terminal_mask"],
                selected120, start_t=120, physical_positions=outer_physical)
            result = concatenate(prefix, suffix)
            result["summary"]["inner_selection"] = _compact(inner)
            result["decisions"][80]["predicted_temporal_selection"] = _compact(inner)
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

    def _install(self, selected, old_mask):
        execution = OptionProgram("C", self.horizon)
        execution.controller = self.controller
        execution.plan, execution.option_old_mask = validate_plan(selected, old_mask, self.controller.next_t), int(old_mask)
        self.base = execution  # Replaces an expired first plan, even on decline.

    def select(self, t, report, old_mask):
        if t != self.controller.next_t or ((report is not None) != (t % 10 == 0)):
            raise ValueError("temporal program skipped/repeated a clock or public report")
        if self.arm == "T" or (self.arm == "G2" and t < 120):
            command, mask, decision = self._first.select(t, report, old_mask)
            if t == 40:
                record = deepcopy(self._first.continuation)
                record.update(start_t=40, bank_id="actual/t40/bank", selected_plan=deepcopy(self.base.plan),
                    selected_model_branch="actual/t40/branch/"+record["selected_branch"])
                for branch in record["branches"]:
                    branch["model_branch"] = "actual/t40/branch/"+branch["id"]
                self._selections[40], self._plans[40] = record, deepcopy(self.base.plan)
                original = record["original_R"]
                self._banks["actual/t40/bank"].update(start_t=40, counts=deepcopy(original["counts"]),
                    digest_layout=deepcopy(original["digest_layout"]))
            return command, mask, decision
        record = None
        if t in (40, 120):
            if t in self._selections:
                raise ValueError("scheduled selection repeated")
            selected, record = self._anticipated_selection(report, old_mask) if t == 40 else self._ordinary_selection(
                self.controller, report, old_mask, 120, "actual/t120")
            self._install(selected, old_mask)
            self._selections[t], self._plans[t] = deepcopy(record), deepcopy(selected)
        command, mask, decision = self.base.select(t, report, old_mask)
        if record is not None:
            decision["option"] = deepcopy(self.base.plan)
            decision["temporal"] = deepcopy(record)
        return command, mask, decision
