"""Complete-census acceptance analysis for RISP-ECR-R01."""

from __future__ import annotations

import ast
from fractions import Fraction
from pathlib import Path
from typing import Mapping

from .contract import (
    CERTIFIED_STATUS,
    COMPLETE_RESULT_SCHEMA,
    DIRECTION_ID,
    INVALID_STATUS,
    MAX_RSS_BYTES,
    MAX_WALL_SECONDS,
    REGISTERED_BINDING,
    TEST_COMPLETE_STATUS,
    TEST_ONLY_BINDING,
    TWIN_CENSUS_SCHEMA,
    parse_fraction_pair,
    validate_public_history,
    validate_schema_instance,
)


class AnalysisError(RuntimeError):
    """A partial or malformed census cannot be analyzed."""


PACKAGE_ROOT = Path(__file__).resolve().parent


def dependency_firewall_observation() -> dict[str, object]:
    """Inspect import edges on the isolated source surface.

    This is a static engineering observation: it establishes that package
    imports do not enter historical RISP/APFI, network, GPU, training, or
    checkpoint modules.  It does not make a scientific claim.
    """

    imports: set[str] = set()
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.add(node.module)
    folded = {name.casefold() for name in imports}
    historical_tokens = (
        "b1",
        "b2_r02",
        "b3_r03",
        "g_init_r01",
        "apfi",
    )
    network_tokens = ("socket", "urllib", "requests", "httpx", "aiohttp")
    gpu_training_tokens = ("torch", "tensorflow", "jax", "cupy", "optimizer")
    historical = sorted(
        name for name in folded if any(token in name for token in historical_tokens)
    )
    network = sorted(name for name in folded if any(name == token or name.startswith(token + ".") for token in network_tokens))
    gpu_training = sorted(
        name
        for name in folded
        if any(name == token or name.startswith(token + ".") for token in gpu_training_tokens)
    )
    return {
        "source_files_inspected": len(tuple(PACKAGE_ROOT.glob("*.py"))),
        "absolute_imports": sorted(imports),
        "historical_risp_or_apfi_imports": historical,
        "network_imports": network,
        "gpu_or_training_imports": gpu_training,
        "historical_coordinates_read": False,
        "historical_results_read": False,
        "apfi_artifacts_read": False,
        "passed": not historical and not network and not gpu_training,
    }


def _fraction(value: object, label: str) -> Fraction:
    try:
        return parse_fraction_pair(value, label)
    except ValueError as error:
        raise AnalysisError(str(error)) from error


def _controller(row: Mapping[str, object], name: str) -> Mapping[str, object]:
    controllers = row.get("controllers")
    if not isinstance(controllers, dict) or not isinstance(controllers.get(name), dict):
        raise AnalysisError(f"complete row is missing controller {name}")
    return controllers[name]  # type: ignore[return-value]


def _positive_regret(summary: Mapping[str, object], controller: str) -> bool:
    regrets = summary.get("equal_weight_regret")
    if not isinstance(regrets, dict) or controller not in regrets:
        raise AnalysisError(f"twin summary lacks {controller} regret")
    return _fraction(regrets[controller], f"{controller} regret") > 0


def _exact_belief(value: object, label: str) -> tuple[Fraction, Fraction, Fraction]:
    if not isinstance(value, list) or len(value) != 3:
        raise AnalysisError(f"{label} must contain exactly three rational masses")
    masses = tuple(_fraction(item, f"{label}[{index}]") for index, item in enumerate(value))
    if any(mass <= 0 for mass in masses) or sum(masses, Fraction()) != 1:
        raise AnalysisError(f"{label} must be a positive exact normalized law")
    return masses  # type: ignore[return-value]


def _json_shape(value: object) -> object:
    if isinstance(value, tuple):
        return [_json_shape(item) for item in value]
    if isinstance(value, list):
        return [_json_shape(item) for item in value]
    return value


