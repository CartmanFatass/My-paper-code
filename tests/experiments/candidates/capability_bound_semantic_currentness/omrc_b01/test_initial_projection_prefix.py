"""TEST_ONLY faithful P32 setup; stop at initial projection before any scores/learning.

Standalone: python -X faulthandler <file> <fresh TEST_ONLY output directory>.
This intentionally invokes the original run_arm only with a stop at its first
_project_panel. It is not a scientific run or a pytest-collected learner test.
"""

import argparse
import json
from pathlib import Path
import sys
import time

STARTED = time.perf_counter()
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04 import run


class PrefixComplete(Exception):
    """End the test before run_arm reaches rule scores or its learner loop."""


def main(output, minimal_reference=None):
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
        if minimal_reference is None:
            (output / "TEST_ONLY_initial_public_tokens.bin").write_bytes(
                b"".join(token.packed for tape in tapes for token in tape.learner_tokens()))
            print("TEST_ONLY INITIAL_PANEL", len(tapes), "tapes; public bytes retained", flush=True)
        observations, work = original_panel(tapes, factory)
        assert tuple(observations.shape) == (32, 152, 168)
        if minimal_reference is None:
            assert calls == 64
        else:
            # Perform the reference read/copy only AFTER projection has returned.
            actual = b"".join(token.packed for tape in tapes for token in tape.learner_tokens())
            assert actual == minimal_reference.read_bytes()
            print("TEST_ONLY POST_PROJECTION input bytes equal saved reference", flush=True)
        (output / "TEST_ONLY_prefix_result.json").write_text(json.dumps({
            "test_only": True, "initial_projection_complete": True,
            "variant": "indexed" if minimal_reference is None else "minimal",
            "logged_projection_calls": calls, "shape": list(observations.shape),
            "saved_input_equal": None if minimal_reference is None else True,
            "dtype": str(observations.dtype), "adapter_work": run.asdict(work),
            "evaluation_tape_digest": run.engine._tape_primitive_digest(tapes),
            "learning_updates": 0, "score_evaluations": 0,
            "python": sys.version, "torch": str(run.torch.__version__),
        }, indent=2) + "\n")
        print("TEST_ONLY PREFIX_COMPLETE; stopping before scores/learning", flush=True)
        raise PrefixComplete

    run.engine._project_panel = initial_panel
    if minimal_reference is None:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--minimal-reference", type=Path,
                        help="omit pre-projection export/logging; compare these saved bytes after projection")
    args = parser.parse_args()
    main(args.output, args.minimal_reference)
