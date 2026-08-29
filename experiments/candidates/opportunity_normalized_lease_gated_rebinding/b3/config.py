"""Frozen registration for the prospective ONLGR B3 screen."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

TREATMENT = "ONLGR-B3-PROSPECTIVE-HEADROOM-EXPOSURE-HETEROGENEITY"
REVISION = "2026-08-28.10-clean-01a04a02-onlgr-successor-02"
ARTIFACT_KIND = "ONLGR_B3_PROSPECTIVE_SCREEN_RESULT"
RESULT_FILENAME = f"{ARTIFACT_KIND}.json"

HORIZON = 256
LEASE_TICKS = 12
ROLES = ("T", "R")
ACTIONS = ("KEEP", "REFRESH-SAME", "REBIND")
IID_SCHEDULE = "RAND-IID-4-16-32"
RHO = 0.5
ROOTS = (271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367)
DISCOVERY_NAMESPACE = "ONLGR_B3_DISCOVERY"
CONFIRMATION_NAMESPACE = "ONLGR_B3_CONFIRMATION"
DISCOVERY_EPISODES = 8
CONFIRMATION_EPISODES = 64
LAMBDA_REF = 0.029177186853336964
LOGIT_OFFSETS = (-2, -1, 0, 1, 2)
MATERIAL_MARGIN = 0.005
EXPOSURE_MIN = 0
EXPOSURE_SPLIT = 16
EXPOSURE_MAX = 32

DISCOVERY_POLICIES = 1 + 25 + 5 + 5
CONFIRMATION_POLICIES = 5
DISCOVERY_TEAM_TICKS = DISCOVERY_POLICIES * len(ROOTS) * DISCOVERY_EPISODES * HORIZON
CONFIRMATION_TEAM_TICKS = CONFIRMATION_POLICIES * len(ROOTS) * CONFIRMATION_EPISODES * HORIZON
TOTAL_TEAM_TICKS = DISCOVERY_TEAM_TICKS + CONFIRMATION_TEAM_TICKS

CPU_THREADS = 1
MAX_RSS_BYTES = 4 * 1024**3
MAX_WALL_SECONDS = 1800.0

BRANCHES = (
    "INVALID",
    "BOUNDED_NO_HEADROOM",
    "HEADROOM_UNRESOLVED",
    "HEADROOM_WITHOUT_IDENTIFIED_EXPOSURE_HETEROGENEITY",
    "HEADROOM_AND_EXPOSURE_HETEROGENEITY",
)


@dataclass(frozen=True)
class RunConfig:
    horizon: int = HORIZON
    roots: tuple[int, ...] = ROOTS
    discovery_episodes: int = DISCOVERY_EPISODES
    confirmation_episodes: int = CONFIRMATION_EPISODES
    cpu_threads: int = CPU_THREADS
    max_rss_bytes: int = MAX_RSS_BYTES
    max_wall_seconds: float = MAX_WALL_SECONDS

    @property
    def registered(self) -> bool:
        return self == PRODUCTION_CONFIG


PRODUCTION_CONFIG = RunConfig()


def registered_work() -> dict[str, int]:
    return {
        "discovery_policies": DISCOVERY_POLICIES,
        "confirmation_policies": CONFIRMATION_POLICIES,
        "discovery_episodes": DISCOVERY_POLICIES * len(ROOTS) * DISCOVERY_EPISODES,
        "confirmation_episodes": CONFIRMATION_POLICIES * len(ROOTS) * CONFIRMATION_EPISODES,
        "discovery_team_ticks": DISCOVERY_TEAM_TICKS,
        "confirmation_team_ticks": CONFIRMATION_TEAM_TICKS,
        "total_team_ticks": TOTAL_TEAM_TICKS,
    }


def frozen_config() -> dict[str, object]:
    return {
        "treatment": TREATMENT,
        "revision": REVISION,
        "artifact_kind": ARTIFACT_KIND,
        "host": {
            "agents": 2,
            "horizon": HORIZON,
            "lease_ticks": LEASE_TICKS,
            "roles": ROLES,
            "actions": ACTIONS,
            "schedule": IID_SCHEDULE,
            "rho": RHO,
        },
        "coordinates": {
            "roots": ROOTS,
            "discovery_namespace": DISCOVERY_NAMESPACE,
            "confirmation_namespace": CONFIRMATION_NAMESPACE,
            "discovery_episodes": DISCOVERY_EPISODES,
            "confirmation_episodes": CONFIRMATION_EPISODES,
        },
        "grid": {
            "lambda_ref": LAMBDA_REF,
            "logit_offsets": LOGIT_OFFSETS,
            "exposure_bins": {"low": [0, 16], "high": [16, 32]},
        },
        "margin": MATERIAL_MARGIN,
        "resources": asdict(PRODUCTION_CONFIG),
        "registered_work": registered_work(),
    }


def config_identity() -> dict[str, object]:
    frozen = frozen_config()
    encoded = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"frozen": frozen, "sha256": hashlib.sha256(encoded).hexdigest()}


assert DISCOVERY_TEAM_TICKS == 1_179_648
assert CONFIRMATION_TEAM_TICKS == 1_310_720
assert TOTAL_TEAM_TICKS == 2_490_368
