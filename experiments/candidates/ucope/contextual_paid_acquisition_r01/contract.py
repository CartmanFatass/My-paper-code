"""Frozen non-result contract for contextual paid acquisition."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping
from copy import deepcopy
import json

CONTRACT_ID = "UCOPE-CONTEXTUAL-PAID-ACQUISITION-R01-20260830"
SCHEMA_VERSION = 1
HORIZON = 12
MARK_COUNT = 6
LINKAGES = ("LINKED", "SEVERED")
RELIABILITIES = (Fraction(13, 20), Fraction(17, 20))
TOTAL_COSTS = (Fraction(9, 100), Fraction(14, 100))
K_TRAIN = (1, 3, 5, 7, 9)
K_TEST = (2, 4, 6, 8)
EPISODES_PER_CONTEXT = 20_480
ROOT_ACTION_FLOOR = 2_048
PROBE_EPISODES = 10_240
DISPLAYED_COUNT_FLOOR = 256
BATCH_SIZE = 256
SEED_SLOTS = tuple(f"cpa-r01-fresh-slot-{index:02d}" for index in range(10))
RNG_VERSION_SPEC = "UCOPE_CPA_COUNTER_V1"
MODEL_SPEC = {"dtype": "float32", "root": [9, 64, 64, 1], "tail": [9, 64, 64, 1], "activation": "relu", "initialization": "counter_glorot"}
OPTIMIZER_SPEC = {
    "name": "AdamW",
    "lr": 0.0003,
    "betas": [0.9, 0.999],
    "eps": 1e-8,
    "weight_decay": 0.0001,
    "amsgrad": False,
    "maximize": False,
    "foreach": None,
    "capturable": False,
    "differentiable": False,
    "fused": None,
    "decoupled_weight_decay": True,
    "gradient_clip": 1.0,
    "passes": 1,
}
RESOURCE_CEILING = {"workers": 1, "torch_threads": 1, "batch_size": BATCH_SIZE, "model_checkpoints_per_seed": 1}

# The scorer structure includes this order. Root and tail use distinct scorers, so stage is
# represented structurally rather than by a tenth coordinate.
FEATURE_NAMES = (
    "linked_indicator",
    "reliability_p",
    "probe_time_signed",
    "probe_energy_signed",
    "belief_short",
    "belief_long",
    "action_is_probe",
    "period_over_9",
    "period_over_9_squared",
)

PRODUCTION_MODE = "PRODUCTION"
TEST_ONLY_MODE = "TEST_ONLY"


class ContractError(ValueError):
    """Raised before any stateful work when a frozen field drifts."""


def contexts() -> tuple[dict[str, Any], ...]:
    return tuple(
        {"link": link, "reliability": p, "total_cost": cost}
        for link in LINKAGES
        for p in RELIABILITIES
        for cost in TOTAL_COSTS
    )


def context_id(context: Mapping[str, Any]) -> str:
    validate_context(context)
    p = as_fraction(context["reliability"])
    cost = as_fraction(context["total_cost"])
    return f"{context['link']}-p{p.numerator}_{p.denominator}-c{cost.numerator}_{cost.denominator}"


def validate_context(context: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(context, Mapping) or set(context) != {"link", "reliability", "total_cost"}:
        raise ContractError("context key inventory mismatch")
    if context["link"] not in LINKAGES:
        raise ContractError("link outside frozen population")
    if as_fraction(context["reliability"]) not in RELIABILITIES:
        raise ContractError("reliability outside frozen population")
    if as_fraction(context["total_cost"]) not in TOTAL_COSTS:
        raise ContractError("cost outside frozen population")
    return context


def as_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, Mapping):
        if set(value) != {"numerator", "denominator"} or type(value["numerator"]) is not int or type(value["denominator"]) is not int:
            raise ContractError("rational JSON must have exact non-bool integer numerator/denominator")
        return Fraction(value["numerator"], value["denominator"])
    if isinstance(value, str):
        return Fraction(value)
    if isinstance(value, bool):
        raise ContractError("bool is not a rational contract value")
    if isinstance(value, float):
        return Fraction(str(value))
    return Fraction(value)


def fraction_json(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def default_manifest(mode: str = PRODUCTION_MODE, episodes_per_context: int | None = None) -> dict[str, Any]:
    if type(mode) is not str or mode not in (PRODUCTION_MODE, TEST_ONLY_MODE):
        raise ContractError("manifest mode must be PRODUCTION or TEST_ONLY")
    if episodes_per_context is not None and type(episodes_per_context) is not int:
        raise ContractError("episodes_per_context must be an integer")
    if mode == PRODUCTION_MODE:
        episodes = EPISODES_PER_CONTEXT
    else:
        episodes = EPISODES_PER_CONTEXT if episodes_per_context is None else episodes_per_context
    spec = contract_spec(mode, episodes)
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "mode": mode,
        "seed_slots": list(SEED_SLOTS),
        "episodes_per_context": episodes,
        "context_ids": [context_id(c) for c in contexts()],
        "contract_spec": spec,
    }


def contract_spec(mode: str, episodes_per_context: int) -> dict[str, Any]:
    unit = episodes_per_context // 10
    return {
        "horizon": HORIZON,
        "mark_count": MARK_COUNT,
        "linkages": list(LINKAGES),
        "reliabilities": [fraction_json(value) for value in RELIABILITIES],
        "total_costs": [fraction_json(value) for value in TOTAL_COSTS],
        "k_train": list(K_TRAIN),
        "k_test": list(K_TEST),
        "feature_names": list(FEATURE_NAMES),
        "support": {
            "episodes_per_context": episodes_per_context,
            "probe_episodes": 5 * unit,
            "per_immediate_period": unit,
            "per_probe_tail_period": unit,
            "displayed_count_floor": DISPLAYED_COUNT_FLOOR if mode == PRODUCTION_MODE else 1,
        },
        "model": deepcopy(MODEL_SPEC),
        "optimizer": deepcopy(OPTIMIZER_SPEC),
        "rng_version": RNG_VERSION_SPEC,
        "mode": mode,
        "resource_ceiling": deepcopy(RESOURCE_CEILING),
        "host_law": {
            "latent_regime_prior": [1, 2],
            "tail_q": "95/100-(k-center)^2/100; centers SHORT=2,LONG=8",
            "tail_time": "-k/100",
            "tail_energy": "-k^2/1000",
            "probe_service": "(2/25)*N_actual/6",
            "probe_time": "-3/100",
            "probe_energy": "-(C-3/100)",
            "severed_display": "independent_balanced_prior_regime_and_marks",
        },
        "oracle_law": {"gamma": "indicator(LINKED)*I_p(K)+1/25-C", "direct": "1/25-C", "required_unique_positive_cell": "LINKED-p17_20-c9_100"},
        "evaluation_law": {"competent_seeds_required": 9, "seed_count": 10, "max_regret": 0.02, "minimum_per_cell_tail_agreement": 0.95, "specificity_t_df9_critical": 1.833112932653633},
    }


def load_manifest(manifest: str | Path | Mapping[str, Any] | None) -> dict[str, Any]:
    if manifest is None:
        return default_manifest()
    if isinstance(manifest, Mapping):
        return dict(manifest)
    with Path(manifest).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ContractError("manifest must be a JSON object")
    return value


def validate_contract(manifest: str | Path | Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate the immutable contract without constructing a model or emitting results."""
    value = load_manifest(manifest)
    required = {"schema_version", "contract_id", "mode", "seed_slots", "episodes_per_context", "context_ids", "contract_spec"}
    if set(value) != required:
        raise ContractError(f"manifest key inventory mismatch: {sorted(set(value) ^ required)}")
    if type(value["schema_version"]) is not int or value["schema_version"] != SCHEMA_VERSION:
        raise ContractError("manifest schema version mismatch")
    if type(value["contract_id"]) is not str or value["contract_id"] != CONTRACT_ID:
        raise ContractError("manifest contract structure mismatch")
    if type(value["mode"]) is not str or value["mode"] not in (PRODUCTION_MODE, TEST_ONLY_MODE):
        raise ContractError("manifest mode must be PRODUCTION or TEST_ONLY")
    if type(value["seed_slots"]) is not list or any(type(item) is not str for item in value["seed_slots"]) or tuple(value["seed_slots"]) != SEED_SLOTS:
        raise ContractError("the ten fresh seed slots are immutable")
    if type(value["context_ids"]) is not list or any(type(item) is not str for item in value["context_ids"]) or value["context_ids"] != [context_id(c) for c in contexts()]:
        raise ContractError("context population or order drift")
    if type(value["episodes_per_context"]) is not int:
        raise ContractError("episodes_per_context must be an integer, not bool/coercible text")
    episodes = value["episodes_per_context"]
    if value["mode"] == PRODUCTION_MODE and episodes != EPISODES_PER_CONTEXT:
        raise ContractError("production materialization requires exactly 20,480 episodes per context")
    if value["mode"] == TEST_ONLY_MODE:
        if episodes < 160 or episodes > EPISODES_PER_CONTEXT or episodes % 160:
            raise ContractError("TEST_ONLY episode count must be 160..20,480 and divisible by 160")
    if len(FEATURE_NAMES) != 9 or len(set(FEATURE_NAMES)) != 9:
        raise ContractError("feature contract drift")
    expected_spec = contract_spec(value["mode"], episodes)
    if type(value["contract_spec"]) is not dict or value["contract_spec"] != expected_spec:
        raise ContractError("manifest frozen contract spec drift")
    # Exact gate construction is imported lazily to keep module import side-effect free.
    from .oracle import construct_flip_certificate

    construct_flip_certificate().validate()
    return value
