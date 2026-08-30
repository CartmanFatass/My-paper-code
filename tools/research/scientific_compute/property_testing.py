from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, Generic, Mapping, ParamSpec, TypeVar, cast

import hypothesis
import numpy as np
from hypothesis import HealthCheck, Phase, example, find, seed, settings
from hypothesis.strategies import SearchStrategy


P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _json_value(value.item())
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, float):
        if np.isnan(value):
            return {"nonfinite": "nan"}
        if np.isposinf(value):
            return {"nonfinite": "+inf"}
        if np.isneginf(value):
            return {"nonfinite": "-inf"}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return repr(value)


@dataclass(frozen=True)
class PropertyTestContract:
    property_id: str
    property_description: str
    generator_domain: Mapping[str, Any]
    filters: tuple[str, ...]
    explicit_examples: tuple[Mapping[str, Any], ...]
    seed: int
    profile_name: str
    max_examples: int
    deadline_ms: int | None
    phases: tuple[str, ...]
    suppress_health_checks: tuple[str, ...]
    report_multiple_bugs: bool

    def __post_init__(self) -> None:
        if not self.property_id.strip() or not self.property_description.strip():
            raise ValueError("property_id and property_description must be explicit")
        if any(not isinstance(key, str) for item in self.explicit_examples for key in item):
            raise ValueError("explicit example argument names must be strings")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if not self.profile_name.strip():
            raise ValueError("profile_name must be explicit")
        if isinstance(self.max_examples, bool) or not isinstance(self.max_examples, int) or self.max_examples < 1:
            raise ValueError("max_examples must be a positive integer")
        if self.deadline_ms is not None and (
            isinstance(self.deadline_ms, bool) or not isinstance(self.deadline_ms, int) or self.deadline_ms < 1
        ):
            raise ValueError("deadline_ms must be None or a positive integer")
        if not self.phases:
            raise ValueError("phases must be explicit and non-empty")
        unknown_phases = [name for name in self.phases if not hasattr(Phase, name)]
        if unknown_phases:
            raise ValueError(f"unknown Hypothesis phase(s): {', '.join(unknown_phases)}")
        unknown_checks = [name for name in self.suppress_health_checks if not hasattr(HealthCheck, name)]
        if unknown_checks:
            raise ValueError(f"unknown Hypothesis health check(s): {', '.join(unknown_checks)}")

    def settings(self) -> settings:
        return settings(
            database=None,
            deadline=self.deadline_ms,
            derandomize=False,
            max_examples=self.max_examples,
            phases=tuple(getattr(Phase, name) for name in self.phases),
            print_blob=True,
            report_multiple_bugs=self.report_multiple_bugs,
            suppress_health_check=tuple(getattr(HealthCheck, name) for name in self.suppress_health_checks),
        )

    def replay_metadata(
        self,
        *,
        minimal_counterexample: Any | None = None,
        reproduce_failure_blob: bytes | None = None,
    ) -> dict[str, Any]:
        reproduce_failure = None
        if reproduce_failure_blob is not None:
            if not isinstance(reproduce_failure_blob, bytes):
                raise ValueError("Hypothesis reproduce-failure blobs must be bytes")
            try:
                encoded_blob = reproduce_failure_blob.decode("ascii")
            except UnicodeDecodeError as exc:
                raise ValueError("Hypothesis reproduce-failure blobs must be ASCII base64 bytes") from exc
            reproduce_failure = {
                "blob_base64": encoded_blob,
                "decorator": f"@hypothesis.reproduce_failure({hypothesis.__version__!r}, {reproduce_failure_blob!r})",
                "hypothesis_version": hypothesis.__version__,
            }
        return {
            "counterexample": _json_value(minimal_counterexample),
            "generator_domain": _json_value(self.generator_domain),
            "hypothesis_version": hypothesis.__version__,
            "kind": "hypothesis_replay",
            "limitations": [
                "A seed is deterministic for the recorded dependency version and frozen strategy/settings, not a cross-version replay guarantee.",
                "A bounded pass means no counterexample was found in this run; it is not a proof.",
            ],
            "profile": {
                "database": None,
                "deadline_ms": self.deadline_ms,
                "explicit_examples": _json_value(self.explicit_examples),
                "filters": list(self.filters),
                "max_examples": self.max_examples,
                "name": self.profile_name,
                "phases": list(self.phases),
                "report_multiple_bugs": self.report_multiple_bugs,
                "suppress_health_checks": list(self.suppress_health_checks),
            },
            "property_description": self.property_description,
            "property_id": self.property_id,
            "replay": {
                "reproduce_failure": reproduce_failure,
                "seed": self.seed,
                "seed_decorator": f"@hypothesis.seed({self.seed})",
            },
            "schema_version": 1,
        }


def with_hypothesis_contract(contract: PropertyTestContract) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Apply frozen examples, settings, and seed to an already-@given property."""

    def decorate(test: Callable[P, R]) -> Callable[P, R]:
        configured = contract.settings()(test)
        for recorded_example in reversed(contract.explicit_examples):
            configured = example(**dict(recorded_example))(configured)
        seeded = seed(contract.seed)(configured)
        return cast(Callable[P, R], seeded)

    return decorate


@dataclass(frozen=True)
class CounterexampleArtifact(Generic[T]):
    value: T
    metadata: dict[str, Any]


def find_counterexample(
    contract: PropertyTestContract,
    strategy: SearchStrategy[T],
    violates_property: Callable[[T], bool],
) -> CounterexampleArtifact[T]:
    """Use Hypothesis generation and shrinking to retain a bounded witness."""
    if contract.report_multiple_bugs:
        raise ValueError("hypothesis.find searches for one witness and requires report_multiple_bugs=False")
    value = find(
        strategy,
        violates_property,
        settings=contract.settings(),
        random=random.Random(contract.seed),
    )
    metadata = contract.replay_metadata(minimal_counterexample=value)
    metadata["search_execution"] = {
        "api": "hypothesis.find",
        "explicit_examples_applied": False,
        "health_checks": "all suppressed internally by hypothesis.find",
        "report_multiple_bugs": False,
    }
    return CounterexampleArtifact(value=value, metadata=metadata)
