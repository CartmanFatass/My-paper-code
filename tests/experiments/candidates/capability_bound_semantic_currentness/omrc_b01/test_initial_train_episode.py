"""TEST_ONLY P47 core-identified TRAIN episode; no model, projection or learner."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04 import run


def main(output):
    output.mkdir(parents=True, exist_ok=False)
    run.torch.set_num_threads(1)
    print('TEST_ONLY TRAIN episode51 seed21223 START', flush=True)
    host = run.DynamicHost(run.B1_RUN_NAME, 21223)
    tape = host.build_stochastic(run.addressing.TRAIN, 51)
    public = tape.learner_tokens()
    assert len(public) == 152
    assert all(len(token.packed) == 17 for token in public)
    (output / 'TEST_ONLY_public_tokens.bin').write_bytes(b''.join(token.packed for token in public))
    (output / 'TEST_ONLY_episode_result.json').write_text(json.dumps({
        'test_only': True, 'identity': vars(tape.identity),
        'shape_bytes': [152, 17], 'primitive_digest': tape.primitive_digest,
        'public_fields': [vars(token) for token in tape.public_tokens],
        'model_initializations': 0, 'optimizer_initializations': 0,
        'projection_calls': 0, 'learning_updates': 0, 'score_evaluations': 0,
        'python': sys.version, 'torch': str(run.torch.__version__),
    }, indent=2) + '\n')
    print('TEST_ONLY TRAIN episode51 COMPLETE; zero models/projections/scores/learning', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    main(parser.parse_args().output)
