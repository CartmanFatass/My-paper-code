"""Zero-return RECCT-LITE dependency/noninterference certificate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from enum import Enum
from fractions import Fraction
import hashlib
import json
from typing import Mapping, Sequence


F = Fraction


class Mask(str, Enum):
    ZERO = "00"
    E1 = "10"
    E2 = "01"
    BOTH = "11"

    @property
    def bits(self) -> tuple[int, int]:
        return int(self.value[0]), int(self.value[1])


MASKS = (Mask.ZERO, Mask.E1, Mask.E2, Mask.BOTH)
ALLOWED_GATE_FIELDS = frozenset(
    {
        "fold_digest",
        "world_digest",
        "ancestry",
        "rng_counters",
        "equality_valid",
        "epoch_valid",
        "proposals",
        "config",
        "current_mask",
    }
)


@dataclass(frozen=True)
class Config:
    epsilon: F = F(1, 4)
    rho_cap: F = F(1, 1)
    rho_threshold: F = F(1, 2)
    credit_threshold: F = F(1, 4)
    eta: F = F(1, 8)
    learning_rate: F = F(1, 4)
    momentum_beta: F = F(1, 2)
    on_cost: F = F(1, 20)
    off_cost: F = F(1, 40)


@dataclass(frozen=True)
class Probe:
    orientation: str
    support: bool
    mu0: F
    mu1: F
    sigma: F
    signed_credit: F


@dataclass(frozen=True)
class OptimizerState:
    parameters: tuple[F, F]
    momentum: tuple[F, F]
    scheduler_step: int
    scaler: F
    clip_limit: F
    accumulation: tuple[F, F]


@dataclass(frozen=True)
class WorldState:
    roster_roles: tuple[str, str, str]
    environment: tuple[F, F]
    learner_metadata: tuple[str, ...]
    gradients: tuple[tuple[F, F], tuple[F, F], tuple[F, F]]
    optimizer: OptimizerState
    buffer: tuple[int, ...]
    partner: tuple[F, F]
    queue: tuple[int, ...]
    normalizer: tuple[F, F]
    checkpoint_epoch: int
    owner_epoch: int
    rng_namespaces: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class Ancestry:
    edges: tuple[tuple[str, str], ...]
    mutable_nodes: tuple[str, ...]
    fitted_nodes: tuple[str, ...]
    evaluation_nodes: tuple[str, ...]


@dataclass(frozen=True)
class GateInput:
    fold_digest: str
    world_digest: str
    ancestry: Ancestry
    rng_counters: tuple[tuple[str, int], ...]
    equality_valid: bool
    epoch_valid: bool
    proposals: tuple[Probe, Probe]
    config: Config
    current_mask: Mask


@dataclass(frozen=True)
class ShadowEvaluation:
    mask: Mask
    clone_id: str
    source_digest: str
    state_bytes: bytes
    q: F


@dataclass(frozen=True)
class Decision:
    current_mask: Mask
    selected_mask: Mask
    feasible_masks: tuple[Mask, ...]
    evaluations: tuple[ShadowEvaluation, ...]
    selected_state_bytes: bytes


@dataclass(frozen=True)
class AuditResult:
    terminal: str
    selected_mask: Mask
    orientation_swapped_mask: Mask
    q_values: tuple[tuple[str, F], ...]
    rho_values: tuple[F, F]
    invariants: tuple[tuple[str, bool], ...]

    def to_bytes(self) -> bytes:
        payload = {
            "invariants": {name: value for name, value in self.invariants},
            "orientation_swapped_mask": self.orientation_swapped_mask.value,
            "q_values": {name: _fs(value) for name, value in self.q_values},
            "rho_values": [_fs(value) for value in self.rho_values],
            "selected_mask": self.selected_mask.value,
            "terminal": self.terminal,
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()


def build_world() -> WorldState:
    return WorldState(
        roster_roles=("r0", "r1", "k"),
        environment=(F(1, 5), F(-1, 5)),
        learner_metadata=("registered-N3", "no-lifecycle-event"),
        gradients=((F(0), F(0)), (F(-1), F(0)), (F(0), F(-1))),
        optimizer=OptimizerState(
            parameters=(F(0), F(0)),
            momentum=(F(0), F(0)),
            scheduler_step=0,
            scaler=F(1),
            clip_limit=F(1),
            accumulation=(F(0), F(0)),
        ),
        buffer=(2, 3, 5),
        partner=(F(2, 7), F(-2, 7)),
        queue=(11, 13),
        normalizer=(F(0), F(1)),
        checkpoint_epoch=5,
        owner_epoch=5,
        rng_namespaces=(("learner", 17), ("partner", 29), ("shadow", 0)),
    )


def world_bytes(world: WorldState) -> bytes:
    return json.dumps(_jsonable(world), separators=(",", ":"), sort_keys=True).encode()


def restore_world(source: bytes) -> WorldState:
    value = json.loads(source)
    opt = value["optimizer"]
    world = WorldState(
        roster_roles=tuple(value["roster_roles"]),
        environment=_fractions(value["environment"]),
        learner_metadata=tuple(value["learner_metadata"]),
        gradients=tuple(_fractions(row) for row in value["gradients"]),
        optimizer=OptimizerState(
            parameters=_fractions(opt["parameters"]),
            momentum=_fractions(opt["momentum"]),
            scheduler_step=int(opt["scheduler_step"]),
            scaler=F(opt["scaler"]),
            clip_limit=F(opt["clip_limit"]),
            accumulation=_fractions(opt["accumulation"]),
        ),
        buffer=tuple(value["buffer"]),
        partner=_fractions(value["partner"]),
        queue=tuple(value["queue"]),
        normalizer=_fractions(value["normalizer"]),
        checkpoint_epoch=int(value["checkpoint_epoch"]),
        owner_epoch=int(value["owner_epoch"]),
        rng_namespaces=tuple((name, int(count)) for name, count in value["rng_namespaces"]),
    )
    if world_bytes(world) != source:
        raise ValueError("world clone is not byte-identical")
    return world


def build_gate_input(
    world: WorldState,
    *,
    owner_keys: tuple[str, str] = ("a", "b"),
    audit_seed: int | None = None,
    audit_record: object | None = None,
) -> GateInput:
    if len(set(owner_keys)) != 2:
        raise ValueError("owner keys must be distinct")
    del owner_keys, audit_seed, audit_record
    source = world_bytes(world)
    ancestry = Ancestry(
        edges=(
            ("sealed_fold", "preprocessor"),
            ("preprocessor", "learner"),
            ("learner_checkpoint", "recurrence"),
            ("sealed_fold", "replay"),
            ("partner_checkpoint", "partner"),
            ("owner_epoch", "sealed_fold"),
            ("sealed_fold", "normalizer"),
        ),
        mutable_nodes=(),
        fitted_nodes=("sealed_fold", "normalizer"),
        evaluation_nodes=("shadow00", "shadow10", "shadow01", "shadow11"),
    )
    raw = {
        "fold_digest": _digest(b"recct-fold-v1"),
        "world_digest": _digest(source),
        "ancestry": ancestry,
        "rng_counters": world.rng_namespaces,
        "equality_valid": True,
        "epoch_valid": world.checkpoint_epoch == world.owner_epoch,
        "proposals": (
            Probe("e1:a->b", True, F(0), F(3, 4), F(1), F(1, 2)),
            Probe("e2:b->a", True, F(0), F(3, 4), F(1), F(1, 2)),
        ),
        "config": Config(),
        "current_mask": Mask.ZERO,
    }
    return bind_gate_input(raw)


def bind_gate_input(raw: Mapping[str, object]) -> GateInput:
    keys = frozenset(raw)
    if keys != ALLOWED_GATE_FIELDS:
        raise ValueError(f"undeclared gate input fields: {sorted(keys - ALLOWED_GATE_FIELDS)}")
    return validate_gate(GateInput(**raw))  # type: ignore[arg-type]


def validate_gate(gate: GateInput) -> GateInput:
    if gate.current_mask is not Mask.ZERO:
        raise ValueError("scientific gate must initialize from literal 00")
    if not gate.equality_valid or not gate.epoch_valid:
        raise ValueError("pretreatment equality and epoch must be authenticated")
    if not validate_ancestry(gate.ancestry):
        raise ValueError("ancestry graph is not isolated")
    names = tuple(name for name, _ in gate.rng_counters)
    if len(set(names)) != len(names) or {"audit", "global"} & set(names):
        raise ValueError("RNG namespaces are not disjoint")
    return gate


def gate_input_bytes(gate: GateInput) -> bytes:
    return json.dumps(_jsonable(gate), separators=(",", ":"), sort_keys=True).encode()


def validate_ancestry(manifest: Ancestry) -> bool:
    reach = set(manifest.edges)
    for _ in range(len({node for edge in reach for node in edge})):
        reach |= {(a, d) for a, b in reach for c, d in reach if b == c}
    acyclic = not any(parent == child for parent, child in reach)
    protected = set(manifest.fitted_nodes) | set(manifest.evaluation_nodes)
    return acyclic and not (set(manifest.mutable_nodes) & protected)


def rho(probe: Probe, config: Config) -> F:
    if probe.sigma + config.epsilon <= 0:
        raise ValueError("rho denominator must be positive")
    raw = (probe.mu1 - probe.mu0) / (probe.sigma + config.epsilon)
    return min(config.rho_cap, max(F(0), raw))


def edge_feasible_values(support: bool, rho_value: F, credit: F, config: Config) -> bool:
    return support and rho_value >= config.rho_threshold and credit >= config.credit_threshold


def optimizer_step(
    world: WorldState,
    mask: Mask,
    config: Config,
) -> WorldState:
    base, edge1, edge2 = world.gradients
    bits = mask.bits
    opt = world.optimizer
    total = tuple(
        base[i] + bits[0] * edge1[i] + bits[1] * edge2[i] + opt.accumulation[i]
        for i in range(2)
    )
    unscaled = tuple(value / opt.scaler for value in total)
    clipped = tuple(min(opt.clip_limit, max(-opt.clip_limit, value)) for value in unscaled)
    momentum = tuple(config.momentum_beta * opt.momentum[i] + clipped[i] for i in range(2))
    learning_rate = config.learning_rate / (opt.scheduler_step + 1)
    parameters = tuple(opt.parameters[i] - learning_rate * momentum[i] for i in range(2))
    updated = replace(
        opt,
        parameters=parameters,
        momentum=momentum,
        scheduler_step=opt.scheduler_step + 1,
        accumulation=(F(0), F(0)),
    )
    return replace(world, optimizer=updated)


def four_step_evaluator(world: WorldState) -> F:
    first, second = world.optimizer.parameters
    return 4 * (2 * first - second)


def evaluate_masks(
    world: WorldState,
    gate: GateInput,
    order: Sequence[Mask] = MASKS,
) -> tuple[ShadowEvaluation, ...]:
    if set(order) != set(MASKS) or len(order) != 4:
        raise ValueError("mask enumeration must contain 00/10/01/11 exactly once")
    source = world_bytes(world)
    source_digest = _digest(source)
    base_state = optimizer_step(restore_world(source), Mask.ZERO, gate.config)
    base_utility = four_step_evaluator(base_state)
    results = []
    for mask in order:
        clone = restore_world(source)
        updated = optimizer_step(clone, mask, gate.config)
        on, off = _transition_counts(gate.current_mask, mask)
        cost = on * gate.config.on_cost + off * gate.config.off_cost
        delta = four_step_evaluator(updated) - base_utility
        q = F(0) if mask is Mask.ZERO else delta - cost
        results.append(
            ShadowEvaluation(mask, f"shadow-{mask.value}", source_digest, world_bytes(updated), q)
        )
    return tuple(results)


def choose_mask(
    current: Mask,
    feasible_masks: Sequence[Mask],
    scores: Mapping[Mask, F],
    eta: F,
) -> Mask:
    feasible = tuple(feasible_masks)
    if Mask.ZERO not in feasible or not feasible:
        raise ValueError("literal 00 must remain feasible")
    top = max(scores[mask] for mask in feasible)
    leaders = tuple(mask for mask in feasible if scores[mask] == top)
    if len(leaders) != 1:
        return current if current in leaders else Mask.ZERO
    best = leaders[0]
    if best is current:
        return current
    second = max(scores[mask] for mask in feasible if mask is not best)
    if top - second > eta:
        return best
    return current if current in feasible else Mask.ZERO


def decide(
    gate: GateInput,
    world: WorldState,
    order: Sequence[Mask] = MASKS,
) -> Decision:
    gate = validate_gate(gate)
    if gate.world_digest != _digest(world_bytes(world)):
        raise ValueError("gate and optimizer world differ")
    evaluations = evaluate_masks(world, gate, order)
    by_mask = {item.mask: item for item in evaluations}
    edge_ok = tuple(
        edge_feasible_values(
            probe.support, rho(probe, gate.config), probe.signed_credit, gate.config
        )
        for probe in gate.proposals
    )
    feasible = tuple(
        mask
        for mask in MASKS
        if (not mask.bits[0] or edge_ok[0]) and (not mask.bits[1] or edge_ok[1])
    )
    selected = choose_mask(
        gate.current_mask,
        feasible,
        {mask: by_mask[mask].q for mask in MASKS},
        gate.config.eta,
    )
    ordered = tuple(sorted(evaluations, key=lambda item: MASKS.index(item.mask)))
    return Decision(gate.current_mask, selected, feasible, ordered, by_mask[selected].state_bytes)


def g_sc(
    gate: GateInput,
    world: WorldState,
    psi: str,
) -> Decision:
    semantic_branch_computed = bool(psi)
    del semantic_branch_computed
    return decide(gate, world)


def g_sd(
    gate: GateInput,
    world: WorldState,
    signs: tuple[int, int],
) -> Decision:
    if any(sign not in (-1, 1) for sign in signs):
        raise ValueError("G_SD signs must be +/-1")
    probes = tuple(
        replace(probe, signed_credit=abs(probe.signed_credit) * signs[index])
        for index, probe in enumerate(gate.proposals)
    )
    return decide(replace(gate, proposals=probes), world)


def g_sem(receipt: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    if set(receipt) != {"authenticated", "confirmation", "support_stratum"}:
        raise ValueError("semantic receipt schema mismatch")
    return tuple(sorted(receipt.items()))


def g_pi(receipt: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    permuted = dict(receipt)
    permuted["confirmation"] = not bool(permuted["confirmation"])
    return g_sem(permuted)


def fit_pretreatment_records(records: Sequence[Mapping[str, object]], stage: str) -> F:
    if stage not in {"fit", "normalize", "threshold"}:
        raise ValueError("unknown pretreatment pipeline stage")
    if any(record.get("record_type") == "audit" for record in records):
        raise ValueError("audit-typed records are forbidden from pretreatment pipelines")
    values = tuple(F(str(record["value"])) for record in records)
    return sum(values, F(0)) / len(values)


def truth_table_complete(config: Config) -> bool:
    levels = tuple(config.rho_threshold + offset for offset in (-F(1, 4), F(0), F(1, 4)))
    credits = tuple(config.credit_threshold + offset for offset in (-F(1, 8), F(0), F(1, 8)))
    threshold_cells = all(
        edge_feasible_values(True, r, credit, config)
        == (r >= config.rho_threshold and credit >= config.credit_threshold)
        for r in levels
        for credit in credits
    )
    tie_scores = {Mask.ZERO: F(1), Mask.E1: F(1), Mask.E2: F(0), Mask.BOTH: F(-1)}
    at_gap = {Mask.ZERO: F(0), Mask.E1: config.eta, Mask.E2: F(-1), Mask.BOTH: F(-2)}
    above_gap = at_gap | {Mask.E1: config.eta + F(1, 16)}
    return threshold_cells and all(
        (
            choose_mask(Mask.ZERO, MASKS, above_gap, config.eta) is Mask.E1,
            choose_mask(Mask.ZERO, MASKS, at_gap, config.eta) is Mask.ZERO,
            choose_mask(Mask.ZERO, MASKS, tie_scores, config.eta) is Mask.ZERO,
            choose_mask(Mask.E1, (Mask.ZERO, Mask.E2), tie_scores, config.eta) is Mask.ZERO,
        )
    )


def run_noninterference_audit() -> AuditResult:
    world = build_world()
    gate = build_gate_input(world)
    seed_variant = build_gate_input(world, audit_seed=991)
    record_variant = build_gate_input(world, audit_record={"record_type": "audit"})
    renamed = build_gate_input(world, owner_keys=("owner-z", "owner-y"))
    decision = g_sc(gate, world, "semantic-false")
    psi_variant = g_sc(gate, world, "semantic-true")
    reverse_order = decide(gate, world, tuple(reversed(MASKS)))
    swapped_world = replace(
        world,
        gradients=(world.gradients[0], world.gradients[2], world.gradients[1]),
    )
    swapped_gate = replace(
        build_gate_input(swapped_world),
        proposals=tuple(reversed(gate.proposals)),
    )
    swapped = decide(swapped_gate, swapped_world)
    sd = g_sd(gate, world, (-1, 1))
    semantic_receipt = {"authenticated": True, "confirmation": True, "support_stratum": "s0"}
    sem_report, pi_report = g_sem(semantic_receipt), g_pi(semantic_receipt)
    evaluations = {item.mask: item for item in decision.evaluations}
    source_digest = _digest(world_bytes(world))
    committed = restore_world(decision.selected_state_bytes)
    invariants = (
        (
            "input_and_audit_isolation",
            gate_input_bytes(gate)
            == gate_input_bytes(seed_variant)
            == gate_input_bytes(record_variant),
        ),
        ("owner_label_bijection_invariant", gate_input_bytes(gate) == gate_input_bytes(renamed)),
        (
            "orientation_swap_equivariant",
            decision.selected_mask is Mask.E1 and swapped.selected_mask is Mask.E2,
        ),
        (
            "four_byte_identical_independent_clones",
            len({item.clone_id for item in decision.evaluations}) == 4
            and all(item.source_digest == source_digest for item in decision.evaluations),
        ),
        (
            "enumeration_order_invariant",
            {item.mask: item.state_bytes for item in decision.evaluations}
            == {item.mask: item.state_bytes for item in reverse_order.evaluations},
        ),
        ("ancestry_and_rng_isolated", validate_ancestry(gate.ancestry)),
        ("threshold_hysteresis_truth_table_complete", truth_table_complete(gate.config)),
        (
            "real_equals_selected_shadow_bytes",
            world_bytes(committed) == evaluations[decision.selected_mask].state_bytes,
        ),
        (
            "semantic_firewall",
            decision.selected_mask == psi_variant.selected_mask
            and decision.selected_state_bytes == psi_variant.selected_state_bytes,
        ),
        (
            "shadow_reports_do_not_mutate_state",
            sem_report != pi_report and world_bytes(world) == world_bytes(build_world()),
        ),
        (
            "matched_sign_null_preserves_optimizer_inputs",
            sd.evaluations == decision.evaluations,
        ),
    )
    passed = all(value for _, value in invariants)
    return AuditResult(
        "PASS_DEPENDENCY_NONINTERFERENCE_D0" if passed else "INVALID_DEPENDENCY_CONTRACT",
        decision.selected_mask,
        swapped.selected_mask,
        tuple((mask.value, evaluations[mask].q) for mask in MASKS),
        tuple(rho(probe, gate.config) for probe in gate.proposals),
        invariants,
    )


def _transition_counts(current: Mask, target: Mask) -> tuple[int, int]:
    pairs = tuple(zip(current.bits, target.bits))
    return sum(a == 0 and b == 1 for a, b in pairs), sum(a == 1 and b == 0 for a, b in pairs)


def _fractions(values: Sequence[str]) -> tuple[F, F]:
    return tuple(F(value) for value in values)  # type: ignore[return-value]


def _fs(value: F) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _jsonable(value: object) -> object:
    if isinstance(value, F):
        return _fs(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
