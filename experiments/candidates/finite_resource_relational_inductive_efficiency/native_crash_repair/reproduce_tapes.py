"""Non-learning source isolation for the retained A07 tape-generation crash.

No native adapter, model, optimizer, environment step, or score is constructed.
Run in a fresh process under the engineering assignment's external wall bound.
"""

import json
import sys
import time

from ..rng import AddressedRNG
from ..tapes import generate_episode_tape


def main() -> None:
    started = time.perf_counter()
    rng = AddressedRNG(bytes(32))
    completed = 0
    fields = ("event_times", "detection_uniform", "uplink_uniform",
              "base_uniform", "action_uniform")
    for episode in range(32):
        for roster in (9, 15):
            args = dict(seed_block="FRRIE-TEST-ONLY-CRASH-ISOLATION",
                        purpose="TEST_ONLY", roster=roster, update=0,
                        episode=episode)
            first = generate_episode_tape(rng, **args)
            second = generate_episode_tape(rng, **args)
            for field in fields:
                left, right = getattr(first, field), getattr(second, field)
                assert left.dtype == right.dtype and left.shape == right.shape
                assert left.tobytes() == right.tobytes(), field
                assert not left.flags.writeable and not right.flags.writeable
            completed += 2
    assert "torch" not in sys.modules
    assert not any(name.endswith(".native_adapter") for name in sys.modules)
    print(json.dumps({"tapes_completed": completed, "paired_byte_checks": 64,
                      "learning_steps": 0, "native_calls": 0,
                      "wall_seconds": time.perf_counter() - started}), flush=True)


if __name__ == "__main__":
    main()
