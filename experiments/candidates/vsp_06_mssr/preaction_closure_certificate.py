"""Fixed rational MSSR pre-action closure and reachability certificate."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable


ASSIGNMENT_ID = "vsp06_mssr_sequence_12_20260803"
CANDIDATE = "CAND-VSP-06-MSSR@adversarial-revision-v8"
TREATMENT = "MSSR-D0-PREACT-CLOSURE-AND-REACHABILITY"
RAW_OUTPUT_BINDING = "vsp06_mssr.preaction_closure.sequence12.v1"
PRODUCTION_BASE_REVISION = "c628683ae04e102620246e440b0e8193955f1e3c"
STATE_ORDER = ("F", "S", "P")
LEGAL_MASKS = {
    "SAME": (1, 1, 1),
    "CHANGE_F": (0, 1, 1),
    "CHANGE_P": (0, 1, 0),
    "CHANGE_S": (0, 0, 0),
}
DAG = (("S", "P"), ("S", "F"), ("P", "F"))
REQUIRED_INVENTORY_CATEGORIES = (
    "persistent_cells", "caches", "routers", "normalizers", "external_memory",
    "optimizer", "ema", "rng", "actor_visible_side_channels",
)
ALLOWED_OUTPUTS = {
    "P_PREACTION_RESIDUAL_PATH_EXISTS", "P_PREACTION_PATH_NULL",
    "P_CURRENT_REBUILD_DETERMINES_P", "UNREGISTERED_PERSISTENT_DESCENDANT",
    "ILLEGAL_VALIDITY_OR_MASK", "GATE_EXACTLY_FACTORIZED", "CONTRACT_NOT_CLOSED",
}


class ContractFailure(ValueError):
    def __init__(self, label: str, detail: str):
        if label not in ALLOWED_OUTPUTS:
            raise ValueError("failure label is outside the frozen D0 vocabulary")
        super().__init__(f"{label}: {detail}")
        self.label, self.detail = label, detail


@dataclass(frozen=True)
class StateEntry:
    name: str
    owner: str
    dimension: int
    dtype: str
    byte_offset: int
    byte_width: int


@dataclass(frozen=True)
class InventoryEntry:
    name: str
    category: str
    owner: str
    depends_on: tuple[str, ...]
    may_carry_p: bool = False


@dataclass(frozen=True)
class StateManifest:
    states: tuple[StateEntry, ...]
    inventory: tuple[InventoryEntry, ...]
    dag: tuple[tuple[str, str], ...]
    descendant_closure: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class Initializer:
    name: str
    reads: tuple[str, ...]
    value: Fraction


@dataclass(frozen=True)
class CurrentContext:
    x0_self: Fraction
    x0_partner: Fraction
    x0_public: Fraction
    q_p: Fraction
    provenance: str


@dataclass(frozen=True)
class CurrentRebuild:
    reads: tuple[str, ...]
    history_reads: tuple[str, ...] = ()


@dataclass(frozen=True)
class SupportedArm:
    historical_p: Fraction
    support_weight: Fraction
    provenance: str
    environment: tuple[str, ...]
    rng: tuple[int, ...]
    non_target_state: tuple[Fraction, ...]
    side_channel_reads: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegisteredPair:
    x0: CurrentContext
    arms: tuple[SupportedArm, ...]


@dataclass(frozen=True)
class EvaluationTrace:
    first_logits_tick: int
    recurrent_update_tick: int
    state_updates: int = 0
    model_updates: int = 0
    optimizer_updates: int = 0
    rng_before: tuple[int, ...] = (17, 23)
    rng_after: tuple[int, ...] = (17, 23)
    non_target_drift: tuple[Fraction, ...] = (Fraction(0), Fraction(0))


def _fail(label: str, detail: str) -> None:
    raise ContractFailure(label, detail)


def frozen_manifest() -> StateManifest:
    states = (
        StateEntry("S", "unit.slow_context", 1, "rational_i64_pair_le", 0, 16),
        StateEntry("P", "unit.partner_interaction", 1, "rational_i64_pair_le", 16, 16),
        StateEntry("F", "unit.fast_control", 1, "rational_i64_pair_le", 32, 16),
    )
    inventory = (
        InventoryEntry("slow_task_context_cell", "persistent_cells", "unit.slow_context", ("S",)),
        InventoryEntry("partner_interaction_cell", "persistent_cells", "unit.partner_interaction", ("P",), True),
        InventoryEntry("fast_control_cell", "persistent_cells", "unit.fast_control", ("S", "P", "F"), True),
        InventoryEntry("fast_feature_cache", "caches", "unit.fast_control", ("S", "P", "F"), True),
        InventoryEntry("renewal_router", "routers", "unit.clock", ("S",)),
        InventoryEntry("input_normalizer", "normalizers", "unit.input", ()),
        InventoryEntry("external_memory", "external_memory", "unit.none", ()),
        InventoryEntry("optimizer_state", "optimizer", "unit.none", ()),
        InventoryEntry("ema_state", "ema", "unit.none", ()),
        InventoryEntry("rng_state", "rng", "unit.fixed_rng", ()),
        InventoryEntry("actor_visible_metadata", "actor_visible_side_channels", "unit.none", ()),
    )
    closure = (
        ("S", ("S", "P", "F", "slow_task_context_cell", "partner_interaction_cell", "fast_control_cell", "fast_feature_cache", "renewal_router")),
        ("P", ("P", "F", "partner_interaction_cell", "fast_control_cell", "fast_feature_cache")),
        ("F", ("F", "fast_control_cell", "fast_feature_cache")),
    )
    return StateManifest(states, inventory, DAG, closure)


def derive_descendant_closure(manifest: StateManifest) -> dict[str, set[str]]:
    state_names = {entry.name for entry in manifest.states}
    children = {name: set() for name in state_names}
    for parent, child in manifest.dag:
        if parent not in state_names or child not in state_names:
            _fail("UNREGISTERED_PERSISTENT_DESCENDANT", "DAG names an unregistered state")
        children[parent].add(child)
    derived = {}
    for root in state_names:
        states, frontier = {root}, [root]
        while frontier:
            for child in children[frontier.pop()]:
                if child not in states:
                    states.add(child)
                    frontier.append(child)
        inventory = {
            item.name for item in manifest.inventory if states.intersection(item.depends_on)
        }
        derived[root] = states | inventory
    return derived


def validate_manifest(manifest: StateManifest) -> None:
    if tuple(entry.name for entry in manifest.states) != ("S", "P", "F"):
        _fail("CONTRACT_NOT_CLOSED", "state manifest must contain exactly S/P/F")
    if manifest.dag != DAG:
        _fail("CONTRACT_NOT_CLOSED", "dependency DAG differs from S->P,S->F,P->F")
    cursor = 0
    for entry in sorted(manifest.states, key=lambda item: item.byte_offset):
        if not entry.owner or entry.dimension <= 0 or entry.dtype != "rational_i64_pair_le":
            _fail("CONTRACT_NOT_CLOSED", "state owner/dimension/dtype manifest is incomplete")
        if entry.byte_offset != cursor or entry.byte_width != 16 * entry.dimension:
            _fail("CONTRACT_NOT_CLOSED", "state byte layout has a gap or overlap")
        cursor += entry.byte_width
    if len({item.name for item in manifest.inventory}) != len(manifest.inventory):
        _fail("CONTRACT_NOT_CLOSED", "persistent inventory names overlap")
    if {item.category for item in manifest.inventory} != set(REQUIRED_INVENTORY_CATEGORIES):
        _fail("CONTRACT_NOT_CLOSED", "persistent inventory categories are incomplete")
    roots = tuple(root for root, _names in manifest.descendant_closure)
    if len(roots) != 3 or len(set(roots)) != 3:
        _fail("CONTRACT_NOT_CLOSED", "descendant closure roots must be exactly S/P/F once each")
    closure = dict(manifest.descendant_closure)
    if set(closure) != {"S", "P", "F"}:
        _fail("CONTRACT_NOT_CLOSED", "descendant closure is incomplete")
    registered = {entry.name for entry in manifest.states} | {item.name for item in manifest.inventory}
    if any(name not in registered for names in closure.values() for name in names):
        _fail("UNREGISTERED_PERSISTENT_DESCENDANT", "closure names an unregistered persistent object")
    derived = derive_descendant_closure(manifest)
    for root, names in closure.items():
        if len(names) != len(set(names)) or set(names) != derived[root]:
            _fail("CONTRACT_NOT_CLOSED", f"declared D({root}) differs from DAG/inventory closure")
    p_descendants = set(closure["P"])
    for item in manifest.inventory:
        if any(parent not in {"S", "P", "F"} for parent in item.depends_on):
            _fail("UNREGISTERED_PERSISTENT_DESCENDANT", f"{item.name} has an unregistered dependency")
        if item.may_carry_p and item.name not in p_descendants:
            _fail("UNREGISTERED_PERSISTENT_DESCENDANT", f"{item.name} carries P outside D(P)")


def validate_mask(mask: tuple[int, int, int]) -> str:
    for name, legal in LEGAL_MASKS.items():
        if tuple(mask) == legal:
            return name
    _fail("ILLEGAL_VALIDITY_OR_MASK", f"mask {tuple(mask)} is not ancestor/descendant closed")
    raise AssertionError("unreachable")


def default_initializers(schema_constant: Fraction = Fraction(2)) -> tuple[Initializer, ...]:
    return (
        Initializer("S", ("frozen_schema_constant", "frozen_policy_generation"), schema_constant),
        Initializer("P", (), Fraction(0)), Initializer("F", (), Fraction(0)),
    )


def validate_initializers(initializers: Iterable[Initializer]) -> dict[str, Initializer]:
    table = {item.name: item for item in initializers}
    if set(table) != {"S", "P", "F"}:
        _fail("CONTRACT_NOT_CLOSED", "initializer inventory is incomplete")
    allowed_s = {"frozen_schema_constant", "frozen_policy_generation"}
    if table["P"].value or table["F"].value or table["P"].reads or table["F"].reads:
        _fail("CONTRACT_NOT_CLOSED", "N_P and N_F must be current-free zeros")
    if set(table["S"].reads) - allowed_s:
        _fail("CONTRACT_NOT_CLOSED", "N_S reads outside frozen schema/policy generation")
    return table


def construct_world(mask: tuple[int, int, int], historical: dict[str, Fraction], initializers: Iterable[Initializer]) -> dict[str, Fraction]:
    validate_mask(mask)
    init = validate_initializers(initializers)
    bits = dict(zip(STATE_ORDER, mask))
    return {name: historical[name] if bits[name] else init[name].value for name in ("S", "P", "F")}


CURRENT_FIELDS = ("x0_self", "x0_partner", "x0_public", "q_p")


def rebuild_p(context: CurrentContext, spec: CurrentRebuild) -> Fraction:
    if spec.reads != CURRENT_FIELDS or spec.history_reads:
        _fail("CONTRACT_NOT_CLOSED", "B_P must read exactly registered current context and no history")
    return context.x0_self + context.x0_partner + context.x0_public + context.q_p


def registered_pair() -> RegisteredPair:
    x0 = CurrentContext(Fraction(1), Fraction(-1), Fraction(1, 2), Fraction(-1, 2), "x0_unit_star")
    shared = dict(provenance=x0.provenance, environment=("partner=frozen", "environment=frozen"), rng=(17, 23), non_target_state=(Fraction(3), Fraction(5)))
    return RegisteredPair(x0, (SupportedArm(Fraction(-1), Fraction(1, 2), **shared), SupportedArm(Fraction(1), Fraction(1, 2), **shared)))


def validate_pair(pair: RegisteredPair) -> None:
    if len(pair.arms) != 2 or len({arm.historical_p for arm in pair.arms}) != 2:
        _fail("CONTRACT_NOT_CLOSED", "same-context pair must contain two distinct historical P values")
    if any(arm.support_weight <= 0 or arm.provenance != pair.x0.provenance for arm in pair.arms):
        _fail("CONTRACT_NOT_CLOSED", "pair support/provenance is missing")
    first = pair.arms[0]
    if any((arm.environment, arm.rng, arm.non_target_state) != (first.environment, first.rng, first.non_target_state) for arm in pair.arms[1:]):
        _fail("CONTRACT_NOT_CLOSED", "non-target environment/RNG/state differs across arms")
    if any(arm.side_channel_reads for arm in pair.arms):
        _fail("CONTRACT_NOT_CLOSED", "metadata or arm label reaches the action path")


def validate_trace(trace: EvaluationTrace) -> None:
    if trace.first_logits_tick >= trace.recurrent_update_tick:
        _fail("CONTRACT_NOT_CLOSED", "first action logits are not computed before recurrence")
    if trace.state_updates or trace.model_updates or trace.optimizer_updates or trace.rng_before != trace.rng_after:
        _fail("CONTRACT_NOT_CLOSED", "D0 evaluation mutated state/model/optimizer/RNG")
    if any(trace.non_target_drift):
        _fail("CONTRACT_NOT_CLOSED", "non-target state drifted")


Vector = tuple[Fraction, Fraction]


def _add(*vectors: Vector) -> Vector:
    values = tuple(sum(parts, Fraction(0)) for parts in zip(*vectors))
    return values[0], values[1]


def _center(vector: Vector) -> Vector:
    mean = sum(vector, Fraction(0)) / 2
    return vector[0] - mean, vector[1] - mean


def _p_contribution(p_value: Fraction, beta: Fraction) -> Vector:
    return -beta * p_value / 2, beta * p_value / 2


def _vector_text(vector: Vector) -> list[str]:
    return [str(value) for value in vector]


def evaluate_arm(
    arm: SupportedArm,
    context: CurrentContext,
    beta: Fraction,
    trace: EvaluationTrace,
    rebuild: CurrentRebuild,
) -> dict[str, object]:
    validate_trace(trace)
    b_p = rebuild_p(context, rebuild)
    # Non-target terms are action-constant in this reachability unit, so the
    # two-action softmax contrast is exactly beta*P and rebuild is uniform.
    current = (Fraction(1, 4), Fraction(1, 4))
    slow = (Fraction(1, 8), Fraction(1, 8))
    fast = (Fraction(0), Fraction(0))
    keep_p, rebuilt_p = _p_contribution(arm.historical_p, beta), _p_contribution(b_p, beta)
    keep_logits = _add(current, slow, keep_p, fast)
    rebuild_logits = _add(current, slow, rebuilt_p, fast)
    delta = _center((keep_p[0] - rebuilt_p[0], keep_p[1] - rebuilt_p[1]))
    keep_probability = 1.0 / (1.0 + math.exp(-float(beta * arm.historical_p)))
    return {
        "historical_p": str(arm.historical_p),
        "support_weight": str(arm.support_weight),
        "keep_logits": _vector_text(keep_logits),
        "rebuild_logits": _vector_text(rebuild_logits),
        "delta_kb": _vector_text(delta),
        "policy_equivalent": delta == (0, 0),
        "keep_action1_probability": keep_probability,
        "rebuild_action1_probability": 0.5,
    }


def residual_output(arm_reports: Iterable[dict[str, object]]) -> str:
    deltas = [tuple(report["delta_kb"]) for report in arm_reports]
    if all(delta == ("0", "0") for delta in deltas):
        return "P_PREACTION_PATH_NULL"
    return "P_PREACTION_RESIDUAL_PATH_EXISTS"


def factorized_gate(mask: tuple[int, int, int]) -> tuple[int, int, int]:
    u_f, u_s, u_p = mask
    return u_f * u_s * u_p, u_s, u_s * u_p


def mssr_gate(mask: tuple[int, int, int]) -> tuple[int, int, int]:
    validate_mask(mask)
    u_f, u_s, u_p = mask
    return int(bool(u_f and u_s and u_p)), int(bool(u_s)), int(bool(u_s and u_p))


def gate_census() -> dict[str, object]:
    rows = {
        name: {
            "mask": list(mask),
            "g_mssr": list(mssr_gate(mask)),
            "g_fact": list(factorized_gate(mask)),
        }
        for name, mask in LEGAL_MASKS.items()
    }
    equal = all(row["g_mssr"] == row["g_fact"] for row in rows.values())
    return {
        "rows": rows,
        "output": "GATE_EXACTLY_FACTORIZED" if equal else "CONTRACT_NOT_CLOSED",
    }


PRODUCTION_PROBES = (
    ("ha_ctse_process/standalone_agent.py", "self.low_actor_hxs = np.zeros", None),
    (
        "ha_ctse_process/standalone_models.py",
        "new_actor_hxs = self.actor_rnn(actor_input, actor_hxs.float())",
        "dist, actor_out = self._dist(new_actor_hxs)",
    ),
    (
        "ha_ctse_process/variable_roster_event_models.py",
        "features, new_hidden = self.actor_rnn(features, hidden, masks)",
        "distribution = self.actor_act.action_out(features)",
    ),
)


def active_binding_report(repo_root: Path | None = None) -> dict[str, object]:
    root = repo_root or Path(__file__).resolve().parents[3]
    observations, texts = [], []
    for relative, first, second in PRODUCTION_PROBES:
        text = (root / relative).read_text(encoding="utf-8")
        texts.append(text)
        if first not in text:
            _fail("CONTRACT_NOT_CLOSED", f"commit-scoped production probe drifted: {relative}")
        if second is not None and (second not in text or text.index(first) >= text.index(second)):
            _fail("CONTRACT_NOT_CLOSED", f"production action-order probe drifted: {relative}")
        fact = "ordinary_hidden_state" if second is None else "recurrence_precedes_action_distribution"
        observations.append({"path": relative, "fact": fact})
    direct_tokens = ("MSSR", "P_CURRENT_REBUILD", "authenticated_partner_interaction_state")
    no_direct_binding = not any(token in text for token in direct_tokens for text in texts)
    return {
        "inspection_base_revision": PRODUCTION_BASE_REVISION,
        "inspection_scope": observations,
        "no_direct_binding_in_inspected_surfaces": no_direct_binding,
        "missing_objects": [
            "registered_selective_S_P_F_partition",
            "authenticated_support_native_P",
            "action_before_recurrence_first_logits",
        ],
        "output": "CONTRACT_NOT_CLOSED",
        "scope_limit": "bounded active-surface probes, not exhaustive repository absence",
    }


def build_report(repo_root: Path | None = None, beta: Fraction = Fraction(1)) -> dict[str, object]:
    manifest = frozen_manifest()
    validate_manifest(manifest)
    initializers = default_initializers()
    historical = {"S": Fraction(7), "P": Fraction(1), "F": Fraction(3)}
    worlds = {
        name: {
            key: str(value)
            for key, value in construct_world(mask, historical, initializers).items()
        }
        for name, mask in LEGAL_MASKS.items()
    }
    if "CHANGE_F" not in worlds:
        _fail("CONTRACT_NOT_CLOSED", "primary CHANGE_F cell is unreachable")
    pair = registered_pair()
    validate_pair(pair)
    rebuild = CurrentRebuild(CURRENT_FIELDS)
    if rebuild_p(pair.x0, rebuild) != 0:
        _fail("CONTRACT_NOT_CLOSED", "synthetic reachability witness requires B_P(x*)=0")
    trace = EvaluationTrace(0, 1)
    arms = [evaluate_arm(arm, pair.x0, beta, trace, rebuild) for arm in pair.arms]
    unit_output = residual_output(arms)
    gate = gate_census()
    active = active_binding_report(repo_root)
    outputs = [unit_output, str(gate["output"]), str(active["output"])]
    if any(output not in ALLOWED_OUTPUTS for output in outputs):
        raise AssertionError("report contains an output outside the frozen D0 vocabulary")
    return {
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "treatment": TREATMENT,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "complexity": {
            "legal_masks": 4,
            "supported_arms": 2,
            "hypothetical_transitions": 0,
            "training": False,
        },
        "manifest": {
            "state_order": list(STATE_ORDER),
            "dag": [list(edge) for edge in DAG],
            "state_layouts": [entry.__dict__ for entry in manifest.states],
            "inventory": [item.__dict__ for item in manifest.inventory],
            "worlds": worlds,
        },
        "synthetic_unit": {
            "registered_x0": {
                **{name: str(getattr(pair.x0, name)) for name in CURRENT_FIELDS},
                "provenance": pair.x0.provenance,
            },
            "current_rebuild_p": str(rebuild_p(pair.x0, rebuild)),
            "arms": arms,
            "output": unit_output,
            "gate": gate,
            "no_state_model_optimizer_rng_update": True,
        },
        "active_binding": active,
        "outputs": outputs,
        "terminal": "CONTRACT_NOT_CLOSED",
        "claim_boundary": (
            "fixed rational unit possibility plus bounded active-binding evidence only; "
            "no value, semantic-memory, transport, training, return, or deployment claim"
        ),
    }


def main() -> None:
    print(json.dumps(build_report(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
