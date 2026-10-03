"""One actual C history with a lawful choice before the retained H_T search."""
from __future__ import annotations

from copy import deepcopy
import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import observed_bs_xy
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import controller as b10
from experiments.candidates.uav_fleet_transmission.b11_travel_ties.controller import TravelTieController
from experiments.candidates.uav_fleet_transmission.b12_resource_assignment.energy import PublicLaw
from .features import BS_SOURCES, lawful_context, pack_features

CHOICE_DTYPE = np.dtype([
    ("step", "<i4"), ("completed", "?"), ("features_available", "?"),
    ("features", "<f4", (327,)), ("previous_targets", "<f8", (8, 2)),
    ("ordinary_targets", "<f8", (8, 2)), ("committed_targets", "<f8", (8, 2)),
    ("assignment_role", "i1", (8,)), ("assignment_column", "<i2", (8,)),
    ("assignment_call", "i1", (8,)), ("eligible", "?", (8,)),
    ("m", "i1"), ("h_eligible", "?"), ("forced_reason", "i1"),
    ("bs_source", "i1"), ("bs_xy", "<f8", (2,)),
    ("owned_edges", "<f8", (8, 5)), ("return_station", "i1", (8,)),
    ("min_slack", "<f8"), ("min_slack_valid", "?"),
    ("has_previous_choice", "?"), ("previous_requested_action", "i1"),
    ("previous_same_choice_count", "<i4"),
    ("requested_action", "i1"), ("masked_action", "i1"), ("executed_action", "i1"),
    ("candidate_first", "<i8"), ("candidate_count", "<i4"),
    ("selected", "<i2"), ("h_selected", "<i2"),
    ("selected_pair", "i1", (2,)), ("tie_changed", "?"),
    ("h_search", "?"), ("h_selected_base", "?"), ("selected_pair_alias", "?"),
    ("ordinary_target_alias", "?"), ("committed_target_changed", "?"),
])


def _action(value):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer))
            or int(value) not in (0, 1)):
        raise ValueError("chooser action must be integer0=C or1=H_T")
    return int(value)


