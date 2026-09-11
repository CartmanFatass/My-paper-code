"""TEST_ONLY faithful P32 setup; stop at initial projection before any scores/learning.

Standalone: python -X faulthandler <file> <fresh TEST_ONLY output directory>.
This intentionally invokes the original run_arm only with a stop at its first
_project_panel. It is not a scientific run or a pytest-collected learner test.
"""

import json
from pathlib import Path
import sys
import time

STARTED = time.perf_counter()
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04 import run


class PrefixComplete(Exception):
    """End the test before run_arm reaches rule scores or its learner loop."""


def main(output):
    original_panel = run.engine._project_panel
    original_observations = run.engine.build_observations
    calls = 0

    def indexed_observations(tape, factory):
        nonlocal calls
        print("TEST_ONLY BEFORE_PROJECTION", calls, "tape", tape.identity.episode_id,
              "pass", calls % 2, flush=True)
        calls += 1
        result = original_observations(tape, factory)
        print("TEST_ONLY AFTER_PROJECTION", calls - 1, flush=True)
        return result

    def initial_panel(tapes, factory):
        assert len(tapes) == 32 and factory is run.engine._ADAPTERS["RAW-GRU"]
        # Retain the exact public input, ordered tape-major, then token-major.
        # Each token occupies17 bytes and each tape152 tokens. No evaluator view.
        (output / "TEST_ONLY_initial_public_tokens.bin").write_bytes(
            b"".join(token.packed for tape in tapes for token in tape.learner_tokens()))
        print("TEST_ONLY INITIAL_PANEL", len(tapes), "tapes; public bytes retained", flush=True)
        observations, work = original_panel(tapes, factory)
        assert calls == 64 and tuple(observations.shape) == (32, 152, 168)
        (output / "TEST_ONLY_prefix_result.json").write_text(json.dumps({
            "test_only": True, "initial_projection_complete": True,
            "projection_calls": calls, "shape": list(observations.shape),
            "dtype": str(observations.dtype), "adapter_work": run.asdict(work),
            "evaluation_tape_digest": run.engine._tape_primitive_digest(tapes),
            "learning_updates": 0, "score_evaluations": 0,
            "python": sys.version, "torch": str(run.torch.__version__),
        }, indent=2) + "\n")
        print("TEST_ONLY PREFIX_COMPLETE; stopping before scores/learning", flush=True)
        raise PrefixComplete

    run.engine._project_panel = initial_panel
    run.engine.build_observations = indexed_observations
    try:
        print("TEST_ONLY P32 faithful setup seed21223 START", flush=True)
        run.run_arm(arm="RAW-GRU", seed=21223, output=output,
                    launch_sha="TEST_ONLY", engineering=False, started=STARTED, b05=True)
        raise AssertionError("run_arm returned past the initial-projection stop")
    except PrefixComplete:
        pass
    finally:
        run.engine._project_panel = original_panel
        run.engine.build_observations = original_observations


if __name__ == "__main__":
    main(Path(sys.argv[1]))
