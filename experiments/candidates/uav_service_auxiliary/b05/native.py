"""B05: fixed independent recurrence of the B04 native risk intervention."""

from dataclasses import dataclass
from pathlib import Path

from ..b04 import native as b04

OBJECT_ID = "UAV-SERVICE-RISK-B05"
TRAINING_SEED = 914173


@dataclass(frozen=True)
class B05Spec(b04.B04Spec):
    seed: int = TRAINING_SEED


def production_spec(seed: int) -> B05Spec:
    if seed != TRAINING_SEED:
        raise ValueError("unplanned B05 training seed")
    return B05Spec(seed=seed)


def run_native(*, arm: str, out: Path, launch_sha: str, device_name="cuda", threads=4,
               spec: B05Spec | None = None):
    return b04.run_native(
        arm=arm, out=out, launch_sha=launch_sha, device_name=device_name, threads=threads,
        spec=spec if spec is not None else production_spec(TRAINING_SEED),
        object_id=OBJECT_ID,
    )
