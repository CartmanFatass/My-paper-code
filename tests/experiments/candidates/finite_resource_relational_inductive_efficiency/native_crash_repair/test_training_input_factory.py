"""Non-learning production input-factory diagnostic with existing TEST fixtures.

Standalone entry point; eight tape-coordinate updates are not learner updates.
Run under the externally enforced complete 120-second P47 diagnostic bound.
"""

import json
import sys
import time


def main():
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02 import experiment
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.semantics import TEST_ROOT_HEX, TEST_SEED_LABEL
    import torch

    torch.set_num_threads(1)
    root = bytes.fromhex(TEST_ROOT_HEX)
    started = time.perf_counter()
    completed = 0
    for coordinate in range(1, 9):
        tapes, origins = experiment.production_training_inputs(root, TEST_SEED_LABEL, coordinate)
        assert len(tapes) == len(origins) == 64
        assert tuple(t.roster for t in tapes) == (9, 15) * 32
        assert all(t.seed_block == TEST_SEED_LABEL and t.update == coordinate for t in tapes)
        assert all(len(row) == 3 for row in origins)
        completed += len(tapes)
        print(json.dumps({"input_coordinate": coordinate, "tapes_completed": completed}), flush=True)
    print(json.dumps({
        "tapes_completed": completed, "origin_rows": completed,
        "origin_selections": completed * 3, "wall_seconds": time.perf_counter() - started,
        "python": sys.version, "torch": torch.__version__, "torch_threads": torch.get_num_threads(),
        "models_created": 0, "learning_steps": 0, "native_calls": 0,
        "trace_active": sys.gettrace() is not None, "profile_active": sys.getprofile() is not None,
    }), flush=True)


if __name__ == "__main__":
    main()