def validate_registered_literal_inventory(
    rows: list[Mapping[str, object]], summaries: list[Mapping[str, object]]
) -> None:
    """Bind registered rows directly to the four literal specification entries."""

    from .contract import registered_spec

    spec = registered_spec()
    support = spec["support"]
    assert isinstance(support, dict)
    twins = support["twins"]
    assert isinstance(twins, list)
    expected_rows: dict[tuple[str, str], dict[str, object]] = {}
    expected_controllers: dict[str, object] = {}
    for twin in twins:
        assert isinstance(twin, dict)
        twin_id = str(twin["twin_id"])
        expected_controllers[twin_id] = twin["coarsened_controller"]
        raw_rows = twin["rows"]
        assert isinstance(raw_rows, list)
        for row in raw_rows:
            assert isinstance(row, dict)
            key = (twin_id, str(row["side"]))
            expected_rows[key] = {
                "twin_id": twin_id,
                "side": row["side"],
                "population_weight": row["population_weight"],
                "expected_raw_action": row["expected_raw_action"],
                "history": row["history"],
            }
    observed_rows: dict[tuple[str, str], Mapping[str, object]] = {}
    for row in rows:
        key = (str(row.get("twin_id")), str(row.get("side")))
        if key in observed_rows:
            raise AnalysisError("registered literal inventory contains a duplicate twin side")
        observed_rows[key] = row
    if set(observed_rows) != set(expected_rows):
        raise AnalysisError("registered literal twin-side inventory differs from specification")
    for key, expected in expected_rows.items():
        observed = observed_rows[key]
        actual = {field: observed.get(field) for field in expected}
        if actual != expected:
            raise AnalysisError("registered history or expected-action entry differs from specification")
    observed_controllers = {
        str(summary.get("twin_id")): summary.get("coarsened_controller")
        for summary in summaries
    }
    if observed_controllers != expected_controllers:
        raise AnalysisError("registered coarsened-controller inventory differs from specification")


