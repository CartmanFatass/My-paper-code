"""Construction-only SCDMP suspended-payload host.

This package contains deterministic semantic fixtures and the exact native
reset-to-terminal host boundary.  It intentionally contains no empirical
identity, model, trainer, runner, checkpoint, evaluation, or result path.
"""

from .config import (
    CARD_REVISION,
    COMPONENT,
    FIXTURE_NAMESPACE,
    HOST_ID,
    HORIZON,
    EventOrder,
    FixtureInput,
    Regime,
    deterministic_fixture,
)

__all__ = [
    "CARD_REVISION",
    "COMPONENT",
    "FIXTURE_NAMESPACE",
    "HOST_ID",
    "HORIZON",
    "EventOrder",
    "FixtureInput",
    "Regime",
    "deterministic_fixture",
]
