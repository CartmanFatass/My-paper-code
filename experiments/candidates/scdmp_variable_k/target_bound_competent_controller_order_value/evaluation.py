"""Complete-only evaluation contracts for the frozen TBCC revision-02 object.

The module owns no identity, coordinate, model, checkpoint, native host, or
result file.  Production callers must inject an authority guard, an accepted
model loader, and the accepted native evaluation service.  The pure aggregation
functions are exercised with deterministic TEST_ONLY fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Final, Iterable, Protocol, Sequence


class EvaluationContractError(RuntimeError):
    pass


REPLICATE_COUNT: Final[int] = 24
EPISODES_PER_REGIME: Final[int] = 120
CONTROLLERS: Final[tuple[str, ...]] = (
    "FOUNDATION", "TREAT", "FREE", "REVERSED", "SET"
)
REGIMES: Final[tuple[str, ...]] = (
    "fixed-5", "fixed-11", "fixed-7", "fixed-13", "7-to-13", "13-to-7"
)
FOUNDATION_REGIMES: Final[tuple[str, ...]] = REGIMES
COMPETENCE_REGIMES: Final[tuple[str, str]] = ("fixed-5", "fixed-11")
TARGET_REGIMES: Final[tuple[str, ...]] = (
    "fixed-7", "fixed-13", "7-to-13", "13-to-7"
)
GRAPH_ORDERS: Final[tuple[str, str]] = ("HR", "RH")
SWITCH_TICKS: Final[tuple[int, int]] = (91, 273)
FAILURE_FIELDS: Final[tuple[str, ...]] = (
    "cable_overload", "gantry_contact", "attitude_loss", "formation_loss"
)
DIRECT_ENDPOINTS: Final[tuple[str, ...]] = ("V", "W", "P", "T", "E", "O", "G", "L", "F")


def deterministic_lexicographic_argmax(logits: Sequence[float]) -> int:
    """Return the first exact maximum among the frozen 18 action logits."""

    if len(logits) != 18 or any(not math.isfinite(float(value)) for value in logits):
        raise EvaluationContractError("evaluation requires exactly 18 finite logits")
    maximum = max(float(value) for value in logits)
    return next(index for index, value in enumerate(logits) if float(value) == maximum)


def _sha256(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise EvaluationContractError(f"{field} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise EvaluationContractError(f"{field} must be a SHA-256 hex digest") from error
    return value.lower()


@dataclass(frozen=True, slots=True)
class EvaluationScenario:
    regime: str
    scenario_index: int
    graph_order: str
    switch_tick: int
    scenario_digest: str

    def validate(self) -> None:
        if self.regime not in REGIMES:
            raise EvaluationContractError("scenario regime is not registered")
        if isinstance(self.scenario_index, bool) or self.scenario_index not in range(EPISODES_PER_REGIME):
            raise EvaluationContractError("scenario_index must lie in [0,120)")
        if self.graph_order not in GRAPH_ORDERS:
            raise EvaluationContractError("graph order must be HR or RH")
        if self.regime in ("7-to-13", "13-to-7"):
            if self.switch_tick not in SWITCH_TICKS:
                raise EvaluationContractError("switch scenario requires tick 91 or 273")
        elif self.switch_tick != 0:
            raise EvaluationContractError("fixed regime must use switch_tick=0")
        _sha256(self.scenario_digest, "scenario_digest")


def validate_complete_scenarios(
    scenarios: Iterable[EvaluationScenario],
) -> tuple[EvaluationScenario, ...]:
    values = tuple(scenarios)
    if len(values) != len(REGIMES) * EPISODES_PER_REGIME:
        raise EvaluationContractError("scenario inventory must contain exactly 720 episodes")
    slots: dict[tuple[str, int], EvaluationScenario] = {}
    for value in values:
        value.validate()
        key = (value.regime, value.scenario_index)
        if key in slots:
            raise EvaluationContractError("scenario inventory contains a duplicate slot")
        slots[key] = value
    expected = {(regime, index) for regime in REGIMES for index in range(EPISODES_PER_REGIME)}
    if set(slots) != expected:
        raise EvaluationContractError("scenario inventory is incomplete or has extra slots")
    if len({value.scenario_digest for value in values}) != len(values):
        raise EvaluationContractError("fresh scenario digest is reused across episode slots")
    for regime in REGIMES:
        regime_rows = tuple(value for value in values if value.regime == regime)
        if regime in ("7-to-13", "13-to-7"):
            counts = {
                (order, tick): sum(
                    value.graph_order == order and value.switch_tick == tick
                    for value in regime_rows
                )
                for order in GRAPH_ORDERS
                for tick in SWITCH_TICKS
            }
            if set(counts.values()) != {30}:
                raise EvaluationContractError("switch order/time cells must each contain 30 episodes")
        else:
            counts = {
                order: sum(value.graph_order == order for value in regime_rows)
                for order in GRAPH_ORDERS
            }
            if counts != {"HR": 60, "RH": 60}:
                raise EvaluationContractError("fixed graph-order cells must each contain 60 episodes")
    return values


@dataclass(frozen=True, slots=True)
class EpisodeEndpoint:
    replicate: int
    controller: str
    scenario: EvaluationScenario
    safe_dock: bool
    timeout: bool
    cable_overload: bool
    gantry_contact: bool
    attitude_loss: bool
    formation_loss: bool
    dock_tick: int | None
    active_energy_sum: float
    active_ticks: int
    post_absorption_policy_queries: int = 0

    def validate(self) -> None:
        if isinstance(self.replicate, bool) or self.replicate not in range(REPLICATE_COUNT):
            raise EvaluationContractError("evaluation replicate must lie in [0,24)")
        if self.controller not in CONTROLLERS:
            raise EvaluationContractError("evaluation controller is not registered")
        self.scenario.validate()
        if any(
            not isinstance(value, bool)
            for value in (
                self.safe_dock,
                self.timeout,
                self.cable_overload,
                self.gantry_contact,
                self.attitude_loss,
                self.formation_loss,
            )
        ):
            raise EvaluationContractError("terminal and physical labels must be booleans")
        failures = tuple(bool(getattr(self, field)) for field in FAILURE_FIELDS)
        if int(self.safe_dock) + int(self.timeout) + int(any(failures)) != 1:
            raise EvaluationContractError("exactly one safe-dock/failure/timeout terminal class is required")
        if self.safe_dock:
            if isinstance(self.dock_tick, bool) or not isinstance(self.dock_tick, int) or self.dock_tick not in range(1, 365):
                raise EvaluationContractError("safe dock requires first post-update dock tick in [1,364]")
        elif self.dock_tick is not None:
            raise EvaluationContractError("failure/timeout must not expose a dock tick")
        if not math.isfinite(float(self.active_energy_sum)) or self.active_energy_sum < 0.0:
            raise EvaluationContractError("active energy sum must be finite and nonnegative")
        if isinstance(self.active_ticks, bool) or not isinstance(self.active_ticks, int) or self.active_ticks not in range(1, 365):
            raise EvaluationContractError("active tick count must lie in [1,364]")
        if self.post_absorption_policy_queries != 0:
            raise EvaluationContractError("post-absorption policy query is forbidden")

    @property
    def completion_value(self) -> float:
        return 0.0 if self.dock_tick is None else 1.0 - self.dock_tick / 364.0

    @property
    def completion_time_seconds(self) -> float:
        return 36.4 if self.dock_tick is None else 0.1 * self.dock_tick


def _validate_rows(
    rows: Iterable[EpisodeEndpoint], *, replicate: int, controllers: tuple[str, ...]
) -> tuple[EpisodeEndpoint, ...]:
    values = tuple(rows)
    expected_count = len(controllers) * len(REGIMES) * EPISODES_PER_REGIME
    if len(values) != expected_count:
        raise EvaluationContractError(f"complete inventory requires exactly {expected_count} endpoints")
    slots: dict[tuple[str, str, int], EpisodeEndpoint] = {}
    for row in values:
        row.validate()
        if row.replicate != replicate or row.controller not in controllers:
            raise EvaluationContractError("endpoint inventory mixes replicate/controller scope")
        key = (row.controller, row.scenario.regime, row.scenario.scenario_index)
        if key in slots:
            raise EvaluationContractError("endpoint slot is duplicated")
        slots[key] = row
    expected = {
        (controller, regime, index)
        for controller in controllers
        for regime in REGIMES
        for index in range(EPISODES_PER_REGIME)
    }
    if set(slots) != expected:
        raise EvaluationContractError("endpoint inventory is incomplete or has extra slots")
    reference = tuple(
        slots[(controllers[0], regime, index)].scenario
        for regime in REGIMES
        for index in range(EPISODES_PER_REGIME)
    )
    validate_complete_scenarios(reference)
    for regime in REGIMES:
        for index in range(EPISODES_PER_REGIME):
            paired = tuple(slots[(controller, regime, index)] for controller in controllers)
            scenario = paired[0].scenario
            if any(row.scenario != scenario for row in paired[1:]):
                raise EvaluationContractError("controller scenarios are not exactly paired")
    return values


@dataclass(frozen=True, slots=True)
class FoundationReplicateSummary:
    replicate: int
    safe_cells: tuple[tuple[str, float], ...]
    pooled_safe: float
    worst_failures: tuple[tuple[str, float], ...]
    episode_count: int = 720

    def validate(self) -> None:
        if self.replicate not in range(REPLICATE_COUNT):
            raise EvaluationContractError("foundation summary replicate differs")
        expected_cells = {
            f"{regime}/{order}" for regime in REGIMES for order in GRAPH_ORDERS
        }
        if len(self.safe_cells) != 12 or {key for key, _ in self.safe_cells} != expected_cells:
            raise EvaluationContractError("foundation safe-cell inventory differs")
        if {key for key, _ in self.worst_failures} != set(FAILURE_FIELDS) or len(self.worst_failures) != 4:
            raise EvaluationContractError("foundation failure inventory differs")
        quantities = [value for _, value in self.safe_cells]
        quantities.extend(value for _, value in self.worst_failures)
        quantities.append(self.pooled_safe)
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in quantities):
            raise EvaluationContractError("foundation summary fraction is outside [0,1]")
        if self.episode_count != 720:
            raise EvaluationContractError("foundation summary is not a complete 720-episode inventory")


def _fraction(values: Sequence[EpisodeEndpoint], field: str) -> float:
    return math.fsum(float(bool(getattr(value, field))) for value in values) / len(values)


def aggregate_foundation_replicate(
    rows: Iterable[EpisodeEndpoint], *, replicate: int
) -> FoundationReplicateSummary:
    values = _validate_rows(rows, replicate=replicate, controllers=("FOUNDATION",))
    safe_cells: list[tuple[str, float]] = []
    for regime in REGIMES:
        for order in GRAPH_ORDERS:
            cell = tuple(
                row for row in values
                if row.scenario.regime == regime and row.scenario.graph_order == order
            )
            if len(cell) != 60:
                raise EvaluationContractError("foundation order/regime denominator differs from 60")
            safe_cells.append((f"{regime}/{order}", _fraction(cell, "safe_dock")))
    worst_failures: list[tuple[str, float]] = []
    for field in FAILURE_FIELDS:
        by_regime = tuple(
            _fraction(tuple(row for row in values if row.scenario.regime == regime), field)
            for regime in REGIMES
        )
        worst_failures.append((field, max(by_regime)))
    result = FoundationReplicateSummary(
        replicate=replicate,
        safe_cells=tuple(safe_cells),
        pooled_safe=_fraction(values, "safe_dock"),
        worst_failures=tuple(worst_failures),
    )
    result.validate()
    return result


@dataclass(frozen=True, slots=True)
class ControllerReplicateSummary:
    controller: str
    competence: tuple[tuple[str, float], ...]
    V: float
    W: float
    P: float
    T: float
    E: float
    O: float
    G: float
    L: float
    F: float
    target_episode_count: int = 480

    def validate(self) -> None:
        if self.controller not in CONTROLLERS:
            raise EvaluationContractError("summary controller is not registered")
        expected = {
            f"{regime}/{order}" for regime in COMPETENCE_REGIMES for order in GRAPH_ORDERS
        } | {"pooled"}
        if len(self.competence) != 5 or {key for key, _ in self.competence} != expected:
            raise EvaluationContractError("final competence inventory differs")
        fractions = [value for _, value in self.competence]
        fractions.extend((self.V, self.W, self.P, self.O, self.G, self.L, self.F))
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in fractions):
            raise EvaluationContractError("controller fraction/value endpoint is outside [0,1]")
        if not math.isfinite(self.T) or not 0.0 < self.T <= 36.4:
            raise EvaluationContractError("controller time endpoint is outside (0,36.4]")
        if not math.isfinite(self.E) or self.E < 0.0:
            raise EvaluationContractError("controller energy endpoint is invalid")
        if self.target_episode_count != 480:
            raise EvaluationContractError("target endpoint inventory differs from 480 episodes")


@dataclass(frozen=True, slots=True)
class FinalReplicateSummary:
    replicate: int
    controllers: tuple[ControllerReplicateSummary, ...]
    episode_count: int = 3_600

    def validate(self) -> None:
        if self.replicate not in range(REPLICATE_COUNT):
            raise EvaluationContractError("final summary replicate differs")
        if len(self.controllers) != 5 or {value.controller for value in self.controllers} != set(CONTROLLERS):
            raise EvaluationContractError("final controller summary inventory differs")
        for value in self.controllers:
            value.validate()
        if self.episode_count != 3_600:
            raise EvaluationContractError("final summary is not a complete 3,600-episode inventory")

    def controller(self, name: str) -> ControllerReplicateSummary:
        self.validate()
        return next(value for value in self.controllers if value.controller == name)


def aggregate_final_replicate(
    rows: Iterable[EpisodeEndpoint], *, replicate: int
) -> FinalReplicateSummary:
    values = _validate_rows(rows, replicate=replicate, controllers=CONTROLLERS)
    summaries: list[ControllerReplicateSummary] = []
    for controller in CONTROLLERS:
        controller_rows = tuple(row for row in values if row.controller == controller)
        competence: list[tuple[str, float]] = []
        competence_pool: list[EpisodeEndpoint] = []
        for regime in COMPETENCE_REGIMES:
            for order in GRAPH_ORDERS:
                cell = tuple(
                    row for row in controller_rows
                    if row.scenario.regime == regime and row.scenario.graph_order == order
                )
                if len(cell) != 60:
                    raise EvaluationContractError("final competence cell denominator differs from 60")
                competence.append((f"{regime}/{order}", _fraction(cell, "safe_dock")))
                competence_pool.extend(cell)
        competence.append(("pooled", _fraction(competence_pool, "safe_dock")))
        by_regime = {
            regime: tuple(row for row in controller_rows if row.scenario.regime == regime)
            for regime in TARGET_REGIMES
        }
        if any(len(cell) != 120 for cell in by_regime.values()):
            raise EvaluationContractError("target regime denominator differs from 120")
        target = tuple(row for regime in TARGET_REGIMES for row in by_regime[regime])
        active_ticks = sum(row.active_ticks for row in target)
        summaries.append(
            ControllerReplicateSummary(
                controller=controller,
                competence=tuple(competence),
                V=math.fsum(row.completion_value for row in target) / 480.0,
                W=min(
                    math.fsum(row.completion_value for row in by_regime[regime]) / 120.0
                    for regime in TARGET_REGIMES
                ),
                P=_fraction(target, "safe_dock"),
                T=math.fsum(row.completion_time_seconds for row in target) / 480.0,
                E=math.fsum(row.active_energy_sum for row in target) / active_ticks,
                O=max(_fraction(by_regime[regime], "cable_overload") for regime in TARGET_REGIMES),
                G=max(_fraction(by_regime[regime], "gantry_contact") for regime in TARGET_REGIMES),
                L=max(_fraction(by_regime[regime], "attitude_loss") for regime in TARGET_REGIMES),
                F=max(_fraction(by_regime[regime], "formation_loss") for regime in TARGET_REGIMES),
            )
        )
    result = FinalReplicateSummary(replicate=replicate, controllers=tuple(summaries))
    result.validate()
    return result


class EvaluationAuthority(Protocol):
    def require_evaluation_authority(self, *, stage: str, replicate: int) -> None: ...


@dataclass(frozen=True, slots=True)
class AcceptedControllerBinding:
    """Caller-supplied accepted/frozen model handle with tied-arm provenance."""

    controller: str
    source_arm: str
    model_digest: str
    model: object
    technically_accepted: bool
    frozen: bool

    def validate(self) -> None:
        expected_source = {
            "FOUNDATION": "FOUNDATION",
            "TREAT": "TREAT",
            "FREE": "FREE",
            "REVERSED": "TREAT",
            "SET": "SET",
        }
        if self.controller not in expected_source or self.source_arm != expected_source[self.controller]:
            raise EvaluationContractError("controller binding violates the frozen tied-arm provenance")
        _sha256(self.model_digest, "model_digest")
        if self.technically_accepted is not True or self.frozen is not True:
            raise EvaluationContractError("evaluation requires a technically accepted frozen model")


class AcceptedModelLoader(Protocol):
    def load_accepted_controller(
        self, *, replicate: int, controller: str
    ) -> AcceptedControllerBinding: ...


class AcceptedNativeEvaluationService(Protocol):
    def evaluate_scenario(
        self,
        *,
        binding: AcceptedControllerBinding,
        replicate: int,
        controller: str,
        scenario: EvaluationScenario,
    ) -> EpisodeEndpoint: ...


def collect_complete_evaluation(
    *,
    stage: str,
    replicate: int,
    scenarios: Iterable[EvaluationScenario],
    authority: EvaluationAuthority,
    model_loader: AcceptedModelLoader,
    native_service: AcceptedNativeEvaluationService,
) -> FoundationReplicateSummary | FinalReplicateSummary:
    """Collect into memory and expose only one complete replicate summary.

    ``stage`` is exactly ``foundation-competence`` or ``final``.  The authority
    check and complete scenario validation occur before model/native calls.
    """

    if stage not in ("foundation-competence", "final"):
        raise EvaluationContractError("evaluation stage is not registered")
    if replicate not in range(REPLICATE_COUNT):
        raise EvaluationContractError("evaluation replicate must lie in [0,24)")
    scenario_values = validate_complete_scenarios(scenarios)
    authority.require_evaluation_authority(stage=stage, replicate=replicate)
    controllers = ("FOUNDATION",) if stage == "foundation-competence" else CONTROLLERS
    bindings: dict[str, AcceptedControllerBinding] = {}
    for controller in controllers:
        binding = model_loader.load_accepted_controller(replicate=replicate, controller=controller)
        if not isinstance(binding, AcceptedControllerBinding):
            raise EvaluationContractError("accepted model loader returned an unregistered binding")
        binding.validate()
        if binding.controller != controller:
            raise EvaluationContractError("accepted model binding differs from the requested controller")
        bindings[controller] = binding
    if stage == "final" and bindings["REVERSED"].model_digest != bindings["TREAT"].model_digest:
        raise EvaluationContractError("REVERSED must reuse the exact frozen TREAT model")
    rows: list[EpisodeEndpoint] = []
    for controller in controllers:
        binding = bindings[controller]
        for scenario in scenario_values:
            row = native_service.evaluate_scenario(
                binding=binding,
                replicate=replicate,
                controller=controller,
                scenario=scenario,
            )
            if row.scenario != scenario or row.controller != controller or row.replicate != replicate:
                raise EvaluationContractError("native service returned an endpoint for a different slot")
            rows.append(row)
    if stage == "foundation-competence":
        return aggregate_foundation_replicate(rows, replicate=replicate)
    return aggregate_final_replicate(rows, replicate=replicate)