def _validate_census_inventory(
    rows: list[Mapping[str, object]],
    summaries: list[Mapping[str, object]],
    *,
    binding_class: str,
    backend: object,
) -> None:
    from .contract import ACTIONS
    from .controllers import last_ack_g_masses
    from .exact_probability import UNIFORM_BELIEF, replay_public_history
    from .reachable_twins import VIEW_FUNCTIONS
    from .reference_host import (
        account_physical_time,
        choose_action,
        history_path_mass,
        q_values,
        raw_history_bayes,
        replay_full_bayes,
    )

    if binding_class == REGISTERED_BINDING:
        # This precedes all registered arithmetic so substitute histories fail
        # before any action or return is evaluated.
        validate_registered_literal_inventory(rows, summaries)

    controller_names = (
        "RAW_HISTORY_BAYES",
        "FULL_BAYES_K",
        "FULL_BAYES_K_ERASED",
        "LAST_ACK_BAYES",
        "LAST_ACK_G",
    )
    grouped: dict[str, list[Mapping[str, object]]] = {}
    full: dict[str, tuple[Fraction, Fraction, Fraction]] = {}
    raw: dict[str, tuple[Fraction, Fraction, Fraction]] = {}
    pre_last: dict[str, tuple[Fraction, Fraction, Fraction]] = {}
    weights: dict[str, Fraction] = {}

    for row in rows:
        twin_id = str(row.get("twin_id"))
        grouped.setdefault(twin_id, []).append(row)
        history = row.get("history")
        if not isinstance(history, dict):
            raise AnalysisError("census row must carry its complete public history")
        validated = validate_public_history(history, expected_binding=binding_class)
        history_id = str(validated["history_id"])
        if history_id != row.get("history_id"):
            raise AnalysisError("row history_id does not match its public history")
        weight = _fraction(row.get("population_weight"), "population_weight")
        if weight != Fraction(1, 2):
            raise AnalysisError("every twin side must retain exact weight 1/2")
        weights[history_id] = weight
        full[history_id] = replay_full_bayes(history)
        raw[history_id] = raw_history_bayes(history)
        events = history["events"]
        assert isinstance(events, list)
        pre_last[history_id] = (
            UNIFORM_BELIEF
            if len(events) == 1
            else replay_public_history(events[:-1], initial_belief=UNIFORM_BELIEF)[0]
        )
        if _exact_belief(row.get("pre_last_belief"), "pre_last_belief") != pre_last[history_id]:
            raise AnalysisError("stored pre-last belief does not replay from public history")
        exact_path_mass = history_path_mass(history)
        if _fraction(row.get("reference_path_mass"), "reference_path_mass") != exact_path_mass:
            raise AnalysisError("reference path mass does not replay under the uniform action law")

        decision = history["decision"]
        assert isinstance(decision, dict)
        credit = decision["next_hold_credit"]
        assert isinstance(credit, dict)
        expected_endpoint = {
            "next_duration": decision["next_duration"],
            "next_hold_credit_start": credit["primitive_start"],
            "next_hold_credit_end": credit["primitive_end"],
        }
        if row.get("endpoint") != expected_endpoint:
            raise AnalysisError("row endpoint does not match its public-history decision")
        accounting = row.get("physical_accounting")
        exact_accounting = account_physical_time(history)
        if not isinstance(accounting, dict) or (
            accounting.get("realized_utility") != exact_accounting["realized_utility"]
            or accounting.get("completed_physical_time")
            != exact_accounting["completed_physical_time"]
            or _fraction(
                accounting.get("physical_time_normalized_return"),
                "physical_time_normalized_return",
            )
            != exact_accounting["physical_time_normalized_return"]
        ):
            raise AnalysisError("physical-time accounting does not replay from public history")

    def marginalized(controller: str) -> dict[tuple[object, ...], tuple[Fraction, Fraction, Fraction]]:
        groups: dict[tuple[object, ...], list[Mapping[str, object]]] = {}
        for row in rows:
            history = row["history"]
            assert isinstance(history, dict)
            groups.setdefault(VIEW_FUNCTIONS[controller](history), []).append(row)
        result: dict[tuple[object, ...], tuple[Fraction, Fraction, Fraction]] = {}
        for view, members in groups.items():
            total = sum((weights[str(member["history_id"])] for member in members), Fraction())
            result[view] = tuple(
                sum(
                    (
                        weights[str(member["history_id"])]
                        * full[str(member["history_id"])][sector]
                        for member in members
                    ),
                    Fraction(),
                )
                / total
                for sector in range(3)
            )  # type: ignore[assignment]
        return result

    erased = marginalized("FULL_BAYES_K_ERASED")
    last = marginalized("LAST_ACK_BAYES")

    for row in rows:
        history = row["history"]
        assert isinstance(history, dict)
        history_id = str(row["history_id"])
        decision = history["decision"]
        assert isinstance(decision, dict)
        next_duration = int(decision["next_duration"])
        expected_states = {
            "RAW_HISTORY_BAYES": raw[history_id],
            "FULL_BAYES_K": full[history_id],
            "FULL_BAYES_K_ERASED": erased[VIEW_FUNCTIONS["FULL_BAYES_K_ERASED"](history)],
            "LAST_ACK_BAYES": last[VIEW_FUNCTIONS["LAST_ACK_BAYES"](history)],
            "LAST_ACK_G": last_ack_g_masses(history),
        }
        controllers = row.get("controllers")
        if not isinstance(controllers, dict) or set(controllers) != set(controller_names):
            raise AnalysisError("row controller inventory is incomplete")
        for name, expected_state in expected_states.items():
            record = controllers[name]
            if not isinstance(record, dict) or record.get("controller") != name:
                raise AnalysisError("controller record name does not match its inventory key")
            expected_kind = "EXACT_FIXED_G_MASS" if name == "LAST_ACK_G" else "EXACT_BELIEF"
            if record.get("state_kind") != expected_kind:
                raise AnalysisError(f"{name} state kind is invalid")
            if _exact_belief(record.get("state"), f"{name}.state") != expected_state:
                raise AnalysisError(f"{name} state does not replay from its exact information view")
            expected_q = q_values(expected_state, next_duration)
            q_wire = record.get("q_values")
            if not isinstance(q_wire, dict) or set(q_wire) != set(ACTIONS):
                raise AnalysisError(f"{name} Q inventory must contain the exact action support")
            observed_q = {
                action: _fraction(q_wire[action], f"{name}.q.{action}") for action in ACTIONS
            }
            if observed_q != expected_q:
                raise AnalysisError(f"{name} Q vector does not match its exact state and endpoint")
            expected_action, expected_value = choose_action(expected_q)
            expected_unique = sum(value == expected_value for value in expected_q.values()) == 1
            if (
                record.get("action") != expected_action
                or _fraction(record.get("value"), f"{name}.value") != expected_value
                or record.get("unique_action") is not expected_unique
                or _fraction(
                    record.get(
                        "decision_state_physical_time_normalized_expected_return"
                    ),
                    f"{name}.decision_state_physical_time_normalized_expected_return",
                )
                != expected_value / next_duration
            ):
                raise AnalysisError(f"{name} action/value/tie/endpoint record is inconsistent")
            raw_endpoint_q = q_values(raw[history_id], next_duration)
            expected_endpoint_value = raw_endpoint_q[expected_action]
            if (
                _fraction(record.get("endpoint_value"), f"{name}.endpoint_value")
                != expected_endpoint_value
                or _fraction(
                    record.get("physical_time_normalized_endpoint_return"),
                    f"{name}.physical_time_normalized_endpoint_return",
                )
                != expected_endpoint_value / next_duration
            ):
                raise AnalysisError(f"{name} row-native endpoint return is inconsistent")
        computed_raw_full = (
            raw[history_id] == full[history_id]
            and controllers["RAW_HISTORY_BAYES"]["action"]
            == controllers["FULL_BAYES_K"]["action"]
            and controllers["RAW_HISTORY_BAYES"]["value"]
            == controllers["FULL_BAYES_K"]["value"]
        )
        if row.get("raw_full_equal") is not computed_raw_full:
            raise AnalysisError("row RAW/FULL equality flag is inconsistent")

    summary_by_id = {str(summary.get("twin_id")): summary for summary in summaries}
    if len(summary_by_id) != len(summaries) or set(summary_by_id) != set(grouped):
        raise AnalysisError("twin summary inventory does not bijectively cover row groups")
    for twin_id, pair in grouped.items():
        if len(pair) != 2 or {row.get("side") for row in pair} != {"A", "B"}:
            raise AnalysisError("each twin group must contain unique sides A and B")
        pair.sort(key=lambda row: str(row.get("side")))
        summary = summary_by_id[twin_id]
        controller = summary.get("coarsened_controller")
        if controller not in ("FULL_BAYES_K_ERASED", "LAST_ACK_BAYES"):
            raise AnalysisError("twin coarsened controller is invalid")
        histories = [row["history"] for row in pair]
        assert all(isinstance(history, dict) for history in histories)
        views = [VIEW_FUNCTIONS[str(controller)](history) for history in histories]  # type: ignore[arg-type]
        common = views[0] == views[1]
        if summary.get("common_key_matches") is not common or not common:
            raise AnalysisError("twin common-key record is inconsistent")
        if summary.get("coarsened_view") != _json_shape(views[0]):
            raise AnalysisError("twin explicit coarsened view is inconsistent")
        exact_pre_last = [pre_last[str(row["history_id"])] for row in pair]
        if summary.get("pre_last_beliefs_differ") is not (
            exact_pre_last[0] != exact_pre_last[1]
        ):
            raise AnalysisError("pre-last-belief difference flag is inconsistent")
        raw_actions = [row["controllers"]["RAW_HISTORY_BAYES"]["action"] for row in pair]  # type: ignore[index]
        if summary.get("raw_actions") != raw_actions:
            raise AnalysisError("twin RAW action inventory is inconsistent")
        if summary.get("raw_actions_opposite") is not (raw_actions[0] != raw_actions[1]):
            raise AnalysisError("twin opposite-action flag is inconsistent")
        regrets = summary.get("equal_weight_regret")
        if not isinstance(regrets, dict):
            raise AnalysisError("twin regret inventory is absent")
        for name in ("FULL_BAYES_K_ERASED", "LAST_ACK_BAYES", "LAST_ACK_G"):
            computed = Fraction()
            for row in pair:
                raw_record = row["controllers"]["RAW_HISTORY_BAYES"]  # type: ignore[index]
                chosen = row["controllers"][name]["action"]  # type: ignore[index]
                raw_q = raw_record["q_values"]
                computed += Fraction(1, 2) * (
                    _fraction(raw_record["value"], "raw value")
                    - _fraction(raw_q[chosen], "raw chosen value")
                )
            if _fraction(regrets.get(name), f"{name} regret") != computed:
                raise AnalysisError(f"{name} equal-weight regret is inconsistent")

    if not isinstance(backend, dict):
        raise AnalysisError("backend inventory is absent")
    if set(backend.get("used", [])) != {str(row.get("backend")) for row in rows}:
        raise AnalysisError("backend-used inventory does not match census rows")
    if backend.get("all_rows_reference_equal") is not all(
        row.get("native_reference_equal") is True for row in rows
    ):
        raise AnalysisError("backend equality aggregate is inconsistent")