def make_chooser(policy, *, initial_parity=0):
    """Stateless audit choosers; action1 is requested only when H is available."""
    if policy not in ("C", "H_T", "alternating") or initial_parity not in (0, 1):
        raise ValueError("unknown scripted chooser")

    def choose(features, h_eligible, step):
        requested = 0 if policy == "C" else 1 if policy == "H_T" else (step // 30 + initial_parity) % 2
        return dict(action=int(requested if h_eligible else 0), scripted_request=int(requested))

    return choose


class SelectorController(TravelTieController):
    """chooser(features327, h_eligible, step)->dict(action=int, diagnostics...).

    reset deliberately never resets or starts the external chooser/learner.
    Production feedback and its physical overrides remain the driver's work.
    """
    policy_arm = "SELECTOR"

    def __init__(self, chooser):
        if not callable(chooser):
            raise TypeError("chooser must be callable")
        self.chooser = chooser
        self.law = None
        self._cold_counts = b10.CostDict()
        super().__init__()

    def reset(self):
        # Parent constructors call this virtually before constructing the final
        # provenance heuristic. Everything used below already exists or is local.
        super().reset()
        self.choice_records = []
        self.choice_diagnostics = []
        self.replay_choice_prefix = None
        self._previous_targets = np.full((8, 2), np.nan)
        self._previous_action = None
        self._same_choice_count = 0
        self._last_context = None
        self._pending_choice = None

    @property
    def cold_costs(self):
        return dict(self._cold_counts)

    @property
    def counters(self):
        return super().counters | self.cold_costs

    @property
    def last_context(self):
        return deepcopy(self._last_context)

    def audit_arrays(self):
        return super().audit_arrays() | {
            "choice_records": np.asarray(self.choice_records, dtype=CHOICE_DTYPE)}

    def propose(self, observations, state, step, previous_done, modes):
        if self.heuristic.replans_next():
            self._previous_targets = self.heuristic.targets_xy.copy()
        return super().propose(observations, state, step, previous_done, modes)

    def _bs_source(self, observations, plan):
        b10.bump(self._counts, "feature_bs_decodes")
        if observed_bs_xy(observations, self.heuristic.layout) is not None:
            return "observed-current"
        if self._seen_bs_xy is not None:
            return "observed-memory"
        return "inferred" if plan["bs_xy"] is not None else "absent"

    def _choose(self, context, step):
        b10.bump(self._counts, "feature_encodings")
        features = pack_features(context, step=step, previous_action=self._previous_action,
                                 same_choice_count=self._same_choice_count)
        # Save before invoking user code; mutation of its private copy cannot
        # alter the audited input or the context from which H is later invoked.
        self._pending_choice["features"] = features
        self._pending_choice["features_available"] = True
        self._last_trace["selector_features"] = features.copy()
        b10.bump(self._counts, "chooser_calls")
        return self.chooser(features.copy(), context["h_eligible"], int(step))

    def _on_plan(self, observations, modes, plan):
        step = self.heuristic.calls
        ordinary = self.heuristic.targets_xy.copy()
        roles = self.heuristic.assignment_role.copy()
        self._last_trace["plan_supplied_xy"] = plan["users"].copy()
        b10.equal(plan["users"], self._last_trace["canonical_xy"], "C/current-map")
        if self.law is None:
            self.law = PublicLaw(self._cold_counts)
        b10.bump(self._counts, "context_decodes")
        context = lawful_context(observations, self.heuristic.layout,
            ordinary_targets=ordinary, previous_targets=self._previous_targets,
            roles=roles, modes=modes, users=plan["users"], bs_xy=plan["bs_xy"],
            bs_source=self._bs_source(observations, plan), law=self.law, counters=self._counts)
        self._last_context = context
        self._last_trace["selector_context"] = deepcopy(context)
        row = np.zeros((), dtype=CHOICE_DTYPE)
        for name in ("requested_action", "masked_action", "executed_action", "selected", "h_selected"):
            row[name] = -1
        row["selected_pair"] = -1
        row["step"], row["previous_targets"], row["ordinary_targets"] = step, self._previous_targets, ordinary
        row["committed_targets"] = ordinary
        for field in ("assignment_role", "assignment_column", "assignment_call"):
            row[field] = getattr(self.heuristic, field)
        for field in ("eligible", "m", "h_eligible", "min_slack", "min_slack_valid", "return_station"):
            row[field] = context[field]
        row["owned_edges"], row["bs_xy"] = context["edges"], context["bs_xy"]
        row["bs_source"] = BS_SOURCES.index(context["bs_source"])
        row["forced_reason"] = 2 if plan["bs_xy"] is None else 1 if context["m"] < 2 else 0
        row["has_previous_choice"] = self._previous_action is not None
        row["previous_requested_action"] = -1 if self._previous_action is None else self._previous_action
        row["previous_same_choice_count"] = self._same_choice_count
        row["candidate_first"] = len(self.candidates)
        index = len(self.choice_records)
        recorded = None
        if self.replay_choice_prefix is not None:
            prefix = self.replay_choice_prefix
            if prefix.ndim != 1 or prefix.dtype != CHOICE_DTYPE:
                raise ValueError("invalid choice prefix schema")
            if index >= len(prefix):
                raise b10.ReplayBoundary("recorded choice prefix exhausted")
            recorded = prefix[index]
        self.choice_records.append(row)
        self.choice_diagnostics.append(None)
        self._pending_choice = row
        response = self._choose(context, step)
        if not isinstance(response, dict) or "action" not in response:
            raise ValueError("chooser must return a dict with action")
        action = _action(response["action"])
        row["requested_action"] = action
        self.choice_diagnostics[index] = deepcopy(response)
        self._last_trace["selector_response"] = deepcopy(response)
        if action == 1 and not context["h_eligible"]:
            raise ValueError("chooser requested H_T at an ineligible boundary")
        row["masked_action"] = action
        if recorded is not None:
            for name in ("step", "features_available", "features", "previous_targets",
                         "ordinary_targets", "assignment_role", "assignment_column", "assignment_call",
                         "eligible", "h_eligible", "owned_edges", "bs_source", "bs_xy", "requested_action"):
                b10.equal(row[name], recorded[name], "choice/input/" + name)
        if action:
            # Exactly the retained H_T model/query/literal tie/commit path.
            row["h_search"] = True
            try:
                super()._on_plan(observations, modes, plan)
            finally:
                row["candidate_count"] = len(self.candidates) - int(row["candidate_first"])
        else:
            self.last_decision = dict(step=int(step), candidate_first=len(self.candidates),
                candidate_count=0, selected=-1, fallback=int(row["forced_reason"]),
                future_xy=np.empty((3, 0, 2)), ordinary_targets=ordinary,
                assignment_role=roles, assignment_column=self.heuristic.assignment_column.copy(),
                assignment_call=self.heuristic.assignment_call.copy(), eligible=context["eligible"].copy(),
                selected_pair=np.array([-1, -1], dtype=np.int8), current_velocities=np.empty((0, 2)),
                h_selected=-1, tie_changed=False, top_score_mask=np.empty(0, dtype=bool),
                min_travel_mask=np.empty(0, dtype=bool))
        for name in ("candidate_count", "selected", "h_selected", "selected_pair", "tie_changed"):
            row[name] = self.last_decision[name]
        row["executed_action"] = action  # Controller choice; physical overrides are external.
        row["h_selected_base"] = bool(action and int(row["selected"]) == 0)
        if action:
            row["selected_pair_alias"] = self.candidates[int(row["candidate_first"]) + int(row["selected"])]["alias_base"]
        committed = self.heuristic.targets_xy.copy()
        row["committed_targets"] = committed
        row["ordinary_target_alias"] = np.array_equal(committed, ordinary, equal_nan=True)
        row["committed_target_changed"] = not np.array_equal(committed, self._previous_targets, equal_nan=True)
        row["completed"] = True
        if recorded is not None:
            for name in CHOICE_DTYPE.names:
                b10.equal(row[name], recorded[name], "choice/output/" + name)
        self._same_choice_count = self._same_choice_count + 1 if action == self._previous_action else 1
        self._previous_action = action
        self.last_decision.update(requested_action=action, masked_action=action,
            executed_action=action, h_eligible=context["h_eligible"], choice_index=index)
        self._last_trace["selector_choice"] = row.copy()


class ThresholdController(SelectorController):
    """Prospectively fixed ordinary latch; no network feature packing or calls."""
    def __init__(self, theta):
        if isinstance(theta, (bool, np.bool_)) or theta not in (0., .10, .20, .30):
            raise ValueError("threshold must be one of0,.10,.20,.30")
        self.theta = float(theta)
        self._latch = 0
        super().__init__(make_chooser("C"))
        self.policy_arm = "T_" + str(self.theta)

    def reset(self):
        super().reset()
        self._latch = 0

    def _choose(self, context, step):
        if not context["h_eligible"]:
            self._latch = 0
        elif context["min_slack"] >= self.theta + .05:
            self._latch = 1
        elif context["min_slack"] <= self.theta:
            self._latch = 0
        return dict(action=self._latch, theta=self.theta, min_slack=context["min_slack"])


def make_controller(arm, *, chooser=None, theta=None, initial_parity=0):
    """Canonical endpoints retain their exact classes and reset/state behavior."""
    if arm == "C":
        return b10.make_controller("C")
    if arm == "H_T":
        return TravelTieController()
    if arm == "T":
        return ThresholdController(theta)
    if arm == "SELECTOR":
        return SelectorController(chooser)
    if arm in ("forced_C", "forced_H_T", "alternating"):
        policy = {"forced_C": "C", "forced_H_T": "H_T", "alternating": "alternating"}[arm]
        return SelectorController(make_chooser(policy, initial_parity=initial_parity))
    raise ValueError("unknown B01 controller program")
