"""Four actual opportunities, each rebuilt from the current lawful history."""

from copy import deepcopy

from experiments.candidates.uav_planning_opportunity_timing.b01.controller import TimingProgram
from experiments.candidates.uav_fleet_transmission.b03.controller import continuation_rank, modeled_execution_identity
from experiments.candidates.uav_fleet_transmission.b04 import controller as frozen
from experiments.candidates.uav_fleet_transmission.b04.surrogate import OptionProgram, concatenate, encode_model_report, validate_plan
from experiments.candidates.uav_fleet_transmission.control import decode_public_state
from .option import enumerate_champions, decline, branch_id, physical_identity, next_clock
from . import segment


class RollingProgram(TimingProgram):
    def __init__(self, arm, horizon=500, branch_sink=None, candidate_sink=None, reuse=True, segment_sink=None):
        if arm not in ("G_E4", "A_E4") or horizon != 500:
            raise ValueError("rolling comparison is fixed at G_E4/A_E4 H500")
        self.arm, self.horizon = arm, horizon
        self.branch_sink, self.candidate_sink = branch_sink, candidate_sink
        self.reuse, self.segment_sink = bool(reuse), segment_sink
        self._selections, self._plans, self._banks = {}, {}, {}
        self._opportunity_times, self._next_opportunity_t = [], 40
        self.base = OptionProgram("C", horizon)

    @property
    def opportunity_times(self):
        return self._opportunity_times.copy()

    @property
    def next_opportunity_t(self):
        return self._next_opportunity_t

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

    def _simulate(self, identifier, controller, report, mask, plan, **kwargs):
        result = segment.simulate_segment(controller, report, mask, plan, reuse=self.reuse, **kwargs)
        self._emit_segment(identifier, result)
        return result

    def _install(self, selected, old_mask):
        execution = OptionProgram("C", self.horizon)
        execution.controller = self.controller
        execution.plan, execution.option_old_mask = validate_plan(selected, old_mask, self.controller.next_t), int(old_mask)
        self.base = execution

    def _rolling_anticipated_selection(self, report, mask, start_t, ordinal):
        # Opportunity1 retains the complete B01 scientific payload and ae/first IDs.
        if ordinal == 1:
            if start_t != 40:
                raise ValueError("first rolling opportunity must be t40")
            return super()._anticipated_selection(report, mask)
        bank_id = f"ae/op{ordinal}/t{start_t}/bank"
        bank = self._bank(self.controller, report, mask, start_t, bank_id)
        positions, _ = decode_public_state(report, 8)
        plans, branches = [None, *bank["champions"]], []
        for plan in plans:
            first, future_t = branch_id(plan), next_clock(plan, start_t)
            scope = f"ae/op{ordinal}/{first}/t{start_t}/t{future_t}"
            prefix = self._simulate(scope + "/prefix", self.controller, report, mask, plan, start_t=start_t, end_t=future_t)
            outer = prefix["arrays"]["positions"][-1].copy()
            inner_report = encode_model_report(outer, report, future_t, self.horizon)
            selected, inner = self._ordinary_selection(deepcopy(prefix["terminal_controller"]), inner_report.copy(),
                                                        prefix["terminal_mask"], future_t, scope, first)
            suffix = self._simulate(scope + "/suffix", prefix["terminal_controller"], inner_report,
                                    prefix["terminal_mask"], selected, start_t=future_t, physical_positions=outer)
            result = concatenate(prefix, suffix)
            result["summary"]["inner_selection"] = frozen._compact(inner)
            result["summary"]["second_t"] = future_t
            result["decisions"][future_t - start_t]["predicted_temporal_selection"] = frozen._compact(inner)
            identifier = scope + "/outer"
            identity = dict(tree="ae", stage="outer", first=first, second=inner["selected_branch"], second_t=future_t,
                            ordinal=ordinal, current_t=start_t)
            summary = deepcopy(result["summary"])
            summary["identity"] = identity
            branches.append(dict(id=first, model_branch=identifier, plan=deepcopy(plan), summary=summary, second_t=future_t,
                                 physical_identity=physical_identity(plan), modeled_execution_identity=modeled_execution_identity(result["arrays"])))
            self._emit_branch(identifier, result, identity)
        best = max(range(len(branches)), key=lambda i: continuation_rank(branches[i]["summary"], plans[i]))
        if branches[best]["summary"]["total_J"] <= branches[0]["summary"]["total_J"]:
            best = 0
        selected = deepcopy(plans[best]) if best else decline(bank, positions)
        return selected, dict(start_t=start_t, second_t=next_clock(selected, start_t), bank_id=bank_id,
                              original_R=deepcopy(bank["original_R"]), branches=branches,
                              selected_branch=branches[best]["id"], selected_model_branch=branches[best]["model_branch"],
                              selected_plan=deepcopy(selected), selected_physical_identity=branches[best]["physical_identity"],
                              strict_model_improvement_over_stay=best != 0)

    def select(self, t, report, old_mask):
        if t != self.controller.next_t or ((report is not None) != (t % 10 == 0)):
            raise ValueError("rolling program skipped/repeated its clock or public report")
        record = None
        if t == self._next_opportunity_t:
            ordinal = len(self._opportunity_times) + 1
            if ordinal > 4 or t in self._selections:
                raise ValueError("rolling opportunity repeated or exceeded four")
            if self.arm == "A_E4" and ordinal < 4:
                selected, record = self._rolling_anticipated_selection(report, old_mask, t, ordinal)
            else:
                previous = self._selections[self._opportunity_times[-1]]["selected_branch"] if ordinal > 1 else None
                scope = f"actual/op{ordinal}/t{t}/first/{previous if previous is not None else 'none'}"
                selected, record = self._ordinary_selection(self.controller, report, old_mask, t, scope, previous)
            self._install(selected, old_mask)
            self._selections[t], self._plans[t] = deepcopy(record), deepcopy(selected)
            self._opportunity_times.append(t)
            self._next_opportunity_t = next_clock(selected, t) if ordinal < 4 else None
        command, mask, decision = self.base.select(t, report, old_mask)
        if record is not None:
            decision["option"] = deepcopy(self.base.plan)
            decision["temporal"] = deepcopy(record)
        return command, mask, decision
