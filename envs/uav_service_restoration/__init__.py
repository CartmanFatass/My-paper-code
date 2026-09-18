"""``uav_service_restoration_v0``: an independent UAV service-restoration environment.

Importing this package has no side effects.  It does not download data, compile
extensions, seed a global RNG, register or replace a default scenario, initialise a
device, or launch a process.  Heavy and optional pieces are imported lazily:

* :mod:`envs.uav_service_restoration.preprocess_milan` (raw-data ingestion) is not
  imported here;
* :mod:`envs.uav_service_restoration.adapter` imports the shared PettingZoo adapter and
  is not imported here either.

The legacy environments, factories, presets and entry points are untouched by this
package, and nothing in it is registered as a default anywhere.
"""

from __future__ import annotations

from .config import (
    ENVIRONMENT_ID,
    SCHEMA_VERSION,
    ConfigError,
    EnvConfig,
    config_from_dict,
    config_to_dict,
    load_config,
)
from .demand import (
    DemandDataError,
    EpisodeSamplingError,
    PreparedDatasetDemandSource,
    SyntheticFixtureDemandSource,
    build_demand_source,
)
from .env import UAVServiceRestorationEnv
from .types import (
    DemandFrame,
    DemandMetadata,
    DemandSource,
    EpisodeDescriptor,
    EventType,
    LinkClass,
    NetworkEvent,
    SchedulerError,
    SchedulerSizeLimitError,
    SchedulerSolveError,
    SchedulerStatus,
    SiteState,
)

__all__ = [
    "ENVIRONMENT_ID",
    "SCHEMA_VERSION",
    "ConfigError",
    "DemandDataError",
    "DemandFrame",
    "DemandMetadata",
    "DemandSource",
    "EnvConfig",
    "EpisodeDescriptor",
    "EpisodeSamplingError",
    "EventType",
    "LinkClass",
    "NetworkEvent",
    "PreparedDatasetDemandSource",
    "SchedulerError",
    "SchedulerSizeLimitError",
    "SchedulerSolveError",
    "SchedulerStatus",
    "SiteState",
    "SyntheticFixtureDemandSource",
    "UAVServiceRestorationEnv",
    "build_demand_source",
    "config_from_dict",
    "config_to_dict",
    "load_config",
]