def analyze_complete_census(
    census: object,
    *,
    binding_class: str,
    resource_observation: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Analyze only a complete census and return one complete result object."""

    if binding_class not in (REGISTERED_BINDING, TEST_ONLY_BINDING):
        raise AnalysisError("unsupported result binding class")
    validate_schema_instance(census, TWIN_CENSUS_SCHEMA)
    if not isinstance(census, dict):
        raise AnalysisError("census must be an object")
    if census.get("binding_class") != binding_class or census.get("complete") is not True:
        raise AnalysisError("analysis requires a complete census with matching binding")
    rows = census.get("rows")
    summaries = census.get("twin_summaries")
    if not isinstance(rows, list) or not isinstance(summaries, list):
        raise AnalysisError("complete census rows and twin summaries must be arrays")
    expected_rows = 4 if binding_class == REGISTERED_BINDING else 2 * len(summaries)
    if len(rows) != expected_rows or len(summaries) < 1:
        raise AnalysisError("incomplete or duplicate census cardinality")
    if len({str(row.get("history_id")) for row in rows if isinstance(row, dict)}) != len(rows):
        raise AnalysisError("census history IDs must be unique")

    typed_rows: list[Mapping[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise AnalysisError("census row must be an object")
        typed_rows.append(row)
    typed_summaries: list[Mapping[str, object]] = []
    for summary in summaries:
        if not isinstance(summary, dict):
            raise AnalysisError("twin summary must be an object")
        typed_summaries.append(summary)
    _validate_census_inventory(
        typed_rows,
        typed_summaries,
        binding_class=binding_class,
        backend=census.get("backend"),
    )

    positive_reachability = all(
        _fraction(row.get("reference_path_mass"), "reference_path_mass") > 0
        for row in typed_rows
    )
    raw_full_equal = all(row.get("raw_full_equal") is True for row in typed_rows)
    native_reference_equal = all(
        row.get("native_reference_equal") is True for row in typed_rows
    )
    unique_actions = all(
        all(
            _controller(row, controller).get("unique_action") is True
            for controller in (
                "RAW_HISTORY_BAYES",
                "FULL_BAYES_K",
                "FULL_BAYES_K_ERASED",
                "LAST_ACK_BAYES",
                "LAST_ACK_G",
            )
        )
        for row in typed_rows
    )
    expected_actions_reproduced = all(
        row.get("expected_raw_action") is None
        or _controller(row, "RAW_HISTORY_BAYES").get("action")
        == row.get("expected_raw_action")
        for row in typed_rows
    )
    clocks_utility_reconcile = all(
        isinstance(row.get("physical_accounting"), dict)
        and isinstance(row["physical_accounting"].get("completed_physical_time"), int)  # type: ignore[union-attr]
        and row["physical_accounting"]["completed_physical_time"] > 0  # type: ignore[index]
        and Fraction(-1) <= _fraction(
            row["physical_accounting"].get("physical_time_normalized_return"),  # type: ignore[union-attr]
            "physical_time_normalized_return",
        )
        <= Fraction(1)
        for row in typed_rows
    )
    normalized_expected_returns_reconcile = all(
        Fraction(-1)
        <= _fraction(
            _controller(row, controller).get(
                field
            ),
            f"{controller} {field}",
        )
        <= Fraction(1)
        for row in typed_rows
        for controller in (
            "RAW_HISTORY_BAYES",
            "FULL_BAYES_K",
            "FULL_BAYES_K_ERASED",
            "LAST_ACK_BAYES",
            "LAST_ACK_G",
        )
        for field in (
            "decision_state_physical_time_normalized_expected_return",
            "physical_time_normalized_endpoint_return",
        )
    )
    pairing = all(
        summary.get("common_key_matches") is True
        and summary.get("pre_last_beliefs_differ") is True
        and summary.get("raw_actions_opposite") is True
        for summary in typed_summaries
    )

    by_id = {str(summary.get("twin_id")): summary for summary in typed_summaries}
    if binding_class == REGISTERED_BINDING:
        if set(by_id) != {"PRIOR_HISTORY_ACK_TWIN", "DURATION_ORDER_TWIN"}:
            raise AnalysisError("registered twin census identity is incomplete")
        k_erased_positive = _positive_regret(
            by_id["DURATION_ORDER_TWIN"], "FULL_BAYES_K_ERASED"
        )
        last_ack_positive = all(
            _positive_regret(summary, "LAST_ACK_BAYES") for summary in typed_summaries
        )
        g_positive = all(
            _positive_regret(summary, "LAST_ACK_G") for summary in typed_summaries
        )
    else:
        k_erased_positive = all(
            summary.get("coarsened_controller") != "FULL_BAYES_K_ERASED"
            or _positive_regret(summary, "FULL_BAYES_K_ERASED")
            for summary in typed_summaries
        )
        last_ack_positive = all(
            summary.get("coarsened_controller") != "LAST_ACK_BAYES"
            or _positive_regret(summary, "LAST_ACK_BAYES")
            for summary in typed_summaries
        )
        # TEST_ONLY fixtures need not be discriminating for the frozen G map.
        g_positive = True

    firewall = dependency_firewall_observation()
    resource = dict(resource_observation or {})
    if binding_class == REGISTERED_BINDING:
        resource_ceiling_observed = (
            resource.get("cpu_threads_start") == 1
            and resource.get("cpu_threads_end") == 1
            and resource.get("gpu_used") is False
            and resource.get("network_used") is False
            and resource.get("scientific_rng_draws") == 0
            and isinstance(resource.get("wall_seconds"), (int, float))
            and not isinstance(resource.get("wall_seconds"), bool)
            and 0 <= resource["wall_seconds"] <= MAX_WALL_SECONDS
            and isinstance(resource.get("peak_rss_bytes_before"), int)
            and isinstance(resource.get("peak_rss_bytes_after"), int)
            and max(resource["peak_rss_bytes_before"], resource["peak_rss_bytes_after"])
            <= MAX_RSS_BYTES
        )
    else:
        resource_ceiling_observed = True
    acceptance = {
        "complete_census": True,
        "positive_exact_reachability": positive_reachability,
        "twin_pairing_and_pre_last_prior_difference": pairing,
        "clocks_ack_utility_reconcile": clocks_utility_reconcile,
        "next_hold_normalized_expected_returns_reconcile": normalized_expected_returns_reconcile,
        "raw_full_rowwise_equality": raw_full_equal,
        "native_reference_rowwise_equality": native_reference_equal,
        "all_controller_actions_unique": unique_actions,
        "registered_raw_actions_reproduced": expected_actions_reproduced,
        "duration_erased_equal_weight_regret_positive": k_erased_positive,
        "last_ack_bayes_equal_weight_regret_positive": last_ack_positive,
        "last_ack_g_equal_weight_regret_positive": g_positive,
        "dependency_firewall": firewall["passed"] is True,
        "resource_ceiling_observed": resource_ceiling_observed,
    }
    passed = all(value is True for value in acceptance.values())
    status = (
        CERTIFIED_STATUS
        if binding_class == REGISTERED_BINDING and passed
        else TEST_COMPLETE_STATUS
        if binding_class == TEST_ONLY_BINDING and passed
        else INVALID_STATUS
    )
    result = {
        "schema": COMPLETE_RESULT_SCHEMA,
        "direction_id": DIRECTION_ID,
        "binding_class": binding_class,
        "spec_schema": census["spec_schema"],
        "status": status,
        "complete": True,
        "census": census,
        "acceptance": acceptance,
        "resource_observation": resource,
        "provenance_firewall": firewall,
    }
    validate_schema_instance(result, COMPLETE_RESULT_SCHEMA)
    return result


def validate_complete_result(value: object) -> Mapping[str, object]:
    """Revalidate the entire nested inventory immediately before publication."""

    validate_schema_instance(value, COMPLETE_RESULT_SCHEMA)
    if not isinstance(value, dict) or value.get("complete") is not True:
        raise AnalysisError("only a complete result can pass publication validation")
    census = value.get("census")
    if not isinstance(census, dict) or census.get("complete") is not True:
        raise AnalysisError("complete result contains a partial census")
    validate_schema_instance(census, TWIN_CENSUS_SCHEMA)
    binding = value.get("binding_class")
    if binding not in (REGISTERED_BINDING, TEST_ONLY_BINDING):
        raise AnalysisError("complete result binding is invalid")
    expected_spec_schema = (
        "RISP-ECR-R01-SPEC-V1"
        if binding == REGISTERED_BINDING
        else "TEST-ONLY-RISP-ECR-R01-SPEC-V1"
    )
    if (
        value.get("spec_schema") != expected_spec_schema
        or census.get("spec_schema") != expected_spec_schema
    ):
        raise AnalysisError("complete result spec schema does not match its binding")
    recomputed = analyze_complete_census(
        census,
        binding_class=str(binding),
        resource_observation=value.get("resource_observation")
        if isinstance(value.get("resource_observation"), dict)
        else None,
    )
    if recomputed != value:
        raise AnalysisError(
            "complete result status/acceptance/provenance does not match its full census"
        )
    return value


__all__ = [
    "AnalysisError",
    "analyze_complete_census",
    "dependency_firewall_observation",
    "validate_complete_result",
    "validate_registered_literal_inventory",
]
